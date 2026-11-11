#!/usr/bin/env python
"""RL5B runner v2 -- extends rl5b_queue.py (imported, NOT modified, so the guarded training pipeline and every
job's command are byte-identical to what the pre-registrations committed).

Adds, per the corresponding author's instructions of 2026-11-11:
  * adoption: on start, MyTrain/MyTest/external-script processes already running (e.g. children of a
    previous runner) are adopted and monitored, never killed or duplicated;
  * external Caus scripts from rebuild/REBUTTAL/EXTERNAL_JOBS/Caus/*.sh: '00_*' pilots run on the next free
    GPU; the others (at most 12) run in filename order after CDR SINet and the anchors and ahead of any EQ job
    not yet started; START/END/exit/GPU-h in status.txt; an interrupted script is re-run from scratch;
    GPU-hours counted separately from RL5B's;
  * hard cutoff: nothing new starts after 2026-11-17 06:00 IST (inference of a run trained before the
    cutoff completes that run, it is not a new job);
  * E3-e (priority 7) starts only if its projected end is before the cutoff;
  * disk rule: no job starts unless free disk >= projected footprint of everything not yet finished + 50 GB;
  * a state file rebuild/RL5B/out/runner_state.json each cycle (read by watchdog.sh).

Run: .venv/bin/python rebuild/RL5B/rl5b_runner.py --jobs rebuild/RL5B/queue_jobs.json [--dry-run]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import rl5b_queue as Q                                       # noqa: E402  (also puts rebuild/ABC on sys.path)

REPO = Q._REPO
CUTOFF = dt.datetime(2026, 11, 17, 6, 0, 0)
EXT_DIR = os.path.join(REPO, 'rebuild', 'REBUTTAL', 'EXTERNAL_JOBS', 'Caus')
EXT_STATUS = os.path.join(EXT_DIR, 'status.txt')
EXT_LOGS = os.path.join(EXT_DIR, 'runner_logs')
CAUS_WORKTREE = '/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD-Caus'
EXT_MAX = 12
EXT_PRIO_PILOT, EXT_PRIO = 0.0, 3.7
BANNED = ('rm -rf', 'rm -fr', 'git push', 'git reset', 'git checkout', 'git clean', 'crontab', 'sudo ',
          'shutdown', 'reboot', 'pkill', 'kill ')
FOOT_GB = {'abc_SINet': 3.1, 'abc_SINetv2': 3.0, 'custom_1': 0.7, 'custom_2': 3.1, 'external': 5.5}
DUR_H = {'abc_SINet': 1.82, 'abc_SINetv2': 2.08, 'custom_SINet_1': 0.70, 'custom_SINetv2_1': 0.85, 'custom_2': 1.82,
         'external': 1.82}
DISK_MARGIN_GB = 50.0
STATE = os.path.join(Q.OUT, 'runner_state.json')
PIDF = os.path.join(Q.OUT, 'queue.pid')


def now():
    return dt.datetime.now()


# Guard on training CODE. rl5b_queue.PIPELINE names the directory 'Src', so any new tracked file under it --
# e.g. the LICENSE moved to Src/LICENSE in commit 125cef0 -- tripped the guard and paused every launch
# (2026-11-11 21:40-23:2x). The refined guard diffs the same paths but only the .py files under Src/; every
# other guarded path is a single code/data file and is kept exactly.
GUARD_PATHS = [':(glob)Src/**/*.py' if p == 'Src' else p for p in Q.PIPELINE]


def guard(job):
    br = Q.git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if br != Q.BRANCH:
        return 'branch is %s, not %s' % (br, Q.BRANCH)
    r = Q.git('diff', '--quiet', job['commit'], '--', *GUARD_PATHS)
    if r.returncode != 0:
        return 'training code differs from campaign commit %s' % job['commit']
    return None


def say(m):
    print('[%s] %s' % (time.strftime('%m-%d %H:%M:%S'), m), flush=True)


# ---------------------------------------------------------------- footprint / duration estimates
def foot(job):
    if job['kind'] == 'external':
        return FOOT_GB['external']
    if job['kind'] == 'abc':
        return FOOT_GB['abc_%s' % job['arch']]
    return FOOT_GB['custom_%d' % job['iteration']]


def dur(job):
    if job['kind'] == 'external':
        return DUR_H['external']
    if job['kind'] == 'abc':
        return DUR_H['abc_%s' % job['arch']]
    return DUR_H['custom_2'] if job['iteration'] == 2 else DUR_H['custom_%s_1' % job['arch']]


# ---------------------------------------------------------------- external (Caus) scripts
def ext_events():
    ev = []
    if os.path.isfile(EXT_STATUS):
        for line in open(EXT_STATUS):
            p = line.rstrip('\n').split('\t')
            if len(p) >= 3:
                ev.append(p)
    return ev


def ext_write(*fields):
    os.makedirs(EXT_DIR, exist_ok=True)
    with open(EXT_STATUS, 'a') as fh:
        fh.write('\t'.join(str(f) for f in fields) + '\n')


def ext_state():
    """script -> 'done' | 'refused' | 'started' (START without END: running or interrupted)."""
    st = {}
    for p in ext_events():
        name, kind = p[0], p[1]
        if kind == 'START':
            st[name] = 'started'
        elif kind in ('END',):
            st[name] = 'done'
        elif kind == 'REFUSED':
            st[name] = 'refused'
        elif kind == 'INTERRUPTED':
            st[name] = 'interrupted'
    return st


def screen(path):
    txt = open(path, errors='replace').read()
    if not re.search(r'cd\s+["\']?%s' % re.escape(CAUS_WORKTREE), txt):
        return 'does not cd into %s' % CAUS_WORKTREE
    low = txt.lower()
    for b in BANNED:
        if b in low:
            return 'contains banned command %r' % b.strip()
    return None


def ext_jobs():
    if not os.path.isdir(EXT_DIR):
        return []
    st = ext_state()
    names = sorted(f for f in os.listdir(EXT_DIR) if f.endswith('.sh'))
    jobs, n_nonpilot = [], 0
    for f in names:
        pilot = f.startswith('00_')
        if not pilot:
            n_nonpilot += 1
        s = st.get(f)
        if s in ('done', 'refused'):
            continue
        if not pilot and n_nonpilot > EXT_MAX:
            ext_write(f, 'REFUSED', now().isoformat(timespec='seconds'), 'more than %d non-pilot scripts' % EXT_MAX)
            continue
        jobs.append(dict(id='CAUS:' + f, kind='external', campaign='caus', script=f,
                         priority=EXT_PRIO_PILOT if pilot else EXT_PRIO, state=s))
    return jobs


def start_external(job, gpu):
    path = os.path.join(EXT_DIR, job['script'])
    why = screen(path)
    if why:
        ext_write(job['script'], 'REFUSED', now().isoformat(timespec='seconds'), why)
        say('REFUSE %s: %s' % (job['script'], why))
        return None, None
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), RL5B_ASSIGNED_GPU=str(gpu))
    os.makedirs(EXT_LOGS, exist_ok=True)
    lg = open(os.path.join(EXT_LOGS, job['script'] + '.log'), 'a')
    lg.write('# %s START %s gpu %d sha256 %s\n' % (job['script'], now().isoformat(timespec='seconds'), gpu, sha))
    lg.flush()
    p = subprocess.Popen(['/bin/bash', path], cwd=EXT_DIR, env=env, stdout=lg, stderr=subprocess.STDOUT)
    ext_write(job['script'], 'START', now().isoformat(timespec='seconds'), 'gpu=%d' % gpu, 'sha256=%s' % sha, 'pid=%d' % p.pid)
    return p, lg


# ---------------------------------------------------------------- adoption
class Adopted:
    """A process this runner did not start (e.g. the child of a previous runner)."""
    def __init__(self, pid):
        self.pid = pid
        self.returncode = None

    def poll(self):
        try:
            with open('/proc/%d/stat' % self.pid) as fh:
                if fh.read().split()[2] == 'Z':
                    return 0
            return None
        except FileNotFoundError:
            return 0


class _NullLog:
    def close(self):
        pass


def scan_processes():
    out = []
    for p in os.listdir('/proc'):
        if not p.isdigit():
            continue
        try:
            cmd = open('/proc/%s/cmdline' % p, 'rb').read().split(b'\0')
            ppid = int(open('/proc/%s/stat' % p).read().split()[3])
            pcmd = open('/proc/%d/cmdline' % ppid, 'rb').read() if ppid > 1 else b''
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
            continue
        args = [c.decode(errors='replace') for c in cmd if c]
        if not args:
            continue
        joined = ' '.join(args)
        if ('MyTrain.py' in joined or 'MyTest.py' in joined) and b'MyTrain.py' not in pcmd and b'MyTest.py' not in pcmd:
            out.append((int(p), args))
        elif len(args) >= 2 and args[0].endswith('bash') and args[1].startswith(EXT_DIR) and args[1].endswith('.sh'):
            out.append((int(p), args))
    return out


def argval(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def adopt(jobs):
    """Map running processes to jobs. Returns {slot: running-entry}."""
    running = {}
    byid = {j['id']: j for j in jobs}
    for pid, args in scan_processes():
        gpu = None
        j, phase, ep = None, None, None
        if 'MyTrain.py' in ' '.join(args):
            gpu = int(argval(args, '--gpu'))
            snap = argval(args, '--save_model').strip('./').rstrip('/')
            for jj in jobs:
                s = (Q.A.snap_dir(Q.A.runid(jj['arch'], jj['arm'], jj['seed'])) if jj['kind'] == 'abc' else jj.get('snap', ''))
                if s and s.rstrip('/') == snap:
                    j = jj
            phase = 'train'
        elif 'MyTest.py' in ' '.join(args):
            gpu = int(argval(args, '--gpu'))
            mp = os.path.dirname(argval(args, '--model_path').strip('./'))
            ep = argval(args, '--dataset')
            for jj in jobs:
                s = (Q.A.snap_dir(Q.A.runid(jj['arch'], jj['arm'], jj['seed'])) if jj['kind'] == 'abc' else jj.get('snap', ''))
                if s and s.rstrip('/') == mp:
                    j = jj
            phase = 'infer'
        else:
            name = os.path.basename(args[1])
            try:
                env = open('/proc/%d/environ' % pid, 'rb').read().split(b'\0')
                gpu = int([e for e in env if e.startswith(b'RL5B_ASSIGNED_GPU=')][0].split(b'=')[1])
            except (IndexError, FileNotFoundError, ValueError):
                gpu = None
            j = byid.get('CAUS:' + name) or dict(id='CAUS:' + name, kind='external', campaign='caus', script=name, priority=EXT_PRIO)
            phase = 'external'
        if j is None or gpu is None:
            say('ADOPT: unmatched process %d (%s) -- left alone' % (pid, ' '.join(args)[:120]))
            continue
        slot = (gpu, 0)
        if slot in running:
            say('ADOPT: second process %d on GPU %d for %s -- left alone' % (pid, gpu, j['id']))
            continue
        ep_left = list(Q.ENDPOINTS[Q.ENDPOINTS.index(ep):]) if phase == 'infer' else list(Q.ENDPOINTS)
        running[slot] = dict(job=j, phase=phase, proc=Adopted(pid), lg=_NullLog(), ep_left=ep_left, adopted=True,
                             t0=time.time())
        say('ADOPT %-26s gpu %d pid %d phase %s%s' % (j['id'], gpu, pid, phase, (' ' + ep) if ep else ''))
        Q.event(kind='adopt', job=j['id'], gpu=gpu, pid=pid, phase=phase, endpoint=ep)
    return running


# ---------------------------------------------------------------- accounting
def gpu_hours():
    """RL5B GPU-h from queue_events (train_start -> train_ok/discard/gave_up, infer included), external from status."""
    rl5b = 0.0
    starts = {}
    if os.path.isfile(Q.EVENTS):
        for line in open(Q.EVENTS):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            t = dt.datetime.fromisoformat(e['at'])
            if e['kind'] in ('train_start',):
                starts[e['job']] = t
            elif e['kind'] in ('job_done', 'discard', 'gave_up', 'infer_failed') and e.get('job') in starts:
                rl5b += (t - starts.pop(e['job'])).total_seconds() / 3600
    caus = 0.0
    for p in ext_events():
        if p[1] == 'END':
            for f in p[3:]:
                if f.startswith('gpu_h='):
                    caus += float(f.split('=')[1])
    return dict(rl5b_completed_or_discarded=round(rl5b, 2), caus_completed=round(caus, 2))


# ---------------------------------------------------------------- main loop
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--gpus', default='0,1')
    ap.add_argument('--retries', type=int, default=1)
    ap.add_argument('--min-gpu-free-gb', type=float, default=24.0)
    ap.add_argument('--poll', type=int, default=30)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    Q.T.EXTRA_TRAIN_FLAGS = list(Q.ABC_FLAGS)
    assert Q.ABC_FLAGS == ['--save_ckpts', 'minimal', '--link_pool'], Q.ABC_FLAGS
    gpus = [int(g) for g in args.gpus.split(',')]
    slots = [(g, 0) for g in gpus]
    attempts, gave_up, done = {}, set(), set()
    jobs0 = [j for _, j in Q.load_jobs(args.jobs)] + ext_jobs()
    if not args.dry_run:
        with open(PIDF, 'w') as fh:
            fh.write(str(os.getpid()))
    running = adopt(jobs0) if not args.dry_run else {}
    # external scripts with START but no END that are not running now were interrupted -> re-run from scratch
    adopted_ext = {r['job']['script'] for r in running.values() if r['job']['kind'] == 'external'}
    if not args.dry_run:
        for name, s in ext_state().items():
            if s == 'started' and name not in adopted_ext:
                ext_write(name, 'INTERRUPTED', now().isoformat(timespec='seconds'), 're-run from scratch')
                say('external %s was interrupted -> will re-run from scratch' % name)
    say('runner v2 start: slots %s, cutoff %s, pipeline hash %s, adopted %d' % (slots, CUTOFF, Q.pipeline_hash(), len(running)))
    if not args.dry_run:
        Q.event(kind='runner_v2_start', slots=slots, pipeline_hash=Q.pipeline_hash(), adopted=len(running),
                head=Q.git('rev-parse', 'HEAD').stdout.strip())
    while True:
        jobs = [j for _, j in Q.load_jobs(args.jobs)] + ext_jobs()
        jobs.sort(key=lambda j: (j.get('priority', 100),))
        busy = {s['job']['id'] for s in running.values()}
        pending = []
        for j in jobs:
            if j['id'] in busy or j['id'] in gave_up or j['id'] in done:
                continue
            if j['kind'] == 'external':
                pending.append((j, False))
                continue
            ok, _ = Q.trained_ok(j)
            if ok and Q.infer_complete(j):
                done.add(j['id'])
                continue
            pending.append((j, ok))
        # gating: Caus non-pilot scripts and EQ only after every CDR SINet and anchor job has been launched
        early = [j for j, _ in pending if j.get('campaign') in ('cdr', 'e3c', 'bridge')]
        need_gb = sum(foot(j) for j, tr in pending if not tr) + sum(foot(s['job']) for s in running.values() if s['phase'] != 'infer')
        free_gb = shutil.disk_usage(REPO).free / 1e9
        hold = None
        if now() >= CUTOFF:
            hold = 'cutoff'
        elif free_gb < need_gb + DISK_MARGIN_GB:
            hold = 'disk: free %.0f GB < remaining %.0f GB + %.0f GB' % (free_gb, need_gb, DISK_MARGIN_GB)
        state = dict(at=now().isoformat(timespec='seconds'), pid=os.getpid(), hold=hold, free_gb=round(free_gb, 1),
                     need_gb=round(need_gb, 1), running={'gpu%d' % k[0]: dict(job=v['job']['id'], phase=v['phase'])
                                                         for k, v in running.items()},
                     pending_by_campaign={c: sum(1 for j, _ in pending if j.get('campaign') == c)
                                          for c in sorted({j.get('campaign') for j, _ in pending})},
                     done=len(done), gave_up=sorted(gave_up), gpu_hours=gpu_hours())
        if args.dry_run:
            print(json.dumps(state, indent=1))
            for j, tr in pending[:12]:
                say('PENDING %-28s %-7s prio %-4s %s' % (j['id'], j.get('campaign'), j.get('priority'),
                                                         'trained, needs inference' if tr else 'needs start'))
            say('done %d, pending %d' % (len(done), len(pending)))
            return
        tmp = STATE + '.tmp'
        json.dump(state, open(tmp, 'w'), indent=1)
        os.replace(tmp, STATE)
        for slot in slots:
            if slot in running or not pending:
                continue
            gpu = slot[0]
            # inference to finish an already-trained run is allowed even under a hold (it starts no new job)
            idx = next((i for i, (j, tr) in enumerate(pending) if tr), None)
            if hold and idx is None:
                break
            if Q.gpu_free_gb(gpu) < args.min_gpu_free_gb:
                continue
            if idx is None:
                cand = None
                for i, (j, tr) in enumerate(pending):
                    if j['kind'] == 'external' and j['priority'] > EXT_PRIO_PILOT and early:
                        continue
                    if j.get('campaign') == 'eq' and early:
                        continue
                    if j.get('campaign') == 'e3e' and now() + dt.timedelta(hours=dur(j)) > CUTOFF:
                        continue
                    cand = i
                    break
                if cand is None:
                    break
                idx = cand
            j, trained = pending.pop(idx)
            if j['kind'] != 'external':
                why = guard(j)
                if why:
                    say('PAUSE %s: %s' % (j['id'], why))
                    Q.event(kind='guard_pause', job=j['id'], why=why)
                    pending.insert(idx, (j, trained))
                    break
            if trained:
                p, lg = Q.start_infer(j, Q.ENDPOINTS[0], gpu)
                running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=list(Q.ENDPOINTS), t0=time.time())
                continue
            if j['kind'] == 'external':
                p, lg = start_external(j, gpu)
                if p is None:
                    continue
                running[slot] = dict(job=j, phase='external', proc=p, lg=lg, ep_left=[], t0=time.time())
                say('EXT   %-26s gpu %d pid %d' % (j['id'], gpu, p.pid))
                continue
            ok, why = Q.ready(j)
            if not ok:
                Q.discard(j, 'pre-launch: ' + why)
                ok, why = Q.ready(j)
            if not ok:
                say('SKIP %s -- %s' % (j['id'], why))
                Q.event(kind='not_launchable', job=j['id'], why=why)
                gave_up.add(j['id'])
                continue
            p, lg = Q.start_train(j, gpu)
            say('TRAIN %-26s gpu %d pid %d' % (j['id'], gpu, p.pid))
            Q.event(kind='train_start', job=j['id'], gpu=gpu, pid=p.pid, head=Q.git('rev-parse', 'HEAD').stdout.strip(),
                    pipeline_hash=Q.pipeline_hash(), campaign=j.get('campaign'), commit=j['commit'])
            running[slot] = dict(job=j, phase='train', proc=p, lg=lg, ep_left=list(Q.ENDPOINTS), t0=time.time())
        time.sleep(args.poll)
        for slot in list(running):
            s = running[slot]
            if s['proc'].poll() is None:
                continue
            s['lg'].close()
            j, gpu = s['job'], slot[0]
            rc = s['proc'].returncode
            if s['phase'] == 'external':
                gh = (time.time() - s['t0']) / 3600
                ext_write(j['script'], 'END', now().isoformat(timespec='seconds'),
                          'exit=%s' % ('unknown(adopted)' if s.get('adopted') else rc), 'gpu_h=%.3f' % gh)
                say('EXT END %s exit %s (%.2f GPU-h)' % (j['script'], rc, gh))
                del running[slot]
                continue
            if s['phase'] == 'train':
                ok, d = Q.trained_ok(j)
                n = attempts.get(j['id'], 0) + 1
                attempts[j['id']] = n
                if ok and (rc in (0, None)):
                    say('OK    %-26s wall %.1fm n_appended %s best_epoch %s' % (j['id'], d['wall_min'], d['n_appended'], d['best_epoch']))
                    Q.event(kind='train_ok', job=j['id'], verify=d)
                    p, lg = Q.start_infer(j, s['ep_left'][0], gpu)
                    running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=s['ep_left'], t0=time.time())
                else:
                    why = 'rc=%s failed=%s' % (rc, d.get('failed_checks') or d.get('fail'))
                    Q.discard(j, why)
                    del running[slot]
                    if n > args.retries:
                        gave_up.add(j['id'])
                        say('GIVE UP %s after %d attempts (%s)' % (j['id'], n, why))
                        Q.event(kind='gave_up', job=j['id'], attempts=n, why=why)
                    else:
                        say('RETRY %s same seed (attempt %d): %s' % (j['id'], n + 1, why))
            else:
                ep = s['ep_left'].pop(0)
                out = os.path.join(REPO, Q.pred_dir(j, ep))
                gtn = len(os.listdir(os.path.join(REPO, 'Dataset/Test/%s/GT' % ep)))
                complete = os.path.isdir(out) and len(os.listdir(out)) == gtn
                Q.event(kind='infer_done', job=j['id'], endpoint=ep, rc=rc, complete=complete)
                if not complete:
                    s['ep_left'].insert(0, ep)
                    if s.get('adopted') or rc in (None, 0):
                        p, lg = Q.start_infer(j, ep, gpu)
                        running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=s['ep_left'], t0=time.time())
                        continue
                    say('INFER FAIL %s %s rc=%s' % (j['id'], ep, rc))
                    del running[slot]
                    gave_up.add(j['id'])
                    Q.event(kind='infer_failed', job=j['id'], endpoint=ep)
                elif s['ep_left']:
                    p, lg = Q.start_infer(j, s['ep_left'][0], gpu)
                    running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=s['ep_left'], t0=time.time())
                else:
                    say('DONE  %s (trained + inferred)' % j['id'])
                    Q.event(kind='job_done', job=j['id'])
                    done.add(j['id'])
                    del running[slot]


if __name__ == '__main__':
    main()

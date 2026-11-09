#!/usr/bin/env python
"""RL5B rebuttal -- one priority queue for every new training campaign (bridge, E3, CDR, EQ, ...).

Runs, never scores. For each job it trains, verifies, and then runs inference on COD10K-test and
NC4K in the same GPU slot. Scoring happens only after a campaign is complete, with the campaign's
pre-committed analysis script, so nothing is looked at mid-campaign.

Jobs live in an append-only JSON file (--jobs). A campaign's jobs are appended only after its
pre-registration is committed; each job carries that commit. The file is re-read every cycle, so a
campaign can be added while the queue runs.

Job kinds
  abc     an ABC-pipeline run (arch, arm, seed): pools, paths, command, verification and inference
          are rebuild/ABC's own (abc_train.launch / verify_run / discard, abc_evaluate.infer_start),
          with EXTRA_TRAIN_FLAGS = --save_ckpts minimal --link_pool (footprint only).
  custom  an explicit run outside the ABC namespace (the bridge re-train; supervised baselines):
          every path, the command and the expected verification values are in the job itself.

Guards before every launch (the queue pauses, never skips, when one fails)
  * branch is rebuttal/iclr27/wip2 and the pipeline files are unchanged since the job's commit
    (git diff --quiet <commit> -- PIPELINE);
  * free disk >= --min-free-gb (shared machine);
  * the GPU has >= --min-gpu-free-gb free memory (never OOM another user's job).
A run that fails verification is discarded and re-run from scratch with the SAME seed (once by
default); it is never replaced by a new seed and never dropped silently.

Usage
  .venv/bin/python rebuild/RL5B/rl5b_queue.py --jobs rebuild/RL5B/queue_jobs.json [--dry-run]
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
for _p in (os.path.join(_REPO, 'rebuild', 'ABC'), os.path.join(_REPO, 'rebuild'), _REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402
import abc_train as T                                         # noqa: E402
import abc_evaluate as E                                      # noqa: E402

PY = '.venv/bin/python'
BRANCH = 'rebuttal/iclr27/wip2'
PIPELINE = ['MyTrain.py', 'MyTest.py', 'CLS.py', 'Src', 'Eval/metrics.py', 'rebuild/common.py',
            'rebuild/C1/c1_space.py', 'rebuild/C1/c1_targeted_vs_random.py', 'rebuild/ABC/abc_common.py',
            'rebuild/ABC/abc_train.py', 'rebuild/ABC/abc_evaluate.py', 'rebuild/ABC/out/cdr/cdr_permutations.json',
            'rebuild/RL5B/rl5b_queue.py']
ABC_FLAGS = ['--save_ckpts', 'minimal', '--link_pool']
ENDPOINTS = ('COD10K', 'NC4K')
OUT = os.path.join(_REPO, 'rebuild', 'RL5B', 'out')
EVENTS = os.path.join(OUT, 'queue_events.jsonl')
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]')
EPOCH = re.compile(r'Epoch Num: (\d+/\d+)')
STEP = re.compile(r'Global Step: \d+/(\d+)')


def now():
    return datetime.datetime.now().isoformat(timespec='seconds')


def say(m):
    print('[%s] %s' % (time.strftime('%m-%d %H:%M:%S'), m), flush=True)


def event(**kw):
    os.makedirs(OUT, exist_ok=True)
    with open(EVENTS, 'a') as fh:
        fh.write(json.dumps(dict(at=now(), **kw)) + '\n')


def git(*args):
    return subprocess.run(['git', '-C', _REPO] + list(args), capture_output=True, text=True)


def pipeline_hash():
    h = hashlib.sha256()
    for p in PIPELINE:
        r = git('ls-files', '-s', '--', p)
        h.update(r.stdout.encode())
        full = os.path.join(_REPO, p)
        files = [full] if os.path.isfile(full) else sorted(
            os.path.join(d, f) for d, _, fs in os.walk(full) for f in fs if f.endswith('.py'))
        for f in files:
            if os.path.isfile(f):
                h.update(open(f, 'rb').read())
    return h.hexdigest()[:16]


def guard(job):
    br = git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    if br != BRANCH:
        return 'branch is %s, not %s' % (br, BRANCH)
    r = git('diff', '--quiet', job['commit'], '--', *PIPELINE)
    if r.returncode != 0:
        return 'pipeline files differ from campaign commit %s' % job['commit']
    return None


def disk_free_gb():
    return shutil.disk_usage(_REPO).free / 1e9


def gpu_free_gb(gpu):
    r = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits', '-i', str(gpu)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip()) / 1024
    except ValueError:
        return 0.0


# ---------------------------------------------------------------- custom jobs
def custom_cmd(job, gpu):
    c = [PY, 'MyTrain.py', '--network', job['network'], '--task', 'S2C', '--method', job['method'],
         '--iteration', str(job['iteration']), '--seed', str(job['seed']),
         '--save_model', './' + job['snap'] + '/', '--source_root', './' + job['pool'] + '/',
         '--target_root', './Dataset/Target/', '--val_root', './Dataset/Val/CAMO/'] + job.get('extra', []) + \
        ['--gpu', str(gpu)]
    return c


def custom_verify(job):
    snap = os.path.join(_REPO, job['snap'])
    tl = os.path.join(snap, 'training_log.log')
    d = dict(runid=job['id'])
    if not os.path.isfile(tl):
        return False, dict(d, fail='no training_log.log')
    lines = open(tl).read().splitlines()
    d['rounds'] = sum(1 for l in lines if l.startswith('Training Log'))
    d['total_step_set'] = ','.join(sorted({m.group(1) for l in lines for m in [STEP.search(l)] if m}))
    ep = [m.group(1) for l in lines for m in [EPOCH.search(l)] if m]
    d['last_epoch'] = ep[-1] if ep else ''
    st = [datetime.datetime.fromisoformat(m.group(1)) for l in lines for m in [TS.match(l)] if m]
    d['wall_min'] = round((st[-1] - st[0]).total_seconds() / 60, 1) if st else None
    run = open(os.path.join(_REPO, job['log'])).read() if os.path.isfile(os.path.join(_REPO, job['log'])) else ''
    loaded = [int(x) for x in re.findall(r'Loaded (\d+) image-mask pairs', run)]
    d['pool_r1'] = loaded[0] if loaded else None
    d['pool_r2'] = loaded[1] if len(loaded) > 1 else None
    d['n_appended'] = (loaded[1] - loaded[0]) if len(loaded) > 1 else None
    be = re.findall(r'Best epoch:(\d+)', run)
    d['best_epoch'] = int(be[-1]) if be else None
    ex = job['expect']
    checks = dict(rounds=d['rounds'] == ex['rounds'], total_step=d['total_step_set'] == ex['total_step'],
                  last_epoch=d['last_epoch'] == ex['last_epoch'],
                  ckpt=os.path.isfile(os.path.join(snap, job['ckpt'])), pool_r1=d['pool_r1'] == ex['pool_r1'])
    d['checks'] = checks
    d['failed_checks'] = [k for k, v in checks.items() if not v]
    return not d['failed_checks'], d


def custom_ready(job):
    pool = os.path.join(_REPO, job['pool'])
    if not os.path.isdir(os.path.join(pool, 'Image')):
        return False, 'pool missing: %s' % job['pool']
    if os.path.exists(os.path.join(_REPO, job['pool'].rstrip('/') + '_iteration2')):
        return False, 'stale CLS output'
    snap = os.path.join(_REPO, job['snap'])
    if os.path.isdir(snap) and [f for f in os.listdir(snap) if f.endswith('.pth')]:
        return False, 'snapshot dir already holds .pth'
    return True, ''


def custom_discard(job, why):
    for p in (job['snap'], job['pool'].rstrip('/') + '_iteration2'):
        full = os.path.join(_REPO, p)
        if os.path.exists(full):
            shutil.rmtree(full)
    event(kind='discard', job=job['id'], why=why)


# ---------------------------------------------------------------- generic
def pred_dir(job, ep):
    if job['kind'] == 'abc':
        return A.pred_dir(A.runid(job['arch'], job['arm'], job['seed']), ep)
    return os.path.join(job['pred_root'], ep)


def infer_complete(job):
    for ep in ENDPOINTS:
        out = os.path.join(_REPO, pred_dir(job, ep))
        gtn = len(os.listdir(os.path.join(_REPO, 'Dataset/Test/%s/GT' % ep)))
        if not (os.path.isdir(out) and len(os.listdir(out)) == gtn):
            return False
    return True


def trained_ok(job):
    if job['kind'] == 'abc':
        return T.verify_run(job['arch'], job['arm'], job['seed'])
    return custom_verify(job)


def start_train(job, gpu):
    if job['kind'] == 'abc':
        p, lg = T.launch(job['arch'], job['arm'], job['seed'], gpu)
        return p, lg
    cmd = custom_cmd(job, gpu)
    os.makedirs(os.path.join(_REPO, job['snap']), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.join(_REPO, job['log'])), exist_ok=True)
    lg = open(os.path.join(_REPO, job['log']), 'w')
    lg.write('# RUNID   %s\n# started %s\n# commit  %s\n# CMD     %s\n\n' % (job['id'], C.now(), C.git_commit(), ' '.join(cmd)))
    lg.flush()
    return subprocess.Popen(cmd, cwd=_REPO, stdout=lg, stderr=subprocess.STDOUT), lg


def start_infer(job, ep, gpu):
    if job['kind'] == 'abc':
        return E.infer_start(job['arch'], job['arm'], job['seed'], ep, gpu)
    ck = './' + os.path.join(job['snap'], job['ckpt'])
    cmd = [PY, 'MyTest.py', '--network', job['network'], '--gpu', str(gpu), '--dataset', ep,
           '--model_path', ck, '--test_save', './' + pred_dir(job, ep)]
    lg = open(os.path.join(_REPO, job['log'].replace('.log', '_infer_%s.log' % ep)), 'w')
    return subprocess.Popen(cmd, cwd=_REPO, stdout=lg, stderr=subprocess.STDOUT), lg


def ready(job):
    if job['kind'] == 'abc':
        return T.assert_ready(job['arch'], job['arm'], job['seed'])
    return custom_ready(job)


def discard(job, why):
    if job['kind'] == 'abc':
        journal = []
        T.discard(job['arch'], job['arm'], job['seed'], why, journal)
        event(kind='discard', job=job['id'], why=why)
    else:
        custom_discard(job, why)


def load_jobs(path):
    jobs = json.load(open(path))['jobs']
    for j in jobs:
        if j['kind'] == 'abc':
            j.setdefault('id', A.runid(j['arch'], j['arm'], j['seed']))
    return sorted(enumerate(jobs), key=lambda x: (x[1].get('priority', 100), x[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--gpus', default='0,1')
    ap.add_argument('--slots-per-gpu', type=int, default=1)
    ap.add_argument('--retries', type=int, default=1)
    ap.add_argument('--min-free-gb', type=float, default=150.0)
    ap.add_argument('--min-gpu-free-gb', type=float, default=24.0)
    ap.add_argument('--poll', type=int, default=30)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    T.EXTRA_TRAIN_FLAGS = list(ABC_FLAGS)
    gpus = [int(g) for g in args.gpus.split(',')]
    slots = [(g, i) for g in gpus for i in range(args.slots_per_gpu)]
    running = {}          # slot -> dict(job, phase, proc, lg, ep_left)
    attempts, gave_up, done = {}, set(), set()
    say('queue start: slots %s, pipeline hash %s' % (slots, pipeline_hash()))
    event(kind='queue_start', slots=slots, pipeline_hash=pipeline_hash(), head=git('rev-parse', 'HEAD').stdout.strip())
    while True:
        jobs = load_jobs(args.jobs)
        busy = {s['job']['id'] for s in running.values()}
        pending = []
        for _, j in jobs:
            if j['id'] in busy or j['id'] in gave_up or j['id'] in done:
                continue
            ok, _ = trained_ok(j)
            if ok and infer_complete(j):
                done.add(j['id'])
                continue
            pending.append((j, ok))
        if args.dry_run:
            for j, ok in pending:
                say('PENDING %-26s %-8s prio %-3s %s' % (j['id'], j.get('campaign'), j.get('priority', 100),
                                                         'trained, needs inference' if ok else 'needs training'))
            say('done %d, pending %d' % (len(done), len(pending)))
            return
        # fill free slots
        for slot in slots:
            if slot in running or not pending:
                continue
            gpu = slot[0]
            if disk_free_gb() < args.min_free_gb:
                say('PAUSE disk free %.0f GB < %.0f GB' % (disk_free_gb(), args.min_free_gb))
                break
            if gpu_free_gb(gpu) < args.min_gpu_free_gb:
                continue
            j, trained = pending.pop(0)
            why = guard(j)
            if why:
                say('PAUSE %s: %s' % (j['id'], why))
                event(kind='guard_pause', job=j['id'], why=why)
                pending.insert(0, (j, trained))
                break
            if trained:          # inference only (e.g. after a queue restart)
                ep_left = [ep for ep in ENDPOINTS]
                p, lg = start_infer(j, ep_left[0], gpu)
                running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=ep_left)
                continue
            ok, why = ready(j)
            if not ok:
                discard(j, 'pre-launch: ' + why)
                ok, why = ready(j)
            if not ok:
                say('SKIP %s -- %s' % (j['id'], why))
                event(kind='not_launchable', job=j['id'], why=why)
                gave_up.add(j['id'])
                continue
            p, lg = start_train(j, gpu)
            say('TRAIN %-26s gpu %d pid %d' % (j['id'], gpu, p.pid))
            event(kind='train_start', job=j['id'], gpu=gpu, pid=p.pid, head=git('rev-parse', 'HEAD').stdout.strip(),
                  pipeline_hash=pipeline_hash(), campaign=j.get('campaign'), commit=j['commit'])
            running[slot] = dict(job=j, phase='train', proc=p, lg=lg, ep_left=list(ENDPOINTS))
        if not running and not pending:
            say('queue idle: all jobs done or given up (done %d, gave up %d); waiting for new jobs' % (len(done), len(gave_up)))
        time.sleep(args.poll)
        for slot in list(running):
            s = running[slot]
            if s['proc'].poll() is None:
                continue
            s['lg'].close()
            j, gpu = s['job'], slot[0]
            if s['phase'] == 'train':
                ok, d = trained_ok(j)
                rc = s['proc'].returncode
                n = attempts.get(j['id'], 0) + 1
                attempts[j['id']] = n
                if ok and rc == 0:
                    say('OK    %-26s wall %.1fm n_appended %s best_epoch %s' % (j['id'], d['wall_min'], d['n_appended'], d['best_epoch']))
                    event(kind='train_ok', job=j['id'], verify=d)
                    p, lg = start_infer(j, s['ep_left'][0], gpu)
                    running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=s['ep_left'])
                else:
                    why = 'rc=%s failed=%s' % (rc, d.get('failed_checks') or d.get('fail'))
                    discard(j, why)
                    del running[slot]
                    if n > args.retries:
                        gave_up.add(j['id'])
                        say('GIVE UP %s after %d attempts (%s)' % (j['id'], n, why))
                        event(kind='gave_up', job=j['id'], attempts=n, why=why)
                    else:
                        say('RETRY %s same seed (attempt %d): %s' % (j['id'], n + 1, why))
            else:
                ep = s['ep_left'].pop(0)
                event(kind='infer_done', job=j['id'], endpoint=ep, rc=s['proc'].returncode)
                if s['proc'].returncode != 0:
                    say('INFER FAIL %s %s rc=%s' % (j['id'], ep, s['proc'].returncode))
                    del running[slot]
                    gave_up.add(j['id'])
                    event(kind='infer_failed', job=j['id'], endpoint=ep)
                elif s['ep_left']:
                    p, lg = start_infer(j, s['ep_left'][0], gpu)
                    running[slot] = dict(job=j, phase='infer', proc=p, lg=lg, ep_left=s['ep_left'])
                else:
                    say('DONE  %s (trained + inferred)' % j['id'])
                    event(kind='job_done', job=j['id'])
                    done.add(j['id'])
                    del running[slot]


if __name__ == '__main__':
    main()

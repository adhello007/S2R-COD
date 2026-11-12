#!/usr/bin/env python
"""CAUS EXP-01 -- one full two-round SINet run for one (arm, seed). Called by one queue script.

Order (rebuild/CAUS/PREREGISTRATION_EXP01.md §5). Any failure exits non-zero, keeps everything:
  1. fresh run folder Result/CAUS_RUNS/<script>/<UTC stamp>_<pid>/   (never reused)
  2. environment record + disk and GPU-memory guards (so a shared-GPU job is never OOM'd)
  3. pool built from leaf symlinks and gated; committed gates G3/G4/G6
  4. MyTrain.py with the committed SINet command line (paths only differ)
  5. completion assertions of abc_train.verify_run
  6. MyTest.py on COD10K and NC4K
  7. run_record.json with every hash
Exit codes: 0 ok | 2 pre-training gate failed | 3 training failed / incomplete |
            4 inference failed | 5 guard (disk / GPU memory) -- RECOVERABLE, ask for a retry.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402
import exp01_alloc as X                                        # noqa: E402
import exp01_pool as P                                         # noqa: E402

SPEC = dict(network='SINet', batch=16, total_step=253, last_epoch='039/040', ref_min=104.5)
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]')
EPOCH = re.compile(r'Epoch Num: (\d+/\d+)')
STEP = re.compile(r'Global Step: \d+/(\d+)')
MIN_FREE_DISK_GB = 25          # one SINet run ~5.5 GB; generous headroom
MIN_FREE_GPU_GB = 24           # SINet bs16 at 352 needs well under this
GPU_WAIT_MIN = 45


def log(fh, m):
    line = '[%s] %s' % (datetime.datetime.now().isoformat(timespec='seconds'), m)
    print(line, flush=True)
    fh.write(line + '\n')
    fh.flush()


def _proc_start(pid):
    """Process start time in clock ticks since boot (field 22 of /proc/<pid>/stat), or None."""
    try:
        s = open('/proc/%d/stat' % pid).read()
        return int(s[s.rindex(')') + 2:].split()[19])
    except (OSError, ValueError, IndexError):
        return None


def _boot_id():
    try:
        return open('/proc/sys/kernel/random/boot_id').read().strip()
    except OSError:
        return 'unknown'


def acquire_lock(script):
    """One live instance per queue script (PREREGISTRATION_EXP01.md Addendum A1).

    The queue runner was observed (pilot, 2026-11-12) to re-run a script it had recorded as
    INTERRUPTED while the original process was still alive, so two copies ran concurrently. A start
    that finds a LIVE holder (same boot, same pid, same process start time, cmdline naming this
    script) yields with exit 6 and trains nothing. A stale lock (dead holder, or a different boot) is
    renamed aside, never deleted, and the new start proceeds."""
    d = os.path.join(K.RUNS_ROOT, script)
    K.assert_writable(d)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, 'RUN_LOCK.json')
    me = dict(pid=os.getpid(), proc_start=_proc_start(os.getpid()), boot_id=_boot_id(),
              script=script, acquired=K.now())
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, 'w') as fh:
                json.dump(me, fh)
            return True, me, None
        except FileExistsError:
            try:
                held = json.load(open(path))
            except (OSError, ValueError):
                held = {}
            pid = int(held.get('pid', -1))
            alive = (held.get('boot_id') == me['boot_id'] and pid > 0
                     and _proc_start(pid) == held.get('proc_start')
                     and script in open('/proc/%d/cmdline' % pid).read().replace('\0', ' ')
                     if os.path.exists('/proc/%d' % pid) else False)
            if alive:
                return False, me, held
            os.rename(path, os.path.join(d, 'RUN_LOCK.stale.%s.json'
                                         % datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
    raise SystemExit('EXP01 HALT: could not acquire %s' % path)


def new_run_dir(script):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    d = os.path.join(K.RUNS_ROOT, script, '%s_%d' % (stamp, os.getpid()))
    K.assert_writable(d)
    os.makedirs(os.path.join(d, 'logs'))
    return d


def env_record(gpu):
    import torch
    d = dict(host_time=K.now(), git=K.git_head(), python=sys.executable,
             torch=torch.__version__, cuda=torch.version.cuda,
             cudnn=torch.backends.cudnn.version(),
             cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
             runner_assigned_gpu=os.environ.get('RL5B_ASSIGNED_GPU'),
             disk_free_gb=round(shutil.disk_usage(K.REPO).free / 2 ** 30, 1))
    if torch.cuda.is_available():
        free, tot = torch.cuda.mem_get_info(gpu)
        d.update(gpu_name=torch.cuda.get_device_name(gpu), gpu_free_gb=round(free / 2 ** 30, 1),
                 gpu_total_gb=round(tot / 2 ** 30, 1))
    try:
        d['nvidia_smi'] = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader'], text=True).strip().splitlines()
    except Exception as e:                                     # pragma: no cover
        d['nvidia_smi'] = str(e)
    return d


def guards(gpu, fh):
    import torch
    free = shutil.disk_usage(K.REPO).free / 2 ** 30
    if free < MIN_FREE_DISK_GB:
        log(fh, 'GUARD: free disk %.1f GB < %d GB' % (free, MIN_FREE_DISK_GB))
        return False
    t0 = time.time()
    while True:
        f, _ = torch.cuda.mem_get_info(gpu)
        if f / 2 ** 30 >= MIN_FREE_GPU_GB:
            log(fh, 'guards ok: disk %.1f GB free, GPU %.1f GB free' % (free, f / 2 ** 30))
            return True
        if time.time() - t0 > GPU_WAIT_MIN * 60:
            log(fh, 'GUARD: GPU free %.1f GB < %d GB after %d min' % (f / 2 ** 30, MIN_FREE_GPU_GB, GPU_WAIT_MIN))
            return False
        time.sleep(60)


def verify(train_log, snap):
    """abc_train.verify_run, against this run's own paths."""
    tl = os.path.join(snap, 'training_log.log')
    d = {}
    if not os.path.isfile(tl):
        return False, dict(fail='no training_log.log')
    lines = open(tl).read().splitlines()
    d['rounds'] = sum(1 for l in lines if l.startswith('Training Log'))
    d['total_step_set'] = ','.join(sorted({m.group(1) for l in lines for m in [STEP.search(l)] if m}))
    ep = [m.group(1) for l in lines for m in [EPOCH.search(l)] if m]
    d['last_epoch'] = ep[-1] if ep else ''
    st = [datetime.datetime.fromisoformat(m.group(1)) for l in lines for m in [TS.match(l)] if m]
    d['wall_min'] = round((st[-1] - st[0]).total_seconds() / 60, 1) if st else None
    d['tea_best'] = os.path.isfile(os.path.join(snap, 'Tea_epoch_best.pth'))
    run = open(train_log).read()
    loaded = [int(x) for x in re.findall(r'Loaded (\d+) image-mask pairs', run)]
    d['pool_r1'] = loaded[0] if loaded else None
    d['pool_r2'] = loaded[1] if len(loaded) > 1 else None
    d['n_appended'] = (d['pool_r2'] - d['pool_r1']) if len(loaded) > 1 else None
    d['target_loaded_4040'] = run.count('Loaded 4040 images')
    be = re.findall(r'Best epoch:(\d+)', run)
    d['best_epoch'] = int(be[-1]) if be else None
    checks = dict(rounds=d['rounds'] == 2, total_step=d['total_step_set'] == '%04d' % SPEC['total_step'],
                  last_epoch=d['last_epoch'] == SPEC['last_epoch'], tea_best=bool(d['tea_best']),
                  wall=bool(d['wall_min'] is not None and d['wall_min'] < 2 * SPEC['ref_min']),
                  pool_r1=d['pool_r1'] == P.N_BASE + X.BUDGET, target=d['target_loaded_4040'] == 2)
    d['checks'] = checks
    d['failed_checks'] = [k for k, v in checks.items() if not v]
    return not d['failed_checks'], d


def train_cmd(seed, snap, pool, gpu, extra=()):
    rel = lambda p: './' + os.path.relpath(p, K.REPO) + '/'      # noqa: E731
    return [K.PY, 'MyTrain.py', '--network', 'SINet', '--task', 'S2C', '--method', 'ours',
            '--iteration', '2', '--seed', str(seed), '--save_model', rel(snap),
            '--source_root', rel(pool), '--target_root', './Dataset/Target/',
            '--val_root', './Dataset/Val/CAMO/', '--gpu', str(gpu)] + list(extra)


def infer(ckpt, out_dir, endpoint, gpu, logpath, timeout=None):
    cmd = [K.PY, 'MyTest.py', '--network', 'SINet', '--gpu', str(gpu), '--dataset', endpoint,
           '--model_path', ckpt, '--test_save', out_dir]
    K.assert_writable(out_dir)
    with open(logpath, 'w') as lg:
        lg.write('# CMD %s\n' % ' '.join(cmd))
        lg.flush()
        rc = subprocess.run(cmd, cwd=K.REPO, stdout=lg, stderr=subprocess.STDOUT, timeout=timeout).returncode
    n_gt = len(os.listdir(os.path.join(K.REPO, 'Dataset/Test', endpoint, 'GT')))
    n = len(os.listdir(out_dir)) if os.path.isdir(out_dir) else 0
    return rc, n, n_gt


def dir_digest(d):
    return K.list_digest(['%s %s' % (K.sha256(os.path.join(d, n)), n) for n in sorted(os.listdir(d))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', required=True, choices=X.TRAINED_ARMS)
    ap.add_argument('--seed', type=int, required=True, choices=X.SEEDS)
    ap.add_argument('--script', required=True, help='queue script name; names the run folder')
    ap.add_argument('--gpu', type=int, default=0)
    args = ap.parse_args()
    rid = 'SINet_%s_s%d' % (args.arm, args.seed)
    ok_lock, me, held = acquire_lock(args.script)
    if not ok_lock:
        rec = dict(runid=rid, script=args.script, status='DUPLICATE START YIELDED', at=K.now(),
                   this_start=me, live_holder=held)
        K.save_json(os.path.join(K.RUNS_ROOT, args.script, 'duplicate_start_%d.json' % os.getpid()), rec)
        print('EXP-01 %s: a live instance (pid %s) already holds this script; yielding, nothing trained'
              % (rid, held.get('pid')), flush=True)
        sys.exit(6)
    run = new_run_dir(args.script)
    L = os.path.join(run, 'logs')
    fh = open(os.path.join(L, 'driver.log'), 'w')
    rec = dict(runid=rid, campaign='EXP-01', arm=args.arm, arm_display=X.DISPLAY[args.arm],
               seed=args.seed, script=args.script, run_dir=os.path.relpath(run, K.REPO),
               started=K.now(), git=K.git_head(),
               oracle_score_source=('endpoint-label-leaky (shape only)' if args.arm.endswith('SHUF')
                                    else 'endpoint-label-leaky'))
    log(fh, 'EXP-01 %s in %s' % (rid, run))
    env = env_record(args.gpu)
    K.save_json(os.path.join(L, 'env.json'), env)
    if not guards(args.gpu, fh):
        rec.update(status='GUARD', ended=K.now())
        K.save_json(os.path.join(run, 'run_record.json'), rec)
        sys.exit(5)

    pool, stems = P.build(run, args.arm, args.seed)
    pg = P.gate(pool, args.arm, args.seed, stems)
    tg = P.trainer_gates()
    K.save_json(os.path.join(L, 'pool_gate.json'), dict(pool=pg, trainer=tg))
    log(fh, 'pool gate %s | trainer gates %s' % (pg['passed'], tg['passed']))
    if not (pg['passed'] and tg['passed']):
        rec.update(status='PRE-TRAINING GATE FAILED', ended=K.now())
        K.save_json(os.path.join(run, 'run_record.json'), rec)
        sys.exit(2)

    snap = os.path.join(run, 'snap')
    cmd = train_cmd(args.seed, snap, pool, args.gpu)
    tlog = os.path.join(L, 'train.log')
    with open(tlog, 'w') as lg:
        lg.write('# RUNID   %s\n# started %s\n# commit  %s\n# CMD     %s\n\n'
                 % (rid, K.now(), K.git_head(), ' '.join(cmd)))
        lg.flush()
        log(fh, 'train: %s' % ' '.join(cmd))
        rc = subprocess.run(cmd, cwd=K.REPO, stdout=lg, stderr=subprocess.STDOUT).returncode
    ok, vd = verify(tlog, snap)
    vd['returncode'] = rc
    K.save_json(os.path.join(L, 'verify.json'), vd)
    log(fh, 'train rc=%d verify ok=%s failed=%s' % (rc, ok, vd.get('failed_checks') or vd.get('fail')))
    if rc != 0 or not ok:
        rec.update(status='TRAINING FAILED OR INCOMPLETE', ended=K.now(), verify=vd)
        K.save_json(os.path.join(run, 'run_record.json'), rec)
        sys.exit(3)

    ck = os.path.join(snap, 'Tea_epoch_best.pth')
    preds = {}
    for ep in ('COD10K', 'NC4K'):
        out = os.path.join(run, 'pred', ep)
        irc, n, n_gt = infer('./' + os.path.relpath(ck, K.REPO), out, ep, args.gpu,
                             os.path.join(L, 'infer_%s.log' % ep))
        preds[ep] = dict(rc=irc, n=n, n_gt=n_gt, dir=os.path.relpath(out, K.REPO))
        log(fh, 'infer %s rc=%d n=%d/%d' % (ep, irc, n, n_gt))
        if irc != 0 or n != n_gt:
            rec.update(status='INFERENCE FAILED', ended=K.now(), verify=vd, predictions=preds)
            K.save_json(os.path.join(run, 'run_record.json'), rec)
            sys.exit(4)
        preds[ep]['digest'] = dir_digest(out)

    it2 = pool.rstrip('/') + '_iteration2'
    rec.update(status='COMPLETE', ended=K.now(), verify=vd, predictions=preds,
               pool_gate=dict(stems_sha256=pg['stems_sha256'], image_list_sha256=pg['image_list_sha256']),
               round2_pool=dict(dir=os.path.relpath(it2, K.REPO),
                                n_image=len(os.listdir(os.path.join(it2, 'Image'))) if os.path.isdir(it2) else None,
                                image_list_sha256=K.list_digest(os.listdir(os.path.join(it2, 'Image')))
                                if os.path.isdir(it2) else None),
               tea_best_sha256=K.sha256(ck), stu40_sha256=K.sha256(os.path.join(snap, 'Stu_40.pth')),
               train_log_sha256=K.sha256(os.path.join(snap, 'training_log.log')),
               env=dict((k, env.get(k)) for k in ('gpu_name', 'torch', 'cuda', 'cudnn', 'runner_assigned_gpu')))
    K.save_json(os.path.join(run, 'run_record.json'), rec)
    log(fh, 'COMPLETE %s' % rid)


if __name__ == '__main__':
    main()

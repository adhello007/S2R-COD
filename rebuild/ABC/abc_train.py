#!/usr/bin/env python
"""ABC -- the training DRIVER, and EXP ABC block #2 (run accounting).

This is a driver, NOT a second trainer. It builds command strings from the run
table and executes the single in-tree MyTrain.py. The commands are written to
rebuild/ABC/out/abc_commands.txt BEFORE execution, so what ran is auditable text.
A second copy of MyTrain.py anywhere in the tree is a gate failure (G3).

Two runs at a time, one per GPU. No two runs can share a source_root -- RUNID
makes that impossible (ABC_PLAN.md A.2) -- and the driver asserts the pool exists
and {RUNID}_iteration2 is absent before each launch anyway.

Every finished run must pass the ABC_PLAN.md A.8.3 completion assertions. A run
that fails any of them is DISCARDED and re-run, and the discard is logged, per
PREREGISTRATION.md 2.5. No partially-trained checkpoint enters the metrics.

Usage:
  .venv/bin/python rebuild/ABC/abc_train.py [--arms A0,A2,B,C10] [--no-log]
"""

import argparse
import csv
import datetime
import os
import re
import shutil
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(_HERE), _HERE, os.path.dirname(os.path.dirname(_HERE))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402

EXP = A.EXP
OUT = A.OUT
PY = '.venv/bin/python'
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]')
EPOCH = re.compile(r'Epoch Num: (\d+/\d+)')
STEP = re.compile(r'Global Step: \d+/(\d+)')


def _p(m):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), m), flush=True)


def cmd_for(arch, arm, seed):
    rid = A.runid(arch, arm, seed)
    return [PY, 'MyTrain.py',
            '--network', A.ARCHS[arch]['network'],
            '--task', 'S2C', '--method', 'ours', '--iteration', '2',
            '--seed', str(seed),
            '--save_model', './' + A.snap_dir(rid) + '/',
            '--source_root', './' + A.pool_dir(rid) + '/',
            '--target_root', './Dataset/Target/',
            '--val_root', './Dataset/Val/CAMO/']


def assert_ready(arch, arm, seed):
    """Pre-launch: pool present at the right size, no stale CLS output, empty
    snapshot dir. Returns (ok, reason)."""
    rid = A.runid(arch, arm, seed)
    pool = os.path.join(C.REPO, A.pool_dir(rid))
    expect = 4447 if arm == 'A0' else 4447 + A.BUDGET
    if not os.path.isdir(pool):
        return False, 'pool missing: %s' % A.pool_dir(rid)
    n = len(os.listdir(os.path.join(pool, 'Image')))
    if n != expect:
        return False, 'pool has %d images, expected %d' % (n, expect)
    if os.path.exists(os.path.join(C.REPO, A.cls_dir(rid))):
        return False, 'stale CLS output: %s' % A.cls_dir(rid)
    snap = os.path.join(C.REPO, A.snap_dir(rid))
    if os.path.isdir(snap) and [f for f in os.listdir(snap) if f.endswith('.pth')]:
        return False, 'snapshot dir already holds .pth: %s' % A.snap_dir(rid)
    return True, ''


def verify_run(arch, arm, seed):
    """ABC_PLAN.md A.8.3. Returns (ok, dict)."""
    rid = A.runid(arch, arm, seed)
    spec = A.ARCHS[arch]
    snap = os.path.join(C.REPO, A.snap_dir(rid))
    tl = os.path.join(snap, 'training_log.log')
    rl = os.path.join(C.REPO, A.runlog(rid))
    d = dict(runid=rid, arch=arch, arm=arm, seed=seed)
    if not os.path.isfile(tl):
        return False, dict(d, fail='no training_log.log')
    lines = open(tl).read().splitlines()
    d['rounds'] = sum(1 for l in lines if l.startswith('Training Log'))
    steps = sorted({m.group(1) for l in lines for m in [STEP.search(l)] if m})
    d['total_step_set'] = ','.join(steps)
    ep = [m.group(1) for l in lines for m in [EPOCH.search(l)] if m]
    d['last_epoch'] = ep[-1] if ep else ''
    stamps = [datetime.datetime.fromisoformat(m.group(1))
              for l in lines for m in [TS.match(l)] if m]
    d['wall_min'] = round((stamps[-1] - stamps[0]).total_seconds() / 60, 1) if stamps else None
    d['tea_best'] = os.path.isfile(os.path.join(snap, 'Tea_epoch_best.pth'))
    run = open(rl).read() if os.path.isfile(rl) else ''
    loaded = [int(x) for x in re.findall(r'Loaded (\d+) image-mask pairs', run)]
    d['pool_r1'] = loaded[0] if loaded else None
    d['pool_r2'] = loaded[1] if len(loaded) > 1 else None
    d['n_appended'] = (d['pool_r2'] - d['pool_r1']) if len(loaded) > 1 else None
    d['target_loaded_4040'] = run.count('Loaded 4040 images')
    be = re.findall(r'Best epoch:(\d+)', run)
    d['best_epoch'] = int(be[-1]) if be else None
    checks = dict(
        rounds=d['rounds'] == 2,
        total_step=d['total_step_set'] == '%04d' % spec['total_step'],
        last_epoch=d['last_epoch'] == spec['last_epoch'],
        tea_best=bool(d['tea_best']),
        wall=bool(d['wall_min'] is not None and d['wall_min'] < 2 * spec['ref_min']),
        pool_r1=d['pool_r1'] == (4447 if arm == 'A0' else 4447 + A.BUDGET),
        target=d['target_loaded_4040'] == 2)
    d['checks'] = checks
    d['failed_checks'] = [k for k, v in checks.items() if not v]
    return (not d['failed_checks']), d


def discard(arch, arm, seed, why, journal):
    rid = A.runid(arch, arm, seed)
    for p in (A.snap_dir(rid), A.cls_dir(rid)):
        full = os.path.join(C.REPO, p)
        if os.path.exists(full):
            shutil.rmtree(full)
    journal.append(dict(runid=rid, reason=why, at=C.now()))
    _p('  DISCARDED %s: %s' % (rid, why))


def launch(arch, arm, seed, gpu):
    rid = A.runid(arch, arm, seed)
    cmd = cmd_for(arch, arm, seed) + ['--gpu', str(gpu)]
    os.makedirs(os.path.join(C.REPO, A.snap_dir(rid)), exist_ok=True)
    lg = open(os.path.join(C.REPO, A.runlog(rid)), 'w')
    lg.write('# RUNID   %s\n# started %s\n# commit  %s\n# CMD     %s\n\n'
             % (rid, C.now(), C.git_commit(), ' '.join(cmd)))
    lg.flush()
    p = subprocess.Popen(cmd, cwd=C.REPO, stdout=lg, stderr=subprocess.STDOUT)
    _p('  launched %-22s gpu %d  pid %d' % (rid, gpu, p.pid))
    return p, lg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', default=','.join(A.ARMS))
    ap.add_argument('--retries', type=int, default=1)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    arms = tuple(a.strip() for a in args.arms.split(',') if a.strip())
    os.makedirs(OUT, exist_ok=True)

    # SINet first (including its A0_s42 sanity run, already done), then SINet-v2
    todo, done_already = [], []
    for arch in ('SINet', 'SINetv2'):
        for arm in arms:
            for seed in A.SEEDS:
                ok, _ = verify_run(arch, arm, seed)
                (done_already if ok else todo).append((arch, arm, seed))
    _p('already complete: %d  -> %s' % (len(done_already),
                                        ', '.join(A.runid(*r) for r in done_already) or 'none'))
    _p('to run: %d' % len(todo))

    with open(os.path.join(OUT, 'abc_commands.txt'), 'w') as fh:
        fh.write('# every command this driver executes, written BEFORE execution\n')
        fh.write('# generated %s | commit %s\n\n' % (C.now(), C.git_commit()))
        for arch, arm, seed in done_already + todo:
            fh.write('%s%s\n' % ('# DONE  ' if (arch, arm, seed) in done_already else '',
                                 ' '.join(cmd_for(arch, arm, seed) + ['--gpu', 'N'])))

    journal, results = [], []
    for arch, arm, seed in done_already:
        _, d = verify_run(arch, arm, seed)
        results.append(d)

    attempts = {}
    queue = list(todo)
    running = {}          # gpu -> (proc, lg, key)
    while queue or running:
        for gpu in (0, 1):
            if gpu not in running and queue:
                key = queue.pop(0)
                ok, why = assert_ready(*key)
                if not ok:
                    if os.path.exists(os.path.join(C.REPO, A.cls_dir(A.runid(*key)))) or \
                       os.path.isdir(os.path.join(C.REPO, A.snap_dir(A.runid(*key)))):
                        discard(*key, why='pre-launch: ' + why, journal=journal)
                        ok, why = assert_ready(*key)
                if not ok:
                    _p('  SKIP %s -- %s' % (A.runid(*key), why))
                    journal.append(dict(runid=A.runid(*key), reason='not launchable: ' + why,
                                        at=C.now()))
                    continue
                running[gpu] = launch(*key, gpu=gpu) + (key,)
        if not running:
            break
        time.sleep(30)
        for gpu in list(running):
            proc, lg, key = running[gpu]
            if proc.poll() is None:
                continue
            lg.close()
            del running[gpu]
            rc = proc.returncode
            ok, d = verify_run(*key)
            d['returncode'] = rc
            n = attempts.get(key, 0) + 1
            attempts[key] = n
            if ok and rc == 0:
                _p('  OK  %-22s wall %.1fm  n_appended %s  best_epoch %s'
                   % (d['runid'], d['wall_min'], d['n_appended'], d['best_epoch']))
                results.append(d)
            else:
                why = 'rc=%d failed=%s' % (rc, d.get('failed_checks') or d.get('fail'))
                discard(*key, why=why, journal=journal)
                if n <= args.retries:
                    _p('  requeue %s (attempt %d)' % (A.runid(*key), n + 1))
                    queue.append(key)
                else:
                    _p('  GIVING UP on %s after %d attempts' % (A.runid(*key), n))
                    results.append(dict(d, abandoned=True))

    # ---- artifacts ----
    fields = ['runid', 'arch', 'arm', 'seed', 'rounds', 'total_step_set', 'last_epoch',
              'wall_min', 'tea_best', 'pool_r1', 'pool_r2', 'n_appended',
              'target_loaded_4040', 'best_epoch', 'returncode', 'failed_checks']
    with open(os.path.join(OUT, 'abc_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in sorted(results, key=lambda x: x['runid']):
            w.writerow(dict(r, failed_checks=','.join(r.get('failed_checks') or [])))
    C.save_json(os.path.join(OUT, 'abc_discards.json'),
                dict(generated=C.now(), n_discards=len(journal), discards=journal))

    # ---- block #2 ----
    good = [r for r in results if not r.get('abandoned')]
    na = [r['n_appended'] for r in good if r.get('n_appended') is not None]
    metrics, thresholds, artifacts, notes = [], [], [], []
    metrics.append(('training_runs_completed', '%d/%d' % (len(good), len(results))))
    metrics.append(('runs_abandoned', sum(1 for r in results if r.get('abandoned'))))
    metrics.append(('runs_discarded_and_rerun', len(journal)))
    for arch in ('SINet', 'SINetv2'):
        sub = [r for r in good if r['arch'] == arch]
        if sub:
            metrics.append(('wall_clock_%s_min' % arch,
                            'mean %.1f  range %.1f-%.1f  n=%d'
                            % (sum(r['wall_min'] for r in sub) / len(sub),
                               min(r['wall_min'] for r in sub),
                               max(r['wall_min'] for r in sub), len(sub)),
                            'reference %.1f min' % A.ARCHS[arch]['ref_min']))
    for r in sorted(good, key=lambda x: x['runid']):
        metrics.append(('n_appended_%s' % r['runid'], r['n_appended'],
                        'CLS round-2 append; best_epoch %s; wall %.1fm'
                        % (r['best_epoch'], r['wall_min'])))
    if na:
        mn, mx, mean = min(na), max(na), sum(na) / len(na)
        spread = (mx - mn) / mean
        metrics.append(('n_appended_mean_range', 'mean %.1f  range %d-%d  spread %.1f%% of mean'
                        % (mean, mn, mx, 100 * spread)))
        metrics.append(('n_appended_spread_exceeds_5pct', spread > 0.05,
                        'ABC_PLAN.md A.12 item 3 -- the one legitimate place the arms '
                        'diverge beyond the Stage C injection'))
        thresholds.append(('CLS round-2 append counts agree across arms within 5%% of '
                           'the mean', spread <= 0.05))
    thresholds += [
        ('every completed run logged exactly 2 CSRDA rounds',
         all(r['rounds'] == 2 for r in good)),
        ('total_step stayed pinned in BOTH rounds of every run (253 SINet / 127 '
         'SINet-v2), so added data bought zero extra optimisation',
         all(r['total_step_set'] == '%04d' % A.ARCHS[r['arch']]['total_step'] for r in good)),
        ('every run reached its final epoch and saved Tea_epoch_best.pth',
         all(r['last_epoch'] == A.ARCHS[r['arch']]['last_epoch'] and r['tea_best']
             for r in good)),
        ('every run read the unfiltered 4040-image target set in both rounds',
         all(r['target_loaded_4040'] == 2 for r in good)),
        ('no run was abandoned', not any(r.get('abandoned') for r in results)),
    ]
    artifacts += ['rebuild/ABC/out/abc_runs.csv', 'rebuild/ABC/out/abc_commands.txt',
                  'rebuild/ABC/out/abc_discards.json']
    notes.append(
        'BLOCK 2 OF 3, AND THE FIRST BLOCK IN THE WHOLE REBUILD WITH TRAINS YES. '
        'Every prior block -- E0, D2, D1, B1, C1 -- records TRAINS NO. Block #1 is '
        'the pre-flight, this is run accounting, #3 is the verdict. None supersedes '
        'another.')
    notes.append(
        'total_step IS PINNED, MEASURED PER RUN. min(len(source), len(target)) at '
        'MyTrain.py:306-307 with zip() truncating at :51,53 means B changes the '
        'MIXTURE and not the step count. So arm A0 gives each base image 0.910 '
        'exposures per epoch against 0.743 for A2/B/C at B=1000 -- 22% more -- which '
        'is exactly why A0 is not a clean control and why A2 exists.')
    notes.append(
        'n_appended DIFFERS PER ARM BY CONSTRUCTION, and is reported rather than '
        'absorbed. CLS selects target images by edge_loss < u*avg_loss (CLS.py:139) '
        'using the arm\'s OWN round-1 model, so each arm appends a different number '
        'of differently-pseudo-labelled images. That is legitimately part of '
        '"closed-loop", but it is a SECOND place the arms differ beyond the Stage C '
        'injection, and it is high-variance. total_step stays pinned for any '
        'n_appended, which is asserted above.')
    notes.append(
        'A DISCARDED RUN NEVER ENTERS THE METRICS. Any run failing an A.8.3 assertion '
        'has its snapshot and CLS directories removed and is re-run; discards are in '
        'abc_discards.json. CLS falls back to Tea_40/Tea_100.pth if Tea_epoch_best is '
        'missing (CLS.py:65-75), so a killed run would silently change which teacher '
        'generates pseudo-labels -- hence the assertion rather than a warning.')
    notes.append(
        'PREREGISTRATION.md was committed before block #1 and is unchanged. This '
        'driver neither reads it as an input nor writes it.')

    block = C.log_block(
        EXP, '.venv/bin/python rebuild/ABC/abc_train.py --arms %s' % args.arms,
        metrics, thresholds, [], artifacts,
        representation=('training reads each arm\'s own pool at '
                        'Dataset/Source/ABC/<RUNID>/{Image,GT}; CLS round 2 reads '
                        'Dataset/Source/ABC/<RUNID>_iteration2/'),
        trains='YES', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

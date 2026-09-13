#!/usr/bin/env python
"""EXP PC -- the positive control: train mean-teacher, SINet, seeds {42,43,45}.

Rule frozen in PREREGISTRATION_PC.md, committed at c2114af BEFORE this file
existed. Does NOT modify rebuild/ABC/abc_train.py, which remains frozen.

Pools are hardlink copies of the committed base pool into Dataset/Source/PC/, so
no committed A/B/C pool is opened for writing at any point.

Usage:
  .venv/bin/python rebuild/PC/pc_train.py --steps pools
  .venv/bin/python rebuild/PC/pc_train.py --steps train --gpu 0 --seeds 42,43,45
  .venv/bin/python rebuild/PC/pc_train.py --steps log
"""

import argparse
import hashlib
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _pth in (_REBUILD, os.path.join(_REBUILD, 'ABC'), _HERE, os.path.dirname(_REBUILD)):
    if _pth not in sys.path:
        sys.path.insert(0, _pth)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402

EXP = 'PC'
OUT = C.exp_dir(EXP, 'out')
os.makedirs(OUT, exist_ok=True)
PY = '.venv/bin/python'
ARCH = 'SINet'
ARM = 'MT'
SEEDS = A.SEEDS                       # (42, 43, 45) -- identical to every campaign here
BASE_POOL = 'Dataset/Source/ABC/SINet_A0_s42'      # committed, read-only here


def _p(m):
    print('[%s] [PC] %s' % (time.strftime('%H:%M:%S'), m), flush=True)


def runid(seed):
    return '%s_%s_s%d' % (ARCH, ARM, seed)


def pool_dir(seed):
    return 'Dataset/Source/PC/%s' % runid(seed)


def snap_dir(seed):
    return 'Snapshot/PC/%s' % runid(seed)


def build_pools():
    """Hardlink the committed base pool into a per-seed PC pool."""
    src = os.path.join(C.REPO, BASE_POOL)
    if not os.path.isdir(src):
        raise RuntimeError('PC HALT: base pool missing at %s' % BASE_POOL)
    for seed in SEEDS:
        dst = os.path.join(C.REPO, pool_dir(seed))
        for sub in ('Image', 'GT'):
            s, d = os.path.join(src, sub), os.path.join(dst, sub)
            os.makedirs(d, exist_ok=True)
            have = set(os.listdir(d))
            for f in os.listdir(s):
                if f not in have:
                    os.link(os.path.join(s, f), os.path.join(d, f))
        n_i = len(os.listdir(os.path.join(dst, 'Image')))
        n_g = len(os.listdir(os.path.join(dst, 'GT')))
        if n_i != 4447 or n_g != 4447:
            raise RuntimeError('PC HALT: %s has %d/%d, expected 4447/4447'
                               % (pool_dir(seed), n_i, n_g))
        _p('pool ready %s  Image %d  GT %d' % (pool_dir(seed), n_i, n_g))


def cmd_for(seed, gpu):
    return [PY, 'MyTrain.py',
            '--network', 'SINet',
            '--task', 'S2C', '--method', 'mean_teacher', '--iteration', '1',
            '--seed', str(seed), '--gpu', str(gpu),
            '--save_model', './' + snap_dir(seed) + '/',
            '--source_root', './' + pool_dir(seed) + '/',
            '--target_root', './Dataset/Target/',
            '--val_root', './Dataset/Val/CAMO/']


def train(seeds, gpu):
    for seed in seeds:
        snap = os.path.join(C.REPO, snap_dir(seed))
        tea = os.path.join(snap, 'Tea_epoch_best.pth')
        if os.path.exists(tea):
            _p('seed %d already has Tea_epoch_best.pth -- skipping' % seed)
            continue
        os.makedirs(snap, exist_ok=True)
        cmd = cmd_for(seed, gpu)
        _p('launch seed %d on gpu %d: %s' % (seed, gpu, ' '.join(cmd)))
        t0 = time.time()
        logp = os.path.join(OUT, 'pc_train_s%d.log' % seed)
        with open(logp, 'w') as lf:
            r = subprocess.run(cmd, cwd=C.REPO, stdout=lf,
                               stderr=subprocess.STDOUT)
        mins = (time.time() - t0) / 60.0
        if r.returncode != 0:
            raise RuntimeError('PC HALT: seed %d exited %d, see %s'
                               % (seed, r.returncode, logp))
        if not os.path.exists(tea):
            raise RuntimeError('PC HALT: seed %d produced no Tea_epoch_best.pth' % seed)
        _p('seed %d done in %.1f min' % (seed, mins))


def sha256(path, n=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(n), b''):
            h.update(chunk)
    return h.hexdigest()


def log_runs():
    metrics, ok = [], 0
    for seed in SEEDS:
        tea = os.path.join(C.REPO, snap_dir(seed), 'Tea_epoch_best.pth')
        if os.path.exists(tea):
            ok += 1
            metrics.append(('teacher_%s' % runid(seed), sha256(tea)[:16],
                            'sha256[:16] of Tea_epoch_best.pth'))
        else:
            metrics.append(('teacher_%s' % runid(seed), 'MISSING', 'run did not complete'))
    metrics.insert(0, ('training_runs_completed', '%d/%d' % (ok, len(SEEDS)),
                       'mean_teacher, SINet, iteration forced to 1 by MyTrain.py:249-251'))
    metrics.insert(1, ('pool_size_each_arm', '4447',
                       'hardlinks of the committed base pool; no A/B/C pool opened for writing'))
    C.log_block(
        EXP,
        cmd='%s rebuild/PC/pc_train.py --steps train' % PY,
        metrics=metrics,
        thresholds=[('all declared mean-teacher runs completed with a best teacher',
                     ok == len(SEEDS))],
        artifacts=[os.path.join(OUT, 'pc_train_s%d.log' % s) for s in SEEDS],
        representation=('MyTrain.py --method mean_teacher --iteration 1, SINet, '
                        'base pool 4447, cuDNN deterministic, seeds 42/43/45'),
        trains='YES',
        notes=('BLOCK 1 OF 2 -- RUN ACCOUNTING FOR THE POSITIVE CONTROL. Rule frozen in '
               'PREREGISTRATION_PC.md at c2114af before this script existed. This is a '
               'control on INSTRUMENT SENSITIVITY, not an ablation: C10 differs from MT '
               'in method, round count and pool size at once, so no component '
               'attribution follows from it and none is made. rebuild/ABC/abc_train.py '
               'is untouched and remains frozen; the committed A/B/C and T2 runs are not '
               'retrained and C10 enters only as a re-scored reference arm in block #2.'))
    _p('EXP PC block #1 appended (%d/%d runs).' % (ok, len(SEEDS)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='pools')
    ap.add_argument('--gpu', type=int, default=0)
    ap.add_argument('--seeds', default=','.join(str(s) for s in SEEDS))
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(',') if s]
    for st in a.steps.split(','):
        if st == 'pools':
            build_pools()
        elif st == 'train':
            train(seeds, a.gpu)
        elif st == 'log':
            log_runs()
        else:
            raise SystemExit('unknown step %s' % st)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""REBUTTAL WS4 -- a same-code supervised upper bound on the standard 4040-image split.

DESCRIPTIVE ANCHOR, NO DECISION RULE (rebuild/REBUTTAL/PREREGISTRATION_WS4.md).
Answers one question a reviewer asked: where does a model trained by THIS code, on
real labelled images, land on the same scorer? It sets the ceiling the synthetic-
source protocol sits under; it does not test any arm against any other.

  SUP = MyTrain.py --method source_only on the real COD10K-train 3040 + CAMO-train
        1000 images WITH their masks, single round (MyTrain forces --iteration 1 for
        any non-'ours' method), native epochs, CAMO-250 checkpoint selection, exactly
        as every arm in this repo selects.

Steps (each appends its own EXP REBUTTAL_WS4 block):
  preflight  the hash gate: the downloaded images must equal Dataset/Target/Image by
             sha256, 4040/4040, name for name, or WS4 STOPS. Masks: 4040, stems equal
             to the images', single-channel-readable, binary-ish. Builds the source pool
             Dataset/Source/WS4/REAL4040/{Image,GT} by COPY (the download stays as
             fetched) and prints the dry-run commands. Trains nothing.
  train      one run per GPU, two GPUs; verifies each run (two-round logic does not
             apply: one round, last epoch reached, Tea_epoch_best.pth present).
  evaluate   MyTest.py inference on COD10K and NC4K, scored by abc_evaluate.score(), the
             scorer every campaign uses, after the same B1 scorer-reproduction gate.

Usage:
  .venv/bin/python rebuild/REBUTTAL/ws4_anchor.py --steps preflight [--no-log]
  .venv/bin/python rebuild/REBUTTAL/ws4_anchor.py --steps train,evaluate
"""

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REB = os.path.dirname(_HERE)
for _p in (_REB, os.path.join(_REB, 'ABC'), os.path.dirname(_REB), os.path.join(os.path.dirname(_REB), 'Eval')):
    sys.path.insert(0, _p)
import common as C                                            # noqa: E402

OUT = os.path.join(_HERE, 'out', 'ws4')
DL = 'Dataset/_download_ws4'
DL_ZIP = DL + '/TrainValDataset.zip'
DL_URL = 'https://drive.google.com/file/d/1M8-Ivd33KslvyehLK9_IUBGJ_Kf52bWG'   # SINet-V2 README
DL_IMG = DL + '/extract/COD-TrainDataset/Imgs'
DL_GT = DL + '/extract/COD-TrainDataset/GT'
TARGET = 'Dataset/Target/Image'
POOL = 'Dataset/Source/WS4/REAL4040'
SEEDS = (42, 43, 45)
ARCHS = {'SINet': dict(network='SINet', last_epoch='040'), 'SINetv2': dict(network='SINet-v2', last_epoch='100')}
ENDPOINTS = ('COD10K', 'NC4K')
PY = '.venv/bin/python'


def R(*p):
    return os.path.join(C.REPO, *p)


def rid(arch, seed):
    return '%s_SUP_s%d' % (arch, seed)


def snap(r):
    return 'Snapshot/WS4/%s/' % r


def pred(r, ep):
    return 'Result/WS4/%s/%s' % (r, ep)


def train_cmd(arch, seed, gpu='N'):
    r = rid(arch, seed)
    return [PY, 'MyTrain.py', '--network', ARCHS[arch]['network'], '--task', 'S2C',
            '--method', 'source_only', '--seed', str(seed), '--save_model', './' + snap(r),
            '--source_root', './' + POOL + '/', '--target_root', './Dataset/Target/',
            '--val_root', './Dataset/Val/CAMO/', '--gpu', str(gpu)]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


# --- preflight ------------------------------------------------------------------------
def preflight(args):
    import numpy as np
    from PIL import Image
    M, T = [], []
    M.append(('download_source', DL_URL, 'SINet-V2 README, "training/validation dataset"'))
    M.append(('download_zip_sha256', sha(R(DL_ZIP)), DL_ZIP))
    imgs = sorted(os.listdir(R(DL_IMG)))
    gts = sorted(os.listdir(R(DL_GT)))
    tgt = sorted(os.listdir(R(TARGET)))
    M += [('downloaded_images', len(imgs), DL_IMG), ('downloaded_masks', len(gts), DL_GT),
          ('target_pool_images', len(tgt), TARGET)]
    same_names = imgs == tgt
    T.append(('downloaded image NAMES equal Dataset/Target/Image, 4040/4040', same_names and len(imgs) == 4040))
    nbad = sum(1 for n in imgs if n in set(tgt) and sha(R(DL_IMG, n)) != sha(R(TARGET, n)))
    M.append(('image_sha256_mismatches_vs_target', nbad, 'per file, all 4040'))
    gate = same_names and len(imgs) == 4040 and nbad == 0
    T.append(('HASH GATE: downloaded images byte-identical to Dataset/Target/Image, 4040/4040', gate))
    stems_i = {os.path.splitext(n)[0] for n in imgs}
    stems_g = {os.path.splitext(n)[0] for n in gts}
    T.append(('every image has exactly one mask with the same stem (4040)', stems_i == stems_g and len(gts) == 4040))
    nonbin = 0
    for n in gts:
        a = np.array(Image.open(R(DL_GT, n)).convert('L'))
        if ((a > 10) & (a < 245)).mean() > 0.05:      # anti-aliased edges allowed, not grey masks
            nonbin += 1
    M.append(('masks_more_than_5pct_grey', nonbin, 'pixel values in (10, 245)'))
    T.append(('masks are binary up to edge anti-aliasing', nonbin == 0))
    if not gate:
        notes = 'HASH GATE FAILED. WS4 STOPS (PREREGISTRATION_WS4.md). No pool is built and nothing trains.'
        print(C.log_block('REBUTTAL_WS4', ' '.join(sys.argv), M, thresholds=T, notes=notes, write=not args.no_log))
        raise SystemExit(2)
    for sub, src in (('Image', DL_IMG), ('GT', DL_GT)):
        d = R(POOL, sub)
        os.makedirs(d, exist_ok=True)
        for n in sorted(os.listdir(R(src))):
            if not os.path.isfile(os.path.join(d, n)):
                shutil.copy2(R(src, n), os.path.join(d, n))
    ni, hi, _ = C.dir_digest(R(POOL, 'Image'))
    ng, hg, _ = C.dir_digest(R(POOL, 'GT'))
    M += [('pool_image', '%d files, digest %s' % (ni, hi), POOL + '/Image'),
          ('pool_gt', '%d files, digest %s' % (ng, hg), POOL + '/GT')]
    T.append(('pool built: 4040 images and 4040 masks', ni == 4040 and ng == 4040))
    free = shutil.disk_usage(C.REPO).free / 2 ** 30
    M.append(('disk_free_GiB', '%.0f' % free, 'need ~4 GiB per run'))
    cmds = [' '.join(train_cmd(a, s)) for a in ARCHS for s in SEEDS]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'ws4_commands.txt'), 'w') as fh:
        fh.write('\n'.join(cmds) + '\n')
    M.append(('dry_run_commands', len(cmds), 'rebuild/REBUTTAL/out/ws4/ws4_commands.txt'))
    notes = ('PREFLIGHT ONLY: nothing trained. WS4 is a DESCRIPTIVE anchor with no decision rule (PREREGISTRATION_WS4.md). The pool is a byte copy of the downloaded images and masks. The images are the same bytes as the unlabelled target pool, so the only difference from the synthetic protocol is real masks in place of synthetic supervision.')
    print(C.log_block('REBUTTAL_WS4', ' '.join(sys.argv), M, thresholds=T,
                      artifacts=['rebuild/REBUTTAL/out/ws4/ws4_commands.txt'], notes=notes, write=not args.no_log))


# --- train ----------------------------------------------------------------------------
def verify(arch, seed):
    r = rid(arch, seed)
    log = R(snap(r), 'training_log.log')
    ok = os.path.isfile(R(snap(r), 'Tea_epoch_best.pth')) and os.path.isfile(log)
    last = ''
    if os.path.isfile(log):
        for line in open(log):
            if 'Epoch Num:' in line:
                last = line.split('Epoch Num:')[1].split('/')[0].strip()
    return ok and last == ARCHS[arch]['last_epoch'], last


def train(args):
    runs = [(a, s) for a in ARCHS for s in SEEDS]
    todo = [x for x in runs if not verify(*x)[0]]
    running, res = {}, []
    while todo or running:
        for gpu in (0, 1):
            if gpu not in running and todo:
                a, s = todo.pop(0)
                os.makedirs(R(snap(rid(a, s))), exist_ok=True)
                lg = open(R('rebuild/REBUTTAL/logs', 'ws4_%s.log' % rid(a, s)), 'w')
                p = subprocess.Popen(train_cmd(a, s, gpu), cwd=C.REPO, stdout=lg, stderr=subprocess.STDOUT)
                running[gpu] = (a, s, p, lg, time.time())
                print('[%s] launched %s gpu %d' % (time.strftime('%H:%M:%S'), rid(a, s), gpu), flush=True)
        for gpu, (a, s, p, lg, t0) in list(running.items()):
            if p.poll() is not None:
                lg.close()
                ok, last = verify(a, s)
                res.append(dict(runid=rid(a, s), arch=a, seed=s, wall_min=round((time.time() - t0) / 60, 1),
                                returncode=p.returncode, last_epoch=last, ok=ok))
                print('[%s] %s %s wall %.1fm' % (time.strftime('%H:%M:%S'), 'OK ' if ok else 'BAD', rid(a, s),
                                                 res[-1]['wall_min']), flush=True)
                del running[gpu]
        time.sleep(20)
    os.makedirs(OUT, exist_ok=True)
    if res:
        with open(os.path.join(OUT, 'ws4_runs.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0]))
            w.writeheader()
            w.writerows(res)
    M = [(r['runid'], 'ok %s  wall %.1f min  last epoch %s' % (r['ok'], r['wall_min'], r['last_epoch']), '') for r in res]
    T = [('every WS4 run completed, reached its last epoch and wrote Tea_epoch_best.pth',
          all(verify(a, s)[0] for a, s in runs))]
    print(C.log_block('REBUTTAL_WS4', ' '.join(sys.argv), M or [('runs_trained_this_call', 0, 'all already complete')],
                      thresholds=T, trains='YES', artifacts=['rebuild/REBUTTAL/out/ws4/ws4_runs.csv'],
                      notes='Run accounting. Descriptive anchor; nothing is decided.', write=not args.no_log))


# --- evaluate -------------------------------------------------------------------------
def evaluate(args):
    import abc_evaluate as E
    s1 = E.score(R('Dataset/Test/COD10K/GT'), R('Result/SINet/S2C'))
    T = [('scorer reproduces B1 (Sa %.6f, MAE %.6f) within %g' % (E.B1_SA, E.B1_MAE, E.TOL),
          abs(s1['Sm'] - E.B1_SA) < E.TOL and abs(s1['MAE'] - E.B1_MAE) < E.TOL)]
    if not T[0][1]:
        raise SystemExit('WS4 HALT: scorer does not reproduce B1')
    rows, M = [], []
    for a in ARCHS:
        for s in SEEDS:
            r = rid(a, s)
            if not verify(a, s)[0]:
                raise SystemExit('WS4 HALT: %s not verified; all runs are reported or none' % r)
            for ep in ENDPOINTS:
                gtd = R('Dataset/Test/%s/GT' % ep)
                pd = R(pred(r, ep))
                if not (os.path.isdir(pd) and len(os.listdir(pd)) == len(os.listdir(gtd))):
                    cmd = [PY, 'MyTest.py', '--network', ARCHS[a]['network'], '--gpu', '0', '--dataset', ep,
                           '--model_path', './' + snap(r) + 'Tea_epoch_best.pth', '--test_save', './' + pred(r, ep)]
                    with open(R('rebuild/REBUTTAL/logs', 'ws4_infer_%s_%s.log' % (r, ep)), 'w') as lg:
                        subprocess.run(cmd, cwd=C.REPO, stdout=lg, stderr=subprocess.STDOUT, check=True)
                m = E.score(gtd, pd)
                rows.append(dict(runid=r, arch=a, seed=s, endpoint=ep, **m))
                M.append(('%s_%s' % (r, ep), 'Sa %.6f  MAE %.6f  Fbw %.6f  meanEm %.6f' % (m['Sm'], m['MAE'], m['wFm'], m['meanEm']), 'n=%d' % m['n']))
    import numpy as np
    for a in ARCHS:
        for ep in ENDPOINTS:
            v = [x['Sm'] for x in rows if x['arch'] == a and x['endpoint'] == ep]
            M.append(('SUP_%s_%s_mean_sd' % (a, ep), '%.4f (sd %.4f, n=%d)' % (np.mean(v), np.std(v, ddof=1), len(v)), 'descriptive'))
    with open(os.path.join(OUT, 'ws4_metrics.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(C.log_block('REBUTTAL_WS4', ' '.join(sys.argv), M, thresholds=T,
                      artifacts=['rebuild/REBUTTAL/out/ws4/ws4_metrics.csv'],
                      notes='DESCRIPTIVE ANCHOR, NO DECISION RULE. Reported whatever it shows, including a gap to the published supervised SINet (0.771) / SINet-v2 (0.815), which are a different code base and are not tuned toward.',
                      write=not args.no_log))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', required=True)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(R('rebuild/REBUTTAL/logs'), exist_ok=True)
    for st in args.steps.split(','):
        dict(preflight=preflight, train=train, evaluate=evaluate)[st.strip()](args)


if __name__ == '__main__':
    main()

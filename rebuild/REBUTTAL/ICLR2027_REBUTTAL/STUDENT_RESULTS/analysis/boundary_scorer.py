"""Boundary-metric scorer shared by AN-01 and EXP-02 (CDR).

The metric is the manuscript's own: `metrics_one` is imported unchanged from
rebuild/DIAG/diag_boundary.py (Boundary IoU, Cheng et al. 2021, band d = max(1, round(0.02 x
image diagonal)) by 3x3 erosion; Boundary F, contour tolerance max(1, round(0.0075 x diagonal));
whole-object IoU). Only the I/O wrapper is generalised from diag_boundary._job so that any
prediction directory and any endpoint can be scored; its preprocessing is identical: grey-scale,
bilinear resize to the GT size when shapes differ, min-max normalisation, prediction >= threshold,
GT > 127. Per-run values are the nan-mean over images, as in diag_boundary.main().

The AN-01 reproduction gate (an01_boundary.py) re-derives the committed
rebuild/DIAG/out/diag_boundary_per_run*.csv with this wrapper before it is used for anything else.
"""
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

import _repo as R

sys.path.insert(0, os.path.join(R.REPO, 'rebuild', 'DIAG'))
from diag_boundary import metrics_one, BIOU_FRAC, BF_FRAC   # noqa: E402

METRICS = ('boundary_iou', 'boundary_f', 'boundary_prec', 'boundary_rec', 'iou')


def score_image(args):
    gt_path, pred_path, thresh = args
    g = np.array(Image.open(gt_path).convert('L'))
    q = Image.open(pred_path).convert('L')
    if q.size != (g.shape[1], g.shape[0]):
        q = q.resize((g.shape[1], g.shape[0]), Image.BILINEAR)
    pr = np.array(q).astype(np.float64)
    gt = g > 127
    rng = pr.max() - pr.min()
    pr = (pr - pr.min()) / rng if rng > 0 else pr * 0.0
    pb = pr >= thresh
    m = metrics_one(gt, pb, float(np.hypot(*gt.shape)))
    m['name'] = os.path.splitext(os.path.basename(gt_path))[0]
    return m


def score_runs(runs, thresholds=(0.5,), workers=32):
    """runs: list of (key, pred_dir, endpoint). Returns {(key, thresh): per-run dict} and per-image rows."""
    jobs, index = [], []
    for key, pred_dir, ep in runs:
        gt_dir = os.path.join(R.REPO, 'Dataset', 'Test', ep, 'GT')
        stems = sorted(os.path.splitext(f)[0] for f in os.listdir(gt_dir) if f.endswith('.png'))
        for t in thresholds:
            for s in stems:
                jobs.append((os.path.join(gt_dir, s + '.png'), os.path.join(pred_dir, s + '.png'), t))
                index.append((key, t))
    with Pool(workers) as pool:
        res = pool.map(score_image, jobs, chunksize=64)
    by = {}
    for (key, t), r in zip(index, res):
        by.setdefault((key, t), []).append(r)
    agg = {}
    for (key, t), rows in by.items():
        d = dict(n=len(rows))
        for m in METRICS:
            d[m] = float(np.nanmean(np.array([x[m] for x in rows], dtype=np.float64)))
        agg[(key, t)] = d
    return agg, by

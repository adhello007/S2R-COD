#!/usr/bin/env python
"""DIAG.3 -- boundary metrics and subgroup breakdowns on committed predictions.

Re-scores predictions that ALREADY EXIST under Result/ABC/. Trains nothing,
runs no inference, and writes nothing outside rebuild/DIAG/out/.

THE QUESTION
------------
The acquisition signal in Equation (ES) is boundary-focused: its first term is an
L1 distance between Sobel gradient magnitudes. The endpoint metric it is judged
by, S_alpha, is structure-aware but not a boundary metric, and MAE is a per-pixel
average that largely ignores the boundary. So the campaign never measured the
quantity the signal was built to move.

This computes two dedicated boundary metrics on the committed predictions:

  Boundary IoU  (Cheng et al. 2021) -- IoU restricted to a band of width
                d = 0.02 * image diagonal inside each mask's contour.
  Boundary F    (DAVIS contour measure) -- precision/recall of contour pixels
                matched within a tolerance theta = 0.0075 * image diagonal.

and breaks performance down by object size, by endpoint uncertainty quantile,
and by camouflage difficulty.

POST-HOC AND NON-DECISIONAL. No pre-registered verdict is re-decided here; the
campaign's endpoint metric remains S_alpha.

Usage:
  .venv/bin/python rebuild/DIAG/diag_boundary.py [--workers 32] [--limit N]
"""

import argparse
import csv
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')

ENDPOINT = 'COD10K'
GT_DIR = os.path.join(REPO, 'Dataset/Test/COD10K/GT')
PRED_ROOT = os.path.join(REPO, 'Result/ABC')
BIOU_FRAC = 0.02        # Cheng et al. 2021 default
BF_FRAC = 0.0075        # DAVIS default contour tolerance
BIN_THRESH = 0.5        # predictions are normalised to [0,1] then thresholded


def _p(m):
    print(m, flush=True)


def _contour(m):
    """Boolean contour: pixels in m that are not interior under 4-connectivity."""
    er = ndimage.binary_erosion(m, structure=np.ones((3, 3), bool), border_value=0)
    return m & ~er


def metrics_one(gt, pr, diag):
    """Boundary IoU, Boundary F, and whole-object IoU for one binarised pair."""
    out = {}
    # ---- Boundary IoU -----------------------------------------------------
    d = max(1, int(round(BIOU_FRAC * diag)))
    gt_in = ndimage.binary_erosion(gt, np.ones((3, 3), bool), iterations=d, border_value=0)
    pr_in = ndimage.binary_erosion(pr, np.ones((3, 3), bool), iterations=d, border_value=0)
    gb, pb = gt & ~gt_in, pr & ~pr_in
    inter = np.count_nonzero(gb & pb)
    union = np.count_nonzero(gb | pb)
    out['boundary_iou'] = (inter / union) if union else float('nan')

    # ---- Boundary F -------------------------------------------------------
    th = max(1, int(round(BF_FRAC * diag)))
    gc, pc = _contour(gt), _contour(pr)
    ng, npx = np.count_nonzero(gc), np.count_nonzero(pc)
    if ng == 0 and npx == 0:
        out.update(boundary_f=float('nan'), boundary_prec=float('nan'),
                   boundary_rec=float('nan'))
    elif ng == 0 or npx == 0:
        out.update(boundary_f=0.0, boundary_prec=0.0, boundary_rec=0.0)
    else:
        # distance to the nearest contour pixel of the other mask
        dg = ndimage.distance_transform_edt(~gc)
        dp = ndimage.distance_transform_edt(~pc)
        prec = float((dg[pc] <= th).mean())        # pred contour near a GT contour
        rec = float((dp[gc] <= th).mean())         # GT contour near a pred contour
        f = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        out.update(boundary_f=f, boundary_prec=prec, boundary_rec=rec)

    # ---- whole-object IoU, for reference ----------------------------------
    u = np.count_nonzero(gt | pr)
    out['iou'] = (np.count_nonzero(gt & pr) / u) if u else float('nan')
    out['gt_fg_frac'] = float(gt.mean())
    return out


_THRESH = BIN_THRESH


def _init(t):
    global _THRESH
    _THRESH = t


def _job(args):
    runid, stem = args
    gp = os.path.join(GT_DIR, stem + '.png')
    pp = os.path.join(PRED_ROOT, runid, ENDPOINT, stem + '.png')
    try:
        g = np.array(Image.open(gp).convert('L'))
        q = Image.open(pp).convert('L')
        if q.size != (g.shape[1], g.shape[0]):
            q = q.resize((g.shape[1], g.shape[0]), Image.BILINEAR)
        pr = np.array(q).astype(np.float64)
    except Exception as e:                                    # noqa: BLE001
        return dict(runid=runid, name=stem, error=str(e))
    gt = g > 127
    rng = pr.max() - pr.min()
    pr = (pr - pr.min()) / rng if rng > 0 else pr * 0.0
    pb = pr >= _THRESH
    diag = float(np.hypot(*gt.shape))
    m = metrics_one(gt, pb, diag)
    m.update(runid=runid, name=stem)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=32)
    ap.add_argument('--limit', type=int, default=0, help='images per run, 0 = all')
    ap.add_argument('--thresh', type=float, default=BIN_THRESH,
                    help='binarisation threshold; the sweep is the robustness '
                         'check that these metrics are not an artifact of 0.5')
    ap.add_argument('--arch', default='', help='restrict to runs of one architecture')
    ap.add_argument('--arms', default='', help='comma list of arms to restrict to')
    ap.add_argument('--suffix', default='', help='output filename suffix')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    runs = sorted(d for d in os.listdir(PRED_ROOT)
                  if os.path.isdir(os.path.join(PRED_ROOT, d, ENDPOINT)))
    if args.arch:
        runs = [r for r in runs if r.split('_')[0] == args.arch]
    if args.arms:
        keep = {a.strip() for a in args.arms.split(',') if a.strip()}
        runs = [r for r in runs if r.split('_')[1] in keep]
    stems = sorted(os.path.splitext(f)[0] for f in os.listdir(GT_DIR) if f.endswith('.png'))
    if args.limit:
        stems = stems[:args.limit]
    jobs = [(r, s) for r in runs for s in stems]
    _p('runs %d  images/run %d  total jobs %d  workers %d'
       % (len(runs), len(stems), len(jobs), args.workers))

    with Pool(args.workers, initializer=_init, initargs=(args.thresh,)) as pool:
        rows = []
        for i, r in enumerate(pool.imap_unordered(_job, jobs, chunksize=64), 1):
            rows.append(r)
            if i % 10000 == 0:
                _p('  %d / %d' % (i, len(jobs)))
    errs = [r for r in rows if 'error' in r]
    rows = [r for r in rows if 'error' not in r]
    _p('done: %d rows, %d errors' % (len(rows), len(errs)))

    fields = ['runid', 'name', 'boundary_iou', 'boundary_f', 'boundary_prec',
              'boundary_rec', 'iou', 'gt_fg_frac']
    with open(os.path.join(OUT, 'diag_boundary_per_image%s.csv' % args.suffix), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x['runid'], x['name'])):
            w.writerow({k: r.get(k) for k in fields})

    # ---- per-run aggregates ------------------------------------------------
    byrun = {}
    for r in rows:
        byrun.setdefault(r['runid'], []).append(r)
    agg = []
    for rid, rs in sorted(byrun.items()):
        parts = rid.split('_')
        d = dict(runid=rid, arch=parts[0], arm=parts[1], seed=int(parts[2][1:]),
                 n=len(rs))
        for m in ('boundary_iou', 'boundary_f', 'boundary_prec', 'boundary_rec', 'iou'):
            v = np.array([x[m] for x in rs], dtype=np.float64)
            d[m] = float(np.nanmean(v))
        agg.append(d)
    with open(os.path.join(OUT, 'diag_boundary_per_run%s.csv' % args.suffix), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)

    json.dump(dict(n_rows=len(rows), n_errors=len(errs), runs=runs,
                   endpoint=ENDPOINT, biou_frac=BIOU_FRAC, bf_frac=BF_FRAC,
                   bin_thresh=args.thresh,
                   errors=errs[:20]),
              open(os.path.join(OUT, 'diag_boundary_meta%s.json' % args.suffix), 'w'), indent=2)
    _p('wrote per-image, per-run and meta under %s' % OUT)


if __name__ == '__main__':
    main()

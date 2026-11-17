#!/usr/bin/env python
"""CAUS -- scoring: the committed scorer, an independent S-measure, and the reuse gate R5.

Primary scorer: rebuild/ABC/abc_evaluate.score(), imported UNCHANGED (Eval/metrics.py underneath),
so every EXP-01 number comes from the exact code that produced the committed campaign metrics.

Second computation: independent_sm(), written from the S-measure definition (Fan et al., ICCV 2017;
alpha = 0.5; object term with sample std, region term = quadrant SSIM split at the 1-indexed rounded
GT centroid). It shares no code with Eval/metrics.py and is used to check the primary scorer.

Modes:
  --validate-b1   score committed Result/SINet/S2C on COD10K; must equal B1's 0.717216 / 0.074463
  --rescore-historical
                  re-score the committed predictions of the reused SINet runs (B, C10, CORACLE,
                  plus CSHUF as reference) on COD10K and NC4K; every metric must reproduce the
                  committed abc_metrics.csv values at 6 dp (reuse gate R5)
  --independent N compare independent_sm against the primary Sm on N images per historical run
"""

import argparse
import csv
import os
import sys
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

for _p in (os.path.join(K.REBUILD, 'ABC'), K.REBUILD, os.path.join(K.REPO, 'Eval')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                             # noqa: E402

B1_SA, B1_MAE = 0.717216, 0.074463
METRICS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
REUSED = (('B', 'rebuild/ABC/out/abc_metrics.csv'), ('C10', 'rebuild/ABC/out/abc_metrics.csv'),
          ('CORACLE', 'rebuild/ABC/out/or/abc_metrics.csv'), ('CSHUF', 'rebuild/ABC/out/t2/abc_metrics.csv'))
SEEDS = (42, 43, 45)
ENDPOINTS = ('COD10K', 'NC4K')


def primary(gt_dir, pred_dir):
    import abc_evaluate as E
    return E.score(gt_dir, pred_dir)


# ---------------------------------------------------------------------------
# Independent S-measure (no shared code with Eval/metrics.py)
# ---------------------------------------------------------------------------

def _norm(pred_u8, gt_u8):
    p = pred_u8.astype(np.float64) / 255.0
    lo, hi = p.min(), p.max()
    if hi > lo:
        p = (p - lo) / (hi - lo)
    return p, gt_u8 > 128


def _obj_term(x_vals):
    if x_vals.size == 0:
        return 0.0
    mu = x_vals.mean()
    sd = x_vals.std(ddof=1) if x_vals.size > 1 else float('nan')
    return 2.0 * mu / (mu * mu + 1.0 + sd + np.spacing(1))


def _ssim(a, b):
    n = a.size
    ma, mb = a.mean(), b.mean()
    va = ((a - ma) ** 2).sum() / (n - 1)
    vb = ((b - mb) ** 2).sum() / (n - 1)
    cov = ((a - ma) * (b - mb)).sum() / (n - 1)
    num = 4.0 * ma * mb * cov
    den = (ma * ma + mb * mb) * (va + vb)
    if num != 0:
        return num / (den + np.spacing(1))
    return 1.0 if den == 0 else 0.0


def independent_sm(pred_u8, gt_u8, alpha=0.5):
    p, g = _norm(pred_u8, gt_u8)
    gf = g.astype(np.float64)
    m = gf.mean()
    if m == 0:
        return 1.0 - p.mean()
    if m == 1:
        return p.mean()
    # object-aware
    fg = _obj_term((p * gf)[g])
    bg = _obj_term(((1 - p) * (1 - gf))[~g])
    so = m * fg + (1 - m) * bg
    # region-aware: centroid in MATLAB 1-indexed convention
    h, w = g.shape
    tot = gf.sum()
    cx = int(np.round((gf.sum(axis=0) * np.arange(1, w + 1)).sum() / tot - 1)) + 1
    cy = int(np.round((gf.sum(axis=1) * np.arange(1, h + 1)).sum() / tot - 1)) + 1
    blocks = ((slice(0, cy), slice(0, cx)), (slice(0, cy), slice(cx, w)),
              (slice(cy, h), slice(0, cx)), (slice(cy, h), slice(cx, w)))
    wts = (cx * cy, (w - cx) * cy, cx * (h - cy))
    wts = [v / (h * w) for v in wts]
    wts.append(1 - sum(wts))
    sr = sum(wt * _ssim(p[b], gf[b]) for wt, b in zip(wts, blocks))
    return max(0.0, alpha * so + (1 - alpha) * sr)


def independent_dir(gt_dir, pred_dir, names):
    import cv2
    out = []
    for nm in names:
        pr = cv2.imread(os.path.join(pred_dir, nm), cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(os.path.join(gt_dir, nm), cv2.IMREAD_GRAYSCALE)
        if pr.shape != gt.shape:
            pr = cv2.resize(pr, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
        out.append(independent_sm(pr, gt))
    return out


def primary_per_image_sm(gt_dir, pred_dir, names):
    import cv2
    import metrics as Measure
    sm = Measure.Smeasure()
    for nm in names:
        pr = cv2.imread(os.path.join(pred_dir, nm), cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(os.path.join(gt_dir, nm), cv2.IMREAD_GRAYSCALE)
        if pr.shape != gt.shape:
            pr = cv2.resize(pr, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
        sm.step(pred=pr, gt=gt)
    return [float(x) for x in sm.sms]


# ---------------------------------------------------------------------------

def _committed(path, rid, ep):
    for r in csv.DictReader(open(os.path.join(K.REPO, path))):
        if r['runid'] == rid and r['endpoint'] == ep:
            return r
    return None


def _task(t):
    arm, path, s, ep = t
    rid = 'SINet_%s_s%d' % (arm, s)
    pred = K.orig(os.path.join('Result/ABC', rid, ep))
    gt = os.path.join(K.REPO, 'Dataset/Test', ep, 'GT')
    got = primary(gt, pred)
    ref = _committed(path, rid, ep)
    row = dict(runid=rid, arm=arm, seed=s, endpoint=ep, committed_source=path, n=got['n'],
               shape_mismatch=got['shape_mismatch'])
    ok = ref is not None and int(ref['n']) == got['n']
    for k in METRICS:
        v = round(got[k], 6)
        row[k] = '%.6f' % v
        row[k + '_committed'] = ref[k] if ref else ''
        ok = ok and ref is not None and abs(v - float(ref[k])) < 5e-7
    row['reproduces_6dp'] = ok
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--validate-b1', action='store_true')
    ap.add_argument('--rescore-historical', action='store_true')
    ap.add_argument('--independent', type=int, default=0)
    ap.add_argument('--procs', type=int, default=8)
    args = ap.parse_args()

    if args.validate_b1:
        r = primary(os.path.join(K.REPO, 'Dataset/Test/COD10K/GT'),
                    os.path.join(K.REPO, 'Result/SINet/S2C'))
        ok = abs(round(r['Sm'], 6) - B1_SA) < 5e-7 and abs(round(r['MAE'], 6) - B1_MAE) < 5e-7
        print('B1 validation: Sm=%.6f (B1 %.6f) MAE=%.6f (B1 %.6f) n=%d -> %s'
              % (r['Sm'], B1_SA, r['MAE'], B1_MAE, r['n'], 'PASS' if ok else 'FAIL'))
        if not ok:
            raise SystemExit(1)

    if args.rescore_historical:
        tasks = [(a, p, s, ep) for a, p in REUSED for s in SEEDS for ep in ENDPOINTS]
        with Pool(args.procs) as pool:
            rows = pool.map(_task, tasks)
        K.write_csv(os.path.join(K.TABLES, 'EXP-01_reuse_R5_rescore.csv'), rows)
        nok = sum(r['reproduces_6dp'] for r in rows)
        for r in rows:
            print('%-20s %-6s Sm %s (committed %s) %s' % (r['runid'], r['endpoint'], r['Sm'],
                                                          r['Sm_committed'], r['reproduces_6dp']))
        print('R5: %d/%d run x endpoint cells reproduce all 9 metrics at 6 dp' % (nok, len(rows)))
        if nok != len(rows):
            raise SystemExit(1)

    if args.independent:
        rng = np.random.default_rng(0)
        rows = []
        for a, _ in REUSED[:3]:
            for s in SEEDS:
                rid = 'SINet_%s_s%d' % (a, s)
                for ep in ENDPOINTS:
                    gt = os.path.join(K.REPO, 'Dataset/Test', ep, 'GT')
                    pred = K.orig(os.path.join('Result/ABC', rid, ep))
                    names = sorted(os.listdir(gt))
                    pick = [names[i] for i in sorted(rng.choice(len(names), args.independent, replace=False))]
                    x = primary_per_image_sm(gt, pred, pick)
                    y = independent_dir(gt, pred, pick)
                    d = np.abs(np.array(x) - np.array(y))
                    rows.append(dict(runid=rid, endpoint=ep, n_images=len(pick),
                                     max_abs_diff=float(d.max()), n_over_1e6=int((d > 1e-6).sum()),
                                     mean_primary=float(np.mean(x)), mean_independent=float(np.mean(y))))
                    print('%-20s %-6s n=%d max|diff|=%.2e n>1e-6=%d' % (rid, ep, len(pick), d.max(),
                                                                       (d > 1e-6).sum()))
        K.write_csv(os.path.join(K.TABLES, 'EXP-01_independent_sm_check.csv'), rows)


if __name__ == '__main__':
    main()

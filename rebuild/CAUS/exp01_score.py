#!/usr/bin/env python
"""CAUS EXP-01 -- scoring on CPU, with an independent second computation of S-alpha.

The scorer of record is the COMMITTED one, called unchanged: rebuild/ABC/abc_evaluate.score
(Eval/metrics.py over the PNGs MyTest.py wrote, 6 dp). Two checks guard it:
  * validate_b1()  -- reproduces B1's committed SINet/S2C COD10K Sa = 0.717216, MAE = 0.074463
                      (tolerance 1e-5, the committed TOL) before any other number is produced;
  * indep_sm()     -- an S-measure written from the definition (Fan et al., ICCV 2017;
                      alpha = 0.5, object + region terms, centroid split, region SSIM),
                      sharing no code with Eval/metrics.py, compared per image on a fixed
                      deterministic subset.

Modes:
  --validate-b1
  --historical            re-score committed predictions of the reused / reference runs and
                          compare to the committed metrics CSVs at 6 dp (reuse gate R5)
  --run DIR [--rid RID]   score one new run's DIR/{COD10K,NC4K}
  --indep N               with --historical or --run: independent S-alpha on N images per set
"""

import argparse
import csv
import os
import sys

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _p in (_HERE, _REBUILD, os.path.join(_REBUILD, 'ABC'), os.path.join(os.path.dirname(_REBUILD), 'Eval')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                             # noqa: E402

import caus_common as K                                        # noqa: E402

B1_SA, B1_MAE, TOL = 0.717216, 0.074463, 1e-5
ENDPOINTS = ('COD10K', 'NC4K')
METRIC_KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
# reuse gate R5: which committed CSV holds each historical run's metrics
HIST = {'B': 'rebuild/ABC/out/or/abc_metrics.csv', 'C10': 'rebuild/ABC/out/or/abc_metrics.csv',
        'CORACLE': 'rebuild/ABC/out/or/abc_metrics.csv', 'CSHUF': 'rebuild/ABC/out/t2/abc_metrics.csv'}


def gt_dir(endpoint):
    return os.path.join(K.REPO, 'Dataset/Test/%s/GT' % endpoint)


def score(gtd, predd):
    import abc_evaluate as E                                   # committed scorer, unchanged
    return E.score(gtd, predd)


# ---------------------------------------------------------------- independent S-measure
def _prep(pred_u8, gt_u8):
    g = gt_u8 > 128
    p = pred_u8.astype(np.float64) / 255.0
    lo, hi = p.min(), p.max()
    if hi > lo:
        p = (p - lo) / (hi - lo)
    return p, g.astype(np.float64)


def _obj_term(x, mask):
    v = x[mask > 0.5]
    mu = v.mean()
    sd = v.std(ddof=1) if v.size > 1 else 0.0
    return 2.0 * mu / (mu * mu + 1.0 + sd + 1e-16)


def _ssim_block(p, g):
    n = p.size
    mp, mg = p.mean(), g.mean()
    vp = ((p - mp) ** 2).sum() / (n - 1)
    vg = ((g - mg) ** 2).sum() / (n - 1)
    cpg = ((p - mp) * (g - mg)).sum() / (n - 1)
    num = 4.0 * mp * mg * cpg
    den = (mp * mp + mg * mg) * (vp + vg)
    if num != 0:
        return num / (den + 1e-16)
    return 1.0 if den == 0 else 0.0


def indep_sm(pred_u8, gt_u8, alpha=0.5):
    p, g = _prep(pred_u8, gt_u8)
    fg_ratio = g.mean()
    if fg_ratio == 0:
        return float(1.0 - p.mean())
    if fg_ratio == 1:
        return float(p.mean())
    # object-aware term: foreground and background similarity, weighted by area
    s_obj = fg_ratio * _obj_term(p * g, g) + (1 - fg_ratio) * _obj_term((1 - p) * (1 - g), 1 - g)
    # region-aware term: split at the (1-based, rounded) GT centroid into four blocks
    h, w = g.shape
    area = g.sum()
    cx = int(np.round((g.sum(axis=0) * np.arange(w)).sum() / area)) + 1
    cy = int(np.round((g.sum(axis=1) * np.arange(h)).sum() / area)) + 1
    blocks = ((slice(0, cy), slice(0, cx)), (slice(0, cy), slice(cx, w)),
              (slice(cy, h), slice(0, cx)), (slice(cy, h), slice(cx, w)))
    wts = (cx * cy / (h * w), cy * (w - cx) / (h * w), (h - cy) * cx / (h * w))
    wts = wts + (1 - sum(wts),)
    s_reg = sum(wt * _ssim_block(p[b], g[b]) for wt, b in zip(wts, blocks))
    return float(max(0.0, alpha * s_obj + (1 - alpha) * s_reg))


def indep_check(gtd, predd, n, seed=0):
    """Independent vs committed per-image S-alpha on a deterministic subset of n images."""
    import cv2
    import metrics as Measure
    names = sorted(os.listdir(gtd))
    rng = np.random.default_rng(seed)
    pick = sorted(rng.choice(len(names), size=min(n, len(names)), replace=False).tolist())
    ref = Measure.Smeasure()
    diffs = []
    for i in pick:
        nm = names[i]
        pr = cv2.imread(os.path.join(predd, nm), cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(os.path.join(gtd, nm), cv2.IMREAD_GRAYSCALE)
        if pr.shape != gt.shape:
            pr = cv2.resize(pr, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
        ref.step(pred=pr, gt=gt)
        diffs.append(abs(ref.sms[-1] - indep_sm(pr, gt)))
    return dict(n_checked=len(pick), max_abs_diff=float(max(diffs)), mean_abs_diff=float(np.mean(diffs)))


# ---------------------------------------------------------------- tasks
def _task(t):
    out = dict(t)
    out.update(score(t['gt'], t['pred']))
    if t.get('indep'):
        out.update({'indep_' + k: v for k, v in indep_check(t['gt'], t['pred'], t['indep']).items()})
    return out


def validate_b1():
    v = score(gt_dir('COD10K'), os.path.join(K.REPO, 'Result/SINet/S2C'))
    ok = abs(v['Sm'] - B1_SA) <= TOL and abs(v['MAE'] - B1_MAE) <= TOL
    print('B1 validation: Sm %.6f (ref %.6f)  MAE %.6f (ref %.6f)  -> %s'
          % (v['Sm'], B1_SA, v['MAE'], B1_MAE, 'PASS' if ok else 'FAIL'))
    return ok, v


def historical(indep, workers):
    from multiprocessing import Pool
    ref = {}
    for arm, f in HIST.items():
        for r in csv.DictReader(open(os.path.join(K.REPO, f))):
            if r['arch'] == 'SINet' and r['arm'] == arm:
                ref[(r['runid'], r['endpoint'])] = r
    tasks = []
    for arm in HIST:
        for s in (42, 43, 45):
            rid = 'SINet_%s_s%d' % (arm, s)
            for e in ENDPOINTS:
                tasks.append(dict(runid=rid, arm=arm, seed=s, endpoint=e, gt=gt_dir(e),
                                  pred=K.orig('Result/ABC/%s/%s' % (rid, e)), indep=indep,
                                  committed_csv=HIST[arm]))
    with Pool(workers) as pool:
        res = pool.map(_task, tasks)
    rows = []
    for r in res:
        c = ref[(r['runid'], r['endpoint'])]
        row = dict(runid=r['runid'], arm=r['arm'], seed=r['seed'], endpoint=r['endpoint'],
                   n=r['n'], committed_csv=r['committed_csv'])
        exact = True
        for k in METRIC_KEYS:
            row[k] = '%.6f' % r[k]
            row['committed_' + k] = c[k]
            exact &= ('%.6f' % r[k]) == c[k]
        row['reproduces_6dp'] = exact
        for k in ('indep_n_checked', 'indep_max_abs_diff', 'indep_mean_abs_diff'):
            row[k] = r.get(k, '')
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--validate-b1', action='store_true')
    ap.add_argument('--historical', action='store_true')
    ap.add_argument('--run', default='')
    ap.add_argument('--rid', default='')
    ap.add_argument('--indep', type=int, default=0)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--out', default='')
    args = ap.parse_args()
    ok, v = validate_b1()
    if not ok:
        raise SystemExit('CAUS SCORE HALT: scorer does not reproduce B1')
    if args.historical:
        rows = historical(args.indep, args.workers)
        out = args.out or os.path.join(K.TABLES, 'EXP-01_reuse_gate_R5_rescore.csv')
        K.write_csv(out, rows)
        n_ok = sum(r['reproduces_6dp'] for r in rows)
        print('R5: %d/%d historical (run, endpoint) sets reproduce committed metrics at 6 dp' % (n_ok, len(rows)))
        if args.indep:
            print('independent S-alpha max |diff| over subsets: %.3g'
                  % max(float(r['indep_max_abs_diff']) for r in rows))
    if args.run:
        from multiprocessing import Pool
        tasks = [dict(runid=args.rid, endpoint=e, gt=gt_dir(e), pred=os.path.join(args.run, e),
                      indep=args.indep) for e in ENDPOINTS if os.path.isdir(os.path.join(args.run, e))]
        with Pool(min(len(tasks), args.workers)) as pool:
            res = pool.map(_task, tasks)
        rows = [{k: r[k] for k in r if k not in ('gt', 'indep')} for r in res]
        out = args.out or os.path.join(args.run, 'metrics.csv')
        K.write_csv(out, rows)
        for r in rows:
            print('%s %s Sm=%.6f MAE=%.6f indep_max=%s' % (r['runid'], r['endpoint'], r['Sm'], r['MAE'],
                                                           r.get('indep_max_abs_diff', '')))


if __name__ == '__main__':
    main()

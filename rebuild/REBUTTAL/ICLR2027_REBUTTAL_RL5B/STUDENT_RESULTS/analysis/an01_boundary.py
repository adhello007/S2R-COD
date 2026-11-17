"""AN-01 -- boundary-metric re-scoring of all eight-seed runs, with covariates (EXPLORATORY / POST HOC).

Stage 1 (--stage gate): reproduction gate. Re-derive the committed per-run boundary tables that
  tab:boundary / table_subgroup_metrics.tex were built from
    rebuild/DIAG/out/diag_boundary_per_run.csv        (threshold 0.5, 36 runs, 3 seeds)
    rebuild/DIAG/out/diag_boundary_per_run_t0.40.csv  (12 runs)
    rebuild/DIAG/out/diag_boundary_per_run_t0.60.csv  (12 runs)
  from the saved prediction maps with analysis/boundary_scorer.py, and require every per-run value
  to agree to 1e-12. Also unit-test Boundary IoU against the reference implementation of
  Cheng et al. (2021), boundary_iou_api `mask_to_boundary` (re-implemented below from the published
  code: pad by 1, cv2.erode 3x3 for `dilation` iterations, boundary = mask - eroded).
Stage 2 (--stage full): score all 64 SE runs (B, C10, CSHUF, CINV x 8 seeds x 2 architectures) on
  COD10K-test and NC4K at thresholds 0.4/0.5/0.6; apply the manuscript's verdict rule with the SE
  campaign's own pooled sigma-hat per metric (df = 28, sign >= 7/8 seed-paired); exploratory
  regression with pseudo-label count and Jaccard(injected set, C10 set) as covariates; SINet-v2
  diagnostics (per-arm SDs, minimum detectable effect). Every output is labelled EXPLORATORY.

Run: .venv/bin/python an01_boundary.py --stage gate|full [--workers 32]
"""
import argparse
import csv
import json
import math
import os

import numpy as np

import _repo as R
import boundary_scorer as BS

DIAG_OUT = os.path.join(R.REPO, 'rebuild', 'DIAG', 'out')
SE_ARMS = ('B', 'C10', 'CSHUF', 'CINV')
SE_SEEDS = (42, 43, 45, 46, 47, 48, 49, 50)
ARCHS = ('SINet', 'SINetv2')
ENDPOINTS = ('COD10K', 'NC4K')
THRESH = (0.4, 0.5, 0.6)
CONTRASTS = (('C10', 'B'), ('CINV', 'B'), ('CSHUF', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'))
LABEL = 'EXPLORATORY / POST HOC -- decides nothing'


def pred(rid, ep):
    return os.path.join(R.REPO, 'Result', 'ABC', rid, ep)


def reference_mask_to_boundary(mask, dilation_ratio=0.02):
    """Cheng et al. 2021, boundary_iou_api/boundary_iou/utils/boundary_utils.py (published code)."""
    import cv2
    h, w = mask.shape
    img_diag = np.sqrt(h ** 2 + w ** 2)
    dilation = int(round(dilation_ratio * img_diag))
    if dilation < 1:
        dilation = 1
    new_mask = cv2.copyMakeBorder(mask, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    kernel = np.ones((3, 3), dtype=np.uint8)
    new_mask_erode = cv2.erode(new_mask, kernel, iterations=dilation)
    mask_erode = new_mask_erode[1: h + 1, 1: w + 1]
    return mask - mask_erode


def unit_test_biou():
    """Boundary IoU from diag_boundary.metrics_one vs the reference mask_to_boundary on real pairs."""
    from PIL import Image
    gt_dir = os.path.join(R.REPO, 'Dataset', 'Test', 'COD10K', 'GT')
    names = sorted(os.listdir(gt_dir))[:25]
    worst = 0.0
    for nm in names:
        g = (np.array(Image.open(os.path.join(gt_dir, nm)).convert('L')) > 127)
        p = np.array(Image.open(os.path.join(pred('SINet_C10_s42', 'COD10K'), nm)).convert('L')).astype(np.float64)
        rng = p.max() - p.min()
        p = (p - p.min()) / rng if rng > 0 else p * 0
        pb = p >= 0.5
        ours = BS.metrics_one(g, pb, float(np.hypot(*g.shape)))['boundary_iou']
        gb = reference_mask_to_boundary(g.astype(np.uint8))
        pbb = reference_mask_to_boundary(pb.astype(np.uint8))
        inter, union = int(((gb * pbb) > 0).sum()), int(((gb + pbb) > 0).sum())
        ref = inter / union if union else float('nan')
        if not (math.isnan(ours) and math.isnan(ref)):
            worst = max(worst, abs(ours - ref))
    return dict(images=len(names), max_abs_diff=worst, passed=worst < 1e-12)


def gate(workers):
    out = {}
    for fname, thr in (('diag_boundary_per_run.csv', 0.5), ('diag_boundary_per_run_t0.40.csv', 0.4),
                       ('diag_boundary_per_run_t0.60.csv', 0.6)):
        rows = list(csv.DictReader(open(os.path.join(DIAG_OUT, fname))))
        runs = [(r['runid'], pred(r['runid'], 'COD10K'), 'COD10K') for r in rows]
        agg, _ = BS.score_runs(runs, (thr,), workers)
        worst, n = 0.0, 0
        for r in rows:
            mine = agg[(r['runid'], thr)]
            for m in BS.METRICS:
                worst = max(worst, abs(mine[m] - float(r[m])))
                n += 1
            assert mine['n'] == int(r['n'])
        out[fname] = dict(threshold=thr, runs=len(rows), values_compared=n, max_abs_diff=worst, passed=worst < 1e-12)
        print('%-36s thr %.1f  %d runs  max |diff| %.3g -> %s' % (fname, thr, len(rows), worst,
                                                                 'MATCH' if worst < 1e-12 else 'MISMATCH'), flush=True)
    ut = unit_test_biou()
    print('Boundary-IoU unit test vs Cheng et al. mask_to_boundary on %d images: max |diff| %.3g -> %s'
          % (ut['images'], ut['max_abs_diff'], 'PASS' if ut['passed'] else 'FAIL'), flush=True)
    out['unit_test_reference_biou'] = ut
    out['GATE'] = 'PASS' if all(v['passed'] for v in out.values() if isinstance(v, dict)) else 'FAIL'
    json.dump(out, open(os.path.join(R.LOGS, 'AN01_reproduction_gate.json'), 'w'), indent=2)
    print('AN-01 reproduction gate:', out['GATE'])
    return out['GATE'] == 'PASS'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['gate', 'full'], required=True)
    ap.add_argument('--workers', type=int, default=32)
    ap.add_argument('--reuse', action='store_true', help='full stage: rebuild tables from the committed per-run CSV')
    a = ap.parse_args()
    if a.stage == 'gate':
        gate(a.workers)
    else:
        import an01_full
        an01_full.run(a.workers, reuse=a.reuse)


if __name__ == '__main__':
    main()

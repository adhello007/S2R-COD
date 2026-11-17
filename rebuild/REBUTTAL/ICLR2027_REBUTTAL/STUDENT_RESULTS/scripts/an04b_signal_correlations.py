#!/usr/bin/env python
"""AN-04 (part b): uncertainty score vs per-pixel and structural error (+0.8553 vs +0.4276).

Calls the UNCHANGED base function rebuild/B1/b1_es_error_correlation.step_correlate (k = 75, 10 k-means
seeds, clusters with >= 15 endpoint images), with only E0_CACHE redirected to the original working
copy's committed cache. Gate: SINet/S2C must reproduce the committed b1_correlations.json values to 1e-9.
Adds an architecture breakdown (every committed per-image score file) and a COD10K super-class
breakdown of the per-image Spearman rho. Endpoint labels are used only descriptively.

Outputs: RESULT_TABLES/AN-04_signal_correlations.csv, EXPERIMENT_LOGS/AN-04b_summary.json
"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np
from scipy.stats import spearmanr

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
for p in (os.path.join(WT, 'rebuild'), os.path.join(WT, 'rebuild/B1')):
    sys.path.insert(0, p)
import b1_es_error_correlation as B1      # noqa: E402  (base, unchanged)

B1.E0_CACHE = os.path.join(DR, 'rebuild/E0/cache')
ARCHS = ['SINet/S2C', 'SINet-v2/S2C', 'SegMaR/S2C', 'SINet/S2C_MT', 'SINet/S2C_SO']


def main():
    t0 = time.time()
    X, tnames, lmeta = B1.load_target('dinoL518')
    committed = json.load(open(os.path.join(WT, 'rebuild/B1/out/b1_correlations.json')))['SINet/S2C|test|k75']
    rows, gate = [], {}
    for arch in ARCHS:
        r = B1.step_correlate(X, tnames, 75, arch, 'test', tag='dinoL518')
        if r is None:
            continue
        row = dict(arch=arch, k=75, n_images=r['n_images'])
        for err in B1.ERRORS:
            pc = r['percluster_%s' % err]
            row['percluster_rho_mean_' + err] = pc['rho_mean']
            row['percluster_rho_sd_' + err] = pc['rho_sd']
            row['per_image_rho_' + err] = r['per_image'][err]['rho']
        row['ratio_structural_over_pixel'] = row['percluster_rho_mean_one_minus_sa'] / row['percluster_rho_mean_mae']
        rows.append(row)
        if arch == 'SINet/S2C':
            for err in ('mae', 'one_minus_sa'):
                mine = r['percluster_%s' % err]['rho_mean']
                ref = committed['percluster_%s' % err]['rho_mean']
                gate[err] = dict(mine=mine, committed=ref, match_1e9=abs(mine - ref) < 1e-9)
        # super-class breakdown of the per-image rho (descriptive)
        sc = {}
        for s in B1.load_scores(arch, 'test'):
            parts = s['name'].split('-')
            key = parts[3] if len(parts) > 3 else 'other'
            sc.setdefault(key, []).append(s)
        for key, ss in sorted(sc.items()):
            if len(ss) < 30:
                continue
            rows.append(dict(arch=arch, k='per-image, super-class %s' % key, n_images=len(ss),
                             per_image_rho_mae=float(spearmanr([x['es'] for x in ss], [x['mae'] for x in ss]).statistic),
                             per_image_rho_one_minus_sa=float(spearmanr([x['es'] for x in ss], [x['one_minus_sa'] for x in ss]).statistic),
                             per_image_rho_one_minus_iou=float(spearmanr([x['es'] for x in ss], [x['one_minus_iou'] for x in ss]).statistic)))
    cols = []
    for r in rows:
        cols += [c for c in r if c not in cols]
    with open(os.path.join(SR, 'RESULT_TABLES/AN-04_signal_correlations.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()})
    summ = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), target_meta=lmeta, gate=gate,
                gate_passed=all(g['match_1e9'] for g in gate.values()),
                archs={r['arch']: dict(mae=r['percluster_rho_mean_mae'], one_minus_sa=r['percluster_rho_mean_one_minus_sa'],
                                       ratio=r['ratio_structural_over_pixel']) for r in rows if r['k'] == 75},
                seconds=round(time.time() - t0, 1))
    json.dump(summ, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-04b_summary.json'), 'w'), indent=1, default=str)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == '__main__':
    main()

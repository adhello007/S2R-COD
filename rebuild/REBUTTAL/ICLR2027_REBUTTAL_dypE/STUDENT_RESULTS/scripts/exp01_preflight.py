#!/usr/bin/env python
"""EXP-01 preflight (CPU only) -- does a larger matched budget actually enlarge the B-vs-C10 contrast?

ANALYSIS_PRESPEC.md §10. Uses the UNCHANGED base selection (abc_common.arm_b_stems / arm_c_stems,
C1 allocation + greedy selection) at budget N by rebinding abc_common.BUDGET. N=1000 must reproduce
the committed stem files byte for byte. No training is launched (EXP-01 training is BLOCKED: no GPU).

Primary contrast (fixed before running): DC(N) = mean_seeds (N - |B_N ∩ C10_N|) / (4447 + N).
Pass: some N in {2000, 3000} with DC(N) >= 1.5 * DC(1000) AND min_seeds DC(N) > max_seeds DC(1000).

Outputs: RESULT_TABLES/EXP-01_preflight.csv, RESULT_TABLES/EXP-01_preflight_by_seed.csv,
         EXPERIMENT_LOGS/EXP-01_preflight.json
"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, os.path.join(SR, 'scripts'))
import basepatch          # noqa: E402

A, c1_space = basepatch.setup(WT, DR)
SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
BUDGETS = [1000, 2000, 3000, 4447]
BASE_N = 4447
ARCH = {'SINet': dict(steps=253, batch=16), 'SINetv2': dict(steps=127, batch=32)}
OUT_SE = os.path.join(WT, 'rebuild/ABC/out/se')


def main():
    t0 = time.time()
    by_seed, rows = [], []
    repro = {}
    for N in BUDGETS:
        A.BUDGET = N
        c10, cell = A.arm_c_stems(1.0, None)
        if N == 1000:
            repro['C10'] = c10 == [l.strip() for l in open(os.path.join(OUT_SE, 'abc_stems_C_a1.0.txt'))]
        dcs = []
        for s in SEEDS:
            b = A.arm_b_stems(s)
            if N == 1000:
                repro['B_s%d' % s] = b == [l.strip() for l in open(os.path.join(OUT_SE, 'abc_stems_B_s%d.txt' % s))]
            I = len(set(b) & set(c10))
            dc = (N - I) / (BASE_N + N)
            dcs.append(dc)
            r = dict(N=N, seed=s, n_B=len(b), n_C10=len(c10), intersection=I, one_sided_diff=N - I,
                     jaccard=I / (2 * N - I), expected_random_intersection=N * N / BASE_N,
                     frac_injection_differs=(N - I) / N, DC_frac_training_pool_differs=dc,
                     distinct_foreground_ids_B=len(set(b)), distinct_foreground_ids_C10=len(set(c10)),
                     novel_foregrounds_vs_base_pool=0, c10_n_displaced=cell['n_displaced'],
                     c10_clusters_funded=cell['clusters_funded'], c10_max_alloc_share=cell['max_alloc_share'])
            for arch, p in ARCH.items():
                draws = p['steps'] * p['batch']
                r['%s_pinned_arm_specific_visits_per_epoch' % arch] = (N - I) * draws / (BASE_N + N)
                r['%s_unpinned_arm_specific_visits_per_epoch' % arch] = float(N - I)
                r['%s_unpinned_steps' % arch] = -(-(BASE_N + N) // p['batch'])
            by_seed.append(r)
        rows.append(dict(N=N, DC_mean=float(np.mean(dcs)), DC_min=float(np.min(dcs)), DC_max=float(np.max(dcs)),
                         one_sided_diff_mean=float(np.mean([x['one_sided_diff'] for x in by_seed if x['N'] == N])),
                         jaccard_mean=float(np.mean([x['jaccard'] for x in by_seed if x['N'] == N])),
                         frac_injection_differs_mean=float(np.mean([x['frac_injection_differs'] for x in by_seed if x['N'] == N])),
                         SINet_pinned_arm_specific_visits_per_epoch_mean=float(np.mean(
                             [x['SINet_pinned_arm_specific_visits_per_epoch'] for x in by_seed if x['N'] == N])),
                         SINetv2_pinned_arm_specific_visits_per_epoch_mean=float(np.mean(
                             [x['SINetv2_pinned_arm_specific_visits_per_epoch'] for x in by_seed if x['N'] == N])),
                         c10_n_displaced=cell['n_displaced'], c10_clusters_funded=cell['clusters_funded'],
                         c10_max_alloc_share=cell['max_alloc_share'], c10_alloc_entropy_norm=cell['alloc_entropy_norm']))
    A.BUDGET = 1000
    base = next(r for r in rows if r['N'] == 1000)
    for r in rows:
        r['DC_ratio_vs_1000'] = r['DC_mean'] / base['DC_mean']
        r['passes_ratio_1p5'] = r['DC_ratio_vs_1000'] >= 1.5
        r['passes_min_gt_max1000'] = r['DC_min'] > base['DC_max']
        r['passes_preflight'] = (r['N'] in (2000, 3000) and r['passes_ratio_1p5'] and r['passes_min_gt_max1000'])
    passing = [r['N'] for r in rows if r['passes_preflight']]
    for name, rs in (('EXP-01_preflight.csv', rows), ('EXP-01_preflight_by_seed.csv', by_seed)):
        with open(os.path.join(SR, 'RESULT_TABLES', name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]))
            w.writeheader()
            for r in rs:
                w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in r.items()})
    out = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               reproduction_N1000=repro, reproduction_all=all(repro.values()),
               rule='pass iff some N in {2000,3000}: DC(N) >= 1.5*DC(1000) and min_seed DC(N) > max_seed DC(1000)',
               passing_budgets=passing, preflight_passed=bool(passing),
               proposed_N=(min(passing) if passing else None),
               training_status='BLOCKED (compute: no GPU available before the 17 Nov cutoff)',
               summary=rows, seconds=round(time.time() - t0, 1))
    json.dump(out, open(os.path.join(SR, 'EXPERIMENT_LOGS/EXP-01_preflight.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()

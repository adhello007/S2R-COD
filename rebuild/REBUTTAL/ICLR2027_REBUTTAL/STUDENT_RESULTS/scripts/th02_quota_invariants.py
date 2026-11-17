#!/usr/bin/env python
"""TH-02 -- quota-multiset invariants and concentration indicators (ANALYSIS_PRESPEC.md §6).

Recomputes every arm's 75 quotas with the UNCHANGED base functions (softmax_alloc,
largest_remainder, es_permutation) on the committed target_es, and the selected stems with the
unchanged arm_c_stems / arm_b_stems. Verifies them against the committed stem files.

Outputs:
  RESULT_TABLES/TH-02_quota_invariants.csv     one row per arm (summary + invariant checks)
  RESULT_TABLES/TH-02_quota_vectors.csv        75 clusters x arms (nominal quotas, realised counts)
  EXPERIMENT_LOGS/TH-02_checks.json
"""
import argparse
import csv
import json
import math
import os
import sys

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
from c1_targeted_vs_random import (softmax_alloc, largest_remainder, rank_by_centroid,   # noqa: E402
                                   serving_orders)

SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
OUT_SE = os.path.join(WT, 'rebuild/ABC/out/se')


def conc(counts):
    q = np.asarray(counts, np.float64)
    p = q / q.sum()
    k = len(p)
    nz = p[p > 0]
    ent = float(-(nz * np.log(nz)).sum() / math.log(k))
    hhi = float((p ** 2).sum())
    srt = np.sort(p)
    gini = float((2 * np.arange(1, k + 1) - k - 1) @ srt / (k * srt.sum()))
    return dict(entropy_norm=ent, hhi=hhi, hhi_effective_clusters=1.0 / hhi, gini=gini,
                max_share=float(p.max()), clusters_funded=int((q > 0).sum()),
                tv_from_uniform=float(0.5 * np.abs(p - 1.0 / k).sum()))


def greedy_with_cluster(alloc, order_idx, serving):
    """Re-implementation of base greedy_select that also records which cluster took each item."""
    taken = np.zeros(order_idx.shape[0], dtype=bool)
    picked, by, displaced = [], {}, 0
    for c in serving:
        need = int(alloc[c])
        if need <= 0:
            continue
        got = 0
        for row in order_idx[:, c]:
            if taken[row]:
                displaced += 1
                continue
            taken[row] = True
            picked.append(int(row))
            by[int(row)] = c
            got += 1
            if got == need:
                break
    return np.array(sorted(picked)), by, displaced


def main():
    sp = c1_space.load_space(A.EMBEDDER)
    es = sp.es
    k = sp.k
    s_e = float(np.std(es))                         # population SD, as softmax_alloc uses
    scores, order = rank_by_centroid(sp)
    nearest = np.argmax(sp.cut @ sp.centroids.T, axis=1)   # each cutout's nearest centroid
    name_idx = {n: i for i, n in enumerate(sp.names)}
    arms = {'C10': None, 'CSHUF': 'shuffled', 'CINV': 'rank_reversed', 'CORACLE': 'oracle_rank'}
    committed_file = {'C10': 'abc_stems_C_a1.0.txt', 'CSHUF': 'abc_stems_CSHUF.txt',
                      'CINV': 'abc_stems_CINV.txt'}
    vec, summ, checks = {}, [], dict(s_e=s_e, s_e_manuscript=0.0101, k=k)
    es_rank = np.argsort(np.argsort(es, kind='stable'), kind='stable')   # 0 = lowest ES
    for arm, kind in arms.items():
        sigma, info = A.es_permutation(es, kind)
        es_used = es if kind is None else es[sigma]
        p = softmax_alloc(es_used, 1.0)
        alloc = largest_remainder(p, A.BUDGET)
        serving = serving_orders(alloc, es_used)[A.SERVING]
        idx, by, disp = greedy_with_cluster(alloc, order, serving)
        stems_base, cell = A.arm_c_stems(A.ARM_ALPHA[arm], A.ARM_ES_PERM[arm])
        mine = [sp.names[i] for i in idx]
        same_as_base_call = mine == stems_base
        cf = committed_file.get(arm)
        committed = [l.strip() for l in open(os.path.join(OUT_SE, cf))] if cf else None
        realised = np.bincount([by[i] for i in idx], minlength=k)
        nearest_hist = np.bincount(nearest[idx], minlength=k)
        fixed = np.where(sigma == np.arange(k))[0]
        vec[arm] = dict(alloc=alloc, realised=realised, nearest=nearest_hist)
        row = dict(arm=arm, kind=str(kind), sum_quotas=int(alloc.sum()),
                   sorted_quota_multiset=' '.join(map(str, sorted(alloc.tolist(), reverse=True))),
                   perm_rho=info.get('perm_rho'), perm_fixed_points=int(len(fixed)),
                   fixed_point_clusters=' '.join(map(str, fixed.tolist())),
                   fixed_point_es_rank_1based=' '.join(str(int(es_rank[f]) + 1) for f in fixed),
                   n_displaced=disp, n_displaced_committed_cell=cell['n_displaced'],
                   selection_equals_base_arm_c_stems=same_as_base_call,
                   selection_equals_committed_file=(None if committed is None else mine == committed),
                   realised_equals_nominal=bool(np.array_equal(realised, alloc)),
                   n_clusters_realised_ne_nominal=int((realised != alloc).sum()),
                   uses_endpoint_labels=(arm == 'CORACLE'),
                   **{'nominal_' + kk: vv for kk, vv in conc(alloc).items()},
                   **{'nearest_centroid_' + kk: vv for kk, vv in conc(nearest_hist).items()})
        summ.append(row)
    # B: expected counts (uniform draw) and realised per seed, by nearest centroid
    pool_hist = np.bincount(nearest, minlength=k)
    exp_b = pool_hist * A.BUDGET / len(nearest)
    vec['B_expected'] = dict(alloc=exp_b, realised=exp_b, nearest=exp_b)
    summ.append(dict(arm='B (expected under uniform draw)', kind='uniform', sum_quotas=float(exp_b.sum()),
                     **{'nominal_' + kk: vv for kk, vv in conc(exp_b).items()},
                     **{'nearest_centroid_' + kk: vv for kk, vv in conc(exp_b).items()}))
    b_ok = []
    for s in SEEDS:
        st = A.arm_b_stems(s)
        committed = [l.strip() for l in open(os.path.join(OUT_SE, 'abc_stems_B_s%d.txt' % s))]
        b_ok.append(st == committed)
        h = np.bincount(nearest[[name_idx[x] for x in st]], minlength=k)
        vec['B_s%d' % s] = dict(alloc=h, realised=h, nearest=h)
        summ.append(dict(arm='B_s%d' % s, kind='uniform draw', sum_quotas=int(h.sum()),
                         selection_equals_committed_file=st == committed,
                         **{'nearest_centroid_' + kk: vv for kk, vv in conc(h).items()}))
    # invariants
    ms = {arm: sorted(vec[arm]['alloc'].tolist()) for arm in arms}
    checks.update(
        all_sum_1000=all(int(vec[arm]['alloc'].sum()) == 1000 for arm in arms),
        multiset_equal_C10_CSHUF=ms['C10'] == ms['CSHUF'], multiset_equal_C10_CINV=ms['C10'] == ms['CINV'],
        multiset_equal_C10_CORACLE=ms['C10'] == ms['CORACLE'],
        per_cluster_C10_vs_CSHUF_differs=int((vec['C10']['alloc'] != vec['CSHUF']['alloc']).sum()),
        per_cluster_C10_vs_CINV_differs=int((vec['C10']['alloc'] != vec['CINV']['alloc']).sum()),
        cinv_single_fixed_point_is_median=(
            next(r for r in summ if r['arm'] == 'CINV')['fixed_point_es_rank_1based'] == str((k + 1) // 2)),
        cshuf_no_fixed_point=next(r for r in summ if r['arm'] == 'CSHUF')['perm_fixed_points'] == 0,
        cshuf_rho=next(r for r in summ if r['arm'] == 'CSHUF')['perm_rho'],
        c_family_selection_matches_committed=all(r['selection_equals_committed_file'] for r in summ
                                                 if r['arm'] in committed_file),
        b_selection_matches_committed_all_seeds=all(b_ok),
        es_ties=int(len(es) - len(np.unique(es))),
        quota_remainder_units=int(1000 - np.floor(softmax_alloc(es, 1.0) * 1000).sum()))
    with open(os.path.join(SR, 'RESULT_TABLES/TH-02_quota_invariants.csv'), 'w', newline='') as f:
        cols = []
        for r in summ:
            cols += [c for c in r if c not in cols]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in summ:
            w.writerow({c: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for c, v in r.items()})
    with open(os.path.join(SR, 'RESULT_TABLES/TH-02_quota_vectors.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        keys = list(vec)
        w.writerow(['cluster', 'target_es', 'es_rank_1based', 'n_target', 'n_cutouts_nearest']
                   + ['%s_%s' % (kk, t) for kk in keys for t in ('nominal', 'realised', 'nearest')])
        for c in range(k):
            w.writerow([c, repr(float(es[c])), int(es_rank[c]) + 1, int(sp.n_target[c]), int(pool_hist[c])]
                       + [('%.6g' % vec[kk][t][c]) for kk in keys for t in ('alloc', 'realised', 'nearest')])
    json.dump(checks, open(os.path.join(SR, 'EXPERIMENT_LOGS/TH-02_checks.json'), 'w'), indent=1, default=str)
    print(json.dumps(checks, indent=1, default=str))
    for r in summ[:4]:
        print(r['arm'], {kk: r[kk] for kk in ('nominal_entropy_norm', 'nominal_hhi', 'nominal_gini', 'nominal_max_share',
                                              'nominal_clusters_funded', 'n_displaced', 'realised_equals_nominal')})


if __name__ == '__main__':
    main()

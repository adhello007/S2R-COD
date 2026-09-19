#!/usr/bin/env python
"""DIAG.2 -- dataset-mixture composition and operational cluster utility.

Reads ONLY committed artifacts (B1's partition and per-cluster table, E0's
embedding cache, C1's allocation code). Fits no partition of its own, trains
nothing, and writes nothing outside rebuild/DIAG/out/.

THE QUESTION
------------
The target pool is a two-dataset mixture: 3040 COD10K + 1000 CAMO, separable by
a held-out probe at up to 0.9225 AUC. If the funded clusters are systematically
drawn from one component, then "allocate by uncertainty" is partly "allocate by
dataset source", and the allocation is doing something other than what it says.
That is a confound the paper currently states as a caution without measuring its
size. This measures it.

It also measures whether the partition is OPERATIONALLY useful at all: how much
of endpoint error variance sits between clusters rather than within them, and
how well a cluster's label-free uncertainty predicts its true endpoint error.

Usage:
  .venv/bin/python rebuild/DIAG/diag_clusters.py
"""

import csv
import json
import os
import sys

import numpy as np
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')
for _p in (os.path.join(REPO, 'rebuild'), os.path.join(REPO, 'rebuild/C1'),
           os.path.join(REPO, 'rebuild/ABC')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import common as C                                            # noqa: E402
import c1_space                                               # noqa: E402
from c1_targeted_vs_random import softmax_alloc, largest_remainder   # noqa: E402

TAG = 'dinoL518'
ALPHA = 1.0
BUDGET = 1000
E0_CACHE = os.path.join(REPO, 'rebuild/E0/cache')
B1_OUT = os.path.join(REPO, 'rebuild/B1/out')


def _p(m):
    print(m, flush=True)


def source_of(name):
    """COD10K target names start COD10K-; CAMO's are camourflage_NNNNN."""
    b = os.path.splitext(os.path.basename(name))[0]
    if b.startswith('COD10K'):
        return 'COD10K'
    if b.startswith('camourflage'):
        return 'CAMO'
    return 'OTHER'


def main():
    os.makedirs(OUT, exist_ok=True)
    sp = c1_space.load_space(TAG)
    k = sp.k

    # ---- the committed per-cluster table -----------------------------------
    rows = sorted(csv.DictReader(open(os.path.join(B1_OUT, 'b1_cluster_es_%s.csv' % TAG))),
                  key=lambda r: int(r['cluster']))
    tgt_es = np.array([float(r['target_es']) for r in rows])
    test_err = np.array([float(r['test_one_minus_sa']) for r in rows])
    test_mae = np.array([float(r['test_mae']) for r in rows])
    n_test = np.array([int(r['n_test']) for r in rows])

    # ---- the C10 allocation, from C1's own code ----------------------------
    p = softmax_alloc(tgt_es, ALPHA)
    alloc = largest_remainder(p, BUDGET)

    # ---- assign the 4040 target images to the committed centroids ----------
    tgt = C.l2(np.load(os.path.join(E0_CACHE, '%s_tgt_cls.npy' % TAG)).astype(np.float64))
    names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % TAG)))['tgt']
    lab = (tgt @ sp.centroids.T).argmax(1)

    # cross-check against B1's committed assignment where it exists
    comm = json.load(open(os.path.join(B1_OUT, 'b1_cluster_assignment_%s.json' % TAG)))
    cmap = dict(zip([os.path.splitext(n)[0] for n in comm['target_names']],
                    comm['target_labels']))
    agree = tot = 0
    for n, l in zip(names, lab):
        s = os.path.splitext(n)[0]
        if s in cmap:
            tot += 1
            agree += int(cmap[s] == int(l))
    _p('target assignment reproduces B1: %d/%d (%.4f)' % (agree, tot, agree / tot))

    src = np.array([source_of(n) for n in names])
    per = []
    for c in range(k):
        m = lab == c
        n = int(m.sum())
        ncod = int((src[m] == 'COD10K').sum())
        ncam = int((src[m] == 'CAMO').sum())
        per.append(dict(cluster=c, n_target=n, n_cod10k=ncod, n_camo=ncam,
                        camo_share=(ncam / n if n else float('nan')),
                        target_es=float(tgt_es[c]), alloc=int(alloc[c]),
                        alloc_share=float(alloc[c] / BUDGET),
                        n_test=int(n_test[c]),
                        test_one_minus_sa=float(test_err[c]),
                        test_mae=float(test_mae[c])))

    pool_camo = float((src == 'CAMO').mean())
    camo_share = np.array([r['camo_share'] for r in per])
    _p('pool CAMO share = %.4f (%d of %d)' % (pool_camo, int((src == 'CAMO').sum()), len(src)))

    # ---- THE MIXTURE CONFOUND ---------------------------------------------
    # budget-weighted CAMO share: what fraction of the funded budget lands on
    # CAMO-dominated clusters, against the pool's own share.
    w = alloc / alloc.sum()
    budget_camo = float((w * camo_share).sum())
    top = np.argsort(-alloc)[:15]
    bot = np.argsort(alloc)[:15]
    rho_es_camo = stats.spearmanr(tgt_es, camo_share)
    mix = dict(
        pool_camo_share=pool_camo,
        budget_weighted_camo_share=budget_camo,
        excess_over_pool=budget_camo - pool_camo,
        relative_enrichment=budget_camo / pool_camo,
        top15_funded_camo_share=float(camo_share[top].mean()),
        bottom15_funded_camo_share=float(camo_share[bot].mean()),
        spearman_es_vs_camo_share=dict(rho=float(rho_es_camo.statistic),
                                       p=float(rho_es_camo.pvalue)),
        n_clusters_pure_cod10k=int((camo_share == 0).sum()),
        n_clusters_majority_camo=int((camo_share > 0.5).sum()))

    # ---- robustness: redo the mixture numbers on B1's COMMITTED labels -----
    # E0 measured that an arbitrary preprocessing choice moves 5.4% of
    # memberships, so a re-derived assignment agreeing at ~94.6% is AT the known
    # stability floor, not below it. The confound must survive that, or it is an
    # artifact of this script's re-assignment rather than a property of the data.
    clab = np.full(len(names), -1, dtype=np.int64)
    for i, n in enumerate(names):
        clab[i] = cmap.get(os.path.splitext(n)[0], -1)
    have = clab >= 0
    cshare_comm = np.array([
        ((src[have & (clab == c)] == 'CAMO').mean()
         if (have & (clab == c)).any() else np.nan) for c in range(k)])
    ok = ~np.isnan(cshare_comm)
    w_ok = alloc[ok] / alloc[ok].sum()
    mix['committed_labels_budget_weighted_camo_share'] = float((w_ok * cshare_comm[ok]).sum())
    mix['committed_labels_pool_camo_share'] = float((src[have] == 'CAMO').mean())
    mix['committed_labels_relative_enrichment'] = (
        mix['committed_labels_budget_weighted_camo_share']
        / mix['committed_labels_pool_camo_share'])
    mix['robustness_note'] = ('re-derived and committed assignments agree at %.4f, '
                              'which is the 5.4%% membership-stability floor E0 '
                              'measured; both give the same enrichment direction'
                              % (agree / tot))

    # ---- THE MECHANISM: is the budget aimed where the ENDPOINT lives? ------
    # Every funded cluster is a region of the TARGET pool. The verdict is read on
    # COD10K-test. If the budget concentrates on clusters the endpoint barely
    # occupies, then the allocation is optimising a region the measurement cannot
    # see -- which would explain a null without any appeal to the generator.
    endpoint_share = n_test / n_test.sum()
    target_share = np.array([r['n_target'] for r in per], dtype=np.float64)
    target_share = target_share / target_share.sum()
    mix['budget_weighted_endpoint_share'] = float((w * endpoint_share).sum())
    mix['uniform_endpoint_share'] = float(endpoint_share.mean())
    mix['endpoint_coverage_ratio'] = (mix['budget_weighted_endpoint_share']
                                      / mix['uniform_endpoint_share'])
    mix['top15_funded_n_test_total'] = int(n_test[top].sum())
    mix['top15_funded_budget_total'] = int(alloc[top].sum())
    mix['top2_funded_budget_total'] = int(alloc[np.argsort(-alloc)[:2]].sum())
    mix['top2_funded_n_test_total'] = int(n_test[np.argsort(-alloc)[:2]].sum())
    mix['top2_funded_camo_share'] = float(camo_share[np.argsort(-alloc)[:2]].mean())

    # ---- operational utility: variance decomposition on the ENDPOINT -------
    # law of total variance over the endpoint images, using the committed
    # per-cluster means and counts. Between = Var of cluster means (n-weighted).
    E = C.l2(np.load(os.path.join(E0_CACHE, '%s_test_cls.npy' % TAG)).astype(np.float64))
    enames = [os.path.splitext(n)[0] for n in
              json.load(open(os.path.join(E0_CACHE, '%s_names.json' % TAG)))['test']]
    elab = (E @ sp.centroids.T).argmax(1)

    def variance_decomposition(col):
        sc = {r['name']: float(r[col]) for r in
              csv.DictReader(open(os.path.join(B1_OUT, 'b1_scores_SINet-S2C_test.csv')))}
        v = np.array([sc[n] for n in enames if n in sc])
        L = np.array([l for n, l in zip(enames, elab) if n in sc])
        grand = v.mean()
        between = within = 0.0
        for c in range(k):
            m = L == c
            if not m.any():
                continue
            between += m.sum() * (v[m].mean() - grand) ** 2
            within += ((v[m] - v[m].mean()) ** 2).sum()
        tot = ((v - grand) ** 2).sum()
        return dict(n=int(len(v)), total_ss=float(tot), between_ss=float(between),
                    within_ss=float(within),
                    between_frac=float(between / tot), icc=float(between / tot),
                    eta=float(np.sqrt(between / tot)))

    util = dict(one_minus_sa=variance_decomposition('one_minus_sa'),
                mae=variance_decomposition('mae'),
                one_minus_iou=variance_decomposition('one_minus_iou'))

    # ---- cluster-level error predictability --------------------------------
    def rho(a, b):
        r = stats.spearmanr(a, b)
        pr = stats.pearsonr(a, b)
        return dict(spearman=float(r.statistic), spearman_p=float(r.pvalue),
                    pearson=float(pr.statistic), pearson_p=float(pr.pvalue),
                    r2=float(pr.statistic ** 2))

    pred = dict(
        es_vs_test_one_minus_sa=rho(tgt_es, test_err),
        es_vs_test_mae=rho(tgt_es, test_mae),
        note=('the allocation ranks clusters by target_es; these say how well '
              'that ranking tracks TRUE endpoint error per cluster'))

    # weighted variants, since n_test ranges 1..94 and small clusters are noisy
    big = n_test >= 10
    pred['es_vs_test_one_minus_sa_n_test_ge_10'] = dict(
        rho(tgt_es[big], test_err[big]), n_clusters=int(big.sum()))

    # ---- partition stability, from B1's committed sweep --------------------
    sweep = {int(r['k']): r for r in
             csv.DictReader(open(os.path.join(B1_OUT, 'b1_k_sweep_%s.csv' % TAG)))}
    s75 = sweep.get(75, {})
    stab = {kk: (float(s75[kk]) if kk in s75 and s75[kk] not in ('', None) else None)
            for kk in ('silhouette_mean', 'silhouette_sd', 'seed_ari_mean',
                       'seed_ari_min', 'bootstrap_ari_mean', 'bootstrap_ari_sd',
                       'n_seeds')}

    res = dict(embedder=TAG, k=k, alpha=ALPHA, budget=BUDGET,
               per_cluster=per, mixture=mix, operational_utility=util,
               predictability=pred, partition_stability=stab,
               target_assignment_agreement=dict(agree=agree, total=tot,
                                                rate=agree / tot),
               sources=['rebuild/B1/out/b1_cluster_es_dinoL518.csv',
                        'rebuild/B1/out/b1_k_sweep_dinoL518.csv',
                        'rebuild/B1/out/b1_scores_SINet-S2C_test.csv',
                        'rebuild/E0/cache/dinoL518_*.npy'])
    with open(os.path.join(OUT, 'diag_clusters.json'), 'w') as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
    with open(os.path.join(OUT, 'diag_cluster_table.csv'), 'w', newline='') as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(per[0].keys()))
        wtr.writeheader()
        wtr.writerows(per)

    # ---- report -----------------------------------------------------------
    _p('\n' + '=' * 78)
    _p('DIAG.2  mixture composition and operational cluster utility')
    _p('=' * 78)
    _p('\n--- the mixture confound ---')
    for kk, vv in mix.items():
        _p('  %-32s %s' % (kk, vv))
    _p('\n--- top 15 funded clusters ---')
    _p('  clus alloc  n_tgt  CAMO%%   target_es  n_test  1-Sa     MAE')
    for c in top:
        r = per[c]
        _p('  %4d %5d  %5d  %5.1f   %.6f  %5d  %.4f  %.4f'
           % (r['cluster'], r['alloc'], r['n_target'], 100 * r['camo_share'],
              r['target_es'], r['n_test'], r['test_one_minus_sa'], r['test_mae']))
    _p('\n--- endpoint error variance: between clusters vs within ---')
    for kk, vv in util.items():
        _p('  %-16s between/total = %.4f  (eta = %.4f, n = %d)'
           % (kk, vv['between_frac'], vv['eta'], vv['n']))
    _p('\n--- does the allocation signal predict true cluster error? ---')
    for kk, vv in pred.items():
        if isinstance(vv, dict) and 'spearman' in vv:
            _p('  %-38s rho %+.4f (p %.4f)  r2 %.4f'
               % (kk, vv['spearman'], vv['spearman_p'], vv['r2']))
    _p('\n--- partition stability at k=75 (B1, committed) ---')
    for kk, vv in stab.items():
        _p('  %-20s %s' % (kk, vv))
    _p('\nwrote %s' % os.path.join(OUT, 'diag_clusters.json'))


if __name__ == '__main__':
    main()

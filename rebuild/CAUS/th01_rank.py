#!/usr/bin/env python
"""CAUS TH-01 / AN-02 -- does concentrating a budget imply lower effective rank? Analytic + empirical.

Part A (analytic, exact): mixture covariance
    Sigma(w) = sum_j w_j Sigma_j + sum_j w_j (mu_j - mu_bar)(mu_j - mu_bar)^T,  mu_bar = sum_j w_j mu_j
evaluated in closed form for small constructions, under the ORIGINAL effective-rank definition of
rebuild/C1/c1_variance_coverage.py (participation ratio PR = (sum lam)^2 / sum lam^2) and, labelled
exploratory, the entropy effective rank exp(H(lam / sum lam)). Each construction is checked by
Monte-Carlo sampling.

Part B (empirical, the studied pool): every allocation shape run through the committed selector
(R2 grey-128 cutout ranking, desc_nc, greedy distinct), plus a perfectly FLAT quota (13-14 per
cluster) that no concentration argument can explain. For each: PR ratio and entropy-erank ratio
against 20 uniform random draws of 1000 (the C1 draws, default_rng(10000+i)), the held-out probe
d against the same draws (C1's effect_size), and the share of the selected set's total variance
that is BETWEEN serving clusters.
Writes RESULT_TABLES/TH-01_rank_constructions.csv and AN-02_shape_geometry.csv.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402
import exp01_alloc as X                                        # noqa: E402

import numpy as np                                             # noqa: E402


def pr(ev):
    ev = np.clip(ev, 0, None)
    return float(ev.sum() ** 2 / (ev ** 2).sum())


def erank(ev):
    ev = np.clip(ev, 0, None)
    p = ev / ev.sum()
    p = p[p > 0]
    return float(np.exp(-(p * np.log(p)).sum()))


def mixture_cov(w, mus, covs):
    w = np.asarray(w, float)
    mbar = sum(wi * m for wi, m in zip(w, mus))
    S = sum(wi * C for wi, C in zip(w, covs))
    S = S + sum(wi * np.outer(m - mbar, m - mbar) for wi, m in zip(w, mus))
    return S


def mc_check(w, mus, covs, n=200_000, seed=0):
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(n, w)
    Z = np.concatenate([rng.multivariate_normal(m, C, size=c) for m, C, c in zip(mus, covs, counts) if c])
    ev = np.linalg.eigvalsh(np.cov(Z.T))
    return pr(ev), erank(ev)


def part_a():
    d = 10
    e1 = np.zeros(d)
    e1[0] = 1
    rows = []
    # Construction 1: an isotropic cluster and a rank-1 cluster, same mean.
    covs = [np.eye(d), 10.0 * np.outer(e1, e1)]
    mus = [np.zeros(d), np.zeros(d)]
    for label, w in (('uniform (1/2,1/2)', (0.5, 0.5)), ('concentrated on isotropic (0.9,0.1)', (0.9, 0.1)),
                     ('concentrated on rank-1 (0.1,0.9)', (0.1, 0.9))):
        ev = np.linalg.eigvalsh(mixture_cov(w, mus, covs))
        m_pr, m_er = mc_check(w, mus, covs)
        rows.append(dict(construction='C1: isotropic + rank-1 cluster, equal means, d=10, s=10', weights=label,
                         pr_exact=round(pr(ev), 4), erank_exact=round(erank(ev), 4),
                         pr_montecarlo=round(m_pr, 4), erank_montecarlo=round(m_er, 4)))
    # Construction 2: identical isotropic clusters, means spread along one axis.
    covs = [np.eye(d)] * 3
    mus = [np.zeros(d), 4 * e1, -4 * e1]
    for label, w in (('uniform (1/3,1/3,1/3)', (1 / 3, 1 / 3, 1 / 3)), ('concentrated (0.9,0.05,0.05)', (0.9, 0.05, 0.05)),
                     ('all on one cluster (1,0,0)', (1.0, 0.0, 0.0))):
        ev = np.linalg.eigvalsh(mixture_cov(w, mus, covs))
        m_pr, m_er = mc_check([x if x > 0 else 0 for x in w], mus, covs)
        rows.append(dict(construction='C2: equal isotropic clusters, means on one axis (+-4), d=10', weights=label,
                         pr_exact=round(pr(ev), 4), erank_exact=round(erank(ev), 4),
                         pr_montecarlo=round(m_pr, 4), erank_montecarlo=round(m_er, 4)))
    return rows


def part_b():
    import c1_space
    from c1_targeted_vs_random import effect_size, largest_remainder
    sp = c1_space.load_space('dinoL518')
    arms = {}
    for a in ('C10', 'CORACLE', 'CSHUF', 'CINV'):
        arms[a] = X.reference_quota(a)[0]
    for a in X.NEW_ARMS:
        arms[a] = X.quota(a)[0]
    arms['FLAT'] = largest_remainder(np.full(sp.k, 1.0 / sp.k), X.BUDGET)
    draws = [np.random.default_rng(10_000 + i).choice(4447, X.BUDGET, replace=False) for i in range(20)]
    rows = []
    for rep, M in (('R2_cut', sp.cut), ('R3_render', sp.render)):
        def spec(Z):
            Zc = Z - Z.mean(0)
            s = np.linalg.svd(Zc, compute_uv=False)
            return s ** 2 / (len(Z) - 1)
        rnd = [spec(M[r]) for r in draws]
        pr_r, er_r = np.mean([pr(e) for e in rnd]), np.mean([erank(e) for e in rnd])
        for a, q in arms.items():
            stems, _, idx = X.select(q)
            ev = spec(M[idx])
            # between-serving-cluster share of total variance
            from exp01_tables import traced_select
            rec, _, _ = traced_select(q)
            lab = {row: c for row, c, _, _ in rec}
            Z = M[idx]
            g = np.array([lab[i] for i in idx])
            tot = ((Z - Z.mean(0)) ** 2).sum()
            btw = sum((g == c).sum() * ((Z[g == c].mean(0) - Z.mean(0)) ** 2).sum() for c in np.unique(g))
            dd = [effect_size(M[idx], M[r], i)['d_heldout'] for i, r in enumerate(draws)]
            p = q / q.sum()
            nz = p[p > 0]
            rows.append(dict(repr=rep, arm=X.DISPLAY.get(a, a), clusters_funded=int((q > 0).sum()),
                             quota_entropy_norm=round(float(-(nz * np.log(nz)).sum() / np.log(sp.k)), 4),
                             pr_ratio_vs_random=round(pr(ev) / pr_r, 4),
                             erank_ratio_vs_random_exploratory=round(erank(ev) / er_r, 4),
                             between_cluster_variance_share=round(float(btw / tot), 4),
                             probe_d_heldout_vs_random=round(float(np.mean(dd)), 4),
                             probe_d_heldout_sd=round(float(np.std(dd)), 4)))
    return rows


def main():
    a = part_a()
    K.write_csv(os.path.join(K.TABLES, 'TH-01_rank_constructions.csv'), a)
    for r in a:
        print('%-58s %-38s PR %.3f (MC %.3f)  erank %.3f (MC %.3f)' % (
            r['construction'][:58], r['weights'], r['pr_exact'], r['pr_montecarlo'], r['erank_exact'], r['erank_montecarlo']))
    b = part_b()
    K.write_csv(os.path.join(K.TABLES, 'AN-02_shape_geometry.csv'), b)
    for r in b:
        print('%-9s %-14s funded=%2d H=%.3f PRratio=%.3f eRratio=%.3f between=%.3f d=%.3f' % (
            r['repr'], r['arm'], r['clusters_funded'], r['quota_entropy_norm'], r['pr_ratio_vs_random'],
            r['erank_ratio_vs_random_exploratory'], r['between_cluster_variance_share'], r['probe_d_heldout_vs_random']))


if __name__ == '__main__':
    main()

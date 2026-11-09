"""TH-02 -- what the same-shape contrasts identify; concentration indices; tau_H for EXP-02 (CDR).

All numbers are computed here from committed artifacts and written by this script; the
write-up RESULT_TABLES/TH02_identification.md is generated from a template, so no number in it
is typed by hand.

Inputs (read-only): the committed allocation space (rebuild/C1/c1_space.load_space('dinoL518'):
target_es, centroids, cutout embeddings), the committed arm definitions (rebuild/ABC/abc_common.py),
the committed overlap counts (rebuild/ABC/out/se/abc_preflight.json).

tau_H rule (fixed here, before any CDR permutation is drawn): on the grid tau in
{0.100, 0.101, ..., 0.999}, take the tau whose REALISED integer quotas q(tau) (identity
assignment, largest remainder, B = 1000) minimise |N_eff(q(tau)) / N_eff(q(1.0)) - 1/2|, where
N_eff(q) = exp(H(q / B)) with natural log; ties go to the larger tau (the less extreme one).

Run: .venv/bin/python th02_sim.py
"""
import csv
import json
import math
import os

import numpy as np

import _repo as R
import abc_common as A
import c1_space
from c1_targeted_vs_random import softmax_alloc, largest_remainder, rank_by_centroid, serving_orders, greedy_select

SIM_SEED = 2026_11_09
B = A.BUDGET


def indices(q):
    q = np.asarray(q, dtype=float)
    p = q / q.sum()
    nz = p[p > 0]
    H = float(-(nz * np.log(nz)).sum())
    k = len(p)
    srt = np.sort(p)
    gini = float((2 * np.arange(1, k + 1) - k - 1) @ srt / (k * srt.sum()))
    return dict(n_eff=math.exp(H), n_eff_over_k=math.exp(H) / k, max_share=float(p.max()), gini=gini,
                tv_from_uniform=float(0.5 * np.abs(p - 1.0 / k).sum()), clusters_funded=int((q > 0).sum()))


def quotas(es, alpha):
    return largest_remainder(softmax_alloc(es, alpha), B)


def select(sp, alloc, es):
    _, order = rank_by_centroid(sp)
    serving = serving_orders(alloc, es)[A.SERVING]
    idx, disp = greedy_select(alloc, order, serving)
    return idx, disp


def induced_counts(sp, idx):
    """Nearest-centroid cluster of each selected cutout (cosine; same embedding as the fill rule)."""
    lab = np.argmax(sp.cut[idx] @ sp.centroids.T, axis=1)
    return np.bincount(lab, minlength=sp.k)


def fill_distance(sp, alloc, es):
    """Cosine distance (1 - cos) of each filled cutout to the centroid of the cluster that took it."""
    scores, order = rank_by_centroid(sp)
    serving = serving_orders(alloc, es)[A.SERVING]
    taken = np.zeros(order.shape[0], dtype=bool)
    d = []
    for c in serving:
        need = int(alloc[c])
        got = 0
        for row in order[:, c]:
            if got == need:
                break
            if taken[row]:
                continue
            taken[row] = True
            d.append(1.0 - scores[row, c])
            got += 1
    d = np.array(d)
    return dict(fill_dist_mean=float(d.mean()), fill_dist_p90=float(np.quantile(d, 0.9)), fill_dist_max=float(d.max()))


def toy_simulation(rng, reps=4000):
    """Known-parameter toy. 75 clusters with fixed true utilities w (direction); an allocation's outcome is
        Y = alpha * N_eff(q)/k + beta * <w, q o pi>/B + set noise + seed noise.
    Estimator: mean over K random admissible permutations at two shapes (q_H, q*), divided by the
    N_eff/k difference, minus the same at random-direction baseline -> recovers alpha; its spread
    shrinks like 1/sqrt(K). With beta = 0 the three same-shape directions are equal in expectation
    whatever alpha is: a direction null says nothing about the shape effect."""
    k = 75
    w = rng.standard_normal(k)
    qL = np.full(k, B / k)
    raw = np.exp(-np.arange(k) / 8.0)
    qH = raw / raw.sum() * B
    qM = np.sqrt(qL * qH)
    qM = qM / qM.sum() * B

    def neff(q):
        p = q / q.sum()
        return math.exp(-(p * np.log(p)).sum()) / k

    def outcome(q, perm, alpha, beta, noise):
        return alpha * neff(q) + beta * (w @ q[perm]) / B + noise

    rows = []
    for alpha, beta in ((0.05, 0.02), (0.0, 0.02), (0.05, 0.0)):
        for K in (1, 2, 5, 10):
            ests, dir_gap = [], []
            for _ in range(reps):
                yH = [outcome(qH, rng.permutation(k), alpha, beta, rng.normal(0, 0.003)) for _ in range(K)]
                yL = [outcome(qM, rng.permutation(k), alpha, beta, rng.normal(0, 0.003)) for _ in range(K)]
                ests.append((np.mean(yH) - np.mean(yL)) / (neff(qH) - neff(qM)))
                ident = np.argsort(np.argsort(-w))           # aligned direction (big quota on high w)
                order_q = np.argsort(-qH)
                pi_u = np.empty(k, dtype=int)
                pi_u[np.argsort(-w)] = order_q               # cluster with r-th largest w gets r-th largest quota
                dir_gap.append(outcome(qH, pi_u, alpha, beta, 0) - outcome(qH, rng.permutation(k), alpha, beta, 0))
            rows.append(dict(alpha_true=alpha, beta_true=beta, K=K, alpha_hat_mean=float(np.mean(ests)),
                             alpha_hat_sd=float(np.std(ests, ddof=1)), bias=float(np.mean(ests) - alpha),
                             aligned_minus_random_direction_mean=float(np.mean(dir_gap))))
    return rows


def main():
    sp = c1_space.load_space(A.EMBEDDER)
    es = sp.es
    k = sp.k
    out_rows = []
    # committed shape q* (C10 == CSHUF == CINV up to assignment) -- nominal and induced
    q_star = quotas(es, 1.0)
    ind_star = indices(q_star)
    sets = {}
    for arm in ('C10', 'CSHUF', 'CINV'):
        st, cell = A.arm_c_stems(A.ARM_ALPHA[arm], A.ARM_ES_PERM[arm])
        sets[arm] = st
        idx = np.array([sp.names.index(s) for s in st])
        out_rows.append(dict(allocation=arm, basis='nominal quota', **indices(q_star)))
        out_rows.append(dict(allocation=arm, basis='induced nearest-centroid', **indices(induced_counts(sp, idx))))
    # B: per seed, induced only (B has no quota)
    b_ind = []
    for s in (42, 43, 45, 46, 47, 48, 49, 50):
        st = A.arm_b_stems(s)
        idx = np.array([sp.names.index(x) for x in st])
        cnt = induced_counts(sp, idx)
        b_ind.append(cnt)
        out_rows.append(dict(allocation='B_s%d' % s, basis='induced nearest-centroid', **indices(cnt)))
    b_mean = {key: float(np.mean([indices(c)[key] for c in b_ind])) for key in indices(b_ind[0])}
    out_rows.append(dict(allocation='B (mean over 8 seeds)', basis='induced nearest-centroid', **b_mean))
    # LU
    q_u = largest_remainder(np.full(k, 1.0 / k), B)
    out_rows.append(dict(allocation='LU', basis='nominal quota', **indices(q_u)))
    st_u, _ = A.arm_c_stems(1.0, 'uniform')
    out_rows.append(dict(allocation='LU', basis='induced nearest-centroid',
                         **indices(induced_counts(sp, np.array([sp.names.index(x) for x in st_u])))))
    # tau grid and tau_H
    grid = [round(0.100 + 0.001 * i, 3) for i in range(900)]
    target = 0.5 * ind_star['n_eff']
    best = None
    tau_rows = []
    for t in grid:
        q = quotas(es, t)
        ne = indices(q)['n_eff']
        gap = abs(ne / ind_star['n_eff'] - 0.5)
        if best is None or gap < best[1] - 1e-15 or (abs(gap - best[1]) <= 1e-15 and t > best[0]):
            best = (t, gap)
    tau_H = best[0]
    for t in sorted(set([0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0, tau_H])):
        q = quotas(es, t)
        st_idx, disp = select(sp, q, es)
        fd = fill_distance(sp, q, es)
        tau_rows.append(dict(tau=t, n_displaced=disp, **indices(q), **fd,
                             top1_quota=int(q.max()), top2_share=float(np.sort(q)[-2:].sum() / B)))
    q_H = quotas(es, tau_H)
    ind_H = indices(q_H)
    fd_star, fd_H = fill_distance(sp, q_star, es), fill_distance(sp, q_H, es)
    fd_u = fill_distance(sp, q_u, es)
    for name, q, fd in (('C10 (tau=1)', q_star, fd_star), ('LH shape (tau_H, identity)', q_H, fd_H), ('LU', q_u, fd_u)):
        out_rows.append(dict(allocation=name, basis='nominal quota + fill distance', **indices(q), **fd))
    # overlap covariance (committed shared counts)
    pf = json.load(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_preflight.json')))
    ov = [g for g in pf['gates'] if g.get('gate') == 'pools'][0]['overlap_B_vs_C']
    pool_n = 4447
    f0 = B / pool_n
    cov_rows = []
    for key, v in sorted(ov.items()):
        f = v['overlap'] / B
        cov_rows.append(dict(pair=key, kind=v['kind'], shared=v['overlap'], shared_fraction=f, jaccard=v['jaccard'],
                             set_var_ratio_vs_independent_random=(1 - f) / (1 - f0)))
    # toy
    rng = np.random.default_rng(SIM_SEED)
    toy = toy_simulation(rng)
    # ---- write
    os.makedirs(R.TABLES, exist_ok=True)

    def wcsv(name, rows):
        keys = []
        for r in rows:
            for kk in r:
                if kk not in keys:
                    keys.append(kk)
        with open(os.path.join(R.TABLES, name), 'w', newline='') as fh:
            wr = csv.DictWriter(fh, fieldnames=keys)
            wr.writeheader()
            for r in rows:
                wr.writerow({kk: ('%.6g' % vv if isinstance(vv, float) else vv) for kk, vv in r.items()})
    wcsv('TH02_concentration_indices.csv', out_rows)
    wcsv('TH02_tau_grid.csv', tau_rows)
    wcsv('TH02_overlap_covariance.csv', cov_rows)
    wcsv('TH02_toy_sim.csv', toy)
    summ = dict(tau_H=tau_H, tau_H_rule='argmin over tau in {0.100..0.999 step 0.001} of |N_eff(q(tau))/N_eff(q(1.0)) - 0.5|, ties -> larger tau',
                n_eff_tau1=ind_star['n_eff'], n_eff_tauH=ind_H['n_eff'], ratio=ind_H['n_eff'] / ind_star['n_eff'],
                n_eff_uniform=indices(q_u)['n_eff'], n_eff_B_induced_mean=b_mean['n_eff'],
                quotas_tauH=[int(x) for x in q_H], max_quota_tauH=int(q_H.max()), clusters_funded_tauH=int((q_H > 0).sum()),
                fill_dist_mean_tau1=fd_star['fill_dist_mean'], fill_dist_mean_tauH=fd_H['fill_dist_mean'],
                fill_dist_mean_uniform=fd_u['fill_dist_mean'], shared_fraction_chance=f0)
    json.dump(summ, open(os.path.join(R.TABLES, 'TH02_summary.json'), 'w'), indent=2)
    write_md(summ, out_rows, tau_rows, cov_rows, toy, ind_star, ind_H, b_mean)
    print(json.dumps({k_: v for k_, v in summ.items() if k_ != 'quotas_tauH'}, indent=1))


def write_md(s, rows, tau_rows, cov_rows, toy, ind_star, ind_H, b_mean):
    def g(name, basis):
        return [r for r in rows if r['allocation'] == name and r['basis'] == basis][0]
    c_ind = g('C10', 'induced nearest-centroid')
    cs_ind = g('CSHUF', 'induced nearest-centroid')
    lu = g('LU', 'nominal quota')
    toy_t = '\n'.join('| %.2f | %.2f | %d | %.4f | %.4f | %+.4f | %+.5f |' % (
        t['alpha_true'], t['beta_true'], t['K'], t['alpha_hat_mean'], t['alpha_hat_sd'], t['bias'],
        t['aligned_minus_random_direction_mean']) for t in toy)
    cov_t = '\n'.join('| %s | %s | %d | %.3f | %.3f |' % (c['pair'], c['kind'], c['shared'], c['shared_fraction'],
                                                         c['set_var_ratio_vs_independent_random']) for c in cov_rows
                      if c['kind'] in ('CxC', 'BxC') and 'B_s' not in c['pair'].split('|')[0] or c['kind'] == 'CxC')
    tau_t = '\n'.join('| %.3f | %.2f | %.3f | %.3f | %d | %d | %.4f | %.4f |' % (
        t['tau'], t['n_eff'], t['max_share'], t['gini'], t['clusters_funded'], t['n_displaced'],
        t['fill_dist_mean'], t['fill_dist_max']) for t in tau_rows)
    reviewer = ("The three same-shape arms answer one question: does it matter which clusters receive the "
                "budget, given how unevenly it is spread? They cannot answer the other: does uneven spreading "
                "itself change accuracy? Comparing the shuffled arm with random selection mixes the spreading "
                "effect with the effect of one particular random assignment, and a single draw cannot tell the "
                "two apart. A null on direction (targeted, shuffled and reversed arms indistinguishable) is "
                "compatible with any spreading effect, including none. The concentrated arms also share about "
                "half of their images, which makes their mutual contrasts more precise than contrasts against "
                "random selection. Identifying a downstream concentration effect therefore needs several "
                "independent permutations at more than one concentration level, which is the design of our "
                "dose-response experiment.")
    md = f"""# TH-02 -- What the same-shape contrasts identify

*Generated by `analysis/th02_sim.py`; every number below is computed by that script from committed
artifacts. Formal content: definitions, assumptions, derivation, numerical checks.*

## 1. Definitions

- $k = 75$ target clusters (k-means on L2-normalised DINOv2 ViT-L/14 CLS features, fitted once).
- An allocation is a pair $(q, \\pi)$: $q$ is the sorted quota vector (the **shape**), $\\pi$ assigns the
  $j$-th largest quota to a cluster (the **direction**). The injected set is $S(q,\\pi)$ = the committed fill
  rule (nearest unclaimed cutouts to each centroid, clusters served in descending quota) applied to $q\\circ\\pi$.
- Outcome: $Y = f(S) + g(S, \\text{{seed}}) + \\eta$, where $g$ is the arm's own pseudo-label path and $\\eta$ seed noise.
- Arms: C10 $=(q^*, \\pi_u)$ (aligned with the scores), CSHUF $=(q^*, \\pi_s)$ (one admissible random
  permutation), CINV $=(q^*, \\pi_r)$ (rank reversal), B = a uniformly random set, redrawn per seed.

## 2. Assumptions

- **A1** $Y$ depends on the allocation only through $S$ (and the pseudo-labels the arm itself produces from $S$).
- **A2** No interference between runs.
- **A3** The shape effect is defined over permutations: $\\theta(q) = \\mathbb{{E}}_{{\\pi}}[Y(q,\\pi)] - \\mathbb{{E}}[Y(B)]$, with $\\pi$
  uniform over the admissible permutations $\\Pi$ (no fixed point, $|\\rho| \\le 0.10$).

## 3. One permutation does not identify the shape effect

Write $Y(q^*,\\pi_s) = \\mathbb{{E}}_\\pi Y(q^*,\\pi) + \\varepsilon(\\pi_s)$ with $\\varepsilon(\\pi_s) = Y(q^*,\\pi_s) - \\mathbb{{E}}_\\pi Y(q^*,\\pi)$. Then

$$\\mathbb{{E}}_{{\\text{{seed}}}}[\\text{{CSHUF}} - \\text{{B}}] = \\theta(q^*) + \\varepsilon(\\pi_s) + (\\text{{set-identity term}}).$$

$\\varepsilon(\\pi_s)$ has mean zero over $\\Pi$ and variance $V_\\pi(q^*) = \\operatorname{{Var}}_\\pi(\\mathbb{{E}}[Y(q^*,\\pi)\\mid\\pi])$. One draw gives
no estimate of $V_\\pi$, so $\\theta(q^*)$ and $\\varepsilon(\\pi_s)$ cannot be separated. Averaging over $K$ independent
admissible permutations reduces the nuisance variance to $V_\\pi/K$ and makes $V_\\pi$ estimable from the
between-permutation spread. C10 and CINV do not help: $\\pi_u$ and $\\pi_r$ are chosen, not drawn, so they are
not samples from $\\Pi$.

## 4. A null on direction is compatible with any shape effect

$\\text{{C10}} - \\text{{CSHUF}} = \\varepsilon(\\pi_u) - \\varepsilon(\\pi_s)$ and $\\text{{CINV}} - \\text{{CSHUF}} = \\varepsilon(\\pi_r) - \\varepsilon(\\pi_s)$: the shape effect
$\\theta(q^*)$ cancels from every same-shape contrast. C10 $\\approx$ CSHUF $\\approx$ CINV therefore says only that the
direction terms are small, and is equally consistent with $\\theta(q^*) = 0$ and with $\\theta(q^*)$ large. The
existing trained data identify a direction null, not a downstream concentration effect. The toy simulation
(Section 7) shows this with $\\beta = 0$: aligned and random directions agree exactly whatever $\\alpha$ is.

## 5. Shared images correlate the concentrated arms

Model the set-identity part of $Y$ as additive over images, $\\frac{{1}}{{N}}\\sum_{{i \\in S}} w_i$ with $w_i$ i.i.d. of
variance $\\sigma_w^2$. For two sets sharing $m = fN$ images, $\\operatorname{{Cov}} = f\\sigma_w^2/N$, so the set-identity variance of their
difference is $2(1-f)\\sigma_w^2/N$, against $2(1-f_0)\\sigma_w^2/N$ for two independent random sets, where $f_0 = N/P =
{s['shared_fraction_chance']:.3f}$ (N = 1000 of P = 4447). Ratio $(1-f)/(1-f_0)$ from the committed shared counts:

| Pair | Kind | Shared | f | variance ratio vs independent random |
|---|---|---|---|---|
{cov_t}

Contrasts among C-family arms therefore carry roughly half to two-thirds of the set-identity variance of a
contrast against B. B's own seed-to-seed spread additionally contains set-sampling variance, because B
redraws its images at every seed. A pooled $\\hat\\sigma$ mixes the two.

## 6. Concentration indices and the choice of $\\tau_H$

$N_\\text{{eff}} = \\exp(H(q/N))$ (natural log). Committed shape $q^*$ ($\\tau = 1.0$): $N_\\text{{eff}} = {ind_star['n_eff']:.2f}$ of 75,
max share {ind_star['max_share']:.3f}, Gini {ind_star['gini']:.3f}. Cluster-uniform (LU): $N_\\text{{eff}} = {lu['n_eff']:.2f}$.
Random selection lands on the clusters (nearest centroid) with mean $N_\\text{{eff}} = {b_mean['n_eff']:.2f}$ over 8 seeds;
by the same induced measure C10 gives {c_ind['n_eff']:.2f} and CSHUF {cs_ind['n_eff']:.2f}, and the cluster-uniform
allocation {g('LU', 'induced nearest-centroid')['n_eff']:.2f}.

**The quotas overstate how concentrated the selected images are.** Because cluster structure is weak, many
cutouts that fill one cluster's quota lie nearer another cluster's centroid. By the nominal quotas, C10 is
{ind_star['n_eff']:.1f} effective clusters against 75 for uniform; by where its images actually fall it is
{c_ind['n_eff']:.1f} against {g('LU', 'induced nearest-centroid')['n_eff']:.1f}, and random selection ({b_mean['n_eff']:.1f}) sits between the
concentrated and the uniform sets. The dose-response experiment therefore reports both measures per allocation;
the nominal one is the manipulated variable.

**$\\tau_H$ = {s['tau_H']:.3f}**, by the rule fixed in the script before any draw: $N_\\text{{eff}}(q(\\tau_H)) = {s['n_eff_tauH']:.2f}$,
ratio {s['ratio']:.4f} to the committed shape. At $\\tau_H$ the largest quota is {s['max_quota_tauH']} and {s['clusters_funded_tauH']} clusters are
funded. Full grid (identity assignment):

| $\\tau$ | $N_\\text{{eff}}$ | max share | Gini | funded | displaced | mean fill dist | max fill dist |
|---|---|---|---|---|---|---|---|
{tau_t}

## 7. Numerical check (toy with known parameters)

$Y = \\alpha\\, N_\\text{{eff}}(q)/k + \\beta \\langle w, q\\circ\\pi\\rangle/N + $ noise, 75 clusters, {4000} replications per row. The
estimator averages $K$ random permutations at two shapes and divides by the $N_\\text{{eff}}/k$ difference.

| $\\alpha$ | $\\beta$ | K | mean $\\hat\\alpha$ | sd $\\hat\\alpha$ | bias | aligned − random direction |
|---|---|---|---|---|---|---|
{toy_t}

The estimator is unbiased; its spread falls roughly as $1/\\sqrt{{K}}$ when direction matters ($\\beta \\ne 0$). With $\\beta = 0$
the aligned-minus-random direction gap is exactly zero for any $\\alpha$ (Section 4).

## 8. Boundary cases

- **Concentration is confounded with fill quality.** A larger quota reaches further down a cluster's ranking: mean
  cutout-to-centroid distance is {s['fill_dist_mean_tau1']:.4f} at $\\tau = 1$ and {s['fill_dist_mean_tauH']:.4f} at $\\tau_H$ (uniform:
  {s['fill_dist_mean_uniform']:.4f}). EXP-02 records fill distance per allocation as a covariate.
- **The cluster-uniform allocation has no direction**: every permutation of uniform quotas gives the same allocation.
- **At odd $k$, CINV has a fixed point**: rank reversal maps the median cluster to itself.
- **Pseudo-labelling** makes arms differ downstream of $S$ (assumption A1). This cannot be eliminated, only measured
  (pseudo-label counts are recorded per run).

## 9. Corrected statement for the manuscript

The same-shape controls establish that *which* clusters receive the budget has no detectable effect on
accuracy. They do not identify whether the *concentration* of the budget affects accuracy: the shape effect
cancels from every same-shape contrast, and its only available estimate (shuffled versus random) rests on a
single permutation whose own direction effect cannot be separated from it. Concentration is established as an
explanation of *training-set distinguishability*; as an explanation of downstream accuracy it is a hypothesis,
tested separately with several permutations per concentration level.

## 10. Reviewer-facing explanation ({len(reviewer)} characters)

{reviewer}
"""
    open(os.path.join(R.TABLES, 'TH02_identification.md'), 'w').write(md)


if __name__ == '__main__':
    main()

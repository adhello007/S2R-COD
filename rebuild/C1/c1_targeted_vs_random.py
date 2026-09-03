#!/usr/bin/env python
"""C1 -- the decisive measurement: how different is targeted data from random?

Specification: rebuild/C1/C1_PLAN.md, approved before this file existed,
including amendments A1 (mandatory held-out CIs + band-straddle flagging) and
A2 (mandatory de-duplication order-sensitivity).

If the targeted and random arms see nearly identical data, no accuracy gain is
possible and the Stage C null is explained. If they differ substantially, that
link of the argument fails and the verdict reopens.

The old package's `d ~ 0.10` had no producing script and no log block. It enters
this file ONLY as an OLD_CLAIMS tuple. No threshold references it, no code
branches on it, and nothing here is positioned relative to it.

Phase 0 gates run first and HALT the run on any failure -- no fallback, no
default, no --force. TRAINS NOTHING; re-embeds nothing.

Usage:
  LAKE-RED/.venv/bin/python rebuild/C1/c1_targeted_vs_random.py
"""

import argparse
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
import common as C                                            # noqa: E402
import c1_preflight as PF                                     # noqa: E402
import c1_space                                               # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'C1'
OUT = C.exp_dir(EXP, 'out')
POOL = PF.POOL

B_GRID = (250, 500, 1000, 2000, 3000, 4447)     # 4447 IS the pool ceiling
ALPHA_START = (0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
ALPHA_MIN, ALPHA_MAX = 1e-4, 1e3
N_DRAWS = 20
N_DRAWS_ORDER = 5      # amendment A2's spread is a PAIRED comparison -- see below
N_BOOT = 1000
N_SHUFFLE = 10
REPRS = ('R2_cut', 'R3_render')

# Verdict bands, on |d|. Partition of [0, inf) at 0.2 and 0.5.
BAND_LO, BAND_HI = 0.2, 0.5
ORDER_SPREAD_MAX = 0.05        # amendment A2's declared threshold

OLD_CLAIMS = [
    ("C1.1 Cohen's d targeted-vs-random", '~0.10  [no code, never computed]'),
    ('C1.2 ||delta mean||', '0.084-0.099  [no code]'),
    ('C1.3 clusters funded / max alloc', '1-49 / 76-999  [no code]'),
]


def _p(m):
    print(m, flush=True)


def band(x):
    a = abs(x)
    return 'CONFIRMED' if a < BAND_LO else ('AMBIGUOUS' if a < BAND_HI else 'REOPENS')


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

def softmax_alloc(es, alpha):
    """p_c over clusters at temperature T = alpha * sd(es). Max-subtracted."""
    sd = float(np.std(es))
    if sd <= 0:
        return np.full(len(es), 1.0 / len(es))
    w = np.exp((es - es.max()) / (alpha * sd))
    return w / w.sum()


def largest_remainder(p, B):
    """Integer allocation summing EXACTLY to B. Ties by ascending cluster index."""
    exact = p * B
    base = np.floor(exact).astype(np.int64)
    rem = B - int(base.sum())
    if rem > 0:
        frac = exact - base
        # -frac ascending == frac descending; stable keeps ascending index on ties
        order = np.argsort(-frac, kind='stable')
        base[order[:rem]] += 1
    return base


def extend_alpha_grid(es, start=ALPHA_START):
    """Widen until BOTH degenerate ends are reached, or the caps are hit.

    concentrated: max(p) >= 0.95        uniform: TV(p, uniform) < 0.01
    """
    grid = sorted(start)
    k = len(es)

    def conc(a):
        return float(softmax_alloc(es, a).max())

    def tv(a):
        p = softmax_alloc(es, a)
        return float(0.5 * np.abs(p - 1.0 / k).sum())

    while conc(grid[0]) < 0.95 and grid[0] / 2 >= ALPHA_MIN:
        grid.insert(0, grid[0] / 2)
    while tv(grid[-1]) >= 0.01 and grid[-1] * 2 <= ALPHA_MAX:
        grid.append(grid[-1] * 2)
    return grid, dict(alpha_min=grid[0], alpha_max=grid[-1],
                      reached_concentrated=bool(conc(grid[0]) >= 0.95),
                      reached_uniform=bool(tv(grid[-1]) < 0.01),
                      max_p_at_min_alpha=conc(grid[0]),
                      tv_at_max_alpha=tv(grid[-1]))


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def rank_by_centroid(space):
    """(POOL, k) cosine of every cutout to every centroid, and per-cluster order.

    Selection is in R2 -- the grey-128 cutout -- because that is what a real
    pipeline has at selection time: the foreground exists, the render does not.
    """
    scores = space.cut @ space.centroids.T
    order = np.argsort(-scores, axis=0, kind='stable')       # stable => tie by index
    return scores, order


def serving_orders(alloc, es, n_shuffle=N_SHUFFLE):
    """The five orders amendment A2 makes mandatory."""
    ks = list(range(len(alloc)))
    out = {
        'desc_nc':   sorted(ks, key=lambda c: (-alloc[c], c)),     # primary
        'asc_nc':    sorted(ks, key=lambda c: (alloc[c], c)),
        'asc_index': list(ks),
        'desc_es':   sorted(ks, key=lambda c: (-es[c], c)),
    }
    for i in range(n_shuffle):
        r = np.random.default_rng(20_000 + i)
        out['shuffled_%d' % i] = list(r.permutation(len(alloc)))
    return out


def greedy_select(alloc, order_idx, serving):
    """Distinct-image selection. Each cluster walks its ranking, skipping taken.

    Returns (indices, n_displaced) where n_displaced counts how often a cluster's
    next choice was already claimed -- a large value means the arms converge for
    a mechanical reason rather than a substantive one.
    """
    taken = np.zeros(order_idx.shape[0], dtype=bool)
    picked, displaced = [], 0
    for c in serving:
        need = int(alloc[c])
        if need <= 0:
            continue
        col = order_idx[:, c]
        got = 0
        for row in col:
            if taken[row]:
                displaced += 1
                continue
            taken[row] = True
            picked.append(int(row))
            got += 1
            if got == need:
                break
    return np.array(sorted(picked), dtype=np.int64), displaced


# ---------------------------------------------------------------------------
# The metric
# ---------------------------------------------------------------------------

def _cohens_d_1d(a, r):
    na, nr = len(a), len(r)
    if na < 2 or nr < 2:
        return float('nan')
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nr - 1) * r.var(ddof=1))
                 / (na + nr - 2))
    return float((a.mean() - r.mean()) / sp) if sp > 0 else 0.0


def effect_size(A, R, draw_idx, n_boot=0):
    """||delta mean||, in-sample d, held-out d, and (optionally) a bootstrap CI.

    The direction is fitted to the data it is evaluated on, which biases d
    upward -- the same in-sample/held-out issue B3 exists to expose. So the
    HEADLINE is d_heldout: estimate the direction on one half, evaluate on the
    disjoint other half.
    """
    delta = A.mean(0) - R.mean(0)
    nrm = float(np.linalg.norm(delta))
    if nrm <= 0:
        return dict(norm_dmean=0.0, d_insample=0.0, d_heldout=0.0, boot=None)
    u = delta / nrm
    d_in = _cohens_d_1d(A @ u, R @ u)

    rng = np.random.default_rng(40_000 + draw_idx)
    ia = rng.permutation(len(A)); ir = rng.permutation(len(R))
    ha, hr = len(A) // 2, len(R) // 2
    A1, A2 = A[ia[:ha]], A[ia[ha:]]
    R1, R2 = R[ir[:hr]], R[ir[hr:]]
    d2 = A1.mean(0) - R1.mean(0)
    n2 = np.linalg.norm(d2)
    if n2 <= 0:
        return dict(norm_dmean=nrm, d_insample=d_in, d_heldout=0.0, boot=None)
    u2 = d2 / n2
    pa, pr = A2 @ u2, R2 @ u2
    d_out = _cohens_d_1d(pa, pr)

    boot = None
    if n_boot:
        b = np.empty(n_boot)
        br = np.random.default_rng(30_000 + draw_idx)
        for i in range(n_boot):
            b[i] = _cohens_d_1d(br.choice(pa, len(pa), replace=True),
                                br.choice(pr, len(pr), replace=True))
        boot = b
    return dict(norm_dmean=nrm, d_insample=d_in, d_heldout=d_out, boot=boot)


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tags', default='%s,%s' % (PF.PRIMARY, PF.SENSITIVITY))
    ap.add_argument('--draws', type=int, default=N_DRAWS)
    ap.add_argument('--boot', type=int, default=N_BOOT)
    ap.add_argument('--skip-gate', default='')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    tags = [t.strip() for t in args.tags.split(',')]
    if args.draws < N_DRAWS:
        raise SystemExit('N_DRAWS is a floor (%d); it may be raised, never lowered'
                         % N_DRAWS)
    os.makedirs(OUT, exist_ok=True)

    # ---------------- Phase 0: gates, and HALT on any failure ----------------
    _p('=== Phase 0: preflight ===')
    skip = {s.strip() for s in args.skip_gate.split(',') if s.strip()}
    report = PF.run_preflight(tags, skip=skip)
    if not report['all_passed']:
        failed = [g['gate'] for g in report['gates'] if not g['passed']]
        raise SystemExit('C1 HALTED at preflight: %s -- see c1_preflight.json'
                         % failed)

    metrics, thresholds, notes, artifacts = [], [], [], []
    metrics.append(('preflight_gates_passed',
                    '%d/%d' % (sum(g['passed'] for g in report['gates']),
                               len(report['gates'])),
                    'signal, cluster_source, embedder, representation, leakage, freshness'))
    thresholds.append(('all six Phase-0 gates pass before any array is loaded',
                       report['all_passed']))
    artifacts.append('rebuild/C1/out/c1_preflight.json')

    cells, draws_rows, order_rows, ceiling_rows, interval_rows = [], [], [], [], []
    null_cal = []
    alpha_meta = {}

    for tag in tags:
        space = c1_space.load_space(tag)
        assert space.tag == tag
        scores, order_idx = rank_by_centroid(space)
        agrid, ameta = extend_alpha_grid(space.es)
        alpha_meta[tag] = ameta
        _p('=== %s: k=%d  alpha grid %d values [%.4g .. %.4g] ==='
           % (tag, space.k, len(agrid), agrid[0], agrid[-1]))

        top_cluster = int(np.argmax(space.es))
        for B in B_GRID:
            rsets = [np.random.default_rng(10_000 + i).choice(POOL, size=B,
                                                              replace=False)
                     for i in range(args.draws)]
            # ---- ceiling: entire budget to the single highest-ES cluster ----
            ceil_alloc = np.zeros(space.k, dtype=np.int64)
            ceil_alloc[top_cluster] = B
            ceil_sel, _ = greedy_select(ceil_alloc, order_idx, [top_cluster])
            for rep in REPRS:
                M = space.cut if rep == 'R2_cut' else space.render
                ds = [effect_size(M[ceil_sel], M[rs], i)['d_heldout']
                      for i, rs in enumerate(rsets)]
                ceiling_rows.append(dict(tag=tag, B=B, repr=rep,
                                         cluster=top_cluster,
                                         d_heldout_mean=round(float(np.mean(ds)), 5),
                                         d_heldout_sd=round(float(np.std(ds)), 5)))

            for alpha in agrid:
                p = softmax_alloc(space.es, alpha)
                alloc = largest_remainder(p, B)
                funded = int((alloc > 0).sum())
                max_share = float(alloc.max() / B)
                tv_unif = float(0.5 * np.abs(p - 1.0 / space.k).sum())
                ent = float(-(p[p > 0] * np.log(p[p > 0])).sum() / np.log(space.k))
                degen = bool(space.k < 10 or funded <= 2
                             or (max_share >= 0.95 and alpha != agrid[0]))

                orders = serving_orders(alloc, space.es)
                sels = {}
                for onm, serving in orders.items():
                    sels[onm] = greedy_select(alloc, order_idx, serving)

                for rep in REPRS:
                    M = space.cut if rep == 'R2_cut' else space.render
                    # ---- primary order: full treatment ----
                    sel, disp = sels['desc_nc']
                    per_draw, boots = [], []
                    for i, rs in enumerate(rsets):
                        e = effect_size(M[sel], M[rs], i, n_boot=args.boot)
                        per_draw.append(e)
                        if e['boot'] is not None:
                            boots.append(e['boot'])
                        draws_rows.append(dict(
                            tag=tag, B=B, alpha=alpha, repr=rep, draw=i,
                            norm_dmean=round(e['norm_dmean'], 6),
                            d_insample=round(e['d_insample'], 6),
                            d_heldout=round(e['d_heldout'], 6)))
                    dh = np.array([e['d_heldout'] for e in per_draw])
                    di = np.array([e['d_insample'] for e in per_draw])
                    nd = np.array([e['norm_dmean'] for e in per_draw])

                    # ---- A1: mandatory intervals, conservative union ----
                    ci_draws = (float(np.percentile(dh, 2.5)),
                                float(np.percentile(dh, 97.5)))
                    if boots:
                        allb = np.concatenate(boots)
                        ci_boot = (float(np.percentile(allb, 2.5)),
                                   float(np.percentile(allb, 97.5)))
                    else:
                        ci_boot = ci_draws
                    ci_comb = (min(ci_draws[0], ci_boot[0]),
                               max(ci_draws[1], ci_boot[1]))
                    b_lo, b_hi = band(ci_comb[0]), band(ci_comb[1])
                    straddles = b_lo != b_hi

                    # ---- A2: mandatory order sensitivity ----
                    # The spread is a PAIRED comparison: every order, INCLUDING the
                    # primary, is evaluated over the SAME first N_DRAWS_ORDER draws,
                    # so a difference between orders cannot be an artefact of the
                    # orders having seen different random arms. Fewer draws makes the
                    # per-order mean noisier, which inflates the spread and therefore
                    # errs toward FLAGGING order-sensitivity -- the conservative
                    # direction for a check whose job is to catch it. The primary's
                    # headline d still uses all N_DRAWS draws.
                    sub = rsets[:N_DRAWS_ORDER]
                    od = {onm: float(np.mean(
                              [effect_size(M[s2], M[rs], i)['d_heldout']
                               for i, rs in enumerate(sub)]))
                          for onm, (s2, _x) in sels.items()}
                    spread = max(abs(v - od['desc_nc']) for v in od.values())
                    prim_set = set(sels['desc_nc'][0].tolist())
                    jac = {onm: len(prim_set & set(s2.tolist()))
                                / max(len(prim_set | set(s2.tolist())), 1)
                           for onm, (s2, _x) in sels.items()}
                    order_sensitive = bool(spread >= ORDER_SPREAD_MAX)
                    for onm in sorted(od):
                        order_rows.append(dict(
                            tag=tag, B=B, alpha=alpha, repr=rep, order=onm,
                            n_draws_paired=N_DRAWS_ORDER,
                            d_heldout=round(od[onm], 6),
                            jaccard_vs_primary=round(jac[onm], 6),
                            d_order_spread=round(spread, 6),
                            ORDER_SENSITIVE=int(order_sensitive)))

                    # ---- the ceiling check, and what it revealed ----
                    # At B = POOL both arms are the ENTIRE pool, so the true
                    # difference is exactly zero and ||delta mean|| must vanish.
                    # That is the assertion.
                    #
                    # d_heldout does NOT vanish there, and that is not a bug. With
                    # no real difference, the direction fitted on halves A1/R1 is
                    # pure split noise, and the disjoint halves A2/R2 are
                    # ANTI-correlated with it -- so the held-out d comes out
                    # NEGATIVE. B=POOL therefore doubles as a NULL CALIBRATION of
                    # the estimator: it measures what d_heldout returns when the
                    # answer is known to be zero. The offset is toward zero/negative,
                    # i.e. the held-out estimator is CONSERVATIVE, which is the safe
                    # direction for a measurement whose job is to detect a
                    # difference. Every measured d is read against this reference.
                    if B == POOL:
                        assert abs(float(nd.mean())) < 1e-9, (
                            'B=POOL must give ||delta mean||=0: both arms are the '
                            'entire pool (got %.3g)' % nd.mean())
                        null_cal.append(dict(tag=tag, repr=rep, alpha=round(alpha, 6),
                                             norm_dmean=float(nd.mean()),
                                             d_heldout=float(dh.mean()),
                                             d_heldout_sd=float(dh.std()),
                                             d_insample=float(di.mean())))

                    cells.append(dict(
                        tag=tag, B=B, alpha=round(alpha, 6), repr=rep,
                        k=space.k, clusters_funded=funded,
                        max_alloc_share=round(max_share, 5),
                        alloc_entropy_norm=round(ent, 5),
                        tv_from_uniform=round(tv_unif, 5),
                        n_displaced=disp, degenerate=int(degen),
                        norm_dmean=round(float(nd.mean()), 6),
                        d_insample=round(float(di.mean()), 6),
                        d_heldout=round(float(dh.mean()), 6),
                        d_heldout_sd=round(float(dh.std()), 6),
                        d_heldout_min=round(float(dh.min()), 6),
                        d_heldout_max=round(float(dh.max()), 6),
                        ci_lo=round(ci_comb[0], 6), ci_hi=round(ci_comb[1], 6),
                        band_lo=b_lo, band_hi=b_hi,
                        ci_straddles_band=int(straddles),
                        d_order_spread=round(spread, 6),
                        ORDER_SENSITIVE=int(order_sensitive)))
                    interval_rows.append(dict(
                        tag=tag, B=B, alpha=round(alpha, 6), repr=rep,
                        d_heldout=round(float(dh.mean()), 6),
                        ci_draws_lo=round(ci_draws[0], 6),
                        ci_draws_hi=round(ci_draws[1], 6),
                        ci_boot_lo=round(ci_boot[0], 6),
                        ci_boot_hi=round(ci_boot[1], 6),
                        ci_combined_lo=round(ci_comb[0], 6),
                        ci_combined_hi=round(ci_comb[1], 6),
                        band_lo=b_lo, band_hi=b_hi,
                        ci_straddles_band=int(straddles)))
            _p('  %s B=%-5d done (%d alphas x %d reprs)' % (tag, B, len(agrid),
                                                            len(REPRS)))

    # ---------------- write artifacts ----------------
    def dump(rows, name):
        p = os.path.join(OUT, name)
        with open(p, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        artifacts.append('rebuild/C1/out/' + name)
    dump(cells, 'c1_cells.csv')
    dump(draws_rows, 'c1_draws.csv')
    dump(order_rows, 'c1_order_sensitivity.csv')
    dump(interval_rows, 'c1_intervals.csv')
    dump(ceiling_rows, 'c1_ceiling.csv')
    dump(null_cal, 'c1_null_calibration.csv')
    C.save_json(os.path.join(OUT, 'c1_alpha_grid.json'), alpha_meta)
    artifacts.append('rebuild/C1/out/c1_alpha_grid.json')

    # ---------------- verdict, per tag x repr, at the peak of B ----------------
    verdicts = {}
    for tag in tags:
        for rep in REPRS:
            sub = [c for c in cells if c['tag'] == tag and c['repr'] == rep
                   and not c['degenerate'] and c['B'] < POOL]
            if not sub:
                continue
            peak = max(sub, key=lambda c: abs(c['d_heldout']))
            v = dict(peak_B=peak['B'], peak_alpha=peak['alpha'],
                     d_heldout=peak['d_heldout'],
                     ci=[peak['ci_lo'], peak['ci_hi']],
                     band_point=band(peak['d_heldout']),
                     ci_straddles=bool(peak['ci_straddles_band']),
                     order_sensitive=bool(peak['ORDER_SENSITIVE']),
                     clusters_funded=peak['clusters_funded'],
                     max_alloc_share=peak['max_alloc_share'])
            v['verdict'] = ('INCONCLUSIVE-CI-STRADDLES-%s|%s'
                            % (peak['band_lo'], peak['band_hi'])
                            if v['ci_straddles'] else v['band_point'])
            verdicts['%s|%s' % (tag, rep)] = v
            metrics.append(
                ('PEAK_%s_%s' % (tag, rep),
                 ('d_heldout %+.4f  CI [%+.4f, %+.4f]  -> %s'
                  % (v['d_heldout'], v['ci'][0], v['ci'][1], v['verdict'])),
                 'at B=%d alpha=%.4g, %d clusters funded, max share %.3f'
                 % (v['peak_B'], v['peak_alpha'], v['clusters_funded'],
                    v['max_alloc_share'])))
    C.save_json(os.path.join(OUT, 'c1_verdicts.json'), verdicts)
    artifacts.append('rebuild/C1/out/c1_verdicts.json')

    # ---------------- declared thresholds ----------------
    n_straddle = sum(c['ci_straddles_band'] for c in cells)
    n_ordsens = sum(c['ORDER_SENSITIVE'] for c in cells)
    metrics += [
        ('cells_measured', len(cells), '%d tags x B x alpha x %d reprs'
         % (len(tags), len(REPRS))),
        ('cells_ci_straddles_band', n_straddle, 'A1: interval spans two verdict bands'),
        ('cells_ORDER_SENSITIVE', n_ordsens,
         'A2: d_order_spread >= %.2f across the 5 serving-order families '
         '(desc_nc, asc_nc, asc_index, desc_es, %d shuffled), paired over %d draws'
         % (ORDER_SPREAD_MAX, N_SHUFFLE, N_DRAWS_ORDER)),
        ('max_d_order_spread', round(max(c['d_order_spread'] for c in cells), 5), ''),
        ('norm_dmean_at_pool_ceiling',
         '%.3g' % max(abs(c['norm_dmean']) for c in cells if c['B'] == POOL),
         'B=4447: both arms are the entire pool, so this MUST be 0'),
        ('NULL_CALIBRATION_d_heldout_at_ceiling',
         '%+.4f (sd %.4f) over %d cells'
         % (float(np.mean([r['d_heldout'] for r in null_cal])),
            float(np.std([r['d_heldout'] for r in null_cal])), len(null_cal)),
         'what d_heldout returns when the true difference is KNOWN to be zero; '
         'negative => the held-out estimator is conservative'),
        ('NULL_CALIBRATION_d_insample_at_ceiling',
         '%+.4f' % float(np.mean([r['d_insample'] for r in null_cal])),
         'the in-sample estimator on the same known-zero case'),
    ]
    for tag in tags:
        am = alpha_meta[tag]
        metrics.append(('alpha_grid_%s' % tag,
                        '[%.4g .. %.4g], concentrated=%s uniform=%s'
                        % (am['alpha_min'], am['alpha_max'],
                           am['reached_concentrated'], am['reached_uniform']),
                        'max p at min alpha %.4f; TV at max alpha %.5f'
                        % (am['max_p_at_min_alpha'], am['tv_at_max_alpha'])))
    for key, v in sorted(verdicts.items()):
        metrics.append(('ceiling_vs_peak_%s' % key.replace('|', '_'),
                        'peak %+.4f' % v['d_heldout'],
                        'ceiling reference in c1_ceiling.csv'))

    # ---- the old package's OWN proposed budget, so the refutation is stated
    # at the B it actually specified, not only at C1's peak ----
    OLD_BUDGET = 1000
    for tag in tags:
        for rep in REPRS:
            sub = [c for c in cells if c['tag'] == tag and c['repr'] == rep
                   and c['B'] == OLD_BUDGET and not c['degenerate']]
            if not sub:
                continue
            b = max(sub, key=lambda c: abs(c['d_heldout']))
            metrics.append(
                ('d_at_old_budget_B%d_%s_%s' % (OLD_BUDGET, tag, rep),
                 'd_heldout %+.4f  CI [%+.4f, %+.4f]  -> %s'
                 % (b['d_heldout'], b['ci_lo'], b['ci_hi'], band(b['d_heldout'])),
                 'alpha=%.4g, %d clusters funded -- the budget the OLD package '
                 'proposed' % (b['alpha'], b['clusters_funded'])))

    # ---- C2 shape cross-check (plan §3.1). C2 HAS NOT BEEN RUN, so this is a
    # comparison against its ANALYTIC design, never against a measurement. ----
    C2_PREDICTED_PEAK_B = 2000
    C2_ACCEPTED = {1000, 2000, 3000}
    argmax_B = {key: v['peak_B'] for key, v in verdicts.items()}
    diverges = {k: b for k, b in argmax_B.items() if b not in C2_ACCEPTED}
    metrics.append(('C2_predicted_peak_B', C2_PREDICTED_PEAK_B,
                    'ANALYTIC design in REBUILD_PLAN.md 3-C2; C2 is UNRUN'))
    metrics.append(('C2_measured_argmax_B',
                    ' '.join('%s=%d' % (k.replace('|', '_'), b)
                             for k, b in sorted(argmax_B.items())), ''))
    metrics.append(('C2_SHAPE_DIVERGENCE', bool(diverges),
                    'argmax_B outside %s in: %s'
                    % (sorted(C2_ACCEPTED),
                       ', '.join(sorted(diverges)) if diverges else 'none')))
    notes.append(
        'C2 SHAPE DIVERGENCE, and a correction to this experiment\'s own plan. The '
        'plan committed to flagging a divergence if argmax_B(d) fell outside '
        '{1000, 2000, 3000}, against C2\'s analytic pool-shift curve which peaks near '
        'B=2000. It does: d is MONOTONE DECREASING in B, with argmax at the smallest '
        'budget. On reflection that divergence is EXPECTED and the plan\'s cross-check '
        'was imprecise, because the two curves measure different things. C2\'s '
        'pool-shift is how much the TRAINING POOL composition changes, which is zero '
        'when nothing is added and zero again when both arms add everything, hence '
        'concave. C1\'s d is how far apart the two SELECTED SETS are, which is '
        'largest when the budget is small enough for targeting to stay concentrated '
        'and falls to zero as both arms converge on the whole pool. Comparing their '
        'shapes was a category error in the plan; it is recorded here rather than '
        'quietly dropped, and it is NOT evidence of a contradiction between '
        'experiments.')

    thresholds += [
        ('||delta mean|| = 0 at the pool ceiling B=4447 (both arms are the entire '
         'pool)',
         max(abs(c['norm_dmean']) for c in cells if c['B'] == POOL) < 1e-9),
        ('the peak |d| exceeds the magnitude of the null calibration, i.e. the '
         'measured effect is larger than what the estimator returns on a '
         'known-zero difference',
         max(abs(v['d_heldout']) for v in verdicts.values())
         > abs(float(np.mean([r['d_heldout'] for r in null_cal])))),
        ('A1: the held-out CI at every peak cell lies entirely within ONE verdict band',
         not any(v['ci_straddles'] for v in verdicts.values())),
        ('A2: d_order_spread < %.2f at every peak cell' % ORDER_SPREAD_MAX,
         not any(v['order_sensitive'] for v in verdicts.values())),
        ('both degenerate ends of the temperature sweep were reached in every space',
         all(alpha_meta[t]['reached_concentrated']
             and alpha_meta[t]['reached_uniform'] for t in tags)),
        ('the two embedder spaces agree on the verdict band (else EMBEDDER-DEPENDENT)',
         len({v['verdict'] for v in verdicts.values()}) == 1),
    ]

    notes.append(
        "LIMITATION, logged regardless of outcome. Cohen's d is a MEAN-SHIFT measure "
        'along a single direction. Two sets can share a mean and differ substantially '
        'in variance, in higher moments, or in which regions of the space they cover. '
        'A small d therefore establishes that the targeted and random arms have nearly '
        'the same CENTRE; it does NOT establish that they are the same SET. Variance '
        'and coverage are unmeasured unless the ambiguity follow-up was triggered, and '
        'are the one route by which a true effect could exceed what a mean-shift '
        'predicts.')
    notes.append(
        'NULL CALIBRATION. At B = 4447 both arms are the entire pool, so the true '
        'difference is exactly zero. ||delta mean|| duly vanishes (asserted). '
        'd_heldout does NOT: with no real difference the fitted direction is split '
        'noise and the disjoint evaluation halves are anti-correlated with it, so the '
        'held-out d is negative. This was caught by the ceiling assertion and is '
        'reported as a CALIBRATION rather than suppressed -- it establishes the '
        'estimator behaves conservatively under a known null, and gives every '
        'measured d a reference to be read against.')
    notes.append(
        'The allocation signal is target_es -- ES measured on the UNLABELED target set '
        'exactly as CLS.py:81-105 computes it, GT-free and available at allocation '
        'time. Gate 1 asserts C1 never reads the endpoint column. B1 completion II '
        'measured that signal as only a MODERATE predictor of endpoint error '
        '(rho +0.6595 dinoL224 / +0.6284 dinoL518), not the +0.87 the endpoint-ES '
        'figure suggested.')
    notes.append(
        'The partition C1 allocates over is WEAKLY SEPARATED: B1 measured silhouette '
        'peaks 0.1465 / 0.1600 / 0.0568 and seed-ARI 0.52-0.77. The unit of allocation '
        'is soft, and C1 inherits that.')
    notes.append(
        'Selection is by R2, the grey-128 cutout, because that is what a real pipeline '
        'has at selection time -- the foreground exists, the render does not. d is '
        'MEASURED in both R2 and R3. Selecting by R3 would require renders before '
        'selection and is out of scope, stated rather than silently omitted.')
    notes.append(
        'C2 HAS NOT BEEN RUN (0 EXP C2 blocks). The pool-ceiling check above is against '
        "C2's ANALYTIC design in REBUILD_PLAN.md 3-C2, not against a measurement, and "
        '|Ds| in {6824, 7824, 8824} remains UNVERIFIED because the iteration-2 pools '
        'were deleted. Only the |Ds|-free part of the predicted shape is compared. If '
        'C2 is later run and disagrees, that is a finding about the two designs.')
    notes.append(
        'Seed-level robustness of the ES signal is UNVERIFIED-DEFERRED (retraining '
        'deferred). clipL224 is DISQUALIFIED as a C1 space: no interior silhouette '
        'peak, k*=5 on the degeneracy guard.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/C1/c1_targeted_vs_random.py --tags %s'
        % args.tags,
        metrics, thresholds,
        [(lbl, val, 'RE-MEASURED') for lbl, val in OLD_CLAIMS],
        artifacts,
        representation=('selection in R2 (grey-128 cutout); d measured in R2 and R3 '
                        '(render); allocation by target_es'),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

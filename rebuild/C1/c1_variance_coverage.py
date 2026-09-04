#!/usr/bin/env python
"""C1 follow-up -- is the measured d attributable to ES-targeting, and do the
arms differ in anything besides their centre?

C1 returned REOPENS with d_heldout ~1.0-1.23. C1_PLAN.md §5 committed to logging,
regardless of outcome, that Cohen's d is a MEAN-SHIFT along a single FITTED
direction, and that variance and coverage stay unmeasured unless the follow-up
runs. The plan's trigger (AMBIGUOUS band or straddling CI) did not fire, so this
runs as an explicit audit rather than an automatic consequence.

Two questions, in this order, because the second is worthless if the first fails.

s1  ATTRIBUTION.  Is d~1.0 caused by ES-targeting, or by any structured
    selection, or by the statistic itself? Four nulls, all measured, never
    assumed:

      random_vs_random   two INDEPENDENT random draws. This is the true null for
                         a fitted-direction d -- NOT the B=POOL ceiling, which
                         compares a set with itself. If this is large, the
                         headline means nothing.
      shuffled_es        the ES vector permuted across clusters. Identical
                         allocation SHAPE, wrong cluster->budget mapping. Isolates
                         the ES content from the concentration it induces.
      random_centroid    B nearest to a RANDOMLY chosen real centroid. Tests
                         whether targeting the RIGHT clusters matters, or merely
                         targeting SOME cluster.
      random_direction   B nearest to a random unit vector. Tests whether any
                         structured selection whatsoever produces a large d.

s2  SPREAD.     trace-of-covariance ratio, pseudo-logdet over the top PCs,
                effective rank, mean within-set distance.
s3  COVERAGE.   k-NN recall and precision of each arm against the TARGET
                manifold, plus coverage of the foreground pool itself.
s4  OCCUPANCY.  clusters each arm touches, and the TV distance between the two
                arms' cluster-occupancy distributions.
s5  OVERLAP.    |A and R| against its chance expectation.

Consumes only committed artifacts via c1_space. TRAINS NOTHING; re-embeds nothing.

Usage:
  LAKE-RED/.venv/bin/python rebuild/C1/c1_variance_coverage.py
"""

import argparse
import csv
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
import common as C                                            # noqa: E402
import c1_preflight as PF                                     # noqa: E402
import c1_space                                               # noqa: E402
import c1_targeted_vs_random as M                             # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'C1'
OUT = C.exp_dir(EXP, 'out')
POOL = PF.POOL
E0_CACHE = C.exp_dir('E0', 'cache')

B_GRID = (250, 500, 1000, 2000, 3000)      # ceiling excluded: both arms identical
N_DRAWS = 20
TOP_PCS = 50
KNN = 5
REPRS = ('R2_cut', 'R3_render')


def _p(m):
    print(m, flush=True)


def arm_matrix(space, rep):
    return space.cut if rep == 'R2_cut' else space.render


def target_matrix(tag):
    """The target manifold, in the SAME space, with D2's leaked names dropped."""
    import json
    cls = np.load(os.path.join(E0_CACHE, '%s_tgt_cls.npy' % tag))
    names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % tag)))['tgt']
    leaked = set(json.load(open(PF.D2_LEAKED))['target_names_to_exclude'])
    keep = [i for i, n in enumerate(names) if n not in leaked]
    return C.l2(cls[keep].astype(np.float64))


# ---------------------------------------------------------------------------
# s1 -- attribution: four nulls
# ---------------------------------------------------------------------------

def targeted_indices(space, order_idx, alpha, B):
    alloc = M.largest_remainder(M.softmax_alloc(space.es, alpha), B)
    serving = sorted(range(space.k), key=lambda c: (-alloc[c], c))
    sel, _ = M.greedy_select(alloc, order_idx, serving)
    return sel, alloc


def null_indices(kind, space, order_idx, alpha, B, seed):
    """One realisation of a null arm. Same size B, same pool, same space."""
    rng = np.random.default_rng(seed)
    if kind == 'random_vs_random':
        return rng.choice(POOL, size=B, replace=False)
    if kind == 'shuffled_es':
        es_shuf = rng.permutation(space.es)          # same values, wrong clusters
        alloc = M.largest_remainder(M.softmax_alloc(es_shuf, alpha), B)
        serving = sorted(range(space.k), key=lambda c: (-alloc[c], c))
        sel, _ = M.greedy_select(alloc, order_idx, serving)
        return sel
    if kind == 'random_centroid':
        c = int(rng.integers(space.k))
        return order_idx[:B, c]
    if kind == 'random_direction':
        v = rng.normal(size=space.centroids.shape[1])
        v /= np.linalg.norm(v)
        return np.argsort(-(arm_matrix(space, 'R2_cut') @ v), kind='stable')[:B]
    raise ValueError(kind)


NULLS = ('random_vs_random', 'shuffled_es', 'random_centroid', 'random_direction')


def step_attribution(space, rep, order_idx, alpha, B, n_draws=N_DRAWS):
    X = arm_matrix(space, rep)
    sel, _ = targeted_indices(space, order_idx, alpha, B)
    rows = []
    # the headline arm, recomputed here so this audit stands alone
    dh = [M.effect_size(X[sel], X[np.random.default_rng(10_000 + i)
                                  .choice(POOL, B, replace=False)], i)
          for i in range(n_draws)]
    tgt_d = float(np.mean([e['d_heldout'] for e in dh]))
    tgt_din = float(np.mean([e['d_insample'] for e in dh]))
    rows.append(dict(arm='TARGETED_by_target_es', d_heldout=tgt_d,
                     d_insample=tgt_din,
                     d_heldout_sd=float(np.std([e['d_heldout'] for e in dh]))))
    for kind in NULLS:
        vals, vin = [], []
        for i in range(n_draws):
            a = null_indices(kind, space, order_idx, alpha, B, 70_000 + i)
            r = np.random.default_rng(10_000 + i).choice(POOL, B, replace=False)
            e = M.effect_size(X[a], X[r], i)
            vals.append(e['d_heldout']); vin.append(e['d_insample'])
        rows.append(dict(arm=kind, d_heldout=float(np.mean(vals)),
                         d_insample=float(np.mean(vin)),
                         d_heldout_sd=float(np.std(vals))))
    base = {r['arm']: r['d_heldout'] for r in rows}
    for r in rows:
        r['incremental_vs_random_null'] = r['d_heldout'] - base['random_vs_random']
    return rows, sel


# ---------------------------------------------------------------------------
# s2 -- spread
# ---------------------------------------------------------------------------

def spread_stats(A, R, top=TOP_PCS):
    def stats(Z):
        Zc = Z - Z.mean(0)
        cov_trace = float((Zc ** 2).sum() / (len(Z) - 1))
        s = np.linalg.svd(Zc, compute_uv=False)
        ev = (s ** 2) / (len(Z) - 1)
        evt = ev[:top]
        return dict(trace_cov=cov_trace,
                    logdet_top=float(np.sum(np.log(evt[evt > 1e-12]))),
                    eff_rank=float((ev.sum() ** 2) / (ev ** 2).sum()),
                    mean_dist_to_own_mean=float(np.linalg.norm(Zc, axis=1).mean()))
    a, r = stats(A), stats(R)
    return dict(trace_cov_A=a['trace_cov'], trace_cov_R=r['trace_cov'],
                trace_ratio=a['trace_cov'] / r['trace_cov'],
                logdet_top_A=a['logdet_top'], logdet_top_R=r['logdet_top'],
                logdet_ratio=a['logdet_top'] - r['logdet_top'],
                eff_rank_A=a['eff_rank'], eff_rank_R=r['eff_rank'],
                eff_rank_ratio=a['eff_rank'] / r['eff_rank'],
                spread_A=a['mean_dist_to_own_mean'],
                spread_R=r['mean_dist_to_own_mean'],
                spread_ratio=(a['mean_dist_to_own_mean']
                              / r['mean_dist_to_own_mean']))


# ---------------------------------------------------------------------------
# s3 -- coverage of the target manifold
# ---------------------------------------------------------------------------

def coverage_stats(A, R, T, k=KNN):
    """Recall: fraction of TARGET images having an arm image among their k-NN
    within the arm. Precision: fraction of arm images whose nearest target is
    within the arm's own k-NN radius. Both computed identically for both arms."""
    def rec(Z):
        sim = T @ Z.T                                  # (n_target, B)
        kk = min(k, Z.shape[0])
        idx = np.argpartition(-sim, kk - 1, axis=1)[:, :kk]
        covered = np.unique(idx)
        return dict(recall_frac_of_arm_used=float(len(covered) / Z.shape[0]),
                    mean_top1_sim=float(sim.max(axis=1).mean()),
                    mean_topk_sim=float(np.take_along_axis(sim, idx, 1).mean()))
    a, r = rec(A), rec(R)
    return dict(target_recall_A=a['recall_frac_of_arm_used'],
                target_recall_R=r['recall_frac_of_arm_used'],
                target_recall_delta=(a['recall_frac_of_arm_used']
                                     - r['recall_frac_of_arm_used']),
                mean_top1_sim_A=a['mean_top1_sim'],
                mean_top1_sim_R=r['mean_top1_sim'],
                mean_top1_sim_delta=a['mean_top1_sim'] - r['mean_top1_sim'],
                mean_topk_sim_A=a['mean_topk_sim'],
                mean_topk_sim_R=r['mean_topk_sim'])


# ---------------------------------------------------------------------------
# s4 / s5 -- occupancy and overlap
# ---------------------------------------------------------------------------

def occupancy_stats(space, sel, rnd):
    cent = space.centroids
    def occ(idx):
        lab = (space.cut[idx] @ cent.T).argmax(1)
        cnt = np.bincount(lab, minlength=space.k).astype(np.float64)
        p = cnt / cnt.sum()
        return cnt, p
    ca, pa = occ(sel)
    cr, pr = occ(rnd)
    return dict(clusters_touched_A=int((ca > 0).sum()),
                clusters_touched_R=int((cr > 0).sum()),
                clusters_total=space.k,
                occupancy_tv=float(0.5 * np.abs(pa - pr).sum()),
                occupancy_entropy_A=float(-(pa[pa > 0] * np.log(pa[pa > 0])).sum()
                                          / np.log(space.k)),
                occupancy_entropy_R=float(-(pr[pr > 0] * np.log(pr[pr > 0])).sum()
                                          / np.log(space.k)))


def overlap_stats(sel, rnd, B):
    inter = len(set(sel.tolist()) & set(rnd.tolist()))
    exp = B * B / POOL
    return dict(overlap=inter, overlap_expected_by_chance=exp,
                overlap_ratio=inter / exp if exp else float('nan'),
                jaccard=inter / len(set(sel.tolist()) | set(rnd.tolist())))


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tags', default='%s,%s' % (PF.PRIMARY, PF.SENSITIVITY))
    ap.add_argument('--draws', type=int, default=N_DRAWS)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    tags = [t.strip() for t in args.tags.split(',')]
    os.makedirs(OUT, exist_ok=True)

    import json
    verdicts = json.load(open(os.path.join(OUT, 'c1_verdicts.json')))
    metrics, thresholds, notes, artifacts = [], [], [], []
    attr_rows, spread_rows, cov_rows, occ_rows = [], [], [], []

    for tag in tags:
        space = c1_space.load_space(tag)
        _, order_idx = M.rank_by_centroid(space)
        T = target_matrix(tag)
        for rep in REPRS:
            v = verdicts['%s|%s' % (tag, rep)]
            peak_alpha = v['peak_alpha']
            X = arm_matrix(space, rep)
            for B in B_GRID:
                rows, sel = step_attribution(space, rep, order_idx, peak_alpha, B,
                                             args.draws)
                for r in rows:
                    attr_rows.append(dict(tag=tag, repr=rep, B=B,
                                          alpha=peak_alpha, **r))
                rnd = np.random.default_rng(10_000).choice(POOL, B, replace=False)
                sp = spread_stats(X[sel], X[rnd])
                spread_rows.append(dict(tag=tag, repr=rep, B=B, **sp))
                cv = coverage_stats(X[sel], X[rnd], T)
                cov_rows.append(dict(tag=tag, repr=rep, B=B, **cv))
                oc = occupancy_stats(space, sel, rnd)
                ov = overlap_stats(sel, rnd, B)
                occ_rows.append(dict(tag=tag, repr=rep, B=B, **oc, **ov))
            _p('  %s %s done' % (tag, rep))

    def dump(rows, name):
        p = os.path.join(OUT, name)
        with open(p, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        artifacts.append('rebuild/C1/out/' + name)
    dump(attr_rows, 'c1_attribution.csv')
    dump(spread_rows, 'c1_spread.csv')
    dump(cov_rows, 'c1_coverage.csv')
    dump(occ_rows, 'c1_occupancy.csv')

    # ---------------- s1 headline: attribution ----------------
    for tag in tags:
        for rep in REPRS:
            sub = [r for r in attr_rows if r['tag'] == tag and r['repr'] == rep]
            byB = {}
            for r in sub:
                byB.setdefault(r['B'], {})[r['arm']] = r
            peakB = max(byB, key=lambda b: byB[b]['TARGETED_by_target_es']['d_heldout'])
            g = byB[peakB]
            metrics.append(
                ('ATTRIBUTION_%s_%s_B%d' % (tag, rep, peakB),
                 'targeted %+.4f | rnd-vs-rnd %+.4f | shuffled-ES %+.4f | '
                 'rnd-centroid %+.4f | rnd-direction %+.4f'
                 % (g['TARGETED_by_target_es']['d_heldout'],
                    g['random_vs_random']['d_heldout'],
                    g['shuffled_es']['d_heldout'],
                    g['random_centroid']['d_heldout'],
                    g['random_direction']['d_heldout']),
                 'all d_heldout, same B, same pool, same space'))
    rr = [r for r in attr_rows if r['arm'] == 'random_vs_random']
    tt = [r for r in attr_rows if r['arm'] == 'TARGETED_by_target_es']
    se = [r for r in attr_rows if r['arm'] == 'shuffled_es']
    metrics += [
        ('NULL_random_vs_random_d_heldout',
         '%+.4f (range %+.4f .. %+.4f)' % (float(np.mean([r['d_heldout'] for r in rr])),
                                           min(r['d_heldout'] for r in rr),
                                           max(r['d_heldout'] for r in rr)),
         'THE null for a fitted-direction d: two independent random draws'),
        ('NULL_random_vs_random_d_INSAMPLE',
         '%+.4f (range %+.4f .. %+.4f)' % (float(np.mean([r['d_insample'] for r in rr])),
                                           min(r['d_insample'] for r in rr),
                                           max(r['d_insample'] for r in rr)),
         'the SAME null under the in-sample estimator -- why held-out is the headline'),
        ('TARGETED_minus_NULL_min_over_cells',
         '%+.4f' % min(r['incremental_vs_random_null'] for r in tt),
         'smallest incremental effect of ES-targeting over the random-vs-random null'),
        ('SHUFFLED_ES_minus_NULL_max',
         '%+.4f' % max(r['incremental_vs_random_null'] for r in se),
         'what the same allocation SHAPE achieves with the ES values scrambled'),
    ]
    # ---- the DECISIVE comparison: paired, per cell, targeted vs its own controls.
    # SHUFFLED_ES_minus_NULL_max above compares a MAX over cells against a MIN over
    # cells, which is unfair in both directions. These pair (tag, repr, B) exactly.
    def by_cell(arm):
        return {(r['tag'], r['repr'], r['B']): r['d_heldout']
                for r in attr_rows if r['arm'] == arm}
    t_c = by_cell('TARGETED_by_target_es')
    keys = sorted(t_c)
    paired = {}
    for arm, what in (('shuffled_es', 'same allocation SHAPE, ES values permuted '
                       'across clusters'),
                      ('random_centroid', 'whole budget to an ARBITRARY cluster'),
                      ('random_direction', 'B extremes along a RANDOM unit direction')):
        o = by_cell(arm)
        vals = [t_c[k] - o[k] for k in keys]
        paired[arm] = vals
        metrics.append(
            ('ES_SIGNAL_INCREMENT_vs_%s' % arm,
             'mean %+.4f | sd %.4f | range %+.4f .. %+.4f | ES wins %d/%d cells'
             % (float(np.mean(vals)), float(np.std(vals)), min(vals), max(vals),
                sum(1 for v in vals if v > 0), len(vals)),
             'PAIRED per (tag, repr, B): d_heldout(targeted) MINUS d_heldout(%s)'
             % what))

    # cross-check against the ORIGINAL C1 run's own ceiling artifact
    try:
        cel = {(r['tag'], r['repr'], int(r['B'])): float(r['d_heldout_mean'])
               for r in csv.DictReader(open(os.path.join(OUT, 'c1_ceiling.csv')))}
        rc = by_cell('random_centroid')
        ck = [k for k in sorted(cel) if k in rc]
        cd = [cel[k] - rc[k] for k in ck]
        metrics.append(
            ('CEILING_top_ES_cluster_MINUS_random_cluster',
             'mean %+.4f | range %+.4f .. %+.4f | top-ES wins %d/%d cells'
             % (float(np.mean(cd)), min(cd), max(cd),
                sum(1 for v in cd if v > 0), len(cd)),
             'c1_ceiling.csv (whole budget to the HIGHEST-target_es cluster, from the '
             'ORIGINAL C1 run) vs this audit\'s whole-budget-to-an-ARBITRARY-cluster '
             'arm -- two independently produced artifacts'))
        thresholds.append(
            ('C1\'s ceiling is a TARGETING ceiling: spending the whole budget on the '
             'highest-ES cluster beats spending it on an arbitrary cluster in a '
             'majority of cells',
             sum(1 for v in cd if v > 0) > len(cd) / 2))
    except (IOError, OSError, KeyError):
        notes.append('c1_ceiling.csv unavailable; ceiling cross-check SKIPPED.')

    thresholds += [
        ('the random-vs-random null is small (|d| < 0.3), so a fitted-direction d '
         'does not manufacture an effect from sampling noise alone',
         max(abs(r['d_heldout']) for r in rr) < 0.3),
        ('ES-targeting exceeds the random-vs-random null by more than 0.5 in EVERY '
         'cell, i.e. the REOPENS verdict is attributable to targeting rather than to '
         'the statistic',
         min(r['incremental_vs_random_null'] for r in tt) > 0.5),
        ('the in-sample estimator would have been unusable: its random-vs-random '
         'null exceeds 0.5',
         max(abs(r['d_insample']) for r in rr) > 0.5),
        ('the ES SIGNAL itself adds something: targeted d_heldout beats its own '
         'ES-shuffled control by at least 0.1 in a majority of cells',
         sum(1 for v in paired['shuffled_es'] if v >= 0.1) > len(keys) / 2),
        ('targeting the HIGHEST-ES cluster beats targeting an ARBITRARY cluster in a '
         'majority of cells',
         sum(1 for v in paired['random_centroid'] if v > 0) > len(keys) / 2),
    ]

    # ---------------- s2/s3/s4 ----------------
    for tag in tags:
        for rep in REPRS:
            s1000 = [r for r in spread_rows if r['tag'] == tag and r['repr'] == rep
                     and r['B'] == 1000]
            c1000 = [r for r in cov_rows if r['tag'] == tag and r['repr'] == rep
                     and r['B'] == 1000]
            o1000 = [r for r in occ_rows if r['tag'] == tag and r['repr'] == rep
                     and r['B'] == 1000]
            if not s1000:
                continue
            s0, c0, o0 = s1000[0], c1000[0], o1000[0]
            metrics += [
                ('SPREAD_%s_%s_B1000' % (tag, rep),
                 'trace ratio %.4f | eff-rank %.1f vs %.1f (%.3f) | logdet delta %+.1f'
                 % (s0['trace_ratio'], s0['eff_rank_A'], s0['eff_rank_R'],
                    s0['eff_rank_ratio'], s0['logdet_ratio']),
                 'targeted vs random; <1 means the targeted arm is NARROWER'),
                ('COVERAGE_%s_%s_B1000' % (tag, rep),
                 'arm-used-by-target %.4f vs %.4f (delta %+.4f) | mean top1 sim '
                 '%.4f vs %.4f (delta %+.4f)'
                 % (c0['target_recall_A'], c0['target_recall_R'],
                    c0['target_recall_delta'], c0['mean_top1_sim_A'],
                    c0['mean_top1_sim_R'], c0['mean_top1_sim_delta']),
                 'against the 4033-image TARGET manifold, k=%d' % KNN),
                ('OCCUPANCY_%s_%s_B1000' % (tag, rep),
                 'clusters touched %d vs %d of %d | TV %.4f | overlap %d vs %.0f '
                 'expected (ratio %.3f)'
                 % (o0['clusters_touched_A'], o0['clusters_touched_R'],
                    o0['clusters_total'], o0['occupancy_tv'], o0['overlap'],
                    o0['overlap_expected_by_chance'], o0['overlap_ratio']),
                 ''),
            ]
    narrower = [r for r in spread_rows if r['trace_ratio'] < 1.0]
    metrics.append(('cells_where_targeted_arm_is_NARROWER',
                    '%d/%d' % (len(narrower), len(spread_rows)),
                    'trace-of-covariance ratio < 1'))
    worse_cov = [r for r in cov_rows if r['target_recall_delta'] < 0]
    metrics.append(('cells_where_targeted_arm_COVERS_TARGET_LESS',
                    '%d/%d' % (len(worse_cov), len(cov_rows)),
                    'fraction of the arm used as a target nearest-neighbour'))
    metrics.append(('cells_where_targeted_arm_has_LOWER_EFFECTIVE_RANK',
                    '%d/%d (mean ratio %.3f)'
                    % (sum(1 for r in spread_rows if r['eff_rank_ratio'] < 1.0),
                       len(spread_rows),
                       float(np.mean([r['eff_rank_ratio'] for r in spread_rows]))),
                    'participation ratio of the covariance spectrum. Reported as an '
                    'OBSERVATION, not a declared threshold -- see NOTES on why it is '
                    'not used to rescue the trace-ratio threshold below'))
    thresholds.append(
        ('the arms differ in more than their centre: spread ratio departs from 1 by '
         'at least 5% in a majority of cells',
         sum(1 for r in spread_rows if abs(r['trace_ratio'] - 1) >= 0.05)
         > len(spread_rows) / 2))

    notes.append(
        'WHY THIS RUNS. C1_PLAN.md §5 committed to logging, regardless of outcome, '
        'that Cohen\'s d is a mean-shift along a single FITTED direction and that '
        'variance and coverage remain unmeasured unless this follow-up runs. The '
        'plan\'s automatic trigger (AMBIGUOUS band or straddling CI) did NOT fire -- '
        'C1 returned a clean REOPENS -- so this is an explicit audit, not an '
        'automatic consequence, and it is labelled as such.')
    notes.append(
        'THE NULL THAT MATTERS. C1 used B=POOL as a null calibration, but there both '
        'arms are the SAME SET. The correct null for a fitted-direction d is two '
        'INDEPENDENT random draws of the same size: different sets, no targeting. '
        'That null is measured here for every cell. It is the control that decides '
        'whether C1\'s headline is about ES-targeting or about the statistic.')
    notes.append(
        'THE IN-SAMPLE ESTIMATOR WOULD HAVE BEEN UNUSABLE. Under random-vs-random -- '
        'where there is no targeting at all -- the in-sample d is large, because the '
        'direction is fitted to the very sampling noise it then measures. The '
        'held-out estimator returns approximately zero on the same data. Had C1 '
        'reported d_insample as its headline, its REOPENS verdict would have been an '
        'artefact. This is the strongest available justification for the held-out '
        'choice, and it is a measurement rather than an argument.')
    notes.append(
        'PROVENANCE OF THE PAIRED METRICS -- stated because it matters. This script '
        'was first executed with --no-log (exploratory, nothing written). The four '
        'null arms, the random-vs-random threshold and the in-sample threshold were '
        'declared BEFORE that pass. The ES_SIGNAL_INCREMENT_* metrics and their two '
        'thresholds, and the ceiling cross-check, were added AFTER seeing it. They '
        'are TIGHTENINGS: each makes the audit harder to pass, none was chosen to '
        'make a failing criterion pass, and no declared threshold was weakened or '
        'removed. Their content was already implied by the pre-declared '
        'SHUFFLED_ES_minus_NULL_max metric; the change is that they pair (tag, repr, '
        'B) exactly instead of comparing a max over cells against a min over cells.')
    notes.append(
        'TRACE AND EFFECTIVE RANK DISAGREE, AND THE DECLARED CRITERION LOSES. The '
        'declared spread threshold is on trace-of-covariance, which departs from 1 by '
        'only 1-2% -- it FAILS. Effective rank tells a different story: the targeted '
        'arm occupies roughly half the effective dimensionality. Trace is dominated '
        'by the isotropic bulk of a 1024-d embedding and is insensitive to that. The '
        'honest reading is that the declared metric was the wrong one, and it is '
        'reported as FAILED rather than quietly replaced by the one that agrees with '
        'the conclusion. Effective rank is reported beside it as an observation.')
    notes.append(
        'SCOPE. This audit still measures GEOMETRY, not accuracy. It establishes '
        'whether the targeted and random arms differ, in what respects, and whether '
        'the difference is attributable to the ES signal. It does NOT establish that '
        'any of it changes a trained model -- that remains C3\'s question and is '
        'untouched here.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/C1/c1_variance_coverage.py --tags %s'
        % args.tags,
        metrics, thresholds,
        [("C1 plan §5 follow-up (variance/coverage)", 'not triggered by the declared '
          'rule; run as an explicit audit', 'RUN ANYWAY')],
        artifacts,
        representation='selection in R2; geometry measured in R2 and R3',
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

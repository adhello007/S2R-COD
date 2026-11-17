#!/usr/bin/env python
"""AN-03 -- architecture-dependent boundary contrasts and the formal architecture interaction.

ANALYSIS_PRESPEC.md §7. Input: RUNS/exp02/exp02_per_run.csv (EXP-02; Gate 3 must have passed) and
RUNS/an01/an01_rescored_full.csv (S_alpha, for the same grid). Statistics: statlib.py (NumPy only),
cross-checked against scipy.

Outputs:
  RESULT_TABLES/AN-03_arch_boundary_grid.csv
  RESULT_TABLES/AN-03_interaction.csv
  RESULT_TABLES/EXP-02_rescored_predictions.csv   (one aggregate row per legitimate cell x arm)
  FIGURES/AN-03_architecture_contrasts.png
  EXPERIMENT_LOGS/AN-03_checks.json
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys

import numpy as np
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument('--sr', required=True)
a = ap.parse_args()
SR = a.sr
sys.path.insert(0, os.path.join(SR, 'scripts'))
import statlib as SL       # noqa: E402

SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
SEEDS3 = [42, 43, 45]
ARCHS = ['SINet', 'SINetv2']
EPS = ['COD10K', 'NC4K']
THR = [0.4, 0.5, 0.6]
METRICS = ['boundary_iou', 'boundary_f', 'Sm']
CONTRASTS = [('C10', 'B'), ('CINV', 'B'), ('CSHUF', 'B'), ('C10', 'CINV'), ('C10', 'CSHUF')]
HEADLINE = [('boundary_iou', 0.5, 'COD10K', 'C10-B'), ('boundary_iou', 0.5, 'COD10K', 'CINV-B')]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    meta = json.load(open(os.path.join(SR, 'EXPERIMENT_LOGS/EXP-02_meta.json')))
    assert meta['gate3']['passed'], 'EXP-02 Gate 3 failed -- AN-03 must not use these values'
    src_b = os.path.join(SR, 'RUNS/exp02/exp02_per_run.csv')
    src_s = os.path.join(SR, 'RUNS/an01/an01_rescored_full.csv')
    V, N = {}, {}
    for r in csv.DictReader(open(src_b)):
        if r['arm'] in ('A0', 'A2'):
            continue
        for m in ('boundary_iou', 'boundary_f'):
            V[(m, float(r['thresh']), r['arch'], r['endpoint'], r['arm'], int(r['seed']))] = float(r[m])
            N[(m, float(r['thresh']), r['arch'], r['endpoint'], r['arm'], int(r['seed']))] = (int(r['n']), int(r['n_nan_' + m]))
    for r in csv.DictReader(open(src_s)):
        for t in THR:     # S_alpha has no threshold; replicate so the grid is rectangular (flagged)
            V[('Sm', t, r['arch'], r['endpoint'], r['arm'], int(r['seed']))] = float(r['Sm'])
            N[('Sm', t, r['arch'], r['endpoint'], r['arm'], int(r['seed']))] = (int(r['n']), 0)
    checks = dict(scipy_mismatch=[])

    # ---- per-arm aggregate rows (EXP-02 deliverable)
    agg = []
    for m in ('boundary_iou', 'boundary_f'):
        for t in THR:
            for arch in ARCHS:
                for ep in EPS:
                    for arm in ('B', 'C10', 'CSHUF', 'CINV'):
                        xs = [V[(m, t, arch, ep, arm, s)] for s in SEEDS]
                        mu, sd = SL.mean_sd(xs)
                        agg.append(dict(metric=m, threshold=t, architecture=arch, endpoint=ep, arm=arm, n_seeds=8,
                                        seeds=' '.join(map(str, SEEDS)), mean=mu, sd=sd,
                                        n_images_per_run=N[(m, t, arch, ep, arm, SEEDS[0])][0],
                                        nan_images_excluded_total=sum(N[(m, t, arch, ep, arm, s)][1] for s in SEEDS),
                                        status='post-review exploratory; boundary metrics are post-hoc',
                                        data_sha256=sha(src_b)))
    # ---- grid of contrasts
    grid = []
    for m in METRICS:
        for t in THR:
            if m == 'Sm' and t != 0.5:
                continue
            for arch in ARCHS:
                for ep in EPS:
                    bar_sd, _ = SL.pooled_sd([[V[(m, t, arch, ep, arm, s)] for s in SEEDS] for arm in ('B', 'C10', 'CSHUF', 'CINV')])
                    bar3, _ = SL.pooled_sd([[V[(m, t, arch, ep, arm, s)] for s in SEEDS3] for arm in ('B', 'C10', 'CSHUF', 'CINV')])
                    for X, Y in CONTRASTS:
                        for subset, seeds, bsd in (('8-seed', SEEDS, bar_sd), ('3-seed {42,43,45}', SEEDS3, bar3)):
                            x = np.array([V[(m, t, arch, ep, X, s)] for s in seeds])
                            y = np.array([V[(m, t, arch, ep, Y, s)] for s in seeds])
                            P, W = SL.paired(x, y), SL.welch(x, y)
                            if not math.isclose(P['p'], float(stats.ttest_rel(x, y).pvalue), rel_tol=1e-9, abs_tol=1e-12):
                                checks['scipy_mismatch'].append((m, t, arch, ep, X, Y, subset))
                            grid.append(dict(
                                metric=m, threshold=(t if m != 'Sm' else 'n/a'), architecture=arch, endpoint=ep,
                                contrast='%s-%s' % (X, Y), seed_subset=subset, n_pairs=len(seeds),
                                seeds=' '.join(map(str, seeds)), mean_D=P['mean'], sd_D=P['sd'],
                                paired_ci95_lo=P['ci95'][0], paired_ci95_hi=P['ci95'][1], paired_p=P['p'],
                                welch_ci95_lo=W['ci95'][0], welch_ci95_hi=W['ci95'][1], welch_p=W['p'],
                                sign_pos=P['n_pos'], sign_neg=P['n_neg'],
                                bar_2x_pooled_sd_4arms=2 * bsd, gap_over_bar=abs(P['mean']) / (2 * bsd),
                                clears_bar_descriptive=abs(P['mean']) > 2 * bsd,
                                sign_rule=('%d/%d' % (max(P['n_pos'], P['n_neg']), len(seeds))),
                                headline=((m, t, ep, '%s-%s' % (X, Y)) in HEADLINE and subset == '8-seed'),
                                units=('S_alpha' if m == 'Sm' else m.replace('_', ' ')),
                                status='post-review exploratory; decides nothing',
                                test_selection_status='held-out endpoints; no test-label selection'))
    # Holm across the 8-seed grid (sensitivity only)
    idx8 = [i for i, g in enumerate(grid) if g['seed_subset'] == '8-seed']
    hp = SL.holm([grid[i]['paired_p'] for i in idx8])
    for i, h in zip(idx8, hp):
        grid[i]['holm_p_grid'] = h
    for g in grid:
        g.setdefault('holm_p_grid', '')
    # ---- interaction
    inter = []
    for m in METRICS:
        for t in THR:
            if m == 'Sm' and t != 0.5:
                continue
            for ep in EPS:
                for X, Y in CONTRASTS:
                    dS = np.array([V[(m, t, 'SINet', ep, X, s)] - V[(m, t, 'SINet', ep, Y, s)] for s in SEEDS])
                    dV = np.array([V[(m, t, 'SINetv2', ep, X, s)] - V[(m, t, 'SINetv2', ep, Y, s)] for s in SEEDS])
                    W = SL.welch(dS, dV)
                    sp = stats.ttest_ind(dS, dV, equal_var=False)
                    if not math.isclose(W['p'], float(sp.pvalue), rel_tol=1e-9, abs_tol=1e-12):
                        checks['scipy_mismatch'].append(('interaction', m, t, ep, X, Y))
                    perm_p, nperm = SL.permutation_two_group_exact(dS, dV)
                    E = SL.paired(dS, dV)
                    inter.append(dict(
                        metric=m, threshold=(t if m != 'Sm' else 'n/a'), endpoint=ep, contrast='%s-%s' % (X, Y),
                        n_seeds_per_arch=8, D_SINet=float(dS.mean()), D_SINetv2=float(dV.mean()),
                        delta_model=W['mean'], welch_se=W['se'], welch_df=W['df'],
                        welch_ci95_lo=W['ci95'][0], welch_ci95_hi=W['ci95'][1], welch_p=W['p'],
                        perm_p_exact=perm_p, perm_n_splits=nperm,
                        seed_matched_ci95_lo=E['ci95'][0], seed_matched_ci95_hi=E['ci95'][1], seed_matched_p=E['p'],
                        headline=((m, t, ep, '%s-%s' % (X, Y)) in HEADLINE),
                        interpretation_rule='interaction inferred only from this CI/permutation, never from '
                                            'separate per-architecture significance',
                        status='post-review exploratory'))
    hp = SL.holm([r['welch_p'] for r in inter])
    for r, h in zip(inter, hp):
        r['holm_p_interaction_family'] = h

    def wcsv(name, rs):
        with open(os.path.join(SR, 'RESULT_TABLES', name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]))
            w.writeheader()
            for r in rs:
                w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in r.items()})
    wcsv('EXP-02_rescored_predictions.csv', agg)
    wcsv('AN-03_arch_boundary_grid.csv', grid)
    wcsv('AN-03_interaction.csv', inter)

    # ---- figure: headline metric, all thresholds, both endpoints, 8-seed paired CI per architecture
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4), sharey='row')
    cols = {'SINet': '#2a6fbb', 'SINetv2': '#d1762b'}
    for i, ep in enumerate(EPS):
        for j, t in enumerate(THR):
            ax = axes[i, j]
            for k, (X, Y) in enumerate(CONTRASTS):
                for o, arch in enumerate(ARCHS):
                    g = next(g for g in grid if g['metric'] == 'boundary_iou' and g['threshold'] == t
                             and g['architecture'] == arch and g['endpoint'] == ep
                             and g['contrast'] == '%s-%s' % (X, Y) and g['seed_subset'] == '8-seed')
                    xpos = k + (o - 0.5) * 0.3
                    ax.errorbar([xpos], [g['mean_D']], yerr=[[g['mean_D'] - g['paired_ci95_lo']],
                                                             [g['paired_ci95_hi'] - g['mean_D']]],
                                fmt='o', color=cols[arch], capsize=3, label=arch if (k == 0) else None)
            ax.axhline(0, color='0.5', lw=0.8)
            ax.set_xticks(range(len(CONTRASTS)))
            ax.set_xticklabels(['%s-%s' % c for c in CONTRASTS], rotation=30, fontsize=8)
            ax.set_title('%s, threshold %.1f' % (ep, t), fontsize=9)
            if j == 0:
                ax.set_ylabel('Boundary-IoU difference\n(paired 95% CI, 8 seeds)', fontsize=8)
    axes[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle('Post-review exploratory: boundary-IoU contrasts by architecture (decides nothing)', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(SR, 'FIGURES/AN-03_architecture_contrasts.png'), dpi=150)
    checks.update(n_grid=len(grid), n_interaction=len(inter), data_sha256_boundary=sha(src_b),
                  data_sha256_sa=sha(src_s), gate3=meta['gate3'])
    json.dump(checks, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-03_checks.json'), 'w'), indent=1, default=str)
    print(json.dumps(checks, indent=1, default=str))
    for g in grid:
        if g['headline']:
            print('HEADLINE', {k: g[k] for k in ('metric', 'threshold', 'architecture', 'endpoint', 'contrast',
                                                 'mean_D', 'paired_ci95_lo', 'paired_ci95_hi', 'gap_over_bar', 'sign_rule')})
    for r in inter:
        if r['headline']:
            print('INTERACTION', {k: r[k] for k in ('contrast', 'D_SINet', 'D_SINetv2', 'delta_model', 'welch_ci95_lo',
                                                    'welch_ci95_hi', 'welch_p', 'perm_p_exact')})


if __name__ == '__main__':
    main()

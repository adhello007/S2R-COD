#!/usr/bin/env python
"""DIAG.5 -- boundary-metric verdicts and subgroup breakdowns.

Consumes DIAG.3's per-image boundary table and the committed per-image endpoint
scores. Trains nothing, infers nothing.

TWO QUESTIONS
-------------
1. The acquisition signal is BOUNDARY-focused (a Sobel-gradient L1 term), but the
   campaign was decided on S_alpha and reported MAE. Does the arm difference look
   different when measured by a metric built for boundaries? If targeting helps
   anywhere, this is where it should show.

2. Are the arms separable inside any SUBGROUP -- by object size, by endpoint
   uncertainty, by camouflage difficulty -- even where they are not separable on
   the whole set? A whole-set null can hide an effect that is real in a slice.

POST-HOC AND NON-DECISIONAL. The 2-sigma-hat machinery is reused so the numbers
are comparable to the committed ones, but no pre-registered verdict is re-decided
and no verdict here is a campaign verdict. Subgroup analysis at n=3 seeds is
exploratory by construction and is labelled that way.

Usage:
  .venv/bin/python rebuild/DIAG/diag_subgroups.py
"""

import csv
import json
import os

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')
B1_OUT = os.path.join(REPO, 'rebuild/B1/out')

SEEDS = (42, 43, 45)
METRICS = ('boundary_iou', 'boundary_f', 'iou')
NQ = 3          # tertiles: subgroup counts must stay large enough to mean anything


def _p(m):
    print(m, flush=True)


def sigma_hat(byarm, arms):
    """Pooled within-arm sd, exactly the committed definition."""
    ss = dfree = 0.0
    for a in arms:
        v = np.array([byarm[a][s] for s in SEEDS])
        ss += ((v - v.mean()) ** 2).sum()
        dfree += len(v) - 1
    return float(np.sqrt(ss / dfree)), int(dfree)


def verdict(delta, bar, signs):
    if abs(delta) <= bar:
        return 'WITHIN NOISE'
    if signs == 3 and delta > 0:
        return 'REAL EFFECT'
    if signs == 3 and delta < 0:
        return 'REAL REGRESSION'
    return 'INCONCLUSIVE'


def gap(byarm, hi, lo, bar):
    a = np.array([byarm[hi][s] for s in SEEDS])
    b = np.array([byarm[lo][s] for s in SEEDS])
    d = a - b
    pos = int((d > 0).sum())
    signs = max(pos, 3 - pos)
    return dict(delta=float(d.mean()), bar=bar, ratio=float(abs(d.mean()) / bar) if bar else None,
                sign_consistent='%d/3' % signs,
                per_seed={str(s): float(x) for s, x in zip(SEEDS, d)},
                verdict=verdict(float(d.mean()), bar, signs))


def main():
    os.makedirs(OUT, exist_ok=True)
    per = list(csv.DictReader(open(os.path.join(OUT, 'diag_boundary_per_image.csv'))))
    _p('loaded %d per-image boundary rows' % len(per))

    # ---- covariates, from the committed per-image endpoint scores ----------
    cov = {}
    for arch_tag, arch in (('SINet-S2C', 'SINet'), ('SINet-v2-S2C', 'SINetv2')):
        f = os.path.join(B1_OUT, 'b1_scores_%s_test.csv' % arch_tag)
        if not os.path.isfile(f):
            continue
        for r in csv.DictReader(open(f)):
            cov.setdefault(arch, {})[r['name']] = dict(
                es=float(r['es']), difficulty=float(r['one_minus_sa']),
                size=float(r['gt_fg_frac']))
    _p('covariates: ' + ', '.join('%s %d images' % (k, len(v)) for k, v in cov.items()))

    rows = []
    for r in per:
        rid = r['runid']
        arch, arm, seed = rid.split('_')[0], rid.split('_')[1], int(rid.split('_')[2][1:])
        c = cov.get(arch, {}).get(r['name'])
        if c is None:
            continue
        rows.append(dict(arch=arch, arm=arm, seed=seed, name=r['name'],
                         boundary_iou=float(r['boundary_iou']),
                         boundary_f=float(r['boundary_f']), iou=float(r['iou']),
                         size=c['size'], es=c['es'], difficulty=c['difficulty']))
    _p('rows with covariates: %d' % len(rows))

    res = dict(what='post-hoc boundary metrics and subgroup breakdowns',
               decides='nothing; the campaign endpoint metric remains S_alpha',
               n_rows=len(rows), whole_set={}, subgroups={})

    # ---- WHOLE SET --------------------------------------------------------
    for arch in sorted({r['arch'] for r in rows}):
        sub = [r for r in rows if r['arch'] == arch]
        arms = sorted({r['arm'] for r in sub})
        for m in METRICS:
            byarm = {}
            for a in arms:
                byarm[a] = {s: float(np.mean([r[m] for r in sub
                                              if r['arm'] == a and r['seed'] == s]))
                            for s in SEEDS}
            pool = [a for a in ('B', 'C10', 'CSHUF', 'CINV') if a in byarm]
            sh, dfree = sigma_hat(byarm, pool)
            bar = 2 * sh
            key = '%s|%s' % (arch, m)
            res['whole_set'][key] = dict(
                sigma_hat=sh, bar=bar, df=dfree, pooled_over=pool,
                arm_mean={a: float(np.mean(list(byarm[a].values()))) for a in arms},
                arm_sd={a: float(np.std(list(byarm[a].values()), ddof=1)) for a in arms},
                gaps={'%s-%s' % (h, l): gap(byarm, h, l, bar)
                      for h, l in (('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'),
                                   ('CSHUF', 'B'), ('CINV', 'B'), ('B', 'A2'), ('A2', 'A0'))
                      if h in byarm and l in byarm})

    # ---- SUBGROUPS --------------------------------------------------------
    for arch in sorted({r['arch'] for r in rows}):
        sub = [r for r in rows if r['arch'] == arch]
        arms = sorted({r['arm'] for r in sub})
        for cvar in ('size', 'es', 'difficulty'):
            vals = np.array([r[cvar] for r in sub if r['arm'] == arms[0]
                             and r['seed'] == SEEDS[0]])
            edges = np.quantile(vals, np.linspace(0, 1, NQ + 1))
            edges[0], edges[-1] = -np.inf, np.inf
            for q in range(NQ):
                lo, hi = edges[q], edges[q + 1]
                cell = [r for r in sub if lo <= r[cvar] < hi]
                if not cell:
                    continue
                byarm = {}
                for a in arms:
                    byarm[a] = {s: float(np.mean([r['boundary_iou'] for r in cell
                                                  if r['arm'] == a and r['seed'] == s]))
                                for s in SEEDS}
                bya_sa = {}
                for a in arms:
                    bya_sa[a] = {s: float(np.mean([r['iou'] for r in cell
                                                   if r['arm'] == a and r['seed'] == s]))
                                 for s in SEEDS}
                pool = [a for a in ('B', 'C10', 'CSHUF', 'CINV') if a in byarm]
                sh, _ = sigma_hat(byarm, pool)
                n_img = len(cell) // (len(arms) * len(SEEDS))
                res['subgroups']['%s|%s|q%d' % (arch, cvar, q + 1)] = dict(
                    covariate=cvar, quantile=q + 1, n_images=n_img,
                    range=[float(lo) if np.isfinite(lo) else None,
                           float(hi) if np.isfinite(hi) else None],
                    sigma_hat=sh, bar=2 * sh,
                    boundary_iou_gap_C10_B=gap(byarm, 'C10', 'B', 2 * sh)
                    if 'C10' in byarm and 'B' in byarm else None,
                    iou_arm_mean={a: float(np.mean(list(bya_sa[a].values()))) for a in arms})

    json.dump(res, open(os.path.join(OUT, 'diag_subgroups.json'), 'w'),
              indent=2, sort_keys=True)

    # ---- report -----------------------------------------------------------
    _p('\n' + '=' * 78)
    _p('DIAG.5  boundary metrics -- whole set (POST-HOC, decides nothing)')
    _p('=' * 78)
    for key in sorted(res['whole_set']):
        w = res['whole_set'][key]
        _p('\n--- %s   sigma_hat %.6f  bar %.6f (df %d) ---' % (key, w['sigma_hat'], w['bar'], w['df']))
        _p('  arm means: ' + '  '.join('%s %.4f' % (a, v) for a, v in sorted(w['arm_mean'].items())))
        for g, v in sorted(w['gaps'].items()):
            _p('    %-12s delta %+.6f  %5.2fx bar  %s  %s'
               % (g, v['delta'], v['ratio'], v['sign_consistent'], v['verdict']))
    _p('\n' + '=' * 78)
    _p('DIAG.5  subgroups -- boundary IoU, C10 vs B (EXPLORATORY)')
    _p('=' * 78)
    for key in sorted(res['subgroups']):
        s = res['subgroups'][key]
        g = s['boundary_iou_gap_C10_B']
        if g is None:
            continue
        _p('  %-28s n=%4d  delta %+.6f  %5.2fx bar  %s  %s'
           % (key, s['n_images'], g['delta'], g['ratio'], g['sign_consistent'], g['verdict']))
    _p('\nwrote %s' % os.path.join(OUT, 'diag_subgroups.json'))


if __name__ == '__main__':
    main()

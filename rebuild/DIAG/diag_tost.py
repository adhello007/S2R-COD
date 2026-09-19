#!/usr/bin/env python
"""DIAG.1 -- formal equivalence testing (TOST) and interval estimation.

Reads ONLY committed metric tables. Trains nothing, infers nothing, and writes
nothing outside rebuild/DIAG/out/.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
The campaign verdicts are the pre-registered `2*sigma_hat` rule in
rebuild/ABC/PREREGISTRATION.md and PREREGISTRATION_T2.md, which state at n=3:
"NO p-value, no bootstrap, no multiple-comparison correction". This script does
NOT overturn, replace or re-decide any of those verdicts. It is a POST-HOC,
NON-DECISIONAL supplement that answers a different question a reader may fairly
ask -- "what interval is actually consistent with your data?" -- and it is
labelled as post-hoc everywhere it is reported.

Every verdict in the paper stands on the frozen rule. Nothing here changes one.

Usage:
  .venv/bin/python rebuild/DIAG/diag_tost.py
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

DELTA = 0.005          # SESOI, declared by the revision brief (Category 2.1)
ALPHA = 0.05           # TOST operates at alpha; the CI it corresponds to is 90%
METRIC = 'Sm'          # S_alpha, the primary endpoint metric
SEEDS = (42, 43, 45)


def _p(m):
    print(m, flush=True)


def load(path):
    with open(os.path.join(REPO, path), newline='') as fh:
        return list(csv.DictReader(fh))


def cells(rows):
    """(arch, endpoint) -> arm -> seed -> value."""
    d = {}
    for r in rows:
        d.setdefault((r['arch'], r['endpoint']), {}) \
         .setdefault(r['arm'], {})[int(r['seed'])] = float(r[METRIC])
    return d


def welch(a, b):
    """Welch (unequal-variance) two-sample statistics for mean(a) - mean(b)."""
    na, nb = len(a), len(b)
    ma, mb = np.mean(a), np.mean(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    se = np.sqrt(va / na + vb / nb)
    if se == 0:
        return dict(diff=float(ma - mb), se=0.0, df=float('nan'), t=float('nan'))
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return dict(diff=float(ma - mb), se=float(se), df=float(df), t=float((ma - mb) / se))


def paired(a, b):
    """Paired statistics on the seed-matched differences a_i - b_i."""
    d = np.asarray(a) - np.asarray(b)
    n = len(d)
    se = float(np.std(d, ddof=1) / np.sqrt(n))
    return dict(diff=float(d.mean()), se=se, df=float(n - 1),
                t=float(d.mean() / se) if se else float('nan'),
                per_seed={str(s): float(x) for s, x in zip(SEEDS, d)},
                sd_of_diff=float(np.std(d, ddof=1)))


def ci(st_, level):
    if not np.isfinite(st_['se']) or st_['se'] == 0 or not np.isfinite(st_['df']):
        return [st_['diff'], st_['diff']]
    tc = stats.t.ppf(0.5 + level / 2.0, st_['df'])
    return [float(st_['diff'] - tc * st_['se']), float(st_['diff'] + tc * st_['se'])]


def tost(st_, delta):
    """Two one-sided tests for equivalence within +/- delta.

    H01: diff <= -delta   (tested upper-tail)
    H02: diff >= +delta   (tested lower-tail)
    Equivalence is concluded iff BOTH are rejected, i.e. p_tost = max(p1,p2) < alpha.
    """
    if not np.isfinite(st_['se']) or st_['se'] == 0 or not np.isfinite(st_['df']):
        return dict(p_lower=float('nan'), p_upper=float('nan'),
                    p_tost=float('nan'), equivalent=None,
                    note='degenerate standard error')
    t1 = (st_['diff'] + delta) / st_['se']          # vs -delta, want t1 large positive
    t2 = (st_['diff'] - delta) / st_['se']          # vs +delta, want t2 large negative
    p1 = float(stats.t.sf(t1, st_['df']))           # P(T > t1)
    p2 = float(stats.t.cdf(t2, st_['df']))          # P(T < t2)
    p = max(p1, p2)
    return dict(p_lower=p1, p_upper=p2, p_tost=p, equivalent=bool(p < ALPHA))


def achieved_bound(st_):
    """The SMALLEST delta at which this data WOULD conclude equivalence at alpha.

    Equivalent to the upper end of the 90% CI in absolute value -- the standard
    'equivalence bound achieved' quantity. Reported because it converts a failed
    TOST into the honest positive statement the data does support.
    """
    if not np.isfinite(st_['se']) or st_['se'] == 0 or not np.isfinite(st_['df']):
        return float('nan')
    tc = stats.t.ppf(1 - ALPHA, st_['df'])
    return float(abs(st_['diff']) + tc * st_['se'])


def analyse(a, b, label):
    w, pr = welch(a, b), paired(a, b)
    out = dict(label=label, n_a=len(a), n_b=len(b),
               mean_a=float(np.mean(a)), mean_b=float(np.mean(b)),
               sd_a=float(np.std(a, ddof=1)), sd_b=float(np.std(b, ddof=1)))
    for nm, st_ in (('welch', w), ('paired', pr)):
        out[nm] = dict(st_)
        out[nm]['ci90'] = ci(st_, 0.90)
        out[nm]['ci95'] = ci(st_, 0.95)
        out[nm]['tost'] = tost(st_, DELTA)
        out[nm]['achieved_equivalence_bound'] = achieved_bound(st_)
        out[nm]['p_two_sided'] = (float(2 * stats.t.sf(abs(st_['t']), st_['df']))
                                  if np.isfinite(st_.get('t', np.nan)) else float('nan'))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    abc = cells(load('rebuild/ABC/out/abc_metrics.csv'))
    t2 = cells(load('rebuild/ABC/out/t2/abc_metrics.csv'))

    res = dict(
        what='post-hoc, non-decisional interval and equivalence analysis',
        decides='NOTHING -- the pre-registered 2*sigma_hat rule is the only decision rule',
        sesoi_delta=DELTA, alpha=ALPHA, metric='S_alpha (Sm)', seeds=list(SEEDS),
        sources=['rebuild/ABC/out/abc_metrics.csv', 'rebuild/ABC/out/t2/abc_metrics.csv'],
        gaps={}, arm_sd={})

    # ---- per-arm standard deviations, every arm in both campaigns ----------
    for src, tab in (('ABC', abc), ('T2', t2)):
        for (arch, ep), arms in sorted(tab.items()):
            for arm, byseed in sorted(arms.items()):
                v = [byseed[s] for s in SEEDS if s in byseed]
                res['arm_sd']['%s|%s|%s|%s' % (src, arch, ep, arm)] = dict(
                    n=len(v), mean=float(np.mean(v)), sd=float(np.std(v, ddof=1)),
                    values={str(s): byseed[s] for s in SEEDS if s in byseed})

    # ---- the decisive gap and its neighbours -------------------------------
    plan = [('ABC', abc, 'C10', 'B'), ('ABC', abc, 'B', 'A2'), ('ABC', abc, 'A2', 'A0'),
            ('T2', t2, 'C10', 'CSHUF'), ('T2', t2, 'C10', 'CINV'),
            ('T2', t2, 'CSHUF', 'CINV'), ('T2', t2, 'C10', 'B')]
    for src, tab, hi, lo in plan:
        for (arch, ep), arms in sorted(tab.items()):
            if hi not in arms or lo not in arms:
                continue
            a = [arms[hi][s] for s in SEEDS]
            b = [arms[lo][s] for s in SEEDS]
            key = '%s|%s|%s|%s-%s' % (src, arch, ep, hi, lo)
            res['gaps'][key] = analyse(a, b, key)

    with open(os.path.join(OUT, 'diag_tost.json'), 'w') as fh:
        json.dump(res, fh, indent=2, sort_keys=True)

    # ---- readable report ---------------------------------------------------
    _p('=' * 78)
    _p('DIAG.1  TOST equivalence and intervals -- POST-HOC, DECIDES NOTHING')
    _p('SESOI delta = %.4f   alpha = %.2f   metric = S_alpha   n = 3 per arm' % (DELTA, ALPHA))
    _p('=' * 78)
    for key in sorted(res['gaps']):
        g = res['gaps'][key]
        _p('\n--- %s ---' % key)
        _p('  means   %.6f vs %.6f     sd  %.6f / %.6f' %
           (g['mean_a'], g['mean_b'], g['sd_a'], g['sd_b']))
        for nm in ('welch', 'paired'):
            s = g[nm]
            _p('  %-6s  delta %+.6f  se %.6f  df %.2f' % (nm, s['diff'], s['se'], s['df']))
            _p('          90%% CI [%+.6f, %+.6f]   95%% CI [%+.6f, %+.6f]'
               % (s['ci90'][0], s['ci90'][1], s['ci95'][0], s['ci95'][1]))
            _p('          TOST p = %s   equivalent at delta=%.3f: %s'
               % (('%.4f' % s['tost']['p_tost']) if np.isfinite(s['tost']['p_tost']) else 'nan',
                  DELTA, s['tost']['equivalent']))
            _p('          smallest delta this data could establish: %.6f'
               % s['achieved_equivalence_bound'])
        _p('  paired per-seed differences: %s'
           % ', '.join('%s %+.6f' % (k, v) for k, v in sorted(g['paired']['per_seed'].items())))
    _p('\nwrote %s' % os.path.join(OUT, 'diag_tost.json'))


if __name__ == '__main__':
    main()

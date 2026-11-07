#!/usr/bin/env python
"""REBUTTAL WS5' -- the pre-registered analysis, committed BEFORE any WS5' number exists.

Implements rebuild/REBUTTAL/PREREGISTRATION_WS5.md SS WS5.1 exactly. Reads ONLY
rebuild/ABC/out/ws5/abc_metrics.csv, written by abc_evaluate.py --tag ws5 once all 102
runs are verified. It refuses to run on a partial campaign: all runs are reported or
none, and there is no interim look.

Per contrast (C10-B total, C10-CSHUF direction, CSHUF-B concentration), on COD10K-test
S_alpha (primary) and NC4K (secondary):
  Welch 95% CI and 90% CI, TOST p at delta = 0.005; paired-by-seed 95% CI (secondary);
  the frozen ABC 2*sigma_hat / sign verdict for continuity, with sigma_hat pooled over
  {B, C10, CSHUF} and the sign rule scaled to n = 34 (>= 23/34, the smallest k whose
  binomial tail does not exceed 7/8's).
Outcome per contrast, from the Welch intervals:
  BENEFIT     95% CI lower bound > 0
  HARM        95% CI upper bound < 0
  EQUIVALENT  90% CI inside (-0.005, +0.005)
  UNRESOLVED  none of the above
BENEFIT/HARM and EQUIVALENT can hold at once (a precise effect smaller than 0.005).
Both flags are then reported, as "BENEFIT, smaller than 0.005" or "HARM, smaller than
0.005". Joint reading on the primary cell:
  C10-B BENEFIT and C10-CSHUF EQUIVALENT -> "concentration, not direction, helps downstream."
  all three EQUIVALENT (and no BENEFIT/HARM) -> "neither helps at +/-0.005."
  anything else -> reported as it falls.
No multiplicity correction; all contrasts are reported unadjusted.

Usage:
  .venv/bin/python rebuild/REBUTTAL/ws5_analyse.py [--no-log]
"""

import argparse
import csv
import os
import sys

import numpy as np
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import common as C                                            # noqa: E402

SRC = os.path.join(C.REPO, 'rebuild/ABC/out/ws5/abc_metrics.csv')
SEEDS = tuple(range(51, 85))
ARMS = ('B', 'C10', 'CSHUF')
CONTRASTS = (('C10', 'B', 'total targeting effect'),
             ('C10', 'CSHUF', 'direction effect, same shape'),
             ('CSHUF', 'B', 'concentration effect, same budget, no aim'))
DELTA = 0.005
SIGN_MIN = 23


def welch(a, b):
    na, nb = len(a), len(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    se = np.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = float(np.mean(a) - np.mean(b))
    t95, t90 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    p = max(stats.t.sf((d + DELTA) / se, df), stats.t.cdf((d - DELTA) / se, df))
    return dict(d=d, lo95=d - t95 * se, hi95=d + t95 * se, lo90=d - t90 * se, hi90=d + t90 * se, p=float(p), df=df)


def outcome(w):
    eq = w['lo90'] > -DELTA and w['hi90'] < DELTA
    if w['lo95'] > 0:
        return 'BENEFIT, smaller than 0.005' if eq else 'BENEFIT'
    if w['hi95'] < 0:
        return 'HARM, smaller than 0.005' if eq else 'HARM'
    return 'EQUIVALENT' if eq else 'UNRESOLVED'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    by = {}
    with open(SRC, newline='') as fh:
        for r in csv.DictReader(fh):
            if r['arch'] == 'SINet':
                by.setdefault(r['endpoint'], {}).setdefault(r['arm'], {})[int(r['seed'])] = float(r['Sm'])
    for ep in ('COD10K', 'NC4K'):
        for a in ARMS:
            got = sorted(by.get(ep, {}).get(a, {}))
            if got != list(SEEDS):
                raise SystemExit('WS5 HALT: %s %s has %d of %d seeds. All runs are reported or none.'
                                 % (ep, a, len(got), len(SEEDS)))
    M, T, primary = [], [], {}
    for ep in ('COD10K', 'NC4K'):
        x = {a: np.array([by[ep][a][s] for s in SEEDS]) for a in ARMS}
        sh = float(np.sqrt(sum(((v - v.mean()) ** 2).sum() for v in x.values()) / (len(ARMS) * (len(SEEDS) - 1))))
        M.append(('%s_sigma_hat' % ep, '%.6f (bar %.6f, df %d)' % (sh, 2 * sh, len(ARMS) * (len(SEEDS) - 1)),
                  'pooled over B, C10, CSHUF'))
        for a in ARMS:
            M.append(('%s_%s_mean_sd' % (ep, a), '%.6f / %.6f' % (x[a].mean(), x[a].std(ddof=1)), 'n = %d' % len(SEEDS)))
        for hi, lo, role in CONTRASTS:
            w = welch(x[hi], x[lo])
            dd = x[hi] - x[lo]
            se = dd.std(ddof=1) / np.sqrt(len(dd))
            t = stats.t.ppf(0.975, len(dd) - 1)
            pos = int((dd > 0).sum())
            sc = max(pos, len(dd) - pos)
            frozen = ('WITHIN NOISE' if abs(w['d']) <= 2 * sh else
                      'REAL EFFECT' if sc >= SIGN_MIN and w['d'] > 0 else
                      'REAL REGRESSION' if sc >= SIGN_MIN and w['d'] < 0 else 'INCONCLUSIVE')
            oc = outcome(w)
            if ep == 'COD10K':
                primary[(hi, lo)] = oc
            M.append(('%s_%s-%s' % (ep, hi, lo),
                      '%s | D %+.4f  W95 [%+.4f, %+.4f]  W90 [%+.4f, %+.4f]  TOST p %.4f | paired95 [%+.4f, %+.4f] | frozen-rule %s (sign %d/%d)'
                      % (oc, w['d'], w['lo95'], w['hi95'], w['lo90'], w['hi90'], w['p'],
                         dd.mean() - t * se, dd.mean() + t * se, frozen, sc, len(dd)),
                      role + ('' if ep == 'COD10K' else '; SECONDARY endpoint')))
    total, direction = primary[('C10', 'B')], primary[('C10', 'CSHUF')]
    if total.startswith('BENEFIT') and direction == 'EQUIVALENT':
        joint = 'concentration, not direction, helps downstream.'
    elif all(v == 'EQUIVALENT' for v in primary.values()):
        joint = 'neither helps at +/-0.005.'
    else:
        joint = 'reported as it falls: ' + '; '.join('%s-%s %s' % (h, l, v) for (h, l), v in primary.items())
    M.append(('joint_reading_primary', joint, 'PREREGISTRATION_WS5.md SS WS5.1'))
    print(C.log_block('REBUTTAL_WS5', '.venv/bin/python rebuild/REBUTTAL/ws5_analyse.py', M, thresholds=T,
                      notes='The PRE-REGISTERED analysis (PREREGISTRATION_WS5.md), committed before any WS5\' number existed. Standalone: never pooled with SE, whose verdicts stand. No multiplicity correction: three contrasts on two endpoints, reported unadjusted.',
                      write=not args.no_log))


if __name__ == '__main__':
    main()

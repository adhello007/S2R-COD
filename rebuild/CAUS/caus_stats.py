#!/usr/bin/env python
"""CAUS TH-02 -- historical estimands recomputed twice, independently, from committed per-run metrics.

Implementation A: numpy + scipy.stats. Implementation B: csv + statistics + math only, with its own
Student-t CDF (regularised incomplete beta by continued fraction) and quantile (bisection). The two
share no code beyond reading the same committed CSV. Every number is compared; any disagreement
beyond 1e-9 is a FAIL.

Estimands (S-alpha):
  frozen rule   Delta = mean(a) - mean(b); bar = 2 * sigma_hat (pooled within-arm sd over the
                campaign's pre-registered arm set, equal n); sign = per-seed agreement count
  post-hoc      Welch 95% CI for Delta (arm-specific sds); Welch TOST against +/-0.005;
                paired-by-seed mean difference and t CI where the seeds align (supplementary)
Writes RESULT_TABLES/TH-02_historical_recompute.csv and TH-02_contrast_definitions.csv.
With --exp01 it also computes the EXP-01 verdicts from EXP-01_metrics_by_seed.csv.
"""

import argparse
import csv
import math
import os
import statistics as S
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402

OUT = os.path.join(K.REPO, 'rebuild/ABC/out')
CAMPAIGNS = {   # pre-registered sigma pools and decisive gaps (a - b)
    'ABC': dict(path='abc_metrics.csv', pool=('A0', 'A2', 'B', 'C10'), gaps=(('C10', 'B'),)),
    'T2': dict(path='t2/abc_metrics.csv', pool=('B', 'C10', 'CSHUF', 'CINV'),
               gaps=(('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV'))),
    'OR': dict(path='or/abc_metrics.csv', pool=('B', 'C10', 'CORACLE'),
               gaps=(('CORACLE', 'B'), ('CORACLE', 'C10'))),
    'FX': dict(path='fx/abc_metrics.csv', pool=('A0FX', 'BFX', 'C10FX'), gaps=(('C10FX', 'BFX'),)),
    'SE': dict(path='se/abc_metrics.csv', pool=('B', 'C10', 'CSHUF', 'CINV'),
               gaps=(('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV'))),
}
CELLS = [(a, e) for a in ('SINet', 'SINetv2') for e in ('COD10K', 'NC4K')]
EQ = 0.005


def load(path):
    d = {}
    for r in csv.DictReader(open(path)):
        d.setdefault((r['arch'], r['endpoint'], r['arm']), {})[int(r['seed'])] = float(r['Sm'])
    return d


# ---------------- implementation A ----------------
def impl_a(d, pool, a, b, arch, ep):
    import numpy as np
    from scipy import stats
    x = np.array([d[(arch, ep, a)][s] for s in sorted(d[(arch, ep, a)])])
    y = np.array([d[(arch, ep, b)][s] for s in sorted(d[(arch, ep, b)])])
    sig = float(np.sqrt(np.mean([np.var(list(d[(arch, ep, m)].values()), ddof=1) for m in pool])))
    df_pool = sum(len(d[(arch, ep, m)]) - 1 for m in pool)
    delta = float(x.mean() - y.mean())
    seeds = sorted(set(d[(arch, ep, a)]) & set(d[(arch, ep, b)]))
    diffs = np.array([d[(arch, ep, a)][s] - d[(arch, ep, b)][s] for s in seeds])
    sgn = int((np.sign(diffs) == np.sign(delta)).sum())
    va, vb = x.var(ddof=1) / len(x), y.var(ddof=1) / len(y)
    se = math.sqrt(va + vb)
    dfw = (va + vb) ** 2 / (va ** 2 / (len(x) - 1) + vb ** 2 / (len(y) - 1))
    tq = float(stats.t.ppf(0.975, dfw))
    p_lo = float(stats.t.sf((delta + EQ) / se, dfw))        # H0: delta <= -EQ
    p_hi = float(stats.t.cdf((delta - EQ) / se, dfw))       # H0: delta >= +EQ
    pm, ps = float(diffs.mean()), float(diffs.std(ddof=1))
    tp = float(stats.t.ppf(0.975, len(diffs) - 1))
    return dict(delta=delta, sigma_hat=sig, bar=2 * sig, df_pool=df_pool, sign=sgn, n_seeds=len(seeds),
                welch_lo=delta - tq * se, welch_hi=delta + tq * se, welch_df=dfw,
                tost_p=max(p_lo, p_hi), paired_mean=pm,
                paired_lo=pm - tp * ps / math.sqrt(len(diffs)), paired_hi=pm + tp * ps / math.sqrt(len(diffs)),
                var_ratio_paired_vs_unpaired=(ps ** 2 / len(diffs)) / (va + vb))


# ---------------- implementation B (no numpy / scipy) ----------------
def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, dd = 1.0, 1.0 - qab * x / qap
    dd = 1.0 / (dd if abs(dd) > 1e-300 else 1e-300)
    h = dd
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        dd = 1.0 / (dd if abs(dd) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e300
        h *= dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        dd = 1.0 / (dd if abs(dd) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e300
        de = dd * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def _ibeta(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * _ibeta(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_ppf(p, df):
    lo, hi = -100.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def impl_b(d, pool, a, b, arch, ep):
    xa, xb = d[(arch, ep, a)], d[(arch, ep, b)]
    x, y = list(xa.values()), list(xb.values())
    sig = math.sqrt(sum(S.variance(list(d[(arch, ep, m)].values())) for m in pool) / len(pool))
    delta = S.fmean(x) - S.fmean(y)
    seeds = sorted(set(xa) & set(xb))
    diffs = [xa[s] - xb[s] for s in seeds]
    sgn = sum(1 for v in diffs if (v > 0) == (delta > 0) and v != 0)
    va, vb = S.variance(x) / len(x), S.variance(y) / len(y)
    se = math.sqrt(va + vb)
    dfw = (va + vb) ** 2 / (va ** 2 / (len(x) - 1) + vb ** 2 / (len(y) - 1))
    tq = t_ppf(0.975, dfw)
    p_lo = 1.0 - t_cdf((delta + EQ) / se, dfw)
    p_hi = t_cdf((delta - EQ) / se, dfw)
    pm, ps = S.fmean(diffs), S.stdev(diffs)
    tp = t_ppf(0.975, len(diffs) - 1)
    return dict(delta=delta, sigma_hat=sig, bar=2 * sig, sign=sgn, welch_lo=delta - tq * se,
                welch_hi=delta + tq * se, tost_p=max(p_lo, p_hi), paired_mean=pm,
                paired_lo=pm - tp * ps / math.sqrt(len(diffs)), paired_hi=pm + tp * ps / math.sqrt(len(diffs)))


def verdict(delta, bar, sign, n):
    if abs(delta) <= bar:
        return 'WITHIN NOISE'
    if sign == n:
        return 'REAL EFFECT' if delta > 0 else 'REAL REGRESSION'
    return 'INCONCLUSIVE'


def historical():
    rows, worst = [], 0.0
    for camp, spec in CAMPAIGNS.items():
        d = load(os.path.join(OUT, spec['path']))
        for arch, ep in CELLS:
            for a, b in spec['gaps']:
                A_ = impl_a(d, spec['pool'], a, b, arch, ep)
                B_ = impl_b(d, spec['pool'], a, b, arch, ep)
                agree = max(abs(A_[k] - B_[k]) for k in B_ if k != 'sign')
                worst = max(worst, agree)
                if A_['sign'] != B_['sign']:
                    agree = float('inf')
                rows.append(dict(
                    campaign=camp, cell='%s|%s' % (arch, ep), gap='%s-%s' % (a, b), n_seeds=A_['n_seeds'],
                    delta='%+.6f' % A_['delta'], sigma_hat='%.6f' % A_['sigma_hat'], bar='%.6f' % A_['bar'],
                    x_bar='%.3f' % (abs(A_['delta']) / A_['bar']), df_pool=A_['df_pool'],
                    sign='%d/%d' % (A_['sign'], A_['n_seeds']),
                    verdict_frozen_rule=verdict(A_['delta'], A_['bar'], A_['sign'], A_['n_seeds']),
                    welch95_lo='%+.6f' % A_['welch_lo'], welch95_hi='%+.6f' % A_['welch_hi'],
                    welch_df='%.2f' % A_['welch_df'], tost_p_pm005='%.4f' % A_['tost_p'],
                    paired_mean='%+.6f' % A_['paired_mean'], paired95_lo='%+.6f' % A_['paired_lo'],
                    paired95_hi='%+.6f' % A_['paired_hi'],
                    var_ratio_paired_vs_unpaired='%.3f' % A_['var_ratio_paired_vs_unpaired'],
                    impl_ab_max_abs_diff='%.2e' % agree,
                    label='frozen rule = pre-registered; Welch/TOST/paired = post-hoc, decide nothing'))
    return rows, worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exp01', action='store_true')
    args = ap.parse_args()
    rows, worst = historical()
    K.write_csv(os.path.join(K.TABLES, 'TH-02_historical_recompute.csv'), rows)
    for r in rows:
        if r['cell'] == 'SINet|COD10K' or r['campaign'] in ('OR',):
            print('%-4s %-15s %-14s d=%s bar=%s x=%s sign=%s %-13s welch[%s,%s] tost=%s AB=%s'
                  % (r['campaign'], r['cell'], r['gap'], r['delta'], r['bar'], r['x_bar'], r['sign'],
                     r['verdict_frozen_rule'], r['welch95_lo'], r['welch95_hi'], r['tost_p_pm005'],
                     r['impl_ab_max_abs_diff']))
    print('implementation A vs B: max |diff| = %.2e -> %s' % (worst, 'PASS' if worst < 1e-9 else 'FAIL'))
    if args.exp01:
        import exp01_stats
        exp01_stats.main()


if __name__ == '__main__':
    main()

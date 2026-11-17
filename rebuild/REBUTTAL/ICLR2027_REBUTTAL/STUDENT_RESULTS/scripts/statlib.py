"""Independent statistics for the dypE follow-up: pure Python/NumPy, no scipy.

Student-t CDF via the regularized incomplete beta function (continued fraction, Lentz's method);
quantiles by bisection. Every function here is cross-checked against scipy by the callers.
"""
import itertools
import math

import numpy as np


# ---------------------------------------------------------------- Student t
def _betacf(a, b, x, itmax=500, eps=1e-16):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def betainc_reg(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    bt = math.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc_reg(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_sf(t, df):
    return t_cdf(-t, df)


def t_ppf(q, df):
    lo, hi = -1e4, 1e4
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-14 * max(1.0, abs(mid)):
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- summaries
def mean_sd(x):
    x = np.asarray(x, dtype=np.float64)
    m = float(x.sum() / len(x))
    sd = math.sqrt(float(((x - m) ** 2).sum()) / (len(x) - 1))
    return m, sd


def paired(x, y, delta=0.005):
    """Paired analysis of D = x - y (same index = same seed)."""
    d = np.asarray(x, dtype=np.float64) - np.asarray(y, dtype=np.float64)
    n = len(d)
    m, sd = mean_sd(d)
    se = sd / math.sqrt(n)
    df = n - 1
    t95, t90 = t_ppf(0.975, df), t_ppf(0.95, df)
    tstat = m / se if se > 0 else float('nan')
    p = 2.0 * t_sf(abs(tstat), df) if se > 0 else float('nan')
    p_lo = t_sf((m + delta) / se, df)       # H0: D <= -delta
    p_hi = t_cdf((m - delta) / se, df)      # H0: D >= +delta
    ci90 = (m - t90 * se, m + t90 * se)
    return dict(n=n, mean=m, sd=sd, se=se, df=df, t=tstat, p=p,
                ci95=(m - t95 * se, m + t95 * se), ci90=ci90,
                upper_one_sided_95=m + t90 * se, lower_one_sided_95=m - t90 * se,
                p_tost=max(p_lo, p_hi), equivalent=(ci90[0] > -delta and ci90[1] < delta),
                smallest_delta=max(abs(ci90[0]), abs(ci90[1])),
                n_pos=int((d > 0).sum()), n_neg=int((d < 0).sum()), n_zero=int((d == 0).sum()))


def welch(x, y, delta=0.005):
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    nx, ny = len(x), len(y)
    mx, sx = mean_sd(x)
    my, sy = mean_sd(y)
    vx, vy = sx * sx / nx, sy * sy / ny
    se = math.sqrt(vx + vy)
    df = (vx + vy) ** 2 / (vx * vx / (nx - 1) + vy * vy / (ny - 1))
    d = mx - my
    t95, t90 = t_ppf(0.975, df), t_ppf(0.95, df)
    p_lo = t_sf((d + delta) / se, df)
    p_hi = t_cdf((d - delta) / se, df)
    return dict(mean=d, se=se, df=df, t=d / se, p=2.0 * t_sf(abs(d / se), df),
                ci95=(d - t95 * se, d + t95 * se), ci90=(d - t90 * se, d + t90 * se),
                upper_one_sided_95=d + t90 * se, p_tost=max(p_lo, p_hi),
                equivalent=(d - t90 * se > -delta and d + t90 * se < delta),
                smallest_delta=abs(d) + t90 * se)


def signflip_exact(d):
    """Two-sided exact sign-flip p for the mean of d (all 2^n sign vectors)."""
    d = np.asarray(d, np.float64)
    n = len(d)
    obs = abs(d.mean())
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
    stats_ = np.abs((signs * d).mean(axis=1))
    return float((stats_ >= obs - 1e-15).sum() / len(signs)), len(signs)


def _norm_cdf(z):
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def _norm_ppf(q):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _norm_cdf(mid) < q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def bootstrap_mean(d, n_boot, rng, level=0.95):
    """Percentile and BCa intervals for the mean of d (paired bootstrap over pairs)."""
    d = np.asarray(d, np.float64)
    n = len(d)
    idx = rng.integers(0, n, size=(n_boot, n))
    bs = d[idx].mean(axis=1)
    a2 = (1 - level) / 2
    pct = (float(np.quantile(bs, a2)), float(np.quantile(bs, 1 - a2)))
    theta = d.mean()
    prop = float((bs < theta).mean())
    prop = min(max(prop, 1.0 / (n_boot + 1)), 1 - 1.0 / (n_boot + 1))
    z0 = _norm_ppf(prop)
    jack = np.array([np.delete(d, i).mean() for i in range(n)])
    jm = jack.mean()
    num, den = ((jm - jack) ** 3).sum(), 6.0 * (((jm - jack) ** 2).sum()) ** 1.5
    acc = float(num / den) if den > 0 else 0.0
    out = []
    for q in (a2, 1 - a2):
        zq = _norm_ppf(q)
        adj = _norm_cdf(z0 + (z0 + zq) / (1 - acc * (z0 + zq)))
        out.append(float(np.quantile(bs, adj)))
    return dict(pct=pct, bca=tuple(out), z0=z0, acc=acc, n_boot=n_boot)


def permutation_two_group_exact(a, b):
    """Exact two-sided permutation p for mean(a) - mean(b) over all relabelings."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    pool = np.concatenate([a, b])
    na, n = len(a), len(a) + len(b)
    obs = abs(a.mean() - b.mean())
    tot = pool.sum()
    cnt = k = 0
    for comb in itertools.combinations(range(n), na):
        sa = pool[list(comb)].sum()
        diff = sa / na - (tot - sa) / (n - na)
        cnt += abs(diff) >= obs - 1e-15
        k += 1
    return cnt / k, k


def holm(ps):
    ps = [float('nan') if p is None else p for p in ps]
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    m = len(ps)
    adj = [0.0] * m
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i]))
        adj[i] = run
    return adj


def pooled_sd(groups):
    """Pooled within-group SD (ddof 1 per group), df = sum(n_g - 1)."""
    ss = dfs = 0.0
    for g in groups:
        g = np.asarray(g, np.float64)
        ss += float(((g - g.mean()) ** 2).sum())
        dfs += len(g) - 1
    return math.sqrt(ss / dfs), int(dfs)

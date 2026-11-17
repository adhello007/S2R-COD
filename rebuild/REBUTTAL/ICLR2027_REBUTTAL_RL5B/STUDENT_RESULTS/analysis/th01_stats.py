"""TH-01 -- statistical re-derivation, sensitivity and power (RL5B CW-01 / QA-01).

Everything here is computed from committed per-run metrics; nothing is typed in by hand.

Inputs (read-only):
  rebuild/ABC/out/se/abc_metrics.csv           per-run S_alpha, 8 seeds x 4 arms x 2 arch x 2 endpoints
  rebuild/ABC/out/{,se/,or/,fx/}abc_verdict.json  committed verdict-rule quantities
  rebuild/FinalPaper/AD-PCH-230926/table_tost_equivalence.tex   committed post-hoc TOST table
  rebuild/FinalPaper/AD-PCH-230926/figs/make_tost_table.py      source of welch_tost (exec'd, not re-implemented)
  AD-PCHGS-250926.tex                          tab:allcells (Appendix C)
  rebuild/SE/PREREGISTRATION_SE.md             SE sign rule (>= 7/8 seed-paired differences)

Outputs: RESULT_TABLES/TH01_*.{csv,md,tex}, EXPERIMENT_LOGS/TH01_stats.log

Run: .venv/bin/python th01_stats.py
"""
import ast
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from scipy import stats

import _repo as R

RNG_SEED = 20261109
DELTA = 0.005
ALPHA = 0.05
SE_ARMS = ('B', 'C10', 'CSHUF', 'CINV')
SE_SEEDS = (42, 43, 45, 46, 47, 48, 49, 50)
SE_MIN_SIGN = 7                      # PREREGISTRATION_SE.md SE.1, run as --min-sign 7
CELLS = [(a, e) for a in ('SINet', 'SINetv2') for e in ('COD10K', 'NC4K')]
GAPS = [('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV')]   # (hi, lo): Delta = hi - lo
NAME = {'SINet': 'SINet', 'SINetv2': 'SINet-v2'}
PAPER = os.path.join(R.REPO, 'rebuild', 'FinalPaper', 'AD-PCH-230926')
TOST_TEX = os.path.join(PAPER, 'table_tost_equivalence.tex')
TOST_PY = os.path.join(PAPER, 'figs', 'make_tost_table.py')
MANUSCRIPT = os.path.join(R.REPO, 'AD-PCHGS-250926.tex')
SIGMA_POSTED = 0.00345               # posted initial rebuttal, Part 1
POSTED = dict(p_at_0005=0.14, p_at_0142=1.00, mde80=0.0083)   # instruction file 5.TH-01.5 / posted text
LOG = []


def log(msg=''):
    LOG.append(msg)
    print(msg, flush=True)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


# ---------------------------------------------------------------- the repo's welch_tost, verbatim
def load_repo_welch_tost():
    """Exec ONLY the welch_tost function (and DELTA) from make_tost_table.py: importing the module
    would rewrite the committed table, so the function source is extracted with ast."""
    src = open(TOST_PY).read()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'welch_tost')
            or (isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'DELTA' for t in n.targets))
            or isinstance(n, (ast.Import, ast.ImportFrom)) and not any(
                getattr(a, 'name', '') == '_repo' or getattr(n, 'module', '') == '_repo' for a in n.names)]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), TOST_PY, 'exec'), ns)
    assert ns['DELTA'] == DELTA
    return ns['welch_tost']


# ---------------------------------------------------------------- data
def load_se():
    by = {c: {a: {} for a in SE_ARMS} for c in CELLS}
    raw = {c: {a: {} for a in SE_ARMS} for c in CELLS}
    with open(R.SE_METRICS) as f:
        for r in csv.DictReader(f):
            c = (r['arch'], r['endpoint'])
            by[c][r['arm']][int(r['seed'])] = float(r['Sm'])
            raw[c][r['arm']][int(r['seed'])] = r['Sm']
    for c in CELLS:
        for a in SE_ARMS:
            assert sorted(by[c][a]) == list(SE_SEEDS), (c, a, sorted(by[c][a]))
    return by, raw


def rule_quantities(cell_data, arms, min_sign):
    """abc_evaluate.py:296-328, re-expressed: pooled within-arm SD over ALL listed arms; sign count =
    seeds whose same-seed difference has the sign of Delta (exact zeros excluded)."""
    ss, df = 0.0, 0
    for a in arms:
        xs = [cell_data[a][s] for s in sorted(cell_data[a])]
        mu = sum(xs) / len(xs)
        ss += sum((x - mu) ** 2 for x in xs)
        df += len(xs) - 1
    sigma = math.sqrt(ss / df)
    out = dict(sigma_hat=sigma, df=df, gaps={})
    for hi, lo in GAPS:
        seeds = sorted(set(cell_data[hi]) & set(cell_data[lo]))
        d = np.mean([cell_data[hi][s] for s in seeds]) - np.mean([cell_data[lo][s] for s in seeds])
        paired = {s: cell_data[hi][s] - cell_data[lo][s] for s in seeds}
        cons = sum(1 for s in seeds if (paired[s] > 0) == (d > 0) and paired[s] != 0)
        if abs(d) <= 2 * sigma:
            v = 'WITHIN NOISE'
        elif d > 2 * sigma and cons >= min_sign:
            v = 'REAL EFFECT'
        elif d < -2 * sigma and cons >= min_sign:
            v = 'REAL REGRESSION'
        else:
            v = 'INCONCLUSIVE'
        out['gaps'][(hi, lo)] = dict(delta=float(d), consistent=cons, n=len(seeds), verdict=v,
                                     xbar=abs(d) / (2 * sigma))
    return out


# ---------------------------------------------------------------- step 2: reproduction
def reproduce(by, welch_tost):
    findings, ok_all = [], True
    log('## Step 2 -- reproduction of committed values')
    # (a) SE verdict JSON (unrounded floats) vs recomputation from the 6-dp CSV
    vj = json.load(open(R.SE_VERDICT))
    for (arch, ep) in CELLS:
        key = '%s|%s' % (arch, ep)
        cj = vj['verdicts'][key]
        rq = rule_quantities(by[(arch, ep)], SE_ARMS, SE_MIN_SIGN)
        ok = abs(rq['sigma_hat'] - cj['sigma_hat']) < 2e-6 and rq['df'] == cj['df'] == 28
        for hi, lo in GAPS:
            g = cj['gaps']['%s->%s' % (lo, hi)]
            m = rq['gaps'][(hi, lo)]
            ok &= abs(m['delta'] - g['delta']) < 2e-6 and m['verdict'] == g['verdict']
            ok &= g['sign_consistent'] == '%d/%d' % (m['consistent'], m['n'])
        log('  SE %-15s sigma_hat %.6f (json %.6f) df %d, 4 gaps delta/sign/verdict -> %s'
            % (key, rq['sigma_hat'], cj['sigma_hat'], rq['df'], 'MATCH' if ok else 'MISMATCH'))
        ok_all &= ok
    # (b) tab:allcells rows in the manuscript (4 dp / 2 dp / sign) for SE, and ABC/OR/FX from their JSONs
    tex = open(MANUSCRIPT).read()
    block = tex[tex.index(r'\label{tab:allcells}'):]
    block = block[:block.index(r'\end{tabular}')]
    rows = re.findall(r'^\s*(ABC|SE|OR|FX)?\s*&\s*(SINet(?:-v2)?) \$\\cdot\$ (COD10K|NC4K)\s*&[^&]*&[^&]*&'
                      r'\s*\$([+-]\d\.\d{4})\$\s*&\s*\$(\d\.\d{4})\$\s*&\s*\$(\d\.\d{2})\$\s*&\s*(\d)/(\d)', block, re.M)
    camp, parsed = None, []
    for r in rows:
        camp = r[0] or camp
        parsed.append((camp, r[1].replace('-v2', 'v2'), r[2], float(r[3]), float(r[4]), float(r[5]), int(r[6]), int(r[7])))
    assert len(parsed) == 16, len(parsed)
    gap_of = {'ABC': 'B->C10', 'SE': 'B->C10', 'OR': 'B->CORACLE', 'FX': 'BFX->C10FX'}
    path_of = {'ABC': 'abc_verdict.json', 'SE': 'se/abc_verdict.json', 'OR': 'or/abc_verdict.json',
               'FX': 'fx/abc_verdict.json'}
    for camp, arch, ep, d, bar, xbar, sc, n in parsed:
        vj2 = json.load(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', path_of[camp])))
        c = vj2['verdicts']['%s|%s' % (arch, ep)]
        g = c['gaps'][gap_of[camp]]
        sig = c['sigma_hat']
        got = (round(g['delta'], 4), round(2 * sig, 4), round(abs(g['delta']) / (2 * sig), 2))
        cons, nseed = (int(x) for x in g['sign_consistent'].split('/'))   # stored as "k/n"
        ok = (got == (d, bar, xbar)) and cons == sc and nseed == n == g['n_seeds']
        if not ok:
            findings.append('tab:allcells %s %s %s: printed (%+.4f, %.4f, %.2f, %d/%d) vs json (%+.4f, %.4f, %.2f, %d/%d)'
                            % (camp, arch, ep, d, bar, xbar, sc, n, got[0], got[1], got[2], cons, len(g['paired'])))
        ok_all &= ok
    log('  tab:allcells: 16/16 rows re-derived from abc_verdict.json variants -> %s'
        % ('MATCH' if not findings else 'MISMATCH (%d rows)' % len(findings)))
    for f_ in findings:
        log('    ' + f_)
    # (c) table_tost_equivalence.tex, all 16 rows, at printed precision
    ttex = open(TOST_TEX).read()
    trows = re.findall(r'^(SINet(?:-v2)?) & (COD10K|NC4K) & \$\\mathrm\{(\w+)\}-\\mathrm\{(\w+)\}\$ & \$([+-]\d\.\d{4})\$ & '
                       r'\$\[([+-]\d\.\d{4}), ([+-]\d\.\d{4})\]\$ & (?:\\textbf\{)?(\d\.\d{4})\}? & \$(\d\.\d{4})\$', ttex, re.M)
    assert len(trows) == 16, len(trows)
    nmis = 0
    for arch, ep, hi, lo, d, lo95, hi95, p, bound in trows:
        a = arch.replace('-v2', 'v2')
        seeds = sorted(set(by[(a, ep)][hi]) & set(by[(a, ep)][lo]))
        w = welch_tost([by[(a, ep)][hi][s] for s in seeds], [by[(a, ep)][lo][s] for s in seeds])
        mine = ('%+.4f' % w['d'], '%+.4f' % w['ci95'][0], '%+.4f' % w['ci95'][1], '%.4f' % w['p_tost'], '%.4f' % w['bound'])
        if mine != (d, lo95, hi95, p, bound):
            nmis += 1
            findings.append('TOST row %s %s %s-%s: printed %s vs recomputed %s' % (arch, ep, hi, lo, (d, lo95, hi95, p, bound), mine))
    neq = sum(1 for r in trows if float(r[7]) < 0.05)
    log('  table_tost_equivalence.tex: 16/16 rows recomputed -> %s; %d/16 reject at delta=0.005'
        % ('MATCH' if nmis == 0 else '%d MISMATCH' % nmis, neq))
    ok_all &= nmis == 0
    # (d) the headline primary-cell numbers quoted by the manuscript / reviewer / posted rebuttal
    c = by[('SINet', 'COD10K')]
    w = welch_tost([c['C10'][s] for s in SE_SEEDS], [c['B'][s] for s in SE_SEEDS])
    w2 = welch_tost([c['C10'][s] for s in SE_SEEDS], [c['CSHUF'][s] for s in SE_SEEDS])
    rq = rule_quantities(c, SE_ARMS, SE_MIN_SIGN)
    prim = dict(delta=w['d'], ci95=w['ci95'], df=w['df'], p_tost=w['p_tost'], p_tost_c10_cshuf=w2['p_tost'],
                sigma_hat=rq['sigma_hat'], bar=2 * rq['sigma_hat'], sign=rq['gaps'][('C10', 'B')]['consistent'])
    expect_ok = ('%+.4f' % prim['delta'] == '+0.0024' and '[%+.4f, %+.4f]' % prim['ci95'] == '[-0.0020, +0.0067]'
                 and '%.3f' % prim['p_tost'] == '0.101' and '%.3f' % prim['p_tost_c10_cshuf'] == '0.019'
                 and '%.4f' % prim['bar'] == '0.0069' and prim['sign'] == 6)
    log('  primary cell SINet/COD10K C10-B: delta %+.6f, Welch 95%% CI [%+.6f, %+.6f], df %.2f, TOST p %.4f; '
        'C10-CSHUF TOST p %.4f; sigma_hat %.6f, 2*sigma_hat %.6f, sign %d/8 -> %s'
        % (prim['delta'], prim['ci95'][0], prim['ci95'][1], prim['df'], prim['p_tost'], prim['p_tost_c10_cshuf'],
           prim['sigma_hat'], prim['bar'], prim['sign'], 'MATCH (+0.0024, [-0.0020,+0.0067], 0.101, 0.019, 0.0069, 6/8)'
           if expect_ok else 'MISMATCH'))
    ok_all &= expect_ok
    return ok_all, findings, prim


# ---------------------------------------------------------------- step 3/4: contrasts
def welch_full(a, b):
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = math.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = float(a.mean() - b.mean())
    t975, t95 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    p_tost = max(stats.t.sf((d + DELTA) / se, df), stats.t.cdf((d - DELTA) / se, df))
    p_two = 2 * stats.t.sf(abs(d) / se, df)
    return dict(d=d, se=se, df=df, ci95=(d - t975 * se, d + t975 * se), ci90=(d - t95 * se, d + t95 * se),
                p_tost=float(p_tost), p_two=float(p_two), smallest_delta=abs(d) + t95 * se)


def paired_full(a, b):
    x = np.asarray(a) - np.asarray(b)
    n = len(x)
    d, sd = float(x.mean()), float(x.std(ddof=1))
    se, df = sd / math.sqrt(n), n - 1
    t975, t95 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    p_tost = max(stats.t.sf((d + DELTA) / se, df), stats.t.cdf((d - DELTA) / se, df))
    return dict(d=d, se=se, df=df, ci95=(d - t975 * se, d + t975 * se), ci90=(d - t95 * se, d + t95 * se),
                p_tost=float(p_tost), p_two=float(2 * stats.t.sf(abs(d) / se, df)),
                r_seed=float(np.corrcoef(a, b)[0, 1]))


def label(w):
    det = w['ci95'][0] > 0 or w['ci95'][1] < 0
    eq = w['p_tost'] < ALPHA
    if det and eq:
        return 'detected and equivalent'
    if det:
        return 'detected'
    if eq:
        return 'equivalent'
    return 'not detected'


def holm(ps):
    order = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def contrasts(by):
    rows = []
    for arch, ep in CELLS:
        rq = rule_quantities(by[(arch, ep)], SE_ARMS, SE_MIN_SIGN)
        for hi, lo in GAPS:
            c = by[(arch, ep)]
            a = [c[hi][s] for s in SE_SEEDS]
            b = [c[lo][s] for s in SE_SEEDS]
            w, p = welch_full(a, b), paired_full(a, b)
            g = rq['gaps'][(hi, lo)]
            rows.append(dict(arch=NAME[arch], endpoint=ep, contrast='%s-%s' % (hi, lo), n_per_arm=8,
                             delta=w['d'], welch_se=w['se'], welch_df=w['df'],
                             ci95_lo=w['ci95'][0], ci95_hi=w['ci95'][1], ci90_lo=w['ci90'][0], ci90_hi=w['ci90'][1],
                             p_tost=w['p_tost'], p_two_sided=w['p_two'], smallest_equiv_delta=w['smallest_delta'],
                             label=label(w),
                             rule_2sigma=2 * rq['sigma_hat'], rule_xbar=g['xbar'], rule_sign='%d/8' % g['consistent'],
                             rule_verdict=g['verdict'],
                             paired_delta=p['d'], paired_ci95_lo=p['ci95'][0], paired_ci95_hi=p['ci95'][1],
                             paired_ci90_lo=p['ci90'][0], paired_ci90_hi=p['ci90'][1], paired_p_tost=p['p_tost'],
                             paired_p_two_sided=p['p_two'], paired_label=label(p), seed_correlation=p['r_seed']))
    for key, src in (('holm_p_two_sided', 'p_two_sided'), ('holm_p_tost', 'p_tost')):
        adj = holm(np.array([r[src] for r in rows]))
        for r, v in zip(rows, adj):
            r[key] = float(v)
    for r in rows:
        r['label_holm'] = ('detected' if r['holm_p_two_sided'] < ALPHA else 'not detected') if r['holm_p_tost'] >= ALPHA \
            else ('equivalent' if r['holm_p_two_sided'] >= ALPHA else 'detected and equivalent')
    return rows


# ---------------------------------------------------------------- step 5: rule sensitivity
def sim_rule(sds, n, deltas, draws, rng, min_signs=(7, 8), hi='C10', lo='B'):
    """Simulate the FULL SE rule: four arms, normal per-run outcomes with their own SDs, sigma_hat pooled
    over all four (df = 4(n-1)), Delta_hat = mean(hi)-mean(lo), seed-paired sign count. Arms independent
    within seed (Welch-consistent; the observed seed correlations are reported separately).
    Common random numbers across deltas."""
    z = {a: rng.standard_normal((draws, n)) * sds[a] for a in sds}
    ss = sum(((z[a] - z[a].mean(1, keepdims=True)) ** 2).sum(1) for a in sds)
    sigma = np.sqrt(ss / (len(sds) * (n - 1)))
    base = z[hi] - z[lo]
    out = {}
    for d in deltas:
        paired = base + d
        dhat = paired.mean(1)
        agree = ((paired > 0) == (dhat[:, None] > 0)).sum(1)
        res = {'clear_bar': float(np.mean(dhat > 2 * sigma))}
        for k in min_signs:
            res['real_effect_min%d' % k] = float(np.mean((dhat > 2 * sigma) & (agree >= k)))
        out[d] = res
    return out


def analytic_p(delta, sigma_bar, se):
    return float(stats.norm.sf((2 * sigma_bar - delta) / se))


def solve_mde(fn, target=0.8, lo=0.0, hi=0.03, it=40):
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        if fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def rule_sensitivity(by, rng):
    rows = []
    grid = (0.0025, 0.005, 0.0067, 0.0083, 0.0142)
    draws = 100_000
    log('## Step 5 -- sensitivity of the 2-sigma rule (C10-B), n = 8 per arm, 100,000 draws per delta')
    for arch, ep in CELLS:
        c = by[(arch, ep)]
        sds = {a: float(np.std([c[a][s] for s in SE_SEEDS], ddof=1)) for a in SE_ARMS}
        rq = rule_quantities(c, SE_ARMS, SE_MIN_SIGN)
        sig = rq['sigma_hat']
        se_pooled = sig * math.sqrt(2 / 8)                       # posted approximation
        se_arm = math.sqrt((sds['C10'] ** 2 + sds['B'] ** 2) / 8)   # same bar, arm-specific SE
        sim = sim_rule(sds, 8, grid, draws, rng)
        # MDE80 under each method (bisection; simulation re-uses a fixed CRN draw set)
        zfix = np.random.default_rng(RNG_SEED + 7)
        zz = {a: zfix.standard_normal((draws, 8)) * sds[a] for a in SE_ARMS}
        ss = sum(((zz[a] - zz[a].mean(1, keepdims=True)) ** 2).sum(1) for a in SE_ARMS)
        sigd = np.sqrt(ss / 28)
        base = zz['C10'] - zz['B']

        def p_sim(d, k):
            paired = base + d
            dh = paired.mean(1)
            if k == 0:
                return float(np.mean(dh > 2 * sigd))
            ag = ((paired > 0) == (dh[:, None] > 0)).sum(1)
            return float(np.mean((dh > 2 * sigd) & (ag >= k)))
        mde = dict(posted_approx=solve_mde(lambda d: analytic_p(d, sig, se_pooled)),
                   posted_approx_sigma00345=solve_mde(lambda d: analytic_p(d, SIGMA_POSTED, SIGMA_POSTED * math.sqrt(2 / 8))),
                   arm_specific_fixed_bar=solve_mde(lambda d: analytic_p(d, sig, se_arm)),
                   sim_bar_only=solve_mde(lambda d: p_sim(d, 0)),
                   sim_rule_7of8=solve_mde(lambda d: p_sim(d, 7)),
                   sim_rule_8of8=solve_mde(lambda d: p_sim(d, 8)))
        for d in grid:
            rows.append(dict(arch=NAME[arch], endpoint=ep, contrast='C10-B', true_delta=d,
                             sigma_hat=sig, bar=2 * sig, sd_B=sds['B'], sd_C10=sds['C10'], sd_CSHUF=sds['CSHUF'],
                             sd_CINV=sds['CINV'],
                             p_posted_approx=analytic_p(d, sig, se_pooled),
                             p_posted_approx_sigma00345=analytic_p(d, SIGMA_POSTED, SIGMA_POSTED * math.sqrt(2 / 8)),
                             p_arm_specific_fixed_bar=analytic_p(d, sig, se_arm),
                             p_sim_bar_only=sim[d]['clear_bar'], p_sim_rule_7of8=sim[d]['real_effect_min7'],
                             p_sim_rule_8of8=sim[d]['real_effect_min8'],
                             mc_se=math.sqrt(max(sim[d]['real_effect_min7'] * (1 - sim[d]['real_effect_min7']), 1e-12) / draws),
                             **{'mde80_' + k: v for k, v in mde.items()}))
        log('  %s/%s sd(B,C10,CSHUF,CINV) = %.5f %.5f %.5f %.5f; sigma_hat %.6f; MDE80: posted-approx %.4f, '
            'arm-specific %.4f, sim bar-only %.4f, sim rule 7/8 %.4f, sim rule 8/8 %.4f'
            % (arch, ep, sds['B'], sds['C10'], sds['CSHUF'], sds['CINV'], sig, mde['posted_approx'],
               mde['arm_specific_fixed_bar'], mde['sim_bar_only'], mde['sim_rule_7of8'], mde['sim_rule_8of8']))
    return rows


# ---------------------------------------------------------------- step 6: EQ power
def tost_power_sim(sd_hi, sd_lo, n, true_d, draws, rng):
    a = rng.standard_normal((draws, n)) * sd_hi + true_d
    b = rng.standard_normal((draws, n)) * sd_lo
    va, vb = a.var(1, ddof=1), b.var(1, ddof=1)
    se = np.sqrt(va / n + vb / n)
    df = (va / n + vb / n) ** 2 / ((va / n) ** 2 / (n - 1) + (vb / n) ** 2 / (n - 1))
    d = a.mean(1) - b.mean(1)
    t95 = stats.t.ppf(0.95, df)
    return float(np.mean((d - t95 * se > -DELTA) & (d + t95 * se < DELTA)))


def closed_form_n(sd1, sd2, true_d, power):
    za = stats.norm.ppf(1 - ALPHA)
    zb = stats.norm.ppf(1 - (1 - power) / 2) if true_d == 0 else stats.norm.ppf(power)
    return math.ceil((za + zb) ** 2 * (sd1 ** 2 + sd2 ** 2) / (DELTA - abs(true_d)) ** 2)


def power_analysis(by, rng):
    c = by[('SINet', 'COD10K')]
    sds = {a: float(np.std([c[a][s] for s in SE_SEEDS], ddof=1)) for a in SE_ARMS}
    pooled = math.sqrt((sds['B'] ** 2 + sds['C10'] ** 2) / 2)
    # one-sided 80% upper confidence bound on each SD (df = 7): a robustness column, not the design value
    up = math.sqrt(7 / stats.chi2.ppf(0.20, 7))
    rows, draws = [], 40_000
    log('## Step 6 -- EQ power (Welch TOST, delta = +/-0.005, alpha = 0.05), SINet/COD10K 8-seed SDs: '
        'B %.5f, C10 %.5f, CSHUF %.5f (pooled B,C10 = %.5f); %d draws per n' % (sds['B'], sds['C10'], sds['CSHUF'], pooled, draws))
    for contrast, lo in (('C10-B', 'B'), ('C10-CSHUF', 'CSHUF')):
        for sd_scale, tag in ((1.0, 'point'), (up, 'sd_upper80')):
            for true_d in (0.0, 0.0012, 0.0024):
                s1, s2 = sds['C10'] * sd_scale, sds[lo] * sd_scale
                curve = {}
                for n in range(4, 151):
                    curve[n] = tost_power_sim(s1, s2, n, true_d, draws, rng)
                    if curve[n] >= 0.92 and n > 6:
                        break
                n80 = next((n for n in sorted(curve) if curve[n] >= 0.80), None)
                n90 = next((n for n in sorted(curve) if curve[n] >= 0.90), None)
                rows.append(dict(contrast=contrast, sd_basis=tag, sd_C10=s1, sd_other=s2, true_delta=true_d,
                                 n80_welch_sim=n80, power_at_n80=curve.get(n80), n90_welch_sim=n90,
                                 power_at_n90=curve.get(n90),
                                 n80_closed_form=closed_form_n(s1, s2, true_d, 0.8),
                                 n90_closed_form=closed_form_n(s1, s2, true_d, 0.9),
                                 n80_closed_form_pooled_sd=closed_form_n(pooled * sd_scale, pooled * sd_scale, true_d, 0.8)
                                 if contrast == 'C10-B' else None,
                                 curve=json.dumps({k: round(v, 4) for k, v in curve.items()})))
                log('  %-9s %-10s true delta %.4f: n80 sim %s (closed %d), n90 sim %s (closed %d)'
                    % (contrast, tag, true_d, n80, closed_form_n(s1, s2, true_d, 0.8), n90, closed_form_n(s1, s2, true_d, 0.9)))
    return rows, sds


# ---------------------------------------------------------------- writers
def fmt(x, p=4):
    return ('%+.' + str(p) + 'f') % x


def write_csv(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ('%.6g' % v if isinstance(v, float) else v) for k, v in r.items()})


def write_contrasts_md(rows, prim, path):
    L = ['# TH-01 -- all sixteen eight-seed contrasts (S_alpha), Welch primary, seed-paired sensitivity',
         '', '*Generated by `analysis/th01_stats.py` from `rebuild/ABC/out/se/abc_metrics.csv`. Post hoc: '
         'the margin delta = 0.005 was chosen after the SE campaign; nothing here changes a pre-registered verdict.*',
         '', 'Labels: **detected** = Welch 95% CI excludes 0; **equivalent** = TOST p < 0.05 at +/-0.005 '
         '(90% CI inside the margin); **not detected** = neither. Both can hold at once ("detected and equivalent").',
         '', '| Arch | Endpoint | Contrast | Delta | Welch 95% CI | 90% CI | df | TOST p | Label | 2-sigma rule (x bar, sign, verdict) | Holm label |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %s | %s | [%s, %s] | [%s, %s] | %.1f | %.4f | %s | %.2f, %s, %s | %s |'
                 % (r['arch'], r['endpoint'], r['contrast'], fmt(r['delta']), fmt(r['ci95_lo']), fmt(r['ci95_hi']),
                    fmt(r['ci90_lo']), fmt(r['ci90_hi']), r['welch_df'], r['p_tost'], r['label'], r['rule_xbar'],
                    r['rule_sign'], r['rule_verdict'], r['label_holm']))
    L += ['', '## Seed-paired sensitivity (secondary; never substituted for Welch)', '',
          'Seeds are shared across arms, so each seed gives one paired difference. B redraws its 1000 images at '
          'every seed while C10, CSHUF and CINV use one fixed set, so a B-vs-C difference carries set-sampling '
          'variance that a C-vs-C difference does not; pairing removes seed effects common to both arms but '
          'cannot remove that asymmetry.', '',
          '| Arch | Endpoint | Contrast | paired Delta | paired 95% CI | paired 90% CI | paired TOST p | paired label | seed corr r |',
          '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %s | %s | [%s, %s] | [%s, %s] | %.4f | %s | %+.2f |'
                 % (r['arch'], r['endpoint'], r['contrast'], fmt(r['paired_delta']), fmt(r['paired_ci95_lo']),
                    fmt(r['paired_ci95_hi']), fmt(r['paired_ci90_lo']), fmt(r['paired_ci90_hi']), r['paired_p_tost'],
                    r['paired_label'], r['seed_correlation']))
    n_eq = sum(r['label'] in ('equivalent', 'detected and equivalent') for r in rows)
    n_det = sum(r['label'] in ('detected', 'detected and equivalent') for r in rows)
    n_nd = sum(r['label'] == 'not detected' for r in rows)
    n_eq_h = sum(r['label_holm'] in ('equivalent', 'detected and equivalent') for r in rows)
    n_det_h = sum(r['label_holm'] in ('detected', 'detected and equivalent') for r in rows)
    L += ['', '## Counts', '',
          '- Unadjusted: %d/16 equivalent, %d/16 detected, %d/16 not detected.' % (n_eq, n_det, n_nd),
          '- Holm-adjusted across the 16 (two-sided Welch p and TOST p separately): %d/16 equivalent, %d/16 detected.' % (n_eq_h, n_det_h),
          '- Primary cell (SINet, COD10K, C10-B): Delta %s, Welch 95%% CI [%s, %s], TOST p %.4f -> **%s**.'
          % (fmt(prim['delta']), fmt(prim['ci95'][0]), fmt(prim['ci95'][1]), prim['p_tost'],
             [r for r in rows if r['arch'] == 'SINet' and r['endpoint'] == 'COD10K' and r['contrast'] == 'C10-B'][0]['label'])]
    open(path, 'w').write('\n'.join(L) + '\n')


def write_main_table_tex(rows, path):
    lab = {'not detected': 'not detected', 'equivalent': 'equivalent', 'detected': 'detected',
           'detected and equivalent': 'detected, equiv.'}
    body = []
    for i, r in enumerate(rows):
        if i and i % 4 == 0:
            body.append(r'\midrule')
        cell = ('%s, %s' % (r['arch'], r['endpoint'])) if i % 4 == 0 else ''
        hi, lo = r['contrast'].split('-')
        body.append(r'%s & $\mathrm{%s}-\mathrm{%s}$ & $%s$ & $[%s, %s]$ & $[%s, %s]$ & %s & %s \\'
                    % (cell, hi, lo, fmt(r['delta']), fmt(r['ci95_lo']), fmt(r['ci95_hi']), fmt(r['ci90_lo']),
                       fmt(r['ci90_hi']), (r'\textbf{%.3f}' if r['p_tost'] < 0.05 else '%.3f') % r['p_tost'],
                       lab[r['label']]))
    tex = r"""%% Generated by analysis/th01_stats.py from rebuild/ABC/out/se/abc_metrics.csv -- do not edit by hand.
\begin{table}[t]
\caption{All sixteen eight-seed contrasts on $S_\alpha$. $\Delta$ is the difference of arm means
(eight seeds each); intervals are Welch. A contrast is \emph{detected} if its 95\% interval excludes
zero, and \emph{equivalent} if its 90\% interval lies inside $\pm0.005$ (TOST, bold $p<0.05$).
A contrast that is neither is not evidence of equivalence: it is a failure to detect an effect at this
precision. The margin was chosen after the experiments, and no entry changes a pre-registered verdict.}
\label{tab:ci_tost}
\begin{center}
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}llccccl@{}}
\toprule
Cell & Contrast & $\Delta$ & 95\% CI & 90\% CI & TOST $p$ & Label \\
\midrule
""" + '\n'.join(body) + r"""
\bottomrule
\end{tabular}
\end{center}
\end{table}
"""
    open(path, 'w').write(tex)


def main():
    rng = np.random.default_rng(RNG_SEED)
    head = subprocess.run(['git', '-C', R.REPO, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    log('# TH-01 statistical re-derivation (generated by analysis/th01_stats.py)')
    log('git HEAD %s; numpy %s, scipy %s; RNG seed %d' % (head, np.__version__, stats.__name__ and __import__('scipy').__version__, RNG_SEED))
    for p in (R.SE_METRICS, R.SE_VERDICT, TOST_TEX, TOST_PY, MANUSCRIPT):
        log('input %s sha256:%s' % (os.path.relpath(p, R.REPO), sha(p)))
    welch_tost = load_repo_welch_tost()
    by, _ = load_se()
    ok, findings, prim = reproduce(by, welch_tost)
    log('REPRODUCTION: %s' % ('PASS' if ok else 'FAIL -- see findings above'))

    rows = contrasts(by)
    os.makedirs(R.TABLES, exist_ok=True)
    write_csv(os.path.join(R.TABLES, 'TH01_contrasts.csv'), rows)
    write_contrasts_md(rows, prim, os.path.join(R.TABLES, 'TH01_contrasts.md'))
    write_main_table_tex(rows, os.path.join(R.TABLES, 'TH01_main_table.tex'))
    log('## Step 3/4 -- contrasts')
    for r in rows:
        log('  %-8s %-6s %-9s d %s CI95 [%s, %s] CI90 [%s, %s] TOST p %.4f -> %-24s | paired [%s, %s] p %.4f -> %s'
            % (r['arch'], r['endpoint'], r['contrast'], fmt(r['delta']), fmt(r['ci95_lo']), fmt(r['ci95_hi']),
               fmt(r['ci90_lo']), fmt(r['ci90_hi']), r['p_tost'], r['label'], fmt(r['paired_ci95_lo']),
               fmt(r['paired_ci95_hi']), r['paired_p_tost'], r['paired_label']))

    srows = rule_sensitivity(by, rng)
    write_csv(os.path.join(R.TABLES, 'TH01_rule_sensitivity.csv'), srows)
    prim_s = [r for r in srows if r['arch'] == 'SINet' and r['endpoint'] == 'COD10K']
    log('  primary cell, P(clear rule | delta):')
    for r in prim_s:
        log('    delta %.4f: posted-approx %.3f (sigma 0.00345: %.3f) | arm-specific %.3f | sim bar-only %.3f | '
            'sim rule 7/8 %.3f | sim rule 8/8 %.3f' % (r['true_delta'], r['p_posted_approx'], r['p_posted_approx_sigma00345'],
                                                      r['p_arm_specific_fixed_bar'], r['p_sim_bar_only'],
                                                      r['p_sim_rule_7of8'], r['p_sim_rule_8of8']))
    p5 = [r for r in prim_s if r['true_delta'] == 0.005][0]
    p142 = [r for r in prim_s if r['true_delta'] == 0.0142][0]
    log('  POSTED-FIGURE CHECK (rebuttal Part 1): "about 0.14 at 0.005" -> posted approximation gives %.3f; the full '
        'rule (arm SDs, 7/8 sign) gives %.3f. "almost surely at 0.0142" -> %.3f / %.3f. "80%% MDE about 0.008" -> %.4f / %.4f.'
        % (p5['p_posted_approx'], p5['p_sim_rule_7of8'], p142['p_posted_approx'], p142['p_sim_rule_7of8'],
           p5['mde80_posted_approx'], p5['mde80_sim_rule_7of8']))

    prows, sds = power_analysis(by, rng)
    write_csv(os.path.join(R.TABLES, 'TH01_power.csv'), prows)
    rec = [r for r in prows if r['contrast'] == 'C10-B' and r['sd_basis'] == 'point' and r['true_delta'] == 0.0024][0]
    log('RECOMMENDATION for EQ: n = %s per arm (smallest n with Welch-simulated TOST power >= 0.80 at true '
        'Delta = +0.0024, the observed value, using 8-seed SDs); closed form %d.' % (rec['n80_welch_sim'], rec['n80_closed_form']))
    json.dump(dict(reproduction_pass=ok, findings=findings, primary=dict(prim, ci95=list(prim['ci95'])),
                   eq_recommended_n=rec['n80_welch_sim'], eq_recommendation_basis='C10-B, point SDs, true delta 0.0024, power 0.80',
                   sds_primary=sds),
              open(os.path.join(R.TABLES, 'TH01_summary.json'), 'w'), indent=2)
    open(os.path.join(R.LOGS, 'TH01_stats.log'), 'w').write('\n'.join(LOG) + '\n')


if __name__ == '__main__':
    main()

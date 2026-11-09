"""EQ (EXP-01) pre-registered analysis -- prereg/EQ.md. Committed with the pre-registration, before any
EQ number exists. Run ONCE, after all 87 runs have verified.

Steps
  1. Completeness: every (arm, seed) in {B, C10, CSHUF} x {101..129} must pass rebuild/ABC/abc_train.verify_run
     and have complete COD10K/NC4K predictions. Otherwise the script stops, unless
     --allow-incomplete is given; that path is a DEVIATION, is labelled as such in every output, and
     analyses only seeds complete for all three arms.
  2. Scorer check: the committed scorer must reproduce Sa 0.717216 / MAE 0.074463 on Result/SINet/S2C.
  3. Score every run with the committed scorer (abc_evaluate.score), 6 dp -> RESULT_TABLES/EXP01_EQ_metrics.csv.
  4. Analysis exactly as EQ.4; decision sentence exactly as EQ.5.
Outputs: RESULT_TABLES/EXP01_EQ.{csv,md}, EXP01_EQ_summary.json, FIGURES/EXP01_forest.pdf,
EXPERIMENT_LOGS/EXP01_analysis.log.

Run: .venv/bin/python eq_analysis.py [--workers 16] [--allow-incomplete]
"""
import argparse
import csv
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

import _repo as R

ARMS = ('B', 'C10', 'CSHUF')
SEEDS = tuple(range(101, 130))
DELTA = 0.005
K_STAR = 20                    # prereg EQ.4: smallest k with P(Bin(29,1/2) >= k) <= 9/256
KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
CONTRASTS = (('C10', 'B', 'H1 (primary)'), ('C10', 'CSHUF', 'H1b (secondary)'))
LOG = []


def log(m=''):
    LOG.append(m)
    print(m, flush=True)


def _score(args):
    import abc_evaluate as E
    gt, pr = args
    return E.score(gt, pr)


def welch(a, b):
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = math.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = float(a.mean() - b.mean())
    t975, t95 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    p_tost = max(stats.t.sf((d + DELTA) / se, df), stats.t.cdf((d - DELTA) / se, df))
    return dict(delta=d, se=se, df=df, ci95=(d - t975 * se, d + t975 * se), ci90=(d - t95 * se, d + t95 * se),
                p_tost=float(p_tost), p_two=float(2 * stats.t.sf(abs(d) / se, df)))


def paired(a, b):
    x = np.asarray(a) - np.asarray(b)
    n = len(x)
    d, se = float(x.mean()), float(x.std(ddof=1)) / math.sqrt(n)
    df = n - 1
    t975, t95 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    p_tost = max(stats.t.sf((d + DELTA) / se, df), stats.t.cdf((d - DELTA) / se, df))
    return dict(delta=d, se=se, df=df, ci95=(d - t975 * se, d + t975 * se), ci90=(d - t95 * se, d + t95 * se),
                p_tost=float(p_tost))


def rule(data, seeds):
    """Manuscript 2-sigma rule with sigma pooled over B, C10, CSHUF; abc_evaluate sign definition; k* = 20
    (scaled with n if --allow-incomplete reduced n: smallest k with binomial tail <= 9/256)."""
    n = len(seeds)
    k = next(k for k in range(n + 1) if stats.binom.sf(k - 1, n, 0.5) <= 9 / 256) if n != 29 else K_STAR
    ss, df = 0.0, 0
    for a in ARMS:
        xs = np.array([data[a][s] for s in seeds])
        ss += float(((xs - xs.mean()) ** 2).sum())
        df += n - 1
    sig = math.sqrt(ss / df)
    out = dict(sigma_hat=sig, df=df, bar=2 * sig, k_star=k, gaps={})
    for hi, lo, _ in CONTRASTS:
        d = float(np.mean([data[hi][s] for s in seeds]) - np.mean([data[lo][s] for s in seeds]))
        pdiff = [data[hi][s] - data[lo][s] for s in seeds]
        cons = sum(1 for x in pdiff if (x > 0) == (d > 0) and x != 0)
        if abs(d) <= 2 * sig:
            v = 'WITHIN NOISE'
        elif d > 2 * sig and cons >= k:
            v = 'REAL EFFECT'
        elif d < -2 * sig and cons >= k:
            v = 'REAL REGRESSION'
        else:
            v = 'INCONCLUSIVE'
        out['gaps']['%s-%s' % (hi, lo)] = dict(delta=d, sign='%d/%d' % (cons, n), verdict=v, xbar=abs(d) / (2 * sig))
    return out


def decision(w, hi, lo):
    f = lambda x: '%+.4f' % x
    det = w['ci95'][0] > 0 or w['ci95'][1] < 0
    eq = w['p_tost'] < 0.05
    arm = {'C10-B': 'random', 'C10-CSHUF': 'shuffled'}['%s-%s' % (hi, lo)]
    if det:
        fav = hi if w['delta'] > 0 else lo
        s = ('The confirmatory campaign detects a difference of %s S_alpha (95%% CI [%s, %s]) in favour of %s.'
             % (f(w['delta']), f(w['ci95'][0]), f(w['ci95'][1]), fav))
        if eq:
            s += ' The difference is smaller than the +/-0.005 margin.'
        return 'iii (detected)' + (' + equivalent' if eq else ''), s
    if eq:
        return 'i (equivalent)', ('A separately pre-registered confirmatory campaign with 29 fresh seeds per arm '
                                  'establishes that targeted and %s allocation are equivalent within +/-0.005 S_alpha '
                                  'on the primary cell (Delta = %s, 90%% CI [%s, %s]).'
                                  % (arm, f(w['delta']), f(w['ci90'][0]), f(w['ci90'][1])))
    return 'ii (neither)', ('The confirmatory campaign neither detects an advantage nor establishes equivalence at '
                            '+/-0.005 (Delta = %s, 95%% CI [%s, %s]). Effects as large as %s are not excluded at '
                            'this precision.' % (f(w['delta']), f(w['ci95'][0]), f(w['ci95'][1]), f(w['ci95'][1])))


def holm(ps):
    order = np.argsort(ps)
    m, adj, run = len(ps), [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def se_campaign(ep):
    """SE campaign per-run S_alpha (committed CSV), for the secondary pooled analysis."""
    d = {a: {} for a in ARMS}
    for r in csv.DictReader(open(R.SE_METRICS)):
        if r['arch'] == 'SINet' and r['endpoint'] == ep and r['arm'] in ARMS:
            d[r['arm']][int(r['seed'])] = float(r['Sm'])
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--allow-incomplete', action='store_true')
    a = ap.parse_args()
    import abc_common as A
    import abc_train as T
    # 1. completeness
    missing, verify = [], {}
    for arm in ARMS:
        for s in SEEDS:
            ok, d = T.verify_run('SINet', arm, s)
            rid = A.runid('SINet', arm, s)
            preds_ok = all(os.path.isdir(os.path.join(R.REPO, A.pred_dir(rid, ep))) and
                           len(os.listdir(os.path.join(R.REPO, A.pred_dir(rid, ep)))) ==
                           len(os.listdir(os.path.join(R.REPO, 'Dataset', 'Test', ep, 'GT'))) for ep in ('COD10K', 'NC4K'))
            verify[rid] = d
            if not (ok and preds_ok):
                missing.append(rid)
    deviation = bool(missing)
    if missing and not a.allow_incomplete:
        raise SystemExit('EQ incomplete (%d runs): %s -- not analysed (prereg EQ.6)' % (len(missing), missing[:10]))
    seeds = [s for s in SEEDS if all(A.runid('SINet', arm, s) not in missing for arm in ARMS)]
    log('# EXP-01 EQ analysis (prereg/EQ.md). %s' % ('DEVIATION: incomplete, %d runs missing: %s' % (len(missing), missing)
                                                       if deviation else 'All 87 runs verified, predictions complete.'))
    # 2. scorer check
    import abc_evaluate as E
    anc = E.score(os.path.join(R.REPO, 'Dataset/Test/COD10K/GT'), os.path.join(R.REPO, 'Result/SINet/S2C'))
    assert abs(anc['Sm'] - 0.717216) <= 1e-5 and abs(anc['MAE'] - 0.074463) <= 1e-5, anc
    log('scorer check: Sa %.6f MAE %.6f -> PASS' % (anc['Sm'], anc['MAE']))
    # 3. score
    jobs = [(arm, s, ep) for arm in ARMS for s in seeds for ep in ('COD10K', 'NC4K')]
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(_score, [(os.path.join(R.REPO, 'Dataset/Test/%s/GT' % ep),
                                    os.path.join(R.REPO, A.pred_dir(A.runid('SINet', arm, s), ep))) for arm, s, ep in jobs]))
    rows = []
    for (arm, s, ep), m in zip(jobs, res):
        d = verify[A.runid('SINet', arm, s)]
        rows.append(dict(runid=A.runid('SINet', arm, s), arch='SINet', arm=arm, seed=s, endpoint=ep, n=m['n'],
                         n_appended=d.get('n_appended'), best_epoch=d.get('best_epoch'), wall_min=d.get('wall_min'),
                         **{k: '%.6f' % m[k] for k in KEYS}))
    with open(os.path.join(R.TABLES, 'EXP01_EQ_metrics.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # 4. analysis (from the 6-dp CSV, as written)
    summary = dict(deviation_incomplete=deviation, missing=missing, seeds=seeds, n_per_arm=len(seeds), endpoints={})
    table = []
    for ep in ('COD10K', 'NC4K'):
        data = {arm: {} for arm in ARMS}
        for r in rows:
            if r['endpoint'] == ep:
                data[r['arm']][r['seed']] = float(r['Sm'])
        sd = {arm: float(np.std([data[arm][s] for s in seeds], ddof=1)) for arm in ARMS}
        mean = {arm: float(np.mean([data[arm][s] for s in seeds])) for arm in ARMS}
        rq = rule(data, seeds)
        epd = dict(arm_mean=mean, arm_sd=sd, rule=rq, contrasts={})
        se_d = se_campaign(ep)
        for hi, lo, role in CONTRASTS:
            wv = welch([data[hi][s] for s in seeds], [data[lo][s] for s in seeds])
            pv = paired([data[hi][s] for s in seeds], [data[lo][s] for s in seeds])
            ws = welch([se_d[hi][s] for s in sorted(se_d[hi])], [se_d[lo][s] for s in sorted(se_d[lo])])
            wts = (1 / wv['se'] ** 2, 1 / ws['se'] ** 2)
            dp = (wts[0] * wv['delta'] + wts[1] * ws['delta']) / sum(wts)
            sep = 1 / math.sqrt(sum(wts))
            z95 = stats.norm.ppf(0.95)
            pooled = dict(delta=dp, se=sep, ci90=(dp - z95 * sep, dp + z95 * sep),
                          p_tost=float(max(stats.norm.sf((dp + DELTA) / sep), stats.norm.cdf((dp - DELTA) / sep))))
            code, sentence = decision(wv, hi, lo)
            key = '%s-%s' % (hi, lo)
            epd['contrasts'][key] = dict(role=role if ep == 'COD10K' else role + ' -- NC4K, secondary', welch=wv,
                                         paired_secondary=pv, pooled_EQ_SE_secondary=pooled, decision=code,
                                         sentence=sentence, rule=rq['gaps'][key])
            table.append(dict(endpoint=ep, contrast=key, role=epd['contrasts'][key]['role'], n_per_arm=len(seeds),
                              delta=wv['delta'], ci95_lo=wv['ci95'][0], ci95_hi=wv['ci95'][1], ci90_lo=wv['ci90'][0],
                              ci90_hi=wv['ci90'][1], welch_df=wv['df'], p_tost=wv['p_tost'], decision=code,
                              rule_2sigma=rq['bar'], rule_xbar=rq['gaps'][key]['xbar'], rule_sign=rq['gaps'][key]['sign'],
                              rule_verdict=rq['gaps'][key]['verdict'], paired_ci95_lo=pv['ci95'][0],
                              paired_ci95_hi=pv['ci95'][1], paired_p_tost=pv['p_tost'], pooled_EQ_SE_delta=dp,
                              pooled_ci90_lo=pooled['ci90'][0], pooled_ci90_hi=pooled['ci90'][1],
                              pooled_p_tost=pooled['p_tost']))
        summary['endpoints'][ep] = epd
    adj = holm([t['p_tost'] for t in table])
    for t, p in zip(table, adj):
        t['holm_p_tost_note'] = p
    with open(os.path.join(R.TABLES, 'EXP01_EQ.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys()))
        w.writeheader()
        for t in table:
            w.writerow({k: ('%.6g' % v if isinstance(v, float) else v) for k, v in t.items()})
    json.dump(summary, open(os.path.join(R.TABLES, 'EXP01_EQ_summary.json'), 'w'), indent=2, default=list)
    prim = summary['endpoints']['COD10K']['contrasts']['C10-B']
    f = lambda x: '%+.4f' % x
    md = ['# EXP-01 (EQ): confirmatory equivalence campaign -- results', '',
          '*Pre-registered in `prereg/EQ.md`; generated by `analysis/eq_analysis.py`.%s*'
          % (' DEVIATION: incomplete -- %d runs missing.' % len(missing) if deviation else ''), '',
          '**H1 (primary, SINet COD10K-test, C10 - B): decision %s.** %s' % (prim['decision'], prim['sentence']), '',
          '| Endpoint | Contrast | Role | n/arm | Delta | Welch 95% CI | Welch 90% CI | TOST p | decision | 2-sigma rule (x bar, sign, verdict) | paired 95% CI (secondary) | pooled EQ+SE 90% CI (secondary) |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for t in table:
        md.append('| %s | %s | %s | %d | %s | [%s, %s] | [%s, %s] | %.4f | %s | %.2f, %s, %s | [%s, %s] | [%s, %s] |'
                  % (t['endpoint'], t['contrast'], t['role'], t['n_per_arm'], f(t['delta']), f(t['ci95_lo']), f(t['ci95_hi']),
                     f(t['ci90_lo']), f(t['ci90_hi']), t['p_tost'], t['decision'], t['rule_xbar'], t['rule_sign'],
                     t['rule_verdict'], f(t['paired_ci95_lo']), f(t['paired_ci95_hi']), f(t['pooled_ci90_lo']), f(t['pooled_ci90_hi'])))
    for ep in ('COD10K', 'NC4K'):
        e = summary['endpoints'][ep]
        md.append('')
        md.append('%s arm means (SD): ' % ep + ', '.join('%s %.4f (%.4f)' % (arm, e['arm_mean'][arm], e['arm_sd'][arm]) for arm in ARMS)
                  + '; sigma-hat %.5f (df %d), bar %.4f, k* = %d.' % (e['rule']['sigma_hat'], e['rule']['df'], e['rule']['bar'], e['rule']['k_star']))
    md += ['', 'Holm-adjusted TOST p across the four TOSTs (note only): ' +
           ', '.join('%s/%s %.4f' % (t['endpoint'], t['contrast'], t['holm_p_tost_note']) for t in table)]
    open(os.path.join(R.TABLES, 'EXP01_EQ.md'), 'w').write('\n'.join(md) + '\n')
    # forest plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ys = list(range(len(table)))[::-1]
    for y, t in zip(ys, table):
        ax.plot([t['ci95_lo'], t['ci95_hi']], [y, y], color='0.35', lw=1)
        ax.plot([t['ci90_lo'], t['ci90_hi']], [y, y], color='0.1', lw=3)
        ax.plot(t['delta'], y, 'o', color='k', ms=4)
    ax.axvline(0, color='0.6', lw=0.8)
    for x in (-DELTA, DELTA):
        ax.axvline(x, color='0.6', lw=0.8, ls='--')
    ax.set_yticks(ys)
    ax.set_yticklabels(['%s, %s' % (t['endpoint'], t['contrast']) for t in table], fontsize=8)
    ax.set_xlabel(r'$\Delta S_\alpha$ (thick: 90% CI, thin: 95% CI; dashed: $\pm0.005$)', fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(R.FIGS, 'EXP01_forest.pdf'))
    log('H1: %s -- %s' % (prim['decision'], prim['sentence']))
    open(os.path.join(R.LOGS, 'EXP01_analysis.log'), 'w').write('\n'.join(LOG) + '\n')


def selftest():
    """Exercise the statistics on the committed SE campaign (seeds 42-50), never on EQ data: Welch must
    reproduce TH-01's primary-cell values and the k* formula must give SE's own 7 at n = 8."""
    d = se_campaign('COD10K')
    s = sorted(d['B'])
    w = welch([d['C10'][x] for x in s], [d['B'][x] for x in s])
    rq = rule(d, s)
    ok = ('%+.4f' % w['delta'] == '+0.0024' and '[%+.4f, %+.4f]' % w['ci95'] == '[-0.0020, +0.0067]'
          and '%.4f' % w['p_tost'] == '0.1009' and rq['k_star'] == 7)
    print('selftest on SE data: delta %+.6f CI95 [%+.4f, %+.4f] TOST p %.4f, k*(n=8) = %d -> %s'
          % (w['delta'], w['ci95'][0], w['ci95'][1], w['p_tost'], rq['k_star'], 'PASS' if ok else 'FAIL'))
    print('decision wording check:', decision(w, 'C10', 'B'))
    return ok


if __name__ == '__main__':
    os.makedirs(R.FIGS, exist_ok=True)
    import sys
    if '--selftest' in sys.argv:
        raise SystemExit(0 if selftest() else 1)
    main()

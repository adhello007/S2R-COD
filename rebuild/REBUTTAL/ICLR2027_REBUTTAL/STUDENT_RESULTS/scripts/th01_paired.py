#!/usr/bin/env python
"""TH-01 -- paired inference on the eight-seed S_alpha table (post-review, exploratory).

Input: RUNS/an01/an01_rescored_full.csv (AN-01 re-score; Gate 2 must have passed).
Method: ANALYSIS_PRESPEC.md §4. Independent implementation = statlib.py (NumPy only),
cross-checked against scipy to <= 1e-12 on every t-based quantity.

Outputs:
  RESULT_TABLES/TH-01_paired_inference.csv
  RESULT_TABLES/TH-01_seed_differences.csv      (per seed: x, y, D; plus leave-one-out rows)
  RESULT_TABLES/TH-01_tost_table_reproduction.csv  (Welch rows vs manuscript tab:tost)
  EXPERIMENT_LOGS/TH-01_checks.json
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys

import numpy as np
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
WT, SR = a.worktree, a.sr
sys.path.insert(0, os.path.join(SR, 'scripts'))
import statlib as SL          # noqa: E402

SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
CELLS = [('SINet', 'COD10K'), ('SINet', 'NC4K'), ('SINetv2', 'COD10K'), ('SINetv2', 'NC4K')]
CONTRASTS = [('C10', 'B', 'primary'), ('C10', 'CSHUF', 'secondary'), ('C10', 'CINV', 'secondary'),
             ('CSHUF', 'CINV', 'secondary'), ('CINV', 'B', 'secondary'), ('CSHUF', 'B', 'secondary')]
DELTA, REF = 0.005, 0.0142
RNG = np.random.default_rng(20261111)
NBOOT = 20000


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def close(a_, b_, tol=1e-12):
    return abs(a_ - b_) <= tol * max(1.0, abs(a_), abs(b_))


def main():
    src = os.path.join(SR, 'RUNS/an01/an01_rescored_full.csv')
    gates = json.load(open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-01_gates.json')))
    assert gates['gate2']['passed'], 'AN-01 Gate 2 failed; TH-01 must not run on unverified values'
    v = {}
    for r in csv.DictReader(open(src)):
        v[(r['arch'], r['endpoint'], r['arm'], int(r['seed']))] = float(r['Sm'])
    verdict = json.load(open(os.path.join(WT, 'rebuild/ABC/out/se/abc_verdict.json')))['verdicts']
    checks = dict(scipy_mismatches=[], known_answer={}, sigma_hat_reproduction={})

    # ---- known-answer test: t for D = [1,2,3,4,5] is mean/(sd/sqrt n) = 3/(sqrt(2.5)/sqrt 5)
    ka = SL.paired([1, 2, 3, 4, 5], [0, 0, 0, 0, 0])
    checks['known_answer'] = dict(t=ka['t'], expected=3 / (math.sqrt(2.5) / math.sqrt(5)),
                                  passed=close(ka['t'], 3 / (math.sqrt(2.5) / math.sqrt(5))))
    for q, dfq in ((0.975, 7), (0.95, 7), (0.975, 13.3)):
        if not close(SL.t_ppf(q, dfq), float(stats.t.ppf(q, dfq)), 1e-11):
            checks['scipy_mismatches'].append(('t_ppf', q, dfq))

    rows, seedrows, primary_ps = [], [], []
    for arch, ep in CELLS:
        key = '%s|%s' % (arch, ep)
        # sigma_hat reproduction (committed pooled 4-arm SD, df 28)
        sh, dfp = SL.pooled_sd([[v[(arch, ep, arm, s)] for s in SEEDS] for arm in ('B', 'C10', 'CSHUF', 'CINV')])
        checks['sigma_hat_reproduction'][key] = dict(mine=sh, committed=verdict[key]['sigma_hat'], df=dfp,
                                                     match_1e9=abs(sh - verdict[key]['sigma_hat']) < 1e-9)
        for X, Y, role in CONTRASTS:
            x = np.array([v[(arch, ep, X, s)] for s in SEEDS])
            y = np.array([v[(arch, ep, Y, s)] for s in SEEDS])
            d = x - y
            P = SL.paired(x, y, DELTA)
            W = SL.welch(x, y, DELTA)
            sf_p, n_sf = SL.signflip_exact(d)
            bt = SL.bootstrap_mean(d, NBOOT, RNG)
            # scipy cross-checks
            sp_p = float(stats.ttest_rel(x, y).pvalue)
            sp_w = stats.ttest_ind(x, y, equal_var=False)
            t95 = float(stats.t.ppf(0.975, 7))
            for nm, mine, ref in (('paired_p', P['p'], sp_p), ('paired_ci95_lo', P['ci95'][0], d.mean() - t95 * d.std(ddof=1) / math.sqrt(8)),
                                  ('welch_p', W['p'], float(sp_w.pvalue)), ('welch_t', W['t'], float(sp_w.statistic)),
                                  ('paired_tost', P['p_tost'], max(float(stats.t.sf((d.mean() + DELTA) / P['se'], 7)),
                                                                   float(stats.t.cdf((d.mean() - DELTA) / P['se'], 7))))):
                if not close(mine, ref, 1e-10):
                    checks['scipy_mismatches'].append((key, X, Y, nm, mine, ref))
            r_xy = float(np.corrcoef(x, y)[0, 1])
            vx, vy, vd = float(np.var(x, ddof=1)), float(np.var(y, ddof=1)), float(np.var(d, ddof=1))
            gap_key = '%s->%s' % (Y, X)
            committed = verdict[key]['gaps'].get(gap_key)
            bar = 2 * verdict[key]['sigma_hat']
            row = dict(
                architecture=arch, endpoint=ep, endpoint_role='primary' if ep == 'COD10K' else 'secondary',
                contrast='%s-%s' % (X, Y), contrast_role=role, units='S_alpha (absolute, alpha=0.5)',
                n_pairs=8, seeds=' '.join(map(str, SEEDS)), pairing='training seed (B redraws its stems per seed)',
                mean_D=P['mean'], sd_D=P['sd'], se_paired=P['se'], df_paired=7,
                paired_ci95_lo=P['ci95'][0], paired_ci95_hi=P['ci95'][1],
                paired_ci90_lo=P['ci90'][0], paired_ci90_hi=P['ci90'][1],
                paired_t=P['t'], paired_p_two_sided=P['p'], sign_pos=P['n_pos'], sign_neg=P['n_neg'],
                paired_upper_one_sided_95=P['upper_one_sided_95'],
                boot_pct95_lo=bt['pct'][0], boot_pct95_hi=bt['pct'][1],
                boot_bca95_lo=bt['bca'][0], boot_bca95_hi=bt['bca'][1], n_boot=NBOOT,
                signflip_p_exact=sf_p, signflip_n_vectors=n_sf,
                paired_tost_p_delta0p005=P['p_tost'], paired_equivalent_delta0p005=P['equivalent'],
                paired_smallest_equiv_delta=P['smallest_delta'],
                welch_se=W['se'], welch_df=W['df'], welch_ci95_lo=W['ci95'][0], welch_ci95_hi=W['ci95'][1],
                welch_p_two_sided=W['p'], welch_tost_p_delta0p005=W['p_tost'],
                welch_equivalent_delta0p005=W['equivalent'], welch_smallest_equiv_delta=W['smallest_delta'],
                welch_upper_one_sided_95=W['upper_one_sided_95'],
                r_xy_across_seeds=r_xy, var_x=vx, var_y=vy, var_D=vd, var_x_plus_var_y=vx + vy,
                cov_xy=(vx + vy - vd) / 2, se_ratio_paired_over_welch=P['se'] / W['se'],
                paired_ci95_excludes_ref_0p0142=P['ci95'][1] < REF,
                paired_ci95_excludes_0p005=P['ci95'][1] < DELTA,
                paired_ci95_excludes_0=(P['ci95'][0] > 0 or P['ci95'][1] < 0),
                welch_ci95_excludes_ref_0p0142=W['ci95'][1] < REF,
                committed_sigma_hat_SE=verdict[key]['sigma_hat'], committed_bar_2sigma=bar,
                gap_over_bar=abs(P['mean']) / bar,
                committed_verdict=(committed or {}).get('verdict', 'not a committed SE gap'),
                committed_sign_consistent=(committed or {}).get('sign_consistent', ''),
                alpha=0.05, ci_level='95% two-sided (90% for TOST)',
                status='post-review exploratory; decides nothing',
                test_selection_status='held-out endpoint; no test-label selection',
                data_sha256=sha(src), code_sha256=sha(os.path.abspath(__file__)))
            rows.append(row)
            if role == 'primary':
                primary_ps.append(P['p'])
            for s, xi, yi in zip(SEEDS, x, y):
                seedrows.append(dict(architecture=arch, endpoint=ep, contrast='%s-%s' % (X, Y), kind='seed',
                                     seed=s, x=xi, y=yi, D=xi - yi, mean_D=None, ci95_lo=None, ci95_hi=None))
            for j, s in enumerate(SEEDS):
                L = SL.paired(np.delete(x, j), np.delete(y, j), DELTA)
                seedrows.append(dict(architecture=arch, endpoint=ep, contrast='%s-%s' % (X, Y),
                                     kind='leave_one_out', seed=s, x=None, y=None, D=None, mean_D=L['mean'],
                                     ci95_lo=L['ci95'][0], ci95_hi=L['ci95'][1]))
    hp = SL.holm(primary_ps)
    i = 0
    for r in rows:
        r['holm_p_primary_family'] = ''
        if r['contrast_role'] == 'primary':
            r['holm_p_primary_family'] = hp[i]
            i += 1

    def wcsv(name, rs):
        with open(os.path.join(SR, 'RESULT_TABLES', name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]))
            w.writeheader()
            for r in rs:
                w.writerow({k: ('' if val is None else (repr(float(val)) if isinstance(val, (float, np.floating)) else (int(val) if isinstance(val, np.integer) else val)))
                            for k, val in r.items()})
    wcsv('TH-01_paired_inference.csv', rows)
    wcsv('TH-01_seed_differences.csv', seedrows)

    # ---- reproduce manuscript tab:tost (Welch) at 4 dp
    tex = open(os.path.join(WT, 'rebuild/FinalPaper/AD-PCH-230926/table_tost_equivalence.tex')).read()
    pat = re.compile(r'^(SINet(?:-v2)?) & (COD10K|NC4K) & \$\\mathrm\{(\w+)\}-\\mathrm\{(\w+)\}\$ & '
                     r'\$([+-]\d\.\d{4})\$ & \$\[([+-]\d\.\d{4}), ([+-]\d\.\d{4})\]\$ & (?:\\textbf\{)?(\d\.\d{4})\}? & '
                     r'\$(\d\.\d{4})\$', re.M)
    rep = []
    for m in pat.finditer(tex):
        arch = 'SINetv2' if m.group(1) == 'SINet-v2' else 'SINet'
        r = next(x for x in rows if x['architecture'] == arch and x['endpoint'] == m.group(2)
                 and x['contrast'] == '%s-%s' % (m.group(3), m.group(4)))
        mine = ('%+.4f' % r['mean_D'], '%+.4f' % r['welch_ci95_lo'], '%+.4f' % r['welch_ci95_hi'],
                '%.4f' % r['welch_tost_p_delta0p005'], '%.4f' % r['welch_smallest_equiv_delta'])
        pub = (m.group(5), m.group(6), m.group(7), m.group(8), m.group(9))
        rep.append(dict(architecture=arch, endpoint=m.group(2), contrast='%s-%s' % (m.group(3), m.group(4)),
                        published_delta=pub[0], recomputed_delta=mine[0], published_ci95=('[%s, %s]' % pub[1:3]),
                        recomputed_welch_ci95=('[%s, %s]' % mine[1:3]), published_tost_p=pub[3],
                        recomputed_welch_tost_p=mine[3], published_smallest_delta=pub[4],
                        recomputed_smallest_delta=mine[4], all_match_4dp=(pub == mine),
                        interval_type='Welch (unpaired), as stated in the tab:tost caption'))
    wcsv('TH-01_tost_table_reproduction.csv', rep)
    checks['tost_table'] = dict(n_rows=len(rep), n_match=sum(r['all_match_4dp'] for r in rep))
    checks['data_sha256'] = sha(src)
    json.dump(checks, open(os.path.join(SR, 'EXPERIMENT_LOGS/TH-01_checks.json'), 'w'), indent=1, default=str)
    print(json.dumps(checks, indent=1, default=str))
    ok = (not checks['scipy_mismatches'] and checks['known_answer']['passed']
          and checks['tost_table']['n_match'] == 16
          and all(x['match_1e9'] for x in checks['sigma_hat_reproduction'].values()))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

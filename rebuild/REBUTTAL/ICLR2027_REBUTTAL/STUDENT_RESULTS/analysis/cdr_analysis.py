"""CDR (EXP-02) pre-registered analysis -- prereg/CDR.md. Committed with the pre-registration, before any
CDR number exists. Run ONCE per architecture, after that architecture's 35 CDR runs have verified.

Steps
  1. Completeness: all 35 CDR runs of --arch verify (abc_train.verify_run) and have complete predictions; the
     references (B: SE seeds 42-50; CSHUF, C10, CINV: seeds 42, 43, 45) have predictions. Otherwise stop,
     unless --allow-incomplete (a DEVIATION, labelled everywhere).
  2. The AN-01 reproduction gate must have PASSED (EXPERIMENT_LOGS/AN01_reproduction_gate.json).
  3. Score boundary metrics (analysis/boundary_scorer.py: the manuscript's metrics_one) at thresholds
     0.4/0.5/0.6 and S_alpha etc. (committed scorer) on COD10K-test and NC4K, for every CDR and reference run.
  4. Primary analysis and decision rule exactly as CDR.4; secondary metrics with the same computations,
     reported only. Long-format CSV for the descriptive mixed models (analysis/mixed_models.py, analysis env).
Outputs: RESULT_TABLES/EXP02_<arch>_{per_run.csv,results.md,summary.json,long.csv},
FIGURES/EXP02_dose_response_<arch>.pdf.

Run: .venv/bin/python cdr_analysis.py --arch SINet|SINetv2 [--workers 32] [--allow-incomplete]
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
import boundary_scorer as BS

L1 = ['CDRL1P%d' % i for i in range(1, 6)]
LH = ['CDRLHP%d' % i for i in range(1, 6)]
CDR_SEEDS = {'CDRLU': (42, 43, 45, 46, 47), **{a: (42, 43, 45) for a in L1 + LH}}
REF_SEEDS = {'B': (42, 43, 45, 46, 47, 48, 49, 50), 'CSHUF': (42, 43, 45), 'C10': (42, 43, 45), 'CINV': (42, 43, 45)}
THRESH = (0.4, 0.5, 0.6)
ENDPOINTS = ('COD10K', 'NC4K')
SM_KEYS = ('Sm', 'wFm', 'MAE', 'meanEm')
PRIMARY = ('COD10K', 0.5, 'boundary_iou')


def _sm(args):
    import abc_evaluate as E
    return E.score(*args)


def level_of(arm):
    return 'LU' if arm == 'CDRLU' else 'L1' if arm in L1 else 'LH' if arm in LH else arm


def analyse(vals, label):
    """vals: {arm: {seed: value}} for one metric/endpoint/threshold. Returns the CDR.4 quantities."""
    am = {a: float(np.mean([vals[a][s] for s in CDR_SEEDS[a]])) for a in CDR_SEEDS}
    mean_B = float(np.mean([vals['B'][s] for s in REF_SEEDS['B']]))
    D = 0.5 * (mean_B + am['CDRLU'])
    ss, df = 0.0, 0
    for a, seeds in CDR_SEEDS.items():
        xs = np.array([vals[a][s] for s in seeds])
        ss += float(((xs - xs.mean()) ** 2).sum())
        df += len(xs) - 1
    sig = math.sqrt(ss / df)
    out = dict(metric=label, D=D, mean_B=mean_B, mean_LU=am['CDRLU'], sigma_hat=sig, df=df, bar=2 * sig,
               allocation_means=am, levels={})
    for L, arms in (('L1', L1), ('LH', LH)):
        ms = np.array([am[a] for a in arms])
        dL = float(ms.mean() - D)
        agree = int(sum(1 for m in ms if np.sign(m - D) == np.sign(dL) and m != D))
        bsd = float(ms.std(ddof=1))
        a_ = abs(dL) > 2 * sig
        b_ = agree >= 4
        c_ = bsd < abs(dL)
        out['levels'][L] = dict(delta=dL, xbar=abs(dL) / (2 * sig), perms_agree='%d/5' % agree,
                                between_perm_sd=bsd, a=a_, b=b_, c=c_, passed=bool(a_ and b_ and c_))
    p1, ph = out['levels']['L1'], out['levels']['LH']
    if p1['passed'] and ph['passed']:
        concl = ('concentration effect supported downstream' if np.sign(p1['delta']) == np.sign(ph['delta'])
                 else 'inconclusive (both levels pass with opposite signs)')
    elif p1['passed'] or ph['passed']:
        concl = 'concentration effect supported downstream'
    elif not p1['a'] and not ph['a']:
        concl = 'not supported'
    else:
        concl = 'inconclusive'
    out['conclusion'] = concl
    conc = [am[a] for a in L1 + LH]
    disp = [am['CDRLU']] + [vals['B'][s] for s in REF_SEEDS['B']]
    out['delta_C'] = float(np.mean(conc) - D)
    va, vb = np.var(conc, ddof=1), np.var(disp, ddof=1)
    se = math.sqrt(va / len(conc) + vb / len(disp))
    wdf = (va / len(conc) + vb / len(disp)) ** 2 / ((va / len(conc)) ** 2 / (len(conc) - 1) + (vb / len(disp)) ** 2 / (len(disp) - 1))
    dd = float(np.mean(conc) - np.mean(disp))
    t = stats.t.ppf(0.975, wdf)
    out['welch_units_reported'] = dict(delta=dd, ci95=(dd - t * se, dd + t * se), df=wdf, n_conc=len(conc), n_disp=len(disp))
    # sensitivity: CSHUF as L1 P0
    if 'CSHUF' in vals:
        ms6 = np.array([am[a] for a in L1] + [float(np.mean([vals['CSHUF'][s] for s in REF_SEEDS['CSHUF']]))])
        out['sensitivity_L1_with_CSHUF'] = dict(delta=float(ms6.mean() - D), between_perm_sd=float(ms6.std(ddof=1)))
    out['context_same_shape'] = {a: float(np.mean([vals[a][s] for s in REF_SEEDS[a]])) for a in ('C10', 'CSHUF', 'CINV') if a in vals}
    out['monotone_order'] = ' < '.join(k for k, _ in sorted((('D', D), ('L1', float(np.mean([am[a] for a in L1]))),
                                                            ('LH', float(np.mean([am[a] for a in LH])))), key=lambda x: x[1]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arch', required=True, choices=['SINet', 'SINetv2'])
    ap.add_argument('--workers', type=int, default=32)
    ap.add_argument('--allow-incomplete', action='store_true')
    a = ap.parse_args()
    import abc_common as A
    import abc_train as T
    gate = json.load(open(os.path.join(R.LOGS, 'AN01_reproduction_gate.json')))
    if gate.get('GATE') != 'PASS':
        raise SystemExit('AN-01 reproduction gate has not passed -- boundary scorer not validated')
    missing, verify = [], {}
    for arm, seeds in CDR_SEEDS.items():
        for s in seeds:
            ok, d = T.verify_run(a.arch, arm, s)
            verify[(arm, s)] = d
            rid = A.runid(a.arch, arm, s)
            if not ok or not all(os.path.isdir(os.path.join(R.REPO, A.pred_dir(rid, ep))) for ep in ENDPOINTS):
                missing.append(rid)
    for arm, seeds in REF_SEEDS.items():
        for s in seeds:
            rid = A.runid(a.arch, arm, s)
            if not all(os.path.isdir(os.path.join(R.REPO, A.pred_dir(rid, ep))) for ep in ENDPOINTS):
                missing.append(rid)
    if missing and not a.allow_incomplete:
        raise SystemExit('CDR %s incomplete (%d): %s' % (a.arch, len(missing), missing[:10]))
    runs = [(arm, s) for arm, seeds in list(CDR_SEEDS.items()) + list(REF_SEEDS.items()) for s in seeds
            if A.runid(a.arch, arm, s) not in missing]
    # boundary metrics
    bruns = [((arm, s, ep), os.path.join(R.REPO, A.pred_dir(A.runid(a.arch, arm, s), ep)), ep)
             for arm, s in runs for ep in ENDPOINTS]
    bagg, _ = BS.score_runs(bruns, THRESH, a.workers)
    # S_alpha family
    jobs = [(arm, s, ep) for arm, s in runs for ep in ENDPOINTS]
    with ProcessPoolExecutor(min(16, a.workers)) as ex:
        sres = list(ex.map(_sm, [(os.path.join(R.REPO, 'Dataset/Test/%s/GT' % ep),
                                  os.path.join(R.REPO, A.pred_dir(A.runid(a.arch, arm, s), ep))) for arm, s, ep in jobs]))
    sm = {k: v for k, v in zip(jobs, sres)}
    alloc_cov = {r['arm']: r for r in csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'cdr', 'cdr_allocations.csv')))}
    rows = []
    for arm, s in runs:
        d = verify.get((arm, s)) or T.verify_run(a.arch, arm, s)[1]
        for ep in ENDPOINTS:
            base = dict(arch=a.arch, arm=arm, level=level_of(arm), allocation=('B_s%d' % s if arm == 'B' else arm), seed=s,
                        endpoint=ep, n_appended=d.get('n_appended'),
                        n_eff_nominal=alloc_cov.get(arm, {}).get('n_eff_nominal', ''),
                        n_eff_induced=alloc_cov.get(arm, {}).get('n_eff_induced', ''),
                        fill_dist_mean=alloc_cov.get(arm, {}).get('fill_dist_mean', ''),
                        **{k: '%.6f' % sm[(arm, s, ep)][k] for k in SM_KEYS})
            for t in THRESH:
                m = bagg[((arm, s, ep), t)]
                rows.append(dict(base, thresh=t, boundary_iou='%.6f' % m['boundary_iou'], boundary_f='%.6f' % m['boundary_f'],
                                 iou='%.6f' % m['iou']))
    tag = a.arch
    with open(os.path.join(R.TABLES, 'EXP02_%s_per_run.csv' % tag), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(R.TABLES, 'EXP02_%s_long.csv' % tag), 'w', newline='') as fh:   # for mixed_models.py
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(r for r in rows if r['level'] in ('LU', 'L1', 'LH', 'B'))

    def vals_for(ep, t, metric):
        v = {}
        for r in rows:
            if r['endpoint'] == ep and float(r['thresh']) == t:
                v.setdefault(r['arm'], {})[int(r['seed'])] = float(r[metric])
        return v
    summary = dict(arch=a.arch, deviation_incomplete=bool(missing), missing=missing, analyses={})
    summary['analyses']['PRIMARY BIoU@0.5 COD10K'] = analyse(vals_for(*PRIMARY), 'boundary_iou@0.5 COD10K')
    for ep in ENDPOINTS:
        for t in THRESH:
            for metric in ('boundary_iou', 'boundary_f'):
                key = '%s@%.1f %s' % (metric, t, ep)
                if (ep, t, metric) != PRIMARY:
                    summary['analyses']['secondary ' + key] = analyse(vals_for(ep, t, metric), key)
        for metric in SM_KEYS:
            summary['analyses']['secondary %s %s' % (metric, ep)] = analyse(vals_for(ep, 0.5, metric), '%s %s' % (metric, ep))
    json.dump(summary, open(os.path.join(R.TABLES, 'EXP02_%s_summary.json' % tag), 'w'), indent=2, default=list)
    P = summary['analyses']['PRIMARY BIoU@0.5 COD10K']
    f = lambda x: '%+.4f' % x
    md = ['# EXP-02 (CDR) %s -- results' % a.arch, '',
          '*Pre-registered in `prereg/CDR.md`; generated by `analysis/cdr_analysis.py`.%s*'
          % (' DEVIATION: incomplete, %d runs missing.' % len(missing) if missing else ''), '',
          '**Primary (Boundary-IoU @0.5, COD10K-test): %s.**' % P['conclusion'], '',
          'D = %.4f (B %.4f over 8 seeds, LU %.4f over 5); sigma-hat %.5f (df %d), bar %.4f.' % (
              P['D'], P['mean_B'], P['mean_LU'], P['sigma_hat'], P['df'], P['bar']), '',
          '| Analysis | Level | Delta_L | x bar | perms agree | between-perm SD | (a) | (b) | (c) | conclusion |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for name, an in summary['analyses'].items():
        for L in ('L1', 'LH'):
            l = an['levels'][L]
            md.append('| %s | %s | %s | %.2f | %s | %.4f | %s | %s | %s | %s |' % (
                name, L, f(l['delta']), l['xbar'], l['perms_agree'], l['between_perm_sd'], l['a'], l['b'], l['c'],
                an['conclusion'] if L == 'LH' else ''))
    md += ['', 'Reported, not deciding (primary metric): Delta_C %s; Welch over units %s, 95%% CI [%s, %s] (%d vs %d units); '
           'L1 with CSHUF as P0: Delta %s; same-shape context C10/CSHUF/CINV means %s; ordering %s.'
           % (f(P['delta_C']), f(P['welch_units_reported']['delta']), f(P['welch_units_reported']['ci95'][0]),
              f(P['welch_units_reported']['ci95'][1]), P['welch_units_reported']['n_conc'], P['welch_units_reported']['n_disp'],
              f(P['sensitivity_L1_with_CSHUF']['delta']), {k: round(v, 4) for k, v in P['context_same_shape'].items()},
              P['monotone_order'])]
    open(os.path.join(R.TABLES, 'EXP02_%s_results.md' % tag), 'w').write('\n'.join(md) + '\n')
    # dose-response figure
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(8, 3), sharey=True)
    vv = vals_for(*PRIMARY)
    for ax, key in zip(axs, ('n_eff_nominal', 'n_eff_induced')):
        for arm in CDR_SEEDS:
            ys = [vv[arm][s] for s in CDR_SEEDS[arm]]
            x = float(alloc_cov[arm][key])
            ax.errorbar(x, np.mean(ys), yerr=np.std(ys, ddof=1), fmt='o', ms=4,
                        color={'LU': 'tab:blue', 'L1': 'tab:orange', 'LH': 'tab:red'}[level_of(arm)], capsize=2)
        ax.axhline(np.mean([vv['B'][s] for s in REF_SEEDS['B']]), color='0.4', ls='--', lw=0.8, label='B (8 seeds)')
        ax.set_xlabel({'n_eff_nominal': 'N_eff of quotas (manipulated)', 'n_eff_induced': 'N_eff of selected images (nearest centroid)'}[key], fontsize=8)
    axs[0].set_ylabel('Boundary-IoU @0.5, COD10K-test', fontsize=8)
    axs[0].legend(fontsize=7)
    fig.suptitle('%s: points = allocations (blue LU, orange L1, red LH); bars = seed SD' % a.arch, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(R.FIGS, 'EXP02_dose_response_%s.pdf' % tag))
    print('PRIMARY %s: %s' % (a.arch, P['conclusion']))


def selftest():
    """Exercise analyse() on synthetic values with a known answer -- never on CDR data."""
    rng = np.random.default_rng(1)
    def make(shift_conc, perm_sd):
        v = {}
        for arm, seeds in list(CDR_SEEDS.items()) + list(REF_SEEDS.items()):
            off = 0.0
            if arm in L1 + LH:
                off = shift_conc + rng.normal(0, perm_sd)
            v[arm] = {s: 0.30 + off + rng.normal(0, 0.003) for s in seeds}
        return v
    big = analyse(make(0.03, 0.002), 'synthetic large effect')['conclusion']
    none = analyse(make(0.0, 0.0), 'synthetic null')['conclusion']
    ok = big.startswith('concentration effect supported') and none == 'not supported'
    print('selftest: large effect ->', big, '| null ->', none, '->', 'PASS' if ok else 'FAIL')
    return ok


if __name__ == '__main__':
    os.makedirs(R.FIGS, exist_ok=True)
    import sys
    if '--selftest' in sys.argv:
        raise SystemExit(0 if selftest() else 1)
    main()

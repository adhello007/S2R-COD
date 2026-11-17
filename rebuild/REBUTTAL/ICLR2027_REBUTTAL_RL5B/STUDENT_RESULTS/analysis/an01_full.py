"""AN-01 stage 2 (EXPLORATORY / POST HOC): boundary metrics for all 64 eight-seed SE runs, both architectures.

Called by an01_boundary.py --stage full, which first requires the stage-1 reproduction gate to have passed.
Outputs (all labelled EXPLORATORY):
  RESULT_TABLES/AN01_boundary_8seed_per_run.csv   per run x endpoint x threshold: BIoU, BF, IoU
  RESULT_TABLES/AN01_boundary_8seed.csv / .md     rule applied with the SE campaign's own sigma-hat per metric
  RESULT_TABLES/AN01_long.csv                     regression input for mixed_models.py an01
  RESULT_TABLES/AN01_sinetv2_diagnostics.csv      per-arm SDs and minimum detectable effects, both architectures
  FIGURES/AN01_boundary_by_arm.pdf
"""
import csv
import json
import math
import os

import numpy as np
from scipy import stats

import _repo as R
import boundary_scorer as BS

ARMS = ('B', 'C10', 'CSHUF', 'CINV')
SEEDS = (42, 43, 45, 46, 47, 48, 49, 50)
ARCHS = ('SINet', 'SINetv2')
EPS = ('COD10K', 'NC4K')
THRESH = (0.4, 0.5, 0.6)
CONTRASTS = (('C10', 'B'), ('CINV', 'B'), ('CSHUF', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'))
OUTM = ('boundary_iou', 'boundary_f')
LABEL = 'EXPLORATORY / POST HOC -- decides nothing'


def rule(v, seeds, min_sign):
    ss, df = 0.0, 0
    for a in ARMS:
        xs = np.array([v[a][s] for s in seeds])
        ss += float(((xs - xs.mean()) ** 2).sum())
        df += len(xs) - 1
    sig = math.sqrt(ss / df)
    res = {}
    for hi, lo in CONTRASTS:
        d = float(np.mean([v[hi][s] for s in seeds]) - np.mean([v[lo][s] for s in seeds]))
        pdiff = [v[hi][s] - v[lo][s] for s in seeds]
        cons = sum(1 for x in pdiff if (x > 0) == (d > 0) and x != 0)
        if abs(d) <= 2 * sig:
            verdict = 'WITHIN NOISE'
        elif cons >= min_sign:
            verdict = 'REAL EFFECT' if d > 0 else 'REAL REGRESSION'
        else:
            verdict = 'INCONCLUSIVE'
        a, b = np.array([v[hi][s] for s in seeds]), np.array([v[lo][s] for s in seeds])
        se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        wdf = (a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) ** 2 / (
            (a.var(ddof=1) / len(a)) ** 2 / (len(a) - 1) + (b.var(ddof=1) / len(b)) ** 2 / (len(b) - 1))
        t = stats.t.ppf(0.975, wdf)
        res['%s-%s' % (hi, lo)] = dict(delta=d, bar=2 * sig, xbar=abs(d) / (2 * sig), sign='%d/%d' % (cons, len(seeds)),
                                      verdict=verdict, welch_ci95=(d - t * se, d + t * se))
    return sig, df, res


def run(workers, reuse=False):
    gate = json.load(open(os.path.join(R.LOGS, 'AN01_reproduction_gate.json')))
    if gate.get('GATE') != 'PASS':
        raise SystemExit('AN-01 reproduction gate has not passed')
    runs = [((arch, arm, s, ep), os.path.join(R.REPO, 'Result', 'ABC', '%s_%s_s%d' % (arch, arm, s), ep), ep)
            for arch in ARCHS for arm in ARMS for s in SEEDS for ep in EPS]
    missing = [k for k, p, _ in runs if not os.path.isdir(p)]
    runs = [r for r in runs if os.path.isdir(r[1])]
    if reuse:   # regenerate the tables from the committed per-run CSV (no re-scoring)
        agg = {}
        for r in csv.DictReader(open(os.path.join(R.TABLES, 'AN01_boundary_8seed_per_run.csv'))):
            agg[((r['arch'], r['arm'], int(r['seed']), r['endpoint']), float(r['thresh']))] = dict(
                n=int(r['n']), boundary_iou=float(r['boundary_iou']), boundary_f=float(r['boundary_f']), iou=float(r['iou']))
    else:
        agg, _ = BS.score_runs(runs, THRESH, workers)
    # covariates
    n_app = {r['runid']: int(r['n_appended']) for r in csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_runs.csv')))}
    se_out = os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se')
    c10 = set(open(os.path.join(se_out, 'abc_stems_C_a1.0.txt')).read().split())

    def stems(arm, s):
        f = {'B': 'abc_stems_B_s%d.txt' % s, 'C10': 'abc_stems_C_a1.0.txt', 'CSHUF': 'abc_stems_CSHUF.txt', 'CINV': 'abc_stems_CINV.txt'}[arm]
        return set(open(os.path.join(se_out, f)).read().split())
    jac = {(arm, s): len(stems(arm, s) & c10) / len(stems(arm, s) | c10) for arm in ARMS for s in SEEDS}
    per_run, long = [], []
    for (arch, arm, s, ep), _, _ in runs:
        for t in THRESH:
            m = agg[((arch, arm, s, ep), t)]
            per_run.append(dict(runid='%s_%s_s%d' % (arch, arm, s), arch=arch, arm=arm, seed=s, endpoint=ep, thresh=t,
                                n=m['n'], boundary_iou='%.6f' % m['boundary_iou'], boundary_f='%.6f' % m['boundary_f'],
                                iou='%.6f' % m['iou'], n_appended=n_app['%s_%s_s%d' % (arch, arm, s)],
                                jaccard_to_C10='%.4f' % jac[(arm, s)], label=LABEL))
            if t == 0.5:
                for metric in OUTM:
                    long.append(dict(arch=arch, arm=arm, seed=s, endpoint=ep, metric=metric, value=m[metric],
                                     concentrated=int(arm != 'B'), n_appended=n_app['%s_%s_s%d' % (arch, arm, s)],
                                     jaccard_to_C10=jac[(arm, s)]))
    for name, rows in (('AN01_boundary_8seed_per_run.csv', per_run), ('AN01_long.csv', long)):
        with open(os.path.join(R.TABLES, name), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    # verdicts at 8 seeds (SE's own sigma-hat, df 28, >= 7/8) and the 3-seed consistency check
    vt, diag_rows = [], []
    for arch in ARCHS:
        for ep in EPS:
            for t in THRESH:
                for metric in OUTM:
                    v = {a: {} for a in ARMS}
                    for r in per_run:
                        if r['arch'] == arch and r['endpoint'] == ep and r['thresh'] == t:
                            v[r['arm']][r['seed']] = float(r[metric])
                    sig, df, res = rule(v, SEEDS, 7)
                    for k, g in res.items():
                        vt.append(dict(arch=arch, endpoint=ep, thresh=t, metric=metric, contrast=k, n_seeds=8,
                                       sigma_hat=sig, df=df, delta=g['delta'], bar=g['bar'], xbar=g['xbar'], sign=g['sign'],
                                       verdict=g['verdict'], welch_ci95_lo=g['welch_ci95'][0], welch_ci95_hi=g['welch_ci95'][1],
                                       label=LABEL))
                    if t == 0.5:
                        sds = {a: float(np.std([v[a][s] for s in SEEDS], ddof=1)) for a in ARMS}
                        se_diff = sig * math.sqrt(2 / 8)
                        diag_rows.append(dict(arch=arch, endpoint=ep, metric=metric, sigma_hat=sig, **{'sd_' + a: sds[a] for a in ARMS},
                                              mde80_rule_approx=2 * sig + stats.norm.ppf(0.8) * se_diff,
                                              delta_C10_B=res['C10-B']['delta'], delta_CINV_B=res['CINV-B']['delta'], label=LABEL))
    with open(os.path.join(R.TABLES, 'AN01_boundary_8seed.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(vt[0].keys()))
        w.writeheader()
        for r in vt:
            w.writerow({k: ('%.6g' % x if isinstance(x, float) else x) for k, x in r.items()})
    with open(os.path.join(R.TABLES, 'AN01_sinetv2_diagnostics.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(diag_rows[0].keys()))
        w.writeheader()
        for r in diag_rows:
            w.writerow({k: ('%.6g' % x if isinstance(x, float) else x) for k, x in r.items()})
    # 3-seed consistency with the committed tab:boundary (diag_subgroups.json whole_set)
    committed = json.load(open(os.path.join(R.REPO, 'rebuild', 'DIAG', 'out', 'diag_subgroups.json')))['whole_set']
    cons = []
    for arch in ARCHS:
        v = {a: {} for a in ARMS}
        for r in per_run:
            if r['arch'] == arch and r['endpoint'] == 'COD10K' and r['thresh'] == 0.5:
                v[r['arm']][r['seed']] = float(r['boundary_iou'])
        sig3, _, res3 = rule(v, (42, 43, 45), 3)
        for k in ('C10-B', 'CINV-B'):
            c = committed['%s|boundary_iou' % arch]['gaps'][k]
            # per-run values are read back from the 6-dp CSV, so agreement is judged at the published precision
            # (2 dp in tab:boundary); the raw difference is reported beside it
            cons.append(dict(arch=arch, contrast=k, ratio_recomputed=res3[k]['xbar'], ratio_committed=c['ratio'],
                             abs_diff=abs(res3[k]['xbar'] - c['ratio']),
                             match=round(res3[k]['xbar'], 2) == round(c['ratio'], 2)))
    # markdown
    f = lambda x: '%+.4f' % x
    md = ['# AN-01: boundary metrics at eight seeds, both architectures -- %s' % LABEL, '',
          '*Generated by `analysis/an01_full.py` from the saved prediction maps of the 64 SE runs. Rule: the '
          "manuscript's 2-sigma rule with the SE campaign's own pooled sigma-hat per metric (B, C10, CSHUF, CINV; "
          'df = 28) and >= 7/8 seed-paired sign agreement. Nothing here re-decides a pre-registered verdict.*', '',
          '**Consistency with the submitted 3-seed table** (same scorer, seeds 42, 43, 45, COD10K, threshold 0.5): ' +
          '; '.join('%s %s %.2fx bar (committed %.2fx; |diff| %.1e from 6-dp rounding) %s' % (
              c['arch'], c['contrast'], c['ratio_recomputed'], c['ratio_committed'], c['abs_diff'],
              'MATCH at 2 dp' if c['match'] else 'MISMATCH') for c in cons), '',
          '| Arch | Endpoint | Thr | Metric | Contrast | Delta | bar (2 sigma-hat) | x bar | sign | verdict | Welch 95% CI |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in vt:
        if r['metric'] == 'boundary_iou' or r['thresh'] == 0.5:
            md.append('| %s | %s | %.1f | %s | %s | %s | %.4f | %.2f | %s | %s | [%s, %s] |' % (
                r['arch'], r['endpoint'], r['thresh'], r['metric'], r['contrast'], f(r['delta']), r['bar'], r['xbar'],
                r['sign'], r['verdict'], f(r['welch_ci95_lo']), f(r['welch_ci95_hi'])))
    md += ['', '## SINet-v2 diagnostics (descriptive only)', '',
           '| Arch | Endpoint | Metric | sigma-hat | SD B | SD C10 | SD CSHUF | SD CINV | MDE80 (rule, approx.) | Delta C10-B | Delta CINV-B |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in diag_rows:
        md.append('| %s | %s | %s | %.5f | %.5f | %.5f | %.5f | %.5f | %.4f | %s | %s |' % (
            r['arch'], r['endpoint'], r['metric'], r['sigma_hat'], r['sd_B'], r['sd_C10'], r['sd_CSHUF'], r['sd_CINV'],
            r['mde80_rule_approx'], f(r['delta_C10_B']), f(r['delta_CINV_B'])))
    md += ['', 'Runs scored: %d run x endpoint folders; missing: %s.' % (len(runs), missing or 'none'),
           'Covariates (pseudo-label count, Jaccard to the C10 set) are post-treatment; the regression is in '
           '`AN01_regression.md` and is not causal.']
    open(os.path.join(R.TABLES, 'AN01_boundary_8seed.md'), 'w').write('\n'.join(md) + '\n')
    json.dump(dict(consistency_3seed=cons, missing=missing, label=LABEL),
              open(os.path.join(R.TABLES, 'AN01_summary.json'), 'w'), indent=2)
    # figure
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8))
    for ax, arch in zip(axs, ARCHS):
        for i, arm in enumerate(ARMS):
            ys = [float(r['boundary_iou']) for r in per_run if r['arch'] == arch and r['arm'] == arm
                  and r['endpoint'] == 'COD10K' and r['thresh'] == 0.5]
            ax.plot([i] * len(ys), ys, '.', color='0.6', ms=4)
            ax.errorbar(i, np.mean(ys), yerr=np.std(ys, ddof=1), fmt='o', color='k', ms=4, capsize=3)
        ax.set_xticks(range(len(ARMS)))
        ax.set_xticklabels(ARMS)
        ax.set_title('%s, COD10K-test, BIoU@0.5 (8 seeds)' % arch, fontsize=8)
    fig.suptitle('AN-01 (exploratory): per-arm Boundary-IoU; dots = seeds, bars = mean +/- SD', fontsize=8)
    fig.tight_layout()
    os.makedirs(R.FIGS, exist_ok=True)
    fig.savefig(os.path.join(R.FIGS, 'AN01_boundary_by_arm.pdf'))
    print('AN-01 full: %d rows; 3-seed consistency %s' % (len(per_run), [c['match'] for c in cons]))

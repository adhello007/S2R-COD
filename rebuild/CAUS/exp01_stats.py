#!/usr/bin/env python
"""CAUS EXP-01 -- score the runs of record and apply PREREGISTRATION_EXP01.md §1 exactly.

Run of record (Addendum A1): for each queue script, the EARLIEST start whose run_record.json says
COMPLETE. Other starts are listed, never used. Historical B / C10 / CORACLE rows come from the committed
metrics (reproduced at 6 dp by reuse gate R5). New runs are scored with the committed scorer
(caus_score.primary -> abc_evaluate.score -> Eval/metrics.py), and each new run is spot-checked by the
independent S-measure on 200 images per endpoint.

Verdicts use BOTH statistics implementations of caus_stats.py (impl_a numpy/scipy, impl_b pure Python);
any disagreement beyond 1e-9 is a HALT. sigma_hat is pooled over the arms of the 7-arm analysis set that
have >= 2 seeds; contrasts use only seeds present in both arms; anything short of 3/3 is PARTIAL.
Writes RESULT_TABLES/EXP-01_metrics_by_seed.csv, EXP-01_comparisons.csv, EXP-01_runs_of_record.csv and
STUDENT_RESULTS/RESULT_TABLES/run_manifest.csv.
"""

import csv
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402
import caus_score as SC                                        # noqa: E402
import caus_stats as ST                                        # noqa: E402

import numpy as np                                             # noqa: E402

SEEDS = (42, 43, 45)
NEW = ('ORTOP10', 'ORTOP10SHUF', 'ORPROP', 'ORTOP5')
HIST = {'B': 'rebuild/ABC/out/abc_metrics.csv', 'C10': 'rebuild/ABC/out/abc_metrics.csv',
        'CORACLE': 'rebuild/ABC/out/or/abc_metrics.csv', 'CSHUF': 'rebuild/ABC/out/t2/abc_metrics.csv'}
POOL7 = ('B', 'C10', 'CORACLE', 'ORPROP', 'ORTOP10', 'ORTOP10SHUF', 'ORTOP5')
PRIMARY = (('ORTOP10', 'CORACLE', 'P1 shape at true-error aim'),
           ('ORTOP10', 'ORTOP10SHUF', 'P2 aim at the top-10 shape'),
           ('ORPROP', 'CORACLE', 'P3 flat shape at true-error aim (overlapping, J=0.5232)'),
           ('ORTOP5', 'CORACLE', 'P4 shape-plus-aim (never aim-isolated)'))
SECONDARY = tuple((a, b, 'secondary') for a in ('ORTOP10', 'ORPROP', 'ORTOP5', 'ORTOP10SHUF') for b in ('B', 'C10')
                  if not (a == 'ORTOP10SHUF' and b == 'C10'))
DISPLAY = {'ORTOP10': 'OR-TOP10', 'ORTOP10SHUF': 'OR-TOP10-SHUF', 'ORPROP': 'OR-PROP', 'ORTOP5': 'OR-TOP5',
           'B': 'B', 'C10': 'C10', 'CORACLE': 'CORACLE', 'CSHUF': 'CSHUF'}
METRICS = SC.METRICS


def runs_of_record():
    out, others = {}, []
    for arm in NEW:
        for s in SEEDS:
            scripts = glob.glob(os.path.join(K.RUNS_ROOT, '*_EXP01_SINet_%s_s%d' % (arm, s)))
            starts = sorted(glob.glob(os.path.join(scripts[0], '2*'))) if scripts else []
            chosen = None
            for d in starts:
                rp = os.path.join(d, 'run_record.json')
                rec = json.load(open(rp)) if os.path.isfile(rp) else dict(status='NO RECORD (running or killed)')
                row = dict(arm=arm, seed=s, run_dir=os.path.relpath(d, K.REPO), status=rec.get('status'))
                if chosen is None and rec.get('status') == 'COMPLETE':
                    chosen = (d, rec)
                    row['role'] = 'RUN OF RECORD'
                else:
                    row['role'] = 'not used' if chosen else 'earlier/incomplete start'
                others.append(row)
            if chosen:
                out[(arm, s)] = chosen
    return out, others


def _score_task(t):
    """Pool worker: committed scorer on one (run, endpoint) + independent S-measure on a fixed subset."""
    d, ep, pick = t
    gt = os.path.join(K.REPO, 'Dataset/Test', ep, 'GT')
    pred = os.path.join(d, 'pred', ep)
    m = SC.primary(gt, pred)
    x = np.array(SC.primary_per_image_sm(gt, pred, pick))
    y = np.array(SC.independent_dir(gt, pred, pick))
    return (d, ep), m, float(np.abs(x - y).max())


def score_new(rr, procs=8):
    from multiprocessing import Pool
    rows, checks = [], []
    rng = np.random.default_rng(0)
    tasks = []
    for (arm, s), (d, rec) in sorted(rr.items()):
        for ep in ('COD10K', 'NC4K'):
            names = sorted(os.listdir(os.path.join(K.REPO, 'Dataset/Test', ep, 'GT')))
            tasks.append((d, ep, [names[i] for i in sorted(rng.choice(len(names), 200, replace=False))]))
    with Pool(procs) as pool:
        res = {k: (m, dx) for k, m, dx in pool.map(_score_task, tasks, chunksize=1)}
    for (arm, s), (d, rec) in sorted(rr.items()):
        for ep in ('COD10K', 'NC4K'):
            m, dx = res[(d, ep)]
            checks.append(dict(arm=DISPLAY[arm], seed=s, endpoint=ep, n=200, max_abs_diff=dx))
            v = rec.get('verify', {})
            rows.append(dict(source='new (EXP-01)', arm=DISPLAY[arm], seed=s, endpoint=ep, n=m['n'],
                             **{k: '%.6f' % m[k] for k in METRICS}, n_appended=v.get('n_appended'),
                             best_epoch=v.get('best_epoch'), wall_min=v.get('wall_min'),
                             run_dir=os.path.relpath(d, K.REPO)))
    return rows, checks


def hist_rows():
    rows = []
    for arm, path in HIST.items():
        for r in csv.DictReader(open(os.path.join(K.REPO, path))):
            if r['arch'] == 'SINet' and r['arm'] == arm and int(r['seed']) in SEEDS:
                rows.append(dict(source='historical (reused, R1-R6 passed)' if arm != 'CSHUF' else 'historical (reference only)',
                                 arm=arm, seed=int(r['seed']), endpoint=r['endpoint'], n=r['n'],
                                 **{k: r[k] for k in METRICS}, n_appended='', best_epoch='', wall_min='',
                                 run_dir=os.path.join('Result/ABC', 'SINet_%s_s%s' % (arm, r['seed']))))
    return rows


def verdicts(rows):
    out, worst = [], 0.0
    for ep in ('COD10K', 'NC4K'):
        d = {}
        for r in rows:
            if r['endpoint'] == ep:
                key = next(k for k, v in DISPLAY.items() if v == r['arm'])
                d.setdefault(('SINet', ep, key), {})[int(r['seed'])] = float(r['Sm'])
        pool = tuple(a for a in POOL7 if len(d.get(('SINet', ep, a), {})) >= 2)
        new_pool = tuple(a for a in NEW if len(d.get(('SINet', ep, a), {})) >= 2)
        for a, b, label in PRIMARY + SECONDARY:
            if ('SINet', ep, a) not in d or ('SINet', ep, b) not in d:
                out.append(dict(endpoint=ep, contrast='%s - %s' % (DISPLAY[a], DISPLAY[b]), role=label,
                                status='INFEASIBLE (arm missing)'))
                continue
            common = sorted(set(d[('SINet', ep, a)]) & set(d[('SINet', ep, b)]))
            if len(common) < 2 or len(d[('SINet', ep, a)]) < 2 or len(d[('SINet', ep, b)]) < 2:
                out.append(dict(endpoint=ep, contrast='%s - %s' % (DISPLAY[a], DISPLAY[b]), role=label,
                                status='INFEASIBLE (< 2 seeds)'))
                continue
            dd = {k: {s: v for s, v in vals.items() if s in common} if k[2] in (a, b) else vals for k, vals in d.items()}
            A_ = ST.impl_a(dd, pool, a, b, 'SINet', ep)
            B_ = ST.impl_b(dd, pool, a, b, 'SINet', ep)
            agree = max(abs(A_[k] - B_[k]) for k in B_ if k != 'sign')
            if A_['sign'] != B_['sign'] or agree > 1e-9:
                raise SystemExit('EXP01 STATS HALT: implementations disagree on %s-%s %s' % (a, b, ep))
            worst = max(worst, agree)
            sig_new = float(np.sqrt(np.mean([np.var(list(d[('SINet', ep, m)].values()), ddof=1) for m in new_pool]))) \
                if new_pool else float('nan')
            n = len(common)
            out.append(dict(
                endpoint=ep, contrast='%s - %s' % (DISPLAY[a], DISPLAY[b]), role=label,
                status='COMPLETE' if n == 3 else 'PARTIAL (%d/3 seeds)' % n,
                n_seeds=n, delta='%+.6f' % A_['delta'], sigma_hat_pool7='%.6f' % A_['sigma_hat'],
                bar='%.6f' % A_['bar'], df_pool=A_['df_pool'], x_bar='%.3f' % (abs(A_['delta']) / A_['bar']),
                sign='%d/%d' % (A_['sign'], n), verdict=ST.verdict(A_['delta'], A_['bar'], A_['sign'], n),
                largest_effect_bar_could_miss='%.6f' % A_['bar'],
                sigma_hat_new_arms_only='%.6f' % sig_new, sigma_hat_OR_committed='see TH-02 (OR SINet bar 0.006130)',
                welch95='[%+.4f, %+.4f]' % (A_['welch_lo'], A_['welch_hi']),
                paired95_df2_unstable='[%+.4f, %+.4f]' % (A_['paired_lo'], A_['paired_hi']),
                impl_ab_max_abs_diff='%.1e' % agree,
                note=('decides' if ep == 'COD10K' and label.startswith('P') else 'reported, never decides')
                + ('; endpoint-label-leaky arm(s): COD10K-test not an unbiased endpoint' if ep == 'COD10K' else '')))
    return out, worst


def manifest(rows, rr):
    sha = lambda p: K.sha256(os.path.join(K.REPO, p)) if os.path.isfile(os.path.join(K.REPO, p)) else ''  # noqa: E731
    splits = {r['split']: r['content_sha256'] for r in csv.DictReader(open(os.path.join(K.TABLES, 'AN-05_split_audit.csv')))
              if r['content_sha256']}
    qm = {r['arm']: r for r in csv.DictReader(open(os.path.join(K.TABLES, 'EXP-01_quota_manifests.csv')))}
    hist = {r['runid']: r for r in csv.DictReader(open(os.path.join(K.TABLES, 'EXP-01_historical_runs.csv')))}
    code = sha('rebuild/CAUS/exp01_run.py')
    out = []
    for r in rows:
        if r['endpoint'] != 'COD10K':
            continue
        arm, s = r['arm'], int(r['seed'])
        key = next(k for k, v in DISPLAY.items() if v == arm)
        q = qm.get(arm, {})
        new = r['source'].startswith('new')
        rec = rr.get((key, s), (None, {}))[1] if new else {}
        h = hist.get('SINet_%s_s%d' % (key, s), {})
        out.append(dict(
            campaign='EXP-01' if new else {'B': 'ABC', 'C10': 'ABC', 'CORACLE': 'OR', 'CSHUF': 'T2'}[key],
            arm=arm, allocation_shape=q.get('allocation_shape', 'uniform random draw' if key == 'B' else ''),
            alignment=q.get('alignment', 'none' if key == 'B' else ''), model='SINet', generator='LAKE-RED (offline, fixed foregrounds)',
            seed=s, endpoint='COD10K (primary); NC4K (secondary)',
            train_split_sha=splits.get('auth', ''), target_split_sha=splits.get('tgt', ''),
            eval_split_sha='COD10K %s; NC4K %s' % (splits.get('test', '')[:16], splits.get('nc4k', '')[:16]),
            calibration_split_sha='none (no disjoint calibration set; see AN-05)',
            generator_version_sha='renders verified against E0 manifest (R3)', foreground_manifest_sha=splits.get('raw', ''),
            render_pool_sha=splits.get('local', ''), quota_file_sha=q.get('quota_sha256', ''),
            selected_inject_sha=q.get('stems_sha256', 'per-seed B draw (committed abc_stems_B_s%d.txt)' % s),
            config_sha=code if new else 'historical driver command line (abc_commands.txt)',
            git_sha=(rec.get('git', '') if new else h.get('run_commit', '')),
            round1_checkpoint_sha='round-1 checkpoints are overwritten by round 2 in this trainer (not retained)',
            round2_checkpoint_sha=(rec.get('tea_best_sha256', '') if new else h.get('tea_best_sha256', '')),
            metric_code_sha=sha('Eval/metrics.py'), mask_qc_report='RESULT_TABLES/AN-03_coverage_and_qc.csv',
            checkpoint_rule='Tea_epoch_best.pth of the final round, CAMO-250 MAE', steps_per_epoch=253, epochs='40 x 2 rounds',
            source_count=4447, target_count=4040, injection_count=1000,
            pseudolabel_count=(rec.get('verify', {}).get('n_appended', '') if new else ''),
            primary_metric='S-alpha (alpha=0.5) = %s' % r['Sm'], raw_prediction_path=os.path.join(r['run_dir'], 'COD10K'),
            raw_log_path=(os.path.join(os.path.relpath(rr[(key, s)][0], K.REPO), 'logs/train.log') if new
                          else 'Snapshot/ABC/SINet_%s_s%d/training_log.log' % (key, s)),
            metric_result_path='RESULT_TABLES/EXP-01_metrics_by_seed.csv',
            status='VERIFIED' if new else 'ORIGINAL VERIFIED (R5)',
            oracle_score_source=q.get('oracle_score_source', 'not-applicable'),
            eligible_capacity_policy=q.get('eligible_capacity_policy', 'uniform without replacement from all 4447')))
    return out


def main():
    rr, starts = runs_of_record()
    new_rows, checks = score_new(rr)
    rows = hist_rows() + new_rows
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_metrics_by_seed.csv'), rows)
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_runs_of_record.csv'), starts or [dict(arm='', seed='', run_dir='', status='no starts yet', role='')])
    if checks:
        K.write_csv(os.path.join(K.TABLES, 'EXP-01_independent_sm_check_new.csv'), checks)
    comp, worst = verdicts(rows)
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_comparisons.csv'), comp,
                ['endpoint', 'contrast', 'role', 'status', 'n_seeds', 'delta', 'sigma_hat_pool7', 'bar', 'df_pool', 'x_bar',
                 'sign', 'verdict', 'largest_effect_bar_could_miss', 'sigma_hat_new_arms_only', 'sigma_hat_OR_committed',
                 'welch95', 'paired95_df2_unstable', 'impl_ab_max_abs_diff', 'note'])
    K.write_csv(os.path.join(K.TABLES, 'run_manifest.csv'), manifest(rows, rr))
    print('runs of record: %d/12; independent S-measure max |diff| %s; impl A/B max |diff| %.1e'
          % (len(rr), '%.1e' % max(c['max_abs_diff'] for c in checks) if checks else 'n/a', worst))
    for c in comp:
        if c.get('verdict'):
            print('%-6s %-26s %-12s d=%s bar=%s sign=%s %s %s' % (c['endpoint'], c['contrast'], c['status'][:12], c['delta'],
                                                                  c['bar'], c['sign'], c['verdict'], c['role'][:30]))
        else:
            print('%-6s %-26s %s' % (c['endpoint'], c['contrast'], c['status']))


if __name__ == '__main__':
    main()

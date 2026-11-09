"""Stage-0 reproduction gate.

1. Scorer anchor: re-score the committed Result/SINet/S2C predictions with the repo scorer
   (rebuild/ABC/abc_evaluate.score) and require Sa = 0.717216, MAE = 0.074463 (tol 1e-5),
   exactly the check abc_evaluate performs before it scores anything.
2. Re-score four committed SE runs (two per architecture) on COD10K-test from their saved
   prediction maps and require every metric to equal the committed value in
   rebuild/ABC/out/se/abc_metrics.csv at its recorded precision (6 decimals).

Usage: .venv/bin/python stage0_repro_gate.py   (writes EXPERIMENT_LOGS/stage0_repro_gate.{log,json})
"""
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor

import _repo as R

RUNS = [('SINet', 'C10', 46), ('SINet', 'B', 49), ('SINetv2', 'CSHUF', 47), ('SINetv2', 'CINV', 50)]
KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
GT = os.path.join(R.REPO, 'Dataset', 'Test', 'COD10K', 'GT')


def _score(pred_dir):
    import abc_evaluate as E
    return E.score(GT, pred_dir)


def main():
    committed = {}
    with open(R.SE_METRICS) as f:
        for row in csv.DictReader(f):
            committed[(row['arch'], row['arm'], int(row['seed']), row['endpoint'])] = row
    jobs = {'anchor': os.path.join(R.REPO, 'Result', 'SINet', 'S2C')}
    for arch, arm, seed in RUNS:
        jobs['%s_%s_s%d' % (arch, arm, seed)] = os.path.join(
            R.REPO, 'Result', 'ABC', '%s_%s_s%d' % (arch, arm, seed), 'COD10K')
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        futs = {k: ex.submit(_score, v) for k, v in jobs.items()}
        got = {k: f.result() for k, f in futs.items()}

    report, ok_all = {}, True
    a = got['anchor']
    ok = abs(a['Sm'] - 0.717216) <= 1e-5 and abs(a['MAE'] - 0.074463) <= 1e-5
    report['anchor'] = dict(Sm=a['Sm'], MAE=a['MAE'], expect=dict(Sm=0.717216, MAE=0.074463), passed=ok)
    ok_all &= ok
    for arch, arm, seed in RUNS:
        rid = '%s_%s_s%d' % (arch, arm, seed)
        row = committed[(arch, arm, seed, 'COD10K')]
        mism = {k: dict(rescored='%.6f' % got[rid][k], committed=row[k])
                for k in KEYS if '%.6f' % got[rid][k] != row[k]}
        report[rid] = dict(Sm='%.6f' % got[rid]['Sm'], committed_Sm=row['Sm'], n=got[rid]['n'],
                           mismatches=mism, passed=not mism)
        ok_all &= not mism
    report['GATE'] = 'PASS' if ok_all else 'FAIL'
    os.makedirs(R.LOGS, exist_ok=True)
    with open(os.path.join(R.LOGS, 'stage0_repro_gate.json'), 'w') as f:
        json.dump(report, f, indent=2)
    lines = ['Stage-0 reproduction gate: %s' % report['GATE'],
             'anchor Result/SINet/S2C: Sa %.6f MAE %.6f (expect 0.717216 / 0.074463) -> %s'
             % (a['Sm'], a['MAE'], 'PASS' if report['anchor']['passed'] else 'FAIL')]
    for arch, arm, seed in RUNS:
        rid = '%s_%s_s%d' % (arch, arm, seed)
        r = report[rid]
        lines.append('%-18s COD10K n=%d  Sa rescored %s committed %s  all 9 metrics at 6 dp: %s'
                     % (rid, r['n'], r['Sm'], r['committed_Sm'], 'MATCH' if r['passed'] else 'MISMATCH %s' % r['mismatches']))
    txt = '\n'.join(lines) + '\n'
    open(os.path.join(R.LOGS, 'stage0_repro_gate.log'), 'w').write(txt)
    print(txt, end='')


if __name__ == '__main__':
    main()

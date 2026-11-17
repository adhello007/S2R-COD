"""Phase 4 spot check for EQ: re-score three EQ runs from their saved COD10K prediction maps with the committed
scorer (rebuild/ABC/abc_evaluate.score, unchanged) and compare with RESULT_TABLES/EXP01_EQ_metrics.csv at 6 dp.
Runs: the two lowest-scoring runs (B s116, CSHUF s115) and one ordinary run (C10 s103).
Usage: nice -n 19 taskset -c 40-47 .venv/bin/python analysis/eq_spot_rescore.py   (log: EXPERIMENT_LOGS/EXP01_spot_rescore.log)
"""
import csv
import os
import sys
from multiprocessing import Pool

import _repo as R

sys.path.insert(0, os.path.join(R.REPO, 'rebuild', 'ABC'))
RUNS = ['SINet_B_s116', 'SINet_CSHUF_s115', 'SINet_C10_s103']


def one(rid):
    import abc_evaluate as E
    return rid, E.score(os.path.join(R.REPO, 'Dataset', 'Test', 'COD10K', 'GT'), os.path.join(R.REPO, 'Result', 'ABC', rid, 'COD10K'))


def main():
    tab = {r['runid']: r for r in csv.DictReader(open(os.path.join(R.TABLES, 'EXP01_EQ_metrics.csv'))) if r['endpoint'] == 'COD10K'}
    with Pool(3) as p:
        res = p.map(one, RUNS)
    lines, bad = ['# EQ spot re-score from saved maps (COD10K-test), committed scorer'], 0
    for rid, v in res:
        for k in ('Sm', 'MAE', 'wFm', 'meanEm'):
            new, old = '%.6f' % v[k], '%.6f' % float(tab[rid][k])
            bad += new != old
            lines.append('%-4s %-18s %-7s re-scored %s  table %s' % ('PASS' if new == old else 'FAIL', rid, k, new, old))
    lines.append('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    open(os.path.join(R.LOGS, 'EXP01_spot_rescore.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

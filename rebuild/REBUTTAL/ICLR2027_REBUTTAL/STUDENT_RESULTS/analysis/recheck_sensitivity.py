#!/usr/bin/env python
"""EXPLORATORY, decides nothing (prereg/RECHECK.md: no result re-decides EQ).

RECHECK R2 re-trained SINet_CSHUF_s115 and did not reproduce it (0.6933 -> 0.7214). That run and SINet_B_s116
have the two lowest pseudo-label counts in EQ or SE (1,359 and 1,346; the next is 1,501). This recomputes the two
COD10K contrasts with eq_analysis.welch, as delivered and with each of those runs left out.
Writes EXPERIMENT_LOGS/RECHECK_sensitivity.log.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eq_analysis as A  # noqa: E402

ROOT = os.path.dirname(HERE)
rows = [r for r in csv.DictReader(open(os.path.join(ROOT, 'RESULT_TABLES', 'EXP01_EQ_metrics.csv')))
        if r['endpoint'] == 'COD10K']
arm = {a: {r['runid']: float(r['Sm']) for r in rows if r['arm'] == a} for a in ('B', 'C10', 'CSHUF')}
low = sorted((int(r['n_appended']), r['runid']) for r in rows)[:3]

out = ['# RECHECK sensitivity (EXPLORATORY; decides nothing). COD10K S_alpha, Welch, TOST margin +/-0.005',
       'lowest pseudo-label counts in EQ: ' + ', '.join('%s %d' % (rid, n) for n, rid in low)]
for hi, lo in (('C10', 'B'), ('C10', 'CSHUF')):
    for drop in (None, 'SINet_B_s116', 'SINet_CSHUF_s115'):
        a = [v for k, v in arm[hi].items() if k != drop]
        b = [v for k, v in arm[lo].items() if k != drop]
        if drop and len(a) == len(arm[hi]) and len(b) == len(arm[lo]):
            continue
        w = A.welch(a, b)
        out.append('%-9s %-26s n %d/%d  delta %+.4f  90%% CI [%+.4f, %+.4f]  TOST p %.4f  -> %s'
                   % ('%s-%s' % (hi, lo), 'as delivered' if drop is None else 'without ' + drop, len(a), len(b),
                      w['delta'], w['ci90'][0], w['ci90'][1], w['p_tost'],
                      'equivalent' if w['p_tost'] < 0.05 else 'not equivalent'))
open(os.path.join(ROOT, 'EXPERIMENT_LOGS', 'RECHECK_sensitivity.log'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))

"""Traceability scan (§0.1): every decimal number written by hand into EXPERIMENTAL_EVIDENCE.md, RESULTS_SUMMARY.md,
EXECUTION_STATUS.md (§11 report), FINAL_SCIENTIFIC_AUDIT.md and INSTRUCTION_COMPLIANCE_AUDIT.md must equal, at its printed precision, a value in a
saved artifact. Artifacts: RESULT_TABLES/, EXPERIMENT_LOGS/, prereg/ and the committed input CSVs. A value matches
if some artifact number rounds to it (half-up or half-even), sign ignored. Numbers that match nothing are listed for
review; the scan cannot tell a typo from a derived quantity (a difference, a ratio, a count), so each listed number
is then checked by hand and the outcome recorded in INSTRUCTION_COMPLIANCE_AUDIT.md.
Usage: python analysis/trace_numbers.py   (log: EXPERIMENT_LOGS/trace_numbers.log)
"""
import glob
import os
import re
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

import _repo as R

DOCS = ['EXPERIMENTAL_EVIDENCE.md', 'RESULTS_SUMMARY.md', 'FINAL_SCIENTIFIC_AUDIT.md', 'EXECUTION_STATUS.md',
        'INSTRUCTION_COMPLIANCE_AUDIT.md']
NUM = re.compile(r'(?<![\w.])[-+−]?\d+\.\d+')
ART = (glob.glob(os.path.join(R.TABLES, '*')) + glob.glob(os.path.join(R.LOGS, '*')) + glob.glob(os.path.join(R.STUDENT, 'prereg', '*'))
       + [os.path.join(R.REPO, p) for p in ('rebuild/ABC/out/se/abc_metrics.csv', 'rebuild/ABC/out/se/abc_runs.csv',
                                            'rebuild/ABC/out/cdr/cdr_allocations.csv', 'rebuild/ABC/out/abc_metrics.csv',
                                            'rebuild/RL5B/out/runner_state.json')])


def main():
    pool = set()
    for f in ART:
        if not os.path.isfile(f) or f.endswith(('.pdf', '.png', '.npy')):
            continue
        for tok in NUM.findall(open(f, errors='replace').read()):
            d = Decimal(tok.replace('−', '-').lstrip('+-'))
            for dp in range(1, 7):
                q = Decimal(1).scaleb(-dp)
                pool.add(str(d.quantize(q, ROUND_HALF_UP)))
                pool.add(str(d.quantize(q, ROUND_HALF_EVEN)))
    lines, total, miss = ['# Traceability scan of hand-written numbers'], 0, []
    for doc in DOCS:
        text = open(os.path.join(R.STUDENT, doc)).read()
        if doc == 'EXECUTION_STATUS.md':
            text = text[:text.index("## Author's binding rules")]          # the §11 report only
        for ln, line in enumerate(text.splitlines(), 1):
            for tok in NUM.findall(line):
                v = tok.replace('−', '-').lstrip('+-')
                total += 1
                if v not in pool:
                    miss.append('%s:%d  %s   | %s' % (doc, ln, tok, line.strip()[:110]))
    lines.append('numbers scanned: %d; traced to an artifact: %d; not traced: %d' % (total, total - len(miss), len(miss)))
    lines += ['  ' + m for m in miss]
    open(os.path.join(R.LOGS, 'trace_numbers.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()

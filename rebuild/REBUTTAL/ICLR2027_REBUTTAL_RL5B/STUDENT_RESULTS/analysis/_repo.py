"""Locate the repo root and put the pipeline modules on sys.path (shared by every analysis script)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDENT = os.path.dirname(HERE)                       # .../STUDENT_RESULTS


def _find_repo(start):
    d = start
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, 'MyTrain.py')) and os.path.isdir(os.path.join(d, 'rebuild')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('repo root not found above %s' % start)


REPO = _find_repo(HERE)
for _p in (os.path.join(REPO, 'rebuild', 'ABC'), os.path.join(REPO, 'rebuild'), REPO,
           os.path.join(REPO, 'Eval'), os.path.join(REPO, 'rebuild', 'C1')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

TABLES = os.path.join(STUDENT, 'RESULT_TABLES')
LOGS = os.path.join(STUDENT, 'EXPERIMENT_LOGS')
FIGS = os.path.join(STUDENT, 'FIGURES')
SE_METRICS = os.path.join(REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_metrics.csv')
SE_VERDICT = os.path.join(REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_verdict.json')

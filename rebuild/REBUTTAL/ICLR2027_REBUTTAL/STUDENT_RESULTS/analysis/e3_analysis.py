"""EXP-03 (descriptive; prereg/E3.md): protocol-matched references and the gap decomposition.

Subcommands
  external   score the released SINet-V2 (E3-a) and RISE (E3-d) prediction maps with OUR scorer
             (rebuild/ABC/abc_evaluate.score) on COD10K-test and NC4K -> RESULT_TABLES/EXP03_external_scores.csv
  anchors    score committed anchor runs that have saved maps (E3-f) -> RESULT_TABLES/EXP03_anchor_scores.csv
  runs       score the E3-c / E3-e runs trained by the queue -> RESULT_TABLES/EXP03_run_scores.csv
  table      assemble RESULT_TABLES/EXP03_protocol_matched.{csv,md} and EXP03_gap_decomposition.md from the
             three score files and the verified published values (RESULT_TABLES/AN02_published_baselines.json).
             Only measured or verified cells are filled; anything missing is shown as an em dash.

Run: .venv/bin/python e3_analysis.py {external,anchors,runs,table} [--workers 16]
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

KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
EPS = ('COD10K', 'NC4K')
EXT = os.path.join(R.REPO, 'Dataset', 'External')
EXTERNAL = {'E3-a SINet-V2 (released maps)': os.path.join(EXT, 'SINetV2_official', 'extract', '2021-TPAMI-SINetV2-PyTorch'),
            'E3-d RISE (released maps)': os.path.join(EXT, 'RISE', 'extract', 'RISE', 'PredictedMap')}


def _score(args):
    import abc_evaluate as E
    return E.score(*args)


def gt(ep):
    return os.path.join(R.REPO, 'Dataset', 'Test', ep, 'GT')


def write(name, rows):
    with open(os.path.join(R.TABLES, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def external(workers):
    jobs = [(name, ep, (gt(ep), os.path.join(root, ep))) for name, root in EXTERNAL.items() for ep in EPS]
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [j[2] for j in jobs]))
    rows = [dict(source=n, endpoint=ep, n=m['n'], shape_mismatch=m['shape_mismatch'], **{k: '%.6f' % m[k] for k in KEYS})
            for (n, ep, _), m in zip(jobs, res)]
    write('EXP03_external_scores.csv', rows)
    for r in rows:
        print('%-32s %-6s n=%d shape_mismatch=%d Sa %s meanEm %s wFm %s MAE %s' % (
            r['source'], r['endpoint'], r['n'], r['shape_mismatch'], r['Sm'], r['meanEm'], r['wFm'], r['MAE']))


def anchors(workers):
    """Committed single-run S2R-COD reproductions with saved maps (COD10K at Result/<net>/<run>; NC4K if present)."""
    cand = [('E3-f SINet ours (two-round, reproduced 0.7172)', 'Result/SINet/S2C'),
            ('E3-f SINet mean teacher (reproduced 0.7030)', 'Result/SINet/S2C_MT'),
            ('E3-f SINet source-only (student)', 'Result/SINet/S2C_SO_stu'),
            ('E3-f SINet-v2 ours (two-round)', 'Result/SINet-v2/S2C'),
            ('E3-f SINet-v2 mean teacher', 'Result/SINet-v2/S2C_MT'),
            ('E3-f SINet-v2 source-only (student)', 'Result/SINet-v2/S2C_SO_stu')]
    jobs = []
    for name, rel in cand:
        base = os.path.join(R.REPO, rel)
        for ep in EPS:
            d = os.path.join(base, ep) if os.path.isdir(os.path.join(base, ep)) else (base if ep == 'COD10K' else None)
            if d and os.path.isdir(d) and len([f for f in os.listdir(d) if f.endswith('.png')]) == len(os.listdir(gt(ep))):
                jobs.append((name, ep, (gt(ep), d)))
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [j[2] for j in jobs]))
    rows = [dict(source=n, endpoint=ep, n=m['n'], shape_mismatch=m['shape_mismatch'], **{k: '%.6f' % m[k] for k in KEYS})
            for (n, ep, _), m in zip(jobs, res)]
    write('EXP03_anchor_scores.csv', rows)
    for r in rows:
        print('%-50s %-6s Sa %s meanEm %s wFm %s' % (r['source'], r['endpoint'], r['Sm'], r['meanEm'], r['wFm']))


def runs(workers):
    jobs_f = json.load(open(os.path.join(R.REPO, 'rebuild', 'RL5B', 'queue_jobs.json')))['jobs']
    jobs = []
    for j in jobs_f:
        if j.get('campaign') in ('e3c', 'e3e'):
            for ep in EPS:
                d = os.path.join(R.REPO, j['pred_root'], ep)
                if os.path.isdir(d) and len(os.listdir(d)) == len(os.listdir(gt(ep))):
                    jobs.append((j, ep, (gt(ep), d)))
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [x[2] for x in jobs]))
    rows = [dict(job=j['id'], campaign=j['campaign'], arch=j['arch'], seed=j['seed'], endpoint=ep, n=m['n'],
                 **{k: '%.6f' % m[k] for k in KEYS}) for (j, ep, _), m in zip(jobs, res)]
    write('EXP03_run_scores.csv', rows)
    print('scored %d run x endpoint folders' % len(rows))


def table():
    raise SystemExit('table: assembled after AN-02 provides verified published values (see prereg/E3.md)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['external', 'anchors', 'runs', 'table'])
    ap.add_argument('--workers', type=int, default=16)
    a = ap.parse_args()
    {'external': lambda: external(a.workers), 'anchors': lambda: anchors(a.workers), 'runs': lambda: runs(a.workers),
     'table': table}[a.cmd]()

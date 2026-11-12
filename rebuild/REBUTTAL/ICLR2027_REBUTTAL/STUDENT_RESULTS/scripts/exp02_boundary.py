#!/usr/bin/env python
"""EXP-02 -- boundary metrics re-scored from stored predictions (post-review, exploratory).

Calls the committed per-image worker diag_boundary._job UNCHANGED (base rebuild/DIAG/diag_boundary.py,
commit 8d1d079), with its module globals pointed at the original working copy's data (read-only):
  PRED_ROOT = <data-root>/Result/ABC, GT_DIR = <data-root>/Dataset/Test/<EP>/GT, ENDPOINT, _THRESH.

Runs: the 64 eight-seed runs (run_manifest.csv) on COD10K and NC4K, plus the 12 committed A0/A2
three-seed runs on COD10K only (Gate 3 reproduction, ANALYSIS_PRESPEC.md §7). Thresholds 0.4/0.5/0.6.

Outputs:
  RUNS/exp02/exp02_per_image.csv.gz         per image x run x endpoint x threshold
  RUNS/exp02/exp02_per_run.csv              nanmean per run x endpoint x threshold (committed aggregation)
  RESULT_TABLES/EXP-02_gate3_reproduction.csv
  EXPERIMENT_LOGS/EXP-02_meta.json
"""
import argparse
import csv
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
ap.add_argument('--workers', type=int, default=8)
ap.add_argument('--limit', type=int, default=0, help='debug: images per run')
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, os.path.join(WT, 'rebuild/DIAG'))
import diag_boundary as DB        # noqa: E402  (base, unchanged)

THRESHOLDS = (0.4, 0.5, 0.6)
METRICS = ('boundary_iou', 'boundary_f', 'boundary_prec', 'boundary_rec', 'iou')
COMMITTED = {0.5: 'diag_boundary_per_run.csv', 0.4: 'diag_boundary_per_run_t0.40.csv',
             0.6: 'diag_boundary_per_run_t0.60.csv'}


def job(t):
    rid, ep, thr, stem = t
    DB.PRED_ROOT = os.path.join(DR, 'Result/ABC')
    DB.GT_DIR = os.path.join(DR, 'Dataset/Test', ep, 'GT')
    DB.ENDPOINT = ep
    DB._THRESH = thr
    r = DB._job((rid, stem))
    r['endpoint'], r['thresh'] = ep, thr
    return r


def main():
    t0 = time.time()
    out = os.path.join(SR, 'RUNS/exp02')
    os.makedirs(out, exist_ok=True)
    man = list(csv.DictReader(open(os.path.join(SR, 'RESULT_TABLES/run_manifest.csv'))))
    runs8 = sorted({'%s_%s_s%s' % (r['architecture'], r['arm'], r['seed']) for r in man})
    assert len(runs8) == 64
    abc = list(csv.DictReader(open(os.path.join(WT, 'rebuild/ABC/out/abc_runs.csv'))))
    gate_only = sorted(r['runid'] for r in abc if r['arm'] in ('A0', 'A2'))
    assert len(gate_only) == 12, gate_only
    stems = {ep: sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(DR, 'Dataset/Test', ep, 'GT'))
                        if f.endswith('.png')) for ep in ('COD10K', 'NC4K')}
    if a.limit:
        stems = {k: v[:a.limit] for k, v in stems.items()}
    jobs = []
    for thr in THRESHOLDS:
        for rid in runs8:
            for ep in ('COD10K', 'NC4K'):
                jobs += [(rid, ep, thr, s) for s in stems[ep]]
        for rid in gate_only:
            jobs += [(rid, 'COD10K', thr, s) for s in stems['COD10K']]
    print('jobs %d workers %d' % (len(jobs), a.workers), flush=True)
    rows = []
    with Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(job, jobs, chunksize=64), 1):
            rows.append(r)
            if i % 50000 == 0:
                print('  %d / %d  %.0fs' % (i, len(jobs), time.time() - t0), flush=True)
    errs = [r for r in rows if 'error' in r]
    rows = [r for r in rows if 'error' not in r]
    rows.sort(key=lambda x: (x['thresh'], x['runid'], x['endpoint'], x['name']))
    with gzip.open(os.path.join(out, 'exp02_per_image.csv.gz'), 'wt') as f:
        w = csv.writer(f)
        w.writerow(['thresh', 'runid', 'endpoint', 'name'] + list(METRICS) + ['gt_fg_frac'])
        for r in rows:
            w.writerow([r['thresh'], r['runid'], r['endpoint'], r['name']]
                       + ['%.9g' % r[m] for m in METRICS] + ['%.9g' % r['gt_fg_frac']])
    # committed aggregation: nanmean over images, per run
    by = {}
    for r in rows:
        by.setdefault((r['thresh'], r['runid'], r['endpoint']), []).append(r)
    agg = []
    for (thr, rid, ep), rs in sorted(by.items()):
        p = rid.split('_')
        d = dict(thresh=thr, runid=rid, arch=p[0], arm=p[1], seed=int(p[2][1:]), endpoint=ep, n=len(rs))
        for m in METRICS:
            v = np.array([x[m] for x in rs], dtype=np.float64)
            d[m] = float(np.nanmean(v))
            d['n_nan_' + m] = int(np.isnan(v).sum())
        agg.append(d)
    with open(os.path.join(out, 'exp02_per_run.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0]))
        w.writeheader()
        for d in agg:
            w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in d.items()})
    # Gate 3
    mine = {(d['thresh'], d['runid']): d for d in agg if d['endpoint'] == 'COD10K'}
    g3, worst, n_cmp = [], 0.0, 0
    for thr, fn in COMMITTED.items():
        for c in csv.DictReader(open(os.path.join(WT, 'rebuild/DIAG/out', fn))):
            m = mine.get((thr, c['runid']))
            for k in METRICS:
                if m is None:
                    g3.append(dict(thresh=thr, runid=c['runid'], metric=k, committed=c[k], recomputed='',
                                   abs_diff='', match_1e9=False, note='run not recomputed'))
                    continue
                dlt = abs(float(c[k]) - m[k])
                worst, n_cmp = max(worst, dlt), n_cmp + 1
                g3.append(dict(thresh=thr, runid=c['runid'], metric=k, committed=c[k], recomputed=repr(m[k]),
                               abs_diff=dlt, match_1e9=dlt <= 1e-9, note='n_committed=%s n_mine=%d'
                               % (c['n'], m['n'])))
    with open(os.path.join(SR, 'RESULT_TABLES/EXP-02_gate3_reproduction.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(g3[0]))
        w.writeheader()
        w.writerows(g3)
    meta = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n_jobs=len(jobs),
                n_rows=len(rows), n_errors=len(errs), errors=errs[:20], thresholds=THRESHOLDS,
                biou_frac=DB.BIOU_FRAC, bf_frac=DB.BF_FRAC, gate3=dict(
                    n_compared=n_cmp, max_abs_diff=worst,
                    n_fail=sum(1 for x in g3 if not x['match_1e9']),
                    passed=all(x['match_1e9'] for x in g3)),
                seconds=round(time.time() - t0, 1), limit=a.limit)
    json.dump(meta, open(os.path.join(SR, 'EXPERIMENT_LOGS/EXP-02_meta.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k != 'errors'}, indent=1))


if __name__ == '__main__':
    main()

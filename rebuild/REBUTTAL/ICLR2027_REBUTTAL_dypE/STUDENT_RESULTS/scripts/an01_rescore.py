#!/usr/bin/env python
"""AN-01 -- re-score the 64 eight-seed runs x {COD10K, NC4K} from stored predictions.

Uses the committed scorer UNCHANGED: score() from base rebuild/ABC/abc_evaluate.py (this
worktree, commit 8d1d079), which uses base Eval/metrics.py. Data are read from --data-root
(the original working copy); nothing is written there.

Gate 1 (ANALYSIS_PRESPEC.md §3): B1 scorer validation, S_alpha 0.717216 / MAE 0.074463, tol 1e-5.
Gate 2: every committed metric reproduced at 6 dp.

Outputs:
  RUNS/an01/an01_rescored_full.csv          full-precision per-run metrics (128 rows)
  RUNS/an01/an01_per_image.csv.gz           per-image S_alpha and MAE (same metric classes)
  RESULT_TABLES/AN-01_original_vs_recomputed.csv
  EXPERIMENT_LOGS/AN-01_gates.json
"""
import argparse
import csv
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True, help='STUDENT_RESULTS dir')
ap.add_argument('--workers', type=int, default=16)
ap.add_argument('--limit', type=int, default=0, help='debug: only first N tasks')
a = ap.parse_args()

WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, os.path.join(WT, 'rebuild/ABC'))
sys.path.insert(0, os.path.join(WT, 'rebuild'))
sys.path.insert(0, os.path.join(WT, 'Eval'))
import abc_evaluate as E          # noqa: E402  (base, unchanged)
import metrics as Measure         # noqa: E402  (base Eval/metrics.py)
import cv2                        # noqa: E402

KEYS = E.METRIC_KEYS


def per_image(gt_dir, pred_dir):
    """Per-image S_alpha and MAE with the SAME classes and the SAME read/resize as score()."""
    SM, MAE = Measure.Smeasure(), Measure.MAE()
    names = sorted(os.listdir(gt_dir))
    for nm in names:
        pred = cv2.imread(os.path.join(pred_dir, nm), cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(os.path.join(gt_dir, nm), cv2.IMREAD_GRAYSCALE)
        if pred.shape != gt.shape:
            pred = cv2.resize(pred, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
        SM.step(pred=pred, gt=gt)
        MAE.step(pred=pred, gt=gt)
    return names, [float(x) for x in SM.sms], [float(x) for x in MAE.maes]


def task(t):
    rid, ep = t
    gt_dir = os.path.join(DR, 'Dataset/Test', ep, 'GT')
    pred_dir = os.path.join(DR, 'Result/ABC', rid, ep)
    t0 = time.time()
    agg = E.score(gt_dir, pred_dir)                      # committed scorer, unchanged
    names, sms, maes = per_image(gt_dir, pred_dir)
    return dict(rid=rid, ep=ep, agg=agg, names=names, sms=sms, maes=maes, sec=time.time() - t0)


def main():
    t0 = time.time()
    out_runs = os.path.join(SR, 'RUNS/an01')
    os.makedirs(out_runs, exist_ok=True)
    gates = {}
    # ---- Gate 1
    b1 = os.path.join(DR, 'Result/SINet/S2C')
    if os.path.isdir(b1):
        v = E.score(os.path.join(DR, 'Dataset/Test/COD10K/GT'), b1)
        gates['gate1'] = dict(Sm=v['Sm'], MAE=v['MAE'], ref_Sm=E.B1_SA, ref_MAE=E.B1_MAE,
                              d_Sm=abs(v['Sm'] - E.B1_SA), d_MAE=abs(v['MAE'] - E.B1_MAE),
                              tol=E.TOL, passed=bool(abs(v['Sm'] - E.B1_SA) < E.TOL
                                                     and abs(v['MAE'] - E.B1_MAE) < E.TOL))
    else:
        gates['gate1'] = dict(passed=None, note='B1 predictions absent')
    print('gate1', gates['gate1'], flush=True)
    if gates['gate1'].get('passed') is False:
        json.dump(gates, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-01_gates.json'), 'w'), indent=1)
        sys.exit('AN-01 HALT: scorer does not reproduce B1')

    man = list(csv.DictReader(open(os.path.join(SR, 'RESULT_TABLES/run_manifest.csv'))))
    committed = {(r['runid'], r['endpoint']): r for r in
                 csv.DictReader(open(os.path.join(WT, 'rebuild/ABC/out/se/abc_metrics.csv')))}
    camp_csv = {'ABC': 'rebuild/ABC/out/abc_metrics.csv', 'T2': 'rebuild/ABC/out/t2/abc_metrics.csv',
                'SE': 'rebuild/ABC/out/se/abc_metrics.csv'}
    camp = {c: {(r['runid'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(WT, p)))}
            for c, p in camp_csv.items()}
    tasks, meta = [], {}
    for r in man:
        rid = '%s_%s_s%s' % (r['architecture'], r['arm'], r['seed'])
        tasks.append((rid, r['endpoint']))
        meta[(rid, r['endpoint'])] = r
    if a.limit:
        tasks = tasks[:a.limit]
    res = []
    with Pool(a.workers) as pool:
        for i, x in enumerate(pool.imap_unordered(task, tasks), 1):
            res.append(x)
            print('[%d/%d] %s %s %.0fs Sm=%.6f' % (i, len(tasks), x['rid'], x['ep'], x['sec'],
                                                 x['agg']['Sm']), flush=True)
    res.sort(key=lambda x: (x['rid'], x['ep']))

    # ---- full-precision table + per-image
    with open(os.path.join(out_runs, 'an01_rescored_full.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['runid', 'arch', 'arm', 'seed', 'endpoint', 'n', 'shape_mismatch'] + list(KEYS)
                   + ['per_image_mean_Sm', 'per_image_mean_MAE'])
        for x in res:
            m = meta[(x['rid'], x['ep'])]
            w.writerow([x['rid'], m['architecture'], m['arm'], m['seed'], x['ep'], x['agg']['n'],
                        x['agg']['shape_mismatch']] + [repr(x['agg'][k]) for k in KEYS]
                       + [repr(sum(x['sms']) / len(x['sms'])), repr(sum(x['maes']) / len(x['maes']))])
    with gzip.open(os.path.join(out_runs, 'an01_per_image.csv.gz'), 'wt') as f:
        w = csv.writer(f)
        w.writerow(['runid', 'endpoint', 'name', 'Sm', 'MAE'])
        for x in res:
            for nm, s, e in zip(x['names'], x['sms'], x['maes']):
                w.writerow([x['rid'], x['ep'], nm, '%.10f' % s, '%.10f' % e])

    # ---- Gate 2 comparison
    rows, n_mis, n_cmp, max_pi_dev = [], 0, 0, 0.0
    for x in res:
        key = (x['rid'], x['ep'])
        m = meta[key]
        c_se = committed[key]
        c_tr = camp[m['trained_in']].get(key)
        pi_dev = max(abs(sum(x['sms']) / len(x['sms']) - x['agg']['Sm']),
                     abs(sum(x['maes']) / len(x['maes']) - x['agg']['MAE']))
        max_pi_dev = max(max_pi_dev, pi_dev)
        for k in KEYS:
            rec6 = '%.6f' % x['agg'][k]
            n_cmp += 1
            eq_se = rec6 == c_se[k]
            eq_tr = (rec6 == c_tr[k]) if c_tr else None
            if not eq_se or eq_tr is False:
                n_mis += 1
            rows.append(dict(runid=x['rid'], architecture=m['architecture'], arm=m['arm'],
                             seed=m['seed'], endpoint=x['ep'], trained_in=m['trained_in'], metric=k,
                             n_images=x['agg']['n'], committed_se_csv=c_se[k],
                             committed_trained_campaign_csv=(c_tr[k] if c_tr else ''),
                             recomputed_6dp=rec6, recomputed_full=repr(x['agg'][k]),
                             abs_diff_vs_se=abs(float(c_se[k]) - x['agg'][k]),
                             exact_6dp_match_se=eq_se, exact_6dp_match_trained=eq_tr,
                             prediction_sha=m['prediction_sha'], gt_sha=m['dataset_manifest_sha'],
                             metric_code_sha=m['metric_code_sha'], status='post-review re-score'))
    with open(os.path.join(SR, 'RESULT_TABLES/AN-01_original_vs_recomputed.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    gates['gate2'] = dict(n_compared=n_cmp, n_mismatch=n_mis, passed=(n_mis == 0),
                          n_tasks=len(res), max_per_image_mean_vs_aggregate=max_pi_dev)
    gates['seconds'] = round(time.time() - t0, 1)
    gates['generated_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(gates, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-01_gates.json'), 'w'), indent=1)
    print(json.dumps(gates, indent=1))


if __name__ == '__main__':
    main()

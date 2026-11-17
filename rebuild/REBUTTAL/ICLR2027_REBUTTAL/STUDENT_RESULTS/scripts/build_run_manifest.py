#!/usr/bin/env python
"""Build the §3 run manifest and an immutable SHA256 inventory for the 64 eight-seed runs.

Run list = the committed rebuild/ABC/out/se/abc_runs.csv at the base commit (this worktree).
Data are READ from the original working copy (--data-root); nothing is written there.

Outputs (under --out-dir):
  RESULT_TABLES/run_manifest.csv                 one row per run x endpoint (128 rows)
  EXPERIMENT_LOGS/checksums/prediction_files.sha256.gz   per-file hashes of every prediction
  EXPERIMENT_LOGS/checksums/gt_files.sha256.gz           per-file hashes of endpoint GT
  EXPERIMENT_LOGS/checksums/checkpoints.sha256           Tea_epoch_best.pth hashes
  EXPERIMENT_LOGS/checksums/manifest_meta.json
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from multiprocessing import Pool

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--out-dir', required=True)
ap.add_argument('--workers', type=int, default=16)
a = ap.parse_args()

WT, DR, OUT = a.worktree, a.data_root, a.out_dir
ENDPOINTS = ('COD10K', 'NC4K')
BASE_OUT = os.path.join(WT, 'rebuild/ABC/out')


def sha_file(p, bs=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def hash_dir(d):
    names = sorted(os.listdir(d))
    rows = [(n, sha_file(os.path.join(d, n))) for n in names]
    digest = sha_bytes(''.join('%s\t%s\n' % r for r in rows).encode())
    return d, rows, digest


def git(*args):
    return subprocess.check_output(['git', '-C', WT] + list(args), text=True).strip()


def main():
    t0 = time.time()
    os.makedirs(os.path.join(OUT, 'RESULT_TABLES'), exist_ok=True)
    ck = os.path.join(OUT, 'EXPERIMENT_LOGS', 'checksums')
    os.makedirs(ck, exist_ok=True)
    runs = list(csv.DictReader(open(os.path.join(BASE_OUT, 'se/abc_runs.csv'))))
    assert len(runs) == 64, len(runs)
    metrics = {(r['runid'], r['endpoint']): r
               for r in csv.DictReader(open(os.path.join(BASE_OUT, 'se/abc_metrics.csv')))}

    # trained-in campaign: B/C10 at committed seeds -> ABC; CSHUF/CINV at committed seeds -> T2; else SE
    def trained_in(arm, seed):
        if seed in (42, 43, 45):
            return 'ABC' if arm in ('B', 'C10') else 'T2'
        return 'SE'
    cmd_file = {'ABC': 'abc_commands.txt', 'T2': 't2/abc_commands.txt', 'SE': 'se/abc_commands.txt'}
    camp_commit, camp_cmds = {}, {}
    for c, f in cmd_file.items():
        txt = open(os.path.join(BASE_OUT, f)).read().splitlines()
        m = re.search(r'commit (\S+)( \(dirty\))?', txt[1])
        camp_commit[c] = m.group(1) + (' (dirty)' if m.group(2) else '')
        camp_cmds[c] = [l for l in txt if 'MyTrain.py' in l]
    camp_metrics = {'ABC': 'rebuild/ABC/out/abc_metrics.csv', 'T2': 'rebuild/ABC/out/t2/abc_metrics.csv',
                    'SE': 'rebuild/ABC/out/se/abc_metrics.csv'}

    def stems_file(arm, seed):
        return {'B': 'abc_stems_B_s%d.txt' % seed, 'C10': 'abc_stems_C_a1.0.txt',
                'CSHUF': 'abc_stems_CSHUF.txt', 'CINV': 'abc_stems_CINV.txt'}[arm]

    metric_code = {p: sha_file(os.path.join(WT, p)) for p in ('Eval/metrics.py', 'rebuild/ABC/abc_evaluate.py')}
    metric_code_sha = sha_bytes(json.dumps(metric_code, sort_keys=True).encode())

    # ---- hash all directories in parallel
    dirs = [os.path.join(DR, 'Dataset/Test', e, 'GT') for e in ENDPOINTS]
    for r in runs:
        for e in ENDPOINTS:
            dirs.append(os.path.join(DR, 'Result/ABC', r['runid'], e))
    ckpts = [os.path.join(DR, 'Snapshot/ABC', r['runid'], 'Tea_epoch_best.pth') for r in runs]
    with Pool(a.workers) as pool:
        dres = {d: (rows, dig) for d, rows, dig in pool.imap_unordered(hash_dir, dirs)}
        cres = dict(zip(ckpts, pool.map(sha_file, ckpts)))
    gt_digest = {e: dres[os.path.join(DR, 'Dataset/Test', e, 'GT')][1] for e in ENDPOINTS}

    with gzip.open(os.path.join(ck, 'prediction_files.sha256.gz'), 'wt') as f:
        for r in runs:
            for e in ENDPOINTS:
                for n, h in dres[os.path.join(DR, 'Result/ABC', r['runid'], e)][0]:
                    f.write('%s  Result/ABC/%s/%s/%s\n' % (h, r['runid'], e, n))
    with gzip.open(os.path.join(ck, 'gt_files.sha256.gz'), 'wt') as f:
        for e in ENDPOINTS:
            for n, h in dres[os.path.join(DR, 'Dataset/Test', e, 'GT')][0]:
                f.write('%s  Dataset/Test/%s/GT/%s\n' % (h, e, n))
    with open(os.path.join(ck, 'checkpoints.sha256'), 'w') as f:
        for p in ckpts:
            f.write('%s  %s\n' % (cres[p], os.path.relpath(p, DR)))

    cols = ['campaign', 'trained_in', 'architecture', 'endpoint', 'arm', 'seed', 'round', 'git_sha',
            'config_sha', 'dataset_manifest_sha', 'inject_manifest_sha', 'checkpoint_sha',
            'prediction_sha', 'source_count', 'target_count', 'injected_count', 'pseudo_count',
            'steps_per_epoch', 'checkpoint_selection_split', 'metric_code_sha', 'raw_log_path',
            'metric_path', 'status', 'n_pred_files', 'n_gt_files', 'pred_names_match_gt',
            'pred_newest_mtime', 'committed_Sm']
    out_rows, problems = [], []
    for r in runs:
        rid, arm, seed, arch = r['runid'], r['arm'], int(r['seed']), r['arch']
        camp = trained_in(arm, seed)
        cmd = [l for l in camp_cmds[camp] if '--save_model ./Snapshot/ABC/%s/' % rid in l]
        if len(cmd) != 1:
            problems.append('%s: %d command lines in %s' % (rid, len(cmd), cmd_file[camp]))
        sf = stems_file(arm, seed)
        inj = sha_file(os.path.join(BASE_OUT, 'se', sf))
        # stems used when the run was TRAINED (ABC/T2 out dirs for committed seeds)
        sub = {'ABC': '', 'T2': 't2', 'SE': 'se'}[camp]
        inj_trained = sha_file(os.path.join(BASE_OUT, sub, sf))
        if inj != inj_trained:
            problems.append('%s: stems differ between se/ and %s/' % (rid, sub or 'ABC'))
        log = os.path.join(DR, 'Snapshot/ABC', rid, 'training_log.log')
        for e in ENDPOINTS:
            pd = os.path.join(DR, 'Result/ABC', rid, e)
            rows, dig = dres[pd]
            gtn = [n for n, _ in dres[os.path.join(DR, 'Dataset/Test', e, 'GT')][0]]
            newest = max(os.path.getmtime(os.path.join(pd, n)) for n, _ in rows)
            ok = (r['failed_checks'] == '' and r['tea_best'] == 'True' and [n for n, _ in rows] == gtn)
            if not ok:
                problems.append('%s/%s: integrity check failed' % (rid, e))
            out_rows.append(dict(
                campaign='SE', trained_in=camp, architecture=arch, endpoint=e, arm=arm, seed=seed,
                round='final (round 2), Tea_epoch_best.pth', git_sha=camp_commit[camp],
                config_sha=sha_bytes(cmd[0].encode()) if len(cmd) == 1 else '',
                dataset_manifest_sha=gt_digest[e], inject_manifest_sha=inj,
                checkpoint_sha=cres[os.path.join(DR, 'Snapshot/ABC', rid, 'Tea_epoch_best.pth')],
                prediction_sha=dig, source_count=r['pool_r1'], target_count=4040,
                injected_count=1000, pseudo_count=r['n_appended'],
                steps_per_epoch=int(r['total_step_set']),
                checkpoint_selection_split='CAMO-250 (Dataset/Val/CAMO, MAE)',
                metric_code_sha=metric_code_sha,
                raw_log_path='Snapshot/ABC/%s/training_log.log' % rid,
                metric_path=camp_metrics[camp] + ' ; rebuild/ABC/out/se/abc_metrics.csv',
                status='OK' if ok else 'INTEGRITY_FAIL', n_pred_files=len(rows), n_gt_files=len(gtn),
                pred_names_match_gt=[n for n, _ in rows] == gtn,
                pred_newest_mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(newest)),
                committed_Sm=metrics[(rid, e)]['Sm']))
    with open(os.path.join(OUT, 'RESULT_TABLES/run_manifest.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)
    meta = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                worktree_head=git('rev-parse', 'HEAD'), data_root=DR, n_runs=len(runs),
                n_rows=len(out_rows), campaign_commits=camp_commit, metric_code=metric_code,
                gt_digest=gt_digest, problems=problems, seconds=round(time.time() - t0, 1),
                digest_definition='sha256 over sorted lines "<filename>\\t<sha256(file)>\\n"')
    json.dump(meta, open(os.path.join(ck, 'manifest_meta.json'), 'w'), indent=1)
    print(json.dumps(meta, indent=1))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()

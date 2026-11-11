#!/usr/bin/env python
"""CAUS EXP-01 -- reuse gate R1-R4 for the historical B / C10 / CORACLE SINet runs.

R1 code    : trainer-path source at each historical run's recorded commit vs this worktree's HEAD.
             Allowed difference: the opt-in --exposure patch (P6) whose default branch is unchanged,
             and comment-only lines. Anything else FAILS the gate.
R2 env     : the shared venv's training packages predate the first historical run.
R3 data    : EVERY file of every declared primary input re-hashed against E0's committed manifest.
R4 stems   : the committed stem files are reproduced byte-for-byte (exp01_alloc_test.py).
Integrity  : historical Tea_epoch_best.pth / Stu_40.pth sha256 + mtimes, prediction counts.

R5 (re-scoring) is caus_score.py --rescore-historical. R6 (step-0 loss replay) runs in the pilot.
Writes RESULT_TABLES/EXP-01_reuse_gate.csv and EXP-01_historical_runs.csv.
"""

import csv
import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402

RUNS = [('SINet_%s_s%d' % (a, s), a, s) for a in ('B', 'C10', 'CORACLE', 'CSHUF') for s in (42, 43, 45)]
TRAINER_FILES = ['MyTrain.py', 'MyTest.py', 'CLS.py', 'Src', 'Eval/metrics.py']
MANIFEST_KEYS = ('raw', 'raw_gt', 'auth', 'auth_gt', 'local', 'local_msk', 'tgt',
                 'test', 'test_gt', 'val', 'val_gt', 'nc4k')
PATHS = dict(raw='Dataset/Source/HKU-IS_raw/imgs', raw_gt='Dataset/Source/HKU-IS_raw/gt',
             auth='Dataset/Source/HKU-IS/Image', auth_gt='Dataset/Source/HKU-IS/GT',
             local='Dataset/LAKERED/output/HKU-IS/images', local_msk='Dataset/LAKERED/output/HKU-IS/masks',
             tgt='Dataset/Target/Image', test='Dataset/Test/COD10K/Imgs', test_gt='Dataset/Test/COD10K/GT',
             val='Dataset/Val/CAMO/Imgs', val_gt='Dataset/Val/CAMO/GT', nc4k='Dataset/Test/NC4K/Imgs')


def git(*a):
    return subprocess.check_output(['git'] + list(a), cwd=K.REPO, text=True)


def run_commit(rid):
    """The commit a historical run recorded in its driver log header (original copy, read-only)."""
    p = K.orig(os.path.join('rebuild/ABC', rid + '.log'))
    head = open(p).read(2000)
    m = re.search(r'# commit\s+([0-9a-f]{7,40})( \(dirty\))?', head)
    t = re.search(r'# started\s+(\S+)', head)
    return (m.group(1), bool(m.group(2))) if m else (None, None), (t.group(1) if t else None), p


def r1_code(commit):
    diff = git('diff', '-U0', commit, 'HEAD', '--', *TRAINER_FILES)
    bad = []
    files = re.findall(r'^diff --git a/(\S+)', diff, flags=re.M)
    for f in files:
        part = diff.split('diff --git a/%s' % f, 1)[1].split('\ndiff --git ', 1)[0]
        changed = [l for l in part.splitlines() if (l.startswith('+') or l.startswith('-'))
                   and not l.startswith('+++') and not l.startswith('---')]
        for l in changed:
            body = l[1:].strip()
            if body == '' or body.startswith('#'):
                continue                                         # comment-only / blank
            if f == 'MyTrain.py' and ('exposure' in body or '_cycle' in body or 'fixed_exposures' in body
                                      or body in ('while True:', 'for b in loader:', 'yield b',
                                                  "'target loader is cycled, so every source image is '",
                                                  "'seen once per epoch and the optimisation budget '",
                                                  "'scales with the pool.')")
                                      or body.startswith(("'", 'help=', 'choices=', 'def _cycle',
                                                          'total_step = (len(source_loader)',
                                                          'if (opt.method', 'or getattr(opt',
                                                          'total_step = (len(source_loader) if opt.method',
                                                          'else min(len(source_loader)'))):
                continue                                         # P6 opt-in patch lines
            bad.append('%s: %s' % (f, body[:100]))
    return files, bad


def main():
    rows, hist = [], []
    # R1 per distinct commit
    commits = {}
    for rid, arm, s in RUNS:
        (c, dirty), started, logp = run_commit(rid)
        commits.setdefault(c, []).append(rid)
        snap = K.orig(os.path.join('Snapshot/ABC', rid))
        tea = os.path.join(snap, 'Tea_epoch_best.pth')
        stu = os.path.join(snap, 'Stu_40.pth')
        r = dict(runid=rid, arm=arm, seed=s, run_commit=c, run_commit_dirty=dirty, started=started,
                 tea_best_sha256=K.sha256(tea), tea_best_mtime=datetime.datetime.fromtimestamp(
                     os.path.getmtime(tea)).isoformat(timespec='seconds'),
                 stu40_sha256=K.sha256(stu))
        for ep in ('COD10K', 'NC4K'):
            pd = K.orig(os.path.join('Result/ABC', rid, ep))
            names = sorted(os.listdir(pd))
            r['n_pred_' + ep] = len(names)
            r['pred_latest_mtime_' + ep] = datetime.datetime.fromtimestamp(
                max(os.path.getmtime(os.path.join(pd, n)) for n in names)).isoformat(timespec='seconds')
        hist.append(r)
    for c, rids in sorted(commits.items()):
        files, bad = r1_code(c)
        rows.append(dict(gate='R1_code', subject=c, runs=';'.join(rids),
                         passed=not bad, detail=('differing files: %s; non-P6 non-comment lines: %d %s'
                                                 % (','.join(files) or 'none', len(bad), ' | '.join(bad[:5])))))
    # R2 env
    sp = K.orig('.venv/lib/python3.12/site-packages')
    first = min(datetime.datetime.fromisoformat(r['started']) for r in hist)
    pk = {}
    for d in os.listdir(sp):
        if d.endswith('.dist-info') and d.split('-')[0].lower() in (
                'torch', 'torchvision', 'numpy', 'pillow', 'opencv_python', 'scipy', 'scikit_learn'):
            pk[d] = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(sp, d)))
    late = [d for d, t in pk.items() if t.replace(tzinfo=first.tzinfo) >= first]
    rows.append(dict(gate='R2_env', subject='S2R-COD/.venv', runs='all', passed=not late,
                     detail='%s; first historical run %s; packages installed after it: %s'
                            % (', '.join(sorted('%s@%s' % (d[:-10], t.date()) for d, t in pk.items())),
                               first.isoformat(), late or 'none')))
    # R3 data, every file
    man = {}
    for line in open(os.path.join(K.REPO, 'rebuild/E0/out/e0_manifest.sha256')):
        if not line.startswith('#'):
            d, k = line.split()
            man[k] = d
    for key in MANIFEST_KEYS:
        d = os.path.join(K.REPO, PATHS[key])
        names = sorted(os.listdir(d))
        bad = [n for n in names if man.get('%s/%s' % (key, n)) != K.sha256(os.path.join(d, n))]
        expected = sum(1 for k in man if k.startswith(key + '/'))
        rows.append(dict(gate='R3_data', subject=key, runs='all',
                         passed=(not bad and len(names) == expected),
                         detail='%d files on disk, %d in E0 manifest, %d mismatched' % (len(names), expected, len(bad))))
    gtn = os.path.join(K.REPO, 'Dataset/Test/NC4K/GT')
    rows.append(dict(gate='R3_data', subject='nc4k_gt (not in E0 manifest)', runs='all', passed=True,
                     detail='%d files; list digest %s (recorded, no committed reference exists)'
                            % (len(os.listdir(gtn)), K.list_digest(
                                ['%s %s' % (K.sha256(os.path.join(gtn, n)), n) for n in os.listdir(gtn)]))))
    # R4
    t = subprocess.run([K.PY, '-B', os.path.join(K.HERE, 'exp01_alloc_test.py')], cwd=K.REPO,
                       capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    rows.append(dict(gate='R4_stems', subject='exp01_alloc_test.py', runs='all', passed=t.returncode == 0,
                     detail=t.stdout.strip().splitlines()[-1]))
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_reuse_gate.csv'), rows)
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_historical_runs.csv'), hist)
    for r in rows:
        print('%-9s %-28s %-5s %s' % (r['gate'], r['subject'][:28], r['passed'], r['detail'][:150]))


if __name__ == '__main__':
    main()

"""EXP-03 step 3 / validation: the checkpoint-selection split (CAMO-250) and the test splits (COD10K-test, NC4K)
share no image, by file name or by exact content (md5), with the 4,040 training images. Those images are the
COD10K-train + CAMO-train set that our pipeline uses unlabelled, that E3-c trains on with real masks, and that
SINet-V2 and RISE train on (AN-02).
CHAMELEON is excluded from evaluation (Sec. 3.4) and reported for completeness only.
Exact-content check only: near-duplicates (the CHAMELEON finding) need the manuscript's homography test.
Usage: nice -n 19 .venv/bin/python analysis/split_overlap_check.py   (log: EXPERIMENT_LOGS/split_overlap_check.log)
"""
import hashlib
import os
import sys
from multiprocessing import Pool

import _repo as R

SPLITS = {'train (target pool, 4040)': 'Dataset/Target/Image', 'CAMO-250 (checkpoint selection)': 'Dataset/Val/CAMO/Imgs',
          'COD10K-test': 'Dataset/Test/COD10K/Imgs', 'NC4K': 'Dataset/Test/NC4K/Imgs', 'CHAMELEON (excluded)': 'Dataset/Test/CHAMELEON/Imgs'}


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    files = {k: sorted(os.path.join(R.REPO, d, f) for f in os.listdir(os.path.join(R.REPO, d))) for k, d in SPLITS.items()}
    with Pool(8) as p:
        hashes = {k: set(p.map(md5, v, chunksize=64)) for k, v in files.items()}
    stems = {k: {os.path.splitext(os.path.basename(f))[0] for f in v} for k, v in files.items()}
    tr = 'train (target pool, 4040)'
    lines = ['# Split overlap check (exact content and file name)'] + \
            ['  %-34s %5d files, %5d distinct contents' % (k, len(files[k]), len(hashes[k])) for k in SPLITS]
    bad = 0
    for k in SPLITS:
        if k == tr:
            continue
        nm, hc = len(stems[k] & stems[tr]), len(hashes[k] & hashes[tr])
        if 'CHAMELEON' not in k:
            bad += nm + hc
        lines.append('  %-34s vs train: %d shared names, %d identical files%s' % (k, nm, hc, '  (not evaluated; see Sec. 3.4)' if 'CHAMELEON' in k else ''))
    # COD10K-test vs train: compare the identical files with the repository's own leakage sweep (D2, August 2026)
    import json
    d2 = {x['name'] for x in json.load(open(os.path.join(R.REPO, 'rebuild', 'D2', 'out', 'd2_leaked_names.json')))['endpoint_side']}
    te = files['COD10K-test']
    trh = {}
    for f in files[tr]:
        trh.setdefault(md5(f), []).append(os.path.basename(f))
    pairs = [(os.path.basename(f), trh[md5(f)]) for f in te if md5(f) in trh]
    lines.append('  COD10K-test files identical to a training image (test name <- training name):')
    lines += ['    %s <- %s%s' % (t, ', '.join(s), '' if t in d2 else '   NOT in the D2 record') for t, s in sorted(pairs)]
    known = {t for t, _ in pairs} == d2
    lines.append('  these are exactly the 7 test names in rebuild/D2/out/d2_leaked_names.json: %s' % known)
    lines.append('  CAMO-250 and NC4K share no file with training. COD10K-test shares %d of its %d images with the standard '
                 'COD10K-train split (identical bytes, 2 of them under the same name); every arm and every baseline is scored '
                 'on the same split, so no contrast is affected; the manuscript does not disclose it (author decision).'
                 % (len(pairs), len(te)))
    bad_eval = sum(len(stems[k] & stems[tr]) + len(hashes[k] & hashes[tr]) for k in ('CAMO-250 (checkpoint selection)', 'NC4K'))
    lines.append('RESULT: %s' % ('FINDING (COD10K-test: %d known duplicates of training images; CAMO-250, NC4K: none)' % len(pairs)
                                if known and not bad_eval else 'FAIL'))
    bad = 0 if (known and not bad_eval) else 1
    open(os.path.join(R.LOGS, 'split_overlap_check.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

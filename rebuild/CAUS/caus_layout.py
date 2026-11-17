#!/usr/bin/env python
"""CAUS -- materialise the read-only input layout inside this worktree, as leaf symlinks.

Idempotent. Creates REAL parent directories and a SYMLINK only at each leaf listed in LINKS,
so every directory any trainer or script writes into is a real directory of this worktree.
An existing correct link is kept; anything else at a link path is a HALT (never replaced).

Usage:  <shared venv python> rebuild/CAUS/caus_layout.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402

# (path relative to the repo root) -- the same relative path in the original copy is the target.
LINKS = (
    'Dataset/Target',                       # 4040 unlabelled target images (read by train + CLS)
    'Dataset/Test',                         # COD10K / NC4K endpoints (+ withdrawn CHAMELEON)
    'Dataset/Val',                          # CAMO-250, checkpoint selection only
    'Dataset/Source/HKU-IS',                # authors' base pool, 4447 pairs
    'Dataset/Source/HKU-IS_raw',            # raw foregrounds + raw GT (selection space source)
    'Dataset/LAKERED/output/HKU-IS',        # the 4447 LAKE-RED renders + masks
    'Dataset/LAKERED/input/HKU-IS',         # LAKE-RED staging inputs (declared input only)
    'Dataset/chameleon_new',                # declared input only; never an endpoint
    'rebuild/E0/cache',                     # frozen embeddings (dinoL518 etc.)
    'Src/model/SINet/resnet50-11ad3fa6.pth',  # SINet ImageNet backbone
    'Result/SINet/S2C',                     # committed S2C predictions (scorer validation)
    'Snapshot/SINet/S2C/Stu_40.pth',        # S2C student, read by inference-only checks
    'Snapshot/SINet/S2C/Tea_epoch_best.pth',  # S2C teacher, read by inference-only checks
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='verify only; create nothing')
    args = ap.parse_args()
    bad = []
    for rel in LINKS:
        dst = os.path.join(K.REPO, rel)
        src = K.orig(rel)
        if not os.path.exists(src):
            bad.append('missing source %s' % src)
            continue
        if os.path.islink(dst):
            if os.readlink(dst) != src:
                bad.append('wrong link %s -> %s' % (dst, os.readlink(dst)))
            continue
        if os.path.exists(dst):
            bad.append('non-link already present at %s (left untouched)' % dst)
            continue
        if args.check:
            bad.append('absent %s' % dst)
            continue
        parent = os.path.dirname(dst)
        # every parent must be a real directory inside the worktree
        p = parent
        while p != K.REPO:
            if os.path.islink(p):
                raise SystemExit('CAUS LAYOUT HALT: parent %s is a symlink' % p)
            p = os.path.dirname(p)
        K.assert_writable(parent)
        os.makedirs(parent, exist_ok=True)
        os.symlink(src, dst)
        print('linked %-45s -> %s' % (rel, src))
    if bad:
        print('\n'.join(bad))
        raise SystemExit('CAUS LAYOUT: %d problem(s)' % len(bad))
    print('layout OK: %d leaf links' % len(LINKS))


if __name__ == '__main__':
    main()

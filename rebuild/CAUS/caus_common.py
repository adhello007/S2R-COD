#!/usr/bin/env python
"""CAUS -- constants and the write guard for the Reviewer-Caus rebuttal work (EXP-01 et al.).

This worktree (rebuttal/Caus-oracle-scope) holds the code at the pre-rebuttal base 8d1d079.
Gitignored inputs -- datasets, embedding caches, backbone weights, historical checkpoints and
predictions -- live only in the ORIGINAL working copy and are read from it, never written.

Two rules make that safe:
  1. Inputs enter this worktree only as LEAF symlinks (caus_layout.py). No directory that any
     code writes into is ever a symlink, so a write cannot fall through into the original copy.
  2. Every path CAUS code writes is passed through assert_writable() first, which resolves it
     and refuses anything outside this worktree.
"""

import hashlib
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REBUILD = os.path.dirname(HERE)
REPO = os.path.dirname(REBUILD)                                     # this worktree
ORIG = os.path.join(os.path.dirname(REPO), 'S2R-COD')               # original copy, READ-ONLY
# The shared environment is the uv venv in the original copy (prompt "s2r-cod"). It is used
# read-only through its interpreter; nothing is ever installed into it, and it is deliberately
# NOT symlinked into this worktree, so no uv command run here can touch it.
PY = os.path.join(ORIG, '.venv', 'bin', 'python')
CAUS_OUT = os.path.join(REPO, 'rebuild', 'REBUTTAL', 'ICLR2027_REBUTTAL_Caus', 'STUDENT_RESULTS')
TABLES = os.path.join(CAUS_OUT, 'RESULT_TABLES')
LOGS = os.path.join(CAUS_OUT, 'EXPERIMENT_LOGS')
FIGS = os.path.join(CAUS_OUT, 'FIGURES')
RUNS_ROOT = os.path.join(REPO, 'Result', 'CAUS_RUNS')               # gitignored by /Result*

BASE_COMMIT = '8d1d0795fc4e19474d51f89adf0c2d8fb977f313'


def assert_writable(path):
    """Resolve `path` and refuse it unless it lies inside this worktree."""
    rp = os.path.realpath(path)
    if not (rp == REPO or rp.startswith(REPO + os.sep)):
        raise SystemExit('CAUS GUARD: refusing write outside the worktree: %s -> %s' % (path, rp))
    return rp


def orig(rel):
    """Absolute path of a file in the original copy (for reading only)."""
    return os.path.join(ORIG, rel)


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        while True:
            b = fh.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def list_digest(items):
    """sha256 over a sorted list of strings, newline-joined."""
    return hashlib.sha256('\n'.join(sorted(items)).encode()).hexdigest()


def git_head():
    try:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'],
                                        cwd=REPO, text=True).strip()
        return sha + (' (dirty)' if dirty else '')
    except Exception as e:                                          # pragma: no cover
        return 'unknown (%s)' % e


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')


def save_json(path, obj):
    assert_writable(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=2, sort_keys=False, default=str)
        fh.write('\n')


def write_csv(path, rows, fields=None):
    import csv
    assert_writable(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = fields or list(rows[0].keys())
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='raise')
        w.writeheader()
        for r in rows:
            w.writerow(r)

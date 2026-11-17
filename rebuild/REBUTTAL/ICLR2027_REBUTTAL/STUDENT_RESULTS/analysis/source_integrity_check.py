"""Audit check: re-hash every input file listed in rebuild/E0/out/e0_manifest.sha256 (renders, base pool, masks,
target images, HKU-IS sources) against its committed digest. The RL5B runner deleted the partial folders of
interrupted runs, including pseudo-label pools that held hardlinks to these files. This check shows whether
any source file was changed or lost.
Usage: nice -n 19 taskset -c 40-47 .venv/bin/python analysis/source_integrity_check.py
Writes EXPERIMENT_LOGS/source_integrity_check.log; exit code 1 on any mismatch or missing file.
"""
import hashlib
import os
import sys
from multiprocessing import Pool

import _repo as R

sys.path.insert(0, os.path.join(R.REPO, 'rebuild'))
import common as C   # noqa: E402  (rebuild/common.py: INPUTS, key -> directory; as bridge_check.py)


def h(args):
    key, fname, want = args
    full = os.path.join(R.REPO, C.INPUTS[key]['path'], fname)
    if not os.path.exists(full):
        return key, fname, 'MISSING'
    d = hashlib.sha256(open(full, 'rb').read()).hexdigest()
    return key, fname, 'OK' if d == want else 'CHANGED'


def main():
    jobs = []
    for line in open(os.path.join(R.REPO, 'rebuild', 'E0', 'out', 'e0_manifest.sha256')):
        if line.startswith('#') or not line.strip():
            continue
        want, p = line.strip().split(None, 1)
        key, _, fname = p.strip().partition('/')
        if key in C.INPUTS:
            jobs.append((key, fname, want))
    with Pool(8) as pool:
        res = pool.map(h, jobs, chunksize=256)
    by = {}
    for k, _, st in res:
        by.setdefault(k, {}).setdefault(st, 0)
        by[k][st] += 1
    bad = [(k, f, st) for k, f, st in res if st != 'OK']
    lines = ['# Source integrity re-check against rebuild/E0/out/e0_manifest.sha256 (%d files)' % len(res)]
    lines += ['  %-12s %s' % (k, ', '.join('%s %d' % kv for kv in sorted(v.items()))) for k, v in sorted(by.items())]
    lines += ['  %s %s/%s' % (st, k, f) for k, f, st in bad[:50]]
    lines.append('RESULT: %s' % ('PASS' if not bad else 'FAIL (%d files)' % len(bad)))
    open(os.path.join(R.LOGS, 'source_integrity_check.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

"""Audit check (post hoc): the per-run verification checked pool image counts, not pool content. This script
re-hashes, now, the Image and GT folders of every pool that a completed CDR or EQ run trained on. It compares
them with the digests recorded when the pools were built and gated, before any run: rebuild/ABC/out/{eq,cdr,
cdr_lu}/abc_pools.json, committed in 0146abc and 49383c0.
Training never writes into these folders: CLS writes into a separate _iteration2 copy and unlinks before every
write. Equality now therefore means each run trained on exactly the gated pool, including its injected set.
Usage: nice -n 19 taskset -c 40-47 .venv/bin/python analysis/pool_integrity_check.py
Writes EXPERIMENT_LOGS/pool_integrity_check.log; exit code 1 on any mismatch.
"""
import json
import os
import sys
from multiprocessing import Pool

import _repo as R

sys.path.insert(0, os.path.join(R.REPO, 'rebuild'))
import common as C   # noqa: E402  (rebuild/common.py: dir_digest)


def one(args):
    tag, rid, rec = args
    root = os.path.join(R.REPO, rec['source_root'])
    _, hi, ni = C.dir_digest(os.path.join(root, 'Image'))
    _, hg, ng = C.dir_digest(os.path.join(root, 'GT'))
    return tag, rid, hi == rec['image_digest'], hg == rec['gt_digest'], ni, ng


def main():
    ev = [json.loads(l) for l in open(os.path.join(R.REPO, 'rebuild', 'RL5B', 'out', 'queue_events.jsonl'))]
    done = {e['job'] for e in ev if e.get('kind') == 'job_done'}
    jobs = []
    for tag in ('eq', 'cdr', 'cdr_lu'):
        pools = json.load(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', tag, 'abc_pools.json')))['pools']
        jobs += [(tag, rid, rec) for rid, rec in pools.items() if rid in done and ('CDR' in rid or tag == 'eq')]
    with Pool(8) as p:
        res = p.map(one, jobs)
    bad = [r for r in res if not (r[2] and r[3])]
    lines = ['# Pool integrity (post hoc) for %d pools of completed CDR/EQ runs' % len(res)]
    for tag in ('eq', 'cdr', 'cdr_lu'):
        sub = [r for r in res if r[0] == tag]
        lines.append('  %-7s %d pools, image+GT digests equal to the gated record: %d' % (tag, len(sub), sum(r[2] and r[3] for r in sub)))
    lines += ['  MISMATCH %s/%s image %s gt %s (n %s/%s)' % r for r in bad]
    lines.append('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    open(os.path.join(R.LOGS, 'pool_integrity_check.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

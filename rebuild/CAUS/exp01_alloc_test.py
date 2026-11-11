#!/usr/bin/env python
"""CAUS EXP-01 -- tests for exp01_alloc.py. Exit code 0 iff every assertion holds.

1. The committed code path reproduces C10, CORACLE, CSHUF, CINV and B_s{42,43,45} stem lists
   byte-for-byte against the committed stem files (the regression guard: nothing drifted).
2. Every EXP-01 arm: integer quotas, sum == 1000, 75 entries, non-negative, exactly 1000
   distinct selected stems, every stem in the 4447-render pool, deterministic on re-call.
3. Every shuffle / inversion has an IDENTICAL sorted quota multiset to its parent shape.
4. OR-TOP-k funds exactly the k highest-err clusters, equal split.
5. An independent re-implementation of the quota rules (no shared helper) agrees.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                             # noqa: E402

import exp01_alloc as X                                        # noqa: E402

FAILS = []


def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        FAILS.append(msg)


def main():
    # 1 -- regression against committed selections
    for key in ('C10', 'CORACLE', 'CSHUF', 'CINV'):
        check(X.stems(key) == X.committed_stems(key), '%s reproduces committed stem file' % key)
    for s in X.SEEDS:
        check(X.stems('B', s) == X.committed_stems('B_s%d' % s), 'B_s%d reproduces committed stem file' % s)

    pool = set(os.path.splitext(f)[0] for f in os.listdir(
        os.path.join(X.A.C.REPO, 'Dataset/Source/HKU-IS_raw/imgs')))
    err, prov = X.oracle_err()
    check(prov['oracle_uses_endpoint_labels'] is True, 'oracle provenance is declared endpoint-leaky')

    # 2 -- integrity of every new arm
    for arm in X.NEW_ARMS:
        q, _ = X.quota(arm)
        q2, _ = X.quota(arm)
        st = X.stems(arm)
        check(q.dtype.kind == 'i' and len(q) == 75 and q.min() >= 0 and int(q.sum()) == 1000,
              '%s: 75 non-negative integer quotas summing to 1000' % arm)
        check(np.array_equal(q, q2) and st == X.stems(arm), '%s: deterministic' % arm)
        check(len(st) == 1000 and len(set(st)) == 1000 and set(st) <= pool,
              '%s: 1000 distinct stems, all in the 4447 pool' % arm)

    # 3 -- same-shape controls
    for child, parent in (('ORTOP10SHUF', 'ORTOP10'), ('ORTOP5SHUF', 'ORTOP5'),
                          ('ORPROPSHUF', 'ORPROP'), ('ORPROPINV', 'ORPROP')):
        a, b = X.quota(child)[0], X.quota(parent)[0]
        check(sorted(a.tolist()) == sorted(b.tolist()) and not np.array_equal(a, b),
              '%s has the identical sorted multiset as %s and a different assignment' % (child, parent))

    # 4 -- top-k definition
    top = np.argsort(-err, kind='stable')
    for arm, k in (('ORTOP10', 10), ('ORTOP5', 5)):
        q = X.quota(arm)[0]
        check(set(np.flatnonzero(q).tolist()) == set(top[:k].tolist()) and
              set(q[q > 0].tolist()) == {1000 // k}, '%s funds exactly the top-%d err clusters equally' % (arm, k))

    # 5 -- independent re-implementation of OR-PROP (plain Python, no shared helper)
    w = [max(e, 0.0) + 1e-6 * max(err) for e in err.tolist()]
    ex = [1000 * x / sum(w) for x in w]
    base = [int(np.floor(v)) for v in ex]
    rem = 1000 - sum(base)
    frac = sorted(range(75), key=lambda i: (-(ex[i] - base[i]), i))
    for i in frac[:rem]:
        base[i] += 1
    check(base == X.quota('ORPROP')[0].tolist(), 'OR-PROP agrees with an independent largest-remainder')

    print('\n%d failure(s)' % len(FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == '__main__':
    main()

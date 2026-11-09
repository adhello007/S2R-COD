"""Unit test for the RL5B allocation additions to rebuild/ABC/abc_common.py.

Proves that the additive CDR code paths leave every committed arm byte-identical, and that the
new paths do what they claim:

  T1  tau = 1.0, identity permutation -> the 75 committed quotas (rebuild/DIAG/out/diag_cluster_table.csv
      'alloc'), the committed C10 stem list (rebuild/ABC/out/abc_stems_C_a1.0.txt, sha256 58333d3c...),
      and C1_CELL[1.0] in full.
  T2  committed arms unchanged: CSHUF, CINV, CORACLE and B_s42/B_s50 reproduce their committed stem
      lists byte for byte.
  T3  the explicit-permutation kind ('cdr:<arm>') given CSHUF's own sigma reproduces CSHUF exactly.
  T4  uniform kind: quotas 14 x 25 (clusters 0-24) + 13 x 50, sum 1000, cell == UNIFORM_CELL.
  T5  expected_cell() of every committed C-family arm is exactly C1_CELL[alpha].

Usage: .venv/bin/python test_alloc_modes.py     (exit code 0 = all pass; log to EXPERIMENT_LOGS)
"""
import csv
import hashlib
import os
import sys

import numpy as np

import _repo as R
import abc_common as A

OUT = os.path.join(R.REPO, 'rebuild', 'ABC', 'out')
RESULTS = []


def check(name, cond, detail=''):
    RESULTS.append((name, bool(cond), detail))
    print('%-4s %s %s' % ('PASS' if cond else 'FAIL', name, detail), flush=True)


def stems_sha(stems):
    return hashlib.sha256(('\n'.join(stems) + '\n').encode()).hexdigest()


def file_sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def quotas(alpha, es_perm=None):
    import c1_space
    from c1_targeted_vs_random import softmax_alloc, largest_remainder
    sp = c1_space.load_space(A.EMBEDDER)
    sigma, _ = A.es_permutation(sp.es, es_perm)
    es = sp.es if es_perm is None else sp.es[sigma]
    p = np.full(sp.k, 1.0 / sp.k) if es_perm == 'uniform' else softmax_alloc(es, alpha)
    return largest_remainder(p, A.BUDGET)


def main():
    # T1
    committed_q = [int(r['alloc']) for r in sorted(csv.DictReader(open(os.path.join(
        R.REPO, 'rebuild', 'DIAG', 'out', 'diag_cluster_table.csv'))), key=lambda r: int(r['cluster']))]
    q = quotas(1.0, None)
    check('T1a quotas(tau=1, identity) == committed 75 quotas', list(q) == committed_q,
          'sum %d max %d' % (q.sum(), q.max()))
    st, cell = A.arm_c_stems(1.0, None)
    ref = os.path.join(OUT, 'abc_stems_C_a1.0.txt')
    check('T1b C10 stem list byte-identical to committed', stems_sha(st) == file_sha(ref),
          'sha %s' % stems_sha(st)[:16])
    check('T1c C10 cell == C1_CELL[1.0] (all 5 keys)',
          all(cell[k] == A.C1_CELL[1.0][k] for k in A.C1_CELL[1.0]),
          str({k: cell[k] for k in A.C1_CELL[1.0]}))
    # T2
    for arm, path in (('CSHUF', 't2/abc_stems_CSHUF.txt'), ('CINV', 't2/abc_stems_CINV.txt'),
                      ('CORACLE', 'or/abc_stems_CORACLE.txt')):
        st, _ = A.arm_c_stems(A.ARM_ALPHA[arm], A.ARM_ES_PERM[arm])
        check('T2 %s stem list byte-identical to committed' % arm,
              stems_sha(st) == file_sha(os.path.join(OUT, path)))
    for seed, path in ((42, 'abc_stems_B_s42.txt'), (50, 'se/abc_stems_B_s50.txt')):
        check('T2 B_s%d stem list byte-identical to committed' % seed,
              stems_sha(A.arm_b_stems(seed)) == file_sha(os.path.join(OUT, path)))
    # T3 -- a temporary in-memory CDR entry carrying CSHUF's sigma
    import c1_space
    sp = c1_space.load_space(A.EMBEDDER)
    sig_cshuf, info = A.es_permutation(sp.es, 'shuffled')
    A.CDR['CDRSELFTEST'] = dict(mode='permuted', tau=1.0, sigma=[int(x) for x in sig_cshuf], draw_index=None)
    st_t3, cell_t3 = A.arm_c_stems(1.0, 'cdr:CDRSELFTEST')
    check('T3 cdr: kind with CSHUF sigma == committed CSHUF stems',
          stems_sha(st_t3) == file_sha(os.path.join(OUT, 't2/abc_stems_CSHUF.txt')),
          'rho %+.5f (CSHUF %+.5f)' % (cell_t3['perm_rho'], info['perm_rho']))
    del A.CDR['CDRSELFTEST']
    # T4
    qu = quotas(None, 'uniform')
    check('T4a uniform quotas: 14 x clusters 0-24, 13 x clusters 25-74, sum 1000',
          list(qu) == [14] * 25 + [13] * 50 and qu.sum() == 1000)
    st_u, cell_u = A.arm_c_stems(1.0, 'uniform')
    check('T4b uniform cell == UNIFORM_CELL', all(cell_u[k] == A.UNIFORM_CELL[k] for k in A.UNIFORM_CELL),
          str({k: cell_u[k] for k in A.UNIFORM_CELL}))
    check('T4c uniform selects 1000 distinct stems', len(set(st_u)) == 1000 == len(st_u))
    # T5
    for arm in ('C10', 'CSHUF', 'CINV', 'CORACLE', 'C10FX'):
        check('T5 expected_cell(%s) is C1_CELL[alpha]' % arm, A.expected_cell(arm) is A.C1_CELL[A.ARM_ALPHA[arm]])
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    lines = ['test_alloc_modes: %d/%d PASS' % (len(RESULTS) - n_fail, len(RESULTS))] + \
            ['%s %s %s' % ('PASS' if ok else 'FAIL', n, d) for n, ok, d in RESULTS]
    open(os.path.join(R.LOGS, 'test_alloc_modes.log'), 'w').write('\n'.join(lines) + '\n')
    print(lines[0])
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""CAUS EXP-01 -- quota vectors and stem selections for the different-SHAPE oracle arms.

Specification: rebuild/CAUS/PREREGISTRATION_EXP01.md (TH-01 / EXP-01 of the Caus guide).

Nothing is re-implemented that already exists. Every arm reuses the COMMITTED selector
unchanged -- C1's largest_remainder, rank_by_centroid (R2 grey-128 cutout, dinoL518),
serving_orders['desc_nc'] and greedy_select -- so the ONLY thing an EXP-01 arm changes
relative to C10 / CORACLE is the integer quota vector handed to that selector.

Arms (display name -> file-safe name):
  OR-PROP        ORPROP       q_j ~ N * w_j / sum(w),  w_j = max(err_j, 0) + eps,
                              eps = 1e-6 * max(err); largest remainder, ties by ascending index
  OR-TOP10       ORTOP10      100 to each of the 10 highest-err clusters (stable argsort of -err)
  OR-TOP5        ORTOP5       200 to each of the 5 highest-err clusters
  OR-TOP10-SHUF  ORTOP10SHUF  OR-TOP10's quota vector permuted by the frozen shuffle rule
  OR-TOP5-SHUF   ORTOP5SHUF   (quota-only) OR-TOP5 permuted by the frozen shuffle rule
  OR-PROP-SHUF   ORPROPSHUF   (quota-only) OR-PROP permuted by the frozen shuffle rule
  OR-PROP-INV    ORPROPINV    (quota-only) OR-PROP rank-reversed against err (deterministic)

err is the CORACLE oracle vector: abc_common.oracle_error(), i.e. the committed per-cluster
mean (1 - S_alpha) of SINet/S2C on COD10K-test. READING IT IS AN ENDPOINT-LABEL READ; every
arm here is a declared, intentionally leaky diagnostic (oracle_score_source =
endpoint-label-leaky), exactly as CORACLE is (PREREGISTRATION_OR.md OR.0).

Frozen shuffle rule: the first offset `off` in 0..63 such that
sigma = numpy.random.default_rng(NS + off).permutation(75) has no fixed point and
|scipy.stats.spearmanr(q[sigma], err).statistic| <= 0.10; q_shuf = q[sigma]. NS is 920000
(OR-PROP), 930000 (OR-TOP10), 940000 (OR-TOP5). Chosen by rule, never by inspection.

TRAINS NOTHING. Deterministic: no argument depends on the training seed.
"""

import csv
import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _p in (_HERE, _REBUILD, os.path.join(_REBUILD, 'C1'), os.path.join(_REBUILD, 'ABC')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                             # noqa: E402

import abc_common as A                                         # noqa: E402

BUDGET = A.BUDGET                     # 1000
K = 75
EPS_SCALE = 1e-6
SHUF_NS = {'ORPROP': 920_000, 'ORTOP10': 930_000, 'ORTOP5': 940_000}
SHUF_TRIES = 64
SHUF_MAX_RHO = 0.10
JACCARD_GATE = A.T2_MAX_JACCARD       # 0.50, inherited from T2.7 / OR.2.4

TRAINED_ARMS = ('ORTOP10', 'ORTOP10SHUF', 'ORPROP', 'ORTOP5')      # 12 runs = 4 x {42,43,45}
QUOTA_ONLY_ARMS = ('ORPROPSHUF', 'ORPROPINV', 'ORTOP5SHUF')
NEW_ARMS = TRAINED_ARMS + QUOTA_ONLY_ARMS
DISPLAY = {'ORPROP': 'OR-PROP', 'ORTOP10': 'OR-TOP10', 'ORTOP5': 'OR-TOP5',
           'ORTOP10SHUF': 'OR-TOP10-SHUF', 'ORTOP5SHUF': 'OR-TOP5-SHUF',
           'ORPROPSHUF': 'OR-PROP-SHUF', 'ORPROPINV': 'OR-PROP-INV',
           'C10': 'C10', 'CORACLE': 'CORACLE', 'CSHUF': 'CSHUF', 'CINV': 'CINV', 'B': 'B'}
SEEDS = (42, 43, 45)


def _space():
    import c1_space
    return c1_space.load_space(A.EMBEDDER)


def oracle_err():
    vec, prov = A.oracle_error()
    return vec, prov


def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


def _lr(p):
    from c1_targeted_vs_random import largest_remainder
    return largest_remainder(p, BUDGET)


def q_prop(err):
    w = np.maximum(err, 0.0) + EPS_SCALE * float(err.max())
    return _lr(w / w.sum())


def q_topk(err, n):
    if BUDGET % n:
        raise RuntimeError('EXP01 HALT: budget %d not divisible by top-k %d' % (BUDGET, n))
    order = np.argsort(-err, kind='stable')
    q = np.zeros(K, dtype=np.int64)
    q[order[:n]] = BUDGET // n
    return q


def frozen_shuffle(q, err, ns):
    for off in range(SHUF_TRIES):
        sigma = np.random.default_rng(ns + off).permutation(K)
        if int((sigma == np.arange(K)).sum()) != 0:
            continue
        rho = spearman(q[sigma], err)
        if abs(rho) <= SHUF_MAX_RHO:
            return q[sigma], dict(perm_seed=int(ns + off), perm_rule='first no-fixed-point, '
                                  '|spearman|<=%.2f in %d draws' % (SHUF_MAX_RHO, SHUF_TRIES))
    raise RuntimeError('EXP01 HALT: no permutation in %d draws from %d met the rule' % (SHUF_TRIES, ns))


def rank_reverse(q, err):
    asc = np.argsort(err, kind='stable')
    sigma = np.empty(K, dtype=np.int64)
    sigma[asc] = asc[::-1]
    return q[sigma], dict(perm_seed=None, perm_rule='rank-reversed against err (deterministic)')


def quota(arm):
    """Integer quota vector (cluster order 0..74) and provenance for any EXP-01 arm."""
    err, _ = oracle_err()
    if arm == 'ORPROP':
        return q_prop(err), dict(perm_seed=None, perm_rule='none')
    if arm == 'ORTOP10':
        return q_topk(err, 10), dict(perm_seed=None, perm_rule='none')
    if arm == 'ORTOP5':
        return q_topk(err, 5), dict(perm_seed=None, perm_rule='none')
    if arm == 'ORTOP10SHUF':
        return frozen_shuffle(q_topk(err, 10), err, SHUF_NS['ORTOP10'])
    if arm == 'ORTOP5SHUF':
        return frozen_shuffle(q_topk(err, 5), err, SHUF_NS['ORTOP5'])
    if arm == 'ORPROPSHUF':
        return frozen_shuffle(q_prop(err), err, SHUF_NS['ORPROP'])
    if arm == 'ORPROPINV':
        return rank_reverse(q_prop(err), err)
    raise ValueError('unknown EXP-01 arm %r' % arm)


def reference_quota(arm):
    """C10 / CORACLE / CSHUF / CINV quota vectors, through the committed code path."""
    from c1_targeted_vs_random import softmax_alloc
    sp = _space()
    sigma, info = A.es_permutation(sp.es, A.ARM_ES_PERM[arm])
    es = sp.es if A.ARM_ES_PERM[arm] is None else sp.es[sigma]
    return _lr(softmax_alloc(es, A.ARM_ALPHA[arm])), info


def select(q):
    """The committed selector, unchanged. Returns (stems sorted by pool index, n_displaced, idx)."""
    from c1_targeted_vs_random import rank_by_centroid, serving_orders, greedy_select
    sp = _space()
    _, order = rank_by_centroid(sp)
    serving = serving_orders(q, sp.es)[A.SERVING]          # desc_nc reads the quota only
    idx, disp = greedy_select(q, order, serving)
    return [sp.names[i] for i in idx], int(disp), idx


def stems(arm, seed=None):
    """Stem list for any arm. B needs a seed; every other arm is seed-independent."""
    if arm == 'B':
        return A.arm_b_stems(seed)
    if arm in A.ARM_ALPHA:
        return A.arm_c_stems(A.ARM_ALPHA[arm], A.ARM_ES_PERM[arm])[0]
    return select(quota(arm)[0])[0]


def vec_hash(q):
    return hashlib.sha256(','.join(str(int(x)) for x in q).encode()).hexdigest()


def shape_hash(q):
    return vec_hash(sorted((int(x) for x in q), reverse=True))


def gini(x):
    """Gini of the quota vector over all 75 clusters (mean-absolute-difference form)."""
    x = np.asarray(x, dtype=np.float64)
    if x.sum() == 0:
        return 0.0
    return float(np.abs(x[:, None] - x[None, :]).sum() / (2 * len(x) ** 2 * x.mean()))


def properties(q):
    err, _ = oracle_err()
    sp = _space()
    p = np.asarray(q, dtype=np.float64) / BUDGET
    nz = p[p > 0]
    srt = np.sort(p)[::-1]
    return dict(
        quota_sum=int(np.sum(q)), clusters_funded=int((q > 0).sum()), max_quota=int(q.max()),
        top1_share=round(float(srt[0]), 5), top5_share=round(float(srt[:5].sum()), 5),
        entropy_norm=round(float(-(nz * np.log(nz)).sum() / np.log(K)), 5),
        hhi=round(float((p ** 2).sum()), 5), gini=round(gini(q), 5),
        tv_from_uniform=round(float(0.5 * np.abs(p - 1.0 / K).sum()), 5),
        spearman_q_err=round(spearman(q, err), 5), spearman_q_es=round(spearman(q, sp.es), 5),
        quota_sha256=vec_hash(q), shape_sha256=shape_hash(q))


def read_stem_file(path):
    with open(path) as fh:
        return [x for x in fh.read().split('\n') if x]


COMMITTED_STEMS = {
    'C10': 'rebuild/ABC/out/abc_stems_C_a1.0.txt',
    'CORACLE': 'rebuild/ABC/out/or/abc_stems_CORACLE.txt',
    'CSHUF': 'rebuild/ABC/out/se/abc_stems_CSHUF.txt',
    'CINV': 'rebuild/ABC/out/se/abc_stems_CINV.txt',
    'B_s42': 'rebuild/ABC/out/abc_stems_B_s42.txt',
    'B_s43': 'rebuild/ABC/out/abc_stems_B_s43.txt',
    'B_s45': 'rebuild/ABC/out/abc_stems_B_s45.txt',
}


def committed_stems(key):
    return read_stem_file(os.path.join(A.C.REPO, COMMITTED_STEMS[key]))

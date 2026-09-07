#!/usr/bin/env python
"""ABC -- the run table, the pool paths, and the arm stem selections.

Specification: rebuild/ABC/ABC_PLAN.md, approved before this file existed.
Decision rule: rebuild/ABC/PREREGISTRATION.md, committed and FROZEN.

One module owns the identity of a run, so no two scripts can disagree about
which directory an arm reads. RUNID is a pure function of (arch, arm, seed), and
every path a run writes is RUNID-prefixed -- including the CLS round-2 pool,
which CLS.py:16 derives from source_root alone. That is what makes collision
impossible rather than merely unlikely (ABC_PLAN.md A.2).

Arm C's stems are obtained by CALLING C1's committed selection code, never by
reimplementing it, so the selection is identical to the one C1 measured.

TRAINS NOTHING. Selects and names; the driver trains.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _p in (_REBUILD, os.path.join(_REBUILD, 'C1'), os.path.dirname(_REBUILD)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'ABC'
OUT = C.exp_dir(EXP, 'out')

# --- the locked decision set (ABC_PLAN.md A.0) ------------------------------
ARCHS = {
    'SINet':   dict(network='SINet',    batch=16, total_step=253,
                    last_epoch='039/040', ref_min=104.5, cls_stu='Stu_40.pth'),
    'SINetv2': dict(network='SINet-v2', batch=32, total_step=127,
                    last_epoch='099/100', ref_min=131.0, cls_stu='Stu_100.pth'),
}
ARMS = ('A0', 'A2', 'B', 'C10')          # C05 is the pre-registered secondary
ARM_ALPHA = {'C10': 1.0, 'C05': 0.5}
SEEDS = (42, 43, 45)
BUDGET = 1000
EMBEDDER = 'dinoL518'
SERVING = 'desc_nc'                      # C1's primary de-duplication order
DRAW_NS = 700_000                        # arm-B draw RNG namespace, per-seed

BASE_POOL = 'Dataset/Source/HKU-IS'                        # authors' pool
RAW_GT = 'Dataset/Source/HKU-IS_raw/gt'
REN_IMG = 'Dataset/LAKERED/output/HKU-IS/images'
REN_MSK = 'Dataset/LAKERED/output/HKU-IS/masks'
ENDPOINTS = ('COD10K', 'NC4K')           # CHAMELEON withdrawn; CAMO never an endpoint

# C1's committed allocation cell for (dinoL518, B=1000, R2_cut), per alpha.
# Deterministic functions of the allocation + selection, so ABC must reproduce
# them exactly or something drifted since C1. Source: rebuild/C1/out/c1_cells.csv.
C1_CELL = {
    1.0: dict(clusters_funded=75, max_alloc_share=0.194,
              alloc_entropy_norm=0.78644, tv_from_uniform=0.49253, n_displaced=370),
    0.5: dict(clusters_funded=40, max_alloc_share=0.509,
              alloc_entropy_norm=0.36203, tv_from_uniform=0.85906, n_displaced=115),
}


def runid(arch, arm, seed):
    return '%s_%s_s%d' % (arch, arm, seed)


def all_runs(arms=ARMS, archs=('SINet', 'SINetv2'), seeds=SEEDS):
    return [(a, m, s) for a in archs for m in arms for s in seeds]


def pool_dir(rid):
    return os.path.join('Dataset/Source/ABC', rid)


def cls_dir(rid):
    """Exactly what CLS.py:16 derives from source_root."""
    return pool_dir(rid).rstrip('/\\') + '_iteration2'


def snap_dir(rid):
    return os.path.join('Snapshot/ABC', rid)


def pred_dir(rid, endpoint):
    return os.path.join('Result/ABC', rid, endpoint)


def runlog(rid):
    return os.path.join('rebuild/ABC', rid + '.log')


# --- stems -----------------------------------------------------------------

def base_stems():
    """The 4447 foreground stems in the row order C1's arrays use."""
    return sorted(os.path.splitext(f)[0]
                  for f in os.listdir(os.path.join(C.REPO, 'Dataset/Source/HKU-IS_raw/imgs')))


def arm_b_stems(seed):
    """B uniformly WITHOUT replacement from the same 4447 pool. Per-seed draw
    (ABC_PLAN.md A.4): 'random' is a distribution over draws, not one draw."""
    stems = base_stems()
    rng = np.random.default_rng(DRAW_NS + seed)
    idx = np.sort(rng.choice(len(stems), size=BUDGET, replace=False))
    return [stems[i] for i in idx]


def arm_c_stems(alpha):
    """Reuse C1's committed selection. Returns (stems, measured_cell)."""
    import c1_space
    from c1_targeted_vs_random import (softmax_alloc, largest_remainder,
                                       rank_by_centroid, serving_orders,
                                       greedy_select)
    sp = c1_space.load_space(EMBEDDER)
    p = softmax_alloc(sp.es, alpha)
    alloc = largest_remainder(p, BUDGET)
    _, order = rank_by_centroid(sp)
    serving = serving_orders(alloc, sp.es)[SERVING]
    idx, disp = greedy_select(alloc, order, serving)
    cell = dict(
        clusters_funded=int((alloc > 0).sum()),
        max_alloc_share=round(float(alloc.max() / BUDGET), 5),
        alloc_entropy_norm=round(float(-(p[p > 0] * np.log(p[p > 0])).sum()
                                       / np.log(sp.k)), 5),
        tv_from_uniform=round(float(0.5 * np.abs(p - 1.0 / sp.k).sum()), 5),
        n_displaced=int(disp))
    return [sp.names[i] for i in idx], cell


def arm_added(arm, seed):
    """What an arm adds: (src_prefix, dst_prefix, stems, (img_dir, img_ext),
    (msk_dir, msk_ext)). The render pool's files already carry SOD_; the authors'
    pool's do not, so the source and destination prefixes differ for A2."""
    if arm == 'A0':
        return None, None, [], None, None
    if arm == 'A2':
        # Foreground-matched duplicates: the AUTHORS' image+GT of the stems arm B
        # drew at this seed. Isolates "is a LAKE-RED re-render worth anything over
        # the authors' own render of the same foreground" (ABC_PLAN.md A.3).
        return '', 'DUP_', arm_b_stems(seed), \
               (BASE_POOL + '/Image', '.jpg'), (BASE_POOL + '/GT', '.png')
    if arm == 'B':
        return 'SOD_', 'SOD_', arm_b_stems(seed), \
               (REN_IMG, '.jpg'), (REN_MSK, '.png')
    if arm in ARM_ALPHA:
        return 'SOD_', 'SOD_', arm_c_stems(ARM_ALPHA[arm])[0], \
               (REN_IMG, '.jpg'), (REN_MSK, '.png')
    raise ValueError('unknown arm %r' % arm)

#!/usr/bin/env python
"""T2-C -- uncertainty signals on the UNLABELED TARGET set, and their correlation
with COMMITTED endpoint error through the COMMITTED B1 partition.

INFERENCE ONLY. TRAINS NOTHING. Writes no checkpoint, builds no pool, fits no
partition artifact. Every primitive is B1's; this module adds only the per-pixel
signal fields, the shared boundary band, a seed-general target-label source, and
the gates.

Rule: leaf functions only. b1_allocation_signal.main() and
b1_es_error_correlation.main() unconditionally rewrite committed artifacts and are
never called from here.

Decision rule: rebuild/T2C/PREREGISTRATION_T2C.md (frozen).
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _pth in (_REBUILD, os.path.join(_REBUILD, 'B1'), os.path.join(_REBUILD, 'C1'),
             os.path.join(_REBUILD, 'E0'), os.path.dirname(_REBUILD)):
    if _pth not in sys.path:
        sys.path.insert(0, _pth)
import common as C                                            # noqa: E402
import b1_es_error_correlation as B1                           # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'T2C'
OUT = C.exp_dir(EXP, 'out')
B1_OUT = B1.OUT

TAG = 'dinoL518'
K = 75
COMMITTED_SEED = 0
N_SEEDS = 10                      # matches B1.N_SEEDS
MIN_TARGET_IN_CLUSTER = 5         # the second floor, b1_allocation_signal.py:171

ENTROPY_EPS = 1e-6
BAND_KSIZE = 3
BAND_ITERS = 2                    # width 2*iters = 4 px across a straight edge
BAND_THRESH = 0.5
MAX_EMPTY_BAND_FRAC = 0.05

ARCHS = ('SINet/S2C', 'SINet-v2/S2C')
ENS_ARMS = {'A0': 'PRIMARY', 'CSHUF': 'SENSITIVITY'}
ENS_SEEDS = (42, 43, 45)          # abc_common.py:56
# B1 net name -> the arch token in Snapshot/ABC/<arch>_<arm>_s<seed>
ABC_ARCH = {'SINet': 'SINet', 'SINet-v2': 'SINetv2'}


def _halt(msg):
    raise RuntimeError('T2C HALT: %s' % msg)


# ---------------------------------------------------------------------------
# per-pixel signal fields
# ---------------------------------------------------------------------------

def binary_entropy_map(prob, eps=ENTROPY_EPS):
    """Per-pixel binary entropy in BITS of a probability map.

    Base 2 only sets the scale: a base change is a positive scalar multiple of
    the per-image mean, so Spearman rho is exactly invariant to it. The clamp is
    NOT rho-neutral in principle -- a float32 sigmoid underflows below eps on
    confident background -- but H(1e-6) ~ 2.1e-5 bits, so its weight in a mean
    over 352*352 pixels is negligible. A 1e-12 variant is reported as a free
    robustness check. float64 throughout, so the clamp is well defined.
    """
    q = np.clip(np.asarray(prob, np.float64), eps, 1.0 - eps)
    return -(q * np.log2(q) + (1.0 - q) * np.log2(1.0 - q))


def ensemble_var_map(probs):
    """Per-pixel POPULATION variance (ddof=0) across ensemble members.

    The standard ensemble-uncertainty statistic, and it extends past 3 members
    unchanged. At n=3 the mean pairwise |delta| is a near-monotone function of
    the sd, so rho would be nearly identical -- a low-risk choice.

    Aggregation is NOT interchangeable, though: mean(var) is not a monotone
    function of mean(sd), so mean(sd) is reported as a separate robustness
    variant rather than treated as equivalent.
    """
    a = np.stack([np.asarray(p, np.float64) for p in probs], axis=0)
    if a.shape[0] < 2:
        _halt('ensemble needs >= 2 members, got %d' % a.shape[0])
    return a.var(axis=0, ddof=0)


def es_map(es_loss, pred, target):
    """Per-pixel ES field whose MEAN is exactly ESLoss.forward(pred, target).

    This is NOT a reimplementation. ESLoss makes exactly two reducing calls --
    F.l1_loss and F.binary_cross_entropy (Src/utils/tool.py:68, 75) -- and both
    accept reduction='none'. Passing it to the SAME two functions reproduces the
    committed scalar elementwise, PyTorch's BCE log-clamping included, with no
    hand-rolled log and no clamp semantics to get wrong.

    (Src/utils/tool.py:9 passes the legacy `reduce='none'` and is a live bug --
    preflight.py:653-663 flags it. The correct kwarg is `reduction='none'`.)

    use_weighted_bce=True is a HALT: the weighted branch is deliberately not
    implemented, so a reconfigured ESLoss breaks the run instead of silently
    changing the measurement. B1 hardcodes False (b1_es_error_correlation.py:131).
    """
    import torch
    import torch.nn.functional as F
    if getattr(es_loss, 'use_weighted_bce', False):
        _halt('ESLoss.use_weighted_bce is True; B1 measured the PGT instance '
              '(use_weighted_bce=False, MyTrain.py:306). Refusing to proceed.')
    gx = F.conv2d(pred, es_loss.sobel_x, padding=1)
    gy = F.conv2d(pred, es_loss.sobel_y, padding=1)
    edge_pred = torch.sqrt(gx ** 2 + gy ** 2 + 1e-8)
    tx = F.conv2d(target, es_loss.sobel_x, padding=1)
    ty = F.conv2d(target, es_loss.sobel_y, padding=1)
    edge_target = torch.sqrt(tx ** 2 + ty ** 2 + 1e-8)
    edge = F.l1_loss(edge_pred, edge_target, reduction='none')
    region = F.binary_cross_entropy(pred, target, reduction='none')
    return es_loss.a * edge + es_loss.b * region


def assert_es_map_identity(es_loss, pred, target, tol=1e-6):
    """Gate 4. Pure arithmetic on the SAME tensors in the SAME process, so the
    only admissible difference is float reduction order -- hence a tight tol."""
    m = float(es_map(es_loss, pred, target).mean().item())
    s = float(es_loss(pred, target).item())
    if abs(m - s) > tol:
        _halt('unreduced ES mean %.12g != ESLoss.forward %.12g (|d|=%.3e > %.1e)'
              % (m, s, abs(m - s), tol))
    return m, s


# ---------------------------------------------------------------------------
# the shared boundary band
# ---------------------------------------------------------------------------

def boundary_band(prob, thresh=BAND_THRESH, ksize=BAND_KSIZE, iters=BAND_ITERS):
    """Symmetric band straddling the teacher's predicted contour, or None.

    band = dilate(M, ones(k,k), iters) & ~erode(M, ones(k,k), iters)
    with M = prob >= thresh on the RAW sigmoid. Width is 2*iters px across a
    straight edge (iters outward, iters inward).

    ONE band per image, from the S2C teacher, SHARED by all three signals, so
    'boundary-restricted' names the same region in every row. A per-signal band
    would make each row's boundary a different region and confound the
    comparison invisibly.

    Extends rather than reuses d2r_reaudit.py:565-566, which applies the same
    3x3 square at iterations=1 but keeps an INNER-only band (fg - eroded).
    Symmetric here because entropy is highest STRADDLING the contour.

    cv2.erode's default border value is the morphological max, so an object
    touching the image edge is not eroded there. Inherited behaviour, and
    identical for every signal because the band is shared.

    Returns None when the band is empty (a globally unconfident teacher, or a
    saturated mask). Callers must treat None as 'this image contributes no
    boundary value' and count it; >5% empty is a HALT.
    """
    import cv2
    m = (np.asarray(prob, np.float64) >= thresh).astype(np.uint8)
    if m.sum() == 0 or m.sum() == m.size:
        return None
    k = np.ones((ksize, ksize), np.uint8)
    dil = cv2.dilate(m, k, iterations=iters)
    ero = cv2.erode(m, k, iterations=iters)
    band = (dil.astype(np.int16) - ero.astype(np.int16)) > 0
    return band if band.any() else None


def aggregate(field, band):
    """The two pre-registered aggregations of one per-pixel field.

    'whole' is the mean over all 352x352 pixels -- the closest analogue to ES's
    region term, and the reduction that reproduces the committed ES scalar. The
    ES map's outer 1-px ring carries a spurious zero-padding Sobel response; it
    is deliberately NOT masked, because the committed scalar includes it and
    masking would break the reproduction gate.
    """
    f = np.asarray(field, np.float64)
    return dict(whole=float(f.mean()),
                boundary=(None if band is None else float(f[band].mean())))


# ---------------------------------------------------------------------------
# target-side clustering, seed-general
# ---------------------------------------------------------------------------

def committed_assignment(tag=TAG):
    a = json.load(open(os.path.join(B1_OUT, 'b1_cluster_assignment_%s.json' % tag)))
    if a['k'] != K or a['seed'] != COMMITTED_SEED or a['embedder'] != tag:
        _halt('committed assignment is (k=%s, seed=%s, %s), expected (%d, %d, %s)'
              % (a['k'], a['seed'], a['embedder'], K, COMMITTED_SEED, tag))
    return a


def cluster_target_signal(tag, k, seed, sig, X=None, tnames=None):
    """Per-cluster mean of a TARGET-side per-image signal. {c: (mean, n)}.

    Generalises b1_allocation_signal.cluster_target_es over the k-means seed.
    That function returns None for every seed but the committed one (:141-142),
    so the pre-registered 10-seed standard deviation is unreachable through it --
    and the failure is a silent None, not an error. Hence this function, and
    hence it RAISES where B1's returns None.

    seed == COMMITTED_SEED : labels read from the committed assignment file, the
                             byte-for-byte partition C1/ABC/T2 consumed.
    seed != COMMITTED_SEED : labels from an IN-MEMORY B1.fit_kmeans refit on the
                             same D2-excluded embeddings. B1._KM_CACHE is a plain
                             dict (b1_es_error_correlation.py:425), so nothing is
                             written and no partition artifact is created.
    """
    a = committed_assignment(tag)
    if k != a['k']:
        _halt('k=%d does not match the committed partition k=%d' % (k, a['k']))
    if seed == a['seed']:
        names, labels = a['target_names'], [int(l) for l in a['target_labels']]
    else:
        if X is None or tnames is None:
            X, tnames, _ = B1.load_target(tag)
        if list(tnames) != list(a['target_names']):
            _halt('target name order drifted from the committed partition '
                  '(%d vs %d names)' % (len(tnames), len(a['target_names'])))
        names = tnames
        labels = [int(l) for l in B1.fit_kmeans(X, k, seed, tag).labels_]
    buckets = {}
    for nm, lab in zip(names, labels):
        if nm in sig and sig[nm] is not None:
            buckets.setdefault(int(lab), []).append(float(sig[nm]))
    return {c: (float(np.mean(v)), len(v)) for c, v in buckets.items()}


def assert_refit_matches_committed(tag=TAG):
    """Gate 5. If the seed-0 refit reproduces the committed labels exactly, the
    seeds 1-9 path is trustworthy. Exact equality is expected: the same
    deterministic KMeans(n_init=10, random_state=0) on the same X."""
    a = committed_assignment(tag)
    X, tnames, _ = B1.load_target(tag)
    if list(tnames) != list(a['target_names']):
        _halt('target names differ from the committed partition')
    got = [int(l) for l in B1.fit_kmeans(X, a['k'], a['seed'], tag).labels_]
    want = [int(l) for l in a['target_labels']]
    if got != want:
        from sklearn.metrics import adjusted_rand_score
        _halt('seed-0 refit does not reproduce the committed labels '
              '(ARI=%.6f); the seeds 1-9 error bar would not be comparable'
              % adjusted_rand_score(want, got))
    return len(got)


# ---------------------------------------------------------------------------
# the target-side invariant -- the most important gate in the experiment
# ---------------------------------------------------------------------------

def assert_target_side(sig, paths_opened, tag=TAG, arch='SINet/S2C'):
    """Gate 1. HALTS if any signal was computed anywhere but the target set.

    Same-side ES gives rho(MAE)=+0.8754 against cross-side +0.6284, and the two
    agree only at rho=0.5732. A same-side signal placed next to B1's +0.6284 is
    a publishable-looking, entirely non-comparable result -- and it is ONE
    argument to a loader, with nothing crashing and no existing gate firing.
    """
    a = committed_assignment(tag)
    tgt_rel = C.INPUTS['tgt']['path']                 # Dataset/Target/Image

    # A -- path provenance. Dataset/Target/ holds only Image/: no GT exists there,
    # so a target-side signal is ground-truth-free by filesystem construction.
    for p in paths_opened:
        rel = os.path.relpath(os.path.abspath(p), C.REPO)
        if not rel.startswith(tgt_rel):
            _halt('signal loader opened %r, which is outside %s' % (rel, tgt_rel))
        if 'Dataset/Test/' in rel or 'Dataset/Val/' in rel:
            _halt('signal loader opened an ENDPOINT path: %r' % rel)
    gt_here = [d for d in os.listdir(os.path.dirname(C.ipath('tgt')))
               if d.lower() != 'image']
    if gt_here:
        _halt('Dataset/Target/ unexpectedly contains %r; the GT-free premise '
              'no longer holds' % gt_here)

    # B -- key space. Target names carry .jpg; endpoint names are bare stems
    # (b1_target_es_*.csv vs b1_scores_*_test.csv). The two spaces are disjoint,
    # so a stem-keyed signal cannot pass this.
    keys = set(sig)
    missing = set(a['target_names']) - keys
    if missing:
        _halt('signal is missing %d of the %d committed target names (e.g. %r)'
              % (len(missing), len(a['target_names']), sorted(missing)[:3]))
    rows = B1.load_scores(arch, 'test')
    if rows is None:
        _halt('committed endpoint scores for %s/test are missing' % arch)
    clash = keys & {r['name'] for r in rows}
    if clash:
        _halt('signal keys intersect ENDPOINT stems (%d, e.g. %r) -- the signal '
              'was computed on the endpoint' % (len(clash), sorted(clash)[:3]))

    # C -- count.
    if len(sig) != C.INPUTS['tgt']['n']:
        _halt('signal covers %d images, expected %d (all of %s)'
              % (len(sig), C.INPUTS['tgt']['n'], tgt_rel))
    return dict(n_signal=len(sig), n_joined=len(a['target_names']),
                target_root=tgt_rel, endpoint_key_clash=0)


# ---------------------------------------------------------------------------
# the correlation -- a faithful mirror of b1_allocation_signal.faithful_correlation
# ---------------------------------------------------------------------------

def t2c_correlation(tag, k, seed, sig, arch='SINet/S2C', n_perm=2000,
                    min_n=B1.MIN_CLUSTER_N,
                    min_clusters=B1.MIN_CLUSTERS_FOR_RHO, X=None, tnames=None):
    """Per-cluster TARGET signal vs per-cluster ENDPOINT error.

    A faithful mirror of b1_allocation_signal.faithful_correlation:150-191, in a
    new file because B1's is committed and hardcodes ES. The `used` line below is
    COPIED VERBATIM from :170-171, so both floors are carried identically -- the
    >=15 endpoint floor (binding, 50 of 75 clusters) and the >=5 target floor
    (currently non-binding at 75/75, but carried because these signals are also
    target-side means and a cluster with 1-4 target images gives a meaningless
    mean). For the boundary aggregation the >=5 floor lands on the BAND-ELIGIBLE
    count, since images with an empty band contribute no value.

    Identity with B1 is not asserted by reading: run with the committed ES dict
    at seed 0 it must reproduce b1_faithful_correlation.json bit-identically
    (Gate 8).
    """
    ces = cluster_target_signal(tag, k, seed, sig, X, tnames)
    if X is None or tnames is None:
        X, tnames, _ = B1.load_target(tag)
    rows = B1.load_scores(arch, 'test')
    if rows is None:
        _halt('committed endpoint scores for %s/test are missing' % arch)
    amap, _ = B1.assign_clusters(X, tnames, k, seed, 'test', tag)
    err = {}
    for r in rows:
        c = amap.get(r['name'])
        if c is not None:
            err.setdefault(c, []).append(r)
    used = sorted(c for c in err
                  if len(err[c]) >= min_n and c in ces
                  and ces[c][1] >= MIN_TARGET_IN_CLUSTER)
    if len(used) < min_clusters:
        return dict(degenerate=True, clusters_used=len(used), k=k, tag=tag,
                    seed=seed, arch=arch)
    a = [ces[c][0] for c in used]
    out = dict(degenerate=False, k=k, tag=tag, seed=seed, arch=arch,
               clusters_used=len(used),
               n_target_in_used=int(sum(ces[c][1] for c in used)),
               signal_mean=float(np.mean(a)), signal_sd=float(np.std(a)))
    for e in B1.ERRORS:
        b = [float(np.mean([r[e] for r in err[c]])) for c in used]
        rho, p, ci = B1.spearman_perm(a, b, n_perm=n_perm, seed=seed)
        out[e] = dict(rho=rho, perm_p=p, ci=ci)
    # B1's OWN committed criterion, b1_allocation_signal.py:360. Not a new
    # threshold, and deliberately not the 0.5 ratio -- which B1 itself froze a
    # threshold declaring 'still not stateable' (:376-381) and which ES's own
    # 0.5463 fails.
    out['ordering_pass'] = bool(
        out['mae']['rho'] is not None
        and out['mae']['rho'] > out['one_minus_sa']['rho'] > out['one_minus_iou']['rho'])
    out['ratio_1mSa_over_MAE'] = (
        float(out['one_minus_sa']['rho'] / out['mae']['rho'])
        if out['mae']['rho'] else None)
    return out


def assert_harness_reproduces_b1(tag=TAG):
    """Gate 8 -- the cheapest and strongest gate, and zero GPU.

    Consumes the COMMITTED per-image ES CSV rather than a fresh forward, so this
    is pure arithmetic through the same functions with the same RNG seed and
    bit-exact equality is achievable (contrast T2 Addendum A1, where a < 1e-9
    comparison against a 6-dp-stored reference was unsatisfiable by any correct
    computation). It proves T2-C's harness IS B1's harness before any new signal
    enters.
    """
    import csv
    p = os.path.join(B1_OUT, 'b1_target_es_SINet-S2C.csv')
    sig = {r['name']: float(r['es']) for r in csv.DictReader(open(p))}
    got = t2c_correlation(tag, K, COMMITTED_SEED, sig, arch='SINet/S2C',
                          n_perm=2000)
    want = json.load(open(os.path.join(B1_OUT,
                                       'b1_faithful_correlation.json')))[tag]
    if got['clusters_used'] != want['clusters_used']:
        _halt('clusters_used %s != committed %s'
              % (got['clusters_used'], want['clusters_used']))
    if got['n_target_in_used'] != want['n_target_in_used']:
        _halt('n_target_in_used %s != committed %s -- the join is not B1\'s'
              % (got['n_target_in_used'], want['n_target_in_used']))
    for e in B1.ERRORS:
        if got[e]['rho'] != want[e]['rho']:
            _halt('rho(%s) %.17g != committed %.17g (|d|=%.3e); the harness is '
                  'not B1\'s' % (e, got[e]['rho'], want[e]['rho'],
                                 abs(got[e]['rho'] - want[e]['rho'])))
    return dict(clusters_used=got['clusters_used'],
                n_target_in_used=got['n_target_in_used'],
                rho={e: got[e]['rho'] for e in B1.ERRORS},
                ratio=got['ratio_1mSa_over_MAE'],
                ordering_pass=got['ordering_pass'])

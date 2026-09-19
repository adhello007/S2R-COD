#!/usr/bin/env python
"""DIAG.4 -- extend the CHAMELEON audit over the 25 UNCHECKED images.

The released detector compares only same-dimension images, so a CHAMELEON image
with no same-dimension partner in the training pool is reported `unchecked`, and
the audit says plainly that unchecked is not clean. 25 of 76 are in that state.
This closes as much of that gap as two additional instruments can:

  STAGE 1  resolution-normalised global matching -- both images resized to a
           common canonical grid, which catches a copy that was RESCALED out of
           its dimension group (the released tool cannot see these at all).
  STAGE 2  local-patch / keypoint retrieval with RANSAC -- SIFT correspondences
           filtered by a geometric model, which catches a CROP or a rescale with
           a changed aspect ratio (neither is visible to any global descriptor).

CALIBRATION, NOT INVENTION
--------------------------
Both stages need a decision threshold, and a threshold chosen by looking at the
25 answers would be worthless. So both are calibrated on data whose answer is
already known and committed:

  positives  the 41 CONFIRMED pairs from rebuild/D2_reaudit/out/chameleon_contaminated.json
  negatives  random CHAMELEON x training pairs, which are overwhelmingly distinct
             photographs

The threshold is fixed from that calibration BEFORE the 25 are scored, and the
separation achieved on the calibration set is reported so a reader can see how
much the threshold is worth.

NEGATIVE CONTROL
----------------
The same extended instrument is run on NC4K, where the released detector found
0/4121 and D2_NC4K established a clean null. An extension that finds matches
everywhere would be measuring its own tolerance; this is the check that it does
not.

Reads only committed data. Trains nothing. Writes only under rebuild/DIAG/out/.

Usage:
  .venv/bin/python rebuild/DIAG/diag_chameleon_ext.py [--workers 24]
"""

import argparse
import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')

CHAM_DIR = os.path.join(REPO, 'Dataset/chameleon_new/animals')
TRAIN_DIR = os.path.join(REPO, 'Dataset/Target/Image')
NC4K_DIR = os.path.join(REPO, 'Dataset/Test/NC4K/Imgs')
COD_TEST_DIR = os.path.join(REPO, 'Dataset/Test/COD10K/Imgs')
COMMITTED = os.path.join(REPO, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')

GRID = 64               # stage-1 canonical grid
VERIFY = 256            # stage-1 verification grid
SHORTLIST = 16          # candidates carried from stage 1 into stage 2
N_NEG = 4000            # random negative pairs for calibration
RANSAC_PX = 4.0
MIN_MATCH = 8


def _p(m):
    print(m, flush=True)


# ---------------------------------------------------------------- descriptors
def _load_gray(path, n):
    im = Image.open(path).convert('L').resize((n, n), Image.BILINEAR)
    return np.asarray(im, dtype=np.float32)


def desc(path):
    """Resolution-normalised descriptor. Aspect is DELIBERATELY not preserved:
    a rescale that changed aspect, and a crop, both survive this where they do
    not survive a same-dimension check. No contrast normalisation -- the released
    detector documents why (it destroys the discriminative scale)."""
    return _load_gray(path, GRID).ravel()


def rms(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def verify_pair(pa, pb):
    """Stage-1 verification at a larger canonical grid."""
    a, b = _load_gray(pa, VERIFY), _load_gray(pb, VERIFY)
    return dict(norm_rms=rms(a, b), norm_mean_abs=float(np.mean(np.abs(a - b))),
                norm_p99=float(np.percentile(np.abs(a - b), 99)),
                norm_corr=float(np.corrcoef(a.ravel(), b.ravel())[0, 1]))


# --------------------------------------------------------------- stage 2 SIFT
_SIFT = None


def _sift():
    global _SIFT
    if _SIFT is None:
        _SIFT = cv2.SIFT_create(nfeatures=1200)
    return _SIFT


def _kp(path, maxdim=640):
    im = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if im is None:
        return None, None, 1.0
    h, w = im.shape
    s = min(1.0, maxdim / max(h, w))
    if s < 1.0:
        im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
    k, d = _sift().detectAndCompute(im, None)
    return k, d, s


def geometric_match(pa, pb):
    """SIFT + Lowe ratio + RANSAC homography. Returns inlier count and share.

    A genuine crop or rescale of ONE photograph yields many correspondences that
    agree on a single homography. Two different photographs of similar scenes
    yield few, and they do not agree on any one model. The inlier count is
    therefore the quantity that separates 'same photograph, transformed' from
    'similar photograph'."""
    ka, da, _ = _kp(pa)
    kb, db, _ = _kp(pb)
    if da is None or db is None or len(da) < MIN_MATCH or len(db) < MIN_MATCH:
        return dict(n_kp_a=0 if da is None else len(da), n_kp_b=0 if db is None else len(db),
                    n_good=0, n_inlier=0, inlier_share=0.0)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    good = []
    for m in bf.knnMatch(da, db, k=2):
        if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
            good.append(m[0])
    if len(good) < MIN_MATCH:
        return dict(n_kp_a=len(da), n_kp_b=len(db), n_good=len(good),
                    n_inlier=0, inlier_share=0.0)
    src = np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, RANSAC_PX)
    n_in = int(mask.sum()) if mask is not None else 0
    return dict(n_kp_a=len(da), n_kp_b=len(db), n_good=len(good), n_inlier=n_in,
                inlier_share=float(n_in / len(good)))


# ------------------------------------------------------------------ pipelines
def _desc_job(p):
    try:
        return p, desc(p)
    except Exception:                                          # noqa: BLE001
        return p, None


def build_bank(paths, workers, label):
    _p('  describing %d images (%s)' % (len(paths), label))
    D, keep = [], []
    with ProcessPoolExecutor(workers) as ex:
        for p, d in ex.map(_desc_job, paths, chunksize=32):
            if d is not None:
                D.append(d)
                keep.append(p)
    return np.vstack(D), keep


def dims(path):
    with Image.open(path) as im:
        return im.size


def _geo_job(t):
    a, b = t
    r = geometric_match(a, b)
    r.update(a=a, b=b)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=24)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(20260918)

    committed = json.load(open(COMMITTED))
    confirmed = {c['chameleon_image']: c for c in committed['contaminated']}
    _p('committed: %d confirmed pairs, %d unchecked declared'
       % (len(confirmed), committed['unchecked']['n']))

    cham = sorted(os.path.join(CHAM_DIR, f) for f in os.listdir(CHAM_DIR)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    train = sorted(os.path.join(TRAIN_DIR, f) for f in os.listdir(TRAIN_DIR)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    _p('CHAMELEON %d   training pool %d' % (len(cham), len(train)))

    # ---- who is unchecked: no same-dimension training candidate -------------
    tdims = {}
    for p in train:
        tdims.setdefault(dims(p), []).append(p)
    unchecked = [p for p in cham if dims(p) not in tdims]
    _p('unchecked (no same-dimension training candidate): %d' % len(unchecked))

    # ---- descriptor banks ---------------------------------------------------
    Dtr, train = build_bank(train, args.workers, 'training pool')
    Dch, cham = build_bank(cham, args.workers, 'CHAMELEON')
    cidx = {p: i for i, p in enumerate(cham)}
    tidx = {os.path.basename(p): i for i, p in enumerate(train)}

    # ---- CALIBRATION: positives are the 41 committed pairs ------------------
    pos = []
    for p in cham:
        b = os.path.basename(p)
        if b in confirmed and confirmed[b]['partner'] in tidx:
            pos.append((cidx[p], tidx[confirmed[b]['partner']]))
    _p('calibration positives resolvable: %d of %d' % (len(pos), len(confirmed)))
    neg = [(int(rng.integers(len(cham))), int(rng.integers(len(train))))
           for _ in range(N_NEG)]

    pos_rms = np.array([rms(Dch[i], Dtr[j]) for i, j in pos])
    neg_rms = np.array([rms(Dch[i], Dtr[j]) for i, j in neg])
    # threshold fixed BEFORE the 25 are scored: the largest positive distance,
    # which keeps 100% recall on the known answers, and its false-positive rate
    # on the negatives is reported rather than assumed.
    thr_rms = float(pos_rms.max())
    fpr = float((neg_rms <= thr_rms).mean())
    _p('stage-1 calibration: positives rms max %.3f mean %.3f | negatives mean %.3f min %.3f'
       % (pos_rms.max(), pos_rms.mean(), neg_rms.mean(), neg_rms.min()))
    _p('stage-1 threshold (100%% recall on 41 knowns) = %.3f  -> FPR on negatives %.4f'
       % (thr_rms, fpr))

    # ---- stage-2 calibration on the same two sets ---------------------------
    _p('stage-2 calibration: SIFT+RANSAC on %d positives and %d sampled negatives'
       % (len(pos), 300))
    negs = neg[:300]
    with ProcessPoolExecutor(args.workers) as ex:
        pos_geo = list(ex.map(_geo_job, [(cham[i], train[j]) for i, j in pos], chunksize=1))
        neg_geo = list(ex.map(_geo_job, [(cham[i], train[j]) for i, j in negs], chunksize=1))
    pin = np.array([g['n_inlier'] for g in pos_geo])
    nin = np.array([g['n_inlier'] for g in neg_geo])
    thr_in = int(max(MIN_MATCH, nin.max() + 1))
    _p('  positives inliers: min %d median %d max %d' % (pin.min(), int(np.median(pin)), pin.max()))
    _p('  negatives inliers: max %d  -> threshold = %d inliers' % (nin.max(), thr_in))
    _p('  recall of that threshold on the 41 knowns: %d/%d' % (int((pin >= thr_in).sum()), len(pin)))

    # ---- SCORE THE 25 -------------------------------------------------------
    rows = []
    for p in unchecked:
        d = Dch[cidx[p]]
        dist = np.sqrt(((Dtr - d) ** 2).mean(1))
        order = np.argsort(dist)[:SHORTLIST]
        cands = [(int(j), float(dist[j])) for j in order]
        geo_jobs = [(p, train[j]) for j, _ in cands]
        with ProcessPoolExecutor(args.workers) as ex:
            geos = list(ex.map(_geo_job, geo_jobs, chunksize=1))
        best = max(range(len(cands)), key=lambda i: geos[i]['n_inlier'])
        j, dj = cands[best]
        v = verify_pair(p, train[j])
        rows.append(dict(
            chameleon_image=os.path.basename(p), cham_dims='%dx%d' % dims(p),
            best_partner=os.path.basename(train[j]), partner_dims='%dx%d' % dims(train[j]),
            stage1_rms=round(dj, 4), stage1_rms_rank1=round(float(dist[order[0]]), 4),
            stage1_pass=bool(dj <= thr_rms),
            n_inlier=geos[best]['n_inlier'], n_good=geos[best]['n_good'],
            inlier_share=round(geos[best]['inlier_share'], 4),
            stage2_pass=bool(geos[best]['n_inlier'] >= thr_in),
            **{k: round(v[k], 4) for k in v}))
        rows[-1]['verdict'] = ('MATCH' if (rows[-1]['stage1_pass'] or rows[-1]['stage2_pass'])
                               else 'no match found')
        _p('  %-22s rms %7.3f  inliers %4d  -> %s'
           % (rows[-1]['chameleon_image'], dj, rows[-1]['n_inlier'], rows[-1]['verdict']))

    # ---- NEGATIVE CONTROL: NC4K against COD10K-test ------------------------
    _p('\nnegative control: NC4K vs COD10K-test under the identical extension')
    nc = sorted(os.path.join(NC4K_DIR, f) for f in os.listdir(NC4K_DIR)
                if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    ct = sorted(os.path.join(COD_TEST_DIR, f) for f in os.listdir(COD_TEST_DIR)
                if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    cdims = {}
    for p in ct:
        cdims.setdefault(dims(p), []).append(p)
    nc_unchecked = [p for p in nc if dims(p) not in cdims]
    sample = [nc_unchecked[i] for i in rng.choice(len(nc_unchecked),
                                                  size=min(120, len(nc_unchecked)),
                                                  replace=False)]
    Dct, ct = build_bank(ct, args.workers, 'COD10K-test')
    Dnc, sample = build_bank(sample, args.workers, 'NC4K unchecked sample')
    ctrl = []
    for i, p in enumerate(sample):
        dist = np.sqrt(((Dct - Dnc[i]) ** 2).mean(1))
        j = int(np.argmin(dist))
        g = geometric_match(p, ct[j])
        ctrl.append(dict(nc4k_image=os.path.basename(p), best=os.path.basename(ct[j]),
                         stage1_rms=round(float(dist[j]), 4), n_inlier=g['n_inlier'],
                         stage1_pass=bool(dist[j] <= thr_rms),
                         stage2_pass=bool(g['n_inlier'] >= thr_in)))
    n_ctrl_hit = sum(1 for c in ctrl if c['stage1_pass'] or c['stage2_pass'])
    _p('  NC4K unchecked total %d, sampled %d, flagged at the declared threshold: %d'
       % (len(nc_unchecked), len(sample), n_ctrl_hit))

    # ---- THE OPERATING POINT, revised by the negative control ---------------
    # The declared stage-2 threshold was calibrated on random CHAMELEON x training
    # negatives, whose inlier ceiling was 8. The NC4K control -- a HARDER negative
    # set, being two real camouflage datasets -- reaches higher. Under-specifying
    # the negative set is this script's own defect, and the fix is a RULE, not a
    # choice: the operating point is one above the largest inlier count any
    # negative set produces. Both counts are reported so the revision is auditable.
    ctrl_in = np.array([c['n_inlier'] for c in ctrl])
    thr_op = int(max(thr_in, ctrl_in.max() + 1))
    _p('  NC4K control inliers: median %d  max %d' % (int(np.median(ctrl_in)), ctrl_in.max()))
    _p('  declared stage-2 threshold %d -> OPERATING POINT %d inliers'
       % (thr_in, thr_op))
    _p('  recall of the operating point on the 41 knowns: %d/%d'
       % (int((pin >= thr_op).sum()), len(pin)))
    n_ctrl_op = int(sum(1 for c in ctrl if c['n_inlier'] >= thr_op))
    _p('  NC4K flagged AT the operating point: %d of %d' % (n_ctrl_op, len(ctrl)))
    for r in rows:
        r['at_operating_point'] = bool(r['n_inlier'] >= thr_op)
    n_op = sum(1 for r in rows if r['at_operating_point'])
    _p('  CHAMELEON matched at the operating point: %d of %d' % (n_op, len(rows)))

    # ---- artifacts ----------------------------------------------------------
    n_match = sum(1 for r in rows if r['verdict'] == 'MATCH')
    res = dict(
        what='extension of the CHAMELEON audit over the images the released detector reports unchecked',
        decides='nothing already committed; 41/76 stands unchanged',
        n_unchecked=len(unchecked), n_new_matches=n_match,
        n_new_matches_at_operating_point=n_op,
        operating_point_inliers=thr_op,
        headline=('41/76 committed + %d newly matched = %d/76 (%.1f%%); '
                  '%d still unchecked, 10 verifiably clean'
                  % (n_op, 41 + n_op, 100.0 * (41 + n_op) / 76, len(unchecked) - n_op)),
        calibration=dict(
            n_positives=len(pos), n_negatives=N_NEG,
            stage1_threshold_rms=thr_rms,
            stage1_positive_rms=dict(min=float(pos_rms.min()), max=float(pos_rms.max()),
                                     mean=float(pos_rms.mean())),
            stage1_negative_rms=dict(min=float(neg_rms.min()), mean=float(neg_rms.mean())),
            stage1_fpr_on_negatives=fpr,
            stage2_threshold_inliers=thr_in,
            stage2_positive_inliers=dict(min=int(pin.min()), median=int(np.median(pin)),
                                         max=int(pin.max())),
            stage2_negative_inliers_max=int(nin.max()),
            stage2_recall_on_knowns='%d/%d' % (int((pin >= thr_in).sum()), len(pin))),
        negative_control=dict(dataset='NC4K vs COD10K-test',
                              n_unchecked=len(nc_unchecked), n_sampled=len(sample),
                              n_flagged=n_ctrl_hit,
                              n_flagged_at_operating_point=n_ctrl_op,
                              inlier_max=int(ctrl_in.max()),
                              inlier_median=int(np.median(ctrl_in)), rows=ctrl),
        rows=rows,
        limitations=('Still a LOWER BOUND. Different photographs of one specimen, '
                     'heavy colour/geometric edits and montages remain undetected. '
                     'Stage 2 needs texture: a low-keypoint image can fail to match '
                     'a true partner.'))
    json.dump(res, open(os.path.join(OUT, 'diag_chameleon_ext.json'), 'w'),
              indent=2, sort_keys=True)
    with open(os.path.join(OUT, 'diag_chameleon_ext.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    _p('\nRESULT at the declared threshold : %d of %d' % (n_match, len(unchecked)))
    _p('RESULT at the operating point    : %d of %d  <- REPORTED' % (n_op, len(unchecked)))
    _p('CHAMELEON contamination: 41/76 -> %d/76 (%.1f%%)  |  unchecked %d  |  clean 10'
       % (41 + n_op, 100.0 * (41 + n_op) / 76, len(unchecked) - n_op))
    _p('wrote %s' % os.path.join(OUT, 'diag_chameleon_ext.json'))


if __name__ == '__main__':
    main()

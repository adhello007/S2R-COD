#!/usr/bin/env python
"""FINAL_AUDIT -- decide whether the geometric extension's matches are the SAME PHOTOGRAPH.

The extension (rebuild/DIAG/diag_chameleon_ext.py) matched CHAMELEON images to training
images with SIFT + RANSAC and reported an inlier count. An inlier count establishes that
many local patches agree on one geometric model. It does NOT establish that the two files
are the same photograph: two exposures of one static scene, seconds apart, also agree on a
homography. The paper claims every match "left its dimension group by a rescale or crop",
which is a claim about pixels, and no pixel measurement was ever made.

This makes it. For each pair, warp the partner into the CHAMELEON frame through the
recovered homography and measure what is left:

  residual   mean|cham - warped| over the valid overlap, in 0-255 units
  corr       Pearson correlation over the same overlap
  transform  H decomposed into scale, rotation, shear, perspective

The same photograph rescaled or cropped leaves a LOW residual under a near-similarity
transform -- resampling blur and re-encoding noise, nothing structural. A different
photograph of the same specimen leaves a HIGH residual however many keypoints agreed,
because the animal and the shadows have moved.

The 41 confirmed same-dimension pairs are measured too, as an anchor: they are already
known to be re-encodes, so their residual under this instrument must land near their known
mean_abs (0.603..5.512) with H ~ identity. If the anchor does not reproduce, the
instrument is wrong and nothing downstream is trustworthy.

Reads only committed data. Trains nothing. Writes only under rebuild/FINAL_AUDIT/out/.

Usage:
  .venv/bin/python rebuild/FINAL_AUDIT/adjudicate.py
"""

import json
import os
import sys

import cv2
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')

CHAM_DIR = os.path.join(REPO, 'Dataset/chameleon_new/animals')
TRAIN_DIR = os.path.join(REPO, 'Dataset/Target/Image')
EXT_JSON = os.path.join(REPO, 'rebuild/DIAG/out/diag_chameleon_ext.json')
CONFIRMED = os.path.join(REPO, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')

SIFT_MAXDIM = 2000      # generous: these are 11 pairs, not a sweep
RANSAC_PX = 4.0
LOWE = 0.75
MIN_MATCH = 8
MIN_OVERLAP = 0.10      # a warp covering <10% of the frame is not evidence of anything


def _p(m):
    print(m, flush=True)
    sys.stdout.flush()


# ------------------------------------------------------------------ geometry
def _load(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise IOError('unreadable: %s' % path)
    return im


def _kp(gray, maxdim=SIFT_MAXDIM):
    h, w = gray.shape
    s = min(1.0, maxdim / max(h, w))
    if s < 1.0:
        gray = cv2.resize(gray, (int(round(w * s)), int(round(h * s))),
                          interpolation=cv2.INTER_AREA)
    k, d = cv2.SIFT_create(nfeatures=4000).detectAndCompute(gray, None)
    return k, d, s


def homography(cham_bgr, part_bgr):
    """Recover H mapping PARTNER pixels into the CHAMELEON frame, at full resolution."""
    gc = cv2.cvtColor(cham_bgr, cv2.COLOR_BGR2GRAY)
    gp = cv2.cvtColor(part_bgr, cv2.COLOR_BGR2GRAY)
    kc, dc, sc = _kp(gc)
    kp_, dp, sp = _kp(gp)
    if dc is None or dp is None or len(dc) < MIN_MATCH or len(dp) < MIN_MATCH:
        return None, 0, 0, 0.0

    bf = cv2.BFMatcher(cv2.NORM_L2)
    good = [m[0] for m in bf.knnMatch(dp, dc, k=2)
            if len(m) == 2 and m[0].distance < LOWE * m[1].distance]
    if len(good) < MIN_MATCH:
        return None, len(good), 0, 0.0

    src = np.float32([kp_[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)   # partner
    dst = np.float32([kc[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)    # cham
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, RANSAC_PX)
    if H is None:
        return None, len(good), 0, 0.0
    n_in = int(mask.sum())

    # lift the homography out of the downscaled detection frames back to full resolution:
    #   full_partner --(sp)--> partner_ds --(H)--> cham_ds --(1/sc)--> full_cham
    Sp = np.diag([sp, sp, 1.0])
    Sc_inv = np.diag([1.0 / sc, 1.0 / sc, 1.0])
    H_full = Sc_inv @ H @ Sp
    return H_full, len(good), n_in, float(n_in / len(good))


def decompose(H):
    """Split H into the parts that say whether it is a plain rescale/crop."""
    H = H / H[2, 2]
    A = H[:2, :2]
    sx = float(np.hypot(A[0, 0], A[1, 0]))
    sy = float(np.hypot(A[0, 1], A[1, 1]))
    rot = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
    # angle between the two mapped basis vectors; 90 degrees means no shear
    c0, c1 = A[:, 0], A[:, 1]
    cosang = float(c0 @ c1 / (np.linalg.norm(c0) * np.linalg.norm(c1) + 1e-12))
    shear = float(90.0 - np.degrees(np.arccos(np.clip(cosang, -1, 1))))
    persp = float(max(abs(H[2, 0]), abs(H[2, 1])))
    return dict(scale_x=sx, scale_y=sy, rotation_deg=rot, shear_deg=shear,
                perspective=persp, aspect_ratio=float(sx / (sy + 1e-12)))


def residual(cham_bgr, part_bgr, H):
    """Warp partner into the CHAMELEON frame and measure what survives."""
    h, w = cham_bgr.shape[:2]
    warped = cv2.warpPerspective(part_bgr, H, (w, h), flags=cv2.INTER_LINEAR,
                                 borderValue=(0, 0, 0))
    cover = cv2.warpPerspective(np.ones(part_bgr.shape[:2], np.uint8), H, (w, h),
                                flags=cv2.INTER_NEAREST, borderValue=0)
    # erode so resampled border pixels do not pollute the statistics
    cover = cv2.erode(cover, np.ones((5, 5), np.uint8))
    ov = cover.astype(bool)
    frac = float(ov.mean())
    if frac < 1e-6:
        return None, warped, cover, 0.0

    a = cham_bgr[ov].astype(np.float32)
    b = warped[ov].astype(np.float32)
    diff = np.abs(a - b)
    ga, gb = a.mean(axis=1), b.mean(axis=1)
    corr = float(np.corrcoef(ga, gb)[0, 1]) if ga.size > 2 and ga.std() > 0 and gb.std() > 0 else 0.0
    return dict(residual_mean=float(diff.mean()),
                residual_p99=float(np.percentile(diff, 99)),
                residual_max=float(diff.max()),
                corr=corr,
                overlap_frac=frac), warped, cover, frac


def measure(cham_name, part_name):
    cp = os.path.join(CHAM_DIR, cham_name)
    pp = os.path.join(TRAIN_DIR, part_name)
    cham, part = _load(cp), _load(pp)
    H, n_good, n_in, share = homography(cham, part)
    row = dict(chameleon_image=cham_name, partner=part_name,
               cham_dims='%dx%d' % (cham.shape[1], cham.shape[0]),
               partner_dims='%dx%d' % (part.shape[1], part.shape[0]),
               n_good=n_good, n_inlier=n_in, inlier_share=round(share, 4))
    if H is None:
        row.update(verdict='NO HOMOGRAPHY')
        return row, None, None, None
    row.update({k: round(v, 5) for k, v in decompose(H).items()})
    res, warped, cover, frac = residual(cham, part, H)
    if res is None:
        row.update(verdict='NO OVERLAP')
        return row, cham, None, None
    row.update({k: round(v, 4) for k, v in res.items()})
    return row, cham, warped, cover


# ------------------------------------------------------------------ contact sheet
def sheet(items, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    n = len(items)
    fig, axes = plt.subplots(n, 4, figsize=(15, 3.3 * n))
    if n == 1:
        axes = axes[None, :]
    for i, (row, cham, warped, cover) in enumerate(items):
        rgb = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        axes[i, 0].imshow(rgb(cham))
        axes[i, 0].set_title('%s\n%s' % (row['chameleon_image'], row['cham_dims']), fontsize=8)
        part = _load(os.path.join(TRAIN_DIR, row['partner']))
        axes[i, 1].imshow(rgb(part))
        axes[i, 1].set_title('%s\n%s' % (row['partner'][:34], row['partner_dims']), fontsize=7)
        if warped is not None:
            axes[i, 2].imshow(rgb(warped))
            axes[i, 2].set_title('partner warped into frame\ninliers=%d share=%.2f'
                                 % (row['n_inlier'], row['inlier_share']), fontsize=8)
            d = cv2.absdiff(cham, warped)
            d[cover == 0] = 0
            axes[i, 3].imshow(rgb(np.clip(d.astype(np.int16) * 3, 0, 255).astype(np.uint8)))
            axes[i, 3].set_title('|difference| x3   residual=%.1f\ncorr=%.2f  overlap=%.0f%%'
                                 % (row.get('residual_mean', -1), row.get('corr', 0),
                                    100 * row.get('overlap_frac', 0)), fontsize=8)
        for j in range(4):
            axes[i, j].axis('off')
    fig.suptitle(title, fontsize=13, y=0.999)
    fig.tight_layout()
    fig.savefig(path, dpi=64, bbox_inches='tight')
    plt.close(fig)
    _p('  wrote %s' % path)


# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)

    ext = json.load(open(EXT_JSON))
    matched = [r for r in ext['rows'] if r.get('verdict') == 'MATCH']
    matched.sort(key=lambda r: -(r.get('n_inlier') or 0))
    _p('extension reports %d MATCH rows (%d at its operating point)'
       % (len(matched), sum(1 for r in matched if r.get('at_operating_point'))))

    conf = json.load(open(CONFIRMED))['contaminated']
    anchors = sorted(conf, key=lambda e: e['mean_abs'])[:4] + \
        sorted(conf, key=lambda e: -e['mean_abs'])[:4]

    _p('\n=== ANCHOR: 8 of the 41 confirmed same-dimension pairs ===')
    _p('%-16s %-7s %-7s %-7s %-7s %-7s' % ('cham', 'known', 'resid', 'corr', 'scale', 'ovlp'))
    arows, aitems = [], []
    for e in anchors:
        row, cham, warped, cover = measure(e['chameleon_image'], e['partner'])
        row['known_mean_abs'] = e['mean_abs']
        row['group'] = 'anchor'
        arows.append(row)
        if warped is not None and len(aitems) < 3:
            aitems.append((row, cham, warped, cover))
        _p('%-16s %-7.3f %-7.3f %-7.3f %-7.4f %-7.2f'
           % (row['chameleon_image'], e['mean_abs'], row.get('residual_mean', -1),
              row.get('corr', 0), row.get('scale_x', 0), row.get('overlap_frac', 0)))

    _p('\n=== ADJUDICATION: the extension matches ===')
    _p('%-16s %-6s %-6s %-8s %-7s %-7s %-7s %-7s %-6s'
       % ('cham', 'inl', 'share', 'resid', 'corr', 'sx', 'sy', 'shear', 'ovlp'))
    mrows, mitems = [], []
    for r in matched:
        row, cham, warped, cover = measure(r['chameleon_image'], r['best_partner'])
        row['ext_inliers'] = r.get('n_inlier')
        row['ext_at_operating_point'] = r.get('at_operating_point')
        row['group'] = 'extension'
        mrows.append(row)
        if warped is not None:
            mitems.append((row, cham, warped, cover))
        _p('%-16s %-6d %-6.2f %-8.3f %-7.3f %-7.4f %-7.4f %-7.2f %-6.2f'
           % (row['chameleon_image'], row['n_inlier'], row['inlier_share'],
              row.get('residual_mean', -1), row.get('corr', 0), row.get('scale_x', 0),
              row.get('scale_y', 0), row.get('shear_deg', 0), row.get('overlap_frac', 0)))

    rows = arows + mrows
    keys = sorted({k for r in rows for k in r})
    import csv
    with open(os.path.join(OUT, 'adjudication.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    json.dump(rows, open(os.path.join(OUT, 'adjudication.json'), 'w'), indent=1)
    _p('\nwrote out/adjudication.{csv,json}  (%d rows)' % len(rows))

    _p('\nrendering contact sheets')
    if aitems:
        sheet(aitems, os.path.join(OUT, 'sheet_anchor.png'),
              'ANCHOR - known same-dimension re-encodes (residual must be near known mean|diff|)')
    if mitems:
        sheet(mitems, os.path.join(OUT, 'sheet_extension.png'),
              'ADJUDICATION - geometric extension matches: is this the SAME PHOTOGRAPH?')

    anchor_res = [r['residual_mean'] for r in arows if 'residual_mean' in r]
    if anchor_res:
        _p('\nanchor residual range %.3f .. %.3f (known mean_abs range 0.603 .. 5.512)'
           % (min(anchor_res), max(anchor_res)))
    ext_res = sorted((r.get('residual_mean', 1e9), r['chameleon_image']) for r in mrows)
    _p('extension residuals, ascending:')
    for v, n in ext_res:
        _p('   %-16s %.3f' % (n, v))


if __name__ == '__main__':
    main()

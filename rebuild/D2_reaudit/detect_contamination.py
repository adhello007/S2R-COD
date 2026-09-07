#!/usr/bin/env python
"""Detect re-encoded duplicate images across two directories.

Answers one question: are images from directory A also present in directory B as
re-encoded copies -- the same photograph saved again at a different JPEG quality,
which no exact hash (md5/sha256) and no pixel-identity check can see?

That case matters because it is how a test set silently enters a training set.
An exact-hash audit reports zero collisions and is *correct at that level*, while
half the evaluation set is training data.

METHOD
  1. Group every image by its exact (width, height). A re-encoded copy keeps its
     dimensions, so only same-dimension pairs can be pixel-comparable, and within
     a dimension group the search is exhaustive -- nothing is missed for want of a
     hash bucket.
  2. Shortlist candidate pairs by a 32x32 greyscale descriptor (bilinear, NOT
     contrast-normalised) compared by per-pixel RMS via a Gram matrix. Contrast
     normalisation destroys the discriminative scale and costs recall; this tool
     deliberately does not use it.
  3. Verify every survivor at FULL resolution: mean absolute difference over RGB.
     A pair is confirmed iff mean|A-B| <= --tol.
  4. For each confirmed pair, extract both files' JPEG quantization tables two
     independent ways (PIL, and a raw DQT-marker parse). Tables that DIFFER are
     positive evidence of re-encoding rather than file copying.
  5. Report, for every image in A, the distance to its nearest same-dimension
     image in B, and look for a discontinuity in the sorted distances. A tight
     cluster followed by a large jump means the boundary is a property of the
     data and not of --tol.

WHAT IT DETECTS
  Re-encoded copies (different JPEG quality, different encoder), and rescaled
  copies that happen to land back on an identical (width, height).

WHAT IT DOES NOT DETECT -- and does not claim
  Crops, flips, rotations, colour shifts, rescaled copies that leave every
  dimension group, and different photographs of the same subject. Every count
  this tool prints is therefore a LOWER BOUND. Images with no same-dimension
  candidate in the other directory are reported as `unchecked`; unchecked is not
  clean.

USAGE
  detect_contamination.py EVAL_DIR TRAIN_DIR
  detect_contamination.py EVAL_DIR TRAIN_DIR --json found.json --csv found.csv
  detect_contamination.py --self-test        # verify the tool on synthetic data

Dependencies: numpy, pillow. Nothing else, and nothing project-specific.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image

# --- method constants. Changing any of these changes what "contaminated" means,
# --- so they are named, defaulted, and printed in every report.
DESC = 32              # descriptor edge, greyscale, NOT contrast-normalised
SHORTLIST_RMS = 14.0   # generous descriptor cutoff; full-resolution verify decides
NEAR_TOL = 6.0         # confirm out to here; a sweep is reported around it
TOL_SWEEP = (1.0, 2.0, 3.0, 5.0, 6.0)
TOPK = 8               # descriptor candidates per image verified at full resolution
EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp')


def _p(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# JPEG quantization tables -- two independent extractions
# ---------------------------------------------------------------------------

def qtable_pil(path):
    """Quantization tables via PIL, keyed by table id.

    Returned as a sorted tuple of (table_id, coefficients) so that dict ordering
    inside PIL cannot influence an equality test.
    """
    try:
        with Image.open(path) as im:
            q = getattr(im, 'quantization', None)
        if not q:
            return None
        return tuple(sorted((int(k), tuple(int(x) for x in v)) for k, v in q.items()))
    except Exception:
        return None


def qtable_dqt(path):
    """Quantization tables by parsing raw JPEG DQT (0xFFDB) markers.

    Independent of any imaging library, so a PIL version change cannot move the
    verdict. Returns the same shape as qtable_pil, or None if the file is not a
    JPEG or carries no DQT segment.
    """
    try:
        with open(path, 'rb') as fh:
            b = fh.read()
    except Exception:
        return None
    if len(b) < 4 or b[0] != 0xFF or b[1] != 0xD8:
        return None                                   # not a JPEG (no SOI)

    tables, i, n = {}, 2, len(b)
    while i < n - 1:
        if b[i] != 0xFF:                              # resynchronise on next marker
            i += 1
            continue
        while i < n and b[i] == 0xFF:                 # skip fill bytes
            i += 1
        if i >= n:
            break
        marker = b[i]
        i += 1
        if marker == 0xD9 or marker == 0xDA:          # EOI, or SOS -> entropy data
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:  # standalone markers
            continue
        if i + 2 > n:
            break
        seg_len = (b[i] << 8) | b[i + 1]
        if seg_len < 2 or i + seg_len > n:
            break
        payload = b[i + 2:i + seg_len]
        i += seg_len
        if marker != 0xDB:
            continue
        j = 0
        while j < len(payload):
            pq_tq = payload[j]
            j += 1
            precision, tid = pq_tq >> 4, pq_tq & 0x0F
            width = 2 if precision else 1
            need = 64 * width
            if j + need > len(payload):
                break
            if width == 1:
                vals = tuple(payload[j:j + 64])
            else:
                vals = tuple((payload[j + 2 * k] << 8) | payload[j + 2 * k + 1]
                             for k in range(64))
            tables[tid] = vals
            j += need
    if not tables:
        return None
    return tuple(sorted(tables.items()))


def _qhash(tbl):
    if tbl is None:
        return None
    return hashlib.sha256(repr(tbl).encode()).hexdigest()[:16]


def container_format(path):
    """Container format from magic bytes, not from the file extension.

    Worth checking on its own: a directory of ".jpg" files can contain PNGs, and
    such a file has no quantization table at all. Comparing a present table
    against a missing one with `!=` reports "the tables differ", which is not
    evidence of re-encoding -- it is the absence of evidence.
    """
    try:
        with open(path, 'rb') as fh:
            head = fh.read(12)
    except Exception:
        return 'unreadable'
    if head[:2] == b'\xff\xd8':
        return 'JPEG'
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        return 'PNG'
    if head[:2] in (b'BM',):
        return 'BMP'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'WEBP'
    if head[:2] in (b'II', b'MM'):
        return 'TIFF'
    return 'other'


def qtable_verdict(pa, pb):
    """('differ' | 'same' | 'na', pil_agrees_with_dqt, qhash_a, qhash_b)."""
    a_pil, b_pil = qtable_pil(pa), qtable_pil(pb)
    a_dqt, b_dqt = qtable_dqt(pa), qtable_dqt(pb)
    if a_dqt is None or b_dqt is None:
        # Not both JPEG, or no DQT segment. Never silently reported as 'differ'.
        return 'na', (a_pil is None) == (a_dqt is None), _qhash(a_dqt), _qhash(b_dqt)
    v_dqt = 'differ' if a_dqt != b_dqt else 'same'
    if a_pil is None or b_pil is None:
        return v_dqt, False, _qhash(a_dqt), _qhash(b_dqt)
    v_pil = 'differ' if a_pil != b_pil else 'same'
    return v_dqt, (v_pil == v_dqt), _qhash(a_dqt), _qhash(b_dqt)


# ---------------------------------------------------------------------------
# descriptors and hashing
# ---------------------------------------------------------------------------

def _descriptor(args):
    """(side, name, path) -> (side, name, (w,h), 32x32 greyscale vector)."""
    side, name, path, desc = args
    try:
        im = Image.open(path)
        w, h = im.size
        g = np.asarray(im.convert('L').resize((desc, desc), Image.BILINEAR),
                       dtype=np.float32)
        return (side, name, (w, h), g.ravel())
    except Exception:
        return (side, name, None, None)


def _phash(path):
    """sha256 of (shape + decoded RGB). Catches re-encodes that decode identically."""
    try:
        a = np.asarray(Image.open(path).convert('RGB'))
    except Exception:
        return None
    h = hashlib.sha256()
    h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def listing(d):
    if not os.path.isdir(d):
        raise SystemExit('not a directory: %s' % d)
    return sorted(f for f in os.listdir(d)
                  if f.lower().endswith(EXTS)
                  and os.path.isfile(os.path.join(d, f)))


def _measure(pa, pb):
    """Full-resolution comparison. None if the two do not share a shape."""
    try:
        A = np.asarray(Image.open(pa).convert('RGB'), np.int16)
        B = np.asarray(Image.open(pb).convert('RGB'), np.int16)
    except Exception:
        return None
    if A.shape != B.shape:
        return None
    d = np.abs(A - B)
    return dict(mean_abs=float(d.mean()), p99_abs=float(np.percentile(d, 99)),
                max_abs=int(d.max()), frac_gt8=float((d > 8).mean()),
                content_std=float(A.std()))


# ---------------------------------------------------------------------------
# the sweep
# ---------------------------------------------------------------------------

def sweep(dir_a, dir_b, tol=NEAR_TOL, shortlist_rms=SHORTLIST_RMS, desc=DESC,
          topk=TOPK, workers=8, quiet=False):
    """Cross-directory near-duplicate sweep plus a nearest-neighbour gap report."""
    names_a, names_b = listing(dir_a), listing(dir_b)
    if not quiet:
        _p('A: %d images in %s' % (len(names_a), dir_a))
        _p('B: %d images in %s' % (len(names_b), dir_b))

    jobs = ([('a', nm, os.path.join(dir_a, nm), desc) for nm in names_a]
            + [('b', nm, os.path.join(dir_b, nm), desc) for nm in names_b])
    groups, unreadable = {}, []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for side, nm, dim, vec in ex.map(_descriptor, jobs, chunksize=64):
            if dim is None:
                unreadable.append((side, nm))
                continue
            groups.setdefault(dim, []).append((side, nm, vec))

    path_of = {('a', nm): os.path.join(dir_a, nm) for nm in names_a}
    path_of.update({('b', nm): os.path.join(dir_b, nm) for nm in names_b})

    # -- confirmed pairs, exhaustive within each dimension group ---------------
    shortlisted, pairs = 0, []
    multi = {k: v for k, v in groups.items()
             if any(m[0] == 'a' for m in v) and any(m[0] == 'b' for m in v)}
    if not quiet:
        _p('%d dimension groups contain images from both directories' % len(multi))
    for dim, members in sorted(multi.items(), key=lambda kv: -len(kv[1])):
        ia = [k for k, m in enumerate(members) if m[0] == 'a']
        ib = [k for k, m in enumerate(members) if m[0] == 'b']
        X = np.stack([m[2] for m in members])
        A_, B_ = X[ia], X[ib]
        d2 = ((A_ * A_).sum(1)[:, None] + (B_ * B_).sum(1)[None, :]
              - 2.0 * (A_ @ B_.T))
        rms = np.sqrt(np.maximum(d2, 0) / (desc * desc))
        for u, v in zip(*np.where(rms <= shortlist_rms)):
            shortlisted += 1
            sa, na, _ = members[ia[u]]
            sb, nb, _ = members[ib[v]]
            m = _measure(path_of[(sa, na)], path_of[(sb, nb)])
            if m is None or m['mean_abs'] > tol:
                continue
            verdict, agree, qa, qb = qtable_verdict(path_of[(sa, na)],
                                                    path_of[(sb, nb)])
            ph_a, ph_b = _phash(path_of[(sa, na)]), _phash(path_of[(sb, nb)])
            fa = container_format(path_of[(sa, na)])
            fb = container_format(path_of[(sb, nb)])
            pairs.append(dict(
                image_a=na, image_b=nb, dims='%dx%d' % dim,
                mean_abs=round(m['mean_abs'], 3),
                p99_abs=round(m['p99_abs'], 1), max_abs=m['max_abs'],
                frac_gt8=round(m['frac_gt8'], 5),
                content_std=round(m['content_std'], 1),
                qtables=verdict, qtable_methods_agree=bool(agree),
                qtable_hash_a=qa, qtable_hash_b=qb,
                format_a=fa, format_b=fb, formats_differ=bool(fa != fb),
                pixel_identical=bool(ph_a is not None and ph_a == ph_b),
                kb_a=os.path.getsize(path_of[(sa, na)]) // 1024,
                kb_b=os.path.getsize(path_of[(sb, nb)]) // 1024))
    pairs.sort(key=lambda r: r['mean_abs'])

    # -- nearest same-dimension B neighbour for every A image ------------------
    nn_rows = []
    for dim, members in groups.items():
        eps = [m for m in members if m[0] == 'a']
        if not eps:
            continue
        trs = [m for m in members if m[0] == 'b']
        if not trs:
            for _, nm, _v in eps:
                nn_rows.append(dict(name=nm, dims='%dx%d' % dim, n_candidates=0,
                                    nearest=None, nearest_name=None))
            continue
        T = np.stack([m[2] for m in trs])
        k_use = len(trs) if topk in (0, None) else min(topk, len(trs))
        for _, nm, vec in eps:
            rms = np.sqrt(((T - vec) ** 2).mean(axis=1))
            order = np.argsort(rms)[:k_use]
            best = (None, None)
            for k in order:
                m = _measure(path_of[('a', nm)], path_of[('b', trs[k][1])])
                if m is None:
                    continue
                if best[0] is None or m['mean_abs'] < best[0]:
                    best = (m['mean_abs'], trs[k][1])
            nn_rows.append(dict(name=nm, dims='%dx%d' % dim, n_candidates=len(trs),
                                nearest=(round(best[0], 3) if best[0] is not None
                                         else None),
                                nearest_name=best[1]))

    vals = sorted(r['nearest'] for r in nn_rows if r['nearest'] is not None)
    gap = None
    for i in range(1, len(vals)):
        if vals[i] - vals[i - 1] > 5 * max(vals[i - 1], 1.0):
            gap = dict(below=vals[i - 1], above=vals[i], n_below=i,
                       ratio=round(vals[i] / max(vals[i - 1], 1e-9), 2))
            break

    matched = sorted({r['image_a'] for r in pairs})
    result = dict(
        method=dict(descriptor='%dx%d greyscale BILINEAR, no contrast normalisation'
                               % (desc, desc),
                    shortlist_rms=shortlist_rms, tolerance_mean_abs=tol,
                    topk_full_res_verified=topk,
                    verification='full-resolution mean|A-B| over RGB int16'),
        dir_a=dict(n=len(names_a)), dir_b=dict(n=len(names_b)),
        candidate_pairs_shortlisted=shortlisted,
        pairs_confirmed=len(pairs),
        contaminated=dict(
            n=len(matched), share=round(len(matched) / len(names_a), 4)
            if names_a else 0.0, names=matched),
        tolerance_sweep={str(t): len({r['image_a'] for r in pairs
                                      if r['mean_abs'] <= t}) for t in TOL_SWEEP},
        nearest_neighbour=dict(
            n_checkable=len(vals),
            n_unchecked=sum(1 for r in nn_rows if r['nearest'] is None),
            sorted_nearest=[round(v, 2) for v in vals], largest_gap=gap),
        unreadable=len(unreadable),
        limitations=('lower bound: crops, flips, colour shifts, rescaled copies '
                     'outside every dimension group, and different photographs of '
                     'one subject are NOT detected. Unchecked is not clean.'),
        pairs=pairs, nn_rows=nn_rows)
    return result


# ---------------------------------------------------------------------------
# self-test: a known answer, built from scratch, needing no external data
# ---------------------------------------------------------------------------

def self_test():
    """Build a synthetic case with a known answer and assert the tool finds it."""
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as tmp:
        da, db = os.path.join(tmp, 'a'), os.path.join(tmp, 'b')
        os.makedirs(da)
        os.makedirs(db)

        # A smooth-plus-texture image, so JPEG re-encoding leaves a small but
        # non-zero residual -- the realistic case.
        yy, xx = np.mgrid[0:240, 0:320]
        base = (128 + 60 * np.sin(xx / 23.0) + 40 * np.cos(yy / 17.0)
                + rng.normal(0, 6, (240, 320)))
        img = np.clip(np.stack([base, base * 0.9 + 12, base * 1.05 - 8], -1),
                      0, 255).astype(np.uint8)
        Image.fromarray(img).save(os.path.join(da, 'shared.jpg'), quality=95)
        # same photograph, re-encoded at a different quality -> must be found
        Image.fromarray(img).save(os.path.join(db, 'shared_reencoded.jpg'), quality=75)

        # an unrelated image at the SAME dimensions -> must NOT be found
        other = np.clip(rng.normal(120, 55, (240, 320, 3)), 0, 255).astype(np.uint8)
        Image.fromarray(other).save(os.path.join(db, 'unrelated.jpg'), quality=90)

        # an image with no same-dimension partner at all -> must be `unchecked`
        odd = np.clip(rng.normal(120, 40, (100, 150, 3)), 0, 255).astype(np.uint8)
        Image.fromarray(odd).save(os.path.join(da, 'no_partner.jpg'), quality=90)

        r = sweep(da, db, workers=2, quiet=True)

        checks = []
        names = r['contaminated']['names']
        checks.append(('the re-encoded copy is detected', names == ['shared.jpg']))
        checks.append(('the unrelated same-dimension image is not matched',
                       all(p['image_b'] != 'unrelated.jpg' for p in r['pairs'])))
        pair = next((p for p in r['pairs'] if p['image_a'] == 'shared.jpg'), None)
        checks.append(('the pair is found exactly once', len(r['pairs']) == 1))
        checks.append(('quantization tables differ (re-encode evidence)',
                       pair is not None and pair['qtables'] == 'differ'))
        checks.append(('PIL and raw-DQT extractions agree',
                       pair is not None and pair['qtable_methods_agree']))
        checks.append(('the pair is NOT pixel-identical (a real re-encode)',
                       pair is not None and not pair['pixel_identical']))
        checks.append(('the residual is non-zero and within tolerance',
                       pair is not None and 0.0 < pair['mean_abs'] <= NEAR_TOL))
        checks.append(('an image with no same-dimension partner is unchecked',
                       r['nearest_neighbour']['n_unchecked'] == 1))

        ok = True
        for label, passed in checks:
            _p('  %-58s %s' % (label, 'PASS' if passed else 'FAIL'))
            ok = ok and bool(passed)
        _p('self-test: %s' % ('PASS' if ok else 'FAIL'))
        return ok


# ---------------------------------------------------------------------------

CSV_FIELDS = ('rank', 'image_a', 'image_b', 'dims', 'mean_abs', 'p99_abs',
              'max_abs', 'frac_gt8', 'content_std', 'qtables',
              'qtable_methods_agree', 'qtable_hash_a', 'qtable_hash_b',
              'format_a', 'format_b', 'formats_differ',
              'pixel_identical', 'kb_a', 'kb_b')


def main():
    ap = argparse.ArgumentParser(
        description='Detect re-encoded duplicate images across two directories.',
        epilog='Counts are a LOWER BOUND; see the module docstring.')
    ap.add_argument('eval_dir', nargs='?', help='directory to audit (e.g. a test set)')
    ap.add_argument('train_dir', nargs='?', help='directory to audit against (e.g. a training set)')
    ap.add_argument('--tol', type=float, default=NEAR_TOL,
                    help='confirm a pair iff full-resolution mean|A-B| <= TOL (default 6.0)')
    ap.add_argument('--shortlist-rms', type=float, default=SHORTLIST_RMS,
                    help='descriptor RMS cutoff for shortlisting (default 14.0)')
    ap.add_argument('--desc', type=int, default=DESC, help='descriptor edge (default 32)')
    ap.add_argument('--topk', type=int, default=TOPK,
                    help='descriptor candidates verified at full resolution per image; '
                         '0 = all same-dimension candidates (default 8)')
    ap.add_argument('--json', dest='json_out', help='write the full report here')
    ap.add_argument('--csv', dest='csv_out', help='write the confirmed pairs here')
    ap.add_argument('--pairs-dir', help='write one side-by-side figure per confirmed pair')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--self-test', action='store_true',
                    help='verify the tool against synthetic data and exit')
    args = ap.parse_args()

    if args.self_test:
        sys.exit(0 if self_test() else 1)
    if not args.eval_dir or not args.train_dir:
        ap.error('EVAL_DIR and TRAIN_DIR are required (or pass --self-test)')

    r = sweep(args.eval_dir, args.train_dir, tol=args.tol,
              shortlist_rms=args.shortlist_rms, desc=args.desc, topk=args.topk,
              workers=args.workers)

    c = r['contaminated']
    _p('')
    _p('shortlisted %d candidate pairs, confirmed %d at mean|diff| <= %.1f'
       % (r['candidate_pairs_shortlisted'], r['pairs_confirmed'], args.tol))
    _p('CONTAMINATED: %d of %d images in %s are re-encoded copies of images in %s  (%.1f%%)'
       % (c['n'], r['dir_a']['n'], args.eval_dir, args.train_dir, 100 * c['share']))
    nq = sum(1 for p in r['pairs'] if p['qtables'] == 'differ')
    nna = sum(1 for p in r['pairs'] if p['qtables'] == 'na')
    _p('quantization tables differ in %d/%d confirmed pairs (re-encode evidence)'
       % (nq, r['pairs_confirmed']))
    if nna:
        nfmt = sum(1 for p in r['pairs']
                   if p['qtables'] == 'na' and p['formats_differ'])
        _p('  %d pair(s) carry no comparable table (a side is not JPEG); of those, '
           '%d differ in CONTAINER FORMAT, which is itself re-encoding evidence'
           % (nna, nfmt))
    if r['pairs']:
        _p('mean|diff| range: %.3f .. %.3f'
           % (r['pairs'][0]['mean_abs'], r['pairs'][-1]['mean_abs']))
    _p('tolerance sweep: %s' % ', '.join('<=%s: %d' % (k, v)
                                         for k, v in r['tolerance_sweep'].items()))
    nn = r['nearest_neighbour']
    _p('nearest-neighbour: %d checkable, %d unchecked (no same-dimension candidate)'
       % (nn['n_checkable'], nn['n_unchecked']))
    if nn['largest_gap']:
        g = nn['largest_gap']
        _p('  GAP: %d images below %.2f, next at %.2f (%.1fx) -- a data boundary, '
           'not a cutoff artifact' % (g['n_below'], g['below'], g['above'], g['ratio']))
    else:
        _p('  no >5x gap: the distribution is continuous, which is what a clean set '
           'looks like')
    _p('')
    _p('LOWER BOUND. %s' % r['limitations'])

    if args.json_out:
        with open(args.json_out, 'w') as fh:
            json.dump(r, fh, indent=2, sort_keys=True)
        _p('wrote %s' % args.json_out)
    if args.csv_out:
        with open(args.csv_out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            w.writeheader()
            for i, p in enumerate(r['pairs'], 1):
                row = dict(p)
                row.pop('_', None)
                w.writerow({k: (row.get(k) if k != 'rank' else i) for k in CSV_FIELDS})
        _p('wrote %s' % args.csv_out)
    if args.pairs_dir:
        os.makedirs(args.pairs_dir, exist_ok=True)
        for i, p in enumerate(r['pairs'], 1):
            A = Image.open(os.path.join(args.eval_dir, p['image_a'])).convert('RGB')
            B = Image.open(os.path.join(args.train_dir, p['image_b'])).convert('RGB')
            d = np.abs(np.asarray(A, np.int16) - np.asarray(B, np.int16))
            D = Image.fromarray(np.clip(d * 20, 0, 255).astype(np.uint8))
            w, h = A.size
            sheet = Image.new('RGB', (w * 3 + 24, h), (250, 250, 250))
            sheet.paste(A, (0, 0))
            sheet.paste(B, (w + 12, 0))
            sheet.paste(D, (2 * w + 24, 0))
            sheet.save(os.path.join(args.pairs_dir, '%02d_%s.png'
                                    % (i, os.path.splitext(p['image_a'])[0])))
        _p('wrote %d pair figures to %s' % (len(r['pairs']), args.pairs_dir))


if __name__ == '__main__':
    main()

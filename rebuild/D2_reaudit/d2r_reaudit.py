#!/usr/bin/env python
"""D2R -- CHAMELEON contamination re-audit against an author-sourced copy.

D2 measured CHAMELEON only against the copy on this disk and said so, at
D2_RESULTS.md 5: "CHAMELEON is not checked against its own publication -- only
against the copies on this disk." This closes that gap and packages the finding.

Method-identical to D2's authoritative s4/s4b so the comparison is apples-to-apples:
every constant is COPIED from rebuild/D2/d2_leakage_sweep.py:204-207, not re-chosen.
No prior value is overwritten -- each is pinned as an OLD CLAIM and reported beside
the new measurement.

Steps:
  s0    reconcile   the two CHAMELEON copies, by content hash and not by filename;
                    plus the mask side, which is a separate question
  s4r   near        same-dimension exhaustive near-duplicate sweep + tolerance sweep
  s4br  endpointNN  nearest same-dimension training image per endpoint image, and
                    the gap that says whether the count is a data boundary
  s5r   impact      how much a contaminated CHAMELEON column would be inflated:
                    (a) model-free difficulty proxies, (b) inference-only score split
  s6r   scope       the mechanism and the README's own design, asserted from source
  s7r   package     the published artifacts, the detector cross-check, the release

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_reaudit.py \
      --steps s0,s4r,s4br,s5r,s6r,s7r --splits full

Trains nothing. s5r-b runs inference from an existing checkpoint; no optimizer
runs and no checkpoint is written. Nothing under Dataset/, Result/ or Snapshot/
is modified.
"""

import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect_contamination as DET                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'D2R'
OUT = C.exp_dir('D2_reaudit', 'out')
CACHE = C.exp_dir('D2_reaudit', 'cache')
PAIRS = C.exp_dir('D2_reaudit', 'pairs')
PREDS = C.exp_dir('D2_reaudit', 'preds')
RELEASE = C.exp_dir('D2_reaudit', 'release')

# --- D2's splits, plus the author-sourced set as a fifth endpoint. Keys are
# --- common.INPUTS keys so paths come from the one registry E0 hashed.
D2_SPLITS = ['tgt', 'test', 'cham', 'nc4k', 'val', 'raw', 'auth', 'local']
SPLITS_FULL = D2_SPLITS + ['chamnew']
SPLITS_MIN = ['tgt', 'cham', 'chamnew']
ENDPOINTS = ['test', 'cham', 'chamnew', 'nc4k', 'val']
TRAINING = ['tgt', 'raw', 'auth', 'local']

# --- method constants, copied verbatim from d2_leakage_sweep.py:204-207 ---
DESC = 32              # descriptor edge, greyscale, NOT contrast-normalised
SHORTLIST_RMS = 14.0   # generous descriptor cutoff; full-res verify decides
NEAR_TOL = 6.0
TOL_SWEEP = (1.0, 2.0, 3.0, 5.0, 6.0)
TOPK_D2 = 8            # s4b's shortlist depth; the comparison run uses this
TOPK_SWEEP = (8, 32, 0)   # 0 = every same-dimension candidate

# --- s5r-b inference ---
CKPT = 'Snapshot/SINet/S2C/Tea_epoch_best.pth'
TESTSIZE = 352
IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]


def _p(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# hashing -- identical to d2_leakage_sweep.py:76-94
# ---------------------------------------------------------------------------

def _hash_one(args):
    split, name, path = args
    with open(path, 'rb') as fh:
        raw = fh.read()
    fhash = hashlib.sha256(raw).hexdigest()
    try:
        im = Image.open(path).convert('RGB')
        a = np.asarray(im)
        ph = hashlib.sha256()
        ph.update(str(a.shape).encode())
        ph.update(a.tobytes())
        return dict(split=split, name=name, fhash=fhash, phash=ph.hexdigest(),
                    shape='%dx%d' % (a.shape[1], a.shape[0]), error='')
    except Exception as e:
        return dict(split=split, name=name, fhash=fhash, phash='UNREADABLE',
                    shape='?', error=str(e)[:80])


def step_hash(splits, workers=8, rehash=False):
    os.makedirs(CACHE, exist_ok=True)
    cache = os.path.join(CACHE, 'hashes.json')
    if not rehash and os.path.isfile(cache):
        recs = json.load(open(cache))
        have = {r['split'] for r in recs}
        if set(splits).issubset(have):
            _p('hashes: loaded %d records from cache' % len(recs))
            return [r for r in recs if r['split'] in splits]
    jobs = []
    for sp in splits:
        d = C.ipath(sp)
        for nm in C.listing(sp):
            jobs.append((sp, nm, os.path.join(d, nm)))
    _p('hashing %d images across %d splits...' % (len(jobs), len(splits)))
    recs = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_hash_one, jobs, chunksize=64)):
            recs.append(r)
            if (i + 1) % 4000 == 0:
                _p('  %d/%d' % (i + 1, len(jobs)))
    with open(cache, 'w') as fh:
        json.dump(recs, fh)
    return recs


# ---------------------------------------------------------------------------
# s0 -- reconcile the two CHAMELEON copies
# ---------------------------------------------------------------------------

MASK_RE = re.compile(r'(\d+)')


def _mask_white(path):
    """Declared normalisation: RGB luminance composited on black, binarised >127.

    Returns (white_mask bool, alpha_fg_fraction or None) -- the WHITE pixels, with
    no polarity interpretation applied yet. The alpha channel is measured rather
    than assumed irrelevant: an RGBA PNG whose alpha carried the object would
    binarise wrongly under a luminance rule, and that has to be a measurement.
    """
    im = Image.open(path)
    alpha_frac = None
    if im.mode in ('RGBA', 'LA', 'PA'):
        a = np.asarray(im.convert('RGBA'))[:, :, 3]
        alpha_frac = float((a > C.THRESH).mean())
        bg = Image.new('RGBA', im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(bg, im.convert('RGBA'))
    g = np.asarray(im.convert('L'))
    return (g > C.THRESH), alpha_frac


def source_polarity(paths):
    """Declare a mask source's polarity from its AGGREGATE white fraction.

    Fixed PER SOURCE, never per image: per-image detection misfires on objects
    that cover a corner or most of the frame (REBUILD_PLAN.md A2, and trap T2 in
    2). A camouflaged object occupies a minority of its frame, so a source whose
    mean white fraction exceeds 0.5 is storing BACKGROUND as white.

    Returns ('object_white' | 'object_black', mean_white_fraction).
    """
    fr = [float(_mask_white(p)[0].mean()) for p in paths]
    mean = float(np.mean(fr)) if fr else 0.0
    return ('object_black' if mean > 0.5 else 'object_white'), mean


def _mask_object(path, polarity):
    """Object mask as uint8 0/255 in SOD polarity (object = 255), given the
    source's declared polarity. Also returns the alpha occupancy."""
    white, alpha = _mask_white(path)
    obj = (~white) if polarity == 'object_black' else white
    return (obj.astype(np.uint8) * 255), alpha


def step_reconcile(recs):
    """Are the repo's CHAMELEON and the author-sourced CHAMELEON the same set?"""
    by = {}
    for r in recs:
        by.setdefault(r['split'], {})[r['name']] = r
    a, b = by.get('cham', {}), by.get('chamnew', {})

    n_a, agg_a, _ = C.dir_digest(C.ipath('cham'))
    n_b, agg_b, _ = C.dir_digest(C.ipath('chamnew'))

    fa = {r['fhash'] for r in a.values()}
    fb = {r['fhash'] for r in b.values()}
    pa = {r['phash'] for r in a.values() if r['phash'] != 'UNREADABLE'}
    pb = {r['phash'] for r in b.values() if r['phash'] != 'UNREADABLE'}

    # outcome boundaries, declared in REAUDIT_PLAN.md 1.5 before running
    if not (os.path.isdir(C.ipath('cham'))):
        outcome = 'd'
    elif n_a != n_b or not (pa & pb):
        outcome = 'c'
    elif len(pa & pb) == len(pa) == len(pb) == n_b:
        outcome = 'a'
    else:
        outcome = 'b'

    rows = []
    for nm in sorted(set(a) | set(b)):
        ra, rb = a.get(nm), b.get(nm)
        qa = DET.qtable_dqt(os.path.join(C.ipath('cham'), nm)) if ra else None
        qb = DET.qtable_dqt(os.path.join(C.ipath('chamnew'), nm)) if rb else None
        rows.append(dict(
            name=nm,
            dims_cham=(ra['shape'] if ra else ''),
            dims_chamnew=(rb['shape'] if rb else ''),
            bytes_cham=(os.path.getsize(os.path.join(C.ipath('cham'), nm))
                        if ra else ''),
            bytes_chamnew=(os.path.getsize(os.path.join(C.ipath('chamnew'), nm))
                           if rb else ''),
            fhash_equal=int(bool(ra and rb and ra['fhash'] == rb['fhash'])),
            phash_equal=int(bool(ra and rb and ra['phash'] == rb['phash'])),
            qtable_equal=int(bool(qa is not None and qa == qb))))

    # --- the mask side, a separate question -------------------------------
    gt_repo = os.path.join(C.REPO, 'Dataset/Test/CHAMELEON/GT')
    m_new = {int(MASK_RE.search(f).group(1)): f
             for f in C.listing('chamnew_gt') if MASK_RE.search(f)}
    m_repo = {}
    if os.path.isdir(gt_repo):
        m_repo = {int(MASK_RE.search(f).group(1)): f
                  for f in sorted(os.listdir(gt_repo)) if MASK_RE.search(f)}
    join_keys = sorted(set(m_new) & set(m_repo))
    bijection = (len(m_new) == len(m_repo) == len(join_keys) == 76)

    # Polarity is DECLARED PER SOURCE from the aggregate, before any comparison.
    pol_new, wf_new = source_polarity([os.path.join(C.ipath('chamnew_gt'), m_new[k])
                                       for k in join_keys])
    pol_repo, wf_repo = source_polarity([os.path.join(gt_repo, m_repo[k])
                                         for k in join_keys])

    mask_rows, identical, alphas = [], 0, []
    raw_ious, aligned_ious = [], []
    for k in join_keys:
        pn = os.path.join(C.ipath('chamnew_gt'), m_new[k])
        pr = os.path.join(gt_repo, m_repo[k])
        bn, af = _mask_object(pn, pol_new)          # polarity-aligned to SOD
        br, _ = _mask_object(pr, pol_repo)
        wn, _ = _mask_white(pn)                     # raw, for the as-stored view
        wr, _ = _mask_white(pr)
        if af is not None:
            alphas.append(af)
        same_shape = (bn.shape == br.shape)
        if same_shape:
            def _iou(a, b):
                u = int((a | b).sum())
                return (int((a & b).sum()) / u) if u else 1.0
            iou_raw = _iou(wn, wr)
            iou = _iou(bn > 0, br > 0)
            exact = bool((bn == br).all())
            raw_ious.append(iou_raw)
            aligned_ious.append(iou)
        else:
            iou_raw, iou, exact = None, None, False
        identical += int(exact)
        mask_rows.append(dict(n=k, canonical=m_new[k], repo=m_repo[k],
                              same_shape=int(same_shape),
                              iou_as_stored=(round(iou_raw, 4)
                                             if iou_raw is not None else None),
                              iou_polarity_aligned=(round(iou, 4)
                                                    if iou is not None else None),
                              exact=int(exact),
                              white_frac_canonical=round(float(wn.mean()), 5),
                              white_frac_repo=round(float(wr.mean()), 5),
                              obj_frac_canonical=round(float((bn > 0).mean()), 5),
                              obj_frac_repo=round(float((br > 0).mean()), 5),
                              alpha_fg_frac_canonical=(round(af, 5)
                                                       if af is not None else None)))

    # which copy did D2 measure? -- from committed artifacts, not disk state
    d2_path = 'UNVERIFIED'
    try:
        blob = C.subprocess.check_output(
            ['git', '-C', C.REPO, 'show', '17dfbbf:rebuild/common.py'],
            text=True, stderr=C.subprocess.DEVNULL)
        m = re.search(r"'cham':\s*dict\(path='([^']+)'", blob)
        if m:
            d2_path = m.group(1)
    except Exception:
        pass
    # corroboration: the committed per-pair manifest's endpoint_kb / dims
    kb_ok = dims_ok = 0
    pair_csv = os.path.join(C.exp_dir('D2', 'out'), 'd2_duplicate_pairs.csv')
    d2_pairs = list(csv.DictReader(open(pair_csv))) if os.path.isfile(pair_csv) else []
    for r in d2_pairs:
        nm = r['endpoint_image']
        p = os.path.join(C.ipath('cham'), nm)
        # D2 recorded round(bytes/1024) -- d2_export_duplicates.py:227
        if os.path.isfile(p) and round(os.path.getsize(p) / 1024) == int(r['endpoint_kb']):
            kb_ok += 1
        rr = next((x for x in rows if x['name'] == nm), None)
        if rr and rr['dims_cham'] == r['dims']:
            dims_ok += 1

    res = dict(
        outcome=outcome,
        cham=dict(n=n_a, agg=agg_a[:16], path=C.INPUTS['cham']['path']),
        chamnew=dict(n=n_b, agg=agg_b[:16], path=C.INPUTS['chamnew']['path']),
        identical_fhash=len(fa & fb), identical_phash=len(pa & pb),
        only_in_cham_phash=len(pa - pb), only_in_chamnew_phash=len(pb - pa),
        filename_join=len(set(a) & set(b)),
        qtables_equal=sum(r['qtable_equal'] for r in rows),
        d2_measured_copy=d2_path,
        d2_manifest_kb_agrees='%d/%d' % (kb_ok, len(d2_pairs)),
        d2_manifest_dims_agrees='%d/%d' % (dims_ok, len(d2_pairs)),
        masks=dict(join_bijection=bool(bijection), n_joined=len(join_keys),
                   n_identical=identical,
                   polarity_canonical=pol_new, white_frac_canonical=round(wf_new, 4),
                   polarity_repo=pol_repo, white_frac_repo=round(wf_repo, 4),
                   polarity_agrees=(pol_new == pol_repo),
                   mean_iou_as_stored=(round(float(np.mean(raw_ious)), 4)
                                       if raw_ious else None),
                   mean_iou_polarity_aligned=(round(float(np.mean(aligned_ious)), 4)
                                              if aligned_ious else None),
                   n_iou_above_0_9=sum(1 for v in aligned_ious if v >= 0.9),
                   canonical_is_rgba=bool(alphas),
                   alpha_fg_frac_mean=(round(float(np.mean(alphas)), 5)
                                       if alphas else None)),
        rows=rows, mask_rows=mask_rows)
    _p('s0: outcome=%s  fhash %d/76  phash %d/76' % (outcome, len(fa & fb),
                                                     len(pa & pb)))
    _p('s0: mask polarity canonical=%s (white %.4f) repo=%s (white %.4f) agrees=%s'
       % (pol_new, wf_new, pol_repo, wf_repo, pol_new == pol_repo))
    _p('s0: mask IoU as-stored %.4f -> polarity-aligned %.4f; identical %d/%d'
       % (res['masks']['mean_iou_as_stored'] or 0.0,
          res['masks']['mean_iou_polarity_aligned'] or 0.0,
          identical, len(join_keys)))
    return res


# ---------------------------------------------------------------------------
# s4r -- near-duplicate sweep. Identical to d2_leakage_sweep.py:210-285
# ---------------------------------------------------------------------------

def _descriptor(args):
    split, name, path = args
    try:
        im = Image.open(path)
        w, h = im.size
        g = np.asarray(im.convert('L').resize((DESC, DESC), Image.BILINEAR),
                       dtype=np.float32)
        return (split, name, (w, h), g.ravel())
    except Exception:
        return (split, name, None, None)


def _descriptors(splits, workers):
    jobs = []
    for sp in splits:
        d = C.ipath(sp)
        for nm in C.listing(sp):
            jobs.append((sp, nm, os.path.join(d, nm)))
    _p('descriptors for %d images...' % len(jobs))
    groups = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for sp, nm, dim, vec in ex.map(_descriptor, jobs, chunksize=64):
            if dim is not None:
                groups.setdefault(dim, []).append((sp, nm, vec))
    return groups


def step_near(recs, groups, tol=NEAR_TOL):
    """Same photograph, re-encoded: exhaustive within every exact-dimension group."""
    phash_of = {(r['split'], r['name']): r['phash'] for r in recs}
    short_d2 = short_new = 0
    found = []
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    _p('s4r: %d dimension groups with >1 member' % len(multi))
    for gi, (dim, members) in enumerate(sorted(multi.items(),
                                               key=lambda kv: -len(kv[1]))):
        X = np.stack([m[2] for m in members])
        sq = (X * X).sum(1)
        d2 = sq[:, None] + sq[None, :] - 2.0 * (X @ X.T)
        np.fill_diagonal(d2, np.inf)
        rms = np.sqrt(np.maximum(d2, 0) / (DESC * DESC))
        ii, jj = np.where(np.triu(rms <= SHORTLIST_RMS, k=1))
        for i, j in zip(ii, jj):
            sa, na, _ = members[i]
            sb, nb, _ = members[j]
            # D2's global counters cover D2's 8 splits; chamnew is counted apart so
            # the committed 323/132/49 stay directly comparable.
            if sa == 'chamnew' or sb == 'chamnew':
                short_new += 1
            else:
                short_d2 += 1
            if phash_of.get((sa, na)) == phash_of.get((sb, nb)):
                continue                       # already pixel-identical
            pa = os.path.join(C.ipath(sa), na)
            pb = os.path.join(C.ipath(sb), nb)
            try:
                A = np.asarray(Image.open(pa).convert('RGB'), np.int16)
                B = np.asarray(Image.open(pb).convert('RGB'), np.int16)
            except Exception:
                continue
            if A.shape != B.shape:
                continue
            d = np.abs(A - B)
            m = float(d.mean())
            if m <= tol:
                found.append(dict(split_a=sa, name_a=na, split_b=sb, name_b=nb,
                                  dims='%dx%d' % dim, mean_abs=round(m, 3),
                                  p99_abs=int(np.percentile(d, 99)),
                                  max_abs=int(d.max()),
                                  frac_gt8=round(float((d > 8).mean()), 5),
                                  content_std=round(float(A.std()), 1)))
        if (gi + 1) % 400 == 0:
            _p('  s4r: %d/%d groups, %d+%d shortlisted, %d confirmed'
               % (gi + 1, len(multi), short_d2, short_new, len(found)))
    _p('s4r: %d (D2 splits) + %d (chamnew) shortlisted, %d confirmed at <= %.1f'
       % (short_d2, short_new, len(found), tol))
    return found, short_d2, short_new


def contamination(near, splits):
    """Distinct endpoint images with >=1 partner in a TRAINING split."""
    out = {}
    eps = [e for e in ENDPOINTS if e in splits]
    for ep in eps:
        names, other = set(), set()
        for n in near:
            for x, y in ((('split_a', 'name_a'), ('split_b', 'name_b')),
                         (('split_b', 'name_b'), ('split_a', 'name_a'))):
                if n[x[0]] == ep:
                    if n[y[0]] in TRAINING:
                        names.add(n[x[1]])
                    elif n[y[0]] in ENDPOINTS:
                        other.add(n[x[1]])
        n_ep = C.INPUTS[ep]['n']
        out[ep] = dict(n=n_ep, vs_training=len(names),
                       frac_vs_training=round(len(names) / n_ep, 4),
                       vs_other_endpoint=len(other),
                       names_vs_training=sorted(names))
    sweep = {}
    for t in TOL_SWEEP:
        sub = [n for n in near if n['mean_abs'] <= t]
        per = {}
        for ep in eps:
            s = set()
            for n in sub:
                if n['split_a'] == ep and n['split_b'] in TRAINING:
                    s.add(n['name_a'])
                if n['split_b'] == ep and n['split_a'] in TRAINING:
                    s.add(n['name_b'])
            per[ep] = len(s)
        sweep['tol_%.1f' % t] = dict(pairs=len(sub), per_endpoint=per)
    out['tolerance_sweep'] = sweep
    return out


# ---------------------------------------------------------------------------
# s4br -- nearest same-dimension training neighbour. d2_leakage_sweep.py:288-357
# ---------------------------------------------------------------------------

def step_endpoint_nn(groups, splits, topk=TOPK_D2):
    out = {}
    for ep in [e for e in ENDPOINTS if e in splits]:
        rows = []
        for dim, members in groups.items():
            eps = [m for m in members if m[0] == ep]
            if not eps:
                continue
            trs = [m for m in members if m[0] in TRAINING]
            if not trs:
                for sp, nm, _ in eps:
                    rows.append(dict(name=nm, dims='%dx%d' % dim, n_candidates=0,
                                     nearest=None, nearest_split=None,
                                     nearest_name=None))
                continue
            T = np.stack([m[2] for m in trs])
            k_use = len(trs) if topk in (0, None) else min(topk, len(trs))
            for sp, nm, vec in eps:
                rms = np.sqrt(((T - vec) ** 2).mean(axis=1))
                order = np.argsort(rms)[:k_use]
                A = np.asarray(Image.open(os.path.join(C.ipath(ep), nm))
                               .convert('RGB'), np.int16)
                best = (1e9, None, None)
                for k in order:
                    tsp, tnm, _ = trs[k]
                    B = np.asarray(Image.open(os.path.join(C.ipath(tsp), tnm))
                                   .convert('RGB'), np.int16)
                    if A.shape != B.shape:
                        continue
                    m = float(np.abs(A - B).mean())
                    if m < best[0]:
                        best = (m, tsp, tnm)
                rows.append(dict(name=nm, dims='%dx%d' % dim,
                                 n_candidates=len(trs),
                                 nearest=(round(best[0], 3) if best[1] else None),
                                 nearest_split=best[1], nearest_name=best[2]))
        vals = sorted(r['nearest'] for r in rows if r['nearest'] is not None)
        gap = None
        for i in range(1, len(vals)):
            if vals[i] - vals[i - 1] > 5 * max(vals[i - 1], 1.0):
                gap = dict(below=vals[i - 1], above=vals[i], n_below=i,
                           ratio=round(vals[i] / max(vals[i - 1], 1e-9), 2))
                break
        out[ep] = dict(n=len(rows), n_checkable=len(vals),
                       n_unchecked=sum(1 for r in rows if r['nearest'] is None),
                       sorted_nearest=[round(v, 2) for v in vals],
                       largest_gap=gap, rows=rows)
        _p('  s4br %-8s n=%d checkable=%d gap=%s'
           % (ep, len(rows), len(vals), gap))
    return out


# ---------------------------------------------------------------------------
# s5r -- how much would a contaminated CHAMELEON column be inflated?
# ---------------------------------------------------------------------------

def _percentiles(clean, dirty):
    """D2's percentile method (d2_leakage_sweep.py:397-400), unchanged."""
    if not len(dirty) or not len(clean):
        return []
    srt = np.sort(np.asarray(clean, float))
    return [float(np.searchsorted(srt, d) / len(srt)) for d in dirty]


def _skew(pcts):
    if not pcts:
        return 'UNVERIFIED'
    m = float(np.mean(pcts))
    return 'none' if 0.25 <= m <= 0.75 else ('easier' if m > 0.75 else 'harder')


def step_difficulty(leaked_names, polarity):
    """s5r-a. Model-free per-image difficulty proxies from the canonical masks.

    `polarity` comes from s0's per-source declaration, so an inverted mask source
    cannot silently turn every proxy inside out.

    Direction is stated per proxy rather than folded into one score, because
    combining them needs sign choices and weights that nothing here justifies.
    """
    import cv2
    from scipy import ndimage, stats

    img_dir, msk_dir = C.ipath('chamnew'), C.ipath('chamnew_gt')
    masks = {int(MASK_RE.search(f).group(1)): f for f in C.listing('chamnew_gt')}
    leaked = {os.path.splitext(n)[0] for n in leaked_names}

    rows = []
    for nm in C.listing('chamnew'):
        stem = os.path.splitext(nm)[0]
        k = int(MASK_RE.search(stem).group(1))
        if k not in masks:
            continue
        binm, _ = _mask_object(os.path.join(msk_dir, masks[k]), polarity)
        fg = binm > 0
        g = np.asarray(Image.open(os.path.join(img_dir, nm)).convert('L'), float)
        if g.shape != fg.shape:
            g = np.asarray(Image.fromarray(g.astype(np.uint8)).resize(
                (fg.shape[1], fg.shape[0]), Image.BILINEAR), float)
        area = float(fg.mean())
        er = cv2.erode(fg.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
        boundary = int((fg.astype(np.uint8) - er).sum())
        n_obj = int(ndimage.label(fg)[1])
        contrast = (abs(float(g[fg].mean()) - float(g[~fg].mean()))
                    if fg.any() and (~fg).any() else 0.0)
        rows.append(dict(name=nm, leaked=int(stem in leaked),
                         object_area_frac=round(area, 5),
                         boundary_complexity=round(boundary / max(fg.sum(), 1), 5),
                         fg_bg_contrast=round(contrast, 3),
                         n_components=n_obj))

    # higher value = easier (+1) or harder (-1); declared, not inferred
    direction = dict(object_area_frac=+1, boundary_complexity=-1,
                     fg_bg_contrast=+1, n_components=-1)
    proxies = {}
    for key, sign in direction.items():
        clean = [r[key] for r in rows if not r['leaked']]
        dirty = [r[key] for r in rows if r['leaked']]
        pct = _percentiles(clean, dirty)
        # percentile is in the raw variable; flip so >0.75 always reads "easier"
        pct_easy = pct if sign > 0 else [1.0 - p for p in pct]
        try:
            u = stats.mannwhitneyu(dirty, clean, alternative='two-sided')
            p_val, u_stat = float(u.pvalue), float(u.statistic)
            rbc = 2.0 * u_stat / (len(dirty) * len(clean)) - 1.0
        except Exception:
            p_val, rbc = None, None
        sd = np.sqrt((np.var(dirty, ddof=1) + np.var(clean, ddof=1)) / 2.0)
        proxies[key] = dict(
            direction=('higher=easier' if sign > 0 else 'higher=harder'),
            leaked_mean=round(float(np.mean(dirty)), 5),
            clean_mean=round(float(np.mean(clean)), 5),
            percentile_mean=round(float(np.mean(pct_easy)), 4),
            percentile_min=round(float(np.min(pct_easy)), 4),
            percentile_q1=round(float(np.percentile(pct_easy, 25)), 4),
            percentile_median=round(float(np.median(pct_easy)), 4),
            percentile_q3=round(float(np.percentile(pct_easy, 75)), 4),
            percentile_max=round(float(np.max(pct_easy)), 4),
            percentiles=[round(p, 4) for p in pct_easy],
            skew=_skew(pct_easy), mannwhitney_p=p_val,
            rank_biserial=(round(float(rbc), 4) if rbc is not None else None),
            cohens_d=(round(float((np.mean(dirty) - np.mean(clean)) / sd), 4)
                      if sd else None))
        _p('  s5r-a %-20s leaked %.4f vs clean %.4f  pct %.3f  skew=%s'
           % (key, proxies[key]['leaked_mean'], proxies[key]['clean_mean'],
              proxies[key]['percentile_mean'], proxies[key]['skew']))
    return dict(n=len(rows), n_leaked=sum(r['leaked'] for r in rows),
                proxies=proxies, rows=rows)


def step_inference(leaked_names, polarity):
    """s5r-b. Inference-only score split. NOT a CHAMELEON endpoint result.

    Exists solely to quantify how much a contaminated CHAMELEON column would be
    inflated. Trains nothing: an existing checkpoint is loaded and no optimizer
    runs. MyTest.py is deliberately not modified -- it excludes CHAMELEON on
    purpose, and this does not reopen that door.
    """
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    sys.path.insert(0, C.REPO)
    from Src.model.SINet.SINet import SINet_ResNet50
    sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
    import metrics as Measure

    ck = os.path.join(C.REPO, CKPT)
    if not os.path.isfile(ck):
        return dict(status='NO-CHECKPOINT', checkpoint=CKPT)

    model = SINet_ResNet50().cuda()
    state = torch.load(ck, map_location='cpu')
    model.load_state_dict(state)
    loaded = model.state_dict()
    copied = sum(torch.equal(v.to(loaded[k].device), loaded[k])
                 for k, v in state.items())
    assert copied == len(state), (
        'checkpoint load copied only %d/%d tensors from %s -- refusing to score '
        'on partially loaded weights (Explanations/CHECKPOINT_LOADING_BUG.md)'
        % (copied, len(state), CKPT))
    model.eval()

    tf = transforms.Compose([transforms.Resize((TESTSIZE, TESTSIZE)),
                             transforms.ToTensor(),
                             transforms.Normalize(IMNET_MEAN, IMNET_STD)])
    os.makedirs(PREDS, exist_ok=True)
    masks = {int(MASK_RE.search(f).group(1)): f for f in C.listing('chamnew_gt')}
    leaked = {os.path.splitext(n)[0] for n in leaked_names}

    # The two mask sets disagree (s0: mean IoU 0.69 after polarity alignment), so
    # every score is computed against BOTH. The absolute value is mask-set
    # dependent; the leaked-vs-clean SPLIT must not be, and that is the check.
    gt_repo_dir = os.path.join(C.REPO, 'Dataset/Test/CHAMELEON/GT')
    repo_gt = {}
    pol_repo = None
    if os.path.isdir(gt_repo_dir):
        repo_gt = {int(MASK_RE.search(f).group(1)): f
                   for f in sorted(os.listdir(gt_repo_dir)) if MASK_RE.search(f)}
        pol_repo = source_polarity([os.path.join(gt_repo_dir, f)
                                    for f in repo_gt.values()])[0]

    per_image = []
    with torch.no_grad():
        for nm in C.listing('chamnew'):
            stem = os.path.splitext(nm)[0]
            k = int(MASK_RE.search(stem).group(1))
            if k not in masks:
                continue
            gt, _ = _mask_object(os.path.join(C.ipath('chamnew_gt'), masks[k]),
                                 polarity)
            im = Image.open(os.path.join(C.ipath('chamnew'), nm)).convert('RGB')
            x = tf(im).unsqueeze(0).cuda()
            _, cam = model(x)
            cam = F.interpolate(cam, size=gt.shape, mode='bilinear',
                                align_corners=True)
            cam = cam.sigmoid().data.cpu().numpy().squeeze()
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
            pred = (cam * 255).astype(np.uint8)
            Image.fromarray(pred).save(os.path.join(PREDS, stem + '.png'))
            row = dict(name=stem, leaked=int(stem in leaked))
            for tag, garr in (('', gt),
                              ('_repogt', (_mask_object(
                                  os.path.join(gt_repo_dir, repo_gt[k]), pol_repo)[0]
                                  if k in repo_gt else None))):
                if garr is None:
                    continue
                p = pred
                if p.shape != garr.shape:
                    p = np.asarray(Image.fromarray(pred).resize(
                        (garr.shape[1], garr.shape[0]), Image.NEAREST))
                mae, sm = Measure.MAE(), Measure.Smeasure()
                mae.step(pred=p, gt=garr)
                sm.step(pred=p, gt=garr)
                row['mae' + tag] = float(mae.get_results()['mae'])
                row['sm' + tag] = float(sm.get_results()['sm'])
            per_image.append(row)

    def split(key):
        allv = np.array([r[key] for r in per_image if key in r])
        cl = np.array([r[key] for r in per_image if key in r and not r['leaked']])
        dy = np.array([r[key] for r in per_image if key in r and r['leaked']])
        return allv, cl, dy

    res = dict(status='OK', checkpoint=CKPT, n_scored=len(per_image),
               n_leaked=int(sum(r['leaked'] for r in per_image)),
               mask_set_primary='chamnew_gt (author-sourced), polarity %s' % polarity,
               mask_set_robustness='Dataset/Test/CHAMELEON/GT, polarity %s' % pol_repo,
               note=('inference only; NOT a CHAMELEON endpoint result. Exists to '
                     'quantify column inflation, never to be quoted as performance. '
                     'Absolute values are mask-set dependent (the two sets agree at '
                     'mean IoU 0.69); the leaked-vs-clean split is reported against '
                     'both sets so the conclusion does not rest on one.'),
               per_image=per_image)
    keys = [k for k in ('mae', 'sm', 'mae_repogt', 'sm_repogt')
            if any(k in r for r in per_image)]
    for key in keys:
        allv, cl, dy = split(key)
        # MAE: lower is better, so a leaked subset that is EASIER pulls the column
        # down. Sa: higher is better, so it pulls the column up.
        pct_raw = _percentiles(cl, dy)
        pct_easy = ([1.0 - p for p in pct_raw] if key.startswith('mae')
                    else pct_raw)
        res[key] = dict(
            all=round(float(allv.mean()), 6),
            clean=round(float(cl.mean()), 6) if cl.size else None,
            leaked=round(float(dy.mean()), 6) if dy.size else None,
            inflation=(round(float(cl.mean() - allv.mean()), 6) if cl.size else None),
            percentile_mean=(round(float(np.mean(pct_easy)), 4) if pct_easy else None),
            percentile_min=(round(float(np.min(pct_easy)), 4) if pct_easy else None),
            percentile_max=(round(float(np.max(pct_easy)), 4) if pct_easy else None),
            percentiles=[round(p, 4) for p in pct_easy],
            skew=_skew(pct_easy))
        _p('  s5r-b %-11s all %.6f  clean %.6f  leaked %.6f  inflation %s  skew=%s'
           % (key, res[key]['all'], res[key]['clean'], res[key]['leaked'],
              res[key]['inflation'], res[key]['skew']))
    res['split_direction_agrees_across_mask_sets'] = bool(
        all(k in res for k in ('mae', 'mae_repogt'))
        and (res['mae']['inflation'] or 0) * (res['mae_repogt']['inflation'] or 0) > 0)
    return res


# ---------------------------------------------------------------------------
# s6r -- mechanism and design scope, asserted from source
# ---------------------------------------------------------------------------

def _lines(rel):
    with open(os.path.join(C.REPO, rel)) as fh:
        return fh.read().split('\n')


def _find(rel, needle, start=0):
    for i, ln in enumerate(_lines(rel)[start:], start + 1):
        if needle in ln:
            return i, ln.strip()
    return None, None


def step_scope():
    """Re-derive the mechanism's line numbers instead of trusting a document.

    D2_RESULTS.md 3.0 cites "MyTrain.py:220,297 feeds get_tarloader". Both are
    wrong: 220 is the --source_root help string and 297 is the EMA teacher weight
    copy. Recorded as a correction rather than silently fixed -- a citation that
    cannot be re-derived is exactly the defect the traceability rule exists for.
    """
    call_ln, call_txt = _find('MyTrain.py', 'get_tarloader(')
    tr_ln, tr_txt = _find('MyTrain.py', "'--target_root'")
    cls_ln, _ = _find('MyTrain.py', 'new_source_root = cls(')
    def_ln, def_txt = _find('Src/utils/Dataloader.py', 'def get_tarloader(')
    src_ln, _ = _find('Src/utils/Dataloader.py', 'def get_srcloader(')

    dl = _lines('Src/utils/Dataloader.py')
    tar_cls = next((i for i, l in enumerate(dl, 1) if l.startswith('class TarDataset')),
                   None)
    tar_body = '\n'.join(dl[tar_cls - 1:tar_cls + 40]) if tar_cls else ''
    getitem_ret = re.search(r'return\s+([^\n]+)',
                            tar_body.split('__getitem__', 1)[-1]) if tar_body else None

    cls_src = '\n'.join(_lines('CLS.py'))
    d220 = _lines('MyTrain.py')[219].strip()
    d297 = _lines('MyTrain.py')[296].strip()

    readme = '\n'.join(_lines('README.md'))
    cham_hits = len(re.findall(r'CHAMELEON', readme))
    cnc_line = next((l for l in _lines('README.md') if 'CNC' in l and 'CHAMELEON' in l),
                    '')
    test_real = readme.split('Test (Real)', 1)[-1].split('Val (Real)', 1)[0] \
        if 'Test (Real)' in readme else ''
    t1 = '\n'.join(_lines('Experiments/REPRODUCE_TABLE1_v2.md'))

    res = dict(
        get_tarloader_call_site='MyTrain.py:%s' % call_ln,
        get_tarloader_call_text=call_txt,
        get_tarloader_def='Src/utils/Dataloader.py:%s' % def_ln,
        get_srcloader_def='Src/utils/Dataloader.py:%s' % src_ln,
        tarloader_has_gt_root=bool(def_txt and 'gt_root' in def_txt),
        srcloader_has_gt_root=bool(
            _find('Src/utils/Dataloader.py', 'def get_srcloader(')[1]
            and 'gt_root' in _find('Src/utils/Dataloader.py', 'def get_srcloader(')[1]),
        tardataset_class='Src/utils/Dataloader.py:%s' % tar_cls,
        tardataset_getitem_return=(getitem_ret.group(1).strip()
                                   if getitem_ret else 'UNPARSED'),
        tardataset_returns_two=bool(getitem_ret
                                    and getitem_ret.group(1).count(',') == 1),
        target_root_line='MyTrain.py:%s' % tr_ln, target_root_text=tr_txt,
        target_dir_has_GT=os.path.isdir(os.path.join(C.REPO, 'Dataset/Target/GT')),
        cls_call_site='MyTrain.py:%s' % cls_ln,
        cls_reads_target_image=("target_root + 'Image/'" in cls_src
                                or 'target_root+"Image/"' in cls_src),
        cls_gt_root_none=bool(re.search(r'gt_root\s*=\s*None', cls_src)),
        # the two lines D2_RESULTS.md cited, quoted so the correction is legible
        d2_cited_line_220=d220, d2_cited_line_297=d297,
        d2_citation_correct=(call_ln in (220, 297)),
        # --- the README's own design ---
        readme_cham_mentions=cham_hits,
        readme_cham_under_cnc_source=bool('CNC' in cnc_line),
        readme_cnc_line=cnc_line.strip(),
        readme_test_real_lists_cham=('CHAMELEON' in test_real),
        readme_test_real=' '.join(test_real.split())[:160],
        dataset_source_CNC_exists=os.path.isdir(
            os.path.join(C.REPO, 'Dataset/Source/CNC')),
        dataset_test_CHAMELEON_exists=os.path.isdir(
            os.path.join(C.REPO, 'Dataset/Test/CHAMELEON')),
        reproduce_table1_cham_mentions=len(re.findall(r'CHAMELEON', t1)),
        mytest_dataset_choices=(_find('MyTest.py', "'--dataset'")[1] or ''),
        result_dirs_with_cham=sorted(
            d for d in (os.listdir(os.path.join(C.REPO, 'Result'))
                        if os.path.isdir(os.path.join(C.REPO, 'Result')) else [])
            if 'CHAM' in d.upper()))
    _p('s6r: get_tarloader at %s (D2 cited 220,297 -> %s); README CHAMELEON x%d, '
       'CNC source=%s, Test(Real) lists it=%s; Source/CNC on disk=%s'
       % (res['get_tarloader_call_site'],
          'CORRECT' if res['d2_citation_correct'] else 'WRONG',
          res['readme_cham_mentions'], res['readme_cham_under_cnc_source'],
          res['readme_test_real_lists_cham'], res['dataset_source_CNC_exists']))
    return res


# ---------------------------------------------------------------------------
# s7r -- the published artifacts, the detector cross-check, the release
# ---------------------------------------------------------------------------

ANON_PATTERNS = ('/home/', 'ai-server', 'Akshat', 'akshat', 'imagine.io',
                 'Dataset/', 'Snapshot/', 'Result/', 'rebuild/', '.venv',
                 'experiments/lakered', 'S2R-COD/')


def _partner_pool(name):
    if name.startswith('COD10K'):
        return 'cod10k_train'
    if name.startswith('camourflage'):
        return 'camo'
    return 'other'


def step_package(near, nn, s0, args):
    """Emit the community resource, cross-check the public detector, build release."""
    os.makedirs(OUT, exist_ok=True)
    # -- the confirmed canonical pairs, selected the way D2 selected its 41:
    # -- s4b rows for the endpoint with nearest <= tol, rank-ordered.
    rows = [r for r in nn['chamnew']['rows']
            if r['nearest'] is not None and r['nearest'] <= NEAR_TOL]
    rows.sort(key=lambda r: r['nearest'])
    manifest = []
    for i, r in enumerate(rows, 1):
        pa = os.path.join(C.ipath('chamnew'), r['name'])
        pb = os.path.join(C.ipath(r['nearest_split']), r['nearest_name'])
        m = DET._measure(pa, pb)
        v_dqt, agree, qa, qb = DET.qtable_verdict(pa, pb)
        # D2's method, kept verbatim for comparability. Note it reports "differ"
        # when one side has NO table at all -- absence of evidence read as
        # evidence. v_dqt separates that case out as 'na'.
        q_pil_same = (DET.qtable_pil(pa) == DET.qtable_pil(pb))
        fa, fb = DET.container_format(pa), DET.container_format(pb)
        manifest.append(dict(
            rank=i, endpoint='chamnew', endpoint_image=r['name'],
            training_split=r['nearest_split'], training_image=r['nearest_name'],
            # field set and rounding identical to d2_export_duplicates.py:220-228
            dims=r['dims'], mean_abs=round(m['mean_abs'], 3),
            p99_abs=round(m['p99_abs'], 1), max_abs=m['max_abs'],
            frac_gt8=round(m['frac_gt8'], 5),
            content_std=round(m['content_std'], 1),
            qtables_identical=int(q_pil_same),
            endpoint_kb=round(os.path.getsize(pa) / 1024),
            training_kb=round(os.path.getsize(pb) / 1024),
            qtables_differ_dqt=int(v_dqt == 'differ'),
            qtable_evidence=v_dqt,
            qtable_methods_agree=int(bool(agree)),
            format_endpoint=fa, format_training=fb,
            formats_differ=int(fa != fb),
            partner_pool=_partner_pool(r['nearest_name'])))

    fields = ('rank', 'endpoint', 'endpoint_image', 'training_split',
              'training_image', 'dims', 'mean_abs', 'p99_abs', 'max_abs',
              'frac_gt8', 'content_std', 'qtables_identical', 'endpoint_kb',
              'training_kb', 'qtables_differ_dqt', 'qtable_evidence',
              'qtable_methods_agree', 'format_endpoint', 'format_training',
              'formats_differ', 'partner_pool')
    with open(os.path.join(OUT, 'd2r_duplicate_pairs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(manifest)

    # -- the community resource. Content-addressed, no local path anywhere.
    n_can, agg_can, _ = C.dir_digest(C.ipath('chamnew'))
    n_tgt, agg_tgt, _ = C.dir_digest(C.ipath('tgt'))
    g = nn['chamnew']['largest_gap']
    sweep = {('%.1f' % t): len({n['name_a'] if n['split_a'] == 'chamnew'
                                else n['name_b']
                                for n in near
                                if n['mean_abs'] <= t
                                and (('chamnew' in (n['split_a'], n['split_b']))
                                     and (n['split_a'] in TRAINING
                                          or n['split_b'] in TRAINING))})
             for t in TOL_SWEEP}
    resource = dict(
        schema_version='1.0',
        finding=('Of this CHAMELEON release, %d of %d images are re-encoded copies '
                 'of images in the COD10K-train / CAMO training pool. Any model '
                 'trained on COD10K-train has therefore seen them. The CHAMELEON '
                 'evaluation column is unreliable for such a model. Test PIXELS '
                 'enter training; test MASKS do not -- this is a transductive '
                 'protocol violation, not label leakage.'
                 % (len(manifest), n_can)),
        method=dict(descriptor='32x32 greyscale BILINEAR, no contrast normalisation',
                    shortlist_rms=SHORTLIST_RMS, tolerance_mean_abs=NEAR_TOL,
                    topk_full_res_verified=TOPK_D2,
                    verification='full-resolution mean|A-B| over RGB int16',
                    quantization_tables='PIL Image.quantization AND raw DQT marker parse'),
        reference_set=dict(name='CHAMELEON', provenance='author-sourced release',
                           n=n_can, listing_sha256=agg_can),
        training_set=dict(name='COD10K-train (+CAMO)', n=n_tgt,
                          listing_sha256=agg_tgt),
        contaminated=[dict(chameleon_image=r['endpoint_image'],
                           partner=r['training_image'],
                           partner_pool=r['partner_pool'], dims=r['dims'],
                           mean_abs=r['mean_abs'], p99_abs=r['p99_abs'],
                           max_abs=r['max_abs'], frac_gt8=r['frac_gt8'],
                           content_std=r['content_std'],
                           qtable_evidence=r['qtable_evidence'],
                           qtables_differ=bool(r['qtable_evidence'] == 'differ'),
                           format_chameleon=r['format_endpoint'],
                           format_partner=r['format_training'],
                           formats_differ=bool(r['formats_differ']))
                      for r in manifest],
        counts=dict(n_contaminated=len(manifest),
                    share=round(len(manifest) / n_can, 4),
                    vs_cod10k_train=sum(1 for r in manifest
                                        if r['partner_pool'] == 'cod10k_train'),
                    vs_camo=sum(1 for r in manifest if r['partner_pool'] == 'camo')),
        tolerance_sweep=sweep,
        nn_gap=(dict(n_below=g['n_below'], below=g['below'], above=g['above'],
                     ratio=g['ratio']) if g else None),
        unchecked=dict(n=nn['chamnew']['n_unchecked'],
                       reason=('no same-dimension training candidate; unchecked is '
                               'not clean')),
        limitations=('LOWER BOUND. Crops, flips, colour shifts, rescaled copies '
                     'outside every dimension group, and different photographs of '
                     'one specimen are not detected and are not claimed.'),
        provenance=dict(log_block='EXP D2R', commit=C.git_commit(),
                        timestamp=C.now()))
    C.save_json(os.path.join(OUT, 'chameleon_contaminated.json'), resource)

    # -- does the standalone public tool reproduce the in-repo sweep? ---------
    _p('s7r: cross-checking the standalone detector...')
    det = DET.sweep(C.ipath('chamnew'), C.ipath('tgt'), workers=args.workers,
                    quiet=True)
    mine = {(r['endpoint_image'], r['training_image']) for r in manifest}
    theirs = {(p['image_a'], p['image_b']) for p in det['pairs']}
    det_names = set(det['contaminated']['names'])
    my_names = {r['endpoint_image'] for r in manifest}
    selftest = DET.self_test()

    # -- the anonymized release bundle ---------------------------------------
    if os.path.isdir(RELEASE):
        shutil.rmtree(RELEASE)
    os.makedirs(RELEASE)
    shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'detect_contamination.py'),
                    os.path.join(RELEASE, 'detect_contamination.py'))
    shutil.copyfile(os.path.join(OUT, 'chameleon_contaminated.json'),
                    os.path.join(RELEASE, 'chameleon_contaminated.json'))
    # strip the provenance commit: it identifies a private repository
    rel = json.load(open(os.path.join(RELEASE, 'chameleon_contaminated.json')))
    rel['provenance'] = dict(log_block='EXP D2R', timestamp=rel['provenance']['timestamp'])
    with open(os.path.join(RELEASE, 'chameleon_contaminated.json'), 'w') as fh:
        json.dump(rel, fh, indent=2, sort_keys=True)
    cp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CLEAN_PROTOCOL.md')
    if os.path.isfile(cp):
        shutil.copyfile(cp, os.path.join(RELEASE, 'CLEAN_PROTOCOL.md'))
    with open(os.path.join(RELEASE, 'README.md'), 'w') as fh:
        fh.write(RELEASE_README % (len(manifest), n_can,
                                   100 * len(manifest) / n_can,
                                   resource['counts']['vs_cod10k_train'],
                                   resource['counts']['vs_camo']))

    hits = []
    for f in sorted(os.listdir(RELEASE)):
        blob = open(os.path.join(RELEASE, f), 'rb').read()
        for pat in ANON_PATTERNS:
            if pat.encode() in blob:
                hits.append('%s:%s' % (f, pat))
    _p('s7r: detector selftest=%s, pairs %d/%d, names %d/%d; release scan hits=%s'
       % ('PASS' if selftest else 'FAIL', len(mine & theirs), len(mine),
          len(det_names & my_names), len(my_names), hits or 'none'))
    return dict(manifest=manifest, resource=resource,
                detector_selftest=bool(selftest),
                detector_pairs_agree='%d/%d' % (len(mine & theirs), len(mine)),
                detector_names_agree='%d/%d' % (len(det_names & my_names),
                                                len(my_names)),
                detector_extra_pairs=len(theirs - mine),
                anonymization_hits=hits,
                release_files=sorted(os.listdir(RELEASE)))


RELEASE_README = """# CHAMELEON / COD10K-train contamination: detector and leaked-image list

**%d of %d images (%.1f%%) in the CHAMELEON camouflaged-object dataset are
re-encoded copies of images in the COD10K-train split** -- %d of them in
COD10K-train and %d in CAMO.

Any model trained on COD10K-train has therefore already seen those images.
A CHAMELEON evaluation column reported for such a model is not an independent
measurement.

## What is here

| File | What it is |
|---|---|
| `chameleon_contaminated.json` | the leaked-image list: every CHAMELEON filename that is a training re-encode, its training-pool partner, and the per-pair evidence |
| `detect_contamination.py` | the detector, standalone. Point it at any two image directories |
| `CLEAN_PROTOCOL.md` | which evaluation columns are safe to report, with measured contamination rates |

## Reproduce it

```
python detect_contamination.py --self-test          # verify the tool itself
python detect_contamination.py CHAMELEON_DIR COD10K_TRAIN_DIR
```

`listing_sha256` in the JSON is the aggregate digest of the sorted
`sha256  filename` listing of each directory, so you can confirm you hold the
same sets before comparing counts.

## What the evidence is

Same exact dimensions; mean absolute pixel difference at full resolution within
tolerance; and **differing JPEG quantization tables** in every pair -- a copied
file keeps its table, a re-encode cannot. The tables are extracted two
independent ways (PIL, and a raw DQT-marker parse) so the verdict does not rest
on one library. The count is also confirmed by a discontinuity in the sorted
nearest-neighbour distances, which owes nothing to the tolerance.

## Scope, stated precisely

- Test **pixels** enter training. Test **masks** do not. This is a transductive
  protocol violation, not label leakage, and no claim of memorisation is made.
- Every count is a **lower bound**. Crops, flips, colour shifts, rescaled copies
  that leave every dimension group, and different photographs of one specimen are
  not detected. Images with no same-dimension candidate are reported as
  `unchecked`; unchecked is not clean.
- No dataset images are redistributed here. The underlying photographs are
  third-party licensed; this bundle carries filenames, measurements and the tool.
"""


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s0,s4r,s4br,s5r,s6r,s7r')
    ap.add_argument('--splits', default='full', choices=['full', 'min'])
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--rehash', action='store_true')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()

    steps = [s.strip() for s in args.steps.split(',') if s.strip()]
    splits = SPLITS_FULL if args.splits == 'full' else SPLITS_MIN
    os.makedirs(OUT, exist_ok=True)
    metrics, thresholds, old_claims, artifacts = [], [], [], []

    def A(p):
        artifacts.append(os.path.relpath(p, C.REPO))

    # every split's declared count is asserted before anything is measured
    counts = {sp: len(C.listing(sp)) for sp in splits}
    for sp in splits:
        assert counts[sp] == C.INPUTS[sp]['n'], (sp, counts[sp],
                                                 C.INPUTS[sp]['n'])
    recs = step_hash(splits, workers=args.workers, rehash=args.rehash)

    s0 = near = nn = diff = inf = scope = pack = None
    groups = None

    if 's0' in steps:
        s0 = step_reconcile(recs)
        C.save_json(os.path.join(OUT, 'd2r_reconcile.json'),
                    {k: v for k, v in s0.items() if k not in ('rows', 'mask_rows')})
        A(os.path.join(OUT, 'd2r_reconcile.json'))
        for name, rows in (('d2r_reconcile.csv', s0['rows']),
                           ('d2r_mask_reconcile.csv', s0['mask_rows'])):
            if rows:
                with open(os.path.join(OUT, name), 'w', newline='') as fh:
                    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
                A(os.path.join(OUT, name))
        metrics += [
            ('cham_ondisk_n', s0['cham']['n'], s0['cham']['path']),
            ('chamnew_canonical_n', s0['chamnew']['n'],
             '%s, author-sourced' % s0['chamnew']['path']),
            ('copies_identical_fhash', '%d/%d' % (s0['identical_fhash'],
                                                  s0['chamnew']['n']),
             'sha256 of file bytes, set-based'),
            ('copies_identical_phash', '%d/%d' % (s0['identical_phash'],
                                                  s0['chamnew']['n']),
             'decoded-RGB hash, set-based'),
            ('copies_reconcile_outcome', s0['outcome'],
             'boundaries declared in REAUDIT_PLAN.md 1.5'),
            ('copies_qtables_identical', '%d/%d' % (s0['qtables_equal'],
                                                    s0['chamnew']['n']),
             'raw DQT parse'),
            ('d2_measured_copy', s0['d2_measured_copy'],
             'git show 17dfbbf:rebuild/common.py'),
            ('d2_manifest_kb_agrees', s0['d2_manifest_kb_agrees'],
             'committed d2_duplicate_pairs.csv endpoint_kb vs cham on disk'),
            ('d2_manifest_dims_agrees', s0['d2_manifest_dims_agrees'],
             'committed d2_duplicate_pairs.csv dims vs cham on disk'),
            ('masks_join_is_bijection', s0['masks']['join_bijection'],
             'mask-N.png <-> animal-N.png over 1..76'),
            ('masks_polarity_canonical', s0['masks']['polarity_canonical'],
             'declared per SOURCE from the aggregate white fraction %.4f'
             % s0['masks']['white_frac_canonical']),
            ('masks_polarity_repo', s0['masks']['polarity_repo'],
             'aggregate white fraction %.4f' % s0['masks']['white_frac_repo']),
            ('masks_polarity_agrees', s0['masks']['polarity_agrees'],
             'trap T2, REBUILD_PLAN.md 2 -- a silent inversion would corrupt s5r'),
            ('masks_mean_iou_as_stored', s0['masks']['mean_iou_as_stored'],
             'white-vs-white, before any polarity interpretation'),
            ('masks_mean_iou_polarity_aligned',
             s0['masks']['mean_iou_polarity_aligned'],
             'object-vs-object, both sources aligned to SOD polarity'),
            ('masks_iou_aligned_above_0.9',
             '%d/%d' % (s0['masks']['n_iou_above_0_9'], s0['masks']['n_joined']), ''),
            ('masks_canonical_vs_repo_identical',
             '%d/%d' % (s0['masks']['n_identical'], s0['masks']['n_joined']),
             'exact equality after polarity alignment'),
            ('masks_canonical_is_rgba', s0['masks']['canonical_is_rgba'],
             'alpha fg frac mean %s -- alpha carries no mask'
             % s0['masks']['alpha_fg_frac_mean']),
        ]
        thresholds += [
            ('T1 both CHAMELEON copies contain exactly 76 images',
             s0['cham']['n'] == 76 and s0['chamnew']['n'] == 76),
            ('T2 the two copies are pixel-identical at phash level, 76/76',
             s0['identical_phash'] == 76 and s0['outcome'] == 'a'),
            ('T3 D2 measured the repo copy Dataset/Test/CHAMELEON/Imgs, established '
             'from committed artifacts',
             s0['d2_measured_copy'] == 'Dataset/Test/CHAMELEON/Imgs'),
            ('T19 canonical vs repo CHAMELEON masks reconciled, with polarity '
             'declared per source (REPORTED; disagreement is itself a finding)',
             s0['masks']['join_bijection']
             and s0['masks']['mean_iou_polarity_aligned'] is not None),
        ]

    if 's4r' in steps or 's4br' in steps:
        groups = _descriptors(splits, args.workers)

    if 's4r' in steps:
        near, short_d2, short_new = step_near(recs, groups)
        contam = contamination(near, splits)
        with open(os.path.join(OUT, 'd2r_near_duplicates.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(near[0]))
            w.writeheader()
            w.writerows(near)
        A(os.path.join(OUT, 'd2r_near_duplicates.csv'))
        C.save_json(os.path.join(OUT, 'd2r_endpoint_contamination.json'), contam)
        A(os.path.join(OUT, 'd2r_endpoint_contamination.json'))

        conf_d2 = [n for n in near
                   if n['split_a'] != 'chamnew' and n['split_b'] != 'chamnew']
        ep_tr_d2 = [n for n in conf_d2
                    if (n['split_a'] in ENDPOINTS and n['split_b'] in TRAINING)
                    or (n['split_b'] in ENDPOINTS and n['split_a'] in TRAINING)]
        cn = contam['chamnew']
        pools = [_partner_pool(n['name_b'] if n['split_a'] == 'chamnew'
                               else n['name_a'])
                 for n in near
                 if 'chamnew' in (n['split_a'], n['split_b'])
                 and (n['split_a'] in TRAINING or n['split_b'] in TRAINING)]
        # Every endpoint is emitted, not just the two CHAMELEON copies: the other
        # three rates are cited by CLEAN_PROTOCOL.md, and a number a document uses
        # has to exist as a logged metric rather than only inside an artifact.
        ep_note = {'chamnew': 'distinct canonical images that are re-encodes of '
                              'training data',
                   'cham': 'the repo copy, re-measured',
                   'test': 'COD10K-test', 'nc4k': 'NC4K', 'val': 'CAMO-val'}
        metrics += [
            ('nearvdup_%s_matching_training' % ep,
             '%d/%d (%.1f%%)' % (contam[ep]['vs_training'], contam[ep]['n'],
                                 100 * contam[ep]['frac_vs_training']),
             ep_note.get(ep, ep))
            for ep in ('chamnew', 'cham', 'test', 'nc4k', 'val') if ep in contam]
        metrics += [
            ('partner_pairs_in_cod10k_train',
             '%d/%d' % (pools.count('cod10k_train'), len(pools)),
             'PAIR level: confirmed canonical-CHAMELEON <-> training pairs whose '
             'training side is in the public COD10K-train split'),
            ('partner_pairs_in_camo', '%d/%d' % (pools.count('camo'), len(pools)),
             'PAIR level; one CHAMELEON image can have more than one partner'),
            ('near_dup_candidate_pairs_shortlisted', short_d2,
             'D2 splits only, exhaustive within-dimension, descriptor RMS <= 14'),
            ('near_dup_shortlisted_involving_chamnew', short_new,
             'the author-sourced set, counted apart so D2 stays comparable'),
            ('near_duplicate_pairs_confirmed', len(conf_d2),
             'D2 splits only, full-res verified, mean|diff| <= 6.0'),
            ('near_dup_endpoint_vs_training', len(ep_tr_d2), 'D2 splits only'),
            ('near_duplicate_pairs_confirmed_with_chamnew', len(near),
             'all %d splits' % len(splits)),
        ]
        for t in TOL_SWEEP:
            metrics.append(('nearvdup_chamnew_at_tol_%g' % t,
                            '%d/%d' % (contam['tolerance_sweep']['tol_%.1f' % t]
                                       ['per_endpoint']['chamnew'], cn['n']),
                            'post-hoc filter on the tol=6.0 set, as in D2'))
        d2_contam = json.load(open(os.path.join(C.exp_dir('D2', 'out'),
                                                'd2_endpoint_contamination.json')))
        old_claims += [
            ('D2 nearvdup_cham_images_matching_training', '41/76 (53.9%)',
             'MATCH' if (cn['vs_training'] == 41 and cn['n'] == 76) else 'MISMATCH'),
            ('D2 near_dup_candidate_pairs_shortlisted', '323',
             'MATCH' if short_d2 == 323 else 'MISMATCH'),
            ('D2 near_duplicate_pairs_confirmed', '132',
             'MATCH' if len(conf_d2) == 132 else 'MISMATCH'),
            ('D2 near_dup_endpoint_vs_training', '49',
             'MATCH' if len(ep_tr_d2) == 49 else 'MISMATCH'),
            ('D2 nearvdup_cham_at_tol_1,2,3,5,6', '11|26|37|40|41 /76',
             'MATCH' if [contam['tolerance_sweep']['tol_%.1f' % t]['per_endpoint']
                         ['chamnew'] for t in TOL_SWEEP] == [11, 26, 37, 40, 41]
             else 'MISMATCH'),
            ('D2 CHAMELEON leaked name set (41 names)',
             '%d names' % len(d2_contam['cham']['names_vs_training']),
             'MATCH' if (set(cn['names_vs_training'])
                         == set(d2_contam['cham']['names_vs_training']))
             else 'MISMATCH'),
        ]
        thresholds += [
            ('T4 canonical CHAMELEON contamination equals D2 41/76 (no value '
             'overwritten -- both reported)',
             cn['vs_training'] == 41 and cn['n'] == 76),
            ('T7 global s4 metrics reproduce D2 over D2 splits (323 shortlisted, '
             '132 confirmed, 49 endpoint-vs-training)',
             short_d2 == 323 and len(conf_d2) == 132 and len(ep_tr_d2) == 49),
            ('T8 the CHAMELEON tolerance sweep reproduces 11/26/37/40/41',
             [contam['tolerance_sweep']['tol_%.1f' % t]['per_endpoint']['chamnew']
              for t in TOL_SWEEP] == [11, 26, 37, 40, 41]),
            ('T9 the canonical matched names equal D2 committed name set',
             set(cn['names_vs_training'])
             == set(d2_contam['cham']['names_vs_training'])),
            ('T10 partner pool decomposition measured (NEW -- no prior value)',
             len(pools) > 0),
        ]

    if 's4br' in steps:
        nn = step_endpoint_nn(groups, splits, topk=TOPK_D2)
        C.save_json(os.path.join(OUT, 'd2r_endpoint_nearest.json'),
                    {k: {kk: vv for kk, vv in v.items() if kk != 'rows'}
                     for k, v in nn.items()})
        A(os.path.join(OUT, 'd2r_endpoint_nearest.json'))
        with open(os.path.join(OUT, 'd2r_endpoint_nearest.csv'), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['endpoint', 'name', 'dims', 'n_candidates', 'nearest',
                        'nearest_split', 'nearest_name'])
            for ep, v in nn.items():
                for r in v['rows']:
                    w.writerow([ep, r['name'], r['dims'], r['n_candidates'],
                                r['nearest'], r['nearest_split'], r['nearest_name']])
        A(os.path.join(OUT, 'd2r_endpoint_nearest.csv'))

        sens = {}
        for k in TOPK_SWEEP:
            if k == TOPK_D2:
                sens['topk_%s' % k] = nn['chamnew']['largest_gap']
                continue
            _p('  s4br sensitivity: re-running chamnew at TOPK=%s' % (k or 'all'))
            one = step_endpoint_nn({d: [m for m in ms
                                        if m[0] in ('chamnew',) + tuple(TRAINING)]
                                    for d, ms in groups.items()},
                                   ['chamnew'], topk=k)
            sens['topk_%s' % (k or 'all')] = one['chamnew']['largest_gap']
        C.save_json(os.path.join(OUT, 'd2r_topk_sensitivity.json'), sens)
        A(os.path.join(OUT, 'd2r_topk_sensitivity.json'))

        g = nn['chamnew']['largest_gap']
        for ep in [e for e in ('chamnew', 'cham', 'test', 'nc4k', 'val')
                   if e in nn]:
            v = nn[ep]
            gg = v['largest_gap']
            metrics += [
                ('epNN_%s_checkable' % ep, '%d/%d' % (v['n_checkable'], v['n']),
                 'has >=1 same-dimension training candidate'),
                ('epNN_%s_unchecked' % ep, '%d/%d' % (v['n_unchecked'], v['n']),
                 'unchecked is NOT clean'),
                ('epNN_%s_gap' % ep,
                 ('%d below %.2f, next at %.2f' % (gg['n_below'], gg['below'],
                                                   gg['above']) if gg else 'none'),
                 ('first >5x jump in sorted nearest distances; ratio %.2fx'
                  % gg['ratio']) if gg else 'no >5x jump found'),
            ]
        for k, v in sens.items():
            metrics.append(('epNN_chamnew_gap_%s' % k,
                            ('%d below %.2f, next at %.2f'
                             % (v['n_below'], v['below'], v['above'])
                             if v else 'none'),
                            'sensitivity; TOPK=8 is the comparison run'))
        d2_nn = json.load(open(os.path.join(C.exp_dir('D2', 'out'),
                                            'd2_endpoint_nearest.json')))
        old_claims += [
            ('D2 epNN_cham_checkable', '51/76',
             'MATCH' if nn['cham']['n_checkable'] == 51 else 'MISMATCH'),
            ('D2 epNN_cham_gap', '41 below 5.51, next at 40.58',
             'MATCH' if (nn['cham']['largest_gap']
                         and nn['cham']['largest_gap']['n_below'] == 41
                         and abs(nn['cham']['largest_gap']['below']
                                 - d2_nn['cham']['largest_gap']['below']) < 0.01
                         and abs(nn['cham']['largest_gap']['above']
                                 - d2_nn['cham']['largest_gap']['above']) < 0.01)
             else 'MISMATCH'),
        ]
        n_tol6 = len({r['name'] for r in nn['chamnew']['rows']
                      if r['nearest'] is not None and r['nearest'] <= NEAR_TOL})
        thresholds += [
            ('T6 s4br gap exists with above/below > 5 AND n_below equals the '
             'tol=6.0 matched count',
             bool(g and g['ratio'] > 5 and g['n_below'] == n_tol6)),
            ('T11 the gap and n_below are stable across TOPK in {8,32,all}',
             len({(v or {}).get('n_below') for v in sens.values()}) == 1),
        ]

    if 's5r' in steps:
        leaked = sorted({r['name'] for r in nn['chamnew']['rows']
                         if r['nearest'] is not None and r['nearest'] <= NEAR_TOL})
        # polarity comes from s0's per-source declaration, or is declared here if
        # s0 was not part of this run -- never assumed
        pol = (s0['masks']['polarity_canonical'] if s0 else
               source_polarity([os.path.join(C.ipath('chamnew_gt'), f)
                                for f in C.listing('chamnew_gt')])[0])
        metrics.append(('s5r_mask_polarity_used', pol,
                        'canonical masks, declared per source in s0'))
        diff = step_difficulty(leaked, pol)
        C.save_json(os.path.join(OUT, 'd2r_difficulty.json'),
                    {k: v for k, v in diff.items() if k != 'rows'})
        A(os.path.join(OUT, 'd2r_difficulty.json'))
        with open(os.path.join(OUT, 'd2r_difficulty.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(diff['rows'][0]))
            w.writeheader()
            w.writerows(diff['rows'])
        A(os.path.join(OUT, 'd2r_difficulty.csv'))
        for k, v in diff['proxies'].items():
            metrics.append(
                ('leaked_pct_%s' % k,
                 '%.4f  [%.3f .. %.3f]' % (v['percentile_mean'],
                                           v['percentile_min'], v['percentile_max']),
                 'percentile of the leaked set within the clean set, oriented so '
                 '>0.75 = easier; %s; skew=%s; MWU p=%s'
                 % (v['direction'], v['skew'], v['mannwhitney_p'])))
        inf = step_inference(leaked, pol)
        C.save_json(os.path.join(OUT, 'd2r_impact.json'), inf)
        A(os.path.join(OUT, 'd2r_impact.json'))
        if inf['status'] == 'OK':
            for key, lbl in (('mae', 'MAE'), ('sm', 'Sa'),
                             ('mae_repogt', 'MAE_repoGT'),
                             ('sm_repogt', 'Sa_repoGT')):
                if key not in inf:
                    continue
                v = inf[key]
                prov = ('INFERENCE ONLY -- not a CHAMELEON endpoint result; %s'
                        % ('author-sourced masks' if not key.endswith('repogt')
                           else "the repo's repackaged GT, as a mask-set "
                                'robustness check'))
                metrics += [
                    ('cham_%s_all_%d' % (lbl, inf['n_scored']), v['all'], prov),
                    ('cham_%s_clean_%d' % (lbl, inf['n_scored'] - inf['n_leaked']),
                     v['clean'], 'the uncontaminated subset'),
                    ('cham_%s_leaked_%d' % (lbl, inf['n_leaked']), v['leaked'],
                     'the contaminated subset'),
                    ('cham_column_inflation_%s' % lbl, v['inflation'],
                     'clean-subset value minus what the full column would report; '
                     'sign convention: for MAE lower is better'),
                    ('cham_%s_leaked_percentile' % lbl,
                     '%.4f  [%.3f .. %.3f]' % (v['percentile_mean'],
                                               v['percentile_min'],
                                               v['percentile_max']),
                     'oriented so >0.75 = easier; skew=%s' % v['skew']),
                ]
            metrics.append(
                ('cham_split_direction_agrees_across_mask_sets',
                 inf.get('split_direction_agrees_across_mask_sets'),
                 'the two mask sets agree at mean IoU 0.69, so the leaked-vs-clean '
                 'conclusion is checked against both'))
        skews = [v['skew'] for v in diff['proxies'].values()]
        thresholds += [
            ('T14 the leaked-set difficulty percentile is reported with its full '
             'distribution for every proxy, and skew is declared',
             all(v.get('percentiles') for v in diff['proxies'].values())),
            ('T15 the inference-based leaked-vs-clean split is computed and the '
             'inflation stated numerically', inf['status'] == 'OK'),
        ]
        metrics.append(('leaked_difficulty_skew_by_proxy', '|'.join(skews),
                        'object_area|boundary|contrast|components, in order'))

    if 's6r' in steps:
        scope = step_scope()
        C.save_json(os.path.join(OUT, 'd2r_scope.json'), scope)
        A(os.path.join(OUT, 'd2r_scope.json'))
        metrics += [
            ('get_tarloader_call_site', scope['get_tarloader_call_site'],
             're-derived from source; D2_RESULTS.md 3.0 cites MyTrain.py:220,297'),
            ('d2_citation_correct', scope['d2_citation_correct'],
             'MyTrain.py:220 is %r; :297 is %r'
             % (scope['d2_cited_line_220'][:44], scope['d2_cited_line_297'][:44])),
            ('tarloader_reads_no_gt', not scope['tarloader_has_gt_root'],
             'get_tarloader has no gt_root parameter; get_srcloader does'),
            ('tardataset_returns_two_no_mask', scope['tardataset_returns_two'],
             'returns %s' % scope['tardataset_getitem_return'][:50]),
            ('target_dir_has_no_GT', not scope['target_dir_has_GT'],
             'Dataset/Target/ has no GT/ subdirectory'),
            ('cls_reads_target_with_gt_root_none',
             scope['cls_reads_target_image'] and scope['cls_gt_root_none'],
             'pseudo-labels are teacher CAMs, never ground truth'),
            ('readme_cham_mentions', scope['readme_cham_mentions'],
             'README.md'),
            ('readme_lists_cham_as_source_only',
             scope['readme_cham_under_cnc_source']
             and not scope['readme_test_real_lists_cham'],
             'CNC synthetic-source bundle; never under Test (Real)'),
            ('dataset_source_CNC_exists', scope['dataset_source_CNC_exists'],
             "the README's own directory for CNC"),
            ('dataset_test_CHAMELEON_exists', scope['dataset_test_CHAMELEON_exists'],
             'undocumented local addition'),
            ('reproduce_table1_cham_mentions',
             scope['reproduce_table1_cham_mentions'],
             'Experiments/REPRODUCE_TABLE1_v2.md'),
            ('result_dirs_with_cham_predictions',
             len(scope['result_dirs_with_cham']),
             'no CHAMELEON predictions exist under Result/'),
        ]
        old_claims += [
            ('D2_RESULTS.md 3.0 cites MyTrain.py:220,297 for get_tarloader',
             'MyTrain.py:220,297',
             'MISMATCH' if not scope['d2_citation_correct'] else 'MATCH'),
            ('REBUILD_PLAN.md 3 names CHAMELEON a secondary endpoint',
             'secondary endpoint',
             'MISMATCH' if (scope['readme_cham_under_cnc_source']
                            and not scope['readme_test_real_lists_cham'])
             else 'MATCH'),
        ]
        thresholds += [
            ('T12 every mechanism assertion holds from source, and the '
             'MyTrain.py:220,297 citation is recorded as wrong',
             (not scope['tarloader_has_gt_root'])
             and scope['tardataset_returns_two']
             and (not scope['target_dir_has_GT'])
             and scope['cls_reads_target_image'] and scope['cls_gt_root_none']
             and (not scope['d2_citation_correct'])),
            ('T13 the README lists CHAMELEON only as CNC source, Source/CNC is '
             'absent from disk, Test/CHAMELEON is present, and Table 1 has no '
             'CHAMELEON column',
             scope['readme_cham_under_cnc_source']
             and not scope['readme_test_real_lists_cham']
             and not scope['dataset_source_CNC_exists']
             and scope['dataset_test_CHAMELEON_exists']
             and scope['reproduce_table1_cham_mentions'] == 0),
        ]

    if 's7r' in steps:
        # s7r can run standalone off its own committed artifacts, the way
        # d2_export_duplicates.py reads s4b's CSV instead of re-deriving it.
        if near is None:
            src = os.path.join(OUT, 'd2r_near_duplicates.csv')
            if not os.path.isfile(src):
                raise SystemExit('missing %s -- run --steps s4r first' % src)
            near = [dict(r, mean_abs=float(r['mean_abs']))
                    for r in csv.DictReader(open(src))]
        if nn is None:
            src = os.path.join(OUT, 'd2r_endpoint_nearest.csv')
            if not os.path.isfile(src):
                raise SystemExit('missing %s -- run --steps s4br first' % src)
            nn = {}
            for r in csv.DictReader(open(src)):
                d = nn.setdefault(r['endpoint'], dict(rows=[]))
                d['rows'].append(dict(
                    name=r['name'], dims=r['dims'],
                    n_candidates=int(r['n_candidates']),
                    nearest=(float(r['nearest']) if r['nearest'] else None),
                    nearest_split=(r['nearest_split'] or None),
                    nearest_name=(r['nearest_name'] or None)))
            js = os.path.join(OUT, 'd2r_endpoint_nearest.json')
            if os.path.isfile(js):
                for ep, v in json.load(open(js)).items():
                    if ep in nn:
                        nn[ep].update({k: vv for k, vv in v.items() if k != 'rows'})
        pack = step_package(near, nn, s0, args)
        A(os.path.join(OUT, 'd2r_duplicate_pairs.csv'))
        A(os.path.join(OUT, 'chameleon_contaminated.json'))
        pl = [r['partner_pool'] for r in pack['manifest']]
        metrics += [
            ('partner_images_in_cod10k_train',
             '%d/%d' % (pl.count('cod10k_train'), len(pl)),
             'IMAGE level: distinct canonical CHAMELEON images whose NEAREST '
             'training partner is in the public COD10K-train split'),
            ('partner_images_in_camo', '%d/%d' % (pl.count('camo'), len(pl)),
             'IMAGE level, nearest partner'),
            ('detector_selftest', 'PASS' if pack['detector_selftest'] else 'FAIL',
             'synthetic known-answer case, no repo data'),
            ('detector_reproduces_s4r_pairs', pack['detector_pairs_agree'],
             'standalone tool vs in-repo sweep, same constants'),
            ('detector_reproduces_s4r_names', pack['detector_names_agree'], ''),
            ('detector_extra_pairs', pack['detector_extra_pairs'],
             'pairs the tool found that s4br did not select'),
            ('anonymization_scan_clean', not pack['anonymization_hits'],
             'patterns: %s' % ', '.join(ANON_PATTERNS)),
            ('release_files', ', '.join(pack['release_files']), 'rebuild/D2_reaudit/release/'),
        ]
        n = len(pack['manifest'])
        qd = sum(r['qtables_differ_dqt'] for r in pack['manifest'])
        qp = sum(1 for r in pack['manifest'] if not r['qtables_identical'])
        ag = sum(r['qtable_methods_agree'] for r in pack['manifest'])
        na = sum(1 for r in pack['manifest'] if r['qtable_evidence'] == 'na')
        fd = sum(r['formats_differ'] for r in pack['manifest'])
        nonjpeg = sorted({r['endpoint_image'] for r in pack['manifest']
                          if r['format_endpoint'] != 'JPEG'})
        allfmt = [DET.container_format(os.path.join(C.ipath('chamnew'), f))
                  for f in C.listing('chamnew')]
        metrics += [
            ('canonical_files_not_JPEG',
             '%d/%d' % (sum(1 for f in allfmt if f != 'JPEG'), len(allfmt)),
             'container format from magic bytes, not extension: %s'
             % ', '.join('%s=%d' % (k, allfmt.count(k)) for k in sorted(set(allfmt)))),
            ('qtables_differ_PIL', '%d/%d' % (qp, n),
             "PIL Image.quantization, D2's method verbatim -- counts a MISSING "
             'table as "differing"'),
            ('qtables_differ_DQT', '%d/%d' % (qd, n),
             'raw 0xFFDB marker parse; %d pair(s) not applicable (a side is not '
             'JPEG, so there is no table to compare)' % na),
            ('qtables_not_applicable', '%d/%d' % (na, n),
             'pairs whose endpoint side is %s' % (', '.join(nonjpeg) or 'n/a')),
            ('pairs_differing_in_container_format', '%d/%d' % (fd, n),
             'a PNG/JPEG pair of one photograph is re-encoding evidence in its '
             'own right, independent of any quantization table'),
            ('qtable_methods_agree', '%d/%d' % (ag, n),
             'the two extractions return the same differ/same/na verdict'),
            ('mean_abs_range', '%.3f .. %.3f' % (pack['manifest'][0]['mean_abs'],
                                                 pack['manifest'][-1]['mean_abs'])
             if pack['manifest'] else 'n/a', 'confirmed canonical pairs'),
        ]
        old_claims.append(
            ('D2 quantization tables differ in 41/41 pairs', '41/41',
             'MATCH' if (qd == n == 41 and na == 0) else 'MISMATCH'))
        thresholds += [
            ('T5 quantization tables differ in every confirmed pair AND the PIL '
             'and raw-DQT extractions agree pair-for-pair',
             qd == n and ag == n),
            ('T5b every confirmed pair carries re-encoding evidence from SOME '
             'independent channel: a differing quantization table, or a differing '
             'container format', qd + fd >= n and ag == n),
            ('T16 the standalone detector passes its self-test and reproduces the '
             "in-repo sweep's canonical pair list",
             pack['detector_selftest']
             and pack['detector_names_agree'].split('/')[0]
             == pack['detector_names_agree'].split('/')[1]),
            ('T17 the release bundle is free of identifying paths and names',
             not pack['anonymization_hits']),
        ]

    # -- comparison table: every prior D2 value beside the new one ------------
    if old_claims:
        with open(os.path.join(OUT, 'd2r_comparison.csv'), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['metric', 'd2_value', 'd2r_verdict'])
            for lbl, old, verdict in old_claims:
                w.writerow([lbl, old, verdict])
        A(os.path.join(OUT, 'd2r_comparison.csv'))

    dirty = C.subprocess.check_output(
        ['git', '-C', C.REPO, 'status', '--porcelain', '--',
         'Dataset', 'Result', 'Snapshot'], text=True).strip()
    thresholds += [
        ('T18 no /tmp, archive or scratchpad path is read; a missing input fails '
         'loudly (common.ipath has no fallback)', True),
        ('T20 nothing under Dataset/, Result/ or Snapshot/ is modified',
         dirty == ''),
    ]

    cmd = ('LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_reaudit.py --steps %s '
           '--splits %s' % (','.join(steps), args.splits))
    notes = NOTES
    text = C.log_block(EXP, cmd, metrics, thresholds, old_claims, artifacts,
                       representation=('decoded pixels (the only level that survives '
                                       're-encoding) + canonical GT masks for s5r'),
                       trains='NO', notes=notes, write=not args.no_log)
    print(text)


NOTES = """s5r-b IS INFERENCE ONLY AND IS NOT A CHAMELEON ENDPOINT RESULT. It loads an existing checkpoint, trains nothing, writes no checkpoint, and exists solely to quantify how much a contaminated CHAMELEON column would be inflated. It must never be quoted as a performance number. MyTest.py was not modified: it excludes CHAMELEON deliberately and this does not reopen that door.
EVERY COUNT IS A LOWER BOUND. Coverage is exact duplicates plus same-dimension re-encodes. Rescaled copies that leave every dimension group, crops, flips, colour shifts and different photographs of one specimen are NOT detected and are not claimed. Endpoint images with no same-dimension training candidate are reported as unchecked -- unchecked is not clean.
The tolerance sweep is a POST-HOC FILTER on the tol=6.0 result set, exactly as D2 computed it, not five independent sweeps. TOPK=8 is D2's s4b shortlist depth and is the comparison run; the TOPK 32/all runs bound its recall and are reported as sensitivity, never as a substitute.
D2's global s4 metrics (323 shortlisted / 132 confirmed / 49 endpoint-vs-training) are recomputed over D2's ORIGINAL 8 SPLITS ONLY, with the author-sourced set counted apart, so the committed figures stay directly comparable. The 9-split totals are reported separately.
CORRECTION TO D2's QUANTIZATION-TABLE EVIDENCE, found by the second extraction. animal-19.jpg and animal-28.jpg in the CHAMELEON release are PNG files carrying a .jpg extension (magic bytes 89504e47), so they have NO JPEG quantization table. D2 compared tables with PIL and `!=`, which reports "the tables differ" when one side has no table at all -- absence of evidence read as evidence. animal-19 is one of the leaked 41, so D2's "quantization tables differ in 41/41 pairs" is properly 40/41 differing plus 1 not-applicable. The CONCLUSION for that pair is unaffected and arguably stronger: its two files differ in CONTAINER FORMAT (PNG vs JPEG), which is re-encoding evidence in its own right. T5 is left FAILING against its declared wording, and T5b states the surviving claim.
CITATION CORRECTION: D2_RESULTS.md 3.0 cites MyTrain.py:220,297 as feeding get_tarloader. Line 220 is the --source_root help string and line 297 is the EMA teacher weight copy; the call site is re-derived here from source. The MECHANISM D2 described is correct -- the target pool enters training unlabeled and CLS pseudo-labels it from teacher CAMs -- only the line numbers were wrong. Recorded, not silently fixed.
SCOPE: this is a TRANSDUCTIVE PROTOCOL VIOLATION, NOT LABEL LEAKAGE. Test pixels enter training through the unlabeled target pool; CHAMELEON ground-truth masks never enter training. No claim of memorisation is made. It inflates a CHAMELEON evaluation column; it does not by itself invalidate a method whose COD10K-test and NC4K numbers are clean.
FRAMING: the contamination is a property of two PUBLIC datasets, not of this repo. The partners live in COD10K-train and CAMO, so any model trained on COD10K-train has seen those CHAMELEON images. Separately, README.md lists CHAMELEON only inside the CNC synthetic-SOURCE bundle and never under Test (Real), and Dataset/Source/CNC does not exist on disk while the undocumented Dataset/Test/CHAMELEON does. REBUILD_PLAN.md 3 -- ours -- adopted CHAMELEON as a secondary endpoint without checking that. Both go to REVISION_TABLE.md.
UNVERIFIED: whether the PUBLISHED S2R-COD paper reports a CHAMELEON column anywhere. The PDF is not in this checkout and Experiments/REPRODUCE_TABLE1_v2.md has no such column. Not claimed either way. Flagged and not answered: under --task C2C the CNC bundle (CAMO+NC4K+CHAMELEON) is the SOURCE pool, so for C2C, CHAMELEON is training data by design; a C2C table reporting CHAMELEON as test would be a direct source/test collision. Resolving that needs the paper.
PROVENANCE DIRECTION IS INFERENCE, NOT MEASUREMENT: CHAMELEON (2015) predates COD10K (2020), so the parsimonious reading is that COD10K-train absorbed CHAMELEON images during its construction. Only pool membership is measured.
NO DIFFICULTY SKEW IS DETECTABLE, so no inflation figure is claimed. All four model-free proxies and all four inference metrics put the leaked set's percentile within the clean set in 0.448-0.559, where 0.5 is indistinguishable, and none of the proxies separates the groups (Mann-Whitney p 0.47-0.99). The SIGN of the score difference even flips with the mask release used: the leaked subset scores worse against the author-sourced masks and marginally better against the repackaged GT, so split_direction_agrees_across_mask_sets is False. The defensible claim is therefore about INDEPENDENCE, not inflation -- the column cannot be read as an independent measurement -- and a specific "inflated by X" figure would be over-reading the data. This mirrors D2's own COD10K result (percentile 0.4761, no memorisation signature) at 20x the contamination rate.
THE TWO CHAMELEON MASK RELEASES DISAGREE, which is a second and independent reason to distrust any CHAMELEON column: mean IoU 0.693 after polarity alignment, only 27/76 identical, and OPPOSITE stored polarity (author-sourced object_black at white fraction 0.7187; repackaged object_white at 0.1400). Polarity was declared PER SOURCE from the aggregate, never per image, per REBUILD_PLAN.md A2. On identical predictions that mask-set disagreement alone moves MAE by 2.7x (0.2196 vs 0.0816), so a published CHAMELEON number depends on which mask release was used.
The COD10K-test, NC4K and CAMO contamination rates carried into CLEAN_PROTOCOL.md were measured against ON-DISK copies, not author-sourced ones. That is the same weakness this re-audit exists to close for CHAMELEON, and it is marked in the protocol table rather than papered over: the same author-sourced re-audit is owed for them."""


if __name__ == '__main__':
    main()

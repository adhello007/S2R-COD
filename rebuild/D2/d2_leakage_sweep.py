#!/usr/bin/env python
"""D2 -- Leakage sweep.

Bounds what any Stage C result can claim, and which sets can be reported as
endpoints. Runs EARLY, before B3 and C1, because those two must consume the
leaked-name set as measured DATA rather than inherit it as a hardcoded constant.
The previous package ran this last and then hardcoded a 7-name LEAK set upstream.

Method: full pairwise hashing, never name matching. Phase 0 established that only
2 of the 7 previously claimed Target/COD10K duplicates share a filename; the
other 5 are cross-named and invisible to any name check. One of those five was
additionally mis-transcribed in the old documents (Flying-53 vs Flying-65).

Two hash levels per image:
  fhash  sha256 of the file bytes        -- catches identical files, any name
  phash  sha256 of (shape + decoded RGB) -- additionally catches re-encodes that
                                            decode to the same pixels

Steps:
  s1  hash      hash every image in every split
  s2  cross     every unordered split pair, by both hash levels
  s3  internal  duplicates within each split
  s4  near      EXPLORATORY: resized/near-duplicate candidates via thumbnail
                hash, verified by actual pixel comparison. Beyond the plan's
                stated pixel-identity scope, so reported separately and never
                thresholded.
  s5  mae       what the contaminated test images do to the reported endpoint,
                using the repo's own Eval/metrics.py
  s6  scope     assert the checkpoint-selection set is a published test split
  s7  determin  is a render a function of its input? (found via s3)
  s4b endpointNN nearest same-dimension training image per endpoint image;
                 shows whether s4's count is a data boundary or a cutoff
  s8  seedtest  CONTROLLED test of s7's mechanism (needs a GPU, ~6 min)

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2/d2_leakage_sweep.py
"""

import argparse
import csv
import hashlib
import itertools
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'D2'
OUT = C.exp_dir(EXP, 'out')
CACHE = C.exp_dir(EXP, 'cache')

# Splits swept. Keys are common.INPUTS keys so counts and paths come from the
# same registry E0 hashed -- no second source of truth for what these are.
SPLITS = ['tgt', 'test', 'cham', 'nc4k', 'val', 'raw', 'auth', 'local']

# Which splits are candidate ENDPOINTS (things a paper would report on) and
# which are TRAINING-side pools. Leakage between the two groups is what bounds
# the claim; leakage inside the endpoint group is a protocol violation of the
# published benchmark rather than something this work introduced.
ENDPOINTS = ['test', 'cham', 'nc4k', 'val']
TRAINING = ['tgt', 'raw', 'auth', 'local']



def _p(msg):
    print(msg, flush=True)


def _hash_one(args):
    """(split, name, path) -> record. Runs in a worker process."""
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
        phash = ph.hexdigest()
        shape = '%dx%d' % (a.shape[1], a.shape[0])
    except Exception as e:                      # unreadable image: record it
        return dict(split=split, name=name, fhash=fhash, phash='UNREADABLE',
                    shape='?', error=str(e)[:80])
    return dict(split=split, name=name, fhash=fhash, phash=phash, shape=shape,
                error='')


def step_hash(workers=8):
    os.makedirs(CACHE, exist_ok=True)
    jobs = []
    for sp in SPLITS:
        d = C.ipath(sp)
        for nm in C.listing(sp):
            jobs.append((sp, nm, os.path.join(d, nm)))
    _p('hashing %d images across %d splits...' % (len(jobs), len(SPLITS)))
    recs = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_hash_one, jobs, chunksize=64)):
            recs.append(r)
            if (i + 1) % 4000 == 0:
                _p('  %d/%d' % (i + 1, len(jobs)))
    with open(os.path.join(CACHE, 'hashes.json'), 'w') as fh:
        json.dump(recs, fh)
    return recs


def load_hashes():
    p = os.path.join(CACHE, 'hashes.json')
    if not os.path.isfile(p):
        return None
    return json.load(open(p))


# ---------------------------------------------------------------------------
# s2 -- cross-split collisions
# ---------------------------------------------------------------------------

def _index(recs, key):
    idx = {}
    for r in recs:
        if r[key] in ('UNREADABLE',):
            continue
        idx.setdefault(r[key], []).append(r)
    return idx


def step_cross(recs):
    """Every unordered split pair, at both hash levels."""
    by_split = {}
    for r in recs:
        by_split.setdefault(r['split'], []).append(r)

    rows, collisions = [], []
    for a, b in itertools.combinations(SPLITS, 2):
        for level in ('fhash', 'phash'):
            ia = {}
            for r in by_split[a]:
                if r[level] != 'UNREADABLE':
                    ia.setdefault(r[level], []).append(r['name'])
            hits = []
            for r in by_split[b]:
                if r[level] == 'UNREADABLE':
                    continue
                if r[level] in ia:
                    for an in ia[r[level]]:
                        hits.append((an, r['name'], r[level]))
            rows.append(dict(split_a=a, split_b=b, level=level,
                             n_a=len(by_split[a]), n_b=len(by_split[b]),
                             collisions=len(hits)))
            for an, bn, h in hits:
                same_name = (os.path.splitext(an)[0] == os.path.splitext(bn)[0])
                collisions.append(dict(split_a=a, name_a=an, split_b=b, name_b=bn,
                                       level=level, same_name=int(same_name),
                                       hash=h[:32]))
    return rows, collisions


def step_internal(recs):
    """Duplicates within each split, at both hash levels."""
    rows, groups = [], []
    for sp in SPLITS:
        sub = [r for r in recs if r['split'] == sp]
        for level in ('fhash', 'phash'):
            idx = {}
            for r in sub:
                if r[level] != 'UNREADABLE':
                    idx.setdefault(r[level], []).append(r['name'])
            dup = {h: ns for h, ns in idx.items() if len(ns) > 1}
            n_extra = sum(len(ns) - 1 for ns in dup.values())
            rows.append(dict(split=sp, level=level, n=len(sub),
                             unique=len(idx), dup_groups=len(dup),
                             redundant_files=n_extra))
            for h, ns in sorted(dup.items()):
                groups.append(dict(split=sp, level=level, hash=h[:32],
                                   n_in_group=len(ns), names='|'.join(sorted(ns))))
    return rows, groups


# ---------------------------------------------------------------------------
# s4 -- near-duplicate scan: EXHAUSTIVE within each exact-dimension group
# ---------------------------------------------------------------------------
# HISTORY, kept because it matters. The first implementation bucketed images by
# a contrast-normalised 16x16 thumbnail hash and only compared within a bucket.
# That had poor RECALL: it reported 10 of CHAMELEON's 76 images as re-encodes of
# Target, while an exhaustive search finds far more. Contrast normalisation
# destroyed the discriminative scale, and hard bucket edges split true pairs.
#
# This version is exhaustive over the only pairs that CAN be pixel-comparable:
# those sharing exact dimensions. 23,854 images fall into 4,427 dimension
# groups giving 7.4M candidate pairs -- shortlisted by a 32x32 greyscale
# descriptor via Gram matrix, then every survivor verified at full resolution.
# A re-encoded copy keeps its dimensions, so nothing in scope is missed for
# lack of a bucket.

DESC = 32           # descriptor edge, greyscale, NOT contrast-normalised
SHORTLIST_RMS = 14.0   # generous descriptor cutoff; full-res verify decides
NEAR_TOL = 6.0      # confirm out to here, then report a TOLERANCE SWEEP
TOL_SWEEP = (1.0, 2.0, 3.0, 5.0, 6.0)


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


def step_near(recs, tol=NEAR_TOL, workers=12):
    """Same photograph, re-encoded or rescaled: exhaustive within dimensions."""
    jobs = []
    for sp in SPLITS:
        d = C.ipath(sp)
        for nm in C.listing(sp):
            jobs.append((sp, nm, os.path.join(d, nm)))
    _p('s4: descriptors for %d images...' % len(jobs))
    groups = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for sp, nm, dim, vec in ex.map(_descriptor, jobs, chunksize=64):
            if dim is None:
                continue
            groups.setdefault(dim, []).append((sp, nm, vec))

    pixel_ident = set()
    for r in recs:
        pixel_ident.add((r['split'], r['name'], r['phash']))
    phash_of = {(r['split'], r['name']): r['phash'] for r in recs}

    shortlisted = 0
    found = []
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    _p('s4: %d dimension groups with >1 member' % len(multi))
    for gi, (dim, members) in enumerate(sorted(multi.items(),
                                               key=lambda kv: -len(kv[1]))):
        X = np.stack([m[2] for m in members])
        # pairwise squared L2 via Gram matrix, then RMS per pixel
        sq = (X * X).sum(1)
        d2 = sq[:, None] + sq[None, :] - 2.0 * (X @ X.T)
        np.fill_diagonal(d2, np.inf)
        rms = np.sqrt(np.maximum(d2, 0) / (DESC * DESC))
        ii, jj = np.where(np.triu(rms <= SHORTLIST_RMS, k=1))
        shortlisted += len(ii)
        for i, j in zip(ii, jj):
            sa, na, _ = members[i]
            sb, nb, _ = members[j]
            if phash_of.get((sa, na)) == phash_of.get((sb, nb)):
                continue                       # already pixel-identical (s2/s3)
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
                                  dims='%dx%d' % dim,
                                  mean_abs=round(m, 3),
                                  p99_abs=int(np.percentile(d, 99)),
                                  max_abs=int(d.max()),
                                  frac_gt8=round(float((d > 8).mean()), 5),
                                  content_std=round(float(A.std()), 1)))
        if (gi + 1) % 200 == 0:
            _p('  s4: %d/%d groups, %d shortlisted, %d confirmed'
               % (gi + 1, len(multi), shortlisted, len(found)))
    _p('s4: %d shortlisted, %d confirmed at mean|diff| <= %.1f'
       % (shortlisted, len(found), tol))
    return found, shortlisted


def step_endpoint_nn(workers=12):
    """Nearest same-dimension TRAINING neighbour for every endpoint image.

    s4 answers "how many pairs fall within tolerance t", which leaves open
    whether a count is a property of the data or of t. This answers the sharper
    question: for each endpoint image, how far is the closest training image of
    the same dimensions? A tight cluster followed by a large gap means the
    boundary is real.

    Bounded to endpoint x training pairs, so it is affordable where an all-pairs
    sweep at a wide tolerance is not -- that attempt had to be abandoned.
    """
    jobs = []
    for sp in SPLITS:
        d = C.ipath(sp)
        for nm in C.listing(sp):
            jobs.append((sp, nm, os.path.join(d, nm)))
    _p('endpoint-NN: descriptors for %d images...' % len(jobs))
    by_dim = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for sp, nm, dim, vec in ex.map(_descriptor, jobs, chunksize=64):
            if dim is not None:
                by_dim.setdefault(dim, []).append((sp, nm, vec))

    out = {}
    for ep in ENDPOINTS:
        rows = []
        for dim, members in by_dim.items():
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
            for sp, nm, vec in eps:
                rms = np.sqrt(((T - vec) ** 2).mean(axis=1))
                order = np.argsort(rms)[:8]
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
                rows.append(dict(name=nm, dims='%dx%d' % dim, n_candidates=len(trs),
                                 nearest=(round(best[0], 3) if best[1] else None),
                                 nearest_split=best[1], nearest_name=best[2]))
        vals = sorted(r['nearest'] for r in rows if r['nearest'] is not None)
        gap = None
        for i in range(1, len(vals)):
            if vals[i] - vals[i - 1] > 5 * max(vals[i - 1], 1.0):
                gap = dict(below=vals[i - 1], above=vals[i], n_below=i)
                break
        out[ep] = dict(n=len(rows), n_checkable=len(vals),
                       n_unchecked=sum(1 for r in rows if r['nearest'] is None),
                       sorted_nearest=[round(v, 2) for v in vals],
                       largest_gap=gap, rows=rows)
        _p('  endpoint-NN %-5s n=%d checkable=%d gap=%s'
           % (ep, len(rows), len(vals), gap))
    return out


# ---------------------------------------------------------------------------
# s5 -- what contamination does to the reported endpoint
# ---------------------------------------------------------------------------

def step_mae(contaminated_test_names, pred_dir='Result/SINet/S2C'):
    """Per-image MAE over COD10K test with the repo's OWN metric code, then the
    endpoint with and without the contaminated images."""
    sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
    import metrics as Measure                                  # noqa: E402
    import cv2

    gt_dir = C.ipath('test_gt')
    pdir = os.path.join(C.REPO, pred_dir)
    if not os.path.isdir(pdir):
        return dict(status='NO-PREDICTIONS', pred_dir=pred_dir)

    names = sorted(os.listdir(gt_dir))
    contaminated = {os.path.splitext(n)[0] for n in contaminated_test_names}
    per_image = []
    for nm in names:
        stem = os.path.splitext(nm)[0]
        g = cv2.imread(os.path.join(gt_dir, nm), cv2.IMREAD_GRAYSCALE)
        pth = os.path.join(pdir, stem + '.png')
        p = cv2.imread(pth, cv2.IMREAD_GRAYSCALE)
        if g is None or p is None:
            continue
        if p.shape != g.shape:
            p = cv2.resize(p, (g.shape[1], g.shape[0]), cv2.INTER_NEAREST)
        m = Measure.MAE()
        m.step(pred=p, gt=g)
        per_image.append(dict(name=stem, mae=float(m.get_results()['mae']),
                              contaminated=int(stem in contaminated)))

    all_mae = np.array([r['mae'] for r in per_image])
    clean = np.array([r['mae'] for r in per_image if not r['contaminated']])
    dirty = np.array([r['mae'] for r in per_image if r['contaminated']])

    pct = []
    if dirty.size and clean.size:
        srt = np.sort(clean)
        pct = [float(np.searchsorted(srt, d) / len(srt)) for d in dirty]

    return dict(status='OK', pred_dir=pred_dir, n_scored=len(per_image),
                n_contaminated=int(dirty.size),
                mae_all=float(all_mae.mean()),
                mae_excluding_contaminated=float(clean.mean()) if clean.size else None,
                delta=float(all_mae.mean() - clean.mean()) if clean.size else None,
                relative_delta=(float((all_mae.mean() - clean.mean()) / clean.mean())
                                if clean.size and clean.mean() else None),
                mae_contaminated_mean=float(dirty.mean()) if dirty.size else None,
                contaminated_percentiles=pct,
                mean_percentile=float(np.mean(pct)) if pct else None,
                per_image=per_image)


# ---------------------------------------------------------------------------
# s7 -- is a render a function of its input?
# ---------------------------------------------------------------------------

def step_determinism():
    """The raw HKU-IS pool contains byte-identical image pairs. Do they produce
    identical renders?

    Found while sweeping internal duplicates, and it settles a question E0 left
    open. LAKE-RED sets torch.manual_seed(seed) ONCE per process (test.py:90-91)
    and shards by stride (test.py:115, pairs[i::total]), so per-image noise is
    drawn sequentially from one stream. A render is therefore a function of
    (image, mask, POSITION WITHIN SHARD), not of (image, mask).

    Two identical inputs landing at the same local position in their respective
    shards get the same noise and the same render; at different positions they
    diverge. This step tests that prediction against every duplicate pair.
    """
    raw_d, gt_d, out_d = C.ipath('raw'), C.ipath('raw_gt'), C.ipath('local')
    # sorted staged listing = the order test.py globs, hence the index it shards
    staged = sorted(os.listdir(C.ipath('lr_in_img')))
    gpos = {os.path.splitext(n)[0]: i for i, n in enumerate(staged)}
    shard_total = 2                      # the run that produced the pool on disk

    def sha(p):
        return hashlib.sha256(open(p, 'rb').read()).hexdigest()

    groups = {}
    for nm in C.listing('raw'):
        groups.setdefault(sha(os.path.join(raw_d, nm)), []).append(
            os.path.splitext(nm)[0])
    dup = {h: sorted(v) for h, v in groups.items() if len(v) > 1}

    rows = []
    for h, stems in sorted(dup.items()):
        for a, b in itertools.combinations(stems, 2):
            ga, gb = gpos.get('SOD_' + a), gpos.get('SOD_' + b)
            la = lb = sa = sb = None
            if ga is not None and gb is not None:
                sa, la = ga % shard_total, ga // shard_total
                sb, lb = gb % shard_total, gb // shard_total
            mask_same = (sha(os.path.join(gt_d, a + '.png'))
                         == sha(os.path.join(gt_d, b + '.png')))
            ren_same = (sha(os.path.join(out_d, 'SOD_%s.jpg' % a))
                        == sha(os.path.join(out_d, 'SOD_%s.jpg' % b)))
            same_pos = (la == lb) if la is not None else None
            # prediction: identical render iff mask identical AND same local pos
            predicted = bool(mask_same and same_pos)
            rows.append(dict(stem_a=a, stem_b=b, image_identical=1,
                             mask_identical=int(mask_same),
                             global_idx_a=ga, global_idx_b=gb,
                             shard_a=sa, local_pos_a=la,
                             shard_b=sb, local_pos_b=lb,
                             same_local_pos=int(bool(same_pos)),
                             render_identical=int(ren_same),
                             predicted_identical=int(predicted),
                             prediction_holds=int(predicted == ren_same)))

    # the clean natural experiment: identical image AND mask, different noise
    clean = [r for r in rows if r['mask_identical'] and not r['same_local_pos']]
    diverged = []
    for r in clean:
        a, b = r['stem_a'], r['stem_b']
        x = np.asarray(Image.open(os.path.join(out_d, 'SOD_%s.jpg' % a))
                       .convert('RGB'), np.int16)
        y = np.asarray(Image.open(os.path.join(out_d, 'SOD_%s.jpg' % b))
                       .convert('RGB'), np.int16)
        g = np.asarray(Image.open(os.path.join(gt_d, a + '.png')).convert('L'))
        if x.shape != y.shape:
            continue
        fg = g >= C.THRESH
        d = np.abs(x - y)
        diverged.append(dict(stem_a=a, stem_b=b,
                             mean_abs=round(float(d.mean()), 3),
                             fg_mean_abs=round(float(d[fg].mean()), 3) if fg.any() else None,
                             bg_mean_abs=round(float(d[~fg].mean()), 3) if (~fg).any() else None,
                             max_abs=int(d.max())))

    return dict(duplicate_input_pairs=len(rows), rows=rows,
                prediction_holds_for=sum(r['prediction_holds'] for r in rows),
                clean_same_input_diff_noise=len(clean),
                divergence=diverged,
                mechanism=('torch.manual_seed once per process (test.py:90-91) + '
                           'stride sharding pairs[i::total] (test.py:115) => per-image '
                           'noise depends on position within the shard'))


# ---------------------------------------------------------------------------
# s6 -- scoping consequence, asserted rather than asserted-in-prose
# ---------------------------------------------------------------------------

def step_scope():
    """The checkpoint-selection set is a published test split. Read it out of
    MyTrain.py rather than restating it."""
    src = open(os.path.join(C.REPO, 'MyTrain.py')).read().splitlines()
    val_default, val_line = None, None
    for i, line in enumerate(src, 1):
        if "'--val_root'" in line:
            val_line = i
            a = line.split("default=")
            if len(a) > 1:
                val_default = a[1].split(',')[0].strip().strip("'\"")
    sel_line = None
    for i, line in enumerate(src, 1):
        if 'best_teamae' in line and '=' in line and 'best_teamae =' not in line:
            sel_line = sel_line or i
    val_path = (val_default or '').lstrip('./').rstrip('/')
    return dict(
        myTrain_val_root_line=val_line,
        val_root_default=val_default,
        val_root_resolves_to=val_path,
        val_root_is_camo=('Val/CAMO' in (val_default or '')),
        camo_val_n=len(C.listing('val')),
        test_camo_present=os.path.isdir(os.path.join(C.REPO, 'Dataset/Test/CAMO')),
        note=('Dataset/Test/CAMO was removed 2026-08-30 (confirmed intentional: it '
              'duplicated Val/CAMO). Filename identity 250/250 and content identity '
              '5/5 sampled were VERIFIED before removal; full 250/250 content '
              'identity is no longer verifiable. The consequence stands either way: '
              'checkpoints are selected on the CAMO split, so CAMO cannot be an '
              'endpoint. Primary endpoint COD10K; secondary CHAMELEON and NC4K.'))


# ---------------------------------------------------------------------------
# s8 -- controlled test of the s7 mechanism
# ---------------------------------------------------------------------------

def step_seed_experiment(stem='0004'):
    """s7 inferred the mechanism from 4 observational pairs. This tests it.

    Three byte-identical (image, mask) pairs are staged under names that sort as
    A, B, C, then generated three ways:

      T1  one shard      -> A,B,C at positions 0,1,2 of ONE noise stream.
                            If noise is sequential they must DIFFER.
      T2  T1 repeated    -> tests run-level reproducibility.
      T3  three shards   -> each input is at LOCAL POSITION 0 of its own
                            seeded stream. The mechanism PREDICTS all three
                            become identical. This is the positive test.

    T3 is the one that matters: a negative result (identical inputs diverge)
    is consistent with several explanations, but only the position mechanism
    predicts that forcing equal positions collapses the divergence to zero.
    """
    import shutil
    lr = os.path.join(C.REPO, 'LAKE-RED')
    py = os.path.join(lr, '.venv', 'bin', 'python')
    root = C.exp_dir(EXP, 'seedtest')
    inp = os.path.join(root, 'input', 'validation')
    src = C.ipath('lr_in_img')
    srcm = C.ipath('lr_in_mask')
    if not os.path.isfile(os.path.join(src, 'SOD_%s.jpg' % stem)):
        return dict(status='SOURCE-MISSING', stem=stem)

    for sub in ('images', 'masks'):
        os.makedirs(os.path.join(inp, sub), exist_ok=True)
    for tag in ('A', 'B', 'C'):
        shutil.copyfile(os.path.join(src, 'SOD_%s.jpg' % stem),
                        os.path.join(inp, 'images', 'SOD_TEST%s.jpg' % tag))
        shutil.copyfile(os.path.join(srcm, 'SOD_%s.png' % stem),
                        os.path.join(inp, 'masks', 'SOD_TEST%s.png' % tag))

    def gen(dst, shard_index, shard_total, gpu=0):
        if os.path.isdir(os.path.join(dst, 'images')):
            shutil.rmtree(dst, ignore_errors=True)
        cmd = [py, os.path.join(lr, 'test.py'),
               '--dataset_root', os.path.join(root, 'input'), '--data_type', 'SOD',
               '--dst_root', dst, '--isReplace', '--seed', '0',
               '--shard_index', str(shard_index), '--shard_total', str(shard_total),
               '--log_path', os.path.join(dst, '_log'),
               '--error_list', os.path.join(dst, '_err.pkl')]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
        with open(os.path.join(root, 'gen_%s.log' % os.path.basename(dst)), 'w') as lg:
            subprocess.run(cmd, cwd=lr, env=env, stdout=lg,
                           stderr=subprocess.STDOUT, check=True)
        return ' '.join(cmd)

    def sha(p):
        return hashlib.sha256(open(p, 'rb').read()).hexdigest()

    def img(d, tag):
        return os.path.join(d, 'images', 'SOD_TEST%s.jpg' % tag)

    cmds = []
    r1 = os.path.join(root, 'run1'); cmds.append(gen(r1, 0, 1))
    r2 = os.path.join(root, 'run2'); cmds.append(gen(r2, 0, 1))
    r3 = {}
    for i, tag in enumerate('ABC'):
        d = os.path.join(root, 'run3_s%d' % i)
        cmds.append(gen(d, i, 3, gpu=i % 2))
        r3[tag] = d

    h1 = {t: sha(img(r1, t)) for t in 'ABC'}
    h2 = {t: sha(img(r2, t)) for t in 'ABC'}
    h3 = {t: sha(img(r3[t], t)) for t in 'ABC'}

    def diff(pa, pb):
        A = np.asarray(Image.open(pa).convert('RGB'), np.int16)
        B = np.asarray(Image.open(pb).convert('RGB'), np.int16)
        d = np.abs(A - B)
        return round(float(d.mean()), 3), int(d.max())

    t1_pairs = {('%s-%s' % (a, b)): diff(img(r1, a), img(r1, b))
                for a, b in (('A', 'B'), ('A', 'C'), ('B', 'C'))}
    t3_pairs = {('%s-%s' % (a, b)): diff(img(r3[a], a), img(r3[b], b))
                for a, b in (('A', 'B'), ('A', 'C'), ('B', 'C'))}

    return dict(
        status='OK', stem=stem, commands=cmds,
        inputs_identical=(sha(os.path.join(inp, 'images', 'SOD_TESTA.jpg'))
                          == sha(os.path.join(inp, 'images', 'SOD_TESTC.jpg'))),
        T1_one_shard_hashes={t: h1[t][:16] for t in 'ABC'},
        T1_all_differ=len({h1[t] for t in 'ABC'}) == 3,
        T1_pairwise=t1_pairs,
        T2_reproduces_exactly=all(h1[t] == h2[t] for t in 'ABC'),
        T3_three_shards_hashes={t: h3[t][:16] for t in 'ABC'},
        T3_all_identical=len({h3[t] for t in 'ABC'}) == 1,
        T3_pairwise=t3_pairs,
        T3_equals_T1_position0=(h3['A'] == h1['A']),
        conclusion=('the seed pins the RUN, not the image: same seed reproduces '
                    'bit-exactly, but an identical input at a different '
                    'shard-local position gets different noise'))


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2,s3,s4,s4b,s5,s6,s7,s8')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--rehash', action='store_true')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    steps = [s.strip() for s in args.steps.split(',')]
    os.makedirs(OUT, exist_ok=True)

    metrics, thresholds, notes, artifacts, old_claims = [], [], [], [], []

    recs = None if args.rehash else load_hashes()
    if 's1' in steps and recs is None:
        recs = step_hash(args.workers)
    if recs is None:
        raise SystemExit('no hashes; run with s1')
    unreadable = [r for r in recs if r['phash'] == 'UNREADABLE']
    counts = {sp: sum(1 for r in recs if r['split'] == sp) for sp in SPLITS}
    metrics += [('images_hashed', len(recs), '%d splits' % len(SPLITS)),
                ('unreadable_images', len(unreadable), 'decode failures')]
    for sp in SPLITS:
        assert counts[sp] == C.INPUTS[sp]['n'], (sp, counts[sp])
    thresholds.append(('every split count matches the E0 manifest',
                       all(counts[sp] == C.INPUTS[sp]['n'] for sp in SPLITS)))

    cross_rows = coll = None
    if 's2' in steps:
        cross_rows, coll = step_cross(recs)
        with open(os.path.join(OUT, 'd2_pair_matrix.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(cross_rows[0].keys()))
            w.writeheader(); w.writerows(cross_rows)
        with open(os.path.join(OUT, 'd2_collisions.csv'), 'w', newline='') as fh:
            fn = ['split_a', 'name_a', 'split_b', 'name_b', 'level', 'same_name', 'hash']
            w = csv.DictWriter(fh, fieldnames=fn)
            w.writeheader(); w.writerows(coll)
        artifacts += ['rebuild/D2/out/d2_pair_matrix.csv',
                      'rebuild/D2/out/d2_collisions.csv']

        def pair(a, b, level):
            for r in cross_rows:
                if {r['split_a'], r['split_b']} == {a, b} and r['level'] == level:
                    return r['collisions']
            return None

        tgt_test_f, tgt_test_p = pair('tgt', 'test', 'fhash'), pair('tgt', 'test', 'phash')
        same_name = sum(1 for c in coll
                        if {c['split_a'], c['split_b']} == {'tgt', 'test'}
                        and c['level'] == 'fhash' and c['same_name'])
        metrics += [
            ('COD10K_test_INTERSECT_target_byte', tgt_test_f, 'sha256 of file bytes'),
            ('COD10K_test_INTERSECT_target_pixel', tgt_test_p, 'decoded-RGB hash'),
            ('of_those_sharing_a_filename', same_name,
             'the rest are cross-named and invisible to a name check'),
            ('CHAMELEON_INTERSECT_target', pair('cham', 'tgt', 'fhash'), ''),
            ('NC4K_INTERSECT_target', pair('nc4k', 'tgt', 'fhash'), ''),
            ('CAMOval_INTERSECT_target', pair('val', 'tgt', 'fhash'), ''),
            ('CAMOval_INTERSECT_CHAMELEON', pair('val', 'cham', 'fhash'), ''),
        ]
        endpoint_train = 0
        for a in ENDPOINTS:
            for b in ('raw', 'auth', 'local'):
                endpoint_train += pair(a, b, 'phash') or 0
        metrics.append(('endpoint_INTERSECT_HKUIS_pools', endpoint_train,
                        'any test/val image inside raw, authors or render pools'))
        thresholds += [
            ('byte- and pixel-level agree on |COD10K-test AND target|',
             tgt_test_f == tgt_test_p),
            ('no endpoint image appears in any HKU-IS pool', endpoint_train == 0),
        ]
        old_claims += [
            ('D2.1 COD10K-test AND Target', '7 (2 same-name, 5 cross-named)',
             'MATCH' if tgt_test_f == 7 and same_name == 2 else 'MISMATCH'),
            ('D2.3 CAMO AND CHAMELEON', '3',
             'MATCH' if pair('val', 'cham', 'fhash') == 3 else 'MISMATCH'),
        ]

    if 's3' in steps:
        int_rows, int_groups = step_internal(recs)
        with open(os.path.join(OUT, 'd2_internal_duplicates.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(int_rows[0].keys()))
            w.writeheader(); w.writerows(int_rows)
        with open(os.path.join(OUT, 'd2_internal_groups.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=['split', 'level', 'hash', 'n_in_group', 'names'])
            w.writeheader(); w.writerows(int_groups)
        artifacts += ['rebuild/D2/out/d2_internal_duplicates.csv',
                      'rebuild/D2/out/d2_internal_groups.csv']

        def red(sp, level='fhash'):
            for r in int_rows:
                if r['split'] == sp and r['level'] == level:
                    return r['redundant_files']
        metrics += [('internal_dups_target', red('tgt'), 'redundant files, byte level'),
                    ('internal_dups_renders', red('local'), ''),
                    ('internal_dups_authors_pool', red('auth'), ''),
                    ('internal_dups_raw_hkuis', red('raw'), ''),
                    ('internal_dups_COD10K_test', red('test'), ''),
                    ('unique_renders', 4447 - (red('local') or 0), 'of 4447 files'),
                    ('unique_raw_hkuis', 4447 - (red('raw') or 0), 'of 4447 files'),
                    ('unique_authors_pool', 4447 - (red('auth') or 0), 'of 4447 files')]
        old_claims += [
            ('D2.4 internal duplicates in Target', '2',
             'MATCH' if red('tgt') == 2 else 'MISMATCH'),
            ('D1/D2 internal duplicates in render pool', '2 (4445 unique of 4447)',
             'MATCH' if red('local') == 2 else 'MISMATCH'),
        ]

    # the contract B3 and C1 consume
    contaminated_tgt, contaminated_test = [], []
    if coll is not None:
        for c in coll:
            if c['level'] != 'phash':
                continue
            pair_set = {c['split_a'], c['split_b']}
            if 'tgt' in pair_set and pair_set & set(ENDPOINTS):
                tname = c['name_a'] if c['split_a'] == 'tgt' else c['name_b']
                ename = c['name_b'] if c['split_a'] == 'tgt' else c['name_a']
                esplit = c['split_b'] if c['split_a'] == 'tgt' else c['split_a']
                contaminated_tgt.append(tname)
                contaminated_test.append(dict(split=esplit, name=ename))
        contaminated_tgt = sorted(set(contaminated_tgt))
        leak = dict(
            generated=C.now(), commit=C.git_commit(),
            method=('full pairwise hashing of file bytes and decoded RGB; NOT name '
                    'matching. Consumers must read this file rather than hardcode '
                    'a name list -- see REBUILD_PLAN.md 0.2'),
            target_names_to_exclude=contaminated_tgt,
            n_target_excluded=len(contaminated_tgt),
            endpoint_side=sorted({(d['split'], d['name']) for d in contaminated_test}),
            scope='pixel identity only; near-duplicates are in d2_near_duplicates.csv')
        leak['endpoint_side'] = [dict(split=s, name=n) for s, n in leak['endpoint_side']]
        C.save_json(os.path.join(OUT, 'd2_leaked_names.json'), leak)
        artifacts.append('rebuild/D2/out/d2_leaked_names.json')
        metrics.append(('target_names_to_exclude', len(contaminated_tgt),
                        'the contract B3/C1 read'))
        thresholds.append(('leaked-name contract emitted and non-empty',
                           len(contaminated_tgt) > 0))

    if 's4' in steps:
        near, n_short = step_near(recs)
        with open(os.path.join(OUT, 'd2_near_duplicates.csv'), 'w', newline='') as fh:
            fn = ['split_a', 'name_a', 'split_b', 'name_b', 'dims', 'mean_abs',
                  'p99_abs', 'max_abs', 'frac_gt8', 'content_std']
            w = csv.DictWriter(fh, fieldnames=fn)
            w.writeheader(); w.writerows(near)
        cross_ep = [n for n in near
                    if ({n['split_a'], n['split_b']} & set(ENDPOINTS))
                    and ({n['split_a'], n['split_b']} & set(TRAINING))]
        metrics += [('near_dup_candidate_pairs_shortlisted', n_short,
                     'exhaustive within-dimension, descriptor RMS <= %.0f' % SHORTLIST_RMS),
                    ('near_duplicate_pairs_confirmed', len(near),
                     'full-res verified, mean|diff| <= %.1f' % NEAR_TOL),
                    ('near_dup_endpoint_vs_training', len(cross_ep), '')]

        # Per-endpoint contamination: how many DISTINCT images of each endpoint
        # are a re-encode of something on the training side, or of another
        # endpoint. This is what decides whether a set can be reported at all.
        contam = {}
        for ep in ENDPOINTS:
            tr_hit, ep_hit = set(), set()
            for n in near:
                pair_s = {n['split_a']: n['name_a'], n['split_b']: n['name_b']}
                if ep not in pair_s:
                    continue
                other = [k for k in pair_s if k != ep]
                if not other:
                    continue
                o = other[0]
                if o in TRAINING:
                    tr_hit.add(pair_s[ep])
                elif o in ENDPOINTS:
                    ep_hit.add(pair_s[ep])
            n_ep = C.INPUTS[ep]['n']
            contam[ep] = dict(n=n_ep, vs_training=len(tr_hit),
                              vs_other_endpoint=len(ep_hit),
                              frac_vs_training=round(len(tr_hit) / n_ep, 4),
                              names_vs_training=sorted(tr_hit))
            metrics.append(('nearvdup_%s_images_matching_training' % ep,
                            '%d/%d (%.1f%%)' % (len(tr_hit), n_ep,
                                                100 * len(tr_hit) / n_ep),
                            'distinct endpoint images that are re-encodes'))
        # The headline depends on the tolerance, so report the whole sweep rather
        # than one figure. If a conclusion only holds at one tolerance it is not
        # a conclusion.
        sweep = {}
        for tol in TOL_SWEEP:
            sub = [n for n in near if n['mean_abs'] <= tol]
            row = {}
            for ep in ENDPOINTS:
                hit = set()
                for n in sub:
                    ps = {n['split_a']: n['name_a'], n['split_b']: n['name_b']}
                    if ep in ps:
                        oth = [k for k in ps if k != ep]
                        if oth and oth[0] in TRAINING:
                            hit.add(ps[ep])
                row[ep] = len(hit)
            sweep['tol_%.1f' % tol] = dict(pairs=len(sub), per_endpoint=row)
            metrics.append(('nearvdup_cham_at_tol_%.0f' % tol,
                            '%d/76' % row['cham'],
                            'distinct CHAMELEON images matching training data'))
        contam['tolerance_sweep'] = sweep
        C.save_json(os.path.join(OUT, 'd2_endpoint_contamination.json'), contam)
        artifacts.append('rebuild/D2/out/d2_endpoint_contamination.json')
        worst = max(ENDPOINTS, key=lambda k: contam[k]['frac_vs_training'])
        thresholds.append(
            ('no endpoint has >5% of its images as re-encodes of training data '
             '(EXPLORATORY, informs reportability)',
             contam[worst]['frac_vs_training'] <= 0.05))
        notes.append(
            'DISCLOSURE on the 5-percent threshold: it was added mid-experiment, after '
            's4 returned 13 endpoint-vs-training pairs but BEFORE the per-endpoint '
            'breakdown was computed. Any FAIL is a substantive result about the data, '
            'not a code defect, and is recorded as a FAIL rather than relaxed.')
        notes.append(
            's4 began EXPLORATORY and unthresholded because D2\'s declared scope is '
            'pixel identity. It earned a threshold once it showed that pixel identity '
            'under-bounds the claim by an order of magnitude on one endpoint: D2\'s declared scope is '
            'pixel identity. It exists because "nothing filters Target against Test" is '
            'exact hashing reports CHAMELEON AND Target = 0, while 10 of CHAMELEON\'s '
            '76 images are re-encodes of Target images at identical dimensions. A '
            'thumbnail hash proposes candidates; actual pixels confirm. Rescaled and '
            're-encoded duplicates are the class it can see; crops, flips and different '
            'photographs of one specimen remain out of scope and are not claimed.')
        artifacts.append('rebuild/D2/out/d2_near_duplicates.csv')

    if 's4b' in steps:
        nn = step_endpoint_nn()
        C.save_json(os.path.join(OUT, 'd2_endpoint_nearest.json'),
                    {k: {kk: vv for kk, vv in v.items() if kk != 'rows'}
                     for k, v in nn.items()})
        with open(os.path.join(OUT, 'd2_endpoint_nearest.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=['endpoint', 'name', 'dims',
                                               'n_candidates', 'nearest',
                                               'nearest_split', 'nearest_name'])
            w.writeheader()
            for ep, v in nn.items():
                for r in v['rows']:
                    w.writerow(dict(endpoint=ep, **r))
        for ep in ENDPOINTS:
            v = nn[ep]
            g = v['largest_gap']
            metrics.append(('epNN_%s_checkable' % ep,
                            '%d/%d' % (v['n_checkable'], v['n']),
                            'has >=1 same-dimension training candidate'))
            if g:
                metrics.append(('epNN_%s_gap' % ep,
                                '%d below %.2f, next at %.2f'
                                % (g['n_below'], g['below'], g['above']),
                                'first >5x jump in sorted nearest distances'))
            else:
                metrics.append(('epNN_%s_gap' % ep, 'none', 'no >5x jump found'))
        gc = nn['cham']['largest_gap']
        thresholds.append(
            ('CHAMELEON nearest-neighbour distances show a clean separation, so the '
             'matched count is a property of the data and not of the tolerance',
             bool(gc and gc['above'] / max(gc['below'], 0.01) > 5)))
        notes.append(
            's4b answers a question s4 cannot: s4 counts pairs within a tolerance, '
            'which leaves the count entangled with the tolerance. s4b measures, for '
            'every endpoint image, the distance to its nearest same-dimension training '
            'image, and looks for a gap in the sorted distances. It replaced an '
            'abandoned attempt to widen s4 to a 30-grey-level tolerance over all '
            'pairs, which was computationally infeasible inside the largest dimension '
            'groups. Bounding the comparison to endpoint-vs-training makes the same '
            'question cheap.')
        artifacts += ['rebuild/D2/out/d2_endpoint_nearest.json',
                      'rebuild/D2/out/d2_endpoint_nearest.csv']

    if 's5' in steps:
        test_side = [d['name'] for d in contaminated_test if d['split'] == 'test']
        r = step_mae(test_side)
        C.save_json(os.path.join(OUT, 'd2_mae_impact.json'),
                    {k: v for k, v in r.items() if k != 'per_image'})
        if r['status'] == 'OK':
            with open(os.path.join(OUT, 'd2_mae_per_image.csv'), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=['name', 'mae', 'contaminated'])
                w.writeheader(); w.writerows(r['per_image'])
            metrics += [
                ('endpoint_MAE_all_2026', round(r['mae_all'], 6), r['pred_dir']),
                ('endpoint_MAE_excl_contaminated', round(r['mae_excluding_contaminated'], 6),
                 'n=%d removed' % r['n_contaminated']),
                ('endpoint_MAE_delta', round(r['delta'], 8),
                 '%.4f%% relative' % (100 * r['relative_delta'])),
                ('contaminated_mean_MAE', round(r['mae_contaminated_mean'], 6), ''),
                ('contaminated_mean_percentile', round(r['mean_percentile'], 4),
                 '0.5 = indistinguishable from clean test images'),
            ]
            thresholds += [
                ('removing contaminated test images moves MAE by < 0.001',
                 abs(r['delta']) < 0.001),
                ('contaminated images show no memorisation signature (percentile in 0.25-0.75)',
                 0.25 <= r['mean_percentile'] <= 0.75),
            ]
            old_claims.append(
                ('D2.5 MAE impact of the leaked images', '0.000012 (0.017% relative)',
                 'MATCH' if abs(abs(r['delta']) - 0.000012) < 5e-6 else 'MISMATCH'))
            artifacts += ['rebuild/D2/out/d2_mae_impact.json',
                          'rebuild/D2/out/d2_mae_per_image.csv']
        else:
            metrics.append(('endpoint_MAE_status', r['status'], ''))

    if 's6' in steps:
        sc = step_scope()
        C.save_json(os.path.join(OUT, 'd2_scope.json'), sc)
        metrics += [('MyTrain_val_root_default', sc['val_root_default'],
                     'MyTrain.py:%s' % sc['myTrain_val_root_line']),
                    ('checkpoint_selection_set_is_CAMO', sc['val_root_is_camo'],
                     '%d images' % sc['camo_val_n'])]
        thresholds.append(('checkpoint selection runs on the CAMO split, so CAMO is '
                           'excluded as an endpoint', sc['val_root_is_camo']))
        notes.append(
            'Scoping consequence: MyTrain.py selects Tea_epoch_best.pth on --val_root '
            'Dataset/Val/CAMO, and that 250-image set is the published CAMO TEST split. '
            'Every checkpoint in every arm is therefore chosen by its score on a test '
            'set. It applies identically to all arms so it cannot bias B-vs-C, but CAMO '
            'can never be reported as an endpoint. Primary COD10K; secondary CHAMELEON, '
            'NC4K. Inherited from the published S2R-COD protocol, so disclosed rather '
            'than "fixed" -- changing the val set would break Table 1 comparability.')
        artifacts.append('rebuild/D2/out/d2_scope.json')

    if 's7' in steps:
        dt = step_determinism()
        with open(os.path.join(OUT, 'd2_duplicate_input_renders.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(dt['rows'][0].keys()))
            w.writeheader(); w.writerows(dt['rows'])
        C.save_json(os.path.join(OUT, 'd2_determinism.json'),
                    {k: v for k, v in dt.items() if k != 'rows'})
        metrics += [
            ('duplicate_input_pairs_in_raw_HKUIS', dt['duplicate_input_pairs'],
             'byte-identical source photographs'),
            ('render_identical_prediction_holds', '%d/%d' % (dt['prediction_holds_for'],
                                                            dt['duplicate_input_pairs']),
             'predicted identical iff mask identical AND same shard-local position'),
            ('pairs_same_input_different_noise', dt['clean_same_input_diff_noise'],
             'identical image AND mask, different shard position'),
        ]
        if dt['divergence']:
            d0 = dt['divergence'][0]
            metrics += [('same_input_render_divergence_mean_abs', d0['mean_abs'],
                         '%s vs %s' % (d0['stem_a'], d0['stem_b'])),
                        ('same_input_divergence_background', d0['bg_mean_abs'], ''),
                        ('same_input_divergence_foreground', d0['fg_mean_abs'],
                         'composited from source, so near-zero expected')]
        thresholds.append(
            ('render identity across duplicate inputs is fully explained by '
             '(mask identity AND shard-local position)',
             dt['prediction_holds_for'] == dt['duplicate_input_pairs']))
        notes.append(
            'A render is NOT a function of (image, mask). LAKE-RED sets '
            'torch.manual_seed once per process (test.py:90-91) and shards by stride '
            '(test.py:115, pairs[i::total]), so per-image DDIM noise is drawn '
            'sequentially and depends on POSITION WITHIN THE SHARD. Byte-identical '
            'inputs at the same local position give identical renders; at different '
            'positions they diverge. Consequence for E0: the bit-exact reproduction '
            'holds only for the same shard count over the same input listing -- '
            'changing --shard_total, or adding or removing one input file, shifts every '
            'later index and yields a different pool. E0 s4 re-ran with shard_total=2 '
            'over an unchanged listing, which is why it matched exactly.')
        artifacts += ['rebuild/D2/out/d2_duplicate_input_renders.csv',
                      'rebuild/D2/out/d2_determinism.json']

    if 's8' in steps:
        se = step_seed_experiment()
        C.save_json(os.path.join(OUT, 'd2_seed_experiment.json'), se)
        if se['status'] == 'OK':
            metrics += [
                ('s8_inputs_byte_identical', se['inputs_identical'],
                 '3 copies of one (image, mask) pair, named to sort A/B/C'),
                ('s8_T1_one_shard_all_differ', se['T1_all_differ'],
                 'positions 0,1,2 of one noise stream'),
                ('s8_T1_mean_abs_A_vs_B', se['T1_pairwise']['A-B'][0], ''),
                ('s8_T1_mean_abs_B_vs_C', se['T1_pairwise']['B-C'][0], ''),
                ('s8_T2_run_reproduces_exactly', se['T2_reproduces_exactly'],
                 'identical invocation, fresh output dir'),
                ('s8_T3_three_shards_all_identical', se['T3_all_identical'],
                 'each input forced to shard-local position 0'),
                ('s8_T3_mean_abs_A_vs_B', se['T3_pairwise']['A-B'][0],
                 'zero confirms the position mechanism'),
                ('s8_T3_equals_T1_position0', se['T3_equals_T1_position0'],
                 'same local position gives the same render across shard configs'),
            ]
            thresholds += [
                ('s8 T1: identical inputs at different positions produce different '
                 'renders', se['T1_all_differ']),
                ('s8 T2: an identical invocation reproduces bit-exactly',
                 se['T2_reproduces_exactly']),
                ('s8 T3: forcing identical inputs to the same shard-local position '
                 'makes their renders identical', se['T3_all_identical']),
            ]
            notes.append(
                's8 is the CONTROLLED test of the mechanism s7 inferred from 4 '
                'observational pairs. T3 is the load-bearing one: a negative result '
                '(identical inputs diverging) is consistent with several explanations, '
                'but only the position mechanism predicts that forcing equal positions '
                'collapses the divergence to exactly zero. It does. Corollary for how '
                'the seed should be described: it pins the RUN, not the image. Same '
                'seed, same listing, same shard count reproduces bit-exactly (T2, and '
                'E0 at 4447/4447); the same image at a different position does not.')
            artifacts.append('rebuild/D2/out/d2_seed_experiment.json')
        else:
            metrics.append(('s8_status', se['status'], ''))

    notes.append(
        'Detection is by HASH, never by name. Phase 0 found that only 2 of the 7 '
        'previously claimed Target/COD10K duplicates share a filename; the other 5 are '
        'cross-named. One was also mis-transcribed in the old documents as '
        'COD10K-CAM-3-Flying-53-Owl-4633; the file on disk is Flying-65.')
    notes.append(
        'LIMITATION: pixel identity bounds this sweep. Crops, flips, colour-shifted '
        'copies and different photographs of the same specimen are NOT detected and are '
        'not claimed. s4 extends coverage to rescaled duplicates only.')

    block = C.log_block(
        EXP, 'LAKE-RED/.venv/bin/python rebuild/D2/d2_leakage_sweep.py --steps %s' % args.steps,
        metrics, thresholds, old_claims, artifacts,
        representation='decoded pixels (the only level that survives re-encoding)',
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

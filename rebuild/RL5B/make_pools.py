#!/usr/bin/env python
"""RL5B rebuttal -- build the source pools for runs outside the ABC namespace. Builds by hardlink
(no bytes copied); verifies before it writes a manifest; never touches an existing pool.

  bridge    Dataset/Source/RL5B/bridge/SINet_C10_s42 : a fresh copy of the committed pool of
            SINet_C10_s42. Its Image/ and GT/ digests must equal the committed ones in
            rebuild/ABC/out/abc_pools.json.
  real4040  Dataset/Source/RL5B/REAL4040 : the 4040 target images (COD10K-train 3040 + CAMO-train
            1000) with their REAL masks, from the benchmark training archive
            Dataset/_download_ws4/TrainValDataset.zip (extracted to .../extract/COD-TrainDataset).
            Every image must be byte-identical to Dataset/Target/Image; every image must have a mask.
  risepl    Dataset/Source/RL5B/RISEPL : the 4040 target images with RISE's released pseudo masks
            (Dataset/External/RISE/...); every target stem must have a pseudo mask.

Usage: .venv/bin/python rebuild/RL5B/make_pools.py {bridge,real4040,risepl} [--pseudo-dir DIR]
"""
import argparse
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_REPO, 'rebuild'))
import common as C                                            # noqa: E402

OUT = os.path.join(_REPO, 'rebuild', 'RL5B', 'out')


def sha(p):
    return C.sha256(p)


def link_tree(pairs, dst_img, dst_gt):
    os.makedirs(dst_img)
    os.makedirs(dst_gt)
    for (si, sg), (di, dg) in pairs:
        os.link(si, os.path.join(dst_img, di))
        os.link(sg, os.path.join(dst_gt, dg))


def bridge():
    rid = 'SINet_C10_s42'
    src = os.path.join(_REPO, 'Dataset', 'Source', 'ABC', rid)
    dst = os.path.join(_REPO, 'Dataset', 'Source', 'RL5B', 'bridge', rid)
    if os.path.exists(dst):
        raise SystemExit('exists, not touched: %s' % dst)
    pools = json.load(open(os.path.join(_REPO, 'rebuild', 'ABC', 'out', 'abc_pools.json')))['pools']
    ref = pools[rid]
    names = sorted(os.listdir(os.path.join(src, 'Image')))
    gts = sorted(os.listdir(os.path.join(src, 'GT')))
    pairs = [((os.path.join(src, 'Image', a), os.path.join(src, 'GT', b)), (a, b)) for a, b in zip(names, gts)]
    link_tree(pairs, os.path.join(dst, 'Image'), os.path.join(dst, 'GT'))
    ni, hi, _ = C.dir_digest(os.path.join(dst, 'Image'))
    ng, hg, _ = C.dir_digest(os.path.join(dst, 'GT'))
    ok = (hi == ref['image_digest'] and hg == ref['gt_digest'] and ni == ref['n_image'])
    man = dict(generated=C.now(), commit=C.git_commit(), pool=os.path.relpath(dst, _REPO), source=os.path.relpath(src, _REPO),
               n_image=ni, n_gt=ng, image_digest=hi, gt_digest=hg, committed_image_digest=ref['image_digest'],
               committed_gt_digest=ref['gt_digest'], digests_match_committed=ok)
    C.save_json(os.path.join(OUT, 'pool_bridge_%s.json' % rid), man)
    print(json.dumps(man, indent=1))
    if not ok:
        raise SystemExit('BRIDGE POOL MISMATCH -- do not train')


def real4040():
    ext = os.path.join(_REPO, 'Dataset', '_download_ws4', 'extract', 'COD-TrainDataset')
    zipf = os.path.join(_REPO, 'Dataset', '_download_ws4', 'TrainValDataset.zip')
    tgt = os.path.join(_REPO, 'Dataset', 'Target', 'Image')
    dst = os.path.join(_REPO, 'Dataset', 'Source', 'RL5B', 'REAL4040')
    if os.path.exists(dst):
        raise SystemExit('exists, not touched: %s' % dst)
    timgs = sorted(os.listdir(tgt))
    stems = [os.path.splitext(t)[0] for t in timgs]
    eimg = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(ext, 'Imgs'))}
    egt = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(ext, 'GT'))}
    missing_img = [s for s in stems if s not in eimg]
    missing_gt = [s for s in stems if s not in egt]
    bad = [s for s in stems if s in eimg and sha(os.path.join(ext, 'Imgs', eimg[s])) != sha(os.path.join(tgt, s + os.path.splitext(eimg[s])[1]))]
    extra = sorted(set(eimg) - set(stems))
    ok = not (missing_img or missing_gt or bad) and len(stems) == 4040
    man = dict(generated=C.now(), commit=C.git_commit(), pool=os.path.relpath(dst, _REPO),
               source_archive=os.path.relpath(zipf, _REPO), source_archive_sha256=sha(zipf) if os.path.isfile(zipf) else None,
               n_target=len(stems), n_cod10k=sum(s.startswith('COD10K') for s in stems),
               n_camo=sum(not s.startswith('COD10K') for s in stems), missing_images=missing_img[:20],
               missing_masks=missing_gt[:20], images_not_byte_identical_to_target=bad[:20],
               archive_extra_images=len(extra), verified=ok)
    if not ok:
        C.save_json(os.path.join(OUT, 'pool_real4040.json'), man)
        raise SystemExit('REAL4040 verification failed -- see pool_real4040.json')
    pairs = [((os.path.join(ext, 'Imgs', eimg[s]), os.path.join(ext, 'GT', egt[s])), (eimg[s], egt[s])) for s in stems]
    link_tree(pairs, os.path.join(dst, 'Image'), os.path.join(dst, 'GT'))
    ni, hi, _ = C.dir_digest(os.path.join(dst, 'Image'))
    ng, hg, _ = C.dir_digest(os.path.join(dst, 'GT'))
    man.update(n_image=ni, n_gt=ng, image_digest=hi, gt_digest=hg)
    C.save_json(os.path.join(OUT, 'pool_real4040.json'), man)
    print(json.dumps(man, indent=1))


def risepl(pseudo_dir):
    tgt = os.path.join(_REPO, 'Dataset', 'Target', 'Image')
    dst = os.path.join(_REPO, 'Dataset', 'Source', 'RL5B', 'RISEPL')
    if os.path.exists(dst):
        raise SystemExit('exists, not touched: %s' % dst)
    timgs = sorted(os.listdir(tgt))
    pm = {os.path.splitext(f)[0]: f for f in os.listdir(pseudo_dir)}
    stems = [os.path.splitext(t)[0] for t in timgs]
    missing = [s for s in stems if s not in pm]
    man = dict(generated=C.now(), commit=C.git_commit(), pool=os.path.relpath(dst, _REPO),
               pseudo_dir=os.path.relpath(pseudo_dir, _REPO), n_target=len(stems), n_pseudo=len(pm),
               missing_pseudo=len(missing), missing_examples=missing[:20], verified=not missing)
    if missing:
        C.save_json(os.path.join(OUT, 'pool_risepl.json'), man)
        raise SystemExit('RISE pseudo masks do not cover the 4040 target stems (%d missing)' % len(missing))
    pairs = [((os.path.join(tgt, t), os.path.join(pseudo_dir, pm[os.path.splitext(t)[0]])),
              (t, os.path.splitext(t)[0] + os.path.splitext(pm[os.path.splitext(t)[0]])[1])) for t in timgs]
    link_tree(pairs, os.path.join(dst, 'Image'), os.path.join(dst, 'GT'))
    ni, hi, _ = C.dir_digest(os.path.join(dst, 'Image'))
    ng, hg, _ = C.dir_digest(os.path.join(dst, 'GT'))
    man.update(n_image=ni, n_gt=ng, image_digest=hi, gt_digest=hg)
    C.save_json(os.path.join(OUT, 'pool_risepl.json'), man)
    print(json.dumps(man, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('which', choices=['bridge', 'real4040', 'risepl'])
    ap.add_argument('--pseudo-dir', default='')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    {'bridge': bridge, 'real4040': real4040}.get(a.which, lambda: risepl(a.pseudo_dir))()

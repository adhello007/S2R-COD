#!/usr/bin/env python
"""CAUS EXP-01 -- build one arm pool from leaf symlinks and gate it (ABC_PLAN A.8.1 #1-#6, plus bytes).

A pool is <run_dir>/pool/{Image,GT}: the authors' 4447 base pairs plus the arm's 1000 LAKE-RED
renders (SOD_<stem>.jpg) and render masks (SOD_<stem>.png), each a SYMLINK to the original
file. File NAMES are exactly those of the committed ABC pools (which were hard links), so the
trainer's sorted listing -- and therefore data order -- is identical. The trainer's CLS step
copies the pool with shutil.copytree (symlinks dereferenced) into <run_dir>/pool_iteration2/,
so nothing is ever written through a link.

Gate (all must hold; any failure HALTS the run before training):
  a1 counts         Image and GT both hold exactly 5447 entries
  a2 stem sets      identical stem sets in Image and GT; no duplicate stems; no .tif
  a4 parity         REAL SrcDataset: stem(images[i]) == stem(gts[i]) for EVERY i
  a5 spot check     4 pairs: same size, mask neither empty nor full
  a6 round-2        parity on the worst-case union of the pool with all 4040 target names (.png)
  bytes             every base file and every selected render/mask re-hashed against E0's manifest
  mask == raw GT    every selected render mask pixel-identical to the raw GT of its foreground
  stems frozen      the arm's stems equal the committed STUDENT_RESULTS/.../EXP-01_stems/<ARM>.txt
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402
import exp01_alloc as X                                        # noqa: E402

BASE_IMG = 'Dataset/Source/HKU-IS/Image'
BASE_GT = 'Dataset/Source/HKU-IS/GT'
N_BASE = 4447


def frozen_stems(arm, seed):
    if arm == 'B':
        return X.committed_stems('B_s%d' % seed)
    p = os.path.join(K.TABLES, 'EXP-01_stems', '%s.txt' % arm)
    return X.read_stem_file(p)


def build(run_dir, arm, seed):
    pool = K.assert_writable(os.path.join(run_dir, 'pool'))
    if os.path.exists(pool):
        raise SystemExit('EXP01 POOL HALT: %s already exists (a run folder is never reused)' % pool)
    stems = X.stems(arm, seed if arm == 'B' else None)
    for sub in ('Image', 'GT'):
        os.makedirs(os.path.join(pool, sub))
    for sub, d in (('Image', BASE_IMG), ('GT', BASE_GT)):
        src = os.path.realpath(os.path.join(K.REPO, d))
        for nm in sorted(os.listdir(src)):
            os.symlink(os.path.join(src, nm), os.path.join(pool, sub, nm))
    ri = os.path.realpath(os.path.join(K.REPO, X.A.REN_IMG))
    rm = os.path.realpath(os.path.join(K.REPO, X.A.REN_MSK))
    for st in stems:
        os.symlink(os.path.join(ri, 'SOD_%s.jpg' % st), os.path.join(pool, 'Image', 'SOD_%s.jpg' % st))
        os.symlink(os.path.join(rm, 'SOD_%s.png' % st), os.path.join(pool, 'GT', 'SOD_%s.png' % st))
    return pool, stems


def gate(pool, arm, seed, stems):
    sys.path.insert(0, K.REPO)
    import numpy as np
    from PIL import Image
    from Src.utils.Dataloader import SrcDataset
    stem = lambda f: os.path.splitext(f)[0]                      # noqa: E731
    img = sorted(os.listdir(os.path.join(pool, 'Image')))
    gt = sorted(os.listdir(os.path.join(pool, 'GT')))
    expect = N_BASE + X.BUDGET
    r = dict(pool=os.path.relpath(pool, K.REPO), arm=arm, seed=seed, n_image=len(img), n_gt=len(gt))
    r['a1_counts'] = len(img) == len(gt) == expect
    r['a2_stem_sets'] = ({stem(f) for f in img} == {stem(f) for f in gt}
                         and len({stem(f) for f in img}) == len(img) and not any(f.endswith('.tif') for f in gt))
    ds = SrcDataset(os.path.join(pool, 'Image') + '/', os.path.join(pool, 'GT') + '/', 352)
    mism = sum(1 for i in range(len(ds))
               if stem(os.path.basename(ds.images[i])) != stem(os.path.basename(ds.gts[i])))
    r['a4_parity_all_i'] = (mism == 0 and len(ds) == expect)
    r['a4_mismatches'] = mism
    spot = True
    for i in [len(ds) // 2] + random.Random(seed).sample(range(len(ds)), 3):
        a = Image.open(ds.images[i])
        b = np.array(Image.open(ds.gts[i]).convert('L'))
        wf = float((b > 127).mean())
        spot &= bool(a.size == (b.shape[1], b.shape[0]) and 0.0 < wf < 1.0)
    r['a5_spotcheck'] = spot
    tgt = sorted(os.listdir(os.path.join(K.REPO, 'Dataset/Target/Image')))
    app = [stem(f) + '.png' for f in tgt]
    si, sg = sorted(img + app), sorted(gt + app)
    r['a6_round2_parity'] = len(si) == len(sg) and all(stem(si[i]) == stem(sg[i]) for i in range(len(si)))
    # bytes against E0's manifest
    man = {}
    for line in open(os.path.join(K.REPO, 'rebuild/E0/out/e0_manifest.sha256')):
        if not line.startswith('#'):
            d, k = line.split()
            man[k] = d
    bad = 0
    for sub, key, rkey in (('Image', 'auth', 'local'), ('GT', 'auth_gt', 'local_msk')):
        for nm in sorted(os.listdir(os.path.join(pool, sub))):
            k = ('%s/%s' % (rkey, nm)) if nm.startswith('SOD_') else ('%s/%s' % (key, nm))
            if man.get(k) != K.sha256(os.path.join(pool, sub, nm)):
                bad += 1
    r['bytes_mismatched_vs_E0'] = bad
    # render mask == raw GT, every selected stem
    nb = 0
    for st in stems:
        a = np.array(Image.open(os.path.join(K.REPO, X.A.RAW_GT, st + '.png')).convert('L'))
        b = np.array(Image.open(os.path.join(pool, 'GT', 'SOD_%s.png' % st)).convert('L'))
        if a.shape != b.shape or int(np.abs(a.astype(int) - b.astype(int)).max()) != 0:
            nb += 1
    r['render_mask_ne_raw_gt'] = nb
    r['stems_equal_frozen'] = sorted(stems) == sorted(frozen_stems(arm, seed))
    r['stems_sha256'] = K.list_digest(stems)
    r['image_list_sha256'] = K.list_digest(img)
    r['passed'] = bool(r['a1_counts'] and r['a2_stem_sets'] and r['a4_parity_all_i'] and r['a5_spotcheck']
                       and r['a6_round2_parity'] and bad == 0 and nb == 0 and r['stems_equal_frozen'])
    return r


def trainer_gates():
    """The committed read-only gates G3 (one trainer + patches), G4 (endpoints), G6 (determinism).
    G2 (provenance) is NOT called here: E0.step_independence() rewrites a committed JSON. Its data
    half is covered by the byte checks above and by exp01_reuse_gate.py (every input file)."""
    sys.path.insert(0, os.path.join(K.REBUILD, 'ABC'))
    import abc_preflight as PFA
    out = {}
    for g in (PFA.gate_one_trainer, PFA.gate_endpoints, PFA.gate_determinism):
        d = g()
        out[d['gate']] = dict(passed=bool(d['passed']), **{k: v for k, v in d.items()
                                                           if k not in ('gate', 'passed', 'note')})
    out['passed'] = all(v['passed'] for v in out.values() if isinstance(v, dict))
    return out

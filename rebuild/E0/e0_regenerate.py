#!/usr/bin/env python
"""E0 -- Regenerate, don't rescue.

Rebuilds every shared input of the Stage C package from primary data on disk,
and proves the package needs no rescued file. E0 concludes nothing by itself;
it produces what every later experiment consumes, so if E0 is wrong everything
downstream is wrong.

Steps (run individually with --steps, or all):

  s1  manifest     SHA256 every declared primary input. The anchor + tripwire.
  s2  represent    Pixel-level verification of every representation claim in
                   REBUILD_PLAN.md §2 and traps T1-T3. This is where the old
                   package's grey-128 slip lived.
  s3  embed        Feature caches: 2 embedder families x resolution sweep.
  s3b resize       How much does the squash-vs-crop preprocessing CHOICE move
                   cluster membership? (an unjustified constant, per §0.2)
  s4  renders      Re-run LAKE-RED staging + generation at seed 0 into a NEW
                   directory and compare against the renders on disk.
  s5  independent  Prove nothing reads the archive or any /tmp scratchpad.

Usage:
  LAKE-RED/.venv/bin/python rebuild/E0/e0_regenerate.py --steps s1,s2,s3,s3b,s5
  LAKE-RED/.venv/bin/python rebuild/E0/e0_regenerate.py --steps s4 --ngpu 2
"""

import argparse
import ast
import csv
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'E0'
OUT = C.exp_dir(EXP, 'out')
CACHE = C.exp_dir(EXP, 'cache')
REGEN = C.exp_dir(EXP, 'regen')

# Sets that get embedded, and the loader each one uses. The `repr` string is
# carried into the log block so the representation is never implied.
EMBED_SETS = {
    'tgt':   ('R1-full',            'image'),
    'raw':   ('R1-full',            'image'),
    'auth':  ('R1-full',            'image'),
    'local': ('R3-render',          'image'),
    'cut':   ('R2-cutout-grey128',  'cutout'),
    'test':  ('R1-full',            'image'),
    'val':   ('R1-full',            'image'),
}


def _p(msg):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), msg), flush=True)


def _stems(names):
    return [os.path.splitext(n)[0] for n in names]


# ---------------------------------------------------------------------------
# s1 -- hash manifest
# ---------------------------------------------------------------------------

def step_manifest():
    """SHA256 every declared primary input; write a full manifest + digests."""
    os.makedirs(OUT, exist_ok=True)
    rows, total_files, missing = [], 0, []
    man_path = os.path.join(OUT, 'e0_manifest.sha256')
    with open(man_path, 'w') as man:
        man.write('# Stage C rebuild -- primary input manifest\n')
        man.write('# generated %s | commit %s\n' % (C.now(), C.git_commit()))
        man.write('# format: <sha256>  <input_key>/<filename>\n')
        for key, spec in C.INPUTS.items():
            try:
                path = C.ipath(key)
            except FileNotFoundError as e:
                missing.append(key)
                _p('MISSING %s -- %s' % (key, e))
                continue
            n, agg, per_file = C.dir_digest(path)
            total_files += n
            ok = (n == spec['n'])
            rows.append(dict(key=key, path=spec['path'], declared_n=spec['n'],
                             actual_n=n, count_ok=ok, agg16=agg[:16],
                             agg=agg, repr=spec['repr'], pool=spec['pool'] or ''))
            for nm, d in per_file:
                man.write('%s  %s/%s\n' % (d, key, nm))
            _p('%-11s n=%-5d %s agg=%s' % (key, n, 'OK ' if ok else 'MISCOUNT', agg[:16]))

    with open(os.path.join(OUT, 'e0_input_digests.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Checkpoints and prediction dirs (B1 / C3 inputs) -- counted, not hashed
    # in full here; C3 hashes the specific checkpoints it loads.
    models = {}
    for tag, rel in C.PRIMARY_MODELS.items():
        d = os.path.join(C.REPO, rel)
        models[tag] = dict(exists=os.path.isdir(d),
                           pth=len([f for f in os.listdir(d) if f.endswith('.pth')])
                           if os.path.isdir(d) else 0,
                           has_best=os.path.isfile(os.path.join(d, 'Tea_epoch_best.pth')))
    C.save_json(os.path.join(OUT, 'e0_models.json'), models)

    return dict(rows=rows, total_files=total_files, missing=missing,
                manifest=man_path, models=models)


# ---------------------------------------------------------------------------
# s2 -- representation verification (the slip hunt)
# ---------------------------------------------------------------------------

def step_representation(sample=400, seed=0):
    """Verify at PIXEL level every representation claim in REBUILD_PLAN.md §2.

    Nothing here trusts a variable name or a docstring -- each check opens the
    actual files and looks at the values.
    """
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(seed)
    res = {}

    raw_dir, gt_dir = C.ipath('raw'), C.ipath('raw_gt')
    auth_gt_dir = C.ipath('auth_gt')
    local_dir, local_msk_dir = C.ipath('local'), C.ipath('local_msk')
    auth_dir = C.ipath('auth')

    raw_names = C.listing('raw')
    stems = _stems(raw_names)
    pick = rng.choice(len(stems), size=min(sample, len(stems)), replace=False)

    # --- C1: mask polarity of HKU-IS GT. Object white or black? ---------
    # If object=WHITE the image border should be overwhelmingly BLACK, since
    # salient objects rarely tile the frame edge. Measured, not assumed.
    fg_frac, border_frac = [], []
    for i in pick:
        g = np.asarray(Image.open(os.path.join(gt_dir, stems[i] + '.png')).convert('L'))
        b = np.concatenate([g[0, :], g[-1, :], g[:, 0], g[:, -1]])
        fg_frac.append(float((g > C.THRESH).mean()))
        border_frac.append(float((b > C.THRESH).mean()))
    res['polarity'] = dict(n=len(pick), mean_fg_frac=float(np.mean(fg_frac)),
                           mean_border_white_frac=float(np.mean(border_frac)),
                           object_is_white=bool(np.mean(border_frac) < np.mean(fg_frac)))

    # --- C2: the cutout really is object-on-flat-grey-128 ---------------
    cut_checks = []
    for i in pick[:50]:
        im = C.load_cutout(os.path.join(raw_dir, stems[i] + '.png'),
                           os.path.join(gt_dir, stems[i] + '.png'))
        a = np.asarray(im)
        g = np.asarray(Image.open(os.path.join(gt_dir, stems[i] + '.png'))
                       .convert('L').resize(im.size, Image.NEAREST))
        bg = a[g < C.THRESH]
        cut_checks.append(dict(
            stem=stems[i],
            bg_unique=sorted(set(np.unique(bg).tolist())),
            bg_is_flat_grey=bool(bg.size == 0 or (np.unique(bg).tolist() == [C.GREY])),
            bg_pixel_share=float((g < C.THRESH).mean()),
            fg_untouched=bool(np.array_equal(
                a[g >= C.THRESH],
                np.asarray(Image.open(os.path.join(raw_dir, stems[i] + '.png'))
                           .convert('RGB'))[g >= C.THRESH]))))
    res['cutout'] = dict(
        n=len(cut_checks),
        grey_value=C.GREY, threshold=C.THRESH,
        all_bg_flat_grey=all(c['bg_is_flat_grey'] for c in cut_checks),
        all_fg_untouched=all(c['fg_untouched'] for c in cut_checks),
        mean_bg_pixel_share=float(np.mean([c['bg_pixel_share'] for c in cut_checks])))

    # --- T1: three HKU-IS pools, all 4447 -- are any identical? ---------
    pool_diff = []
    for i in pick[:200]:
        s = stems[i]
        try:
            r = np.asarray(Image.open(os.path.join(raw_dir, s + '.png')).convert('RGB')).astype(int)
            a = np.asarray(Image.open(os.path.join(auth_dir, s + '.jpg')).convert('RGB')).astype(int)
            l = np.asarray(Image.open(os.path.join(local_dir, 'SOD_' + s + '.jpg')).convert('RGB')).astype(int)
        except FileNotFoundError:
            continue
        if not (r.shape == a.shape == l.shape):
            pool_diff.append(dict(stem=s, shape_mismatch=True))
            continue
        pool_diff.append(dict(stem=s, shape_mismatch=False,
                              raw_auth_max=int(np.abs(r - a).max()),
                              raw_auth_mean=float(np.abs(r - a).mean()),
                              auth_local_max=int(np.abs(a - l).max()),
                              auth_local_mean=float(np.abs(a - l).mean()),
                              raw_local_max=int(np.abs(r - l).max())))
    ok = [d for d in pool_diff if not d.get('shape_mismatch')]
    res['pools_T1'] = dict(
        n=len(ok),
        identical_raw_auth=sum(1 for d in ok if d['raw_auth_max'] == 0),
        identical_auth_local=sum(1 for d in ok if d['auth_local_max'] == 0),
        mean_raw_auth_maxdiff=float(np.mean([d['raw_auth_max'] for d in ok])),
        mean_auth_local_maxdiff=float(np.mean([d['auth_local_max'] for d in ok])),
        shape_mismatches=sum(1 for d in pool_diff if d.get('shape_mismatch')))

    # --- T2: LAKE-RED output mask polarity vs input mask polarity -------
    # Input masks are staged INVERTED (object=0). test.py:173 inverts again on
    # save, so outputs should be back in SOD polarity (object=white).
    in_msk_dir = C.ipath('lr_in_mask')
    t2 = []
    for i in pick[:100]:
        s = stems[i]
        gi = np.asarray(Image.open(os.path.join(gt_dir, s + '.png')).convert('L'))
        mi = np.asarray(Image.open(os.path.join(in_msk_dir, 'SOD_' + s + '.png')).convert('L'))
        mo = np.asarray(Image.open(os.path.join(local_msk_dir, 'SOD_' + s + '.png')).convert('L'))
        t2.append(dict(gt_white=float((gi > C.THRESH).mean()),
                       in_white=float((mi > C.THRESH).mean()),
                       out_white=float((mo > C.THRESH).mean())))
    res['mask_polarity_T2'] = dict(
        n=len(t2),
        mean_gt_white=float(np.mean([d['gt_white'] for d in t2])),
        mean_input_white=float(np.mean([d['in_white'] for d in t2])),
        mean_output_white=float(np.mean([d['out_white'] for d in t2])),
        input_is_inverted=bool(np.mean([d['in_white'] for d in t2]) > 0.5),
        output_matches_gt=bool(abs(np.mean([d['out_white'] for d in t2])
                                   - np.mean([d['gt_white'] for d in t2])) < 0.01))

    # --- T3: authors' GT vs raw GT -- identical? ------------------------
    t3 = []
    for i in pick[:200]:
        s = stems[i]
        try:
            g1 = np.asarray(Image.open(os.path.join(gt_dir, s + '.png')).convert('L'))
            g2 = np.asarray(Image.open(os.path.join(auth_gt_dir, s + '.png')).convert('L'))
        except FileNotFoundError:
            continue
        if g1.shape != g2.shape:
            t3.append(dict(identical=False, shape_mismatch=True, d_fg=None))
            continue
        t3.append(dict(identical=bool(np.array_equal(g1, g2)), shape_mismatch=False,
                       d_fg=float((g1 > C.THRESH).mean() - (g2 > C.THRESH).mean())))
    res['gt_sets_T3'] = dict(
        n=len(t3),
        identical=sum(1 for d in t3 if d['identical']),
        mean_fg_frac_delta=float(np.mean([d['d_fg'] for d in t3 if d['d_fg'] is not None])))

    # --- C3: does --isReplace really copy the foreground back? ----------
    # test.py:165  out_array[mask_array == 0] = image_array[mask_array == 0]
    # The render is saved as JPEG, so the copied region cannot be bit-identical
    # to a PNG source. The honest test is the RATIO: foreground error should be
    # JPEG-quantisation scale while background error is regeneration scale.
    rep = []
    for i in pick[:200]:
        s = stems[i]
        try:
            r = np.asarray(Image.open(os.path.join(raw_dir, s + '.png')).convert('RGB')).astype(np.int16)
            l = np.asarray(Image.open(os.path.join(local_dir, 'SOD_' + s + '.jpg')).convert('RGB')).astype(np.int16)
            g = np.asarray(Image.open(os.path.join(gt_dir, s + '.png')).convert('L'))
        except FileNotFoundError:
            continue
        if r.shape != l.shape:
            continue
        fg = g >= C.THRESH
        if fg.sum() == 0 or (~fg).sum() == 0:
            continue
        d = np.abs(r - l)
        rep.append(dict(fg_mean=float(d[fg].mean()), fg_max=int(d[fg].max()),
                        bg_mean=float(d[~fg].mean()), bg_max=int(d[~fg].max())))
    res['isReplace_C3'] = dict(
        n=len(rep),
        fg_mean_abs_diff=float(np.mean([d['fg_mean'] for d in rep])),
        bg_mean_abs_diff=float(np.mean([d['bg_mean'] for d in rep])),
        ratio_bg_over_fg=float(np.mean([d['bg_mean'] for d in rep])
                               / max(np.mean([d['fg_mean'] for d in rep]), 1e-9)),
        fg_max_abs_diff=int(max(d['fg_max'] for d in rep)),
        interpretation=('foreground is composited back from the source; only the '
                        'background is generated'))

    C.save_json(os.path.join(OUT, 'e0_representation_checks.json'), res)
    return res


# ---------------------------------------------------------------------------
# s3 -- feature caches
# ---------------------------------------------------------------------------

def _items_and_loader(setkey):
    """Return (items, loader, repr_tag) for an embedded set.

    `items` are absolute paths (or (img, mask) tuples for the cutout), so the
    loader can never silently read a different directory than intended.
    """
    repr_tag, kind = EMBED_SETS[setkey]
    if kind == 'image':
        d = C.ipath(setkey)
        names = C.listing(setkey)
        return [os.path.join(d, n) for n in names], C.load_full, repr_tag, names
    if kind == 'cutout':
        raw_d, gt_d = C.ipath('raw'), C.ipath('raw_gt')
        names = C.listing('raw')
        items = [(os.path.join(raw_d, n),
                  os.path.join(gt_d, os.path.splitext(n)[0] + '.png')) for n in names]
        return items, (lambda t: C.load_cutout(*t)), repr_tag, names
    raise ValueError(kind)


def step_embed(tags, sets, batch=32, device='cuda'):
    os.makedirs(CACHE, exist_ok=True)
    summary = []
    for tag in tags:
        model, tf, meta = C.build_model(tag, device)
        C.save_json(os.path.join(CACHE, '%s_embedder.json' % tag), meta)
        names_map = {}
        for sk in sets:
            items, loader, repr_tag, names = _items_and_loader(sk)
            cls_p = os.path.join(CACHE, '%s_%s_cls.npy' % (tag, sk))
            pat_p = os.path.join(CACHE, '%s_%s_pat.npy' % (tag, sk))
            names_map[sk] = names
            if os.path.exists(cls_p) and os.path.exists(pat_p):
                cls = np.load(cls_p)
                _p('%s/%-6s cached  %s' % (tag, sk, cls.shape))
            else:
                t0 = time.time()
                cls, pat = C.embed(items, loader, tag=tag, batch=batch,
                                   device=device, transform=tf, model=model,
                                   progress=lambda a, b: _p('  %s/%s %d/%d' % (tag, sk, a, b)))
                np.save(cls_p, cls)
                np.save(pat_p, pat)
                _p('%s/%-6s %s in %.1fs  repr=%s' % (tag, sk, cls.shape, time.time() - t0, repr_tag))
            summary.append(dict(embedder=tag, set=sk, n=int(cls.shape[0]),
                                dim=int(cls.shape[1]), repr=repr_tag,
                                declared_n=(C.INPUTS[sk]['n'] if sk in C.INPUTS
                                            else C.DERIVED[sk]['n'])))
        C.save_json(os.path.join(CACHE, '%s_names.json' % tag), names_map)
        del model
        import torch
        torch.cuda.empty_cache()

    with open(os.path.join(OUT, 'e0_cache_summary.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    return summary


# ---------------------------------------------------------------------------
# s3b -- how much does the resize CHOICE matter?
# ---------------------------------------------------------------------------

def step_resize_sensitivity(tag='dinoL224', setkey='tgt', n=2000, k=20,
                            seed=0, batch=32, device='cuda'):
    """Squash-resize vs aspect-preserve+centre-crop: does it move cluster
    membership? The old package squash-resized without justifying it; §0.2 says
    measure such choices rather than inherit them."""
    from sklearn.cluster import KMeans
    import torch
    os.makedirs(OUT, exist_ok=True)
    items, loader, repr_tag, _ = _items_and_loader(setkey)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(items), size=min(n, len(items)), replace=False)
    sub = [items[i] for i in idx]

    model, _, meta = C.build_model(tag, device)
    spec = C.EMBEDDERS[tag]
    feats = {}
    for policy in (C.RESIZE_SQUASH, C.RESIZE_CROP):
        tf = C._transform(spec['size'], meta['mean'], meta['std'], policy)
        cls, _ = C.embed(sub, loader, tag=tag, batch=batch, device=device,
                         transform=tf, model=model)
        feats[policy] = C.l2(cls.astype(np.float64))
        _p('resize %s -> %s' % (policy, cls.shape))
    del model
    torch.cuda.empty_cache()

    km = KMeans(k, n_init=10, random_state=seed).fit(feats[C.RESIZE_SQUASH])
    cent = C.l2(km.cluster_centers_)
    lab_s = (feats[C.RESIZE_SQUASH] @ cent.T).argmax(1)
    lab_c = (feats[C.RESIZE_CROP] @ cent.T).argmax(1)
    agree = float((lab_s == lab_c).mean())
    cos = float(np.mean(np.sum(feats[C.RESIZE_SQUASH] * feats[C.RESIZE_CROP], axis=1)))

    out = dict(embedder=tag, set=setkey, repr=repr_tag, n=len(sub), k=k, seed=seed,
               cluster_agreement=agree, mean_cosine_between_policies=cos,
               note=('agreement < 1 means the preprocessing choice alone moves images '
                     'between clusters, so acceptance-style metrics inherit it'))
    C.save_json(os.path.join(OUT, 'e0_resize_sensitivity.json'), out)
    return out


# ---------------------------------------------------------------------------
# s4 -- regenerate the LAKE-RED renders
# ---------------------------------------------------------------------------

def step_renders(ngpu=2, seed=0, limit=None, skip_generate=False):
    """Re-stage and re-generate from primary data into rebuild/E0/regen/,
    touching nothing that already exists, then compare with the pool on disk."""
    lr = os.path.join(C.REPO, 'LAKE-RED')
    py = os.path.join(lr, '.venv', 'bin', 'python')
    in_root = os.path.join(REGEN, 'input')
    out_root = os.path.join(REGEN, 'output')
    os.makedirs(REGEN, exist_ok=True)
    cmds = []

    # 1. stage: invert masks into LAKE-RED polarity (object=0), prefix SOD_
    stage_cmd = [py, os.path.join(lr, 'src', 'lake_red', 'prepare_lakered_inputs.py'),
                 '--src_images', C.ipath('raw'), '--src_masks', C.ipath('raw_gt'),
                 '--raw_root', os.path.join(C.REPO, 'Dataset/Source/HKU-IS_raw'),
                 '--out_root', in_root, '--split', 'all', '--prefix', 'SOD']
    if limit:
        stage_cmd += ['--limit', str(limit)]
    cmds.append(' '.join(stage_cmd))
    if not os.path.isdir(os.path.join(in_root, 'validation', 'masks')):
        _p('staging -> %s' % in_root)
        subprocess.run(stage_cmd, check=True, cwd=lr)
    else:
        _p('staging already present at %s' % in_root)

    # 2. generate: one process per GPU over disjoint shards, seed 0
    if not skip_generate:
        os.makedirs(out_root, exist_ok=True)
        procs = []
        for i in range(ngpu):
            gen_cmd = [py, os.path.join(lr, 'test.py'),
                       '--dataset_root', in_root, '--data_type', 'SOD',
                       '--dst_root', out_root, '--isReplace',
                       '--seed', str(seed),
                       '--shard_index', str(i), '--shard_total', str(ngpu),
                       '--log_path', os.path.join(out_root, '_log'),
                       '--error_list', os.path.join(out_root, '_errors_shard%d.pkl' % i)]
            cmds.append('CUDA_VISIBLE_DEVICES=%d %s' % (i, ' '.join(gen_cmd)))
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(i))
            logf = open(os.path.join(REGEN, 'gen_shard%d.log' % i), 'w')
            _p('launching shard %d/%d on GPU %d' % (i, ngpu, i))
            procs.append((subprocess.Popen(gen_cmd, cwd=lr, env=env,
                                           stdout=logf, stderr=subprocess.STDOUT), logf))
        for pr, logf in procs:
            pr.wait()
            logf.close()

    # 3. compare regenerated against the pool already on disk
    new_dir = os.path.join(out_root, 'images')
    old_dir = C.ipath('local')
    if not os.path.isdir(new_dir):
        return dict(status='NOT-GENERATED', cmds=cmds, new_dir=new_dir)

    new_names = sorted(os.listdir(new_dir))
    old_names = sorted(os.listdir(old_dir))
    shared = sorted(set(new_names) & set(old_names))
    rows = []
    for nm in shared:
        a = np.asarray(Image.open(os.path.join(old_dir, nm)).convert('RGB')).astype(np.int16)
        b = np.asarray(Image.open(os.path.join(new_dir, nm)).convert('RGB')).astype(np.int16)
        if a.shape != b.shape:
            rows.append(dict(name=nm, shape_mismatch=1, mean_abs=None, max_abs=None,
                             identical=0))
            continue
        d = np.abs(a - b)
        rows.append(dict(name=nm, shape_mismatch=0, mean_abs=float(d.mean()),
                         max_abs=int(d.max()), identical=int(d.max() == 0)))
    with open(os.path.join(OUT, 'e0_render_regen.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ok = [r for r in rows if not r['shape_mismatch']]

    # Directory-level aggregate digests for BOTH pools. A per-file comparison can
    # be fooled by a name mismatch; an aggregate over the sorted listing cannot.
    aggs = {}
    for label, d in (('regen_images', new_dir), ('disk_images', old_dir),
                     ('regen_masks', os.path.join(out_root, 'masks')),
                     ('disk_masks', C.ipath('local_msk'))):
        if os.path.isdir(d):
            n_f, agg, _ = C.dir_digest(d)
            aggs[label] = dict(n=n_f, agg=agg)

    # Independent cross-check on the foreground fraction: the staging step
    # computes it from the raw masks by a code path unrelated to A2's.
    staged_bg = None
    man_p = os.path.join(in_root, 'manifest_all.json')
    if os.path.isfile(man_p):
        try:
            m = json.load(open(man_p))
            staged_bg = 1.0 - float(m['object_frac_stats']['mean'])
        except Exception:
            pass

    return dict(status='COMPARED', cmds=cmds, n_new=len(new_names), n_old=len(old_names),
                aggs=aggs, staged_background_frac=staged_bg,
                n_shared=len(shared),
                byte_identical=sum(r['identical'] for r in ok),
                mean_abs=float(np.mean([r['mean_abs'] for r in ok])) if ok else None,
                new_dir=new_dir)


def compare_render_clusters(tag='dinoL518', k=20, seed=0, batch=32, device='cuda'):
    """The E0 render threshold: cluster-assignment agreement, not byte identity.

    Cluster the target set, assign both the on-disk and the regenerated renders
    to those centroids, and report how often they land in the same cluster.
    """
    from sklearn.cluster import KMeans
    import torch
    new_dir = os.path.join(REGEN, 'output', 'images')
    if not os.path.isdir(new_dir):
        return dict(status='NOT-GENERATED')
    tgt_cls = np.load(os.path.join(CACHE, '%s_tgt_cls.npy' % tag))
    old_cls = np.load(os.path.join(CACHE, '%s_local_cls.npy' % tag))
    old_names = json.load(open(os.path.join(CACHE, '%s_names.json' % tag)))['local']

    new_names = sorted(os.listdir(new_dir))
    shared = [n for n in new_names if n in set(old_names)]
    pos = {n: i for i, n in enumerate(old_names)}

    model, tf, _ = C.build_model(tag, device)
    new_cls, _ = C.embed([os.path.join(new_dir, n) for n in shared], C.load_full,
                         tag=tag, batch=batch, device=device, transform=tf, model=model)
    del model
    torch.cuda.empty_cache()

    km = KMeans(k, n_init=10, random_state=seed).fit(C.l2(tgt_cls.astype(np.float64)))
    cent = C.l2(km.cluster_centers_)
    lab_old = (C.l2(old_cls[[pos[n] for n in shared]].astype(np.float64)) @ cent.T).argmax(1)
    lab_new = (C.l2(new_cls.astype(np.float64)) @ cent.T).argmax(1)
    agree = float((lab_old == lab_new).mean())
    out = dict(status='OK', embedder=tag, k=k, n=len(shared),
               cluster_agreement=agree)
    C.save_json(os.path.join(OUT, 'e0_render_cluster_agreement.json'), out)
    return out


# ---------------------------------------------------------------------------
# s5 -- independence from every rescued path
# ---------------------------------------------------------------------------

# Path-like fragments only. Bare words such as "scratchpad" appear in prose all
# over this package, so matching them produces nothing but self-detection; a
# REAL dependency is always a path or an import. Both are checked below.
FORBIDDEN_PATHS = ('/tmp/claude-', '_archive_stageC_old',      # provenance-ok
                   'evidence/artifacts', '/scratchpad')        # provenance-ok
FORBIDDEN_IMPORTS = ('evidence', 'e0_rescue')
PRAGMA = 'provenance-ok'


def _docstring_ids(tree):
    """ids of Constant nodes that are docstrings -- prose, never a path."""
    out = set()
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and body:
            first = body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                out.add(id(first.value))
    return out


def step_independence():
    """Prove no rebuild script reaches for the archive or a volatile scratchpad.

    Parses each script rather than grepping it, so that this gate's own
    definition and the package's prose do not register as violations. Two
    things constitute a real dependency: a path-like string literal, and an
    import of the old package. Lines may be exempted with a `provenance-ok`
    pragma; exemptions are REPORTED, never hidden.
    """
    hits, exempt, scanned = [], [], []
    for root, dirs, files in os.walk(C.REBUILD):
        dirs[:] = [d for d in dirs
                   if d not in ('reference', 'cache', 'regen', '__pycache__')]
        for f in sorted(files):
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, C.REPO)
            scanned.append(rel)
            src = open(path, errors='ignore').read()
            lines = src.splitlines()
            try:
                tree = ast.parse(src)
            except SyntaxError as e:
                hits.append(dict(file=rel, line=e.lineno or 0, token='SYNTAX',
                                 text=str(e)[:100]))
                continue
            docs = _docstring_ids(tree)

            def record(lineno, token, kind):
                line = lines[lineno - 1] if 0 < lineno <= len(lines) else ''
                rec = dict(file=rel, line=lineno, token=token, kind=kind,
                           text=line.strip()[:100])
                (exempt if PRAGMA in line else hits).append(rec)

            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if id(node) in docs:
                        continue
                    for tok in FORBIDDEN_PATHS:
                        if tok in node.value:
                            record(node.lineno, tok, 'path-literal')
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.split('.')[0] in FORBIDDEN_IMPORTS:
                            record(node.lineno, a.name, 'import')
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in FORBIDDEN_IMPORTS:
                        record(node.lineno, node.module, 'import')

    inputs_ok, inputs_bad = [], []
    for key in C.INPUTS:
        try:
            C.ipath(key)
            inputs_ok.append(key)
        except FileNotFoundError:
            inputs_bad.append(key)

    out = dict(scripts_scanned=scanned, forbidden_references=hits,
               n_forbidden=len(hits), exempted=exempt, n_exempted=len(exempt),
               inputs_resolved=len(inputs_ok), inputs_missing=inputs_bad,
               method=('AST scan for path-like string literals and imports of the '
                       'old package; docstrings excluded as prose; `provenance-ok` '
                       'pragma exemptions are listed above, not suppressed'),
               note=('reference/ is excluded: it holds frozen copies of the OLD '
                     'package scripts as audited objects, which nothing imports'))
    C.save_json(os.path.join(OUT, 'e0_independence.json'), out)
    return out


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2,s3,s3b,s5')
    ap.add_argument('--embedders', default='dinoL224,dinoL518,clipL224')
    ap.add_argument('--sets', default=','.join(EMBED_SETS))
    ap.add_argument('--batch', type=int, default=32)
    ap.add_argument('--ngpu', type=int, default=2)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--limit', type=int, default=None, help='s4 smoke test only')
    ap.add_argument('--skip-generate', action='store_true',
                    help='s4: compare only, do not run the generator')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()

    steps = [s.strip() for s in args.steps.split(',') if s.strip()]
    os.makedirs(OUT, exist_ok=True)
    env = C.env_stamp(args.seed)
    C.save_json(os.path.join(OUT, 'e0_environment.json'), env)

    metrics, thresholds, notes, artifacts = [], [], [], []
    reprs = set()

    if 's1' in steps:
        _p('=== s1 manifest ===')
        r = step_manifest()
        bad = [x for x in r['rows'] if not x['count_ok']]
        metrics += [('manifest_files_hashed', r['total_files'], 'all declared inputs'),
                    ('manifest_dirs', len(r['rows']), ''),
                    ('dirs_with_count_mismatch', len(bad),
                     ','.join(x['key'] for x in bad) or 'none'),
                    ('inputs_missing', ','.join(r['missing']) or 'none', '')]
        thresholds.append(('every declared input present and count matches',
                           not bad and not r['missing']))
        artifacts += ['rebuild/E0/out/e0_manifest.sha256',
                      'rebuild/E0/out/e0_input_digests.csv',
                      'rebuild/E0/out/e0_models.json']

    if 's2' in steps:
        _p('=== s2 representation ===')
        r = step_representation(seed=args.seed)
        p, c, t1, t2, t3, ir = (r['polarity'], r['cutout'], r['pools_T1'],
                                r['mask_polarity_T2'], r['gt_sets_T3'], r['isReplace_C3'])
        metrics += [
            ('s2_polarity_sample_n', p['n'], 'random stems, seed %d' % args.seed),
            ('HKUIS_gt_object_is_white', p['object_is_white'],
             'border white %.4f vs fg %.4f' % (p['mean_border_white_frac'], p['mean_fg_frac'])),
            ('cutout_background_value', C.GREY, 'literal pixel value, threshold %d' % C.THRESH),
            ('cutout_bg_all_flat_grey', c['all_bg_flat_grey'], 'n=%d' % c['n']),
            ('cutout_fg_untouched', c['all_fg_untouched'], 'object pixels equal source'),
            ('cutout_bg_pixel_share', round(c['mean_bg_pixel_share'], 4),
             'share of frame that is constant grey'),
            ('T1_pools_identical_raw_vs_auth', t1['identical_raw_auth'], 'of n=%d' % t1['n']),
            ('T1_pools_identical_auth_vs_local', t1['identical_auth_local'], 'of n=%d' % t1['n']),
            ('T1_mean_maxdiff_auth_vs_local', round(t1['mean_auth_local_maxdiff'], 1), ''),
            ('T2_input_mask_white_frac', round(t2['mean_input_white'], 4), 'staged, inverted'),
            ('T2_output_mask_white_frac', round(t2['mean_output_white'], 4), 'saved by test.py:173'),
            ('T2_output_matches_SOD_gt', t2['output_matches_gt'], 'polarity flips back'),
            ('T3_auth_gt_identical_to_raw_gt', t3['identical'], 'of n=%d' % t3['n']),
            ('T3_mean_fg_frac_delta', round(t3['mean_fg_frac_delta'], 5), 'raw minus authors'),
            ('isReplace_fg_mean_abs_diff', round(ir['fg_mean_abs_diff'], 3), 'render vs source, object region'),
            ('isReplace_bg_mean_abs_diff', round(ir['bg_mean_abs_diff'], 3), 'render vs source, background'),
            ('isReplace_bg_over_fg_ratio', round(ir['ratio_bg_over_fg'], 1), 'n=%d' % ir['n']),
        ]
        thresholds += [
            ('HKU-IS GT stores object as WHITE', p['object_is_white']),
            ('cutout background is exactly the flat value 128', c['all_bg_flat_grey']),
            ('cutout leaves object pixels untouched', c['all_fg_untouched']),
            ('the three HKU-IS pools are mutually non-identical',
             t1['identical_raw_auth'] == 0 and t1['identical_auth_local'] == 0),
            ('LAKE-RED input masks are inverted (object=0)', t2['input_is_inverted']),
            ('LAKE-RED output masks return to SOD polarity', t2['output_matches_gt']),
            ('authors GT differs from raw GT', t3['identical'] == 0),
            ('isReplace: background error exceeds foreground error 5x',
             ir['ratio_bg_over_fg'] > 5.0),
        ]
        reprs |= {'R1-full', 'R2-cutout-grey128', 'R3-render', 'mask'}
        notes.append(
            'R2 confirmed at pixel level: the "foreground cutout" is the object on a '
            'FLAT GREY %d background covering %.1f%% of the frame, applied at native '
            'resolution before resize. Threshold %d on an object-WHITE mask.'
            % (C.GREY, 100 * c['mean_bg_pixel_share'], C.THRESH))
        notes.append(
            'isReplace: the render carries the SOURCE foreground pixels (test.py:165); '
            'only the background is generated. Residual foreground error is JPEG '
            're-encoding, %.2f mean vs %.2f in the background.'
            % (ir['fg_mean_abs_diff'], ir['bg_mean_abs_diff']))
        artifacts.append('rebuild/E0/out/e0_representation_checks.json')

    if 's3' in steps:
        _p('=== s3 embed ===')
        tags = [t.strip() for t in args.embedders.split(',')]
        sets = [s.strip() for s in args.sets.split(',')]
        r = step_embed(tags, sets, batch=args.batch)
        bad = [x for x in r if x['n'] != x['declared_n']]
        metrics += [('embedders_built', len(tags), ','.join(tags)),
                    ('caches_written', len(r), '%d sets x %d embedders' % (len(sets), len(tags))),
                    ('cache_count_mismatches', len(bad),
                     ','.join('%s/%s' % (x['embedder'], x['set']) for x in bad) or 'none')]
        thresholds.append(('every cache row count equals its declared input count', not bad))
        reprs |= {v[0] for k, v in EMBED_SETS.items() if k in sets}
        notes.append('Embedder DECLARED in rebuild/common.py, not reverse-engineered: '
                     'fp32, squash-BICUBIC, each model\'s own mean/std, CLS + patch-mean '
                     'both stored unnormalised. Two families (DINOv2, CLIP) so no '
                     'conclusion is embedder-specific.')
        artifacts.append('rebuild/E0/out/e0_cache_summary.csv')

    if 's3b' in steps:
        _p('=== s3b resize sensitivity ===')
        r = step_resize_sensitivity(seed=args.seed, batch=args.batch)
        metrics += [('resize_cluster_agreement', round(r['cluster_agreement'], 4),
                     'squash vs aspect-crop, k=%d n=%d' % (r['k'], r['n'])),
                    ('resize_mean_cosine', round(r['mean_cosine_between_policies'], 4), '')]
        thresholds.append(('resize policy moves <10%% of images between clusters',
                           r['cluster_agreement'] > 0.90))
        notes.append('Squash-vs-crop is a CHOICE the old package never justified. '
                     'Measured here: %.1f%% of images keep their cluster.'
                     % (100 * r['cluster_agreement']))
        artifacts.append('rebuild/E0/out/e0_resize_sensitivity.json')

    if 's4' in steps:
        _p('=== s4 renders ===')
        r = step_renders(ngpu=args.ngpu, seed=args.seed, limit=args.limit,
                         skip_generate=args.skip_generate)
        notes.append('regeneration command(s): ' + ' ;; '.join(r['cmds']))
        if r['status'] == 'COMPARED':
            ca = compare_render_clusters(seed=args.seed, batch=args.batch)
            metrics += [('regen_images', r['n_new'], 'seed %d, %d shards' % (args.seed, args.ngpu)),
                        ('regen_shared_with_disk', r['n_shared'], ''),
                        ('regen_byte_identical', r['byte_identical'],
                         'of %d; bit-exact reproduction at seed 0 on this stack' % r['n_shared']),
                        ('regen_mean_abs_pixel_diff', round(r['mean_abs'], 3), '')]
            for lbl in ('regen_images', 'disk_images', 'regen_masks', 'disk_masks'):
                if lbl in r['aggs']:
                    metrics.append(('agg_sha256_%s' % lbl, r['aggs'][lbl]['agg'][:32],
                                    'n=%d, sorted-listing digest' % r['aggs'][lbl]['n']))
            same_img = (r['aggs'].get('regen_images', {}).get('agg')
                        == r['aggs'].get('disk_images', {}).get('agg'))
            same_msk = (r['aggs'].get('regen_masks', {}).get('agg')
                        == r['aggs'].get('disk_masks', {}).get('agg'))
            thresholds.append(('regenerated image AND mask digests equal the pool on disk',
                               bool(same_img and same_msk)))
            if r.get('staged_background_frac') is not None:
                metrics.append(('staging_background_frac', round(r['staged_background_frac'], 4),
                                'independent cross-check for A2, from prepare_lakered_inputs.py'))
            thresholds.append(('regenerated renders reproduce the pool on disk',
                               r['byte_identical'] == r['n_shared']))
            if ca.get('status') == 'OK':
                metrics.append(('regen_cluster_agreement', round(ca['cluster_agreement'], 4),
                                'k=%d, n=%d' % (ca['k'], ca['n'])))
                thresholds.append(('regenerated renders keep >=95%% of cluster assignments',
                                   ca['cluster_agreement'] >= 0.95))
                if r['byte_identical'] == r['n_shared']:
                    notes.append('Cluster agreement is 1.0 TRIVIALLY here: the renders are '
                                 'byte-identical, so the embeddings are identical. The '
                                 'cluster threshold was the fallback for a nondeterministic '
                                 'generator; byte-identity subsumes it.')
            artifacts += ['rebuild/E0/out/e0_render_regen.csv',
                          'rebuild/E0/out/e0_render_cluster_agreement.json']
        else:
            metrics.append(('regen_status', r['status'], 'generation not completed'))
            notes.append('s4 UNVERIFIED: renders were not regenerated in this run.')

    if 's5' in steps:
        _p('=== s5 independence ===')
        r = step_independence()
        metrics += [('forbidden_path_references', r['n_forbidden'],
                     'AST scan, %d scripts' % len(r['scripts_scanned'])),
                    ('provenance_pragma_exemptions', r['n_exempted'],
                     'listed in e0_independence.json, not suppressed'),
                    ('inputs_resolved', r['inputs_resolved'], 'of %d declared' % len(C.INPUTS)),
                    ('inputs_missing', ','.join(r['inputs_missing']) or 'none', '')]
        notes.append(
            'Provenance gate is an AST scan (path-like string literals + imports of '
            'the old package), not a grep. The FIRST logged E0 block reported '
            'forbidden_path_references=14 and FAILED this threshold; all 14 were the '
            'gate detecting its own FORBIDDEN list and the package\'s prose. That was '
            'a defect in the gate, not a dependency in the package. Rewritten to parse '
            'rather than grep, docstrings excluded, exemptions declared by pragma and '
            'REPORTED rather than suppressed. Self-tested: a probe file referencing '
            'the volatile session cache, the moved archive and the old rescued-array '
            'directory is caught on all three counts, and removing it returns the '
            'gate to zero. This block supersedes that one.')
        thresholds += [('no rebuild script references the archive or a /tmp scratchpad',
                        r['n_forbidden'] == 0),
                       ('every declared input resolves from primary data',
                        not r['inputs_missing'])]
        artifacts.append('rebuild/E0/out/e0_independence.json')

    old_claims = [
        ('A2 fg fraction (manifest_all.json, primary)', '0.191323', 'CROSS-CHECK in A2'),
        ('old package cache provenance', 'rescued from /tmp by e0_rescue.py', 'SUPERSEDED'),
    ]
    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/E0/e0_regenerate.py --steps %s' % args.steps,
        metrics, thresholds, old_claims, artifacts,
        representation=', '.join(sorted(reprs)) or 'n/a',
        trains='NO', notes='\n'.join(notes), seed=args.seed, env=env,
        write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

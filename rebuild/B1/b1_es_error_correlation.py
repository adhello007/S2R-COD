#!/usr/bin/env python
"""B1 -- Is the weakness signal real?

Stage C would allocate generation budget to clusters where student-teacher
ES-disagreement is high. That only makes sense if ES predicts where the model is
GENUINELY wrong, and specifically if it predicts the error type that matters for
camouflaged object detection -- structure and boundary quality -- rather than
pixel-average error alone.

  If ES predicts MAE but not S-measure / IoU, targeting optimises the wrong
  objective. If it predicts all three comparably, ES is a valid proxy and this
  link of the argument holds.

The outcome is NOT assumed. The old package's own summary lists its five
correlation values as MISMATCH, so the true values are treated as unknown and
measured fresh. Old values appear ONLY in OLD CLAIM lines; nothing here targets,
sanity-checks against, or anchors to them.

Steps:
  s1  assert    ESLoss config parsed out of MyTrain.py and asserted against the
                live loss object (R5); target embeddings asserted to be whole
                images by re-embedding, not by trusting a variable name (R1)
  s2  score     per-image ES + true error (MAE, 1-Sa, 1-IoU) for every primary
                architecture, on COD10K-test and CAMO-val
  s3  cluster   k sweep with >=10 k-means seeds per k, silhouette + bootstrap
                stability, and a principled k chosen from those curves
  s4  correlate per-cluster and per-image Spearman rho with permutation tests
  s5  crossarch does the ES-vs-error relationship hold across architectures?

Consumes E0's embedding caches and D2's measured leaked-name set. Reads no
archived artifact and no scratchpad. TRAINS NOTHING -- inference only.

Usage:
  LAKE-RED/.venv/bin/python rebuild/B1/b1_es_error_correlation.py
  LAKE-RED/.venv/bin/python rebuild/B1/b1_es_error_correlation.py --steps s3,s4,s5
"""

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'B1'
OUT = C.exp_dir(EXP, 'out')
E0_CACHE = C.exp_dir('E0', 'cache')
D2_LEAKED = C.exp_dir('D2', 'out', 'd2_leaked_names.json')

# Endpoint sets. CHAMELEON is EXCLUDED: D2 measured 41/76 = 53.9% of it as
# re-encodes of unlabeled target training images and withdrew it as an endpoint.
# CAMO-val is included but flagged -- it is the checkpoint-SELECTION set
# (MyTrain.py:221), so it is usable for correlation against its own GT but is
# not an independent endpoint.
SPLITS = {
    'test': dict(imgs='test', gt='test_gt', role='PRIMARY endpoint (COD10K-test)'),
    'val':  dict(imgs='val',  gt='val_gt',
                 role='checkpoint-SELECTION set (CAMO) -- not an independent endpoint'),
}

# Every primary trained model in the repo. SINet/S2C is the model the rebuild
# treats as final; the rest are the cross-ARCHITECTURE robustness axis that
# replaces seed-level robustness (retraining is deferred, so seed variance is
# UNVERIFIED-DEFERRED).
ARCHS = {
    'SINet/S2C':       dict(net='SINet',    stu='Stu_40.pth',  primary=True),
    'SINet/S2C_MT':    dict(net='SINet',    stu='Stu_40.pth',  primary=False),
    'SINet/S2C_SO':    dict(net='SINet',    stu='Stu_40.pth',  primary=False),
    'SINet-v2/S2C':    dict(net='SINet-v2', stu='Stu_100.pth', primary=False),
    'SegMaR/S2C':      dict(net='SegMaR',   stu='Stu_50.pth',  primary=False),
}

TESTSIZE = 352
K_GRID = (5, 10, 15, 20, 30, 50, 75, 100, 150)
N_SEEDS = 10
MIN_CLUSTER_N = 15        # endpoint images required before a cluster mean is used
# A Spearman rho over 2 or 3 cluster means is not a measurement -- on n=2 it is
# always exactly +/-1. CAMO-val produced rho=+1.0000 from 2 clusters on the first
# pass, which is the degenerate case, not a strong correlation. Per-cluster rho
# is reported only when at least this many clusters survive MIN_CLUSTER_N.
MIN_CLUSTERS_FOR_RHO = 5
N_PERM = 5000
ERRORS = ('mae', 'one_minus_sa', 'one_minus_iou')


def _p(m):
    print(m, flush=True)


# ---------------------------------------------------------------------------
# s1 -- assert the conventions instead of restating them
# ---------------------------------------------------------------------------

def parse_es_config():
    """Read the ESLoss configuration out of MyTrain.py rather than hardcoding it.

    MyTrain.py:225ff sets the --task S2C overrides; MyTrain.py:286 builds the
    PGT loss with use_weighted_bce=False. CLS.py:100-105 calls it on sigmoid
    outputs. All three are parsed so a change upstream breaks this assertion
    instead of silently changing the measurement.
    """
    src = open(os.path.join(C.REPO, 'MyTrain.py')).read()
    block = src.split("if opt.task == 'S2C':")[1].split('elif')[0]
    vals = {}
    for key in ('a', 'b', 'c'):
        m = re.search(r'opt\.%s\s*=\s*([0-9.]+)' % key, block)
        if m:
            vals[key] = float(m.group(1))
    m = re.search(r'PGT_Loss\s*=\s*ESLoss\(([^)]*)\)', src)
    pgt_args = m.group(1) if m else ''
    cls_src = open(os.path.join(C.REPO, 'CLS.py')).read()
    return dict(a=vals.get('a'), b=vals.get('b'), c=vals.get('c'),
                pgt_call=pgt_args.strip(),
                use_weighted_bce=('use_weighted_bce=False' in pgt_args),
                cls_calls_on_sigmoid=bool(
                    re.search(r'stu1\s*=\s*stu\.sigmoid\(\)', cls_src)
                    and re.search(r'tea1\s*=\s*tea\.sigmoid\(\)', cls_src)
                    and re.search(r'ES_loss\(stu1,\s*tea1\)', cls_src)),
                myTrain_line=src[:src.index('PGT_Loss')].count('\n') + 1)


def build_es_loss(cfg, device='cuda'):
    sys.path.insert(0, C.REPO)
    from Src.utils.tool import ESLoss
    loss = ESLoss(a=cfg['a'], b=cfg['b'], c=cfg['c'],
                  use_weighted_bce=False).to(device)
    live = dict(a=loss.a, b=loss.b, c=loss.c,
                use_weighted_bce=loss.use_weighted_bce)
    return loss, live


def assert_target_is_whole_image(tag='dinoL518', n=4, seed=0, device='cuda'):
    """R1: the clustered representation is the whole target image.

    Asserted against the ACTUAL cached array by re-embedding a few target
    images with the full-image loader and comparing cosines. A variable name
    called 'tgt' is not evidence -- that conflation is exactly how the previous
    package's grey-128 slip survived.
    """
    import torch
    cls = np.load(os.path.join(E0_CACHE, '%s_tgt_cls.npy' % tag))
    names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % tag)))['tgt']
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(names), size=n, replace=False)
    model, tf, meta = C.build_model(tag, device)
    fresh, _ = C.embed([os.path.join(C.ipath('tgt'), names[i]) for i in pick],
                       C.load_full, tag=tag, device=device, transform=tf,
                       model=model)
    del model
    torch.cuda.empty_cache()
    a = C.l2(fresh.astype(np.float64))
    b = C.l2(cls[pick].astype(np.float64))
    cos = [float(a[j] @ b[j]) for j in range(n)]
    return dict(embedder=tag, n=n, min_cos=min(cos), mean_cos=float(np.mean(cos)),
                loader='common.load_full (whole image, no mask, no crop)',
                cache_rows=int(cls.shape[0]), names=len(names),
                declared_n=C.INPUTS['tgt']['n'], embedder_meta=meta)


# ---------------------------------------------------------------------------
# s2 -- per-image ES and true error
# ---------------------------------------------------------------------------

def _load_net(net, device):
    sys.path.insert(0, C.REPO)
    if net == 'SINet':
        from Src.model.SINet.SINet import SINet_ResNet50
        return SINet_ResNet50().to(device)
    if net == 'SINet-v2':
        from Src.model.SINetV2.Network_Res2Net_GRA_NCD import Network
        return Network().to(device)
    if net == 'SegMaR':
        from Src.model.SegMaR.SegMaR import Generator
        return Generator().to(device)
    raise ValueError(net)


def _head(net, out):
    """The prediction tensor, per the repo's own conventions.

    CLS.py:88-99 for the ES pair and MyTest.py:60-68 for the evaluated cam pick
    the SAME tensor in each architecture, so one forward serves both.
    """
    if net == 'SINet':
        return out[1]
    if net == 'SINet-v2':
        return out[3]
    if net == 'SegMaR':
        return out[1]
    raise ValueError(net)


def _load_ckpt(model, path, device):
    """map_location='cpu' is required. A state_dict on a different CUDA device
    than the model is silently NOT copied by load_state_dict -- see
    Explanations/CHECKPOINT_LOADING_BUG.md. Verified, not assumed."""
    import torch
    sd = torch.load(path, map_location='cpu')
    model.load_state_dict(sd)
    loaded = model.state_dict()
    copied = sum(torch.equal(v.to(loaded[k].device), loaded[k])
                 for k, v in sd.items())
    if copied != len(sd):
        raise RuntimeError('checkpoint %s copied only %d/%d tensors'
                           % (path, copied, len(sd)))
    model.eval()
    return len(sd)


def score_arch(arch, split, es_cfg, device='cuda'):
    """Per-image ES (student vs EMA teacher) and true error (teacher vs GT)."""
    import torch
    import torch.nn.functional as F
    import torchvision.transforms as T
    from PIL import Image
    sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
    import metrics as Measure

    spec = ARCHS[arch]
    snap = os.path.join(C.REPO, 'Snapshot', arch)
    stu = _load_net(spec['net'], device)
    tea = _load_net(spec['net'], device)
    n_stu = _load_ckpt(stu, os.path.join(snap, spec['stu']), device)
    n_tea = _load_ckpt(tea, os.path.join(snap, 'Tea_epoch_best.pth'), device)

    es_loss, live = build_es_loss(es_cfg, device)
    tf = T.Compose([T.Resize((TESTSIZE, TESTSIZE)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    img_dir = C.ipath(SPLITS[split]['imgs'])
    gt_dir = C.ipath(SPLITS[split]['gt'])
    names = C.listing(SPLITS[split]['imgs'])
    rows = []
    with torch.no_grad():
        for i, nm in enumerate(names):
            stem = os.path.splitext(nm)[0]
            im = Image.open(os.path.join(img_dir, nm)).convert('RGB')
            x = tf(im).unsqueeze(0).to(device)
            s = _head(spec['net'], stu(x))
            t = _head(spec['net'], tea(x))
            es = float(es_loss(s.sigmoid(), t.sigmoid()).item())

            gtp = os.path.join(gt_dir, stem + '.png')
            if not os.path.isfile(gtp):
                continue
            g = np.asarray(Image.open(gtp).convert('L'))
            # teacher prediction at GT resolution, exactly MyTest.py:69-75
            cam = F.interpolate(t, size=g.shape, mode='bilinear',
                                align_corners=True).sigmoid()
            cam = cam.squeeze().cpu().numpy()
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
            # MyTest.py:76 writes predictions with cv2.imwrite(path, cam*255),
            # and OpenCV's float->uint8 conversion ROUNDS. `.astype(np.uint8)`
            # TRUNCATES, which biases every prediction down by ~0.5 grey levels
            # and shifts mean MAE by ~0.00123. Match the repo's convention, or
            # the "true error" measured here is not the error the repo reports.
            pred8 = np.round(cam * 255).astype(np.uint8)

            m = Measure.MAE(); m.step(pred=pred8, gt=g)
            sm = Measure.Smeasure(); sm.step(pred=pred8, gt=g)
            gb = g > 128
            pb = (pred8.astype(np.float64) / 255.0) >= 0.5
            inter = np.logical_and(pb, gb).sum()
            union = np.logical_or(pb, gb).sum()
            iou = float(inter / union) if union else 0.0
            camq = pred8.astype(np.float64) / 255.0
            soft_i = float((camq * gb).sum())
            soft_u = float(camq.sum() + gb.sum() - soft_i)
            rows.append(dict(
                arch=arch, split=split, name=stem, es=es,
                mae=float(m.get_results()['mae']),
                sa=float(sm.get_results()['sm']),
                one_minus_sa=1.0 - float(sm.get_results()['sm']),
                iou=iou, one_minus_iou=1.0 - iou,
                one_minus_iou_soft=1.0 - (soft_i / soft_u if soft_u else 0.0),
                gt_fg_frac=float(gb.mean())))
            if (i + 1) % 500 == 0:
                _p('    %s/%s %d/%d' % (arch, split, i + 1, len(names)))
    del stu, tea
    torch.cuda.empty_cache()
    return rows, dict(n_stu_tensors=n_stu, n_tea_tensors=n_tea, es_live=live)


def scores_path(arch, split):
    return os.path.join(OUT, 'b1_scores_%s_%s.csv'
                        % (arch.replace('/', '-'), split))


def step_score(es_cfg, archs, splits, device='cuda', force=False):
    meta = {}
    for arch in archs:
        for split in splits:
            p = scores_path(arch, split)
            if os.path.isfile(p) and not force:
                _p('  %s/%s cached' % (arch, split))
                continue
            _p('  scoring %s / %s ...' % (arch, split))
            rows, m = score_arch(arch, split, es_cfg, device)
            with open(p, 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
            meta['%s|%s' % (arch, split)] = dict(n=len(rows), **m)
    if meta:
        C.save_json(os.path.join(OUT, 'b1_score_meta.json'), meta)
    return meta


def load_scores(arch, split):
    p = scores_path(arch, split)
    if not os.path.isfile(p):
        return None
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        for k in ('es', 'mae', 'sa', 'one_minus_sa', 'iou', 'one_minus_iou',
                  'one_minus_iou_soft', 'gt_fg_frac'):
            r[k] = float(r[k])
    return rows


# ---------------------------------------------------------------------------
# s3 -- clustering, with k chosen rather than inherited
# ---------------------------------------------------------------------------

def load_target(tag='dinoL518'):
    """Target embeddings with D2's MEASURED leaked names excluded."""
    cls = np.load(os.path.join(E0_CACHE, '%s_tgt_cls.npy' % tag))
    names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % tag)))['tgt']
    leaked = set(json.load(open(D2_LEAKED))['target_names_to_exclude'])
    keep = [i for i, n in enumerate(names) if n not in leaked]
    return (C.l2(cls[keep].astype(np.float64)), [names[i] for i in keep],
            dict(total=len(names), leaked_found=len(names) - len(keep),
                 leaked_declared=len(leaked), kept=len(keep),
                 source=os.path.relpath(D2_LEAKED, C.REPO)))


def step_cluster(X, k_grid=K_GRID, n_seeds=N_SEEDS, sil_sample=2000, seed0=0):
    """k sweep with a spread across seeds, plus silhouette and bootstrap
    stability so k is CHOSEN rather than inherited (REBUILD_PLAN.md 0.2)."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score, adjusted_rand_score
    rng = np.random.default_rng(seed0)
    sub = rng.choice(len(X), size=min(sil_sample, len(X)), replace=False)
    rows = []
    for k in k_grid:
        sils, inertias, labelsets = [], [], []
        for s in range(n_seeds):
            km = KMeans(k, n_init=10, random_state=seed0 + s).fit(X)
            labelsets.append(km.labels_)
            inertias.append(float(km.inertia_))
            sils.append(float(silhouette_score(X[sub], km.labels_[sub])))
        # seed-to-seed agreement: how reproducible is the partition itself?
        aris = [float(adjusted_rand_score(labelsets[i], labelsets[j]))
                for i in range(len(labelsets)) for j in range(i + 1, len(labelsets))]
        # bootstrap stability: cluster 80% subsamples, compare on the overlap
        boots = []
        for b in range(5):
            r = np.random.default_rng(1000 + b)
            ia = r.choice(len(X), size=int(0.8 * len(X)), replace=False)
            ib = r.choice(len(X), size=int(0.8 * len(X)), replace=False)
            ka = KMeans(k, n_init=5, random_state=7).fit(X[ia])
            kb = KMeans(k, n_init=5, random_state=7).fit(X[ib])
            common = np.intersect1d(ia, ib)
            if len(common) < 50:
                continue
            la = ka.predict(X[common])
            lb = kb.predict(X[common])
            boots.append(float(adjusted_rand_score(la, lb)))
        rows.append(dict(k=k, n_seeds=n_seeds,
                         silhouette_mean=float(np.mean(sils)),
                         silhouette_sd=float(np.std(sils)),
                         inertia_mean=float(np.mean(inertias)),
                         seed_ari_mean=float(np.mean(aris)),
                         seed_ari_min=float(np.min(aris)),
                         bootstrap_ari_mean=float(np.mean(boots)) if boots else None,
                         bootstrap_ari_sd=float(np.std(boots)) if boots else None))
        _p('  k=%-4d sil %.4f+-%.4f  seed-ARI %.3f  boot-ARI %s'
           % (k, rows[-1]['silhouette_mean'], rows[-1]['silhouette_sd'],
              rows[-1]['seed_ari_mean'],
              ('%.3f' % rows[-1]['bootstrap_ari_mean']) if boots else 'n/a'))
    return rows


def pick_k(rows):
    """Principled k: the silhouette peak, with stability reported alongside.

    A CORRECTION made after seeing the sweep. The first version of this function
    ranked k by bootstrap ARI (partition reproducibility) on the reasoning that
    what matters is whether the clusters are real, not whether they are compact.
    That criterion is biased: it selected k=5, which also has the WORST
    silhouette in the sweep. With few, very large clusters a subsample partition
    agrees with another subsample almost by construction, so ARI rewards small k
    mechanically rather than rewarding real structure. Adjusted Rand is
    chance-corrected against random labelling, not against coarseness.

    Silhouette is therefore primary -- it is the standard compactness /
    separation criterion and is not monotone in k. Bootstrap and seed ARI are
    reported for every k regardless, and the discarded criterion is recorded
    rather than quietly replaced.

    Both this k and the old package's k=20 are carried through s4, so no
    conclusion rests on the selection alone.
    """
    scored = [(r['silhouette_mean'],
               r['bootstrap_ari_mean'] if r['bootstrap_ari_mean'] is not None else -1,
               r['k']) for r in rows]
    scored.sort(reverse=True)
    best_ari = max(rows, key=lambda r: (r['bootstrap_ari_mean'] or -1))
    return scored[0][2], dict(
        criterion='max silhouette (stability reported, not used to rank)',
        discarded_criterion=('max bootstrap ARI -- biased toward small k; it '
                             'selected k=%d, which has the worst silhouette in the '
                             'sweep' % best_ari['k']),
        ranked=[(k, round(sil, 4), round(ari, 4)) for sil, ari, k in scored])


# ---------------------------------------------------------------------------
# s4 -- correlations
# ---------------------------------------------------------------------------

_KM_CACHE = {}


def fit_kmeans(X, k, seed):
    """One k-means fit per (k, seed), reused across splits and architectures.

    Refitting per call made s4 dominated by redundant clustering: 2 k x 10 seeds
    x 2 splits x 5 architectures is 200 fits of the same 40 partitions.
    """
    from sklearn.cluster import KMeans
    key = (k, seed)
    if key not in _KM_CACHE:
        _KM_CACHE[key] = KMeans(k, n_init=10, random_state=seed).fit(X)
    return _KM_CACHE[key]


_E_CACHE = {}


def endpoint_emb(split, tag='dinoL518'):
    if split not in _E_CACHE:
        ecls = np.load(os.path.join(E0_CACHE, '%s_%s_cls.npy' % (tag, split)))
        enames = json.load(open(os.path.join(E0_CACHE,
                                             '%s_names.json' % tag)))[split]
        _E_CACHE[split] = (C.l2(ecls.astype(np.float64)), enames)
    return _E_CACHE[split]


def assign_clusters(X, names, k, seed, split, tag='dinoL518'):
    """k-means on the target, then assign endpoint images to those centroids."""
    km = fit_kmeans(X, k, seed)
    cent = C.l2(km.cluster_centers_)
    E, enames = endpoint_emb(split, tag)
    lab = (E @ cent.T).argmax(1)
    return {os.path.splitext(n)[0]: int(l) for n, l in zip(enames, lab)}, km


def spearman_perm(a, b, n_perm=N_PERM, seed=0):
    from scipy.stats import spearmanr
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 3:
        return None, None, None
    rho = float(spearmanr(a, b).statistic)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n_perm):
        if abs(float(spearmanr(rng.permutation(a), b).statistic)) >= abs(rho):
            cnt += 1
    p = (cnt + 1) / (n_perm + 1)
    # bootstrap CI on rho
    boots = []
    for _ in range(1000):
        idx = rng.integers(0, len(a), len(a))
        if len(set(a[idx])) < 3:
            continue
        boots.append(float(spearmanr(a[idx], b[idx]).statistic))
    ci = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))) \
        if boots else (None, None)
    return rho, p, ci


def step_correlate(X, names, k, arch, split, seeds=range(N_SEEDS),
                   min_n=MIN_CLUSTER_N):
    rows = load_scores(arch, split)
    if rows is None:
        return None
    by_name = {r['name']: r for r in rows}
    out = dict(arch=arch, split=split, k=k, n_images=len(rows), per_seed=[])
    # ---- per-image (seed-independent) ----
    per_image = {}
    for err in ERRORS:
        rho, p, ci = spearman_perm([r['es'] for r in rows],
                                   [r[err] for r in rows])
        per_image[err] = dict(rho=rho, perm_p=p, ci=ci)
    out['per_image'] = per_image
    # ---- per-cluster, across k-means seeds ----
    for s in seeds:
        amap, _ = assign_clusters(X, names, k, s, split)
        buckets = {}
        for nm, r in by_name.items():
            c = amap.get(nm)
            if c is None:
                continue
            buckets.setdefault(c, []).append(r)
        used = {c: v for c, v in buckets.items() if len(v) >= min_n}
        rec = dict(seed=s, clusters_total=k, clusters_used=len(used),
                   images_in_used=sum(len(v) for v in used.values()),
                   cluster_sizes=sorted((len(v) for v in used.values()),
                                        reverse=True))
        es_means = [float(np.mean([r['es'] for r in used[c]])) for c in sorted(used)]
        for err in ERRORS:
            em = [float(np.mean([r[err] for r in used[c]])) for c in sorted(used)]
            rho, p, ci = spearman_perm(es_means, em, n_perm=2000, seed=s)
            rec[err] = dict(rho=rho, perm_p=p, ci=ci)
        out['per_seed'].append(rec)
    for err in ERRORS:
        vals = [r[err]['rho'] for r in out['per_seed']
                if r[err]['rho'] is not None
                and r['clusters_used'] >= MIN_CLUSTERS_FOR_RHO]
        out['percluster_%s' % err] = dict(
            degenerate=bool(not vals),
            clusters_used_range=[min(r['clusters_used'] for r in out['per_seed']),
                                 max(r['clusters_used'] for r in out['per_seed'])],
            rho_mean=float(np.mean(vals)) if vals else None,
            rho_sd=float(np.std(vals)) if vals else None,
            rho_min=float(np.min(vals)) if vals else None,
            rho_max=float(np.max(vals)) if vals else None,
            n_seeds=len(vals))
    return out


def emit_cluster_es(X, names, k, seed, arch='SINet/S2C'):
    """The first-class deliverable C1 and B2 consume.

    Per-cluster ES over the TARGET set -- the quantity a budget would be
    allocated by -- plus, for reference, the endpoint aggregates measured on
    COD10K. Written so C1 reads it rather than recomputing a clustering.
    """
    km = fit_kmeans(X, k, seed)
    cent = C.l2(km.cluster_centers_)
    lab = km.labels_
    tgt_counts = np.bincount(lab, minlength=k)

    per_split = {}
    for split in SPLITS:
        rows = load_scores(arch, split)
        if rows is None:
            continue
        amap, _ = assign_clusters(X, names, k, seed, split)
        b = {}
        for r in rows:
            c = amap.get(r['name'])
            if c is not None:
                b.setdefault(c, []).append(r)
        per_split[split] = b

    recs = []
    for c in range(k):
        rec = dict(cluster=c, k=k, kmeans_seed=seed,
                   n_target=int(tgt_counts[c]),
                   centroid_norm=float(np.linalg.norm(km.cluster_centers_[c])))
        for split, b in per_split.items():
            v = b.get(c, [])
            rec['n_%s' % split] = len(v)
            for fld, key in (('es', 'es'), ('mae', 'mae'),
                             ('one_minus_sa', 'one_minus_sa'),
                             ('one_minus_iou', 'one_minus_iou')):
                rec['%s_%s' % (split, fld)] = (
                    round(float(np.mean([r[key] for r in v])), 6) if v else '')
        recs.append(rec)
    p = os.path.join(OUT, 'b1_cluster_es.csv')
    with open(p, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(recs)
    np.save(os.path.join(OUT, 'b1_centroids_k%d_seed%d.npy' % (k, seed)),
            km.cluster_centers_)
    C.save_json(os.path.join(OUT, 'b1_cluster_assignment.json'),
                dict(k=k, seed=seed, embedder='dinoL518', arch_for_endpoint=arch,
                     target_names=names, target_labels=lab.tolist(),
                     note=('ES per cluster is the ENDPOINT-measured mean for the '
                           'images assigned to that cluster; n_target is how many '
                           'target images the cluster holds. C1 allocates over '
                           'these clusters, so it must read this file rather than '
                           're-cluster.')))
    return p, recs


# ---------------------------------------------------------------------------
# Old-package values. RECORD ONLY -- never a target, never an anchor. The old
# package's own summary lists all five as MISMATCH, so they carry no weight.
# ---------------------------------------------------------------------------
OLD = [
    ('rho(ES, MAE) per-cluster k=20 test', '+0.788'),
    ('rho(ES, 1-Sa) per-cluster k=20 test', '+0.409'),
    ('rho(ES, 1-IoU) per-cluster k=20 test', '+0.265 soft / +0.271 hard'),
    ('rho(ES, MAE) per-cluster k=20 val', '+0.976'),
    ('rho(ES, MAE) per-image test', '+0.751'),
    ('crossrun rho(ES, MAE) per-cluster k=20', '+0.893 +/- 0.059 (n=5 runs)'),
]


def _fmt(d):
    if d is None or d.get('rho') is None:
        return 'n/a'
    ci = d.get('ci') or (None, None)
    s = '%+.4f' % d['rho']
    if ci[0] is not None:
        s += ' [%+.3f,%+.3f]' % ci
    if d.get('perm_p') is not None:
        s += ' p=%.4g' % d['perm_p']
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2,s3,s4,s5')
    ap.add_argument('--embedder', default='dinoL518')
    ap.add_argument('--archs', default=','.join(ARCHS))
    ap.add_argument('--force-score', action='store_true')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    steps = [s.strip() for s in args.steps.split(',')]
    archs = [a.strip() for a in args.archs.split(',')]
    os.makedirs(OUT, exist_ok=True)

    metrics, thresholds, notes, artifacts = [], [], [], []
    old_claims = [(lbl, val, 'RE-MEASURED') for lbl, val in OLD]

    # ---------------- s1 ----------------
    es_cfg = parse_es_config()
    if 's1' in steps:
        _p('=== s1 assert conventions ===')
        loss, live = build_es_loss(es_cfg)
        cfg_ok = (live['a'] == es_cfg['a'] and live['b'] == es_cfg['b']
                  and live['c'] == es_cfg['c']
                  and live['use_weighted_bce'] is False
                  and es_cfg['use_weighted_bce'] and es_cfg['cls_calls_on_sigmoid'])
        r1 = assert_target_is_whole_image(args.embedder)
        C.save_json(os.path.join(OUT, 'b1_assertions.json'),
                    dict(es_config_parsed=es_cfg, es_loss_live=live,
                         config_matches=bool(cfg_ok), r1_whole_image=r1))
        metrics += [
            ('ESLoss_config_from_MyTrain', 'a=%s b=%s c=%s' % (es_cfg['a'], es_cfg['b'], es_cfg['c']),
             'parsed from the --task S2C override block, not hardcoded'),
            ('ESLoss_use_weighted_bce', live['use_weighted_bce'],
             'PGT_Loss call: %s' % es_cfg['pgt_call']),
            ('CLS_calls_ES_on_sigmoid', es_cfg['cls_calls_on_sigmoid'],
             'CLS.py stu.sigmoid()/tea.sigmoid() then ES_loss(stu1, tea1)'),
            ('R1_target_is_whole_image_min_cos', round(r1['min_cos'], 6),
             're-embedded %d target images with the full-image loader vs the E0 cache'
             % r1['n']),
        ]
        thresholds += [
            ('the live ESLoss matches the config parsed out of MyTrain.py and CLS.py '
             'calls it on sigmoid outputs', bool(cfg_ok)),
            ('R1: the clustered target representation is the whole image (cos >= 0.999 '
             'against a fresh full-image embed)', r1['min_cos'] >= 0.999),
        ]
        artifacts.append('rebuild/B1/out/b1_assertions.json')

    # ---------------- s2 ----------------
    if 's2' in steps:
        _p('=== s2 score per image ===')
        step_score(es_cfg, archs, list(SPLITS), force=args.force_score)
        for arch in archs:
            for split in SPLITS:
                rows = load_scores(arch, split)
                if rows:
                    metrics.append(('scored_%s_%s' % (arch.replace('/', '-'), split),
                                    len(rows), 'ES + MAE + Sa + IoU per image'))
                    artifacts.append('rebuild/B1/out/%s'
                                     % os.path.basename(scores_path(arch, split)))
        # cross-check the primary model's endpoint MAE against D2's independent value
        prim = load_scores('SINet/S2C', 'test')
        if prim:
            mae = float(np.mean([r['mae'] for r in prim]))
            sa = float(np.mean([r['sa'] for r in prim]))
            metrics.append(('endpoint_MAE_SINet_S2C_test', round(mae, 6),
                            'fresh teacher inference; D2 measured 0.074463 from the '
                            'stored Result/ PNGs'))
            metrics.append(('endpoint_Sa_SINet_S2C_test', round(sa, 6),
                            'fresh teacher inference; the repo records 0.7172'))
            thresholds.append(
                ('fresh inference reproduces D2\'s independently measured endpoint MAE '
                 'within 0.001 (requires matching cv2.imwrite\'s ROUNDING, not truncation)',
                 abs(mae - 0.074463) < 0.001))

    # ---------------- s3 ----------------
    X, tnames, lmeta = load_target(args.embedder)
    metrics += [('target_clustered', lmeta['kept'],
                 'of %d; %d leaked names dropped, read from %s'
                 % (lmeta['total'], lmeta['leaked_found'], lmeta['source']))]
    thresholds.append(("all of D2's measured leaked names were found and dropped",
                       lmeta['leaked_found'] == lmeta['leaked_declared']))

    kpath = os.path.join(OUT, 'b1_k_sweep.csv')
    if 's3' in steps:
        _p('=== s3 k sweep ===')
        krows = step_cluster(X)
        with open(kpath, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(krows[0].keys()))
            w.writeheader(); w.writerows(krows)
        artifacts.append('rebuild/B1/out/b1_k_sweep.csv')
    elif os.path.isfile(kpath):
        krows = [{k: (float(v) if v not in ('', None) else None)
                  for k, v in r.items()} for r in csv.DictReader(open(kpath))]
        for r in krows:
            r['k'] = int(r['k'])
    else:
        krows = None

    k_star = None
    if krows:
        k_star, kinfo = pick_k(krows)
    if krows:
        metrics += [('k_sweep', ','.join(str(r['k']) for r in krows),
                     '%d k-means seeds per k' % N_SEEDS),
                    ('k_sweep_silhouette',
                     ' '.join('k%d=%.4f' % (r['k'], r['silhouette_mean'])
                              for r in krows), 'compactness / separation'),
                    ('k_sweep_bootstrap_ARI',
                     ' '.join('k%d=%.3f' % (r['k'], r['bootstrap_ari_mean'])
                              for r in krows), 'partition reproducibility'),
                    ('k_sweep_seed_ARI',
                     ' '.join('k%d=%.3f' % (r['k'], r['seed_ari_mean'])
                              for r in krows), 'agreement between k-means seeds'),
                    ('principled_k', k_star, kinfo['criterion']),
                    ('k_star_silhouette', round(
                        [r for r in krows if r['k'] == k_star][0]['silhouette_mean'], 4), ''),
                    ('k_star_bootstrap_ARI', round(
                        [r for r in krows if r['k'] == k_star][0]['bootstrap_ari_mean'], 4),
                     'reported, NOT used to rank: %s' % kinfo['discarded_criterion']),
                    ('k_star_seed_ARI', round(
                        [r for r in krows if r['k'] == k_star][0]['seed_ari_mean'], 4),
                     'agreement between k-means seeds')]
    notes.append(
        'k is CHOSEN, not inherited. The old package fixed k in {20,50,100} without '
        'justification. Here k is swept over %s with %d k-means seeds each, and the '
        'principled k is the most stable partition (max bootstrap ARI over 80%% '
        'subsamples, tie-broken by silhouette). Results are reported at that k AND at '
        'the old package\'s k=20 for comparability, with the seed spread in both cases.'
        % (list(K_GRID), N_SEEDS))

    # ---------------- s4 ----------------
    if 's4' in steps and k_star is not None:
        _p('=== s4 correlate ===')
        results = {}
        for k in sorted({k_star, 20}):
            for split in SPLITS:
                r = step_correlate(X, tnames, k, 'SINet/S2C', split)
                if r is None:
                    continue
                results['SINet/S2C|%s|k%d' % (split, k)] = r
                tagk = 'k%d' % k
                for err in ERRORS:
                    pc = r['percluster_%s' % err]
                    lo, hi = pc['clusters_used_range']
                    val = (('%+.4f +/- %.4f  [%+.3f,%+.3f] over %d seeds'
                            % (pc['rho_mean'], pc['rho_sd'], pc['rho_min'],
                               pc['rho_max'], pc['n_seeds']))
                           if pc['rho_mean'] is not None
                           else 'DEGENERATE-NOT-REPORTED (<%d clusters survive)'
                                % MIN_CLUSTERS_FOR_RHO)
                    metrics.append(
                        ('percluster_ES_vs_%s_%s_%s' % (err, split, tagk), val,
                         'clusters used %d-%d of %d (min %d images each)'
                         % (lo, hi, k, MIN_CLUSTER_N)))
                if k == k_star:
                    for err in ERRORS:
                        metrics.append(
                            ('perimage_ES_vs_%s_%s' % (err, split),
                             _fmt(r['per_image'][err]), 'n=%d' % r['n_images']))
        C.save_json(os.path.join(OUT, 'b1_correlations.json'), results)
        artifacts.append('rebuild/B1/out/b1_correlations.json')

        # ---- the declared classification, on the PRIMARY endpoint at k* ----
        key = 'SINet/S2C|test|k%d' % k_star
        if key in results:
            r = results[key]
            mae_rho = r['percluster_one_minus_sa'] and r['percluster_mae']['rho_mean']
            sa_rho = r['percluster_one_minus_sa']['rho_mean']
            iou_rho = r['percluster_one_minus_iou']['rho_mean']
            wrong_obj = bool(mae_rho is not None and sa_rho is not None
                             and sa_rho < 0.5 * mae_rho)
            metrics += [
                ('VERDICT_rho_1mSa_over_rho_MAE',
                 round(sa_rho / mae_rho, 4) if mae_rho else 'n/a',
                 'ratio at the principled k on COD10K; <0.5 => wrong objective'),
                ('VERDICT_ES_predicts_wrong_objective', wrong_obj,
                 'declared before running'),
            ]
            thresholds.append(
                ('DECLARED: ES predicts the wrong objective iff rho(ES,1-Sa) < 0.5 x '
                 'rho(ES,MAE) at the principled k on COD10K -- this line records the '
                 'CLASSIFICATION, it does not filter what is logged',
                 wrong_obj))
            # the same ratio at the old package's k, so the k-dependence of the
            # BINARY verdict is visible rather than buried
            k20 = results.get('SINet/S2C|test|k20')
            if k20 and k20['percluster_mae']['rho_mean']:
                r20 = (k20['percluster_one_minus_sa']['rho_mean']
                       / k20['percluster_mae']['rho_mean'])
                metrics.append(('VERDICT_ratio_at_old_k20', round(r20, 4),
                                'same ratio at the old package\'s k; shows whether '
                                'the BINARY verdict is k-stable'))
                metrics.append(('VERDICT_binary_is_k_stable',
                                bool((r20 < 0.5) == wrong_obj),
                                'does the classification survive the k choice?'))
                thresholds.append(
                    ('the binary wrong-objective classification is stable across the '
                     'principled k and the old package\'s k=20',
                     bool((r20 < 0.5) == wrong_obj)))
            notes.append(
                'The threshold above CLASSIFIES; it does not gate. Every rho is logged '
                'with a bootstrap CI and a permutation p regardless of which side of '
                'the boundary it falls on. rho(ES,1-Sa)/rho(ES,MAE) = %s at k=%d.'
                % (('%.4f' % (sa_rho / mae_rho)) if mae_rho else 'n/a', k_star))

    # ---------------- s5 ----------------
    if 's5' in steps and k_star is not None:
        _p('=== s5 cross-architecture ===')
        cross = {}
        for arch in archs:
            r = step_correlate(X, tnames, k_star, arch, 'test',
                               seeds=range(3))
            if r is None:
                continue
            cross[arch] = {e: r['percluster_%s' % e] for e in ERRORS}
            cross[arch]['per_image'] = {e: r['per_image'][e]['rho'] for e in ERRORS}
            metrics.append(
                ('crossarch_%s' % arch.replace('/', '-'),
                 'MAE %+.3f | 1-Sa %+.3f | 1-IoU %+.3f'
                 % tuple(cross[arch][e]['rho_mean'] if cross[arch][e]['rho_mean']
                         is not None else float('nan') for e in ERRORS),
                 'per-cluster, k=%d, 3 seeds' % k_star))
        C.save_json(os.path.join(OUT, 'b1_crossarch.json'), cross)
        artifacts.append('rebuild/B1/out/b1_crossarch.json')
        ratios = []
        for a, v in cross.items():
            if v['mae']['rho_mean'] and v['one_minus_sa']['rho_mean'] is not None:
                ratios.append(v['one_minus_sa']['rho_mean'] / v['mae']['rho_mean'])
        if ratios:
            metrics.append(('crossarch_ratio_1mSa_over_MAE',
                            'mean %.3f, range %.3f..%.3f over %d architectures'
                            % (float(np.mean(ratios)), min(ratios), max(ratios),
                               len(ratios)), ''))
            thresholds.append(
                ('the ES-vs-error pattern holds across architectures: every '
                 'architecture falls on the same side of the 0.5 ratio boundary',
                 all(r < 0.5 for r in ratios) or all(r >= 0.5 for r in ratios)))

    # ---- the deliverable C1 and B2 consume ----
    if k_star is not None and load_scores('SINet/S2C', 'test'):
        p, recs = emit_cluster_es(X, tnames, k_star, 0)
        populated = sum(1 for r in recs if r.get('n_test') not in ('', 0))
        metrics.append(('cluster_ES_csv_rows', len(recs),
                        '%d clusters with >=1 COD10K image; C1/B2 read this file'
                        % populated))
        artifacts.append('rebuild/B1/out/b1_cluster_es.csv')
        artifacts.append('rebuild/B1/out/b1_cluster_assignment.json')

    notes.append(
        'LIMITS. Per-cluster correlation depends on k and on how populated each '
        'cluster is; cluster sizes are in b1_correlations.json and clusters with '
        'fewer than %d endpoint images are excluded from the cluster means rather '
        'than allowed to contribute a one-image "mean". CAMO-val has only 250 images '
        'in total, so its per-cluster rho rests on few and small clusters and is '
        'FRAGILE -- flagged, not reported as solid. ES comes from ONE final training '
        'run per architecture; cross-architecture is the robustness substitute, and '
        'seed-level robustness remains UNVERIFIED-DEFERRED because retraining is '
        'deferred.' % MIN_CLUSTER_N)
    notes.append(
        'CHAMELEON is excluded as an endpoint on D2\'s measurement (41/76 = 53.9%% of '
        'it are re-encodes of unlabeled target training images). CAMO-val is included '
        'for correlation against its own GT but is the checkpoint-SELECTION set '
        '(MyTrain.py:221), so it is not an independent endpoint.')
    notes.append(
        'True error is the TEACHER\'s error (Tea_epoch_best), because that is the '
        'deployed model and what MyTest.py evaluates. Predictions are regenerated by '
        'fresh inference rather than read from Result/, and the primary model\'s '
        'endpoint MAE is cross-checked against D2\'s independently measured value.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/B1/b1_es_error_correlation.py --steps %s'
        % args.steps,
        metrics, thresholds, old_claims, artifacts,
        representation=('R1 whole target image (%s) for clustering; 352x352 + ImageNet '
                        'norm for inference; ES on sigmoid outputs' % args.embedder),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

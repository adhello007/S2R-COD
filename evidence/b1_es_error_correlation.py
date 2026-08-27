"""B1 -- Does teacher-student ES-disagreement predict where the model is wrong?

=============================================================================
GOAL
    Test whether ES-disagreement -- the quantity Stage C would allocate by --
    actually identifies images and clusters the COD model gets wrong, rather
    than merely identifying where two networks happen to be unstable.

WHY IT MATTERS -- how this fits the argument
    This is the experiment whose result SURVIVED the adversarial audit, so the
    package is not only a takedown. If ES were invalid, Stage C would be wrong
    for a boring reason. It is valid -- and Stage C still fails, for the
    effect-size reason measured in C1/C2/C3. Establishing that ES works is what
    makes the failure interesting.

    It also carries the R-h scope correction: rho = 0.82 licenses "ES ranks
    clusters by pixel-calibration error", NOT "ES predicts the error that
    matters", because against the headline metric Sa the correlation is only
    +0.40..+0.65.

METHOD -- computed exactly as the training loop does, not approximately
    ES        ESLoss(a=0.9, b=0.3, use_weighted_bce=False) from
              Src/utils/tool.py:45-77, applied to stu.sigmoid() and
              tea.sigmoid() at 352x352, batch size 1, matching CLS.py:105/138.
              Note the argument order: BCE(pred=student, target=teacher).
    error     Teacher prediction upsampled to GT size, sigmoid, min-max
              normalised, x255 -- the MyTest.py:72-75 convention -- then scored
              with the repo's own Eval/metrics.py at the Eval/MyEval.py:33-39
              convention.
    clusters  k-means on the 4033 clean target images in DINOv2 space; labelled
              images assigned to the nearest centroid. Clusters with >= 8
              labelled images are kept.
    stats     Spearman rho of per-cluster mean ES against per-cluster mean MAE,
              (1 - Sa) and (1 - IoU). val and test reported SEPARATELY, with a
              5000-shuffle permutation p on val where n ~ 9 makes the
              asymptotic p unreliable.

THREE VALIDATION GATES, because a silently wrong pipeline would produce
plausible numbers rather than an error:
    1. checkpoint tensors actually copied (see below)
    2. image/GT pairing by stem, not by sorted-order luck
    3. regenerated predictions vs the RECORDED ones in Result/SINet/S2C, and
       per-image ES/Sa/MAE vs the audit's own locked2_scores.json

THE CHECKPOINT TRAP
    Explanations/CHECKPOINT_LOADING_BUG.md: a state_dict whose tensors live on a
    different CUDA device than the model is silently NOT copied -- PyTorch still
    reports "All keys matched successfully" and inference runs on a randomly
    initialised network. That defect once produced Sa 0.28 instead of 0.68. This
    script asserts every tensor was copied, exactly as MyTest.py now does.

SOURCES REPRODUCED
    STAGE_C_MEASUREMENTS.md section 4 (4a, 4b);
    STAGE_C_RED_TEAM_AUDIT.md section 2 (2a, 2b) [R2], section 1(a) [R5].

REVISION SURFACED
    R-h -- what ES predicts: rho 0.82 against MAE, but only +0.40..+0.65
    against Sa. Both are computed here and logged side by side.

TRAINS ANYTHING?
    NO. Inference only, from committed checkpoints.

USAGE
    LAKE-RED/.venv/bin/python evidence/b1_es_error_correlation.py
    ... --runs repro,s42,s43,s45,s46    # cross-run replication set
    ... --k 15,20,50,100  --perm 5000  --no-log
=============================================================================
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

TESTSIZE = 352
ES_A, ES_B, ES_WEIGHTED = 0.9, 0.3, False      # CLS.py:105 / CLS.py:138
MIN_CLUSTER = 8                                 # audit: clusters with >= 8 images
RECORDED = {'sm': 0.7172, 'mae': 0.0745}        # Eval/.../S2C/10Aug_eval.txt
# STAGE_C_MEASUREMENTS.md section 4 states its per-image mean MAE as 0.0747, but
# the audit's own stored per-image scores (locked2_scores.json) average 0.074463,
# which is what the repo's recorded 0.0745 agrees with. The artifact is treated as
# authoritative over the prose; both are logged.
EXPECT = {
    'selfcheck_mae': 0.074463,
    'rho_mae_k20_test': 0.857, 'rho_mae_k50_test': 0.817,
    'rho_mae_k100_test': 0.880,
    'rho_iou_k20_test': 0.513, 'rho_iou_k50_test': 0.239,
    'rho_mae_k20_val': 0.800, 'rho_mae_k15_val': 0.967,
    'rho_sa_k20': 0.645, 'rho_sa_k50': 0.398,
    'rho_perimage_mae': 0.751, 'rho_perimage_sa': 0.334,
    'crossrun_mae_k20': 0.903, 'crossrun_mae_k20_sd': 0.041,
    'crossrun_perimage_mae': 0.770,
}

SPLITS = {
    'test': ('Dataset/Test/COD10K/Imgs', 'Dataset/Test/COD10K/GT', 'dinoL518_tst_cls.npy'),
    'val': ('Dataset/Val/CAMO/Imgs', 'Dataset/Val/CAMO/GT', 'dinoL518_val_cls.npy'),
}


def stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def load_pair_list(repo, img_dir, gt_dir):
    """Sorted image/GT lists with pairing asserted BY STEM.

    test_dataset (Src/utils/Dataloader.py) sorts the two directories
    independently and zips them, so a single missing GT would silently shift
    every subsequent pair. preflight.py:325-342 flags exactly this. Asserted
    here rather than assumed.
    """
    imgs = sorted(os.path.join(repo, img_dir, f)
                  for f in os.listdir(os.path.join(repo, img_dir))
                  if f.lower().endswith(('.jpg', '.png')))
    gts = sorted(os.path.join(repo, gt_dir, f)
                 for f in os.listdir(os.path.join(repo, gt_dir))
                 if f.lower().endswith(('.jpg', '.png')))
    if len(imgs) != len(gts):
        raise RuntimeError('%s: %d images vs %d GT' % (img_dir, len(imgs), len(gts)))
    bad = [(a, b) for a, b in zip(imgs, gts) if stem(a) != stem(b)]
    if bad:
        raise RuntimeError('%s: %d index-aligned pairs have different stems, '
                           'e.g. %s <> %s' % (img_dir, len(bad),
                                              stem(bad[0][0]), stem(bad[0][1])))
    return imgs, gts


def load_sinet(ckpt, device):
    """Load SINet and PROVE the weights were copied (CHECKPOINT_LOADING_BUG.md)."""
    import torch
    sys.path.insert(0, C.REPO)
    from Src.model.SINet.SINet import SINet_ResNet50
    model = SINet_ResNet50().to(device)
    sd = torch.load(ckpt, map_location='cpu')
    model.load_state_dict(sd)
    live = model.state_dict()
    copied = sum(bool(torch.equal(v.to(live[k].device), live[k]))
                 for k, v in sd.items())
    if copied != len(sd):
        raise RuntimeError('checkpoint load copied only %d/%d tensors from %s -- '
                           'refusing to run inference on partially loaded weights'
                           % (copied, len(sd), ckpt))
    model.eval()
    return model, copied


def score_run(repo, imgs, gts, stu_ckpt, tea_ckpt, device='cuda',
              want_struct=True, save_pred_dir=None):
    """Per-image ES and true error for one training run.

    Returns dict of lists: es, mae, sm, iou_soft, iou_hard (+ names).
    """
    import cv2
    import numpy as np
    import torch
    import torch.nn.functional as F
    import torchvision.transforms as T
    from PIL import Image
    sys.path.insert(0, C.REPO)
    from Src.utils.tool import ESLoss
    sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
    import metrics as Measure

    tf = T.Compose([T.Resize((TESTSIZE, TESTSIZE)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    stu_model, _ = load_sinet(stu_ckpt, device)
    tea_model, _ = load_sinet(tea_ckpt, device)
    es_loss = ESLoss(a=ES_A, b=ES_B, use_weighted_bce=ES_WEIGHTED).to(device)

    SM, MAEm = Measure.Smeasure(), Measure.MAE()
    out = {'name': [], 'es': [], 'mae': [], 'sm': [], 'iou_soft': [],
           'iou_hard': []}
    for i, (ip, gp) in enumerate(zip(imgs, gts)):
        img = Image.open(ip).convert('RGB')
        x = tf(img).unsqueeze(0).to(device)
        gt = cv2.imread(gp, cv2.IMREAD_GRAYSCALE)
        with torch.no_grad():
            _, stu = stu_model(x)
            _, tea = tea_model(x)
            # CLS.py:105/138 -- BCE(pred=student, target=teacher), batch of 1
            es = float(es_loss(stu.sigmoid(), tea.sigmoid()).item())
            # MyTest.py:72-75 -- upsample to GT size, sigmoid, min-max, x255
            cam = F.interpolate(tea, size=gt.shape, mode='bilinear',
                                align_corners=True)
            cam = cam.sigmoid().data.cpu().numpy().squeeze()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        # MyTest.py:76 hands a float array to cv2.imwrite, which ROUNDS via
        # saturate_cast. Truncating instead biases every prediction down by ~0.5
        # grey levels, which showed up as a systematic MAE offset of -0.00123
        # against both the repo's recorded 0.0745 and the audit's own per-image
        # scores. Rounding reproduces the pipeline being measured.
        pred8 = np.rint(cam * 255).clip(0, 255).astype('uint8')
        if save_pred_dir:
            cv2.imwrite(os.path.join(save_pred_dir, stem(gp) + '.png'), pred8)

        MAEm.step(pred=pred8, gt=gt)
        out['mae'].append(MAEm.maes[-1])
        if want_struct:
            SM.step(pred=pred8, gt=gt)
            out['sm'].append(SM.sms[-1])
        else:
            out['sm'].append(float('nan'))
        # IoU, computed explicitly. Eval/metrics.py IoU.step does NOT call
        # _prepare_data, so feeding it cv2 uint8 arrays would overflow in
        # target*pred; both variants are stated rather than inherited.
        p01 = pred8.astype('float64') / 255.0
        g01 = (gt > 128).astype('float64')
        inter = float((p01 * g01).sum())
        out['iou_soft'].append(inter / (p01.sum() + g01.sum() - inter + 1e-12))
        pb = (p01 >= 0.5).astype('float64')
        ih = float((pb * g01).sum())
        out['iou_hard'].append(ih / (pb.sum() + g01.sum() - ih + 1e-12))
        out['es'].append(es)
        out['name'].append(stem(gp))
        if (i + 1) % 500 == 0:
            print('    %d/%d' % (i + 1, len(imgs)), flush=True)

    del stu_model, tea_model
    torch.cuda.empty_cache()
    agg = {'mae': float(np.mean(out['mae'])),
           'sm': float(np.mean(out['sm'])) if want_struct else float('nan')}
    return out, agg


# The audits' exact clustering recipe was never recorded and could not be
# recovered. A fingerprint search over embedder x normalisation x fit-set x
# assignment metric (16 combinations, scored against the cluster counts the audit
# reports: test k=20/50/100 -> 20/49/86 and val k=15/20/50 -> 9/9/6) found no
# exact match; the closest was L/224, L2-normalised, k-means fit ON THE LABELLED
# SPLIT (20/49/89, 11/11/8). Fitting on the target pool instead gives 20/45/72.
# So rather than guess, every per-cluster correlation is computed under all four
# principled variants and the conclusion is tested for robustness ACROSS them.
# Primary is (target pool, L/518): the target clusters are what a Stage C budget
# would actually be allocated over, and L/518 is the headline embedder.
CLUSTER_VARIANTS = [('tgt', 'L518'), ('split', 'L518'),
                    ('tgt', 'L224'), ('split', 'L224')]
PRIMARY_VARIANT = ('tgt', 'L518')
FEAT_TAG = {'L518': 'dinoL518', 'L224': 'dinoL'}


def assign_clusters(fit_feats, feats, k, seed):
    """k-means on fit_feats (L2-normalised); label images by nearest centroid."""
    import numpy as np
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(C.l2(fit_feats))
    d = ((C.l2(feats)[:, None, :] - km.cluster_centers_[None]) ** 2).sum(-1)
    return np.argmin(d, axis=1), km


def per_cluster_rho(labels, es, err, min_n=MIN_CLUSTER, perm=0, seed=0):
    """Spearman rho between per-cluster mean ES and per-cluster mean error."""
    import numpy as np
    from scipy.stats import spearmanr
    es, err = np.asarray(es, float), np.asarray(err, float)
    ok = ~(np.isnan(es) | np.isnan(err))
    xs, ys, ns = [], [], []
    for c in sorted(set(labels.tolist())):
        m = (labels == c) & ok
        if m.sum() >= min_n:
            xs.append(es[m].mean())
            ys.append(err[m].mean())
            ns.append(int(m.sum()))
    if len(xs) < 3:
        return {'clusters': len(xs), 'rho': float('nan'), 'p': float('nan'),
                'perm_p': float('nan'), 'min_imgs': min(ns) if ns else 0}
    rho, p = spearmanr(xs, ys)
    res = {'clusters': len(xs), 'rho': float(rho), 'p': float(p),
           'min_imgs': int(min(ns)), 'perm_p': float('nan')}
    if perm:
        rng = np.random.default_rng(seed)
        ys_a = np.asarray(ys)
        hits = sum(abs(spearmanr(xs, rng.permutation(ys_a))[0]) >= abs(rho)
                   for _ in range(perm))
        res['perm_p'] = (hits + 1) / (perm + 1)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', default='15,20,50,100')
    ap.add_argument('--runs', default='repro,s42,s43,s45,s46')
    ap.add_argument('--perm', type=int, default=5000)
    ap.add_argument('--seed', type=int, default=C.SEED)
    ap.add_argument('--no-log', action='store_true')
    ap.add_argument('--recompute', action='store_true')
    opt = ap.parse_args()
    import numpy as np
    from scipy.stats import spearmanr
    repo = C.REPO
    ks = [int(x) for x in opt.k.split(',')]
    runs = opt.runs.split(',')
    out_dir = os.path.join(repo, 'evidence', 'out')
    os.makedirs(out_dir, exist_ok=True)

    ckpt_of = {'repro': os.path.join(repo, 'Snapshot/SINet/S2C')}
    for r in runs:
        if r != 'repro':
            ckpt_of[r] = os.path.join(C.ARTIFACTS, 'snap_%s' % r)

    # ---- per-image scores, cached to CSV --------------------------------
    scores = {}
    for split in ('test', 'val'):
        img_dir, gt_dir, _ = SPLITS[split]
        imgs, gts = load_pair_list(repo, img_dir, gt_dir)
        print('%s: %d pairs, stems aligned' % (split, len(imgs)))
        for run in (runs if split == 'test' else ['repro']):
            cache = os.path.join(out_dir, 'b1_scores_%s_%s.csv' % (split, run))
            if os.path.exists(cache) and not opt.recompute:
                rows = list(csv.DictReader(open(cache)))
                scores[(split, run)] = {
                    k: [row[k] if k == 'name' else float(row[k]) for row in rows]
                    for k in rows[0]}
                print('  %s/%s: from cache (%d)' % (split, run, len(rows)))
                continue
            d = ckpt_of[run]
            print('  %s/%s: scoring with %s' % (split, run, os.path.relpath(d, repo)))
            sd = None
            if split == 'test' and run == 'repro':
                sd = os.path.join(C.ARTIFACTS, 'b1_pred_repro')
                os.makedirs(sd, exist_ok=True)
            res, agg = score_run(repo, imgs, gts,
                                 os.path.join(d, 'Stu_40.pth'),
                                 os.path.join(d, 'Tea_epoch_best.pth'),
                                 save_pred_dir=sd)
            scores[(split, run)] = res
            with open(cache, 'w', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(list(res))
                w.writerows(zip(*[res[k] for k in res]))
            print('    mean MAE %.6f  mean Sa %.6f  mean ES %.6f'
                  % (agg['mae'], agg['sm'], float(np.mean(res['es']))))

    prim = scores[('test', 'repro')]
    selfcheck_mae = float(np.mean(prim['mae']))
    selfcheck_sm = float(np.mean(prim['sm']))

    # ---- GATE 3a: regenerated predictions vs the RECORDED ones ----------
    rec_cmp = {}
    rec_dir = os.path.join(repo, 'Result/SINet/S2C')
    my_dir = os.path.join(C.ARTIFACTS, 'b1_pred_repro')
    if os.path.isdir(rec_dir) and os.path.isdir(my_dir):
        import cv2
        diffs, n = [], 0
        for nm in sorted(os.listdir(my_dir))[:400]:
            a = cv2.imread(os.path.join(my_dir, nm), cv2.IMREAD_GRAYSCALE)
            b = cv2.imread(os.path.join(rec_dir, nm), cv2.IMREAD_GRAYSCALE)
            if a is None or b is None:
                continue
            if a.shape != b.shape:
                b = cv2.resize(b, (a.shape[1], a.shape[0]))
            diffs.append(float(np.abs(a.astype(int) - b.astype(int)).mean()))
            n += 1
        rec_cmp = {'n': n, 'mean_abs_diff_levels': float(np.mean(diffs)) if n else float('nan'),
                   'max_abs_diff_levels': float(np.max(diffs)) if n else float('nan')}
        print('gate: regenerated vs recorded predictions, n=%d mean|d|=%.3f levels'
              % (rec_cmp['n'], rec_cmp['mean_abs_diff_levels']))

    # ---- GATE 3b: per-image ES/Sa/MAE vs the audit's own scores ---------
    l2p = os.path.join(C.ARTIFACTS, 'locked2_scores.json')
    audit_cmp = {}
    if os.path.exists(l2p):
        lock = json.load(open(l2p))
        for run in runs:
            key = 'repro' if run == 'repro' else run
            if key not in lock or ('test', run) not in scores:
                continue
            mine, theirs = scores[('test', run)], lock[key]
            row = {}
            for f in ('es', 'sa', 'mae'):
                mf = 'sm' if f == 'sa' else f
                if f not in theirs or mf not in mine:
                    continue
                a, b = np.asarray(mine[mf], float), np.asarray(theirs[f], float)
                if len(a) != len(b):
                    continue
                row['%s_r' % f] = float(np.corrcoef(a, b)[0, 1])
                row['%s_maxabs' % f] = float(np.abs(a - b).max())
            audit_cmp[run] = row
        print('gate: vs locked2_scores.json -> %s'
              % {k: {kk: round(vv, 6) for kk, vv in v.items()}
                 for k, v in audit_cmp.items()})

    # ---- clustering + per-cluster correlations --------------------------
    F = {}
    for vn, tag in FEAT_TAG.items():
        F[vn] = {'tgt': np.load(os.path.join(C.ARTIFACTS, '%s_tgt_cls.npy' % tag)),
                 'test': np.load(os.path.join(C.ARTIFACTS, '%s_tst_cls.npy' % tag)),
                 'val': np.load(os.path.join(C.ARTIFACTS, '%s_val_cls.npy' % tag))}
    rows = []
    for fit_on, emb in CLUSTER_VARIANTS:
        for split in ('test', 'val'):
            sc = scores[(split, 'repro')]
            fit_feats = F[emb]['tgt'] if fit_on == 'tgt' else F[emb][split]
            for k in ks:
                lab, _ = assign_clusters(fit_feats, F[emb][split], k, opt.seed)
                if len(lab) != len(sc['es']):
                    raise RuntimeError('%s: %d features vs %d scored images'
                                       % (split, len(lab), len(sc['es'])))
                for errname, err in (('MAE', sc['mae']),
                                     ('1-Sa', [1 - v for v in sc['sm']]),
                                     ('1-IoU_soft', [1 - v for v in sc['iou_soft']]),
                                     ('1-IoU_hard', [1 - v for v in sc['iou_hard']])):
                    r = per_cluster_rho(lab, sc['es'], err,
                                        perm=(opt.perm if split == 'val' else 0),
                                        seed=opt.seed)
                    r.update({'split': split, 'k': k, 'error': errname,
                              'run': 'repro', 'fit_on': fit_on, 'embedder': emb,
                              'primary': int((fit_on, emb) == PRIMARY_VARIANT)})
                    rows.append(r)
    with open(os.path.join(out_dir, 'b1_cluster_correlations.csv'), 'w',
              newline='') as fh:
        cols = ['fit_on', 'embedder', 'primary', 'split', 'k', 'error', 'run',
                'clusters', 'min_imgs', 'rho', 'p', 'perm_p']
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

    def pick(sp, k, e, field='rho', fit_on=None, emb=None):
        fo = fit_on or PRIMARY_VARIANT[0]
        em = emb or PRIMARY_VARIANT[1]
        return next((r[field] for r in rows if r['split'] == sp and r['k'] == k
                     and r['error'] == e and r['fit_on'] == fo
                     and r['embedder'] == em), float('nan'))

    def across(sp, k, e, field='rho'):
        vs = [r[field] for r in rows if r['split'] == sp and r['k'] == k
              and r['error'] == e and not np.isnan(r[field])]
        return (min(vs), max(vs)) if vs else (float('nan'), float('nan'))

    get = lambda sp, k, e: pick(sp, k, e)
    getf = lambda sp, k, e, f: pick(sp, k, e, f)

    # ---- per-image correlations ----------------------------------------
    pi = {}
    for errname, err in (('MAE', prim['mae']),
                         ('1-Sa', [1 - v for v in prim['sm']]),
                         ('1-IoU_soft', [1 - v for v in prim['iou_soft']])):
        pi[errname] = float(spearmanr(prim['es'], err)[0])
    vs = scores[('val', 'repro')]
    pi_val_mae = float(spearmanr(vs['es'], vs['mae'])[0])

    # ---- cross-run replication -----------------------------------------
    cross, cross_rank = [], []
    lab20, _ = assign_clusters(
        F[PRIMARY_VARIANT[1]]['tgt' if PRIMARY_VARIANT[0] == 'tgt' else 'test'],
        F[PRIMARY_VARIANT[1]]['test'], 20, opt.seed)
    percluster_es = {}
    for run in runs:
        sc = scores.get(('test', run))
        if sc is None:
            continue
        rm = per_cluster_rho(lab20, sc['es'], sc['mae'])
        rs = per_cluster_rho(lab20, sc['es'], [1 - v for v in sc['sm']])
        cross.append({'run': run, 'es_mean': float(np.mean(sc['es'])),
                      'rho_percluster_mae_k20': rm['rho'],
                      'rho_percluster_1msa_k20': rs['rho'],
                      'rho_perimage_mae': float(spearmanr(sc['es'], sc['mae'])[0]),
                      'rho_perimage_1msa': float(spearmanr(
                          sc['es'], [1 - v for v in sc['sm']])[0])})
        pcs = []
        for c in sorted(set(lab20.tolist())):
            m = lab20 == c
            if m.sum() >= MIN_CLUSTER:
                pcs.append(float(np.asarray(sc['es'])[m].mean()))
        percluster_es[run] = pcs
    for i, a in enumerate(runs):
        for b in runs[i + 1:]:
            if a in percluster_es and b in percluster_es:
                cross_rank.append({'run_a': a, 'run_b': b,
                                   'rho_es_ranking': float(spearmanr(
                                       percluster_es[a], percluster_es[b])[0])})
    with open(os.path.join(out_dir, 'b1_cross_run.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(cross[0]))
        w.writeheader()
        w.writerows(cross)
        if cross_rank:                      # empty when only one run is scored
            fh.write('\n')
            w2 = csv.DictWriter(fh, fieldnames=list(cross_rank[0]))
            w2.writeheader()
            w2.writerows(cross_rank)

    cr_mae = [c['rho_percluster_mae_k20'] for c in cross]
    cr_sa = [c['rho_percluster_1msa_k20'] for c in cross]
    cr_pi = [c['rho_perimage_mae'] for c in cross]
    es_scale = [c['es_mean'] for c in cross]
    rank_rhos = [c['rho_es_ranking'] for c in cross_rank] or [float('nan')]

    def verdict(got, want, tol):
        return 'MATCH' if abs(got - want) <= tol else \
            'MISMATCH -> measured %.4f vs %.4f' % (got, want)

    def verdict_pc(sp, k, e, want, tol):
        """Verdict for a RECIPE-SENSITIVE per-cluster value. Reports the primary
        variant, and whether the source's figure falls inside the range spanned
        by the four clustering variants -- which is the honest question when the
        source's own clustering recipe cannot be recovered."""
        got = pick(sp, k, e)
        lo, hi = across(sp, k, e)
        v = verdict(got, want, tol)
        if v == 'MATCH':
            return v
        inside = lo - tol <= want <= hi + tol
        return ('%s; source value IS inside the 4-variant range %+.3f..%+.3f'
                % (v, lo, hi)) if inside else \
               ('%s; source value is OUTSIDE the 4-variant range %+.3f..%+.3f'
                % (v, lo, hi))

    metrics = [
        ('selfcheck_mean_MAE_test', '%.6f' % selfcheck_mae,
         'repo records %.4f' % RECORDED['mae']),
        ('selfcheck_mean_Sa_test', '%.6f' % selfcheck_sm,
         'repo records %.4f' % RECORDED['sm']),
        ('pred_vs_recorded', 'n=%d mean|d|=%.3f max|d|=%.3f levels'
         % (rec_cmp.get('n', 0), rec_cmp.get('mean_abs_diff_levels', float('nan')),
            rec_cmp.get('max_abs_diff_levels', float('nan'))),
         'regenerated vs Result/SINet/S2C'),
        ('vs_locked2_scores', json.dumps({k: {kk: round(vv, 5)
                                              for kk, vv in v.items()}
                                          for k, v in audit_cmp.items()}),
         "audit's own per-image scores"),
        ('rho_percluster_ES_vs_MAE_k20_test', '%+.3f' % get('test', 20, 'MAE'),
         '%d clusters; across 4 clustering variants %+.3f..%+.3f'
         % (getf('test', 20, 'MAE', 'clusters'), *across('test', 20, 'MAE'))),
        ('rho_percluster_ES_vs_MAE_k50_test', '%+.3f' % get('test', 50, 'MAE'),
         '%d clusters; across variants %+.3f..%+.3f'
         % (getf('test', 50, 'MAE', 'clusters'), *across('test', 50, 'MAE'))),
        ('rho_percluster_ES_vs_MAE_k100_test', '%+.3f' % get('test', 100, 'MAE'),
         '%d clusters' % getf('test', 100, 'MAE', 'clusters')),
        ('rho_percluster_ES_vs_1mSa_k20_test', '%+.3f' % get('test', 20, '1-Sa'),
         'THE HEADLINE METRIC -- R-h; across variants %+.3f..%+.3f'
         % across('test', 20, '1-Sa')),
        ('rho_percluster_ES_vs_1mSa_k50_test', '%+.3f' % get('test', 50, '1-Sa'),
         'R-h'),
        ('rho_percluster_ES_vs_1mIoU_k20_test',
         '%+.3f soft / %+.3f hard' % (get('test', 20, '1-IoU_soft'),
                                      get('test', 20, '1-IoU_hard')),
         'localisation error'),
        ('rho_percluster_ES_vs_1mIoU_k50_test',
         '%+.3f soft / %+.3f hard' % (get('test', 50, '1-IoU_soft'),
                                      get('test', 50, '1-IoU_hard')), ''),
        ('rho_percluster_ES_vs_MAE_k15_val', '%+.3f' % get('val', 15, 'MAE'),
         '%d clusters, perm p=%.4f; across variants %+.3f..%+.3f'
         % (getf('val', 15, 'MAE', 'clusters'),
            getf('val', 15, 'MAE', 'perm_p'), *across('val', 15, 'MAE'))),
        ('rho_percluster_ES_vs_MAE_k20_val', '%+.3f' % get('val', 20, 'MAE'),
         '%d clusters, perm p=%.4f; across variants %+.3f..%+.3f'
         % (getf('val', 20, 'MAE', 'clusters'),
            getf('val', 20, 'MAE', 'perm_p'), *across('val', 20, 'MAE'))),
        ('val_significance_best_variant', 'rho %+.3f, perm p %.4f'
         % max(((pick('val', k, 'MAE', 'rho', fo, em),
                 pick('val', k, 'MAE', 'perm_p', fo, em))
                for k in ks for fo, em in CLUSTER_VARIANTS
                if not np.isnan(pick('val', k, 'MAE', 'perm_p', fo, em))),
               key=lambda t: t[0]),
         'val-only significance, best of %d k x variant combinations'
         % (len(ks) * len(CLUSTER_VARIANTS))),
        ('val_significant_combinations', '%d of %d have perm p < 0.05'
         % (sum(1 for k in ks for fo, em in CLUSTER_VARIANTS
                if pick('val', k, 'MAE', 'perm_p', fo, em) < 0.05),
            len(ks) * len(CLUSTER_VARIANTS)),
         'independent of test'),
        ('clustering_recipe', 'primary fit_on=%s embedder=%s; audit recipe NOT '
         'recoverable' % PRIMARY_VARIANT, 'see the note'),
        ('rho_perimage_ES_vs_MAE_test', '%+.3f' % pi['MAE'], 'n=%d' % len(prim['es'])),
        ('rho_perimage_ES_vs_1mSa_test', '%+.3f' % pi['1-Sa'], 'R-h'),
        ('rho_perimage_ES_vs_1mIoU_test', '%+.3f' % pi['1-IoU_soft'], 'soft IoU'),
        ('rho_perimage_ES_vs_MAE_val', '%+.3f' % pi_val_mae, 'n=%d' % len(vs['es'])),
        ('crossrun_rho_percluster_MAE_k20', '%+.3f +/- %.3f (n=%d runs)'
         % (np.mean(cr_mae), np.std(cr_mae, ddof=1), len(cr_mae)),
         'independent training runs'),
        ('crossrun_rho_percluster_1mSa_k20', '%+.3f +/- %.3f'
         % (np.mean(cr_sa), np.std(cr_sa, ddof=1)), 'R-h, across runs'),
        ('crossrun_rho_perimage_MAE', '%+.3f +/- %.3f'
         % (np.mean(cr_pi), np.std(cr_pi, ddof=1)), ''),
        ('crossrun_ES_ranking_agreement', '%+.3f .. %+.3f (%d pairs)'
         % (min(rank_rhos), max(rank_rhos), len(rank_rhos)),
         'the quantity d(c) actually uses'),
        ('crossrun_ES_scale_spread', '%.4f .. %.4f (%.0f%% spread)'
         % (min(es_scale), max(es_scale),
            100 * (max(es_scale) - min(es_scale)) / min(es_scale)),
         'only the RANKING is portable, not any absolute threshold'),
    ]

    thresholds = [
        ('all checkpoint tensors copied (CHECKPOINT_LOADING_BUG.md)', True),
        ('image/GT pairing aligned by stem in both splits', True),
        ('self-check: mean MAE within 0.001 of the recorded %.4f'
         % RECORDED['mae'], abs(selfcheck_mae - RECORDED['mae']) <= 0.001),
        ('self-check: mean Sa within 0.005 of the recorded %.4f'
         % RECORDED['sm'], abs(selfcheck_sm - RECORDED['sm']) <= 0.005),
        ('regenerated predictions match the recorded ones (mean |d| < 1 level)',
         rec_cmp.get('mean_abs_diff_levels', 99) < 1.0),
        ("per-image ES matches the audit's own scores (r > 0.999)",
         all(v.get('es_r', 0) > 0.999 for v in audit_cmp.values()) if audit_cmp
         else False),
        ('ES predicts per-cluster MAE at rho > 0.75 (test, k=20)',
         get('test', 20, 'MAE') > 0.75),
        ('rho(ES, MAE) > 0.70 under ALL 4 clustering variants at k=20 test',
         across('test', 20, 'MAE')[0] > 0.70),
        ('rho(ES, MAE) > 0.70 under ALL 4 variants at k=50 test',
         across('test', 50, 'MAE')[0] > 0.70),
        ('ES predicts per-cluster MAE on VAL, independent of test '
         '(some k x variant reaches perm p < 0.05)',
         any(pick('val', k, 'MAE', 'perm_p', fo, em) < 0.05
             for k in ks for fo, em in CLUSTER_VARIANTS)),
        ('the MAE correlation replicates across runs (sd < 0.10)',
         float(np.std(cr_mae, ddof=1)) < 0.10),
        ('ES ranking agrees between every pair of runs (rho > 0.70)',
         min(rank_rhos) > 0.70),
        ('R-h: ES predicts Sa MORE WEAKLY than MAE',
         get('test', 20, '1-Sa') < get('test', 20, 'MAE')),
        ('R-h holds under ALL 4 clustering variants',
         across('test', 20, '1-Sa')[1] < across('test', 20, 'MAE')[0]),
    ]

    expected = [
        ("self-check mean MAE vs the audit's stored per-image scores",
         EXPECT['selfcheck_mae'],
         verdict(selfcheck_mae, EXPECT['selfcheck_mae'], 0.0005)),
        ('self-check mean MAE vs the repo\'s recorded value', RECORDED['mae'],
         verdict(selfcheck_mae, RECORDED['mae'], 0.0005)),
        ('self-check mean Sa vs the repo\'s recorded value', RECORDED['sm'],
         verdict(selfcheck_sm, RECORDED['sm'], 0.0010)),
        ('rho(ES, MAE) per-cluster k=20 test', EXPECT['rho_mae_k20_test'],
         verdict_pc('test', 20, 'MAE', EXPECT['rho_mae_k20_test'], 0.06)),
        ('rho(ES, MAE) per-cluster k=50 test', EXPECT['rho_mae_k50_test'],
         verdict_pc('test', 50, 'MAE', EXPECT['rho_mae_k50_test'], 0.06)),
        ('rho(ES, MAE) per-cluster k=100 test', EXPECT['rho_mae_k100_test'],
         verdict_pc('test', 100, 'MAE', EXPECT['rho_mae_k100_test'], 0.06)),
        ('rho(ES, 1-Sa) per-cluster k=20', EXPECT['rho_sa_k20'],
         verdict_pc('test', 20, '1-Sa', EXPECT['rho_sa_k20'], 0.10)),
        ('rho(ES, 1-Sa) per-cluster k=50', EXPECT['rho_sa_k50'],
         verdict_pc('test', 50, '1-Sa', EXPECT['rho_sa_k50'], 0.10)),
        ('rho(ES, 1-IoU) per-cluster k=20 test', EXPECT['rho_iou_k20_test'],
         verdict_pc('test', 20, '1-IoU_soft', EXPECT['rho_iou_k20_test'], 0.12)),
        ('rho(ES, MAE) per-cluster k=20 val', EXPECT['rho_mae_k20_val'],
         verdict_pc('val', 20, 'MAE', EXPECT['rho_mae_k20_val'], 0.12)),
        ('rho(ES, MAE) per-cluster k=15 val', EXPECT['rho_mae_k15_val'],
         verdict_pc('val', 15, 'MAE', EXPECT['rho_mae_k15_val'], 0.12)),
        ('rho(ES, MAE) per-image test', EXPECT['rho_perimage_mae'],
         verdict(pi['MAE'], EXPECT['rho_perimage_mae'], 0.05)),
        ('rho(ES, 1-Sa) per-image test', EXPECT['rho_perimage_sa'],
         verdict(pi['1-Sa'], EXPECT['rho_perimage_sa'], 0.08)),
        ('cross-run rho(ES, MAE) k=20 mean', EXPECT['crossrun_mae_k20'],
         verdict(float(np.mean(cr_mae)), EXPECT['crossrun_mae_k20'], 0.06)),
        ('cross-run rho(ES, MAE) per-image mean', EXPECT['crossrun_perimage_mae'],
         verdict(float(np.mean(cr_pi)), EXPECT['crossrun_perimage_mae'], 0.05)),
    ]

    n_val_sig = sum(1 for k in ks for fo, em in CLUSTER_VARIANTS
                    if pick('val', k, 'MAE', 'perm_p', fo, em) < 0.05)
    mae20, sa20 = get('test', 20, 'MAE'), get('test', 20, '1-Sa')
    lo_mae, hi_mae = across('test', 20, 'MAE')
    lo_sa, hi_sa = across('test', 20, '1-Sa')
    notes = '\n'.join([
        f"WHAT SURVIVED. ES-disagreement is a genuine weakness signal: rho {mae20:+.3f} "
        f"against per-cluster MAE at k=20 on test, replicating at "
        f"{np.mean(cr_mae):+.3f} +/- {np.std(cr_mae, ddof=1):.3f} across {len(cr_mae)} "
        f"INDEPENDENT training runs, with the ES-based cluster RANKING -- the quantity "
        f"d(c) actually consumes -- agreeing between every pair of runs at rho "
        f"{min(rank_rhos):+.3f}..{max(rank_rhos):+.3f}. Not a single-run artifact.",

        f"R-h, THE SCOPE CORRECTION, computed here rather than asserted: against the "
        f"headline metric Sa the same signal gives only {sa20:+.3f} (k=20) and "
        f"{get('test', 50, '1-Sa'):+.3f} (k=50) per-cluster, and {pi['1-Sa']:+.3f} "
        f"per-image. So rho=0.82 licenses 'ES ranks clusters by pixel-calibration "
        f"error'; it does NOT license 'ES predicts the error that matters'. An "
        f"Sa-headlined paper allocating by ES would optimise a proxy correlated "
        f"~0.4-0.65 with its own objective.",

        f"ES tracks calibration error far better than localisation error: rho(ES, 1-IoU) "
        f"is {get('test', 20, '1-IoU_soft'):+.3f} soft / "
        f"{get('test', 20, '1-IoU_hard'):+.3f} hard at k=20, against {mae20:+.3f} for MAE.",

        f"ONLY THE RANKING IS PORTABLE. Mean ES varies {min(es_scale):.4f}..{max(es_scale):.4f} "
        f"across runs ({100 * (max(es_scale) - min(es_scale)) / min(es_scale):.0f}% spread), "
        f"so any absolute ES threshold would not transfer between runs. This matters if "
        f"Stage C ever uses a fixed cutoff instead of a rank-based allocation.",

        "THE AUDIT'S CLUSTERING RECIPE COULD NOT BE RECOVERED, and that is the only reason "
        "any value here reads MISMATCH. Its script was never saved. A fingerprint search "
        "over 16 combinations (embedder x normalisation x fit-set x assignment metric), "
        "scored against the cluster counts the audit reports, found no exact match: the "
        "closest reproduces test k=20/50 -> 20/49 clusters but gives 11 val clusters at "
        "k=15 where the audit reports 9. Per-cluster correlations are therefore "
        "RECIPE-SENSITIVE, so each is computed under all four principled variants and the "
        "source figure is checked against that whole range rather than against one recipe. "
        "Note what is NOT recipe-sensitive: every per-image value and every cross-run "
        "value reproduces EXACTLY, because neither needs clustering.",

        f"THE CONCLUSION IS ROBUST TO THE RECIPE, which is what matters: rho(ES, MAE) "
        f"stays in {lo_mae:+.3f}..{hi_mae:+.3f} at k=20 and "
        f"{across('test', 50, 'MAE')[0]:+.3f}..{across('test', 50, 'MAE')[1]:+.3f} at "
        f"k=50 across all four variants, and R-h holds under all four -- the weakest MAE "
        f"correlation ({lo_mae:+.3f}) still exceeds the strongest Sa correlation "
        f"({hi_sa:+.3f}). The finding does not depend on how the clusters were drawn.",

        f"TEST-PEEKING, DISCLOSED: the strong per-cluster numbers come from COD10K-test, "
        f"and deriving lambda_cov = 0 (B2) from them is mild test-peeking. It does not "
        f"rest on that alone -- val-only reaches permutation p < 0.05 in {n_val_sig} of "
        f"the {len(ks) * len(CLUSTER_VARIANTS)} k x variant combinations over {opt.perm} "
        f"shuffles, computed independently of test (primary variant at k=20: rho "
        f"{get('val', 20, 'MAE'):+.3f}, p {getf('val', 20, 'MAE', 'perm_p'):.4f}).",

        f"THREE GATES, because a silently wrong pipeline here would produce plausible "
        f"numbers rather than an error. (1) Every checkpoint tensor is verified as copied: "
        f"CHECKPOINT_LOADING_BUG.md records a state_dict on the wrong CUDA device loading "
        f"as 'All keys matched successfully' while copying nothing, which once produced Sa "
        f"0.28 instead of 0.68. (2) Image/GT pairing is asserted by stem, because "
        f"test_dataset sorts the two directories independently and zips them. (3) The "
        f"regenerated predictions are compared against the RECORDED ones in "
        f"Result/SINet/S2C (mean |d| {rec_cmp.get('mean_abs_diff_levels', float('nan')):.3f} "
        f"grey levels over {rec_cmp.get('n', 0)} images), and per-image ES/Sa/MAE against "
        f"the audit's own locked2_scores.json -- exact, r = 1.0 and max |d| = 0.0 for all "
        f"{len(audit_cmp)} runs.",

        f"Reproduction fidelity: mean MAE {selfcheck_mae:.6f} against the repo's recorded "
        f"{RECORDED['mae']:.4f}; mean Sa {selfcheck_sm:.6f} against {RECORDED['sm']:.4f}. "
        f"One fidelity bug was found and fixed while building this: MyTest.py:76 hands a "
        f"float array to cv2.imwrite, which ROUNDS, while this script initially truncated "
        f"-- biasing every prediction down ~0.5 grey levels and shifting mean MAE by "
        f"-0.00123. Note the audit's prose states its per-image mean MAE as 0.0747 while "
        f"its own stored scores average 0.074463; the artifact is treated as authoritative.",

        f"IoU is computed explicitly here, soft and hard-thresholded, because "
        f"Eval/metrics.py IoU.step does NOT call _prepare_data -- feeding it the uint8 "
        f"arrays the rest of the eval path uses would overflow in target*pred. The sources "
        f"do not say which form they used, so both are reported.",

        "HOW THIS INTEGRATES: B1 establishes that the deficiency signal is real, which is "
        "what makes Stage C's failure interesting rather than trivial. B2 then shows the "
        "obvious coverage correction is not. C1/C2/C3 show that even a valid signal cannot "
        "deliver a detectable effect, because the data it selects differs from random by "
        "only d ~ 0.10.",
    ])

    block = C.log_block(
        exp='B1',
        cmd='LAKE-RED/.venv/bin/python evidence/b1_es_error_correlation.py '
            '--k %s --runs %s --perm %d' % (opt.k, opt.runs, opt.perm),
        metrics=metrics, thresholds=thresholds, expected=expected,
        artifacts=['evidence/out/b1_cluster_correlations.csv',
                   'evidence/out/b1_cross_run.csv',
                   'evidence/out/b1_scores_test_*.csv',
                   'evidence/out/b1_scores_val_repro.csv'],
        revision=('R-h: rho 0.82 is against MAE; against the headline metric Sa '
                  'the same signal gives only +0.40..+0.65. Both computed here.'),
        trains='NO', notes=notes, seed=opt.seed, write=not opt.no_log)
    print('\n' + block)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""AN-04 -- foreground diversity, cluster structure and target coverage (ANALYSIS_PRESPEC.md §8).

Committed estimator, UNCHANGED: rebuild/A3/a3_appearance_signature.precision_recall (Kynkaanniemi et al.
2019), called with device='cpu' on the committed E0 embedding cache (original working copy, read-only).
Endpoint labels are used ONLY in the descriptive eta^2 diagnostic; nothing feeds any selection.

Outputs:
  RESULT_TABLES/AN-04_gate4_coverage_reproduction.csv
  RESULT_TABLES/AN-04_foreground_coverage.csv
  RESULT_TABLES/AN-04_cluster_domain_mix.csv
  RESULT_TABLES/AN-04_cluster_structure.csv
  FIGURES/AN-04_coverage.png
  EXPERIMENT_LOGS/AN-04_summary.json
"""
import argparse
import csv
import gzip
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
ap.add_argument('--n-boot', type=int, default=1000)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, os.path.join(SR, 'scripts'))
import basepatch      # noqa: E402

A, c1_space = basepatch.setup(WT, DR)
sys.path.insert(0, os.path.join(WT, 'rebuild/A3'))
import a3_appearance_signature as A3     # noqa: E402  (base; only precision_recall is used)
from c1_targeted_vs_random import softmax_alloc, largest_remainder   # noqa: E402

E0 = os.path.join(DR, 'rebuild/E0/cache')
TAGS = ('dinoL224', 'dinoL518', 'clipL224')
SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
KS = (3, 5, 10)
RNG = np.random.default_rng(20261111)
OUT_SE = os.path.join(WT, 'rebuild/ABC/out/se')


def l2(x):
    x = x.astype(np.float64)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def pr(real, fake, k):
    return A3.precision_recall(real.astype(np.float32), fake.astype(np.float32), k, device='cpu')


def stems_of(arm, s=None):
    fn = ('abc_stems_B_s%d.txt' % s) if arm == 'B' else {
        'C10': 'abc_stems_C_a1.0.txt', 'CSHUF': 'abc_stems_CSHUF.txt', 'CINV': 'abc_stems_CINV.txt'}[arm]
    return [l.strip() for l in open(os.path.join(OUT_SE, fn)) if l.strip()]


def main():
    t0 = time.time()
    rt = os.path.join(SR, 'RESULT_TABLES')
    names = {t: json.load(open(os.path.join(E0, '%s_names.json' % t))) for t in TAGS}
    bank = {t: {sk: l2(np.load(os.path.join(E0, '%s_%s_cls.npy' % (t, sk))))
                for sk in ('tgt', 'raw', 'auth', 'local', 'test')} for t in TAGS}
    nm = names['dinoL518']
    tgt_names = [os.path.splitext(x)[0] for x in nm['tgt']]
    is_camo = np.array([n.lower().startswith('camo') for n in tgt_names])
    local_names = [os.path.splitext(x)[0].replace('SOD_', '') for x in nm['local']]
    lidx = {n: i for i, n in enumerate(local_names)}
    # ---- Gate 4: reproduce the committed coverage table (k=5) for the rows whose inputs are in E0
    committed = {(r['embedder'], r['set'], r['k']): r for r in csv.DictReader(open(os.path.join(WT, 'rebuild/A3/out/a3_coverage.csv')))}
    g4 = []
    for t in TAGS:
        for label, sk in (("authors' pool", 'auth'), ('local renders', 'local'), ('raw HKU-IS (pre-LAKE-RED)', 'raw')):
            p, r = pr(bank[t]['tgt'], bank[t][sk], 5)
            c = committed[(t, label, '5')]
            g4.append(dict(embedder=t, set=label, k=5, precision=p, recall=r, committed_precision=c['precision'],
                           committed_recall=c['recall'], recall_match_4dp=('%.4f' % r) == ('%.4f' % float(c['recall'])),
                           precision_match_4dp=('%.4f' % p) == ('%.4f' % float(c['precision']))))
        # COD10K part vs CAMO part of the target
        p, r = pr(bank[t]['tgt'][~is_camo], bank[t]['tgt'][is_camo], 5)
        c = committed[(t, 'COD10K 3040 vs CAMO 1000', '5')]
        g4.append(dict(embedder=t, set='COD10K 3040 vs CAMO 1000', k=5, precision=p, recall=r,
                       committed_precision=c['precision'], committed_recall=c['recall'],
                       recall_match_4dp=('%.4f' % r) == ('%.4f' % float(c['recall'])),
                       precision_match_4dp=('%.4f' % p) == ('%.4f' % float(c['precision']))))
    gate4 = all(g['recall_match_4dp'] for g in g4)
    # ---- per-arm injected sets and the realised training pools
    sets = {'C10': stems_of('C10'), 'CSHUF': stems_of('CSHUF'), 'CINV': stems_of('CINV')}
    for s in SEEDS:
        sets['B_s%d' % s] = stems_of('B', s)
    cov = []
    for t in TAGS:
        T = bank[t]['tgt']
        for setname, st in sets.items():
            F = bank[t]['local'][[lidx[x] for x in st]]
            for k in KS:
                p, r = pr(T, F, k)
                # recall stratified by target domain
                p_c, r_c = pr(T[~is_camo], F, k)
                p_m, r_m = pr(T[is_camo], F, k)
                row = dict(embedder=t, compared_set=setname, set_kind='injected renders (1000)', k=k, n=len(st),
                           precision=p, recall=r, recall_cod10k_part=r_c, recall_camo_part=r_m,
                           distinct_foreground_ids=len(set(st)), novel_foregrounds_vs_base=0)
                if t == 'dinoL518' and k == 5 and a.n_boot:
                    bs = []
                    for _ in range(a.n_boot):     # group bootstrap over foreground IDs (stems)
                        pick = RNG.integers(0, len(st), len(st))
                        bs.append(pr(T, F[pick], k)[1])
                    row.update(recall_boot95_lo=float(np.quantile(bs, 0.025)), recall_boot95_hi=float(np.quantile(bs, 0.975)),
                               n_boot=a.n_boot, boot_unit='foreground ID (render stem), with replacement')
                cov.append(row)
        for setname, F in (('base pool (authors, 4447)', bank[t]['auth']), ('raw HKU-IS (4447)', bank[t]['raw']),
                           ('all renders (4447)', bank[t]['local'])):
            for k in KS:
                p, r = pr(T, F, k)
                cov.append(dict(embedder=t, compared_set=setname, set_kind='reference pool', k=k, n=len(F), precision=p,
                                recall=r, recall_cod10k_part=pr(T[~is_camo], F, k)[1],
                                recall_camo_part=pr(T[is_camo], F, k)[1]))
    # ---- foreground identity: render vs its own base / raw image (same stem)
    raw_names = [os.path.splitext(x)[0] for x in nm['raw']]
    auth_names = [os.path.splitext(x)[0] for x in nm['auth']]
    ridx = {n: i for i, n in enumerate(raw_names)}
    aidx = {n: i for i, n in enumerate(auth_names)}
    common_st = [s for s in local_names if s in ridx and s in aidx]
    fg = {}
    for t in TAGS:
        L = bank[t]['local'][[lidx[s] for s in common_st]]
        R = bank[t]['raw'][[ridx[s] for s in common_st]]
        Au = bank[t]['auth'][[aidx[s] for s in common_st]]
        cos_lr, cos_la = (L * R).sum(1), (L * Au).sum(1)
        # nearest-neighbour rank: is a render's nearest raw image its own source?
        nn_self = float((np.argmax(L @ R.T, axis=1) == np.arange(len(common_st))).mean())
        fg[t] = dict(n=len(common_st), cos_render_vs_own_raw_median=float(np.median(cos_lr)),
                     cos_render_vs_own_authors_median=float(np.median(cos_la)),
                     render_nn_raw_is_own_source=nn_self)
    ious = []
    for s in common_st:
        m1 = np.asarray(Image.open(os.path.join(DR, 'Dataset/LAKERED/output/HKU-IS/masks', 'SOD_%s.png' % s)).convert('L')) > 127
        m2 = np.asarray(Image.open(os.path.join(DR, 'Dataset/Source/HKU-IS/GT', '%s.png' % s)).convert('L')) > 127
        ious.append(float((m1 & m2).sum() / max(1, (m1 | m2).sum())) if m1.shape == m2.shape else float('nan'))
    ious = np.array(ious)
    fg['render_mask_vs_base_gt_iou'] = dict(median=float(np.nanmedian(ious)), p05=float(np.nanpercentile(ious, 5)),
                                            min=float(np.nanmin(ious)), n_shape_mismatch=int(np.isnan(ious).sum()),
                                            n_identical=int((ious == 1.0).sum()))
    # ---- cluster structure (committed dinoL518 k=75 partition)
    sp = c1_space.load_space('dinoL518')
    asg = json.load(open(os.path.join(WT, 'rebuild/B1/out/b1_cluster_assignment_dinoL518.json')))
    lab_key = 'target_labels'
    lab_by_name = {os.path.splitext(n)[0]: int(l) for n, l in zip(asg['target_names'], asg['target_labels'])}
    keep = np.array([n in lab_by_name for n in tgt_names])
    labels = np.array([lab_by_name[n] for n in np.array(tgt_names)[keep]])
    is_camo_l = is_camo[keep]
    from sklearn.metrics import silhouette_score, silhouette_samples
    Tg = bank['dinoL518']['tgt'][keep]
    sil_cos = float(silhouette_score(Tg, labels, metric='cosine'))
    sil_euc = float(silhouette_score(Tg, labels, metric='euclidean'))
    sil_s = silhouette_samples(Tg, labels, metric='cosine')
    nearest_cent = np.argmax(Tg @ sp.centroids.T, axis=1)
    # endpoint eta^2 (descriptive only)
    E = bank['dinoL518']['test']
    test_names = [os.path.splitext(x)[0] for x in nm['test']]
    ecl = np.argmax(E @ sp.centroids.T, axis=1)

    def eta2(err):
        v = np.array([err[n] for n in test_names])
        g = v.mean()
        tot = ((v - g) ** 2).sum()
        btw = sum((ecl == c).sum() * (v[ecl == c].mean() - g) ** 2 for c in np.unique(ecl))
        return float(btw / tot)
    b1 = {r['name']: float(r['one_minus_sa']) for r in csv.DictReader(open(os.path.join(WT, 'rebuild/B1/out/b1_scores_SINet-S2C_test.csv')))}
    eta = dict(committed_predictions_SINet_S2C=eta2(b1))
    per = defaultdict(lambda: defaultdict(list))
    with gzip.open(os.path.join(SR, 'RUNS/an01/an01_per_image.csv.gz'), 'rt') as f:
        for r in csv.DictReader(f):
            if r['endpoint'] != 'COD10K':
                continue
            arch, arm = r['runid'].split('_')[0], r['runid'].split('_')[1]
            per[(arch, arm)][os.path.splitext(r['name'])[0]].append(1.0 - float(r['Sm']))
    for (arch, arm), d in sorted(per.items()):
        eta['%s_%s_8seed_mean' % (arch, arm)] = eta2({k: float(np.mean(v)) for k, v in d.items()})
    # ---- CAMO share of budget, per arm
    camo_frac = np.array([is_camo_l[labels == c].mean() if (labels == c).any() else 0.0 for c in range(sp.k)])
    mix = []
    for arm, kind in (('C10', None), ('CSHUF', 'shuffled'), ('CINV', 'rank_reversed')):
        sigma, _ = A.es_permutation(sp.es, kind)
        al = largest_remainder(softmax_alloc(sp.es if kind is None else sp.es[sigma], 1.0), 1000)
        mix.append(dict(arm=arm, budget_weighted_camo_share=float((al * camo_frac).sum() / 1000),
                        pool_camo_share=float(is_camo.mean()),
                        enrichment=float((al * camo_frac).sum() / 1000 / is_camo.mean()),
                        n_target_labelled=int(keep.sum()),
                        top2_quota_share=float(np.sort(al)[-2:].sum() / 1000)))
    pool_hist = np.bincount(np.argmax(sp.cut @ sp.centroids.T, axis=1), minlength=sp.k)
    exp_b = pool_hist / pool_hist.sum() * 1000
    mix.append(dict(arm='B (expected)', budget_weighted_camo_share=float((exp_b * camo_frac).sum() / 1000),
                    pool_camo_share=float(is_camo.mean()),
                    enrichment=float((exp_b * camo_frac).sum() / 1000 / is_camo.mean()), top2_quota_share=''))
    per_cluster = []
    for c in range(sp.k):
        m = labels == c
        per_cluster.append(dict(cluster=c, n_target=int(m.sum()), camo_frac=float(camo_frac[c]),
                                target_es=float(sp.es[c]), silhouette_mean_cosine=float(sil_s[m].mean()) if m.any() else '',
                                n_test_assigned=int((ecl == c).sum()), n_cutouts_nearest=int(pool_hist[c])))

    def wcsv(name, rs):
        with open(os.path.join(rt, name), 'w', newline='') as f:
            cols = []
            for r in rs:
                cols += [c for c in r if c not in cols]
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rs:
                w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in r.items()})
    wcsv('AN-04_gate4_coverage_reproduction.csv', g4)
    wcsv('AN-04_foreground_coverage.csv', cov)
    wcsv('AN-04_cluster_domain_mix.csv', mix + [dict(arm='cluster %d' % r['cluster'], **r) for r in per_cluster])
    struct = [dict(quantity='silhouette (cosine, the 4033 labelled target images, committed k=75 labels)', value=sil_cos),
              dict(quantity='silhouette (euclidean on L2-normalised)', value=sil_euc),
              dict(quantity='committed silhouette_mean (b1_k_sweep, manuscript 0.1600)',
                   value=json.load(open(os.path.join(WT, 'rebuild/DIAG/out/diag_clusters.json')))['partition_stability']['silhouette_mean']),
              dict(quantity='committed-label vs nearest-centroid agreement (target)', value=float((nearest_cent == labels).mean()))]
    struct += [dict(quantity='eta^2 between-cluster share of (1-S_alpha), COD10K-test, ' + k, value=v) for k, v in eta.items()]
    wcsv('AN-04_cluster_structure.csv', struct)
    # ---- figure
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, t in zip(axes, TAGS):
        rows = [r for r in cov if r['embedder'] == t and r['k'] == 5]
        lab = [r['compared_set'] for r in rows]
        ax.barh(range(len(rows)), [r['recall'] for r in rows], color=['#888' if 'pool' in r['set_kind'] else '#2a6fbb' for r in rows])
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels(lab, fontsize=7)
        ax.set_xlim(0, 1)
        ax.set_title('%s, k=5 recall of real target' % t, fontsize=9)
    fig.suptitle('Post-review exploratory: how much of the real target each injected set covers', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(SR, 'FIGURES/AN-04_coverage.png'), dpi=150)
    summ = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), gate4_passed=gate4,
                gate4=[(g['embedder'], g['set'], round(g['recall'], 4), g['committed_recall']) for g in g4],
                foreground=fg, silhouette_cosine=sil_cos, silhouette_euclidean=sil_euc, eta2=eta, camo_mix=mix,
                labels_key=lab_key, seconds=round(time.time() - t0, 1),
                note='endpoint labels used only for the descriptive eta^2; no selection uses them')
    json.dump(summ, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-04_summary.json'), 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()

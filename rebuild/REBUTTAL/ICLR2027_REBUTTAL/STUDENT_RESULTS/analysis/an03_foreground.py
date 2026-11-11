"""AN-03 -- how much diversity the render pool can offer an allocation policy (CW-04 / QA-04).

Inputs (read-only, committed or cached): the pools' file listings; stem lists of every arm
(rebuild/ABC/out/{se,or,cdr}/...); frozen DINOv2 ViT-L/14 (518 px, CLS) embeddings of the authors' base
renders ('auth'), the LAKE-RED renders ('local'), the original HKU-IS photographs ('raw') and the grey-128
cutouts ('cut') -- rebuild/E0/cache/dinoL518_*; the committed k = 75 centroids and target assignment
(rebuild/B1/out); the quotas at tau = 1 and tau_H (TH-02).

Outputs: RESULT_TABLES/AN03_foreground_diversity.{csv,md}, AN03_arm_overlap.csv, AN03_cluster_fill.csv,
AN03_summary.json, FIGURES/AN03_fill_distance.pdf.  Embedding model: dinoL518 (state it with every number).
"""
import csv
import glob
import json
import math
import os

import numpy as np

import _repo as R

E0 = os.path.join(R.REPO, 'rebuild', 'E0', 'cache')
B1 = os.path.join(R.REPO, 'rebuild', 'B1', 'out')
OUT = os.path.join(R.REPO, 'rebuild', 'ABC', 'out')
RNG = np.random.default_rng(20261109)


def stem(n):
    n = os.path.splitext(os.path.basename(n))[0]
    return n[4:] if n.startswith(('SOD_', 'DUP_')) else n


def l2(x):
    x = np.asarray(x, dtype=np.float64)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def arm_sets():
    se, ot = os.path.join(OUT, 'se'), os.path.join(OUT, 'or')
    sets = {'B_s%d' % s: os.path.join(se, 'abc_stems_B_s%d.txt' % s) for s in (42, 43, 45, 46, 47, 48, 49, 50)}
    sets.update(C10=os.path.join(se, 'abc_stems_C_a1.0.txt'), CSHUF=os.path.join(se, 'abc_stems_CSHUF.txt'),
                CINV=os.path.join(se, 'abc_stems_CINV.txt'), CORACLE=os.path.join(ot, 'abc_stems_CORACLE.txt'))
    for p in sorted(glob.glob(os.path.join(OUT, 'cdr', 'cdr_stems_*.txt'))):
        sets[os.path.basename(p)[len('cdr_stems_'):-4]] = p
    return {k: open(v).read().split() for k, v in sets.items()}


def anova(groups):
    """Multivariate one-way ANOVA on L2-normalised embeddings. groups: list of (k, d) arrays of equal k."""
    X = np.concatenate(groups)
    k = groups[0].shape[0]
    G = len(groups)
    gm = np.stack([g.mean(0) for g in groups])
    tot = ((X - X.mean(0)) ** 2).sum()
    ssb = k * ((gm - X.mean(0)) ** 2).sum()
    ssw = sum(((g - g.mean(0)) ** 2).sum() for g in groups)
    msb, msw = ssb / (G - 1), ssw / (G * (k - 1))
    return dict(r2=float(ssb / tot), icc=float((msb - msw) / (msb + (k - 1) * msw)))


def main():
    names = json.load(open(os.path.join(E0, 'dinoL518_names.json')))
    emb = {k: np.load(os.path.join(E0, 'dinoL518_%s_cls.npy' % k)) for k in ('auth', 'local', 'raw', 'cut')}
    idx = {k: {stem(n): i for i, n in enumerate(names[k])} for k in ('auth', 'local', 'raw', 'cut')}
    # 1. source and bijection, from the directories themselves
    base = {stem(f) for f in os.listdir(os.path.join(R.REPO, 'Dataset/Source/HKU-IS/Image'))}
    local = {stem(f) for f in os.listdir(os.path.join(R.REPO, 'Dataset/LAKERED/output/HKU-IS/images'))}
    raw = {stem(f) for f in os.listdir(os.path.join(R.REPO, 'Dataset/Source/HKU-IS_raw/imgs'))}
    hkuis_split_files = sorted(f for f in os.listdir(os.path.join(R.REPO, 'Dataset/Source/HKU-IS_raw')) if f.endswith('.mat'))
    d1 = json.load(open(os.path.join(R.REPO, 'rebuild', 'D1', 'out', 'd1_bijection.json')))
    distinct = list(csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'D1', 'out', 'd1_pool_distinctness.csv'))))
    src = dict(base_pool_foregrounds=len(base), lakered_renders=len(local), raw_photographs=len(raw),
               renders_equal_base_stems=local == base, raw_equal_base_stems=raw == base,
               hkuis_split_files=hkuis_split_files, d1_is_bijection_local=d1.get('is_bijection_local'),
               d1_is_bijection_auth=d1.get('is_bijection_auth'),
               raw_unique_images=int([r for r in distinct if r['pool'] == 'raw'][0]['unique']))
    # 2. per-arm diversity and overlap
    sets = arm_sets()
    rows = []
    for a, st in sets.items():
        s = set(st)
        rows.append(dict(arm=a, injected=len(st), distinct_foregrounds=len(s), in_base_pool=len(s & base),
                         frac_in_base_pool=len(s & base) / len(s),
                         distinct_foregrounds_in_training_pool=len(base | s),
                         images_in_training_pool=len(base) + len(st),
                         share_of_pool_images_whose_foreground_appears_twice=2 * len(s & base) / (len(base) + len(st))))
    names_sorted = sorted(sets)
    ov = []
    for i, a in enumerate(names_sorted):
        for b in names_sorted[i + 1:]:
            x, y = set(sets[a]), set(sets[b])
            ov.append(dict(a=a, b=b, shared=len(x & y), jaccard=len(x & y) / len(x | y)))
    # 3. variance decomposition: foreground identity vs background
    common = sorted(set(idx['auth']) & set(idx['local']) & set(idx['raw']))
    A = l2(emb['auth'][[idx['auth'][s] for s in common]])
    L = l2(emb['local'][[idx['local'][s] for s in common]])
    W = l2(emb['raw'][[idx['raw'][s] for s in common]])
    two = anova([np.stack([A[i], L[i]]) for i in range(len(common))])
    three = anova([np.stack([A[i], L[i], W[i]]) for i in range(len(common))])
    perm2, perm3 = [], []
    for _ in range(50):
        p, q = RNG.permutation(len(common)), RNG.permutation(len(common))
        perm2.append(anova([np.stack([A[i], L[p[i]]]) for i in range(len(common))]))
        perm3.append(anova([np.stack([A[i], L[p[i]], W[q[i]]]) for i in range(len(common))]))
    cos_own = (L * A).sum(1)
    cos_rand = (L * A[RNG.permutation(len(common))]).sum(1)
    cos_raw_own = (L * W).sum(1)
    cos_raw_rand = (L * W[RNG.permutation(len(common))]).sum(1)
    var = dict(embedding='DINOv2 ViT-L/14, 518 px, CLS (rebuild/E0/cache/dinoL518_*)', n_foregrounds=len(common),
               two_renders=dict(r2=two['r2'], icc=two['icc'], perm_r2_mean=float(np.mean([x['r2'] for x in perm2])),
                                perm_icc_mean=float(np.mean([x['icc'] for x in perm2]))),
               renders_and_photo=dict(r2=three['r2'], icc=three['icc'], perm_r2_mean=float(np.mean([x['r2'] for x in perm3])),
                                      perm_icc_mean=float(np.mean([x['icc'] for x in perm3]))),
               cos_render_own_base=(float(cos_own.mean()), float(cos_own.std())),
               cos_render_random_base=(float(cos_rand.mean()), float(cos_rand.std())),
               cos_render_own_photo=(float(cos_raw_own.mean()), float(cos_raw_own.std())),
               cos_render_random_photo=(float(cos_raw_rand.mean()), float(cos_raw_rand.std())))
    # 4. per-cluster fill distances
    cen = l2(np.load(os.path.join(B1, 'b1_centroids_dinoL518_k75_seed0.npy')))
    cut = l2(emb['cut'])
    d = 1.0 - cut @ cen.T                                     # (4447, 75) cosine distance
    ds = np.sort(d, axis=0)
    asg = json.load(open(os.path.join(B1, 'b1_cluster_assignment_dinoL518.json')))
    tgt_names = json.load(open(os.path.join(E0, 'dinoL518_names.json')))['tgt']
    tgt = l2(np.load(os.path.join(E0, 'dinoL518_tgt_cls.npy')))
    tpos = {stem(n): i for i, n in enumerate(tgt_names)}
    labels = {stem(n): int(l) for n, l in zip(asg['target_names'], asg['target_labels'])}
    import c1_space
    from c1_targeted_vs_random import softmax_alloc, largest_remainder
    sp = c1_space.load_space('dinoL518')
    tauH = json.load(open(os.path.join(R.TABLES, 'TH02_summary.json')))['tau_H']
    q1 = largest_remainder(softmax_alloc(sp.es, 1.0), 1000)
    qH = largest_remainder(softmax_alloc(sp.es, tauH), 1000)
    crow = []
    for j in range(cen.shape[0]):
        members = [tpos[s] for s, l in labels.items() if l == j and s in tpos]
        md_ = float(np.median(1.0 - tgt[members] @ cen[j])) if members else float('nan')
        crow.append(dict(cluster=j, n_target=len(members), median_member_distance=md_,
                         d1=ds[0, j], d10=ds[9, j], d50=ds[49, j], q_tau1=int(q1[j]), d_q_tau1=ds[max(int(q1[j]) - 1, 0), j],
                         q_tauH=int(qH[j]), d_q_tauH=ds[max(int(qH[j]) - 1, 0), j],
                         nearest_cutout_farther_than_median_member=bool(ds[0, j] > md_)))
    summ = dict(source=src, variance=var, n_clusters=len(crow),
                clusters_nearest_cutout_farther_than_median_member=sum(r['nearest_cutout_farther_than_median_member'] for r in crow),
                d1_median=float(np.median([r['d1'] for r in crow])), median_member_distance_median=float(np.nanmedian([r['median_member_distance'] for r in crow])),
                coverage_cited=dict(note='cited from committed outputs, not re-derived here',
                                    a3_coverage='rebuild/A3/out/a3_coverage.csv', silhouette='rebuild/B1/out/b1_k_sweep_dinoL518.csv'))
    # writers
    def wcsv(name, rr):
        with open(os.path.join(R.TABLES, name), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rr[0].keys()))
            w.writeheader()
            for r in rr:
                w.writerow({k: ('%.6g' % v if isinstance(v, float) else v) for k, v in r.items()})
    wcsv('AN03_foreground_diversity.csv', rows)
    wcsv('AN03_arm_overlap.csv', ov)
    wcsv('AN03_cluster_fill.csv', crow)
    json.dump(summ, open(os.path.join(R.TABLES, 'AN03_summary.json'), 'w'), indent=2)
    sil = [r for r in csv.DictReader(open(os.path.join(B1, 'b1_k_sweep_dinoL518.csv'))) if r['k'] == '75']
    cov = list(csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'A3', 'out', 'a3_coverage.csv'))))
    md = ['# AN-03 -- foreground pool and generator constraints', '',
          '*Generated by `analysis/an03_foreground.py`; independently re-counted by `analysis/an03_counts_check.py`. '
          'Embedding for every distance and variance number: %s.*' % var['embedding'], '',
          '## 1. Foreground source and the bijection', '',
          '- Base pool: %d foregrounds; LAKE-RED renders: %d; original photographs: %d. Render stems equal base stems: %s; '
          'photo stems equal base stems: %s (D1 bijection flags: local %s, auth %s). The %d originals contain %d distinct images.'
          % (src['base_pool_foregrounds'], src['lakered_renders'], src['raw_photographs'], src['renders_equal_base_stems'],
             src['raw_equal_base_stems'], src['d1_is_bijection_local'], src['d1_is_bijection_auth'], src['raw_photographs'], src['raw_unique_images']),
          '- Source dataset: HKU-IS (the raw folder carries the HKU-IS split files %s).' % ', '.join(hkuis_split_files), '',
          '## 2. Distinct foregrounds and reuse per arm', '',
          '| Arm | injected | distinct foregrounds | already in base pool | distinct foregrounds in training pool | images in pool | share of pool images whose foreground appears twice |',
          '|---|---|---|---|---|---|---|']
    for r in rows:
        md.append('| %s | %d | %d | %d (%.1f%%) | %d | %d | %.3f |' % (r['arm'], r['injected'], r['distinct_foregrounds'], r['in_base_pool'],
                                                                     100 * r['frac_in_base_pool'], r['distinct_foregrounds_in_training_pool'],
                                                                     r['images_in_training_pool'], r['share_of_pool_images_whose_foreground_appears_twice']))
    jv = [o['jaccard'] for o in ov]
    md += ['', 'Pairwise overlap across all %d arms (`AN03_arm_overlap.csv`): Jaccard %.3f-%.3f.' % (len(sets), min(jv), max(jv)), '',
           '## 3. Foreground identity versus background in the render embeddings', '',
           '- Two renders of the same foreground (authors\' base render and the LAKE-RED render, different backgrounds): '
           'share of embedding variance between foregrounds R^2 = %.3f (random pairing: %.3f); intraclass correlation %.3f (random: %.3f).'
           % (var['two_renders']['r2'], var['two_renders']['perm_r2_mean'], var['two_renders']['icc'], var['two_renders']['perm_icc_mean']),
           '- Adding the original photograph (third background): R^2 = %.3f (random %.3f); ICC %.3f (random %.3f).'
           % (var['renders_and_photo']['r2'], var['renders_and_photo']['perm_r2_mean'], var['renders_and_photo']['icc'],
              var['renders_and_photo']['perm_icc_mean']),
           '- Cosine similarity, LAKE-RED render to its own base render %.3f +/- %.3f vs to a random base render %.3f +/- %.3f; '
           'to its own photograph %.3f +/- %.3f vs a random photograph %.3f +/- %.3f.'
           % (var['cos_render_own_base'] + var['cos_render_random_base'] + var['cos_render_own_photo'] + var['cos_render_random_photo']), '',
           '## 4. How close the available foregrounds are to each target cluster', '',
           '- Median over the 75 clusters of the distance from the centroid to its nearest available cutout: %.4f; median over '
           'clusters of the median distance of the cluster\'s own real members to its centroid: %.4f. In %d of 75 clusters the '
           'nearest available cutout is farther from the centre than the median real member. Caveat: cutouts are objects on a '
           'flat grey background while cluster members are full photographs, so part of this gap is the representation '
           'difference itself; the comparison describes the space the fill rule actually ranks in, not a pure measure of '
           'foreground mismatch.'
           % (summ['d1_median'], summ['median_member_distance_median'], summ['clusters_nearest_cutout_farther_than_median_member']),
           '- Per cluster: distance to the 1st, 10th, 50th and q_j-th nearest cutout at tau = 1 and tau_H = %.3f in `AN03_cluster_fill.csv`; '
           'the figure plots quota against the distance of the q-th nearest cutout. These ignore cross-cluster de-duplication; the '
           'realised fill distances per allocation (with de-duplication) are in `rebuild/ABC/out/cdr/cdr_allocations.csv`.' % tauH, '',
           '## 5. Relation to the submitted coverage and clustering numbers (cited, not re-derived)', '',
           '- k-means silhouette at k = 75 (dinoL518): %s (`rebuild/B1/out/b1_k_sweep_dinoL518.csv`).' % (sil[0]['silhouette_mean'] if sil else 'n/a'),
           '- k-NN coverage of the real target manifold: `rebuild/A3/out/a3_coverage.csv` (%d rows; the manuscript\'s 0.13-0.54 for '
           'synthetic vs 0.71-0.75 for the generator\'s source photographs).' % len(cov)]
    open(os.path.join(R.TABLES, 'AN03_foreground_diversity.md'), 'w').write('\n'.join(md) + '\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.scatter([r['q_tau1'] for r in crow], [r['d_q_tau1'] for r in crow], s=10, label='tau = 1 (C10 shape)')
    ax.scatter([r['q_tauH'] for r in crow], [r['d_q_tauH'] for r in crow], s=10, marker='x', label='tau_H = %.3f' % tauH)
    ax.axhline(summ['median_member_distance_median'], color='0.5', ls='--', lw=0.8, label='median real member to centroid')
    ax.set_xscale('symlog')
    ax.set_xlabel('quota of the cluster (images)', fontsize=8)
    ax.set_ylabel('cosine distance of the q-th nearest cutout', fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(R.FIGS, 'AN03_fill_distance.pdf'))
    print(json.dumps(dict(variance=var, clusters_far=summ['clusters_nearest_cutout_farther_than_median_member'],
                          d1_median=summ['d1_median'], member_median=summ['median_member_distance_median']), indent=1))


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""B1 completion II -- the ALLOCATION signal, and the gaps C1 depends on.

Three things, all of which C1 rests on and none of which the earlier B1 blocks
established.

1. THE ALLOCATION SIGNAL IS TARGET-MEASURED, NOT ENDPOINT-MEASURED.
   CLS.py:81-82 builds its loader on `target_root + 'Image/'` with
   `gt_root=None`, and CLS.py:105 computes ES there. ES is student-vs-teacher
   disagreement, so it needs no ground truth and IS available on the unlabeled
   target set at allocation time.

   The committed B1 blocks correlated ENDPOINT ES against ENDPOINT error --
   both measured on COD10K-test. That answers "does ES track error on the same
   images". It is NOT the quantity Stage C would allocate by. The cluster CSV
   C1 consumes carries `n_target` (a count) but no `target_es` at all, so a C1
   that allocated from it would be allocating by a test-set signal the pipeline
   does not have.

   This script computes per-image ES on the target set exactly as CLS.py does,
   aggregates it per cluster, and adds it to the artifact.

2. THE FAITHFUL CORRELATION. With target ES in hand, the question Stage C's
   design actually rests on becomes measurable: does per-cluster ES measured on
   the UNLABELED TARGET predict per-cluster error measured on the ENDPOINT?
   That is a different and harder question than the committed one, and it is
   the one that licenses targeted allocation.

3. THE CROSS-ARCHITECTURE GAP. The committed cross-architecture axis ran only
   in dinoL518. B1_RESULTS.md flagged that as unmeasured; this closes it in
   dinoL224 and clipL224 so the robustness claim is not itself
   embedder-specific.

Then it verifies every input C1 needs, in both candidate embedder spaces.

Consumes E0's caches, D2's leaked-name set, and the earlier B1 artifacts.
Nothing is re-embedded. TRAINS NOTHING -- inference only.

Usage:
  LAKE-RED/.venv/bin/python rebuild/B1/b1_allocation_signal.py
"""

import argparse
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
import common as C                                            # noqa: E402
import b1_es_error_correlation as B1                          # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'B1'
OUT = B1.OUT
EMBEDDERS = ('dinoL224', 'dinoL518', 'clipL224')
C1_CANDIDATES = ('dinoL518', 'dinoL224')   # clipL224 disqualified: no interior peak


def _p(m):
    print(m, flush=True)


def target_es_path(arch):
    return os.path.join(OUT, 'b1_target_es_%s.csv' % arch.replace('/', '-'))


# ---------------------------------------------------------------------------
# s1 -- per-image ES on the unlabeled target set, exactly as CLS.py computes it
# ---------------------------------------------------------------------------

def score_target_es(arch, es_cfg, device='cuda'):
    """ES per target image. NO ground truth is used or needed.

    Mirrors CLS.py:81-105 -- the same loader size, the same student/EMA-teacher
    pair, the same sigmoid-then-ESLoss call. The only difference from
    B1.score_arch is that no error metric is computed, because the target set
    has no GT; that is precisely why ES is usable as an allocation signal.
    """
    import torch
    import torchvision.transforms as T
    from PIL import Image

    spec = B1.ARCHS[arch]
    snap = os.path.join(C.REPO, 'Snapshot', arch)
    stu = B1._load_net(spec['net'], device)
    tea = B1._load_net(spec['net'], device)
    B1._load_ckpt(stu, os.path.join(snap, spec['stu']), device)
    B1._load_ckpt(tea, os.path.join(snap, 'Tea_epoch_best.pth'), device)
    es_loss, live = B1.build_es_loss(es_cfg, device)
    tf = T.Compose([T.Resize((B1.TESTSIZE, B1.TESTSIZE)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    d = C.ipath('tgt')
    names = C.listing('tgt')
    rows = []
    with torch.no_grad():
        for i, nm in enumerate(names):
            x = tf(Image.open(os.path.join(d, nm)).convert('RGB')).unsqueeze(0).to(device)
            s = B1._head(spec['net'], stu(x))
            t = B1._head(spec['net'], tea(x))
            rows.append(dict(arch=arch, name=nm,
                             es=float(es_loss(s.sigmoid(), t.sigmoid()).item())))
            if (i + 1) % 1000 == 0:
                _p('    %s target %d/%d' % (arch, i + 1, len(names)))
    del stu, tea
    torch.cuda.empty_cache()
    return rows, live


def step_target_es(es_cfg, archs, force=False):
    out = {}
    for arch in archs:
        p = target_es_path(arch)
        if os.path.isfile(p) and not force:
            _p('  %s target ES cached' % arch)
        else:
            _p('  scoring target ES: %s' % arch)
            rows, _ = score_target_es(arch, es_cfg)
            with open(p, 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=['arch', 'name', 'es'])
                w.writeheader(); w.writerows(rows)
        out[arch] = {r['name']: float(r['es'])
                     for r in csv.DictReader(open(p))}
    return out


# ---------------------------------------------------------------------------
# s2 / s3 -- per-cluster target ES, and the faithful correlation
# ---------------------------------------------------------------------------

def cluster_target_es(tag, k, seed, tgt_es):
    """Mean target-set ES per cluster, over the target images IN that cluster."""
    ap = os.path.join(OUT, 'b1_cluster_assignment_%s.json' % tag)
    if not os.path.isfile(ap):
        return None
    a = json.load(open(ap))
    if a['k'] != k or a['seed'] != seed:
        return None
    buckets = {}
    for nm, lab in zip(a['target_names'], a['target_labels']):
        if nm in tgt_es:
            buckets.setdefault(int(lab), []).append(tgt_es[nm])
    return {c: (float(np.mean(v)), len(v)) for c, v in buckets.items()}


def faithful_correlation(tag, k, seed, tgt_es, arch='SINet/S2C',
                         min_n=B1.MIN_CLUSTER_N, min_clusters=B1.MIN_CLUSTERS_FOR_RHO):
    """Per-cluster TARGET ES  vs  per-cluster ENDPOINT error.

    The allocation signal on one side, the thing it is meant to predict on the
    other. Both aggregated over the same cluster partition.
    """
    ces = cluster_target_es(tag, k, seed, tgt_es)
    if ces is None:
        return None
    X, tnames, _ = B1.load_target(tag)
    rows = B1.load_scores(arch, 'test')
    if rows is None:
        return None
    amap, _ = B1.assign_clusters(X, tnames, k, seed, 'test', tag)
    err = {}
    for r in rows:
        c = amap.get(r['name'])
        if c is not None:
            err.setdefault(c, []).append(r)
    used = sorted(c for c in err
                  if len(err[c]) >= min_n and c in ces and ces[c][1] >= 5)
    if len(used) < min_clusters:
        return dict(degenerate=True, clusters_used=len(used), k=k, tag=tag)
    a = [ces[c][0] for c in used]
    out = dict(degenerate=False, k=k, tag=tag, clusters_used=len(used),
               n_target_in_used=int(sum(ces[c][1] for c in used)),
               target_es_mean=float(np.mean(a)), target_es_sd=float(np.std(a)))
    for e in B1.ERRORS:
        b = [float(np.mean([r[e] for r in err[c]])) for c in used]
        rho, p, ci = B1.spearman_perm(a, b, n_perm=2000, seed=seed)
        out[e] = dict(rho=rho, perm_p=p, ci=ci)
    # and the endpoint-ES version on the SAME clusters, so the two questions are
    # compared on identical footing rather than across different cluster sets
    aes = [float(np.mean([r['es'] for r in err[c]])) for c in used]
    for e in B1.ERRORS:
        b = [float(np.mean([r[e] for r in err[c]])) for c in used]
        rho, _, _ = B1.spearman_perm(aes, b, n_perm=200, seed=seed)
        out['endpointES_%s' % e] = dict(rho=rho)
    rho_tt, _, _ = B1.spearman_perm(a, aes, n_perm=200, seed=seed)
    out['target_vs_endpoint_ES'] = dict(rho=rho_tt)
    return out


def augment_cluster_csv(tag, tgt_es, arch='SINet/S2C'):
    """Add target_es / n_target_scored to the artifact C1 reads."""
    p = os.path.join(OUT, 'b1_cluster_es_%s.csv' % tag)
    if not os.path.isfile(p):
        return None
    rows = list(csv.DictReader(open(p)))
    a = json.load(open(os.path.join(OUT, 'b1_cluster_assignment_%s.json' % tag)))
    ces = cluster_target_es(tag, a['k'], a['seed'], tgt_es)
    for r in rows:
        c = int(r['cluster'])
        if ces and c in ces:
            r['target_es'] = round(ces[c][0], 6)
            r['n_target_scored'] = ces[c][1]
        else:
            r['target_es'] = ''
            r['n_target_scored'] = 0
    fields = list(rows[0].keys())
    # put the allocation signal next to the target count, where it belongs
    for f in ('target_es', 'n_target_scored'):
        fields.remove(f)
    i = fields.index('n_target') + 1
    fields[i:i] = ['target_es', 'n_target_scored']
    with open(p, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    return p, sum(1 for r in rows if r['target_es'] != '')


# ---------------------------------------------------------------------------
# s5 -- is C1 actually runnable in both candidate spaces?
# ---------------------------------------------------------------------------

def check_c1_inputs(tag):
    """Every array C1 needs, verified present and row-aligned."""
    rep = dict(tag=tag)
    cs = os.path.join(OUT, 'b1_cluster_es_%s.csv' % tag)
    rep['cluster_es_csv'] = os.path.isfile(cs)
    if rep['cluster_es_csv']:
        rows = list(csv.DictReader(open(cs)))
        rep['n_clusters'] = len(rows)
        rep['clusters_with_target_es'] = sum(1 for r in rows
                                             if r.get('target_es') not in ('', None))
    ap = os.path.join(OUT, 'b1_cluster_assignment_%s.json' % tag)
    rep['assignment_json'] = os.path.isfile(ap)
    if rep['assignment_json']:
        a = json.load(open(ap))
        rep['k'] = a['k']
        rep['centroids_npy'] = os.path.isfile(
            os.path.join(OUT, 'b1_centroids_%s_k%d_seed%d.npy' % (tag, a['k'], a['seed'])))
    # the CUTOUT cache -- what C1 selects over (R2, grey-128), per E0
    cut = os.path.join(B1.E0_CACHE, '%s_cut_cls.npy' % tag)
    rep['cutout_cache'] = os.path.isfile(cut)
    if rep['cutout_cache']:
        arr = np.load(cut)
        names = json.load(open(os.path.join(B1.E0_CACHE,
                                            '%s_names.json' % tag)))['cut']
        raw_stems = [os.path.splitext(n)[0] for n in C.listing('raw')]
        cut_stems = [os.path.splitext(n)[0] for n in names]
        rep['cutout_rows'] = int(arr.shape[0])
        rep['cutout_dim'] = int(arr.shape[1])
        rep['cutout_aligned_to_raw'] = bool(cut_stems == raw_stems)
        rep['cutout_names_n'] = len(names)
    rep['leaked_names_json'] = os.path.isfile(B1.D2_LEAKED)
    rep['ready'] = all([rep.get('cluster_es_csv'), rep.get('assignment_json'),
                        rep.get('centroids_npy'), rep.get('cutout_cache'),
                        rep.get('cutout_aligned_to_raw'),
                        rep.get('leaked_names_json'),
                        rep.get('clusters_with_target_es', 0) > 0])
    return rep


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archs', default=','.join(B1.ARCHS))
    ap.add_argument('--embedders', default=','.join(EMBEDDERS))
    ap.add_argument('--force-score', action='store_true')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    archs = [a.strip() for a in args.archs.split(',')]
    tags = [t.strip() for t in args.embedders.split(',')]

    metrics, thresholds, notes, artifacts, old_claims = [], [], [], [], []
    es_cfg = B1.parse_es_config()

    # ---------------- s1: the allocation signal ----------------
    _p('=== s1 target-set ES (GT-free, per CLS.py) ===')
    tgt_es = step_target_es(es_cfg, archs, force=args.force_score)
    prim = tgt_es['SINet/S2C']
    v = np.array(list(prim.values()))
    metrics += [
        ('target_ES_images_scored', len(prim),
         'Dataset/Target/Image -- NO ground truth used, exactly CLS.py:81-105'),
        ('target_ES_mean_sd_range',
         '%.4f +- %.4f  [%.4f, %.4f]' % (v.mean(), v.std(), v.min(), v.max()),
         'SINet/S2C, the allocation signal Stage C would actually use'),
    ]
    thresholds.append(('target-set ES is computed for every target image without '
                       'using any ground truth', len(prim) == C.INPUTS['tgt']['n']))
    for a in archs:
        artifacts.append('rebuild/B1/out/%s' % os.path.basename(target_es_path(a)))

    # endpoint ES for the same model, for scale comparison
    ep = B1.load_scores('SINet/S2C', 'test')
    if ep:
        ev = np.array([r['es'] for r in ep])
        metrics.append(('endpoint_ES_mean_sd', '%.4f +- %.4f' % (ev.mean(), ev.std()),
                        'COD10K-test, for scale -- a DIFFERENT quantity from target ES'))

    # ---------------- s2: augment the C1 artifact ----------------
    _p('=== s2 augment cluster CSVs with target_es ===')
    for tag in tags:
        r = augment_cluster_csv(tag, prim)
        if r:
            p, n = r
            metrics.append(('cluster_csv_target_es_%s' % tag,
                            '%d clusters carry target_es' % n,
                            os.path.basename(p)))
            artifacts.append('rebuild/B1/out/%s' % os.path.basename(p))

    # ---------------- s3: the faithful correlation ----------------
    _p('=== s3 TARGET-ES vs ENDPOINT-ERROR per cluster ===')
    faith = {}
    for tag in tags:
        a = json.load(open(os.path.join(OUT, 'b1_cluster_assignment_%s.json' % tag)))
        f = faithful_correlation(tag, a['k'], a['seed'], prim)
        if f is None:
            continue
        faith[tag] = f
        if f.get('degenerate'):
            metrics.append(('FAITHFUL_%s_k%d' % (tag, a['k']),
                            'DEGENERATE-NOT-REPORTED (%d clusters)' % f['clusters_used'],
                            'target ES vs endpoint error'))
            continue
        metrics.append(
            ('FAITHFUL_targetES_vs_endpointERR_%s_k%d' % (tag, f['k']),
             'MAE %+.4f | 1-Sa %+.4f | 1-IoU %+.4f'
             % tuple(f[e]['rho'] for e in B1.ERRORS),
             '%d clusters, %d target images; THE quantity Stage C allocates by'
             % (f['clusters_used'], f['n_target_in_used'])))
        metrics.append(
            ('for_comparison_endpointES_same_clusters_%s' % tag,
             'MAE %+.4f | 1-Sa %+.4f | 1-IoU %+.4f'
             % tuple(f['endpointES_%s' % e]['rho'] for e in B1.ERRORS),
             'endpoint ES on the SAME clusters -- what the committed blocks measured'))
        metrics.append(
            ('rho_targetES_vs_endpointES_%s' % tag,
             round(f['target_vs_endpoint_ES']['rho'], 4),
             'do the two ES signals even agree per cluster?'))
        metrics.append(
            ('FAITHFUL_ratio_1mSa_over_MAE_%s' % tag,
             round(f['one_minus_sa']['rho'] / f['mae']['rho'], 4),
             'the wrong-objective ratio computed on the REAL allocation signal'))
    C.save_json(os.path.join(OUT, 'b1_faithful_correlation.json'), faith)
    artifacts.append('rebuild/B1/out/b1_faithful_correlation.json')

    good = {t: f for t, f in faith.items() if not f.get('degenerate')}
    if good:
        thresholds.append(
            ('the allocation signal (TARGET ES) predicts endpoint MAE at all '
             '(rho > 0.2 in every non-degenerate embedder space)',
             all(f['mae']['rho'] is not None and f['mae']['rho'] > 0.2
                 for f in good.values())))
        thresholds.append(
            ('TARGET-ES keeps the same ordering as ENDPOINT-ES: MAE > 1-Sa > 1-IoU',
             all(f['mae']['rho'] > f['one_minus_sa']['rho'] > f['one_minus_iou']['rho']
                 for f in good.values())))
        # the same test restricted to the spaces C1 can actually use, so a failure
        # caused only by clipL224's k=5 quantisation is distinguishable from a
        # substantive one
        cand = {t: f for t, f in good.items() if t in C1_CANDIDATES}
        thresholds.append(
            ('TARGET-ES ordering holds in the two C1-CANDIDATE spaces (clipL224 '
             'excluded: no interior silhouette peak, k*=5 on the degeneracy guard)',
             all(f['mae']['rho'] > f['one_minus_sa']['rho'] > f['one_minus_iou']['rho']
                 for f in cand.values())))
        fr = {t: f['one_minus_sa']['rho'] / f['mae']['rho'] for t, f in cand.items()}
        metrics.append(('FAITHFUL_ratio_range_candidates',
                        ' '.join('%s=%.4f' % (t, v) for t, v in fr.items()),
                        'the real-signal ratio in the spaces C1 may use'))
        thresholds.append(
            ('on the REAL allocation signal the 0.5 wrong-objective boundary is '
             'still not stateable (the ratio does not land cleanly on one side '
             'across spaces and signals)',
             not (all(v < 0.5 for v in fr.values())
                  or all(v >= 0.5 for v in fr.values()))))
        drops = {t: (f['endpointES_mae']['rho'] - f['mae']['rho'])
                 for t, f in good.items()}
        metrics.append(('rho_drop_endpointES_to_targetES_MAE',
                        ' '.join('%s=%+.4f' % (t, d) for t, d in drops.items()),
                        'how much weaker the REAL allocation signal is'))

    # ---------------- s4: cross-architecture, the flagged gap ----------------
    _p('=== s4 cross-architecture in the other embedder spaces ===')
    cross = {}
    for tag in tags:
        a = json.load(open(os.path.join(OUT, 'b1_cluster_assignment_%s.json' % tag)))
        X, tnames, _ = B1.load_target(tag)
        per = {}
        for arch in archs:
            r = B1.step_correlate(X, tnames, a['k'], arch, 'test',
                                  seeds=range(3), tag=tag)
            if r is None:
                continue
            per[arch] = {e: r['percluster_%s' % e]['rho_mean'] for e in B1.ERRORS}
        cross[tag] = per
        ok = [arch for arch, vv in per.items()
              if None not in vv.values()
              and vv['mae'] > vv['one_minus_sa'] > vv['one_minus_iou']]
        metrics.append(('crossarch_ordering_holds_%s' % tag,
                        '%d/%d architectures' % (len(ok), len(per)),
                        'k=%d, 3 seeds; failures: %s'
                        % (a['k'], ','.join(sorted(set(per) - set(ok))) or 'none')))
        for arch, vv in sorted(per.items()):
            if None in vv.values():
                continue
            metrics.append(('crossarch_%s_%s' % (tag, arch.replace('/', '-')),
                            'MAE %+.3f | 1-Sa %+.3f | 1-IoU %+.3f'
                            % (vv['mae'], vv['one_minus_sa'], vv['one_minus_iou']),
                            ''))
    C.save_json(os.path.join(OUT, 'b1_crossarch_all_embedders.json'), cross)
    artifacts.append('rebuild/B1/out/b1_crossarch_all_embedders.json')
    so_inverts = {}
    for tag, per in cross.items():
        v = per.get('SINet/S2C_SO')
        if v and None not in v.values():
            so_inverts[tag] = bool(v['one_minus_sa'] > v['mae'])
    metrics.append(('S2C_SO_inversion_by_embedder',
                    ' '.join('%s=%s' % (t, b) for t, b in so_inverts.items()),
                    'is the source-only inversion embedder-specific?'))

    # ---------------- s5: C1 readiness ----------------
    _p('=== s5 C1 input readiness ===')
    ready = {t: check_c1_inputs(t) for t in tags}
    C.save_json(os.path.join(OUT, 'b1_c1_readiness.json'), ready)
    artifacts.append('rebuild/B1/out/b1_c1_readiness.json')
    for t in tags:
        r = ready[t]
        metrics.append(('C1_ready_%s' % t, r['ready'],
                        'k=%s, %s clusters (%s with target_es), cutouts %sx%s '
                        'aligned=%s'
                        % (r.get('k'), r.get('n_clusters'),
                           r.get('clusters_with_target_es'), r.get('cutout_rows'),
                           r.get('cutout_dim'), r.get('cutout_aligned_to_raw'))))
    thresholds.append(
        ('C1 is runnable in BOTH candidate spaces (dinoL518 primary and dinoL224 '
         'sensitivity): every array present, cutouts row-aligned to the raw pool, '
         'target_es populated',
         all(ready[t]['ready'] for t in C1_CANDIDATES if t in ready)))

    # ------------------------------------------------------------------
    notes.append(
        'WHY THIS BLOCK EXISTS. CLS.py:81-82 builds its loader on '
        "target_root + 'Image/' with gt_root=None, and CLS.py:105 computes ES there. "
        'ES is student-vs-teacher disagreement, so it needs no ground truth and IS '
        'available on the unlabeled target set at allocation time. The two committed '
        'B1 blocks correlated ENDPOINT ES against ENDPOINT error -- a real result, '
        'but not the quantity Stage C allocates by. The cluster CSV C1 consumes '
        'carried n_target as a COUNT and no target_es at all, so a C1 built on it '
        'would have allocated by a test-set signal the pipeline does not have. Every '
        'committed value stands; this adds the missing one beside it.')
    notes.append(
        'THE TWO SIGNALS ARE REPORTED SIDE BY SIDE on the SAME clusters, so the '
        'comparison is not confounded by a different partition. rho for target ES and '
        'rho for endpoint ES appear in adjacent metrics, along with the correlation '
        'between the two signals themselves.')
    notes.append(
        'CROSS-ARCHITECTURE GAP CLOSED. B1_RESULTS.md recorded that the '
        'cross-architecture axis had run only in dinoL518 and that whether '
        "S2C_SO's inversion was embedder-specific was NOT measured. It is measured "
        'here in all three spaces.')
    notes.append(
        'UNCHANGED AND STILL TRUE: per-image rho is embedder-independent by '
        'construction and is not recomputed here; CAMO stays per-image only; '
        'CHAMELEON is excluded on D2\'s measurement; the >=5-cluster degeneracy guard '
        'applies in every space; clipL224 remains disqualified as C1\'s space because '
        'its silhouette curve has no interior maximum.')
    notes.append(
        'LIMITS. Target ES is computed from ONE final checkpoint pair per '
        'architecture; seed-level robustness stays UNVERIFIED-DEFERRED. The faithful '
        'correlation aggregates a target-side signal and an endpoint-side error over '
        'the same cluster partition, so it inherits the weak cluster structure already '
        'measured (silhouette 0.1465 / 0.1600 / 0.0568). Clusters needing at least 5 '
        'scored target images AND %d endpoint images are used; the rest are dropped '
        'rather than allowed to contribute a thin mean.' % B1.MIN_CLUSTER_N)

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/B1/b1_allocation_signal.py --embedders %s'
        % args.embedders,
        metrics, thresholds, old_claims, artifacts,
        representation=('target ES on whole target images at 352x352 (no GT); '
                        'clustering in %s' % ', '.join(tags)),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

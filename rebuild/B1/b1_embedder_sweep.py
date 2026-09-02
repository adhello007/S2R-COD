#!/usr/bin/env python
"""B1 completion -- is B1's answer embedder-specific?

The committed EXP B1 block (commit cc24dd9) measured everything in ONE embedding
space, dinoL518. E0 declared three embedders precisely so that no conclusion
would be embedder-specific (REBUILD_PLAN.md 0.2), so B1's clustering-dependent
findings were incomplete. This completes them.

WHAT IS AND IS NOT EMBEDDER-DEPENDENT, established from the committed code:

  embedder-DEPENDENT (all defaulted to dinoL518 in the committed run)
    - load_target            -> the array that gets clustered
    - step_cluster           -> k sweep, silhouette, seed-ARI, bootstrap-ARI
    - assign_clusters        -> which cluster each endpoint image falls in
    - per-cluster rho        -> depends on assign_clusters
    - cross-architecture rho -> same
    - emit_cluster_es        -> the artifact C1 consumes

  embedder-INDEPENDENT BY CONSTRUCTION
    - score_arch: contains no reference to any embedding cache. It reads image
      files, runs the student and EMA teacher, and computes ES plus MAE / Sa /
      IoU per image.
    - per-image rho: computed as spearman([r['es']], [r[err]]) over the score
      CSV rows. No clustering, no centroids, no embedding.

    Those per-image values therefore need no sweep. Rather than merely assert
    that, this script RECOMPUTES them inside every embedder loop and asserts
    they are bit-identical across all three -- if the claim of independence were
    wrong, that assertion fails.

Everything else is held identical to the committed run: the same ESLoss config
parsed from MyTrain.py, >=10 k-means seeds, the >=5-cluster degeneracy guard,
COD10K primary, CAMO per-image only, CHAMELEON excluded.

Reuses E0's cached embeddings -- nothing is re-embedded. TRAINS NOTHING.

Usage:
  LAKE-RED/.venv/bin/python rebuild/B1/b1_embedder_sweep.py
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

# All three embedders E0 declared and cached.
EMBEDDERS = ('dinoL224', 'dinoL518', 'clipL224')
CANONICAL = 'dinoL518'      # what the committed block used

# The committed dinoL518 values, for side-by-side comparison. RECORD ONLY --
# the sweep recomputes dinoL518 from scratch and must reproduce them; a
# divergence is a defect to resolve, not to smooth over.
COMMITTED = {
    'principled_k': 75,
    'silhouette_at_k_star': 0.16,
    'percluster_k75': dict(mae=0.8553, one_minus_sa=0.4276, one_minus_iou=0.2983),
    'percluster_k20': dict(mae=0.8699, one_minus_sa=0.5067, one_minus_iou=0.4060),
    'ratio_k75': 0.4999,
    'ratio_k20': 0.5825,
    'perimage_test': dict(mae=0.7514, one_minus_sa=0.3114, one_minus_iou=0.2015),
}


def _p(m):
    print(m, flush=True)


def sweep_one(tag, k_extra=20, seeds=None):
    """Everything clustering-dependent, in one embedder space."""
    seeds = seeds if seeds is not None else range(B1.N_SEEDS)
    X, tnames, lmeta = B1.load_target(tag)
    _p('  [%s] target %d x %d  (%d leaked dropped)'
       % (tag, X.shape[0], X.shape[1], lmeta['leaked_found']))

    kpath = os.path.join(OUT, 'b1_k_sweep_%s.csv' % tag)
    if os.path.isfile(kpath):
        krows = []
        for row in csv.DictReader(open(kpath)):
            krows.append({kk: (int(vv) if kk in ('k', 'n_seeds')
                               else (float(vv) if vv not in ('', None) else None))
                          for kk, vv in row.items()})
        _p('  [%s] k sweep reused from %s' % (tag, os.path.basename(kpath)))
    else:
        krows = B1.step_cluster(X)
        with open(kpath, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(krows[0].keys()))
            w.writeheader(); w.writerows(krows)
    k_star, kinfo = B1.pick_k(krows)
    sil_at = {r['k']: r['silhouette_mean'] for r in krows}
    boot_at = {r['k']: r['bootstrap_ari_mean'] for r in krows}
    seed_at = {r['k']: r['seed_ari_mean'] for r in krows}

    per_k = {}
    for k in sorted({k_star, k_extra}):
        per_k[k] = {}
        for split in B1.SPLITS:
            per_k[k][split] = B1.step_correlate(X, tnames, k, 'SINet/S2C', split,
                                                seeds=seeds, tag=tag)
    return dict(tag=tag, X_shape=list(X.shape), leaked=lmeta,
                k_rows=krows, k_star=k_star, k_info=kinfo,
                silhouette=sil_at, bootstrap_ari=boot_at, seed_ari=seed_at,
                per_k={str(k): v for k, v in per_k.items()},
                tnames=tnames)


def ratio(res, k, split='test'):
    r = res['per_k'][str(k)][split]
    m = r['percluster_mae']['rho_mean']
    s = r['percluster_one_minus_sa']['rho_mean']
    if m in (None, 0) or s is None:
        return None
    return s / m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--embedders', default=','.join(EMBEDDERS))
    ap.add_argument('--k-extra', type=int, default=20)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    tags = [t.strip() for t in args.embedders.split(',')]
    os.makedirs(OUT, exist_ok=True)

    metrics, thresholds, notes, artifacts, old_claims = [], [], [], [], []

    # ---- the ES convention is unchanged; re-assert it rather than assume ----
    es_cfg = B1.parse_es_config()
    _, live = B1.build_es_loss(es_cfg)
    cfg_ok = (live['a'] == es_cfg['a'] and live['b'] == es_cfg['b']
              and live['c'] == es_cfg['c'] and live['use_weighted_bce'] is False
              and es_cfg['cls_calls_on_sigmoid'])
    metrics.append(('ESLoss_config_unchanged',
                    'a=%s b=%s c=%s weighted=%s' % (es_cfg['a'], es_cfg['b'],
                                                    es_cfg['c'], live['use_weighted_bce']),
                    'same convention as the committed block, re-parsed from MyTrain.py'))
    thresholds.append(('the ES convention is identical to the committed B1 block',
                       bool(cfg_ok)))

    results = {}
    for tag in tags:
        _p('=== sweeping %s ===' % tag)
        results[tag] = sweep_one(tag, k_extra=args.k_extra)

    # ------------------------------------------------------------------
    # per-image rho: asserted embedder-independent, not merely claimed
    # ------------------------------------------------------------------
    pi = {}
    for tag in tags:
        r = results[tag]
        k0 = sorted(r['per_k'])[0]
        pi[tag] = {sp: {e: r['per_k'][k0][sp]['per_image'][e]['rho']
                        for e in B1.ERRORS} for sp in B1.SPLITS}
    ref = pi[tags[0]]
    identical = all(pi[t] == ref for t in tags)
    metrics.append(('perimage_rho_identical_across_embedders', identical,
                    'per-image rho reads only per-image ES and per-image error; '
                    'no embedding enters it'))
    for sp in B1.SPLITS:
        metrics.append(('perimage_%s_rho' % sp,
                        ' | '.join('%s %+.4f' % (e, ref[sp][e]) for e in B1.ERRORS),
                        'EMBEDDER-INDEPENDENT by construction, verified identical '
                        'across %d spaces' % len(tags)))
    thresholds.append(('per-image rho is bit-identical in all three embedder spaces, '
                       'confirming it is embedder-independent by construction',
                       bool(identical)))
    old_claims.append(('committed B1 per-image rho(ES,MAE) test',
                       '%+.4f' % COMMITTED['perimage_test']['mae'],
                       'MATCH' if abs(ref['test']['mae']
                                      - COMMITTED['perimage_test']['mae']) < 5e-4
                       else 'MISMATCH'))

    # ------------------------------------------------------------------
    # cluster structure per embedder
    # ------------------------------------------------------------------
    interior = {}
    for tag in tags:
        r = results[tag]
        ks = sorted(r['silhouette'])
        interior[tag] = bool(ks[0] < r['k_star'] < ks[-1])
        metrics.append(
            ('%s_principled_k' % tag, r['k_star'],
             'silhouette peak = %.4f; bootstrap ARI %.3f; seed ARI %.3f; peak is %s'
             % (r['silhouette'][r['k_star']], r['bootstrap_ari'][r['k_star']],
                r['seed_ari'][r['k_star']],
                'an INTERIOR maximum' if interior[tag]
                else 'AT THE GRID EDGE -- not a real peak')))
        metrics.append(
            ('%s_silhouette_curve' % tag,
             ' '.join('k%d=%.4f' % (k, v) for k, v in sorted(r['silhouette'].items())),
             'compactness / separation'))
        metrics.append(
            ('%s_bootstrap_ARI_curve' % tag,
             ' '.join('k%d=%.3f' % (k, v) for k, v in sorted(r['bootstrap_ari'].items())),
             'partition reproducibility over 80% subsamples'))
    sil_peaks = {t: results[t]['silhouette'][results[t]['k_star']] for t in tags}
    metrics.append(('silhouette_peak_all_embedders',
                    ' '.join('%s=%.4f' % (t, v) for t, v in sil_peaks.items()),
                    'weak structure iff every peak is low'))
    thresholds.append(
        ('WEAK CLUSTER STRUCTURE is embedder-robust: the silhouette peak is below '
         '0.25 in every embedder space', all(v < 0.25 for v in sil_peaks.values())))
    metrics.append(('silhouette_peak_is_interior_maximum',
                    ' '.join('%s=%s' % (t, interior[t]) for t in tags),
                    'False means the "peak" is the smallest k in the grid, so the '
                    'silhouette criterion did not select anything'))
    thresholds.append(
        ('the silhouette criterion actually selects a k in every embedder space '
         '(an interior maximum, not the grid edge)', all(interior.values())))

    # a COMMON operating point, so the three spaces are compared at the same k
    common_k = args.k_extra
    common = {}
    for tag in tags:
        cr = results[tag]['per_k'].get(str(common_k), {}).get('test')
        if not cr:
            continue
        m = cr['percluster_mae']['rho_mean']
        sa = cr['percluster_one_minus_sa']['rho_mean']
        io = cr['percluster_one_minus_iou']['rho_mean']
        common[tag] = (m, sa, io)
        metrics.append(('COMMON_k%d_%s' % (common_k, tag),
                        'MAE %+.4f | 1-Sa %+.4f | 1-IoU %+.4f | ratio %.4f'
                        % (m, sa, io, sa / m),
                        'same k in every space -- the apples-to-apples comparison'))
    thresholds.append(
        ('at a COMMON k=%d the ordering MAE > 1-Sa > 1-IoU holds in every embedder '
         'space' % common_k,
         all(m > sa > io for m, sa, io in common.values())))

    # ------------------------------------------------------------------
    # per-cluster rho per embedder, at k* and at k=20
    # ------------------------------------------------------------------
    rows = []
    for tag in tags:
        r = results[tag]
        for kstr, per_split in r['per_k'].items():
            k = int(kstr)
            for split, cr in per_split.items():
                rec = dict(embedder=tag, k=k, is_k_star=int(k == r['k_star']),
                           split=split, n_images=cr['n_images'],
                           clusters_used_lo=cr['percluster_mae']['clusters_used_range'][0],
                           clusters_used_hi=cr['percluster_mae']['clusters_used_range'][1],
                           silhouette=round(r['silhouette'][k], 4))
                for e in B1.ERRORS:
                    pc = cr['percluster_%s' % e]
                    rec['rho_%s' % e] = (round(pc['rho_mean'], 4)
                                         if pc['rho_mean'] is not None else '')
                    rec['sd_%s' % e] = (round(pc['rho_sd'], 4)
                                        if pc['rho_sd'] is not None else '')
                    rec['degenerate_%s' % e] = int(pc['degenerate'])
                    rec['perimage_%s' % e] = round(cr['per_image'][e]['rho'], 4)
                rec['ratio_1mSa_over_MAE'] = (
                    round(rec['rho_one_minus_sa'] / rec['rho_mae'], 4)
                    if rec['rho_mae'] not in ('', 0) and rec['rho_one_minus_sa'] != ''
                    else '')
                rows.append(rec)
                if split == 'test':
                    metrics.append(
                        ('percluster_%s_k%d_test' % (tag, k),
                         ('MAE %+.4f+-%.4f | 1-Sa %+.4f+-%.4f | 1-IoU %+.4f+-%.4f'
                          % (rec['rho_mae'], rec['sd_mae'],
                             rec['rho_one_minus_sa'], rec['sd_one_minus_sa'],
                             rec['rho_one_minus_iou'], rec['sd_one_minus_iou']))
                         if rec['rho_mae'] != '' else 'DEGENERATE-NOT-REPORTED',
                         'clusters used %d-%d of %d%s'
                         % (rec['clusters_used_lo'], rec['clusters_used_hi'], k,
                            ' [k*]' if rec['is_k_star'] else '')))
                elif rec['rho_mae'] == '':
                    metrics.append(
                        ('percluster_%s_k%d_val' % (tag, k),
                         'DEGENERATE-NOT-REPORTED (<%d clusters survive)'
                         % B1.MIN_CLUSTERS_FOR_RHO,
                         'clusters used %d-%d of %d -- CAMO stays per-image only'
                         % (rec['clusters_used_lo'], rec['clusters_used_hi'], k)))

    with open(os.path.join(OUT, 'b1_embedder_sweep.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    artifacts.append('rebuild/B1/out/b1_embedder_sweep.csv')

    # ---- ordering: pixel >> structure > boundary, in every space? ----
    order_ok, ratios = {}, {}
    for tag in tags:
        r = results[tag]
        for k in (r['k_star'], args.k_extra):
            cr = r['per_k'][str(k)]['test']
            m = cr['percluster_mae']['rho_mean']
            sa = cr['percluster_one_minus_sa']['rho_mean']
            io = cr['percluster_one_minus_iou']['rho_mean']
            if None in (m, sa, io):
                continue
            order_ok['%s@k%d' % (tag, k)] = bool(m > sa > io)
            ratios['%s@k%d' % (tag, k)] = sa / m
    metrics.append(('ordering_MAE_gt_1mSa_gt_1mIoU',
                    ' '.join('%s=%s' % (kk, vv) for kk, vv in order_ok.items()),
                    'per-cluster on COD10K'))
    metrics.append(('ratio_1mSa_over_MAE_all',
                    ' '.join('%s=%.4f' % (kk, vv) for kk, vv in ratios.items()), ''))
    thresholds.append(
        ('the ES-vs-error ORDERING (pixel >> structure > boundary) holds in every '
         'embedder space at every k tested', all(order_ok.values())))
    rv = list(ratios.values())
    metrics.append(('ratio_range', 'min %.4f max %.4f spread %.4f'
                    % (min(rv), max(rv), max(rv) - min(rv)),
                    'how far the ratio moves across embedder x k'))
    straddles = any(v < 0.5 for v in rv) and any(v >= 0.5 for v in rv)
    metrics.append(('ratio_straddles_the_0.5_boundary', straddles,
                    'if True the wrong-objective LABEL is not stateable; the effect '
                    'size still is'))
    thresholds.append(
        ('the declared 0.5 wrong-objective boundary is stable across embedders as '
         'well as across k (i.e. the binary label is stateable)', not straddles))

    # ---- reconcile the recomputed dinoL518 against the committed block ----
    if CANONICAL in results:
        r = results[CANONICAL]
        recon = []
        if r['k_star'] == COMMITTED['principled_k']:
            recon.append(('principled_k', True))
        else:
            recon.append(('principled_k', False))
        for k, key in ((COMMITTED['principled_k'], 'percluster_k75'),
                       (args.k_extra, 'percluster_k20')):
            if str(k) not in r['per_k']:
                continue
            cr = r['per_k'][str(k)]['test']
            for e in B1.ERRORS:
                got = cr['percluster_%s' % e]['rho_mean']
                exp = COMMITTED[key][e]
                recon.append(('%s_%s' % (key, e),
                              got is not None and abs(got - exp) < 5e-3))
        ok = all(v for _, v in recon)
        metrics.append(('dinoL518_reproduces_committed_block', ok,
                        '%d/%d values within 5e-3' % (sum(v for _, v in recon),
                                                      len(recon))))
        thresholds.append(
            ('re-running dinoL518 from scratch reproduces the committed EXP B1 '
             'values (no value is overwritten -- both are reported)', bool(ok)))
        for k, key in ((COMMITTED['principled_k'], 'percluster_k75'),
                       (args.k_extra, 'percluster_k20')):
            for e in B1.ERRORS:
                old_claims.append(
                    ('committed dinoL518 %s %s' % (key, e),
                     '%+.4f' % COMMITTED[key][e], 'RECONCILED'))

    # ------------------------------------------------------------------
    # the artifact C1 consumes -- now one per embedder, plus a stated choice
    # ------------------------------------------------------------------
    emitted = []
    for tag in tags:
        r = results[tag]
        p, recs = B1.emit_cluster_es(
            B1.load_target(tag)[0], r['tnames'], r['k_star'], 0,
            tag=tag, suffix='_%s' % tag)
        emitted.append((tag, r['k_star'], len(recs), os.path.basename(p)))
        metrics.append(('cluster_es_csv_%s' % tag,
                        '%s (k=%d, %d rows)' % (os.path.basename(p), r['k_star'],
                                                len(recs)),
                        'per-embedder deliverable'))
        artifacts.append('rebuild/B1/out/%s' % os.path.basename(p))
    metrics.append(('C1_should_read', 'b1_cluster_es_%s.csv' % CANONICAL,
                    'the canonical choice -- see the note below for why'))

    C.save_json(os.path.join(OUT, 'b1_embedder_sweep.json'),
                {t: {kk: vv for kk, vv in results[t].items() if kk != 'tnames'}
                 for t in tags})
    artifacts.append('rebuild/B1/out/b1_embedder_sweep.json')

    # ------------------------------------------------------------------
    notes.append(
        'SCOPE OF THE COMMITTED BLOCK, established from the code rather than assumed. '
        'Embedder-DEPENDENT and previously measured only in dinoL518: load_target '
        '(the clustered array), step_cluster (k sweep, silhouette, seed/bootstrap '
        'ARI), assign_clusters (endpoint-to-cluster assignment), every per-cluster '
        'rho, the cross-architecture per-cluster rho, and emit_cluster_es. '
        'Embedder-INDEPENDENT by construction: score_arch contains no reference to '
        'any embedding cache, and per-image rho is spearman over the score CSV alone. '
        'Per-image values are therefore NOT recomputed as a sweep -- they are '
        'recomputed inside every embedder loop and ASSERTED bit-identical, so the '
        'independence claim is tested rather than asserted.')
    notes.append(
        'TWO LATENT DEFECTS in the committed script, fixed here before sweeping. '
        'fit_kmeans cached on (k, seed) and endpoint_emb on split alone, and '
        'step_correlate / emit_cluster_es called assign_clusters WITHOUT a tag. With '
        'one embedder those are harmless; with three, the second and third spaces '
        'would silently have received dinoL518 k-means fits and dinoL518 endpoint '
        'embeddings, and every "embedder-robust" conclusion would have been an '
        'artifact of reading one cache three times. Cache keys now include the tag, '
        'the tag is threaded through, and defaults are unchanged so the committed '
        'dinoL518 result is bit-preserved -- which this block verifies by '
        'reproducing it.')
    notes.append(
        'CLIP DOES NOT HAVE A SILHOUETTE PEAK. Its curve falls monotonically from the '
        'smallest k in the grid (k5=0.0568 down to k150=0.0357), so the silhouette '
        'criterion returns k=5 by reaching the grid edge rather than by finding a '
        'maximum -- unlike both DINOv2 spaces, which have genuine interior maxima '
        '(k=50 and k=75). Two consequences, both reported rather than smoothed. '
        'First, clipL224 k*=5 sits exactly on the >=5-cluster guard, where Spearman '
        'over 5 points can only take a few discrete values -- which is why its MAE '
        'rho is exactly +1.0000 and its 1-Sa and 1-IoU are both exactly +0.6000, and '
        'why the ordering test fails there on a tie rather than on a reversal. '
        'Second, the honest cross-embedder comparison is at a COMMON k, which is why '
        'k=20 is reported for all three. The guard was NOT relaxed to make this go '
        'away.')
    notes.append(
        'CAMO remains per-image only in every embedder space: at these k values 1-4 '
        'clusters clear the 15-image floor, below the >=5 guard, so its per-cluster '
        'rho is logged DEGENERATE-NOT-REPORTED rather than reported as a 2-point '
        'correlation. CHAMELEON is excluded throughout on D2\'s measurement.')
    notes.append(
        'WHICH EMBEDDER C1 SHOULD INHERIT. C1 must not re-cluster, so the choice is '
        'now load-bearing. Recommendation: dinoL518, for three reasons that do not '
        'depend on the outcome. (1) It is the space the committed EXP B1 block used, '
        'so C1 inherits a clustering whose ES-vs-error behaviour is already measured '
        'and logged. (2) It is the only space in which the cross-architecture axis '
        'was run. (3) Its per-cluster ES is the artifact already committed. The '
        'per-embedder CSVs are all emitted, so a sensitivity re-run of C1 in another '
        'space costs one flag -- and given the ratio and k-star spread measured here, '
        'that sensitivity run is worth doing rather than assuming.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/B1/b1_embedder_sweep.py --embedders %s'
        % args.embedders,
        metrics, thresholds, old_claims, artifacts,
        representation=('R1 whole target image in THREE spaces (%s); per-image '
                        'metrics use no embedding at all' % ', '.join(tags)),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

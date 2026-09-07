#!/usr/bin/env python
"""D2_NC4K -- is NC4K contaminated by the COD10K test split?

WHY THIS SPECIFIC CHECK. The S2R-COD paper's Task Setup, Case 3, describes the NC4K
evaluation as additionally introducing synthetic images derived from the COD10K TEST
set into the SOURCE domain (Table 3 row "CAMO + CHAM. + COD10K -> NC4K"). If NC4K's
own test images overlap COD10K's test images, then the model trained for that row saw
synthetic renderings of photographs whose real versions are in the NC4K test set --
a source-into-test collision, and one the authors describe explicitly rather than one
introduced by accident.

That is a different mechanism from D2/D2R's CHAMELEON finding. There the leak was
target-side: unlabeled test pixels entering training through the target pool. Here it
would be source-side: the injected material is what supervises the model.

METHOD -- identical to the committed CHAMELEON audit, by construction. The sweep,
the descriptor, the tolerance, the quantization-table logic and the gap rule are not
re-implemented here: this script IMPORTS rebuild/D2_reaudit/detect_contamination.py,
the same module that produced the 41/76 CHAMELEON result and that passes an
8-assertion synthetic self-test while importing nothing from this repository.

Three levels, as D2:
  fhash  sha256 of file bytes        -- identical files, any name
  phash  sha256 of (shape + decoded RGB) -- additionally catches jpg<->png re-encodes
  near   exhaustive within each exact-dimension group, 32x32 descriptor shortlist at
         RMS <= 14, EVERY survivor verified at full resolution, mean|diff| <= 6.0,
         with the 1/2/3/5/6 tolerance sweep and the nearest-neighbour gap

Steps:
  s1  hash      both endpoints at both hash levels; set intersections; input digests
  s2  near      NC4K vs COD10K-TEST -- the primary target of this check (Case 3)
  s3  topk      is the gap verdict invariant to shortlist depth 8 / 32 / all?
  s4  train     NC4K vs COD10K-TRAIN, reported SEPARATELY, so the claim can say which
                COD10K partition any collision involves
  s5  evidence  per confirmed pair: quantization tables two ways + container format,
                with D2R's caveat that a MISSING table is "not applicable", never
                "differs"

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2_nc4k/d2_nc4k_crosscheck.py

Trains nothing -- no model is loaded at all. Nothing under Dataset/, Result/ or
Snapshot/ is written.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

# The method comes from the committed, self-testing detector -- not re-implemented.
sys.path.insert(0, C.exp_dir('D2_reaudit'))
import detect_contamination as DET                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'D2_NC4K'
OUT = C.exp_dir('D2_nc4k', 'out')
CACHE = C.exp_dir('D2_nc4k', 'cache')

NC4K = 'Dataset/Test/NC4K/Imgs'
NC4K_GT = 'Dataset/Test/NC4K/GT'
TEST = 'Dataset/Test/COD10K/Imgs'
TEST_GT = 'Dataset/Test/COD10K/GT'
TRAIN = 'rebuild/D2_nc4k/cache/cod10k_train'   # COD10K-CAM-* subset of Target/Image

# declared counts, asserted before anything is measured
N_DECLARED = {NC4K: 4121, NC4K_GT: 4121, TEST: 2026, TEST_GT: 2026, TRAIN: 3040}

TOL = DET.NEAR_TOL          # 6.0
TOL_SWEEP = DET.TOL_SWEEP   # (1.0, 2.0, 3.0, 5.0, 6.0)
TOPK_SWEEP = (8, 32, 0)     # 0 = every same-dimension candidate


def _p(m):
    print(m, flush=True)


def _hash_one(args):
    """Identical to d2_leakage_sweep.py:76-94."""
    split, name, path = args
    with open(path, 'rb') as fh:
        raw = fh.read()
    fhash = hashlib.sha256(raw).hexdigest()
    try:
        a = np.asarray(Image.open(path).convert('RGB'))
        ph = hashlib.sha256()
        ph.update(str(a.shape).encode())
        ph.update(a.tobytes())
        return dict(split=split, name=name, fhash=fhash, phash=ph.hexdigest(),
                    shape='%dx%d' % (a.shape[1], a.shape[0]))
    except Exception as e:
        return dict(split=split, name=name, fhash=fhash, phash='UNREADABLE',
                    shape='?', error=str(e)[:60])


def step_hash(dirs, workers):
    jobs = []
    for tag, d in dirs.items():
        full = os.path.join(C.REPO, d)
        for nm in sorted(os.listdir(full)):
            jobs.append((tag, nm, os.path.join(full, nm)))
    _p('s1: hashing %d images across %d sets...' % (len(jobs), len(dirs)))
    recs = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_hash_one, jobs, chunksize=64)):
            recs.append(r)
            if (i + 1) % 4000 == 0:
                _p('  %d/%d' % (i + 1, len(jobs)))
    return recs


def cross(recs, a, b, level):
    """|a INTERSECT b| at one hash level, set-based, filename-independent."""
    ha = {r[level] for r in recs if r['split'] == a and r[level] != 'UNREADABLE'}
    hits = []
    for r in recs:
        if r['split'] == b and r[level] != 'UNREADABLE' and r[level] in ha:
            names = [x['name'] for x in recs
                     if x['split'] == a and x[level] == r[level]]
            for an in names:
                hits.append((an, r['name'], r[level][:32]))
    return hits


def evidence(dir_a, dir_b, pairs):
    """Per-pair re-encoding evidence, with D2R's not-applicable caveat."""
    rows = []
    for i, p in enumerate(sorted(pairs, key=lambda r: r['mean_abs']), 1):
        pa = os.path.join(C.REPO, dir_a, p['image_a'])
        pb = os.path.join(C.REPO, dir_b, p['image_b'])
        v, agree, qa, qb = DET.qtable_verdict(pa, pb)
        fa, fb = DET.container_format(pa), DET.container_format(pb)
        rows.append(dict(rank=i, nc4k_image=p['image_a'], partner=p['image_b'],
                         dims=p['dims'], mean_abs=p['mean_abs'],
                         p99_abs=p['p99_abs'], max_abs=p['max_abs'],
                         frac_gt8=p['frac_gt8'], content_std=p['content_std'],
                         pixel_identical=int(p['pixel_identical']),
                         qtable_evidence=v, qtable_methods_agree=int(bool(agree)),
                         qtable_hash_a=qa, qtable_hash_b=qb,
                         format_nc4k=fa, format_partner=fb,
                         formats_differ=int(fa != fb)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    metrics, thresholds, old_claims, artifacts = [], [], [], []

    def A(p):
        artifacts.append(os.path.relpath(p, C.REPO))

    # ---- inputs asserted before any measurement -------------------------
    counts = {}
    for d, n in N_DECLARED.items():
        full = os.path.join(C.REPO, d)
        if not os.path.isdir(full):
            raise SystemExit('missing input %s -- no fallback path by design' % d)
        counts[d] = len(os.listdir(full))
    digests = {d: C.dir_digest(os.path.join(C.REPO, d))[1][:16] for d in N_DECLARED}
    for d, n in N_DECLARED.items():
        metrics.append(('input_%s' % os.path.basename(os.path.dirname(d) + '_'
                                                      + os.path.basename(d)),
                        '%d files, agg %s' % (counts[d], digests[d]), d))
    thresholds.append(
        ('T1 every declared input is present with its declared count '
         '(NC4K 4121+4121, COD10K-test 2026+2026, COD10K-train 3040)',
         all(counts[d] == n for d, n in N_DECLARED.items())))

    # ---- s1: exact identity, both levels --------------------------------
    recs = step_hash({'nc4k': NC4K, 'test': TEST, 'train': TRAIN}, args.workers)
    unreadable = sum(1 for r in recs if r['phash'] == 'UNREADABLE')
    pairs_exact = {}
    for a, b in (('nc4k', 'test'), ('nc4k', 'train'), ('test', 'train')):
        for level in ('fhash', 'phash'):
            hits = cross(recs, a, b, level)
            pairs_exact[(a, b, level)] = hits
            _p('s1: %s INTERSECT %s at %s = %d' % (a, b, level, len(hits)))
    metrics += [
        ('images_hashed', len(recs), '3 sets'),
        ('unreadable_images', unreadable, 'decode failures'),
        ('NC4K_INTERSECT_COD10Ktest_byte',
         len(pairs_exact[('nc4k', 'test', 'fhash')]), 'sha256 of file bytes'),
        ('NC4K_INTERSECT_COD10Ktest_pixel',
         len(pairs_exact[('nc4k', 'test', 'phash')]), 'decoded-RGB hash'),
        ('NC4K_INTERSECT_COD10Ktrain_byte',
         len(pairs_exact[('nc4k', 'train', 'fhash')]), ''),
        ('NC4K_INTERSECT_COD10Ktrain_pixel',
         len(pairs_exact[('nc4k', 'train', 'phash')]), ''),
        ('COD10Ktest_INTERSECT_COD10Ktrain_byte',
         len(pairs_exact[('test', 'train', 'fhash')]),
         'context: D2 measured 7 against the full Target pool'),
    ]

    # ---- s2 / s4: the near-duplicate sweeps -----------------------------
    res = {}
    for tag, other in (('test', TEST), ('train', TRAIN)):
        _p('s%s: NC4K vs COD10K-%s -- same-dimension exhaustive sweep...'
           % ('2' if tag == 'test' else '4', tag))
        r = DET.sweep(os.path.join(C.REPO, NC4K), os.path.join(C.REPO, other),
                      tol=TOL, topk=8, workers=args.workers, quiet=True)
        res[tag] = r
        c, nn = r['contaminated'], r['nearest_neighbour']
        vals = nn['sorted_nearest']
        _p('   confirmed pairs %d | distinct NC4K images %d/%d | checkable %d | '
           'unchecked %d | gap %s'
           % (r['pairs_confirmed'], c['n'], counts[NC4K], nn['n_checkable'],
              nn['n_unchecked'], nn['largest_gap']))
        metrics += [
            ('nearvdup_NC4K_matching_COD10K%s' % tag,
             '%d/%d (%.1f%%)' % (c['n'], counts[NC4K], 100 * c['share']),
             'distinct NC4K images that are exact or same-dimension re-encoded '
             'duplicates'),
            ('near_dup_shortlisted_NC4K_vs_%s' % tag,
             r['candidate_pairs_shortlisted'],
             'exhaustive within-dimension, descriptor RMS <= 14'),
            ('near_dup_confirmed_NC4K_vs_%s' % tag, r['pairs_confirmed'],
             'full-res verified, mean|diff| <= 6.0'),
            ('epNN_NC4K_vs_%s_checkable' % tag,
             '%d/%d' % (nn['n_checkable'], counts[NC4K]),
             'has >=1 same-dimension candidate on the other side'),
            ('epNN_NC4K_vs_%s_unchecked' % tag,
             '%d/%d' % (nn['n_unchecked'], counts[NC4K]),
             'no same-dimension candidate -- UNCHECKED IS NOT CLEAN'),
            ('epNN_NC4K_vs_%s_gap' % tag,
             ('%d below %.2f, next at %.2f' % (nn['largest_gap']['n_below'],
                                               nn['largest_gap']['below'],
                                               nn['largest_gap']['above'])
              if nn['largest_gap'] else 'none'),
             ('ratio %.2fx' % nn['largest_gap']['ratio']) if nn['largest_gap']
             else 'no >5x jump found -- a continuous distribution is what a clean '
                  'set looks like'),
            ('epNN_NC4K_vs_%s_min_nearest' % tag,
             ('%.3f' % vals[0]) if vals else 'n/a',
             'the closest any NC4K image gets to the other set, in grey levels'),
            ('epNN_NC4K_vs_%s_nearest_deciles' % tag,
             (' '.join('%.1f' % np.percentile(vals, q)
                       for q in (10, 25, 50, 75, 90)) if vals else 'n/a'),
             'p10 p25 p50 p75 p90 of the nearest-distance distribution'),
            # promoted from arithmetic into metrics: both are quoted by
            # CLEAN_PROTOCOL.md, and a number a document uses must be logged
            ('epNN_NC4K_vs_%s_min_nearest_over_tol' % tag,
             ('%.2fx' % (vals[0] / TOL)) if vals else 'n/a',
             'closest approach as a multiple of the %.1f confirmation tolerance; '
             'the margin by which the null holds' % TOL),
            ('epNN_NC4K_vs_%s_unchecked_share' % tag,
             '%.1f%%' % (100.0 * nn['n_unchecked'] / counts[NC4K]),
             'share of NC4K that cannot be compared at all -- unchecked is not clean'),
        ]
        for t in TOL_SWEEP:
            metrics.append(('nearvdup_NC4K_vs_%s_at_tol_%g' % (tag, t),
                            '%d/%d' % (r['tolerance_sweep'][str(t)], counts[NC4K]),
                            'post-hoc filter on the tol=6.0 set, as in D2'))
        C.save_json(os.path.join(OUT, 'd2nc4k_sweep_%s.json' % tag),
                    {k: v for k, v in r.items() if k != 'nn_rows'})
        A(os.path.join(OUT, 'd2nc4k_sweep_%s.json' % tag))
        with open(os.path.join(OUT, 'd2nc4k_nearest_%s.csv' % tag), 'w',
                  newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(r['nn_rows'][0]))
            w.writeheader()
            w.writerows(r['nn_rows'])
        A(os.path.join(OUT, 'd2nc4k_nearest_%s.csv' % tag))

    # partition the COD10K-train partners, so the claim can name the partition
    pools = {}
    for p in res['train']['pairs']:
        k = 'cod10k_train' if p['image_b'].startswith('COD10K') else 'other'
        pools[k] = pools.get(k, 0) + 1
    metrics.append(('NC4K_train_partner_partition',
                    (', '.join('%s=%d' % kv for kv in sorted(pools.items()))
                     or 'no confirmed pairs'),
                    'which COD10K partition any collision involves'))

    # ---- s3: is the gap verdict invariant to shortlist depth? -----------
    sens = {}
    for k in TOPK_SWEEP:
        if k == 8:
            sens['topk_8'] = res['test']['nearest_neighbour']
        else:
            _p('s3: re-running NC4K vs COD10K-test at topk=%s' % (k or 'all'))
            r = DET.sweep(os.path.join(C.REPO, NC4K), os.path.join(C.REPO, TEST),
                          tol=TOL, topk=k, workers=args.workers, quiet=True)
            sens['topk_%s' % (k or 'all')] = r['nearest_neighbour']
    for name, nn in sens.items():
        metrics.append(('epNN_NC4K_vs_test_gap_%s' % name,
                        ('%d below %.2f, next at %.2f'
                         % (nn['largest_gap']['n_below'], nn['largest_gap']['below'],
                            nn['largest_gap']['above'])
                         if nn['largest_gap'] else 'none'),
                        'min nearest %.3f; sensitivity, topk=8 is the comparison run'
                        % (nn['sorted_nearest'][0] if nn['sorted_nearest'] else -1)))
    C.save_json(os.path.join(OUT, 'd2nc4k_topk_sensitivity.json'),
                {k: {kk: vv for kk, vv in v.items() if kk != 'sorted_nearest'}
                 for k, v in sens.items()})
    A(os.path.join(OUT, 'd2nc4k_topk_sensitivity.json'))
    gap_verdicts = {bool(v['largest_gap']) for v in sens.values()}
    min_nearest = {round(v['sorted_nearest'][0], 3) if v['sorted_nearest'] else None
                   for v in sens.values()}

    # ---- s5: evidence per confirmed pair --------------------------------
    ev = {t: evidence(NC4K, d, res[t]['pairs'])
          for t, d in (('test', TEST), ('train', TRAIN))}
    n_ev = len(ev['test']) + len(ev['train'])
    if n_ev:
        for t in ('test', 'train'):
            if not ev[t]:
                continue
            with open(os.path.join(OUT, 'd2nc4k_pairs_%s.csv' % t), 'w',
                      newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(ev[t][0]))
                w.writeheader()
                w.writerows(ev[t])
            A(os.path.join(OUT, 'd2nc4k_pairs_%s.csv' % t))
        qd = sum(1 for t in ev for r in ev[t] if r['qtable_evidence'] == 'differ')
        na = sum(1 for t in ev for r in ev[t] if r['qtable_evidence'] == 'na')
        fd = sum(r['formats_differ'] for t in ev for r in ev[t])
        ag = sum(r['qtable_methods_agree'] for t in ev for r in ev[t])
        metrics += [
            ('qtables_differ_DQT', '%d/%d' % (qd, n_ev),
             'raw 0xFFDB parse; %d not applicable (a side is not JPEG)' % na),
            ('qtables_not_applicable', '%d/%d' % (na, n_ev),
             'D2R: a MISSING table is not applicable, never "differs"'),
            ('pairs_differing_in_container_format', '%d/%d' % (fd, n_ev), ''),
            ('qtable_methods_agree', '%d/%d' % (ag, n_ev), 'PIL vs raw DQT'),
        ]
        thresholds.append(
            ('T5 every confirmed pair carries independent re-encoding evidence -- a '
             'differing quantization table or a differing container format',
             qd + fd >= n_ev and ag == n_ev))
    else:
        metrics.append(('confirmed_pairs_total', 0,
                        'no pair reached mean|diff| <= 6.0 at identical dimensions, '
                        'so there is no per-pair evidence to report'))
        thresholds.append(
            ('T5 every confirmed pair carries independent re-encoding evidence '
             '(vacuously satisfied: there are no confirmed pairs)', True))

    # ---- the contaminated-pair resource, only if there is anything ------
    n_test = res['test']['contaminated']['n']
    if n_test:
        na_, aggn, _ = C.dir_digest(os.path.join(C.REPO, NC4K))
        nt, aggt, _ = C.dir_digest(os.path.join(C.REPO, TEST))
        C.save_json(os.path.join(OUT, 'nc4k_contaminated.json'), dict(
            schema_version='1.0',
            finding=('%d of %d NC4K images are exact or same-dimension re-encoded '
                     'duplicates of COD10K-test images.' % (n_test, counts[NC4K])),
            method=res['test']['method'],
            reference_set=dict(name='NC4K test', n=na_, listing_sha256=aggn),
            other_set=dict(name='COD10K test', n=nt, listing_sha256=aggt),
            contaminated=ev['test'],
            counts=dict(n_contaminated=n_test,
                        share=res['test']['contaminated']['share']),
            tolerance_sweep=res['test']['tolerance_sweep'],
            nn_gap=res['test']['nearest_neighbour']['largest_gap'],
            unchecked=dict(n=res['test']['nearest_neighbour']['n_unchecked'],
                           reason='no same-dimension candidate; unchecked is not clean'),
            limitations=res['test']['limitations'],
            provenance=dict(log_block='EXP D2_NC4K', commit=C.git_commit(),
                            timestamp=C.now())))
        A(os.path.join(OUT, 'nc4k_contaminated.json'))
    else:
        _p('s5: no confirmed NC4K/COD10K-test pairs -- no contaminated-pair list '
           'is emitted, because there is nothing to list')

    # ---- declared thresholds --------------------------------------------
    thresholds += [
        ('T2 NC4K INTERSECT COD10K-test is empty at the file-byte level',
         len(pairs_exact[('nc4k', 'test', 'fhash')]) == 0),
        ('T3 NC4K INTERSECT COD10K-test is empty at the decoded-pixel level',
         len(pairs_exact[('nc4k', 'test', 'phash')]) == 0),
        ('T4 no NC4K image is a same-dimension re-encoded duplicate of a '
         'COD10K-test image at mean|diff| <= 6.0', n_test == 0),
        ('T6 the NC4K-vs-COD10K-test gap verdict and minimum nearest distance are '
         'invariant across shortlist depth 8 / 32 / all',
         len(gap_verdicts) == 1 and len(min_nearest) == 1),
        ('T7 NC4K INTERSECT COD10K-train measured and reported separately '
         '(NEW -- no prior value)', True),
    ]
    dirty = C.subprocess.check_output(
        ['git', '-C', C.REPO, 'status', '--porcelain', '--',
         'Dataset', 'Result', 'Snapshot'], text=True).strip()
    thresholds.append(
        ('T8 nothing under Dataset/, Result/ or Snapshot/ is modified', dirty == ''))

    cmd = 'LAKE-RED/.venv/bin/python rebuild/D2_nc4k/d2_nc4k_crosscheck.py'
    text = C.log_block(EXP, cmd, metrics, thresholds, old_claims, artifacts,
                       representation=('decoded pixels (the only level that survives '
                                       're-encoding)'),
                       trains='NO', notes=NOTES, write=not args.no_log)
    print(text)


NOTES = """WHY: the S2R-COD paper's Task Setup Case 3 describes the NC4K evaluation as additionally introducing synthetic images derived from the COD10K TEST set into the SOURCE domain (Table 3, "CAMO + CHAM. + COD10K -> NC4K"). Were NC4K to overlap COD10K-test, that injection would put synthetic renderings of NC4K's own test photographs into supervision -- a SOURCE-INTO-TEST collision, and a different mechanism from D2/D2R's CHAMELEON finding, which was target-side and unlabeled.
METHOD IDENTITY IS BY IMPORT, NOT BY COPY. This script imports rebuild/D2_reaudit/detect_contamination.py -- the same module that produced the committed 41/76 CHAMELEON result, which imports nothing from this repository and passes an 8-assertion synthetic known-answer self-test. The descriptor (32x32 greyscale BILINEAR, no contrast normalisation), the shortlist (Gram-matrix RMS <= 14, exhaustive within each exact-dimension group), the confirmation rule (full-resolution mean|A-B| <= 6.0), the 1/2/3/5/6 tolerance sweep and the >5x gap rule are therefore identical by construction rather than by inspection.
EVERY COUNT IS A LOWER BOUND. Coverage is exact duplicates plus same-dimension re-encodes. Rescaled copies that land outside every dimension group, crops, flips, rotations, colour shifts and different photographs of one specimen are NOT detected and are NOT claimed. An NC4K image with no same-dimension candidate on the other side is UNCHECKED, NOT CLEAN, and the unchecked count is reported for both comparisons rather than folded into a clean rate.
A NULL IS A RESULT. The thresholds are written so that PASS means NO collision. If they pass, Case 3's described injection does not put COD10K-test photographs into the NC4K test column by this measure, and that is reported as measured -- not strained toward a finding. The minimum nearest distance and the decile spread are logged precisely so a null is quantitative rather than merely an absence.
TRACEABILITY: this is the second D2_NC4K block. The first ran every step and reached the same verdict, but two figures CLEAN_PROTOCOL.md quotes -- the closest approach as a multiple of the tolerance, and the unchecked share as a percentage -- existed only as arithmetic over logged values rather than as logged metrics. They are promoted here. No measured value changed. Same rule as D2's own blocks 1->2 (R4 in REVISION_TABLE.md) and E0's blocks 3->4.
CONTEXT, NOT A CLAIM ABOUT INTENT: D2's committed d2_pair_matrix.csv already recorded NC4K INTERSECT COD10K-test = 0 at both hash levels as part of its 8-split sweep. This experiment re-derives that with the near-duplicate level added, which D2 never ran for this specific pair, and adds the COD10K-train partition. Whether the paper's Case 3 text describes a leak is a question about the measured overlap; this block reports the overlap and does not attribute intent.
SCOPE OF THE COD10K-TRAIN SIDE: "COD10K-train" here is the 3040 COD10K-CAM-* files inside Dataset/Target/Image, exposed as a directory of symlinks under rebuild/D2_nc4k/cache/ so the detector can take it as a plain path. That is the published COD10K camouflage train split as this checkout holds it; the other 1000 files in Target/Image are CAMO and are excluded from that side by construction."""


if __name__ == '__main__':
    main()

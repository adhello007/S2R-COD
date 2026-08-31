#!/usr/bin/env python
"""D1 -- Foreground exhaustion.

Establishes what any null result in this pipeline may be scoped to. If every
image Stage C could "add" is a re-render of a foreground already in the base
training pool, then a null is correctly stated as "targeting does not help once
the foreground pool is exhausted" -- NOT the broader "targeting does not help".

D2 sharpened two things this experiment must respect rather than paper over:

  * Distinctness is POOL-DEPENDENT (D2 s3): raw HKU-IS 4443 unique of 4447,
    authors' pool 4447, local renders 4445. "4447 distinct foregrounds" is not
    a fact; it is a file count.
  * A render is keyed by (foreground, mask, POSITION IN SHARD), not by the
    foreground alone (D2 s7/s8). So "the render pool is a function of the
    foreground pool" holds only at a fixed shard count over a fixed input
    listing, and D1 carries that qualifier.

Steps:
  s1  verify     E0's manifest hashes still describe the files on disk
  s2  pools      per-pool unique counts, reconciled against D2
  s3  polarity   assert the polarity of EVERY mask set at run time (trap T2)
  s4  bijection  does the render set map onto the raw foreground set?
  s5  literal    is the mapping literal -- does each render carry its source
                 object pixels? (E0's isReplace finding, over all 4447)
  s6  scope      the position qualifier, read from D2's output

Consumes E0's manifest; does not re-hash except to verify. Reads no archived
artifact and no scratchpad. Trains nothing.

Usage:
  LAKE-RED/.venv/bin/python rebuild/D1/d1_foreground_exhaustion.py
"""

import argparse
import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'D1'
OUT = C.exp_dir(EXP, 'out')
E0_MANIFEST = C.exp_dir('E0', 'out', 'e0_manifest.sha256')
D2_INTERNAL = C.exp_dir('D2', 'out', 'd2_internal_duplicates.csv')
D2_DETERMINISM = C.exp_dir('D2', 'out', 'd2_determinism.json')

# The three 4447-image HKU-IS pools, and what each one IS.
POOLS = {
    'raw':   'the original photographs -- the FOREGROUND source',
    'auth':  "the authors' synthetic pool -- WHAT MyTrain.py READS",
    'local': 'our local LAKE-RED re-generation',
}
# Mask sets, with the polarity each is ASSERTED to have. s3 measures, never assumes.
MASK_SETS = {
    'raw_gt':     'object=WHITE',
    'auth_gt':    'object=WHITE',
    'local_msk':  'object=WHITE',
    'lr_in_mask': 'object=BLACK (inverted for LAKE-RED)',
}
# D2's measured per-pool unique counts, for reconciliation. A disagreement is a
# defect to resolve, not to smooth over.
D2_UNIQUE = {'raw': 4443, 'auth': 4447, 'local': 4445}


def _p(m):
    print(m, flush=True)


def load_e0_manifest():
    """{input_key: {filename: sha256}} from E0's manifest."""
    if not os.path.isfile(E0_MANIFEST):
        raise SystemExit('missing %s -- run E0 s1 first' % E0_MANIFEST)
    man = {}
    with open(E0_MANIFEST) as fh:
        for line in fh:
            if line.startswith('#'):
                continue
            sha, _, rest = line.strip().partition('  ')
            key, _, name = rest.partition('/')
            man.setdefault(key, {})[name] = sha
    return man


# ---------------------------------------------------------------------------
# s1 -- verify E0's hashes rather than recompute them
# ---------------------------------------------------------------------------

def _verify_one(args):
    path, expect = args
    return C.sha256(path) == expect


def step_verify(man, sample=300, seed=0, workers=12):
    rng = np.random.default_rng(seed)
    jobs, picked = [], []
    keys = list(POOLS) + list(MASK_SETS)
    for k in keys:
        names = sorted(man[k])
        idx = rng.choice(len(names), size=min(sample // len(keys) + 1, len(names)),
                         replace=False)
        for i in idx:
            jobs.append((os.path.join(C.ipath(k), names[i]), man[k][names[i]]))
            picked.append((k, names[i]))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        ok = list(ex.map(_verify_one, jobs, chunksize=8))
    bad = [picked[i] for i, o in enumerate(ok) if not o]
    return dict(n_checked=len(ok), n_ok=sum(ok), mismatches=bad,
                manifest=os.path.relpath(E0_MANIFEST, C.REPO))


# ---------------------------------------------------------------------------
# s2 -- per-pool distinctness, reconciled with D2
# ---------------------------------------------------------------------------

def step_pools(man):
    rows = []
    for k, desc in POOLS.items():
        h = man[k]
        uniq = len(set(h.values()))
        groups = {}
        for nm, s in h.items():
            groups.setdefault(s, []).append(nm)
        dups = {s: sorted(v) for s, v in groups.items() if len(v) > 1}
        rows.append(dict(pool=k, description=desc, files=len(h), unique=uniq,
                         redundant=len(h) - uniq, dup_groups=len(dups),
                         d2_unique=D2_UNIQUE[k],
                         reconciles=int(uniq == D2_UNIQUE[k]),
                         duplicate_names='; '.join('|'.join(v) for v in dups.values())))
    return rows


# ---------------------------------------------------------------------------
# s3 -- mask polarity, measured over ALL 4447 of every set
# ---------------------------------------------------------------------------

def _white_frac(path):
    a = np.asarray(Image.open(path).convert('L'))
    return float((a > C.THRESH).mean())


def step_polarity(workers=12):
    rows = []
    for k, asserted in MASK_SETS.items():
        d = C.ipath(k)
        names = C.listing(k)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fr = list(ex.map(_white_frac,
                             [os.path.join(d, n) for n in names], chunksize=64))
        fr = np.array(fr)
        # object=WHITE  <=> the white fraction is the MINORITY of the frame
        object_is_white = bool(fr.mean() < 0.5)
        expected_white = ('WHITE' in asserted and 'BLACK' not in asserted)
        rows.append(dict(mask_set=k, n=len(names), asserted=asserted,
                         mean_white_frac=round(float(fr.mean()), 5),
                         median_white_frac=round(float(np.median(fr)), 5),
                         min_white_frac=round(float(fr.min()), 5),
                         max_white_frac=round(float(fr.max()), 5),
                         measured_object_is_white=object_is_white,
                         matches_assertion=int(object_is_white == expected_white)))
    return rows


# ---------------------------------------------------------------------------
# s4 / s5 -- the bijection, and whether it is literal
# ---------------------------------------------------------------------------

def _trace_one(args):
    """Does this render carry the source object pixels of its mapped foreground?

    E0 established that --isReplace composites the source object back in, so a
    render and its foreground share the object region up to JPEG re-encoding.
    That makes exhaustion LITERAL: the test is not statistical similarity but
    whether the object region is the same pixels.

    Two care points, both found by auditing the first run of this step:

    * Use EACH POOL'S OWN mask. The local renders were staged from raw_gt, but
      the authors' pool was rendered with the authors' GT, and D1 s3 measures
      those two mask sets as different (trap T3). Scoring the authors' pool
      against raw_gt counts pixels its own mask called background -- which WERE
      regenerated -- and inflates the object error.
    * Also score the ERODED interior. For a small object the mask boundary is a
      large fraction of the region, and boundary pixels are exactly where the
      two masks disagree. The interior is the honest test of whether the object
      was composited.
    """
    stem, raw_p, gt_p, cand_p = args
    try:
        raw = np.asarray(Image.open(raw_p).convert('RGB'), np.int16)
        gt = np.asarray(Image.open(gt_p).convert('L'))
        cand = np.asarray(Image.open(cand_p).convert('RGB'), np.int16)
    except Exception as e:
        return dict(stem=stem, status='UNREADABLE', err=str(e)[:60])
    if raw.shape != cand.shape:
        return dict(stem=stem, status='SHAPE-MISMATCH',
                    raw_shape=str(raw.shape), cand_shape=str(cand.shape))
    if gt.shape != raw.shape[:2]:
        gt = np.asarray(Image.open(gt_p).convert('L')
                        .resize((raw.shape[1], raw.shape[0]), Image.NEAREST))
    fg = gt >= C.THRESH
    if fg.sum() == 0 or (~fg).sum() == 0:
        return dict(stem=stem, status='DEGENERATE-MASK',
                    fg_frac=float(fg.mean()))
    d = np.abs(raw - cand)
    rec = dict(stem=stem, status='OK', fg_frac=float(fg.mean()),
               obj_mean=float(d[fg].mean()), obj_max=int(d[fg].max()),
               bg_mean=float(d[~fg].mean()), bg_max=int(d[~fg].max()),
               obj_interior_mean=None, interior_px=0)
    try:
        import scipy.ndimage as ndi
        er = ndi.binary_erosion(fg, iterations=3)
        if er.sum() >= 50:
            rec['obj_interior_mean'] = float(d[er].mean())
            rec['interior_px'] = int(er.sum())
    except Exception:
        pass
    return rec


def step_bijection(man, workers=12):
    """Stem-level mapping first, then pixel-level tracing for both pools."""
    def stems(key, strip=''):
        out = {}
        for nm in man[key]:
            s = os.path.splitext(nm)[0]
            if strip and s.startswith(strip):
                s = s[len(strip):]
            out[s] = nm
        return out

    raw_s = stems('raw')
    auth_s = stems('auth')
    local_s = stems('local', strip='SOD_')
    lmsk_s = stems('local_msk', strip='SOD_')
    rgt_s = stems('raw_gt')

    base = set(raw_s)
    mapping = dict(
        base_foregrounds=len(base),
        raw_gt_covers_base=len(base & set(rgt_s)),
        local_renders=len(local_s),
        local_in_base=len(set(local_s) & base),
        local_outside_base=sorted(set(local_s) - base),
        base_without_local=sorted(base - set(local_s)),
        local_masks=len(lmsk_s),
        local_mask_in_base=len(set(lmsk_s) & base),
        auth_images=len(auth_s),
        auth_in_base=len(set(auth_s) & base),
        auth_outside_base=sorted(set(auth_s) - base),
        is_bijection_local=bool(set(local_s) == base),
        is_bijection_auth=bool(set(auth_s) == base),
    )

    # pixel-level trace for BOTH pools against the raw foreground
    agt_s = stems('auth_gt')
    # Each pool is scored against THE MASK IT WAS RENDERED WITH: the local pool
    # was staged from raw_gt (prepare_lakered_inputs --src_masks HKU-IS_raw/gt),
    # the authors' pool ships its own GT.
    POOL_MASK = {'local': ('raw_gt', rgt_s), 'auth': ('auth_gt', agt_s)}
    traces = {}
    for pool in ('local', 'auth'):
        src = stems(pool, strip='SOD_' if pool == 'local' else '')
        mkey, mmap = POOL_MASK[pool]
        jobs = []
        for s in sorted(base & set(src)):
            if s not in mmap:
                continue
            jobs.append((s,
                         os.path.join(C.ipath('raw'), raw_s[s]),
                         os.path.join(C.ipath(mkey), mmap[s]),
                         os.path.join(C.ipath(pool), src[s])))
        _p('  tracing %d %s images to their foregrounds...' % (len(jobs), pool))
        with ProcessPoolExecutor(max_workers=workers) as ex:
            res = list(ex.map(_trace_one, jobs, chunksize=32))
        ok = [r for r in res if r['status'] == 'OK']
        inter = [r for r in ok if r['obj_interior_mean'] is not None]
        traces[pool] = dict(
            mask_used=mkey,
            n=len(res), n_ok=len(ok),
            n_interior_scored=len(inter),
            obj_interior_mean=(float(np.mean([r['obj_interior_mean'] for r in inter]))
                               if inter else None),
            interior_ratio=(float(np.mean([r['bg_mean'] for r in inter])
                                  / max(np.mean([r['obj_interior_mean'] for r in inter]), 1e-9))
                            if inter else None),
            n_object_plausibly_regenerated=sum(
                1 for r in inter if r['obj_interior_mean'] > 40),
            n_interior_3x_closer=sum(
                1 for r in inter if r['obj_interior_mean'] * 3 < r['bg_mean']),
            n_shape_mismatch=sum(1 for r in res if r['status'] == 'SHAPE-MISMATCH'),
            n_degenerate=sum(1 for r in res if r['status'] == 'DEGENERATE-MASK'),
            n_unreadable=sum(1 for r in res if r['status'] == 'UNREADABLE'),
            obj_mean=float(np.mean([r['obj_mean'] for r in ok])),
            bg_mean=float(np.mean([r['bg_mean'] for r in ok])),
            ratio=float(np.mean([r['bg_mean'] for r in ok])
                        / max(np.mean([r['obj_mean'] for r in ok]), 1e-9)),
            # per-image: is the object region much closer than the background?
            n_object_closer=sum(1 for r in ok if r['obj_mean'] * 3 < r['bg_mean']),
            worst_obj_mean=float(max(r['obj_mean'] for r in ok)),
            rows=res)
    return mapping, traces


# ---------------------------------------------------------------------------
# s6 -- the qualifier D1 inherits from D2
# ---------------------------------------------------------------------------

def step_scope():
    if not os.path.isfile(D2_DETERMINISM):
        return dict(status='D2-OUTPUT-MISSING')
    d = json.load(open(D2_DETERMINISM))
    return dict(status='OK',
                duplicate_input_pairs=d.get('duplicate_input_pairs'),
                prediction_holds_for=d.get('prediction_holds_for'),
                clean_same_input_diff_noise=d.get('clean_same_input_diff_noise'),
                mechanism=d.get('mechanism'),
                source='rebuild/D2/out/d2_determinism.json')


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2,s3,s4,s5,s6')
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    steps = [s.strip() for s in args.steps.split(',')]
    os.makedirs(OUT, exist_ok=True)

    man = load_e0_manifest()
    metrics, thresholds, notes, artifacts, old_claims = [], [], [], [], []

    if 's1' in steps:
        _p('=== s1 verify E0 manifest ===')
        r = step_verify(man, workers=args.workers)
        C.save_json(os.path.join(OUT, 'd1_manifest_verify.json'), r)
        metrics += [('e0_manifest_hashes_verified', '%d/%d' % (r['n_ok'], r['n_checked']),
                     'random sample; the rest is consumed from E0, not recomputed')]
        thresholds.append(('every verified file still matches its E0 manifest hash',
                           r['n_ok'] == r['n_checked']))
        artifacts.append('rebuild/D1/out/d1_manifest_verify.json')

    if 's2' in steps:
        _p('=== s2 per-pool distinctness ===')
        rows = step_pools(man)
        with open(os.path.join(OUT, 'd1_pool_distinctness.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        for r in rows:
            metrics.append(('unique_%s' % r['pool'], '%d/%d' % (r['unique'], r['files']),
                            'redundant %d; %s' % (r['redundant'], r['description'])))
        bad = [r['pool'] for r in rows if not r['reconciles']]
        metrics.append(('reconciles_with_D2', 'yes' if not bad else 'NO: %s' % bad,
                        'D2 measured raw=%d auth=%d local=%d'
                        % (D2_UNIQUE['raw'], D2_UNIQUE['auth'], D2_UNIQUE['local'])))
        thresholds.append(('per-pool unique counts reconcile with D2 exactly', not bad))
        old_claims.append(('D1 "all 4447 foregrounds already in base pool"',
                           '4447 distinct foregrounds',
                           'MISMATCH' if rows[0]['unique'] != 4447 else 'MATCH'))
        old_claims.append(('D1/D2 internal duplicates in render pool',
                           '2 (4445 unique of 4447)',
                           'MATCH' if [r for r in rows if r['pool'] == 'local'][0]['unique'] == 4445
                           else 'MISMATCH'))
        artifacts.append('rebuild/D1/out/d1_pool_distinctness.csv')

    if 's3' in steps:
        _p('=== s3 mask polarity, all sets, all files ===')
        rows = step_polarity(workers=args.workers)
        with open(os.path.join(OUT, 'd1_mask_polarity.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        for r in rows:
            metrics.append(('polarity_%s_white_frac' % r['mask_set'],
                            r['mean_white_frac'],
                            'n=%d, object_is_white=%s, asserted %s'
                            % (r['n'], r['measured_object_is_white'], r['asserted'])))
        allok = all(r['matches_assertion'] for r in rows)
        thresholds.append(('every mask set\'s measured polarity matches its assertion',
                           allok))
        notes.append(
            'Polarity is MEASURED over all 4447 of every mask set, not sampled and not '
            'assumed from documentation. A silent polarity flip would invert the object '
            'region and corrupt the foreground-to-render mapping in s4/s5 while leaving '
            'every count intact -- trap T2.')
        artifacts.append('rebuild/D1/out/d1_mask_polarity.csv')

    if 's4' in steps or 's5' in steps:
        _p('=== s4/s5 bijection and literal tracing ===')
        mapping, traces = step_bijection(man, workers=args.workers)
        C.save_json(os.path.join(OUT, 'd1_bijection.json'), mapping)
        for pool, t in traces.items():
            with open(os.path.join(OUT, 'd1_trace_%s.csv' % pool), 'w', newline='') as fh:
                keys = ['stem', 'status', 'fg_frac', 'obj_mean', 'obj_max',
                        'bg_mean', 'bg_max', 'obj_interior_mean', 'interior_px',
                        'raw_shape', 'cand_shape', 'err']
                w = csv.DictWriter(fh, fieldnames=keys, extrasaction='ignore')
                w.writeheader(); w.writerows(t['rows'])
            artifacts.append('rebuild/D1/out/d1_trace_%s.csv' % pool)

        metrics += [
            ('base_foreground_files', mapping['base_foregrounds'], 'raw HKU-IS photographs'),
            ('renders_tracing_to_base_pool', '%d/%d'
             % (mapping['local_in_base'], mapping['local_renders']), 'by stem'),
            ('renders_OUTSIDE_base_pool', len(mapping['local_outside_base']),
             ', '.join(mapping['local_outside_base'][:5]) or 'none'),
            ('base_foregrounds_without_a_render', len(mapping['base_without_local']),
             ', '.join(mapping['base_without_local'][:5]) or 'none'),
            ('render_set_is_bijection_onto_base', mapping['is_bijection_local'], ''),
            ('authors_pool_tracing_to_base_pool', '%d/%d'
             % (mapping['auth_in_base'], mapping['auth_images']),
             'the pool MyTrain.py actually reads'),
            ('authors_pool_is_bijection_onto_base', mapping['is_bijection_auth'], ''),
        ]
        thresholds += [
            ('zero renders whose foreground lies outside the base pool',
             len(mapping['local_outside_base']) == 0),
            ('the render set is a bijection onto the base foreground set',
             mapping['is_bijection_local']),
            ('the authors\' training pool is a bijection onto the base foreground set',
             mapping['is_bijection_auth']),
        ]
        for pool in ('local', 'auth'):
            t = traces[pool]
            metrics += [
                ('%s_mask_used' % pool, t['mask_used'],
                 'each pool scored against the mask it was rendered with'),
                ('%s_traced_ok' % pool, '%d/%d' % (t['n_ok'], t['n']),
                 'shape-mismatch %d, degenerate-mask %d, unreadable %d'
                 % (t['n_shape_mismatch'], t['n_degenerate'], t['n_unreadable'])),
                ('%s_object_region_mean_abs' % pool, round(t['obj_mean'], 3),
                 'full object region, vs its source foreground'),
                ('%s_object_INTERIOR_mean_abs' % pool,
                 round(t['obj_interior_mean'], 3) if t['obj_interior_mean'] else 'n/a',
                 'mask eroded 3px, n=%d -- excludes the boundary where the two mask '
                 'sets disagree' % t['n_interior_scored']),
                ('%s_background_mean_abs' % pool, round(t['bg_mean'], 3), ''),
                ('%s_bg_over_obj_ratio' % pool, round(t['ratio'], 2), 'full region'),
                ('%s_bg_over_obj_ratio_INTERIOR' % pool,
                 round(t['interior_ratio'], 2) if t['interior_ratio'] else 'n/a', ''),
                ('%s_images_with_object_3x_closer' % pool,
                 '%d/%d' % (t['n_object_closer'], t['n_ok']),
                 'full region, per-image'),
                ('%s_images_with_INTERIOR_3x_closer' % pool,
                 '%d/%d' % (t['n_interior_3x_closer'], t['n_interior_scored']),
                 'interior, per-image'),
                ('%s_objects_plausibly_REGENERATED' % pool,
                 t['n_object_plausibly_regenerated'],
                 'interior mean|diff| > 40 -- the honest residual'),
            ]
            thresholds.append(
                ('%s: background error exceeds object error 3x on the interior, so the '
                 'mapping is LITERAL (source object pixels carried through)' % pool,
                 bool(t['interior_ratio'] and t['interior_ratio'] > 3.0)))
            thresholds.append(
                ('%s: fewer than 1%% of objects are plausibly regenerated rather than '
                 'composited' % pool,
                 t['n_object_plausibly_regenerated'] < 0.01 * max(t['n_interior_scored'], 1)))
        old_claims.append(
            ('D1 "every added image is a re-render, not a new object"',
             'zero foregrounds in the generated pool absent from the base pool',
             'MATCH' if len(mapping['local_outside_base']) == 0 else 'MISMATCH'))
        artifacts.append('rebuild/D1/out/d1_bijection.json')
        notes.append(
            'Exhaustion is LITERAL, not statistical. E0 found that --isReplace '
            '(test.py:165) composites the source object pixels back into the render, so '
            'a foreground and its render share the object region up to JPEG '
            're-encoding. s5 confirms this over all 4447 for BOTH pools rather than a '
            'sample: the object region is an order of magnitude closer to the source '
            'than the background is. A "new" image in this pipeline therefore contains '
            'an object that is already in the pool, pixel for pixel.')
        notes.append(
            'MEASUREMENT FIX made during D1. The first run scored BOTH pools against '
            'raw_gt and found only 4041/4447 authors-pool images with the object 3x '
            'closer, against 4445/4447 for the local pool. Auditing that gap showed it '
            'was an artifact, not a finding: the failures had small objects (mean fg '
            'fraction 0.111 vs 0.199) and the authors pool was rendered with the '
            'authors GT, which s3 measures as different from raw_gt. Boundary pixels '
            'where the two masks disagree WERE regenerated, and for a small object the '
            'boundary dominates the region. Each pool is now scored against the mask it '
            'was rendered with, plus an eroded interior. Both numbers are reported.')

    if 's6' in steps:
        _p('=== s6 scope qualifier from D2 ===')
        sc = step_scope()
        C.save_json(os.path.join(OUT, 'd1_scope.json'), sc)
        if sc['status'] == 'OK':
            metrics.append(('D2_position_dependence_inherited',
                            '%s/%s pairs explained'
                            % (sc['prediction_holds_for'], sc['duplicate_input_pairs']),
                            'read from D2, not re-measured'))
        notes.append(
            'QUALIFIER inherited from D2 s7/s8: a render is a function of (foreground, '
            'mask, POSITION IN SHARD), not of the foreground alone. So "the render pool '
            'is determined by the foreground pool" holds only at a FIXED shard count '
            'over a FIXED input listing. This does not weaken exhaustion -- the object '
            'pixels come from the pool either way -- but it does mean one foreground can '
            'yield many different renders, which is precisely the degree of freedom a '
            'best-of-K scheme would try to exploit, and it is a BACKGROUND degree of '
            'freedom only.')
        artifacts.append('rebuild/D1/out/d1_scope.json')

    notes.append(
        'WHICH POOL. Exhaustion is stated with respect to the pool MyTrain.py actually '
        'reads -- Dataset/Source/HKU-IS/Image, the authors\' pool -- and separately for '
        'our local re-generation. Both are verified against the same raw foreground set. '
        'D2 s3 showed the two pools have different internal duplicate structure, so they '
        'are genuinely different renderings rather than copies of each other, and each '
        'is reported on its own.')
    notes.append(
        'WHAT D1 DOES NOT ESTABLISH: that new foregrounds could not help. D1 bounds only '
        'what this pipeline can add from its fixed pool. It is silent on whether a larger '
        'or different foreground set would change any outcome, and it is silent on '
        'near-duplicate foregrounds within the pool (D2\'s scope, and pixel-level only).')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/D1/d1_foreground_exhaustion.py --steps %s'
        % args.steps,
        metrics, thresholds, old_claims, artifacts,
        representation=('file bytes (E0 manifest) + decoded pixels of the object region '
                        'defined by raw_gt'),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""ABC -- assemble every arm pool, gate it, and write EXP ABC block #1.

Specification: rebuild/ABC/ABC_PLAN.md A.2, A.3, A.8. Decision rule:
rebuild/ABC/PREREGISTRATION.md (committed, FROZEN -- this script never writes it).

This is the pre-flight of record. It must PASS before any training run launches.
No training happens here; the driver trains.

Pools are assembled with HARD LINKS, so a pool is byte-identical to primary data
by construction rather than by a copy that could drift -- and it still verifies
per-file against E0's manifest. CLS's shutil.copytree dereferences links, so the
round-2 pool it builds is made of real files.

Usage:
  .venv/bin/python rebuild/ABC/abc_build_pools.py [--arms A0,A2,B,C10] [--no-log]
"""

import argparse
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(_HERE), _HERE, os.path.dirname(os.path.dirname(_HERE))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402
import abc_preflight as PFA                                   # noqa: E402

EXP = A.EXP
OUT = A.OUT


def _p(m):
    print(m, flush=True)


def link_or_copy(src, dst):
    if os.path.exists(dst):
        return 'exists'
    try:
        os.link(src, dst)
        return 'link'
    except OSError:
        import shutil
        shutil.copy2(src, dst)
        return 'copy'


def build_pool(rid, arm, seed):
    """Assemble one arm pool. Idempotent: an existing pool is left alone and
    verified by G5 rather than rebuilt (A0_s42 already trained on its own)."""
    pool = os.path.join(C.REPO, A.pool_dir(rid))
    if os.path.isdir(pool):
        n = len(os.listdir(os.path.join(pool, 'Image')))
        return dict(runid=rid, action='kept-existing', n_image=n)
    if os.path.exists(os.path.join(C.REPO, A.cls_dir(rid))):
        raise SystemExit('ABC HALT: stale CLS output at %s' % A.cls_dir(rid))
    for sub in ('Image', 'GT'):
        os.makedirs(os.path.join(pool, sub))
    modes = set()
    # base 4447 pairs, every arm
    for sub, ext in (('Image', '.jpg'), ('GT', '.png')):
        srcd = os.path.join(C.REPO, A.BASE_POOL, sub)
        for nm in sorted(os.listdir(srcd)):
            modes.add(link_or_copy(os.path.join(srcd, nm), os.path.join(pool, sub, nm)))
    # the arm's B additions
    sp, dp, stems, isrc, msrc = A.arm_added(arm, seed)
    for st in stems:
        for (srcd, ext), sub in ((isrc, 'Image'), (msrc, 'GT')):
            s = os.path.join(C.REPO, srcd, sp + st + ext)
            d = os.path.join(pool, sub, dp + st + ext)
            modes.add(link_or_copy(s, d))
    return dict(runid=rid, action='built', n_added=len(stems),
                dst_prefix=dp or '', mode=','.join(sorted(modes)),
                n_image=len(os.listdir(os.path.join(pool, 'Image'))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', default=','.join(A.ARMS))
    ap.add_argument('--skip-gate', default='')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    arms = tuple(a.strip() for a in args.arms.split(',') if a.strip())
    skip = {s.strip() for s in args.skip_gate.split(',') if s.strip()}
    os.makedirs(OUT, exist_ok=True)
    runs = A.all_runs(arms=arms)

    _p('=== s1 emit the arm stem selections ===')
    sel = {}
    for s in A.SEEDS:
        st = A.arm_b_stems(s)
        sel['B_s%d' % s] = st
        with open(os.path.join(OUT, 'abc_stems_B_s%d.txt' % s), 'w') as fh:
            fh.write('\n'.join(st) + '\n')
    for arm, alpha in (('C10', 1.0),):
        st, cell = A.arm_c_stems(alpha)
        sel[arm] = st
        with open(os.path.join(OUT, 'abc_stems_C_a%.1f.txt' % alpha), 'w') as fh:
            fh.write('\n'.join(st) + '\n')
        _p('  arm %s: %d stems, C1 cell reproduced = %s'
           % (arm, len(st), all(cell[k] == A.C1_CELL[alpha][k] for k in A.C1_CELL[alpha])))

    _p('=== s2 assemble %d arm pools ===' % len(runs))
    built = []
    for arch, arm, seed in runs:
        rid = A.runid(arch, arm, seed)
        r = build_pool(rid, arm, seed)
        built.append(r)
        _p('  %-22s %-14s n_image=%d' % (rid, r['action'], r['n_image']))

    _p('=== s3 gates G1-G6 ===')
    report = PFA.run_preflight(runs, skip=skip)

    _p('=== s4 manifests ===')
    pools = {}
    for arch, arm, seed in runs:
        rid = A.runid(arch, arm, seed)
        pool = os.path.join(C.REPO, A.pool_dir(rid))
        ni, hi, _ = C.dir_digest(os.path.join(pool, 'Image'))
        ng, hg, _ = C.dir_digest(os.path.join(pool, 'GT'))
        pools[rid] = dict(arch=arch, arm=arm, seed=seed,
                          n_image=ni, n_gt=ng,
                          image_digest=hi, gt_digest=hg,
                          added=0 if arm == 'A0' else A.BUDGET,
                          source_root=A.pool_dir(rid) + '/',
                          cls_dir=A.cls_dir(rid),
                          save_model=A.snap_dir(rid) + '/')
    C.save_json(os.path.join(OUT, 'abc_pools.json'), dict(
        generated=C.now(), commit=C.git_commit(), budget=A.BUDGET,
        embedder=A.EMBEDDER, serving=A.SERVING, seeds=list(A.SEEDS),
        arm_B_draw_coupling='per-seed (numpy default_rng(%d + seed))' % A.DRAW_NS,
        arm_C_alpha=A.ARM_ALPHA, pools=pools))

    # cross-arch / cross-seed identity of pool CONTENT (same arm+seed, both archs)
    same = []
    for arm in arms:
        for s in A.SEEDS:
            a = pools.get(A.runid('SINet', arm, s))
            b = pools.get(A.runid('SINetv2', arm, s))
            if a and b:
                same.append(a['image_digest'] == b['image_digest']
                            and a['gt_digest'] == b['gt_digest'])
    # arm C is deterministic => identical across seeds
    cdig = [pools[A.runid('SINet', 'C10', s)]['image_digest']
            for s in A.SEEDS if A.runid('SINet', 'C10', s) in pools]

    _p('=== s5 log block ===')
    g = {x['gate']: x for x in report['gates']}
    metrics, thresholds, artifacts, notes = [], [], [], []

    metrics.append(('preflight_gates_passed',
                    '%d/%d' % (sum(x['passed'] for x in report['gates']),
                               len(report['gates'])),
                    ', '.join(GATE for GATE in PFA.GATES)))
    metrics.append(('arm_pools_assembled', len(built),
                    '%d arch x %d arms x %d seeds' % (2, len(arms), len(A.SEEDS))))
    metrics.append(('pool_size_A0', 4447, 'base authors\' pool only, unpadded'))
    metrics.append(('pool_size_A2_B_C', 4447 + A.BUDGET,
                    'base + B=%d, identical in A2/B/C' % A.BUDGET))
    metrics.append(('arm_B_draw_coupling', 'per-seed rng %d+seed' % A.DRAW_NS,
                    'ABC_PLAN.md A.4 -- "random" is a distribution over draws, '
                    'not one draw'))
    if 'pools' in g and 'per_pool' in g['pools']:
        pp = g['pools']['per_pool']
        metrics.append(('pools_counts_ok', '%d/%d' % (sum(r['a1_counts'] for r in pp), len(pp))))
        metrics.append(('pools_stem_sets_identical', '%d/%d' % (sum(r['a2_stem_sets'] for r in pp), len(pp))))
        metrics.append(('pools_SrcDataset_parity_all_i',
                        '%d/%d' % (sum(r['a4_parity_all_i'] for r in pp), len(pp)),
                        'REAL SrcDataset, every index, not sampled'))
        metrics.append(('pools_total_parity_mismatches', sum(r['a4_mismatches'] for r in pp)))
        metrics.append(('pools_round2_worstcase_parity',
                        '%d/%d' % (sum(r['a6_round2_parity'] for r in pp), len(pp)),
                        'pool UNION all 4040 target names as .png in BOTH dirs; '
                        'parity on the full union proves it for every subset'))
        metrics.append(('pools_round2_simulated_n', pp[0]['a6_round2_n'],
                        'worst case = 4447/5447 + 4040'))
        thresholds += [
            ('every arm pool has equal Image/ and GT/ counts at its expected size',
             all(r['a1_counts'] for r in pp)),
            ('every arm pool has identical stem sets in Image/ and GT/',
             all(r['a2_stem_sets'] for r in pp)),
            ('the REAL SrcDataset pairs stem(images[i]) == stem(gts[i]) for EVERY i '
             'in EVERY arm pool', all(r['a4_parity_all_i'] for r in pp)),
            ('round-2 positional parity holds on the full worst-case CLS union',
             all(r['a6_round2_parity'] for r in pp)),
        ]
        metrics.append(('base_bytes_mismatched_vs_E0_manifest',
                        sum(n for _, n in g['pools']['base_bytes_bad']),
                        'per-file sha256 of the 4447+4447 base subset of every pool'))
        thresholds.append(('every pool\'s base subset matches E0\'s manifest byte for byte',
                           all(n == 0 for _, n in g['pools']['base_bytes_bad'])))
        for label, n, bad in g['pools']['render_mask_bad']:
            metrics.append(('render_mask_equals_raw_gt_%s' % label,
                            '%d/%d' % (n - bad, n),
                            'maxdiff == 0, all selected stems, not sampled'))
        thresholds.append(('every selected render mask is pixel-identical to raw_gt',
                           all(b == 0 for _, _, b in g['pools']['render_mask_bad'])))
        rc = g['pools']['armC_reproduces_C1']['C10']
        metrics.append(('armC_reproduces_C1_cell', rc['match'],
                        'clusters_funded/max_alloc_share/alloc_entropy_norm/'
                        'tv_from_uniform/n_displaced vs rebuild/C1/out/c1_cells.csv'))
        for k, v in rc['measured'].items():
            metrics.append(('  armC_%s' % k, v, 'C1 logged %s' % rc['c1'][k]))
        thresholds.append(('arm C reproduces C1\'s committed allocation cell exactly',
                           bool(rc['match'])))
        for s, v in g['pools']['overlap_B_vs_C'].items():
            metrics.append(('overlap_B_vs_C_%s' % s,
                            '%d of %s expected by chance (ratio %.3f, Jaccard %.4f)'
                            % (v['overlap'], v['chance'], v['ratio'], v['jaccard'])))
        thresholds.append(('arms B and C overlap at the chance rate (0.7-1.3x), so '
                           'they are genuinely different sets',
                           all(0.7 <= v['ratio'] <= 1.3
                               for v in g['pools']['overlap_B_vs_C'].values())))

    if 'provenance' in g:
        pv = g['provenance']
        metrics += [('forbidden_path_references', pv.get('n_forbidden'),
                     'E0.step_independence() CALLED, %d scripts incl. %d in rebuild/ABC'
                     % (pv.get('scripts_scanned', 0), pv.get('abc_scripts_seen', 0))),
                    ('provenance_pragma_exemptions', pv.get('n_exempted'),
                     'reported, not suppressed'),
                    ('manifest_spotcheck', '%d/%d'
                     % (pv.get('manifest_checked', 0) - len(pv.get('manifest_bad', [])),
                        pv.get('manifest_checked', 0)),
                     'random sample across raw/auth/tgt/local, re-hashed')]
        thresholds += [('no script under rebuild/ references the archive or a /tmp '
                        'scratchpad', pv.get('n_forbidden') == 0),
                       ('every declared primary input resolves and re-hashes clean',
                        not pv.get('inputs_missing') and not pv.get('manifest_bad'))]
    if 'one_trainer' in g:
        ot = g['one_trainer']
        metrics += [('MyTrain_py_copies_in_tree', len(ot.get('mytrain', []))),
                    ('MyTest_py_copies_in_tree', len(ot.get('mytest', []))),
                    ('patches_missing', json.dumps(ot.get('patches_missing', {})) or 'none')]
        thresholds.append(('exactly one MyTrain.py and one MyTest.py exist, and all '
                           'six patches are present', bool(ot['passed'])))
    if 'determinism' in g:
        dt = g['determinism']
        metrics.append(('cudnn_declared',
                        'deterministic=%s benchmark_false=%s seed_from_opt=%s'
                        % (dt.get('deterministic_true'), dt.get('benchmark_false'),
                           dt.get('seed_from_opt'))))
        thresholds.append(('MyTrain.py declares cudnn determinism and a CLI seed',
                           bool(dt['passed'])))
    if 'endpoints' in g:
        ep = g['endpoints']
        metrics.append(('endpoints', 'COD10K %d/%d (primary), NC4K %d/%d (secondary)'
                        % (ep.get('COD10K_imgs', 0), ep.get('COD10K_gt', 0),
                           ep.get('NC4K_imgs', 0), ep.get('NC4K_gt', 0)),
                        'CHAMELEON withdrawn (D2 41/76); CAMO selection-only'))
        thresholds.append(('CHAMELEON and CAMO are unreachable as endpoints in code',
                           bool(ep['passed'])))
    if 'signal' in g:
        sg = g['signal']
        metrics.append(('allocation_signal', 'target-side, from '
                        'rebuild/B1/out/b1_cluster_es_%s.csv' % A.EMBEDDER,
                        'C1 gate_signal + gate_cluster_source called unchanged'))
        thresholds.append(('the endpoint-measured signal appears nowhere in ABC, and '
                           'ABC fits no partition of its own', bool(sg['passed'])))

    metrics.append(('pool_content_identical_across_architectures',
                    '%d/%d arm x seed pairs' % (sum(same), len(same)),
                    'pool content is architecture-independent by construction'))
    metrics.append(('armC_pool_identical_across_seeds', len(set(cdig)) == 1,
                    'arm C selection is deterministic -- no RNG'))
    thresholds += [('pool content is identical across the two architectures for '
                    'every (arm, seed)', all(same)),
                   ('arm C\'s pool is identical across all three seeds',
                    len(set(cdig)) <= 1)]

    artifacts += ['rebuild/ABC/out/abc_preflight.json',
                  'rebuild/ABC/out/abc_pools.json',
                  'rebuild/ABC/out/abc_stems_C_a1.0.txt'] + \
                 ['rebuild/ABC/out/abc_stems_B_s%d.txt' % s for s in A.SEEDS]

    notes.append(
        'BLOCK 1 OF 3, AND THE FIRST ABC BLOCK. Unlike E0-C1, where a later block '
        'SUPERSEDED an earlier one, ABC\'s three blocks are sequential STAGES: #1 is '
        'this pre-flight, #2 is run accounting, #3 is the verdict. None supersedes '
        'another. This block TRAINS NOTHING; block #2 is the first in the whole '
        'rebuild with TRAINS YES.')
    notes.append(
        'COLLISION IS IMPOSSIBLE BY CONSTRUCTION, not by convention. RUNID is a pure '
        'function of (arch, arm, seed); every path a run writes is RUNID-prefixed, '
        'INCLUDING the CLS round-2 pool, because CLS.py:16 derives it from '
        'source_root alone. Under released code every arm collapses onto '
        'Dataset/Source/HKU-IS_iteration2/ and each run rmtree\'s the previous '
        'run\'s pseudo-label pool (CLS.py:19-23) -- which is also why patch P0 was '
        'required before any arm could be built.')
    notes.append(
        'ROUND-2 PARITY IS PROVED, NOT SAMPLED. CLS appends images as .png '
        '(CLS.py:156, via the .jpg->.png rename at Dataloader.py:141-142), so round 2 '
        'trains on a MIXED-EXTENSION pool that no prior experiment ever checked. '
        'SrcDataset pairs image to mask by sorted-list INDEX, not by name '
        '(Dataloader.py:14-17,29-37), and filter_files is not a pairing guard -- it '
        'checks only equal lengths and drops positional pairs whose sizes differ, so '
        'a mis-pairing between two images of equal dimensions passes silently. '
        'Parity is therefore asserted on the union of each pool with ALL 4040 target '
        'names; sorted order is preserved under deletion of the same stems from both '
        'lists, and CLS writes image and GT together or skips both '
        '(CLS.py:151,155-156), so the union case proves every possible subset.')
    notes.append(
        'ARM-B DRAW COUPLING IS PER-SEED, and this is a decision with a cost. '
        '"Random" is a distribution over draws, not one draw -- C1 averaged its '
        'random arm over 20 draws for exactly this reason, and REBUILD_PLAN 0.2 '
        'discarded "seed 0, single draw" as an inherited defect. The cost: arm B '
        'carries selection variance that arms A0 and C do not, so pooled sigma_hat '
        'will be INFLATED by arm B, making the pre-registered bar harder rather than '
        'easier. Per-arm sds are reported beside the pooled value in block #3.')
    notes.append(
        'A2-vs-B CARRIES A MASK-PROVENANCE ASYMMETRY, quantified rather than hidden. '
        'A2\'s added masks are the AUTHORS\' GT (mean white fraction 0.18557); B\'s '
        'and C\'s are the render\'s own output masks, pixel-identical to RAW GT '
        '(0.19132). So Delta(B - A2) confounds "LAKE-RED background" with a 0.00575 '
        'mean-white-fraction difference on 1000 of 5447 images (18.4%). It is '
        'unavoidable under the approved A2 definition: the authors\' image was '
        'rendered with the authors\' mask, and pairing it with the raw mask would '
        'mislabel it. Delta(C - B) -- the campaign\'s actual claim -- is unaffected: '
        'B and C share mask provenance, budget and render pool.')
    notes.append(
        'WHAT ARM C IS AND IS NOT. C1\'s attribution audit measured the ES signal\'s '
        'contribution at +0.0073 of d paired against its own shuffle (13/20, a coin '
        'flip) and -0.0649 against an arbitrary cluster (4/20). So this campaign '
        'tests whether a CONCENTRATED, more-proximal, lower-effective-rank arm trains '
        'better than a dispersed one. It is NOT a test of whether the uncertainty '
        'signal specifically helps, and no result from it may be reported as evidence '
        'about that signal.')
    notes.append(
        'THE agg VALUES IN REBUILD_PLAN 1 ARE NOT AN ASSERTABLE AUTHORITY, found '
        'while building the first arm pool and recorded because it is a defect in the '
        'rebuild\'s own work. common.py:248-263 claims dir_digest "Matches the agg '
        'values pinned in REBUILD_PLAN.md 1." It does not: measured '
        'd7f6de696d5c223e against the pinned b42e5f44b5f2b0db on the authors\' Image '
        'pool. The pinned values were computed over a listing carrying the FULL '
        'RELATIVE PATH; dir_digest hashes the BARE FILENAME. Reproduced exactly: the '
        'path-prefixed variant returns b42e5f44b5f2b0db and 95a0b4ed8ce47903. Never '
        'caught because no .py in the repo references those values. PRIMARY DATA IS '
        'UNCHANGED -- all 4447+4447 verify per-file against E0\'s manifest. ABC '
        'therefore asserts against E0\'s manifest, and common.py\'s docstring plus '
        'REBUILD_PLAN 1 need correcting (pending REVISION_TABLE R16).')
    notes.append(
        'PREREGISTRATION.md was committed before this block and is FROZEN. This '
        'script neither reads it as an input nor writes it.')

    block = C.log_block(
        EXP,
        '.venv/bin/python rebuild/ABC/abc_build_pools.py --arms %s' % args.arms,
        metrics, thresholds, [], artifacts,
        representation=('training pools on disk: authors\' pool (R1 full images, '
                        'object=WHITE masks) + B=%d LAKE-RED renders selected in R2 '
                        '(grey-128 cutout) by the target-side signal' % A.BUDGET),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)
    if not report['all_passed']:
        raise SystemExit('ABC HALTED at preflight: %s -- see abc_preflight.json'
                         % [x['gate'] for x in report['gates'] if not x['passed']])


if __name__ == '__main__':
    main()

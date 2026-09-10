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
    ap.add_argument('--tag', default='', help='output namespace; "t2" is additive')
    args = ap.parse_args()
    arms = tuple(a.strip() for a in args.arms.split(',') if a.strip())
    skip = {s.strip() for s in args.skip_gate.split(',') if s.strip()}
    global OUT, EXP
    OUT = A.set_out(args.tag)
    EXP = 'T2' if args.tag == 't2' else A.EXP
    os.makedirs(OUT, exist_ok=True)
    runs = A.all_runs(arms=arms)

    _p('=== s1 emit the arm stem selections ===')
    sel = {}
    for s in A.SEEDS:
        st = A.arm_b_stems(s)
        sel['B_s%d' % s] = st
        with open(os.path.join(OUT, 'abc_stems_B_s%d.txt' % s), 'w') as fh:
            fh.write('\n'.join(st) + '\n')
    for arm in [m for m in arms if m in A.ARM_ALPHA]:
        alpha = A.ARM_ALPHA[arm]
        st, cell = A.arm_c_stems(alpha, A.ARM_ES_PERM[arm])
        sel[arm] = st
        name = ('abc_stems_C_a%.1f.txt' % alpha if A.ARM_ES_PERM[arm] is None
                else 'abc_stems_%s.txt' % arm)
        with open(os.path.join(OUT, name), 'w') as fh:
            fh.write('\n'.join(st) + '\n')
        keys = A.SHAPE_KEYS if A.ARM_ES_PERM[arm] else tuple(A.C1_CELL[alpha])
        _p('  arm %-6s %d stems, perm=%-13s rho=%+.5f  shape reproduced = %s'
           % (arm, len(st), cell['es_perm'], cell['perm_rho'],
              all(cell[k] == A.C1_CELL[alpha][k] for k in keys)))

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
    # every C-family arm is deterministic => identical across all three seeds.
    # Checked per arm actually built, and NON-VACUOUSLY: an empty digest list is a
    # FAIL, not a silent pass (PREREGISTRATION_T2.md T2.5).
    cseed = {}
    for arm in arms:
        if arm in A.ARM_ALPHA:
            dg = [pools[A.runid('SINet', arm, s)]['image_digest']
                  for s in A.SEEDS if A.runid('SINet', arm, s) in pools]
            cseed[arm] = (len(dg), bool(len(dg) == len(A.SEEDS) and len(set(dg)) == 1))

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
        for arm, rc in sorted(g['pools']['armC_reproduces_C1'].items()):
            full = 'n_displaced' in rc['asserted']
            metrics.append(('armC_reproduces_C1_cell_%s' % arm, rc['match'],
                            '%s vs rebuild/C1/out/c1_cells.csv'
                            % '/'.join(rc['asserted'])))
            for k, v in rc['measured'].items():
                metrics.append(('  %s_%s' % (arm, k), v,
                                ('C1 logged %s' % rc['c1'][k]) if k in rc['c1']
                                else 'T2 provenance; not a C1 quantity'))
            thresholds.append((
                'arm %s reproduces C1\'s committed allocation %s' % (
                    arm, 'cell exactly (all five keys)' if full else
                    'SHAPE exactly -- the same-shape assertion, '
                    'n_displaced reported not asserted (PREREGISTRATION_T2.md T2.4)'),
                bool(rc['match'])))
        ovp = g['pools']['overlap_B_vs_C']
        for key, v in sorted(ovp.items()):
            metrics.append(('overlap_%s' % key,
                            '%d of %s expected by chance (ratio %.3f, Jaccard %.4f, '
                            'n_differing %d)'
                            % (v['overlap'], v['chance'], v['ratio'], v['jaccard'],
                               v['n_differing']), v['kind']))
        thresholds.append(('arms B and C overlap at the chance rate (0.7-1.3x), so '
                           'they are genuinely different sets',
                           all(0.7 <= v['ratio'] <= 1.3
                               for v in ovp.values() if v['kind'] == 'BxC')))
        cxc = {k: v for k, v in ovp.items() if v['kind'] == 'CxC'}
        if cxc:
            thresholds.append((
                'no two C-family arms overlap above Jaccard %.2f, so a WITHIN NOISE '
                'result cannot be mechanical (PREREGISTRATION_T2.md T2.7)'
                % A.T2_MAX_JACCARD,
                all(v['jaccard'] <= A.T2_MAX_JACCARD for v in cxc.values())))

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
    for arm, (ndg, okd) in sorted(cseed.items()):
        metrics.append(('armC_pool_identical_across_seeds_%s' % arm, okd,
                        '%d/%d seed digests compared; the selection is '
                        'deterministic -- no RNG' % (ndg, len(A.SEEDS))))
    thresholds += [('pool content is identical across the two architectures for '
                    'every (arm, seed)', all(same)),
                   ('every deterministic C-family arm has an identical pool at all '
                    'three seeds (vacuous pass excluded)',
                    bool(cseed) and all(okd for _, okd in cseed.values()))]

    relout = os.path.relpath(OUT, C.REPO)
    artifacts += [os.path.join(relout, 'abc_preflight.json'),
                  os.path.join(relout, 'abc_pools.json')] + \
                 [os.path.join(relout, f) for f in sorted(os.listdir(OUT))
                  if f.startswith('abc_stems_')]

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

    if args.tag == 't2':
        # T2 is a different experiment with a different claim. A/B/C's narrative
        # notes do not describe it, and two are actively wrong for it: there is no
        # A2 arm here, and "WHAT ARM C IS AND IS NOT" is precisely the disclaimer
        # T2 exists to discharge. Keep only the structural facts about the pool
        # machinery, which hold for any arm.
        notes = [x for x in notes
                 if x.startswith(('COLLISION IS IMPOSSIBLE', 'ROUND-2 PARITY IS PROVED'))]
        notes.append(
            'BLOCK 1 OF 3 OF THE T2 EXTENSION, AND ADDITIVE. '
            'rebuild/ABC/PREREGISTRATION.md and every committed A/B/C artifact are '
            'FROZEN and unaltered by this block. T2 writes only to '
            'rebuild/ABC/out/t2/ and appends EXP T2 blocks here. The three blocks '
            'are sequential STAGES -- #1 pre-flight, #2 run accounting, #3 verdict '
            '-- and none supersedes any ABC block.')
        notes.append(
            'WHAT T2 TESTS, AND WHY IT IS NOT ARM C. C1 measured the ES signal\'s own '
            'contribution at +0.0073 of d against its own shuffle (13/20, a coin '
            'flip) and -0.0649 against an arbitrary cluster (worse in 16 of 20 '
            'cells) -- but only in EMBEDDING-DISTANCE space, which is why A/B/C '
            'disclaimed any reading of arm C as evidence about the signal. T2 is the '
            'direct test on TRAINED ACCURACY: allocation SHAPE held exactly fixed, '
            'signal DIRECTION destroyed (CSHUF) and reversed (CINV).')
        notes.append(
            'SAME SHAPE, DIFFERENT TARGET -- ASSERTED, NOT ASSUMED. Both transforms '
            'are PERMUTATIONS of the committed target_es vector, so softmax_alloc\'s '
            'p is a permutation of C10\'s and entropy / TV / max-share / '
            'clusters-funded are preserved EXACTLY. Measured 0.78644 / 0.49253 / '
            '0.194 / 75 for both new arms, equal to C1\'s committed cell to the fifth '
            'decimal. n_displaced is a CONSEQUENCE of the allocation, so it is '
            'reported and never asserted: 404 (CSHUF) and 367 (CINV) against C10\'s '
            '370.')
        notes.append(
            'A VALUE-SPACE INVERSION WAS REJECTED BEFORE ANY ARM WAS BUILT. Negating '
            'the ES vector and reflecting it (ES_max - ES_c) give an IDENTICAL '
            'allocation here, because softmax_alloc max-subtracts and np.std is '
            'invariant under both: each reduces to min(es) - es. And neither '
            'preserves concentration on a skewed ES vector, so either would have '
            'varied direction AND concentration together, leaving Delta(C10 - CINV) '
            'uninterpretable. The rank-reversing PERMUTATION holds the shape exactly '
            'and still reaches rho = -1.')
        notes.append(
            'CINV HAS EXACTLY ONE FIXED POINT, BY CONSTRUCTION: at odd k the '
            'median-ranked cluster is its own mirror. Mathematically necessary, not '
            'a defect; disclosed in PREREGISTRATION_T2.md T2.3 and reported as '
            'perm_fixed_points = 1, with the other 74 clusters reassigned. The '
            'zero-fixed-point requirement is scoped to CSHUF, whose permutation is '
            'the FIRST of 64 declared draws meeting the rule: seed 910004, '
            'rho = -0.03351.')
        notes.append(
            'THE DISTINCTNESS GATE GUARDS AGAINST MANUFACTURING OUR OWN CONCLUSION. '
            'Under this pre-registration EQUALITY is the SUPPORTING outcome, so two '
            'arms sharing most of their images would fake support rather than test '
            'it. C-vs-C overlap is therefore gated at Jaccard <= 0.50 BEFORE any '
            'training, at zero GPU cost. Measured: C10|CSHUF 0.3774, C10|CINV 0.3236, '
            'CINV|CSHUF 0.3755 -- 452 to 511 of 1000 images differ. B-vs-C pairs stay '
            'at chance (0.91-1.08x), as C1 and A/B/C found.')
        notes.append(
            'SIGNAL PROVENANCE IS EXACT, NOT MERELY HASHED. No hash of '
            'rebuild/B1/out/b1_cluster_es_dinoL518.csv was recorded when C10 was '
            'built -- it appears in no manifest and no preflight JSON, a gap this '
            'block records rather than papers over. Its git blob OID is '
            '3fb4c46677a647e9a396e31cbc2b8f81b016ddd8 at HEAD AND at 065dac6, the '
            'A/B/C block-#1 commit, and exactly one commit ever touched it (470e224, '
            'EXP B1): the file has never been modified since B1 created it. C10 is '
            'reproduced here as a reference arm on all FIVE keys as the downstream '
            'check.')
        notes.append(
            'PREREGISTRATION_T2.md was committed before this block and is FROZEN. '
            'This script neither reads it as an input nor writes it.')

    block = C.log_block(
        EXP,
        '.venv/bin/python rebuild/ABC/abc_build_pools.py --arms %s%s'
        % (args.arms, ' --tag ' + args.tag if args.tag else ''),
        metrics, thresholds, [], artifacts,
        representation=('training pools on disk: authors\' pool (R1 full images, '
                        'object=WHITE masks) + B=%d LAKE-RED renders selected in R2 '
                        '(grey-128 cutout) by %s' % (
                            A.BUDGET,
                            'a PERMUTATION of the target-side signal -- same '
                            'allocation shape, different target cluster'
                            if args.tag == 't2' else 'the target-side signal')),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)
    if not report['all_passed']:
        raise SystemExit('ABC HALTED at preflight: %s -- see abc_preflight.json'
                         % [x['gate'] for x in report['gates'] if not x['passed']])


if __name__ == '__main__':
    main()

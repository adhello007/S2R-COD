#!/usr/bin/env python
"""AN-02 -- realised overlap, foreground identity, pseudo-label sets and theoretical exposure.

Method: ANALYSIS_PRESPEC.md §5. Reads the committed stem lists (this worktree, base 8d1d079) and the
materialised pools / renders in the original working copy (read-only).

Outputs:
  RESULT_TABLES/AN-02_overlap_by_seed.csv
  RESULT_TABLES/AN-02_exposure_by_run.csv
  RESULT_TABLES/AN-02_pseudolabel_overlap.csv
  RESULT_TABLES/AN-02_pool_verification.csv
  RESULT_TABLES/AN-02_hand_inspection.csv
  EXPERIMENT_LOGS/AN-02_summary.json
"""
import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
ap.add_argument('--workers', type=int, default=8)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, os.path.join(WT, 'rebuild'))
import common as C        # noqa: E402  (base; used only for dir_digest definition check)

SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
ARMS = ['B', 'C10', 'CSHUF', 'CINV']
ARCH = {'SINet': dict(steps=253, batch=16, epochs=39, fx_steps=341),
        'SINetv2': dict(steps=127, batch=32, epochs=99, fx_steps=171)}
BASE_N, BUDGET = 4447, 1000
OUT_ABC = os.path.join(WT, 'rebuild/ABC/out')


def sha(p, bs=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(bs), b''):
            h.update(b)
    return h.hexdigest()


def stems_for(arm, seed):
    fn = {'B': 'abc_stems_B_s%d.txt' % seed, 'C10': 'abc_stems_C_a1.0.txt',
          'CSHUF': 'abc_stems_CSHUF.txt', 'CINV': 'abc_stems_CINV.txt'}[arm]
    return [l.strip() for l in open(os.path.join(OUT_ABC, 'se', fn)) if l.strip()]


def inode_digest(path, cache):
    """Reproduces common.dir_digest: sha256 over sorted '<sha256>  <name>\\n'; hashes each inode once."""
    names = sorted(f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
    h = hashlib.sha256()
    for nm in names:
        p = os.path.join(path, nm)
        st = os.stat(p)
        k = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
        if k not in cache:
            cache[k] = sha(p)
        h.update(('%s  %s\n' % (cache[k], nm)).encode())
    return len(names), h.hexdigest(), names


def pool_job(rid):
    cache = {}
    pdir = os.path.join(DR, 'Dataset/Source/ABC', rid)
    ni, hi, names_i = inode_digest(os.path.join(pdir, 'Image'), cache)
    ng, hg, names_g = inode_digest(os.path.join(pdir, 'GT'), cache)
    r2 = pdir + '_iteration2'
    r2_names = sorted(os.listdir(os.path.join(r2, 'Image'))) if os.path.isdir(os.path.join(r2, 'Image')) else None
    return rid, ni, hi, names_i, ng, hg, r2_names


def main():
    t0 = time.time()
    rt = os.path.join(SR, 'RESULT_TABLES')
    pools = json.load(open(os.path.join(OUT_ABC, 'se/abc_pools.json')))['pools']
    runs = list(csv.DictReader(open(os.path.join(OUT_ABC, 'se/abc_runs.csv'))))
    runmeta = {r['runid']: r for r in runs}
    base_stems = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(DR, 'Dataset/Source/HKU-IS_raw/imgs')))
    assert len(base_stems) == BASE_N
    S = {(arm, s): stems_for(arm, s) for arm in ARMS for s in SEEDS}
    for k, v in S.items():
        assert len(v) == BUDGET and len(set(v)) == BUDGET, k

    # ---- 0. dir_digest definition check on one pool (base function vs inode-cached reproduction)
    probe = os.path.join(DR, 'Dataset/Source/ABC/SINet_B_s42/GT')
    n0, h0, _ = C.dir_digest(probe)
    n1, h1, _ = inode_digest(probe, {})
    digest_def_ok = (n0 == n1 and h0 == h1)
    assert digest_def_ok, 'digest reproduction differs from base common.dir_digest'

    # ---- 1. pool verification (all 64 runs)
    rids = sorted(runmeta)
    with Pool(a.workers) as pool:
        pres = {x[0]: x for x in pool.imap_unordered(pool_job, rids)}
    pv, r2sets = [], {}
    for rid in rids:
        _, ni, hi, names_i, ng, hg, r2_names = pres[rid]
        arch, arm, s = rid.split('_')[0], rid.split('_')[1], int(rid.split('_s')[-1])
        inj = sorted(n[4:-4] for n in names_i if n.startswith('SOD_'))
        base_in_pool = sorted(n[:-4] for n in names_i if not n.startswith('SOD_'))
        committed = pools[rid]
        r1_names = set(names_i)
        appended = sorted(n for n in (r2_names or []) if n not in r1_names) if r2_names is not None else None
        r2sets[rid] = appended
        pv.append(dict(runid=rid, architecture=arch, arm=arm, seed=s, n_image=ni, n_gt=ng,
                       image_digest_recomputed=hi, image_digest_committed=committed['image_digest'],
                       gt_digest_recomputed=hg, gt_digest_committed=committed['gt_digest'],
                       digests_match=(hi == committed['image_digest'] and hg == committed['gt_digest']),
                       injected_stems_match_committed_list=(inj == sorted(S[(arm, s)])),
                       base_stems_complete=(base_in_pool == base_stems),
                       round2_pool_present=r2_names is not None,
                       round2_pool_size=len(r2_names) if r2_names is not None else '',
                       round2_appended=len(appended) if appended is not None else '',
                       committed_pool_r2=runmeta[rid]['pool_r2'], committed_n_appended=runmeta[rid]['n_appended'],
                       appended_matches_committed=(appended is not None and len(appended) == int(runmeta[rid]['n_appended']))))

    # ---- 2. overlap by seed for every arm pair (stems identical across architectures)
    ov = []
    exp_rand = BUDGET * BUDGET / BASE_N
    for s in SEEDS:
        for X, Y in itertools.combinations(ARMS, 2):
            I = len(set(S[(X, s)]) & set(S[(Y, s)]))
            one = BUDGET - I
            ov.append(dict(seed=s, arm_x=X, arm_y=Y, intersection=I, one_sided_diff=one,
                           symmetric_diff=2 * one, jaccard=I / (2 * BUDGET - I),
                           frac_injection_differs=one / BUDGET,
                           frac_of_5447_pool_one_sided=one / (BASE_N + BUDGET),
                           frac_of_5447_pool_symmetric=2 * one / (BASE_N + BUDGET),
                           frac_of_union_of_two_pools_symmetric=2 * one / (BASE_N + 2 * BUDGET - I),
                           expected_random_intersection=exp_rand, intersection_over_chance=I / exp_rand,
                           pair_type=('C-family (deterministic, same at every seed)' if 'B' not in (X, Y)
                                      else 'B vs C-family (B redrawn per seed)'),
                           foreground_identity='render stem = base-pool foreground'))
    # B vs B across seeds (how different are two random draws)
    bb = [len(set(S[('B', s1)]) & set(S[('B', s2)])) for s1, s2 in itertools.combinations(SEEDS, 2)]

    # ---- 3. foreground identity / render bytes
    ren_img = os.path.join(DR, 'Dataset/LAKERED/output/HKU-IS/images')
    ren_msk = os.path.join(DR, 'Dataset/LAKERED/output/HKU-IS/masks')
    all_inj = sorted(set().union(*[set(v) for v in S.values()]))
    novel = [st for st in all_inj if st not in set(base_stems)]
    with Pool(a.workers) as pool:
        h_img = dict(zip(base_stems, pool.map(sha, [os.path.join(ren_img, 'SOD_%s.jpg' % st) for st in base_stems])))
        h_msk = dict(zip(base_stems, pool.map(sha, [os.path.join(ren_msk, 'SOD_%s.png' % st) for st in base_stems])))
    dup_img = sum(c - 1 for c in Counter(h_img.values()).values() if c > 1)
    dup_msk = sum(c - 1 for c in Counter(h_msk.values()).values() if c > 1)

    # ---- 4. hand inspection: 12 injected items by the global RNG
    rng = np.random.default_rng(20261111)
    pick = [all_inj[i] for i in sorted(rng.choice(len(all_inj), size=12, replace=False))]
    hi_rows = []
    for st in pick:
        ip, mp = os.path.join(ren_img, 'SOD_%s.jpg' % st), os.path.join(ren_msk, 'SOD_%s.png' % st)
        bp = os.path.join(DR, 'Dataset/Source/HKU-IS/GT', '%s.png' % st)
        im, mk, bg = Image.open(ip), np.array(Image.open(mp).convert('L')), np.array(Image.open(bp).convert('L'))
        same_shape = mk.shape == bg.shape
        hi_rows.append(dict(stem=st, render_image=os.path.relpath(ip, DR), render_size='%dx%d' % im.size,
                            mask_size='%dx%d' % (mk.shape[1], mk.shape[0]), mask_unique_values=len(np.unique(mk)),
                            mask_binary=bool(set(np.unique(mk)).issubset({0, 255})),
                            base_gt_size='%dx%d' % (bg.shape[1], bg.shape[0]),
                            mask_equals_base_gt_pixelwise=bool(same_shape and np.array_equal(mk > 127, bg > 127)),
                            mask_iou_with_base_gt=(float(((mk > 127) & (bg > 127)).sum() / max(1, ((mk > 127) | (bg > 127)).sum()))
                                                   if same_shape else ''),
                            in_arms=' '.join(sorted({arm for (arm, s), v in S.items() if st in set(v)}))))

    # ---- 5. pseudo-label (round-2 appended) overlap between arms at equal seed and architecture
    pl = []
    for arch in ARCH:
        for s in SEEDS:
            for X, Y in itertools.combinations(ARMS, 2):
                ax, ay = r2sets['%s_%s_s%d' % (arch, X, s)], r2sets['%s_%s_s%d' % (arch, Y, s)]
                if ax is None or ay is None:
                    continue
                I = len(set(ax) & set(ay))
                camo = lambda z: sum(1 for n in z if n.startswith('camourflage'))   # noqa: E731
                pl.append(dict(architecture=arch, seed=s, arm_x=X, arm_y=Y, n_x=len(ax), n_y=len(ay),
                               intersection=I, jaccard=I / (len(ax) + len(ay) - I),
                               only_x=len(ax) - I, only_y=len(ay) - I, camo_x=camo(ax), camo_y=camo(ay),
                               note='pseudo-label sets are post-treatment (first-round policy outcome); mediator, not adjusted'))

    # ---- 6. theoretical exposure per run (pinned schedule as executed) + FX-style unpinned reference
    ex = []
    for rid in rids:
        r = runmeta[rid]
        arch, arm, s = r['arch'], r['arm'], int(r['seed'])
        A = ARCH[arch]
        assert int(r['total_step_set']) == A['steps']
        draws = A['steps'] * A['batch']
        p1, p2 = int(r['pool_r1']), int(r['pool_r2'])
        other = {}
        for Y in ARMS:
            if Y != arm:
                other[Y] = BUDGET - len(set(S[(arm, s)]) & set(S[(Y, s)]))
        for rnd, pool_n in ((1, p1), (2, p2)):
            per_item = draws / pool_n
            ex.append(dict(runid=rid, architecture=arch, arm=arm, seed=s, round=rnd, pool_size=pool_n,
                           steps_per_epoch=A['steps'], batch=A['batch'], epochs=A['epochs'],
                           source_draws_per_epoch=draws, source_loader_batches=-(-pool_n // A['batch']),
                           frac_pool_seen_per_epoch=per_item,
                           expected_visits_per_item_per_epoch=per_item,
                           expected_visits_per_item_per_round=per_item * A['epochs'],
                           injected_share_of_draws=BUDGET / pool_n,
                           expected_injected_visits_per_round=BUDGET * per_item * A['epochs'],
                           arm_specific_vs_B=other.get('B', ''), arm_specific_vs_C10=other.get('C10', ''),
                           arm_specific_vs_CSHUF=other.get('CSHUF', ''), arm_specific_vs_CINV=other.get('CINV', ''),
                           arm_specific_share_of_draws_vs_B=(other['B'] / pool_n) if 'B' in other else '',
                           arm_specific_share_of_draws_vs_C10=(other['C10'] / pool_n) if 'C10' in other else '',
                           unpinned_fx_steps_reference=A['fx_steps'] if rnd == 1 else '',
                           unpinned_visits_per_item_per_epoch=(1.0 if rnd == 1 else ''),
                           pseudo_count=r['n_appended'] if rnd == 2 else 0,
                           exposure_status='THEORETICAL (expected under uniform shuffle, truncated epoch); '
                                           'actual per-sample visits UNVERIFIED -- no sampler trace logged'))

    # ---- 7. search for a sampler trace in run logs
    trace_hits = {}
    pat = re.compile(r'(sampler|indices|index|visit|batch_ids|perm)', re.I)
    for rid in rids:
        for lp in (os.path.join(DR, 'Snapshot/ABC', rid, 'training_log.log'), os.path.join(DR, 'rebuild/ABC', rid + '.log')):
            if os.path.isfile(lp):
                n = 0
                with open(lp, errors='replace') as f:
                    for line in f:
                        if pat.search(line):
                            n += 1
                trace_hits[os.path.relpath(lp, DR)] = n

    def wcsv(name, rs):
        with open(os.path.join(rt, name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]))
            w.writeheader()
            for r in rs:
                w.writerow({k: (repr(float(v)) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, np.integer) else v)) for k, v in r.items()})
    wcsv('AN-02_pool_verification.csv', pv)
    wcsv('AN-02_overlap_by_seed.csv', ov)
    wcsv('AN-02_exposure_by_run.csv', ex)
    wcsv('AN-02_pseudolabel_overlap.csv', pl)
    wcsv('AN-02_hand_inspection.csv', hi_rows)

    def summ(X, Y):
        xs = [o for o in ov if o['arm_x'] == X and o['arm_y'] == Y]
        f = [o['frac_injection_differs'] for o in xs]
        g = [o['frac_of_5447_pool_one_sided'] for o in xs]
        return dict(min_frac_differs=min(f), max_frac_differs=max(f), mean_frac_differs=float(np.mean(f)),
                    mean_frac_of_5447=float(np.mean(g)), min_one_sided=min(o['one_sided_diff'] for o in xs),
                    max_one_sided=max(o['one_sided_diff'] for o in xs))
    pairs = {'%s-%s' % p: summ(*p) for p in itertools.combinations(ARMS, 2)}
    per_arm_pl = defaultdict(list)
    for r in runs:
        per_arm_pl[r['arm']].append(int(r['n_appended']))
    summary = dict(
        generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), digest_definition_matches_base=digest_def_ok,
        pools_all_digests_match=all(p['digests_match'] for p in pv),
        pools_all_injected_match=all(p['injected_stems_match_committed_list'] for p in pv),
        pools_all_base_complete=all(p['base_stems_complete'] for p in pv),
        round2_appended_all_match=all(p['appended_matches_committed'] for p in pv),
        pair_summary=pairs, expected_random_intersection=exp_rand,
        B_vs_B_across_seeds_intersection=dict(min=min(bb), max=max(bb), mean=float(np.mean(bb))),
        injected_stems_union=len(all_inj), injected_stems_novel_vs_base_pool=len(novel),
        render_images_byte_duplicates=dup_img, render_masks_byte_duplicates=dup_msk,
        hand_inspection_all_binary=all(h['mask_binary'] for h in hi_rows),
        hand_inspection_mask_equals_base_gt=sum(h['mask_equals_base_gt_pixelwise'] for h in hi_rows),
        pseudo_label_mean_by_arm={k: float(np.mean(v)) for k, v in per_arm_pl.items()},
        pseudo_label_range_by_arm={k: [min(v), max(v)] for k, v in per_arm_pl.items()},
        pseudo_label_audit_targets=dict(B=1977, C10=2025, CSHUF=1990, CINV=1979),
        sampler_trace_search=dict(pattern=pat.pattern, files_scanned=len(trace_hits),
                                  files_with_hits=sum(1 for v in trace_hits.values() if v)),
        seconds=round(time.time() - t0, 1))
    json.dump(summary, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-02_summary.json'), 'w'), indent=1)
    json.dump(trace_hits, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-02_sampler_trace_search.json'), 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()

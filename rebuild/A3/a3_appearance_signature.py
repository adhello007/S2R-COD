#!/usr/bin/env python
"""A3 -- The generator's signature, with honest controls.

Tests whether "LAKE-RED's synthetic output sits far from the real target
distribution" survives the controls that make high real-vs-synthetic
separability a near-truism, and whether LAKE-RED reduces manifold coverage
relative to ITS OWN INPUT POOL.

This is a PORT-AND-REPAIR of the pre-rebuild A3, not a fresh build. The old
script (recoverable at `git show 96fe223^:evidence/a3_appearance_signature.py`)
already carried the full control battery and already demoted its own headline.
It is re-implemented here rather than imported: the rebuild permits exactly one
in-tree implementation, and no resurrected side file. Four defects the rebuild
has since MEASURED are repaired:

  R1  THE TARGET SET SEPARATES FROM ITSELF. Dataset/Target/Image is 3040 COD10K
      + 1000 CAMO (REBUILD_PLAN.md S1), not COD10K-train. The old "sorted-split
      bug" at AUC 0.8888 was that mixture separating from itself -- and the
      split was not even clean (2020 COD10K vs 1020 COD10K + 1000 CAMO, so
      dataset origin was conflated with COD10K's taxonomic filename order). The
      CLEAN COD10K(3040)-vs-CAMO(1000) probe has never been computed. s3 row 5
      computes it. It is the number that inoculates the experiment against
      "your 0.999 is measured against a set that separates from itself at
      0.889".

  R2  AUC CANNOT CARRY THE DECISION. 0.9989 real-vs-LAKE-RED against a 0.9831
      cross-dataset baseline, ceiling 1.0 -- no margin is stateable. The
      decision moves to the PAIRED COVERAGE DELTA (s4), which is immune to the
      real-vs-synthetic truism because it is a within-content intervention:
      the same 4447 foregrounds, the same masks (D1 measured raw_gt and
      local_msk both at 0.19132 white fraction), only the background
      regenerated (E0: object-region error 6.245 vs background 71.676, 11.5x).

  R3  COHEN'S d = 4.67 IS IN-SAMPLE. The old estimator fitted the axis on the
      training half but projected ALL rows, and took abs(). C1 measured that
      this reaches +1.4506 with no real effect against a held-out null of
      -0.1328 (C1_RESULTS.md S8.5). s3 reports four d's per row so the defect
      is visible rather than described, and T8 reproduces C1's demonstration
      in A3's own data.

  R4  THE CONTROL BATTERY MUST REPORT TOGETHER, and the authors' pool -- the
      one MyTrain.py actually reads -- has never been probed
      (REBUILD_PLAN.md S5 item 5). Every synthetic number is reported twice,
      authors' pool and local re-generation, labelled.

Steps:
  s1  preflight   E0 cache shapes, input digests, leaked names, and the
                  index-wise pool alignment the paired delta depends on
  s2  embed       the sets E0 does not have: NC4K, the JPEG sweep, darkening
  s3  probe       the 14-row separability ladder x 3 embedders, four d's each
  s4  coverage    k-NN precision/recall -- THE DECISION (T1)
  s5  distance    polynomial-kernel MMD and C1's spread stats, descriptive
  s6  pixels      the old panel 1, ported over all 4447 and three pools

Consumes E0's caches and manifest, D2's leaked-name contract, and D2_NC4K's
clean-overlap result. Reuses C1's held-out effect-size estimator and spread
statistics BY IMPORT, so method identity cannot drift. Trains nothing: frozen
inference plus logistic probes on frozen features. No optimizer, no checkpoint.

Usage:
  LAKE-RED/.venv/bin/python rebuild/A3/a3_appearance_signature.py
"""

import argparse
import csv
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

sys.path.insert(0, C.exp_dir('C1'))
import c1_targeted_vs_random as C1M                           # noqa: E402
import c1_variance_coverage as C1VC                           # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

EXP = 'A3'
OUT = C.exp_dir(EXP, 'out')
CACHE = C.exp_dir(EXP, 'cache')
E0_CACHE = C.exp_dir('E0', 'cache')
E0_SUMMARY = C.exp_dir('E0', 'out', 'e0_cache_summary.csv')
E0_DIGESTS = C.exp_dir('E0', 'out', 'e0_input_digests.csv')
D2_LEAKED = C.exp_dir('D2', 'out', 'd2_leaked_names.json')
D2_NC4K_TRAIN = C.exp_dir('D2_nc4k', 'out', 'd2nc4k_sweep_train.json')

# All three E0 embedder spaces. Two families, so no conclusion is
# embedder-specific; the coverage direction is judged per space, never blended.
TAGS = ('dinoL224', 'dinoL518', 'clipL224')

# The sets A3 reads from E0's cache, and what each one IS. R1-full whole images
# throughout. `cut` is NEVER loaded: E0 measured it as 82.24% flat grey 128, so
# a probe on cutouts separates on mask geometry, not appearance. It is a
# SELECTION representation (B3/C1's use), meaningless for a distribution
# comparison.
E0_SETS = {
    'tgt':   'the real target domain -- 3040 COD10K + 1000 CAMO, what CSRDA adapts to',
    'raw':   'the original photographs -- LAKE-RED\'s OWN INPUT, the paired baseline',
    'auth':  "the authors' synthetic pool -- WHAT MyTrain.py READS",
    'local': 'our local LAKE-RED re-generation -- WHAT THE ABC CAMPAIGN ADDED',
    'test':  'COD10K-test -- the second null (same dataset, different split)',
}
# The two synthetic pools. Both are reported, always, labelled. E0 measured
# them as genuinely different samples of one generator (0 of 200 identical,
# mean maxdiff 232.3 of 255), so reporting both IS an independent replication.
GEN_POOLS = ('auth', 'local')

JPEG_QUALITIES = (90, 75, 50, 30)
JPEG_ANCHOR = 75            # the old audit's single setting -- the A3.3 anchor
DARKEN_LEVELS = 20          # the old audit's single setting
PR_KS = (3, 5, 10, 20)
PR_K_ANCHOR = 5             # Kynkaanniemi's default and the old A3's choice
PROBE_TEST_FRAC = 0.30
PROBE_SEED = 0

# T1, the PRIMARY rule, declared before the run. See A3.md S5.
MIN_REL_LOSS = 0.15         # recall(gen) must fall >= 15% BELOW recall(raw)
MIN_SPACES = 2              # in at least 2 of the 3 embedder spaces
# T7/T8 bands, inherited from C1 so the two experiments are commensurable.
NULL_D_MAX = 0.30           # a held-out d this small is a genuine null
INSAMPLE_D_MIN = 0.50       # an in-sample d this large proves the old bias
VACUITY_AUC = 0.90          # REBUILD_PLAN.md's declared vacuity trigger

# C1's measured null calibration, CITED for scale -- never recomputed here.
C1_NULL_HELDOUT = -0.1328
C1_NULL_INSAMPLE_MAX = 1.4506

# The old package's values, transcribed from REBUILD_PLAN.md S4 as a FROZEN
# RECORD. A claim under test, never an input, never a baseline, never a target.
OLD = {
    'A3.1': ('Probe AUC real-vs-LAKE-RED', 0.9989),
    'A3.2': ('Probe AUC true null', 0.4781),
    'A3.3': ('Probe AUC JPEG-75', 0.4117),
    'A3.4': ('Probe AUC sorted-split bug', 0.8888),
    'A3.5': ("Cohen's d probe axis", '4.67 / 4.61 / 4.33'),
    'A3.6': ('Recall, LAKE-RED', 0.4662),
    'A3.7': ('Recall, raw HKU-IS', 0.7461),
    'A3.8': ('Generation recall delta', '-0.2799 (-37.5%)'),
}
# Old-log values absent from the frozen S4 table, pinned so they are re-tested
# rather than quietly dropped.
OLD_EXTRA = {
    'precision_lakered': 0.6906,
    'precision_raw_hkuis': 0.6494,
    'ceiling_random_precision': 0.9405,
    'ceiling_random_recall': 0.9370,
    'probe_auc_darkened20': 0.3469,
    'probe_auc_real_vs_raw': 0.9831,
    'bg_luminance_shift': -19.24,
    'fg_bg_corr_real': -0.191,
    'fg_bg_corr_generated': 0.397,
    'fg_bg_corr_authors_pool': 0.399,
}


def _p(m):
    print(m, flush=True)


def _stem(name):
    """Pool-independent foreground identity: drop the render prefix and the
    extension. raw `0004.png`, auth `0004.jpg` and local `SOD_0004.jpg` are
    the same foreground, and s1 asserts that they are at the same ROW INDEX."""
    base = os.path.splitext(name)[0]
    return base[4:] if base.startswith('SOD_') else base


# ---------------------------------------------------------------------------
# s1 -- preflight: everything the rest of A3 assumes, measured
# ---------------------------------------------------------------------------

def step_preflight(tags=TAGS):
    """Verify E0's caches and inputs, resolve D2's leaked names, and assert the
    index-wise pool alignment on which the whole paired coverage delta rests.

    The alignment check is not a formality. s4's headline is a comparison
    between row i of `raw` and row i of a generated pool; if the cache row
    orders ever diverged, that comparison would silently pair different
    foregrounds and the result would look entirely normal.
    """
    if not os.path.isfile(E0_SUMMARY):
        raise SystemExit('missing %s -- run E0 s3 first' % E0_SUMMARY)
    declared = {}
    with open(E0_SUMMARY) as fh:
        for r in csv.DictReader(fh):
            declared[(r['embedder'], r['set'])] = (int(r['n']), int(r['dim']),
                                                   r['repr'])

    shape_bad, repr_bad = [], []
    for tag in tags:
        for sk in E0_SETS:
            key = (tag, sk)
            if key not in declared:
                raise SystemExit('E0 declares no cache for %s/%s' % key)
            n, dim, repr_tag = declared[key]
            a = np.load(os.path.join(E0_CACHE, '%s_%s_cls.npy' % (tag, sk)),
                        mmap_mode='r')
            if a.shape != (n, dim):
                shape_bad.append('%s/%s %s vs declared (%d,%d)'
                                 % (tag, sk, a.shape, n, dim))
            if repr_tag not in ('R1-full', 'R3-render'):
                repr_bad.append('%s/%s repr=%s' % (tag, sk, repr_tag))

    # Names must be identical across embedder spaces, or a per-tag index mask
    # built once would not be valid in another space.
    names = {}
    for tag in tags:
        names[tag] = json.load(open(os.path.join(E0_CACHE,
                                                 '%s_names.json' % tag)))
    ref = names[tags[0]]
    names_agree = all(names[t][sk] == ref[sk] for t in tags for sk in E0_SETS)

    # The pairing precondition (T9).
    align = {}
    base = [_stem(x) for x in ref['raw']]
    for sk in ('auth', 'local'):
        got = [_stem(x) for x in ref[sk]]
        align[sk] = dict(index_wise=sum(1 for a, b in zip(base, got) if a == b),
                         n=len(base), same_set=set(got) == set(base))

    # D2's leaked-name contract: read the file, never carry a name list.
    if not os.path.isfile(D2_LEAKED):
        raise SystemExit('missing %s -- run D2 first' % D2_LEAKED)
    lk = json.load(open(D2_LEAKED))
    leaked = set(lk['target_names_to_exclude'])
    tgt_names = ref['tgt']
    resolved = sum(1 for n in tgt_names if n in leaked)

    # Index masks, all pure name predicates over E0's own listing.
    cod = [i for i, n in enumerate(tgt_names) if n.startswith('COD10K')]
    cam = [i for i, n in enumerate(tgt_names) if n.startswith('camourflage')]
    lkx = [i for i, n in enumerate(tgt_names) if n in leaked]
    keep = [i for i, n in enumerate(tgt_names) if n not in leaked]

    # Input directories still match E0's aggregate digests.
    want = {}
    with open(E0_DIGESTS) as fh:
        for r in csv.DictReader(fh):
            want[r['key']] = (int(r['actual_n']), r['agg'])
    dig_bad = []
    dig_checked = []
    for key in ('tgt', 'raw', 'auth', 'local', 'test', 'nc4k'):
        n_files, agg, _ = C.dir_digest(C.ipath(key))
        dig_checked.append(key)
        if key in want and (n_files, agg) != want[key]:
            dig_bad.append('%s: %d/%s vs E0 %d/%s'
                           % (key, n_files, agg[:16], want[key][0],
                              want[key][1][:16]))

    # D2_NC4K's clean-overlap result, consumed rather than recomputed.
    nc = json.load(open(D2_NC4K_TRAIN)) if os.path.isfile(D2_NC4K_TRAIN) else None

    return dict(shape_bad=shape_bad, repr_bad=repr_bad, names_agree=names_agree,
                align=align, n_leaked=len(leaked), leaked_resolved=resolved,
                idx=dict(cod=cod, cam=cam, leaked=lkx, keep=keep),
                n_tgt=len(tgt_names), digest_bad=dig_bad,
                digest_checked=dig_checked,
                nc4k=None if nc is None else dict(
                    n_nc4k=nc['dir_a']['n'], n_cod_train=nc['dir_b']['n'],
                    contaminated=nc['contaminated']['n'],
                    shortlisted=nc['candidate_pairs_shortlisted'],
                    sweep=nc['tolerance_sweep']))


# ---------------------------------------------------------------------------
# s2 -- embed the control sets E0's cache does not hold
# ---------------------------------------------------------------------------

def _jpeg_loader(quality):
    """Re-encode an identical image at a reduced JPEG quality. The content is
    unchanged, so real-vs-this is a FLOOR: whatever two versions of the same
    picture score is the least any comparison can mean."""
    def load(path):
        im = Image.open(path).convert('RGB')
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=quality)
        buf.seek(0)
        return Image.open(buf).convert('RGB')
    return load


def _dark_loader(levels):
    def load(path):
        a = np.asarray(Image.open(path).convert('RGB')).astype('int16')
        return Image.fromarray(np.clip(a - levels, 0, 255).astype('uint8'))
    return load


def _control_sets():
    """{setkey: (items, loader, loader_description)} for everything fresh."""
    tgt_names = json.load(open(os.path.join(E0_CACHE,
                                            '%s_names.json' % TAGS[0])))['tgt']
    tgt_paths = [os.path.join(C.ipath('tgt'), n) for n in tgt_names]
    nc4k_names = C.listing('nc4k')
    sets = {'nc4k': ([os.path.join(C.ipath('nc4k'), n) for n in nc4k_names],
                     C.load_full, 'R1-full, PIL RGB, unmodified')}
    for q in JPEG_QUALITIES:
        sets['tgt_jpeg%d' % q] = (
            tgt_paths, _jpeg_loader(q),
            'R1-full re-encoded through BytesIO at JPEG quality %d' % q)
    sets['tgt_dark%d' % DARKEN_LEVELS] = (
        tgt_paths, _dark_loader(DARKEN_LEVELS),
        'R1-full with every channel shifted by -%d levels, clipped'
        % DARKEN_LEVELS)
    return sets


def step_embed(tags=TAGS, batch=32, device='cuda'):
    """Write rebuild/A3/cache/ in E0's exact layout.

    The old package's cache key was the caller's name string alone -- it did
    not include the loader or the input list, so two different controls were
    distinguished only by the caller remembering to pass different names. Here
    a sidecar records the loader description and the input count per set, and a
    cache whose sidecar disagrees is rebuilt rather than trusted.
    """
    os.makedirs(CACHE, exist_ok=True)
    sets = _control_sets()
    fresh, reused = [], []
    for tag in tags:
        model = tf = None
        side_p = os.path.join(CACHE, '%s_loaders.json' % tag)
        side = json.load(open(side_p)) if os.path.isfile(side_p) else {}
        names_map = {}
        for sk, (items, loader, desc) in sets.items():
            names_map[sk] = [os.path.basename(p) for p in items]
            cls_p = os.path.join(CACHE, '%s_%s_cls.npy' % (tag, sk))
            pat_p = os.path.join(CACHE, '%s_%s_pat.npy' % (tag, sk))
            stamp = dict(loader=desc, n=len(items))
            ok = (os.path.exists(cls_p) and os.path.exists(pat_p)
                  and side.get(sk) == stamp)
            if ok:
                reused.append('%s/%s' % (tag, sk))
                continue
            if model is None:
                model, tf, meta = C.build_model(tag, device)
                C.save_json(os.path.join(CACHE, '%s_embedder.json' % tag), meta)
            cls, pat = C.embed(
                items, loader, tag=tag, batch=batch, device=device,
                transform=tf, model=model,
                progress=lambda a, b, _t=tag, _s=sk: _p('    %s/%s %d/%d'
                                                        % (_t, _s, a, b)))
            np.save(cls_p, cls)
            np.save(pat_p, pat)
            side[sk] = stamp
            fresh.append('%s/%s' % (tag, sk))
            _p('  %s/%-14s %s  %s' % (tag, sk, cls.shape, desc))
        C.save_json(side_p, side)
        C.save_json(os.path.join(CACHE, '%s_names.json' % tag), names_map)
        if model is not None:
            del model
            import torch
            torch.cuda.empty_cache()
    return dict(fresh=fresh, reused=reused, sets=sorted(sets))


# ---------------------------------------------------------------------------
# The feature bank -- L2 once, centrally, so no downstream site can forget
# ---------------------------------------------------------------------------

def feature_bank(tag, pre, seed=PROBE_SEED):
    """Every named feature matrix A3 compares, in one embedder space.

    Vectors are stored unnormalised by E0 and normalised here exactly once,
    in float64, following C1's convention. The two real-vs-real splits of the
    target set get their own RNG stream: the old package recorded that sharing
    one stream moved the null AUC 0.494 -> 0.529 purely because an earlier
    panel consumed a different number of draws first.
    """
    b = {}
    for sk in E0_SETS:
        b[sk] = C.l2(np.load(os.path.join(E0_CACHE, '%s_%s_cls.npy'
                                          % (tag, sk))).astype(np.float64))
    for sk in ['nc4k'] + ['tgt_jpeg%d' % q for q in JPEG_QUALITIES] \
            + ['tgt_dark%d' % DARKEN_LEVELS]:
        b[sk] = C.l2(np.load(os.path.join(CACHE, '%s_%s_cls.npy'
                                          % (tag, sk))).astype(np.float64))
    idx = pre['idx']
    b['tgt_cod'] = b['tgt'][idx['cod']]          # 3040 -- R1's decomposition
    b['tgt_cam'] = b['tgt'][idx['cam']]          # 1000 -- R1's decomposition
    b['tgt_keep'] = b['tgt'][idx['keep']]        # 4033 -- leak sensitivity

    rng_split = np.random.default_rng(seed + 1)
    order = rng_split.permutation(len(b['tgt']))
    half = len(b['tgt']) // 2
    b['tgt_randA'] = b['tgt'][order[:half]]
    b['tgt_randB'] = b['tgt'][order[half:]]
    # The old package's defect, reproduced deliberately as a LABELLED control.
    # E0's listing is already sorted, so this is the identity permutation --
    # which is exactly why the old "null" was not one.
    b['tgt_sortA'] = b['tgt'][:half]
    b['tgt_sortB'] = b['tgt'][half:]
    return b


# The separability ladder. Order is the reporting order, and the roles are what
# make the headline readable: a number is only interpretable beside its floor.
LADDER = [
    ('real target vs AUTHORS pool (what MyTrain reads)', 'tgt', 'auth', 'headline'),
    ('real target vs LOCAL renders (what ABC added)', 'tgt', 'local', 'headline'),
    ('real target vs raw HKU-IS (LAKE-RED\'s OWN INPUT)', 'tgt', 'raw', 'paired-baseline'),
    ('real target minus 7 leaked vs AUTHORS pool', 'tgt_keep', 'auth', 'leak-sensitivity'),
    ('COD10K 3040 vs CAMO 1000 -- INSIDE the target set', 'tgt_cod', 'tgt_cam', 'self-separation'),
    ('real vs real, RANDOM halves (true null)', 'tgt_randA', 'tgt_randB', 'null'),
    ('real vs real, SORTED halves (the old defect)', 'tgt_sortA', 'tgt_sortB', 'old-defect'),
    ('real vs same images JPEG-90', 'tgt', 'tgt_jpeg90', 'floor'),
    ('real vs same images JPEG-75', 'tgt', 'tgt_jpeg75', 'floor'),
    ('real vs same images JPEG-50', 'tgt', 'tgt_jpeg50', 'floor'),
    ('real vs same images JPEG-30', 'tgt', 'tgt_jpeg30', 'floor'),
    ('real vs same images darkened 20', 'tgt', 'tgt_dark20', 'floor'),
    ('COD10K-train minus 7 vs COD10K-test (second null)', 'tgt_keep', 'test', 'null'),
    ('real target vs NC4K (cross-dataset real-vs-real)', 'tgt', 'nc4k', 'cross-dataset'),
]


# ---------------------------------------------------------------------------
# s3 -- the probe ladder, with four effect sizes per row
# ---------------------------------------------------------------------------

def probe(fa, fb, draw_idx, seed=PROBE_SEED, label='', role=''):
    """Held-out AUC plus FOUR effect sizes, each with a distinct job.

    d_probe_axis_insample  the OLD estimator exactly: logistic axis fitted on
                           the training half, projected over ALL rows, abs().
                           Reported so the 4.67 is reproduced rather than
                           merely asserted to be wrong.
    d_probe_axis_heldout   the direct repair: the SAME logistic axis, but the
                           separation measured only on rows the axis never saw.
    d_meandiff_heldout     C1's estimator, imported. Commensurable with C1's
                           measured null of -0.1328, and signed.
    d_meandiff_insample    C1's in-sample variant, which is what T8 uses to
                           show the bias inside A3's own data.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    X = np.concatenate([fa, fb])
    y = np.concatenate([np.zeros(len(fa)), np.ones(len(fb))])
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=PROBE_TEST_FRAC, random_state=seed, stratify=y)
    clf = LogisticRegression(max_iter=5000).fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    w = clf.coef_[0]
    w = w / np.linalg.norm(w)

    proj_all = X @ w
    d_in = abs(C1M._cohens_d_1d(proj_all[y == 1], proj_all[y == 0]))
    proj_te = Xte @ w
    d_out = abs(C1M._cohens_d_1d(proj_te[yte == 1], proj_te[yte == 0]))

    es = C1M.effect_size(fa, fb, draw_idx)
    return dict(comparison=label, role=role, n_a=len(fa), n_b=len(fb),
                accuracy=float(clf.score(Xte, yte)),
                auc=float(roc_auc_score(yte, p)),
                d_probe_axis_insample=float(d_in),
                d_probe_axis_heldout=float(d_out),
                d_meandiff_heldout=float(es['d_heldout']),
                d_meandiff_insample=float(es['d_insample']),
                norm_dmean=float(es['norm_dmean']))


def step_probe(banks, tags=TAGS):
    rows = []
    for ti, tag in enumerate(tags):
        b = banks[tag]
        for ri, (label, ka, kb, role) in enumerate(LADDER):
            r = probe(b[ka], b[kb], draw_idx=ti * 100 + ri,
                      label=label, role=role)
            r['embedder'] = tag
            rows.append(r)
            _p('  %-10s %-52s AUC %.4f  d_ho %+.2f  d_is %+.2f'
               % (tag, label[:52], r['auc'], r['d_meandiff_heldout'],
                  r['d_meandiff_insample']))
    return rows


# ---------------------------------------------------------------------------
# s4 -- coverage of the target manifold. THE DECISION.
# ---------------------------------------------------------------------------

def precision_recall(real, fake, k, device='cuda'):
    """Kynkaanniemi et al. 2019 improved precision/recall on L2-normalised
    features. precision = share of FAKE inside REAL's k-NN manifold;
    recall = share of REAL inside FAKE's manifold.

    Both sides here are scored against ONE fixed manifold, which is what makes
    the raw-vs-generated comparison a controlled intervention rather than two
    unrelated sets being ranked.
    """
    import torch
    R = torch.as_tensor(real, device=device, dtype=torch.float32)
    F = torch.as_tensor(fake, device=device, dtype=torch.float32)

    def radii(X):
        d = torch.cdist(X, X)
        d.fill_diagonal_(float('inf'))
        return d.kthvalue(min(k, len(X) - 1), dim=1).values

    rR, rF = radii(R), radii(F)
    d = torch.cdist(F, R)
    precision = float((d <= rR[None, :]).any(dim=1).float().mean())
    recall = float((d.T <= rF[None, :]).any(dim=1).float().mean())
    del R, F, d, rR, rF
    torch.cuda.empty_cache()
    return precision, recall


COVER = [
    ("authors' pool", 'tgt', 'auth', 'generated'),
    ('local renders', 'tgt', 'local', 'generated'),
    ('raw HKU-IS (pre-LAKE-RED)', 'tgt', 'raw', 'input-pool'),
    ('NC4K (a different real set)', 'tgt', 'nc4k', 'cross-dataset'),
    ('ceiling, RANDOM halves', 'tgt_randA', 'tgt_randB', 'ceiling'),
    ('ceiling, SORTED halves (old defect)', 'tgt_sortA', 'tgt_sortB', 'ceiling-old'),
    ('COD10K 3040 vs CAMO 1000', 'tgt_cod', 'tgt_cam', 'self-separation'),
]


def step_coverage(banks, tags=TAGS, ks=PR_KS):
    rows = []
    for tag in tags:
        b = banks[tag]
        for k in ks:
            got = {}
            for label, ka, kb, role in COVER:
                prec, rec = precision_recall(b[ka], b[kb], k)
                got[label] = (prec, rec)
                rows.append(dict(embedder=tag, k=k, set=label, role=role,
                                 n_real=len(b[ka]), n_other=len(b[kb]),
                                 precision=prec, recall=rec))
            ceil_rec = got['ceiling, RANDOM halves'][1]
            raw_rec = got['raw HKU-IS (pre-LAKE-RED)'][1]
            for r in rows:
                if r['embedder'] == tag and r['k'] == k:
                    r['recall_share_of_ceiling'] = (r['recall'] / ceil_rec
                                                    if ceil_rec else float('nan'))
                    if r['role'] == 'generated':
                        r['recall_delta_vs_raw'] = r['recall'] - raw_rec
                        r['rel_loss_vs_raw'] = ((raw_rec - r['recall']) / raw_rec
                                                if raw_rec else float('nan'))
                    else:
                        r['recall_delta_vs_raw'] = ''
                        r['rel_loss_vs_raw'] = ''
            _p('  %-10s k=%-3d raw %.4f | auth %.4f | local %.4f | ceiling %.4f'
               % (tag, k, raw_rec, got["authors' pool"][1],
                  got['local renders'][1], ceil_rec))
    return rows


def decide(cov_rows, k=PR_K_ANCHOR):
    """Evaluate T1, the pre-declared coverage rule, per pool and per space.

    The rule is declared on RELATIVE loss rather than an absolute margin
    because absolute recall levels differ between embedder spaces; a fixed
    margin would confound embedder-robustness with scale.
    """
    at_k = [r for r in cov_rows if r['k'] == k]
    raw = {r['embedder']: r['recall'] for r in at_k
           if r['role'] == 'input-pool'}
    ceil = {r['embedder']: r['recall'] for r in at_k if r['role'] == 'ceiling'}
    verdict = {}
    for pool, label in (('auth', "authors' pool"), ('local', 'local renders')):
        cells = []
        for r in at_k:
            if r['set'] != label:
                continue
            rel = (raw[r['embedder']] - r['recall']) / raw[r['embedder']]
            cells.append(dict(embedder=r['embedder'], recall=r['recall'],
                              recall_raw=raw[r['embedder']],
                              ceiling=ceil[r['embedder']], rel_loss=rel,
                              below_raw=r['recall'] < raw[r['embedder']],
                              clears_margin=rel >= MIN_REL_LOSS,
                              below_ceiling=r['recall'] < ceil[r['embedder']]))
        verdict[pool] = dict(
            cells=cells,
            n_clearing=sum(1 for c in cells if c['clears_margin']),
            n_below_raw=sum(1 for c in cells if c['below_raw']),
            n_below_ceiling=sum(1 for c in cells if c['below_ceiling']),
            passes=sum(1 for c in cells if c['clears_margin']) >= MIN_SPACES,
            signs_agree=len({c['recall'] < c['recall_raw'] for c in cells}) == 1)
    verdict['T1'] = all(verdict[p]['passes'] for p in ('auth', 'local'))
    return verdict


# ---------------------------------------------------------------------------
# s5 -- an unsaturated distance, and spread. Descriptive; no threshold.
# ---------------------------------------------------------------------------

def poly_mmd2(A, B, degree=3, device='cuda'):
    """Unbiased polynomial-kernel MMD^2 -- the KID estimator's kernel.

    Chosen over a Frechet distance because it needs no covariance estimate: at
    n ~ 4000 and d = 1024 a 1024x1024 covariance rests on ~4 samples per
    dimension and carries real bias. This is reported as DESCRIPTIVE only. No
    threshold is declared on it, following C1's own finding that swapping in an
    agreeing metric after seeing the data is the move the rebuild exists to
    prevent.
    """
    import torch
    X = torch.as_tensor(A, device=device, dtype=torch.float32)
    Y = torch.as_tensor(B, device=device, dtype=torch.float32)
    d = X.shape[1]
    m, n = len(X), len(Y)

    def kmean_offdiag(P, Q, same):
        G = ((P @ Q.T) / d + 1.0) ** degree
        # float64 ACCUMULATION, deliberately. A naive float32 sum over ~1.6e7
        # kernel values of magnitude ~1 loses exactly the low-order bits that
        # MMD^2 -- a difference of three such means -- is made of.
        if same:
            tot = (G.sum(dtype=torch.float64)
                   - G.diagonal().sum(dtype=torch.float64))
            return float(tot / (len(P) * (len(P) - 1)))
        return float(G.sum(dtype=torch.float64) / (len(P) * len(Q)))

    kxx = kmean_offdiag(X, X, True)
    kyy = kmean_offdiag(Y, Y, True)
    kxy = kmean_offdiag(X, Y, False)
    del X, Y
    torch.cuda.empty_cache()
    return kxx + kyy - 2.0 * kxy


def step_distance(banks, tags=TAGS):
    rows = []
    for tag in tags:
        b = banks[tag]
        for label, ka, kb, role in LADDER:
            rows.append(dict(embedder=tag, comparison=label, role=role,
                             mmd2=poly_mmd2(b[ka], b[kb])))
        for pool in GEN_POOLS + ('raw',):
            s = C1VC.spread_stats(b[pool], b['tgt'])
            rows.append(dict(embedder=tag, comparison='SPREAD %s vs target' % pool,
                             role='spread', mmd2='',
                             trace_ratio=s['trace_ratio'],
                             eff_rank_pool=s['eff_rank_A'],
                             eff_rank_target=s['eff_rank_R'],
                             eff_rank_ratio=s['eff_rank_ratio']))
        _p('  %-10s MMD2 auth %.5f | local %.5f | raw %.5f | COD-vs-CAMO %.5f'
           % (tag,
              [r['mmd2'] for r in rows if r['embedder'] == tag
               and r['role'] == 'headline'][0],
              [r['mmd2'] for r in rows if r['embedder'] == tag
               and r['role'] == 'headline'][1],
              [r['mmd2'] for r in rows if r['embedder'] == tag
               and r['role'] == 'paired-baseline'][0],
              [r['mmd2'] for r in rows if r['embedder'] == tag
               and r['role'] == 'self-separation'][0]))
    return rows


# ---------------------------------------------------------------------------
# s6 -- panel 1, ported: pixel statistics over all 4447 and three pools
# ---------------------------------------------------------------------------

PX_FIELDS = ['stem'] + ['%s_%s' % (t, f) for t in ('real', 'gen', 'auth')
                        for f in ('fg_lum', 'bg_lum', 'bg_r', 'bg_g', 'bg_b')]


def _pixel_one(stem):
    """Mask-restricted foreground/background statistics for one foreground, in
    all three pools. The mask is the same in every pool, so the regions are
    directly comparable -- which is the whole point."""
    import cv2
    raw_d, gt_d = C.ipath('raw'), C.ipath('raw_gt')
    img_r = cv2.imread(os.path.join(raw_d, stem + '.png'))
    img_g = cv2.imread(os.path.join(C.ipath('local'), 'SOD_' + stem + '.jpg'))
    gt = cv2.imread(os.path.join(gt_d, stem + '.png'), cv2.IMREAD_GRAYSCALE)
    if img_r is None or img_g is None or gt is None:
        return None
    if img_g.shape[:2] != img_r.shape[:2]:
        img_g = cv2.resize(img_g, (img_r.shape[1], img_r.shape[0]))
    fg = gt > 127                                  # object=WHITE in raw_gt
    if fg.sum() < 16 or (~fg).sum() < 16:
        return None
    img_a = cv2.imread(os.path.join(C.ipath('auth'), stem + '.jpg'))
    if img_a is not None and img_a.shape[:2] != img_r.shape[:2]:
        img_a = cv2.resize(img_a, (img_r.shape[1], img_r.shape[0]))
    rec = {f: '' for f in PX_FIELDS}
    rec['stem'] = stem
    pools = [('real', img_r), ('gen', img_g)]
    if img_a is not None:
        pools.append(('auth', img_a))
    for tag, im in pools:
        rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype('float64')
        grey = rgb.mean(axis=2)
        rec['%s_fg_lum' % tag] = float(grey[fg].mean())
        rec['%s_bg_lum' % tag] = float(grey[~fg].mean())
        for ci, cname in enumerate('rgb'):
            rec['%s_bg_%s' % (tag, cname)] = float(rgb[~fg, ci].mean())
    return rec


def step_pixels(workers=12):
    stems = sorted(os.path.splitext(f)[0] for f in C.listing('raw'))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = [r for r in ex.map(_pixel_one, stems, chunksize=32)
                if r is not None]

    def col(tag, field):
        return np.array([r['%s_%s' % (tag, field)] for r in rows
                         if r['%s_%s' % (tag, field)] != ''], dtype=float)

    def pearson(tag):
        x, y = col(tag, 'fg_lum'), col(tag, 'bg_lum')
        return float(np.corrcoef(x, y)[0, 1])

    st = dict(n=len(rows),
              bg_lum_real=float(col('real', 'bg_lum').mean()),
              bg_lum_gen=float(col('gen', 'bg_lum').mean()),
              corr_real=pearson('real'), corr_gen=pearson('gen'))
    auth = [r for r in rows if r['auth_fg_lum'] != '']
    st['n_auth'] = len(auth)
    st['bg_lum_auth'] = float(col('auth', 'bg_lum').mean()) if auth else float('nan')
    st['corr_auth'] = pearson('auth') if auth else float('nan')
    st['bg_lum_shift'] = st['bg_lum_gen'] - st['bg_lum_real']
    for tag in ('real', 'gen', 'auth'):
        st['r2_%s' % tag] = st['corr_%s' % tag] ** 2
    for cname in 'rgb':
        st['bg_%s_shift' % cname] = float(np.mean(
            [r['gen_bg_%s' % cname] - r['real_bg_%s' % cname] for r in rows]))
    return st, rows


# ---------------------------------------------------------------------------

def _v(x, digits=4):
    return ('%.*f' % (digits, x)) if isinstance(x, float) else str(x)


def _tol(got, want, tol):
    return 'MATCH' if abs(got - want) <= tol else 'MISMATCH'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2,s3,s4,s5,s6')
    ap.add_argument('--tags', default=','.join(TAGS))
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--batch', type=int, default=32)
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    steps = [s.strip() for s in args.steps.split(',')]
    tags = tuple(t.strip() for t in args.tags.split(','))
    os.makedirs(OUT, exist_ok=True)

    metrics, thresholds, notes, artifacts, old_claims = [], [], [], [], []
    t8 = None          # filled by s3; the global notes explain its outcome

    # ---- s1 --------------------------------------------------------------
    _p('=== s1 preflight ===')
    pre = step_preflight(tags)
    C.save_json(os.path.join(OUT, 'a3_preflight.json'),
                {k: v for k, v in pre.items() if k != 'idx'})
    artifacts.append('rebuild/A3/out/a3_preflight.json')
    metrics += [
        ('e0_cache_shape_mismatches', len(pre['shape_bad']),
         'all %d embedder x set caches A3 reads, against e0_cache_summary.csv'
         % (len(tags) * len(E0_SETS))),
        ('e0_cache_names_agree_across_embedders', pre['names_agree'],
         'a per-tag index mask would be invalid otherwise'),
        ('input_digests_verified', '%d checked, %d mismatched'
         % (len(pre['digest_checked']), len(pre['digest_bad'])),
         'aggregate sha256 per directory vs e0_input_digests.csv'),
        ('target_set_composition', '%d COD10K + %d CAMO = %d'
         % (len(pre['idx']['cod']), len(pre['idx']['cam']), pre['n_tgt']),
         'Dataset/Target/Image is a TWO-DATASET MIXTURE -- the R1 repair'),
        ('d2_leaked_names_resolved', '%d/%d'
         % (pre['leaked_resolved'], pre['n_leaked']),
         'read from D2 s output; A3 carries no name list'),
        ('leaked_all_inside_COD10K',
         set(pre['idx']['leaked']) <= set(pre['idx']['cod']),
         'so the 4033 row only shrinks the COD10K side'),
    ]
    for sk, a in pre['align'].items():
        metrics.append(('pool_alignment_raw_vs_%s' % sk,
                        '%d/%d' % (a['index_wise'], a['n']),
                        'index-wise stem identity -- the paired coverage delta '
                        'compares row i of raw with row i of %s' % sk))
    if pre['nc4k']:
        n = pre['nc4k']
        metrics.append(('nc4k_overlap_with_COD10K_train',
                        '%d/%d contaminated, %d pairs shortlisted'
                        % (n['contaminated'], n['n_nc4k'], n['shortlisted']),
                        'CONSUMED from D2_NC4K, not recomputed; its axis was '
                        'NC4K vs the %d COD10K-train images' % n['n_cod_train']))
    thresholds += [
        ('every E0 cache A3 reads matches its declared shape',
         not pre['shape_bad']),
        ('E0 cache names are identical across all embedder spaces',
         pre['names_agree']),
        ('every input directory still matches its E0 aggregate digest',
         not pre['digest_bad']),
        ('T9 raw/auth/local are index-wise aligned 4447/4447 (the paired '
         'coverage delta depends on it)',
         all(a['index_wise'] == a['n'] for a in pre['align'].values())),
        ('all 7 D2 leaked names resolve against E0 s target listing',
         pre['leaked_resolved'] == pre['n_leaked']),
    ]

    # ---- s2 --------------------------------------------------------------
    if 's2' in steps:
        _p('=== s2 embed control sets ===')
        em = step_embed(tags, batch=args.batch)
        metrics += [
            ('control_sets_embedded', len(em['sets']),
             ', '.join(em['sets'])),
            ('fresh_embeddings_computed', len(em['fresh']),
             'the rest read from rebuild/A3/cache/ (%d reused)'
             % len(em['reused'])),
        ]

    banks = None
    if any(s in steps for s in ('s3', 's4', 's5')):
        _p('=== loading feature banks ===')
        banks = {t: feature_bank(t, pre) for t in tags}
        for t in tags:
            _p('  %s: %s' % (t, ' '.join('%s=%d' % (k, len(v))
                                         for k, v in sorted(banks[t].items()))))

    # ---- s3 --------------------------------------------------------------
    pr_rows = None
    if 's3' in steps:
        _p('=== s3 separability ladder ===')
        pr_rows = step_probe(banks, tags)
        with open(os.path.join(OUT, 'a3_probe_table.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(pr_rows[0].keys()))
            w.writeheader()
            w.writerows(pr_rows)
        artifacts.append('rebuild/A3/out/a3_probe_table.csv')

        def row(label_frag, tag):
            return next(r for r in pr_rows if r['embedder'] == tag
                        and label_frag in r['comparison'])

        for tag in tags:
            for frag, name in (('AUTHORS pool', 'authpool'),
                               ('LOCAL renders', 'local'),
                               ('OWN INPUT', 'rawinput'),
                               ('COD10K 3040 vs CAMO', 'SELFSEP_cod_vs_camo'),
                               ('RANDOM halves', 'null_random'),
                               ('SORTED halves', 'old_sorted_defect'),
                               ('NC4K', 'crossdataset_nc4k'),
                               ('JPEG-75', 'floor_jpeg75'),
                               ('darkened 20', 'floor_dark20')):
                r = row(frag, tag)
                metrics.append(('AUC_%s_%s' % (name, tag), _v(r['auc']),
                                'n %d vs %d; role %s' % (r['n_a'], r['n_b'],
                                                         r['role'])))
        # The AUC ladder, per space, in one readable line each.
        for tag in tags:
            floors = [r['auc'] for r in pr_rows
                      if r['embedder'] == tag and r['role'] == 'floor']
            metrics.append(
                ('AUC_LADDER_%s' % tag,
                 'floors %.4f-%.4f < self-separation %.4f < cross-dataset '
                 '%.4f < LAKE-RED %.4f/%.4f'
                 % (min(floors), max(floors),
                    row('COD10K 3040 vs CAMO', tag)['auc'],
                    row('NC4K', tag)['auc'],
                    row('AUTHORS pool', tag)['auc'],
                    row('LOCAL renders', tag)['auc']),
                 'JPEG+dark floors | COD10K-vs-CAMO inside the target | NC4K | '
                 'authors/local. SATURATED at the top -- describes, decides nothing'))
        # The four d's, on the headline and on the null.
        for tag in tags:
            r = row('LOCAL renders', tag)
            metrics.append(
                ('D_headline_local_%s' % tag,
                 'meandiff held-out %+.3f | meandiff in-sample %+.3f | '
                 'probe-axis held-out %.3f | probe-axis in-sample %.3f'
                 % (r['d_meandiff_heldout'], r['d_meandiff_insample'],
                    r['d_probe_axis_heldout'], r['d_probe_axis_insample']),
                 'R3. The old 4.67 was the probe-axis IN-SAMPLE estimator'))
            n = row('RANDOM halves', tag)
            metrics.append(
                ('D_null_random_%s' % tag,
                 'meandiff held-out %+.4f | meandiff in-sample %+.4f'
                 % (n['d_meandiff_heldout'], n['d_meandiff_insample']),
                 'C1 measured -0.1328 held-out and up to +1.4506 in-sample'))
            metrics.append(
                ('D_null_OLD_ESTIMATOR_%s' % tag,
                 'probe-axis in-sample %.4f | same axis held out %.4f'
                 % (n['d_probe_axis_insample'], n['d_probe_axis_heldout']),
                 'THE disqualifying measurement: this is the estimator that '
                 'produced 4.67, run on a TRUE NULL. Whatever it reports here '
                 'it manufactured from nothing'))
            metrics.append(
                ('D_null_insample_inflation_%s' % tag,
                 'probe-axis %+.4f | meandiff %+.4f'
                 % (n['d_probe_axis_insample'] - n['d_probe_axis_heldout'],
                    n['d_meandiff_insample'] - n['d_meandiff_heldout']),
                 'in-sample minus held-out on a true null -- an OBSERVATION, '
                 'not promoted to a threshold (C1 R14)'))
        metrics.append(
            ('C1_null_calibration_cited', 'held-out %.4f | in-sample max %.4f'
             % (C1_NULL_HELDOUT, C1_NULL_INSAMPLE_MAX),
             'from C1, for scale beside A3 s own null -- not recomputed here'))

        for tag in tags:
            worst = max((r for r in pr_rows if r['embedder'] == tag
                         and r['role'] == 'floor'), key=lambda r: r['auc'])
            xd = row('NC4K', tag)
            ss = row('COD10K 3040 vs CAMO', tag)
            metrics.append(
                ('VACUITY_floor_vs_real_controls_%s' % tag,
                 'worst floor "%s" %.4f vs cross-dataset NC4K %.4f vs '
                 'self-separation %.4f -> floor %s the cross-dataset control'
                 % (worst['comparison'].split('images ')[-1], worst['auc'],
                    xd['auc'], ss['auc'],
                    'EXCEEDS' if worst['auc'] > xd['auc'] else 'stays below'),
                 'the sharpest form of the vacuity argument, and only the '
                 'quality SWEEP reveals it -- the old single setting missed it'))

        nulls = [row('RANDOM halves', t) for t in tags]
        floors_all = [r for r in pr_rows if r['role'] == 'floor']
        t8 = dict(passed=all(r['d_meandiff_insample'] > INSAMPLE_D_MIN
                             for r in nulls),
                  md=[r['d_meandiff_insample'] for r in nulls],
                  pax=[r['d_probe_axis_insample'] for r in nulls],
                  pax_ho=[r['d_probe_axis_heldout'] for r in nulls])
        thresholds += [
            ('T3 the true null is genuine, |AUC - 0.5| <= 0.05 in every space',
             all(abs(r['auc'] - 0.5) <= 0.05 for r in nulls)),
            ('T4 the old sorted-split defect reproduces, AUC > 0.75',
             all(row('SORTED halves', t)['auc'] > 0.75 for t in tags)),
            ('T5 the clean COD10K-vs-CAMO self-separation probe is computed and '
             'reported beside the headline',
             all(np.isfinite(row('COD10K 3040 vs CAMO', t)['auc'])
                 for t in tags)),
            ('T6 VACUITY FLAG: some identity-preserving control exceeds AUC 0.90',
             any(r['auc'] > VACUITY_AUC for r in floors_all)),
            ('T7 the held-out d on random halves is a genuine null, |d| < 0.30',
             all(abs(r['d_meandiff_heldout']) < NULL_D_MAX for r in nulls)),
            ('T8 the in-sample d on random halves exceeds 0.50 -- reproducing '
             'C1 s demonstration in A3 s own data, which is what disqualifies '
             'the old 4.67',
             all(r['d_meandiff_insample'] > INSAMPLE_D_MIN for r in nulls)),
        ]
        old_claims += [
            ('A3.1 %s (local pool, %s)' % (OLD['A3.1'][0], tags[0]),
             OLD['A3.1'][1],
             _tol(row('LOCAL renders', tags[0])['auc'], OLD['A3.1'][1], 0.01)),
            ('A3.1 same claim, AUTHORS pool (never probed before)',
             OLD['A3.1'][1], 'NEW'),
            ('A3.2 %s (exact value is a property of the draw)' % OLD['A3.2'][0],
             OLD['A3.2'][1],
             _tol(row('RANDOM halves', tags[0])['auc'], OLD['A3.2'][1], 0.05)),
            ('A3.2 restated as the property that matters, |AUC-0.5| <= 0.05',
             '0.5',
             'MATCH' if all(abs(r['auc'] - 0.5) <= 0.05 for r in nulls)
             else 'MISMATCH'),
            ('A3.3 %s' % OLD['A3.3'][0], OLD['A3.3'][1],
             _tol(row('JPEG-75', tags[0])['auc'], OLD['A3.3'][1], 0.05)),
            ('A3.4 %s -- reproduced here as a LABELLED control' % OLD['A3.4'][0],
             OLD['A3.4'][1],
             _tol(row('SORTED halves', tags[0])['auc'], OLD['A3.4'][1], 0.05)),
            ('A3.4 the CLEAN split it conflated: COD10K 3040 vs CAMO 1000',
             'never computed', 'NEW'),
            ('A3.5 %s -- REPRODUCED with the old in-sample estimator'
             % OLD['A3.5'][0], '4.67 (L/224 arm)',
             _tol(row('LOCAL renders', tags[0])['d_probe_axis_insample'],
                  4.67, 0.20)),
            ('A3.5 %s -- as a FINDING, in-sample logistic axis' % OLD['A3.5'][0],
             OLD['A3.5'][1], 'SUPERSEDED'),
            ('A3.5 sub-value 4.61 was dinoB/224', '4.61',
             'NOT-REPRODUCIBLE'),
            ('old-log probe AUC real vs raw HKU-IS', OLD_EXTRA['probe_auc_real_vs_raw'],
             _tol(row('OWN INPUT', tags[0])['auc'],
                  OLD_EXTRA['probe_auc_real_vs_raw'], 0.03)),
            ('old-log probe AUC darkened-20', OLD_EXTRA['probe_auc_darkened20'],
             _tol(row('darkened 20', tags[0])['auc'],
                  OLD_EXTRA['probe_auc_darkened20'], 0.10)),
        ]

    # ---- s4 --------------------------------------------------------------
    if 's4' in steps:
        _p('=== s4 coverage (THE DECISION) ===')
        cov = step_coverage(banks, tags)
        with open(os.path.join(OUT, 'a3_coverage.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(cov[0].keys()))
            w.writeheader()
            w.writerows(cov)
        artifacts.append('rebuild/A3/out/a3_coverage.csv')
        dec = decide(cov, PR_K_ANCHOR)
        C.save_json(os.path.join(OUT, 'a3_decision.json'), dec)
        artifacts.append('rebuild/A3/out/a3_decision.json')

        for pool in GEN_POOLS:
            for c in dec[pool]['cells']:
                metrics.append(
                    ('COVERAGE_%s_%s' % (pool, c['embedder']),
                     'recall %.4f vs raw %.4f -> delta %+.4f, relative loss '
                     '%.1f%% (ceiling %.4f)'
                     % (c['recall'], c['recall_raw'],
                        c['recall'] - c['recall_raw'], 100 * c['rel_loss'],
                        c['ceiling']),
                     'k=%d, paired: same foregrounds, same masks, only the '
                     'background regenerated' % PR_K_ANCHOR))
            metrics.append(
                ('COVERAGE_RULE_%s' % pool,
                 '%d/%d spaces clear the %.0f%% margin -> %s'
                 % (dec[pool]['n_clearing'], len(dec[pool]['cells']),
                    100 * MIN_REL_LOSS, 'PASS' if dec[pool]['passes'] else 'FAIL'),
                 'T1 requires >= %d of 3' % MIN_SPACES))
        # k sensitivity, so the anchor is not load-bearing on its own.
        for pool, label in (('auth', "authors' pool"), ('local', 'local renders')):
            for tag in tags:
                by_k = []
                for k in PR_KS:
                    g = next(r for r in cov if r['embedder'] == tag
                             and r['k'] == k and r['set'] == label)
                    rw = next(r for r in cov if r['embedder'] == tag
                              and r['k'] == k and r['role'] == 'input-pool')
                    by_k.append('k%d %+.1f%%' % (k, -100 * (rw['recall']
                                                            - g['recall'])
                                                 / rw['recall']))
                metrics.append(('COVERAGE_k_sweep_%s_%s' % (pool, tag),
                                ' | '.join(by_k),
                                'relative loss vs raw at every k -- the anchor '
                                'is k=%d' % PR_K_ANCHOR))

        ceil = [r for r in cov if r['role'] == 'ceiling' and r['k'] == PR_K_ANCHOR]
        ceil_old = [r for r in cov if r['role'] == 'ceiling-old'
                    and r['k'] == PR_K_ANCHOR]
        metrics.append(('ceiling_random_split_%s' % tags[0],
                        'precision %.4f / recall %.4f'
                        % (ceil[0]['precision'], ceil[0]['recall']),
                        'the CORRECTED ceiling -- real vs real, random halves'))
        metrics.append(('ceiling_SORTED_split_%s' % tags[0],
                        'precision %.4f / recall %.4f'
                        % (ceil_old[0]['precision'], ceil_old[0]['recall']),
                        'the old defect s ceiling, reproduced so the '
                        '0.871 -> 0.937 correction is visible'))

        thresholds += [
            ('T1 PRIMARY: recall(generated) falls >= %.0f%% below recall(raw '
             'HKU-IS) in >= %d of 3 embedder spaces, for BOTH synthetic pools'
             % (100 * MIN_REL_LOSS, MIN_SPACES), dec['T1']),
            ('T2 recall(generated) is below the random-split ceiling in every '
             'cell',
             all(c['below_ceiling'] for p in GEN_POOLS
                 for c in dec[p]['cells'])),
            ('T10 the coverage-delta sign is identical in all three embedder '
             'spaces (embedder-robustness)',
             all(dec[p]['signs_agree'] for p in GEN_POOLS)),
        ]
        g_local = next(c for c in dec['local']['cells']
                       if c['embedder'] == tags[0])
        old_claims += [
            ('A3.6 %s' % OLD['A3.6'][0], OLD['A3.6'][1],
             _tol(g_local['recall'], OLD['A3.6'][1], 0.03)),
            ('A3.6 same claim, AUTHORS pool (never probed before)',
             OLD['A3.6'][1], 'NEW'),
            ('A3.7 %s' % OLD['A3.7'][0], OLD['A3.7'][1],
             _tol(g_local['recall_raw'], OLD['A3.7'][1], 0.03)),
            ('A3.8 %s' % OLD['A3.8'][0], OLD['A3.8'][1],
             _tol(g_local['recall'] - g_local['recall_raw'], -0.2799, 0.05)),
            ('old-log ceiling, random split (precision/recall)',
             '%.4f / %.4f' % (OLD_EXTRA['ceiling_random_precision'],
                              OLD_EXTRA['ceiling_random_recall']),
             _tol(ceil[0]['recall'], OLD_EXTRA['ceiling_random_recall'], 0.03)),
            ('old-log precision, LAKE-RED', OLD_EXTRA['precision_lakered'],
             _tol(next(r for r in cov if r['embedder'] == tags[0]
                       and r['k'] == PR_K_ANCHOR
                       and r['set'] == 'local renders')['precision'],
                  OLD_EXTRA['precision_lakered'], 0.03)),
            ('old-log precision, raw HKU-IS', OLD_EXTRA['precision_raw_hkuis'],
             _tol(next(r for r in cov if r['embedder'] == tags[0]
                       and r['k'] == PR_K_ANCHOR
                       and r['role'] == 'input-pool')['precision'],
                  OLD_EXTRA['precision_raw_hkuis'], 0.03)),
        ]

    # ---- s5 --------------------------------------------------------------
    if 's5' in steps:
        _p('=== s5 distance and spread (descriptive) ===')
        dist = step_distance(banks, tags)
        fields = sorted({k for r in dist for k in r})
        with open(os.path.join(OUT, 'a3_distance.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields, restval='')
            w.writeheader()
            w.writerows(dist)
        artifacts.append('rebuild/A3/out/a3_distance.csv')
        for tag in tags:
            def m(role, i=0):
                return [r['mmd2'] for r in dist if r['embedder'] == tag
                        and r['role'] == role][i]
            metrics.append(
                ('MMD2_LADDER_%s' % tag,
                 'floors %.5f-%.5f | self-separation %.5f | cross-dataset '
                 '%.5f | raw input %.5f | authors %.5f | local %.5f'
                 % (min(r['mmd2'] for r in dist if r['embedder'] == tag
                        and r['role'] == 'floor'),
                    max(r['mmd2'] for r in dist if r['embedder'] == tag
                        and r['role'] == 'floor'),
                    m('self-separation'), m('cross-dataset'),
                    m('paired-baseline'), m('headline', 0), m('headline', 1)),
                 'unbiased polynomial-kernel MMD^2, degree 3. UNSATURATED, '
                 'unlike AUC. Descriptive -- no threshold declared'))
            sp = [r for r in dist if r['embedder'] == tag and r['role'] == 'spread']
            metrics.append(
                ('SPREAD_vs_target_%s' % tag,
                 ' | '.join('%s eff-rank %.1f vs %.1f (ratio %.3f)'
                            % (r['comparison'].split()[1], r['eff_rank_pool'],
                               r['eff_rank_target'], r['eff_rank_ratio'])
                            for r in sp),
                 'C1 s spread_stats, imported. Descriptive, no threshold -- '
                 'C1 found that promoting an agreeing metric post hoc is the '
                 'move the rebuild exists to prevent'))

    # ---- s6 --------------------------------------------------------------
    if 's6' in steps:
        _p('=== s6 pixel statistics (secondary) ===')
        px, px_rows = step_pixels(args.workers)
        with open(os.path.join(OUT, 'a3_pixel_stats.csv'), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['key', 'value'])
            for k, v in sorted(px.items()):
                w.writerow([k, round(v, 6) if isinstance(v, float) else v])
        # Fixed fieldnames: the old package derived them from row 0, so a first
        # row without the authors' pool silently dropped those columns for all.
        with open(os.path.join(OUT, 'a3_pixel_per_image.csv'), 'w',
                  newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=PX_FIELDS, restval='')
            w.writeheader()
            w.writerows(px_rows)
        artifacts += ['rebuild/A3/out/a3_pixel_stats.csv',
                      'rebuild/A3/out/a3_pixel_per_image.csv']
        metrics += [
            ('bg_luminance_real', _v(px['bg_lum_real'], 2),
             'mask-restricted, n=%d' % px['n']),
            ('bg_luminance_local_render', _v(px['bg_lum_gen'], 2), 'same images'),
            ('bg_luminance_authors_pool', _v(px['bg_lum_auth'], 2),
             'n=%d' % px['n_auth']),
            ('bg_luminance_shift', _v(px['bg_lum_shift'], 2), 'local - real'),
            ('bg_channel_shift_rgb', '%.2f %.2f %.2f'
             % (px['bg_r_shift'], px['bg_g_shift'], px['bg_b_shift']),
             'local - real'),
            ('fg_bg_colour_corr_real', _v(px['corr_real'], 3),
             'R2 %.3f' % px['r2_real']),
            ('fg_bg_colour_corr_local', _v(px['corr_gen'], 3),
             'R2 %.3f' % px['r2_gen']),
            ('fg_bg_colour_corr_authors', _v(px['corr_auth'], 3),
             'R2 %.3f -- an INDEPENDENT generator run, so this is a '
             'replication rather than a repeat' % px['r2_auth']),
        ]
        thresholds.append(
            ('the foreground->background colour correlation flips sign from '
             'the real photographs to BOTH generated pools',
             px['corr_real'] < 0 < px['corr_gen']
             and px['corr_real'] < 0 < px['corr_auth']))
        old_claims += [
            ('old-log bg luminance shift', OLD_EXTRA['bg_luminance_shift'],
             _tol(px['bg_lum_shift'], OLD_EXTRA['bg_luminance_shift'], 1.0)),
            ('old-log fg->bg corr, real', OLD_EXTRA['fg_bg_corr_real'],
             _tol(px['corr_real'], OLD_EXTRA['fg_bg_corr_real'], 0.05)),
            ('old-log fg->bg corr, local render',
             OLD_EXTRA['fg_bg_corr_generated'],
             _tol(px['corr_gen'], OLD_EXTRA['fg_bg_corr_generated'], 0.05)),
            ('old-log fg->bg corr, authors pool',
             OLD_EXTRA['fg_bg_corr_authors_pool'],
             _tol(px['corr_auth'], OLD_EXTRA['fg_bg_corr_authors_pool'], 0.05)),
        ]

    # ---- notes -----------------------------------------------------------
    notes.append(
        'WHAT A3 IS. A characterization of the synthetic-vs-real DISTRIBUTION. '
        'It is NOT a training-utility bound and must not be read as one: a '
        'distant or low-coverage synthetic set can still improve a model, and '
        'the ABC arm means in fact rose monotonically in all four architecture '
        'x endpoint cells. A3 supplies a candidate mechanism CONSISTENT WITH '
        'the absence of a resolvable gain; it does not demonstrate that no '
        'gain exists.')
    notes.append(
        'WHY IT CARRIES WEIGHT ANYWAY. A3 is deterministic over fixed vectors '
        '-- there is no seed spread and no sigma-hat. The ABC campaign is '
        'underpowered against its own pre-registered statement (2 sigma-hat = '
        '0.017933 on the primary endpoint, larger than the 0.0142 gap the '
        'design declared it could half-resolve), so a null from ABC cannot '
        'stand alone. A3 is the only measurement in the rebuild that speaks to '
        'synthetic-vs-real distance and does not depend on power.')
    notes.append(
        'THE DECISION RESTS ON COVERAGE, NOT AUC. Read the AUC ladder as '
        'description only. It is SATURATED at the top: the identity-preserving '
        'floors sit near chance, the cross-dataset and self-separation controls '
        'and the headline all crowd into the top few hundredths of the scale, '
        'and the ceiling is 1.0. No margin is stateable there, which is why T1 '
        'was declared on the paired coverage delta before the run.')
    notes.append(
        'WHY THE PAIRED DELTA IS NOT APPLES-TO-ORANGES. The objection is that '
        'raw HKU-IS is salient-object photography while LAKE-RED output is '
        'camouflage-style renders, so their recalls measure different '
        'manifolds. It does not apply, and the reason is measured rather than '
        'argued: the comparison is a WITHIN-CONTENT INTERVENTION. The same '
        '4447 foregrounds in bijection (T9 asserts index-wise alignment); the '
        'same masks (D1 measured raw_gt and local_msk both at 0.19132 white '
        'fraction, agreeing to five decimals); the same single target manifold '
        'on both sides; and only the background regenerated (E0 measured the '
        'isReplace split at object-region error 6.245 vs background 71.676, a '
        '11.5x ratio, re-derived independently by D2 s7 at 0.962 vs 41.667). '
        'One manipulated variable, one fixed manifold.')
    notes.append(
        'THE TARGET SET IS A MIXTURE, AND THAT IS THE R1 REPAIR. '
        'Dataset/Target/Image is 3040 COD10K + 1000 CAMO. The headline is '
        'reported against all 4040 because that is what CSRDA adapts to and '
        'what every ABC run read, but the COD10K-vs-CAMO self-separation probe '
        'is reported in the SAME table, because a real-vs-real comparison '
        'inside the target set is the bar the headline has to clear. The old '
        'package computed a version of this number, got 0.8888, and filed it '
        'as a bug in its own null control instead of recognising it as a '
        'measurement of the target set s heterogeneity. Its split was also not '
        'clean -- sorted order gave 2020 COD10K against 1020 COD10K + 1000 '
        'CAMO, and COD10K filenames are ordered taxonomically, so dataset '
        'origin and taxonomy were conflated. The clean 3040-vs-1000 probe here '
        'is new.')
    notes.append(
        'BOTH SYNTHETIC POOLS, ALWAYS. The authors pool is what MyTrain.py '
        'reads (its S2C default source_root, plus Image/); the local renders '
        'are what the ABC campaign actually added on top of it. E0 measured '
        'the two as genuinely different samples of one generator -- 0 of 200 '
        'identical, mean maxdiff 232.3 of 255 -- so agreement between them is '
        'an independent replication, not a repeat. Every old A3 number came '
        'from the local pool alone; the authors pool is probed here for the '
        'first time.')
    notes.append(
        'MANIFOLD-ESTIMATION CAVEATS, STATED. k-NN precision/recall is an '
        'estimate whose value depends on k, so k is swept over 3/5/10/20 and '
        'the anchor k=5 is declared rather than chosen after the fact. It also '
        'depends on L2 normalisation, which is applied here and is OUR STATED '
        'CHOICE -- the original sources never said whether they normalised. '
        'Recall of a manifold is a distributional statement and is not a bound '
        'on supervision value. MMD is kernel-dependent (degree-3 polynomial, '
        'the KID kernel) and is reported without a threshold. A Frechet '
        'distance was considered and declined: at n ~ 4000 with d = 1024 the '
        'covariance rests on about four samples per dimension.')
    notes.append(
        'SCOPE OF THE NC4K CONTROL. D2_NC4K measured NC4K against the 3040 '
        'COD10K-train images and found the overlap empty at every level, so '
        'the cross-dataset row carries no leakage confound on that axis. The '
        'CAMO 1000 side of the target set was NOT part of that check, so the '
        'cleanliness claim is scoped to the COD10K axis. NC4K is also not in '
        'E0 s cache; it is embedded here into rebuild/A3/cache/ with E0 s '
        'declared pipeline, not a re-derived one.')
    notes.append(
        'THE 7 LEAKED NAMES. Read from D2 s output, never typed here. The '
        'headline uses all 4040 and a 4033 row is reported beside it; the '
        'exclusion is immaterial there (7 of 4040, and D2 measured that '
        'removing them moves MAE by 1.242e-05). It is MANDATORY on the '
        'COD10K-test row, where those 7 are exact duplicates of test images '
        'and would otherwise place identical rows on both sides of a '
        'real-vs-real control.')
    if t8 is not None and not t8['passed']:
        notes.append(
            'T8 IS LEFT FAILING RATHER THAN RELAXED. T8 was declared on C1 s '
            'IMPORTED mean-difference estimator, for commensurability with C1 s '
            'published null. On A3 s true null that estimator reports in-sample '
            '%s -- below the declared 0.50, so T8 FAILS. The reason is sample '
            'size, not a contradiction: C1 measured its +0.6991 mean over '
            'subsets of B = 250..3000 and its own range reached down to '
            '+0.2144, whereas A3 s null splits 4040 into two halves of ~2020, '
            'at the large end where the in-sample bias is smallest. '
            'CRUCIALLY, THE DISQUALIFICATION OF 4.67 DOES NOT DEPEND ON T8. '
            'The old figure came from the LOGISTIC probe axis, not the '
            'mean-difference axis, and that estimator reports %s on the same '
            'true null against %s for the held-out version of itself. A number '
            'near 0.7 manufactured from two random halves of one dataset is '
            'what makes 4.67 uninterpretable. Following C1 R14, the declared '
            'threshold is reported FAILED and the agreeing measurement is '
            'reported beside it as an OBSERVATION, not swapped in as a '
            'replacement threshold.'
            % (' / '.join('%+.4f' % v for v in t8['md']),
               ' / '.join('%.4f' % v for v in t8['pax']),
               ' / '.join('%.4f' % v for v in t8['pax_ho'])))
    notes.append(
        'THE IDENTITY-PRESERVING FLOORS CAN SIT BELOW CHANCE, and that is the '
        'correct behaviour rather than a defect. When two sets carry the same '
        'content the probe has no separable signal to find, so it fits noise '
        'in the training half and generalises worse than chance on the held-out '
        'half. An AUC below 0.5 on a floor row therefore reads as "no signal", '
        'not as "inverted signal".')
    notes.append(
        'THREE REPORTING METRICS WERE ADDED AFTER AN EXPLORATORY --no-log PASS '
        'on one embedder space: the old estimator s behaviour on the true null, '
        'the in-sample inflation gap, and the floor-versus-real-control '
        'comparison. Disclosed here per C1 R15. All three are METRICS, not '
        'thresholds -- no declared threshold was added, weakened or removed '
        'after seeing data, and all three are recomputable from the committed '
        'probe table.')
    notes.append(
        'WHAT REPLACES THE OLD 4.67. The old Cohen s d fitted a logistic axis '
        'on the training half, then projected EVERY row onto it and took the '
        'absolute value. C1 measured that estimator: with no real effect at '
        'all the in-sample d reaches +1.4506, against a held-out null of '
        '-0.1328. So the old figure is superseded rather than merely disputed. '
        'Four d s are reported per row -- the old estimator (so the 4.67 is '
        'reproduced, not asserted away), the same logistic axis held out, and '
        'C1 s imported mean-difference estimator in both variants. T8 requires '
        'the in-sample null to exceed 0.5 inside A3 s own data, which makes '
        'the supersession a measurement.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/A3/a3_appearance_signature.py '
        '--steps %s' % args.steps,
        metrics, thresholds, old_claims, artifacts,
        representation=('R1-full whole images for every set (E0 cache for '
                        'tgt/raw/auth/local/test, rebuild/A3/cache for '
                        'NC4K + JPEG sweep + darkening); CLS token, L2 at use '
                        'time; the R2 grey-128 cutout cache is NEVER read'),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

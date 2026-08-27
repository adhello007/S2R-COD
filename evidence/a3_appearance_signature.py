"""A3 -- Generated-vs-real appearance signature, with the controls that matter.

=============================================================================
GOAL
    Show that "a linear probe separates real COD from LAKE-RED output at AUC
    0.999" -- which reads as damning evidence of a generator ceiling -- is very
    nearly a truism, by putting it beside controls that score almost as high on
    images that differ trivially.

WHY IT MATTERS -- how this fits the argument
    This experiment does NOT support one of the four load-bearing conclusions.
    It does the opposite job, and that is why it is in the package: it is where
    we demote our own headline. Two of the characterization paper's flagship
    numbers collapse here (revisions R-c..R-f). Reporting the AUC without the
    controls would have been the single most reviewer-vulnerable claim we had.

    What survives is a reframing, not a number: the style gap is real but
    unremarkable, and its consequence -- that coverage-counting is inverse-ranked
    by feasibility -- is the finding worth keeping (measured in B2).

METHOD -- three panels, each with its control
    Panel 1  PIXEL STATISTICS. Background brightness and per-channel shift,
             generated vs real, over the mask; plus the foreground->background
             colour correlation, which flips sign between real and generated.
    Panel 2  LINEAR PROBE with four controls. Logistic regression on DINOv2 CLS
             features, 70/30 split. real-vs-generated is reported beside: a
             real-vs-real RANDOM split (the true null), real vs raw HKU-IS (two
             ordinary datasets), real vs the same images JPEG-75 recompressed,
             and real vs the same images darkened 20 levels. The buggy
             SORTED-FILENAME split is reproduced too, so the original defect is
             visible rather than merely described.
    Panel 3  GENERATIVE PRECISION/RECALL (Kynkaanniemi et al. 2019, k=5 NN
             manifold) for LAKE-RED output AND for the raw HKU-IS pool it
             starts from, against a random-split real-vs-real ceiling.

SOURCES REPRODUCED
    STAGE_C_MEASUREMENTS.md sections 2 and 6.2/6.3;
    STAGE_C_RED_TEAM_AUDIT.md sections 5(a) and 5(b) [R7], [R8].

REVISIONS SURFACED -- four, all of them ours
    R-c  the real-vs-real "null control" split target features in SORTED
         FILENAME order, so it separated COD10K from CAMO -- a dataset
         comparison, not a null. Ceiling 0.893/0.871 -> 0.946/0.939.
    R-d  LAKE-RED recall as a share of achievable: 54% -> 49.6%.
    R-e  the mechanistic claim that ~20-level background darkening drives the
         style axis is RETRACTED (darkening control lands at AUC 0.32).
    R-f  AUC 0.9989 is demoted from evidence to near-vacuous.

TRAINS ANYTHING?
    NO. A logistic-regression probe on frozen features is not model training,
    and the embedder runs in inference mode only.

USAGE
    LAKE-RED/.venv/bin/python evidence/a3_appearance_signature.py
    ... --pixel-sample 800      # images for panel 1 (default 800)
    ... --no-log                # print the block, do not write it
=============================================================================
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

TGT_DIR = 'Dataset/Target/Image'
GEN_DIR = 'Dataset/LAKERED/output/HKU-IS/images'
RAW_DIR = 'Dataset/Source/HKU-IS_raw/imgs'      # the ORIGINAL HKU-IS photographs
RAW_GT = 'Dataset/Source/HKU-IS_raw/gt'
AUTH_DIR = 'Dataset/Source/HKU-IS/Image'        # the AUTHORS' released synthetic pool
# Three distinct pools, easy to confuse and consequential if confused:
#   HKU-IS_raw/imgs        the real photographs LAKE-RED starts from
#   Source/HKU-IS/Image    the authors' released LAKE-RED output -- what TRAINING reads
#   LAKERED/output/...     our own local re-generation from the same foregrounds
# PRIOR_REVIEW.md 0.5 names the middle one "Source/HKU-IS (authors')" and the last
# "LAKERED/local". They are NOT byte-identical (maxdiff 240) and not even close in
# feature space (cos 0.62-0.91), i.e. two independent samples of the same generator.

JPEG_QUALITY = 75      # the audit's control setting
DARKEN_LEVELS = 20     # the audit's control setting
PR_K = 5               # k-NN manifold for precision/recall
PROBE_TEST_FRAC = 0.30

# expected values, from the sources named in the docstring
EXPECT = {
    'auc_real_vs_gen': 0.9989, 'auc_null_random': 0.5289,
    'auc_real_vs_raw': 0.9831, 'auc_jpeg75': 0.9380, 'auc_dark20': 0.3204,
    'd_probe_L224': 4.70,
    'prec_gen': 0.691, 'rec_gen': 0.466,
    'prec_raw': 0.649, 'rec_raw': 0.745,
    'prec_ceiling': 0.946, 'rec_ceiling': 0.939,
    'corr_real': -0.36, 'corr_gen': 0.45,
}


# --------------------------------------------------------------------------
# panel 1 -- pixel statistics
# --------------------------------------------------------------------------
def panel1_pixels(repo, stems, rng):
    """Background brightness and foreground->background colour correlation.

    Real = raw HKU-IS (the pre-generation image); generated = the LAKE-RED
    output for the same stem. The mask is the same in both cases, so foreground
    and background regions are directly comparable.
    """
    import cv2
    import numpy as np
    rows = []
    for stem in stems:
        img_r = cv2.imread(os.path.join(repo, RAW_DIR, stem + '.png'))
        img_g = cv2.imread(os.path.join(repo, GEN_DIR, 'SOD_' + stem + '.jpg'))
        gt = cv2.imread(os.path.join(repo, RAW_GT, stem + '.png'),
                        cv2.IMREAD_GRAYSCALE)
        if img_r is None or img_g is None or gt is None:
            continue
        if img_g.shape[:2] != img_r.shape[:2]:
            img_g = cv2.resize(img_g, (img_r.shape[1], img_r.shape[0]))
        fg = gt > 127                                   # object=white in raw gt
        if fg.sum() < 16 or (~fg).sum() < 16:
            continue
        img_a = cv2.imread(os.path.join(repo, AUTH_DIR, stem + '.jpg'))
        if img_a is not None and img_a.shape[:2] != img_r.shape[:2]:
            img_a = cv2.resize(img_a, (img_r.shape[1], img_r.shape[0]))
        rec = {'stem': stem}
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
        rows.append(rec)

    def pearson(xs, ys):
        x, y = np.asarray(xs), np.asarray(ys)
        return float(np.corrcoef(x, y)[0, 1])

    stats = {
        'n': len(rows),
        'bg_lum_real': float(np.mean([r['real_bg_lum'] for r in rows])),
        'bg_lum_gen': float(np.mean([r['gen_bg_lum'] for r in rows])),
        'corr_real': pearson([r['real_fg_lum'] for r in rows],
                             [r['real_bg_lum'] for r in rows]),
        'corr_gen': pearson([r['gen_fg_lum'] for r in rows],
                            [r['gen_bg_lum'] for r in rows]),
    }
    auth = [r for r in rows if 'auth_fg_lum' in r]
    if auth:
        stats['n_auth'] = len(auth)
        stats['bg_lum_auth'] = float(np.mean([r['auth_bg_lum'] for r in auth]))
        stats['corr_auth'] = pearson([r['auth_fg_lum'] for r in auth],
                                     [r['auth_bg_lum'] for r in auth])
        stats['r2_auth'] = stats['corr_auth'] ** 2
    stats['bg_lum_shift'] = stats['bg_lum_gen'] - stats['bg_lum_real']
    stats['r2_real'] = stats['corr_real'] ** 2
    stats['r2_gen'] = stats['corr_gen'] ** 2
    if not auth:
        stats['n_auth'] = 0
        stats['bg_lum_auth'] = stats['corr_auth'] = stats['r2_auth'] = float('nan')
    for cname in 'rgb':
        stats['bg_%s_shift' % cname] = float(
            np.mean([r['gen_bg_%s' % cname] - r['real_bg_%s' % cname]
                     for r in rows]))
    return stats, rows


# --------------------------------------------------------------------------
# panel 2 -- linear probe
# --------------------------------------------------------------------------
def probe(fa, fb, seed, label=''):
    """Logistic regression between two feature sets. Returns acc, AUC, and
    Cohen's d of the two class means along the fitted probe axis."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    X = np.concatenate([C.l2(fa), C.l2(fb)])
    y = np.concatenate([np.zeros(len(fa)), np.ones(len(fb))])
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=PROBE_TEST_FRAC, random_state=seed, stratify=y)
    clf = LogisticRegression(max_iter=5000).fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    w = clf.coef_[0]
    proj = X @ w / np.linalg.norm(w)
    a, b = proj[y == 0], proj[y == 1]
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1)
                      + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return {'comparison': label, 'n_a': len(fa), 'n_b': len(fb),
            'accuracy': float(clf.score(Xte, yte)),
            'auc': float(roc_auc_score(yte, p)),
            'cohens_d_probe_axis': float(abs(b.mean() - a.mean()) / pooled)}


# --------------------------------------------------------------------------
# panel 3 -- generative precision / recall
# --------------------------------------------------------------------------
def precision_recall(real, fake, k=PR_K, device='cuda'):
    """Kynkaanniemi et al. 2019 improved precision/recall on L2-normalised
    features. precision = share of FAKE inside REAL's k-NN manifold;
    recall = share of REAL inside FAKE's manifold."""
    import torch
    R = torch.as_tensor(C.l2(real), device=device)
    F = torch.as_tensor(C.l2(fake), device=device)

    def radii(X):
        d = torch.cdist(X, X)
        d.fill_diagonal_(float('inf'))
        return d.kthvalue(k, dim=1).values          # distance to k-th NN

    rR, rF = radii(R), radii(F)
    d = torch.cdist(F, R)                           # (fake, real)
    precision = float((d <= rR[None, :]).any(dim=1).float().mean())
    recall = float((d.T <= rF[None, :]).any(dim=1).float().mean())
    return precision, recall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pixel-sample', type=int, default=0,
                    help='images for panel 1; 0 = all 4447')
    ap.add_argument('--seed', type=int, default=C.SEED)
    ap.add_argument('--no-log', action='store_true')
    opt = ap.parse_args()
    repo = C.REPO
    # One RNG stream per panel. Sharing a stream would mean changing panel 1's
    # sample size silently changes panel 2's train/test split -- observed while
    # developing this script (the null-control AUC moved 0.494 -> 0.529 purely
    # because --pixel-sample changed how many draws panel 1 consumed first).
    rng = C.rng(opt.seed)              # panel 1 image sample
    rng_split = C.rng(opt.seed + 1)    # panel 2/3 real-vs-real random split
    import numpy as np
    from PIL import Image

    # ---- GATE: this pipeline must reproduce the audits' cached features ----
    gate = C.assert_embedder_matches_cache(seed=opt.seed)
    print('embedder gate: %s' % gate)

    names = json.load(open(os.path.join(C.ARTIFACTS, 'dinoL_names.json')))
    tgt = np.load(os.path.join(C.ARTIFACTS, 'dinoL_tgt_cls.npy'))
    gen = np.load(os.path.join(C.ARTIFACTS, 'dinoL_gen_cls.npy'))
    tgt_paths = [os.path.join(repo, TGT_DIR, n) for n in names['tgt']]

    # ---- panel 1 ----------------------------------------------------------
    raw_stems = sorted(os.path.splitext(f)[0]
                       for f in os.listdir(os.path.join(repo, RAW_DIR)))
    pick = (raw_stems if opt.pixel_sample in (0, None) else
            [raw_stems[i] for i in rng.choice(
                len(raw_stems), size=min(opt.pixel_sample, len(raw_stems)),
                replace=False)])
    px, px_rows = panel1_pixels(repo, pick, rng)
    print('panel1: bg luminance real %.2f -> gen %.2f (shift %+.2f); '
          'fg-bg colour corr %.3f -> %.3f'
          % (px['bg_lum_real'], px['bg_lum_gen'], px['bg_lum_shift'],
             px['corr_real'], px['corr_gen']))

    # ---- fresh embeddings for the controls --------------------------------
    prog = lambda i, n: print('    embedding %d/%d' % (i, n), flush=True)

    raw_paths = [os.path.join(repo, RAW_DIR, s + '.png') for s in raw_stems]
    raw, fresh_raw = C.embed_cached('a3_rawhkuis', raw_paths, progress=prog)

    def jpeg_loader(p):
        import io
        im = Image.open(p).convert('RGB')
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=JPEG_QUALITY)
        buf.seek(0)
        return Image.open(buf).convert('RGB')

    def dark_loader(p):
        im = np.asarray(Image.open(p).convert('RGB')).astype('int16')
        return np.clip(im - DARKEN_LEVELS, 0, 255).astype('uint8')

    jpg, fresh_jpg = C.embed_cached('a3_tgt_jpeg%d' % JPEG_QUALITY, tgt_paths,
                                    loader=jpeg_loader, progress=prog)
    drk, fresh_drk = C.embed_cached('a3_tgt_dark%d' % DARKEN_LEVELS, tgt_paths,
                                    loader=dark_loader, progress=prog)

    # ---- panel 2 ----------------------------------------------------------
    half = len(tgt) // 2
    order = rng_split.permutation(len(tgt))
    rand_a, rand_b = tgt[order[:half]], tgt[order[half:]]
    srt = np.argsort(names['tgt'])                 # the ORIGINAL bug
    srt_a, srt_b = tgt[srt[:half]], tgt[srt[half:]]

    probes = [
        probe(tgt, gen, opt.seed, 'real target vs LAKE-RED output'),
        probe(rand_a, rand_b, opt.seed, 'real vs real, RANDOM split (true null)'),
        probe(tgt, raw, opt.seed, 'real target vs raw HKU-IS (two datasets)'),
        probe(tgt, jpg, opt.seed, 'real vs same images JPEG-%d' % JPEG_QUALITY),
        probe(tgt, drk, opt.seed, 'real vs same images darkened %d'
              % DARKEN_LEVELS),
        probe(srt_a, srt_b, opt.seed,
              'real vs real, SORTED-filename split (the R-c bug)'),
    ]
    for r in probes:
        print('  probe %-52s acc %.4f  AUC %.4f  d %.2f'
              % (r['comparison'], r['accuracy'], r['auc'],
                 r['cohens_d_probe_axis']))

    # probe d at the other cached embedder settings, for the size/resolution check
    d_variants = {'L/224': probes[0]['cohens_d_probe_axis']}
    for tag, lbl in (('dinoB', 'B/224'), ('dinoL518', 'L/518')):
        ct = os.path.join(C.ARTIFACTS, '%s_tgt_cls.npy' % tag)
        cg = os.path.join(C.ARTIFACTS, '%s_gen_cls.npy' % tag)
        if os.path.exists(ct) and os.path.exists(cg):
            d_variants[lbl] = probe(np.load(ct), np.load(cg), opt.seed,
                                    lbl)['cohens_d_probe_axis']

    # ---- panel 3 ----------------------------------------------------------
    prec_gen, rec_gen = precision_recall(tgt, gen)
    prec_raw, rec_raw = precision_recall(tgt, raw)
    prec_ceil, rec_ceil = precision_recall(rand_a, rand_b)
    prec_srt, rec_srt = precision_recall(srt_a, srt_b)     # the R-c bug again
    print('  precision/recall  LAKE-RED %.3f/%.3f  rawHKU %.3f/%.3f  '
          'ceiling(random) %.3f/%.3f  ceiling(SORTED bug) %.3f/%.3f'
          % (prec_gen, rec_gen, prec_raw, rec_raw, prec_ceil, rec_ceil,
             prec_srt, rec_srt))
    share_gen = rec_gen / rec_ceil
    share_raw = rec_raw / rec_ceil

    # ---- outputs ----------------------------------------------------------
    out = os.path.join(repo, 'evidence', 'out')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'a3_probe_table.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(probes[0]))
        w.writeheader()
        w.writerows(probes)
    with open(os.path.join(out, 'a3_precision_recall.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['set', 'precision', 'recall', 'recall_share_of_ceiling',
                    'ceiling_used'])
        w.writerow(['LAKE-RED output', round(prec_gen, 4), round(rec_gen, 4),
                    round(share_gen, 4), 'random split'])
        w.writerow(['raw HKU-IS (pre-LAKE-RED)', round(prec_raw, 4),
                    round(rec_raw, 4), round(share_raw, 4), 'random split'])
        w.writerow(['real-vs-real ceiling (RANDOM split)', round(prec_ceil, 4),
                    round(rec_ceil, 4), 1.0, '-'])
        w.writerow(['real-vs-real ceiling (SORTED split, the R-c bug)',
                    round(prec_srt, 4), round(rec_srt, 4), '', '-'])
    with open(os.path.join(out, 'a3_pixel_stats.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['key', 'value'])
        for k, v in px.items():
            w.writerow([k, round(v, 6) if isinstance(v, float) else v])
    with open(os.path.join(out, 'a3_pixel_per_image.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(px_rows[0]))
        w.writeheader()
        w.writerows(px_rows)

    P = {r['comparison'][:12]: r for r in probes}
    rv, nl = probes[0], probes[1]
    metrics = [
        ('embedder_gate', 'min cos %.5f over %d images'
         % (gate['min_cos'], gate['n']), 'fresh vs cached dinoL_tgt_cls.npy'),
        ('probe_auc_real_vs_lakered', '%.4f' % rv['auc'], 'THE headline claim'),
        ('probe_auc_real_vs_real_random', '%.4f' % nl['auc'],
         'the TRUE null control'),
        ('probe_auc_real_vs_raw_hkuis', '%.4f' % probes[2]['auc'],
         'two ordinary different datasets'),
        ('probe_auc_jpeg%d' % JPEG_QUALITY, '%.4f' % probes[3]['auc'],
         'IDENTICAL images, recompressed'),
        ('probe_auc_darkened%d' % DARKEN_LEVELS, '%.4f' % probes[4]['auc'],
         'IDENTICAL images, darkened -- refutes the R-e mechanism'),
        ('probe_auc_sorted_split_BUG', '%.4f' % probes[5]['auc'],
         'reproduces the R-c defect'),
        ('probe_cohens_d', ' '.join('%s=%.2f' % (k, v)
                                    for k, v in d_variants.items()),
         'probe axis, by embedder'),
        ('precision_lakered', '%.4f' % prec_gen, ''),
        ('recall_lakered', '%.4f' % rec_gen, 'k=%d NN manifold' % PR_K),
        ('precision_raw_hkuis', '%.4f' % prec_raw, 'the pool LAKE-RED starts FROM'),
        ('recall_raw_hkuis', '%.4f' % rec_raw, 'the pool LAKE-RED starts FROM'),
        ('ceiling_random_split', '%.4f / %.4f' % (prec_ceil, rec_ceil),
         'corrected ceiling'),
        ('ceiling_SORTED_split_BUG', '%.4f / %.4f' % (prec_srt, rec_srt),
         'the R-c defect reproduced'),
        ('recall_share_lakered', '%.1f%%' % (100 * share_gen),
         'of the corrected ceiling'),
        ('recall_share_raw_hkuis', '%.1f%%' % (100 * share_raw),
         'of the corrected ceiling'),
        ('generation_recall_delta', '%+.4f (%.1f%% relative)'
         % (rec_gen - rec_raw, 100 * (rec_gen - rec_raw) / rec_raw),
         'LAKE-RED output minus its own input pool'),
        ('bg_luminance_real', '%.2f' % px['bg_lum_real'],
         '%d images, mask-restricted' % px['n']),
        ('bg_luminance_generated', '%.2f' % px['bg_lum_gen'], 'same images'),
        ('bg_luminance_shift', '%+.2f' % px['bg_lum_shift'], 'gen - real'),
        ('bg_channel_shift_rgb', '%+.2f %+.2f %+.2f'
         % (px['bg_r_shift'], px['bg_g_shift'], px['bg_b_shift']), 'gen - real'),
        ('fg_bg_colour_corr_real', '%+.3f' % px['corr_real'],
         'R2 %.3f' % px['r2_real']),
        ('fg_bg_colour_corr_generated', '%+.3f' % px['corr_gen'],
         'our local re-generation, R2 %.3f' % px['r2_gen']),
        ('fg_bg_colour_corr_authors_pool', '%+.3f' % px['corr_auth'],
         "authors' released pool (n=%d), R2 %.3f -- independent replication"
         % (px['n_auth'], px['r2_auth'])),
        ('bg_luminance_authors_pool', '%.2f' % px['bg_lum_auth'],
         "authors' released pool"),
        ('fresh_embeddings_computed', 'raw=%s jpeg=%s dark=%s'
         % (fresh_raw, fresh_jpg, fresh_drk), 'False = read from cache'),
    ]

    thresholds = [
        ('embedder reproduces the cached features (min cos >= 0.999)', True),
        ('real-vs-real RANDOM split is a genuine null (AUC < 0.60)',
         nl['auc'] < 0.60),
        ('the sorted-filename split is NOT a null (AUC > 0.75) -- the R-c bug',
         probes[5]['auc'] > 0.75),
        ('JPEG-%d alone reaches AUC > 0.85, so 0.999 is near-vacuous'
         % JPEG_QUALITY, probes[3]['auc'] > 0.85),
        ('two ordinary different datasets reach AUC > 0.95 -- the surviving '
         'support for R-f', probes[2]['auc'] > 0.95),
        ('the fg->bg colour sign flip replicates in the AUTHORS pool too',
         px['n_auth'] > 0 and px['corr_real'] < 0 < px['corr_auth']),
        ('darkening does NOT separate (AUC < 0.60) -- R-e retraction',
         probes[4]['auc'] < 0.60),
        ('generation REDUCES recall vs its own input pool', rec_gen < rec_raw),
        ('corrected ceiling exceeds the buggy one', rec_ceil > rec_srt),
    ]

    def verdict(got, want, tol):
        return 'MATCH' if abs(got - want) <= tol else \
            'MISMATCH -> measured %.4f vs %.4f' % (got, want)

    expected = [
        ('probe AUC real vs LAKE-RED', EXPECT['auc_real_vs_gen'],
         verdict(rv['auc'], EXPECT['auc_real_vs_gen'], 0.01)),
        # Two rows on purpose. The first compares against the audit's PARTICULAR
        # random draw, which is sampling noise, not a finding -- kept because the
        # tolerance was registered before the run and must not be tuned away. The
        # second tests the property that actually matters: a null control should
        # sit at chance. AUC 0.478 and 0.529 are both chance.
        ('probe AUC true null vs the audit\'s particular draw',
         EXPECT['auc_null_random'],
         verdict(nl['auc'], EXPECT['auc_null_random'], 0.05)),
        ('true null is chance-level (|AUC - 0.5| <= 0.05)', 0.500,
         verdict(nl['auc'], 0.500, 0.05)),
        ('probe AUC real vs raw HKU-IS', EXPECT['auc_real_vs_raw'],
         verdict(probes[2]['auc'], EXPECT['auc_real_vs_raw'], 0.03)),
        ('probe AUC JPEG-75', EXPECT['auc_jpeg75'],
         verdict(probes[3]['auc'], EXPECT['auc_jpeg75'], 0.05)),
        ('probe AUC darkened-20', EXPECT['auc_dark20'],
         verdict(probes[4]['auc'], EXPECT['auc_dark20'], 0.10)),
        ("Cohen's d probe axis, L/224", EXPECT['d_probe_L224'],
         verdict(d_variants['L/224'], EXPECT['d_probe_L224'], 0.40)),
        ('LAKE-RED precision/recall',
         '%.3f/%.3f' % (EXPECT['prec_gen'], EXPECT['rec_gen']),
         verdict(rec_gen, EXPECT['rec_gen'], 0.03)),
        ('raw HKU-IS precision/recall',
         '%.3f/%.3f' % (EXPECT['prec_raw'], EXPECT['rec_raw']),
         verdict(rec_raw, EXPECT['rec_raw'], 0.03)),
        ('corrected ceiling',
         '%.3f/%.3f' % (EXPECT['prec_ceiling'], EXPECT['rec_ceiling']),
         verdict(rec_ceil, EXPECT['rec_ceiling'], 0.03)),
        ('recall share of ceiling', '49.6%',
         verdict(100 * share_gen, 49.6, 3.0)),
        ('fg->bg colour corr, real', EXPECT['corr_real'],
         verdict(px['corr_real'], EXPECT['corr_real'], 0.10)),
        ('fg->bg colour corr, generated', EXPECT['corr_gen'],
         verdict(px['corr_gen'], EXPECT['corr_gen'], 0.10)),
    ]

    notes = (
        'THIS EXPERIMENT DEMOTES OUR OWN HEADLINE, which is why it is in the package. '
        'AUC %.4f real-vs-generated looks damning until the controls sit beside it: '
        'JPEG-%d recompression of the IDENTICAL images reaches %.4f, and two ordinary '
        'different datasets reach %.4f. AUC 0.999 establishes only "these are different '
        'distributions", which nobody disputes. A reviewer would have dismissed it.\n'
        'The protocol itself is sound -- the true null (random real-vs-real split) lands '
        'at %.4f, i.e. chance.\n'
        'THREE VALUES DID NOT REPRODUCE, and they are not equal in kind:\n'
        '  (1) the null control, %.4f here vs 0.5289 in the source. Both are chance; the '
        'exact figure is a property of which random split was drawn, not of any finding. '
        'The pre-registered +/-0.05 tolerance is logged as MISMATCH rather than widened, '
        'and a second EXPECTED row tests the property that matters (|AUC-0.5| <= 0.05).\n'
        '  (2) JPEG-%d, %.4f here vs 0.9380 in the source -- a real disagreement we CANNOT '
        'explain. Re-encoding an already-JPEG target image at quality 75 leaves DINOv2 '
        'features essentially unchanged, which is what %.4f says. The source script was '
        'never saved, so the 0.9380 cannot be traced. Consequence: R-f loses one of its '
        'two supports. The near-vacuity of AUC 0.999 now rests on the cross-dataset '
        'control alone (two ordinary datasets -> %.4f), which is sufficient but should be '
        'stated as one control rather than two.\n'
        '  (3) the real-image fg->bg colour correlation, %+.3f here vs -0.36 in the '
        'source. Robust: -0.183 at n=800, -0.191 at n=4447, -0.189 under luma-601 '
        'weighting. The QUALITATIVE claim survives intact -- the correlation flips sign '
        'from real to generated and R2 is ~0.15-0.19 on the generated side -- but the '
        'real-side magnitude is about half what was published.\n'
        'AN INDEPENDENT REPLICATION we added: the sign flip appears in the AUTHORS\' '
        'released synthetic pool too (%+.3f), not just our local re-generation (%+.3f), '
        'against %+.3f for the real photographs. Two independent LAKE-RED generation runs '
        'land within 0.01 of each other while the real photos sit on the other side of '
        'zero. That is a stronger form of the claim than either run alone.\n'
        'THREE POOLS, easy to confuse: Source/HKU-IS_raw/imgs are the real photographs; '
        'Source/HKU-IS/Image is the authors\' released LAKE-RED output and is what '
        'TRAINING reads; LAKERED/output is our own local re-generation. The middle two '
        'are both generated but are NOT the same images (maxdiff 240, cos 0.62-0.91). '
        'PRIOR_REVIEW.md 0.5 names them "Source/HKU-IS (authors\')" and "LAKERED/local".\n'
        'GATE: this script re-embeds 8 target images and requires cos >= 0.999 against '
        'the cached vectors before mixing fresh control features with cached ones '
        '(measured %.5f). The original preprocessing was never saved and had to be '
        'recovered by testing eight candidate pipelines; the winner is PIL '
        'Resize((224,224)) BICUBIC with no crop, ImageNet normalisation, CLS token '
        'stored unnormalised. Near-misses were dangerous: Resize+CenterCrop gives 0.978 '
        'and cv2.INTER_AREA gives 0.997, so a reasonable-looking pipeline would have '
        'silently produced slightly wrong features.\n'
        'R-c REPRODUCED, NOT JUST DESCRIBED: the original "null control" split the target '
        'features in sorted-filename order, which put COD10K on one side and CAMO on the '
        'other. This script computes that split too -- AUC %.4f and ceiling %.3f/%.3f -- '
        'beside the corrected random split (%.4f, %.3f/%.3f). Both are logged so the '
        'defect is visible.\n'
        'R-e RETRACTED: darkening the identical images by %d levels gives AUC %.4f. '
        'DINOv2 is essentially invariant to that shift, so background darkening cannot '
        'be the mechanism behind the style axis. The earlier mechanistic claim is '
        'withdrawn.\n'
        'THE RESULT THAT ACTUALLY MATTERS is panel 3, and it points the opposite way '
        'from the original framing: LAKE-RED does not merely have LIMITED coverage of '
        'the target manifold, it DESTROYS coverage its own input already had. Raw '
        'HKU-IS recall %.3f -> LAKE-RED %.3f, a %.1f%% relative loss, bought for '
        '%+.3f precision.\n'
        'HOW THIS INTEGRATES: A3 supports none of the four load-bearing conclusions. It '
        'removes two claims we should not lean on, and reframes the style gap as a '
        'CONSEQUENCE -- it is why coverage-counting is inverse-ranked by feasibility, '
        'which B2 measures directly as rho(acceptance, n_s) = +0.73..+0.92.\n'
        'Limitations: JPEG quality %d and darkening %d levels are the audit\'s specific '
        'control settings, not a sweep. k=%d for the manifold estimate. Precision/recall '
        'is computed on L2-normalised features; the sources did not state whether they '
        'normalised, so this is our stated choice.'
        % (rv['auc'], JPEG_QUALITY, probes[3]['auc'], probes[2]['auc'],
           nl['auc'],
           nl['auc'], JPEG_QUALITY, probes[3]['auc'], probes[3]['auc'],
           probes[2]['auc'], px['corr_real'],
           px['corr_auth'], px['corr_gen'], px['corr_real'],
           gate['min_cos'], probes[5]['auc'], prec_srt, rec_srt,
           nl['auc'], prec_ceil, rec_ceil, DARKEN_LEVELS, probes[4]['auc'],
           rec_raw, rec_gen, 100 * (rec_raw - rec_gen) / rec_raw,
           prec_gen - prec_raw, JPEG_QUALITY, DARKEN_LEVELS, PR_K))

    block = C.log_block(
        exp='A3',
        cmd='LAKE-RED/.venv/bin/python evidence/a3_appearance_signature.py '
            '--pixel-sample %d' % opt.pixel_sample,
        metrics=metrics, thresholds=thresholds, expected=expected,
        artifacts=['evidence/out/a3_probe_table.csv',
                   'evidence/out/a3_precision_recall.csv',
                   'evidence/out/a3_pixel_stats.csv',
                   'evidence/out/a3_pixel_per_image.csv'],
        revision=('R-c sorted-filename split bug (ceiling 0.893/0.871 -> '
                  'corrected, both computed here); R-d recall share 54% -> '
                  'recomputed; R-e ~20-level darkening RETRACTED as the '
                  'mechanism; R-f AUC 0.999 demoted to near-vacuous'),
        trains='NO', notes=notes, seed=opt.seed, write=not opt.no_log)
    print('\n' + block)


if __name__ == '__main__':
    main()

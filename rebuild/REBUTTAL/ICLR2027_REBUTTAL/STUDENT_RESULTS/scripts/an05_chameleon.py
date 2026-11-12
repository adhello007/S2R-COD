#!/usr/bin/env python
"""AN-05 -- CHAMELEON duplicate re-run, exact-hash scopes, protocol pathways and mask releases.

ANALYSIS_PRESPEC.md §9. Every detector is the committed code, UNCHANGED:
  Tier A  rebuild/D2_reaudit/release/detect_contamination.py (CLI, run as a subprocess)
  Tier B  rebuild/DIAG/diag_chameleon_ext.py main()  (module path globals repointed, OUT redirected)
  Adjud.  rebuild/D2_FINAL_AUDIT/adjudicate.py main() (same)
  Masks   rebuild/D2_reaudit/d2r_reaudit.py _mask_white / source_polarity / _mask_object
Thresholds are the published ones; none is changed. Data are read from --data-root only.

Stages (--stage): tierA, tierB, adjudicate, tables, all.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
ap.add_argument('--stage', default='all')
ap.add_argument('--workers', type=int, default=8)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
RUN = os.path.join(SR, 'RUNS/an05')
os.makedirs(RUN, exist_ok=True)
PY = sys.executable
DET = os.path.join(WT, 'rebuild/D2_reaudit/release/detect_contamination.py')
CHAM = os.path.join(DR, 'Dataset/chameleon_new/animals')         # author-sourced release (76)
CHAM_REPO = os.path.join(DR, 'Dataset/Test/CHAMELEON/Imgs')      # repo copy
POOLS = {   # name -> (dir, role in THIS paper's protocol)
    'target_4040': (os.path.join(DR, 'Dataset/Target/Image'), 'unlabelled target (COD10K-train 3040 + CAMO-train 1000)'),
    'source_hkuis_4447': (os.path.join(DR, 'Dataset/Source/HKU-IS/Image'), 'supervised source (labels used)'),
    'source_hkuis_raw': (os.path.join(DR, 'Dataset/Source/HKU-IS_raw/imgs'), 'supervised source, raw release'),
    'renders_4447': (os.path.join(DR, 'Dataset/LAKERED/output/HKU-IS/images'), 'synthetic injection pool (labels used)'),
    'camo250_val': (os.path.join(DR, 'Dataset/Val/CAMO/Imgs'), 'checkpoint selection (MAE)'),
    'cod10k_test': (os.path.join(DR, 'Dataset/Test/COD10K/Imgs'), 'held-out primary endpoint'),
    'nc4k_test': (os.path.join(DR, 'Dataset/Test/NC4K/Imgs'), 'held-out secondary endpoint (negative control)'),
}


def log(m):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), m), flush=True)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def stage_tierA():
    cmds = []
    r = subprocess.run([PY, '-I', '-B', DET, '--self-test'], capture_output=True, text=True)
    open(os.path.join(RUN, 'tierA_selftest.log'), 'w').write(r.stdout + r.stderr + '\nrc=%d\n' % r.returncode)
    cmds.append(('self-test', r.returncode))
    for name, (d, _) in POOLS.items():
        js, cs = os.path.join(RUN, 'tierA_%s.json' % name), os.path.join(RUN, 'tierA_%s.csv' % name)
        cmd = [PY, '-I', '-B', DET, CHAM, d, '--json', js, '--csv', cs, '--workers', str(a.workers)]
        log('Tier A vs %s' % name)
        r = subprocess.run(cmd, capture_output=True, text=True)
        open(os.path.join(RUN, 'tierA_%s.log' % name), 'w').write(' '.join(cmd) + '\n' + r.stdout + r.stderr
                                                                   + '\nrc=%d\n' % r.returncode)
        cmds.append((name, r.returncode))
    # repo copy vs target as well (the "byte-identical release" check is done in tables)
    json.dump(cmds, open(os.path.join(RUN, 'tierA_rc.json'), 'w'))


def stage_tierB():
    sys.path.insert(0, os.path.join(WT, 'rebuild/DIAG'))
    import diag_chameleon_ext as X
    X.CHAM_DIR, X.TRAIN_DIR = CHAM, POOLS['target_4040'][0]
    X.NC4K_DIR, X.COD_TEST_DIR = POOLS['nc4k_test'][0], POOLS['cod10k_test'][0]
    X.COMMITTED = os.path.join(WT, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')   # base, committed
    X.OUT = os.path.join(RUN, 'tierB')
    sys.argv = ['diag_chameleon_ext.py', '--workers', str(a.workers)]
    log('Tier B (unchanged diag_chameleon_ext.main)')
    X.main()


def stage_adjudicate():
    sys.path.insert(0, os.path.join(WT, 'rebuild/D2_FINAL_AUDIT'))
    import adjudicate as J
    J.CHAM_DIR, J.TRAIN_DIR = CHAM, POOLS['target_4040'][0]
    J.EXT_JSON = os.path.join(RUN, 'tierB', 'diag_chameleon_ext.json')
    J.CONFIRMED = os.path.join(WT, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')
    J.OUT = os.path.join(RUN, 'adjudicate')
    sys.argv = ['adjudicate.py']
    log('Adjudication (unchanged adjudicate.main)')
    J.main()


def stage_tables():
    rt = os.path.join(SR, 'RESULT_TABLES')
    names = sorted(os.listdir(CHAM), key=lambda s: int(re.search(r'(\d+)', s).group(1)))
    assert len(names) == 76
    stem = lambda n: os.path.splitext(n)[0]      # noqa: E731
    # ---- Tier A results per pool
    tA = {}
    for name in POOLS:
        js = os.path.join(RUN, 'tierA_%s.json' % name)
        tA[name] = json.load(open(js)) if os.path.isfile(js) else None
    committedA = json.load(open(os.path.join(WT, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')))
    # ---- Tier B + adjudication
    adj = json.load(open(os.path.join(RUN, 'adjudicate', 'adjudication.json')))
    ext = json.load(open(os.path.join(RUN, 'tierB', 'diag_chameleon_ext.json')))
    # ---- exact hashes and decoded-pixel identity vs every pool
    def pix_hash(p):
        with Image.open(p) as im:
            arr = np.asarray(im.convert('RGB'))
        return hashlib.sha256(arr.tobytes() + str(arr.shape).encode()).hexdigest()
    cham_sha = {n: sha(os.path.join(CHAM, n)) for n in names}
    cham_pix = {n: pix_hash(os.path.join(CHAM, n)) for n in names}
    repo_names = sorted(os.listdir(CHAM_REPO))
    repo_sha = {stem(n): sha(os.path.join(CHAM_REPO, n)) for n in repo_names}
    exact = defaultdict(dict)
    for pname, (d, _) in POOLS.items():
        fs = sorted(os.listdir(d))
        hs, ps = defaultdict(list), defaultdict(list)
        for f in fs:
            p = os.path.join(d, f)
            hs[sha(p)].append(f)
        for n in names:
            exact[n][pname] = hs.get(cham_sha[n], [])
        # pixel identity only where a same-dimension file exists (cheap)
        dims_c = {n: Image.open(os.path.join(CHAM, n)).size for n in names}
        need = set(dims_c.values())
        for f in fs:
            p = os.path.join(d, f)
            try:
                if Image.open(p).size in need:
                    ps[pix_hash(p)].append(f)
            except Exception:                                  # noqa: BLE001
                pass
        for n in names:
            exact[n][pname + '_pixel'] = ps.get(cham_pix[n], [])
    # ---- per-image ledger
    confA = {}
    for pr in tA['target_4040']['pairs']:
        confA.setdefault(stem(pr['image_a']), []).append(pr)
    uncheckedA = {stem(r['name']) for r in tA['target_4040']['nn_rows'] if r['nearest'] is None}
    ext_match = {stem(r['chameleon_image']): r for r in ext['rows']
                 if r.get('verdict') == 'MATCH' and r.get('at_operating_point')}
    adj_ext = {stem(r['chameleon_image']): r for r in adj if r.get('group') == 'extension'}
    committed_final = {stem(r['image']): r for r in json.load(open(os.path.join(
        WT, 'rebuild/D2_FINAL_AUDIT/out/final_verdicts.json')))['rows']}

    def transform_consistent(r):
        # Reproduction consistency check of the manuscript's adjudication criterion ("same photograph
        # rescaled or cropped": a full-resolution homography exists, near-similarity, high correlation).
        # NOT a threshold of the published method; the committed decisions were a documented judgement.
        if r is None or r.get('verdict') in ('NO HOMOGRAPHY', 'NO OVERLAP'):
            return False
        return abs(r.get('shear_deg', 99)) <= 5.0 and r.get('corr', 0) >= 0.90
    pool_of = lambda f: ('COD10K-train' if f.startswith('COD10K') else ('CAMO-train' if f.lower().startswith('camo') else 'other'))  # noqa: E731
    rows = []
    for n in names:
        s = stem(n)
        pa = confA.get(s, [])
        partner_a = sorted({p['image_b'] for p in pa})
        rb = adj_ext.get(s)
        b_ok = (s in ext_match) and transform_consistent(rb)
        if partner_a:
            status, tier, partners = 'confirmed', 'A', partner_a
        elif b_ok:
            status, tier, partners = 'confirmed', 'B', [rb['partner']]
        elif s in uncheckedA:
            status, tier, partners = 'unchecked', '', []
        else:
            status, tier, partners = 'tierA_checked_no_match', '', []
        cf = committed_final.get(s, {})
        rows.append(dict(
            chameleon=s, status=status, tier=tier, partners=' '.join(partners),
            partner_pools=' '.join(sorted({pool_of(f) for f in partners})),
            in_cod10k_train=any(pool_of(f) == 'COD10K-train' for f in partners),
            in_camo_train=any(pool_of(f) == 'CAMO-train' for f in partners),
            tierA_mean_abs=(min(p['mean_abs'] for p in pa) if pa else ''),
            tierA_n_partners=len(partner_a), tierA_no_same_dim_candidate=(s in uncheckedA),
            tierB_match_at_operating_point=(s in ext_match),
            tierB_inliers=(ext_match[s]['n_inlier'] if s in ext_match else ''),
            adj_residual=(rb.get('residual_mean', '') if rb else ''), adj_corr=(rb.get('corr', '') if rb else ''),
            adj_scale=('%s/%s' % (rb.get('scale_x', ''), rb.get('scale_y', '')) if rb else ''),
            adj_shear_deg=(rb.get('shear_deg', '') if rb else ''), adj_verdict=(rb.get('verdict', '') if rb else ''),
            tierB_transform_consistent=(transform_consistent(rb) if rb else ''),
            committed_final_verdict=cf.get('verdict', ''), committed_final_tier=cf.get('tier', ''),
            committed_partner=cf.get('partner', ''), committed_pool=cf.get('pool', ''),
            agrees_with_committed=(
                (status == 'confirmed') == (cf.get('verdict') == 'CONTAMINATED')
                and (status == 'unchecked') == (cf.get('verdict') == 'UNCHECKED')),
            exact_sha_target=' '.join(exact[n]['target_4040']), exact_sha_camo250=' '.join(exact[n]['camo250_val']),
            exact_sha_source=' '.join(exact[n]['source_hkuis_4447'] + exact[n]['source_hkuis_raw'] + exact[n]['renders_4447']),
            exact_sha_cod10k_test=' '.join(exact[n]['cod10k_test']), exact_sha_nc4k=' '.join(exact[n]['nc4k_test']),
            pixel_identical_target=' '.join(exact[n]['target_4040_pixel']),
            pixel_identical_camo250=' '.join(exact[n]['camo250_val_pixel']),
            author_release_equals_repo_copy=(cham_sha[n] == repo_sha.get(s)),
            sha256=cham_sha[n]))
    n_conf = sum(r['status'] == 'confirmed' for r in rows)
    n_cod = sum(r['status'] == 'confirmed' and r['in_cod10k_train'] for r in rows)
    n_unch = sum(r['status'] == 'unchecked' for r in rows)
    n_neg = sum(r['status'] == 'tierA_checked_no_match' for r in rows)
    assert len(rows) == 76 and n_conf + n_unch + n_neg == 76
    for r in rows:
        r.update(confirmed_floor_total=n_conf, in_cod10k_train_total=n_cod, unchecked_total=n_unch,
                 tierA_checked_no_match_total=n_neg)
    with open(os.path.join(rt, 'AN-05_chameleon_pairs.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # ---- protocol pathways
    paths = []
    for r in rows:
        dup = r['status'] == 'confirmed'
        camo250 = bool(r['exact_sha_camo250'] or r['pixel_identical_camo250'])
        unknown = r['status'] != 'confirmed'
        def lvl(hit):
            return 'direct' if hit else ('unknown' if unknown else 'absent')
        paths.append(dict(
            chameleon=r['chameleon'], status=r['status'], partner_pools=r['partner_pools'],
            this_paper_supervised_source_labels=('absent' if not r['exact_sha_source'] else 'direct') +
            ' (source = HKU-IS + renders; exact/pixel check and Tier A vs source pools)',
            this_paper_unlabelled_target_image=lvl(dup) + (' (photo in 4040 target pool; image only, no label)' if dup else ''),
            this_paper_checkpoint_selection=('direct (byte-identical in CAMO-250)' if camo250 else 'absent (exact/pixel)'),
            this_paper_test_endpoint='absent (CHAMELEON is not an endpoint here)',
            common_supervised_protocol_train_labels=lvl(dup) + (' (partner in public %s with mask)' % r['partner_pools'] if dup else ''),
            common_protocol_checkpoint_selection=('direct if CAMO-test is the selection split' if camo250 else 'protocol-dependent'),
            common_protocol_test='CHAMELEON is the evaluated test set'))
    with open(os.path.join(rt, 'AN-05_protocol_paths.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(paths[0]))
        w.writeheader()
        w.writerows(paths)
    # ---- mask releases
    sys.path.insert(0, os.path.join(WT, 'rebuild/D2_reaudit'))
    sys.path.insert(0, os.path.join(WT, 'rebuild'))
    sys.path.insert(0, os.path.join(WT, 'Eval'))
    import d2r_reaudit as R
    import metrics as Measure
    md_a = os.path.join(DR, 'Dataset/chameleon_new/masks')
    md_r = os.path.join(DR, 'Dataset/Test/CHAMELEON/GT')
    ma = {int(re.search(r'(\d+)', f).group(1)): f for f in os.listdir(md_a)}
    mr = {int(re.search(r'(\d+)', f).group(1)): f for f in os.listdir(md_r)}
    pol_a, wf_a = R.source_polarity([os.path.join(md_a, f) for f in ma.values()])
    pol_r, wf_r = R.source_polarity([os.path.join(md_r, f) for f in mr.values()])
    preds = os.path.join(DR, 'rebuild/D2_reaudit/preds')
    mrows, maes = [], {'author': [], 'repo': []}
    for n in names:
        k = int(re.search(r'(\d+)', n).group(1))
        wa, _ = R._mask_white(os.path.join(md_a, ma[k]))
        wr, _ = R._mask_white(os.path.join(md_r, mr[k]))
        oa, _ = R._mask_object(os.path.join(md_a, ma[k]), pol_a)
        orr, _ = R._mask_object(os.path.join(md_r, mr[k]), pol_r)
        same = wa.shape == wr.shape
        iou_stored = float((wa & wr).sum() / max(1, (wa | wr).sum())) if same else float('nan')
        A_, B_ = oa > 127, orr > 127
        iou_al = float((A_ & B_).sum() / max(1, (A_ | B_).sum())) if same else float('nan')
        row = dict(chameleon=stem(n), author_mask=ma[k], repo_mask=mr[k], author_mask_sha=sha(os.path.join(md_a, ma[k])),
                   repo_mask_sha=sha(os.path.join(md_r, mr[k])), same_shape=same, iou_as_stored=iou_stored,
                   iou_polarity_aligned=iou_al, identical_after_alignment=bool(same and np.array_equal(A_, B_)),
                   author_polarity=pol_a, repo_polarity=pol_r)
        pp = os.path.join(preds, stem(n) + '.png')
        if os.path.isfile(pp):
            pred = np.asarray(Image.open(pp).convert('L'))
            for tag, g in (('author', oa), ('repo', orr)):
                p = pred if pred.shape == g.shape else np.asarray(Image.fromarray(pred).resize((g.shape[1], g.shape[0]), Image.NEAREST))
                m = Measure.MAE()
                m.step(pred=p, gt=g)
                row['mae_' + tag] = float(m.get_results()['mae'])
                maes[tag].append(row['mae_' + tag])
        mrows.append(row)
    with open(os.path.join(rt, 'AN-05_mask_release.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(mrows[0]))
        w.writeheader()
        w.writerows(mrows)
    ious = [r['iou_polarity_aligned'] for r in mrows]
    summary = dict(
        generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        tierA_selftest_rc=json.load(open(os.path.join(RUN, 'tierA_rc.json')))[0],
        tierA={k: (dict(contaminated=v['contaminated']['n'], sweep=v['tolerance_sweep'],
                        n_unchecked=v['nearest_neighbour']['n_unchecked'], pairs=v['pairs_confirmed'])
                   if v else None) for k, v in tA.items()},
        tierB_operating_point=ext.get('operating_point', ext.get('threshold')),
        tierB_keys=list(ext)[:30],
        confirmed_floor=n_conf, in_cod10k_train=n_cod, unchecked=n_unch, tierA_checked_no_match=n_neg,
        exact_sha_matches={p: sum(1 for n in names if exact[n][p]) for p in POOLS},
        pixel_identical_matches={p: sum(1 for n in names if exact[n][p + '_pixel']) for p in POOLS},
        camo250_exact_names=[stem(n) for n in names if exact[n]['camo250_val']],
        author_release_equals_repo_copy=sum(r['author_release_equals_repo_copy'] for r in rows),
        masks=dict(author_polarity=pol_a, author_white_frac=wf_a, repo_polarity=pol_r, repo_white_frac=wf_r,
                   mean_iou_as_stored=float(np.nanmean([r['iou_as_stored'] for r in mrows])),
                   mean_iou_aligned=float(np.nanmean(ious)),
                   n_identical_after_alignment=sum(r['identical_after_alignment'] for r in mrows),
                   n_iou_ge_0p9=int(sum(1 for x in ious if x >= 0.9)),
                   mae_author=float(np.mean(maes['author'])) if maes['author'] else None,
                   mae_repo=float(np.mean(maes['repo'])) if maes['repo'] else None,
                   n_preds=len(maes['author']), preds_source='rebuild/D2_reaudit/preds (SINet S2C Tea_epoch_best, committed)'))
    json.dump(summary, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-05_summary.json'), 'w'), indent=1, default=str)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == '__main__':
    st = a.stage
    if st in ('tierA', 'all'):
        stage_tierA()
    if st in ('tierB', 'all'):
        stage_tierB()
    if st in ('adjudicate', 'all'):
        stage_adjudicate()
    if st in ('tables', 'all'):
        stage_tables()

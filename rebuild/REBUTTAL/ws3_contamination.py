#!/usr/bin/env python
"""REBUTTAL WS3 -- CHAMELEON contamination by protocol, with the Tier-B adjudication logged.

Two jobs, one block.

1. THE ADJUDICATION, RE-RUN. The geometric extension (rebuild/DIAG/diag_chameleon_ext.py)
   put 10 candidates at its 20-inlier operating point, giving the JSON headline 41 + 10 = 51.
   The paper says 50: Appendix F warps each partner into the CHAMELEON frame through a
   full-resolution homography, measures the residual, and rejects animal-7. That step was
   committed (rebuild/D2_FINAL_AUDIT/adjudicate.py, 1cf637a) but never logged. This
   script RE-RUNS it by importing that module's own measure() -- not a reimplementation --
   on all 10 candidates, applies an accept rule declared below, and asserts the paper's
   adjudication table (parsed from the submitted .tex) is reproduced. If it is not, the
   script halts with the paper's fallback wording rather than forcing 50.

   Accept rule (POST-HOC, as the adjudication itself is): a candidate is the SAME
   PHOTOGRAPH, rescaled or cropped, iff a homography is recovered at full resolution
   with |shear| <= SHEAR_MAX deg, perspective <= PERSP_MAX, overlap >= the module's
   MIN_OVERLAP and corr >= CORR_MIN. A rescale or crop is a similarity transform, so
   it has no shear and no perspective; the thresholds are generous on purpose, and
   the block reports how far each accepted pair sits from them. The anchor --
   8 of the 41 known re-encodes, whose mean|diff| is already recorded -- must
   reproduce to RES_TOL, or the instrument is not trusted.

2. THE PROTOCOL TABLE. How CHAMELEON enters under each protocol a reader might use:
   supervised standard split, S2R-COD's target as described, the released 4040 target
   pool, and checkpoint selection on CAMO-250 (sha256 against Dataset/Val/CAMO).

Trains nothing. Reads images and committed JSON. Writes rebuild/REBUTTAL/out/.

Usage:
  .venv/bin/python rebuild/REBUTTAL/ws3_contamination.py [--no-log]
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'D2_FINAL_AUDIT'))
import common as C                                            # noqa: E402
import adjudicate as ADJ                                      # noqa: E402

OUT = os.path.join(_HERE, 'out')
EXT_JSON = os.path.join(C.REPO, 'rebuild/DIAG/out/diag_chameleon_ext.json')
TIER_A = os.path.join(C.REPO, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')
PAPER_TEX = os.path.join(C.REPO, 'AD-PCHG-250926_Final.tex')
CHAM_REPO = os.path.join(C.REPO, 'Dataset/Test/CHAMELEON/Imgs')
TARGET = os.path.join(C.REPO, 'Dataset/Target/Image')
VAL = os.path.join(C.REPO, 'Dataset/Val/CAMO/Imgs')

SHEAR_MAX = 1.0         # degrees
PERSP_MAX = 1e-3
CORR_MIN = 0.90
RES_TOL = 0.01          # anchor reproduction, 0-255 units
N_CHAM = 76


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def paper_table():
    """The adjudication table as SUBMITTED: CHAMELEON, inliers, residual, corr, scale, pool."""
    rows = {}
    pat = re.compile(r'\\texttt\{(animal-\d+)\}\s*&\s*\$(\d+)\$\s*&\s*\$([\d.]+)\$\s*&\s*\$([\d.]+)\$'
                     r'\s*&\s*\$([\d./]+)\$[^&]*&\s*(CAMO|COD10K-train)')
    rej = re.compile(r'\\texttt\{(animal-\d+)\}\s*&\s*\$(\d+)\$\s*&\s*\\multicolumn\{4\}\{l\}\{\\textbf\{rejected\}')
    accepted, rejected = {}, {}
    for line in open(PAPER_TEX):
        m = pat.search(line)
        if m:
            accepted[m.group(1) + '.jpg'] = dict(inliers=int(m.group(2)), residual=float(m.group(3)),
                                                 corr=float(m.group(4)), scale=m.group(5),
                                                 pool=m.group(6))
        m = rej.search(line)
        if m:
            rejected[m.group(1) + '.jpg'] = dict(ext_inliers=int(m.group(2)))
    return accepted, rejected


def scale_str(r):
    """Format scale the way the paper's table does: one value if isotropic to 2 dp."""
    a, b = round(r['scale_x'], 2), round(r['scale_y'], 2)
    return '%.2f' % a if a == b else '%.2f/%.2f' % (a, b)


def accept(r):
    if 'residual_mean' not in r:
        return False, r.get('verdict', 'no measurement')
    why = []
    if abs(r['shear_deg']) > SHEAR_MAX:
        why.append('shear %.2f' % r['shear_deg'])
    if r['perspective'] > PERSP_MAX:
        why.append('perspective %.2e' % r['perspective'])
    if r['corr'] < CORR_MIN:
        why.append('corr %.3f' % r['corr'])
    if r['overlap_frac'] < ADJ.MIN_OVERLAP:
        why.append('overlap %.2f' % r['overlap_frac'])
    return (not why), ('; '.join(why) or 'similarity transform, low residual')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    M, T, OLD = [], [], []

    # --- instrument validation on the known re-encodes (adjudicate.py's own anchor set)
    tier_a = json.load(open(TIER_A))['contaminated']
    assert len(tier_a) == 41, len(tier_a)
    anchors = sorted(tier_a, key=lambda e: e['mean_abs'])[:4] + sorted(tier_a, key=lambda e: -e['mean_abs'])[:4]
    worst = 0.0
    for e in anchors:
        row = ADJ.measure(e['chameleon_image'], e['partner'])[0]
        worst = max(worst, abs(row['residual_mean'] - e['mean_abs']))
    M.append(('anchor_max_abs_error', '%.4f' % worst,
              '8 of the 41 Tier-A pairs, residual vs recorded mean|diff|, adjudicate.measure()'))
    T.append(('instrument reproduces the 8 anchor mean|diff| values within %.2f' % RES_TOL, worst <= RES_TOL))
    if worst > RES_TOL:
        raise SystemExit('WS3 HALT: adjudication instrument does not reproduce its anchor (%.4f)' % worst)

    # --- the adjudication itself, on every candidate at the extension's operating point
    ext = json.load(open(EXT_JSON))
    cands = sorted([r for r in ext['rows'] if r.get('at_operating_point')], key=lambda r: r['chameleon_image'])
    M.append(('tier_b_candidates_at_operating_point', len(cands),
              'diag_chameleon_ext.json, %d-inlier operating point' % ext['operating_point_inliers']))
    for r in cands:   # adjudicate reads the author-sourced copy; it must be the repo's bytes
        T.append(('%s author copy byte-identical to repo copy' % r['chameleon_image'],
                  sha(os.path.join(ADJ.CHAM_DIR, r['chameleon_image'])) == sha(os.path.join(CHAM_REPO, r['chameleon_image']))))
    adj = []
    for r in cands:
        row = ADJ.measure(r['chameleon_image'], r['best_partner'])[0]
        ok, why = accept(row)
        row.update(ext_inliers=r['n_inlier'], accepted=ok, reason=why,
                   partner_pool='COD10K-train' if r['best_partner'].startswith('COD10K') else 'CAMO',
                   partner_in_target=os.path.isfile(os.path.join(TARGET, r['best_partner'])))
        adj.append(row)
        M.append(('adj_%s' % r['chameleon_image'][:-4],
                  '%s  inl %s  resid %s  corr %s  scale %s  shear %s  persp %s'
                  % ('ACCEPT' if ok else 'REJECT', row['n_inlier'],
                     '%.2f' % row['residual_mean'] if 'residual_mean' in row else '-',
                     '%.3f' % row['corr'] if 'corr' in row else '-',
                     scale_str(row) if 'scale_x' in row else '-',
                     '%.3f' % row['shear_deg'] if 'shear_deg' in row else '-',
                     '%.1e' % row['perspective'] if 'perspective' in row else '-'),
                  '%s; ext inliers %d; %s' % (row['partner_pool'], r['n_inlier'], why)))
    acc = [r for r in adj if r['accepted']]
    rej = [r for r in adj if not r['accepted']]
    max_shear = max(abs(r['shear_deg']) for r in acc) if acc else float('nan')
    M += [('tier_b_accepted', len(acc), 'post-hoc accept rule, module docstring'),
          ('tier_b_rejected', ', '.join(r['chameleon_image'] for r in rej) or 'none', ''),
          ('accepted_max_abs_shear_deg', '%.4f' % max_shear, 'margin to SHEAR_MAX=%.1f' % SHEAR_MAX),
          ('accepted_min_corr', '%.4f' % min(r['corr'] for r in acc), 'margin to CORR_MIN=%.2f' % CORR_MIN),
          ('accepted_residual_range', '%.2f .. %.2f' % (min(r['residual_mean'] for r in acc),
                                                       max(r['residual_mean'] for r in acc)), '0-255 units')]

    paper_acc, paper_rej = paper_table()
    agree = (set(paper_acc) == {r['chameleon_image'] for r in acc}
             and set(paper_rej) == {r['chameleon_image'] for r in rej})
    cell_ok = True
    display = []
    for r in acc:
        p = paper_acc.get(r['chameleon_image'])
        if p is None:
            cell_ok = False
            continue
        # Measurement cells. The printed scale is checked against scale_x, and against
        # scale_y too where the paper prints two values.
        ps = p['scale'].split('/')
        same = (p['inliers'] == r['n_inlier'] and round(r['residual_mean'], 2) == p['residual']
                and round(r['corr'], 2) == p['corr'] and r['partner_pool'] == p['pool']
                and '%.2f' % r['scale_x'] == ps[0]
                and (len(ps) == 1 or '%.2f' % r['scale_y'] == ps[1]))
        cell_ok &= same
        OLD.append(('paper adjudication row %s (inl %d, resid %.2f, corr %.2f, scale %s, %s)'
                    % (r['chameleon_image'][:-4], p['inliers'], p['residual'], p['corr'], p['scale'], p['pool']),
                    'as submitted', 'MATCH' if same else 'MISMATCH'))
        # Display. One printed value claims isotropy at 2 dp; say so where it is not.
        if len(ps) == 1 and scale_str(r) != p['scale']:
            display.append('%s prints %s; measured %s' % (r['chameleon_image'][:-4], p['scale'], scale_str(r)))
    T += [('accept/reject set equals the paper table (9 accepted, animal-7 rejected)', agree),
          ('every accepted row reproduces the paper table: inliers, residual, corr, pool, printed scale value(s)', cell_ok),
          ('the paper prints a single scale only where scale_x = scale_y at 2 dp', not display)]
    M.append(('paper_scale_display_omissions', '; '.join(display) or 'none',
              'a presentation defect in the submitted table, not a measurement mismatch'))

    # --- per-image tiers for all 76 ----------------------------------------------------
    names = sorted(os.listdir(CHAM_REPO))
    assert len(names) == N_CHAM, len(names)
    tA = {e['chameleon_image']: e['partner'] for e in tier_a}
    tB = {r['chameleon_image']: r['partner'] for r in acc}
    ext_checked = {r['chameleon_image'] for r in ext['rows']}
    tier = {}
    for n in names:
        tier[n] = ('A' if n in tA else 'B' if n in tB
                   else 'unchecked' if n in ext_checked else 'clean_vs_training')
    counts = {k: sum(1 for v in tier.values() if v == k) for k in ('A', 'B', 'unchecked', 'clean_vs_training')}
    partners = {**tA, **tB}
    in_cod = sorted(n for n, p in partners.items() if p.startswith('COD10K'))
    in_camo = sorted(n for n, p in partners.items() if p.startswith('camourflage'))
    all_in_target = all(os.path.isfile(os.path.join(TARGET, p)) for p in partners.values())
    contaminated = counts['A'] + counts['B']

    # --- checkpoint selection: byte-identity with CAMO-250 -----------------------------
    val = {}
    for f in os.listdir(VAL):
        val.setdefault(sha(os.path.join(VAL, f)), []).append(f)
    byte_val = [(n, val[sha(os.path.join(CHAM_REPO, n))][0]) for n in names
                if sha(os.path.join(CHAM_REPO, n)) in val]
    tgt_hashes = {sha(os.path.join(TARGET, f)) for f in os.listdir(TARGET)}
    byte_tgt = sum(1 for n in names if sha(os.path.join(CHAM_REPO, n)) in tgt_hashes)

    M += [('tier_counts', '  '.join('%s %d' % kv for kv in counts.items()), 'all 76 CHAMELEON images'),
          ('contaminated_total', '%d/76 (%.1f%%)' % (contaminated, 100 * contaminated / N_CHAM), 'Tier A + Tier B, a floor'),
          ('partners_in_COD10K_train', len(in_cod), ''),
          ('partners_in_CAMO_train', len(in_camo), ''),
          ('every_partner_in_released_4040_target', all_in_target, 'Dataset/Target/Image'),
          ('byte_identical_vs_training_pool', byte_tgt, 'sha256, the standard check'),
          ('byte_identical_vs_CAMO250', len(byte_val),
           '; '.join('%s = %s [tier %s]' % (n, v, tier[n]) for n, v in byte_val))]
    T += [('contaminated total is 50', contaminated == 50),
          ('partners split 44 COD10K-train + 6 CAMO-train', (len(in_cod), len(in_camo)) == (44, 6)),
          ('every partner is in the released 4040-image target pool', all_in_target)]

    table = [
        dict(protocol='Supervised training, standard split (COD10K-train 3040 + CAMO-train 1000)',
             how='partner photograph trained on with its own mask', count='%d/76' % contaminated,
             detail='%d COD10K-train + %d CAMO-train; %d unchecked' % (len(in_cod), len(in_camo), counts['unchecked']),
             labels='partner mask yes; CHAMELEON GT no'),
        dict(protocol='Unlabelled target adaptation, S2R-COD as described (COD10K-train target)',
             how='partner in the unlabelled target pool', count='%d/76' % len(in_cod), detail='', labels='no'),
        dict(protocol='Unlabelled target adaptation, as the released 4040-image pool runs it',
             how='partner in the unlabelled target pool', count='%d/76' % contaminated, detail='', labels='no'),
        dict(protocol='Checkpoint selection (CAMO-250)',
             how='CHAMELEON file byte-identical to a selection image', count='%d/76' % len(byte_val),
             detail='; '.join('%s [tier %s]' % (n[:-4], tier[n]) for n, _ in byte_val),
             labels='selection GT, used to pick the checkpoint'),
    ]
    tpath = os.path.join(OUT, 'ws3_protocol_table.csv')
    with open(tpath, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    apath = os.path.join(OUT, 'ws3_adjudication.json')
    C.save_json(apath, dict(rule=dict(shear_max_deg=SHEAR_MAX, persp_max=PERSP_MAX, corr_min=CORR_MIN,
                                      overlap_min=ADJ.MIN_OVERLAP, posthoc=True),
                            rows=adj, tiers=tier, byte_identical_camo250=byte_val, table=table))
    for i, row in enumerate(table, 1):
        M.append(('protocol_row_%d' % i, row['count'], '%s -- %s' % (row['protocol'], row['detail'] or row['how'])))

    if not (agree and cell_ok):
        notes_head = ('ADJUDICATION NOT REPRODUCED. Fallback wording applies: "41 confirmed plus 9-10 by geometric matching." 50 is NOT claimed.\n')
    else:
        notes_head = ('ADJUDICATION REPRODUCED from committed code: 9 of the 10 operating-point candidates are accepted and animal-7 is rejected (no homography at full resolution). Every printed measurement in the submitted table is reproduced. 41 + 9 = 50.\n'
                      + ('DISPLAY DEFECT in the submitted table: %s. The revision prints both scale values.\n' % '; '.join(display) if display else ''))
    notes = notes_head + (
        'POST-HOC. The accept rule is declared in this script and was not pre-registered, as the adjudication never was. It is not threshold-sensitive in practice: accepted pairs sit at |shear| <= accepted_max_abs_shear_deg against a 1.0 deg bound, and the rejects fail on recovering any homography at all.\n'
        'NON-INDEPENDENCE, NOT INFLATION: none of the paper\'s endpoints uses CHAMELEON, and D2R found no score advantage on the leaked subset. The protocol table states how CHAMELEON images enter each protocol; it claims nothing about scores.\n'
        '"Labels" under supervised training means each PARTNER photograph is trained on with its own mask. The CHAMELEON GT mask itself never enters training.\n'
        '50 is a floor: unchecked images are not clean.')
    print(C.log_block('REBUTTAL_CONTAM', '.venv/bin/python rebuild/REBUTTAL/ws3_contamination.py', M,
                      thresholds=T, old_claims=OLD, artifacts=[os.path.relpath(p, C.REPO) for p in (tpath, apath)],
                      notes=notes, write=not args.no_log))
    if not (agree and cell_ok):
        raise SystemExit(2)


if __name__ == '__main__':
    main()

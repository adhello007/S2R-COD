#!/usr/bin/env python
"""REBUTTAL P2 -- log blocks for the post-hoc diagnostics the paper cites. POST-HOC.

The paper's Table 3 (boundary metrics), its threshold-sweep sentence, Table 6 (TOST)
and the CHAMELEON geometric extension were produced by committed scripts and committed
JSON, but no EXP block in results/REBUILD_LOG.txt ever recorded them. The AI-use
statement says every number is traceable to a log block. This script makes that true
for these diagnostics, by RE-EMITTING each one through its own committed script and
asserting that the re-emission matches what the paper cites. Nothing is recomputed by
new code where a committed script exists.

  --part boundary  diag_boundary.py re-run at thresholds 0.5 / 0.4 / 0.6 with --seeds
                   42,43,45 and --suffix _reemit* (run_rescore.sh), and diag_subgroups.py
                   --suffix _reemit. Asserts: per-run values equal the committed CSVs;
                   the re-emitted whole-set gaps equal diag_subgroups.json; the printed
                   Table 3 cells (table_subgroup_metrics.tex) are reproduced; and the
                   threshold-sweep ratios, which diag_emit.py carries as HARD-CODED TEXT,
                   are re-derived from the per-run sweep files.
  --part tost      figs/make_tost_table.py executed unchanged, its paper_out() pointed at
                   rebuild/REBUTTAL/out/, and the result compared byte for byte with the
                   table compiled into the submitted paper.
  --part chamext   diag_chameleon_ext.py --suffix _reemit compared with the committed JSON
                   on every field the paper uses.

Each part appends one EXP DIAG block dated 2026-11. Trains nothing.

Usage:
  .venv/bin/python rebuild/REBUTTAL/p2_diag_provenance.py --part boundary|tost|chamext [--no-log]
"""

import argparse
import csv
import json
import os
import re
import runpy
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import common as C                                            # noqa: E402

DIAG = os.path.join(C.REPO, 'rebuild/DIAG/out')
PAPERDIR = os.path.join(C.REPO, 'rebuild/FinalPaper/AD-PCH-230926')
OUT = os.path.join(_HERE, 'out')
FIGS = os.path.join(PAPERDIR, 'figs')
SEEDS3 = (42, 43, 45)
ARMS4 = ('B', 'C10', 'CSHUF', 'CINV')
TOL_RUN = 1e-12
FIELDS = ('boundary_iou', 'boundary_f', 'boundary_prec', 'boundary_rec', 'iou')


def per_run(name):
    with open(os.path.join(DIAG, name), newline='') as fh:
        return {r['runid']: r for r in csv.DictReader(fh)}


def equal_runs(a, b):
    if set(a) != set(b):
        return False, 'run sets differ: %s' % sorted(set(a) ^ set(b))
    # Per-run values are nanmeans over images that Pool.imap_unordered returns in
    # nondeterministic order, so they agree to float summation order, not bit for bit.
    worst = max(abs(float(a[r][k]) - float(b[r][k])) for r in a for k in FIELDS)
    return worst <= TOL_RUN, 'max |diff| %.3g over %d runs x %d fields (tolerance %.0e: float summation order)' % (worst, len(a), len(FIELDS), TOL_RUN)


def sweep_ratio(rows, arch, met, hi, lo):
    """diag_subgroups' rule on one per-run table: sigma_hat pooled over B/C10/CSHUF/CINV at
    three seeds, bar = 2 sigma_hat, ratio = |mean paired difference| / bar."""
    v = {m: np.array([float(rows['%s_%s_s%d' % (arch, m, s)][met]) for s in SEEDS3]) for m in ARMS4}
    sh = np.sqrt(sum(((x - x.mean()) ** 2).sum() for x in v.values()) / (len(ARMS4) * (len(SEEDS3) - 1)))
    d = v[hi] - v[lo]
    pos = int((d > 0).sum())
    return abs(d.mean()) / (2 * sh), max(pos, 3 - pos)


def part_boundary(M, T):
    for suf, ref in (('_reemit', 'diag_boundary_per_run.csv'),
                     ('_reemit_t0.40', 'diag_boundary_per_run_t0.40.csv'),
                     ('_reemit_t0.60', 'diag_boundary_per_run_t0.60.csv')):
        ok, why = equal_runs(per_run('diag_boundary_per_run%s.csv' % suf), per_run(ref))
        M.append(('boundary_per_run%s_vs_committed' % suf, why, ref))
        T.append(('diag_boundary.py re-emission %s equals committed %s' % (suf, ref), ok))
    new = json.load(open(os.path.join(DIAG, 'diag_subgroups_reemit.json')))['whole_set']
    old = json.load(open(os.path.join(DIAG, 'diag_subgroups.json')))['whole_set']
    worst = 0.0
    for key in old:
        worst = max(worst, abs(new[key]['bar'] - old[key]['bar']))
        for g in old[key]['gaps']:
            worst = max(worst, abs(new[key]['gaps'][g]['delta'] - old[key]['gaps'][g]['delta']))
    M.append(('subgroups_whole_set_max_abs_diff', '%.3g' % worst, 'diag_subgroups_reemit.json vs diag_subgroups.json'))
    T.append(('diag_subgroups.py re-emission equals the committed whole-set gaps and bars', worst == 0.0))

    # the printed Table 3
    nice = {'Boundary IoU': 'boundary_iou', 'Boundary $F$': 'boundary_f', 'IoU': 'iou'}
    arch = {'SINet': 'SINet', 'SINet-v2': 'SINetv2'}
    cols = ('C10-B', 'CINV-B', 'C10-CSHUF', 'C10-CINV')
    pat = re.compile(r'^(SINet(?:-v2)?) & (Boundary IoU|Boundary \$F\$|IoU) & \$([\d.]+)\$ & (.*) \\\\')
    cell = re.compile(r'\$([+-][\d.]+)\$ (\d/3)')
    nrow, bad = 0, []
    for line in open(os.path.join(PAPERDIR, 'table_subgroup_metrics.tex')):
        m = pat.match(line.strip())
        if not m:
            continue
        nrow += 1
        w = new['%s|%s' % (arch[m.group(1)], nice[m.group(2)])]
        printed = cell.findall(m.group(4))
        mine = [('%+.4f' % w['gaps'][c]['delta'], w['gaps'][c]['sign_consistent']) for c in cols]
        if '%.4f' % w['bar'] != m.group(3) or printed != mine:
            bad.append((m.group(1), m.group(2), m.group(3), printed, '%.4f' % w['bar'], mine))
    M.append(('table3_rows_reproduced', '%d/%d' % (nrow - len(bad), nrow), 'table_subgroup_metrics.tex, bar + 4 gaps + sign each'))
    T.append(('all 6 printed rows of Table 3 reproduced from the re-emission', nrow == 6 and not bad))

    # the threshold sweep that diag_emit.py hard-codes
    tabs = {0.4: per_run('diag_boundary_per_run_reemit_t0.40.csv'),
            0.5: per_run('diag_boundary_per_run_reemit.csv'),
            0.6: per_run('diag_boundary_per_run_reemit_t0.60.csv')}
    claim = {('C10', 'B'): ('1.39', '1.37', '1.23'), ('CINV', 'B'): ('1.25', '1.34', '1.26')}
    for (hi, lo), printed in claim.items():
        got = [sweep_ratio(tabs[t], 'SINet', 'boundary_iou', hi, lo) for t in (0.4, 0.5, 0.6)]
        mine = tuple('%.2f' % r for r, _ in got)
        M.append(('sweep_%s-%s_ratio_t0.4/0.5/0.6' % (hi, lo), '/'.join(mine) + '  signs ' + '/'.join('%d/3' % s for _, s in got),
                  'paper (hard-coded in diag_emit.py): %s' % '/'.join(printed)))
        T.append(('sweep %s-%s ratios reproduce the paper\'s %s' % (hi, lo, '/'.join(printed)), mine == printed))
    for (hi, lo), printed in ((('C10', 'CSHUF'), '0.52'), (('C10', 'CINV'), '0.14')):
        rs = {t: sweep_ratio(tabs[t], 'SINet', 'boundary_iou', hi, lo)[0] for t in tabs}
        mx = max(rs.values())
        M.append(('sweep_%s-%s_max_ratio' % (hi, lo), '%.4f (at t=%.1f)' % (mx, max(rs, key=rs.get)),
                  'paper: "never exceed %sx"' % printed))
        T.append(('sweep %s-%s: the paper\'s bound "never exceeds %sx" holds' % (hi, lo, printed), mx <= float(printed)))
        T.append(('sweep %s-%s: the printed %sx equals the measured maximum at 2 dp' % (hi, lo, printed), '%.2f' % mx == printed))
    return ('rebuild/DIAG/diag_boundary.py --seeds 42,43,45 [...] --suffix _reemit*; rebuild/DIAG/diag_subgroups.py --suffix _reemit',
            ['rebuild/DIAG/out/diag_boundary_per_run_reemit.csv', 'rebuild/DIAG/out/diag_boundary_per_run_reemit_t0.40.csv',
             'rebuild/DIAG/out/diag_boundary_per_run_reemit_t0.60.csv', 'rebuild/DIAG/out/diag_subgroups_reemit.json'],
            'DIAG.3/DIAG.5 RE-EMITTED, POST-HOC (2026-11). The paper\'s Table 3 and its threshold-sweep sentence, previously traceable to committed JSON/CSV but to no log block. These are THREE-SEED values, exactly as the paper prints them. The eight-seed re-score is EXP REBUTTAL_STATS (bnd8_*), and it does not reproduce the SINet effect: see that block.\n'
            'The sweep ratios were HARD-CODED TEXT in diag_emit.py. Here they are derived from the per-run sweep files by diag_subgroups\' own rule. Five of six printed values reproduce. The C10-CSHUF maximum is 0.505x, printed as "0.52x". The bound it states is true; the revision prints 0.51.')


def part_tost(M, T):
    sys.path.insert(0, FIGS)
    import _repo
    os.makedirs(OUT, exist_ok=True)
    _repo.paper_out = lambda name: os.path.join(OUT, 'reemit_' + name)
    runpy.run_path(os.path.join(FIGS, 'make_tost_table.py'), run_name='__main__')
    new = open(os.path.join(OUT, 'reemit_table_tost_equivalence.tex'), 'rb').read()
    old = open(os.path.join(PAPERDIR, 'table_tost_equivalence.tex'), 'rb').read()
    M.append(('table6_reemit_bytes', '%d vs %d' % (len(new), len(old)), 'make_tost_table.py output (LF) vs the compiled table'))
    M.append(('table6_compiled_line_endings', 'CRLF' if b'\r\n' in old else 'LF', 'the compiled copy was saved with Windows line endings'))
    T.append(('make_tost_table.py re-emits the submitted Table 6 exactly, line endings normalised',
              new.replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n')))
    return ('runpy rebuild/FinalPaper/AD-PCH-230926/figs/make_tost_table.py (paper_out -> rebuild/REBUTTAL/out/)',
            ['rebuild/REBUTTAL/out/reemit_table_tost_equivalence.tex'],
            'DIAG.1 / Table 6 RE-EMITTED, POST-HOC (2026-11). The committed script runs unchanged; only its output path is redirected so the paper\'s file is not touched. The 16 rows are also reproduced value by value inside EXP REBUTTAL_STATS.')


def part_chamext(M, T):
    new = json.load(open(os.path.join(DIAG, 'diag_chameleon_ext_reemit.json')))
    old = json.load(open(os.path.join(DIAG, 'diag_chameleon_ext.json')))
    keys = ('headline', 'n_new_matches', 'n_new_matches_at_operating_point', 'n_unchecked', 'operating_point_inliers')
    for k in keys:
        M.append(('chamext_%s' % k, new.get(k), 'committed: %s' % old.get(k)))
        T.append(('re-emitted %s equals committed' % k, new.get(k) == old.get(k)))
    rk = lambda rs: {(r['chameleon_image'], r['best_partner'], r['n_inlier'], r['at_operating_point'], r['verdict']) for r in rs}
    same_rows = rk(new['rows']) == rk(old['rows'])
    T.append(('every candidate row (image, partner, inliers, operating point, verdict) equals committed', same_rows))
    same_cal = new['calibration'] == old['calibration']
    T.append(('calibration (positives, negatives, thresholds, recall) equals committed', same_cal))
    nc_same = {k: new['negative_control'][k] for k in ('n_flagged', 'n_flagged_at_operating_point', 'n_sampled', 'inlier_max')} == \
              {k: old['negative_control'][k] for k in ('n_flagged', 'n_flagged_at_operating_point', 'n_sampled', 'inlier_max')}
    T.append(('NC4K negative control (sampled, flagged, max inliers) equals committed', nc_same))
    return ('.venv/bin/python rebuild/DIAG/diag_chameleon_ext.py --workers 40 --suffix _reemit',
            ['rebuild/DIAG/out/diag_chameleon_ext_reemit.json'],
            'DIAG.4 RE-EMITTED, POST-HOC (2026-11). The extension\'s own headline is 41 + 10 = 51 at its operating point. The paper\'s 50 comes from the adjudication step, which EXP REBUTTAL_CONTAM re-runs and logs (9 accepted, animal-7 rejected). The two blocks together are the traceable chain 41 -> 41 + 10 candidates -> 41 + 9 = 50.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', required=True, choices=('boundary', 'tost', 'chamext'))
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    M, T = [], []
    cmd, arts, notes = dict(boundary=part_boundary, tost=part_tost, chamext=part_chamext)[args.part](M, T)
    print(C.log_block('DIAG', '.venv/bin/python rebuild/REBUTTAL/p2_diag_provenance.py --part %s   [re-emits: %s]' % (args.part, cmd),
                      M, thresholds=T, artifacts=arts, notes=notes, write=not args.no_log))
    if not all(ok for _, ok in T):
        raise SystemExit(2)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""REBUTTAL WS1 -- the statistics package. POST-HOC throughout.

Every reviewer raised the same objection: the targeting-vs-random gap on the primary
cell, +0.0024 [-0.0020, +0.0067], does not pass equivalence at +/-0.005, so the
result is "no evidence of benefit", not "no meaningful effect". This script measures
how far that objection reaches, on the committed SE campaign's eight seeds per arm,
without re-deciding any verdict.

Reproduction gate, before anything new is emitted: the 16 Welch rows of the
submitted Table 6 (table_tost_equivalence.tex, as compiled into the paper) are
recomputed with make_results.py's welch_tost and must match the printed strings
EXACTLY. If they do not, the script halts.

Then, per architecture x endpoint, for C10-B, C10-CSHUF, C10-CINV, CSHUF-CINV, and the
two contrasts the paper does not tabulate (CINV-B, CSHUF-B):
  * Welch: mean difference, 95% CI, TOST p at delta in {0.005, 0.0071}, smallest delta
  * paired by seed: the same, on the per-seed differences (df = n - 1)
  * within-seed Pearson r between the two arms, and the sign count
  * minimum detectable effect at 80% power, two-sided alpha = .05, n = 8 per arm
B-vs-C overlap at all eight seeds and the corrected effective contrast.
The eight-seed boundary-metric re-score (DIAG.3 run over SE's predictions, written by
rebuild/REBUTTAL/run_rescore.sh as diag_boundary_per_run_se8.csv), read against the
SE campaign's own pooled-sigma rule for comparability, with Welch intervals beside it.

0.0071 is half the method's own gain (PREREGISTRATION.md SS2.9) and was the ABC
campaign's pre-registered SENSITIVITY TARGET. It is not, and is never called, a
declared equivalence margin. Nothing here is a campaign verdict.

Trains nothing. Reads committed CSVs. Writes rebuild/REBUTTAL/out/.

Usage:
  .venv/bin/python rebuild/REBUTTAL/ws1_stats.py [--no-log]
"""

import argparse
import csv
import json
import os
import re
import sys

import numpy as np
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'FinalPaper'))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'ABC'))
import common as C                                            # noqa: E402
import make_results as MR                                     # noqa: E402
import abc_common as A                                        # noqa: E402

OUT = os.path.join(_HERE, 'out')
SE = os.path.join(C.REPO, 'rebuild/ABC/out/se')
TABLE6 = os.path.join(C.REPO, 'rebuild/FinalPaper/AD-PCH-230926/table_tost_equivalence.tex')
BOUND_SE8 = os.path.join(C.REPO, 'rebuild/DIAG/out/diag_boundary_per_run_se8.csv')
BOUND_3 = os.path.join(C.REPO, 'rebuild/DIAG/out/diag_boundary_per_run.csv')
CELLS = [(a, e) for a in ('SINet', 'SINetv2') for e in ('COD10K', 'NC4K')]
TABLE6_GAPS = [('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV')]
EXTRA_GAPS = [('CINV', 'B'), ('CSHUF', 'B')]
MARGINS = (0.005, 0.0071)
SEEDS = (42, 43, 45, 46, 47, 48, 49, 50)
NAME = {'SINet': 'SINet', 'SINetv2': 'SINet-v2'}
ARMS4 = ('B', 'C10', 'CSHUF', 'CINV')


def tost_p(d, se, df, delta):
    return float(max(stats.t.sf((d + delta) / se, df), stats.t.cdf((d - delta) / se, df)))


def welch(a, b):
    w = MR.welch_tost(a, b)                     # the paper's own function, delta = MR.DELTA
    assert MR.DELTA == 0.005
    out = dict(d=w['diff'], lo=w['ci95'][0], hi=w['ci95'][1], dmin=w['bound'], se=w['se'], df=w['df'])
    for m in MARGINS:
        out['p%s' % m] = tost_p(w['diff'], w['se'], w['df'], m)
    return out


def paired(a, b):
    x = np.asarray(a) - np.asarray(b)
    n = len(x)
    d, se, df = float(x.mean()), float(x.std(ddof=1) / np.sqrt(n)), n - 1
    t95, t90 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    out = dict(d=d, lo=d - t95 * se, hi=d + t95 * se, dmin=abs(d) + t90 * se, se=se, df=df,
               pos=int((x > 0).sum()), n=n)
    for m in MARGINS:
        out['p%s' % m] = tost_p(d, se, df, m)
    return out


def load_se():
    by = {}
    with open(os.path.join(SE, 'abc_metrics.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            by.setdefault((r['arch'], r['endpoint']), {}).setdefault(r['arm'], {})[int(r['seed'])] = float(r['Sm'])
    for cell in CELLS:
        for arm in ARMS4:
            assert sorted(by[cell][arm]) == list(SEEDS), (cell, arm)
    return by


def table6_rows():
    """The printed rows of the submitted Table 6, as strings."""
    pat = re.compile(r'^(SINet(?:-v2)?) & (COD10K|NC4K) & \$\\mathrm\{(\w+)\}-\\mathrm\{(\w+)\}\$ & '
                     r'\$([+-][\d.]+)\$ & \$\[([+-][\d.]+), ([+-][\d.]+)\]\$ & (?:\\textbf\{)?([\d.]+)\}? & \$([\d.]+)\$')
    rows = {}
    for line in open(TABLE6):
        m = pat.match(line.strip())
        if m:
            rows[(m.group(1), m.group(2), m.group(3), m.group(4))] = m.groups()[4:]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    by = load_se()
    M, T = [], []

    # --- gate: reproduce the submitted Table 6 exactly -----------------------------------
    printed = table6_rows()
    mism = []
    for arch, ep in CELLS:
        for hi, lo in TABLE6_GAPS:
            w = MR.welch_tost([by[(arch, ep)][hi][s] for s in SEEDS], [by[(arch, ep)][lo][s] for s in SEEDS])
            mine = ('%+.4f' % w['diff'], '%+.4f' % w['ci95'][0], '%+.4f' % w['ci95'][1],
                    '%.4f' % w['p_tost'], '%.4f' % w['bound'])
            if printed.get((NAME[arch], ep, hi, lo)) != mine:
                mism.append((arch, ep, hi, lo, printed.get((NAME[arch], ep, hi, lo)), mine))
    T.append(('all 16 printed rows of Table 6 parsed', len(printed) == 16))
    T.append(('all 16 Welch rows of Table 6 reproduced exactly (Delta, CI, TOST p, smallest delta)', not mism))
    M.append(('table6_rows_reproduced', '%d/16' % (16 - len(mism)), os.path.relpath(TABLE6, C.REPO)))
    if mism or len(printed) != 16:
        print(mism)
        raise SystemExit('WS1 HALT: Table 6 is not reproduced; nothing new is emitted')

    # --- intervals, both forms, both margins -----------------------------------------------
    rows = []
    for arch, ep in CELLS:
        cell = by[(arch, ep)]
        for hi, lo in TABLE6_GAPS + EXTRA_GAPS:
            a = [cell[hi][s] for s in SEEDS]
            b = [cell[lo][s] for s in SEEDS]
            w, p = welch(a, b), paired(a, b)
            r = float(np.corrcoef(a, b)[0, 1])
            rows.append(dict(arch=arch, endpoint=ep, contrast='%s-%s' % (hi, lo),
                             in_table6=(hi, lo) in TABLE6_GAPS, delta=round(w['d'], 6),
                             welch_lo=round(w['lo'], 6), welch_hi=round(w['hi'], 6),
                             welch_p005=round(w['p0.005'], 4), welch_p0071=round(w['p0.0071'], 4),
                             welch_dmin=round(w['dmin'], 6),
                             paired_lo=round(p['lo'], 6), paired_hi=round(p['hi'], 6),
                             paired_p005=round(p['p0.005'], 4), paired_p0071=round(p['p0.0071'], 4),
                             paired_dmin=round(p['dmin'], 6), within_seed_r=round(r, 4),
                             sign_pos='%d/8' % p['pos']))
            M.append(('%s_%s_%s-%s' % (arch, ep, hi, lo),
                      'D %+.4f | W [%+.4f, %+.4f] p.005 %.4f p.0071 %.4f dmin %.4f | P [%+.4f, %+.4f] p.005 %.4f p.0071 %.4f dmin %.4f | r %+.2f | pos %d/8'
                      % (w['d'], w['lo'], w['hi'], w['p0.005'], w['p0.0071'], w['dmin'],
                         p['lo'], p['hi'], p['p0.005'], p['p0.0071'], p['dmin'], r, p['pos']),
                      'Table 6 contrast' if (hi, lo) in TABLE6_GAPS else 'NOT in Table 6 -- new post-hoc contrast'))
    t6 = [r for r in rows if r['in_table6']]
    for m, key in ((0.005, 'p005'), (0.0071, 'p0071')):
        for form in ('welch', 'paired'):
            k = sum(1 for r in t6 if r['%s_%s' % (form, key)] < 0.05)
            M.append(('equivalent_%s_at_%s' % (form, m), '%d/16' % k, 'Table 6 contrasts, TOST p < 0.05'))
    cb = [r for r in rows if r['contrast'] == 'C10-B']
    M.append(('C10-B_equivalent_at_0.0071_all_cells',
              all(r['welch_p0071'] < 0.05 and r['paired_p0071'] < 0.05 for r in cb), 'Welch and paired'))
    excl = [r for r in rows if r['welch_lo'] > 0 or r['welch_hi'] < 0 or r['paired_lo'] > 0 or r['paired_hi'] < 0]
    M.append(('intervals_excluding_zero',
              '; '.join('%s %s %s (W [%+.4f,%+.4f], P [%+.4f,%+.4f])'
                        % (r['arch'], r['endpoint'], r['contrast'], r['welch_lo'], r['welch_hi'],
                           r['paired_lo'], r['paired_hi']) for r in excl) or 'none',
              'unadjusted, %d comparisons' % len(rows)))

    # --- minimum detectable effect, 80% power, two-sided .05, n = 8/arm -------------------
    for arch, ep in CELLS:
        b = np.array([by[(arch, ep)]['B'][s] for s in SEEDS])
        c = np.array([by[(arch, ep)]['C10'][s] for s in SEEDS])
        sp = np.sqrt((b.var(ddof=1) + c.var(ddof=1)) / 2)
        n, df = len(SEEDS), 2 * len(SEEDS) - 2
        mde = (stats.t.ppf(0.975, df) + stats.t.ppf(0.80, df)) * sp * np.sqrt(2 / n)
        M.append(('MDE80_%s_%s_C10-B' % (arch, ep), '%.4f' % mde, 'pooled sd(B, C10) %.5f, df %d' % (sp, df)))

    # --- overlap and effective contrast -----------------------------------------------------
    c10 = set(open(os.path.join(SE, 'abc_stems_C_a1.0.txt')).read().split())
    cs = set(open(os.path.join(SE, 'abc_stems_CSHUF.txt')).read().split())
    ci = set(open(os.path.join(SE, 'abc_stems_CINV.txt')).read().split())
    pool = len(A.base_stems()) + A.BUDGET
    share = A.BUDGET / pool
    ov = {}
    for s in SEEDS:
        bs = set(open(os.path.join(SE, 'abc_stems_B_s%d.txt' % s)).read().split())
        assert len(bs) == A.BUDGET
        assert bs == set(A.arm_b_stems(s)), 'stem file for seed %d does not match the committed draw' % s
        ov[s] = len(bs & c10)
    diff_frac = 1 - np.mean(list(ov.values())) / A.BUDGET
    cc = [len(c10 & cs), len(c10 & ci), len(cs & ci)]
    M += [('overlap_B_C10_per_seed', ' '.join('s%d:%d' % kv for kv in ov.items()),
           'of %d; chance %.1f' % (A.BUDGET, A.BUDGET ** 2 / len(A.base_stems()))),
          ('B_C10_differing_fraction', '%.4f' % diff_frac, 'mean over 8 seeds'),
          ('injected_share_of_pool', '%.4f (%d/%d)' % (share, A.BUDGET, pool), ''),
          ('effective_contrast_C10-B', '%.4f' % (share * diff_frac), 'share x differing fraction; corrects App. C "8.8%"'),
          ('effective_contrast_C_family', '%.4f .. %.4f' % (share * (1 - max(cc) / A.BUDGET), share * (1 - min(cc) / A.BUDGET)),
           'C10|CSHUF, C10|CINV, CSHUF|CINV overlaps %s -- what App. C\'s 48%% / 8.8%% actually describe' % cc)]

    # --- the eight-seed boundary re-score -------------------------------------------------
    br = {}
    with open(BOUND_SE8, newline='') as fh:
        for r in csv.DictReader(fh):
            br.setdefault(r['arch'], {}).setdefault(r['arm'], {})[int(r['seed'])] = r
    old = {}
    with open(BOUND_3, newline='') as fh:
        for r in csv.DictReader(fh):
            old[r['runid']] = r
    same3 = all(abs(float(br[a][m][s][k]) - float(old['%s_%s_s%d' % (a, m, s)][k])) < 1e-12
                for a in br for m in ARMS4 for s in (42, 43, 45) for k in ('boundary_iou', 'boundary_f', 'iou'))
    T.append(('8-seed boundary re-score reproduces the committed 3-seed per-run values at seeds 42/43/45', same3))
    brows = []
    for arch in ('SINet', 'SINetv2'):
        assert all(sorted(br[arch][m]) == list(SEEDS) for m in ARMS4), arch
        for met in ('boundary_iou', 'boundary_f', 'iou'):
            v = {m: np.array([float(br[arch][m][s][met]) for s in SEEDS]) for m in ARMS4}
            ss = sum(((x - x.mean()) ** 2).sum() for x in v.values())
            sh = float(np.sqrt(ss / (len(ARMS4) * (len(SEEDS) - 1))))
            bar = 2 * sh
            for hi, lo in (('C10', 'B'), ('CINV', 'B'), ('CSHUF', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV')):
                d = v[hi] - v[lo]
                pos = int((d > 0).sum())
                sc = max(pos, 8 - pos)
                dm = float(d.mean())
                ver = ('WITHIN NOISE' if abs(dm) <= bar else
                       'REAL EFFECT' if sc >= 7 and dm > 0 else
                       'REAL REGRESSION' if sc >= 7 and dm < 0 else 'INCONCLUSIVE')
                w = welch(list(v[hi]), list(v[lo]))
                brows.append(dict(arch=arch, metric=met, contrast='%s-%s' % (hi, lo), delta=round(dm, 6),
                                  bar=round(bar, 6), ratio=round(abs(dm) / bar, 3), sign='%d/8' % sc,
                                  se_rule=ver, welch_lo=round(w['lo'], 6), welch_hi=round(w['hi'], 6)))
                M.append(('bnd8_%s_%s_%s-%s' % (arch, met, hi, lo),
                          '%+.4f  bar %.4f (%.2fx)  sign %d/8  %s  | W [%+.4f, %+.4f]'
                          % (dm, bar, abs(dm) / bar, sc, ver, w['lo'], w['hi']),
                          'SE-style 2*sigma_hat pooled over 4 arms x 8 seeds, df 28, sign >= 7/8; POST-HOC'))

    for name, data in (('ws1_intervals.csv', rows), ('ws1_boundary8.csv', brows)):
        with open(os.path.join(OUT, name), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    prim = [r for r in rows if r['arch'] == 'SINet' and r['endpoint'] == 'COD10K' and r['contrast'] == 'C10-B'][0]
    M.append(('rule_out_sentence_X', '%+.4f (95%% CI upper, Welch); %+.4f at the one-sided 5%% TOST bound'
              % (prim['welch_hi'], prim['welch_dmin']), 'SINet COD10K C10-B'))
    notes = ('POST-HOC. No verdict is re-decided. The SE campaign\'s verdicts stand on its frozen 2*sigma_hat / >=7/8 rule. Every interval, TOST and boundary number here is a non-decisional supplement and is labelled post-hoc wherever reported.\n'
             '0.0071 is the ABC campaign\'s pre-registered SENSITIVITY TARGET (half the MT->Ours gap of 0.0142, PREREGISTRATION.md SS2.9). It is not a declared equivalence margin. 0.005 is the reviewers\' margin.\n'
             'No multiplicity correction: %d interval comparisons on Sa and %d on boundary metrics are reported unadjusted. Intervals that exclude zero are listed, not promoted.\n'
             'CINV-B and CSHUF-B are NOT in Table 6 and NOT among SE\'s frozen gaps.\n'
             'The boundary re-score reads SE-style bars (pooled over B/C10/CSHUF/CINV at eight seeds, sign >= 7/8) for comparability with Table 3\'s three-seed reading. It is not a pre-registered test.' % (len(rows), len(brows)))
    print(C.log_block('REBUTTAL_STATS', '.venv/bin/python rebuild/REBUTTAL/ws1_stats.py', M, thresholds=T,
                      artifacts=['rebuild/REBUTTAL/out/ws1_intervals.csv', 'rebuild/REBUTTAL/out/ws1_boundary8.csv'],
                      notes=notes, write=not args.no_log))


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Independent verification pass (brief §7). Deliberately does NOT import statlib or any analysis script.

Recomputes headline numbers from raw per-run tables and committed manifests with separate code
(plain Python + scipy.stats), then checks that each number appears, as stated, in the documents that
cite it. Also: relative-link check over all Markdown, character count of the OpenReview text, scan of
reviewer-facing text for private paths, manuscript integrity re-run.

Exit code 0 only if every check passes. Writes EXPERIMENT_LOGS/AUDIT_independent.json.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
REB = os.path.dirname(SR)
RT = os.path.join(SR, 'RESULT_TABLES')
SEEDS = [42, 43, 45, 46, 47, 48, 49, 50]
results = []


def check(name, ok, detail=''):
    results.append(dict(check=name, passed=bool(ok), detail=str(detail)[:400]))


def mean(x):
    return sum(x) / len(x)


def sd(x):
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def doc(name):
    return open(os.path.join(SR, name), encoding='utf-8').read()


def fmt(v, nd=4, sign=True):
    s = ('%+.' + str(nd) + 'f') % v if sign else ('%.' + str(nd) + 'f') % v
    return s.replace('-', '−') if s.startswith('-') else s


def appears(text, s):
    return s in text or s.replace('−', '-') in text


# ------------------------------------------------------------------ 1. S_alpha re-score vs committed
mine = {(r['runid'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(SR, 'RUNS/an01/an01_rescored_full.csv')))}
comm = {(r['runid'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(WT, 'rebuild/ABC/out/se/abc_metrics.csv')))}
keys = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
mism = [(k, m) for k in comm for m in keys if '%.6f' % float(mine[k][m]) != comm[k][m]]
check('AN-01 all committed metrics reproduce at 6 dp', len(comm) == 128 and not mism, '%d rows, %d mismatches' % (len(comm), len(mism)))

# ------------------------------------------------------------------ 2. paired / Welch primary and cells
S = defaultdict(dict)
for r in mine.values():
    S[(r['arch'], r['endpoint'], r['arm'])][int(r['seed'])] = float(r['Sm'])
reb, short = doc('FINAL_UPDATED_REBUTTAL.md'), doc('FINAL_UPDATED_REBUTTAL_OPENREVIEW.md')
doc1 = doc('DOC-01_MANUSCRIPT_PROPOSED_EDITS.md')
for arch, ep in (('SINet', 'COD10K'), ('SINet', 'NC4K'), ('SINetv2', 'COD10K'), ('SINetv2', 'NC4K')):
    x = [S[(arch, ep, 'C10')][s] for s in SEEDS]
    y = [S[(arch, ep, 'B')][s] for s in SEEDS]
    d = [p - q for p, q in zip(x, y)]
    se = sd(d) / math.sqrt(8)
    t95 = stats.t.ppf(0.975, 7)
    lo, hi = mean(d) - t95 * se, mean(d) + t95 * se
    w = stats.ttest_ind(x, y, equal_var=False)
    ci_w = w.confidence_interval(0.95)
    tost = max(stats.t.sf((mean(d) + 0.005) / se, 7), stats.t.cdf((mean(d) - 0.005) / se, 7))
    s_p = '[%s, %s]' % (fmt(lo), fmt(hi))
    s_w = '[%s, %s]' % (fmt(ci_w.low), fmt(ci_w.high))
    check('rebuttal cites paired CI %s %s %s' % (arch, ep, s_p), appears(reb, s_p))
    check('rebuttal cites Welch CI %s %s %s' % (arch, ep, s_w), appears(reb, s_w))
    check('TOST paired p %s %s = %.3f cited' % (arch, ep, tost), appears(reb, '%.3f' % tost))
    if (arch, ep) == ('SINet', 'COD10K'):
        u1 = mean(d) + stats.t.ppf(0.95, 7) * se
        r_xy = stats.pearsonr(x, y)[0]
        for t in (reb, short):
            check('primary paired CI in both versions', appears(t, s_p))
        check('primary one-sided bound +%.4f' % u1, appears(reb, fmt(u1)) and appears(short, fmt(u1)))
        check('primary r = %.2f' % r_xy, appears(short, 'r = ' + fmt(r_xy, 2)))
        check('primary 6/8 seeds positive', sum(v > 0 for v in d) == 6 and '6 of 8 seeds' in reb)
        check('DOC-01 Edit 3 paired CI', appears(doc1, '$[%s, %s]$' % (('%+.4f' % lo), ('%+.4f' % hi))))

# ------------------------------------------------------------------ 3. overlap from raw stem files
stems = lambda f: set(l.strip() for l in open(os.path.join(WT, 'rebuild/ABC/out/se', f)) if l.strip())  # noqa: E731
c10 = stems('abc_stems_C_a1.0.txt')
inter = [len(stems('abc_stems_B_s%d.txt' % s) & c10) for s in SEEDS]
frac = mean([(1000 - i) / 5447 for i in inter])
check('B∩C10 range %d–%d' % (min(inter), max(inter)), min(inter) == 209 and max(inter) == 246 and '209–246' in reb and '209–246' in short)
check('B vs C10 differing share of pool %.1f%%' % (100 * frac), '%.1f%%' % (100 * frac) == '14.1%' and '14.1%' in reb and '14.1%' in short)
cf = [1000 - len(stems(p) & stems(q)) for p, q in (('abc_stems_C_a1.0.txt', 'abc_stems_CSHUF.txt'),
                                                  ('abc_stems_C_a1.0.txt', 'abc_stems_CINV.txt'),
                                                  ('abc_stems_CSHUF.txt', 'abc_stems_CINV.txt'))]
check('C-family differing %d–%d of 1000 (45–51%%)' % (min(cf), max(cf)), min(cf) == 452 and max(cf) == 511)
check('C-family share of pool 8.3–9.4%%', '%.1f' % (100 * min(cf) / 5447) == '8.3' and '%.1f' % (100 * max(cf) / 5447) == '9.4')

# ------------------------------------------------------------------ 4. boundary headline from per-run table
B = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(SR, 'RUNS/exp02/exp02_per_run.csv'))):
    if r['endpoint'] == 'COD10K' and r['thresh'] == '0.5':
        B[(r['arch'], r['arm'])][int(r['seed'])] = float(r['boundary_iou'])
for arch in ('SINet', 'SINetv2'):
    for arm in ('C10', 'CINV'):
        d = [B[(arch, arm)][s] - B[(arch, 'B')][s] for s in SEEDS]
        se = sd(d) / math.sqrt(8)
        t95 = stats.t.ppf(0.975, 7)
        s_ci = '%s [%s, %s]' % (fmt(mean(d)), fmt(mean(d) - t95 * se), fmt(mean(d) + t95 * se))
        check('boundary %s %s-B %s cited' % (arch, arm, s_ci), appears(reb, s_ci))
    # three-seed bar ratio reproduces the manuscript
    for arm, want in (('C10', '1.37'), ('CINV', '1.34')):
        d3 = [B[(arch, arm)][s] - B[(arch, 'B')][s] for s in (42, 43, 45)]
        pooled = math.sqrt(sum(sum((B[(arch, m)][s] - mean([B[(arch, m)][t] for t in (42, 43, 45)])) ** 2
                                   for s in (42, 43, 45)) for m in ('B', 'C10', 'CSHUF', 'CINV')) / 8)
        if arch == 'SINet':
            check('3-seed %s-B bar ratio = %s' % (arm, want), '%.2f' % (abs(mean(d3)) / (2 * pooled)) == want)
# interaction, independent: Welch on per-seed differences
for arm, want in (('C10', '+0.0044 [−0.0075, +0.0163]'), ('CINV', '+0.0065 [−0.0001, +0.0131]')):
    dS = [B[('SINet', arm)][s] - B[('SINet', 'B')][s] for s in SEEDS]
    dV = [B[('SINetv2', arm)][s] - B[('SINetv2', 'B')][s] for s in SEEDS]
    w = stats.ttest_ind(dS, dV, equal_var=False)
    ci = w.confidence_interval(0.95)
    got = '%s [%s, %s]' % (fmt(mean(dS) - mean(dV)), fmt(ci.low), fmt(ci.high))
    check('interaction %s = %s' % (arm, got), got == want and appears(reb, got))

# ------------------------------------------------------------------ 5. EXP-01 preflight
pf = {int(r['N']): float(r['DC_mean']) for r in csv.DictReader(open(os.path.join(RT, 'EXP-01_preflight.csv')))}
for n, s in ((1000, '14.1%'), (2000, '17.2%'), (3000, '13.1%')):
    check('preflight DC(%d) = %s' % (n, s), '%.1f%%' % (100 * pf[n]) == s and s in short)
by = [r for r in csv.DictReader(open(os.path.join(RT, 'EXP-01_preflight_by_seed.csv'))) if r['N'] == '1000']
check('preflight N=1000 matches raw stems', sorted(int(r['intersection']) for r in by) == sorted(inter))

# ------------------------------------------------------------------ 6. CHAMELEON from detector JSON + ledgers
tA = json.load(open(os.path.join(SR, 'RUNS/an05/tierA_target_4040.json')))
check('Tier A 41 and sweep 11/26/37/40/41', tA['contaminated']['n'] == 41 and
      [tA['tolerance_sweep'][k] for k in ('1.0', '2.0', '3.0', '5.0', '6.0')] == [11, 26, 37, 40, 41])
P = list(csv.DictReader(open(os.path.join(RT, 'AN-05_chameleon_pairs.csv'))))
cnt = defaultdict(int)
for r in P:
    cnt[r['status']] += 1
cod = sum(1 for r in P if r['status'] == 'confirmed' and r['in_cod10k_train'] == 'True')
check('76 = 50 + 16 + 10; 44 in COD10K-train', len(P) == 76 and cnt['confirmed'] == 50 and cnt['unchecked'] == 16
      and cnt['tierA_checked_no_match'] == 10 and cod == 44)
tt = json.load(open(os.path.join(SR, 'RUNS/an05/tierA_cod10k_test.json')))
tv = json.load(open(os.path.join(SR, 'RUNS/an05/tierA_camo250_val.json')))
test_names = {p['image_a'][:-4] for p in tt['pairs']}
check('32 CHAMELEON photos in COD10K-test incl. all 16 unchecked',
      len(test_names) == 32 and all(r['chameleon'] in test_names for r in P if r['status'] == 'unchecked'))
check('4 in CAMO-250', len({p['image_a'] for p in tv['pairs']}) == 4)
X = list(csv.DictReader(open(os.path.join(RT, 'AN-05_cross_benchmark.csv'))))
check('74/76 duplicated somewhere', sum(r['duplicated_anywhere_checked'] == 'True' for r in X) == 74 and '74 of 76' in reb)
M = list(csv.DictReader(open(os.path.join(RT, 'AN-05_mask_release.csv'))))
ma, mr = mean([float(r['mae_author']) for r in M]), mean([float(r['mae_repo']) for r in M])
check('mask MAE 0.2196 / 0.0816', '%.4f' % ma == '0.2196' and '%.4f' % mr == '0.0816' and '0.2196' in short)
pl = [int(r['n_cham_partners_appended']) for r in csv.DictReader(open(os.path.join(RT, 'AN-05_pseudolabel_exposure.csv')))]
check('pseudo-label re-use 14–32 per run', min(pl) == 14 and max(pl) == 32 and '14–32' in short)

# ------------------------------------------------------------------ 6b. AN-04: independent k-NN recall (numpy, not A3 code)
import numpy as np   # noqa: E402
E0 = os.path.join(DR, 'rebuild/E0/cache')
nm = json.load(open(os.path.join(E0, 'dinoL518_names.json')))
tgt = np.load(os.path.join(E0, 'dinoL518_tgt_cls.npy')).astype(np.float64)
loc = np.load(os.path.join(E0, 'dinoL518_local_cls.npy')).astype(np.float64)
tgt /= np.linalg.norm(tgt, axis=1, keepdims=True)
loc /= np.linalg.norm(loc, axis=1, keepdims=True)
lidx = {os.path.splitext(n)[0].replace('SOD_', ''): i for i, n in enumerate(nm['local'])}


def knn_recall(real, fake, k=5):
    dff = np.sqrt(np.maximum(2 - 2 * fake @ fake.T, 0))
    np.fill_diagonal(dff, np.inf)
    rad = np.sort(dff, axis=1)[:, k - 1]
    drf = np.sqrt(np.maximum(2 - 2 * real @ fake.T, 0))
    return float((drf <= rad[None, :] + 1e-6).any(axis=1).mean())


cov = {r['compared_set']: float(r['recall']) for r in csv.DictReader(open(os.path.join(RT, 'AN-04_foreground_coverage.csv')))
       if r['embedder'] == 'dinoL518' and r['k'] == '5'}
for setname, st_ in (('C10', c10), ('B_s42', stems('abc_stems_B_s42.txt'))):
    mine_r = knn_recall(tgt, loc[[lidx[s] for s in sorted(st_)]])
    check('independent k-NN recall %s = %.3f (table %.3f)' % (setname, mine_r, cov[setname]), abs(mine_r - cov[setname]) < 0.002)
b_rng = [cov['B_s%d' % s] for s in SEEDS]
cf_rng = [cov[x] for x in ('C10', 'CSHUF', 'CINV')]
check('coverage ranges cited 0.35–0.43 / 0.62–0.64', '%.2f–%.2f' % (min(b_rng), max(b_rng)) == '0.35–0.43'
      and '%.2f–%.2f' % (min(cf_rng), max(cf_rng)) == '0.62–0.64' and '0.62–0.64' in reb and '0.35–0.43' in reb)
g4 = list(csv.DictReader(open(os.path.join(RT, 'AN-04_gate4_coverage_reproduction.csv'))))
check('Gate 4: 12/12 committed coverage values at 4 dp', len(g4) == 12 and all(r['recall_match_4dp'] == 'True' for r in g4))
eta = {r['quantity']: float(r['value']) for r in csv.DictReader(open(os.path.join(RT, 'AN-04_cluster_structure.csv')))}
e_c = [v for k_, v in eta.items() if 'committed_predictions' in k_][0]
check('eta^2 committed = %.3f cited as 20.5%%' % e_c, '%.1f%%' % (100 * e_c) == '20.5%' and '20.5%' in reb)
sc = json.load(open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-04b_summary.json')))
check('signal correlations reproduce exactly', sc['gate_passed'])

# ------------------------------------------------------------------ 7. character count (independent of the writer)
txt = open(os.path.join(SR, 'FINAL_UPDATED_REBUTTAL_OPENREVIEW.md'), encoding='utf-8').read()
wc = subprocess.run(['wc', '-m', os.path.join(SR, 'FINAL_UPDATED_REBUTTAL_OPENREVIEW.md')], capture_output=True,
                    text=True, env={'LC_ALL': 'C.UTF-8'}).stdout.split()[0]
check('OpenReview text <= 5000 code points (python %d, wc -m %s)' % (len(txt), wc), len(txt) <= 5000 and int(wc) == len(txt))

# ------------------------------------------------------------------ 8. reviewer-facing text has no private paths
part_a = reb.split('## Part B')[0]
bad = [p for p in ('/home/', 'rebuild/', 'Snapshot', 'RESULT_TABLES', '.py', '.csv', 'TH-0', 'AN-0', 'EXP-0', 'DOC-0')
       if p in part_a.split('---', 1)[1] or p in txt]
check('no private paths / task codes in reviewer-facing text', not bad, bad)
allmd = {os.path.basename(m): open(m, encoding='utf-8').read() for m in glob.glob(os.path.join(SR, '*.md'))}
ph = {k: re.findall(r'\{\{[^}]*\}\}', v) for k, v in allmd.items() if '{{' in v}
check('no unfilled placeholders in any STUDENT_RESULTS document', not ph, ph)

# ------------------------------------------------------------------ 9. Markdown relative links
broken = []
for md in glob.glob(os.path.join(REB, '**', '*.md'), recursive=True):
    for target in re.findall(r'\]\(([^)#\s]+)(?:#[^)]*)?\)', open(md, encoding='utf-8').read()):
        if re.match(r'^[a-z]+://', target):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(md), target))):
            broken.append('%s -> %s' % (os.path.relpath(md, REB), target))
check('all relative Markdown links resolve', not broken, broken)

# ------------------------------------------------------------------ 10. manuscript integrity re-run
r = subprocess.run([sys.executable, '-I', '-B', os.path.join(SR, 'scripts/manuscript_check.py'), '--tex',
                    os.path.join(DR, 'AD-PCHGS-250926.tex'), '--bib', os.path.join(DR, 'reference 1.bib'),
                    '--inputs-dir', os.path.join(WT, 'rebuild/FinalPaper/AD-PCH-230926'),
                    '--out', os.path.join(SR, 'EXPERIMENT_LOGS/00_manuscript_check/manuscript_integrity_final.json')],
                   capture_output=True, text=True)
mi = json.load(open(os.path.join(SR, 'EXPERIMENT_LOGS/00_manuscript_check/manuscript_integrity_final.json')))
check('manuscript unchanged (sha) and refs/cites resolve', r.returncode == 0 and
      mi['tex_sha256'] == '84d3bf97ea881b14b13d2a80af4593ba83f9a68416e5f0113adfe877acfc771a')

out = dict(n_checks=len(results), n_failed=sum(not x['passed'] for x in results), checks=results)
json.dump(out, open(os.path.join(SR, 'EXPERIMENT_LOGS/AUDIT_independent.json'), 'w'), indent=1, ensure_ascii=False)
for x in results:
    print('%s  %s  %s' % ('PASS' if x['passed'] else 'FAIL', x['check'], '' if x['passed'] else x['detail']))
print('\n%d checks, %d failed' % (out['n_checks'], out['n_failed']))
sys.exit(0 if out['n_failed'] == 0 else 1)

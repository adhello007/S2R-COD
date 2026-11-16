"""Phase 6 audit: recompute, from the raw per-run files, every number the final rebuttal quotes, with code
written separately from the analysis scripts (none of their functions is imported, apart from the scorer
wrapper used for the spot re-score of saved prediction maps).

Each check prints the recomputed value, the value as quoted (rounded as in the rebuttal), and PASS or FAIL.
It also checks that every quoted string actually appears in FINAL_UPDATED_REBUTTAL.md, and that the rebuttal
carries no internal details (paths, hashes, hardware, agent).

Usage: nice -n 19 taskset -c 40-47 .venv/bin/python analysis/audit_recompute.py [--no-rescore] [--final]
(--final: unresolved [EQ]/[AUTHOR] markers count as failures; use it after the EQ insertion.)
Writes EXPERIMENT_LOGS/audit_recompute.log; exit code 1 on any FAIL.
"""
import csv
import itertools
import json
import math
import os
import re
import sys

import numpy as np
from scipy import stats

import _repo as R

TAB = R.TABLES
REB = open(os.path.join(R.STUDENT, 'FINAL_UPDATED_REBUTTAL.md')).read()
out, fails = [], []


def log(s=''):
    out.append(s)
    print(s)


def check(name, value, quoted, fmt, in_rebuttal=True):
    """value is recomputed; quoted is the string used in the rebuttal; fmt renders value like the quote."""
    got = fmt % value if isinstance(value, (int, float, np.floating, np.integer)) else str(value)
    ok = got == quoted
    present = (quoted in REB) if in_rebuttal else None
    status = 'PASS' if ok and present is not False else 'FAIL'
    if status == 'FAIL':
        fails.append(name)
    log('%-4s %-62s recomputed %-12s quoted %-10s%s' % (status, name, got, quoted,
        '' if present is None else ('  (in rebuttal)' if present else '  (NOT FOUND in rebuttal)')))


def rows(path):
    return list(csv.DictReader(open(path)))


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d = a.mean() - b.mean()
    t95 = stats.t.ppf(0.975, df)
    p_tost = max(stats.t.sf((d + 0.005) / se, df), stats.t.cdf((d - 0.005) / se, df))
    return d, (d - t95 * se, d + t95 * se), df, p_tost


def holm_count(ps, alpha=0.05):
    k = 0
    for i, p in enumerate(sorted(ps)):
        if p <= alpha / (len(ps) - i):
            k += 1
        else:
            break
    return k


def main():
    rescore = '--no-rescore' not in sys.argv
    log('# Phase 6 audit: independent recomputation of the numbers quoted in FINAL_UPDATED_REBUTTAL.md')
    log()

    # ---- CW-01: SE campaign, S_alpha
    se = rows(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_metrics.csv'))
    v = {}
    for r in se:
        v.setdefault((r['arch'], r['endpoint'], r['arm']), {})[int(r['seed'])] = float(r['Sm'])
    log('## CW-01 (SE campaign, S_alpha; %d rows)' % len(se))
    c10, b = v[('SINet', 'COD10K', 'C10')], v[('SINet', 'COD10K', 'B')]
    d, ci, df, p = welch(list(c10.values()), list(b.values()))
    check('primary Delta C10-B', d, '+0.0024', '%+.4f')
    check('primary 95% CI low', ci[0], '-0.0020', '%+.4f', in_rebuttal=False)
    check('primary 95% CI high', ci[1], '+0.0067', '%+.4f')
    check('primary TOST p', p, '0.101', '%.3f')
    sig = math.sqrt(np.mean([np.var(list(v[('SINet', 'COD10K', a)].values()), ddof=1) for a in ('B', 'C10', 'CSHUF', 'CINV')]))
    check('sigma-hat pooled (4 arms, df 28)', sig, '0.00343', '%.5f')
    ps = []
    for arch, ep in itertools.product(('SINet', 'SINetv2'), ('COD10K', 'NC4K')):
        for hi, lo in (('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV')):
            ps.append(welch(list(v[(arch, ep, hi)].values()), list(v[(arch, ep, lo)].values()))[3])
    check('phrase present: five of 16 equivalent, none after Holm', 'Five of the 16 contrasts are equivalent at $\\pm0.005$ before correction, and none after a Holm correction', 'Five of the 16 contrasts are equivalent at $\\pm0.005$ before correction, and none after a Holm correction', '%s')
    log('     (recomputed count %d of %d; Holm-equivalent %d)' % (sum(p < 0.05 for p in ps), len(ps), holm_count(ps)))
    if sum(p < 0.05 for p in ps) != 5 or holm_count(ps) != 0:
        fails.append('equivalence counts')
    three = np.mean([c10[s] for s in (42, 43, 45)])
    three_nc = np.mean([v[('SINet', 'NC4K', 'C10')][s] for s in (42, 43, 45)])
    check('3-seed SINet C10 COD10K', three, '0.7185', '%.4f')
    check('3-seed SINet C10 NC4K', three_nc, '0.7690', '%.4f')

    # independent simulation of the rule's sensitivity (normal arms, own SDs, sigma-hat re-estimated, >= 7/8 signs)
    rng = np.random.default_rng(1117)
    sds = {a: np.std(list(v[('SINet', 'COD10K', a)].values()), ddof=1) for a in ('B', 'C10', 'CSHUF', 'CINV')}
    nsim, n = 200000, 8
    def fires(delta):
        x = {a: rng.normal(0, sds[a], (nsim, n)) for a in sds}
        x['C10'] = x['C10'] + delta
        s_hat = np.sqrt(np.mean([x[a].var(axis=1, ddof=1) for a in sds], axis=0))
        dd = x['C10'].mean(1) - x['B'].mean(1)
        pair = x['C10'] - x['B']
        agree = (np.sign(pair) == np.sign(dd)[:, None]).sum(1)
        return np.mean((np.abs(dd) > 2 * s_hat) & (agree >= 7) & (dd > 0))
    p005, p0142 = fires(0.005), fires(0.0142)
    check('P(rule fires | 0.005), full rule, simulated', p005, '0.20', '%.2f')
    check('P(rule fires | 0.0142) > 0.99', 'probability above $0.99$' if p0142 > 0.99 else 'NOT above 0.99', 'probability above $0.99$', '%s')
    log('     (P at 0.0142 = %.4f)' % p0142)
    lo, hi = 0.006, 0.012
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if fires(mid) >= 0.8 else (mid, hi)
    check('80% detectable effect, full rule', (lo + hi) / 2, '0.0087', '%.4f')
    log()

    # ---- CW-02: AN-01 eight-seed boundary, CDR
    log('## CW-02')
    an = rows(os.path.join(TAB, 'AN01_boundary_8seed_per_run.csv'))
    bi = {}
    for r in an:
        if r['arch'] == 'SINet' and r['endpoint'] == 'COD10K' and float(r['thresh']) == 0.5:
            bi.setdefault(r['arm'], {})[int(r['seed'])] = float(r['boundary_iou'])
    sb = math.sqrt(np.mean([np.var(list(bi[a].values()), ddof=1) for a in ('B', 'C10', 'CSHUF', 'CINV')]))
    for arm, q_d, q_x in (('C10', '+0.0046', '0.30'), ('CINV', '+0.0098', '0.64')):
        dd = np.mean(list(bi[arm].values())) - np.mean(list(bi['B'].values()))
        check('AN-01 SINet COD10K BIoU@0.5 %s-B Delta' % arm, dd, q_d, '%+.4f')
        check('AN-01 %s-B x bar' % arm, abs(dd) / (2 * sb), q_x, '%.2f')
    cd = [r for r in rows(os.path.join(TAB, 'EXP02_SINet_per_run.csv')) if r['endpoint'] == 'COD10K' and float(r['thresh']) == 0.5]
    alloc = {}
    for r in cd:
        key = ('B', 'B') if r['level'] == 'B' else (r['level'], r['allocation'])   # B: one set per seed
        alloc.setdefault(key, []).append(float(r['boundary_iou']))
    mean_b = np.mean(alloc[('B', 'B')])
    mean_lu = np.mean(alloc[('LU', 'CDRLU')])
    D = 0.5 * (mean_b + mean_lu)
    within = [k for k in alloc if k[0] in ('LU', 'L1', 'LH')]
    ss = sum(((np.asarray(alloc[k]) - np.mean(alloc[k])) ** 2).sum() for k in within)
    dfw = sum(len(alloc[k]) - 1 for k in within)
    sig_c = math.sqrt(ss / dfw)
    check('CDR dispersed reference D', D, '0.331', '%.3f')
    check('CDR sigma-hat df', dfw, '24', '%d', in_rebuttal=False)
    check('CDR bar 2 sigma-hat', 2 * sig_c, '0.0193', '%.4f')
    for lev, q_d, q_x, q_k in (('L1', '-0.0005', '0.03', '2/5'), ('LH', '+0.0021', '0.11', '4/5')):
        means = [np.mean(alloc[k]) for k in alloc if k[0] == lev]
        dl = np.mean(means) - D
        check('CDR %s Delta' % lev, dl, q_d, '%+.4f')
        check('CDR %s x bar' % lev, abs(dl) / (2 * sig_c), q_x, '%.2f')
        check('CDR %s permutations agreeing' % lev, '%d/5' % sum(np.sign(m - D) == np.sign(dl) for m in means), q_k, '%s')
    conc = [np.mean(alloc[k]) for k in alloc if k[0] in ('L1', 'LH')]
    disp = [mean_lu] + list(alloc[('B', 'B')])
    dd, ci, _, _ = welch(conc, disp)
    check('CDR units Welch Delta (10 vs 9)', dd, '+0.0024', '%+.4f')
    check('CDR units Welch CI low', ci[0], '-0.0024', '%+.4f')
    check('CDR units Welch CI high', ci[1], '+0.0072', '%+.4f')
    al = rows(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'cdr', 'cdr_allocations.csv'))
    for lev, q in (('LU', '50'), ('L1', '45'), ('LH', '41')):
        check('induced N_eff %s' % lev, np.mean([float(a['n_eff_induced']) for a in al if a['level'] == lev]), q, '%.0f')
    for lev, q in (('LU', '75'), ('L1', '30'), ('LH', '15')):
        check('nominal N_eff %s' % lev, np.mean([float(a['n_eff_nominal']) for a in al if a['level'] == lev]), q, '%.0f')
    shared = [round(float(a['jaccard_c10']) * 2000 / (1 + float(a['jaccard_c10']))) for a in al if a['level'] in ('L1', 'LH')]
    check('images shared with C10, min-max', '%d–%d' % (min(shared), max(shared)), '440–518', '%s')
    th2 = {r['allocation']: r for r in rows(os.path.join(TAB, 'TH02_concentration_indices.csv'))}
    check('induced N_eff random B (mean 8 seeds)', float(th2['B (mean over 8 seeds)']['n_eff']), '43', '%.0f')
    runs = rows(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_runs.csv'))
    by = {}
    for r in runs:
        by.setdefault(r['arm'], []).append(int(r['n_appended']))
    m = {a: np.mean(x) for a, x in by.items()}
    check('pseudo-label arm means, min-max', '%.0f–%.0f' % (min(m.values()), max(m.values())), '1991–2020', '%s')
    allv = [x for xs in by.values() for x in xs]
    check('pseudo-label runs, min-max (%d runs)' % len(allv), '%d–%d' % (min(allv), max(allv)), '1782–2278', '%s')
    log()

    # ---- CW-03
    log('## CW-03')
    mets = rows(os.path.join(TAB, 'EXP03_run_scores.csv'))
    sup = {}
    for r in mets:
        if r['campaign'] == 'e3c':
            sup.setdefault((r['arch'], r['endpoint']), []).append(float(r['Sm']))
    ext = {(r['source'], r['endpoint']): float(r['Sm']) for r in rows(os.path.join(TAB, 'EXP03_external_scores.csv'))}
    sv2 = [k for k in ext if k[0].startswith('E3-a')][0][0]
    rise = [k for k in ext if 'RISE' in k[0]][0][0]
    c10v2 = np.mean(list(v[('SINetv2', 'COD10K', 'C10')].values()))
    for (arch, ep), q in ((('SINet', 'COD10K'), '0.717'), (('SINet', 'NC4K'), '0.768'),
                          (('SINetv2', 'COD10K'), '0.695'), (('SINetv2', 'NC4K'), '0.749')):
        check('C10 8-seed %s %s' % (arch, ep), np.mean(list(v[(arch, ep, 'C10')].values())), q, '%.3f')
    for key, q in ((('SINet', 'COD10K'), '0.805'), (('SINet', 'NC4K'), '0.840'), (('SINetv2', 'COD10K'), '0.807'), (('SINetv2', 'NC4K'), '0.839')):
        check('supervised anchor %s %s (n=%d)' % (key + (len(sup[key]),)), np.mean(sup[key]), q, '%.3f')
    check('released SINet-V2 COD10K', ext[(sv2, 'COD10K')], '0.815', '%.3f')
    check('released SINet-V2 NC4K', ext[(sv2, 'NC4K')], '0.847', '%.3f')
    check('RISE COD10K', ext[(rise, 'COD10K')], '0.763', '%.3f')
    check('RISE NC4K', ext[(rise, 'NC4K')], '0.805', '%.3f')
    check('gap: supervised SINet-V2 - C10 SINet-V2, COD10K', ext[(sv2, 'COD10K')] - c10v2, '0.120', '%.3f')
    check('gap: real labels, our recipe (SINet-V2, COD10K)', np.mean(sup[('SINetv2', 'COD10K')]) - c10v2, '0.112', '%.3f')
    check('gap: official recipe on top', ext[(sv2, 'COD10K')] - np.mean(sup[('SINetv2', 'COD10K')]), '0.008', '%.3f')
    check('gap: RISE - C10 SINet-V2, COD10K', ext[(rise, 'COD10K')] - c10v2, '+0.068', '%+.3f')
    check('gap: RISE - C10 SINet-V2, NC4K', ext[(rise, 'NC4K')] - np.mean(list(v[('SINetv2', 'NC4K', 'C10')].values())), '+0.056', '%+.3f')
    pub = json.load(open(os.path.join(TAB, 'AN02_published_baselines.json')))
    log('     (published-vs-re-scored agreement is checked in AN02_published_baselines.json: %s)' %
        ('present' if pub else 'missing'))
    log()

    # ---- CW-04
    log('## CW-04')
    a3 = json.load(open(os.path.join(TAB, 'AN03_summary.json')))
    vv = a3['variance']['two_renders']
    check('R2 between foregrounds (two renders)', vv['r2'], '0.86', '%.2f')
    check('R2 random pairing', vv['perm_r2_mean'], '0.50', '%.2f')
    check('ICC', vv['icc'], '0.71', '%.2f')
    check('cosine to own base render', a3['variance']['cos_render_own_base'][0], '0.73', '%.2f')
    check('cosine to random base render', a3['variance']['cos_render_random_base'][0], '0.06', '%.2f')
    check('clusters with nearest cut-out beyond median member', a3['clusters_nearest_cutout_farther_than_median_member'], '52 of the 75', '%d of the 75')
    log()

    # ---- spot re-score of saved prediction maps (CDR primary)
    if rescore:
        log('## Spot re-score of saved CDR maps (Boundary-IoU at 0.5, COD10K) against EXP02_SINet_per_run.csv')
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import boundary_scorer as BS
        picks = ['SINet_CDRLHP3_s43', 'SINet_CDRL1P2_s45']
        res = BS.score_runs([(k, os.path.join(R.REPO, 'Result', 'ABC', k, 'COD10K'), 'COD10K') for k in picks],
                            thresholds=(0.5,), workers=8)
        agg = res[0] if isinstance(res, tuple) else res
        for k in picks:
            new = agg[(k, 0.5)]['boundary_iou']
            old = [float(r['boundary_iou']) for r in cd if '%s_%s_s%s' % (r['arch'], r['allocation'], r['seed']) == k][0]
            ok = abs(new - old) < 5e-7
            if not ok:
                fails.append('rescore ' + k)
            log('%-4s %-40s re-scored %.6f  table %.6f' % ('PASS' if ok else 'FAIL', k, new, old))
        log()

    # ---- the rebuttal carries no internal details
    log('## Internal details in the rebuttal (must be none)')
    body = re.sub(r'<!--.*?-->', '', REB, flags=re.S)
    markers = re.findall(r'\*\*\[(?:EQ|AUTHOR)[^\]]*\]\*\*', body)
    body = re.sub(r'\*\*\[(?:EQ|AUTHOR)[^\]]*\]\*\*', '', body)   # placeholders are counted below, not scanned
    final = '--final' in sys.argv
    if markers and final:
        fails.append('unresolved markers')
    log('%-4s %-26s %d (%s)' % ('FAIL' if markers and final else ('PEND' if markers else 'PASS'), 'unresolved [EQ]/[AUTHOR]',
        len(markers), 'must be 0 with --final' if markers else 'none'))
    pats = {'file path or extension': r'\b[\w-]*[A-Za-z][\w-]*/[\w./-]*[A-Za-z]|\.(csv|json|py|md|tex|sh)\b', 'commit hash': r'\b[0-9a-f]{7,40}\b',
            'hardware': r'\b(GPU|RTX|Blackwell|CUDA)\b', 'agent or tool': r'\b(Claude|agent|LLM|cron|watchdog)\b',
            'internal task code': r'\b(TH-0\d|AN-0\d|EXP-0\d|DOC-0\d|E3-[a-f]|CDR|EQ\b)'}
    for name, pat in pats.items():
        hits = sorted({m.group(0) for m in re.finditer(pat, body)})
        if hits:
            fails.append('internal: ' + name)
        log('%-4s %-26s %s' % ('FAIL' if hits else 'PASS', name, ', '.join(hits[:8]) if hits else 'none'))
    log()
    log('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d): %s' % (len(fails), '; '.join(fails))))
    open(os.path.join(R.STUDENT, 'EXPERIMENT_LOGS', 'audit_recompute.log'), 'w').write('\n'.join(out) + '\n')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()

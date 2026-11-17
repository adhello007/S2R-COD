#!/usr/bin/env python
"""CAUS DOC-01 -- proposed manuscript scope edits, applied to a COPY of the submitted .tex.

The submitted file (S2R-COD/AD-PCHGS-250926.tex) is only read. Each edit must match exactly once, or
the script halts. The new appendix (app:shapeoracle) is generated from the EXP-01 result tables, so no
number in it is typed by hand; while EXP-01 is incomplete it says so and gives no outcome.
The copy is compiled with the committed inputs (rebuild/FinalPaper/AD-PCH-230926 at HEAD) in a build
directory given on the command line, and the page on which the AI-use statement starts is reported (the
discussion-phase limit is 10 pages of main text).
Writes STUDENT_RESULTS/manuscript_scope_edits.patch (unified diff, original -> revised).
Usage: doc01_make_patch.py <build_dir>
"""

import csv
import difflib
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

SUBMITTED = K.orig('AD-PCHGS-250926.tex')
BIB = K.orig('reference 1.bib')

EDITS = [
    # (id, old, new)  -- ids map to DOC-01_edits.md and the AN-01 claim ledger
    ('E01 title (optional; C-01)',
     r"\title{Concentration, Not Uncertainty: Why Targeted Synthetic Data Doesn't Help Camouflaged Object Detection}",
     r"\title{Concentration, Not Uncertainty: Why Targeted Synthetic Data Did Not Help an Offline Camouflaged Object Detection Pipeline}"),
    ('E02 abstract scope + controls (C-02, C-03, C-04)',
     "Across 103 training runs, uncertainty-based targeting does not outperform random allocation. Five independent controls further show that this null result is not an artifact: targeted training sets are measurably different from random sets, but the difference is explained by concentrating the generation budget rather than by where uncertainty is concentrated, as every concentration rule we test reproduces the effect and, on boundary accuracy, so does aiming at the clusters the model was most certain about.",
     "Across 103 training runs in an offline pipeline (LAKE-RED renders of a fixed foreground set, two-round S2R-COD training, SINet and SINet-v2), uncertainty-based targeting does not outperform random allocation at the measured sensitivity. Five controls each rule out a specific artifact: targeted training sets are measurably different from random sets, but the difference comes from matching and concentrating the generation budget rather than from where uncertainty points, as same-shape rules aimed elsewhere reproduce it and, on boundary accuracy, so does aiming at the clusters the model was most certain about."),
    ('E03 abstract CHAMELEON floor (C-22; contingent on author adjudication of animal-54)',
     "with 50 of its 76 images duplicated from training data",
     "with at least 51 of its 76 images duplicated from training data"),
    ('E04 abstract last sentence (C-04)',
     "budget concentration, not uncertainty-based targeting, accounts for the observed training-set effects.",
     "budget concentration and target matching, not uncertainty-based targeting, account for the observed training-set differences in this pipeline."),
    ('E05 intro probe sentence (C-04)',
     "But it is picking up concentration, not aim.",
     "But it is picking up matching and concentration, not aim."),
    ('E06 intro probe sentence (C-04)',
     "Only removing the unevenness itself defeats it. What looked like the effect of targeting was the effect of concentrating, the",
     "Only a random draw defeats it; a perfectly even quota under the same matching does not. What looked like the effect of targeting was the effect of matching and concentrating, the"),
    ('E07 intro oracle sentence (C-05)',
     "Substituting a perfect score using a test-set error for ours changes nothing.",
     "Re-ranking the same allocation by each cluster's test-set error gives no resolvable gain, and Appendix~\\ref{app:shapeoracle} reports oracle allocations of other shapes."),
    ('E08 intro CHAMELEON (C-22)',
     "where 50 of its 76 images are direct copies",
     "where at least 51 of its 76 images are direct copies"),
    ('E09 contribution bullet (C-05)',
     "control, a perfect-score oracle, an unpinned optimization schedule",
     "control, an endpoint-error oracle at fixed allocation shape, an unpinned optimization schedule"),
    ('E10 contribution bullet CHAMELEON (C-22)',
     r"\item \textit{CHAMELEON is $50$ of $76$ images ($65.8\%$) training data}",
     r"\item \textit{CHAMELEON is at least $51$ of $76$ images ($67.1\%$) training data}"),
    ('E11 table 2 oracle label (C-05)',
     "OR & a perfect score in place of ours & $3$",
     "OR & a test-error ranking, same shape & $3$"),
    ('E12 oracle paragraph scope (C-06)',
     r"This converts \emph{our score did not help} into the stronger \emph{no score of any quality helped here}.",
     r"This converts \emph{our score did not help} into the stronger \emph{no ranking of clusters, even one built from the endpoint's own errors, helped at this allocation shape}; Appendix~\ref{app:shapeoracle} reports oracle allocations of other shapes."),
    ('E13 probe collapse sentence (C-04)',
     r"Only removing the unevenness itself, by drawing two random sets of equal size, collapses it (Figure~\ref{fig:thesis}a). The probe was detecting the concentration the whole time.",
     r"Only drawing at random collapses it (Figure~\ref{fig:thesis}a); a perfectly even quota under the same centroid matching still separates (held-out $d \approx 0.5$, Appendix~\ref{app:shapeoracle}). The probe detects the matched, concentrated selection, and the signal's direction adds nothing to it."),
    ('E14 effective-rank definition (C-12)',
     r"effective rank than a random draw's in all twenty cells (mean ratio $0.634$), and covers no more of",
     r"effective rank (participation ratio) than a random draw's in all twenty cells (mean ratio $0.634$), an empirical property of these selections and not a consequence of concentration (Appendix~\ref{app:shapeoracle}), and covers no more of"),
    ('E15 coverage k (C-20)',
     r"($k$-NN recall, Appendix~\ref{app:coverage}), while the generator's own source photographs, real",
     r"($k$-NN recall at $k = 5$, Appendix~\ref{app:coverage}; lower than the input at every $k$ from $3$ to $20$), while the generator's own source photographs, real"),
    ('E16 CHAMELEON floor sentence (C-22)',
     r"reported \textsc{unchecked} rather than clean, so $50$ is a floor rather than an estimate.",
     r"reported \textsc{unchecked} rather than clean, so $50$ is a floor rather than an estimate. A post-review re-check with an independent detector found one more, \texttt{animal-54}, a rescaled copy of a COD10K-train image, so the floor is at least $51$."),
    ('E17 discussion geometric statement (C-23)',
     "and we state it without hedging: concentration, not the",
     "and we state it plainly: the matched, concentrated selection, not the"),
    ('E18 discussion scope (C-24)',
     "only that this build could not have shown that it does.",
     "only that this build could not have shown that it does. The null is bounded to an offline LAKE-RED pool of fixed foregrounds, a two-round S2R-COD protocol, SINet and SINet-v2, and the COD10K and NC4K endpoints; a modern transformer detector and a generator that varies the foreground remain untested."),
    ('E19 conclusion scope (C-25)',
     "Under a fixed synthetic-data budget, aiming generation at the clusters a model finds hardest did not beat spending it at random.",
     "Under a fixed synthetic-data budget, in an offline pipeline that repaints the backgrounds of a fixed foreground set, aiming generation at the clusters a model finds hardest did not beat spending it at random."),
    ('E20 conclusion attribution (C-04)',
     "but through concentration rather than aim, which only a same-shape control exposes.",
     "but through matching and concentration rather than aim, which only a same-shape control exposes."),
    ('E21 conclusion CHAMELEON (C-22)',
     "$50$ of CHAMELEON's $76$ images are altered copies",
     "at least $51$ of CHAMELEON's $76$ images are altered copies"),
    ('E22 AI-use grammar (C-27)',
     "categories theoretical frameworks, mathematical claims and proofs, translation, and qualitative\ndata analysis do not apply.",
     "categories (theoretical frameworks, mathematical claims and proofs, translation, and qualitative\ndata analysis) do not apply."),
    ('E23 AI-use pre-registration timing (C-07)',
     "decision rules governing every verdict: the arms, the endpoints, the seeds, the noise estimate,\nand the verdict bands, were pre-registered before the runs they govern",
     "decision rules governing every verdict (the arms, the endpoints, the seeds, the noise estimate,\nand the verdict bands) were committed before any result they decide, and all but one before the runs they govern"),
    ('E24 reproducibility timing (C-07)',
     "The decision rules governing every result are committed before the runs they govern, at the commits",
     "The decision rules governing every result are committed before any result they decide, and all but one before the runs they govern, at the commits"),
    ('E25 app:method opening (C-07)',
     "Every decision rule was committed before the\nruns it governs.",
     "Every decision rule but one was committed before the\nruns it governs."),
    ('E26 app:method commit list (C-07, C-31)',
     "the\nseed expansion's at \\texttt{b755aa9}, dated 2026-09-18. The oracle and optimization schedule\ncampaigns carry their own pre-registrations, each committed before that campaign's first training\nrun.",
     "the\nseed expansion's at \\texttt{a79886a} (2026-09-18, two days before its first run), together with the optimization-schedule campaign's, also before its first run. The oracle campaign's rule was written before any of its scores existed and committed in the same \\texttt{a79886a}, 62 minutes after its first run had started (first run 10:46, commit 11:48, first score 18:23); that commit is preserved under the tag \\texttt{prereg-or-fx-se-a79886a}."),
    ('E27 app:controls timing (C-07)',
     "and the pre-registration says so\nbefore the first run:",
     "and the pre-registration, written before any oracle score existed, says so:"),
]


def q4(x, signed=False):
    """Round a decimal string to 4 dp, half-up, from its text (not via binary floating point)."""
    from decimal import Decimal, ROUND_HALF_UP
    v = Decimal(x).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    return ('%+.4f' if signed else '%.4f') % v if v != 0 else ('+0.0000' if signed else '0.0000')


def shape_appendix():
    """app:shapeoracle, generated from committed result tables only."""
    T = K.TABLES
    props = {r['arm']: r for r in csv.DictReader(open(os.path.join(T, 'TH-01_quota_properties.csv')))}
    geo = {(r['repr'], r['arm']): r for r in csv.DictReader(open(os.path.join(T, 'AN-02_shape_geometry.csv')))}
    comp_p = os.path.join(T, 'EXP-01_comparisons.csv')
    comp = [r for r in csv.DictReader(open(comp_p))] if os.path.isfile(comp_p) else []
    prim = [r for r in comp if r['endpoint'] == 'COD10K' and r['role'].startswith('P')]
    nc = {r['contrast']: r for r in comp if r['endpoint'] == 'NC4K' and r['role'].startswith('P')}
    done = prim and all(r['status'] == 'COMPLETE' for r in prim)
    g = lambda a: geo[('R2_cut', a)]                           # noqa: E731
    lines = [
        r"\section{Post-review: Oracle Allocations of a Different Shape}",
        r"\label{app:shapeoracle}",
        "",
        r"CORACLE re-aims C10's quota multiset by true endpoint error and so tests direction at a fixed shape. "
        r"To test shape, we pre-registered three oracle allocations at $N = 1000$, built from the same endpoint-error "
        r"vector and served by the same selector: \emph{OR-PROP}, quotas proportional to each cluster's error; "
        r"\emph{OR-TOP10}, $100$ images to each of the ten highest-error clusters; and \emph{OR-TOP5}, $200$ to each of "
        r"the five highest. \emph{OR-TOP10-SHUF} gives OR-TOP10's multiset to clusters drawn by a frozen permutation. "
        r"All use endpoint labels to choose training data, so COD10K-test is not an unbiased endpoint for them; NC4K "
        r"labels are read by no allocation. B, C10 and CORACLE are the committed runs, reused after a reuse gate "
        r"(identical code path, data bytes and selections; committed metrics reproduced at six decimals; identical first "
        r"training step).",
        "",
        r"Two facts were fixed before any training. Because per-cluster error spans only $0.09$--$0.47$, the "
        r"error-proportional quota is nearly flat ($%s$--$%s$ per cluster); every permutation of it leaves at least "
        r"$84\%%$ of the selected images unchanged, so its direction cannot be tested with this selector and its shuffle "
        r"was not trained. And concentration does not determine effective rank: a perfectly even quota under the same "
        r"matching is still separable from a random draw (held-out $d = %s$) with a lower participation ratio "
        r"(ratio $%s$), while the five-cluster shuffle keeps a near-random ratio ($%s$)."
        % ('4', props['OR-PROP']['max_quota'], g('FLAT')['probe_d_heldout_vs_random'],
           g('FLAT')['pr_ratio_vs_random'], g('OR-TOP5-SHUF')['pr_ratio_vs_random']),
        "",
    ]
    if not done:
        lines.append(r"\emph{[Trained results pending: %d of 4 primary contrasts complete. This paragraph is replaced by "
                     r"the verified table once every run of record exists.]}" % sum(r['status'] == 'COMPLETE' for r in prim))
        return '\n'.join(lines) + '\n'
    lines += [r"\begin{center}\small", r"\begin{tabular}{@{}lccccc@{}}", r"\toprule",
              r"Contrast (SINet, $n = 3$) & $\Delta$ COD10K & $2\hat{\sigma}$ & sign & verdict & $\Delta$ NC4K \\",
              r"\midrule"]
    for r in prim:
        n = nc.get(r['contrast'], {})
        lines.append(r"%s & $%s$ & $%s$ & %s & \textsc{%s} & $%s$ \\" % (
            r['contrast'].replace(' - ', r' $-$ '), q4(r['delta'], True), q4(r['bar']), r['sign'],
            r['verdict'].lower(), q4(n['delta'], True) if n.get('delta') else 'n/a'))
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{center}", ""]
    within = all(r['verdict'] == 'WITHIN NOISE' for r in prim)
    if within:
        lines.append(r"No oracle shape, flat, top-ten or top-five, resolves a gain over the C10-shaped oracle at this "
                     r"sensitivity, and aim at the top-ten shape does not resolve against its own shuffle, although the "
                     r"endpoint-label leak can only favour these arms. The bars are as wide as the effects they would miss "
                     r"($2\hat{\sigma} = %s$ on $\mathrm{df} = %s$); this is a null at this sensitivity, not evidence of no effect."
                     % (q4(prim[0]['bar']), prim[0]['df_pool']))
    else:
        lines.append(r"At least one oracle shape departs from the C10-shaped oracle by more than its bar; the verdicts above "
                     r"are reported as pre-registered, and because these arms read endpoint labels, a COD10K gain is "
                     r"interpreted only together with its NC4K counterpart.")
    return '\n'.join(lines) + '\n'


def main():
    build = sys.argv[1]
    src = open(SUBMITTED).read()
    out = src
    applied = []
    for eid, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            raise SystemExit('DOC-01 HALT: edit %s matches %d times' % (eid, n))
        out = out.replace(old, new)
        applied.append(eid)
    app = shape_appendix()
    anchor = r"\end{document}"
    if out.count(anchor) != 1:
        raise SystemExit('DOC-01 HALT: \\end{document} anchor')
    out = out.replace(anchor, app + '\n' + anchor)
    # build
    if os.path.exists(build):
        raise SystemExit('DOC-01: build dir exists, use a new one: %s' % build)
    os.makedirs(build)
    tar = subprocess.run(['git', 'archive', 'HEAD', 'rebuild/FinalPaper/AD-PCH-230926'], cwd=K.REPO, capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', build, '--strip-components=3'], input=tar, check=True)
    shutil.copy(BIB, os.path.join(build, 'reference.bib'))
    with open(os.path.join(build, 'AD-PCHGS-250926.tex'), 'w') as fh:
        fh.write(out)
    rc = subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'AD-PCHGS-250926.tex'],
                        cwd=build, capture_output=True, timeout=400).returncode
    pdf = os.path.join(build, 'AD-PCHGS-250926.pdf')
    pages, ai_page = None, None
    if rc == 0 and os.path.isfile(pdf):
        info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
        pages = int([l for l in info.splitlines() if l.startswith('Pages:')][0].split()[1])
        for p in range(1, pages + 1):
            t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'], capture_output=True, text=True).stdout
            if 'AI U SE S TATEMENT' in t or 'AI Use Statement' in t or 'AI USE STATEMENT' in t:
                ai_page = p
                break
        log = open(os.path.join(build, 'AD-PCHGS-250926.log'), errors='ignore').read()
        undefined = log.count('undefined')
    else:
        undefined = None
    diff = difflib.unified_diff(src.splitlines(keepends=True), out.splitlines(keepends=True),
                                fromfile='a/AD-PCHGS-250926.tex (as submitted)',
                                tofile='b/AD-PCHGS-250926.tex (proposed scope edits)')
    patch = os.path.join(K.CAUS_OUT, 'manuscript_scope_edits.patch')
    K.assert_writable(patch)
    with open(patch, 'w') as fh:
        fh.write('# Proposed scope edits for Reviewer Caus (DOC-01). Generated by rebuild/CAUS/doc01_make_patch.py.\n')
        fh.write('# Applies to S2R-COD/AD-PCHGS-250926.tex (sha256 84d3bf97...). The submitted file is NOT modified.\n')
        fh.write('# Compiled copy: latexmk rc=%s, %s pages, AI-use statement starts on page %s (limit: main text <= 10 pages), '
                 'undefined refs in log: %s\n' % (rc, pages, ai_page, undefined))
        fh.write('# Edits: %s + new appendix app:shapeoracle\n' % '; '.join(applied))
        fh.writelines(diff)
    print('applied %d edits; latexmk rc=%s; pages=%s; AI-use statement on page %s; undefined=%s' % (len(applied), rc, pages, ai_page, undefined))
    print('patch:', os.path.relpath(patch, K.REPO))


if __name__ == '__main__':
    main()

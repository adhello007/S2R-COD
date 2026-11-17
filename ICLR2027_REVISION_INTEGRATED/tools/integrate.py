#!/usr/bin/env python3
"""Build paper/REVISED_PAPER.tex from the RL5B revision plus the Caus and dypE edits.

Re-runnable: every run starts from the pristine RL5B package copy, applies exact replacements
(each must match exactly once, or the script stops), and writes the result into paper/.
Colour macros: \\revA (RL5B, blue), \\revB (Caus, teal), \\revC (dypE, purple),
\\revShared (two or more reviewers, orange). See ../05_COLOR_CHANGE_LOG.md.
"""
import pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]            # repo root (S2R-COD-merged)
SRC = ROOT / "rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/revision"
OUT = ROOT / "ICLR2027_REVISION_INTEGRATED/paper"

# ---------------------------------------------------------------- copy the pristine base
OUT.mkdir(parents=True, exist_ok=True)
for p in SRC.iterdir():
    if p.name in ("AD-PCHGS-original-copy.tex", "manuscript.diff", "AD-PCHGS-revised.tex", "eq_result.tex"):
        continue
    if p.is_dir():
        shutil.copytree(p, OUT / p.name, dirs_exist_ok=True)
    else:
        shutil.copy2(p, OUT / p.name)
tex = (SRC / "AD-PCHGS-revised.tex").read_text()
LOG = []


def R(old, new, tag):
    """Replace exactly one occurrence of old with new; tag names the change for the log."""
    global tex
    n = tex.count(old)
    if n != 1:
        sys.exit(f"[{tag}] expected exactly 1 match, found {n}:\n{old[:200]}")
    tex = tex.replace(old, new)
    LOG.append(tag)


def edit_file(name, pairs, tag):
    p = OUT / name
    s = p.read_text()
    for old, new in pairs:
        if s.count(old) != 1:
            sys.exit(f"[{tag}] {name}: expected 1 match, found {s.count(old)}:\n{old[:200]}")
        s = s.replace(old, new)
    p.write_text(s)
    LOG.append(tag)


# ================================================================ preamble: colours, one switch
R(r"""\usepackage{graphicx}
""", r"""\usepackage{graphicx}
\usepackage{xcolor}

% ---------------------------------------------------------------------
% Revision colours (post-discussion revision). One switch: REVISED_CLEAN.tex
% defines \revclean before \input-ing this file, which prints everything in black.
% RL5B = blue, Caus = teal, dypE = purple, two or more reviewers = orange.
% ---------------------------------------------------------------------
\newif\ifrevmarked \revmarkedtrue
\ifdefined\revclean \revmarkedfalse \fi
\definecolor{RevA}{RGB}{0,72,190}       % RL5B only: blue
\definecolor{RevB}{RGB}{0,115,115}      % Caus only: teal
\definecolor{RevC}{RGB}{105,45,160}     % dypE only: purple
\definecolor{RevShared}{RGB}{190,85,0}  % two or more reviewers: orange
\DeclareRobustCommand{\revA}[1]{\ifrevmarked{\color{RevA}#1}\else{#1}\fi}
\DeclareRobustCommand{\revB}[1]{\ifrevmarked{\color{RevB}#1}\else{#1}\fi}
\DeclareRobustCommand{\revC}[1]{\ifrevmarked{\color{RevC}#1}\else{#1}\fi}
\DeclareRobustCommand{\revShared}[1]{\ifrevmarked{\color{RevShared}#1}\else{#1}\fi}
% for multi-paragraph spans and \input files
\newenvironment{revblock}[1]{\ifrevmarked\color{#1}\fi}{}
% for whole floats: place right after \begin{table}
\newcommand{\revfloatcolor}[1]{\ifrevmarked\color{#1}\fi}
""", "preamble-colour-macros")

R(r"""% Rebuttal revision: outcome-dependent text is held in these two macros and filled from the pre-registered
% decision sentences once the result exists (dose-response: after its 35 SINet runs; confirmatory equivalence
% campaign: after its 81 runs). A compiled PDF that still shows "[pending]" is not final.
\newcommand{\cdrverdict}{\textbf{[dose-response result pending]}}
\newcommand{\eqverdict}{\textbf{[confirmatory equivalence result pending]}}
\newcommand{\cdrshort}{\textbf{[one-sentence dose-response result pending]}}
\newcommand{\eqshort}{\textbf{[one-sentence equivalence result pending]}}
\input{cdr_result.tex}  % dose-response result, filled 2026-11-16 from the pre-registered sentence
\input{eq_result.tex}   % confirmatory equivalence result, filled 2026-11-17 from the pre-registered sentence (INCOMPLETE rule)
""", r"""% The dose-response verdict is the pre-registered decision sentence, generated from the committed result
% (cdr_result.tex). The confirmatory-equivalence numbers are written out in Section 3.1 and Table 3 with all
% three arms' seed counts (16/15/15), so the generated EQ sentence is no longer used.
\newcommand{\cdrverdict}{\textbf{[dose-response result pending]}}
\newcommand{\cdrshort}{\textbf{[one-sentence dose-response result pending]}}
\input{cdr_result.tex}  % dose-response result, filled 2026-11-16 from the pre-registered sentence
""", "preamble-drop-eq-macros")

# ================================================================ abstract (central claim, constraint 1 + Q1)
R(r"""retrains the model. Across 103 training runs, uncertainty-based targeting shows no detectable advantage over random allocation. At eight seeds the primary gap is $+0.0024$ $S_\alpha$, with a 95\% interval of $-0.0020$ to $+0.0067$: an advantage as large as the published method's own gain ($+0.0142$) is excluded, but smaller ones are not. \eqshort{} Five controls address the main ways the design itself could produce such a null. Targeted training sets are nonetheless measurably different from random ones, and that difference comes from concentrating the budget rather than from where it is aimed: every concentrating rule we test reproduces it. \cdrshort{} Separately, we find substantial data contamination in CHAMELEON, with 50 of its 76 images duplicated from training data despite the standard overlap check reporting zero overlap. These conclusions are bounded to the setting tested: allocation over a fixed, offline pool of LAKE-RED renders that re-use 4,447 foregrounds with new backgrounds, $k = 75$ clusters of frozen self-supervised features, two SINet architectures with two-round self-training, and a budget of 1,000 images.""",
  r"""retrains the model. \revShared{Within the pipeline we test, uncertainty-guided allocation shows no detectable benefit over random allocation across 103 training runs, and a pre-registered confirmatory campaign establishes equivalence within $\pm0.005$ $S_\alpha$ on the primary comparison (90\% interval $-0.0027$ to $+0.0039$). Same-shape controls show that the direction of the uncertainty signal adds nothing detectable.} Targeted training sets are nonetheless measurably different from random ones, \revB{and how the selector matches images to clusters and how unevenly it spreads the budget explain that difference, not where the budget is aimed}; \revShared{a pre-registered dose-response test found no effect of concentration on accuracy.} Separately, we find substantial data contamination in CHAMELEON, with \revC{at least} 50 of its 76 images duplicated from training data despite the standard overlap check reporting zero overlap. \revShared{These conclusions are bounded to the setting tested: allocation over a fixed, offline pool of LAKE-RED renders that re-use 4,447 foregrounds with new backgrounds, the S2R-COD two-round protocol, $k = 75$ clusters of frozen self-supervised features, SINet and SINet-v2, and a budget of 1,000 images.}""",
  "abstract")
R(r"""We study an uncertainty-guided allocation strategy that clusters the unlabelled real images, identifies clusters on which the model is least certain, allocates a fixed pool of synthetic images toward those clusters, and""",
  r"""We study an uncertainty-guided \revShared{allocation} strategy that clusters the unlabelled real images, identifies clusters on which the model is least certain, allocates \revShared{a fixed pool of synthetic images} toward those clusters, and""",
  "abstract-allocation-wording")

# ================================================================ introduction
R(r"""learns to tell which set an image came from even images it never saw. But it is picking up concentration, not aim. Targeting piles the budget onto a few clusters, and any rule that piles it the same way works just as well: point the same lopsided budget at the wrong clusters and the classifier still wins. Only removing the unevenness itself defeats it. What looked like an effect of targeting on the training set was an effect of concentrating it; the
comparison that settles this is not a random set, but one with the same lopsided shape
aimed at nothing in particular. Whether concentration also changes trained accuracy is a separate question, and we
test it directly rather than infer it from the training sets.""",
  r"""learns to tell which set an image came from even images it never saw. But it is picking up \revB{how the set was filled}, not aim. Targeting piles the budget onto a few clusters, and any rule that piles it the same way works just as well: point the same lopsided budget at the wrong clusters and the classifier still wins. \revB{Only a random draw defeats it; even a perfectly even quota, filled by the same matching to cluster centres, does not.} What looked like an effect of targeting on the training set was an effect of \revB{matching and} concentrating it; the
comparison that settles this is not a random set, but one with the same lopsided shape
aimed at nothing in particular. \revShared{Whether concentration also changes trained accuracy is a separate question, and we
test it directly rather than infer it from the training sets.}""",
  "intro-matching")
R(r"""In terms of trained accuracy, targeting shows no detectable advantage over random allocation. That null is
bounded rather than absolute: at eight seeds it excludes an advantage the size of the published method's own gain,
but not one between about $+0.005$ and $+0.0067$ $S_\alpha$, and a positive control confirms that the measurement
detects a real effect.
Substituting a perfect score using a test-set error for ours produces no detectable change either.""",
  r"""In terms of trained accuracy, targeting shows \revShared{no detectable advantage} over random allocation. That null is
bounded rather than absolute: \revShared{at eight seeds it excludes an advantage the size of the published method's own gain
but not smaller ones, and a pre-registered confirmatory campaign then establishes equivalence within $\pm0.005$
$S_\alpha$ on the primary comparison;} a positive control confirms that the measurement
detects a real effect.
\revB{Re-ranking the same allocation by each cluster's test-set error produces no detectable change, and neither do
oracle allocations of three other shapes.}""",
  "intro-bounded-null")
R(r"""\item \textit{A bounded null on the direction}: no detectable advantage, with the sizes of effect that are and are
not excluded stated, and five independent controls: a positive control, a perfect-score oracle, an unpinned
optimization schedule, a same-shape shuffle, and a seed expansion.""",
  r"""\item \textit{A bounded null on the direction}: \revShared{no detectable advantage, with the sizes of effect that are and are
not excluded stated, a pre-registered confirmatory test of equivalence,} and five independent controls: a positive control, \revB{an endpoint-error oracle at the committed shape and at three others}, an unpinned
optimization schedule, a same-shape shuffle, and a seed expansion.""",
  "intro-contribution-null")
R(r"""\item \textit{CHAMELEON is $50$ of $76$ images ($65.8\%$) training data} for models trained on""",
  r"""\item \textit{CHAMELEON is \revC{at least} $50$ of $76$ images ($65.8\%$) training data} for models trained on""",
  "intro-contribution-chameleon")
R(r"""These conclusions concern the allocation of a fixed, background-varied render pool, not uncertainty-guided generation
in general; Section~\ref{sec:discussion} states the scope exactly.""",
  r"""\revShared{These conclusions concern the allocation of a fixed, background-varied render pool, not uncertainty-guided generation
in general; Section~\ref{sec:discussion} states the scope exactly.}""",
  "intro-scope")
R(r"""Separately, we expose a major flaw in the standard CHAMELEON test set, where 50 of its 76 images are direct copies""",
  r"""Separately, we expose a major flaw in the standard CHAMELEON test set, where \revC{at least} 50 of its 76 images are direct copies""",
  "intro-chameleon-floor")

R(r"""Moreover, re-running the decisive comparison at eight
seeds per scenario leaves the gap \emph{smaller} than it was at three. Separately,""", r"""Separately,""", "cutI-intro-superseded-sentence (deleted, uncoloured)")

R(r"""and target our synthetic data generation toward those regions. The methods of that loop are
Standard and uses uncertainty sampling from active learning~\citep{settles2009active}, a student--teacher
disagreement score~\citep{tarvainen2017mean}, clustering over self-supervised
features~\citep{oquab2024dinov2} so the budget spreads rather than piling onto near-duplicates. The
composition is ours, and we failed to make it function.""", r"""and target our synthetic data generation toward those regions. Every ingredient of that loop is standard
(Section~\ref{sec:related}); the composition is ours, and we failed to make it function.""", "cut6-intro-redundant (uncoloured; same content in Sec. 1.1)")

# ================================================================ related work, methods (RL5B only)
R(r"""Unsupervised RISE~\citep{du2025rise} reaches higher absolute accuracy by a different route, pseudo masks on the real target images (Appendix~\ref{app:related}).""",
  r"""\revA{Unsupervised RISE~\citep{du2025rise} reaches higher absolute accuracy by a different route, pseudo masks on the real target images (Appendix~\ref{app:related}).}""",
  "related-rise")
R(r"""\emph{and} the seeds agree on
its sign (every seed at three seeds; at least seven of eight in the eight-seed expansion, a threshold fixed before
that campaign ran);""",
  r"""\emph{and} \revA{the seeds agree on
its sign (every seed at three seeds; at least seven of eight in the eight-seed expansion, a threshold fixed before
that campaign ran)};""",
  "methods-sign-rule")

# ================================================================ 3.1
R(r"""\textit{Aiming the budget by uncertainty showed no detectable advantage over spending it at random.}""",
  r"""\textit{Aiming the budget by uncertainty \revShared{showed no detectable advantage over} spending it at random.}""",
  "null-opening")
R(r"""compares against a method we expected to be clearly worse, clears its bar more than threefold.
Per-cell tables for both architectures and both endpoints are in Appendix~\ref{app:diag}.""",
  r"""compares against a method we expected to be clearly worse, clears its bar more than threefold.
\revB{ORS (oracle allocations of other shapes) was run after review and reads endpoint labels to choose training data (Appendix~\ref{app:shapeoracle}).}
Per-cell tables for both architectures and both endpoints are in Appendix~\ref{app:diag}.""",
  "table2-caption")
R(r"""\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}llcccccl@{}}
\toprule
& What it tests""", r"""\small
\setlength{\tabcolsep}{2.5pt}
\begin{tabular}{@{}llcccccl@{}}
\toprule
& What it tests""", "table2-padding (uncoloured; fits the ORS rows)")
R(r"""FX & the optimisation budget unpinned & $3$ & C10FX$-$BFX & $+0.0014$ & $0.0116$ & $0.12$ & \textsc{within noise} \\
\midrule""",
  r"""FX & the optimisation budget unpinned & $3$ & C10FX$-$BFX & $+0.0014$ & $0.0116$ & $0.12$ & \textsc{within noise} \\
\revB{ORS} & \revB{oracle, ten worst clusters} & \revB{$3$} & \revB{TOP10$-$CORACLE} & \revB{$+0.0022$} & \revB{$0.0057$} & \revB{$0.38$} & \revB{\textsc{within noise}} \\
 & \revB{the same quotas, aim shuffled} & \revB{$3$} & \revB{TOP10$-$SHUF} & \revB{$-0.0002$} & \revB{$0.0057$} & \revB{$0.03$} & \revB{\textsc{within noise}} \\
\midrule""",
  "table2-rows")
R(r"""rank correlation of $+0.2372$, so we replaced the signal with something several times better aimed, and the trained result did not notice. So the absence of a detectable advantage is not specific to our score: a score aimed with the true endpoint error shows none either.""",
  r"""rank correlation of $+0.2372$, so we replaced the signal with something several times better aimed, and the trained result did not notice. \revShared{So the absence of a detectable advantage is not specific to our score: a ranking built from the true endpoint error shows none either, at this allocation shape.} \revB{Because that oracle keeps C10's shape, after review we also tested oracle allocations of three other shapes from the same error vector (proportional to error, the ten worst clusters, the five worst) and a same-shape shuffle of the ten-cluster one (Table~\ref{tab:trained}, ORS; Appendix~\ref{app:shapeoracle}). None resolves a gain over the C10-shaped oracle on either endpoint, and at the ten-cluster shape true-error aim does no better than shuffling, although these arms read COD10K-test labels, a leak that could only help them.}""",
  "null-oracle-shapes")
R(r"""\emph{Perhaps three seeds are too few.} They were, which is why the seed expansion above exists.
It is a separate campaign with its own arms, noise estimate, and verdicts rather than extra seeds
bolted onto a finished one, because adding seeds after seeing a result is how a null gets talked
into existence.""",
  r"""\emph{Perhaps three seeds are too few.} They were, which is why the seed expansion above exists, as a
separate campaign rather than extra seeds bolted onto a finished one.""",
  "cut5-three-seeds")
R(r"""would see the difference. It did, comfortably and with every seed agreeing. And that control does not close the gap that matters most. It shows an effect of roughly the reference magnitude is visible; it does not show that an effect the size of our nulls would be.
The control's own bar, $0.0060$, is itself larger than the decisive gap it is meant to reassure us
about, so a positive control at $0.02$ licenses \emph{the instrument works}, not \emph{it would have
seen the effect we are nulling}.""",
  r"""would see the difference. It did, comfortably and with every seed agreeing. It shows that an effect of roughly the reference magnitude is visible, not that an effect the size of our nulls would be.""",
  "cut4-positive-control")
R(r"""The decisive statement is the pre-registered one above: no effect on the primary cell larger than the bar the seed expansion
measured. That rule was built to catch effects the size of the reference effect, not effects near zero: simulated
exactly, it detects a true advantage of $+0.005$ only about one time in five, and the effect it detects with 80\%
probability is about $0.0087$. Two conclusions therefore have to be kept apart. A difference is \emph{not detected}
when its 95\% interval contains zero; two arms are \emph{equivalent} when the whole 90\% interval of their difference
lies inside a margin small enough not to matter, here $\pm 0.005$, about a third of the reference effect. On the
primary cell the post-hoc interval for the two arms actually compared is $[-0.0020, +0.0067]$: nothing is detected
and the reference effect is \textit{excluded by more than a factor of two}, but equivalence is not established
(TOST $p = 0.101$), because advantages between about $+0.005$ and $+0.0067$ remain possible.
Table~\ref{tab:ci_tost} applies the same distinction to all sixteen eight-seed contrasts. These intervals are post hoc
and decide nothing. \eqverdict

\input{table_ci_tost.tex}""",
  r"""The decisive statement is the pre-registered one above: no effect on the primary cell larger than the bar the seed expansion
measured. \revShared{That rule was built to catch effects the size of the reference effect, not effects near zero: simulated
exactly, it detects a true advantage of $+0.005$ only about one time in five, and the effect it detects with 80\%
probability is about $0.0087$. Two conclusions therefore have to be kept apart. A difference is \emph{detected}
when its 95\% interval excludes zero; two arms are \emph{equivalent} when the whole 90\% interval of their difference
lies inside a margin small enough not to matter, here $\pm 0.005$, about a third of the reference effect. At eight seeds the
primary interval is $[-0.0020, +0.0067]$ (Table~\ref{tab:equiv}): nothing is detected
and the reference effect is \textit{excluded by more than a factor of two}, but equivalence is not
(TOST $p = 0.101$).} \revC{Pairing the arms by seed does not sharpen this: B redraws its images at every seed, so a seed
shares training randomness but not data, and the paired scores are uncorrelated ($r = -0.04$).}
\revShared{We therefore ran a separately pre-registered confirmatory campaign on SINet (fresh seeds; arms B, C10, CSHUF;
29 seeds per arm from a TOST power analysis, capped at 27 before any run). Hardware interruptions left it incomplete at
16, 15 and 15 seeds; every completed run is analysed as pre-registered, and none is dropped. On the primary cell it
establishes equivalence within $\pm 0.005$ ($\Delta = +0.0006$, 90\% interval $[-0.0027, +0.0039]$, TOST $p = 0.015$).
Against the same-shape shuffle on COD10K-test it establishes neither a difference nor equivalence ($\Delta = -0.0009$, 95\%
interval $[-0.0060, +0.0043]$); on NC4K both contrasts are equivalent (design and deviations: Appendix~\ref{app:diag}).}

\input{table_equiv.tex}""",
  "null-equivalence-block")

# ================================================================ 3.2
R(r"""\subsection{Concentration, Not Targeting, Shapes the Training Set}""",
  r"""\subsection{Concentration, Not Targeting, \texorpdfstring{\revShared{Shapes the Training Set}}{Shapes the Training Set}}""",
  "s32-heading")
R(r"""The null above concerns the endpoint. It does not say that targeting changes nothing, and it plainly does change
something, because a targeted training set is easy to tell apart from a random one. Three claims follow, and they rest
on different evidence. \textit{First, established: what makes a targeted training set different is that the budget is
concentrated on a few clusters, not that it is aimed at the right ones}; the geometry of the selected sets shows this.
\textit{Second, established: where the concentrated budget points makes no detectable difference to trained accuracy},
because arms with the same concentration and different directions cannot be told apart. \textit{Third, a hypothesis
until tested: that concentration itself changes trained accuracy.} The same-shape arms cannot answer this, because the
effect of the shape cancels from every comparison among them, so we tested it with a separate pre-registered experiment
that varies concentration and averages direction out (end of this section).""",
  r"""\revShared{The null above concerns the endpoint, but targeting plainly changes something: a targeted training set is easy to
tell apart from a random one. Three claims follow, on different evidence.} \textit{\revShared{First, established:} \revB{what makes
a targeted training set different is how the selector fills each cluster and how unevenly it spreads the budget, not
where the budget is aimed.}} \revShared{\textit{Second, established: where the budget points makes no detectable difference to
trained accuracy.} \textit{Third, tested and not supported: that concentration itself changes trained accuracy}, which the
same-shape arms cannot answer, because the shape cancels from every comparison among them (end of this section).}""",
  "s32-three-claims")
R(r"""Only removing the unevenness itself, by drawing two random sets of equal size, collapses it (Figure~\ref{fig:thesis}a). The probe was detecting the concentration the whole time.""",
  r"""\revB{Only drawing at random collapses it (Figure~\ref{fig:thesis}a). A perfectly even quota, filled by the same matching to
cluster centres, still separates from random draws (held-out $d = 0.52$, against $0.64$ for the targeted set, in a
post-review run of the same probe; Appendix~\ref{app:shapeoracle}): the probe detects the matched, concentrated
selection, and the direction of the signal adds nothing to it.}""",
  "s32-probe-matching")
R(r"""effective rank than a random draw's in all twenty cells (mean ratio $0.634$), and covers no more of
the target manifold.""",
  r"""effective rank \revB{(participation ratio)} than a random draw's in all twenty cells (mean ratio $0.634$)\revB{, a property of
these selections, not of concentration (Appendix~\ref{app:shapeoracle})}, \revC{and whether it covers more of the target depends on the
estimator (Appendix~\ref{app:coverage})}.""",
  "s32-rank-coverage")
R(r"""At eight seeds, a formal equivalence test becomes informative, and it adds no asymmetry (Table~\ref{tab:ci_tost}).
Before any correction for multiple comparisons, five of the sixteen gaps are equivalent within $\pm 0.005$: four
direction contrasts, and the targeting-versus-random gap on NC4K only. On the primary cell, targeting against its own
shuffle is equivalent ($p = 0.019$) and targeting against random is not ($p = 0.101$). After a Holm correction across
the sixteen, none is equivalent. These tests are post hoc and decide nothing.""",
  r"""\revShared{Equivalence tests on all sixteen eight-seed gaps add no asymmetry either (Table~\ref{tab:ci_tost}): five are
equivalent within $\pm 0.005$ before correction, four of them direction contrasts, and none after a Holm correction.}""",
  "cut2-s32-equivalence")
R(r"""move. We therefore re-scored every committed prediction with two boundary metrics (Table~\ref{tab:boundary} in Appendix~\ref{app:diag}). At
three seeds, on SINet, both comparisons of a concentrated arm against random cleared their bars, the targeted arm at
$1.37\times$ and the anti-targeted arm at $1.34\times$, while the direction contrasts stayed far inside theirs.
\textit{At eight seeds that pattern does not hold}: on SINet the targeted arm sits at $0.30\times$ its bar
($+0.0046$ Boundary-IoU) and the anti-targeted arm at $0.64\times$ ($+0.0098$), both within noise, and SINet-v2
resolves none of the contrasts at either seed count. The boundary metrics therefore do not establish that
concentration changes accuracy.""",
  r"""move. \revShared{We therefore re-scored every committed prediction with two boundary metrics (Table~\ref{tab:boundary}, Appendix~\ref{app:diag}).
The three-seed pattern, in which both concentrated arms cleared their bars on SINet, \textit{does not hold at eight seeds}: no
contrast on either architecture clears its bar, and none of the $140$ eight-seed contrasts survives a Holm correction.}
\revC{The architecture interaction is not resolved either way.} \revShared{One exploratory signal remains: on SINet the reversed
arm leads random by $+0.0098$ Boundary-IoU (paired 95\% interval $[+0.0039, +0.0157]$, $7/8$ seeds, $0.64\times$ its bar),
before correction only (Holm-adjusted $p = 0.79$); the targeted arm, with identical concentration, does not ($0.30\times$),
so concentration cannot explain it.}""",
  "cut3-s32-boundary")
R(r"""Cohen's $d$. Every rule that keeps the allocation's \emph{concentration} reproduces the separation;  only destroying concentration collapses it.""",
  r"""Cohen's $d$. Every rule that keeps the allocation's \emph{concentration} reproduces the separation; \revB{only a random draw collapses it (a flat quota under the same matching does not; Appendix~\ref{app:shapeoracle}).}""",
  "fig3-caption")
R(r"""These metrics were not pre-registered and re-decide no verdict; Table~\ref{tab:trained} stands. They binarise
predictions where $S_\alpha$ does not. The question they could not settle, whether concentration changes accuracy, is
the one our dose-response experiment was designed for. It holds the budget at 1,000 images and sets three levels of
concentration: cluster-uniform, the committed shape, and one twice as concentrated. Each concentrated level is
realised with five independent random directions, so direction averages out, and the experiment was pre-registered
with Boundary-IoU on SINet as its primary measure. \cdrverdict{} As delivered, the levels are closer than their quotas (effective numbers of clusters 50, 45 and 41, against 75, 30 and 15; random selection 43), because few foregrounds lie close to most clusters (Section~\ref{sec:discussion}). The planned replication on SINet-v2 was not run, for
lack of compute.""",
  r"""\revShared{These metrics were not pre-registered and re-decide no verdict. Whether concentration changes accuracy is what our
dose-response experiment was designed to test. It holds the budget at 1,000 images and sets three levels of
concentration: cluster-uniform, the committed shape, and one twice as concentrated. Each concentrated level is
realised with five independent random directions, so direction averages out, and the experiment was pre-registered
with Boundary-IoU on SINet as its primary measure (Table~\ref{tab:cdr}). \cdrverdict{} As delivered, the levels are closer than their quotas (effective numbers of clusters 50, 45 and 41, against 75, 30 and 15; random selection 43), because few foregrounds lie close to most clusters (Section~\ref{sec:discussion}). The planned replication on SINet-v2 was not run, for
lack of compute.}""",
  "s32-cdr")

# ================================================================ 3.3
R(r"""Concentration explains why targeting \emph{looks} the way it does.""",
  r"""\revB{Matching and concentration explain} why targeting \emph{looks} the way it does.""",
  "s33-opening")
R(r"""($k$-NN recall, Appendix~\ref{app:coverage}), while the generator's own source photographs, real""",
  r"""($k$-NN recall \revB{at $k = 5$}, Appendix~\ref{app:coverage}\revB{; lower than the input at every $k$ from $3$ to $20$}), while the generator's own source photographs, real""",
  "s33-coverage-k")

# ================================================================ 3.4 CHAMELEON (dypE QA-03)
R(r"""format, so not one byte matches while every pixel does. Sixteen images resolve neither way and are
reported \textsc{unchecked} rather than clean, so $50$ is a floor rather than an estimate.""",
  r"""format, so not one byte matches while every pixel does. Sixteen images resolve neither way \revC{against the training pools} and are
reported \textsc{unchecked} rather than clean, so $50$ is a floor rather than an estimate\revC{. The sixteen are re-encodes
of COD10K-test photographs, as are $32$ of the $76$, so CHAMELEON and COD10K-test are not independent benchmarks
(Appendix~\ref{app:chamext})}.""",
  "s34-floor-cod10k")
R(r"""Nor do we recommend reporting CHAMELEON on its uncontaminated subset,
because that subset is now $10$ images, one of which is byte-identical to an
image in the split we select checkpoints on. \textit{A ten-image endpoint is not an endpoint:
report COD10K-test and NC4K instead, and disclose the unchecked share.}""",
  r"""Nor do we recommend reporting CHAMELEON on its uncontaminated subset\revC{: of the $26$ images without a training-pool partner,
$24$ are re-encodes of COD10K-test photographs, and we found no duplicate anywhere for only two.} \textit{\revC{A two-image endpoint is not an endpoint}:
report COD10K-test and NC4K instead, and disclose the unchecked share.}""",
  "s34-subset")

# ================================================================ discussion
R(r"""\emph{geometric} result is positive, and we state it without hedging: concentration, not the
direction of the uncertainty signal, produces the separation that makes targeted selection look like it works. The \emph{downstream} result is a null under stated sensitivity: it excludes an advantage the size of the published method's own gain, a confirmatory campaign bounds the primary gap within $\pm0.005$, and it does not show that uncertainty guidance cannot work.""",
  r"""\emph{geometric} result is positive, and we state it \revB{plainly: the selector's matching and the budget's concentration}, not the
direction of the uncertainty signal, produce the separation that makes targeted selection look like it works. The \emph{downstream} result is a null under stated sensitivity: \revShared{it excludes an advantage the size of the published method's own gain, a confirmatory campaign bounds the primary gap within $\pm0.005$, and it} does not show that uncertainty guidance cannot work.""",
  "discussion-geometric")
R(r"""grows with the pool rather than one under which added images displace real ones, a foreground supply
not already exhausted, a generator wider than its own input,""",
  r"""grows with the pool rather than one under which added images displace real ones, a foreground supply
not already exhausted \revC{(in this pool a larger budget does not widen the contrast between arms; Appendix~\ref{app:diag})}, a generator wider than its own input,""",
  "discussion-preflight")
R(r"""In 52 of the 75 target clusters, the nearest available foreground cut-out lies farther from
the cluster's centre than the cluster's median real image, partly because a cut-out on a plain background and a full
photograph differ.""", r"""In 52 of the 75 target clusters, the nearest available cut-out lies farther from the cluster's
centre than the cluster's median real image, partly a cut-out-versus-photograph difference.""", "cutK-scope-compress (inside orange span; caveat kept)")
R(r"""\textit{Scope.} Every conclusion here is bounded to what was tested.""",
  r"""\revShared{\textit{Scope.} Every conclusion here is bounded to what was tested.""",
  "scope-open")
R(r"""foregrounds for the hardest clusters, or one steered by the score while it generates, is outside this experiment, and
we make no claim about other generators.""",
  r"""foregrounds for the hardest clusters, or one steered by the score while it generates, is outside this experiment, and
we make no claim about other generators.} \revB{A modern transformer-based detector is untested as well.}""",
  "scope-close-detector")

# ================================================================ conclusion
R(r"""route to an artifactual null, the gap stays within noise. \eqshort{} Targeting does change the training set,
but through concentration rather than aim, which only a same-shape control exposes. \cdrshort{} These conclusions hold
for allocation over a fixed LAKE-RED render pool that varies only backgrounds, with the clusters, architectures,
training scheme and budget we tested. Independently,
$50$ of CHAMELEON's $76$ images are altered copies""",
  r"""route to an artifactual null, the gap stays within noise\revShared{, and a pre-registered confirmatory campaign, incomplete at
16, 15 and 15 of 27 seeds per arm, establishes equivalence within $\pm0.005$ on the primary comparison}. Targeting does change the training set,
but through \revB{matching and} concentration rather than aim\revShared{: same-shape controls show that direction adds nothing
detectable, and a pre-registered dose-response test found no effect of concentration on accuracy. These conclusions hold
for allocation over a fixed LAKE-RED render pool that varies only backgrounds (Section~\ref{sec:discussion})}. Independently,
\revC{at least} $50$ of CHAMELEON's $76$ images are altered copies""",
  "conclusion")
R(r"""Under a fixed synthetic-data budget, aiming a pool of generated images at the clusters a model finds hardest showed no detectable advantage over spending it at random.""",
  r"""Under a fixed synthetic-data budget, aiming \revShared{a pool of generated images} at the clusters a model finds hardest \revShared{showed no detectable advantage over} spending it at random.""",
  "conclusion-open")

# ================================================================ statements (excluded from the page count)
R(r"""categories theoretical frameworks, mathematical claims and proofs, translation, and qualitative
data analysis do not apply.""",
  r"""categories (theoretical frameworks, mathematical claims and proofs, translation, and qualitative
data analysis) do not apply.""",
  "ai-use-grammar (uncoloured)")
R(r"""decision rules governing every verdict: the arms, the endpoints, the seeds, the noise estimate,
and the verdict bands, were pre-registered before the runs they govern
(Appendix~\ref{app:method}), with amendments append-only and dated; any analysis outside those rules
is reported as post-hoc and marked as deciding nothing (Tables~\ref{tab:tost}
and~\ref{tab:boundary}).""",
  r"""decision rules governing every verdict (the arms, the endpoints, the seeds, the noise estimate,
and the verdict bands) were \revB{committed before any result they decide, and all but one before the runs they govern}
(Appendix~\ref{app:method}), with amendments append-only and dated; any analysis outside those rules
is reported as post-hoc and marked as deciding nothing (Tables~\ref{tab:ci_tost}
and~\ref{tab:boundary}).""",
  "ai-use-prereg-timing")
R(r"""The decision rules governing every result are committed before the runs they govern, at the commits
named in Appendix~\ref{app:method},""",
  r"""The decision rules governing every result are \revB{committed before any result they decide, and all but one before the runs they govern}, at the commits
named in Appendix~\ref{app:method},""",
  "repro-prereg-timing")
R(r"""caption names it. Per-run metrics for all $103$ training runs are in the supplement
(\texttt{rebuild/FinalPaper/results.md});""",
  r"""caption names it. Per-run metrics for all $103$ training runs are in the supplement
(\texttt{rebuild/FinalPaper/results.md})\revShared{; the post-review campaigns add $99$ trained runs (confirmatory $46$,
dose-response $35$, oracle shapes $12$, supervised references $6$), whose records are in the repository's rebuttal
packages}""",
  "repro-run-count")

# ================================================================ appendix
R(r"""\appendix
""", r"""\appendix

\ifrevmarked
\paragraph{Revision colours.} In this marked copy, changes made in response to the discussion are coloured by the
reviewer concern they address: \revA{RL5B only, blue}; \revB{Caus only, teal}; \revC{dypE only, purple}; and
\revShared{two or more reviewers, orange}, which overrides the individual colours. Text that is not coloured is
unchanged from the submission or was only moved.
\fi
""", "appendix-legend")

R(r"""Unsupervised COD avoids masks altogether. RISE~\citep{du2025rise} clusters each training image with frozen DINOv2""",
  r"""\begin{revblock}{RevA}Unsupervised COD avoids masks altogether. RISE~\citep{du2025rise} clusters each training image with frozen DINOv2""",
  "appA-rise-open")
R(r"""difference in detector or representation.

\input{gap_paragraph.tex}

\input{table_protocol.tex}""",
  r"""difference in detector or representation.

\input{gap_paragraph.tex}
\end{revblock}

\input{table_protocol.tex}""",
  "appA-rise-close")
R(r"""(the mean E-measure over thresholds, the variant SINet-V2 and RISE report) are computed and reported, but they decide
nothing.""",
  r"""\revA{(the mean E-measure over thresholds, the variant SINet-V2 and RISE report)} are computed and reported, but they decide
nothing.""",
  "appB-emeasure")
R(r"""MT); T2 is the falsification campaign (CSHUF, CINV).""",
  r"""MT); T2 is the falsification campaign (CSHUF, CINV)\revB{; ORS is the post-review oracle-shape campaign
(Appendix~\ref{app:shapeoracle})}\revShared{; EQ and CDR are the post-review confirmatory-equivalence and dose-response
campaigns (Appendix~\ref{app:diag})}.""",
  "appB-campaign-codes")
R(r"""\textsc{not detected} ($|\Delta| \le 2\hat{\sigma}$). The eight-seed expansion
requires at least seven of eight seed-paired differences to agree in sign, a threshold its pre-registration fixed
before its first run: under a fair coin, seven or more of eight has probability $9/256 \approx 0.035$, stricter than
three of three ($0.125$).""",
  r"""\textsc{not detected} ($|\Delta| \le 2\hat{\sigma}$). \revA{The eight-seed expansion
requires at least seven of eight seed-paired differences to agree in sign, a threshold its pre-registration fixed
before its first run: under a fair coin, seven or more of eight has probability $9/256 \approx 0.035$, stricter than
three of three ($0.125$).}""",
  "appB-sign-rule")
R(r"""\paragraph{Pre-registration commits and amendments.} Every decision rule was committed before the
runs it governs. The four-arm rule is recorded at \texttt{065dac6}, the commit carrying that
campaign's first log block; the falsification campaign's at \texttt{617a2e1}; the signal-generality
check's at \texttt{6efde9f}; the area control's and the positive control's at \texttt{c2114af}; the
seed expansion's at \texttt{b755aa9}, dated 2026-09-18. The oracle and optimization schedule
campaigns carry their own pre-registrations, each committed before that campaign's first training
run. Three amendments exist,""",
  r"""\paragraph{Pre-registration commits and amendments.} Every decision rule \revB{but one} was committed before the
runs it governs. The four-arm rule is recorded at \texttt{065dac6}, the commit carrying that
campaign's first log block; the falsification campaign's at \texttt{617a2e1}; the signal-generality
check's at \texttt{6efde9f}; the area control's and the positive control's at \texttt{c2114af}\revB{, which was later reset off
the branch and is preserved under the tag \texttt{prereg-ac-pc-c2114af}; the seed expansion's and the
optimization-schedule campaign's at \texttt{a79886a} (2026-09-18 11:48, before either campaign's first run), preserved
under the tag \texttt{prereg-or-fx-se-a79886a}. The oracle campaign's rule was written before any of its scores existed
and committed in the same \texttt{a79886a}, $62$ minutes after its first run had started (first run 10:46, commit
11:48, first score 18:23). The post-review oracle-shape rule (ORS) was committed at \texttt{b21b67c} (2026-11-11), before its
pilot}\revShared{; the confirmatory (EQ) and dose-response (CDR) rules at \texttt{2137849} (2026-11-09), and EQ's one
amendment, which capped $n$ at $27$ per arm and fixed the analysis of an incomplete campaign, at \texttt{808988b}
(2026-11-11), before any EQ run (first CDR run 2026-11-11 18:26; first EQ run 2026-11-13 23:59)}. Three amendments \revShared{to the submitted campaigns} exist,""",
  "appB-prereg-commits")

# ---- appendix C
R(r"""measured on this cell, $0.0055$. Appendix~\ref{app:diag} gives the per-arm spreads.""",
  r"""measured on this cell, $0.0055$. The paragraphs below give the per-arm spreads.""",
  "appC-selfref (uncoloured)")
R(r"""\input{table_boundary_8seed.tex}


\paragraph{Why the committed bar is so wide""",
  r"""\input{table_cdr.tex}

\input{table_boundary_8seed.tex}

\paragraph{Why the committed bar is so wide""",
  "appC-cdr-table")
R(r"""\input{table_tost_equivalence.tex}
""",
  r"""\input{table_ci_tost.tex}

\begin{revblock}{RevShared}
\paragraph{The confirmatory equivalence campaign (EQ).} It was pre-registered after review, with Welch TOST at
$\pm 0.005$ $S_\alpha$ on SINet $\cdot$ COD10K-test as its primary test (H1, C10$-$B) and C10$-$CSHUF as its secondary
test (H1b). A power analysis gave $29$ seeds per arm for power $0.80$ at a true $\Delta = +0.0024$; the first amendment
capped this at $27$ (seeds $101$--$127$, power $0.78$) before any run and fixed the rule for a campaign the cutoff
interrupts: every completed run of each arm is analysed, none is dropped, and the result is labelled incomplete.
Repeated power outages left $46$ of the $81$ runs complete, $16$ (B, seeds $101$--$116$), $15$ (C10) and $15$ (CSHUF,
both seeds $101$--$115$). Run-to-run spread is larger than in the eight-seed campaign ($\hat\sigma = 0.0064$ against
$0.0034$), and it tracks how many target images each run's self-training round pseudo-labels ($r = 0.74$ across runs).
Two checks run after the cutoff are exploratory and decide nothing: same-seed re-training shows that training is not
reproducible run to run (one re-train moved from $0.6933$ to $0.7214$), and leaving out either of the two runs with the
fewest pseudo-labels changes neither verdict.
\end{revblock}

\input{table_paired.tex}
""",
  "appC-ci_tost-eq-paired")
R(r"""\input{boundary_sweep.tex}
""",
  r"""\begin{revblock}{RevShared}
\input{boundary_sweep.tex}
\end{revblock}

\begin{revblock}{RevC}
\paragraph{Architecture, multiplicity and domain mix.} Tested directly, the difference between the architectures'
Boundary-IoU gains over random (threshold $0.5$, COD10K-test) is $+0.0044$ (95\% CI $[-0.0075, +0.0163]$, $p = 0.43$)
for the targeted arm and $+0.0065$ ($[-0.0001, +0.0131]$, $p = 0.053$) for the reversed arm, so the interaction is not
resolved either way: we cannot say the two architectures differ, or that they agree. None of the $140$ eight-seed
contrasts (two boundary metrics at three thresholds and $S_\alpha$, on both architectures and endpoints) survives a Holm
correction; the smallest adjusted $p$ is $0.50$. On $S_\alpha$ the reversed arm also leads random on SINet $\cdot$
COD10K-test ($+0.0045$, paired 95\% CI $[+0.0015, +0.0074]$), inside its bar ($0.65\times$) and not after correction.
One candidate explanation, untested: the three same-shape arms put $53\%$, $29\%$ and $20\%$ of their budget on CAMO
images (targeted, shuffled, reversed), and neither endpoint contains CAMO images.
\end{revblock}
""",
  "appC-boundary-interaction")
R(r"""\paragraph{How much the trained comparison is attenuated.} The trained half of the concentration
result is diluted three times over, and we disclose it because the attenuation biases toward the
null we report. Injected images are $1000$ of $5447$ pairs, or $18.4\%$ of the pool; under the
committed schedule, the pinned step count dilutes their exposure further; and only about $48\%$ of
injected images differ between any two arms, giving an effective contrast near $8.8\%$. Two of the
three are now measured rather than argued: the optimization-schedule campaign removes the pin and
the decisive gap \emph{shrinks}, and the seed expansion raises the degrees of freedom behind the
bar from $8$ to $28$. What remains is the third, which is a property of comparing two arms that
share their whole base pool and roughly half of their injected images by construction.""",
  r"""\paragraph{How much the trained comparison is attenuated.} The trained half of the concentration
result is diluted three times over, and we disclose it because the attenuation biases toward the
null we report. Injected images are $1000$ of $5447$ pairs, or $18.4\%$ of the pool; under the
committed schedule, the pinned step count dilutes their exposure further; and \revC{how many injected images differ depends
on the comparison. The three concentrated arms share about half of theirs ($45$--$51\%$ differ, $8.3$--$9.4\%$ of the
training pool). Targeted and random selection share far less, $209$--$246$ of $1000$ per seed, close to the $225$
expected by chance, so $77\%$ of injected images and $14.1\%$ of the training pool differ in the decisive comparison.
Under the pinned schedule an epoch draws $4048$ of the $5447$ source images, so images present only in the targeted arm
are about $14\%$ of source draws in round one and $10\%$ in round two (expected values; the sampler order was not
logged). Between rounds each arm also appends its own pseudo-labelled target images, and the targeted and random sets
of these overlap only at Jaccard $0.58$--$0.68$, a second difference that follows from the first round and is reported
rather than adjusted away. A larger budget does not widen the decisive contrast in this pool: the differing share is
$17.2\%$ at $2000$ images ($1.22\times$ the committed one), $13.1\%$ at $3000$ and $0$ at $4447$, because random
selection draws from the same finite foreground set that targeting ranks; a preflight fixed in advance required
$1.5\times$ before any training, and it failed, so nothing was trained.} Two of the
three \revC{attenuations} are now measured rather than argued: the optimization-schedule campaign removes the pin and
the decisive gap \emph{shrinks}, and the seed expansion raises the degrees of freedom behind the
bar from $8$ to $28$. What remains is the third, which is a property of comparing two arms that
share their whole base pool \revC{and, for the concentrated arms, about half of their injected images}.""",
  "appC-attenuation")

# ---- CHAMELEON appendix
R(r"""\paragraph{Scope of the exact-hash zero.} The $0$ we report is measured against the training pool.
Across benchmarks it is not zero: \texttt{animal-17}, \texttt{animal-25} and \texttt{animal-60} are
byte-identical to CAMO-250 images. Those files are absent from the training pool and so do not enter
the contamination count, but CAMO-250 is the split that this repository selects checkpoints on.

\paragraph{What remains uncounted.} Sixteen images have no partner at either tier and are reported
\textsc{unchecked}, not clean. Different photographs of one specimen, montages, and heavy color edits
are not detected and are not claimed. Every figure here is a lower bound.""",
  r"""\paragraph{Scope of the exact-hash zero.} The $0$ we report is measured against the training pool.
Across benchmarks it is not zero: \texttt{animal-17}, \texttt{animal-25} and \texttt{animal-60} are
byte-identical to CAMO-250 images\revC{, and \texttt{animal-28} is a re-encoded copy of a fourth}. Those files are absent from the training pool and so do not enter
the contamination count, but CAMO-250 is the split that this repository selects checkpoints on.
\revC{Pointed at COD10K-test, the released same-dimension detector, unchanged and at its published tolerance, finds
$32$ re-encoded duplicates, including all sixteen images that are unchecked against the training pools.
Table~\ref{tab:chamcount} reconciles every count.}

\input{table_cham_counts.tex}

\begin{revblock}{RevC}
\paragraph{What the overlap means for each protocol.} \emph{Supervised training} on COD10K-train and CAMO-train trains on
$50$ of the $76$ photographs with their own COD10K or CAMO masks, which breaks independent evaluation whether or not a
score moves. \emph{Unlabelled target adaptation}, our protocol, puts the same photographs in the unlabelled target pool;
between rounds $14$--$32$ of the $50$ matches per run (mean $24.7$) were re-used with the model's own predicted
mask as a pseudo-label, and no CHAMELEON annotation is used anywhere, so this is exposure to the image, not label
leakage, and its effect would depend on the method. \emph{Checkpoint selection} on CAMO-250 gives any protocol that also
reports CHAMELEON a label-based selection path through four photographs. \emph{Evaluation} on COD10K-test as well is
not independent, through $32$ re-encodes. NC4K shares none. None of these overlaps touches a number in this paper,
because CHAMELEON is not one of our endpoints. COD10K-test itself, as distributed, contains $7$ images byte-identical to
images in the standard COD10K-train split ($2$ under the same file name); those training images are in our unlabelled
target pool, so every arm and every baseline is exposed to the same $7$ without labels and scored on the same split. No
contrast is affected, but absolute COD10K-test numbers include them.
\end{revblock}

\paragraph{What remains uncounted.} Sixteen images have no partner at either tier and are reported
\textsc{unchecked} \revC{against the training pools; each is a re-encode of a COD10K-test photograph. Ten more have no
training-pool partner after Tier A checked their dimension group; eight of them are COD10K-test photographs, and for
the other two we found no duplicate anywhere. We call these \emph{no duplicate found}}, not clean. Different photographs of one specimen, montages, and heavy color edits
are not detected and are not claimed. Every figure here is a lower bound.""",
  "appE-chameleon")

# ---- controls appendix
R(r"""on the endpoint. That is information no real method could have, and the pre-registration says so
before the first run: it is a diagnostic upper bound and never a method,""",
  r"""on the endpoint. That is information no real method could have, and the pre-registration\revB{, written before any oracle
score existed,} says so: it is a diagnostic upper bound and never a method,""",
  "appG-oracle-timing")
R(r"""different number of differently-labeled images. Over the 40 runs the seed expansion added (seeds 46--50), the means
are $1977$ (B), $2025$ (C10), $1990$ (CSHUF) and $1979$ (CINV), with per-run values spanning $1817$ to $2259$; over all
eight seeds they are $1991$, $2007$, $2020$ and $2015$, spanning $1782$ to $2278$.""",
  r"""different number of differently-labeled images. \revShared{Over the 40 runs the seed expansion added (seeds 46--50), the means
are $1977$ (B), $2025$ (C10), $1990$ (CSHUF) and $1979$ (CINV), with per-run values spanning $1817$ to $2259$; over all
eight seeds they are $1991$, $2007$, $2020$ and $2015$, spanning $1782$ to $2278$.}""",
  "appG-pseudolabel-means")

# ---- new appendix: oracle shapes (Caus)
R(r"""regardless, which is asserted per run.

\end{document}""",
  r"""regardless, which is asserted per run.

\section{\texorpdfstring{\revB{Post-review: Oracle Allocations of a Different Shape}}{Post-review: Oracle Allocations of a Different Shape}}
\label{app:shapeoracle}
\begin{revblock}{RevB}
CORACLE re-aims C10's quota multiset by true endpoint error and so tests direction at a fixed shape. To test shape, we
pre-registered (\texttt{b21b67c}, before any run) three oracle allocations at $N = 1000$, built from the same
endpoint-error vector and served by the same selector: \emph{OR-PROP}, quotas proportional to each cluster's error;
\emph{OR-TOP10}, $100$ images to each of the ten highest-error clusters; and \emph{OR-TOP5}, $200$ to each of the five
highest. \emph{OR-TOP10-SHUF} gives OR-TOP10's quotas to clusters drawn by a frozen permutation. All four use endpoint
labels to choose training data, so COD10K-test is not an unbiased endpoint for them; NC4K labels are read by no
allocation. Each was trained on SINet at the three committed seeds ($12$ runs). B, C10 and CORACLE are the committed
runs, reused after a gate: identical code path, data bytes and selections, committed metrics reproduced at six decimals,
and an identical first training step. The bar is twice the pooled seed-to-seed spread over the seven compared arms
($2\hat\sigma = 0.0057$ on COD10K-test and $0.0065$ on NC4K, $\mathrm{df} = 14$).

Two facts were fixed before any training. Because per-cluster error spans only $0.09$--$0.47$, the error-proportional
quota is nearly flat ($4$--$24$ per cluster); every permutation of it leaves at least $84\%$ of the selected images
unchanged, so its direction cannot be tested with this selector and its shuffle was not trained. And OR-TOP5 has no
same-shape control, so its contrast never isolates direction.

\begin{center}\small
\begin{tabular}{@{}lccccc@{}}
\toprule
Contrast (SINet, $n = 3$) & $\Delta$ COD10K & $\times$\,bar & sign & verdict & $\Delta$ NC4K \\
\midrule
OR-TOP10 $-$ CORACLE (shape) & $+0.0022$ & $0.38$ & 2/3 & \textsc{within noise} & $+0.0011$ \\
OR-TOP10 $-$ OR-TOP10-SHUF (aim) & $-0.0002$ & $0.03$ & 2/3 & \textsc{within noise} & $-0.0009$ \\
OR-PROP $-$ CORACLE (flat) & $+0.0023$ & $0.40$ & 2/3 & \textsc{within noise} & $+0.0028$ \\
OR-TOP5 $-$ CORACLE (shape + aim) & $+0.0011$ & $0.20$ & 2/3 & \textsc{within noise} & $+0.0005$ \\
\bottomrule
\end{tabular}
\end{center}

Every oracle arm lands between random allocation and our targeted arm: against B the COD10K-test differences are
$+0.0020$ to $+0.0032$, against C10 $-0.0019$ to $-0.0031$, all within noise. No oracle shape, flat, ten-cluster or
five-cluster, resolves a gain over the C10-shaped oracle at this sensitivity, and aim at the ten-cluster shape does
not resolve against its own shuffle, although the endpoint-label leak can only favour these arms. The bars are as wide
as the effects they would miss: effects below about $0.006$ can be missed with three seeds. This is a null at this
sensitivity, not evidence of no effect, and it says nothing about shapes we did not try or about SINet-v2, which we
did not re-run.

\paragraph{Separability does not require concentration.} Run through the same probe after review ($N = 1000$, the
same $20$ random draws), a perfectly even quota under the committed matching is still separable from random draws
(held-out $d = 0.52$, against $0.64$ for C10 and $0.61$ for CSHUF) and has a lower participation ratio than random
(ratio $0.855$). Concentration does not set the rank either: the five-cluster oracle has a ratio of $0.56$, while its
own shuffle, equally concentrated, keeps a near-random $0.94$. The lower effective rank of Section~\ref{sec:concentration}
is therefore an empirical property of these selections, and the separation a probe finds is the selector's matching
as much as the budget's concentration. Neither changes the controlled comparison: at a fixed shape, the direction of the
signal adds $+0.0073$ of a Cohen's $d$.
\end{revblock}

\end{document}""",
  "appH-shapeoracle")

# ================================================================ write the paper
(OUT / "REVISED_PAPER.tex").write_text(tex)

# ================================================================ generated inputs: colour and labels
# moved 16-row table: now in App. C; labels made consistent with Table 3 (detected / equivalent / neither)
edit_file("table_ci_tost.tex", [
    (r"""\begin{table}[t]
\caption{All sixteen eight-seed contrasts on $S_\alpha$.""",
     r"""\begin{table}[h]
\revfloatcolor{RevShared}
\caption{All sixteen eight-seed contrasts on $S_\alpha$ (moved from the main text; see Table~\ref{tab:equiv}).""",),
    (r"""zero, and \emph{equivalent} if its 90\% interval lies inside $\pm0.005$ (TOST, bold $p<0.05$).
A contrast that is neither is not evidence of equivalence: it is a failure to detect an effect at this
precision.""",
     r"""zero, and \emph{equivalent} if its 90\% interval lies inside $\pm0.005$ (TOST~\citep{lakens2017equivalence}, bold
$p<0.05$); \emph{neither} is a failure to detect an effect at this precision, not evidence of equivalence. The
smallest margin at which a contrast would be equivalent is the larger absolute end of its 90\% interval.""",),
], "appC-ci_tost-caption")
s = (OUT / "table_ci_tost.tex").read_text().replace("& not detected \\\\", "& neither \\\\")
(OUT / "table_ci_tost.tex").write_text(s)
edit_file("table_boundary_8seed.tex", [
    (r"""\begin{table}[t]
\caption{Boundary-IoU""", r"""\begin{table}[t]
\revfloatcolor{RevShared}
\caption{Boundary-IoU""")], "appC-boundary-table-colour")
edit_file("table_protocol.tex", [
    (r"""\begin{table}[t]
\caption{Protocols""", r"""\begin{table}[t]
\revfloatcolor{RevA}
\caption{Protocols"""),
    # double-rounding fix: the exact 8-seed mean is 0.717479 (rebuild/ABC/out/se/abc_metrics.csv), not 0.718
    (r"""LAKE-RED & 8 seeds & 0.718 & 0.748""", r"""LAKE-RED & 8 seeds & 0.717 & 0.748""")], "appA-protocol-table-colour+0.717-fix")

# ---- new tables
(OUT / "table_equiv.tex").write_text(r"""%% Values: RL5B STUDENT_RESULTS/RESULT_TABLES/EXP01_EQ.csv (confirmatory rows), TH01_contrasts.csv (8-seed Welch),
%% dypE STUDENT_RESULTS/RESULT_TABLES/TH-01_paired_inference.csv (8-seed paired). Checked by tools/verify_numbers.py.
\begin{table}[t]
\revfloatcolor{RevShared}
\caption{How small an advantage the primary comparison excludes ($S_\alpha$, SINet; C10 minus comparator; equivalence by
TOST~\citep{lakens2017equivalence} at $\pm0.005$). Eight-seed rows are post hoc. The confirmatory campaign is pre-registered
and \textsc{incomplete} (B/C10/CSHUF at $16/15/15$ of $27$ seeds); its $2\hat\sigma$ rule finds every gap within noise, and
H1 survives a Holm correction over its four tests ($p = 0.030$).}
\label{tab:equiv}
\begin{center}
\scriptsize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{@{}llllccccl@{}}
\toprule
Campaign & Endpoint & Comparator & Seeds & $\Delta$ & 95\% CI & 90\% CI & TOST $p$ & Reading \\
\midrule
Eight-seed, Welch & COD10K & B & $8/8$ & $+0.0024$ & $[-0.0020, +0.0067]$ & $[-0.0012, +0.0059]$ & $0.101$ & neither \\
Eight-seed, paired & COD10K & B & $8$ pairs & $+0.0024$ & $[-0.0023, +0.0070]$ & $[-0.0014, +0.0061]$ & $0.111$ & neither \\
\midrule
Confirmatory, H1 & COD10K & B & $15/16$ & $+0.0006$ & $[-0.0033, +0.0045]$ & $[-0.0027, +0.0039]$ & $\mathbf{0.015}$ & equivalent \\
Confirmatory, H1b & COD10K & CSHUF & $15/15$ & $-0.0009$ & $[-0.0060, +0.0043]$ & $[-0.0051, +0.0034]$ & $0.056$ & neither \\
Confirmatory & NC4K & B & $15/16$ & $+0.0005$ & $[-0.0016, +0.0025]$ & $[-0.0013, +0.0022]$ & $\mathbf{<0.001}$ & equivalent \\
Confirmatory & NC4K & CSHUF & $15/15$ & $-0.0005$ & $[-0.0030, +0.0019]$ & $[-0.0026, +0.0015]$ & $\mathbf{<0.001}$ & equivalent \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
(OUT / "table_paired.tex").write_text(r"""%% Values: dypE STUDENT_RESULTS/RESULT_TABLES/TH-01_paired_inference.csv. Checked by tools/verify_numbers.py.
\begin{table}[h]
\revfloatcolor{RevC}
\caption{Targeted minus random ($S_\alpha$) at eight seeds, paired by training seed beside the Welch analysis (post hoc;
decides nothing). Pairing does not sharpen the comparison, because B redraws its images at every seed: on the primary
cell the paired scores are uncorrelated ($r = -0.04$), the targeted arm is ahead on $6$ of $8$ seeds (exact sign-flip
$p = 0.29$), and the smallest margin at which the paired test would show equivalence is $\pm 0.0061$.}
\label{tab:paired}
\begin{center}
\scriptsize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lccc@{}}
\toprule
Cell & Welch 95\% CI & Paired 95\% CI & Paired TOST $p$ ($\pm0.005$) \\
\midrule
SINet, COD10K (primary) & $[-0.0020, +0.0067]$ & $[-0.0023, +0.0070]$ & $0.111$ \\
SINet, NC4K & $[-0.0033, +0.0040]$ & $[-0.0038, +0.0045]$ & $\mathbf{0.016}$ \\
SINet-v2, COD10K & $[-0.0067, +0.0045]$ & $[-0.0081, +0.0059]$ & $0.114$ \\
SINet-v2, NC4K & $[-0.0068, +0.0049]$ & $[-0.0077, +0.0058]$ & $0.100$ \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
(OUT / "table_cdr.tex").write_text(r"""%% Values: RL5B STUDENT_RESULTS/RESULT_TABLES/EXP02_SINet_results.md and EXP02_SINet_summary.json.
\begin{table}[h]
\revfloatcolor{RevShared}
\caption{The pre-registered dose-response experiment (SINet, $N = 1000$, $35$ new runs plus the eight-seed B runs).
$\Delta$ is each concentrated level's difference from the dispersed reference (cluster-uniform and random arms,
Boundary-IoU $0.3308$ at threshold $0.5$ on COD10K-test, the primary measure); the bar is $2\hat\sigma = 0.0193$
($\mathrm{df} = 24$). A level counts as an effect only if it clears the bar, at least four of its five random permutations
agree in sign, and the spread between permutations is smaller than the effect. Effective numbers of clusters are
nominal (quota) and delivered (nearest cluster centre of each selected render). The SINet-v2 replication was not run.}
\label{tab:cdr}
\begin{center}
\scriptsize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lccccccl@{}}
\toprule
Level & Clusters (nom./deliv.) & Runs & $\Delta$ B-IoU & $\times$\,bar & Perms agree & $\Delta S_\alpha$ & Verdict \\
\midrule
Dispersed (uniform, random) & $75$ / $50$ (random $43$) & $5 + 8$ & reference & & & & \\
Committed shape ($\atemp = 1.0$) & $30$ / $45$ & $5 \times 3$ & $-0.0005$ & $0.03$ & $2/5$ & $+0.0004$ & \\
Sharper ($\atemp = 0.758$) & $15$ / $41$ & $5 \times 3$ & $+0.0021$ & $0.11$ & $4/5$ & $+0.0015$ & not supported \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
(OUT / "table_cham_counts.tex").write_text(r"""%% Values: dypE STUDENT_RESULTS/RESULT_TABLES/AN-05_chameleon_pairs.csv and AN-05_cross_benchmark.csv
%% (released detectors only). Reconciliation script: tools/verify_numbers.py.
\begin{table}[h]
\revfloatcolor{RevC}
\caption{Every CHAMELEON count, reconciled ($76$ images). Training pool: COD10K-train and CAMO-train. ``No duplicate
found'' replaces ``clean'': the detectors find copies of the same photograph, not other photographs of a specimen.}
\label{tab:chamcount}
\begin{center}
\scriptsize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lr@{}}
\toprule
Training-pool partner, released detectors (Tier A $41$ + Tier B $9$; $44$ in COD10K-train) & $\mathbf{50}$ \\
No training-pool partner: unchecked at both tiers & $16$ \\
No training-pool partner after a Tier-A check of the dimension group & $10$ \\
\midrule
Re-encodes of COD10K-test images (all $16$ unchecked, $8$ of the $10$, and $8$ with a training-pool partner) & $32$ \\
In CAMO-250, the checkpoint-selection split ($3$ byte-identical, $1$ re-encoded) & $4$ \\
In NC4K & $0$ \\
\midrule
A duplicate found somewhere in COD10K or CAMO & $74$ \\
No duplicate found anywhere & $2$ \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
edit_file("appendix_coverage.tex", [
    (r"""Every real set covers the target near its own ceiling; both synthetic pools collapse, most sharply in
\texttt{clipL224}.""",
     r"""Every real set covers the target near its own ceiling; both synthetic pools collapse, most sharply in
\texttt{clipL224}. \revB{The values depend on $k$, but the ordering does not: at $k = 3, 5, 10, 20$ our renders cover
$0.07$--$0.48$, $0.13$--$0.54$, $0.25$--$0.63$ and $0.38$--$0.75$ of the target across the three spaces, against
$0.60$--$0.64$, $0.71$--$0.75$, $0.84$--$0.88$ and $0.95$--$0.97$ for the raw HKU-IS photographs the generator starts
from.}"""),
    (r"""A real-versus-synthetic classifier is not used as evidence,""",
     r"""\begin{revblock}{RevC}
\paragraph{Coverage of the selected sets.} The same estimator applied to the $1000$ injected renders of each arm
separates the arms that the probe's own coverage table did not: in \texttt{dinoL518}, the three concentrated selections
cover $0.62$--$0.64$ of the target, against $0.35$--$0.43$ for the eight random draws ($0.50$--$0.53$ against
$0.27$--$0.45$ in \texttt{dinoL224}; in \texttt{clipL224} the ranges overlap). Concentration therefore moves the
selected set closer to the target under this estimator, and trained accuracy does not follow. We give no interval,
because resampling foregrounds biases this estimator.
\end{revblock}

A real-versus-synthetic classifier is not used as evidence,"""),
], "appE-coverage-k-and-selections")
for f in ["table_tost_equivalence.tex", "table_subgroup_metrics.tex"]:
    if (OUT / f).exists():
        (OUT / f).unlink()           # superseded: tab:tost -> tab:ci_tost; 3-seed tab:boundary -> 8-seed version
print(f"OK: {len(LOG)} replacements applied")
(OUT.parent / "tools" / "integrate_log.txt").write_text("\n".join(LOG) + "\n")

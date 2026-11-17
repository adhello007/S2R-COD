# AN-01: manuscript claim and reproducibility audit

**Status: VERIFIED.** 33 claims are audited. The ledger is `RESULT_TABLES/AN-01_claim_ledger.csv`;
the proposed edits are in `DOC-01_edits.md` and `../manuscript_scope_edits.patch`.

## Which manuscript was audited

- **Supplied manuscript.** `S2R-COD/AD-PCHGS-250926.tex` (sha256 `84d3bf97…`) equals the committed
  `AD-PCHG-250926_Final.tex` (commit `09add3d`, 2026-09-25 23:16), plus two punctuation-only hunks in
  the AI-use statement (lines 509–510 and 518–519). No number, claim or label differs.
- **Bibliography.** `reference 1.bib` is byte-identical to the committed `reference.bib` (sha256
  `1a978102…`).
- **Compilation.** The supplied .tex compiled against its committed inputs from
  `rebuild/FinalPaper/AD-PCH-230926/`: 25 pages, 0 undefined references or citations. The main text
  ends on page 9, and the AI-use statement opens page 10.
- **The committed PDF is not the submission build.** `AD-PCHG-250926_FINAL.pdf` was compiled
  2026-09-25 17:22, six hours *before* the .tex was committed. Against the compiled .tex it differs in
  167 wording blocks, including the abstract. Its numeric tokens differ only in bibliography entries
  (DOIs, pages, volumes); every experimental number is identical.
- **Not verifiable locally:** whether the PDF uploaded to OpenReview is the build of this .tex. The
  corresponding author should compare it against the upload.

## Method

1. Every section, equation, table and figure label was read.
2. Every number was traced to a committed artifact. Where cheap, it was **re-derived from raw
   artifacts**:
   - every trained-campaign statistic (two independent implementations, TH-02);
   - the probe and effective-rank analysis (original code re-run, AN-02);
   - provenance and coverage (independent implementations, AN-03);
   - the CHAMELEON overlap (independent detector, AN-05).
3. A high-risk phrase search covered: "perfect", "no score of any quality", "changes nothing",
   "nothing moves", "the whole time", "without hedging", "every concentrat…", "Doesn't Help",
   "closed loop", "generaliz…", "proves".
4. Citations were checked. All 41 cited keys (main text and `\input` files) resolve, with 0 undefined in
   the compile, and every one was checked against the sentence it supports. Two minor imprecisions:
   CLIP is called self-supervised, and COD10K is cited only to the TPAMI paper (C-33). Two bib entries
   are never cited, which is harmless.
5. The anonymised repository (`anonymous.4open.science/r/AD-35F1/`) is live: published 2026-09-25
   08:59 UTC, expires 2027-03-25, downloads enabled. Its top level lists the trainer code, `Eval/`,
   `Src/`, `rebuild/`, `results/`, `Paper/`, `Snapshot/` and a separately written README. Ten of the
   sixteen top-level files match the submission commit in size, including `MyTrain.py`, `MyTest.py`
   and `CLS.py`. Blob hashes differ, as expected from anonymisation. Subfolders need a browser
   session, so their contents were not inspected.

## Findings, in order of consequence

**Corrections to statements of fact**
- **C-07, pre-registration timing for the oracle campaign.**
  - *Manuscript:* the oracle pre-registration was "committed before that campaign's first training
    run" (app:method; repeated in app:controls, the AI-use and reproducibility statements, and the
    pre-registration's own header).
  - *Git:* the first OR runs started 2026-09-18 10:46:09. The pre-registration's first commit,
    `a79886a`, is at 11:48:26, 62 minutes later. That commit is on no branch but is preserved by tag
    `prereg-or-fx-se-a79886a`. The on-branch copy `28cfd84` differs only by the appended, dated
    Addendum A1.
  - *What protects the result:* no OR score existed until 18:23, and the rule text was never edited.
  - *FX and SE* were committed before their runs, as stated.
  - **This is the one statement of fact in the paper that is wrong as written.** It should be
    corrected in the revision rather than defended.
- **C-31, SE commit reference.** The appendix records the seed-expansion rule "at `b755aa9`". That commit
  (2026-09-13) does not contain the SE pre-registration. The file was first committed in `a79886a` on
  2026-09-18, two days before SE's first run. The ordering claim holds; only the commit reference is
  wrong.
- **C-22, CHAMELEON count.** The paper's 50/76 is a floor and stands. An independent detector
  recovers all 41 Tier-A images. One further candidate it flagged (`animal-54`) is not claimed
  (dropped by author decision, 2026-11-17).
- **C-32, a provenance commit at risk.** The manuscript's pointer `c2114af` (AC and PC rules) is
  correct: it was committed 5 minutes before the first PC run. But it is on no branch and has no tag,
  so it can be garbage-collected. Tagging it, as `a79886a` was tagged, is the author's decision.
- **C-27, prose defect.** The punctuation edit in the supplied .tex leaves one AI-use sentence
  ungrammatical.

**Overstated or mis-scoped interpretations** (the core of Reviewer Caus's concerns)
- **C-06.** "No score of any quality helped here" holds only *at C10's fixed quota shape*.
  CORACLE permuted C10's multiset. QA-01 is exactly this gap, and EXP-01 tests other shapes.
- **C-05.** "A perfect score … changes nothing" and "a perfect-score oracle" overstate a 3-seed,
  within-noise result. The oracle was also built from one architecture's errors.
- **C-04 and C-23.**
  - *The paper says:* "The probe was detecting the concentration the whole time" and "only removing
    the unevenness … collapses it".
  - *New evidence:* a perfectly flat quota with the same centroid-proximity selector is still
    separable from random (d ≈ 0.5) and has lower effective rank. The most concentrated shuffle keeps
    near-random rank (TH-01 §5, `AN-02_shape_geometry.csv`). The separation belongs to the matched,
    concentrated selection.
  - *What stands:* the direction of the uncertainty signal still adds nothing measurable (+0.0073 d).
- **C-01, C-02, C-24, C-25.** The title, abstract and conclusion state the null without its pipeline
  scope (offline LAKE-RED fixed-foreground pool, two-round S2R-COD, SINet/SINet-v2, COD10K/NC4K). The
  discussion already says "nothing here says closed-loop generation cannot work". The headline
  sentences should say the same.
- **C-03.** "Five controls show the null is not an artifact": each control closes one named artifact.
  Say which.
- **C-12 and C-20.** Both are correct as numbers but omit their definitions. Effective rank is the
  participation ratio, and its decrease is empirical, not implied by concentration (TH-01 §5).
  Coverage is k-NN recall at k = 5, and it is k-dependent: renders span 0.07–0.75 over k = 3–20, always
  below the raw input.

**Supported and verified as written**
- C-08 to C-11, C-13, C-14: the trained null and its intervals and equivalence tests.
- C-16 to C-19: cluster quality, CAMO enrichment, error correlations, 8,885 traced objects.
- C-26, C-28, C-30.
- C-15 (boundary metrics) and C-29 (the 0.7030 baseline) are supported by committed artifacts but were
  not re-derived here. They are labelled historical.

## What the claim audit means for the rebuttal

The empirical record holds up: every trained number re-derives exactly. The rebuttal should:
1. concede the oracle-shape scope (C-06/C-05) and answer it with EXP-01;
2. correct the pre-registration timing (C-07) unprompted;
3. narrow the concentration attribution (C-04/C-23) in the direction the reviewer's CW-01 pushes;
4. state the pipeline scope in the title, abstract and conclusion (C-01/C-02/C-25).

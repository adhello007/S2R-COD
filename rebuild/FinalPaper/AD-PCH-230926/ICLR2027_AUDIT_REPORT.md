# ICLR 2027 Pre-Submission Audit Report

**Manuscript:** *Concentration, Not Uncertainty: Why Targeted Synthetic Data Doesn't Help Camouflaged Object Detection*
**Entry file:** `main.tex` (inputs: `math_commands.tex`, `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`, `appendix_tables.tex`; bibliography `reference.bib`, style `iclr2027_conference.sty/.bst`)
**Audit date:** 2026-09-23
**Companion reports:** `SYMBOL_CONSISTENCY_REPORT.md`, `EQUATION_AUDIT_REPORT.md`

Line numbers refer to the **post-audit** `main.tex` unless marked "orig". Pre-audit copies of every edited file were kept outside the project for the before/after list in §16.

---

## 0. Revision Round 2: repository-informed fixes (supersedes the statuses below where they conflict)

> **Reading note.** §§1–17 below are the round-1 report. Their line numbers and appendix letters refer to the round-1 manuscript, which is preserved in `AD-P-230926_ICLR2027_audited_round1.zip`. Round 2 added App. E (coverage), so the round-1 App. E/F/G are now **F/G/H**. Where §§1–17 conflict with this section or the §18 register, this section and §18 are current.

After the first audit the authors supplied the experiment repository (`s2r-cod-supplement.zip`). Every issue that the round-1 audit left open for lack of data was then checked against the code and the committed artifacts, and fixed where the repository settled it. The final issue register (§18) reflects this round.

### 0.1 Corrections to my round-1 report

1. **M1's cause is now known and verified.** `softmax_alloc` (`rebuild/C1/c1_targeted_vs_random.py:75`) divides the cluster scores by their population standard deviation across clusters before the τ-softmax, and quotas come from largest-remainder rounding. Running the repo's functions on the committed scores reproduces **all 75 quotas exactly**, with s_e = 0.01012. That matches the ≈0.0101 I inferred in round 1. The paper was incomplete, not wrong.
2. **The 90.2 % figure is correct.** It is the committed `top2_funded_camo_share` in `diag_clusters.json`. My round-1 recomputation (Mo5) used the wrong definition. I withdraw that finding.
3. **Numbers I called "untraceable" all have committed sources:**

   | Number | Source |
   |---|---|
   | +0.8553 / +0.4276 | `B1_RESULTS.md`: per-cluster Spearman at k = 75, mean over 10 seeds |
   | 0.9928 | `A3_RESULTS.md`: identical images re-encoded at JPEG-30, clipL224 |
   | 8885 | `D1_RESULTS.md` |
   | 0.634 | `C1_RESULTS.md`: mean effective-rank ratio over 20 cells |
   | Coverage 0.13–0.54 and 0.71–0.75 | `a3_coverage.csv` |
   | "a fifth" | 0.2046 (`results.md` §5.2) |
   | 103 runs | ABC 24 + T2 12 + PC 3 + OR 6 + FX 18 + SE 40 |

4. **"Twenty" vs "four" cells (Mo11) was a presentation gap, not a contradiction.** Fig. 2a averages the four cells at budget N = 250 (`figs/make_fig1.py`, `PEAK_B = 250`). The text's twenty cells span all budgets.
5. **Regression I introduced in round 1.** My `% AUDIT FIX` comment in the Reproducibility statement shared a line with the next sentence, so "The contamination detector is released with an" was commented out of the PDF. It is **fixed**, and every comment line was re-checked.

### 0.2 New findings from the repository

| ID | Severity | Finding | Status |
|---|---|---|---|
| N1 | **Major** | The TOST claim was false, not just overstated. Of the 16 eight-seed gaps, the 5 that reach equivalence are four direction contrasts **and C10−B on SINet·NC4K (p = 0.0084)**. So "they are the direction contrasts … the targeting-versus-random gap does not reject" is wrong, and the claimed "asymmetry" does not exist: 4 of 12 direction contrasts reject vs 1 of 4 targeting-vs-random gaps. | **Fixed.** §3.2 and §3.1 reworded; Table 5 now shows all 16 rows, regenerated from `se/abc_metrics.csv`; footnote corrected in both the `.tex` and the generator. |
| N2 | **Major** | The abstract and intro said reversing the signal "reproduces the effect" alongside the geometry result. The C1 geometry experiment has **no reversed arm** (its arms are targeted, shuffled, random_centroid, random_direction and random_vs_random). The reversal evidence is the post-hoc SINet boundary metric only. | **Fixed.** Now reads "on boundary accuracy so does one that reverses the uncertainty signal." |
| N3 | Moderate | The released `CLEAN_PROTOCOL.md` (both copies, `rebuild/D2_reaudit/` and `release/`) still recommends reporting CHAMELEON "on the 35-image uncontaminated subset". The paper says this subset is now 10 images and must not be used. | **Fixed in round 3** (§0.5). |
| N4 | **Critical if an author's handle** | The supplement's `LICENSE` reads "Copyright (c) 2025 Muscape". It may be inherited from the upstream S2R-COD code. If "Muscape" identifies an author, it is a desk-rejection risk. | **Closed in round 3**: the README (l.226–227) documents it as the upstream MIT notice; not an author name (§0.5). |
| N5 | Moderate | 73 commit-hash references in the supplement (e.g. `results.md`: "at commit `de2c845`"). Removing the paper's five hashes alone would not help. | **Accepted in round 3**: the repository is private, so the hashes cannot be looked up (§0.5). |
| N6 | Low | `Eval/metrics.py` contains a third-party e-mail from upstream code. Log hostnames are already redacted (`<author-given hostname>`). | Informational |
| N8 | Moderate | `rebuild/FinalPaper/results.md` §7 still lists "Seed expansion … **NOT RUN**", while its §1 and §6 say SE is COMPLETE. The Reproducibility statement now sends reviewers to this file. | **Fixed in round 3** (§0.5). |
| N9 | Moderate | `rebuild/DIAG/diag_emit.py` writes `table_tost_equivalence.tex`, `table_cluster_composition.tex` and `table_subgroup_metrics.tex` into the paper folder with **stale content**: the 3-seed TOST table, the old `B`/`es_j` notation, and old captions. Re-running it would silently overwrite three corrected paper tables. | **Fixed in round 3** (§0.5). |
| N7 | Minor | `release/chameleon_contaminated.json` stores the 41 Tier-A pairs under `contaminated` and the 9 Tier-B pairs under `tier_b`. This is consistent with the 50, but a user reading only `contaminated` will count 41. | Suggestion: document it in the release README |

### 0.3 What round 2 changed in the manuscript

**Main text** (every change checked against the page budget; the main text still ends on p. 9 and p. 10 opens with the AI-use statement):
- **M1:** §2 now says the softmax is taken over scores "in units of their across-cluster standard deviation". The full rule is App. B Eq. (2), with largest-remainder quotas, and states that it reproduces all 75 quotas.
- **M2:** §3.1 now says the √(8/3) projection was a pre-registration error (σ̂ is a per-run spread). App. C's paragraph was rewritten accordingly.
- **M5/N1:** TOST passage rewritten (§3.2) and §3.1's "asymmetry it reveals" pointer removed.
- **M6:** contribution 1 and the §3.2 opener now say "shown in geometry, supported post hoc on one architecture, consistent with eight seeds".
- **M7:** "under whole-image aggregation" added.
- **N2:** abstract and intro reversal wording corrected.
- **Mo8:** CORACLE now "re-assigns the quotas by each cluster's true endpoint error".
- **Mo9:** "an ensemble and predictive entropy".
- **Mo12:** "the reference effect of Section 1.1".
- **Mi7:** "the four nulls".
- **Mi11:** "A0, which appends nothing".
- **Mo15:** "Nor do we recommend …" (the self-reference is removed).
- **Mo10:** Discussion AUC now points to App. E.
- **Mi10:** BCE expanded.
- Coverage metric defined ("k-NN recall, App. E").
- **Fig. 2 caption:** "the four cells at budget N = 250".
- §3.3 cites Table 11.
- The title is **unchanged** (see M8).

**Appendix:**
- **App. B:**
  - New "The allocation rule" paragraph with Eq. (2).
  - Budget renamed B → N (Mo19).
  - MAE and E-measure expanded; MAE on CAMO-250 is the checkpoint-selection metric (Mo18).
  - EMA expanded.
  - ES defined, with both terms stated as per-pixel means and the teacher as the BCE target (Mo20, from `Src/utils/tool.py`).
  - df = 4 for the two-arm positive control (Mo1, from `pc_verdict.json`).
  - New "Campaign codes and verdicts" paragraph defining ABC/SE/OR/FX/PC/T2, MT and DETECTED/NOT DETECTED, taken from `PREREGISTRATION_PC.md` (Mo6, Mo7).
- **App. C:** projection paragraph corrected (M2); the "89 %" replaced with "their whole base pool and roughly half of their injected images" (Mo3).
- **App. D:** the orphaned cluster-composition table is now included as Table 11 (Mo5, safe now that M1 is documented). `\clearpage` keeps Tables 6–11 inside App. D.
- **New App. E (Coverage of the Target Manifold, and Why AUC Is Not Used):** generated from `a3_coverage.csv` and `a3_probe_table.csv`. It supports the §3.3 coverage numbers and the Discussion's 0.9928 claim, and cites Kynkäänniemi et al. (2019).
- **App. F (formerly E):** the animal-7 sentence was reworded, and the 525–1174 band is now explained as a Tier-A description, not an acceptance rule (Mo4).
- **App. H (formerly G):** "twenty-four runs at the committed seeds (twelve per architecture)" (Mo2, from `SE_RESULTS.md`).

**Statements:**
- AI-use: "the verdict bands" (the ABC pre-registration defines three; the PC pre-registration defines two); "each table and figure caption names its source".
- Reproducibility: per-run metrics for **all 103 runs** are in the supplement (`rebuild/FinalPaper/results.md`, verified: 200 campaign rows + 6 PC rows).

**Bibliography:**
- `cheng2021boundary` changed to `@inproceedings`.
- `kynkaanniemi2019improved` added. I wrote this entry from memory (NeurIPS 2019), so **verify it manually**.

**Tables regenerated from repository data, not hand-edited:**
- `figs/make_appendix_tables.py` reproduces `appendix_tables.tex` **byte-for-byte**. Every value in Tables 6–10 was unchanged; only two formatting drifts were synced into the script, plus Table 7's `tabcolsep` 1.5 pt, which fixes its 6.1 pt overflow.
- `figs/make_tost_table.py` now emits both endpoints. All 16 rows match `results.md` §4 exactly.
- New `figs/make_coverage_table.py` reproduces `appendix_coverage.tex` exactly.
- Table 11 values were checked against `diag_clusters.json`: all match.

### 0.3a Numbers upgraded from "cannot verify" to verified (recomputed from the ledger's per-run rows)

- **Table 4, all 16 rows (ABC, SE, OR, FX × 4 cells):** Δ, bar, ×bar and sign all reproduce. The sign column counts seeds agreeing with the sign of the mean Δ (the committed `abc_verdict.json` convention). That is why SINet-v2 FX shows 1/3 where two seeds point the other way. The convention is correct but worth stating in the caption.
- **Table 2 (boundary metrics), all 6 rows:** bars, Δs and sign counts match `results.md` §5.3.
- **App. C eight-seed per-arm SDs:** 0.00251, 0.00489, 0.00278, 0.00302 all reproduce.
- **Table 5 (TOST, 16 rows)** and **Tables 6–11:** regenerated from the repository (§0.3).
- **App. B training loss:** a = 0.9, b = 0.3, c = 0.5 are confirmed in `b1_score_meta.json` and the `MyTrain.py:255` task override. The acquisition score uses unweighted BCE. The *training* consistency loss uses saliency-weighted BCE, which is now stated in App. B.

### 0.5 Round 3: the supplement fixes and the reproducibility package

**Deliverable: `ICLR2027_supplementary_material.zip`.** This is the reviewer-facing supplement. It replaces `s2r-cod-supplement.zip`, which is kept unmodified as the original. It is about 43 MB; check the size against the ICLR 2027 author guide. The package contains the corrected supplement plus:

- **`verify_paper.py`.** One command, no data, no GPU, and it needs only numpy and scipy. It re-runs every table generator and byte-compares the output with the paper's tables. It recomputes all 16 decisive-gap verdicts and the positive control from the per-run CSVs. It reproduces all 75 allocation quotas. **All checks pass from a fresh extraction.**
- **`Paper/figs/`.** Holds the paper's generators (`make_appendix_tables.py`, `make_tost_table.py`, `make_coverage_table.py`, `make_fig1.py`, `make_fig2.py`, `make_fig_arms.py`). They now find the repository by searching upward for `rebuild/` and write UTF-8 with LF line endings. `Paper/` is also `diag_emit.py`'s output folder, so the TOST caption's `figs/make_tost_table.py` resolves.
- **`paper_reference/`.** The five generated tables exactly as printed, plus the four figure PDFs for visual comparison.
- **README.** The title now matches the paper. A new "Check the paper in one command" section maps every paper table, figure and equation to its generator and inputs, and says which elements need the datasets (Fig. 3 only).

**Supplement fixes:**
- `CLEAN_PROTOCOL.md` (N3): the 35-image recommendation is withdrawn in favour of the 10-image finding. The `release/` copy is re-synced, as the pipeline itself does.
- `make_results.py` and `results.md` (N8): §7 corrected, and output made portable (UTF-8, `/` paths). It regenerates byte-identically.
- `diag_emit.py` (N9): stale TOST emission removed, emitters mirror the paper, LF output, lazy matplotlib.
- `NAVIGATION.md` §0 and the README: the 3-seed `diag_tost.py` is no longer called "the paper's TOST table".
- `rebuild/ABC/driver.pid` removed.

**Checks run on the final ZIP, from a fresh extraction:**
- `verify_paper.py`: ALL CHECKS PASSED.
- NAVIGATION §0's four commands all run. The detector self-test passes; `ac_measure.py` returns AREA-ROBUST at 4.92e-05; `make_results.py` regenerates `results.md` byte-identically.
- Every `\texttt{}` path and log-line reference in the paper resolves in the package (`REBUILD_LOG.txt:922/2550/2612` point at EXP B1 #3, T2C and AC; EXP ABC #3 and EXP T2 #3 exist).
- Anonymity scan (paths, users, hosts, IPs, e-mails, accounts, conda envs, GPU serials, PNG text chunks): **no identifying information**. The only hits are upstream third-party credits (an e-mail and GitHub links in inherited code), upstream dataset-download links quoted from the S2R-COD README, and version numbers.

**Kept out of the supplement:** the audit reports, `_preaudit/`, `_audit_logs/` and `main.tex`, whose header comments are internal.

### 0.4 Still open after round 2

- **M8 (title).** Left unchanged, as an author decision. A scope-matched alternative: *"Concentration, Not Uncertainty: Why Targeted Synthetic Data Did Not Help Camouflaged Object Detection"*.
- **Supplement items:** N3, N8 and N9 are fixed in round 3 and N4 is closed, as described in §0.5. N5 (commit hashes) is accepted, because the repository is private.
- **Mo14:** the paper's five commit hashes in App. B. Moot unless N5 is addressed.
- **Mo17:** Figure 3's overlapping row labels. The source images are not in the supplement, so `make_fig2.py` cannot be re-run here.
- **Mi14, Mi15, Mi16:** notation overload of σ/∇, the `\itemsep` tweak, internal paths in captions. All cosmetic.
- **Mi17:** manually verify the 2025 bib entries and the added Kynkäänniemi entry.
- **AUTHOR CHECK 1–3:** AI-use statement, dataset licences, repository link.
- **Page budget:** zero spare lines remain in §§1–5.

---

## 1. Executive Summary

| Dimension | Assessment |
|---|---|
| Overall technical consistency | **Good.** Every number that can be recomputed from data in the manuscript (Table 9/10 per-run metrics) reproduces exactly: all four ABC cells of Tables 1/4, all per-arm SDs, the 92.7 % A0 variance share, the 0.0055 falsification bar, the 3-seed Welch interval \[−0.0035, +0.0136\] at df ≈ 2.76, the positive-control gap and ratio, and the Table 2 boundary ratios. |
| Mathematical reliability | **One real gap and one real error.** (a) The allocation rule as written (τ = 1 softmax on raw cluster scores) cannot produce the reported quotas (**M1**). (b) The √(8/3) "projection" contradicts the paper's own 2σ̂ definition (**M2**). |
| Notation quality | Fair. There is one displayed equation. The allocation step is described only in words and relies on symbols (`p_j`) that are defined only in the appendix. `B`, `σ` and `p` are each overloaded. |
| Theorem/proof reliability | **N/A.** The manuscript has no theorems, lemmas, propositions or proofs. |
| Experiment/claim consistency | Mostly careful and self-qualifying. Several claims are stronger than their evidence: **M5** (TOST "direction is equivalent"), **M6** (contribution 1), **M7** (signal-generality scope), **M8** (title). |
| LaTeX status | Compiles cleanly: 0 errors, 0 undefined references or citations, 0 duplicate labels. The two layout defects found were fixed (**C1**, **C2**). Remaining overfull boxes are cosmetic and in the appendix. |
| ICLR compliance | Main text is now **9 pages** (pp. 1–9). Appendix comes after the references. Anonymous header is on. AI-use, Ethics and Reproducibility statements are all present, each with an `AUTHOR CHECK` item that still needs confirming. |
| Anonymity | No names, affiliations, URLs or usernames in the sources, the PDF or the figure metadata. Two **moderate** risks remain: commit hashes and "our own earlier recommendation" (§12). The LaTeX build logs contain the Windows username; never ship them (the ZIP copies are redacted). |
| **Submission readiness** | Round 1: **REQUIRES MODERATE REVISION**. Round 2: ready after minor corrections. **After round 3: READY**, subject to the author decisions in §0.4: the title, Fig. 3's labels, and the AUTHOR CHECK items. |

**Why this classification.** The core evidence is sound and reproduces from the paper's own data. Nothing found invalidates the central null. But four things need author decisions before submission:
- The allocation method is under-specified (M1). This is detectable from the project sources, specifically the orphaned `table_cluster_composition.tex`. It is not yet detectable from the PDF, but it will be as soon as that table or code is released.
- One stated statistical expectation is wrong (M2).
- Several headline claims are stronger than their evidence (M5–M8).
- Several reported numbers contradict each other (Mo1–Mo5).

None of these is a quick mechanical fix, and none can be settled without the authors' data.

> **Regression disclosure.** Earlier in this session I added a *Conclusion* section at the user's request and reported a "clean build." That build had already pushed the main text **2 lines onto page 10**, over the 9-page limit. My earlier check verified compilation but not page count, so I missed it. It is fixed (C1), and the fix is part of this audit.

---

## 2. Critical Issues

| ID | File | Section | Line(s) | Issue | Severity | Confidence | Status / Fix |
|---|---|---|---|---|---|---|---|
| C1 | main.tex | §5 Conclusion | 537–545 | The main text overflowed onto p. 10: the Conclusion body ran 2 lines past p. 9. **I caused this** by adding the Conclusion earlier in the session. | Critical (page limit) | High | **FIXED.** The Conclusion is shortened to 7 lines. Its content is kept, and its ambiguous phrase "two-thirds training data under an exact-byte check" is corrected. Verified: p. 9 ends with the Conclusion and p. 10 opens with "AI USE STATEMENT". |
| C2 | appendix_tables.tex (and generator) | App. D, Table 9 | orig 97–190 | The per-run table (78 rows) was "Float too large for page by 233.7 pt". **16 NC4K rows, from SINetv2 A0 45 to SINetv2 CSHUF 45, were cut off the page** in the PDF. | Critical (data silently missing) | High | **FIXED.** Split programmatically into Table 9 (COD10K) and Table 10 (NC4K), with every row copied verbatim. 156/156 values verified present in the PDF text. The warning is gone. `figs/make_appendix_tables.py` got the identical change. |

No anonymity violation or theorem error rises to Critical.

---

## 3. Equation and Mathematical Issues

### M1: The allocation rule as described cannot produce the reported allocation (Major)

**Location:** §2 "The allocation, in four stages", step (iii), lines 216–218; App. B "Allocation sweeps", lines 782–785; data in `table_cluster_composition.tex`. That table is **orphaned**: it is never `\input`, but the main text quotes its numbers at lines 452–455.

**Original**
```latex
The budget is spread by a temperature softmax over the cluster scores, at temperature $\atemp = 1.0$
```

**Problem.** The cluster scores `es_j` of the ten most-funded clusters lie between 0.0471 and 0.0707.
- A softmax with τ = 1 over values that close is almost uniform: exp(0.0707 − 0.0471) = **1.024**.
- The reported quotas are 194 vs 19, a ratio of **10.2**.

**Verification.** Regressing log(quota) on `es_j` over the 10 tabulated clusters gives r = 0.9999 with slope 98.8. The allocation therefore *is* a softmax, but with an effective temperature of **≈ 0.0101 in raw-score units**, about 100× smaller than τ = 1. Some unstated normalization is being applied, for example standardising the scores before the softmax. The App. B definition of the τ grid's "uniform" end (TV < 0.01) implies the same thing: on raw scores, τ = 1 would already be close to that degenerate uniform end.

**Recommended correction (author must supply the actual normalization):**
```latex
The budget is spread by a temperature softmax over the \emph{<normalised>} cluster scores,
$p_j \propto \exp(\tilde{e}_j/\atemp)$ with $\tilde{e}_j = <\text{normalisation of } \mathrm{ES}_j>$, at $\atemp = 1.0$
```

**Severity:** Major. **Confidence:** High that the text is incomplete or incorrect; **Low** about what the missing normalization is. The evidence comes from the orphaned table, so check it against the code.

### M2: The √(8/3) projection contradicts the 2σ̂ rule's own definition (Major)

**Location:** §3.1 lines 311–313; App. C lines 884–891.

**Original**
```latex
projected that eight seeds would tighten the bar by $\sqrt{8/3} \approx 1.63\times$, \emph{if the per-arm spreads stayed as measured}.
```

**Problem.** §2 defines σ̂ as the *pooled within-arm standard deviation* of per-run S_α. That estimates the spread of a single run. It does not shrink as seeds are added; only its *precision* improves.

**Verification.** All three bars reproduce as 2 × pooled per-run SD with no 1/√n factor:
- 0.0179 from A0, A2, B and C10 at 3 seeds
- 0.0055 from B, C10, CSHUF and CINV
- 0.0069 from the paper's 8-seed per-arm SDs

So if the spreads "stayed as measured", the bar would stay at **0.0055**, not fall to 0.0034. The 0.0034 figure applies √(8/3) scaling, which fits a *standard error of a mean difference*, not this rule. The paper's broader lesson ("did not buy a smaller bar, it bought a trustworthy one") is correct; the projection it is contrasted with is not.

**Recommended correction:** state that the pre-registered projection was itself an error, because a 2σ̂ bar on per-run spread does not scale with n. Or, if the pre-registration meant a standard-error bar, say so and explain why the verdict rule uses per-run SD. Do not keep "if the per-arm spreads stayed as measured".

**Severity:** Major. **Confidence:** High.

### M3: "which at three seeds it did not" contradicted by the paper's own numbers (Major, FIXED)

**Location:** §3.1 line 315 (orig 314–315).

**Original**
```latex
the gap now sits inside even the tightest bar this project has measured, $0.0055$, which at three seeds it did not.
```

**Verification:** the 3-seed gap is +0.00503 (recomputed from Table 9), which is **0.91×** the 0.00553 bar, so it was already inside. Separately, "tightest bar this project has measured" is false across cells: OR's SINet·NC4K bar is 0.0047 (Table 4).

**Applied correction** (marked with `% AUDIT FIX`):
```latex
the gap now sits inside even the tightest bar measured on this cell, $0.0055$.
```

**Severity:** Major. **Confidence:** High.

### Mo1: Positive-control bar reproduces only as a two-arm pool at df = 4 (Moderate)

**Verification.** From Table 9, the PC bar of 0.0060 and the ratio of 3.31× reproduce **only** when σ̂ is pooled over {C10, MT} (df = 4). Every three-arm pool gives a different bar:

| Pool | Bar | Ratio |
|---|---|---|
| {B, C10, MT} | 0.0053 | 3.73× |
| {C10, CINV, MT} | 0.0059 | 3.36× |

App. B's "Degrees of freedom" paragraph (line 793ff) lists only df = 8, 6 and 28.

**Recommendation:** add "4 for the two-arm positive control" to that paragraph, or correct the PC bar. **Confidence:** Medium-High.

### Mo2 – Mo5: see §8 (numerical)

---

## 4. Symbol and Notation Consistency

The full inventory is in `SYMBOL_CONSISTENCY_REPORT.md`. Conflicts:

| Symbol | Meaning | First Definition | Other Uses | Status |
|---|---|---|---|---|
| `B` | Random-allocation arm | §2, l. 226 | Generation **budget** `B ∈ {250,…,4447}`, `B = 1000` (App. B l. 782–785); "% of B" (orphan table) | **Conflict.** Rename the budget (e.g. `N_{\text{gen}}`) or the arm (`RAND`). |
| `σ` / `σ̂` | Sigmoid (Eq. 1) / pooled per-run SD (§2) | l. 212 / l. 251 | Throughout | Overloaded but distinguished by the hat. Acceptable; consider `\operatorname{sig}` for the sigmoid. |
| `p` | Allocation share `p_j` (App. B only) | l. 784 (appendix only) | TOST *p*-values (§3.2, Table 5) | Minor overload. `p_j` is **never defined** in the main text. |
| `∇` | Sobel gradient **magnitude** (Eq. 1) | l. 212 | none | Non-standard: `∇` usually denotes a gradient vector. Define `G(\cdot)` or write `|\nabla\cdot|`. |
| `ES` vs `es_j` | Per-image score / cluster score | Eq. 1 / orphan table | none | Acronym ES is never expanded. The cluster-score notation appears only in the orphaned table. |
| `α` | S-measure weight 0.5 | l. 136/252 | none | Consistent. The temperature was already moved to `τ` via `\atemp`, and `\atemp` is used consistently at l. 218, 782, 784 and 785. |

---

## 5. Undefined Symbols and Acronyms

| Item | Where first used | Issue |
|---|---|---|
| **ES** | Eq. 1 (l. 208) | Never expanded. |
| `p_j` | App. B l. 784 | Allocation share. Never defined; the main text gives the softmax only in words. |
| **DETECTED** (verdict) | Table 1 (l. 302) | Never defined. §2 defines three bands, and the AI-use statement (l. 582) says "four verdict bands". |
| **ABC, SE, OR, FX, PC** | Table 1 row labels | Campaign codes never introduced in the main text. SE = "seed expansion" and FX = "unpinned schedule" can only be inferred. |
| **MT** | Table 1 (l. 302) | "mean-teacher baseline" (l. 342) is never tied to the code MT. |
| **C10**, **C10FX/BFX** | §2 l. 227; Table 1 | Neither the "10" nor the FX suffix is explained. |
| MAE, BCE, ARI, EMA, IoU | l. 787, 209, App. D, App. B, Table 2 | Not expanded (MAE and IoU are standard; BCE and EMA should be expanded). |
| TOST | §3.2 l. 398 | Not expanded in the main text (**now expanded and cited in the Table 5 caption**). |
| COD | App. A l. 658 | "COD" is used without expansion; the main text always writes it out. |
| `E_φ` | App. B l. 788 | E-measure symbol never defined (cited in App. A only as "enhanced-alignment E-measure"). |
| "padded / unpadded arm" | §3.3 l. 470–472 | Undefined (it means A0 vs. A2/B/C10). |
| effective-rank ratio | §3.2 l. 385 | A ratio of *what* to *what* is not stated. |
| "reach 0.13 to 0.54 of the real target distribution" | §3.3 l. 467 | Metric undefined. |
| `H`, `I` (homography) | App. E l. 978 | Implicit; acceptable in context. |

---

## 6. Theorem and Proof Audit

| Result | Assumptions Adequate? | Proof Valid? | Claim Strength Correct? | Issues |
|---|---|---|---|---|
| none | N/A | N/A | N/A | The manuscript has **no** theorems, lemmas, propositions, corollaries or proofs. The formal content is statistical, and is audited in §§3, 8 and 9. |

---

## 7. Algorithm–Equation Consistency

There are no algorithm or pseudocode environments. The "four-stage allocation" (§2) is the de facto algorithm:

| Stage | Text | Consistency |
|---|---|---|
| (i) k-means, k = 75, on L2-normalised self-supervised embeddings | §2 l. 202–203 | Consistent with Table 6: the bold `dinoL518` optimum is at k = 75 with silhouette 0.1600, matching §3.3. |
| (ii) per-image ES (Eq. 1), cluster mean | l. 207–214 | Consistent. `a = 0.9` and `b = 0.3` are in App. B. |
| (iii) softmax at τ = 1.0 | l. 216–218 | **Inconsistent with the reported quotas (M1).** |
| (iv) nearest foregrounds to the funded centroid | l. 219–220 | Consistent with App. B ("grey-masked cutout"). |
| CORACLE | §2 l. 235: "replaces the score with each cluster's true endpoint error" | **Inconsistent** with App. G (l. 1035–1037) and Fig. 1, which describe it as *re-assigning the committed quotas by the rank* of true error, a shape-preserving permutation. Replacing the score before the softmax would change the shape. Reword §2 to match App. G (**Mo8**). |
| Steps per epoch | l. 333–334; App. B l. 761–766 | **Verified:** ⌈4040/16⌉ = 253, ⌈4040/32⌉ = 127, ⌈5447/16⌉ = 341, ⌈5447/32⌉ = 171; 341/253 = 1.35. |
| Verdict rule | §2 l. 251–257 | Consistent with every bar that can be recomputed. |

---

## 8. Numerical and Experimental Consistency

### Verified (recomputed from Table 9/10 or by arithmetic)

**Tables 1 and 4 (ABC campaign):**
- Every Δ, bar, ×bar ratio and sign count in all four cells.
- For example, SINet·COD10K: Δ = +0.0050, bar 0.0179, 0.28×, 3/3.

**§3 and App. C statistics:**
- Per-arm SDs: A0 0.01727, A2 0.00193, B 0.00181, C10 0.00406, CSHUF 0.00166, CINV 0.00285.
- A0 contributes 92.7 % of the pooled variance.
- The falsification bar is 0.0055.
- The SE bar of 0.0069 follows from the stated 8-seed SDs.
- The positive control: Δ = +0.0197 at 3.31×.
- The 3-seed Welch 95 % CI is \[−0.0035, +0.0136\] at df = 2.76.
- 0.0142 / 0.0067 = 2.12, so "more than a factor of two" holds.

**Table 2 ratios:** 1.37× and 1.34×.

**Table 5 (TOST):** every "smallest δ" is consistent with |Δ| + t₀.₉₅·SE, and the bold marks match p < 0.05. The generator's `welch_tost` is a correct TOST implementation.

**Tables 7 and 8:**
- Every PASS/FAIL and every ordering count (8/8, 7/8, 6/8, 2/8) is correct.
- "Raises ρ(1−S_α) in every row" holds for all 8 rows.

**Counts and percentages:** 50/76 = 65.8 %; 50 + 16 + 10 = 76; 1000/4040 = 24.8 %; 0.515/0.248 = 2.08×; 1000/5447 = 18.4 %; 18.4 % × 0.48 = 8.8 %.

**Run total:** 103 is consistent with ABC 24 + T2 12 + PC 3 + SE 40 + (OR + FX) 24. The OR/FX split cannot be verified.

### Inconsistencies

| ID | Location | Issue | Confidence |
|---|---|---|---|
| **M4** | Reproducibility Statement (orig l. 624); Table 9 caption | Claimed "per-run metrics for **all 103** training runs" and "every training run in this work". The appendix tabulates **39** runs. **FIXED** (both now say 39). The SE, OR and FX per-run metrics remain absent from the paper: author decision. | High |
| Mo2 | App. G l. 1060 | "The **twelve** runs at the committed seeds are re-scored." SE is 4 arms × 8 seeds × 2 architectures = 64 = 40 trained + **24** re-scored. Possibly "twelve per architecture". | Medium |
| Mo3 | App. C l. 918 | "two arms that share **89 %** of their training data." With 452–511 of 1000 injected images differing in a 5447-pair pool, the shared fraction is **90.6–91.7 %**. | Medium |
| Mo4 | App. E l. 1002 | "animal-7 was the **only** candidate below the calibration band of 525–1174 inliers." The sentence is false: animal-72 (396) and animal-43 (263) are also below 525. **Wording error only.** The band describes same-dimension Tier-A positives and is not an acceptance rule. Acceptance uses the operating point of 20 plus the residual check, and rescaled copies (scale 6.36 and 0.53) naturally yield fewer inliers. Suggested rewording: "the only candidate near the operating point". | High |
| Mo5 | Orphan `table_cluster_composition.tex` | Never `\input`, yet §3.3 quotes its numbers. Its "two largest quotas … are **90.2 %** CAMO" does not reproduce from its own rows: budget-weighted 91.0 %, member-weighted 87.3 %. | Medium |
| Mo11 | §3.2 l. 382 vs Fig. 2 caption | The text pairs "across **twenty** cells"; the Fig. 2 caption says "means over **four** cells". These are possibly different analyses, but the connection is not stated. | Medium |
| Mi5 | App. C orig l. 916 | "triples the degrees of freedom" (8 → 28 = 3.5×). **FIXED.** | High |
| Mi4 | App. E orig l. 977 | "to three decimals (5.512 → 5.514)". **FIXED** to "to within 0.002". | High |
| Mi3 | Table 6 caption | "`clipL224` falls monotonically": 0.0486 → 0.0488 at k = 30. **FIXED** to "almost monotonically", in the .tex and the generator. | High |
| — | §3.3 l. 458 | "+0.8553 against +0.4276" appears in **no** table. Table 7's ES values are 0.7070/0.5628 (SINet-v2) and 0.6284/0.3433 (SINet). Cannot be traced within the manuscript. | Medium |

### Could not verify from manuscript data

These values are marked CANNOT VERIFY, not VERIFIED:
- Any SE (8-seed), OR or FX per-run value
- The Table 2 boundary-metric bars
- The Table 5 inputs
- The Fig. 2 values
- The effective-rank ratio
- Cohen's d attribution
- The between-cluster variance fraction
- The 8885 traced objects
- The 0.9928 AUC
- The 0.13–0.54 and 0.71–0.75 coverage figures

---

## 9. Claim–Evidence Audit

| Claim | Location | Evidence | Assessment |
|---|---|---|---|
| Targeting does not beat random at a bounded sensitivity | Abstract, §1, §3.1, Tables 1/4/5 | 16/16 cells within noise; the 8-seed CI excludes +0.0142 | **Supported** |
| Five independent controls each close a distinct objection | Abstract, contribution 2 | OR, FX, SE, CSHUF and PC are each reported | **Supported** (PC bar caveat, Mo1) |
| A targeted set is measurably different, via concentration and not direction (geometry) | Abstract, §3.2 | Probe separation survives shuffle and arbitrary-cluster aiming, and collapses only for random-vs-random (Fig. 2a) | **Supported** (Fig. 2 values cannot be verified) |
| Concentration "demonstrated … across eight seeds of trained accuracy" | Contribution 1 (l. 112–114); §3.2 opener (l. 366–368) | At 8 seeds C10−B is **within noise** (0.34×). The 8-seed result shows *no ordering by direction*; it does not show that concentration changes trained accuracy | **Overstated (M6)**. Use "consistent with". |
| Concentration demonstrated "in trained boundary accuracy" | Contribution 1 | Post-hoc, SINet only, 3 seeds, 1.03–1.37×; SINet-v2 resolves none of it (the paper says so in §3.2) | **Partially supported.** The bullet should carry the post-hoc/one-architecture qualifier. |
| "Direction is equivalent; concentration is not" / "the direction contrasts do [reach equivalence]" | §3.2 l. 399–402; Table 5 footnote | On COD10K only **3 of 6** direction contrasts reject (SINet C10−CINV p = 0.091; SINet-v2 C10−CSHUF p = 0.25; C10−CINV p = 0.31 do not). The "five of sixteen" includes NC4K rows that are **not shown** | **Overstated (M5)**. Accurate version: "only direction contrasts reach equivalence (5 of 12); the targeting-vs-random gap never does". |
| Uncertainty tracks pixel error ~2× more than structural error, "for three independent estimators on both architectures" | §3.3 l. 455–458 | Holds under **whole-image** aggregation only (8/8). Boundary aggregation passes 2/8 with 4 negative rows (Table 7). The headline numbers are untraceable | **Overstated (M7)**. Add "under whole-image aggregation". |
| "Section 3.3 measures two of [deep ensembles, MC-dropout, BADGE]" | §1.1 l. 164–165 | The estimators measured are *ensembles* and *predictive entropy*; entropy is none of the three | **Partially supported (Mo9)** |
| The interval "excludes the improvement this approach reports" | §1 l. 97–98 | The reference effect is the reproduced improvement of the *base published method* (§1.1), not something the targeting approach reports | **Misattributed wording (Mo12)** |
| "a lossy re-save … separates at 0.9928" | Discussion l. 551–552 | Not reported anywhere else in the paper | **Unsupported (Mo10)** |
| "every numeric value … Appendix D records that mapping" | AI-use & Reproducibility statements | App. D gives sources only for its own tables | **Overstated (Mo13)** |
| CHAMELEON 50/76 contaminated; exact hashing reports 0 | Abstract, §3.4, App. E | Two-tier counts, calibration and adjudication tables are internally consistent (except Mo4) | **Supported** |
| Title: "…Doesn't Help Camouflaged Object Detection" | Title | One generator, one budget, one τ, two architectures from one family. The Discussion itself says "Nothing here says closed-loop generation cannot work" | **Overstated (M8)**, author decision |
| Conclusion (rewritten) | §5 | Every statement restates a result that §§3.1–3.4 support; no new claims | **Supported** |

---

## 10. Cross-Reference and Citation Issues

| Item | Status |
|---|---|
| Undefined references or citations | **0** (final log). |
| Duplicate labels | **0**. |
| Semantically wrong: AI-use statement "(Section~\ref{sec:method})" and Reproducibility "commits named in Section~\ref{sec:method}". The commits are in App. B | **FIXED** → `Appendix~\ref{app:method}`. |
| Orphan label `tab:clustercomp` (file never `\input`) | Report only (Mo5). |
| Unreferenced appendices `app:masks` (F) and `app:controls` (G) | The main text never points to them. Suggest one pointer each. |
| l. 278 "which is how we know the **fourth column** means anything" | Table 1's fourth column is *Gap*. It probably means the *Verdict* column. Report only (Medium). |
| `\cite` used where a parenthetical citation was intended (37 occurrences: Ethics, App. A, Table 3). These rendered "COD10K Fan et al. (2022)" | **FIXED** → `\citep`. |
| Bib entries present but uncited despite the methods being used: `cheng2021boundary` (Boundary IoU), `lakens2017equivalence` (TOST) | **FIXED in the appendix:** App. C sweep paragraph and the Table 5 caption, with the generator updated. Not added to the main text, where the page budget has no room. Suggest adding at first use if space allows. |
| `cheng2021boundary` is an `@article` whose `journal` field is CVPR | Should be `@inproceedings` with `booktitle`. **Verify manually.** |
| 2025 entries (`chen2025synque`, `chen2025realcamo`, `luo2025s2rcod`, `frisch2025gauda`, `liang2025discl`) | Not verified externally. Some render with year only and no venue. **Verify manually.** No bibliographic data was invented. |

---

## 11. ICLR 2027 Compliance

| Item | Status |
|---|---|
| Template/style | `iclr2027_conference.sty` + `.bst`, `times`; letter paper; no margin, `\textheight` or `\linespread` changes. The only spacing tweak is `\itemsep0.04em` on the contributions list (low risk). |
| Main-text page count | **9 pages** (pp. 1–9). The Conclusion ends at the bottom of p. 9. **Zero spare lines**: any addition to §§1–5 will overflow. |
| Assumption | The AI-use, Ethics and Reproducibility statements (pp. 10–11) are treated as outside the limit, following ICLR's convention for ethics and reproducibility statements. The `.sty` contains no page-limit rule. **Confirm against the ICLR 2027 author guide.** If the AI-use statement counts, the paper is over the limit. |
| References placement | p. 11, after the statements. |
| Appendix placement | p. 13, **after** the references. |
| Anonymity | See §12. `\iclrfinalcopy` is commented out, so the header reads "Anonymous authors / Paper under double-blind review". |
| AI-use statement | **Present.** Contains `% AUTHOR CHECK 1` (l. 575): the authors must confirm it matches their actual use. "Four verdict bands" conflicts with the three defined (Mo6). Not fabricated or altered beyond the reference fix. |
| Ethics statement | **Present and appropriate** (dataset licensing, contamination attribution). `% AUTHOR CHECK 2`: confirm dataset licences. |
| Reproducibility statement | **Present.** Corrected "all 103" → 39 and the section reference. `% AUTHOR CHECK 3`: repository link. |
| Supplementary material | Referenced but not in this project folder. Not audited. |

---

## 12. Anonymity Audit

| Risk | Location | Classification |
|---|---|---|
| Short commit hashes `065dac6`, `617a2e1`, `6efde9f`, `c2114af`, `b755aa9` | App. B l. 805–808 | **Moderate.** If the repository is or becomes public, GitHub commit search can identify the authors. Replace with anonymised identifiers, or confirm the repository is private. |
| "We also withdraw **our own earlier recommendation** to report CHAMELEON on its uncontaminated subset" | §3.4 l. 510 | **Moderate** if that recommendation is public (preprint, workshop paper, earlier submission), because it links the authors to it. **Low** if it refers to an internal draft; in that case it also means nothing to reviewers. |
| Internal paths in captions (`results/REBUILD_LOG.txt:922`, `D2_FINAL_AUDIT/…`, `rebuild/…`) | Tables 6–10, Figs 1–3 | **Low.** Not identifying, but reviewers can't use them. |
| Source comments (`rebuild/FinalPaper/REWRITE_PLAN_2209.md`, `Paper/main_v2.tex`, artifact/decision codes) | main.tex header | **Low.** Not in the PDF. Strip them if the `.tex` goes into the supplement or to arXiv. |
| The Windows username appears in LaTeX compile logs (`C:/Users/<user>/AppData/Local/MiKTeX/…`) | `compile*.log`, `main.log` | **Moderate if shipped.** Never include build logs in the submission supplement. The copies in the audit ZIP (`_audit_logs/`) are redacted. |
| Names, affiliations, e-mails, URLs, acknowledgements, grants | none found in `.tex`, `.bib`, PDF text or figure metadata. The Windows username does not appear in any PDF. | **None.** |

---

## 13. Main Text vs. Appendix Recommendations

| Material | Current Location | Recommended Location | Reason |
|---|---|---|---|
| Allocation normalisation / softmax formula (M1) | Nowhere | §2 step (iii), one line | Central to the method. Without it the method is not reproducible and contradicts the paper's own data. |
| Campaign-code legend (ABC/SE/OR/FX/PC, MT, DETECTED) | Nowhere | Table 1 caption | Table 1 is the paper's key evidence table. |
| Cluster-composition table (`table_cluster_composition.tex`) | Orphaned | App. D, **only after** M1 is resolved in §2 and the 90.2 % is fixed | Its numbers are quoted in §3.3 with no visible support. Adding it *before* the normalisation is stated would hand reviewers the M1 contradiction. |
| Scope qualifier for signal generality (whole-image only) | App. D (Table 7) | §3.3, one clause | The main-text claim is broader than the table. |
| PC bar pooling/df | Nowhere | App. B df paragraph | Needed to reproduce Table 1's PC row. |
| SE/OR/FX per-run metrics | Supplement (claimed) | App. D or supplement, stated explicitly | The Reproducibility statement now honestly says 39. |
| Statistical detail (bars, TOST, sweeps) | App. C | Keep in the appendix | Correctly placed. |

The main text has **no** spare room (§11). Every addition above must be paid for by an equal cut. The authors should decide what to cut; no content was moved.

---

## 14. Language and Presentation Issues

- **Figure 3 (`figs/fig2_pairs.pdf`):** the top-row y-labels "COD10K-train" and "CHAMELEON" overprint each other (visible on p. 9). Regenerate with `figs/make_fig2.py`. The source images are not in this project, so it was not fixed here.
- **l. 278:** "the fourth column" is ambiguous (§10).
- **"padded/unpadded"** (§3.3): define, or say "A0".
- **Table 3 and App. E adjudication table:** underfull/overfull boxes. The appendix Table 7 overflows by 6.1 pt. All cosmetic.
- **Terminology:** "Concentration, Not Targeting" (§3.2 title, source header) vs "Concentration, Not Uncertainty" (paper title). Pick one framing.
- **Generated-file drift:** `appendix_tables.tex` already differed from `figs/make_appendix_tables.py` *before* this audit: Table 7 uses `\footnotesize` and 2 pt `tabcolsep` in the .tex but `\small` in the script, and the Table 6 source path differs. The generator also writes to `rebuild/PAPER_V4/appendix_tables.tex`, not to this folder. The AI-use claim that "no result was transcribed by hand" rests on regenerability, so re-sync the two. This audit's changes were mirrored in both generators (syntax-checked, not executed: the CSVs are not in this project).

---

## 15. Remaining Author Decisions

1. **M1:** state the actual score normalisation used before the softmax, and check the orphan table against the code.
2. **M2:** rewrite the √(8/3) projection passage (main text l. 311–313, App. C l. 882–891).
3. **M5–M8:** decide the claim strength for the TOST sentence and footnote, contribution 1, the signal-generality scope, and the title.
4. **Mo1–Mo5:** confirm the PC df, the "twelve" vs 24, the 89 % figure, the wording of the animal-7 sentence, and the orphan table (90.2 %).
5. **Mo6/Mo7:** define DETECTED and the campaign codes; reconcile "four verdict bands".
6. **Mo8:** align the CORACLE definition in §2 with App. G.
7. **Mo10:** support or remove the 0.9928 AUC claim in the Discussion.
8. **Anonymity:** commit hashes and "our own earlier recommendation".
9. **AI-use statement:** confirm it describes actual use (`AUTHOR CHECK 1`). **I did not write or alter its substance**, only the section reference.
10. **Page budget:** confirm whether ICLR 2027 counts the AI-use statement. Any §§1–5 additions need matching cuts.
11. **Missing reproducibility data:** whether to add SE, OR and FX per-run metrics.
12. **Figure 3:** regenerate to fix the overlapping labels.

---

## 16. Changes Applied (before → after)

| File | Location | Change | Why |
|---|---|---|---|
| main.tex | §5 Conclusion | Shortened from 11 to 7 source lines; clarified the CHAMELEON sentence | C1: page limit (regression I introduced) |
| main.tex | l. 314–318 | Removed the false clause; scoped "tightest" to this cell; `% AUDIT FIX` comment | M3 |
| main.tex | Table 1 | `\tabcolsep` 4.5 pt → 4 pt | Overfull 4.76 pt in the main text |
| main.tex | AI-use & Reproducibility statements | `Section~\ref{sec:method}` → `Appendix~\ref{app:method}` (×2) | Semantic reference |
| main.tex | Reproducibility statement | "all 103" → "the 39 runs … (Tables 9 and 10)"; `% AUDIT FIX` comment | M4 |
| main.tex | Ethics, App. A, Table 3 | `\cite` → `\citep` (37×) | Citation form |
| main.tex | App. C threshold sweep | + `\citep{cheng2021boundary}` | Uncited method |
| main.tex | App. C | "triples the degrees of freedom" → "from 8 to 28" | Mi5 |
| main.tex | App. E | "to three decimals" → "to within 0.002" | Mi4 |
| appendix_tables.tex | Table 9 | Split into Tables 9 (COD10K) + 10 (NC4K) with `[p]` placement; caption scope corrected (39 of 103 runs); added the missing PC source file | C2, M4 |
| appendix_tables.tex | Table 6 caption | "monotonically" → "almost monotonically" | Mi3 |
| figs/make_appendix_tables.py | Same two changes | Mirrored | Keeps the table regenerable |
| table_tost_equivalence.tex + figs/make_tost_table.py | Caption | Expanded TOST + `\citealp{lakens2017equivalence}` | Uncited method |

Pre-audit copies of every edited file are in the session scratchpad `orig/` folder (outside the project).

---

## 17. Final Verification

- Rebuilt from scratch with the aux, bbl and log files removed: `pdflatex → bibtex → pdflatex ×3`. **0 errors.**
- **0** undefined references, **0** undefined citations, **0** multiply-defined labels, **0** "Float too large" warnings.
- 23 pages. Main text pp. 1–9; p. 10 starts with "AI USE STATEMENT"; References p. 11; Appendix A p. 13.
- All 156 per-run values are present in the PDF text. Tables 9 and 10 are placed on pp. 20 and 21 and fit on their pages.
- Regression scan: the new label `tab:perrun-nc4k` resolves; the changed `\ref` targets resolve; Eq. 1 is still numbered (1); tables are numbered 1–10 and figures 1–3.

---

## 18. Issue Register (every finding, one row; statuses after round 2)

| ID | Severity | Confidence | Location | Issue | Status |
|---|---|---|---|---|---|
| C1 | Critical | High | §5 | Main text overflowed onto p. 10 (my Conclusion) | **Fixed** (R1) |
| C2 | Critical | High | App. D Table 9 | 16 rows cut off the page | **Fixed** (R1) |
| M1 | Major | High | §2 (iii); App. B | Allocation normalisation unstated | **Fixed** (R2): App. B Eq. (2) reproduces all 75 quotas |
| M2 | Major | High | §3.1; App. C | √(8/3) projection contradicts the 2σ̂ definition | **Fixed** (R2): stated as a pre-registration error |
| M3 | Major | High | §3.1 | "which at three seeds it did not" | **Fixed** (R1) |
| M4 | Major | High | Repro. stmt; Table 9 | "all 103 runs" / "every training run" | **Fixed** (R1 narrowed, R2 restored truthfully: all 103 in the supplement) |
| M5 | Major | High | §3.2; Table 5 | TOST "direction is equivalent" | **Fixed** (R2); see N1 |
| M6 | Major | High | Contribution 1; §3.2 | Concentration "demonstrated … across eight seeds" | **Fixed** (R2) |
| M7 | Major | High | §3.3 | Signal-generality scope; source of 0.8553 | **Fixed** (R2): scoped to whole-image; source B1 |
| M8 | Major | Medium | Title | Scope broader than the evidence | **Open** (author decision; alternative proposed) |
| N1 | Major | High | §3.2; Table 5 | TOST: the 5 equivalences include C10−B on SINet·NC4K; no asymmetry | **Fixed** (R2) |
| N2 | Major | High | Abstract; §1 | Reversal claimed to reproduce the geometry effect; C1 has no reversed arm | **Fixed** (R2) |
| Mo1 | Moderate | High | App. B | PC df = 4 not listed | **Fixed** (R2) |
| Mo2 | Moderate | High | App. H | "twelve" re-scored runs (24) | **Fixed** (R2) |
| Mo3 | Moderate | Medium | App. C | "share 89 %" | **Fixed** (R2): reworded without the unsupported number |
| Mo4 | Moderate | High | App. F | animal-7 "only candidate below the band" | **Fixed** (R2) |
| Mo5 | Moderate | High | orphan table | Table never included (my 90.2 % objection was wrong) | **Fixed** (R2): Table 11, values verified |
| Mo6 | Moderate | High | Table 1; AI-use stmt | DETECTED undefined; "four verdict bands" | **Fixed** (R2) |
| Mo7 | Moderate | High | Table 1 | Campaign and arm codes undefined | **Fixed** (R2): App. B legend |
| Mo8 | Moderate | High | §2 | CORACLE definition inconsistent with App. H | **Fixed** (R2) |
| Mo9 | Moderate | High | §1.1 | "measures two of them" | **Fixed** (R2) |
| Mo10 | Moderate | High | Discussion | 0.9928 AUC unsupported in the paper | **Fixed** (R2): App. E |
| Mo11 | Moderate | High | §3.2; Fig. 2 | Twenty vs four cells; effective rank undefined | **Fixed** (R2) |
| Mo12 | Moderate | High | §1 | Reference-effect misattribution | **Fixed** (R2) |
| Mo13 | Moderate | High | AI-use & Repro. stmts | "Appendix D records that mapping" | **Fixed** (R2) |
| Mo14 | Moderate | Medium | App. B | Commit hashes | **Open**, moot while N5 stands |
| Mo15 | Moderate | High | §3.4 | "our own earlier recommendation" | **Fixed** (R2) in the paper; the supplement still contradicts it (N3) |
| Mo16 | Moderate | High | generators | Generated-file drift | **Fixed** (R2): 3 generators reproduce their `.tex` exactly |
| Mo17 | Moderate | High | Fig. 3 | Overlapping row labels | **Open**: source images not supplied |
| Mo18 | Moderate | High | App. B | Checkpoint-selection split unstated | **Fixed** (R2) |
| Mo19 | Moderate | High | App. B | `B` = arm and `B` = budget | **Fixed** (R2): budget is `N` |
| Mo20 | Moderate | High | Eq. 1; App. B | ℓ1 normalisation, BCE argument order, `p_j` | **Fixed** (R2), from `Src/utils/tool.py` |
| Mo21 | Moderate | High | build logs | Username in logs | Mitigated (redacted in the ZIP) |
| Mo22 | Moderate | High | statements | Section 2 cited for commits | **Fixed** (R1) |
| N3 | Moderate | High | supplement `CLEAN_PROTOCOL.md` ×2 | Recommended the 35-image subset the paper withdraws | **Fixed** (R3, supplement package) |
| N4 | ~~Critical if an author handle~~ | High | supplement `LICENSE` | "Copyright (c) 2025 Muscape" | **Closed** (R3): README l.226–227 documents it as the upstream S2R-COD MIT notice, which the licence requires to be kept. It does not name the submitting authors. |
| N5 | Low (downgraded) | High | supplement | Commit hashes in the log and results documents | **Accepted** (R3): the repository is private (`d2r_reaudit.py` strips hashes from the release for that reason), so the hashes cannot be looked up; they also let reviewers match App. B to log blocks |
| N8 | Moderate | High | supplement `results.md` §7 | "Seed expansion … NOT RUN" contradicted §1/§6 | **Fixed** (R3): generator corrected; `results.md` regenerated byte-identically otherwise |
| N9 | Moderate | High | supplement `diag_emit.py` | Would overwrite corrected paper tables with stale versions | **Fixed** (R3): stale TOST emission removed; Table 11 and Table 2 emitters mirror the paper exactly; LF output; matplotlib imported lazily |
| R2-REG | Moderate | High | Repro. stmt | Regression from my R1 comment swallowing a sentence | **Fixed** (R2) |
| Mi1–Mi6, Mi12 | Minor | High | various | Cite form, uncited bib entries, "monotonically", "three decimals", "triples", Table 1 overflow, PC source | **Fixed** (R1) |
| Mi7 | Minor | High | §3.1 | "the fourth column" | **Fixed** (R2) |
| Mi8 | Minor | High | bib | `cheng2021boundary` entry type | **Fixed** (R2) |
| Mi9 | Minor | High | header comment | Title mismatch | **Fixed** (R2) |
| Mi10 | Minor | High | various | Unexpanded acronyms | **Fixed** (R2): BCE, MAE, EMA, COD, E-measure, ES (ARI remains, standard) |
| Mi11 | Minor | High | §3.3 | "padded/unpadded" | **Fixed** (R2) |
| Mi13 | Minor | High | Tables 3 and 7; App. F | Overfull boxes | **Fixed** except Table 3 (1.1 pt, cosmetic) |
| Mi14 | Minor | Medium | Eq. 1 | σ/σ̂ and ∇ notation | Open (cosmetic) |
| Mi15 | Minor | Low | §1 | `\itemsep` tweak | Open (low risk) |
| Mi16 | Minor | High | captions | Internal file paths | Open (they now also serve as the source mapping) |
| Mi17 | Minor | Low | bib | 2025 entries and the new Kynkäänniemi entry unverified | Open (manual) |
| N6, N7 | Low / Minor | High | supplement | Third-party e-mail; pair-list split | Informational |
| S1 | Suggestion | n/a | main text | Pointers to the mask and controls appendices | Open (no main-text space) |
| S2 | Suggestion | n/a | §2 | Display the allocation formula | Done in App. B (Eq. 2) |
| S3 | Suggestion | n/a | §3.2 | Cite Boundary IoU/TOST at first main-text use | Open (no space) |
| S4 | Suggestion | n/a | main.tex | Strip internal comments before a source upload | Open |

**Totals over both rounds:**

| Severity | Found | Fixed | Open |
|---|---|---|---|
| Critical | 2 (N4 closed, not an identity leak) | 2 | none |
| Major | 10 | 9 | M8 |
| Moderate | 27 | 23 | Mo14, Mo17; N5 downgraded and accepted; Mo21 mitigated |
| Minor | 17 | 13 | 4 |
| Suggestions | 4 | 1 done | 3 |

The Moderate count includes the R2 regression I introduced.

**Withdrawn:** the round-1 claim that 90.2 % does not reproduce.

**Author confirmations (not counted as issues):** `AUTHOR CHECK 1–3`.

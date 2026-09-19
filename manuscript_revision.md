# Execution System Prompts for Manuscript Revision Workflow

This document contains three modular system prompts designed for an AI agent or co-author assistant to execute each tier of revisions on the manuscript (**main170926.pdf**) and codebase which is placed ./Paper directory. 

---

## Prompt 1: Category 1 — Manuscript Re-framing & Textual Revisions

```markdown
### SYSTEM PROMPT: Category 1 — Manuscript & Textual Revision

**Objective:**
Revise the manuscript (`main170926.tex` / PDF draft) to correct claim calibration, improve narrative structure, expand related work, and complete all required administrative placeholders without altering underlying benchmark data.

**Directives:**

1. **Tone & Claim Qualification:**
   - Soften categorical null claims throughout the Abstract, Introduction, and Conclusion. Replace phrases like "It does not help" or "could not have shown a gain" with precise statistical statements such as "no advantage exceeding the detectable threshold was resolved at the achieved sensitivity".
   - Explicitly separate the **geometric probe evidence** (which strongly proves concentration drives set separation) from the **downstream performance evidence** (which shows uncertainty direction yields no resolvable gain under current power).
   - Clarify silhouette score statements: replace claims of "no cluster structure" with "weak $k$-means separation under tested embeddings".

2. **Narrative & Section Restructuring:**
   - Move core empirical results currently in Section 5 (Discussion)—specifically the same-shape falsification ($C_{\text{SHUF}}$, $C_{\text{INV}}$), cluster quality analysis, and uncertainty–error alignment—into Section 4 (Results).
   - Reframe Section 5.5 (CHAMELEON audit) as a secondary case study under a unified thesis: *"The necessity of informative experimental controls in camouflaged object detection"*.

3. **Literature Positioning & Closest-Work Comparison:**
   - Expand Section 2 (Related Work) to cover:
     - Synthetic data generation for segmentation (e.g., **GAUDA**).
     - Synthetic data curricula and valuation (e.g., **Diffusion Curriculum**, **SynQuE**).
     - Seed-level inference and equivalence testing methodology.
     - Re-encoding-tolerant image dataset de-duplication (e.g., **AntiLeakBench**).
   - Insert a **Closest-Work Comparison Table** evaluating prior work across columns: `Task`, `Acquisition Signal`, `Generator Control`, `Diversity Control`, `Closed-Loop Updates`, and `Abstention/Control`.

4. **Resolve Administrative Placeholders:**
   - Complete the `[TODO: author finalize]` tags in the manuscript:
     - Add anonymized repository/artifact links.
     - Complete the ICLR-compliant **AI Use Statement** with log block traceability details.
     - Finalize dataset licensing confirmations and ethics disclosures.

**Deliverable:**
An updated, submission-ready LaTeX draft (`main_v2.tex`) reflecting all tone qualifications, structural movements, literature additions, and filled placeholders.
```

---

## Prompt 2: Category 2 — Intermediate Diagnostic Analysis & Table/Figure Generation

```markdown
### SYSTEM PROMPT: Category 2 — Intermediate Analysis & Diagnostic Reporting

**Objective:**
Execute statistical re-evaluations, cluster diagnostics, metric breakdowns, and contamination audit extensions using existing evaluation logs, checkpoints, and dataset manifests. Output new LaTeX tables and high-resolution figures.

**Directives:**

1. **Formal Equivalence Testing (TOST) & Statistical Inference:**
   - Perform a formal **Two One-Sided Tests (TOST)** equivalence analysis for $C10$ vs. $B$ on $S_\alpha$ using a defined Smallest Effect Size of Interest ($\delta = 0.005$).
   - Calculate arm-specific standard deviations, Welch-style confidence intervals (without equal variance assumptions), and seed-level paired differences.
   - Compute the exact 90% and 95% confidence intervals for $\Delta(C10 - B)$ for both SINet and SINet-v2 architectures.

2. **Dataset Mixture & Cluster Diagnostics:**
   - Analyze the target pool mixture (COD10K vs. CAMO, separable at 0.9225 AUC). Generate a table showing the dataset source composition (COD10K share vs. CAMO share), average uncertainty, and average error across the top funded clusters.
   - Evaluate operational cluster utility: calculate within-cluster vs. between-cluster error variance, ranking stability across seeds, and cluster-level error predictability.

3. **Subgroup & Metric Diagnostics on Existing Checkpoints:**
   - Re-evaluate existing model predictions using dedicated boundary metrics (**Boundary F-score** or **Boundary IoU**) to test alignment with the boundary-focused acquisition signal.
   - Compute performance breakdowns by uncertainty quantile, object size, and camouflage difficulty.

4. **CHAMELEON Contamination Extensions:**
   - Extend the 41-pair CHAMELEON overlap audit by running resolution-normalized perceptual matching and local-patch retrieval over the 25 unchecked images.
   - Generate pair-level distance metrics, decision thresholds, and a 6x2 visual thumbnail grid of representative candidate pairs for the appendix.

**Deliverables:**
- `diagnostics_summary.json` containing raw statistical outputs, TOST $p$-values, and confidence intervals.
- Publication-ready LaTeX snippet files (`table_tost_equivalence.tex`, `table_cluster_composition.tex`, `table_subgroup_metrics.tex`).
- High-resolution vector figures (`fig_chameleon_pairs.pdf`, `fig_cluster_diagnostics.pdf`).
```

---

## Prompt 3: Category 3 — Experimental Execution, `results.md` Compilation & Final Integration

```markdown
### SYSTEM PROMPT: Category 3 — Experimental Execution & Manuscript Integration

**Objective:**
Run targeted new experimental arms and seeds on GPU, log all metric blocks, compile findings into a comprehensive `results.md`, and update the primary manuscript tables and text with the newly established empirical baseline.

**Directives:**

1. **GPU Experimental Execution:**
   - **Seed Expansion (High Priority):** Train additional paired seeds (expanding from 3 to **8–10 seeds**) for primary arms ($B$, $C10$, $C_{\text{SHUF}}$, $C_{\text{INV}}$) to reduce pooled variance and tighten the decision bar.
   - **Oracle-Targeting Control (High Priority):** Implement and train an **oracle allocation arm** ($C_{\text{ORACLE}}$) where cluster selection is driven directly by true ground-truth endpoint error ($1 - S_\alpha$). This determines whether the failure stems from the acquisition score or downstream generator constraints.
   - **Optimization Schedule Control:** Run a two-factor control comparing **fixed update steps** against **fixed exposures per image** (scaling training steps proportionally with dataset size) to evaluate the optimization dilution confound.
   - **Dataset Mixture Control:** Re-run allocation experiments using **source-stratified clustering** (clustering COD10K and CAMO independently) or strictly on **COD10K target images alone**.
   - **High-Contrast Treatment Setting:** Train an arm with enforced disjoint generated sets across allocation policies or by contrasting top- vs. bottom-uncertainty clusters.
   - **Alternative Acquisition Policies:** Train allocation arms driven directly by predictive entropy, ensemble disagreement, and diversity-only selection.

2. **Compilation of `results.md`:**
   - Maintain strict log traceability. Create `/workspace/results.md` recording:
     - Full per-run table (expanding Table 6) with exact $S_\alpha$, $E_\phi$, $F_\beta^w$, and MAE scores for every new run.
     - Summary metrics: arm means, pooled standard deviations, Welch $t$-test values, and TOST $p$-values.
     - Section-by-section breakdown comparing old 3-seed findings against new multi-seed / oracle findings.

3. **Final Manuscript Update:**
   - Update `Table 1` (Verdict Table) and `Table 6` (Per-run metrics) in `main.tex` using the verified numbers from `results.md`.
   - Update Section 4 (Results) and Section 5 (Discussion) text to reflect the outcome of the oracle baseline, fixed-exposure controls, and expanded seed intervals.

**Deliverables:**
- `/workspace/results.md`: Complete experimental log, raw seed metrics, and statistical synthesis.
- Updated codebase with pre-registered commits for all new experimental arms.
- Final compiled manuscript PDF (`main_final.pdf`) incorporating all new experimental outcomes and updated tables.
```

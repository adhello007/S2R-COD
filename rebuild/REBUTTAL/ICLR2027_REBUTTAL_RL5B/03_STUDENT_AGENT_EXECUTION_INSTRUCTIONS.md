# Student-Agent Execution Instructions
## ICLR 2027 Rebuttal — Reviewer RL5B — Paper `AD-PCHGS-250926`
The submitted tex code of the paper is at: ./AD-PCHGS-250926.tex and reference 1.bib
**Audience.** One student operating an autonomous AI research/coding agent on their own machine. This file is self-contained: you do not need the master prompt, the review file, or any conversation history.

**Your job:**
1. Execute every task in Section 5 in the order given in Section 4.
2. Verify every result (Phase 4, Section 7).
3. Write the updated rebuttal (Phase 5, Section 8).
4. Audit it (Phase 6, Section 9).
5. Return the `STUDENT_RESULTS/` directory (Section 10) to the corresponding author.

**Do not stop after producing a plan.** Execute everything that is feasible, then report.

---

## 0. Non-negotiable rules

1. **No fabrication.**
   - Every number you report must be emitted by a script you ran and must be traceable to a saved artifact.
   - Never transcribe a number by hand into a result table. Generate tables programmatically from saved outputs.
2. **No suppression.** Negative, null, inconclusive and contradictory results are reported with the same prominence as favourable ones.
3. **No optional stopping, no post-hoc analysis switching.**
   - Before the first training run of any new campaign, commit its pre-registration (arms, seeds, sample size, metric, analysis and decision rule) to git.
   - Never add seeds, drop runs, change metrics or change thresholds after seeing results.
   - Any analysis not in a pre-registration is labelled **EXPLORATORY / POST HOC** and decides nothing.
4. **Preserve originals.**
   - Never modify the submitted manuscript `AD-PCHGS-250926.tex` in place, the original committed results, or the frozen campaign outputs.
   - Work on a new git branch `rebuttal-RL5B` in a separate working copy.
   - Write new outputs only under new directories.
5. **No irreversible actions without the author's authorization.** This covers deleting data or checkpoints, force-pushing, rewriting history, publishing anything, or making repositories public.
6. **Never submit anything to OpenReview.** The corresponding author approves and posts everything.
7. **Reuse before rebuilding.** Inspect existing code, configs and artifacts before writing new code. Change the existing pipeline minimally and record every change in `CODE_CHANGES.patch`.
8. **Autonomy.**
   - Proceed without asking for confirmation on routine, reversible operations.
   - Diagnose and retry recoverable failures (OOM → reduce eval batch size, not training batch size; transient I/O → retry).
   - If a task is blocked, document the blocker and continue with independent tasks.
   - Checkpoint long runs so they can resume. If a run is interrupted mid-training, discard it and re-run it from scratch, as the manuscript's SE campaign did. Never score a partially trained model.

---

## 1. Scientific context

### 1.1 The paper in brief
**Title (submitted):** *Concentration, Not Uncertainty: Why Targeted Synthetic Data Doesn't Help Camouflaged Object Detection.*

**Setting.** Synthetic-to-real camouflaged object detection (COD), following the S2R-COD protocol (Luo et al., ACM MM 2025).
- **Labelled source pool:** 4447 synthetic image–mask pairs rendered by the LAKE-RED diffusion generator (Zhao et al., CVPR 2024). Foregrounds come from a salient-object dataset (HKU-IS, per the ethics statement — confirm in the repo).
- **Unlabelled target pool:** 4040 real images (3040 COD10K-train + 1000 CAMO-train).
- **Endpoints:**
  - COD10K-test (2026 images): **primary, decides verdicts**.
  - NC4K: reported.
  - CAMO-250: checkpoint selection by MAE.
- **Architectures:**
  - SINet: batch 16, 40 epochs.
  - SINet-v2: batch 32, 100 epochs.
  - Both: Adam 1e-4, 352×352, EMA teacher momentum 0.996.
- **Training:** two rounds. Between rounds, target images on which student and teacher agree are appended with teacher pseudo-labels, and round 2 retrains from scratch. The generator renders its pool once, offline, and is never invoked during training.

**Allocation loop under test.**
1. Cluster the target pool: k-means, k = 75, over L2-normalised frozen self-supervised (DINOv2/CLIP) embeddings, fitted once.
2. Score each image by student–teacher disagreement, Eq. (1):

   ES(x) = a·‖∇σ(s(x)) − ∇σ(t(x))‖₁ + b·BCE(σ(s(x)), σ(t(x))),  with a = 0.9, b = 0.3.

   The cluster score e_j is the mean ES over the cluster's members.
3. Allocate the budget N by a temperature softmax in units of the across-cluster SD, Eq. (2):

   p_j ∝ exp((e_j − max e)/(τ·s_e)),  with τ = 1.0, s_e = 0.0101, integer quotas by largest remainder.
4. Fill each quota with the foregrounds whose masked cutouts are closest to the cluster centroid.

**Arms.** All arms share the base pool and differ only in the 1000 images appended to it.

| Arm | What is appended |
|---|---|
| A0 | nothing |
| A2 | 1000 real photographs |
| B | 1000 renders drawn uniformly at random (redrawn per seed) |
| C10 | the 1000 renders the allocation selects |
| CSHUF | C10's quotas with cluster scores permuted (first of 64 pre-declared draws with zero fixed points and \|ρ\| ≤ 0.10; realised ρ = −0.03351) |
| CINV | C10's quotas in reversed rank |
| CORACLE | C10's quotas reassigned by the true endpoint error |
| A0FX / BFX / C10FX | A0 / B / C10 with steps-per-epoch unpinned (253 → 341 for SINet; 127 → 171 for SINet-v2) |
| MT | A0's pool run single-round (positive control) |

**Verdict rule (pre-registered).** Let σ̂ be the pooled within-arm per-run SD of S_α (α = 0.5).
- **REAL EFFECT:** gap > 2σ̂ **and** all seeds agree in sign.
- **WITHIN NOISE:** gap ≤ 2σ̂.
- **INCONCLUSIVE:** gap > 2σ̂ without sign agreement.

No p-values are reported at 3 seeds.

**Seeds.**
- Committed: {42, 43, 45}.
- Seed expansion (SE): adds {46, 47, 48, 49, 50}.
- The SE campaign uses arms B, C10, CSHUF and CINV at 8 seeds on both architectures, df = 28, and cost 75.9 GPU-h for 40 trained runs.

### 1.2 Central claims and key reported numbers (for checking reproduction)
- **Targeting vs random (Table 2, `tab:trained`; Table `tab:allcells`, App. C).**
  - ABC: C10−B = +0.0050, 2σ̂ = 0.0179.
  - **SE: C10−B = +0.0024, 2σ̂ = 0.0069, 6/8 sign agreement (SINet·COD10K).**
  - OR: CORACLE−B = +0.0008, 2σ̂ = 0.0061.
  - FX: C10FX−BFX = +0.0014, 2σ̂ = 0.0116.
  - PC: C10−MT = +0.0197, 2σ̂ = 0.0060 → DETECTED.
  - All 16 decisive cells are WITHIN NOISE.
- **Post-hoc interval (Sec. 3.1):** C10−B ∈ [−0.0020, +0.0067] at 8 seeds. The reference effect is 0.7030 → 0.7172 (+0.0142).
- **Per-arm SDs on the primary cell (App. C):**

  | Arm | SD at 3 seeds | SD at 8 seeds |
  |---|---|---|
  | B | 0.00181 | 0.00251 |
  | C10 | 0.00406 | 0.00489 |
  | CSHUF | 0.00166 | 0.00278 |
  | CINV | 0.00285 | 0.00302 |

  At 3 seeds, A0 had SD 0.01727 and contributes 92.7% of the ABC pooled variance.
- **TOST at ±0.005 (Sec. 3.2; `table_tost_equivalence.tex`, post hoc).**
  - 5/16 gaps are equivalent.
  - Primary cell: C10 vs CSHUF is equivalent (p = 0.019); C10 vs B is **not** (p = 0.101).
- **Concentration (Sec. 3.2).**
  - Probe separation (held-out Cohen's d) survives the shuffle and arbitrary-cluster aiming, and collapses only for random-vs-random. Real signal over shuffle: +0.0073 d. Vs arbitrary cluster: −0.0649.
  - Effective-rank ratio is 0.634 (20/20 cells).
  - CINV has the highest trained mean in 4/4 cells, all within noise.
- **Boundary metrics (post hoc; `table_subgroup_metrics.tex`, `tab:boundary`).**
  - On SINet: C10−B = 1.37× bar and CINV−B = 1.34× bar; direction contrasts are far inside the bar.
  - Threshold sweep 0.4/0.5/0.6 (Boundary-IoU): C10−B = 1.39/1.37/1.23×; CINV−B = 1.25/1.34/1.26×.
  - **SINet-v2 resolves none.**
- **Mechanism (Sec. 3.3).**
  - Silhouette ≤ 0.16; about 1/5 of the structural-error variance is between clusters.
  - CAMO is 24.8% of the pool but receives 51.5% of the budget.
  - The ES score tracks per-pixel error (+0.8553) more than structural error (+0.4276).
  - The render set is a bijection onto the base foregrounds (8885 objects traced, none regenerated).
  - Synthetic k-NN recall of the target manifold is 0.13–0.54, against 0.71–0.75 for the generator's source photos.
- **Between-arm differences beyond the injected images.**
  - Pseudo-label counts: B 1977, C10 2025, CSHUF 1990, CINV 1979 (range 1817–2259).
  - Between same-shape arm pairs, 452–511 of 1000 injected images differ.
- **CHAMELEON:** 50/76 images are training-data copies. This is not challenged by RL5B and needs no work.

### 1.3 Reviewer RL5B — verbatim concerns
Inline math was lost in the copy supplied to us. Values in [brackets] for CW-01 are restored from the manuscript. Obtain the CW-03 values from the corresponding author, who has the rendered OpenReview text.

- **CW-01.** "For the primary comparison C10−B, the reported difference is [+0.0024], with a confidence interval of [[−0.0020, +0.0067]]. This interval does not establish equivalence within the proposed margin of [±0.005]. The results support a lack of reliable evidence for an advantage, not the stronger conclusion that uncertainty guidance has no meaningful effect."
- **CW-02.** "The distributional analyses show that concentrated allocation changes the training-set composition, but this does not establish that concentration explains downstream performance changes. The post-hoc boundary-metric results are suggestive but are not consistent across both architectures."
- **CW-03.** "The reported C10 results achieve approximately [value] ([value]) on COD10K-test and [value] ([value]) on NC4K, below the reported unsupervised RISE results of [value] and [value], respectively, and standard supervised SINet-v2 results of approximately [value] and [value]. These results are not directly comparable because the training protocols differ. And the gap raises questions about the effectiveness of the overall pipeline. Stronger protocol-matched baselines and a clearer explanation of the performance gap are needed."
- **CW-04.** "The method relies on a fixed generator and a limited foreground pool, with synthetic diversity primarily coming from background changes. Weak clustering structure and limited foreground diversity may constrain the method from the outset. Consequently, the results provide limited evidence about uncertainty-guided synthetic-data generation more generally."
- **QA-01.** "Could the primary confidence intervals and equivalence-test results be presented more prominently, with a clear distinction between failure to detect an effect and evidence of equivalence?"
- **QA-02.** "What evidence supports the claim that budget concentration explains downstream performance, rather than merely changing the training-set distribution?"
- **QA-03.** "Can the performance gap be explained through protocol-matched comparisons with supervised and unsupervised COD baselines?"
- **QA-04.** "Can the conclusions be better bounded to the specific generator, foreground pool, and training setup evaluated?"

### 1.4 What the corresponding author has committed to (initial rebuttal)
The full posted text is reproduced in **Appendix A** of this file. Its binding commitments are:

| Commitment (as stated in the rebuttal) | Concern | Task(s) |
|---|---|---|
| Reword abstract, intro, Sec. 3.1 and conclusion: no detectable advantage; reference-size effects excluded; smaller effects not excluded; revise the title | CW-01, QA-01 | DOC-01 |
| Main-text table of Δ, 95% CI, 90% CI, TOST p and a three-way label for all 16 eight-seed contrasts | QA-01 | TH-01, DOC-01 |
| Recompute intervals and TOST from per-run metrics; Welch primary, seed-paired as sensitivity; report the rule's sensitivity analytically | CW-01 | TH-01 |
| Separately pre-registered confirmatory campaign (B, C10, CSHUF), fresh seeds, n fixed by TOST power analysis at ±0.005; no extension of the existing campaign; reported either way | CW-01 | EXP-01 |
| Separate the claims (distributional = established; downstream direction null = established; concentration-as-downstream-cause = hypothesis) in the abstract, Sec. 3.2 and its heading, and the discussion | CW-02 | DOC-01, TH-02 |
| Pre-registered concentration dose-response campaign: N = 1000, ≥ 3 concentration levels, several independent low-overlap permutations per level; primary Boundary-IoU on SINet·COD10K; S_α secondary; SINet-v2 replication; decision rule stated in advance | CW-02, QA-02 | EXP-02 |
| Re-score all existing eight-seed runs on both architectures with boundary metrics, with pseudo-label count and overlap as covariates, labelled exploratory | CW-02 | AN-01 |
| Protocol table (labels used, target images, backbone and pretraining, generator; S_α, E_φ, F_β^w on COD10K-test and NC4K; published values verified) | CW-03 | AN-02, DOC-02 |
| In-codebase supervised SINet/SINet-v2 on real masks of the same 4040 images; released SINet-v2 and RISE predictions/checkpoints re-scored with our scorer; source-only and reproduced S2R-COD baselines | CW-03, QA-03 | EXP-03 |
| Decomposition of the gap into label supervision, representation/backbone and reproduction differences | CW-03 | EXP-03, AN-02 |
| If compute permits: pre-registered replication of C10, B and CSHUF at a higher operating point (base pool plus a fixed fraction of real labelled target images); say so if not completed | CW-03 | EXP-04 |
| Add RISE to the related work | CW-03 | DOC-02 |
| Scope statement in abstract, intro, conclusion and title (LAKE-RED, 4447-foreground pool, background-only variation, k = 75 frozen-feature clusters, two SINet architectures, two-round self-training, N = 1000) | CW-04, QA-04 | DOC-03 |
| Report distinct foregrounds and reuse per arm, render-embedding variance by foreground vs background, and distance from each target cluster to its nearest available foreground | CW-04 | AN-03 |
| No claims about other generators; list as a limitation | CW-04 | DOC-03 |

### 1.5 Scientific objectives
1. Replace the unqualified null with a quantified one: what effect sizes are excluded and which are not.
2. Test, under pre-registration, whether concentration has a downstream effect, rather than inferring it from distributional evidence.
3. Place the pipeline's absolute performance against protocol-matched baselines and explain the gap.
4. Bound every conclusion to the generator, pool and training setup actually tested.

---

## 2. Inputs you need

| Input | Location | Needed by |
|---|---|---|
| Manuscript source `AD-PCHGS-250926.tex` + `reference.bib` | supplied by the author | DOC-* |
| Included LaTeX files: `math_commands.tex`, `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`, `appendix_tables.tex`, `table_cluster_composition.tex`, `appendix_coverage.tex`, `figs/` | repo `rebuild/FinalPaper/` (ask the author if absent) | TH-01, AN-01, DOC-* |
| Code repository (anonymised: `https://anonymous.4open.science/r/AD-35F1/`; use the private git original from the author) | author | all |
| Result artifacts: `abc_verdict.json` and its `se/`, `or/`, `fx/` variants; `pc_verdict.json`; `out/se/abc_metrics.csv`; `c1_attribution.csv`; `abc_pools.json`; `T2_RESULTS.md`; `results.md` | repo | TH-01, AN-01, TH-02 |
| Saved prediction maps or checkpoints for all SE runs (both architectures) | repo / storage | AN-01 |
| Datasets: COD10K (train/test), CAMO (train, CAMO-250), NC4K, HKU-IS, LAKE-RED checkpoint and render pool + manifest | local | EXP-*, AN-03 |
| Cluster model (k = 75), embeddings, committed cluster scores e_j, committed quotas | repo | EXP-02, EXP-04, TH-02, AN-03 |
| Rendered CW-03 reviewer values (OpenReview) | author | AN-02 |
| External: SINet-v2 official code and predictions; RISE official code (`https://github.com/xiaohainku/RISE`, arXiv:2510.18437, ICCV 2025) | internet | EXP-03, AN-02 |

If an input is missing, mark the dependent task **BLOCKED** with the exact missing item and continue with other tasks.

---

## 3. Environment setup (Stage 0, do first)

1. Clone the repository into a new working copy. Run `git checkout -b rebuttal-RL5B`. Record the base commit hash.
2. Create `ICLR2027_REBUTTAL/STUDENT_RESULTS/` with the sub-directories listed in Section 10.
3. Record the environment in `EXPERIMENT_LOGS/environment.txt`: `nvidia-smi`, CUDA/cuDNN versions, `python -V`, `pip freeze` (or `conda env export`), OS, CPU, RAM, GPU model and count.
4. Keep the manuscript's deterministic settings: `cudnn.deterministic=True`, `cudnn.benchmark=False`.
5. **Reproduction gate.** Re-score at least 4 committed SE runs (2 per architecture) from saved predictions with the repo's scorer.
   - Each must reproduce its committed S_α to the recorded precision (6 decimals for SE).
   - If this fails, stop the experiment tasks, diagnose, and document the failure. TH-01 (which uses committed CSVs) can still proceed.
6. Measure the wall-clock GPU-hours of one SINet run and one SINet-v2 run. Use these to fill the compute budget table in Section 6 **before** launching campaigns.

---

## 4. Execution order (dependency-aware)

```
Stage 0  Setup + reproduction gate
Stage 1  (P0, CPU)  TH-01 → TH-02 → AN-01 (needs predictions)
         (P0, GPU)  EXP-02 pre-registration commit (needs TH-02) → launch EXP-02 SINet runs
         (P0, text) DOC-01 outcome-independent edits
Stage 2  (P1, GPU)  EXP-01 pre-registration (needs TH-01 power analysis) → launch
                    EXP-03 (supervised upper references; re-scoring of released predictions)
                    EXP-02 SINet-v2 replication
         (P1, CPU)  AN-02, AN-03, DOC-02, DOC-03
Stage 3  (P2, GPU)  EXP-04 (only if budget remains after P0/P1 are complete or running)
Stage 4  Phase 4 verification → Phase 5 final rebuttal → Phase 6 audit; finalise DOC-01 outcome-dependent text
```

- Launch long GPU jobs as early as their pre-registration allows, and run CPU tasks while they train.
- If compute is short, the order of sacrifice is: EXP-04 first, then EXP-02 SINet-v2, then EXP-01 SINet-v2 (if added).
- **EXP-02 on SINet and EXP-01 on SINet are never sacrificed** without the author's authorization.

---

## 5. Task specifications

Each task lists: concerns, commitment, objective, hypothesis/question, inputs, dependencies, steps, design, controls, metrics, validation, deliverables, acceptance criteria, and limitations.

**Experimental procedure common to every EXP task.** Apply these steps every time:
1. Inspect the repo and locate the trainer, configs, allocation code, pseudo-labelling step and scorer.
2. Reproduce the relevant existing numbers where feasible.
3. Implement changes minimally, behind new config flags. Never change defaults used by committed runs.
4. Use identical splits, scorer, checkpoint rule (CAMO-250 MAE), image size, epochs and step-count rule as the committed campaigns, unless the task explicitly varies one.
5. Use the seeds specified.
6. Record hardware and software for each run.
7. Save each run's config, git hash, log, checkpoint, prediction maps and per-run metrics row.
8. Compute metrics with the repo scorer.
9. Report mean, SD, n and intervals.
10. Compare to the manuscript.
11. Interpret both possible outcomes.

---

### TH-01 — Statistical re-derivation, sensitivity and power (P0)

- **Concerns:** CW-01, QA-01.
- **Commitment:** "recompute every interval and TOST statistic from the per-run metrics and report the rule's sensitivity analytically, with Welch as primary (as in the manuscript) and a seed-paired analysis as sensitivity"; it also supports the main-text table and the EXP-01 sample size.
- **Objective:** Establish exactly which effect sizes the existing data exclude, which they do not, and how sensitive the pre-registered rule was.
- **Question:** For each of the 16 eight-seed contrasts, is the result *not detected*, *equivalent within ±0.005*, or *neither*? How large an effect could the 2σ̂ rule have missed?
- **Inputs:** `out/se/abc_metrics.csv` (per-run S_α, E_φ, F_β^w, both architectures, both endpoints); `se/abc_verdict.json`; `table_tost_equivalence.tex`.
- **Dependencies:** none.

**Steps**
1. Load the per-run metrics. Identify the 16 contrasts in `table_tost_equivalence.tex` (expected: C10−B, C10−CSHUF, C10−CINV, CSHUF−CINV, or as defined there, × 4 cells). Use exactly the manuscript's definitions.
2. **Reproduction.** Recompute Δ, the pooled σ̂ (df = 28), the 2σ̂ bars, sign agreement and verdicts. They must match Table `tab:allcells` exactly at the recorded precision. Recompute the Welch 95% CI and the TOST p-values. They must match [−0.0020, +0.0067] and p = 0.101 / 0.019 on the primary cell. Any mismatch is a finding: report it.
3. For each contrast, compute:
   - Δ;
   - Welch 95% CI;
   - Welch 90% CI;
   - TOST p (two one-sided Welch t-tests, margin ±0.005, α = 0.05);
   - Welch df;
   - the three-way label: *not detected* (95% CI includes 0 and TOST p ≥ 0.05), *equivalent* (TOST p < 0.05), *detected* (95% CI excludes 0), with combinations stated explicitly.
4. **Sensitivity analysis (secondary, labelled).** Seeds are shared across arms, so compute seed-paired differences, a paired t-interval and paired TOST. Report them beside the Welch results; never substitute them. Note that B redraws its image set per seed while C10/CSHUF/CINV sets are fixed across seeds, so B's variance includes set-sampling variance. Discuss what this implies for each analysis.
5. **Sensitivity of the 2σ̂ rule.**
   - Analytically: P(Δ̂ > 2σ̂ | δ) under normality with SE = σ̂√(2/n), for δ ∈ {0.0025, 0.005, 0.0067, 0.0083, 0.0142}.
   - By simulation: 100,000 draws from normal per-run outcomes with the observed per-arm SDs, n = 8, applying the **full** rule including all-seeds sign agreement (define sign agreement exactly as the repo code does; read it, don't guess).
   - Report the effect detectable with 80% probability.
   - Expected values from the rebuttal (normal approximation, ignoring the sign rule): ≈ 0.14 at δ = 0.005, ≈ 1.00 at δ = 0.0142, 80% MDE ≈ 0.0083. Confirm or correct them. If they are wrong, flag it prominently for the author, because they were posted.
6. **Power analysis for EXP-01.**
   - Compute the per-arm n needed for TOST at ±0.005, α = 0.05, power ∈ {0.8, 0.9}, using the 8-seed SDs of B and C10 (and CSHUF), under true Δ ∈ {0, +0.0012, +0.0024}.
   - Use Welch-based simulation, not only closed form.
   - Indicative closed-form values (pooled σ ≈ 0.00389): ≈ 11 per arm at Δ = 0; ≈ 29 per arm at Δ = 0.0024.
7. Write a 1-page reviewer-facing explanation of the difference between non-detection and equivalence, with the actual numbers.

- **Validation:** Every reproduced value matches the manuscript, or a discrepancy is documented. Simulation code is seeded and saved. Closed form and simulation agree within Monte-Carlo error, with any disagreement explained (the sign rule).
- **Deliverables:**
  - `RESULT_TABLES/TH01_contrasts.csv` and `.md`, and `RESULT_TABLES/TH01_rule_sensitivity.csv`, `RESULT_TABLES/TH01_power.csv`;
  - `EXPERIMENT_LOGS/TH01_*.log`; script `analysis/th01_stats.py`;
  - a LaTeX fragment `RESULT_TABLES/TH01_main_table.tex` for DOC-01.
- **Acceptance:** all 16 contrasts covered; primary-cell reproduction matches; the posted sensitivity figures are confirmed or corrected; an n is recommended for EXP-01 with its justification.
- **Limitations:** normality with 8 seeds; the variance-structure asymmetry between B and the C-family; the ±0.005 margin is post hoc (state this).

---

### TH-02 — Identification analysis: what do the same-shape contrasts identify? (P0)

- **Concerns:** CW-02, QA-02.
- **Commitment:** supports "separate the claims … concentration as a downstream explanation remains a hypothesis" and the design of EXP-02.
- **Objective:** State formally which causal quantities C10−B, C10−CSHUF, CSHUF−B and CINV−B identify, under which assumptions, and what additional design identifies a "concentration effect".
- **Inputs:** manuscript Sec. 2, Sec. 3.2, App. B; the allocation code; `abc_pools.json`.
- **Dependencies:** none.

**Procedure**
1. **Definitions.**
   - An allocation is a pair (q, π): q is the sorted quota vector (the shape) and π is the assignment of quotas to clusters (the direction).
   - The injected set is S(q, π) = the fill rule applied to the assignment.
   - The outcome is Y = f(S) + seed noise.
   - The arms are: C10 = (q*, π_u); CSHUF = (q*, π_s); CINV = (q*, π_r); B = a random set with induced cluster-count vector q_B (compute it by assigning each B render to its nearest target-cluster centroid, using the same embedding).
2. **Assumptions, stated explicitly.**
   - A1: the outcome depends on the allocation only through S, plus the arm's own downstream pseudo-labels.
   - A2: no interference across runs.
   - A3: a permutation-exchangeability assumption for defining a shape effect, i.e., the shape effect is θ(q) = E_π[Y(q, π)] − E[Y(B)] with π uniform over admissible permutations.
3. **Derivation.** Show that CSHUF−B = θ(q*) + [Y(q*, π_s) − E_π Y(q*, π)] + set-identity noise. The single-permutation term does not vanish. Derive its variance as Var_π(Y(q*, π)), which is unknown from one draw. Conclude that one permutation does not identify θ, and that K permutations reduce the term by 1/K.
4. Show that a trained null on direction (C10 ≈ CSHUF ≈ CINV) is compatible with θ(q*) of any size, including 0. Therefore the existing trained data do not identify a downstream concentration effect.
5. Show how the overlap between concentrated arms (about 50% shared images) correlates their errors. Derive the effect on the variance of contrasts between C-family arms vs contrasts against B. Give the covariance expression in terms of the shared fraction.
6. **Concentration index.** Define it as N_eff = exp(H(p)), plus the max share, Gini and TV distance from uniform. Compute it for C10/CSHUF/CINV (identical), B (from q_B, averaged over seeds), cluster-uniform, and candidate τ values for EXP-02. Pick an EXP-02 high-concentration τ such that N_eff(τ_H) ≈ N_eff(1.0)/2 on the committed scores, and fix it before EXP-02 is pre-registered.
7. **Boundary cases.**
   - Highly concentrated allocations may exhaust a cluster's nearby foregrounds (fill distance grows), so concentration and foreground-match quality are confounded. Quantify this with AN-03 data.
   - The cluster-uniform allocation removes direction entirely.
   - At odd k, CINV has a fixed point.
8. Write the corrected or qualified statement for the manuscript, and the reviewer-facing explanation (≤ 1,200 characters).

- **Validation:** Check the derivations numerically by a small simulation with synthetic f(S) where θ is known (a toy where outcome = α·N_eff + β·direction + noise). The estimator from K permutations must recover α. Save the code.
- **Deliverables:** `RESULT_TABLES/TH02_identification.md` (derivation), `RESULT_TABLES/TH02_concentration_indices.csv`, `analysis/th02_sim.py`, and the chosen τ_H written into the EXP-02 pre-registration.
- **Acceptance:** assumptions explicit; the non-identification by a single permutation is shown; τ_H is fixed with its N_eff; the simulation recovers known parameters.
- **Limitations:** A1–A3 are modelling assumptions. Pseudo-labelling makes arms differ downstream of S. State that this cannot be eliminated, only measured.

---

### AN-01 — Boundary-metric re-scoring of all eight-seed runs, with covariates (P0, EXPLORATORY)

- **Concerns:** CW-02(b), QA-02.
- **Commitment:** "re-score all existing eight-seed runs on both architectures with the boundary metrics, with pseudo-label count and image overlap as covariates, labelled exploratory."
- **Objective:** Determine whether the SINet boundary result holds at 8 seeds, and whether it is explained by the pseudo-label count or image overlap; characterise the SINet-v2 non-replication.
- **Inputs:** prediction maps (or checkpoints → re-infer) for SE arms B, C10, CSHUF and CINV × seeds {42, 43, 45–50} × {SINet, SINet-v2} × {COD10K-test, NC4K}; the boundary-metric code that produced `tab:boundary` (identify both metrics and their parameters from `table_subgroup_metrics.tex` and the scoring script); per-run pseudo-label counts; injected-set manifests.
- **Dependencies:** Stage 0 gate.

**Steps**
1. Reproduce `tab:boundary` exactly on the runs it was computed on (determine whether those were 3 or 8 seeds). This is the reproduction gate for this task.
2. Compute both boundary metrics at thresholds 0.4/0.5/0.6 for all 64 runs × 2 endpoints. Use the same Boundary-IoU dilation parameter as the manuscript; record it.
3. Apply the manuscript's verdict rule using the SE campaign's own pooled σ̂ for each boundary metric. Report Δ, bar, ×bar and sign agreement for C10−B, CINV−B, CSHUF−B, C10−CSHUF and C10−CINV, per cell.
4. **Exploratory regression:** per-run metric ~ concentrated (C-family vs B) + pseudo-label count + Jaccard(injected set, C10 set) + architecture-specific intercepts + (1 | seed). Report coefficients with CIs. Do not use the regression to re-decide any verdict.
5. **SINet-v2 diagnostics.** Compare per-arm SDs between architectures and compute the minimum detectable Δ under the rule for each. Report whether SINet-v2's non-replication is better described as a smaller effect or as larger noise, as **descriptive only**.

- **Validation:** The reproduction gate passes. The scorer is unit-tested on one image pair against the reference Boundary-IoU implementation (Cheng et al., CVPR 2021).
- **Deliverables:** `RESULT_TABLES/AN01_boundary_8seed.csv/.md`, `RESULT_TABLES/AN01_regression.md`, `FIGURES/AN01_boundary_by_arm.pdf`, logs.
- **Acceptance:** 64/64 runs scored (or the missing ones listed); every output labelled EXPLORATORY; both architectures reported side by side.
- **Limitations:** post hoc; binarisation dependence; the covariates are post-treatment (pseudo-label count is affected by the arm) — say so; regression coefficients are not causal.

---

### EXP-01 — Confirmatory equivalence campaign "EQ" for the primary contrast (P1)

- **Concerns:** CW-01, QA-01.
- **Commitment:** "a separately pre-registered confirmatory campaign for the primary contrast (B, C10 and CSHUF), with fresh seeds and a sample size fixed in advance by a power analysis for TOST at ±0.005 … reported whether or not equivalence is established."
- **Objective:** Obtain a confirmatory, pre-registered estimate of C10−B (and C10−CSHUF) precise enough to establish or reject equivalence at ±0.005.
- **Hypotheses (pre-register verbatim):**
  - H1 (primary): |μ_C10 − μ_B| < 0.005 on SINet·COD10K-test S_α (TOST, Welch, α = 0.05).
  - H1b (secondary): the same for C10−CSHUF.
  - NC4K is reported as secondary.
- **Inputs:** committed C10 and CSHUF injected sets (unchanged); the B sampling procedure (redrawn per seed, as committed); base pool; trainer.
- **Dependencies:** TH-01 (n); Stage 0 gate.

**Pre-registration** (commit `prereg/EQ.md` before the first run):
- **Arms:** B, C10, CSHUF.
- **Architecture:** SINet (primary). Add SINet-v2 only if the budget table shows it is affordable, and decide that now, in the pre-registration.
- **Seeds:** fresh and never used before. Exclude {42, 43, 44, 45, 46, 47, 48, 49, 50}. Use 101, 102, …, 100+n.
- **Sample size:** n per arm = the TH-01 recommendation for 80% power at true Δ = +0.0024 (the observed value), capped at the largest n the compute budget allows. If capped, pre-register the achieved precision (expected 90% CI half-width) and state that equivalence may not be reachable.
- **Metric:** S_α at α = 0.5, scored by the committed scorer; checkpoint by CAMO-250 MAE.
- **Analysis:** Welch 90% and 95% CIs, TOST at ±0.005; the manuscript's 2σ̂ verdict rule also reported. A seed-paired analysis is secondary.
- **Secondary, labelled pooled analysis:** inverse-variance combination of EQ with SE. Mark it secondary, because SE was seen before EQ was designed.
- **Stopping:** all n runs per arm complete; no interim looks at endpoint metrics. A run lost to failure is re-run from scratch with the same seed; it is never replaced by a new seed and never dropped.
- **Decision statements, written in advance:** (i) equivalent; (ii) not equivalent and not detected (inconclusive at this precision); (iii) detected (95% CI excludes 0); with the reviewer-facing sentence for each.

**Steps**
1. Commit the pre-registration and record its hash.
2. Launch all runs; checkpoint and resume on crash.
3. Assert per run: base pool hash manifest matches; step count pinned at 253 (SINet) / 127 (SINet-v2); injected set hash matches the arm's manifest (for B, the seed-specific draw).
4. Score and analyse with a script written **before** the results exist (commit it with the pre-registration).

- **Controls:** CSHUF is the same-shape control; B is the random control. MT is not needed.
- **Metrics:** S_α (primary), E_φ, F_β^w, MAE (reported).
- **Validation:** spot-re-score 3 runs from saved predictions; confirm the analysis output matches.
- **Deliverables:** `prereg/EQ.md` (+ hash), `RESULT_TABLES/EXP01_EQ.csv/.md`, `FIGURES/EXP01_forest.pdf`, `EXPERIMENT_LOGS/EXP01/`.
- **Acceptance:** all pre-registered runs complete; analysis exactly as pre-registered; the outcome is reported with the pre-written sentence.
- **Limitations / failure conditions:**
  - The margin ±0.005 was chosen post hoc in the original paper; justify it as ≈ 0.35× the reference effect and note this.
  - If capped below the power target, the result may be inconclusive; report it as such.
  - Seed nondeterminism is reduced, not eliminated (cuDNN).

---

### EXP-02 — Concentration dose-response campaign "CDR" (P0 SINet, P1 SINet-v2)

- **Concerns:** CW-02, QA-02.
- **Commitment:** "a pre-registered campaign that holds the budget at N = 1000 and varies concentration across at least three levels (cluster-uniform; the committed τ = 1.0 shape; a more concentrated τ), each realised by several independent random permutations of the cluster scores constrained to low image overlap with C10 … Primary metric: Boundary-IoU on SINet·COD10K, fixed before any run; S_α secondary; SINet-v2 as replication … we will describe concentration as a downstream explanation only if the outcome changes with concentration consistently across permutations; otherwise we will restrict the claim to the training-set distribution."
- **Objective:** Test whether the allocation's concentration, with direction averaged out and image identity varied, affects downstream boundary accuracy.
- **Hypothesis (pre-register):** H2: mean Boundary-IoU (threshold 0.5) on SINet·COD10K-test differs between the concentrated levels (L1, LH) and the dispersed references (B, LU). Exploratory: the difference grows monotonically with concentration (LU/B < L1 < LH, or reversed).
- **Inputs:** committed cluster scores e_j, k-means model, fill rule, render pool; τ_H from TH-02; SE runs of B, C10, CSHUF and CINV at seeds {42, 43, 45} (re-scored, not retrained).
- **Dependencies:** TH-02 (τ_H, concentration indices), AN-01 (scorer and reproduction of the boundary metric), Stage 0.

**Design**

| Level | Allocation | Direction | Allocations | Seeds | New runs per architecture |
|---|---|---|---|---|---|
| LU | cluster-uniform quotas (equal shares, largest-remainder) | none | 1 | 42, 43, 45, 46, 47 | 5 |
| L1 | committed τ = 1.0 quotas (shape q*) under new permutations P1–P5 | random | 5 | 42, 43, 45 | 15 |
| LH | τ_H quotas under new permutations P1–P5 | random | 5 | 42, 43, 45 | 15 |
| ref | B, CSHUF (= L1 perm P0), C10, CINV | existing | — | 42, 43, 45 (+ SE seeds for B) | 0 (re-score) |

That is about 35 new runs per architecture.

**Permutation draws (rule fixed before drawing; never chosen by inspecting consequences):**
- Use NumPy `default_rng(2027)`. Generate permutations of the 75 cluster scores in sequence.
- Accept a permutation only if all of the following hold:
  - zero fixed points;
  - |Spearman ρ(permuted scores, true scores)| ≤ 0.10;
  - Jaccard(injected set, C10 set) ≤ 0.35;
  - Jaccard with every already-accepted set at the same level ≤ 0.50.
- Accept the first 5 that pass, separately for L1 and LH.
- If fewer than 5 pass within 10,000 draws, relax the C10-Jaccard bound in pre-declared steps (0.40, then 0.45, then 0.50) and record which step was used.
- Record the realised ρ, Jaccards and N_eff for every accepted draw.
- **Set-distinctness gate (before GPU time):** every pair of CDR sets has Jaccard ≤ 0.50 (the manuscript's bound).
- **Fill-quality record:** for each allocation, the mean and max cutout-to-centroid distance of filled foregrounds (from AN-03). It is a covariate, because concentration may force poorer matches.

**Pre-registration** (commit `prereg/CDR.md` before the first run):
- Primary metric: Boundary-IoU at threshold 0.5, with the manuscript's dilation parameter.
- Primary cell: SINet·COD10K-test.
- Secondary: S_α under the manuscript's verdict rule; NC4K; SINet-v2 as replication with the same analysis.

**Primary analysis**
1. Unit of analysis = allocation (mean over its seeds), because direction is the nuisance being averaged.
2. Contrast: mean over L1 ∪ LH allocations vs mean over {B, LU}. Report the Welch CI over allocation means.
3. Also report the seed-level mixed model: BIoU ~ level + (1 | allocation) + (1 | seed).
4. Report the between-permutation SD at each level.

**Decision rule (pre-registered):**

| Condition | Conclusion |
|---|---|
| (a) The concentrated-vs-dispersed difference exceeds 2σ̂ (σ̂ pooled within allocation across seeds, per the manuscript's rule) **and** (b) ≥ 4/5 permutations at L1 (or LH) agree in sign with the difference **and** (c) the between-permutation SD at that level is smaller than \|difference\| | **"concentration effect supported downstream (SINet)"** |
| (a) fails at both levels | **"not supported"** |
| Any other combination | **"inconclusive"** |

SINet-v2 is judged by the same rule. The paper may say "consistent across architectures" only if both are "supported".

**Steps**
1. Implement `--allocation_mode {uniform, permuted, tau}` and `--perm_seed`, `--tau` flags in the allocation script without altering default behaviour. Unit-test that τ = 1.0 with the identity permutation reproduces all 75 committed quotas and the committed C10 set hash exactly.
2. Generate the allocations and sets; run the gates; commit manifests and the pre-registration.
3. Launch SINet runs (P0), then SINet-v2 (P1).
4. Assert the step count and base-pool hash per run, and record the pseudo-label count per run.
5. Score with the AN-01 scorer; analyse with the pre-committed script.

- **Controls:** LU (dispersed, no direction); B (random); CSHUF/C10/CINV (fixed shape, three directions).
- **Metrics:** Boundary-IoU at thresholds 0.4/0.5/0.6, the second boundary metric of `tab:boundary`, S_α, E_φ, F_β^w, MAE.
- **Validation:**
  - The unit test reproduces the committed quotas.
  - Re-scored existing runs match AN-01.
  - An independent recomputation of the primary contrast from raw per-run CSV matches.
- **Deliverables:** `prereg/CDR.md`, `RESULT_TABLES/EXP02_allocations.csv` (ρ, Jaccards, N_eff, fill distances), `RESULT_TABLES/EXP02_results.csv/.md`, `FIGURES/EXP02_dose_response.pdf` (metric vs N_eff, points = allocations, error bars = seed SD), `EXPERIMENT_LOGS/EXP02/`.
- **Acceptance:** gates passed; all SINet runs complete; decision reported per the rule; SINet-v2 complete or explicitly BLOCKED/not run with the reason.
- **Limitations / failure conditions:**
  - Concentration is confounded with fill quality (record it and use it as a covariate in an exploratory model).
  - 3 seeds per permutation.
  - The low-overlap constraint may itself select unusual permutations; report the acceptance rate.
  - A "not supported" outcome means the manuscript must drop the downstream concentration claim. Report it as such.

---

### EXP-03 — Protocol-matched baselines and gap decomposition (P1)

- **Concerns:** CW-03(a–d), QA-03.
- **Commitment:** "SINet and SINet-v2 trained with the real masks of the same 4040 images (a labelled upper reference); released SINet-v2 and RISE predictions or checkpoints re-scored with our evaluation code, to separate scorer differences from training differences; and our source-only and reproduced S2R-COD baselines … decompose the gap into label supervision, representation/backbone, and reproduction differences."
- **Objective:** Explain the absolute gap quantitatively under one scorer and one set of test splits.
- **Question:** How much of the gap between C10 and supervised SINet-v2 / RISE is due to (i) real labels, (ii) the training recipe, (iii) representation/backbone and method, and (iv) scorer or reproduction differences?
- **Inputs:** real masks for COD10K-train and CAMO-train; official SINet-v2 code, released prediction maps and checkpoint; RISE official repo (code, checkpoints, pseudo-labels or predictions, whichever is released); our trainer.
- **Dependencies:** AN-02 (published numbers and protocols), Stage 0.

**Arms and evaluations**

| ID | Description | Seeds | Purpose |
|---|---|---|---|
| E3-a | Score the released SINet-v2 prediction maps with **our** scorer on COD10K-test and NC4K | — | scorer agreement (tolerance ±0.002 S_α vs published) |
| E3-b | SINet-v2 retrained with the official recipe on COD10K-train + CAMO-train real masks | 3 (42, 43, 45) | recipe reproduction; skip if E3-a matches and the budget is short |
| E3-c | SUP-ours: our trainer, single round, real masks of the same 4040 images, no synthetic data; SINet and SINet-v2 | 3 | label-supervision gap under our recipe |
| E3-d | Score RISE released predictions/checkpoint with our scorer | — | scorer-matched unsupervised reference |
| E3-e (optional) | SINet trained on RISE pseudo-labels of the 4040 target images (if released or reproducible) | 3 | separates RISE's supervision quality from its architecture/representation |
| E3-f | Our anchors from existing runs: A0, MT, B, C10 (SE seeds), and the S2R-COD reproduction pair 0.7030 / 0.7172 (identify exactly which runs or configs these are) | existing | pipeline anchors |

**Steps**
1. For each external method, record: training images; label source (real masks / none / synthetic); backbone and pretraining; image size; test-time choices.
2. Run E3-a first. If our scorer disagrees with published numbers beyond tolerance, investigate (mask binarisation, resizing, metric implementation) before anything else, and document it.
3. Run E3-c with the same checkpoint rule (CAMO-250 MAE) — and note that CAMO-250 must not overlap CAMO-train (check). Then run E3-b and E3-e as the budget allows.
4. Build the gap decomposition table:
   - E3-c − C10 → label supervision under our recipe;
   - E3-b (or published) − E3-c → recipe;
   - E3-d − C10 → unsupervised method + representation;
   - E3-e − C10 and E3-d − E3-e → supervision quality vs architecture;
   - published vs E3-a / E3-d re-scored → scorer.
5. Report CIs over seeds where seeds exist.

- **Controls:** same test splits, same scorer, same image size for in-codebase arms.
- **Metrics:** S_α, E_φ (state which variant: mean or adaptive; match the published variant), F_β^w, MAE on COD10K-test and NC4K. CHAMELEON is excluded (Sec. 3.4).
- **Validation:** E3-a must match published within tolerance or the discrepancy is explained. Check that the training images of external methods do not include test images; note any overlap with our target pool.
- **Deliverables:** `RESULT_TABLES/EXP03_protocol_matched.csv/.md`, `RESULT_TABLES/EXP03_gap_decomposition.md`, `FIGURES/EXP03_gap_bars.pdf`, logs.
- **Acceptance:** E3-a, E3-c (both architectures) and E3-f complete; E3-d complete or BLOCKED with the reason (e.g., nothing released); the decomposition table is filled only with measured values (missing cells shown as "—", never estimated).
- **Limitations:** a supervised upper reference is not a fair competitor, and the text must say so; RISE may be impossible to re-score; the gap decomposition is not strictly additive (state this).

---

### EXP-04 — Replication of the decisive contrasts at a higher operating point (P2, optional)

- **Concerns:** CW-03(b), CW-04(d).
- **Commitment:** "If compute permits, we plan a pre-registered replication of C10, B and CSHUF at a higher operating point (base pool plus a fixed small fraction of real labelled target images) … If it cannot be completed in time, we will say so."
- **Objective:** Test whether the direction null depends on the low operating point.
- **Hypothesis (pre-register):** at the higher operating point, C10−B and C10−CSHUF on SINet·COD10K-test S_α are within noise (manuscript rule) vs not. Report the TOST at ±0.005 as well.
- **Inputs:** real masks; committed clusters; allocation code.
- **Dependencies:** EXP-03 E3-c (the labelled-data pipeline), Stage 0. Start only after the P0/P1 GPU jobs are complete or running and budget remains.

**Design**
1. Draw a stratified random 10% of the target pool (304 COD10K-train + 100 CAMO-train) with `default_rng(2028)`. Commit the list.
2. Add these images, with their real masks, to the labelled base pool of all arms. They remain in the unlabelled target pool unchanged, so clusters and target data are identical to the original.
3. Train A0′ (round 1), recompute ES scores and the C10′ allocation at τ = 1.0 with the committed procedure, and build CSHUF′ with the **same** permutation as CSHUF.
4. Arms: A0′, B′, C10′, CSHUF′ at seeds {42, 43, 45, 46, 47}, SINet only (20 runs).
5. Record the steps-per-epoch actually used, which depends on which loader is shorter.

- **Steps:** pre-register (`prereg/OP.md`) → implement a config flag for extra labelled real images → run → analyse with the manuscript's rule plus Welch CI/TOST.
- **Validation:** A0′ must outperform A0. If it does not, the operating point was not raised; report that and do not interpret the contrasts.
- **Deliverables:** `prereg/OP.md`, `RESULT_TABLES/EXP04_operating_point.csv/.md`, logs.
- **Acceptance:** completed per the pre-registration, or reported as **not run** with the reason.
- **Limitations:** a single operating point; 10% is an arbitrary fraction; the semi-supervised regime differs from both original protocols.

---

### AN-02 — Literature and protocol audit for the performance gap (P1)

- **Concerns:** CW-03, QA-03.
- **Commitment:** the protocol table, with all published values verified against the original papers; part of the gap decomposition.
- **Objective:** Produce verified published numbers and protocol descriptions for SINet, SINet-v2, RISE, S2R-COD and LAKE-RED-based training, and check the reviewer's quoted values.

**Steps**
1. Obtain from the author the reviewer's rendered CW-03 values.
2. For each method, record from the **original paper** (cite table and page): S_α, E_φ (variant), F_β^w, MAE on COD10K-test and NC4K; training data; labels; backbone; pretraining; input size.
3. Locate our own C10 absolute values in `appendix_tables.tex` / `results.md` and confirm the reviewer's figures.
4. Write a verified BibTeX entry for RISE. Candidate details from a web search: Du, Wang, Hao, Yu, Chen, Wu, Wang, Xu, Li, "Beyond Single Images: Retrieval Self-Augmented Unsupervised Camouflaged Object Detection", ICCV 2025, arXiv:2510.18437, DOI 10.1109/ICCV51701.2025.02055. **Verify every field** against the CVF/IEEE page.
5. Confirm from the paper or repo which feature extractor RISE uses. The initial rebuttal said only "frozen self-supervised ViT features with dataset-level retrieval"; if that is inaccurate, flag it for correction.

- **Validation:** every number has a source (table/page); no number is copied from secondary summaries.
- **Deliverables:** `RESULT_TABLES/AN02_published_baselines.md`, `RESULT_TABLES/AN02_rise.bib`.
- **Acceptance:** all cells sourced, or marked "not reported".
- **Limitations:** published numbers may use different metric variants; record the variant.

---

### AN-03 — Foreground-pool and generator constraint quantification (P1)

- **Concerns:** CW-04, QA-04.
- **Commitment:** "distinct foregrounds and foreground reuse per arm; the share of render-embedding variance explained by foreground identity versus background; and, for each target cluster, the distance to the nearest available foreground."
- **Objective:** Quantify how much diversity the render pool can offer an allocation policy.
- **Inputs:** render manifest (render → foreground id → base-pool image); injected-set manifests for B (per seed), C10, CSHUF, CINV, CORACLE and the CDR sets; DINOv2 embeddings (same model and preprocessing as the clustering); cutout embeddings used by the fill rule; cluster centroids.

**Steps**
1. Confirm the foreground source (HKU-IS or other) and the bijection claim (each render ↔ exactly one base-pool foreground). Report the counts.
2. **Per arm:** number of distinct foregrounds; fraction already present in the base pool (expected 100% if the bijection holds); semantic/category diversity if labels exist; overlap with every other arm.
3. **Variance decomposition:** for renders and their base-pool counterparts (same foreground, different background), compute the share of embedding variance explained by foreground identity (between-foreground variance ÷ total, from pairs or groups). Also report cosine similarity of render ↔ own base image vs render ↔ random base image.
4. **Per target cluster:** distance from the centroid to its 1st, 10th, 50th and q_j-th nearest available cutout, where q_j is the committed C10 quota and the LH quota. Plot quota vs fill distance.
5. Relate the results to the reported coverage numbers (0.13–0.54 vs 0.71–0.75) and silhouette (≤ 0.16), without re-deriving those unless their scripts are available, in which case reproduce them.

- **Validation:** counts are reproducible from the manifests by an independent second script.
- **Deliverables:** `RESULT_TABLES/AN03_foreground_diversity.csv/.md`, `FIGURES/AN03_fill_distance.pdf`, logs.
- **Acceptance:** all three committed quantities reported.
- **Limitations:** embedding-based diversity depends on the embedding; state the model.

---

### DOC-01 — Claim calibration and main-text CI/TOST table (P0 text; finalise after results)

- **Concerns:** CW-01, CW-02, QA-01, QA-02.
- **Commitment:** reword the abstract, introduction, Sec. 3.1 and conclusion; separate the claims in Sec. 3.2 and its heading; add the main-text table; revise the title.

**Steps**
1. Copy the manuscript to `revision/AD-PCHGS-revised.tex`. **Never edit the original.**
2. Find every overclaiming sentence:

   ```
   grep -n -iE "doesn.t help|does not (outperform|help|beat)|no (score|effect)|not an artifact|cannot|never|null" revision/AD-PCHGS-revised.tex
   ```

   List each sentence with its proposed revision in `RESULT_TABLES/DOC01_claims.md`. Known items: the title; abstract ("does not outperform", "not an artifact", final sentence); intro paragraphs 3–4 and contribution bullet 2; Sec. 3.1 ("no score of any quality helped here", "Perhaps three seeds are too few. It was" (grammar)); Sec. 3.2 heading and first paragraph; Sec. 3.2 TOST sentence ("on NC4K" is ambiguous); conclusion.
3. **Outcome-independent edits now:**
   - The downstream claim becomes "no detectable advantage; reference-size effects excluded; effects ≲ +0.0067 not excluded on the primary cell".
   - The three-tier claim structure for concentration.
   - Insert the TH-01 table into Sec. 3.1, with a definition of *not detected* vs *equivalent*.
4. **Outcome-dependent edits after EXP-01, EXP-02 and AN-01:** write the final wording from the actual outcomes, using the pre-registered decision sentences.
5. Title options for the author (the author decides; check ICLR policy on title changes during the discussion period):
   - (i) "Concentration Without Direction: A Controlled, Bounded Null for Uncertainty-Guided Allocation of Synthetic Data in Camouflaged Object Detection"
   - (ii) "Uncertainty-Guided Allocation of Synthetic Training Data Shows No Detectable Benefit for Camouflaged Object Detection"
   - If EXP-02 does not support a downstream concentration effect, avoid putting "Concentration" in a title that could be read as a downstream claim.
6. Produce `CODE_CHANGES.patch`-style diffs for the manuscript: `revision/manuscript.diff`.

- **Deliverables:** `revision/AD-PCHGS-revised.tex`, `revision/manuscript.diff`, `RESULT_TABLES/DOC01_claims.md`.
- **Acceptance:** every listed sentence is addressed; the revised .tex compiles (with the included files) or the compile blocker is documented; no new claim exceeds verified evidence.

### DOC-02 — Related work, RISE, and the protocol table (P1)
- **Concerns:** CW-03, QA-03.
- **Steps:**
  1. Add RISE to App. A (COD detectors paragraph) and to Sec. 1.1 if space permits, with the verified BibTeX from AN-02.
  2. Add the protocol-matched table (from EXP-03 / AN-02) to the main text or App. A.
  3. Add a paragraph explaining the gap using only measured decomposition values.
- **Deliverables:** edits in `revision/AD-PCHGS-revised.tex`; `revision/reference.bib` with the new entry.
- **Acceptance:** every number in the table traces to AN-02 (published) or EXP-03 (measured).

### DOC-03 — Scope and limitations (P1)
- **Concerns:** CW-04, QA-04.
- **Steps:** Write a "Scope" paragraph and add one sentence each to the abstract, intro and conclusion. The scope is: LAKE-RED; fixed render pool, rendered once and offline; the 4447-foreground pool (source as confirmed in AN-03); background-only variation; allocation, not generation; k = 75 k-means on frozen self-supervised features; SINet and SINet-v2; two-round self-training with pinned steps; N = 1000; COD10K-test/NC4K endpoints. Include the AN-03 numbers. State that other generators are untested.
- **Acceptance:** each item of the posted scope list appears in the revised text.

---

## 6. Compute budget (fill in at Stage 0 before launching)

| Task | Runs (SINet) | Runs (SINet-v2) | GPU-h/run (measured) | Total GPU-h | Priority |
|---|---|---|---|---|---|
| EXP-02 CDR | 35 | 35 | | | P0 / P1 |
| EXP-01 EQ | 3 × n | (optional) | | | P1 |
| EXP-03 E3-b, E3-c, E3-e | 3 + 3 (+3) | 3 + 3 | | | P1 |
| EXP-04 OP | 20 + A0′ scoring | — | | | P2 |

For reference, the manuscript's SE campaign averaged ≈ 1.9 GPU-h per run (75.9 GPU-h / 40 runs, both architectures).

If the total exceeds the available budget, follow the sacrifice order in Section 4 and record the decision **before** launching.

---

## 7. Phase 4 — Scientific verification and evidence collection

Verify every completed task **before** any of its numbers enters a rebuttal. For each task, check:
1. it was actually executed (logs exist, timestamps plausible, run count matches the pre-registration);
2. every reported value matches a saved artifact (regenerate the tables from raw files and diff them);
3. the evaluation protocol is valid (splits, scorer, checkpoint rule, step pin, hashes);
4. baselines are fair (same data, scorer, image size; differences listed);
5. mathematical conclusions follow from stated assumptions;
6. statistical interpretation is appropriate (pre-registered vs exploratory; no p-hacking; multiplicity noted where several tests are reported);
7. results support the *specific* reviewer-facing sentence they will be used for;
8. negative and inconclusive results are included.

Create **`STUDENT_RESULTS/EXPERIMENTAL_EVIDENCE.md`** with one entry per task in this template:

```
## <TASK-ID> — <title>
Reviewer issues: <CW/QA IDs>
Status: VERIFIED | PARTIALLY VERIFIED | INCONCLUSIVE | FAILED | BLOCKED
Pre-registration: <path + git hash, or "n/a (exploratory)">
Code revision: <git hash>
Commands: <exact commands>
Datasets: <splits, sizes, hashes>
Configuration: <config paths; key parameters>
Seeds: <list>
Hardware/software: <pointer to environment.txt + per-run deviations>
Artifacts: <paths to CSVs, logs, figures — must exist>
Results: <table generated from artifacts>
Interpretation: <what it shows, what it does not>
Limitations: <list>
Verification notes: <which of checks 1–8 were done and how>
```

Status definitions:
- **VERIFIED:** complete as specified; all checks pass.
- **PARTIALLY VERIFIED:** some sub-parts complete and verified, others missing.
- **INCONCLUSIVE:** executed correctly, but the result does not resolve the question at the achieved precision.
- **FAILED:** executed, but invalid (a bug, a protocol violation, or a reproduction-gate failure).
- **BLOCKED:** could not be executed; state the exact blocker.

Also create:
- **`EXECUTION_STATUS.md`:** a table of task, status, start/end, GPU-h used, blockers, and deviations from this file (each with its reason).
- **`RESULTS_SUMMARY.md`:** at most 2 pages. Key verified findings per reviewer concern, with numbers, and an explicit list of anything that contradicts statements in the initial rebuttal.

---

## 8. Phase 5 — Final updated rebuttal

Create **`STUDENT_RESULTS/FINAL_UPDATED_REBUTTAL.md`**.

1. Re-read the initial rebuttal (Appendix A). For each concern, identify: the original response; the work performed; the verified findings; whether the concern is now resolved; and the update.
2. **Correct anything the new evidence shows to be inaccurate**, including the posted sensitivity figures (TH-01) or the RISE description (AN-02). Say so explicitly in the response ("In our initial response we stated X; on re-derivation the correct value is Y").
3. Structure for each CW-XX and QA-XX (QA items may be merged with their CW, as in the initial rebuttal):

   ```
   ### CW-XX: <title>
   **Response** — concise scientific answer to the original concern.
   **Additional Validation** — what was done (pre-registered or exploratory, n, seeds, arms).
   **Results** — verified numbers only; a compact table where useful; original vs new results clearly labelled.
   **Interpretation** — how this addresses the concern and what limitation remains.
   ```

4. **Writing requirements:**
   - Open with a brief acknowledgment.
   - Write in the authors' collective voice ("we").
   - Respond to every CW and QA.
   - Include no internal execution details (no paths, hashes, GPU names, agent references).
   - Cite no fabricated references.
   - Acknowledge unresolved limitations.
   - State outcomes plainly even when unfavourable (e.g., "the pre-registered dose-response test did not support a downstream concentration effect; we have therefore restricted the claim to the training-set distribution").
5. **OpenReview format:**
   - Markdown with `$…$` math.
   - Split into parts of ≤ 5,000 characters each, measured programmatically; report the counts at the end of the file in an HTML comment.
   - Also produce a short (≤ 2,500 characters) "Summary of revisions" post suitable for the general thread.
6. Do **not** post anything. The author reviews and submits.

---

## 9. Phase 6 — Final scientific audit

Create **`STUDENT_RESULTS/FINAL_SCIENTIFIC_AUDIT.md`**. Perform the audit independently of the drafting: re-open the artifacts, don't trust the summaries.

For each of CW-01…CW-04 and QA-01…QA-04, answer:
- Was the concern fully understood?
- Was the promised analysis executed (list each commitment from Section 1.4 with done/not done)?
- Are the results scientifically valid?
- Does the evidence directly address the concern?
- Are the numbers reproducible from saved artifacts?
- Are the mathematical claims justified?
- Are the manuscript references accurate (section, table, figure numbers against the compiled revised PDF)?
- Are the conclusions appropriately qualified?
- Is the final rebuttal consistent with the initial one, with any corrections flagged?

Classify each concern as **FULLY ADDRESSED / SUBSTANTIALLY ADDRESSED / PARTIALLY ADDRESSED / UNRESOLVED**, with an explicit explanation for anything below FULLY.

End with a **commitment ledger**: every "we will / we plan" from Appendix A, mapped to what was delivered.

---

## 10. Required output structure

```
ICLR2027_REBUTTAL/
├── 01_INITIAL_REBUTTAL_FOR_SUBMISSION.md        (provided; do not edit)
├── 02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md     (provided; do not edit)
├── 03_STUDENT_AGENT_EXECUTION_INSTRUCTIONS.md   (this file)
└── STUDENT_RESULTS/
    ├── FINAL_UPDATED_REBUTTAL.md
    ├── RESULTS_SUMMARY.md
    ├── EXPERIMENTAL_EVIDENCE.md
    ├── EXECUTION_STATUS.md
    ├── FINAL_SCIENTIFIC_AUDIT.md
    ├── CODE_CHANGES.patch          (git diff of rebuttal-RL5B vs base commit; if no code
    │                                changed, a file stating "No code changes were necessary")
    ├── prereg/                      (EQ.md, CDR.md, OP.md + commit hashes)
    ├── revision/                    (AD-PCHGS-revised.tex, reference.bib, manuscript.diff)
    ├── analysis/                    (all analysis scripts)
    ├── EXPERIMENT_LOGS/             (environment.txt, per-task logs, per-run configs)
    ├── RESULT_TABLES/               (CSV + MD + TeX fragments, generated by scripts)
    └── FIGURES/                     (PDF/PNG, generated by scripts)
```

**Every path referenced in any Markdown file must exist.** Before finishing, run a link checker: a script that extracts the paths from all .md files and asserts that they exist, and save its output to `EXPERIMENT_LOGS/path_check.log`.

## 11. Final report to the corresponding author

When done, print and save to `EXECUTION_STATUS.md` (top section):
1. Tasks per status.
2. GPU-hours used.
3. The verdicts of EXP-01 and EXP-02 in one sentence each.
4. Any correction to the posted initial rebuttal.
5. Concerns not FULLY ADDRESSED and why.
6. Items needing the author's decision (title, compute beyond budget, BLOCKED inputs).

---

## Appendix A — Initial rebuttal as posted (verbatim)

The corresponding author posts this text before your work begins. It is the reference against which consistency is checked in Phases 5–6.

## Response to Reviewer RL5B — Part 1/4

We thank the reviewer for a careful evaluation and for criticisms precise enough to act on. We are glad the reviewer found the same-shape controls and the CHAMELEON audit useful. **We agree with the substance of all four weaknesses.** For each one, we state what the submitted manuscript already shows, where our wording went further than the evidence, and what additional analysis or controlled experiment we plan. This response reports **no new results**. Anything we add during the discussion period will be posted separately, whatever the outcome.

#### CW-01 / QA-01: Absence of evidence vs. evidence of equivalence

**Reviewer Concern**

> For the primary comparison C10−B, the reported difference is [$+0.0024$], with a confidence interval of [$[-0.0020, +0.0067]$]. This interval does not establish equivalence within the proposed margin of [$\pm 0.005$]. The results support a lack of reliable evidence for an advantage, not the stronger conclusion that uncertainty guidance has no meaningful effect.

> *QA-01:* Could the primary confidence intervals and equivalence-test results be presented more prominently, with a clear distinction between failure to detect an effect and evidence of equivalence?

**Response**

We agree, and the manuscript's own numbers support the reviewer's reading. On the primary cell (SINet, COD10K-test, eight seeds), $\Delta(\mathrm{C10}-\mathrm{B}) = +0.0024$ and the post-hoc interval is $[-0.0020, +0.0067]$ (Sec. 3.1). The upper limit is above the $+0.005$ margin. Consistently, the equivalence test in Sec. 3.2 is **not** significant for this contrast ($p = 0.101$). The only targeting-versus-random contrast that is equivalent at the margin is on NC4K.

The evidence therefore supports two statements:
- (a) There is no detectable advantage under the pre-registered rule.
- (b) An advantage as large as the reference effect ($+0.0142$) is excluded on the primary cell.

It does **not** exclude advantages between roughly $+0.005$ and $+0.0067$.

The sensitivity of the pre-registered rule points the same way. The rule declares an effect only when $\Delta > 2\hat\sigma = 0.0069$. With $\hat\sigma \approx 0.00345$ and $n = 8$ per arm, the standard error of a difference of means is about $\hat\sigma\sqrt{2/8} \approx 0.0017$. Under a normal approximation:
- A true effect of $0.005$ would clear the bar with probability only about $0.14$.
- The reference effect would clear it almost surely.
- The effect the rule detects with 80% probability is about $0.008$. The sign-agreement condition can only lower these probabilities.

So the rule is suited to detecting reference-size effects. It cannot rule out effects at the margin. Wording such as "no score of any quality helped here" (Sec. 3.1) and the title's "doesn't help" overstate this, and we will correct them.

**Planned revisions and validation**
1. **Wording.** We will revise the abstract, introduction, Sec. 3.1 and the conclusion so the downstream claim reads: no detectable advantage; reference-size effects excluded on the primary cell; smaller effects not excluded. We also plan to revise the title accordingly.
2. **Main-text table (QA-01).** We will add a table reporting, for all 16 eight-seed contrasts, $\Delta$, its 95% interval, the 90% interval used by TOST, the TOST $p$-value, and one of three labels: *not detected*, *equivalent within $\pm0.005$*, or *neither*. The text will define these categories explicitly.
3. **Re-derivation.** We will recompute every interval and TOST statistic from the per-run metrics and report the rule's sensitivity analytically. Welch remains the primary analysis, as in the manuscript; a seed-paired analysis is a sensitivity check.
4. **Confirmatory campaign.** We plan a separately pre-registered confirmatory campaign for the primary contrast (arms B, C10 and CSHUF). It will use fresh seeds, and its sample size will be fixed in advance by a power analysis for TOST at $\pm 0.005$. We will **not** add seeds to the existing campaign, because doing so after seeing its result would be optional stopping. The outcome will be reported whether or not equivalence is established.

---

## Response to Reviewer RL5B — Part 2/4

#### CW-02 / QA-02: Distributional change vs. downstream explanation

**Reviewer Concern**

> The distributional analyses show that concentrated allocation changes the training-set composition, but this does not establish that concentration explains downstream performance changes. The post-hoc boundary-metric results are suggestive but are not consistent across both architectures.

> *QA-02:* What evidence supports the claim that budget concentration explains downstream performance, rather than merely changing the training-set distribution?

**Response**

We agree that these are two different claims, and that the manuscript establishes the first much more firmly than the second. The current evidence is as follows.

- **Distributional (established).** Set separation is reproduced by every rule that preserves concentration, and it collapses only when concentration is removed (Fig. 2a). The real signal adds only $+0.0073$ in Cohen's $d$ over its own shuffle (Sec. 3.2).
- **Downstream, $S_\alpha$.** The three same-shape arms cannot be distinguished (Fig. 2b). This shows that *direction* is not detectably consequential. It does **not** show that *concentration* is.
- **Downstream, boundary metrics.** On SINet, C10−B and CINV−B both exceed their bar ($1.37\times$ and $1.34\times$), while the direction contrasts do not. However, this analysis is post hoc and binarised, and it does not resolve on SINet-v2.

At most, then, the evidence shows that concentrated arms differ from random on one architecture and one post-hoc metric family, irrespective of direction.

Three further limitations strengthen the reviewer's point:
1. **Shared images.** The same-shape arms share roughly half of their injected images (452–511 of 1000 differ between any pair; Appendix B). "Concentrated vs. random" is therefore partly confounded with *which images* are shared.
2. **Single permutation.** CSHUF is one permutation. CSHUF−B therefore mixes the effect of the allocation's shape with the effect of one particular random direction. Identifying a pure shape effect requires averaging over many permutations.
3. **Pseudo-label counts.** The number of pseudo-labelled target images differs by arm (means 1977–2025; Appendix, controls section).

**Planned revisions and validation**
1. **Claim restructuring.** We will separate the claims explicitly in the abstract, Sec. 3.2 (including its heading) and the discussion:
   - *established:* the training-set distribution effect;
   - *established:* no detectable downstream effect of direction;
   - *hypothesis only:* concentration as a downstream explanation, with post-hoc support on one architecture.
2. **Concentration dose-response campaign.** We plan a pre-registered campaign that holds the budget at $N = 1000$ and varies concentration across at least three levels (cluster-uniform; the committed $\tau = 1.0$ shape; a more concentrated $\tau$). Each level will be realised by several independent random permutations of the cluster scores, constrained to low image overlap with C10. This averages out direction and varies image identity.
   - Primary metric: Boundary-IoU on SINet·COD10K, fixed before any run.
   - Secondary metric: $S_\alpha$.
   - Replication: SINet-v2.
   - Decision: we will describe concentration as a downstream explanation only if the outcome changes with concentration consistently across permutations. Otherwise we will restrict the claim to the training-set distribution.
3. **Re-scoring existing runs.** We will re-score all existing eight-seed runs on both architectures with the boundary metrics, with pseudo-label count and image overlap as covariates. This analysis will be labelled exploratory.

---

## Response to Reviewer RL5B — Part 3/4

#### CW-03 / QA-03: Absolute performance and protocol-matched baselines

**Reviewer Concern**

> The reported C10 results achieve approximately [value] ([value]) on COD10K-test and [value] ([value]) on NC4K, below the reported unsupervised RISE results of [value] and [value], respectively, and standard supervised SINet-v2 results of approximately [value] and [value]. These results are not directly comparable because the training protocols differ. And the gap raises questions about the effectiveness of the overall pipeline. Stronger protocol-matched baselines and a clearer explanation of the performance gap are needed.

> *QA-03:* Can the performance gap be explained through protocol-matched comparisons with supervised and unsupervised COD baselines?

**Response**

We agree that the protocols differ and that the gap needs to be explained. The protocols differ in three ways:

- **Our pipeline.** It follows the synthetic-to-real protocol of S2R-COD. The only labelled training data are 4447 synthetic composites rendered by LAKE-RED, whose foregrounds come from a salient-object dataset (HKU-IS). The 4040 real COD10K/CAMO training images are used **without masks**.
- **Supervised SINet-v2.** It is trained on the real masks of those same images.
- **RISE (ICCV 2025).** It uses no annotations, but it relies on a different representation (frozen self-supervised ViT features with dataset-level retrieval) and a different training pipeline.

The gap to supervised SINet-v2 therefore mainly reflects the absence of real labels. The gap to RISE mixes differences in representation and method. Within its own protocol, our base pipeline reproduces the published method it builds on ($0.7030 \rightarrow 0.7172$; Sec. 1.1).

The reviewer's underlying concern is still valid and bears on generality: at a low operating point, there may be little that *any* allocation can improve. The manuscript addresses this only partly. The positive control shows the design detects a $+0.0197$ gap at this operating point (Table 2). But the manuscript reports no protocol-matched external baselines, and it does not discuss RISE, which we will add.

**Planned revisions and validation**
1. **Protocol table.** For each method we will list the labels used, the target images used, the backbone and its pretraining, the generator, and $S_\alpha$, $E_\phi$ and $F_\beta^w$ on COD10K-test and NC4K. All published values will be verified against the original papers.
2. **Protocol-matched evaluation in our codebase and scorer:**
   - SINet and SINet-v2 trained with the real masks of the same 4040 images (a labelled upper reference);
   - released SINet-v2 and RISE predictions or checkpoints, re-scored with our evaluation code, to separate scorer differences from training differences;
   - our source-only and reproduced S2R-COD baselines.
3. **Gap decomposition.** We will decompose the gap into three components: label supervision, representation/backbone, and reproduction differences.
4. **Higher operating point (if compute permits).** We plan a pre-registered replication of C10, B and CSHUF at a higher operating point: the base pool plus a fixed small fraction of real labelled target images. This tests whether the null is specific to the low-performance regime. If it cannot be completed in time, we will say so.

---

## Response to Reviewer RL5B — Part 4/4

#### CW-04 / QA-04: Fixed generator, limited foreground pool, scope of conclusions

**Reviewer Concern**

> The method relies on a fixed generator and a limited foreground pool, with synthetic diversity primarily coming from background changes. Weak clustering structure and limited foreground diversity may constrain the method from the outset. Consequently, the results provide limited evidence about uncertainty-guided synthetic-data generation more generally.

> *QA-04:* Can the conclusions be better bounded to the specific generator, foreground pool, and training setup evaluated?

**Response**

We agree. The manuscript documents these constraints but does not carry them into its headline claims. The existing evidence (Sec. 3.3) is:
- the render set is a bijection onto the base foregrounds, so each injected render re-uses a foreground already in the base pool with a new background;
- none of 8885 traced objects was regenerated;
- synthetic images cover $0.13$–$0.54$ of the real target manifold, against $0.71$–$0.75$ for the generator's own source photographs;
- $k$-means silhouette peaks at $0.16$;
- only about a fifth of the endpoint's structural-error variance lies between clusters.

Appendix A states that the null is bound to LAKE-RED, and the discussion lists the conditions under which the idea could still work.

We read these constraints as part of the result: they explain why this pipeline could not express an allocation effect. But we agree that they limit what the result covers. The experiment tests uncertainty-guided **allocation over a fixed, background-varied render pool**, not uncertainty-guided generation in general. The generator renders its pool once, offline, and never sees the score (Sec. 2). "Targeted synthetic data" in the title therefore overstates the scope.

One part is less tied to the generator: the between-cluster share of error is computed on the target data and endpoint errors, not on the synthetic pool. It therefore bounds the leverage of *any* cluster-level allocation in this setting, including the oracle arm.

**Planned revisions and validation**
1. **Scope statement.** We will add an explicit scope statement to the abstract, introduction, conclusion and title. It will name the LAKE-RED generator, the 4447-foreground pool, background-only variation, $k = 75$ clusters over frozen self-supervised features, the two SINet architectures, two-round self-training, and $N = 1000$.
2. **Quantifying the foreground constraint.** We will report:
   - distinct foregrounds and foreground reuse per arm;
   - the share of render-embedding variance explained by foreground identity versus background;
   - for each target cluster, the distance to the nearest available foreground.
3. **No claims about other generators.** Replacing the generator is beyond what we can do rigorously within the discussion period, so we will list it as a limitation rather than offer a weaker substitute.

**Summary.** We will recalibrate the claims (CW-01, CW-04), separate distributional from downstream conclusions (CW-02), and add protocol-matched baselines (CW-03). We will also run the confirmatory, dose-response and baseline experiments described above and report their results as they are, including unfavourable ones. We thank the reviewer again; these points will make the paper's claims more accurate.

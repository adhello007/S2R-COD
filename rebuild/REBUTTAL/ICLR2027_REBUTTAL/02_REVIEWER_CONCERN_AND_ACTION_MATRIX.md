# Reviewer dypE — Concern-to-Action Matrix

## Inputs, scope, and exact text policy

- Manuscript: `AD-PCHGS-250926.tex` (uploaded version); bibliography: `reference.bib`.
- Reviewer report: `dypE.md`. This report has **2 critical weaknesses (CW-01, CW-02)** and **3 author questions (QA-01–QA-03)**. All substantive subissues are enumerated below.
- The verbatim reviewer comments below are reproduced from `dypE.md`, including the reviewer's original wording. The 5,000-character paste-ready initial rebuttal uses short verbatim excerpts; this matrix and the standalone student guide preserve the full comments.
- This is a plan and evidence map, **not** a record of new experiments. Manuscript-reported results have not been independently verified against raw logs supplied with this conversation.

## Triage

| Concern | Main issue | Priority | Mapped tasks |
|---|---|---|---|
| CW-01 | Statistical sensitivity and bounded null | P0 | TH-01, AN-01, AN-02, EXP-01, DOC-01 |
| CW-02 | Concentration hypothesis, architecture, and generator scope | P0/P1 | TH-02, AN-03, AN-04, EXP-02, EXP-03, DOC-01 |
| QA-01 | Practical scale and paired eight-seed inference | P0 | TH-01, AN-01, DOC-01 |
| QA-02 | Limited injection differences and foreground-diversity counterfactual | P1 | AN-02, AN-04, EXP-01, EXP-03, DOC-01 |
| QA-03 | CHAMELEON leak paths under different evaluation protocols | P0 | AN-05, DOC-02 |

## Point-by-point evidence and action records

### CW-01: Statistical sensitivity and bounded null

**Priority:** P0

**Exact reviewer comment:**

> 1. Statistical Sensitivity and Interpretation of the Negative Result
>
> The difference between targeted and random training is quite small. Synthetic images make up only 18.4% of the training set, and about half are shared across different groups. As noted in Appendix C, only around 8.8% of the full training set actually differs. This may make small improvements hard to detect.
>
> The authors also use twice the pooled standard deviation as their decision rule, which is more conservative than using the standard error. The eight-seed comparison shows a difference of +0.0024, with a 95% confidence interval of [-0.0020, +0.0067]. This rules out the reference improvement of +0.0142, but smaller gains are still possible. Also, the targeting-versus-random comparison does not pass the equivalence test at ±0.005.
>
> Overall, the results show that this method does not bring a large improvement in the tested setting. However, they do not fully rule out smaller gains. I think the paper should make this limitation clearer.

**Distinct scientific subissues:**

- CW-01a: 1,000/5,447 = 18.4% injections; about 48% of injections and only ~8.8% of all training pairs differ.
- CW-01b: pre-registered two-pooled-SD/sign-consistency gate is not a standard error, precision interval or equivalence criterion.
- CW-01c: eight-seed C10–B +0.0024 with 95% CI [−0.0020,+0.0067] excludes +0.0142 but not smaller benefit.
- CW-01d: targeting versus random did not achieve equivalence at ±0.005 (p=0.101).
- CW-01e: language implying absence of small gains would exceed the evidence.

**Relevant manuscript evidence:** Methods §2 (label sec:method; detection rule), §3.1 “Does Targeting Beat Random” (sec:null), Table “Trained comparison” (tab:trained), §3.2 (sec:concentration), Appendix “Decisive Gap” (app:diag), paragraph “How much the trained comparison is attenuated.” Main B/C10 are equal-sized fixed-budget arms. Eight-seed schedule includes seeds 42,43,45–50.

**Sufficiency of existing evidence:** Existing manuscript supports a bounded interpretation and cites an unpaired/post-hoc interval; paired seed differences, raw variance, true per-seed exposure, and sensitivity curves cannot be verified from the uploaded TeX alone.

**Rebuttal argument:** Concede limited power for small changes; distinguish pre-registered per-run variability rule from inferential confidence interval; reference +0.0142 is an observed comparator, not a universal COD MCID; ±0.005 is a post-hoc exploratory margin. Preserve all negative/inconclusive results.

**Required experimental, mathematical, or analytical work:** TH-01, AN-01, AN-02, EXP-01, DOC-01

**Acceptance and independent verification:** Reproduce each per-seed metric from logs; verify matched seed/run pairing; check paired CI/TOST computations independently; compare realized unique set overlap and pseudo-label/exposure counts; audit wording and manuscript citations.

### CW-02: Concentration hypothesis, architecture, and generator scope

**Priority:** P0/P1

**Exact reviewer comment:**

> 2. Downstream Validation and Generalizability of the Concentration Hypothesis**
>
> The geometric analysis shows that concentrating samples changes the selected dataset, even when uncertainty scores are shuffled or reversed. However, this does not mean that concentration improves detection performance.
>
> In the post-hoc boundary-metric analysis, both targeted and reversed allocation perform better than random allocation on SINet. However, these gains are much smaller on SINet-v2. This suggests that the effect of concentration may depend on the model architecture.
>
> The experiments also use a fixed pool of LAKE-RED images generated offline. Since no new foreground content is generated, uncertainty guidance can only select from existing samples. This may limit its benefits, especially when the synthetic data does not cover the real data distribution well.
>
> Therefore, the negative results may be partly caused by the generation setup. It is still unclear whether the same conclusion would hold with better synthetic data or an adaptive generation process.

**Distinct scientific subissues:**

- CW-02a: a classifier that distinguishes selected sets shows geometric/compositional difference only; it is not a downstream performance effect.
- CW-02b: post-hoc SINet boundary gains appear for both correctly targeted and reversed arms, weakening any direction attribution.
- CW-02c: SINet-v2 does not replicate a resolved boundary benefit; architecture interaction needs examination, not an inference from significance alone.
- CW-02d: LAKE-RED background-only re-rendering of an offline foreground pool restricts coverage and cannot test an adaptive generator.
- CW-02e: the null may be conditional on training/generation pipeline, not general to every uncertainty-guided method.

**Relevant manuscript evidence:** §3.2 “Concentration, Not Targeting” (sec:concentration), Fig. fig:thesis, §3.3 “Why It Fails” (sec:why), §4 Discussion (sec:discussion), Methods (sec:method; offline generator), Appendix “Boundary metrics” (app:diag) and missing externally included table_subgroup_metrics.tex / appendix_coverage.tex. Embedding effective-rank ratio 0.634; 8-seed post-hoc Boundary-IoU on SINet ~1.37× bar (C10–B) and ~1.34× (CINV–B), without corresponding SINet-v2 detection.

**Sufficiency of existing evidence:** Existing evidence discriminates selection geometry from trained scores, but cannot support a general causal concentration benefit, full architecture invariance, or adaptive/new-foreground generality. Some exact supplementary tables are unavailable in the upload.

**Rebuttal argument:** State geometry result distinctly from unproven downstream causal benefit; stratify by architecture; call boundary findings exploratory; restrict scope to fixed offline LAKE-RED pool.

**Required experimental, mathematical, or analytical work:** TH-02, AN-03, AN-04, EXP-02, EXP-03, DOC-01

**Acceptance and independent verification:** Check exact concentration summary statistics/quotas, binarization thresholds and paired architecture interaction; independently recompute foreground coverage; prospective training with matched controls only where feasible; no claims about untested generators.

### QA-01: Practical scale and paired eight-seed inference

**Priority:** P0

**Exact reviewer comment:**

> 1. How well do the results rule out smaller improvements from uncertainty-guided targeting?
>
> The eight-seed results rule out large improvements, but the targeting-versus-random comparison does not pass the equivalence test at ±0.005. Could the authors clarify what level of improvement they consider meaningful for COD? Also, could they provide a paired analysis using the same random seeds? This would help clarify whether the negative result also applies to smaller but useful improvements.

**Distinct scientific subissues:**

- QA-01a: clarify meaningful performance improvement (reference +0.0142 versus smaller possible gains).
- QA-01b: provide a genuine matched-seed, paired analysis of C10 versus B.
- QA-01c: interpret failure of equivalence at ±0.005 correctly and avoid claiming small benefits are excluded.

**Relevant manuscript evidence:** §2 Related Work reference S_alpha +0.0142 (0.7030 to 0.7172), §3.1 +0.0024 95% CI, §3.2 post-hoc TOST (p=0.101), Appendix “Seeds and what was held constant” (app:method), missing included table_tost_equivalence.tex.

**Sufficiency of existing evidence:** Reference and existing unpaired interval present; per-seed values, paired CI, paired TOST and an externally validated meaningful-difference threshold are not established from uploads.

**Rebuttal argument:** Frame +0.0142 as study comparator and ±0.005 as sensitivity margin; compute matched-seed paired uncertainty with proper conditions and report interval relative to several improvement thresholds.

**Required experimental, mathematical, or analytical work:** TH-01, AN-01, DOC-01

**Acceptance and independent verification:** Same-seed manifest join, independent numerical check, no paired inference unless eight matched seeds and endpoint consistency are evidenced.

### QA-02: Limited injection differences and foreground-diversity counterfactual

**Priority:** P1

**Exact reviewer comment:**

> 2. How much do the limited training-set differences and synthetic data diversity affect the conclusion?
>
> As noted in Appendix C, only about 8.8% of the training pool differs between the compared groups. The synthetic data also have limited coverage of the real data distribution. Would the same conclusion hold if the training sets had larger differences or if the generator could produce more diverse foreground content? Additional experiments or discussion on these limitations would help support the generality of the results.

**Distinct scientific subissues:**

- QA-02a: effective ~8.8% contrasting training data may hide small effects.
- QA-02b: larger realized contrast requires proof rather than increasing N by assumption.
- QA-02c: more diverse foregrounds or online adaptation are absent; separate feasible within-pool tests from untestable generator counterfactuals.

**Relevant manuscript evidence:** Methods source pool 4,447, target pool 4,040, +1,000 injected images; Appendix “How much the trained comparison is attenuated” (app:diag), “Allocation sweeps” (app:method) N={250,500,1000,2000,3000,4447}, §3.3 “Why It Fails”, Appendix app:coverage included file absent.

**Sufficiency of existing evidence:** Existing attenuation and kNN coverage analysis support limitation; larger-contrast retraining and genuinely novel-foreground tests not verified or present.

**Rebuttal argument:** Preflight overlap at N=2000/3000 (or feasible choices), train matched-budget paired controls only when contrast is demonstrably larger, audit existing pool coverage; present new foreground synthesis as conditional, not already accomplished.

**Required experimental, mathematical, or analytical work:** AN-02, AN-04, EXP-01, EXP-03, DOC-01

**Acceptance and independent verification:** Manifest-verified unique foreground IDs, train/target split, contrast fraction, comparable optimization, independent metric recomputation; explicit BLOCKED status if no generator or new legal foreground dataset.

### QA-03: CHAMELEON leak paths under different evaluation protocols

**Priority:** P0

**Exact reviewer comment:**

> 3. How does CHAMELEON contamination affect existing COD evaluation results?
>
> The paper identifies 50 overlapping images, including 44 that also appear in COD10K-train. Could the authors clarify how these overlaps may affect common COD training and evaluation protocols? In particular, it would be useful to distinguish between supervised training, unlabeled target-domain adaptation, and checkpoint selection. This would help readers better understand the practical impact of the contamination finding.

**Distinct scientific subissues:**

- QA-03a: lower bound of 50/76 CHAMELEON overlaps, 44 with COD10K-train, distinguish exact byte hash from visual duplicates.
- QA-03b: supervised training on evaluation photographs is leakage; unlabeled target use is transductive exposure but not automatically training with test labels.
- QA-03c: checkpoint selection overlap uses a third pathway, separate from train/test membership.
- QA-03d: 16 unmatched cases remain unchecked; no measured score inflation should be claimed; multiple CHAMELEON mask releases change metrics.

**Relevant manuscript evidence:** §3.4 “CHAMELEON Is Mostly Training Data” (sec:contamination), Fig. fig:cham, Appendix app:chamext (Tier A 41/Tier B 9, 44 COD10K; exact hash zero against TRAINING only), app:masks (polarity and MAE variant; 3 images byte-identical CAMO-250 checkpoint split), ethics/reproducibility statements. Manuscript explicitly says difficulty analysis did NOT show leaked-subset score advantage.

**Sufficiency of existing evidence:** Manuscript supports protocol-risk classification; actual per-pipeline exposure and causal performance impact require model/data manifests and cannot be inferred from duplicate counts alone.

**Rebuttal argument:** Explain direct supervised reuse, unlabeled target transduction, and checkpoint-selection contamination separately; report lower-bound matches and unchecked cases; prefer independent COD10K-test and NC4K with explicit image/mask-release disclosures.

**Required experimental, mathematical, or analytical work:** AN-05, DOC-02

**Acceptance and independent verification:** Re-run duplicate detector with known-answer test and pair-manifest adjudication if datasets available; compute exact intersections with source/target/validation/test manifests; trace training checkpoint-selection rule; no claimed inflation without a legitimate no-leak counterfactual.

## Shared methodological safeguards and source limitations

1. **No logical “proof of no effect” from a pooled-SD bar.** The manuscript’s twice-pooled-SD rule is a frozen descriptive decision threshold; inferential statements must use valid uncertainty intervals and carefully specified equivalence margins. Not meeting an equivalence test is neither a significant difference nor evidence for equivalence.
2. **No causal overreach.** Holding allocation concentration constant changes where samples are drawn; subsequent pseudo-labels also vary across arms as a consequence of first-round training (Appendix app:controls). Separate measured total effects from any unverified direct-effect mechanisms. The offline corpus does not establish results for adaptive foreground generators.
3. **No architecture cherry-picking.** Report SINet and SINet-v2, both COD10K-test and NC4K, and the post-hoc character of boundary metrics and equivalence tests. A statistically significant result in one architecture and non-significant in another is not itself a demonstrated interaction.
4. **Dataset leakage is protocol-dependent.** Report intersection with supervised-source, unlabeled-target, checkpoint/validation, and independent test pools separately. Keep 50 confirmed/16 unchecked distinct; never equate image exposure with observed metric inflation.
5. **Missing supporting TeX inputs:** `math_commands.tex`, `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`, `appendix_tables.tex`, `table_cluster_composition.tex`, `appendix_coverage.tex`; graphics, raw logs, source repository and data are not uploaded. Consequently, some table-specific values and log-level assertions remain to be verified by the student's agent. Bibliography integrity check against `reference.bib`: all 39 unique cited keys found among 43 bibliography entries (syntax-level check only; no external semantic verification). The anonymized source URL in the manuscript was not retrievable through the current browser.

# ICLR 2027 — Single-Student Autonomous Research-Agent Execution Guide

**For one student and their autonomous research/coding agent.** This document can be circulated without the master preparation prompt. It contains the reviewer's full concerns in Appendix A, the author's initial response in Appendix B, and the complete verification/action matrix in Appendix C. **This is an execution specification, not evidence that new experiments have been performed.**

## 0. Mission, authority, and non-negotiable boundaries

You are the single student-agent executing the follow-up work for an ICLR 2027 submission entitled **“Concentration, Not Uncertainty: Why Targeted Synthetic Data Doesn't Help Camouflaged Object Detection.”** The corresponding author has already prepared an initial reviewer response. Your task is to **execute all feasible studies below and deliver a verified, reviewer-ready, post-experiment response**. Do not simply make another plan and stop.

1. **Never post to OpenReview or impersonate the corresponding author.** Provide files for their review and authorization.
2. Work on a separate Git branch or copy; preserve the submitted `.tex`, raw data, configurations, checkpoints, and logs. Do not overwrite historical results or silently modify the original findings.
3. Inspect the actual repository before selecting entrypoints, configurations, or file paths. Paths identified in the paper are **candidates**, not guarantees that the repository contains them; never assert an artifact exists until found.
4. Do not fabricate missing experimental results; label tasks `BLOCKED`, `FAILED`, `INCONCLUSIVE`, or `PARTIALLY VERIFIED` as appropriate. Never drop negative findings or selectively report successful seeds/thresholds/architectures.
5. Work autonomously on reversible tasks (inspection, creation of new scripts/files, runs in fresh directories). Ask permission for truly destructive operations, costly external services beyond existing permissions, downloads with unknown licensing, or disclosure of credentials. Record blockers and continue independent tasks.
6. All claims in the final response must be linked to **actual output artifacts and commands**. Every value should be recomputable by a separate audit script. No fake citations, proofs, or inference of equivalence from a nonsignificant difference.
7. Preserve original preregistered campaigns. Label **all new analyses and reruns post-review, exploratory**, including the paired sensitivity and any new dose/diversity experiments, unless a documented preregistration proves otherwise.

## 1. Scientific context: what the submitted manuscript actually tests

- **Problem:** under a fixed synthetic-data budget, does uncertainty-guided placement of synthetic samples improve camouflaged object detection over an equally sized random synthetic sample set?
- **Design:** 4,447 base labeled image–mask pairs; 4,040 unlabeled real target images (3,040 COD10K plus 1,000 CAMO); two-round student/EMA-teacher training; synthetic LAKE-RED images rendered **once offline**, not generated adaptively during training; 75 k-means clusters of L2-normalized self-supervised image embeddings. Student–teacher edge-aware uncertainty ranks clusters; softmax allocation at temperature 1.0 assigns a 1,000-image injection budget, then selects nearest masked foreground cutouts.
- **Arm definitions:** A0 no injection; A2 +1,000 real photos; B +1,000 randomly sampled renders; C10 +1,000 uncertainty-targeted renders; CSHUF the **same concentration/quotas** with cluster scores permuted; CINV quota ranking reversed; CORACLE quota allocation by *endpoint ground-truth error* solely as an **oracle diagnostic**, never a deployable algorithm; BFX/C10FX unpinned training-schedule controls; MT positive-control comparator.
- **Model/metrics:** SINet (batch 16, 40 epochs) and SINet-v2 (batch 32, 100 epochs), Adam 1e-4, 352×352 inputs; EMA momentum 0.996; primary endpoint S-measure S_alpha at alpha=0.5 on COD10K-test, secondary independent endpoint NC4K; checkpoint selection on CAMO-250 MAE; post-hoc Boundary-IoU and other boundary analyses must remain exploratory. Paper reports 103 trained runs overall, but those are **manuscript claims**, not newly reverified results.
- **Seed records:** committed {42,43,45}; separate eight-seed expansion {42,43,45,46,47,48,49,50}. In the eight-seed SINet/COD10K primary cell, C10−B = +0.0024, post-hoc 95% CI [−0.0020,+0.0067]; preregistered per-run pooled-SD gate 2 sigma_hat=0.0069; exploratory targeting-versus-random TOST at ±0.005 did **not** show equivalence (p=0.101). The +0.0142 reference effect is **study-specific**, not an established minimum clinically/practically meaningful COD delta.
- **Contrast and scope:** 1,000/5,447=18.4% nominal synthetic proportion; about 48% of injection differs across compared arms, ~8.8% of the *unique training pool* differs. The pinned schedule can further reduce realized exposure. Fixed LAKE-RED content reuses foregrounds; the manuscript finds kNN recall 0.13–0.54 for synthetic versus real target and makes **no** claim about truly novel, adaptively generated foregrounds.
- **Geometry versus performance:** same-shape concentration controls explain separability of selected synthetic sets; they do not establish that concentration *improves trained S-measure*. The paper's exploratory Boundary-IoU signal appears in SINet, not convincingly in SINet-v2, requiring an explicit architecture interaction analysis and careful endpoint distinction.
- **CHAMELEON audit:** 50/76 photographs overlap public COD10K/CAMO training pools (41 dimension-matched re-encoded + 9 geometric matches), including 44 partners in COD10K-train; 16 remain **unchecked**, not verified clean. Exact file hashing misses overlap with the training pool; three CHAMELEON images are separately byte-identical with CAMO-250 (checkpoint-selection split), not with the counted training pool. Different ground-truth mask releases change MAE; overlap alone does **not** establish actual score inflation.
- **Two types of controls must stay separate:** uncertainty **direction** versus quota **concentration**; duplicated **images** versus labels and checkpoint-selection use. Treat source/target/validation/test splits and supervision modes separately.

### Reproduction anchors in the submitted TeX

| Scientific statement | Source location/label | Traceable entries referred to in manuscript |
|---|---|---|
| Edge-aware score and quota rule | Eq. `eq:es`, Eq. `eq:alloc`; `sec:method`, `app:method` | k=75, temperature=1, a=0.9, b=0.3, N=1000 |
| Arm identity and concentrations | `tab:arms`, `fig:arms`, `app:method` | original allocation manifests; shuffling must preserve quota multiset |
| Trained null and seed expansion | `tab:trained`, `tab:allcells`, `sec:null`, `app:diag` | `abc_verdict.json`, campaign `se/`, `or/`, `fx/`, PC; verify paths |
| Post-hoc CI, equivalence, and boundary | `sec:concentration`, `app:diag`, imported `table_tost_equivalence.tex` and `table_subgroup_metrics.tex` | imports may be absent; do not invent their contents |
| Concentration geometry and failure mechanisms | `sec:concentration`, `sec:why`, imported `appendix_coverage.tex`, `table_cluster_composition.tex` | published effective-rank/coverage claims need underlying logs |
| CHAMELEON duplicates and masks | `sec:contamination`, `app:chamext`, `app:masks` | Tier A detector, SIFT/RANSAC/warp, mask-release identities |
| Actual between-arm round-2 differences | `app:controls` | per-run pseudo-label means differ, so injection is not the sole realized difference |

**Potentially missing from the supplied materials:** `math_commands.tex`, `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`, `appendix_tables.tex`, `table_cluster_composition.tex`, `appendix_coverage.tex`, `figs/*`; full Git repository, training/selection scripts, original configs, run manifests, checkpoints, prediction arrays, rendered pool, duplicate pair list, benchmark image/mask releases. The corresponding author supplied only the manuscript `AD-PCHGS-250926.tex`, `reference.bib`, and review `dypE.md` for preparation; locate the missing items on your own machine and **list any that remain absent**. Do not guess their data. The prompt's older filenames `Rohit_PCHGR_250926.tex` and `v58c.MD` do not match these actual inputs.

## 2. Review concerns and unambiguous response commitments

All reviewer concerns and the full initial rebuttal occur **verbatim** in Appendices A and B. Use them as the source of truth. The abbreviated commitment ledger is:

| Reviewer ID | Specific initial-rebuttal commitment | Required task IDs | Urgency |
|---|---|---|---|
| CW-01 | Clarify limited power, 2-SD gate versus CI, ±0.005 non-equivalence; quantify paired sensitivity and training exposure | TH-01, AN-01, AN-02, EXP-01, DOC-01 | P0 |
| CW-02 | Separate geometry from downstream effects; architecture-aware boundary comparisons; audit offline diversity | TH-02, AN-03, AN-04, EXP-02, EXP-03, DOC-01 | P0/P1 |
| QA-01 | Clarify meaningful-effect interpretation, eight-seed paired contrasts and paired TOST | TH-01, AN-01, DOC-01 | P0 |
| QA-02 | Realized overlap/exposure; larger matched-budget contrasts **if preflight shows greater contrast**; diverse foreground feasibility | AN-02, AN-04, EXP-01, EXP-03, DOC-01 | P1 |
| QA-03 | Separate supervised, unlabeled/transductive and validation-selection paths; clarify lower bound and mask-release sensitivity | AN-05, DOC-02 | P0 |

**Scope of deliverable tasks:** **3 experiments** (`EXP-01`–`03`), **2 theoretical/statistical validations** (`TH-01`–`02`), **5 analyses** (`AN-01`–`05`), and **2 documentation tasks** (`DOC-01`–`02`). Experiments are conditional on available data, compute, and repository resources; analysis of existing runs is prioritized before retraining. Task verification must record every infeasible branch.

## 3. Discovery / audit setup — execute first (P0, no GPU required)

Create `ICLR2027_REBUTTAL/STUDENT_RESULTS/` with `EXPERIMENT_LOGS/`, `RESULT_TABLES/`, `FIGURES/`, and a **new isolated run directory** outside submitted originals. Record UTC timestamps, current Git revision, dirty tree status, root location, package-lock/environment metadata, model and dataset hashes, GPU model, CUDA/driver/PyTorch versions, CPU RAM, access/license restrictions, and feasible compute budget. Work on a new `rebuttal/dypE-validation` branch or a clearly timestamped working copy. Verify that selected copies of submitted manuscript/review/bib exactly match the author's versions; if different, save diffs and investigate. Do not assume the branch name or Git is available.

Commands below are *discovery examples*, not invented execution entrypoints:

```bash
pwd && git rev-parse HEAD && git status --short
find . -maxdepth 4 -type f \( -name '*verdict*.json' -o -name '*manifest*' -o -name '*prediction*' -o -name '*config*' -o -name 'table_tost_equivalence.tex' \) | sort
rg -n 'C10|CSHUF|CINV|CORACLE|Boundary.?IoU|chameleon|LAKE.RED' . --glob '*.py' --glob '*.json' --glob '*.md' --glob '*.yaml' --glob '*.yml'
```

If commands/tools differ on your system, use their safe equivalent. Inventory *actual* run lists and resolve their identities before deciding what needs to be rerun. The manuscript points to historical Git commits `065dac6`, `617a2e1`, `6efde9f`, `c2114af`, `b755aa9`; treat them as **unverified pointers** until present in your repository. Confirm preregistered instructions from commits rather than retrospectively editing them. Use existing environment managers rather than indiscriminately upgrading dependencies. Validate a cheap historical run/rescore first; never launch a large campaign until shape, data paths and checkpoint loading pass unit tests.

Create a machine-readable run manifest, preferably CSV/JSON with one record per run:

```text
campaign,architecture,endpoint,arm,seed,round,git_sha,config_sha,
dataset_manifest_sha,inject_manifest_sha,checkpoint_sha,prediction_sha,
source_count,target_count,injected_count,pseudo_count,steps_per_epoch,
checkpoint_selection_split,metric_code_sha,raw_log_path,metric_path,status
```

A result belongs to a cell only if all necessary run identifiers match exactly. Preserve per-image predictions and per-seed metrics where possible. Audit original versus new output provenance.

## 4. Dependency-aware execution schedule

1. **P0 first:** discovery → `TH-01`, `AN-01` (paired inference) → `AN-02` (actual contrast/exposure) → `TH-02` (causal claim limits) → `AN-05` (leakage paths). Execute independent CPU audits concurrently where practical.
2. **P0/P1 next:** `AN-03` and `EXP-02` (boundary re-score + architecture interaction), `AN-04` (coverage/diversity). `DOC-01` and `DOC-02` are updated as the corresponding evidence is verified.
3. **P1 controlled retraining, only if justified:** preflight `EXP-01` at larger budget and then matched training. `EXP-03` requires verified access to a *genuinely* diverse or adaptive-foreground generation method; otherwise it is `BLOCKED` with precise reason and no synthetic conclusion.
4. **P2 packaging/independent audit:** recompute summary tables; generate post-experiment rebuttal, limitations and code patch; run final scientific audit against all five concerns; deliver all files to the author, **without submitting**.

If blocked, record: task ID, missing item, attempted discovery/command, error, required resource, valid alternative, and what scientific conclusion remains unresolved. Continue on independent tasks rather than waiting for permission on routine reversible actions.

## 5. Fully specified tasks

### TH-01 — Statistical estimands, valid paired inference and equivalence (P0)

- **Addresses:** CW-01, QA-01. **Initial commitment:** “We will make these qualifications prominent and examine paired-seed sensitivity and realized data exposure without assuming their outcomes”; “We will report uncertainty against both scales and compute matched-seed C10–B differences, paired CIs, and paired equivalence tests from the existing eight-seed runs ... after checking run manifests.”
- **Question:** Does the available eight-seed evidence support an effect larger than +0.0142, a positive effect as small as +0.005, equivalence within ±0.005, or merely non-resolution? What does each uncertainty statement actually mean?
- **Inputs/dependencies:** Manuscript `sec:method`, `tab:trained`, `app:diag`, `app:method`; actual 8-seed run manifests/results for B and C10; seeds 42,43,45–50; full replication for each of two architectures × two endpoints, plus optional CSHUF/CINV.
- **Procedure:** Derive and document estimand D_i = S_alpha(C10, seed i) − S_alpha(B, seed i) for each architecture/endpoint. Confirm true matching of seeds, endpoints, data splits, checkpoint rules, metric version, and training budgets; matching seed **numbers alone** do not guarantee shared sampling randomness or strong paired gains. Compute mean D, SD(D), SE(D)=SD(D)/sqrt(n), t_(n−1) confidence interval, sign count, two-sided paired t-test (exploratory), paired bootstrap interval (if feasible), and an exact/permutation sign-flip sensitivity analysis clearly qualifying its symmetry/exchangeability assumption. Show a paired-versus-unpaired comparison, explaining the role of within-pair covariance, rather than selecting whichever favors the paper. Report robustness to each individual seed and, separately, distribution of raw per-arm scores. Compute paired TOST for H0: D≤−δ or D≥δ at δ=0.005; equivalence at α=0.05 requires 90% paired CI entirely within [−δ,δ]. Report CI relative to reference +0.0142 and ±0.005, both explicitly exploratory/scale references rather than a community-standard COD minimum. Preserve the paper's frozen 2-pooled-SD sign gate as a **different descriptive decision rule**; neither that gate nor lack of significance can prove no effect.
- **Controls/validation:** Independent pure-Python/NumPy implementation cross-checked with vetted statistical library, manual check on small synthetic test data, independent rerun of S_alpha from stored predictions where available. Audit unequal variance, missing seed handling, rounding, and all four cells. Never substitute Welch CI for paired CI without explanation. Predefine the analysis code **before looking at subgroup signs** wherever practical; tag post-review exploratory.
- **Deliverables:** `RESULT_TABLES/TH-01_paired_inference.csv` with all four cells and audit fields; `RESULT_TABLES/TH-01_seed_differences.csv`; a reproducible analysis script, calculations appendix, result/log paths, and succinct implication for CW-01/QA-01.
- **Acceptance:** Every published number recomputed to recorded precision where raw inputs exist; all 8 pairs checked; primary and secondary endpoints included; correct sidedness/df/TOST interpretation; full provenance. **Failure:** if per-seed runs or predictions are absent, do not reconstruct from aggregate values; mark `BLOCKED` or `PARTIALLY VERIFIED`, report manuscript-published CI only as **reported**.

### AN-01 — Independent eight-seed metrics/paired sensitivity audit (P0)

- **Addresses:** CW-01, QA-01. **Initial commitment:** “compute matched-seed C10–B differences, paired CIs, and paired equivalence tests ... after checking run manifests”; “smaller useful gains cannot currently be excluded.”
- **Question:** Are source run values, fold membership, checkpoint choices and reported CI/TOST mutually consistent?
- **Inputs:** historical verdict JSONs, checkpoints/predictions and metric scripts if available, TeX eight-seed SE schedule; actual CI/TOST imported table if found.
- **Execution:** Discover every eight-seed run; make immutable SHA256 checksum inventory. Re-score frozen predictions at alpha=0.5 for COD10K-test and NC4K with the manuscript's evaluation code; ensure no CAMO-250 checkpoint-selection scores are mixed into held-out endpoints. Compare recomputed per-run metrics to manuscript at recorded precision, record any mismatch separately. Call TH-01 on the *verified* per-seed table. Compare post-hoc interval and TOST for primary C10–B with manuscript claims [−0.0020,+0.0067] and p=0.101; locate, but do not infer, whether those were Welch/unpaired or paired. Report minimum effect excluded under each method and sensitivity to seed matching. Include SINet-v2 and NC4K, not only SINet/COD10K.
- **Controls:** same scorer/version, same mask releases and normalization, same split checksum; skip a corrupted run only with a documented integrity failure, **not** based on its outcome.
- **Deliverables:** `RESULT_TABLES/AN-01_original_vs_recomputed.csv`, `RESULT_TABLES/AN-01_run_integrity.csv`, annotated differences and command transcript.
- **Acceptance/failure:** complete per-seed audit or documented missing artifacts; never report unavailable raw values as reverified; distinguish new paired inference from previously published unpaired inference.

### AN-02 — Unique-set overlap, optimization and actual exposure (P0)

- **Addresses:** CW-01, QA-02. **Initial commitment:** “examine ... realized data exposure”; “quantify realized per-seed overlap and exposure ... before matched-budget retraining.”
- **Question:** Is the 8.8% *unique-pair* contrast borne out for each seed, and how much of a divergence is actually consumed by training under pinned/unpinned steps and pseudo-label changes?
- **Inputs:** immutable B/C10/CSHUF/CINV injection manifests, 4,447 common base-pair manifest, epoch loader/sampler seeds, optimization scheduler, round-1/round-2 pseudo-label manifests, step logs.
- **Procedure:** Hash/canonicalize image identity at original source level **and** injection-pair identity; do not conflate similar renders with byte-equal pairs. Compute intersection/union, per-arm injection counts, symmetric difference, Jaccard, distinct foreground IDs, difference relative to 5,447-pair training pool. Define clearly whether “48% differing” is based on 1,000−|A∩B| or symmetric difference 2(1,000−|A∩B|); show both and reconcile manuscript language. Reconstruct actual per-example **exposure counts** from data loader logs and sampler state, per epoch and per training round, accounting for step cap (253 SINet, 127 SINet-v2) versus unpinned (341/171 in FX campaign). If event logs absent, report *theoretical opportunities* separately and do not claim actual visits. Quantify round-2 pseudo-label counts and their overlap per arm, using the manuscript mean per-run values (B 1,977; C10 2,025; CSHUF 1,990; CINV 1,979) **as audit targets only**. Analyze absolute/injection-weighted exposure contrast, not a causal attribution adjusted for post-treatment pseudo-label counts.
- **Controls/verification:** deterministic manifest recomputation, hash spot checks, random hand inspection of 10+ pairs, source/target split purity, all eight seeds when available, both architectures; no test labels in selection.
- **Deliverables:** `RESULT_TABLES/AN-02_overlap_by_seed.csv`, `RESULT_TABLES/AN-02_exposure_by_run.csv`, `FIGURES/AN-02_overlap_exposure.png`, list of unverifiable assumptions.
- **Acceptance:** total and per-seed contrast matches manifests, unambiguous definitions; if no sampler trace, mark exposure **unverified** rather than infer from epochs alone.

### TH-02 — What concentration controls prove, and what they do not (P0)

- **Addresses:** CW-02. **Initial commitment:** “explicitly separate geometric from downstream claims, test architecture-dependent contrasts, and label all boundary analyses exploratory”; “the null does not generalize to adaptive generation or novel foreground synthesis.”
- **Question:** Which effects are identified by each arm, and what assumptions would be needed to claim downstream detection improves *because* of budget concentration?
- **Inputs:** `eq:alloc`, `tab:arms`, `fig:arms`, `sec:concentration`, `app:controls`; actual quota vectors; any per-run injection and pseudo-label manifests.
- **Method:** Formalize quota multiset `sort(q_j)` and its concentration indicators (entropy/Herfindahl/Gini), the rank mapping between quotas and uncertainty, and a sample-set geometry statistic. Verify mathematically and computationally that CSHUF/CINV preserve quota **multiset**, not necessarily individual cluster quotas, and that reversed-ranking leaves the middle rank fixed for odd k=75. Prove/quasi-prove only definitional identities under the documented construction; explicitly separate (i) selection-distribution geometry, (ii) total effect of assigning an arm on trained accuracy, and (iii) any mechanism-specific mediation by pseudo-labels. Document confounding B versus C10 in *both* direction and concentration; CSHUF/CINV enable an equal-shape direction test **only within this selection mechanism**. Clarify that no pair is an intervention isolating *only* concentration while fixing every other selected-content characteristic. Identify multiple comparison/post-hoc metric selection and architecture uncertainty.
- **Edge cases:** identical/near-zero score SD in Eq. eq:alloc; quota ties/rounding to N; k odd; limited pool/foreground repeated under larger N; round-2 pseudo-label feedback; reuse of test labels in CORACLE diagnostic (never valid test performance for a deployable method).
- **Deliverables:** `RESULT_TABLES/TH-02_quota_invariants.csv`, short mathematical note with exact definitions and limits, reviewer-facing safe wording.
- **Acceptance:** actual 75 cluster quota vectors pass invariant/normalization checks (sum N=1,000; same sorted quotas in all same-shape arms), correct scope conditions, no unjustified causal or generalization claim. If quota artifacts unavailable, mathematical verification limited to formulas: `PARTIALLY VERIFIED`.

### AN-03 — Architecture-dependent boundary reanalysis and interaction (P0/P1)

- **Addresses:** CW-02. **Initial commitment:** “test architecture-dependent contrasts ... label all boundary analyses exploratory.”
- **Question:** Are SINet and SINet-v2 different in *the policy effect* on boundary metrics, rather than simply one crossing a threshold and the other failing to?
- **Inputs:** frozen predictions for B, C10, CSHUF, CINV for both models on COD10K-test/NC4K, checkpoint/mask evaluation versions; historic Boundary-IoU scripts.
- **Procedure:** Build one analysis grid architecture (2) × endpoint (2) × boundary threshold (0.4,0.5,0.6) × contrast (C10−B, CINV−B, C10−CINV, C10−CSHUF, plus CSHUF−B as available). Use the same deterministic mask/preprocessing/binarization across all arms. For each contrast, compute per-seed paired differences and uncertainty from seeds **present in that campaign** (do not silently describe three-seed T2 results as eight-seed). Report original predeclared 2-SD/sign gates separately from post-hoc inferential CIs. Estimate architecture interaction Δ_model = (C10−B)_SINet − (C10−B)_SINet-v2, with matched seeds/endpoints, CI or valid hierarchical/permutation sensitivity where possible; do not conclude interaction merely from one arm's p-value <0.05 and the other's >0.05. Distinguish relative-to-bar ratio (1.37×/1.34× manuscript SINet) from actual absolute metric delta. Evaluate both boundary metrics if code exists; include per threshold but do not choose a winner ex post.
- **Controls:** independent metric script test on known masks, empty-mask conventions, resizing/prediction scale, mask-release identity, architecture comparisons using identical endpoints.
- **Deliverables:** `RESULT_TABLES/AN-03_arch_boundary_grid.csv`, `RESULT_TABLES/AN-03_interaction.csv`, `FIGURES/AN-03_architecture_contrasts.png`; limitations and multiplicity disclosure.
- **Acceptance:** all eligible arms/cells included, N and seed identities explicit, exact vs approximate data distinguished, interaction correctly characterized. Missing raw outputs are a blocker for new claims.

### AN-04 — Foreground diversity, clustering, and target coverage audit (P1)

- **Addresses:** CW-02, QA-02. **Initial commitment:** “audit diversity ... fixed offline LAKE-RED pool”; “analyze coverage conditional on foreground identity”; “without a genuine new-foreground capability, report adaptive/diverse foreground generation as an open limitation.”
- **Question:** Is low target-domain coverage linked to reusing foreground content, clustering failure, CAMO budget bias, or mismatch of uncertainty with the endpoint? Which statements are descriptive versus causal?
- **Inputs:** source 4,447-pair manifest, 4,447 generated pool/foreground IDs, target 4,040 embeddings and cluster memberships, coverage code and kNN embeddings, label metadata. Optional real source photographs are comparison only.
- **Procedure:** Check source/render foreground mapping as source-IDs plus perceptual/segmentation similarity; sample manual validation to avoid conflating same animal versus exact foreground. Quantify count unique foreground identities, within-ID variation, cluster occupancy, CAMO quotas/participation, kNN precision/recall to real target across multiple specified embeddings and neighborhood k values (if original settings known, reproduce first); compare paper's reported synthetic recall 0.13–0.54 to real-source 0.71–0.75 **only using the same estimator**. Stratify target coverage by COD10K/CAMO, foreground ID, cluster and uncertainty bins. Recompute k-means silhouette and between-cluster structural-error fraction if labels/benchmark predictions available, while preventing evaluation test labels from entering any new train selection. Contrast acquisition score's per-pixel vs structural-error correlations (reported +0.8553 vs +0.4276), with domain-level and architecture breakdowns. Document what *cannot* be inferred about genuinely novel foreground synthesis.
- **Controls/validation:** no contamination between fit/reference/evaluation partitions; embedding checkpoint and image preprocessing hashes; confidence intervals via group-aware resampling for dependent foregrounds; report k-NN estimator quirks, class imbalance, domain mixture, and repeated objects.
- **Deliverables:** `RESULT_TABLES/AN-04_foreground_coverage.csv`, `RESULT_TABLES/AN-04_cluster_domain_mix.csv`, `FIGURES/AN-04_coverage.png`, feasibility memo for EXP-03.
- **Acceptance:** unambiguous source/generated IDs and reproducible estimator; uncertainty statements include dependence and finite support. If assets missing, conduct only justified metadata analysis and mark the rest blocked.

### AN-05 — Protocol-specific CHAMELEON leakage and release audit (P0)

- **Addresses:** QA-03. **Initial commitment:** “audit exposure by protocol, distinguish 16 unchecked cases, disclose mask-release sensitivity, and favor COD10K-test/NC4K.”
- **Question:** Exactly which CHAMELEON evaluation photographs were accessible under (a) supervised source training, (b) unlabeled/transductive target adaptation, and (c) validation/checkpoint selection? Does any score-difference claim follow?
- **Inputs:** published Tier-A/Tier-B pair list and detector from repo if available; CHAMELEON 76 originals, COD10K-train, CAMO train, COD10K unlabelled target, CAMO target, CAMO-250 selection set, held-out test splits; checkpoint provenance; exact image/mask-release hashes; original evaluation code/predictions.
- **Procedure:** First reproduce Tier-A method: same-dimension groups, 32×32 gray RMS candidate cutoff 14.0; full-resolution RGB mean absolute difference <6/255. Reproduce 41 same-dimension matches on author-sourced release. Then only if dependencies present, run Tier B: SIFT, Lowe=0.75, RANSAC homography ≤4 px, ≥20 inliers followed by full-resolution warp residual/correlation/geometric sanity; verify nine additional matches and reject any geometric false positive such as the manuscript's `animal-7`. Record candidate acceptance and manual adjudication **without changing published thresholds to improve count**. Keep 50/76 minimum, 44 COD10K-train, and 16 unresolved as separate fields. **Reconcile exact-hash scopes:** 0 overlap with *training pool*, but `animal-17`, `animal-25`, `animal-60` exact hashes coincide with CAMO-250 selection split. Build an exposure pathway matrix per CHAMELEON image: supervised source label use; unlabeled target image exposure (non-label, transductive); validation/checkpoint exposure; held-out test, with direct/possible/absent/unknown and supporting manifest path. Analyze potential consequences conditionally; no automatic claim that transductive access equals supervised label leakage, and no assertion of causal score inflation without a genuine no-leak counterfactual. If feasible, rerun evaluation on strictly independent COD10K-test/NC4K using frozen checkpoints (no test-label tuning), without cherry-picked CHAMELEON survivors. Compare mask releases for same prediction vectors, recording polarity, preprocessing, checksum, MAE differences (paper reports 0.2196 vs 0.0816) and qualitative implications; confirm or explain any discrepancy.
- **Controls:** NC4K calibration negative set, synthetic known-answer self-test, manual audit of accepted homographies, no tuning thresholds against 16 unchecked, separate release-specific metrics, report mislabeled/re-encoded ambiguities.
- **Deliverables:** `RESULT_TABLES/AN-05_chameleon_pairs.csv`, `RESULT_TABLES/AN-05_protocol_paths.csv`, `RESULT_TABLES/AN-05_mask_release.csv`, `FIGURES/AN-05_protocol_paths.png` (privacy/license-compliant), duplicate-detector run logs and explanatory note.
- **Acceptance:** independently reproduced pair list where data available; no conflation of byte-identical/visual duplicate, training/target/checkpoint exposure or contamination/score inflation; all 76 images accounted for as confirmed or unchecked. Without exact image access, mark unreplicated counts as *manuscript reported*.

### EXP-01 — Matched-budget larger-contrast robustness (P1; conditional retraining)

- **Addresses:** CW-01, QA-02. **Initial commitment:** “preflight larger matched-budget allocations to ensure they truly increase between-arm differences”; “attempt controlled training where feasible.”
- **Hypothesis:** Increasing *realized distinct content and its training exposure* may reveal an effect obscured by the weak N=1,000 contrast; changing nominal N without increasing actual contrast cannot answer this.
- **Inputs:** source/target/generated pool manifests and original selection/trainer code; sufficient GPU access; verified fixed splits; B and C10 configurations, preferably SINet and SINet-v2, both held-out endpoints.
- **Preflight (no GPU):** Recompute N=1,000 baseline selection. Simulate **identical total budgets** for random versus targeted at candidate N=2,000 and 3,000 (available allocation sweep in manuscript), with same 75 clusters, temperature, generator pool and source pool. Calculate per-arm injection intersections, distinct foreground identity, fraction of total training *actually distinct*, predicted and if available replayed sample exposure under the pinned schedule. Since finite pool saturation can make **larger N increase overlap**, select a larger-N condition **only if** documented unique-set and/or exposure contrast is materially larger; define the contrast metric before inspecting outcomes. If neither is larger, do not run useless larger-N training; mark hypothesis untestable under pool and propose a scientifically valid alternative such as less-overlapping draw *at a fixed budget*, explicitly flagged as a different sampling algorithm rather than C10.
- **Execution if preflight passes:** Execute B_N and C10_N, matched architecture, seeds, source labels, target pool, total injected N, model initialization scheme, optimizer/training steps and checkpoint selection; ensure budget/effective steps are matched **within each N**. Use seeds from original campaign for comparability only after documenting new exploratory design; use ≥3 matched seeds as minimal screening, favor eight if feasible and budget permits. Freeze allocation config before launching; avoid new test-label-driven changes. Record every epoch loss, actual exposure, pseudo-label counts and seed. If new budget changes source-data loader length, audit changes in optimization before attributing effects to selection. Compare C10_N−B_N versus original C10_1000−B_1000 with uncertainty; formal dose interaction requires appropriate replicated inference and is otherwise descriptive.
- **Controls:** within-N B_N random baseline, original B/C10 N=1000 historical if reverified, optional same-shape CSHUF_N/CINV_N **only if resources allow**, identical COD10K-test/NC4K scoring. Do not compare methods of unequal total injection budget as if isolating targeting.
- **Metrics:** S_alpha (primary), NC4K held-out S_alpha, boundary metrics exploratory, MAE on fixed checkpoint-selection split, achieved injection/exposure contrast, foreground coverage.
- **Deliverables:** `RESULT_TABLES/EXP-01_preflight.csv`; if run, `RESULT_TABLES/EXP-01_seeds_metrics.csv`, run configs, raw logs, checkpoints/paths and training resource tally, interpretive note. Keep failed/partial seeds visible.
- **Acceptance:** documented stronger realized contrast and completely matched within-N design; independent recomputation of primary metrics; no favorable-outcome filtering. **Blocker:** generated-pool saturation, missing trainer/dataset/GPU, or unresolved leakage; report `BLOCKED`/`INCONCLUSIVE`, not a null for higher contrast.

### EXP-02 — Re-score boundary metrics with controlled architecture grid (P1)

- **Addresses:** CW-02. **Initial commitment:** “test architecture-dependent contrasts”; “label all boundary analyses exploratory.”
- **Hypothesis:** A concentration-associated boundary benefit may appear in SINet and not in SINet-v2, but the appropriate evidence is the *architecture-by-arm interaction*, not separate threshold decisions.
- **Inputs:** frozen stored predictions for B/C10/CSHUF/CINV, per-seed endpoint masks, exact metric implementations and run manifests; if frozen predictions unavailable, original checkpoints and deterministic inference code.
- **Implementation:** Prefer **no retraining**: pin inference version; produce/copy the score maps to a new checksum-tracked directory and validate two example images by independent re-inference. For all available seeds across each arm, compute Boundary-IoU at thresholds 0.4/0.5/0.6 and second boundary metric if manuscript implements it, plus S_alpha. Use the exact same image/mask dimensions and empty-mask policy. Export per-image, per-seed and aggregate results. Call AN-03 to compute matched contrasts and formal interaction. If predictions/checkpoints absent, retraining is a *separate* authorized resource-dependent path; do not manufacture historical run values or imply reruns are independent preregistered evidence.
- **Controls:** randomized arm B, fixed-concentration CSHUF/CINV, both models and both endpoints, all planned thresholds, consistent mask releases. Keep SINet 1.37×/1.34× historical **bar ratios** distinct from absolute performance improvements.
- **Deliverables:** `RESULT_TABLES/EXP-02_rescored_predictions.csv` (one aggregate row per legitimate cell), raw per-image metrics or compact serialized table, `EXPERIMENT_LOGS/EXP-02_commands.log`, reproducible metric harness/tests, plus AN-03 results.
- **Acceptance:** every score traceable to immutable prediction and annotation checksums; architecture comparisons honest about sample size/metric selection. If no predictions or checkpoints, mark `BLOCKED` and provide analytic rationale only.

### EXP-03 — Genuine new-foreground/adaptive generation conditional test (P1; likely resource-blocked)

- **Addresses:** CW-02, QA-02. **Initial commitment:** “audit diversity ... the null does not generalize to adaptive generation or novel foreground synthesis”; “without a genuine new-foreground capability, ... report ... an open limitation.”
- **Scientific question:** Can uncertainty direction become useful when generation changes the *foreground support*, rather than selecting re-backgrounded copies of pre-existing objects?
- **Gate before any run:** Confirm code/model capable of producing **genuinely new**, legally usable and independently validated foreground content; a fixed re-backgrounded pool is **not** sufficient. Confirm masks, quality controls, provenance, content diversity, compute/permission constraints, and an independent contamination screen. Otherwise stop this task and mark `BLOCKED` with reason and explain non-generalizability. Do not label background variation as novel foreground synthesis.
- **Conditional controlled design:** Generate equal-size (e.g. N=1,000) candidate synthetic pools under uncertainty-ranked versus random allocation with the *same generator family*, prompts/conditioning class, foreground license pool, input-image distribution, compute budget, quality/mask-filtering rules, render resolution and checkpoints. To isolate direction from concentration, include CSHUF/CINV style same-shape quota controls if feasible; if the generator generates genuinely new objects or masks, demonstrate independent novelty/quality and identical acceptance filtering across arms. Commit frozen design and seeds before evaluating outcomes; do not use COD10K-test/NC4K labels to steer generation or checkpoint choice. Train B_new vs C10_new with same architecture, steps, synthetic-budget, source/target splits and checkpoint procedure, ideally both architectures and multiple shared seeds. Compare coverage/foreground novelty before and after training, with per-seed S_alpha and uncertainty; record all draw/selection attempts including rejected images, not only successes.
- **Controls/limitations:** It is a *new generative regime*, not an internal ablation of the old LAKE-RED selection, so never conflate its result with historical fixed-pool claims. If full matched experiments are not feasible, use AN-04 observational coverage audit only; do not claim effects of adaptive generation.
- **Deliverables:** if executed, `RESULT_TABLES/EXP-03_generation_manifest.csv`, `RESULT_TABLES/EXP-03_metrics.csv`, quality/novelty audit, configs/logs/sources; otherwise `EXPERIMENT_LOGS/EXP-03_BLOCKER.md` with attempted search and required resources.
- **Acceptance:** demonstrable new foreground identities, fair matched budgets and validation, reproducible held-out metrics; otherwise explicit unresolved question.

### DOC-01 — Correct scientific interpretation throughout revised argument (P1)

- **Addresses:** CW-01, CW-02, QA-01, QA-02. **Initial commitment:** “make qualifications prominent”; “explicitly separate geometric from downstream claims”; “state [generator] boundary explicitly.”
- **Inputs:** verified TH-01/02, AN-01–04, EXP-01–03; manuscript text `abstract`, `sec:null`, `sec:concentration`, `sec:why`, `sec:discussion`, `sec:conclusion`, `app:diag`.
- **Procedure:** Prepare a **separate patch proposal**, not an unauthorized overwrite of submitted paper, with precise new wording. Make null finite/setting-specific, quantify exact CI and unresolved ±0.005 equivalence, contrast between concentration geometry and measured detection, mention SINet-v2 architecture disagreement, pinned schedule and pseudo-label mediation, limited 8.8% distinct pool, and offline foreground-reuse scope. Mark previously published and newly verified quantities distinctly. Update the reference citation +0.0142 as reference effect, not universal MCID. Correct any overly strong phrase such as “no score of any quality helped here” or generalized causal claim if evidence not sufficient. Append a provenance footnote for newly added experiments and a table of proposed edits with section label and reason.
- **Deliverables:** `RESULT_TABLES/DOC-01_claim_evidence_map.csv`, `DOC-01_MANUSCRIPT_PROPOSED_EDITS.md`, and source diff/patch only if local working copy intentionally edited (original preserved).
- **Acceptance:** every changed statement supported by actual verified artifacts; consistent across abstract/body/supplement; no promise of adaptive foreground validation unless executed.

### DOC-02 — CHAMELEON protocol, duplicates and mask release clarification (P1)

- **Addresses:** QA-03. **Initial commitment:** “audit exposure by protocol, distinguish 16 unchecked cases, disclose mask-release sensitivity, and favor COD10K-test/NC4K.”
- **Procedure:** Draft a concise reviewer-facing table comparing (i) supervised source images with masks, (ii) unlabeled target transduction, and (iii) selection/validation, indicating when CHAMELEON photographic overlap is present/unknown and whether labels are exposed. Explain exact-file hashing versus geometric duplicate detection, 50 confirmed floor versus 16 unresolved, 44 COD10K-train subset, and three exact CAMO-250 selection overlaps **outside** the counted training pool. Clarify risks without assuming score inflation (paper's difficulty analysis did not find leaked-subset advantage), and distinguish distinct CHAMELEON ground-truth releases/polarity/MAE. Recommend independent COD10K-test and NC4K protocol with split hashing and image-level overlap audit. Any rerun results must come from AN-05.
- **Deliverables:** `DOC-02_CHAMELEON_PROTOCOL_CLARIFICATION.md` and amendments proposed for `sec:contamination`, `app:chamext`, `app:masks` without overwriting original.
- **Acceptance:** all exposure pathways and caveats accurate; contamination lower bound and unchecked remainder preserved; no unsupported claim of quantified inflation.

## 6. Shared numerical/statistical discipline

1. Use fixed column names, units, N, CI level, upper/lower limits, paired/unpaired label, α, primary/secondary/exploratory flag, test-selection status and code/data checksum in every result table.
2. Report all four model–endpoint cells, not just the best. Separate **absolute performance delta** from “times its two-SD bar,” which is a different scale.
3. Main 2-sigma rule is **pooled per-run SD**, does not shrink as 1/sqrt(n) when n grows, and is not a precision interval or effect bound. Paired t intervals use SD of **paired differences** / sqrt(number of valid pairs). Recompute degrees of freedom and disclose small-sample uncertainty.
4. An eight-seed 95% CI whose upper limit is +0.0067 excludes +0.0142 but **permits some smaller positive gains**. The ±0.005 equivalence failure does **not** imply a positive effect. Post-hoc margins require labeling and sensitivity discussion.
5. Test for architecture interaction directly; a significant result on one architecture and not on another does not alone imply a significant difference between architectures. Correct for interpretation under multiple endpoints, thresholds and exploratory comparisons; do not hide multiplicity.
6. Respect held-out endpoints: CORACLE uses endpoint **labels as a diagnostic** and cannot be proposed as deployable selection or as evidence from a leak-free method. Avoid selecting parameters/foregrounds based on test-label feedback.
7. The two-round pseudo-label counts are outcomes of first-round policy. Treat them as potential mediators; do not adjust them away or pretend “injected samples” are the only between-arm difference after the first round.
8. Duplicates of the **photograph** can matter without byte-level duplication; an unlabeled copy is *transductive access*, not the same as supervised mask leakage; validation set overlap is a distinct checkpoint-selection path. No measured boost can be claimed from overlap counts alone.

## 7. Verification and results packaging (execute after feasible tasks)

For each completed task, independently verify commands were executed, configs and seeds match saved outputs, raw metrics recompute, thresholds/margins reflect what was actually tested, baselines are fair, no outcome was omitted, and mathematical statements are justified. Each concern receives one final resolution: `FULLY ADDRESSED`, `SUBSTANTIALLY ADDRESSED`, `PARTIALLY ADDRESSED`, or `UNRESOLVED`; each task status is `VERIFIED`, `PARTIALLY VERIFIED`, `INCONCLUSIVE`, `FAILED`, or `BLOCKED`.

Create **exactly these core output paths** under `ICLR2027_REBUTTAL/STUDENT_RESULTS/` (plus legitimate extra scripts/checksums/configs and task files):

```text
ICLR2027_REBUTTAL/
  01_INITIAL_REBUTTAL_FOR_SUBMISSION.md    # copy from author, immutable
  02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md  # copy from author, immutable
  03_STUDENT_AGENT_EXECUTION_INSTRUCTIONS.md # this standalone instruction
  STUDENT_RESULTS/
    FINAL_UPDATED_REBUTTAL.md
    RESULTS_SUMMARY.md
    EXPERIMENTAL_EVIDENCE.md
    EXECUTION_STATUS.md
    FINAL_SCIENTIFIC_AUDIT.md
    CODE_CHANGES.patch                       # if code modified
    EXPERIMENT_LOGS/
    RESULT_TABLES/
    FIGURES/
```

If no code changes occurred, put `No code changes necessary` in `EXECUTION_STATUS.md` and omit the patch. Do **not** create empty fake result files only to fill the tree; link only files that exist, and state blocked/omitted artifact paths explicitly. Make a relative-link validation check. `EXPERIMENTAL_EVIDENCE.md` is the authoritative provenance ledger and must include at least: task IDs, reviewer IDs, baseline and output commands, code revision, dataset split/checksum, configs, seeds, hardware/software, generated output paths, metrics with units/uncertainties, interpretation, caveats, and task status. Use an audit table and one detailed subsection per task. Include your original code patch, if any, as `git diff` against the documented baseline; keep data/checkpoint files out of the patch.

### Required shape of `FINAL_UPDATED_REBUTTAL.md`

The final rebuttal is the most important **student-produced** artifact. Open with a brief reviewer acknowledgment and respond point-by-point to CW-01, CW-02, QA-01, QA-02, QA-03, each using subsections **Response**, **Additional Validation**, **Results**, **Interpretation**. Write as authors (“we”), not as a tool or student. Cite relevant manuscript sections and exact verified values; **distinguish submitted-paper evidence from post-review evidence**, and mark unresolved work rather than promising that it happened. Do not include private repository paths, commands, or unverified checkpoints in reviewer-facing prose; keep provenance in the evidence files. Avoid premature equivalence/generalization claims. Add a **separate paste-ready OpenReview version <=5,000 characters** (including headings/Markdown) if the author still needs that platform limit; preserve an unrestricted expanded rebuttal for archival use. Independently count Unicode code points in the short version; include an exact character-count audit. The author—not the agent—chooses which text to submit.

### Required shape of `RESULTS_SUMMARY.md`

Provide per-task status and summary tables for paired effects by architecture/endpoints, realized unique/exposure contrast, boundary interaction, coverage/foreground novelty and CHAMELEON protocol pathways. Identify missing experimental resources, unmeasured effects and implications for the reviewer. Include negative and conflicting outcomes.

### Required shape of `FINAL_SCIENTIFIC_AUDIT.md`

For **each of the five** reviewer concerns, ask: Was the concern understood accurately? Was the corresponding initial commitment addressed? Which task evidence and file/line/path support the response? Did runs execute? Do numbers match raw outputs? Fair baselines/splits/masks? Are mathematical, statistical and causal interpretations valid? Does final wording preserve limitations? Is the claim consistent with initial response? Assign the four-level resolution label with explanation and list unresolved dependencies. Check manuscript labels, bibliography citation keys, LaTeX source integrity and all Markdown links. Conduct an independent verification pass using a different script or independent calculation rather than only re-reading main outputs.

### Submission-control protocol

The student sends the entire `STUDENT_RESULTS/` directory plus `FINAL_UPDATED_REBUTTAL.md` and a brief `EXECUTION_STATUS.md` to the corresponding author. The student **must not submit** or edit the live OpenReview response. Clearly explain exactly which new experiments ran, which were only analyses of historical data, and which were blocked. Ensure the author can reproduce evidence without having to infer unlisted paths or accept guessed numbers.

---

## Appendix A — Verbatim reviewer concerns

The following text is extracted from the uploaded reviewer report `dypE.md`. Preserve its meaning and headings when drafting responses. These are the **complete** relevant critical weaknesses and author questions, not short paraphrases.

# Critical Weaknesses:

1. Statistical Sensitivity and Interpretation of the Negative Result

The difference between targeted and random training is quite small. Synthetic images make up only 18.4% of the training set, and about half are shared across different groups. As noted in Appendix C, only around 8.8% of the full training set actually differs. This may make small improvements hard to detect.

The authors also use twice the pooled standard deviation as their decision rule, which is more conservative than using the standard error. The eight-seed comparison shows a difference of +0.0024, with a 95% confidence interval of [-0.0020, +0.0067]. This rules out the reference improvement of +0.0142, but smaller gains are still possible. Also, the targeting-versus-random comparison does not pass the equivalence test at ±0.005.

Overall, the results show that this method does not bring a large improvement in the tested setting. However, they do not fully rule out smaller gains. I think the paper should make this limitation clearer.

2. Downstream Validation and Generalizability of the Concentration Hypothesis**

The geometric analysis shows that concentrating samples changes the selected dataset, even when uncertainty scores are shuffled or reversed. However, this does not mean that concentration improves detection performance.

In the post-hoc boundary-metric analysis, both targeted and reversed allocation perform better than random allocation on SINet. However, these gains are much smaller on SINet-v2. This suggests that the effect of concentration may depend on the model architecture.

The experiments also use a fixed pool of LAKE-RED images generated offline. Since no new foreground content is generated, uncertainty guidance can only select from existing samples. This may limit its benefits, especially when the synthetic data does not cover the real data distribution well.

Therefore, the negative results may be partly caused by the generation setup. It is still unclear whether the same conclusion would hold with better synthetic data or an adaptive generation process.

# Questions For Authors:

 1. How well do the results rule out smaller improvements from uncertainty-guided targeting?

The eight-seed results rule out large improvements, but the targeting-versus-random comparison does not pass the equivalence test at ±0.005. Could the authors clarify what level of improvement they consider meaningful for COD? Also, could they provide a paired analysis using the same random seeds? This would help clarify whether the negative result also applies to smaller but useful improvements.

 2. How much do the limited training-set differences and synthetic data diversity affect the conclusion?

As noted in Appendix C, only about 8.8% of the training pool differs between the compared groups. The synthetic data also have limited coverage of the real data distribution. Would the same conclusion hold if the training sets had larger differences or if the generator could produce more diverse foreground content? Additional experiments or discussion on these limitations would help support the generality of the results.

3. How does CHAMELEON contamination affect existing COD evaluation results?

The paper identifies 50 overlapping images, including 44 that also appear in COD10K-train. Could the authors clarify how these overlaps may affect common COD training and evaluation protocols? In particular, it would be useful to distinguish between supervised training, unlabeled target-domain adaptation, and checkpoint selection. This would help readers better understand the practical impact of the contamination finding.

---

## Appendix B — Corresponding author's complete initial reviewer response

The author may have already posted the version below. Treat its stated actions as commitments, not as evidence that experiments were completed. This is an exact copy of `01_INITIAL_REBUTTAL_FOR_SUBMISSION.md` in the preparation bundle; if the author has subsequently edited or posted a different response, compare it and update the commitment ledger **before** executing contradictory tasks.

# Initial Response to Reviewer dypE

We thank the reviewer for the constructive assessment and for recognizing our controls and CHAMELEON audit. We agree the null requires qualification.

### CW-01: Statistical sensitivity
**Reviewer Concern (verbatim excerpt):** “However, they do not fully rule out smaller gains.”

**Response:** Agreed. Our pre-registered threshold of twice the pooled *per-run standard deviation* plus seed-wise sign agreement is a conservative decision rule, **not** a confidence bound or proof of no effect (Methods; Appendix “Decisive Gap”). For eight-seed SINet/COD10K, C10–B = +0.0024, with post-hoc 95% CI [−0.0020, +0.0067]. This excludes the reproduced reference improvement (+0.0142), but admits smaller positive gains. At ±0.005, post-hoc equivalence of C10 and B is **not** established (p = 0.101). Injected images are 18.4% of the pool; about 48% differ between arms, yielding roughly 8.8% total-pool contrast. We will make these qualifications prominent and examine paired-seed sensitivity and realized data exposure without assuming their outcomes.

### CW-02: Concentration versus downstream performance
**Reviewer Concern (verbatim excerpt):** “However, this does not mean that concentration improves detection performance.”

**Response:** We agree. Dataset distinguishability and embedding geometry show that **concentration changes the selected data**, not that it universally improves detection. Same-shape shuffle (CSHUF) and reversed-ranking (CINV) controls do not establish an uncertainty-direction benefit in downstream S-measure. On post-hoc SINet boundary metrics, C10–B and CINV–B reach approximately 1.37× and 1.34× their bars, respectively; SINet-v2 shows no comparably resolved effect. We will explicitly separate geometric from downstream claims, test architecture-dependent contrasts, and label all boundary analyses exploratory. The fixed offline LAKE-RED pool reuses foregrounds, so our null does **not** generalize to adaptive generation or novel foreground synthesis; we will audit diversity and state this boundary explicitly.

### QA-01: Smaller meaningful improvements and pairing
**Reviewer Concern (verbatim excerpt):** “Could the authors clarify what level of improvement they consider meaningful for COD? Also, could they provide a paired analysis using the same random seeds?”

**Response:** +0.0142 is a *reproduced, study-specific reference effect*, not a universal minimum meaningful COD improvement. The ±0.005 margin is exploratory, not a validated practical-significance threshold. We will report uncertainty against both scales and compute matched-seed C10–B differences, paired CIs, and paired equivalence tests from the existing eight-seed runs (seeds 42, 43, 45–50), after checking run manifests. Smaller useful gains cannot currently be excluded.

### QA-02: Limited contrast and foreground diversity
**Reviewer Concern (verbatim excerpt):** “Would the same conclusion hold if the training sets had larger differences or if the generator could produce more diverse foreground content?”

**Response:** That remains untested. Shared base images and substantial injection overlap attenuate the contrast (Appendix “How much the trained comparison is attenuated”); the background-only, fixed-pool generator limits content diversity (Section “Why It Fails”). We will quantify realized per-seed overlap and exposure, preflight larger matched-budget allocations to ensure they truly increase between-arm differences, and analyze coverage conditional on foreground identity. We will attempt controlled training where feasible. Without a genuine new-foreground capability, we will report adaptive/diverse foreground generation as an open limitation, not imply it has been evaluated.

### QA-03: Protocol consequences of CHAMELEON overlap
**Reviewer Concern (verbatim excerpt):** “In particular, it would be useful to distinguish between supervised training, unlabeled target-domain adaptation, and checkpoint selection.”

**Response:** We confirm at least 50/76 CHAMELEON photographs in COD10K/CAMO training pools (44 in COD10K-train): 41 re-encodes and nine geometrically verified copies despite zero exact-hash training matches (Section “CHAMELEON Is Mostly Training Data”; Appendix “CHAMELEON Contamination”). **Supervised overlap** violates independent-image evaluation; **unlabeled adaptation** can expose the model to test photographs without using test labels, so its consequences depend on the protocol; **checkpoint selection** on overlapping validation images introduces a separate selection path (the appendix documents CAMO-250 matches). This finding does **not** demonstrate score inflation, which our difficulty analysis did not show. We will audit exposure by protocol, distinguish 16 unchecked cases, disclose mask-release sensitivity, and favor COD10K-test/NC4K.

We will report inconclusive outcomes alongside any additional findings.


---

## Appendix C — Full concern-to-action matrix and manuscript evidence anchors

This matrix captures **every identified substantive subissue** from the reviewer, including precise manuscript labels, the limits of existing evidence, priority and verification criteria. It is included so this single Markdown guide can be sent without separate access to the preparation master prompt. The authoritative manuscript is still the student's verified original `.tex` file, not this summary.

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


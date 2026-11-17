# ICLR 2027 — Reviewer Caus: Single-Student Autonomous Agent Execution Guide

**Audience:** Exactly one student working on their own machine with an autonomous research/coding agent. **This file is self-contained.** It includes all five original reviewer concerns verbatim (Appendix A), the complete author-prepared initial rebuttal verbatim (Appendix B), methodological context, a task/commitment ledger, execution recipes, evidence standards, and final deliverable specifications. It does **not** require the student to open `RevisionPrompt.md` or reconstruct the review from another conversation.

**Current stage:** The corresponding author will review and submit the initial rebuttal before additional experiments. **You, the student's agent, must carry out feasible new validation, verify results, and draft a final updated response; you must not submit to OpenReview.** Do not stop after making a plan. Work autonomously on routine reversible tasks; do not ask the author to approve each command. If a resource, permission, or irreversible action blocks a task, document it and continue on other tasks. Scientific correctness outranks a positive rebuttal.

**Read first:** the whole of this guide, then the submitted manuscript `AD-PCHGS-250926.tex`, its available inputs, and the full repository. The user originally referred to `Rohit_PCHGR_250926.tex` and `v58c.MD` in a reusable prompt; for this reviewer, the actual supplied inputs are `AD-PCHGS-250926.tex`, `reference.bib`, and `Caus.md`. Confirm the locally available manuscript matches the corresponding author's submission. If its version differs, report differences before using its numbers. Do not confuse `Caus` with the prior reviewer `dypE`; produce **reviewer-specific** responses and a separate execution branch and output directory.

## 1. Scientific background and exact claim boundaries

The study asks whether uncertainty-guided allocation of a *fixed* offline synthetic-data budget improves camouflaged object detection (COD). A base training source contains **4,447** labeled pairs; **4,040** unlabeled real target images (3,040 COD10K + 1,000 CAMO) are clustered into **k=75** groups using frozen normalized self-supervised features. The uncertainty score is student–teacher disagreement based on edge-aware saliency (ES), aggregated at cluster level. A **N=1,000** synthetic-image budget is allocated using a standardized-score softmax at temperature **τ=1.0**, with largest-remainder integer quotas. LAKE-RED supplies an **offline rendered pool** consisting of fixed foreground cutouts with replaced backgrounds. A two-round S2R-COD-style student/EMA-teacher training procedure includes inter-round pseudo-labeling; the generator is **not called online** or retrained during the loop.

The original architectures are SINet (batch 16, 40 epochs) and SINet-v2 (batch 32, 100 epochs), Adam learning rate 1e−4, 352×352 image training, and EMA teacher momentum 0.996 (Appendix `app:method`). Primary endpoint: COD10K-test **S-measure S_α at α=0.5**; secondary endpoint: NC4K. CAMO-250 MAE is used for checkpoint selection; S-measure, E-measure, weighted Fβ, and exploratory boundary metrics are different outcomes and must not be conflated.

Original arms (`tab:arms`): `A0` no injection; `A2` add real images; `B` uniformly random 1,000 renders; `C10` uncertainty-targeted allocation; `CSHUF` same quota multiset, permuted score alignment; `CINV` reversed quota rankings; `CORACLE` **same C10 quota multiset reassigned** by true endpoint error; FX arms remove an optimization-step cap; MT is a positive control. Crucially, CORACLE **does not change quota concentration**. The primary eight-seed C10−B SINet/COD10K gap is +0.0024, within a 2 pooled-SD bar of 0.0069, with post-hoc 95% CI [−0.0020,+0.0067]. Three-seed CORACLE−B is +0.0008 with bar 0.0061, and must not be misrepresented as an alternative-shape oracle. The sample-level probe/effective-rank findings support geometric differentiation, **not** detector improvement. Post-hoc boundary effects mainly occur for SINet, not SINet-v2.

The manuscript reports mean effective-rank ratio C10/random **0.634** over 20 geometry cells, score-direction effect +0.0073 Cohen's d vs shuffle and −0.0649 vs arbitrary-cluster control. Generator provenance: **8,885** traced objects and no evidence of regenerated foreground, kNN target-manifold recall **0.13–0.54** under the audited settings (raw coverage appendix is separately imported). Further diagnostic checks include maximal clustering silhouette 0.1600, about one fifth of measured endpoint structural-error variance between clusters, and uncertainty–pixel-error / uncertainty–S-error correlations +0.8553/+0.4276. These are descriptive observations, **not** a proof that generator diversity causes the null. A separate CHAMELEON study found ≥50/76 train-test photographic overlaps, so it must not be introduced as a clean evaluation endpoint.

**The paper's genuine contributions:** (i) a concentration-preserving, direction-destroying counterfactual for allocation claims, (ii) an honestly bounded negative COD result with falsification controls and an interpretable sensitivity limit, (iii) diagnostic checks for cluster quality, composition, error variance and foreground coverage, and (iv) an independent contamination audit. It does **not** claim universally low rank for any nonuniform allocation or that closed-loop generation cannot work elsewhere. The reviewer wants (a) a clearer account of methodological versus detector contribution, (b) a different-*shape* true-error oracle, and (c) a more expressive generator and modern detector replication.

### Exact manuscript anchors / evidence locations

| Subject | LaTeX source identifiers | Relevant original artifact hints (verify actual paths) |
|---|---|---|
| Loop, scoring, quota formula | `sec:method`, `eq:es`, `eq:alloc`, `app:method` | allocation scripts, cluster assignment manifests, original score/quota CSVs, `abc_pools.json` |
| Arms and concentration control | `tab:arms`, `fig:arms`, `sec:concentration`, `fig:thesis` | `T2_RESULTS.md`, `c1_attribution.csv`, shape/control manifests |
| Trained primary comparisons | `sec:null`, `tab:trained`, `tab:allcells`, `app:diag` | `abc_verdict.json`, `or/`, `fx/`, `se/`, `out/se/abc_metrics.csv`, `rebuild/FinalPaper/results.md` |
| Oracle provenance | `app:controls`, oracle paragraph | CORACLE pre-registration, endpoint error by cluster, architecture-specific predictions |
| Generator diversity and coverage | `sec:why`, `sec:discussion`, `app:coverage` via `\input{appendix_coverage.tex}` | raw image/mask pairs, foreground IDs/hashes, embedding extraction, recall scripts |
| Architecture / optimization | `app:method`, `app:controls`, `tab:trained` | SINet/SINet-v2 code, checkpoint selection, per-round logs, pseudo-label manifests |
| Leak controls | `sec:contamination`, `app:chamext`, `app:masks` | pair detection reports, split manifests, mask release manifests |
| External papers/citations | `sec:related`, `app:related`, bibliography | `reference.bib` (validate every cited key and its semantic correspondence) |

**Absent from the preparation uploads:** full code/repository and experiment configs, `math_commands.tex`, `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`, `table_cluster_composition.tex`, `appendix_tables.tex`, `appendix_coverage.tex`, and `figs/*`. They may exist in your research workspace; search rather than invent. The submitted TeX points to an anonymized repository `https://anonymous.4open.science/r/AD-35F1/`; inspect its available state if locally permitted and usable. The presence of a repository URL in the manuscript is **not** proof it is accessible or contains data/weights. Respect privacy, licenses and anonymization.

## 2. Reviewer concern ledger and initial rebuttal commitments

The complete exact review appears in **Appendix A**. The initial rebuttal text to be honored appears **verbatim** in **Appendix B**. The mapping below makes the promised follow-up executable. An initial promise to *assess/attempt if feasible* is **not** a guarantee of a result or a license to invent one.

| Reviewer ID | Critical issue | Initial-response commitment | Action IDs | Priority |
|---|---|---|---|---|
| CW-01 | Algorithmic contribution vs largely expected geometric probe and null | Emphasize allocation attribution/control, distinguish covariance geometry from S-measure gains, avoid universal rank claim, foreground benchmark audit | TH-01, AN-01, AN-02, DOC-01 | P0 |
| CW-02 | Limited COD/LAKE-RED/S2R-COD/architecture scope | State exact empirical bound; modern architecture validation where trainable; do not claim global transfer | TH-02, AN-01, AN-04, EXP-02, EXP-04, DOC-01, DOC-02 | P0/P1 |
| CW-03 | Fixed foreground identity and 0.13–0.54 coverage may block steering | Verify provenance and coverage; attempt mask-valid new foreground content; separate diversity/coverage/accuracy | AN-03, EXP-03, EXP-04, DOC-02 | P0/P1 |
| QA-01 | CORACLE keeps C10 shape; alternative shape untested | Explicitly acknowledge *No*; compare error-proportional and top-error quotas at N=1000, matched controls, appropriate leaky-oracle caveat | TH-01, TH-02, AN-02, AN-05, EXP-01, DOC-02 | P0 |
| QA-02 | Modern backbone plus foreground-varying generator replication, narrow claim | Architecture and generator perturbations separately, then combined if feasible; fixed-budget B/C10/CSHUF comparisons | AN-03, AN-04, EXP-02, EXP-03, EXP-04, DOC-01, DOC-02 | P1 |

**Task totals:** 4 controlled experiments (`EXP-01`–`EXP-04`), 2 mathematical/statistical validations (`TH-01`–`TH-02`), 5 analyses (`AN-01`–`AN-05`), and 2 writing/documentation tasks (`DOC-01`–`DOC-02`). These counts are for this reviewer only.

## 3. Agent operating instructions, permissions and independent verification

1. **Begin execution without reinterpreting the problem.** Inventory code/data and confirm original results reproducible when feasible. Use an isolated Git branch such as `rebuttal/Caus-oracle-scope` or a timestamped working directory. Do not modify or replace the submitted anonymous TeX or original logs. Work with a new set of outputs; use checksums and revision identifiers.
2. **Respect boundaries.** Routine read, test, reversible edit, benchmark, and checkpoint operations may proceed autonomously. Do not delete/rewrite source data, alter cloud accounts, trigger uncontrolled high-cost compute, disclose identities in a blind submission, or submit anywhere without authorization. Set a defensible compute limit based on observed hardware and owner's constraints; document resource blockers rather than silently degrading scientific controls.
3. **Check before training.** Validate train/test/target splits, official weights/licenses, foreground provenance, render quotas and unique capacities, checkpoint compatibility, masks, metric implementations, seed mapping, and sufficient disk/VRAM. Run a few-example smoke test and a one-epoch pilot on every new code path before a full campaign. A failed preflight invalidates that run; do not convert it to evidence.
4. **No fabricated runs.** Every claimed number must map to an actual result table/log and actual code revision. Historical manuscript numbers must be labeled historical until locally reverified. No selective seed deletion, metric cherry-picking, outcome-dependent stopping, hyperparameter selection on held-out endpoints, or undisclosed changes to original preregistration.
5. **Autonomous recovery.** Checkpoint long-running jobs; record commands and failures. Retry only recoverable faults with the **same** fixed configuration and seed. On an interrupted run, resume only if optimizer/data-loader/RNG state makes resumption equivalent; otherwise rerun from scratch and log the discard. Continue with other independent tasks when a run is blocked.
6. **Independent audit.** Every task must be checked with a second computation or direct input/output comparison where feasible. Distinguish `[ORIGINAL VERIFIED]`, `[NEW VERIFIED]`, `[PARTIAL]`, `[INCONCLUSIVE]`, `[FAILED]`, and `[BLOCKED]`. Do not call exploratory experiments preregistered; freeze new analysis specifications before training to the extent possible.
7. **One owner.** One student is responsible for all experiments, verification, and final package. The agent may parallelize safe independent operations but must produce a single coherent evidence ledger and rebuttal. No assumption that another team member will fill missing evidence.

### Repository discovery (illustrative commands, NOT presumed runnable entrypoints)

```bash
pwd
(git rev-parse HEAD && git status --short) || true
find . -maxdepth 5 -type f \( -iname '*oracle*' -o -iname '*pool*' -o -iname '*manifest*' -o -iname '*verdict*' -o -iname '*coverage*' -o -iname '*train*' \) | sort
rg -n 'CORACLE|C10|CSHUF|CINV|LAKE.RED|S2R|effective.rank|foreground' . --glob '*.py' --glob '*.json' --glob '*.md' --glob '*.yaml' || true
nvidia-smi || true
```

Do not invent scripts named `train.py` or `run_oracle.py` unless you create and test them. Inspect actual CLI flags by reading source and `--help`; record exact invocations once discovered. Repository commits mentioned in the manuscript (`065dac6`, `617a2e1`, `6efde9f`, `c2114af`, `b755aa9`) are **historical pointers**, not assertions of local checkout availability.

### Required machine-readable manifests

Create `STUDENT_RESULTS/RESULT_TABLES/run_manifest.csv` with, at minimum:

```text
campaign,arm,allocation_shape,alignment,model,generator,seed,endpoint,
train_split_sha,target_split_sha,eval_split_sha,calibration_split_sha,
generator_version_sha,foreground_manifest_sha,render_pool_sha,
quota_file_sha,selected_inject_sha,config_sha,git_sha,
round1_checkpoint_sha,round2_checkpoint_sha,metric_code_sha,
mask_qc_report,checkpoint_rule,steps_per_epoch,epochs,source_count,
target_count,injection_count,pseudolabel_count,primary_metric,
raw_prediction_path,raw_log_path,metric_result_path,status
```

Include an `oracle_score_source` field recording `endpoint-label-leaky`, `disjoint-calibration`, or `not-applicable` and an `eligible_capacity_policy` field. Never mix contaminated diagnostic scores with clean held-out performance in one unqualified table.

### Experimental invariants and controls

- **Fixed budget** N=1,000 injected images per arm; base pool and source/target/test splits remain identical within each model×generator cell. If a new generator cannot supply enough unique valid samples, mark the cell infeasible or report an explicitly reduced-budget *separate* experiment; never quietly recycle the same image.
- **Fair comparison within cell:** same optimizer, epochs, step policy, augmentations, seeds, teacher formulation (if supported), checkpoint rule, image size *within architecture*, same generator candidates, same mask provenance; different arms should differ primarily by allocation/selection. Record the unavoidable pseudo-label-count differences from closed-loop feedback.
- **Core arms:** `B` uniformly random from that generator pool, `C10` uncertainty guided, `CSHUF` same allocation shape with shuffled direction. Add `CINV` where affordable; `CORACLE` and oracle variants are **diagnostic** only.
- **Controls:** separate same-shape direction effects (`C10−CSHUF`), concentration-plus-direction effects (`C10−B`), and oracle shape effects (`OR-PROP−CORACLE`, `OR-TOPK−CORACLE`, with suitable same-shape controls). Comparing shape-changed oracle directly with B alone confounds shape and alignment.
- **Evaluation:** COD10K-test Sα is primary for historical equivalence; NC4K secondary and disjoint-label audit. Report per-seed results, paired differences when seeds genuinely comparable, CIs and effect-size scales. Keep original frozen 2-pooled-SD+seed-sign verdict as a separate descriptive historical rule. Do not claim a null proves zero effect; small effects can be unresolved.
- **No test-set tuning:** Calibration true error may use labeled training-/calibration-only images explicitly excluded from training and final evaluation, when the protocol permits. If original CORACLE or a new oracle uses endpoint test masks, treat it as an intentionally leaky *mechanistic stress test*. Neither allocate based on those labels to claim generalization nor select quota form/top-k/temperature on its endpoint performance. Preserve a genuinely untouched endpoint if claiming generalization. If unavailable, say so and give no unbiased conclusion.
- **Generator comparison:** Fix a vetted foreground-diverse render pool for all allocation arms in the new-generator setting. Document whether the generator changes foreground identity, shape, actual foreground pixels, or merely uses **new source cutouts**; these are different expressiveness claims. Pair every training image with a valid mask and audit human quality where necessary.

## 4. Dependency-aware execution schedule

**P0 — execute first, largely CPU:** repository preflight; `AN-01` manuscript claim audit; `TH-01` shape mathematics; `AN-02` quota/probe audit; `TH-02` inferential/test-leakage design; `AN-05` split/endpoint audit; `AN-03` foreground provenance and coverage measurement. Launch `EXP-01` only after oracle definition, quota feasibility, and leakage gates have passed. Use discovered historical runs as baselines rather than training unnecessary duplicates.

**P1 — high:** `AN-04` modern-detector and generator feasibility; `EXP-02` modern detector on existing LAKE-RED; `EXP-03` foreground-varying generator with existing SINet; `EXP-04` combined factorial only if both components pass validation. Execute separately or in parallel within owned resource limits. Preserve independent logs even if a campaign is later abandoned.

**P2 — packaging and clarification:** `DOC-01` manuscript claim edits in a **copy**, then `DOC-02` updated rebuttal, results summary and final audit. Revisit every one of the five reviewer comments, even when experiments fail or remain blocked.

**Preflight stop gates:** missing dataset license/credentials, inability to verify train/test split disjointness, no valid foreground masks, no matching fixed-budget allocation, corrupted/pseudolabeled checkpoint, metric mismatch against a known historical run, or unbounded compute cost. Continue other tasks; write a blocker record rather than guessing.

## 5. Exact executable tasks

Each task below specifies issue mapping, initial commitment, objective/question, inputs, implementation steps, controls, metrics, verification, outputs, acceptance conditions and failure handling. Do not collapse these into a vague task list. Task statuses are recorded individually in `EXPERIMENTAL_EVIDENCE.md` and the execution ledger.

### TH-01 — Allocation shape, direction, and what effective rank logically implies (**P0**)

**Concerns/commitments:** CW-01 and QA-01. Exact initial commitments: “We do not claim that every nonuniform allocation necessarily lowers effective rank”; “We will evaluate error-proportional and top-error-cluster allocations at the same 1,000-image budget, with uniform, C10, CORACLE, and shape-matched controls.”

**Scientific objective and hypothesis:** Distinguish the *direction* of cluster quotas from their *shape* and verify whether the reviewer's proposed universal link between nonuniform budgets and low effective rank follows mathematically (it need not). Define a new oracle-shape test without importing hidden post-hoc endpoint choices.

**Required inputs and dependencies:** Exact cluster IDs (k=75), target embeddings, original errors/scores, C10 quotas, candidate render indices and eligibility capacities; `eq:alloc`, `app:method`, original effective-rank/probe implementation. If using true error, document the labeled source, model used to calculate it, prediction/ground-truth version, and whether labels overlap the endpoint.

**Procedure:**

1. Re-derive `p_j = exp((e_j−max(e))/(τ·sd(e))) / Σ exp((e_l−max(e))/(τ·sd(e)))` and largest-remainder rounding to N=1000. Check that old C10 integer quotas match original source exactly before modifying this code. Define a deterministic tie-break on cluster index and reallocation when candidate quotas exceed unique eligible samples.
2. Define “shape” as the **sorted multiset of integer quotas** and state concentration diagnostics: entropy of quota shares, Herfindahl index `Σ(p_j)^2`, top-1/top-5 share, Gini (definition fixed), and number of funded clusters. Define “direction” through correlation of *unsorted* per-cluster quotas with rank or magnitude of the error/uncertainty signal. A permutation preserves sorted shape/entropy/HHI but changes direction.
3. Define `OR-PROP` from nonnegative error weights `w_j=max(err_j,0)+eps` and `q_j≈N*w_j/Σw`, largest remainder; declare `eps` from a deterministic scale rule before evaluation. If a cluster has no calibration images, use a predeclared shrinkage-to-global-mean strategy and report missingness, not a zero-error assumption. Define `OR-TOP5` and `OR-TOP10` by placing candidate quota mass on the five or ten highest-error eligible clusters, with a deterministic equal or error-proportional split (choose **one** primary implementation before inspecting outcomes). Ensure caps and unique renders are respected; if not, report infeasible and implement a clearly labeled capacity-constrained variant rather than silently breaking fixed N.
4. For each oracle shape generate one score-permuted `OR-PROP-SHUF` and `OR-TOPK-SHUF` matching **exact quota shape**, along with `CORACLE` (C10 shape, true-error direction). Use the same fixed permutation rule or a newly frozen permutation seed; no permutation may be selected based on held-out performance.
5. Formally examine feature covariance of mixtures: between-cluster terms and within-cluster covariance can drive effective rank in opposite directions, so no theorem follows from quota entropy alone. Supply a small **mathematical counterexample or analytic construction** with explicit covariance eigenvalues where changing weights does not yield universally lower rank. This is symbolic/analytic checking, not a new paper training experiment.
6. Verify the **definition of effective rank in the original analysis code** before repeating original values; entropy-of-eigenvalues rank, stable rank, and numerical rank are not equivalent. Recompute existing values only using original implementation first; compare alternate definitions separately, clearly labeled exploratory.

**Controls and metrics:** shape identity, direction rank correlation, quota sum=1000, unique candidate count, eligibility cap, rank-probe outcome, numerical effective rank under original definition, and outcome contrast when training becomes available via EXP-01.

**Acceptance:** equations and randomized tests reproduce existing quota hashes; every new shape passes integer/uniqueness test; a mathematically valid scope argument/counterexample is provided; leaky and clean oracle sources are labeled. **Failure modes:** missing raw error vector, incompatible cluster support, insufficient per-cluster renders, ambiguous original rank definition. Report precise blockers and keep a quota-only result separate from downstream training.

**Evidence/output:** `RESULT_TABLES/TH-01_oracle_shapes.csv`, `RESULT_TABLES/TH-01_quota_properties.csv`, `RESULT_TABLES/TH-01_eligibility_caps.csv`, `EXPERIMENT_LOGS/TH-01_math_verification.md`, tested allocation code and SHA, and a short reviewer-facing qualification suitable for CW-01/QA-01.

### TH-02 — Causal identifiability, oracle leakage, and legitimate statistical interpretation (**P0**)

**Concerns/commitments:** CW-02 and QA-01. Original commitments: “We therefore cannot infer a null for online adaptive generation or other task domains”; “Using test labels for an oracle is an explicitly leaky diagnostic, never a deployable method.”

**Objective/question:** Specify precisely what the original controls identify and what a new modern-detector/foreground-diverse result would identify. Verify statistical estimands without turning non-significance into equivalence or an oracle into a theorem.

**Inputs:** Original preregistration and 103-run evidence, run manifests, the eight-seed comparison, original covariance/rank and coverage diagnostics, test/target labels, and the planned factorial designs.

**Procedure:**

1. Build a causal/experimental design table with factors: architecture `a`, generator content support `g`, quota shape `h`, quota alignment `d`, fixed budget `N`, optimization schedule `o`, training seed `s`, pseudo-labeling feedback `p`; document which comparisons vary which dimensions and what remains uncontrolled. Explicitly record round-2 pseudo-label feedback as a *mediating feature of the loop*, not an independently held constant.
2. For `C10−CSHUF`, argue shape fixed but direction altered; the control tests specificity to score alignment conditional on the same generator support. For `C10−B`, shape and direction change together. For `OR-PROP−CORACLE`, both shape and cap pressure may change; add a matched-shape shuffle to isolate directional contribution *conditional on the new shape*. No design here proves a universally optimal budget.
3. Diagnose true-error label pathways. Distinguish (i) disjoint calibration (diagnostic with legitimately separate held-out test), (ii) endpoint-label oracle (leaky diagnostic only), and (iii) direct test-label hyperparameter tuning (prohibited as a claimed unbiased result). Validate no test labels are read at any stage by standard B/C10/CSHUF training or checkpoint selection.
4. Re-derive the paper's frozen gate: magnitude > `2 * pooled within-arm per-run SD` **and** sign agreement; this is not a sampling-error CI. Do not replace it by `2*SE` after seeing data. If paired seeds exist, compute supplementary `D_s` paired mean, CI, and paired-vs-unpaired variance only after checking actual seed alignment; mark post-review/exploratory. For architecture or generator interaction, calculate `[(C10−CSHUF)_new − (C10−CSHUF)_original]` using independently justified SE/CI, not a difference in raw model scores.
5. Treat the initial eight-seed CI [−0.0020, +0.0067] as an existing historical estimate; it excludes +0.0142 but not small positive gains. The ±0.005 targeting-vs-random equivalence criterion was not met. If new runs are few, emphasize uncertainty and avoid confident directional or generalization claims.
6. Write explicit inferential outcomes: positive with adequate precision, negative/evidence against improvement at a named scale, null unresolved, infeasible. Include architecture-by-generator heterogeneity and mask-quality threats.

**Controls/metrics:** random/targeted/shape-matched, model×generator comparisons, per-run Sα, signed differences, CI with documented method, pooled-SD historical gate, checkpoint-rule compliance, validation-label provenance.

**Verification:** independent numerical implementation against saved seed metrics; derivation of an interaction contrast; validation of split manifests. **Acceptance:** all findings mapped to identifiable estimands with leakage and uncertainty labels. **Failures:** unmatched seeds, unverified preregistration, data leakage or poor variability estimates—record as inconclusive instead of asserting no effect.

**Output:** `EXPERIMENT_LOGS/TH-02_identification_and_statistics.md`, `RESULT_TABLES/TH-02_contrast_definitions.csv`, verified inference script and per-contrast table when results exist.

### AN-01 — Manuscript claims, contribution and reproducibility audit (**P0**)

**Concerns/commitments:** CW-01/CW-02; initial text promises to “sharpen” geometric/detector distinction and narrow abstract/claims/conclusion.

**Objective:** Ensure each statement in the initial/final rebuttal is supported by exact manuscript text, original logs or new verified analysis; identify overbroad causal/universal wording.

**Inputs/dependencies:** Full submitted TeX plus each imported `\input{...}` file if accessible; bibliography; full original repository results; `Caus.md` and Appendix B below.

**Execution:** Parse/inspect all section, equation and label definitions; reconstruct the arms and main/supplementary tables from raw results where feasible. Generate a claim inventory showing claim, exact manuscript anchor, evidence artifact, support level, proposed correction. Search for high-risk phrasings (“not uncertainty”, “no score of any quality”, “perfect oracle”, “all targeting”, “every nonuniform”, “proves”, “generalizes”, “better COD”, “closed loop”) and explicitly mark whether the statement is a tested estimate, post-hoc observation, theoretical statement, or hypothesis. Preserve the independent CHAMELEON finding as a separate contribution without letting it substitute for COD methodological gains. Verify cited BibTeX keys resolve and cited works semantically support their nearby claims; do not invent bibliography replacements.

**Controls/validation:** For each claim use manuscript line/section and data path; second pass against raw results or source code. Give priority to abstract and closing claims. **Acceptance:** all five concerns supported by a claim audit and no unsupported universal language remains. **Failures:** missing imported results, bibliography/figure artifacts unavailable—mark unverifiable.

**Output:** `EXPERIMENT_LOGS/AN-01_claim_audit.md`, `RESULT_TABLES/AN-01_claim_ledger.csv`, reviewer-facing proposed edits for DOC-01.

### AN-02 — Allocation geometry, shapes, distinctness and probe attribution (**P0**)

**Concerns/commitments:** CW-01/QA-01; clarify why same-shape controls matter and preflight new oracle quotas.

**Question:** Does changing quota direction while maintaining shape explain observed geometry; do new shape oracles actually produce a different source sample set, or merely shuffle nearly identical images due to source caps?

**Inputs:** source/target/render candidate IDs, original selection manifests, cluster membership, C10/CSHUF/CINV/CORACLE quotas, input embeddings; source probe train/test split; TH-01 new quota definitions. No GPU required for initial allocation and geometry preflight, unless embeddings must be recomputed.

**Steps:**

1. Recompute original quota shape, `Σq=1000`, score rank, entropy, HHI, effective rank and per-arm selection Jaccard/unique IDs. Inspect original gate that 452–511 of 1,000 injected images differ between controlled arms; verify or mark historical. Audit what happens when multiple clusters pick the same foreground/render.
2. Re-run original probe with its **same** train/held-out splits and leakage controls if source available; separately evaluate a deliberately equally concentrated *wrong-direction* control. Record means, seeds/trials, CIs, source metadata, and statistical dependence due to re-encoded variants; a high AUC on source-versus-synthetic images alone is not evidence of helpful coverage.
3. Generate oracle-shape selection manifests from TH-01, before expensive training. Check new shape's *actual selected render IDs*, not just quotas: unique samples, overlap with B/C10/CORACLE, foreground identity diversity, nearest-neighbor target coverage, and cluster imbalance. Shape may change but selected pool can be near-identical because of capacity or matching rules; quantify.
4. Ensure every shape-matched shuffle has **identical sorted integer quota vector**. Confirm it is meaningfully distinct in direction **and** selection set; if a permutation is practically identical, declare uninformative and use a separately frozen alternative (never select by test outcomes).
5. Flag that lower empirical effective rank may be an artifact of representation normalization or a covariance estimator; reproduce exact pipeline then run labeled sensitivity checks. Distinguish between-cluster and within-cluster covariance.

**Metrics/control:** held-out probe Cohen's d/AUC, effective rank, coverage, HHI/Gini, quota correlation with error, selection Jaccard, unique foreground count, eligible caps. **Verification:** independent quota reimplementation and original hashes; probe label-shuffle check; train/test probe image-group separation. **Acceptance:** selected lists and quota properties are fully reproducible, shape control works as claimed; otherwise mark the affected downstream training as blocked. **Failure:** missing raw rendered pool/embeddings; create reproducibility inventory and do not fake effect sizes.

**Output:** `RESULT_TABLES/AN-02_selection_overlap.csv`, `RESULT_TABLES/AN-02_probe_geometry.csv`, `FIGURES/AN-02_quota_shape_comparison.png` if generated, `EXPERIMENT_LOGS/AN-02_audit.md`.

### AN-03 — Generator provenance, foreground diversity, manifold coverage and label quality (**P0/P1**)

**Concerns/commitments:** CW-03/QA-02; “verify provenance and coverage computations” and assess “genuinely foreground-varying synthesis” with separate mask validity metrics.

**Question:** Does the old pool only repaint backgrounds? Does the new pool add genuinely new foreground content, and are its masks sufficiently valid for a fair COD experiment?

**Inputs:** rendered images/masks, source cutouts, foreground IDs and masks, generator code/checkpoint/seed, target set and held-out evaluation splits, reference feature extractors and coverage implementation.

**Steps:**

1. Locate source-to-render provenance. For each sample, hash/canonicalize source and generated foreground/mask; where necessary register scale/crop transform and test mask-region similarity, not just whole-image hashing. Reproduce or explicitly fail to verify original 8,885-foreground audit. Document near duplicates across train and held-out image splits.
2. Recreate reported 0.13–0.54 synthetic-to-target kNN coverage/recall using **the manuscript's actual embedding family, K, normalization, sample sizes, and threshold definition**, as recoverable from `appendix_coverage.tex` and scripts. If definitions are unavailable, say the range is not independently validated; any alternative recall is new exploratory, never the original metric.
3. Define foreground variation types: (i) same object/cutout with new background, (ii) same object with transformed color/texture, (iii) genuine shape/pose variation with mask adjusted, (iv) new object identities not in original source, (v) generated *new* object pixels/identities. Count and show grouped examples and source lineage without personal/identifying data.
4. For the candidate new generator, audit whether its training data include COD10K-test or NC4K images/masks; confirm licensing for checkpoints and input foregrounds, and exclude test photography from generation, feature prompts, matching, and checkpoint selection. If provenance cannot be established, label evaluation not leakage-clean.
5. Quantify mask-image alignment (boundary agreement on manual/random blinded sample or approved automatic check), mask emptiness, multiple objects/holes, geometry validity, blur/degradation, object-area distribution, and class/foreground uniqueness. Use a fixed quality gate defined before training; report exclusions and rates per arm rather than trimming one arm selectively. If new generator lacks masks, do **not** silently use the old mask for a changed-geometry object.
6. Compare target-manifold recall, per-cluster candidate capacity, foreground identity count, nearest-neighbor coverage, class mix and any realism metric common to both generators; note more coverage does not imply better segmentation. Create figure panels only from permitted data and report reproducible IDs.

**Metrics/control:** verified new foreground IDs/geometry, source-copy rate, valid-mask rate, unique candidates and per-cluster capacities, kNN recall/coverage under same features/K, Sα only after training. **Validation:** independent sample provenance check, human review where feasible, file/hash provenance, metric code cross-check. **Acceptance:** enough *validated distinct* foreground-varying samples for N=1000 per core arm, with mask integrity and split cleanliness; otherwise `EXP-03/04` are BLOCKED with the reason. **Failure:** unavailable weights, unreliable masks, no new foregrounds, licensing or contamination problems.

**Outputs:** `RESULT_TABLES/AN-03_foreground_provenance.csv`, `RESULT_TABLES/AN-03_coverage_and_qc.csv`, `FIGURES/AN-03_generator_qc.png` if appropriate, `EXPERIMENT_LOGS/AN-03_generator_audit.md`.

### AN-04 — Modern detector integration and protocol parity preflight (**P1**)

**Concerns/commitments:** CW-02/QA-02; assess modern transformer COD detector while preserving comparable allocation contrasts.

**Objective:** Select **one** trainable modern detector and configure a fair comparison before evaluating outcomes; do not choose model after seeing favorable gains.

**Inputs:** existing SINet trainer/data loader, target/student-teacher scores, modern detector candidate code/checkpoint, source/target/train/test manifests, GPU budget, original checkpoint metric implementation.

**Candidate rule (proposed, not a result):** First consider **CamoFormer** (2024 TPAMI, transformer-based; official repository `https://github.com/HVision-NKU/CamoFormer`). Its public repository shows model/test/evaluation code, but **not an obvious complete training entrypoint**; ascertain trainability locally rather than guessing. Alternative **CTF-Net** (2025 CNN–Transformer; repository `https://github.com/zcc0616/CTF-Net`) only if CamoFormer cannot be reproducibly integrated. Any replacement must be declared with reasons **before** analyzing outcomes, prefer models with checkpoint and training code and compatible license. A more recent COD model with full official train pipeline can be substituted if its provenance and backbone character are verified; do not silently change design.

**Procedure:** Inventory exact source files, checkpoint downloads/hashes, PyTorch/CUDA/VRAM, training CLI, model output convention, logits/probabilities, student/teacher forward contract, 352×352 vs native resolution implications, checkpoint selection on CAMO-250, and any difference in preprocessing. Implement a minimal adapter that maps the model into the existing two-round training and Sα evaluation. If integration requires changing the loss/training schedule, first reproduce a stable model baseline with those settings and disclose it; all arms **within modern detector cell** must share settings. Run data-loader/forward/loss/backprop smoke tests, one small training pilot and exact metric parity check before new campaigns. Predeclare seeds and compute plan; don't use COD10K-test to tune any training decisions.

**Controls/metrics:** one-backbone B/C10/CSHUF with identical source and generator, primary Sα and secondary NC4K, per-seed variability, checkpoint MAE CAMO-250, total training steps/compute; optional CINV. **Validation:** compare reproduced public checkpoint metrics only as an implementation sanity check, not a valid substitute for trained arm comparison. Verify checkpoint selection split is distinct from test and no CHAMELEON leak. **Acceptance:** demonstrably trainable reproducible modern model with multi-arm parity. **Failure:** missing train code/weights, unsupported GPU, output format incompatible, costs beyond capacity. Record and leave EXP-02/04 blocked rather than reporting an untrained comparison.

**Output:** `EXPERIMENT_LOGS/AN-04_model_integration.md`, verified model adapter/config, `RESULT_TABLES/AN-04_preflight.csv`, chosen candidate rationale and source revision.

### AN-05 — Leakage, oracle calibration and endpoint audit (**P0**)

**Concerns/commitments:** QA-01, CW-02/03; prevent diagnostic oracle scores from becoming circular evaluation or contaminating generator/detector transfer.

**Objective:** Trace exactly which labeled photographs/masks affect quotas, model weights, pseudo-label selection, generator inputs, checkpoint selection and reported endpoints.

**Inputs:** sample identities/hashes, split lists and reencode-aware duplicate detector; original CORACLE score source; candidate calibration split; all new datasets/generator training source information.

**Steps:** Build a `sample_id → provenance(s) → role(s)` ledger for base source, unlabeled target, calibration, generator conditioning/weights where auditable, CAMO-250 checkpoint selection, COD10K-test and NC4K. Run hash and re-encode-aware near duplicate checks on accessible images; report unresolved uncertain pairs, not assume no overlap. Audit the *original* CORACLE explicitly as a test-label diagnostic. Choose separate calibration labels from permissible labeled data if any while avoiding simultaneous inclusion in base training or evaluation; otherwise run only leaky diagnostic allocation and do not report unbiased COD10K-test improvement. Check independent NC4K if genuinely not used for oracle allocation/hyperparameter choices. Prevent any modern model pretrained on evaluation splits from being called a clean transfer test without disclosures. Do not use CHAMELEON as a clean outcome given manuscript contamination audit.

**Metrics/control:** duplicate/exposure counts, exact split hashes, oracle score-source identity, no-test-label-access standard arms, signed exposure flow diagram. **Verification:** file-level provenance cross-check and second independent split comparison; audit code access paths. **Acceptance:** every arm's contamination risk explicitly classified; clean endpoint exists for any claimed generalization. **Failure:** dataset identity inaccessible/unclear, unverifiable model pretraining leakage, target labels used in training—label outcome diagnostic only.

**Output:** `RESULT_TABLES/AN-05_split_audit.csv`, `EXPERIMENT_LOGS/AN-05_leakage_and_calibration.md`, `FIGURES/AN-05_dataflow.png` if produced.

### EXP-01 — Fixed-budget *different-shape* oracle campaign (**P0; core reviewer request**)

**Concerns/commitments:** QA-01, CW-01. Exact promise: “We will evaluate error-proportional and top-error-cluster allocations at the same 1,000-image budget, with uniform, C10, CORACLE, and shape-matched controls, checking realized quotas and distinctness.”

**Scientific question:** Does an oracle that can change quota **shape**, rather than only move C10's quota multiset among clusters, materially improve held-out COD detection under the original generator's fixed capacity? How much is attributable to shape versus error-informed direction?

**Inputs and prerequisites:** Passed TH-01, TH-02, AN-02, AN-05 audits; original SINet/SINet-v2 configs and verified B/C10/CORACLE selection/prediction manifests; k=75 assignments; valid rendered pool; source and target splits; error estimates and provenance. Prefer a calibration split that does not also serve as an endpoint. Keep the original N=1000 and the original training/metric pipeline; if changing training code, write a separate prospective campaign and do not merge its results into original 103-run figures.

**Experimental design (freeze before outcome inspection):**

| Arm | Quota shape | Quota direction | True-error access | Why included |
|---|---|---|---|---|
| B | uniform random realized draw | none | no | Fixed-budget control |
| C10 | original uncertainty softmax τ=1.0 | uncertainty | no | Original targeted comparator |
| CORACLE | **C10 fixed multiset** | true-error rank | yes, diagnostic | Prior oracle baseline, confirms fixed-shape behavior |
| OR-PROP | recomputed proportional-to-error weights | true error | yes, diagnostic | Alternative continuous shape |
| OR-PROP-SHUF | **identical OR-PROP multiset** | pre-frozen shuffle | score values for shape only | Matched-shape direction control |
| OR-TOP5 | mass to top 5 true-error clusters subject to caps | true-error rank | yes, diagnostic | Stronger concentration |
| OR-TOP5-SHUF | identical OR-TOP5 multiset | pre-frozen shuffle | score values for shape only | Matched-shape direction control |
| OR-TOP10 | mass to top 10 true-error clusters subject to caps | true-error rank | yes, diagnostic | Less extreme top-k control |
| OR-TOP10-SHUF | identical OR-TOP10 multiset | pre-frozen shuffle | score values for shape only | Matched-shape direction control |

If cost prohibits all arms, primary priority is B, C10, CORACLE, OR-PROP, OR-PROP-SHUF, OR-TOP10, OR-TOP10-SHUF; **do not** silently claim to have evaluated TOP5. Predeclare any smaller plan with rationale *before training*. Fix three historical-style seeds 42,43,45 for initial comparable SINet/COD10K estimates, with expanded seeds 46–50 only if resource budget permits; expansion is a separate post-review analysis and must not be used as outcome-driven optional stopping. Reusing historical B/C10/CORACLE models is allowed **only** if every model/data/config/endpoint identity is verified against the new campaign's controls. Otherwise rerun under consistent protocol.

**Implementation sequence:**

1. Calculate error estimates with explicit label provenance: ideally a disjoint calibration set, assigning calibration images to frozen target clusters without fitting clusters on evaluation labels; if no such set, use endpoint-label oracle only as an **intentionally leaky diagnostic** and identify a truly untouched endpoint (if one exists). Do not use final test scores to choose ε, top-k, temperatures, or training hyperparameters.
2. Produce quota vectors for `OR-PROP`, TOP5 and TOP10 using TH-01 deterministic rounding/cap rules. Audit sum=1000, valid eligible cluster capacities and exact shape hashes. For clusters where requested quotas exceed available eligible renders, predeclare deterministic spillover to next rank; record the *realized* shape. If original goal (e.g., top5-only allocation) cannot be realized without duplicates or breaking budget, label that named arm **infeasible**, and distinguish any relaxed cap-constrained variant.
3. Construct every injected set with the same foreground-matching selector used by C10, as appropriate; ensure no test image or mask is injected. Save raw per-image selection IDs, source foreground ID, cluster, quota, scores, and all hashes. Create exact shape-preserving wrong-direction selections with independent pre-frozen permutation. Verify selected-set overlap and pseudo-label feedback.
4. Test loading, 1 batch loss/backprop, 1 epoch, checkpoint-restart reproducibility and Sα scorer on one known checkpoint. No new large run until the gates pass. Train through the original two-round protocol at committed steps/epoch, architecture, seed and checkpoint-selection rule. All arms receive equal N and same eligible rendered support, and all standard arms are **blind** to endpoint labels.
5. Report per-seed COD10K-test and NC4K `Sα`, exploratory E/F/MAE only with source and threshold documented, and paired or appropriately unpaired differences. Primary contrasts: OR-PROP vs CORACLE, OR-TOP10 vs CORACLE (**shape+potential matching effects**), OR-PROP vs OR-PROP-SHUF (**direction at new shape**), OR-TOP10 vs its shuffle, and each versus B/C10. Do not call these comparisons a generator upper bound or a proof of no useful allocation. Include bootstrap/t CI only where assumptions/samples allow meaningful interpretation.
6. On the *leaky* oracle path, write prominently that target labels were used to generate training-set quotas; COD10K-test is no longer an unbiased assessment of a feasible strategy. If the ranking is derived from COD10K-test and the score is read on NC4K without using NC4K labels, discuss domain coupling and residual dependence rather than asserting total independence.

**Metrics/controls:** Sα on both endpoints, differences with uncertainty, sign consistency, candidate/realized quotas, top-k concentration, selected-set Jaccard, identities, mask validity, leakage flags, training steps, pseudo-label count, GPU hours. Retain original two-SD campaign verdict as historical and classify new inference as exploratory unless a new precommitted analysis exists.

**Acceptance:** At least one **genuine shape-changed oracle** and its same-shape shuffle are demonstrably feasible and run on comparable fixed-budget valid data; every claim backed by raw per-seed logs. A clean calibration-based comparison is preferred but not assumed. **Failure conditions:** no independent calibration, insufficient pool capacity, corrupt labels, unavailable training GPU, posterior outcome tuning, or same-shape-control mismatch. A quota-only preflight is **PARTIALLY VERIFIED**, not a completed detector experiment.

**Expected artifacts:** `RESULT_TABLES/EXP-01_quota_manifests.csv`, `RESULT_TABLES/EXP-01_metrics_by_seed.csv`, `RESULT_TABLES/EXP-01_comparisons.csv`, `EXPERIMENT_LOGS/EXP-01/` (actual run logs and command/config manifests), optional `FIGURES/EXP-01_shape_vs_direction.png`, source patch and review-facing 150–250-word finding with evidence IDs.

### EXP-02 — Modern COD detector × existing LAKE-RED pool (**P1**)

**Concerns/commitments:** CW-02/QA-02. Promise: “We will assess a reproducible modern transformer-based COD model... [preserving] comparable budgets, splits, evaluation and checkpoint protocols.”

**Question:** Does the absence of a resolved uncertainty-direction benefit persist when the **detector** changes but source data, offline generator, and allocation protocol are held fixed?

**Inputs:** AN-04 chosen modern detector/adapter and checkpoint, passed code/mask/split preflight, original LAKE-RED N=1000 pool, B/C10/CSHUF assignment rules; TH-02 stats plan; AN-05 leak audit.

**Procedure:**

1. Freeze the architecture and training settings before reading new endpoint results. Convert selected masks/predictions to the detector's native output format. Keep **identical model/optimizer** setup across B, C10, CSHUF; preserve two-round training and pseudo-label rules where technically possible. If impossible (e.g., original teacher consistency loss incompatible), explicitly define a *matched alternate training regime for all three arms* and identify the altered research question; never represent it as an exact S2R-COD replication.
2. Decide whether to recompute uncertainty scores using the new detector's student/EMA teacher and the original frozen target clusters. This is the primary design if the adaptation works. A fixed old uncertainty vector is an interesting secondary “transfer-of-ranking” diagnostic but must not be silently presented as new-detector active targeting. Record what information each arm's selection used.
3. Train B, C10, CSHUF on matched budget/data and fixed seeds 42,43,45 (additional seeds 46–50 if realistically resourced, prespecified). Use same checkpoint selection scheme and no COD10K-test hyperparameter tuning. Log all pre/post-round pool sizes, pseudo-label counts and step policies.
4. Generate and check each checkpoint's COD10K-test Sα and NC4K Sα (plus boundary metric if code and preregistered plan permit); compute C10−B and C10−CSHUF with uncertainty. Compare *directional contrast* to SINet/SINet-v2, **not raw model performance across backbones**, which has different score baselines.
5. Verify quality of first-round uncertainty and cluster score calibration; report any inability to create teacher/consistency scores. Include how much selection overlaps source and whether modern model has higher/lower variance.

**Controls:** identical generator/splits across modern arms, positive sanity baseline using model-native supervised training, no test-label oracle in standard arms; hold allocation temperature/budget fixed unless documented exploratory sensitivity. **Metrics:** Sα, variance/seeds, relative contrasts, architecture×policy interaction from TH-02, GPU-hours, convergence and mask validity.

**Acceptance:** complete B/C10/CSHUF modern-detector runs and raw metrics under identical feasible settings; transparent comparability statement. **Failure:** no trainable model, incompatible teacher, insufficient GPU, known split leakage, unstable baseline. Mark `BLOCKED` or `INCONCLUSIVE` with reasons; a released model's original benchmark score **does not** answer the reviewer.

**Outputs:** `RESULT_TABLES/EXP-02_modern_detector.csv`, selection manifests, config hashes, `EXPERIMENT_LOGS/EXP-02/`, and a short comparison paragraph grounded in actual values.

### EXP-03 — Existing SINet × genuinely foreground-varying synthesis (**P1**)

**Concerns/commitments:** CW-03/QA-02. Promise: “if suitable generation code and masks are available, compare against genuinely foreground-varying synthesis at a matched budget.”

**Question:** Does providing new source foreground identities/geometry (or genuinely synthesized foregrounds) make uncertainty selection more useful than matched random and same-shape controls? Alternatively, do the results remain unresolved with coverage and mask validity adequately quantified?

**Inputs:** AN-03 vetted new render pool with N≥1000 valid unique candidates per required arm, new source foregrounds/labels/provenance, original SINet trainer and data splits, target clusters and matching embeddings, AN-05 leak audit.

**Generator selection guidance:** First check whether author-owned code already supports object/foreground changes. If not, explore a legally usable generation approach such as **Camouflage Anything** (CVPR 2025; https://openaccess.thecvf.com/content/CVPR2025/html/Das_Camouflage_Anything_Learning_to_Hide_using_Controlled_Out-painting_and_Representation_CVPR_2025_paper.html) using **new non-test source segmented objects**, with careful distinction between using different object cutouts and synthesizing new object pixels. This is an **external candidate, not a verified plug-in or guaranteed mask generator**. If a generator only paints backgrounds around the *same LAKE-RED cutout catalog*, it fails the foreground-variation criterion. Another qualified method can be chosen only after code/weights/masks/license and provenance audit; log decision before outcome inspection. Do not derive new foreground masks from test-set ground truth or hallucinate masks for changed geometry.

**Procedure:**

1. Freeze a single vetted new-generator output pool, source identities and masks. Ensure it is available equally to all selection arms and is not built using evaluation images. Keep N=1000 per arm and original k=75 target clusters. Because the new generator may change the eligible foreground domain, recompute foreground-to-cluster matching and per-cluster capacities **once**, before training, with a documented matching algorithm common to all arms.
2. Construct B (uniform new-generator sample), C10 (same student–teacher-driven quota rule, τ=1), and CSHUF (identical C10 integer quota shape, permuted alignment) under an identical pool. If shape-preserving permutation is infeasible due to caps, report it and choose a predeclared feasible permutation; no outcome-based choice.
3. Train original SINet under an unchanged two-round, split, checkpoint and metrics protocol; use fixed seeds 42,43,45, with further seeds prespecified only if available. Reproduce at least one known original B/C10 validation checkpoint as a sanity check; do not compare old and new source data under different training exposure without disclosure.
4. Measure per-seed Sα on COD10K-test and NC4K; C10−B and C10−CSHUF on new generator; changes in C10−CSHUF between LAKE-RED and new generator using TH-02. Report sample validity and coverage separately, ensuring possible benefits do not derive from test contamination or larger training data.
5. Audit foreground identity/shape count and pixel/label alignment **after** final selected sets. Keep invalid samples in an explicit preflight exclusion record, not selectively deleted after reviewing accuracy.

**Controls/metrics:** fixed N/splits/architecture, sample-level identity, kNN coverage under same features, valid-mask rate, select-set overlap, Sα with seed variability, computational cost, blinded image QC. **Acceptance:** a sufficiently varied, mask-valid new pool; B/C10/CSHUF all run fairly; truthful inference. **Failures:** no genuine new foregrounds, mask misalignment, generator weights or code unavailable, source contamination, insufficient unique per-cluster candidates, compute shortfall. If only pool validation is complete, mark experiment `PARTIALLY VERIFIED` and say no performance generalization is possible.

**Outputs:** `RESULT_TABLES/EXP-03_diverse_generator.csv`, `RESULT_TABLES/EXP-03_mask_and_coverage.csv`, run logs/selection/QC manifests, `EXPERIMENT_LOGS/EXP-03/` and a quantitative reviewer-facing note.

### EXP-04 — Combined modern detector × foreground-varying generator factorial (**P1 conditional, highest compute cost**)

**Concerns/commitments:** QA-02, CW-02 and CW-03. Promise: “Testing the backbone and generator factors separately before their combination will clarify attribution.”

**Question:** Is the contribution of score direction to segmentation conditional on both the model family and the expressiveness of the generator? This experiment distinguishes *interaction* from simply having a strong modern detector or richer training images.

**Entry gates:** EXP-02 passed with a trainable modern model, EXP-03 passed with mask-valid truly varied foregrounds, fixed split/evaluation protocol and sufficient compute to run a fair matched-budget comparison. If either gate fails, **mark this task `BLOCKED`**, but still finish all independent audits/writing tasks.

**Design:** A common factorial table across `architecture ∈ {SINet, modern}` and `generator ∈ {LAKE-RED, varied}` with `allocation ∈ {B, C10, CSHUF}` at **N=1000** each. The SINet×LAKE-RED cell comes from original runs *only if matching configs/seed/data exactly*; otherwise rerun or label cross-cell comparison not fully causal. Each architecture×generator cell uses **identical internal arm settings**, while model-native training differences between architecture cells are documented. Recompute student–teacher uncertainty for each model (if supported) and keep target cluster definition common; when generator candidates differ, retain common matching logic and record eligible capacities. Fix seeds beforehand (42,43,45 minimum planned, more as budget permits); if not enough compute for all cells, label the design partial rather than compare an unbalanced cherry-picked subset.

**Procedure:** Use validated EXP-02/03 protocols; train the missing modern×varied B/C10/CSHUF cell. Create a complete 2×2×3 table of Sα per seed and relevant QC metadata. Estimate within-cell C10−CSHUF (direction at equal shape) and C10−B (confounded compound contrast). For generator interaction on a given architecture, subtract the two C10−CSHUF effects (varied minus LAKE-RED). For architecture interaction, subtract modern minus SINet directional effects at fixed generator. If all cells exist, present a factorial difference-in-differences/interaction with uncertainty calculated using the actual covariance/seed structure. Do **not** infer interactions merely because one cell has p<0.05 and another does not.

**Controls:** identical budget, clean split, valid masks, no endpoint-label oracles, fixed outcome and selection metric, architecture-specific optimization parity across arms. **Metrics:** per-seed COD10K-test and NC4K Sα, CIs/sensitivity, interaction effect, coverage/QC, GPU-hours and systematic failure rates. **Verification:** rerun statistical aggregation independently; check full factorial missingness and all raw hashes. **Acceptance:** at least the missing modern×varied B/C10/CSHUF cell and a reproducible well-documented comparison across factors; if original cells are not comparable, report within-cell only. **Failures:** input gates, large compute cost, model×generator incompatibility, inadequate seed sensitivity or deployment-level leakage. Preserve partial outcomes.

**Outputs:** `RESULT_TABLES/EXP-04_factorial.csv`, `RESULT_TABLES/EXP-04_interactions.csv`, `EXPERIMENT_LOGS/EXP-04/` and optional `FIGURES/EXP-04_interaction.png`.

### DOC-01 — Manuscript clarification and reviewer-facing contribution statement (**P0/P2**)

**Concerns/commitments:** CW-01/CW-02/QA-02; clarify what transfers and what does not. No new numerical result is prerequisite for basic honest wording.

**Inputs:** AN-01 claim audit, TH-01 and TH-02 conclusions, original TeX and any newer verified results.

**Steps:** Work in `rebuttal/Caus-oracle-scope` only. Create a patch or proposed insertion in `sec:intro` contribution bullets, `sec:concentration`, `sec:why`, `sec:discussion`, `sec:conclusion`, and abstract. Suggested *substance*, not mandated exact prose: “Within the tested offline LAKE-RED/S2R-COD synthetic-to-real COD pipeline, uncertainty-aligned allocation did not produce a resolved advantage over random or same-shape shuffled allocation at the measured sensitivity; this does not establish inefficacy of richer foreground-generating closed loops.” Explain that fixed C10 quota multiset for CORACLE **only** tests direction; lower effective rank is empirical rather than universal; probe geometry is independent of downstream score; foreground coverage is a plausible but unproven causal bottleneck. Keep the separate CHAMELEON audit with original evidence and do not silently remove inconvenient results. Check figure/table references for compilation and resolve only available LaTeX inputs. Do not quietly modify the submitted file.

**Controls/verification:** compare patch to original, math/section labels, bibliography, no unverified numbers, no claims that post-review work is complete when blocked; if compilation is impossible due to missing imports, document that explicitly. **Acceptance:** concise proposed claim revisions mapped to CW-01/CW-02/CW-03 and QA-02. **Failure:** missing imports prevent compilation—deliver a valid patch/annotated edits anyway.

**Output:** `STUDENT_RESULTS/RESULTS_SUMMARY.md` section “Manuscript wording recommendations”, proposed `manuscript_scope_edits.patch` in STUDENT_RESULTS if source modified, and claim-to-sentence table in `EXPERIMENT_LOGS/DOC-01_edits.md`.

### DOC-02 — Full reviewer response, results summary, evidence ledger and final scientific audit (**P0/P2; required even if runs blocked**)

**Concerns/commitments:** CW-01–03 and QA-01–02; all five original answers in Appendix B must be updated with **verified** results and explicit limits. Final author retains submission authority.

**Steps:** Collect each task's status and proof: raw command/log, code SHA, dataset/selection manifest and checksum, seed list, metrics and independent recalc, output path and interpretation. Prepare `FINAL_UPDATED_REBUTTAL.md` in authors' plural voice with one section per reviewer issue and **Response → Additional Validation → Results → Interpretation**. Do not merely append a table; directly answer QA-01 **No in the submitted paper; here's what we subsequently tested or why it was blocked**. Differentiate fixed-shape CORACLE, new shape oracles, old models versus modern models, old backgrounds-only generator versus authentic new foregrounds, and clean versus leaky oracle evaluations. Explicitly state if an ambitious experiment was infeasible. Compress a **second file** `FINAL_UPDATED_REBUTTAL_OPENREVIEW_5000.md` to ≤5000 Unicode characters (count Markdown as plain text) if the platform limit remains 5000; verify platform current limits before final posting. If verified new evidence is sparse, do not overstate resolution.

Write `RESULTS_SUMMARY.md` with (i) new results and historical baseline separately, (ii) count of verified tasks, (iii) figure/table references to real output files, (iv) materially unresolved points. Write `EXECUTION_STATUS.md` with progress/errors/blockers. Write `EXPERIMENTAL_EVIDENCE.md` with an evidence row per task including run commands, code/data hashes, training seed, hardware software, raw artifact paths, provenance, quality and outcome. Audit **every concern** as `FULLY ADDRESSED`, `SUBSTANTIALLY ADDRESSED`, `PARTIALLY ADDRESSED` or `UNRESOLVED` in `FINAL_SCIENTIFIC_AUDIT.md`. Produce `CODE_CHANGES.patch` if source code changed; if not, state “No source-code changes necessary” in execution status and do not fabricate patch. Finally package `STUDENT_RESULTS/` as a portable archive for the corresponding author after validating links/hashes.

**Verification:** The author should be able to reproduce every added table entry from cited raw artifacts; re-run table calculations in a second script or independently compare raw CSV aggregates; grep all final Markdown for unsupported “completed,” “proves,” “oracle optimal,” and broadened null statements. Check 5,000-character count on OpenReview-ready copy. **Acceptance:** every CW/QA accounted for; logs and verified numbers traceable; unresolved work explicitly classified; output packaging complete. **Failure:** missing runs do not prevent honest partial updated response; label missing evidence rather than guess.

## 6. Scientific result verification — mandatory procedure for each task

For **each** completed analysis or experiment, perform all applicable checks below and record them in `EXPERIMENTAL_EVIDENCE.md`:

- Command/run identifiers exist and correspond to **actual executed** code and artifacts (not a sample command or speculative plan); original and new runs have separate provenance.
- Train/source/target/test/calibration dataset hashes and generator foreground IDs are traceable; model weights/checkpoints and seed values are recorded.
- Quota sums, finite capacities, shape-preserving permutations, and realized selected-set identities are verified, not just requested.
- Prediction masks match ground-truth filenames without off-by-one, resizing or normalization errors; mask quality and empty-mask rates are logged.
- Sα is independently recomputed from saved predictions on a subset/full test where feasible and agrees with reported metrics within a documented numerical tolerance.
- Statistical intervals and decision rules are correct; no selective endpoint/seed/metric reporting. When n is small, explain interval instability. Do not equate an unresolved difference with proof of no effect.
- Oracle score provenance is **explicit**: any test-label usage is tagged as leaky diagnostic and cannot support unbiased evaluation claims.
- Cross-model/cross-generator comparisons use within-cell effects, not unsupported raw score comparisons, and account for source/model/generator dependencies.
- Negative, unexpected, unstable, and failed outcomes are recorded with exactly the same status discipline as successful ones.
- Relevant manuscript claims and proposed edited sentences cite actual evidence; all imported table/figure references are checked where available.

**Task statuses (use exactly):** `VERIFIED`, `PARTIALLY VERIFIED`, `INCONCLUSIVE`, `FAILED`, `BLOCKED`. `VERIFIED` says the analysis/run is executed and traceable, **not** that it supports the authors' favored hypothesis. Audit classifications are a different controlled vocabulary: `FULLY ADDRESSED`, `SUBSTANTIALLY ADDRESSED`, `PARTIALLY ADDRESSED`, `UNRESOLVED`.

**Example evidence-table header** (replace with real lines after execution):

```text
Task ID | Reviewer issue | Status | Claimed result | Command + git SHA |
Dataset/split hashes | Model + generator revision | Seeds | Config + quotas |
Output artifact path | Independently checked against | Leakage flag |
Scientific interpretation | Limitations
```

If `BLOCKED`, include missing item, what discovery commands were tried, exact error, resources/permission needed, alternate route attempted, and scientific claim that cannot be made. Do not write “GPU unavailable” without identifying what was attempted. If `FAILED`, preserve logs and note the point at which validity was lost; never quietly delete a failing run.

## 7. Final required directory structure and handoff

Create **only initial files** for planning on the author's side. On the student's machine, materialize the following as the *output of actual work*:

```text
ICLR2027_REBUTTAL_Caus/
├── 01_INITIAL_REBUTTAL_FOR_SUBMISSION.md           # author's original, immutable
├── 02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md        # author's original, immutable
├── 03_STUDENT_AGENT_EXECUTION_INSTRUCTIONS.md      # this complete guide, immutable
└── STUDENT_RESULTS/
    ├── FINAL_UPDATED_REBUTTAL.md
    ├── FINAL_UPDATED_REBUTTAL_OPENREVIEW_5000.md
    ├── RESULTS_SUMMARY.md
    ├── EXPERIMENTAL_EVIDENCE.md
    ├── EXECUTION_STATUS.md
    ├── FINAL_SCIENTIFIC_AUDIT.md
    ├── CODE_CHANGES.patch                         # only if source actually changed
    ├── manuscript_scope_edits.patch                # if proposed patch exists
    ├── EXPERIMENT_LOGS/
    │   ├── EXP-01/  EXP-02/  EXP-03/  EXP-04/      # directories for executed tasks only
    │   └── AN-*/TH-*/DOC-* supporting reports
    ├── RESULT_TABLES/
    └── FIGURES/
```

**Required handoff:** the verified `FINAL_UPDATED_REBUTTAL.md` is the principal scientific deliverable; the shortened OpenReview version is a convenience requiring human review. Provide an archive of `STUDENT_RESULTS/` with checksums, summarize 5 concern-level dispositions and 13 task statuses, and highlight any risk to original claims. No output Markdown may reference an artifact path that does not actually exist *when the student finishes*. Relative Markdown links must resolve within the handoff archive. If there are no figures/patch files, omit those file links and state why. Do not substitute synthetic screenshots or fabricated console logs.

## 8. Final machine-checked audit checklist

Before finishing, check every item, marking unmet ones as blockers rather than silently passing them:

- [ ] All **3 critical weaknesses** and **2 questions** have an initial commitment, task mapping and final response.
- [ ] Submitted TeX was preserved; any revision is in a branch/copy with auditable diff.
- [ ] Original CORACLE fixed-shape property is verified, and new **different-shape** oracle experiments are distinguishable from it.
- [ ] At least one genuine new quota shape plus a **same-shape shuffle** was preflighted; if it could not be trained, report what did and did not happen.
- [ ] All oracle labels are documented as disjoint calibration or leaky test-endpoint diagnostic.
- [ ] Probe/effective-rank claims never stand in for downstream COD improvements.
- [ ] Modern backbone choice and completeness of train code were verified, not assumed from an inference-only repository.
- [ ] Foreground-diverse generator genuinely changes foreground inventory/content and supplies valid masks; mere background variation is not described as foreground variation.
- [ ] Fixed-budget B/C10/CSHUF controls and realized pool sizes/split hashes match within each experimental cell.
- [ ] At least one independent recomputation checks every new key numerical claim.
- [ ] New inference reports seed variability and avoids claiming equivalence from a non-significant result.
- [ ] Generator and architecture scope of any remaining null is carefully bounded.
- [ ] Every missing dependency and blocked/failed task is transparently identified.
- [ ] Final rebuttal remains consistent with the author's initial commitments, correcting any assertion contradicted by new evidence.
- [ ] No claims of generalization from leaky label-oracle performance or CHAMELEON overlap.
- [ ] Both final rebuttal versions are prepared, with the OpenReview copy character-counted if limit applies.
- [ ] Final evidence, run logs, data hashes, code patch (when applicable), status and scientific audit exist and every linked path resolves.
- [ ] No automatic OpenReview submission, no irreversible action without permission, and no suppression of unfavorable results.

## 9. Response-writing template for use **after** validation (not to be filled with invented data)

Use exactly one section per review item, using the authors' plural voice:

```markdown
# Updated Response to Reviewer Caus

We thank the reviewer for [appropriate acknowledgment].

### CW-01: Methodological contribution
**Response.** [Correctly bounded contribution, sourced from manuscript.]
**Additional Validation.** [TH-01/AN-01/AN-02 actions actually executed.]
**Results.** [Verified figures only, linked to evidence; or explicit blocked status.]
**Interpretation.** [What concern is resolved, what remains.]

### CW-02: Generalizability
... same four parts ...

### CW-03: Generator bottleneck
... same four parts ...

### QA-01: Different-shape oracle
**Response.** No different-shape oracle was in the submitted paper.
**Additional Validation.** [Report OR-PROP/TOPK and controls or infeasibility.]
**Results.** [Distinguish clean calibration and leaky diagnostic.]
**Interpretation.** [No universal optimality claim.]

### QA-02: Modern backbone and new generator
... same four parts; scope to measured pipeline ...
```

**Author control:** The corresponding author approves all claims and decides whether/when to post either the initial or the verified updated rebuttal. The student/agent must **never** post on OpenReview, expose identifying affiliations in blind-review content, or alter the original review.

---

## Appendix A — Exact reviewer comments (`Caus.md`, verbatim)

The passage below is copied from the review file; preserve any wording irregularities, do not paraphrase in source quotes. Our issue IDs are:

- **CW-01:** paragraph beginning “The main contribution of this paper...”
- **CW-02:** paragraph beginning “Bounded Scope...”
- **CW-03:** paragraph beginning “Generator Expressiveness Bottleneck...”
- **QA-01:** “CORACLE keeps C10's shape...”
- **QA-02:** “Replicate with one modern backbone...”

```markdown
# Paper Summary:

This paper investigates whether an uncertainty-guided closed-loop strategy can efficiently allocate a fixed synthetic data generation budget (e.g., 1,000 images)

The authors evaluate a standard active-learning-style loop: Cluster unlabeled real target images into k=75 clusters using self-supervised representations (DINOv2)

Measure model uncertainty across clusters using a student–teacher disagreement score

Allocate more synthetic images to clusters where the model is least certain using a softmax temperature distribution.

Append the synthetic data to the training pool and retrain the model

Key Finding — Null Result on Uncertainty: Across 103 training runs, uncertainty-based targeting does not beat allocating synthetic data uniformly at random on downstream segmentation accuracy.
## Presentation: 2: Generally understandable, but requires substantial effort in places.
## Informativeness: 2: I learned something interesting or useful.
## Soundness: 1: I have significant concerns about the paper’s soundness that do not appear easy to address.

# Critical Strengths:

Authors introduces the "same-shape shuffle" control to decouple budget concentration (shape) from budget direction (aim). This exposes a major drawback present in prior synthetic data allocation literature.

In-Depth Failure Diagnosis: Rather than stopping at a null result, the authors rigorously analyze why the loop failed (clustering silhouette analysis, within vs. between error variance, manifold coverage)

# Critical Weaknesses:

The main contribution of this paper is the validation of null hypothesis i.e. Any non-uniform allocation is separable from a uniform draw with lower effective rank, so the probe result is only as good as a sanity check . From a contribution view point this has limited role in advancing the camouflage object detection methodology.

Bounded Scope: The conclusions are bounded to Camouflaged Object Detection (COD) using the LAKE-RED generator, SINet/SINet-v2 architectures, and background replacement. Findings may not directly transfer to task domains with vastly more expressive generative feedback loops.

Generator Expressiveness Bottleneck: The generator is constrained to reusing fixed foreground cutouts, creating a narrow synthetic distribution (0.13 --0.54 manifold coverage) that may inherently limit the potential benefit of any steering policy
# Questions For Authors:

CORACLE keeps C10's shape. Did you test an oracle with a different shape (e.g., proportional to true error, or concentrated on the truly worst clusters)?

Replicate with one modern backbone and one foreground-varying generator, and scope the claim to the LAKE-RED/S2R-COD pipeline.
## Flag For Ethics Review: No
## Rating: 2: Weak rejection
## Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.
```

---

## Appendix B — Corresponding author's complete prepared initial response (verbatim)

```markdown
# Initial Response to Reviewer Caus

We thank the reviewer for recognizing our same-shape control and failure diagnosis, and for asking us to distinguish a methodological contribution from improved COD accuracy. The oracle-shape and generalizability questions identify important boundaries of our evidence.

### CW-01: Contribution beyond a sanity check
**Concern (excerpt):** “From a contribution view point this has limited role in advancing the camouflage object detection methodology.”

**Response:** We agree this is **not a new detector or a positive augmentation algorithm**. The contribution is an experimental control for attributing gains from *where* a fixed synthetic budget is spent. Targeting versus uniform sampling changes both quota concentration and score alignment; CSHUF and CINV preserve the quota shape while shuffling/reversing direction (Table 1; Secs. 3–4). Geometry must not be mistaken for accuracy: the effective-rank ratio averages 0.634, but the targeting-specific probe increment over shuffle is only +0.0073 Cohen's d. Eight-seed direction contrasts remain unresolved on S-measure; exploratory boundary effects depend on architecture. We do **not** claim that every nonuniform allocation necessarily lowers effective rank—our finding is empirical for the studied pools. We will sharpen this distinction and emphasize the separate CHAMELEON contamination contribution.

### CW-02: Bounded generalizability
**Concern (excerpt):** “Findings may not directly transfer to task domains with vastly more expressive generative feedback loops.”

**Response:** Agreed. Our null pertains to the **offline LAKE-RED fixed-foreground pool and two-round S2R-COD-style protocol**, with 1,000 injections, 75 frozen clusters, and SINet/SINet-v2 evaluated on COD10K-test/NC4K. The generator is not updated during training (Methods). We therefore cannot infer a null for online adaptive generation or other task domains. We will narrow the abstract, claims, and conclusion accordingly and assess a modern detector if its training infrastructure is available. This is planned, not completed, validation.

### CW-03: Foreground bottleneck
**Concern (excerpt):** “The generator is constrained to reusing fixed foreground cutouts...”

**Response:** We agree this limitation may constrain steering, without claiming it is the proven cause of the null. Our audit found no regenerated foreground among 8,885 traced objects; the reported synthetic-to-real k-NN recall is 0.13–0.54 under the studied settings (Sec. 4.3; coverage appendix). Reallocation cannot create unseen object content. We will verify provenance and coverage computations and, if suitable generation code and masks are available, compare against genuinely foreground-varying synthesis at a matched budget. Coverage, label validity, and detection performance will be assessed separately; improved coverage alone is not evidence of improved COD.

### QA-01: Different-shape oracle
**Reviewer question:** “CORACLE keeps C10's shape. Did you test an oracle with a different shape (e.g., proportional to true error, or concentrated on the truly worst clusters)?”

**Response:** **No.** CORACLE places C10's existing quotas according to true endpoint-error rank; it tests **direction at fixed shape**, not whether that shape is optimal (Table 1; Appendix “Three Controls”). CORACLE–B is +0.0008 at three seeds on SINet/COD10K, inside its 0.0061 bar (Table 2); this does not exclude other shapes. We will evaluate error-proportional and top-error-cluster allocations at the same 1,000-image budget, with uniform, C10, CORACLE, and shape-matched controls, checking realized quotas and distinctness. Using test labels for an oracle is an **explicitly leaky diagnostic**, never a deployable method; we will prefer disjoint calibration labels where feasible and will not tune checkpoint selection using endpoint labels. We will report uncertainty and infeasibility transparently.

### QA-02: Modern backbone and generator
**Reviewer request:** “Replicate with one modern backbone and one foreground-varying generator, and scope the claim to the LAKE-RED/S2R-COD pipeline.”

**Response:** We agree. We will assess a reproducible modern transformer-based COD model and a generator that demonstrably changes foreground content while providing valid masks. We will preserve comparable budgets, splits, evaluation and checkpoint protocols and compare random, targeted, and shape-preserving shuffled policies. Testing the backbone and generator factors separately before their combination will clarify attribution. These experiments depend on available code, checkpoints, masks, and compute, and **are not yet complete**. Whether successful, inconclusive, or infeasible, they will not be used to generalize the current null beyond LAKE-RED/S2R-COD.

We will disclose negative and inconclusive results and identify any new analyses as post-review validation.
```

**Consistency instruction:** Quote this response accurately in the final updated response workflow. If new evidence contradicts it, correct the interpretation explicitly; the author retains control of what gets submitted.

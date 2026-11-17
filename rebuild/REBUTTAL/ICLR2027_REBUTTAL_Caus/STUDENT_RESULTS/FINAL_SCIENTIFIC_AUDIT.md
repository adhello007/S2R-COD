# Final scientific audit: Reviewer Caus

## Concern-level dispositions

| Concern | Disposition | Basis | What remains |
|---|---|---|---|
| CW-01: contribution beyond a sanity check | **SUBSTANTIALLY ADDRESSED** | Original probe and rank code reproduced. Exact constructions show concentration does not fix the sign of effective rank. The pool geometry shows matching plus concentration drives separation, and that direction adds nothing. The paper's over-attribution to concentration is corrected (C-04/C-23). | The contribution is a control and an audit, not a detector. That is by design, and the rebuttal says so. |
| CW-02: bounded generalisability | **PARTIALLY ADDRESSED** | Scope stated in the title, abstract, discussion and conclusion (patch). Every trained number re-derived. | No modern detector was trained (AN-04/EXP-02 BLOCKED). |
| CW-03: foreground bottleneck | **PARTIALLY ADDRESSED** | Provenance, coverage (every k) and mask QC re-measured; the bottleneck premise is confirmed. | No foreground-varying generator was tested (EXP-03 BLOCKED), so its causal role is untested. |
| QA-01: different-shape oracle | **SUBSTANTIALLY ADDRESSED** | Three different-shape oracles plus a same-shape shuffle were pre-registered and trained (12/12 runs). All four primary contrasts are WITHIN NOISE on both endpoints. The answer to the reviewer is "No" for the submitted paper, then the new result. | SINet only; 3 seeds (bar 0.0057); endpoint-label-leaky (no disjoint calibration set); OR-PROP's direction is untestable; OR-TOP5 has no same-shape control |
| QA-02: modern backbone + new generator; scope the claim | **PARTIALLY ADDRESSED** | The scoping half is done. The replication half is BLOCKED, with concrete reasons (licence, trainability, target-label leakage of released weights, no generator with code, compute). | Both replications |

## Task statuses (13)

| Task | Status |
|---|---|
| TH-01 | VERIFIED |
| TH-02 | VERIFIED |
| AN-01 | VERIFIED |
| AN-02 | VERIFIED |
| AN-03 | PARTIALLY VERIFIED |
| AN-04 | BLOCKED |
| AN-05 | VERIFIED |
| EXP-01 | VERIFIED |
| EXP-02 | BLOCKED |
| EXP-03 | BLOCKED |
| EXP-04 | BLOCKED |
| DOC-01 | VERIFIED |
| DOC-02 | VERIFIED |

## Risks to the original claims (for the corresponding author)

1. **The OR pre-registration timing is misstated.** The paper says it was committed before the first
   oracle run. It was committed 62 minutes after the first run started, before any oracle score existed
   (commit `a79886a`, tag `prereg-or-fx-se-a79886a`). The SE rule is cited at the wrong commit. Both
   are corrected in the patch, and the rebuttal discloses the first.
2. **"No score of any quality helped"** is supported only at C10's fixed allocation shape. EXP-01
   addresses other shapes (above).
3. **"The probe was detecting the concentration the whole time"** is too strong. A flat quota under
   the same matching still separates (d ≈ 0.5).
4. **Unlabelled endpoint overlap:** 15 COD10K-test and 32 NC4K photographs are also in the unlabelled
   target pool, identically for every arm. This affects absolute levels, not contrasts. The paper
   discloses only the 7 exact COD10K pairs.
5. **A provenance commit can be lost.** `c2114af` (the AC and PC rules, committed 5 minutes before
   the first PC run) is on no branch and has no tag (C-32). Tag it, as `a79886a` was tagged.
6. **Not checked locally:** whether the manuscript and `01_INITIAL_REBUTTAL_FOR_SUBMISSION.md` match
   what was uploaded and posted.

## §8 checklist

| Item | Met? |
|---|---|
| All 3 critical weaknesses and 2 questions have a commitment, task mapping and final response | yes (`FINAL_UPDATED_REBUTTAL.md`) |
| Submitted TeX preserved; revision in a copy with an auditable diff | yes (`manuscript_scope_edits.patch`; the submitted file was only read) |
| CORACLE's fixed-shape property verified; new different-shape oracles distinguishable | yes (identical shape hashes for the C-family; new shapes and distinctness in `AN-02_selection_overlap.csv`) |
| At least one genuine new shape plus a same-shape shuffle preflighted and run | yes (OR-TOP10 / OR-TOP10-SHUF, Jaccard 0.216; trained at 3 seeds) |
| Oracle labels documented as calibration or leaky endpoint | yes: all endpoint-label-leaky; no calibration source exists (AN-05) |
| Probe and effective-rank claims never stand in for COD gains | yes |
| Modern backbone choice and trainability verified, not assumed | yes: verified as not trainable and not licensed (BLOCKED) |
| Foreground-diverse generator changes the foreground and supplies valid masks | not met: none available (BLOCKED, recorded) |
| B/C10/CSHUF-type controls and pool sizes and split hashes match within the cell | yes for EXP-01 (5447 pools, identical split hashes, reuse gate R1–R6) |
| At least one independent recomputation of every new key number | yes: stats impl A/B; independent S-measure on 200 images per run and endpoint; independent provenance, coverage and duplicate detectors |
| New inference reports seed variability; no equivalence claimed from non-significance | yes |
| Generator and architecture scope of the null carefully bounded | yes |
| Every missing dependency and blocked task identified | yes (`EXPERIMENTAL_EVIDENCE.md` §6 records) |
| Final rebuttal consistent with the initial commitments, correcting contradicted assertions | yes. The initial response's "we will prefer disjoint calibration labels where feasible" is answered: no disjoint set exists in the workspace, so the oracle is labelled leaky. |
| No generalisation from leaky-oracle performance or CHAMELEON | yes |
| Both final rebuttal versions prepared; OpenReview copy character-counted | yes (count in `EXECUTION_STATUS.md`). OpenReview's current limit should be confirmed before posting. |
| Evidence, logs, hashes, code patch, status and audit exist; every linked path resolves | yes (`rebuild/CAUS/doc02_package.py` link check) |
| No posting, no irreversible action without permission, no suppressed result | yes: nothing posted, nothing deleted, every run reported |

## Compliance with the instruction file

**What was checked.** `Caus_AGENT_EXECUTION_INSTRUCTIONS.md` at the worktree root is byte-identical
to `03_STUDENT_AGENT_EXECUTION_INSTRUCTIONS.md` (sha256 `b6364bc0…`). This check runs through §§3, 5,
6 and 7 of it, task by task.

| Requirement | Delivered | Deviation / note |
|---|---|---|
| §3 run manifest with the listed fields, `oracle_score_source`, `eligible_capacity_policy` | `RESULT_TABLES/run_manifest.csv` (24 rows: 12 new, 12 historical) | Round-1 checkpoints are overwritten by round 2 in this trainer, so `round1_checkpoint_sha` says so instead of giving a hash |
| §3.3 smoke test and one-epoch pilot before any campaign | `EXPERIMENT_LOGS/EXP-01/00_pilot/` | The optional CLS smoke timed out on its own budget; validity was shown otherwise (Addendum A1) |
| TH-01 outputs (3 tables, math log, code SHA, qualification) | all present | — |
| TH-02 outputs (log, contrast definitions, verified inference script, per-contrast table) | all present (`caus_stats.py`, `exp01_stats.py`, `EXP-01_comparisons.csv`) | Interaction contrasts are defined but not estimable (EXP-02/03 BLOCKED) |
| AN-01 outputs (audit, ledger, proposed edits); every cited key validated; anonymous repository inspected | all present; 41/41 keys; repository state recorded | Repository subfolders could not be listed without a browser session |
| AN-02 outputs (overlap, probe/geometry tables, audit) | all present | The optional figure was not drawn. Probe CIs are reported as across-draw sd (as committed), not re-bootstrapped. No normalisation-sensitivity rerun; the alternative rank definition and both representations are reported. |
| AN-03 outputs (provenance, coverage/QC, audit) | all present | No human mask QC on a blinded sample (masks are shared by every arm). Generator licence not re-checked: no new generator was used. |
| AN-04 outputs (integration log, preflight, rationale, source revision) | log and preflight present | No adapter (BLOCKED). Source revision not recorded (pages only). |
| AN-05 outputs (split audit, leakage log) | present (plus cross-split pairs, role ledger, CHAMELEON cross-check) | No data-flow figure; the role ledger carries the flow |
| EXP-01 outputs (quota manifests, metrics by seed, comparisons, logs, patch, 150–250-word finding) | all present (`EXPERIMENT_LOGS/EXP-01/EXP-01_finding.md`, 243 words) | Smaller arm set predeclared with its rationale (TOP5-SHUF and PROP-SHUF not trained) |
| EXP-02 / EXP-03 / EXP-04 | §6 blocker records | No log folders: they were not executed (§7) |
| DOC-01 (summary section, patch, claim-to-sentence table) | all present; patch compiles; main text 9 pages | The CHAMELEON edits were withdrawn (author decision) |
| DOC-02 (both rebuttals, summary, status, evidence, audit, code patch, archive with checksums) | all present; OpenReview copy counted | — |
| §7 tree | as specified | `02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md` was not supplied and was not created (noted). `FIGURES/` holds only a README (no figures). |

**Not done, and not claimed:**
- the clean-calibration oracle comparison;
- the SINet-v2 oracle runs;
- the modern-detector and new-generator experiments.

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
4. **The CHAMELEON floor is ≥ 51/76, not 50.** This strengthens the finding and needs the author's
   adjudication of `animal-54`.
5. **Unlabelled endpoint overlap:** 15 COD10K-test and 32 NC4K photographs are also in the unlabelled
   target pool, identically for every arm. This affects absolute levels, not contrasts. The paper
   discloses only the 7 exact COD10K pairs.
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

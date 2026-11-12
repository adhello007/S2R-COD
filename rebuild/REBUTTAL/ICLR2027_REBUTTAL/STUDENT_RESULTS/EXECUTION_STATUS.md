# Execution status: reviewer dypE follow-up

**Deadline:** 17 Nov 2026 12:00 IST. **Branch:** `rebuttal/dypE-validation` (local commits only; not
pushed). **Base:** `8d1d079`. **Nothing was posted to OpenReview.** The author chooses what to submit.

## What ran, and what kind of evidence it is
- **New experiments (training):** none. EXP-01 training is BLOCKED (failed preflight and no GPU).
  EXP-03 is BLOCKED (gate).
- **New computation on stored artifacts (CPU only):** re-scoring of all 64 eight-seed runs (S-measure
  and eight other metrics, plus two boundary metrics at three thresholds, on both endpoints). Paired
  inference. Overlap and exposure from selection records. Quota invariants. The EXP-01 preflight
  simulation. Coverage and cluster diagnostics. The CHAMELEON detector re-run across all pools. Two
  CPU re-inferences per architecture as a pipeline check.
- **Submitted-paper evidence** is quoted as such and was reproduced before use (see the gates in
  `EXPERIMENTAL_EVIDENCE.md`).

## Task status

| Task | Status | One-line result |
|---|---|---|
| TH-01 | VERIFIED | Primary C10−B +0.0024, paired 95% CI [−0.0023, +0.0070]; excludes +0.0142, not +0.005; not equivalent at ±0.005 (p 0.111) |
| AN-01 | VERIFIED | 1152/1152 committed metric values reproduced at 6 dp; submitted CI/TOST were Welch |
| AN-02 | PARTIALLY VERIFIED | B vs C10 differ on 77% of injections, 14.1% of pool, not 8.8%; exposure theoretical only (no sampler trace) |
| TH-02 | VERIFIED | Same-shape arms share the quota multiset exactly; the CINV fixed point is the median cluster |
| AN-03 | VERIFIED (exploratory findings) | Three-seed boundary effect does not hold for C10−B at eight seeds; interaction not resolved |
| EXP-02 | PARTIALLY VERIFIED | Re-score exact (Gate 3); CPU re-inference 3/4 within pre-specified tolerance, 1 just outside |
| AN-04 | {{AN04_STATUS}} | {{AN04_LINE}} |
| AN-05 | VERIFIED | All counts reproduce; new: 32 COD10K-test and a 4th CAMO-250 duplicate; 74/76 duplicated somewhere |
| EXP-01 | BLOCKED (preflight FAILED) | Larger N raises the B–C10 contrast at most 1.22× (needs 1.5×); no GPU |
| EXP-03 | BLOCKED | No generator of genuinely new foregrounds available |
| DOC-01 | VERIFIED | Edits with label, old/new text, reason, evidence; numbers independently re-checked |
| DOC-02 | VERIFIED | Protocol table and amendments for QA-03 |

## Concern resolutions (justified in `FINAL_SCIENTIFIC_AUDIT.md`)

| Concern | Resolution |
|---|---|
| CW-01 | SUBSTANTIALLY ADDRESSED |
| CW-02 | SUBSTANTIALLY ADDRESSED |
| QA-01 | FULLY ADDRESSED |
| QA-02 | PARTIALLY ADDRESSED |
| QA-03 | FULLY ADDRESSED |

## Blockers (fields per brief §4)

| Task | Missing item | Attempted | Error / outcome | Required resource | Valid alternative | Unresolved conclusion |
|---|---|---|---|---|---|---|
| EXP-01 (training) | A budget with materially larger contrast; GPU time | `scripts/exp01_preflight.py` at N = 1000/2000/3000/4447 | DC 0.141/0.172/0.131/0.000, so it fails the 1.5× rule | Larger foreground pool; about 23 GPU-h (3 seeds) or 61 GPU-h (8 seeds) | Fixed-budget draw from C10's complement (DC 0.184); a different algorithm, not run | Whether a much larger realised contrast reveals an effect |
| EXP-03 | A generator of new foregrounds with masks and a licence | Repository, local model and cache search (`EXP-03_BLOCKER.md`) | Only LAKE-RED (background inpainting around a given mask) | A new-object generator, novelty validation, GPU | AN-04 observational audit only | Whether uncertainty guidance helps with new foreground support |
| AN-02 (actual exposure) | A per-sample sampler trace | Searched 128 logs | No trace logged | A re-run with sampler logging (GPU) | Theoretical exposure, labelled | Realised per-image visit counts |

## Deviations from `ANALYSIS_PRESPEC.md` (committed `55061ba`)
1. **Additions** (descriptive, not pre-specified; nothing was replaced):
   - Holm adjustment over the 20 secondary TH-01 contrasts.
   - `AN-05_pseudolabel_exposure.csv`: how many CHAMELEON partners entered our pseudo-labelled sets.
   - `AN-05_cross_benchmark.csv`: a per-image union over the pools that §9 already listed.
2. **Bug fixes and reruns** (no result changed by a fix, apart from 2b):
   - (a) A numpy-2 `repr` leaked `np.float64(...)` into two CSVs. The writers were fixed, and TH-01,
     AN-03, AN-02, EXP-01 and TH-02 were rerun. EXP-02 (2.6 h) was not rerun: its outputs contained
     no affected values, and the change to its script is formatting-only.
   - (b) The AN-05 pathway column initially used exact or pixel identity only for CAMO-250, which
     undercounted it by one (`animal-28`). It now also uses Tier A, and the tables stage was rerun.
   - (c) AN-04 crashed on its first launch before writing any output (`stems_of` formatted a
     filename with a seed of None). It was fixed and rerun.
3. **Not done although useful:** Tier B was not run on the 10 same-dimension negatives or against the
   source pools. This was not pre-specified, and §9 of the prespec fixes Tier B to the published
   scope.
4. **Pre-specified check that failed:** the EXP-02 CPU re-inference tolerance on one of four images
   (99.84% of pixels within ±1 against the required 99.9%). It is reported, not re-tuned.
5. **Disclosure:** the primary S-measure paired and Welch intervals were computed in memory during
   discovery, before the prespec was committed (prespec §1.1).

## Assumptions and inputs
- `01_INITIAL_REBUTTAL_FOR_SUBMISSION.md` and `02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md` were **not
  supplied**. They were created verbatim from Appendices B and C of
  `03_STUDENT_AGENT_EXECUTION_INSTRUCTIONS.md` by line range (03 lines 308–337 and 346–518), with
  line-for-line equality checked. **We assumed Appendix B is the response the author posted.** If the
  posted text differs, compare it before using `FINAL_UPDATED_REBUTTAL.md`.
- Appendix C describes the boundary result as "8-seed". The manuscript's 1.37×/1.34× is three-seed
  and COD10K-only (`tab:boundary`; manuscript line 830). This post-review work produced the first
  eight-seed and NC4K boundary numbers.
- The manuscript was checked against the last committed source. There is no local copy of the
  uploaded PDF, so whether the uploaded PDF used the em-dash or the colon variant of the AI-use
  statement cannot be determined here. This affects no content.

## Code changes
Only new files under `STUDENT_RESULTS/scripts/` were added; no existing repository file was modified.
`CODE_CHANGES.patch` is `git diff 8d1d079 -- STUDENT_RESULTS/scripts`. Data and checkpoints are not
in the patch.

## Footprint and constraints honoured
- CPU only. `CUDA_VISIBLE_DEVICES=''` was set for every job, and no process ever appeared on a GPU.
- Nothing was written under `S2R-COD/`. No installs. The shared `.venv` was used read-only.
- Kept clean: no other reviewer's folders, branches or files were read.
- Disk: about 75 MB in this folder. The per-image boundary table `RUNS/exp02/exp02_per_image.csv.gz`
  (43 MB, sha256 `4f295440…`) is untracked and regenerable with `scripts/exp02_boundary.py`.
- The machine rebooted on 12 Nov at about 11:47 IST. Every job had finished before the reboot or
  started after it; nothing was lost.

## Commits (local)
`55061ba` brief, verbatim 01/02, manifest, prespec · `686bcc0` AN-01/TH-01/AN-02/TH-02/EXP-01/EXP-02/AN-03 ·
`1a7fcda` AN-05 · {{FINAL_COMMITS}}

## For the author to decide
1. Whether to post the short version (`FINAL_UPDATED_REBUTTAL_OPENREVIEW.md`, 5,000-character limit)
   or the full Part A.
2. Whether to adopt DOC-01 Edit 4. It withdraws a claim that the submitted main text calls "the
   strongest form of the result".
3. Whether to describe the CINV advantage on SINet as an open observation, as drafted, or leave it out
   of the main text. Leaving it out is not recommended, because the brief forbids dropping conflicting
   outcomes.
4. Whether to push this branch.

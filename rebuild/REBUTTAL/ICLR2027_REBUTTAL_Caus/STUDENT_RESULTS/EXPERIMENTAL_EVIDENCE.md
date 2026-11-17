# Experimental evidence ledger: Reviewer Caus

**Conventions**
- Every command was run from the worktree root with the shared uv venv, read-only:
  `PY=S2R-COD/.venv/bin/python`, `PYTHONDONTWRITEBYTECODE=1 nice -n 10–15 $PY -B <script>`.
- Commit SHAs are on branch `rebuttal/Caus-oracle-scope`.
- Split hashes are the content digests in `RESULT_TABLES/AN-05_split_audit.csv`. Every primary input
  also matches E0's committed per-file manifest (`EXP-01_reuse_gate.csv`, R3).
- Labels: **[ORIGINAL VERIFIED]** a historical number re-derived here; **[NEW VERIFIED]** a new
  measurement, independently checked; **[HISTORICAL]** read from a committed artifact, not re-derived.

## TH-01: shape, direction, effective rank (CW-01, QA-01)

| Field | Content |
|---|---|
| Status | VERIFIED |
| Claimed result | C10, CORACLE, CSHUF, CINV and B stems reproduce byte-for-byte [ORIGINAL VERIFIED]. New shapes are feasible with 1000 distinct stems each [NEW VERIFIED]. OR-PROP's direction is untestable (Jaccard 0.813 / 0.730) [NEW VERIFIED]. Effective rank is the participation ratio; concentration does not fix its sign (exact constructions with Monte Carlo; empirical OR-TOP5-SHUF 0.943, FLAT 0.855) [NEW VERIFIED]. |
| Commands + SHA | `exp01_alloc_test.py`, `exp01_tables.py` (`b21b67c`); `th01_rank.py` (`d96ca60`) |
| Data | dinoL518 frozen embeddings (`rebuild/E0/cache`, E0-manifest inputs); B1 cluster table blob `3fb4c466` |
| Seeds | deterministic. Shuffle seeds 930000 (TOP10), 940007 (TOP5), 920004 (PROP, quota-only). Random references `default_rng(10000+i)`, i < 20. |
| Outputs | `TH-01_*.csv`, `AN-02_shape_geometry.csv`, `EXPERIMENT_LOGS/TH-01_math_verification.md` |
| Independent check | plain-Python largest remainder; tracing selector asserted equal to the committed `greedy_select`; Monte Carlo against exact covariance |
| Leakage flag | quota inputs for oracle arms are endpoint-label-leaky (declared) |
| Interpretation | "Every non-uniform allocation lowers effective rank" is false in general and in this pool. The paper's 0.634 is empirical. |
| Limitations | Geometry is not accuracy. 20 C1 cells share one pool and two embedders, so they are not independent replicates. |

## TH-02: identification and statistics (CW-02, QA-01)

| Field | Content |
|---|---|
| Status | VERIFIED |
| Claimed result | Every historical trained number re-derives [ORIGINAL VERIFIED]: SE +0.0024 / bar 0.0069 / 6/8; Welch [−0.0020, +0.0067]; OR +0.0008 / 0.0061; TOST 0.019 / 0.101; 5/16 equivalent. Paired-seed analysis adds no precision (variance ratio 1.03). |
| Commands + SHA | `caus_stats.py` (`213039c`); EXP-01 verdict code `exp01_stats.py` (`d832800`), validated on OR |
| Data | `rebuild/ABC/out/{.,t2,or,fx,se}/abc_metrics.csv` (committed; R5 re-scores 24/24 SINet cells at 6 dp) |
| Outputs | `TH-02_historical_recompute.csv`, `TH-02_contrast_definitions.csv`, `EXPERIMENT_LOGS/TH-02_identification_and_statistics.md` |
| Independent check | implementation A (numpy/scipy) against B (pure Python with its own t distribution): max diff 2.6e-14 |
| Leakage flag | CORACLE rows are endpoint-label-leaky (declared) |
| Interpretation | The null is "no effect above about +0.007 at this sensitivity". The equivalence of C10 and B is not established. |
| Limitations | Interaction contrasts are not estimable (EXP-02/03 BLOCKED) |

## AN-01: claim audit (all concerns)

| Field | Content |
|---|---|
| Status | VERIFIED |
| Claimed result | 33 claims audited. Incorrect statements of fact: the OR pre-registration timing (C-07; committed 62 min after the first run, before any score) and the SE commit reference (C-31). Overstated: "no score of any quality" (C-06), "perfect" oracle (C-05), concentration-only attribution (C-04/C-23), missing scope (C-01/02/24/25). CHAMELEON 50/76 supported as a floor; 41/41 Tier-A recovered independently (C-22). |
| Commands + SHA | compile of the submitted .tex with committed inputs (`latexmk`, 25 pages, 0 undefined); git provenance (`git log`, `git cat-file`, tag `prereg-or-fx-se-a79886a`) |
| Outputs | `AN-01_claim_ledger.csv`, `EXPERIMENT_LOGS/AN-01_claim_audit.md` |
| Independent check | each number traced to a committed artifact and, where cheap, re-derived (TH-02, AN-02, AN-03, AN-05) |
| Limitations | Not checked against the OpenReview-uploaded PDF (not available locally). Boundary metrics (C-15) are [HISTORICAL]. |

## AN-02: geometry, distinctness, probe (CW-01, QA-01)

| Field | Content |
|---|---|
| Status | VERIFIED |
| Claimed result | Original C1 code reproduces `c1_attribution/spread/coverage/occupancy` (≤ 3.1e-13) [ORIGINAL VERIFIED]: +0.0073, −0.0649, 0.634 (20/20). Label shuffle collapses d to about 0. Distinctness: OR-TOP10/-SHUF 645 differing, OR-PROP/-SHUF 103. A flat quota still separates (d 0.52). |
| Commands + SHA | `caus_repro_c1.py`, `th01_rank.py` (`d96ca60`); `exp01_tables.py` (`b21b67c`) |
| Outputs | `AN-02_c1_reproduction.csv`, `AN-02_probe_geometry.csv`, `AN-02_effrank_definitions.csv`, `AN-02_selection_overlap.csv`, `AN-02_shape_geometry.csv`, `EXPERIMENT_LOGS/AN-02_audit.md`, `EXPERIMENT_LOGS/AN-02/c1_reproduction.log` |
| Independent check | committed CSVs, cell by cell; label-permutation control |
| Interpretation | Separation comes from the matched selection plus concentration; the score's direction adds nothing |
| Limitations | Probe d is a geometric statistic, not accuracy |

## AN-03: provenance, coverage, masks, generators (CW-03, QA-02)

| Field | Content |
|---|---|
| Status | VERIFIED (LAKE-RED pool); BLOCKED (new generator) |
| Claimed result | 8,885 objects traced, 0 regenerated [ORIGINAL VERIFIED]. 4,443 distinct foregrounds. k-NN recall 0.13–0.54 at k = 5 reproduced at every k [ORIGINAL VERIFIED], k-dependent (0.07–0.75). Masks: 0 empty, 47% multi-component. Camouflage Anything and RealCamo both preserve the foreground; neither has released code. |
| Commands + SHA | `an03_provenance_coverage.py` (`de07bc5`); public pages read 2026-11-12 (URLs in the report) |
| Outputs | `AN-03_foreground_provenance.csv`, `AN-03_coverage_and_qc.csv`, `EXPERIMENT_LOGS/AN-03_generator_audit.md` |
| Independent check | D1 per-image interior error (median diff 0.000); A3 coverage (to 4 dp) |
| Interpretation | The premise of CW-03 is confirmed: the pool only repaints backgrounds of a fixed foreground set. Its causal role in the null is untested. |

## AN-04: modern detector preflight (CW-02, QA-02)

| Field | Content |
|---|---|
| Status | BLOCKED |
| Claimed result | CamoFormer has no training entrypoint in its repository. CTF-Net has training code but no licence. Both release weights trained on this study's target-pool labels. |
| Outputs | `AN-04_preflight.csv`, `EXPERIMENT_LOGS/AN-04_model_integration.md` |
| Blocker record | see EXP-02 below |

## AN-05: leakage and calibration (QA-01, CW-02/03)

| Field | Content |
|---|---|
| Status | VERIFIED |
| Claimed result | Exact overlaps reproduce D2 (7 target × COD10K-test; 3 CAMO-250 × CHAMELEON) [ORIGINAL VERIFIED]. New near-duplicates: 15 COD10K-test and 32 NC4K photographs in the unlabelled target pool; 7 CAMO-250 × COD10K-test. All are identical across arms. No disjoint calibration source exists, so the oracle arms are endpoint-label-leaky. CHAMELEON: all 41 Tier-A images recovered independently. |
| Commands + SHA | `an05_split_audit.py` (`b130d3f`); CHAMELEON cross-check (`5e7a2f9`) |
| Outputs | `AN-05_split_audit.csv`, `AN-05_cross_split_pairs.csv`, `AN-05_role_ledger.csv`, `AN-05_chameleon_crosscheck.csv`, `EXPERIMENT_LOGS/AN-05_leakage_and_calibration.md` |
| Independent check | 13/13 confirmed pairs inspected by eye; D2 committed counts |
| Limitations | Near-duplicate counts are lower bounds (crops, flips and recolours escape the detector) |

## EXP-01: different-shape oracle (QA-01, CW-01)

| Field | Content |
|---|---|
| Status | VERIFIED: 12/12 runs (2026-11-13 13:06 → 11-14 01:13 IST), one start each, completion assertions passed, 21.7 GPU-h |
| Pre-registration | `rebuild/CAUS/PREREGISTRATION_EXP01.md` (`b21b67c`, before any run script); Addendum A1 (`213039c`, before any run) |
| Seeds / arms | 42, 43, 45 × {OR-TOP10, OR-TOP10-SHUF, OR-PROP, OR-TOP5}; reused B, C10, CORACLE |
| Quotas | `EXP-01_quota_manifests.csv`, `EXP-01_stems/`, `EXP-01_selection_manifest.csv` |
| Reuse gate | R1–R6 pass: `EXP-01_reuse_gate.csv`, `EXP-01_reuse_R5_rescore.csv`, `EXPERIMENT_LOGS/EXP-01/00_pilot/` |
| Leakage flag | endpoint-label-leaky (all oracle arms); NC4K read by no allocation |
| Hardware / software | every run: NVIDIA RTX PRO 6000 Blackwell (95 GB, ≥ 93.7 GB free at launch), GPUs 0 and 1; Python 3.12 shared uv venv; torch 2.11.0+cu128, CUDA 12.8, cuDNN 9.19 (`runs/*/env.json`) |
| Results | All four primary contrasts WITHIN NOISE on COD10K (2σ̂ = 0.0057, df 14): P1 +0.0022, P2 −0.0002, P3 +0.0023, P4 +0.0011 (signs 2/3). NC4K (2σ̂ = 0.0064): +0.0011, −0.0009, +0.0028, +0.0005. All secondary contrasts are within noise. [NEW VERIFIED] |
| Commands + SHA | queue scripts `01..12_EXP01_SINet_*.sh` (pinned hashes) → `rebuild/CAUS/exp01_run.py` at `e21752f`; scoring and verdicts `exp01_stats.py` (log `EXPERIMENT_LOGS/EXP-01/scoring/exp01_stats.log`) |
| Outputs | `EXP-01_metrics_by_seed.csv`, `EXP-01_comparisons.csv`, `EXP-01_runs_of_record.csv`, `EXP-01_independent_sm_check_new.csv`, `run_manifest.csv`, `EXPERIMENT_LOGS/EXP-01/runs/` |
| Independent check | independent S-measure vs committed scorer: max diff 2.2e-16 (200 images × 12 runs × 2 endpoints); stats implementation A vs B: 1.9e-14 |
| Interpretation | No oracle shape tested (flat, top-10, top-5) resolves a gain over the C10-shaped oracle; aim at the top-10 shape does not resolve against its shuffle |
| Limitations | SINet only; 3 seeds; leaky oracle; OR-PROP's direction untestable; OR-TOP5 has no same-shape control |

## EXP-02: modern detector × LAKE-RED (CW-02, QA-02), §6 blocker record

| Field | Content |
|---|---|
| Status | BLOCKED |
| Missing item | A trainable, licensed modern COD detector integrated into the two-round student/EMA-teacher loop, and ≥ 9 GPU runs (B/C10/CSHUF × 3 seeds) plus an adapter pilot |
| Discovery tried | CamoFormer and CTF-Net repository pages and listings (2026-11-12); a search for CamoFormer training code |
| Exact errors | CamoFormer: no training script (README covers test and eval only). CTF-Net: no licence file or statement. Both: released checkpoints trained on COD10K-train/CAMO-train masks, i.e. this study's unlabelled target pool. |
| Resources / permission needed | A GPU allocation beyond the 12-run budget; an author decision on CTF-Net's licence status or an alternative detector |
| Alternative attempted | The guide's declared fallback (CTF-Net), evaluated and blocked |
| Claim that cannot be made | That the absence of a direction effect holds for a modern transformer-based detector |

## EXP-03: SINet × foreground-varying generator (CW-03, QA-02), §6 blocker record

| Field | Content |
|---|---|
| Status | BLOCKED |
| Missing item | A generator that produces new foreground content with valid masks (or a vetted pool of new labelled cutouts rendered by LAKE-RED), with ≥ 1000 valid unique samples per arm, plus 9 GPU runs |
| Discovery tried | Camouflage Anything (CVPR 2025) and RealCamo (arXiv 2512.22974) checked from public pages; LAKE-RED's local code considered |
| Exact errors | Both candidates out-paint around a preserved foreground (fail the foreground-variation criterion by design), and neither has released code. LAKE-RED with new cutouts would vary identity only and needs GPU rendering. |
| Resources / permission needed | GPU for rendering and training; a licensed, endpoint-disjoint labelled cutout source with its own contamination audit |
| Alternative attempted | Characterised the existing pool instead (AN-03): provenance, coverage at every k, mask QC |
| Claim that cannot be made | That the null holds, or fails, when the generator can supply new foreground content |

## EXP-04: factorial (QA-02), §6 blocker record

| Field | Content |
|---|---|
| Status | BLOCKED |
| Missing item | The entry gates: EXP-02 and EXP-03 both passed |
| Claim that cannot be made | Any architecture × generator interaction on the direction effect |

## DOC-01 / DOC-02

| Field | Content |
|---|---|
| DOC-01 | VERIFIED (draft). `manuscript_scope_edits.patch` (`490ccec`) compiles; the main text ends on page 9 (limit 10). |
| DOC-02 | in progress |

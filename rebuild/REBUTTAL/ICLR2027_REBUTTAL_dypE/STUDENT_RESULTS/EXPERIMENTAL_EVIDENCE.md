# Experimental evidence ledger (authoritative provenance)

**Scope:** every post-review number used in `FINAL_UPDATED_REBUTTAL.md`, `RESULTS_SUMMARY.md`, `DOC-01_*`
and `DOC-02_*`. **No new training was run. No GPU process was started.** Every analysis is post-review
and exploratory, and none re-decides a pre-registered verdict.

## Shared provenance

| Item | Value |
|---|---|
| Code base | branch `rebuttal/dypE-validation`, base commit `8d1d0795fc4e19474d51f89adf0c2d8fb977f313` (= `experiments/lakered/finalized/12sept`) |
| Analysis code | `scripts/` (new files only; no existing repository file modified; see `CODE_CHANGES.patch`). Analysis plan committed first at `55061ba` (`ANALYSIS_PRESPEC.md`) |
| Committed results | `686bcc0` (AN-01, TH-01, AN-02, TH-02, EXP-01 preflight, EXP-02, AN-03), `1a7fcda` (AN-05), then the packaging commit (see `EXECUTION_STATUS.md`) |
| Data (read-only) | `S2R-COD/` working copy: gitignored `Dataset/`, `Result/ABC/<64 runs>`, `Snapshot/ABC/<64 runs>`, `rebuild/E0/cache`, `rebuild/D2_reaudit/preds`, round-1/round-2 pools under `Dataset/Source/ABC/`. Nothing written there |
| Run list | the 64 runs of the committed `rebuild/ABC/out/se/abc_runs.csv` (4 arms × 8 seeds {42,43,45–50} × 2 architectures). All prediction files are dated ≤ 2026-09-22 (pre-rebuttal). `RESULT_TABLES/run_manifest.csv` follows the brief's §3 schema |
| Integrity | Per-file SHA256 of all 393,408 prediction PNGs (`EXPERIMENT_LOGS/checksums/prediction_files.sha256.gz`), the GT (`gt_files.sha256.gz`), and the 64 `Tea_epoch_best.pth` (`checkpoints.sha256`). GT digests: COD10K `6079a373…`, NC4K `893bb28d…`. Metric code: `Eval/metrics.py` `10c90659…`, `abc_evaluate.py` `c00e9ec9…` |
| Hardware / software | AMD Threadripper PRO 7965WX (48 threads), 251 GB RAM, CPU only (`CUDA_VISIBLE_DEVICES=''`), jobs under `nice -n 19`. Python 3.12.3, numpy 2.5.1, scipy 1.18.0, scikit-learn 1.9.0, OpenCV 5.0.0, torch 2.11.0+cu128 used on CPU (`EXPERIMENT_LOGS/00_environment.md`) |
| Manuscript | `AD-PCHGS-250926.tex` (sha256 `84d3bf97…`). Identical to the committed `AD-PCHG-250926_Final.tex` (09add3d) except two punctuation hunks in the AI-use statement (`00_manuscript_check/`). Bib identical to the committed `reference.bib`. 39 cite keys in the main file, 41 with `\input`s, all among 43 entries; no undefined `\ref` |
| Random seeds | `numpy.random.default_rng(20261111)` for every bootstrap and random sample |

## Audit table

| Task | Reviewer IDs | Status | Key output | Gate / check |
|---|---|---|---|---|
| AN-01 | CW-01, QA-01 | **VERIFIED** | `AN-01_original_vs_recomputed.csv` | Scorer check passed (ΔS_α 3.8e-7); **1152/1152** committed values equal at 6 dp |
| TH-01 | CW-01, QA-01 | **VERIFIED** | `TH-01_paired_inference.csv`, `TH-01_seed_differences.csv` | NumPy vs scipy agree; known-answer test passes; σ̂ reproduced to 1e-9; 16/16 `tab:tost` rows reproduced at 4 dp |
| AN-02 | CW-01, QA-02 | **PARTIALLY VERIFIED** | `AN-02_overlap_by_seed.csv`, `AN-02_exposure_by_run.csv` | Overlap and pools verified (64/64 digests match). Exposure is **theoretical**; actual visits are unverified (no sampler trace in 128 logs) |
| TH-02 | CW-02 | **VERIFIED** | `TH-02_quota_invariants.csv` | All invariants hold; selections byte-equal to committed stems |
| AN-03 | CW-02 | **VERIFIED** (findings exploratory) | `AN-03_arch_boundary_grid.csv`, `AN-03_interaction.csv` | Inputs passed Gate 3; scipy cross-check passes |
| EXP-02 | CW-02 | **PARTIALLY VERIFIED** | `EXP-02_rescored_predictions.csv`, `EXP-02_gate3_reproduction.csv` | Gate 3: 300/300 committed values (max Δ 1.1e-16). CPU re-inference: 3 of 4 images within tolerance, 1 outside (see below) |
| AN-04 | CW-02, QA-02 | **PARTIALLY VERIFIED** | `AN-04_foreground_coverage.csv`, `AN-04_cluster_domain_mix.csv`, `AN-04_cluster_structure.csv`, `AN-04_signal_correlations.csv` | Gate 4: 12/12 committed coverage values at 4 dp; correlation gate exact; bootstrap invalid for k-NN recall |
| AN-05 | QA-03 | **VERIFIED** | `AN-05_chameleon_pairs.csv`, `AN-05_protocol_paths.csv`, `AN-05_mask_release.csv`, `AN-05_cross_benchmark.csv` | Every submitted count reproduced; detector self-test passes; agrees with committed verdicts 76/76 |
| EXP-01 | CW-01, QA-02 | **BLOCKED** (preflight run: FAILED its rule) | `EXP-01_preflight.csv`, `EXPERIMENT_LOGS/EXP-01_BLOCKER.md` | N = 1000 reproduces 9/9 committed stem files byte for byte |
| EXP-03 | CW-02, QA-02 | **BLOCKED** (gate) | `EXPERIMENT_LOGS/EXP-03_BLOCKER.md` | No generator of new foregrounds available |
| DOC-01 | CW-01, CW-02, QA-01, QA-02 | **VERIFIED** | `DOC-01_MANUSCRIPT_PROPOSED_EDITS.md`, `RESULT_TABLES/DOC-01_claim_evidence_map.csv` | Numbers re-checked by `scripts/audit_independent.py` |
| DOC-02 | QA-03 | **VERIFIED** | `DOC-02_CHAMELEON_PROTOCOL_CLARIFICATION.md` | Same audit |

---

## AN-01: independent eight-seed re-score
- **Command:** `scripts/an01_rescore.py --workers 16` (`EXPERIMENT_LOGS/run_logs/an01_rescore.log`). It imports
  `score()` unchanged from `rebuild/ABC/abc_evaluate.py`.
- **Inputs:** 64 runs × {COD10K-test (2026 images), NC4K (4121)}, `Tea_epoch_best.pth` predictions,
  final round. CAMO-250 is never used as an endpoint.
- **Result:** the scorer check against the B1 reference values passed (S_α 0.7172156, MAE 0.0744632).
  All 9 metrics × 128 run-endpoints equal the committed `out/se/abc_metrics.csv` and the
  trained-campaign CSVs at 6 dp, 1152/1152. The per-image mean equals the aggregate to 2e-16.
- **Interpretation:** the per-seed table used by TH-01 is exactly the submitted one; nothing was
  reconstructed from aggregates. The submitted CI and TOST were **Welch (unpaired)**, as the `tab:tost`
  caption states. The paired analysis is new.

## TH-01: paired inference, equivalence, scales
- **Command:** `scripts/th01_paired.py` (`run_logs/th01.log`). Method: `ANALYSIS_PRESPEC.md` §4.
- **Estimand:** D_i = S_α(C10, seed i) − S_α(B, seed i), with n = 8 pairs, df 7. Pairing is by training
  seed. Arm B redraws its 1,000 stems per seed (`default_rng(700000+seed)`), so a pair does not share
  data.
- **Primary (SINet, COD10K):** D̄ = +0.00235. SD(D) 0.0056; paired 95% CI [−0.0023, +0.0070];
  two-sided p 0.273; 6/8 positive; one-sided 95% upper bound +0.0061; paired TOST(±0.005) p = 0.111,
  not equivalent; smallest equivalence margin 0.0061. Exact sign-flip p 0.289 (256 vectors).
  BCa 95% [−0.0018, +0.0055] (unreliable at n = 8, sensitivity only). Leave-one-out means
  +0.0013…+0.0037, every CI contains 0. Welch: [−0.0020, +0.0067], TOST p 0.101, smallest margin
  0.0059, reproducing the submitted numbers. r(B, C10) = −0.04; SE_paired/SE_Welch = 1.02. The frozen
  2σ̂ bar of 0.00686 gives 0.34×, WITHIN NOISE, as submitted.
- **All four cells, C10−B:**

| Cell | D̄ | Paired 95% CI | Paired TOST p | Welch 95% CI | Welch TOST p |
|---|---|---|---|---|---|
| SINet COD10K | +0.0024 | [−0.0023, +0.0070] | 0.111 | [−0.0020, +0.0067] | 0.101 |
| SINet NC4K | +0.0003 | [−0.0038, +0.0045] | 0.016 | [−0.0033, +0.0040] | 0.008 |
| SINet-v2 COD10K | −0.0011 | [−0.0081, +0.0059] | 0.114 | [−0.0067, +0.0045] | 0.076 |
| SINet-v2 NC4K | −0.0009 | [−0.0077, +0.0058] | 0.100 | [−0.0068, +0.0049] | 0.079 |

  Holm over the 4 primary-family cells: all adjusted p = 1.0.
- **Secondary contrasts** (20 tests): three have raw p < 0.05. These are CINV−B SINet/COD10K
  +0.0045 [+0.0015, +0.0074] (p 0.009); CSHUF−CINV SINet/COD10K −0.0024 [−0.0044, −0.0004]; and
  CSHUF−CINV SINet/NC4K −0.0037 [−0.0059, −0.0016]. None survives Holm over the 20 (smallest 0.091).
  Paired equivalence at ±0.005 holds for 6 of the 16 SE gaps, against 5 for Welch.
- **Interpretation:** the reference +0.0142 is excluded in every cell. +0.005 is not excluded on the
  primary cell. Equivalence is not established on the primary cell. The paired analysis neither
  strengthens nor weakens the submitted Welch statement.

## AN-02: realised overlap and exposure
- **Command:** `scripts/an02_overlap_exposure.py` (`run_logs/an02.log`).
- **Verification:** all 64 materialised round-1 pools reproduce their committed image and GT digests.
  The injected stems in each pool equal the committed stem file, and all 4447 base stems are present.
  The round-2 appended counts equal the committed `n_appended`.
- **Overlap (per seed; stems are identical across architectures):** B∩C10 = 209–246 (mean 233.4;
  chance 224.9). That is 754–791 differing, 76.7% of injections, 14.07% of the 5,447 pool (one-sided).
  B∩CSHUF 214–243; B∩CINV 204–250. C-family pairs (deterministic): C10∩CSHUF 548, C10∩CINV 489,
  CSHUF∩CINV 546, so 45.2–51.1% of injections differ (8.30–9.38% of the pool). **Reconciliation:** the
  manuscript's "about 48%" and "8.8%" match the C-family pairs under the one-sided definition, not
  B-vs-C10. Both one-sided and symmetric definitions are tabulated.
- **Foreground identity:** 4106 distinct stems are injected across arms and seeds, and **0 are new**
  relative to the base pool. 2 render images and 4 render masks are byte-duplicates of another
  stem's. In 12 hand-inspected stems the render mask is binary and has the same size as the base GT,
  with IoU 0.92–0.98, not identical.
- **Exposure (theoretical):** an epoch draws steps × batch = 4048 (SINet) or 4064 (SINet-v2) source
  images. Round-1 pool 5447 gives 0.743 visits per image per epoch, about 29 per round (SINet,
  39 epochs) or 74 (SINet-v2, 99 epochs). Round-2 pool 7229–7725 gives 0.53–0.56 per epoch. C10-only
  images (vs B) are 13.8–14.5% of draws in round 1 and 9.9–10.9% in round 2. The search for a sampler
  trace (128 logs; pattern `sampler|indices|index|visit|batch_ids|perm`) found 0 hits, so actual
  visits are **UNVERIFIED**.
- **Pseudo-labels:** per-arm means over all 64 runs are B 1991.0, C10 2006.8, CSHUF 2019.9,
  CINV 2015.1, range 1782–2278. Over SE's 40 trained runs they are 1977.2, 2024.8, 1989.9, 1978.9,
  range 1817–2259, which is what the manuscript reports. B vs C10 round-2 appended sets at equal seed
  and architecture: Jaccard 0.580–0.678.
- **Caveat:** the exposure figures assume a fresh uniform shuffle per epoch truncated at `total_step`.
  This was confirmed from `MyTrain.py` (`zip(source_loader, target_loader)`, `shuffle=True`) but not
  logged.

## TH-02: quota invariants
- **Command:** `scripts/th02_quota_invariants.py` (base C1 functions, unchanged).
- **Result:** s_e = 0.010122, which rounds to the manuscript's 0.0101. All four concentrated quota vectors
  (C10, CSHUF, CINV, CORACLE) sum to 1000 and share the identical sorted multiset (75 clusters funded,
  max share 0.194, entropy 0.787 on integer quotas, HHI 0.0739, Gini 0.627). C10 vs CSHUF differ in 73
  of 75 cluster quotas, and C10 vs CINV in 72. CINV has exactly one fixed point, the median-ES cluster
  (rank 38 of 75). CSHUF has none, ρ = −0.03351. The realised per-cluster counts equal the nominal
  quotas, with n_displaced 370/404/367/509. There are no ties in target_es. Remainder units: 37.
- **Limits (analytic):** the arms share the quota *multiset*, not cluster identity. Same-shape arms
  isolate direction *given* this selection mechanism. No arm pair varies concentration alone while
  holding selected content fixed, so a downstream "concentration effect" is not identified by any
  pair. Round-2 pseudo-labels are a post-treatment mediator. CORACLE uses endpoint labels and is a
  diagnostic only.

## EXP-02 and AN-03: boundary re-score and architecture interaction
- **Commands:** `scripts/exp02_boundary.py --workers 8` (2.6 h CPU; `run_logs/exp02_boundary.log`) and
  `scripts/an03_interaction.py`. `diag_boundary._job` is called unchanged (Boundary-IoU at
  d = 0.02·diag, Boundary-F at θ = 0.0075·diag, nanmean per run).
- **Gate 3:** for the 36 committed 3-seed runs (all six arms) at t = 0.4/0.5/0.6, 300 values reproduce
  with max |Δ| 1.1e-16. The 3-seed subset with a pooled 4-arm bar gives C10−B 1.39/1.37/1.23× and
  CINV−B 1.25/1.34/1.26×, exactly the manuscript's figures.
- **Eight-seed headline (BIoU, t = 0.5, COD10K):** SINet C10−B +0.0046 [−0.0066, +0.0158], 5/8,
  0.30× bar. SINet CINV−B +0.0098 [+0.0039, +0.0157], 7/8, 0.64×. SINet-v2 C10−B +0.0002
  [−0.0061, +0.0064]. SINet-v2 CINV−B +0.0033 [−0.0009, +0.0074]. NC4K and all thresholds show the
  same pattern. Holm across 140 eight-seed contrasts gives smallest adjusted p 0.50.
- **Interaction (Welch on per-seed differences; exact permutation over C(16,8) = 12,870 splits):**
  C10−B +0.0044 [−0.0075, +0.0163], p 0.43 (perm 0.43). CINV−B +0.0065 [−0.0001, +0.0131], p 0.053
  (perm 0.052). Across all 70 interaction cells the smallest Holm-adjusted p is 1.0.
- **CPU re-inference check** (`scripts/exp02_reinfer.py`; `EXPERIMENT_LOGS/EXP-02_reinference.json`;
  pre-specified tolerance ≤ 2 grey levels and ≥ 99.9% within ±1):
  - SINet_C10_s46: two images, max |Δ| 1 and 2, 100% and 99.9994% within ±1. **Pass.**
  - SINetv2_C10_s46 on `…5063`: max 2, 99.995%. **Pass.**
  - SINetv2_C10_s46 on `…BatFish-2`: max 2, **99.84%** within ±1. **Fails** the share criterion.
  - Per-image S_α shifts are ≤ 1.9e-4. This is consistent with CPU-vs-GPU floating point. It does not
    affect any EXP-02 score, which uses the stored predictions.
- **Caveat:** boundary metrics are post-hoc. The bar ratios are a descriptive scale, not an absolute
  effect size.

## AN-05: CHAMELEON
- **Commands:** `scripts/an05_chameleon.py` (stages tierA, tierB, adjudicate, tables;
  `run_logs/an05_*`), `scripts/an05_cross_benchmark.py`, `scripts/an05_pseudolabel_exposure.py`.
  The detectors used are the released `detect_contamination.py` (CLI), `diag_chameleon_ext.main`,
  and `adjudicate.main`, all unchanged at the published thresholds.
- **Reproduced:** Tier A 41 (sweep 11/26/37/40/41; gap 5.51 → 40.58; 42 pairs, one image has two
  partners). Tier B 10 of 25 at the operating point (41/41 recall; NC4K 0/120); after adjudication 9,
  with `animal-7` failing the full-resolution homography. Totals: 50 confirmed (44 COD10K-train,
  6 CAMO-train), 16 unchecked, 10 same-dimension negatives, agreeing with the committed final verdicts
  for 76/76. Exact SHA256 against the target pool, HKU-IS (authors' and raw) and the renders: 0.
  Against CAMO-250: 3 (`animal-17/25/60`). The detector self-test passes.
- **New (pools listed in the pre-specification):** against COD10K-test, 32 matches (gap
  4.49 → 30.91, 6.9×), which include all 16 unchecked and 8 of the 10 negatives. Against CAMO-250, 4
  (adds `animal-28`, mean abs diff 0.607; gap 79×). Against NC4K, 0. In total 74/76 are duplicated in
  some checked split; `animal-38` and `animal-54` are not.
- **Transductive use in our runs:** 14–32 (mean 24.7) of the 50 photos per run entered round 2 as
  pseudo-labelled targets; 46/50 did so in at least one run.
- **Masks:** author release object-black (white 0.719), repackaged object-white (0.140). IoU 0.0 as
  stored, 0.6932 aligned; 27/76 identical; 40/76 at IoU ≥ 0.9. MAE of the committed predictions
  `rebuild/D2_reaudit/preds` is 0.21965 vs 0.08163.
- **Caveats:** Tier B was not run on the 10 same-dimension negatives, nor against the source pools.
  No score-inflation estimate exists.

## EXP-01: larger-budget preflight
- **Command:** `scripts/exp01_preflight.py` (base `abc_common`/C1 selection with `BUDGET` rebound).
  N = 1000 reproduces all 9 committed stem files byte for byte.
- **Result:** DC = 0.1407 / 0.1719 / 0.1307 / 0.0000 at N = 1000 / 2000 / 3000 / 4447. The ratio is
  1.22× at 2000, below the pre-specified 1.5×, so the **preflight fails**. Jaccard rises
  0.13 → 0.29 → 0.51 → 1.00. Training is BLOCKED (`EXP-01_BLOCKER.md`).

## EXP-03
**BLOCKED** at its own gate (`EXPERIMENT_LOGS/EXP-03_BLOCKER.md`). No conclusion is drawn about
adaptive or novel-foreground generation.

## AN-04: foreground diversity, clusters and coverage
- **Commands:** `scripts/an04_coverage.py --n-boot 2000` (44.9 min CPU; `run_logs/an04.log`; the first launch
  crashed before writing anything, see `EXECUTION_STATUS.md` §Deviations) and
  `scripts/an04b_signal_correlations.py` (`run_logs/an04b.log`). The coverage estimator is
  `rebuild/A3/a3_appearance_signature.precision_recall` (Kynkäänniemi et al. 2019), unchanged, run on
  CPU. Inputs: the committed E0 embedding cache (dinoL518, dinoL224, clipL224), the committed k = 75
  dinoL518 partition (`b1_cluster_assignment_dinoL518.json`, 4033 labelled target images), and the
  committed B1 per-image score files.
- **Gate 4 (coverage reproduction): PASSED.** All 12 committed values (3 embedders × authors' pool, local
  renders, raw HKU-IS, and COD10K-vs-CAMO) reproduce at 4 dp. Synthetic recall is 0.1277–0.5421 and
  raw source 0.7097–0.7473, i.e. the published 0.13–0.54 and 0.71–0.75.
- **Gate (signal correlations): PASSED.** For SINet/S2C at k = 75, the per-cluster ρ is +0.8553181524182
  against MAE and +0.4275556500297265 against 1 − S_α, both equal to the committed values to 1e-9.
  Architecture breakdown (per-cluster ρ, MAE vs 1 − S_α; ratio): SINet-v2 0.887 / 0.565 (0.64);
  SegMaR 0.828 / 0.540 (0.65); SINet-MT 0.869 / 0.452 (0.52); **SINet source-only 0.355 / 0.458
  (1.29, ordering reversed)**. Per-image ρ by COD10K super-class is in `AN-04_signal_correlations.csv`.
- **Foreground identity:** every render maps to its own base foreground (stem bijection). The render
  mask vs the base GT has median IoU 0.968, 5th percentile 0.914, minimum 0.670, with 0 of 4447
  identical. The median cosine of a render to its own raw source image is 0.61 / 0.70 / 0.66
  (dinoL224 / dinoL518 / clipL224), and the render's nearest raw image is its own source in
  67% / 73% / 43% of cases.
- **Coverage of the real target by each injected 1000-image set** (k-NN recall at k = 5; dinoL518):
  - B: 0.349–0.428 over 8 seeds.
  - C10 0.620, CSHUF 0.644, CINV 0.631.
  - Base pool (4447) 0.483; all renders (4447) 0.542; raw HKU-IS 0.710.
  - The same ordering holds in dinoL224 (B 0.27–0.45; C-family 0.50–0.53) and clipL224
    (B 0.05–0.23; C-family 0.20–0.25).
  - By target domain (dinoL518), C10 covers 0.610 of COD10K and 0.651 of CAMO; B averages
    0.352 / 0.465.
- **The bootstrap is not valid for this estimator (finding, not a deviation):** the pre-specified group
  bootstrap resamples foregrounds with replacement. Duplicated points shrink the k-NN radii, which
  biases recall downward: C10's 0.620 lies above its own bootstrap interval [0.391, 0.556]. The
  intervals are left in the CSV for transparency but **must not be cited**. The variation across the
  8 independent B draws (0.349–0.428) is the usable indication of draw-to-draw spread.
- **Cluster structure:**
  - Silhouette of the committed partition on all 4033 labelled target images: **0.156**
    (Euclidean on L2-normalised features, the committed convention; the committed mean over 10 seeds
    on a 2000-image subsample is 0.1600), and **0.253** with cosine distance. The latter sits at the
    lower edge of the conventional "weak structure" band; both are well below "reasonable structure".
  - Committed-label vs nearest-centroid agreement on the target: 0.945.
- **Between-cluster share of structural error (η², COD10K-test, descriptive only):** 0.2046 with the
  committed SINet/S2C predictions, reproducing "about a fifth" (committed 0.205). With each arm's own
  8-seed mean errors it is 0.189–0.209. Endpoint labels are used here and nowhere else.
- **CAMO share of the budget** (budget-weighted CAMO fraction of funded clusters; committed labels):
  C10 0.530 (2.14× the pool's 0.248; the manuscript's 0.515 uses nearest-centroid assignment, also in
  the committed `diag_clusters.json`), CSHUF 0.285, CINV 0.199, B expected 0.356. The three
  concentrated arms share one quota multiset but **differ strongly in domain mix**.
- **Interpretation:** the coverage and signal-correlation claims reproduce. Two qualifications follow:
  1. The main text's "covers no more of the target manifold" rests on C1's target recall, which is
     saturated near 1.0 for both arms. Under the appendix's k-NN recall on the injected renders,
     concentrated selections cover more than equal-size random draws. The claim is
     estimator-dependent (DOC-01 Edit 10).
  2. The structural-vs-pixel ordering does not hold for the source-only SINet baseline.
  - The differing CAMO share across same-shape arms is a **hypothesis-level** candidate explanation
    for the CINV signal on SINet (it steers the budget away from CAMO-heavy clusters, while the
    endpoints are COD10K-test and NC4K). It is not tested here.
- **Status: PARTIALLY VERIFIED.** Every estimator reproduces, but valid uncertainty statements for
  coverage that account for dependent foregrounds were not obtained.

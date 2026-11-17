# EXPERIMENTAL_EVIDENCE: RL5B rebuttal (Phase 4)

One entry per task, in the §7 template. Paths are relative to `STUDENT_RESULTS/` unless they start with
`rebuild/`, `Snapshot/`, `Result/` or `Dataset/`, which are relative to the repository root.

**Common to every entry.**
- **Hardware and software:** `EXPERIMENT_LOGS/environment.txt` (2× RTX PRO 6000 Blackwell, driver 595.99.02,
  one training job per GPU; training environment `.venv`; analysis environment `.venv-analysis`).
- **Kernel change.** The kernel changed from 7.0.0-42 to 7.0.0-43 at the reboot of 2026-11-13 10:31. This was a
  system update on the shared machine, not ours; the driver and CUDA stack are unchanged. Affected: CDR runs
  started after that time, and all EQ runs.
- **Scorer:** `Eval/metrics.py` through `rebuild/ABC/abc_evaluate.py` (self-check 0.717216 / 0.074463,
  `EXPERIMENT_LOGS/stage0_repro_gate.log`); boundary metrics through `rebuild/DIAG/diag_boundary.py`.
- **Test splits:** COD10K-test (2,026 images) and NC4K (4,121 images), as in the submission.
- **Training pipeline:** the base commit `8d1d079`, plus additive flags (`CODE_CHANGES.patch`). The flags are
  `--save_ckpts minimal`, `--link_pool` and `--val_net`, each numerically neutral (bridge check below).
- **Verification checks 1–8** are those of §7 of the instructions.

---

## TH-01 — Statistical re-derivation, sensitivity and power
Reviewer issues: CW-01, QA-01
Status: VERIFIED
Pre-registration: n/a (re-analysis of the committed SE campaign; the ±0.005 margin is post hoc, as the submission says)
Code revision: `138ad30` (script); inputs unchanged since `8d1d079`
Commands: `.venv/bin/python analysis/th01_stats.py` (RNG seed 20261109; 100,000 simulations per cell)
Datasets: `rebuild/ABC/out/se/abc_metrics.csv` (128 rows = 64 runs × 2 endpoints; sha256 prefix 489053fdebc8db0d, logged)
Configuration: Welch t (primary), seed-paired t (sensitivity), TOST at ±0.005, Holm over the 16 TOSTs; the 2σ̂ rule with σ̂ pooled over B, C10, CSHUF, CINV (df 28) and the ≥ 7/8 sign rule the SE campaign ran
Seeds: SE seeds 42, 43, 45, 46, 47, 48, 49, 50
Artifacts: `RESULT_TABLES/TH01_contrasts.csv`, `RESULT_TABLES/TH01_contrasts.md`, `RESULT_TABLES/TH01_rule_sensitivity.csv`, `RESULT_TABLES/TH01_power.csv`, `RESULT_TABLES/TH01_main_table.tex`, `RESULT_TABLES/TH01_explainer.md`, `RESULT_TABLES/TH01_summary.json`, `EXPERIMENT_LOGS/TH01_stats.log`
Results:

| Quantity | Submitted / posted | Re-derived |
|---|---|---|
| Δ(C10 − B), SINet·COD10K | +0.0024 | +0.002352 |
| Welch 95% CI | [−0.0020, +0.0067] | [−0.00195, +0.00666], df 10.44 |
| TOST p, C10 − B / C10 − CSHUF | 0.101 / 0.019 | 0.1009 / 0.0189 |
| σ̂ (pooled, df 28) | ≈ 0.00345 (posted) | 0.003431 |
| Equivalent at ±0.005, before / after Holm | 5 of 16 | 5 of 16 / 0 of 16 |
| P(rule fires \| Δ = 0.005) | ≈ 0.14 (normal approx.) | 0.139 (same approx.); **0.205** (simulated full rule, ≥ 7/8); 0.128 (8/8) |
| P(rule fires \| Δ = 0.0142) | "almost surely" | 0.999 |
| 80% detectable effect | ≈ 0.008 | 0.0083 (approx.); **0.0087** (full rule, 7/8); 0.0106 (8/8) |
| EQ n per arm for TOST power 0.8 at Δ = +0.0024 | — | 29 (Welch-simulated; capped at 27, see EXP-01) |

Interpretation: The submitted numbers reproduce exactly. The rule detects reference-size effects and cannot rule out effects at the ±0.005 margin. The posted sensitivity figure understated the full rule's probability: it is about one time in five, not one in seven, because σ̂ is re-estimated in every replicate and the arm SDs differ (C10 0.00489, B 0.00251).
Limitations: The margin is post hoc. Holm over 16 TOSTs removes every equivalence. The seed-paired analysis cannot remove the variance asymmetry between B (a new set at every seed) and the fixed C-family sets.
Verification notes: (1) the log exists, with input hashes. (2) The tables are regenerated from the CSV, and the primary cell matches the submission at 6 dp (reproduction PASS). (3) Same scorer outputs as the submission. (5) Analytic and simulated values agree where both exist. (6) Post hoc, labelled; multiplicity reported. (8) Non-equivalences reported.

---

## TH-02 — What the same-shape contrasts identify
Reviewer issues: CW-02, QA-02
Status: VERIFIED
Pre-registration: n/a (theory and design; τ_H fixed here before the CDR draw)
Code revision: `138ad30`
Commands: `.venv/bin/python analysis/th02_sim.py`
Datasets: committed quotas, centroids `rebuild/B1/out/b1_centroids_dinoL518_k75_seed0.npy`, cluster scores `rebuild/B1/out/b1_cluster_es_dinoL518.csv`
Configuration: concentration indices (N_eff, max share, Gini, TV); τ grid 0.100–0.999; toy simulation with known α, β
Seeds: toy RNG fixed in the script
Artifacts: `RESULT_TABLES/TH02_identification.md`, `RESULT_TABLES/TH02_concentration_indices.csv`, `RESULT_TABLES/TH02_tau_grid.csv`, `RESULT_TABLES/TH02_overlap_covariance.csv`, `RESULT_TABLES/TH02_toy_sim.csv`, `RESULT_TABLES/TH02_summary.json`
Results:
- τ_H = 0.758 (N_eff 14.9 = 0.499 × N_eff(τ = 1) of 29.9).
- Nominal N_eff: cluster-uniform 75.0, committed shape 29.9, τ_H 14.9.
- Induced N_eff (each selected render assigned to its nearest target centroid): C10 37.5, CSHUF 40.5, CINV 47.1, B 42.5 (mean of 8 seeds), LU 50.3.
- The toy recovers α without bias, and its spread falls as 1/√K over K permutations.
Interpretation: Same-shape contrasts identify direction only. One permutation cannot separate shape from its own direction. A null on direction is compatible with any shape effect. Identification therefore needs several permutations at more than one concentration level, which is the CDR design.
Limitations: Concentration is confounded with fill quality (mean fill distance 0.8005 / 0.8327 / 0.8547 for uniform / τ = 1 / τ_H), recorded as a covariate. Delivered concentration is weaker than nominal (see EXP-02).
Verification notes: (1) outputs regenerated. (5) The derivations are checked numerically by the toy. (7) The reviewer paragraph is limited to what the derivation shows.

---

## AN-01 — Boundary metrics for all eight-seed runs, with covariates
Reviewer issues: CW-02, QA-02
Status: VERIFIED (EXPLORATORY / POST HOC; decides nothing)
Pre-registration: n/a (exploratory, as posted)
Code revision: `223fa14` (gate), `77b7840` and `d42e68c` (full analysis, regression caveat)
Commands: `.venv/bin/python analysis/an01_boundary.py --stage gate`; `.venv/bin/python analysis/an01_full.py`; `.venv-analysis/bin/python analysis/mixed_models.py an01 RESULT_TABLES/AN01_long.csv RESULT_TABLES/AN01_regression.md`
Datasets: saved prediction maps of the 64 SE runs, `Result/ABC/<arch>_<arm>_s<seed>/{COD10K,NC4K}`
Configuration: Boundary-IoU (erosion band 0.02 · diagonal; matches the reference implementation of Cheng et al. 2021) and Boundary-F, at thresholds 0.4, 0.5 and 0.6; the SE campaign's 2σ̂ rule per metric with ≥ 7/8 signs
Seeds: 42, 43, 45, 46, 47, 48, 49, 50
Artifacts: `RESULT_TABLES/AN01_boundary_8seed.md`, `RESULT_TABLES/AN01_boundary_8seed.csv`, `RESULT_TABLES/AN01_boundary_8seed_per_run.csv`, `RESULT_TABLES/AN01_regression.md`, `RESULT_TABLES/AN01_sinetv2_diagnostics.csv`, `RESULT_TABLES/AN01_summary.json`, `EXPERIMENT_LOGS/AN01_reproduction_gate.log`, `EXPERIMENT_LOGS/AN01_full.log`, `FIGURES/AN01_boundary_by_arm.pdf`
Results (Boundary-IoU at 0.5, COD10K):

| Arch | Contrast | 3 seeds (submitted) | 8 seeds: Δ, × bar, signs, Welch 95% CI |
|---|---|---|---|
| SINet | C10 − B | 1.37× | +0.0046, 0.30×, 5/8, [−0.0056, +0.0147] |
| SINet | CINV − B | 1.34× | +0.0098, 0.64×, 7/8, [+0.0046, +0.0150] |
| SINet | CSHUF − B | — | +0.0046, 0.30×, 6/8, [−0.0015, +0.0106] |
| SINet-v2 | C10 − B | 0.16× | +0.0002, 0.02×, 4/8, [−0.0052, +0.0056] |
| SINet-v2 | CINV − B | 0.41× | +0.0033, 0.34×, 6/8, [−0.0019, +0.0084] |

None of the 80 contrast rows clears its bar at eight seeds (2 architectures × 2 endpoints × 4 metric/threshold cells × 5 contrasts). Unadjusted, 14 of the 80 Welch 95% intervals exclude 0: 12 are CINV − B, 2 are CSHUF − B, and none is C10 − B.

Interpretation: The 3-seed boundary signal does not survive at eight seeds under the rule. The largest contrast is CINV − B on SINet (0.64× bar, 7/8 seeds). CINV and C10 share one concentration, and C10 − B is 0.30×, so concentration alone cannot account for that contrast. With one fixed set per C-arm, an effect of that particular set cannot be separated from a shape effect, which is why CDR uses five permutations per level. The intervals are post hoc and unadjusted across 80 rows; the rebuttal reports the per-contrast numbers and does not treat them as evidence for concentration.
Limitations: Post hoc, with many rows and no multiplicity control. The pooled regression is degenerate (boundary variance, non-convergence) and its covariates are post-treatment. By the author's rule it is kept only in RESULT_TABLES, and the rebuttal never cites its pooled interval.
Verification notes: (1) The gate regenerated the 36-run per-run table and the 0.4/0.6 sweep and matched the submitted table. (2) The 3-seed ratios match at 2 dp (|diff| ≤ 4e-5, from 6-dp rounding). (3) Same maps, same scorer. (6) Labelled exploratory throughout.

---

## AN-02 — Literature and protocol audit for the performance gap
Reviewer issues: CW-03, QA-03
Status: VERIFIED
Pre-registration: n/a
Code revision: `0146abc`; corrected sentence 2026-11-16 (E3-e was not run)
Commands: `.venv/bin/python analysis/an02_published.py`
Datasets: original papers (hashes in `EXPERIMENT_LOGS/AN02_papers.sha256`); released SINet-V2 and RISE prediction maps (hashes in `EXPERIMENT_LOGS/EXP03_downloads.sha256`)
Configuration: published S_α, mean E_φ, F_β^w and MAE, each with table and page; re-score tolerance 0.002
Seeds: n/a
Artifacts: `RESULT_TABLES/AN02_published_baselines.md`, `RESULT_TABLES/AN02_published_baselines.json`, `RESULT_TABLES/AN02_rise.bib`
Results:
- The reviewer's values trace to our 3-seed SINet C10 means (0.7185 / 0.7690), RISE Table 1 (0.763 / 0.805), and SINet-V2 Table 2 (0.815 on COD10K). SINet-V2's 0.847 on NC4K matches our re-score of its released maps (0.8472); the SINet-V2 paper does not report NC4K.
- 12 of 12 published values reproduce within 0.002 under our scorer (max |diff| 0.0005).
- RISE's detector is SINet-V2, trained with SINet-V2's own recipe on pseudo masks for the same 4,040 COD10K/CAMO images we use unlabelled. DINOv2 features are used only to make those masks.
Interpretation: The posted description of RISE ("a different representation … and a different training pipeline") is inaccurate. The gap to RISE reflects the supervision on the real target images much more than the detector.
Limitations: Published NC4K numbers are missing for SINet-V2 and S2R-COD. S2R-COD rows are as published (COD10K only).
Verification notes: (1) PDFs are hashed. (2) Table and page are recorded per value. (4) One scorer for every re-scored row.

---

## AN-03 — Foreground pool and generator constraints
Reviewer issues: CW-04, QA-04
Status: VERIFIED
Pre-registration: n/a
Code revision: `e43a5e9`
Commands: `.venv/bin/python analysis/an03_foreground.py`; `.venv/bin/python analysis/an03_counts_check.py`
Datasets: base pool (4,447 foregrounds), LAKE-RED renders (4,447), source photographs (4,447; 4,443 distinct), DINOv2 ViT-L/14 caches `rebuild/E0/cache/`
Configuration: per-arm distinct foregrounds and reuse; variance explained by foreground identity (R², ICC, against random pairing); per-cluster nearest-cutout distances
Seeds: n/a
Artifacts: `RESULT_TABLES/AN03_foreground_diversity.md`, `RESULT_TABLES/AN03_foreground_diversity.csv`, `RESULT_TABLES/AN03_arm_overlap.csv`, `RESULT_TABLES/AN03_cluster_fill.csv`, `RESULT_TABLES/AN03_summary.json`, `EXPERIMENT_LOGS/AN03_counts_check.log`, `FIGURES/AN03_fill_distance.pdf`
Results:
- Every injected render re-uses a foreground already in the base pool: 1,000 of 1,000 in all 23 arms. The training pool always holds 4,447 distinct foregrounds in 5,447 images, and 36.7% of its images show a foreground that appears twice.
- Foreground identity explains most of the render-embedding variance: R² = 0.856 against 0.499 for random pairing; ICC 0.713 against −0.001. A render's cosine similarity is 0.730 to its own base render and 0.057 to a random one.
- In 52 of 75 clusters, the nearest available cutout is farther from the centroid than the median real member (median distances 0.669 and 0.219).
Interpretation: Synthetic diversity comes from backgrounds. Foreground identity dominates the embedding, and most clusters have no close foreground.
Limitations: Cutouts sit on a flat background while cluster members are full photographs, so part of the distance gap is the representation itself. Coverage and silhouette are cited from committed outputs, not re-derived.
Verification notes: (2) The independent re-count passes for all 23 arms. (7) The rebuttal uses the counts, R²/ICC and the 52 of 75, with the caveat.

---

## EXP-01 — Confirmatory equivalence campaign (EQ)
Reviewer issues: CW-01, QA-01
Status: PARTIALLY VERIFIED. The campaign is INCOMPLETE under Amendment 1: 46 of 81 runs. The primary question is resolved: **equivalent**.
Pre-registration: `prereg/EQ.md` (`2137849`, 2026-11-09 08:13); Amendment 1, n = 27 per arm (`808988b`, 2026-11-11 21:16, before any EQ run); hashes in `prereg/EQ.hash`
Code revision: jobs at `808988b`; runner guard: pipeline hash 281e42b8c66b3a74 on every launch
Commands: queue `rebuild/RL5B/rl5b_runner.py --jobs rebuild/RL5B/queue_jobs.json`; analysis `analysis/eq_analysis.py --workers 8 --allow-incomplete`, triggered once by `rebuild/RL5B/eq_autorun.sh` (2026-11-17 07:40, finished 08:16); spot check `analysis/eq_spot_rescore.py`; manuscript sentences `analysis/make_eq_sentences.py`
Datasets: as above; pools gated 6/6 (`EXPERIMENT_LOGS/EXP01_build_pools_eq.log`)
Configuration: arms B, C10 and CSHUF on SINet; Welch TOST at ±0.005 (H1: C10 − B; H1b: C10 − CSHUF); 2σ̂ rule; pooled EQ+SE secondary
Seeds: completed 101–116 for B and 101–115 for C10 and CSHUF. Not run: 35 jobs (B s117–127, C10 and CSHUF s116–127), named in `EXPERIMENT_LOGS/EXP01_analysis.log`
Artifacts: `RESULT_TABLES/EXP01_EQ.csv`, `RESULT_TABLES/EXP01_EQ.md`, `RESULT_TABLES/EXP01_EQ_summary.json`, `RESULT_TABLES/EXP01_EQ_metrics.csv`, `FIGURES/EXP01_forest.pdf`, `EXPERIMENT_LOGS/EXP01_analysis.log`, `EXPERIMENT_LOGS/EXP01_autorun.log`, `EXPERIMENT_LOGS/EXP01_spot_rescore.log`, `revision/eq_result.tex`
Results (S_α; Welch; n per arm C10 / other):

| Endpoint | Contrast | n | Δ | 90% CI | 95% CI | TOST p | Decision | 2σ̂ rule |
|---|---|---|---|---|---|---|---|---|
| COD10K | C10 − B (H1, primary) | 15 / 16 | +0.0006 | [−0.0027, +0.0039] | [−0.0033, +0.0045] | 0.0149 | (i) equivalent | 0.05×, 8/15, within noise |
| COD10K | C10 − CSHUF (H1b) | 15 / 15 | −0.0009 | [−0.0051, +0.0034] | [−0.0060, +0.0043] | 0.0555 | (ii) neither | 0.07×, 10/15, within noise |
| NC4K | C10 − B | 15 / 16 | +0.0005 | [−0.0013, +0.0022] | [−0.0016, +0.0025] | 0.0001 | (i) equivalent | within noise |
| NC4K | C10 − CSHUF | 15 / 15 | −0.0005 | [−0.0026, +0.0015] | [−0.0030, +0.0019] | 0.0004 | (i) equivalent | within noise |

The Holm-adjusted TOST p-values over the four tests are 0.030, 0.056, 0.0002 and 0.0012.

COD10K arm means (SD) are B 0.7139 (0.0054), C10 0.7145 (0.0053) and CSHUF 0.7153 (0.0081). σ̂ = 0.0064 (df 43), against 0.0034 in SE.

Interpretation: The pre-registered primary test establishes equivalence of targeted and random allocation within ±0.005 S_α on SINet·COD10K, and it survives Holm. Equivalence to the shuffled arm is not established on COD10K (p = 0.056); on NC4K it is.
Limitations:
- Only 15–16 of 27 seeds per arm were completed.
- **Run-to-run spread is about twice SE's.**
  - The lowest runs (CSHUF s115 0.6933, B s116 0.6974, C10 s111 0.7022) have the lowest pseudo-label counts (1346–1501), and across runs r(pseudo-label count, S_α) = 0.74.
  - Counts are more spread than in SE (SD 164 against 89).
  - Low counts occurred before the 11-13 kernel update too (CDR minimum 1487).
  - No run failed verification, and none is dropped (prereg EQ.6).
- The design-time power figures assumed the SE SDs.
Verification notes:
- (1) 46 runs, each with `train_ok` (step pin 253, rounds 2, hashes) and inference complete. No interim look: the analysis ran once, by the cron trigger, after the cutoff.
- (2) `analysis/audit_recompute.py` recomputes every EQ number quoted (PASS). Three runs re-scored from their saved maps, including the two lowest, match at 6 dp (`EXPERIMENT_LOGS/EXP01_spot_rescore.log`).
- (3) Scorer self-check PASS (0.717216 / 0.074463).
- (6) Pre-registered primary; secondaries and Holm reported.
- (8) H1b's non-equivalence on COD10K is reported.
---

## EXP-02 — Concentration dose-response (CDR)
Reviewer issues: CW-02, QA-02
Status: PARTIALLY VERIFIED (SINet complete and verified; the SINet-v2 replication was not run)
Pre-registration: `prereg/CDR.md` (`2137849`, 2026-11-09 08:13), with the draw rule committed in `138ad30` and the draw in `49383c0`; hashes in `prereg/CDR.hash`
Code revision: CDR jobs at `2137849`; analysis `analysis/cdr_analysis.py` (committed with the prereg); sentences `analysis/make_cdr_sentences.py`; mixed models `analysis/mixed_models.py` (`c32d547`)
Commands: `.venv/bin/python analysis/cdr_analysis.py --arch SINet --workers 8`; `.venv-analysis/bin/python analysis/mixed_models.py cdr RESULT_TABLES/EXP02_SINet_long.csv RESULT_TABLES/EXP02_SINet_mixed.md`; `.venv/bin/python analysis/make_cdr_sentences.py`
Datasets: CDR pools gated 6/6 (`EXPERIMENT_LOGS/EXP02_build_pools_cdr.log`, `EXPERIMENT_LOGS/EXP02_build_pools_cdr_lu.log`); allocation record `rebuild/ABC/out/cdr/cdr_allocations.csv`; draw log `EXPERIMENT_LOGS/EXP02_cdr_draw.log`
Configuration: levels LU (cluster-uniform), L1 (committed shape τ = 1.0) and LH (τ_H = 0.758), each with 5 permutations (one stream, seed 2027). Primary: Boundary-IoU at 0.5 on SINet·COD10K. D = ½(B + LU). σ̂ is pooled within allocations (df 24). Decision rule (a), (b) and (c) as pre-registered.
Seeds: LU 42, 43, 45, 46, 47; every L1 and LH allocation 42, 43, 45 (35 runs)
Artifacts: `RESULT_TABLES/EXP02_SINet_results.md`, `RESULT_TABLES/EXP02_SINet_summary.json`, `RESULT_TABLES/EXP02_SINet_per_run.csv`, `RESULT_TABLES/EXP02_SINet_long.csv`, `RESULT_TABLES/EXP02_SINet_mixed.md`, `EXPERIMENT_LOGS/EXP02_cdr_analysis_SINet.log`, `FIGURES/EXP02_dose_response_SINet.pdf`, `revision/cdr_result.tex`
Results (primary):

| Level | Δ vs D (D = 0.3308) | × bar (bar 0.0193) | permutations agreeing | between-permutation SD | rule |
|---|---|---|---|---|---|
| L1 (committed shape) | −0.0005 | 0.03 | 2/5 | 0.0081 | fails (a), (b), (c) |
| LH (twice as concentrated) | +0.0021 | 0.11 | 4/5 | 0.0026 | fails (a), (c) |

**Conclusion: not supported.** All 19 secondary measures (Boundary-IoU and Boundary-F at three thresholds, S_α, F_β^w, MAE and mean E_φ, on both endpoints) are also not supported. Reported, deciding nothing:
- Welch over units, 10 concentrated allocations against 9 dispersed units: +0.0024, 95% CI [−0.0024, +0.0072].
- Level-only mixed model: all level contrasts ≈ 0, CIs include 0. The covariate model is singular and is reported as unfit.

Interpretation: Concentrating the budget did not change boundary accuracy beyond noise. The concentration claim is therefore restricted to the training-set distribution, as pre-registered.
Limitations:
- One architecture: the SINet-v2 replication was not run.
- The rule's bar is 2σ̂ per run (0.0193), so it is insensitive to small effects. The descriptive unit-level CI excludes only effects above about +0.007.
- Delivered concentration is weaker than nominal. The nominal N_eff is 75, 29.9 and 14.9; the induced N_eff is 50.3, 44.5 and 40.9, and B is 42.5. The test is therefore a test of concentration as this pool can deliver it.
Verification notes:
- (1) 35/35 runs are complete and verified (step pin 253, rounds 2, hashes). Interrupted runs were discarded and re-run with the same seed.
- (2) Results are regenerated from per-run CSVs.
- (3) The pools are gated, and the set-distinctness gate passed.
- (6) Pre-registered primary; secondaries and models labelled.
- (8) The negative result is reported as such.

---

## EXP-03 — Protocol-matched baselines and gap decomposition
Reviewer issues: CW-03, QA-03
Status: PARTIALLY VERIFIED (E3-a, E3-c, E3-d and E3-f done; E3-b and E3-e not run)
Pre-registration: `prereg/E3.md` (`49383c0`; descriptive, no decision rule); hashes in `prereg/E3.hash`
Code revision: E3-c jobs at `49383c0`; tables `5c8d4c2`; manuscript fragments `20db526`
Commands: `.venv/bin/python analysis/e3_analysis.py external` (E3-a, E3-d); `... e3_analysis.py runs` (E3-c); `... e3_analysis.py anchors` (E3-f); `... e3_analysis.py table`; `.venv/bin/python analysis/make_protocol_table.py`
Datasets: real masks of the same 4,040 images (`Dataset/_download_ws4/TrainValDataset.zip`, images byte-identical to `Dataset/Target/Image`); released maps (`EXPERIMENT_LOGS/EXP03_downloads.sha256`)
Configuration: E3-c runs our trainer on the real masks, single round, with `--val_net student`. Each other row is one scorer on the same splits.
Seeds: E3-c 42, 43, 45 for each architecture
Artifacts: `RESULT_TABLES/EXP03_protocol_matched.md`, `RESULT_TABLES/EXP03_protocol_matched.csv`, `RESULT_TABLES/EXP03_gap_decomposition.md`, `RESULT_TABLES/EXP03_gap_decomposition.json`, `RESULT_TABLES/EXP03_external_scores.csv`, `RESULT_TABLES/EXP03_run_scores.csv`, `RESULT_TABLES/EXP03_anchor_scores.csv`, `EXPERIMENT_LOGS/EXP03_external.log`, `EXPERIMENT_LOGS/EXP03_runs.log`, `EXPERIMENT_LOGS/EXP03_anchors.log`, `FIGURES/EXP03_gap_bars.pdf`, `revision/table_protocol.tex`, `revision/gap_paragraph.tex`
Results (S_α; COD10K / NC4K):

| Component | SINet | SINet-v2 |
|---|---|---|
| Real masks, our recipe − C10 | +0.087 / +0.071 | +0.112 / +0.090 |
| Released SINet-V2 − our supervised anchor | — | +0.008 / +0.009 |
| RISE (re-scored) − C10 | — | +0.068 / +0.056 |
| Published − our re-score (same maps) | max abs diff 0.0005 | |

Anchors: the reproduced S2R-COD pair scores 0.7172 (two-round) and 0.7030 (mean teacher) under our scorer.

Interpretation: Most of the gap to supervised SINet-V2 is the absence of real labels; the official recipe adds under 0.01 on top. The gap to RISE (whose detector is ours) is about 0.06–0.07, and it reflects pseudo masks on the real target images against synthetic renders plus self-training.
Limitations: Without E3-e, the quality of RISE's masks cannot be separated from its recipe. E3-b was not re-trained; the released maps stand in for it. The components overlap and do not add up.
Verification notes: (2) The tables are regenerated from per-run scores. (3) The E3-a tolerance (0.002) passes. (4) One scorer and the same splits for every row; released maps are scored as released. (8) Missing cells are "—".

---

## EXP-04 — Replication at a higher operating point
Reviewer issues: CW-03 (generality), QA-03
Status: BLOCKED (compute). Dropped before launch on 2026-11-09 and never pre-registered (`prereg/OP.hash`).
Pre-registration: none
Code revision: n/a
Commands: none
Datasets: n/a
Configuration: n/a
Seeds: n/a
Artifacts: `EXECUTION_STATUS.md` (deviation 11)
Results: none
Interpretation: Whether the null is specific to the low operating point is untested. The final rebuttal says so, as posted Part 3 promised.
Limitations: n/a
Verification notes: no run exists (queue records).

---

## DOC-01 — Claim calibration and the main-text CI/TOST table
Reviewer issues: CW-01, CW-02, QA-01, QA-02
Status: PARTIALLY VERIFIED (EQ sentences pending; title for the author)
Pre-registration: n/a
Code revision: `96e4fda`, `f254a3a`, `c5c73fd`
Commands: `latexmk -pdf -interaction=nonstopmode -outdir=build_rev AD-PCHGS-revised.tex` (in `revision/`)
Datasets: n/a
Configuration: `revision/AD-PCHGS-revised.tex`; the outcome macros `\eqverdict` and `\eqshort` are pending, while `\cdrverdict` and `\cdrshort` are filled from `revision/cdr_result.tex`
Seeds: n/a
Artifacts: `RESULT_TABLES/DOC01_claims.md`, `revision/AD-PCHGS-revised.tex`, `revision/table_ci_tost.tex`, `revision/table_boundary_8seed.tex`, `revision/manuscript.diff`
Results: 27 changes, listed in `RESULT_TABLES/DOC01_claims.md`: 25 outcome-independent, and 2 added on 11-16 (the delivered-concentration sentence and the untested operating point). The CDR sentences are filled. The compiled revision has 27 pages, the main text ends on page 10 (the discussion-period limit), and there are no errors or undefined references.
Interpretation: Every overclaim listed in the posted rebuttal is revised, including "no score of any quality helped here", the §3.2 heading and the boundary paragraph.
Limitations: The title is unchanged until the author decides. The EQ sentences go in on 17 Nov.
Verification notes: recompiled after every insertion; the page limit is re-checked.

---

## DOC-02 — Related work, RISE and the protocol table
Reviewer issues: CW-03, QA-03
Status: VERIFIED
Pre-registration: n/a
Code revision: `f254a3a`, `20db526`
Commands: `.venv/bin/python analysis/make_protocol_table.py`
Datasets: `RESULT_TABLES/EXP03_protocol_matched.csv`, `RESULT_TABLES/EXP03_gap_decomposition.json`
Configuration: generated fragments only; no hand-typed number
Seeds: n/a
Artifacts: `revision/table_protocol.tex`, `revision/gap_paragraph.tex`, `RESULT_TABLES/AN02_rise.bib`
Results: RISE is in §1.1 and App. A with verified BibTeX. The protocol table and the gap paragraph are in App. A.
Interpretation: The protocol differences the reviewer asked for are explicit, under one scorer.
Limitations: As EXP-03.
Verification notes: the fragments are regenerated from the CSVs; the build compiles.

---

## DOC-03 — Scope and limitations
Reviewer issues: CW-04, QA-04
Status: VERIFIED
Pre-registration: n/a
Code revision: `96e4fda`
Commands: as DOC-01
Datasets: n/a
Configuration: scope paragraph in the Discussion; one scope sentence each in the abstract, introduction and conclusion
Seeds: n/a
Artifacts: `revision/AD-PCHGS-revised.tex`, `revision/manuscript.diff`
Results: Every item of the posted scope list is named. That covers the LAKE-RED generator, the 4,447-foreground pool and background-only variation. It also covers k = 75 clusters of frozen self-supervised features, the two SINet architectures, two-round self-training and N = 1000. The AN-03 numbers are included, and the Discussion states that no claim is made about other generators.
Interpretation: The conclusions are bounded to the tested setting.
Limitations: The title still carries the general wording until the author decides.
Verification notes: checked against posted Part 4, item 1.

---

## BRIDGE — Determinism and neutrality of the footprint flags (supporting)
Reviewer issues: supports EXP-01 and EXP-02
Status: VERIFIED
Pre-registration: `prereg/BRIDGE.md` (`49383c0`; path amendment `de3746f`); hashes in `prereg/BRIDGE.hash`
Code revision: `138ad30`
Commands: `.venv/bin/python analysis/bridge_check.py`
Datasets: `SINet_C10_s42`, re-trained into a fresh pool with `--save_ckpts minimal --link_pool`
Configuration: declared band |diff| ≤ 0.0069 (2σ̂_SE)
Seeds: 42
Artifacts: `EXPERIMENT_LOGS/BRIDGE_check.log`, `EXPERIMENT_LOGS/BRIDGE_check.json`
Results: COD10K |ΔS_α| = 0.00006, within the band. All 21,828 linked source files are unchanged.
Interpretation: The flags do not change results beyond run-to-run nondeterminism, and no source render was written to.
Limitations: The difference is not exactly 0 at 6 dp, so runs are near-deterministic, not bit-identical.
Verification notes: hashes recomputed after the run.

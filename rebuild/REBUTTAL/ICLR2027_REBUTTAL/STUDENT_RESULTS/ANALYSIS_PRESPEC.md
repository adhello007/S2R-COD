# Analysis pre-specification: reviewer dypE follow-up (post-review, exploratory)

**Written:** 2026-11-11 (IST), before any outcome listed in §1.2 was computed.
**Committed:** in the same commit as this file, on branch `rebuttal/dypE-validation`. Its hash is recorded
in `EXECUTION_STATUS.md`.
**Base:** `8d1d0795fc4e19474d51f89adf0c2d8fb977f313`.

**Status.** Every analysis below is **post-review and exploratory**. None re-decides a pre-registered
verdict (`rebuild/ABC/PREREGISTRATION*.md`, `rebuild/SE/PREREGISTRATION_SE.md`), and no seed, arm or
run is added to any committed campaign. Where this file and a later result disagree, this file
governs. Any deviation is logged in `EXECUTION_STATUS.md` §Deviations with a reason.

## 1. What had and had not been seen when this was written

### 1.1 Seen during discovery (disclosed)
- Committed per-run S_α and MAE for all 64 eight-seed runs (`rebuild/ABC/out/se/abc_metrics.csv`), the
  committed SE verdict JSON (including the eight per-seed C10−B differences on SINet/COD10K), and the
  committed `tab:tost` (Welch) and `tab:boundary` (three-seed, COD10K) tables in the manuscript.
- An in-memory calculation (nothing saved) of the **paired** and **Welch** 95% CIs for C10−B on all four
  S_α cells from the committed CSV. Primary paired 95% CI ≈ [−0.0023, +0.0070]; within-seed correlation
  of B and C10 between −0.36 and −0.04. **The TH-01 S_α results are therefore not blind.** The method
  below is the one the brief prescribes; it was not chosen in light of those values.

### 1.2 Not seen (pre-specified here)
Eight-seed or NC4K boundary metrics; per-seed boundary differences beyond the committed three-seed
table; the architecture interaction; any per-seed overlap between arm stem lists; theoretical exposure;
pseudo-label set overlaps; EXP-01 overlaps at N > 1000; quota invariants; silhouette and
between-cluster variance; coverage re-estimation; the CHAMELEON re-run and mask-release comparison.

## 2. Global conventions
- Seeds S = {42, 43, 45, 46, 47, 48, 49, 50}; n = 8 unless a cell says otherwise. The runs are exactly the
  64 in `RESULT_TABLES/run_manifest.csv`.
- Architectures: SINet, SINet-v2. Endpoints: COD10K-test (primary), NC4K (secondary). CAMO-250 is the
  checkpoint-selection split and is never an endpoint.
- RNG for every bootstrap or random sample: `numpy.random.default_rng(20261111)`, with a fixed draw order
  per script.
- α = 0.05. Every CI is two-sided 95% unless labelled 90% (the TOST interval).
- Per-run value = the arithmetic mean over images of the per-image metric, as in the committed scorer.
- Rounding: full precision is stored; tables show 4 dp (metrics) or 3 dp (p-values).
- **Multiplicity:** no family-wise correction decides anything. Holm-adjusted p-values are reported
  beside raw p as sensitivity for each family: TH-01 (4 C10−B S_α cells), AN-03 (whole grid), and
  AN-03 interaction (whole grid). Every cell is reported; none is dropped.
- Labels: "submitted-paper evidence" means values in the manuscript or committed artifacts;
  "post-review evidence" means computed here.

## 3. AN-01: re-scoring and integrity
- Scorer: `score(gt_dir, pred_dir)` imported unchanged from base `rebuild/ABC/abc_evaluate.py`, using
  base `Eval/metrics.py`. GT is `Dataset/Test/{COD10K,NC4K}/GT`, and predictions come from the manifest
  paths.
- **Gate 1:** the B1 scorer validation (`Result/SINet/S2C` vs COD10K GT → S_α 0.717216, MAE 0.074463,
  tolerance 1e-5) must pass, if the B1 predictions are present. If they are absent, this is recorded and
  Gate 2 is the sole check.
- **Gate 2:** for each of 128 run×endpoint rows and each of the nine committed metrics, the re-score
  rounded to 6 dp must equal the committed CSV value. A mismatch is reported as is; it is never patched.
- Independent S_α: a separate NumPy implementation of Fan et al. (2017), written from the paper and not
  from `metrics.py`. It runs on 4 runs (SINet_B_s46, SINet_C10_s46, SINetv2_B_s46, SINetv2_C10_s46) ×
  200 images per endpoint, drawn with the global RNG from the sorted GT list. Pass: max per-image
  |Δ| ≤ 1e-6. Otherwise the convention difference is documented.
- Welch reproduction: re-implement `welch_tost` and compare with `tab:tost`, all 16 rows, at 4 dp.

## 4. TH-01: paired inference
For each architecture × endpoint and contrast X−Y (primary: C10−B; secondary: C10−CSHUF, C10−CINV,
CSHUF−CINV, CINV−B, CSHUF−B):
- D_i = S_α(X, i) − S_α(Y, i), i ∈ S, using the AN-01 re-scored full-precision values.
- Report: mean D̄; SD(D) (ddof 1); SE = SD/√n; t₇ 95% and 90% CIs; two-sided paired t p; sign count
  #{D_i > 0}; one-sided 95% upper bound U = D̄ + t₀.₉₅,₇·SE (effects > U excluded at the one-sided 5% level).
- Paired bootstrap: percentile and BCa 95% CIs, 20 000 resamples of the 8 pairs. Labelled unreliable at
  n = 8 and used as sensitivity only.
- Exact sign-flip test: all 2⁸ = 256 sign vectors; two-sided p = #{|mean(εD)| ≥ |D̄|}/256. Assumption
  stated: under H0 each D_i is symmetric about 0. This is plausible because the arms are independent
  trainings, but it is not guaranteed.
- Leave-one-seed-out: D̄ and paired 95% CI with each seed removed (n = 7).
- Paired TOST at δ = 0.005: p = max(p_lower, p_upper) with t₇. Equivalence is claimed iff the 90% CI is
  inside (−δ, +δ). Smallest δ at which equivalence holds = max(|L₉₀|, |U₉₀|).
- Welch counterpart (as in the manuscript) beside each paired value. Covariance disclosure: r(X, Y)
  across seeds, Var(D) vs Var(X) + Var(Y), and SE_paired/SE_Welch.
- Scales, kept separate: whether the 95% CI excludes +0.0142 (study-specific reference effect), whether it
  excludes +0.005, the ±0.005 equivalence result, and the committed 2σ̂_SE gate reproduced from the
  committed pooled σ̂ (df 28) as a different, descriptive decision rule.
- Cross-check: pure-NumPy implementation vs scipy (`ttest_rel`, `ttest_ind`, `t.ppf`), agreement ≤ 1e-12.
  Known-answer test on synthetic data with an analytically known t statistic.

## 5. AN-02: overlap and exposure
- Identity: an injected item is a render stem (index into the 4447 LAKE-RED renders). Byte identity is
  checked by SHA256 of the render image and mask for every stem. The materialised pool
  `Dataset/Source/ABC/<rid>/` is checked against the committed `abc_pools.json` digests, by
  recomputation if the digest definition can be recovered from base code.
- For each seed and arm pair (X, Y) among {B, C10, CSHUF, CINV}, with I = |X ∩ Y|:
  - `one_sided_diff` = 1000 − I, `sym_diff` = 2(1000 − I), Jaccard = I/(2000 − I).
  - Fractions: one_sided_diff/1000; one_sided_diff/5447; sym_diff/(4447 + 2000 − I), the union of the
    two training pools; and the expected random overlap 1000²/4447.
- Reconciliation of "about 48% differ" and "8.8%": state which pairs and definition reproduce each, and
  report every pair, B pairs included.
- Foreground identity: a render's foreground is the base-pool stem it re-renders. Count distinct
  foreground IDs per arm, and how many are novel relative to the base pool.
- **Theoretical exposure** (pinned): per epoch, steps × batch source samples are drawn, with steps fixed
  at 253 or 127 and batch 16 or 32. Expected visits per source item per epoch = steps·batch/|pool|, by
  round (round 1 |pool| = 5447; round 2 |pool| = pool_r2 from `abc_runs.csv`). The arm-specific exposure
  contrast per epoch = one_sided_diff × steps·batch/|pool|, and totals multiply by epochs. FX unpinned
  values (341/171 steps) are shown for contrast. This assumes a fresh shuffle without replacement per
  epoch, truncated at `total_step`, which will be confirmed from base `MyTrain.py` and
  `Src/utils/Dataloader.py`.
- **Actual visits:** UNVERIFIED unless a per-sample sampler trace is found in the run logs. The search is
  recorded either way.
- Pseudo-labels: n_appended per run and its per-arm mean, compared with 1977/2025/1990/1979 as audit
  targets only. Where `Dataset/Source/ABC/<rid>_iteration2/` exists, the appended target-image sets are
  compared between arms at equal seed (Jaccard). Pseudo-labels are treated as a mediator and never
  adjusted for.
- Hand inspection: 12 injected items drawn by the global RNG. Check file existence, image/mask
  dimensions, mask binarity, and that the mask equals the base-pool mask of the same stem.

## 6. TH-02: quota invariants
- Quotas are recomputed with base C1 functions (`softmax_alloc`, `largest_remainder`, `es_permutation`)
  on the committed `target_es`.
- Checks: each quota vector sums to 1000; sorted quota multisets are identical across C10, CSHUF and
  CINV; CINV has exactly one fixed point (the median rank, k = 75 odd); CSHUF has no fixed point and
  ρ = −0.03351; and `s_e` matches the manuscript's 0.0101.
- Realised per-cluster counts after greedy selection are compared with nominal quotas (n_displaced).
- Concentration indicators per arm: normalised entropy, HHI, Gini, max share, clusters funded, TV from
  uniform. For B the expected per-cluster counts come from the cutout→cluster assignment.
- Edge cases are treated analytically: s_e → 0, ties, rounding, larger N, and pseudo-label feedback.

## 7. EXP-02 / AN-03: boundary re-score and architecture interaction
- Metrics: Boundary-IoU (d = round(0.02·diag)) and Boundary-F (θ = round(0.0075·diag)) via
  `metrics_one` imported unchanged from base `rebuild/DIAG/diag_boundary.py`, with its preprocessing
  (GT > 127; prediction bilinear-resized to GT if needed, then min-max normalised and binarised at t).
  Thresholds t ∈ {0.4, 0.5, 0.6}. NaN images (empty union) are excluded per the committed convention
  and counted.
- **Gate 3:** for the committed rows (3 seeds, COD10K, every arm in the committed CSVs, t = 0.4/0.5/0.6),
  the re-scored per-run means must equal `rebuild/DIAG/out/diag_boundary_per_run*.csv` to 1e-9. On
  failure, stop and investigate before any eight-seed number is used.
- Grid: 2 architectures × 2 endpoints × 3 thresholds × 2 metrics × contrasts {C10−B, CINV−B, CSHUF−B,
  C10−CINV, C10−CSHUF}. Per cell: n, seed IDs, D̄, paired t 95% CI, Welch 95% CI, sign count, raw and
  Holm p. Separately, the descriptive committed-style bar: 2 × pooled within-arm SD over the four arms
  at that cell (df 28), with |D̄|/bar. The three-seed subset {42, 43, 45} is reported in its own labelled
  rows for continuity with the manuscript.
- **Headline cell, fixed now:** Boundary-IoU, t = 0.5, COD10K, C10−B and CINV−B. All other cells are
  secondary.
- Interaction Δ_model = D̄_SINet − D̄_SINet-v2 per contrast/metric/endpoint/threshold:
  - (a) Welch-type: SE = √(s²_S/8 + s²_v2/8), Welch–Satterthwaite df, 95% CI. This is the primary.
  - (b) Exact permutation of architecture labels over the 16 per-seed differences, C(16,8) = 12 870
    splits, two-sided.
  - (c) Seed-matched sensitivity: E_i = D_S,i − D_v2,i with paired t. B's stem draw is the same at equal
    seed across architectures.
  - An interaction is never inferred from one architecture's p < 0.05 and the other's p ≥ 0.05.
- **Two-image CPU re-inference:** runs SINet_C10_s46 and SINetv2_C10_s46, on the first and last names of
  the sorted COD10K GT list. The base inference pipeline is reproduced (MyTest.py preprocessing and
  post-processing) with `map_location='cpu'` and `CUDA_VISIBLE_DEVICES=""`. Pass: max |Δ| ≤ 2 grey
  levels and ≥ 99.9% of pixels within ±1 of the stored PNG. Otherwise report FAILED with the numbers.
  CPU vs GPU floating-point differences are expected and disclosed.

## 8. AN-04: coverage and diversity
- Reproduce first: run the committed estimator (`rebuild/FinalPaper/AD-PCH-230926/figs/make_coverage_table.py`
  and its inputs) unchanged in logic. **Gate 4:** reproduce the published synthetic recall range
  0.13–0.54 and the real-source range 0.71–0.75 at their printed precision.
- Then: per-arm distinct foreground IDs; cluster occupancy of each arm's injection; CAMO share of quota
  vs of target pool; kNN precision and recall against the real target at k ∈ {3, 5, 10} (or the
  committed k plus neighbours) on each available embedder (dinoL518, dinoL224, clipL224), stratified by
  domain (COD10K/CAMO), cluster and uncertainty quintile. CIs by group bootstrap over foreground IDs
  (2000 resamples).
- **k-means silhouette** of the committed k = 75 partition on L2-normalised target embeddings (cosine
  distance), over all target images, plus a per-cluster distribution.
- **Between-cluster share of structural-error variance** η² = SS_between/SS_total of per-image
  (1 − S_α) on COD10K-test images assigned to their nearest committed centroid. Two sources:
  (i) the committed diagnostic's predictions, to reproduce 20.5%; (ii) each arm's eight-seed predictions,
  as robustness. **Endpoint labels are used here only as a descriptive diagnostic. No result feeds any
  selection, allocation, threshold or checkpoint choice.**
- Per-pixel vs structural correlations (+0.8553 / +0.4276) are reproduced from committed B1 artifacts if
  their inputs are present.

## 9. AN-05: CHAMELEON protocol paths
- Tier A as published: same-dimension groups; 32×32 grey RMS < 14.0 to shortlist; full-res RGB mean
  abs diff < 6/255 to confirm. The released code comes from base (`rebuild/D2*`) and is reused unchanged.
  Tier B as published: SIFT, Lowe 0.75, RANSAC ≤ 4 px, ≥ 20 inliers, warp check, with `animal-7` rejected
  as in the manuscript. The base `rebuild/DIAG/diag_chameleon_ext.py` logic is reused. **Thresholds are
  not changed.**
- **Gate 5:** 41 Tier-A plus 9 Tier-B = 50 confirmed; 44 with a COD10K-train partner.
- Pools, checked separately: base source (4447 HKU-IS pairs; supervised in this paper), the unlabelled
  target 4040 (COD10K-train 3040 + CAMO-train 1000), CAMO-250 (checkpoint selection), and the test
  splits.
- Exact SHA256 and pixel-identity against every pool. Expected from the manuscript: 0 against the
  training pool and 3 against CAMO-250 (`animal-17/25/60`).
- Output fields are kept separate: `confirmed_floor` (50), `in_cod10k_train` (44) and `unchecked` (16).
  The table has exactly 76 rows, each `confirmed` or `unchecked`. An assertion fails otherwise.
- Pathway matrix per image × {supervised source labels, unlabelled target image, checkpoint selection,
  held-out test}, for (i) this paper's protocol and (ii) the common supervised COD protocol that trains
  with masks on COD10K-train + CAMO-train. Values: direct / possible / absent / unknown.
- Mask releases: compare `Dataset/Test/CHAMELEON/GT` with `Dataset/chameleon_new/masks` on polarity,
  checksum and per-image disagreement, and the MAE of the manuscript's prediction set under each
  release (target 0.2196 vs 0.0816).
- Self-tests: a known-answer test (JPEG re-encode and rescale or crop of CHAMELEON images must be found)
  and the NC4K negative set. False-positive count reported.

## 10. EXP-01 preflight (CPU only; training BLOCKED for compute)
- Reproduce N = 1000: B stems for all 8 seeds and C10 stems must equal the committed stem files byte for
  byte, via base `abc_common`/C1 code pointed at the committed E0 cache.
- Simulate N ∈ {2000, 3000}, plus 4447 as the saturation check: B_N via `default_rng(700000 + seed)`
  without replacement; C10_N via the same allocation, ranking and greedy selection at budget N.
- **Primary contrast metric, fixed now:** DC(N) = mean over 8 seeds of (N − |B_N ∩ C10_N|)/(4447 + N),
  the fraction of the training pool that differs between the two arms.
- Secondary: per-seed min/max, Jaccard, distinct foreground IDs, n_displaced, and theoretical pinned
  exposure contrast = (N − I)·steps·batch/(4447 + N) per epoch. Unpinned exposure uses
  steps = ⌈(4447+N)/batch⌉ if the source loader drove (FX-style).
- **Pass rule:** some N ∈ {2000, 3000} with DC(N) ≥ 1.5 × DC(1000) **and** min-over-seeds DC(N) >
  max-over-seeds DC(1000). If it passes, the smallest passing N is the proposed design. If not, larger-N
  training is not useful in this pool, and a fixed-budget, less-overlapping draw is proposed and labelled
  a different algorithm.
- Training under any outcome: BLOCKED (no GPU before the deadline).

## 11. EXP-03 gate
Requires a verified generator that produces genuinely new foreground content, legally usable and
independently validated. LAKE-RED re-renders the backgrounds of a fixed foreground pool, so it does not
qualify. A search of the repository and local model directories is recorded. No downloads.

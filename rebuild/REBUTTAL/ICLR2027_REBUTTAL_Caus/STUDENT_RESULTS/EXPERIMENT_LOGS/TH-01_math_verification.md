# TH-01: allocation shape, direction, and what effective rank implies

**Status: VERIFIED** (quota mathematics, new shapes and the rank argument). The trained outcome of the
new shapes is EXP-01's, reported separately.

Code: `rebuild/CAUS/exp01_alloc.py` and `exp01_alloc_test.py` (36/36 assertions pass),
`exp01_tables.py`, `th01_rank.py`, `caus_repro_c1.py`. Commits: `b21b67c`, `d96ca60`.

## 1. The allocation rule reproduces exactly

The rule is Equation `eq:alloc`: a softmax over cluster scores in units of their population
standard deviation (s_e = 0.0101), at τ = 1.0, followed by largest-remainder rounding to N = 1000 with
ties broken by the lower cluster index.

- **C10:** this rule, followed by the committed selector (R2 grey-128 cutout embedding, dinoL518
  centroid ranking, desc_nc serving order, greedy distinct selection), reproduces the committed C10
  stem list byte-for-byte.
- **Other committed arms:** CORACLE, CSHUF, CINV and the three per-seed B draws reproduce
  byte-for-byte too.
- **Independent check:** OR-PROP's quotas from a separate plain-Python largest-remainder agree with
  the shared code.

## 2. Shape and direction, defined

- **Shape** is the sorted multiset of integer quotas. The concentration diagnostics are all
  functions of it: funded clusters, top-1 and top-5 share, normalised entropy, HHI, Gini and TV
  from uniform.
- **Direction** is Spearman(q, signal) on the unsorted per-cluster quotas: against the true-error
  vector for oracle arms, against target ES for method arms.
- A permutation preserves shape exactly and changes only direction. That is why CSHUF, CINV and
  CORACLE share C10's multiset (`shape_sha256` identical), and why each new shuffle shares its
  parent's multiset.

Values: `RESULT_TABLES/TH-01_quota_properties.csv`; per cluster: `TH-01_oracle_shapes.csv`.

| Arm | funded | max q | top-5 share | entropy | HHI | Gini | ρ(q, err) |
|---|---|---|---|---|---|---|---|
| C10 / CORACLE / CSHUF / CINV | 75 | 194 | 0.505 | 0.787 | 0.074 | 0.627 | +0.235 / +0.996 / −0.022 / −0.246 |
| OR-PROP | 75 | 24 | 0.109 | 0.989 | 0.015 | 0.174 | +0.996 |
| OR-TOP10 / -SHUF | 10 | 100 | 0.500 | 0.533 | 0.100 | 0.867 | +0.589 / −0.094 |
| OR-TOP5 / -SHUF | 5 | 200 | 1.000 | 0.373 | 0.200 | 0.933 | +0.432 / −0.005 |

ρ(q, err) for the top-k arms is below 1 only because the quota vector has 65 or 70 tied zeros.

## 3. The new oracle shapes are feasible, and one of them has no testable direction

- **Capacity:** every cluster can draw from all 4,447 renders, so any quota up to 1000 is
  realisable without duplicates. Every new arm yields exactly 1000 distinct stems.
- **Capacity policy:** `eligible_capacity_policy` = "all 4447 renders eligible to every cluster;
  greedy distinct, desc_nc serving; no per-cluster cap". How deep each cluster had to walk its
  ranking is in `TH-01_eligibility_caps.csv`.
- **OR-PROP's direction is untestable.** Per-cluster error spans only 0.087–0.471, so a quota
  proportional to error is nearly flat (4–24 per cluster). Its frozen shuffle shares 897 of 1000
  images (Jaccard 0.813). The deterministic rank-reversal shares 844 (Jaccard 0.730). Both fail the
  inherited same-shape distinctness gate (≤ 0.50).
- **Consequence:** at that shape, direction cannot be tested with this selector, and OR-PROP-SHUF was
  not trained (`PREREGISTRATION_EXP01.md`, smaller-plan clause).
- **The top-k shapes pass:** OR-TOP10 against its shuffle is at Jaccard 0.216, and OR-TOP5 against
  its shuffle at 0.198.

## 4. What "effective rank" means in the original analysis

`rebuild/C1/c1_variance_coverage.py:166` defines effective rank as the **participation ratio**
PR = (Σλ)² / Σλ² of the covariance eigenvalues. It is not the entropy effective rank of Roy & Vetterli,
and not numerical rank.

- **Reproduction:** re-running the original code from the frozen embeddings reproduces the committed
  ratio, mean **0.63366** over 20 cells, below 1 in 20/20 (range 0.266–0.955).
- **Exploratory alternative:** under the entropy definition the same comparison gives **0.796**,
  below 1 in 20/20 (`AN-02_probe_geometry.csv`, `AN-02_effrank_definitions.csv`).

## 5. Concentration does not imply lower effective rank

**Analytic.** A mixture's covariance is Σ(w) = Σ_j w_j Σ_j + Σ_j w_j (μ_j − μ̄)(μ_j − μ̄)ᵀ, a
weighted within-cluster term plus a between-cluster term. Changing w moves the two terms in
different directions, so quota entropy alone determines no sign. Two exact constructions show it,
each confirmed by Monte Carlo with 200,000 samples (`TH-01_rank_constructions.csv`):

| Construction (d = 10) | weights | PR | entropy erank |
|---|---|---|---|
| C1: isotropic cluster I₁₀ + rank-1 cluster 10·e₁e₁ᵀ, equal means | uniform (½, ½) | 3.08 | 5.35 |
| | concentrated on the isotropic cluster (0.9, 0.1) | **9.17** | 9.64 |
| | concentrated on the rank-1 cluster (0.1, 0.9) | **1.21** | 1.65 |
| C2: three I₁₀ clusters, means at 0, ±4e₁ | uniform | 2.94 | 5.16 |
| | concentrated (0.9, 0.05, 0.05) | **8.54** | 9.36 |
| | all on one cluster | **10.00** | 10.00 |

In C1 the same degree of concentration either triples or nearly erases the effective rank, depending
on *which* cluster receives the budget. In C2 concentrating the budget raises it monotonically,
because the between-cluster spread is what made the uniform mixture low-rank.

**Empirical, on the studied pool.** `AN-02_shape_geometry.csv` runs each shape through the committed
selector and compares it with 20 uniform random draws of 1000:

- **OR-TOP5-SHUF:** the most concentrated selection tested (5 clusters, entropy 0.373) has a PR ratio
  of **0.943 (R2) / 0.928 (R3)**, the closest to random of any arm. It is still separable from random
  (held-out probe d = 0.55 / 0.43).
- **FLAT:** a perfectly flat quota (13–14 per cluster, entropy 1.000) has a PR ratio of
  **0.855 / 0.882**. It is also separable (d = 0.52 / 0.48).

Both the lower rank and the separability therefore come largely from the selector itself: each
cluster takes the renders closest to its centroid. Concentration adds to that effect, but it is not
the whole of it.

## 6. Qualifications for the reviewer and for the paper

1. "Every non-uniform allocation has lower effective rank" is false as mathematics (§5, analytic).
   It also fails empirically in this pool: the 5-cluster OR-TOP5-SHUF keeps near-random rank.
2. The paper's 0.634 is an empirical property of the studied selections under the participation
   ratio. It is reproduced exactly and is not a theorem.
3. The paper says (§4.2) that "only removing the unevenness itself … collapses" the probe separation.
   Its collapse control was random-vs-random, which removes both concentration and centroid matching.
   The FLAT arm separates the two: with the quotas flattened but matching kept, d stays at 0.52 (R2)
   / 0.48 (R3), against 0.64 / 0.54 for C10 at N = 1000.
   - The supported reading: the probe detects matching plus concentration, and the score's
     direction adds nothing (+0.0073 d against its own shuffle).
   - The unsupported reading: the probe detects concentration alone.
4. No geometric result here is evidence about detector accuracy. Accuracy is EXP-01's question.

**Missing data.** The oracle vector has a value for all 75 clusters: n_test is 1–94 per cluster, sum
2026, with one single-image cluster. No shrinkage rule was needed, so none was applied. The noise in
low-n clusters is disclosed in the OR pre-registration (§OR.2.3).

**Oracle-source label (TH-01 acceptance).** Every new oracle quota comes from the endpoint-label-leaky
CORACLE vector; the shuffles are leaky in shape only. No disjoint calibration source exists in the
pre-rebuttal workspace (`AN-05_leakage_and_calibration.md`).

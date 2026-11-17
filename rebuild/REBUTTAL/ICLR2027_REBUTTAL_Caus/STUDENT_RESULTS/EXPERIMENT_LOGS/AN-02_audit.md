# AN-02: allocation geometry, shapes, distinctness and probe attribution

**Status: VERIFIED.** The original analysis was reproduced from raw embeddings, and the new shapes
were preflighted before any training. Code: `rebuild/CAUS/exp01_tables.py`, `caus_repro_c1.py`,
`th01_rank.py`. Log: `AN-02/c1_reproduction.log`.

## 1. Quotas and selections reproduce exactly

- **Committed lists.** The C10, CORACLE, CSHUF, CINV and B_s42/43/45 stem lists are reproduced
  byte-for-byte by the committed selector (`exp01_alloc_test.py`).
- **Tracing selector.** A second selector records which cluster took each image. It is asserted
  identical to the committed `greedy_select` on every arm, in both indices and `n_displaced`.
- **Per-image manifest.** `EXP-01_selection_manifest.csv` has 9,000 rows: stem, serving cluster, rank
  in that cluster's ordering, cosine to centroid, and render and mask sha256.

## 2. Distinctness (`AN-02_selection_overlap.csv`, every pair; chance overlap 224.9)

- **The manuscript's 452–511 differing images** between same-shape arms: verified. C10|CSHUF has 452
  differing (Jaccard 0.3774); C10|CINV has 511 (0.3236).
- **New same-shape pairs:**
  - OR-TOP10 / OR-TOP10-SHUF: 645 differing (0.2158). Passes.
  - OR-TOP5 / OR-TOP5-SHUF: 669 differing (0.1983). Passes.
  - OR-PROP / OR-PROP-SHUF: **103 differing (0.8132). Fails.**
  - OR-PROP / OR-PROP-INV: **156 differing (0.7301). Fails.**
  - The OR-PROP control is therefore declared uninformative and was not trained.
- **New shapes against CORACLE:** OR-TOP10 0.4695, OR-PROP 0.5232, OR-TOP5 0.4276. Disclosed
  beside every contrast.
- **Every new arm against random B:** 0.98–1.05× chance. The new arms are genuinely different from
  random.
- **Foreground identity:** every selection draws from the same 4,447 renders of 4,443 distinct source
  photographs. No arm reaches a foreground identity that another arm could not (AN-03).

## 3. Original probe and geometry, reproduced from raw embeddings

The original C1 code was re-run with its output redirected (`AN-02_c1_reproduction.csv`):
- **All four committed tables reproduce,** worst cell 3.1e-13: `c1_attribution` 100 rows,
  `c1_spread`, `c1_coverage`, `c1_occupancy`.
- **Probe attribution** (mean over 20 cells of held-out d(targeted) − d(null)):
  - vs own shuffle: **+0.0073** (targeted ahead in 13/20);
  - vs arbitrary cluster: **−0.0649** (4/20);
  - vs random direction: +0.0479 (18/20);
  - vs random draw: +0.8077 (20/20).
- **Effective rank** (participation ratio): mean ratio **0.634**, below 1 in 20/20 (0.266–0.955).
  The entropy effective rank (exploratory) gives 0.796, also 20/20.
- **Label-shuffle control:** with the targeted/random labels permuted, held-out d is −0.023 to
  +0.019, against a real d of 0.65–1.11. The held-out split does not leak.
- **Statistical dependence.** The 20 "cells" share the same 4,447-image pool and two embedders, so
  they are not independent replicates. The attribution counts are descriptive, not tests.

## 4. New: what the geometry is driven by (`AN-02_shape_geometry.csv`)

Each shape was run through the committed selector and compared with the same 20 random draws (N = 1000,
dinoL518). R2 and R3 are the two representations; their ordering agrees.

| Arm | funded | quota entropy | PR ratio (R2) | held-out d vs random (R2) |
|---|---|---|---|---|
| FLAT (13–14 per cluster) | 75 | 1.000 | 0.855 | 0.52 |
| OR-PROP | 75 | 0.989 | 0.908 | 0.51 |
| C10 | 75 | 0.787 | 0.754 | 0.64 |
| CORACLE | 75 | 0.787 | 0.736 | 0.59 |
| CSHUF | 75 | 0.787 | 0.840 | 0.61 |
| OR-TOP10 | 10 | 0.533 | 0.670 | 0.85 |
| OR-TOP10-SHUF | 10 | 0.533 | 0.533 | 0.62 |
| OR-TOP5 | 5 | 0.373 | 0.562 | 0.72 |
| OR-TOP5-SHUF | 5 | 0.373 | **0.943** | 0.55 |

Readings:
- **Matching alone separates.** A flat quota has no concentration at all, yet it is still separable
  from random (d 0.52) and lower-rank (0.855). Selecting the renders closest to each centroid is
  itself enough.
- **Concentration does not set rank.** The two 5-cluster allocations sit at opposite ends of the
  rank range (0.562 and 0.943), depending on *which* clusters they fund. This matches the analytic
  constructions in TH-01 §5.
- **Aim at a fixed shape is not consistent in sign.** At the C10 shape, true-error aim (CORACLE, 0.59)
  separates *less* than a shuffle (CSHUF, 0.61). At the top-10 shape, true-error aim separates more
  (0.85 against 0.62). These are geometric facts about the selected sets, and **none is evidence
  about detector accuracy.**

## 5. Effect on the paper and on CW-01

The reviewer's premise ("any non-uniform allocation is separable from a uniform draw with lower
effective rank") is half right on this pool and wrong in general:
- separability from a random draw is near-universal for *matched* selections, flat ones included;
- lower effective rank is neither implied by concentration (TH-01 constructions) nor observed for
  every concentrated selection (OR-TOP5-SHUF).

The paper's own sentence "the probe was detecting the concentration the whole time" needs the same
correction (AN-01 C-04). The finding that survives intact is the one the paper turns on: the score's
direction adds nothing measurable beyond a same-shape shuffle, +0.0073 d.

No figure was produced. The table above carries the comparison, and a figure would add no number not
already in `AN-02_shape_geometry.csv`.

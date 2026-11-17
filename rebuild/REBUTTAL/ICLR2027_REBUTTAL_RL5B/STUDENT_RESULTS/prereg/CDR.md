# CDR: concentration dose-response (pre-registration)

**Status.** This file is committed before the first CDR run, together with its analysis script
`analysis/cdr_analysis.py` and the allocation manifest. It is never edited after any CDR number exists;
amendments are appended, with their date, below the line at the end. It is part of the response to
Reviewer RL5B, CW-02 / QA-02 (task EXP-02).

**Inputs fixed before writing.**
- `RESULT_TABLES/TH02_identification.md` and `TH02_summary.json`: τ_H and the concentration indices.
- `rebuild/ABC/cdr_allocate.py`: the permutation-acceptance rule, committed in `138ad30` before the draw.
- `rebuild/ABC/out/cdr/cdr_permutations.json` and `cdr_allocations.csv`: the drawn allocations.
- `rebuild/ABC/out/cdr/abc_preflight.json` and `rebuild/ABC/out/cdr_lu/abc_preflight.json`: gates 6/6.

## CDR.0 Question

The submitted paper shows that concentrating the budget changes the training-set distribution, and
that the direction of the allocation has no detectable effect on accuracy. It does not show that
concentration itself changes accuracy (TH-02, Sections 3–4). The only available estimate, shuffled
versus random, rests on one permutation. CDR varies concentration at a fixed budget and averages
direction out over several independent random permutations, so that the shape effect can be estimated.

## CDR.1 Hypotheses

- **H2.** Mean Boundary-IoU (threshold 0.5) on SINet·COD10K-test differs between the concentrated
  levels (L1, LH) and the dispersed references (B, LU).
- **Exploratory.** The difference grows monotonically with concentration (LU/B < L1 < LH, or the
  reverse). This decides nothing.

## CDR.2 Design

The budget is N = 1000 throughout. All levels use the committed target scores e_j, k = 75 clusters,
the committed fill rule and the committed base pool.

| Level | Allocation | Direction | Allocations | Seeds | New runs per architecture |
|---|---|---|---|---|---|
| LU | cluster-uniform quotas (14 × 25 + 13 × 50) | none | 1 (`CDRLU`) | 42, 43, 45, 46, 47 | 5 |
| L1 | softmax at τ = 1.0: the committed shape q\*, N_eff 29.86 | random | 5 (`CDRL1P1`–`P5`) | 42, 43, 45 | 15 |
| LH | softmax at **τ_H = 0.758**: N_eff 14.91, ratio 0.499 to q\* | random | 5 (`CDRLHP1`–`P5`) | 42, 43, 45 | 15 |
| ref | B (SE seeds 42–50); CSHUF (= L1 P0), C10, CINV (seeds 42, 43, 45) | existing | — | — | 0 (re-scored, not retrained) |

**τ_H.** It was fixed by the TH-02 rule before any draw: the τ on a 0.001 grid whose realised integer
quotas give N_eff closest to half of N_eff(q\*).

**Permutations.** They were drawn by the committed rule in `cdr_allocate.py`:
- one `default_rng(2027)` stream;
- zero fixed points;
- |ρ| ≤ 0.10;
- Jaccard to the C10 set ≤ 0.35;
- Jaccard ≤ 0.50 to every set already accepted, with CSHUF counted as L1's P0, and to LU;
- at LH, Jaccard ≤ 0.50 to every L1 set as well.

L1 needed candidates 0–1058 (acceptance rate 0.0047); LH needed candidates 1059–1089 (0.161). No
relaxation step was needed. The global set-distinctness gate passed, with a maximum pair Jaccard of
0.4948.

**Concentration is weaker than the quotas suggest.** Measured by where the selected images actually
fall (nearest centroid), N_eff is:

| Allocation | N_eff (induced) |
|---|---|
| L1 sets | 40.4–48.4 |
| LH sets | 37.3–46.1 |
| LU | 50.3 |
| random B (mean over 8 seeds) | 42.5 |

(Sources: `cdr_allocations.csv`, `TH02_concentration_indices.csv`.) The manipulated variable is the
nominal level. The induced value is recorded per allocation and reported. A small or null difference
must be read in that light.

**Fill quality.** It is recorded per allocation: mean, 90th percentile and maximum cutout-to-centroid
cosine distance. Mean fill distance is 0.80 for LU, 0.78–0.87 for L1 and 0.83–0.88 for LH.
Concentration and match quality are therefore partly confounded, and that is reported.

**Training.** Training is identical to the committed campaigns: `MyTrain.py --method ours --iteration 2`,
steps pinned at 253 (SINet) and 127 (SINet-v2), checkpoint `Tea_epoch_best` by CAMO-250 MAE, inference
`MyTest.py`, and the footprint flags `--save_ckpts minimal --link_pool` (EQ.2).

**Architectures.**
- **SINet** (P0, 35 runs) is never sacrificed.
- **SINet-v2** (P1, 35 runs) is the replication, run after the EQ SINet campaign. If, at the 2026-11-12
  or 2026-11-14 checkpoint, it is projected not to finish all 35 runs by 2026-11-16 06:00 IST, it is
  dropped **whole**, never left partly run. That decision is recorded in `EXECUTION_STATUS.md` before
  it is acted on.

## CDR.3 Metrics

- **Primary metric.** Boundary-IoU at binarisation threshold 0.5: band width max(1, round(0.02 × image
  diagonal)), per-run mean over the 2026 COD10K-test images. It is computed by `analysis/boundary_scorer.py`,
  which imports the manuscript's own `metrics_one` from `rebuild/DIAG/diag_boundary.py`. That scorer
  must first pass the AN-01 reproduction gate: it re-derives the committed `tab:boundary` per-run tables
  exactly.
- **Primary cell.** SINet·COD10K-test.
- **Secondary.**
  - S_α under the manuscript's 2σ̂ rule (σ̂ as in CDR.4);
  - Boundary-F;
  - Boundary-IoU at thresholds 0.4 and 0.6;
  - E_φ (mean), F_β^w, MAE;
  - NC4K;
  - SINet-v2 as replication, with the same analysis.

## CDR.4 Primary analysis (implemented in `analysis/cdr_analysis.py`, committed with this file)

Notation: ā_{L,k} is the mean Boundary-IoU over the seeds of allocation k at level L.

1. **Dispersed reference.** D = ½(mean_B + mean_LU). mean_B is the mean over B's eight SE seeds 42–50;
   each B seed is its own random allocation. mean_LU is the mean over LU's five seeds.
2. **Level differences.** Δ_L = mean_{k=1..5} ā_{L,k} − D, for L ∈ {L1, LH}. The pooled concentrated
   contrast is Δ_C = (mean of the 10 concentrated allocation means) − D.
3. **Noise estimate.** σ̂ is the within-allocation SD of per-run Boundary-IoU, pooled over LU and the ten
   L1/LH allocations (df = 4 + 10 + 10 = 24). B is excluded, because its eight seeds are eight different sets.
4. **Decision rule, per level L.**
   - (a) |Δ_L| > 2σ̂.
   - (b) At least 4 of the 5 permutations at L have sign(ā_{L,k} − D) = sign(Δ_L).
   - (c) The between-permutation SD at L (the SD of the five allocation means) is smaller than |Δ_L|.

| Condition | Conclusion |
|---|---|
| (a), (b) and (c) hold at L1 or at LH, and where both levels pass, their signs agree | **concentration effect supported downstream (SINet)** |
| (a) fails at both levels | **not supported** |
| any other combination, including both levels passing with opposite signs | **inconclusive** |

SINet-v2 is judged by the same rule. The paper may say "consistent across architectures" only if both
architectures are "supported" with the same sign.
5. **Reported, deciding nothing.**
   - A Welch 95% CI over units: the 10 concentrated allocation means against the 9 dispersed units
     (LU's mean and the 8 B runs).
   - Δ_C.
   - The between-permutation SD at each level.
   - The mixed model BIoU ~ level + (1 | allocation) + (1 | seed): statsmodels MixedLM with
     groups = allocation and seed as a variance component.
   - The dose-response figure: BIoU against nominal N_eff, one point per allocation, error bars = seed
     SD, with a second panel against induced N_eff.
   - An exploratory model adding the fill distance and the pseudo-label count as covariates. Both are
     post-treatment.
   - A sensitivity analysis that adds CSHUF as L1's P0 (seeds 42, 43, 45).
   - The same-shape references C10 and CINV as context.
6. **Monotonicity (exploratory).** The ordering of D, the L1 mean and the LH mean is reported.

## CDR.5 Stopping and failures

- All runs complete, with no interim looks at endpoint metrics. The queue trains and runs inference;
  `cdr_analysis.py` runs once per architecture, after that architecture's 35 runs have verified.
- A failed run is re-run from scratch with the same seed and never replaced.
- An allocation that cannot complete its seeds by the cutoff is reported as incomplete, never silently
  dropped.

## CDR.6 Sentences fixed in advance

- **Supported:** "In a pre-registered dose-response experiment, concentrating the budget changed
  boundary accuracy consistently across independent random permutations (Δ = {Δ_L} against a bar of
  {2σ̂}); concentration is supported as a downstream explanation on SINet{ and SINet-v2}."
- **Not supported:** "The pre-registered dose-response experiment did not support a downstream
  concentration effect (largest level difference {Δ_L}, bar {2σ̂}); we therefore restrict the
  concentration claim to the training-set distribution."
- **Inconclusive:** "The pre-registered dose-response experiment was inconclusive ({reason}); concentration
  remains a hypothesis about downstream accuracy."

## CDR.7 Limitations, stated before the result

- Concentration is partly confounded with fill quality.
- There are only 3 seeds per permutation.
- The low-overlap constraint is selective at L1 (acceptance rate 0.0047), so the accepted permutations may
  be unusual.
- The realised spread of images over clusters differs far less between levels than the quotas do.
- The B references were trained in September with the same code. The bridge re-train checks that this
  code still reproduces a committed run.
- Boundary metrics depend on binarisation; the 0.4/0.6 thresholds are reported.

---
*Amendments (dated, append-only) go below this line.*

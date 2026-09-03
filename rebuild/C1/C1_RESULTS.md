# C1 — Verified results

**Status: COMPLETE. 6 of 7 thresholds PASS; 1 FAIL.**

**VERDICT: REOPENS — in all four (embedder × representation) cells. The old package's
`d ≈ 0.10` is REFUTED.**

Source: `results/REBUILD_LOG.txt`, the **third** `EXP C1` block. Block 1 → 2 added the
`C2_SHAPE_DIVERGENCE` cross-check my own plan (§3.1) specified and my first implementation omitted;
block 2 → 3 added the `B = 1000` metrics this document quotes.
Setup: `rebuild/C1/C1.md`. Specification: `rebuild/C1/C1_PLAN.md`, approved before any C1 code existed.
**Trains a model: NO.**

---

## 1. The headline

All six Phase-0 gates passed (`preflight_gates_passed = 6/6`) before a single array was loaded.

| Space × representation | peak `d_heldout` | `ci_combined` | verdict |
|---|---|---|---|
| dinoL224 × R2 cutout | **+1.2325** | [**+0.7700**, **+1.6422**] | **REOPENS** |
| dinoL224 × R3 render | **+1.0795** | [**+0.7959**, **+1.3902**] | **REOPENS** |
| dinoL518 × R2 cutout | **+1.1135** | [**+0.7626**, **+1.4953**] | **REOPENS** |
| dinoL518 × R3 render | **+1.0028** | [**+0.6612**, **+1.3301**] | **REOPENS** |

Every CI lies **entirely inside** the REOPENS band — amendment A1's threshold PASSES, so no verdict is
suppressed as `INCONCLUSIVE-CI-STRADDLES`. Both embedder spaces agree (threshold PASS), so the result
is not embedder-dependent.

**By the threshold declared before running — `d ≥ 0.5` → the verdict reopens — the targeted and random
arms are NOT materially identical in embedding space.**

## 2. Against the old claim

| Old claim | Old value | Measured | Verdict |
|---|---|---|---|
| C1.1 Cohen's *d* targeted-vs-random | `≈ 0.10` `[no code]` | **+1.0028** to **+1.2325** at peak | **MISMATCH — refuted, ~10×** |
| C1.1 at the old package's own budget `B = 1000` | `≈ 0.10` | **+0.6547** to **+0.8298** | **MISMATCH — 7–8×** |
| C1.3 clusters funded | `1–49` | 4 to 50 at the peaks | overlaps; not a point value |

At the budget the old package actually proposed, `B = 1000`, and over **non-degenerate** cells only:

| Space × representation | `d_heldout` | `ci_combined` | band |
|---|---|---|---|
| dinoL518 × R2 | **+0.7973** | [**+0.6156**, **+0.9675**] | REOPENS |
| dinoL518 × R3 | **+0.6547** | [**+0.4615**, **+0.8325**] | REOPENS |
| dinoL224 × R2 | **+0.8298** | [**+0.6594**, **+1.0176**] | REOPENS |
| dinoL224 × R3 | **+0.6947** | [**+0.5134**, **+0.8852**] | REOPENS |

All four exceed 0.5. (An ad-hoc scan of the cell CSV during analysis gave a higher top figure by
including allocations that fund a single cluster; the logged metric excludes those under the
degeneracy guard, and the guarded values above are the ones that stand.)

`d ≈ 0.10` had no producing script and no log block. It is now measured, and it is wrong by roughly an
order of magnitude.

## 3. The B-curve, and why the peak sits where it does

`d_heldout` is **monotone decreasing** in budget (dinoL518, R2, max over α):

| B | max \|d\| | clusters funded | max alloc share |
|---|---|---|---|
| 250 | +1.172 | 1 | 1.00 |
| 500 | +0.930 | 25 | 0.51 |
| 1000 | +0.797 | 40 | 0.51 |
| 2000 | +0.476 | 4 | 0.82 |
| 3000 | +0.244 | 2 | 1.00 |
| **4447** | **−0.347** | 1 | 1.00 |

This is the expected geometry: targeting concentrates a small budget near a few centroids, while a
random draw spreads; as the budget approaches the pool both arms converge on the same 4447 images.

Across all 264 cells: **137 REOPENS, 104 AMBIGUOUS, 23 CONFIRMED**. Excluding the trivial ceiling,
137 / 60 / 23. The REOPENS band is not an artifact of one corner of the sweep.

**Sweep coverage is complete**: both degenerate ends were reached in both spaces (`max p = 1.0000` at
α = 0.02; `TV = 0.00903` / `0.00988` at α = 40), so the temperature axis was not truncated.

## 4. The null calibration — a finding the ceiling assertion produced

At `B = 4447` both arms are the entire pool, so the true difference is exactly zero.
`norm_dmean_at_pool_ceiling = 0` — asserted and PASSED.

But `d_heldout` there is **−0.3241** (sd **0.0166** over 44 cells), while `d_insample` is **+0.0000**.

My ceiling assertion originally required *both* to vanish and it fired. That was not a bug in the
measurement: with no real difference, the direction fitted on halves A₁/R₁ is pure split noise, and the
disjoint evaluation halves A₂/R₂ are **anti-correlated** with it, so the held-out estimator returns a
negative value. It is now reported as a **calibration**: the estimator's offset under a known-zero
difference is **negative**, i.e. **conservative**. A measured +1.1 is not merely above zero, it is
~1.4 above what the estimator returns when the answer is known to be nothing.

Declared threshold "peak |d| exceeds the null calibration magnitude" — **PASS**.

## 5. Amendment A2 FAILED, and what it means

`cells_ORDER_SENSITIVE = 87` of 264; `max_d_order_spread = 0.18002`. Two of the four peak cells are
flagged. Per the plan, all five order families are reported rather than the primary alone:

| Peak cell | spread | desc_nc | asc_nc | asc_index | desc_es | shuffled |
|---|---|---|---|---|---|---|
| dinoL224 R2 | **0.1800** | +1.299 | +1.193 | +1.119 | +1.304 | +1.245 ± 0.037 |
| dinoL224 R3 | 0.0603 | +1.095 | +1.101 | +1.121 | +1.095 | +1.103 ± 0.032 |
| dinoL518 R2 | 0.0000 | +1.183 | +1.183 | +1.183 | +1.183 | +1.183 ± 0.000 |
| dinoL518 R3 | 0.0240 | +0.997 | +0.988 | +1.003 | +0.997 | +0.996 ± 0.014 |

**The point estimate is order-sensitive; the verdict is not.** Every serving order in every peak cell
returns `d ≥ 1.1`, far inside REOPENS. So the de-duplication rule moves the number by up to 0.18 but
cannot move the band. That distinction is exactly what amendment A2 was added to expose, and it is
reported rather than averaged away. Jaccard overlap against the primary selection ranges 0.748–1.000.

## 6. `C2_SHAPE_DIVERGENCE` — flagged, and a correction to my own plan

`C2_measured_argmax_B = 250` in all four cells, against `C2_predicted_peak_B = 2000`. The flag is
**True**, as the plan required.

**But the plan's cross-check was a category error, and that is recorded rather than quietly dropped.**
C2's pool-shift curve `(B/|Ds|)·(1 − B/4447)` measures how much the *training pool composition* changes
— zero when nothing is added, zero again when both arms add everything, hence concave with an interior
peak. C1's *d* measures how far apart the two *selected sets* are — largest when the budget is small
enough for targeting to stay concentrated, falling to zero as both arms converge on the pool. The two
curves *should* have different shapes. This is **not** evidence of a contradiction between experiments.

C2 remains **UNRUN** (0 `EXP C2` blocks), and `|Ds|` remains **UNVERIFIED**, so nothing here confirms
or refutes C2.

---

## 7. What this changes

### 7.1 One leg of the "Stage C is not viable" argument does not hold

- **Standing claim:** targeted and random arms see nearly identical data (`d ≈ 0.10`), so no accuracy
  gain is possible.
- **Measured:** `d` = 1.00–1.23 at peak, 0.65–0.83 at `B = 1000`, in both embedder spaces and both
  representations, with CIs entirely in the REOPENS band and a conservative estimator.
- **Revised position:** **that leg fails.** The two arms are substantially separated in embedding
  space. Any argument that Stage C cannot work *because the arms are identical* is not supported by
  measurement.
- **What this does NOT establish:** that Stage C works. C1 measures a distance between selected image
  sets. It does not measure accuracy, and it does not touch the other legs of the argument — A1's
  48-scalar conditioning bottleneck, D1's foreground exhaustion, B1's finding that the allocation
  signal is only a moderate predictor of endpoint error, or C3's noise floor. Those are separate and
  remain as they were.

### 7.2 The limitation that most constrains this result

Logged unconditionally, per the plan:

> Cohen's *d* is a **mean-shift** measure along a **single, fitted** direction. In a 1024-dimensional
> space, any structured subset will separate from a random one along *some* direction. A large *d*
> establishes that such a direction exists and that the separation along it is large; it does **not**
> establish that the two sets differ in a way that would change training.

The follow-up variance/coverage comparison was **not triggered**, because the declared rule fires on
AMBIGUOUS or a straddling CI, and this result is neither. **I am flagging it as the most valuable next
measurement anyway**: it would say whether the arms differ in spread and coverage or only in centre,
which is what determines whether a distance this large could plausibly move a trained model.

### 7.3 The measurement was self-corrected twice, both before the authoritative block

- The **ceiling assertion fired** and turned into §4's null calibration rather than being relaxed.
- The **plan's own C2 cross-check was unimplemented** in the first run; block 1 → 2 added it, and
  implementing it exposed that the comparison was a category error (§6).

---

## 8. What C1 does not establish

- **That targeting improves accuracy.** C1 measures set separation, not model performance.
- **That the separation is trainingly meaningful.** See §7.2 — direction-fitted mean shift only.
- **Anything about C2 or `|Ds|`.** C2 is unrun; the shape comparison was against an analytic design and
  was, on inspection, comparing different quantities.
- **Seed robustness of the allocation signal** — `UNVERIFIED-DEFERRED`; one checkpoint pair per model.
- **Anything in `clipL224`** — disqualified at Gate 3 and not measured.
- **Selection by R3.** Out of scope: renders do not exist at selection time. *d* is measured in R3, but
  selection is always by R2.
- **A finer B grid below 250.** `d` is still rising as B falls; the true maximum may lie below the
  smallest budget swept.

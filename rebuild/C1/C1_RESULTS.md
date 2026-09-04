# C1 — Verified results

**Status: COMPLETE, then AUDITED. Measurement: 6 of 7 thresholds PASS. Attribution audit
(§8): 2 of 7 PASS, 5 FAIL.**

**VERDICT: `d ≈ 0.10` is REFUTED — the arms are separated by `d` ≈ 1.0–1.23, not 0.10.
But §8's audit shows that separation is NOT attributable to the ES signal.** Destroying the
targeting information while keeping the allocation *shape* reproduces the same `d`. The
honest verdict is therefore **REOPENS-BUT-NOT-BY-TARGETING**: the old number is wrong, and
the conclusion it was used to license is still unavailable.

Source: `results/REBUILD_LOG.txt`, `EXP C1` blocks **3** (measurement) and **4** (audit).
Block 1 → 2 added the `C2_SHAPE_DIVERGENCE` cross-check my own plan (§3.1) specified and my
first implementation omitted; block 2 → 3 added the `B = 1000` metrics this document quotes;
block 4 is the §8 audit.
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

> **Read §8 before using any number in this table.** These values are correct as measured, and
> they refute `d ≈ 0.10`. They do **not** mean what the threshold was designed to test. The audit
> shows an arm built by permuting the ES values across clusters — i.e. with the weakness signal
> destroyed — scores `+0.9139` to `+1.1403` in the same cells. The quantity these numbers measure
> is **concentration**, not **targeting**.

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

### 7.1 The "arms are identical" leg fails — but not in the way the number suggests

- **Standing claim:** targeted and random arms see nearly identical data (`d ≈ 0.10`), so no accuracy
  gain is possible.
- **Measured:** `d` = 1.00–1.23 at peak, 0.65–0.83 at `B = 1000`, both embedder spaces, both
  representations, CIs entirely in the REOPENS band.
- **Revised position, after §8:** the *number* `0.10` is refuted, and the arms are genuinely
  near-disjoint sets (they overlap at exactly the chance rate — §8.4). But **`d` at this magnitude is
  what any concentrated selection produces against a dispersed one.** It is not evidence that
  ES-targeting selects distinctive data, because arms with the ES signal destroyed score the same.
- So the leg fails **as stated** — one cannot claim the arms are identical. It does **not** convert
  into support for Stage C, because the separation is not attributable to the mechanism Stage C
  depends on.

### 7.2 The limitation named in §7.2 of the pre-audit draft was the decisive one

The plan committed, unconditionally, to logging this:

> Cohen's *d* is a **mean-shift** measure along a **single, fitted** direction. In a 1024-dimensional
> space, any structured subset will separate from a random one along *some* direction.

The pre-audit draft flagged the follow-up as "the most valuable next measurement" even though the
declared trigger had not fired. **Running it changed the verdict.** That sentence was not a formality
— it named the exact failure mode that the audit then confirmed. This is the clearest case in the
rebuild so far for logging limitations unconditionally rather than only when a threshold forces it.

### 7.3 The measurement was self-corrected three times

- The **ceiling assertion fired** and turned into §4's null calibration rather than being relaxed.
- The **plan's own C2 cross-check was unimplemented** in the first run; block 1 → 2 added it, and
  implementing it exposed that the comparison was a category error (§6).
- The **headline was audited after it passed**, not only after it failed, and the audit overturned its
  interpretation (§8).

---

## 8. The attribution audit — the ES signal is not what produces `d ≈ 1.0`

Fourth `EXP C1` block. Script: `rebuild/C1/c1_variance_coverage.py`. Artifacts:
`out/c1_attribution.csv`, `c1_spread.csv`, `c1_coverage.csv`, `c1_occupancy.csv`.

### 8.1 The control arms

Every arm below has the **same budget `B`, the same 4447-image pool, the same embedding space, and the
same held-out estimator** as the targeted arm. Only the selection rule differs. `d_heldout`, mean over
20 draws, at each cell's peak `B = 250`:

| arm | what it destroys | dinoL518 R2 | dinoL518 R3 | dinoL224 R2 | dinoL224 R3 |
|---|---|---|---|---|---|
| **targeted by `target_es`** | *(nothing — the real arm)* | **+1.1135** | **+1.0028** | **+1.2325** | **+1.0795** |
| `shuffled_es` | ES values permuted across clusters; allocation **shape kept** | **+1.1304** | **+0.9139** | **+1.1940** | **+1.1403** |
| `random_centroid` | whole budget to an **arbitrary** cluster | **+1.2262** | **+1.0534** | **+1.4243** | **+1.1908** |
| `random_direction` | `B` extremes along a **random** unit vector | **+1.1245** | **+0.9332** | **+1.1433** | **+0.8867** |
| `random_vs_random` | everything — two independent draws | **−0.0373** | **−0.0109** | **−0.0330** | **−0.0115** |

Every arm that keeps *concentration* but discards *targeting* reproduces the headline.

### 8.2 Paired increments — the decisive numbers

Paired per (tag, representation, `B`) across all **20 cells**, so no comparison is between different
budgets:

| comparison | mean | sd | range | ES wins |
|---|---|---|---|---|
| targeted − `shuffled_es` | **+0.0073** | 0.0560 | −0.1372 … +0.0889 | **13/20** |
| targeted − `random_centroid` | **−0.0649** | 0.0756 | −0.1993 … +0.0386 | **4/20** |
| targeted − `random_direction` | **+0.0479** | 0.0531 | −0.0683 … +0.1929 | **18/20** |

- Against its own shuffle, the ES signal contributes **+0.007** — 0.6% of a `d` of 1.1 — and wins
  13/20, indistinguishable from a coin flip.
- Against an **arbitrary** cluster it is **negative**: targeting the highest-ES cluster is *worse*
  than picking a cluster at random, in 16 of 20 cells.
- The one consistent edge is over a random *direction*: **+0.048**, winning **18/20**. The sign is
  reliable; the magnitude is ~5% of the effect. The correct statement is that the ES signal's
  contribution is **detectable but negligible**, not that it is zero.

### 8.3 Cross-check against the original run's own ceiling

`C1_PLAN.md` §2.4 defined `d_max_possible` as "entire budget to the single highest-`target_es`
cluster" — the bound on what targeting could *ever* achieve. The audit's `random_centroid` arm is that
same construction with an **arbitrary** cluster. Comparing the two artifacts, produced by different
scripts in different runs:

```
CEILING_top_ES_cluster_MINUS_random_cluster = mean +0.0077 | range -0.1007 .. +0.1144 | top-ES wins 10/20
```

**C1's declared ceiling is not a targeting ceiling; it is a concentration ceiling.** Ten wins out of
twenty is an exact coin flip. The highest-ES cluster is not a better place to spend the budget than
any other cluster.

### 8.4 What the arms *do* differ in — spread, coverage, occupancy

At `B = 1000`, targeted vs random:

| | dinoL518 R2 | dinoL518 R3 | dinoL224 R2 | dinoL224 R3 |
|---|---|---|---|---|
| trace-of-covariance ratio | 0.9887 | 0.9819 | 0.9851 | 0.9945 |
| **effective rank ratio** | **0.574** | **0.640** | **0.600** | **0.538** |
| target-manifold coverage Δ | −0.0030 | −0.0210 | −0.0010 | +0.0120 |
| **mean top-1 similarity Δ** | **+0.0056** | **+0.0530** | **+0.0936** | **+0.0958** |
| clusters touched | 67/75 vs 74 | 67/75 vs 74 | 49/50 vs 47 | 46/50 vs 47 |
| overlap vs chance | 1.045 | 0.992 | 0.943 | 0.987 |

Four readings, in order of how much they matter:

1. **The arms are genuinely different sets.** Overlap sits at the chance rate (0.94–1.05), so the
   `d` is not an artifact of the two arms sharing images.
2. **The targeted arm is narrower in the way that counts.** Trace barely moves (1–2%) because a
   1024-d embedding's trace is dominated by its isotropic bulk. Effective rank — the participation
   ratio of the covariance spectrum — drops to **0.53–0.64**: the targeted arm spans roughly **half
   the effective dimensionality**, in **20/20 cells** (mean ratio 0.634).
3. **It buys average proximity, not coverage.** Mean top-1 similarity to the target manifold rises by
   up to **+0.096**, while the fraction of the target manifold actually served changes by ≈ 0
   (−0.021 to +0.012; the targeted arm covers *less* in 10/20 cells).
4. **A declared threshold was wrong and is reported as FAILED.** The spread criterion was declared on
   the trace ratio, which fails at 1–2%. Effective rank agrees with the conclusion, and is reported
   **as an observation, not promoted to a threshold**, because swapping in the metric that agrees
   after seeing the data is exactly the move this rebuild exists to prevent.

### 8.5 The two thresholds that PASS are load-bearing

| threshold | result | why it matters |
|---|---|---|
| random-vs-random null is small (`|d| < 0.3`) | **PASS** — `−0.1328` (range −0.2560 … −0.0109) | the held-out estimator does **not** manufacture an effect from sampling noise. Without this, every number above would be suspect |
| the in-sample estimator would have been unusable (null > 0.5) | **PASS** — `+0.6991` (range +0.2144 … **+1.4506**) | with **no targeting at all**, the in-sample `d` reaches **+1.45** — larger than C1's headline. Had `d_insample` been the headline, the entire REOPENS verdict would have been an artefact of fitting the direction to the noise it then measures |

The second row is the single strongest justification in the rebuild for the held-out choice, and it is
a **measurement**, not an argument.

### 8.6 A mechanism consistent with the Stage C null

This is a **hypothesis the audit makes available**, not something it demonstrates:

> Targeting produces a set that is **more proximal to the target manifold on average** but spans
> **half the effective dimensionality** and covers **no more** of that manifold. If training benefits
> more from coverage and diversity than from average proximity, a large `d` is entirely compatible
> with zero accuracy gain.

That would reconcile C1's REOPENS with the Stage C null without either being wrong. **C3 is the
experiment that can test it; C1 cannot.**

### 8.7 Provenance of the added metrics — stated because it matters

`c1_variance_coverage.py` was first run with `--no-log` (exploratory, nothing written). The four null
arms and the `random_vs_random` / in-sample thresholds were declared **before** that pass. The
`ES_SIGNAL_INCREMENT_*` metrics, their two thresholds, and the §8.3 ceiling cross-check were added
**after** seeing it.

They are **tightenings**: each makes the audit harder to pass, none was chosen to rescue a failing
criterion, and no declared threshold was weakened or removed — the five failures stand. Their content
was already implied by the pre-declared `SHUFFLED_ES_minus_NULL_max = +1.2270` metric; what changed is
that they pair (tag, repr, `B`) exactly instead of comparing a max over cells against a min over
cells, which was unfair in both directions. This paragraph is also in the log block's `NOTES`.

---

## 9. What C1 does not establish

- **That targeting improves accuracy.** C1 measures set separation, not model performance.
- **That the separation is caused by targeting.** §8 shows it is not — it is caused by concentration,
  which is available with no weakness signal at all.
- **That the ES signal is worthless.** Its measured contribution is small and positive against a
  random direction (+0.048, 18/20) and null-to-negative against every structured control. "Negligible
  in this geometry" is supported; "zero" and "harmful" are not.
- **That a lower-rank, more-proximal arm trains worse.** §8.6 is a hypothesis for C3, not a result.
- **Anything about C2 or `|Ds|`.** C2 is unrun; the shape comparison was against an analytic design and
  was, on inspection, comparing different quantities.
- **Seed robustness of the allocation signal** — `UNVERIFIED-DEFERRED`; one checkpoint pair per model.
- **Anything in `clipL224`** — disqualified at Gate 3 and not measured.
- **Selection by R3.** Out of scope: renders do not exist at selection time. *d* is measured in R3, but
  selection is always by R2.
- **A finer B grid below 250.** `d` is still rising as B falls; the true maximum may lie below the
  smallest budget swept — and by §8 that maximum would be a concentration effect too.

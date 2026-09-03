# C1_PLAN.md — the decisive measurement, planned before any code

> **APPROVED 2026-09-02, with amendments A1 and A2 (§8).** This is the specification the C1 scripts
> must satisfy; it was written and approved *before* any C1 code existed. **C1 trains nothing, ever.**

---

## Context

C1 is the load-bearing measurement of the whole rebuild: *how different is targeted training data
from random?* If the two arms see nearly identical data, no accuracy gain is possible and the Stage C
null is explained. The old package listed `d ≈ 0.10` with **no producing script and no log block** —
it was never computed.

**Ground rule.** `d ≈ 0.10` is an `OLD CLAIM` with a blank measured column. It appears in this plan
**only** in §6's comparison row. It is not a target, prior, expectation, or sanity-check anywhere in
the design, and no threshold below is positioned relative to it.

Every input named here was verified to exist, with its exact path, before this plan was written.

---

## 0. Verified inputs — exact paths

| Artifact | Path | Verified |
|---|---|---|
| Allocation signal + partition | `rebuild/B1/out/b1_cluster_es_dinoL518.csv` | 75 rows, `target_es` **75/75** populated, `n_target` sums **4033** |
| — sensitivity | `rebuild/B1/out/b1_cluster_es_dinoL224.csv` | 50 rows, **50/50**, sums 4033 |
| — disqualified | `rebuild/B1/out/b1_cluster_es_clipL224.csv` | 5 rows, **5/5**, sums 4033 |
| Centroids | `rebuild/B1/out/b1_centroids_{tag}_k{k}_seed0.npy` | (75,1024) / (50,1024) / (5,1024) |
| Partition provenance | `rebuild/B1/out/b1_cluster_assignment_{tag}.json` | `k`, `seed=0`, `embedder`, 4033 names + labels |
| **R2 cutout** (selection space) | `rebuild/E0/cache/{tag}_cut_cls.npy` | (4447, 1024) all three tags |
| **R3 render** (measurement space) | `rebuild/E0/cache/{tag}_local_cls.npy` | (4447, 1024) all three tags |
| Row order | `rebuild/E0/cache/{tag}_names.json` | `cut` stems **==** `local` stems **==** sorted raw pool; **identical across all 3 embedders** |
| Leakage | `rebuild/D2/out/d2_leaked_names.json` | `n_target_excluded = 7` |
| Input integrity | `rebuild/E0/out/e0_manifest.sha256` | 4.29 MB, 48 365 lines |
| Freshness gate | `rebuild/E0/e0_regenerate.py::step_independence()` | AST scan, already walks all of `rebuild/` |

**R2↔R3 row alignment is exact**, so one selection can be measured in both representations without a
name join.

### Files C1 will create

```
rebuild/C1/c1_preflight.py            # §1 — the six gates
rebuild/C1/c1_targeted_vs_random.py   # §2–§3 — the measurement
rebuild/C1/C1.md                      # setup doc, E0/D2/D1/B1 shape
rebuild/C1/C1_RESULTS.md              # written last
rebuild/C1/out/…                      # artifacts
```

---

## 1. Phase 0 — validation gates

All six run in `c1_preflight.py::main()`, each returning a dict appended to a list, all written to
`rebuild/C1/out/c1_preflight.json`.

### HALT semantics — exact control flow

```python
GATES = [gate_signal, gate_cluster_source, gate_embedder,
         gate_representation, gate_leakage, gate_freshness]

def run_preflight(tags) -> dict:
    report = {'gates': [], 'all_passed': None}
    for fn in GATES:
        r = fn(tags)                      # never raises for a data failure
        report['gates'].append(r)
    report['all_passed'] = all(g['passed'] for g in report['gates'])
    C.save_json(os.path.join(OUT, 'c1_preflight.json'), report)
    return report
```

and in `c1_targeted_vs_random.py::main()`, **before any measurement code runs**:

```python
report = c1_preflight.run_preflight(tags)
if not report['all_passed']:
    failed = [g['gate'] for g in report['gates'] if not g['passed']]
    raise SystemExit('C1 HALTED at preflight: %s -- see c1_preflight.json' % failed)
```

**HALT means `SystemExit` before the first array is loaded.** There is no fallback, no default, no
`try/except` that continues, and no `--force` flag. A failing gate is a defect to fix or a finding to
report, never something to proceed past. `c1_preflight.json` is written **even on failure**, so the
failure itself is an artifact.

### Gate 1 — signal (`target_es`, never `test_es`)

- **Opens:** `rebuild/B1/out/b1_cluster_es_{tag}.csv`
- **Assertions:**
  1. `'target_es' in reader.fieldnames`
  2. every row has `row['target_es'] not in ('', None)` → count must equal row count
  3. `sum(int(r['n_target']) for r in rows) == 4033`
  4. `float(r['target_es']) > 0` for every row (ES is a loss; zero would mean student≡teacher)
- **The single line that reads the signal**, and the only place `target_es` is read:
  ```python
  def load_allocation_signal(tag) -> tuple[np.ndarray, np.ndarray]:
      rows = sorted(csv.DictReader(open(cluster_es_path(tag))), key=lambda r: int(r['cluster']))
      es      = np.array([float(r['target_es']) for r in rows], dtype=np.float64)   # ALLOCATION SIGNAL
      n_tgt   = np.array([int(r['n_target'])   for r in rows], dtype=np.int64)
      return es, n_tgt
  ```
- **Negative assertion:** an AST scan of `rebuild/C1/*.py` asserts the string literal `'test_es'`
  appears **zero** times outside a `# provenance-ok`-style comment. Reading `test_es` anywhere in C1
  is a gate failure.
- **Pass/fail:** all four assertions true **and** zero `test_es` references → pass.

### Gate 2 — cluster source (consume B1's partition, never re-cluster)

- **Opens:** `b1_cluster_es_{tag}.csv`, `b1_cluster_assignment_{tag}.json`, `b1_centroids_{tag}_k{k}_seed0.npy`
- **Assertions:**
  1. `len(rows) == {'dinoL518': 75, 'dinoL224': 50, 'clipL224': 5}[tag]` — B1 completion II §D5
  2. `assignment['k'] == len(rows)` and `assignment['seed'] == 0` and `assignment['embedder'] == tag`
  3. `centroids.shape == (len(rows), 1024)`
  4. `len(assignment['target_names']) == len(assignment['target_labels']) == 4033`
  5. `set(assignment['target_labels']) ⊆ set(range(k))`
- **No-clustering assertion**, AST over every `rebuild/C1/*.py`:
  ```python
  banned_calls   = {'KMeans', 'MiniBatchKMeans', 'AgglomerativeClustering', 'DBSCAN', 'fit_kmeans'}
  banned_modules = {'sklearn.cluster'}
  ```
  fail if any `ast.Call` name, `ast.Import`, or `ast.ImportFrom` matches. **C1 never fits a
  partition; it only reads centroids and labels B1 committed.**

### Gate 3 — embedder discipline, and the §C2 cache-mixing bug

B1 §C2 found `fit_kmeans` keyed on `(k, seed)` and `endpoint_emb` on `split` alone — inert with one
embedder, silently corrupting with three. C1 prevents recurrence structurally:

- **Cache-key discipline (named):** *every* module-level cache in C1 is keyed by a tuple whose
  **first element is the embedder tag**, and no bare array is ever stored at module scope. The only
  loader is:
  ```python
  Space = collections.namedtuple('Space', 'tag k centroids cut render es n_target names')
  _SPACE_CACHE: dict[str, Space] = {}          # key IS the tag, by construction

  def load_space(tag: str) -> Space:
      if tag not in _SPACE_CACHE:
          _SPACE_CACHE[tag] = _build_space(tag)
      s = _SPACE_CACHE[tag]
      assert s.tag == tag, 'cache key/tag mismatch'      # cannot return another space
      return s
  ```
  Every downstream function takes a `Space`, never loose arrays, so a wrong-space value cannot be
  passed in. A gate assertion loads all tags and checks
  `load_space(t).tag == t and load_space(t).centroids.shape[0] == expected_k[t]` for each.
- **Role assertions:** `dinoL518` primary; `dinoL224` mandatory sensitivity; `clipL224`
  **disqualified** — carried only if `--include-disqualified` is passed, written to a separate
  `c1_disqualified_clipL224.json`, tagged `DISQUALIFIED-k5-degenerate` in every row, and **never**
  entering any headline metric, threshold, or the peak-of-B judgement.
- **Never averaged:** an assertion that no output row aggregates across `tag`; every result row
  carries its `tag` as a key column.

### Gate 4 — representation (pixel-level, not variable name)

The R2 cache must really be the grey-128 cutout, not a full scene or a render.

- **Opens:** `rebuild/E0/cache/{tag}_cut_cls.npy`, `{tag}_names.json`, plus the primary images
  `Dataset/Source/HKU-IS_raw/{imgs,gt}` via `common.load_cutout`.
- **Alignment assertion (exact):**
  ```python
  cut_stems  = [os.path.splitext(n)[0] for n in names['cut']]
  rend_stems = [os.path.splitext(n)[0].replace('SOD_', '', 1) for n in names['local']]
  raw_stems  = sorted(os.path.splitext(f)[0] for f in C.listing('raw'))
  assert cut_stems == raw_stems == rend_stems          # row i is the same foreground in R2 and R3
  assert cut.shape[0] == render.shape[0] == 4447
  ```
- **Pixel-level identity check** (the part a variable name cannot satisfy), on `n=4` rows drawn with
  `np.random.default_rng(0)`:
  1. Rebuild the cutout for that stem with `common.load_cutout(img, mask)` — the committed R2 loader.
  2. Assert directly on those pixels: `np.unique(a[gt < 127]) == [128]` and
     `np.array_equal(a[gt >= 127], raw_rgb[gt >= 127])` — background is the flat constant **128**,
     object untouched.
  3. Re-embed with `common.build_model(tag)` + `common.embed(..., loader=lambda t: C.load_cutout(*t))`
     and assert `cosine(fresh_i, cut_cache[i]) >= 0.999`.
  4. **Discriminative negative control:** re-embed the same stems as the *full raw scene* and as the
     *render*, and assert both give a **lower** cosine to `cut_cache[i]` than the cutout does. Without
     this, a cache of full scenes could pass step 3 by accident.
- **Pass/fail:** all four true for all sampled rows.

### Gate 5 — leakage

The 7 leaked names are **COD10K target-domain images**; the 4447 HKU-IS foreground pool is a
different set. So leakage enters C1 on the **allocation** side, not the selection side:

- **Assertion A (allocation side, inherited from B1):**
  `sum(n_target) == 4033` and `len(assignment['target_names']) == 4033`, i.e. B1 already excluded
  them. Additionally assert `set(json.load(D2)['target_names_to_exclude']) & set(assignment['target_names']) == set()`.
- **Assertion B (selection side, cited to D2):** the cutout pool shares no image with any endpoint.
  D2 measured `endpoint_INTERSECT_HKUIS_pools = 0`. C1 re-asserts by reading that value out of
  `rebuild/D2/out/d2_pair_matrix.csv` and requiring `collisions == 0` for every
  (endpoint × {raw, auth, local}) pair, rather than restating the number.
- **Pass/fail:** both assertions true; the 7 names are logged verbatim in `c1_preflight.json`.

### Gate 6 — freshness

- **No archive / scratchpad:** import and call `e0_regenerate.step_independence()` — it already walks
  all of `rebuild/`, so it scans C1 automatically. Require `n_forbidden == 0`. Reusing E0's definition
  rather than writing a second one means C1 cannot drift from the gate E0 self-tested.
- **Manifest resolution:** the `.npy` caches are *derived*, so C1 verifies the **primary inputs that
  produced them**. Parse `rebuild/E0/out/e0_manifest.sha256` and re-hash a `rng(0)` sample of
  **100 files** across `raw`, `raw_gt`, `tgt`, `local`, asserting each equals its manifest entry
  (same pattern as `d1_foreground_exhaustion.py::step_verify`). Any mismatch → fail.
- **Pass/fail:** `n_forbidden == 0` **and** 100/100 hashes match.

---

## 2. Phase 1 — the measurement design

### 2.1 Targeted arm

**Allocation.** Temperature-softmax over the per-cluster allocation signal, with `T` expressed
scale-free so it is comparable across embedders (which differ in `k` and hence in the spread of
`target_es`):

```
T      = alpha * sd(es)                       # sd over the k cluster values
w_c    = exp((es_c - max(es)) / T)            # max-subtracted for numerical stability
p_c    = w_c / sum(w)
n_c    = largest_remainder(p * B)             # integer allocation summing exactly to B
```

`largest_remainder` is specified explicitly (floor, then distribute the remaining
`B - sum(floor)` units to the largest fractional parts) so the allocation is deterministic and
`sum(n_c) == B` exactly. Ties in the remainder broken by **ascending cluster index**.

**Selection within a cluster.** Rank all 4447 cutouts by cosine to centroid `c` in R2:

```
scores_c = L2(cut) @ L2(centroid_c)           # cosine; both L2-normalised via common.l2
order_c  = np.argsort(-scores_c, kind='stable')
```

`kind='stable'` makes equal cosines resolve by ascending row index — the exact tie-break rule.

**Cross-cluster de-duplication (the rule that makes the arm well-defined).** A cutout may rank highly
for several centroids, but the budget is a set of `B` **distinct** images. Clusters are served in
**descending `n_c`**, ties by ascending cluster index; each cluster walks its `order_c` and takes the
next not-yet-taken row until it has `n_c`. Recorded per cell: `n_displaced` (how many times a
cluster's first choice was already taken), because a large value means the arms are converging for a
mechanical reason rather than a substantive one.

**Order-sensitivity check — MANDATORY, run for every cell.** The serving order is a defensible choice
but still a choice, and a different order yields a different targeted set. Rather than checking this
only when `n_displaced` looks large, every cell is selected under **five** orders:

```python
ORDERS = {
    'desc_nc':      lambda alloc: sorted(alloc, key=lambda c: (-alloc[c], c)),   # primary
    'asc_nc':       lambda alloc: sorted(alloc, key=lambda c: ( alloc[c], c)),
    'asc_index':    lambda alloc: sorted(alloc),
    'desc_es':      lambda alloc: sorted(alloc, key=lambda c: (-es[c], c)),
    'shuffled':     # 10 permutations, rng(20_000 + i), reported as mean +- sd
}
```

Reported per cell: `d_heldout` under each order; `jaccard_vs_primary` (set overlap of the selected
indices against `desc_nc`); and `d_order_spread = max|d_order - d_primary|` including the shuffled
arm's extremes.

- **Threshold (declared):** `d_order_spread < 0.05` — a quarter of the narrowest verdict band. If
  exceeded, the cell is flagged `ORDER_SENSITIVE`, **all five orders are reported rather than the
  primary alone**, and the verdict for that cell is stated as a range across orders, not a point.
- If the peak cell is `ORDER_SENSITIVE`, the overall verdict carries that flag and the de-duplication
  rule is named as a load-bearing arbitrary choice in `C1_RESULTS.md`.

**Built-in correctness check.** At `B = 4447` the targeted set is the entire pool, and so is the
random set. Therefore `‖Δmean‖` and `d` **must be exactly 0**. This is asserted, not just observed:

```python
assert B < POOL or (norm_dmean < 1e-12 and abs(d) < 1e-12), 'B=pool must give d=0'
```

A non-zero value at the ceiling is a bug, and the run halts.

### 2.2 Random arm — construction, stated precisely

- **Uniform draw without replacement** of size `B` from the **same 4447-row cutout pool**, in the
  **same embedding space**, using `np.random.default_rng(10_000 + draw_idx)`.
- **`N_DRAWS = 20`** independent draws minimum (configurable upward, never downward).
- **Spread is reported, never collapsed:** every cell reports
  `d_mean, d_sd, d_min, d_max, d_p05, d_p95` over the 20 draws, and the full per-draw vector is
  written to `c1_draws.csv`. No cell is summarised by a single number anywhere, including in
  `C1_RESULTS.md`.

### 2.3 Sweeps — exact grids

| Axis | Grid |
|---|---|
| **B** | `{250, 500, 1000, 2000, 3000, 4447}` — 4447 **is** the pool ceiling (D1: 4447 files, 4443 byte-unique), where d must be 0 |
| **alpha** (`T = alpha·sd(es)`) | start `{0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0}`, then **extended** by the rule below until both degeneracies are reached |
| **embedder** | `dinoL518` (primary), `dinoL224` (sensitivity) — **judged separately, never averaged** |
| **representation** | d measured in **R2** (cut) and **R3** (render) for every cell |

**Degenerate-end detection (both ends defined numerically):**

- **Concentrated end reached** when `max(n_c) / B >= 0.95` for the smallest alpha in the grid.
  If not reached, halve the smallest alpha and re-run, up to `alpha_min = 1e-4`.
- **Uniform end reached** when `total_variation(p, uniform) < 0.01`, i.e.
  `0.5 * sum(|p_c - 1/k|) < 0.01`, for the largest alpha.
  If not reached, double the largest alpha, up to `alpha_max = 1e3`.
- Both bounds and whether each was reached are logged as
  `alpha_min_reached_concentrated` / `alpha_max_reached_uniform` (booleans). If either cannot be
  reached within the caps, that is **logged as a limitation**, not silently accepted.

**Allocation diagnostics per cell** — so a small `d` is never confused with "we never actually
targeted": `clusters_funded`, `max_alloc_share`, `alloc_entropy_normalised`, `tv_from_uniform`,
`n_displaced`.

### 2.4 Metric — exact definition

Let `A` (targeted, B×D) and `R` (random draw, B×D), both L2-normalised rows.

```
delta      = A.mean(0) - R.mean(0)
norm_dmean = np.linalg.norm(delta)                       # ‖Δmean‖
u          = delta / norm_dmean                          # unit direction
a, r       = A @ u, R @ u                                # 1-D projections
s_pooled   = sqrt(((nA-1)*a.var(ddof=1) + (nR-1)*r.var(ddof=1)) / (nA+nR-2))
d_insample = (a.mean() - r.mean()) / s_pooled            # Cohen's d
```

**The direction is fitted to the same data it is evaluated on, which biases `d` upward.** This is the
same in-sample/held-out issue B3 was designed to expose, so C1 reports **both**:

- `d_insample` — as above.
- `d_heldout` — split both arms in half by `rng(draw_idx)`; estimate `u` from half A₁/R₁; evaluate the
  projections and Cohen's d on the disjoint half A₂/R₂. **`d_heldout` is the headline**; `d_insample`
  is reported beside it as the optimistic bound.

**Confidence intervals on `d_heldout` — MANDATORY for every cell.** A point estimate of `d` near a
band edge is exactly how a plausible-but-wrong number slips through, so no cell reports `d_heldout`
without an interval. Two independent sources of variability are quantified separately, then combined
conservatively:

| Interval | Construction | Captures |
|---|---|---|
| `ci_draws` | 2.5 / 97.5 percentiles of `d_heldout` over the `N_DRAWS = 20` random draws | random-arm variability |
| `ci_boot` | 1000 bootstrap resamples (with replacement) of the evaluation halves `A₂`, `R₂`, recomputing `d` each time; pooled across draws; `rng(30_000 + draw_idx)` | within-set sampling variability |
| **`ci_combined`** | `[min(lo_draws, lo_boot), max(hi_draws, hi_boot)]` — the **conservative union** | both, and it is the interval every judgement uses |

`ci_combined` is the interval carried into §4. Using the union rather than either alone means the
verdict cannot be made to look tighter by choosing the friendlier source.

**Ceiling reference — `d_max_possible`.** Compute `d` for the maximally-concentrated allocation
(entire budget `B` to the single highest-`target_es` cluster) versus random, per (embedder, B,
representation). This bounds what targeting could *ever* achieve at that budget, independent of `T`.
Without it, a small measured `d` cannot be distinguished from "this temperature happened to be mild".

---

## 3. Phase 2 — cross-checks, and what counts as a contradiction

### 3.1 C2 consistency — **C2 has not been run**

Verified: `grep -c "| EXP C2" results/REBUILD_LOG.txt` → **0**. So there is no measured C2 to check
against. The comparison is therefore against C2's **analytic design** in `REBUILD_PLAN.md` §3-C2 —
the pool-shift curve `(B/|Ds|)·(1 − B/4447)` — and the plan states plainly that this is a
**prediction, not a measurement**, and that `|Ds| ∈ {6824, 7824, 8824}` is **`UNVERIFIED`** because
the iteration-2 pools were deleted (`REBUILD_PLAN.md` §5b, D1).

C1 will therefore log a **shape** comparison only, and only for the quantity that does not depend on
`|Ds|`:

| Predicted (analytic) | Measured by C1 | Logged as a CONTRADICTION if |
|---|---|---|
| curve is **zero at B = 4447** | `d(B=4447)` | `d != 0` — this is a hard assert, since at the ceiling both arms are the whole pool |
| curve is **concave with an interior maximum** | `d` vs `B` | `d` is **monotone increasing** across the whole B grid, i.e. `argmax_B(d) == 4447` while `d(4447) == 0` is also required — a self-inconsistency that must be reported |
| peak located near **B ≈ 2000** | `argmax_B(d_heldout)` per embedder | the measured peak falls outside `{1000, 2000, 3000}` — logged as `C2_SHAPE_DIVERGENCE` with both values |

A divergence is written to the log block as an explicit `CONTRADICTION` metric naming both
experiments, and carried into `REVISION_TABLE.md`. It is **not** reconciled by adjusting C1, and it is
**not** smoothed by re-deriving `|Ds|`. If C2 is later run and disagrees with C1, that is a finding
about the two designs, and the plan says so in advance.

### 3.2 Degeneracy check (the clipL224 k=5 artifact)

B1 saw 5-point Spearman take only discrete values (ρ exactly `+1.0000`, `+0.6000`, `+0.3000`). The
analogue here is a partition too coarse to allocate over.

- **Detector:** for every (tag, B, alpha) cell, flag `DEGENERATE_PARTITION` when **any** of:
  1. `k < 10` (the partition itself is too coarse to express an allocation), or
  2. `clusters_funded <= 2`, or
  3. `max_alloc_share >= 0.95` **at an alpha that is not the concentrated end of the sweep**
     (i.e. concentration that is a property of the partition, not of `T`).
- **Consequence:** flagged cells are written to `c1_cells.csv` with `degenerate=1`, are **excluded
  from every threshold judgement and from the peak-of-B**, and appear in the log block only under a
  `DEGENERATE` metric name. `clipL224` (k=5) is expected to trip rule 1 by construction and is
  already disqualified at Gate 3; the detector exists so the same artifact is caught if it recurs in
  a space that was *not* pre-disqualified.

---

## 4. Thresholds — declared before running, and how ambiguity is handled

Judged on **`d_heldout`**, at **`argmax_B`** per embedder (the peak of the B-sweep, not a single B),
over non-degenerate cells, in **R2** and **R3** separately, for `dinoL518` and `dinoL224` separately.

| Band | Verdict | Action |
|---|---|---|
| `d_peak < 0.2` | **CONFIRMED-BY-MEASUREMENT** — the arms are materially identical | threshold PASS |
| `d_peak >= 0.5` | **VERDICT-REOPENS** — the arms differ substantially | threshold FAIL, and `REVISION_TABLE.md` records that this link of the argument does not hold |
| `0.2 <= d_peak < 0.5` | **AMBIGUOUS** — reported as such, **no binary call is forced** | see below |

### Band assignment uses the INTERVAL, not the point estimate

The three bands partition `[0, ∞)` at **0.2** and **0.5**. For every cell:

```python
def band(x):  return 'CONFIRMED' if x < 0.2 else ('AMBIGUOUS' if x < 0.5 else 'REOPENS')
lo, hi   = ci_combined
straddles = band(lo) != band(hi)
```

- **`ci_straddles_band` is logged for every cell**, naming both bands it spans
  (e.g. `CONFIRMED|AMBIGUOUS`), together with `d_heldout`, `ci_draws`, `ci_boot`, `ci_combined`.
- **Declared threshold:** *the held-out `ci_combined` at the peak cell lies entirely within one
  verdict band.* PASS/FAIL is logged like any other threshold.
- **If it FAILS**, the verdict for that (embedder × representation) is
  **`INCONCLUSIVE-CI-STRADDLES-{band_lo}|{band_hi}`**, and the point estimate is **not** reported as
  the answer anywhere — not in the log block's headline metrics, not in `C1_RESULTS.md`, not in
  `REVISION_TABLE.md`. A point estimate whose interval crosses 0.2 or 0.5 does not license the
  corresponding claim, and the plan commits to that in advance so the decision is not made after
  seeing which side the point landed on.
- A straddling CI at the peak also **triggers §4's variance/coverage follow-up**, on the same footing
  as an AMBIGUOUS point estimate.

**Ambiguity is not resolved by picking a side.** If any (embedder × representation) peak lands in
`[0.2, 0.5)`, C1 reports `VERDICT = AMBIGUOUS` and runs one named follow-up — a **variance/coverage
comparison**, specified now so it is not invented after seeing the number:

```python
def variance_coverage_followup(A, R, target_emb) -> dict:
    #  (i) spread:   trace(cov(A)) / trace(cov(R))   and   logdet ratio (pseudo-det, top-50 PCs)
    #  (ii) coverage: k-NN recall of A and of R against the TARGET manifold, k=5,
    #                 the same construction A3 uses, reported as recall_A, recall_R, delta
    # (iii) occupancy: how many of the k clusters each arm touches, and the TV distance
    #                 between the two arms' cluster-occupancy distributions
```

Reported for both arms at the ambiguous cell, with the explicit statement that a mean-shift of
`d ∈ [0.2, 0.5)` **plus** a materially different spread or coverage would be a different situation
from a mean-shift alone.

**Disagreement between embedders or between R2 and R3** is itself reported: if `dinoL518` and
`dinoL224` land in different bands, the verdict is `EMBEDDER-DEPENDENT` and both are stated. B1
already showed a 0.10 swing in ρ between these two spaces, so this is a live possibility, not a
formality.

---

## 5. Limitation statement — logged regardless of outcome

Written into the `EXP C1` log block's `NOTES` **whatever the result is**:

> Cohen's *d* is a **mean-shift** measure along a single direction. Two sets can share a mean and
> differ substantially in variance, in higher moments, or in which regions of the space they cover. A
> small *d* therefore establishes that the targeted and random arms have nearly the same **centre**;
> it does **not** establish that they are the same **set**. Variance and coverage are unmeasured
> unless §4's follow-up was triggered, and are the one route by which a true effect could exceed what
> a mean-shift predicts.

Plus the inherited limitations, also logged unconditionally:

- The partition C1 allocates over is **weakly separated** — B1 measured silhouette peaks 0.1465 /
  0.1600 / 0.0568 and seed-ARI 0.52–0.77. The unit of allocation is soft.
- The allocation signal itself is only a **moderate** predictor of endpoint error — B1 completion II
  measured ρ(target ES, endpoint MAE) = +0.6595 / +0.6284, not the +0.87 the endpoint-ES figure
  suggested.
- Selection is by **R2** (the grey-128 cutout), which is what a real pipeline has at selection time.
  Selecting by R3 would require renders to exist before selection. Out of scope, stated as such.
- **Seed-level robustness of the ES signal is `UNVERIFIED-DEFERRED`** (retraining deferred).

---

## 6. Old claims — comparison rows only, filled after measurement

| Old claim | Old value | Measured | Verdict |
|---|---|---|---|
| C1.1 Cohen's *d* targeted-vs-random | `≈ 0.10` `[no code]` | *(blank until measured)* | |
| C1.2 ‖Δmean‖ | `0.084–0.099` `[no code]` | *(blank)* | |
| C1.3 clusters funded / max alloc | `1–49` / `76–999` `[no code]` | *(blank)* | |

These enter the script **only** as `OLD_CLAIMS` tuples passed to `common.log_block(..., old_claims=…)`,
exactly as D2/D1/B1 do. No code branches on them; no threshold references them.

---

## 7. Deliverables

| Deliverable | Path |
|---|---|
| Gate script | `rebuild/C1/c1_preflight.py` |
| Measurement script | `rebuild/C1/c1_targeted_vs_random.py` |
| Preflight record | `rebuild/C1/out/c1_preflight.json` |
| Per-cell results | `rebuild/C1/out/c1_cells.csv` |
| Per-draw spread | `rebuild/C1/out/c1_draws.csv` |
| Selected sets | `rebuild/C1/out/c1_selection_{tag}_B{B}_a{alpha}.json` (indices, for auditability) |
| Ceiling reference | `rebuild/C1/out/c1_ceiling.csv` |
| **CI + band straddle** | `rebuild/C1/out/c1_intervals.csv` — `d_heldout`, `ci_draws`, `ci_boot`, `ci_combined`, `band_lo`, `band_hi`, `ci_straddles_band` per cell |
| **Order sensitivity** | `rebuild/C1/out/c1_order_sensitivity.csv` — `d_heldout` under all five serving orders, `jaccard_vs_primary`, `d_order_spread`, `ORDER_SENSITIVE` |
| Follow-up (if ambiguous) | `rebuild/C1/out/c1_variance_coverage.json` |
| Disqualified space | `rebuild/C1/out/c1_disqualified_clipL224.json` |
| Log | one appended `EXP C1` block in `results/REBUILD_LOG.txt`, same discipline as E0/D2/D1/B1 |
| Setup doc | `rebuild/C1/C1.md` |
| Results doc | `rebuild/C1/C1_RESULTS.md` (written last, every bolded figure traceable to the block) |
| Revision table | `REVISION_TABLE.md` updated with C1.1–C1.3 and any self-corrections |

---

## 8. Amendments (accepted at review, before any execution)

Both target a specific way a plausible-looking but wrong `d` could pass unnoticed.

| # | Amendment | Where | Why it matters |
|---|---|---|---|
| **A1** | Held-out **confidence intervals are mandatory** for every cell, and any CI straddling a verdict band is flagged and blocks the point estimate from being reported as the answer | §2.4, §4 | A point estimate sitting near 0.2 or 0.5 reads as a clean verdict while the underlying interval spans two bands. Making the interval mandatory and band-aware means the ambiguity cannot be lost between the measurement and the write-up |
| **A2** | The de-duplication **order-sensitivity check is mandatory**, run under five orders for every cell, not conditional on `n_displaced` looking large | §2.1 | The serving order is an arbitrary choice that changes which images are selected. Gating the check on a heuristic would only catch it when it was already obvious; running it always means an order-dependent `d` is caught even when `n_displaced` looks unremarkable |

Both add declared thresholds (`ci_combined` within one band; `d_order_spread < 0.05`) that PASS/FAIL
in the log block like any other.

---

## (a) Inputs this plan depends on that are NOT yet confirmed

1. **C2 has not been run** — verified `0` `EXP C2` blocks. §3.1's cross-check is against an
   **analytic prediction**, not a measurement. It cannot confirm C2; it can only flag a shape
   divergence for later reconciliation.
2. **`|Ds| ∈ {6824, 7824, 8824}` is `UNVERIFIED`** (iteration-2 pools deleted). No C1 threshold uses
   it; only the `|Ds|`-free parts of C2's predicted shape are compared.
3. **B3 has not been run** — so C1's R2-vs-R3 measurement cannot be cross-checked against B3's
   acceptance figures. Noted, not blocking.
4. **The A3 k-NN recall construction** named in §4's follow-up does not exist yet (A3 unrun). If the
   follow-up triggers, C1 will implement recall inline and label it `C1-local implementation`, to be
   reconciled when A3 runs.

## (b) Where I am least confident the specification is precise enough

1. **The alpha/degeneracy grid.** `T = alpha·sd(es)` is scale-free and the two degeneracy detectors
   are numeric, but the caps (`alpha_min = 1e-4`, `alpha_max = 1e3`) are guesses. If either end is
   unreachable within them, that is logged as a limitation — but the *right* caps are not yet known.
2. **`d_heldout` as the headline.** Splitting in half halves the sample and widens the estimate; at
   `B = 250` each half is 125. **Amendment A1 addresses this**: the widening is now measured rather
   than assumed, because `ci_boot` quantifies exactly that cost and `ci_combined` carries it into the
   verdict. What remains unbounded is whether `B = 250` will produce an interval so wide that it
   straddles a band by construction — if it does, that is reported as a limitation of the small-`B`
   end of the sweep, not as an ambiguous result.
3. ~~**The de-duplication rule.**~~ **Resolved by amendment A2** — measured for every cell under five
   orders, with a declared threshold, rather than checked only when it looked necessary.
4. **`d_max_possible`.** I am confident it is the right reference to have, less confident that
   "entire budget to the single highest-ES cluster" is the tightest achievable ceiling.

## (c) Execution status

**No code has been written or executed.** This turn performed read-only verification of the input
artifacts listed in §0 and read existing scripts; nothing was created, modified, or run.

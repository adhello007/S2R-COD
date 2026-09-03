# REVISION_TABLE.md — where the rebuilt number differs from the old package

Running record, appended as each experiment completes. Every row cites the log block that produced the
measured value. The "old value" column is the frozen record from `REBUILD_PLAN.md` §4 — a claim under
test, never an input.

Completed so far: **E0, D2, D1, B1, C1**. Seven outstanding: A1, A2, A3, B2, B3, C2, C3.

> **C1 REOPENS THE VERDICT.** The decisive measurement was never computed by the old
> package. Measured, it refutes `d ~ 0.10` by roughly an order of magnitude and removes one
> leg of the "Stage C is not viable" argument. See C1.1-C1.4 below.

---

## 1. Old values that MOVED

| # | Claim | Old value | Measured | Log block | Why it moved |
|---|---|---|---|---|---|
| D1.1 | Distinct foregrounds in the base pool | **4447** | **4443** unique of 4447 files (raw) | `EXP D1` | The old package wrote a *file count* as a *distinctness* claim. Byte-level hashing finds 4 redundant files. Strengthens the conclusion — the pool is more exhausted, not less |
| E0.1 | Render reproducibility at a fixed seed | *"byte-identity is not expected — cuDNN is nondeterministic"* (my own planned expectation) | **4447/4447 byte-identical**, images and masks | `EXP E0` | The expectation was wrong. Measured bit-exact on this stack. The cluster-agreement threshold I built as a fallback passed at 1.0 trivially |
| E0.2 | Scope of that reproducibility | *unqualified* | holds only at **fixed shard count over a fixed input listing** | `EXP D2` | D2 s7/s8 found a render depends on position-in-shard. E0's headline needed the qualifier and did not have it |
| D2.1 | CHAMELEON ∩ Target | **0** (pixel identity — correct at that level) | **41/76 (53.9 %)** are re-encodes of Target training images | `EXP D2` | Exact hashing cannot see re-encoding. The old method under-bounded the quantity it was reporting. CHAMELEON is withdrawn as an endpoint |
| D2.2 | Cross-named duplicate identity | `COD10K-CAM-3-Flying-**53**-Owl-4633` | `Flying-**65**-Owl-4633` | `EXP D2` | Transcription error in the old documents. No such file exists at `Flying-53`. Immaterial to any number |
| B1.1 | ρ(ES, MAE) per-cluster k=20 test | +0.788 | **+0.8699** ± 0.0297 | `EXP B1` | Moved **up**. Old package had no seed spread; this is 10 k-means seeds |
| B1.2 | ρ(ES, 1−Sα) per-cluster k=20 test | +0.409 | **+0.5067** ± 0.0725 | `EXP B1` | Moved **up** |
| B1.3 | ρ(ES, 1−IoU) per-cluster k=20 test | +0.265 / +0.271 | **+0.4060** ± 0.0884 | `EXP B1` | Moved **up** |
| B1.4 | ρ(ES, MAE) per-cluster k=20 **val** | +0.976 | **DEGENERATE — not reportable** | `EXP B1` | Not a value that moved. Only 1–4 CAMO clusters clear the 15-image floor; Spearman over 2–3 points is ±1 by construction. Confirmed degenerate in **all three** embedder spaces |
| B1.5 | "ES predicts the wrong objective" as a **binary** | asserted as a clean threshold | **not stateable on endpoint ES** — ratio 0.4919–0.6952 across 3 embedders × 2 k, straddling 0.5 | `EXP B1` (3rd block) | k-unstable and embedder-unstable. Retired in favour of the effect size |
| B1.6 | The ES signal B1 correlates | **endpoint** ES (COD10K-test) | **target** ES is what `CLS.py:81-105` computes and what Stage C allocates by — GT-free, on the unlabeled target set | `EXP B1` (4th block) | The cluster CSV C1 consumes had `n_target` as a count and **no `target_es`**. A C1 built on it would have allocated by a test-set signal the pipeline does not have |
| B1.7 | ρ(ES, MAE) per-cluster, as a usable allocation signal | +0.87 (endpoint ES) | **+0.6595** (dinoL224) / **+0.6284** (dinoL518) on the real target-ES signal | `EXP B1` (4th block) | The committed figure **overstated the usable signal by ρ ≈ 0.21–0.25**. The two ES signals only moderately agree per cluster (ρ 0.695 / 0.573) |
| **C1.1** | **Cohen's *d* targeted-vs-random** | **`≈ 0.10`** `[no code, never computed]` | **+1.0028 to +1.2325 at peak**, all four embedder × representation cells | `EXP C1` | **REFUTED, ~10×.** CIs entirely inside the REOPENS band; both embedder spaces agree. The arms are NOT materially identical in embedding space |
| **C1.2** | *d* at the old package's own budget `B = 1000` | `≈ 0.10` | **+0.655 to +1.024** | `EXP C1` | **REFUTED, 7-10×** at the budget the old package itself proposed |
| **C1.3** | "the two arms see nearly identical data, so no gain is possible" | asserted | **not supported** — declared threshold `d ≥ 0.5` → VERDICT REOPENS | `EXP C1` | This leg of the argument fails. It does **not** establish that Stage C works — the other legs (A1 bottleneck, D1 exhaustion, B1 moderate signal, C3 noise floor) are untouched |
| **C1.4** | Held-out Cohen's *d* under a known-zero difference | assumed 0 | **−0.3241** (sd 0.0166) | `EXP C1` | New. The ceiling assertion fired and exposed that the half-split estimator is **negatively biased under the null**, i.e. conservative. Every measured *d* is now read against this reference |
| B1.8 | Direction of the wrong-objective claim | "ES predicts pixel, not structure" | **NOT SUPPORTED on the real signal** — ratio 0.5166 / 0.5463, both ≥ 0.5 in both candidate spaces | `EXP B1` (4th block) | A **reversal of direction**. I declared a threshold expecting the boundary to stay unstateable; it failed because the boundary *is* stateable on target ES and lands on the other side. B1's contribution becomes "the allocation signal is moderately predictive at best", not "it points at the wrong error type" |

## 2. Corrections to the rebuild's own work

Kept visible because a rebuild that only ever corrects someone else is not auditing itself.

| # | What was wrong | Where | How it was found | Fix |
|---|---|---|---|---|
| R1 | Provenance gate was a grep, and flagged its own `FORBIDDEN` list plus the package's prose — 14 false positives | `EXP E0` blocks 1–2 | The gate FAILED its own threshold | Rewritten as an AST scan; docstrings excluded; pragma exemptions reported, not suppressed; self-tested against injected violations |
| R2 | Four figures in `E0_RESULTS.md` existed only outside the log (s2 sample size, staging cross-check, two ad-hoc directory digests) | `EXP E0` blocks 3→4 | Mechanical traceability check | Promoted into the script; new threshold comparing image and mask digests |
| R3 | D2's near-duplicate scan used contrast-normalised thumbnail bucketing — roughly a quarter of the true recall | `EXP D2` blocks 2→3 | Audit against an exhaustive search | Replaced by exhaustive within-dimension search. CHAMELEON moved 10/76 → 41/76 |
| R4 | `4443` used in `D2_RESULTS.md` as arithmetic rather than a logged metric | `EXP D2` blocks 1→2 | Traceability check | `unique_raw_hkuis` / `unique_authors_pool` added as metrics |
| R5 | D1 scored **both** pools against `raw_gt`, producing an apparent 406-image anomaly in the authors' pool | D1, pre-log | Audit of D1's own first run | Each pool scored against the mask it was rendered with, plus an eroded interior. Anomaly was a mask-boundary artifact; plausibly-regenerated count is 0 |

| R6 | B1's first scoring pass used `.astype(np.uint8)` (truncation) where `MyTest.py` uses `cv2.imwrite` (rounding), biasing every prediction down ~0.5 grey levels | B1, pre-log | Endpoint MAE missed D2's independently measured value by 1.23e-03, failing a declared threshold | `np.round`; endpoint MAE became 0.074463 (delta 2.3e-07), Sα 0.717216 |
| R7 | B1's k-selection ranked k by bootstrap ARI, which is biased toward small k — it chose k=5, the worst silhouette in the sweep | B1, pre-log | The selected k had the worst compactness in its own sweep | Silhouette primary; stability reported but not used to rank; discarded criterion recorded in the log |
| R8 | B1 reported a per-cluster ρ of +1.0 on CAMO from 2 clusters | B1, pre-log | Reproduced the old package's +0.976 artifact | Per-cluster ρ suppressed below 5 surviving clusters |
| R9 | B1's `fit_kmeans` cached on `(k, seed)` and `endpoint_emb` on `split` alone, and `step_correlate` / `emit_cluster_es` called `assign_clusters` **without** a tag | B1, before the embedder sweep | Inert with one embedder; would have silently fed dinoL518's k-means fits and endpoint embeddings to the CLIP and dinoL224 runs | Cache keys include the tag; the tag is threaded through; defaults unchanged, verified by reproducing the committed block 7/7 |
| R11 | C1's ceiling assertion required `d_heldout = 0` at `B = 4447` as well as `‖Δmean‖ = 0` | C1, pre-log | The assertion fired | `‖Δmean‖ = 0` is the correct ceiling check; the held-out *d* there is a **null calibration**, not a bug — reported as a measurement rather than relaxed away |
| R12 | C1's plan §3.1 specified a `C2_SHAPE_DIVERGENCE` cross-check that the first implementation omitted | C1 blocks 1→2 | Re-reading the approved plan against the code | Implemented — and implementing it revealed the cross-check was a **category error**: C2's pool-shift and C1's *d* are different quantities with legitimately different B-shapes. Recorded, not dropped |
| R13 | C1's first Gate-1 scan flagged its own module docstring | C1, pre-log | The gate failed on a clean tree | Docstrings excluded (prose cannot read a CSV column), matching E0's fix. Gates then **self-tested** with an injected probe: both caught it, both returned to PASS when removed |
| R10 | B1 correlated **endpoint** ES throughout, and shipped C1 a cluster CSV with no `target_es` column | B1 completions I and II | Reading `CLS.py:81-82` — the loader is built on the target root with `gt_root=None`, so the allocation signal is GT-free and target-side | Target ES computed for all 4040 images × 5 architectures; `target_es` added to all three cluster CSVs; the faithful correlation measured. **Changed the direction of B1's headline claim** — see B1.8 |

**R3 is the only one where a measurement was substantively wrong** rather than untraceable. It was
found by auditing my own method, not by the method reporting a problem — which is the failure mode
this rebuild is most exposed to.

## 3. Old values that RE-TESTED CLEAN

Worth recording explicitly: the old package's D2/D1 claims were marked `[no code]` — no producing
script, no log block — yet these all reproduce. **The old defect was provenance, not arithmetic.**
Being unverifiable is not the same as being wrong, and the rebuild has to be able to say so.

| Claim | Old value | Measured | Log block |
|---|---|---|---|
| COD10K-test ∩ Target | 7 (2 same-name, 5 cross-named) | 7 (2 same-name) | `EXP D2` |
| CAMO ∩ CHAMELEON | 3 | 3 | `EXP D2` |
| Internal duplicates in Target | 2 | 2 | `EXP D2` |
| Internal duplicates in the render pool | 2 (4445 unique) | 2 (4445 unique) | `EXP D2`, `EXP D1` |
| MAE impact of the leaked images | 0.000012 (0.017 %) | 1.242e-05 (0.0167 %) | `EXP D2` |
| Every added image is a re-render, not a new object | zero foregrounds outside the base pool | 0 outside; bijection both pools | `EXP D1` |
| ρ(ES, MAE) **per-image** test | +0.751 | **+0.7514** [+0.727, +0.777] | `EXP B1` |
| Invented background fraction | 80.87 % | 0.8087 (`staging_background_frac`, independent code path) | `EXP E0` |

## 4. Claims that changed in KIND, not value

| Claim | Old framing | Rebuilt framing | Log block |
|---|---|---|---|
| "Object preserved, background generated" | object *regenerated faithfully* | the **source object pixels are composited back** (`test.py:165`); object error 6.245 vs background 71.676 | `EXP E0` |
| Foreground exhaustion | "additions are re-renders" | **"the foreground pool is exhausted; the background is not"** — the object is fixed pixel-for-pixel, the background has unbounded freedom | `EXP D1` |
| "The generated pool" | one pool | **three** mutually non-identical pools; training reads the authors' pool, the old evidence embedded the local one | `EXP E0`, `EXP D2` |
| "The HKU-IS foreground fraction" | one number | **set-dependent** — `raw_gt` 0.19132 vs `auth_gt` 0.18557 | `EXP D1` |
| Cluster membership | a stable label | an unjustified preprocessing choice reassigns **5.4 %** of images (E0); silhouette peaks at only 0.1465 / 0.1600 / 0.0568 across the three embedder spaces, and CLIP has no interior peak at all — the unit of allocation is soft in **every** space | `EXP E0`, `EXP B1` |
| "ES predicts the wrong objective" | a binary verdict | an **effect size**: ES tracks pixel error ~2× as strongly as structural error (ρ 0.86 vs 0.43 per-cluster). The binary flips with k (ratio 0.4999 at k=75, 0.5825 at k=20), so the label is not k-stable and is not quoted | `EXP B1` |

## 5. Still outstanding

Every §4 row of `REBUILD_PLAN.md` belonging to A1, A2, A3, B2, B3, C2, C3 remains untested. The
load-bearing one is **C1** (`d ≈ 0.10`), which never had a producing script in the old package; it now
has its input ready — `rebuild/B1/out/b1_cluster_es_dinoL518.csv`, 75 clusters with per-cluster ES,
**with a mandated sensitivity re-run against `b1_cluster_es_dinoL224.csv` (50 clusters)**, because the
two spaces differ by 0.10 in ρ(ES,1−Sα) at k=20 and C1 must not re-cluster. Both CSVs now carry
`target_es`, and **C1 must allocate by `target_es`, not `test_es`** — completion II verified C1
runnable in both spaces (cutouts 4447×1024, row-aligned to the raw pool).

The old package's cross-run ρ(ES, MAE) = +0.893 ± 0.059 (n=5 runs) is **UNVERIFIED-DEFERRED**: it is a
seed-variance claim, and retraining is deferred. B1 substitutes a cross-architecture axis instead.

**The highest-value next measurement is C1's variance/coverage follow-up.** It was *not* triggered —
the declared rule fires on an AMBIGUOUS band or a straddling CI, and C1 returned a clean REOPENS — but
it is what would say whether the arms differ in spread and coverage or only in centre, which is what
determines whether a separation of *d* ≈ 1 could plausibly move a trained model. C1 measures a
direction-fitted mean shift and nothing more.

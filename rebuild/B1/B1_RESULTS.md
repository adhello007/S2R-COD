# B1 — Verified results

**Status: COMPLETE. 6 of 7 thresholds PASS; 1 FAIL, and the FAIL is the most important result.**

The log holds two `EXP B1` blocks; the second is authoritative. Block 1 -> 2 added `endpoint_Sa` and
the full k-sweep curves as logged metrics, because this document used them and the traceability rule
requires a number to exist in the log before it appears here.

Source of every number below: `results/REBUILD_LOG.txt`, block **`EXP B1`** timestamped
`2026-09-01T14:04+05:30` (the second `EXP B1` block), commit `0a1d238`. That block is authoritative; this file is a reading of
it. Every figure quoted here appears verbatim in that block — checked mechanically.

Setup: `rebuild/B1/B1.md`. **Trains a model: NO.**

---

## 1. The headline: ES predicts pixel error about twice as strongly as structural error

Per-cluster Spearman ρ on **COD10K-test**, mean ± sd over 10 k-means seeds, with the range across
seeds:

| Error type | at principled k=**75** | at old package's k=**20** |
|---|---|---|
| MAE (pixel-average) | **+0.8553** ± 0.0264 [+0.796, +0.891] | **+0.8699** ± 0.0297 [+0.817, +0.922] |
| 1 − Sα (structure) | **+0.4276** ± 0.0461 [+0.356, +0.506] | **+0.5067** ± 0.0725 [+0.373, +0.635] |
| 1 − IoU (localisation) | **+0.2983** ± 0.0564 [+0.221, +0.401] | **+0.4060** ± 0.0884 [+0.280, +0.564] |

Per-image, which needs no clustering choice at all (n = **2026**, permutation p = **0.0002** for all
three, bootstrap CI in brackets):

| Error type | ρ |
|---|---|
| MAE | **+0.7514** [+0.727, +0.777] |
| 1 − Sα | **+0.3114** [+0.270, +0.355] |
| 1 − IoU | **+0.2015** [+0.161, +0.247] |

The **ordering is unambiguous and consistent everywhere**: ρ(MAE) ≫ ρ(1−Sα) > ρ(1−IoU). It holds
per-cluster at both k, per-image, and on CAMO (per-image MAE **+0.6604**, 1−Sα **+0.3888**,
1−IoU **+0.2495**). The CIs for MAE and 1−Sα do not overlap at any setting.

## 2. The declared threshold lands on a knife edge, and the binary verdict is not k-stable

| Metric | Value |
|---|---|
| ρ(ES,1−Sα) / ρ(ES,MAE) at k=75 | **0.4999** |
| Declared boundary | 0.5 |
| Same ratio at k=20 | **0.5825** |
| Binary classification stable across k? | **False** |

The classification threshold I declared before running — "wrong objective iff ratio < 0.5" — returns
**True** at the principled k by a margin of 0.0001 (0.5 - 0.4999), and **False** at k=20. **That threshold FAILS
its own stability check and should not be quoted as a binary verdict.**

This is reported as a FAIL rather than resolved by picking the convenient k. What survives is not the
binary label but the **effect size**: ES explains structural error roughly **half** as well as it
explains pixel error, with the exact ratio depending on k in the range ~0.50–0.58.

## 3. Cross-architecture

Per-cluster ρ at k=75, 3 seeds:

| Architecture | MAE | 1−Sα | 1−IoU |
|---|---|---|---|
| SINet/S2C (primary) | **+0.863** | **+0.449** | **+0.324** |
| SINet/S2C_MT | **+0.879** | **+0.483** | **+0.353** |
| SINet/S2C_SO | **+0.402** | **+0.510** | **+0.354** |
| SINet-v2/S2C | **+0.899** | **+0.597** | **+0.432** |
| SegMaR/S2C | **+0.840** | **+0.576** | **+0.426** |

Ratio 1−Sα / MAE: **mean 0.738, range 0.520..1.268** over 5 architectures.

Four of five agree closely: ρ(MAE) 0.84–0.90 and ρ(1−Sα) 0.45–0.60. **`S2C_SO` is the outlier** —
its ρ(MAE) collapses to +0.402 while ρ(1−Sα) stays at +0.510, inverting the pattern. That is
mechanistically expected rather than surprising: source-only training runs no consistency loss and
never forwards a target image (`MyTrain.py:47`), so its "teacher" is not an EMA of a student that
learned from a teacher. ES on a source-only pair is measuring a different quantity. It is reported,
not excluded.

## 4. Clustering: the target set barely has cluster structure

| k | silhouette | seed-ARI | bootstrap-ARI |
|---|---|---|---|
| 5 | 0.0566 | 0.732 | 0.624 |
| 20 | 0.1326 | 0.524 | 0.506 |
| **75** | **0.16** | 0.6155 | 0.5789 |
| 150 | 0.1507 | 0.625 | 0.618 |

Silhouette peaks at **0.16** — very weak separation. Bootstrap ARI never exceeds 0.624 (`k5=0.624`
in the logged curve), and
clusters used at k=75 range **50-53 of 75** (the rest hold fewer than 15 endpoint images).

---

## 5. Old claims re-tested

Re-measured with the outcome treated as unknown. The old package's own summary listed all five as
MISMATCH, so these were not targets.

| Old claim | Old value | Measured | Verdict |
|---|---|---|---|
| ρ(ES, MAE) per-cluster k=20 test | +0.788 | **+0.8699** ± 0.0297 | **MISMATCH** — moved **up** |
| ρ(ES, 1−Sα) per-cluster k=20 test | +0.409 | **+0.5067** ± 0.0725 | **MISMATCH** — moved **up** |
| ρ(ES, 1−IoU) per-cluster k=20 test | +0.265 soft / +0.271 hard | **+0.4060** ± 0.0884 (hard) | **MISMATCH** — moved **up** |
| ρ(ES, MAE) per-cluster k=20 val | +0.976 | **DEGENERATE-NOT-REPORTED** | **REFUTED AS A NUMBER** |
| ρ(ES, MAE) per-image test | +0.751 | **+0.7514** [+0.727, +0.777] | **MATCH** |
| Cross-run ρ(ES, MAE) k=20 | +0.893 ± 0.059 (n=5 runs) | not comparable — seed axis deferred | **UNVERIFIED-DEFERRED** |

Two things stand out. **The per-image value reproduces to four decimals** (+0.7514 vs +0.751), which
is a strong sign the ES computation and the error metrics are being computed the same way the old
package computed them — so the per-cluster divergences are about the *clustering*, not the signal.

And **the old val figure of +0.976 is not a value that moved — it is a number that should never have
been reported.** At k=20 on CAMO only **1–4** clusters clear the 15-image floor. Spearman ρ over 2 or
3 points is always near ±1 by construction. My own first pass reproduced exactly this artifact
(rho = +1.0 from 2 clusters, in a superseded `--no-log` run) before I added the degeneracy guard.

---

## 6. How the findings change our approach, thinking and assertions

### 6.1 The claim "ES optimises the wrong objective" is directionally right and was over-stated as binary

- **Standing claim:** ES predicts MAE but not Sα, so targeting optimises the wrong objective. The
  threshold was declared as a clean binary.
- **Measured:** ρ(MAE) = **+0.8553**, ρ(1−Sα) = **+0.4276** at k=75 — a ratio of **0.4999**, i.e.
  exactly on the declared boundary, and **0.5825** at k=20. The binary flips with k.
- **Revised position:** state the **effect size, not the label**. ES is a strong predictor of
  pixel-average error (ρ ≈ 0.86 per-cluster, 0.75 per-image) and a **materially weaker** predictor of
  structural and localisation error (ρ ≈ 0.43 and 0.30 per-cluster; 0.31 and 0.20 per-image). The gap
  is large, robust across k, seeds, splits and four of five architectures, and the CIs do not overlap.
  What is *not* robust is any statement of the form "ES fails to predict Sα" — it does predict it,
  about half as well.
- **Why this matters for the verdict:** the argument does not need the binary. "Targeting allocates
  budget by a signal that tracks pixel error roughly twice as well as it tracks the structural error
  the benchmark actually reports" is both weaker-sounding and better-supported than "ES predicts the
  wrong thing". Overclaiming here would have been the old package's failure mode in a new coat.

### 6.2 A correlation over two clusters is not a correlation — and this bit both packages

- **Measured:** at k=20 on CAMO, **1-4** clusters clear the population floor; the old package reported
  +0.976 and my own first pass produced rho = +1.0, both from 2-3 points.
- **Revised position:** per-cluster ρ is reported only when **≥ 5** clusters survive; otherwise it is
  logged as `DEGENERATE-NOT-REPORTED` with the cluster count. The old +0.976 is not a divergence to
  reconcile — it is an artifact of tiny n, and reporting it as evidence that "ES strongly predicts
  error on val" was unsupported.
- **Consequence:** CAMO contributes **per-image** ρ only. B2, which inherits this clustering, must
  apply the same guard.

### 6.3 The target set has weak cluster structure, which undercuts the premise upstream of B1

- **Measured:** silhouette peaks at **0.16**; bootstrap ARI never exceeds **0.624**; seed-ARI at k=20
  is 0.524 (`k20=0.524` in the logged seed-ARI curve), meaning two k-means runs with different seeds
  agree only moderately on the partition.
- **Position:** Stage C's design presumes clusters that a budget can be meaningfully allocated over.
  These clusters are weakly separated and only moderately reproducible. That does not invalidate B1's
  correlations — they are computed over whatever partition exists, and reported with the seed spread —
  but it does mean **the unit of allocation is itself soft**. B3 and C1 inherit this: an allocation
  over clusters this diffuse is an allocation over a partition that would change materially with a
  different seed.
- **This is upstream of the question B1 was asked**, and it was not visible in the old package because
  k was never swept and stability never measured.

### 6.4 A quantisation convention changed every error number, and was caught by cross-checking D2

- **What happened:** my first scoring pass used `(cam*255).astype(np.uint8)`, giving endpoint MAE
  0.073237 (a superseded `--no-log` run) against D2's independently measured **0.074463** — a delta of 1.23e-03 that failed my
  declared 0.001 threshold.
- **Cause:** `MyTest.py:76` writes predictions with `cv2.imwrite(path, cam*255)`, and OpenCV's
  float→uint8 conversion **rounds**, while `.astype` **truncates**. Truncation biases every prediction
  down by ~0.5 grey levels.
- **Fix:** `np.round(cam*255)`, applied to MAE, Sα and both IoU variants. Endpoint MAE became
  **0.074463** (delta 2.3e-07) and Sα **0.717216**, matching the repo's recorded 0.7172.
- **Position:** the cross-check earned its place. Without an independently measured value to reproduce,
  a systematic 1.7 % relative error in every "true error" number would have propagated silently into
  every correlation. Recorded because it was my defect.

### 6.5 The k-selection criterion was wrong on first formulation

- **What happened:** `pick_k` initially ranked k by bootstrap ARI, on the reasoning that reproducibility
  matters more than compactness. It selected **k=5**, which has the **worst** silhouette (0.0566) in
  the sweep.
- **Cause:** with few, very large clusters, two subsample partitions agree almost by construction.
  Adjusted Rand is chance-corrected against random labelling, not against coarseness.
- **Fix:** silhouette is primary; stability is measured and reported but does not rank. Both curves are
  in `out/b1_k_sweep.csv`, and every correlation is reported at the principled k **and** k=20.
- **Position:** recorded rather than silently swapped. It is also why §6.1 refuses to lean on a
  k-dependent binary.

---

## 7. Consequences by downstream experiment

| Experiment | What B1 changes for it |
|---|---|
| **C1** | **Reads `out/b1_cluster_es.csv`** — 75 clusters with per-cluster ES and error. It must not re-cluster. §6.3 means its allocation is over a soft partition; §6.2's guard applies to any per-cluster statistic |
| **B2** | Inherits this clustering, the k choice, the seed spread, and the ≥5-cluster guard. Its coverage term is correlated against the same three error types, reported separately |
| **B3** | §6.3 is a direct caution: acceptance is defined *on* cluster membership, and these clusters are weakly separated and only moderately seed-stable |
| **C3 / findings** | The ES→error link is *partial*, not broken: strong for MAE, about half as strong for Sα. The verdict must be phrased as an effect size |
| **Any reporting** | The old val ρ of +0.976 must not appear. It is a 2-point artifact |

---

## 8. What B1 does not establish

- **That ES is useless as an allocation signal.** It is a strong predictor of pixel error and a
  moderate predictor of structural error. B1 measures the gap; it does not show the signal is noise.
- **Causality.** These are rank correlations between two quantities measured on the same images. B1
  does not show that allocating by ES *would* or *would not* change accuracy — that is C1's and C3's
  question.
- **Seed-level robustness of ES itself.** Every ES value comes from one final training run per
  architecture. Cross-architecture is the substitute. Seed variance is **UNVERIFIED-DEFERRED**.
- **Anything about CHAMELEON**, excluded on D2's measurement, or about NC4K, which has no ES here
  because it was not scored.
- **That k=75 is the right k.** It is the silhouette peak of a weakly-clustered set. The honest
  statement is that no k is strongly supported by the data, which is why everything is reported at two
  k values with the seed spread.
- **A per-cluster ρ on CAMO.** Structurally unavailable at these k values, not merely uncertain.

---
---

# B1 completion — the embedder sweep

**Status: COMPLETE. 5 of 8 thresholds PASS; 3 FAIL, all three substantive.**

Source: `results/REBUILD_LOG.txt`, the **third** `EXP B1` block. The two earlier blocks are preserved
and nothing above this line is overwritten — the committed dinoL518 values were **re-derived from
scratch** and reproduce (`dinoL518_reproduces_committed_block = True`, 7/7 within 5e-3).

Script: `rebuild/B1/b1_embedder_sweep.py`, which **extends** `b1_es_error_correlation.py` rather than
replacing it. Reuses E0's cached embeddings; nothing re-embedded. **Trains nothing.**

## C1. What the committed block actually covered

Established from the code, not assumed:

| Component | Embedder-dependent? |
|---|---|
| `load_target` → the clustered array | **yes** — `dinoL518` |
| `step_cluster` → k sweep, silhouette, seed-/bootstrap-ARI | **yes** |
| `assign_clusters` → endpoint→cluster assignment | **yes** |
| per-cluster ρ | **yes** |
| cross-architecture per-cluster ρ | **yes** |
| `emit_cluster_es` → the C1 artifact | **yes** |
| `score_arch` → per-image ES, MAE, Sα, IoU | **no** — contains zero references to any embedding cache |
| **per-image ρ** | **no** — `spearman([r['es']], [r[err]])` over the score CSV alone |

**Per-image ρ needs no sweep and was not recomputed as one.** Instead it is recomputed inside every
embedder loop and asserted bit-identical, so the independence claim is tested rather than stated:

| Split | ρ(ES,MAE) | ρ(ES,1−Sα) | ρ(ES,1−IoU) |
|---|---|---|---|
| COD10K-test | **+0.7514** | **+0.3114** | **+0.2015** |
| CAMO-val | **+0.6604** | **+0.3888** | **+0.2495** |

`perimage_rho_identical_across_embedders = True`. The MAE value is unchanged from the committed block
and still matches the old package's +0.751 to four decimals.

## C2. Two latent defects in the committed script, fixed before sweeping

`fit_kmeans` cached on `(k, seed)` and `endpoint_emb` on `split` alone, while `step_correlate` and
`emit_cluster_es` called `assign_clusters` **without** a tag. With one embedder those are inert. With
three, the second and third spaces would have silently received **dinoL518's k-means fits and
dinoL518's endpoint embeddings** — and every "embedder-robust" conclusion here would have been an
artifact of reading one cache three times. Cache keys now include the tag, the tag is threaded
through, and defaults are unchanged, which is why the committed result still reproduces.

## C3. Cluster structure in all three spaces

| Embedder | principled k | silhouette peak | peak is | bootstrap ARI | seed ARI |
|---|---|---|---|---|---|
| dinoL224 | **50** | **0.1465** | interior maximum | 0.610 | 0.615 |
| dinoL518 | **75** | **0.1600** | interior maximum | 0.579 | 0.616 |
| clipL224 | **5** | **0.0568** | **AT THE GRID EDGE** | 0.953 | 0.983 |

CLIP's silhouette curve falls **monotonically** — `k5=0.0568` down to `k150=0.0357` — so the criterion
returns k=5 by hitting the grid boundary, not by finding a maximum. `THRESHOLD ... an interior
maximum, not the grid edge -> FAIL`, recorded as a FAIL.

Two consequences, neither smoothed away. CLIP's k*=5 sits **exactly on** the ≥5-cluster guard, where
Spearman over 5 points takes only a few discrete values — which is why its ρ(MAE) is exactly
**+1.0000** and its 1−Sα and 1−IoU are both exactly **+0.6000**, and why the ordering test fails there
on a *tie*, not a reversal. And the honest cross-embedder comparison is therefore at a **common k**.
**The guard was not relaxed to make this go away.**

## C4. The comparison at a common k=20

| Embedder | ρ(ES,MAE) | ρ(ES,1−Sα) | ρ(ES,1−IoU) | ratio 1−Sα/MAE |
|---|---|---|---|---|
| dinoL224 | **+0.8767** | **+0.6095** | **+0.5447** | **0.6952** |
| dinoL518 | **+0.8699** | **+0.5067** | **+0.4060** | **0.5825** |
| clipL224 | **+0.8933** | **+0.5102** | **+0.3948** | **0.5712** |

`THRESHOLD at a COMMON k=20 the ordering MAE > 1-Sa > 1-IoU holds in every embedder space -> PASS`.

At each space's own k*: dinoL224@k50 **+0.8731 / +0.4295 / +0.3202** (ratio **0.4919**), dinoL518@k75
**+0.8553 / +0.4276 / +0.2983** (ratio **0.4999**), clipL224@k5 the degenerate case above.

Across all embedder × k cells the ratio spans **min 0.4919 max 0.6952 spread 0.2033**, and
`ratio_straddles_the_0.5_boundary = True`.

## C5. How this changes our assertions

### C5.1 The wrong-objective LABEL is now doubly unstateable — effect size is all that survives

- **Before:** the committed block showed the 0.5 binary was **k**-unstable (0.4999 at k=75, 0.5825 at
  k=20).
- **Now:** it is also **embedder**-unstable. The ratio ranges 0.4919–0.6952 across three spaces and two
  k values and straddles the boundary. `THRESHOLD ... the binary label is stateable -> FAIL`.
- **Position:** the binary label is retired for good. What is robust is the **effect size and the
  ordering**: ES tracks pixel error strongly (ρ 0.855–0.893 per-cluster, 0.7514 per-image) and
  structural error **materially less well** (ρ 0.428–0.610 per-cluster, 0.3114 per-image). The ratio
  sits between roughly **0.49 and 0.70** depending on space and k — i.e. structural correlation is
  somewhere between half and seven-tenths of pixel correlation, never equal to it.
- **This is a weaker claim than the committed block implied, and it is the one the data supports.**

### C5.2 Weak cluster structure is embedder-robust, and worse in CLIP

- **Measured:** silhouette peaks **0.1465 / 0.1600 / 0.0568**. All far below 0.25;
  `THRESHOLD WEAK CLUSTER STRUCTURE is embedder-robust -> PASS`.
- **Position:** Stage C's "allocate budget over clusters" premise is undermined **regardless of
  embedder**, and CLIP is not a rescue — it is worse, with no interior peak at all. The unit of
  allocation is soft in every space E0 declared.
- **Caveat, stated:** CLIP's high ARI (0.953 bootstrap, 0.983 seed) is the small-k artifact the
  committed block already identified — 5 huge clusters reproduce trivially. It is not evidence of
  structure; its silhouette is the lowest of the three.

### C5.3 The ordering is robust; its magnitude is not

- **Measured:** MAE > 1−Sα > 1−IoU holds in **5 of 6** embedder × k cells and in **3 of 3** at the
  common k=20. The one failure is CLIP at k=5, on a tie between two 5-point Spearman values.
- **But the magnitudes move materially:** ρ(1−Sα) at k=20 is **+0.6095** in dinoL224 against **+0.5067**
  in dinoL518 — a 0.10 swing from the embedding choice alone, larger than the seed sd (±0.04–0.07).
- **Position:** report the ordering as robust and the ratio as a **range**, never a point value. Any
  document quoting a single ratio is quoting an embedder-and-k-specific number.

---

## C6. Which embedder C1 should inherit — recommendation

**Recommendation: `dinoL518`, with a mandatory sensitivity re-run in `dinoL224`.**

Three reasons that do not depend on the outcome:

1. It is the space the committed `EXP B1` block used, so C1 inherits a clustering whose ES-vs-error
   behaviour is already measured, logged and reproduced.
2. It is the only space in which the cross-architecture axis was run.
3. It has the **highest silhouette** of the three (0.1600) and a genuine **interior** peak — the least
   bad option on the only criterion that discriminates between them.

**Why the sensitivity run is mandatory rather than optional.** `clipL224` is disqualified: no interior
peak, and its k* of 5 lands on the degeneracy guard. But `dinoL224` is a legitimate alternative — an
interior peak at k=50, silhouette 0.1465, and a ratio of 0.4919 versus dinoL518's 0.4999. Those two
are close, yet they sit on opposite sides of nothing in particular, and at k=20 they differ by 0.10 in
ρ(1−Sα). Since C1 is the decisive experiment and must not re-cluster, that choice propagates. All
three per-embedder CSVs are emitted, so the re-run costs one flag.

| Artifact | k | rows |
|---|---|---|
| `out/b1_cluster_es_dinoL518.csv` | 75 | **75** ← C1 reads this |
| `out/b1_cluster_es_dinoL224.csv` | 50 | **50** ← sensitivity re-run |
| `out/b1_cluster_es_clipL224.csv` | 5 | **5** — disqualified, kept for completeness |

## C7. What the completion does not establish

- **That any of the three embedders is the *right* space.** All three have low silhouette; the choice
  is between weakly-structured options, and it is made on stated grounds, not on a strong signal.
- **The cross-architecture axis in the other two spaces.** It was run only in dinoL518. Whether
  `S2C_SO`'s inversion is embedder-specific is **not measured**.
- **Anything about CAMO at the cluster level**, in any space. 1–4 clusters clear the floor everywhere;
  it stays per-image only.
- **A k grid finer than the 9 values swept.** CLIP's true optimum may be below 5; the grid does not
  reach there, which is exactly why its "peak" is reported as a grid-edge artifact.

---
---

# B1 completion II — the allocation signal, and C1's readiness

**Status: COMPLETE. 4 of 6 thresholds PASS; 2 FAIL. One of those FAILs overturns the direction of
B1's headline claim.**

Source: `results/REBUILD_LOG.txt`, the **fourth** `EXP B1` block. Script:
`rebuild/B1/b1_allocation_signal.py`, extending both earlier B1 scripts. Nothing above is overwritten.
**Trains nothing** — inference only.

## D1. The committed blocks measured the wrong ES

`CLS.py:81-82` builds its loader on `target_root + 'Image/'` with **`gt_root=None`**, and `CLS.py:105`
computes ES there. ES is student-vs-teacher disagreement, so it requires **no ground truth** and *is*
available on the unlabeled target set at allocation time.

Both committed blocks correlated **endpoint** ES against **endpoint** error — both measured on
COD10K-test. That is a real result, but it is not the quantity Stage C allocates by. The cluster CSV
C1 consumes carried `n_target` as a *count* and **no `target_es` at all**. A C1 built on it would have
allocated by a test-set signal the pipeline does not possess.

| Metric | Value |
|---|---|
| Target images scored, no GT used | **4040** |
| Target ES (SINet/S2C) | **0.0378** ± **0.0315**, range [**0.0043**, **0.3571**] |
| Endpoint ES, for scale | **0.0439** ± **0.0406** |

## D2. The faithful correlation: target ES → endpoint error

Both aggregated over the **same** cluster partition, so the comparison is not confounded:

| Space | k | clusters | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) | ratio |
|---|---|---|---|---|---|---|
| dinoL224 | 50 | 42 | **+0.6595** | **+0.3407** | **+0.2510** | **0.5166** |
| dinoL518 | 75 | 50 | **+0.6284** | **+0.3433** | **+0.2613** | **0.5463** |
| clipL224 | 5 | 5 | **+0.9000** | **+0.3000** | **+0.3000** | 0.3333 (degenerate) |

Endpoint ES on the **identical** clusters, for direct comparison:

| Space | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) |
|---|---|---|---|
| dinoL224 | **+0.8695** | **+0.3916** | **+0.2918** |
| dinoL518 | **+0.8754** | **+0.3810** | **+0.2304** |

**The real allocation signal is materially weaker**: `rho_drop_endpointES_to_targetES_MAE` =
**+0.2100** (dinoL224) and **+0.2470** (dinoL518). And the two ES signals only moderately agree per
cluster — ρ(target ES, endpoint ES) = **0.695** and **0.5732**. They are genuinely different
quantities, not one thing measured twice.

## D3. This overturns the direction of the headline claim

The declared boundary was "wrong objective iff ρ(1−Sα) < 0.5 × ρ(MAE)". The endpoint-ES row
below is quoted from the **third** `EXP B1` block (§C4); the target-ES row is from the fourth.

| Signal | ratio, dinoL224 | ratio, dinoL518 | verdict |
|---|---|---|---|
| endpoint ES (committed, *block 3*) | 0.4919 @k* / **0.6952** @k20 | **0.4999** @k* / **0.5825** @k20 | straddles 0.5 — not stateable |
| **target ES (real signal)** | **0.5166** | **0.5463** | **both ≥ 0.5 — consistently NOT wrong-objective** |

I declared a threshold saying the boundary would *still* be unstateable on the real signal. **It
FAILED — because the boundary is stateable on the real signal, and it lands on the opposite side.**
That FAIL is informative, not a defect: my expectation was wrong.

**Revised position, and it is a real reversal of direction:**

- "ES optimises the wrong objective" is **not supported** by the signal Stage C would actually use. On
  target ES the structural correlation is **0.52–0.55** of the pixel correlation in both candidate
  spaces — above the declared boundary, consistently.
- What *is* supported, and is the finding that should carry forward: **the real allocation signal is
  only a moderate predictor of endpoint error at all** — ρ ≈ **0.63–0.66** for MAE and ≈ **0.34** for
  1−Sα, against the ρ ≈ 0.87 the committed blocks reported for MAE. The committed figure overstated
  the usable signal by about **0.21–0.25** of ρ because it was measured on the endpoint.
- So B1's contribution to the verdict changes shape: not *"ES points at the wrong error type"* but
  *"the allocation signal available at allocation time is substantially weaker than it appears when
  measured on the test set, and it ranks structural error at roughly a third"*.

The ordering MAE > 1−Sα > 1−IoU **does** hold on the real signal in both C1-candidate spaces (declared
threshold PASS). The global ordering threshold FAILs only on clipL224's k=5 tie
(1−Sα = 1−IoU = exactly +0.3000), the same 5-point quantisation as before — recorded, and the guard
was again not relaxed.

## D4. Cross-architecture gap closed

`B1_RESULTS.md` §C7 recorded that the cross-architecture axis had run only in dinoL518 and that
whether `S2C_SO`'s inversion was embedder-specific was **not measured**. It is now:

| Space | ordering holds | failures |
|---|---|---|
| dinoL224 (k=50) | **4/5** | `SINet/S2C_SO` |
| dinoL518 (k=75) | **4/5** | `SINet/S2C_SO` |
| clipL224 (k=5) | **2/5** | `SINet-v2/S2C`, `SINet/S2C`, `SINet/S2C_SO` |

`S2C_SO_inversion_by_embedder = dinoL224=True dinoL518=True clipL224=True`. **The source-only
inversion is not embedder-specific** — it reproduces in all three spaces, consistent with the
mechanistic explanation (source-only runs no consistency loss and never forwards a target image, so
its "teacher" is not an EMA of a student that learned from one).

CLIP's 2/5 is the k=5 quantisation again, not an architecture finding.

## D5. C1 readiness

| Space | ready | k | clusters (with `target_es`) | cutouts |
|---|---|---|---|---|
| dinoL518 | **True** | 75 | 75 / 75 | 4447×1024, aligned to raw pool |
| dinoL224 | **True** | 50 | 50 / 50 | 4447×1024, aligned |
| clipL224 | **True** | 5 | 5 / 5 | 4447×1024, aligned |

All three cluster CSVs now carry `target_es` and `n_target_scored` beside `n_target`. The cutout cache
(**R2**, grey-128 — the representation C1 selects over) is verified row-aligned to the raw foreground
pool in every space.

**C1 must allocate by `target_es`, not `test_es`.** Both columns are present; using `test_es` would
allocate by a signal the pipeline does not have at allocation time.

## D6. What this completion does not establish

- **Whether allocating by target ES helps.** D2 measures that the signal is moderately predictive.
  Whether acting on it changes accuracy is C1's and C3's question.
- **Seed robustness of target ES.** One final checkpoint pair per architecture; retraining deferred,
  so seed variance stays `UNVERIFIED-DEFERRED`.
- **A target-side error.** The target set has no GT by construction, so "does ES predict error *on the
  target*" is unanswerable here. The faithful correlation bridges target-side signal to endpoint-side
  error, which is the closest measurable proxy and is not the same thing.
- **Anything at cluster level for CAMO**, in any space, or for clipL224 beyond flagging its degeneracy.
- **A finer k grid.** CLIP's optimum may sit below k=5; the grid does not reach there.

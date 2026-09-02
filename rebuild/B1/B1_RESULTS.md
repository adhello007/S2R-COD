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

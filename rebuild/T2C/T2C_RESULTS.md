# T2C_RESULTS.md — is the pixel-over-structure gap specific to ES?

> Decision rule: `rebuild/T2C/PREREGISTRATION_T2C.md`, committed at `6efde9f` **before any T2-C code
> existed**. Specification: `T2C_PLAN.md`. Run: `EXP T2C` in `results/REBUILD_LOG.txt`.
> **TRAINS NOTHING** — 64,640 inference forwards, no checkpoint written, no partition fit.
>
> Dated 2026-09-11.

## §1 The answer

**The ordering generalises. The strong reading of it does not.**

The pre-registered criterion — `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)` at seed 0, B1's own committed test
(`b1_allocation_signal.py:360`) — **passes on 8 of 8 whole-image rows**, 7 of them at 10/10 k-means
seeds. Predictive entropy and ensemble disagreement behave like ES on both architectures.

So B1's finding is **not a property of ES**. It is a property of every uncertainty signal this
pipeline can compute.

**But the magnitude does not generalise, and the strong claim is not supported.** On SINet-v2,
ρ(1−Sα) sits at **+0.54 to +0.56** — substantial, not a null. "Uncertainty in COD carries no
localisation information" is **false as stated** for SINet-v2. What survives is strictly comparative
and ordinal: *pixel error is predicted better than structural error, always; structural error is
still predicted, sometimes well.*

## §2 The comparison table — whole-image aggregation (primary)

ρ at the committed seed 0, ± sd over 10 k-means seeds. 50 clusters, 3428 target images.

| arch | signal | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) | ordering | seeds | ratio |
|---|---|---|---|---|---|---|---|
| SINet | **ES** (validation row) | +0.6284 ± 0.0381 | +0.3433 ± 0.0301 | +0.2613 ± 0.0383 | PASS | 10/10 | 0.5463 |
| SINet | entropy | +0.5892 ± 0.0368 | +0.4267 ± 0.0277 | +0.3588 ± 0.0351 | PASS | 10/10 | 0.7242 |
| SINet | ensemble A0 | +0.6028 ± 0.0466 | +0.2698 ± 0.0487 | +0.1491 ± 0.0560 | PASS | 10/10 | 0.4476 |
| SINet | ensemble CSHUF | +0.5212 ± 0.0564 | +0.4006 ± 0.0459 | +0.3361 ± 0.0447 | PASS | 10/10 | 0.7687 |
| SINet-v2 | **ES** | +0.7070 ± 0.0404 | +0.5628 ± 0.0359 | +0.4591 ± 0.0315 | PASS | 10/10 | 0.7961 |
| SINet-v2 | entropy | +0.7393 ± 0.0309 | +0.5404 ± 0.0408 | +0.4070 ± 0.0395 | PASS | 10/10 | 0.7310 |
| SINet-v2 | ensemble A0 | +0.6191 ± 0.0675 | +0.5483 ± 0.0409 | +0.4540 ± 0.0451 | PASS | 9/10 | 0.8857 |
| SINet-v2 | ensemble CSHUF | +0.5576 ± 0.0690 | +0.4488 ± 0.0580 | +0.3370 ± 0.0577 | PASS | 10/10 | 0.8049 |

The **ES / SINet row reproduces B1's committed `+0.6284 / +0.3433 / +0.2613` and ratio `0.5463`
exactly** (Δ ratio = −0.0000). It is a validation row, not a result.

**The pixel-over-structure gap, `ρ(MAE) − ρ(1−Sα)`, spans +0.0708 to +0.3330.** Every value clears
the pre-registered ~0.06 resolution floor, but the smallest (SINet-v2 ensemble A0, +0.0708) only just
does, and carries the largest ratio sd in the table.

## §3 The ratio benchmark failed as a discriminator — and that vindicates the ordering rule

The pre-registration benchmarked the ratio `ρ(1−Sα)/ρ(MAE)` against **ES's committed 0.5463**, having
refused the `< 0.5` constant because ES itself fails it. That was right, but it assumed 0.5463 was
architecture-stable. **It is not:**

```
ES's OWN ratio:   0.5463 (SINet)   vs   0.7961 (SINet-v2)      shift +0.25
measured ratio sd per row: 0.052 - 0.112   (pre-registered estimate ~0.077 -- accurate)
```

A 0.25 shift in the reference signal's own benchmark, against a per-row sd of ~0.05–0.11, means the
ratio cannot separate signals **or** architectures. Every signal's ratio (0.4476–0.8857) is within
reach of ES's own architecture-to-architecture movement.

This is a stronger version of what B1 already froze as a threshold — *"on the REAL allocation signal
the 0.5 wrong-objective boundary is still not stateable"* (`b1_allocation_signal.py:376-381`),
`VERDICT_binary_is_k_stable = False`. The pre-registered decision to make the **ordering** primary and
the ratio **descriptive only** is what makes this experiment readable at all.

## §4 Boundary aggregation — the hypothesis fails, and the reason is measurable

**2 of 8 boundary rows pass.** Four go *negative*:

| arch | signal | ρ(MAE) | ρ(1−Sα) | ordering |
|---|---|---|---|---|
| SINet | ES | −0.0012 ± 0.0481 | −0.0567 ± 0.0500 | FAIL 8/10 |
| SINet | entropy | +0.2434 ± 0.0414 | +0.2492 ± 0.0540 | FAIL 6/10 |
| SINet | ensemble A0 | +0.3633 ± 0.0605 | +0.2910 ± 0.0509 | PASS 10/10 |
| SINet | ensemble CSHUF | +0.3175 ± 0.0637 | +0.3857 ± 0.0381 | FAIL 2/10 |
| SINet-v2 | ES | **−0.5485** ± 0.0745 | −0.1146 ± 0.0675 | FAIL 0/10 |
| SINet-v2 | entropy | +0.4208 ± 0.0356 | +0.4182 ± 0.0455 | PASS 8/10 |
| SINet-v2 | ensemble A0 | −0.1960 ± 0.0524 | +0.0425 ± 0.0410 | FAIL 0/10 |
| SINet-v2 | ensemble CSHUF | −0.2527 ± 0.0668 | −0.0591 ± 0.0609 | FAIL 0/10 |

**This lands outside the pre-registered three-way interpretation.** That trichotomy anticipated the
boundary predicting *neither*, *pixel only*, or *structure*. It did not anticipate signals
**inverting**. Reported as it fell, per §T2C.1.

### The measured mechanism — POST-HOC, not pre-registered

Two diagnostics, run after the fact and labelled as such:

```
per-cluster mean BAND AREA vs endpoint error   SINet   MAE +0.3695 | 1-Sa +0.0811
                                               SINetv2 MAE +0.6286 | 1-Sa +0.3673
per-cluster EMPTY-BAND fraction vs error       SINet   MAE +0.2168 | 1-Sa +0.2780 | 1-IoU +0.2674
                                               SINetv2 MAE +0.1226 | 1-Sa +0.3587 | 1-IoU +0.3223
empty bands                                    SINet 131/4040 (3.24%) | SINetv2 22/4040 (0.54%)
```

**Band area alone predicts MAE at +0.6286 on SINet-v2** — as well as any signal in §2. A whole-image
mean is effectively *uncertainty density × area*; restricting to the band and taking a **mean**
divides the area out, removing the component that carried the prediction. That is sufficient to
explain both the collapse and the sign flips.

Compounding it, images whose band is empty are **dropped** from boundary rows, and empty-band
fraction is positively correlated with every error (+0.22 to +0.36) — a selection bias against
precisely the hardest material.

**Consequence for the claim.** The boundary rows do **not** test "is uncertainty informative where
localisation lives". They test an area-normalised quantity confounded with object size and with
model confidence. The pre-registered "strongest general claim" branch is therefore **not reachable
from this design**, and is not claimed.

## §5 Ensemble sensitivity condition — fired once

Pre-registered: an A0 finding that does not survive the tight CSHUF ensemble is *a possible
weak-member artifact, not a result*.

| cell | A0 | CSHUF | outcome |
|---|---|---|---|
| SINet whole | PASS | PASS | AGREE |
| SINet **boundary** | PASS 10/10 | FAIL 2/10 | **DISAGREE → weak-member artifact, not a result** |
| SINet-v2 whole | PASS | PASS | AGREE |
| SINet-v2 boundary | FAIL | FAIL | AGREE |

The one boundary row that passed on SINet is **withdrawn** under the pre-registered rule. All four
whole-image ensemble cells agree, so the §2 result does not rest on A0's heterogeneity.

## §6 Integrity — every gate, measured

| gate | result |
|---|---|
| G1 target-side invariant | PASS; 4/4 negative controls HALT (endpoint-keyed, stem-keyed, endpoint paths, truncated) |
| G2 ES config | a=0.9 b=0.3 c=0.5, PGT unweighted, CLS on sigmoid — parsed from live `MyTrain.py` |
| G3 signal gate | 0 violations; **C1's literal ban also passes** — T2-C never reads the endpoint ES column |
| G4 unreduced-ES identity | max 4.199e-08 (SINet) / 1.178e-07 (SINet-v2), every image, tol 1e-6 |
| G5 partition identity | 4033 labels identical to the committed partition |
| G6 ES reproduction, per image | max 4.199e-08 / 1.178e-07; mean 1.968e-09 / 4.455e-09 |
| G7 ES reproduction, per cluster | 4.942e-07 (SINet); **NOT APPLICABLE** on SINet-v2 — see Addendum A1 |
| G8 harness | **bit-identical** to `b1_faithful_correlation.json`; 50 clusters, 3428 images |
| G9 scorer | Sα 0.7172156 (Δ 3.77e-07), MAE 0.0744632 (Δ 2.32e-07), tol 1e-5 |
| G10 provenance | `E0.step_independence()` unchanged, n_forbidden = 0, both T2C files in scan |
| G11 checkpoints | 16 hashed, 0 missing, 0 mismatched, **0 duplicate ensemble members** |
| G12 boundary coverage | 3.24% / 0.54% empty, both under the 5% HALT |

Two independent corroborations nobody asked for: the re-derived ES whole-image mean is
**0.03784 ± 0.03145**, reproducing B1's committed `target_ES_mean_sd = 0.0378 ± 0.0315`; and the
measured 10-seed ρ sds (0.028–0.11) bracket the pre-registered ~0.06 floor and ~0.077 ratio sd.

**One gate misfired and was corrected in scope, not substance** — G7 on the non-primary architecture.
`b1_cluster_es_dinoL518.csv`'s `target_es` column holds `SINet/S2C`'s ES for every architecture
(`b1_allocation_signal.py:283`), so on SINet-v2 it compared two different architectures' signals.
Confirmed by feeding B1's *own* committed SINet-v2 ES through the same aggregation — identical
8.754e-02 deviation. Recorded in **`PREREGISTRATION_T2C.md` Addendum A1**; §T2C.1 untouched.

## §7 What this does and does not license

**Licensed.** The pixel-over-structure ordering in B1 is a property of uncertainty signals for COD
generally, not of ES. Three signals × two architectures, one measurement structure, 8/8 under the
pre-registered criterion. Combined with T2's WITHIN NOISE result on trained accuracy, this is a
**strong prior** that uncertainty-guided allocation will not buy structural accuracy for COD.

**Not licensed.**

- **Not causal.** T2-C is correlational. It cannot upgrade into "uncertainty guidance fails in
  training" for signals T2 did not train.
- **Not "no localisation information".** ρ(1−Sα) reaches +0.56 on SINet-v2. The claim is ordinal.
- **Not a boundary result.** §4's confound means this design cannot test the boundary question.
  Answering it needs an area-controlled statistic (e.g. partialling out band area, or a band *sum*
  rather than mean) — new work, separately pre-registered.
- **One endpoint.** COD10K-test only; NC4K has no DINOv2 cache, is not a B1 split, and has no
  per-cluster error columns.
- **Ensemble rows are weakest.** n=3, heterogeneous members, optimisation-stochasticity only, and
  the members are not the model whose error is the endpoint column (S2C teacher Sα 0.717216 matches
  no A0 member).
- **Sub-0.06 ρ differences between signals are not interpreted.**

## §8 Artifacts

```
rebuild/T2C/out/t2c_table.csv               the section-2/4 matrix, primary + robustness rows
rebuild/T2C/out/t2c_correlations.json       full per-seed record, perm p and bootstrap CI at seed 0
rebuild/T2C/out/t2c_preflight.json          all pre-signal gates
rebuild/T2C/out/t2c_signals_<arch>.csv      4040 rows x 20 signal columns, per architecture
rebuild/T2C/out/t2c_signal_meta_<arch>.json G1/G4/G12 evidence per architecture
```

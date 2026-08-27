# Stage C — red-team audit of `STAGE_C_MEASUREMENTS.md`

Adversarial audit. Every claim below was attacked with a measurement designed to break it, and is
reported CONFIRMED/HOLDS only where the attack failed. Three of the five locked decisions moved.
Two numbers in `STAGE_C_MEASUREMENTS.md` were my own errors and are corrected here.

All runs cited were executed in this session. Nothing is quoted from the prior documents without
independent recomputation from raw artifacts.

**Executed-run index** (referenced as `[R#]` below):

| ref | what ran | artifacts |
|---|---|---|
| R1 | recompute all 6 noise-floor runs from prediction files with `Eval/metrics.py` | `scratchpad/noisefloor/audit6.json` |
| R2 | ES + per-image Sα for 4 independent seeds + reproduction | `scratchpad/locked2_scores.json` |
| R3 | chance-level acceptance baseline, binomial test, 2 embedders × k∈{20,50} | stdout |
| R4 | held-out generation split (rank on half A, measure on half B) | stdout |
| R5 | val-only ES correlation + permutation p (5000 shuffles), k∈{5,8,10,15,20,50} | stdout |
| R6 | coverage-term correlation at k∈{20,50,100} × {val,test} | stdout |
| R7 | linear probe with random null control + JPEG-75 + darkening controls | stdout |
| R8 | precision/recall with random-split ceiling + raw-HKU-IS baseline | stdout |
| R9 | per-arm sampling arithmetic | stdout |
| R10 | effect-size translation | stdout |

---

## 0. Premise correction — the noise floor was not missing

**Attempted falsification of the audit brief's own premise** ("the noise floor was never run… right
now it is a guess").

**Evidence.** `scratchpad/noisefloor/` contains six completed runs: `train_s{42,43,45,46}.log` and
`train_rep{B,C}.log`, all terminating at `Epoch Num: 039/040`; `pred_*` directories each holding
2026 predictions; `snap_*` each holding 17 checkpoints. `[R1]` recomputed every run from its
prediction files using the repo's own `Eval/metrics.py` at the `Eval/MyEval.py:33-39` convention;
`s42/s43/s45/s46` reproduce `STAGE_C_MEASUREMENTS.md` §3 exactly, and `Result/SINet/S2C` reproduces
the recorded Sα 0.7172 / MAE 0.0745 (`Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`).

The stale "unmeasured noise floor" text is in the *prior review* file, not the measurements doc.

**Verdict: the premise is FALSIFIED.** §3 was completed. What *is* missing is a 5th **distinct**
seed — see §D3.

---

## 1. LOCKED: λ_cov = 0 (drop the coverage term)

### 1(a) Attack: the ρ(ES, true-error) = +0.82 result was measured on test. Does it survive on CAMO-val alone, or collapse to too-few-clusters?

**How I attacked it.** `[R5]` Recomputed ρ(ES_c, MAE_c) on CAMO-val only, sweeping k∈{5,8,10,15,20,50}
to find a k where val has both enough clusters and enough images per cluster, with a 5000-shuffle
permutation p-value (Spearman's asymptotic p is unreliable at n≈9).

**What I found.**

| k | split | clusters | min imgs/cluster | ρ(ES_c, MAE_c) | perm p |
|---|---|---|---|---|---|
| 10 | val | 6 | 11 | +1.000 | 0.0024 |
| **15** | **val** | **9** | **8** | **+0.967** | **0.0002** |
| 20 | val | 9 | 8 | +0.800 | 0.0060 |
| 50 | val | 6 | 8 | +0.943 | 0.0108 |
| 15 | test | 15 | 56 | +0.861 | 0.0000 |
| 20 | test | 20 | 26 | +0.857 | 0.0000 |

Val-only is significant at k=10–20, independent of test. The doc's own caveat (6 clusters at k=50)
is resolved by lowering k: k=15 gives 9 val clusters at p=0.0002.

**Verdict: HOLDS.** The attack failed. λ_cov=0 does not rest on test-set correlations.

### 1(b) Attack: was the coverage term's ρ = +0.006 an artifact of the specific k or embedder?

**How I attacked it.** `[R6]` Recomputed ρ(coverage_c, true MAE_c) at k∈{20,50,100} on both splits,
plus the combined d(c) at λ_cov=0.05.

**What I found — the coverage term is worse than "noise".**

| k | ρ(cov, MAE) **val** | ρ(cov, MAE) test | ρ(ES) val | ρ(ES + 0.05·cov) val |
|---|---|---|---|---|
| 20 | **−0.717** | +0.006 | +0.800 | **−0.733** |
| 50 | −0.200 | +0.006 | +0.943 | −0.200 |
| 100 | −0.600 | +0.070 | +1.000 | −0.300 |

On the well-powered split (test, 20–86 clusters) it is +0.006…+0.070, i.e. noise. On val it is
*anti*-predictive, and adding it flips a +0.800 signal to −0.733. Sign is unstable; magnitude is
zero-to-harmful in every configuration.

**Label-free corroboration** (needs no ground truth at all): ρ(acceptance, n_s(c)) =
+0.762/+0.734/+0.873 for DINOv2-L/518 at k=20/50/100, and +0.893/+0.918/+0.878 at L/224 `[R5-R6]`.
Coverage-ranking is inverse-ranking by feasibility, provably, without labels.

**Verdict: HOLDS — STRENGTHENED.** The doc understates this: the term is not merely uninformative,
it destroys a valid signal, and the justification does not require labelled data.

---

## 2. LOCKED: ES-disagreement is a valid deficiency signal (ρ ≈ 0.82)

### 2(a) Attack: it was measured with the reproduction's own checkpoints. Is the correlation an artifact of that one training run?

**How I attacked it.** `[R2]` Recomputed ES with `Stu_40.pth` + `Tea_epoch_best.pth` from four
**independent** training runs (`snap_s42/43/45/46`, different seeds, separate processes) plus the
reproduction, using the exact `CLS.py:105`/`CLS.py:138` convention — `ESLoss(a=0.9, b=0.3,
use_weighted_bce=False)` from `Src/utils/tool.py:45-77` on `stu.sigmoid()`, `tea.sigmoid()` at
352×352.

**What I found.**

| run | ES mean | per-image ρ vs MAE | per-cluster ρ vs MAE (k=20) |
|---|---|---|---|
| s42 | 0.0612 | +0.792 | +0.917 |
| s43 | 0.0529 | +0.778 | +0.862 |
| s45 | 0.0591 | +0.787 | +0.937 |
| s46 | 0.0461 | +0.742 | +0.944 |
| repro | 0.0439 | +0.751 | +0.857 |
| **mean ± sd** | — | **+0.770 ± 0.022** | **+0.903 ± 0.041** |

Cross-run stability of the ES-based cluster *ranking* — the quantity d(c) actually uses: ρ between
every pair of runs is +0.784 … +0.941.

Secondary observation: the ES *scale* varies 0.0439–0.0612 across runs (40% spread), so any absolute
ES threshold would not transfer between runs. Only the ranking is portable. This matters if Stage C
ever uses a fixed cutoff rather than a rank-based allocation.

**Verdict: HOLDS.** The attack failed. d(c) is reproducible across independent runs.

### 2(b) Attack: ES tracks MAE (+0.75) but not IoU (+0.24). If the headline metric is Sα, does ES predict the error that matters?

**How I attacked it.** `[R2]` Extracted per-image Sα via `Eval/metrics.py:111` (`Smeasure.sms`),
validated against the aggregate: my per-image mean for s42 is 0.70222, matching
`Smeasure.get_results()` exactly `[R1]`. Then correlated ES against (1−Sα).

**What I found.**

| | vs MAE | vs (1−Sα) |
|---|---|---|
| per-image, mean of 5 runs | +0.770 ± 0.022 | **+0.334 ± 0.080** |
| per-cluster k=20 | +0.903 ± 0.041 | **+0.645 ± 0.043** |
| per-cluster k=50 | +0.844 | **+0.398** |

Per-run at k=50 vs (1−Sα): s42 +0.579, s43 +0.379, s45 +0.343, s46 +0.335, repro +0.354.

**Verdict: WEAKENED.** ρ=0.82 licenses "ES ranks clusters by pixel-calibration error." It does **not**
license "ES predicts where the model is bad" in Sα — that is +0.645 at k=20 and collapses to +0.398
at k=50. An Sα-headlined paper allocating by ES is optimising a proxy correlated 0.40–0.65 with its
own objective. `STAGE_C_MEASUREMENTS.md` §4 overstates what this signal buys.

---

## 3. LOCKED: targeting is feasible (acceptance 0% → 26.67%, DINOv2 k=20, 518px)

### 3(a) Attack: at k=20 there are only 20 broad clusters. Is acceptance high simply because clusters are big? What is chance?

**How I attacked it.** `[R3]` Computed the correct chance baseline: for each cluster c, the rate at
which generations land in c *without* steering, p_land(c) = n_s(c)/Σn_s. Averaged over the same
deficient-12 the budget targets, plus a pooled one-sided binomial test of observed successes against
that chance rate.

**What I found.**

| embedder / k | observed | chance (mean p_land) | lift | binomial p |
|---|---|---|---|---|
| **L/518 k=20** | **26.67%** | **1.63%** | **16.4×** | 1.3e-112 |
| L/518 k=50 | 11.46% | 0.32% | 35.6× | 2.2e-65 |
| L/224 k=20 | 6.46% | 0.16% | 39.2× | 1.6e-38 |
| L/224 k=50 | 3.12% | 0.05% | 59.6× | 5.1e-22 |

All-cluster: 36.62% observed vs 5.00% uniform at k=20 (7.3× lift); 29.80% vs 2.00% at k=50 (14.9×).

**Verdict: HOLDS.** The attack failed decisively. Steering is real, not a big-bucket artifact.

### 3(b) Attack: the deficient-12 ranking is computed from the same generations whose acceptance is then measured. Does it survive on held-out generations?

**How I attacked it.** `[R4]` Random 50/50 split of the 4447 generations. Rank clusters by deficiency
using **only half A**'s n_s; measure acceptance using **only half B**'s cutouts and their generations.

**What I found.**

| embedder / k | held-out | in-sample | chance (half B) | lift |
|---|---|---|---|---|
| **L/518 k=20** | **20.62%** | 28.12% | 1.68% | 12.3× |
| L/518 k=50 | 10.83% | 13.75% | 0.41% | 26.3× |
| L/224 k=20 | 5.00% | 5.83% | 0.20% | 24.7× |
| L/224 k=50 | 2.92% | 3.33% | 0.07% | 38.9× |

~27% relative in-sample optimism, confirmed.

**Verdict: WEAKENED but HOLDS.** The honest headline is **20.62%**, not 26.67%. Still feasible:
B=1000 → 4,850 generations → 2.3 GPU-h/cycle-arm at the measured 1.73 s/image. The decision stands
with a corrected number; `STAGE_C_MEASUREMENTS.md` §1 must be revised.

---

## 4. LOCKED: A/B/C is a clean, fixed-compute comparison (9,867 identical steps)

### 4(a) Attack: identical step count is not identical compute-on-signal. How many times per epoch is a targeted image actually seen vs a random one? Is "fixed compute" hiding an under-sampling that throttles the intervention?

**How I attacked it.** `[R9]` Computed per-arm sampling from `MyTrain.py:306-307`
(`total_step = min(len(source_loader), len(target_loader))`), `MyTrain.py:51` (`zip`), and
`Src/utils/Dataloader.py:206` (`shuffle=True`, so each epoch draws a fresh uniform subset).

**What I found.**

| arm | \|Ds\| | len(src) | total_step | imgs seen/epoch | **P(a given image seen)** | added-block presentations/epoch |
|---|---|---|---|---|---|---|
| A (none) | 6824 | 427 | 253 | 4048 | **0.593** | 0 |
| B (+1000 random) | 7824 | 489 | 253 | 4048 | **0.517** | 517.4 |
| C (+1000 targeted) | 7824 | 489 | 253 | 4048 | **0.517** | 517.4 |

B and C are identical in every column. The loader cannot distinguish a targeted image from a random
one — both are sampled uniformly at 0.517 — so there is **no arm-specific throttle** between B and C.
But arm A sees each of its images 0.593× per epoch against 0.517× for B/C.

**Verdict: HOLDS for B-vs-C. FALSIFIED for A-vs-B.** Arm A confounds "1000 more images" with "every
image gets 13% less exposure," so it is not a clean control. Only B-vs-C is a clean contrast; A must
be dropped or re-scoped (e.g. arm A padded with 1000 duplicate existing images to equalise |Ds|).

### 4(b) Attack: does the fork structure leak arm identity? Do model_ema, global step, and best-model tracking reset? Does any cached CLS file carry a per-arm signature?

**How I attacked it.** Read `MyTrain.py:245-291` line by line for state crossing the iteration
boundary, and checked what sits outside the loop.

**What I found.** Inside the loop: `MyTrain.py:250-262` rebuilds `model` and `model_ema` from scratch;
`:278` re-copies student→teacher; `:282` constructs a fresh `Adam`; `:285-286` fresh `ES_Loss` /
`PGT_Loss`; `:288-290` resets `global_step`, `best_teamae`, `best_epoch`. Outside the loop: only
`set_random_seed` at `MyTrain.py:242` and `torch.cuda.set_device` at `:240`. Forked arms are separate
processes seeded identically, so even that does not differ. CLS runs once per seed *before* the fork,
so its output cannot carry an arm signature.

**Verdict: HOLDS.** No leak. One design requirement this exposes: Stage C must write each arm's pool
to its own copy and never mutate the shared CLS output — and note `CLS.py:16-17` derives its path
from `source_root` alone and `rmtree`s it at `:21`/`:27`, so the arm tag must be threaded through.

---

## 5. LOCKED: the generator ceiling is real (AUC 0.999 separable, 54% recall)

**First: a bug in my own prior work.** `STAGE_C_MEASUREMENTS.md` §2's "real-vs-real" null control and
its precision/recall ceiling were computed by splitting the target features in **sorted-filename
order**. That put 2016 COD10K images in half one and 1017 COD10K + all 1000 CAMO in half two — the
"null control" was separating two different datasets. Both prior numbers (the AUC 0.8888 null and the
0.893/0.871 ceiling) are wrong. Redone below with random splits.

### 5(a) Attack: AUC 0.999 real-vs-generated is expected for almost any generator under any strong embedder. Is it evidence of a problem, or a truism?

**How I attacked it.** `[R7]` Added three controls: a *random*-split real-vs-real null; real vs the
same real images JPEG-75 recompressed; real vs the same real images darkened 20 levels (the shift I
had earlier claimed as the mechanism); and real target vs raw HKU-IS as an "two ordinary different
datasets" reference.

**What I found.**

| comparison | accuracy | AUC |
|---|---|---|
| real vs LAKE-RED (the doc's claim) | 0.9827 | 0.9989 |
| real vs real, **random** split (true null) | 0.5240 | **0.5289** |
| real target vs **raw HKU-IS** (two ordinary datasets) | 0.9367 | **0.9831** |
| real vs real, **JPEG-75 recompressed** | 0.8905 | **0.9380** |
| real vs real, **darkened 20 levels** | 0.3640 | 0.3204 |

The protocol is sound — the true null is 0.529. But AUC ≈0.98 is what *any* two different image
distributions give, and mere JPEG recompression of the identical images gives 0.938. AUC 0.9989
establishes "these are different distributions," which nobody disputes.

Additionally, the darkening control (AUC 0.32, Cohen's d 0.14) **refutes my earlier mechanistic
claim** that LAKE-RED's ~20-level background darkening drives the separation. DINOv2 is essentially
invariant to that shift.

**Verdict: WEAKENED to near-vacuous as evidence.** A reviewer will dismiss it. The finding must be
restated as a *consequence* — ρ(acceptance, n_s(c)) = +0.92, i.e. the style difference is what makes
coverage-counting inverse-ranked by feasibility — not as separability.

### 5(b) Attack: is 54% recall low relative to anything? Without a baseline, is the "ceiling" claim comparative or absolute?

**How I attacked it.** `[R8]` Recomputed with a random-split ceiling, and added the one baseline that
matters and was missing: the **un-generated HKU-IS source LAKE-RED starts from** (`Dataset/Source/
HKU-IS_raw/imgs`, embedded fresh with the same DINOv2 L/224 pipeline).

**What I found.**

| | precision | recall | recall as % of ceiling |
|---|---|---|---|
| **raw HKU-IS (pre-LAKE-RED)** | 0.649 | **0.745** | **79.3%** |
| **LAKE-RED output** | 0.691 | **0.466** | **49.6%** |
| real-vs-real ceiling (random split) | 0.946 | 0.939 | — |

**Verdict: FALSIFIED AS STATED, and the corrected result is worse for the pipeline.** The "54% of
achievable" figure is wrong — it is 49.6%, because the ceiling was understated (0.871 vs the true
0.939). More importantly the doc frames generation as *limited*; the measurement says generation is
**destructive**: LAKE-RED takes a source with recall 0.745 and returns one with 0.466, a **37%
relative loss of target-manifold coverage**, buying only +0.042 precision. The claim is comparative,
the baseline now exists, and it points the opposite way from the doc's framing.

---

## (a) Noise-floor numbers and the effect-vs-2σ verdict

`[R1]`, independently recomputed from prediction files with `Eval/metrics.py`:

| grouping | n | σ(Sα) | 95% CI on σ(Sα) | σ(Fβw) | σ(MAE) |
|---|---|---|---|---|---|
| distinct seeds (42,43,45,46) | 4 | 0.00286 | [0.00162, 0.01065] | 0.00757 | 0.00477 |
| same seed 42 (orig, repB, repC) | 3 | 0.00229 | [0.00119, 0.01437] | 0.00980 | 0.00281 |
| **ALL runs = arm-run variance** | **6** | **0.00356** | **[0.00222, 0.00872]** | 0.00844 | 0.00388 |

Per-run Sα: 0.6961, 0.6971, 0.7005, 0.7016, 0.7022, 0.7058.

**`STAGE_C_MEASUREMENTS.md` §3's headline σ = 0.00286 uses the wrong grouping.** An arm *is* one run,
so its variance includes seed choice *and* training nondeterminism: **σ = 0.00356, 2σ = 0.00712**.

σ from 4 distinct seeds is barely an estimate — the 95% CI spans a 6.6× range. n=6 narrows it to
3.9×. A 5th distinct seed could not be run (see §D3).

### Effect-vs-2σ — the number

`[R10]`, assumption chain explicit so it can be attacked:

| input | value | source |
|---|---|---|
| σ(Sα), arm-run | 0.00356 | measured `[R1]`, n=6 |
| Cohen's d, real COD vs LAKE-RED | 4.70 | measured, DINOv2 L/224 probe axis |
| Cohen's d, arm-C block vs arm-B block | 0.10 | measured, stable over k∈{20,50}, T∈{0.005…0.05} |
| response anchor: MT → Ours | +0.0142 Sα | reproduction, 0.7030 → 0.7172 |
| cause of anchor | CLS added 2377 real target images = 34.8% of the new pool | measured |

Anchor pool-mean shift toward target = 0.348 × 4.70 = 1.637 SD ⇒ response rate **0.00867 Sα per SD**.

Arm B → C pool-mean shift = (1000/7824) × 0.10 = **0.01278 SD**.

> **Predicted Δ Sα = 0.01278 × 0.00867 = 0.000111 Sα = 0.031 σ.**
> **2σ = 0.00712. Arm C needs 64× the linear response rate to clear it.**

Inverse check: to reach 2σ the added block would need Cohen's d = **7.09**, while the *entire*
real-vs-LAKE-RED gap is d = **4.70**. Arm C's 1000 images would have to differ from arm B's by 1.5×
the real-vs-synthetic gap itself — unreachable inside the generator's output space.

Secondary prediction, same model: arm B vs arm A moves the pool from 34.8% → 30.4% real, a 0.209 SD
shift *away* from target ⇒ Δ Sα ≈ **−0.0018 (−0.51σ)**. Adding 1000 synthetic images is predicted to
slightly **hurt**.

**VERDICT: a positive allocation claim is NOT admissible.** The expected effect is 0.031σ against a
2σ bar.

**Robustness to σ.** The verdict does not depend on which σ is used: at σ=0.00229 the effect is
0.048σ; at the CI upper bound σ=0.00872 it is 0.013σ. Both branches give a null. The direction hinges
on **d = 0.10**, not on σ.

---

## (b) The five locked decisions, post-audit

| # | locked decision | post-audit status | what happened |
|---|---|---|---|
| 1 | **λ_cov = 0** | **HOLDS — STRENGTHENED** | Survived the test-peeking attack (val-only k=15: ρ=+0.967, perm p=0.0002). Coverage is worse than noise — anti-predictive on val (−0.717), and it flips a +0.800 signal to −0.733. Label-free defence ρ(acceptance, n_s)=+0.73…+0.92 needs no ground truth. |
| 2 | **ES is a valid deficiency signal** | **(a) HOLDS / (b) WEAKENED** | Replicates across 4 independent runs (+0.903±0.041), rankings agree ρ=0.78–0.94. But predicts Sα at only +0.645 (k=20) / +0.398 (k=50) / +0.334 per-image. Does not license "predicts the error that matters." |
| 3 | **Targeting is feasible (0%→27%)** | **WEAKENED but HOLDS** | 16.4× above chance, p=1.3e-112 — the coarse-cluster attack failed. But held-out generations give 20.62%, not 26.67%. Corrected number, decision intact. |
| 4 | **A/B/C is fixed-compute** | **(a) FALSIFIED for A-vs-B / HOLDS for B-vs-C** | B and C identical (P(seen)=0.517, 517 presentations/epoch). Arm A sees each image 0.593× vs 0.517× — not a clean control. No fork leak. |
| 5 | **The generator ceiling is real** | **(a) WEAKENED to near-vacuous / (b) FALSIFIED AS STATED** | AUC 0.999 is a truism (JPEG-75 gives 0.938; two ordinary datasets give 0.983). Recall is 49.6% not 54% (ceiling was understated). And raw HKU-IS scores recall 0.745 vs LAKE-RED's 0.466 — generation *destroys* 37% of coverage. |

---

## (c) The single most likely reason the committed direction still fails

**Both headline metrics of the characterization paper have collapsed — one into a truism, the other
into a finding about a single tool.**

AUC 0.9989 is not evidence: JPEG recompression of the same images gives 0.938 and two ordinary
different datasets give 0.983 `[R7]`. And the recall result, once correctly measured against the
right baseline, says "LAKE-RED reduces target-manifold coverage by 37% relative to its own input"
`[R8]` — a negative result about one generator, not a general claim about generation-in-the-loop.

Strip those two and what remains is: a deficiency signal that is valid for MAE (+0.90) but weak for
the headline metric (+0.40–0.65); a decisive negative on the obvious coverage correction (λ_cov=0);
and a measured noise floor. That is a solid workshop paper and a thin main-conference one.

The one experiment that converts diagnosis into contribution has never been run and cannot be run
read-only: **widen the conditioning channel and show the prescription is causal** — concatenate a
target-cluster embedding into BKRA's cross-attention at
`LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1579` and show acceptance *and* recall both rise. Without
it the paper describes a failure; with it, it prescribes a fix.

**The single fatal measurement, and it has been run.** `d ≈ 0.10`, the arm-C-vs-arm-B block shift. If
it were d ≳ 2 the allocation claim would be live. It is measured at 8 settings (k∈{20,50} ×
T∈{0.005,0.01,0.02,0.05}), all in 0.084–0.099. Confirmed run, not deferred. Newly second-most fatal:
raw-HKU-IS recall 0.745 > LAKE-RED 0.466 `[R8]`, which undercuts the premise that generation improves
the source pool at all.

---

## (d) What we are committing to on faith rather than measurement

| # | item | status | why it matters |
|---|---|---|---|
| 1 | **Linearity** of the pool-shift → Sα response in the effect translation | ESTIMATED — one anchor point (MT→Ours) | The only real escape hatch. If targeted data is superlinear, 0.031σ is an underestimate. Note the anchor adds *real target-domain supervision*, which arm C does not, so the rate is if anything generous to arm C. |
| 2 | **σ for the arm pool.** All 6 runs used the 4447-image HKU-IS pool; arms use ~7824 with 30–35% real content | UNVERIFIED | σ may differ under a different pool size and composition. |
| 3 | **A 5th distinct seed** | NOT RUN — plan mode forbids non-readonly actions and training writes checkpoints | σ from 4 distinct seeds has a 95% CI spanning 6.6×. |
| 4 | **d = 0.10 as a sufficient summary** of the arm-C intervention | UNVERIFIED beyond the mean | It is a *mean* shift. Higher-moment differences (variance, coverage) are unmeasured and are the one way the effect could exceed prediction. |
| 5 | **Generator-side conditioning ablation** | NEVER RUN | The paper's prescriptive claim rests entirely on it. |
| 6 | **BKRA caching speedup (~12–30%)** | UNVERIFIED — never timed | Cost claim only; not load-bearing. |
| 7 | **In-loop Stage C acceptance at k=20/518** | UNVERIFIED | Acceptance was measured on pre-existing generations, never inside a live loop with fresh sampling. |
| 8 | **ES → Sα sufficiency** | MEASURED AND WEAK (+0.40–0.65) | Allocation would optimise a proxy correlated 0.40–0.65 with the objective. Committing anyway. |
| 9 | **Stage C's write path preserves Image/GT sort-parity** | Design requirement, not a verified property | `Src/utils/Dataloader.py:39-50` silently drops pairs whose sizes differ, after only a length assert. |

---

## Corrections required to `STAGE_C_MEASUREMENTS.md`

1. §1 — acceptance headline: **20.62%** (held-out), not 26.67% (in-sample).
2. §2 — delete the "real-vs-real ceiling 0.893/0.871"; correct to **0.946/0.939** (random split).
3. §2 — recall is **49.6%** of achievable, not 54%.
4. §2 — replace the AUC framing: it is near-vacuous. Lead with **raw HKU-IS recall 0.745 → LAKE-RED
   0.466**.
5. §2 — retract the claim that the ~20-level darkening drives the style axis (control: AUC 0.32).
6. §3 — planning σ is **0.00356** (arm-run, n=6), not 0.00286.
7. §4 — state explicitly that ES predicts Sα at +0.40–0.65, not +0.82.
8. §5/§6 — arm A is not a clean control (exposure 0.593 vs 0.517); drop or pad it.

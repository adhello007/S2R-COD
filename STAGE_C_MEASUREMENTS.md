# Stage C — DINOv2 re-measurement and direction decision

Follow-up to `hazy-launching-eclipse.md`. That review's load-bearing numbers used InceptionV3-2048
because `timm`/`transformers` were absent. This document re-runs them under DINOv2 and adds the
noise-floor, deficiency-validation, and arm-design measurements.

**Headline: two of my prior conclusions change.** The "~0% acceptance, Option C is dead" finding was
substantially an artifact of the weak embedder and is **reversed** at low k / native resolution. The
"ES-disagreement measures instability, not error" concern is **refuted** — ES predicts true error at
ρ=+0.82. What survives, and hardens: the coverage term is noise and actively harmful, and the
achievable arm-C effect is tiny.

## Environment

Installed into the existing `LAKE-RED/.venv` (torch 2.11.0+cu128, py 3.12.3): **`scikit-learn
1.9.0`** (+ `threadpoolctl 3.6.0`, `narwhals 2.25.0` as transitive deps). Nothing else — `timm
1.0.28` and `transformers 5.15.1` were already present, so DINOv2 needed no new model library.

DINOv2 weights via **timm**, from the HF hub:
- **`vit_large_patch14_dinov2.lvd142m`** — 304M params, embed_dim 1024, `hf_hub_id
  timm/vit_large_patch14_dinov2.lvd142m`. **Primary**, because it is the strongest DINOv2 available
  short of ViT-g and because a *stronger* embedder is the adversarial choice here: if targeting
  fails under the best available features, that is a property of the generator, not of the metric.
- `vit_base_patch14_dinov2.lvd142m` — 87M, embed_dim 768. Model-size robustness check.

Pooling: CLS token, L2-normalized (patch-mean gave the same ordering; not reported separately).
Resolutions: **224** for the sweep and **518 (native)** for the headline, via `img_size=`, since
timm hard-asserts the pretrained 518 input (`timm/layers/patch_embed.py:121`). The 7
test-identical target images from A8 are excluded in-memory before k-means (4033 kept of 4040);
no files were deleted.

---

## 1. Acceptance re-measurement — the primary gate

Same procedure as before: k-means on the target images; for each cluster take the N=40 cutouts
nearest its centroid; look up where their **real, already-generated** LAKE-RED outputs land; accept
if the landing cluster is the intended one. Now over all 4447 cutouts (the InceptionV3 run used
2000), which is strictly more favourable to the method.

Acceptance in the **12 most coverage-deficient clusters** — i.e. where a `−λ_cov·log(n_s/n_t)` term
sends the budget:

| embedder | k=20 | k=50 | k=100 | all-cluster mean (k=50) | zero-kept clusters (k=50) |
|---|---|---|---|---|---|
| InceptionV3-2048 | ~0% | **0.00%** | 0.00% | 6.7% | 26/50 |
| DINOv2 ViT-B/14 @224 | 14.58% | 2.50% | 0.42% | 27.6% | 6/50 |
| DINOv2 ViT-L/14 @224 | 6.46% | 3.12% | 0.42% | 24.6% | 5/50 |
| **DINOv2 ViT-L/14 @518** | **26.67%** | **11.46%** | 3.96% | **29.8%** | **2/50** |

Compute for B=1000 in the deficient clusters, at the measured 1.73 s/image aggregate:

| embedder / k | acceptance | generations | GPU-h per cycle-arm |
|---|---|---|---|
| InceptionV3, k=50 | 0.00% | ∞ | infeasible |
| DINOv2 L/518, k=50 | 11.46% | 8,726 | 4.2 |
| **DINOv2 L/518, k=20** | **26.67%** | **3,750** | **1.8** |

The inverted-competence profile (works only where already saturated) is still present but its
severity is strongly k- and resolution-dependent — deficient-12 vs saturated-4 acceptance:

| | k=20 | k=50 | k=100 |
|---|---|---|---|
| InceptionV3 | — | 0.00% vs 82.5% (∞×) | 0.00% vs 76.9% (∞×) |
| DINOv2 L/518 | 26.67% vs 41.2% (**1.5×**) | 11.46% vs 82.5% (7.2×) | 3.96% vs 73.1% (18×) |

**VERDICT (1): REVERSES the prior finding at k=20 / native resolution, confirms it at k=100.**
DINOv2 lifts deficient-cluster acceptance from 0.00% to 26.67% (k=20, 518) — feasible at 1.8
GPU-h/cycle-arm. My prior "Option C is dead on acceptance" was embedder-limited and I was wrong to
state it that strongly. The inverted profile survives but is mild at k=20 (1.5×). Rejection
sampling is viable **if and only if** k is small and features are native-resolution DINOv2.

---

## 2. Distribution gap, occupancy collapse, and the style axis

| | InceptionV3 | DINOv2 L/224 | DINOv2 L/518 |
|---|---|---|---|
| TV(target, synth occupancy) k=20 | 0.701 | 0.513 | **0.336** |
| TV k=50 | 0.706 | 0.583 | **0.507** |
| TV k=100 | 0.703 | 0.618 | 0.551 |
| largest synth cluster, k=50 | 1742 (39%) | 1237 (28%) | 958 (21.5%) |
| empty-for-synth, k=100 | 17/100 | 14/100 | **1/100** |
| median n_s vs n_t, k=50 | 6 vs 80 | 6 vs 60 | 22 vs 61 |
| edge-dweller ratio k=50 | 1.11 | 1.32 | **1.39** |

Occupancy collapse is materially less severe under DINOv2 at native resolution (TV 0.507 vs 0.706;
1 empty cluster vs 17). But the **edge-dweller gap got worse**, not better: synthetic images sit
1.29–1.52× further from their assigned centroid than target images do, versus 1.07–1.15× under
InceptionV3. In a more semantic space the synthetic pool is *more* clearly a separate manifold that
gets assigned to target clusters without living in them.

**Linear probe, real-COD (4033) vs LAKE-RED output (4447)**, logistic regression, 70/30 split:

| embedder | accuracy | AUC | Cohen's d on the probe axis |
|---|---|---|---|
| DINOv2 ViT-L/14 @224 | 0.9827 | **0.9989** | **4.70** |
| DINOv2 ViT-B/14 @224 | 0.9843 | 0.9988 | 4.62 |
| DINOv2 ViT-L/14 @518 | 0.9811 | 0.9985 | 4.35 |

Invariant to model size and resolution. A *linear* probe separates real from generated at AUC
0.9985–0.9989, with the class means 4.35–4.70 pooled SDs apart. The "LAKE-RED look" is not a
subtle artifact — it is a dominant, linearly-decodable direction in DINOv2 space.

**Generative precision/recall** (Kynkäänniemi et al. 2019), DINOv2 L/224, k=5 NN manifold:

| | precision | recall |
|---|---|---|
| LAKE-RED output vs target | 0.691 | **0.466** |
| real-vs-real split (ceiling) | 0.893 | 0.871 |

LAKE-RED reaches 77% of achievable precision but only **54% of achievable recall** (0.466/0.871).
It is realism-good and diversity-poor: roughly half the target manifold is unreachable from any
HKU-IS foreground.

**VERDICT (2): the coverage term still measures style, not coverage. λ_cov must be 0.** TV improves
to 0.507 but a d=4.35 linear style axis dominates the space in which `n_s(c)` is counted, and §4
shows the term has literally zero correlation with true error. See §4 for the decisive number.

---

## 3. Noise floor

4 seeds (42/43/45/46), SINet `--method ours --iteration 1`, 39 epochs, 253 steps/epoch, 2 per GPU,
each ~1 h 50 m. Evaluated on COD10K-test with the repo's own `Eval/metrics.py` at the exact
`MyEval.py:33-39` convention. Patch: 2 lines in a scratchpad copy of `MyTrain.py` (`--seed` argparse
+ `set_random_seed(opt.seed)` replacing the hardcoded 42 at `MyTrain.py:242`); default 42 so existing
commands stay byte-identical. `worker_init_fn` (the missing fix at `Dataloader.py:200-219`)
deliberately NOT applied — it changes the augmentation distribution, and the goal was sigma of the
pipeline *as it exists*.

| seed | Sα | Fβw | MAE | meanEm | meanFm |
|---|---|---|---|---|---|
| 42 | 0.7022 | 0.4333 | 0.0926 | 0.7221 | 0.5188 |
| 43 | 0.7005 | 0.4474 | 0.0901 | 0.7226 | 0.5226 |
| 45 | 0.6961 | 0.4300 | 0.0893 | 0.7151 | 0.5126 |
| 46 | 0.6971 | 0.4364 | 0.0816 | 0.7144 | 0.5189 |
| **mean** | **0.69899** | 0.43678 | 0.08841 | 0.71857 | 0.51823 |
| **sd** | **0.00286** | 0.00757 | 0.00477 | 0.00439 | 0.00416 |
| range | 0.00611 | 0.01746 | 0.01107 | 0.00816 | 0.01004 |

**σ(Sα) = 0.00286**, so 2σ = 0.00571. Relative noise: Sα 0.4%, Fβw 1.6%, **MAE 6.4%** of the
reported values — MAE is far noisier than Sα and should not be the headline metric.

Against everything on record:

| effect | Sα | in σ | vs 2σ |
|---|---|---|---|
| plan's expected Stage C effect (low) | 0.0020 | 0.70σ | **below** |
| plan's expected (high) | 0.0050 | 1.75σ | **below** |
| your reproduction deviation vs the paper | 0.0036 | 1.26σ | **below** — i.e. explained by noise |
| paper's Mean-Teacher → Ours gap | 0.0140 | 4.90σ | detectable |

A single-seed A/B/C comparison cannot resolve the expected effect. But — and this changes my prior
position — the experiment **is** powered at feasible seed counts, because a run is only ~1.8 h and
four fit concurrently on the two GPUs. Using the forked design from §5 (1 shared iteration-1 + CLS
per seed, then 3 arms = 4 runs/seed):

| seeds/arm | MDE (Sα, 80% power) | runs | wall clock |
|---|---|---|---|
| 5 | 0.00506 | 20 | 9.2 h |
| 10 | 0.00358 | 40 | 18.3 h |
| 15 | 0.00292 | 60 | 27.5 h |
| **20** | **0.00253** | 80 | **36.6 h** |
| 30 | 0.00206 | 120 | 54.9 h |

Seeds required to reach 80% power at a given true effect: δ=0.005 → 6/arm (11 h); δ=0.003 → 15/arm
(27.5 h); δ=0.002 → 32/arm (59 h). All fit inside 30 days.

**VERDICT (3): σ(Sα) = 0.00286. A single seed per arm is useless — the expected effect is
0.70–1.75σ. But 20–30 seeds/arm reaches an MDE of 0.0021–0.0025 in 37–55 h wall clock, which covers
the plan's expected range. The allocation experiment is not compute-blocked; it is
prior-probability-blocked (see §5's d≈0.10).** Caveats: n=4 gives a wide CI on σ itself
([0.57, 3.73]×σ_true); these runs used the 4447-image HKU-IS pool while the arms would use ~7824
with different composition, so σ may differ — UNVERIFIED. Because each arm is itself a standalone
`--iteration 1` run (§5), σ measured this way is the right scale, and the shared CLS pool cancels in
a paired test, which would lower the required n further.

### 3b. How much does a paired design actually buy? — MEASURED

Two extra runs at the **same** seed 42 (1/GPU, no contention), giving three seed-42 runs. Their
spread isolates training nondeterminism from the seed effect.

| run (all seed 42) | Sα | Fβw | MAE |
|---|---|---|---|
| original | 0.7022 | 0.4333 | 0.0926 |
| replicate B | 0.7058 | 0.4464 | 0.0871 |
| replicate C | 0.7016 | 0.4272 | 0.0907 |

| | σ(Sα) | σ(Fβw) | σ(MAE) |
|---|---|---|---|
| **fixed-seed** (n=3, seed 42) | **0.00229** | 0.00980 | 0.00281 |
| across-seed (n=4) | 0.00286 | 0.00757 | 0.00477 |
| ratio | **0.80** | 1.29 | 0.59 |

**80% of the Sα run-to-run spread is training nondeterminism, not seed choice.** Pairing by seed
therefore removes only 1 − 0.80² ≈ **36%** of the variance. Note replicate B (0.7058) exceeds every
one of the four different-seed runs (max 0.7022) — at n=3/n=4 these two σ's are not cleanly
separable, but the point estimate says the seed is the minor term.

Paired design, σ_d = √2 × 0.00229 = 0.00324:

| δ (Sα) | pairs | total runs (incl. shared iter-1) | GPU-h | days on 2 GPUs |
|---|---|---|---|---|
| 0.0010 | 83 | 332 | 598 | 12.5 |
| **0.0020** | **21** | **84** | 151 | **3.2** |
| 0.0030 | 10 | 40 | 72 | 1.5 |
| 0.0050 | 4 | 16 | 29 | 0.6 |

Pairing beats unpaired by ~36% (21 pairs = 42 arm-runs vs 33/arm = 66 arm-runs at δ=0.002), so use
it — but it is a modest win, not a rescue.

**The actionable consequence:** because the seed is the *minor* noise term, the highest-leverage
change for making this experiment cheap is not more seeds — it is **making training deterministic**.
`set_random_seed` (`tool.py:24-28`) never sets `torch.backends.cudnn.deterministic = True` nor
`torch.use_deterministic_algorithms(True)`. If SINet's ops all have deterministic kernels, σ_fixed
could fall toward 0 and the paired MDE would collapse with it. Whether they do, and the throughput
cost, is **UNVERIFIED** — it needs one timed run, and it is the cheapest thing to try before
committing 84 runs.

---

## 4. Does the deficiency signal predict where the model is actually bad?

Student `Stu_40.pth` + teacher `Tea_epoch_best.pth` from `Snapshot/SINet/S2C/` (the reproduction
that scored Sα 0.7172). ES computed exactly as `CLS.py:105`/`138`: `ESLoss(a=0.9, b=0.3,
use_weighted_bce=False)` on `stu.sigmoid()`, `tea.sigmoid()` at 352×352. True error from the
teacher's prediction upsampled and min-max normalized per `MyTest.py:72-75`.

Pipeline validated: my per-image mean MAE on COD10K-test is **0.0747** against the repo's recorded
**0.0745** (`Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`).

**4a. Per-image.** Spearman(ES, MAE) = **+0.751** (test, n=2026), **+0.660** (CAMO-val, n=250).
Spearman(ES, 1−IoU) = +0.201 / +0.250.

**4b. Per-cluster** (the quantity `d(c)` actually consumes), clusters with ≥8 labelled images:

| k | split | clusters | ρ(ES_c, MAE_c) | ρ(ES_c, 1−IoU_c) |
|---|---|---|---|---|
| 20 | test | 20 | **+0.857** | +0.513 |
| 50 | test | 49 | **+0.817** | +0.239 |
| 100 | test | 86 | **+0.880** | +0.264 |
| 20 | val | 9 | +0.800 | +0.550 |
| 50 | val | 6 | +0.943 | +0.771 |

**4c. What the coverage term does to it** (k=50, test, 49 clusters):

| d(c) formulation | ρ(d(c), true MAE_c) | top-10 overlap with true worst-10 |
|---|---|---|
| **ES only (λ_cov = 0)** | **+0.817** | **5/10** |
| λ_cov = 0.01 | +0.431 | — |
| λ_cov = 0.05 | +0.138 | 2/10 |
| **coverage term alone** | **+0.006** | — |

**And the mechanism, measured:** ρ(acceptance, n_s(c)) = **+0.893** (k=20), **+0.916** (k=50). The
coverage term ranks by −n_s(c); acceptance is almost perfectly *predicted* by n_s(c). So
coverage-ranked allocation is close to inverse-ranked by feasibility — by construction, not by
accident. Meanwhile ρ(acceptance, ES_c) = −0.280 (k=20) / −0.015 (k=50): ES-based deficiency is
essentially **independent** of reachability.

Consequence — allocating by ES instead of by coverage fixes the compute problem too:

| ranking (k=50, DINOv2 L/224) | top-12 mean acceptance | gens for B=1000 | GPU-h |
|---|---|---|---|
| coverage-ranked | 3.12% | 32,000 | 15.4 |
| **ES-ranked (λ_cov=0)** | **18.33%** | 5,454 | **2.6** |

**VERDICT (4): my prior C1 concern is REFUTED — ES-disagreement is a strong error proxy (ρ=+0.82
per-cluster, +0.75 per-image). The coverage term is noise (ρ=+0.006) and actively destroys the
signal (+0.82 → +0.14). Set λ_cov = 0; that single change simultaneously restores d(c)'s validity
and makes generation ~6× cheaper.** Caveat: ES tracks MAE-like error (ρ≈0.82) far better than
IoU-like error (ρ≈0.24) — it predicts calibration error more than localization error. Caveat 2: the
strong numbers come from COD10K-test; val-only has too few populated clusters (6 at k=50) to stand
alone, though it agrees in direction (+0.80 at k=20, 9 clusters). Deriving λ_cov=0 from test data is
mild test-peeking and must be disclosed.

---

## 5. Is A/B/C clean and runnable?

**Fixed-compute equality — CONFIRMED.** `total_step = min(len(source_loader), len(target_loader))`
(`MyTrain.py:306-307`) with `zip()` at `MyTrain.py:51`. `len(target_loader)` is pinned at
`ceil(4040/16) = 253`. Arm A (|Ds|=6824) → 253; arms B and C (|Ds|=7824) → 253. All three arms run
**253 × 39 = 9867 identical gradient steps**, and each epoch draws a fresh uniformly-random
253×16 = 4048-image subset because `get_srcloader` sets `shuffle=True` (`Dataloader.py:206`) and
DataLoader reshuffles per `iter()`. B and C additionally have identical |Ds|, so B-vs-C differs
*only* in the identity of the 1000 appended images. That is a genuinely clean comparison.

**A cheaper, less confounded arm structure — new finding.** `MyTrain.py:250-290` constructs a fresh
`model`, fresh `model_ema`, fresh `Adam`, and resets `global_step`/`best_teamae`/`best_epoch` inside
the iteration loop. **Nothing carries from iteration 1 to iteration 2 except `opt.source_root`.** So
"iteration 2" is exactly a standalone `--iteration 1` run pointed at the iteration-2 pool. Therefore:
run iteration 1 + CLS **once per seed**, then fork into three arms as three `--iteration 1` runs.
That is 1+3 runs/seed instead of 3×2, and it removes iteration-1 stochasticity as a confound between
arms. (Caveat: `set_random_seed` is called once before the loop at `MyTrain.py:242`, so a forked run
is not bitwise identical to monolithic iteration 2 — irrelevant if all arms are forked identically.)

**What must be patched** for 3 arms × N seeds:

1. **`--seed`** — `MyTrain.py:242` hardcodes `set_random_seed(42)`. Minimal patch, 2 lines, applied
   in this study as `scratchpad/noisefloor/MyTrain_seed.py` (`diff` against the original is exactly
   one added argparse line + one changed call, default 42 so existing commands are byte-identical):
   ```python
   parser.add_argument('--seed', type=int, default=42)
   ...
   set_random_seed(opt.seed)
   ```
2. **Worker seeding** — `get_srcloader`/`get_tarloader` (`Dataloader.py:200-219`) pass no
   `worker_init_fn`, while `SrcDataset.__getitem__:32` calls `np.random.rand()` in 6 forked workers,
   so all 6 share the parent's numpy stream. Fix: `worker_init_fn=lambda w: np.random.seed(seed*1000+w)`
   plus an explicit `generator`. **Deliberately NOT applied here** — it changes the augmentation
   distribution, and the aim was σ of the pipeline *as it exists*.
3. **`--save_model` per arm and per iteration** — one constant used at `MyTrain.py:141`, `146-151`,
   `187`, `309`, `324`, and handed to `cls()` at `328`. Iteration 2 overwrites iteration 1's
   `Tea_epoch_best.pth`/`Stu_40.pth`. Worse: `CLS.py:65` reads `Tea_epoch_best.pth` from that same
   directory, so two arms sharing `--save_model` can pseudo-label from each other's teacher. Write
   to `f'{save_model}/{arm}_s{seed}/it{i}/'` and pass that same path to `cls()`.
4. **CLS output path** — `CLS.py:16-17` derives `_iteration{N}/` from `source_root`/`gt_root` alone;
   `network` is a parameter (`CLS.py:13`) that never enters the path, and lines 21/27 `rmtree` it.
   Add an explicit `out_root` parameter and compose it in `MyTrain.py` from
   (network, method, arm, seed, iteration). Also guard `if gt_copy_root != source_copy_root:` around
   `CLS.py:25-29` — `MyTrain.py:328` passes `opt.source_root` for both, so CLS currently `rmtree`s
   the copy it just made.
5. **Post-write pairing assertion** — reuse `preflight.py:325-342` (`pairing()`) and
   `preflight.py:362+` (the `filter_files` silent-drop check) rather than reimplementing, then
   assert `len(SrcDataset(...)) == expected_total` after Stage C writes.

**Remaining confound — and it is the serious one.** How different is arm C's added data from arm
B's? Allocating B=1000 by temperature-softmax over ES_c, then taking the nearest cutouts per
funded cluster, versus a uniform-random 1000 of 4447, in DINOv2 L/224 space:

| k | T | clusters funded | max alloc | ‖mean_C − mean_rand‖ | Cohen's d |
|---|---|---|---|---|---|
| 20 | 0.005 | 14 | 456 | 0.0854 | **0.09** |
| 20 | 0.05 | 20 | 76 | 0.0946 | **0.10** |
| 50 | 0.005 | **1** | 999 | 0.0980 | **0.10** |
| 50 | 0.01 | 22 | 927 | 0.0992 | **0.11** |
| 50 | 0.05 | 49 | 76 | 0.0838 | **0.09** |

Two things here. First, arm C's appended set differs from arm B's by only **d ≈ 0.10** in feature-space
mean — a tenth of a standard deviation, and those 1000 images are 12.8% of the training pool.
Second, **the temperature knob barely moves the outcome**: d ranges 0.084–0.099 across a 10×
sweep of T, even though T changes the number of funded clusters from 1 to 49. The one hyperparameter
that defines "targeted" has almost no effect on the resulting data distribution.

**VERDICT (5): A/B/C is clean, runnable, and genuinely fixed-compute, and the fork structure makes
it cheap. But the B-vs-C contrast is d≈0.10 on 12.8% of the pool, invariant to T — the design is
sound and the effect it can deliver is very small.**

---

## Two side findings, re-verified after challenge

### (a) Test/Target overlap — real, but NOT "live contamination".

Confirmed facts. `Dataset/Target/Image` contains 7 images pixel-identical to COD10K-test images
(2 same-name, 5 cross-named — the latter are COD10K's own duplicate photographs spanning its own
train/test split). CLS pseudo-labels from `target_root/Image/` (`CLS.py:115-156`) with no
test-exclusion, so some of them pass the confidence gate and land in the iteration-2 pool:

| pool | leaked test images present | pixel-identity | GT present | size match |
|---|---|---|---|---|
| `HKU-IS_iteration2` | 5/7 | maxdiff **0** | yes | yes |
| `HKU-IS_iteration2-SINet` | 3/7 | maxdiff **0** | yes | yes |
| `HKU-IS_iteration2-SINetV2` | 2/7 | maxdiff **0** | yes | yes |

All have GT and matching size, so `filter_files` (`Dataloader.py:39-50`) keeps them and training
reads them. **These three directories are one lineage renamed per network** (collision-avoidance for
the `CLS.py:16-17` path bug), not three independent pools — the differing counts are just CLS's gate
admitting different subsets under each run's iteration-1 teacher.

**But the measured impact is nil, and my "reviewer-fatal" characterisation was wrong:**

| | value |
|---|---|
| test MAE, all 2026 | 0.074697 |
| test MAE, excluding all 7 | 0.074709 |
| **shift from removing every leaked image** | **0.000012 (0.017% relative)** |
| MAE percentile of the 7 within the clean test set | 0.088, 0.126, 0.734, 0.865, 0.913, 0.580, 0.029 |
| **mean percentile** | **0.477** (0.5 = indistinguishable) |
| 1−IoU on the 7 vs the rest | 0.579 vs 0.551 (leaked are *worse*) |

No memorisation signature at all. The reason is structural: the pseudo-label comes from the
**teacher**, not from ground truth, so no test *labels* leak — only test *pixels*, with
self-generated targets. Training on unlabelled target-domain images that happen to overlap the test
split is the transductive UDA setting, not label leakage. The real defect is narrower: S2R-COD's
stated protocol (target = COD10K-train, eval = COD10K-test) is violated by COD10K's own duplicates.

**What survives as actionable:** the *mechanism*, not the current numbers. Nothing filters Target
against Test, so every future cycle re-admits these images, and Stage C's `d(c)` would steer
generation toward the clusters they occupy. That is a one-line `preflight.py` check (full pairwise
hash, not name-matching — 5 of the 7 are cross-named) and one disclosure sentence in the paper. It
is **not** grounds for re-running the Table 1 reproduction.

Full pairwise sweep, closing the E2 UNVERIFIED item: Test∩Target = 7; Test∩Val, Test∩Source,
Target∩Val, Val∩Source all **0**. Also found: 2 internal byte-identical duplicates inside `Target/`.

### (b) By iteration 2 the "synthetic source" pool is ~30-35% real imagery — CONFIRMED

| pool | total | from HKU-IS (synthetic) | from Target (real) | % real | pixel-exact sample |
|---|---|---|---|---|---|
| `HKU-IS_iteration2` | 6824 | 4447 | 2377 | **34.8%** | 25/25 |
| `HKU-IS_iteration2-SINet` | 6353 | 4447 | 1906 | **30.0%** | 25/25 |
| `HKU-IS_iteration2-SINetV2` | 6322 | 4447 | 1875 | **29.7%** | 25/25 |

CLS copies real target images in pixel-exactly (`CLS.py:156`, jpg→png re-encode only), which is why
the byte-hash sweep reported Target∩Src_it2 = 0 while they are pixel-identical.

This is the more consequential of the two findings, because it changes the denominator for Stage C:
B=1000 is 12.8% of the 7824-image pool but only **18% of its synthetic part**, and it competes
against ~2400 real target images carrying teacher pseudo-labels. Expected effect shrinks accordingly.

---

## 6. Direction call

**Characterization-led, with a powered A/B/C experiment reported as the empirical section — and
λ_cov = 0 as its own contribution.**

The deciding numbers. Option C is *not* dead: DINOv2 at native resolution lifts deficient-cluster
acceptance from InceptionV3's 0.00% to **26.67%** at k=20 (§1), which is 1.8 GPU-h per cycle-arm, so
my prior kill was embedder-limited and wrong. The ES term is *not* broken either: it predicts true
per-cluster error at **ρ=+0.817** (§4), refuting my prior C1 concern. What is broken is the coverage
term alone — **ρ(coverage, true error) = +0.006**, and adding it degrades d(c) from +0.817 to +0.138,
because **ρ(acceptance, n_s(c)) = +0.92** makes coverage-ranking almost exactly inverse-ranking by
feasibility (§4). Dropping it fixes validity and cost simultaneously (15.4 → 2.6 GPU-h). So the
plan is repairable. What is *not* repairable by any of this is the effect size: arm C's appended
1000 images differ from arm B's by **Cohen's d ≈ 0.10** in DINOv2 space, invariant across a 10×
sweep of T (§5); Stage C adds **zero** gradient steps (`total_step` = 253 either way, §5); B=1000 is
~18% of the *synthetic* part of a pool that is **30–35% real target imagery**; and the noise floor
is **σ(Sα) = 0.00286**, putting the plan's expected 0.002–0.005 at 0.70–1.75σ (§3).

So: allocation-led as the *primary* claim is a bet that a d≈0.10 perturbation of 12.8% of a pool,
with no extra optimization, moves Sα by more than 0.0025. Nothing measured here supports that bet,
and three independent measurements argue against it. But the experiment is cheap enough (37–55 h)
that it should still be run — as evidence inside the characterization paper, where either outcome is
publishable because the mechanism is explained.

**What already constitutes the characterization paper** (all measured, no further compute):
1. The conditioning bottleneck — LAKE-RED's entire steerable channel is 16 superpixels × 3 mean-colour
   channels = **48 numbers** (`ddpm.py:1548-1590`), with 81.8% of every output being invented
   background. Foreground→background colour correlation flips from −0.36 (real HKU-IS) to +0.45
   (generated), so the lever is real but R²≈0.2.
2. The style manifold — a **linear** probe separates real COD from LAKE-RED output at **AUC 0.9985–
   0.9989, Cohen's d 4.35–4.70**, invariant to model size and resolution (§2).
3. The diversity ceiling — generative **recall 0.466 vs an 0.871 real-vs-real ceiling** (54% of
   achievable); precision 0.691 vs 0.893 (77%). Realism-good, diversity-poor (§2).
4. The inverted competence profile — acceptance is +0.92 correlated with existing coverage, so
   naive coverage-driven targeting is inverse-ranked by feasibility (§1, §4).
5. The repairable-signal result — ES-disagreement is a valid error proxy (ρ=+0.82); the obvious
   coverage correction is not (ρ=+0.006) and is actively harmful (§4). **This is the transferable
   prescription:** allocate by model disagreement, never by embedding-space coverage counts, unless
   the generator's outputs are style-indistinguishable from the target.
6. The measurement floor — σ(Sα)=0.00286 for this pipeline, which retroactively explains the 0.0036
   reproduction deviation as noise (§3).

**What is still missing for it:** (a) the A/B/C result itself at n≥21 pairs (§3b); (b) a
generator-side ablation showing the prescription is causal rather than descriptive — e.g. widen the
conditioning beyond `vec_fg` (concatenate a target-cluster embedding into BKRA's cross-attention)
and show acceptance and recall both rise. (b) is the difference between a diagnosis and a
contribution, and it is the one piece I have not measured.

**If run as allocation-led anyway, the pre-registered design:** claim — "allocating a fixed
synthetic budget by teacher–student ES-disagreement beats uniform-random allocation." Arms A(none) /
B(random-unfiltered) / C(ES-allocated, λ_cov=0, keep-all, no rejection sampling). Forked design: one
shared iteration-1 + CLS per seed, then three `--iteration 1` arms (§5). Primary metric **Sα** — not
MAE, whose σ is 6.4% of its value. λ_cov fixed at **0** and T fixed a priori at 0.02 (§5 shows T
barely matters, so pick it once and never touch it). k=20, DINOv2 ViT-L/14 at native 518.

Sample size, using the **measured** paired σ_d = √2 × 0.00229 = **0.00324** (§3b), not an assumed
one: **21 pairs** for 80% power at δ=0.002 (84 runs, 3.2 days on 2 GPUs); 10 pairs at δ=0.003;
83 pairs at δ=0.001. Decision rule: paired t-test on C − B at α=0.05, powered for δ=0.002 — declare
success only if the paired mean difference is positive with its 95% CI excluding 0; otherwise report
the null **with the CI**, which is the informative outcome given §5's d≈0.10 prior.

**Do this first, before committing 84 runs.** §3b shows the seed is the *minor* noise term — 80% of
the spread is training nondeterminism. So the cheapest lever is not more seeds but
`torch.backends.cudnn.deterministic = True` + `torch.use_deterministic_algorithms(True)`, neither of
which `set_random_seed` (`tool.py:24-28`) sets. If SINet's ops all have deterministic kernels, σ_fixed
falls toward 0 and the required pair count collapses with it. One timed run settles it; whether it
works and what it costs in throughput is **UNVERIFIED**.

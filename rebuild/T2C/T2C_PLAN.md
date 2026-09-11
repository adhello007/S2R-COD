# T2C_PLAN.md — is the pixel-over-structure gap specific to ES, or general to uncertainty in COD?

> **Specification, approved before any T2-C code was written or any T2-C number existed.**
> Decision rule: `rebuild/T2C/PREREGISTRATION_T2C.md`, committed and FROZEN.
> **TRAINS NOTHING.** Inference only. No checkpoint is written, no pool is built, no partition is fit.
>
> Dated 2026-09-11. Additive to the frozen B1 / C1 / A-B-C / T2 record. Scoping audit:
> `rebuild/T2C/T2C_SCOPING.md`.

---

## §0 The question, and what an answer would be worth

B1 measured, for the ES allocation signal, target-side against COD10K-test error through the
committed `dinoL518 k=75 seed=0` partition:

| | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) | ratio 1−Sα / MAE |
|---|---|---|---|---|
| target-side ES → endpoint error | **+0.6284** | **+0.3433** | **+0.2613** | **0.5463** |

`rebuild/B1/out/b1_faithful_correlation.json`, `results/REBUILD_LOG.txt:1005-1008`.

ES is **0.9-weighted on an edge term** (§3.1) and still tracks pixel error nearly twice as well as
structural error. T2-C asks whether two other uncertainty signals do the same thing. If all three
show `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)`, the finding stops being about ES and becomes a task-level
statement: **uncertainty in COD tracks calibration, not localisation.**

T2-C is **correlational**. It establishes a prior; it does not prove that every signal fails in
training (§9).

## §1 Inherited, asserted rather than restated

| Inherited | Asserted at |
|---|---|
| Partition `dinoL518, k=75, kmeans_seed=0` — read, never refit | `b1_cluster_assignment_dinoL518.json`, cross-checked via `c1_space.load_space` |
| Target set 4040 → **4033** after D2's 7 measured leaked names | `B1.load_target` (`b1_es_error_correlation.py:329-338`), reading `d2_leaked_names.json` |
| Endpoint COD10K-test (2026); CHAMELEON withdrawn; CAMO selection-only | `B1.SPLITS` (`:60-64`) |
| Per-image endpoint error `mae / one_minus_sa / one_minus_iou` | `b1_scores_{SINet-S2C,SINet-v2-S2C}_test.csv`, via `B1.load_scores` |
| Floors: ≥15 endpoint images **and** ≥5 target images | line copied verbatim from `b1_allocation_signal.py:170-171` |
| 352×352 + ImageNet normalisation | `B1.TESTSIZE`, `score_target_es` transform (`b1_allocation_signal.py:94-95`) |
| Head per architecture | `B1._head` — SINet `out[1]`, SINet-v2 `out[3]` (`:183-195`) |
| Checkpoint-copy assertion | `B1._load_ckpt` (`:198-212`), per `Explanations/CHECKPOINT_LOADING_BUG.md` |
| Spearman ρ + permutation p + bootstrap CI | `B1.spearman_perm` (`:470-491`) — reused, not reimplemented |
| Provenance scan | `E0.step_independence()` called unchanged |
| Scorer validation | `abc_evaluate.score` + `B1_SA/B1_MAE/TOL` (`abc_evaluate.py:43`) |

T2-C adds **one module** (`t2c_signals.py`), one driver, one output namespace
(`rebuild/T2C/out/`), and one log tag (`EXP T2C`). It edits no committed file.

## §2 Endpoint: COD10K-test only

**NC4K is dropped.** Three separate things are missing and all require work outside an
inference-only experiment:

1. **No embeddings.** `rebuild/E0/cache/` holds `dinoL518_{auth,cut,local,raw,test,tgt,val}_*` —
   no `nc4k`. Cluster assignment for its 4121 images is impossible without an E0 pass.
2. **NC4K is not a B1 split.** `B1.SPLITS` has `test` and `val` only; `endpoint_emb` reads
   `%s_%s_cls.npy` and would fail.
3. **No per-cluster NC4K error.** The committed cluster CSV has `test_*` / `val_*` columns only.

Also, `common.INPUTS` declares `nc4k` but **no `nc4k_gt`** — every NC4K GT access in the repo is a
hardcoded string.

**Stated limitation.** T2-C rests on a single endpoint. A pattern that held on COD10K and reversed
on NC4K would not be visible. CHAMELEON stays excluded (D2 measured re-encodes of target images);
CAMO stays selection-only, and at k=75 it is degenerate anyway (2 surviving clusters,
`REBUILD_LOG.txt:800`).

## §3 Signals, exactly

All signals are per-image scalars on the **unlabeled target set** (4040 scored, 4033 joined), at
**352×352**, from the **raw sigmoid** — never min-max renormalised (§3.5).

### 3.1 Why "comparable to ES" cannot mean "same functional form"

With the committed live config `a=0.9, b=0.3, c=0.5, use_weighted_bce=False`
(`REBUILD_LOG.txt:767-768`):

```
ES = 0.9 · mean|Sobel(σ(stu)) − Sobel(σ(tea))|₁  +  0.3 · mean BCE(σ(stu), σ(tea))
```

`target` is the **teacher's sigmoid**, not ground truth. ES is a weighted sum of two whole-image
means over two different per-pixel fields, one of which (edge disagreement) has no single-model
analogue.

**Comparability is declared as: same images, same clusters, same resolution, same floors, same
statistic — explicitly NOT same functional form.** Stated rather than implied.

### 3.2 Predictive entropy

```
H(p) = −( p·log₂ p + (1−p)·log₂(1−p) ),   p = clip(σ(logit_teacher), 1e-6, 1−1e-6)
```

- **Checkpoint: `Snapshot/<arch>/S2C/Tea_epoch_best.pth`.** Forced, not preferred: B1's committed
  endpoint error is the *teacher's* error (`b1_es_error_correlation.py:216, 252-254`), and
  `ema_model` is CLS's sole pseudo-label producer (`CLS.py:141-145`). Student entropy would pair one
  model's confidence with another model's error.
- **Base 2**, so H ∈ [0, 1] bits. A base change is a positive scalar multiple of the per-image mean,
  so **Spearman ρ is exactly invariant** to it — the choice sets scale only.
- **Clamp 1e-6**, float64 accumulation. Unlike the base, the clamp is not ρ-neutral in principle
  (float32 sigmoid underflows below 1e-6 on confident background). H(1e-6) ≈ 2.1e-5 bits, so the
  effect on a mean over 123,904 pixels is negligible; a 1e-12 variant is reported as a free
  robustness check.

### 3.3 Ensemble disagreement

Per-pixel **population variance** (`ddof=0`) of `σ(logit)` across the 3 members' `Tea_epoch_best.pth`.

**Why variance:** it is the standard ensemble-uncertainty statistic and extends past 3 members
unchanged. Mean pairwise |Δ| is, at n=3, a near-monotone function of the sd, so ρ would be nearly
identical — a low-risk choice, stated rather than agonised over. Note that the **aggregation** is
not interchangeable: `mean(var)` is not a monotone function of `mean(sd)`, so `mean(sd)` is reported
as a separate free robustness variant rather than treated as equivalent.

**Primary arm: A0 {42, 43, 45}** — configuration-matched to ES (base pool only, the authors' setup).
**Sensitivity arm: CSHUF {42, 43, 45}** — the tightest available.

**Disclosed prominently, beside every ensemble ρ:**

| arch | A0 members (Sα, COD10K) | A0 spread | A0 arm sd | CSHUF arm sd |
|---|---|---|---|---|
| SINet | 0.715086 / **0.681706** / 0.706058 | **0.0334** | **0.017266** | 0.001655 |
| SINetv2 | 0.688813 / **0.678740** / 0.699883 | 0.0211 | **0.010575** | 0.003523 |

A0 is the outlier arm by an order of magnitude on SINet and 3× on SINet-v2
(`rebuild/ABC/out/abc_sigma.json`, `out/t2/abc_sigma.json`). With one member 0.033 Sα worse than
another, part of the disagreement measures **which member is weak**, not **which image is hard** —
and a weak model errs most on large-error images, which is exactly the pixel axis T2-C is trying to
separate from the structural axis. **The confound pushes toward the hypothesis**, the dangerous
direction.

**Two further disclosures.**

1. **Model mismatch.** The ensemble members are *not* the model whose error is the endpoint column.
   The S2C teacher scores Sα 0.717216; no A0 member does. The ensemble rows therefore correlate one
   model family's disagreement against another model's error. Unavoidable within an inference-only
   scope (an A0-specific error column would need a new B1 pass), and reported as a limitation.
2. **What it measures.** Same data, same architecture, same hyperparameters, same pool — **only the
   training seed differs** (`abc_common.py:56`). This is *optimisation-stochasticity* disagreement,
   not epistemic uncertainty about the data distribution, and must not be reported as such.

**Power.** 3 members is a very small ensemble; a 3-sample variance has ~70% relative standard error.
Per-cluster means over ≥15 images recover some of that, but **a null from the ensemble is weaker
evidence than a null from entropy**, and is reported that way.

**Sensitivity condition.** If A0 and CSHUF disagree on the ordering, the ensemble result is reported
as **a possible weak-member artifact, not a finding**.

### 3.4 ES, re-derived

For a like-for-like row, ES is re-derived in **unreduced** form using the same two functional calls
`ESLoss.forward` makes, with `reduction='none'`:

```
es_map = a · |edge_pred − edge_target|  +  b · BCE_elementwise(σ(stu), σ(tea))
```

`es_map.mean()` is the committed scalar by construction. `use_weighted_bce=True` is a **HALT** —
the weighted branch is deliberately not implemented, so a reconfigured `ESLoss` breaks the run
instead of silently changing the measurement (§6 Gate 2).

**Disclosed artifact.** `ESLoss` uses `padding=1` **zero**-padding, so the outer 1-px ring of
`es_map` carries a spurious Sobel response. It is 1.1% of 352² and invisible under the whole-image
mean — but it **must not be masked**, because the committed scalar includes it and masking would
break the reproduction gate. Under the boundary aggregation it contributes only where an object
touches the image edge. Reported, not corrected.

### 3.5 Aggregations — both, for all three signals

Every signal is aggregated **twice**, over identical regions:

| aggregation | definition |
|---|---|
| **whole-image** | mean over all 352×352 pixels — closest analogue to ES's region term |
| **boundary** | mean over a band straddling the teacher's predicted contour |

**The band, exactly.** One band per image, **shared by all three signals**:

```
M    = σ(logit_teacher) >= 0.5              # raw sigmoid, 352x352, S2C teacher
band = dilate(M, ones(3,3), iters=2) & ~erode(M, ones(3,3), iters=2)
```

- threshold **0.5** on the **raw** sigmoid;
- kernel **3×3 full square** (8-connected), **2 iterations**;
- resulting width **2·iters = 4 px** across a straight edge (2 outward, 2 inward). The measured mean
  band area fraction is reported rather than derived.
- Repo precedent: `d2r_reaudit.py:565-566` uses the same 3×3 square at `iterations=1` but an
  **inner-only** band (`fg − eroded`). T2-C uses a **symmetric** band because entropy is highest
  *straddling* the contour — an acknowledged **extension** of that precedent, not a reuse of it.
  `iters=1` (2 px) is reported as a free robustness variant.
- `cv2.erode`'s default border value is the morphological max, so an object touching the image edge
  is not eroded there. Inherited behaviour, identical for all signals because the band is shared.

**Why one shared band.** The band is prediction-dependent and the three signals come from different
models. A per-signal band would make "boundary-restricted" name a *different region* in each row,
confounding the comparison invisibly. The shared band is the S2C teacher's, because the endpoint
error column is that teacher's error. For the ensemble only, a per-signal band (from the ensemble
mean prediction) is reported as a robustness variant.

**Empty-band handling, pre-registered.** If `band` is empty (globally unconfident teacher, or a
saturated mask), the image contributes **no** boundary value. Per-cluster boundary means use only
band-eligible images, and the ≥5-target floor is applied to the **band-eligible** count.
`n_boundary_empty` is reported. **HALT if > 5% of target images have an empty band** — a boundary
signal defined on 90% of images is not comparable to a whole-image signal on 100%.

**The min-max trap.** B1's *error* path min-max renormalises the prediction
(`b1_es_error_correlation.py:256`); its *ES* path uses the raw sigmoid. Entropy is a calibration
quantity, and min-max renormalisation would stretch p across [0,1] and destroy it. **All T2-C
signals and the band threshold use the raw sigmoid at 352×352.** Asserted (§6 Gate 3).

## §4 Structure: target-side signal, endpoint-side error

Reproduces `faithful_correlation` (`b1_allocation_signal.py:150-191`) exactly:

```
signal  :  per-image, on Dataset/Target/Image        (4040 scored -> 4033 joined, no GT exists)
error   :  per-image, on COD10K-test                 (2026, B1's committed CSV)
join    :  the committed target-fitted partition; endpoint images assigned to target centroids
           by argmax(E @ centroids.T) on L2-normalised vectors  (b1_es_error_correlation.py:461-467)
floors  :  len(err[c]) >= 15  AND  ces[c][1] >= 5    (verbatim from b1_allocation_signal.py:170-171)
rho     :  B1.spearman_perm, n_perm=2000 at seed 0 (matching the committed call), 200 for seeds 1-9
```

**The endpoint never influences the partition.** Why this is the one invariant that gets a HALT:

| dinoL518, k=75, 50 clusters | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) |
|---|---|---|---|
| **target-side ES → endpoint error** (T2-C's structure) | **+0.6284** | +0.3433 | +0.2613 |
| endpoint-side ES, same clusters (the easier question) | +0.8754 | +0.3810 | +0.2304 |
| ρ(target ES, endpoint ES) per cluster | | | **0.5732** |

The two ES variants agree only at ρ = 0.5732 — **not interchangeable**. Computing a new signal on
COD10K is the *natural* mistake, because that is where the GT and the error already are. It is one
argument to a loader. Nothing would crash, no existing gate would fire, and the resulting table
would sit next to B1's +0.6284 as though comparable. `B1.step_correlate` (`:494-541`) computes
exactly that same-side quantity and is **never called by T2-C**.

## §5 Seeds: seed 0 is the headline, 10 seeds are the yardstick

- **Seed 0** — the committed partition, read from `b1_cluster_assignment_dinoL518.json`. Every
  headline ρ comes from here, so it is directly comparable to B1's +0.6284.
- **Seeds 1–9** — `B1.fit_kmeans(X, 75, seed)` refits **in memory only** (`_KM_CACHE` is a plain
  dict, `b1_es_error_correlation.py:425`). Nothing is written; no committed artifact is touched.
  These give each ρ a standard deviation.

`cluster_target_es` returns `None` for any seed but the committed one
(`b1_allocation_signal.py:141-142`), so this path is new code, and it is gated: at seed 0 the refit
must reproduce `a['target_labels']` **exactly** (§6 Gate 5).

**Resolution limit, pre-registered.** ρ differences below **~0.06** between signals are not
distinguishable. Committed support, at the committed k=75 (`REBUILD_LOG.txt:794-796`):
ρ(MAE) ±0.0264, ρ(1−Sα) ±0.0461, ρ(1−IoU) ±0.0564 over 10 seeds — so two independent ρ(1−Sα) values
differ with sd ≈ 0.065. **The claim is about the pattern (all signals show pixel > structure), never
about fine ρ differences between signals.** Sub-0.06 gaps are not interpreted.

The ratio is worse: propagating the above gives sd(ratio) ≈ **0.077**, so a ±0.10 band is ~1.3 sd
wide. T2-C measures and reports the ratio's own 10-seed sd beside it.

## §6 Gates — all must PASS before any correlation is computed

| # | Gate | Requirement | HALT |
|---|---|---|---|
| **1** | **Target-side invariant** | §Gate 1 below, four assertions | **yes** |
| 2 | ES config | live `ESLoss` is `a=0.9, b=0.3, c=0.5`, `use_weighted_bce=False`, parsed from `MyTrain.py` by `B1.parse_es_config` | yes |
| 3 | Raw sigmoid | no min-max renormalisation anywhere in the signal path; AST scan of `rebuild/T2C/*.py` for renorm patterns; band threshold reads the raw sigmoid | yes |
| 4 | Unreduced-ES identity | per image, `abs(es_map.mean() − ESLoss.forward(pred,target)) < 1e-6`, same forward outputs, same process | yes |
| 5 | Partition identity | `fit_kmeans(X,75,0).labels_ == a['target_labels']` exactly; on failure report ARI and halt | yes |
| 6 | ES reproduction (per image) | vs committed `b1_target_es_<arch>.csv` (4040 rows): `max|Δ| < 1e-5`, `mean|Δ| < 1e-6` | yes |
| 7 | ES reproduction (per cluster) | vs committed `b1_cluster_es_dinoL518.csv` `target_es`: `|Δ| <= 5e-6` for all 75 | yes |
| 8 | **Harness reproduction** | `t2c_correlation(dinoL518,75,0, committed_ES)` reproduces `b1_faithful_correlation.json['dinoL518']` ρ **bit-identically**, with `clusters_used == 50` and `n_target_in_used == 3428` | yes |
| 9 | Scorer validation | `abc_evaluate.score('Dataset/Test/COD10K/GT','Result/SINet/S2C')` reproduces Sα **0.717216** / MAE **0.074463** to `< 1e-5` | yes |
| 10 | Provenance | `E0.step_independence()` called unchanged; `n_forbidden == 0`; `inputs_missing` empty | yes |
| 11 | Checkpoint identity | sha256 of all 8 `.pth` recorded and matched against §7 | yes |
| 12 | Boundary coverage | `n_boundary_empty / 4040 <= 0.05` per architecture | yes |

**Gate 8 is the cheapest and strongest.** It consumes the *committed* ES CSV — not a fresh forward —
so it is pure arithmetic through the same functions with the same RNG seed, and bit-exact equality is
achievable. It proves T2-C's harness **is** B1's harness before any new signal enters. Zero GPU.

**Tolerances are satisfiable by construction** — the T2 Addendum A1 lesson. Gate 4 is tight (1e-6)
because it compares two reductions of the *same* tensors. Gates 6/7 are looser because B1's scoring
set no cudnn determinism flags, so a fresh forward can differ from the committed one by more than
float-reduction noise. Gate 7's 5e-6 exceeds the 5e-7 admitted by 6-dp storage alone. **No gate
compares a full-precision float against a rounded reference at a tolerance finer than the rounding.**

### Gate 1 — the target-side invariant, as concrete assertions

```
A. PATH        every image path the signal loader opened starts with Dataset/Target/ ,
               and no path contains Dataset/Test/ or Dataset/Val/.
               Dataset/Target/ has no GT subdirectory at all -- only Image/ .
B. KEY SPACE   set(signal) >= set(a['target_names'])            # 4033, all ending .jpg
               set(signal) & set(endpoint_stems) == empty        # the two key spaces are disjoint
C. COUNT       len(signal) == 4040  before the join;  4033 after restriction to target_names
D. CARDINALITY at seed 0:  clusters_used == 50  and  n_target_in_used == 3428
               (B1's committed values; an endpoint-side signal cannot produce 3428)
```

Any failure raises `RuntimeError('T2C HALT: ...')` **before** any ρ is computed. This is an
assertion, not a convention, because it is a one-line mistake that produces a publishable-looking,
entirely non-comparable result.

### Gate 3 — the T2-C-appropriate signal gate

C1/ABC's `gate_signal` AST-bans the literal endpoint-ES column name (`c1_preflight.py:65`, enforced
`abc_preflight.py:77-101`). **T2-C must not adopt it unmodified: T2-C legitimately reads endpoint
error, so that ban would fail the build by construction.** B1 itself reads these quantities and is
the correct precedent.

T2-C's gate instead:

- **asserts** every signal is target-side (Gate 1) — the substantive property that ban was
  protecting;
- **permits** reading endpoint error via `B1.load_scores(arch, 'test')`;
- **bans** `B1.step_correlate` (the same-side function) by AST call-scan;
- **bans** `sklearn.cluster` imports and direct `KMeans(` construction — clustering goes through
  `B1.fit_kmeans` only, reusing C1's `BANNED_CLUSTER_CALLS`/`BANNED_CLUSTER_MODULES`;
- **reuses** `E0.step_independence()` unchanged for the archive/scratchpad scan.

`c1_preflight._c1_sources()` and `abc_preflight._abc_sources()` are **directory-local globs** and see
nothing under `rebuild/T2C/`, so T2-C binds its own `_scan` over `rebuild/T2C/*.py`, mirroring
`abc_preflight._scan` (`:58-71`) and reusing `PF.docstring_ids` and `PF.PRAGMA` — no second pragma is
invented.

**Declared for the record:** T2-C is a **correlation study**. The allocation-signal ban does not
apply to it, and **no T2-C output is ever used to allocate.**

## §7 Provenance to be recorded

No `.pth` is hashed anywhere in `rebuild/` today; integrity rests on the tensor-copy assertion. T2-C
records all eight:

```
Snapshot/SINet/S2C/{Tea_epoch_best,Stu_40}.pth
Snapshot/SINet-v2/S2C/{Tea_epoch_best,Stu_100}.pth
Snapshot/ABC/{SINet,SINetv2}_{A0,CSHUF}_s{42,43,45}/Tea_epoch_best.pth
```

A0 reference hashes, measured 2026-09-11 before any T2-C code existed:

```
7902923839f26cfbbe5f8705b69b9221565cb0877adcb72bd9b32e15a1142646  SINet_A0_s42
391c62df5f5996f7c731c111fa7ed86e2d14fd02e0a3c573e21b161ee4af3907  SINet_A0_s43
8c868b4ef2dcd6abf7d314b2ee7cc432480d92149126be62ac5b25bca20fde79  SINet_A0_s45
ec2bc90311dda6c71f1fdb36c83e0ab732e9cc43b89972b7dc445bee3c3cae8d  SINetv2_A0_s42
065ebe6124de1c1ae15c8839a1a3958f7f14eec00b0276f86e061d87246c6e2d  SINetv2_A0_s43
e2a2404160af380fe5f4ccd560733e09769409dd5b342e21d371e4f43edf7379  SINetv2_A0_s45
```

All six distinct — the 3-member ensemble is 3 genuinely different networks.
`rebuild/ABC/out/abc_runs.csv` corroborates independent training: distinct `wall_min`
(104.5/105.7/107.3), distinct round-2 pool sizes (**6313/6179/6243**) and distinct `best_epoch`
(32/28/27). A copied checkpoint cannot produce a different CLS round-2 pool.

**Disclosed defect:** `SINet_A0_s42` has an **empty `returncode`** field where every other row has
`0`. `wall_min` and both pool sizes are recorded, so the run completed; this is a logging gap, and it
is reported rather than discovered later.

**Also disclosed:** the `.pth` files and the E0 `.npy` caches are **untracked and gitignored**. They
exist on this machine and are not recoverable from the repository. Inherited from B1 and A/B/C, not
introduced here.

## §8 The comparison table

Per architecture (**SINet**, **SINet-v2**); SegMaR is out of scope (no A0 ensemble under
`Snapshot/ABC/`).

| signal | aggregation | ρ(MAE) ± sd | ρ(1−Sα) ± sd | ρ(1−IoU) ± sd | ordering pass | ratio (Δ vs 0.5463) |
|---|---|---|---|---|---|---|
| ES (re-derived) | whole | | | | | |
| ES (re-derived) | boundary | | | | | |
| entropy | whole | | | | | |
| entropy | boundary | | | | | |
| ensemble A0 | whole | | | | | |
| ensemble A0 | boundary | | | | | |
| ensemble CSHUF | whole | | | | | |
| ensemble CSHUF | boundary | | | | | |

- **ρ** is the seed-0 value; **sd** is over 10 k-means seeds.
- **ordering pass** = `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)` at seed 0 — B1's committed criterion
  (`b1_allocation_signal.py:360`). The per-seed fraction (e.g. `9/10`) is reported beside it as a
  robustness measure. The seed-0 value is the pre-registered decision.
- **ratio** = ρ(1−Sα)/ρ(MAE), with its own 10-seed sd, benchmarked against ES's committed **0.5463**
  — never against 0.5.
- The **ES / whole** row must equal B1's committed `+0.6284 / +0.3433 / +0.2613` and ratio `0.5463`
  at seed 0. It is a validation row, not a result.
- Every ensemble row carries the member spread and arm sd from §3.3 inline.

Free robustness variants, same forwards: entropy clamp 1e-12; band `iters=1` (2 px);
ensemble `mean(sd)` instead of `mean(var)`; ensemble per-signal band.

## §9 What T2-C can and cannot conclude

Fixed before any number exists.

**All three signals show `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)`** → the gap is **not** ES-specific.
Reported as: uncertainty signals available to this pipeline track pixel-level error substantially
better than structural error on COD10K. Task-level, correlational.

**Signals disagree on the ordering** → the gap is **ES-specific**, and §6(v)'s reasoning cannot be
generalised to uncertainty signals as a class. Reported as-is.

**The three-way boundary reading**, pre-committed:

| outcome | reading |
|---|---|
| whole-image predicts neither | background drowns the signal; the whole-image null is uninformative about structure |
| boundary predicts pixel but not structure | **strongest general claim** — uncertainty carries no localisation information even where localisation lives |
| boundary predicts structure | **constructive finding** — uncertainty *is* informative at the boundary, and standard whole-image aggregation discards it |

**Hard limits.**

- **Correlational, not causal.** T2-C establishes a **strong prior** that uncertainty-guidance fails
  for COD. It is **not proof that every signal fails in training**. T2 tested ES's *direction* on
  trained accuracy and found WITHIN NOISE; a correlation cannot be upgraded into a causal claim.
- **One endpoint** (§2).
- **Two signals, one aggregation family, two architectures.** Not a survey of uncertainty
  quantification.
- **Ensemble rows are the weakest**: n=3, heterogeneous members, and a model mismatch against the
  error column (§3.3).
- **ρ differences below ~0.06 are not interpreted** (§5).

## §10 Run accounting

**Order of operations.** Signals → gates (incl. the target-side HALT) → scorer validation →
correlations → verdict block. No ρ is computed before every gate passes.

**Sanity step, before the full matrix.** One signal end-to-end: SINet, entropy-whole, seed 0 only.
It must (a) pass Gate 1, (b) pass Gate 8, (c) return `clusters_used == 50` and
`n_target_in_used == 3428`. Deliberately includes a **negative control**: the invariant is re-run
against a deliberately stem-keyed signal dict and must HALT. Only then does the full matrix run.

**Compute — inference only.** Per architecture, per target image: 2 forwards (S2C student + teacher,
serving the ES map, teacher entropy and the shared band) + 3 (A0) + 3 (CSHUF) = **8**.

| | forwards |
|---|---|
| 8 × 4040 × 2 architectures | **64,640** |
| all boundary / robustness variants | **0** — aggregation only, same forwards |
| scorer validation | 0 — CPU scoring of 2026 stored PNGs |

**Wall-clock: ESTIMATE, NOT MEASURED.** No committed block records a wall time for target-side
scoring. Derived from A/B/C inference throughput at ~500–1500 img/min for a single 352×352 forward:
**≈ 50–130 GPU-minutes ≈ 25–65 min wall-clock across the 2 GPUs**, plus ~1–3 min for ten k-means
fits and well under a minute of correlation. **This corrects the scoping estimate of 32,320
forwards**, which omitted the student forward required by the re-derived ES row and the CSHUF
sensitivity arm — both locked in.

**No training. No checkpoint written. No pool built. No partition fit.**

## §11 Additivity

Writes only under `rebuild/T2C/out/`. Appends `EXP T2C` blocks to `results/REBUILD_LOG.txt` via
`C.log_block(..., trains='NO')`. Overwrites no committed artifact.

Explicitly **not called**: `b1_allocation_signal.main()` (which unconditionally rewrites
`b1_cluster_es_<tag>.csv` at `:216` and three JSONs) and `b1_es_error_correlation.main()` (which
calls `emit_cluster_es` unconditionally at `:867`). T2-C calls **leaf functions only**.

`augment_cluster_csv` is never called. The 7 D2-leaked names are excluded by reading
`d2_leaked_names.json` through `B1.load_target`, never hardcoded.

No `/tmp/…`, `/scratchpad`, `evidence/artifacts` or `_archive_stageC_old` literal appears in any
T2-C file — `E0.step_independence()` walks all of `rebuild/`, so such a literal would fail C1 gate 6
and ABC G2 for **every other experiment**, not just this one.

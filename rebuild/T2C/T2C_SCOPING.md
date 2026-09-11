# T2C_SCOPING.md — pre-execution scoping audit

> **Nothing was computed, trained or scripted for this document.** It is a read-only audit of
> committed code, committed artifacts and data on disk. Every DECISION cites `file:line` or a
> `results/REBUILD_LOG.txt` line number. Where the answer is not determinable from what is committed,
> the item is marked **UNRESOLVED** and says what is needed. No gap is filled with a plausible guess.
>
> Dated 2026-09-11. Audit target: **T2-C** — is the pixel-vs-structure correlation gap found for ES in
> B1 specific to ES, or general to uncertainty signals for COD?

**STATUS SUMMARY: 11 SETTLED · 8 NEEDS-YOUR-CALL · 1 UNRESOLVED** (§5.2 NC4K, which also needs your
call). Three items would change the shape of the experiment rather than just its parameters: the
ratio threshold that **fails on ES itself** (§6.2), the entropy aggregation (§3.2), and NC4K's
unavailability (§5.2). Read §10 and §11 first if short on time.

---

## §1 Reused clustering — the inherited partition

**DECISION.** T2-C uses B1's committed `dinoL518, k=75, kmeans_seed=0` partition and **fits no
clustering of its own**. It must read the committed assignment file directly rather than refit.

**EVIDENCE.**
- Artifact: `rebuild/B1/out/b1_cluster_assignment_dinoL518.json` (declares `k=75`, `seed=0`,
  `embedder='dinoL518'`) plus `rebuild/B1/out/b1_cluster_es_dinoL518.csv` — **75 data rows**, columns
  `cluster,k,kmeans_seed,n_target,target_es,n_target_scored,centroid_norm,n_test,test_es,test_mae,
  test_one_minus_sa,test_one_minus_iou,n_val,val_es,val_mae,val_one_minus_sa,val_one_minus_iou`.
- Centroids: `rebuild/B1/out/b1_centroids_dinoL518_k75_seed0.npy`.
- Same partition C1/ABC/T2 consumed, via the single sanctioned accessor
  `rebuild/C1/c1_space.py:93-99` (`load_space`), which asserts its own tag.
- Direct `np.load` of `rebuild/E0/cache/*.npy` is **forbidden** — `ABC_PLAN.md:238-240`.
- The committed T2 block re-verified this partition end-to-end on 2026-09-10
  (`results/REBUILD_LOG.txt:2295`, C10 reproduces C1's cell on all five keys).

**STATUS: SETTLED.**

### §1.1 The floors — there are TWO, not one

**DECISION.** Two independent floors gate a cluster into the target-side correlation:

| floor | constant | applies to | clusters passing |
|---|---|---|---|
| ≥ 15 endpoint images | `MIN_CLUSTER_N = 15` | COD10K-test images in the cluster | **50 of 75** |
| ≥ 5 target images scored | literal `ces[c][1] >= 5` | target images in the cluster | **75 of 75** |
| ≥ 5 clusters for any ρ | `MIN_CLUSTERS_FOR_RHO = 5` | the correlation itself | n/a |

**EVIDENCE.** `b1_es_error_correlation.py:81-86` (both constants, with the rationale that Spearman on
n=2 is always ±1); `b1_allocation_signal.py:170-172` — `used = sorted(c for c in err if len(err[c])
>= min_n and c in ces and ces[c][1] >= 5)`. Verified against the committed CSV: `n_test >= 15` → 50
clusters; `n_target_scored >= 5` → 75; **both** → 50, matching the logged "50 clusters"
(`REBUILD_LOG.txt:1005`). `sum(n_test) = 2026` = COD10K-test size.

**The ≥15 endpoint floor is the binding one.** The ≥5 target floor is currently non-binding but must
still be applied, because T2-C's new signals are also target-side means and a cluster with 1–4 target
images would give a meaningless mean.

**STATUS: SETTLED** — and note the second floor was not in the brief; it is real and must be carried.

### §1.2 The 7 D2-leaked exclusions

**DECISION.** 7 target names are dropped before clustering; the target set is **4040 → 4033**.
T2-C must read the exclusion list from D2's artifact, never hardcode names.

**EVIDENCE.** `rebuild/D2/out/d2_leaked_names.json`: `n_target_excluded = 7`,
`target_names_to_exclude` has 7 entries, `endpoint_side = 7`, `method = "full pairwise hashing of file
bytes and decoded RGB; NOT name matching. Consumers must read this file rather than hardcode a name
list"`. Consumed at `b1_es_error_correlation.py:53` (`D2_LEAKED`) and `:330-338` (`load_target` —
*"Target embeddings with D2's MEASURED leaked names excluded"*). Consistent with
`sum(n_target) = 4033` in the committed CSV.

**STATUS: SETTLED.**

### §1.3 Which seed the headline ρ came from

**DECISION.** B1's committed target-side ρ is from the **single committed seed-0 partition**, not a
multi-seed mean. T2-C should match that.

**EVIDENCE.** `b1_allocation_signal.py:320` — `f = faithful_correlation(tag, a['k'], a['seed'], prim)`
where `a` is the committed assignment JSON (`seed=0`). `fit_kmeans` is deterministic and cached per
`(tag,k,seed)` with `KMeans(k, n_init=10, random_state=seed)` (`b1_es_error_correlation.py:428-442`).

**CAVEAT THAT MATTERS FOR THE DECISION RULE.** A single-seed ρ carries **no uncertainty estimate**.
B1's *endpoint-side* per-cluster correlation was run over 10 k-means seeds and reported
`+0.8699 ± 0.0297` (`REBUILD_LOG.txt:788`). If ±0.03 is the scale of clustering-induced ρ noise, then
**ρ differences below ≈0.06 between signals are not distinguishable at one seed.** T2-C's whole claim
is a comparison of ρ values, so this is load-bearing.

**STATUS: NEEDS YOUR CALL** — single committed seed (comparable to B1's headline, no error bars) vs
10 seeds per signal (error bars, ~10× the clustering cost, still inference-free).
**Recommendation: do both** — seed 0 as the headline for comparability with B1, plus the 10-seed sd
as the yardstick for whether any two signals actually differ.

---

## §2 Which checkpoints supply each signal — the highest-risk item

### §2.1 What exists on disk (verified)

| path | contents | role |
|---|---|---|
| `Snapshot/SINet/S2C/` | `Tea_epoch_best.pth`, `Stu_40.pth` | **the checkpoints B1's ES used** |
| `Snapshot/SINet-v2/S2C/` | `Tea_epoch_best.pth`, `Stu_100.pth`, `Stu_40.pth` | B1's ES, second architecture |
| `Snapshot/SegMaR/S2C/` | (present) | B1's third architecture; out of T2-C scope |
| `Snapshot/ABC/{SINet,SINetv2}_A0_s{42,43,45}/` | `Tea_epoch_best.pth` × 6, all present | ensemble candidates |

### §2.2 Predictive entropy — which model?

**DECISION (conditional).** To be comparable with ES, entropy must come from the **same checkpoints
ES came from**: `Snapshot/<arch>/S2C/`. But ES is a *student–teacher pair*, and entropy is a
*single-model* quantity — so "the same checkpoint" is ambiguous and must be chosen explicitly.

**EVIDENCE.** `b1_allocation_signal.py:86-92`:
```
spec = B1.ARCHS[arch]
snap = os.path.join(C.REPO, 'Snapshot', arch)
stu = B1._load_net(...); tea = B1._load_net(...)
B1._load_ckpt(stu, os.path.join(snap, spec['stu']), device)      # Stu_40.pth  (SINet)
B1._load_ckpt(tea, os.path.join(snap, 'Tea_epoch_best.pth'), device)
```
`ARCHS` (`b1_es_error_correlation.py:70-76`): `'SINet/S2C'` → `stu='Stu_40.pth'`, `primary=True`;
`'SINet-v2/S2C'` → `stu='Stu_100.pth'`, `primary=False`.

So ES consumes **both** `Tea_epoch_best.pth` and `Stu_40.pth` (resp. `Stu_100.pth`).

**Recommendation:** entropy from **`Tea_epoch_best.pth`** of `Snapshot/<arch>/S2C/` — the EMA teacher
is the model CLS actually uses to generate pseudo-labels (`CLS.py:65-75` fallback logic), so its
entropy is the allocation-relevant quantity, and it is one of the two nets ES is built from. The
student is the alternative and would also be defensible.

**STATUS: NEEDS YOUR CALL** (teacher vs student). Recommendation: teacher.

### §2.3 Ensemble disagreement — the arm choice is a confound, and A0 is the worst available

**DECISION (conditional).** A 3-member ensemble **must** come from `Snapshot/ABC/*_A0_s{42,43,45}/`,
because only one checkpoint exists per architecture under `Snapshot/<arch>/S2C/`. All 6 are present.
They are genuinely independent runs — different `--seed`, cudnn determinism declared, verified per the
A/B/C record. **But A0's three members are severely heterogeneous in quality.**

**EVIDENCE (committed, `rebuild/ABC/out/abc_metrics.csv` and `abc_runs.csv`).**

| member | Sα COD10K | best_epoch |
|---|---|---|
| SINet_A0_s42 | 0.715086 | 32 |
| SINet_A0_s43 | **0.681706** | 28 |
| SINet_A0_s45 | 0.706058 | 27 |
| SINetv2_A0_s42 | 0.688813 | 92 |
| SINetv2_A0_s43 | **0.678740** | 99 |
| SINetv2_A0_s45 | 0.699883 | 62 |

SINet A0 spread is **0.0334 Sα** — s43 is 0.033 worse than s42. A/B/C's committed per-arm sd confirms
A0 is the outlier arm: **0.017266** on SINet|COD10K, against A2 0.001930, B 0.001807, C10 0.004059,
CSHUF 0.001655, CINV 0.002853 (`rebuild/ABC/out/abc_sigma.json`). A0 is an **order of magnitude**
more variable than every other arm. SINet-v2 members were also selected at wildly different epochs
(92 / 99 / 62), on CAMO-val, which is a second axis of heterogeneity.

**Why this is a confound, not a nuisance.** Ensemble disagreement is supposed to measure *where the
data is uncertain*. With one member 0.033 Sα worse than another, a large part of the disagreement
measures *which member is bad*, not *which image is hard*. That inflates disagreement systematically
on images the weak member fails — and a weak model fails most on large-error images, which is exactly
the pixel-error axis T2-C is trying to separate from the structural axis. **The confound pushes in the
direction of the hypothesis**, which is the dangerous direction.

**Options:**
1. **A0** — matches ES's data configuration (base pool only, the authors' setup) but members are
   heterogeneous (sd 0.0173).
2. **CSHUF / B / A2** — homogeneous members (sd 0.0017–0.0019, ~10× tighter) but trained with +1000
   synthetic images, so a different model family from the ES/entropy model.
3. **Both**, A0 as the configuration-matched primary with the spread disclosed, one homogeneous arm as
   a pre-registered sensitivity check.

**STATUS: NEEDS YOUR CALL.** Recommendation: **option 3** — A0 primary (configuration-matched to ES),
with the 0.0334 spread reported beside every ensemble ρ, plus CSHUF (tightest arm, sd 0.001655) as a
pre-registered sensitivity arm. If the two disagree, the ensemble result is about member quality and
must be reported as uninterpretable rather than as a finding.

**Also flag, as instructed:** 3 members is very low-powered. A 3-sample variance has ~70% relative
standard error; the per-cluster mean over ≥15 images recovers some of that, but the ensemble signal is
categorically weaker evidence than entropy or ES.

### §2.4 Both architectures runnable?

**DECISION.** Yes for both signals, for **SINet** and **SINet-v2**. ES baselines are committed for
both (`b1_scores_SINet-S2C_test.csv`, `b1_scores_SINet-v2-S2C_test.csv`,
`b1_target_es_SINet-S2C.csv`, `b1_target_es_SINet-v2-S2C.csv`, 4040 rows each). SegMaR has ES
artifacts too but **no A0 ensemble** under `Snapshot/ABC/`, so SegMaR is entropy-only and is
recommended out of scope.

**EVIDENCE.** `ls rebuild/B1/out/` (5 archs × target_es + test/val scores); `Snapshot/ABC/` contains
only `SINet_*` and `SINetv2_*` RUNIDs.

**STATUS: SETTLED** (SINet + SINet-v2 in; SegMaR out).

---

## §3 Signal definitions

### §3.1 The comparability premise in the brief does not survive contact with the code

**This is the finding that most changes the experiment's design.**

ES is **not** a per-pixel uncertainty averaged over an image. `Src/utils/tool.py:45-77`:

```
edge_pred   = sqrt(Sobel_x(pred)^2   + Sobel_y(pred)^2   + 1e-8)
edge_target = sqrt(Sobel_x(target)^2 + Sobel_y(target)^2 + 1e-8)
edge_loss   = F.l1_loss(edge_pred, edge_target)          # whole-image mean
region_loss = F.binary_cross_entropy(pred, target)       # whole-image mean, unweighted
return self.a * edge_loss + self.b * region_loss
```

with committed live config **a = 0.9, b = 0.3, c = 0.5, `use_weighted_bce=False`**
(`REBUILD_LOG.txt:767-768`, parsed from MyTrain.py's `--task S2C` override block, not hardcoded;
threshold at `:817` asserts the live loss matches it, and that CLS calls it on sigmoid outputs).

So **ES = 0.9 · mean|Sobel(student) − Sobel(teacher)|₁ + 0.3 · mean BCE(student, teacher)**, where
`target` is the *teacher's* sigmoid, not ground truth.

Three consequences:
1. **ES is predominantly an edge-disagreement measure** (weight 0.9 vs 0.3) — and it *still* correlates
   with pixel MAE (+0.6284) far better than with structural 1−Sα (+0.3433). The signal that most
   obviously ought to track structure, because three-quarters of its weight is a boundary term,
   does not. This strengthens T2-C's motivation and should be stated in the pre-registration.
2. **"Aggregate entropy the same way as ES" is ill-defined.** ES has no single aggregation: it is a
   weighted sum of two whole-image means over two different per-pixel fields, one of which has no
   single-model analogue (there is no "edge disagreement" for one network's entropy).
3. The closest defensible analogue is ES's **region term**: a whole-image mean of a per-pixel scalar.
   That makes whole-image-mean entropy the honest primary, with ES's edge term motivating — not
   satisfying — the boundary-restricted variant.

**STATUS: NEEDS YOUR CALL** on what "comparable to ES" is declared to mean. Recommendation: declare
comparability as *same images, same clusters, same resolution, same floors, same ρ statistic* —
explicitly **not** "same functional form", and say so in the pre-registration rather than implying an
equivalence the code does not support.

### §3.2 Predictive entropy — definition

**DECISION.** Per-pixel binary entropy of the sigmoid output:
`H(p) = −p·log₂(p) − (1−p)·log₂(1−p)`, `p = σ(logit)`, with clamping (e.g. `p ∈ [1e-6, 1−1e-6]`) to
keep `log` finite. Log base and clamp value must be fixed in the pre-registration (they change the
scale, not the Spearman ρ — ρ is invariant to any monotone transform, which is worth stating as the
reason the choice is low-risk).

**Aggregation to a per-image scalar — the critical COD-specific decision.** Background dominates a COD
image and boundary is where structure lives, so the three candidates are not interchangeable:

| aggregation | definition | what it measures |
|---|---|---|
| **whole-image mean** | mean H over all 352×352 pixels | dominated by easy background; closest analogue to ES's region term |
| **foreground-region mean** | mean H over `σ(logit) > 0.5` | confined to the predicted object; circular (the mask is the prediction) |
| **boundary-restricted mean** | mean H over a band around the predicted contour | where structure/localisation actually lives |

**Recommendation: compute whole-image AND boundary-restricted at minimum**, both pre-registered,
whole-image as primary (comparable to ES's region term) and boundary-restricted as the surgical test.
Foreground-region is recommended as a third if cheap, flagged as prediction-dependent.

**Boundary band definition.** Recommend `dilate(M, k) − erode(M, k)` where `M = σ(logit) > 0.5`, with
a **precedent in the repo**: `rebuild/D2_reaudit/d2r_reaudit.py:565-566` uses
`cv2.erode(fg, np.ones((3,3)), iterations=1)` and `boundary = fg − eroded` — an *inner* band only. A
symmetric dilation−erosion band is the better choice here because entropy is highest *straddling* the
contour, but the kernel size and iteration count are free parameters. At 352×352 a 3×3 kernel with
1 iteration gives a ~2px band, which may be too thin to be stable; 5×5 or 2 iterations gives ~4px.

**STATUS: NEEDS YOUR CALL** — (a) which aggregations are in, (b) the band kernel/iterations.
Recommendation: whole-image + boundary at dilate/erode 3×3 with **2 iterations** (~4px band), band
width pre-registered and reported, with the ~2px variant as a robustness check since it is free once
the forward pass is done.

### §3.3 Ensemble disagreement — definition

**DECISION.** Across the 3 members' per-pixel probabilities `p₁,p₂,p₃`:
- **Recommended:** per-pixel **variance** (population, `ddof=0`), then aggregated identically to
  entropy. It is the standard ensemble-uncertainty statistic and extends to >3 members unchanged.
- Alternative: mean pairwise absolute difference `⅓(|p₁−p₂|+|p₁−p₃|+|p₂−p₃|)`. At n=3 this is a
  near-monotone function of the sd, so **Spearman ρ will be nearly identical** — the choice is
  low-risk and should be stated rather than agonised over.

**What it measures, stated for the record.** Same data, same architecture, same hyperparameters, same
pool — **only the training seed differs** (`abc_common.py:43`, `SEEDS = (42,43,45)`; per-seed via
`MyTrain.py --seed`). So this is **optimisation-stochasticity disagreement only**. It is not epistemic
uncertainty about the data distribution, and must not be reported as such. Compounded by §2.3's member
heterogeneity and by n=3.

**STATUS: SETTLED on the statistic** (variance, with the note that pairwise-|Δ| is equivalent under ρ);
**inherits §2.3's NEEDS-YOUR-CALL** on which arm supplies the members.

### §3.4 Resolution

**DECISION.** All signals at **352×352 with ImageNet normalisation**, identical to ES.

**EVIDENCE.** `b1_es_error_correlation.py:78` — `TESTSIZE = 352`; `b1_allocation_signal.py:93-94` —
`T.Resize((B1.TESTSIZE, B1.TESTSIZE))`, `T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])`;
`REBUILD_LOG.txt` B1 REPR line — *"R1 whole target image (dinoL518) for clustering; 352x352 +
ImageNet norm for inference; ES on sigmoid outputs"*. Clustering embeddings are a separate
representation (dinoL518 on the whole image) and are **not** affected by this.

**STATUS: SETTLED.**

---

## §4 The comparison to ES — the two-sided structure

### §4.1 B1's actual structure, which T2-C must reproduce exactly

**DECISION.** The correlation is **cross-side**: signal on the *target* set (no GT), true error on the
*labeled endpoint*, joined by cluster. T2-C reproduces this.

**EVIDENCE.** `b1_allocation_signal.py:150-192`, `faithful_correlation` — docstring: *"Per-cluster
TARGET ES vs per-cluster ENDPOINT error. The allocation signal on one side, the thing it is meant to
predict on the other. Both aggregated over the same cluster partition."*

```
ces  = cluster_target_es(tag, k, seed, tgt_es)         # per-cluster mean TARGET-side signal
rows = B1.load_scores(arch, 'test')                    # per-image ENDPOINT error (COD10K)
amap = B1.assign_clusters(X, tnames, k, seed, 'test', tag)   # endpoint images -> target centroids
used = [c for c in err if len(err[c]) >= 15 and ces[c][1] >= 5]
a = [ces[c][0] for c in used]                          # target-side signal means
b = [mean(r[e] for r in err[c]) for c in used]         # endpoint error means
rho, p, ci = B1.spearman_perm(a, b, n_perm=2000, seed=seed)
```

`assign_clusters` (`b1_es_error_correlation.py:461-467`) — *"k-means on the target, then assign
endpoint images to those centroids"*: endpoint embeddings are assigned by `argmax(E @ centroids.T)`
on L2-normalised vectors. **The endpoint never influences the partition.**

**The distinction the brief flags is real and is a genuine trap.** `b1_es_error_correlation.py:493-540`
(`step_correlate`) computes a **same-side** correlation — ES and error from the *same* endpoint rows —
and that is the *easier* question. Both quantities are committed and they differ substantially:

| dinoL518, k=75, 50 clusters | MAE | 1−Sα | 1−IoU | 1−Sα / MAE |
|---|---|---|---|---|
| **target-side ES vs endpoint error** *(the T2-C structure)* | **+0.6284** | **+0.3433** | +0.2613 | **0.5463** |
| endpoint-side ES, same clusters *(the easier question)* | +0.8754 | +0.3810 | +0.2304 | 0.4352 |
| ρ(target ES, endpoint ES) per cluster | | | | 0.5732 |

**EVIDENCE.** `REBUILD_LOG.txt:1005-1008`. The two ES variants agree only at ρ=0.5732 per cluster —
they are **not interchangeable**. Using the endpoint-side version would be a different, easier
experiment and would not be comparable to B1's headline.

**STATUS: SETTLED** — target-side signal, endpoint-side error, joined by the committed partition.
Both floors from §1.1. Must be asserted in code, not assumed.

### §4.2 ES baseline availability for side-by-side reporting

**DECISION.** Available and committed at both the per-image and per-cluster level, for both
architectures — no recomputation needed for the ES column.

**EVIDENCE.** Per-image target ES: `rebuild/B1/out/b1_target_es_SINet-S2C.csv` and
`b1_target_es_SINet-v2-S2C.csv`, **4040 rows each**. Per-cluster: `target_es` populated **75/75** in
`b1_cluster_es_dinoL518.csv`. Per-cluster endpoint error: `test_mae`, `test_one_minus_sa`,
`test_one_minus_iou` populated **75/75**. Full correlation record:
`rebuild/B1/out/b1_faithful_correlation.json`.

**STATUS: SETTLED.**

---

## §5 True-error targets

### §5.1 COD10K (primary) — reuse, no recomputation

**DECISION.** Per-cluster MAE, 1−Sα, 1−IoU on COD10K-test are **already committed**; T2-C reuses them
and computes no new error metric for the primary endpoint.

**EVIDENCE.** `b1_cluster_es_dinoL518.csv` — `test_mae`, `test_one_minus_sa`, `test_one_minus_iou` all
75/75 populated; `sum(n_test) = 2026` = COD10K-test. Per-image source:
`rebuild/B1/out/b1_scores_SINet-S2C_test.csv` with fields `es, mae, sa, one_minus_sa, iou,
one_minus_iou, one_minus_iou_soft, gt_fg_frac` (`b1_es_error_correlation.py:313-322`).
`ERRORS = ('mae','one_minus_sa','one_minus_iou')` (`:88`).

**Scorer validation gate.** The `< 1e-5` reproduction of B1's committed Sα 0.717216 / MAE 0.074463 is
implemented at `rebuild/ABC/abc_evaluate.py:43,131-140` and passed in T2's run
(`Sα 0.7172156`, Δ 3.8e-07). T2-C must run the same gate before any correlation **if** it recomputes
any error; if it consumes B1's committed per-cluster values unchanged, the gate reduces to asserting
the CSV's provenance. **Note:** T2's Addendum A1 documents that a `< 1e-9` comparison against a
6-dp-stored reference is unsatisfiable — T2-C must not repeat that mistake; compare at 6 dp.

**STATUS: SETTLED.**

### §5.2 NC4K (secondary) — NOT AVAILABLE

**DECISION: UNRESOLVED.** NC4K cannot be used as a secondary endpoint without new work outside T2-C's
stated inference-only scope. Three separate things are missing:

1. **No embeddings.** `ls rebuild/E0/cache/` contains `dinoL518_{auth,cut,local,raw,test,tgt,val}_*` —
   **no `nc4k`**. Cluster assignment for NC4K's 4121 images is therefore impossible without an E0 run.
2. **NC4K is not a B1 split.** `b1_es_error_correlation.py:60-64` — `SPLITS` = `test` (COD10K,
   PRIMARY) and `val` (CAMO, checkpoint-selection only). `endpoint_emb` (`:449-458`) reads
   `%s_%s_cls.npy % (tag, split)` and would fail for `nc4k`.
3. **No per-cluster NC4K error.** The committed CSV has `test_*` and `val_*` columns only.

NC4K *is* declared as a primary input — `rebuild/common.py:65`,
`'nc4k': dict(path='Dataset/Test/NC4K/Imgs', n=4121, repr='R1-full')` — and ABC/T2 predictions exist
under `Result/ABC/*/NC4K/`, but those are ABC-arm models, not the `Snapshot/<arch>/S2C` model whose
signal T2-C measures.

**WHAT IS NEEDED:** either (a) drop NC4K and declare COD10K the sole endpoint, or (b) scope an E0
embedding pass for `nc4k` plus a B1-style scoring pass of `Snapshot/<arch>/S2C` on NC4K — both new
work, pre-registered separately.

**STATUS: UNRESOLVED — NEEDS YOUR CALL.** Recommendation: **(a) drop NC4K**, declare COD10K-test the
sole endpoint, and state the single-endpoint limitation in the pre-registration. It keeps T2-C
inference-only and honest. CHAMELEON stays excluded (D2: 10 of 76 images are re-encodes of Target
images, `REBUILD_LOG.txt:364`); CAMO stays selection-only (`SPLITS[val]['role']`).

---

## §6 The pre-registered claim and decision rule

### §6.1 What `PREREGISTRATION_T2C.md` must contain

**DECISION.** A separate, dated, additive pre-registration committed **before any correlation is
computed**, specifying at minimum:

1. **Signals**, exactly: ES (committed, reused), predictive entropy (checkpoint per §2.2, definition
   per §3.2), ensemble disagreement (arm per §2.3, statistic per §3.3).
2. **Aggregations**, exactly: which of whole-image / foreground / boundary are in, and the boundary
   band's kernel and iteration count (§3.2).
3. **Structure**: target-side signal, endpoint-side error, committed seed-0 `dinoL518 k=75` partition,
   both floors (≥15 endpoint, ≥5 target), 352×352, ImageNet norm.
4. **Statistic**: Spearman ρ per cluster, per signal, per error type (`mae`, `one_minus_sa`,
   `one_minus_iou`), per architecture, with `spearman_perm`'s permutation p and bootstrap CI
   (`b1_es_error_correlation.py:470-491`) — reusing B1's function, not a new one.
5. **The reported quantity**: the ratio `ρ(1−Sα) / ρ(MAE)` per signal, which B1 already computes for
   ES (`b1_allocation_signal.py:346`, committed as `FAITHFUL_ratio_1mSa_over_MAE_dinoL518 = 0.5463`).
6. **Interpretation fixed in advance** (see §6.2 — the drafted threshold needs changing).
7. **The honest limit**, pre-committed: this is **correlational, not a training test**. It establishes
   a prior that uncertainty-guided allocation fails for COD; it is not proof for every signal or every
   aggregation. T2 (the training test) found WITHIN NOISE for ES's *direction*; T2-C cannot upgrade a
   correlation into a causal claim.

**STATUS: SETTLED as a specification** (the document does not exist yet).

### §6.2 The drafted threshold fails on ES itself — this must be fixed before it is frozen

**DECISION: the brief's proposed rule is not usable as written.**

The drafted criterion is *"if all three signals show ρ(structural) < ~0.5·ρ(pixel), the gap is a
general property."* Applied to ES, the signal that motivated the study:

```
ρ(1-Sa) / ρ(MAE)  =  0.3433 / 0.6284  =  0.5463        >  0.5
```

**ES itself does not clear the threshold.** `REBUILD_LOG.txt:1005` and `:1008`
(`FAITHFUL_ratio_1mSa_over_MAE_dinoL518 = 0.5463`). Freezing `< 0.5` would classify the reference
signal as *not* exhibiting the gap it was named for, and any new signal landing at 0.52 would be
scored inconsistently with ES.

For context, the same ratio in the other committed spaces: dinoL224 **0.5166**, clipL224 **0.3333**
(degenerate, k=5), and the endpoint-side variant **0.4352** (`REBUILD_LOG.txt:1004,1008,1012-1013`).
Note the 1−IoU ratio is much lower: `0.2613 / 0.6284 = 0.4158`.

**Options for the frozen rule:**
1. **Benchmark against ES rather than an absolute constant** — e.g. *"the gap generalises if every
   signal's ratio lies within ±0.10 of ES's committed 0.5463, and every signal's ρ(1−Sα) is lower
   than its ρ(MAE) with non-overlapping bootstrap CIs."* Self-calibrating, and it cannot be gamed by
   the constant's choice.
2. **Raise the constant to 0.6** so ES clears it, and say plainly the constant was set from ES's
   committed value before any new signal was computed.
3. **Drop the ratio as the criterion** and pre-register the ordering instead: `ρ(MAE) > ρ(1−Sα) >
   ρ(1−IoU)` for every signal — which is exactly the threshold B1 already froze and passed
   (`b1_allocation_signal.py:360,369`).

**STATUS: NEEDS YOUR CALL — highest-priority item in this audit.** Recommendation: **option 1 plus
option 3** — pre-register the *ordering* as the primary criterion (it is B1's own, already tested and
passed, and is robust to the ±0.03 seed noise of §1.3), with the ES-benchmarked ratio band as the
quantitative secondary. Do not freeze a bare `< 0.5`.

---

## §7 Boundary-restricted extension — cost and value

**DECISION. Cheap, and recommended IN.** The boundary-restricted variant costs **no additional
forward passes** — it is a different reduction over per-pixel fields already produced. The only new
cost is the mask morphology (an `erode`/`dilate` per image, negligible against a network forward) and
storing/streaming per-pixel maps rather than scalars.

**What it would add — the surgical finding.** ES is already 0.9-weighted on an edge term (§3.1) yet
tracks pixel error; if boundary-restricted entropy *also* fails to predict 1−Sα, the claim strengthens
from "these signals are misdirected" to "**uncertainty in COD carries no localisation information even
where localisation lives**". That is the sharpest available version of the result.

**Caveat.** Recomputing ES boundary-restricted means **re-deriving ES**, not reusing the committed
scalar: `ESLoss.forward` returns an already-reduced scalar (`Src/utils/tool.py:77`), so a
boundary-restricted ES needs the unreduced per-pixel fields — i.e. reimplementing ES's two terms with
`reduction='none'`. That is new code touching the definition of the committed signal, and the
reimplementation **must be asserted to reproduce the committed per-image ES** (whole-image reduction,
against `b1_target_es_SINet-S2C.csv`, 4040 rows) before any boundary variant is believed.

**STATUS: NEEDS YOUR CALL** on whether boundary-ES is in. Recommendation: **entropy and ensemble
boundary variants IN** (free, no definitional risk); **boundary-ES IN only with the
reproduce-the-committed-scalar assertion as a hard gate** — otherwise it silently redefines the
signal B1 committed. All must be pre-registered.

---

## §8 Integrity reuse

**DECISION.** T2-C inherits the same discipline, with **one important exception**.

| requirement | status | evidence |
|---|---|---|
| One scorer, validated against B1 before any new number | inherit | `abc_evaluate.py:43,131-140` |
| No `/tmp/archive`, `/tmp/claude-`, `_archive_stageC_old`, `evidence/artifacts`, `/scratchpad` | inherit | `e0_regenerate.py:539-542`, `step_independence()` `:559-626` |
| Results under a new output dir only | `rebuild/T2C/out/` | see below |
| One log block `EXP T2C` | inherit | `common.log_block` |
| Committed clustering untouched | §1 | read-only consumption via `c1_space.load_space` |
| Never read `test_es` as a signal | **EXCEPTION — see below** | `c1_preflight.py:64-66` |

**THE EXCEPTION, which would otherwise fail the build.** C1/ABC's `gate_signal` AST-bans the string
literal `test_es` (`c1_preflight.py:65`, `BANNED_SIGNAL = 'test_es'`; enforced
`abc_preflight.py:76`). That ban is correct for **allocation** experiments — allocating by
endpoint-measured ES would be leakage. T2-C is a **B1-class correlation study**: it must read endpoint
error, and §4.1's side-by-side table legitimately reports the endpoint-side ES variant. **If T2-C
adopts C1/ABC's `gate_signal` unmodified it will FAIL by construction.** B1 itself reads these
quantities and is the correct precedent.

**STATUS: SETTLED, with the exception flagged.** T2-C must declare explicitly that it is a correlation
study, that the allocation-signal ban does not apply, and that no T2-C output is ever used to allocate.

**Output dir — small open choice.** T2 used `rebuild/ABC/out/t2/` because it reused ABC's scripts.
T2-C reuses **B1's** code, so `rebuild/T2C/out/` (a new experiment dir, via `C.exp_dir('T2C','out')`,
`common.py:37-39`) is the cleaner home. **STATUS: NEEDS YOUR CALL** (trivial).
Recommendation: `rebuild/T2C/out/`.

**New code required — the minimum.** (a) per-pixel binary entropy + aggregation; (b) ensemble
variance + aggregation; (c) the boundary band; (d) optionally an unreduced ES (§7). Everything else is
reuse: `load_space`/assignment, `spearman_perm`, `load_scores`, `load_target`, the floors, the D2
exclusion read. **Nothing requires a trainer.**

---

## §9 Current state and run accounting

### §9.1 Dependencies

| artifact | status |
|---|---|
| `b1_cluster_assignment_dinoL518.json`, `b1_centroids_dinoL518_k75_seed0.npy` | **COMMITTED** |
| `b1_cluster_es_dinoL518.csv` (75 rows, target_es + test error all 75/75) | **COMMITTED** |
| `b1_target_es_{SINet-S2C,SINet-v2-S2C}.csv` (4040 rows each) | **COMMITTED** |
| `b1_scores_{SINet-S2C,SINet-v2-S2C}_test.csv` | **COMMITTED** |
| `b1_faithful_correlation.json` | **COMMITTED** |
| `d2_leaked_names.json` (7 exclusions) | **COMMITTED** |
| `rebuild/E0/cache/dinoL518_{tgt,test}_cls.npy` + `dinoL518_names.json` | **ON DISK** (untracked cache) |
| `Snapshot/{SINet,SINet-v2}/S2C/{Tea_epoch_best,Stu_40/Stu_100}.pth` | **ON DISK** (untracked, `*.pth` gitignored) |
| `Snapshot/ABC/{SINet,SINetv2}_A0_s{42,43,45}/Tea_epoch_best.pth` | **ON DISK** (6/6 verified) |
| `Dataset/Target/Image` (4040), `Dataset/Test/COD10K/Imgs` (2026) | **ON DISK** |
| NC4K embeddings, NC4K per-cluster error, NC4K in `SPLITS` | **MISSING** (§5.2) |
| entropy / ensemble / boundary implementations | **MISSING — to be written** (§8) |
| `PREREGISTRATION_T2C.md` | **MISSING — must precede any correlation** (§6) |

**Unverified dependency to flag:** the `.pth` checkpoints and the E0 `.npy` caches are **untracked**
and gitignored. They exist on this machine; they are **not** recoverable from the repository. T2-C's
reproducibility therefore rests on local files, exactly as B1's and ABC's did. This is inherited, not
introduced, but it should be stated.

### §9.2 Compute — inference only, no training

Forward passes needed on the 4040-image target set (4033 after exclusion — but the exclusion is
applied at embedding-load time, so scoring all 4040 and filtering afterwards is simpler and is what B1
did: its per-image CSVs have 4040 rows):

| signal | passes per architecture | × 2 architectures |
|---|---|---|
| predictive entropy (1 checkpoint) | 4040 × 1 | 8,080 |
| ensemble disagreement (3 checkpoints) | 4040 × 3 | 24,240 |
| *(optional)* unreduced ES (student + teacher) | 4040 × 2 | 16,160 |
| **total without boundary-ES** | | **32,320 forwards** |

All boundary/foreground variants reuse the same forward passes — aggregation only, **zero additional
inference**.

**Wall-clock: ESTIMATE, NOT MEASURED.** No committed B1 block records a wall time for target-ES
scoring, so this is derived from ABC's inference throughput (2026 + 4121 images per endpoint pass,
2 GPUs, ~22 inference jobs in well under an hour). At an order of ~500–1500 img/min for a single
352×352 forward, 32,320 forwards ≈ **25–65 min of GPU time**, parallelisable across the 2 GPUs, plus
correlation time that is seconds. **Marked as an estimate** — the only way to bound it properly is a
timed single-checkpoint pass, which is out of scope for this audit.

**No training. No checkpoint is written. No pool is built.**

---

## §10 Decisions ranked by damage if gotten wrong

1. **§4.1 — target-side signal vs endpoint-side signal.** The committed numbers differ enormously
   (ρ(MAE) +0.6284 cross-side vs +0.8754 same-side) and the two ES variants agree only at ρ=0.5732.
   Computing the new signals on the endpoint answers an easier question and is **not comparable to
   B1's headline**. Mechanically easy to get wrong: it is one argument to `load_scores`/`cluster_*`.
2. **§3.2 — entropy aggregation.** Whole-image mean is dominated by background in a COD image; a
   whole-image null could be an artifact of background swamping the signal rather than evidence about
   structure. Computing only whole-image would make a null uninterpretable.
3. **§6.2 — the ratio threshold.** As drafted (`< 0.5`) it fails on ES itself (0.5463), so the frozen
   rule would contradict its own motivating case.
4. **§2.3 — ensemble arm choice.** A0's members span 0.0334 Sα (arm sd 0.017266, ~10× every other
   arm). Disagreement then partly measures *which member is weak*, and a weak member errs most on
   large-error images — biasing toward the hypothesis.
5. **§2.2 — teacher vs student for entropy.** Lower risk than the above but must be fixed in advance
   and matched to ES's provenance.
6. **§5.2 — NC4K.** Cannot be done as scoped; pretending otherwise would produce a secondary endpoint
   with a silently different partition.
7. **§1.3 — no error bars at one seed.** B1's own 10-seed sd was ±0.0297; ρ differences below ~0.06
   are not distinguishable. A comparison of signals without this yardstick could call noise a finding.
8. **§7 — boundary-ES reimplementation.** Redefines a committed signal unless gated on reproducing
   the committed per-image scalar.

---

## §11 The single ambiguity most likely to invalidate the comparison

**Which side the new signals are computed on (§4.1).**

Every other item on this list degrades the result. This one silently replaces the question. B1's
committed structure is *target-side signal → endpoint-side error*, joined through a partition fitted on
the target and never touched by the endpoint (`b1_allocation_signal.py:150-156`,
`b1_es_error_correlation.py:461-467`). Compute entropy or ensemble disagreement on COD10K instead —
the natural thing to do, since that is where the GT and the error already are — and the numbers will
look *better* and *more significant*, because same-side ES gives ρ(MAE) = +0.8754 against cross-side
+0.6284. Nothing would fail, no gate would fire, and the resulting table would sit next to B1's
+0.6284 as though the two were comparable when the two ES variants themselves agree only at ρ=0.5732.

It is a one-line mistake that produces a publishable-looking, entirely non-comparable result. It
should be an explicit asserted invariant in T2-C's pre-flight — *the signal array is indexed by target
names, the error array by endpoint names, and the two are joined only through the committed cluster
map* — not a convention anyone is trusted to remember.

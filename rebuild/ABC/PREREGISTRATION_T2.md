# PREREGISTRATION_T2.md — the T2 falsification arms' decision rule

> **Committed before the first T2 training run. Never edited after any T2 number exists.**
>
> **ADDITIVE.** `rebuild/ABC/PREREGISTRATION.md` is frozen and is **not altered, superseded or
> reinterpreted** by this document. No A/B/C arm, gate, verdict or artifact is restated, recomputed
> or replaced. T2 adds two arms, one gap set and one output namespace; it inherits everything else
> unchanged and **asserts that inheritance mechanically** rather than re-implementing it.
>
> If any part of §T2.1 is changed after a single T2 Sα has been computed, T2 is void and must be
> re-run. A/B/C is unaffected either way.
>
> Dated **2026-09-10**. Written after A/B/C's results were committed and read; written **before** any
> T2 pool was built, any T2 permutation was drawn, and any T2 number existed.

## §T2.1 The rule — verbatim, as approved

```
Dated extension  : 2026-09-10. Additive to rebuild/ABC/PREREGISTRATION.md (frozen, unaltered).

Claim under test : C1 measured, in embedding-distance space, that the ES signal contributes
                   negligibly beyond concentration (+0.0073 of d ~ 1.1 against its own shuffle,
                   13/20; targeting the highest-ES cluster is WORSE than an arbitrary cluster in
                   16/20 cells). T2 tests whether that holds on TRAINED ACCURACY.
Hypothesis       : real-C ~ shuffled-C ~ inverted-C, all within 2*sigma_hat on the primary endpoint.

New arms         : CSHUF = C10 with the committed target_es vector PERMUTED ACROSS CLUSTERS by a
                           declared random permutation (Spearman rho vs the real signal ~ 0).
                   CINV  = C10 with the committed target_es vector permuted by the RANK-REVERSING
                           map, so budget flows to the LOWEST-deficiency clusters (rho = -1 exactly).
                   Both transforms are PERMUTATIONS: the allocation SHAPE is preserved exactly and
                   only which cluster receives which budget changes.
                   Identical to C10 in every other respect: alpha = 1.0, k = 75, B = 1000, dinoL518,
                   R2 grey-128 centroid ranking, desc_nc serving order, greedy distinct selection,
                   LAKE-RED render pool, same base pool (HKU-IS 4447), same target set.
Reference arms   : C10 and B, exactly as already committed. NOT re-trained and NOT re-inferred.
                   Their committed predictions are RE-SCORED by the same scorer in the same process
                   to build the noise pool, and must reproduce rebuild/ABC/out/abc_metrics.csv to
                   < 1e-9 or T2 halts.

Primary endpoint : COD10K-test, S-alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K, S-alpha (reported, never decides).
Also reported    : MAE, F-beta-w, E-phi on both endpoints.
Seeds            : {42, 43, 45}. Both new arms are DETERMINISTIC and identical across the three
                   seeds -- only the training seed varies. (Contrast: arm B redraws per seed.)

Noise estimate   : sigma_hat = pooled within-arm sd of S-alpha over arms {B, C10, CSHUF, CINV},
                   per architecture, per endpoint, df = 4 x 2 = 8. Per-arm sd reported beside it.
Gaps             : Delta_1 = mean(Sa_C10)   - mean(Sa_CSHUF)   [does the REAL signal beat no signal]
                   Delta_2 = mean(Sa_C10)   - mean(Sa_CINV)    [does it beat the REVERSED signal]
                   Delta_3 = mean(Sa_CSHUF) - mean(Sa_CINV)    [is direction ordered at all]
                   Each on COD10K (primary) and NC4K (secondary, reported, never decides).

Rule (identical to A/B/C, unchanged):
  REAL EFFECT     iff Delta > 2*sigma_hat AND sign consistent 3/3 seeds
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3  -> report as-is, do NOT add seeds

Interpretation, fixed before any T2 number exists:
  ALL THREE WITHIN NOISE
      -> the target-side ES signal carries NO accuracy-relevant information beyond concentration,
         IN ANY DIRECTION. Supports section 6(v) on trained accuracy, not only on geometry.
  Delta_1 or Delta_2 > 2*sigma_hat with 3/3 sign consistency
      -> the signal DOES contribute. 6(v) is falsified as stated and must be SOFTENED accordingly.
  Delta_1 or Delta_2 < -2*sigma_hat with 3/3 (anti-targeting BEATS targeting)
      -> reported as a REAL REGRESSION of the real signal; 6(v) restates as "not merely
         uninformative but misleading."
  Whichever occurs is reported. No arm is dropped, no seed is added, no gap is redefined after
  the fact, and no result is reclassified once seen.

Report           : 2*sigma_hat rule primary; paired per-seed differences as a table; sign-consistency
                   count; NO p-value at n=3.
```

## §T2.2 Mechanical specification — operational definitions only; alters nothing in §T2.1

### T2.2 Inheritance, asserted rather than re-implemented

Every property that made A/B/C trustworthy is inherited **identically**. T2 does not re-derive any of
them; it re-runs the same assertion code over the new pools.

| Inherited | Where it is asserted (unchanged code) |
|---|---|
| Base pool `Dataset/Source/HKU-IS` (4447 image+GT pairs) | `abc_build_pools.py:56-62`, byte-checked against E0's manifest in `abc_preflight.py:262-274` |
| Target set `Dataset/Target/` (4040) | `abc_train.py` §A.8.3 `target_loaded_4040` check |
| Seeds {42, 43, 45} | `abc_common.py:43` |
| Six patches, incl. **P0 `--source_root`** and **P2 cudnn determinism** | `abc_preflight.py:144-150` (grep-marks), `:318-329` (G6) |
| Per-RUNID directory scheme, collision-proof incl. the CLS round-2 pool | `abc_common.py:66-92` |
| Six pre-flight gates | `abc_preflight.py:332-357` |
| Endpoints COD10K (primary) / NC4K (secondary); CHAMELEON withdrawn; CAMO selection-only | `abc_preflight.py:180-202` (G4) |
| Scorer validated against B1's committed Sα = 0.717216 / MAE = 0.074463 at < 1e-5 **before** any new number | `abc_evaluate.py:131-140` |
| Metric source `Eval/metrics.py`, 6 dp, headline Eφ = `meanEm` | `abc_evaluate.py:45`, `:52-78` |
| Checkpoint `Snapshot/ABC/{RUNID}/Tea_epoch_best.pth`, final round | `abc_evaluate.py:92` |

T2 adds **no new script**. It adds one allocation branch beside C10's and one output namespace. The
trainer and the evaluation path are literally the same files, so gate **G3 (one trainer, one eval)**
*proves* identity rather than asserting it.

### T2.3 Arm construction, exact

Both arms compute `es_used = es[sigma]` and then run C10's pipeline untouched.

- **CINV — rank-reversing map.** `asc = argsort(es, kind='stable')`, then `sigma[asc] = asc[::-1]`.
  The cluster holding the r-th largest ES is served the allocation the (k+1−r)-th largest would have
  received, so budget flows to the **lowest-deficiency** clusters — the ones where the model is most
  confident. Spearman ρ(es[σ], es) = **−1** exactly. **No RNG.**

  **Disclosed:** at odd k the rank-reversing map has exactly **one fixed point** — the median-ranked
  cluster is its own mirror (`asc[37] -> asc[75-1-37] = asc[37]`). This is mathematically necessary,
  not a defect, and it is why the zero-fixed-point requirement below is scoped to CSHUF alone. That
  one cluster retains its own allocation of roughly the median size, ≈1% of the B = 1000 budget; the
  other 74 clusters are all reassigned. Reported as `perm_fixed_points = 1` in block #1.
- **CSHUF — declared random permutation.** The **first** offset in `0..63` for which
  `numpy.random.default_rng(910_000 + offset).permutation(75)` satisfies **both**: zero fixed points,
  and `|Spearman(es[sigma], es)| <= 0.10`.

  The acceptance rule is declared **here, before the draw**, so the permutation is selected by a rule
  and never by inspection of what it does downstream. The accepted `perm_seed`, `perm_rho` and
  `perm_fixed_points` are reported in `EXP T2` block #1. Exhausting all 64 draws is a **HALT**, not a
  reason to relax the bound.

A **single fixed permutation per arm**, applied identically across all three training seeds.

**Why a permutation and not a value transform.** The originally-specified construction — negate the
ES vector, or reflect it as `ES_max − ES_c` — was examined and rejected on two grounds established
before any arm was built:

1. **The two are the same operation here.** `softmax_alloc` (`c1_targeted_vs_random.py:75-81`)
   max-subtracts, and `np.std` is invariant under both maps:
   `−es − max(−es) = min(es) − es` and `(max−es) − max(max−es) = min(es) − es`.
   Identical to float ULP. The choice between them is a non-choice and controls nothing.
2. **Neither preserves concentration.** `target_es` spans 0.018391–0.070668 over 75 clusters and is
   not symmetric, so `exp(+z)` and `exp(−z)` have different entropies. A value-inverted arm would
   vary direction **and** concentration, confounding exactly what §T2.4 exists to hold fixed.

A permutation preserves the multiset `{p_c}` and therefore the shape **exactly**, giving a clean
three-point axis at fixed concentration: ρ = **+1** (C10), **≈0** (CSHUF), **−1** (CINV).

### T2.4 The same-shape assertion — the crux for both new arms

For each arm `X ∈ {CSHUF, CINV}`, the measured allocation cell must equal C10's committed cell on the
four **shape** keys, at **exact equality of the 5-decimal-rounded values** as emitted by
`abc_common.py:124-130` — i.e. tolerance **|Δ| < 5e-6** on the unrounded quantity:

```
clusters_funded    == 75        (exact integer)
max_alloc_share    == 0.194     (round(alloc.max() / B, 5))
alloc_entropy_norm == 0.78644   (round(-sum p log p / log k, 5))
tv_from_uniform    == 0.49253   (round(0.5 * sum |p - 1/k|, 5))
```

Source of the reference values: the committed C1 cell `(dinoL518, B=1000, R2_cut, alpha=1.0)` in
`rebuild/C1/out/c1_cells.csv`, mirrored at `abc_common.py:58-63`.

`n_displaced` is **excluded** from the assertion and reported only (C10 = 370) — see T2.6.

**This is not a loose "within rounding" allowance.** Entropy, TV-from-uniform and max are symmetric
functions of the multiset `{p_c}`, and a permutation leaves that multiset unchanged, so the equality
is exact whenever the transform really is a permutation. **A failure therefore means the transform
was not a permutation — a code defect — and is a HALT, never a reason to widen the tolerance.**

One documented way it could legitimately trip: `largest_remainder`
(`c1_targeted_vs_random.py:84-94`) breaks ties by ascending cluster index, so two clusters with
*exactly* equal fractional parts could exchange one unit of budget under a permutation and move
`max_alloc_share` by 0.001. With 75 distinct float64 ES values this does not occur; if it ever did,
the gate FAILS, T2 halts, and the event is reported rather than absorbed.

C10 itself continues to be asserted against **all five** keys, `n_displaced` included, exactly as
A/B/C does today. The T2 arms relax nothing about C10.

### T2.5 Determinism and seed-independence

Neither new arm takes a seed argument: `arm_c_stems` is a pure function of `(alpha, es_perm)`, and
`es_permutation` is a pure function of `(es, kind)`. Both arms therefore select an identical
foreground set at all three training seeds, and **only the training seed varies** — exactly C10's
property, and deliberately unlike arm B, which redraws per seed by design
(`abc_common.py:103-109`, `ABC_PLAN.md` §A.4).

Asserted, not assumed: G5 requires `image_digest` and `gt_digest` equality across all three seeds
**and** both architectures for each T2 arm, the same cross-seed identity check A/B/C already applies
to C10 (`abc_build_pools.py:139-150`).

### T2.6 Displacement accounting

`n_displaced` counts how often a cluster's next-ranked candidate was already claimed
(`c1_targeted_vs_random.py:153-177`). C10's committed value is **370**. A different cluster→budget
assignment walks the same per-cluster rankings in a different order and therefore displaces a
different number of times.

It is **reported per arm, never asserted.** It is disclosed in `EXP T2` block #1 beside the overlap
table because it is a mechanical driver of set overlap: a high displacement count means the arms
converge on the same images for a mechanical reason rather than a substantive one, and the reader is
entitled to see it before reading any verdict.

### T2.7 Overlap disclosure and the distinctness gate

Reported for **every pair** among {CSHUF, CINV, C10, B_s42, B_s43, B_s45}: `overlap`,
`overlap / chance` where chance = 1000² / 4447 = **224.9**, `Jaccard`, and
`n_differing = 1000 − |∩|`.

- **B×C pairs** keep A/B/C's committed chance band **0.7 ≤ ratio ≤ 1.3**. C1 and A/B/C found these at
  chance (226/246/230 vs 224.9; Jaccard 0.1274/0.1403/0.1299). The new arms' overlaps are
  **measured and reported, never assumed**.
- **C×C pairs are gated at Jaccard ≤ 0.50.** Above it, T2 **halts before training** and reports the
  number.

**Why this gate exists.** C10 and CSHUF both fund all 75 clusters, so their selected sets can overlap
far above chance even though the allocation is permuted. Under this pre-registration *equality is the
supporting outcome*, so a design that mechanically forces equality — two arms sharing most of their
images — would manufacture support for the hypothesis rather than test it. That is a pro-null bias,
and it is the one failure mode this document treats as disqualifying rather than merely disclosable.
The measurement costs **zero GPU-hours** and precedes every run.

`n_differing` — the effective contrast — is reported alongside every T2 verdict, so a WITHIN NOISE
result that squeaks under the gate is still read with its true resolving power in view.

### T2.8 Signal provenance

Both arms read `target_es` from the committed `rebuild/B1/out/b1_cluster_es_dinoL518.csv` (75 rows,
target-measured, GT-free) via `c1_space.load_space()` — the only sanctioned accessor. Never
`test_es`, which `gate_signal` bans by AST scan of every `rebuild/ABC/*.py`
(`c1_preflight.py:64`, `abc_preflight.py:79-99`). Never a direct `np.load` of `rebuild/E0/cache/*.npy`
(`ABC_PLAN.md:238-240`).

The permutation is applied to that vector and to nothing else, so **the only difference between C10,
CSHUF and CINV is the transformation of an identical source vector.**

**Provenance of that vector, established before any T2 run:**

```
file        rebuild/B1/out/b1_cluster_es_dinoL518.csv
sha256      1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8
git blob    3fb4c46677a647e9a396e31cbc2b8f81b016ddd8
            IDENTICAL at HEAD and at 065dac6, the A/B/C block-#1 commit
history     one commit only: 470e224 (EXP B1), which created it
```

**Disclosure.** No hash of this file was recorded when C10 was built — it appears in no manifest and
in no preflight JSON, and E0's manifest covers only primary image/mask inputs. The blob-OID identity
above is therefore the evidence of record, and it is exact: the file has never been modified since
B1 created it. The A/B/C block-#1 commit was logged `065dac6 (dirty)`, so a blob comparison alone
would be necessary rather than sufficient; C10's continued **full-cell** reproduction (all five keys)
closes the remainder, since any perturbation large enough to matter would move the allocation. The
T2 build re-asserts both the sha256 and the blob identity.

### T2.9 Gates

All six A/B/C pre-flight gates must PASS on the T2 pools **before any training**, with no
`--skip-gate`:

| Gate | Requirement |
|---|---|
| G1 signal | allocate by the target-side signal, never the endpoint one; consume B1's committed partition; never fit one |
| G2 provenance | `E0.step_independence()` **called**, not re-implemented; no `/tmp/claude-`, `_archive_stageC_old`, `evidence/artifacts` or `/scratchpad` reference in any script under `rebuild/`, the new code included; primary inputs still match E0's manifest |
| G3 one trainer | exactly one `MyTrain.py` and one `MyTest.py` in the tree, all six patches present |
| G4 endpoints | CHAMELEON withdrawn, CAMO selection-only |
| G5 pools | per-arm integrity, **including the positional-pairing invariant** (below), plus §T2.4 and §T2.7 |
| G6 determinism | `MyTrain.py` declares `cudnn.deterministic = True`, `cudnn.benchmark = False`, `set_random_seed(opt.seed)` |

**The positional-pairing invariant, asserted per new pool.** The **real** `Src.utils.Dataloader.SrcDataset`
— the trainer's own loader, not a reimplementation — must satisfy
`stem(basename(ds.images[i])) == stem(basename(ds.gts[i]))` for **every** index `i`, at
`len(ds) == 5447`, with zero mismatches (`abc_preflight.py:226-231`). Sampling is not sufficient and
is not used. The round-2 worst case is proved on the full union of the pool with all 4040 target
names as `.png` in both directories, `n = 9487` (`abc_preflight.py:240-246`).

### T2.10 No substitution, no optional stopping

Seeds are not added to break an INCONCLUSIVE. σ̂ is computed on T2's own pool {B, C10, CSHUF, CINV}
and is **not** swapped for A/B/C's committed σ̂ if T2's comes out larger — the bar is `2σ̂`, not a
fixed number. The primary endpoint is not swapped for NC4K. No metric is substituted for Sα.

### T2.11 Power, stated before results

A/B/C's committed COD10K σ̂ puts the bar at ≈ **0.0179** (SINet, σ̂ = 0.008966) and ≈ **0.0123**
(SINet-v2, σ̂ = 0.006129). T2's own σ̂ is the bar of record.

Stated plainly: **T2 resolves a signal contribution comparable to the paper's whole MT→Ours gap
(0.0142) and not one of C1's measured magnitude.** C1's +0.0073 of a Cohen's `d` is a statement about
embedding geometry and maps to no accuracy prediction at all.

**A WITHIN NOISE result is therefore consistent with a small real effect and must be reported as
"no effect resolvable at this sensitivity," never as "no effect."** This sentence is committed before
any T2 number exists precisely so it cannot be softened after one.

### T2.12 Additivity, mechanically enforced

T2 writes to `rebuild/ABC/out/t2/` and appends `EXP T2` blocks to `results/REBUILD_LOG.txt`. It
overwrites **no** committed A/B/C artifact. The A/B/C gap set remains the code default; T2's is
opt-in via `--gaps t2`. C10 and B are re-scored, never re-trained, and must reproduce
`rebuild/ABC/out/abc_metrics.csv` to < 1e-9 or T2 halts.

Re-running the A/B/C pre-flight under the T2 diff must produce the same pass/fail decision and a
byte-identical C10 stem list. That regression check is part of the T2 build, not an afterthought.

### T2.13 No p-value

No p-value, no bootstrap, no multiple-comparison correction, at n = 3. Three gaps are reported
per architecture per endpoint, each against the same `2σ̂` bar, with paired per-seed differences and
a sign-consistency count.

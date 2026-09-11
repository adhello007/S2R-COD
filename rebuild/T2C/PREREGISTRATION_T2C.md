# PREREGISTRATION_T2C.md — the T2-C uncertainty-signal comparison decision rule

> **Committed before the first T2-C signal was computed. Never edited after any T2-C number exists.**
>
> **ADDITIVE.** `rebuild/ABC/PREREGISTRATION.md`, `rebuild/ABC/PREREGISTRATION_T2.md`, the B1 blocks
> and the C1 record are **frozen and are not altered, superseded or reinterpreted** by this document.
> No A/B/C or T2 arm, gate, verdict or artifact is restated, recomputed or replaced. T2-C adds two
> signals, one aggregation axis, one output namespace (`rebuild/T2C/out/`) and one log tag
> (`EXP T2C`); it inherits everything else unchanged and **asserts that inheritance mechanically**
> rather than re-implementing it.
>
> If any part of §T2C.1 is changed after a single T2-C ρ has been computed, T2-C is void and must be
> re-run. B1, C1, A/B/C and T2 are unaffected either way.
>
> Dated **2026-09-11**. Written after B1's, C1's, A/B/C's and T2's results were committed and read;
> written **before** any T2-C signal was computed, any T2-C forward pass was run, and any T2-C number
> existed.

## §T2C.1 The rule — verbatim, as approved

```
Dated extension  : 2026-09-11. Additive to the frozen B1 / C1 / A-B-C / T2 record, unaltered.

Claim under test : B1 measured, target-side through the committed dinoL518 k=75 seed=0 partition,
                   rho(MAE) = +0.6284 vs rho(1-Sa) = +0.3433 vs rho(1-IoU) = +0.2613 for the ES
                   allocation signal. T2-C tests whether that pixel-over-structure ORDERING is
                   specific to ES or general to uncertainty signals for COD.
Hypothesis       : every signal shows rho(MAE) > rho(1-Sa) > rho(1-IoU).

Signals          : ES       -- re-derived unreduced, a=0.9 b=0.3 use_weighted_bce=False,
                              Snapshot/<arch>/S2C {Stu_40|Stu_100, Tea_epoch_best}.
                   ENTROPY  -- H(p) = -(p log2 p + (1-p) log2 (1-p)), p = clip(sigmoid(logit),
                              1e-6, 1-1e-6), from Tea_epoch_best.pth of Snapshot/<arch>/S2C.
                   ENSEMBLE -- per-pixel population variance (ddof=0) of sigmoid across the three
                              Tea_epoch_best.pth of A0 s{42,43,45}  [PRIMARY]
                              and of CSHUF s{42,43,45}              [SENSITIVITY].
                   All at 352x352 + ImageNet norm, on the RAW sigmoid, never min-max renormalised.

Aggregations     : WHOLE    -- mean over all 352x352 pixels.
                   BOUNDARY -- mean over band = dilate(M,ones(3,3),2) & ~erode(M,ones(3,3),2),
                              M = sigmoid(logit_teacher) >= 0.5, width 2*iters = 4 px.
                              ONE band per image, from the S2C teacher, SHARED by all three signals.
                   Both aggregations computed for all three signals. Empty band -> the image
                   contributes no boundary value; >5% empty is a HALT.

Structure        : signal on the UNLABELED TARGET set (4040 scored, 4033 joined after D2's 7
                   measured leaked names); true error on the LABELED COD10K-test endpoint (2026,
                   B1's committed per-image CSV); joined ONLY through the committed target-fitted
                   partition. Floors: >=15 endpoint images AND >=5 target images per cluster.
                   Computing any signal on the endpoint is a HALT, not a variant.

Endpoint         : COD10K-test, SOLE endpoint. NC4K dropped (no DINOv2 cache, not a B1 split, no
                   per-cluster error columns). CHAMELEON excluded (D2 contamination). CAMO
                   selection-only, and degenerate at k=75.

Statistic        : Spearman rho per cluster, via B1.spearman_perm -- reused, not reimplemented.
                   n_perm=2000 at seed 0 (the committed call), 200 for seeds 1-9. Permutation p and
                   bootstrap CI reported at seed 0.
Seeds            : k-means seeds 0..9. Seed 0 = the COMMITTED partition, read not refit, and the
                   headline. Seeds 1-9 = in-memory refits, for the standard deviation only.

DECISION RULE (primary, frozen):
  For each signal x aggregation row, PASS iff  rho(MAE) > rho(1-Sa) > rho(1-IoU)  at seed 0.
  This is B1's OWN committed criterion (b1_allocation_signal.py:360), already tested and passed by
  ES. It is NOT a new threshold.

  REPORTED, SECONDARY, DESCRIPTIVE ONLY:
    ratio = rho(1-Sa) / rho(MAE), benchmarked against ES's committed 0.5463 -- NEVER against 0.5.

  Why not 0.5. ES's own target-side ratio is 0.5463 > 0.5, so a frozen "< 0.5" rule would classify
  the reference signal as NOT exhibiting the gap it was named for, and would score a new signal
  landing at 0.52 inconsistently with ES. B1 itself froze a threshold stating that "on the REAL
  allocation signal the 0.5 wrong-objective boundary is still not stateable" (:376-381), and
  recorded VERDICT_binary_is_k_stable = False (REBUILD_LOG.txt:809; the ratio is 0.5463 at k=75
  and 0.5825 at k=20). The 0.5 figure traces to VERDICT_rho_1mSa_over_rho_MAE = 0.4999, which is
  the ENDPOINT-side 10-seed-mean ratio -- a different quantity from the target-side 0.5463, and on
  the other side of the boundary. The ordering criterion is used instead because it is B1's own,
  is robust to seed noise, and cannot be gamed by the choice of a constant.

RESOLUTION LIMIT (frozen): rho differences below ~0.06 between signals are NOT distinguishable.
  Committed support at k=75 over 10 seeds: rho(MAE) +-0.0264, rho(1-Sa) +-0.0461,
  rho(1-IoU) +-0.0564 (REBUILD_LOG.txt:794-796), so two independent rho(1-Sa) values differ with
  sd ~ 0.065. Propagated, sd(ratio) ~ 0.077.
  The claim is about THE PATTERN -- all signals show pixel > structure -- and NEVER about fine rho
  differences between signals. Sub-0.06 gaps are not interpreted, in either direction.

ENSEMBLE SENSITIVITY CONDITION (frozen): A0's members are unequal -- Sa spread 0.0334 (SINet) and
  0.0211 (SINetv2); per-arm sd 0.017266 / 0.010575 against 0.001655 / 0.003523 for CSHUF. Part of
  A0's disagreement therefore measures WHICH MEMBER IS WEAK rather than which image is hard, and a
  weak model errs most on large-error images -- biasing TOWARD the hypothesis.
  Every A0 ensemble finding MUST be checked against the tight CSHUF ensemble. A finding that holds
  only in A0 is reported as A POSSIBLE WEAK-MEMBER ARTIFACT, NOT A RESULT.
  Also fixed in advance: 3 members is a small ensemble (a 3-sample variance has ~70% relative
  standard error), the members are NOT the model whose error is the endpoint column, and only the
  training seed differs -- so this is optimisation-stochasticity disagreement, not epistemic
  uncertainty. A NULL FROM THE ENSEMBLE IS WEAKER EVIDENCE THAN A NULL FROM ENTROPY.

BOUNDARY INTERPRETATION, fixed before any number exists:
  whole-image predicts NEITHER pixel nor structure
      -> background drowns the signal. The whole-image null is UNINFORMATIVE about structure and
         must not be reported as evidence about it.
  boundary predicts pixel but NOT structure
      -> STRONGEST GENERAL CLAIM: uncertainty in COD carries no localisation information even
         where localisation lives.
  boundary predicts STRUCTURE
      -> CONSTRUCTIVE FINDING: uncertainty is informative only at the boundary, and standard
         whole-image aggregation discards it. Reported as a positive result, not suppressed.
  Whichever occurs is reported. No signal is dropped, no aggregation is added, no row is
  reclassified once seen, and no seed is added to break a tie.

SCOPE, stated before any number exists:
  T2-C is CORRELATIONAL. It establishes a STRONG PRIOR that uncertainty-guided allocation fails for
  COD. It is NOT proof that every signal fails in training. T2 tested ES's DIRECTION on trained
  accuracy and found WITHIN NOISE; a correlation cannot be upgraded into a causal claim. One
  endpoint, two new signals, two architectures. This sentence is committed now precisely so it
  cannot be softened after a result.
```

## §T2C.2 Mechanical specification — operational definitions only; alters nothing in §T2C.1

### T2C.2.1 Inheritance, asserted rather than re-implemented

| Inherited | Where it is asserted (unchanged code) |
|---|---|
| Partition `dinoL518 k=75 seed=0`, read never refit | `b1_cluster_assignment_dinoL518.json`; cross-checked via `c1_space.load_space` |
| Target 4040 → 4033, D2's **measured** leaked names read from its artifact | `B1.load_target` (`b1_es_error_correlation.py:329-338`) |
| Both floors, verbatim | copied from `b1_allocation_signal.py:170-171` |
| 352×352 + ImageNet norm | `B1.TESTSIZE`; transform from `b1_allocation_signal.py:94-95` |
| Head per architecture | `B1._head` (`:183-195`) |
| Checkpoint tensor-copy assertion | `B1._load_ckpt` (`:198-212`) |
| ρ + permutation p + bootstrap CI | `B1.spearman_perm` (`:470-491`) |
| ES config parsed from live source | `B1.parse_es_config` (`:99-124`) |
| Scorer Sα 0.717216 / MAE 0.074463 at < 1e-5 **before** any new number | `abc_evaluate.py:43`, `:154-163` |
| Provenance scan | `E0.step_independence()`, called not re-implemented |

### T2C.2.2 The target-side invariant — the single most important one

Four assertions, all HALT (`RuntimeError('T2C HALT: ...')`) before any ρ:

```
A. PATH        every image path opened by the signal loader starts with Dataset/Target/ ;
               no path contains Dataset/Test/ or Dataset/Val/ .
               Dataset/Target/ has NO GT subdirectory -- only Image/ -- so a target-side signal
               is ground-truth-free by filesystem construction.
B. KEY SPACE   set(signal) >= set(a['target_names'])         # 4033 names, all ending .jpg
               set(signal) & set(endpoint_stems) == empty     # disjoint key spaces
C. COUNT       len(signal) == 4040 before the join; 4033 after restriction to target_names.
D. CARDINALITY at seed 0: clusters_used == 50 and n_target_in_used == 3428.
```

**Why an assertion and not a convention.** Same-side ES gives ρ(MAE) = **+0.8754** against
cross-side **+0.6284**, and the two agree only at ρ = **0.5732** — they are not interchangeable. The
same-side computation is the *natural* mistake, because the GT and the error are already on the
endpoint. It is one argument to a loader; nothing would crash and no existing gate would fire, and
the resulting table would sit next to B1's +0.6284 as though comparable. Assertion **D** is the
backstop: `n_target_in_used == 3428` counts *target* images and cannot arise from an endpoint-side
signal. `B1.step_correlate` computes the same-side quantity and is banned by AST scan.

### T2C.2.3 The T2-C signal gate — a declared, scoped departure

C1/ABC's `gate_signal` AST-bans the literal endpoint-ES column name (`c1_preflight.py:65`; enforced
`abc_preflight.py:77-101`). That ban is correct for **allocation** experiments, where allocating by
an endpoint-measured quantity would be leakage. T2-C is a **B1-class correlation study**: it must
read endpoint error. **Adopted unmodified, that gate would fail the build by construction.** B1
itself reads these quantities and is the precedent.

T2-C's gate therefore **asserts** target-side computation (T2C.2.2), **permits** reading endpoint
error through `B1.load_scores(arch, 'test')`, and **bans** `B1.step_correlate`, `sklearn.cluster`
imports and direct `KMeans(` construction. `E0.step_independence()` is reused **unchanged**.

Because `_c1_sources()` and `_abc_sources()` are directory-local globs that see nothing under
`rebuild/T2C/`, T2-C binds its own `_scan` over `rebuild/T2C/*.py`, mirroring `abc_preflight._scan`
and reusing `PF.docstring_ids` and `PF.PRAGMA` — no second pragma is invented.

**Declared:** T2-C is a correlation study; the allocation-signal ban does not apply; **no T2-C output
is ever used to allocate.**

### T2C.2.4 Reproduction gates, and why each tolerance is satisfiable

| gate | comparison | tolerance | why |
|---|---|---|---|
| unreduced-ES identity | `es_map.mean()` vs `ESLoss.forward`, same tensors, same process | `< 1e-6` | pure arithmetic; only float reduction order differs |
| ES per image | vs committed `b1_target_es_<arch>.csv` (4040 rows) | `max < 1e-5`, `mean < 1e-6` | B1's scoring set no cudnn determinism flags, so a fresh forward can differ by more than reduction noise |
| ES per cluster | vs committed `b1_cluster_es_dinoL518.csv` `target_es` (6 dp) | `<= 5e-6` | 6-dp storage admits 5e-7 from rounding alone; 5e-6 is satisfiable **and** meaningful |
| **harness** | `t2c_correlation(...,0, committed_ES)` vs `b1_faithful_correlation.json['dinoL518']` | **bit-identical** | consumes the *committed CSV*, not a forward — same functions, same RNG seed, so exact equality is achievable |

**T2's Addendum A1 is the reason this table exists.** T2 froze a `< 1e-9` comparison against a
6-dp-stored reference, which no correct computation can satisfy, and the first full run halted at it.
**No T2-C gate compares a full-precision float against a rounded reference at a tolerance finer than
the rounding.** The harness gate is the strongest and costs zero GPU; it proves T2-C's harness *is*
B1's harness before any new signal enters.

### T2C.2.5 Multi-seed clustering — new code, and why

`cluster_target_es` returns `None` unless `(k, seed)` matches the committed assignment file
(`b1_allocation_signal.py:141-142`), so the multi-seed standard deviation **cannot** be obtained by
looping B1's function — and the failure is a silent `None`, not an error. T2-C therefore supplies its
own target-label source:

- **seed 0** — labels read from `b1_cluster_assignment_dinoL518.json`, identical to
  `cluster_target_es`;
- **seeds 1–9** — labels from `B1.fit_kmeans(X, 75, seed).labels_`, where `_KM_CACHE` is an
  **in-memory dict** (`b1_es_error_correlation.py:425`). **Nothing is written; the committed
  partition is never rewritten and no new partition artifact is created.**

Gated: at seed 0 the refit must reproduce `a['target_labels']` **exactly**; on failure the ARI is
reported and the run halts.

### T2C.2.6 Boundary band, exact

```
M    = sigmoid(logit_teacher) >= 0.5        # RAW sigmoid, 352x352, S2C Tea_epoch_best
dil  = cv2.dilate(M.astype(uint8), np.ones((3,3), np.uint8), iterations=2)
ero  = cv2.erode (M.astype(uint8), np.ones((3,3), np.uint8), iterations=2)
band = (dil - ero) > 0                      # width 2*iters = 4 px across a straight edge
```

One band per image, from the S2C teacher, **shared by all three signals** — so "boundary-restricted"
names the *same region* in every row. Rationale: the endpoint error column is that teacher's error.
A per-signal band would make each row's boundary a different region and confound the comparison
invisibly; it is reported for the ensemble as a robustness variant only.

Repo precedent `d2r_reaudit.py:565-566` uses the same 3×3 square at `iterations=1` but an
**inner-only** band; T2-C's symmetric band is a declared **extension**, because entropy is highest
straddling the contour. `iters=1` (2 px) is a free robustness variant.

Empty band → the image contributes no boundary value; the ≥5-target floor applies to the
**band-eligible** count; `n_boundary_empty` is reported; **> 5% empty is a HALT**.

**Raw sigmoid, not min-max.** B1's *error* path min-max renormalises the prediction
(`b1_es_error_correlation.py:256`); its *ES* path does not. Entropy is a calibration quantity and
min-max renormalisation would destroy it. All T2-C signals and the band threshold read the raw
sigmoid.

### T2C.2.7 Comparability, declared

ES has **no per-pixel form** in the committed code: it is a ¾-edge-weighted student–teacher
disagreement, a weighted sum of two whole-image means over two different per-pixel fields, one of
which has no single-model analogue. **Comparability is declared at the level of same images, same
clusters, same resolution, same floors, same statistic — explicitly NOT same functional form.**
Stated here rather than implied by putting the rows in one table.

### T2C.2.8 Disclosures, made before any number exists

1. **A0 member heterogeneity** — §T2C.1, reported beside every ensemble ρ.
2. **A0 model mismatch** — the ensemble members are not the model whose error is the endpoint column
   (S2C teacher Sα 0.717216; no A0 member matches).
3. **`SINet_A0_s42` has an empty `returncode`** in `abc_runs.csv` where every other row has `0`. The
   run completed (`wall_min` and both pool sizes recorded); a logging gap, disclosed.
4. **All eight `.pth` sha256 recorded**; the six A0 hashes are pinned in `T2C_PLAN.md` §7. All
   distinct, and `abc_runs.csv` shows distinct wall times, round-2 pool sizes (6313/6179/6243) and
   best epochs (32/28/27) — independent runs.
5. **ES zero-padding border artifact** — `padding=1` gives the outer 1-px ring a spurious Sobel
   response. **Not masked**, because the committed scalar includes it and masking would break the
   reproduction gate.
6. **SINet upsamples with `align_corners=True`; SINet-v2 without.** Per-pixel maps sit on slightly
   different grids. T2-C never compares per-pixel maps across architectures, so this affects no
   reported quantity; disclosed for completeness.
7. **`.pth` and E0 `.npy` caches are untracked and gitignored** — reproducibility rests on local
   files, inherited from B1 and A/B/C.
8. **CSHUF is in `rebuild/ABC/out/t2/abc_metrics.csv`, not `out/`.** B and C10 overlap both with
   byte-identical Sα, so the tranches are comparable.

### T2C.2.9 No substitution, no optional stopping

Seeds are not added to break a tie. The ordering criterion is not swapped for the ratio if the
ordering comes out inconvenient, and the ratio's benchmark is not moved off ES's committed 0.5463.
COD10K is not swapped for another endpoint. No signal is dropped after being computed, and no
aggregation is added after seeing a null. Every row specified in `T2C_PLAN.md` §8 is reported,
whatever it says.

### T2C.2.10 Additivity, mechanically enforced

T2-C writes only under `rebuild/T2C/out/` and appends `EXP T2C` blocks with `trains='NO'`. It
overwrites no committed artifact. `b1_allocation_signal.main()` and
`b1_es_error_correlation.main()` are **never called** — both unconditionally rewrite committed
artifacts (`:216`, `:349`, `:415`, `:429`; `:867`). Leaf functions only. `augment_cluster_csv` is
never called. No T2-C file contains a `/tmp/…`, `/scratchpad`, `evidence/artifacts` or
`_archive_stageC_old` literal, since `E0.step_independence()` walks all of `rebuild/` and such a
literal would fail C1 gate 6 and ABC G2 for every other experiment.

# PREREGISTRATION_OR.md — the oracle-targeting arm's decision rule

> **Committed before the first OR training run. Never edited after any OR number exists.**
>
> **ADDITIVE.** `rebuild/ABC/PREREGISTRATION.md` and `rebuild/ABC/PREREGISTRATION_T2.md` are frozen
> and are **not altered, superseded or reinterpreted** by this document. No A/B/C or T2 arm, gate,
> verdict or artifact is restated, recomputed or replaced. OR adds **one arm**, one gap set and one
> output namespace; it inherits everything else unchanged and **asserts that inheritance
> mechanically** rather than re-implementing it.
>
> If any part of §OR.1 is changed after a single OR Sα has been computed, OR is void and must be
> re-run. A/B/C and T2 are unaffected either way.
>
> Dated **2026-09-18**, at commit `b755aa9`. Written **before** any OR pool was built, any oracle
> vector was loaded into an allocation, and any OR number existed.

---

## §OR.0 The declaration that must be read first

**This arm deliberately uses ground-truth labels from the primary endpoint to choose training data.
It is a cheat, on purpose.**

Gate **G1** (`abc_preflight.py:76`) exists to guarantee that every *method* arm allocates by the
target-side, label-free signal and never by the endpoint-measured one. C_ORACLE allocates by the
endpoint-measured one. That is not a gate failure to be worked around; it is the entire content of
the arm, and it is declared here so that no reader can mistake what it is.

Three consequences, committed now:

1. **C_ORACLE is never reported as a method result, a configuration, or a recommendation.** It is a
   diagnostic upper bound and is labelled as one wherever it appears. Any sentence of the form
   "our method achieves …" that draws on C_ORACLE is a reporting error.
2. **C_ORACLE cannot be run by anyone without endpoint labels.** It is not reproducible as a
   deployable policy and is not proposed as one.
3. **G1 is run anyway and its result recorded**, rather than skipped. The arm is constructed so that
   the banned token never appears (it reads the column `test_one_minus_sa`, not `test_es`), so G1
   will PASS on syntax while the arm violates its intent. **That discrepancy is disclosed here and
   in `EXP OR` block #1 as `oracle_uses_endpoint_labels = true`.** Passing G1 is not offered as
   evidence that this arm is clean.

## §OR.1 The rule — verbatim, as approved

```
Dated extension  : 2026-09-18. Additive to rebuild/ABC/PREREGISTRATION.md and
                   rebuild/ABC/PREREGISTRATION_T2.md (both frozen, unaltered).

Question under   : A/B/C measured that targeting by the ES signal does not beat random allocation at
test               a resolvable level, and T2 measured that destroying or reversing the signal's
                   DIRECTION changes nothing on trained accuracy. Both leave one cause unseparated:
                   the failure may sit in the ACQUISITION SCORE (ES is a poor proxy for where the
                   model is actually wrong) or DOWNSTREAM (the generator cannot act on any score,
                   however good). OR separates them by replacing the score with a PERFECT one.

Hypothesis       : If the acquisition score is the binding constraint, C_ORACLE beats B and C10 by
                   more than 2*sigma_hat. If the constraint is downstream, C_ORACLE is WITHIN NOISE
                   of both, and no acquisition score of any quality can help in this pipeline.

New arm          : CORACLE = C10's committed allocation SHAPE, re-assigned across clusters by the
                   RANK OF TRUE ENDPOINT ERROR. Construction, exactly:

                     oracle_c := per-cluster mean (1 - S_alpha) on COD10K-test, read from the
                                 committed rebuild/B1/out/b1_cluster_es_dinoL518.csv column
                                 `test_one_minus_sa` (75 rows, one per cluster).
                     asc_es   := argsort(target_es, stable)        # ES ranks, ascending
                     asc_or   := argsort(oracle_c,  stable)        # true-error ranks, ascending
                     sigma[asc_or[i]] := asc_es[i]   for i in 0..74
                     es_used  := target_es[sigma]

                   so the cluster with the r-th LARGEST true endpoint error receives exactly the
                   budget the cluster with the r-th LARGEST ES received under C10. This is a
                   PERMUTATION, so the allocation shape is preserved EXACTLY and only the
                   cluster->budget assignment changes -- the same device T2 uses, with the ranking
                   supplied by ground truth instead of by a permutation.

                   Identical to C10 in every other respect: alpha = 1.0, k = 75, B = 1000, dinoL518,
                   R2 grey-128 centroid ranking, desc_nc serving order, greedy distinct selection,
                   LAKE-RED render pool, same base pool (HKU-IS 4447), same target set (4040).

Reference arms   : C10 and B, exactly as already committed. NOT re-trained and NOT re-inferred.
                   Their committed predictions are RE-SCORED by the same scorer in the same process
                   and must reproduce rebuild/ABC/out/abc_metrics.csv at 6 dp exactly, or OR halts.
                   (The '< 1e-9' form of this clause is a known defect; see PREREGISTRATION_T2.md
                   Addendum A1. The strictest satisfiable form -- exact equality at the recorded
                   precision -- is what is required here, declared before the fact rather than
                   after it.)

Primary endpoint : COD10K-test, S-alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K, S-alpha (reported, never decides).
Also reported    : MAE, F-beta-w, E-phi on both endpoints.
Seeds            : {42, 43, 45}. CORACLE is DETERMINISTIC across seeds -- only the training seed
                   varies, exactly as C10, CSHUF and CINV are.

Noise estimate   : sigma_hat = pooled within-arm sd of S-alpha over arms {B, C10, CORACLE}, per
                   architecture, per endpoint, df = 3 x 2 = 6. Per-arm sd reported beside it.
                   T2's sigma_hat is ALSO reported for comparison and does NOT replace OR's own.
Gaps             : Delta_1 = mean(Sa_CORACLE) - mean(Sa_B)    [does a PERFECT score beat random]
                   Delta_2 = mean(Sa_CORACLE) - mean(Sa_C10)  [does a perfect score beat the real one]
                   Each on COD10K (primary) and NC4K (secondary, reported, never decides).

Rule (identical to A/B/C and T2, unchanged):
  REAL EFFECT     iff Delta > 2*sigma_hat AND sign consistent 3/3 seeds
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3  -> report as-is, do NOT add seeds

Interpretation, fixed before any OR number exists:
  BOTH WITHIN NOISE
      -> the acquisition score is NOT the binding constraint in this pipeline. Even a score with
         perfect knowledge of endpoint error buys nothing resolvable, so the constraint is
         downstream -- the generator, the exhausted foreground pool, or the pinned step budget.
         This STRENGTHENS the scoping in the paper's setup-specific limitations section and
         WEAKENS any reading of the null as "uncertainty estimation is the problem."
  Delta_1 > 2*sigma_hat with 3/3 sign consistency
      -> a perfect score DOES help. The acquisition score is then a binding constraint, the null
         is attributable in part to ES being a poor proxy, and the paper must say so. This is the
         outcome that most damages the paper's current framing, and it is reported if it occurs.
  Delta_1 < -2*sigma_hat with 3/3
      -> reported as a REAL REGRESSION: allocating to the truly-worst clusters is actively harmful
         in this pipeline. Reported, not explained away.
  Whichever occurs is reported. No arm is dropped, no seed is added, no gap is redefined after the
  fact, and no result is reclassified once seen.

Report           : 2*sigma_hat rule primary; paired per-seed differences as a table; sign-consistency
                   count; NO p-value at n=3.
```

## §OR.2 Mechanical specification — operational definitions only; alters nothing in §OR.1

### OR.2.1 Inheritance, asserted rather than re-implemented

Every property that made A/B/C and T2 trustworthy is inherited **identically**, by re-running the
same assertion code over the new pool. OR adds **no new trainer and no new scorer**: it adds one
`ARM_ES_PERM` branch beside CSHUF's and one output namespace `rebuild/ABC/out/or/`.

| Inherited | Where it is asserted (unchanged code) |
|---|---|
| Base pool `Dataset/Source/HKU-IS` (4447 pairs) | `abc_build_pools.py:56-62`; byte-checked against E0's manifest in `abc_preflight.py` |
| Target set `Dataset/Target/` (4040) | `abc_train.py` `target_loaded_4040` check |
| Six pre-flight gates G1–G6, none skipped | `abc_preflight.py` |
| Endpoints COD10K primary / NC4K secondary; CHAMELEON withdrawn; CAMO selection-only | `abc_preflight.py` G4 |
| Scorer validated against B1's committed Sα = 0.717216 / MAE = 0.074463 before any new number | `abc_evaluate.py` |
| Checkpoint `Snapshot/ABC/{RUNID}/Tea_epoch_best.pth`, final round | `abc_evaluate.py` |
| Positional-pairing invariant on the real `SrcDataset`, zero mismatches at n=5447 and n=9487 | `abc_preflight.py` |

### OR.2.2 The same-shape assertion — identical to T2.4

The measured allocation cell must equal C10's committed cell on the four **shape** keys, at exact
equality of the 5-decimal-rounded values:

```
clusters_funded    == 75
max_alloc_share    == 0.194
alloc_entropy_norm == 0.78644
tv_from_uniform    == 0.49253
```

A permutation leaves the multiset `{p_c}` unchanged, so this equality is exact whenever the
transform really is a permutation. **A failure means the transform was not a permutation — a code
defect — and is a HALT, never a reason to widen the tolerance.** `n_displaced` is reported, never
asserted (T2.6).

Because the shape is held exactly fixed, C_ORACLE is directly comparable to C10, CSHUF and CINV on
the existing same-shape axis. It extends that axis with a fourth point: ρ against the **true error**
ranking is **+1** by construction, where C10's is whatever ES achieves.

### OR.2.3 The oracle vector's provenance

`rebuild/B1/out/b1_cluster_es_dinoL518.csv`, column `test_one_minus_sa`, 75 rows.

- **sha256 and git blob OID are recorded in `EXP OR` block #1** and must match the values recorded
  in `PREREGISTRATION_T2.md` §T2.8 for the same file — the file has one commit in its history
  (`470e224`, EXP B1) and has never been modified since.
- The column is the **mean of `1 - S_alpha` over the COD10K-test images assigned to each cluster**
  by the committed dinoL518 partition, from the committed S2C model. It is read, never recomputed.
- **Disclosed, before any run:** `n_test` per cluster ranges **1 to 94** (sum 2026). A cluster whose
  mean is taken over a single test image carries an extremely noisy oracle value. This makes the
  oracle *imperfect in the tail*, which biases the arm **towards** the null, and is reported beside
  the verdict rather than discovered afterwards. The oracle is "perfect information about the
  endpoint, estimated on the endpoint's own finite sample", not "perfect information about the
  population".
- No other column of that file is read. `test_es` — the banned token — is **not** read, and the
  substitution is on the error column alone.

### OR.2.4 Overlap disclosure and the distinctness gate

Reported for every pair among {CORACLE, C10, CSHUF, CINV, B_s42, B_s43, B_s45}: `overlap`,
`overlap / chance` where chance = 1000² / 4447 = **224.9**, `Jaccard`, and `n_differing`.

**C×C pairs are gated at Jaccard ≤ 0.50**, identical to T2.7. Above it, OR **halts before training**
and reports the number. The reasoning is T2.7's, unchanged: under a rule where equality is a
supporting outcome, two arms that mechanically share most of their images would manufacture support.

`n_differing` — the effective contrast — is reported alongside every OR verdict.

### OR.2.5 Determinism and seed-independence

`arm_c_stems` is a pure function of `(alpha, es_perm)` and the oracle permutation is a pure function
of `(target_es, oracle_c)`. No RNG. CORACLE therefore selects an identical foreground set at all
three training seeds, and only the training seed varies — C10's property exactly. Asserted by G5's
cross-seed `image_digest` / `gt_digest` equality, unchanged.

### OR.2.6 No substitution, no optional stopping

Seeds are not added to break an INCONCLUSIVE. σ̂ is computed on OR's own pool {B, C10, CORACLE} and
is **not** swapped for T2's or A/B/C's if OR's comes out larger. The primary endpoint is not swapped
for NC4K. No metric is substituted for Sα.

### OR.2.7 Power, stated before results

T2's committed σ̂ puts the bar near **0.0055** (SINet). OR's own σ̂, on its own three-arm pool at
df = 6, is the bar of record and is expected to be of that order. Stated plainly:

**A WITHIN NOISE result is consistent with a small real effect and must be reported as "no effect
resolvable at this sensitivity", never as "no effect."** This sentence is committed before any OR
number exists precisely so that it cannot be softened after one.

**And the asymmetry is the opposite of T2's.** In T2 equality was the *supporting* outcome, so a
tight bar was conservative. Here a *difference* is the outcome that would falsify the paper's
current framing, so **WITHIN NOISE is the pro-paper outcome and the bar must not be allowed to
flatter it.** OR therefore reports, beside every WITHIN NOISE verdict, the largest effect its bar
could have missed.

### OR.2.8 Additivity, mechanically enforced

OR writes to `rebuild/ABC/out/or/` and appends `EXP OR` blocks to `results/REBUILD_LOG.txt`. It
overwrites **no** committed A/B/C or T2 artifact. C10 and B are re-scored, never re-trained.
Re-running the A/B/C pre-flight under the OR diff must produce the same pass/fail decision and a
byte-identical C10 stem list; that regression check is part of the OR build, not an afterthought.

### OR.2.9 No p-value

No p-value, no bootstrap, no multiple-comparison correction, at n = 3. Two gaps are reported per
architecture per endpoint, each against the same `2σ̂` bar, with paired per-seed differences and a
sign-consistency count.

---

# Addendum A1 — 2026-09-19: the oracle vector is single-architecture, and §OR.2.3 did not say so

**§OR.0 and §OR.1 above are left EXACTLY as frozen. Nothing in either is edited, deleted or
reinterpreted, and no decision rule, gap, band, bar or interpretation clause changes.** This addendum
records a disclosure that §OR.2.3 should have carried and did not, so a reader can audit the gap
rather than discover it.

## Timing, stated plainly

**Written after OR's per-run metrics existed on disk** (`rebuild/ABC/out/or/abc_metrics.csv`,
written 2026-09-18T18:23) **and before any OR verdict, gap, σ̂ or architecture comparison had been
read by the author.** The order is recorded here because it is the only thing that makes this
addendum auditable, and it follows the precedent of `PREREGISTRATION_T2.md` Addendum A1, which was
written under the same constraint and states its timing the same way.

**The fact below was not discovered from any OR outcome.** It was found by reading committed *input*
artifacts — `rebuild/B1/out/b1_cluster_assignment_dinoL518.json` and the two committed per-image
score tables — all of which existed before OR was designed. It was therefore knowable before the
first OR run and could have been written into §OR.2.3. That it was not is this document's defect,
not a property of the result.

## The omission

§OR.2.3 records the oracle vector's file, column, sha256, value range and per-cluster `n_test`
spread. It does **not** record which model's errors the column contains.

It contains **SINet's**. `b1_cluster_assignment_dinoL518.json` declares
`arch_for_endpoint = "SINet/S2C"`, and `b1_es_error_correlation.py` writes every per-split column of
`b1_cluster_es_dinoL518.csv` — `target_es` and `test_one_minus_sa` alike — from that one
architecture's scores.

OR trains **both** architectures. So:

- **The SINet cells are a true oracle.** The vector is that architecture's own endpoint error.
- **The SINet-v2 cells are not.** They are ranked by *SINet's* error profile. "Perfect information"
  is the wrong phrase for those three runs, and §OR.1's interpretation clauses should be read on
  SINet-v2 as *near*-oracle rather than oracle.

## How near, measured

Computed from the two committed per-image score tables under the committed dinoL518 partition, all
75 clusters scored by both architectures:

```
rho( SINet per-cluster (1 - S_alpha) , SINet-v2 per-cluster (1 - S_alpha) )  = +0.9211
rho( ES signal                       , SINet-v2 per-cluster (1 - S_alpha) )  = +0.2623
rho( ES signal                       , SINet    per-cluster (1 - S_alpha) )  = +0.2372
```

So on SINet-v2 the substituted vector ranks true error at **ρ = +0.92** where the signal it replaces
manages **+0.26**. The intervention is a ~3.5× improvement in rank agreement rather than the perfect
one the SINet cells get. **The contrast remains the intended one; only the word "perfect" is wrong
for half the cells.**

## Why this does not bias the OR gaps

`target_es` — the vector **C10 itself allocates by** — comes from the same file, the same column
family and the same single architecture, and the committed campaign already applies it to both
architectures. **Both arms in Δ(CORACLE − C10) therefore carry identical architecture provenance,
so it cancels in the difference rather than favouring either arm.** The same holds for
Δ(CORACLE − B), where B allocates by nothing at all.

This is an inherited property of the campaign's original design, not something OR introduced. It is
nonetheless **undisclosed in the paper**: no sentence in the manuscript states that the allocation
signal is measured on one architecture and applied to two. B1's own results document lists the
cross-architecture axis among its limits, and the paper's third amendment records "one verification
gate not applicable in scope after it was found to compare two architectures' signals", so the
project knew; the main text does not tell the reader. **That is a paper-level disclosure owed
independently of OR**, and it is recorded here so it is not lost.

## What was NOT changed

The arms, the endpoints, the seeds, the σ̂ definition and its df = 6, the two gaps, the four verdict
bands, the 2σ̂ bar, every interpretation clause, the same-shape assertion, the distinctness gate, and
the no-optional-stopping and no-p-value rules are all untouched. Nothing here alters what OR
measures or how its verdict is decided. The only change is that a scope sentence which should have
sat in §OR.2.3 now exists, with its timing on the record.

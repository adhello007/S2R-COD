# ABC — Verified results

**Status: COMPLETE. Block #1: 6/6 gates, 15/15 thresholds PASS. Block #2: 5 of 6 thresholds PASS,
1 FAIL. Block #3: 3/3 thresholds PASS.**

**VERDICT ON THE CAMPAIGN'S CLAIM: `Δ(C − B)` is WITHIN NOISE on both architectures and both
endpoints.** A concentrated, more-proximal, lower-effective-rank training set does not beat a
dispersed one by the pre-registered rule. **But the campaign is underpowered against its own
pre-registered power statement** — the measured `2σ̂` on the primary endpoint is **0.017933**, larger
than the whole MT→Ours gap of 0.0142 this design was declared able to resolve half of. Both halves of
that sentence belong in any report of this result.

Source of every number below: `results/REBUILD_LOG.txt`, the three `EXP ABC` blocks —
**#1** `2026-09-04T23:36+05:30` (pre-flight), **#2** `2026-09-05T22:56+05:30` (run accounting),
**#3** `2026-09-06T13:37:26+05:30` (verdict), commit `065dac6`. Unlike E0–C1, where a later block
**superseded** an earlier one, these three are sequential **stages**; each is authoritative for its own
content and none supersedes another. Every figure quoted here appears verbatim in its block.

Setup: `rebuild/ABC/ABC_PLAN.md`. Rule: `rebuild/ABC/PREREGISTRATION.md`, committed before block #1 and
unchanged since. **Trains a model: YES** — the first experiment in the rebuild for which that is true.

---

## 1. What was measured

### 1.1 The pre-flight (block #1)

| Metric | Value |
|---|---|
| Gates passed | **6/6** (signal, provenance, one_trainer, endpoints, pools, determinism) |
| Arm pools assembled | **24** — 2 architectures × 4 arms × 3 seeds |
| Pool sizes | A0 **4447**; A2/B/C **5447** (base + B = 1000, identical across the three) |
| Counts / stem-sets / **real `SrcDataset` parity for every index** | **24/24**, **24/24**, **24/24**; total mismatches **0** |
| **Round-2 worst-case parity** (pool ∪ all 4040 target names as `.png` in both dirs) | **24/24** at n = **8487** |
| Base bytes vs `e0_manifest.sha256` | **0** mismatched, over all 24 pools |
| Render masks pixel-identical to `raw_gt` | **1000/1000** for C10, B_s42, B_s43, B_s45 |
| **Arm C reproduces C1's committed allocation cell** | `clusters_funded` **75**, `max_alloc_share` **0.194**, `alloc_entropy_norm` **0.78644**, `tv_from_uniform` **0.49253**, `n_displaced` **370** — all five exact |
| Overlap(B, C) against chance **224.9** | s42 **226** (ratio **1.005**), s43 **246** (**1.094**), s45 **230** (**1.023**) |
| Provenance | `forbidden_path_references` **0** over 15 scripts including 3 in `rebuild/ABC`; manifest spot-check **203/203** |
| Trainers in tree | **1** `MyTrain.py`, **1** `MyTest.py`, `patches_missing` **{}** |

### 1.2 The runs (block #2)

`training_runs_completed` **24/24**; `runs_abandoned` **0**; `runs_discarded_and_rerun` **0**.

Wall clock: SINet mean **106.9** min (range **104.5–108.3**), SINet-v2 mean **127.0** min (range
**121.2–129.7**).

Four thresholds PASS: exactly 2 CSRDA rounds in every run; `total_step` pinned at **253** (SINet) /
**127** (SINet-v2) in **both** rounds of every run; every run reached its final epoch and saved
`Tea_epoch_best.pth`; every run read the unfiltered 4040-image target set in both rounds.

**One threshold FAILS, and it stays failed.** `n_appended_mean_range` = mean **1945.8**, range
**1732–2163**, **spread 22.2% of mean**, against a declared 5% bound.
`n_appended_spread_exceeds_5pct` = **True**.

### 1.3 The verdict (block #3)

The eval path was validated before it produced any new number: `scorer_reproduces_B1` = Sα
**0.717216** (delta **3.77e-07**), MAE **0.074463** (delta **2.32e-07**) on the committed
`Result/SINet/S2C`. `runs_scored` **24**; `endpoint_shape_mismatches` **0**.

**COD10K-test, Sα — the primary endpoint:**

| | σ̂ (df = 8) | 2σ̂ | Δ(B − A2) | **Δ(C − B)** | Δ(A0 → B) | Δ(A0 → C10) |
|---|---|---|---|---|---|---|
| **SINet** | **0.008966** | **0.017933** | **+0.005768** 3/3 | **+0.005034** 3/3 | +0.012497 2/3 | +0.017530 3/3 |
| **SINet-v2** | **0.006129** | **0.012257** | **+0.002967** 3/3 | **−0.000399** 2/3 | +0.005923 2/3 | +0.005524 2/3 |

**Every one of those is WITHIN NOISE.** `architectures_agree_on_verdict` = `A0->A2 YES  A0->B YES
A0->C10 YES  A2->B YES  B->C10 YES`.

**NC4K, Sα — secondary, reported, never decides:** SINet σ̂ **0.004155**; Δ(B − A2) **+0.003694** 3/3
WITHIN NOISE, Δ(C − B) **+0.002110** 3/3 WITHIN NOISE. SINet-v2 σ̂ **0.005267**; Δ(B − A2)
**+0.000729**, Δ(C − B) **+0.000946**, both WITHIN NOISE.

Two NC4K figures must not be read as support, and §3.4 explains why: `DELTA_A0->B_SINet|NC4K` =
**+0.008782** 2/3 → **INCONCLUSIVE**, and `DELTA_A0->C10_SINet|NC4K` = **+0.010892** 3/3 →
**REAL EFFECT**.

### 1.4 Arm means and per-arm sds

| COD10K, Sα | A0 | A2 | B | C10 |
|---|---|---|---|---|
| SINet mean | **0.700950** | **0.707679** | **0.713447** | **0.718481** |
| SINet sd | **0.017266** | **0.001930** | **0.001807** | **0.004059** |
| SINet-v2 mean | **0.689145** | **0.692102** | **0.695069** | **0.694669** |
| SINet-v2 sd | **0.010575** | **0.003222** | **0.004863** | **0.002091** |

The arm ordering A0 < A2 < B ≈ C10 is monotone in all four architecture × endpoint cells, and every
step of it is inside noise.

---

## 2. Old claims re-tested

| # | Old claim | Old value | Measured | Verdict |
|---|---|---|---|---|
| C3.1 | σ(Sα), all runs n=6 | 0.00356 `[no code]` | **0.008966** (SINet/COD10K, pooled within-arm, df=8) | **SUPERSEDED — 2.5× larger** |
| C3.2 | σ(Sα), distinct seeds n=4 | 0.00286 `[no code]` | **0.008966** | **SUPERSEDED** |
| C3.4 | Predicted ΔSα | 0.000111 `[no code]` | Δ(C−B) **+0.005034** / **−0.000399** measured | **RE-MEASURED** — measured on SINet at roughly 45× the prediction, and still within noise |
| C3.5 | Shortfall vs 2σ | 64× `[no code]` | Δ(C−B) **+0.005034** against 2σ̂ **0.017933** on SINet | **RE-MEASURED** — a shortfall of about 3.6×, not 64× |
| C1.1 | Cohen's *d* targeted-vs-random ≈ 0.10 | `[no code]` | *d* was refuted by C1 at +1.00–1.23; the **trained** outcome of that separation is **within noise** | **CROSS-CHECKED against a trained outcome for the first time** |

The old package's arithmetic was wrong in both directions and by large factors — it under-estimated σ by
2.5× and over-estimated the shortfall by ~18×. Both errors happened to point at the same conclusion.
**Getting the right answer from the wrong numbers is not a reproduction.**

---

## 3. How the findings change our approach, thinking and assertions

### 3.1 The Stage C claim is not supported — and the honest reason is partly that we could not see it

- **Standing claim:** uncertainty-guided closed-loop Stage C generation improves COD accuracy.
- **Measured:** Δ(C − B) = **+0.005034** (SINet) and **−0.000399** (SINet-v2) on COD10K against
  2σ̂ of **0.017933** and **0.012257**. WITHIN NOISE on both, and the two architectures **disagree on
  the sign**.
- **Sharpened claim, both halves mandatory:** *(i)* there is no detectable accuracy benefit to
  allocating a 1000-image Stage C budget by concentration rather than at random, at this sample size;
  *(ii)* this design could not have detected a benefit the size of the paper's own headline
  improvement. `2σ̂ = 0.017933` exceeds the MT→Ours gap of 0.0142
  (`Eval/Eval/eval_txt/SINet/S2C_MT` 0.7030 → `.../S2C` 0.7172). `PREREGISTRATION.md` §2.9 declared
  this design able to resolve *half* that gap; it resolves about **1.3×** it.
- **Consequence:** the result is reportable as a null **with the power statement attached**. Reporting
  "no effect" without "and we could not have seen one this large" would be the old package's failure
  mode with better provenance.

### 3.2 My own limitation #4 was wrong in direction, and the log block's annotation is wrong with it

- **What I declared, before the runs:** `ABC_PLAN.md` §A.4 and §A.12 item 4 predicted **arm B** would
  inflate pooled σ̂, because its draw varies per seed and so it alone carries selection variance. The
  prediction was used to argue the bar would be conservative.
- **Measured:** arm B has among the **lowest** sds — **0.001807** (SINet/COD10K), **0.004863**
  (SINet-v2/COD10K). **Arm A0 is the largest in both architectures** (**0.017266** and **0.010575**),
  by roughly an order of magnitude over the tightest arm in each case.
- **This makes the provenance annotation on `per_arm_sd_*` in block #3 false.** It reads *"arm B
  carries selection variance A0 and C do not — pooled sigma_hat is inflated by it."* The **values** in
  that metric are correct; the **explanation attached to them is refuted by the values themselves.**
  Recorded here rather than quietly corrected, and logged as `REVISION_TABLE.md` R17. A block #4 would
  be needed to fix the annotation in the log itself; the values do not change.
- **Position:** per-seed draw variance in arm B is real but small enough to be invisible against
  run-to-run noise. What actually drives σ̂ is something the plan did not anticipate at all — §3.3.

### 3.3 The unpadded baseline is the unstable arm, in both architectures, and nobody predicted it

- **Measured, COD10K:** SINet A0 spans Sα **0.715086** / **0.681706** / **0.706058** — a range of
  0.033, and its sd of **0.017266** is ~9× arm B's **0.001807**. SINet-v2 A0 spans **0.688813** /
  **0.678740** / **0.699883**, sd **0.010575**, again the widest arm. On NC4K A0 is the widest arm in
  both architectures too (**0.006798**, **0.007782**).
- **So this is a reproducible property of the arm, not one unlucky run.** It reproduces across two
  architectures and both endpoints — four independent cells.
- **Why it matters:** A0 contributes 2 of the 8 degrees of freedom in the pooled σ̂ that every verdict
  is measured against. The arm the plan already called "not a clean control" for a *mechanistic*
  reason (22% more per-image exposure, `ABC_PLAN.md` §A.5.1) turns out to be the arm that sets the
  detection bar for the comparisons it is not even part of.
- **Sharpened position:** A2 is the right reference arm on **empirical** grounds as well as conceptual
  ones. A pre-registered amendment naming A2 the reference and pooling σ̂ over A2/B/C only would be
  defensible **before** seeing results; doing it now would be exactly the metric-substitution this
  rebuild exists to prevent, so **it is not done and no such σ̂ is reported here.**
- **Unexplained, and stated as unexplained:** no mechanism is offered for why the smaller,
  higher-exposure pool trains less stably. It is not the CLS append count (§3.4). It is a concrete
  follow-up, not a finding.

### 3.4 `n_appended` diverges by 22.2%, and the one arm-level pattern is not architecture-robust

- **Measured:** mean **1945.8**, range **1732–2163**, spread **22.2%** — the declared 5% threshold
  **FAILS**.
- **The structure matters more than the flag.** Per arm: SINet A0 **1798.0**, A2 **1792.7**,
  B **2008.0**, C10 **1932.3**; SINet-v2 A0 **1952.0**, A2 **2042.0**, B **2020.0**, C10 **2021.3**.
  On SINet the two render-carrying arms appended ~200 more pseudo-labels than the two without —
  consistent with round-1 models trained on LAKE-RED renders being more confident on target images, so
  CLS accepting more. **On SINet-v2 that pattern is absent** (all four arms within 4%).
- **And within-arm seed spread is itself large** — SINet C10 runs 1782 → 2163, 19.7%.
- **Position:** the flag fires mostly on seed noise. The one arm-level signal is **not**
  architecture-robust and is reported as an observation, not a mechanism. It is also **not** the
  explanation for §3.3: on SINet, A0 and A2 have nearly identical append counts — arithmetic on the
  logged triples above gives 1798.0 against 1792.7 — while their sds differ by an order of magnitude.
- **Why it is reported at all:** it is the one legitimate place the arms diverge beyond the Stage C
  injection, because CLS selects with the arm's own round-1 model (`CLS.py:139`). Absorbing it would
  hide a second-order difference from anyone reading the comparison.

### 3.5 NC4K produced a "REAL EFFECT" that is not usable, and the protocol is what stops it

- **Measured:** `DELTA_A0->C10_SINet|NC4K` = **+0.010892**, sign 3/3, against 2σ̂ = **0.008309** →
  the frozen rule returns **REAL EFFECT**.
- **Why it cannot be reported as one, on two independent grounds each sufficient:** NC4K is the
  **secondary** endpoint and `PREREGISTRATION.md` §1 says it is *"reported, never decides"*; and the
  comparison is against **A0**, which is confounded by 22% more per-image exposure and is the arm §3.3
  shows to be unstable. Every A2→B and B→C10 gap on NC4K is WITHIN NOISE on both architectures.
- **Position:** this is the pre-registration doing its job. Had the endpoint hierarchy and the A0
  caveat been decided after the numbers existed, this is precisely the figure that would have been
  promoted. It is recorded prominently **because** it is the tempting one.

### 3.6 What the campaign establishes about concentration, and what it says about the ES signal — nothing

- C1's audit measured the ES signal's own contribution at **+0.0073** of *d* against its own shuffle
  (13/20, a coin flip) and **−0.0649** against an arbitrary cluster (4/20). Arm C differs from arm B by
  **concentration**: effective-rank ratio 0.53–0.64, mean top-1 similarity to the target manifold up to
  +0.096, target-manifold coverage Δ ≈ 0.
- **So the measured null is about concentration.** It is **not** evidence for or against the
  uncertainty signal, and `ABC_PLAN.md` §A.12 item 7 forbids reporting it as such — in either
  direction.
- **What it does add to the verdict:** C1 §8.6 offered the hypothesis that a more-proximal,
  half-effective-rank, no-extra-coverage arm could be *compatible with zero accuracy gain*. That
  hypothesis is now **consistent with measurement** rather than merely available — at this power.

### 3.7 Two measurement defects found in ABC's own work

- **The `agg` values in `REBUILD_PLAN.md` §1 are not an assertable authority.** `common.py:248-263`
  claims `dir_digest` matches them; it does not (**d7f6de696d5c223e** measured against the pinned
  **b42e5f44b5f2b0db**). The pinned values were computed over a **full-relative-path** listing;
  `dir_digest` hashes the **bare filename**, and the path-prefixed variant reproduces both pinned
  values exactly. Never caught because no `.py` references them. **Primary data is unchanged** — all
  4447 + 4447 verify per-file against E0's manifest. ABC asserts against the manifest instead
  (`REVISION_TABLE.md` R16).
- **My first pool-provenance check used the regex `Loaded 4[0-9]*`**, which cannot match the
  5447-image pools, and reported 18 spurious mismatches. Corrected before any conclusion rested on it;
  the corrected check returns **24/24** runs reading their own pool in round 1 and their own
  `_iteration2` in round 2. Recorded because the first number was wrong and it was mine.

---

## 4. Consequences by downstream experiment

| Experiment | What ABC changes for it |
|---|---|
| **C3** | Largely superseded. σ was the input C3 could not measure; it is now **0.008966** from primary runs, and ΔSα is measured directly instead of predicted from a response rate. C3's 2-D (r, σ) surface is no longer the best available statement |
| **A3** | Unaffected and still required. ABC says nothing about whether LAKE-RED output is far from the real target distribution |
| **B3** | Its question — is steering feasible at all — is now **downstream of a null**. Arm C's selection provably concentrates (block #1 reproduces C1's cell), so infeasibility is not the explanation for §3.1 |
| **C2** | Its central claim is re-proved at scale: `total_step` pinned at 253/127 in **both** rounds of **all 24** runs, so added data bought zero extra optimisation |
| **Any α = 0.5 follow-up** | Lower value than it looked. α = 0.5 is a **more** concentrated arm, and concentration is what came back within noise |
| **Reporting** | The old σ of 0.00356 must not appear. It is 2.5× too small and was measured at `--iteration 1` |

---

## 5. What ABC does not establish

- **That Stage C does not work.** It establishes that no benefit is **detectable at this power**, and
  §3.1 quantifies the power: `2σ̂ = 0.017933` on the primary endpoint, larger than the reference gap of
  0.0142. A real effect smaller than that is entirely consistent with these data.
- **Anything about the ES uncertainty signal** (§3.6). The arms differ by concentration.
- **That more seeds would settle it.** Adding seeds to *this* campaign is foreclosed —
  `PREREGISTRATION.md` §1 and §2.7 forbid it, and topping up after seeing the answer is optional
  stopping. A separately pre-registered campaign is the legitimate route.
- **A mechanism for §3.3.** Why the unpadded arm trains least stably, in both architectures, is
  unexplained.
- **Anything at a second k, a second embedder, or α = 0.5.** k = 75 / `dinoL518` / α = 1.0 only.
  C1's k- and embedder-robustness is inherited, not re-established on trained outcomes.
- **Scope of the null, inherited from D1 §5:** this is evidence about targeting under an **exhausted
  foreground pool**. It is silent on whether new foregrounds would help — the DUTS/Oracle arm was
  deliberately out of this campaign and nothing here needed it.
- **Seed-level determinism.** cuDNN determinism was enabled and **reduces**, but is not claimed to
  eliminate, kernel nondeterminism. §3.3's spread is the observable consequence.
- **Anything on CHAMELEON** (withdrawn, D2) or **CAMO** (checkpoint-selection set only).

---

## 6. Log blocks

Three `EXP ABC` blocks, sequential stages rather than supersessions:

| Block | Result | Content |
|---|---|---|
| **#1** | 6/6 gates, **15 PASS / 0 FAIL** | Pre-flight of record: 24 arm pools assembled and asserted, arm-C reproduction of C1's cell, provenance, one-trainer, endpoint policy, determinism |
| **#2** | **5 PASS / 1 FAIL** | Run accounting for 24 runs. The FAIL is `n_appended` spread at 22.2% (§3.4) and it stays |
| **#3** | **3 PASS / 0 FAIL** | σ̂, the gaps, the frozen rule, the verdict |

`rebuild/ABC/PREREGISTRATION.md` was committed before block #1 and is byte-identical to its committed
version. Neither `abc_build_pools.py` nor `abc_evaluate.py` reads it as an input or writes it.

**One known defect in block #3 that is not corrected in the log:** the provenance annotation on the
four `per_arm_sd_*` metrics asserts that arm B inflates pooled σ̂. The measured values refute it
(§3.2). The values are correct; the annotation is wrong. Superseding it would require a block #4 that
changes no number.

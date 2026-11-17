# TH-02: what each contrast identifies, where labels flow, and how the statistics are read

**Status: VERIFIED** for the historical estimands and the identification analysis. EXP-01's verdicts
are produced by the same code once its runs exist (`EXP-01_comparisons.csv`).

Code: `rebuild/CAUS/caus_stats.py`. It has two independent implementations: (A) numpy/scipy, and (B)
csv/statistics/math with its own Student-t CDF and quantile. They agree to **2.6e-14** on every
quantity. Table: `RESULT_TABLES/TH-02_historical_recompute.csv`; definitions:
`RESULT_TABLES/TH-02_contrast_definitions.csv`.

## 1. Factors, and what each contrast varies

Factors: architecture *a*, generator support *g*, quota shape *h*, quota alignment (direction) *d*,
budget *N*, optimisation schedule *o*, training seed *s*, inter-round pseudo-label feedback *p*.

| Contrast | Varies | Held fixed | Mediating / uncontrolled |
|---|---|---|---|
| C10 − CSHUF, C10 − CINV | *d* only | *a, g, N, o, h* | *p* |
| C10 − B | *h* and *d* together | *a, g, N, o* | *p*; B's draw changes per seed |
| CORACLE − C10 | *d* (true-error rank vs ES rank) | *a, g, N, o, h* | *p* |
| EXP-01 P2: OR-TOP10 − OR-TOP10-SHUF | *d* only, at a new shape | *a, g, N, o, h* | *p* |
| EXP-01 P1/P3: OR-TOP10/OR-PROP − CORACLE | *h* only (both aimed by true error) | *a, g, N, o, d-source* | *p*; selection overlap 47% / 52% |
| EXP-01 P4: OR-TOP5 − CORACLE | *h* and the realised pattern of *d* | *a, g, N, o* | *p*; no same-shape control trained |

**Pseudo-label feedback *p*.** Round 2 appends target images that each arm's *own* round-1 model
labels confidently. It is therefore a mediator inside the loop, not a held constant. Across SE the
appended counts were 1,977 (B), 2,025 (C10), 1,990 (CSHUF) and 1,979 (CINV), per the manuscript.
EXP-01 records the count per run (`verify.json` → `n_appended`).

**What no design here identifies.**
- A globally optimal budget shape.
- The behaviour of an online or foreground-generating loop.
- Any *a* or *g* interaction: EXP-02, EXP-03 and EXP-04 are BLOCKED.

## 2. Label pathways (from `AN-05_role_ledger.csv`)

| Pathway | Where | Status |
|---|---|---|
| (i) Disjoint calibration: labels from images that are neither trained on nor scored | none available. The only endpoint-disjoint labelled set in the target clusters is the target pool's own masks, which are not in the pre-rebuttal workspace (AN-05 §3). | not used |
| (ii) Endpoint-label oracle: COD10K-test masks set quotas | CORACLE (historical); OR-PROP, OR-TOP10, OR-TOP5 (direction and shape); OR-TOP10-SHUF (shape only) | **leaky diagnostic**. COD10K-test is not an unbiased endpoint for these arms. NC4K is read by no allocation. |
| (iii) Test-label tuning of a claimed method | none | prohibited, not done |

**Standard arms never read endpoint labels.**
- *Allocation:* reads only `target_es` (gate G1, re-run in every EXP-01 pool gate through the committed
  `abc_preflight` functions).
- *Training:* reads the target pool without masks (`get_tarloader`), and the source pool's own masks.
- *Checkpoint selection:* reads CAMO-250 masks only (`--val_root ./Dataset/Val/CAMO/`).
- *Endpoint masks:* read only by `MyTest.py`/`Eval` after training.

AN-05 found two caveats. Both affect every arm alike:
- 15 COD10K-test and 32 NC4K photographs also sit, unlabelled, in the target pool.
- CAMO-250 shares 7 photographs with COD10K-test.

## 3. The frozen rule, re-derived, and every historical number checked

The rule: Δ > 2σ̂ **and** sign agreement across seeds. σ̂ is the pooled within-arm per-run standard
deviation over the campaign's pre-registered arms. **It is a per-run spread, not a standard error,**
so it does not shrink with more seeds. It is not replaced by 2·SE after the fact.

| Manuscript number | Recomputed (A = B) | Match |
|---|---|---|
| SE C10 − B, SINet·COD10K: +0.0024, bar 0.0069, 0.34×, 6/8 | +0.002352, 0.006862, 0.343, 6/8 | ✓ |
| Post-hoc interval [−0.0020, +0.0067] | Welch 95%: [−0.001954, +0.006659], df ≈ 10.4 | ✓ |
| OR CORACLE − B: +0.0008, bar 0.0061, 0.14×, 2/3 | +0.000844, 0.006130, 0.138, 2/3 | ✓ |
| ABC C10 − B: +0.0050, bar 0.0179 | +0.005034, 0.017933 | ✓ |
| T2 bar 0.0055; FX +0.0014, bar 0.0116 | 0.005533; +0.001440, 0.011650 | ✓ |
| Three-seed Welch interval [−0.0035, +0.0136] | [−0.003540, +0.013607] | ✓ |
| TOST ±0.005: C10 − CSHUF p = 0.019; C10 − B p = 0.101; 5 of 16 SE gaps equivalent | 0.0189; 0.1009; 5/16 (four direction contrasts + C10 − B on SINet·NC4K) | ✓ |
| "All eight OR gaps within noise, none directionally stable" | 8/8 WITHIN NOISE, every one 2/3 | ✓ |

**Reading the interval.** The eight-seed Welch interval excludes the +0.0142 reference effect. It
does not exclude positive effects up to +0.0067, and the ±0.005 equivalence criterion for C10 − B is
**not** met (p = 0.101). The supported statement is "no effect larger than about +0.007 at this
sensitivity". It is not "no effect".

## 4. Paired-by-seed analysis (supplementary, post-review, exploratory)

The SE seeds align across arms (42, 43, 45–50 for every arm), so per-seed differences D_s are
defined.

| Contrast (SINet·COD10K, n = 8) | paired mean | paired 95% t-CI | Var(paired) / Var(unpaired) |
|---|---|---|---|
| C10 − B | +0.0024 | [−0.0023, +0.0070] | 1.03 |
| C10 − CSHUF | +0.0003 | [−0.0050, +0.0056] | 1.27 |
| CSHUF − CINV | −0.0024 | [−0.0044, −0.0004] | 0.34 |

Pairing by seed buys nothing for the decisive contrast (ratio ≈ 1). That is expected: training is not
bit-reproducible on this hardware (EXP-01 pilot), and B redraws its images per seed. The one paired
interval that excludes zero (CSHUF − CINV, favouring the *reversed* arm) is one of 16 post-hoc
intervals, so it is reported, not interpreted. It points the same way as the manuscript's
observation that CINV has the highest mean in 4/4 cells.

For EXP-01 at n = 3 the paired t-interval has df = 2 and is flagged unstable wherever reported.

## 5. Interaction contrasts (planned, not estimable)

- **Generator interaction:** [(C10 − CSHUF)_new generator − (C10 − CSHUF)_LAKE-RED].
- **Architecture interaction:** [(C10 − CSHUF)_modern − (C10 − CSHUF)_SINet].

Each would use a standard error built from the two cells' seed variances. Neither is estimable:
EXP-02 and EXP-03 are BLOCKED (`EXPERIMENTAL_EVIDENCE.md`). No raw cross-backbone score comparison is
made anywhere.

## 6. Inferential outcome vocabulary for EXP-01

Each primary contrast receives exactly one of:
- **positive at adequate precision:** REAL EFFECT under the frozen rule, and NC4K of the same sign;
- **evidence against improvement at a named scale:** WITHIN NOISE, reported with the largest effect
  the bar could have missed;
- **unresolved:** INCONCLUSIVE, or WITHIN NOISE with an interval wide enough to include the reference
  effect;
- **infeasible:** a run is missing.

Threats recorded alongside:
- the leaky oracle source;
- selection overlap with CORACLE (P1 47%, P3 52%);
- arm-specific pseudo-label counts;
- run-to-run GPU nondeterminism;
- mask quality, which is shared across arms (AN-03).

# EQ: confirmatory equivalence campaign for the primary contrast (pre-registration)

**Status.** This file is committed before the first EQ run, together with its analysis script
`analysis/eq_analysis.py`. It is never edited after any EQ number exists; any amendment is
appended, with its date, below the line at the end. It is part of the response to Reviewer RL5B,
CW-01 / QA-01 (task EXP-01 of `RL5B_AGENT_EXECUTION_INSTRUCTIONS.md`).

**Inputs fixed before writing.**
- `RESULT_TABLES/TH01_power.csv`: power analysis.
- `prereg/EQ_design_numbers.json`: the design numbers quoted below, generated from TH01_power.csv.
- The committed SE campaign: `rebuild/SE/PREREGISTRATION_SE.md`, `rebuild/ABC/out/se/`.

## EQ.0 Question

At eight seeds per arm, the primary contrast (SINet, COD10K-test, S_α) is
Δ(C10 − B) = +0.0024 with a Welch 95% CI of [−0.0020, +0.0067]. It neither detects an advantage nor
establishes equivalence at ±0.005 (TOST p = 0.101). EQ asks the same question again, with fresh seeds
and a sample size fixed in advance, so that the answer is confirmatory.

## EQ.1 Hypotheses (verbatim)

- **H1 (primary).** |μ_C10 − μ_B| < 0.005 on SINet·COD10K-test S_α (TOST, Welch, α = 0.05).
- **H1b (secondary).** |μ_C10 − μ_CSHUF| < 0.005 on SINet·COD10K-test S_α (TOST, Welch, α = 0.05).
- **NC4K (secondary).** The same two tests on NC4K are reported and decide nothing.

## EQ.2 Design

| Item | Value |
|---|---|
| Arms | B, C10, CSHUF |
| B | 1000 renders drawn uniformly without replacement from the 4447 foregrounds, **redrawn per seed** (`default_rng(700000 + seed)`), exactly as committed |
| C10 | The committed set (`rebuild/ABC/out/abc_stems_C_a1.0.txt`, sha256 `58333d3c36db0891…`), unchanged |
| CSHUF | The committed set (`rebuild/ABC/out/t2/abc_stems_CSHUF.txt`, sha256 `2a661ce64f3c1021…`), unchanged |
| Architecture | **SINet only.** SINet-v2 is not run: at 2.03 GPU-h per run it does not fit the budget once the P0 work is scheduled (EQ.6). This is decided here. |
| Seeds | **101, 102, …, 129** (n = 29 per arm). None has been used before; seeds 42–50 are excluded. |
| Everything else | Identical to the committed SE campaign: base pool, trainer `MyTrain.py --method ours --iteration 2`, pseudo-labelling, 352×352, 40 epochs, Adam 1e-4, EMA 0.996, steps per epoch pinned at 253, checkpoint `Tea_epoch_best.pth` (CAMO-250 MAE on the EMA teacher), inference `MyTest.py`. |
| Footprint flags | `--save_ckpts minimal --link_pool` (saves fewer files and hardlinks the round-2 pool). They change no weight and no RNG; this is checked by the bridge re-train (`prereg/BRIDGE.md`) before any conclusion is drawn. |

**Sample size.** n = 29 per arm is the smallest n whose Welch-simulated TOST power (40,000 draws) is
at least 0.80 at a true Δ = +0.0024. That is the observed value; the simulation uses the eight-seed SDs
on the primary cell (B 0.00251, C10 0.00489). The closed form gives 28. The number is not capped.

This sample size is fragile, and that is stated now. If the true SDs equal their one-sided 80% upper
confidence bounds, the power at n = 29 is 0.58 for a true Δ = +0.0024, and 0.85 for a true Δ = +0.0012
(`EQ_design_numbers.json`). At the observed SDs, the expected 90% CI half-width for C10 − B is 0.0017.
**Equivalence may therefore not be reached even if the true difference is as small as observed.** That
outcome is reported as such (decision ii).

**Margin.** ±0.005 was chosen post hoc in the submitted paper, after the SE campaign. It is about
0.35× the reference effect of the reproduced published method (0.7030 → 0.7172, +0.0142). It is kept
because it is the margin the reviewer and the paper refer to, and it is reported as a limitation.

## EQ.3 Metric and scorer

- **Primary metric.** S_α at α = 0.5, scored by the committed scorer (`Eval/metrics.py`, called through
  `rebuild/ABC/abc_evaluate.score`) at 6 decimals.
- **Scorer check.** Before any EQ run is scored, the scorer must reproduce Sα 0.717216 / MAE 0.074463 on
  `Result/SINet/S2C`.
- **Also reported, deciding nothing.** E_φ (mean, `meanEm`), F_β^w, MAE.

## EQ.4 Analysis (implemented in `analysis/eq_analysis.py`, committed with this file)

1. **Primary.** For C10 − B on SINet·COD10K: Δ, the Welch 95% CI, the Welch 90% CI, and the TOST
   p-value at ±0.005 (the larger of the two one-sided Welch p-values).
   - H1 holds iff TOST p < 0.05, i.e. the 90% CI lies inside (−0.005, +0.005).
2. **H1b.** The same for C10 − CSHUF.
3. **The manuscript's 2σ̂ rule, also reported.**
   - σ̂ is the within-arm SD pooled over B, C10 and CSHUF (df = 3 × 28 = 84).
   - REAL EFFECT iff Δ > 2σ̂ **and** at least k\* = 20 of the 29 seed-paired differences agree in sign
     with Δ (exact zeros do not count). The definition is that of `abc_evaluate.py`.
   - k\* is the smallest k with P(Bin(29, ½) ≥ k) ≤ 9/256. That is the same one-sided tail as SE's 7/8
     rule; P(Bin(29, ½) ≥ 20) = 0.031.
   - WITHIN NOISE iff |Δ| ≤ 2σ̂. INCONCLUSIVE otherwise. REAL REGRESSION is the mirror case.
4. **Secondary, labelled as such.**
   - The seed-paired analysis: paired 95% and 90% CIs and paired TOST, where seed s of one arm is paired
     with seed s of the other. It is never substituted for the Welch result. B redraws its set at every
     seed, while C10 and CSHUF do not.
   - A pooled estimate combining EQ with SE: a fixed-effect inverse-variance combination of the two
     campaigns' Welch Δ (weights 1/SE²), with a normal 90% CI. It is secondary because SE was seen
     before EQ was designed.
   - NC4K: everything above, repeated.
5. **Multiplicity.** H1 is the single primary test. H1b and NC4K are secondary and reported
   unadjusted, with a Holm adjustment across the four TOSTs as a note.

## EQ.5 Decision statements, written now (for H1; H1b uses the same wording with CSHUF)

- **(i) Equivalent** (TOST p < 0.05):
  "A separately pre-registered confirmatory campaign with 29 fresh seeds per arm establishes that
  targeted and random allocation are equivalent within ±0.005 S_α on the primary cell
  (Δ = {Δ}, 90% CI [{lo90}, {hi90}])."
- **(ii) Neither equivalent nor detected** (TOST p ≥ 0.05 and the 95% CI includes 0):
  "The confirmatory campaign neither detects an advantage nor establishes equivalence at ±0.005
  (Δ = {Δ}, 95% CI [{lo95}, {hi95}]). Effects as large as {hi95} are not excluded at this precision."
- **(iii) Detected** (95% CI excludes 0):
  "The confirmatory campaign detects a difference of {Δ} S_α (95% CI [{lo95}, {hi95}]) in favour of
  {arm}." If the 90% CI also lies inside ±0.005, add: "the difference is smaller than the ±0.005 margin."

The manuscript's 2σ̂-rule verdict is reported next to whichever statement applies.

## EQ.6 Budget, stopping and failures

- **Budget.** 87 SINet runs × 1.77 GPU-h (measured over the SE campaign) ≈ 154 GPU-h. That fits within
  the window before 2026-11-16 06:00 IST, alongside the CDR SINet runs, both of which are never
  sacrificed. The full budget table is in `EXECUTION_STATUS.md`.
- **Stopping.** All 87 runs complete. Nobody looks at endpoint metrics in the meantime: the queue
  trains and runs inference only, and `eq_analysis.py` scores and analyses once, after the last run has
  verified.
- **Failures.** A run that fails verification is discarded and re-run from scratch **with the same
  seed**. It is never replaced by a new seed and never dropped. If a seed cannot be completed by the
  cutoff, the campaign is reported as incomplete, with that seed named, and analysed on the seeds that
  completed for all three arms. That analysis is labelled a deviation.

## EQ.7 Per-run assertions

- **Before launch.** All six preflight gates pass on the EQ pools: base-pool bytes against the E0
  manifest, injected-set hashes (B: the seed-specific draw; C10 and CSHUF: the committed hashes),
  render masks, positional parity, one trainer, determinism.
- **After training.** `verify_run` checks 2 rounds, steps per epoch exactly 253, last epoch 039/040,
  `Tea_epoch_best` present, and the target pool loaded twice. The pseudo-label count (`n_appended`) is
  recorded.

## EQ.8 What each outcome would and would not mean

- **Equivalence** would establish, for this pipeline and operating point, that any advantage of the
  targeted allocation over random selection is smaller than 0.005 S_α. It would not address other
  generators, other pools or other training setups.
- **Neither** would mean the experiment is still too imprecise to separate "no effect" from "an effect
  of up to the upper CI bound". It would not be evidence of an effect.
- **Detection** would contradict the submitted claim on the primary cell and would be reported
  prominently, whatever its sign.

---
*Amendments (dated, append-only) go below this line.*

### Amendment 1: 2026-11-11, committed before any EQ run has started (no EQ run has been trained, inferred or scored)

1. **n = 27 per arm**, seeds **101–127**; arms **B, C10, CSHUF**; **SINet only**. Seeds 128 and 129 are removed
   from the campaign and are never run.
2. **Reason.** n is capped below the 80% power target (29) for two reasons: the 2026-11-09 power outage, which
   cost about 57 GPU-hours, and GPU time given to other campaigns. The corresponding author authorised the cap
   on 2026-11-11.
3. **Expected precision at n = 27** (Welch-simulated, 40,000 draws, eight-seed SDs B 0.00251 and C10 0.00489;
   `prereg/EQ_amendment1_numbers.json`, from `RESULT_TABLES/TH01_power.csv`):
   - TOST power at a true Δ = +0.0024 is **0.78** for H1 (C10 − B) and 0.76 for H1b. It is at least 0.92 for a
     true Δ ≤ +0.0012. If the true SDs are at their 80% upper bounds, power at Δ = +0.0024 is 0.55.
   - Expected 90% CI half-width for C10 − B: **0.00178**. Expected 95% CI half-width: 0.00214.
   - The 2σ̂ rule's sign threshold at n = 27 is **k\* = 19** (P(Bin(27, ½) ≥ 19) = 0.026 ≤ 9/256; the EQ.4 rule).
4. **Equivalence at ±0.005 may not be reachable at this n.**
5. **Order.** Runs go seed by seed, with all three arms for each seed (101: B, C10, CSHUF; then 102; …).
6. **If the cutoff comes first** (2026-11-17 06:00 IST), every completed run is analysed as pre-registered and
   the result is reported as **INCOMPLETE**, with the missing runs named. No completed run is dropped. Welch
   and the pooled σ̂ use all completed runs of each arm; the seed-paired quantities use the seeds both arms of
   a contrast completed.
7. **No interim looks.** No COD10K-test or NC4K number for any EQ run is computed or opened before all 81 runs
   are trained. That includes the MAE lines `MyTest.py` writes into the inference logs.
8. After this commit, n never changes. `analysis/eq_analysis.py` is updated in the same commit (seeds 101–127,
   k\* = 19, the INCOMPLETE path) and re-passes its self-test on SE data only.

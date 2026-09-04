# PREREGISTRATION.md — the A/B/C campaign's decision rule

> **Committed before the first training run. Never edited after any number exists.**
>
> This file, and the six patches of `ABC_PLAN.md` §A.7, are committed in the commit that precedes
> run 1. **If any part of §1 below is changed after a single Sα has been computed, the campaign is void
> and must be re-run.** The whole value of a pre-registered rule is destroyed if it is written, or
> amended, after the numbers exist.

## §1 The rule — verbatim, as approved

```
Primary endpoint : COD10K-test, Sα, Tea_epoch_best.pth, final round.
Secondary        : NC4K, Sα (reported, never decides).
Also reported    : MAE, Fβw, Eφ on both endpoints.
Seeds            : {42, 43, 45}.
Noise estimate   : sigma_hat = pooled within-arm sd of Sα across all arms.
Gaps             : Delta_BA = mean(Sa_B) - mean(Sa_A2)   [does re-render data help over matched control]
                   Delta_CB = mean(Sa_C) - mean(Sa_B)    [THE claim: does targeting beat random]
                   (also report Delta vs A0 for paper-comparability)
Rule:
  REAL EFFECT     iff Delta > 2*sigma_hat AND sign consistent 3/3 seeds
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3  -> report as-is, do NOT add seeds
Power statement  : resolves an effect ~half the paper's MT->Ours gap (0.0142) and no smaller.
Report           : 2*sigma_hat rule primary; paired per-seed differences as a table; sign-consistency
                   count; NO p-value at n=3.
```

## §2 Mechanical specification — operational definitions only; alters nothing in §1

Needed because "pooled within-arm sd" and "sign consistent" cannot be pre-registered without them.

1. **Scope.** The rule is applied **independently per architecture** (SINet, SINet-v2). SINet is the
   primary; SINet-v2 is the robustness check. Neither overrides the other; a disagreement is reported as
   a disagreement.

2. **σ̂.** Per architecture, per endpoint:

   ```
   sigma_hat = sqrt( SUM_over_arms SUM_over_seeds (x[arm,seed] - mean(x[arm]))^2
                     / SUM_over_arms (n_seeds - 1) )
   ```

   over arms {A0, A2, B, C} and seeds {42, 43, 45}, **df = 4 × 2 = 8**. Reported to 6 decimals beside
   the four per-arm sds, so the arm-B selection-variance asymmetry (`ABC_PLAN.md` §A.4) is visible.

3. **"Sign consistent 3/3."** The **paired per-seed** difference `x[C,s] − x[B,s]` (and
   `x[B,s] − x[A2,s]`) has the same sign as the corresponding mean difference for all three
   `s ∈ {42, 43, 45}`.

4. **Metric source.** `Eval/metrics.py` classes, scored from the PNGs written by `MyTest.py`, at **6
   decimal places**. Headline Eφ = **`meanEm`**, with `adpEm` and `maxEm` also reported and the
   `metrics.py:274` truncation disclosed.

5. **Checkpoint.** `Snapshot/ABC/{RUNID}/Tea_epoch_best.pth` after the final (second) CSRDA round. A run
   failing any `ABC_PLAN.md` §A.8.3 assertion is discarded and re-run; the discard is logged and the
   partial checkpoint never enters the metrics.

6. **α.** α = 1.0 is the primary arm C. α = 0.5 is a **pre-registered secondary**, declared here before
   any run, reported in a separate block, and never substituted for the primary.

7. **No optional stopping and no metric substitution.** Seeds are not added to break an INCONCLUSIVE
   (§1 says so explicitly). If σ̂ comes out larger than the prior scale, the bar rises with it — the bar
   is `2 σ̂`, not a fixed number.

8. **Prior scale, for expectation only — not the bar.** σ(Sα) ≈ **0.003555** (n = 6 archived
   `--iteration 1` runs) and **0.002287** (same seed 42, n = 3). At the former the bar is
   ΔSα > **0.0071**; at the latter, > **0.0046**. Both figures are provenance-caveated and were measured
   at a different operating point (`ABC_PLAN.md` §A.6). The bar of record is computed from this
   campaign's own runs.

9. **Power, restated arithmetically.** The repo's whole MT→Ours gap is 0.7030 → 0.7172 = **+0.0142 =
   4.0 σ_prior**, i.e. **twice the detection bar.** The campaign resolves an effect **half the size of
   the paper's own headline improvement, and no smaller.** That is the experiment's sensitivity and
   should be stated as such.

10. **Baseline sanity gate.** `SINet_A0_s42` must satisfy `|Sα − 0.7172| ≤ 3 σ_prior = 0.0107` against
    `Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`, or the campaign halts for diagnosis before the
    remaining 23 runs.

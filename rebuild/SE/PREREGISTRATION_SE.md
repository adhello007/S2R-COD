# PREREGISTRATION_SE.md — the seed-expansion campaign's decision rule

> **Committed before the first SE training run. Never edited after any SE number exists.**
>
> Dated **2026-09-18**, at commit `b755aa9`. Written **before** any SE pool was built and any SE
> number existed.

---

## §SE.0 The problem this document exists to solve

The revision brief asks for the primary arms to be expanded "from 3 to 8–10 seeds … to reduce pooled
variance and tighten the decision bar." **Done naively, that is the one thing this project's frozen
rules forbid.** Both say so in terms:

- `PREREGISTRATION.md`: `INCONCLUSIVE ... -> report as is, do NOT add seeds`
- `PREREGISTRATION_T2.md` §T2.10, titled *No substitution, no optional stopping*: "Seeds are not
  added to break an INCONCLUSIVE."

Those clauses exist because adding seeds *after seeing a result* is optional stopping: it lets the
analyst keep sampling until the answer moves, and it invalidates the error rate of every verdict the
campaign reports. The committed verdicts are the paper's central claim, and their value is entirely
in the fact that nothing about them was chosen after the numbers existed.

**So SE does not add seeds to ABC or T2.** It is a **separate campaign with its own arms, its own
noise estimate, its own bar and its own verdicts**, standing beside the committed ones exactly as T2
stands beside ABC. Three consequences, committed now:

1. **The committed 3-seed verdicts are not restated, recomputed, replaced or re-decided.** They
   remain the paper's pre-registered result. `abc_verdict.json` and `out/t2/abc_verdict.json` are
   untouched.
2. **SE's verdicts are reported alongside them, never instead of them.** Where SE and a committed
   verdict disagree, **both are reported and the disagreement is the finding**, not an occasion to
   pick one.
3. **SE's own seeds are fixed here, before its first run**, so SE is not itself subject to optional
   stopping. If SE returns INCONCLUSIVE, that is reported and no further seed is added to SE either.

## §SE.1 The rule — verbatim, as approved

```
Dated extension  : 2026-09-18. A SEPARATE campaign. PREREGISTRATION.md, PREREGISTRATION_T2.md,
                   PREREGISTRATION_OR.md and PREREGISTRATION_FX.md are frozen and unaltered.

Question under   : ABC and T2 resolve coarsely. The decisive gap Delta(C10 - B) sits at 0.91x the
test               tighter of the two committed bars, and the largest falsification gap at 1.82
                   sigma_hat. A campaign with more seeds per arm would put a narrower bar on the
                   same comparisons. SE runs that campaign, from scratch, under its own rule.

Arms             : B, C10, CSHUF, CINV -- exactly as defined in PREREGISTRATION.md and
                   PREREGISTRATION_T2.md, by the same selection code, with no change of any kind.
                   A0 and A2 are NOT included: they are not in any decisive gap, and A0's seed
                   instability is what inflated ABC's pooled bar in the first place.

Seeds            : the three committed seeds {42, 43, 45} PLUS five new ones {46, 47, 48, 49, 50},
                   giving n = 8 per arm. The five new seeds are declared HERE, before any SE run,
                   and no sixth is added for any reason.
                   Arm B REDRAWS its 1000 stems per seed, by design and unchanged
                   (abc_common.arm_b_stems, DRAW_NS + seed). C10, CSHUF and CINV are deterministic
                   across seeds; only the training seed varies. Both properties are inherited, not
                   re-decided.
                   The 12 runs at the committed seeds are NOT re-trained: the committed
                   checkpoints and predictions are re-scored, and must reproduce
                   rebuild/ABC/out/abc_metrics.csv and out/t2/abc_metrics.csv at 6 dp exactly or SE
                   halts. Only the 40 runs at the five new seeds are trained.

Primary endpoint : COD10K-test, S-alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K, S-alpha (reported, never decides).
Also reported    : MAE, F-beta-w, E-phi on both endpoints.

Noise estimate   : sigma_hat_SE = pooled within-arm sd of S-alpha over {B, C10, CSHUF, CINV}, per
                   architecture, per endpoint, df = 4 x 7 = 28. Per-arm sd reported beside it.
                   This is SE's bar of record. It is NOT swapped for a committed sigma_hat in
                   either direction, whichever is smaller.

Gaps             : Delta_1 = mean(Sa_C10)   - mean(Sa_B)      [targeting vs random]
                   Delta_2 = mean(Sa_C10)   - mean(Sa_CSHUF)  [real signal vs destroyed]
                   Delta_3 = mean(Sa_C10)   - mean(Sa_CINV)   [real signal vs reversed]
                   Delta_4 = mean(Sa_CSHUF) - mean(Sa_CINV)   [is direction ordered at all]

Rule (the frozen four bands, with the sign-consistency count rescaled to n = 8):
  REAL EFFECT     iff Delta >  2*sigma_hat_SE AND sign consistent >= 7/8 seed-paired differences
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat_SE
  REAL REGRESSION iff Delta < -2*sigma_hat_SE AND sign consistent >= 7/8
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat_SE but sign not >= 7/8 -> report as-is, ADD NO SEEDS

  The 7/8 threshold is declared here, before any SE number. It is the closest analogue of the
  committed 3/3 rule that n = 8 admits: 3/3 has a one-sided probability of 1/8 = 0.125 under a fair
  coin, and 7-or-more of 8 has 9/256 = 0.035 -- i.e. STRICTER than the committed rule, not looser.
  Requiring 8/8 would be stricter still but is brittle to a single outlier run; 7/8 is chosen for
  that reason and not because of anything any number does.

At n = 8 a p-value is admitted, and is REPORTED WITHOUT DECIDING:
  Paired t-test on the 8 seed-matched differences, two-sided, and a Welch two-sample t-test, plus
  90% and 95% intervals and a TOST at delta = 0.005. These are reported for every gap. THE VERDICT
  REMAINS THE 2*sigma_hat_SE RULE ABOVE. No p-value threshold appears in any verdict band, and no
  gap is reclassified by one. This clause exists so that the statistics cannot be promoted into the
  decision after the fact.

Interpretation, fixed before any SE number exists:
  Delta_1 WITHIN NOISE at the tighter bar
      -> the committed null survives a bar roughly sqrt(8/3) = 1.63x tighter. The paper's power
         qualification narrows accordingly and the sentence "this campaign resolved coarsely" must
         be rewritten against SE's bar rather than deleted.
  Delta_1 > 2*sigma_hat_SE with >= 7/8
      -> targeting DOES beat random at this sensitivity. The committed WITHIN NOISE verdict is then
         a power failure, must be reported as one, and the paper's central claim must be withdrawn
         as stated and re-scoped. This is the outcome that most damages the paper and it is
         reported if it occurs.
  Delta_2 or Delta_3 > 2*sigma_hat_SE with >= 7/8
      -> the uncertainty DIRECTION contributes after all, and Section 4's concentration-not-
         targeting claim is falsified as stated and must be softened.
  Delta_2 and Delta_3 WITHIN NOISE while Delta_1 clears the bar
      -> concentration helps and direction does not, now at n = 8. This is the paper's thesis at
         the strongest sensitivity this suite can reach.
  Whichever occurs is reported. No arm is dropped, no seed is added, no gap is redefined after the
  fact, and no result is reclassified once seen.

Report           : 2*sigma_hat_SE rule primary; the committed 3-seed verdicts reported BESIDE it,
                   never replaced; paired per-seed differences for all 8 seeds; sign-consistency
                   counts; the statistics above, marked non-decisional.
```

## §SE.2 Mechanical specification — operational definitions only; alters nothing in §SE.1

### SE.2.1 Inheritance

Arms, pools, gates, trainer, scorer, endpoints and checkpoint rule are inherited **identically** and
asserted by re-running the same code. SE adds **no new arm and no new script**: it adds five values
to the seed list via the driver's `--seeds` flag, whose default is the committed `{42, 43, 45}`, and
one output namespace `rebuild/ABC/out/se/`.

`--exposure` is left at its default `fixed_steps`, so SE runs the committed schedule. SE and FX vary
different factors and are not combined.

### SE.2.2 What the five new seeds change, disclosed before the run

- **Arm B redraws.** B's 1000 stems are a function of the seed, so the five new seeds draw five new
  random sets. This is arm B's committed design, and it means B carries selection variance that the
  three deterministic C-family arms do not. The consequence is that `sigma_hat_SE` is **inflated by
  arm B**, making SE's bar *harder* to clear rather than easier. Per-arm sds are reported beside the
  pooled value so this is visible.
- **The C-family arms do not redraw.** Their pools are identical at all eight seeds; only the
  training seed varies. G5's cross-seed digest equality is asserted over all eight.
- **Nothing else varies.** Same base pool, same 4040-image target set, same budget, same alpha, same
  embedder, same serving order.

### SE.2.3 Re-scoring the committed seeds

The 12 runs at seeds {42, 43, 45} are **not re-trained**. Their committed predictions are re-scored
by the same scorer in the same process and must reproduce the committed CSVs at the precision both
record (6 dp, exact equality). This is the strictest satisfiable form of that check and is declared
here rather than after a halt — see `PREREGISTRATION_T2.md` Addendum A1 for why the `< 1e-9` form of
this clause is a defect.

A mismatch is a **HALT**: it would mean something in the tree had drifted since ABC, and no SE number
could be trusted.

### SE.2.4 Gates

All six pre-flight gates must PASS on the SE pools before any training, with no `--skip-gate`, plus
the T2.4 same-shape assertion on CSHUF and CINV and the T2.7 Jaccard distinctness gate on every
C-family pair, both unchanged.

### SE.2.5 Power, stated before results

`sigma_hat` scales roughly as `1/sqrt(n)` in the standard error of a difference, so moving from
n = 3 to n = 8 should tighten the bar by about `sqrt(8/3) = 1.63x` **if the per-arm spreads stay as
measured**. Against T2's committed bar of 0.0055 on SINet that projects to roughly 0.0034, which
would put the committed `Delta(C10 - B) = 0.0050` **above** the bar.

**That projection is stated here, before the runs, precisely because it names the outcome that would
damage the paper most.** If SE's bar lands near 0.0034 and the gap stays near 0.0050, SE returns
REAL EFFECT and the committed null is a power failure. The five new seeds may equally move the gap
itself; nothing here predicts which. **A WITHIN NOISE result at SE's bar is still "no effect
resolvable at this sensitivity", never "no effect."**

### SE.2.6 Additivity

SE writes to `rebuild/ABC/out/se/` and appends `EXP SE` blocks to `results/REBUILD_LOG.txt`. It
overwrites no committed artifact. Re-running the ABC and T2 pre-flights under the SE diff must
produce the same pass/fail decisions and byte-identical committed stem lists.

### SE.2.7 Cost, stated because it bounds what can be run

40 new training runs. The 24-run ABC campaign cost 46.8 GPU-hours on two RTX PRO 6000 cards, so SE
is roughly **78 GPU-hours, about 39 hours of wall clock on two cards**. That is the reason this
campaign is specified in full but scheduled after OR and FX.

### SE.2.8 The sign rule, mechanically

`§SE.1`'s `>= 7/8` is passed to the shared evaluator as `--min-sign 7`. That flag's default is `0`,
meaning "all seed-paired differences", which is the committed 3-of-3 rule exactly — so every prior
invocation of the evaluator is unchanged and ABC, T2, OR and FX are unaffected.

The flag exists because the evaluator's generalisation of the committed rule is `n`-of-`n`, and at
`n = 8` that is **far stricter** than the rule it generalises: 3-of-3 has a one-sided probability of
`0.125` under a fair coin, 8-of-8 has `0.004`. A stricter sign requirement makes `REAL EFFECT`
harder to reach and therefore biases toward `WITHIN NOISE` — **which is this paper's own claim**. The
requirement is consequently declared rather than inherited, and it is declared in the direction that
makes the paper's claim harder to support, not easier.

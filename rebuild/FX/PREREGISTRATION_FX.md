# PREREGISTRATION_FX.md — the optimisation-schedule control's decision rule

> **Committed before the first FX training run. Never edited after any FX number exists.**
>
> **ADDITIVE.** `rebuild/ABC/PREREGISTRATION.md`, `PREREGISTRATION_T2.md` and
> `rebuild/OR/PREREGISTRATION_OR.md` are frozen and are **not altered, superseded or
> reinterpreted**. No committed arm, gate, verdict or artifact is restated, recomputed or replaced.
> FX adds **one factor** — the trainer's step schedule — three arms that instantiate its new level,
> and one output namespace. It inherits everything else unchanged and asserts that inheritance
> mechanically.
>
> If any part of §FX.1 is changed after a single FX Sα has been computed, FX is void and must be
> re-run. A/B/C, T2 and OR are unaffected either way.
>
> Dated **2026-09-18**, at commit `b755aa9`. Written **before** any FX pool was built and any FX
> number existed.

---

## §FX.0 What this control is for, and one thing it is *not* for

The paper's own scope section concedes the largest reviewer objection available against it:

> *"You fixed the number of gradient steps and then observed that adding data didn't help. That is a
> scheduling bug in your training script, not a result about synthetic data."*

`total_step` is pinned at **253** (SINet) and **127** (SINet-v2) in both rounds of every committed
run, regardless of pool size, because `zip(source_loader, target_loader)` truncates to the shorter
loader and the 4040-image target loader is always the shorter one (`MyTrain.py:326`). FX removes
that pin and measures what changes.

**The thing it is not for, stated before any result exists.** It is tempting to say the pin
invalidates the decisive gap Δ(C10 − B). **It does not, and FX is not run on that premise.** B and
C10 hold *identical* pool sizes (5447), so they receive *identical* step counts under **both**
schedules. The pin was never an asymmetry between them.

What the pin actually does is change what adding 1000 images *means*:

| Schedule | steps/epoch (SINet, 5447-pool) | exposures per image per epoch | Stage C's 1000 images |
|---|---|---|---|
| `fixed_steps` (committed) | 253 | 253×16 / 5447 = **0.74** | **displace** real images inside a fixed budget |
| `fixed_exposures` (FX) | 341 | 341×16 / 5447 = **1.00** | **are added to** a budget that grew |

So under the committed schedule every arm's added images *substitute* for base-pool exposure, and
under FX they are genuinely trained on in addition. If the targeting signal carries anything, it has
a better chance of showing under FX. **FX is therefore the condition most favourable to the paper's
own hypothesis, which is exactly why it is worth running against a null.**

## §FX.1 The rule — verbatim, as approved

```
Dated extension  : 2026-09-18. Additive to PREREGISTRATION.md, PREREGISTRATION_T2.md and
                   PREREGISTRATION_OR.md (all frozen, unaltered).

Factor added     : SCHEDULE, with two levels.
                   fixed_steps     = min(len(source_loader), len(target_loader)). The committed
                                     behaviour of every run in ABC, T2 and OR. NOT re-run: the
                                     committed A0/B/C10 rows supply this level.
                   fixed_exposures = len(source_loader), with the target loader CYCLED so it never
                                     exhausts. Every source image is seen exactly once per epoch and
                                     the optimisation budget scales with the pool.
                   Implemented as MyTrain.py --exposure, PATCH P6, default fixed_steps. The default
                   branch is byte-identical to the committed code path.

New arms         : A0FX, BFX, C10FX. Each has a pool BYTE-IDENTICAL to its base arm's (same stems,
                   same size, same provenance, same per-seed draw for B) and differs from it in
                   the --exposure flag and in NOTHING else. Asserted, not assumed: G5 compares each
                   FX pool's image_digest and gt_digest against its base arm's.

Expected steps   : ceil(pool / batch), asserted per run and per architecture:
                     SINet    (batch 16)  A0FX 278   BFX 341   C10FX 341   (pinned was 253)
                     SINet-v2 (batch 32)  A0FX 139   BFX 171   C10FX 171   (pinned was 127)
                   A run whose round-1 step count equals the PINNED value is a HALT, not a result:
                   it means the flag did not take effect and the manipulation never happened.

Primary endpoint : COD10K-test, S-alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K, S-alpha (reported, never decides).
Also reported    : MAE, F-beta-w, E-phi on both endpoints.
Seeds            : {42, 43, 45}, the committed set, so every FX run is seed-paired with a committed
                   fixed_steps run of the same arm and architecture.

Noise estimate   : sigma_hat = pooled within-arm sd of S-alpha over arms {A0FX, BFX, C10FX}, per
                   architecture, per endpoint, df = 3 x 2 = 6. Per-arm sd reported beside it.
                   FX's own sigma_hat is the bar of record for FX gaps. It is NOT swapped for
                   ABC's or T2's if it comes out larger.

Gaps, within FX  : Delta_1 = mean(Sa_C10FX) - mean(Sa_BFX)   [does targeting beat random when the
                                                              budget is actually trained on]
                   Delta_2 = mean(Sa_BFX)   - mean(Sa_A0FX)  [does padding the pool help when the
                                                              optimisation budget grows with it]
Gaps, across     : Delta_3 = mean(Sa_C10FX) - mean(Sa_C10)   [what the schedule itself is worth]
schedule           Delta_4 = mean(Sa_BFX)   - mean(Sa_B)
                   Delta_5 = mean(Sa_A0FX)  - mean(Sa_A0)
Interaction      : Delta_I = Delta_1 - Delta(C10 - B) as committed in abc_verdict.json.
                   REPORTED WITH ITS OWN BAR AND NEVER TREATED AS A VERDICT: a difference of two
                   noisy differences carries roughly sqrt(2) times the noise of either, and at n=3
                   that is not a quantity this design can resolve. It is reported so the reader can
                   see its sign and size, explicitly labelled underpowered.

Rule (identical to A/B/C, T2 and OR, unchanged):
  REAL EFFECT     iff Delta > 2*sigma_hat AND sign consistent 3/3 seeds
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3  -> report as-is, do NOT add seeds

Interpretation, fixed before any FX number exists:
  Delta_1 WITHIN NOISE
      -> the null on targeting SURVIVES the removal of the dilution confound. The paper's first
         setup-specific limitation is then measured rather than conceded, and the sentence
         "nothing here measures what happens when the optimisation budget grows with the data"
         must be DELETED and replaced by this measurement.
  Delta_1 > 2*sigma_hat with 3/3
      -> targeting DOES help once its images are actually trained on. The committed null is then
         scoped to the pinned schedule and the paper's central claim must be narrowed accordingly.
         This is the outcome that most damages the current framing and it is reported if it occurs.
  Delta_2 > 2*sigma_hat with 3/3
      -> padding the pool helps when the budget grows with it. Reported as the answer to the
         largest open question the paper currently creates, regardless of what Delta_1 does.
  Delta_3/4/5 any sign
      -> reported as the schedule's own effect. These are NOT a verdict about targeting and no
         targeting claim may be built on them.
  Whichever occurs is reported. No arm is dropped, no seed is added, no gap is redefined after the
  fact, and no result is reclassified once seen.

Report           : 2*sigma_hat rule primary; paired per-seed differences; sign-consistency counts;
                   NO p-value at n=3. Every FX run's measured total_step is reported beside its
                   score, so the reader can verify the manipulation took effect run by run.
```

## §FX.2 Mechanical specification — operational definitions only; alters nothing in §FX.1

### FX.2.1 The code change, in full

`MyTrain.py`, PATCH **P6**, two sites plus one CLI flag:

1. `--exposure {fixed_steps,fixed_exposures}`, **default `fixed_steps`**.
2. `total_step` becomes `len(source_loader)` when the flag is `fixed_exposures` (it already was for
   `source_only`), and is otherwise unchanged.
3. The batch generator becomes `zip(source_loader, _cycle(target_loader))` when the flag is
   `fixed_exposures`, and is otherwise unchanged. `_cycle` **re-iterates** the loader rather than
   caching its batches, so memory is unchanged and each pass is freshly shuffled.

**The default path is byte-identical to the committed code path**, and `getattr(opt, 'exposure',
'fixed_steps')` is used so that any caller that predates the flag behaves exactly as before. The
five existing `MyTrain.py` patch marks that gate **G3** checks are untouched; P6 adds a sixth.

### FX.2.2 Identity of the pools, asserted

An FX arm's pool is its base arm's pool, rebuilt by the same builder from the same stems. `arm_added`
dispatches on `base_arm(arm)`, so `C10FX` and `C10` call the identical selection code with identical
arguments. G5 asserts `image_digest` and `gt_digest` equality between each FX arm and its base arm.
**If those digests ever differ, the schedule is no longer the only manipulated factor and FX halts.**

RUNIDs differ (`SINet_C10FX_s42` vs `SINet_C10_s42`) so that no FX run can write into a committed
snapshot, pool or prediction directory. That separation is by construction, not convention — every
path is RUNID-prefixed, including the CLS round-2 pool.

### FX.2.3 What the schedule change also changes, disclosed before the run

Removing the pin is not a single-variable edit and pretending otherwise would be dishonest. Under
`fixed_exposures`, relative to the committed schedule:

- **more gradient steps per epoch** (the intended manipulation): +9.9% for A0FX, +34.8% for BFX and
  C10FX on SINet; +9.4% and +34.6% on SINet-v2;
- **more EMA teacher updates and more consistency-loss evaluations per epoch**, in the same
  proportion, since both happen once per step;
- **more target-image views per epoch**, because the cycled target loader is consumed past its own
  length — 341 target batches per epoch instead of 253, drawn from the same 4040 images;
- **a longer wall clock**, by roughly the step ratio.

All four are consequences of "let the source loader drive", not separable factors, and no attempt is
made here to separate them. **What FX therefore identifies is the schedule as a whole, not the step
count in isolation**, and every FX claim is worded that way.

### FX.2.4 The learning-rate schedule is NOT rescaled, and why

`adjust_lr` decays on an **epoch** counter, not a step counter, and the epoch count is held at the
committed 40 / 100. So FX arms take more steps at each learning rate rather than traversing the
schedule faster. Rescaling the decay to hold total steps constant would re-introduce a fixed budget
and defeat the control. Holding epochs fixed and letting steps grow is the operational meaning of
"fixed exposures per image", which is what the control was asked for. **Disclosed, not silent:** an
alternative design that holds total steps constant while varying the mixture is a different
experiment and is not run here.

### FX.2.5 Round 2 and CLS

Round 2 rebuilds from ImageNet initialisation on the CLS-enlarged pool, exactly as committed. Under
FX the round-2 step count is therefore `ceil(pool_r2 / batch)`, which is larger again and varies by
run with `n_appended`. **Only the round-1 step count is asserted** — it is the one whose expected
value is known in advance from the pool size. The round-2 count is recorded and reported per run.

`n_appended` is a second uncontrolled channel already disclosed for ABC and T2 (the pseudo-label
filter depends on each arm's own round-1 model). FX inherits that disclosure unchanged and reports
its own spread.

### FX.2.6 Gates

All six pre-flight gates must PASS on the FX pools before any training, with no `--skip-gate`, plus:

| Gate | Requirement |
|---|---|
| G1–G6 | unchanged, as inherited |
| **FX-A** | every FX pool's `image_digest`/`gt_digest` equals its base arm's |
| **FX-B** | round-1 `total_step` equals `ceil(pool / batch)` for every FX run |
| **FX-C** | round-1 `total_step` does **not** equal the pinned committed value for any FX run |

FX-C is the gate that proves the manipulation happened. It cannot be waived.

### FX.2.7 No substitution, no optional stopping

Seeds are not added to break an INCONCLUSIVE. σ̂ is FX's own. The primary endpoint is not swapped for
NC4K. No metric is substituted for Sα. The committed fixed_steps rows are not re-trained, re-scored
or adjusted.

### FX.2.8 Power, stated before results

At n = 3 per arm and df = 6, FX resolves effects of the same order as T2's bar (≈ 0.0055 on SINet)
and not smaller ones. **A WITHIN NOISE result is consistent with a small real effect and must be
reported as "no effect resolvable at this sensitivity", never as "no effect."**

And as in OR, **the asymmetry runs against the paper**: WITHIN NOISE on Δ_1 is the pro-paper outcome,
so FX reports, beside every WITHIN NOISE verdict, the largest effect its bar could have missed.

### FX.2.9 Additivity

FX writes to `rebuild/ABC/out/fx/` and appends `EXP FX` blocks to `results/REBUILD_LOG.txt`. It
overwrites no committed artifact. Re-running the A/B/C pre-flight under the FX diff must produce the
same pass/fail decision and byte-identical committed stem lists; that regression check is part of
the FX build.

### FX.2.10 No p-value

No p-value, no bootstrap, no multiple-comparison correction, at n = 3.

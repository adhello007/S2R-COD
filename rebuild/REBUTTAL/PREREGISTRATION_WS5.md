# PREREGISTRATION_WS5.md — WS5′, the three-arm equivalence extension

> **Committed before the first WS5′ training run. Never edited after any WS5′ number exists.**
>
> Dated **2026-11-07 (IST)**. A **standalone** campaign. It is additive to every committed
> pre-registration, all unaltered, and **never pooled with SE**: SE's verdicts stand exactly
> as decided. Sizing: `EXP REBUTTAL_WS5_POWER` (2026-11-07T15:03:12, script
> `rebuild/REBUTTAL/ws5_power.py` @ `412d0f2`). Analysis: `rebuild/REBUTTAL/ws5_analyse.py`
> @ `c03a2c0`, committed before this file and before any WS5′ number.

## §WS5.0 Why this exists

All three reviewers made the same point. On the primary cell the targeting-versus-random
gap, C10−B = +0.0024 with Welch 95% CI [−0.0020, +0.0067], does not pass equivalence at
±0.005, so the paper can say "no evidence of benefit" but not "no meaningful effect". The
eight-seed design cannot resolve that (power 0.32 at the observed gap). WS5′ is a new,
pre-registered campaign sized to resolve it, and it also separates the two components
C10−B mixes: concentration and direction.

## §WS5.1 The rule — verbatim

```
Arms             : B      1000 renders drawn uniformly, per seed: numpy default_rng(700000 + seed)
                   C10    the committed allocation at alpha = 1.0 (deterministic)
                   CSHUF  C10's quotas with cluster scores permuted by the committed T2
                          permutation (perm_seed 910004; deterministic)
                   All three exactly as committed in rebuild/ABC/abc_common.py; nothing changed.
Architecture     : SINet only.
Seeds            : 51, 52, ..., 84  (n = 34 per arm; 102 runs). Fresh and disjoint from every
                   committed campaign. Same seed -> same initialisation across arms.
Primary endpoint : COD10K-test S_alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K S_alpha (reported, never decides). MAE, F-beta-w, E-phi reported.

Contrasts, fixed roles:
  C10 - B        total targeting effect
  C10 - CSHUF    direction effect, same shape
  CSHUF - B      concentration effect, same budget, no aim

Primary test     : Welch two one-sided tests at delta = 0.005, alpha = 0.05, per contrast.
Reported per contrast:
                   Welch 95% CI; Welch 90% CI; TOST p; paired-by-seed 95% CI (secondary);
                   the frozen ABC 2*sigma_hat / sign verdict FOR CONTINUITY ONLY, with
                   sigma_hat pooled within-arm over {B, C10, CSHUF} (df = 3 x 33 = 99) and the
                   sign rule scaled to n = 34: >= 23/34 (binomial tail 0.0288, the smallest k
                   not exceeding SE's >= 7/8 at 0.0352).

Outcome per contrast (Welch intervals), fixed now:
  EQUIVALENT   90% CI inside (-0.005, +0.005)
  BENEFIT      95% CI lower bound > 0
  HARM         95% CI upper bound < 0
  UNRESOLVED   otherwise
  BENEFIT or HARM can co-occur with EQUIVALENT (a precise effect smaller than 0.005). Both are
  then reported: "BENEFIT, smaller than 0.005" / "HARM, smaller than 0.005".

Joint readings, primary cell, fixed now:
  C10-B BENEFIT and C10-CSHUF EQUIVALENT   -> "concentration, not direction, helps downstream."
  all three EQUIVALENT                     -> "neither helps at +/-0.005."
  any other combination                    -> reported as it falls, contrast by contrast.

Multiplicity     : NONE. Three contrasts on two endpoints, reported unadjusted, and the paper
                   says so.
Power (planning) : at the observed eight-seed differences, n = 34: C10-B 0.86, C10-CSHUF 1.00,
                   CSHUF-B 1.00, all three jointly 0.86 (EXP REBUTTAL_WS5_POWER).
Stopping         : NONE. All 102 runs are trained, verified and scored, then analysed once.
                   No interim look at any endpoint score. All runs are reported or none.
Discards         : a run failing verify_run is re-run under the SAME seed and logged as a
                   discard. Its partial checkpoint never enters the metrics.
```

## §WS5.2 Schedule and gates, fixed now

1. **Launch gate: 2026-11-10 06:00 IST.** If WS5′ has not launched by then, it is
   **dropped**. It is not shrunk, and no other campaign is moved to make room.
2. **Planned end:** 2026-11-14 09:00 IST with a 10% buffer (00:00 without it). That assumes
   102 × 105.9 min on two GPUs, one run per GPU, which is the SE campaign's measured SINet
   wall clock.
3. **Disk gate before launch.** About 6.1 GB per run (pool 0.14, CLS round-2 pool 2.5,
   checkpoints 3.2, predictions 0.28), so about 625 GB for 102 runs. If free space at launch
   is below the campaign's need plus a 50 GB margin, WS5′ does not launch until space is
   made by a means the author approves. No committed artifact is deleted to make room
   without that approval.
4. **Analysis runs once,** after `abc_evaluate.py --arms B,C10,CSHUF --gaps ws5 --tag ws5
   --archs SINet --seeds 51,...,84 --min-sign 23` has scored all 102 runs:
   `.venv/bin/python rebuild/REBUTTAL/ws5_analyse.py`.

## §WS5.3 Disclosures fixed now

- **Arm-B draws at seeds 51–84 are new draws.** They are gated for mask identity and chance
  overlap with C10 and CSHUF in this campaign's own preflight; the gate follows the run set's
  seeds since commit `177a0ce`.
- **Independent-normal arms** were the power model's assumption. B carries draw variance by
  design, which the model inherits through B's observed sd.
- **A CI excluding zero is not promoted to an effect** beyond the outcome labels above, and
  the 2σ̂ verdict is reported for continuity only. It does not override the TOST outcome.

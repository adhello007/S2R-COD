# PREREGISTRATION_PC.md — the positive control

> **Committed before `pc_train.py` was written and before a single mean-teacher run was launched.**
> If any part of §PC.1–§PC.5 is changed after one `S_alpha` exists, this experiment is void and must
> be re-run from scratch. Amendments are append-only and dated.

## §PC.0 The question, and why a null campaign needs it

Across 36 committed training runs — 24 in the A/B/C campaign and 12 in the falsification campaign —
**no gap anywhere clears its bar.** Every verdict is WITHIN NOISE.

The falsification arms are a strong **negative** control: they show the harness does not manufacture
differences where none exist. They are not evidence that it can detect differences that do exist.
Without that, every null in this work is ambiguous between two readings:

1. the effect is absent or smaller than the bar, or
2. **the harness cannot resolve effects of this size at all**, in which case we are measuring the
   instrument rather than the method.

Nothing committed distinguishes these. This experiment does.

## §PC.1 Design

- **Architecture:** SINet only. The primary architecture of the frozen campaigns.
- **Method:** `MyTrain.py --method mean_teacher`. `MyTrain.py:249-251` forces `--iteration 1` for any
  non-`ours` method, so the MT arm is single-round by construction; this is recorded, not chosen.
- **Seeds:** `{42, 43, 45}` — identical to every other campaign here.
- **Pool:** the base pool of 4447 pairs, i.e. arm A0's already-built pool, unpadded. MT is a baseline
  and receives no Stage C budget.
- **Scoring:** the same scorer, same endpoint (COD10K-test, `S_alpha`), same checkpoint rule as every
  committed run. Gate **G-PC1** requires the scorer to reproduce B1's committed
  `S_alpha 0.717216 / MAE 0.074463` before any PC number is computed, exactly as the A/B/C, T2 and
  T2C blocks each did.
- **Reference arm:** the **committed** C10 runs. They are re-used as scored, never re-trained.

## §PC.2 The contrast, and what it is a control on

`Delta(C10 - MT)` reproduces the published Mean-Teacher-to-Ours contrast inside this harness.

**This is a control on instrument sensitivity, not an ablation.** C10 differs from MT in method, in
round count, and in pool size simultaneously. It therefore cannot attribute any part of the gap to
Stage C, and no such attribution will be made from it. Its only job is to answer: *at the bar this
work uses to declare nulls, can this harness see an effect of the size the literature reports?*

## §PC.3 The reference magnitudes, fixed in advance

Two distinct quantities that this repository's own documents have conflated, separated here:

| Quantity | Value | Source |
|---|---|---|
| **Published** gap, SINet S2C: MT `0.6984` -> Ours `0.7136` | **0.0152** | `Experiments/REPRODUCE_TABLE1_v2.md` Table 1 |
| **This repository's reproduction** gap: MT `0.7030` -> Ours `0.7172` | **0.0142** | `rebuild/ABC/PREREGISTRATION.md` §9 |

The frozen falsification bar is `2*sigma_hat = 0.005533`. Both reference gaps are therefore
**2.6x and 2.7x** that bar.

## §PC.4 The prior, stated before the run so the outcome binds either way

Our committed C10 mean is `0.718481`. If our MT lands near the published `0.6984` or the repo's
`0.7030`, `Delta(C10 - MT)` should fall in roughly `0.015`-`0.020`, i.e. **2.7x-3.7x the tight bar**,
and the rule below should return DETECTED.

**We commit to publishing the outcome whichever way it falls.** A NOT DETECTED result would mean the
nulls in this work are bounded by the harness rather than by the method, and that is a finding about
our own evidence that we would be obliged to report prominently. There will be no additional seeds,
no second architecture added after the fact, and no adjustment to the bar in response to the result.

## §PC.5 The decision rule — frozen

```
sigma_hat_PC = pooled within-arm sd of S_alpha over arms {MT, C10},
               df = 2 * (3 - 1) = 4
bar_PC       = 2 * sigma_hat_PC

DETECTED       iff Delta(C10 - MT) >  bar_PC  AND sign consistent 3/3 seeds
NOT DETECTED   iff |Delta(C10 - MT)| <= bar_PC
INCONCLUSIVE   iff |Delta| > bar_PC but sign not 3/3 -> report as-is, do NOT add seeds
```

Reported alongside, and never substituted for the above:

- `Delta` against the **frozen falsification bar 0.005533**, unchanged, since that is the bar the
  paper's headline sensitivity analysis uses.
- The per-seed paired differences and the sign-consistency count.
- Per-arm standard deviations beside the pooled value.

**No p-value.** `n = 3`, consistent with every other campaign here.

Threshold **T-PC1** records the verdict. Threshold **T-PC2** records whether `Delta` also exceeds the
falsification bar `0.005533`.

## §PC.6 What this experiment cannot establish

- **Not an ablation of Stage C.** Three things vary at once (§PC.2). No component attribution follows.
- **Not a reproduction claim for the published number.** Our MT is trained here, on this stack, with
  cuDNN determinism; agreement with `0.6984` would be reassuring and disagreement would not by itself
  indicate an error.
- **One architecture.** SINet only. Whether SINet-v2's harness can resolve the same effect is not
  measured, and a DETECTED result on SINet will not be stated as though it covered both.
- **A DETECTED result does not validate the nulls' magnitude.** It establishes that effects of roughly
  `0.015` are visible. It says nothing about whether effects of `0.005` would be.
- **Seed-level determinism** is reduced, not eliminated, exactly as disclosed for the other campaigns.

## §PC.7 Provenance

Writes only under `rebuild/PC/out/` and `Snapshot/PC/`. Touches no committed A/B/C or T2 artifact;
`rebuild/ABC/abc_train.py` is **not modified** — its `cmd_for()` hardcodes `--method ours
--iteration 2` and remains frozen. `pc_train.py` imports `rebuild/ABC/abc_common.py` read-only for run
ids, pool paths and the scorer. Emits `EXP PC` blocks to `results/REBUILD_LOG.txt`.

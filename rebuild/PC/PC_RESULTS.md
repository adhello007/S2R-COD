# PC_RESULTS.md — the positive control

**Status: COMPLETE. Verdict DETECTED on both endpoints, 3/3 sign-consistent.
The harness resolves an effect of `+0.0197` at a bar of `0.0060` — `3.3x` threshold.**

Authoritative blocks: `EXP PC` #1 (run accounting) and #2 (verdict) in `results/REBUILD_LOG.txt`.
Those blocks are authoritative; this file is a reading of them. If the two disagree, the log wins.

Rule frozen in `PREREGISTRATION_PC.md` at commit `c2114af`, **before `pc_train.py` existed and before
a single mean-teacher run was launched**. Nothing in §PC.5 was altered after a number existed.

---

## 1. Why this experiment exists

Across 36 committed training runs — 24 in the A/B/C campaign and 12 in the falsification campaign —
**no gap anywhere clears its bar**. Every verdict is WITHIN NOISE.

The falsification arms are a strong *negative* control: they show the harness does not manufacture
differences where none exist. They cannot show it detects differences that do exist. Without that,
every null in this work is ambiguous between two readings:

1. the effect is absent or smaller than the bar, or
2. **the harness cannot resolve effects of this size at all**, in which case we are measuring the
   instrument rather than the method.

Nothing committed distinguished these. This experiment does.

## 2. Design, and what it is a control on

SINet, `MyTrain.py --method mean_teacher`, seeds `{42, 43, 45}`, base pool 4447 (arm A0's pool, copied
by hard link so no committed pool was opened for writing). `MyTrain.py:249-251` forces `--iteration 1`
for any non-`ours` method, so the mean-teacher arm is single-round by construction; that is recorded,
not chosen. C10 enters **re-scored, never re-trained**.

**This is a control on instrument sensitivity, not an ablation.** C10 differs from MT in method, in
round count and in pool size simultaneously. No component attribution follows from it, and none is
made anywhere in this document or in the paper.

**Gate G-PC1**, run before any PC number existed: the scorer reproduced B1's committed values on the
committed `Result/SINet/S2C` predictions — `Sα 0.717216` (Δ `3.77e-07`) and `MAE 0.074463`
(Δ `2.32e-07`), against a `1e-5` tolerance. The evaluation path is the same one every committed
campaign used.

## 3. The result

*`σ̂` pooled within-arm over `{MT, C10}`, df = 4. Paired differences are per seed.*

| endpoint | MT mean (sd) | C10 mean (sd) | Δ(C10−MT) | 2σ̂ | Δ / bar | sign | verdict |
|---|---|---|---|---|---|---|---|
| **COD10K-test** *(primary)* | **0.698767** (0.001120) | **0.718481** (0.004059) | **+0.019713** | **0.005954** | **3.31×** | **3/3** | **DETECTED** |
| NC4K *(secondary)* | 0.749659 (0.003089) | 0.769013 (0.003240) | +0.019354 | 0.006331 | 3.06× | 3/3 | DETECTED |

**Per-seed, COD10K-test `Sα`:**

| seed | MT | C10 | paired Δ |
|---|---|---|---|
| 42 | 0.699633 | 0.717165 | **+0.017532** |
| 43 | 0.699167 | 0.723034 | **+0.023867** |
| 45 | 0.697503 | 0.715243 | **+0.017740** |

**Thresholds.**

| Threshold | Measured | Verdict |
|---|---|---|
| G-PC1 — scorer reproduces B1 before any PC number | Δ `3.77e-07` / `2.32e-07` | **PASS** |
| T-PC1 — Δ > 2σ̂ and sign 3/3 on the primary endpoint | `+0.019713` vs `0.005954`, 3/3 | **PASS — DETECTED** |
| T-PC2 — Δ also exceeds the frozen falsification bar `0.005533` | `+0.019713`, `3.56×` | **PASS** |

## 4. What this establishes, and the gap it does not close

**Established.** The harness resolves a real effect of roughly `0.020` in `Sα`, on two endpoints, with
consistent sign across all three seeds, using the same scorer, endpoint and decision rule as every
null in this work. The instrument is not blind.

**Not established, and this is the load-bearing limit.** The nulls in this paper concern effects near
`0.005`. This experiment demonstrates detection at `0.0197`, roughly **four times** that. It does
**not** show that an effect of `0.005` would be visible, and no such claim is made. In fact the
arithmetic runs the other way and should be stated plainly: the positive control's own bar
(`0.005954`) is **larger than** the campaign's decisive gap `Δ(C10−B) = 0.005034`, so an effect of
that size would not have cleared this pooling either. **A positive control at `0.020` licenses "the
instrument works", not "the instrument would have seen the effect we are nulling".**

**Also not established.**

- **Not an ablation of Stage C.** Three things vary at once (§2). No component attribution follows.
- **One architecture.** SINet only; whether SINet-v2's harness resolves the same effect is unmeasured.
- **Not a reproduction claim.** Our MT is trained here, on this stack, with cuDNN determinism.
- **Seed-level determinism** is reduced, not eliminated, exactly as disclosed for the other campaigns.

## 5. Two observations worth recording

**(a) Our mean teacher lands on the published figure, and below this repository's own reproduction of
it.** Measured `0.698767`, against a published `0.6984` — a difference of `0.0004` — and against this
repository's own MT reproduction of `0.7030`, which sits `0.0042` above ours. We tuned nothing toward
either; the agreement with the published value is independent and is reported as an observation, not
as a reproduction claim.

**(b) The measured effect exceeds both reference gaps.** `Δ = 0.019713` against this repository's
reproduction gap of `0.0142` (MT `0.7030` → Ours `0.7172`) and the published gap of `0.0152`
(`0.6984` → `0.7136`). Ours is larger mainly because our MT is lower than the repository's MT
reproduction while our C10 (`0.718481`) sits slightly above its Ours (`0.7172`). This is reported
because it is the honest accounting; no claim of improvement over the published method is made or
intended, and C10 is not the published configuration under a matched protocol.

## 6. Provenance and one disclosure

`rebuild/PC/PREREGISTRATION_PC.md` (frozen at `c2114af`) · `rebuild/PC/pc_train.py` ·
`rebuild/PC/pc_evaluate.py` · `EXP PC` blocks #1 and #2 in `results/REBUILD_LOG.txt` · artifacts
`rebuild/PC/out/pc_verdict.json`, `rebuild/PC/out/pc_metrics.csv`. `rebuild/ABC/abc_train.py` was
**not modified** and remains frozen.

**Disclosure on block order.** The verdict was first computed in a `--no-log` pass, and block #1 (run
accounting) was appended afterwards, so the two blocks do not appear in the order the work was done.
No value differs between the passes: scoring is deterministic over fixed checkpoints and fixed
predictions, the decision rule was frozen at `c2114af` and was not touched, and no threshold was
added, removed or re-pointed after seeing a number. Recorded here rather than left for a reader to
notice from the timestamps.

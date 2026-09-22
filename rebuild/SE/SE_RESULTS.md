# SE_RESULTS.md — the seed-expansion campaign

**Setup document:** [`PREREGISTRATION_SE.md`](PREREGISTRATION_SE.md), committed 2026-09-18 at
`b755aa9`, before any SE pool was built and before any SE number existed.
**Interruption record:** [`INTERRUPTION_2026-09-20.md`](INTERRUPTION_2026-09-20.md).
**Artifacts:** `rebuild/ABC/out/se/` — `abc_runs.csv`, `abc_discards.json`, `abc_preflight.json`,
`abc_pools.json`, `abc_metrics.csv`, `abc_sigma.json`, `abc_verdict.json`.
**Status:** trained 2026-09-20 03:50 → 2026-09-22 16:05; evaluated 2026-09-22 17:54, `rc=0`.
**Verdict: 16/16 cells `WITHIN NOISE`. The committed null survives.**

> **If this document and the `EXP SE` log block ever disagree, the log wins and this file is
> wrong.** Every number below is read from a committed artifact.

---

# 1. The question, in one paragraph

The revision brief asked for the primary arms to be expanded from 3 seeds to 8–10, to tighten the
decision bar. Done the obvious way, that is the one move this project's frozen rules forbid:
`PREREGISTRATION.md` says `do NOT add seeds`, and `PREREGISTRATION_T2.md` §T2.10 says seeds are not
added to break an `INCONCLUSIVE`. Those clauses are not bureaucracy. Adding seeds *after seeing a
result* lets the analyst keep sampling until the answer moves, and it destroys the error rate of
every verdict the campaign reports — including the ones the paper stands on.

So SE does not add seeds to ABC or T2. **It is a separate campaign with its own arms, its own noise
estimate, its own bar and its own verdicts**, standing beside the committed ones exactly as T2
stands beside ABC. Its eight seeds were fixed in writing before its first run, so SE is not itself
subject to optional stopping either.

---

# 2. What was run

Four arms — **B** (random), **C10** (targeted), **CSHUF** (signal destroyed), **CINV** (signal
reversed) — at eight seeds {42, 43, 45, 46, 47, 48, 49, 50}, on two architectures. 64 cells.

| | cells | what happened |
|---|---|---|
| committed seeds {42, 43, 45} | 24 (12 per architecture) | **re-scored, not re-trained** |
| new seeds {46, 47, 48, 49, 50} | 40 | **trained from scratch for SE** |

The committed cells are re-scored rather than retrained on purpose: §SE.1 requires them to
reproduce `rebuild/ABC/out/abc_metrics.csv` and `out/t2/abc_metrics.csv` to 6 decimal places, or SE
halts. That makes the old and new halves of SE commensurable by construction instead of by
assumption.

A0 and A2 are deliberately absent. Neither appears in any decisive gap, and A0's seed instability
is what inflated ABC's pooled bar in the first place.

---

# 3. Execution record

| | |
|---|---|
| launched | 2026-09-20 03:50:23, chained behind the OR→FX chain |
| **host power loss** | 2026-09-20, last driver entry 14:30:53 |
| host returned | 2026-09-21 08:52, nothing running |
| resumed | 2026-09-21 12:35:20, `bash rebuild/SE/se_resume.sh` |
| training complete | **2026-09-22 16:04:53**, driver `rc=0` |
| scoring started | 2026-09-22 16:04:53 |

**The power loss cost two runs and no rules.** `SINet_CSHUF_s48` and `SINet_CSHUF_s49` were killed
part-way through round 1; the driver discarded both on its own pre-launch check
(`snapshot dir already holds .pth`) and re-ran them from scratch. They are the only two entries in
`abc_discards.json`. No partially trained model can enter the scoring pool, no seed was added or
dropped, and no SE number existed at the moment resumption was decided — `abc_metrics.csv` was
absent, so nothing had been computed and nothing had been seen. The full damage assessment is in
`INTERRUPTION_2026-09-20.md`; the cost was about 3.5 GPU-hours.

**Cost of the campaign.** 4556 GPU-minutes = **75.9 GPU-hours** across the 40 trained runs, run two
at a time on the two RTX PRO 6000 cards, so roughly 38 hours of wall clock. With SE's 40 runs the
project now stands at **103 trained runs**: ABC 24, T2 12, PC 3, OR 6, FX 18, SE 40.

| architecture | runs | mean wall | range |
|---|---|---|---|
| SINet | 20 | 105.9 min | 105.3 – 106.5 |
| SINet-v2 | 20 | 121.9 min | 121.2 – 122.7 |

The spread is under 1.5 minutes per architecture across 20 runs, which is worth recording only
because it makes the schedule verifiable: every run did the same amount of work.

---

# 4. What the training half establishes

Every one of the 40 runs passed the driver's `verify_run` gate, which is not a return-code check.
It reads the training log for two completed rounds, the expected step count, the final epoch, the
presence of `Tea_epoch_best.pth`, the round-1 pool size, and the two 4040-image target loads.

- **40/40 verified**, `abc_runs.csv` holds 64 rows.
- **`total_step` pinned and measured per run** — 253 (SINet) and 127 (SINet-v2) in both rounds of
  every run, so SE inherits the committed schedule exactly and is not silently an FX-style
  experiment.
- **Every run read the unfiltered 4040-image target set in both rounds.**
- **No run abandoned.** Two discarded, both re-run, both from the power loss.

**`n_appended` differs by arm by construction and is reported rather than absorbed.** CLS selects
target images with each arm's *own* round-1 model, so each arm appends a different number of
differently-pseudo-labelled images:

| arm | mean `n_appended` | range |
|---|---|---|
| B | 1977 | 1817 – 2090 |
| C10 | 2025 | 1838 – 2259 |
| CSHUF | 1990 | 1859 – 2106 |
| CINV | 1979 | 1869 – 2149 |

This is legitimately part of "closed-loop", and it is a second place the arms differ beyond the
Stage C injection. It is high-variance, and at n = 8 it is better characterised than it was at
n = 3. `total_step` stays pinned regardless, which is asserted per run.

**The scorer was validated before it was allowed to score anything new.** It reproduces B1's
committed `S_α` and MAE to within 4e-7 and 3e-7 respectively, and the evaluator halts if it does
not.

---

# 5. The rule, as committed

Restated compactly; `PREREGISTRATION_SE.md` §SE.1 governs and this is not a re-derivation of it.

**Primary endpoint** COD10K-test, `S_α`, `Tea_epoch_best.pth`, final round. NC4K secondary and
reported only.

**Bar** `σ̂_SE` = pooled within-arm sd of `S_α` over the four arms, per architecture, per endpoint,
df = 4 × 7 = 28. SE's own bar, not swapped for a committed one in either direction, whichever is
smaller.

**Gaps** Δ₁ = C10 − B (targeting vs random) · Δ₂ = C10 − CSHUF (signal vs destroyed) ·
Δ₃ = C10 − CINV (signal vs reversed) · Δ₄ = CSHUF − CINV (is direction ordered at all).

**Bands**

```
REAL EFFECT      Δ >  2σ̂_SE  AND sign consistent ≥ 7/8 seed-paired differences
WITHIN NOISE    |Δ| ≤ 2σ̂_SE
REAL REGRESSION  Δ < -2σ̂_SE  AND sign consistent ≥ 7/8
INCONCLUSIVE    |Δ| >  2σ̂_SE but sign not ≥ 7/8  →  report as-is, ADD NO SEEDS
```

The 7/8 threshold is **stricter** than the committed 3/3 rule, not looser: 3-of-3 has one-sided
probability 0.125 under a fair coin, 7-or-more-of-8 has 9/256 = 0.035.

At n = 8 a paired t-test, a Welch test, 90% and 95% intervals and a TOST at δ = 0.005 are all
reported — and all marked non-decisional. The verdict remains the 2σ̂_SE rule. That clause exists so
the statistics cannot be promoted into the decision after the fact.

---

# 6. The verdict

**All sixteen gaps are `WITHIN NOISE`.** Four gaps × two architectures × two endpoints, decided by
the 2σ̂_SE rule committed on 2026-09-18. Read from `abc_verdict.json`, generated 2026-09-22
17:54:19 at commit `9a8d1a0`.

The scorer re-validated at the start of the run: `S_α` 0.7172156 and MAE 0.0744632 against B1's
committed values, `passed: true`.

## 6.1 The decisive gap

| | Δ(C10 − B), SINet, COD10K | bar | |
|---|---|---|---|
| ABC, committed, n = 3 | **+0.00503** | 0.01793 | `WITHIN NOISE` |
| **SE, n = 8** | **+0.00235** | 0.00686 | **`WITHIN NOISE`**, 0.34× bar, sign 6/8 |

**The gap itself moved.** It is now **less than half** what the committed campaign measured, and it
sits at about a third of SE's bar. It is also within noise against *T2's* committed bar of 0.00553
— the tightest bar this project has — which it was not at n = 3, where it sat at 0.91× of it.

## 6.2 All sixteen gaps

Δ₁ = C10 − B · Δ₂ = C10 − CSHUF · Δ₃ = C10 − CINV · Δ₄ = CSHUF − CINV. All `WITHIN NOISE`.

| cell | bar 2σ̂ | Δ₁ | Δ₂ | Δ₃ | Δ₄ |
|---|---|---|---|---|---|
| SINet · COD10K *(primary)* | 0.00686 | +0.00235 (0.34×, 6/8) | +0.00031 (0.05×, 3/8) | −0.00211 (0.31×, 4/8) | −0.00242 (0.35×, **7/8**) |
| SINet · NC4K | 0.00592 | +0.00034 (0.06×, 4/8) | +0.00068 (0.12×, 5/8) | −0.00305 (0.52×, 5/8) | −0.00374 (0.63×, **8/8**) |
| SINet-v2 · COD10K | 0.01014 | −0.00109 (0.11×, 5/8) | −0.00333 (0.33×, 5/8) | −0.00348 (0.34×, 6/8) | −0.00015 (0.01×, 5/8) |
| SINet-v2 · NC4K | 0.00935 | −0.00095 (0.10×, 4/8) | −0.00234 (0.25×, 5/8) | −0.00426 (0.46×, **7/8**) | −0.00191 (0.20×, 5/8) |

No gap reaches even two-thirds of its bar. The three cells that clear the 7/8 sign threshold do not
clear the magnitude threshold, so the band is `WITHIN NOISE` in every case — the rule requires both.

## 6.3 The bar did not tighten as projected, and this matters

§SE.1 projected that n = 3 → n = 8 would tighten the bar by √(8/3) = 1.63×, *"if the per-arm spreads
stay as measured"* — putting it near 0.0034 against T2's 0.0055. **They did not stay as measured.**

| cell | ABC bar | T2 bar | **SE bar** | SE vs T2 |
|---|---|---|---|---|
| SINet · COD10K | 0.01793 | 0.00553 | **0.00686** | 1.24× **wider** |
| SINet · NC4K | 0.00831 | 0.00551 | **0.00592** | 1.07× wider |
| SINet-v2 · COD10K | 0.01226 | 0.00639 | **0.01014** | 1.59× wider |
| SINet-v2 · NC4K | 0.01053 | 0.00556 | **0.00935** | 1.68× wider |

Every per-arm sd grew. On SINet · COD10K: B 0.00181 → 0.00251, C10 0.00406 → 0.00489,
CSHUF 0.00166 → 0.00278, CINV 0.00285 → 0.00302.

**This is the expected behaviour of a variance estimate at n = 3, not a defect of SE.** A pooled sd
on df = 8 is a noisy estimate that lands low as often as high; SE's rests on **df = 28**. So SE did
not buy a tighter bar — it bought a *trustworthy* one, and the honest statement is that the
committed 3-seed bars were optimistic rather than conservative.

**Which makes the result stronger than the projected branch would have been.** The feared outcome
was a bar tightening to 0.0034 under a gap holding at 0.0050, forcing withdrawal of the central
claim. What happened instead is that the bar widened slightly on 3.5× the degrees of freedom *and*
the gap halved. The null holds comfortably rather than marginally, and it holds on the best noise
estimate the project has.

## 6.4 CINV has the highest mean in 4 of 4 cells

| cell | B | C10 | CSHUF | **CINV** |
|---|---|---|---|---|
| SINet · COD10K | 0.71513 | 0.71748 | 0.71717 | **0.71959** |
| SINet · NC4K | 0.76802 | 0.76836 | 0.76768 | **0.77141** |
| SINet-v2 · COD10K | 0.69627 | 0.69517 | 0.69850 | **0.69865** |
| SINet-v2 · NC4K | 0.74998 | 0.74903 | 0.75138 | **0.75329** |

**CINV deliberately reverses the uncertainty signal — it aims the budget at the clusters the score
says are least uncertain — and it has the highest mean `S_α` in every cell.** T2 saw this at n = 3
in 3 of 4 cells; at n = 8 it is 4 of 4. C10, the targeted arm, is *below* random on both SINet-v2
cells.

Every one of these differences is within noise and **none of them is a claim that reversing the
signal helps.** What they rule out is the opposite: there is no ordering by signal direction here
to be found. Δ₄ (CSHUF − CINV) carries the strongest sign consistency in the campaign — 8/8 on
SINet · NC4K, 7/8 on SINet · COD10K — and still does not reach two-thirds of its bar.

This is the concentration-not-targeting thesis showing up in trained accuracy at n = 8: all four
arms concentrate the budget, and which way the budget points does nothing the instrument can see.

---

# 7. What this changes in the paper

**The branch we are in.** §SE.1's first interpretation clause: *"Δ₁ WITHIN NOISE at the tighter bar
→ the committed null survives … the sentence 'this campaign resolved coarsely' must be rewritten
against SE's bar rather than deleted."* The central claim stands. The title stands. Nothing is
withdrawn.

**But the clause's premise was wrong, and the rewrite must say so.** It assumed SE's bar would be
tighter. SE's bar is *wider* than T2's on all four cells (§6.3). The power qualification therefore
does **not** narrow the way the pre-registration anticipated, and writing that it does would be
reporting a projection instead of a measurement. What actually improved is different and better:

- the noise estimate now rests on **df = 28** instead of df = 8, so the bar is trustworthy rather
  than small, and the committed 3-seed bars are revealed as optimistic;
- **the decisive gap halved**, +0.00503 → +0.00235, and is now within noise even against T2's
  tighter committed bar;
- **no gap in the campaign reaches two-thirds of its bar**, on 8 seeds and 4 arms.

The paper's scope sentence should be rewritten against SE's numbers: *no effect above about 0.007
`S_α` on the primary cell, measured on 8 seeds per arm with df = 28*. That is a weaker-sounding
bound than the projected 0.0034 and a considerably more defensible one.

**Three objections, three answers, none of them in the draft.** SE answers *"three seeds is not
enough"*, alongside **OR** (*"you picked a bad uncertainty estimator"*) and **FX** (*"your added
data displaced rather than augmented"*). None of the three appears in `main_v2.tex`. All three
belong in §4 as a table row and a paragraph each, per
[`../FinalPaper/SCOPING_ANALYSIS.md`](../FinalPaper/SCOPING_ANALYSIS.md) §4.

**§6.4 belongs in the concentration section, not here.** CINV holding the highest mean in 4 of 4
cells at n = 8 is the trained-accuracy form of the concentration-not-targeting thesis, and it
strengthens the same argument that the boundary-metric result makes (SCOPING_ANALYSIS §F5). It is
evidence *for* the paper's positive result, not a curiosity about a control arm.

**Reported beside, never instead.** Per §SE.0, the committed 3-seed verdicts are not restated,
recomputed, replaced or re-decided. SE agrees with them, so no disagreement has to be adjudicated —
but the agreement is reported as two campaigns concurring, not as one confirming the other.

**Project total: 103 trained runs** — ABC 24, T2 12, PC 3, OR 6, FX 18, SE 40 — of which SE's 40
are the largest single campaign. The paper currently claims 24 in one place and 36 in another.

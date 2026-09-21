# FX_RESULTS.md — the optimisation-schedule control

**Setup document:** [`PREREGISTRATION_FX.md`](PREREGISTRATION_FX.md), committed 2026-09-18 before
any FX pool was built and before any FX number existed.
**Artifacts:** `rebuild/ABC/out/fx/` — `abc_metrics.csv`, `abc_runs.csv`, `abc_sigma.json`,
`abc_verdict.json`, `abc_preflight.json`.
**Status:** trained 2026-09-18 18:23 → 2026-09-20 01:53; evaluated 2026-09-20 03:49, `rc=0`.

> **If this document and the `EXP FX` log block ever disagree, the log wins and this file is
> wrong.** Every number below is read from a committed artifact.

---

# 1. The question, in one paragraph

The paper's own scope section concedes the strongest objection anyone can make to it:

> *"You fixed the number of gradient steps and then observed that adding data didn't help. That is
> a scheduling bug in your training script, not a result about synthetic data."*

That objection is about a real property of the trainer. `total_step` is pinned at **253** (SINet)
and **127** (SINet-v2) in both rounds of every committed run, no matter how big the training pool
is. FX unpins it and re-runs the campaign. **The paper could previously only concede this; now it
is measured.**

---

# 2. Why the budget was pinned — and the answer to "isn't the target set the bottleneck?"

**Your understanding is correct, and it is exactly why the pin exists.** Writing it out properly,
because the mechanism is the whole point of this experiment.

Each training step needs **two** batches at once:

| | comes from | used for |
|---|---|---|
| a **source** batch (image + mask) | the labelled pool, 4447 or 5447 images | the supervised loss |
| a **target** batch (weak + strong view) | the unlabelled real pool, **4040 images** | the student–teacher consistency loss |

The trainer pairs them with `zip(source_loader, target_loader)` (`MyTrain.py:51`). **`zip` stops as
soon as the shorter iterator runs out.** The target loader holds 4040 images at batch 16 = 253
batches, and the source loader holds 5447 images = 341 batches. So the epoch ends at step 253, and
the last 88 source batches are simply never reached.

That is the pin, and it has a consequence the paper leans on:

```
committed schedule, SINet, C10 pool of 5447:
   253 steps x batch 16  =  4048 source images consumed per epoch
   4048 / 5447           =  0.743 exposures per source image per epoch
```

Adding Stage C's 1000 generated images to a 4447-image pool **does not buy any extra training**.
It spreads the same 4048 image-slots over more images, so every image — real and synthetic alike —
is seen *less*. The added images **displace** rather than **augment**.

### So how does FX get past it?

**Not by acquiring more real target images.** There are still only 4040. FX **wraps** the target
loader so it never runs out:

```python
def _cycle(loader):
    while True:
        for b in loader:
            yield b

batches = zip(source_loader, _cycle(target_loader))     # PATCH P6
```

Now `zip` stops when the **source** loader runs out, and the target loader restarts as often as
needed. The source pool decides the epoch length:

```
FX schedule, SINet, C10FX pool of 5447:
   341 steps x batch 16  =  5456 source images consumed per epoch
   5456 / 5447           =  1.002 exposures per source image per epoch
```

Every source image is now seen exactly once per epoch, and adding 1000 images buys 88 extra
gradient steps per epoch rather than nothing.

### The price, stated plainly

**We did not get more real images. We re-used the ones we had.** Those same 5456 steps consume 5456
target samples from a pool of 4040:

| schedule | arch | steps/epoch | source seen / epoch | **target seen / epoch** |
|---|---|---|---|---|
| pinned (committed) | SINet, 5447 pool | 253 | 0.743 | 1.002 |
| **FX** | SINet, 5447 pool | **341** | **1.002** | **1.350** |
| pinned | SINet, A0's 4447 pool | 253 | 0.910 | 1.002 |
| **FX** | SINet, A0FX's 4447 pool | **278** | **1.000** | **1.101** |
| pinned | SINet-v2, 5447 pool | 127 | 0.746 | 1.006 |
| **FX** | SINet-v2, 5447 pool | **171** | **1.005** | **1.354** |

So under FX each of the 4040 real target images is seen about **1.35 times per epoch** instead of
once. Two things soften that and one does not:

- Both loaders use `shuffle=True` (`Dataloader.py:200,211`), so each wrap of the target set is a
  **fresh shuffle** — repeats are not served in the same order or paired with the same source batch.
- The **strong** view is stochastic (`RandomAutocontrast`, `GaussianBlur`), so a repeated target
  image gives the student a genuinely different input.
- But the **weak** view is deterministic (resize → tensor → normalise). **A repeated target image
  gives the teacher a byte-identical input**, so within one epoch the consistency loss is computed
  against the same teacher target more than once for ~35% of the draws.

This was declared in advance: `PREREGISTRATION_FX.md` §FX.2.3 lists *"more target-image views per
epoch"* as one of four things the schedule change bundles together. **FX identifies the schedule as
a whole, not the step count in isolation**, and no claim here separates them.

### The thing this does *not* fix, which matters most

It is tempting to conclude the pin invalidated the decisive comparison. **It did not**, and FX was
not run on that premise. B and C10 hold **identical pool sizes** (5447), so they received identical
step counts under *both* schedules — 253 each before, 341 each now. **The pin was never an asymmetry
between them.** What it changed is whether Stage C's images were trained on or merely substituted
in. That is worth testing, but it is a different claim from "the pin hid an effect."

---

# 3. What was actually trained

**Three arms**, each with a pool **byte-identical** to the committed arm it mirrors — same stems,
same provenance, same per-seed draw for B. The *only* difference from the committed runs is the
`--exposure fixed_exposures` flag.

| Arm | mirrors | pool | round-1 steps (SINet / v2) |
|---|---|---|---|
| `A0FX` | A0, unpadded baseline | 4447 | 278 / 139 |
| `BFX` | B, 1000 random renders | 5447 | 341 / 171 |
| `C10FX` | C10, 1000 targeted renders | 5447 | 341 / 171 |

**Everything else is the committed protocol, unchanged:**

- **Architectures:** SINet (batch 16, 40 epochs) and SINet-v2 (batch 32, 100 epochs)
- **Seeds:** {42, 43, 45} — the committed set, so every FX run is seed-paired with a committed run
- **Rounds:** 2. Round 1 trains on the arm's pool; CLS appends pseudo-labelled target images; round 2
  rebuilds both models from ImageNet init and trains on the enlarged pool
- **Endpoints:** COD10K-test primary, NC4K secondary (reported, never decides); best teacher
  checkpoint, final round
- **Optimiser:** Adam at 1e-4, 352×352, EMA momentum 0.996 — all untouched
- **18 runs** (3 arms × 2 architectures × 3 seeds)

**Wall clock: 57.7 GPU-hours**, mean 192 min/run — SINet 138–169 min, SINet-v2 158–282 min. The
committed runs averaged ~107 and ~127 min, and FX runs are longer by roughly the step ratio, which
is what the manipulation predicts.

### Round 2 grows too, and by more

CLS appends pseudo-labelled target images between rounds, so round 2's pool is larger again and its
step count larger with it:

| Arm | round-1 steps | round-2 steps | `n_appended` |
|---|---|---|---|
| `A0FX` SINet | 278 | 390–400 | 1785–1947 |
| `BFX` SINet | 341 | 467–475 | 2019–2145 |
| `C10FX` SINet | 341 | 455–474 | 1824–2065 |

Only the **round-1** count is asserted, because only it is predictable in advance from the pool
size. Round 2's is recorded and reported. `n_appended` varies 1601–2145 across runs — the
pseudo-label filter is a second uncontrolled channel, disclosed for ABC and T2 and inherited here
unchanged.

### The gate that proves the manipulation happened

`PREREGISTRATION_FX.md` §FX.2.6 declares **FX-C**: a run whose round-1 step count equals the
*pinned* value is a HALT, not a result, because it would mean the flag never took effect.

**All 18 runs passed.** Observed round-1 counts were exactly 278 / 341 (SINet) and 139 / 171
(SINet-v2); the pinned 253 / 127 appear nowhere. Pool integrity also held: `overlap_C10|C10FX`
came back at Jaccard **1.0000**, `n_differing = 0` — the FX pool is its base arm's pool exactly.

---

# 4. Results

`σ̂` is pooled within-arm across {A0FX, BFX, C10FX} at df = 6, per architecture and endpoint — FX's
own bar, not swapped for any committed one.

## 4.1 Arm means, COD10K-test `S_alpha`

| Arch | A0FX | BFX | C10FX | bar 2σ̂ |
|---|---|---|---|---|
| SINet | 0.699292 | 0.711298 | **0.712739** | 0.011649 |
| SINet-v2 | 0.690387 | 0.689094 | 0.688411 | 0.010007 |

## 4.2 The verdicts

| Arch / endpoint | Δ(C10FX−BFX) **the decisive gap** | Δ(BFX−A0FX) | Δ(C10FX−A0FX) |
|---|---|---|---|
| SINet / COD10K | +0.001440 2/3 · **WITHIN NOISE** | +0.012006 2/3 · INCONCLUSIVE | +0.013446 2/3 · INCONCLUSIVE |
| SINet / NC4K | +0.002280 2/3 · WITHIN NOISE | +0.004955 2/3 · WITHIN NOISE | +0.007235 2/3 · WITHIN NOISE |
| SINet-v2 / COD10K | −0.000683 1/3 · WITHIN NOISE | −0.001293 2/3 · WITHIN NOISE | −0.001976 1/3 · WITHIN NOISE |
| SINet-v2 / NC4K | −0.000305 1/3 · WITHIN NOISE | +0.002005 2/3 · WITHIN NOISE | +0.001699 2/3 · WITHIN NOISE |

**The decisive gap is WITHIN NOISE in all four cells**, at 0.12×, 0.21×, 0.07× and 0.03× of its bar.

Two **INCONCLUSIVE** verdicts on SINet/COD10K: both exceed the 0.0116 bar but are only 2/3
sign-consistent. Under the frozen rule that is reported as-is and **no seeds are added**.

## 4.3 The gap got *smaller*, not larger

The comparison FX exists to make — the same decisive gap under each schedule, COD10K:

| Arch | pinned (committed) | fixed exposures (FX) |
|---|---|---|
| SINet | +0.005034 | **+0.001440** |
| SINet-v2 | −0.000399 | −0.000683 |

**Removing the dilution confound shrank the targeting gap by 3.5× on SINet.** If the pin had been
hiding a real effect, this is where it would have appeared. It did the opposite.

## 4.4 What the schedule itself was worth

Δ = FX minus committed, same arm, same seeds (`FX.1` Δ₃/Δ₄/Δ₅):

| Arch / endpoint | A0→A0FX | B→BFX | C10→C10FX |
|---|---|---|---|
| SINet / COD10K | −0.001658 | −0.002149 | −0.005742 |
| SINet / NC4K | −0.003231 | −0.007057 | −0.006886 |
| SINet-v2 / COD10K | +0.001241 | −0.005975 | −0.006259 |
| SINet-v2 / NC4K | −0.001662 | −0.003860 | −0.005112 |

**11 of 12 cells are negative.** Growing the optimisation budget by 35% made every arm slightly
*worse*, not better.

The most likely reason is disclosed in §FX.2.4 and was a deliberate design choice: `adjust_lr`
decays on an **epoch** counter, and the epoch count was held at the committed 40 / 100. FX arms
therefore take *more steps at each learning rate* rather than traversing the schedule faster.
Rescaling the decay would have re-imposed a fixed budget and defeated the control. **This is a
plausible mechanism, not a measured one** — no experiment here separates "more steps" from "more
steps at an unrescaled learning rate."

---

# 5. What this establishes, and what it does not

## Established

**The targeting null survives removal of the dilution confound.** When Stage C's 1000 images are
genuinely trained on instead of displacing base-pool exposure, targeted allocation still does not
beat random allocation at any resolvable level — on either architecture, on either endpoint. And
the gap moved *toward* zero.

**This retires a concession.** The paper currently says:

> *"nothing here measures what happens when the optimisation budget grows with the data, which is
> the largest open question this paper creates."*

That sentence is now false and `PREREGISTRATION_FX.md` pre-committed to deleting it. The first
setup-specific limitation moves from **conceded** to **measured**. A reviewer can no longer dismiss
the null as a scheduling artifact — and cannot do so with hindsight either, because the replacement
wording was fixed before the runs.

**A hint about pool size, not about targeting.** The two INCONCLUSIVE gaps on SINet/COD10K both
involve A0FX, the unpadded arm, at +0.0120 and +0.0134. Read cautiously, *padding the pool* may help
once the budget grows with it. That is a claim about **how many** images, not **which** ones, and it
is exactly the arm the committed campaign already flagged as its least stable. It is reported
because it points away from our conclusion, not toward it.

## Not established

- **Not "more optimisation doesn't help."** The negative cross-schedule deltas are confounded with
  the unrescaled learning-rate schedule. What we measured is *this* schedule change, as a package.
- **Not "the pin never mattered."** It mattered for what adding data *means*; it just never created
  an asymmetry between B and C10.
- **Not a resolution of the A0 comparison.** Two INCONCLUSIVE verdicts are reported as inconclusive.
  No seeds were added to break them, per the frozen rule.
- **Not zero.** WITHIN NOISE means **no effect resolvable at this sensitivity**, never no effect.
  §FX.2.8 requires naming what the bar could have missed: on SINet/COD10K the bar is 0.0116, so an
  effect up to roughly that size would not have been seen. FX resolves effects of T2's order, not
  smaller ones.
- **Four factors moved together.** Steps, EMA updates, consistency evaluations and target-view
  repetition all scale with the schedule (§FX.2.3). No claim here attributes the outcome to any one
  of them.

## How it fits with the other controls

FX is the second of three independent attacks on the null, and all three now point the same way:

| Objection | Campaign | Outcome |
|---|---|---|
| *"Your uncertainty score was bad"* | **OR** | A perfect score — true endpoint error — also does nothing. All 8 cells WITHIN NOISE. |
| *"You never really trained on the added data"* | **FX** | When you do, the gap **shrinks**. All 4 cells WITHIN NOISE. |
| *"n = 3 is too few"* | **SE** | In progress, n = 8. |

Two of the three most natural dismissals of this paper have now been tested and neither holds.

# A3 — Verified results

**Status: COMPLETE. 14 of 15 declared thresholds PASS; the 1 FAIL is a correction to A3's own
threshold design, and it is left failing rather than repaired.**
**Old claims re-tested: 18 MATCH, 4 NEW, 1 SUPERSEDED, 1 NOT-REPRODUCIBLE — and 0 MISMATCH.**

Source of every number below: `results/REBUILD_LOG.txt`, block **`EXP A3`** timestamped
`2026-09-08T10:34:47+05:30`, commit `8a7a15d`. That block is authoritative; this file is a reading of
it. If the two ever disagree, the log wins.

**Traceability, checked mechanically rather than by eye.** Every numeric token in this file was
matched against the log block and the seven artifacts it names: all resolve, 15 of them as roundings
of full-precision CSV entries (e.g. the quoted MMD² `0.000054` against the stored `0.000053922`). The
only figures *not* drawn directly from a logged value are five **ratios** computed in this file from
two logged values each — flagged inline where they appear, because arithmetic performed in a document
rather than by a script is a defect this rebuild has already recorded once (`REVISION_TABLE.md` R4).

Setup and pre-declared thresholds: `rebuild/A3/A3.md`, fixed before the run. Scoping decisions:
`rebuild/A3/A3_SCOPING.md`. Environment: py3.12.3, torch 2.11.0+cu128, CUDA 12.8, timm 1.0.28,
numpy 2.5.2, 2× RTX PRO 6000 Blackwell, seed 0. **Trains a model: NO** — frozen-inference feature
extraction plus logistic probes on frozen features; no optimizer ran and no checkpoint was written.

---

## 0. The result in one paragraph

The old package's A3 reproduces almost completely — **18 of its pinned values re-test clean and none
mismatches**, including the headline AUC, the JPEG-75 floor, the recall pair, and every pixel
statistic to six decimals. What does not survive is the **framing**. The quality sweep the original
never ran shows that re-encoding the *identical* target images at JPEG-30 separates them from
themselves at **0.9928** in `clipL224` — above `REBUILD_PLAN`'s declared 0.90 vacuity trigger, above
*both* genuine real-vs-real controls, and within **0.007** of the real-vs-LAKE-RED headline. On those
same floors MMD² is **≈ 0**. So AUC was never measuring distributional distance, and the declared
vacuity flag fired. Meanwhile the metric declared as the decision *before* the run — the paired
coverage delta — passes in **3 of 3** embedder spaces for **both** synthetic pools, at 24–83 %
relative loss. **The finding survives; the metric that used to carry it does not.**

---

## 1. What was measured

### 1.1 The headline, and the number that inoculates it

Held-out linear-probe AUC, stratified 70/30, whole images (`R1-full`), CLS token, L2 at use time.

| embedder | vs **authors' pool**<br>(what `MyTrain.py` reads) | vs **local renders**<br>(what ABC added) | **COD10K 3040 vs CAMO 1000**<br>*inside the target set* |
|---|---|---|---|
| `dinoL224` | **0.9986** | **0.9988** | **0.8648** |
| `dinoL518` | **0.9982** | **0.9980** | **0.8592** |
| `clipL224` | **0.9993** | **0.9995** | **0.9225** |

Two things follow immediately.

**The authors' pool is indistinguishable from the local pool.** Every old A3 number came from the
local re-generation; `REBUILD_PLAN.md` §5 item 5 named the authors' pool as never probed. Probed now,
it lands within 0.0006 of the local pool in all three spaces. Since E0 measured the two as genuinely
different samples of one generator (0 of 200 identical, mean maxdiff 232.3 of 255), this is an
**independent replication**, not a repeat.

**The target set separates from itself.** `Dataset/Target/Image` is a **two-dataset mixture** —
`3040 COD10K + 1000 CAMO = 4040` — and its two components separate at **0.8648 / 0.8592 / 0.9225**.
That, not chance, is the bar a 0.999 headline has to clear. The old package computed a version of
this number (0.8888), and filed it as a *bug in its own null control*. Its split was not even clean:
sorted filename order gave 2020 COD10K against 1020 COD10K + 1000 CAMO, and COD10K filenames are
ordered taxonomically, so dataset origin was conflated with taxonomy. **The clean 3040-vs-1000 probe
had never been computed.** Reproducing the old sorted split as a *labelled control* gives
**0.8975 / 0.9110 / 0.8928** (`T4` PASS).

### 1.2 The decision — the paired coverage delta

Kynkäänniemi k-NN precision/recall against the target manifold, anchor **k = 5**, declared in advance.

| embedder | raw HKU-IS<br>*(LAKE-RED's own input)* | authors' pool | local renders | **auth rel. loss** | **local rel. loss** | ceiling |
|---|---|---|---|---|---|---|
| `dinoL224` | 0.7473 | 0.4829 | 0.4668 | **−35.4 %** | **−37.5 %** | 0.9332 |
| `dinoL518` | 0.7097 | 0.4834 | 0.5421 | **−31.9 %** | **−23.6 %** | 0.9431 |
| `clipL224` | 0.7470 | 0.1277 | 0.1349 | **−82.9 %** | **−81.9 %** | 0.8931 |

**`T1`, the PRIMARY threshold, PASSES 3/3 for both pools** — the rule required ≥ 2 of 3 at ≥ 15 %
relative loss. `T2` (below ceiling in every cell) PASSES. `T10` (sign identical in all three spaces)
PASSES. The direction survives the whole `k` sweep:

| | k=3 | k=5 | k=10 | k=20 |
|---|---|---|---|---|
| authors', `dinoL224` / `dinoL518` / `clipL224` | −35.5 / −28.6 / −89.3 % | −35.4 / −31.9 / −82.9 % | −34.2 / −32.5 / −77.2 % | −30.2 / −28.6 / −68.7 % |
| local, `dinoL224` / `dinoL518` / `clipL224` | −38.8 / −20.3 / −88.4 % | −37.5 / −23.6 / −81.9 % | −34.3 / −24.6 / −71.6 % | −25.2 / −21.7 / −60.6 % |

**Why this is the one A3 number the truism cannot touch.** It is a *within-content intervention*, and
every element of that is measured rather than asserted: the same 4447 foregrounds in bijection
(`T9` asserts index-wise cache alignment at **4447/4447**); the same masks (D1 measured `raw_gt` and
`local_msk` both at **0.19132** white fraction, agreeing to five decimals); one fixed target manifold
on both sides; and only the background regenerated (E0 measured the `isReplace` split at
object-region error **6.245** against background **71.676**, a **11.5×** ratio, re-derived
independently by D2 s7 at 0.962 against 41.667). One manipulated variable, one fixed manifold.

**And the full coverage ladder answers the apples-to-oranges objection outright.** Recall at k = 5,
from `out/a3_coverage.csv`:

| set | `dinoL224` | `dinoL518` | `clipL224` | what it is |
|---|---|---|---|---|
| ceiling, random halves | 0.9332 | 0.9431 | 0.8931 | the target against itself |
| COD10K 3040 vs CAMO 1000 | 0.8898 | 0.9003 | 0.8730 | two real datasets *inside* the target |
| **NC4K** | **0.8874** | **0.8995** | **0.7921** | a genuinely **different real** camouflage set |
| raw HKU-IS | 0.7473 | 0.7097 | 0.7470 | real photographs, a **different genre** |
| **authors' pool** | **0.4829** | **0.4834** | **0.1277** | synthetic |
| **local renders** | **0.4668** | **0.5421** | **0.1349** | synthetic |

Every real set — including two whose *content* differs from the target as much as anything could —
covers the target manifold at 0.71–0.90, near the ceiling. The synthetic pools collapse to 0.13–0.54.
The objection was that raw HKU-IS is salient-object photography while LAKE-RED output is
camouflage-style renders, so their recalls measure different manifolds. The measurement says the
opposite: **raw photographs of the wrong genre still cover the target better than the synthetic
images generated from those very photographs.** Coverage discriminates where AUC cannot.

### 1.3 The full AUC ladder — and why it decides nothing

| row | role | `dinoL224` | `dinoL518` | `clipL224` |
|---|---|---|---|---|
| real vs real, RANDOM halves | true null | 0.5052 | 0.5122 | 0.4717 |
| COD10K-train−7 vs COD10K-test | second null | 0.5607 | 0.5628 | 0.5716 |
| real vs same images JPEG-90 | floor | 0.2826 | 0.3256 | 0.6266 |
| real vs same images JPEG-75 | floor | 0.4156 | 0.5564 | 0.8548 |
| real vs same images JPEG-50 | floor | 0.7401 | 0.7323 | 0.9690 |
| **real vs same images JPEG-30** | **floor** | **0.8509** | **0.7969** | **0.9928** |
| real vs same images darkened 20 | floor | 0.3501 | 0.3108 | 0.7690 |
| real target vs NC4K | cross-dataset | 0.8040 | 0.8243 | 0.9381 |
| COD10K vs CAMO | self-separation | 0.8648 | 0.8592 | 0.9225 |
| real vs real, SORTED halves | old defect | 0.8975 | 0.9110 | 0.8928 |
| real target vs raw HKU-IS | paired baseline | 0.9794 | 0.9802 | 0.9899 |
| **real target vs authors' / local** | **headline** | **0.9986 / 0.9988** | **0.9982 / 0.9980** | **0.9993 / 0.9995** |

**`T6`, the declared vacuity flag, FIRED** (`REBUILD_PLAN.md` §3-A3: *vacuity if any
identity-preserving control exceeds AUC 0.90*). In `clipL224` a JPEG-30 re-encode of the same
photographs reaches **0.9928** — above the trigger, above the self-separation control (0.9225), above
the cross-dataset control (0.9381), and 0.0067 short of the headline (0.9995). In `dinoL224` the
JPEG-30 floor (0.8509) **exceeds** the NC4K control (0.8040). In 2 of 3 spaces the floor outranks a
genuine comparison between two different real datasets.

**Only the sweep reveals this.** The original pinned a single quality and read 0.4117 as evidence that
the floor was harmless — which is exactly why its own log recorded that R-f then rested on the
cross-dataset control alone. It rests on nothing: at quality 30 the floor overtakes that control.

**The relabelling that matters.** The old A3 called `tgt` vs `raw` "two ordinary different datasets"
and leaned the surviving vacuity argument on it. `raw` is **LAKE-RED's own input pool**, so that row
is the *paired baseline*, not a generic control. Mislabelled, it both overstated the vacuity argument
and discarded the most informative comparison in the experiment: generation moves its own input
**further** from the target (0.9794 → 0.9988 in `dinoL224`).

### 1.4 MMD² — the unsaturated companion, and the mechanism behind the vacuity

Unbiased polynomial-kernel MMD² (degree 3, the KID kernel), float64 accumulation. **Descriptive; no
threshold is declared on it.**

| row | `dinoL224` | `dinoL518` | `clipL224` |
|---|---|---|---|
| true null (random halves) | −0.000000 | −0.000000 | −0.000000 |
| JPEG-90 / 75 / 50 / 30 floors | −0.000001 … 0.000005 | −0.000001 … 0.000002 | 0.000002 … 0.000054 |
| darkened 20 | −0.000001 | −0.000001 | 0.000008 |
| real target vs NC4K | 0.000024 | 0.000025 | 0.000062 |
| COD10K vs CAMO | 0.000050 | 0.000045 | 0.000113 |
| real target vs raw HKU-IS | 0.000131 | 0.000102 | 0.000294 |
| **real target vs authors' pool** | **0.000332** | **0.000233** | **0.000509** |
| **real target vs local renders** | **0.000301** | **0.000189** | **0.000488** |

This is the crispest statement of what went wrong with AUC. **A probe separates two encodings of one
photograph at 0.9928 while MMD² between them is 0.000054** — three to nine times smaller than between
two real datasets, and roughly ten times smaller than the headline. Ratios computed in this file from
the logged values: the headline sits at ≈ **6.6×** the self-separation control and ≈ **14×** the
cross-dataset control in `dinoL224`, and ≈ **2.5×** its own input pool. The ordering that AUC
compressed into the top 0.02 of its range, MMD² spreads over an order of magnitude, and it puts the
identity-preserving floors where they belong: at zero.

**Spread**, via C1's imported `spread_stats` (descriptive, no threshold). Effective rank of each pool
against the target's: authors' **188.1 / 209.5 / 88.2**, local **193.2 / 229.4 / 99.0**, raw
**243.3 / 301.1 / 111.3**, target **106.9 / 114.5 / 54.4**. Every source pool is *broader* than the
target in every space, and the synthetic pools are **narrower than the raw photographs they came
from** — consistent with the coverage loss, and measured independently of it.

### 1.5 The effect sizes — what replaces the old 4.67

Four estimators per row, each with a distinct job.

| | `dinoL224` | `dinoL518` | `clipL224` |
|---|---|---|---|
| old estimator: probe axis, **in-sample** | **4.658** | 4.300 | 5.639 |
| same logistic axis, **held out** | 4.428 | 4.068 | 5.421 |
| C1's imported mean-difference, **held out** | **+3.103** | **+2.709** | **+4.267** |
| C1's mean-difference, in-sample | +3.144 | +2.729 | +4.255 |

**The old 4.67 reproduces at 4.658**, so the supersession is not concealing a failure to reproduce.
The disqualification is a separate measurement. Run on a **true null** — two random halves of one
dataset, where by construction there is nothing to find — the estimators behave as follows:

| on the true null | `dinoL224` | `dinoL518` | `clipL224` |
|---|---|---|---|
| old estimator: probe axis, in-sample | **0.6867** | **0.6805** | **0.4854** |
| same axis, held out | 0.0318 | 0.0224 | 0.0889 |
| C1's mean-difference, held out (`T7`) | −0.0783 | −0.0716 | −0.0951 |
| C1's mean-difference, in-sample | +0.4015 | +0.4024 | +0.3031 |

The old estimator **manufactures ≈ 0.65 of *d* from nothing**, reproducing C1's independently
measured in-sample null of **+0.6991** to two decimals against its held-out **−0.1328**. `T7` PASSES:
A3's held-out null is a genuine null in all three spaces. The effect itself is large and real
everywhere; only the estimator changes.

### 1.6 Pixel statistics (secondary panel, no threshold on the values)

Ported from the original over all **4447** foregrounds and all three pools. It reproduces to six
decimals:

| metric | old package | measured |
|---|---|---|
| background luminance, real | 117.876384 | **117.876384** |
| background luminance, local render | 98.63953 | **98.63953** |
| background luminance, authors' pool | 98.529343 | **98.529343** |
| shift (local − real) | −19.24 | **−19.236854** |
| per-channel shift R / G / B | −21.33 / −22.89 / −13.49 | **−21.334249 / −22.887969 / −13.488345** |
| fg→bg colour correlation, real | −0.191 | **−0.190784** (R² 0.036399) |
| fg→bg colour correlation, local | +0.397 | **+0.396659** (R² 0.157338) |
| fg→bg colour correlation, authors' | +0.399 | **+0.399463** (R² 0.159571) |

The declared threshold — the correlation flips sign from the real photographs to **both** generated
pools — **PASSES**. Two independent generation runs land within **0.0028** of each other while the
real photographs sit on the other side of zero.

### 1.7 Preflight — every assumption the rest of A3 rests on

| check | result |
|---|---|
| E0 cache shape mismatches, over all 15 embedder × set caches A3 reads | **0** |
| E0 cache name lists identical across all three embedder spaces | **True** |
| Input directories re-digested against `e0_input_digests.csv` | **6 checked, 0 mismatched** |
| Target composition | **3040 COD10K + 1000 CAMO = 4040** |
| D2 leaked names resolved against E0's own target listing | **7/7**, all inside COD10K |
| **Pool alignment, `raw` vs `auth` and `raw` vs `local`** | **4447/4447** index-wise (`T9`) |
| NC4K ∩ COD10K-train, consumed from D2_NC4K rather than recomputed | **0/4121**, 0 pairs shortlisted |

The alignment check is not a formality: s4's headline compares row *i* of `raw` with row *i* of a
generated pool. Had the cache row orders ever diverged it would have paired different foregrounds and
the result would have looked entirely normal.

**One provenance note, stated plainly.** The final logged run reports
`fresh_embeddings_computed = 0` with `18 reused`, because the six control sets × three embedders were
written to `rebuild/A3/cache/` by an earlier `--steps s2` invocation of **this same committed
script** on the same commit. The embedding happened; the cache-hit guard then reused it, exactly as
D1/B1/C1 consume E0's caches. The guard is keyed on the loader description and input count, so a
cache written by a different loader is rebuilt rather than trusted.

---

## 2. How this changes our approach

1. **Never report a real-vs-generated AUC without an identity-preserving sweep.** A single quality
   setting is not a floor — it is one point on a curve that reaches 0.9928. The old package's single
   Q75 reading (0.4117, reproduced here at 0.4156) actively misled it into thinking the floor was
   harmless.
2. **Declare the decision on an unsaturated quantity.** AUC compressed the floors, both real-vs-real
   controls, the paired baseline and the headline into the top 0.2 of its range. Coverage and MMD²
   both spread the same comparisons over an order of magnitude. The rule was declared on coverage
   before the run for exactly this reason, and the run vindicated the choice.
3. **A mixture target must be decomposed in the same table as the headline.** Reporting against the
   4040-image mixture alone would have passed every threshold, produced internally consistent
   numbers, and hidden that the target separates from itself at 0.86–0.92.
4. **Report both generated pools, always.** It costs nothing and converts a single measurement into a
   replication.

## 3. How this changes our thinking

**The style gap is real but unremarkable; the coverage loss is the finding.** This is where A3 lands
after its own controls, and it is where the old package landed too — its log said so in as many
words. The rebuild adds the measurement that makes the conclusion safe rather than asserted: the
identity-preserving floor overtakes a genuine cross-dataset comparison, so "these are different
distributions" is worth nothing on AUC.

**What LAKE-RED does is narrow, not merely shift.** Coverage falls 24–83 % against its own input pool;
effective rank falls from 243.3 → 193.2 (`dinoL224`, raw → local) while both remain broader than the
target; and precision *rises* slightly (raw 0.6490 → local 0.6886) as recall collapses. The generator
buys a little proximity by discarding a great deal of variety.

**The strongest form of the claim is comparative, not absolute.** "LAKE-RED sits far from the real
target" is unpublishable on its own — everything sits far from everything on a linear probe. What
survives is: *a genuinely different real camouflage dataset covers the target manifold at 0.79–0.90,
and real photographs of an entirely different genre cover it at 0.71–0.75, while the synthetic images
generated from those very photographs cover it at 0.13–0.54.*

## 4. How this changes our assertions

| assertion | status after A3 |
|---|---|
| "A linear probe separates real from LAKE-RED at AUC 0.999" | **Keep only with the full ladder.** True, reproduced, and near-vacuous: an identity-preserving JPEG-30 re-encode reaches 0.9928 |
| "Cohen's *d* = 4.35–4.67 between real and generated" | **Withdraw as stated.** The estimator returns 0.69 on a true null. Held out: **+3.10 / +2.71 / +4.27** |
| "LAKE-RED covers only ~50 % of the achievable manifold" | **Keep, and strengthen to the paired form.** Recall 0.4668 against its own input pool's 0.7473, ceiling 0.9332 |
| "The real target distribution is COD10K-train" | **Withdraw.** It is 3040 COD10K + 1000 CAMO, and the two separate at 0.86–0.92 |
| "The background darkens by ~20 levels, and that drives the style axis" | **Half stands.** The shift is real (−19.236854); as a *mechanism* it was already retracted, and darkening the same images by 20 levels reaches only 0.3501 / 0.3108 in the DINO spaces |
| "Both generated pools behave alike" | **Now measured, first time.** Within 0.0006 AUC and 0.0028 colour correlation, on two independent generation runs |

## 5. The threshold that FAILED — and why it stays failed

`T8` required the in-sample *d* on random halves to exceed **0.50**, to reproduce C1's demonstration
inside A3's own data. Measured: **0.4015 / 0.4024 / 0.3031**. **FAIL.**

The cause is sample size, not a contradiction. C1 measured its +0.6991 over subsets of
B = 250…3000, and its own range reached down to +0.2144; A3's null splits 4040 into halves of ~2020,
at the large end where in-sample bias is smallest.

`T8` was also declared on the wrong arm — on C1's **imported mean-difference** estimator, chosen for
commensurability with C1's published null, whereas the figure `T8` exists to disqualify came from the
**logistic probe axis**. That estimator, on the same true null, returns
**0.6867 / 0.6805 / 0.4854**.

Following C1 R14, **the declared threshold is reported FAILED rather than relaxed or re-pointed**, and
the agreeing measurement is reported beside it as an **observation**, never promoted to a replacement
threshold. Logged as `REVISION_TABLE.md` **R23**. The disqualification of 4.67 does not depend on
`T8`: it rests on 0.6867 measured from two random halves of one dataset.

## 6. What A3 does NOT establish

**A3 is a distributional characterization, not a training-utility bound.** A distant or low-coverage
synthetic set can still improve a model, and in the ABC campaign the arm means rose *monotonically* in
all four architecture × endpoint cells. A3 supplies a candidate mechanism **consistent with** the
absence of a resolvable gain. It does not demonstrate that no gain exists, and writing it as
"the distribution is far, therefore no amount of it can help" would be a non-sequitur.

**Why it still carries weight.** A3 is deterministic over fixed vectors — no seeds, no σ̂. The ABC
campaign is underpowered against its own pre-registered statement (`2σ̂ = 0.017933` on the primary
endpoint, larger than the 0.0142 gap the design declared it could half-resolve), so ABC's null cannot
stand alone. A3 is the only measurement in the rebuild that speaks to synthetic-vs-real distance and
does not depend on power.

## 7. Limitations, declared

- **k-NN precision/recall is a manifold *estimate*.** It depends on `k` — swept over 3/5/10/20, with
  the anchor declared in advance — and on L2 normalisation, which is applied and is **our stated
  choice**; the original sources never said whether they normalised.
- **MMD is kernel-dependent** (degree-3 polynomial) and carries no threshold. A Fréchet distance was
  considered and **declined**: at n ≈ 4000 with d = 1024 a 1024×1024 covariance rests on roughly four
  samples per dimension. The absence is a choice, not an oversight.
- **The NC4K control's cleanliness is scoped to the COD10K axis.** D2_NC4K measured NC4K against the
  3040 COD10K-train images; the 1000 CAMO images in the target set were not part of that check.
- **The identity-preserving floors sweep two dimensions only** — JPEG quality and a luminance shift.
  Other corruptions are untested, so 0.9928 is a lower bound on how high a floor can reach.
- **`dinoB/224` has no rebuild cache**, so one of the original's three *d* sub-values (4.61) has no
  counterpart and is logged `NOT-REPRODUCIBLE` rather than substituted.
- **Three reporting metrics were added after an exploratory `--no-log` pass** on one embedder space:
  the old estimator's behaviour on the true null, the in-sample inflation gap, and the
  floor-versus-real-control comparison. Disclosed per C1 R15. All three are **metrics, not
  thresholds** — no declared threshold was added, weakened or removed after seeing data, and all
  three are recomputable from the committed probe table.
- **A sub-chance AUC on a floor row means "no signal", not "inverted signal."** When two sets carry
  identical content the probe fits noise in the training half and generalises worse than chance
  (JPEG-90 reaches 0.2826 in `dinoL224`).

---

## 8. Reproducing this

```bash
LAKE-RED/.venv/bin/python rebuild/A3/a3_appearance_signature.py
```

Embedding-only, under an hour on one GPU; the six control sets cache to `rebuild/A3/cache/`
(gitignored) and every subsequent run reads them. Re-running `s3` reproduces
`out/a3_probe_table.csv` **byte-identically**.

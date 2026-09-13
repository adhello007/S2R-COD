# AC_RESULTS.md — the area control on the pixel-over-structure ordering

**Status: COMPLETE. Verdict AREA-ROBUST — 7/8 and 6/8 against a declared floor of 6/8.
The second covariate clears by exactly zero margin, and that is the headline caveat.**

Authoritative block: `EXP AC` @ `results/REBUILD_LOG.txt:2612`. That block is authoritative; this
file is a reading of it. If the two ever disagree, the log wins.

Rule frozen in `PREREGISTRATION_AC.md` at `c2114af`, before `ac_measure.py` existed. Addendum A1
(dated 2026-09-13) discloses that §AC.1's `< 1e-9` reference tolerance was unsatisfiable against a
4-decimal file and replaces it with exact agreement at the recorded precision. **No §AC.4 decision
threshold was altered.**

---

## 1. What was tested

`EXP T2C` licensed the claim that `rho(MAE) > rho(1-Sa) > rho(1-IoU)` is a property of uncertainty
signals for this task rather than of ES, on 8 of 8 whole-image rows. T2C's own post-hoc explanation of
its boundary-aggregation collapse — *"band area alone predicts MAE at +0.6286"*, and a whole-image
mean is `uncertainty density x area` — **applies to the whole-image rows too**. If MAE, and the
signals, both scale with area while `S_alpha` carries an object-size term that does not, the ordering
could be a property of the metrics rather than of the signals.

This experiment partials area out and re-tests, holding the cluster partition, both floors and both
aggregations identical to the committed measurement by importing T2C's and B1's own code path.

**Gate G-AC1.** The unpartialled recomputation reproduces the committed `t2c_table.csv` whole-image
rows at the recorded 4 dp, max deviation **4.92e-05** — every value rounds to the committed figure.
The partition being read is the committed one.

---

## 2. The result

*50 clusters, committed seed 0, first-order partial Spearman. `z_obj` = per-cluster mean object area
(`gt_fg_frac`, endpoint side). `z_unc` = per-cluster mean band area (`band_frac`, target side).*

| arch | signal | rho(MAE) raw / obj / unc | rho(1-Sa) raw / obj / unc | obj | unc |
|---|---|---|---|---|---|
| SINet | ES | +0.6284 / +0.5761 / +0.5518 | +0.3433 / +0.4988 / +0.3897 | PASS | PASS |
| SINet | entropy | +0.5892 / +0.5505 / +0.5060 | +0.4267 / **+0.5517** / +0.4426 | **FAIL** | PASS |
| SINet | ensemble A0 | +0.6028 / +0.5411 / +0.5603 | +0.2698 / +0.4301 / +0.2583 | PASS | PASS |
| SINet | ensemble CSHUF | +0.5212 / +0.5002 / +0.4857 | +0.4006 / +0.4857 / +0.3937 | PASS | PASS |
| SINet-v2 | ES | +0.7070 / +0.7062 / **+0.4457** | +0.5628 / +0.6272 / **+0.4744** | PASS | **FAIL** |
| SINet-v2 | entropy | +0.7393 / +0.7134 / +0.5369 | +0.5404 / +0.6546 / +0.4266 | PASS | PASS |
| SINet-v2 | ensemble A0 | +0.6191 / +0.6245 / **+0.4355** | +0.5483 / +0.5969 / **+0.4488** | PASS | **FAIL** |
| SINet-v2 | ensemble CSHUF | +0.5576 / +0.5344 / +0.4482 | +0.4488 / +0.5209 / +0.3615 | PASS | PASS |

```
unpartialled ordering     8/8     (reproduces T2C)
partialled on object area 7/8     -> PASS, floor 6/8
partialled on band area   6/8     -> PASS, floor 6/8, ZERO MARGIN
VERDICT                   AREA-ROBUST
```

---

## 3. What the numbers actually say, including what cuts against us

**(a) The confound is real, and partial.** Area explains part of the gap. It does not explain its
sign. Under object-area partialling `rho(MAE)` falls in 7 of 8 rows, but the gap narrows mainly from
the *other* side.

**(b) Partialling object area RAISES `rho(1-Sa)` in all eight rows** — SINet ES `+0.3433 -> +0.4988`,
ensemble A0 `+0.2698 -> +0.4301`. This is the **opposite** of what the confound hypothesis predicts.
Object area was *suppressing* the structural correlation, not inflating the pixel one. The honest
statement is that controlling for object area makes uncertainty look like a **better** predictor of
structural error than the committed measurement suggested, while still a worse one than of pixel
error in 7 of 8 rows.

**(c) The single object-area failure is a tie, not a reversal.** SINet/entropy crosses by **0.0012**
(`+0.5505` against `+0.5517`), far inside the ~0.06 resolution floor T2C pre-registered. It is
recorded as a FAIL because the rule is ordinal and was frozen; it should not be read as evidence that
structure is better predicted than pixels for that row.

**(d) The band-area result is the weak one and clears by nothing.** 6 of 8 is exactly the declared
floor. Both failures are on SINet-v2, and they are where the signal is most strongly area-driven:
`rho(signal, band area)` reaches **+0.7787** (ES) and **+0.7048** (entropy) on that architecture,
against **+0.1719** to **+0.3571** across SINet. On SINet-v2, `rho(MAE)` falls from `+0.7070` to
`+0.4457` once band area is removed. **For SINet-v2, a substantial share of what the signal predicts
is area.**

**(e) Consequence for the paper's claim.** The licensed claim stands, but it must now travel with the
architecture split: the ordering is area-robust on SINet across all four signals, and area-robust on
SINet-v2 only for two of four once uncertain-region area is partialled out.

---

## 4. What this does not establish

- **Still correlational.** Partialling does not establish causation, and a surviving ordering does not
  show the signal is useful.
- **Two covariates, not all confounds.** Object area and band area are the two T2C's own account
  names. Contrast, object count, boundary complexity and scale are uncontrolled.
- **First-order only.** The covariates are partialled one at a time. No joint control was declared and
  none is substituted after the fact.
- **One endpoint**, COD10K-test, inherited from T2C.
- **Nothing about trained accuracy.** This experiment trains nothing and re-scores nothing.
- **The band-sum secondary (§AC.5) is an observation**, not a threshold, and does not reopen the
  boundary question T2C declared unreachable.

---

## 5. Threshold ledger

| Threshold | Measured | Verdict |
|---|---|---|
| G-AC1 — unpartialled rho reproduces the committed T2C table at 4 dp | max dev **4.92e-05** | **PASS** |
| ordering survives object-area partialling in >= 6 of 8 | **7/8** | **PASS** |
| ordering survives band-area partialling in >= 6 of 8 | **6/8** | **PASS**, zero margin |

**Provenance.** `rebuild/AC/PREREGISTRATION_AC.md` (+ Addendum A1) · `rebuild/AC/ac_measure.py` ·
`EXP AC` @ `results/REBUILD_LOG.txt:2612` · artifacts `rebuild/AC/out/ac_partials.json`,
`rebuild/AC/out/ac_table.csv`. Reads only committed artifacts. Trains nothing. No GPU.

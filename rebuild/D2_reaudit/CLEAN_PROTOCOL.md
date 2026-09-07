# A clean evaluation protocol for COD10K-trained camouflage models

Which evaluation columns can be reported as independent measurements, and which
cannot, with the contamination rate measured for each.

Every figure here comes from a log block in a measurement log — `EXP D2R` for the
CHAMELEON rows, `EXP D2_NC4K` for the NC4K/COD10K-test rows — and each was produced by
a committed script, not transcribed. Method and limitations are stated below so a
reader can decide whether they accept the measurement rather than take it on trust.

---

## The finding

**41 of CHAMELEON's 76 images (53.9 %) are re-encoded copies of images in the
COD10K-train / CAMO training pool.** By nearest partner, 40 are in the public
COD10K-train split and 1 is in CAMO.

Any model trained on COD10K-train has therefore already seen over half of
CHAMELEON during training. A CHAMELEON column reported for such a model is not an
independent measurement of generalisation.

This is a property of two **public datasets**, not of any one codebase. CHAMELEON
was released in 2015 and COD10K in 2020, so the parsimonious reading is that
COD10K-train absorbed CHAMELEON images when it was assembled — but only pool
membership is measured here; the direction is inference from release chronology.

---

## The protocol table

| Endpoint | Contaminated vs training | Unchecked | Nearest-neighbour gap | Verification status | Verdict |
|---|---|---|---|---|---|
| **COD10K-test** | **2 / 2026 (0.1 %)** | 524 / 2026 | none — continuous | on-disk copies; **not author-verified** | Reportable, with the caveat below |
| **NC4K** | **1 / 4121 (0.0 %)** vs the training pool; **0 / 4121** vs COD10K-test | 2406 / 4121 (vs training); 3039 / 4121 (vs COD10K-test) | none — continuous, both axes | on-disk copies; **not author-verified** | Reportable, with the caveat below |
| **CHAMELEON** | **41 / 76 (53.9 %)** | 25 / 76 | **41 below 5.51, next at 40.58** (**7.36**×) | **author-sourced release, re-audited** | **Not reportable** |
| **CAMO** | 4 / 250 (1.6 %) | 155 / 250 | none — continuous | on-disk copies; **not author-verified** | Never an endpoint — it is the checkpoint-selection set in this protocol |

**Read the gap column, not just the rate.** A contamination count is conditional on
a tolerance. The gap is not: for CHAMELEON, the sorted nearest-neighbour distances
cluster tightly and then jump 7.4× immediately after the 41st image, so 41 is a
property of the data rather than of the cutoff. The other three endpoints show no
discontinuity at all — a continuous distribution is what a clean set looks like.

**Two caveats that apply to every row.**

1. *Unchecked is not clean.* The sweep compares only images that share exact
   dimensions, so an image with no same-dimension candidate in the training pool is
   unchecked, not verified clean. That is a large fraction of NC4K and a third of
   CHAMELEON. Every rate here is a **lower bound**.
2. *The COD10K-test, NC4K and CAMO rates were measured against on-disk copies, not
   author-sourced ones.* That is the same weakness the CHAMELEON re-audit exists to
   close, and it is marked rather than hidden: **the same author-sourced re-audit is
   owed for those three.** Until it is done, treat their rates as provisional.

---

## NC4K and the COD10K test split — a clean null (`EXP D2_NC4K`)

Checked separately because the S2R-COD paper's Task Setup, **Case 3**, describes the
NC4K evaluation as additionally introducing synthetic images derived from the **COD10K
test set** into the **source** domain (Table 3, `CAMO + CHAM. + COD10K → NC4K`). Were
NC4K to overlap COD10K-test, that injection would put synthetic renderings of NC4K's
own test photographs into supervision — a *source-side* collision, distinct from the
target-side CHAMELEON finding above.

**It does not. The overlap is empty at every level measured.**

| Level | NC4K ∩ COD10K-test | NC4K ∩ COD10K-train |
|---|---|---|
| File bytes (sha256) | **0** | **0** |
| Decoded pixels (shape + RGB hash) | **0** | **0** |
| Same-dimension near-duplicates, mean\|diff\| ≤ 6.0 | **0 / 4121** | **0 / 4121** |
| — at tolerance 1 / 2 / 3 / 5 / 6 | **0 / 0 / 0 / 0 / 0** | **0 / 0 / 0 / 0 / 0** |
| Candidate pairs even shortlisted (descriptor RMS ≤ 14) | **1**, which failed full-resolution verification | **0** |
| Closest approach, mean\|diff\| | **20.610** (**3.44x** the tolerance) | **17.190** (**2.87x**) |
| Nearest-distance spread (p10/p25/p50/p75/p90) | 43.0 / 50.9 / 59.3 / 68.3 / 79.2 | 41.4 / 48.8 / 56.3 / 65.8 / 74.7 |
| Nearest-neighbour gap | **none** — continuous | **none** — continuous |

The null has a margin. The closest any NC4K image gets to a same-dimension COD10K-test
image is **20.610** grey levels — **3.44x** the confirmation tolerance, and far outside
the 0.603–5.512 range that the 41 confirmed CHAMELEON duplicates occupy. The verdict is
unchanged at shortlist depth 8, 32, and every same-dimension candidate. The two closest
pairs were also inspected by eye and are plainly different photographs, adjacent only
because both are dark, low-contrast frames at identical dimensions.

**So Case 3's described injection is not a source-into-test collision by this measure.**
The synthetic material it introduces is derived from COD10K-test photographs, and none
of those photographs is in NC4K. What the paper describes is a legitimate source-domain
choice, not a leak, and the NC4K column of Table 3 is not compromised by it.

Two caveats, both load-bearing:

- **This is a lower bound, and the unchecked fraction is large.** Only 1082 of NC4K's
  4121 images share exact dimensions with any COD10K-test image, so **3039** are
  unchecked, not clean — a **73.7%** share, and **71.7%** on the COD10K-train axis. A
  rescaled copy is invisible to this method.
- **The synthetic renderings themselves were not compared.** This measures real NC4K
  against real COD10K. Whether a *generated* image derived from a COD10K-test photograph
  can approach an NC4K image is a different question and is not answered here.

Incidentally sharpened: **COD10K-test ∩ COD10K-train = 7** at both hash levels. D2
measured 7 against the full 4040-image target pool; this locates all 7 in the COD10K
partition specifically, with none in CAMO.

---

## What the contamination is, mechanically

The leaked images enter training through the **unlabeled target-domain pool**. In
the protocol audited here, that pool is read by a loader with no ground-truth path
at all, and pseudo-labels are generated by a teacher model's own predictions.

So: **test pixels enter training; test masks never do.** This is a **transductive
protocol violation, not label leakage.** No claim of memorisation is made, and none
is supported — see the next section.

## What it does and does not invalidate

**It does** make the CHAMELEON column unreliable as an independent endpoint for any
COD10K-trained model, because the identity of the evaluation set is compromised:
over half of it is training data.

**It does not** invalidate a method whose COD10K-test and NC4K numbers are clean,
and it is not evidence that any particular published result is wrong.

**It also does not show that the contaminated images are easier.** That was measured
directly, and the honest answer is that no difficulty skew is detectable:

| Measure | Leaked (41) | Clean (35) | Leaked-set percentile within the clean set |
|---|---|---|---|
| Object-area fraction | 0.2779 | 0.2851 | 0.501 |
| Boundary complexity | 0.0605 | 0.0606 | 0.485 |
| Foreground/background contrast | 22.34 | 19.75 | 0.548 |
| Connected components | 143.5 | 52.5 | 0.559 |
| MAE, author-sourced masks | 0.2294 | 0.2082 | 0.448 |
| MAE, repackaged GT | 0.0791 | 0.0846 | 0.495 |

A percentile of 0.5 means indistinguishable from the clean subset. All six land in
0.45–0.56, and none of the four mask-derived proxies separates the groups
(Mann–Whitney *p* = 0.47–0.99). **The direction of the score difference even flips
depending on which mask release is used** — the leaked subset scores worse against
the author's masks and marginally better against the repackaged GT.

The conclusion to draw is therefore about **independence, not inflation**: the
column cannot be read as an independent measurement, and no defensible numeric
"inflation" can be quoted from these data. Claiming a specific inflation figure
would be over-reading it.

---

## A second, independent reason to distrust a CHAMELEON column

The two CHAMELEON mask releases disagree. The author-sourced masks and the
commonly-redistributed repackaged GT agree at **mean IoU 0.693** after polarity is
aligned, with only 27 of 76 identical — and they store opposite polarity
(author-sourced: object black; repackaged: object white).

That disagreement alone moves the measured score by a factor of **2.7×** on the same
predictions (MAE 0.2196 against the author masks, 0.0816 against the repackaged GT).
So a published CHAMELEON number depends on which mask release was used, and that is
rarely stated.

Two further quirks worth knowing: `animal-19.jpg` and `animal-28.jpg` in the
author-sourced release are **PNG files carrying a `.jpg` extension**, and the
canonical masks are RGBA with a fully-opaque alpha channel that carries no mask
information.

---

## Method

Contamination is detected as follows, and the detector is published alongside this
document so the measurement can be repeated on any pair of directories.

1. **Group by exact (width, height).** A re-encoded copy keeps its dimensions, so
   only same-dimension pairs can be pixel-comparable; within a dimension group the
   search is exhaustive.
2. **Shortlist** by a 32×32 greyscale descriptor (bilinear, **not**
   contrast-normalised — normalising costs recall), compared by per-pixel RMS ≤ 14.
3. **Verify every survivor at full resolution.** A pair is confirmed iff
   mean |A − B| ≤ 6.0 over RGB.
4. **Report a tolerance sweep, not one cutoff.** For CHAMELEON: 11 / 26 / 37 / 40 /
   41 images at tolerance 1 / 2 / 3 / 5 / 6. It saturates at 41.
5. **Confirm the boundary independently** with the nearest-neighbour gap above,
   which owes nothing to the tolerance, and which is unchanged whether 8, 32, or
   every same-dimension candidate is verified.
6. **Corroborate re-encoding per pair** from the JPEG quantization tables, extracted
   two independent ways (a library call and a raw DQT-marker parse) so the verdict
   does not rest on one implementation. Tables differ in 40 of the 41 pairs; the
   41st is the PNG noted above, where the container formats differ instead — which
   is re-encoding evidence in its own right.

### What the method cannot see

Crops, flips, rotations, colour shifts, rescaled copies that land outside every
dimension group, and different photographs of the same specimen. These are neither
detected nor claimed.

---

## Recommendation

For a COD10K-trained camouflaged-object model:

- Report **COD10K-test** and **NC4K**, disclosing that both were audited against
  on-disk copies and that a fraction of each is unchecked. NC4K survives the extra
  check its Case 3 setup invites: it does not overlap COD10K-test at any level.
- **Do not report CHAMELEON** as an independent endpoint. If it is reported at all,
  report it on the 35-image uncontaminated subset, name the subset, and state which
  mask release was used.
- Do not report the set used for checkpoint selection as an endpoint. In this
  protocol that is CAMO.
- Run the detector on your own directories before reporting anything. Exact hashing
  will tell you a contaminated set is clean: on this data, hashing CHAMELEON against
  the training pool returns **zero** collisions while 53.9 % of it is training data.
  That is the trap this document exists to close.

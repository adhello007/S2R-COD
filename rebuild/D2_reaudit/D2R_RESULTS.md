# D2R — Verified results

**Status: COMPLETE. 20 of 21 thresholds PASS; 1 FAIL, and the FAIL is a correction to D2's own evidence.**
**All 8 of D2's CHAMELEON values re-tested against an author-sourced copy: 8 MATCH. 3 MISMATCH, all three corrections to our own prior work.**

Source of every number below: `results/REBUILD_LOG.txt`, the **fourth and last**
block **`EXP D2R`**. That block is authoritative; this file is a reading of it. Every
one of the 85 bolded figures in this file appears verbatim in that block — checked
mechanically, not by eye.

Setup and pre-declared thresholds: `rebuild/D2_reaudit/REAUDIT_PLAN.md`, approved
before any code ran. **Trains a model: NO** (s5r-b runs inference from an existing
checkpoint; no optimizer runs and no checkpoint is written).

---

## 1. What was measured

### 1.1 The two CHAMELEON copies are the same images — and D2's finding transfers directly

| Metric | Value |
|---|---|
| `Dataset/Test/CHAMELEON/Imgs` | **76** |
| `Dataset/chameleon_new/animals` (author-sourced) | **76** |
| Identical at file-byte level (sha256, set-based) | **76/76** |
| Identical at decoded-pixel level (set-based) | **76/76** |
| Reconciliation outcome | **(a)** — pixel-identical |

Outcome (a) was one of four possibilities with boundaries fixed in the plan before
running. The images are **byte-identical**, so the re-audit measures the same pixels
D2 measured, and D2's finding transfers directly rather than by argument.

Which copy D2 used was established from **committed artifacts**, not from disk state:
`git show 17dfbbf:rebuild/common.py` gives `'cham': path='Dataset/Test/CHAMELEON/Imgs'`,
corroborated by the committed per-pair manifest agreeing on **41/41** file sizes and
**41/41** dimensions.

### 1.2 Contamination against the author-sourced canonical set

Method-identical to D2's authoritative s4/s4b — every constant copied, not re-chosen:
32×32 greyscale BILINEAR descriptor with **no** contrast normalisation, exhaustive
within each exact-dimension group, Gram-matrix shortlist at RMS ≤ 14, then **every
survivor verified at full resolution** at mean|diff| ≤ 6.0.

| Metric | D2 (repo copy) | D2R (author-sourced) | Verdict |
|---|---|---|---|
| CHAMELEON images that are re-encodes of training data | **41/76 (53.9 %)** | **41/76 (53.9 %)** | **MATCH** |
| The 41 filenames | 41 names | identical set | **MATCH** |
| Candidate pairs shortlisted | **323** | **323** | **MATCH** |
| Pairs confirmed at mean\|diff\| ≤ 6.0 | **132** | **132** | **MATCH** |
| — crossing endpoint ↔ training | **49** | **49** | **MATCH** |

D2's three global figures are recomputed over **D2's original 8 splits only**, with
the author-sourced set counted apart, so the committed numbers stay directly
comparable. Across all 9 splits the confirmed total is **207**.

**Tolerance sweep** — the headline must not depend on one cutoff:

| mean\|diff\| ≤ | 1.0 | 2.0 | 3.0 | 5.0 | 6.0 |
|---|---|---|---|---|---|
| Canonical CHAMELEON matched | **11/76** | **26/76** | **37/76** | **40/76** | **41/76** |

Identical to D2 at every tolerance. It saturates at 41.

### 1.3 The gap — 41 is a property of the data, not of the cutoff

For every endpoint image, the full-resolution distance to its nearest same-dimension
*training* image, then a search for a discontinuity in the sorted distances:

| Endpoint | Checkable | Unchecked | Gap in sorted nearest distances |
|---|---|---|---|
| COD10K test | **1502/2026** | 524 | **none** |
| **CHAMELEON (canonical)** | **51/76** | **25** | **41 below 5.51, next at 40.58** |
| CHAMELEON (repo copy) | **51/76** | 25 | **41 below 5.51, next at 40.58** |
| NC4K | **1715/4121** | 2406 | **none** |
| CAMO-val | **95/250** | 155 | **none** |

A **7.36×** jump immediately after exactly 41 images, and `n_below` equals the
tolerance-6.0 matched count — two instruments agreeing on the same integer from
directions that owe nothing to each other. The other three endpoints show no
discontinuity: a continuous distribution is what a clean set looks like.

**This was the result most able to overturn the finding, and it held.** The plan named
it in advance: the count 41 is tolerance-conditional and arguable on its own; the gap
is what makes it a claim about the data.

**Shortlist-depth sensitivity**, added because D2's s4b verifies only the descriptor
top-8, so its "nearest" is a lower bound:

| Candidates verified at full resolution | 8 (D2's depth) | 32 | every same-dimension candidate |
|---|---|---|---|
| Gap | **41 below 5.51, next at 40.58** | **41 below 5.51, next at 40.58** | **41 below 5.51, next at 40.58** |

Unchanged. The top-8 shortlist was not hiding anything.

### 1.4 Per-pair re-encoding evidence — and a correction to D2

Extracted two independent ways so the verdict does not rest on one library: PIL's
`Image.quantization` (D2's method, verbatim) and a raw JPEG **DQT** marker parse.

| Metric | Value |
|---|---|
| Quantization tables differ, raw DQT parse | **40/41** |
| Not applicable (a side has no JPEG table) | **1/41** — `animal-19.jpg` |
| Pairs differing in container format | **1/41** |
| The two extractions return the same verdict | **41/41** |
| `mean\|diff\|` range across the 41 pairs | **0.603 .. 5.512** |
| Canonical CHAMELEON files that are not JPEG | **2/76** (JPEG=74, PNG=2) |

**D2's "quantization tables differ in 41/41 pairs" is properly 40/41 differing plus one
not-applicable.** `animal-19.jpg` and `animal-28.jpg` are **PNG files carrying a `.jpg`
extension** (magic bytes `89504e47`), so they have no JPEG quantization table at all.
D2 compared tables with `!=`, which reports "the tables differ" when one side has no
table — absence of evidence read as evidence. `animal-19` is one of the leaked 41.

The conclusion for that pair is unaffected and arguably stronger: its two files differ
in **container format** (a 413 KB PNG against a 132 KB JPEG of the same photograph),
which is re-encoding evidence in its own right. So **41/41 pairs carry independent
re-encoding evidence** — 40 by quantization table, 1 by container format. Threshold T5
is left **FAILING** against its declared wording; T5b states what survives.

### 1.5 All 41 pairs, visually verified

Exported by `d2r_export_pairs.py` to `rebuild/D2_reaudit/pairs/`: the 41 canonical
images, their 41 training partners, one figure per pair (CHAMELEON | training partner |
difference amplified ×20), and three contact sheets. The per-pair manifest is tracked at
`out/d2r_duplicate_pairs.csv`; the 108 MB of images is not.

Three were inspected directly, chosen as the extremes and the awkward case:

- **Rank 1** — `animal-76.jpg` / `COD10K-CAM-3-Flying-65-Owl-4516.jpg`, mean|diff| **0.603**.
  One owl on one tree. The ×20 difference panel is structureless noise.
- **Rank 41** — `animal-31.jpg` / `COD10K-CAM-1-Aquatic-20-Turtle-1208.jpg`, mean|diff|
  **5.512**, content std 69.2. One turtle in one patch of leaf litter, matching down to
  individual leaves. The larger residual is a texture effect, not a structural one: the
  difference panel is uniform high-frequency noise.
- **Rank 39** — `animal-19.jpg` / `COD10K-CAM-3-Flying-53-Bird-3014.jpg`, mean|diff|
  3.750. One snowy owl on one rock face; the PNG-vs-JPEG pair above.

(Per-pair values other than the range are not logged individually; they are tracked in
`out/d2r_duplicate_pairs.csv`, which is the artifact the log block names.)

### 1.6 Where the partners live — the finding is about public datasets

| Metric | Value |
|---|---|
| Distinct canonical images contaminated, nearest partner in **public COD10K-train** | **40/41** |
| — nearest partner in CAMO | **1/41** |
| Confirmed pairs whose training side is in COD10K-train (pair level) | **41/42** |
| — in CAMO (pair level) | **1/42** |

Pair level exceeds image level because one CHAMELEON image has two partners within
tolerance. This is the reframing: the contamination is a property of **two public
benchmarks**, not of this repository. Any model trained on COD10K-train has seen those
40 images.

### 1.7 Impact — no difficulty skew is detectable, so no inflation figure is claimed

The plan pre-declared the reading: a leaked-set percentile within the clean set in
[0.25, 0.75] means no difficulty skew; > 0.75 means easier (inflation); < 0.25 means
harder. Percentiles are oriented so that > 0.75 always reads "easier".

Model-free proxies from the canonical masks (s5r-a):

| Proxy | Leaked (41) | Clean (35) | Percentile | Mann–Whitney *p* | Skew |
|---|---|---|---|---|---|
| Object-area fraction | 0.2779 | 0.2851 | **0.5010** | 0.992 | none |
| Boundary complexity | 0.0605 | 0.0606 | **0.4850** | 0.827 | none |
| Foreground/background contrast | 22.34 | 19.75 | **0.5484** | 0.472 | none |
| Connected components | 143.5 | 52.5 | **0.5589** | 0.475 | none |

Inference-only score split (s5r-b), `Snapshot/SINet/S2C/Tea_epoch_best.pth` over the 76
canonical images, scored with the repo's own `Eval/metrics.py`:

| Mask set | All 76 | Clean 35 | Leaked 41 | Clean − All | Leaked percentile | Skew |
|---|---|---|---|---|---|---|
| Author-sourced, MAE | **0.219648** | **0.208234** | **0.229392** | **−0.011414** | **0.4481** | none |
| Author-sourced, Sα | **0.583363** | **0.601893** | **0.567545** | **0.01853** | **0.4606** | none |
| Repackaged GT, MAE | **0.081631** | **0.084573** | **0.079119** | **+0.002943** | **0.4948** | none |
| Repackaged GT, Sα | **0.724257** | **0.727781** | **0.721249** | **+0.003524** | **0.4934** | none |

**All eight percentiles land in 0.448–0.559**, where 0.5 is indistinguishable from the
clean subset, and no proxy separates the groups. Worse, **the sign of the score
difference flips with the mask release**: against the author's own masks the leaked
subset scores *worse*; against the repackaged GT it scores marginally *better*.
`split_direction_agrees_across_mask_sets` = **False**.

**So the honest claim is about independence, not inflation.** The contaminated images
are not detectably easier, and no defensible "the column is inflated by X" figure comes
out of these data. This mirrors D2's own COD10K result — mean percentile 0.4761, no
memorisation signature — at 20× the contamination rate. Quoting an inflation number
here would be over-reading it, and the plan's pre-declared reading is what makes that
call rather than hindsight.

### 1.8 A second, independent reason to distrust a CHAMELEON column

| Metric | Value |
|---|---|
| Mask filename join `mask-N.png` ↔ `animal-N.png` is a bijection over 1…76 | **True** |
| Author-sourced mask polarity (declared per source) | **object_black**, white fraction **0.7187** |
| Repackaged GT polarity | **object_white**, white fraction **0.1400** |
| Polarities agree | **False** |
| Mean IoU as stored | **0.0** |
| Mean IoU after polarity alignment | **0.6932** |
| Masks with aligned IoU ≥ 0.9 | **40/76** |
| Exactly identical after alignment | **27/76** |
| Canonical masks are RGBA | **True**, alpha foreground fraction **1.0** — alpha carries no mask |

The two CHAMELEON *mask* releases are not the same annotation. Polarity was declared
**per source** from the aggregate white fraction, never per image — per `REBUILD_PLAN.md`
A2, because per-image detection misfires on objects covering most of a frame, and trap
T2 in §2 is exactly this failure. Had it been assumed, every number in §1.7 would have
been computed against inverted masks.

On identical predictions, that mask-set disagreement alone moves MAE by **2.7×**
(0.2196 against the author masks, 0.0816 against the repackaged GT). A published
CHAMELEON number therefore depends on which mask release was used, which is rarely
stated.

### 1.9 The mechanism, re-derived from source

| Assertion | Measured |
|---|---|
| `get_tarloader` call site | **`MyTrain.py:317`** |
| D2_RESULTS.md's cited lines are correct | **False** |
| `get_tarloader` has a `gt_root` parameter | **False** (`get_srcloader` does) |
| `TarDataset.__getitem__` returns a mask | **False** — returns `weak_image, strong_image` |
| `Dataset/Target/` has a `GT/` subdirectory | **False** |
| `CLS.py` reads the target pool with `gt_root=None` | **True** |

`D2_RESULTS.md` §3.0 cites *"`MyTrain.py:220,297` feeds `get_tarloader`"*. Line 220 is
the `--source_root` help string and line 297 is the EMA teacher weight copy. The
**mechanism** D2 described is correct — the target pool enters training unlabeled and
CLS pseudo-labels it from teacher CAMs — only the line numbers were wrong. Recorded as
a correction, not silently fixed, and now asserted from source at run time so it cannot
drift again.

### 1.10 Was CHAMELEON ever a sanctioned endpoint?

| Assertion | Measured |
|---|---|
| `README.md` CHAMELEON mentions | **1** — inside `Source (Synthetic)` / CNC |
| README lists CHAMELEON under `Test (Real)` | **False** |
| `Dataset/Source/CNC/` — the README's own path for CNC — exists | **False** |
| `Dataset/Test/CHAMELEON/` — absent from the README's tree — exists | **True** |
| `Experiments/REPRODUCE_TABLE1_v2.md` CHAMELEON mentions | **0** |
| CHAMELEON prediction directories under `Result/` | **0** |

---

## 2. D2's values re-tested

| # | D2 value | D2R | Verdict |
|---|---|---|---|
| 1 | CHAMELEON contaminated = 41/76 (53.9 %) | 41/76 (53.9 %) | **MATCH** |
| 2 | The 41 leaked filenames | identical set | **MATCH** |
| 3 | Candidate pairs shortlisted = 323 | 323 | **MATCH** |
| 4 | Pairs confirmed = 132 | 132 | **MATCH** |
| 5 | Endpoint↔training pairs = 49 | 49 | **MATCH** |
| 6 | Tolerance sweep = 11/26/37/40/41 | 11/26/37/40/41 | **MATCH** |
| 7 | `epNN_cham_checkable` = 51/76 | 51/76 | **MATCH** |
| 8 | `epNN_cham_gap` = 41 below 5.51, next at 40.58 | 41 below 5.51, next at 40.58 | **MATCH** |
| 9 | Quantization tables differ in 41/41 pairs | **40/41 differ + 1 not applicable** | **MISMATCH** |
| 10 | `MyTrain.py:220,297` feeds `get_tarloader` | **`MyTrain.py:317`** | **MISMATCH** |
| 11 | `REBUILD_PLAN.md` §3: CHAMELEON is a secondary endpoint | README lists it as CNC **source** only | **MISMATCH** |

Eight of eight measurements reproduce exactly against an author-sourced copy. **All
three MISMATCHes are corrections to our own prior work, not to the data** — one
over-counted evidence channel, one wrong line citation, one endpoint we adopted without
checking the README.

---

## 3. How the findings change our approach, thinking and assertions

### 3.1 The finding survives independent re-verification, and gets larger

- **Standing claim:** 41 of CHAMELEON's 76 images are re-encoded training data —
  measured against the copy on this disk, with D2 itself recording at §5 that
  "CHAMELEON is not checked against its own publication."
- **Measured:** the author-sourced release is **byte-identical** to the repo copy
  (76/76 at both hash levels), and every D2 figure reproduces exactly — 41/76, the
  same 41 names, the 7.36× gap, the full tolerance sweep, 323/132/49.
- **Sharpened claim:** the contamination is **`CHAMELEON ∩ COD10K-train = 40/76`**,
  a fact about two **public benchmarks**. 40 of the 41 partners are public
  COD10K-train images and 1 is CAMO. Any model trained on COD10K-train has seen them.
- **Consequence.** This stops being a note about one repository's endpoint choice and
  becomes a reusable result: the CHAMELEON column is not an independent measurement
  for the whole class of COD10K-trained methods. That is what `detect_contamination.py`
  and `chameleon_contaminated.json` are for.

### 3.2 The claim is about independence, not inflation — and the data forced that

- **What we expected to report:** "by how much the column misleads", mirroring D2's
  0.476 percentile analysis.
- **Measured:** nothing. All eight difficulty measures put the leaked set at percentile
  **0.448–0.559** within the clean subset; no proxy separates the groups (*p* 0.47–0.99);
  and the sign of the score gap **flips** between the two mask releases.
- **Revised position:** we report that **CHAMELEON cannot serve as an independent
  endpoint**, and we explicitly decline to quote an inflation figure. The compromise is
  to the *identity* of the evaluation set, not to a measurable score advantage.
- **Why this matters more than it looks.** The tempting paper sentence — "contaminated
  benchmarks inflate reported scores" — is not supported here, and the plan's
  pre-declared [0.25, 0.75] reading is what stopped us writing it. A protocol violation
  does not need a score advantage to be disqualifying.

### 3.3 An independent second extraction earned its cost immediately

- **Standing claim:** quantization tables differ in **41/41** pairs.
- **Measured:** **40/41** differ; the 41st (`animal-19.jpg`) is a **PNG with a `.jpg`
  extension** and has no JPEG table, and D2's `!=` comparison scored a missing table as
  a differing one.
- **Sharpened claim:** 41/41 pairs carry independent re-encoding evidence — 40 by
  quantization table, 1 by container format, which for a PNG/JPEG pair of one
  photograph is stronger evidence, not weaker.
- **Position:** the FAIL stays. The second extraction existed only to stop the verdict
  resting on one library's behaviour, and it caught a real over-claim on its first run.
  Two files in the release are PNGs pretending to be JPEGs, which is worth knowing on
  its own.

### 3.4 Mask polarity was inverted, and assuming otherwise would have corrupted §1.7

- **Standing claim:** none — D2 explicitly disclaimed any claim about endpoint masks
  ("No claim about GT masks", §5).
- **Measured:** the author-sourced masks store **object = black** (white fraction
  0.7187); the repo's repackaged GT stores **object = white** (0.1400). As stored, their
  IoU is **0.0**. After per-source polarity alignment it is **0.6932**, with only 27/76
  identical.
- **Position:** polarity is declared **per source** from the aggregate, never per image.
  Every number in §1.7 depends on this having been measured rather than assumed — trap
  T2 in `REBUILD_PLAN.md` §2, arriving exactly where it was predicted.
- **New consequence:** the two mask releases are different annotations, and choosing
  between them moves MAE by **2.7×**. That is a second, independent reason a CHAMELEON
  column is not comparable across papers, and it is not about contamination at all.

### 3.5 We adopted an endpoint the repository never sanctioned

- **Standing claim:** `REBUILD_PLAN.md` §3 — "primary endpoint COD10K; **secondary
  endpoints CHAMELEON and NC4K**."
- **Measured:** `README.md` mentions CHAMELEON exactly once, inside the
  `Source (Synthetic)` CNC bundle, and lists only COD10K-test under `Test (Real)`.
  `Dataset/Source/CNC/` does not exist on disk; the undocumented
  `Dataset/Test/CHAMELEON/` does. `Experiments/REPRODUCE_TABLE1_v2.md` has **0**
  CHAMELEON mentions, and `Result/**` holds **0** CHAMELEON predictions.
- **Revised position:** the framing is **not** "we found a bug in their evaluation."
  CHAMELEON is *source* material in this repository's documented design; the test
  directory is an undocumented local addition; and it was **our own** rebuild plan that
  promoted it to a secondary endpoint without checking. That correction goes in
  `REVISION_TABLE.md` §2 beside R3 and R4.
- **Left `UNVERIFIED`, deliberately:** whether the **published** S2R-COD paper reports a
  CHAMELEON column anywhere. The PDF is not in this checkout. Also flagged and *not*
  answered: under `--task C2C` the CNC bundle is the **source** pool, so for C2C
  CHAMELEON is training data by design, and a C2C table reporting it as test would be a
  direct source/test collision — strictly worse than what D2 found. Resolving that needs
  the paper.

### 3.6 The published detector makes the method checkable by strangers

- **Measured:** `detect_contamination.py` passes an 8-assertion synthetic
  known-answer self-test with no repository data, and reproduces this sweep's canonical
  pair list at **41/41** pairs and **41/41** names. It found **1** extra pair — the
  second partner of the image that has two, which s4br does not select because it keeps
  only the nearest.
- **Position:** the tool's correctness is a **logged threshold** (T16), not a claim in a
  README. It takes any two directories, imports nothing from this repository, and the
  release bundle passes a 12-pattern anonymisation scan with **0** hits.

---

## 4. Consequences by downstream experiment

| Experiment | What D2R changes for it |
|---|---|
| **D2** | Its CHAMELEON finding is confirmed against an author-sourced copy; three of its statements are corrected (quantization count, line citation, and the endpoint's status). Its 41-name set and 0.1 %/0.0 % rates stand |
| **B1 / B2 / C1 / C3** | Unchanged. They already read `d2_leaked_names.json` and already exclude CHAMELEON |
| **Reporting** | The claim to make is "CHAMELEON is not an independent endpoint for COD10K-trained models", **not** "CHAMELEON scores are inflated". §1.7 does not support the latter |
| **Any CHAMELEON number, anywhere** | Must state which mask release it used. The two disagree at IoU 0.693 and move MAE by 2.7× |
| **`REBUILD_PLAN.md` §3** | Its "secondary endpoint CHAMELEON" was never sanctioned by the README. Corrected in `REVISION_TABLE.md` |
| **COD10K-test / NC4K / CAMO** | Their rates are still measured against on-disk copies only. The same author-sourced re-audit is **owed** for them, and `CLEAN_PROTOCOL.md` marks it |

---

## 5. What D2R does not establish

- **Every count remains a lower bound.** Coverage is exact duplicates plus
  same-dimension re-encodes. Rescaled copies that leave every dimension group, crops,
  flips, colour shifts, and different photographs of one specimen are **not** detected
  and are not claimed. **25 of the canonical 76** have no same-dimension training
  candidate at all and are therefore **unchecked, not clean**.
- **No inflation figure.** §1.7 measures no difficulty skew and the sign flips with the
  mask set, so "the column is inflated by X" is not available from these data.
- **No claim about the published paper.** Whether S2R-COD reports a CHAMELEON column is
  `UNVERIFIED` — the PDF is not in this checkout.
- **No literature survey.** That any *specific* published method's CHAMELEON column is
  affected follows only from the measurement plus that method's training set. D2R
  measures the datasets, not the literature.
- **COD10K-test, NC4K and CAMO are not author-verified.** Their rates come from the
  copies on this disk — the exact weakness this re-audit closed for CHAMELEON alone.
- **The provenance direction is inference.** CHAMELEON (2015) predates COD10K (2020), so
  COD10K-train absorbing CHAMELEON is the parsimonious reading; only pool membership is
  measured.
- **s5r-b is inference, not an endpoint result.** It exists solely to test for a
  difficulty skew and must never be quoted as a CHAMELEON performance number.

---

## 6. Why the log has four D2R blocks

| Block | Result | Cause |
|---|---|---|
| 1 | 18 PASS / 1 FAIL | All steps ran on the full 9 splits. T5 failed, which is how the PNG-with-`.jpg`-extension case was found |
| 2 | s0 + s7r only | Quantization evidence re-emitted with the `na` case separated and T5b added, plus `CLEAN_PROTOCOL.md` in the release bundle. Partial, so not authoritative |
| 3 | 20 PASS / 1 FAIL | Full pipeline with the evidence correction in place |
| 4 | **20 PASS / 1 FAIL** | The traceability rule. Blocks 1–3 emitted `epNN` and contamination metrics for the two CHAMELEON copies only, while this file and `CLEAN_PROTOCOL.md` cite COD10K-test's 1502/2026, NC4K's 1715/4121 and CAMO's 95/250. Those were computed and sitting in `out/d2r_endpoint_nearest.json`, but a number a document uses must exist as a **logged metric**, so all five endpoints were promoted into the script. No value changed. **Authoritative** |

Blocks 3 → 4 are the same rule that produced D2's own blocks 1 → 2 and E0's blocks
3 → 4: a figure that cannot be traced to a log block does not belong in a document,
**even when the figure is correct**. Nothing was superseded; six numbers were promoted
from artifact to metric.

The FAIL in every block is T5, the quantization-table threshold, and **it stays**: the
declared wording said tables differ in *every* confirmed pair, and one pair has no table
to compare. Relaxing the wording after seeing the data would defeat the point of
declaring it beforehand. T5b was added to state the claim that does survive, and its
addition is disclosed here rather than absorbed silently.

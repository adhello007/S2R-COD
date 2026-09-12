# FINAL_RESULTS.md — Stage C consolidated results

**What this file is.** A per-experiment consolidation of the Stage C rebuild, built to be the direct
source for paper-writing. It contains no new computation. Every number is quoted verbatim from a
committed result document or a committed `EXP` block in `results/REBUILD_LOG.txt`, with the source
cited inline.

**What this file is not.** It does not decide section structure, does not write narrative prose, and
makes no claim that is not traceable to a committed artifact.

## Sourcing rules applied throughout

1. **Nothing is recomputed, re-averaged or re-derived.** A value the paper may want that does not
   exist in a committed artifact is marked `[NOT IN COMMITTED ARTIFACTS]` rather than produced.
2. **Citation format** — `[<result doc> §<section> | EXP <id> #<block ordinal> @ REBUILD_LOG.txt:<line>]`.
   The line number is the block's header line in the committed log.
3. **Where a result document and a log block disagree, the disagreement is flagged**, not resolved.
   See §16 (a)–(b). Every result document in this suite states its own precedence rule — typically
   *"That block is authoritative; this file is a reading of it. If the two ever disagree, the log
   wins."*
4. **Claim-type tags** are applied to every headline and secondary finding:
   - `[MEASURED]` — produced by a logged run.
   - `[PREDICTED]` — stated in advance, not yet tested by a run.
   - `[PREDICTION CONFIRMED BY TRAINING]` — an earlier prediction that a later training campaign
     turned into a measurement. These are a specific strength of this suite and are called out.
   - `[PREDICTION REFUTED BY MEASUREMENT]` — a stated expectation that the data overturned.
   - `[INFERRED]` — follows from a measurement plus an argument, and is labelled as such in the source.
5. **Markers carried forward, never silently resolved** — `UNVERIFIED`, `UNVERIFIED-DEFERRED`,
   `DEFERRED`, `UNRUN`, `NOT-REPRODUCIBLE`, `DEGENERATE-NOT-REPORTED`, `NOT APPLICABLE`. Full ledger
   in §15.
6. **Table candidacy** is labelled `[MAIN-TEXT CANDIDATE]` or `[APPENDIX CANDIDATE]` on every table.
7. **Every blockquote is a verbatim quotation from a committed source**, with one exception: three
   editorial notes, each opening with a bold label — the A1 `[NO EXPERIMENT RUN …]` box (entry 6),
   the **Structural note** on B1 (entry 8) and the **Location note** on T2 (entry 11). These are
   written by this consolidation, not quoted.

**Verification performed on this file.** All **478** distinctive numeric literals (≥3 decimal places,
scientific notation, or `N/M` fractions) were matched back to the committed sources — **0 unmatched**.
All **239** quotation blockquote lines match a source line verbatim under whitespace normalisation.
All **18** cited `REBUILD_LOG.txt` line numbers land exactly on the block header they name.

## A naming hazard, stated once

`T1` / `T2` / `T3` are overloaded in this repository in four unrelated senses. In **this** file:

- `EXP T2` and `EXP T2C` always mean the **experiments** (the falsification arms, and the
  signal-generality check). They are always written with the `EXP` prefix or as entry numbers 11/12.
- `T1`…`T8` inside an experiment's own discussion are that experiment's **pre-registered threshold
  labels**, and are unrelated between experiments.
- The **scope tiers** are written `Tier 1` / `Tier 2` / `Tier 3`, spelled out, and appear only in
  `TIER_SEGREGATION.md`.
- `trap T1/T2/T3` refers to the data traps declared in `REBUILD_PLAN.md` §2.

---

# 0. Inventory

Every experiment directory under `rebuild/`, its committed result document, and its committed `EXP`
block(s). `results/REBUILD_LOG.txt` is 2,610 lines and holds **32 `EXP` blocks across 11 distinct
experiment ids**. Working tree verified clean for `rebuild/` and `results/` at the time of writing
(`git status --porcelain rebuild/ results/` empty, HEAD `8f12766`). Note `6efde9f`, which appears
inside the `EXP T2C` block and in T2C's pre-registration citation, is the commit recorded **at run
time**, not HEAD.

## 0.1 The twelve experiments

| # | EXP id | Directory | Result document (lines) | `EXP` blocks @ REBUILD_LOG.txt | Authoritative | Status, quoted verbatim |
|---|---|---|---|---|---|---|
| 1 | `E0` | `rebuild/E0/` | `E0_RESULTS.md` (256) | 4 — L29, L95, L163, **L231** | block #4 | "**Status: COMPLETE. 16 / 16 thresholds PASS.**" |
| 2 | `D2` | `rebuild/D2/` | `D2_RESULTS.md` (349) | 5 — L306, L372, L440, L514, **L600** | block #5 | "**Status: COMPLETE. 12 of 13 thresholds PASS; 1 FAIL, and the FAIL is the headline finding.**" / "**All 5 old claims re-tested: 5 MATCH.**" |
| 3 | `D2R` | `rebuild/D2_reaudit/` | `D2R_RESULTS.md` (425) | 4 — L1484, L1627, L1694, **L1844** | block #4 | "**Status: COMPLETE. 20 of 21 thresholds PASS; 1 FAIL, and the FAIL is a correction to D2's own evidence.**" |
| 4 | `D2_NC4K` | `rebuild/D2_nc4k/` | `README.md` (126) — **setup only, no numbers** | 2 — L2006, **L2074** | block #2 | *(no status line in the doc; block #2 records* `T1`–`T8` *all* `-> PASS`*)* |
| 5 | `D1` | `rebuild/D1/` | `D1_RESULTS.md` (201) | 1 — **L696** | the only block | "**Status: COMPLETE. All ten declared thresholds PASS.**" / "**Old claims re-tested: 2 MATCH, 1 MISMATCH.**" |
| 6 | `A1` | `rebuild/A1/` | `A1_SCOPING.md` (634) | **none** | — | "Resolved by **static citation only — no experiment run.**" |
| 7 | `A3` | `rebuild/A3/` | `A3_RESULTS.md` (363) | 1 — **L2147** | the only block | "**Status: COMPLETE. 14 of 15 declared thresholds PASS; the 1 FAIL is a correction to A3's own threshold design, and it is left failing rather than repaired.**" |
| 8 | `B1` | `rebuild/B1/` | `B1_RESULTS.md` (501) — **three stacked documents** | 4 — L762, L840, L922, L990 | per-document: doc 1 → block #2; doc 2 → block #3; doc 3 → block #4 | "**Status: COMPLETE. 6 of 7 thresholds PASS; 1 FAIL, and the FAIL is the most important result.**" |
| 9 | `C1` | `rebuild/C1/` | `C1_RESULTS.md` (316) | 4 — L1054, L1099, L1148, **L1201** | blocks **#3** (measurement) and **#4** (audit) | "**Status: COMPLETE, then AUDITED. Measurement: 6 of 7 thresholds PASS. Attribution audit (§8): 2 of 7 PASS, 5 FAIL.**" |
| 10 | `ABC` | `rebuild/ABC/` | `ABC_RESULTS.md` (275) | 3 — L1252, L1323, L1376 | **all three** — sequential stages, each authoritative for its own | "**Status: COMPLETE. Block #1: 6/6 gates, 15/15 thresholds PASS. Block #2: 5 of 6 thresholds PASS, 1 FAIL. Block #3: 3/3 thresholds PASS.**" |
| 11 | `T2` | `rebuild/ABC/` (artifacts in `out/t2/`) | `ABC/T2_RESULTS.md` (369) | 3 — L2295, L2409, L2452 | **all three** — #1 pre-flight, #2 run accounting, #3 verdict | "**WITHIN NOISE on all twelve cells: every gap, both architectures, both endpoints.**" |
| 12 | `T2C` | `rebuild/T2C/` | `T2C_RESULTS.md` (185) | 1 — **L2550** | the only block | *(no status banner)* "**The ordering generalises. The strong reading of it does not.**" |

## 0.2 Inventory anomalies — nothing here is missing, but several things are not where the name implies

| Anomaly | Detail |
|---|---|
| **`EXP T2` has no `rebuild/T2/` directory** | It lives in `rebuild/ABC/` (`T2_RESULTS.md`, `T2_PLAN.md`, `PREREGISTRATION_T2.md`) with artifacts in `rebuild/ABC/out/t2/`. **`rebuild/ABC/` therefore holds two experiments** and must not be read as one. Its log blocks record `--tag t2`. |
| **Result document, no log block** | `A1` — `rebuild/A1/A1_SCOPING.md` exists; there are **zero** `EXP A1` blocks. The document states this itself: "**No number in this document enters `results/REBUILD_LOG.txt`.**" Entry 6 is written accordingly. |
| **Log blocks, no `*_RESULTS.md`** | `D2_NC4K` — 2 committed blocks, but the only document is `README.md`, which states "**No measured number appears in this file.**" Every NC4K number in entry 4 is quoted from the log block or from `rebuild/D2_reaudit/CLEAN_PROTOCOL.md`. |
| **Numbers, no log block** | `rebuild/ABC/POOL_MECHANICS_AUDIT.md` (628 lines, read-only audit; driver `pool_mechanics_probe.py` emitted no `EXP` block). Per the sourcing rule its figures are **not** promoted into any entry or table. Recorded in §16(c). |
| **Neither — declared unrun** | `EXP C2`: **0 blocks, no directory, no document.** `C1_RESULTS.md` §6 records "C2 remains **UNRUN** (0 `EXP C2` blocks), and `\|Ds\|` remains **UNVERIFIED**". Carried forward in §15. |
| **`EXP` id ≠ directory name** | `D2R` → `rebuild/D2_reaudit/`; `D2_NC4K` → `rebuild/D2_nc4k/`; `T2` → `rebuild/ABC/`. |
| **Not an experiment** | `rebuild/PAPER/` (gitignored, untracked) and `rebuild/reference/old_scripts/` (archived). Neither is used as a source anywhere in this file — see §16(e). |

**Chronology vs dependency order.** Entries below run in dependency order, with the contamination
track kept contiguous. The committed blocks ran in a different order: `D2R` and `D2_NC4K` are dated
`2026-09-07`, i.e. **after** `ABC` (2026-09-04 … 09-06), and `A3` is dated `2026-09-08`. Where a
later experiment corrects an earlier one, the entry says so.

---

# 1. E0 — input provenance and representation verification

**What it tested.** E0 built and certified the inputs every later experiment reads: a per-file hash
manifest, the pixel-level meaning of each image and mask representation, three embedder caches, and
whether the LAKE-RED render pool can be *regenerated* rather than inherited. It deliberately answers
no question about whether targeting works.

**Headline result.** LAKE-RED regenerates the pool exactly: **4447 / 4447** images and
**4447 / 4447** masks **byte-identical** at `--seed 0`, mean absolute pixel difference **0.0**
`[E0_RESULTS.md §1 s4, §2.2 | EXP E0 #4 @ REBUILD_LOG.txt:231]`. `[MEASURED]` — and this
**refuted the plan's own stated expectation** that byte-identity would not survive cuDNN
nondeterminism `[PREDICTION REFUTED BY MEASUREMENT]`.

### Table 1.1 — Render regeneration `[APPENDIX CANDIDATE]`

*Source: `E0_RESULTS.md` §1 s4, block `EXP E0` #4 @ `REBUILD_LOG.txt:231`.*

| Metric | Value |
|---|---|
| Images regenerated | **4447** (seed 0, 2 shards, ~66 min) |
| Shared with the pool on disk | **4447** |
| **Byte-identical** | **4447 / 4447** |
| Mean absolute pixel difference | **0.0** |
| Cluster agreement | **1.0** (k=20, n=4447) |

### Table 1.2 — `isReplace` compositing: the object is copied, not generated `[MAIN-TEXT CANDIDATE]`

*Source: `E0_RESULTS.md` §1 s2 and §2.1, block `EXP E0` #4 @ `REBUILD_LOG.txt:231`. n=200.*
*This is the mechanism D1 later re-measures over all 4447 of both pools — see entry 5.*

| Check | Measured | Reading |
|---|---|---|
| `isReplace` object-region error | **6.245** mean abs | JPEG scale |
| `isReplace` background error | **71.676** mean abs | generation scale |
| Ratio background / object | **11.5×** (n=200) | only the background is synthesized |
| Cutout background value | **128**, threshold 127 | literal constant |
| Cutout background share of frame | **0.8224** | **82.2% of the frame is one constant** |

`test.py:165` is `out_array[mask_array == 0] = image_array[mask_array == 0]`, and mask==0 is the
object region `[E0_RESULTS.md §2.1]`.

**Secondary findings.**

- **Three distinct 4447-image HKU-IS pools, none identical** — authors' vs local mean maxdiff
  **232.3**, 0 of 200 stems identical in either pairing. Consequence stated in the source: *"the
  previous package's A3/B3/C1 embedded `LAKERED/output/HKU-IS/images` (local). **The old numbers
  therefore describe a pool the trained model never saw.**"* `[E0_RESULTS.md §2.4]` `[MEASURED]`
- **An arbitrary preprocessing choice moves 5.4% of cluster memberships** — squash-resize vs
  aspect-preserve + centre-crop agree on **94.6%** of assignments, mean cosine **0.9308**. Sets a
  floor: *"an effect smaller than ~5% of cluster membership cannot be attributed to targeting."*
  `[E0_RESULTS.md §1 s3, §2.6]` `[MEASURED]`
- **The authors' GT is not the raw GT** — 0 of 200 masks identical; foreground fraction differs by
  **+0.00542** `[E0_RESULTS.md §1 s2, §2.5]`. Cross-checked independently: LAKE-RED's own staging
  code measured background **0.8087** over all 4447 raw masks, corroborating the old package's
  **80.87%** from primary data `[E0_RESULTS.md §2.5]`.
- **Self-caught, twice: "a grep is not a provenance gate."** The first gate flagged 14 forbidden
  references, *all of them its own `FORBIDDEN` list and this package's prose*; the second version
  still failed on one — *"the note **explaining the fix** contained a path-like literal"*
  `[E0_RESULTS.md §2.7]`. Rewritten as an AST scan and verified **negatively** (a probe file is
  caught on all three counts; removing it returns the gate to zero), because *"a gate that has never
  failed is not evidence."*
- **Blocks 3 → 4 exist only to enforce traceability.** Block 3 was already 15 PASS / 0 FAIL, but
  four values used in the document existed only outside the log; block 4 promoted them into the
  script `[E0_RESULTS.md §5]`. The stated rule: *"a number that cannot be traced to a log block does
  not belong in a document, **even when the number is correct**."*

**Impact.** E0 supplies the paper's reproducibility claim and, more importantly, the **mechanism**
that makes the foreground-exhaustion argument literal rather than statistical: because `isReplace`
composites the source object pixels back in, a "new" synthetic image contains an object that is
already in the pool. Every downstream distributional claim (A3), every allocation-geometry claim
(C1), and the exhaustion claim (D1) rests on this. It also establishes that the render pool is not
an inherited artifact — the paper can state that its inputs are regenerable on demand. Its negative
contribution matters too: §2.4 shows the previous package's numbers described a pool the trained
model never saw, which is why every later experiment names its pool explicitly.

**Honest limits** — quoted verbatim from `## 4. What E0 does not establish`:

> - **No conclusions.** E0 produces inputs. It says nothing about whether targeting works.
> - **Sampling.** s2 polarity used 400 stems; other checks 50–200. These are existence and consistency
>   proofs. A2 measures the distribution over all 4447; D1 hashes every file.
> - **One seed.** s4 regenerated at `--seed 0` only. Generator variance across seeds is unmeasured.
> - **`cut` is never materialised.** Only its embeddings are cached, so re-verifying the cutout
>   representation means re-running s2, not inspecting images.
> - **The provenance gate is static.** It proves no script *references* a rescued path. It does not
>   prove, by execution with those paths removed, that no run would touch one.
> - **`clipL224` is present but unexercised.** The second embedder family is cached and ready; no
>   conclusion yet depends on it. Its value is realised in A3, B3 and C1.

Additionally, §2.2 scopes the reproducibility claim: *"this establishes reproducibility **on this
machine with this stack**, not determinism in general, across hardware, or across driver versions."*
**D2 §3.3 later adds a required qualifier E0 did not have** — see entry 2.

**Provenance.** `rebuild/E0/E0_RESULTS.md` (all sections) · `EXP E0` block #4 @
`results/REBUILD_LOG.txt:231` (authoritative; blocks #1–#3 at L29/L95/L163 retained deliberately).

---

# 2. D2 — benchmark contamination sweep

**What it tested.** Whether any evaluation endpoint contains images that also appear in the
training pool — not only as byte-identical copies, but as **re-encodes of the same photograph**. It
also tested, by a controlled generator experiment, whether a LAKE-RED render is a function of its
input.

**Headline result.** **41 of CHAMELEON's 76 images (53.9 %)** are the same photographs as Target
training images, re-encoded `[D2_RESULTS.md §1.4, §3.1 | EXP D2 #5 @ REBUILD_LOG.txt:600]`.
`[MEASURED]` Exact hashing returns **0** for CHAMELEON ∩ Target and is *correct at that level* — the
source's own framing: *"The number was right; the inference from it was not."* The declared
contamination threshold **FAILS**, and the FAIL is the finding.

### Table 2.1 — Endpoint contamination `[MAIN-TEXT CANDIDATE]`

*Source: `D2_RESULTS.md` §1.4, block `EXP D2` #5 @ `REBUILD_LOG.txt:600`.*
*Distinct endpoint images that are re-encodes of training data.*

| Endpoint | Contaminated | Share |
|---|---|---|
| COD10K test | **2/2026** | 0.1 % |
| **CHAMELEON** | **41/76** | **53.9 %** |
| NC4K | **1/4121** | 0.0 % |
| CAMO-val | **4/250** | 1.6 % |

### Table 2.2 — 41 is a property of the data, not of the cutoff `[MAIN-TEXT CANDIDATE]`

*Source: `D2_RESULTS.md` §1.4 (tolerance sweep and s4b gap analysis), block `EXP D2` #5 @
`REBUILD_LOG.txt:600`. Two instruments, independent of each other, landing on the same integer.*

| mean\|diff\| ≤ | 1.0 | 2.0 | 3.0 | 5.0 | 6.0 |
|---|---|---|---|---|---|
| CHAMELEON matched | **11/76** | **26/76** | **37/76** | **40/76** | **41/76** |

| Endpoint | Checkable | Gap in sorted nearest distances |
|---|---|---|
| COD10K test | **1502/2026** | **none** |
| **CHAMELEON** | **51/76** | **41 below 5.51, next at 40.58** |
| NC4K | **1715/4121** | **none** |
| CAMO-val | **95/250** | **none** |

D2 reports this jump as *"A 7.4x jump after exactly 41 images"*; D2R states it to three significant
figures as **7.36×** (entry 3). Same quantity, different precision — not a discrepancy.

### Table 2.3 — A render is not a function of (image, mask) `[APPENDIX CANDIDATE]`

*Source: `D2_RESULTS.md` §1 s8 (controlled) and §3.3, block `EXP D2` #5 @ `REBUILD_LOG.txt:600`.*
*Three byte-identical inputs, generated three ways.*

| s8 — controlled | Value |
|---|---|
| Inputs byte-identical | **True** |
| **T1** one shard, positions 0/1/2 → all differ | **True** |
| T1 mean\|diff\| A vs B | **36.738** |
| T1 mean\|diff\| B vs C | **40.338** |
| **T2** identical invocation, fresh output dir → reproduces bit-exactly | **True** |
| **T3** three shards, each input at local position 0 → all identical | **True** |
| T3 mean\|diff\| A vs B | **0.0** |

*"T3 is why this is a mechanism and not a correlation: a negative result is consistent with several
explanations, but only the position account predicts that equalising positions collapses the
divergence to exactly zero."* `[D2_RESULTS.md §3.3]`

**Secondary findings.**

- **Contamination does not bias the reported endpoint.** Removing the 7 exact COD10K duplicates
  changes MAE by **−1.242e-05** (**0.0167 %**); their mean percentile within the clean test set is
  **0.4761** `[D2_RESULTS.md §1, §3.5]`. *"no memorisation signature."* This **closes an escape
  route**: contamination is not a competing explanation for a null result on COD10K.
- **Self-caught error, and it is large.** D2's own first s4 reported CHAMELEON at **10/76 (13.2 %)**
  against the true **41/76 (53.9 %)** — *"roughly a quarter of the true count"* — because contrast
  normalisation destroyed the discriminative scale and hard bucket edges split true pairs
  `[D2_RESULTS.md §3.2]`. *"The first number was wrong and it was mine."* A second attempt was
  abandoned as computationally infeasible and replaced by s4b.
- **A correction to E0.** *"a static seed reproduces LAKE-RED" is right at the **run** level and
  wrong at the **image** level … **E0's headline needed this qualifier and did not have it**"*
  `[D2_RESULTS.md §3.3]`. Change `--shard_total`, or add or remove one input file, and every later
  index shifts.
- **E0's "unmeasured and unclaimed" seed variance is now measured** — re-rolling the noise on one
  fixed foreground moves the render by **~37–40** grey levels mean absolute `[D2_RESULTS.md §3.3]`.
- **A third independent confirmation of E0 §2.1**, from a direction E0 never used: in s7's clean pair
  the **object** region differs by **0.962** while the background differs by **41.667**
  `[D2_RESULTS.md §1 s7, §3.3]`.
- **All 5 old claims re-tested: 5 MATCH** `[D2_RESULTS.md §2]`. The source draws the inference that
  matters for how the whole rebuild is read: *"these were `[no code]` in the old package … yet every
  one is correct. The old defect was *provenance*, not arithmetic. Being unverifiable is not the same
  as being wrong."*
- **CAMO can never be an endpoint** — `MyTrain.py:221` defaults `--val_root` to
  `./Dataset/Val/CAMO/`, and that 250-image set is the published CAMO **test** split. Every
  checkpoint in every arm is selected on a test set; identical across arms, so it cannot bias B-vs-C
  `[D2_RESULTS.md §3.6]`.

**Impact.** D2 supplies the paper's Tier 3 result — the one that stands regardless of whether the
method worked. It removes CHAMELEON as a reportable endpoint outright (*"Not caveated — removed"*),
which is why no main table may carry a CHAMELEON column. It also supplies a second, quieter
contribution the paper should use: the **methodological** point that exact hashing is the wrong
instrument for contamination and returns a confidently clean answer, demonstrated on the authors'
own data and then re-demonstrated on D2's own first implementation. Finally §3.5 removes
contamination as a confound for the null on COD10K, and §3.3 supplies the render-determinism
mechanism that D1 needs to scope the exhaustion argument.

**Honest limits** — quoted verbatim from `## 5. What D2 does not establish`:

> - **Everything here is a lower bound on contamination.** Coverage is exact duplicates plus
>   same-dimension re-encodes. **Rescaled** copies are *not* covered — a duplicate saved at a different
>   resolution falls outside every dimension group and is invisible to this sweep. So are crops, flips,
>   colour shifts, and different photographs of one specimen. 25 of CHAMELEON's 35 unmatched images have
>   no same-dimension candidate at all and are therefore **unchecked, not clean**.
> - **The tolerance is a choice**, which is why §1.4 reports the sweep and s4b's gap analysis rather
>   than one number.
> - **s8 uses one source image** (`0004`) and three positions. It establishes the mechanism decisively —
>   T3 is a positive prediction — but the *magnitude* of noise-driven divergence rests on that one
>   foreground. B3 should characterise the distribution.
> - **No claim about GT masks.** D2 hashes images; whether endpoint *masks* are duplicated is not
>   measured.
> - **CHAMELEON is not checked against its own publication** — only against the copies on this disk.

The last bullet is the gap D2R was built to close — see entry 3.

**Provenance.** `rebuild/D2/D2_RESULTS.md` (all sections) · `EXP D2` block #5 @
`results/REBUILD_LOG.txt:600` (authoritative; blocks #1–#4 at L306/L372/L440/L514 retained). **Note a
doc/log count discrepancy — §16(b) item 1.**

---

# 3. D2R — the CHAMELEON re-audit against an author-sourced copy

**What it tested.** D2's own declared weakness: *"CHAMELEON is not checked against its own
publication — only against the copies on this disk."* D2R obtained an author-sourced CHAMELEON
release and re-ran D2's method against it, with every constant copied rather than re-chosen, plus
four checks D2 never ran (shortlist-depth sensitivity, a second independent re-encoding extraction,
mask-release reconciliation, and a difficulty-skew analysis).

**Headline result.** The finding survives and gets **larger in scope**: the author-sourced release is
**byte-identical** to the repo copy (**76/76** at both hash levels), every D2 figure reproduces
exactly, and the sharpened claim is **`CHAMELEON ∩ COD10K-train = 40/76`** — *"a fact about two
**public benchmarks**"*, not about this repository
`[D2R_RESULTS.md §1.1, §1.6, §3.1 | EXP D2R #4 @ REBUILD_LOG.txt:1844]`. `[MEASURED]`

### Table 3.1 — D2's CHAMELEON values re-tested against an author-sourced copy `[MAIN-TEXT CANDIDATE]`

*Source: `D2R_RESULTS.md` §2, block `EXP D2R` #4 @ `REBUILD_LOG.txt:1844`.*
*8 of 8 measurements reproduce; all 3 MISMATCHes are corrections to our own prior work.*

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

### Table 3.2 — No difficulty skew, so no inflation figure is claimed `[MAIN-TEXT CANDIDATE]`

*Source: `D2R_RESULTS.md` §1.7 (s5r-b, inference only), block `EXP D2R` #4 @ `REBUILD_LOG.txt:1844`.*
*The reading — percentile in [0.25, 0.75] means no skew — was pre-declared in `REAUDIT_PLAN.md`.*

| Mask set | All 76 | Clean 35 | Leaked 41 | Clean − All | Leaked percentile | Skew |
|---|---|---|---|---|---|---|
| Author-sourced, MAE | **0.219648** | **0.208234** | **0.229392** | **−0.011414** | **0.4481** | none |
| Author-sourced, Sα | **0.583363** | **0.601893** | **0.567545** | **0.01853** | **0.4606** | none |
| Repackaged GT, MAE | **0.081631** | **0.084573** | **0.079119** | **+0.002943** | **0.4948** | none |
| Repackaged GT, Sα | **0.724257** | **0.727781** | **0.721249** | **+0.003524** | **0.4934** | none |

**All eight percentiles land in 0.448–0.559**, and `split_direction_agrees_across_mask_sets` =
**False** — the sign of the score difference flips with the mask release `[D2R_RESULTS.md §1.7]`.

### Table 3.3 — The two CHAMELEON mask releases are different annotations `[APPENDIX CANDIDATE]`

*Source: `D2R_RESULTS.md` §1.8, block `EXP D2R` #4 @ `REBUILD_LOG.txt:1844`.*
*A second, independent reason a CHAMELEON column is not comparable across papers — unrelated to contamination.*

| Metric | Value |
|---|---|
| Author-sourced mask polarity | **object_black**, white fraction **0.7187** |
| Repackaged GT polarity | **object_white**, white fraction **0.1400** |
| Polarities agree | **False** |
| Mean IoU as stored | **0.0** |
| Mean IoU after polarity alignment | **0.6932** |
| Masks with aligned IoU ≥ 0.9 | **40/76** |
| Exactly identical after alignment | **27/76** |

On identical predictions, that mask-set disagreement alone moves MAE by **2.7×** (0.2196 against the
author masks, 0.0816 against the repackaged GT) `[D2R_RESULTS.md §1.8]`.

**Secondary findings.**

- **The claim is independence, not inflation — and the data forced that.** *"**What we expected to
  report:** 'by how much the column misleads' … **Measured:** nothing."* `[D2R_RESULTS.md §3.2]`
  `[PREDICTION REFUTED BY MEASUREMENT]`. The source names the sentence it refused to write:
  *"The tempting paper sentence — 'contaminated benchmarks inflate reported scores' — is not
  supported here, and the plan's pre-declared [0.25, 0.75] reading is what stopped us writing it."*
- **Threshold T5 is left FAILING and T5b added beside it.** `animal-19.jpg` and `animal-28.jpg` are
  **PNG files carrying a `.jpg` extension** (magic bytes `89504e47`), so they have no JPEG
  quantization table; D2 compared with `!=`, scoring a missing table as a differing one —
  *"absence of evidence read as evidence."* Result: **41/41 pairs carry independent re-encoding
  evidence** — 40 by quantization table, 1 by container format `[D2R_RESULTS.md §1.4, §3.3]`.
  *"Relaxing the wording after seeing the data would defeat the point of declaring it beforehand."*
- **The shortlist-depth sensitivity check, which could have overturned the finding, held.** Gap
  identical at depth 8 / 32 / every same-dimension candidate: **41 below 5.51, next at 40.58** in all
  three `[D2R_RESULTS.md §1.3]`. *"This was the result most able to overturn the finding, and it
  held."*
- **We adopted an endpoint the repository never sanctioned.** `README.md` mentions CHAMELEON exactly
  once, inside the `Source (Synthetic)` CNC bundle; `Experiments/REPRODUCE_TABLE1_v2.md` has **0**
  mentions and `Result/**` holds **0** CHAMELEON predictions `[D2R_RESULTS.md §1.10, §3.5]`. The
  source refuses the flattering framing: *"the framing is **not** 'we found a bug in their
  evaluation' … it was **our own** rebuild plan that promoted it to a secondary endpoint without
  checking."*
- **The released detector is checkable by strangers.** `detect_contamination.py` passes an
  8-assertion synthetic known-answer self-test with no repository data, reproduces the canonical pair
  list at **41/41** pairs and **41/41** names, and found **1** extra pair (the second partner of the
  image that has two). The release bundle passes a 12-pattern anonymisation scan with **0** hits
  `[D2R_RESULTS.md §3.6]`.
- **Blocks 3 → 4 were again traceability only** — *"No value changed … six numbers were promoted from
  artifact to metric"* `[D2R_RESULTS.md §6]`.

**Impact.** D2R converts D2's finding from a claim about one repository's disk into a claim about
two public benchmarks, which is what makes it publishable independently of the method under test. It
also supplies the paper's most disciplined moment: the inflation figure the story wanted was
pre-declared unreportable and then *was* unreportable, and this is recorded rather than quietly
dropped. §1.8 adds a second, entirely separate reason to distrust published CHAMELEON columns (the
mask releases disagree at IoU 0.693 and move MAE 2.7×), which does not depend on contamination at
all. The released detector plus `CLEAN_PROTOCOL.md` turn the finding into a reusable artifact.

**Honest limits** — quoted verbatim from `## 5. What D2R does not establish`:

> - **Every count remains a lower bound.** Coverage is exact duplicates plus
>   same-dimension re-encodes. Rescaled copies that leave every dimension group, crops,
>   flips, colour shifts, and different photographs of one specimen are **not** detected
>   and are not claimed. **25 of the canonical 76** have no same-dimension training
>   candidate at all and are therefore **unchecked, not clean**.
> - **No inflation figure.** §1.7 measures no difficulty skew and the sign flips with the
>   mask set, so "the column is inflated by X" is not available from these data.
> - **No claim about the published paper.** Whether S2R-COD reports a CHAMELEON column is
>   `UNVERIFIED` — the PDF is not in this checkout.
> - **No literature survey.** That any *specific* published method's CHAMELEON column is
>   affected follows only from the measurement plus that method's training set. D2R
>   measures the datasets, not the literature.
> - **COD10K-test, NC4K and CAMO are not author-verified.** Their rates come from the
>   copies on this disk — the exact weakness this re-audit closed for CHAMELEON alone.
> - **The provenance direction is inference.** CHAMELEON (2015) predates COD10K (2020), so
>   COD10K-train absorbing CHAMELEON is the parsimonious reading; only pool membership is
>   measured.
> - **s5r-b is inference, not an endpoint result.** It exists solely to test for a
>   difficulty skew and must never be quoted as a CHAMELEON performance number.

**Provenance.** `rebuild/D2_reaudit/D2R_RESULTS.md` (all sections) · `EXP D2R` block #4 @
`results/REBUILD_LOG.txt:1844` (authoritative; blocks #1–#3 at L1484/L1627/L1694) ·
`rebuild/D2_reaudit/CLEAN_PROTOCOL.md` for the protocol table.

---

# 4. D2_NC4K — is NC4K contaminated by the COD10K test split?

**What it tested.** A *different mechanism* from D2/D2R. The S2R-COD paper's Task Setup Case 3
describes the NC4K evaluation as introducing synthetic images derived from the COD10K **test** set
into the **source** domain. If NC4K overlapped COD10K-test, that injection would place synthetic
renderings of NC4K's own test photographs into supervision — a **source-into-test** collision, where
the CHAMELEON finding was target-side and unlabeled. A null was pre-declared to be a reportable
result.

**Headline result.** A **clean null, with a margin**. NC4K ∩ COD10K-test is empty at every level
measured: **0** byte, **0** pixel, and **0/4121** same-dimension re-encoded duplicates; the closest
any NC4K image gets to COD10K-test is **20.610** grey levels, **3.44×** the 6.0 confirmation
tolerance `[EXP D2_NC4K #2 @ REBUILD_LOG.txt:2074]`. `[MEASURED]`

**No table is worth showing from the result document** — `rebuild/D2_nc4k/README.md` states
outright: *"**No measured number appears in this file.**"* It is a setup document. Every number
below is therefore quoted from the log block or from `CLEAN_PROTOCOL.md`.

### Table 4.1 — NC4K against both COD10K splits `[APPENDIX CANDIDATE]`

*Source: block `EXP D2_NC4K` #2 @ `REBUILD_LOG.txt:2074` (metric names as logged).*
*Thresholds are inverted here: **PASS means no collision**.*

| Metric | vs COD10K-**test** | vs COD10K-**train** |
|---|---|---|
| Intersection, file-byte level | **0** | **0** |
| Intersection, decoded-pixel level | **0** | **0** |
| Same-dimension re-encoded duplicates | **0/4121 (0.0%)** | **0/4121 (0.0%)** |
| Shortlisted candidates | **1** | **0** |
| Confirmed at mean\|diff\| ≤ 6.0 | **0** | **0** |
| Checkable | **1082/4121** | **1166/4121** |
| Unchecked | **3039/4121** | **2955/4121** |
| Unchecked share | **73.7%** | **71.7%** |
| Gap in sorted nearest distances | **none** | **none** |
| Minimum nearest distance | **20.610** | **17.190** |
| — as a multiple of the tolerance | **3.44x** | **2.87x** |
| Nearest-distance deciles (p10 p25 p50 p75 p90) | **43.0 50.9 59.3 68.3 79.2** | **41.4 48.8 56.3 65.8 74.7** |
| Tolerance sweep 1/2/3/5/6 | **0/4121** at every tolerance | **0/4121** at every tolerance |

All eight declared thresholds `T1`–`T8` record `-> PASS`.

**Secondary findings.**

- **The null is quantitative by design, not a bare absence.** The minimum nearest distance and the
  decile spread were pre-declared as required outputs precisely so that *"'no collision' carries a
  margin instead of being a bare absence"* `[D2_nc4k/README.md §6]`.
- **Method identity is by import, not by inspection.** The script imports
  `rebuild/D2_reaudit/detect_contamination.py` — *"the same module that produced the committed 41/76
  CHAMELEON result"* — so the descriptor, shortlist, confirmation rule, tolerance sweep and gap rule
  *"are therefore identical by construction rather than by inspection"* `[EXP D2_NC4K #2 NOTES]`.
  This is the strongest form the cross-experiment consistency argument takes anywhere in the suite.
- **Gap verdict is invariant to shortlist depth** — `none` at topk 8 / 32 / all, min nearest
  **20.610** in each `[EXP D2_NC4K #2]`.
- **Context, not a claim about intent.** The block states explicitly: *"Whether the paper's Case 3
  text describes a leak is a question about the measured overlap; this block reports the overlap and
  does not attribute intent."*
- **Blocks 1 → 2 were traceability only** — two figures `CLEAN_PROTOCOL.md` quotes existed only as
  arithmetic over logged values; *"They are promoted here. No measured value changed."*

**A distinction that must not be collapsed.** D2's committed NC4K rate is **1/4121** measured
against the **full Target training pool**; D2_NC4K's is **0/4121** measured against **COD10K-train**
(the 3040 `COD10K-CAM-*` files only — *"the other 1000 files in Target/Image are CAMO and are
excluded from that side by construction"*) and **0/4121** against **COD10K-test**. These are three
different axes. `CLEAN_PROTOCOL.md` keeps them distinct: *"**1 / 4121 (0.0 %)** vs the training
pool; **0 / 4121** vs COD10K-test"*.

**Impact.** This is the negative control that makes the CHAMELEON result credible. The same
detector, imported rather than re-implemented, returns a clean null with a quantified margin on a
benchmark where the paper's own described protocol gave reason to expect a problem. Without it, a
reviewer could ask whether the method finds contamination everywhere it looks; with it, the answer
is measured. It also lets the paper report an NC4K column without a contamination caveat beyond the
lower-bound one that applies to every row.

**Honest limits** — quoted verbatim from `## 6. Scope, declared in advance`
(`rebuild/D2_nc4k/README.md`):

> - **Every count is a lower bound.** Coverage is exact duplicates plus same-dimension
>   re-encodes. Rescaled copies that land outside every dimension group, crops, flips,
>   rotations, colour shifts and different photographs of one specimen are **not**
>   detected and are **not** claimed.
> - **Unchecked is not clean.** An NC4K image with no same-dimension candidate on the
>   other side cannot be compared at all. That count is logged for both comparisons
>   rather than folded into a clean rate — and for this pair of sets it is large.
> - **A null is quantitative here.** The minimum nearest distance and the decile spread
>   of the nearest-distance distribution are logged, so "no collision" carries a margin
>   instead of being a bare absence.
> - **No claim about intent.** The block reports the measured overlap. Whether Case 3's
>   described injection amounts to a leak follows from that measurement plus the paper's
>   own text; this experiment supplies the measurement.
> - **No mask claim.** GT directories are hashed for provenance. Whether NC4K and
>   COD10K-test *masks* overlap is not measured.

The unchecked share is the binding limit here: **73.7%** of NC4K cannot be compared at all against
COD10K-test.

**Provenance.** `EXP D2_NC4K` block #2 @ `results/REBUILD_LOG.txt:2074` (authoritative; block #1 at
L2006) · `rebuild/D2_nc4k/README.md` (setup and declared scope **only** — contains no measured
numbers) · `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` (protocol table row).

---

# 5. D1 — foreground exhaustion

**What it tested.** Whether Stage C can generate a *new foreground*, or only new backgrounds for
foregrounds it already has. It traced every render back to a source foreground, over every file of
both render pools, and measured whether the mapping is literal at the pixel level.

**Headline result.** The render set is a **bijection** onto the raw foreground set — **4447/4447**
trace in, **0** outside, **0** base foregrounds unrendered — and the same holds for the **authors'
pool, the one training actually reads** `[D1_RESULTS.md §1, §3.1 | EXP D1 @ REBUILD_LOG.txt:696]`.
`[MEASURED]` Exhaustion is an **identity statement about pixels**, not a distributional argument:
**0** of 8885 traced objects across both pools show any sign of having been regenerated.

### Table 5.1 — The bijection, and whether the mapping is literal `[MAIN-TEXT CANDIDATE]`

*Source: `D1_RESULTS.md` §1 ("The bijection" and "Is the mapping literal?"), block `EXP D1` @
`REBUILD_LOG.txt:696`. All 4447 of both pools, each scored against its own mask.*

| Metric | local renders | authors' pool |
|---|---|---|
| Mask used | `raw_gt` | `auth_gt` |
| Traced OK | **4447/4447** | **4447/4447** |
| Object region mean\|diff\| | **6.003** | **12.163** |
| Object **interior** mean\|diff\| | **5.603** | **9.633** |
| Background mean\|diff\| | **70.802** | **70.555** |
| Ratio on the interior | **12.64** | **7.32** |
| Images with interior 3× closer | **4442/4443** | **4361/4442** |
| **Objects plausibly REGENERATED** (interior > 40) | **0** | **0** |

| Bijection metric | Value |
|---|---|
| Base foreground files | **4447** |
| Renders tracing to the base pool | **4447/4447** |
| **Renders whose foreground lies OUTSIDE the base pool** | **0** |
| Base foregrounds with no render | **0** |
| Render set is a bijection onto the base set | **True** |
| Authors' pool is a bijection onto the base set | **True** |

### Table 5.2 — Per-pool distinctness `[APPENDIX CANDIDATE]`

*Source: `D1_RESULTS.md` §1, block `EXP D1` @ `REBUILD_LOG.txt:696`. Reconciles with D2 exactly
(`reconciles_with_D2 = yes`).*

| Pool | Unique / files | Redundant | What it is |
|---|---|---|---|
| raw HKU-IS | **4443/4447** | 4 | the original photographs — the foreground source |
| authors' pool | **4447/4447** | 0 | **what `MyTrain.py` reads** |
| local renders | **4445/4447** | 2 | our local LAKE-RED re-generation |

**Secondary findings.**

- **The revised phrasing D1 adopts is the one the paper should use:** *"the foreground pool is
  exhausted; the background is not."* `[D1_RESULTS.md §3.3]` This is *"a materially different and
  more useful statement than 'additions are re-renders'"*, and it survives D2's position qualifier —
  the freedom a render has is entirely in the background.
- **D2's prediction held 4/4** — a render is a function of (foreground, mask, position-in-shard)
  `[D1_RESULTS.md §3.3]` `[PREDICTION CONFIRMED BY MEASUREMENT]`.
- **Old claim MISMATCH, and it strengthens the conclusion.** *"All 4447 foregrounds already in base
  pool"* was written as **4447 distinct**; measured, it is **4443** distinct in raw, 4447 *files*.
  *"there are **fewer** distinct foregrounds than claimed, so the pool is more exhausted, not less"*
  `[D1_RESULTS.md §2]`. Reporting rule: *"'4447 distinct foregrounds' must not be written."*
- **Self-caught measurement fix.** The first run scored **both** pools against `raw_gt` and found
  only **4041/4447** authors'-pool images with the object 3× closer. The cause was the mask choice,
  not the data: the authors' pool was rendered with the authors' GT. *"the apparent 406-image
  discrepancy was an artifact of my mask choice … Recorded because the first number was wrong and it
  was mine"* `[D1_RESULTS.md §3.4]`. Both earlier runs used `--no-log`, so no superseded block
  exists — and §6 states the rule distinguishing that from a post-logging defect.
- **Mask polarity measured over every file of every set**, not assumed: `raw_gt` **0.19132**,
  `auth_gt` **0.18557**, `local_msk` **0.19132**, `lr_in_mask` **0.80868** (inverted)
  `[D1_RESULTS.md §1]`. The 0.00575 difference between `raw_gt` and `auth_gt` is flagged in the
  source itself as *"derived from the two logged values"* — an in-document derivation, disclosed.
- **E0's manifest consumed, not recomputed** — **301/301** hashes verified on a sample
  `[D1_RESULTS.md §1]`.

**Impact.** D1 is the experiment that makes the paper's foreground-exhaustion cause a *fact about
pixels* rather than an argument about distributions. That distinction is what makes the cause
defensible: *"'The added images look similar to existing ones' invites a counter-argument about
whether similarity is enough. 'The added images contain the same object pixels' does not."* It also
supplies the scope sentence the entire null inherits — evidence about targeting under an exhausted
foreground pool — and it verifies the property on the **authors' pool**, closing the objection that
the argument was made about the wrong data.

**Honest limits** — quoted verbatim from `## 5. What D1 does not establish`:

> **The single most important one:** D1 does **not** establish that *new foregrounds could not help*. It
> bounds only what this pipeline can add from its fixed pool. Any null result inherits that scope
> exactly — it is evidence about targeting under an exhausted foreground pool, and it is silent on
> whether a larger or more diverse foreground set would change the outcome. Stating the null more
> broadly than that would be unsupported.
>
> Also not established:
>
> - **Near-duplicate foregrounds within the pool.** D1's distinctness is byte-level. Two visually
>   near-identical but non-identical foregrounds count as two distinct foregrounds. D2's near-duplicate
>   machinery was not applied *within* the raw pool, so 4443 is an upper bound on distinct objects.
> - **That background variation is useless.** D1 shows the object pixels are fixed. Whether varying the
>   background alone can move accuracy is B3's and C1's question, not answered here.
> - **Anything about the masks as labels.** D1 asserts mask polarity and uses masks to define regions. It
>   does not check whether the GT masks themselves are correct or duplicated.
> - **Single-file drift.** s1 verified 301 sampled hashes, which detects wholesale change, not one
>   altered file among the seven sets D1 reads.
> - **A mechanism for the 8 high-error images** seen in the first run. After the mask fix none exceed the
>   cutoff, so no exception is claimed — but no positive explanation for those particular images is
>   offered either.

**Provenance.** `rebuild/D1/D1_RESULTS.md` (all sections) · `EXP D1` @ `results/REBUILD_LOG.txt:696`
(the only block; all ten declared thresholds PASS). **Carries an uncorrected citation — §16(b)
item 3.**

---

# 6. A1 — the generator conditioning channel

> **`[NO EXPERIMENT RUN — RESOLVED BY SOURCE READING; NO LOG BLOCK]`**
> `rebuild/A1/A1_SCOPING.md` states it directly: *"No experiment was written and none was run … **No
> number in this document enters `results/REBUILD_LOG.txt`.**"* There are **zero** `EXP A1` blocks.
> Everything in this entry is a source-reading result, and the one quantitative figure is marked
> `[NOT IN COMMITTED LOG BLOCK]`.

**What it tested.** Whether the LAKE-RED generator's conditioning channel is a bottleneck — the
standing account being that foreground information reaches the regenerated background only through a
narrow 48-scalar summary. A1 was planned as a runtime experiment (`A1-T` / `A1-P`) but was resolved
before it was written, because static reading of the architecture settled it.

**Headline result.** The narrow-channel account is **refuted as stated**, by source reading rather
than by measurement. There are **four** routes by which foreground information reaches the
regenerated background region; exactly one is the 48-scalar summary, and *"The largest is one the
existing plan does not mention: the full-resolution foreground latent is handed to the UNet directly,
and the UNet is globally connected by spatial self-attention"* `[A1_SCOPING.md §0]`.
`[PREDICTION REFUTED BY SOURCE READING — NOT A MEASUREMENT]`

**No paper-ready table.** A1 produced no logged metrics, so it yields no table. The key inline
figures, both from source reading:

- **Four routes**, of which the 48-scalar summary is one; the UNet applies *"unmasked global spatial
  self-attention at three resolutions plus its middle block (`openaimodel.py:318-324,541,606`;
  `attention_resolutions: [8,4,2]`)"* `[A1_SCOPING.md §6(a)]`.
- The `fuse` 1×1 convolution (`ddpm.py:1587`) admits the raw `fg` latent into every regenerated
  position *"with a **larger** learned weight norm than the 48-scalar summary receives (0.907 vs
  0.810, ratio 1.12, measured from the released checkpoint)"* `[A1_SCOPING.md §6(a)]`
  `[NOT IN COMMITTED LOG BLOCK]` — read by a `torch.load` of `LAKE-RED/ckpt/LAKERED.ckpt`, which the
  document classes as read-only code execution that produced no logged metric.
- **The decisive check the plan named is the wrong check.** *"'whether the foreground tensor is
  identically zero under the mask' … is (a) architecturally unsatisfiable, and (b) not sufficient
  even if it held, because the dominant route bypasses the tensor it inspects"* `[A1_SCOPING.md §0]`.

**Secondary findings.**

- **Two tempting claims were deliberately kept out.** *"Two claims were **deliberately kept out** of
  the paper as unsupported by static reading: that the generator is 'not the binding constraint', and
  that it is *steerable*. Static reading shows the channel is not narrow; it does not show the
  capacity is used"* `[A1_SCOPING.md outcome box]`. This is a self-imposed limit on a result that
  could easily have been stated more strongly.
- **The pre-registered confirm condition was unsatisfiable.** *"`REBUILD_PLAN.md:250-251`'s confirm
  condition is unsatisfiable (§3.2)"* — *"A1 as currently planned can only ever return 'refuted'"*
  `[A1_SCOPING.md §3.3 note, §6(d)(4)]`. The document argues for *"amending the plan explicitly and
  dating the amendment, not silently substituting a different check."*
- **Generator-source provenance is weak by construction.** `LAKE-RED/` is untracked in this
  repository, so *"Every `file:line` below is therefore a citation into a working-tree file, not a
  committed artifact"*; the nine cited sources are pinned only by
  `rebuild/A1/out/a1_source_manifest.sha256`, which A1 itself records `[A1_SCOPING.md preamble]`.
- **`[DEFERRED]` — still open**, quoted: *"Still open: decisions (d)(3)–(d)(6) in §6, and whether §3
  (A1) of `REBUILD_PLAN.md` receives a dated amendment for its unsatisfiable pre-registered confirm
  condition."*

**Impact.** A1's contribution to the paper is a **withdrawal**, and withdrawals of one's own
candidate explanations are credibility assets. A conditioning bottleneck was a plausible and
convenient cause for the null; A1 removes it, which makes the remaining causes carry more of the
account rather than less. It also demonstrates the suite's willingness to kill a hypothesis by
reading the source rather than by running an experiment that would have produced a number. Two
things temper it: the refutation is **not a measurement**, and A1 explicitly declines to claim the
generator is therefore adequate.

**Honest limits** — quoted verbatim from `### 4.3 What A1 cannot establish, even if perfectly
executed`. Note these were written for the experiment that was **never run**, so they bound the
strongest form A1 could have taken:

> 1. **It bounds the architectural channel, not the training benefit.** A1 says how much foreground
>    information *can* reach the background. It says nothing about whether a *richer* conditioning
>    interface would have improved anything — that would require retraining the generator with a wider
>    interface and re-running the loop, which is a separate and untested question.
> 2. **It does not measure whether the capacity is used semantically.** A non-zero background MAE shows
>    foreground content perturbs the output. It does not show the generator uses that content to
>    *adapt the background to the object*. Those are different claims and A1 can only reach the first.
> 3. **It does not license the converse.** Even the "binds" outcome would not show the bottleneck
>    *caused* the null result in §5; it would only make the bottleneck a viable explanation. The
>    paper's "plausible but unverified cause" framing must survive in weakened form either way.
> 4. **It says nothing about the checkpoint's training regime.** `bg_embed` is a learned buffer of
>    8192 entries (§2.2); whether it is well-used, collapsed, or near-random is a separate probe that
>    A1 should not silently fold in.
> 5. **Generator-source provenance.** `LAKE-RED/` is untracked here, so A1's citations are pinned only
>    by the hashes A1 itself records (§5).

**Provenance.** `rebuild/A1/A1_SCOPING.md` (outcome box, §0, §4.3, §6) · **no `EXP A1` log block
exists** · `rebuild/A1/out/a1_source_manifest.sha256` (source pinning only, not a metric artifact).

---

# 7. A3 — where the synthetic images sit relative to the real target

**What it tested.** How far the LAKE-RED output distribution sits from the real target distribution,
and — critically — whether the metric the original used to answer that question can answer it at
all. A3 re-tested the old package's pinned values and added the identity-preserving control sweep the
original never ran.

**Headline result.** Two findings, and the second disqualifies the first's metric.
**(i)** The pre-declared decision metric passes: the paired coverage delta shows synthetic pools
losing **24–83 %** of recall against the target manifold relative to LAKE-RED's **own input pool**,
`T1` PASSING **3/3** in both pools `[A3_RESULTS.md §1.2]`. **(ii)** The declared vacuity flag `T6`
**FIRED**: re-encoding the *identical* target images at JPEG-30 separates them from themselves at
**0.9928** in `clipL224` — above the 0.90 trigger, above both genuine real-vs-real controls, and
**0.0067** short of the real-vs-LAKE-RED headline `[A3_RESULTS.md §0, §1.3]`. `[MEASURED]`
The source's own summary: ***"The finding survives; the metric that used to carry it does not."***

### Table 7.1 — The full coverage ladder `[MAIN-TEXT CANDIDATE — strongest single exhibit]`

*Source: `A3_RESULTS.md` §1.2, from `out/a3_coverage.csv`; block `EXP A3` @ `REBUILD_LOG.txt:2147`.*
*Recall at k = 5 against the target manifold.*

| set | `dinoL224` | `dinoL518` | `clipL224` | what it is |
|---|---|---|---|---|
| ceiling, random halves | 0.9332 | 0.9431 | 0.8931 | the target against itself |
| COD10K 3040 vs CAMO 1000 | 0.8898 | 0.9003 | 0.8730 | two real datasets *inside* the target |
| **NC4K** | **0.8874** | **0.8995** | **0.7921** | a genuinely **different real** camouflage set |
| raw HKU-IS | 0.7473 | 0.7097 | 0.7470 | real photographs, a **different genre** |
| **authors' pool** | **0.4829** | **0.4834** | **0.1277** | synthetic |
| **local renders** | **0.4668** | **0.5421** | **0.1349** | synthetic |

*"**raw photographs of the wrong genre still cover the target better than the synthetic images
generated from those very photographs.** Coverage discriminates where AUC cannot."*

### Table 7.2 — The AUC ladder, and the floor that overtakes the controls `[MAIN-TEXT CANDIDATE — the vacuity exhibit]`

*Source: `A3_RESULTS.md` §1.3; block `EXP A3` @ `REBUILD_LOG.txt:2147`.*
*Held-out linear-probe AUC, stratified 70/30, CLS token, L2 at use time.*

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

*"In `dinoL224` the JPEG-30 floor (0.8509) **exceeds** the NC4K control (0.8040). In 2 of 3 spaces the
floor outranks a genuine comparison between two different real datasets."*

### Table 7.3 — The paired coverage delta, the pre-declared decision `[MAIN-TEXT CANDIDATE]`

*Source: `A3_RESULTS.md` §1.2; block `EXP A3` @ `REBUILD_LOG.txt:2147`. Anchor k = 5, declared in
advance. `T1` required ≥ 2 of 3 at ≥ 15 % relative loss; it PASSES **3/3 for both pools**.*

| embedder | raw HKU-IS *(LAKE-RED's own input)* | authors' pool | local renders | **auth rel. loss** | **local rel. loss** | ceiling |
|---|---|---|---|---|---|---|
| `dinoL224` | 0.7473 | 0.4829 | 0.4668 | **−35.4 %** | **−37.5 %** | 0.9332 |
| `dinoL518` | 0.7097 | 0.4834 | 0.5421 | **−31.9 %** | **−23.6 %** | 0.9431 |
| `clipL224` | 0.7470 | 0.1277 | 0.1349 | **−82.9 %** | **−81.9 %** | 0.8931 |

### Table 7.4 — The old effect size, and its disqualification on a true null `[APPENDIX CANDIDATE]`

*Source: `A3_RESULTS.md` §1.5; block `EXP A3` @ `REBUILD_LOG.txt:2147`.*
*Two random halves of one dataset, where by construction there is nothing to find.*

| on the true null | `dinoL224` | `dinoL518` | `clipL224` |
|---|---|---|---|
| old estimator: probe axis, in-sample | **0.6867** | **0.6805** | **0.4854** |
| same axis, held out | 0.0318 | 0.0224 | 0.0889 |
| C1's mean-difference, held out (`T7`) | −0.0783 | −0.0716 | −0.0951 |
| C1's mean-difference, in-sample | +0.4015 | +0.4024 | +0.3031 |

**The old 4.67 reproduces at 4.658**, so *"the supersession is not concealing a failure to
reproduce"*; held out, the effect is **+3.103 / +2.709 / +4.267** `[A3_RESULTS.md §1.5]`.

**Secondary findings.**

- **18 of the old package's pinned values re-test clean and none mismatches** — *"18 MATCH, 4 NEW, 1
  SUPERSEDED, 1 NOT-REPRODUCIBLE — and 0 MISMATCH"* `[A3_RESULTS.md header]`.
- **The target set separates from itself.** `Dataset/Target/Image` is a two-dataset mixture —
  **3040 COD10K + 1000 CAMO = 4040** — separating at **0.8648 / 0.8592 / 0.9225**. *"That, not
  chance, is the bar a 0.999 headline has to clear."* The old package's version of this number
  (0.8888) was filed as a bug in its own null control, and its split was not even clean
  `[A3_RESULTS.md §1.1]`.
- **An independent replication, free.** The authors' pool had never been probed; probed now it lands
  within **0.0006** of the local pool in all three spaces, and E0 measured the two as genuinely
  different samples (0 of 200 identical, mean maxdiff 232.3) `[A3_RESULTS.md §1.1]`.
- **A cross-check on C1.** The old estimator *"manufactures ≈ 0.65 of *d* from nothing, reproducing
  C1's independently measured in-sample null of **+0.6991** to two decimals against its held-out
  **−0.1328**"* `[A3_RESULTS.md §1.5]`.
- **MMD² is the crispest statement of the failure.** *"A probe separates two encodings of one
  photograph at 0.9928 while MMD² between them is 0.000054"* — three to nine times smaller than
  between two real datasets `[A3_RESULTS.md §1.4]`. Note the source flags that five ratios in that
  section are *"computed in this file from the logged values"*, an in-document derivation disclosed
  inline.
- **What LAKE-RED does is narrow, not merely shift.** Effective rank falls **243.3 → 193.2**
  (`dinoL224`, raw → local) while precision *rises* (**0.6490 → 0.6886**) as recall collapses: *"The
  generator buys a little proximity by discarding a great deal of variety"* `[A3_RESULTS.md §3]`.
- **A relabelling that changes the argument.** The old A3 called `tgt` vs `raw` *"two ordinary
  different datasets"*; `raw` is LAKE-RED's **own input pool**, so that row is the paired baseline.
  Mislabelled, *"it both overstated the vacuity argument and discarded the most informative
  comparison in the experiment"* `[A3_RESULTS.md §1.3]`.
- **Threshold `T8` FAILED and stays failed.** It required in-sample *d* on random halves > **0.50**;
  measured **0.4015 / 0.4024 / 0.3031** `[A3_RESULTS.md §5]`. It was also *"declared on the wrong
  arm"*. Per C1 R14, *"the declared threshold is reported FAILED rather than relaxed or re-pointed"*,
  and the agreeing measurement (0.6867) is reported beside it as an **observation**, never promoted
  to a replacement threshold. Logged as `REVISION_TABLE.md` **R23**.
- **`[NOT-REPRODUCIBLE]`** — *"`dinoB/224` has no rebuild cache, so one of the original's three *d*
  sub-values (4.61) has no counterpart and is logged `NOT-REPRODUCIBLE` rather than substituted"*
  `[A3_RESULTS.md §7]`.

**Impact.** A3 gives the paper two distinct contributions. The first is the coverage result, which is
the only measurement in the suite that speaks to synthetic-vs-real distance **and does not depend on
statistical power** — the source makes exactly this argument about why it matters given ABC's
underpowering. The second is methodological and travels furthest: a real-vs-synthetic linear-probe
AUC near 1.0 is **near-vacuous**, demonstrated by a control in which the two sets are the same
photographs at a different JPEG quality. That is a criticism of a metric in wide use, established on
this data but not specific to it. The comparative framing — real-of-the-wrong-genre covers the target
better than synthetic-from-those-very-photographs — is the publishable form.

**Honest limits** — quoted verbatim from `## 6. What A3 does NOT establish`:

> **A3 is a distributional characterization, not a training-utility bound.** A distant or low-coverage
> synthetic set can still improve a model, and in the ABC campaign the arm means rose *monotonically* in
> all four architecture × endpoint cells. A3 supplies a candidate mechanism **consistent with** the
> absence of a resolvable gain. It does not demonstrate that no gain exists, and writing it as
> "the distribution is far, therefore no amount of it can help" would be a non-sequitur.
>
> **Why it still carries weight.** A3 is deterministic over fixed vectors — no seeds, no σ̂. The ABC
> campaign is underpowered against its own pre-registered statement (`2σ̂ = 0.017933` on the primary
> endpoint, larger than the 0.0142 gap the design declared it could half-resolve), so ABC's null cannot
> stand alone. A3 is the only measurement in the rebuild that speaks to synthetic-vs-real distance and
> does not depend on power.

And from `## 7. Limitations, declared`, the load-bearing ones:

> - **k-NN precision/recall is a manifold *estimate*.** It depends on `k` — swept over 3/5/10/20, with
>   the anchor declared in advance — and on L2 normalisation, which is applied and is **our stated
>   choice**; the original sources never said whether they normalised.
> - **MMD is kernel-dependent** (degree-3 polynomial) and carries no threshold. A Fréchet distance was
>   considered and **declined**: at n ≈ 4000 with d = 1024 a 1024×1024 covariance rests on roughly four
>   samples per dimension. The absence is a choice, not an oversight.
> - **The NC4K control's cleanliness is scoped to the COD10K axis.** D2_NC4K measured NC4K against the
>   3040 COD10K-train images; the 1000 CAMO images in the target set were not part of that check.
> - **The identity-preserving floors sweep two dimensions only** — JPEG quality and a luminance shift.
>   Other corruptions are untested, so 0.9928 is a lower bound on how high a floor can reach.
> - **`dinoB/224` has no rebuild cache**, so one of the original's three *d* sub-values (4.61) has no
>   counterpart and is logged `NOT-REPRODUCIBLE` rather than substituted.
> - **Three reporting metrics were added after an exploratory `--no-log` pass** on one embedder space:
>   the old estimator's behaviour on the true null, the in-sample inflation gap, and the
>   floor-versus-real-control comparison. Disclosed per C1 R15. All three are **metrics, not
>   thresholds** — no declared threshold was added, weakened or removed after seeing data, and all
>   three are recomputable from the committed probe table.
> - **A sub-chance AUC on a floor row means "no signal", not "inverted signal."** When two sets carry
>   identical content the probe fits noise in the training half and generalises worse than chance
>   (JPEG-90 reaches 0.2826 in `dinoL224`).

**Provenance.** `rebuild/A3/A3_RESULTS.md` (all sections) · `EXP A3` @
`results/REBUILD_LOG.txt:2147` (the only block; 14 of 15 thresholds PASS, `T8` FAIL retained) ·
artifacts `out/a3_coverage.csv`, `out/a3_probe_table.csv`.

---

# 8. B1 — does the ES uncertainty signal predict endpoint error?

> **Structural note.** `B1_RESULTS.md` is **three stacked documents** with independent section
> numbering, each reading a different log block: doc 1 (`## 1`–`## 8`) → block #2; doc 2
> (`## C1`–`## C7`, the embedder sweep) → block #3; doc 3 (`## D1`–`## D6`, the allocation signal) →
> block #4. **Doc 3 partially overturns doc 1**, so doc 1 must not be quoted alone. The header's
> claim that "the log holds two `EXP B1` blocks" is stale for the file as a whole — see §16(b) item 4.

**What it tested.** Whether the ES (student–teacher disagreement) signal that Stage C allocates by
actually predicts endpoint error, and if so which *kind* of error — pixel-average (MAE) or structural
(Sα, IoU). Doc 3 then asked the question doc 1 had got wrong: whether the *target-side* ES available
at allocation time behaves like the *endpoint-side* ES the first blocks measured.

**Headline result — and it moves between documents.** ES predicts pixel error roughly **twice** as
strongly as structural error: per-cluster ρ(MAE) **+0.8553** ± 0.0264 against ρ(1−Sα) **+0.4276**
± 0.0461 at k=75 `[B1_RESULTS.md §1 | EXP B1 #2 @ REBUILD_LOG.txt:840]`. `[MEASURED]`
**But doc 3 establishes that the committed blocks measured the wrong ES**, and on the real allocation
signal the ratio is **0.5166 / 0.5463** — *above* the declared 0.5 boundary, i.e. **not**
"wrong objective" `[B1_RESULTS.md §D2, §D3 | EXP B1 #4 @ REBUILD_LOG.txt:990]`.
`[PREDICTION REFUTED BY MEASUREMENT]`

### Table 8.1 — The faithful correlation: target ES → endpoint error `[MAIN-TEXT CANDIDATE — the corrected headline]`

*Source: `B1_RESULTS.md` §D2, block `EXP B1` #4 @ `REBUILD_LOG.txt:990`. Both quantities aggregated
over the **same** cluster partition, so the comparison is not confounded.*

| Space | k | clusters | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) | ratio |
|---|---|---|---|---|---|---|
| dinoL224 | 50 | 42 | **+0.6595** | **+0.3407** | **+0.2510** | **0.5166** |
| dinoL518 | 75 | 50 | **+0.6284** | **+0.3433** | **+0.2613** | **0.5463** |
| clipL224 | 5 | 5 | **+0.9000** | **+0.3000** | **+0.3000** | 0.3333 (degenerate) |

Endpoint ES on the **identical** clusters, for direct contrast:

| Space | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) |
|---|---|---|---|
| dinoL224 | **+0.8695** | **+0.3916** | **+0.2918** |
| dinoL518 | **+0.8754** | **+0.3810** | **+0.2304** |

*"**The real allocation signal is materially weaker**: `rho_drop_endpointES_to_targetES_MAE` =
**+0.2100** (dinoL224) and **+0.2470** (dinoL518)."* The two ES signals only moderately agree per
cluster — ρ(target ES, endpoint ES) = **0.695** and **0.5732**.

### Table 8.2 — The target set barely has cluster structure `[MAIN-TEXT CANDIDATE]`

*Source: `B1_RESULTS.md` §C3, block `EXP B1` #3 @ `REBUILD_LOG.txt:922`.*
*This is the measurement Stage C's whole premise rests on, in all three embedding spaces.*

| Embedder | principled k | silhouette peak | peak is | bootstrap ARI | seed ARI |
|---|---|---|---|---|---|
| dinoL224 | **50** | **0.1465** | interior maximum | 0.610 | 0.615 |
| dinoL518 | **75** | **0.1600** | interior maximum | 0.579 | 0.616 |
| clipL224 | **5** | **0.0568** | **AT THE GRID EDGE** | 0.953 | 0.983 |

CLIP's silhouette curve falls **monotonically** — `k5=0.0568` down to `k150=0.0357` — so the criterion
returns k=5 by hitting the grid boundary, not by finding a maximum.
`THRESHOLD ... an interior maximum, not the grid edge -> FAIL`, recorded as a FAIL.
***"The guard was not relaxed to make this go away."***

### Table 8.3 — Per-image correlations, no clustering choice required `[APPENDIX CANDIDATE]`

*Source: `B1_RESULTS.md` §1, block `EXP B1` #2 @ `REBUILD_LOG.txt:840`. n = 2026, permutation
p = 0.0002 for all three, bootstrap CI in brackets.*

| Error type | ρ |
|---|---|
| MAE | **+0.7514** [+0.727, +0.777] |
| 1 − Sα | **+0.3114** [+0.270, +0.355] |
| 1 − IoU | **+0.2015** [+0.161, +0.247] |

### Table 8.4 — Cross-architecture `[APPENDIX CANDIDATE]`

*Source: `B1_RESULTS.md` §3, block `EXP B1` #2 @ `REBUILD_LOG.txt:840`. Per-cluster ρ at k=75, 3 seeds.*

| Architecture | MAE | 1−Sα | 1−IoU |
|---|---|---|---|
| SINet/S2C (primary) | **+0.863** | **+0.449** | **+0.324** |
| SINet/S2C_MT | **+0.879** | **+0.483** | **+0.353** |
| SINet/S2C_SO | **+0.402** | **+0.510** | **+0.354** |
| SINet-v2/S2C | **+0.899** | **+0.597** | **+0.432** |
| SegMaR/S2C | **+0.840** | **+0.576** | **+0.426** |

`S2C_SO` is the outlier and is *"reported, not excluded"*; the inversion is explained mechanistically
(source-only training runs no consistency loss and never forwards a target image, `MyTrain.py:47`)
and later shown **not** to be embedder-specific — `S2C_SO_inversion_by_embedder = dinoL224=True
dinoL518=True clipL224=True` `[B1_RESULTS.md §D4]`.

**Secondary findings.**

- **The committed blocks measured the wrong ES — B1's own most serious self-caught defect.**
  *"Both committed blocks correlated **endpoint** ES against **endpoint** error … That is a real
  result, but it is not the quantity Stage C allocates by … **A C1 built on it would have allocated by
  a test-set signal the pipeline does not possess.**"* `[B1_RESULTS.md §D1]` The cluster CSV C1
  consumes carried `n_target` as a count and **no `target_es` at all**.
- **A declared threshold FAILED because the author's expectation was wrong.** *"I declared a threshold
  saying the boundary would *still* be unstateable on the real signal. **It FAILED — because the
  boundary is stateable on the real signal, and it lands on the opposite side.** That FAIL is
  informative, not a defect: my expectation was wrong."* `[B1_RESULTS.md §D3]`
  `[PREDICTION REFUTED BY MEASUREMENT]`
- **The revised position, which is what should carry forward:** not *"ES points at the wrong error
  type"* but *"the allocation signal available at allocation time is substantially weaker than it
  appears when measured on the test set, and it ranks structural error at roughly a third"*
  `[B1_RESULTS.md §D3]`.
- **The knife-edge threshold, reported as a FAIL.** ρ(ES,1−Sα)/ρ(ES,MAE) = **0.4999** at k=75 against
  a declared boundary of 0.5 — *"True at the principled k by a margin of 0.0001"* — and **0.5825** at
  k=20. *"That threshold FAILS its own stability check and should not be quoted as a binary
  verdict … This is reported as a FAIL rather than resolved by picking the convenient k."*
  `[B1_RESULTS.md §2]`
- **Cross-check: the per-image value reproduces the old package to four decimals** — **+0.7514**
  against the old **+0.751**, verdict **MATCH** `[B1_RESULTS.md §5]`. *"a strong sign the ES
  computation and the error metrics are being computed the same way the old package computed them —
  so the per-cluster divergences are about the *clustering*, not the signal."*
- **Cross-check that caught a real bug: the quantisation convention.** B1's first scoring pass used
  `(cam*255).astype(np.uint8)`, giving endpoint MAE **0.073237** against D2's independently measured
  **0.074463** — a 1.23e-03 delta that failed the declared 0.001 threshold. Cause: `MyTest.py:76`
  writes with `cv2.imwrite(path, cam*255)`, and OpenCV **rounds** while `.astype` **truncates**.
  After `np.round`, MAE became **0.074463** (delta 2.3e-07) and Sα **0.717216** `[B1_RESULTS.md §6.4]`.
  *"Without an independently measured value to reproduce, a systematic 1.7 % relative error in every
  'true error' number would have propagated silently into every correlation."*
- **`DEGENERATE-NOT-REPORTED`.** The old package's val ρ of **+0.976** is *"not a value that moved — it
  is a number that should never have been reported"*: at k=20 on CAMO only **1–4** clusters clear the
  15-image floor. B1's own first pass reproduced the artifact (ρ = +1.0 from 2 clusters) before the
  degeneracy guard was added `[B1_RESULTS.md §5, §6.2]`.
- **The k-selection criterion was wrong on first formulation.** `pick_k` initially ranked k by
  bootstrap ARI and selected **k=5**, which has the **worst** silhouette (0.0566) in the sweep.
  *"recorded rather than silently swapped"* `[B1_RESULTS.md §6.5]`.
- **Two latent defects in the committed script, caught before sweeping.** Without the fix, the second
  and third embedder spaces *"would have silently received **dinoL518's k-means fits and dinoL518's
  endpoint embeddings** — and every 'embedder-robust' conclusion here would have been an artifact of
  reading one cache three times"* `[B1_RESULTS.md §C2]`.
- **B1 closed its own declared gap.** §C7 recorded the cross-architecture axis as run only in
  dinoL518 and `S2C_SO`'s inversion as **not measured**; §D4 measures it in all three spaces
  `[B1_RESULTS.md §C7 → §D4]`.

**Impact.** B1 supplies two things the paper needs and one warning. The measurement that travels
furthest is **Table 8.2**: the target set has almost no cluster structure — best silhouette **0.1600**,
below any conventional threshold, in every embedding space tried — which undercuts the premise of
cluster-wise allocation *upstream of* whether the signal works. The second is the corrected
signal-strength result: the real allocation signal predicts endpoint error at ρ ≈ 0.63–0.66, not the
≈ 0.87 the endpoint-side measurement suggested. The warning is that B1's own headline framing ("ES
optimises the wrong objective") is **not supported** by the signal Stage C would actually use, and
the paper must not revive it — the source refuses it explicitly, and T2C (entry 12) later reframes
what does survive as strictly comparative and ordinal.

**Honest limits.** B1 carries **three** separate scope sections. From `## 8. What B1 does not
establish`:

> - **That ES is useless as an allocation signal.** It is a strong predictor of pixel error and a
>   moderate predictor of structural error. B1 measures the gap; it does not show the signal is noise.
> - **Causality.** These are rank correlations between two quantities measured on the same images. B1
>   does not show that allocating by ES *would* or *would not* change accuracy — that is C1's and C3's
>   question.
> - **Seed-level robustness of ES itself.** Every ES value comes from one final training run per
>   architecture. Cross-architecture is the substitute. Seed variance is **UNVERIFIED-DEFERRED**.
> - **Anything about CHAMELEON**, excluded on D2's measurement, or about NC4K, which has no ES here
>   because it was not scored.
> - **That k=75 is the right k.** It is the silhouette peak of a weakly-clustered set. The honest
>   statement is that no k is strongly supported by the data, which is why everything is reported at two
>   k values with the seed spread.
> - **A per-cluster ρ on CAMO.** Structurally unavailable at these k values, not merely uncertain.

From `## C7. What the completion does not establish`:

> - **That any of the three embedders is the *right* space.** All three have low silhouette; the choice
>   is between weakly-structured options, and it is made on stated grounds, not on a strong signal.
> - **The cross-architecture axis in the other two spaces.** It was run only in dinoL518. Whether
>   `S2C_SO`'s inversion is embedder-specific is **not measured**.
> - **Anything about CAMO at the cluster level**, in any space. 1–4 clusters clear the floor everywhere;
>   it stays per-image only.
> - **A k grid finer than the 9 values swept.** CLIP's true optimum may be below 5; the grid does not
>   reach there, which is exactly why its "peak" is reported as a grid-edge artifact.

*(The second bullet was subsequently closed by §D4 — see secondary findings.)*

From `## D6. What this completion does not establish`:

> - **Whether allocating by target ES helps.** D2 measures that the signal is moderately predictive.
>   Whether acting on it changes accuracy is C1's and C3's question.
> - **Seed robustness of target ES.** One final checkpoint pair per architecture; retraining deferred,
>   so seed variance stays `UNVERIFIED-DEFERRED`.
> - **A target-side error.** The target set has no GT by construction, so "does ES predict error *on the
>   target*" is unanswerable here. The faithful correlation bridges target-side signal to endpoint-side
>   error, which is the closest measurable proxy and is not the same thing.
> - **Anything at cluster level for CAMO**, in any space, or for clipL224 beyond flagging its degeneracy.
> - **A finer k grid.** CLIP's optimum may sit below k=5; the grid does not reach there.

**Provenance.** `rebuild/B1/B1_RESULTS.md` doc 1 (`§1`–`§8`) · doc 2 (`§C1`–`§C7`) · doc 3
(`§D1`–`§D6`) · `EXP B1` blocks #2 @ `REBUILD_LOG.txt:840`, #3 @ `:922`, #4 @ `:990` (blocks #1 @
`:762`). **Carries a doc/log discrepancy — §16(b) item 4.**

---

# 9. C1 — is a targeted allocation actually different from a random one?

**What it tested.** Whether the set Stage C selects by targeting is geometrically separated from a
randomly drawn set of the same size — the old package's claim being that the separation was
negligible (`d ≈ 0.10`). C1 measured it with a held-out estimator, then **audited its own headline
after it passed**, by building control arms that destroy the targeting information while keeping the
allocation shape.

**Headline result — two halves, and the second one is the finding.**
*"**VERDICT: `d ≈ 0.10` is REFUTED — the arms are separated by `d` ≈ 1.0–1.23, not 0.10. But §8's
audit shows that separation is NOT attributable to the ES signal.** Destroying the targeting
information while keeping the allocation *shape* reproduces the same `d`. The honest verdict is
therefore **REOPENS-BUT-NOT-BY-TARGETING**"* `[C1_RESULTS.md header, §1, §8 | EXP C1 #3 @
REBUILD_LOG.txt:1148 (measurement), #4 @ :1201 (audit)]`. `[MEASURED]`

### Table 9.1 — The attribution audit: control arms `[MAIN-TEXT CANDIDATE — the single most important table in C1]`

*Source: `C1_RESULTS.md` §8.1, block `EXP C1` #4 @ `REBUILD_LOG.txt:1201`. Every arm has the same
budget `B`, the same 4447-image pool, the same embedding space and the same held-out estimator as the
targeted arm — only the selection rule differs. `d_heldout`, mean over 20 draws, at each cell's peak
`B = 250`.*

| arm | what it destroys | dinoL518 R2 | dinoL518 R3 | dinoL224 R2 | dinoL224 R3 |
|---|---|---|---|---|---|
| **targeted by `target_es`** | *(nothing — the real arm)* | **+1.1135** | **+1.0028** | **+1.2325** | **+1.0795** |
| `shuffled_es` | ES values permuted across clusters; allocation **shape kept** | **+1.1304** | **+0.9139** | **+1.1940** | **+1.1403** |
| `random_centroid` | whole budget to an **arbitrary** cluster | **+1.2262** | **+1.0534** | **+1.4243** | **+1.1908** |
| `random_direction` | `B` extremes along a **random** unit vector | **+1.1245** | **+0.9332** | **+1.1433** | **+0.8867** |
| `random_vs_random` | everything — two independent draws | **−0.0373** | **−0.0109** | **−0.0330** | **−0.0115** |

***"Every arm that keeps *concentration* but discards *targeting* reproduces the headline."***

### Table 9.2 — Paired increments: what the ES signal itself contributes `[MAIN-TEXT CANDIDATE — "the decisive numbers"]`

*Source: `C1_RESULTS.md` §8.2, block `EXP C1` #4 @ `REBUILD_LOG.txt:1201`. Paired per
(tag, representation, `B`) across all 20 cells, so no comparison is between different budgets.*

| comparison | mean | sd | range | ES wins |
|---|---|---|---|---|
| targeted − `shuffled_es` | **+0.0073** | 0.0560 | −0.1372 … +0.0889 | **13/20** |
| targeted − `random_centroid` | **−0.0649** | 0.0756 | −0.1993 … +0.0386 | **4/20** |
| targeted − `random_direction` | **+0.0479** | 0.0531 | −0.0683 … +0.1929 | **18/20** |

*"Against its own shuffle, the ES signal contributes **+0.007** — 0.6% of a `d` of 1.1 — and wins
13/20, indistinguishable from a coin flip."* Against an arbitrary cluster it is **negative**:
*"targeting the highest-ES cluster is *worse* than picking a cluster at random, in 16 of 20 cells."*
The source's own careful statement: the contribution is *"**detectable but negligible**, not …
zero."*

### Table 9.3 — The headline measurement `[APPENDIX CANDIDATE — must carry the §8 warning]`

*Source: `C1_RESULTS.md` §1, block `EXP C1` #3 @ `REBUILD_LOG.txt:1148`. Peak `d_heldout` with
combined CI.*

| Space × representation | peak `d_heldout` | `ci_combined` | verdict |
|---|---|---|---|
| dinoL224 × R2 cutout | **+1.2325** | [**+0.7700**, **+1.6422**] | **REOPENS** |
| dinoL224 × R3 render | **+1.0795** | [**+0.7959**, **+1.3902**] | **REOPENS** |
| dinoL518 × R2 cutout | **+1.1135** | [**+0.7626**, **+1.4953**] | **REOPENS** |
| dinoL518 × R3 render | **+1.0028** | [**+0.6612**, **+1.3301**] | **REOPENS** |

The source attaches a standing warning to this table, which must travel with it into any paper use:

> **Read §8 before using any number in this table.** These values are correct as measured, and
> they refute `d ≈ 0.10`. They do **not** mean what the threshold was designed to test. The audit
> shows an arm built by permuting the ES values across clusters — i.e. with the weakness signal
> destroyed — scores `+0.9139` to `+1.1403` in the same cells. The quantity these numbers measure
> is **concentration**, not **targeting**.

### Table 9.4 — What the arms *do* differ in `[MAIN-TEXT CANDIDATE]`

*Source: `C1_RESULTS.md` §8.4, block `EXP C1` #4 @ `REBUILD_LOG.txt:1201`. At `B = 1000`, targeted vs
random.*

| | dinoL518 R2 | dinoL518 R3 | dinoL224 R2 | dinoL224 R3 |
|---|---|---|---|---|
| trace-of-covariance ratio | 0.9887 | 0.9819 | 0.9851 | 0.9945 |
| **effective rank ratio** | **0.574** | **0.640** | **0.600** | **0.538** |
| target-manifold coverage Δ | −0.0030 | −0.0210 | −0.0010 | +0.0120 |
| **mean top-1 similarity Δ** | **+0.0056** | **+0.0530** | **+0.0936** | **+0.0958** |
| clusters touched | 67/75 vs 74 | 67/75 vs 74 | 49/50 vs 47 | 46/50 vs 47 |
| overlap vs chance | 1.045 | 0.992 | 0.943 | 0.987 |

The targeted arm *"spans roughly **half the effective dimensionality**, in **20/20 cells** (mean ratio
0.634)"*, buys *"average proximity, not coverage"* (top-1 similarity up to **+0.096**, coverage Δ ≈ 0),
and the arms are genuinely different sets (overlap at the chance rate, 0.94–1.05).

**Secondary findings.**

- **The declared ceiling is a concentration ceiling, not a targeting ceiling.** Cross-checked between
  two artifacts produced by **different scripts in different runs**:
  `CEILING_top_ES_cluster_MINUS_random_cluster = mean +0.0077 | range -0.1007 .. +0.1144 | top-ES
  wins 10/20`. *"Ten wins out of twenty is an exact coin flip. The highest-ES cluster is not a better
  place to spend the budget than any other cluster."* `[C1_RESULTS.md §8.3]`
- **Two load-bearing PASSes, and the second is the strongest justification in the rebuild for the
  held-out estimator.** random-vs-random null `|d| < 0.3` → **PASS**, `−0.1328`; the in-sample
  estimator would have been unusable (null > 0.5) → **PASS**, `+0.6991` with range reaching
  **+1.4506** — *"with **no targeting at all**, the in-sample `d` reaches **+1.45** — larger than C1's
  headline"* `[C1_RESULTS.md §8.5]`. Cross-checked independently by A3 at +0.6991 to two decimals
  (entry 7).
- **The null calibration is conservative, and it came from an assertion that fired.** At `B = 4447`
  both arms are the whole pool, so the true difference is exactly zero; `d_heldout` is **−0.3241**
  (sd 0.0166 over 44 cells) while `d_insample` is **+0.0000**. *"the estimator's offset under a
  known-zero difference is **negative**, i.e. **conservative**"* `[C1_RESULTS.md §4]`.
- **Amendment A2 FAILED and all five order families are reported.** `cells_ORDER_SENSITIVE = 87` of
  264; `max_d_order_spread = 0.18002`. *"**The point estimate is order-sensitive; the verdict is
  not.** Every serving order in every peak cell returns `d ≥ 1.1` … reported rather than averaged
  away."* `[C1_RESULTS.md §5]`
- **A declared threshold was wrong and is reported as FAILED, not re-pointed.** The spread criterion
  was declared on the trace ratio, which fails at 1–2%. Effective rank agrees with the conclusion and
  is reported *"**as an observation, not promoted to a threshold**, because swapping in the metric
  that agrees after seeing the data is exactly the move this rebuild exists to prevent"*
  `[C1_RESULTS.md §8.4 item 4]`.
- **A correction to C1's own plan.** `C2_measured_argmax_B = 250` in all four cells against
  `C2_predicted_peak_B = 2000`; the flag fires as required — *"**But the plan's cross-check was a
  category error, and that is recorded rather than quietly dropped.** … The two curves *should* have
  different shapes. This is **not** evidence of a contradiction between experiments."*
  `[C1_RESULTS.md §6]`
- **The measurement was self-corrected three times** — the ceiling assertion fired and became §4's
  calibration; the plan's own C2 cross-check was unimplemented in the first run and implementing it
  exposed the category error; *"the **headline was audited after it passed**, not only after it
  failed, and the audit overturned its interpretation (§8)"* `[C1_RESULTS.md §7.3]`.
- **Added-metric provenance disclosed.** `c1_variance_coverage.py` first ran with `--no-log`; the
  `ES_SIGNAL_INCREMENT_*` metrics, their two thresholds and the §8.3 ceiling cross-check were added
  **after** seeing it. *"They are **tightenings**: each makes the audit harder to pass, none was
  chosen to rescue a failing criterion, and no declared threshold was weakened or removed — the five
  failures stand."* `[C1_RESULTS.md §8.7]`
- **`[UNRUN]` / `[UNVERIFIED]`** — *"C2 remains **UNRUN** (0 `EXP C2` blocks), and `|Ds|` remains
  **UNVERIFIED**"* `[C1_RESULTS.md §6]`.
- **A hypothesis handed forward, later confirmed.** §8.6 offers *"a **hypothesis the audit makes
  available**, not something it demonstrates"*: a more-proximal, half-effective-rank, no-extra-coverage
  arm is *"entirely compatible with zero accuracy gain"*. ABC later reports this as *"consistent with
  measurement"* — see entry 10. `[PREDICTED → CONFIRMED BY TRAINING]`

**Impact.** C1 is the experiment that separates **concentration** from **targeting**, and that
distinction is the backbone of the paper's signal-side argument. It refutes the old `d ≈ 0.10` by an
order of magnitude and then refuses to bank the refutation, because its own control arms reproduce
the effect with the signal destroyed. The +0.0073-of-a-*d*-at-13/20 number is the quantitative form
of "the uncertainty signal adds almost nothing beyond the shape of the allocation it induces" — a
claim T2 later tests on trained accuracy and confirms. §8.6 supplies the mechanism that reconciles a
large geometric separation with a null accuracy outcome, which is what stops the two results looking
contradictory.

**Honest limits** — quoted verbatim from `## 9. What C1 does not establish`:

> - **That targeting improves accuracy.** C1 measures set separation, not model performance.
> - **That the separation is caused by targeting.** §8 shows it is not — it is caused by concentration,
>   which is available with no weakness signal at all.
> - **That the ES signal is worthless.** Its measured contribution is small and positive against a
>   random direction (+0.048, 18/20) and null-to-negative against every structured control. "Negligible
>   in this geometry" is supported; "zero" and "harmful" are not.
> - **That a lower-rank, more-proximal arm trains worse.** §8.6 is a hypothesis for C3, not a result.
> - **Anything about C2 or `|Ds|`.** C2 is unrun; the shape comparison was against an analytic design and
>   was, on inspection, comparing different quantities.
> - **Seed robustness of the allocation signal** — `UNVERIFIED-DEFERRED`; one checkpoint pair per model.
> - **Anything in `clipL224`** — disqualified at Gate 3 and not measured.
> - **Selection by R3.** Out of scope: renders do not exist at selection time. *d* is measured in R3, but
>   selection is always by R2.
> - **A finer B grid below 250.** `d` is still rising as B falls; the true maximum may lie below the
>   smallest budget swept — and by §8 that maximum would be a concentration effect too.

**Provenance.** `rebuild/C1/C1_RESULTS.md` (all sections) · `EXP C1` block #3 @
`results/REBUILD_LOG.txt:1148` (measurement) and block #4 @ `:1201` (the §8 audit); blocks #1–#2 @
`:1054`, `:1099` · artifacts `out/c1_attribution.csv`, `c1_spread.csv`, `c1_coverage.csv`,
`c1_occupancy.csv`.

---

# 10. ABC — the training campaign: does concentrated allocation beat random?

**What it tested.** The campaign's actual claim, on trained accuracy: 24 training runs
(2 architectures × 4 arms × 3 seeds) comparing an unpadded baseline (A0), a padded control (A2), a
randomly drawn 1000-image Stage C budget (B), and a concentration-targeted 1000-image budget (C10).
The pre-registered decision was `Δ(C − B)` against a `2σ̂` bar, with the rule fixed before training.

**Headline result.** *"**VERDICT ON THE CAMPAIGN'S CLAIM: `Δ(C − B)` is WITHIN NOISE on both
architectures and both endpoints.**"* — and the second half is mandatory: *"**But the campaign is
underpowered against its own pre-registered power statement** — the measured `2σ̂` on the primary
endpoint is **0.017933**, larger than the whole MT→Ours gap of 0.0142 this design was declared able to
resolve half of. Both halves of that sentence belong in any report of this result."*
`[ABC_RESULTS.md header, §1.3, §3.1 | EXP ABC #3 @ REBUILD_LOG.txt:1376]`. `[MEASURED]`

### Table 10.1 — The verdict, COD10K-test Sα (primary endpoint) `[MAIN-TEXT CANDIDATE — the headline table]`

*Source: `ABC_RESULTS.md` §1.3, block `EXP ABC` #3 @ `REBUILD_LOG.txt:1376`. σ̂ pooled within-arm,
df = 8. Sign-consistency counts shown as n/3.*

| | σ̂ (df = 8) | 2σ̂ | Δ(B − A2) | **Δ(C − B)** | Δ(A0 → B) | Δ(A0 → C10) |
|---|---|---|---|---|---|---|
| **SINet** | **0.008966** | **0.017933** | **+0.005768** 3/3 | **+0.005034** 3/3 | +0.012497 2/3 | +0.017530 3/3 |
| **SINet-v2** | **0.006129** | **0.012257** | **+0.002967** 3/3 | **−0.000399** 2/3 | +0.005923 2/3 | +0.005524 2/3 |

**Every one of those is WITHIN NOISE.** `architectures_agree_on_verdict` =
`A0->A2 YES  A0->B YES  A0->C10 YES  A2->B YES  B->C10 YES`. Note the two architectures **disagree on
the sign** of Δ(C − B).

### Table 10.2 — Arm means and per-arm sds `[MAIN-TEXT CANDIDATE]`

*Source: `ABC_RESULTS.md` §1.4, block `EXP ABC` #3 @ `REBUILD_LOG.txt:1376`. COD10K, Sα.*

| COD10K, Sα | A0 | A2 | B | C10 |
|---|---|---|---|---|
| SINet mean | **0.700950** | **0.707679** | **0.713447** | **0.718481** |
| SINet sd | **0.017266** | **0.001930** | **0.001807** | **0.004059** |
| SINet-v2 mean | **0.689145** | **0.692102** | **0.695069** | **0.694669** |
| SINet-v2 sd | **0.010575** | **0.003222** | **0.004863** | **0.002091** |

*"The arm ordering A0 < A2 < B ≈ C10 is monotone in all four architecture × endpoint cells, and every
step of it is inside noise."*

### Table 10.3 — Old claims re-tested `[APPENDIX CANDIDATE]`

*Source: `ABC_RESULTS.md` §2, block `EXP ABC` #3 @ `REBUILD_LOG.txt:1376`.*

| # | Old claim | Old value | Measured | Verdict |
|---|---|---|---|---|
| C3.1 | σ(Sα), all runs n=6 | 0.00356 `[no code]` | **0.008966** (SINet/COD10K, pooled within-arm, df=8) | **SUPERSEDED — 2.5× larger** |
| C3.2 | σ(Sα), distinct seeds n=4 | 0.00286 `[no code]` | **0.008966** | **SUPERSEDED** |
| C3.4 | Predicted ΔSα | 0.000111 `[no code]` | Δ(C−B) **+0.005034** / **−0.000399** measured | **RE-MEASURED** — measured on SINet at roughly 45× the prediction, and still within noise |
| C3.5 | Shortfall vs 2σ | 64× `[no code]` | Δ(C−B) **+0.005034** against 2σ̂ **0.017933** on SINet | **RE-MEASURED** — a shortfall of about 3.6×, not 64× |
| C1.1 | Cohen's *d* targeted-vs-random ≈ 0.10 | `[no code]` | *d* was refuted by C1 at +1.00–1.23; the **trained** outcome of that separation is **within noise** | **CROSS-CHECKED against a trained outcome for the first time** |

*"The old package's arithmetic was wrong in both directions and by large factors — it under-estimated
σ by 2.5× and over-estimated the shortfall by ~18×. Both errors happened to point at the same
conclusion. **Getting the right answer from the wrong numbers is not a reproduction.**"*

### Table 10.4 — Run integrity, including the pinned optimisation budget `[MAIN-TEXT CANDIDATE — this is a cause, not bookkeeping]`

*Source: `ABC_RESULTS.md` §1.1 (block #1 @ `REBUILD_LOG.txt:1252`) and §1.2 (block #2 @ `:1323`).*

| Metric | Value |
|---|---|
| Gates passed | **6/6** (signal, provenance, one_trainer, endpoints, pools, determinism) |
| `training_runs_completed` | **24/24**; `runs_abandoned` **0**; `runs_discarded_and_rerun` **0** |
| Pool sizes | A0 **4447**; A2/B/C **5447** (base + B = 1000, identical across the three) |
| **`total_step` pinned** | **253** (SINet) / **127** (SINet-v2) in **both** rounds of **every** run |
| Rounds | exactly 2 CSRDA rounds in every run |
| **Arm C reproduces C1's committed allocation cell** | `clusters_funded` **75**, `max_alloc_share` **0.194**, `alloc_entropy_norm` **0.78644**, `tv_from_uniform` **0.49253**, `n_displaced` **370** — **all five exact** |
| `scorer_reproduces_B1` | Sα **0.717216** (delta **3.77e-07**), MAE **0.074463** (delta **2.32e-07**) |
| Base bytes vs `e0_manifest.sha256` | **0** mismatched, over all 24 pools |
| Render masks pixel-identical to `raw_gt` | **1000/1000** for C10, B_s42, B_s43, B_s45 |

**The pinned `total_step` is the load-bearing integrity metric.** Steps per epoch are fixed at
**253** / **127** regardless of pool size, so adding 1000 images to a 4447-image pool bought **no
additional optimisation** — it changed only the mixture each step samples from.

**Secondary findings.**

- **A pre-run prediction refuted by the data it was used to justify.** *"`ABC_PLAN.md` §A.4 and §A.12
  item 4 predicted **arm B** would inflate pooled σ̂ … The prediction was used to argue the bar would
  be conservative."* Measured: arm B has among the **lowest** sds (**0.001807**, **0.004863**), and
  **arm A0 is the largest in both architectures** (**0.017266**, **0.010575**) by roughly an order of
  magnitude `[ABC_RESULTS.md §3.2]`. `[PREDICTION REFUTED BY MEASUREMENT]`
  **This makes a provenance annotation in the committed log block false — see §16(b) item 2.**
- **The unpadded baseline is the unstable arm, in both architectures, and nobody predicted it.** SINet
  A0 spans Sα **0.715086 / 0.681706 / 0.706058**, sd **0.017266**, ~9× arm B's. It reproduces across
  two architectures and both endpoints — *"four independent cells"*. *"**Unexplained, and stated as
  unexplained:** no mechanism is offered … It is a concrete follow-up, not a finding."*
  `[ABC_RESULTS.md §3.3]`
- **A defensible amendment was refused because it came too late.** *"A pre-registered amendment naming
  A2 the reference and pooling σ̂ over A2/B/C only would be defensible **before** seeing results; doing
  it now would be exactly the metric-substitution this rebuild exists to prevent, so **it is not done
  and no such σ̂ is reported here.**"* `[ABC_RESULTS.md §3.3]`
- **A threshold that PASSED and was still refused.** `DELTA_A0->C10_SINet|NC4K` = **+0.010892**, sign
  3/3, against 2σ̂ = **0.008309** → *"the frozen rule returns **REAL EFFECT**."* It is not reported as
  one, on two independent grounds each sufficient: NC4K is the secondary endpoint (*"reported, never
  decides"*), and the comparison is against the confounded, unstable A0. *"It is recorded prominently
  **because** it is the tempting one."* `[ABC_RESULTS.md §3.5]`
- **A threshold that FAILED and stays failed.** `n_appended_mean_range` = mean **1945.8**, range
  **1732–2163**, **spread 22.2% of mean** against a declared 5% bound; `n_appended_spread_exceeds_5pct`
  = **True** `[ABC_RESULTS.md §1.2, §3.4]`. *"Why it is reported at all: it is the one legitimate place
  the arms diverge beyond the Stage C injection … Absorbing it would hide a second-order difference."*
  The one arm-level pattern is **not** architecture-robust (present on SINet, absent on SINet-v2).
- **What it says about the ES signal: nothing, by design.** *"**So the measured null is about
  concentration.** It is **not** evidence for or against the uncertainty signal, and `ABC_PLAN.md`
  §A.12 item 7 forbids reporting it as such — in either direction."* `[ABC_RESULTS.md §3.6]` This
  disclaimer is what T2 was built to discharge — see entry 11.
- **C1's §8.6 hypothesis is upgraded by training.** *"That hypothesis is now **consistent with
  measurement** rather than merely available — at this power."* `[ABC_RESULTS.md §3.6]`
  `[PREDICTION CONFIRMED BY TRAINING]`
- **Two measurement defects found in ABC's own work.** (i) *"The `agg` values in `REBUILD_PLAN.md` §1
  are not an assertable authority"* — `common.py:248-263` claims `dir_digest` matches them; it does
  not (**d7f6de696d5c223e** against the pinned **b42e5f44b5f2b0db**), because the pinned values were
  computed over a full-relative-path listing while `dir_digest` hashes the bare filename.
  ***"Primary data is unchanged"*** — all 4447 + 4447 verify per-file against E0's manifest
  (`REVISION_TABLE.md` R16). (ii) A first pool-provenance check used the regex `Loaded 4[0-9]*`,
  which cannot match the 5447-image pools, and reported **18 spurious mismatches**; corrected before
  any conclusion rested on it `[ABC_RESULTS.md §3.7]`.

**Impact.** ABC is the paper's central null: with the decision rule fixed before training, a
concentrated Stage C allocation does not beat a random one on two architectures and two endpoints.
Equally important, it is the experiment that supplies the paper's **power honesty** — the bar is
larger than the improvement the method claims, so the null must be reported as "no effect resolvable
at this sensitivity", never as "no effect". Table 10.4 carries what is arguably the single most
consequential mechanism in the whole suite: `total_step` is pinned, so adding data cannot buy
optimisation in this loop. Finally, ABC is the first place C1's geometric separation meets a trained
outcome, and it turns C1 §8.6 from an available hypothesis into one consistent with measurement.

**Honest limits** — quoted verbatim from `## 5. What ABC does not establish`:

> - **That Stage C does not work.** It establishes that no benefit is **detectable at this power**, and
>   §3.1 quantifies the power: `2σ̂ = 0.017933` on the primary endpoint, larger than the reference gap of
>   0.0142. A real effect smaller than that is entirely consistent with these data.
> - **Anything about the ES uncertainty signal** (§3.6). The arms differ by concentration.
> - **That more seeds would settle it.** Adding seeds to *this* campaign is foreclosed —
>   `PREREGISTRATION.md` §1 and §2.7 forbid it, and topping up after seeing the answer is optional
>   stopping. A separately pre-registered campaign is the legitimate route.
> - **A mechanism for §3.3.** Why the unpadded arm trains least stably, in both architectures, is
>   unexplained.
> - **Anything at a second k, a second embedder, or α = 0.5.** k = 75 / `dinoL518` / α = 1.0 only.
>   C1's k- and embedder-robustness is inherited, not re-established on trained outcomes.
> - **Scope of the null, inherited from D1 §5:** this is evidence about targeting under an **exhausted
>   foreground pool**. It is silent on whether new foregrounds would help — the DUTS/Oracle arm was
>   deliberately out of this campaign and nothing here needed it.
> - **Seed-level determinism.** cuDNN determinism was enabled and **reduces**, but is not claimed to
>   eliminate, kernel nondeterminism. §3.3's spread is the observable consequence.
> - **Anything on CHAMELEON** (withdrawn, D2) or **CAMO** (checkpoint-selection set only).

**Provenance.** `rebuild/ABC/ABC_RESULTS.md` (all sections) · `EXP ABC` blocks #1 @
`results/REBUILD_LOG.txt:1252` (pre-flight), #2 @ `:1323` (run accounting), #3 @ `:1376` (verdict) —
*"these three are sequential **stages**; each is authoritative for its own"* · artifacts
`out/abc_metrics.csv`, `out/abc_sigma.json`, `out/abc_verdict.json`. **Carries a known-false
annotation in block #3 — §16(b) item 2.**

---

# 11. T2 — the falsification arms: does the ES signal do anything to accuracy?

> **Location note.** `EXP T2` has no `rebuild/T2/` directory. Document: `rebuild/ABC/T2_RESULTS.md`;
> pre-registration: `rebuild/ABC/PREREGISTRATION_T2.md` (committed at `617a2e1` **before** the first
> T2 training run); artifacts: `rebuild/ABC/out/t2/`. **ADDITIVE** — every committed A/B/C number is
> unaltered.

**What it tested.** The question A/B/C explicitly could not answer. ABC's arm C differed from arm B by
**concentration**, so its null said nothing about the uncertainty signal. T2 holds concentration
*exactly* fixed and varies only the signal's **direction**: C10 (the real `target_es`), CSHUF (ES
permuted across clusters, targeting destroyed) and CINV (rank-reversed, maximally anti-targeted).
12 further training runs, 2 architectures × 3 arms × 3 seeds.

**Headline result.** *"**WITHIN NOISE on all twelve cells: every gap, both architectures, both
endpoints.** The largest gap anywhere is 0.005007 (1.82 σ̂); the largest on the primary endpoint is
0.002656 (0.83 σ̂). Nothing approaches the 2 σ̂ bar."* `[T2_RESULTS.md §1, §1.2 | EXP T2 #3 @
REBUILD_LOG.txt:2452]`. `[MEASURED]` The pre-committed reading that obtains: *"the target-side ES
signal carries **no accuracy-relevant information beyond concentration, in any direction**"* — and,
critically, *"C1 established this in embedding-distance space; **it now holds on trained accuracy**"*
`[PREDICTION CONFIRMED BY TRAINING]`.

### Table 11.1 — The frozen verdict table, primary endpoint `[MAIN-TEXT CANDIDATE — the headline]`

*Source: `T2_RESULTS.md` §1.2, block `EXP T2` #3 @ `REBUILD_LOG.txt:2452`.*
*`Δ₁ = C10 − CSHUF` · `Δ₂ = C10 − CINV` · `Δ₃ = CSHUF − CINV`, on Sα, COD10K-test.*

**SINet | COD10K (2 σ̂ = 0.005533)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | +0.001525 | 0.55 | −0.001437 | +0.006059 | −0.000048 | 1/3 | **WITHIN NOISE** |
| Δ₂ C10 − CINV | −0.000866 | 0.31 | −0.005448 | +0.005691 | −0.002841 | 2/3 | **WITHIN NOISE** |
| Δ₃ CSHUF − CINV | −0.002390 | 0.86 | −0.004010 | −0.000368 | −0.002793 | 3/3 | **WITHIN NOISE** |

**SINetv2 | COD10K (2 σ̂ = 0.006390)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | −0.002656 | 0.83 | −0.008948 | +0.001838 | −0.000858 | 2/3 | **WITHIN NOISE** |
| Δ₂ C10 − CINV | −0.002312 | 0.72 | −0.004687 | −0.000004 | −0.002245 | 3/3 | **WITHIN NOISE** |
| Δ₃ CSHUF − CINV | +0.000344 | 0.11 | +0.004261 | −0.001842 | −0.001387 | 1/3 | **WITHIN NOISE** |

*"No cell is REAL EFFECT, REAL REGRESSION or INCONCLUSIVE. **12/12 WITHIN NOISE.**"* (NC4K,
secondary: Δ₁ +0.001705 / −0.001840, Δ₂ −0.003302 / −0.003904, Δ₃ −0.005007 / −0.002064 — all WITHIN
NOISE.)

### Table 11.2 — The bar is tighter than pre-registered `[MAIN-TEXT CANDIDATE — the power table]`

*Source: `T2_RESULTS.md` §1.1, block `EXP T2` #3 @ `REBUILD_LOG.txt:2452`. σ̂ = pooled within-arm sd
of Sα over arms {B, C10, CSHUF, CINV}, df = 8.*

| cell | T2 σ̂ | T2 bar (2 σ̂) | A/B/C committed σ̂ | A/B/C bar | T2 bar is |
|---|---|---|---|---|---|
| SINet \| COD10K *(primary)* | **0.002767** | **0.005533** | 0.008966 | 0.017933 | **3.24× tighter** |
| SINet \| NC4K | 0.002757 | 0.005514 | 0.004155 | 0.008309 | 1.51× tighter |
| SINetv2 \| COD10K | **0.003195** | **0.006390** | 0.006129 | 0.012257 | **1.92× tighter** |
| SINetv2 \| NC4K | 0.002781 | 0.005563 | 0.005267 | 0.010534 | 1.89× tighter |

*"`PREREGISTRATION_T2.md` §T2.11 projected a bar of ≈0.0179 (SINet) / ≈0.0123 (SINet-v2) … **The
realised bar is 3.2× and 1.9× tighter than that.** The reason is structural and not a choice made
after the fact"* — T2's pool excludes A0, whose sd was an order of magnitude above every other arm.
*"T2 resolves **39%** of the paper's whole MT→Ours gap (0.0142) on SINet and **45%** on SINet-v2,
against the ~126% the pre-registration conceded. **The null is therefore stronger than promised, not
weaker.**"* `[PREDICTION EXCEEDED — the realised power beat the pre-registered projection]`

### Table 11.3 — The same-shape assertion: the crux `[MAIN-TEXT CANDIDATE — this is what makes T2 interpretable]`

*Source: `T2_RESULTS.md` §2.2, block `EXP T2` #1 @ `REBUILD_LOG.txt:2295`. Measured for both new arms
against **C1's committed cell** (dinoL518, B=1000, R2_cut, α=1.0).*

| quantity | C1 committed | CSHUF | CINV |
|---|---|---|---|
| `clusters_funded` | 75 | 75 ✓ | 75 ✓ |
| `max_alloc_share` | 0.194 | 0.194 ✓ | 0.194 ✓ |
| `alloc_entropy_norm` | 0.78644 | 0.78644 ✓ | 0.78644 ✓ |
| `tv_from_uniform` | 0.49253 | 0.49253 ✓ | 0.49253 ✓ |
| `n_displaced` | 370 | 404 *(reported)* | 367 *(reported)* |

*"Exact equality at the recorded 5 dp — not a tolerance. **So the comparison varies the signal's
direction at fixed concentration, which is precisely what A/B/C could not do.**"*

### Table 11.4 — The arms `[APPENDIX CANDIDATE — defines the design]`

*Source: `T2_RESULTS.md` §2.1, block `EXP T2` #1 @ `REBUILD_LOG.txt:2295`.*

| arm | permutation | ρ(es[σ], es) | fixed pts | perm seed | `n_displaced` |
|---|---|---|---|---|---|
| C10 *(reference)* | identity | **+1.0** | 75 | — | 370 |
| CSHUF | random, rule-selected | **−0.03351** | 0 | 910004 | 404 |
| CINV | rank-reversing | **−1.0** | 1 *(structural)* | — | 367 |

*"CSHUF's permutation is the **first** of 64 pre-declared draws satisfying zero fixed points and
|ρ| ≤ 0.10 — chosen by a rule fixed before the draw, never by inspecting its consequences."*

**Secondary findings.**

- **A directional pattern is reported even though it is not significant.** §4 exists because
  *"suppressing a directional pattern because it failed a threshold would be the same sin as promoting
  one that passed."* Its content: *"**C10 — the real signal — is the best arm in none of the four
  cells**, and is the *worst* of the four on SINetv2|COD10K (0.694669, below even B)"*; *"**CINV —
  maximally anti-targeted — has the highest mean in 3 of 4 cells**, and Δ₂ (C10 − CINV) is **negative
  in all four**: −0.000866, −0.002312, −0.003302, −0.003904."* The source's own reading: the
  architectures disagree in sign on Δ₁ and Δ₃, *"which is the signature of noise rather than of a
  small real effect"*, and — *"**It does not reach the bar, so that is not the verdict.**"*
- **The standing ABC disclaimer is formally discharged.** *"The standing disclaimer in
  `ABC_RESULTS.md` §3.7 and `abc_build_pools.py` — 'no result from it may be reported as evidence
  about that signal' — is hereby **discharged for T2**. A/B/C's arm C still tested concentration, not
  targeting; T2 tests targeting at fixed concentration."* `[T2_RESULTS.md §3]`
  *(The internal section reference is off by one — see §16(b) item 5.)*
- **Cross-check: T2 reproduces ABC's committed metrics exactly, while deliberately computing a
  different σ̂.** B and C10 were *"re-scored, never re-trained"* and reproduce `abc_metrics.csv`
  *"**exactly at the recorded 6 dp, 24/24 cells, max deviation 0.000e+00**"*; T2's per-arm sd for B
  (**0.001807**) and C10 (**0.004059**) equal A/B/C's committed values to six decimals, and A/B/C's
  `Δ(C10 − B) = +0.005034` is reproduced exactly `[T2_RESULTS.md §6.3]`. The **σ̂ differs by design**
  (A0-free pool) — see §13 for the correct phrasing of this cross-check.
- **A third independent reproduction of the scorer against B1** — Sα 0.7172156 (Δ 3.8e-07), MAE
  0.0744632 (Δ 2.3e-07), under the 1e-5 bar `[T2_RESULTS.md §6.3]`.
- **A value-space inversion was considered and rejected before any arm was built** — negating the ES
  vector and reflecting it produce an *identical* allocation here, and neither preserves concentration
  on a skewed ES vector *"leaving Δ₂ uninterpretable"* `[T2_RESULTS.md §2.2]`.
- **Set distinctness was gated before any GPU time**, at Jaccard ≤ 0.50, *"because under this
  pre-registration equality is the *supporting* outcome and two near-identical arms would manufacture
  it."* Measured: **452 / 511 / 454** of 1000 images differ between arm pairs `[T2_RESULTS.md §2.3]`.
- **Signal provenance established retroactively and exactly.** No hash of
  `b1_cluster_es_dinoL518.csv` was recorded when C10 was built; T2 records sha256
  `1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8`, *"**identical at HEAD and at
  `065dac6`, the A/B/C block-#1 commit** — and exactly one commit ever touched the file"*
  `[T2_RESULTS.md §6.2]`.
- **A threshold that FAILS and was left exactly as frozen.** `n_appended` spread **17.6%** of mean
  (1914–2278) against the 5% threshold, *"as it also failed in the frozen A/B/C record at a worse
  22.2% (1732–2163)"*. *"**The 5% threshold was left exactly as frozen** — moving a bar after seeing
  the number it fails is retuning, not fixing."* `[T2_RESULTS.md §5.3]` Note `total_step` stays pinned
  (**0253** SINet / **0127** SINet-v2) in both rounds of every run, *"so this changes the mixture and
  never the optimisation budget."*
- **Addendum A1 — a correction to T2's own pre-registration, and the record's declared weakest link.**
  §T2.1 as frozen required reproducing `abc_metrics.csv` to `< 1e-9`, which is *"**unsatisfiable by any
  correct computation**: the file records Sα at 6 dp, so rounding alone admits up to 5e-7, ~500× the
  stated tolerance. The first full evaluation halted on it."* The replacement is *stricter* than a
  1e-6 tolerance (exact equality at 6 dp) and A1 is append-only, dated, and written *"before any σ̂,
  gap or verdict had been computed."* The source declines to let itself off: *"**Defect 4 was a
  substantive clause in the frozen pre-registration that could not be satisfied**, and it is the
  weakest link in this record: the author of the rule also authored the flaw … a reader should audit
  A1 directly rather than accept that framing."* `[T2_RESULTS.md §6.3, §6.4]`
- **Three further defects, all reporting faults that produced no wrong number**, including a
  seed-independence assertion that *"passed **vacuously** (`len(set([])) <= 1` is `True`) while its own
  metric printed `False`"* and a block that *"asserted A/B/C's Δ(C−B) and emitted a spurious **FAIL**"*
  `[T2_RESULTS.md §6.4]`. *"Every defective log block was uncommitted when found and was regenerated,
  never edited in place."*
- **No secondary metric reverses the picture** — MAE, Fβw and Eφ leave the arms interleaved, and C10
  leads on exactly one of six (architecture × metric) combinations `[T2_RESULTS.md §1.5]`.

**Impact.** T2 is the experiment that converts the suite's signal-side claim from geometry into
trained accuracy, and it is the strongest single piece of evidence the paper has on the uncertainty
signal. C1 had shown the ES signal contributes +0.0073 of a *d* against its own shuffle (a coin flip)
in embedding space; T2 shows that real, destroyed and *reversed* targeting are indistinguishable on
trained COD accuracy, at a bar 3.2× tighter than the campaign that preceded it. Because concentration
is held **exactly** fixed by construction (Table 11.3), this is a clean test of *direction* — the
thing A/B/C could not isolate. Its §4 is also a model of reporting discipline: the anti-targeted arm
has the highest mean in 3 of 4 cells and this is printed, framed as noise, and explicitly not claimed.

**Honest limits** — quoted verbatim from `## §5 Limits — what these twelve cells cannot settle`:

> ### §5.1 A null is bounded by sensitivity, not by truth
> The bar is 0.005533 (SINet) / 0.006390 (SINet-v2) — 39% and 45% of the paper's entire MT→Ours gap of
> 0.0142. **A WITHIN NOISE result means "no effect resolvable at this sensitivity," never "no effect".**
> This sentence was committed before any T2 number existed precisely so it could not be softened after
> one. C1's +0.0073 of a *d* is a geometric quantity and predicts no accuracy difference at all, so T2
> was never powered to detect an effect of that specific magnitude.
>
> ### §5.2 Every gap is attenuated by shared images
> 452–511 of 1000 injected images differ between any two C-family arms (§2.3); the rest are shared. The
> effective contrast is therefore roughly half the nominal budget, and the attenuation biases **toward**
> the null — which is the supporting outcome here. The 0.50 Jaccard gate bounds this but does not remove
> it. Every Δ above should be read against `n_differing`, not as a full-budget contrast.
>
> ### §5.3 Pseudo-labelling is a second uncontrolled channel
> `n_appended` spread **17.6%** of mean (1914–2278) across the 12 runs — far above the campaign's 5%
> threshold, which **FAILS**, as it also failed in the frozen A/B/C record at a worse 22.2%
> (1732–2163). Per architecture: SINet 7.2%, SINet-v2 14.4%. CLS selects target images by
> `edge_loss < u·avg_loss` using each arm's **own** round-1 model, so the arms differ in how many
> differently-pseudo-labelled images they append, beyond the permutation under test. `total_step` stays
> pinned (0253 SINet / 0127 SINet-v2) in both rounds of every run, so this changes the mixture and never
> the optimisation budget. **The 5% threshold was left exactly as frozen** — moving a bar after seeing
> the number it fails is retuning, not fixing.
>
> ### §5.4 Other limits
> - **n = 3.** No p-value, no bootstrap, no multiple-comparison correction, by design. Three gaps × 2
>   architectures × 2 endpoints are reported against one bar, with sign-consistency counts.
> - **CINV is a permutation**, hence formally a member of the shuffle family — deliberately its
>   maximally anti-correlated member. It is not a value-space inversion (§2.2).
> - **`best_epoch` ranges 21–99.** `SINetv2_CINV_s43` selected its teacher at epoch 99 of 100 — the
>   final epoch — so that run was still improving when training stopped. No assertion covers
>   `best_epoch`; disclosed so σ̂ is read with it in view.
> - **T2 says nothing about concentration.** It varies direction at fixed concentration. Whether
>   concentration itself helps is A/B/C's Δ(C10 − B), already WITHIN NOISE.

**Provenance.** `rebuild/ABC/T2_RESULTS.md` (all sections) · `rebuild/ABC/PREREGISTRATION_T2.md`
(committed `617a2e1`, plus Addendum A1 dated 2026-09-11) · `EXP T2` blocks #1 @
`results/REBUILD_LOG.txt:2295` (pre-flight), #2 @ `:2409` (run accounting), #3 @ `:2452` (verdict) ·
artifacts under `rebuild/ABC/out/t2/`.

---

# 12. T2C — is the pixel-over-structure gap specific to ES?

**What it tested.** Whether B1's central ordering — uncertainty predicts pixel error better than
structural error — is a property of the **ES signal** or of **uncertainty signals for COD in
general**. Three signals (ES, predictive entropy, ensemble disagreement in two variants) × two
architectures, under B1's own committed test. **TRAINS NOTHING** — *"64,640 inference forwards, no
checkpoint written, no partition fit."*

**Headline result.** *"**The ordering generalises. The strong reading of it does not.**"* The
pre-registered criterion `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)` **passes on 8 of 8 whole-image rows**, 7 of
them at 10/10 k-means seeds `[T2C_RESULTS.md §1, §2 | EXP T2C @ REBUILD_LOG.txt:2550]`. `[MEASURED]`
*"So B1's finding is **not a property of ES**. It is a property of every uncertainty signal this
pipeline can compute."* **But**: *"On SINet-v2, ρ(1−Sα) sits at **+0.54 to +0.56** — substantial, not
a null. 'Uncertainty in COD carries no localisation information' is **false as stated** for
SINet-v2."*

### Table 12.1 — Whole-image comparison across signals and architectures `[MAIN-TEXT CANDIDATE — the primary table]`

*Source: `T2C_RESULTS.md` §2, block `EXP T2C` @ `REBUILD_LOG.txt:2550`. ρ at the committed seed 0,
± sd over 10 k-means seeds. 50 clusters, 3428 target images.*

| arch | signal | ρ(MAE) | ρ(1−Sα) | ρ(1−IoU) | ordering | seeds | ratio |
|---|---|---|---|---|---|---|---|
| SINet | **ES** (validation row) | +0.6284 ± 0.0381 | +0.3433 ± 0.0301 | +0.2613 ± 0.0383 | PASS | 10/10 | 0.5463 |
| SINet | entropy | +0.5892 ± 0.0368 | +0.4267 ± 0.0277 | +0.3588 ± 0.0351 | PASS | 10/10 | 0.7242 |
| SINet | ensemble A0 | +0.6028 ± 0.0466 | +0.2698 ± 0.0487 | +0.1491 ± 0.0560 | PASS | 10/10 | 0.4476 |
| SINet | ensemble CSHUF | +0.5212 ± 0.0564 | +0.4006 ± 0.0459 | +0.3361 ± 0.0447 | PASS | 10/10 | 0.7687 |
| SINet-v2 | **ES** | +0.7070 ± 0.0404 | +0.5628 ± 0.0359 | +0.4591 ± 0.0315 | PASS | 10/10 | 0.7961 |
| SINet-v2 | entropy | +0.7393 ± 0.0309 | +0.5404 ± 0.0408 | +0.4070 ± 0.0395 | PASS | 10/10 | 0.7310 |
| SINet-v2 | ensemble A0 | +0.6191 ± 0.0675 | +0.5483 ± 0.0409 | +0.4540 ± 0.0451 | PASS | 9/10 | 0.8857 |
| SINet-v2 | ensemble CSHUF | +0.5576 ± 0.0690 | +0.4488 ± 0.0580 | +0.3370 ± 0.0577 | PASS | 10/10 | 0.8049 |

*"**The pixel-over-structure gap, `ρ(MAE) − ρ(1−Sα)`, spans +0.0708 to +0.3330.** Every value clears
the pre-registered ~0.06 resolution floor, but the smallest (SINet-v2 ensemble A0, +0.0708) only just
does, and carries the largest ratio sd in the table."*

### Table 12.2 — Boundary aggregation: the hypothesis fails, and the reason is measurable `[MAIN-TEXT CANDIDATE — as a negative result]`

*Source: `T2C_RESULTS.md` §4, block `EXP T2C` @ `REBUILD_LOG.txt:2550`. **2 of 8 rows pass; four go
negative.** Printed in full rather than dropped.*

| arch | signal | ρ(MAE) | ρ(1−Sα) | ordering |
|---|---|---|---|---|
| SINet | ES | −0.0012 ± 0.0481 | −0.0567 ± 0.0500 | FAIL 8/10 |
| SINet | entropy | +0.2434 ± 0.0414 | +0.2492 ± 0.0540 | FAIL 6/10 |
| SINet | ensemble A0 | +0.3633 ± 0.0605 | +0.2910 ± 0.0509 | PASS 10/10 |
| SINet | ensemble CSHUF | +0.3175 ± 0.0637 | +0.3857 ± 0.0381 | FAIL 2/10 |
| SINet-v2 | ES | **−0.5485** ± 0.0745 | −0.1146 ± 0.0675 | FAIL 0/10 |
| SINet-v2 | entropy | +0.4208 ± 0.0356 | +0.4182 ± 0.0455 | PASS 8/10 |
| SINet-v2 | ensemble A0 | −0.1960 ± 0.0524 | +0.0425 ± 0.0410 | FAIL 0/10 |
| SINet-v2 | ensemble CSHUF | −0.2527 ± 0.0668 | −0.0591 ± 0.0609 | FAIL 0/10 |

*"**This lands outside the pre-registered three-way interpretation.** That trichotomy anticipated the
boundary predicting *neither*, *pixel only*, or *structure*. It did not anticipate signals
**inverting**. Reported as it fell, per §T2C.1."*
`[PREDICTION REFUTED — OUTCOME OUTSIDE THE PRE-REGISTERED SPACE]`

The mechanism, explicitly labelled **POST-HOC, not pre-registered**: *"**Band area alone predicts MAE
at +0.6286 on SINet-v2** — as well as any signal in §2. A whole-image mean is effectively
*uncertainty density × area*; restricting to the band and taking a **mean** divides the area out …
That is sufficient to explain both the collapse and the sign flips."* Compounded by a selection bias:
empty-band images are dropped, and empty-band fraction correlates positively with every error
(+0.22 to +0.36).

### Table 12.3 — Ensemble sensitivity condition `[APPENDIX CANDIDATE]`

*Source: `T2C_RESULTS.md` §5, block `EXP T2C` @ `REBUILD_LOG.txt:2550`. Pre-registered: an A0 finding
that does not survive the tight CSHUF ensemble is a weak-member artifact, not a result.*

| cell | A0 | CSHUF | outcome |
|---|---|---|---|
| SINet whole | PASS | PASS | AGREE |
| SINet **boundary** | PASS 10/10 | FAIL 2/10 | **DISAGREE → weak-member artifact, not a result** |
| SINet-v2 whole | PASS | PASS | AGREE |
| SINet-v2 boundary | FAIL | FAIL | AGREE |

*"The one boundary row that passed on SINet is **withdrawn** under the pre-registered rule."*

**Secondary findings.**

- **The pre-registered ratio benchmark failed as a discriminator — and that vindicates the ordering
  rule.** The pre-registration benchmarked `ρ(1−Sα)/ρ(MAE)` against ES's committed **0.5463**, *"having
  refused the `< 0.5` constant because ES itself fails it. That was right, but it assumed 0.5463 was
  architecture-stable. **It is not**"* — ES's own ratio is **0.5463** (SINet) vs **0.7961**
  (SINet-v2), a shift of **+0.25** against a per-row sd of ~0.05–0.11. *"the ratio cannot separate
  signals **or** architectures."* `[T2C_RESULTS.md §3]` `[PREDICTION REFUTED BY MEASUREMENT]`
- **Cross-check: the ES / SINet row reproduces B1 exactly.** *"The **ES / SINet row reproduces B1's
  committed `+0.6284 / +0.3433 / +0.2613` and ratio `0.5463` exactly** (Δ ratio = −0.0000). It is a
  validation row, not a result."* `[T2C_RESULTS.md §2]`
- **Two further corroborations "nobody asked for".** The re-derived ES whole-image mean is
  **0.03784 ± 0.03145**, reproducing B1's committed `target_ES_mean_sd = 0.0378 ± 0.0315`; and the
  measured 10-seed ρ sds (0.028–0.11) bracket the pre-registered ~0.06 floor and ~0.077 ratio sd
  `[T2C_RESULTS.md §6]`.
- **A third reproduction of the scorer** — G9: Sα 0.7172156 (Δ 3.77e-07), MAE 0.0744632 (Δ 2.32e-07),
  tol 1e-5 `[T2C_RESULTS.md §6]`.
- **G8 is bit-identical to B1's committed harness output** — *"**bit-identical** to
  `b1_faithful_correlation.json`; 50 clusters, 3428 images"* `[T2C_RESULTS.md §6]`.
- **C1's literal ban passes.** G3: *"0 violations; **C1's literal ban also passes** — T2-C never reads
  the endpoint ES column"* `[T2C_RESULTS.md §6]`.
- **`[NOT APPLICABLE]` carried forward.** G7 (ES reproduction, per cluster) is
  **4.942e-07** on SINet but ***NOT APPLICABLE*** on SINet-v2, because
  `b1_cluster_es_dinoL518.csv`'s `target_es` column holds `SINet/S2C`'s ES for every architecture
  (`b1_allocation_signal.py:283`) — so on SINet-v2 the gate compared two different architectures'
  signals. *"One gate misfired and was corrected in scope, not substance"*; confirmed by feeding B1's
  own committed SINet-v2 ES through the same aggregation (identical 8.754e-02 deviation). Recorded in
  `PREREGISTRATION_T2C.md` **Addendum A1**; §T2C.1 untouched `[T2C_RESULTS.md §6]`.
- **The strongest branch of the design is declared unreachable and not claimed.** *"The boundary rows
  do **not** test 'is uncertainty informative where localisation lives'. They test an area-normalised
  quantity confounded with object size and with model confidence. The pre-registered 'strongest
  general claim' branch is therefore **not reachable from this design**, and is not claimed."*
  `[T2C_RESULTS.md §4]`

**Impact.** T2C is the experiment that lets the paper state its signal-side finding about
**uncertainty-guided allocation for COD**, not merely about ES-guided allocation in CSRDA. The
ordering holds for predictive entropy and ensemble disagreement as well as ES, on both architectures,
8/8 under a criterion fixed in advance — so the pixel-over-structure gap is a property of the
*problem and the signal class*, not of one implementation detail. Combined with T2's WITHIN NOISE
result on trained accuracy, the source calls this *"a **strong prior** that uncertainty-guided
allocation will not buy structural accuracy for COD."* It also sharply bounds the claim: the
magnitude does **not** generalise, and the paper must say "pixel error is predicted better than
structural error, always; structural error is still predicted, sometimes well" rather than anything
stronger.

**Honest limits** — quoted verbatim from `## §7 What this does and does not license`:

> **Licensed.** The pixel-over-structure ordering in B1 is a property of uncertainty signals for COD
> generally, not of ES. Three signals × two architectures, one measurement structure, 8/8 under the
> pre-registered criterion. Combined with T2's WITHIN NOISE result on trained accuracy, this is a
> **strong prior** that uncertainty-guided allocation will not buy structural accuracy for COD.
>
> **Not licensed.**
>
> - **Not causal.** T2-C is correlational. It cannot upgrade into "uncertainty guidance fails in
>   training" for signals T2 did not train.
> - **Not "no localisation information".** ρ(1−Sα) reaches +0.56 on SINet-v2. The claim is ordinal.
> - **Not a boundary result.** §4's confound means this design cannot test the boundary question.
>   Answering it needs an area-controlled statistic (e.g. partialling out band area, or a band *sum*
>   rather than mean) — new work, separately pre-registered.
> - **One endpoint.** COD10K-test only; NC4K has no DINOv2 cache, is not a B1 split, and has no
>   per-cluster error columns.
> - **Ensemble rows are weakest.** n=3, heterogeneous members, optimisation-stochasticity only, and
>   the members are not the model whose error is the endpoint column (S2C teacher Sα 0.717216 matches
>   no A0 member).
> - **Sub-0.06 ρ differences between signals are not interpreted.**

**Provenance.** `rebuild/T2C/T2C_RESULTS.md` (all sections) · `rebuild/T2C/PREREGISTRATION_T2C.md`
(committed at `6efde9f` *"before any T2-C code existed"*, plus Addendum A1) · `EXP T2C` @
`results/REBUILD_LOG.txt:2550` (the only block) · artifacts `out/t2c_table.csv`,
`out/t2c_correlations.json`.

---

# 13. Cross-check ledger — where experiments verify each other

Mutual consistency between independently written experiments is a credibility asset, and this suite
has an unusual amount of it. Every row below is a case where one experiment reproduced another's
committed number, or caught an error by failing to.

| # | What is cross-checked | Result | Source |
|---|---|---|---|
| 1 | B1's per-image ρ(ES, MAE) against the **old package's** +0.751 | **+0.7514** [+0.727, +0.777] — **MATCH** to four decimals | `B1_RESULTS.md §5` |
| 2 | The eval scorer against B1's committed values, **independently in three documents** | Sα **0.717216** (Δ **3.77e-07**), MAE **0.074463** (Δ **2.32e-07**), tol 1e-5 — same two values in all three | `ABC_RESULTS.md §1.3`; `T2_RESULTS.md §6.3`; `T2C_RESULTS.md §6` G9 |
| 3 | T2's re-scoring against ABC's committed `abc_metrics.csv` | *"exactly at the recorded 6 dp, **24/24 cells, max deviation 0.000e+00**"*; per-arm sd B **0.001807** and C10 **0.004059** equal to six decimals; `Δ(C10 − B)` = **+0.005034** reproduced exactly | `T2_RESULTS.md §6.3` |
| 4 | ABC's arm C against **C1's committed allocation cell** | `clusters_funded` **75**, `max_alloc_share` **0.194**, `alloc_entropy_norm` **0.78644**, `tv_from_uniform` **0.49253**, `n_displaced` **370** — **all five exact** | `ABC_RESULTS.md §1.1` |
| 5 | T2's two **new** arms against the same C1 cell — a third reproduction | 4 of 5 keys exact at 5 dp for both CSHUF and CINV (`n_displaced` reported, not asserted equal: 404 / 367) | `T2_RESULTS.md §2.2` |
| 6 | T2C's ES / SINet row against B1's committed correlation | **+0.6284 / +0.3433 / +0.2613**, ratio **0.5463** — *"exactly (Δ ratio = −0.0000)"*; *"a validation row, not a result"* | `T2C_RESULTS.md §2` |
| 7 | T2C's re-derived ES scale against B1's committed `target_ES_mean_sd` | **0.03784 ± 0.03145** against **0.0378 ± 0.0315** | `T2C_RESULTS.md §6` |
| 8 | T2C's harness against B1's committed artifact | G8 **bit-identical** to `b1_faithful_correlation.json`; 50 clusters, 3428 images | `T2C_RESULTS.md §6` |
| 9 | A3's true-null behaviour against **C1's independently measured** in-sample null | *"manufactures ≈ 0.65 of *d* from nothing, reproducing C1's … **+0.6991** to two decimals against its held-out **−0.1328**"* | `A3_RESULTS.md §1.5` ← `C1_RESULTS.md §8.5` |
| 10 | **B1 against D2 — and it caught a real bug.** B1's first scoring pass gave MAE **0.073237** against D2's independently measured **0.074463** | Failed B1's declared 0.001 threshold → found the `.astype` truncation vs `cv2` rounding defect → **0.074463** (Δ 2.3e-07) | `B1_RESULTS.md §6.4` ← `D2_RESULTS.md §1` |
| 11 | D1's per-pool distinctness against D2's | `reconciles_with_D2 = yes` — **4443 / 4447 / 4445** in both | `D1_RESULTS.md §1` ← `D2_RESULTS.md §1` |
| 12 | D1 consuming E0's manifest rather than recomputing | **301/301** hashes verified on a sample | `D1_RESULTS.md §1` |
| 13 | D1 re-measuring E0's `isReplace` finding **at full scale** | E0: 200 samples of one pool, ratio **11.5×**. D1: all 4447 of **both** pools, interior ratios **12.64** / **7.32**, and **0** objects with interior error > 40 | `D1_RESULTS.md §3.2` ← `E0_RESULTS.md §2.1` |
| 14 | D2's s7 re-deriving E0 §2.1 *"from a direction E0 never used"* | object region **0.962** vs background **41.667** | `D2_RESULTS.md §3.3` |
| 15 | E0's staging cross-check against the old package's background figure | `staging_background_frac` **0.8087**, i.e. **80.87%** — *"that specific old number is corroborated from primary data before A2 even runs"* | `E0_RESULTS.md §2.5` |
| 16 | **D2R against D2**, on an author-sourced CHAMELEON copy | **8 of 8 MATCH**; the 3 MISMATCHes are *"corrections to our own prior work, not to the data"* | `D2R_RESULTS.md §2` |
| 17 | Two independent instruments landing on the same integer, 41 | Tolerance sweep saturates at **41/76**; the nearest-distance gap has `n_below` = **41** — *"two instruments agreeing on the same integer from directions that owe nothing to each other"* | `D2R_RESULTS.md §1.3` |
| 18 | D2R's released detector against D2R's own sweep | **41/41** pairs and **41/41** names, plus an 8-assertion synthetic known-answer self-test with no repository data; found **1** extra pair (the second partner of the image that has two) | `D2R_RESULTS.md §3.6` |
| 19 | **D2_NC4K inheriting D2R's method by import, not by re-implementation** | *"the same module that produced the committed 41/76 CHAMELEON result … identical by construction rather than by inspection"* | `EXP D2_NC4K #2 NOTES` @ `REBUILD_LOG.txt:2074` |
| 20 | D2's prediction that a render is keyed by (foreground, mask, position) tested by D1 | held **4/4** | `D1_RESULTS.md §3.3` |
| 21 | A3's two synthetic pools, never previously compared | Within **0.0006** AUC in all three spaces, on two genuinely different generation runs — *"an **independent replication**, not a repeat"* | `A3_RESULTS.md §1.1` |
| 22 | **C1's §8.6 hypothesis against a trained outcome (ABC)** | *"now **consistent with measurement** rather than merely available — at this power"* | `ABC_RESULTS.md §3.6` ← `C1_RESULTS.md §8.6` |
| 23 | **C1's embedding-space null against trained accuracy (T2)** | *"C1 established this in embedding-distance space; **it now holds on trained accuracy**"* — 12/12 WITHIN NOISE | `T2_RESULTS.md §1, §3` |
| 24 | C1's own declared ceiling, across two scripts in two different runs | `CEILING_top_ES_cluster_MINUS_random_cluster = mean +0.0077 \| range -0.1007 .. +0.1144 \| top-ES wins 10/20` | `C1_RESULTS.md §8.3` |
| 25 | B1's `S2C_SO` inversion, across all three embedding spaces | `S2C_SO_inversion_by_embedder = dinoL224=True dinoL518=True clipL224=True` — *"not embedder-specific"* | `B1_RESULTS.md §D4` |

**One cross-check that is routinely mis-stated, and the correct phrasing.** It is tempting to write
"T2 reproduces A/B/C's committed σ̂". **It does not, and it was not supposed to.** T2 reproduces
ABC's committed *per-arm sds*, its *metric table* and its *Δ*, exactly — then computes a
**different** σ̂ over a **different, pre-registered arm pool** that excludes A0. The correct sentence
is: *T2 reproduces A/B/C's committed metrics exactly (24/24 cells at 6 dp) and, by excluding A0 from
the noise pool as pre-registered, obtains a bar 3.24× tighter (σ̂ 0.002767 against 0.008966).*

---

# 14. Self-caught errors and failed-but-kept thresholds

Both categories are evidence of rigor and should be visible in the paper, not buried. The suite's own
stated rule, from `E0_RESULTS.md` §5: *"a number that cannot be traced to a log block does not belong
in a document, **even when the number is correct**."*

## 14.1 Self-caught errors — each found by the experiment's own author

| Exp | Defect | Magnitude | Disposition | Source |
|---|---|---|---|---|
| **D2** | First s4 bucketed by a contrast-normalised thumbnail hash | Reported CHAMELEON at **10/76 (13.2 %)** against the true **41/76 (53.9 %)** — *"roughly a quarter of the true count"* | Superseded **in the open**, blocks 1–2 → block 5 | `D2_RESULTS.md §3.2` |
| **D2** | A second fix attempt (30-grey-level tolerance over all pairs) | Computationally infeasible | Abandoned, replaced by s4b, *"Recorded because the discarded approach is part of why the current one is shaped as it is"* | `D2_RESULTS.md §3.2` |
| **B1** | `(cam*255).astype(np.uint8)` **truncates** where `cv2.imwrite` **rounds** | Endpoint MAE **0.073237** vs **0.074463** — a systematic **1.7 %** relative error in every error number | Fixed with `np.round`; *"the cross-check earned its place"* | `B1_RESULTS.md §6.4` |
| **B1** | Committed blocks correlated **endpoint** ES, not **target** ES | *"A C1 built on it would have allocated by a test-set signal the pipeline does not possess"*; ρ(MAE) drops **+0.2100 / +0.2470** on the real signal | Corrected in doc 3 (block #4); overturns doc 1's direction | `B1_RESULTS.md §D1, §D3` |
| **B1** | `pick_k` ranked k by bootstrap ARI | Selected **k=5**, the **worst** silhouette (0.0566) in the sweep | *"recorded rather than silently swapped"* | `B1_RESULTS.md §6.5` |
| **B1** | Two latent defects in the committed sweep script | Spaces 2 and 3 *"would have silently received dinoL518's k-means fits and dinoL518's endpoint embeddings"* | Fixed before sweeping | `B1_RESULTS.md §C2` |
| **D1** | First run scored **both** pools against `raw_gt` | An apparent **406-image** discrepancy (4041/4447 vs 4445/4447) | *"an artifact of my mask choice, not a property of the data"*; both runs were `--no-log`, so no superseded block | `D1_RESULTS.md §3.4, §6` |
| **C1** | Self-corrected **three times** | Ceiling assertion fired → became §4's calibration; plan's C2 cross-check unimplemented → implementing it exposed a **category error**; headline audited **after it passed** → audit overturned its interpretation | All three recorded, none reverted | `C1_RESULTS.md §7.3, §4, §6, §8` |
| **ABC** | Own pre-run prediction (§A.4/§A.12) that arm B would inflate σ̂ | Refuted by its own values — A0 is largest by ~an order of magnitude | **The log block's annotation is left false** — `REVISION_TABLE.md` R17; see §16(b) item 2 | `ABC_RESULTS.md §3.2` |
| **ABC** | `REBUILD_PLAN.md` §1 `agg` values not an assertable authority | **d7f6de696d5c223e** measured against pinned **b42e5f44b5f2b0db** (path-prefixed vs bare-filename listing) | ***"Primary data is unchanged"***; ABC asserts against E0's manifest instead (`REVISION_TABLE.md` R16) | `ABC_RESULTS.md §3.7` |
| **ABC** | Pool-provenance regex `Loaded 4[0-9]*` cannot match 5447-image pools | **18 spurious mismatches** | Corrected before any conclusion rested on it | `ABC_RESULTS.md §3.7` |
| **D2R** | D2's quantization comparison used `!=`, scoring a **missing** table as a differing one | **41/41 → 40/41 differ + 1 not applicable**; two files are PNGs with a `.jpg` extension | T5 left **FAILING**, T5b added and disclosed | `D2R_RESULTS.md §1.4, §3.3` |
| **D2R** | D2's `MyTrain.py:220,297` line citation | Correct call site is **`MyTrain.py:317`**; the *mechanism* D2 described was right | *"Recorded as a correction, not silently fixed"*, and now asserted from source at run time | `D2R_RESULTS.md §1.9` |
| **D2R** | Our own rebuild plan promoted CHAMELEON to a secondary endpoint without checking the README | README lists it as CNC **source** only; **0** CHAMELEON predictions under `Result/` | *"the framing is **not** 'we found a bug in their evaluation'"* | `D2R_RESULTS.md §3.5` |
| **E0** | First provenance gate was a grep | Flagged **14** forbidden references, *all its own `FORBIDDEN` list and prose*; the second version failed on the note explaining the fix | Rewritten as an AST scan and verified **negatively** | `E0_RESULTS.md §2.7` |
| **A3** | `T8` declared on the **wrong arm** (C1's mean-difference, not the logistic probe axis) | The estimator `T8` exists to disqualify returns **0.6867 / 0.6805 / 0.4854** | Reported **FAILED rather than re-pointed**; `REVISION_TABLE.md` R23 | `A3_RESULTS.md §5` |
| **T2** | §T2.1's `< 1e-9` reference tolerance | **Unsatisfiable by any correct computation** (6-dp file admits 5e-7); first full evaluation halted after ~22 min | Addendum A1, append-only and dated; replacement is **stricter**. *"the weakest link in this record: the author of the rule also authored the flaw"* | `T2_RESULTS.md §6.3, §6.4` |
| **T2** | Seed-independence check hard-coded to `C10` | Assertion passed **vacuously** (`len(set([])) <= 1` is `True`) while its own metric printed `False` | Per-arm; empty digest list is now a FAIL | `T2_RESULTS.md §6.4` |
| **T2** | Block notes/artifacts inherited from A/B/C in three scripts | Block #3 asserted A/B/C's Δ(C−B) and emitted a **spurious FAIL** | Regenerated, never edited in place | `T2_RESULTS.md §6.4` |
| **T2C** | G7 compared two different architectures' signals on SINet-v2 | `b1_cluster_es_dinoL518.csv` holds `SINet/S2C`'s ES for every architecture (`b1_allocation_signal.py:283`) | Gate marked **NOT APPLICABLE** in scope; `PREREGISTRATION_T2C.md` Addendum A1; §T2C.1 untouched | `T2C_RESULTS.md §6` |

## 14.2 Thresholds that FAILED and were kept failed

| Exp | Threshold | Measured | Why it stays | Source |
|---|---|---|---|---|
| **D2** | CHAMELEON contamination | **41/76 (53.9 %)** — FAIL in **all five** blocks | *"**It stays.** A failing threshold that reflects the data is the instrument working"* | `D2_RESULTS.md §6` |
| **D2R** | `T5` — quantization tables differ in *every* confirmed pair | **40/41** differ + **1** not applicable | *"Relaxing the wording after seeing the data would defeat the point of declaring it beforehand."* T5b added **and its addition disclosed** | `D2R_RESULTS.md §3.3, §6` |
| **A3** | `T8` — in-sample *d* on random halves > **0.50** | **0.4015 / 0.4024 / 0.3031** | *"the declared threshold is reported FAILED rather than relaxed or re-pointed"*; the agreeing measurement is an **observation**, not a replacement threshold | `A3_RESULTS.md §5` |
| **A3** | `T6` — vacuity flag, fires above AUC 0.90 | **FIRED** at **0.9928** | The flag firing *is* the finding; the decision metric was pre-declared elsewhere for exactly this reason | `A3_RESULTS.md §1.3` |
| **B1** | ratio `< 0.5` → "wrong objective", as a binary | **0.4999** at k=75 (margin 0.0001), **0.5825** at k=20 | *"That threshold FAILS its own stability check … reported as a FAIL rather than resolved by picking the convenient k"* | `B1_RESULTS.md §2` |
| **B1** | silhouette peak must be an interior maximum, not the grid edge | CLIP falls **monotonically**, `k5=0.0568` → `k150=0.0357` → **FAIL** | *"**The guard was not relaxed to make this go away.**"* | `B1_RESULTS.md §C3` |
| **B1** | declared expectation: the boundary stays unstateable on the real signal | **FAILED** — it *is* stateable, and lands on the **opposite side** (0.5166 / 0.5463) | *"That FAIL is informative, not a defect: my expectation was wrong."* | `B1_RESULTS.md §D3` |
| **C1** | Amendment A2 — order-insensitivity | `cells_ORDER_SENSITIVE` = **87** of 264; `max_d_order_spread` = **0.18002** | All five order families reported rather than the primary alone; *"The point estimate is order-sensitive; the verdict is not"* | `C1_RESULTS.md §5` |
| **C1** | attribution audit as a whole | **2 of 7 PASS, 5 FAIL** | The five failures are the finding | `C1_RESULTS.md` header, §8 |
| **C1** | spread criterion, declared on the trace ratio | Fails at **1–2 %**; effective rank agrees with the conclusion | Effective rank reported *"**as an observation, not promoted to a threshold**, because swapping in the metric that agrees after seeing the data is exactly the move this rebuild exists to prevent"* | `C1_RESULTS.md §8.4` |
| **ABC** | `n_appended` spread ≤ 5 % of mean | mean **1945.8**, range **1732–2163**, **22.2 %** | *"Absorbing it would hide a second-order difference from anyone reading the comparison"* | `ABC_RESULTS.md §1.2, §3.4` |
| **T2** | the same 5 % bound | **17.6 %** (1914–2278) | *"**The 5% threshold was left exactly as frozen** — moving a bar after seeing the number it fails is retuning, not fixing"* | `T2_RESULTS.md §5.3` |
| **T2C** | boundary-aggregation ordering | **2 of 8** rows pass; **four go negative** (SINet-v2 ES at **−0.5485**) | Printed in full; the pre-registered "strongest general claim" branch declared **not reachable** and not claimed | `T2C_RESULTS.md §4` |
| **T2C** | ratio benchmark against ES's committed 0.5463 | Assumption of architecture-stability **refuted** — ES's own ratio shifts **+0.25** | *"the ratio cannot separate signals **or** architectures"*; the ordering rule was primary by pre-registration | `T2C_RESULTS.md §3` |

## 14.3 The inverse — a threshold that PASSED and was refused anyway

| Exp | Threshold | Measured | Why it was refused | Source |
|---|---|---|---|---|
| **ABC** | `DELTA_A0->C10_SINet\|NC4K` vs 2σ̂ | **+0.010892**, sign 3/3, against 2σ̂ = **0.008309** → the frozen rule returns **REAL EFFECT** | Two independent grounds, each sufficient: NC4K is secondary (*"reported, never decides"*), and A0 is confounded and unstable. *"It is recorded prominently **because** it is the tempting one."* | `ABC_RESULTS.md §3.5` |
| **T2C** | SINet boundary row, ensemble A0 | **PASS 10/10** | **Withdrawn** under the pre-registered ensemble-sensitivity rule, because the tight CSHUF ensemble FAILs 2/10 | `T2C_RESULTS.md §5` |
| **ABC** | a σ̂ pooled over A2/B/C only | Would have been defensible **before** seeing results | *"doing it now would be exactly the metric-substitution this rebuild exists to prevent, so **it is not done and no such σ̂ is reported here**"* | `ABC_RESULTS.md §3.3` |
| **D2R** | an inflation figure for the CHAMELEON column | *"**Measured:** nothing"* — all eight percentiles in **0.448–0.559**, sign flips with mask release | *"The tempting paper sentence … is not supported here, and the plan's pre-declared [0.25, 0.75] reading is what stopped us writing it."* | `D2R_RESULTS.md §3.2` |

---

# 15. Carried-forward marker ledger

Every `UNVERIFIED` / `DEFERRED` / `UNRUN` / `NOT-REPRODUCIBLE` / `NOT APPLICABLE` /
`DEGENERATE-NOT-REPORTED` marker in a committed source. **None of these is resolved by this file.**

| Marker | Subject | Source |
|---|---|---|
| **`UNRUN`** | `EXP C2` — *"C2 remains **UNRUN** (0 `EXP C2` blocks)"*. No directory, no document, no block. | `C1_RESULTS.md §6` |
| **`UNVERIFIED`** | `\|Ds\|` — *"remains **UNVERIFIED**, so nothing here confirms or refutes C2"* | `C1_RESULTS.md §6` |
| **`UNVERIFIED`** | Whether the **published** S2R-COD paper reports a CHAMELEON column anywhere — *"the PDF is not in this checkout"* | `D2R_RESULTS.md §3.5, §5` |
| **`UNVERIFIED` (flagged, not answered)** | Under `--task C2C` the CNC bundle is the **source** pool, so a C2C table reporting CHAMELEON as test *"would be a direct source/test collision — strictly worse than what D2 found. Resolving that needs the paper."* | `D2R_RESULTS.md §3.5` |
| **`UNVERIFIED-DEFERRED`** | Seed-level robustness of ES itself — *"Every ES value comes from one final training run per architecture"* (three separate occurrences) | `B1_RESULTS.md §5, §8, §D6` |
| **`UNVERIFIED-DEFERRED`** | Seed robustness of the allocation signal — *"one checkpoint pair per model"* | `C1_RESULTS.md §9` |
| **`UNVERIFIED-DEFERRED`** | Cross-run ρ(ES, MAE) k=20, old value +0.893 ± 0.059 (n=5 runs) — *"not comparable — seed axis deferred"* | `B1_RESULTS.md §5` |
| **`DEGENERATE-NOT-REPORTED`** | ρ(ES, MAE) per-cluster k=20 **val**, old value +0.976 — **REFUTED AS A NUMBER**; 1–4 clusters clear the floor | `B1_RESULTS.md §5, §6.2` |
| **`NOT-REPRODUCIBLE`** | `dinoB/224` has no rebuild cache, so one of the original's three *d* sub-values (**4.61**) has no counterpart — *"logged `NOT-REPRODUCIBLE` rather than substituted"* | `A3_RESULTS.md §7` |
| **`NOT APPLICABLE`** | T2C gate **G7**, ES reproduction per cluster, on SINet-v2 — the committed CSV holds `SINet/S2C`'s ES for every architecture | `T2C_RESULTS.md §6` + `PREREGISTRATION_T2C.md` Addendum A1 |
| **not measured** | The cross-architecture axis in the other two embedder spaces (**subsequently closed** by `B1_RESULTS.md §D4`) | `B1_RESULTS.md §C7` → `§D4` |
| **not measured** | Anything in `clipL224` for C1 — *"disqualified at Gate 3 and not measured"* | `C1_RESULTS.md §9` |
| **owed** | The author-sourced re-audit for **COD10K-test, NC4K and CAMO** — *"The same author-sourced re-audit is **owed** for them, and `CLEAN_PROTOCOL.md` marks it"*; until then *"treat their rates as provisional"* | `D2R_RESULTS.md §4, §5`; `CLEAN_PROTOCOL.md` caveat 2 |
| **still open** | A1 decisions (d)(3)–(d)(6), and whether `REBUILD_PLAN.md` §3 receives a dated amendment for its **unsatisfiable** pre-registered confirm condition | `A1_SCOPING.md` outcome box, §6(d)(4) |
| **unexplained** | Why the unpadded arm A0 trains least stably, in both architectures — *"no mechanism is offered … It is a concrete follow-up, not a finding"* | `ABC_RESULTS.md §3.3` |
| **unmeasured** | Generator variance across seeds at the **pool** level (E0 ran `--seed 0` only). Partially addressed by D2 s8 at the **image** level (~37–40 grey levels) on **one** foreground | `E0_RESULTS.md §4`; `D2_RESULTS.md §3.3, §5` |
| **disclosed** | `best_epoch` ranges **21–99**; `SINetv2_CINV_s43` selected its teacher at epoch 99 of 100, *"so that run was still improving when training stopped"* | `T2_RESULTS.md §5.4` |

---

# 16. Discrepancy and provenance register

## 16(a) Experiments missing a result document or a log block

| Experiment | Missing | Detail |
|---|---|---|
| **A1** | **No log block** | Zero `EXP A1` blocks. `A1_SCOPING.md` states it: *"No experiment was written and none was run … **No number in this document enters `results/REBUILD_LOG.txt`.**"* Entry 6 is written as a source-reading result and its one figure is marked `[NOT IN COMMITTED LOG BLOCK]`. |
| **D2_NC4K** | **No `*_RESULTS.md`** | 2 committed blocks; the only document is `README.md`, a setup document — *"**No measured number appears in this file.**"* Entry 4 sources every number from the log block and `CLEAN_PROTOCOL.md`. |
| **C2** | **Both** | Declared **UNRUN**: 0 blocks, no directory, no document. |

## 16(b) Discrepancies found between a result document and its log block

**These are flagged, not resolved.** Every result document in this suite carries a precedence rule of
the form *"That block is authoritative; this file is a reading of it. If the two ever disagree, the
log wins."*

| # | Discrepancy | Status |
|---|---|---|
| 1 | **`D2_RESULTS.md` §6 is headed *"Why the log has **four** D2 blocks, and a FAIL in all of them"*, but `results/REBUILD_LOG.txt` contains **five** `EXP D2` blocks** (L306, L372, L440, L514, L600) — and the section's own table has **five** rows, ending *"5 \| **12 PASS / 1 FAIL** \| … Authoritative"*. | Heading text only; the table and the log agree at five. No number is affected. |
| 2 | **ABC block #3 carries a provenance annotation that is false, and it is uncorrected in the committed log.** `ABC_RESULTS.md` §3.2: *"This makes the provenance annotation on `per_arm_sd_*` in block #3 false. It reads 'arm B carries selection variance A0 and C do not — pooled sigma_hat is inflated by it.' The **values** in that metric are correct; the **explanation attached to them is refuted by the values themselves.**"* The document adds: *"A block #4 would be needed to fix the annotation in the log itself; the values do not change."* | **The sharpest doc-vs-log disagreement in the suite**, self-declared. Logged as `REVISION_TABLE.md` R17. Values unaffected; the paper must not quote the annotation. |
| 3 | **`D1_RESULTS.md` §3.1 still cites `MyTrain.py:220,297`** as what loads the authors' pool. D2R §1.9 measured the call site as **`MyTrain.py:317`** and recorded *"`D2_RESULTS.md`'s cited lines are correct = **False**"*. D1 does not carry the correction. | D2R corrected D2's copy of this citation but not D1's. The **mechanism** both describe is correct; only the line numbers are wrong. |
| 4 | **`B1_RESULTS.md` cites a log timestamp that does not exist.** Its header names the authoritative block as `EXP B1` timestamped **`2026-09-01T14:04+05:30`**; the log's second `EXP B1` block is timestamped **`2026-09-01T13:56:55+05:30`** and **no block anywhere in the file carries `14:04`**. The block is still unambiguously identified by ordinal (*"the second `EXP B1` block"*) and by commit (`0a1d238`, which matches). Separately, the same header states *"The log holds **two** `EXP B1` blocks"*, while the log holds **four** and the file's own docs 2 and 3 cite *"the **third**"* and *"the **fourth**"*. | Timestamp is wrong; block identity is recoverable from the ordinal and commit. The "two blocks" statement is true of doc 1 only and stale for the file as a whole. |
| 5 | **`T2_RESULTS.md` §3 cites the standing ABC disclaimer as `ABC_RESULTS.md` §3.7.** It is **§3.6** (*"What the campaign establishes about concentration, and what it says about the ES signal — nothing"*); §3.7 is *"Two measurement defects found in ABC's own work"*. | Internal cross-reference only; the quoted disclaimer text is accurate. |
| 6 | **Two different NC4K contamination rates, on two different axes, which must not be collapsed.** D2 reports **1/4121** against the **full Target training pool**; D2_NC4K reports **0/4121** against **COD10K-train** (the 3040 `COD10K-CAM-*` files only — *"the other 1000 files in Target/Image are CAMO and are excluded from that side by construction"*) and **0/4121** against **COD10K-test**. | Not a contradiction — three different comparisons. `CLEAN_PROTOCOL.md` keeps them distinct and the paper must too. |
| 7 | **`common.py:248-263` claims `dir_digest` matches `REBUILD_PLAN.md` §1's `agg` values; it does not** — **d7f6de696d5c223e** measured against the pinned **b42e5f44b5f2b0db**. | Artifact-vs-plan, not doc-vs-log. *"**Primary data is unchanged**"* — all 4447 + 4447 verify per-file against E0's manifest. `REVISION_TABLE.md` R16. |
| 8 | **E0 and D1 report the raw-vs-authors' foreground-fraction difference differently** — E0 §1 s2: **+0.00542** over 200 sampled stems; D1 §1: **0.19132** vs **0.18557**, a difference D1 itself labels *"derived from the two logged values"*, over all 4447. | Not a contradiction — different sample sizes, and D1's is explicitly flagged as an in-document derivation. |
| 9 | **The CHAMELEON nearest-distance jump is quoted at two precisions.** D2 §1.4: *"A **7.4x** jump after exactly 41 images"*. D2R §1.3 and `CLEAN_PROTOCOL.md`: **7.36×**. | Same quantity, different rounding. Prefer D2R's **7.36×**. |

## 16(c) Numbers that exist but have no committed log block

| Source | Content | Disposition |
|---|---|---|
| `rebuild/ABC/POOL_MECHANICS_AUDIT.md` (628 lines) | A read-only audit driven by `pool_mechanics_probe.py`, which emitted **no `EXP` block** | **Not used** in any entry or table in this file, per the sourcing rule. Available if the paper needs it, but it would be the only unlogged source in the manuscript. |
| `rebuild/A1/A1_SCOPING.md` | The `fuse` 1×1 conv weight norm **0.907 vs 0.810, ratio 1.12**, read from `LAKE-RED/ckpt/LAKERED.ckpt` | Quoted in entry 6 and explicitly marked `[NOT IN COMMITTED LOG BLOCK]`. The document itself states no number of its reaches the log. |
| `rebuild/A3/A3_RESULTS.md` §1.4 | Five **ratios** computed in the document from two logged values each | Flagged inline by the source itself, *"because arithmetic performed in a document rather than by a script is a defect this rebuild has already recorded once (`REVISION_TABLE.md` R4)"*. Quoted here with that flag attached. |
| `rebuild/D1/D1_RESULTS.md` §1 | The **0.00575** mask-fraction difference | Flagged by the source as *"derived from the two logged values"*. |
| `rebuild/ABC/ABC_RESULTS.md` §3.4 | The SINet A0-vs-A2 append-count comparison (**1798.0** against **1792.7**) | Flagged by the source as *"arithmetic on the logged triples above"*. |

## 16(d) Values the paper will likely want that are `[NOT IN COMMITTED ARTIFACTS]`

| Wanted | Status |
|---|---|
| A **p-value or confidence interval** on any ABC or T2 arm gap | `[NOT IN COMMITTED ARTIFACTS]` — *"**n = 3.** No p-value, no bootstrap, no multiple-comparison correction, **by design**"* (`T2_RESULTS.md` §5.4). Verdicts are Δ against a 2σ̂ bar with sign-consistency counts. |
| A **CHAMELEON score-inflation figure** | `[NOT IN COMMITTED ARTIFACTS]` and **deliberately unavailable** — *"No inflation figure. §1.7 measures no difficulty skew and the sign flips with the mask set"* (`D2R_RESULTS.md` §5). |
| Whether the **published S2R-COD paper** reports a CHAMELEON column | `UNVERIFIED` — the PDF is not in this checkout (`D2R_RESULTS.md` §5). |
| Author-sourced contamination rates for **COD10K-test, NC4K, CAMO** | `[NOT IN COMMITTED ARTIFACTS]` — measured against on-disk copies only; the re-audit is **owed** (`D2R_RESULTS.md` §5). |
| **Seed variance** of the ES signal or the allocation signal | `UNVERIFIED-DEFERRED` throughout (`B1_RESULTS.md` §8/§D6, `C1_RESULTS.md` §9). |
| **Generator seed variance at the pool level** | Unmeasured — E0 ran `--seed 0` only; D2 s8 measures it at the image level on **one** foreground (`E0_RESULTS.md` §4, `D2_RESULTS.md` §5). |
| A **mechanism** for A0's instability | Explicitly unexplained (`ABC_RESULTS.md` §3.3). |
| A **boundary-localised** uncertainty result | Declared **not reachable from this design**; needs an area-controlled statistic, *"new work, separately pre-registered"* (`T2C_RESULTS.md` §4, §7). |
| A **C2** result of any kind | `UNRUN` — 0 blocks. |
| `dinoB/224` counterpart to the original's *d* = 4.61 | `NOT-REPRODUCIBLE` (`A3_RESULTS.md` §7). |
| A **DUTS/Oracle (new-foregrounds)** arm | Out of scope by design — *"the DUTS/Oracle arm was deliberately out of this campaign"* (`ABC_RESULTS.md` §5). This is the arm that would test D1's central limit. |

## 16(e) Sources deliberately not used

`rebuild/PAPER/` — containing `PAPER_PLAN.md`, `main.tex` and a compiled `main.pdf` — is **gitignored
and untracked** (`.gitignore`: `/rebuild/PAPER*`; `git ls-files rebuild/PAPER/` is empty), and is
therefore not a committed artifact. It was **not** used as a source for any number, tier or claim in
either consolidation file. Two consequences worth knowing: a recursive `grep` from the repo root
silently skips it, and any tier assignment or cause list it contains may now disagree with
`TIER_SEGREGATION.md`, which was derived independently from the committed result documents.

`rebuild/reference/old_scripts/` is an archived audit object and is not a source.

---

*End of `FINAL_RESULTS.md`. The tier classification of every finding above is in
`rebuild/TIER_SEGREGATION.md`, which also carries the closing `CONSOLIDATION_NOTES`.*

# D2 — Verified results

**Status: COMPLETE. 12 of 13 thresholds PASS; 1 FAIL, and the FAIL is the headline finding.**
**All 5 old claims re-tested: 5 MATCH.**

Source of every number below: `results/REBUILD_LOG.txt`, block **`EXP D2`** timestamped
`2026-08-31T14:32:23+05:30`, commit `ddf42f8`. That block is authoritative; this file is a reading of
it. Every figure quoted here appears verbatim in that block — checked mechanically.

Setup: `rebuild/D2/D2.md`. **Trains a model: NO** (s8 runs the generator, but trains nothing).

---

## 1. What was measured

### Coverage

| Metric | Value |
|---|---|
| Images hashed | **23854** across 8 splits |

### Exact duplicates across splits

| Pair | Collisions |
|---|---|
| COD10K-test ∩ Target, byte level | **7** |
| COD10K-test ∩ Target, pixel level | **7** |
| — of those sharing a filename | **2** |
| CHAMELEON ∩ Target | **0** |
| NC4K ∩ Target | **0** |
| CAMO-val ∩ Target | **0** |
| CAMO-val ∩ CHAMELEON | **3** |
| any endpoint ∩ any HKU-IS pool | **0** |

Byte and pixel levels agree exactly. **But see §1.4 — "0" here does not mean clean.**

### Duplicates within a split

| Split | Redundant files | Unique |
|---|---|---|
| Target | **2** | — |
| COD10K test | **0** | — |
| raw HKU-IS | **4** | **4443** of 4447 |
| authors' pool | **0** | **4447** of 4447 |
| local renders | **2** | **4445** of 4447 |

### 1.4 Near-duplicates — the same photograph, re-encoded

Exhaustive within every exact-dimension group; shortlisted by a 32×32 descriptor, then **every
survivor verified at full resolution**.

| Metric | Value |
|---|---|
| Candidate pairs shortlisted | **323** |
| Confirmed at mean\|diff\| ≤ 6.0 | **132** |
| — crossing endpoint ↔ training | **49** |

Distinct **endpoint** images that are re-encodes of training data:

| Endpoint | Contaminated | Share |
|---|---|---|
| COD10K test | **2/2026** | 0.1 % |
| **CHAMELEON** | **41/76** | **53.9 %** |
| NC4K | **1/4121** | 0.0 % |
| CAMO-val | **4/250** | 1.6 % |

**Tolerance sweep** for CHAMELEON, because the headline depends on the cutoff and a conclusion that
holds at only one tolerance is not a conclusion:

| mean\|diff\| ≤ | CHAMELEON matched |
|---|---|
| 1.0 | **11/76** |
| 2.0 | **26/76** |
| 3.0 | **37/76** |
| 5.0 | **40/76** |
| 6.0 | **41/76** |

It saturates at 41. **s4b settles whether that is a data boundary or a cutoff artifact**, by measuring
for every endpoint image the distance to its nearest same-dimension *training* image and looking for a
gap in the sorted distances:

| Endpoint | Checkable | Gap in sorted nearest distances |
|---|---|---|
| COD10K test | **1502/2026** | **none** |
| **CHAMELEON** | **51/76** | **41 below 5.51, next at 40.58** |
| NC4K | **1715/4121** | **none** |
| CAMO-val | **95/250** | **none** |

A 7.4x jump after exactly 41 images. So 41 is a property of the data, not of the tolerance. The other
three endpoints show no gap at all — their nearest-distance distributions are continuous, which is what
a clean set looks like.

"Checkable" means the image has at least one same-dimension training candidate. **A large fraction of
every endpoint is unchecked** — 25 of CHAMELEON's 76, and most of NC4K — because a duplicate saved at a
different resolution falls outside every dimension group. Unchecked is not clean.

### Impact on the reported endpoint

Computed with the repo's own `Eval/metrics.py` over `Result/SINet/S2C`:

| Metric | Value |
|---|---|
| MAE, all 2026 images | **0.074463** |
| MAE, excluding the 7 exact duplicates | **0.074476** |
| Delta | **−1.242e-05** (−0.0167 % relative) |
| Mean MAE of those 7 | **0.070882** |
| Their mean percentile within the clean set | **0.4761** (0.5 = indistinguishable) |

### Scoping

| Metric | Value |
|---|---|
| `MyTrain.py` `--val_root` default | **`./Dataset/Val/CAMO/`** (line 221) |
| Checkpoint-selection set is CAMO | **True**, 250 images |

### Is a render a function of its input? (s7 observational, s8 controlled)

| s7 — observed in the production pool | Value |
|---|---|
| Byte-identical image pairs in raw HKU-IS | **4** |
| Prediction holds (identical render **iff** mask identical **and** same shard-local position) | **4/4** |
| Pairs with identical image **and** mask but different position | **1** |
| Their render divergence, mean abs | **26.096** |
| — background | **41.667** |
| — object region | **0.962** |

| s8 — controlled, 3 byte-identical inputs named to sort A/B/C | Value |
|---|---|
| Inputs byte-identical | **True** |
| **T1** one shard, positions 0/1/2 → all differ | **True** |
| T1 mean\|diff\| A vs B | **36.738** |
| T1 mean\|diff\| B vs C | **40.338** |
| **T2** identical invocation, fresh output dir → reproduces bit-exactly | **True** |
| **T3** three shards, each input at local position 0 → all identical | **True** |
| T3 mean\|diff\| A vs B | **0.0** |
| T3 render equals the one-shard position-0 render | **True** |

---

## 2. Old claims re-tested

| # | Old claim | Old value | Measured | Verdict |
|---|---|---|---|---|
| D2.1 | COD10K-test ∩ Target | 7 (2 same-name, 5 cross-named) | 7 (2 same-name) | **MATCH** |
| D2.3 | CAMO ∩ CHAMELEON | 3 | 3 | **MATCH** |
| D2.4 | Internal duplicates in Target | 2 | 2 | **MATCH** |
| D1/D2 | Internal duplicates in render pool | 2 (4445 unique of 4447) | 2 (4445 unique) | **MATCH** |
| D2.5 | MAE impact of the leaked images | 0.000012 (0.017 % relative) | 1.242e-05 (0.0167 %) | **MATCH** |

All five reproduce. **This matters for how the rebuild is read:** these were `[no code]` in the old
package — no producing script, no log block — yet every one is correct. The old defect was
*provenance*, not arithmetic. Being unverifiable is not the same as being wrong.

One correction, immaterial to any number: the old documents name a cross-named duplicate
`COD10K-CAM-3-Flying-53-Owl-4633`. No such file exists; it is `Flying-65`.

---

## 3. How the findings change our approach, thinking and assertions

### 3.0 The 41 pairs, on disk and visually verified

All 41 are exported by `d2_export_duplicates.py` to `rebuild/D2/duplicates/`:
`chameleon/` (the 41 endpoint images), `target/` (their 41 training-pool partners), `pairs/` (one
figure each: CHAMELEON | Target | amplified difference), and three contact sheets. Per-pair
measurements are tracked at `out/d2_duplicate_pairs.csv`.

**Quantization tables differ in 41/41 pairs** — a copied file would keep its table, a re-encode
cannot. `mean|diff|` spans **0.603** to **5.512**. Both extremes were inspected visually and are
plainly the same photograph: rank 1 (`animal-76` / `Owl-4516`) is one owl on one tree, and rank 41
(`animal-31` / `Turtle-1208`) is one turtle in one patch of leaf litter. The larger residual at rank 41
is a texture effect, not a structural one — that image has content std **69.2**, so re-encoding it at a
different quality leaves bigger errors everywhere. Its difference panel is uniform noise with no
structure.

**What "training data" means here.** The partners live in `Dataset/Target/Image`, the **unlabeled
target-domain pool** that `MyTrain.py:220,297` feeds to `get_tarloader`. So the model sees those pixels
during training, and CLS generates pseudo-labels from them, but CHAMELEON's ground-truth masks never
enter training. Test *pixels* in training, not test *labels* — the same transductive-UDA situation as
the 7 COD10K duplicates in §3.5, at 20x the rate.

### 3.1 CHAMELEON is not reportable — and exact hashing calls it perfectly clean

- **Standing claim:** primary endpoint COD10K; **secondary endpoints CHAMELEON and NC4K**
  (`REBUILD_PLAN.md` §3). Exact hashing appears to confirm it: CHAMELEON ∩ Target = **0**.
- **Measured:** **41 of CHAMELEON's 76 images (53.9 %)** are the same photographs as Target training
  images, re-encoded — identical dimensions, mean\|diff\| ≤ 6, and **different JPEG quantization
  tables** in every case, which is independent confirmation of re-encoding rather than file copying.
- **Revised position:** **CHAMELEON is removed as a reportable endpoint.** Not caveated — removed.
  Over half of it is training data. The reportable set is **COD10K test (primary, 2/2026 = 0.1 %) and
  NC4K (secondary, 1/4121)**.
- **The deeper lesson, which is the point of this rebuild.** Exact hashing returns **0** for
  CHAMELEON ∩ Target and is *correct at that level*. The old package used pixel identity, reported 0,
  and treated 0 as "clean". A method that cannot see re-encoding was used to license a claim about
  contamination. The number was right; the inference from it was not.

### 3.2 My own first implementation had the same flaw, one layer up

- **What happened:** D2's first s4 bucketed images by a contrast-normalised 16×16 thumbnail hash and
  compared only within a bucket. It reported CHAMELEON at **10/76 (13.2 %)**. The exhaustive
  within-dimension search finds **41/76 (53.9 %)** — so the first version had roughly a quarter of the true count (compare log blocks 1-2 at 10/76 against block 5 at 41/76).
- **Cause:** contrast normalisation destroyed the discriminative scale, and hard bucket edges split
  true pairs. Both are recall failures, and a recall failure in a contamination sweep produces
  exactly the error in §3.1 — an under-count reported as a bound.
- **A second attempt also failed, differently.** Widening s4's tolerance to 30 grey levels over *all*
  pairs was computationally infeasible: inside the largest dimension group (2768 images) the shortlist
  explodes and every survivor needs two full-resolution decodes. Abandoned and replaced by **s4b**,
  which asks the same question bounded to endpoint-vs-training pairs. Recorded because the discarded
  approach is part of why the current one is shaped as it is.
- **Fix:** exhaustive over the only pairs that can be pixel-comparable — those sharing exact
  dimensions. 23854 images fall into 4427 dimension groups, 7.4M candidate pairs, shortlisted by
  Gram matrix and verified at full resolution. Nothing in scope is missed for want of a bucket.
- **Position:** recorded rather than quietly corrected. The first number was wrong and it was mine.
  It is also why §1.4 now carries a tolerance sweep and an independent brute-force cross-check
  instead of a single figure.

### 3.3 The seed pins the run, not the image

- **Standing claim, from E0:** LAKE-RED at `--seed 0` reproduces bit-exactly on this stack.
- **Mechanism, read from source:** `test.py:90-91` sets `torch.manual_seed(seed)` **once per
  process**; `test.py:115` shards by stride (`pairs[i::total]`). Per-image DDIM noise is therefore
  drawn sequentially and depends on **position within the shard**.
- **s7, observational:** 4 byte-identical input pairs in raw HKU-IS; the prediction *identical render
  iff mask identical **and** same shard-local position* holds **4/4**.
- **s8, controlled — and this is the load-bearing test:** three byte-identical inputs, generated
  three ways.
  - **T1** one shard → three **different** renders (mean\|diff\| 36.7 and 40.3). A render is **not** a
    function of (image, mask).
  - **T2** the same invocation repeated → **bit-identical**. The run *is* deterministic.
  - **T3** three shards, each input forced to local position **0** → **all three identical**,
    mean\|diff\| **0.0**, and equal to the one-shard position-0 render.
  T3 is why this is a mechanism and not a correlation: a negative result is consistent with several
  explanations, but only the position account predicts that equalising positions collapses the
  divergence to exactly zero.
- **Sharpened claim:** *"a static seed reproduces LAKE-RED"* is right at the **run** level and wrong
  at the **image** level. Same seed + same input listing + same shard count → bit-identical (T2, and
  E0 at 4447/4447). The same image at a different position → a different background. **E0's headline
  needed this qualifier and did not have it:** change `--shard_total`, or add or remove one input
  file, and every later index shifts.
- **Bonus, and it is not small.** E0 recorded generator seed-variance as "unmeasured and unclaimed".
  s8 measures it: re-rolling the noise on one fixed foreground moves the render by **~37–40** grey
  levels mean absolute. That is the quantity a best-of-K selection scheme would exploit, so B3 can
  now reason about it from measurement instead of assumption.
- **A third, independent confirmation of E0 §2.1.** In s7's clean pair the **object** region differs
  by **0.962** while the background differs by **41.667**. Two renders of one foreground under
  different noise share their object pixels almost exactly — re-deriving the `isReplace` compositing
  finding from a direction E0 never used.

### 3.4 The leaked-name set is a contract, not a constant

- **Standing claim:** 7 target images excluded, hardcoded as a `LEAK` set in the old `embed_dino.py`.
- **Measured:** the same 7, emitted to `out/d2_leaked_names.json` with method, commit, endpoint-side
  partners, and an explicit scope statement.
- **Position:** B3 and C1 **read this file**; they carry no name list. The old failure mode — a
  measured result frozen into upstream code — is structurally prevented, and the `Flying-53`
  transcription error could not have propagated, because nothing downstream reads a name typed into
  a document.

### 3.5 Exact contamination does not bias the endpoint — a confound removed

- **Measured:** removing the 7 exact duplicates changes MAE by **−1.242e-05** (**0.0167 %**). Their
  mean percentile within the clean test set is **0.4761**; their mean MAE **0.070882** against a set
  mean of **0.074463**.
- **Position:** **no memorisation signature.** These are a violated benchmark protocol, not label
  leakage — pseudo-labels come from the teacher, so test *pixels* enter training while test *labels*
  never do. Inherited from the published S2R-COD protocol, so disclosed rather than "fixed".
- **Consequence for the verdict:** an escape route closes. Had the duplicates been anomalously easy,
  any arm difference could have been blamed on contamination. They are not, so contamination is
  **not** a competing explanation for a null result on COD10K.
- **Scope of that reassurance:** it covers the **7 exact** duplicates on COD10K. It does **not** cover
  CHAMELEON, where contamination is 53.9 % and the endpoint is simply withdrawn.

### 3.6 CAMO can never be an endpoint, asserted in code

- **Measured:** `MyTrain.py:221` defaults `--val_root` to `./Dataset/Val/CAMO/`; that 250-image set is
  the published CAMO **test** split.
- **Position:** every checkpoint in every arm is selected on a test set. Identical across arms, so it
  cannot bias B-vs-C — but CAMO is never an endpoint. Asserted by reading `MyTrain.py` at run time.
- **On the deleted directory:** `Dataset/Test/CAMO` was removed mid-audit, confirmed intentional as a
  duplicate of `Val/CAMO`. Filename identity 250/250 and content identity 5/5 sampled were verified
  before removal; full 250/250 is no longer verifiable. The conclusion does not depend on it — the
  duplication is *why* validation and test were the same images.

### 3.7 The three HKU-IS pools have different duplicate structure

- **Measured:** raw HKU-IS **4443** unique of 4447; authors' pool **4447** of 4447; renders **4445**.
- **Position:** further evidence for E0 trap T1. If the authors' pool were a re-encoding of raw
  HKU-IS, byte-identical raw inputs would give byte-identical authors' outputs and the redundant count
  would be 4, not 0. Genuinely different provenance.
- **Consequence for D1:** "4447 distinct foregrounds" needs care — distinctness is pool-dependent, and
  per §3.3 a render is keyed by (foreground, mask, position), not by foreground alone.

---

## 4. Consequences by downstream experiment

| Experiment | What D2 changes for it |
|---|---|
| **D1** | Distinctness is pool-dependent: 4443 / 4447 / 4445. A render is not keyed by its foreground alone (§3.3) |
| **A3** | Per-pool reporting reinforced (§3.7). The render pool carries a noise draw as well as a foreground |
| **B1 / B2** | Endpoints reduced to **COD10K + NC4K**. No correlation may be reported on CHAMELEON |
| **B3** | Reads `d2_leaked_names.json`. §3.3 gives it a measured starting point for noise-driven render variance (~37–40 grey levels), which is what best-of-K feasibility rests on |
| **C1** | Reads `d2_leaked_names.json` for the 7 exclusions |
| **C3** | Endpoint metrics on COD10K (primary) and NC4K; CHAMELEON is out |
| **E0** | Its bit-exact reproduction claim gains a required qualifier: same shard count, same input listing |
| **Reporting** | Any table with a CHAMELEON column must drop it. 53.9 % contamination is not a footnote |

---

## 5. What D2 does not establish

- **Everything here is a lower bound on contamination.** Coverage is exact duplicates plus
  same-dimension re-encodes. **Rescaled** copies are *not* covered — a duplicate saved at a different
  resolution falls outside every dimension group and is invisible to this sweep. So are crops, flips,
  colour shifts, and different photographs of one specimen. 25 of CHAMELEON's 35 unmatched images have
  no same-dimension candidate at all and are therefore **unchecked, not clean**.
- **The tolerance is a choice**, which is why §1.4 reports the sweep and s4b's gap analysis rather
  than one number.
- **s8 uses one source image** (`0004`) and three positions. It establishes the mechanism decisively —
  T3 is a positive prediction — but the *magnitude* of noise-driven divergence rests on that one
  foreground. B3 should characterise the distribution.
- **No claim about GT masks.** D2 hashes images; whether endpoint *masks* are duplicated is not
  measured.
- **CHAMELEON is not checked against its own publication** — only against the copies on this disk.

---

## 6. Why the log has four D2 blocks, and a FAIL in all of them

| Block | Result | Cause |
|---|---|---|
| 1 | 8 PASS / 1 FAIL | All steps ran. But `4443` was used in this document while existing only as arithmetic, not as a logged metric |
| 2 | 8 PASS / 1 FAIL | `unique_raw_hkuis` / `unique_authors_pool` promoted into the script |
| 3 | 9 PASS / 1 FAIL | **s4 rewritten** — thumbnail bucketing replaced by exhaustive within-dimension search after an audit showed ~27 % recall (§3.2). CHAMELEON moved 10/76 → 41/76. Tolerance sweep added |
| 4 | 11 PASS / 1 FAIL | **s8 added** — the controlled seed experiment, so the mechanism in §3.3 is produced by committed code rather than an ad-hoc shell session |
| 5 | **12 PASS / 1 FAIL** | **s4b added** — endpoint nearest-neighbour gap analysis, so §1.4's claim that 41 is a data boundary is measured rather than asserted. Authoritative |

The FAIL in every block is the CHAMELEON contamination threshold. **It stays.** A failing threshold
that reflects the data is the instrument working; the previous package's problem was a record in which
nothing ever failed.

Blocks 1 → 2 and 3 → 4 are both the traceability rule: a number that cannot be traced to a log block
does not belong in a document, even when it is correct. Block 2 → 3 is different and more serious — it
is a measurement being *wrong*, found by auditing my own method rather than by the method reporting a
problem.

(Four earlier attempts produced nothing loggable — a `%`-formatting bug, a dict-key collision, a
missing import, and one computationally infeasible design, all mine, all resolved before the run that
logged. Nothing was logged, so nothing was superseded.)

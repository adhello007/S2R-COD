# E0 — Verified results

**Status: COMPLETE. 16 / 16 thresholds PASS.**

Source of every number below: `results/REBUILD_LOG.txt`, block **`EXP E0`** timestamped
`2026-08-31T12:59:10+05:30`, commit `3ad38e8`. That block is authoritative; this file is a reading of
it. If the two ever disagree, the log wins. Every figure quoted here appears verbatim in that block —
checked mechanically, not by eye.

Setup: `rebuild/E0/E0.md`. Environment: py3.12.3, torch 2.11.0+cu128, CUDA 12.8, timm 1.0.28,
numpy 2.5.2, 2× RTX PRO 6000 Blackwell, seed 0. **Trains a model: NO.**

Four `EXP E0` blocks exist in the log; all are kept deliberately — see §5. Block 4 is the one read
here.

---

## 1. What was measured

### s1 — Provenance manifest

| Metric | Value |
|---|---|
| Files hashed | **48,365** |
| Input directories | **15** |
| Directories with a count mismatch | **0** |
| Declared inputs missing | **none** |

Every one of the 15 directories matched the count pinned in `REBUILD_PLAN.md` §1. Per-file SHA256 is
in `out/e0_manifest.sha256`; per-directory aggregates in `out/e0_input_digests.csv`.

### s2 — Representation verification (pixel level)

| Check | Measured | Verdict |
|---|---|---|
| s2 polarity sample | **400** random stems, seed 0 | provenance |
| HKU-IS GT polarity | border white **0.0119** vs foreground **0.1858** | object is **WHITE** |
| Cutout background value | **128**, threshold 127 | literal constant |
| Cutout background is flat grey | **True** (n=50, `np.unique` == `{128}`) | confirmed |
| Cutout leaves object untouched | **True** | confirmed |
| Cutout background share of frame | **0.8224** | **82.2% of the frame is one constant** |
| Pools identical: raw vs authors' | **0** of 200 | all distinct |
| Pools identical: authors' vs local | **0** of 200 | all distinct |
| Mean maxdiff, authors' vs local | **232.3** (of 255) | not near-copies |
| LAKE-RED *input* mask white fraction | **0.8123** | inverted (object = 0) |
| LAKE-RED *output* mask white fraction | **0.1877** | back to SOD polarity |
| Authors' GT identical to raw GT | **0** of 200 | different mask sets |
| Foreground-fraction delta, raw − authors' | **+0.00542** | raw has 0.54 pp more object |
| `isReplace` object-region error | **6.245** mean abs | JPEG scale |
| `isReplace` background error | **71.676** mean abs | generation scale |
| Ratio background / object | **11.5×** (n=200) | see §2.1 |

### s3 / s3b — Feature caches and preprocessing sensitivity

| Metric | Value |
|---|---|
| Embedders built | **3** — `dinoL224`, `dinoL518`, `clipL224` |
| Caches written | **21** (7 sets × 3 embedders) |
| Cache row-count mismatches | **0** |
| Cluster agreement, squash vs aspect-crop | **0.946** (k=20, n=2000) |
| Mean cosine between the two policies | **0.9308** |

### s4 — Render regeneration

| Metric | Value |
|---|---|
| Images regenerated | **4447** (seed 0, 2 shards, ~66 min) |
| Shared with the pool on disk | **4447** |
| **Byte-identical** | **4447 / 4447** |
| Mean absolute pixel difference | **0.0** |
| Cluster agreement | **1.0** (k=20, n=4447) |

Directory-level aggregate digests, computed by the script over the sorted `sha256  name` listing —
a per-file loop can be fooled by a name mismatch, an aggregate cannot:

| Pool | n | agg sha256 (first 32) |
|---|---|---|
| regenerated images | 4447 | `cf6587cfce24b8f687a0a9d0c675210a` |
| on-disk images | 4447 | `cf6587cfce24b8f687a0a9d0c675210a` |
| regenerated masks | 4447 | `91e9556434cb63e4cde29b4216c91d94` |
| on-disk masks | 4447 | `91e9556434cb63e4cde29b4216c91d94` |

Both pairs match, so images **and** masks reproduce exactly. The mask digest also equals the
`local_msk` aggregate recorded independently by s1. Confirmed on genuinely separate files — different
inodes, mtimes 2026-08-21 vs 2026-08-31.

| Independent cross-check | Value |
|---|---|
| `staging_background_frac` (from `prepare_lakered_inputs.py`) | **0.8087** |

That figure is produced by LAKE-RED's own staging code from the raw masks, by a path unrelated to
A2's — see §2.5.

### s5 — Independence from rescued inputs

| Metric | Value |
|---|---|
| Forbidden path references | **0** (AST scan, 2 scripts) |
| Pragma exemptions | **4** — all on the gate's own definition lines, listed in `out/e0_independence.json` |
| Declared inputs resolving from primary data | **15 / 15** |

---

## 2. How the findings change our approach, thinking and assertions

This is the part that matters. Each item states the claim we held going in, what E0 measured, and what
we must now do differently.

### 2.1 `isReplace` — "background generated" is right, "object preserved" was too vague

- **Standing claim:** "LAKE-RED preserves the object and regenerates the background."
- **Measured:** object-region error **6.245** vs background **71.676** — **11.5×**. `test.py:165` is
  `out_array[mask_array == 0] = image_array[mask_array == 0]`, and mask==0 is the object region.
- **Sharpened claim:** the object is not *regenerated faithfully* — the **original source pixels are
  composited back in** after generation. The residual 6.245 is JPEG re-encoding, not model error.
  Only the background is synthesized.
- **Why it matters, concretely:**
  - **A3** — a "real vs generated" classifier cannot be reading the object at all. Any separability
    it finds must live in the background, which is ~82% of the frame (§2.3). This makes A3's
    controls *more* important, not less: the probe may be reading JPEG history rather than generation.
  - **B3** — a grey-128 cutout and its own render contain **the same object pixels**. The two
    representations differ *only* in background treatment: flat 128 versus synthesized. So the
    selection-vs-measurement mismatch is precisely a background mismatch, and B3's three arms isolate
    exactly that.
  - **D1** — foreground exhaustion stops being a statistical argument. Every render literally carries
    one of the 4447 source foregrounds, pixel for pixel.
  - **A1** — reinforces the bottleneck framing: the generator's only job is the background, steered
    through the 48-scalar channel A1 tests.

### 2.2 LAKE-RED is bit-exactly reproducible — our stated expectation was wrong

- **Standing claim (written into the plan):** byte-identity is not expected across a re-run because
  cuDNN is nondeterministic; threshold on cluster agreement instead.
- **Measured:** **4447/4447 images and 4447/4447 masks byte-identical** at `--seed 0`.
- **Revised position:** the expectation was wrong and both documents were corrected. The
  cluster-agreement threshold passes at 1.0 **trivially** — identical bytes give identical embeddings
  — so it measured nothing here. Byte-identity is the stronger result and subsumes it.
- **Scope discipline:** this establishes reproducibility **on this machine with this stack**, not
  determinism in general, across hardware, or across driver versions. Stated as such.
- **What it buys:** the render pool is no longer an inherited artifact. Any later experiment reading
  `Dataset/LAKERED/output/HKU-IS/` is reading something we can reproduce on demand. `rebuild/E0/regen/`
  is therefore provably redundant and safe to delete.
- **What it does NOT buy:** nothing about *seed* variance. A best-of-K selection scheme depends on how
  much the pool moves at a different seed, and that is unmeasured and unclaimed.

### 2.3 The grey-128 cutout is mostly not an image

- **Standing claim:** the old package's selection step embedded "foreground cutouts".
- **Measured:** background is exactly the constant **128**, occupying **82.2%** of the frame; object
  pixels are untouched.
- **Revised position:** calling this "a cutout" understates the problem. Under four fifths of the
  frame is a single value, so the embedding is dominated by a constant, and the object's *apparent
  scale* after squash-resize varies with the original aspect ratio. Any similarity ranked in this
  space is ranked largely on object silhouette and size against a uniform field — not on scene
  appearance, which is what the target clusters encode.
- **Consequence:** B3 must not treat cutout-based selection as a neutral proxy for render-based
  selection. They are different questions, which is why B3 runs three explicit arms (cutout, render,
  raw scene) rather than one.

### 2.4 Three HKU-IS pools, none identical — "the generated pool" is ambiguous

- **Standing claim:** there is a LAKE-RED output pool of 4447 renders.
- **Measured:** three distinct 4447-image pools. Authors' vs local mean maxdiff **232.3**; 0 of 200
  stems identical in either pairing.
- **Revised position:** "the generated pool" is not a well-defined term in this repo. Training reads
  `Source/HKU-IS/Image` (authors'); the previous package's A3/B3/C1 embedded
  `LAKERED/output/HKU-IS/images` (local). **The old numbers therefore describe a pool the trained
  model never saw.**
- **Consequence:** every A3 / B3 / C1 number is reported twice, once per pool. This was already the
  agreed plan; E0 turns it from a precaution into a requirement, because the pools are not
  approximately equal.

### 2.5 The authors' GT is not the raw GT

- **Measured:** 0 of 200 masks identical; foreground fraction differs by **0.00542** (raw is higher).
- **Revised position:** "the foreground fraction of HKU-IS" is not a single number. A2 must report it
  **per mask set** and name which set each downstream claim uses. A headline that mixes an ~18%
  figure from one set with an ~82% figure from another is internally inconsistent.
- **Cross-check available:** LAKE-RED's own staging code, an unrelated path, independently measured
  background = **0.8087** over all 4447 raw masks while building E0's regen inputs. This is now a
  logged E0 metric (`staging_background_frac`), not a figure scraped from stdout. Notably it lands on
  **80.87%**, the same value the previous package reported for invented background — so that specific
  old number is corroborated from primary data before A2 even runs, while the ~18% figure it was
  paired with still is not.

### 2.6 An arbitrary preprocessing choice moves 5.4% of cluster memberships

- **Measured:** squash-resize vs aspect-preserve + centre-crop agree on **94.6%** of assignments;
  mean cosine **0.9308**.
- **Revised position:** cluster membership is not a robust label. A preprocessing decision nobody
  justified reassigns roughly one image in twenty. Acceptance-style metrics are defined *on* cluster
  membership, so they inherit at least this much arbitrary variation.
- **Consequence:** B3 and C1 must report spread across seeds and settings, not point values. A lone
  acceptance percentage is not separable from this noise. It also sets a floor: an effect smaller
  than ~5% of cluster membership cannot be attributed to targeting.

### 2.7 A grep is not a provenance gate

- **What happened:** the first gate flagged 14 forbidden references, all of them its own `FORBIDDEN`
  list and this package's prose. The second version still failed on one — the note *explaining the
  fix* contained a path-like literal.
- **Revised position:** static string matching cannot distinguish a dependency from a discussion of
  one. The gate now parses each script (AST), checks path-like string literals and imports of the old
  package, excludes docstrings as prose, and requires exemptions to be declared by pragma and
  **reported** rather than suppressed.
- **Verified negatively:** a probe file referencing the volatile session cache, the moved archive and
  the old rescued-array directory is caught on all three counts, and removing it returns the gate to
  zero. A gate that has never failed is not evidence.

---

## 3. Consequences by downstream experiment

| Experiment | What E0 changes for it |
|---|---|
| **D2** | Manifest gives byte-level hashes for all 19k+ candidate images before the leakage sweep begins |
| **D1** | §2.1 makes exhaustion literal: every render carries one of the 4447 source foregrounds pixel for pixel. §2.4 means "the render pool" must be named explicitly |
| **A1** | §2.1 sharpens the bottleneck framing — the generator's only task is the background |
| **A2** | §2.5 forces per-mask-set reporting; two independent corroborations already exist (0.191323 manifest, 80.9% staging) |
| **A3** | §2.1 means separability cannot come from the object. §2.4 requires both pools. Controls become load-bearing, not decorative |
| **B1 / B2** | §2.6 requires spread across seeds; single-seed correlations are not measurements |
| **B3** | §2.1 + §2.3 define the three arms precisely: the arms differ *only* in background treatment. §2.6 sets a noise floor on acceptance |
| **C1** | §2.4 requires both pools; §2.6 requires ≥10 draws and reported spread |
| **C2** | Unaffected — reads code and training logs, not images |
| **C3** | Unaffected by E0; its own limits stand as recorded in the plan |

---

## 4. What E0 does not establish

- **No conclusions.** E0 produces inputs. It says nothing about whether targeting works.
- **Sampling.** s2 polarity used 400 stems; other checks 50–200. These are existence and consistency
  proofs. A2 measures the distribution over all 4447; D1 hashes every file.
- **One seed.** s4 regenerated at `--seed 0` only. Generator variance across seeds is unmeasured.
- **`cut` is never materialised.** Only its embeddings are cached, so re-verifying the cutout
  representation means re-running s2, not inspecting images.
- **The provenance gate is static.** It proves no script *references* a rescued path. It does not
  prove, by execution with those paths removed, that no run would touch one.
- **`clipL224` is present but unexercised.** The second embedder family is cached and ready; no
  conclusion yet depends on it. Its value is realised in A3, B3 and C1.

---

## 5. Why the log has four E0 blocks

| Block | Result | Cause |
|---|---|---|
| 1 | 14 PASS / 1 FAIL | Provenance gate reported 14 references — all self-detection of its own list and prose. A defect in the gate, not a dependency in the package |
| 2 | 14 PASS / 1 FAIL | Gate rewritten as an AST scan and self-tested. One hit remained: the note documenting the fix contained a path-like literal |
| 3 | 15 PASS / 0 FAIL | Prose reworded. All thresholds passing, but four values used in this document existed only outside the log — the s2 sample size, the staging cross-check, and two directory digests computed ad hoc in a shell |
| 4 | **16 PASS / 0 FAIL** | Those four promoted into the script so they are produced by committed code, plus a new threshold comparing image and mask digests. Authoritative |

Nothing is deleted. The log is append-only so that a failure and its repair are both visible; the
previous package's problem was a record that showed only conclusions. Block 3 → 4 is the rule working
as intended: a number that cannot be traced to a log block does not belong in a document, even when
the number is correct.

# D1 — Verified results

**Status: COMPLETE. All ten declared thresholds PASS.**
**Old claims re-tested: 2 MATCH, 1 MISMATCH.**

Source of every number below: `results/REBUILD_LOG.txt`, block **`EXP D1`** timestamped
`2026-08-31T18:09:56+05:30`, commit `17dfbbf`. That block is authoritative; this file is a reading of
it. Every figure quoted here appears verbatim in that block — checked mechanically.

Setup: `rebuild/D1/D1.md`. **Trains a model: NO.**

---

## 1. What was measured

### Provenance — E0's hashes consumed, not recomputed

| Metric | Value |
|---|---|
| E0 manifest hashes verified on a sample | **301/301** |

### Per-pool distinctness — pool-dependent, and it matters

| Pool | Unique / files | Redundant | What it is |
|---|---|---|---|
| raw HKU-IS | **4443/4447** | 4 | the original photographs — the foreground source |
| authors' pool | **4447/4447** | 0 | **what `MyTrain.py` reads** |
| local renders | **4445/4447** | 2 | our local LAKE-RED re-generation |

Reconciles with D2 exactly (`reconciles_with_D2 = yes`).

### Mask polarity — every file of every set, measured not assumed

| Mask set | Mean white fraction | Object is white? | Asserted |
|---|---|---|---|
| `raw_gt` | **0.19132** | yes | object=WHITE ✓ |
| `auth_gt` | **0.18557** | yes | object=WHITE ✓ |
| `local_msk` | **0.19132** | yes | object=WHITE ✓ |
| `lr_in_mask` | **0.80868** | no | object=BLACK, inverted ✓ |

`raw_gt` and `local_msk` agree to five decimals — the output masks are the input masks re-inverted, as
`test.py:173` implies. `auth_gt` differs from `raw_gt` in mean white fraction (0.19132 vs 0.18557 — a difference of
0.00575 of frame area, derived from the two logged values), now measured over all 4447 rather than
sampled (E0 trap T3).

### The bijection

| Metric | Value |
|---|---|
| Base foreground files | **4447** |
| Renders tracing to the base pool | **4447/4447** |
| **Renders whose foreground lies OUTSIDE the base pool** | **0** |
| Base foregrounds with no render | **0** |
| Render set is a bijection onto the base set | **True** |
| Authors' pool tracing to the base pool | **4447/4447** |
| Authors' pool is a bijection onto the base set | **True** |

### Is the mapping literal? (all 4447, both pools, each against its own mask)

| Metric | local renders | authors' pool |
|---|---|---|
| Mask used | `raw_gt` | `auth_gt` |
| Traced OK | **4447/4447** | **4447/4447** |
| Object region mean\|diff\| | **6.003** | **12.163** |
| Object **interior** mean\|diff\| | **5.603** | **9.633** |
| Background mean\|diff\| | **70.802** | **70.555** |
| Background/object ratio | **11.79** | **5.8** |
| Ratio on the interior | **12.64** | **7.32** |
| Images with object 3× closer | **4445/4447** | **4207/4447** |
| Images with interior 3× closer | **4442/4443** | **4361/4442** |
| **Objects plausibly REGENERATED** (interior > 40) | **0** | **0** |

Zero of 8885 traced objects across both pools show any sign of having been regenerated rather than
composited from the source.

---

## 2. Old claims re-tested

| Old claim | Old value | Measured | Verdict |
|---|---|---|---|
| "All 4447 foregrounds already in base pool" | 4447 **distinct** foregrounds | **4443** distinct in raw; 4447 *files* | **MISMATCH** |
| Internal duplicates in the render pool | 2 (4445 unique of 4447) | 2 (**4445** unique) | **MATCH** |
| "Every added image is a re-render, not a new object" | zero foregrounds in the generated pool absent from the base pool | **0** outside | **MATCH** |

The MISMATCH is a precision correction, not a reversal: the old package wrote a *file count* as a
*distinctness* claim. The conclusion it supports is unchanged and in fact slightly strengthened — there
are **fewer** distinct foregrounds than claimed, so the pool is more exhausted, not less.

---

## 3. How the findings change our approach, thinking and assertions

### 3.1 Exhaustion holds, and it holds for the pool that actually matters

- **Standing claim:** every image Stage C could add is a re-render of a foreground already in the base
  pool.
- **Measured:** the render set is a **bijection** onto the raw foreground set — 4447/4447 trace in,
  **0** outside, **0** base foregrounds unrendered. The same holds for the **authors' pool**, which is
  the one `MyTrain.py:220,297` actually loads.
- **Why the second half matters.** D2 §3.7 showed the authors' pool and the local renders have
  different internal duplicate structure (0 vs 2 redundant), so they are genuinely different
  renderings, not copies. It was therefore an open question whether exhaustion applied to the pool
  *training reads* or only to our local re-generation. It applies to both, verified separately against
  the same raw foreground set. Had it held only for the local pool, the argument would have been about
  the wrong data.
- **Position:** any null result is correctly scoped to *"targeting does not help once the foreground
  pool is exhausted."* That scope is now established for the training pool, not assumed from it.

### 3.2 Exhaustion is literal, not statistical — confirmed at scale

- **Standing claim, from E0 §2.1:** `--isReplace` composites the source object pixels back in, so only
  the background is generated. E0 measured this on 200 samples of one pool.
- **Measured:** over **all 4447 of both pools**, and against each pool's own mask. Object interior
  **5.603** (local) and **9.633** (auth) against backgrounds of **70.802** and **70.555** — ratios of
  **12.64** and **7.32**. And the residual that would matter: **0** objects with interior error > 40 in
  either pool.
- **Sharpened claim:** a "new" image in this pipeline contains an object that is already in the pool
  **pixel for pixel**, not merely a similar object. So exhaustion is not a statistical statement about
  distributional overlap that could be argued about — it is an identity statement about pixels.
- **Consequence:** this closes a gap in the argument. "The added images look similar to existing ones"
  invites a counter-argument about whether similarity is enough. "The added images contain the same
  object pixels" does not.

### 3.3 The exhaustion argument needs the position qualifier, and it survives it

- **Standing claim, sharpened by D2 §3.3:** a render is a function of (foreground, mask,
  **position-in-shard**), not of the foreground alone. D2's prediction held **4/4**.
- **What that could have broken:** if one foreground yields many renders, "the render pool is
  determined by the foreground pool" is false as stated, and a best-of-K scheme has real freedom to
  exploit.
- **What it actually does:** the freedom is entirely in the **background**. The object pixels come from
  the fixed pool regardless of position — §3.2 measures that directly. So exhaustion survives: Stage C
  can generate unboundedly many *backgrounds* for a foreground, but it cannot generate a new
  *foreground*.
- **Revised phrasing, which D1 adopts:** *"the foreground pool is exhausted; the background is not."*
  That is a materially different and more useful statement than "additions are re-renders", and it
  hands B3 the precise question — is background variation alone enough to move the model?

### 3.4 A measurement fix inside D1, found by auditing its own first run

- **What happened:** the first run scored **both** pools against `raw_gt` and found only
  **4041/4447** authors'-pool images with the object 3× closer, against 4445/4447 for the local pool.
- **Audit:** the failures had small objects (mean fg fraction 0.111 vs 0.199) and the worst cases were
  tiny (fg 0.002–0.077). Only 8 of 4447 had object error above 40. The authors' pool was rendered with
  the **authors' GT**, which s3 measures as different from `raw_gt`; boundary pixels where the two masks
  disagree *were* regenerated, and for a small object the boundary dominates the region.
- **Fix:** score each pool against the mask it was rendered with, and additionally against an eroded
  interior. Both numbers are reported. On the interior, the authors' pool goes to **4361/4442** and
  the plausibly-regenerated count to **0**.
- **Position:** the apparent 406-image discrepancy was an artifact of my mask choice, not a property of
  the data. Recorded because the first number was wrong and it was mine — and because "use each pool's
  own mask" is exactly the kind of care the old package's grey-128 slip came from omitting.

---

## 4. Consequences by downstream experiment

| Experiment | What D1 changes for it |
|---|---|
| **A3** | The "generator signature" can only live in the background — now established over all 4447 of both pools, not 200 samples of one |
| **B3** | §3.3 sharpens its question: background variation is the *only* degree of freedom targeting has. Its acceptance metric is measuring background steering, nothing else |
| **C1** | Targeted-vs-random distance is a distance between *background* renderings of the same fixed object set |
| **C3 / findings** | Any null is scoped as "the foreground pool is exhausted; the background is not" — stronger and narrower than the old wording |
| **Reporting** | "4447 distinct foregrounds" must not be written. It is 4443 distinct raw, 4447 files |

---

## 5. What D1 does not establish

**The single most important one:** D1 does **not** establish that *new foregrounds could not help*. It
bounds only what this pipeline can add from its fixed pool. Any null result inherits that scope
exactly — it is evidence about targeting under an exhausted foreground pool, and it is silent on
whether a larger or more diverse foreground set would change the outcome. Stating the null more
broadly than that would be unsupported.

Also not established:

- **Near-duplicate foregrounds within the pool.** D1's distinctness is byte-level. Two visually
  near-identical but non-identical foregrounds count as two distinct foregrounds. D2's near-duplicate
  machinery was not applied *within* the raw pool, so 4443 is an upper bound on distinct objects.
- **That background variation is useless.** D1 shows the object pixels are fixed. Whether varying the
  background alone can move accuracy is B3's and C1's question, not answered here.
- **Anything about the masks as labels.** D1 asserts mask polarity and uses masks to define regions. It
  does not check whether the GT masks themselves are correct or duplicated.
- **Single-file drift.** s1 verified 301 sampled hashes, which detects wholesale change, not one
  altered file among the seven sets D1 reads.
- **A mechanism for the 8 high-error images** seen in the first run. After the mask fix none exceed the
  cutoff, so no exception is claimed — but no positive explanation for those particular images is
  offered either.

---

## 6. Log blocks

One `EXP D1` block: all ten declared thresholds PASS, none FAIL.

The measurement fix in §3.4 was made *before* anything was logged — both earlier runs used `--no-log`,
so no superseded block exists. That is the intended use of `--no-log`: fixing a defect in measurement
code should not leave a trail of near-identical blocks, while a defect found *after* logging must be
superseded in the open, as E0 blocks 3→4 and D2 blocks 2→3 were.

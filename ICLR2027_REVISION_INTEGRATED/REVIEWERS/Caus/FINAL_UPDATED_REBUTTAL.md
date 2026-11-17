<!--
FOR THE CORRESPONDING AUTHOR. Not posted. Two OpenReview comments, each pasted exactly as the text between its
BEGIN/END markers. Lengths: tools/count_chars.py (limit 5,000 characters per comment).
Locators checked against paper/build/REVISED_MARKED.aux by tools/check_locators.py.
Our initial response (8 Nov 2026) is already posted; this is a follow-up.
Long-form evidence: rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/ (FINAL_UPDATED_REBUTTAL.md, EXPERIMENTAL_EVIDENCE.md).
Superseded in the package draft: "the ±0.005 equivalence criterion is not met" (true of the eight-seed campaign only;
the confirmatory campaign now establishes it on the primary cell), and "we will narrow the title" (not allowed during
discussion; camera-ready instead).
-->

<!-- BEGIN COMMENT 1 -->
## Follow-up to our response, 1/2: results (CW-01, Q1)

We thank the reviewer again. This follow-up to our posted response reports the results of what we committed to, and what we could not do. In the revised PDF, changes for this review are teal and changes serving two or more reviewers are orange (legend in the general response). Locators refer to the revised PDF.

### CW-01: contribution beyond a sanity check

We agree that the probe on its own is close to a sanity check, and post-review analysis shows it is closer than we said.

Re-running the original probe code from the frozen embeddings reproduces every committed number: +0.0073 Cohen's *d* for the signal over its own shuffle, −0.0649 against an arbitrary cluster, and a mean effective-rank ratio of 0.634. We then ran further allocation shapes through the same selector (N = 1000, the same 20 random draws):

| Selection | Clusters funded | Held-out *d* vs. random | Participation-ratio ratio |
|---|---|---|---|
| perfectly even quota (no concentration) | 75 | 0.52 | 0.855 |
| C10 (targeted) | 75 | 0.64 | 0.754 |
| CSHUF (same shape, shuffled) | 75 | 0.61 | 0.840 |
| five worst clusters (oracle) | 5 | 0.72 | 0.56 |
| the same five-cluster shape, shuffled | 5 | 0.55 | 0.94 |

→ **§3.2; App. I ("Separability does not require concentration").**

Even an unconcentrated quota separates from random, because the selector takes the renders nearest each cluster centre. Concentration does not set the effective rank either.

We have therefore corrected the manuscript's sentence that the probe "was detecting the concentration the whole time". The separation comes from the selector's matching and the budget's concentration, and the lower rank is an empirical property of these selections.

What stands, and what the paper now leads with, is the controlled comparison. At a fixed shape, the direction of the signal adds nothing to separability (+0.0073 *d*) and nothing detectable to accuracy. The CHAMELEON audit is presented as a separate contribution.

### Q1: an oracle with a different shape

No, the submission did not test one: CORACLE only re-aims C10's shape. We pre-registered three oracle shapes at the same budget, pool and selector, all built from the same true-error vector, plus a same-shape shuffle of one of them. Each was trained on SINet at the three committed seeds (12 runs), and the committed B, C10 and CORACLE runs were reused after a reuse gate. These arms read COD10K-test labels to choose their training data, so they are leaky diagnostics, never methods; NC4K labels are read by no allocation.

| Contrast (SINet, 3 seeds) | Δ COD10K | × bar | Δ NC4K | Verdict |
|---|---|---|---|---|
| ten worst clusters − CORACLE (shape) | +0.0022 | 0.38 | +0.0011 | within noise |
| ten worst clusters − its shuffle (aim) | −0.0002 | 0.03 | −0.0009 | within noise |
| error-proportional − CORACLE (flat shape) | +0.0023 | 0.40 | +0.0028 | within noise |
| five worst clusters − CORACLE | +0.0011 | 0.20 | +0.0005 | within noise |

→ **Table 2 (§3.1, rows ORS); App. I.** Bars are 2σ̂ = 0.0057 (COD10K) and 0.0065 (NC4K), df 14.

No shape resolves a gain over the C10-shaped oracle, even though the label leak could only help these arms. At the ten-cluster shape, true-error aim does no better than shuffling.

Two caveats on the design. The error-proportional shape is nearly flat, so its direction cannot be tested with this selector. The five-cluster arm has no same-shape control.

These are nulls at three-seed sensitivity: effects below about 0.006 can be missed. They cover SINet only and say nothing about shapes we did not try.

**Corrections to the manuscript:**
- The original oracle was said to turn "our score did not help" into "no score of any quality helped here". That holds only at C10's shape, and the sentence is now scoped (§3.1).
- The manuscript said every pre-registration was committed before its runs. The oracle campaign's rule was written before any oracle score existed, but committed 62 minutes after its first run started. App. B now states this, cites the seed expansion's rule at the correct commit, and names the tags that preserve both commits.
<!-- END COMMENT 1 -->

---

<!-- BEGIN COMMENT 2 -->
## Follow-up to our response, 2/2: results (CW-02, CW-03, Q2)

### CW-02: bounded generalisability

Agreed, and done. The abstract, introduction, a new Scope paragraph (§4) and the conclusion now bound the null to:
- an offline LAKE-RED pool that repaints the backgrounds of 4,447 fixed foregrounds;
- two-round S2R-COD training, with N = 1000 over k = 75 frozen clusters;
- SINet and SINet-v2;
- the COD10K-test and NC4K endpoints.

The null does not extend to online or adaptive generation, other generators or other tasks.

Within that scope the null is now sharper. A separately pre-registered confirmatory campaign on SINet establishes equivalence within ±0.005 $S_\alpha$ between targeted and random allocation on the primary cell. It is incomplete, at 16/15/15 of 27 seeds per arm.

| Contrast (SINet, COD10K-test) | Seeds | Δ | 90% CI | TOST *p* | Reading |
|---|---|---|---|---|---|
| C10−B, eight seeds (post hoc) | 8/8 | +0.0024 | [−0.0012, +0.0059] | 0.101 | neither |
| C10−B, confirmatory | 15/16 | +0.0006 | [−0.0027, +0.0039] | 0.015 | equivalent |
| C10−CSHUF, confirmatory | 15/15 | −0.0009 | [−0.0051, +0.0034] | 0.056 | neither |

→ **Table 3 (§3.1); App. C.**

**A modern detector could not be added:**
- CamoFormer's repository has no training entry point.
- CTF-Net has training code but no licence.
- Both release weights trained on the images our protocol treats as unlabelled targets, which would leak their labels.
- No GPU time remained beyond the oracle experiment.

§4 states that a modern transformer detector is untested.

### CW-03: foreground bottleneck

We agree this may limit any steering policy; we do not claim it causes the null. We re-measured independently:
- **Provenance.** All 4,447 renders trace to a source photograph, and none of the 8,885 traced objects shows regenerated object pixels. Object interiors are preserved to about 6/255.
- **Coverage.** In our initial response we quoted k-NN recall of 0.13–0.54 without saying it is measured at k = 5. The value depends on k, but the ordering does not:

| k | Our renders | Generator's source photographs |
|---|---|---|
| 3 | 0.07–0.48 | 0.60–0.64 |
| 5 | 0.13–0.54 | 0.71–0.75 |
| 10 | 0.25–0.63 | 0.84–0.88 |
| 20 | 0.38–0.75 | 0.95–0.97 |

→ **§3.3; App. E.**

- **No foreground-varying generator was available.** Camouflage Anything and RealCamo out-paint around a preserved foreground, and neither had released code when we checked. Rendering new real cut-outs through LAKE-RED would vary object identity but not object pixels, and needed GPU time we did not have.

Whether a generator that creates new objects would let steering help is untested, and §4 says so.

### Q2: modern backbone and new generator

We did the scoping. Neither replication could be run in the discussion period, for the reasons above. We have checked the candidate detectors and generators for training code, licence, checkpoint provenance and what they actually change, and the interaction contrasts are defined. We will not generalise the null beyond LAKE-RED/S2R-COD, whichever way a future replication lands.

**Correction.** In our initial response we wrote that exploratory boundary effects "depend on architecture". At eight seeds, no boundary contrast clears its bar on either architecture, and a direct test of the interaction is not resolved either way (§3.2; App. C).

**Title.** ICLR does not allow title changes during discussion. For the camera-ready version we will retitle to remove the downstream concentration claim, as proposed in the general response.
<!-- END COMMENT 2 -->

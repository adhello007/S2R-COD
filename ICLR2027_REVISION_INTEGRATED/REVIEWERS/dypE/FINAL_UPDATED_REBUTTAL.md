<!--
FOR THE CORRESPONDING AUTHOR. Not posted. Two OpenReview comments, each pasted exactly as the text between its
BEGIN/END markers. Lengths: tools/count_chars.py (limit 5,000 characters per comment).
Locators checked against paper/build/REVISED_MARKED.aux by tools/check_locators.py.
Our initial response (8 Nov 2026) is already posted; this is a follow-up.
Long-form evidence: rebuild/REBUTTAL/ICLR2027_REBUTTAL_dypE/STUDENT_RESULTS/ (FINAL_UPDATED_REBUTTAL.md Part A, EXPERIMENTAL_EVIDENCE.md).
Superseded in the package draft: "equivalence at ±0.005 is not established / smaller gains are not excluded" (true of the
eight-seed campaign; the pre-registered confirmatory campaign, run for reviewer RL5B, now establishes equivalence on the
primary cell), and "50/76 ... 16 unchecked" (50 stands; the 16 are COD10K-test re-encodes).
CHAMELEON counts are the released detectors' only. animal-54, flagged by the Caus package's independent detector
(5e7a2f9), was withdrawn by the author (73c18d6) and is not claimed.
-->

<!-- BEGIN COMMENT 1 -->
## Follow-up to our response, 1/2: results (CW-01, Q1, Q2)

We thank the reviewer again. This follow-up to our posted response reports the analyses we committed to and one new pre-registered experiment, and it corrects numbers we gave. In the revised PDF, changes for this review are purple and changes serving two or more reviewers are orange (legend in the general response). Locators refer to the revised PDF. Post-review analyses of the eight-seed runs are exploratory and re-decide no pre-registered verdict.

### CW-01 / Q1: how well are smaller improvements ruled out?

The reviewer was right that the eight-seed campaign does not exclude small gains, and pairing by seed does not change that. A separately pre-registered confirmatory campaign now settles the primary cell: SINet, arms B, C10 and CSHUF, fresh seeds, Welch TOST at ±0.005. It is incomplete. Power outages left 16 (B), 15 (C10) and 15 (CSHUF) of 27 planned seeds per arm, all analysed as pre-registered.

| Primary cell (SINet, COD10K, C10−B) | Δ | 95% CI | 90% CI | TOST *p* | Reading |
|---|---|---|---|---|---|
| eight seeds, Welch (submitted) | +0.0024 | [−0.0020, +0.0067] | [−0.0012, +0.0059] | 0.101 | neither |
| eight seeds, paired by seed | +0.0024 | [−0.0023, +0.0070] | [−0.0014, +0.0061] | 0.111 | neither |
| confirmatory, 15/16 seeds | +0.0006 | [−0.0033, +0.0045] | [−0.0027, +0.0039] | 0.015 | **equivalent** |

→ **Table 3 (§3.1).** The paired analysis for all four cells is in **Table 10 (App. C)**.

- **Pairing does not help.** B redraws its images at every seed, so a seed shares training randomness but not data, and the paired scores are uncorrelated (r = −0.04). The targeted arm leads on 6 of 8 seeds (exact sign-flip *p* = 0.29).
- **What is excluded.** On the primary cell, the confirmatory 90% interval lies inside ±0.005, so gains of 0.005 or more are excluded. H1 survives a Holm correction across the campaign's four tests (*p* = 0.030).
- **What is not excluded.** Against the same-shape shuffle the confirmatory result is "neither" (95% CI [−0.0060, +0.0043]). SINet-v2 has only the eight-seed campaign, and there gains of about 0.005 or less are not excluded (paired *p* 0.100–0.114; Table 10).
- **Scale.** +0.0142 is the reproduced method's gain over its own baseline in our setup: a study-specific reference, not a field-wide threshold. ±0.005 is a margin we chose, about a third of it.

### Q2 (part): how much do the compared training sets differ?

**Correction.** In our initial response we said about 48% of injected images differ between arms, about 8.8% of the training pool. Those figures describe the three concentrated arms. For the decisive targeted-vs-random comparison, the correct values are larger:

| Comparison | Injected images that differ | Share of the 5,447-image pool |
|---|---|---|
| targeted vs. random (decisive) | 77% (209–246 of 1,000 shared; ≈225 expected by chance) | 14.1% |
| among the three concentrated arms | 45–51% | 8.3–9.4% |

→ **App. C ("How much the trained comparison is attenuated").**

Images present only in the targeted arm make up about 14% of source draws in round one and 10% in round two. These are expected values, because sampler order was not logged. The pseudo-labelled sets appended between rounds overlap at Jaccard 0.58–0.68. That is a second, post-treatment difference, which we report rather than adjust for.
<!-- END COMMENT 1 -->

---

<!-- BEGIN COMMENT 2 -->
## Follow-up to our response, 2/2: results (CW-02, Q2, Q3)

### CW-02: concentration and downstream performance

**Correction.** In our initial response we cited SINet boundary gains of about 1.37× (C10−B) and 1.34× (CINV−B) their bar. Those were three-seed figures; the eight-seed values follow. We re-scored all 64 eight-seed runs on both architectures and endpoints at thresholds 0.4, 0.5 and 0.6, and the three-seed values reproduce exactly.

| Boundary-IoU, COD10K, gain over random | SINet | SINet-v2 | SINet − SINet-v2 |
|---|---|---|---|
| targeted (C10−B) | +0.0046 [−0.0066, +0.0158], 0.30× bar | +0.0002 [−0.0061, +0.0064] | +0.0044 [−0.0075, +0.0163] |
| reversed (CINV−B) | +0.0098 [+0.0039, +0.0157], 0.64× bar | +0.0033 [−0.0009, +0.0074] | +0.0065 [−0.0001, +0.0131] |

→ **§3.2; Table 8 and "Architecture, multiplicity and domain mix" (App. C).**

- None of the 140 eight-seed contrasts survives a Holm correction (smallest adjusted *p* = 0.50). We have withdrawn the claim that this was "the strongest form of the result".
- The architecture interaction is not resolved either way.
- CINV's unadjusted lead cannot come from concentration, which C10 shares exactly. One untested candidate is domain mix: the targeted, shuffled and reversed arms put 53%, 29% and 20% of the budget on CAMO, and neither endpoint contains CAMO.

A pre-registered dose-response experiment then tested directly whether concentration changes accuracy (SINet, 35 runs). The answer was no: the twice-as-concentrated level gained +0.0021 Boundary-IoU, 0.11× its bar (Table 7, App. C). Concentration claims are now restricted to the training sets. The SINet-v2 replication was not run.

### Q2: larger contrasts and more diverse foregrounds

We preflighted larger matched budgets with the exact selector. The rule, fixed in advance, was to train only if the differing pool share grew by at least 1.5×.

| Budget | 1,000 | 2,000 | 3,000 | 4,447 |
|---|---|---|---|---|
| pool share that differs (targeted vs. random) | 14.1% | 17.2% | 13.1% | 0% |

The preflight failed, so nothing was trained: random selection draws from the same 4,447 foregrounds that targeting ranks, and every injected render re-uses a base-pool foreground. Under App. E's estimator, the concentrated selections cover more of the target than random draws (0.62–0.64 against 0.35–0.43 in one embedding space), yet accuracy does not follow. Whether a generator that creates new objects would change the conclusion is untested (§4, Scope).

### Q3: CHAMELEON and COD protocols

Both detectors reproduce the submitted counts exactly. **Corrections and additions** to our initial response:

| Count (of 76) | Value |
|---|---|
| training-pool copies found by the released detectors (a floor) | 50 |
| re-encodes of COD10K-test images (including all 16 we called unchecked) | 32 |
| in CAMO-250 (we said three: 3 byte-identical, plus 1 re-encode) | 4 |
| duplicated somewhere in COD10K or CAMO | 74 |
| no duplicate found anywhere | 2 |

→ **§3.4; Table 17 and "What the overlap means for each protocol" (App. F).**

- **Supervised training** sees 50 of these photographs with their COD10K or CAMO masks, which breaks independent evaluation whether or not scores move.
- **Unlabelled adaptation (ours)** exposes the model to the images but not to their labels. 14–32 matches per run (mean 24.7) were re-used with the model's own pseudo-label.
- **Checkpoint selection** on CAMO-250 opens a label-based selection path through 4 photographs.
- **Evaluation:** with 32 shared re-encodes, CHAMELEON and COD10K-test are not independent benchmarks.
- We claim no score inflation, and CHAMELEON is not one of our endpoints. COD10K-test itself contains 7 images byte-identical to COD10K-train images, which every arm sees unlabelled; no contrast is affected (App. F).
<!-- END COMMENT 2 -->

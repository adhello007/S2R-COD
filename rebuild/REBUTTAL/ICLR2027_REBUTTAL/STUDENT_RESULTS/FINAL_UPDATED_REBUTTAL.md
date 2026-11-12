# Response to Reviewer dypE (updated after follow-up analyses)

*Draft for the corresponding author. Part A is the full response for the record. Part B is the
paste-ready OpenReview version (≤ 5,000 characters). Part C audits Part B's length. Nothing here has
been posted.*

---

## Part A: Full response

We thank the reviewer for a careful reading and for recognising the controls and the CHAMELEON
audit. The review asked us to bound the null more precisely, separate geometry from downstream
accuracy, and spell out contamination pathways. We have done all three using the trained models we
already had. The numbers under "Additional validation" and "Results" are post-review. We recomputed
them from the stored predictions and selection records of the 64 eight-seed runs, with no new
training. Before producing any new number, we checked that every stored per-run metric reproduces the
submitted value exactly, 1,152 of 1,152 to six decimals. The post-review analyses are exploratory:
none re-decides a pre-registered verdict. Two results go against statements in the submission, and we
report them first: the boundary-metric result does not hold at eight seeds (CW-02), and the "8.8%"
contrast describes the wrong comparison (CW-01).

### CW-01. Statistical sensitivity and interpretation of the negative result

**Response.** We agree. The pre-registered rule, twice the pooled per-run standard deviation plus
sign agreement, is a decision threshold on per-run spread. It is not a confidence bound and cannot
show that there is no effect. We now report the decisive comparison on three separate scales (the
frozen rule, an interval, an equivalence test) and say which gains it excludes and which it does not.
One correction to our own text: the 8.8% figure the reviewer quotes describes the comparisons among
the three concentrated arms, not targeted versus random.

**Additional validation (post-review).** A paired analysis over the eight matched training seeds,
beside the Welch analysis in the paper. Realised overlap measured from the selection records of every
run. Expected exposure under the pinned schedule. A preflight of larger matched budgets
(QA-02).

**Results.** Primary cell (SINet, COD10K-test, S-measure), targeted minus random:

| | Estimate | 95% interval | One-sided 95% upper bound | Equivalence at ±0.005 |
|---|---|---|---|---|
| Submitted (Welch, unpaired) | +0.0024 | [−0.0020, +0.0067] | +0.0059 | not shown, p = 0.101 |
| Post-review, paired by seed | +0.0024 | [−0.0023, +0.0070] | +0.0061 | not shown, p = 0.111 |

The targeted arm is ahead on 6 of 8 seeds (two-sided paired p = 0.27). The smallest margin at which
equivalence would be shown is ±0.0061. Removing any single seed leaves the estimate between +0.0013
and +0.0037, and the paired interval always contains zero.

How much the arms actually differ (post-review):
- Targeted and random selection share 209–246 of their 1,000 injected images per seed, which is close
  to the 225 expected by chance. So **77% of injected images, 14.1% of the 5,447-image training pool,
  differ** in the decisive comparison. Our "about 48%" and "8.8%" are correct only for the three
  concentrated arms (45–51% of injections, 8.3–9.4% of the pool).
- Under the pinned schedule an epoch draws 4,048 of the 5,447 source images. Images present only in
  the targeted arm are therefore about 14% of source draws in round one and 10% in round two. These
  are expected values; the order in which images were sampled was not logged.
- Between rounds each arm appends its own roughly 2,000 pseudo-labelled target images. The targeted
  and random sets of these overlap only at Jaccard 0.58–0.68. This is a second difference that follows
  from the first round, and we report it rather than adjust for it.

**Interpretation.** The campaign excludes the reference improvement (+0.0142) and any gain above about
0.006–0.007. It does not exclude gains of +0.005 or less, and it does not establish equivalence at
±0.005. The realised contrast is larger than we stated (14.1%, not 8.8%), but it is still a minority
of the training signal. We will state the bound in the abstract, results and conclusion.

### CW-02. Downstream validation and generalisability of the concentration hypothesis

**Response.** We agree, and the eight-seed data change one of our claims. The geometric result stands:
concentrating the budget changes what is selected, and shuffled or reversed allocations reproduce the
separation. The downstream boundary result does **not** hold up as we wrote it. In the submission it
came from three seeds. Re-scored on all eight, targeted selection no longer beats random, so we
withdraw the sentence calling it "the strongest form of the result". We also tested the architecture
dependence directly, as the reviewer asked, instead of comparing two separate significance results.

**Additional validation (post-review).** We re-scored Boundary-IoU and Boundary-F for all 64 runs, on
both endpoints, at binarisation thresholds 0.4, 0.5 and 0.6. The three-seed values reproduce the
submitted table exactly (1.37× and 1.34× the bar). We added a direct test of the architecture
interaction and verified the quota invariants of the concentrated arms. We audited foreground
diversity and coverage of the target data.

**Results.** Boundary-IoU at threshold 0.5, COD10K-test, eight seeds, gain over random (paired 95% CI):

| | SINet | SINet-v2 | Difference between architectures |
|---|---|---|---|
| Targeted | +0.0046 [−0.0066, +0.0158], 0.30× bar | +0.0002 [−0.0061, +0.0064] | +0.0044 [−0.0075, +0.0163], p = 0.43 |
| Reversed signal | +0.0098 [+0.0039, +0.0157], 0.64× bar, 7/8 seeds | +0.0033 [−0.0009, +0.0074] | +0.0065 [−0.0001, +0.0131], p = 0.053 |

The pattern is the same at all three thresholds and on NC4K. None of the 140 eight-seed contrasts we
examined (two boundary metrics and S-measure, both architectures and endpoints, three thresholds)
survives a Holm correction; the smallest adjusted p is 0.50. On S-measure the reversed arm is also
ahead of random on SINet/COD10K, +0.0045 [+0.0015, +0.0074], but inside the frozen bar (0.66×), and
not after correction across the twenty secondary contrasts (adjusted p = 0.17). The concentrated arms
are verified to share one quota multiset exactly: every quota vector sums to 1,000 and is the same
after sorting, while 72–73 of the 75 cluster quotas differ between arms.

Generator scope: every one of the 4,106 distinct renders injected across arms and seeds re-renders a
foreground already in the base pool (0 new objects). Each render's mask matches its base mask at
median IoU 0.97, and none is identical. Measured with the appendix's coverage estimator (k-NN recall, k = 5), every 1,000-image synthetic set covers far less of
the real target than the generator's own source photographs do (0.71). The share covered is 0.35–0.43
for random draws and 0.62–0.64 for the three concentrated selections, which differ only in direction
and cover about equally. Concentration moves the set closer to the target, but trained accuracy did not
follow. The pool-level values reproduce the submitted appendix table exactly.

**Interpretation.**
1. Geometry: concentration changes the selected data. This is unchanged.
2. Downstream: we find **no resolved benefit of concentration**. The targeted and reversed arms have
   identical concentration, but only the reversed arm shows a gain, so concentration cannot explain
   it. We report that gain as an exploratory signal on one architecture. One candidate explanation,
   which we have not tested: the three same-shape arms put very different shares of the budget on CAMO
   images (53%, 29% and 20% for targeted, shuffled and reversed), and neither endpoint contains CAMO
   images.
3. Architecture: the interaction is not resolved either way. We cannot say the two architectures
   differ, or that they agree.
4. Generator: our null covers a fixed, offline pool of re-rendered backgrounds around existing
   foregrounds. It does not cover adaptive generation or synthesis of new objects. No generator able
   to create new foregrounds was available to us, so that experiment was not run and remains open.

### QA-01. How well do the results rule out smaller improvements?

**Response.** There is no field-wide minimum meaningful S-measure gain for camouflaged object
detection. +0.0142 is the gain of the reproduced method over its own baseline in our setup, a study
reference rather than a standard. ±0.005 is a sensitivity margin we chose after the fact. We now
provide the paired analysis the reviewer asked for.

**Additional validation (post-review).** Paired analysis by matched training seed for all four
architecture–endpoint cells. It gives the paired interval, paired equivalence test, an exact sign-flip
test, a bootstrap, and leave-one-seed-out. Each is shown beside the Welch analysis, with the
within-pair correlation reported.

**Results.** Targeted minus random, eight seeds:

| Cell | Paired 95% CI | Welch 95% CI | Equivalent at ±0.005 (paired p) |
|---|---|---|---|
| SINet, COD10K (primary) | [−0.0023, +0.0070] | [−0.0020, +0.0067] | no (0.111) |
| SINet, NC4K | [−0.0038, +0.0045] | [−0.0033, +0.0040] | **yes** (0.016) |
| SINet-v2, COD10K | [−0.0081, +0.0059] | [−0.0067, +0.0045] | no (0.114) |
| SINet-v2, NC4K | [−0.0077, +0.0058] | [−0.0068, +0.0049] | no (0.100) |

Pairing does not sharpen the comparison. The random arm redraws its images at every seed, so a seed
shares training randomness between arms but not data, and the paired scores are uncorrelated
(r = −0.04 on the primary cell).

**Interpretation.** Gains as large as the reference are excluded in every cell. Gains of about 0.005
or smaller cannot be excluded on three of four cells. The negative result therefore does not extend to
small improvements, and we will say so.

### QA-02. How much do the limited training-set differences and synthetic diversity affect the conclusion?

**Response.** We measured both. We could not train new experiments: the trained comparison would need
GPU time we do not have during the discussion period. More importantly, the preflight shows that
larger budgets would not create a larger contrast in this pool.

**Additional validation (post-review).** Realised per-seed overlap (CW-01). A preflight simulating the
exact selection procedure at matched budgets of 2,000, 3,000 and 4,447 images, against a rule fixed
beforehand: train only if the differing share of the training pool grows at least 1.5-fold. A
foreground-diversity and coverage audit.

**Results.** The differing share of the training pool is 14.1% at the committed 1,000, 17.2% at 2,000
(1.22×), 13.1% at 3,000 and 0% at 4,447. Random selection draws from the same finite set of 4,447
foregrounds that targeting ranks, so the two converge as the budget grows. The preflight fails, and we
did not train. A fixed-budget alternative, drawing the random arm only from images the targeted arm did
not pick, would raise the share to 18.4%. That is a different sampling algorithm and we did not run it.
On diversity: the renders re-use base foregrounds one-to-one (median mask IoU 0.97 with the original),
and synthetic sets cover at most 0.64 of the real target, against 0.71 for the real photographs the
generator started from. Only about a fifth of the endpoint's structural-error variance lies between
clusters (20.5%, reproduced; 18.9–20.9% with each arm's own predictions). That caps what any
cluster-wise allocation could change.

**Interpretation.** Whether a much larger contrast, or more diverse foregrounds, would change the
conclusion is untested. In this pool a larger budget cannot produce it, and testing new foregrounds
needs a different generator. We will state both as limitations and not imply that either has been
evaluated.

### QA-03. How does CHAMELEON contamination affect common COD protocols?

**Response.** We re-ran both duplicate detectors after the review, unchanged and at the published
thresholds. Every submitted count reproduces exactly: 50 of 76 photographs (41 re-encodes and 9
rescaled or cropped copies), 44 with a partner in COD10K-train, 16 unchecked, and 0 exact-hash matches
with the training pool. We then separated the protocols as the reviewer suggested.

**Additional validation (post-review).** A per-image exposure matrix covering supervised training,
unlabelled target adaptation, checkpoint selection and evaluation. The same released detector pointed
at the validation and test splits as well as the training pool. A count of how often the duplicated
photographs entered our own pseudo-labelled sets. The two CHAMELEON mask releases compared on the same
predictions.

**Results.**
- **Supervised training (image and mask).** A model trained the standard way on COD10K-train and
  CAMO-train has fitted the ground-truth masks of 50 of the 76 CHAMELEON photographs. This breaks
  independent evaluation whether or not the score moves.
- **Unlabelled target adaptation (our protocol).** The same 50 photographs are in our unlabelled target
  pool. Every run sees them without labels. Between rounds, 14–32 of them per run (mean 24.7) were
  re-used with the model's own predicted mask as a pseudo-label. No CHAMELEON annotation is used
  anywhere. This is exposure to the image, not label leakage, and its effect would depend on the
  method.
- **Checkpoint selection.** Four CHAMELEON photographs are in CAMO's 250-image test split, which we use
  to select checkpoints by MAE: three byte-identical, and one re-encoded copy we had not reported. Any
  protocol that selects on CAMO-test and reports CHAMELEON has a label-based selection path.
- **Evaluation.** 32 of the 76 photographs are re-encodes of COD10K-test images, including all 16 we
  had called unchecked. CHAMELEON and COD10K-test are therefore not independent benchmarks. In total,
  74 of 76 CHAMELEON photographs appear somewhere in COD10K or CAMO. NC4K shares none.
- **Mask releases.** The two circulating CHAMELEON annotations have opposite polarity. After alignment
  they agree at mean IoU 0.69, and only 27 of 76 masks are identical. The same predictions score MAE
  0.2196 against one release and 0.0816 against the other.

**Interpretation.** We do not claim inflated scores: our difficulty analysis found no advantage for
the duplicated images, and no model trained without them exists to compare against. What the audit
supports is a protocol statement. CHAMELEON is not an independent test set for models trained or
adapted on COD10K/CAMO, nor for models also evaluated on COD10K-test. Any CHAMELEON number must name
its mask release. We report COD10K-test and NC4K, neither of which depends on CHAMELEON. None of these
overlaps touches a number in our paper, because CHAMELEON is not one of our endpoints.

### Changes we will make to the manuscript
- **Abstract and Conclusion:** state the bound. Gains above about 0.007 are excluded; smaller gains are
  not; equivalence at ±0.005 is not shown.
- **Results, null section:** add the paired and Welch intervals, the scale reference, and why pairing
  does not help. Soften "no score of any quality helped here".
- **Results, concentration section:** replace the three-seed boundary claim with the eight-seed result
  and the direct interaction test, and withdraw "the strongest form of the result".
- **Appendix:** correct the 48% / 8.8% sentence, add the exposure and pseudo-label overlap, and qualify
  the pseudo-label means (40 vs 64 runs).
- **Concentration and why-it-fails sections:** state that "covers no more of the target manifold"
  depends on the coverage estimator, and add the different domain mix of the same-shape arms.
- **Discussion:** add the larger-budget preflight and the generator scope (re-rendered fixed pool;
  new-object generation untested).
- **CHAMELEON sections:** add the 32 COD10K-test duplicates and the fourth CAMO-250 duplicate, the
  protocol table, and "no duplicate found" instead of "clean" for the 10 same-dimension negatives.

### What remains unresolved
- Whether gains of +0.005 or less exist. The data permit them.
- Whether a materially larger contrast would reveal an effect. This pool cannot produce one.
- Whether uncertainty guidance helps when the generator can create new foregrounds. Not tested.
- Why the reversed-signal arm shows a small, uncorrected advantage on SINet. Not explained.
- Whether CHAMELEON contamination changes any published score. Not measurable without a model trained
  without the duplicates.

---

## Part B: OpenReview version (paste-ready)

See the separate file [`FINAL_UPDATED_REBUTTAL_OPENREVIEW.md`](FINAL_UPDATED_REBUTTAL_OPENREVIEW.md). It
is kept as its own file so that its character count covers exactly what would be pasted.

## Part C: Character-count audit of Part B

| Measure | Value |
|---|---|
| File | `FINAL_UPDATED_REBUTTAL_OPENREVIEW.md` (exactly the text to paste) |
| SHA256 | `b29ec58716b9604bd3e4e9f84d76bc17bcf12b61afa52a1eea74283c98be16fb` |
| Unicode code points, Python `len(str)` | **4658** |
| Unicode code points, `wc -m` (C.UTF-8) | **4658** |
| Code points after NFC normalisation | 4658 |
| Code points without the final newline | 4657 |
| UTF-8 bytes (`wc -c`) | 4685 |
| Lines | 25 |
| Non-ASCII characters used | 6 distinct (U+00B1 U+00D7 U+03C3 U+2013 U+2212 U+2264) |
| Limit | 5,000 characters including headings and Markdown |
| Margin | 342 characters |
| Verdict | PASS |

The two counters are independent: the Python string length, and coreutils `wc -m` in a UTF-8 locale.
If OpenReview counts UTF-8 bytes instead of characters, the text is 4685 bytes, still under 5,000.

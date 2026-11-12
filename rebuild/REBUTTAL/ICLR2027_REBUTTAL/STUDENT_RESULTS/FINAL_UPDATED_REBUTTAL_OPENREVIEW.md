We thank the reviewer. All new numbers below come from re-analysing the stored predictions of our 64 eight-seed runs (no new training; every stored metric reproduces exactly). They are post-hoc and re-decide no pre-registered verdict. Two of them correct our submission.

**CW-01 / QA-01: how small a gain is excluded**
The 2σ rule is a per-run spread threshold, not a confidence bound. On the primary cell (SINet, COD10K), targeted minus random is +0.0024: Welch 95% CI [−0.0020, +0.0067]; paired by seed [−0.0023, +0.0070]; one-sided 95% bound +0.0061. Pairing gains nothing: the random arm redraws its images at every seed, and paired scores are uncorrelated (r = −0.04). Equivalence at ±0.005 is not shown (paired p = 0.111). It is shown on SINet/NC4K (p = 0.016) but not on either SINet-v2 cell. +0.0142 is the reproduced method's gain in our setup, a study reference rather than a field standard. So: gains above about 0.007 are excluded; gains of 0.005 or less are not.

Correction: our "8.8%" describes the three concentrated arms. Targeted and random share only 209–246 of 1,000 injected images per seed (chance: 225), so 14.1% of the training pool differs in the decisive comparison. Under the pinned schedule, targeted-only images are about 14% of source draws in round 1 and 10% in round 2 (expected values; sampling order was not logged). Round-2 pseudo-label sets differ too (Jaccard 0.58–0.68), a second channel that follows from round 1.

**CW-02: concentration vs. downstream accuracy**
The geometric result stands; the boundary result does not. The submitted 1.37×/1.34× came from three seeds. At eight seeds (SINet, COD10K, Boundary-IoU), targeted minus random is +0.0046 [−0.0066, +0.0158], 0.30× its bar. Reversed-signal minus random is +0.0098 [+0.0039, +0.0157] (7/8 seeds, 0.64× bar). No contrast among the 140 we examined survives Holm correction. Tested directly, the architecture difference is not resolved (targeted: +0.0044 [−0.0075, +0.0163]; reversed: +0.0065 [−0.0001, +0.0131]). The targeted and reversed arms share an identical quota multiset (verified), yet only the reversed arm shows a gain, so concentration cannot explain it. We withdraw "the strongest form of the result" and report no resolved downstream benefit of concentration.

Scope: all 4,106 distinct injected renders re-use a base-pool foreground (0 new objects). Our null covers a fixed, offline, background-only generator. It does not cover adaptive or new-foreground generation, which we could not test.

**QA-02: larger contrast, more diversity**
Larger budgets do not help in this pool. Simulating the exact selection procedure, the share of the training pool that differs is 14.1% at N = 1,000, 17.2% at 2,000, 13.1% at 3,000 and 0% at 4,447: random and targeted draw from the same 4,447 foregrounds and converge. Our preflight rule required 1.5×, so no training was run. Drawing the random arm only from unselected images would give 18.4%, but that is a different algorithm. More diverse foregrounds need a different generator; we list this as untested.

**QA-03: CHAMELEON by protocol**
Re-running both detectors unchanged reproduces 50/76 (41 re-encodes + 9 rescaled or cropped), 44 in COD10K-train, 16 unchecked, and 0 exact-hash matches with training data.
- Supervised training (image and mask): standard COD10K/CAMO training has fitted the masks of 50 CHAMELEON photos.
- Unlabelled adaptation (our protocol): the same 50 are in our target pool. Every run sees them unlabelled, and 14–32 per run were re-used with the model's own predicted mask. No CHAMELEON label is used anywhere.
- Checkpoint selection: 4 CHAMELEON photos are in CAMO's 250-image test split, which we select on (3 byte-identical, plus 1 re-encode we had missed).
- Evaluation: 32 of 76 are re-encodes of COD10K-test images, including all 16 "unchecked"; 74/76 appear somewhere in COD10K or CAMO.
- The two mask releases have opposite polarity; the same predictions score MAE 0.2196 against one and 0.0816 against the other.
We claim no score inflation: duplicated images were not easier, and no duplicate-free model exists to compare. CHAMELEON is not an independent test set for COD10K/CAMO-trained or -adapted models. Our endpoints are COD10K-test and NC4K; CHAMELEON is not one of them.

**Revisions:** the bound in the abstract and conclusion; paired and Welch intervals; eight-seed boundary results with an interaction test; the corrected contrast and exposure; the larger-budget preflight; the generator scope; and the CHAMELEON protocol table. Still open: gains ≤0.005, much larger contrasts, new-foreground generation, and the reversed arm's small advantage on SINet.

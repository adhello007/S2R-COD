Thank you, especially for asking what improvement would matter. Answering it changed how we state the result.

**Paired analysis at matched seeds.** Done [Tab. N]. The same seed gives every arm the same initialisation, but on the primary cell the within-seed correlation between targeted and random is essentially zero (r = −0.04). Pairing therefore doesn't narrow the interval: paired 95% CI [−0.0023, +0.0070], TOST p = 0.11 at ±0.005, against Welch's [−0.0020, +0.0067] and p = 0.10 (seed-expansion campaign, eight seeds per arm). We report both for every contrast.

**What improvement is meaningful for COD?** We anchor on the protocol itself, because any outside threshold would be our invention. The method this loop sits on gains 0.0142 S_α over mean teacher in our reproduction (0.0152 in S2R-COD's own Table 1), and seed-to-seed spread on the primary cell is 0.0025–0.0049 S_α. We take half that gain, about 0.007, as the smallest effect that would change which method a practitioner picks. Every targeted-versus-random cell is equivalent at that margin (TOST p ≤ 0.021 in all four cells). At your ±0.005, the primary cell is not. The table gives the smallest margin at which each comparison would pass, so a reader with a stricter threshold can apply it.

**Does concentration explain downstream accuracy?** Not established, and we no longer say it is. The boundary-metric support was a three-seed SINet result. Re-scored at eight seeds it does not hold: targeted minus random is 0.30× its bar on Boundary IoU [§3.2, App. D]. What survives: concentration explains why the training sets are separable, and no metric we tried shows direction mattering.

**More diverse foregrounds, or larger training-set differences?** The difference between the compared sets is larger than we wrote. 76.7% of injected images differ between targeted and random, so the effective contrast is 14.1% of the pool, not the 8.8% we gave in Appendix C (that figure applies to same-shape arms). We have not varied the foreground pool in this window, and the scope paragraph [§4] names that as untested.

**How CHAMELEON contamination enters each protocol** [new table, App. F]:
- **Supervised training on the standard split** (COD10K-train 3,040 + CAMO-train 1,000): 50 of 76 CHAMELEON images have their photograph, with its own mask, in the training set. 44 partners are in COD10K-train and 6 in CAMO-train.
- **Unlabelled target adaptation:** the same images sit unlabelled in the target pool. That is 44 under S2R-COD's target as described (COD10K-train) and all 50 under the 4,040-image pool as released.
- **Checkpoint selection:** 3 CHAMELEON files are byte-identical to images in CAMO-250, the split checkpoints are selected on.

In each case the issue is non-independence. We measured no score inflation on the leaked subset, and none of our endpoints uses CHAMELEON. Fifty is a floor: 16 images remain unchecked.

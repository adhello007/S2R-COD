# Updated Response to Reviewer Caus

We thank the reviewer for recognising the same-shape control and the failure diagnosis. We also thank
them for pressing on three boundaries we had stated too loosely: what the probe result does and does
not show, how far the null extends, and whether an oracle of a different *shape* would have helped.
Since our initial response we have run the validation we promised where it was feasible on the
compute available, and we report below what we could not do. New analyses are post-review. Every
number below can be traced to a committed table or log in the supplementary package.

### CW-01: Contribution beyond a sanity check

**Response.** We agree the paper is not a new detector or a positive augmentation method. Its
methodological contribution is a control for deciding *why* a steered synthetic-data budget differs
from a random one. A targeted allocation differs from random in two ways at once: how unevenly the
budget is spread, and where it points. A same-shape shuffle separates the two. We also agree with the
reviewer's premise in part: the geometric probe on its own is closer to a sanity check than to a
finding about detection.

**Additional validation.**
1. We re-ran the original probe and covariance code from the frozen embeddings and reproduced every
   committed table.
2. We asked directly whether concentrating a budget must lower effective rank, the measure we
   report, which is the participation ratio of covariance eigenvalues.
3. We ran every allocation shape we now have through the same selector, including a perfectly even
   one.

**Results.**
- **The original numbers reproduce exactly:** +0.0073 Cohen's *d* for the uncertainty signal over
  its own shuffle; −0.0649 against an arbitrary cluster; a mean effective-rank ratio of 0.634, lower
  in 20/20 cells. Permuting the probe's labels drives *d* to about zero.
- **Concentration does not imply lower rank.** For a two-cluster mixture, putting 90% of the budget
  on an isotropic cluster triples the effective rank relative to an even split, while putting it on a
  low-rank cluster cuts it to 1.2. In our pool, the most concentrated selection we built (five
  clusters, shuffled) keeps a near-random rank (ratio 0.94).
- **An even quota is still separable from random** (held-out *d* ≈ 0.5, rank ratio 0.86). The reason
  is the selector: it picks, for each cluster, the renders closest to that cluster's centre.

**Interpretation.** The reviewer is right that "different from a random draw" is nearly automatic
here, and it is so even without concentration. We will therefore correct our own sentence that the
probe "was detecting the concentration the whole time". What survives, and what we will lead with, is
the controlled comparison: at a fixed allocation shape, the direction of the uncertainty signal adds
nothing to the separation (+0.0073 *d*), and nothing measurable to trained accuracy (eight seeds,
below). We will describe the lower effective rank as an empirical property of these selections, not a
consequence of non-uniformity. We will also keep the CHAMELEON audit as a separate contribution. A
post-review re-check with an independent detector found one more contaminated image (`animal-54`, a
rescaled COD10K-train photograph), so the floor is at least 51 of 76.

### CW-02: Bounded generalisability

**Response.** Agreed. The null belongs to one pipeline: an offline LAKE-RED pool that repaints the
backgrounds of a fixed set of foregrounds, two-round S2R-COD self-training, a 1,000-image budget over
75 frozen clusters, SINet and SINet-v2, and the COD10K-test and NC4K endpoints. It does not extend to
online or adaptive generation, or to other tasks.

**Additional validation.** We re-derived every trained statistic in the paper with two independent
implementations, re-scored the committed predictions behind the runs we reuse, and assessed a modern
transformer-based detector for this protocol.

**Results.**
- **Every trained number reproduces:** the eight-seed targeting-versus-random gap is +0.0024 against
  a bar of 0.0069. Its post-hoc 95% interval is [−0.0020, +0.0067], which excludes the +0.0142
  reference effect but not small positive effects. The ±0.005 equivalence criterion is not met
  (p = 0.101).
- **A modern detector could not be added within this rebuttal.** CamoFormer's repository provides no
  training entry point. CTF-Net, the fallback, has training code but no licence. Both release weights
  trained on the very images our protocol treats as unlabelled targets, which would leak their labels.
  No GPU time beyond the oracle experiment below was available.

**Interpretation.** We will narrow the title, abstract and conclusion to the tested pipeline, state the
boundary in the discussion, and say plainly that a modern detector remains untested. That experiment is
not complete, and we do not imply that it is.

### CW-03: Foreground bottleneck

**Response.** We agree this may limit any steering policy. We do not claim it causes the null.

**Additional validation.** We re-measured provenance, coverage and mask quality independently, and
looked for a generator that changes the foreground itself.

**Results.**
- **The pool repaints backgrounds of a fixed foreground set.** All 4,447 renders trace to their source
  photograph (4,443 distinct), and none of 8,885 traced objects shows regenerated object pixels. The
  object interior differs from its source by about 6/255 on average, against about 71/255 for the
  background.
- **The pool covers less of the target than its own source photographs do,** at every neighbourhood
  size we tried. Our reported 0.13–0.54 is k-NN recall at k = 5; it rises to 0.38–0.75 at k = 20, while
  the source photographs reach 0.95–0.97.
- **The render masks are valid but shared by every arm:** none is empty, and many contain several
  objects, as HKU-IS does.
- **No suitable generator was available.** Two recent camouflage generators, Camouflage Anything and
  RealCamo, both out-paint around a preserved foreground, and neither had released code when we
  checked. The one route open to us, rendering new real cutouts through LAKE-RED, would vary object
  identity but not object pixels, and needed GPU time we did not have.

**Interpretation.** The audit supports the premise of the reviewer's concern: re-allocating over this
pool cannot create unseen object content. Whether a foreground-varying generator would let steering
help remains untested, and we say so in the revised discussion.

### QA-01: Different-shape oracle

**Response.** No, the submitted paper did not test one. CORACLE gives C10's existing quotas to clusters
ranked by true endpoint error. It tests where a fixed budget shape points, not whether that shape is
right. Our sentence that this shows "no score of any quality helped" was too strong. It holds only at
that shape.

**Additional validation.** Before any training, we pre-registered three oracle allocations of
different shapes at the same 1,000-image budget, the same generator pool and the same selector:
- **OR-PROP:** quotas proportional to each cluster's true error;
- **OR-TOP10:** 100 images to each of the ten worst clusters;
- **OR-TOP5:** 200 images to each of the five worst.

We also included a same-shape shuffle of OR-TOP10. These use the same endpoint-error vector as
CORACLE, so each comparison with CORACLE changes only the shape. They read COD10K-test labels to
choose training data, so they are leaky diagnostics, never methods. COD10K-test is not an unbiased
endpoint for them, and we read NC4K, whose labels no allocation uses, beside it. We trained these on
SINet at the three committed seeds. We compared them against the committed B, C10 and CORACLE runs,
which we reused after checking that code, data, selections and the first training step are identical
and that their committed metrics re-score exactly.

Two things were settled before training:
- **The error-proportional shape is nearly flat,** because per-cluster error varies only from 0.09
  to 0.47. Every rearrangement of its quotas leaves at least 84% of the selected images unchanged, so
  its direction cannot be tested with this selector. We did not train its shuffle, and used those
  runs for the five-cluster oracle instead.
- **That five-cluster oracle therefore has no same-shape control,** and we never read its contrast as
  isolating direction.

**Results.** All 12 runs completed, one start each, and all passed their completion checks. The bar is
twice the pooled seed-to-seed spread over the seven compared arms (2σ̂ = 0.0057 on COD10K and 0.0064
on NC4K, 14 degrees of freedom).

| Pre-registered contrast (SINet, 3 seeds) | Δ COD10K | sign | Δ NC4K | verdict |
|---|---|---|---|---|
| OR-TOP10 − CORACLE (shape, at true-error aim) | +0.0022 | 2/3 | +0.0011 | within noise |
| OR-TOP10 − its same-shape shuffle (aim, at the new shape) | −0.0002 | 2/3 | −0.0009 | within noise |
| OR-PROP − CORACLE (flat shape) | +0.0023 | 2/3 | +0.0028 | within noise |
| OR-TOP5 − CORACLE (shape and aim together) | +0.0011 | 2/3 | +0.0005 | within noise |

- **Secondary comparisons.** Every oracle arm lands between random allocation (B) and our own
  targeted arm (C10). Against B the differences are +0.0020 to +0.0032; against C10, −0.0019 to
  −0.0031. All are within noise.
- **Arm means.** On COD10K the seven arm means span 0.7134–0.7185. The top-ten oracle and its
  shuffle are 0.7165 and 0.7166.
- **Intervals (post hoc, three seeds, so unstable).** On COD10K the intervals for these four contrasts
  run from about −0.007 to +0.0095. They exclude the +0.0142 reference effect but not effects of a few
  thousandths.

**Interpretation.** Changing the shape of an oracle allocation, from C10's softmax shape to a near-flat
error-proportional one, a ten-cluster one or a five-cluster one, bought no resolvable gain on either
endpoint. The endpoint-label leak could only have helped these arms. At the ten-cluster shape, aiming by
true error did no better than the same quotas given to shuffled clusters. Together with the original
oracle, this extends "no ranking helped" from one allocation shape to the four we tested.

It is still a null at this sensitivity, not proof of no effect: effects below about 0.006 can be
missed with three seeds. It says nothing about shapes we did not try, nor about SINet-v2, which we did
not re-run. No oracle result is a claim of optimality, and none is evidence for a deployable method.
The pattern fits a constraint that sits downstream of allocation in this pipeline, such as the fixed
foreground pool of CW-03, though we have not shown that this is the cause.

We have also corrected a provenance statement while auditing the oracle campaign. Its
pre-registration was written before any oracle result existed, but it was committed 62 minutes after
the first oracle run started, not before it as the appendix says. The revision states this exactly,
and the commit is preserved.

### QA-02: Modern backbone and new generator

**Response.** We agree with both requests and with scoping the claim to the LAKE-RED / S2R-COD
pipeline. We did the scoping. We could not do the two replications within this rebuttal, for the
specific reasons given under CW-02 and CW-03: no licensed, trainable modern detector without
target-label leakage; no released generator that changes the foreground; and no GPU time beyond the
oracle experiment.

**Additional validation.** The preparation that can be done without a GPU is done. The candidate
detectors were checked for training code, licence and checkpoint provenance. The available generators
were checked for what they actually change. The interaction contrasts, whether the effect of direction
changes with the detector or the generator, are defined and ready to be estimated.

**Results.** None to report for either replication.

**Interpretation.** Our null stays bounded to LAKE-RED backgrounds over a fixed foreground set, SINet
and SINet-v2. We will not generalise it beyond that, in whichever direction a future replication
lands.

We will report negative and inconclusive outcomes as they are, and mark every post-review analysis as
such.

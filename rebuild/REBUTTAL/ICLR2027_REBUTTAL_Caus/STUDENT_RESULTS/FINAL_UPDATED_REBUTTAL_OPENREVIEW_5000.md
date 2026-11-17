# Updated Response to Reviewer Caus

We thank the reviewer for pressing on three boundaries we had stated too loosely. All new analyses are post-review. Every number below is traceable to a released table.

**CW-01 (contribution).** We agree this is not a new detector. The contribution is a control: a same-shape shuffle separates *how unevenly* a fixed budget is spread from *where* it points. We re-ran the original probe and covariance code from frozen embeddings and reproduced every table: +0.0073 *d* for the signal over its own shuffle, −0.0649 against an arbitrary cluster, effective-rank ratio 0.634 in 20/20 cells. The reviewer's premise is partly right, and we will say so. Concentration does not imply lower rank: putting 90% of a two-cluster budget on an isotropic cluster triples effective rank, and our most concentrated selection keeps a near-random rank (ratio 0.94). Even a perfectly even quota is separable from random (*d* ≈ 0.5), because the selector matches renders to cluster centres. We will drop "the probe was detecting concentration the whole time". What remains is that, at fixed shape, the uncertainty signal's direction adds nothing, geometrically or on trained accuracy.

**CW-02 (scope).** Agreed. The null belongs to an offline LAKE-RED pool that repaints backgrounds of fixed foregrounds, two-round S2R-COD, SINet/SINet-v2 and COD10K/NC4K. Every trained number re-derives with two independent implementations: the eight-seed targeting-vs-random gap is +0.0024 against a 0.0069 bar, 95% CI [−0.0020, +0.0067]. That interval excludes the +0.0142 reference effect but not smaller gains, and equivalence within ±0.005 is not met (p = 0.101). We will narrow the title, abstract and conclusion accordingly.

**CW-03 (foreground bottleneck).** We re-measured the pool independently. All 4,447 renders trace to 4,443 source photographs, and none of 8,885 traced objects has regenerated pixels. Coverage of the target is below that of the generator's own input at every neighbourhood size; our 0.13–0.54 is k-NN recall at k = 5. Re-allocation cannot create unseen objects. Whether a foreground-varying generator would let steering help remains untested.

**QA-01 (different-shape oracle).** No, the submitted paper did not test one. CORACLE re-aims C10's quota multiset, so our "no score of any quality helped" holds only at that shape. Before training we pre-registered three oracle shapes at N = 1000, the same pool and the same selector, built from the same endpoint-error vector as CORACLE:
- **OR-PROP:** quotas proportional to true error;
- **OR-TOP10:** 100 images to each of the ten worst clusters;
- **OR-TOP5:** 200 to each of the five worst;
- plus a same-shape shuffle of OR-TOP10.

These read test labels, so they are leaky diagnostics, never methods, and we read NC4K beside COD10K. The proportional shape is nearly flat, so any shuffle leaves at least 84% of images unchanged and its direction is untestable; we used those runs for the five-cluster oracle, which therefore has no same-shape control. SINet, seeds 42/43/45, against the committed B, C10 and CORACLE runs (reuse gate passed: identical code, data and first training step; committed metrics re-score exactly):
all four pre-registered contrasts are within noise on COD10K and NC4K (bar 2σ̂ = 0.0057; Δ COD10K: OR-TOP10 − CORACLE +0.0022, OR-TOP10 − its shuffle −0.0002, OR-PROP − CORACLE +0.0023, OR-TOP5 − CORACLE +0.0011). Every oracle arm lands between random and our targeted arm. This null holds although the label leak could only help these arms, so "no ranking helped" now covers four allocation shapes. It is still a null at three seeds, not proof of no effect.

We also correct a provenance statement: the oracle pre-registration was written before any oracle result but committed 62 minutes after its first run started.

**QA-02 (modern backbone, new generator).** We scoped the claim; we could not run either replication. CamoFormer releases no training code. CTF-Net has training code but no licence. Both ship weights trained on images our protocol treats as unlabelled. The available camouflage generators (Camouflage Anything, RealCamo) out-paint around a preserved foreground, and neither had released code. No GPU time remained beyond the oracle study. The null stays bounded to LAKE-RED and SINet/SINet-v2, and we will not generalise it in either direction.

# Initial Response to Reviewer Caus

We thank the reviewer for recognizing our same-shape control and failure diagnosis, and for asking us to distinguish a methodological contribution from improved COD accuracy. The oracle-shape and generalizability questions identify important boundaries of our evidence.

### CW-01: Contribution beyond a sanity check
**Concern (excerpt):** “From a contribution view point this has limited role in advancing the camouflage object detection methodology.”

**Response:** We agree this is **not a new detector or a positive augmentation algorithm**. The contribution is an experimental control for attributing gains from *where* a fixed synthetic budget is spent. Targeting versus uniform sampling changes both quota concentration and score alignment; CSHUF and CINV preserve the quota shape while shuffling/reversing direction (Table 1; Secs. 3–4). Geometry must not be mistaken for accuracy: the effective-rank ratio averages 0.634, but the targeting-specific probe increment over shuffle is only +0.0073 Cohen's d. Eight-seed direction contrasts remain unresolved on S-measure; exploratory boundary effects depend on architecture. We do **not** claim that every nonuniform allocation necessarily lowers effective rank—our finding is empirical for the studied pools. We will sharpen this distinction and emphasize the separate CHAMELEON contamination contribution.

### CW-02: Bounded generalizability
**Concern (excerpt):** “Findings may not directly transfer to task domains with vastly more expressive generative feedback loops.”

**Response:** Agreed. Our null pertains to the **offline LAKE-RED fixed-foreground pool and two-round S2R-COD-style protocol**, with 1,000 injections, 75 frozen clusters, and SINet/SINet-v2 evaluated on COD10K-test/NC4K. The generator is not updated during training (Methods). We therefore cannot infer a null for online adaptive generation or other task domains. We will narrow the abstract, claims, and conclusion accordingly and assess a modern detector if its training infrastructure is available. This is planned, not completed, validation.

### CW-03: Foreground bottleneck
**Concern (excerpt):** “The generator is constrained to reusing fixed foreground cutouts...”

**Response:** We agree this limitation may constrain steering, without claiming it is the proven cause of the null. Our audit found no regenerated foreground among 8,885 traced objects; the reported synthetic-to-real k-NN recall is 0.13–0.54 under the studied settings (Sec. 4.3; coverage appendix). Reallocation cannot create unseen object content. We will verify provenance and coverage computations and, if suitable generation code and masks are available, compare against genuinely foreground-varying synthesis at a matched budget. Coverage, label validity, and detection performance will be assessed separately; improved coverage alone is not evidence of improved COD.

### QA-01: Different-shape oracle
**Reviewer question:** “CORACLE keeps C10's shape. Did you test an oracle with a different shape (e.g., proportional to true error, or concentrated on the truly worst clusters)?”

**Response:** **No.** CORACLE places C10's existing quotas according to true endpoint-error rank; it tests **direction at fixed shape**, not whether that shape is optimal (Table 1; Appendix “Three Controls”). CORACLE–B is +0.0008 at three seeds on SINet/COD10K, inside its 0.0061 bar (Table 2); this does not exclude other shapes. We will evaluate error-proportional and top-error-cluster allocations at the same 1,000-image budget, with uniform, C10, CORACLE, and shape-matched controls, checking realized quotas and distinctness. Using test labels for an oracle is an **explicitly leaky diagnostic**, never a deployable method; we will prefer disjoint calibration labels where feasible and will not tune checkpoint selection using endpoint labels. We will report uncertainty and infeasibility transparently.

### QA-02: Modern backbone and generator
**Reviewer request:** “Replicate with one modern backbone and one foreground-varying generator, and scope the claim to the LAKE-RED/S2R-COD pipeline.”

**Response:** We agree. We will assess a reproducible modern transformer-based COD model and a generator that demonstrably changes foreground content while providing valid masks. We will preserve comparable budgets, splits, evaluation and checkpoint protocols and compare random, targeted, and shape-preserving shuffled policies. Testing the backbone and generator factors separately before their combination will clarify attribution. These experiments depend on available code, checkpoints, masks, and compute, and **are not yet complete**. Whether successful, inconclusive, or infeasible, they will not be used to generalize the current null beyond LAKE-RED/S2R-COD.

We will disclose negative and inconclusive results and identify any new analyses as post-review validation.

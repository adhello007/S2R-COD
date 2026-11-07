Thank you all for careful, specific reviews. Three concerns are shared, and we have revised the paper around each of them. A fourth change came out of re-checking our own evidence, and we put it first because it weakens a claim you may have credited.

**A result we withdraw.** The paper's "strongest form of the result" was a post-hoc boundary-metric effect on SINet: concentration cleared its bar at three seeds (C10−B 1.37× on Boundary IoU). We re-scored all eight seeds of the seed-expansion campaign, and it does not hold: C10−B is +0.0046, 0.30× its bar, with 5/8 seeds agreeing. The abstract and §3.2 no longer claim any downstream effect of concentration [§3.2, App. D].

**1. "No evidence of benefit" is not "no meaningful effect."** You are right, and the paper now says so in those words. On the primary cell (SINet, COD10K, eight seeds per arm), targeted minus random is +0.0024 with 95% CI [−0.0020, +0.0067]. It does not pass equivalence at ±0.005 (TOST p = 0.10). We state what the data allow: **we rule out benefits larger than +0.0067 S_α; smaller benefits remain possible.** A new table [§3.1, Tab. N] separates "failed to detect" from "evidence of equivalence" for every comparison, at two margins:
- **±0.005, your margin.** 5 of 16 comparisons pass.
- **±0.0071, half the method's own gain over mean teacher.** This was our pre-registered sensitivity target, not a declared margin. 13 of 16 pass, including every targeted-versus-random cell.

The asymmetry is the informative part. Targeting against its own shuffle, which holds the allocation's shape fixed, does pass at ±0.005 (p = 0.019). Targeting against random does not. Targeting-versus-random mixes concentration with direction, so a small concentration effect would sit exactly there, and the eight-seed design cannot see below about 0.006 (its 80%-power detectable effect is 0.0059). [If launched: a separate pre-registered campaign, 34 fresh seeds per arm with targeting, its shuffle and random, sized to resolve ±0.005 (power 0.86 at the observed gap), was committed before its first run and reports by 14 Nov.]

**2. Concentration explains the training set, not the accuracy.** Agreed. The claim is now split: concentration explains why targeted and random training sets are separable (established), and on trained accuracy neither concentration nor direction is resolved [abstract, §3.2].

**3. Scope.** A new paragraph [§4] names the bounds: LAKE-RED (background-only variation), a fixed pool of 4,447 foregrounds, the S2R-COD protocol, and the SINet family. The null concerns which synthetic images to add within that protocol.

**Other changes in the revision**
- Appendix C gave the effective contrast between targeted and random as about 8.8%. That figure belongs to pairs of same-shape arms. Between targeted and random, 76.7% of injected images differ, which makes it 14.1% of the pool.
- Appendix B now gives exact commit times for each pre-registration; one campaign's file was committed an hour after its runs started, before any result existed.
- Every post-hoc diagnostic in the paper (Tables 3 and 6, the CHAMELEON extension) is now re-emitted by its committed script into a dated log block. Two sweep values are corrected (0.52× → 0.51×, 0.14× → at most 0.15×).

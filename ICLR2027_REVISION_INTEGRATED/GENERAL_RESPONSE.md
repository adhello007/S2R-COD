<!--
FOR THE CORRESPONDING AUTHOR. Not posted. One OpenReview general comment: paste the text between the BEGIN/END markers.
Length: tools/count_chars.py (limit 5,000 characters). Reviewer-specific replies: REVIEWERS/<ID>/FINAL_UPDATED_REBUTTAL.md.
-->

<!-- BEGIN COMMENT G -->
## General response: revised manuscript and summary of changes

We thank the three reviewers and the AC. Our initial responses are posted; each reviewer now has a two-part follow-up with the results, inline tables and exact locations in the revised PDF. The main text is within the 10-page limit.

**Revision colours.** In the marked revision, changes addressing RL5B only are blue; changes addressing Caus only are teal; changes addressing dypE only are purple; revisions addressing two or more reviewers are orange. Orange overrides the individual colours. Uncoloured text is unchanged or was only moved. A clean, uncoloured copy has the same content.

**The claim, as now stated throughout.** Within the tested pipeline (LAKE-RED fixed render pool, S2R-COD protocol, SINet/SINet-v2, N = 1000), uncertainty-guided allocation shows no detectable benefit over random allocation.
- A pre-registered confirmatory campaign establishes equivalence within ±0.005 $S_\alpha$ on the primary cell.
- Same-shape controls show that the direction of the signal adds nothing detectable.
- The selector's matching and the budget's concentration explain how the selected training sets differ, but a pre-registered dose-response test found no effect of concentration on accuracy.
- The CHAMELEON audit is a separate contribution.

**Main changes**
- **Equivalence, not just non-detection** (RL5B, dypE; orange). New Table 3 (§3.1) gives the eight-seed Welch and paired intervals and a pre-registered confirmatory campaign. That campaign establishes equivalence on the primary cell: Δ = +0.0006, 90% CI [−0.0027, +0.0039], TOST $p$ = 0.015. It is **incomplete** (16/15/15 of 27 seeds per arm, after power outages), and against the same-shape shuffle on COD10K-test it is neither detected nor equivalent. All 16 eight-seed contrasts are in Table 9 (App. C).
- **Concentration restricted to the training set** (RL5B, dypE; orange). The pre-registered dose-response test did not support a downstream effect (Table 7). The three-seed boundary-metric result does not hold at eight seeds and is withdrawn (Table 8). One exploratory CINV−B signal is reported with its correction status.
- **Scope** (all three; orange). The abstract, introduction, a new Scope paragraph (§4) and the conclusion bound every claim to the tested generator, pool, clusters, architectures, training and budget. The foreground constraint is quantified, and coverage is reported at every k (App. E).
- **Oracle allocations of other shapes** (Caus; teal). Three pre-registered shapes, 12 runs; none resolves a gain (Table 2; App. I). The probe correction: even an unconcentrated quota separates from random under the same selector (§3.2).
- **Protocol-matched baselines** (RL5B; blue). RISE, supervised SINet-V2 and our trainer on real masks, under one scorer (Table 4, App. A).
- **Training-set contrast and CHAMELEON protocols** (dypE; purple):
  - the decisive comparison differs in 14.1% of the pool, not 8.8%;
  - a larger-budget preflight failed;
  - CHAMELEON shares 32 images with COD10K-test, and a 51st training-pool copy is reported;
  - the overlap's meaning is spelled out per protocol (Table 17, App. F).

**New work.** 99 trained runs after review:
- the confirmatory campaign, 46;
- the dose-response experiment, 35;
- the oracle shapes, 12;
- supervised references, 6.

**Not run:**
- the SINet-v2 dose-response replication;
- a higher operating point;
- a modern transformer detector (no licensed, leak-free training code);
- a generator that creates new foregrounds (none available).

Each is stated as a limitation, not implied.

**Corrections to our posted responses** (detailed in each reply):
- rule sensitivity 0.20, not 0.14;
- 80%-detectable effect 0.0087, not 0.008;
- boundary ratios 0.30×/0.64× at eight seeds, not 1.37×/1.34×;
- decisive contrast 14.1%, not 8.8%;
- RISE's detector is SINet-V2 trained on pseudo masks for the same images;
- CHAMELEON copies in CAMO-250 are four, not three.

The manuscript also corrects its pre-registration record: one rule (the oracle campaign's) was committed 62 minutes after its first run started, though before any of its results existed (App. B).

**Title.** ICLR does not allow title changes during the discussion period, so the title is unchanged here. For the camera-ready version we will retitle to remove the downstream concentration claim, proposing: *"Uncertainty-Guided Allocation of Synthetic Training Data Shows No Detectable Benefit for Camouflaged Object Detection."*
<!-- END COMMENT G -->

# RESULTS_SUMMARY: RL5B rebuttal

*Verified findings per reviewer concern. Every number is drawn from the artifact cited in `EXPERIMENTAL_EVIDENCE.md`.
EQ (EXP-01) is still training and is added on 17 Nov.*

## CW-01 / QA-01: absence of evidence vs equivalence

- **The submitted primary cell reproduces exactly** (SINet·COD10K, 8 seeds):
  - Δ(C10 − B) = +0.0024, Welch 95% CI [−0.0020, +0.0067];
  - TOST p = 0.101, so it is neither detected nor equivalent;
  - before correction, 5 of 16 contrasts are equivalent at ±0.005; after Holm, none.
- **The rule's sensitivity**, simulated as run (arm SDs, σ̂ re-estimated, ≥ 7/8 signs):
  - P(fires | Δ = 0.005) = 0.205, against 0.139 under the posted approximation;
  - the 80% detectable effect is 0.0087;
  - P(fires | Δ = 0.0142) = 0.999.
- **EQ:** pre-registered at n = 29 and capped at 27 before any run (power 0.78 at Δ = +0.0024). It is projected INCOMPLETE at about 15 seeds per arm, which gives an expected 90% half-width of about 0.0024 instead of 0.0018. No EQ number has been computed.

## CW-02 / QA-02: distribution vs downstream explanation

- **TH-02.** Same-shape contrasts identify direction only. A single permutation cannot separate shape from its own direction, which is why CDR uses several permutations at several levels.
- **AN-01 (exploratory).** At eight seeds no boundary contrast clears its bar on either architecture (80 rows).
  - SINet C10 − B is 0.30× and CINV − B is 0.64× (the 3-seed figures were 1.37× and 1.34×).
  - 14 of the 80 unadjusted intervals exclude 0: 12 are CINV − B, 2 are CSHUF − B, and none is C10 − B.
- **CDR, SINet (pre-registered).** The verdict is **not supported.**
  - Against the dispersed reference D = 0.3308 and a bar of 0.0193, the committed shape gives −0.0005 (2/5 permutations) and the twice-concentrated level gives +0.0021 (4/5).
  - All 19 secondary measures, including S_α, are not supported.
  - Descriptively, concentrated minus dispersed units is +0.0024, 95% CI [−0.0024, +0.0072]. The mixed model's level contrasts are all ≈ 0.
- **Limitation found in the design** (a property fixed before any run). Delivered concentration is much weaker than nominal: nominal N_eff 75 / 30 / 15 against induced N_eff 50 / 45 / 41, with random B at 43. The test is of concentration as this pool can deliver it.
- **Pseudo-label counts.** Over all 64 runs the arm means are 1991 / 2007 / 2020 / 2015 (B / C10 / CSHUF / CINV), range 1782–2278.

## CW-03 / QA-03: absolute performance

- **Sources of the reviewer's figures.** Ours is the 3-seed SINet C10 (0.7185 / 0.7690), RISE is its Table 1, and SINet-V2 COD10K is its Table 2. SINet-V2's NC4K value of 0.847 comes from its released maps.
- **One scorer.** 12 of 12 published values reproduce within 0.002.
- **Gap (S_α, SINet-V2, COD10K):**
  - total gap to supervised SINet-V2: 0.120;
  - real labels under our recipe: +0.112;
  - official recipe on top: +0.008;
  - RISE − ours: +0.068 (NC4K +0.056).
- **RISE's detector is SINet-V2**, trained on pseudo masks for the same 4,040 images.
- **Not run:** E3-b (released maps stand in), E3-e (so RISE's mask quality cannot be separated from its recipe), and EXP-04 (the higher operating point).

## CW-04 / QA-04: generator and foreground constraints

- **Reuse.** 1,000 of 1,000 injected renders re-use a base foreground in all 23 arms.
- **Foreground identity dominates the render embedding:** R² 0.856 against 0.499 for random pairing, ICC 0.713.
- **Coverage.** In 52 of 75 clusters the nearest available cut-out is farther from the centre than the median real member. Part of that gap is the difference in representation.
- **Manuscript.** The scope statement, with the posted list and an untested operating point, is in the abstract, the introduction, the Discussion and the conclusion.

## Contradictions with the initial rebuttal or the submission (each corrected in the revision or the final rebuttal)

| # | Statement | Finding | Corrected in |
|---|---|---|---|
| D1 | Manuscript: the rule needs "every seed" to agree | the eight-seed campaign pre-registered and ran ≥ 7/8 | revision §2; rebuttal Part 1 |
| D2 | Rebuttal Part 2: pseudo-label means 1977–2025 | those cover seeds 46–50 only; over all seeds 1991–2020 | revision App. H; rebuttal Part 2 |
| D3 | Rebuttal Part 2: C10−B and CINV−B exceed the boundary bar, 1.37× / 1.34× | 3-seed figures; at 8 seeds 0.30× / 0.64×, within noise | revision §3.2 and Table 7; rebuttal Part 2 |
| D4 | Three sign-count definitions coexist in the code base | new campaigns pre-register the `abc_evaluate` definition | prereg/EQ.md, prereg/CDR.md |
| D5 | Manuscript names "the E-measure" without its variant | it is the mean E-measure | revision App. B |
| D6 | Rebuttal Part 1: P = 0.14 at Δ = 0.005; MDE ≈ 0.008; σ̂ ≈ 0.00345 | 0.205 under the full rule; 0.0087; 0.003431 | rebuttal Part 1 |
| D7 | Rebuttal Part 3: RISE uses "a different representation … and a different training pipeline" | RISE's detector is SINet-V2 on pseudo masks for the same images | revision §1.1, App. A; rebuttal Part 3 |
| D8 (new) | Rebuttal Part 2: the dose-response varies concentration across three levels | true of the quotas; the delivered levels are much closer (N_eff 50 / 45 / 41) | revision §3.2; rebuttal Part 2 |
| D9 (new) | Rebuttal Parts 2–3: SINet-v2 replication; higher operating point | neither was run | revision §3.2, Discussion; rebuttal Parts 2–3 |

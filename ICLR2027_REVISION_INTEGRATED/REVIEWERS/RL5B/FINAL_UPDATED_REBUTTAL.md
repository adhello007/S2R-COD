<!--
FOR THE CORRESPONDING AUTHOR. Not posted. Two OpenReview comments, each pasted exactly as the text between its
BEGIN/END markers. Lengths are measured by tools/count_chars.py (limit 5,000 characters per comment).
Locators were checked against paper/build/REVISED_MARKED.aux by tools/check_locators.py.
Our initial response (8 Nov 2026) is already posted; this is a follow-up, not a replacement.
Long-form evidence: rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/ (FINAL_UPDATED_REBUTTAL.md, EXPERIMENTAL_EVIDENCE.md).
-->

<!-- BEGIN COMMENT 1 -->
## Follow-up to our response, 1/2: results (CW-01, CW-02)

We thank the reviewer again. This follow-up to our posted response reports what we committed to, including what was not run, and says so wherever the new work showed that something we wrote was wrong. In the revised PDF, changes for this review are blue and changes serving two or more reviewers are orange (legend in the general response). Locators refer to the revised PDF.

### CW-01 / Q1: no detected advantage vs. equivalence

We now keep the two apart throughout (abstract, §3.1, conclusion). At eight seeds there is no detected advantage, and the reference effect (+0.0142) is excluded, but smaller ones are not. A separately pre-registered confirmatory campaign then tested equivalence directly: SINet, arms B, C10 and CSHUF, fresh seeds, Welch TOST at ±0.005 $S_\alpha$. It is **incomplete**. Power outages left 16 (B), 15 (C10) and 15 (CSHUF) of 27 planned seeds per arm. Every completed run is analysed as pre-registered; none is dropped.

| Contrast ($S_\alpha$, SINet) | Endpoint | Seeds | $\Delta$ | 90% CI | TOST $p$ | Reading |
|---|---|---|---|---|---|---|
| C10−B, eight-seed (post hoc) | COD10K | 8/8 | +0.0024 | [−0.0012, +0.0059] | 0.101 | neither |
| **C10−B, confirmatory (H1)** | COD10K | 15/16 | **+0.0006** | **[−0.0027, +0.0039]** | **0.015** | **equivalent** |
| C10−CSHUF, confirmatory (H1b) | COD10K | 15/15 | −0.0009 | [−0.0051, +0.0034] | 0.056 | neither |
| C10−B, confirmatory | NC4K | 15/16 | +0.0005 | [−0.0013, +0.0022] | <0.001 | equivalent |
| C10−CSHUF, confirmatory | NC4K | 15/15 | −0.0005 | [−0.0026, +0.0015] | <0.001 | equivalent |

→ **Revised Table 3 (§3.1).** All 16 eight-seed contrasts with 95%/90% intervals and TOST: **Table 9 (App. C)**. Campaign design and deviations: **App. C**.

- H1 survives a Holm correction over the four confirmatory tests ($p$ = 0.030), and the 2σ̂ rule finds every confirmatory gap within noise.
- H1b, against the same-shape shuffle (95% CI [−0.0060, +0.0043]), is neither detected nor equivalent at this precision.

**Corrections to our initial response:**
- We stated that a true +0.005 effect would clear the rule's bar with probability ≈ 0.14, and that the 80%-detectable effect is ≈ 0.008. Simulated as the rule actually runs, the correct values are **0.20** and **0.0087** (§3.1).
- We stated σ̂ ≈ 0.00345; the correct value is **0.00343**.
- We stated that n would be "fixed in advance by TOST power analysis". The analysis gave 29 per arm, which we capped at 27 before any run (amendment committed 2026-11-11; App. B); 16/15/15 finished.
- The manuscript's eight-seed sign rule required at least 7 of 8 seeds, not "every seed" as it said (§2, App. B).

**Limits.** Equivalence is shown on SINet only. The SINet-v2 cells rest on eight seeds and do not exclude gains below 0.005 (Table 9). Run-to-run spread in the confirmatory campaign is larger than at eight seeds (σ̂ 0.0064 vs 0.0034). A same-seed re-train showed that training is not reproducible run to run; this is exploratory and reported in App. C.

### CW-02 / Q2: training-set distribution vs. accuracy

The pre-registered dose-response experiment did not support a downstream effect of concentration. We have therefore restricted the concentration claim to the training-set distribution, including the §3.2 heading. The design is SINet, N = 1000, five random directions per level, and 35 new runs; Boundary-IoU on COD10K-test is the primary measure, with a bar of 2σ̂ = 0.0193.

| Level | Δ vs. dispersed | × bar | Permutations agreeing | Δ $S_\alpha$ |
|---|---|---|---|---|
| committed shape (τ = 1.0) | −0.0005 | 0.03 | 2/5 | +0.0004 |
| twice as concentrated (τ = 0.758) | +0.0021 | 0.11 | 4/5 | +0.0015 |

→ **§3.2 (verdict); Table 7 (App. C).** The SINet-v2 replication we promised was **not run** (compute), and we make no cross-architecture claim.

**Correction.** In our initial response we cited the SINet boundary gains of C10−B and CINV−B as 1.37× and 1.34× their bar. Those were three-seed figures. At eight seeds the correct values are **0.30×** (+0.0046 Boundary-IoU) and **0.64×** (+0.0098). Both are within noise, and no contrast on either architecture clears its bar (Table 8, App. C). We have withdrawn every statement resting on the three-seed result.

One exploratory signal remains. CINV−B on SINet has a paired 95% interval of [+0.0039, +0.0157], unadjusted; it does not survive a Holm correction ($p$ = 0.79). CINV has the same concentration as C10, so concentration cannot explain it (§3.2).

**Limits.** The test covers one architecture. The delivered concentration levels are closer together than their quotas: 50, 45 and 41 effective clusters against a nominal 75, 30 and 15.
<!-- END COMMENT 1 -->

---

<!-- BEGIN COMMENT 2 -->
## Follow-up to our response, 2/2: results (CW-03, CW-04, title)

### CW-03 / Q3: absolute performance and protocol-matched baselines

We placed our pipeline beside RISE and supervised SINet-V2, under one scorer and one set of test splits. The released SINet-V2 and RISE prediction maps, re-scored with our code, reproduce all 12 published values within 0.002.

| Method | Supervision on the 4,040 target images | Detector | $S_\alpha$ COD10K / NC4K |
|---|---|---|---|
| Ours, C10 (8 seeds) | none (synthetic renders) | SINet | 0.717 / 0.768 |
| Ours, C10 (8 seeds) | none (synthetic renders) | SINet-V2 | 0.695 / 0.749 |
| RISE (released maps) | pseudo masks | SINet-V2 | 0.763 / 0.805 |
| Our trainer, real masks (3 seeds) | real | SINet | 0.805 / 0.840 |
| Our trainer, real masks (3 seeds) | real | SINet-V2 | 0.807 / 0.839 |
| SINet-V2 (released maps) | real | SINet-V2 | 0.815 / 0.847 |

→ **Table 4 and "Where the absolute gap comes from" (App. A).** RISE is added to §1.1.

- For SINet-V2 on COD10K, real labels under our recipe account for 0.112 of the 0.120 gap to supervised SINet-V2; the official recipe adds 0.008.
- Without labels, RISE gains +0.068 / +0.056 over our SINet-V2 arm by using pseudo masks on the real target images.
- These components overlap and do not add up.

**Correction.** In our initial response we described RISE as using "a different representation" and training pipeline. That was inaccurate. RISE's detector is SINet-V2, trained with its own recipe on pseudo masks for the same 4,040 images we use unlabelled; its DINOv2 features and retrieval only produce those masks.

**Not run:**
- re-training with the official SINet-V2 recipe (the released maps stand in for it);
- our recipe trained on RISE's masks, so we cannot separate RISE's mask quality from its recipe;
- the replication at a higher operating point. Whether the null holds there is open, and §4 (Scope) says so.

### CW-04 / Q4: generator, foreground pool and scope

Every conclusion is now bounded to the tested setting, in the abstract, the introduction, a new Scope paragraph (§4) and the conclusion. That setting is:
- LAKE-RED, run once offline and never shown the score;
- a pool of 4,447 foregrounds with background-only variation;
- k = 75 clusters of frozen self-supervised features;
- SINet and SINet-v2 with two-round S2R-COD self-training;
- N = 1000, with no real labels in any arm.

We tested allocation, not generation, and make no claim about other generators. The foreground constraint is now quantified:

| Quantity | Value |
|---|---|
| injected renders that re-use a base-pool foreground | 1000/1000 in every arm |
| intraclass correlation of embeddings, same foreground on new backgrounds | 0.71 (random pairs 0.00) |
| clusters whose nearest foreground lies farther than the cluster's median real image | 52 of 75 |
| share of endpoint error variance between clusters | about one fifth |

→ **§4 (Scope); App. E (coverage, with its k-dependence).** A generator that creates new foregrounds, a modern detector and a higher operating point remain untested.

### Title

ICLR does not allow title changes during the discussion period, so the title is unchanged in this revision. In our initial response we said we would reword the title now; that is not possible. For the camera-ready version we will retitle to remove the downstream concentration claim. We propose: *"Uncertainty-Guided Allocation of Synthetic Training Data Shows No Detectable Benefit for Camouflaged Object Detection."*

We thank the reviewer for pushing us to separate these claims; the paper is more accurate for it.
<!-- END COMMENT 2 -->

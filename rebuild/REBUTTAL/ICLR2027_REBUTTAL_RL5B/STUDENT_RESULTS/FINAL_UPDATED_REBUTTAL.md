<!--
DRAFT FOR THE AUTHOR. Not posted. Post each "Part" as a separate OpenReview comment, and the summary as a general comment.
Before posting, resolve every bold [AUTHOR …] or [EQ …] marker:
  - (EQ markers resolved 2026-11-17 from the committed analysis.)
  - [AUTHOR: title] in Part 4 and in the summary: the title decision.
Character counts are at the end of this file; re-run the count after the EQ insertion.
-->

## Response to Reviewer RL5B — Part 1/4 (follow-up: results)

We thank the reviewer again. This follow-up reports what we committed to in our initial response, with outcomes as they came out. Where the new work shows that something we wrote was wrong, we say so and give the corrected value. Two planned items were not run, the SINet-v2 replication of the dose-response experiment and the replication at a higher operating point, and the confirmatory campaign finished only part of its pre-registered seeds; we say so where they arise.

### CW-01 / QA-01: Absence of evidence vs. evidence of equivalence

**Response.** The downstream claim now reads, throughout: no detectable advantage; the eight-seed data exclude an advantage the size of the published method's own gain but not smaller ones; and the pre-registered confirmatory campaign establishes equivalence within $\pm0.005$ on the primary comparison. Sentences such as "no score of any quality helped here" are gone from the abstract, introduction, Sec. 3.1 and the conclusion. A new main-text table (Table 3, Sec. 3.1) reports all 16 eight-seed contrasts with $\Delta$, the 95% interval, the 90% interval used by TOST, the TOST $p$-value and one of three labels, *detected*, *equivalent within $\pm0.005$* or *not detected*, each defined in the text.

**Additional validation.**
- We recomputed every interval and TOST statistic from the per-run metrics.
- We simulated the pre-registered rule exactly as it was run.
- We ran a separately pre-registered confirmatory campaign: arms B, C10 and CSHUF on SINet, fresh seeds, Welch TOST at $\pm0.005$ as the primary test.

**Results.**
- The re-derivation reproduces the manuscript: $\Delta(\mathrm{C10}-\mathrm{B}) = +0.0024$, 95% CI $[-0.0020, +0.0067]$, TOST $p = 0.101$.
- Five of the 16 contrasts are equivalent at $\pm0.005$ before correction, and none after a Holm correction. The primary contrast is neither detected nor equivalent.
- *Correction.* In our initial response we stated that a true effect of $0.005$ would clear the rule's bar with probability about $0.14$, and that the rule detects about $0.008$ with 80% probability. Those figures came from a normal approximation with $\hat\sigma$ held fixed. Simulated as run, with each arm's own spread, $\hat\sigma$ re-estimated every time and the sign condition as pre-registered, the probability is **$0.20$** and the 80% detectable effect is **$0.0087$**.
  - The sign condition was "at least seven of eight seeds", not "every seed" as the manuscript said; Sec. 2 is corrected.
  - We also gave $\hat\sigma \approx 0.00345$; the value is $0.00343$.
  - The rule still detects a reference-size effect ($+0.0142$) with probability above $0.99$, and still cannot rule out effects at the margin.

**Confirmatory campaign.** A power analysis for TOST at $\pm0.005$ gave 29 seeds per arm (power 0.80 at a true $\Delta = +0.0024$). Before any run, we reduced this to 27 for compute (power 0.78) and committed the change.

Hardware interruptions left the campaign incomplete: 16 (random), 15 (targeted) and 15 (shuffled) of the 27 pre-registered seeds per arm finished before our compute deadline. As pre-registered, every completed run is analysed and none is dropped.

| Contrast (SINet) | Endpoint | Seeds | $\Delta$ | 90% CI | TOST $p$ | Outcome |
|---|---|---|---|---|---|---|
| targeted − random (primary) | COD10K-test | 15 / 16 | $+0.0006$ | $[-0.0027, +0.0039]$ | $0.015$ | equivalent |
| targeted − shuffled | COD10K-test | 15 / 15 | $-0.0009$ | $[-0.0051, +0.0034]$ | $0.056$ | neither |
| targeted − random | NC4K | 15 / 16 | $+0.0005$ | $[-0.0013, +0.0022]$ | $<0.001$ | equivalent |
| targeted − shuffled | NC4K | 15 / 15 | $-0.0005$ | $[-0.0026, +0.0015]$ | $<0.001$ | equivalent |

- The campaign establishes that targeted and random allocation are equivalent within $\pm0.005$ $S_\alpha$ on the primary cell ($\Delta = +0.0006$, 90% CI $[-0.0027, +0.0039]$). This survives a Holm correction over the four tests ($p = 0.030$).
- The manuscript's $2\hat\sigma$ rule finds the gap within noise ($0.05\times$ its bar).
- Against the shuffled arm on COD10K-test, the campaign neither detects a difference nor establishes equivalence ($\Delta = -0.0009$, 95% CI $[-0.0060, +0.0043]$).
- Run-to-run spread is larger than in the eight-seed campaign ($\hat\sigma$ $0.0064$ against $0.0034$). It tracks how many target images the self-training round pseudo-labels ($r = 0.74$ across runs).

**Interpretation.** On the primary comparison, the claim is now equivalence within $\pm0.005$, not only the absence of a detectable advantage. The confirmatory 90% interval ends at $+0.0039$, below the margin and below the eight-seed upper limit of $+0.0067$. Two qualifications remain: the campaign finished 15–16 of its 27 seeds per arm, and equivalence to the shuffled arm on COD10K-test is not established at this precision.
---

## Response to Reviewer RL5B — Part 2/4 (follow-up: results)

### CW-02 / QA-02: Distributional change vs. downstream explanation

**Response.** The pre-registered dose-response experiment did not support a downstream effect of concentration, so we have restricted the concentration claim to the training-set distribution. Sec. 3.2 (now titled "Concentration, Not Targeting, Shapes the Training Set"), the abstract and the discussion state three tiers:
- *established:* concentration, not direction, makes targeted training sets distinguishable from random ones;
- *established:* direction makes no detectable difference to accuracy;
- *not supported:* concentration as an explanation of accuracy.

**Additional validation.**
1. *Boundary metrics, all eight seeds (exploratory).* We re-scored the 64 eight-seed runs of both architectures with Boundary-IoU and Boundary-F, on both endpoints and at three thresholds, using the manuscript's rule.
2. *Dose-response (pre-registered before any run).* We held the budget at $N = 1000$ and used three concentration levels:
   - cluster-uniform;
   - the committed $\tau = 1.0$ shape;
   - $\tau = 0.758$, which halves the effective number of clusters.

   Each concentrated level was realised by five independent random permutations of the cluster scores, each sharing 440–518 of its 1,000 images with C10 (fewer than C10 shares with its own shuffle), so direction and image identity average out. Each allocation was trained with three seeds and the uniform one with five, giving 35 SINet runs. The primary measure was Boundary-IoU on SINet·COD10K. A level counts as an effect only if its difference from the dispersed reference exceeds $2\hat\sigma$, at least four of five permutations agree in sign, and the between-permutation spread is smaller than the effect.
3. *Not run:* the SINet-v2 replication, for lack of compute.

**Results.**
- *Correction.* In our initial response we cited C10−B and CINV−B exceeding their boundary bar on SINet ($1.37\times$ and $1.34\times$). Those ratios rest on three seeds. At eight seeds they are $0.30\times$ ($+0.0046$ Boundary-IoU) and $0.64\times$ ($+0.0098$), within noise, and no contrast on either architecture clears its bar. CINV−B's unadjusted interval excludes zero, but CINV has the same concentration as C10, whose contrast with B ($0.30\times$) is the smaller one. Table 7 (App. C) now reports the eight-seed numbers.
- *Dose-response* (Boundary-IoU; dispersed reference $0.331$; bar $2\hat\sigma = 0.0193$):

| Level | Difference from dispersed | × bar | Permutations agreeing |
|---|---|---|---|
| committed shape ($\tau = 1.0$) | $-0.0005$ | $0.03$ | 2/5 |
| twice as concentrated ($\tau = 0.758$) | $+0.0021$ | $0.11$ | 4/5 |

  Neither level clears its bar, and no secondary measure does either, $S_\alpha$ included. Descriptively, the ten concentrated allocations exceed the dispersed ones by $+0.0024$ (95% CI $[-0.0024, +0.0072]$).
- *Correction (pseudo-labels).* We gave mean pseudo-label counts of 1977–2025. Those cover only the 40 runs the seed expansion added. Over all 64 runs the arm means are 1991–2020 (individual runs 1782–2278). The appendix is corrected.

**Interpretation.** Concentration explains why targeted training sets look different. It did not detectably change accuracy.

Three limits remain:
- The test ran on one architecture.
- Its interval excludes boundary effects above about $0.007$, not smaller ones.
- The levels delivered to the training set are closer than their quotas. Assigning each selected render to its nearest cluster centre gives effective cluster counts of 50, 45 and 41, against 75, 30 and 15 nominally, because few foregrounds lie close to most clusters (Part 4). The experiment therefore tests concentration as this pool can deliver it; Sec. 3.2 says so.

---

## Response to Reviewer RL5B — Part 3/4 (follow-up: results)

### CW-03 / QA-03: Absolute performance and protocol-matched baselines

**Response.** The values the reviewer quotes trace to:
- our three-seed SINet C10 means ($0.7185$ / $0.7690$);
- RISE's Table 1 ($0.763$ / $0.805$);
- SINet-V2's Table 2 ($0.815$ on COD10K). Its paper reports no NC4K value; $0.847$ matches our re-score of its released NC4K maps.

The revision adds RISE to the related work, and Appendix A now has a protocol table (Table 4) and a paragraph explaining the gap.

*Correction.* In our initial response we described RISE as relying on a different representation and a different training pipeline. That was inaccurate. RISE's detector is SINet-V2, trained with SINet-V2's own procedure. It is trained on pseudo masks that RISE generates for the same 4,040 COD10K and CAMO training images our pipeline uses without masks. Its frozen DINOv2 features and retrieval serve only to make those masks. The gap to RISE is therefore about supervision on the real target images, not about the detector.

**Additional validation** (one scorer, one set of test splits):
- the released SINet-V2 and RISE predictions, re-scored with our code: all 12 published values reproduce within $0.002$ (largest difference $0.0005$);
- SINet and SINet-V2 trained in our codebase on the real masks of the same 4,040 images (three seeds, single round), as a labelled upper reference;
- our reproduced S2R-COD baselines, $0.7172$ and $0.7030$.

**Not run:**
- re-training with the official SINet-V2 recipe (its released maps stand in);
- our recipe trained on RISE's pseudo masks;
- the higher operating point.

**Results** ($S_\alpha$, COD10K-test / NC4K):

| Method | Labels | Detector | $S_\alpha$ |
|---|---|---|---|
| Ours, C10 (8 seeds) | synthetic | SINet | 0.717 / 0.768 |
| Ours, C10 (8 seeds) | synthetic | SINet-V2 | 0.695 / 0.749 |
| RISE (released maps) | pseudo masks on target | SINet-V2 | 0.763 / 0.805 |
| Our trainer, real masks (3 seeds) | real | SINet | 0.805 / 0.840 |
| Our trainer, real masks (3 seeds) | real | SINet-V2 | 0.807 / 0.839 |
| SINet-V2 (released maps) | real | SINet-V2 | 0.815 / 0.847 |

**Interpretation.**
- *Real labels.* For SINet-V2 on COD10K, real labels under our recipe account for $0.112$ of the $0.120$ gap to supervised SINet-V2, and the official recipe adds $0.008$.
- *RISE.* Without labels, RISE recovers more than half of that gap ($+0.068$ / $+0.056$ over our SINet-V2 arm), using pseudo masks on the real target images, a closer source of supervision than synthetic renders. Without training our recipe on RISE's masks, we cannot separate the quality of its masks from its recipe.
- *Overlap.* These differences overlap and do not add up.
- *Operating point.* The higher-operating-point replication was not run, so whether the null is specific to this low operating point remains open. The Discussion now says so.

---

## Response to Reviewer RL5B — Part 4/4 (follow-up: results)

### CW-04 / QA-04: Fixed generator, limited foreground pool, scope of conclusions

**Response.** The revision bounds every conclusion to the tested setting. The scope statement appears in the abstract, the introduction, a new Scope paragraph in the Discussion and the conclusion. It names:
- the LAKE-RED generator, run once offline and never shown the score;
- the 4,447-foreground pool, with background-only variation;
- $k = 75$ clusters of frozen self-supervised features;
- the two SINet architectures, with two-round self-training;
- $N = 1000$;
- the fact that every arm trains without real labels.

It states that we tested allocation, not generation, and makes no claim about other generators. **[AUTHOR: title — state the revised title here, or that the title change is left to the program chairs' policy.]**

**Additional validation.** We quantified the foreground constraint, as committed:
- distinct foregrounds and reuse per arm;
- the share of render-embedding variance explained by foreground identity;
- for each target cluster, the distance to the nearest available foreground.

**Results.**
- *Reuse.* Every injected render re-uses a foreground already in the base pool: 1,000 of 1,000 in every arm, the dose-response allocations included. Every training pool holds the same 4,447 distinct foregrounds in 5,447 images.
- *Foreground identity dominates.* For two renders of the same foreground on different backgrounds, the between-foreground share of embedding variance is $R^2 = 0.86$, against $0.50$ for random pairs; the intraclass correlation is $0.71$, against $0.00$. A render's cosine similarity is $0.73$ to its own base render and $0.06$ to a random one.
- *Coverage.* In 52 of the 75 clusters, the nearest available foreground lies farther from the cluster centre than the cluster's median real image. Part of that gap is the difference between a cut-out on a plain background and a full photograph.
- *Effect on the dose-response experiment.* The same constraint compresses the delivered concentration levels (Part 2).

**Interpretation.** The pool varies backgrounds around a fixed set of foregrounds, and most clusters have no close foreground. That limits what any cluster-level allocation over this pool can change. The between-cluster share of endpoint error (about a fifth) bounds the leverage of cluster-level allocation, oracle included, independently of the generator. Replacing the generator is outside what we could do rigorously in the discussion period; it stays a stated limitation, not a weaker substitute.

---

## Summary of revisions (general comment)

We thank the reviewers and the AC. In response to Reviewer RL5B we recalibrated the claims, separated distributional from downstream conclusions, added protocol-matched baselines and bounded the scope. We ran the planned experiments and report their outcomes as they came out.

- **Equivalence (CW-01).** A new main-text table gives every eight-seed contrast with its 95% and 90% intervals, the TOST $p$-value and a label (detected / equivalent / not detected). The claim is now "no detectable advantage". A separately pre-registered confirmatory campaign, incomplete at 15–16 of 27 seeds per arm, establishes equivalence within $\pm0.005$ on the primary comparison ($\Delta = +0.0006$, 90% CI $[-0.0027, +0.0039]$); against the shuffled arm on COD10K-test, equivalence is not established.
- **Concentration (CW-02).** A pre-registered dose-response experiment found no downstream effect of concentration on accuracy (SINet, 35 runs, five random directions per level). We therefore restrict the concentration claim to the training sets. The planned SINet-v2 replication was not run.
- **Corrections to our initial response.**
  - The rule's sensitivity at $+0.005$ is $0.20$, not $0.14$, and its 80% detectable effect is $0.0087$, not $0.008$.
  - The boundary ratios $1.37\times$/$1.34\times$ were three-seed figures; at eight seeds they are $0.30\times$/$0.64\times$, within noise.
  - The pseudo-label means 1977–2025 covered only part of the runs.
  - RISE's detector is SINet-V2, trained on pseudo masks for the same images, not a different pipeline.
- **Performance gap (CW-03).** Under one scorer, real labels account for most of the gap to supervised SINet-V2: $0.112$ of $0.120$ on COD10K. RISE's advantage comes from pseudo masks on the real target images. The higher-operating-point replication was not run, and the paper says so.
- **Scope (CW-04).** Every conclusion is bounded to allocation over a fixed LAKE-RED pool that re-uses 4,447 foregrounds with new backgrounds, with the constraint quantified. We make no claim about other generators. **[AUTHOR: title.]**

<!-- CHARACTER COUNTS (measured by analysis/count_rebuttal.py, 2026-11-17 11:17; Python len() on each post from its "## " heading to the next "---")
  Response to Reviewer RL5B — Part 1/4 (follow-up: results)       4887 / 5000 OK
  Response to Reviewer RL5B — Part 2/4 (follow-up: results)       3802 / 5000 OK
  Response to Reviewer RL5B — Part 3/4 (follow-up: results)       2919 / 5000 OK
  Response to Reviewer RL5B — Part 4/4 (follow-up: results)       2613 / 5000 OK
  Summary of revisions (general comment)                          2121 / 2500 OK
  unresolved [EQ]/[AUTHOR] markers: 2
-->

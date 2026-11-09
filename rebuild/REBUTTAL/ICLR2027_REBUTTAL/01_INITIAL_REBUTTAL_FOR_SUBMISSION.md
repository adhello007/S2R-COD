## Response to Reviewer RL5B — Part 1/4

We thank the reviewer for a careful evaluation and for criticisms precise enough to act on. We are glad the reviewer found the same-shape controls and the CHAMELEON audit useful. **We agree with the substance of all four weaknesses.** For each one, we state what the submitted manuscript already shows, where our wording went further than the evidence, and what additional analysis or controlled experiment we plan. This response reports **no new results**. Anything we add during the discussion period will be posted separately, whatever the outcome.

#### CW-01 / QA-01: Absence of evidence vs. evidence of equivalence

**Reviewer Concern**

> For the primary comparison C10−B, the reported difference is [$+0.0024$], with a confidence interval of [$[-0.0020, +0.0067]$]. This interval does not establish equivalence within the proposed margin of [$\pm 0.005$]. The results support a lack of reliable evidence for an advantage, not the stronger conclusion that uncertainty guidance has no meaningful effect.

> *QA-01:* Could the primary confidence intervals and equivalence-test results be presented more prominently, with a clear distinction between failure to detect an effect and evidence of equivalence?

**Response**

We agree, and the manuscript's own numbers support the reviewer's reading. On the primary cell (SINet, COD10K-test, eight seeds), $\Delta(\mathrm{C10}-\mathrm{B}) = +0.0024$ and the post-hoc interval is $[-0.0020, +0.0067]$ (Sec. 3.1). The upper limit is above the $+0.005$ margin. Consistently, the equivalence test in Sec. 3.2 is **not** significant for this contrast ($p = 0.101$). The only targeting-versus-random contrast that is equivalent at the margin is on NC4K.

The evidence therefore supports two statements:
- (a) There is no detectable advantage under the pre-registered rule.
- (b) An advantage as large as the reference effect ($+0.0142$) is excluded on the primary cell.

It does **not** exclude advantages between roughly $+0.005$ and $+0.0067$.

The sensitivity of the pre-registered rule points the same way. The rule declares an effect only when $\Delta > 2\hat\sigma = 0.0069$. With $\hat\sigma \approx 0.00345$ and $n = 8$ per arm, the standard error of a difference of means is about $\hat\sigma\sqrt{2/8} \approx 0.0017$. Under a normal approximation:
- A true effect of $0.005$ would clear the bar with probability only about $0.14$.
- The reference effect would clear it almost surely.
- The effect the rule detects with 80% probability is about $0.008$. The sign-agreement condition can only lower these probabilities.

So the rule is suited to detecting reference-size effects. It cannot rule out effects at the margin. Wording such as "no score of any quality helped here" (Sec. 3.1) and the title's "doesn't help" overstate this, and we will correct them.

**Planned revisions and validation**
1. **Wording.** We will revise the abstract, introduction, Sec. 3.1 and the conclusion so the downstream claim reads: no detectable advantage; reference-size effects excluded on the primary cell; smaller effects not excluded. We also plan to revise the title accordingly.
2. **Main-text table (QA-01).** We will add a table reporting, for all 16 eight-seed contrasts, $\Delta$, its 95% interval, the 90% interval used by TOST, the TOST $p$-value, and one of three labels: *not detected*, *equivalent within $\pm0.005$*, or *neither*. The text will define these categories explicitly.
3. **Re-derivation.** We will recompute every interval and TOST statistic from the per-run metrics and report the rule's sensitivity analytically. Welch remains the primary analysis, as in the manuscript; a seed-paired analysis is a sensitivity check.
4. **Confirmatory campaign.** We plan a separately pre-registered confirmatory campaign for the primary contrast (arms B, C10 and CSHUF). It will use fresh seeds, and its sample size will be fixed in advance by a power analysis for TOST at $\pm 0.005$. We will **not** add seeds to the existing campaign, because doing so after seeing its result would be optional stopping. The outcome will be reported whether or not equivalence is established.

---

## Response to Reviewer RL5B — Part 2/4

#### CW-02 / QA-02: Distributional change vs. downstream explanation

**Reviewer Concern**

> The distributional analyses show that concentrated allocation changes the training-set composition, but this does not establish that concentration explains downstream performance changes. The post-hoc boundary-metric results are suggestive but are not consistent across both architectures.

> *QA-02:* What evidence supports the claim that budget concentration explains downstream performance, rather than merely changing the training-set distribution?

**Response**

We agree that these are two different claims, and that the manuscript establishes the first much more firmly than the second. The current evidence is as follows.

- **Distributional (established).** Set separation is reproduced by every rule that preserves concentration, and it collapses only when concentration is removed (Fig. 2a). The real signal adds only $+0.0073$ in Cohen's $d$ over its own shuffle (Sec. 3.2).
- **Downstream, $S_\alpha$.** The three same-shape arms cannot be distinguished (Fig. 2b). This shows that *direction* is not detectably consequential. It does **not** show that *concentration* is.
- **Downstream, boundary metrics.** On SINet, C10−B and CINV−B both exceed their bar ($1.37\times$ and $1.34\times$), while the direction contrasts do not. However, this analysis is post hoc and binarised, and it does not resolve on SINet-v2.

At most, then, the evidence shows that concentrated arms differ from random on one architecture and one post-hoc metric family, irrespective of direction.

Three further limitations strengthen the reviewer's point:
1. **Shared images.** The same-shape arms share roughly half of their injected images (452–511 of 1000 differ between any pair; Appendix B). "Concentrated vs. random" is therefore partly confounded with *which images* are shared.
2. **Single permutation.** CSHUF is one permutation. CSHUF−B therefore mixes the effect of the allocation's shape with the effect of one particular random direction. Identifying a pure shape effect requires averaging over many permutations.
3. **Pseudo-label counts.** The number of pseudo-labelled target images differs by arm (means 1977–2025; Appendix, controls section).

**Planned revisions and validation**
1. **Claim restructuring.** We will separate the claims explicitly in the abstract, Sec. 3.2 (including its heading) and the discussion:
   - *established:* the training-set distribution effect;
   - *established:* no detectable downstream effect of direction;
   - *hypothesis only:* concentration as a downstream explanation, with post-hoc support on one architecture.
2. **Concentration dose-response campaign.** We plan a pre-registered campaign that holds the budget at $N = 1000$ and varies concentration across at least three levels (cluster-uniform; the committed $\tau = 1.0$ shape; a more concentrated $\tau$). Each level will be realised by several independent random permutations of the cluster scores, constrained to low image overlap with C10. This averages out direction and varies image identity.
   - Primary metric: Boundary-IoU on SINet·COD10K, fixed before any run.
   - Secondary metric: $S_\alpha$.
   - Replication: SINet-v2.
   - Decision: we will describe concentration as a downstream explanation only if the outcome changes with concentration consistently across permutations. Otherwise we will restrict the claim to the training-set distribution.
3. **Re-scoring existing runs.** We will re-score all existing eight-seed runs on both architectures with the boundary metrics, with pseudo-label count and image overlap as covariates. This analysis will be labelled exploratory.

---

## Response to Reviewer RL5B — Part 3/4

#### CW-03 / QA-03: Absolute performance and protocol-matched baselines

**Reviewer Concern**

> The reported C10 results achieve approximately [value] ([value]) on COD10K-test and [value] ([value]) on NC4K, below the reported unsupervised RISE results of [value] and [value], respectively, and standard supervised SINet-v2 results of approximately [value] and [value]. These results are not directly comparable because the training protocols differ. And the gap raises questions about the effectiveness of the overall pipeline. Stronger protocol-matched baselines and a clearer explanation of the performance gap are needed.

> *QA-03:* Can the performance gap be explained through protocol-matched comparisons with supervised and unsupervised COD baselines?

**Response**

We agree that the protocols differ and that the gap needs to be explained. The protocols differ in three ways:

- **Our pipeline.** It follows the synthetic-to-real protocol of S2R-COD. The only labelled training data are 4447 synthetic composites rendered by LAKE-RED, whose foregrounds come from a salient-object dataset (HKU-IS). The 4040 real COD10K/CAMO training images are used **without masks**.
- **Supervised SINet-v2.** It is trained on the real masks of those same images.
- **RISE (ICCV 2025).** It uses no annotations, but it relies on a different representation (frozen self-supervised ViT features with dataset-level retrieval) and a different training pipeline.

The gap to supervised SINet-v2 therefore mainly reflects the absence of real labels. The gap to RISE mixes differences in representation and method. Within its own protocol, our base pipeline reproduces the published method it builds on ($0.7030 \rightarrow 0.7172$; Sec. 1.1).

The reviewer's underlying concern is still valid and bears on generality: at a low operating point, there may be little that *any* allocation can improve. The manuscript addresses this only partly. The positive control shows the design detects a $+0.0197$ gap at this operating point (Table 2). But the manuscript reports no protocol-matched external baselines, and it does not discuss RISE, which we will add.

**Planned revisions and validation**
1. **Protocol table.** For each method we will list the labels used, the target images used, the backbone and its pretraining, the generator, and $S_\alpha$, $E_\phi$ and $F_\beta^w$ on COD10K-test and NC4K. All published values will be verified against the original papers.
2. **Protocol-matched evaluation in our codebase and scorer:**
   - SINet and SINet-v2 trained with the real masks of the same 4040 images (a labelled upper reference);
   - released SINet-v2 and RISE predictions or checkpoints, re-scored with our evaluation code, to separate scorer differences from training differences;
   - our source-only and reproduced S2R-COD baselines.
3. **Gap decomposition.** We will decompose the gap into three components: label supervision, representation/backbone, and reproduction differences.
4. **Higher operating point (if compute permits).** We plan a pre-registered replication of C10, B and CSHUF at a higher operating point: the base pool plus a fixed small fraction of real labelled target images. This tests whether the null is specific to the low-performance regime. If it cannot be completed in time, we will say so.

---

## Response to Reviewer RL5B — Part 4/4

#### CW-04 / QA-04: Fixed generator, limited foreground pool, scope of conclusions

**Reviewer Concern**

> The method relies on a fixed generator and a limited foreground pool, with synthetic diversity primarily coming from background changes. Weak clustering structure and limited foreground diversity may constrain the method from the outset. Consequently, the results provide limited evidence about uncertainty-guided synthetic-data generation more generally.

> *QA-04:* Can the conclusions be better bounded to the specific generator, foreground pool, and training setup evaluated?

**Response**

We agree. The manuscript documents these constraints but does not carry them into its headline claims. The existing evidence (Sec. 3.3) is:
- the render set is a bijection onto the base foregrounds, so each injected render re-uses a foreground already in the base pool with a new background;
- none of 8885 traced objects was regenerated;
- synthetic images cover $0.13$–$0.54$ of the real target manifold, against $0.71$–$0.75$ for the generator's own source photographs;
- $k$-means silhouette peaks at $0.16$;
- only about a fifth of the endpoint's structural-error variance lies between clusters.

Appendix A states that the null is bound to LAKE-RED, and the discussion lists the conditions under which the idea could still work.

We read these constraints as part of the result: they explain why this pipeline could not express an allocation effect. But we agree that they limit what the result covers. The experiment tests uncertainty-guided **allocation over a fixed, background-varied render pool**, not uncertainty-guided generation in general. The generator renders its pool once, offline, and never sees the score (Sec. 2). "Targeted synthetic data" in the title therefore overstates the scope.

One part is less tied to the generator: the between-cluster share of error is computed on the target data and endpoint errors, not on the synthetic pool. It therefore bounds the leverage of *any* cluster-level allocation in this setting, including the oracle arm.

**Planned revisions and validation**
1. **Scope statement.** We will add an explicit scope statement to the abstract, introduction, conclusion and title. It will name the LAKE-RED generator, the 4447-foreground pool, background-only variation, $k = 75$ clusters over frozen self-supervised features, the two SINet architectures, two-round self-training, and $N = 1000$.
2. **Quantifying the foreground constraint.** We will report:
   - distinct foregrounds and foreground reuse per arm;
   - the share of render-embedding variance explained by foreground identity versus background;
   - for each target cluster, the distance to the nearest available foreground.
3. **No claims about other generators.** Replacing the generator is beyond what we can do rigorously within the discussion period, so we will list it as a limitation rather than offer a weaker substitute.

**Summary.** We will recalibrate the claims (CW-01, CW-04), separate distributional from downstream conclusions (CW-02), and add protocol-matched baselines (CW-03). We will also run the confirmatory, dose-response and baseline experiments described above and report their results as they are, including unfavourable ones. We thank the reviewer again; these points will make the paper's claims more accurate.

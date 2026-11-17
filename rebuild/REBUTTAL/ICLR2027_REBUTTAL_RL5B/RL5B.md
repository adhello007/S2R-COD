Official Review of Submission39230 by Reviewer RL5B[cite: 1]
Official Review by Reviewer RL5B 20 Oct 2026, 12:21 (modified: 17 Nov 2026, 14:39) Everyone Revisions[cite: 1]
Paper Summary:[cite: 1]
This paper studies whether uncertainty-guided allocation of a fixed synthetic-data budget improves camouflaged object detection (COD). Through controlled comparisons with random, shuffled, reversed, and current-error-guided allocation, the authors find no reliable improvement in the primary metrics. The paper also reports substantial image overlap between CHAMELEON and training data.[cite: 1]

Presentation: 3: Clear and easy to follow.[cite: 1]
Informativeness: 2: I learned something interesting or useful.[cite: 1]
Soundness: 2: I have minor or fixable concerns about the paper’s soundness.[cite: 1]
Critical Strengths:[cite: 1]
* The same-shape shuffled and reversed controls provide a meaningful way to isolate the contribution of uncertainty-guided allocation. The extensive experiments make the negative results more informative than a simple comparison against random sampling.[cite: 1]
* The CHAMELEON overlap audit examines re-encoded and geometrically transformed images, offering potentially useful evidence about benchmark integrity.[cite: 1]

Critical Weaknesses:[cite: 1]
* For the primary comparison C10-B, the reported difference is $+0.0024$, with a $95$ confidence interval of $[-0.0020, +0.0067]$. This interval does not establish equivalence within the proposed margin of ($\delta = 0.005$). The results support a lack of reliable evidence for an advantage, not the stronger conclusion that uncertainty guidance has no meaningful effect.[cite: 1]
* The distributional analyses show that concentrated allocation changes the training-set composition, but this does not establish that concentration explains downstream performance changes. The post-hoc boundary-metric results are suggestive but are not consistent across both architectures.[cite: 1]
* The reported C10 results achieve approximately ($S_\alpha = 0.719$) on COD10K-test and ($0.769$) on NC4K, below the reported unsupervised RISE results of $0.763$ and $0.805$, respectively, and standard supervised SINet-v2 results of approximately $0.815$ and $0.847$. These results are not directly comparable because the training protocols differ. And the gap raises questions about the effectiveness of the overall pipeline. Stronger protocol-matched baselines and a clearer explanation of the performance gap are needed.[cite: 1]
* The method relies on a fixed generator and a limited foreground pool, with synthetic diversity primarily coming from background changes. Weak clustering structure and limited foreground diversity may constrain the method from the outset. Consequently, the results provide limited evidence about uncertainty-guided synthetic-data generation more generally.[cite: 1]

Questions For Authors:[cite: 1]
* Could the primary confidence intervals and equivalence-test results be presented more prominently, with a clear distinction between failure to detect an effect and evidence of equivalence?[cite: 1]
* What evidence supports the claim that budget concentration explains downstream performance, rather than merely changing the training-set distribution?[cite: 1]
* Can the performance gap be explained through protocol-matched comparisons with supervised and unsupervised COD baselines?[cite: 1]
* Can the conclusions be better bounded to the specific generator, foreground pool, and training setup evaluated?[cite: 1]

Flag For Ethics Review: No[cite: 1]
Rating: 2: Weak rejection[cite: 1]
Confidence: 3: I am familiar with this topic and its relevant literature.[cite: 1]

Response to reviewer RL5B
Official Comment by Authors (Sanjay Singh, Akshat Dobhal) 08 Nov 2026, 18:04 Program Chairs, Senior Area Chairs, Area Chairs, Reviewers, Authors
Comment:
We thank the reviewer for a careful, precise evaluation. We agree with the substance of all four weaknesses. No new results are reported here; additional results will be posted whatever their outcome.

CW-01 / QA-01: Non-detection vs. equivalence. We agree. On the primary cell (SINet, COD10K-test, 8 seeds), Δ(C10 − B) = +0.0024, interval [−0.0020, +0.0067] (Sec. 3.1). The upper limit exceeds the ±0.005 margin, and our own TOST for this contrast is not significant (p = 0.101, Sec. 3.2). The data support (a) no detectable advantage and (b) exclusion of the reference-size effect (+0.0142), but not exclusion of effects of about 0.005–0.0067. With σ̂ ≈ 0.00345 and n = 8, the SE of the difference is ≈ 0.0017. Under a normal approximation, a true effect of 0.005 would clear the 2σ̂ = 0.0069 bar with probability ≈ 0.14, and the 80%-detectable effect is ≈ 0.008.

We will:
* reword the title, abstract, Sec. 3.1 and conclusion accordingly;
* add a main-text table giving, for all 16 contrasts, Δ, the 95% and 90% CIs, the TOST p, and a label (not detected / equivalent / neither);
* run a separately pre-registered confirmatory campaign (B, C10, CSHUF; fresh seeds; n fixed in advance by TOST power analysis). We will not add seeds to the existing campaign, which would be optional stopping.

CW-02 / QA-02: Distribution vs. downstream. We agree that the manuscript establishes the distributional claim far more firmly than the downstream one. The same-shape arms are indistinguishable on S_α (Fig. 2b). This shows that direction is not detectably consequential; it does not show that concentration is. The boundary-metric support (SINet: C10-B 1.37×, CINV-B 1.34× bar) is post hoc and absent on SINet-v2. Two further confounds strengthen the reviewer's point:
* the same-shape arms share about half their injected images (App. B);
* CSHUF is a single permutation, so CSHUF-B mixes the shape effect with one random direction.

We will:
* restate the claims as follows: distributional effect established; downstream direction effect not detected; concentration as a downstream cause a hypothesis only;
* run a pre-registered dose-response campaign: N = 1000; three concentration levels (cluster-uniform, τ = 1, a sharper τ); several low-overlap random permutations per level. Boundary-IoU on SINet-COD10K is the primary metric and SINet-v2 the replication. The downstream claim stands only if the effect is consistent across permutations;
* re-score all 8-seed runs with boundary metrics, with pseudo-label count and overlap as covariates (exploratory).

CW-03 / QA-03: Absolute performance. The protocols differ substantially. We follow the synthetic-to-real S2R-COD protocol: the only labels are 4447 LAKE-RED composites with salient-object foregrounds, and the 4040 real COD10K/CAMO training images are used without masks. Supervised SINet-v2 trains on those images' real masks. RISE is annotation-free but uses a different representation (frozen self-supervised ViT features with dataset-level retrieval). Within its protocol, our base pipeline reproduces the method it builds on (0.7030 → 0.7172), and the positive control shows the design detects a +0.0197 gap. The reviewer is right, however, that a low operating point may limit what any allocation can achieve, and that protocol-matched baselines are missing.

We will:
* add RISE to the related work;
* add a protocol table (labels, backbone, data, metrics), with published values verified;
* train supervised SINet/SINet-v2 in our codebase on the same 4040 images as an upper reference;
* re-score released SINet-v2 and RISE predictions with our scorer;
* decompose the gap into label-supervision, representation and reproduction components;
* if compute permits, run a pre-registered replication at a higher operating point (adding a small fixed fraction of real labels).

CW-04 / QA-04: Scope. We agree. Sec. 3.3 documents these constraints:
* each render re-uses a base-pool foreground with a new background;
* synthetic coverage of the target manifold is 0.13–0.54, against 0.71–0.75 for the generator's source photos;
* silhouette is ≤ 0.16;
* only about 1/5 of error variance is between clusters.

The experiment therefore tests uncertainty-guided allocation over a fixed, background-varied render pool, not generation in general; the generator renders once, offline, and never sees the score.

We will:
* add explicit statements to the title, abstract and conclusion (LAKE-RED, the 4447-foreground pool, k = 75 frozen-feature clusters, two SINet architectures, two-round training, N = 1000);
* quantify foreground reuse, the foreground- vs background-driven share of render variance, and the cluster-to-nearest-foreground distances.

We make no claims about other generators. We thank the reviewer again.[cite: 2]
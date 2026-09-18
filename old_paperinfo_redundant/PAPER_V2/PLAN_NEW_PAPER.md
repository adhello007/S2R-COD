# Context

A prior draft of this paper reached **borderline reject** for three reasons: (1) transferable knowledge read as thin — the null was scoped so tightly to CSRDA that nothing generalizable was visible; (2) the paper was titled after its weaker half — the CSRDA-specific null led while the contamination finding sat as an aside; (3) a central mechanism (the generator conditioning bottleneck) was left unmeasured as `[TODO]`.

We are rebuilding the paper from scratch, as if that draft did not exist. This step produces the plan only — **no `.tex` is touched**.

Since the first draft, four experiments were added: **EXP T2** (arms CSHUF "T2A" and CINV "T2B"), **EXP T2C**, and the **A1** conditioning investigation. `FINAL_RESULTS.md` (1,996 lines) and `TIER_SEGREGATION.md` (509 lines) now consolidate all twelve experiments with per-number provenance. The plan below is built from `FINAL_RESULTS.md` first, as instructed.

**Deliverable of this step:** write the content below, verbatim, to `rebuild/PAPER_V2/PAPER_PLAN_NEW.md` (one new file, one directory). Nothing else changes.

**Three findings from reading the sources that change the plan's shape — read these first:**

1. **A1 ran no experiment.** There are **zero `EXP A1` blocks**. `A1_SCOPING.md`: *"No experiment was written and none was run … No number in this document enters `results/REBUILD_LOG.txt`."* §6(ii) therefore **cannot** be a measured pillar. The structural fix for reviewer objection (3) is different and better: A1 becomes a **closed, labelled withdrawal of a candidate cause**, not a `[TODO]`. Detail in §6.5 and in closing answer (b).
2. **The DUTS/Oracle new-foreground arm was never run** (`FINAL_RESULTS.md` §16(d)) — scoped future work only.
3. **The concentration-attribution audit exists and is strong** — C1 §8, `EXP C1` #4 @ `REBUILD_LOG.txt:1201`. It is a T2 pillar.

---

# rebuild/PAPER_V2/PAPER_PLAN_NEW.md

## 0. The framing spine

The paper makes **three tiers of contribution**. Tier labels are load-bearing and appear in the text, in the contributions list, and as a column in Table 2.

| Tier | Definition (from `TIER_SEGREGATION.md` §"tier definitions") | Role in the paper |
|---|---|---|
| **Tier 3** | Independent of the method entirely — would stand unchanged if the method had worked | **Co-headline.** Benchmark contamination + released detector + clean protocol. Influential for the whole COD community. Its own top-level section (§7). |
| **Tier 2** | Concerns the **target data** or the **uncertainty signal**; travels beyond CSRDA | **The intellectual core.** Leads the dissection (§6.1–§6.4) and leads the title. These are transferable lessons, not CSRDA artifacts. |
| **Tier 1** | Specific to CSRDA or LAKE-RED | **The honest mechanism, not the message.** Collected last (§6.5), explicitly scoped down, with the repeated caveat that these do **not** license *"generators-in-the-loop cannot work."* |

**The discipline this enforces.** Every Tier 1 finding in §6.5 is written together with the dismissal a reviewer would legitimately make — `TIER_SEGREGATION.md` §2 supplies that dismissal for each one, and conceding it is what stops a Tier 1 cause being read as a Tier 2 claim.

**The generalization ceiling, stated in the paper in as many words** (`TIER_SEGREGATION.md` §6): *instantiated in CSRDA with LAKE-RED, uncertainty-guided closed-loop generation yields no accuracy gain resolvable at 39–45 % of the reference improvement* — a null bounded by sensitivity, not a demonstration of absence. The paper never reaches "synthetic data does not help" and never reaches "uncertainty-guided closed-loop generation does not help" in general.

### Naming hazard — enforced throughout the draft

`T1/T2/T3` is overloaded four ways in this repository. In the manuscript:
- **Scope tiers** are always spelled **"Tier 1 / Tier 2 / Tier 3"**.
- **`EXP T2`** and **`EXP T2C`** are experiments — always written with the `EXP` prefix on first use, then "the falsification arms" and "the signal-generality check".
- Per-experiment threshold labels `T1…T8` never appear in main text.
- **Two different "A1"s exist**: the conditioning investigation (`A1_SCOPING.md`) and "Addendum A1" in `PREREGISTRATION_T2.md` / `PREREGISTRATION_T2C.md`. The draft writes the first as "the conditioning scoping study" and never as "A1".

---

## 1. Title

**Recommended (primary):**

> **Concentration, Not Targeting: A Pre-Registered Null for Uncertainty-Guided Synthetic Data in Camouflaged Object Detection, and a Benchmark Half of Which Is Training Data**

Why this one. The first clause is the Tier 2 lesson stated *exactly as measured* — C1 shows the separation credited to targeting is reproduced with the signal destroyed (+0.0073 of a *d*, 13/20), and `EXP T2` shows real / destroyed / reversed targeting are indistinguishable on trained accuracy (12/12 WITHIN NOISE). "Concentration, not targeting" is not a slogan; it is the finding. The second clause co-headlines Tier 3 while avoiding the one sentence D2R measured for and refused to write ("contaminated benchmarks inflate reported scores"). "Half of which is training data" is accurate: 41/76 = 53.9 %.

**Alternate A** (contamination named numerically): *Concentration, Not Targeting: A Pre-Registered Null for Uncertainty-Guided Synthetic Data in Camouflaged Object Detection, and 53.9 % Contamination in CHAMELEON.*

**Alternate B** (author's candidate, with an accuracy caveat that must be resolved before use): *When Uncertainty Doesn't Help: A Pre-Registered Study of Closed-Loop Synthetic Generation for Camouflaged Detection.* — **Caveat:** "uncertainty doesn't help" is broader than anything measured. `EXP T2C` measures ρ(1−Sα) reaching **+0.5628** on SINet-v2; `T2C_RESULTS.md` §7 states explicitly *"Not 'no localisation information'. … The claim is ordinal."* What was measured is that the **direction** of the allocation signal makes no resolvable difference **at fixed concentration**. If Alternate B is used, that scope must appear in the abstract's first two sentences.

---

## 2. Page budget — sums to 8.65 of 9

ICLR 2027 limit confirmed from the template: *"strict upper limit of **9 pages** for the main text of the initial submission, with unlimited additional pages for citations"* (`iclr2027/iclr2027_conference.tex:131`). AI-use, ethics and reproducibility statements are **not** page-limited.

| § | Section | Pages | Tier weight |
|---|---|---|---|
| 1 | Introduction | **1.25** | T3 + T2 lead; T1 as scoped mechanism |
| 2 | Related Work | **0.75** | — |
| 3 | The Approach Under Test | **1.25** | T1 (setting) |
| 4 | Experimental Setup and Pre-Registration | **0.60** | — |
| 5 | The Pre-Registered Null | **0.90** | T1 |
| 6 | What Generalizes: A Tiered Dissection | **1.90** | **T2 ×4, then T1** |
| 7 | Benchmark Contamination and a Clean Protocol | **1.50** | **T3 (co-primary)** |
| 8 | Conclusion | **0.50** | — |
| | **Total main text** | **8.65** | 0.35 pp slack |
| | References | unlimited | — |
| | AI use / Ethics / Reproducibility | not counted | — |
| | Appendix | unlimited | — |

**Overflow rule, fixed now:** if the draft exceeds 9 pages, the cuts come in this order — (i) §3 minutiae → Appendix A; (ii) §5's secondary-endpoint discussion → Appendix C; (iii) §6.5's generator-determinism paragraph → Appendix B. **§6.1–§6.4 and §7 are never cut** — they are the two contributions the reviewer objections were about.

---

## 3. Section-by-section plan

Written in the order: **Method → Experiments → Contamination → Related Work → Introduction → Conclusion → Abstract.**

---

### §3 The Approach Under Test — 1.25 pp *(written first)*

**Purpose.** Specify the method completely enough that the null is attributable to something. A negative-results paper carries a burden a positive one does not: the reader must be able to check that the thing that failed was implemented correctly and is the thing the reader has in mind.

**Opening framing sentence (the justification, stated once):** *A negative result is only as informative as the specification of what was tested; we therefore give the loop in full, and state which of its properties are pre-registered, which are inherited from the released implementation, and which we measured rather than assumed.*

**Content bullets.**

1. **Setting.** Source-to-real domain adaptation for camouflaged object detection. Labelled source pool = HKU-IS, **4447** image+GT pairs. Unlabelled target pool = **4040** images, itself a mixture of **3040 COD10K + 1000 CAMO**. Endpoints: COD10K-test (primary), NC4K (secondary). *Tier 2 flag raised here and cashed in §6.1:* the "target distribution" is a two-dataset mixture whose components separate at **0.8648 / 0.8592 / 0.9225**.
2. **CSRDA in two rounds.** Round 1 trains student + EMA teacher; CLS pseudo-labels target images by `edge_loss < u·avg_loss` (u = 0.8, τ = 0.4); round 2 **rebuilds both models from ImageNet weights** and trains on the enlarged pool; the final round's `Tea_epoch_best.pth` is evaluated. Round count is a hardcoded constant (`--iteration 2`), **not** a convergence criterion — stated plainly, because "closed loop" invites the opposite assumption.
3. **The generator is offline, frozen, one-shot.** LAKE-RED renders 4447 (image, inverted-mask) pairs once, at 50 DDIM steps with `--isReplace`. It is never invoked from the training loop. **The only feedback edge carries pseudo-labels, not images.**
4. **The four-stage allocation loop**, given in full:
   - **(i) Clustering.** k-means, k = 75, on L2-normalised DINOv2-L/518 CLS embeddings of the target set, seed 0. Fitted once and **committed, never refit**.
   - **(ii) ES deficiency scoring.** Per target image, with no ground truth:
     ```
     ES(x) = a · || ∇_sobel σ(s(x)) − ∇_sobel σ(t(x)) ||_1  +  b · BCE( σ(s(x)), σ(t(x)) )
     ```
     with student *s*, EMA teacher *t*, **a = 0.9, b = 0.3**, `use_weighted_bce = False`. Per-cluster score `es_j` is the mean over the cluster.
     **⚠ Number hazard H1 — the class default in `Src/utils/tool.py:46` is `a=0.7`; the *configured* value, parsed from the `--task S2C` override and logged, is `a=0.9`.** The draft writes 0.9 and cites the log.
   - **(iii) Softmax allocation.** Temperature-softmax over `es_j` with **T = α·sd(es)** (scale-free, so comparable across embedders and k), α = 1.0. Integer budgets by largest-remainder, ties by ascending cluster index, so Σn_c = B = 1000 exactly and deterministically.
   - **(iv) Greedy foreground selection.** Cosine of every grey-128 **cutout** to every centroid — cutout, not render, *because that is what a real pipeline has at selection time: the foreground exists, the render does not*. Stable argsort; clusters served in order; each takes the next unclaimed row; `n_displaced` records collisions.
5. **The conditions.** A0 (unpadded baseline, 4447 — the paper-comparable row, and an **unclean** control); A2 (5447; +1000 authors' originals of arm B's stems — the exposure-matched clean control); B (5447; +1000 **random** renders, redrawn per seed); C10 = "Ours" (5447; +1000 **ES-targeted** renders at α=1.0). Plus the two falsification arms introduced in §4: CSHUF (ES permuted across clusters — targeting destroyed) and CINV (rank-reversed — targeting reversed).
6. **What is held constant across arms, and verified rather than assumed:** base 4447 bytes asserted against E0's hash manifest (**0** mismatches over all 24 pools); the unfiltered 4040-image target set in both rounds; one trainer invocation; `Tea_epoch_best.pth` of the final round; cuDNN determinism; endpoints and metrics.

**Pushed to Appendix A (minutiae):** dataloader index-pairing semantics and the mixed-extension round-2 pool parity proof; the strong/weak augmentation definitions; EMA momentum λ = 0.996 under S2C; batch sizes, lr, epoch counts; the full α and B sweep grids and the degenerate-end definitions (`max(p) ≥ 0.95`; `TV(p,uniform) < 0.01`); the metric implementations and the non-squared β caution; the A2 mask-provenance confound note (0.00575 white-fraction difference on 1000 of 5447 images) and why it leaves Δ(C−B) unaffected.

**Committed sources.**

| Claim | Source |
|---|---|
| ES equation, a=0.9 b=0.3 c=0.5, `use_weighted_bce=False` | `EXP B1` #1–#3 @ `REBUILD_LOG.txt:767, 845, 927` |
| Softmax `T = α·sd(es)`, largest-remainder, R2-cutout selection, greedy distinct | `rebuild/C1/C1.md` §3 ("Allocation", "Selection") |
| k=75, dinoL518, seed 0, committed and never refit | `FINAL_RESULTS.md` §8 Table 8.2; `EXP B1` #3 @ `:922` |
| Target set = 4040 = 3040 COD10K + 1000 CAMO; components separate 0.8648/0.8592/0.9225 | `FINAL_RESULTS.md` §7 secondary findings; `EXP A3` @ `:2147` (`target_set_composition`) |
| Arm definitions, pool sizes (A0 4447; A2/B/C 5447), seeds {42,43,45} | `FINAL_RESULTS.md` Table 10.4; `EXP ABC` #1 @ `:1252`, #2 @ `:1323` |
| Exactly 2 CSRDA rounds in every run; round 2 rebuilds from ImageNet weights | `FINAL_RESULTS.md` Table 10.4; `ABC_RESULTS.md` §1.2 |
| CLS rule `edge_loss < u·avg_loss`, u=0.8, τ=0.4 | `T2_RESULTS.md` §5.3 (quoted in `FINAL_RESULTS.md` §11) |
| Base bytes vs `e0_manifest.sha256` = 0 mismatched over 24 pools | `FINAL_RESULTS.md` Table 10.4 |
| Generator offline/frozen; 50 DDIM steps; `--isReplace`; `--seed 0` | `FINAL_RESULTS.md` §1 (E0), §5 (D1) |

**Reviewer objection defused.** *"Is the method rigorous and reproducible — and is the thing that failed the thing I think it is?"* The section answers by (a) giving the loop completely, (b) naming which properties were **verified against committed hashes** rather than assumed, and (c) stating up front that the generation loop is not closed in the sense the phrase implies, so no reader credits the method with an adaptivity it does not have.

**Tier tags in-text:** §3 is Tier 1 throughout (it is the instantiation). One Tier 2 flag is planted (the mixture target) and cashed in §6.1.

---

### §4 Experimental Setup and Pre-Registration — 0.60 pp

**Purpose.** Establish the credibility anchor **before** any result is shown. This is the section that converts "they got a null" into "they committed to how they would read a null".

**Content bullets.**

1. **Endpoints, frozen.** Primary: COD10K-test, Sα, from `Tea_epoch_best.pth` of the final round. Secondary: NC4K, Sα — *"reported, never decides."* Also reported: MAE, Fβw, Eφ. **CHAMELEON is not an endpoint** — forward-reference to §7, one sentence, because the reason is a contribution.
2. **Seeds.** {42, 43, 45}, 3 per arm.
3. **The frozen σ-rule, quoted as the paper's decision procedure:**
   ```
   REAL EFFECT     iff Δ >  2σ̂ AND sign consistent 3/3 seeds
   WITHIN NOISE    iff |Δ| ≤ 2σ̂
   REAL REGRESSION iff Δ < −2σ̂ AND sign consistent 3/3 seeds
   INCONCLUSIVE    iff |Δ| > 2σ̂ but sign not 3/3 → report as-is, do NOT add seeds
   ```
   σ̂ = pooled within-arm sd of Sα, df = 8, applied **independently per architecture**; SINet primary, SINet-v2 robustness; *"a disagreement is reported as a disagreement."*
4. **No p-values, by design, at n = 3** — no bootstrap, no multiple-comparison correction. Verdicts are Δ against a 2σ̂ bar with sign-consistency counts. Stated as a design choice, not an omission.
5. **Pre-registration provenance, with commits.** `PREREGISTRATION.md` recorded at commit `065dac6`, the commit carrying the campaign's first log block; `PREREGISTRATION_T2.md` at `617a2e1`, **before the first `EXP T2` training run** (first T2 block is at `8077730`); `PREREGISTRATION_T2C.md` at `6efde9f`, *"before any T2-C code existed."*
6. **Amendments are append-only and dated.** Two exist and both are disclosed with the defect that prompted them — the `< 1e-9` reference tolerance that was **unsatisfiable by any correct computation** (a 6-dp file admits 5e-7), replaced by a *stricter* rule; and T2C's gate G7 marked `NOT APPLICABLE` in scope. `T2_RESULTS.md` declines to let itself off: *"the weakest link in this record: the author of the rule also authored the flaw."* **That sentence goes in the paper**, in the appendix audit trail, cited.

**Committed sources.** `rebuild/ABC/PREREGISTRATION.md` §1–§2 (verbatim rule); `rebuild/ABC/PREREGISTRATION_T2.md` (+ Addendum A1, dated 2026-09-11); `rebuild/T2C/PREREGISTRATION_T2C.md` (+ Addendum A1); `FINAL_RESULTS.md` §16(d) row 1 (no p-values, by design); `T2_RESULTS.md` §5.4, §6.3–§6.4.

**Reviewer objection defused.** *"Did they decide what counts as a result before or after seeing it?"* — answered with commit hashes, not assurances. It also pre-empts *"why no p-values"* before the reviewer forms the question.

---

### §5 The Pre-Registered Null — 0.90 pp

**Purpose.** State the central Tier 1 result once, completely, with both halves of the power sentence, and then get out of the way so §6 can do the generalizable work.

**Content bullets.**

1. **The verdict, and it is one sentence:** Δ(C − B) is **WITHIN NOISE** on both architectures and both endpoints. **Table 1** carries it.
2. **The full arm ordering is monotone and every step of it is inside noise** — A0 < A2 < B ≈ C10 in all four architecture × endpoint cells.
3. **The two architectures disagree on the sign of Δ(C − B)** (+0.005034 on SINet, −0.000399 on SINet-v2). Reported as a disagreement, per the frozen rule, and read as the signature of noise.
4. **The honest power statement — mandatory, both halves in the same sentence.** The measured 2σ̂ on the primary endpoint is **0.017933**, *larger* than the whole MT→Ours reference gap of **0.0142** that this design was declared able to half-resolve. The campaign therefore **resolved coarser than it declared**. `EXP T2` later improves the bar by **3.24×** (σ̂ 0.002767 vs 0.008966) by excluding A0 from the noise pool **as pre-registered** — but even then resolves only **39 % (SINet) / 45 % (SINet-v2)** of the reference gap.
   - **Phrasing that must not be used:** *"T2 reproduces A/B/C's σ̂."* It does not, and was not supposed to. The correct sentence, from `FINAL_RESULTS.md` §13: *T2 reproduces A/B/C's committed metrics exactly (24/24 cells at 6 dp) and, by excluding A0 from the noise pool as pre-registered, obtains a bar 3.24× tighter.* **⚠ Hazard H9.**
5. **A threshold that PASSED and was refused anyway.** `Δ(A0→C10)` on SINet|NC4K = **+0.010892**, sign 3/3, against 2σ̂ = **0.008309** — the frozen rule returns **REAL EFFECT**. It is not reported as one, on two independent grounds each sufficient: NC4K is secondary, and A0 is the confounded, unstable arm. *"It is recorded prominently **because** it is the tempting one."* This paragraph earns more reviewer trust than any other in the paper and costs three lines.
6. **What the null does *not* say**, stated here rather than deferred: not "Stage C does not work"; nothing about the ES signal (arm C differs from arm B by **concentration** — that disclaimer is discharged only by §6.2); and, inherited from D1, it is *"evidence about targeting under an exhausted foreground pool."*

**Committed sources.** `FINAL_RESULTS.md` Tables 10.1, 10.2 and §10 header/limits | `ABC_RESULTS.md` §1.3, §1.4, §3.1, §3.3, §3.5, §5 | `EXP ABC` #3 @ `REBUILD_LOG.txt:1376` | `FINAL_RESULTS.md` Table 11.2 and §13 for the σ̂ phrasing | artifacts `rebuild/ABC/out/abc_metrics.csv`, `abc_sigma.json`, `abc_verdict.json`.

**⚠ Hazard H8 — do not quote ABC block #3's `per_arm_sd_*` provenance annotation.** It reads *"arm B carries selection variance A0 and C do not — pooled sigma_hat is inflated by it"* and is **false and uncorrected in the committed log**; ABC's own measured values refute it (A0's sd is largest by ~an order of magnitude). The **values** are correct; the attached explanation is not. `FINAL_RESULTS.md` §16(b) item 2; `REVISION_TABLE.md` R17.

**Reviewer objection defused.** *"Is the null rigorous, or just underpowered?"* — the paper concedes underpowering in its own voice, quantifies it, and shows the one later campaign that improved the bar and by how much. Conceding this is what makes §6 credible.

**Tier tag:** the whole section is labelled **Tier 1** in-text. One explicit sentence: *on its own this null generalizes to nothing; its reach comes entirely from the Tier 2 causes in §6.*

---

### §6 What Generalizes: A Tiered Dissection — 1.90 pp **← the heart**

**Purpose.** This is the section the "thin transferable knowledge" objection was about. **It is ordered Tier 2 first**, four subsections deep, before any Tier 1 cause appears. Every subsection opens with a bold tier tag and closes with a one-line **"what a researcher outside this setting can take from it."**

**Table 2** (the tiered cause summary) anchors the whole section; the tier column is the load-bearing element.

---

#### §6.1 **[Tier 2]** The target distribution has no cluster structure for any allocation method to use — 0.40 pp

- Best silhouette **0.1600** (dinoL518, k=75), **0.1465** (dinoL224, k=50), **0.0568** (clipL224, k=5). All three below any conventional threshold. **Embedder-robust in the only sense that matters: no embedder rescues it.**
- CLIP's curve falls **monotonically** (k=5: 0.0568 → k=150: 0.0357), so its "peak" is a **grid-edge artifact**, recorded as a `FAIL` of the interior-maximum guard. *"The guard was not relaxed to make this go away."*
- Reinforced independently: an arbitrary preprocessing choice (squash-resize vs aspect-preserve + centre-crop) **reassigns 5.4 %** of cluster memberships — agreement **94.6 %**, mean cosine **0.9308**. This sets a floor: *an effect smaller than ~5 % of cluster membership cannot be attributed to targeting.*
- The target pool is also a **two-dataset mixture** (3040 + 1000) whose halves separate at **0.8648 / 0.8592 / 0.9225** — i.e. the pool separates from *itself* far more strongly than its clusters separate from each other.
- **Scope limit, stated:** three embedding spaces and k-means only; *"no k is strongly supported by the data"*; B1 does not claim the clusters are meaningless, only weakly separated and only moderately reproducible.
- **Take-away line:** *this is upstream of whether any signal works — a cluster-wise budget is being spent over a partition the data does not support, and the same check costs one silhouette sweep for anyone allocating over clusters.*
- **Sources:** `FINAL_RESULTS.md` Table 8.2 | `B1_RESULTS.md` §C3 | `EXP B1` #3 @ `REBUILD_LOG.txt:922` | `E0_RESULTS.md` §1 s3, §2.6 | `EXP A3` @ `:2147` | artifacts `rebuild/B1/out/b1_k_sweep_{dinoL224,dinoL518,clipL224}.csv`.
- **⚠ Hazard H2:** **0.0566** is dinoL518 at k=5 (the `pick_k` defect) and **0.0568** is clipL224 at k=5 (its grid-edge "peak"). Two near-identical numbers for different quantities. The draft uses **0.0568** in main text and mentions 0.0566 only in the Appendix D audit trail.

---

#### §6.2 **[Tier 2]** An uncertainty signal can contribute nothing beyond the concentration of the allocation it induces — 0.55 pp *(the paper's single most transferable lesson)*

Presented as a **pair, geometry first then trained accuracy**, because the transition from predicted to measured is itself the strength.

**(a) In embedding geometry (C1's attribution audit).** The targeted arm separates from a random one at *d* ≈ **1.00–1.23** — an order of magnitude above the prior claim of *d* ≈ 0.10. Then the audit: **every control arm that keeps concentration but discards targeting reproduces it.** Permuting ES across clusters gives **+0.9139 … +1.1403** in the same cells. Paired increments: targeted − shuffled = **+0.0073** (sd 0.0560), ES wins **13/20** — a coin flip; targeted − random-centroid = **−0.0649**, ES wins **4/20**, i.e. *targeting the highest-ES cluster is worse than picking a cluster at random in 16 of 20 cells*; the declared ceiling is a concentration ceiling (**+0.0077**, top-ES wins **10/20**), cross-checked across two scripts in two runs. What the targeted arm actually does: spans roughly **half the effective dimensionality** (rank ratio **0.53–0.64**, **20/20** cells), buys **average proximity, not coverage** (top-1 similarity up to **+0.096**, coverage Δ ≈ 0).

**(b) On trained accuracy (`EXP T2`).** Concentration held **exactly** fixed — CSHUF and CINV reproduce C1's committed allocation cell at exact 5-dp equality on `clusters_funded` **75**, `max_alloc_share` **0.194**, `alloc_entropy_norm` **0.78644**, `tv_from_uniform` **0.49253** (Table 4, appendix) — and only the signal's **direction** varied. Result: **12/12 WITHIN NOISE**; largest gap anywhere **0.005007** (1.82 σ̂), largest on the primary endpoint **0.002656** (0.83 σ̂). *"C1 established this in embedding-distance space; it now holds on trained accuracy."*

**(c) The directional pattern is printed even though it fails the bar.** C10 — the real signal — is the best arm in **none** of the four cells, and is the *worst* on SINet-v2 | COD10K (0.694669, below even B); CINV — maximally **anti**-targeted — has the highest mean in **3 of 4** cells, and Δ₂(C10 − CINV) is negative in all four. The architectures disagree in sign on Δ₁ and Δ₃ — *"the signature of noise rather than of a small real effect"* — and **it does not reach the bar, so that is not the verdict.** Reported because *"suppressing a directional pattern because it failed a threshold would be the same sin as promoting one that passed."*

- **Scope limits, stated:** C1 is embedding geometry only, two DINO spaces — *"'Negligible in this geometry' is supported; 'zero' and 'harmful' are not."* `EXP T2` was measured only inside CSRDA with LAKE-RED; a different loop could exploit the same signal differently. Gaps are attenuated by shared images (**452 / 511 / 454** of 1000 differ between arm pairs), so the effective contrast is roughly half the nominal budget — attenuation that biases **toward** the null, which is the supporting outcome here, and is disclosed for exactly that reason.
- **Take-away line:** *for anyone doing uncertainty-guided data acquisition — in any domain — the control that matters is not random selection but a same-shape allocation with the signal destroyed; without it, concentration is credited to targeting.*
- **Sources:** `FINAL_RESULTS.md` Tables 9.1, 9.2, 9.4, 11.1, 11.2, 11.3, 11.4 and §11 secondary findings §4 | `C1_RESULTS.md` §8.1–§8.4 | `EXP C1` #4 @ `REBUILD_LOG.txt:1201` | `T2_RESULTS.md` §1.1, §1.2, §2.2, §2.3, §4, §5.1–§5.2 | `EXP T2` #1 @ `:2295`, #3 @ `:2452` | artifacts `rebuild/C1/out/c1_attribution.csv`, `c1_ceiling.csv`, `c1_spread.csv`, `c1_coverage.csv`; `rebuild/ABC/out/t2/abc_metrics.csv`, `abc_verdict.json`.

---

#### §6.3 **[Tier 2]** Uncertainty predicts pixel error better than structural error — for every signal class, not just ours — 0.45 pp

- The pre-registered ordering **ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)** passes on **8 of 8** whole-image rows, **7 of them at 10/10** k-means seeds, across **three signals** (ES, predictive entropy, ensemble disagreement in two variants) × **two architectures**. **Table 5** (appendix) carries all eight rows; main text carries the span. So the ordering *"is not a property of ES. It is a property of every uncertainty signal this pipeline can compute."*
- The pixel-over-structure gap ρ(MAE) − ρ(1−Sα) spans **+0.0708 to +0.3330**; the smallest (SINet-v2, ensemble A0) *"only just"* clears the pre-registered ~0.06 resolution floor and carries the largest ratio sd in the table — said in the paper, not hidden.
- **The instrument demonstrably can fail:** the same pre-registered criterion **fails 6 of 8** boundary-aggregation rows, with four going negative (SINet-v2 ES at **−0.5485**) — an outcome *outside* the pre-registered three-way interpretation space, *"reported as it fell."* The mechanism offered is labelled **POST-HOC**: band area alone predicts MAE at **+0.6286** on SINet-v2, and a band **mean** divides the area out. The boundary branch is declared **not reachable from this design** and is **not claimed**.
- **The bound that must travel with the claim:** ρ(1−Sα) reaches **+0.5628** on SINet-v2. *"'Uncertainty in COD carries no localisation information' is false as stated."* The claim is **ordinal and comparative**: pixel error is predicted better than structural error, always; structural error is still predicted, sometimes well.
- **⚠ Hazard H7 — the claim that must NOT be revived.** B1's original framing *"ES optimises the wrong objective"* is **not supported** by the signal Stage C actually uses: on the faithful target-side signal the ratio is **0.5166 / 0.5463**, i.e. *above* the declared 0.5 boundary and on the opposite side. B1 recorded that FAIL as informative — *"my expectation was wrong."* The draft states the ordering, never the binary.
- **Take-away line:** *if the quantity you care about is structural or boundary quality, an uncertainty signal is a systematically better proxy for pixel error than for the thing you want — and this is a property of the signal class and the problem, not of any one signal.*
- **Sources:** `FINAL_RESULTS.md` Tables 12.1, 12.2, 12.3, 8.1 and §12 limits | `T2C_RESULTS.md` §1–§5, §7 | `EXP T2C` @ `REBUILD_LOG.txt:2550` | `B1_RESULTS.md` §D2, §D3 | `EXP B1` #4 @ `:990` | artifacts `rebuild/T2C/out/t2c_table.csv`, `t2c_correlations.json`.
- **⚠ Hazard H3:** `FINAL_RESULTS.md` Table 12.1's caption says *"50 clusters, 3428 target images"*; `t2c_table.csv` records `n_images = 4040` (whole) / `3909` (boundary), while **3428** is B1's `n_target_in_used` for dinoL518 in `b1_faithful_correlation.json`. → `[TODO: verify — reconcile T2C row-n before writing any caption that states n]`.

---

#### §6.4 **[Tier 2]** An allocation signal measured at the endpoint overstates the signal you actually have — 0.20 pp

- Every committed B1 block correlated **endpoint** ES against endpoint error. That is a real result, but it is **not the quantity Stage C allocates by** — *"A C1 built on it would have allocated by a test-set signal the pipeline does not possess."* The cluster CSV that C1 consumes carried no `target_es` column at all.
- Measured faithfully, ρ(MAE) drops by **+0.2100** (dinoL224) and **+0.2470** (dinoL518): from **+0.8695 / +0.8754** down to **+0.6595 / +0.6284**. The two ES signals only moderately agree per cluster — ρ = **0.695 / 0.5732**.
- **Take-away line:** *any allocation scheme validated on a signal computed where labels exist will overstate the usable signal; measure it where the pipeline actually has it, and expect ~0.2 of ρ to disappear.*
- **Why this is in main text at all:** it is a self-caught defect that **overturned the authors' own headline direction**, and it is a methodological caution that costs a reader nothing to apply. Six lines.
- **Sources:** `FINAL_RESULTS.md` Table 8.1 and §8 secondary findings | `B1_RESULTS.md` §D1–§D3 | `EXP B1` #4 @ `REBUILD_LOG.txt:990` | artifact `rebuild/B1/out/b1_faithful_correlation.json`.

---

#### §6.5 **[Tier 1]** Why *this* instantiation could not have shown a gain — 0.30 pp

Opens with the scoping sentence, and the sentence is repeated in §8: **these are properties of CSRDA and LAKE-RED. They explain this failure. They do not license the conclusion that generators-in-the-loop cannot work.** Each cause is given with the reviewer dismissal it must concede.

1. **The optimisation budget is pinned.** `total_step` = **253** (SINet) / **127** (SINet-v2) in **both rounds of every run**, regardless of pool size. Adding 1000 images to a 4447-image pool bought **no additional optimisation** — it changed only the mixture each step samples from. *Concession, in the paper's own voice:* a reviewer may call this a scheduling property of the training script rather than a result about synthetic data, and **that reading is correct**; nothing here measures what happens when the optimisation budget grows with the data.
2. **The foreground pool is exhausted; the background is not.** The render set is a **bijection** onto the 4447 raw foregrounds — **0** renders trace outside the base pool, **0** base foregrounds unrendered, on the authors' pool as well as ours. And the mapping is **literal**: object-interior error **5.603 / 9.633** against background error **70.802 / 70.555**, with **0 of 8885** traced objects showing any sign of regeneration. *This is an identity statement about pixels, not a distributional argument* — which is why it survives the "but is similarity enough?" counter-argument.
   **⚠ Hazard H10 — the phrase "4447 distinct foregrounds" must never be written.** Measured, the raw pool holds **4443 distinct** images in 4447 files. *"there are fewer distinct foregrounds than claimed, so the pool is more exhausted, not less."*
3. **[Tier 1, main text by explicit decision] The generated distribution is narrow, and this is the one piece of evidence that does not depend on statistical power.** Synthetic pools recall the target manifold at **0.4829 / 0.4834 / 0.1277** (authors') and **0.4668 / 0.5421 / 0.1349** (local), against **0.7473 / 0.7097 / 0.7470** for raw HKU-IS — *LAKE-RED's own input pool* — and **0.8874 / 0.8995 / 0.7921** for NC4K, a genuinely different real camouflage set. The publishable form is strictly comparative: **real photographs of the wrong genre cover the target better than the synthetic images generated from those very photographs.** Paired relative loss against the generator's own input: **−35.4 / −31.9 / −82.9 %** (authors'), **−37.5 / −23.6 / −81.9 %** (local), `T1` passing **3/3 in both pools**. Mechanism: effective rank falls **243.3 → 193.2** while precision *rises* **0.6490 → 0.6886** — *"the generator buys a little proximity by discarding a great deal of variety."*
   - **Tier tag is explicit and the reason is given:** this measures LAKE-RED's output, so by the tier definitions it is **Tier 1**; what generalizes is the **design** — a paired within-content coverage delta against the generator's own input pool, with a real-set ladder as reference.
   - **Mandatory guard, attached to the paragraph:** *"A3 is a distributional characterization, not a training-utility bound … writing it as 'the distribution is far, therefore no amount of it can help' would be a non-sequitur."*
4. **A candidate cause we removed rather than kept.** The standing account held that foreground information reaches the regenerated background only through a narrow 48-scalar summary. Source reading of the released generator refutes that as stated: there are **four** routes, of which the 48-scalar summary is one, and the dominant route is the full-resolution foreground latent handed to a UNet that is globally connected by unmasked spatial self-attention. **This is explicitly labelled as resolved by source reading, not by measurement** — there is no experiment and no logged metric. And the withdrawal is bounded: it shows the channel is **not narrow**; it does **not** show the capacity is used, and we decline both the claim that the generator is "not the binding constraint" and the claim that it is steerable.
   - **Reviewer dismissal conceded in-text:** *"this is a reading of one generator's source code, with no experiment, and you withdrew a cause rather than establishing one."* Both halves are true; the value is that a convenient explanation was removed by the authors instead of left standing.
   - **⚠ The single unlogged figure — handling rule.** The `fuse` 1×1 convolution weight-norm comparison (**0.907 vs 0.810**, ratio 1.12) is marked `[NOT IN COMMITTED LOG BLOCK]` in `FINAL_RESULTS.md` §16(c). **Main text states the four-routes finding qualitatively and does not quote 0.907/0.810.** If the number is wanted, it goes in Appendix B with the `[NOT IN COMMITTED LOG BLOCK]` label attached verbatim. `[TODO: author decide — quote or omit]`.

**Deliberately excluded from the whole paper (author decision, recorded):** `rebuild/ABC/POOL_MECHANICS_AUDIT.md` and every number in it (identical gradient-step totals across arms; round-1 per-image exposure 0.9103 vs 0.7432; the 22.5 % gap). Its driver emitted **no `EXP` block**, and admitting it would make it the only unlogged source in the manuscript. The pinned-budget cause is carried by the **logged** `total_step` = 253/127 instead, which makes the same point.

**Sources for §6.5.** `FINAL_RESULTS.md` Table 10.4, Tables 5.1, 7.1, 7.3, §7 secondary findings, §6 (entire A1 entry), §16(c) | `ABC_RESULTS.md` §1.2 | `EXP ABC` #2 @ `REBUILD_LOG.txt:1323` | `D1_RESULTS.md` §1, §2, §3.1–§3.3 | `EXP D1` @ `:696` | `A3_RESULTS.md` §1.2, §3, §6 | `EXP A3` @ `:2147` | `A1_SCOPING.md` §0, §6(a), outcome box (**no log block**) | artifacts `rebuild/A3/out/a3_coverage.csv`, `rebuild/D1/out/d1_bijection.json`, `d1_trace_auth.csv`, `d1_trace_local.csv`.

**Reviewer objections §6 defuses.** *"What generalizes?"* — four Tier 2 subsections before any Tier 1 cause, each closing with an explicit transfer statement. *"Are the claims supported?"* — every claim carries its own scope limit in the same paragraph, and the two most quotable framings available (ES targets the wrong objective; the distribution is too far to help) are **named and refused**. *"Isn't this just your setup?"* — §6.5 concedes exactly that for exactly the Tier 1 causes, which is what protects §6.1–§6.4 from the same charge.

---

### §7 Benchmark Contamination and a Clean Protocol — 1.50 pp **← co-primary, its own top-level section**

**Purpose.** A contribution that stands **regardless of whether the method worked**, positioned so that a reader who disagrees with everything else still leaves with something usable. Not an appendix. Not a subsection. Placed **after** the dissection and **before** the conclusion, at full section weight, and co-headlined in title, abstract and intro.

**Content bullets.**

1. **The finding.** **41 of CHAMELEON's 76 images (53.9 %)** are the same photographs as images in the COD10K-train / CAMO training pool, re-encoded. By nearest partner, **40 are in the public COD10K-train split** and 1 is in CAMO. Any model trained on COD10K-train has already seen **over half** of CHAMELEON.
2. **It is a fact about two public benchmarks, not about one repository.** The author-sourced CHAMELEON release is **byte-identical** to the on-disk copy (**76/76** at both hash levels) and every figure reproduces — so the finding does not depend on which copy was audited. Sharpened claim: **CHAMELEON ∩ COD10K-train = 40/76.** Provenance direction (CHAMELEON 2015 predates COD10K 2020) is labelled **inference from release chronology**; only pool membership is measured.
3. **The exact-hashing trap — the methodological half, and it generalizes.** Exact hashing returns **0** collisions for CHAMELEON ∩ training and is *correct at that level*: *"The number was right; the inference from it was not."* Demonstrated **twice**: on the original work, and on our own first implementation, which reported **10/76 (13.2 %)** — *"roughly a quarter of the true count"* — because contrast normalisation destroyed the discriminative scale. *"The first number was wrong and it was mine."*
4. **41 is a property of the data, not of the cutoff — two independent instruments agree on the integer.** Tolerance sweep saturates: **11 / 26 / 37 / 40 / 41** at mean|diff| ≤ 1 / 2 / 3 / 5 / 6. Independently, the sorted nearest-neighbour distances show **41 below 5.51, next at 40.58** — a **7.36×** jump immediately after the 41st image — and that gap is **identical at shortlist depth 8 / 32 / and every same-dimension candidate**. *"This was the result most able to overturn the finding, and it held."* The other three endpoints show **no discontinuity at all**; a continuous distribution is what a clean set looks like.
   **⚠ Hazard H5:** the jump is quoted as **7.4×** in D2 and **7.36×** in D2R/`CLEAN_PROTOCOL.md`. The draft uses **7.36×** everywhere.
5. **The negative control.** The **same detector, imported rather than re-implemented**, returns a clean null on NC4K vs COD10K-test: **0** byte, **0** pixel, **0/4121** re-encoded, no gap, minimum nearest distance **20.610** = **3.44×** the confirmation tolerance, **0/4121 at every tolerance swept**. This is what shows the instrument can return "clean". Without it, the CHAMELEON number is one measurement; with it, it is a measurement from a calibrated instrument.
   **⚠ Hazard H4 — three axes that must not be collapsed:** NC4K is **1/4121** against the **full Target training pool** (D2), **0/4121** against **COD10K-train** and **0/4121** against **COD10K-test** (D2_NC4K). Different comparisons, all correct.
6. **The author-sourced re-audit, and a threshold left failing.** Four checks D2 never ran were added; **8 of 8** of D2's measurements reproduce. Three MISMATCHes are **corrections to our own prior work**, not to the data. One declared threshold is **left FAILING**: D2 compared JPEG quantization tables with `!=`, scoring a *missing* table as a differing one — *"absence of evidence read as evidence"* — because two files are **PNGs carrying a `.jpg` extension**. Corrected result: **41/41 pairs carry independent re-encoding evidence**, 40 by quantization table and 1 by container format. *"Relaxing the wording after seeing the data would defeat the point of declaring it beforehand."*
7. **The sentence we wanted to write and could not.** *"What we expected to report: 'by how much the column misleads' … Measured: nothing."* All eight difficulty percentiles land in **0.448–0.559**, and `split_direction_agrees_across_mask_sets` = **False** — the sign of the score difference **flips with the mask release**. Therefore: **we claim non-independence, not inflation.** The honest claim is *"CHAMELEON is not an independent endpoint for COD10K-trained models"* — **not** *"CHAMELEON scores are inflated."* The pre-declared [0.25, 0.75] reading is what stopped us writing the quotable sentence, and **a protocol violation does not need a score advantage to be disqualifying.**
8. **A second, entirely independent reason a CHAMELEON column is not comparable across papers.** The two circulating mask releases are **different annotations**: opposite polarity, mean IoU **0.0** as stored, **0.6932** after polarity alignment, only **27/76** exactly identical and **40/76** at IoU ≥ 0.9. On *identical predictions* the choice of release moves MAE by **2.7×** (0.2196 vs 0.0816). This has nothing to do with contamination **or** with our method.
9. **Every rate is a lower bound, and the unchecked share is printed.** Coverage is exact duplicates plus same-dimension re-encodes. Rescaled copies, crops, flips, colour shifts and different photographs of one specimen are **not** detected and **not** claimed. **25 of CHAMELEON's 76** have no same-dimension training candidate and are therefore **unchecked, not clean**; so are **3039/4121 (73.7 %)** of NC4K against COD10K-test. **"Unchecked is not clean"** is a standing label on Table 3.
10. **A correction to our own work, stated plainly.** CHAMELEON was **never a sanctioned endpoint** in this repository — its README names it once, as a CNC *source* bundle, and there are **0** CHAMELEON predictions under `Result/`. *"the framing is **not** 'we found a bug in their evaluation' … it was **our own** rebuild plan that promoted it to a secondary endpoint without checking."* [Tier 1 housekeeping; included because it bounds the claim, and the Tier 3 findings do not depend on it.]
11. **The clean protocol and the released artifact.** Table 3 is the protocol table. The detector is released and **checkable by strangers**: it passes an **8-assertion synthetic known-answer self-test with no repository data**, reproduces the canonical **41/41** pairs and **41/41** names, found **1** extra pair (the second partner of the image that has two), and the release bundle passes a **12-pattern anonymisation scan with 0 hits**. Recommendation: report COD10K-test and NC4K with the unchecked share disclosed; **do not report CHAMELEON as an independent endpoint** — if reported at all, report it on the named 35-image uncontaminated subset and say which mask release was used.
12. **The re-audit that is owed.** COD10K-test, NC4K and CAMO rates were measured against on-disk copies only. *"The same author-sourced re-audit is owed for them"*; until then, **treat their rates as provisional.** Printed in the protocol table, not buried.

**Committed sources.** `FINAL_RESULTS.md` Tables 2.1, 2.2, 3.1, 3.2, 3.3, 4.1 and §2, §3, §4 in full | `D2_RESULTS.md` §1.4, §2, §3.1–§3.6, §5, §6 | `EXP D2` #5 @ `REBUILD_LOG.txt:600` | `D2R_RESULTS.md` §1.1–§1.10, §2, §3.1–§3.6, §4, §5 | `EXP D2R` #4 @ `:1844` | `EXP D2_NC4K` #2 @ `:2074` | `rebuild/D2_nc4k/README.md` §6 (declared scope; **contains no measured number**) | `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` (protocol table, method, recommendation) | `rebuild/D2_reaudit/release/` (detector, `chameleon_contaminated.json`, README) | artifacts `d2_endpoint_contamination.json`, `d2_endpoint_nearest.csv`, `d2r_reconcile.csv`, `d2r_difficulty.json`, `d2r_mask_reconcile.csv`, `d2nc4k_sweep_test.json`, `d2nc4k_topk_sensitivity.json`.

**Reviewer objection defused.** *"The impactful finding was under-positioned."* — fixed structurally: own section, co-headline in title/abstract/intro, 1.5 pp, a released artifact, and a protocol other people can run. And the second-order objection — *"you found what you went looking for"* — is defused by the NC4K negative control, the shortlist-depth invariance, and the refusal to report an inflation figure.

---

### §2 Related Work — 0.75 pp *(written fourth)*

**Purpose.** Two jobs, and the section fails if either is missing: (a) establish that **the idea was reasonable given prior work** — a negative result about an unreasonable idea is not interesting; (b) establish that **benchmark contamination is a recognized concern**, so §7 lands as a contribution to an existing conversation rather than as an isolated audit.

**⚠ The prior reviewer flagged an empty bibliography as disqualifying. Every citation below is a `[CITE: <topic>]` placeholder. No reference is fabricated at plan stage, and none may be invented at draft stage — each placeholder is resolved by the author against a real, verified reference, or the sentence is cut.**

**Theme 1 — COD and its benchmarks (~0.20 pp).** Task definition and the benchmark suite the field reports on; the architectures used here; the metrics. Ends by naming the four endpoints as *the* standard reporting set — which is what makes §7 consequential.
`[CITE: COD task definition / survey]`, `[CITE: COD10K benchmark]`, `[CITE: CAMO benchmark]`, `[CITE: NC4K benchmark]`, `[CITE: CHAMELEON benchmark]`, `[CITE: SINet]`, `[CITE: SINet-v2]`, `[CITE: SegMaR]`, `[CITE: S-measure]`, `[CITE: E-measure]`, `[CITE: weighted F-measure]`.

**Theme 2 — synthetic data and generators (~0.20 pp).** Generative augmentation for detection and segmentation; the specific S2R-COD / LAKE-RED line this paper tests; and — stated explicitly — **other camouflage generators exist and were not tested here**, so the null is about this instantiation. This sentence is load-bearing for the scope claim.
`[CITE: S2R-COD]`, `[CITE: LAKE-RED]`, `[CITE: latent diffusion]`, `[CITE: DDIM]`, `[CITE: diffusion-generated training data for segmentation]`, `[CITE: copy-paste augmentation]`, `[CITE: other camouflage image generation]`, `[CITE: synthetic-to-real domain adaptation]`.

**Theme 3 — active learning and uncertainty-guided acquisition (~0.20 pp).** The prior that makes the idea reasonable: uncertainty sampling works in many settings, and cluster/diversity-based acquisition is standard. Also the known result that **uncertainty and diversity are confounded in batch acquisition** — which is precisely what §6.2 measures and what makes our shuffle control the right one.
`[CITE: uncertainty sampling / active learning survey]`, `[CITE: core-set / diversity-based acquisition]`, `[CITE: batch active learning, uncertainty-diversity trade-off]`, `[CITE: deep ensembles]`, `[CITE: predictive entropy / MC-dropout]`, `[CITE: mean teacher]`, `[CITE: consistency regularisation / FixMatch]`, `[CITE: pseudo-labelling]`, `[CITE: DINOv2]`, `[CITE: CLIP]`.

**Theme 4 — negative results and benchmark integrity (~0.15 pp).** Train-test contamination and duplicate studies in vision benchmarks; contamination as a recognized concern in the LLM era; pre-registration in ML; and critiques of probe-based / learned distributional distances — which is what makes the AUC-vacuity result a contribution to an existing critique rather than an aside.
`[CITE: train-test contamination in vision benchmarks]`, `[CITE: CIFAR/ImageNet duplicate analysis]`, `[CITE: benchmark contamination in LLM evaluation]`, `[CITE: pre-registration in machine learning]`, `[CITE: negative results / reproducibility in ML]`, `[CITE: critiques of learned-probe distributional distance]`, `[CITE: FID / representation-metric critiques]`.

**Reviewer objection defused.** *"Novelty and placement"* — and specifically the empty-bibliography objection. Theme 3 legitimizes the idea (so the null is informative); Theme 4 legitimizes both the contamination contribution and the pre-registration framing.

---

### §1 Introduction — 1.25 pp *(written fifth)*

**Purpose.** Fixes reviewer objections (1) and (2) at the framing level. By the end of page 1 the reader must know: what generalizes, that contamination is a co-equal contribution, and that the CSRDA-specific null is a scoped mechanism rather than the message.

**Paragraph plan.**

1. **Problem (¶1, ~5 lines).** Camouflaged object detection is label-scarce; generating synthetic training data conditioned on where the model is currently weak is an attractive way to spend a generation budget. Frame it as a *reasonable* idea, with the prior work that makes it reasonable cited here.
2. **The idea, stated fairly and non-defensively (¶2, ~7 lines).** Cluster the unlabelled target set; score each cluster by student–teacher disagreement; allocate a generation budget by temperature-softmax over that score; select foregrounds nearest each funded cluster. State it as its proponents would — **no hedging, no foreshadowing.** A reader who thinks it is a good idea should still think so at the end of this paragraph.
3. **We test it, and it does not hold — with scope in the same breath (¶3, ~6 lines).** 24 pre-registered training runs across 2 architectures × 4 arms × 3 seeds, plus 12 falsification runs. Δ(C−B) is WITHIN NOISE on both architectures and both endpoints. **Scope stated immediately, not deferred:** at a bar resolving 39–45 % of the reference improvement, inside one loop whose optimisation budget is pinned and whose foreground supply is a fixed, exhausted set. *No effect resolvable at this sensitivity — never "no effect".*
4. **The tier framework, introduced explicitly (¶4, ~5 lines).** Name the three tiers and say which contributions sit where. This paragraph is the structural fix for "thin transferable knowledge": it tells the reviewer, on page 1, exactly which findings are claimed to travel and which are not.
5. **Contributions list — ordered Tier 3 / Tier 2 first, Tier 1 last (¶5, ~18 lines).**
   - **C1 [Tier 3].** **41 of CHAMELEON's 76 images (53.9 %) are re-encoded copies of COD10K-train / CAMO training images** — invisible to exact hashing, which returns 0. Verified against an author-sourced release that is byte-identical to the on-disk copy, with a negative control (NC4K, clean at 0/4121) and a released detector that passes a known-answer self-test with no repository data. We claim **non-independence, not inflation**, and say why. *We release the detector and a clean evaluation protocol.*
   - **C2 [Tier 2].** **The target distribution has no cluster structure for any allocation method to use** — best silhouette **0.1600**, and no better in any of three embedding spaces. This is upstream of whether any signal works.
   - **C3 [Tier 2].** **An uncertainty signal can contribute nothing beyond the concentration of the allocation it induces.** Against its own shuffle it adds **+0.0073** of a *d* (13/20, a coin flip) in geometry; with concentration held *exactly* fixed, real, destroyed and reversed targeting are indistinguishable on trained accuracy in **12/12** cells. **A caution for anyone doing uncertainty-guided data acquisition, not only for COD.**
   - **C4 [Tier 2].** **Uncertainty predicts pixel error better than structural error — for every signal class we could compute**, 8/8 rows under a pre-registered criterion across three signals and two architectures. The claim is ordinal; structural error is still predicted, sometimes at ρ ≈ 0.56.
   - **C5 [Tier 1, explicitly scoped].** A dissection of why *this* instantiation could not have shown a gain: the optimisation budget is pinned at 253/127 steps regardless of pool size; the foreground supply is a bijection onto 4447 objects that are copied pixel-for-pixel; the generated distribution is narrower than the real photographs it was generated from. **And one candidate cause we removed rather than kept:** the generator's conditioning channel is not the narrow bottleneck the standing account assumed — resolved by source reading, labelled as such, with no experiment claimed.
   - **C6.** A pre-registered, fully traceable evidence base: every number in this paper is traceable to a committed log block or artifact; failed thresholds are reported failed; two thresholds that *passed* are reported and refused.
6. **Pre-registration as the credibility anchor (¶6, ~4 lines).** Decision rules were committed before the runs, at named commits; amendments are append-only and dated; failed thresholds stay failed; the one quotable sentence the data did not support was pre-declared unreportable and is not reported. *A null is only worth reading if the reader can tell it was not the result of choosing how to look.*

**Sources.** Every number in ¶3 and ¶5 is drawn from §5, §6 and §7 and must match those sections **to the same decimal** — this is a mechanical check in the draft's final pass, listed in §9 below.

**Reviewer objections defused.** (1) thin transferable knowledge — fixed by ¶4 and by C2–C4 preceding C5; (2) titled after its weaker half — fixed by the title and by C1 leading the contributions list.

---

### §8 Conclusion — 0.50 pp *(written sixth)*

**Purpose.** Answer *"so what, and where does this leave the field?"* without softening the null or inflating it.

**Content bullets.**

1. **Restate the null with its tier scope, in one sentence.** Instantiated in CSRDA with LAKE-RED, uncertainty-guided closed-loop generation yields no accuracy gain resolvable at 39–45 % of the reference improvement — a null bounded by sensitivity, not a demonstration of absence.
2. **Restate what travels, and say it is the point of the paper:** a target distribution with no cluster structure to allocate over; an uncertainty signal that adds nothing beyond the concentration it induces; a pixel-over-structure ordering that holds for every uncertainty signal we could compute. **These are claims about the data and the signal, not about our loop.**
3. **What a working system would require** — constructive, and each item tied to the finding that motivates it:
   - **an optimisation budget that scales with the data**, because a pinned step count makes added data a change of mixture rather than of training;
   - **genuinely new foregrounds**, because the render set is a bijection onto a fixed pool and the objects are copied, not generated;
   - **a boundary-aware signal**, because every uncertainty signal tested predicts pixel error better than structural error, and structure is what COD is scored on;
   - **a generator that can be steered**, noting that we showed the conditioning channel is *not narrow* but did **not** show the capacity is used — that remains open.
4. **Scoped future work, named as not-run:** an arm with a genuinely different foreground supply (DUTS / an oracle real-camouflage set) is *"the arm that would test D1's central limit and raise the paper's ceiling"*, and it was deliberately out of this campaign. Also unrun: C2; a boundary-localised uncertainty statistic that controls for band area — *"new work, separately pre-registered."* **These are stated as unrun, never as results.**
5. **Close on the lasting value of the contamination protocol.** The detector and clean protocol are usable today by any COD paper, independent of everything above: report COD10K-test and NC4K with the unchecked share disclosed, do not report CHAMELEON as an independent endpoint, and name the mask release. **A protocol violation does not need a score advantage to be disqualifying.**

**Sources.** `TIER_SEGREGATION.md` §6 (generalization ceiling, quoted) | `FINAL_RESULTS.md` §16(d) (every "not run" item) | `ABC_RESULTS.md` §5 | `T2C_RESULTS.md` §4, §7 | `A1_SCOPING.md` outcome box | `CLEAN_PROTOCOL.md` "Recommendation".

---

### Abstract — ~200 words *(written last)*

**Purpose.** Lead with **both** the null and the contamination; make the Tier 2 content the part a skimming reviewer remembers.

**Sentence plan (≈200 words).**

1. **Context (1 sentence).** Generating synthetic training data where a model is currently weak is an attractive way to spend a budget in label-scarce camouflaged object detection.
2. **Idea, stated fairly (1 sentence).** Cluster the unlabelled target set, score clusters by student–teacher disagreement, allocate generation by softmax over that score.
3. **Pre-registered null (2 sentences).** In **24 pre-registered training runs** (2 architectures × 4 arms × **3 seeds**), targeted allocation does not beat random: Δ(C−B) is within noise on both architectures and both endpoints. State the scope in the same breath — *resolvable at 39–45 % of the reference improvement*.
4. **Tiered dissection, T2 emphasised (3 sentences).** The target distribution has almost no cluster structure to allocate over (**best silhouette 0.16**, in three embedding spaces). **12 further runs** hold concentration exactly fixed and vary only the signal's direction: real, destroyed and reversed targeting are **indistinguishable in 12/12 cells** — the signal adds nothing beyond the concentration it induces. And across three uncertainty signals and two architectures, uncertainty predicts pixel error better than structural error in **8/8** pre-registered tests.
5. **Contamination co-contribution (2 sentences).** Independently, **41 of CHAMELEON's 76 images (53.9 %) are re-encoded copies of COD10K-train data**, invisible to exact hashing. We claim non-independence, not inflation, and release a detector and clean protocol.
6. **Constructive takeaway (1 sentence).** What a working system would need: optimisation that scales with data, genuinely new foregrounds, and a boundary-aware signal.

**Numbers permitted in the abstract, and each must match its section to the same decimal:** 24, 12, 2 architectures, 3 seeds, 39–45 %, 0.16, 12/12, 8/8, 41/76, 53.9 %. **No other numeral appears in the abstract.**

---

## 4. Table specifications

Every caption ends with its source artifact. Every table number is reconciled against its in-text mention in the final pass (§9).

### Table 1 — The pre-registered null *(main text, §5)*

**Structure:** one row per architecture; columns: **σ̂ (df=8) | 2σ̂ | Δ(B−A2) + sign n/3 | Δ(C−B) + sign n/3 | verdict**. Two rows: SINet, SINet-v2. Primary endpoint (COD10K-test, Sα) only.

| | σ̂ (df=8) | 2σ̂ | Δ(B−A2) | **Δ(C−B)** | Verdict |
|---|---|---|---|---|---|
| SINet | 0.008966 | 0.017933 | +0.005768 (3/3) | **+0.005034 (3/3)** | WITHIN NOISE |
| SINet-v2 | 0.006129 | 0.012257 | +0.002967 (3/3) | **−0.000399 (2/3)** | WITHIN NOISE |

**Caption:** states the frozen rule in one clause, notes the two architectures disagree on the sign of Δ(C−B), and cites: *`ABC_RESULTS.md` §1.3; block `EXP ABC` #3 @ `results/REBUILD_LOG.txt:1376`; artifact `rebuild/ABC/out/abc_verdict.json`.*

**Companion Table 1b (same page, 4 rows × 4 cols) — arm means ± per-arm sd:** SINet 0.700950±0.017266 / 0.707679±0.001930 / 0.713447±0.001807 / 0.718481±0.004059; SINet-v2 0.689145±0.010575 / 0.692102±0.003222 / 0.695069±0.004863 / 0.694669±0.002091. Caption notes the ordering A0 < A2 < B ≈ C10 is monotone in all four cells and every step is inside noise. Source: `ABC_RESULTS.md` §1.4, same block; `abc_sigma.json`.

**Decision:** **NC4K columns go to Appendix Table C1, not Table 1.** Reason: FINAL_RESULTS tabulates only the primary endpoint, and NC4K Δ values would have to be read from `abc_verdict.json` directly. Keeping Table 1 to the primary endpoint keeps every main-text number inside a table that FINAL_RESULTS already certifies. The §5 text still reports the NC4K verdicts in prose (all WITHIN NOISE) and the refused `Δ(A0→C10)` = **+0.010892** vs 2σ̂ **0.008309**, both sourced to `ABC_RESULTS.md` §3.5.

### Table 2 — The tiered cause summary *(main text, §6; the tier column is load-bearing)*

**Structure:** one row per cause. Columns: **Cause | Measured quantity (with value) | Experiment | Tier | What it generalizes to**. Ordered Tier 2 first.

| Cause | Measured quantity | Exp | **Tier** | Generalizes to |
|---|---|---|---|---|
| No cluster structure to allocate over | best silhouette **0.1600** (0.1465 / 0.0568 elsewhere) | B1 | **2** | any method allocating over clusters of this target distribution |
| Cluster membership is not a robust label | **5.4 %** of memberships move under a preprocessing change | E0 | **2** | a floor below which no effect is attributable to targeting |
| Signal adds nothing beyond concentration (geometry) | **+0.0073** of a *d* vs its own shuffle, **13/20** | C1 | **2** | any uncertainty-guided acquisition: shuffle is the right control |
| …and nothing on trained accuracy | **12/12 WITHIN NOISE** at a **3.24×** tighter bar | `EXP T2` | **2** | the direction of this signal class carries no resolvable accuracy information |
| Targeting buys proximity, not coverage | effective-rank ratio **0.53–0.64**, **20/20**; coverage Δ ≈ 0 | C1 | **2** | concentration narrows the selected set rather than extending its reach |
| Pixel error is predicted better than structural error | ordering passes **8/8** rows, 3 signals × 2 architectures | `EXP T2C` | **2** | uncertainty-guided allocation for COD in general |
| Endpoint-measured signal overstates itself | ρ drop **+0.2100 / +0.2470** | B1 | **2** | any allocation signal validated where labels exist |
| Optimisation budget is pinned | `total_step` **253 / 127**, both rounds, every run | ABC | **1** | nothing — a property of this loop |
| Foreground pool is exhausted | bijection **4447/4447**, **0** outside, **0** unrendered | D1 | **1 → 2** | the scoping sentence any comparable null must carry |
| Objects are copied, not generated | interior **5.603 / 9.633** vs background **70.802 / 70.555**; **0** of 8885 regenerated | D1 | **1** | the measurement design is reusable on any inpainting generator |
| Generated distribution is narrow | recall **0.13–0.54** vs **0.71–0.90** for every real set | A3 | **1** | the *design* (paired within-content coverage delta) |
| Conditioning channel is **not** the bottleneck | four routes; **source reading, no experiment** | A1 | **1** | nothing — **a withdrawn cause** |

**Caption:** *Tier definitions per §0. Rows sourced individually: `FINAL_RESULTS.md` Tables 8.2, 8.1, 9.2, 9.4, 11.1, 12.1, 5.1, 7.1, 10.4, and §1/§6 secondary findings; blocks `EXP B1` #3 @ `:922` and #4 @ `:990`, `EXP C1` #4 @ `:1201`, `EXP T2` #3 @ `:2452`, `EXP T2C` @ `:2550`, `EXP ABC` #2 @ `:1323`, `EXP D1` @ `:696`, `EXP A3` @ `:2147`; A1 has no log block.*

### Table 3 — Contamination and the clean protocol *(main text, §7)*

**Structure:** one row per benchmark. Columns: **Endpoint | Contaminated vs training | Exact-hash collisions | Unchecked | NN gap | Verification status | Verdict**. Tolerance sweep is a two-line sub-table beneath.

| Endpoint | Contaminated | Exact hash | Unchecked | NN gap | Verification | Verdict |
|---|---|---|---|---|---|---|
| COD10K-test | **2/2026 (0.1 %)** | — | 524/2026 | none | on-disk; not author-verified | reportable, with caveat |
| NC4K | **1/4121** vs pool; **0/4121** vs COD10K-test | — | 2406/4121; 3039/4121 | none, both axes | on-disk; not author-verified | reportable, with caveat |
| **CHAMELEON** | **41/76 (53.9 %)** | **0** | 25/76 | **41 below 5.51, next at 40.58 (7.36×)** | **author-sourced, re-audited** | **not reportable** |
| CAMO | 4/250 (1.6 %) | — | 155/250 | none | on-disk; not author-verified | never an endpoint (selection set) |

**Sub-table — tolerance sweep, CHAMELEON:** mean|diff| ≤ 1 / 2 / 3 / 5 / 6 → **11 / 26 / 37 / 40 / 41** of 76. Plus: gap invariant at shortlist depth 8 / 32 / all; NC4K **0/4121 at every tolerance**, min nearest **20.610** = **3.44×**.

**Caption:** *Every rate is a lower bound; "unchecked" is not "clean". Source: `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` (protocol table); `D2_RESULTS.md` §1.4; `D2R_RESULTS.md` §1.2–§1.3; blocks `EXP D2` #5 @ `:600`, `EXP D2R` #4 @ `:1844`, `EXP D2_NC4K` #2 @ `:2074`.*

### Appendix tables

| # | Content | Source |
|---|---|---|
| **A1** | **Full silhouette sweep, k ∈ {5,10,15,20,30,50,75,100,150} × 3 embedders**, with bootstrap ARI and seed ARI | `rebuild/B1/out/b1_k_sweep_dinoL224.csv`, `b1_k_sweep_dinoL518.csv`, `b1_k_sweep_clipL224.csv`; `EXP B1` #3 @ `:922` |
| **A2** | Per-image ES↔error correlations (n=2026, permutation p=0.0002, bootstrap CI) | `FINAL_RESULTS.md` Table 8.3; `EXP B1` #2 @ `:840` |
| **A3** | Cross-architecture ρ at k=75 over 5 architecture variants, incl. the `S2C_SO` inversion reported-not-excluded | `FINAL_RESULTS.md` Table 8.4; `B1_RESULTS.md` §3, §D4 |
| **B1** | **Per-run metrics, all 36 runs** (24 ABC + 12 T2), Sα/MAE/Fβw/Eφ, both endpoints | `rebuild/ABC/out/abc_metrics.csv`, `rebuild/ABC/out/t2/abc_metrics.csv` |
| **B2** | The falsification arms' design: permutation, ρ(es[σ],es), fixed points, perm seed, `n_displaced` | `FINAL_RESULTS.md` Table 11.4; `EXP T2` #1 @ `:2295` |
| **B3** | The same-shape assertion (5-dp equality on four keys) | `FINAL_RESULTS.md` Table 11.3 |
| **C1** | NC4K secondary-endpoint verdicts, both architectures, all five gaps | `rebuild/ABC/out/abc_verdict.json` |
| **C2** | T2 power table: per-cell σ̂, bar, and the tightening factor vs A/B/C | `FINAL_RESULTS.md` Table 11.2 |
| **D1** | **Full T2C table: 8 whole-image + 8 boundary rows**, ±sd over 10 k-means seeds, incl. the four negative boundary rows and the withdrawn PASS | `rebuild/T2C/out/t2c_table.csv`; `FINAL_RESULTS.md` Tables 12.1–12.3 |
| **E1** | A3 coverage ladder (full, 3 embedders × 6 sets) and AUC ladder (12 rows incl. all JPEG floors) | `rebuild/A3/out/a3_coverage.csv`, `a3_probe_table.csv` |
| **F1** | D1 bijection and per-pool distinctness | `rebuild/D1/out/d1_bijection.json`, `d1_pool_distinctness.csv` |
| **G1** | D2R reconciliation: 8 MATCH / 3 MISMATCH against D2 | `FINAL_RESULTS.md` Table 3.1 |
| **G2** | Mask-release reconciliation (polarity, IoU, MAE 2.7×) | `FINAL_RESULTS.md` Table 3.3 |
| **H1** | **Traceability map** — every main-text number → artifact → log block line | built from `FINAL_RESULTS.md` citations |
| **H2** | **Self-caught errors** (19 rows) and **thresholds that failed and were kept failed** (14 rows), plus the 4 that passed and were refused | `FINAL_RESULTS.md` §14.1, §14.2, §14.3 |
| **H3** | Carried-forward marker ledger: every `UNVERIFIED` / `DEFERRED` / `UNRUN` / `NOT-REPRODUCIBLE` | `FINAL_RESULTS.md` §15 |

---

## 5. Appendix contents list

- **A. Method minutiae** — dataloader semantics, augmentations, EMA momentum, optimiser settings, sweep grids, degenerate-end definitions, metric implementations, the A2 mask-provenance confound. *(Tables A1–A3.)*
- **B. Full experimental record** — all 36 runs, the falsification-arm design, the same-shape assertion, run-integrity gates (6/6), pool provenance (0 byte mismatches over 24 pools), the conditioning source-reading detail with its `[NOT IN COMMITTED LOG BLOCK]` label. *(Tables B1–B3.)*
- **C. Secondary endpoint** — NC4K verdicts, the power table, the refused `Δ(A0→C10)` PASS. *(Tables C1–C2.)*
- **D. Signal-generality detail** — full T2C table including all boundary rows and the withdrawn PASS; the band-area confound (POST-HOC label attached). *(Table D1.)*
- **E. Distributional characterization** — full coverage and AUC ladders; MMD²; effective rank/precision. *(Table E1.)*
- **F. Foreground exhaustion** — bijection, distinctness, mask polarity. *(Table F1.)*
- **G. Contamination detail** — D2R reconciliation, mask-release reconciliation, detector self-test, NC4K deciles, release bundle contents. *(Tables G1–G2.)*
- **H. Audit trail** — traceability map, self-caught errors, failed-and-kept thresholds, marker ledger, and the disclosed doc↔log discrepancies from `FINAL_RESULTS.md` §16(b). *(Tables H1–H3.)*

**Rationale for H existing at all:** a negative-results paper's central asset is that its authors did not choose how to look. Publishing the errors we caught ourselves, the thresholds we left failing, and the two that passed and were refused, is the evidence for that — and it costs no main-text pages.

---

## 6. Required statements *(not page-limited; placed after §8, before references)*

1. **AI use statement — REQUIRED** (`iclr2027_conference.tex:397-412`). Must be honest, human-verified, and follow the template's four-part shape: tasks with required disclosure; tasks not used; not-applicable tasks; tasks with recommended disclosure; plus how AI-assisted work was verified. **Marked `[TODO: author finalize — AI use statement]`** — the author states the actual usage; the plan does not presume it. Note for drafting: this paper's evidence base has an unusually strong answer available (every number is traceable to a committed log block emitted by a committed script; results were not transcribed), and that verification mechanism should be named in the statement.
2. **Ethics statement — recommended.** Content: no human subjects; all datasets are public research benchmarks used under their published terms; **the contamination finding names public datasets, not authors, and the paper explicitly attributes no intent** — the committed source states *"this block reports the overlap and does not attribute intent."* The one correction directed at anyone is directed at ourselves (we promoted CHAMELEON to an endpoint our own repository never sanctioned). `[TODO: author confirm dataset licence statements]`.
3. **Reproducibility statement — recommended.** Points to: the pre-registration files and their commits; the per-experiment result documents; `results/REBUILD_LOG.txt` with block line numbers; the committed `out/*.csv|json` artifacts; the released detector with its known-answer self-test; and Appendix H's traceability map. Must **also** disclose the limits: reproducibility is established *"on this machine with this stack"*, not across hardware or driver versions; and a render is a function of (foreground, mask, **position-in-shard**), so changing shard count changes outputs. `[TODO: author finalize — anonymised code/artifact release URL]`.

---

## 7. Style rules the draft must enforce

1. **Register:** formal, smooth, neutral. **Report, never apologize.** No "unfortunately", no "we had hoped", no defensive hedging. A failed threshold is stated as a measurement.
2. **Tense:** present tense for findings ("the signal contributes +0.0073"); past tense only for procedure ("we committed the rule before the first run").
3. **Main text is idea-level.** No file paths, no function names, no line numbers in main text — those live in the appendix and in captions' source lines.
4. **Template discipline:** use the ICLR template's own commands and `iclr2027_conference.bst`. **Edit only the manuscript `.tex`. Never edit `iclr2027_conference.sty`, `.bst`, `fancyhdr.sty`, `natbib.sty`, or `math_commands.tex`.** Do not uncomment `\iclrfinalcopy` (anonymous submission).
5. **Every factual sentence is sourced or marked.** A sentence carrying a number carries, in its section's source map, the artifact it came from. Anything else is `[TODO: verify — <source>]` or `[CITE: <topic>]`. **Nothing is invented.**
6. **In-text numbers match table numbers to the same decimal.** No rounding drift between §5's prose and Table 1, or between the abstract and §6.
7. **Scope sentences travel with their claims**, in the same paragraph — never relegated to a limitations section at the end.
8. **Banned phrasings** (each corresponds to a claim the committed sources refuse):
   - "contaminated benchmarks inflate reported scores" → use *"not an independent endpoint."*
   - "ES optimises the wrong objective" → use the ordinal comparative statement.
   - "uncertainty carries no localisation information" → false as stated at ρ = 0.5628.
   - "the distribution is far, therefore no amount of it can help" → explicit non-sequitur.
   - "no effect" → *"no effect resolvable at this sensitivity."*
   - "4447 distinct foregrounds" → 4443 distinct, 4447 files.
   - "T2 reproduces A/B/C's σ̂" → use the §13 phrasing.
   - "generators-in-the-loop cannot work" → outside the ceiling.

---

## 8. Number-reconciliation hazards — checked in the final pass

| # | Hazard | Rule |
|---|---|---|
| H1 | ES `a` is **0.9** (configured, logged) not 0.7 (class default) | write 0.9, cite `REBUILD_LOG.txt:767` |
| H2 | **0.0566** = dinoL518@k5; **0.0568** = clipL224@k5 | main text uses 0.0568 only |
| H3 | T2C row-n: caption says 3428, artifact says 4040 / 3909 | `[TODO: verify]` before writing any n in a T2C caption |
| H4 | NC4K: 1/4121 (vs pool) / 0/4121 (vs COD10K-train) / 0/4121 (vs COD10K-test) | three axes, never collapsed |
| H5 | CHAMELEON jump: 7.4× (D2) vs 7.36× (D2R) | use **7.36×** |
| H6 | 41/76 (vs full training pool) vs 40/76 (∩ COD10K-train) | both correct on different axes; state which |
| H7 | B1 ratio 0.4999 (endpoint ES, failed threshold) vs 0.5166/0.5463 (target ES) | never revive "wrong objective" |
| H8 | ABC block #3's `per_arm_sd` annotation is **false** in the committed log | never quote the annotation; values are fine |
| H9 | T2 σ̂ ≠ ABC σ̂ **by design** | use the `FINAL_RESULTS.md` §13 sentence verbatim |
| H10 | "4447 distinct foregrounds" | banned; 4443 distinct in 4447 files |
| H11 | Two different "A1"s | conditioning study vs pre-registration addenda; disambiguate |
| H12 | Tier labels collide with `EXP T2`/`T2C` and threshold labels `T1`–`T8` | spell out "Tier 1/2/3"; prefix experiments with `EXP` |
| H13 | `rebuild/PAPER/` is gitignored and **was not used as a source** for FINAL_RESULTS or TIER_SEGREGATION; any tier map it holds may disagree | do not consult it; the v2 draft derives only from the committed consolidations |
| H14 | `figures/` is **untracked** | any figure used must be committed first, or `[TODO: verify — figure asset provenance]` |

---

## 9. Complete `[TODO]` / `[CITE]` register — the gaps, before drafting

### `[TODO]` — 10 items

| # | Marker | Section | Nature |
|---|---|---|---|
| 1 | `[TODO: author finalize — AI use statement]` | Statements | **Required by ICLR**; author must state actual usage |
| 2 | `[TODO: author confirm — dataset licence / ethics statement scope]` | Statements | author judgement |
| 3 | `[TODO: author finalize — anonymised code + artifact release URL]` | Statements, §7 | needed for the detector release claim |
| 4 | `[TODO: verify — does the published S2R-COD paper report a CHAMELEON column?]` | §7 | `UNVERIFIED`; the PDF is not in this checkout. **The single most quotable gap** — §7's framing of who is affected depends on it |
| 5 | `[TODO: verify — reconcile T2C row n: caption 3428 vs t2c_table.csv 4040/3909]` | §6.3, Table D1 | H3 |
| 6 | `[TODO: verify — author-sourced re-audit owed for COD10K-test, NC4K, CAMO; rates provisional]` | §7, Table 3 | stated in the protocol table as a caveat, not hidden |
| 7 | `[TODO: author decide — quote or omit the fuse-conv weight norms 0.907/0.810]` | §6.5 / App. B | `[NOT IN COMMITTED LOG BLOCK]` |
| 8 | `[TODO: verify — ABC pre-registration timing phrasing]` | §4 | `PREREGISTRATION.md` and ABC block #1 share commit `065dac6`; write "recorded at `065dac6`, the commit carrying the campaign's first log block", not "the preceding commit" |
| 9 | `[TODO: verify — figure asset provenance; `figures/` is untracked]` | figures | H14 |
| 10 | `[TODO: verify — final pass: every in-text number matches its table to the same decimal]` | all | mechanical check, §7 rule 6 |

### `[CITE]` — 36 topics, none fabricated

**COD & benchmarks (11):** COD task definition/survey · COD10K benchmark · CAMO benchmark · NC4K benchmark · CHAMELEON benchmark · SINet · SINet-v2 · SegMaR · S-measure · E-measure · weighted F-measure.

**Synthetic data / generators (8):** S2R-COD · LAKE-RED · latent diffusion · DDIM · diffusion-generated training data for segmentation · copy-paste augmentation · other camouflage image generation (related, **not tested**) · synthetic-to-real domain adaptation.

**Active learning & uncertainty (10):** uncertainty sampling / active-learning survey · core-set / diversity-based acquisition · batch active learning uncertainty–diversity trade-off · deep ensembles · predictive entropy / MC-dropout · mean teacher · consistency regularisation / FixMatch · pseudo-labelling · DINOv2 · CLIP.

**Negative results & benchmark integrity (7):** train-test contamination in vision benchmarks · CIFAR/ImageNet duplicate analysis · benchmark contamination in LLM evaluation · pre-registration in machine learning · negative results / reproducibility in ML · critiques of learned-probe distributional distance · FID / representation-metric critiques.

---

## 10. Closing answers

### (a) Every claim the paper wants to make that is NOT backed by a committed artifact — the honest boundary

| Wanted claim | Status |
|---|---|
| A p-value or confidence interval on **any** arm gap | **Absent by design** — *"n = 3. No p-value, no bootstrap, no multiple-comparison correction."* Verdicts are Δ vs 2σ̂ with sign counts |
| **"CHAMELEON scores are inflated by X"** | **Deliberately unavailable** — measured for, not found (percentiles 0.448–0.559; sign flips with mask release) |
| Whether the **published S2R-COD paper** reports a CHAMELEON column | `UNVERIFIED` — PDF not in checkout. `[TODO #4]` |
| Author-sourced contamination rates for **COD10K-test, NC4K, CAMO** | **Owed** — on-disk copies only; rates provisional |
| **Seed variance** of the ES signal / the allocation signal | `UNVERIFIED-DEFERRED` — one checkpoint pair per architecture |
| **Generator seed variance at the pool level** | Unmeasured — `--seed 0` only; measured at *image* level on **one** foreground (~37–40 grey levels) |
| A **mechanism for A0's instability** | Explicitly **unexplained** — *"a concrete follow-up, not a finding"* |
| A **boundary-localised** uncertainty result | **Not reachable from this design** — needs an area-controlled statistic; new work, separately pre-registered |
| **C2** result of any kind, and `\|Ds\|` | `UNRUN` / `UNVERIFIED` — 0 log blocks |
| `dinoB/224` counterpart to the original *d* = 4.61 | `NOT-REPRODUCIBLE` — no rebuild cache |
| A **DUTS / Oracle new-foreground arm** | **Never run** — deliberately out of the campaign. *This is the arm that would test D1's central limit and raise the paper's ceiling* |
| **What happens when the optimisation budget scales with the data** | Never measured — the largest open question the paper creates |
| That the generator is **steerable** or **not the binding constraint** | Deliberately **not claimed** — source reading shows the channel is not narrow; it does not show the capacity is used |
| Exposure-dilution figures (identical gradient-step totals; 0.9103 vs 0.7432) | Exist in `POOL_MECHANICS_AUDIT.md` but have **no log block** — **excluded by author decision** |

**These are not weaknesses to be hidden. §6.5, §8 and Appendix H state them in the paper's own voice**, because a null whose authors advertise what they could not measure is worth more than one whose authors do not.

### (b) Does the A1 conditioning experiment exist — is §6(ii) a measured pillar?

**No. It must not be written as a measured pillar — and it is not cut either.**

`FINAL_RESULTS.md` §6 and §16(a), and `TIER_SEGREGATION.md` §7(a), are unambiguous: there are **zero `EXP A1` blocks**, and `A1_SCOPING.md` states *"No experiment was written and none was run … No number in this document enters `results/REBUILD_LOG.txt`."* Its single quantitative figure (fuse-conv weight norms 0.907 vs 0.810) is explicitly flagged `[NOT IN COMMITTED LOG BLOCK]`.

**What the plan does instead, and why it fixes the reviewer's objection better than a measurement would have.** The prior reviewer's complaint was that a central mechanism sat unresolved as a `[TODO]`. The plan closes it — as a **labelled withdrawal**: the narrow-conditioning account is *refuted as stated* by source reading (four routes reach the regenerated background; the dominant one bypasses the 48-scalar summary entirely), and the refutation is (i) tagged in-text as source reading rather than measurement, (ii) bounded — we decline both "the generator is not the binding constraint" and "the generator is steerable", and (iii) presented as removing a convenient explanation, which makes the remaining causes carry more of the account. A reviewer sees a closed item with honest epistemics, not an open `[TODO]`. It is Tier 1, it lives in §6.5 item 4, it appears in the contributions list as C5's final clause, and it appears in Table 2 with Tier column "1" and "Generalizes to: **nothing — a withdrawn cause**."

### (c) The single section most at risk of overclaiming, and how the plan constrains it

**§7, Benchmark Contamination.** It is the most quotable material in the paper (53.9 % is a headline number), it is the least dependent on anything else, and `TIER_SEGREGATION.md` §4 flags it as *"the section most at risk of being over-quoted"* while §7 adds that a main-track case built primarily on it *"is a dataset-audit paper rather than a negative-results paper."* The specific overclaim available is one short step away: from *non-independence* to *inflation*.

**Five structural constraints the plan imposes:**
1. **The claim is fixed in advance** — *"CHAMELEON is not an independent endpoint for COD10K-trained models"* — and *"contaminated benchmarks inflate reported scores"* is on the banned-phrasings list (§7 rule 8).
2. **The refusal is written into the section as content, not as a caveat** (bullet 7): we say what we expected to report, that we measured nothing, and that a pre-declared reading is what stopped us.
3. **Every rate carries its unchecked share in the same table cell** — "unchecked is not clean" is a standing label on Table 3, and 25/76 and 73.7 % are printed.
4. **The negative control is in the main table**, so the instrument is visibly capable of returning "clean".
5. **The Tier 1 self-correction is included** (CHAMELEON was never a sanctioned endpoint in this repository, and it was our own plan that promoted it) — which caps the rhetorical reach at "a fact about two public datasets", not "a bug in someone's evaluation".

*Runner-up:* §6.3, where the ordinal finding could drift into "uncertainty carries no localisation information". Constrained by printing **ρ(1−Sα) = +0.5628** in the same paragraph and by the banned-phrasings list.

### (d) Traceability

**No number will be written into the manuscript that is not traceable to a committed artifact** — `rebuild/FINAL_RESULTS.md`, a committed `EXP` block in `results/REBUILD_LOG.txt` cited by line, or a committed file under `rebuild/*/out/` — and any value without one is written as `[TODO: verify — source]` or `[CITE: <topic>]` and never as a number.

---

## Verification plan for this step

1. **Confirm the plan file exists and is complete:** `rebuild/PAPER_V2/PAPER_PLAN_NEW.md` contains §0–§10 above; page budget sums to 8.65 < 9; all three tables and 15 appendix tables are specified with sources; the `[TODO]`/`[CITE]` register lists 10 + 36 items.
2. **Spot-check three sourced numbers end to end** (already done during planning, repeat after writing): `0.017933` → `FINAL_RESULTS.md` Table 10.1 → `EXP ABC` #3 @ `REBUILD_LOG.txt:1376`; `0.1600` → Table 8.2 → `b1_k_sweep_dinoL518.csv` k=75 `silhouette_mean` = 0.1600050979…; `41/76` → Table 2.1 → `EXP D2` #5 @ `:600` and `CLEAN_PROTOCOL.md`.
3. **Confirm nothing else changed:** `git status --porcelain` shows only the new `rebuild/PAPER_V2/` (plus the pre-existing untracked `LAKE-RED/` and `figures/`). **No `.tex` file is touched**, and no file under `iclr2027/` is modified.

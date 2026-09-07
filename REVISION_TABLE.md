# REVISION_TABLE.md — where the rebuilt number differs from the old package

Running record, appended as each experiment completes. Every row cites the log block that produced the
measured value. The "old value" column is the frozen record from `REBUILD_PLAN.md` §4 — a claim under
test, never an input.

Completed so far: **E0, D2, D2R, D1, B1, C1, ABC**. Six outstanding: A1, A2, A3, B2, B3, C3. (C2's load-bearing claim is proved by ABC block #2 at scale; it still has no `EXP C2` block of its own.)

> **D2R RE-VERIFIES D2's HEADLINE AGAINST AN AUTHOR-SOURCED CHAMELEON AND IT HOLDS EXACTLY.** The
> author's release is **byte-identical** to the repo copy (76/76 at both hash levels), and all eight
> D2 CHAMELEON measurements reproduce: 41/76, the same 41 filenames, 323/132/49, the 11/26/37/40/41
> tolerance sweep, and the 7.36× nearest-neighbour gap at exactly 41 — which is also invariant to
> shortlist depth 8/32/all. **The three MISMATCHes below are all corrections to our own prior work,
> not to the data.** Two findings change the claim's shape rather than its size: the contamination is
> `CHAMELEON ∩ COD10K-train = 40/76`, a fact about **public benchmarks** rather than this repo; and
> **no difficulty skew is detectable**, so the reportable claim is that the column is not
> *independent*, never that it is *inflated*.

> **C1 REFUTES THE OLD NUMBER, AND THEN ITS OWN AUDIT REFUTES THE INFERENCE.** The decisive
> measurement was never computed by the old package. Measured, it refutes `d ~ 0.10` by roughly
> an order of magnitude. **But C1's attribution audit (4th block) shows that separation is not
> produced by the ES signal:** permuting the ES values across clusters — destroying the targeting
> while keeping the allocation shape — reproduces the same `d` (+0.91 to +1.14 against a targeted
> +1.00 to +1.23), and spending the whole budget on an **arbitrary** cluster beats spending it on
> the highest-ES cluster in 16 of 20 cells. The `d` measures **concentration**, not **targeting**.
> Net: the old number is wrong; the conclusion it was used to license remains unavailable.
> See C1.1-C1.8 below.

---

## 1. Old values that MOVED

| # | Claim | Old value | Measured | Log block | Why it moved |
|---|---|---|---|---|---|
| D2R.1 | Scope of D2's CHAMELEON contamination | *a fact about this repo's Target pool* | **`CHAMELEON ∩ COD10K-train = 40/76`** — 40 of the 41 nearest partners are public COD10K-train images, 1 is CAMO | `EXP D2R` | Changed in KIND, not size. The partners are public benchmark images, so **any** model trained on COD10K-train has seen them. This is what makes the finding a citable resource rather than a note on one endpoint choice |
| D2R.2 | Impact of the contamination on a CHAMELEON score | *expected to quantify an inflation, mirroring D2's 0.4761 percentile analysis* | **No difficulty skew detectable.** Eight measures put the leaked set at percentile **0.448–0.559** within the clean subset; Mann–Whitney *p* **0.47–0.99**; and the sign of the score gap **flips** between the two mask releases | `EXP D2R` | The data does not support an inflation figure. The reportable claim is that the column is not an *independent* measurement — the compromise is to the evaluation set's identity, not to a measurable score advantage. Mirrors D2's own COD10K null (0.4761) at 20× the rate |
| D2R.3 | CHAMELEON's ground-truth masks | *unmeasured — D2 explicitly disclaimed any mask claim* | The two releases are **different annotations**: opposite stored polarity, mean IoU **0.6932** after alignment, **27/76** identical. On identical predictions the choice moves MAE by **2.7×** (0.2196 vs 0.0816) | `EXP D2R` | A second, independent reason a CHAMELEON column is not comparable across papers, unrelated to contamination. Polarity was declared **per source**, per `REBUILD_PLAN.md` A2 — trap T2 arriving exactly where §2 predicted it |
| D1.1 | Distinct foregrounds in the base pool | **4447** | **4443** unique of 4447 files (raw) | `EXP D1` | The old package wrote a *file count* as a *distinctness* claim. Byte-level hashing finds 4 redundant files. Strengthens the conclusion — the pool is more exhausted, not less |
| E0.1 | Render reproducibility at a fixed seed | *"byte-identity is not expected — cuDNN is nondeterministic"* (my own planned expectation) | **4447/4447 byte-identical**, images and masks | `EXP E0` | The expectation was wrong. Measured bit-exact on this stack. The cluster-agreement threshold I built as a fallback passed at 1.0 trivially |
| E0.2 | Scope of that reproducibility | *unqualified* | holds only at **fixed shard count over a fixed input listing** | `EXP D2` | D2 s7/s8 found a render depends on position-in-shard. E0's headline needed the qualifier and did not have it |
| D2.1 | CHAMELEON ∩ Target | **0** (pixel identity — correct at that level) | **41/76 (53.9 %)** are re-encodes of Target training images | `EXP D2` | Exact hashing cannot see re-encoding. The old method under-bounded the quantity it was reporting. CHAMELEON is withdrawn as an endpoint |
| D2.2 | Cross-named duplicate identity | `COD10K-CAM-3-Flying-**53**-Owl-4633` | `Flying-**65**-Owl-4633` | `EXP D2` | Transcription error in the old documents. No such file exists at `Flying-53`. Immaterial to any number |
| B1.1 | ρ(ES, MAE) per-cluster k=20 test | +0.788 | **+0.8699** ± 0.0297 | `EXP B1` | Moved **up**. Old package had no seed spread; this is 10 k-means seeds |
| B1.2 | ρ(ES, 1−Sα) per-cluster k=20 test | +0.409 | **+0.5067** ± 0.0725 | `EXP B1` | Moved **up** |
| B1.3 | ρ(ES, 1−IoU) per-cluster k=20 test | +0.265 / +0.271 | **+0.4060** ± 0.0884 | `EXP B1` | Moved **up** |
| B1.4 | ρ(ES, MAE) per-cluster k=20 **val** | +0.976 | **DEGENERATE — not reportable** | `EXP B1` | Not a value that moved. Only 1–4 CAMO clusters clear the 15-image floor; Spearman over 2–3 points is ±1 by construction. Confirmed degenerate in **all three** embedder spaces |
| B1.5 | "ES predicts the wrong objective" as a **binary** | asserted as a clean threshold | **not stateable on endpoint ES** — ratio 0.4919–0.6952 across 3 embedders × 2 k, straddling 0.5 | `EXP B1` (3rd block) | k-unstable and embedder-unstable. Retired in favour of the effect size |
| B1.6 | The ES signal B1 correlates | **endpoint** ES (COD10K-test) | **target** ES is what `CLS.py:81-105` computes and what Stage C allocates by — GT-free, on the unlabeled target set | `EXP B1` (4th block) | The cluster CSV C1 consumes had `n_target` as a count and **no `target_es`**. A C1 built on it would have allocated by a test-set signal the pipeline does not have |
| B1.7 | ρ(ES, MAE) per-cluster, as a usable allocation signal | +0.87 (endpoint ES) | **+0.6595** (dinoL224) / **+0.6284** (dinoL518) on the real target-ES signal | `EXP B1` (4th block) | The committed figure **overstated the usable signal by ρ ≈ 0.21–0.25**. The two ES signals only moderately agree per cluster (ρ 0.695 / 0.573) |
| **C1.1** | **Cohen's *d* targeted-vs-random** | **`≈ 0.10`** `[no code, never computed]` | **+1.0028 to +1.2325 at peak**, all four embedder × representation cells | `EXP C1` | **REFUTED, ~10×.** CIs entirely inside the REOPENS band; both embedder spaces agree. The arms are NOT materially identical in embedding space |
| **C1.2** | *d* at the old package's own budget `B = 1000` | `≈ 0.10` | **+0.655 to +1.024** | `EXP C1` | **REFUTED, 7-10×** at the budget the old package itself proposed |
| **C1.3** | "the two arms see nearly identical data, so no gain is possible" | asserted | **not supported as stated** — declared threshold `d ≥ 0.5` → VERDICT REOPENS; the arms overlap at exactly the chance rate (0.94-1.05) and are genuinely different sets | `EXP C1` | This leg fails **as stated**. Per C1.5 it does not convert into support for Stage C: the separation is not attributable to targeting. The other legs (A1 bottleneck, D1 exhaustion, B1 moderate signal, C3 noise floor) are untouched |
| **C1.4** | Held-out Cohen's *d* under a known-zero difference | assumed 0 | **−0.3241** (sd 0.0166) | `EXP C1` | New. The ceiling assertion fired and exposed that the half-split estimator is **negatively biased under the null**, i.e. conservative. Every measured *d* is now read against this reference |
| **C1.5** | **The measured *d* is caused by ES-targeting** | implied by C1.1-C1.3 | **REFUTED.** Paired over 20 cells: targeted − ES-shuffled = **+0.0073** (sd 0.056, ES wins **13/20**, a coin flip); targeted − arbitrary-cluster = **−0.0649** (ES wins **4/20**); targeted − random-direction = **+0.0479** (ES wins 18/20) | `EXP C1` (4th block) | **New, and it overturns the reading of C1.1.** Any concentrated selection reproduces the headline. The ES signal's contribution is **detectable but negligible** — consistently positive only against a random *direction*, at ~5% of the effect |
| **C1.6** | C1's own `d_max_possible` is a **targeting** ceiling | `C1_PLAN.md` §2.4 | **REFUTED.** Whole budget to the highest-`target_es` cluster minus whole budget to an **arbitrary** cluster = **+0.0077**, top-ES wins **10/20** | `EXP C1` (4th block) | Cross-check between two independently produced artifacts (`c1_ceiling.csv` from block 3, `c1_attribution.csv` from block 4). The ceiling is a **concentration** ceiling |
| **C1.7** | Held-out *d* under two independent random draws (the correct null) | never measured | **−0.1328** (range −0.2560 … −0.0109); the **in-sample** estimator on the same data gives **+0.6991**, reaching **+1.4506** | `EXP C1` (4th block) | New. The held-out estimator does not manufacture effects — but the in-sample one **exceeds C1's own headline with no targeting at all**. Had `d_insample` been the headline, REOPENS would have been an artefact. The strongest justification in the rebuild for the held-out choice, and it is a measurement |
| **C1.8** | The targeted and random arms differ only in centre | limitation logged unconditionally | **They differ in shape too, but not usefully:** effective rank ratio **0.53–0.64** (**20/20** cells narrower), mean top-1 similarity to the target manifold up **+0.096**, but target coverage Δ ≈ 0 (−0.021 … +0.012, **less** in 10/20) | `EXP C1` (4th block) | New. Targeting buys **average proximity at the cost of effective dimensionality, and buys no coverage.** §8.6 of `C1_RESULTS.md` states the resulting hypothesis — that this profile is compatible with zero accuracy gain — as a question for **C3**, not a result |
| B1.8 | Direction of the wrong-objective claim | "ES predicts pixel, not structure" | **NOT SUPPORTED on the real signal** — ratio 0.5166 / 0.5463, both ≥ 0.5 in both candidate spaces | `EXP B1` (4th block) | A **reversal of direction**. I declared a threshold expecting the boundary to stay unstateable; it failed because the boundary *is* stateable on target ES and lands on the other side. B1's contribution becomes "the allocation signal is moderately predictive at best", not "it points at the wrong error type" |
| **ABC.1** | **σ(Sα) as the detection bar** | **0.00356** (n=6) / 0.00286 (n=4), both `[no code]` | **0.008966** — pooled within-arm sd of Sα over 4 arms × 3 seeds, df=8, SINet/COD10K | `EXP ABC` #3 | **SUPERSEDED, and 2.5× LARGER.** The archived figures came from `--iteration 1` runs at Sα ≈ 0.699, rescued from a volatile scratchpad by code that was not version-controlled. The consequence is unfavourable: `2σ̂` = **0.017933** exceeds the 0.0142 MT→Ours gap, so **the campaign is underpowered against its own pre-registered power statement** |
| **ABC.2** | Predicted ΔSα from Stage C, and the shortfall vs 2σ | 0.000111 and 64× `[no code]` | Δ(C−B) = **+0.005034** (SINet) / **−0.000399** (SINet-v2) on COD10K | `EXP ABC` #3 | **RE-MEASURED.** Both old figures were wrong and by large factors — σ under-estimated 2.5×, the shortfall over-estimated ~18× — and both errors happened to point at the same conclusion. Getting the right answer from the wrong numbers is not a reproduction |
| **ABC.3** | "Uncertainty-guided closed-loop Stage C improves COD accuracy" | asserted | **WITHIN NOISE** on both architectures and both endpoints. `architectures_agree_on_verdict` = YES on all five gaps | `EXP ABC` #3 | The first time Stage C was **trained**. Per `ABC_PLAN.md` §A.12 item 7 this is a result about **concentration**, not about the ES signal, whose own contribution C1 measured at ~0.6% of *d*. The null must be reported **with** the power statement in ABC.1 |
| **ABC.4** | Arm A0 as a usable baseline | assumed usable, flagged only for the 22% exposure confound | **A0 is the most VARIABLE arm in both architectures** — sd **0.017266** (SINet) and **0.010575** (SINet-v2) on COD10K, against **0.001807** and **0.004863** for arm B | `EXP ABC` #3 | **New, and it sets the detection bar for comparisons A0 is not part of.** A0 contributes 2 of the 8 df in the pooled σ̂. Reproducible across 2 architectures × 2 endpoints, so not one unlucky run. Mechanism **unexplained** |
| **ABC.5** | CLS round-2 append count as an arm-invariant | never examined | mean **1945.8**, range **1732–2163**, **spread 22.2%** — declared 5% threshold **FAILS** | `EXP ABC` #2 | Reported, not absorbed: it is the one legitimate place the arms diverge beyond the Stage C injection, because CLS selects with the arm's own round-1 model (`CLS.py:139`). The one arm-level pattern (render-carrying arms append more) appears on SINet and **not** on SINet-v2, so it is not architecture-robust |

## 2. Corrections to the rebuild's own work

Kept visible because a rebuild that only ever corrects someone else is not auditing itself.

| # | What was wrong | Where | How it was found | Fix |
|---|---|---|---|---|
| R1 | Provenance gate was a grep, and flagged its own `FORBIDDEN` list plus the package's prose — 14 false positives | `EXP E0` blocks 1–2 | The gate FAILED its own threshold | Rewritten as an AST scan; docstrings excluded; pragma exemptions reported, not suppressed; self-tested against injected violations |
| R2 | Four figures in `E0_RESULTS.md` existed only outside the log (s2 sample size, staging cross-check, two ad-hoc directory digests) | `EXP E0` blocks 3→4 | Mechanical traceability check | Promoted into the script; new threshold comparing image and mask digests |
| R3 | D2's near-duplicate scan used contrast-normalised thumbnail bucketing — roughly a quarter of the true recall | `EXP D2` blocks 2→3 | Audit against an exhaustive search | Replaced by exhaustive within-dimension search. CHAMELEON moved 10/76 → 41/76 |
| R4 | `4443` used in `D2_RESULTS.md` as arithmetic rather than a logged metric | `EXP D2` blocks 1→2 | Traceability check | `unique_raw_hkuis` / `unique_authors_pool` added as metrics |
| R5 | D1 scored **both** pools against `raw_gt`, producing an apparent 406-image anomaly in the authors' pool | D1, pre-log | Audit of D1's own first run | Each pool scored against the mask it was rendered with, plus an eroded interior. Anomaly was a mask-boundary artifact; plausibly-regenerated count is 0 |

| R6 | B1's first scoring pass used `.astype(np.uint8)` (truncation) where `MyTest.py` uses `cv2.imwrite` (rounding), biasing every prediction down ~0.5 grey levels | B1, pre-log | Endpoint MAE missed D2's independently measured value by 1.23e-03, failing a declared threshold | `np.round`; endpoint MAE became 0.074463 (delta 2.3e-07), Sα 0.717216 |
| R7 | B1's k-selection ranked k by bootstrap ARI, which is biased toward small k — it chose k=5, the worst silhouette in the sweep | B1, pre-log | The selected k had the worst compactness in its own sweep | Silhouette primary; stability reported but not used to rank; discarded criterion recorded in the log |
| R8 | B1 reported a per-cluster ρ of +1.0 on CAMO from 2 clusters | B1, pre-log | Reproduced the old package's +0.976 artifact | Per-cluster ρ suppressed below 5 surviving clusters |
| R9 | B1's `fit_kmeans` cached on `(k, seed)` and `endpoint_emb` on `split` alone, and `step_correlate` / `emit_cluster_es` called `assign_clusters` **without** a tag | B1, before the embedder sweep | Inert with one embedder; would have silently fed dinoL518's k-means fits and endpoint embeddings to the CLIP and dinoL224 runs | Cache keys include the tag; the tag is threaded through; defaults unchanged, verified by reproducing the committed block 7/7 |
| R11 | C1's ceiling assertion required `d_heldout = 0` at `B = 4447` as well as `‖Δmean‖ = 0` | C1, pre-log | The assertion fired | `‖Δmean‖ = 0` is the correct ceiling check; the held-out *d* there is a **null calibration**, not a bug — reported as a measurement rather than relaxed away |
| R12 | C1's plan §3.1 specified a `C2_SHAPE_DIVERGENCE` cross-check that the first implementation omitted | C1 blocks 1→2 | Re-reading the approved plan against the code | Implemented — and implementing it revealed the cross-check was a **category error**: C2's pool-shift and C1's *d* are different quantities with legitimately different B-shapes. Recorded, not dropped |
| R14 | C1's variance/coverage audit declared its spread threshold on **trace-of-covariance**, which is dominated by the isotropic bulk of a 1024-d embedding and moves only 1-2% | C1 block 4 | The threshold FAILED while effective rank (0.53-0.64, 20/20 cells) showed a large shape difference | The declared threshold is reported **FAILED**; effective rank is reported beside it as an **observation, not promoted to a threshold**. Swapping in the metric that agrees after seeing the data is the move this rebuild exists to prevent |
| R15 | C1 block 4's `ES_SIGNAL_INCREMENT_*` metrics, their two thresholds, and the ceiling cross-check were added **after** an exploratory `--no-log` pass | C1 block 4 | Self-declared | Recorded in the log block's `NOTES` and `C1_RESULTS.md` §8.7. They are **tightenings** — each makes the audit harder to pass, no declared threshold was weakened or removed (5 of 7 still FAIL), and their content was already implied by the pre-declared `SHUFFLED_ES_minus_NULL_max` metric; they only pair cells exactly instead of comparing a max over cells against a min over cells |
| R13 | C1's first Gate-1 scan flagged its own module docstring | C1, pre-log | The gate failed on a clean tree | Docstrings excluded (prose cannot read a CSV column), matching E0's fix. Gates then **self-tested** with an injected probe: both caught it, both returned to PASS when removed |
| R10 | B1 correlated **endpoint** ES throughout, and shipped C1 a cluster CSV with no `target_es` column | B1 completions I and II | Reading `CLS.py:81-82` — the loader is built on the target root with `gt_root=None`, so the allocation signal is GT-free and target-side | Target ES computed for all 4040 images × 5 architectures; `target_es` added to all three cluster CSVs; the faithful correlation measured. **Changed the direction of B1's headline claim** — see B1.8 |
| R16 | `common.py:248-263` claims `dir_digest` *"Matches the `agg` values pinned in REBUILD_PLAN.md §1."* **It does not** — measured `d7f6de696d5c223e` against the pinned `b42e5f44b5f2b0db` | ABC, while building the first arm pool | An ABC pool assertion written against §1's `agg` failed on data that was provably intact | The pinned values were computed over a **full-relative-path** listing; `dir_digest` hashes the **bare filename**. The path-prefixed variant reproduces both pinned values exactly. Never caught because **no `.py` references them**. Primary data is unchanged — all 4447+4447 verify per-file against E0's manifest. ABC now asserts against the manifest. **`common.py`'s docstring and `REBUILD_PLAN.md` §1 still need correcting** |
| R17 | `EXP ABC` #3's provenance annotation on the four `per_arm_sd_*` metrics asserts *"arm B carries selection variance A0 and C do not — pooled sigma_hat is inflated by it"* | ABC block #3, post-log | **The metric's own values refute its annotation**: arm B has among the lowest sds (**0.001807** SINet, **0.004863** SINet-v2); arm A0 is the largest | My prediction in `ABC_PLAN.md` §A.4 / §A.12 item 4 was wrong **in direction**, and I wrote it into the metric's provenance string before the runs. The **values are correct**; the explanation attached to them is not. Recorded rather than quietly corrected. Fixing it in the log needs a block #4 that changes no number |
| R18 | ABC's first pool-provenance check used the regex `Loaded 4[0-9]*`, which cannot match the 5447-image pools, and reported **18 spurious mismatches** | ABC, pre-evaluation | The "mismatches" were exactly the 18 non-A0 runs | Corrected before any conclusion rested on it; the corrected check returns **24/24** runs reading their own pool in round 1 and their own `_iteration2` in round 2. Recorded because the first number was wrong and it was mine |
| R19 | `D2_RESULTS.md` §3.0: *"quantization tables differ in **41/41** pairs"* | `EXP D2R`, T5 FAIL | An independent raw-DQT extraction returned **40/41**, not 41/41 | `animal-19.jpg` and `animal-28.jpg` in the CHAMELEON release are **PNG files carrying a `.jpg` extension**, so they have no JPEG quantization table. D2 compared tables with `!=`, scoring a *missing* table as a *differing* one — absence of evidence read as evidence. `animal-19` is one of the leaked 41. Properly **40/41 differing + 1 not applicable**. The pair's conclusion is unaffected and stronger: its container formats differ (413 KB PNG vs 132 KB JPEG of one photograph), so **41/41 still carry independent re-encoding evidence**. T5 is left FAILING against its declared wording; T5b states what survives |
| R20 | `D2_RESULTS.md` §3.0 cites **`MyTrain.py:220,297`** as feeding `get_tarloader` | `EXP D2R` | Line numbers re-derived from source instead of trusted | Line 220 is the `--source_root` **help string**; line 297 is the **EMA teacher weight copy**. The real call site is **`MyTrain.py:317`**. The *mechanism* D2 described is correct — the target pool enters training unlabeled and `CLS.py` pseudo-labels it from teacher CAMs — only the citation was wrong. Now asserted from source at run time so it cannot drift again |
| R21 | `REBUILD_PLAN.md` §3: *"primary endpoint COD10K; **secondary endpoints CHAMELEON and NC4K**"* | `EXP D2R`, T13 | Checked against the repo's own README for the first time | `README.md` mentions CHAMELEON **once**, inside the `Source (Synthetic)` CNC bundle, and lists only COD10K-test under `Test (Real)`. `Dataset/Source/CNC/` does not exist on disk; the undocumented `Dataset/Test/CHAMELEON/` does. `REPRODUCE_TABLE1_v2.md` has **0** CHAMELEON mentions and `Result/**` holds **0** CHAMELEON predictions. **We promoted CHAMELEON to an endpoint the repository never sanctioned.** The framing is therefore not "a bug in their evaluation" — CHAMELEON is *source* material in this design |
| R22 | `rebuild/D2/D2.md:38` records the command as `--steps s1,s2,s3,s4,s5,s6,s7` | `EXP D2R`, while establishing method identity | The authoritative `EXP D2` block ran `--steps s2,s3,s4,s4b,s5,s6,s7,s8` | The setup doc omits **`s4b`** and **`s8`**, the two steps that produced the gap analysis and the controlled seed experiment. Documentation-only; no number depends on it |

**R3 is the only one where a measurement was substantively wrong** rather than untraceable. It was
found by auditing my own method, not by the method reporting a problem — which is the failure mode
this rebuild is most exposed to.

## 3. Old values that RE-TESTED CLEAN

Worth recording explicitly: the old package's D2/D1 claims were marked `[no code]` — no producing
script, no log block — yet these all reproduce. **The old defect was provenance, not arithmetic.**
Being unverifiable is not the same as being wrong, and the rebuild has to be able to say so.

| Claim | Old value | Measured | Log block |
|---|---|---|---|
| COD10K-test ∩ Target | 7 (2 same-name, 5 cross-named) | 7 (2 same-name) | `EXP D2` |
| CAMO ∩ CHAMELEON | 3 | 3 | `EXP D2` |
| Internal duplicates in Target | 2 | 2 | `EXP D2` |
| Internal duplicates in the render pool | 2 (4445 unique) | 2 (4445 unique) | `EXP D2`, `EXP D1` |
| MAE impact of the leaked images | 0.000012 (0.017 %) | 1.242e-05 (0.0167 %) | `EXP D2` |
| Every added image is a re-render, not a new object | zero foregrounds outside the base pool | 0 outside; bijection both pools | `EXP D1` |
| ρ(ES, MAE) **per-image** test | +0.751 | **+0.7514** [+0.727, +0.777] | `EXP B1` |
| Invented background fraction | 80.87 % | 0.8087 (`staging_background_frac`, independent code path) | `EXP E0` |
| CHAMELEON contaminated by training data | 41/76 (53.9 %) | **41/76 (53.9 %)**, against an **author-sourced** copy | `EXP D2R` |
| The 41 leaked CHAMELEON filenames | 41 names | identical set, 41/41 | `EXP D2R` |
| Near-dup candidates shortlisted / confirmed / endpoint↔training | 323 / 132 / 49 | **323 / 132 / 49** | `EXP D2R` |
| CHAMELEON tolerance sweep | 11/26/37/40/41 | **11/26/37/40/41** | `EXP D2R` |
| CHAMELEON nearest-neighbour gap | 41 below 5.51, next at 40.58 | **41 below 5.51, next at 40.58** (7.36×), and invariant at shortlist depth 8/32/all | `EXP D2R` |
| CHAMELEON checkable / unchecked | 51/76 / 25 | **51/76 / 25** | `EXP D2R` |
| COD10K-test / NC4K / CAMO contamination | 2/2026, 1/4121, 4/250 | **2/2026 (0.1 %)**, **1/4121 (0.0 %)**, **4/250 (1.6 %)**, all three still on-disk copies only | `EXP D2R` |

## 4. Claims that changed in KIND, not value

| Claim | Old framing | Rebuilt framing | Log block |
|---|---|---|---|
| "Object preserved, background generated" | object *regenerated faithfully* | the **source object pixels are composited back** (`test.py:165`); object error 6.245 vs background 71.676 | `EXP E0` |
| Foreground exhaustion | "additions are re-renders" | **"the foreground pool is exhausted; the background is not"** — the object is fixed pixel-for-pixel, the background has unbounded freedom | `EXP D1` |
| "The generated pool" | one pool | **three** mutually non-identical pools; training reads the authors' pool, the old evidence embedded the local one | `EXP E0`, `EXP D2` |
| "The HKU-IS foreground fraction" | one number | **set-dependent** — `raw_gt` 0.19132 vs `auth_gt` 0.18557 | `EXP D1` |
| Cluster membership | a stable label | an unjustified preprocessing choice reassigns **5.4 %** of images (E0); silhouette peaks at only 0.1465 / 0.1600 / 0.0568 across the three embedder spaces, and CLIP has no interior peak at all — the unit of allocation is soft in **every** space | `EXP E0`, `EXP B1` |
| "ES predicts the wrong objective" | a binary verdict | an **effect size**: ES tracks pixel error ~2× as strongly as structural error (ρ 0.86 vs 0.43 per-cluster). The binary flips with k (ratio 0.4999 at k=75, 0.5825 at k=20), so the label is not k-stable and is not quoted | `EXP B1` |

## 5. Still outstanding

**Owed by D2R:** the COD10K-test, NC4K and CAMO contamination rates were measured against the copies
on this disk, not author-sourced ones — the exact weakness the CHAMELEON re-audit closed. The same
author-sourced re-audit is owed for those three, and `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` marks
every one of their rows as *not author-verified* rather than leaving the caveat implicit. Also
`UNVERIFIED`, and not claimable either way: whether the **published** S2R-COD paper reports a
CHAMELEON column anywhere — the PDF is not in this checkout. Flagged and unanswered: under
`--task C2C` the CNC bundle (CAMO + NC4K + CHAMELEON) is the **source** pool, so a C2C table
reporting CHAMELEON as a test set would be a direct source/test collision. Resolving that needs the
paper.


Every §4 row of `REBUILD_PLAN.md` belonging to A1, A2, A3, B2, B3, C2, C3 remains untested. The
load-bearing one is **C1** (`d ≈ 0.10`), which never had a producing script in the old package; it now
has its input ready — `rebuild/B1/out/b1_cluster_es_dinoL518.csv`, 75 clusters with per-cluster ES,
**with a mandated sensitivity re-run against `b1_cluster_es_dinoL224.csv` (50 clusters)**, because the
two spaces differ by 0.10 in ρ(ES,1−Sα) at k=20 and C1 must not re-cluster. Both CSVs now carry
`target_es`, and **C1 must allocate by `target_es`, not `test_es`** — completion II verified C1
runnable in both spaces (cutouts 4447×1024, row-aligned to the raw pool).

The old package's cross-run ρ(ES, MAE) = +0.893 ± 0.059 (n=5 runs) is **UNVERIFIED-DEFERRED**: it is a
seed-variance claim, and retraining is deferred. B1 substitutes a cross-architecture axis instead.

**C1's variance/coverage follow-up has now been run** (4th `EXP C1` block) even though its declared
trigger never fired, and it changed the interpretation of C1's headline — see C1.5-C1.8. The general
lesson is recorded here because it generalises past C1: *a threshold that PASSES deserves an audit as
much as one that fails.* The pre-audit draft of `C1_RESULTS.md` named this exact failure mode in its
own limitations section and then flagged the follow-up as the highest-value next measurement; running
it confirmed the limitation was decisive rather than formal.

**The highest-value next measurement is now C3.** C1.8 leaves a specific, testable hypothesis: the
targeted arm is more proximal to the target manifold on average but spans roughly half the effective
dimensionality and covers no more of it. Whether that profile trains worse, better, or identically is
exactly what C3 measures and what C1 structurally cannot. **A2 and B3 are the next most valuable**:
A2 because the 48-scalar conditioning bottleneck bounds how much of any selected difference can reach
a render at all, and B3 because C1's in-sample/held-out gap (C1.7) is the same estimator issue B3 was
designed to expose, now with a measured magnitude to check against.

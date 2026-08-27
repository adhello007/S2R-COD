# Stage C A/B/C ablation — experiment plan

**Deliverables.** Plan mode restricts me to this one file, so the four requested documents are the
four top-level sections below (§1 EXPERIMENT_PLAN, §2 PATCHES, §3 PREFLIGHT, §4 RISKS). On approval I
will split them into `EXPERIMENT_PLAN.md`, `PATCHES.md`, `PREFLIGHT.md`, `RISKS.md` verbatim.

---

## §0. Three premise corrections, verified before planning

**0.1 Two of the three documents you named as known context do not exist.**
`Issues_StageC.md` — **MISSING**. `STAGE_C_Issues2.md` — **MISSING**. `STAGE_C_PLAN.md` — **MISSING**
(it existed earlier in the session; it is gone from disk now). What exists and is real context:
`STAGE_C_MEASUREMENTS.md` (481 lines) and `STAGE_C_RED_TEAM_AUDIT.md` (415 lines). I have never
produced files by the first two names. This plan is built on the two that exist.

**0.2 SUPERSEDED — the dataset was updated 2026-08-27; all four test sets are now present.** Re-verified:

| set | files | note |
|---|---|---|
| `Test/COD10K/{Imgs,GT}` | 2026 | primary endpoint |
| `Test/CAMO/{Imgs,GT}` | 250 | **byte-identical to `Val/CAMO` — see §0.5** |
| `Test/CHAMELEON/{Imgs,GT}` | 76 | usable |
| `Test/NC4K/{Imgs,GT}` | 4121 | usable |

All four have `.jpg` images / `.png` GT with verified stem parity. The original requirement (a) — an
exhaustive sweep over all four — **can now be met in full**, and the earlier "scope to what's on disk"
decision is upgraded accordingly. What is *gone* and must be accounted for: `Dataset/Test/{Image,GT}`
(the flat layout `MyTest.py:51-52` hardcodes), `Dataset/Source/COD10K`, and all three
`Source/HKU-IS_iteration2*` CLS pools.

**0.3 The decisive one: `Dataset/Source/HKU-IS` and `Dataset/LAKERED/output/HKU-IS` are two
*independent* LAKE-RED samples, not copies.** Measured:

| | max abs pixel diff vs the other | MAE in object | MAE in background | mtime |
|---|---|---|---|---|
| `Source/HKU-IS/Image/0004.jpg` | 240 | 7.55 | 74.28 | **2025-07-23** |
| `LAKERED/output/.../SOD_0004.jpg` | — | 3.10 | 83.67 | **2026-08-21** |

Both preserve the object and regenerate the background, so both are LAKE-RED output — but they differ
by mean 35.8/255 and their GT white-fractions differ (0.211 vs 0.217). Combined with the mtimes and
`README.md:15`, `Source/HKU-IS` is the **authors' released synthetic dataset** (what the Table 1
reproduction trained on) and `LAKERED/output/HKU-IS` is the **local reproduction**, currently unused
by any training run.

**Why this matters:** arms B and C can draw their added images from an already-generated, independent,
never-trained-on pool. That removes generation from the critical path and removes rejection sampling
from the design entirely.

**The honest limitation it creates:** HKU-IS has exactly 4447 foregrounds and all of them are already
represented in the base pool. So *any* B/C addition is a **re-render** — same object, new invented
background — never a genuinely new foreground. This is not a choice; it is what the source dataset
permits. It makes the intervention weaker than "new scenes" would be, and that biases toward the
null. §1.3 mitigates it as far as is possible; §4 lists it as the top threat to interpreting a null.

---

## §0.5 Post-update re-verification — one new blocker, one requirement now satisfiable

Full pairwise md5 sweep over the new layout (executed):

| test set | ∩ Target | ∩ Source/HKU-IS (authors') | ∩ LAKERED/local |
|---|---|---|---|
| COD10K | **7** | 0 | 0 |
| CAMO | 0 | 0 | 0 |
| CHAMELEON | 0 | 0 | 0 |
| NC4K | 0 | 0 | 0 |

**NEW BLOCKER — the validation set *is* the CAMO test set: 250 / 250 byte-identical.**
`MyTrain.py:324` selects `Tea_epoch_best.pth` on `--val_root ./Dataset/Val/CAMO/`, and every one of
those 250 images is byte-identical to `Dataset/Test/CAMO/Imgs`. So every checkpoint in this experiment
— in all three arms — is chosen by its score on the CAMO test set.

Consequences, and they are not optional:
1. **CAMO is excluded from the evaluation.** Reporting it would be reporting the selection criterion.
   Primary endpoint stays COD10K-test; secondary become **CHAMELEON (76)** and **NC4K (4121)** only.
2. It applies identically to all three arms, so it **cannot bias B-vs-C** — the comparison stays valid.
   It bounds only the *absolute* numbers' external validity, which this experiment does not claim.
3. It is inherited from the published S2R-COD protocol (CAMO as val), not introduced here. Recorded as
   a protocol note, not silently fixed — changing the val set would break comparability with Table 1.

Also found: `CAMO ∩ CHAMELEON = 3` byte-identical images (two test sets sharing three photos), and
`LAKERED/local` contains 2 internal duplicate hashes (4445 unique of 4447). Both are logged, neither
blocks.

The 7 COD10K-test ∩ Target duplicates persist and are re-listed exactly (2 same-name: `Cat-1506`,
`Crab-32`; 5 cross-named: Owl-4633↔Bird-3205, Deer-1762↔Deer-1796, Gecko-1892↔Chameleon-1694,
Giraffe-1932↔Giraffe-1930, Gecko-1895↔Gecko-1928). Removal from `Target` before Phase 1 stands.

---

## §0.6 Which HKU-IS images does each arm use? — explicit

There are **two independent LAKE-RED renderings** of the same 4447 HKU-IS foregrounds on this machine.
They are not copies of each other (§0.3: mean 35.8/255 apart, 0 byte-overlap, different GT
white-fractions, mtimes a year apart).

| # | pool | path | provenance | used by |
|---|---|---|---|---|
| **P0** | raw HKU-IS | `Dataset/Source/HKU-IS_raw/{imgs,gt}` | original 2015 saliency dataset — real photos, **not** camouflage | foreground identity + object masks only; never trained on |
| **P1** | **authors' release** | `Dataset/Source/HKU-IS/{Image,GT}` | S2R-COD authors' post-processed LAKE-RED output, downloaded (mtime 2025-07-23), `README.md:15` | **base training pool for ALL THREE arms** (arm A trains on it alone) |
| **P2** | **our local render** | `Dataset/LAKERED/output/HKU-IS/{images,masks}` | generated on this machine 2026-08-21 by `run_hkuis.sh` from `Dataset/LAKERED/input/HKU-IS/validation/` (the inverted-polarity staged inputs), `--seed 0`, `--isReplace` | **render #0 of the bank → source of the additions for arms B and C** |
| **P3** | bank renders #1–3 | `Dataset/LAKERED/output/HKU-IS_k{1,2,3}/` (to be generated in Phase 0) | same staged inputs, `--seed 1,2,3` | remaining bank renders for arms B/C |

**So, plainly:**
- **Base pool (identical in A, B, C): the authors' pool P1.** This is what `--task S2C` selects at
  `MyTrain.py:232` and what the Table 1 reproduction trained on. Untouched.
- **Arm A adds nothing.** It trains on the base pool exactly as published CSRDA does.
- **Arms B and C's +2000: images from OUR local renders (P2/P3), never the authors' pool.** These are
  new pixels — same foreground object, a freshly invented camouflage background — and they are
  verifiably absent from the base pool (0 byte-overlap, 0 test-set overlap).

Arm B and arm C draw from the *same* bank; they differ only in **which foreground** and **which of the
K renders** they take. That is the entire intervention.

---

## §0.4 Locked decisions

| decision | choice | consequence |
|---|---|---|
| **Pre-check before committing** | **Run it first, as a hard gate** | Build the K=4 bank (~6.4 GPU-h), run arm-C selection, re-measure the block shift vs random. Phase 0 below. The 164-run commitment is **not** made until this number is in hand. |
| **Seed budget** | **N = 41 pairs** — but **contingent on §0.7 D2** | 164 runs, ~77 h (3.2 d) at 4 concurrent, MDE = 0.00178 Sα = **0.50 σ**, meeting the stated requirement exactly. **This lock holds only if D2 resolves to direction (i).** Under D2(iii) it drops to N=13 (52 runs, ~24 h, MDE 0.88 σ). Do not treat 41 as settled until D2 is answered. |
| **Leakage-sweep scope** | ~~COD10K-test + CAMO-val~~ → **UPGRADED: all four test sets** | The 2026-08-27 dataset update added CAMO/CHAMELEON/NC4K (§0.2), so requirement (a) is now met in full. Sweep executed already: only the 7 known COD10K↔Target duplicates. |
| **Evaluation endpoints** | **COD10K-test (primary), CHAMELEON + NC4K (secondary). CAMO excluded.** | Forced by §0.5 — `Val/CAMO` is byte-identical to `Test/CAMO`, so CAMO is the checkpoint-selection set and cannot also be an endpoint. |
| **Network** | **SINet only** | σ=0.00356 was measured on SINet; a second architecture needs its own noise floor (+6 runs) and doubles multiplicity. Single-architecture is an explicit scope limit. SINet-v2 replication is the follow-up *if* C−B lands significant. |
| **Budget B** | **B = 2000** (was 1000) | The measured optimum. Training cost is identical at any B (`total_step` pins at 253), and B=2000 gives 1.26× the B-vs-C pool shift. See §0.7 for why larger is *worse*. |
| **Arm C's levers** | **Bundled** — allocation *and* best-of-K render together | The prior is that no effect exists, so the first job is to detect one at all; bundling hands arm C every advantage. Attribution is a second experiment, earned only if this one finds something. |
| **B/C foreground overlap** | **Independent draws** (~55% overlap at B=2000) | Forced-disjoint would make arm B "the complement of C's choices" — itself a targeted selection, which would make a positive result uninterpretable. Independent draws is also what a real deployment does. |
| **Primary test** | **Two-sided paired t-test on Sα**, Wilcoxon signed-rank as a pre-registered sensitivity check | n=41 makes t robust and Sα≈0.70 is far from the [0,1] boundaries. Reporting both, with a rule to flag disagreement, removes the temptation to pick whichever crosses 0.05. |

### Execution phasing

**Phase 0 — the gate (must complete and be reviewed before Phase 1 starts).**
1. Build the K=4 render bank: 3 fresh `LAKE-RED/test.py` passes at `--seed 1,2,3` into separate
   `--dst_root`s, plus the existing local reproduction as render #0. ~6.4 GPU-h of new generation.
2. Run Gate 1 (`leakage_report.json`) — must be all-green.
3. Embed the bank with DINOv2 L/14 @518, fit k=20 on the 4033 clean target images.
4. Compute the arm-C selection (allocation + best-of-K) for **3 pilot seeds** and measure the block
   shift `‖mean_C − mean_B‖ / pooled sd` in DINOv2 space, exactly as the audit measured d≈0.10 for
   foreground-selection alone.
5. **Report that number and stop.** Decision point: if best-of-K lifts the block shift materially
   above 0.10, Phase 1 proceeds as planned. If it stays ≈0.10, the experiment would be re-measuring
   what the audit already extrapolated from, and we decide together whether 77 GPU-h is warranted or
   whether the honest move is to report the bound analytically and redirect the compute.

**Phase 1 — the ablation (only after the Phase 0 review).** 41 seeds × 4 runs, Gate 2 after every
pool assembly, results table + paired tests + per-cluster mechanism check.

No training runs at all in Phase 0 — it is generation, embedding, and selection arithmetic only.

---

## §0.7 OPEN DOUBTS — not settled, and I am not confident enough to settle them alone

### D1 (retraction) — "raise B" was arithmetically wrong. Corrected here.

`STAGE_C_RED_TEAM_AUDIT.md` and my earlier review both advised raising B to increase the effect.
**That was wrong** and the correction changes the ceiling on this whole experiment.

Arm C takes the top-B foregrounds by allocation; arm B takes B at random; expected overlap is
B²/4447, so the fraction of the added block that actually *differs* between the arms is (1 − B/4447).
Pool-level B-vs-C shift = (B/|Ds|) × (1 − B/4447):

| B | block % of pool | % of block differing | pool shift | vs B=1000 | predicted ΔSα | in σ |
|---|---|---|---|---|---|---|
| 1000 | 12.8% | 77.5% | 0.0128 SD | 1.00× | 0.000111 | 0.031 σ |
| **2000** | **22.7%** | **55.0%** | **0.0161 SD** | **1.26×** | **0.000140** | **0.039 σ** |
| 3000 | 30.5% | 32.5% | 0.0128 SD | 1.00× | 0.000111 | 0.031 σ |
| 4447 | 39.5% | **0%** | **0** | **0.00×** | 0 | 0 |

Raising B buys at most **1.26×** and then *reverses*, because the two arms converge on identical
content. **No budget setting can rescue the effect size.** At B=2000 the predicted effect is 0.039σ
against a 2σ bar — it would need 51× the linear response rate.

### D2 — the research-direction fork. This is the real question and it is yours to answer.

Given D1, the honest position is that this experiment is very likely to return a null, and we now know
no parameter choice changes that. Three directions:

**(i) Run A/B/C as planned (77 h).** Delivers a *powered* null: "any targeting effect is below 0.5σ,"
measured rather than extrapolated. Scientific value is real but bounded — it closes a question rather
than opening one. Risk: 3.2 days for a negative result whose magnitude we already predict.

**(ii) Skip the ablation; spend the compute on the generator-side conditioning ablation instead.**
The audit's conclusion was that the only experiment that converts diagnosis into prescription is
widening LAKE-RED's conditioning channel — concatenating a target-cluster embedding into BKRA's
cross-attention at `ddpm.py:1579` — and showing acceptance *and* generative recall both rise. That
attacks the actual bottleneck (a 48-number colour bottleneck; recall 0.466 vs a 0.939 ceiling) rather
than measuring a lever we already know is weak. Risk: it is real ML engineering on someone else's
diffusion codebase, with no guarantee of success, and it produces no COD accuracy number.

**(iii) Do (i) at reduced scale (13 pairs, 24 h, MDE 0.88σ) and put the saved 53 h into (ii).**
Gets a defensible-but-weaker null on the ablation plus a genuine attempt at the mechanism.

➡️ **My recommendation: (iii), with the reduced A/B/C run gated on Phase 0.** Reasoning: a null at
MDE 0.88σ is already enough to rule out any effect worth writing about, given the predicted effect is
0.039σ — the extra 53 h to tighten 0.88σ→0.50σ buys precision on a number we are confident is
indistinguishable from zero. That compute is worth far more pointed at the generator. **But this is a
judgement about what paper you want, not a technical fact, so I am leaving it open.**

### D3 — round-2 questions, blocked on nothing now that D2's shape is clear

**D3a — bank size K.** Arm C's second lever is best-of-K render selection. K=2 costs 2.1 GPU-h of new
generation, K=4 costs 6.4 h, K=8 costs 15.0 h. Larger K = stronger lever (more chances to find a
render near the cluster centroid) but diminishing: the renders are i.i.d. samples from the same
conditional, so the expected best-of-K distance to a centroid improves like the K-th order statistic.
➡️ **K=4.** Cheap, and doubling to 8 for a marginal order-statistic gain is not worth 9 extra hours.

**D3b — the Phase-0 gate threshold. This is a genuine pre-registration hole.** I wrote "if best-of-K
lifts the block shift materially above 0.10, proceed" without defining "materially." Without a number
the gate is subjective and can be rationalised either way after seeing the result.
➡️ **Proposed rule: proceed only if the measured B-vs-C block shift at B=2000 exceeds d = 0.25**
(≈3.5× the 0.071 currently predicted). Rationale: d=0.25 is the point at which the predicted ΔSα
reaches ~0.00049 = 0.14σ — still below detectability, but it would mean my linear model is badly
wrong in the favourable direction, which is itself the only evidence that would justify the runs.
**I am not confident in this threshold** and would rather agree it with you than defend it alone.

**D3c — what happens if Phase 0 fails the gate.** Options: abandon the ablation and pivot to D2(ii);
run a token 13-pair version anyway for the record; or run it and report the analytic bound instead of
training at all.
➡️ **Pivot to D2(ii)**, and report D1's table as the result — it is a derivation, not a measurement,
but it is a correct and sufficient answer to "can budget allocation matter here."

### D4 — doubts I cannot resolve by any amount of planning

1. **The re-render ceiling.** Every addition is the same 4447 foregrounds re-rendered. A null is
   scoped to "targeting does not help when the foreground pool is exhausted," never to "targeting
   does not help." Only a new foreground source (CAMO/NC4K-derived cutouts, or another SOD dataset)
   would lift this, and that changes the paper.
2. **Whether ES→Sα at ρ≈0.65 (k=20) is good enough** for allocation to be able to help even in
   principle. Allocation optimises a proxy that explains ~42% of the variance in the objective.
3. **Whether σ transfers** from the 4447-pool noise-floor runs to the 8824-pool arms. Re-estimated
   from the arm-B/C runs themselves, but not knowable in advance.
4. **Whether the fork is empirically identical** to a monolithic 2-iteration run. Verified by code
   reading (`MyTrain.py:250-290` resets everything but `source_root`), never by running both.

---

## §1. EXPERIMENT_PLAN

### 1.1 The question

Does deficiency-targeted synthetic data (arm C) change final COD accuracy relative to the same volume
of randomly-chosen synthetic data (arm B), and relative to unmodified CSRDA (arm A)?

Prior analysis predicts C−B ≈ 0.031σ from a linear extrapolation off one anchor point. This experiment
replaces the extrapolation with a measurement. **It is designed to detect an effect, and it is
explicitly not powered to confirm the point prediction** — see 1.5, which states plainly that no
feasible experiment can resolve 0.031σ, and what this one can resolve instead.

### 1.2 The three arms

All three are iteration-2 retrains that share, per seed, one iteration-1 teacher and one CLS pool.
They differ **only** in the contents of 1000 appended slots.

| arm | appended | \|Ds\| | each image seen | role |
|---|---|---|---|---|
| **A** baseline | **nothing** — unmodified CSRDA | 6824 | 23.1× | reference point |
| **B** random | **2000** bank renders, foreground + render both uniform-random | 8824 | 17.9× | control for arm C |
| **C** targeted | **2000** bank renders, foreground allocated by `d(c)` + best-of-K render | 8824 | 17.9× | the intervention |

**`B→C` is the decisive contrast** and it is exactly clean: identical pool size, identical per-image
exposure, identical step count, identical everything except *which* 1000 images. This is the
pre-registered primary endpoint.

**`A→B` is a reference, not a clean causal contrast.** Because `total_step` is pinned at 253
(`MyTrain.py:306-307`), all arms draw the same 4048 images/epoch and the same 157,872 total
presentations — but a larger pool spreads them thinner, so arm A's images are each seen 23.1× against
17.9× in B/C. That dilution is **not a confound to be removed: it is intrinsic to what "adding
2000 images" means in this pipeline.** You cannot add data at a fixed step budget without diluting
exposure. A→B therefore honestly answers "what happens when you add 2000 synthetic images to CSRDA,"
dilution included, and is reported as such.

*Superseded design note:* an earlier draft padded arm A with 1000 duplicated images to equalise
exposure. That is **dropped.** It would have made arm A no longer the published CSRDA baseline, and it
answers an artificial question (holding exposure fixed) rather than the real one. If a dilution-free
A→B contrast is ever wanted it belongs as an optional 4th arm A′ (+41 runs, ~19 h), not as a
replacement for A.

### 1.3 Fair power — where the comparison is clean and where it is not

`total_step = min(len(source_loader), len(target_loader))` (`MyTrain.py:306-307`) pins the step count
at 253 for every arm, and `Dataloader.py:206` shuffles, so:

| | \|Ds\| | images/epoch | P(seen/epoch) | seen over 39 ep | total presentations |
|---|---|---|---|---|---|
| A | 6824 | 4048 | 0.593 | 23.1× | 157,872 |
| B, C | **8824** | 4048 | **0.459** | **17.9×** | 157,872 |

**B vs C is exactly clean** — same size, same exposure, same steps. Nothing needs equalising, because
the intervention *is* the swap of which 1000 images occupy the added slots.

**A vs B carries the exposure dilution and we keep it.** Adding 2000 images at a fixed step budget
necessarily thins per-image exposure by 23%; that is a property of the pipeline the paper published,
not an artefact this experiment introduces. Arm A stays the untouched CSRDA baseline. A→B is reported
as "what adding 1000 synthetic images does, dilution included," and is explicitly *not* claimed as an
isolated measurement of "new information."

**Strengthening arm C's lever (so the design is not stacked toward the null).** Arm C gets two levers,
not one:
1. **Which foreground** — allocation across k=20 DINOv2 clusters by deficiency score.
2. **Which render of that foreground** — a one-time bank of K=4 independent LAKE-RED samples per
   foreground; arm C keeps the render whose embedding is nearest the intended cluster centroid
   (best-of-K), arm B keeps a uniformly random render.

Best-of-K is the strongest steering available without rejection sampling, and it costs nothing at run
time because the bank is built once. Bank cost: 4447 × 4 = 17,788 generations = **8.5 GPU-h one-time**
(one of the four is already on disk, so ~6.4 GPU-h of new generation).

### 1.4b Arm C, step by step — what DINOv2 does and where the disagreement score enters

Answering the two questions directly: **DINOv2 is used only to partition the target domain and to
embed candidate renders. It never computes the disagreement score.** The disagreement score is
computed by the repo's own SINet student/teacher pair through `ESLoss` — one scalar per *target*
image — and is then averaged inside each DINOv2 cluster. DINOv2 defines the buckets; SINet scores them.

**ONE-TIME (offline, before any seed — Phase 0):**

| step | operation | input → output |
|---|---|---|
| O1 | Remove the 7 test-duplicate images from `Target` | 4040 → **4033** target images |
| O2 | Embed all 4033 target images with **DINOv2 ViT-L/14, native 518 px, CLS token, L2-normalized** | 4033 × 1024 |
| O3 | **k-means, k = 20** on those embeddings | 20 centroids `μ_1..μ_20`; each target image gets a cluster label |
| O4 | Generate bank renders #1–3 (`--seed 1,2,3`) | 4 renders per foreground × 4447 foregrounds |
| O5 | Embed all 4 × 4447 bank renders with the same DINOv2 config | 17,788 × 1024 |

Nothing here involves the segmentation model, and nothing here varies by seed.

**PER SEED s (this is where the disagreement score is computed):**

| step | operation | detail |
|---|---|---|
| S1 | Train iteration-1 on P1 with seed s | → `Stu_40.pth`, `Tea_epoch_best.pth` |
| S2 | Run CLS once with that pair | → `pool_s` (≈6824 = 4447 synthetic + ≈2377 pseudo-labelled real) |
| S3 | **Compute the disagreement score.** For every one of the 4033 target images: forward it through *both* the student and the teacher at 352×352, then `ES_i = ESLoss(a=0.9, b=0.3, use_weighted_bce=False)(stu.sigmoid(), tea.sigmoid())` | one scalar per target image — exactly the `CLS.py:105` / `CLS.py:138` call |
| S4 | **Aggregate into the DINOv2 clusters from O3.** `d(c) = mean{ ES_i : image i ∈ cluster c }`, **λ_cov = 0** — no coverage term | 20 scalars |
| S5 | Allocate the budget: `w_c = softmax(d(c) / T)` with **T = 0.02 fixed a priori**; `B_c = floor(w_c × 2000)` | 20 integers summing to ≈2000 |
| S6 | **Foreground selection (lever 1).** For each cluster c, take the `B_c` HKU-IS foregrounds whose *cutout* embedding is nearest `μ_c`, without reuse across clusters | 2000 foreground ids |
| S7 | **Render selection (lever 2, best-of-K).** For each selected foreground, choose the one of its K bank renders whose embedding is nearest that cluster's `μ_c` | 2000 (image, mask) pairs |
| S8 | Append to `pool_s` under the `z_stagec_C_s{seed}_*` naming scheme; write the manifest | pool_C = 8824 |
| S9 | Gate 2 checks, then train iteration-2 with seed s | → arm-C result |

**Arm B is S6–S9 with S3–S5 skipped:** 2000 foregrounds drawn uniformly at random, and one of the K
renders drawn uniformly at random — *from the same bank as arm C*, so B and C differ only in the
selection criterion, never in the candidate set. **Arm A skips S3–S8 entirely** — it trains on
`pool_s` as-is.

So the answer to "are we calculating the disagreement score during this process of checking?" — yes,
once per seed at step S3, using that seed's own iteration-1 student and teacher, over the target
images, before arm C's pool is assembled. It is never recomputed during training and never uses
DINOv2.

### 1.4 Deficiency score (arm C only)

Per the audit's surviving findings:
- Clustering: **DINOv2 ViT-L/14, native 518 px, CLS token, L2-normalized, k=20**. k=20 is the only
  setting where deficient-cluster acceptance was materially above zero (20.62% held-out, 12.3× chance).
- Score: **`d(c) = mean_over_cluster ES(student, teacher)`, λ_cov = 0.** The coverage term is dropped —
  the audit found ρ(coverage, true error) = +0.006 on test and **−0.717 on val**, and that adding it
  flips a +0.800 signal to −0.733.
- ES: the repo's own `ESLoss(a=0.9, b=0.3, c=0.5, use_weighted_bce=False)` from
  `Src/utils/tool.py:45-77`, fed `stu.sigmoid()` / `tea.sigmoid()` at 352×352 — byte-for-byte the
  `CLS.py:105` / `CLS.py:138` convention.
- Allocation: temperature softmax over d(c), **T = 0.02 fixed a priori and never tuned** (the audit
  measured that T changes the resulting data distribution by <0.02 Cohen's d across a 10× sweep, so
  tuning it is both pointless and a p-hacking surface).
- Teacher/student: that seed's own iteration-1 pair, so arm C's allocation varies per seed exactly as
  it would in a real deployment.

### 1.5 Statistical power — stated honestly

Noise floor, from the audit `[R1]`, n=6 independent runs recomputed from prediction files:

| metric | σ (arm-run) | relative |
|---|---|---|
| **Sα** | **0.00356** | 0.5% |
| Fβw | 0.00844 | 1.9% |
| Eφ (meanEm) | 0.00439 | 0.6% |
| MAE | 0.00388 | 4.4% |

Variance decomposition: fixed-seed σ = 0.00229, distinct-seed σ = 0.00286 ⇒ seed-attributable
sd = 0.00171, so ρ(arms sharing a seed) = **0.359**. Pairing therefore buys only 20%:
**σ_d(C−B) = 0.00356 × √(2(1−0.359)) = 0.00403.**

Paired t-test, 80% power, two-sided α = 0.05:

| target effect | δ (Sα) | pairs needed | training runs (4/seed) | wall clock @4 concurrent |
|---|---|---|---|---|
| 2.0 σ | 0.00712 | 3 | 12 | 5.6 h |
| 1.0 σ | 0.00356 | 11 | 44 | 20.6 h |
| **0.5 σ** | **0.00178** | **41** | **164** | **76.7 h (3.2 d)** |
| 0.25 σ | 0.00089 | 161 | 644 | 301 h |

Minimum detectable effect at a given budget:

| pairs | runs | wall clock | MDE (Sα) | MDE in σ |
|---|---|---|---|---|
| 13 | 52 | 24.3 h | 0.00313 | 0.88 σ |
| 20 | 80 | 37.4 h | 0.00252 | 0.71 σ |
| 26 | 104 | 48.6 h | 0.00221 | 0.62 σ |
| **41** | **164** | **76.7 h** | **0.00178** | **0.50 σ** |

**LOCKED: N = 41 pairs**, which meets the "0.5σ must be visible" requirement exactly. Pre-registered
before any Phase 1 run; not to be extended or truncated on the basis of an interim look (no
alpha-spending schedule is defined, so a peek-and-extend would invalidate the stated α).

**And the thing I must not obscure:** resolving the *predicted* 0.031σ effect would need ~10,500
pairs. No feasible experiment can do that. So the experiment cannot "confirm the prediction." What
N=41 buys is the ability to **bound** the effect: if C−B comes back inside ±0.00178 we can state, at
80% power, that any targeting effect is smaller than half a standard deviation of run-to-run noise.
That is a measurement, not an extrapolation, and it is the scientifically useful statement available.
A null at N=41 is materially stronger evidence than a null at N=13 — I will report the achieved N and
its MDE alongside any null, never a bare "no difference."

Runs are ~1.87 h each measured (39 epochs × 253 steps, SINet, 2 concurrent per GPU; 4 concurrent
across the two RTX PRO 6000s is throughput-optimal — 3-per-GPU measured *worse* at 0.33 vs 0.40
epochs/min).

### 1.6 Fork structure (per seed s)

1. Train iteration-1 on `Dataset/Source/HKU-IS` (4447), seed s → `Stu_40.pth`, `Tea_epoch_best.pth`.
2. Run CLS once with that pair → `pool_s` (~6824), written to a seed-tagged path.
3. Score deficiency from that same pair → per-cluster d(c) → allocation for arm C.
4. Assemble the three pools: **A = `pool_s` unchanged (6824)**, B = `pool_s`+2000 (8824), C = `pool_s`+2000 (8824).
5. Train iteration-2 three times (arms A/B/C), seed s, each reading its own pool.

= **4 training runs per seed.** This is exactly equivalent to the published 2-iteration protocol:
the audit §4(b) verified that `MyTrain.py:250-290` rebuilds model, EMA, and optimizer and resets
`global_step`/`best_teamae`/`best_epoch` inside the loop, so **nothing crosses the iteration boundary
except `opt.source_root`**. Running iteration 2 as a fresh `--iteration 1` invocation on the
iteration-2 pool is therefore protocol-identical — and *better* for a paired test, because all three
arms get bit-identical initialization from the same seed in fresh processes.

**Protocol fidelity:** 2 CSRDA iterations, unchanged. No extra iterations, no extra epochs, no changed
step count. `total_step` stays 253 for all arms (verified).

### 1.7 Metrics, tests, and the pre-registered decision rule

Report **Sα, Fβw, Eφ, MAE** per arm per seed, mean ± sd, using the repo's own `Eval/metrics.py` at the
`Eval/MyEval.py:33-39` convention, on:

| endpoint | set | n | role |
|---|---|---|---|
| **primary** | COD10K-test | 2026 | the pre-registered decision rule applies here only |
| secondary | CHAMELEON | 76 | generalization; n=76 makes it noisy — reported descriptively |
| secondary | NC4K | 4121 | generalization; largest set, best-powered secondary |
| **excluded** | CAMO | 250 | it *is* `Val/CAMO` (§0.5) — the checkpoint-selection set |

Evaluation cost: 6223 images × 164 checkpoints ≈ **+20 h** on top of the 77 h of training, so Phase 1
is ~97 h (≈4 days) of GPU occupancy end to end.

**Primary endpoint: Sα, C−B, paired t-test across the N seeds, two-sided α = 0.05.** Sα is primary
because it is the headline COD metric; Fβw/Eφ/MAE are secondary and reported with Holm correction
across the three.

Pre-registered rule, fixed before any run:

- **C−B > 2σ (0.00712) on Sα and p < 0.05** → targeting produces a measurable effect.
- **|C−B| < 2σ and the 95% CI excludes ±0.5σ (±0.00178)** → the effect is bounded below 0.5σ;
  **null confirmed by measurement** at the stated resolution.
- **CI wider than ±0.5σ** → underpowered; report the CI and the achieved MDE, and label the result
  inconclusive rather than null.
- Sign is reported regardless. A negative C−B (targeting hurts) is a valid, reportable outcome.
- Secondary: A−B on Sα, same test — answers "does new synthetic data help at all."

**Mechanism check (not just the aggregate).** For each cluster c: assign COD10K-test images to the
k=20 clusters, compute mean Sα per cluster for arm C and arm B, and report (i) ΔSα_c = Sα_c(C) −
Sα_c(B) for funded vs unfunded clusters, and (ii) ρ(budget B_c, ΔSα_c). If the aggregate is null but
funded clusters improved and unfunded ones degraded, that is a real mechanism with a zero-sum
aggregate — a different and more interesting finding than "nothing happened," and the aggregate test
alone would miss it.

### 1.8 Reproducibility

- `--seed` CLI arg, recorded in every run's log and in the results table. Seeds are **varied**
  (1001…1041), never frozen — we are measuring variance, not eliminating it.
- `worker_init_fn` added so the 6 dataloader workers get distinct, seed-derived numpy streams
  (currently all 6 inherit the parent's state — `Dataloader.py:200-219` passes no `worker_init_fn`
  while `SrcDataset.__getitem__:32` calls `np.random.rand()`).
- **cudnn determinism deliberately NOT enabled.** Real run-to-run variance is the quantity the
  decision rule is calibrated against; forcing determinism would understate σ and inflate false
  positives.
- Every arm pool's exact file manifest is written to disk (`pool_manifest_{arm}_s{seed}.json`) so any
  result can be traced to the exact file list that produced it (6824 for A, 8824 for B/C).

---

## §2. PATCHES

Every change is additive and default-preserving: with no new flags passed, existing commands behave
byte-identically. Nothing in the paper's protocol is altered.

### P1 — `MyTrain.py`: `--seed` CLI arg
*Audit finding:* `MyTrain.py:242` hardcodes `set_random_seed(42)`; no seed can be varied.

```
# after line 218 (--save_model), ADD:
parser.add_argument('--seed', type=int, default=42, help='RNG seed (was hardcoded at :242)')

# line 242, BEFORE:
    set_random_seed(42)
# AFTER:
    set_random_seed(opt.seed)
```
Default 42 ⇒ existing invocations unchanged. (Already validated this session: the 6 noise-floor runs
used exactly this patch.)

### P2 — `MyTrain.py`: per-iteration, per-arm checkpoint directory
*Audit finding:* `opt.save_model` is one constant used at `:141`, `:146-151`, `:187`, `:309`, `:324`
and handed to `cls()` at `:328`, so iteration 2 overwrites iteration 1's `Tea_epoch_best.pth` /
`Stu_40.pth`, and — worse — `CLS.py:65` reads `Tea_epoch_best.pth` from that same directory, so two
arms sharing `--save_model` can pseudo-label from each other's teacher.

```
# inside the iteration loop, before line 292 (loader construction), ADD:
        opt.save_model = os.path.join(base_save_model, f'it{i}') + os.sep
        os.makedirs(opt.save_model, exist_ok=True)
# and capture the original once, before line 245:
    base_save_model = opt.save_model.rstrip('/\\')
```
In the fork design each arm is a separate process with its own `--save_model`, so this is belt-and-braces;
it is still required so that a monolithic `--iteration 2` run cannot self-overwrite.

### P3 — `CLS.py`: explicit output root, no derived path, no self-rmtree
*Audit finding:* `CLS.py:16-17` derives `_iteration{N}/` from `source_root`/`gt_root` alone — `network`
is a parameter (`CLS.py:13`) that never enters the path — and `:21`/`:27` `rmtree` it on entry. Also
`MyTrain.py:328` passes `opt.source_root` as **both** `source_root` and `gt_root`, so
`source_copy_root == gt_copy_root` and lines 25-29 delete the copy lines 19-23 just made.

```
# line 13, BEFORE:
def cls(model_path, source_root, gt_root, target_root, ES_loss, u, tau, iteration=1, testsize=352, dataset_name='COD10K', network='SINet'):
# AFTER:
def cls(model_path, source_root, gt_root, target_root, ES_loss, u, tau, iteration=1, testsize=352,
        dataset_name='COD10K', network='SINet', out_root=None):

# lines 16-17, BEFORE:
    source_copy_root = source_root.rstrip('/\\') + f'_iteration{iteration + 1}/'
    gt_copy_root     = gt_root.rstrip('/\\')     + f'_iteration{iteration + 1}/'
# AFTER:
    if out_root is None:                      # unchanged legacy behaviour
        out_root = source_root.rstrip('/\\') + f'_iteration{iteration + 1}/'
    source_copy_root = out_root
    gt_copy_root     = out_root if os.path.normpath(gt_root) == os.path.normpath(source_root) \
                       else out_root

# lines 25-29, BEFORE: unconditional rmtree + copytree of gt_root
# AFTER: guard the alias
    if os.path.normpath(gt_copy_root) != os.path.normpath(source_copy_root):
        if os.path.exists(gt_copy_root): shutil.rmtree(gt_copy_root)
        shutil.copytree(gt_root, gt_copy_root)
```

### P4 — `MyTrain.py:328`: pass the tagged output root
```
# BEFORE:
new_source_root = cls(opt.save_model, opt.source_root, opt.source_root, opt.target_root, PGT_Loss, opt.u, opt.tau, iteration=i, network=opt.network)
# AFTER:
new_source_root = cls(opt.save_model, opt.source_root, opt.source_root, opt.target_root,
                      PGT_Loss, opt.u, opt.tau, iteration=i, network=opt.network,
                      out_root=opt.cls_out_root)   # new CLI arg, default None => legacy path
```
`MyTrain.py:329` (`opt.source_root = new_source_root`) then reads back this arm's own pool — the
return value at `CLS.py:162` is `source_copy_root`, which is now the tagged path.

### P5 — `Src/utils/Dataloader.py`: worker seeding
*Audit finding:* `get_srcloader`/`get_tarloader` (`:200-219`) pass no `worker_init_fn`, while
`SrcDataset.__getitem__:32` calls `np.random.rand()` inside 6 forked workers that all inherit the
parent's numpy state.

```
# add a module-level helper and pass it in both loader factories:
def _seed_worker(worker_id):
    import numpy as _np, random as _r, torch as _t
    s = _t.initial_seed() % 2**31
    _np.random.seed(s + worker_id); _r.seed(s + worker_id)
# then in get_srcloader / get_tarloader DataLoader(...):
                                  worker_init_fn=_seed_worker,
```
This changes the augmentation stream, so it is a **deliberate deviation** from the Table 1
reproduction. Justification: it is required for the arms to be independently seeded rather than
sharing a correlated flip sequence, and it is applied identically to all three arms so it cannot bias
B-vs-C. Recorded in the results as a protocol note.

### P6 — new `stage_c/assemble.py` (no existing file modified)
Standalone, read-mostly: builds the bank index, computes DINOv2 embeddings, k-means (k=20), the
deficiency score, the allocation, and writes each arm's pool + manifest. Reuses
`Src/utils/tool.ESLoss`, `Src/utils/Dataloader.test_dataset`, and the model constructors — no
reimplementation.

### P7 — new `stage_c/preflight_stagec.py`
The gate in §3. Reuses `preflight.py:325-342` (`pairing()`) and `preflight.py:362+` (the `filter_files`
silent-drop check) rather than reimplementing them.

### P9 — `MyTest.py`: parameterize the test-set root (NEW — the dataset update broke it)
*Cause:* `MyTest.py:51-52` hardcodes `./Dataset/Test/Image/` and `./Dataset/Test/GT/`. Both paths were
removed in the 2026-08-27 update; the layout is now `Dataset/Test/<SET>/{Imgs,GT}`. **`MyTest.py` will
crash as-is.**

```
# after line 21 (--gpu), ADD:
parser.add_argument('--test_root', type=str, default='./Dataset/Test/COD10K',
                    help='test set root containing Imgs/ and GT/')
# line 47, BEFORE:
for dataset in ['COD10K']:
# AFTER:
for dataset in [os.path.basename(opt.test_root.rstrip('/'))]:
# lines 51-52, BEFORE:
    test_loader = test_dataset(image_root='./Dataset/Test/Image/'.format(dataset),
                               gt_root='./Dataset/Test/GT/'.format(dataset),
# AFTER:
    test_loader = test_dataset(image_root=os.path.join(opt.test_root, 'Imgs') + os.sep,
                               gt_root=os.path.join(opt.test_root, 'GT') + os.sep,
```
All four sets have verified `.jpg`/`.png` stem parity, so `test_dataset`'s positional pairing
(`Dataloader.py:117-125`) is safe here — Gate 1 asserts it per set rather than assuming it.

### P8 — `LAKE-RED/test.py`: none required
Bank generation uses the existing CLI: `--seed {1,2,3}` (already present at `test.py:199`) with a
distinct `--dst_root` per K. `test.py:111-113`'s resume-skip works in our favour — a fresh `dst_root`
per K means nothing is skipped.

---

## §3. PREFLIGHT

Two gates. Both write JSON and **exit non-zero on any failure**; the training driver refuses to start
unless the corresponding JSON exists, is fresh, and has `"status": "PASS"`.

### Gate 1 — before pool assembly: `leakage_report.json`

| check | method | pass condition |
|---|---|---|
| L1 exhaustive pairwise hash | md5 of every file in `Test/Image`, `Val/CAMO/Imgs`, `Target/Image`, every `Source/*/Image`, the K-render bank | `Test ∩ (any trained-on set) = ∅` |
| L2 near-duplicate sweep | DINOv2 L/14 1-NN from every test image into every trained-on set | no pair below the 1st-percentile intra-test NN distance |
| L3 arm-B/C provenance | every bank render's manifest row traces to an `HKU-IS_raw` stem | 100% HKU-IS-derived, 0 test-derived |
| L4 centroid purity | hash the exact index list used to fit k-means | the 7 known Test∩Target stems absent; recorded count = 4033 |
| L5 internal duplicates | md5 within each set | reported (2 known inside `Target/`); fail only if inside an arm pool |

**L1 requires a pipeline change and I am flagging it as a deliberate deviation:** the 7 Test∩Target
duplicates (2 same-name, 5 cross-named) must be **removed from `Dataset/Target/Image` before this
experiment**, because CLS pseudo-labels from `target_root/Image/` (`CLS.py:115-156`) and would
otherwise carry pixel-exact test images into every arm's pool — as it did in the Table 1 reproduction
(5/7, 3/7, 2/7 across the three archived pools). Measured impact on the reproduction was 0.000012 MAE
with no memorisation signature (mean percentile 0.477), so removing them does not invalidate the
baseline; it makes this experiment defensible. `Target` goes 4040 → 4033, which leaves
`len(target_loader) = ceil(4033/16) = 253` **unchanged**, so `total_step` is unaffected.

**Scope: now complete.** L1/L2 cover **all four** test sets (COD10K 2026, CAMO 250, CHAMELEON 76,
NC4K 4121) against Target, the authors' pool P1, and the full bank P2/P3. The sweep has already been
executed once on the updated dataset: the only hits are the 7 known COD10K↔Target duplicates. Gate 1
re-runs it after the bank is built, so the 13,341 new renders are covered too.

**One extra check the new layout requires — L6 selection-set disclosure:** assert and record that
`Val/CAMO` is byte-identical to `Test/CAMO` (250/250), and that CAMO is absent from the endpoint list.
This fails loudly if anyone later adds CAMO to the evaluation.

### Gate 2 — after each arm pool is assembled: `pool_report_{arm}_s{seed}.json`

| check | method | fails loudly if |
|---|---|---|
| P1 stem parity | `sorted(Image)` vs `sorted(GT)` compared stem-by-stem, reusing `preflight.py:325-342` | any index has different stems |
| P2 **exact count** | construct `SrcDataset(pool)` once and assert `len(ds) == N_expected` (**6824** for arm A, **8824** for B/C, read from that pool's manifest) | `filter_files` silently dropped anything |
| P3 size match | `Image.open(img).size == Image.open(gt).size` for every pair in the pool | any mismatch (the silent-drop cause) |
| P4 added-block integrity | the 1000 added stems are present in both dirs, and each maps to a manifest row | any missing or orphan |
| P5 no cross-arm bleed | pool path contains the arm+seed tag; manifest hash differs across arms | two arms resolve to the same path |
| P6 checkpoint isolation | `save_model` path contains arm+seed+iteration; directory empty at start | any pre-existing `.pth` |

**Filename scheme that makes P1 structurally true rather than lucky.** Added images are written as
`z_stagec_{arm}_s{seed}_{nnnnn}` with the **identical stem** in both `Image/` (`.jpg`) and `GT/`
(`.png`) — the same discipline `CLS.py:155-156` already uses. The `z_` prefix sorts strictly after
every existing stem family (numeric `0004`, `COD10K-*`, `camourflage_*`; byte order: digits `0x30` <
uppercase `0x41` < lowercase `0x63`), so the added block cannot interleave with existing entries and
the extension difference cannot flip order. Masks are copied from the bank **without resizing** —
`test.py:157` already emits each render at its mask's native resolution, verified 0/4447 size
mismatches — and P3 asserts it per pool rather than trusting it.

---

## §4. RISKS

| # | risk | how it produces a wrong answer | prevention in this plan |
|---|---|---|---|
| **R1** | **False null from the re-render ceiling** | Every B/C addition is the same 4447 foregrounds re-rendered (§0.3). If targeting only pays off with *new* foregrounds, we measure ≈0 and wrongly conclude targeting is worthless in general. | Cannot be eliminated — HKU-IS is exhausted. Mitigated by giving arm C the best-of-K render lever (§1.3). **Must be stated as a scope limit on any null**: the claim becomes "targeting does not help when the foreground pool is exhausted," not "targeting never helps." This is the single biggest interpretive risk. |
| **R2** | **False null from under-power** | A real 0.4σ effect goes undetected at N=13 and is reported as "no effect." | N=41 pre-registered (MDE 0.50σ); decision rule distinguishes *bounded-null* from *inconclusive*; achieved N and MDE reported with every null. |
| **R3** | **False positive from a pairing bug** | A mis-paired image/mask trains one arm on wrong labels; the arm looks worse and we read it as a targeting effect. | Gate 2: P1 stem parity, **P2 exact `len(SrcDataset)` == the manifest count**, P3 per-pair size match. The `z_` prefix makes parity structural. This is the failure mode most likely to fake a significant result. |
| **R4** | **Arm cross-contamination** | `CLS.py:16-17`'s derived path + `rmtree` lets one arm's pool or teacher overwrite another; arms silently share data. | P3/P4 patches (explicit `out_root`), P2 (per-arm/iteration checkpoints), Gate-2 P5/P6. Fork verified leak-free by audit §4(b). |
| **R5** | **Test contamination** | Pixel-exact test images in the training pool inflate all arms (and could differentially inflate one). | Gate 1 L1–L5, all-green required; the 7 known duplicates removed from `Target` before any run. |
| **R6** | **Arm-A exposure dilution read as an information effect** | A sees each image 23.1× vs 17.9× in B/C, so A−B mixes "more data" with "thinner exposure." | **Not removed** — it is intrinsic to adding data at a fixed step budget (§1.3). A→B is reported as a reference with the dilution stated; it is never claimed as an isolated information effect. B−C, the primary endpoint, is unaffected. |
| **R7** | **Multiplicity** | Four metrics × three contrasts ⇒ ~12 tests; one crosses p<0.05 by chance and is reported as the finding. | Sα/C−B pre-registered as the single primary; everything else secondary with Holm correction. |
| **R8** | **Mechanism invisible in the aggregate** | Funded clusters improve, unfunded degrade, aggregate is zero — we report "no effect" and miss a real mechanism. | Per-cluster ΔSα and ρ(budget, ΔSα) reported regardless of the aggregate outcome (§1.7). |
| **R9** | **σ measured on the wrong pool** | σ = 0.00356 came from 4447-image runs; arms use 8824 with ~27% real content, so the true σ may differ and the decision bar is miscalibrated. | The 41 arm-B and 41 arm-C runs *are* 8824-pool runs; σ will be re-estimated from them and the decision rule re-evaluated at the measured σ, with both reported. |
| **R10** | **`worker_init_fn` deviation** | Changing the augmentation stream makes results non-comparable to the published Table 1. | Applied identically to all arms, so it cannot bias B-vs-C. Absolute numbers reported as "this protocol," not as a Table 1 reproduction. |
| **R11** | **Checkpoint selection on a test set** (`Val/CAMO` ≡ `Test/CAMO`, 250/250) | Every arm's `Tea_epoch_best.pth` is chosen by CAMO-test score. If CAMO were reported as an endpoint, the number would be the selection criterion, not a result. | CAMO excluded from all endpoints (Gate-1 L6 asserts it). Applies identically to all arms so B-vs-C is unaffected; disclosed as an inherited protocol property, not fixed, to preserve Table 1 comparability. |
| **R12** | **`MyTest.py` crashes on the new layout** | `MyTest.py:51-52` points at the deleted `Dataset/Test/{Image,GT}`. A silent fallback or a hasty edit could evaluate the wrong set. | Patch P9 parameterizes `--test_root`; Gate 1 asserts per-set stem parity and image/GT counts before any evaluation. |

---

## §5. Assumptions I am least sure about, ranked

1. **That a re-render intervention can express targeting at all.** Arm C's whole lever is *which of
   4447 already-seen foregrounds to re-render, and which of K backgrounds to keep*. If targeting needs
   new foregrounds, N=41 buys a confident null about a mechanism we never actually tested. This is the
   assumption I would attack first.
2. ~~**That best-of-K meaningfully strengthens arm C.**~~ **NOW BEING MEASURED — Phase 0 step 4.**
   The audit measured the *foreground-selection* block shift at d≈0.10; whether best-of-K render
   selection adds on top was my assumption. It is now a hard gate before the 164-run commitment, so
   it is no longer an assumption the experiment rests on. If Phase 0 returns ≈0.10, we redirect
   rather than spend 77 GPU-h confirming a bound we could state analytically.
3. **That σ transfers from the 4447-pool runs to the 8824-pool arms.** Mitigated by R9 but unverified
   until the arm-A runs land; if σ is larger, the MDE degrades and N=41 may not reach 0.5σ.
4. **That ρ = 0.359 (arm correlation under a shared seed) holds.** It was estimated from n=3 vs n=4
   variance components — very thin. If ρ is lower, σ_d rises and N=41 under-delivers; if higher,
   pairing helps more than budgeted.
5. **That k=20 / native-518 is the right clustering operating point.** Chosen because it is the only
   setting where deficient-cluster reachability was non-trivial (20.62% held-out). It was never
   validated as the best *allocation* granularity — only as the most *reachable* one.
6. **That the fork is protocol-identical to a monolithic 2-iteration run.** Verified by code reading
   (audit §4(b)) but never verified empirically by running both and comparing distributions.

### The single thing most likely to make the result untrustworthy

**A silent image/mask mis-pairing or silent drop in an assembled arm pool** (R3). It is the only
failure mode that can manufacture a *significant* difference between arms rather than merely hide one —
`Dataloader.py:39-50` asserts length only and then drops size-mismatched pairs with no error, so an
arm could quietly train on 7200 images or on shifted labels and the run would complete normally and
report a confidently wrong number. Gate-2 P1/P2/P3 exist specifically for this, and P2 (constructing
`SrcDataset` and asserting the exact count) is the one check that cannot be satisfied by accident.

Second most likely was **spending 77 GPU-hours to bound an effect whose intervention we already
measured at d≈0.10** — a null that is real but uninformative because the lever was never strong
enough to test. That risk is now **retired by construction**: Phase 0 measures the lever strength and
gates the commitment, so the 164 runs only happen if there is something for them to detect.

What remains after that is R1 (the re-render ceiling), which Phase 0 *cannot* retire — it can tell us
how strong the lever is inside the re-render regime, but not whether targeting would work with new
foregrounds. Any null must carry that scope limit explicitly.

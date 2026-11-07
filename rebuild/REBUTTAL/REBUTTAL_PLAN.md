# REBUTTAL_PLAN.md — ICLR 2027 Submission 39230

*"Concentration, Not Uncertainty: Why Targeted Synthetic Data Doesn't Help Camouflaged Object Detection"* (arXiv 2610.09807 v1)

**Context.** All three reviews are 2/4. Two reviewers, dypE (soundness 2, conf 2) and RL5B (soundness 2, conf 3), called their concerns "minor or fixable". The goal is to move both to 3, and Caus (soundness 1) gets a complete answer. Discussion and PDF revision close **18 Nov 2026**; today is 7 Nov. This file is a plan: nothing has been trained, written to the paper, or committed. On approval, the file is copied verbatim to `rebuild/REBUTTAL/REBUTTAL_PLAN.md`. Every training run waits for a separate go-ahead, after its pre-registration has been committed.

**Two things to know before reading on:**
1. **The reviews are not in the repo.** Every concern below is quoted from the planning prompt, which paraphrases the reviews. **The OpenReview text has to be pasted into `rebuild/REBUTTAL/reviews/` before any reply is posted**, and each one-line restatement has to be checked against it.
2. **Phase 0 found three problems in the paper itself that we must correct whatever the reviewers say** (P1–P3 below). P1 is a narrow timing correction for OR only (FX and SE check out), but because it concerns the pre-registration record it gets fixed first.

---

## Phase 0 — verification results

All of this was computed read-only on 2026-11-07. "Ad hoc" means I computed it in this session and it is **not yet** in a committed script or an EXP block. WS1 and WS3 turn every ad hoc number into a logged one before anything cites it.

### (a) ABC power statement — **VERIFIED**
`rebuild/ABC/PREREGISTRATION.md:26`, first and only commit `065dac6` (2026-09-04):
> `Power statement  : resolves an effect ~half the paper's MT->Ours gap (0.0142) and no smaller.`

§2.9 of the same file: *"The repo's whole MT→Ours gap is 0.7030 → 0.7172 = **+0.0142** … The campaign resolves an effect **half the size of the paper's own headline improvement**"*, which is 0.0071. §2.8 notes that 0.0071 is also the prior 2σ bar (σ_prior = 0.003555). The frozen rule is a 2σ̂ rule. **It declares no equivalence margin.** 0.0071 is a sensitivity target and must never be called a margin.

### (b) Table 6 (`tab:tost`) from `rebuild/ABC/out/se/abc_metrics.csv` — **VERIFIED, all 16 rows reproduce exactly**
I recomputed with the paper's `welch_tost` logic (`rebuild/FinalPaper/make_results.py:119`). Primary C10−B: Δ +0.0024, CI [−0.0020, +0.0067], TOST p 0.1009, smallest δ 0.0059 ✓. C10−CSHUF: p 0.0189, smallest δ 0.0039 ✓. The other 14 rows match the table to 4 dp (full grid in WS1).
**Provenance gap (P2):** `grep "EXP DIAG"` finds no block in `results/REBUILD_LOG.txt`. Table 6, the boundary table (`diag_subgroups.json`) and the CHAMELEON geometric extension (`diag_chameleon_ext.json`) come from committed scripts and JSON, but **no EXP block logs them**. The AI-use statement says *"every number … is traceable to a log block"*. WS1 and WS3 add post-hoc EXP blocks for them.

### (c) Effective contrast — **MISMATCH (paper is wrong for C10−B)**
- Paper App. C (`AD-PCHG-250926_Final.tex:838-840`): *"only about 48% of injected images differ between any two arms, giving an effective contrast near 8.8%"*.
- Where the 48% comes from: the **C-vs-C** pairs (T2 block, log l.2359-2361), where 452–511 of 1000 differ. That gives 18.4% × ~48% ≈ 8.8%, which is right for the **direction contrasts** only.
- **B vs C10:** overlap per seed is 226 / 246 / 230 (logged, ABC #1, l.1279-1281, chance 224.9), and ad hoc for SE seeds 46–50: 234 / 238 / 209 / 245 / 239. Mean overlap over 8 seeds is 233.4, so **76.7% differ**.
- **Corrected effective contrast for C10−B: 18.4% × 76.7% ≈ 14.1%** (per-seed range 13.9–14.5%). Your ~14% estimate is confirmed. The direction contrasts stay at 8.3–9.4%.
- Seeds 46–50 overlaps exist only in this session. WS1 logs them.

### (d) Seed matching across arms — **VERIFIED with a caveat**
`MyTrain.py:280` calls `set_random_seed(opt.seed)` (random/numpy/torch/cuda) and sets cuDNN to deterministic, so the same `--seed` gives the same round-1 student/teacher initialisation in every arm (`abc_commands.txt`: identical CLI apart from the pool). Arm B's draw uses `numpy default_rng(700000+seed)` (SE #1, l.3051). **Caveat:** data order matches only in index space, because the pools differ. Round-2 initialisation depends on round-1 RNG consumption, which I have not verified to be data-independent. Pairing by seed is therefore a valid design, but **in practice it buys nothing**. The within-seed correlation of C10 and B on the primary cell is **r = −0.04** (ad hoc), so the paired CI comes out slightly *wider* than Welch.

### (e) Contamination audit pool — **VERIFIED, with one correction to the prompt**
- `Dataset/Target/Image` holds 4040 files: 3040 `COD10K-CAM-*` and 1000 `camourflage_*`. That is the standard supervised COD training split (COD10K-train camouflaged + CAMO-train), and `rebuild/common.py` declares the same.
- 50/76 = 41 Tier-A (D2R block, l.1844ff) + 9 Tier-B (paper App. `app:chamext` adjudication table).
- **44 COD10K-train partners = 40 Tier-A (D2R `partner_images_in_cod10k_train = 40/41`) + 4 Tier-B (animal-22/66/73/74).** VERIFIED. The other **6** partners are in CAMO-train: 1 Tier-A + 5 Tier-B (I checked all 5 are in `Target/Image` and none in `Val`).
- **Correction to the prompt:** the S2R-COD target pool *as this repo runs it* (4040) contains **all 50** CHAMELEON partners, not 44. The paper's footnote uses 44 because S2R-COD's paper describes its target as COD10K-train only. WS3 reports both rows.
- **3 byte-identical CHAMELEON↔CAMO-250 files: VERIFIED ad hoc** (sha256 over `Dataset/Test/CHAMELEON/Imgs` vs `Dataset/Val/CAMO/Imgs`: 3; vs `Target/Image`: 0). The paper says only that *one* of the 10 clean images is byte-identical to a val image, so WS3 identifies which tier the other two fall in.
- **Tier-B count discrepancy:** `diag_chameleon_ext.json` headline says *"41 + 10 = 51/76"*. The paper says 50 because the residual adjudication rejects animal-7. **I found no committed artifact for that adjudication step.** WS3 must commit the script and output, or the paper's number goes back to "≥ 50, adjudication not logged".
- **"Seen with labels"** is precise only this way: under the standard supervised protocol, the *partner* image is trained on with *its own* mask. The CHAMELEON GT mask itself is never seen.

### (f) GT masks for COD10K-train / CAMO-train — **NOT ON DISK; obtainable**
There is no `GT` directory for `Dataset/Target`, and `rebuild/D2_nc4k/cache/cod10k_train` holds images only. The masks are public: the COD10K-v3 release (Train/GT_Object) and the CAMO-V.1.0 train GT, or the standard 4040 "TrainDataset" bundle linked from the SINet-v2 repo. **Fetching them is an outward action that needs your approval.** Gate: after download, the sha256 of every image must equal `Target/Image`, or the anchor isn't protocol-matched. `MyTrain.py --method source_only` already supports training on a labelled source root (single round), so no new trainer is needed.

### (g) Wall clock and throughput — **VERIFIED** (`abc_runs.csv` ×4, `SE_RESULTS.md:71-79`)
| arch | ABC mean | SE mean | OR mean |
|---|---|---|---|
| SINet | 106.9 min | 106.3 (range 105.3–106.5) | 108.8 |
| SINet-v2 | 127.0 min | 123.4 (121.2–122.7 for new runs) | 125.2 |

Every campaign ran **one run per GPU, two concurrent** (`abc_train.py:220`). Two runs per GPU was never measured, so I don't plan on it. That gives **SINet ≈ 27 runs/day, SINet-v2 ≈ 23/day, and ~22/day for planning** (10% margin for scoring and inference). GPUs are idle right now (0% util).

### (h) ICLR 2027 Author Guide (iclr.cc/Conferences/2027/AuthorGuidelines) — **VERIFIED except the comment limit**
- Page limit during discussion: **10 pages**, *"strictly enforced"*. Submitted main text is 9 pages, so **we have one page**.
- *"Authors can also revise their paper until the end of the public discussion period (Nov 18)."* A pdfdiff is shown, and *"reviewers and area chairs are not required to look at every revision"*, so batch the changes into two revisions.
- Title: *"No changes to title are permitted after the submission deadline until the end of the discussion period."* (an FAQ line conflicts with this) → **no title change**. The abstract may be revised.
- Comments: *"There is a word limit for each comment, but there is no limit on the number of comments."* **The numeric limit is UNVERIFIED.** Every draft below is kept to ≤ 4,500 characters (under OpenReview's usual 5,000), and splitting is allowed.
- An AI-use statement is required.

### (i) Literature numbers
| Method | COD10K Sα | NC4K Sα | Backbone | Labels | Status |
|---|---|---|---|---|---|
| RISE (ICCV'25) w/o SAM | 0.763 | 0.805 | DINOv2 ViT-L/14 | none (unsupervised) | **VERIFIED**, arXiv 2510.18437 Tab. 1 |
| RISE w/ SAM | 0.790 | 0.825 | DINOv2 + SAM ViT-H (box prompts from own pseudo-masks) | none | **VERIFIED**, same |
| UCOD-DPL (CVPR'25) DINOv1 | 0.727 | 0.761 | DINOv1 | none | VERIFIED, arXiv 2506.07087 Tab. 1 |
| UCOD-DPL DINOv2 | 0.834 | 0.850 | DINOv2 | none | VERIFIED, same |
| **UCOD-DPL "0.709 / ~0.754"** | — | — | — | — | **MISMATCH**: not in UCOD-DPL Tab. 1 (closest is .707 in a Tab. 3 ablation). Do not use. |
| SINet (supervised) | 0.771 | 0.808 | ResNet-50 | full masks, 4040 | COD10K: SINet CVPR'20. **NC4K: secondary source only** (UCOD-DPL Tab. 1), since NC4K postdates SINet |
| SINet-v2 (supervised) | 0.815 | 0.847 | Res2Net-50 | full masks, 4040 | as reported in UCOD-DPL Tab. 1; **confirm in the TPAMI'21 PDF before use** |
| S2R-COD S2C, SINet: SO / MT / Ours | 0.6418 / 0.6984 / 0.7136 | n/a* | ResNet-50 | synthetic masks + unlabelled real | **VERIFIED**, arXiv 2507.18911v3 Tab. 1 |
| S2R-COD S2C, SINet-v2: SO / MT / Ours | 0.6466 / 0.6485 / 0.6845 | n/a* | Res2Net-50 | same | **VERIFIED**, same |

\*S2R-COD's NC4K table uses a *different* source mix (CAMO + CHAM. + COD10K → NC4K), so it is not comparable to our NC4K column. The table caption has to say so.
The literature numbers were extracted through an HTML-to-text tool. **Before the table goes in the PDF, a human checks every literature cell against the PDF.**

### Problems found in our own paper (must fix in revision 1)
- **P1 — pre-registration commit record (re-audited 2026-11-07; the first pass was wrong).** The three files were committed together in **`a79886a`, 2026-09-18 11:48:26** ("Pre-register EXP OR, FX and SE…"). At 12:05–12:06 a reset took that commit off the branch, and the same files were committed again in `28cfd84` (2026-09-19). FX and SE are byte-identical between the two commits. OR gained only an append-only Addendum A1, dated 2026-09-19, with §OR.0/§OR.1 unchanged. **`a79886a` was never pushed and exists only in the local reflog.**
  - **FX:** written 11:03:17 and never modified after; committed 11:48; first run 18:23. **Committed before its runs.** ✔
  - **SE:** written 11:41–11:46; committed 11:48; first new run 2026-09-20 03:50. **Committed before its runs.** ✔ The paper's hash "b755aa9" is wrong: that is the 09-13 base commit the log blocks record.
  - **OR:** written 10:44:13 (filesystem birth time); first runs launched 10:46:09; committed 11:48:26, about 62 min into the first two runs. No OR endpoint score existed until 18:23 (EXP OR scoring block). **The rule was committed before any OR number existed, but not before OR training began.** Git can't show what the file said between 10:44 and 11:47:56, when its blob was staged. The decision rule itself is the ABC 2σ̂ / sign rule frozen at `065dac6`, applied to the new arm.
  - **Fix:** correct the appendix sentence to these facts, cite `a79886a`, and **preserve `a79886a` with a pushed tag before the reflog expires** (needs your OK).
- **P2 — DIAG numbers have no EXP block** (see b). Append post-hoc EXP DIAG blocks dated 2026-11, re-emitted by the committed scripts, and fix the AI-use sentence until those blocks exist.
- **P3 — the effective-contrast sentence** (see c).

### A post-hoc finding the paired analysis brings up (report it, don't bury it)
On SINet, **CINV−B** has Welch 95% CI **[+0.0015, +0.0074]** on COD10K (7/8 seeds positive) and [+0.0006, +0.0062] on NC4K. CINV−B is not one of SE's frozen gaps. Its Δ of +0.0045 is under SE's 2σ̂ bar of 0.0069, so it decides nothing. It is consistent with the thesis: CINV has C10's concentrated shape, and concentration rather than aim is what moves things. But it is unadjusted, one of 24 comparisons, and SINet only. CSHUF−CINV, a direction contrast, also excludes zero on SINet: paired CI [−0.0044, −0.0004] on COD10K, Welch [−0.0064, −0.0011] on NC4K (already in Table 6), 8/8 there. **"Direction makes no detectable difference" is therefore too strong. The right sentence is: "aiming by the uncertainty score buys nothing detectable; on SINet, reversing it does slightly better than shuffling it."**

---

## Workstream table

| WS | Answers | Method | Trains? | Runs | GPU-h | Earliest result | Gate |
|---|---|---|---|---|---|---|---|
| **WS1** Statistics | all three, shared C10−B objection; dypE paired request; dypE "meaningful" | 16+8 contrasts × {Welch, paired} × δ∈{0.005, 0.0071}; smallest δ; MDE; overlap logging; **8-seed boundary re-score (post-hoc)** | no | 0 | 0 (CPU) | 9 Nov | none |
| **WS2** Claims/scope | RL5B c2, c4; dypE c2; Caus scope | before/after diffs; P1–P3 corrections | no | 0 | 0 | 11 Nov | WS1 numbers logged |
| **WS3** Contamination by protocol | dypE Q3 | 3-row table + EXP block; commit the Tier-B adjudication | no | 0 | 0 | 10 Nov | none |
| **WS4** Anchors | RL5B c3 | supervised SINet/SINet-v2 on real 4040 ×3 seeds (descriptive); literature table; existing MT/A0/C10 | yes | 6 | ≤ 8 (UNVERIFIED single-round time) | 10 Nov | (f) download approved + sha256 match |
| **WS4b** Source-only anchor | RL5B c3 | `--method source_only` on HKU-IS synthetic ×2 arch ×3 | yes | 6 | ≤ 8 | 10 Nov | optional, only if WS4 is gated out or you approve the extra 6 |
| **WS5′** Equivalence extension | all three | **B vs C10, SINet, 32 fresh seeds/arm**, standalone, δ = 0.005 | yes | 64 | 113 | 12–13 Nov | pre-reg committed by 9 Nov; launch by 10 Nov 06:00 or skip |
| **WS6** Different-shape oracles | Caus Q1 | CORACLE-PROP, CORACLE-TOP(k = 5) × 2 arch × 3 seeds vs existing B | yes | 12 | 23 | 10 Nov | pre-reg committed before run 1 |
| **WS7** New foregrounds | dypE Q2, RL5B c4 | DUTS-TR overlap sweep → 2000 renders → B_new vs C10_new, SINet ×3 | yes | 6 (+ renders) | 11 + render (UNVERIFIED) | 13–14 Nov | go/no-go 11 Nov: sweep clean, render throughput measured, WS1–6 on track |
| **WS8** Modern backbone | Caus Q2, RL5B (partly) | assessment only | no | 0 | 0 | — | **recommend: do not run** |

**Why WS5 changed (gate result).** The prompt's gate was 16 seeds per arm. I simulated Welch TOST at δ = 0.005 (4000 draws) using the eight-seed spreads (sd B 0.00251, C10 0.00489). **At the observed Δ = +0.0024, 16 seeds/arm gives 58% power. Twenty-four gives 73%, and 32 gives 83%.** If the true Δ is 0, 16 seeds already gives 93%. The 16-seed design fails its own gate. The spec also counted "16 seeds" by pooling SE's 8, which adds seeds to a committed campaign. My recommendation is WS5′: **a standalone campaign, 32 new seeds {51…82}, only B and C10, only SINet.** That is 64 runs, ~57 h of wall clock. CSHUF/CINV are left out: their primary-cell equivalence already passes, and the open question is C10−B. **If you prefer the original 4-arm, 16-seed design, it is underpowered at the observed gap, and the pre-registration must say so.**

**WS8 assessment.** Porting a PVTv2- or DINOv2-based COD model means student/teacher EMA, ES loss on a single-channel output, the CLS step between rounds, a `MyTest.py` path and preflight. The SegMaR port (`Explanations/SEGMAR.md`, an 85 KB post-mortem) is the honest reference for that effort. Realistically it is 3–5 days of porting and debugging before any run, so **it can't be scored by 16 Nov**. SegMaR itself is already in `MyTrain.py`, but it is ResNet-50 (CVPR'22, not modern). Its reproduction (0.6973 vs paper 0.6832) lives only in the operational layer, and its run time is unmeasured. **It is not offered as the modern backbone.** Caus gets a written answer instead.

---

## Compute budget (measured throughput, 1 run/GPU, 2 GPUs)

Window: **9 Nov 08:00 → 15 Nov 20:00 = 156 h wall = 312 GPU-h.**

| Slot (wall) | Work | GPU-h |
|---|---|---|
| 9 Nov 08:00 → ~10 Nov 00:00 | WS6 (12) + WS4 (6) *or* WS4b (6) | ~31 |
| 10 Nov 00:00 → ~12 Nov 09:00 | WS5′ 64 SINet runs (64 × 106 min / 2) | 113 |
| 12 Nov 09:00 → ~13 Nov 06:00 | WS7 renders (measure the first 50; abort if the 2000 renders would take > 12 h) + 6 SINet runs | ~11 + render |
| 13–15 Nov | scoring, buffer for one SE-style interruption (~3.5 GPU-h last time) | — |
| **Total committed** | | **~155–165 of 312 (≈ 52%)** |

If WS5′ misses its 10 Nov 06:00 launch, it gets dropped. Nothing else is moved to make room for it.

---

## WS1 — statistics package (no training; first draft 10 Nov)

**Script:** `rebuild/REBUTTAL/ws1_stats.py`, reusing `welch_tost` (`rebuild/FinalPaper/make_results.py:119`) and the CSV reader pattern of `figs/make_tost_table.py`. It reads only `rebuild/ABC/out/se/abc_metrics.csv`, `abc_verdict.json` and the `abc_stems_*.txt` files, appends **one `EXP REBUTTAL_STATS` block** marked POST-HOC, and writes `rebuild/REBUTTAL/out/ws1_*.json|csv`.

Emitted:
1. Per-seed differences for every contrast (these exist in `abc_verdict.json`; it re-emits them).
2. Welch **and** paired: mean, 95% CI, TOST p at δ = 0.005 and at 0.0071, smallest δ, within-seed r.
3. MDE at 80% power, two-sided α = .05, n = 8/arm. Ad hoc: **SINet COD10K 0.0059, SINet NC4K 0.0051, SINet-v2 COD10K 0.0077, SINet-v2 NC4K 0.0081**.
4. Seeds-per-arm power curve for the WS5′ pre-registration.
5. B-vs-C overlap at all 8 seeds, and the corrected effective contrast.
6. **Boundary metrics at 8 seeds:** run `diag_boundary.py`'s scorer over `Result/ABC/*_s4[6-9]*`, `*_s50*` (predictions exist; 100 run dirs). This tests whether the SINet-only boundary result holds at n = 8. It is post-hoc and gets reported whatever it shows. If it weakens, WS2's §3.2 diff says so.

**Ad hoc preview (exact values come from the script):**

| Cell | Contrast | Welch CI | p(.005) | p(.0071) | δ_min | Paired CI | p(.005) | δ_min |
|---|---|---|---|---|---|---|---|---|
| SINet·COD10K | C10−B | [−.0020, +.0067] | .101 | **.017** | .0059 | [−.0023, +.0070] | .111 | .0061 |
| | C10−CSHUF | [−.0041, +.0047] | **.019** | **.003** | .0039 | [−.0050, +.0056] | **.037** | .0046 |
| | C10−CINV | [−.0066, +.0023] | .091 | **.015** | .0057 | [−.0076, +.0034] | .126 | .0065 |
| | CSHUF−CINV | [−.0055, +.0007] | **.049** | **.003** | .0050 | [−.0044, −.0004] | **.010** | .0040 |
| SINet·NC4K | C10−B | [−.0033, +.0040] | **.008** | **.001** | .0033 | [−.0038, +.0045] | **.017** | .0037 |
| SINet-v2·COD10K | C10−B | [−.0067, +.0045] | .076 | **.018** | .0057 | [−.0081, +.0059] | .114 | .0067 |
| SINet-v2·NC4K | C10−B | [−.0068, +.0049] | .079 | **.021** | .0057 | [−.0077, +.0058] | .100 | .0064 |

**Equivalence passes (Welch / paired): 5/16 and 6/16 at δ = 0.005; 13/16 and 13/16 at δ = 0.0071.** All four C10−B cells pass at 0.0071 under both tests. The failures at 0.0071 are SINet-v2 C10−CSHUF and C10−CINV, plus SINet-v2 NC4K C10−CINV (paired).

**New main-text table (≈ ⅓ page): "Absence of evidence vs evidence of absence".** One row per C10−B / C10−CSHUF cell. Columns: "detected? (2σ̂ rule)", "equivalent at 0.005?", "equivalent at 0.0071?", "δ_min". The caption carries this sentence: *"0.0071 is half the method's own gain and was the pre-registered sensitivity target, not a declared equivalence margin. All tests here are post-hoc."*

**Drafted sentence:** *"On the primary cell we rule out a benefit of targeted over random allocation larger than +0.0067 Sα (95% CI; +0.0059 at the one-sided 5% level used by TOST). Smaller benefits, including the 0.005 the reviewers propose, remain possible."*

**What "meaningful" means (dypE).** We answer with anchors internal to the protocol, because no outside anchor is verified. The method's own gain over mean teacher is 0.0142 in our reproduction and 0.0152 in S2R-COD's Tab. 1 (0.6984 → 0.7136). Our positive control detects 0.0197. Seed-to-seed sd on the primary cell is 0.0025–0.0049. Half the method's gain, 0.0071, is the smallest effect that changes which method a practitioner picks. We state it as our judgment and give the δ_min column so readers can apply their own.

---

## WS2 — claim and scope recalibration (text diffs; 11 Nov)

Every diff goes against `AD-PCHG-250926_Final.tex` (and the compiled copy in `rebuild/FinalPaper/AD-PCH-230926/`). Each line below is the edit to make; the exact LaTeX lands in `rebuild/REBUTTAL/diffs/`.

| # | Location | Before (verbatim fragment) | After |
|---|---|---|---|
| D1 | Abstract | "the difference is explained by concentrating the generation budget rather than by where uncertainty is concentrated, as every concentration rule we test reproduces the effect and, on boundary accuracy, so does aiming at the clusters the model was most certain about." | "…the **separation between targeted and random training sets** is explained by concentrating the budget, not by where it points. On trained accuracy, we find no evidence that the direction of the signal helps, and we bound any benefit of targeting over random at +0.0067 Sα; a post-hoc boundary-metric analysis on one of two architectures is consistent with concentration." |
| D2 | Abstract, last sentence | "…budget concentration, not uncertainty-based targeting, accounts for the observed training-set effects." | "…accounts for the observed **training-set separation**, within a LAKE-RED, background-only, fixed-foreground setting on the SINet family." |
| D3 | Contribution 2 | "A bounded null on the direction, defended by five independent controls" | "A bounded null: no evidence that targeting beats random (benefits above +0.0067 Sα ruled out on the primary cell; equivalence at ±0.005 holds for the same-shape direction contrast but **not** for targeted-vs-random)…" |
| D4 | §3.2 opener (l.328-332) | "trained accuracy at eight seeds is consistent with it, and the one family of metrics…supports it" | "Concentration explains the separation; that is established. Whether it explains downstream accuracy is not: the boundary-metric support is post-hoc, holds on SINet and not SINet-v2, and [8-seed result from WS1.6]." |
| D5 | §3.2 TOST para (l.355-358) | "…targeting against its own shuffle is equivalent (p = 0.019) and targeting against random is not (p = 0.101)." | add: "C10−B mixes concentration and direction, so a small concentration effect could sit precisely there; it is the one gap we cannot close (Table new)." + the CINV−B and CSHUF−CINV post-hoc disclosure. |
| D6 | §3.2 "direction" | "the absence of an ordering… nothing is paid" | keep, and add "on SINet, reversal does slightly better than shuffling (CSHUF−CINV CI excludes 0 on both endpoints, unadjusted, post-hoc)". |
| D7 | §4 Discussion | — | **new scope paragraph (~8 lines):** LAKE-RED; fixed HKU-IS foreground pool of 4447; background-only variation; the S2R-COD protocol (synthetic source + unlabelled 4040 target); SINet / SINet-v2 (ResNet-50 / Res2Net-50). The null concerns the **allocation layer inside that protocol**. It says nothing about foreground-varying generators or modern backbones (names RealCamo, CamDiff and PVTv2/DINOv2 as untested). |
| D8 | App. C l.838-840 | "only about 48% of injected images differ between any two arms, giving an effective contrast near 8.8%" | "about 77% of injected images differ between C10 and B (effective contrast ≈ 14.1% of the pool), and about 48% between the C-family arms (≈ 8.8%)" — **P3** |
| D9 | App. method l.732-737 | "The oracle and optimization schedule campaigns carry their own pre-registrations, each committed before that campaign's first training run." / "the seed expansion's at b755aa9" | "The oracle, schedule and seed-expansion pre-registrations were committed together at `a79886a` (2026-09-18 11:48). The schedule's and seed expansion's runs began afterwards. The oracle's runs had launched 62 minutes earlier, from a file written two minutes before launch. Its rule was committed before any oracle score existed, but git records the text only from the commit." — **P1** |
| D10 | AI-use statement | "every number is emitted by a committed script and is traceable to a log block" | keep only once the P2 EXP blocks exist. Otherwise: "…traceable to a log block or, for the post-hoc diagnostics of App. D, to a committed script output." Plus the WS-AI addendum below. |
| D11 | New §3.1 table + literature/anchor table (App., with one main-text sentence) | — | WS1 table and WS4 table |

**Page budget:** one new page (9 → 10). WS1 table ≈ ⅓ page, scope paragraph ≈ ¼, D4–D6 ≈ ¼, WS6 result (2 lines + appendix). WS3, WS4, WS7 and the literature go in the appendix with a one-sentence pointer each.

---

## WS3 — contamination by protocol (10 Nov)

The script `rebuild/REBUTTAL/ws3_contamination.py` re-derives the figures from `d2r_*` and `diag_chameleon_ext.json`, runs the sha256 check against CAMO-250, and **commits the residual adjudication** (the animal-7 rejection) as an artifact. It appends `EXP REBUTTAL_CONTAM`.

| Protocol | How CHAMELEON enters | Count (floor) | Labels seen? |
|---|---|---|---|
| Supervised, standard split (COD10K-train 3040 + CAMO-train 1000) | partner image in the labelled training set | **50/76** (44 COD10K-train + 6 CAMO-train); 16 unchecked | partner's own mask, yes; CHAMELEON GT, no |
| Unlabelled target adaptation, S2R-COD as described (COD10K-train target) | partner in the unlabelled target pool | **44/76** | no |
| Same, as the released data runs it (4040 target) | same | **50/76** | no |
| Checkpoint selection (CAMO-250) | file byte-identical to a val image | **3/76** (tiers TBD by WS3) | val GT used for selection only |

Framing, consistent with the paper: **non-independence, not inflation.** The measured difficulty percentiles 0.448–0.559 show no score advantage. None of our endpoints uses CHAMELEON.

---

## Pre-registration drafts (committed before run 1; frozen after any number exists)

All three inherit `abc_build_pools.py` / `abc_train.py` / `abc_evaluate.py` with a new `--tag`, the E0 manifest assertion, the `verify_run` gate and the scorer. They add no gate that ABC/T2/OR/FX/SE lacked, and they re-decide nothing.

### `rebuild/REBUTTAL/PREREGISTRATION_WS4.md` — descriptive anchors
- **Arms:** SUP = `MyTrain.py --method source_only --source_root <real 4040 Imgs+GT>`, single round, native epochs (SINet 40, SINet-v2 100). Optional SO = the same on HKU-IS synthetic 4447.
- **Seeds:** {42, 43, 45}. **Endpoints:** COD10K-test Sα (primary), NC4K; MAE/Fβw/Eφ reported. Checkpoint: CAMO-250 selection, as every arm uses.
- **Decision rule: none.** These are descriptive anchors. They will be reported whatever they show, including if SUP lands below the published 0.771 / 0.815 (we report the gap and do not tune).
- **Pre-condition:** downloaded images hash-match `Target/Image` 4040/4040, or WS4 stops.

### `rebuild/REBUTTAL/PREREGISTRATION_WS6.md` — different-shape oracles (diagnostic, uses test labels)
- **Declaration:** both arms allocate by **true endpoint error** (`b1_cluster_es_dinoL518.csv:test_one_minus_sa`, sha256 `1ff27cd1…f693f8`, as in OR). They are diagnostics and never a method, under OR §0's three commitments.
- **CORACLE-PROP:** Eq. 2 (softmax over z-scored cluster values at τ = 1.0) applied to true per-cluster error, so it has its own shape. Quotas are filled by the same nearest-centroid rule. Report entropy, TV-to-uniform, max share and clusters funded beside C10's.
- **CORACLE-TOP:** the whole budget of 1000 goes to the **k = 5** truly worst clusters, split in proportion to their target-cluster sizes and capped at supply. Overflow goes to cluster 6, then 7, and so on, and gets reported. (k = 5 is fixed now. It is the smallest k at which supply covers 1000 renders; **WS6 preflight verifies that and logs it before training; if supply is short, k rises to the smallest feasible value, which is decided in preflight and logged, never after a number exists.**) Clusters with n_test = 1 are excluded from "worst".
- **Comparator:** the existing SE arm B at seeds {42, 43, 45} (not re-trained). Seeds {42, 43, 45}; both architectures.
- **Rule:** the frozen ABC form. REAL EFFECT iff Δ(X−B) > 2σ̂ and sign 3/3, where σ̂ is pooled over {B, X} at those seeds. WITHIN NOISE iff |Δ| ≤ 2σ̂. INCONCLUSIVE gets reported as-is, with no seeds added.
- **Reporting:** both outcomes are pre-written. A null means "no score of any shape, even a perfect one, moves the endpoint in this pipeline". An effect means "a correct score with the right shape can help, so the binding constraint was the acquisition signal". Either way it goes in the main text in 2 lines.

### `rebuild/REBUTTAL/PREREGISTRATION_WS5.md` — equivalence extension (standalone)
- **Arms:** B, C10. **Arch:** SINet. **Seeds:** {51…82}, 32 per arm, disjoint from every committed campaign. **Never pooled with SE**, and SE's verdicts stand untouched.
- **Primary test:** Welch TOST, δ = 0.005, α = 0.05, on COD10K-test Sα, Tea_epoch_best. Secondary: NC4K; paired-by-seed TOST.
- **Power statement:** 83% at a true Δ of +0.0024 and ~100% at Δ = 0, from SE spreads (WS1 output 4).
- **Outcomes:** EQUIVALENT (90% CI within ±0.005); NOT EQUIVALENT, BENEFIT (CI lower > 0); NOT EQUIVALENT, UNRESOLVED. All three wordings are pre-written and the revision will use whichever occurs.
- **Stopping:** all 64 runs or none get reported. A run that fails `verify_run` is re-run under the same seed and logged as a discard. No interim look.

### `rebuild/REBUTTAL/PREREGISTRATION_WS7.md` — foreground diversity (only on a go)
- **Step 0, before any render:** run `detect_contamination.py` (Tier A) plus the Tier-B keypoint stage on DUTS-TR (10,553) against COD10K-test, NC4K, CAMO-250, CHAMELEON and `Target/Image`. Any hit is removed and logged.
- **Pool:** 2000 DUTS-TR foregrounds rendered through LAKE-RED with the E0 pipeline, unioned with the 4447 existing renders. **B_new** = uniform 1000 from the union (rng 800000+seed). **C10_new** = the same allocation rule and the same cluster scores over the union.
- SINet, seeds {42, 43, 45}; the frozen ABC rule. Scope sentence, fixed now: *"foreground diversity under a background-only generator; not a generator replication."*

---

## Response drafts

Written in the house style: intuition first, and we own the result. Each draft comes in under ~4,500 characters. `[§x / Tab. y]` marks a location in revision 1. Bracketed placeholders get filled from logged results only.

### General comment (to all reviewers)
> Thank you all for close, careful reviews. Three concerns are shared, and we have revised the paper around them.
>
> **1. "No evidence of benefit" vs "no meaningful effect."** You are right, and the revision now says so in the abstract and §3.1. The targeted-vs-random gap on the primary cell, +0.0024 [−0.0020, +0.0067], does not pass equivalence at ±0.005 (TOST p = 0.10). We now state the result as what it is: we rule out benefits larger than +0.0067 Sα, and smaller ones remain possible. A new table [Tab. N] separates "failed to detect" from "evidence of equivalence" for every comparison, at two margins: the reviewers' 0.005, and 0.0071, half the method's own gain over mean teacher, which was our pre-registered sensitivity target and not a declared margin. At 0.0071, all four targeted-vs-random cells pass. At 0.005 the primary cell does not. The same-shape direction contrast (targeted vs its own shuffle) does pass at ±0.005 on the primary cell (p = 0.019). That asymmetry is informative: C10−B mixes concentration with direction, so it is where a small concentration effect would sit. All of these tests are post-hoc and labelled that way. [If WS5′ lands: a separate, pre-registered 64-run campaign at 32 seeds/arm gives … reported as pre-written whatever it showed.]
>
> **2. Concentration explains the training set, not (yet) the accuracy.** Also right. We split the claim in two: concentration explains the distributional separation (established), and on trained accuracy the direction of the signal buys nothing detectable. The boundary-metric support is post-hoc and holds on SINet but not SINet-v2. [8-seed re-score: …] [§3.2].
>
> **3. Scope.** There is a new scope paragraph [§4]: LAKE-RED, a fixed foreground pool, background-only variation, the S2R-COD protocol, and the SINet family. The null concerns the allocation layer inside that protocol. [WS7 if run.]
>
> **A correction we owe you.** Appendix C gave the effective contrast as ≈8.8%. That figure belongs to pairs of C-family arms. Between C10 and random, ~77% of injected images differ, which makes it ≈14.1%. While re-checking provenance, we also tightened the pre-registration record [App. B]: the oracle campaign's rule was committed after its runs launched, though before any of its scores existed, and the appendix now gives the exact commit and times. Every new number comes with a log block.

### Reply to dypE
> **Paired analysis at matched seeds.** Done [Tab. N]. Seeds match initialisation across arms, but the within-seed correlation of C10 and B is ≈0 (r = −0.04), so pairing doesn't narrow the interval: paired CI [−0.0023, +0.0070], TOST p = 0.11 at ±0.005. We report both.
>
> **What is meaningful for COD?** We anchor on the protocol itself. The method's gain over mean teacher is 0.0142 in our reproduction (0.0152 in S2R-COD's Table 1), and seed-to-seed sd is 0.0025–0.0049. We treat half that gain, 0.0071, as the smallest effect that would change a practitioner's choice, and every C10−B cell is equivalent at that margin. The δ_min column lets readers apply a stricter threshold. At 0.005, the primary cell is not equivalent.
>
> **Does concentration explain accuracy?** Not established, and we no longer say it is [§3.2]. [8-seed boundary result.]
>
> **More diverse foregrounds / larger differences?** [If WS7 ran: B_new vs C10_new with 2000 new, overlap-swept foregrounds → result, App. X.] Otherwise this is named as untested in the scope paragraph. On the size of the training-set difference: the C10−B effective contrast is ≈14% of the pool, not the 8.8% we wrote (corrected).
>
> **Contamination, by protocol** [App. Y, new table]: (i) standard supervised training: 50/76 CHAMELEON images have their photograph, with its own mask, in the standard 4040-image training split (44 in COD10K-train). (ii) Unlabelled target adaptation: the same images sit unlabelled in the target pool, 44 under S2R-COD's stated COD10K-train target and 50 under the 4040-image pool as released. (iii) Checkpoint selection: 3 CHAMELEON files are byte-identical to CAMO-250 images. In every case the problem is non-independence, not a measured score inflation, and none of our endpoints uses CHAMELEON.

### Reply to RL5B
> **Absolute scores below RISE and supervised SINet-v2.** That's right, and a new anchor table [App. Z] explains why. RISE uses a DINOv2 ViT-L/14 extractor (0.763 COD10K Sα; 0.790 with SAM). Supervised SINet-v2 trains on real masks (0.815). Our arms are ResNet-50/Res2Net-50 SINet models trained under the S2R-COD protocol with synthetic masks. Inside that protocol, our C10 (0.7175) and B (0.7151) sit at or above S2R-COD's own published result (0.7136), and our mean teacher (0.6988) reproduces theirs (0.6984). [WS4: same-code supervised upper bound on real masks, 3 seeds: SINet …, SINet-v2 ….] The level is inherited from the protocol and backbone. The null concerns which 1000 synthetic images to add within it.
>
> **Concentration ≠ downstream.** Agreed. The claim is split [§3.2, abstract]. The boundary result is post-hoc and SINet-only. [8-seed update.]
>
> **Scope.** New paragraph [§4]. [WS7.]
>
> **Equivalence.** See the general comment and [Tab. N].

### Reply to Caus
> **"Only a sanity check."** We agree the separation result alone can't carry the paper. It earns its place because it shows the comparison a random baseline can't make: holding the budget's shape fixed while moving its aim.
>
> **An oracle with a different shape.** Fair, since our oracle reused C10's shape. We trained two more [§3.1, App. W], both deliberately using test-set error as diagnostics: CORACLE-PROP, which allocates in proportion to true per-cluster error through the same rule and so has its own shape, and CORACLE-TOP, which puts the whole budget on the 5 truly worst clusters. Results: [pre-written wording for whichever occurred], with shape statistics.
>
> **A modern backbone and a foreground-varying generator.** We could not do either responsibly in this window. Porting a PVTv2/DINOv2 COD model into the two-round teacher-student loop with the ES loss and CLS step is several days before the first valid run, and a foreground-varying generator such as RealCamo or CamDiff is a new environment. We say so plainly and scope the claims to LAKE-RED and the SINet family [§4]. [If WS7 ran: we did vary foreground content within LAKE-RED; result in App. X.]

---

## AI-use statement — what needs updating
New code (`ws1_stats.py`, `ws3_contamination.py`, the WS4/WS6/WS7 pool builders, the PROP/TOP allocation code) and the draft rebuttal prose are LLM-assisted. Add one sentence: *"During the discussion period, generative AI tools were also used to draft the post-hoc statistics and contamination scripts, the allocation code for the additional oracle arms, and the response text; all outputs are committed and every new number is emitted by a committed script into a dated log block."* Apply D10.

---

## Schedule
- **8 Nov:** paste the reviews. WS1 script and EXP block. WS3 script and EXP block. Commit the WS4/WS5′/WS6 pre-registrations. Get your approval for the (f) download.
- **9 Nov 08:00:** launch WS6 and WS4 (or WS4b). WS1 draft table done.
- **10 Nov:** WS5′ launch (hard gate 06:00). WS2 diffs. WS7 overlap sweep and render-throughput probe.
- **11 Nov:** WS7 go/no-go. Build revision 1 (WS1–WS3, P1–P3, WS4/WS6 if scored).
- **12 Nov:** post the general comment and the three replies, and upload revision 1.
- **13–15 Nov:** WS5′/WS7 land → revision 2 (final upload by 16 Nov).
- **17 Nov:** short follow-ups to any reviewer who hasn't replied.

## Verification
- The `ws1_stats.py` output reproduces Table 6's 16 Welch rows exactly (assertion in the script) before it emits anything new.
- Every number in a response draft is grep-able in `results/REBUILD_LOG.txt` (an existing block or the new REBUTTAL_* blocks) before posting. A pre-post checklist script greps each listed value.
- Revision PDF: main text ≤ 10 pages (check `main.log`), title unchanged, pdfdiff reviewed by hand.

---

## (a) Top three changes most likely to move dypE and RL5B
1. **The "failed to detect vs equivalent" table, with the drafted sentence.** It concedes the exact point all three raised and shows the asymmetry (direction contrast equivalent, C10−B not) that makes the concession informative instead of fatal. dypE asked for this almost word for word.
2. **Splitting the concentration claim and adding the scope paragraph.** It removes the over-claim RL5B and dypE both flagged at zero compute, and the 8-seed boundary re-score either strengthens the SINet result or tells us honestly that it doesn't.
3. **The anchor table: published S2R-COD vs ours vs supervised vs RISE, with backbone and labels.** It answers RL5B's only non-textual concern, and our arms matching or beating S2R-COD's own published number shows that the low absolute level comes from the protocol, not from a weak reproduction.

## (b) Every number in the drafts and its source
| Number | Source |
|---|---|
| +0.0024 [−0.0020, +0.0067], p 0.10 / 0.1009, δ_min 0.0059 | `tab:tost` ← `out/se/abc_metrics.csv`; **EXP block pending (P2) → `EXP REBUTTAL_STATS`** |
| C10−CSHUF p 0.019 | same |
| paired CI [−0.0023, +0.0070], p 0.11; r = −0.04; 13/16, 5/16, 6/16; MDE values | **ad hoc → `EXP REBUTTAL_STATS`** |
| 0.0142, 0.0071 | `rebuild/ABC/PREREGISTRATION.md` §1/§2.9 @ `065dac6` |
| 0.0152 (0.6984 → 0.7136), 0.6845 | S2R-COD arXiv 2507.18911v3 Tab. 1 (external) |
| sd 0.0025–0.0049 | `se/abc_verdict.json` per_arm_sd → EXP SE l.3617 |
| C10 0.7175, B 0.7151 | EXP SE (l.3617ff) / `se/abc_verdict.json` arm_means |
| MT 0.6988 | EXP PC (l.2658ff) `MT_mean_COD10K = 0.698767` |
| 0.0197 (PC) | EXP PC `DELTA_C10_minus_MT_COD10K = +0.019713` |
| 77% differ, 14.1%, 18.4% | EXP ABC #1 l.1279-1281 (3 seeds) + ad hoc seeds 46–50 → `EXP REBUTTAL_STATS`; 18.4% from EXP ABC #1 l.1316 |
| 48%, 8.8% | EXP T2 #1 l.2359-2361 |
| 50/76, 44, 41, 9 | EXP D2R (41; 40/41 COD10K-train); 9 Tier-B **unlogged adjudication → `EXP REBUTTAL_CONTAM`** |
| 6 CAMO-train, 50 in the 4040 pool, 3 byte-identical | **ad hoc → `EXP REBUTTAL_CONTAM`** |
| 0.763 / 0.790 (RISE), DINOv2 ViT-L/14 | arXiv 2510.18437 Tab. 1 (external) |
| 0.815 (SINet-v2 supervised) | secondary (UCOD-DPL Tab. 1); **confirm against the TPAMI PDF** |
| a79886a 2026-09-18 11:48:26 (re-committed 28cfd84 2026-09-19); OR launch 10:46, OR first score 18:23, FX first run 18:23 (09-18), SE first run 09-20 03:50 | `git reflog` (a79886a, reflog-only until tagged); `rebuild/OR/driver_or.log`; `Snapshot/ABC/*/training_log.log` first lines; EXP OR scoring block l.3305 |
| WS4/WS5′/WS6/WS7 results | placeholders; filled only from their EXP blocks |

## (c) UNVERIFIED or MISMATCH — must not be claimed
- **UCOD-DPL 0.709 / 0.754**: not in the paper. Use 0.727/0.761 (DINOv1) or 0.834/0.850 (DINOv2) only after a PDF check.
- **SINet NC4K 0.808** is not from the SINet paper. Cite it as a secondary source or drop it. **SINet-v2 0.815/0.847** waits on the primary-source check.
- **The 9 Tier-B / animal-7 rejection** (paper says 50, JSON says 51) until the adjudication is committed.
- **"Each pre-registration committed before its campaign's first run"** holds for FX and SE (`a79886a`), **not for OR**: committed 62 min after launch and before any score (P1). Also, `a79886a` exists only in the local reflog until it is tagged.
- **"Every number traceable to a log block"** until the P2 blocks exist.
- **The OpenReview comment character limit** is unverified; stay ≤ 4,500 chars.
- **Two runs per GPU** has never been measured, so the budget doesn't assume it. **Single-round supervised run time and LAKE-RED render throughput** are unmeasured, and the first run of each measures them.
- **That round-2 initialisation matches across arms at the same seed** is unverified, so "paired" means round-1 init plus the seed-coupled B draw.
- **The review text itself**: every concern above is the prompt's paraphrase.

---
---

# Addendum 1 — 2026-11-07 (IST)

*Append-only. Nothing above this line is edited or deleted. Where this addendum and the text above disagree, this addendum governs. Each item cites the log block its facts come from.*

## A1. P1 and diff D9 are corrected (supersedes the P1 bullet in Phase 0 and row D9)

Checked against `EXP REBUTTAL_PREREG_PROVENANCE` (2026-11-07T15:01:30, commit `eabbfed`). Every time below comes from that block:

| Fact | Value (IST) | Source line in the block |
|---|---|---|
| a79886a author = committer date | 2026-09-18 11:48:26 | `a79886a_author_date`, `a79886a_committer_date` |
| tag `prereg-or-fx-se-a79886a` → a79886a | PASS | threshold 1 |
| FX, SE blobs a79886a ≡ 28cfd84 | sha256 `5f96c844…`, `45127974…` | thresholds 3–4 |
| OR a79886a is an exact prefix of 28cfd84; §OR.0, §OR.1 byte-identical | PASS (+4574 bytes = Addendum A1, 2026-09-19) | thresholds 5–7; diff in `out/or_prereg_a79886a_to_28cfd84.diff` |
| OR first training step | 2026-09-18 10:46:14 | `OR_first_training_step` |
| OR first endpoint-derived number (MyTest per-image MAE) | 2026-09-18 16:51:49 | `OR_first_endpoint_number` |
| OR first S_alpha | 2026-09-18 18:23:17 | `OR_first_S_alpha_written`; EXP OR scoring block (log l.3305) |
| FX first training step | 2026-09-18 18:23:23 | `FX_first_training_step` |
| SE first new-run step | 2026-09-20 03:50:28 | `SE_first_new_run_step` |
| tag on remote | **UNVERIFIED**: this environment has no GitHub credentials (`Permission denied (publickey)`, no key in `~/.ssh`, no agent) | `tag_on_remote` |

**Correction to the prompt's claim "first scored OR result 18:23".** S_alpha was first written at 18:23:17. But `MyTest.py` prints a per-image **endpoint MAE** during inference, so the first endpoint-derived OR number dates from **16:51:49**. Both are after the 11:48 commit, so the substance of the claim holds. The text below uses "before any oracle result existed" and gives the earlier time.

**Correction to the proposed sentence's last clause.** "Only the arm's construction was new" is not accurate. OR's *verdict bands* are the four-arm rule frozen at `065dac6`, verbatim ("Rule (identical to A/B/C and T2, unchanged)"). Its arm, its two gaps (CORACLE−B, CORACLE−C10), its noise pool ({B, C10, CORACLE}, df = 6) and its interpretation clauses were new.

**P1, replacing the Phase-0 bullet, and D9 "after" text:**
> Our repository history records that the pre-registrations for the seed expansion, the oracle and the unpinned schedule were committed together at `a79886a` (18 Sept 2026, 11:48 IST). A later history rewrite re-committed them, unchanged, as `28cfd84`, and the original commit is preserved under a tag. The schedule and seed-expansion campaigns began after that commit. The oracle campaign's first runs began about an hour earlier, at 10:46, before any oracle result existed (the first endpoint-derived number dates from 16:51). Its verdict rule is the four-arm rule frozen at `065dac6`, unchanged. Its arm, its two gaps and the arms its noise estimate pools over were new.

**SE hash, everywhere:** `b755aa9` → `a79886a`. That covers D9, the response drafts, and any future revision text. `b755aa9` is the 2026-09-13 base commit the log blocks were run against, not the pre-registration commit.

## A2. WS5′ becomes three arms (supersedes the WS5′ row, its compute line, and PREREGISTRATION_WS5 draft)

- **Arms:** B, C10, CSHUF. **Arch:** SINet only. **Seeds:** 51…84 (fresh).
- **n = 34 per arm, 102 runs**, from `EXP REBUTTAL_WS5_POWER` (2026-11-07T15:03:12, commit `412d0f2`): the largest n with ⌈3n/2⌉ × 105.9 min × 1.10 ≤ 6120 min.
  - Launch 2026-11-10 06:00 IST, end 2026-11-14 09:00 IST with the buffer (00:00 without it). n = 35 would end 12:53 and miss 14 Nov 12:00.
  - n ≥ 24, so the recommendation is to **run**.
- **Power** (Welch TOST, δ = 0.005, α = 0.05, 4000 draws, at the observed eight-seed differences), COD10K primary:

| Contrast | Role | Observed (SE, 8 seeds) | Power at n = 34 |
|---|---|---|---|
| C10 − B | total targeting effect | +0.0024 | **0.86** |
| C10 − CSHUF | direction effect, same shape | +0.0003 | **1.00** |
| CSHUF − B | concentration effect, same budget, no aim | +0.0020 | **1.00** |
| all three jointly | | | 0.86 |

- **Reported per contrast:** Welch 95% CI; TOST at 0.005; the paired-by-seed CI (secondary); and the frozen ABC 2σ̂ / sign verdict, for continuity only.
- **Outcome wording, fixed in advance:** EQUIVALENT (90% CI within ±0.005) · BENEFIT (95% CI lower bound > 0) · HARM (95% CI upper bound < 0) · UNRESOLVED (otherwise).
- **Joint readings, fixed in advance:**
  - C10−B BENEFIT with C10−CSHUF EQUIVALENT → "concentration, not direction, helps downstream."
  - All three EQUIVALENT → "neither helps at ±0.005."
  - Any other combination is reported as it falls.
- **No multiplicity correction.** All three contrasts are reported unadjusted, and the paper says so.
- **Arm mechanics:** B draws with `default_rng(700000+seed)`; CSHUF uses the committed T2 permutation (`perm_seed` 910004); C10 is deterministic.
- **Discipline:** never pooled with SE. All runs are reported or none. A run that fails `verify_run` is re-run under the same seed and logged as a discard. No interim looks.
- **Compute:** 102 × 105.9 min ≈ 180 GPU-h. With WS6 + WS4 (~31 GPU-h), the total committed rises to about 211 of 312 GPU-h.

## A3. WS7 is deferred

WS7 runs only if WS5′ finishes at least 24 h before 16 Nov 00:00 IST. The decision is made on 12 Nov from WS5′'s **actual** progress (runs verified so far and the measured mean wall), not from this estimate. At the planned end time (14 Nov 09:00), WS7 would not run.

## A4. WS4b is dropped; the WS4 download is approved

The source-only row is covered by S2R-COD's published Tab. 1 source-only numbers (SINet 0.6418, SINet-v2 0.6466), cited as external and labelled as such. The WS4 download is approved. Its gate is unchanged: downloaded images must match `Dataset/Target/Image` by sha256, 4040/4040, or WS4 stops.

## A5. Response-draft rules (the drafts themselves are in A5-drafts below, written after WS1/WS3)

1. **General comment.** Delete the sentence about pre-registration files "reaching git a day after their runs began" (and the softened version that replaced it). Add one line to a short "other changes in the revision" list: *"Appendix B now gives exact commit times for each pre-registration; one campaign's file was committed an hour after its runs started, before any result existed."* Keep the effective-contrast correction.
2. **Caus, the "sanity check" point.** Name GAUDA, DisCL and SynQuE. **VERIFIED** against the submitted PDF (`AD-PCHG-250926_FINAL.pdf`, Table 4 = `tab:closest`): each is listed with abstention/control "none reported".
3. **Every reply labels the campaign behind each number.** No table in the paper prints three-seed arm means: Table 1 is arm definitions, Table 2 shows gaps only, and per-run values are in Tables 10/11. A three-seed mean is therefore cited to the ABC verdict block, and an eight-seed mean to the SE verdict block.

# Equation Audit Report

The manuscript contains **one numbered equation** (Eq. 1). Because most of its mathematical content is stated inline or in prose, the important inline mathematical and statistical statements are audited in §2 as well. Line numbers refer to post-audit `main.tex`.

## 1. Numbered equations

| Eq. | Location | Symbols Defined? | Dimensionally Valid? | Algebraically Valid? | Consistent With Later Use? | Status |
|---|---|---|---|---|---|---|
| (1) ES(x) = a‖∇σ(s(x)) − ∇σ(t(x))‖₁ + b·BCE(σ(s(x)), σ(t(x))) | §2, l. 207–211 | Mostly. `s, t, σ, ∇, a, b` are defined. **ES is not expanded**; the normalisation of ‖·‖₁ and the argument order of BCE are unspecified. | Yes: both terms are scalars. The first is an L1 norm of the difference of two same-shape magnitude maps; the second is a cross-entropy of two maps in (0,1). | Yes. Domain: the sigmoid outputs lie in (0,1), so the BCE logs are defined (numerical clipping is implied). | Yes: §3.2 correctly calls it "boundary-focused", and App. B gives a = 0.9, b = 0.3 and the "unweighted cross-entropy" variant. The claim that the gradient term is "dominant" (l. 215) cannot be checked without the normalisation. | **VERIFIED WITH MINOR ISSUE** |

### Detail for Eq. 1

- **Normalisation.** If ‖·‖₁ is a *sum* over 352² pixels while BCE is a per-pixel *mean*, the first term is larger by roughly 10⁵. It would then be "dominant" by construction, not because of the data. State which is used.
- **Notation.** `∇` here means Sobel gradient *magnitude*, not a gradient vector. Consider `G(·)`.
- **BCE(p, q).** BCE is asymmetric. State which argument is the target; the text implies the teacher.

## 2. Important inline mathematical statements

| # | Statement | Location | Status | Notes |
|---|---|---|---|---|
| I1 | Allocation: "temperature softmax over the cluster scores, at τ = 1.0" | §2 l. 216–218; App. B l. 782–785 | **QUESTIONABLE** | The reported quotas imply an effective temperature of ≈ 0.0101 in raw-score units (log-quota vs score: r = 0.9999, slope 98.8). A τ = 1 softmax on raw scores (range 0.047–0.071) is nearly uniform: top/10th ratio 1.024 vs the reported 10.2. An unstated normalisation must exist. See the reasoning below. |
| I2 | Verdict rule: REAL EFFECT iff \|Δ\| > 2σ̂ and every seed agrees in sign | §2 l. 251–255 | **VERIFIED** | Reproduces every bar and verdict computable from Tables 9/10. |
| I3 | σ̂ = pooled within-arm SD; pooled over arms at df = arms × (seeds − 1) | §2; App. B l. 793–796 | **VERIFIED WITH MINOR ISSUE** | Correct for 8/6/28. The positive-control bar implies df = 4 (two arms), which is not listed. |
| I4 | "eight seeds would tighten the bar by √(8/3) ≈ 1.63× if the per-arm spreads stayed as measured"; projected bar 0.0034 | §3.1 l. 312–313; App. C l. 883–885 | **INCORRECT** | See below. |
| I5 | 3-seed Welch 95 % CI for C10−B = \[−0.0035, +0.0136\], df ≈ 2.8 | App. C l. 896–898 | **VERIFIED** | Recomputed: df = 2.76, CI \[−0.0035, +0.0136\]. |
| I6 | 8-seed Welch CI \[−0.0020, +0.0067\]; TOST at δ = 0.005; "smallest δ" | §3.1 l. 357; Table 5 | **VERIFIED (internal consistency)** / CANNOT VERIFY (inputs) | The script's `welch_tost` is a correct TOST: p = max of the two one-sided tests, and bound = \|Δ\| + t₀.₉₅·SE. Every row's smallest δ and bolding agree. The 8-seed data are not in the manuscript. |
| I7 | A0 contributes 92.7 % of the pooled variance | App. C l. 866 | **VERIFIED** | 0.927. |
| I8 | Falsification bar 0.0055 over B, C10, CSHUF, CINV | App. C l. 875 | **VERIFIED** | 0.00553. |
| I9 | SE bar 0.0069 from the per-arm SDs 0.00251, 0.00489, 0.00278, 0.00302 | App. C l. 885–887 | **VERIFIED** | 2·√(mean of the variances) = 0.0069. |
| I10 | Steps per epoch 253/127 → 341/171 (×1.35) | §3.1 l. 334; App. B; App. G | **VERIFIED** | Ceilings of 4040/16, 4040/32, 5447/16 and 5447/32. |
| I11 | Effective contrast ≈ 18.4 % × 48 % ≈ 8.8 %; arms share 89 % of their data | App. C l. 912–918 | **VERIFIED WITH MINOR ISSUE** | 8.8 % is correct. The 89 % is inconsistent: 452–511 differing of 5447 gives a shared fraction of 90.6–91.7 %. |
| I12 | Degenerate-end definitions: max_j p_j ≥ 0.95; TV from uniform < 0.01; τ ∈ \[10⁻⁴, 10³\] | App. B l. 783–785 | **VERIFIED WITH MINOR ISSUE** | Well defined, but `p_j` is never defined. Interacts with I1. |
| I13 | CSHUF permutation: zero fixed points, \|ρ\| ≤ 0.10; realised ρ = −0.03351; CINV ρ = −1 with one fixed point at odd k | App. B l. 756–760 | **VERIFIED** | Mathematically correct: reversing a ranking of odd length k = 75 fixes the median element (rank 38). |
| I14 | Cohen's d attribution +0.0073 / −0.0649; effective-rank ratio 0.634 | §3.2 l. 382–386 | **CANNOT VERIFY FROM MANUSCRIPT** | The effective-rank ratio's numerator and denominator are undefined. |
| I15 | "about twice as strongly" (+0.8553 vs +0.4276) | §3.3 l. 457–458 | **CANNOT VERIFY FROM MANUSCRIPT** | The arithmetic is right (2.000), but neither value appears in Table 7. The claim's scope exceeds Table 7, where the boundary block fails 6/8. |
| I16 | 50/76 = 65.8 %; 50 + 16 + 10 = 76; 1000/4040 = 24.8 %; enrichment 2.08× | §3.3, §3.4 | **VERIFIED** | |
| I17 | Adjudication "animal-7 … the only candidate below the calibration band 525–1174" | App. E l. 1002 | **INCORRECT** | animal-72 (396) and animal-43 (263) are also below 525. |
| I18 | Homography sanity check "to three decimals (5.512 → 5.514)" | App. E | **FIXED** | Now reads "to within 0.002". |

## 3. Reasoning for QUESTIONABLE and INCORRECT items

### I1: Allocation temperature (QUESTIONABLE, Major)

Take the ten tabulated clusters from `table_cluster_composition.tex`, with quota q_j and score es_j. If q_j ∝ exp(es_j/τ), then log q_j = es_j/τ + c. A least-squares fit gives 1/τ_eff = 98.8, so τ_eff ≈ 0.0101, with r = 0.9999. The allocation is therefore exactly a softmax, but on scores divided by ≈ 0.0101. That value is plausibly the across-cluster standard deviation of es_j, meaning the scores were z-scored before the softmax. **This is inferred, not established.** With τ = 1 on raw scores the top-to-tenth quota ratio would be e^{0.0236} = 1.024, not 194/19 = 10.2. The main text must state the normalisation. Caveat: the evidence comes from a table that is not in the compiled PDF.

### I4: √(8/3) projection (INCORRECT, Major)

σ̂ is defined as a pooled per-run standard deviation, and all three reported bars reproduce as 2σ̂ with no √n factor (I8, I9 and the ABC bar). For a fixed underlying spread, E[σ̂] does not depend on the number of seeds n. More seeds shrink only Var(σ̂). So "if the per-arm spreads stayed as measured", the 8-seed bar would equal the 3-seed bar (0.0055), not 0.0055/√(8/3) = 0.0034. A √(8/3) reduction applies to the *standard error of a difference of means*. The rule does not use that quantity, although the Welch/TOST analysis correctly does.

### I17: Calibration band (INCORRECT, Moderate)

The adjudication table lists these inlier counts: 2015, 3332, 3403, 3097, **396**, 1456, **263**, 860, 1017, and 25 for animal-7. Three are below 525, so the sentence is false as written. This is a **wording error only**. The 525–1174 band describes the same-dimension Tier-A positives and is not an acceptance rule. Acceptance uses the operating point of 20 plus the residual check, and rescaled copies (animal-72 at scale 6.36, animal-43 at 0.53) naturally yield fewer inliers. Suggested rewording: "the only candidate near the operating point".

## 4. Summary

| Category | Count |
|---|---|
| Numbered equations checked | 1 |
| Numbered equations verified (with minor issue) | 1 |
| Inline statements checked | 18 |
| Verified | 8 (I2, I5, I7, I8, I9, I10, I13, I16) |
| Verified with minor issue | 3 (I3, I11, I12) |
| Verified internally, inputs unverifiable | 1 (I6) |
| Questionable | 1 (I1) |
| Incorrect | 2 (I4, I17) |
| Cannot verify from manuscript | 2 (I14, I15) |
| Fixed during audit | 1 (I18) |

---

## 5. Round 2 update (after the repository was supplied)

| # | Round-1 status | Round-2 status | Basis |
|---|---|---|---|
| Eq. (1) | Verified with minor issue | **VERIFIED.** ES is the protocol's edge-aware saliency loss. Both terms are per-pixel means (`F.l1_loss`, `F.binary_cross_entropy`, default `reduction='mean'`). The student's output is the prediction and the teacher's the BCE target. The acquisition score uses the unweighted BCE. All of this is now stated in App. B. | `Src/utils/tool.py:57–77`; `rebuild/T2C/t2c_signals.py:98` |
| **Eq. (2) (new)** | n/a | **VERIFIED.** p_j ∝ exp((e_j − max e)/(τ·s_e)), with s_e the population SD across clusters, plus largest-remainder quotas. The repo's `softmax_alloc` + `largest_remainder` on the committed scores reproduce **all 75** quotas exactly; s_e = 0.01012. | `rebuild/C1/c1_targeted_vs_random.py:75–94`; `DIAG/out/diag_clusters.json` |
| I1 (allocation) | Questionable | **RESOLVED.** Documented as Eq. (2). | as above |
| I3 (df) | Minor issue | **VERIFIED.** df = 4 for the two-arm PC is now listed. | `PC/out/pc_verdict.json` (σ̂ = 0.002977 pooled over C10 and MT) |
| I4 (√(8/3)) | Incorrect | **FIXED.** Stated in §3.1 and App. C as a pre-registration error. | `SE/PREREGISTRATION_SE.md:101,167` |
| I6 (TOST) | Internally verified | **VERIFIED against data, and a claim corrected.** All 16 rows regenerated from `se/abc_metrics.csv` match `results.md` §4. The 5 equivalences include C10−B on SINet·NC4K (p = 0.0084). | `figs/make_tost_table.py` |
| I11 (89 %) | Minor issue | **FIXED.** The unsupported number was removed. | — |
| I14 (effective rank) | Cannot verify | **VERIFIED.** The participation-ratio effective rank of the embedding covariance is lower than a random draw's in 20/20 cells, mean 0.634. | `C1/C1_RESULTS.md:241–254` |
| I15 (0.8553/0.4276) | Cannot verify | **VERIFIED.** Per-cluster Spearman at k = 75, mean over 10 seeds; the ratio is 0.4999. | `B1/B1_RESULTS.md:24–25` |
| I17 (animal-7) | Incorrect | **FIXED.** Reworded. | adjudication table |

**Final equation tally.** Numbered equations: 2, both verified. Inline statements: 18.

| Status | Inline statements |
|---|---|
| Verified | 14 |
| Fixed during the audit | 4 (I4, I11, I17, I18) |
| Questionable | 0 |
| Incorrect and not fixed | 0 |
| Cannot verify | 0 |

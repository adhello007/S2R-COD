# Symbol Consistency Report

Line numbers refer to post-audit `main.tex`. "App." means the appendix sections of `main.tex`, or the `\input` table files where named.

The paper defines its symbols mainly in prose. It uses one displayed equation (Eq. 1), and most quantities are named statistics or codes rather than algebraic objects. `math_commands.tex` is the stock ICLR macro file; apart from `\atemp`, none of its notation macros are used.

## 1. Mathematical symbols

| Symbol | Meaning | Type/Dimension | Defined At | Used At | Consistent? | Comments |
|---|---|---|---|---|---|---|
| `x` | an unlabelled target image | input image (352×352×3) | Eq. 1, l. 208 | Eq. 1 only | Yes | The image size is given only in App. B (l. 749). |
| `s(x)`, `t(x)` | student / teacher logits | per-pixel logit map | l. 212 | Eq. 1 | Yes | `t` is only local. |
| `σ(·)` | sigmoid | elementwise map | l. 212 | Eq. 1 | **Overloaded** | Shares its letter with `σ̂` (SD). The hat disambiguates. Suggest `\operatorname{sig}`. |
| `∇(·)` | Sobel gradient **magnitude** | map → nonnegative map | l. 212 | Eq. 1 | Non-standard | `∇` normally denotes a gradient vector. Suggest `G(\cdot)` or `|\nabla \cdot|`. |
| `‖·‖₁` | L1 norm over pixels | map → scalar | Eq. 1 | Eq. 1 | **Unspecified** | Sum or per-pixel mean is not stated. This matters for the claim that it is the "dominant term" (l. 215). |
| `BCE(·,·)` | binary cross-entropy between two soft maps | (map, map) → scalar | Eq. 1 | Eq. 1 | **Unspecified** | Never expanded; the argument order (which map is the target) is undefined. App. B l. 752 says "unweighted cross-entropy variant". |
| `a`, `b` | Eq. 1 weights | scalars, 0.9 / 0.3 | l. 213 (values App. B l. 751) | Eq. 1, App. B | Yes | App. B calls them "consistency weights", consistent with l. 206. |
| `ES(x)` | per-image uncertainty (disagreement) score | scalar ≥ 0 | Eq. 1 | §3.2 ("Equation 1"), Tables 7/8 ("ES") | Yes | **Acronym never expanded.** |
| `es_j` | cluster score (mean ES over members) | scalar | orphan `table_cluster_composition.tex` | none in the PDF | n/a | The main text says "a cluster's score is the mean over its members" (l. 214) but never names it. |
| `k` | number of k-means clusters | integer, 75 | l. 203 | Table 6, App. B | Yes | Consistent with Table 6 (bold k = 75 for `dinoL518`). |
| `j` | cluster index | integer | App. B l. 784 (`max_j p_j`) | orphan table | Partly | Not introduced in the main text. |
| `p_j` | allocation share of cluster j | probability simplex | **not defined** (appears first in App. B l. 784) | App. B | **Undefined** | Should be defined in §2 as the softmax output. See M1: the implied scale is inconsistent with τ = 1 on raw scores. |
| `τ` (`\atemp`) | allocation temperature | scalar > 0, 1.0 | l. 218 | App. B l. 782–785 | Yes | Always typed via `\atemp`, as the header comment requires. |
| `B` | **(1)** random-allocation arm; **(2)** generation budget | label / integer | (1) l. 226; (2) App. B l. 782 | (1) throughout; (2) App. B, orphan table "% of B" | **CONFLICT** | Rename one of them, e.g. budget `N` or `N_{\text{gen}}`. |
| `S_α` | S-measure | scalar in [0, 1] | l. 136 | throughout | Yes | α = 0.5 fixed (l. 252, l. 787). |
| `α` | S-measure structural weight | scalar, 0.5 | l. 252 | App. B l. 787 | Yes | Previously also the temperature; fixed by the author before this audit (`\atemp`). |
| `σ̂` | pooled within-arm SD of per-run S_α | scalar | l. 251 | Tables 1, 2, 4, 5; App. C | Yes | Verified to be the **per-run** SD: the bars reproduce as 2σ̂ with no 1/√n. That makes the √(8/3) projection inconsistent (M2). |
| `2σ̂` / "bar" | verdict threshold | scalar | l. 251–253 | Tables 1, 2, 4 | Yes | |
| `×bar` | \|Δ\| / 2σ̂ | ratio | Table 1 header | Tables 1, 4 | Yes | Defined only implicitly. |
| `Δ` | difference of arm means | scalar | Table 1 | Tables 1, 4, 5; App. C | Yes | |
| `n` | seeds per arm | integer | Table 1 | Tables 1, 4 | Yes | The orphan table's `n_target` and `n_test` are counts, a different meaning, but that table is not in the PDF. |
| df | degrees of freedom | integer / real | §3.1 l. 312; App. B l. 793 | App. C | **Partly** | App. B lists 8/6/28; the positive control reproduces only at df = 4 (Mo1). The Welch df (≈ 2.8) is a different quantity, described correctly. |
| `ρ` | Spearman rank correlation | [−1, 1] | l. 757 (`|ρ| ≤ 0.10`), Table 7 | Tables 7, 8, App. B, §3.1 | Yes | "rank correlation" is used in prose throughout, consistently. |
| `d` | Cohen's d | scalar | §3.2 l. 382 | Fig. 2 | Yes | |
| `δ` | TOST equivalence margin | scalar, 0.005 | Table 5 caption | Table 5, §3.2 (`±0.005`) | Yes | |
| `p` | TOST p-value | [0, 1] | §3.2 l. 400 | Table 5 | **Minor overload** with `p_j` | |
| `z_obj`, `z_unc` | partialled covariates | per-cluster scalars | Table 8 caption | Table 8 | Yes | |
| `H`, `I` | homography, identity | 3×3 matrices | App. E l. 978 (implicit) | App. E | Acceptable | |
| `F^w_β`, `E_φ` | weighted F-measure, E-measure | scalar metrics | App. A / App. B | App. B l. 788 | **`E_φ` undefined** as a symbol | |
| MAE | mean absolute error | scalar | App. B l. 787 (unexpanded) | Tables 7–10 | Yes | Expand once. |
| IoU / Boundary IoU / Boundary F | segmentation metrics | scalar | Table 2 | Table 2, App. C | Yes | Boundary IoU is now cited in App. C. |

## 2. Experimental identifiers (used like symbols)

| Symbol | Meaning | Defined At | Used At | Consistent? | Comments |
|---|---|---|---|---|---|
| A0 | base pool only | l. 224 | Tables 1, 9, App. C | Yes | Called "the unpadded arm" in §3.3 (undefined term). |
| A2 | +1000 real photographs | l. 225 | Tables 9/10, App. B | Yes | |
| B | +1000 random renders | l. 226 | throughout | **Conflict** with budget `B` | |
| C10 | +1000 targeted renders | l. 227 | throughout | Yes | The "10" is unexplained. |
| CSHUF / CINV / CORACLE | shuffled / reversed / oracle allocation | l. 233–235 | throughout | **CORACLE inconsistent** | §2 says "replaces the score"; App. G and Fig. 1 say "re-assigns committed quotas by rank" (shape-preserving). |
| MT | mean-teacher baseline | implicit (l. 342) | Tables 1, 9/10 | **Code undefined** | |
| C10FX / BFX | arms under the unpinned schedule | none | Tables 1, 4 | **Undefined** | |
| ABC / SE / OR / FX / PC / T2 / T2C / AC / B1 | campaign codes | none (SE, OR, FX, PC inferable) | Tables 1, 4, 6–10 captions, App. G | **Undefined** | Add a legend to the Table 1 caption. |
| verdict bands | REAL EFFECT, WITHIN NOISE, INCONCLUSIVE | l. 253–255 | Tables 1, 4; §3.3 | **Partly** | DETECTED (Table 1) is undefined, and the AI-use statement says "four" bands. |

## 3. Drift summary

1. **`B`**: arm vs budget. Rename one.
2. **`p_j`**: used but never defined, and its implied scale contradicts τ = 1 (M1).
3. **`σ`**: sigmoid vs `σ̂`. Tolerable.
4. **ES / `es_j`**: acronym never expanded; cluster-level notation only in the orphaned table.
5. **CORACLE**: two different definitions (§2 vs App. G).
6. **Campaign and arm codes**: several are used in the key table without definition.
7. **Verdict vocabulary**: 3 bands defined, a fourth (DETECTED) used, and "four" claimed.

---

## 4. Round 2 update

| Symbol | Round-1 status | Round-2 resolution |
|---|---|---|
| `B` (budget) vs `B` (arm) | Conflict | The budget is now **`N`** throughout App. B and Table 11. `B` denotes only the random arm. |
| `p_j` | Undefined | Defined by App. B Eq. (2). |
| `e_j` (cluster score) | Only in the orphaned table (`es_j`) | Defined in App. B as the mean of Eq. (1) over the cluster's target members; Table 11 uses `e_j`. |
| `s_e` | n/a (new) | Population SD of `e_1…e_k`. Defined in App. B; value 0.0101. |
| ES | Acronym never expanded | App. B: "the edge-aware saliency loss of the protocol we build on". |
| `‖·‖₁`, BCE | Normalisation and argument order unspecified | App. B: per-pixel means; BCE takes the teacher as target. BCE is also expanded in §2. |
| CORACLE | Two definitions | §2 now matches App. H (quotas re-assigned by true-error rank). |
| MT, campaign codes, DETECTED | Undefined | App. B "Campaign codes and verdicts". |
| MAE, EMA, COD, E_φ | Unexpanded | Expanded in App. B and App. A. |
| `σ`/`σ̂`, `∇` | Tolerable overload | Unchanged (cosmetic). |

**Remaining drift:** none of consequence. The only overloads left are σ/σ̂, which the hat distinguishes, and `p` (allocation share `p_j` vs TOST p-value), which is local and unambiguous.

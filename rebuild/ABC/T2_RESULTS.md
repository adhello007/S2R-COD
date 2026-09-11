# T2_RESULTS.md — the falsification arms: does the ES signal do anything to accuracy?

> Decision rule: `rebuild/ABC/PREREGISTRATION_T2.md`, committed at `617a2e1` **before** the first T2
> training run, plus Addendum A1 (see §6.3). Applied strictly, whatever the answer.
>
> Log blocks of record: `results/REBUILD_LOG.txt`, three `EXP T2` blocks — #1 pre-flight
> (2026-09-10T11:50), #2 run accounting (2026-09-11T11:12), #3 verdict (2026-09-11T11:52).
>
> **ADDITIVE.** `rebuild/ABC/PREREGISTRATION.md` and every committed A/B/C number are unaltered.
> T2 writes only under `rebuild/ABC/out/t2/`.

---

## §1 Headline

**WITHIN NOISE on all twelve cells: every gap, both architectures, both endpoints.**

The largest gap anywhere is 0.005007 (1.82 σ̂); the largest on the primary endpoint is 0.002656
(0.83 σ̂). Nothing approaches the 2 σ̂ bar.

Per the interpretation fixed before any number existed: **the target-side ES signal carries no
accuracy-relevant information beyond concentration, in any direction.** C1 established this in
embedding-distance space; it now holds on trained accuracy. Real targeting, destroyed targeting and
reversed targeting are indistinguishable at this sensitivity.

### §1.1 σ̂ and the bar — tighter than pre-registered

σ̂ = pooled within-arm sd of Sα over arms {B, C10, CSHUF, CINV}, per architecture per endpoint,
**df = 4 × 2 = 8**.

| cell | T2 σ̂ | T2 bar (2 σ̂) | A/B/C committed σ̂ | A/B/C bar | T2 bar is |
|---|---|---|---|---|---|
| SINet \| COD10K *(primary)* | **0.002767** | **0.005533** | 0.008966 | 0.017933 | **3.24× tighter** |
| SINet \| NC4K | 0.002757 | 0.005514 | 0.004155 | 0.008309 | 1.51× tighter |
| SINetv2 \| COD10K | **0.003195** | **0.006390** | 0.006129 | 0.012257 | **1.92× tighter** |
| SINetv2 \| NC4K | 0.002781 | 0.005563 | 0.005267 | 0.010534 | 1.89× tighter |

`PREREGISTRATION_T2.md` §T2.11 projected a bar of ≈0.0179 (SINet) / ≈0.0123 (SINet-v2) from A/B/C's
committed σ̂. **The realised bar is 3.2× and 1.9× tighter than that.** The reason is structural and
not a choice made after the fact: A/B/C's noise pool contained arm **A0**, whose per-arm sd was
0.017266 on SINet|COD10K — an order of magnitude above every other arm. T2's pool excludes A0 by
pre-registered definition, so the bar is set by four arms that are all B/C-family and all
exposure-matched at 5447 images.

Consequence: T2 resolves **39%** of the paper's whole MT→Ours gap (0.0142) on SINet and **45%** on
SINet-v2, against the ~126% the pre-registration conceded. The null is therefore stronger than
promised, not weaker.

### §1.2 The three gaps — the frozen verdict table

`Δ₁ = mean(Sα_C10) − mean(Sα_CSHUF)` · `Δ₂ = mean(Sα_C10) − mean(Sα_CINV)` ·
`Δ₃ = mean(Sα_CSHUF) − mean(Sα_CINV)`

**SINet | COD10K — PRIMARY (2 σ̂ = 0.005533)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | +0.001525 | 0.55 | −0.001437 | +0.006059 | −0.000048 | 1/3 | **WITHIN NOISE** |
| Δ₂ C10 − CINV | −0.000866 | 0.31 | −0.005448 | +0.005691 | −0.002841 | 2/3 | **WITHIN NOISE** |
| Δ₃ CSHUF − CINV | −0.002390 | 0.86 | −0.004010 | −0.000368 | −0.002793 | 3/3 | **WITHIN NOISE** |

**SINetv2 | COD10K — PRIMARY (2 σ̂ = 0.006390)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | −0.002656 | 0.83 | −0.008948 | +0.001838 | −0.000858 | 2/3 | **WITHIN NOISE** |
| Δ₂ C10 − CINV | −0.002312 | 0.72 | −0.004687 | −0.000004 | −0.002245 | 3/3 | **WITHIN NOISE** |
| Δ₃ CSHUF − CINV | +0.000344 | 0.11 | +0.004261 | −0.001842 | −0.001387 | 1/3 | **WITHIN NOISE** |

**SINet | NC4K — secondary, reported, never decides (2 σ̂ = 0.005514)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | +0.001705 | 0.62 | −0.001417 | +0.003258 | +0.003274 | 2/3 | WITHIN NOISE |
| Δ₂ C10 − CINV | −0.003302 | 1.20 | −0.009400 | −0.002873 | +0.002367 | 2/3 | WITHIN NOISE |
| Δ₃ CSHUF − CINV | −0.005007 | **1.82** | −0.007983 | −0.006131 | −0.000907 | 3/3 | WITHIN NOISE |

**SINetv2 | NC4K — secondary (2 σ̂ = 0.005563)**

| gap | Δ | \|Δ\|/σ̂ | s42 | s43 | s45 | sign | verdict |
|---|---|---|---|---|---|---|---|
| Δ₁ C10 − CSHUF | −0.001840 | 0.66 | −0.005621 | +0.000296 | −0.000195 | 2/3 | WITHIN NOISE |
| Δ₂ C10 − CINV | −0.003904 | 1.40 | −0.004422 | −0.002761 | −0.004528 | 3/3 | WITHIN NOISE |
| Δ₃ CSHUF − CINV | −0.002064 | 0.74 | +0.001198 | −0.003057 | −0.004333 | 2/3 | WITHIN NOISE |

No cell is REAL EFFECT, REAL REGRESSION or INCONCLUSIVE. **12/12 WITHIN NOISE.**

### §1.3 Arm means and per-arm sd

| cell | B | C10 | CSHUF | CINV |
|---|---|---|---|---|
| SINet\|COD10K mean | *0.713447* | 0.718481 | 0.716956 | **0.719346** |
| SINet\|COD10K sd | 0.001807 | 0.004059 | 0.001655 | 0.002853 |
| SINetv2\|COD10K mean | 0.695069 | *0.694669* | **0.697326** | 0.696981 |
| SINetv2\|COD10K sd | 0.004863 | 0.002091 | 0.003523 | 0.000637 |
| SINet\|NC4K mean | *0.766904* | 0.769013 | 0.767308 | **0.772315** |
| SINet\|NC4K sd | 0.002512 | 0.003240 | 0.000639 | 0.003632 |
| SINetv2\|NC4K mean | *0.748613* | 0.749559 | 0.751399 | **0.753463** |
| SINetv2\|NC4K sd | 0.004837 | 0.001173 | 0.002443 | 0.000454 |

**bold** = highest mean in the cell; *italic* = lowest.

### §1.4 Per-run Sα — all 48 cells

**COD10K (primary)**

| arm | SINet s42 | s43 | s45 | SINetv2 s42 | s43 | s45 |
|---|---|---|---|---|---|---|
| B *(ref)* | 0.711554 | 0.713632 | 0.715155 | 0.698340 | 0.689481 | 0.697385 |
| C10 *(ref)* | 0.717165 | 0.723034 | 0.715243 | 0.692321 | 0.696328 | 0.695360 |
| CSHUF | 0.718602 | 0.716974 | 0.715291 | 0.701269 | 0.694490 | 0.696218 |
| CINV | 0.722612 | 0.717343 | 0.718084 | 0.697008 | 0.696331 | 0.697605 |

**NC4K (secondary)**

| arm | SINet s42 | s43 | s45 | SINetv2 s42 | s43 | s45 |
|---|---|---|---|---|---|---|
| B *(ref)* | 0.764108 | 0.768972 | 0.767632 | 0.753317 | 0.743653 | 0.748868 |
| C10 *(ref)* | 0.765296 | 0.771241 | 0.770503 | 0.748534 | 0.750839 | 0.749305 |
| CSHUF | 0.766713 | 0.767983 | 0.767229 | 0.754154 | 0.750543 | 0.749500 |
| CINV | 0.774697 | 0.774114 | 0.768136 | 0.752956 | 0.753600 | 0.753833 |

### §1.5 Secondary metrics — COD10K arm means

| arch | arm | MAE ↓ | Fβw ↑ | Eφ (meanEm) ↑ |
|---|---|---|---|---|
| SINet | B | 0.076093 | 0.471096 | 0.742008 |
| SINet | C10 | 0.075558 | **0.487441** | 0.750806 |
| SINet | CSHUF | 0.077286 | 0.477135 | 0.747300 |
| SINet | CINV | **0.074947** | 0.483545 | **0.751834** |
| SINetv2 | B | 0.089752 | **0.483114** | 0.754122 |
| SINetv2 | C10 | 0.091109 | 0.481097 | 0.754280 |
| SINetv2 | CSHUF | **0.088099** | 0.482051 | **0.757193** |
| SINetv2 | CINV | 0.088640 | 0.480485 | 0.754933 |

**bold** = best in that architecture's column (MAE lower is better). C10 leads exactly one of the six (architecture x metric) combinations.

No secondary metric reverses the Sα picture: the arms are interleaved with no consistent ordering,
and C10 leads on none of the six (arch × metric) combinations except SINet Fβw.

---

## §2 What was actually tested

### §2.1 The arms

All three C-family arms are identical to C10 except for one substitution: the committed `target_es`
vector is **permuted across clusters** before the softmax. Same α = 1.0, k = 75, B = 1000, dinoL518,
R2 grey-128 centroid ranking, `desc_nc` serving, greedy distinct selection, LAKE-RED render pool, same
4447 base pool, same 4040 target set.

| arm | permutation | ρ(es[σ], es) | fixed pts | perm seed | `n_displaced` |
|---|---|---|---|---|---|
| C10 *(reference)* | identity | **+1.0** | 75 | — | 370 |
| CSHUF | random, rule-selected | **−0.03351** | 0 | 910004 | 404 |
| CINV | rank-reversing | **−1.0** | 1 *(structural)* | — | 367 |

CSHUF's permutation is the **first** of 64 pre-declared draws satisfying zero fixed points and
|ρ| ≤ 0.10 — chosen by a rule fixed before the draw, never by inspecting its consequences. CINV's
single fixed point is mathematically necessary: at odd k the median-ranked cluster is its own mirror
(`PREREGISTRATION_T2.md` §T2.3).

### §2.2 The same-shape assertion — the crux, and it held exactly

A permutation leaves `softmax_alloc`'s `p` a permutation of C10's, so entropy, TV-from-uniform and
max-share — symmetric functions of the multiset `{p_c}` — are preserved **exactly**. Measured, for
both new arms, against C1's committed cell `(dinoL518, B=1000, R2_cut, α=1.0)`:

| quantity | C1 committed | CSHUF | CINV |
|---|---|---|---|
| `clusters_funded` | 75 | 75 ✓ | 75 ✓ |
| `max_alloc_share` | 0.194 | 0.194 ✓ | 0.194 ✓ |
| `alloc_entropy_norm` | 0.78644 | 0.78644 ✓ | 0.78644 ✓ |
| `tv_from_uniform` | 0.49253 | 0.49253 ✓ | 0.49253 ✓ |
| `n_displaced` | 370 | 404 *(reported)* | 367 *(reported)* |

Exact equality at the recorded 5 dp — not a tolerance. **So the comparison varies the signal's
direction at fixed concentration, which is precisely what A/B/C could not do.**

A value-space inversion was considered and rejected before any arm was built: negating the ES vector
and reflecting it (`ES_max − ES_c`) produce an *identical* allocation here, because `softmax_alloc`
max-subtracts and `np.std` is invariant under both — each reduces to `min(es) − es`. And neither
preserves concentration on a skewed ES vector, so either would have varied direction **and**
concentration, leaving Δ₂ uninterpretable.

### §2.3 Set distinctness — gated before training

All three C-family arms fund all 75 clusters, so they overlap above chance by construction. Gated at
Jaccard ≤ 0.50 **before any GPU time**, because under this pre-registration equality is the
*supporting* outcome and two near-identical arms would manufacture it.

| pair | overlap | ×chance | Jaccard | **n_differing** |
|---|---|---|---|---|
| C10 \| CSHUF | 548 | 2.437 | 0.3774 | **452 / 1000** |
| C10 \| CINV | 489 | 2.175 | 0.3236 | **511 / 1000** |
| CSHUF \| CINV | 546 | 2.428 | 0.3755 | **454 / 1000** |

B-vs-C pairs remained at chance (0.907–1.081×), as C1 and A/B/C found. **Roughly half of each arm's
1000 injected images differ from any other arm's** — a real contrast, but see §5.2.

---

## §3 Interpretation, as fixed before any number existed

`PREREGISTRATION_T2.md` §T2.1 committed three readings in advance. The one that obtains:

> **ALL THREE WITHIN NOISE → the target-side ES signal carries NO accuracy-relevant information
> beyond concentration, IN ANY DIRECTION. Supports section 6(v) on trained accuracy, not only on
> geometry.**

This is the outcome, on both architectures and both endpoints. Neither falsification branch fires: no
Δ₁ or Δ₂ exceeds +2 σ̂ with 3/3 (which would have shown the signal contributes and forced §6(v) to be
softened), and none falls below −2 σ̂ with 3/3 (which would have made the signal actively misleading).

**§6(v) now rests on trained accuracy, not on embedding geometry alone.** C1 measured the signal's
contribution at +0.0073 of a Cohen's *d* against its own shuffle (13/20 cells, a coin flip) and
−0.0649 against an arbitrary cluster (worse in 16 of 20). T2 cross-checks all of that against a
trained outcome for the first time and finds the same thing: nothing.

The standing disclaimer in `ABC_RESULTS.md` §3.7 and `abc_build_pools.py` — *"no result from it may be
reported as evidence about that signal"* — is hereby **discharged for T2**. A/B/C's arm C still tested
concentration, not targeting; T2 tests targeting at fixed concentration, and that is what these twelve
cells measure.

---

## §4 The pattern that is NOT significant, reported because it exists

Under the frozen rule every gap is WITHIN NOISE and **no claim below is a finding.** Recorded because
suppressing a directional pattern because it failed a threshold would be the same sin as promoting one
that passed.

1. **C10 — the real signal — is the best arm in none of the four cells**, and is the *worst* of the
   four on SINetv2|COD10K (0.694669, below even B).
2. **CINV — maximally anti-targeted — has the highest mean in 3 of 4 cells**, and Δ₂ (C10 − CINV) is
   **negative in all four**: −0.000866, −0.002312, −0.003302, −0.003904. It reaches 3/3 sign
   consistency on SINetv2 at both endpoints.
3. The largest gap in the campaign, Δ₃ on SINet|NC4K (−0.005007, 1.82 σ̂, 3/3), also points away from
   the real signal.

Read honestly: this is what a null looks like when the signal is uninformative and the sign therefore
wanders — the two architectures **disagree in sign** on Δ₁ (+0.001525 SINet vs −0.002656 SINet-v2) and
on Δ₃ (−0.002390 vs +0.000344), which is the signature of noise rather than of a small real effect.
But the Δ₂ direction is consistent across all four cells, and the pre-registration named exactly this
case: a REAL REGRESSION would mean the signal is *not merely uninformative but misleading*. **It does
not reach the bar, so that is not the verdict.** It is the direction a larger or more sensitive
experiment should be pointed at, and it is not evidence of anything today.

---

## §5 Limits — what these twelve cells cannot settle

### §5.1 A null is bounded by sensitivity, not by truth
The bar is 0.005533 (SINet) / 0.006390 (SINet-v2) — 39% and 45% of the paper's entire MT→Ours gap of
0.0142. **A WITHIN NOISE result means "no effect resolvable at this sensitivity," never "no effect".**
This sentence was committed before any T2 number existed precisely so it could not be softened after
one. C1's +0.0073 of a *d* is a geometric quantity and predicts no accuracy difference at all, so T2
was never powered to detect an effect of that specific magnitude.

### §5.2 Every gap is attenuated by shared images
452–511 of 1000 injected images differ between any two C-family arms (§2.3); the rest are shared. The
effective contrast is therefore roughly half the nominal budget, and the attenuation biases **toward**
the null — which is the supporting outcome here. The 0.50 Jaccard gate bounds this but does not remove
it. Every Δ above should be read against `n_differing`, not as a full-budget contrast.

### §5.3 Pseudo-labelling is a second uncontrolled channel
`n_appended` spread **17.6%** of mean (1914–2278) across the 12 runs — far above the campaign's 5%
threshold, which **FAILS**, as it also failed in the frozen A/B/C record at a worse 22.2%
(1732–2163). Per architecture: SINet 7.2%, SINet-v2 14.4%. CLS selects target images by
`edge_loss < u·avg_loss` using each arm's **own** round-1 model, so the arms differ in how many
differently-pseudo-labelled images they append, beyond the permutation under test. `total_step` stays
pinned (0253 SINet / 0127 SINet-v2) in both rounds of every run, so this changes the mixture and never
the optimisation budget. **The 5% threshold was left exactly as frozen** — moving a bar after seeing
the number it fails is retuning, not fixing.

### §5.4 Other limits
- **n = 3.** No p-value, no bootstrap, no multiple-comparison correction, by design. Three gaps × 2
  architectures × 2 endpoints are reported against one bar, with sign-consistency counts.
- **CINV is a permutation**, hence formally a member of the shuffle family — deliberately its
  maximally anti-correlated member. It is not a value-space inversion (§2.2).
- **`best_epoch` ranges 21–99.** `SINetv2_CINV_s43` selected its teacher at epoch 99 of 100 — the
  final epoch — so that run was still improving when training stopped. No assertion covers
  `best_epoch`; disclosed so σ̂ is read with it in view.
- **T2 says nothing about concentration.** It varies direction at fixed concentration. Whether
  concentration itself helps is A/B/C's Δ(C10 − B), already WITHIN NOISE.

---

## §6 Integrity record

### §6.1 Inherited identically, asserted not re-implemented
Six pre-flight gates **6/6 PASS** before any training. Same base pool (4447, byte-verified against
E0's manifest, 0 mismatches), same target set, same seeds {42,43,45}, same six patches (P0
`--source_root`, P2 cudnn determinism included), same per-RUNID directory scheme, same endpoints, same
trainer and same eval path — gate G3 *proves* one `MyTrain.py` and one `MyTest.py`, so identity is not
argued but counted.

- Real `SrcDataset` positional parity, **every index of every pool**, 12/12 at n = 5447, 0 mismatches.
- Round-2 worst-case parity on the full union, 12/12 at n = 9487.
- Render masks pixel-identical to `raw_gt`, 1000/1000 for each new arm.
- `forbidden_path_references` = 0 over 25 scripts; no `/tmp/archive`, `/scratchpad` or archive
  dependency anywhere.
- Both new arms **seed-independent**: identical `image_digest` at all three seeds, 3/3 each,
  vacuous-pass excluded.
- Training: 12/12 runs, **0 discarded, 0 abandoned**. Wall 104.8–107.2 min SINet (ceiling 209),
  120.6–127.5 min SINet-v2 (ceiling 262).

### §6.2 Signal provenance is exact
No hash of `rebuild/B1/out/b1_cluster_es_dinoL518.csv` was recorded when C10 was built — it appears in
no manifest and no preflight JSON. Recorded here instead: sha256
`1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8`, git blob
`3fb4c46677a647e9a396e31cbc2b8f81b016ddd8` — **identical at HEAD and at `065dac6`, the A/B/C block-#1
commit** — and exactly one commit ever touched the file (`470e224`, EXP B1). The signal has never been
modified since B1 created it. C10 reproduces C1's committed cell on all **five** keys, `n_displaced`
included, as the downstream check.

### §6.3 The scorer, and Addendum A1
The eval path was validated against B1's committed values **before producing any new number**:
Sα 0.7172156 vs 0.717216 (Δ 3.8e-07), MAE 0.0744632 vs 0.074463 (Δ 2.3e-07), both under the 1e-5 bar.

B and C10 were **re-scored, never re-trained**, to build the σ̂ pool through one code path. They
reproduce `rebuild/ABC/out/abc_metrics.csv` **exactly at the recorded 6 dp, 24/24 cells, max deviation
0.000e+00**. Independent confirmation: T2's per-arm sd for B (0.001807) and C10 (0.004059) equal
A/B/C's committed values to six decimals, and A/B/C's committed Δ(C10 − B) = +0.005034 is reproduced
exactly.

**Addendum A1 (2026-09-11) is a correction to this document's own pre-registration and must be read
with it.** §T2.1 as frozen required the reference arms to reproduce `abc_metrics.csv` to `< 1e-9`.
That clause is **unsatisfiable by any correct computation**: the file records Sα at 6 dp, so rounding
alone admits up to 5e-7, ~500× the stated tolerance. The first full evaluation halted on it. The
clause was applied instead at the reference's own precision — exact equality of the recorded 6-dp
values, which is *stricter* than a 1e-6 tolerance — and is met with zero deviation. §T2.1 was not
edited; A1 is append-only and dated, and records that it was written after T2's 48 metric rows existed
but **before** any σ̂, gap or verdict had been computed. Endpoints, seeds, arms, the σ̂ definition and
df, the three gaps, the four bands, the 2 σ̂ bar and the interpretation clauses are untouched.

### §6.4 Defects found by running the path, and what they cost
Recorded because a campaign that reports only its successes cannot be audited.

| # | Defect | Consequence | Resolution |
|---|---|---|---|
| 1 | Seed-independence check hard-coded to `C10` | Assertion passed **vacuously** (`len(set([])) <= 1` is `True`) while its own metric printed `False` | Per-arm, empty digest list is now a FAIL |
| 2 | `cfam` derived only from the run set | Overlap gate never compared the new arms against **C10**, the reference every gap is measured against | C10 is always a reference set |
| 3 | Block notes/artifacts were A/B/C's, in **three** scripts | Blocks cited untagged paths; block #3 asserted A/B/C's Δ(C−B) and emitted a spurious **FAIL**; block #2 claimed "first TRAINS YES block"; block #1 carried the very disclaimer T2 discharges | Gap-set-aware thresholds, derived paths, T2 notes and T2 OLD CLAIMs |
| 4 | §T2.1's `< 1e-9` reference tolerance | Unsatisfiable; first full evaluation halted after ~22 min of scoring | Addendum A1 (§6.3) |

Defects 1–3 were reporting faults that produced no wrong number. **Defect 4 was a substantive clause
in the frozen pre-registration that could not be satisfied**, and it is the weakest link in this
record: the author of the rule also authored the flaw. Its mitigation is that it gates a
reproducibility cross-check rather than the hypothesis, and that its replacement is exact equality
rather than a looser tolerance — but a reader should audit A1 directly rather than accept that framing.
Every defective log block was uncommitted when found and was regenerated, never edited in place; the
superseded text is preserved outside the repository.

---

## §7 Bottom line

| question | answer |
|---|---|
| Does the real ES signal beat a shuffled one on accuracy? | **No.** Δ₁ WITHIN NOISE on both architectures; the two disagree in sign. |
| Does it beat a *reversed* one? | **No.** Δ₂ WITHIN NOISE everywhere, and negative in all four cells. |
| Is the direction of targeting ordered at all? | **No.** Δ₃ WITHIN NOISE; sign flips between architectures. |
| Does §6(v) survive on trained accuracy? | **Yes**, at a bar of 39–45% of the paper's headline gap. |
| Could a small real effect still hide here? | **Yes** — see §5.1 and §5.2. A null is bounded by sensitivity. |

The ES signal's *concentration* was already WITHIN NOISE in A/B/C. Its *direction* is now WITHIN NOISE
too. Nothing in the target-side uncertainty signal, as constructed, is resolvable on trained COD
accuracy at this budget — in any direction.

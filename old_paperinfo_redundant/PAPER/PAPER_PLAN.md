# PAPER_PLAN.md — ICLR 2027 negative-results paper

## Context

The Stage C rebuild is complete and committed: a pre-registered A/B/C campaign returned a null, the
causes were measured separately, and a contamination audit produced a released detector and a clean
evaluation protocol. The next step is the first full draft of an ICLR 2027 negative-results paper.

**Status: APPROVED 2026-09-09.** Drafting proceeds one section at a time, each reviewed before
the next. The manuscript lives in `rebuild/PAPER/`; the style files in `iclr2027/` are never edited.

The plan exists because the previous Stage C package wrote conclusions first and left scripts to catch
up. The rebuild's governing rule — *no number enters a document before a committed script has written
it to `results/REBUILD_LOG.txt`* — must be inherited by the paper. Everything below was verified
against committed artifacts this session; every gap is named rather than filled.

## Thesis (fixed, do not drift)

> We test whether uncertainty-guided closed-loop synthetic generation improves synthetic-to-real
> camouflaged object detection. Instantiated in CSRDA with the LAKE-RED generator, it yields no
> measurable accuracy gain. We dissect why — separating causes specific to this framework/generator
> from more fundamental ones — and we independently uncover severe contamination in a standard COD
> benchmark, for which we establish a clean evaluation protocol.

## Decisions taken (your answers)

| Question | Decision |
|---|---|
| Cause (ii), 48-scalar bottleneck | Keep as `[TODO: verify]`; **add D1 as a fifth cause** |
| A3 | **Include with the vacuity caveat** |
| Contamination sourcing | **D2 → D2R → D2_NC4K chain**, D2R as the verification headline |
| T1 metrics | **Sα only**; other metrics to appendix |

---

## 1. Corrections to the brief (verified this session)

| Brief said | Verified reality | Source |
|---|---|---|
| Template at `Downloads/iclr-2027-style-files/iclr2027/` | **Path does not exist.** Only copy is `iclr2027/` at repo root, **untracked** | `find`; `git status` |
| "LLM-use disclosure section" | Section is titled **“AI use statement”**; required, **not** page-limited, **≤ 1 page**; template supplies a fill-in paragraph | `iclr2027_conference.tex:397-412` |
| A3 is UNRUN | **A3 RAN** — `EXP A3`, 2026-09-08T10:34:47, 14/15 PASS | `REBUILD_LOG.txt:2147` |
| Cause (ii) source = "A1 block" | **No `EXP A1` block, no `rebuild/A1/`.** 48 is `UNMEASURED`, and *contradicted as a bound* | `ABC_SCOPING.md:1093`; `REBUILD_PLAN.md:336` |
| 53.9 % sourced to D2 | **Correct — D2 established it** (first logged `EXP D2` blk 3). D2R re-verified: MATCH, delta 0. *This corrects my own earlier statement to you.* | `REBUILD_LOG.txt:468`, `:628`, `:1867`, `:1977` |
| Power: "resolves ~half the MT→Ours gap and no smaller" | That is the **pre-registered intent**. Measured `2σ̂ = 0.017933` **exceeds** the 0.0142 gap → realised bar ≈ **1.3×** it. **Underpowered** | `ABC_RESULTS.md:6-11`, `:120-123` |
| Tolerance sweep incl. `d2_seed_experiment.json` | **Wrong file** — that is D2's LAKE-RED seed/shard determinism experiment (s8), no contamination content | `d2_seed_experiment.json`; `REBUILD_LOG.txt:657-664` |

---

## 2. Template constraints

`iclr2027/`: `iclr2027_conference.{sty,bst,bib,tex}`, `math_commands.tex`, `natbib.sty`,
`fancyhdr.sty`. No README, no PDF — the `.tex` *is* the instruction set.

- **9 pages** main text (10 camera-ready); **citations unlimited**. Appendix not addressed either way.
- Preamble is exactly `\documentclass{article}`, `\usepackage{iclr2027_conference,times}`,
  `\input{math_commands.tex}`, `\usepackage{hyperref}`, `\usepackage{url}`.
  **Neither `graphicx` nor `tikz` is loaded** — both must be added (tikz for `figures/methodology.tex`).
- `\iclrfinalcopy` stays **commented out** for submission.
- Template ships `\bibliography{}` *before* `\bibliographystyle{}`; reproduce as-is.
- `\citet{}` author-in-sentence, `\citep{}` otherwise; `.sty` fixes `authoryear,round`.
- Back matter: main → **AI use statement** → Ethics → Reproducibility → Author Contributions →
  Acknowledgments → bibliography → `\appendix`.
- `\addcontentsline` disabled (`\tableofcontents` empty); `\parindent 0pt` forced.
- **Do not alter style files.** Only the manuscript `.tex`.

---

## 3. Tier discipline

- **T1** — specific to CSRDA + LAKE-RED. An artefact of this loop or this generator.
- **T2** — about the data or the signal; travels further.
- **T3** — fully independent (the contamination audit).

Stated once in §1. Every T1 result carries an adjacent sentence naming what it does *not* generalise
to. **The failure mode to prevent:** pinned `total_step` (T1) reads as "adding synthetic data cannot
help", a T2/T3-sized claim that is unsupported.

---

## 4. Section plan with per-number sources

### Abstract — ~200 words, **written last**
Context → idea tested → the null (pre-registered, 2 architectures, 3 seeds) → causes by tier →
contamination → what a working system needs. All figures back-references; drafted only after every
section exists, then reconciled against tables.

### 1 Introduction — T-mixed
COD annotation scarcity; the idea stated **fairly and non-defensively**; "we test it, it does not
hold" with the tier taxonomy in the same breath; contributions = (a) null + pre-registration,
(b) five-cause dissection, (c) diffuse-cluster T2 result, (d) contamination + clean protocol +
released detector. **Tone: report, do not apologise.** Citations all `[CITE: …]`.

### 2 Related Work — every citation a marker, none invented
COD & benchmarks · synthetic data for COD (S2R-COD, LAKE-RED; other camouflage generators as
**related, not tested**) · uncertainty & active learning · negative results & benchmark integrity.

### 3 Method — "The Approach Under Test" — T1
Framing sentence: *we specify this in full because our contribution is a precise account of why it
fails; each component is later shown to be a distinct point of breakdown.*
Target clustering · deficiency scoring (ES) · softmax allocation at `T = α·sd(es)`, integer by
largest-remainder · foreground selection and the LAKE-RED interface · the A0/A2/B/C10 conditions.

**Verified constants:** EMA **λ = 0.996** (`MyTrain.py:230` overwrites the `0.9996` argparse default
under `--task S2C`); **u = 0.8**, **τ = 0.4**, **a = 0.9**, **b = 0.3**, **c = 0.5**;
`L_ES = 0.9·L_EA + 0.3·L_SW` (Eq. 6–8, `Explanations/MEAN_TEACHER.md`); `total_step` **253**/**127**;
2 rounds.

**Prerequisite flagged:** the generator's mechanism (`n_super_pix: 16`, `LMP`, `self.fuse`) lives in
`LAKE-RED/`, which has **zero tracked files and no submodule gitlink** (separate repo at `ed14bd4`).
Under the rebuild's own rule no `ddpm.py` line is a committed artifact. Either pin LAKE-RED as a
submodule before drafting §3, or cite it as an external dependency at that upstream commit.

**To appendix:** pretraining ids + SHA-256, interpolation, ε, tie-breaking, Sobel kernels,
`n_super_pix`, the six `MyTrain.py` patches.

### 4 Setup and pre-registration — T1
Endpoints: **COD10K-test primary**, **NC4K secondary (reported, never decides)**, **CHAMELEON
withdrawn** → forward-ref §7, **CAMO selection-only, never an endpoint**. Seeds {42,43,45}; 2
architectures; 24 runs; arms A0/A2/B/C10.

Rule quoted verbatim from `PREREGISTRATION.md` §1 (committed before run 1; the file states the
campaign is void if §1 changed after any Sα existed):
`REAL EFFECT iff Δ > 2σ̂ AND sign 3/3` · `WITHIN NOISE iff |Δ| ≤ 2σ̂` ·
`REAL REGRESSION iff Δ < −2σ̂ AND 3/3` · `INCONCLUSIVE iff |Δ| > 2σ̂ but sign not 3/3 → report as-is,
do NOT add seeds`. **No p-value at n = 3.** σ̂ = pooled within-arm sd of Sα across arms, **df = 8**.
Gates: 1st `EXP ABC` block, **16** thresholds, all PASS (note `ABC_RESULTS.md` says 15 — use 16, the
log wins; discrepancy already recorded in `REBUILD_FINDINGS.md` §6).

### 5 The null — T1 — **Table T1**
**Δ(C−B) is WITHIN NOISE in all four architecture × endpoint cells.** From `abc_verdict.json` (gap
keys `"B->C10"`, `"A2->B"`, `"A0->A2"`, `"A0->B"`, `"A0->C10"`), `abc_sigma.json`, `abc_metrics.csv`
(primary metric = column **`Sm`**), 3rd `EXP ABC` block:

| cell | Δ(C−B) | sign | σ̂ | 2σ̂ | verdict |
|---|---|---|---|---|---|
| SINet \| COD10K **(primary)** | +0.005034 | 3/3 | 0.008966 | **0.017933** | WITHIN NOISE |
| SINetv2 \| COD10K | −0.000399 | 2/3 | 0.006129 | 0.012257 | WITHIN NOISE |
| SINet \| NC4K | +0.002110 | 3/3 | 0.004155 | 0.008309 | WITHIN NOISE |
| SINetv2 \| NC4K | +0.000946 | 2/3 | 0.005267 | 0.010534 | WITHIN NOISE |

Arm means ± per-arm sd (Sα), primary cell: A0 0.700950±0.017266 · A2 0.707679±0.001930 ·
B 0.713447±0.001807 · C10 0.718481±0.004059. All 16 cells independently recomputed from
`abc_metrics.csv`, matching to 6 dp. Δ(B−A2): +0.005768 / +0.002967 / +0.003694 / +0.000729.

**Verdict census across all 20 gap tests:** WITHIN NOISE ×18, INCONCLUSIVE ×1, **REAL EFFECT ×1**.
`REAL REGRESSION` never occurs.

**The one REAL EFFECT is inadmissible and must be named as such.** It is `SINet | NC4K`, `A0→C10`,
Δ = +0.010892, 3/3 — a **secondary** endpoint the pre-registration says never decides, against
**A0, the unclean control** (22 % exposure advantage). `ABC_RESULTS.md:71-74` already warns these
"must not be read as support." The draft reports it in the limitations sentence only, never in prose
as a positive finding.

**Power — both halves, adjacent, mandatory.** `PREREGISTRATION.md` declared the design able to
resolve "~half the paper's MT→Ours gap (0.0142) and no smaller." Measured `2σ̂ = 0.017933` **exceeds**
0.0142: realised bar ≈ **1.3×** the reference gap. **Underpowered against its own pre-registered
statement.** 0.0142 reconstructs as Sα 0.7172 − 0.7030 from
`Eval/Eval/eval_txt/SINet/{S2C/10Aug_eval.txt,S2C_MT/12Aug_eval.txt}`. σ_seed is
`UNVERIFIED-DEFERRED` (C3 unrun); the old response-rate anchor `0.00867 Sα/SD` was **discarded as
non-derivable** and may not be reintroduced. Pre-reg §2.7 pre-authorised a rising bar, so this is
disclosed, not a protocol breach.

**Trap:** `Eval/.../SINet-v2/S2C/` contains two files suffixed `_incorrect` (Sα 0.2816 / 0.2733).
Valid file is `12Aug_eval.txt` (0.6999). Never read the others.

### 6 Why it fails: five causes (+ A3) — **Table T2**

| # | Cause | Verified quantity | Tier | Source |
|---|---|---|---|---|
| i | Pinned budget; added data **dilutes** | `total_step` 253/127 pinned in both rounds of all 24 runs (`abc_runs.csv` `total_step_set`, `rounds=2`); A0 exposure **0.9103** vs **0.7432** (A2/B/C10) = **+22 %** (log) / 22.5 % (audit); renders enter ≈**18.4 %** of round-1 gradient content | **T1** | 2nd `EXP ABC` block `:1364`, `:1369`; `POOL_MECHANICS_AUDIT.md` §7(a) |
| ii | Generator conditioning bottleneck | **`[TODO: verify — A1 unrun; contradicted as a bound]`** | **T1** | none |
| iii | Foreground exhaustion | Bijection onto 4447 raw foregrounds (0 outside, 0 unrendered); `--isReplace` composites object pixels back — interior err **5.603**/**9.633** vs background **70.802**/**70.555** (ratios 12.64/7.32); **0** objects with interior err > 40 | **T1** mechanism / **T2** consequence | `EXP D1`; `D1_RESULTS.md` §3.1-3.2 |
| iv | Diffuse target clusters | Silhouette peak **0.1600** @ k=75 (dinoL518); dinoL224 **0.1465** @ k=50; clipL224 **0.0568** @ k=5. Threshold *"weak cluster structure is embedder-robust: peak below 0.25 in every space"* → **PASS** | **T2** | `EXP B1` blk 3 `:967`; `b1_k_sweep*.csv`, `b1_embedder_sweep.{csv,json}` |
| v | Signal contributes negligibly | Attribution audit 2/7 PASS, 5 FAIL; destroying targeting while keeping allocation *shape* reproduces the same `d` → **REOPENS-BUT-NOT-BY-TARGETING** | **T2** | 4th `EXP C1` block; `C1_RESULTS.md` §8 |

**Cause i — dilution, never exclusion.** Both loaders are `shuffle=True`, so added data *is* sampled;
it uniformly reduces every image's per-epoch exposure. `POOL_MECHANICS_AUDIT.md` §7(a) explicitly
corrects the looser framing and notes that under exclusion Stage B/C would be provable no-ops. Two
constraints: (a) the audit's "19,734 steps / 315,744 images" is **SINet-only** (SINet-v2 is 25,146 /
804,672) — must be qualified; (b) `POOL_MECHANICS_AUDIT.md` has **no `EXP` log block**, so its *new*
numbers (round-2 exposure, the 19.3 % round-2 advantage, 13.3 % round-2 render share) are outside the
authoritative log. They reproduce from committed `abc_runs.csv` but the paper should prefer the logged
round-1 figures and mark the round-2 ones `[TODO: verify — not logged]`.

**Cause iv caveat.** A companion threshold **FAILS**: clipL224's silhouette falls monotonically to
0.0357 at k=150, so its peak is at the **grid edge**, not an interior maximum. Report the PASS and the
FAIL together. Also: B1's log NOTES prose describes the k-criterion as max bootstrap ARI, while the
METRICS line and `b1_embedder_sweep.json` say max silhouette with ARI `discarded_criterion` — the
artifacts and `B1_RESULTS.md:184` agree on silhouette; the NOTES prose is stale. Matters because ARI
would have selected k=5, not k=75. Cite the artifacts.

**A3 — sixth item, T2, comparative form only.** The publishable form is A3's own: *a different real
camouflage dataset covers the target manifold at **0.79–0.90**, real photographs of another genre at
**0.71–0.75**, while synthetic images generated from those very photographs cover it at
**0.13–0.54**.* The vacuity control is **mandatory**: the declared flag **fired** — a JPEG-30
re-encode of the *identical* images separates them from themselves at **0.9928** (clipL224) against a
headline of 0.9993, exceeding both real controls (NC4K 0.9381, COD10K-vs-CAMO 0.9225). A3's own limit
must be quoted: *"a distributional characterization, not a training-utility bound"* — arm means in
fact rose **monotonically** in all four cells. **Absolute "far from real" phrasing is forbidden.**

### 7 Contamination audit and clean protocol — **top-level section, T3** — **Table T3**

- **Headline: 41 / 76 = 53.9 % of CHAMELEON are re-encodes of the training pool.** Established by
  **`EXP D2`** (first logged blk 3 `:468`; authoritative blk 5 `:628`), **re-verified by `EXP D2R`**
  against an author-sourced copy: 41/76, `OLD CLAIM → MATCH`, delta 0 (`:1867`, `:1977`). The two
  copies are byte-identical, 76/76 (`:1851-1853`).
- **Partner split (D2R only):** **40** in COD10K-train, **1** in CAMO (`animal-57.jpg ↔
  camourflage_00836.jpg`), **0** elsewhere — the pool is only COD10K-train + CAMO (`:1941-1942`).
- **Methodological strength to foreground:** D2 corrected *itself* from 10/76 (13.2 %, blocks 1–2,
  contrast-normalised 16×16 thumbnails) to 41/76 once the exhaustive within-dimension search replaced
  it — a **+40.7 pp** self-correction (`:331`, `:399` → `:468`; `D2_RESULTS.md` §3.2).
- **Exact hashing finds nothing.** CHAMELEON ∩ training pool = **0** byte, **0** decoded-pixel
  (`:610`). This is the trap: hashing declares a 53.9 %-contaminated set clean.
- **Detection method** (`detect_contamination.py`, 547 lines, numpy+pillow only): exact `(w,h)`
  grouping → 32×32 grey BILINEAR 1024-d descriptor, **no contrast normalisation** (the rejected
  normalisation is precisely D2's recall bug) → Gram-matrix shortlist at `rms ≤ 14.0` → **confirm iff
  `mean|A−B| ≤ 6.0`** on full-resolution int16 RGB. Complexity: 23,854 images → 4,427 dimension
  groups → 7.4 M candidate pairs → **323** shortlisted. Self-test: 8 assertions, no repo data,
  `detector_selftest = PASS` (`:1943`); reproduces the in-repo result 41/41 pairs and names
  (`:1944-1945`).
- **The criterion is a *mean*, not `maxdiff == 0`.** The 41 pairs have `max_abs` from 13 to 70, so a
  maxdiff test rejects all of them. The three levels (byte / decoded-identical / near-dup) are
  **disjoint by construction** in the sweep (`d2_leakage_sweep.py:259-260` skips phash-equal pairs).
- **Tolerance-independent corroboration:** nearest-neighbour gap — 41 below **5.512**, next at
  **40.577**, ratio **7.36×**; the other three endpoints show **no** gap (`:1884-1898`).
- **Clean protocol** (cite `CLEAN_PROTOCOL.md`, **not** the release copy — see below): report
  **COD10K-test + NC4K** with the on-disk-copy caveat; **do not report CHAMELEON** as an independent
  endpoint (if at all, on the named 35-image uncontaminated subset, stating the mask release); never
  report the checkpoint-selection set (CAMO) as an endpoint; run the detector on your own directories
  first.

**Four hazards this section must handle explicitly:**

1. **No inflation effect exists, and claiming one is contradicted.** D2 on the 7 exact COD10K-test
   duplicates: removing them moves MAE by **−1.242e-05** (−0.0167 %), percentile **0.4761**. D2R on
   CHAMELEON leaked-vs-clean: all eight percentiles in **0.448–0.559**, Mann–Whitney *p* 0.47–0.99,
   and `split_direction_agrees_across_mask_sets = **False**` — the sign flips between mask releases.
   `CLEAN_PROTOCOL.md:145-148` is the sentence to quote: the conclusion is *"about **independence, not
   inflation** … Claiming a specific inflation figure would be over-reading it."* `:1990` forbids
   quoting the D2R inference run as a performance number at all.
2. **Our own clean protocol understates COD10K-test by 4.4×.** `CLEAN_PROTOCOL.md:34` reports
   `2/2026 (0.1 %)`, which is the near-duplicate count only; the **7** byte/pixel-identical duplicates
   are disjoint from those 2 (verified: no overlap between the 7 names in `d2_leaked_names.json` and
   the 2 in `d2_endpoint_contamination.json`). True total is **9/2026 = 0.44 %**. The paper reports
   **9/2026** and states the correction. `[TODO: fix CLEAN_PROTOCOL.md:34 upstream]`
3. **CHAMELEON ∩ COD10K-test = 32 (42.1 %) is artifact-only.** Present in
   `d2_endpoint_contamination.json` / `d2r_endpoint_contamination.json` as `vs_other_endpoint`, but in
   **no log block and no document**. It is a strong finding and it lacks the traceability the rest of
   this work requires. Either log it before use, or carry it as
   `[TODO: verify — artifact-only, unlogged]`.
4. **Cite `CLEAN_PROTOCOL.md`, not `release/CLEAN_PROTOCOL.md`.** The release copy drops the entire
   `EXP D2_NC4K` section including the "COD10K-test ∩ COD10K-train = 7" sentence, simplifies the NC4K
   row, and attributes everything to D2R alone. The release bundle is the **weaker** document.
   `[TODO: reconcile release/CLEAN_PROTOCOL.md upstream]`

**Also to state:** threshold **T5 FAILED** and was left failing — `animal-19.jpg` and `animal-28.jpg`
are **PNGs carrying `.jpg` extensions**, so they carry no JPEG quantization table, and D2's PIL `!=`
comparison read a missing table as a differing one. D2's "41/41 qtables differ" is corrected to
**40/41 differ + 1 not-applicable**. The replacement **T5b PASSES**: every confirmed pair carries
re-encoding evidence from some independent channel — 40 by quantization table, 1 by container format
(413 KB PNG vs 132 KB JPEG). The count never depended on quantization tables.

**Separately measured and larger:** the **mask-release choice alone** moves CHAMELEON MAE by **2.7×**
(0.219648 vs 0.081631) on *identical* predictions; mean IoU 0.6932 after polarity alignment, 0.0 as
stored, only 27/76 identical (`:1858-1866`). Worth a sentence — it is a benchmark-integrity finding in
its own right.

### 8 Conclusion
Restate the null with tiers. "What a working system would require": a regime that scales optimisation
with data (cause i) · a non-exhausted foreground source (cause iii) · a boundary-aware signal
(causes iv–v) · a steerable / text-conditioned generator (cause ii, *if* A1 ever substantiates it).
RealCamo and the Oracle are **scoped future work, not results**. Close on the clean protocol's lasting
value. Sources: back-references plus `REBUILD_PLAN.md` §3 (A1/A2/C3 objectives, unrun).

### AI use statement — required, non-page-limited, ≤ 1 page
Honest disclosure of LLM use in analysis, drafting and editing, on the template's own skeleton.
`[TODO: author to finalize wording]` — human-verified, never auto-asserted.

---

## 5. Tables

**T1 — main result (§5).** Rows: arm × architecture × endpoint. Cols: Sα mean ± per-arm sd; Δ(C−B);
Δ(B−A2); 2σ̂; verdict. Source: `abc_metrics.csv` (col `Sm`), `abc_sigma.json`, `abc_verdict.json`,
3rd `EXP ABC` block. **Quote gaps and σ̂ from `abc_verdict.json`** (full precision) not the 6-dp CSV,
and say so — recomputing from the CSV shifts Δ by ~1e-6.

**T2 — dissection summary (§6).** One row per cause: cause · measured quantity · tier · source block.
Five rows + A3. Cause ii's quantity cell is `[TODO: verify]`.

**T3 — contamination (§7).** Panel A: per-benchmark, exact / near-dup / total / share / NN gap —
CHAMELEON 0/41/**41**/53.9 %/gap 7.36× · COD10K-test 7/2/**9**/0.44 %/none · NC4K 0/1/**1**/0.0 %/none
· CAMO-val 0/4/**4**/1.6 %/none · NC4K∩COD10K-test 0/0/**0**/0 %/none. Panel B: CHAMELEON tolerance
sweep at tol 1/2/3/5/6 → **11/26/37/40/41**, identical for both copies. Panel C (optional): TOPK
∈ {8, 32, all} → 41 at all three, gap 7.36× throughout. Sources: `EXP D2` blk 5, `EXP D2R` blk 4,
`EXP D2_NC4K` blk 2. Rows sourced artifact-only are footnoted as such.

**T4 — cluster quality (appendix).** Silhouette across k ∈ {5,10,15,20,30,50,75,100,150} × 3
embedders. dinoL518: 0.0566 / 0.0923 / 0.1152 / 0.1326 / 0.1527 / 0.1556 / **0.1600** / 0.1557 /
0.1507. Source: `EXP B1` blk 3, `b1_k_sweep*.csv`.

Every caption names its source artefact. **Final reconciliation pass:** every in-text number checked
against its table cell at identical rounding, and every table number checked against its log block.

---

## 6. To the appendix

Implementation minutiae (pretraining ids + SHA-256, interpolation, ε, tie-breaking, Sobel kernels,
`n_super_pix`, the six patches) · T4 silhouette sweep · threshold ledger (143 declared / 127 PASS /
16 FAIL over cited blocks, `REBUILD_FINDINGS.md`) · per-run accounting for 24 runs · CLS round-2
append counts and their 22.2 %-of-mean spread · secondary metrics (wFm, Em, MAE) · D2/D2R
reconciliation and the mask-polarity finding · determinism evidence · the 132-pair split
decomposition.

---

## 7. Marker inventory the draft will carry

**`[TODO: verify — source needed]`**
1. Cause ii, the 48-scalar conditioning bound (A1 unrun; contradicted as a bound — see §9).
2. `POOL_MECHANICS_AUDIT.md` round-2 numbers (19.3 %, 13.3 %) — not in any log block.
3. CHAMELEON ∩ COD10K-test = 32 / 42.1 % — artifact-only, unlogged.
4. Tolerance-sweep rows for COD10K-test / NC4K / CAMO-val (1/1/2/2/2 · 0/0/0/1/1 · 0/1/2/3/4) —
   artifact-only, unlogged.
5. Raw-HKU-IS pixel-level internal duplicates (90 redundant / 4357 unique) — artifact-only.
6. Detector wall-clock runtime — **no committed source**; complexity only.
7. Whether the published S2R-COD paper reports a CHAMELEON column — `UNVERIFIED` by design, PDF not
   in the checkout.
8. Author-sourced re-audit for COD10K-test / NC4K / CAMO — explicitly **owed and not done**.
9. σ_seed — `UNVERIFIED-DEFERRED` (C3 unrun).
10. `[TODO: author to finalize wording]` — AI use statement.
11. `[TODO: fix upstream]` — `CLEAN_PROTOCOL.md:34` (2/2026 → 9/2026); `release/CLEAN_PROTOCOL.md`
    reconciliation; `REVISION_TABLE.md:201`'s reliance on the unsupported 48-scalar leg.

**`[CITE: …]`** — no reference invented; a later deep-research pass fills these.
`[CITE: COD10K]` `[CITE: NC4K]` `[CITE: CAMO]` `[CITE: CHAMELEON]` `[CITE: SINet]`
`[CITE: SINet-v2]` `[CITE: SegMaR]` `[CITE: S2R-COD]` `[CITE: LAKE-RED]`
`[CITE: camouflage generation other]` `[CITE: diffusion inpainting]` `[CITE: mean teacher]`
`[CITE: domain adaptation seg]` `[CITE: active learning survey]` `[CITE: uncertainty sampling]`
`[CITE: core-set selection]` `[CITE: generative active learning]` `[CITE: synthetic data scaling]`
`[CITE: negative results venue]` `[CITE: train-test contamination]` `[CITE: dataset duplication]`
`[CITE: pre-registration in ML]` `[CITE: silhouette]` `[CITE: DINOv2]` `[CITE: CLIP]`
`[CITE: MMD]` `[CITE: precision-recall generative]` `[CITE: DGNet eval protocol]`

---

## 8. Verification of the eventual draft

1. Grep the `.tex` for bare decimals with no adjacent source or marker — none may remain.
2. Every table cell traced to a log line number or CSV row.
3. Compile against `iclr2027/` with TinyTeX (`~/.TinyTeX`, already installed); add `graphicx` + `tikz`.
4. Page count ≤ 9 with the AI use statement and references excluded.
5. Confirm no `_incorrect.txt` eval file was read; confirm `Sm` (not MAE) is the reported metric.

---

## 9. (a) Claims the paper wants that are NOT backed by a committed artifact

| Claim | Status |
|---|---|
| **"The generator's conditioning channel is 48 scalars"** | **Worse than unsourced — contradicted as a *bound*.** The LMP path does give 16×3, but `self.fuse = nn.Conv2d(6,3,1)` computes `fg2bg = self.fuse(cat((vec_bg, fg)))` and `new_fg = fg*(1-mask) + fg2bg*mask`, so raw `fg` enters at full resolution. The decisive sub-check (`fg[mask==1]` identically zero) is claim A1.4, logged *never tested*. Cannot be asserted. |
| Any **inflation** of reported scores by contamination | **Actively contradicted** by `d2r_impact.json` / `d2_mae_impact.json`. Must not be claimed. |
| "Published CHAMELEON results are compromised" | Requires knowing the published paper reports CHAMELEON — `UNVERIFIED`, PDF absent. |
| CHAMELEON ∩ COD10K-test = 32 (42.1 %) | Artifact-only; no log block, no document. |
| Contamination rates for COD10K-test / NC4K / CAMO as *author-verified* | Measured on on-disk copies only; re-audit **owed**. |
| σ_seed / any seed-variance figure | `UNVERIFIED-DEFERRED`. |
| A response rate translating pool shift → Sα | **Discarded as non-derivable**; must not be reinvented. |
| Round-2 exposure figures (19.3 %, 13.3 %) | Reproducible but unlogged. |
| Detector runtime | No committed source. |
| Anything cited to `ddpm.py` | `LAKE-RED/` is untracked — not a committed artifact. |
| Every related-work reference | None exist yet; all `[CITE:]`. |

## 9. (b) The section most at risk of overclaiming

**§7, the contamination audit** — not §5 or §6.

It is the paper's most quotable result, it is T3 and therefore feels unassailable, and the natural
next sentence after "53.9 % of CHAMELEON is training data" is *"therefore reported CHAMELEON scores
are inflated"* — which the artifacts **measured and contradicted**. It also inherits two defects from
our own documents: `CLEAN_PROTOCOL.md:34` understates COD10K-test by 4.4×, and the release copy is
weaker than the repo copy.

How the plan constrains it: (i) the section states the conclusion as **independence, not inflation**,
quoting `CLEAN_PROTOCOL.md:145-148`, and reports the null impact measurements as results in their own
right; (ii) it reports **9/2026** for COD10K-test and flags the upstream fix; (iii) it cites the repo
protocol, never the release copy; (iv) it carries the T5 failure and its T5b replacement rather than
hiding a failed threshold; (v) it makes no claim about the published paper's tables; (vi) every
artifact-only number carries a `[TODO]`.

Runner-up: **§6 cause ii**, constrained by being reduced to a `[TODO]` with the counter-mechanism
named in the text, so a reader cannot mistake it for a measured bound.

## 9. (c) Confirmation

**No number will be written into the `.tex` that is not traceable to a committed source.** Every
figure in this plan carries its block line number, CSV column, or `.md` section. Where a number the
paper wants does not exist, it appears in §9(a) and will appear in the draft as a `[TODO: verify]`
marker, never as a value. Where an artifact contradicts a desired claim — the 48-scalar bound, score
inflation — the plan records the contradiction and forbids the claim. Related-work references are
`[CITE:]` markers; not one will be fabricated.

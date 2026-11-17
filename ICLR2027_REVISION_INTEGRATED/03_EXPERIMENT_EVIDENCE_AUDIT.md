# 03 — Experiment evidence audit and source-of-truth ledger

Audited 2026-11-17, 20:40–21:30 IST, on branch `rebuttal/iclr27/merged`.

- Every number added to the paper or the replies is recomputed from its source artifact by
  `tools/verify_numbers.py`; output is in `tools/verify_numbers_output.txt`. The current run passes **92 checks with 0 failures**.
- The reviewer-ready prose in each package was treated as a claim to verify, not as evidence.

Status words:
- **VERIFIED**: recomputed from committed data and the protocol confirmed.
- **PARTIAL**: verified, but the planned scope was not completed.
- **UNRESOLVED**: not run, or no evidence.
- **CONTRADICTED**: the evidence contradicts a statement we had made.

Package roots used below:
- `RL5B/` = `rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/`
- `Caus/` = `rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/`
- `dypE/` = `rebuild/REBUTTAL/ICLR2027_REBUTTAL_dypE/STUDENT_RESULTS/`

## 1. Experiments and analyses

| ID | What | Protocol (data · split · seeds · metric) | VAL or TEST use | Status | Evidence |
|---|---|---|---|---|---|
| **EQ** (RL5B EXP-01) | Confirmatory equivalence test, C10 vs B (H1) and vs CSHUF (H1b) | SINet; COD10K-test primary, NC4K secondary; seeds 101–127 planned, completed 16/15/15 (B/C10/CSHUF); $S_\alpha$; Welch TOST at ±0.005 | TEST is the endpoint only. Checkpoints are selected on CAMO-250 MAE; no interim looks (Amendment 1 §7) | **PARTIAL**: pre-registered and INCOMPLETE (46 of 81 runs); H1 equivalent, H1b neither | `RL5B/RESULT_TABLES/EXP01_EQ.csv`, `EXP01_EQ_summary.json`, `RL5B/prereg/EQ.md` (Amendment 1), queue log `rebuild/RL5B/out/queue_events.jsonl` |
| **CDR** (RL5B EXP-02) | Dose-response over three concentration levels | SINet; N = 1000; 35 new runs (uniform 5 seeds; two levels × 5 permutations × 3 seeds) plus SE's B; Boundary-IoU@0.5 on COD10K-test | TEST endpoint only | **PARTIAL**: SINet done and not supported; the SINet-v2 replication was not run | `RL5B/RESULT_TABLES/EXP02_SINet_results.md`, `EXP02_SINet_summary.json`, `RL5B/prereg/CDR.md` |
| **E3** (RL5B EXP-03) | Protocol-matched baselines and gap decomposition | Released SINet-V2/RISE maps re-scored (12 values, max diff 0.0005); our trainer on real masks, 3 seeds × 2 architectures, single round | TEST endpoint only | **PARTIAL**: E3-b (official recipe retrain) and E3-e (our recipe on RISE masks) not run | `RL5B/RESULT_TABLES/EXP03_protocol_matched.csv`, `EXP03_gap_decomposition.md` |
| **AN01** (RL5B) / **AN-03** (dypE) | Boundary metrics re-scored on all 64 eight-seed runs | Both architectures and endpoints, thresholds 0.4/0.5/0.6; the 3-seed values reproduce exactly | post hoc, decides nothing | **VERIFIED**. Two packages reach the same numbers independently. **CONTRADICTS** the submission's three-seed boundary claim, which is now withdrawn | `RL5B/RESULT_TABLES/AN01_boundary_8seed.csv`; `dypE/RESULT_TABLES/AN-03_arch_boundary_grid.csv`, `AN-03_interaction.csv` |
| **TH01** (RL5B) / **TH-01** (dypE) | Intervals, TOST and rule power for the 16 eight-seed contrasts; paired analysis | Eight seeds {42, 43, 45–50}; Welch and paired | post hoc | **VERIFIED**. The posted 0.14 / 0.008 / σ̂ 0.00345 are **CONTRADICTED** (correct: 0.20 / 0.0087 / 0.00343) | `RL5B/RESULT_TABLES/TH01_contrasts.csv`, `TH01_power.csv`; `dypE/RESULT_TABLES/TH-01_paired_inference.csv` |
| **ORS** (Caus EXP-01) | Oracle allocations of three other shapes, plus a same-shape shuffle | SINet; seeds 42/43/45; 12 new runs; committed B/C10/CORACLE reused after a reuse gate; $S_\alpha$; bar over 7 arms, df 14 | Allocation reads **COD10K-test labels** (leaky diagnostic, as with CORACLE); NC4K is read by no allocation | **VERIFIED**: all four pre-registered contrasts within noise on both endpoints | `Caus/RESULT_TABLES/EXP-01_comparisons.csv`, `EXP-01_metrics_by_seed.csv`, `EXP-01_runs_of_record.csv`; pre-registration commit `b21b67c` |
| **AN-02** (Caus) | Probe and effective-rank reproduction; shapes through the selector | Frozen embeddings; N = 1000; 20 random draws; R2/R3 representations | none | **VERIFIED**. **CONTRADICTS** the manuscript's "the probe was detecting the concentration the whole time": a flat quota gives d = 0.52 | `Caus/RESULT_TABLES/AN-02_shape_geometry.csv`, `AN-02_probe_geometry.csv`; `Caus/EXPERIMENT_LOGS/AN-02_audit.md` |
| **AN-03** (Caus) / **AN03** (RL5B) / **AN-04** (dypE) | Foreground provenance, reuse and coverage | 4,447 renders, 8,885 traced objects; k-NN recall at k = 3/5/10/20; selection-level coverage | none | **VERIFIED**. The manuscript's 0.13–0.54 is at k = 5, previously unstated | `Caus/RESULT_TABLES/AN-03_coverage_and_qc.csv`; `RL5B/RESULT_TABLES/AN03_foreground_diversity.csv`; `dypE/RESULT_TABLES/AN-04_foreground_coverage.csv` |
| **AN-02** (dypE) | Realised overlap, exposure, pseudo-label overlap | Selection records of all 64 runs | none | **VERIFIED**. **CONTRADICTS** the posted 48% / 8.8% for the decisive comparison (correct: 77% / 14.1%) | `dypE/RESULT_TABLES/AN-02_overlap_by_seed.csv`, `AN-02_exposure_by_run.csv`, `AN-02_pseudolabel_overlap.csv` |
| **EXP-01** (dypE) | Larger-budget preflight | Exact selector at N = 1000/2000/3000/4447; pre-specified 1.5× gate | none | **VERIFIED**: the preflight fails, so nothing was trained | `dypE/RESULT_TABLES/EXP-01_preflight.csv` |
| **AN-05** (dypE) + Caus crosscheck | CHAMELEON re-audit, cross-benchmark and protocol exposure | Released detector unchanged; Tier A/B; COD10K-test, CAMO-250, NC4K | none (CHAMELEON is not an endpoint) | **VERIFIED**, with the reconciliation in §3 | `dypE/RESULT_TABLES/AN-05_*.csv`; `git show 5e7a2f9:rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/RESULT_TABLES/AN-05_chameleon_crosscheck.csv` |
| **RECHECK** (RL5B) | Same-seed re-trains (C10 s42, CSHUF s115) | 2 runs | none | **VERIFIED, exploratory**: training is not reproducible run to run. Reported in App. C only (constraint 3) | `RL5B/EXPERIMENT_LOGS/RECHECK.json`, `RL5B/EXPERIMENT_LOGS/RECHECK_sensitivity.log` |
| D2 | COD10K-test files byte-identical to COD10K-train files | Full pairwise hashing | none | **VERIFIED**: 7 files; disclosed in App. F (author decision Q2) | `rebuild/D2/out/d2_leaked_names.json`; `RL5B/EXPERIMENT_LOGS/split_overlap_check.log` |
| Modern detector (Caus EXP-02) | CamoFormer / CTF-Net replication | — | — | **UNRESOLVED (blocked)**: no training code / no licence; released weights trained on our target images | `Caus/EXPERIMENT_LOGS/` blocker records |
| Foreground-varying generator (Caus EXP-03/04; dypE QA-02) | — | — | — | **UNRESOLVED (blocked)**: no generator with released code changes the foreground | `Caus/EXPERIMENT_LOGS/`, `dypE/EXPERIMENT_LOGS/EXP-03_BLOCKER.md` |
| Higher operating point (RL5B EXP-04) | — | — | — | **UNRESOLVED**: dropped before launch for lack of compute | `RL5B/EXECUTION_STATUS.md` |

**Post-review training count.** 99 trained runs: EQ 46, CDR 35, E3 supervised references 6, ORS 12. In addition, 1 bridge run and 2 same-seed re-trains were used only as checks. Counted from `rebuild/RL5B/out/queue_events.jsonl` (`job_done` events) and `Caus/RESULT_TABLES/EXP-01_runs_of_record.csv`.

## 2. Pre-registration timing (constraint 8)

Each commit was checked with `git cat-file`, and reachability from HEAD with `git merge-base --is-ancestor`. First-run times come from the run logs.

| Rule | Commit (date) | First run | Before its runs? | Reachable |
|---|---|---|---|---|
| ABC | `065dac6` (09-04) | — | as recorded | yes |
| T2 | `617a2e1` (09-10) | — | as recorded | yes |
| T2C | `6efde9f` (09-11) | — | as recorded | yes |
| AC, PC | `c2114af` (09-13 12:48) | — | as recorded | **no**, except through the new local tag `prereg-ac-pc-c2114af` (author decision Q3) |
| SE, FX | `a79886a` (09-18 11:48) | FX 09-18 18:23; SE 09-20 | yes | no, except through tag `prereg-or-fx-se-a79886a` |
| OR | `a79886a` (09-18 11:48) | **10:46** (first score 18:23) | **no: committed 62 min after the first run started**, before any score | tag |
| The submission cited SE at `b755aa9` | `b755aa9` is dated 09-13 and is the AC/PC results commit | — | **wrong citation, corrected** | yes |
| EQ, CDR | `2137849` (11-09 08:13) | CDR 11-11 18:26; EQ 11-13 23:59 | yes | yes |
| EQ Amendment 1 (n = 27; INCOMPLETE rule) | `808988b` (11-11 21:16) | EQ 11-13 23:59 | yes | yes |
| ORS | `b21b67c` (11-11 23:55) | pilot `cebf128` 11-12 00:01; runs placed 11-12 12:56 | yes | yes |

## 3. CHAMELEON: reconciling the packages' counts (constraint 6)

| Source | Training-pool matches | Other counts | Status now |
|---|---|---|---|
| Submitted paper | 50 (41 Tier A + 9 Tier B; 44 in COD10K-train), 16 unchecked, 10 "clean" | 3 byte-identical in CAMO-250 | the floor stands |
| Caus package, `5e7a2f9` (11-12) | 51: animal-54 is a rescaled copy of COD10K-train Spider-2513 (880×660 vs 900×675, dHash 2, MAD 0.92/255), visually confirmed | — | dropped by author decision on 2026-11-17 morning; **reinstated by `AUTHOR_REVISION_CONSTRAINTS.md` item 6** as one manually confirmed match |
| dypE package (AN-05) | 50 reproduced exactly; animal-54 recorded as `tierA_checked_no_match` (Tier A needs equal dimensions; Tier B never scored it) | 32 COD10K-test re-encodes (all 16 unchecked, 8 of the 10 "clean", 8 confirmed); 4 in CAMO-250 (animal-17/-25/-60 byte-identical, animal-28 re-encoded); 74/76 duplicated somewhere | all reproduced by `verify_numbers.py` |
| **Revision (this integration)** | **at least 50** automated (abstract, intro, conclusion); **51** in total (§3.4, App. F, Table 17) | 32 COD10K-test; 4 CAMO-250; **75/76** duplicated somewhere (74 + animal-54); no duplicate found for only animal-38; 25 without a training-pool partner, 24 of them COD10K-test | consistent across the paper and the dypE reply |

The pair image for animal-54 can be recovered with:
`git show 5e7a2f9:rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/FIGURES/AN-05_chameleon_animal54_vs_COD10K-train_Spider-2513.jpg`
It was removed from the working tree in `73c18d6`.

## 4. Cross-package contradictions found and how they were resolved

| # | Contradiction | Resolution |
|---|---|---|
| C1 | The Caus and dypE drafts say "±0.005 equivalence not met (p = 0.101)"; RL5B's EQ establishes it | Both are true for different campaigns. The paper and all replies now state the eight-seed result and the confirmatory result side by side (Table 3). |
| C2 | The dypE draft proposed "gains above ≈0.007 excluded, smaller ones not" for the abstract and conclusion | Superseded on SINet's primary cell by EQ. The SINet-v2 cells (eight seeds only) are stated as not excluding gains ≤0.005 in the dypE reply and Table 9. |
| C3 | CHAMELEON 50 / 51 / 74 across packages | Reconciled in §3; Table 17. |
| C4 | Probe "concentration the whole time" vs a flat quota at d = 0.52 | Author chose "matching + concentration" (Q1). Abstract, intro, §3.2, §3.3, discussion, conclusion, Fig. 2 caption. |
| C5 | Fig. 2 caption: "only destroying concentration collapses it" | Corrected: only a random draw collapses it. |
| C6 | The posted 8.8% vs the measured 14.1% for the decisive comparison | Corrected in App. C and the dypE reply; 8.8% is kept for the concentrated arms (8.3–9.4%). |
| C7 | The posted boundary ratios 1.37× / 1.34× vs 0.30× / 0.64× | Corrected in §3.2, Table 8, and the RL5B and dypE replies. |
| C8 | The Caus initial response said boundary effects "depend on architecture"; the interaction is not resolved | Corrected in the Caus reply. |
| C9 | RL5B `table_protocol.tex` shows SINet C10 COD10K $S_\alpha$ = 0.718; the exact mean is 0.717479 | Double-rounding fixed to 0.717 in Table 4 and the RL5B reply; check added. |
| C10 | The `RL5B/revision/eq_result.tex` sentence omits CSHUF's seed count; the conclusion said "15–16 of 27" | Replaced by explicit 16/15/15 text everywhere (constraint 3). |
| C11 | The RL5B draft said the confirmatory n was "fixed in advance" | Corrected: 29 capped to 27 before any run (Amendment 1, `808988b`). |
| C12 | The dypE draft claimed "the same ordering in the other two spaces" for selection coverage | Not true in clipL224, where the ranges overlap. The paper says so. |
| C13 | The CDR pre-registered decision sentence says "concentration explains why targeted training sets look different" | Kept verbatim. Constraint 4 requires the pre-registered sentence, and it remains true; the matching qualifier is stated in §3.2 and App. I. |

## 5. Leakage and protocol checks

- No TEST information enters selection or tuning in EQ, CDR or E3. Checkpoints are selected on CAMO-250 MAE, as in every campaign.
- EQ forbade interim looks at endpoint metrics (Amendment 1 §7), and its analysis ran once, after the cutoff.
- ORS and CORACLE read COD10K-test labels to choose training data. They are labelled as leaky diagnostics in Table 2, §3.1 and App. I. NC4K, which no allocation reads, is reported beside it.
- Baselines in Table 4 use one scorer and the same splits. The supervised rows are an upper reference, not competitors.
- Matched evaluation: every arm and baseline is scored on the same COD10K-test, which contains 7 files byte-identical to training images (App. F).

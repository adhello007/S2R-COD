# Results summary: Reviewer Caus

**Task count: 8 of 13 tasks VERIFIED** (TH-01, TH-02, AN-01, AN-02, AN-05, EXP-01, DOC-01, DOC-02).
**1 PARTIALLY VERIFIED** (AN-03: the existing pool is verified, the new generator blocked).
**4 BLOCKED** (AN-04, EXP-02, EXP-03, EXP-04).

Paths below are relative to `STUDENT_RESULTS/`. `rebuild/CAUS/…` paths are source files in the branch,
all contained in `CODE_CHANGES.patch`.

## 1. New results (post-review)

### EXP-01: different-shape oracle (QA-01)

[EXP-01 SUMMARY]

### Geometry and the reviewer's rank premise (CW-01)
`EXPERIMENT_LOGS/TH-01_math_verification.md`, `EXPERIMENT_LOGS/AN-02_audit.md`

- **Concentration does not fix the sign of effective rank.** In exact mixture constructions, the same
  90% concentration takes the participation ratio from 3.08 (uniform) to 9.17 or to 1.21, depending on
  which cluster receives the budget (`RESULT_TABLES/TH-01_rank_constructions.csv`).
- **In the studied pool, the most concentrated selection keeps near-random rank.** OR-TOP5-SHUF (five
  clusters) has a rank ratio of 0.943. A perfectly flat quota under the same selector is still
  separable from random (held-out *d* 0.52) and has lower rank (0.855)
  (`RESULT_TABLES/AN-02_shape_geometry.csv`).
- **Consequence:** the separation is matching plus concentration. The direction of the signal adds
  nothing (+0.0073 *d*).

### Leakage and provenance audits (CW-02, CW-03, QA-01)
- **Overlap with the unlabelled target pool:** 15 COD10K-test and 32 NC4K photographs sit there as
  unlabelled images, identical for every arm. CAMO-250 shares 7 photographs with COD10K-test
  (`RESULT_TABLES/AN-05_cross_split_pairs.csv`).
- **CHAMELEON:** `animal-54` (committed verdict: clean) is a rescaled COD10K-train image, so the floor
  is ≥ 51/76 (`RESULT_TABLES/AN-05_chameleon_crosscheck.csv`,
  `FIGURES/AN-05_chameleon_animal54_vs_COD10K-train_Spider-2513.jpg`).
- **Generators:** both available camouflage generators preserve the foreground and have no released
  code. **Detectors:** CamoFormer has no training code, and CTF-Net has no licence
  (`EXPERIMENT_LOGS/AN-03_generator_audit.md`, `EXPERIMENT_LOGS/AN-04_model_integration.md`).

## 2. Historical baseline, re-derived (labelled ORIGINAL VERIFIED)

Source: `RESULT_TABLES/TH-02_historical_recompute.csv`, `AN-02_c1_reproduction.csv`,
`AN-03_foreground_provenance.csv`, `AN-03_coverage_and_qc.csv`.

| Manuscript number | Re-derived |
|---|---|
| SE C10 − B +0.0024, bar 0.0069, 6/8; 95% CI [−0.0020, +0.0067]; TOST p = 0.101 | identical (two implementations agree to 2.6e-14) |
| OR CORACLE − B +0.0008, bar 0.0061, 2/3 | identical |
| +0.0073 / −0.0649 *d*; effective-rank ratio 0.634 (20/20) | original code re-run, ≤ 3.1e-13 |
| 8,885 traced objects, 0 regenerated | independent re-measurement, identical |
| k-NN recall 0.13–0.54 (k = 5) | identical at every k; k-dependent (0.07–0.75 over k = 3–20) |
| CHAMELEON 50/76 | floor is ≥ 51/76 |

## 3. Manuscript wording recommendations (DOC-01)

The full patch, 27 edits plus one generated appendix, is `manuscript_scope_edits.patch`. Mapping:
`EXPERIMENT_LOGS/DOC-01_edits.md`. In summary:
- scope the title, abstract and conclusion to the offline LAKE-RED / S2R-COD / SINet pipeline;
- replace "perfect score" and "no score of any quality" with "at this allocation shape", and add the
  different-shape appendix;
- attribute the probe separation to matching plus concentration; name the effective-rank definition
  and the k of the coverage metric;
- **correct two provenance statements:** the OR pre-registration was committed 62 minutes after its
  first run (C-07), and SE is cited at the wrong commit (C-31);
- CHAMELEON floor ≥ 51, if the author confirms `animal-54`.

The copy compiles, and the main text stays at 9 pages (limit 10).

## 4. Materially unresolved

- **Modern detector (EXP-02) and foreground-varying generator (EXP-03, EXP-04): not run.** The null is
  bounded to SINet/SINet-v2 and LAKE-RED's fixed-foreground pool.
- **No disjoint calibration source.** Every oracle arm is endpoint-label-leaky. A calibration-label
  oracle was not attempted.
- **EXP-01 is SINet-only at 3 seeds.** Its bar is per-run noise, so effects smaller than the bar can be
  missed.
- **Not verifiable locally:** whether the manuscript matches the uploaded PDF, and whether
  `01_INITIAL_REBUTTAL_FOR_SUBMISSION.md` matches what was posted.

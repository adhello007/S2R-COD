# Final scientific audit

**Auditor's method.** Each of the five reviewer concerns is checked against the reviewer's text
(Appendix A), the initial response (`../01_INITIAL_REBUTTAL_FOR_SUBMISSION.md`), the task evidence
(`EXPERIMENTAL_EVIDENCE.md`) and the updated response (`FINAL_UPDATED_REBUTTAL.md`). The independent
verification pass is `scripts/audit_independent.py`. It shares no code with the analysis scripts
(plain Python + scipy; no `statlib`). It recomputes the headline numbers from the raw per-run tables
and committed stem files, and then checks that each number appears as stated in the documents. Its
results are in `EXPERIMENT_LOGS/AUDIT_independent.json`: {{AUDIT_RESULT}}.

## Integrity checks (all concerns)

| Check | Result | Evidence |
|---|---|---|
| Manuscript identical to submission source | Yes, up to 2 punctuation hunks in the AI-use statement; no content change | `EXPERIMENT_LOGS/00_manuscript_check/manuscript_vs_committed.diff` |
| LaTeX source integrity | A scratch copy compiles (latexmk rc 0, 25 pages). 0 undefined references or citations. Main text ends on page 9 | `00_manuscript_check/latex_build.json` |
| Labels and citation keys | 35 labels, none duplicated; all 27 referenced labels defined. 39 main-file cite keys (41 with inputs), all among 43 bib entries | `00_manuscript_check/manuscript_integrity_final.json` |
| Markdown links | All relative links in the rebuttal folder resolve | `AUDIT_independent.json` |
| Reviewer-facing text free of paths, task codes and placeholders | Checked mechanically | `AUDIT_independent.json` |
| OpenReview length | {{COUNT}} code points ≤ 5,000 (Python and `wc -m` agree) | `FINAL_UPDATED_REBUTTAL.md` Part C |
| Runs used are pre-rebuttal and from committed manifests | 64/64 from `se/abc_runs.csv`; newest prediction file 2026-09-22 | `RESULT_TABLES/run_manifest.csv` |
| No outcome-based exclusion | No run, seed, threshold or cell dropped; all 4 cells, both architectures and endpoints reported | all `RESULT_TABLES` |

---

## CW-01: statistical sensitivity and interpretation of the negative result
- **Understood accurately?** Yes. The reviewer's points were: (a) a small realised contrast (18.4% / 8.8%);
  (b) a 2-SD rule that is not a standard error; (c) a CI that excludes +0.0142 but not smaller gains;
  (d) TOST failing at ±0.005; and (e) the paper should say so.
- **Initial commitment addressed?** "Make these qualifications prominent and examine paired-seed
  sensitivity and realized data exposure." Paired sensitivity: done (TH-01). Realised exposure: overlap
  measured exactly; exposure theoretical only, because no sampler trace exists (AN-02). Prominence:
  DOC-01 Edits 1, 3 and 9.
- **Evidence:** `TH-01_paired_inference.csv` (primary row), `AN-02_overlap_by_seed.csv`,
  `AN-02_exposure_by_run.csv`, `AN-02_pseudolabel_overlap.csv`.
- **Did runs execute? Do numbers match raw outputs?** Yes. All 1152 stored metric values reproduce at
  6 dp. The paired CI, TOST and overlap counts were recomputed independently by the audit script.
- **Fair baselines and splits?** B and C10 share the base pool, the target set, the pinned step count,
  the checkpoint rule and the endpoints (verified per run). The between-arm pseudo-label difference is
  reported as a mediator and not adjusted for.
- **Statistical validity:** the paired t (df 7) and TOST are correct for n = 8. The covariance
  disclosure shows pairing adds nothing (r = −0.04), so the paired CI is not presented as tighter.
  Equivalence is not inferred from non-significance. +0.0142 and ±0.005 are labelled as a study
  reference and a post-hoc margin. The 2σ̂ rule is kept separate.
- **Wording preserves limitations?** Yes: "gains of +0.005 or less are not excluded".
- **Consistent with the initial response?** Mostly. **One correction:** the initial response repeated
  "about 48% differ … roughly 8.8% total-pool contrast". The measured B–C10 figures are 77% and 14.1%;
  48% and 8.8% describe only the concentrated-arm pairs. The updated response states the correction
  explicitly.
- **Resolution: SUBSTANTIALLY ADDRESSED.** Open dependencies: realised per-image exposure is not
  measurable from existing logs, and a larger-contrast retraining is blocked (EXP-01).

## CW-02: downstream validation and generalisability of the concentration hypothesis
- **Understood accurately?** Yes. The reviewer's points were: (a) geometry is not performance;
  (b) C10−B and CINV−B boundary gains on SINet, much smaller on SINet-v2, which suggests architecture
  dependence; (c) a fixed offline LAKE-RED pool limits what guidance can do; and (d) generality to
  better or adaptive generators is unclear.
- **Initial commitment addressed?** "Separate geometric from downstream claims, test
  architecture-dependent contrasts, label all boundary analyses exploratory … audit diversity and state
  this boundary explicitly." The separation is in DOC-01 Edits 1 and 4. The interaction test is
  AN-03. Exploratory labelling is used throughout. The diversity audit is AN-02 foreground identity
  plus AN-04. The scope statement is DOC-01 Edit 8. Adaptive generation is BLOCKED (EXP-03), as the
  initial response anticipated.
- **Evidence:** `AN-03_arch_boundary_grid.csv`, `AN-03_interaction.csv`, `EXP-02_gate3_reproduction.csv`,
  `TH-02_quota_invariants.csv`, `AN-04_*`, `EXPERIMENT_LOGS/EXP-03_BLOCKER.md`.
- **Did runs execute? Do numbers match?** The boundary re-score reproduces the 300 committed
  three-seed values (max Δ 1.1e-16) and the published 1.37× and 1.34× ratios. The eight-seed
  headline and interaction numbers were recomputed by the audit script.
- **Validity:** the interaction is estimated directly (Welch on per-seed differences, exact
  permutation, seed-matched sensitivity). It is not inferred from separate significance results.
  Multiplicity is disclosed (Holm over 140 contrasts; smallest 0.50). Bar ratios are kept distinct
  from absolute deltas. The causal reading is limited correctly: C10 and CINV share an identical
  quota multiset, so a gain present in one and absent in the other cannot be attributed to
  concentration.
- **Wording preserves limitations?** Yes. The response withdraws a submitted claim instead of keeping
  it, and states the generator scope.
- **Consistent with the initial response?** **No, on one point, and the change is disclosed.** The
  initial response repeated the three-seed result ("C10–B and CINV–B reach approximately 1.37× and
  1.34× their bars") without saying it was three-seed. At eight seeds C10−B is 0.30× its bar with a
  CI spanning zero. The updated response reports this in its first paragraph.
- **Resolution: SUBSTANTIALLY ADDRESSED.** Open dependency: the generator counterfactual (better,
  more diverse or adaptive foregrounds) is untested because EXP-03 is blocked. The CINV signal on
  SINet is unexplained.

## QA-01: how well do the results rule out smaller improvements?
- **Understood accurately?** Yes: what improvement is meaningful, a paired same-seed analysis, and
  whether the null covers small useful gains.
- **Initial commitment addressed?** "Report uncertainty against both scales and compute matched-seed
  C10–B differences, paired CIs, and paired equivalence tests … after checking run manifests." Done
  for all four cells, after the manifest check (64/64 runs, 1152/1152 values).
- **Evidence:** `TH-01_paired_inference.csv`, `TH-01_seed_differences.csv`, `TH-01_tost_table_reproduction.csv`.
- **Validity:** the paired analysis is valid but is not a stronger design here (B redraws data per
  seed), and the response says so. The exact sign-flip test and leave-one-out are included, and the
  bootstrap is flagged as unreliable at n = 8.
- **Consistent with the initial response?** Yes ("smaller useful gains cannot currently be excluded").
- **Resolution: FULLY ADDRESSED.** The reviewer's question is answered quantitatively for every cell,
  with the limits stated.

## QA-02: limited training-set differences and synthetic diversity
- **Understood accurately?** Yes: does an 8.8% contrast hide effects; would larger differences or more
  diverse foregrounds change the conclusion.
- **Initial commitment addressed?** "Quantify realized per-seed overlap and exposure, preflight larger
  matched-budget allocations … analyze coverage conditional on foreground identity … attempt
  controlled training where feasible … report adaptive/diverse foreground generation as an open
  limitation." Overlap: done. Exposure: theoretical. Preflight: done; it failed its pre-specified rule,
  so training was not justified (and there is no GPU). Coverage by foreground identity: AN-04.
  Limitation: stated.
- **Evidence:** `EXP-01_preflight.csv`, `EXP-01_BLOCKER.md`, `AN-02_*`, `AN-04_*`, `EXP-03_BLOCKER.md`.
- **Validity:** the preflight metric and pass rule were fixed in the prespec before computation.
  N = 1000 reproduces the committed selections byte for byte. The proposed fixed-budget alternative is
  labelled as a different algorithm.
- **Consistent with the initial response?** Yes, and the larger-contrast question is now answered for
  this pool: larger N does not produce a larger contrast.
- **Resolution: PARTIALLY ADDRESSED.** The counterfactuals the reviewer asks about (materially larger
  contrasts; more diverse foregrounds) could not be tested. The response explains why, and does not
  imply that they were.

## QA-03: protocol consequences of CHAMELEON overlap
- **Understood accurately?** Yes: how the 50 / 44 overlaps affect supervised training, unlabelled
  target adaptation and checkpoint selection.
- **Initial commitment addressed?** "Audit exposure by protocol, distinguish 16 unchecked cases,
  disclose mask-release sensitivity, and favor COD10K-test/NC4K." All done (AN-05, DOC-02), with
  per-image pathways.
- **Evidence:** `AN-05_chameleon_pairs.csv`, `AN-05_protocol_paths.csv`, `AN-05_cross_benchmark.csv`,
  `AN-05_pseudolabel_exposure.csv`, `AN-05_mask_release.csv`, `FIGURES/AN-05_protocol_paths.png`.
- **Numbers match?** Every submitted count reproduces with the unchanged detectors. The agreement with
  the committed per-image verdicts is 76/76.
- **Validity:** image exposure, label use and selection use are kept separate. No inflation is claimed.
  The two new facts come from the same released detector, with nearest-neighbour discontinuities of
  6.9× and 79×. All 76 images are accounted for (50 + 16 + 10). The "clean vs training" label for the
  10 is shown to overstate the check.
- **Consistent with the initial response?** Yes, with two refinements that strengthen it: a 4th
  CAMO-250 duplicate, and the 16 "unchecked" being COD10K-test re-encodes. The initial response's
  "favor COD10K-test/NC4K" still holds for this paper (CHAMELEON is not an endpoint). For other papers
  the response now adds that CHAMELEON and COD10K-test are not independent.
- **Resolution: FULLY ADDRESSED.**

---

## Residual risks the author should know about
1. **Edit 4 withdraws a claim the submitted abstract leans on** ("on boundary accuracy, so does aiming
   at the clusters the model was most certain about"). The geometric thesis does not depend on it, but
   the abstract and `sec:concentration` must change together.
2. The reversed-signal arm's small advantage on SINet (S-measure and boundary) is uncorrected and
   unexplained. It must not be presented as a finding that reversal helps.
3. Exposure is theoretical. A reviewer who asks for realised visit counts can only be offered a
   re-run with sampler logging.
4. The CHAMELEON / COD10K-test overlap is a statement about benchmarks, not about this paper's numbers.
   Keep it in that register.

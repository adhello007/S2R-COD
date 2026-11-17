# FINAL_SCIENTIFIC_AUDIT: RL5B rebuttal (Phase 6)

*Final, 2026-11-17. The CW-01 entry and the ledger row for the confirmatory campaign were re-assessed after the
committed EQ analysis ran (07:40–08:16).*

## How the audit was done

- **The numbers were recomputed independently.** `analysis/audit_recompute.py` re-opens the raw per-run files:
  - `rebuild/ABC/out/se/abc_metrics.csv` and `rebuild/ABC/out/se/abc_runs.csv`;
  - `RESULT_TABLES/AN01_boundary_8seed_per_run.csv` and `RESULT_TABLES/EXP02_SINet_per_run.csv`;
  - `RESULT_TABLES/EXP03_run_scores.csv` and `RESULT_TABLES/EXP03_external_scores.csv`;
  - `rebuild/ABC/out/cdr/cdr_allocations.csv`.

  With its own code (Welch, TOST, Holm, pooled σ̂, the CDR rule, and a fresh simulation of the 2σ̂ rule), it
  recomputes every number the final rebuttal quotes and checks that each quoted string appears in the
  rebuttal.
- **Two saved CDR prediction maps were re-scored** from the image files; they match the table at 6 dp.
- **The rebuttal was scanned for internal details:** paths, hashes, hardware, tools, internal task codes.
- **Result:** `EXPERIMENT_LOGS/audit_recompute.log`, run with `--final`: 88 checks, all PASS, including every EQ
  number. Two [AUTHOR] markers (the title) remain for the author.
- **EQ spot check:** three EQ runs re-scored from their saved maps with the committed scorer match at 6 dp
  (`EXPERIMENT_LOGS/EXP01_spot_rescore.log`). They include the two lowest-scoring runs.
- **Manuscript references** were checked against the compiled revision
  (`revision/build_rev/AD-PCHGS-revised.pdf`, 27 pages, main text ends on page 10) through its `.aux` labels:

| Reference in the final rebuttal | Label | Compiled number and page | Correct |
|---|---|---|---|
| Table 3, Sec. 3.1 (16 contrasts, CIs, TOST) | `tab:ci_tost` in `sec:null` | Table 3, p. 6, §3.1 | yes |
| Sec. 3.2, new heading | `sec:concentration` | §3.2, p. 6, "Concentration, Not Targeting, Shapes the Training Set" | yes |
| Sec. 2, sign rule corrected | Methods | §2 now says "at least seven of eight in the eight-seed expansion" | yes |
| Table 7 (App. C), eight-seed boundary table | `tab:boundary` in `app:diag` | Table 7, p. 19, App. C | yes |
| Appendix A, protocol table (Table 4) and gap paragraph | `tab:protocol` in `app:related` | Table 4, p. 15, App. A | yes |
| "The appendix is corrected" (pseudo-label counts) | `app:controls` | App. H now gives 1991, 2007, 2020, 2015 (1782–2278) | yes |
| "Sec. 3.2 says so" (delivered concentration) | §3.2 dose-response paragraph | sentence present | yes |
| "The Discussion now says so" (operating point) | `sec:discussion`, Scope | sentence present | yes |
| New Scope paragraph in the Discussion | `sec:discussion` | present, p. 10 | yes |

---

## CW-01 / QA-01: absence of evidence vs evidence of equivalence

- **Understood?** Yes. The concern is that an interval reaching past the margin cannot support "no meaningful effect"; QA-01 asks for the intervals and for the detected/equivalent distinction to be prominent.
- **Promised analyses executed?**
  - Wording, the table and the re-derivation: done.
  - Confirmatory campaign: pre-registered, run, and **INCOMPLETE** (16 / 15 / 15 of 27 seeds per arm), analysed by the committed script under Amendment 1's rule.
  - Title: the author's decision.
- **Scientifically valid?** Yes.
  - The re-derivation reproduces the submission exactly.
  - Independent code reproduces the rule simulation (0.20 and 0.0087) and every EQ statistic.
  - The EQ analysis ran once, after the cutoff, with no interim look, and no completed run was dropped.
  - The margin of the eight-seed analysis is labelled post hoc. The EQ margin was pre-registered.
- **Directly addresses the concern?** Yes. The reviewer said the interval "does not establish equivalence". The confirmatory campaign establishes it on the primary cell (Δ = +0.0006, 90% CI [−0.0027, +0.0039], TOST p = 0.015, 0.030 after Holm). The claim is calibrated to match.
- **Reproducible?** Yes (`EXPERIMENT_LOGS/audit_recompute.log`, `EXPERIMENT_LOGS/EXP01_spot_rescore.log`).
- **Mathematics justified?** Yes. The posted normal approximation is shown to understate the full rule's sensitivity, and the correction is stated.
- **References accurate?** Yes (table above). The EQ sentences sit in §3.1, the abstract and the conclusion, and the main text still ends on page 10.
- **Appropriately qualified?** Yes:
  - "incomplete at 15–16 of 27 seeds per arm" is stated wherever the result appears;
  - equivalence to the shuffled arm on COD10K is reported as not established (p = 0.056);
  - the larger run-to-run spread, and its link to pseudo-label counts, is reported.
- **Consistent with the initial rebuttal?** Yes, with three corrections flagged: the sensitivity figure, σ̂ and the sign rule. The posted design promised a sample size "fixed in advance"; the reduction to 27 before any run, and the incomplete finish, are both stated.
- **Classification: SUBSTANTIALLY ADDRESSED.** The substance is fully addressed: the overclaim is removed, QA-01 is met, and equivalence on the primary comparison is established by a pre-registered test. Two items keep it below FULLY:
  - the posted plan also revises the title (P1.1b), which is the author's decision;
  - the campaign stopped at 15–16 of 27 seeds, so H1b on COD10K is unresolved.

  It is FULLY ADDRESSED once the title is revised.

## CW-02 / QA-02: distributional change vs downstream explanation

- **Understood?** Yes. Training-set separation is not evidence of an accuracy effect, and the boundary signal was post hoc and confined to one architecture.
- **Promised analyses executed?**
  - Claim restructuring: done.
  - Dose-response on SINet: done, pre-registered, 35 runs.
  - SINet-v2 replication: **not run**.
  - Re-scoring of all eight-seed runs with covariates: done, exploratory.
- **Scientifically valid?** Yes.
  - The CDR rule was applied as pre-registered and recomputed independently.
  - Two maps were re-scored from images.
  - Pools and set-distinctness were gated before training.
  - The mixed model's covariate fit is singular and is reported as unfit, not forced.
- **Directly addresses the concern?** Yes. QA-02 asked what supports the downstream claim; the answer is that the pre-registered test does not, and the claim is withdrawn to the training-set level.
- **Reproducible?** Yes.
- **Mathematics justified?** Yes. TH-02 shows why the same-shape contrasts cannot identify a shape effect and why several permutations are needed; the toy simulation checks it.
- **References accurate?** Yes.
- **Appropriately qualified?** Yes. The rebuttal names all three limits:
  - one architecture;
  - the unit-level interval excludes only boundary effects above about 0.007;
  - delivered concentration is weaker than nominal (N_eff 50 / 45 / 41 against 75 / 30 / 15).

  It reports CINV − B's unadjusted interval without treating it as evidence, and it never presents the pooled regression interval as evidence (author rule 5).
- **Consistent with the initial rebuttal?** Yes, with two corrections flagged: the 1.37× / 1.34× figures, and the pseudo-label means. The posted overlap figure (452–511 of 1000 images differ) is consistent with the recomputed shared counts (548, 489, 546).
- **Classification: SUBSTANTIALLY ADDRESSED.** The claim is fully corrected. The promised SINet-v2 replication was not run, and the delivered concentration contrast is narrower than designed, so the null covers concentration as this pool delivers it.

## CW-03 / QA-03: absolute performance and protocol-matched baselines

- **Understood?** Yes. The concern is the absolute gap and whether the pipeline is weak. QA-03 asks for protocol-matched comparisons.
- **Promised analyses executed?** Done:
  - the protocol table, with published values verified;
  - real-mask training of both architectures in our codebase;
  - re-scoring of the released SINet-V2 and RISE maps;
  - source-only and reproduced S2R-COD anchors;
  - the gap decomposition, from measured cells only;
  - RISE in the related work.

  **Not run:** the higher operating point (EXP-04), re-training with the official SINet-V2 recipe (E3-b), and our recipe on RISE's masks (E3-e).
- **Scientifically valid?** Yes. One scorer reproduces all 12 published values within 0.002. Supervised rows are labelled as an upper reference.
- **Directly addresses the concern?** Yes for "explain the gap": real labels account for 0.112 of the 0.120 gap to supervised SINet-V2 on COD10K. Only partly for generality, because the operating-point replication was not run.
- **Reproducible?** Yes.
- **Mathematics justified?** n/a. The text states that the components overlap and do not add up.
- **References accurate?** Yes.
- **Appropriately qualified?** Yes. The RISE gap is attributed to supervision on the real target images, and the rebuttal says that mask quality and recipe cannot be separated without E3-e.
- **Consistent with the initial rebuttal?** Yes, with one correction flagged: the RISE description. The posted reproduction claim (0.7030 → 0.7172) is confirmed under our scorer.
- **Classification: SUBSTANTIALLY ADDRESSED.**
  - The gap is explained under one scorer.
  - What remains open: whether the null holds at a higher operating point (not run, stated), and the split of RISE's advantage into mask quality and recipe.

## CW-04 / QA-04: fixed generator, limited foreground pool, scope

- **Understood?** Yes. The concern is the fixed generator and the background-only diversity, and whether the conclusions are bounded to them.
- **Promised analyses executed?** Done:
  - the scope statement in the abstract, introduction, Discussion and conclusion;
  - all three foreground quantifications;
  - "no claims about other generators".

  The **title** is pending the author's decision.
- **Scientifically valid?** Yes. Counts were re-checked independently (23 arms). The variance and distance numbers come from the committed embeddings, with the representation caveat stated.
- **Directly addresses the concern?** Yes.
- **Reproducible?** Yes.
- **Mathematics justified?** n/a.
- **References accurate?** Yes.
- **Appropriately qualified?** Yes. The between-cluster share of error (about a fifth) is cited from the submission, not re-derived here.
- **Consistent with the initial rebuttal?** Yes.
- **Classification: SUBSTANTIALLY ADDRESSED**, and FULLY once the title carries the scope, as posted Part 4 item 1 promised.

---

## Commitment ledger (every "we will / we plan" in the posted rebuttal)

| # | Posted commitment | Delivered | Status |
|---|---|---|---|
| P1.0 | "Anything we add during the discussion period will be posted separately, whatever the outcome." | `FINAL_UPDATED_REBUTTAL.md`, four parts and a summary, including the unfavourable CDR outcome | done (the author posts) |
| P1.1 | Revise the abstract, introduction, Sec. 3.1 and conclusion to "no detectable advantage; reference-size effects excluded; smaller not excluded" | `revision/AD-PCHGS-revised.tex`; `RESULT_TABLES/DOC01_claims.md` rows 1–12, 18, 20 | done |
| P1.1b | "We also plan to revise the title accordingly." | two options in `RESULT_TABLES/DOC01_claims.md`; (ii) recommended | **author decision** |
| P1.2 | Main-text table for all 16 contrasts: Δ, 95% CI, 90% CI, TOST p, three labels, defined in the text | Table 3, §3.1 (`revision/table_ci_tost.tex`) | done |
| P1.3 | Recompute every interval and TOST statistic; report the rule's sensitivity; Welch primary, seed-paired as sensitivity | TH-01 (`RESULT_TABLES/TH01_contrasts.md`, `RESULT_TABLES/TH01_rule_sensitivity.csv`) | done; posted sensitivity corrected |
| P1.4 | Separately pre-registered confirmatory campaign: B, C10, CSHUF, fresh seeds, n from a TOST power analysis, no seeds added to SE, outcome reported either way | `prereg/EQ.md` (n = 29 by power analysis; Amendment 1 reduced it to 27 before any run); 46 of 81 runs; primary **equivalent** (TOST p = 0.015), H1b on COD10K neither | done, **INCOMPLETE** (16 / 15 / 15 of 27 seeds per arm), stated plainly |
| P1.5 | "Wording … overstate[s] this, and we will correct them" | "no score of any quality helped here" and similar removed | done; title pending (P1.1b) |
| P2.1 | Separate the claims in the abstract, Sec. 3.2 (including its heading) and the discussion: three tiers | revision §3.2 heading and three tiers; abstract; Discussion | done |
| P2.2 | Dose-response campaign: N = 1000; ≥ 3 levels (uniform, τ = 1.0, more concentrated); several random permutations with low overlap with C10; primary BIoU on SINet·COD10K; secondary S_α; decision rule as posted | `prereg/CDR.md`; 35 SINet runs; verdict "not supported"; the claim is restricted to the training sets. Permutations share 440–518 of 1,000 images with C10, fewer than C10 shares with its own shuffle | done (SINet) |
| P2.2b | "Replication: SINet-v2" | not run (author, 11-11; compute after the 11-09 outage) | **not done; stated plainly** |
| P2.3 | Re-score all existing eight-seed runs, both architectures, with boundary metrics and covariates (pseudo-label count, overlap), labelled exploratory | AN-01 (`RESULT_TABLES/AN01_boundary_8seed.md`, `RESULT_TABLES/AN01_regression.md`) | done; the regression fit is degenerate and is kept only as exploratory |
| P3.1 | Protocol table: labels, target images, backbone and pretraining, generator, S_α / E_φ / F_β^w on COD10K and NC4K; published values verified | Table 4, App. A; AN-02 | done; published NC4K values are missing where the papers give none ("—") |
| P3.2a | SINet and SINet-v2 trained on the real masks of the same 4,040 images | E3-c, 3 seeds per architecture | done |
| P3.2b | Released SINet-v2 and RISE predictions or checkpoints re-scored with our code | E3-a, E3-d; 12/12 within 0.002 | done |
| P3.2c | Our source-only and reproduced S2R-COD baselines | E3-f anchors | done |
| P3.3 | Decompose the gap: label supervision, representation/backbone, reproduction differences | `RESULT_TABLES/EXP03_gap_decomposition.md`, from measured cells only | done in part: labels and recipe measured; the RISE split (mask quality against recipe) needs E3-e, which was not run |
| P3.4 | Higher operating point, if compute permits; "if it cannot be completed in time, we will say so" | not run; said so in rebuttal Part 3 and in the revised Discussion | **not done; stated plainly** |
| P3.5 | "it does not discuss RISE, which we will add" | §1.1 and App. A, verified BibTeX | done |
| P4.1 | Scope statement in the abstract, introduction, conclusion **and title**, naming the posted list | abstract, introduction, Discussion (Scope) and conclusion | done; **title pending** |
| P4.2 | Distinct foregrounds and reuse per arm; variance share by foreground identity vs background; distance to the nearest foreground per cluster | AN-03 (`RESULT_TABLES/AN03_foreground_diversity.md`) | done |
| P4.3 | No claims about other generators; list as a limitation | Discussion: "we make no claim about other generators" | done |
| Sum. | "report their results as they are, including unfavourable ones" | the CDR "not supported" outcome and the boundary-figure correction lead their sections | done |

**Not delivered, each stated plainly in the final rebuttal:**
- the SINet-v2 replication (P2.2b);
- the higher operating point (P3.4);
- the RISE split (P3.3, in part).

**Pending:** the title (P1.1b, P4.1), which is the author's decision.

**No "consistent across architectures" anywhere** (author rule 1): checked by grep over the rebuttal and the revised source. The CDR prereg allows that phrase only if both architectures are "supported".

# Unresolved items

None of these is marked complete anywhere in the deliverables. Each is stated as a limitation in the paper and/or the
relevant reply.

## Scientific: not run, or incomplete

| Item | Reviewer(s) | State | Where it is disclosed |
|---|---|---|---|
| Confirmatory equivalence campaign (EQ) | RL5B, dypE | **INCOMPLETE**: 46 of 81 runs (16/15/15 of 27 per arm), after power outages; analysed as pre-registered. H1 equivalent; H1b neither | Table 3, §3.1, §5, App. C; RL5B and dypE replies |
| H1b, C10 vs CSHUF on COD10K-test | RL5B, dypE | neither detected nor equivalent at this precision | Table 3; replies |
| SINet-v2 replication of the dose-response test | RL5B, dypE | **not run** (compute) | §3.2, Table 7 caption; replies |
| SINet-v2 equivalence | RL5B, dypE | eight-seed only; gains ≤ 0.005 not excluded | Table 9, Table 10; RL5B and dypE replies |
| Official SINet-V2 recipe re-trained (E3-b); our recipe on RISE masks (E3-e) | RL5B | **not run**; RISE's mask quality and recipe cannot be separated | App. A gap paragraph; RL5B reply |
| Higher operating point (some real labels) | RL5B | **not run** | §4 Scope; RL5B reply |
| Modern transformer detector | Caus | **blocked**: CamoFormer has no training code; CTF-Net has no licence; released weights trained on our target images | §4 Scope; Caus reply |
| Foreground-varying generator | Caus, dypE | **blocked**: no released generator varies object pixels | §4 Scope; Caus and dypE replies |
| Larger-contrast experiment | dypE | not trainable in this pool: the preflight failed at 1.22× | Discussion; App. C; dypE reply |
| Why CINV leads B on SINet Boundary-IoU (unadjusted) | RL5B, dypE | unexplained; one untested candidate (domain mix) | §3.2; App. C |
| Oracle shapes on SINet-v2 | Caus | not run (three seeds, SINet only) | App. I; Caus reply |
| Training reproducibility | — | same-seed re-trains are not reproducible run to run (RECHECK); verdicts unchanged | App. C (exploratory) |
| Whether CHAMELEON contamination changes any published score | dypE | not measurable without a model trained without the duplicates | App. F; dypE reply |

## Author actions (not done by this integration)

1. **Review and post.** Nothing has been posted to OpenReview.
   - Post `GENERAL_RESPONSE.md` (one comment).
   - Post two comments per reviewer from `REVIEWERS/<ID>/FINAL_UPDATED_REBUTTAL.md`, pasting only the text between the BEGIN/END markers.
   - Upload `REVISED_MARKED.pdf`, `REVISED_CLEAN.pdf`, or both, per your preference and the venue's revision rules.
2. **Push.** The integration commit on `rebuttal/iclr27/merged` is local and unpushed. Tags `prereg-ac-pc-c2114af` (new) and `prereg-or-fx-se-a79886a` are local. The paper cites both tags, so they need `git push origin <tag>` before the anonymous repository is refreshed, otherwise readers cannot resolve them.
3. **Anonymous repository.** The paper's anonymised link (https://anonymous.4open.science/r/AD-35F1/) mirrors the repository. Whether it should now include the rebuttal packages that the reproducibility statement mentions is your call.
4. **Cron entries** left by the RL5B runner (`watchdog.sh`, `eq_autorun.sh`, `@reboot`) are still installed. They are no longer needed; remove them when you agree (RL5B `EXECUTION_STATUS.md` §11 item 6).
5. **Leftover files** from a duplicate Caus session (harmless) remain for you to clean up.
6. **CTF-Net licence**: you were checking it. If it is granted, the modern-detector replication becomes feasible for the camera-ready version.

## Process notes for the record

- **Deletion of partial runs.** The RL5B runner's discard step deleted partial-run folders, despite the instruction "never delete" (RL5B deviation 26). No completed data was affected.
- **animal-54 is not claimed.** The Caus package's independent detector flagged it on 12 Nov (`5e7a2f9`) as a rescaled COD10K-train image, pending your adjudication. On 17 Nov you dropped it without recording a reason, and the package marked it "not adjudicated and not claimed" (`73c18d6`). Constraint 6 briefly reinstated it; on the evening of 17 Nov you ruled that the evidence overrides the constraint, so the paper and replies give only the released detectors' counts (50/76; 74/76 duplicated somewhere). To claim it in the camera-ready version, adjudicate the pair image (report 03 §3) and record the decision.
- **CDR decision sentence.** It says "concentration explains why targeted training sets look different". It is kept verbatim (constraint 4) next to the new "matching and concentration" wording (author decision Q1). The two are consistent, because the sentence is about concentration's role, not exclusivity. Flagged here in case you prefer a footnote.

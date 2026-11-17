# Reviewer roster and revision-colour assignment

Submission 39230, ICLR 2027. Recorded 2026-11-17 before any manuscript edit.

| Slot | Reviewer ID | Colour (RGB) | Macro | Review + posted initial response | Evidence package |
|---|---|---|---|---|---|
| REVIEWER_A | **RL5B** | blue (0, 72, 190) | `\revA{}` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/RL5B.md` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/` |
| REVIEWER_B | **Caus** | teal (0, 115, 115) | `\revB{}` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/Caus.md` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/` |
| REVIEWER_C | **dypE** | purple (105, 45, 160) | `\revC{}` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_dypE/dypE.md` | `rebuild/REBUTTAL/ICLR2027_REBUTTAL_dypE/STUDENT_RESULTS/` |
| shared | two or more of the above | orange (190, 85, 0) | `\revShared{}` | — | — |

The posted initial responses (8 Nov 2026) are reproduced at the end of each `<ID>.md` file and in each package's
`rebuild/REBUTTAL/ICLR2027_REBUTTAL_<ID>/01_INITIAL_REBUTTAL_FOR_SUBMISSION.md`.

## Rules

1. **Overlap rule.** A change made to address concerns of two or more reviewers is orange, whichever package
   produced the evidence. Orange overrides the individual colours.
2. **Attribution is by the concern addressed, not by the package of origin.** For example, the 51st CHAMELEON match
   (animal-54) was found in the Caus package but answers dypE QA-03, so it is purple.
3. **Smallest coherent span.** Mixed-origin paragraphs are tagged sentence by sentence. A float created for an
   overlapping concern is coloured as a whole.
4. **Unchanged text is never coloured.** Changes that serve no reviewer (grammar fixes) are left uncoloured and listed
   in `05_COLOR_CHANGE_LOG.md`.
5. **One switch.** All colour is produced by the four macros and the `revblock` environment defined once in
   `paper/REVISED_PAPER.tex`. `paper/REVISED_CLEAN.tex` sets `\revmarkedfalse` and prints the same source in black.

## Contrast on white (WCAG relative-luminance ratio; computed by `tools/color_audit.py`)

See `06_LATEX_AND_CITATION_QA.md` §Colour for the computed ratios. All four must be at least 4.5:1.

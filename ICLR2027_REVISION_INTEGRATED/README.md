# ICLR 2027 integrated revision: submission 39230

This folder holds the post-discussion revision. It merges the work for reviewers RL5B, Caus and dypE into one
manuscript, and adds the updated replies and the audit reports.

- Prepared 2026-11-17 for the corresponding author, who keeps final approval.
- **Nothing has been posted to OpenReview, and nothing has been pushed.**

## Start here

| File | What it is |
|---|---|
| `REVISED_MARKED.pdf` | The revised paper, with changes coloured by reviewer (legend at the start of the appendix). Main text ends on p.10. |
| `REVISED_CLEAN.pdf` | The same paper with all colours off. |
| `GENERAL_RESPONSE.md` | The general comment: summary of changes, colour legend, the title statement. |
| `REVIEWERS/RL5B/FINAL_UPDATED_REBUTTAL.md` | Two comments for RL5B, with inline tables and checked locators. |
| `REVIEWERS/Caus/FINAL_UPDATED_REBUTTAL.md` | Two comments for Caus. |
| `REVIEWERS/dypE/FINAL_UPDATED_REBUTTAL.md` | Two comments for dypE. |
| `UNRESOLVED_ITEMS.md` | What was not run or is incomplete, and the actions left to the author (posting, pushing tags, cron). |

## Reports

| File | Contents |
|---|---|
| `REVIEWER_ROSTER.md` | Reviewer IDs, package paths, colours, and the rule that a change serving two or more reviewers is orange. |
| `01_REVIEWER_TRACEABILITY_MATRIX.md` | Each issue → commitment → evidence → change → colour → location → reply. Also the constraint checklist. |
| `02_REVISION_PLAN.md` | The plan written before editing, with the headline choices and the placement map. |
| `03_EXPERIMENT_EVIDENCE_AUDIT.md` | Source-of-truth ledger: status of each experiment, pre-registration timing, CHAMELEON reconciliation, contradictions resolved. |
| `04_PAGE_BUDGET_AND_PLACEMENT_REPORT.md` | Verified page rule, compiled page count, headline locations, cuts made. |
| `05_COLOR_CHANGE_LOG.md` | Every change → macro → issue IDs; the uncoloured changes. |
| `06_LATEX_AND_CITATION_QA.md` | Build status, references, citations, numerical checks, colour contrast. |
| `REVISION_DIFF.patch` | `diff -u` of the submitted `AD-PCHGS-250926.tex` against `paper/REVISED_PAPER.tex`. |
| `REVISION_DIFF_inputs.patch` | The same for the `\input` files; new files are listed. |

The git commit on branch `rebuttal/iclr27/merged` is the other identifier of the change.

## Rebuild and re-check

```
python3 tools/integrate.py            # rebuilds paper/REVISED_PAPER.tex from the RL5B package base + Caus/dypE edits
cd paper && latexmk -pdf -outdir=build REVISED_MARKED.tex && latexmk -pdf -outdir=build REVISED_CLEAN.tex && cd ..
python3 tools/verify_numbers.py       # recomputes 92 numbers from source artifacts
python3 tools/check_locators.py       # every reply locator against the compiled .aux
python3 tools/count_chars.py          # every OpenReview comment <= 5,000 characters
python3 tools/color_audit.py          # contrast and coloured-span inventory
python3 tools/path_check.py           # every path named in these reports exists
```

`paper/` is the complete buildable project. `REVISED_PAPER.tex` is the main source; `REVISED_MARKED.tex` and
`REVISED_CLEAN.tex` are one-line wrappers that switch colours on or off.

The submitted manuscript `AD-PCHGS-250926.tex` at the repository root is unchanged.

# 06 — LaTeX, citation and numerical QA

## Build

Run from `ICLR2027_REVISION_INTEGRATED/`:

```
python3 tools/integrate.py                       # regenerates paper/REVISED_PAPER.tex and the generated inputs
cd paper
latexmk -pdf -interaction=nonstopmode -outdir=build REVISED_MARKED.tex
latexmk -pdf -interaction=nonstopmode -outdir=build REVISED_CLEAN.tex
cp build/REVISED_MARKED.pdf build/REVISED_CLEAN.pdf ..
```

The build uses the TeX installation on the machine (pdfTeX via latexmk, BibTeX). It needs the project's own
`iclr2027_conference.sty`, `iclr2027_conference.bst`, `fancyhdr.sty`, `natbib.sty` and `math_commands.tex`, all in `paper/`.

| Check | Marked | Clean |
|---|---|---|
| latexmk exit status | 0 | 0 |
| `!` errors | 0 | 0 |
| undefined references or citations | 0 | 0 |
| BibTeX warnings | 0 | 0 |
| overfull boxes | 1, of 1.08 pt at `REVISED_PAPER.tex` l.712 (inherited from the submission; also in `build_base`) | same |
| other LaTeX warnings | 7 × "`h` float specifier changed to `ht`" (appendix tables; benign) | same |
| pages | 31 | 31 |
| main text (end of §5) | p.10, with 3 lines spare (`04_PAGE_BUDGET_AND_PLACEMENT_REPORT.md`) | p.10 |

**Text identity.** `diff <(pdftotext REVISED_CLEAN.pdf -) <(pdftotext REVISED_MARKED.pdf -)` differs only in the
marked build's colour legend paragraph and in the template's margin line numbers on that page. One real difference
was found and fixed: the leading space swallowed by `\color` (see `05_COLOR_CHANGE_LOG.md`).

## Visual inspection

Pages 1 and 5–10 of the marked PDF were rendered at 70–80 dpi with `pdftoppm` and inspected. The renders are in the
session scratchpad and are not part of the deliverable.

- Colours are distinct from each other and from black body text.
- Tables 2 and 3 are legible at normal magnification after the overfull fixes.
- Table 3 sits at the top of p.6, beside its first reference.
- The Table 2 ORS rows (teal) are on p.5.
- The Conclusion ends on p.10. The AI-use statement begins below it on p.10; it does not count toward the limit.

## Colour contrast (`tools/color_audit.py`)

| Colour | On white (print, light viewers) | On black (dark viewers that keep colours) |
|---|---|---|
| blue RL5B | 7.86:1 | 2.67:1 |
| teal Caus | 5.68:1 | 3.70:1 |
| purple dypE | 8.46:1 | 2.48:1 |
| orange shared | 4.68:1 | 4.49:1 |

All four pass WCAG AA (4.5:1) on white. **Limitation:** a dark viewer that keeps colours while blacking the page
background gives 2.5–4.5:1. Viewers that invert the page (most PDF dark modes) keep the text readable. The clean PDF is
provided for reading in any viewer.

## References and labels

- All `\ref`s resolve (0 undefined).
- Every locator in the four reply files was checked against `paper/build/REVISED_MARKED.aux` by `tools/check_locators.py`. Each locator was rendered from the label it is meant to point to (e.g. "Table 3" must be `tab:equiv`) and found in the reply. All pass.
- Every Table/App./§ token in the replies is covered by one of these checks.

Label map (compiled):

| Section | Number | Table / figure | Number |
|---|---|---|---|
| §1.1 related work | 1.1 | Table 2 `tab:trained` | 2 (p.5) |
| §3.1 `sec:null` | 3.1 | Table 3 `tab:equiv` | 3 (p.6) |
| §3.2 `sec:concentration` | 3.2 | Table 4 `tab:protocol` | 4 (App. A) |
| §3.3 `sec:why` | 3.3 | Table 7 `tab:cdr` | 7 (App. C) |
| §3.4 `sec:contamination` | 3.4 | Table 8 `tab:boundary` | 8 (App. C) |
| §4 `sec:discussion` | 4 | Table 9 `tab:ci_tost` | 9 (App. C) |
| App. A, B, C, E, F, H, I | related, method, diag, coverage, chamext, controls, shapeoracle | Table 10 `tab:paired`; Table 17 `tab:chamcount` | App. C; App. F |

## Citations: identity and whether each supports its claim

| Key | Where (new or moved use) | Check |
|---|---|---|
| `du2025rise` (the only new bibliography entry) | §1.1; App. A | Identity checked against the [CVF open-access record](https://openaccess.thecvf.com/content/ICCV2025/html/Du_Beyond_Single_Images_Retrieval_Self-Augmented_Unsupervised_Camouflaged_Object_Detection_ICCV_2025_paper.html) and [arXiv:2510.18437](https://arxiv.org/abs/2510.18437v1): title, ICCV 2025, pp. 22131–22142, first author Ji Du. Claim support: prototype retrieval producing pseudo masks, as both pages describe. "Detector is SINet-V2 with its own recipe" and the published 0.763 / 0.805 come from RL5B AN-02, which re-scored the released maps (max difference 0.0005). The full author list was taken from RL5B's `AN02_rise.bib` and not re-checked name by name. |
| `lakens2017equivalence` | Table 3 and Table 9 captions (moved from the removed `tab:tost`) | an existing entry; a primer on TOST equivalence testing, which is how it is used |
| `kynkaanniemi2019improved` | App. E (unchanged) | existing |

No other citation was added, removed or repurposed. The diff of citation keys against the submission (main file plus
inputs) shows only `du2025rise` as new.

## Numerical integrity

- `tools/verify_numbers.py` recomputes **92** quantities from source artifacts: 92 pass, 0 fail (`tools/verify_numbers_output.txt`). These cover:
  - EQ (H1, H1b, NC4K rows, Holm, σ̂, bar);
  - eight-seed Welch and paired intervals;
  - ORS contrasts;
  - probe shapes;
  - boundary grid and interaction;
  - overlap, exposure and preflight;
  - domain mix;
  - selection coverage;
  - every CHAMELEON count;
  - CDR rows;
  - Table 4 means;
  - run counts;
  - arithmetic.
- Two rounding issues were found and settled from unrounded data:
  1. `table_protocol.tex` showed SINet C10 COD10K $S_\alpha$ = 0.718. The exact eight-seed mean is 0.717479, so the value is now **0.717**. This was double rounding in the generator, and the paper and RL5B reply now agree.
  2. OR-PROP−CORACLE on NC4K is stored at 6 dp as 0.002750. Exact from per-seed values it is 0.0027503, so **+0.0028**, which is unchanged.
- Percentages recomputed:
  - 0.112/0.120 = 93% of the SINet-V2 gap;
  - 14.1% is the mean over seeds of the one-sided differing share of the 5,447-image pool (seed 42 alone: 774/5447 = 14.2%);
  - 9/256 = 0.035;
  - ×bar 0.0022/0.0057 = 0.38 from unrounded values.
- Reply lengths (`tools/count_chars.py`), in characters including Markdown:

| File | Comment 1 | Comment 2 |
|---|---|---|
| RL5B | 4711 | 3609 |
| Caus | 4161 | 3548 |
| dypE | 3376 | 3814 |
| general | 4527 | — |

  All are ≤ 5,000, with ≤ 2 comments per reviewer. UTF-8 byte counts are also ≤ 5,000.

## Mathematical statements and assumptions touched by the revision

- TOST at ±0.005 on Welch intervals: an equivalence claim needs the 90% interval inside the margin. Table 3 and §3.1 use exactly this.
- The paired analysis is reported as uninformative because the pairs are uncorrelated (r = −0.04), which follows from B redrawing its images per seed.
- Holm corrections:
  - EQ: four confirmatory tests;
  - eight-seed TOST: sixteen contrasts;
  - boundary grid: 140 contrasts.

  Each family is named where it is used.
- Concentration and participation ratio: the revised text no longer says concentration lowers rank, only that these selections have lower rank. App. I gives the counterexample (the five-cluster shuffle at 0.94).
- No proof or new theorem is claimed.

## Withdrawn or superseded phrasings (grep over the revised tex and the replies)

Each phrase below now appears only as a stated correction:
- "strongest form";
- "no score of any quality";
- "detecting the concentration the whole time";
- "only destroying concentration".

Never present: "15 per arm" and "15--16 of 27" (in the main paper), and any 51st CHAMELEON match (animal-54, "fifty-first", 75/76), checked by `verify_numbers.py`. "1.37/1.34" appears only as superseded three-seed
history. No remaining "deterministic" claim concerns the runs; the one hit describes the cuDNN setting, "not claimed to
eliminate" nondeterminism.

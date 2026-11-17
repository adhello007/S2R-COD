# 04 — Page budget and placement report

## Rule

The [ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines), checked 2026-11-17, say:
- the main-text limit rises to **10 pages** during the discussion and rebuttal phase, and is strictly enforced;
- references, the AI-use statement, the ethics statement and the reproducibility statement do not count.

The main-text boundary is therefore the end of §5 (Conclusion). Page counts below come from the **compiled PDFs**,
using `pdftotext -f N -l N`, not from source length.

## Result

| Build | Total pages | Conclusion ends on | Next block starts on | Spare main-text lines |
|---|---|---|---|---|
| Submitted (`AD-PCHGS-250926.tex`) | — | p.9 | — | — |
| RL5B package revision (`paper/build_base/`) | 28 | p.10, last line | p.11 (AI-use statement) | 0 |
| **Integrated, marked** (`REVISED_MARKED.pdf`) | 31 | **p.10** | p.10, below the Conclusion (AI-use statement, which does not count) | **3** |
| **Integrated, clean** (`REVISED_CLEAN.pdf`) | 31 | **p.10** | p.10, below the Conclusion (AI-use statement) | 3 |

**Measuring the spare lines.** The ICLR template stretches a page that ends at a heading break, so the y-position of
the last line cannot show slack. Instead, filler lines were appended to the Conclusion in a scratch copy:
- up to three filler lines stay on p.10;
- four filler lines push onto p.11.

**Any main-text addition longer than three lines must come with a cut.**

**No layout hacks.** Font size, margins, line spacing, `\vspace` and float placement were not touched. Two tables got
narrower column padding (`\tabcolsep`) inside their own float, to clear overfull boxes:
- Table 2: 4pt to 2.5pt;
- Table 3: 3pt to 2pt.

## Headline result per reviewer (all before the boundary)

| Reviewer | Headline | Location | Page | Why this one |
|---|---|---|---|---|
| RL5B | pre-registered confirmatory equivalence (H1 equivalent; H1b neither) with the eight-seed intervals | **Table 3, §3.1** (orange) | p.6 | CW-01/Q1 is RL5B's first weakness and first question, and the paper's central null rests on it |
| dypE | the same table, plus the paired-by-seed row | **Table 3, §3.1** (orange, shared) | p.6 | dypE CW-01/Q1 is the same concern; one table serves both, as the brief allows |
| Caus | oracle allocations of other shapes (ORS) | **Table 2 rows ORS, §3.1** (teal), with two sentences in §3.1 | p.5–6 | Caus gave the lowest soundness score; Q1 is the only experiment Caus asked for, and the only new trained one |

Secondary main-text results:
- dose-response verdict, §3.2, p.7;
- boundary withdrawal and the exploratory CINV−B sentence, §3.2, p.7;
- probe/matching correction, §3.2, p.7;
- CHAMELEON additions, §3.4, p.9;
- Scope paragraph, §4, p.10.

## Appendix placement

| Material | Location |
|---|---|
| Protocol-matched baselines, RISE, gap decomposition | App. A, Table 4 |
| Pre-registration commits and tags; EQ/CDR/ORS rule commits | App. B |
| Dose-response table | App. C, Table 7 |
| Boundary metrics at eight seeds; sweep; interaction, multiplicity, domain mix | App. C, Table 8 and paragraphs |
| All 16 eight-seed contrasts (moved from the main text; merged with the former `tab:tost`) | App. C, Table 9 |
| EQ design, amendment, incompleteness, spread, RECHECK (exploratory) | App. C paragraph |
| Paired analysis, four cells | App. C, Table 10 |
| Realised contrast 77% / 14.1%, exposure, pseudo-label overlap, preflight | App. C, "How much the trained comparison is attenuated" |
| Coverage at every k; coverage of the selected sets | App. E |
| CHAMELEON: fourth CAMO-250 copy, 32 COD10K-test, the fifty-first match, count reconciliation, protocol exposure, 7 COD10K-test duplicates | App. F, Table 17 |
| Oracle-timing wording; pseudo-label means | App. H |
| Oracle shapes: design, 4 contrasts, separability without concentration | App. I (new) |

## Cuts made to fit (all scientific, logged in `tools/integrate_log.txt`)

| Cut | Lines saved (approx.) | Reason |
|---|---|---|
| 16-row `tab:ci_tost` replaced in §3.1 by the 6-row Table 3; the full table moved to App. C | ~10 | headline kept, detail moved |
| §3.2 equivalence paragraph cut to one sentence | ~3 | duplicated Table 9 |
| §3.2 boundary paragraph condensed | ~3 | the claim is withdrawn |
| Last two sentences of the positive-control paragraph | ~3 | dypE's suggested cut; Table 3 carries the point |
| "Perhaps three seeds are too few" condensed | ~2 | redundant with App. H |
| Intro list of standard ingredients, which §1.1 repeats | ~2.5 | redundant; also fixes the broken grammar "are Standard and uses" |
| Intro sentence "re-running … leaves the gap smaller" | ~1.5 | superseded by the confirmatory result |
| Preflight numbers moved from the Discussion to App. C | ~2 | detail |
| Scope sentence reworded more briefly; the caveat is kept ("partly a cut-out-versus-photograph difference") | ~0.5 | wording only |
| Conclusion, Table 3 caption and the oracle-shape sentences tightened | ~6 | — |
| Table 2 caption pointer to Table 3 dropped; §3.2 transition sentence tightened ("Table 2 stands" removed; the sentence still says the boundary metrics re-decide no verdict) | ~2 | wording only |

No unfavourable finding was cut. Every withdrawn claim, incomplete campaign and experiment that was not run is
still stated in the main text.

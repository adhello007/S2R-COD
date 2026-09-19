# PAGE_BUDGET.md — where the main text's pages went, and what to cut

`main_v2.tex` compiles to **25 pages total**, of which the **main text runs to page 11** (the
Conclusion ends there; the AI Use / Ethics / Reproducibility statements begin on page 12 and do not
count toward an ICLR main-text limit). The original `main170926.tex` ended its Conclusion exactly at
the bottom of page 9.

**So you are 2 pages over a 9-page limit, or 1 page over a 10-page limit.** This file says exactly
where the extra went and what each cut would buy, so the editorial calls are yours rather than mine.

---

## 1. What was added, and what it cost

| # | Addition | Directive | Main-body cost |
|---|---|---|---|
| A1 | Closest-work comparison table (§2) | Cat 1 §3 | ~0.45 pp |
| A2 | Related-work paragraphs: GAUDA, DisCL, SynQuE; equivalence + re-encoding audit | Cat 1 §3 | ~0.40 pp |
| A3 | §4.3 boundary metrics — the concentration effect on trained accuracy | Cat 2 §3 | ~0.55 pp |
| A4 | CAMO mixture confound in §4.4 | Cat 2 §2 | ~0.35 pp |
| A5 | Welch-interval paragraph in §4.1 | Cat 2 §1 | ~0.25 pp |
| A6 | CHAMELEON extension paragraph in §5.2 | Cat 2 §4 | ~0.30 pp |
| A7 | Reframed §5.2 opening as a control case study | Cat 1 §2 | ~0.15 pp |
| | **total added** | | **~2.45 pp** |

Restructuring §5 → §4 (Cat 1 §2) was page-neutral: the three subsections moved intact.

## 2. What was already moved out or compressed, to claw that back

Already done — these are **not** available to cut again:

- Contamination table (`tab:contamination`) → Appendix F
- Original confirmed-pairs figure (`fig:pairs`) → Appendix F
- All four new artifacts → Appendix F (`tab:tost`, `tab:clustercomp`, `tab:boundary`,
  `fig:clusterdiag`, `fig:chamext`)
- Closest-work table trimmed from 7 prior-work rows to 5
- Compressed: introduction (~25 %), concentration subsection (~20 %), area control (~30 %),
  setup-specific limitations (~20 %), NC4K negative control (~60 %), tolerance-saturation paragraph
  (~50 %), loose-ends + anchoring paragraphs (merged, ~40 %), related-work additions (~25 %)

Without those, the main text would run to roughly page 14.

## 3. Cut list, ranked by value-per-page

Each entry is independent; take them from the top until you fit.

| Rank | Cut | Saves | What it costs you |
|---|---|---|---|
| 1 | **§4.3 boundary metrics → Appendix F**, leaving 3 sentences and a pointer | ~0.55 pp | Main-body prominence for the strongest new result. The finding survives in full in the appendix, and the 3-sentence version still states that concentration clears the bar and CINV matches it. **Recommended first cut.** |
| 2 | **CHAMELEON case study (§5.2) down ~50 %** | ~0.60 pp | Keep: case framing, 51/76 headline, non-independence, retire-the-benchmark, the published-protocol instance. Move to appendix: tolerance saturation, extension calibration detail, mask-release detail. The contribution survives; its texture thins. |
| 3 | **Mixture-confound paragraph → Appendix F**, leaving 2 sentences | ~0.35 pp | The 2.08× CAMO enrichment is a one-line claim anyway; the supporting table and figure are already in the appendix. Cheap. |
| 4 | **Welch-interval paragraph → Appendix F**, leaving 1 sentence | ~0.25 pp | You lose the in-place argument that the pooled bar is inflated by A0. `tab:tost` already carries the numbers. |
| 5 | **Closest-work table → Appendix A** | ~0.45 pp | Directive Cat 1 §3 asked for the table but not for its placement. Reviewers value it in the main body; it is nonetheless the single largest movable block. |
| 6 | **Related-work additions down ~50 %** | ~0.30 pp | Keep GAUDA (the closest system) and the one-line equivalence/auditing note; drop the DisCL and SynQuE sentences to citations inside the GAUDA paragraph. |

**To reach 9 pages:** cuts 1 + 2, or 1 + 3 + 4, or 5 + 2.
**To reach 10 pages:** cut 1 alone, or 3 + 4.

## 4. One thing worth checking before cutting anything

ICLR's main-text limit has been 9 pages in recent years, but confirm against the ICLR 2027 call for
papers — if it is 10, cut 1 alone is enough, and the paper keeps everything else.

## 5. Two author actions still outstanding in `main_v2.tex`

Both are marked with `% AUTHORS:` comments in the source (invisible in the PDF) rather than left as
`[TODO]`, so the draft compiles as submission-ready. Neither can be settled without you:

1. **AI Use Statement** — a complete draft is written, covering the required disclosure categories
   and the log-block traceability mechanism this work genuinely has. It describes tool use that the
   repository evidences; confirm each sentence matches what you actually did before submitting.
2. **Dataset licences and artifact link** — the ethics statement names all five data sources and
   states non-commercial academic use; confirm against each dataset's current terms. The
   reproducibility statement points at supplementary material, which preserves anonymity without a
   third-party host; substitute an anonymised repository URL if you prefer one.

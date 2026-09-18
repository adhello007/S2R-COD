# PAPER_PLAN_V4 — closing the gap between weak accept and accept

**Deliverable of this step:** write this content to `rebuild/PAPER_V4/PAPER_PLAN_V4.md`
(replacing the interim draft already there, which carried the verdict as `[PENDING]`).
Working dir `rebuild/PAPER_V4/` is already seeded from V3. **Nothing is pushed; commits are yours.**

---

## 1. Context

V3 received **weak accept — 6, confidence 4**, up from reject (v1) and borderline reject (v2). The
reviewer: *"This has crossed the line … a paper I would argue for in the discussion phase."*

**One thing separated it from a clear accept.** The paper's spine is *"a control that returns zero is
informative only if it could have returned something else"* — and its headline null was itself a
control returning zero whose sensitivity had never been demonstrated. The intro promised a
mean-teacher positive control; V3 shipped **no verdict for it**. A hostile reviewer could write one
unanswerable sentence: *"the authors' own framing condemns their own null."*

**That is now closed.** The positive control is trained, scored, and logged.

---

## 2. What is new since V3 — both experiments complete

### `EXP PC` — the positive control. **DETECTED.**

Rule frozen in `PREREGISTRATION_PC.md` at `c2114af`, before the first run. Blocks #1 and #2 at
`results/REBUILD_LOG.txt:2640` and `:2658`. All three thresholds PASS.

| endpoint | MT mean (sd) | C10 mean (sd) | Δ(C10−MT) | 2σ̂ | Δ/bar | sign | verdict |
|---|---|---|---|---|---|---|---|
| **COD10K** *(primary)* | **0.698767** (0.001120) | **0.718481** (0.004059) | **+0.019713** | **0.005954** | **3.31×** | **3/3** | **DETECTED** |
| NC4K *(secondary)* | 0.749659 (0.003089) | 0.769013 (0.003240) | +0.019354 | 0.006331 | 3.06× | 3/3 | DETECTED |

Paired per seed: `+0.017532`, `+0.023867`, `+0.017740`. Gate **G-PC1** passed before any PC number
existed — the scorer reproduced B1's committed `Sα 0.717216` (Δ `3.77e-07`) and `MAE 0.074463`
(Δ `2.32e-07`).

### `EXP AC` — the area control. **AREA-ROBUST**, `7/8` and `6/8` against a `6/8` floor.

Already in V3 but **understated**. The genuinely convincing detail is buried: partialling object area
**raises** ρ(1−Sα) in **all eight rows** — the opposite of the confound's prediction.

---

## 3. Audit of the review

**Every numeric claim in the review checks out.** This is the first review in the series with no
factual errors — worth saying when you respond to it.

Verified against artifacts: the `0.91×` clustering on both gaps; σ̂ = `0.002767` over
`{B, C10, CSHUF, CINV}` at df=8; COD10K maxima `0.002656` (SINet-v2) and `0.002390` (SINet); A0
spreads `0.0334` / `0.0211`; `P(X≥6 | n=8) = 0.1445`; the §3.3-vs-Appendix-G contradiction; Table 7's
three stale entries; the §6.5 / Tier-1-appendix duplication (323 vs 546 words); NC4K per-run values
absent from the paper though present in `abc_metrics.csv`.

**Two things the artifacts can now answer that V3 left open:**

- **`8885 = 4443 + 4442`.** Those 4 and 5 rows carry `interior_px = 0` in
  `d1_trace_{local,auth}.csv`; foreground fractions `0.0019`–`0.0095`, i.e. objects at 0.2–0.9 % of
  frame, **too small to leave any pixels after erosion**. One clause, sourced.
- **The S2R-COD path**, verified from `Explanations/S2R-CODpaper.pdf` rather than taken on trust.
  Table 3 reports `(CAMO + NC4K → CHAM.)`. Task Setup, verbatim: *"For C2C task, we **consistently use
  the real unlabeled COD10K training set as the target domain**."* Case 2, verbatim: source-side
  CHAMELEON removal *"to prevent target domain data leakage"*. **Cases 1–3 adjust only the source.**
  Our measurement: **40 of CHAMELEON's 76 images are in COD10K-train** ⇒ the source path is closed and
  the target path is not.

---

## 4. Decisions taken (asked and answered)

1. **PC scope stated explicitly** — concede the gap in our own voice (§5 below).
2. **Signal count** — lead with **six independent tests**, mention the 8 table rows second.
3. **Δ vs reference gaps** — **omit from the paper**; it stays in `PC_RESULTS.md` §5(b).
4. **A0 instability** — qualitative hypothesis only; do **not** import `POOL_MECHANICS_AUDIT.md`'s
   unlogged exposure numbers. "Every number traces to a committed log block" stays absolute.
5. **S2R-COD** — name it, quote its own setup, attribute no intent.

---

## 5. Section-by-section changes

### §5 The Pre-Registered Null — the section that decides the score *(+370 words)*

1. **The positive-control verdict.** MT `0.698767` vs C10 `0.718481`, Δ `+0.019713` against a bar of
   `0.005954`, `3/3` signs → **DETECTED**. State it is a control on *instrument sensitivity*, not an
   ablation: MT differs from C10 in method, round count and pool size at once, so no component
   attribution follows and none is made.
2. **The scope gap, conceded in our own voice** — the decisive sentence:
   > This establishes the harness resolves effects of roughly the reference magnitude. It does **not**
   > establish that an effect the size of our nulls would be visible: the positive control's own bar
   > (`0.005954`) is **larger than** the decisive gap `Δ(C10−B) = 0.005034`, so an effect of that size
   > would not have cleared this pooling either. A positive control at `0.020` licenses *the
   > instrument works*, not *the instrument would have seen the effect we are nulling*.
3. **State the σ̂ pool explicitly** — *pooled within-arm over `{B, C10, CSHUF, CINV}`, df = 8*. The
   reader must not reverse-engineer the paper's most contested number.
4. **Own the 0.91× clustering**, one sentence: both of the campaign's largest effects sit just inside
   the bar (`0.005034/0.005533` and `0.005007/0.005514`), and a modest gain in sensitivity would flip
   at least one verdict to `INCONCLUSIVE`.
5. **Restore v2's clarifier, with endpoints named**: largest gap anywhere `0.005007` is on **NC4K**;
   on the primary endpoint the maxima are `0.002656` (SINet-v2) and `0.002390` (SINet).
   ⚠ Naming the endpoint is mandatory — collapsing it is the exact error the paper warns against.
6. **The 126 % corollary**, now quantified both ways: the 24-run campaign's bar `0.017933` is 126 % of
   the reference gap `0.0142`, so **that campaign could not have detected the reference effect had it
   been present**, and the null survives only on the imported tighter bar. (It *could* have detected an
   effect the size the positive control measured, `0.019713` — state this too, it is the honest
   symmetric fact.)
7. **Fold Appendix G in** — where the arms sit against published numbers is the first question asked
   of a null; it is currently on page 14. Fix the contradiction while moving: **A0 is the unpadded
   baseline; C10 is the configuration corresponding to the published row.** One wording, both places.
8. **A0's instability → a named hypothesis**, qualitative: A0 holds 4447 images against 5447 elsewhere
   under an identical pinned step count, so it samples a different mixture and should carry higher
   seed variance; the effect reproduces on both architectures, which argues for a substantive property
   rather than a broken run. Explicitly untested.

### §6.3 Ordering — lead with the anti-confound evidence *(+40 words)*

1. **Topic sentence becomes the ρ(1−Sα) rise** in all eight rows — the strongest anti-confound
   evidence in the paper, currently buried below the counts.
2. **Qualify the floor**: `6/8` is `P ≈ 0.145` under a fair coin, and the uncertain-area covariate —
   the one our own density-times-area argument implicates — clears it by **zero margin**.
3. **Six independent tests**, then the 8 rows: three estimators (student–teacher disagreement,
   predictive entropy, ensemble disagreement), the ensemble evaluated on two arms, and by T2C's own
   pre-registration the CSHUF ensemble is a *sensitivity check on* the A0 ensemble — so they were never
   independent. Remove "four signal variants" everywhere.

### §7 Contamination *(+125 words)*

1. **Resolve the standing TODO** with the two verified S2R-COD quotes and the 40/76 consequence, with
   both scope limits: our COD10K-train side is an on-disk copy (author-sourced re-audit *owed*), and
   provenance direction is inference from chronology.
2. **Add the axis clause** to the `1082` figure: *0 of 1082 checkable against the COD10K test split;
   the 1715 checkable figure in Table 2 is the training-pool axis.*

### Abstract, and small fixes *(+30 words)*

- Add the positive control and **restore the sensitivity number** (*"a bar resolving 39 % to 45 %"*).
- Qualify the area claim: *survives a pre-registered area control, at a floor near chance on one of
  two covariates*.
- Drop "four variants" → six independent tests.
- **Figure 1(b) caption must name which σ̂** the band is — the tight falsification bar. With two bars
  differing by 3.24×, an unnamed band visually overstates the null.
- **`8885`**: add the one-clause reason (erosion leaves no interior for 4 and 5 objects at 0.2–0.9 %).

---

## 6. Figures and tables

- **Figure 2 — done.** Now three closest (`0.603`, `0.645`, `0.653`) plus **three most marginal**
  (`3.750`, `4.490`, `5.512`), the last sitting exactly at the `5.51` nearest-neighbour gap boundary;
  marginal pairs dashed. They remain visibly the same photographs at the boundary, which argues the
  case better than the easy pairs alone. One marginal pair (`animal-19`) is the PNG-with-`.jpg`
  container case. Caption states both halves of the rule.
- **Appendix per-run table — add NC4K.** Values exist in `abc_metrics.csv`; the refused `REAL EFFECT`
  rests on them and they are nowhere in the paper. Add the three PC runs too.
- **Table 7 — three fixes.** Signals row → three estimators; add an area-control row; remove the
  demoted "Endpoint-measured signal" Tier 2 row (it lives in the appendix now — one home, not two).

## 7. Appendix restructure

- **Cut the Tier 1 appendix to what §6.5 does not carry** — 546 words duplicating a 323-word section.
- **One home for tables.** "Supporting tables" holds one table while others float unheaded inside the
  Tier 1 appendix. Consolidate.
- **Appendix G moves into §5**, leaving no orphan.
- Add a short **positive-control appendix**: per-seed values, both endpoints, and the frozen rule.

---

## 8. Page budget — main text must stay ≤ 9 pages

V4 currently stands at **5321 words, ending exactly on page 9**. Additions must be matched.

| | words |
|---|---|
| §5 additions (PC, scope gap, σ̂ pool, 0.91×, clarifier, 126 %, Appendix G, A0) | **+370** |
| §6.3 (ρ rise lead, floor qualifier, six tests) | +40 |
| §7 (S2R-COD, axis clause) | +125 |
| Abstract, Fig 1 caption, 8885 clause | +30 |
| **Total additions** | **+565** |
| §6.5 main text trimmed (appendix carries detail) | −140 |
| §6.2 geometry paragraph | −120 |
| §7 finding + exact-hashing paragraphs | −150 |
| §3 Method | −90 |
| §1 Introduction | −70 |
| **Total cuts** | **−570** |

Net ≈ 0. **Never cut:** the two figures, the contamination claim, or the positive-control paragraph.
Cut order if it overruns: §2 Related Work → §3 → §6.5 → appendix pointers.

---

## 9. Verification

- `pdflatex` twice: 0 errors, 0 undefined references; **main text ends on page 9**, measured with a
  section-boundary label (not eyeballed).
- No style file modified (`iclr2027_conference.sty`, `.bst`, `fancyhdr.sty`, `natbib.sty`,
  `math_commands.tex` byte-identical to `./iclr2027`); `\iclrfinalcopy` still commented.
- Every new number traces to `EXP PC` (`:2640`, `:2658`), `EXP AC` (`:2612`), or a committed artifact.
- Banned-phrase scan clean; in-text numbers match tables to the same decimal.
- The three S2R-COD quotes match the PDF verbatim.
- `[TODO]` count **drops from 5 to 3** — the S2R-COD CHAMELEON question is now resolved and removed.

## 10. Flags

1. **`0.005007` is an NC4K figure.** Name the endpoint every time it appears.
2. **Do not let the positive control become a claim it is not.** It is instrument sensitivity, never an
   ablation of Stage C, and never evidence that a `0.005` effect is visible.
3. **`rebuild/PAPER_V4/` is gitignored** by `.gitignore:31` (`/rebuild/PAPER*`), so the manuscript is
   untracked. Your call whether to change that; I will not touch `.gitignore`.
4. **PC_RESULTS.md §5(b)** retains the Δ-vs-reference-gaps accounting that the paper omits by decision
   4.3 — intentional, so the record is complete even though the manuscript is silent.

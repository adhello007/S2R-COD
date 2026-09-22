# Plan: execute the rewrite into `rebuild/FinalPaper/UpdatedPaper/`

## Context

The planning phase is finished. `rebuild/FinalPaper/SCOPING_ANALYSIS.md` diagnosed the draft against
three exemplars; `rebuild/FinalPaper/REWRITE_PLAN_2209.md` (879 lines) converts that diagnosis into
a section-by-section spec with nine section specs, a narrative spine (J), voice mechanics (K), an
accuracy protocol (L), a per-section QA pass (M), and a claims ledger (E) that gates every number.

**This plan executes that spec.** It does not re-derive it. `REWRITE_PLAN_2209.md` is the authority
for content, voice and numbers; this file is the runbook for producing the document.

**Why now.** Prerequisites P1–P3 are complete: `make_results.py` has been re-run and patched to read
the adjudicated audit, so `results.md` now carries SE's 16 verdicts, the n = 8 Welch/TOST rows and
the corrected 50/76 contamination count. The generator is deterministic (re-run is byte-identical).
`EXPERIMENTS_EXPLAINED.md` is current. Nothing in the spec is waiting on data.

**Outcome.** A 9-page ICLR 2027 main text that leads with the positive result (concentration, not
direction), scopes it with a null now defended by five controls, and carries the CHAMELEON audit as
an independent second contribution — replacing a 12-page draft that leads with the null, never
defines `S_α`, and omits OR, FX and SE entirely.

---

## Settled

| | Decision |
|---|---|
| **Target** | A new self-contained build directory, `rebuild/FinalPaper/UpdatedPaper/`, mirroring `Paper/`. `Paper/main_v2.tex` is **never edited** and stays as the reference. |
| **`0.7136`** | **Cut.** The C10-vs-published sentence leaves §4; the verifiable reference effect (0.7030 → 0.7172 = +0.0142, `ABC/PREREGISTRATION.md` §2.9) carries the anchoring claim instead. Removes the one number that traced to no committed artifact. |
| **Figure 1** | Built **during §3**, so that gate is reviewable as the section will actually appear. |
| **§1 + abstract** | **Full gates**, not a close-out. See Step 0.5 item 1. |
| **§5 ordering** | **Conclusion-first**, as already specified for §4. See Step 0.5 item 2. |

---

## Step 0.5 — Two spec amendments to `REWRITE_PLAN_2209.md`, applied before any prose

Both are tightenings of existing specs, not new scope.

### 1. §1 and the abstract are full gates, compressed to cap as they are written

These two carry the density problem that motivated the entire rewrite — **132 numbers per 1000
words against the exemplars' 41–52** — which makes them the highest-leverage prose in the paper,
not a close-out.

- Each gets **its own gate** with the full M1–M9 pass, exactly like §2–§8.
- Each is written **to its ledger cap** (abstract ≤ 160 words / ≤ 8 numbers; §1 ≤ 650 words /
  ≤ 12 numbers), at its own gate — **not** trimmed to cap afterwards.
- Both are reviewed **before** Step 2 begins.
- **Step 2 is therefore rewritten.** The ~0.75 pp of line-level compression was always going to come
  from the abstract/introduction density correction; under this amendment that reduction is
  *already realized* by the time Step 2 runs. Step 2's job changes from "trim the intro" to
  "confirm the budget closed, and if it did not, find the remainder somewhere that is not §1 or the
  abstract." Amend artifact H's residual line to say so.

### 2. §5 is ordered conclusion-first

§5 is the paper's thesis, and its core claim reads as a paradox if stated result-first: *the
instrument resolves concentration but fails to resolve direction in the same cells*, and *the
signal-reversing arm reproduces the effect in full*. Stated cold, a reader hears "the broken version
works too" as a problem rather than as the finding.

Replace §5's beat 1 ("the near-paradox, as drafted") with the same three-move structure §4's
bar-widening passage already uses:

| | Move | Content |
|---|---|---|
| **(a)** | **Takeaway first** | Targeting *looks* like it works — a probe tells a targeted training set from a random one easily, on images it has never seen. The thing that actually makes the set different is that the budget is **concentrated on a few clusters**, not that it is **aimed** at the right ones. |
| **(b)** | **The three legs as evidence for (a)** | Leg 1 geometry (C1) · Leg 2 trained accuracy at n = 8 (SE, CINV highest in 4 of 4) · Leg 3 boundary metrics (DIAG). Each is now read as confirming a stated claim rather than as a fresh puzzle. |
| **(c)** | **Equivalence asymmetry** | Unchanged — stays where the spec already puts it, closing leg 2. |

**The reader must never hold "the reversed arm also works" as a paradox.** Under (a) it is not a
surprise but the expected consequence: if direction were what mattered, reversing it would hurt;
it does not, which is the evidence. The draft's §4.1 opening (`main_v2.tex:462–470`) is still
preserved for its register, but it is re-voiced to follow (a) rather than to pose the puzzle first.

---

## Step 0 — Scaffold `UpdatedPaper/`

Copy from `Paper/`, excluding build products (`main_v2.aux/.log/.pdf/.bbl/.blg/.fls/.out`):

- **Build/style:** `iclr2027_conference.sty`, `iclr2027_conference.bst`, `fancyhdr.sty`,
  `natbib.sty`, `math_commands.tex`
- **Bibliography:** `reference.bib`
- **Table fragments:** `appendix_tables.tex`, `table_cluster_composition.tex`,
  `table_subgroup_metrics.tex`, `table_tost_equivalence.tex`
- **`figs/`:** `fig1_thesis.pdf`, `fig_chameleon_pairs.pdf`, `fig_cluster_diagnostics.pdf`,
  `fig2_pairs.pdf`, `fig2_preview.png`, `make_fig1.py`, `make_fig2.py`, `make_appendix_tables.py`

Then create `UpdatedPaper/main.tex`: preamble, `\title` (D-3 default T1), and a section skeleton
with `\fbox` placeholders for every section, **so it compiles from the first gate onward** and each
gate can be reviewed as a rendered PDF rather than as LaTeX.

Apply the two preamble-level global fixes now: drop the `\fix`/`\new` margin macros (artifact F-6)
and set up the `α → τ` convention for the allocation temperature (F-4, D-5).

---

## Step 1 — Sections, one gate at a time

**Order** — spine order; the abstract and §1 are written last *because* they are written from the
finished sections, and each is a full gate in its own right:

> §2 → §3 → §4 → §5 → §6 → §7 → §8 → **§1** → **abstract**

§2 goes first because its background block defines `S_α`, arm, seed, endpoint and the reference
effect — and rule **K4** (no term used before it is defined) binds every later section to it.

**Each gate delivers, then stops for your review:**

1. The section's prose in `main.tex`, written to its spec in `REWRITE_PLAN_2209.md` Part 5.
2. Its figures/tables — built or promoted per artifact C.
3. **Its appendix edits**, applied in the same gate rather than deferred: every cut lands at the
   destination named in artifact G, so no material is ever in flight between two documents.
4. A compiled PDF and the section's page count against its budget (artifact H).
5. **The M1–M9 pass** (artifact M) reported as a short checklist — density against the ledger cap,
   claim-first paragraphs, the J.2 handoff, terms-before-use, ledger compliance, one-hedge limit,
   spine advancement, and the M9 tonal-seam flags where preserved passages sit in new prose.

**Numbers are ledger-gated throughout (artifact L).** A value enters the text only if artifact E
lists it with its source, and I re-read the cited artifact before finalizing the section.
`main_v2.tex` is not a source of numbers — it predates OR, FX and SE and is wrong on the
contamination count.

**Section-specific work worth flagging:**

- **§3** — build `figs/make_fig_arms.py` → `figs/fig_arms.pdf`, the two-axis arm diagram
  (concentration × direction) covering A0, A2, B, C10, CSHUF, CINV, CORACLE and the FX variants.
  No such asset exists.
- **§4** — the section that grows (~1.2 → 1.8 pp). Assemble Table 1 from six verdict files; write
  the three objection-closures (OR, FX, SE); write the seed-expansion passage **conclusion-first**
  in the three-sentence order the spec fixes. Cut the `0.7136` sentence here.
- **§5** — **conclusion-first per Step 0.5 item 2.** Promote `tab:boundary` out of Appendix E;
  update `make_fig1.py` panel (b) to n = 8.
- **§6** — the section most at risk of reverting to a list. Write the five links with the explicit
  connectives the spec supplies; A0 and A1 stay at one clause each.
- **§7** — 3.0 → 0.7 pp, the single largest cut. Three paragraphs, a footnote, Figure 3 cropped to
  four pairs.
- **§1 and abstract** — written to cap at their own gates, per Step 0.5 item 1.
- **Appendix additions that must be written, not moved:** an SE section (per-run metrics, the
  2026-09-20 interruption record, the bar-widening analysis) and OR/FX detail sections.

---

## Step 2 — Final passes

Runs only after the §1 and abstract gates have been reviewed.

1. **Consistency sweep** — all fifteen artifact-F items verified applied, in particular the run
   counts reading **103** with the breakdown given once, and **50/76** everywhere.
2. **Budget reconciliation** — compile and measure. The density correction in §1 and the abstract
   has already been realized at their gates, so this is a confirmation, not a trim. If the budget
   has not closed, the remainder is found **outside** §1 and the abstract.
3. **Full-document read** — the spine (J.1) traced end to end, every handoff (J.2) present, and the
   geometric/downstream distinction stated exactly once.

---

## Open item

**D-2 — does ICLR 2027 count the Ethics and Reproducibility statements against the 9 pages?** Not
verifiable from the repo; it needs the 2027 CFP. The budget assumes **excluded**, as ICLR normally
does. It only bites at Step 2, and the contingency is already written (artifact H: §7 → 0.6 pp,
§2 → 0.7 pp, §5 → 1.2 pp recovers the full page). If you can confirm it before then, nothing is
wasted either way.

Every other decision (D-1, D-3 … D-10) has an adopted default recorded in `REWRITE_PLAN_2209.md`
Part 8 and will be applied as written unless you say otherwise at a gate.

---

## Verification

- **Per gate:** M1–M9 pass; section page count within budget; every number traces to an artifact-E
  row and was re-read from its source.
- **§1 and abstract specifically:** within their word **and** number caps as delivered, before
  Step 2 — not brought within them by later trimming.
- **End to end:** main text compiles at **9.0 pp**; `main_v2.tex` byte-identical to its current
  state; `50/76` and `103 runs` consistent across `main.tex`, `results.md` and
  `EXPERIMENTS_EXPLAINED.md`; the five C4-flagged values appear nowhere; OR, FX and SE each present
  in §4 and SE additionally in §5; all six `SCOPING` Part 3.3 "must survive" passages present.
- **Reproducibility:** `make_results.py` re-run once more at the end to confirm the numbers in the
  paper still match a freshly generated `results.md`.

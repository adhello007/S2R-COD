# REWRITE_PLAN_2209.md — the section-by-section rewrite spec for `main_v2`

**Status:** plan only. No paper prose is written here and `main_v2.tex` is untouched.
**Audience:** us, as the working spec the rewrite executes against.
**Authority chain:** `SCOPING_ANALYSIS.md` Parts 1–2 (the exemplar analysis and the P1–P10
playbook) are locked and not re-derived. For every number, **the committed artifact governs**;
where an artifact and a document disagree, the artifact wins. **`main_v2.tex` is not a source of
numbers** — see artifact L.

**Read Part 0 first.** SE finished scoring at 2026-09-22 17:54, after the scoping analysis was
written. The null holds, but not for the reason the brief assumes, and §4's headline sentence
changes as a result.

---

# PART 0 — Corrections carried into this plan

The frame is locked and survives: SE is scored, **all sixteen gaps are `WITHIN NOISE`**, the null
holds, the positive result leads. Three factual details differ from the brief and the rewrite
follows the artifacts.

## C1 — The SE bar did not tighten to ~0.0034. It widened.

The brief says the gap *"stays within noise even at the tightened (~0.0034) bar."* That was the
**pre-registration's projection**, explicitly conditional on *"if the per-arm spreads stay as
measured."* They did not; every per-arm sd grew.

| | ABC n=3 | T2 n=3 | **SE n=8** |
|---|---|---|---|
| bar 2σ̂, SINet·COD10K | 0.01793 | 0.00553 | **0.00686** (1.24× **wider** than T2) |
| df | 8 | 8 | **28** |
| Δ(C10−B) | +0.00503 | — | **+0.00235** |
| reading | 0.28× | 0.91× of T2's bar | **0.34× of its own** |

*Sources: `rebuild/ABC/out/se/abc_sigma.json`, `.../abc_verdict.json`, `rebuild/SE/SE_RESULTS.md`
§6.3.*

SE bought a **trustworthy** bar (df = 28, up from 8), not a small one, and revealed the committed
three-seed bars as optimistic. What rescued the null is that **the decisive gap halved**.
`SE_RESULTS.md` §7 states that the rewrite must say so rather than report the projection.

**This is a better story than the brief assumes:** we pre-registered the outcome that would have
forced withdrawal of the central claim, it did not occur, and it did not occur for a reason we did
not predict. §4 beat 4 specifies how to tell it without asking the reader to hold a paradox.

## C2 — A stronger sensitivity statement exists but is not yet an artifact

**RESOLVED 2026-09-22 — `make_results.py` re-run; these are now committed artifacts in
`results.md` §4.** SINet·COD10K gives **Δ = +0.00235, 95% CI [−0.0020, +0.0067] at df = 10.44**,
against ABC's n = 3 `[−0.0035, +0.0136]` at df = 2.76. The upper bound is under half the 0.0142
reference effect and the "holds only just" caveat disappears.

**And a result the draft says is unobtainable.** The draft states that *"a formal equivalence test
at δ = 0.005 rejects nothing anywhere here — at three seeds that is a statement about the design,
not the effect."* At eight seeds, **five of the sixteen SE gaps establish formal equivalence at
δ = 0.005**:

| cell | gap | TOST p |
|---|---|---|
| SINet · COD10K | **C10 − CSHUF** | 0.0189 |
| SINet · COD10K | **CSHUF − CINV** | 0.0486 |
| SINet · NC4K | C10 − B | 0.0084 |
| SINet · NC4K | C10 − CSHUF | 0.0106 |
| SINet-v2 · COD10K | **CSHUF − CINV** | 0.0402 |

**The shape of this is exactly the paper's thesis.** Equivalence is establishable for the
*direction* contrasts — C10 vs its own shuffle, and shuffle vs reversal — on the primary
architecture. It is **not** establishable for the decisive targeting-vs-random gap on the primary
cell (C10 − B, p = 0.1009), because that comparison varies concentration as well as direction.
Direction is equivalent; concentration is not. *Source: `results.md` §4.*

Supersedes `SCOPING` F9; adopted provisionally as Decision D-4. See D-7 for how to report it.

## C3 — Two supporting documents are stale

| Document | Says | Should say | Status |
|---|---|---|---|
| `results.md` §1 | SE `RUNNING (14 of 40 runs started)` | COMPLETE, 40/40 | **RESOLVED** by P1 |
| `results.md` §5.4 | CHAMELEON **51/76 (67.1%)**, 15 unchecked | **50/76 (65.8%)**, 16 unchecked | **RESOLVED** by P2 |
| `results.md` §6 rows 5, 8 | 51/76; SE "RUNNING" | 50/76; SE COMPLETE, 8/8 within noise | **RESOLVED** by P1/P2 |
| `EXPERIMENTS_EXPLAINED.md` §17 | SE "(running)", 12 complete, 0.0034 projection | complete; the measured bar | **RESOLVED** (author) |
| `EXPERIMENTS_EXPLAINED.md` §18 | 51/76 | 50/76 | **RESOLVED** by P3 |

**One item P1 did not fix.** `results.md` §4 closes with a hardcoded paragraph, *"The one line
worth reading"*, still anchored to the ABC n = 3 interval and its *"at df ~ 2.8 the exclusion holds
only just"* caveat. It is not wrong — it is about ABC — but the SE rows two lines above it are now
the stronger statement. Under Decision D-4 this paragraph should point at the SE interval instead.
Left unchanged pending that sign-off, since it is prose in a committed generator.

`main_v2.tex` already says 50 and is correct on this point. Direct count from
`final_verdicts.csv`: `CONTAMINATED 50`, `UNCHECKED 16`, `CLEAN_VS_TRAINING 10`;
`tier` = 41 `A_same_dimension` + 9 `B_geometric`; `pool` = 44 `cod10k_train` + 6 `camo`.

## C4 — Five numbers in `main_v2` could not be verified

Flagged, not carried. Each is Decision D-6.

| Value | Site | Problem |
|---|---|---|
| `0.7136` "reported for the corresponding published configuration" | `:447` | Absent from every `rebuild/` artifact. Needs an external citation or deletion. |
| `P ≈ 0.13`, `P ≈ 0.006` | `:477–479` | One-sided binomial sign tests on 13/20 and 4/20; not in `C1_RESULTS.md`. The paper elsewhere declines p-values. |
| "Run first on the **41** known pairs" | `:710` | `CONTAMINATION_LEDGER.md` says the instrument was validated on **8** of the 41. |
| `243.3 → 193.2` effective rank; `0.6490 → 0.6886` precision | appendix | Not located in `A3_RESULTS.md` at these values. |
| The two separate `44`s | `:139` and §7 | Partners in COD10K-train, and CHAMELEON images in the protocol's target pool. Almost certainly the same 44; must be stated as such or they read as independent corroboration. |

---

# PART 1 — Prerequisite actions

Run before any prose is drafted. Not part of the deliverable.

| # | Action | Why |
|---|---|---|
| **P1** | ~~Re-run `rebuild/FinalPaper/make_results.py`~~ **DONE 2026-09-22** | It already reads all five SE artifacts. Regenerates the SE campaign block, SE per-run rows, and the §4 Welch/TOST table **with n = 8 rows** — turning C2's indicative interval into a committed artifact. Clears the stale SE status. |
| **P2** | ~~Patch `make_results.py` §5.4~~ **DONE 2026-09-22** — now reads `D2_FINAL_AUDIT/out/final_verdicts.json`, and §6 row 5 reads it too | Otherwise it keeps emitting 51/76. The script knows nothing of `D2_FINAL_AUDIT`. |
| **P3** | ~~Correct `EXPERIMENTS_EXPLAINED.md` §17 and §18~~ **DONE 2026-09-22** — §17 marked complete (author); §18's 51/76 corrected to 50/76 with the supersession explained inline |
| **P4** | Re-measure the compiled page count after the first structural pass | The 9 pp budget assumes Decision D-2. |

---

# PART 2 — Global frame (artifact A)

## A.1 Thesis sentence

> **A1 (provisional default).** What makes a targeted synthetic training set measurably different
> from a random one is that the budget is *concentrated*, not that it is *aimed*: every rule that
> preserves the allocation's shape reproduces the effect, including one that reverses the
> uncertainty signal inside it.

> **A2 (alternative).** Concentration, not the direction of the uncertainty signal, produces the
> difference between a targeted training set and a random one — in feature geometry, in boundary
> accuracy, and across eight seeds of trained accuracy.

A1 names the mechanism rather than listing evidence, and is the sentence the title compresses.

## A.2 The two nulls — final wording, each stated **once**

**Null A — the bounded direction-null. §4 only.**

> Holding the allocation's concentration exactly fixed and varying only where the budget points,
> the direction of the uncertainty signal changes trained accuracy by nothing this design resolves.
> Across an eight-seed campaign on four arms, two architectures and two endpoints, all sixteen gaps
> are within noise and none reaches two-thirds of its bar (2σ̂ = 0.0069 on the primary cell,
> df = 28).

**Null B — the contamination non-finding. §7 only.**

> We expected the contamination to inflate CHAMELEON scores, measured it, and did not find it: all
> eight difficulty percentiles for the leaked subset fall between 0.448 and 0.559, and the sign of
> the clean-minus-leaked difference flips with the mask release. The claim is therefore
> non-independence, not inflation.

**Rule.** The geometric/downstream distinction currently appears four times (abstract, §1, §5
opening, conclusion). It is stated **once**, in §8.

## A.3 Title — provisional default T1

| | Title | Assessment |
|---|---|---|
| **T1 (default)** | *Concentration, Not Targeting: A Pre-Registered Null for Uncertainty-Guided Synthetic Data in Camouflaged Object Detection* | Leads with the positive result, scopes with the null, names the task. Already drafted at `main_v2.tex:11` (commented out). "Pre-Registered" is announced rigour, which our style note discourages — but for a null it is load-bearing: it tells a reviewer in the title that the result is not post-hoc. |
| T2 | *Concentration, Not Targeting: What Makes a Targeted Synthetic Training Set Different* | Cleaner and more memorable; drops both the task and the null. |
| T3 | *It Is the Concentration, Not the Signal: A Controlled Null for Uncertainty-Guided Data Generation* | Most general; weakest fit to a COD venue. |

Retire the current title (`:13`), which asserts *"Targeted Synthetic Data Doesn't Help"* — a
different and weaker claim than the paper proves.

---

# PART 3 — Narrative spine and handoffs (artifact J)

## J.1 The spine

Six sentences. Every section advances one of them; a passage that advances none is a candidate cut.

1. Camouflaged object detection needs pixel-accurate masks that are unusually expensive to draw, so
   synthetic training images are a standard remedy — which raises a question nobody has answered:
   under a fixed budget, which images should you generate?
2. The obvious answer, and the one we built, is to let the model choose: cluster the unlabelled
   real images it will face, find the clusters it is least sure about, and aim the generation there.
3. That loop does produce a training set measurably different from a random one — but the
   difference comes from **concentrating** the budget on a few clusters, not from **aiming** it,
   because destroying or reversing the signal inside the same allocation reproduces the effect in
   full.
4. On trained accuracy the direction of the signal moves nothing this design can resolve, and five
   independent controls — a positive control, a perfect-oracle score, an unpinned schedule, a
   same-shape shuffle, and an eight-seed expansion — each close a different reason the null might
   be an artifact rather than a result.
5. The loop could not have delivered, for reasons measurable in the data rather than in the
   training: the target barely clusters, most of its error is within-cluster, the budget behaves as
   a dataset selector, the signal predicts the wrong kind of error, and the generator copies
   objects rather than inventing them.
6. Separately and independently, the benchmark the field uses to check such claims is itself
   two-thirds training data and the standard check reports it clean — one more instance of the
   thread running through the whole paper: a control that returns zero is informative only if it
   could have returned something else.

## J.2 Section handoffs

One line per adjacent boundary. **Each section spec opens by citing its incoming handoff.** The
handoff is the *connection to be written*, not text to paste.

| Boundary | Handoff |
|---|---|
| Abstract → §1 | The abstract states the claim; §1 earns it by showing why anyone would have built this loop in the first place. |
| §1 → §2 | §1 called every ingredient standard; §2 says precisely what each one is and what the paper measures with. |
| §2 → §3 | The vocabulary is in place; §3 specifies the loop that the vocabulary will be used to judge. |
| §3 → §4 | The loop is specified, so the first question is the one it was built to answer: does aiming the budget beat spending it at random? |
| §4 → §5 | The null says direction did not move the endpoint; the obvious next question is why targeting *looked* like it worked — which §5 answers. |
| §5 → §6 | Concentration explains the appearance; §6 explains why the loop could never have delivered the substance. |
| §6 → §7 | The causes above are about our loop; the next finding is about the benchmark everyone uses, and holds whether or not our loop worked. |
| §7 → §8 | Two findings, one methodological thread; §8 says what transfers beyond this setup. |

---

# PART 4 — Voice mechanics (artifact K)

These replace every bare "Voice: ViT §X" pointer. Each section spec cites **K plus its specific
exemplar move**. Extracted from `SCOPING_ANALYSIS.md` Part 2.1.

| # | Rule | From |
|---|---|---|
| **K1** | Every paragraph opens with its claim as the topic sentence; the table or evidence reference is the second sentence. One claim per paragraph. | P5 |
| **K2** | Numbers in prose are **relative and stated once**; absolutes live in tables. A value repeated in two sections is a defect. | P4 |
| **K3** | **Mechanism before metric** — say in words what a thing does, then quote one relative number. | P10 |
| **K4** | No term is used before it is defined. The §2 background block is the **one** place terms are defined. | P2 |
| **K5** | **Concede in a clause, then point at the control.** Never a paragraph of hedging where a measurement exists. | P7 |
| **K6** | Sections close forward — a summary sentence or a pointer to what the next section settles. | P8 |

Two further rules derived from the same analysis, applying where K1–K6 are silent:

| # | Rule | From |
|---|---|---|
| **K7** | An equation gets one sentence before it saying what it is for and one after saying what it buys. It is never walked through term by term. | P3 |
| **K8** | **Hedging budget: at most one reader-instruction per section.** The draft carries seven ("The honest limit…", "Two loose ends, neither of which flatters us", "Three qualifications, all cutting against it", …). Where a control exists, K5 replaces the hedge. | `SCOPING` F7 |

---

# PART 5 — The section specs

Nine specs (abstract + §1–§8). Each carries eight fields. Page targets sum to **9.0**.

---

## Abstract

1. **Job.** State the claim so a reviewer can repeat it accurately after one read, without having
   read the paper.
2. **Length.** 0.3 pp. **≤ 160 words. ≤ 8 substantive numbers** (ledger cap; ViT's abstract carries
   0, CamoDiffusion's 1).
3. **Ordered beats.**
   1. The task and why its labels are expensive — one clause.
   2. **The obvious idea anyone would try:** let the model's own uncertainty choose which images to
      generate.
   3. What we built, in one sentence.
   4. **The null: one bar, one number.** The direction of the signal changes nothing this design
      resolves. *Source: `se/abc_verdict.json`, `se/abc_sigma.json`.*
   5. **The positive finding:** concentration, not direction, is what makes a targeted set
      different — shown by a control that keeps the allocation's shape and destroys the signal
      inside it. *Source: `C1_RESULTS.md` §8.2; `SE_RESULTS.md` §6.4.*
   6. Scope: what size of effect this design could and could not see.
   7. *(Flagged — see Decision D-8.)* The independent CHAMELEON contribution, ~25 words.
      *Source: `CONTAMINATION_LEDGER.md`.*
4. **Cuts.** The current abstract (`main_v2.tex:35–76`) runs ~400 words with the
   geometric/downstream split spelled out at paragraph length. That split moves to §8 and is stated
   once. The commented-out alternative abstract (`:47–75`) is deleted, not revived.
5. **Promotions.** None.
6. **Figures/tables.** None.
7. **Voice.** **K1–K8**, plus ViT's abstract: no notation, no arm names, claim stated flat.
8. **Preserved.** Nothing. The abstract is written last, from the finished sections.

**Forbidden vocabulary** (same list as §1): `C10`, `B`, `CSHUF`, `CINV`, `CORACLE`, `σ̂`, `2σ̂`,
`WITHIN NOISE`, `df`, `S_α`, "126%", "3.24×", "0.91×", "0.34×".

---

## §1 Introduction

1. **Job.** Take a non-COD reader from "what is camouflaged object detection" to "these authors
   built a reasonable thing, found it did not work, and found out why" — such that they can state
   the paper's claim having read nothing else.
   **Incoming handoff (J.2):** the abstract stated the claim; §1 earns it.
2. **Length.** 1.2 pp. **≤ 650 words** (currently 1151 with the abstract). **≤ 12 substantive
   numbers.**
3. **Ordered beats** — ViT's five-move funnel.
   1. The task; why its masks are unusually expensive; why synthetic data is the standard remedy.
   2. The unanswered question: under a fixed budget, which thousand images? Name the obvious answer
      and note that every ingredient is standard, so this is the composition anyone would try.
   3. What we built, in plain words, no notation. §3 carries the specification.
   4. **The negative, volunteered with its mechanism named but not quantified** (ViT move 4): the
      direction of the signal changes nothing we can resolve — and the reason is that what makes a
      targeted set different is the concentration, not the aim.
      *Source: `C1_RESULTS.md` §8.2; `SE_RESULTS.md` §6.4.*
   5. The scope sentence: one bar, one number. *Source: `se/abc_sigma.json`.*
   6. The second, independent contribution in two sentences. *Source: `CONTAMINATION_LEDGER.md`.*
   7. Contributions: **four items, one line each**, numbers only in the last.
4. **Cuts.** The "What we found, and how far the measurement reaches" paragraph (`:98–112`) — ten
   quantities and three noise bars → **§4**. The five multi-sentence contribution bullets
   (`:126–159`) → four one-liners; their evidence → §§4–7.
5. **Promotions.** None.
6. **Figures/tables.** None.
7. **Voice.** **K1–K8**, plus ViT §1: plain, declarative, near-zero notation. K4 binds hardest
   here — the forbidden-vocabulary list above is its enforcement.
8. **Preserved.** Nothing originates here; §4.1's register (`:462–470`) is the tonal target.

---

## §2 Background and related work

1. **Job.** Teach the five terms every verdict depends on, then place the work among systems that
   steer a generation budget.
   **Incoming handoff:** §1 called every ingredient standard; §2 says what each one is.
2. **Length.** 0.9 pp (from 1.35). **≤ 6 numbers.**
3. **Ordered beats.**
   1. **The background block** — artifact B. One labelled paragraph, ≤ 1 equation.
   2. Closest systems — LAKE-RED, S2R-COD — and exactly what we changed. Two sentences.
   3. The acquisition lineage: active learning, mean-teacher, core-set. Three sentences.
   4. The three budget-steering systems (GAUDA, DisCL, SynQuE) and the control none of them runs.
      **Two sentences replacing `tab:closest`.**
4. **Cuts.** `tab:closest` (`:216–246`) → **Appendix A** (`app:related`), saving 0.35 pp; ViT
   places no comparison table in related work. "Evaluation context" (`:247–255`) → **§3**.
5. **Promotions.** None.
6. **Figures/tables.** None in main text.
7. **Voice.** **K1–K8**, plus CamoDiffusion §3.1 for the background block (pay the background cost
   once, in a labelled place, immediately before it is needed) and ViT §2 for related work.
8. **Preserved.** The α-collision is *resolved* here by adopting τ (artifact F item 4).

---

## §3 The loop we built

1. **Job.** Specify the thing that failed precisely enough that the null means something — and no
   more precisely than that.
   **Incoming handoff:** the vocabulary is in place; §3 specifies what it will judge.
2. **Length.** 1.4 pp (from 1.55). **≤ 10 numbers.**
3. **Ordered beats.**
   1. The picture in four sentences (keep `:259–263` in spirit).
   2. Setting: source pool **4447**, target pool **4040** (3040 COD10K + 1000 CAMO), two endpoints.
      *Source: `D1_RESULTS.md`; `A3_RESULTS.md`:61.*
   3. The four allocation stages, as drafted (`:286–310`) — this passage already works.
   4. Equation 1 under **K7**, with the allocation temperature **renamed α → τ**.
   5. **The arms as a figure, not a list** (Figure 1). Prose names A0, A2, B, C10; CSHUF, CINV and
      CORACLE are deferred to §4–5 where they are used.
   6. The decision rule: the four verdict bands, compressed.
4. **Cuts.** → **Appendix B** (`app:method`): the Jaccard distinctness gate; the permutation
   selection rule (first of 64 draws, |ρ| ≤ 0.10, realised −0.03351); df bookkeeping; and the
   pre-registration provenance apparatus ("committed at a named commit", "append-only and dated",
   "thresholds that failed are reported failed") — which the Reproducibility statement already
   carries verbatim.
5. **Promotions.** None.
6. **Figures/tables.** **Figure 1 — arm diagram (NEW, must be built).**
7. **Voice.** **K1–K8**, plus CamoDiffusion §3.2's four-stage narration and its
   challenge → why-the-obvious-fails → our-fix → equation → what-it-buys micro-arc.
8. **Preserved.** The α-collision fix lands at `:302`.

---

## §4 Does targeting beat random?

1. **Job.** Deliver the null and, in the same section, close every standard objection to it with a
   measurement rather than a concession.
   **Incoming handoff:** the loop is specified; the first question is the one it was built to answer.
2. **Length.** 1.8 pp (from ~1.2 — this section **grows**). **≤ 25 numbers.**
3. **Ordered beats.**
   1. **The verdict in one sentence, one number.** *Source: `se/abc_verdict.json`.*
   2. **Table 1 — every trained comparison.**
   3. **The primary result at n = 8.** Δ(C10−B) = +0.00235 against a bar of 0.00686, 0.34×, sign
      6/8. Sixteen of sixteen gaps within noise; none reaches two-thirds of its bar.
      *Source: `se/abc_verdict.json`, `se/abc_sigma.json`.*
   4. **The seed-expansion passage — conclusion-first. Write it in this sentence order:**

      | | Sentence | Content |
      |---|---|---|
      | **(a)** | **Takeaway first** | With five more seeds per arm the effect is, if anything, *smaller* — and the measurement is now one we can trust. |
      | **(b)** | **Mechanism, one sentence** | Eight seeds give a truer estimate of the seed-to-seed spread than three did: the true spread is larger than the optimistic three-seed guess, while the gap itself halved (+0.00503 → +0.00235). |
      | **(c)** | **Numbers, one sentence, then the appendix** | The bar therefore sits at 0.0069 on df = 28 rather than the 0.0034 the pre-registration projected — wider, on 3.5× the degrees of freedom, and the gap now clears T2's tighter committed bar of 0.00553, which it did not at n = 3; Appendix D gives the per-arm spreads and the projection it replaces. |

      **The reader must never be asked to hold "wider bar = better" as a paradox.** (a) delivers
      the conclusion in plain language; (b) supplies the only mechanism needed; (c) is where df,
      the 1.24× widening and projection-vs-measurement are discharged and handed to the appendix.
      *Source: `SE_RESULTS.md` §6.3, §7; `PREREGISTRATION_SE.md`:167–174.*
   5. **Three objections, three closures** — one short paragraph each, under **K5**:
      - *"You picked a bad uncertainty estimator."* → **OR.** Substituting the true per-cluster test
        error for the score leaves all eight gaps within noise, none directionally stable (2/3
        everywhere); the score and the truth agree at ρ = +0.2372, so the replacement was four
        times better and moved nothing. *Source: `or/abc_verdict.json`; `results.md` §5.2.*
      - *"Your added data displaced rather than augmented."* → **FX.** Unpinning the schedule raises
        steps/epoch from 253 → 341 (SINet) and 127 → 171 (SINet-v2); the decisive gap stays within
        noise in all four cells and **shrinks** to +0.00144 at 2/3 sign. *Source:
        `fx/abc_verdict.json`; `FX_RESULTS.md` §§2, 4.*
      - *"Three seeds is not enough."* → **SE**, already delivered in beats 3–4.
   6. **The instrument is not blind.** PC: Δ = +0.01971 at 3.31× its bar, 3/3, `DETECTED` — and the
      honest half in the same paragraph: PC's own bar (0.005954) exceeds the decisive gap, so a
      positive control at 0.020 licenses *the instrument works*, not *it would have seen the effect
      we are nulling*. *Source: `PC/out/pc_verdict.json`.*
   7. **The sensitivity statement, once** (Decision D-4). One clause notes that formal
      equivalence is establishable at eight seeds and is reported in §5, where the asymmetry it
      reveals belongs; **no equivalence number is repeated here** (K2).
4. **Cuts.** → **Appendix D** (`app:diag`): the three-bar narrative (`:401–425`) reduced to one
   sentence plus a pointer; **the ABC n = 3 Welch interval and its "holds only just" caveat leave
   the main text entirely**; the A0-dominance arithmetic.
5. **Promotions.** None — Table 1 is assembled.
6. **Figures/tables.** **Table 1 — every trained comparison (ASSEMBLE).**
7. **Voice.** **K1–K8**, plus ViT §4.2: claim, table, one concession, pointer. K5 and K8 bind
   hardest here — this section replaces the draft's four hedging paragraphs with four measurements.
8. **Preserved.** PC's self-limiting half (`:434–440`) — among the best passages in the draft.

---

## §5 Concentration, not targeting

1. **Job.** Deliver the paper's positive result as a discovery, on three independent legs.
   **Incoming handoff:** the null says direction did not move the endpoint; why did targeting
   *look* like it worked?
2. **Length.** 1.4 pp. **≤ 20 numbers.**
3. **Ordered beats.**
   1. **Conclusion-first opening.** Do *not* pose the near-paradox and resolve it later; state the
      answer, then let the legs confirm it. Write it in this move order:

      | | Move | Content |
      |---|---|---|
      | **(a)** | **Takeaway first** | Targeting *looks* like it works — a probe tells a targeted training set from a random one easily, on images it has never seen. What actually makes the set different is that the budget is **concentrated on a few clusters**, not that it is **aimed** at the right ones. |
      | **(b)** | **The three legs, as evidence for (a)** | Beats 2–4 below. Each now confirms a claim the reader already holds rather than posing a fresh puzzle. |
      | **(c)** | **Equivalence asymmetry** | Unchanged — closes leg 2 (beat 3). |

      **The reader must never hold "the reversed arm also works" as a paradox.** Under (a) it is
      not a surprise but the expected consequence: if direction were what mattered, reversing it
      would hurt; it does not, and that is the evidence. The draft's §4.1 opening (`:462–470`) is
      still **preserved for its register**, but re-voiced to follow (a) rather than to pose the
      puzzle first (M9 tonal-seam check applies).
   2. **Leg 1 — geometry.** Targeted vs random separate at held-out d = 1.00–1.23; permuting the
      scores across clusters reproduces it at 0.91–1.14; an arbitrary cluster reproduces it again;
      only destroying the unevenness collapses it. Paired over twenty cells the signal adds +0.0073
      of a d against its own shuffle (13/20) and is **negative** at −0.0649 against an arbitrary
      cluster (4/20). What targeting buys is narrowness: effective-rank ratio **mean 0.634 across
      20/20 cells**, coverage unchanged. *Source: `C1_RESULTS.md` §§8.1, 8.2, 8.4, :254.*
   3. **Leg 2 — trained accuracy at n = 8 (NEW).** With concentration held exactly fixed, **CINV —
      the arm that deliberately reverses the signal — has the highest mean `S_α` in 4 of 4 cells**
      (3 of 4 at n = 3); C10 sits below random on both SINet-v2 cells. Every difference is within
      noise; the claim is **not that reversal helps but that there is no ordering by direction to
      be found.** Δ₄ carries the campaign's strongest sign consistency (8/8 on SINet·NC4K, 7/8 on
      SINet·COD10K) and still does not reach two-thirds of its bar. *Source: `SE_RESULTS.md` §6.4,
      which states this belongs here rather than in SE's own section.*

      **Close the leg with the equivalence asymmetry** — one sentence, marked post-hoc. At eight
      seeds, formal equivalence at δ = 0.005 is establishable for the *direction* contrasts on the
      primary architecture (C10 − CSHUF, p = 0.019; CSHUF − CINV, p = 0.049) but **not** for the
      targeting-vs-random gap (C10 − B, p = 0.101), which varies concentration as well as
      direction. **Direction is equivalent; concentration is not — the thesis in statistical
      form.** This replaces the draft's claim that equivalence "rejects nothing anywhere here",
      which was true at three seeds and is not true at eight. *Source: `results.md` §4;
      non-decisional per §SE.1 — see D-7.*
   4. **Leg 3 — boundary metrics (PROMOTED).** On SINet the concentration effect clears its bar:
      Boundary-IoU Δ(C10−B) = +0.0138 at 1.37×, 3/3; and **Δ(CINV−B) = +0.0135 at 1.34×, 3/3** —
      the same effect to within a tenth of a bar — while the direction contrasts sit at 0.37× and
      0.04×. The instrument resolves concentration and fails to resolve direction *in the same
      cells*, so the direction null is not an absence of sensitivity. *Source: `results.md` §5.3.*
   5. Qualifications — **three clauses, not three bolded paragraphs** (K8): not pre-registered and
      re-decides nothing; robust to binarisation (1.39/1.37/1.23× at 0.4/0.5/0.6); **SINet-v2
      resolves none of it.**
4. **Cuts.** → **Appendix D**: the full binarisation sweep; the three-way attenuation arithmetic
   (`:486–496`), which FX and SE have largely superseded.
5. **Promotions.** `tab:boundary` (labelled in `table_subgroup_metrics.tex`, `\input` at `:1061`
   inside Appendix E) → **Table 2, main text.**
6. **Figures/tables.** **Figure 2 — `fig:thesis`** (`figs/fig1_thesis.pdf`, exists; panel (b)
   updated to n = 8); **Table 2 — boundary metrics (PROMOTED).**
7. **Voice.** **K1–K8**, plus: this is the one section with **no hedging** — extend the draft's own
   instinct ("we state it without hedging") to the whole section. K3 governs each leg: say what the
   control does, then one number.
8. **Preserved.** The §4.1 opening (`:462–470`); the concentration/direction distinction itself.

---

## §6 Why it fails

1. **Job.** Leave the reader with **a single mechanism, not seven findings.** This section is one
   causal chain; if it reads as a list, it has failed at the thing it exists to do.
   **Incoming handoff:** concentration explains the appearance; §6 explains why the loop could
   never have delivered the substance.
2. **Length.** **0.75 pp** (rebalanced; see artifact H). **≤ 15 numbers.** The five links get
   the room; the two demotions stay at one clause each.
3. **The chain — write the connectives, not just the links.**

   | # | Link | Claim | **Connective into the next link** |
   |---|---|---|---|
   | 1 | **The data barely clusters.** Best silhouette 0.1600, with 0.1465 and 0.0568 in two other embedding spaces. *(`B1_RESULTS.md`:151, 272)* | a cluster-wise policy is drawing lines the data does not support | **— so** the partition is weak; **and even where it is real,** |
   | 2 | **Most of the error is not between clusters.** Only 20.5% of endpoint 1−`S_α` variance is between-cluster. *(`results.md` §5.2)* | four fifths of what a cluster-level allocation would have to fix is invisible to it however well aimed | **— so** aiming cannot reach it; **and what the budget does reach** |
   | 3 | **The budget behaves as a dataset selector.** 51.5% lands on CAMO images, which are 24.8% of the pool — 2.08× enrichment; the two largest quotas take 335 of 1000 and hold 7 of the 2026 endpoint images. *(`results.md` §5.1)* | "allocate by uncertainty" is in substantial part "allocate to CAMO" | **— and** the quantity it allocates *by* is itself the wrong one: |
   | 4 | **The signal predicts the wrong kind of error.** ρ(MAE) = +0.8553 against ρ(1−`S_α`) = +0.4276, and the ordering holds on 8/8 rows across three independent estimators and two architectures. *(`B1_RESULTS.md`:24–25; `T2C_RESULTS.md`:14)* | this is a property of uncertainty-guided allocation here, not a quirk of our score | **— and** even a perfectly aimed budget would be spending it on images that are not new: |
   | 5 | **The generator copies rather than invents.** The render set is a bijection onto 4447 foregrounds with 0 of 8885 objects showing regeneration; the generated distribution reaches 0.13–0.54 of the real target while the generator's *own input photographs* reach 0.71–0.75. *(`D1_RESULTS.md`:46–56; `A3_RESULTS.md`:75–77)* | the supply the policy allocates over is narrower than the pool it was drawn from | **— which closes the chain.** |

   **Worked shape of the chain** (structure to be written, not text to paste): *the data barely
   clusters — so a cluster-wise policy is partitioning noise; and even the real structure is mostly
   within-cluster — so four fifths of the target is invisible to any cluster-level allocation;
   meanwhile the budget behaves as a dataset selector — and the quantity steering it predicts the
   wrong kind of error; and beneath all of it the generator supplies no new objects at all.*

4. **Two demotions — one clause each, not paragraphs.**
   - **The A0 "pool size may matter" pattern.** ABC returns `REAL EFFECT` on A0→C10 at the
     secondary endpoint (+0.01089, 1.31×, 3/3) and FX returns two `INCONCLUSIVE` A0 gaps (+0.01201,
     +0.01345): *how many* images may matter where *which* images do not. Reported, not claimed.
     **One clause.** *Source: `abc_verdict.json`; `fx/abc_verdict.json`.* **Currently absent from
     the paper entirely.**
   - **The A1 withdrawal.** The conditioning channel is not narrow (0.907 vs 0.810 weight norms,
     dominant route bypassing the summary), so we withdrew our own candidate cause rather than
     leave it standing. **One clause.** *Source: `A1_SCOPING.md`.*
5. **Cuts.** → **Appendix C/E**: the area-control pass counts and the P ≈ 0.145 zero-margin
   discussion (one clause survives: partialling object area **raises** ρ(1−`S_α`) in 8/8 rows, the
   opposite of the confound's prediction); the full silhouette sweep; T2C's boundary-band failure
   (2/8 rows, four negative); the 5.4% cluster-instability floor if space is tight.
   **DELETE outright:** *"The first is also the largest open question this paper creates"*
   (`:645–652`). FX measured it; §4 beat 5 replaces it.
6. **Promotions.** None. `fig:clusterdiag` stays in the appendix — the budget does not fund it.
7. **Figures/tables.** None. The chain carries itself.
8. **Voice.** **K1–K8**, plus ViT §4.3: the failure presented as something the evidence predicts
   ("This seemingly discouraging outcome may be expected"), not as a confession. **K2 binds hardest
   here — one number per link, five numbers for five links.** The connectives in the table above
   are the section's spine; a paragraph that starts without one is a list item, not a link.
9. **Preserved.** The A1 withdrawal; the `Transfers:` content for these causes, which is gathered
   into §8 rather than tagged here.

---

## §7 CHAMELEON is mostly training data

1. **Job.** Deliver a fully independent, highly portable contribution at a quarter of its current
   length.
   **Incoming handoff:** the causes above are about our loop; this finding is about the benchmark
   everyone uses, and holds whether or not our loop worked.
2. **Length.** **0.7 pp** (from 3.0; 0.2 pp transferred to §6). **≤ 15 numbers.** Figure 3 shrinks
   to 0.25 pp (four pairs, not six), leaving ~0.45 pp of prose.
3. **Ordered beats** — three paragraphs and a figure.
   1. **The finding and the failure of the standard check.** 50 of 76 (65.8%) are re-encoded,
      rescaled or cropped copies of COD10K-train and CAMO training images — 44 with partners in
      COD10K-train, 6 in CAMO. Exact hashing returns **0** because not one byte matches while every
      pixel does. 16 resolve neither way, so 50 is a floor. *Source: `CONTAMINATION_LEDGER.md`;
      `D2_FINAL_AUDIT/out/final_verdicts.csv`.*
   2. **How we know.** Two tiers — same-dimension re-encode (41) and homography-warped residual for
      rescales and crops (9: residual 3.8–12.1 on 0–255, correlation 0.96–1.00, scales
      0.39×–6.36×). Operating point 20 inliers, set one above the NC4K control's maximum of 19.
      Verified against an author-sourced release, byte-identical at 76/76. Negative control:
      **0 of 120** at the geometric tier and 0 of 4121 at the pixel tier.
      *Source: `CONTAMINATION_LEDGER.md`; `D2_NC4K`.*
   3. **What we claim and what we do not** — **Null B verbatim from A.2** — then the protocol
      recommendation: only 10 images are clean with respect to the training pool, and one of those
      is byte-identical to a CAMO-250 image, so retire rather than subset.
   4. **Footnote, not a paragraph** (moved under the 0.2 pp transfer): the protocol under test uses
      COD10K-train as its unlabelled target domain, which holds **the same 44** CHAMELEON images.
   5. **Figure 3** — confirmed pairs.
4. **Cuts.** → **Appendix G/H** (`app:chamext`, `app:masks`), both of which exist: the tolerance
   sweep (11/26/37/40/41) and the 7.36× nearest-neighbour jump; the three byte-identical
   CHAMELEON↔CAMO-250 files; the two mask releases (IoU 0.6932, 27/76 identical, MAE moves 2.7×);
   the excluded tenth candidate and its shear decomposition (−86.5°, 0.24 vs 1.24); the calibration
   band (525–1174 inliers); our own 10/76 first-implementation bug; Stage 1's 0/25 contribution.
5. **Promotions.** `fig:chamext` / `fig:pairs` (`figs/fig_chameleon_pairs.pdf`;
   `D2_FINAL_AUDIT/out/sheet_extension.png`) → main text.
6. **Figures/tables.** **Figure 3 — confirmed pairs (PROMOTED, 4 pairs).** `tab:contamination`
   stays in the appendix.
7. **Voice.** **K1–K8**, plus: flat and factual. The finding does not need help, and K8 means at
   most one qualifying sentence in the whole section ("16 resolve neither way, so 50 is a floor").
8. **Preserved.** Null B's self-discipline — we measured for inflation, did not find it, and did
   not write the quotable sentence. The 10/76 self-correction survives as a clause or moves to the
   appendix. **Promote from `\subsection` of the Discussion to a top-level `\section`.**

---

## §8 Discussion and conclusion

1. **Job.** Say what transfers, and what would have to be true for the idea to work.
   **Incoming handoff:** two findings, one methodological thread.
2. **Length.** **0.30 pp** (rebalanced; ~195 words, longer than ViT's 175-word conclusion). **≤ 3 substantive numbers** (exemplar rate 0–13 per 1000 words;
   current draft 105).
3. **Ordered beats.**
   1. The geometric/downstream distinction — **stated once, here, and nowhere else.**
   2. **The gathered `Transfers:` claims**, currently scattered as bolded tags across four
      subsections where no reader will assemble them:
      - the three checks that cost no training and should precede any cluster-wise allocation — the
        silhouette, the composition of the funded clusters against the pool they are drawn from,
        and the between-cluster share of endpoint error variance;
      - the discriminating control is a same-shape shuffle, not a random baseline;
      - a null on the endpoint metric does not license a null on the quantity the acquisition
        signal was built to move;
      - a real-vs-synthetic AUC near 1.0 is near-vacuous evidence — a JPEG re-save of identical
        images separates at 0.9928. *(`A3_RESULTS.md`:124)*
   3. What would have to change for the loop to have a chance.
   4. One sentence closing the thread: a control that returns zero is informative only if it could
      have returned something else.
4. **Cuts.** Any recap of the sensitivity arithmetic; the fourth restatement of the two-evidence
   split; all `% AUTHORS:` comments in the three statements (artifact F item 7).
5. **Promotions.** None.
6. **Figures/tables.** None.
7. **Voice.** **K1–K8**, plus ViT §5: what we did, what is simple about it, what remains. K2 is
   absolute here — three numbers total.
8. **Preserved.** The `Transfers:` device — the paper's best answer to "why should a non-COD reader
   care", and a device none of the three exemplars uses.

---

# PART 6 — Supporting artifacts

## B. §2 background-block spec

One labelled paragraph. Each term gets one plain sentence; the block must be readable by someone
who has never opened a COD paper.

| Term | Definition to be written | Source | Status |
|---|---|---|---|
| **`S_α` (S-measure)** | A structural-similarity score between a predicted mask and the true one; runs 0–1, higher is better; **every model in this paper scores near 0.70**, so a difference of 0.005 is about half a percent of the operating range. State α = 0.5. | `results.md` §§2–3; `ABC/PREREGISTRATION.md` | **NON-NEGOTIABLE — currently never defined in the main text.** First used at `:148`; pinned to α = 0.5 only in Appendix B (`:961`). |
| **arm** | One training condition. All arms share a base pool and differ only in which 1000 images are appended. | `:311` | Move forward from §3.3; used in the abstract at `:42`. |
| **seed** | One training run of one arm. Repeat runs of the same arm do not return the same score, and that spread is what any real difference must beat. | `:337` | Move forward. |
| **endpoint** | A held-out test set the verdict is read from: COD10K-test decides, NC4K is reported. | `:270` | Move forward. |
| **the reference effect** | The improvement this repository reproduced for the published method, 0.7030 → 0.7172 = **+0.0142** — the size of effect the design had to be able to see. | `ABC/PREREGISTRATION.md` §2.9 | Currently used at `:102` as "126%" with no plain-language anchor. |

## C. Figure and table plan

| Asset | Status | Source / what must be built | § | Est. |
|---|---|---|---|---|
| **Figure 1 — arm diagram** | **NEW — must be built** | No asset exists. Two-axis schematic: *concentration* (dispersed → concentrated) × *direction* (reversed / destroyed / arbitrary / targeted / oracle), placing A0, A2, B, C10, CSHUF, CINV, CORACLE and the FX variants. Adapts BiRefNet Fig. 2. Data: `abc_pools.json`, `t2/abc_pools.json`. | §3 | 0.25 pp |
| **Figure 2 — concentration thesis** | **EXISTS** | `Paper/figs/fig1_thesis.pdf`, built by `figs/make_fig1.py`. Panel (a) held-out Cohen's d by rule; panel (b) trained `S_α` at fixed shape. **Update (b) to n = 8** from `se/abc_metrics.csv`. | §5 | 0.30 pp |
| **Figure 3 — confirmed pairs** | **EXISTS, promote** | `Paper/figs/fig_chameleon_pairs.pdf` (`fig:pairs`, `:1069`) and `D2_FINAL_AUDIT/out/sheet_extension.png`. **Four pairs** spanning Tier A and Tier B. | §7 | 0.25 pp |
| **Table 1 — every trained comparison** | **ASSEMBLE** | Rows: ABC / T2 / OR / FX / SE / PC. Columns: campaign, n, gap, Δ, bar 2σ̂, ratio, sign, verdict. Sources: `abc_verdict.json` + `abc_sigma.json` in `out/`, `out/t2/`, `out/or/`, `out/fx/`, `out/se/`, plus `PC/out/pc_verdict.json`. | §4 | 0.35 pp |
| **Table 2 — boundary metrics** | **PROMOTE** | `tab:boundary`, labelled in `Paper/table_subgroup_metrics.tex`, `\input` at `:1061`. Trim to two architectures × {Boundary-IoU, Boundary-F} × {C10−B, CINV−B, C10−CSHUF, C10−CINV}. | §5 | 0.25 pp |

Total **1.40 pp** of 9.0 — in line with the exemplars (ViT: 2 tables + 7 figures in 9 pp).

## D. Evidence-to-narrative table

`SCOPING` Part 4.1, with every "absent" and "running" status resolved.

| # | Exp | Role | Section | Status → after |
|---|---|---|---|---|
| 1 | E0 | infrastructure; the 5.4% floor is a scope constant | §6 link 1 (optional); Repro stmt | partial → trimmed |
| 2 | D1 | motivation + scope-setter | §3 beat 2; §6 link 5 | §5.1 only → moved up |
| 3 | D2 | **core — second headline** | §7 beat 1 | §5.2 → §7, promoted to `\section` |
| 4 | D2_NC4K | control | §7 beat 2 | yes → one sentence |
| 5 | D2_reaudit | robustness + Null B | §7 beat 3 | yes → compressed |
| 6 | D2_FINAL_AUDIT | core extension | §7 beat 1 | yes (50) → unchanged |
| 7 | B1 | mechanism, links 1 & 4 | §6 links 1, 4 | §4.3/§4.4 → §6 |
| 8 | C1 | **CORE — positive result, leg 1** | §5 beat 2 | §4.1 → §5 |
| 9 | A1 | withdrawal | §6 demotion 2 | 1 clause → 1 clause |
| 10 | A3 | mechanism link 5 + a transfer | §6 link 5; §8 | appendix → §6 |
| 11 | ABC | **CORE — the null** | §4 Table 1 | §4 → kept; **the `REAL EFFECT` A0→C10 cell added to §6 demotion 1** |
| 12 | T2 | core control (direction, n = 3) | §4 Table 1; §5 | §3.4/§4.1 → split |
| 13 | T2C | robustness | §6 link 4 | §4.4 → one clause |
| 14 | AC | control | §6 cuts | §4.4 → one clause |
| 15 | PC | control — instrument sensitivity | §4 beat 6 | yes → kept |
| 16 | **OR** | control — "no score could have" | §4 beat 5 | **ABSENT → §4** |
| 17 | **FX** | control — kills the strongest objection | §4 beat 5 | **ABSENT → §4** |
| 18 | **SE** | **core — the null at n = 8** | §4 beats 3–4; §5 leg 2 | **ABSENT → §4 + §5** |
| 19 | DIAG | sharpens the null; proves the thesis on accuracy | §5 leg 3; §6 links 2–3 | boundary table in appendix → **promoted** |

## E. Claims ledger

**A number not in this ledger does not enter the main text.** Scope: substantive empirical numbers
appearing in *prose*. Table interiors are specified in C; citation years and cross-references are
out of scope.

**Density caps** (`SCOPING` P4; exemplars run 41–52 per 1000 words in abstract+intro, 70–74
overall, 0–13 in the conclusion):

| Abstract | §1 | §2 | §3 | §4 | §5 | §6 | §7 | §8 | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 12 | 6 | 10 | 25 | **22** | 15 | 15 | 3 | **≤ 116** |

Against ~1004 in the current 12-page draft.

| Value | Claim it supports | Source file | § |
|---|---|---|---|
| 103 trained runs (ABC 24, T2 12, PC 3, OR 6, FX 18, SE 40) | scale, claimed once | `SE_RESULTS.md` §3 | abs, §1 |
| 4447 / 4040 | source pool, target pool | `D1_RESULTS.md`; `A3_RESULTS.md`:61 | §3 |
| 3040 + 1000 | the target pool is a two-dataset mixture | `A3_RESULTS.md`:61 | §3, §6 |
| 5447 | pool size held equal across A2/B/C10 | `abc_pools.json` | §3 |
| k = 75, B = 1000, τ = 1.0, a = 0.9, b = 0.3 | allocation specification | `:286–310` | §3 |
| 0–1, ≈ 0.70, α = 0.5 | `S_α` range and operating point | `results.md` §2 | §2 |
| 0.7030 → 0.7172 = +0.0142 | the reference effect | `ABC/PREREGISTRATION.md` §2.9 | §2, §4 |
| **+0.00235** | decisive gap at n = 8 | `se/abc_verdict.json` | abs, §1, §4 |
| **0.00686** (2σ̂, df = 28) | the bar the gap is read against | `se/abc_sigma.json` | abs, §1, §4 |
| 0.34×, 6/8 | how far inside the bar | `se/abc_verdict.json` | §4 |
| 16 of 16 within noise | the SE verdict | `se/abc_verdict.json` | §4 |
| +0.00503 → +0.00235 | the gap halved from n = 3 to n = 8 | `abc_verdict.json`, `se/abc_verdict.json` | §4 |
| 0.00553 | the null now clears T2's tighter committed bar | `t2/abc_sigma.json` | §4 |
| df 8 → 28 | why the wider bar is the better one | `se/abc_sigma.json` | §4 |
| ~0.0034 (projected) | the pre-registered branch that would have forced withdrawal | `PREREGISTRATION_SE.md`:167–174 | §4 |
| **[−0.0020, +0.0067]**, df = 10.44 | n = 8 interval; excludes 0.0142 by >2× | `results.md` §4 | §4 |
| 5 of 16, TOST p < 0.05 at δ = 0.005 | direction contrasts reach formal equivalence; C10−B does not | `results.md` §4 | §4 |
| +0.01971, 3.31× bar, 3/3 | PC — the instrument detects a real effect | `PC/out/pc_verdict.json` | §4 |
| 0.005954 > 0.00503 | PC's own bar exceeds the decisive gap | `PC/out/pc_verdict.json` | §4 |
| 8 of 8 within noise, 2/3 sign | OR — a perfect score changes nothing | `or/abc_verdict.json` | §4 |
| ρ = +0.2372 | score vs true per-cluster error | `results.md` §5.2 | §4 |
| 253 → 341, 127 → 171 | FX — the schedule was genuinely unpinned | `FX_RESULTS.md` §§2, 4 | §4 |
| +0.00144 | FX — the gap shrinks when the data is trained on | `fx/abc_verdict.json` | §4 |
| d = 1.00–1.23 | targeted and random separate | `C1_RESULTS.md` §8.1 | §1, §5 |
| 0.91–1.14 | the shuffle reproduces the separation | `C1_RESULTS.md` §8.1 | §5 |
| +0.0073, 13/20 | the signal's contribution over its own shuffle | `C1_RESULTS.md` §8.2 | §5 |
| −0.0649, 4/20 | the signal is *negative* against an arbitrary cluster | `C1_RESULTS.md` §8.2 | §5 |
| mean 0.634, 20/20 | targeting buys narrowness, not reach | `C1_RESULTS.md`:254 | §5 |
| 4 of 4 cells (3 of 4 at n = 3) | CINV holds the highest mean at n = 8 | `SE_RESULTS.md` §6.4 | §1, §5 |
| 8/8, 7/8 | Δ₄ sign consistency, still under the bar | `se/abc_verdict.json` | §5 |
| +0.0138, 1.37×, 3/3 | boundary — concentration resolves | `results.md` §5.3 | §5 |
| +0.0135, 1.34×, 3/3 | boundary — the reversed arm captures it in full | `results.md` §5.3 | §5 |
| 0.37×, 0.04× | the direction contrasts do not resolve | `results.md` §5.3 | §5 |
| 1.39 / 1.37 / 1.23× | robust to binarisation | `results.md` §5.3 | §5 |
| 0.1600 / 0.1465 / 0.0568 | **chain link 1** — the data barely clusters | `B1_RESULTS.md`:151, 272 | §1, §6 |
| 20.5% | **chain link 2** — most error is within-cluster | `results.md` §5.2 | §6 |
| 51.5% vs 24.8%, 2.08× | **chain link 3** — the budget is a dataset selector | `results.md` §5.1 | §1, §6 |
| 335 / 1000, 7 of 2026 | the budget is aimed where the endpoint is not | `results.md` §5.1 | §6 |
| +0.8553 vs +0.4276 | **chain link 4** — the signal points at pixel error | `B1_RESULTS.md`:24–25 | §6 |
| 8 of 8 rows | the ordering generalises across three estimators | `T2C_RESULTS.md`:14 | §6 |
| 8 of 8 rows (raised) | the area control refutes the confound by direction | `AC_RESULTS.md`:65 | §6 |
| 4447/4447 bijection, 0 of 8885 | **chain link 5** — the generator copies objects | `D1_RESULTS.md`:46–56 | §6 |
| 0.13–0.54 vs 0.71–0.75 | synthetic covers the target worse than its own input | `A3_RESULTS.md`:75–77, 104–106 | §6 |
| +0.01089, 1.31×, 3/3 | ABC `REAL EFFECT` — pool size may matter | `abc_verdict.json` | §6 |
| +0.01201, +0.01345 | FX `INCONCLUSIVE` A0 gaps, same pattern | `fx/abc_verdict.json` | §6 |
| 0.907 vs 0.810 | A1 — the channel is not narrow; hypothesis withdrawn | `A1_SCOPING.md` | §6 |
| **50 / 76 (65.8%)** | CHAMELEON contamination | `CONTAMINATION_LEDGER.md`; `final_verdicts.csv` | abs, §1, §7 |
| 41 + 9 | two tiers | `final_verdicts.csv` (`tier`) | §7 |
| 16 unchecked, 10 clean | 50 is a floor | `final_verdicts.csv` (`verdict`) | §7 |
| 44 + 6 | partners in COD10K-train / CAMO — **the same 44** as the target-pool claim | `final_verdicts.csv` (`pool`) | §7 |
| **0** | exact hashing returns no collisions | `D2_reaudit` | abs, §1, §7 |
| 76 / 76 byte-identical | author-sourced verification | `D2_reaudit` | §7 |
| 3.8–12.1, 0.96–1.00, 0.39×–6.36× | Tier-B residual evidence | `CONTAMINATION_LEDGER.md` | §7 |
| 20 inliers, NC4K max 19 | the operating point is set by the control | `CONTAMINATION_LEDGER.md` | §7 |
| 0 of 120, 0 of 4121 | the negative control is clean | `D2_NC4K`; `CONTAMINATION_LEDGER.md` | §7 |
| 0.448–0.559 | **Null B** — no score inflation found | `D2_reaudit` | §7 |
| 0.9928 | a real-vs-synthetic AUC near 1.0 is near-vacuous | `A3_RESULTS.md`:124 | §8 |

**Flagged — must not be used until resolved (Decision D-6):** `0.7136`; the C1 p-values
`P ≈ 0.13` / `P ≈ 0.006`; the "41 known pairs" validation claim (the ledger says **8**); A3's
`243.3 → 193.2` and `0.6490 → 0.6886`.

## F. Consistency-fix checklist

| # | Site(s) | Fix |
|---|---|---|
| 1 | `:42` (36), `:98` (24), `:377` (24), `:862` (36), `:945` (24) | Replace with **103 trained runs**, broken down once: ABC 24, T2 12, PC 3, OR 6, FX 18, SE 40. State the scope per sentence where a subset is meant. |
| 2 | `:645–652` | **DELETE** *"The first is also the largest open question this paper creates"* and its concession. Replace with the FX measurement (§4 beat 5). |
| 3 | `results.md` §§1, 5.4; `EXPERIMENTS_EXPLAINED.md` §§17, 18 | 51/76 → **50/76**; 15 unchecked → **16**; SE status → COMPLETE. Requires P1–P3. `main_v2` already says 50. |
| 4 | `:302`, `:141`, §3.2 equation block | **Rename the allocation temperature α → τ**: `T = τ · sd(es)`, `τ = 1.0`. Keep `S_α` (field notation). One clause in §2 noting the two were distinct quantities sharing a symbol. |
| 5 | `:476` | *"a previously claimed 0.10"* → attribute explicitly to **our own earlier estimate**, refuted by C1. It currently reads as a criticism of a cited work. |
| 6 | `:24–25` | Delete the `\fix` and `\new` margin macros. |
| 7 | `:804–810`, `:846–848`, `:872–875` | Resolve and delete every `% AUTHORS:` comment in the AI Use, Ethics and Reproducibility statements. Each requests a confirmation not recorded as made. |
| 8 | `:710` | *"Run first on the 41 known pairs"* → the instrument was validated on **8** of the 41. |
| 9 | `:447` | `0.7136` — cite the external source or delete. |
| 10 | `:481` | `0.634` is the **mean** effective-rank ratio across 20/20 cells (per-cell range 0.538–0.640). Say "mean". |
| 11 | `:139`, §7 | The two `44`s are the **same images**. State it, or they read as independent corroboration. |
| 12 | `:477–479` | The C1 p-values — label as derived one-sided sign tests, or drop. |
| 13 | `:401` | *"this campaign resolved coarsely"* — per `PREREGISTRATION_SE.md` §SE.1, **rewrite against SE's bar, do not delete.** |
| 14 | `:451`, `:454–456` | Delete the duplicated `% 5. DISCUSSION` marker and the orphan paragraph addressing a prior revision. |
| 15 | `:247–255` | Move "Evaluation context" from §2 to §3. |

## G. Appendix reorganization

| Cut from | Lands in | Exists? |
|---|---|---|
| `tab:closest` (§2) | **A** `app:related` (`:884`) | section exists; table moves |
| Provenance apparatus, Jaccard gate, permutation rule, df bookkeeping (§3) | **B** `app:method` (`:933`) | exists; extend |
| Three-bar narrative, **the ABC n = 3 Welch interval**, A0-dominance arithmetic (§4) | **D** `app:diag` (`:1026`) | exists; extend |
| Binarisation sweep, attenuation arithmetic (§5) | **D** `app:diag` | exists |
| Area-control pass counts, silhouette sweep, T2C boundary-band failure (§6) | **C** `app:tables` (`:983`) — `tab:areacontrol`, `tab:silhouette`, `tab:t2cfull` | **all three exist** |
| Tolerance sweep, NN jump, CAMO-250 triple, mask releases, excluded 10th candidate, calibration band, the 10/76 bug, Stage 1's null (§7) | **G** `app:chamext` (`:1167`), **H** `app:masks` (`:1247`) | exist; extend |
| Setup-specific limitations, A1 withdrawal detail (§6) | **E** `app:tier1` (`:1097`) | exists |
| **SE campaign detail** — per-run metrics, the 2026-09-20 interruption record, the bar-widening analysis, `n_appended` by arm | **NEW appendix section** | **must be written**; source `SE_RESULTS.md` §§3–6 |
| **OR and FX detail** — pre-registrations, the oracle's test-label disclosure, FX's four bundled changes, the 11-of-12 cross-schedule negatives | **NEW appendix section(s)** | **must be written**; source `PREREGISTRATION_OR.md`, `FX_RESULTS.md` |
| Per-run metrics for all runs | **C** `app:tables` — `tab:perrun` | exists; **must grow from 36 to 103 rows** via P1 |

## H. Page budget

| § | Section | Pages | Now | Δ |
|---|---|---|---|---|
| — | Title + abstract | 0.3 | 0.55 | −0.25 |
| 1 | Introduction | 1.2 | 1.6 | −0.4 |
| 2 | Background and related work | 0.9 | 1.35 | −0.45 |
| 3 | The loop we built | 1.4 | 1.55 | −0.15 |
| 4 | Does targeting beat random? | 1.8 | ~1.2 | **+0.6** |
| 5 | Concentration, not targeting | **1.65** | ~1.3 | +0.35 |
| 6 | **Why it fails** | **0.75** | ~1.3 | −0.55 |
| 7 | **CHAMELEON is mostly training data** | **0.7** | ~2.7 | **−2.0** |
| 8 | Discussion and conclusion | **0.30** | ~0.45 | −0.15 |
| | **Main text** | **9.0** | **~11.9** | **−2.85** |

The "Now" column is measured from the compiled PDF by page fraction and is approximate to ±0.1 pp;
the §6 and §7 rows split the draft's current §5, whose limitations subsection (5.1) is counted in
§6 and whose contamination subsection (5.2) is counted in §7.
| — | Statements | 1.0 | 1.0 | see D-2 |

**Change from the scoping budget:** §6 rises 0.7 → 0.9 pp and §7 falls 0.9 → **0.7 pp**.

**Rebalance at the §5 gate (2026-09-22), author-approved.** §5 measured ~1.65 pp against a 1.4
target and would not come down without cutting the paper's thesis: it carries both a table and a
full-width figure, ~0.55 pp of floats against 0.85 pp of allowed prose, and two rounds of trimming
recovered only ~0.1 pp. Rather than mutilate the thesis section or carry the overage into §1 and the
abstract --- which the Step 0.5 amendment forbids --- the budget moves: **§5 1.4 → 1.65**, **§6
0.9 → 0.75**, **§8 0.4 → 0.30**. Net zero; the total holds at 9.0. §6 keeps most of the headroom
Step 0.5 gave it (0.75 against the scoping brief's 0.7), and §8 at 0.30 pp is ~195 words, which is
longer than ViT's 175-word conclusion. §3 measured ~1.45 against 1.4 and that 0.05 is carried
against the residual, leaving **≈ 0.70 pp**. §6 needed the room because a five-link chain with
connectives cannot be written in 0.7 pp without collapsing into the list it exists to replace; §7
absorbs the cut by moving its protocol-instance paragraph to a footnote and shrinking Figure 3 from
six pairs to four.

**Arithmetic.** Cuts ≈ **3.75 pp**: contamination 2.0, `tab:closest` 0.35, noise bars 0.4, intro
0.4, limitations 0.3, area control 0.25, structural seams 0.05.
Spend ≈ **1.65 pp**: OR/FX/SE 0.6, background block 0.3, Figure 1 0.25, Table 2 0.25, Figure 3 0.25.
Net **−2.10 against a required −2.85**, leaving **≈ 0.75 pp** to come from the density correction:
~100 numbers and their carrying clauses leave the abstract and introduction (132 → ~45 numbers per
1000 words ≈ 0.5 pp), and §8 falls from 105 numbers per 1000 words to ≤ 3, supplying the rest.

**This is not a residual trim.** §1 and the abstract are written **to their caps at their own
gates** (Part 7, execution contract), so by the time the final pass runs this reduction is already
realized and the pass only confirms it. If the budget has not closed, the remainder is found
**outside** §1 and the abstract — those two are never compressed after the fact, because they are
the highest-leverage prose in the paper and the density problem they carry is what motivated the
rewrite. The D-2 contingency is the fallback if it still does not close.

**Contingency if the statements count against the 9 pp (D-2):** §7 → 0.6 pp, §2 → 0.7 pp, §5 → 1.2
pp. Recovers 1.0 pp.

---

# PART 7 — Execution protocols

## L. Accuracy protocol

Applies to every section as it is drafted.

| # | Rule |
|---|---|
| **L1** | **A number may appear in the main text only if it is in the claims ledger (artifact E) with its source.** |
| **L2** | **Before finalizing a section, re-read the cited artifact and confirm the value.** Not from this plan, not from memory — from the file. |
| **L3** | **`main_v2.tex` is not a source of numbers.** It is demonstrably stale: SE, OR and FX are absent; it carries the "largest open question" line that FX closed; its supporting documents disagree with it on 50-vs-51. Numbers come only from the regenerated artifacts of P1–P3. |
| **L4** | **A number not in the ledger is flagged for the author, never written from memory.** If a section needs a quantity the ledger lacks, stop and add it to the ledger with its source first. |
| **L5** | The project's inherited provenance rule holds: where a document and its `EXP` log block disagree, **the log wins** and the document is wrong. |
| **L6** | The five C4-flagged values are blocked until Decision D-6 resolves them. |

## M. Fluency-and-accuracy pass

Run **after each section is drafted**, before moving to the next. Nine checks; a section is not
done until all nine pass.

| # | Check |
|---|---|
| **M1** | Numeric density is within the section's ledger cap (artifact E). |
| **M2** | Every paragraph opens with its claim as the topic sentence (**K1**). |
| **M3** | The section opens by making its incoming handoff (**J.2**) and closes forward (**K6**). |
| **M4** | Every term is defined before first use; nothing is defined outside the §2 background block (**K4**). |
| **M5** | Every number resolves to a ledger row with its source, and the source was re-read (**L1, L2**). |
| **M6** | Numbers in prose are relative and appear once; no value is repeated across sections (**K2**). |
| **M7** | At most one reader-instruction in the section; every other concession is a clause plus a pointer to a control (**K5, K8**). |
| **M8** | The section advances at least one spine sentence (**J.1**). A passage advancing none is a candidate cut. |
| **M9** | **Tonal-seam check.** Flag every place a *preserved* passage sits inside newly written prose as a possible seam to re-voice. Known seams: the §4.1 opening inside §5; the `Transfers:` tags gathered into §8; PC's self-limiting half inside §4; Null B's wording inside §7. Preserved passages keep their substance; they may need their connective tissue rewritten to match the surrounding voice. |

## Execution contract

**The rewrite runs section by section, stopping after each section for author review before the
next begins.** It is not a single pass. Order follows the spine:

> §2 → §3 → §4 → §5 → §6 → §7 → §8 → **§1** → **abstract**

§2 goes first because its background block defines every term K4 then binds the rest of the paper
to. §1 and the abstract go last because they are written *from* the finished sections.

**§1 and the abstract are full gates, not a close-out.** Each gets its own gate with the complete
M1–M9 pass, exactly like §2–§8, and each is written **to its ledger cap as it is drafted**
(abstract ≤ 160 words / ≤ 8 numbers; §1 ≤ 650 words / ≤ 12 numbers) — never drafted long and
trimmed to cap afterwards. Both are reviewed before the final passes begin.

The reason is in the measurement that motivated this whole rewrite: the abstract and introduction
run at **132 numbers per 1000 words against the exemplars' 41–52**, and at 1151 words against ViT's
524. They are where the paper is won or lost with a reviewer who reads nothing else, which makes
them the highest-leverage prose in the document — not the place to absorb whatever page debt is
left over. Artifact H's budget is written on that basis.

The execution prompt inherits this contract, artifacts J–M, and the ledger.

---

# PART 8 — Decisions (artifact I)

Items 1–5 are adopted as **provisional defaults** so the specs above are concrete. All remain open
for author sign-off.

| # | Decision | Provisional default | Status |
|---|---|---|---|
| **D-1** | May the plan override the brief's *"tightened (~0.0034) bar"* with the measured widening? | **Yes.** `SE_RESULTS.md` §7 requires it; the projection was conditional on spreads that did not hold. | **Adopted; confirm.** |
| **D-2** | Do the Ethics and Reproducibility statements count against the ICLR 2027 9 pp limit? | Assumed **excluded**, as ICLR normally does. | **Open — not verifiable from the repo. Needs the 2027 CFP.** Worth 1.0 pp; contingency in H. |
| **D-3** | Final title | **T1** — *Concentration, Not Targeting: A Pre-Registered Null for Uncertainty-Guided Synthetic Data in Camouflaged Object Detection* | **Adopted; confirm.** |
| **D-4** | The headline sensitivity statement | **SE's pre-registered bar, 2σ̂ = 0.00686 at df = 28, as the decisive statement; the regenerated SE n = 8 Welch interval as the supporting post-hoc statement; the ABC n = 3 interval removed from the main text.** Supersedes `SCOPING` F9. | **Adopted; confirm.** Requires P1 — the indicative interval must be regenerated by the committed script. |
| **D-5** | α → τ rename for the allocation temperature | **Adopted.** `S_α` unchanged. | **Adopted; confirm the symbol.** |
| **D-6** | The five unverifiable values (C4) | **Blocked from the main text** until cited, derived-and-labelled, or dropped. | **Open — author input needed on `0.7136` in particular.** |
| **D-7** | SE's TOST equivalences — **5 of 16 gaps reach p < 0.05 at δ = 0.005**, including two direction contrasts on the primary architecture | Report as **post-hoc and non-decisional**, per §SE.1, which forbids promoting statistics into the decision after the fact — but **do report them**, and report the asymmetry: direction contrasts reach equivalence, the targeting-vs-random gap does not. That asymmetry is the thesis in statistical form. Replaces the draft's "rejects nothing anywhere here". | **Open; recommend as stated.** |
| **D-10** | `results.md` §4's hardcoded *"one line worth reading"* paragraph still points at the ABC n = 3 interval | **Repoint it at the SE n = 8 interval** under D-4. Requires a one-paragraph edit to `make_results.py`. | **Open — left unchanged pending D-4.** |
| **D-8** | The abstract arc specified in the brief ends at "scope" and omits the CHAMELEON contribution | **Add it** as a final ~25-word sentence; it is an independent headline contribution and the abstract is where a reviewer decides whether the paper has two results or one. | **Open — a deviation from the specified arc, raised rather than taken silently.** |
| **D-9** | Does the A0 "pool size may matter" pattern enter §6? | **Yes**, as one clause. It is the only pattern pointing away from the conclusion, it now has an ABC `REAL EFFECT` cell and two FX `INCONCLUSIVE` cells behind it, and it is absent from the paper. | **Adopted; confirm.** |

---

# PART 9 — Verification

The plan is correctly executed when:

1. **Numbers.** Every value in the main text resolves to an artifact-E row with its source, and
   each was re-read per L2. The five C4-flagged values appear nowhere. No number is taken from
   `main_v2.tex` (L3).
2. **Density.** Per-section prose counts fall within the artifact-E caps; abstract+intro lands near
   45 numbers per 1000 words against the current 132.
3. **Coherence.** Every section opens by making its J.2 handoff and closes forward; every section
   advances at least one J.1 spine sentence; §6 reads as one chain, with an explicit connective
   between each of its five links.
4. **Budget.** Sections sum to 9.0 pp; the cut/spend arithmetic reconciles to the stated ~0.75 pp
   residual, and the residual is actually recovered by the density correction rather than carried.
5. **Consistency.** All fifteen artifact-F items are applied. Run counts read 103 with the
   breakdown given once. The contamination count reads 50 everywhere, including in the regenerated
   supporting documents.
6. **Completeness.** OR, FX and SE each have a named home in §4, and SE additionally in §5. All six
   `SCOPING` 3.3 "must survive" items appear in a *Preserved* field: the §4.1 opening (§5), the
   `Transfers:` device (§8), the concentration/direction distinction (§5), the contamination
   self-discipline (§7), the A1 withdrawal and 10/76 correction (§6, §7), the α-collision flag
   (§3, F-4).
7. **Process.** Each section passed all nine M-checks before the next was begun, and the author
   reviewed each before the next began.
8. **Scope.** `main_v2.tex` is edited only during execution, never during planning.

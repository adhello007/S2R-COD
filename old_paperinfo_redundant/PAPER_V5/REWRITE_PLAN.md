
# PAPER_V5 — Rewrite plan: write outward

**Scope: exposition only.** Every number, verdict, claim, scope limit, and citation placeholder in
V4 is preserved. Nothing is measured, added, softened, or strengthened. The paper is rewritten for a
competent ICLR reviewer from an adjacent field who has never worked on camouflaged object detection.

**Governing test, applied before every sentence:** *what does a smart stranger need to already know
for this sentence to land, and have I given it to them yet?* If not, give it first.

**Decisions fixed before this plan was written** (agreed with the author):

1. **Paper title unchanged.** For a null result, a reviewer scanning titles needs the word "pre-registered". But `\section{The Pre-Registered Null}` becomes **"The Null Result"**, and §4's heading becomes **"Setup, and the Rules We Fixed in Advance"**.
2. **The abstract keeps exactly two result figures:** `41 of 76 (53.9%)` and the `39%-45%` sensitivity bound. The bound stays numeric because that is where an over-claim would cost most.
3. **§6 is reordered** so the concentration lesson leads, putting Figure 1 on the section's first page.

**Files touched by the rewrite: `main.tex` only.** `appendix_tables.tex` carries no tier labels and
no prose needing a gloss. The five style files (`iclr2027_conference.sty`, `.bst`, `fancyhdr.sty`,
`natbib.sty`, `math_commands.tex`) are byte-identical copies of V4's and are never edited.

**Four rules, everywhere:**

1. **Intuition, then the number.** One or two plain sentences a human can picture, *then* the measurement as evidence. Never a Cohen's *d*, a threshold, or a σ̂ before the reader knows what was measured and why it matters.
2. **This is our method.** The authors designed, built, and tested this loop. It composes standard ingredients (active learning, mean-teacher disagreement, clustering) — say so — but the closed loop is theirs. The reader must always know: what is prior work, what we built, what we measured, what we found.
3. **Pre-registration is normal practice, stated once.** Once in §4 setup, then only where a verdict's credibility actually depends on it (three places, listed in Part 3). No announcing of rigor.
4. **No tier labels in the reader's path.** The plain distinction — "some of this is specific to our setup, some travels" — carried in prose. One table keeps the split explicit, in plain words.

---

## Part 1 — Section-by-section rewrite specification

### Abstract — 242 → **235 words**

**What it does wrong.** Opens on a riddle ("A control that returns zero is informative only if it
could have returned something else") before the reader knows the paper's subject. Carries **12
numeric tokens**, including `+0.0073` of a Cohen's *d* three sentences before the shuffle experiment
is described. Never says what camouflaged object detection is, never says the method is ours.

**New structure** — five beats, in order:

1. The problem, plainly: COD needs labelled data; masks are slow to trace because the object is hard to see; synthetic generation is a partial remedy.
2. The question that creates: if you can generate images, where do you aim them?
3. **Our** idea and what happened: we built a loop that aims by the model's own uncertainty; it does not beat random. One scope sentence with the `39%–45%` bound.
4. The more useful finding: the apparent benefit is concentration, not targeting — any rule that concentrates reproduces it. Plain, no *d* values.
5. The independent second finding: `41 of 76 (53.9%)` of CHAMELEON is re-encoded training data; exact hashing reports zero. Then, and only then, the riddle as one closing line.

**Numbers:** exactly two load-bearing result figures (`41/76 = 53.9%`; `39%–45%`), plus `36` as design
scale. Ten numeric tokens leave the abstract; **all ten already appear in the body** (verified — see
Part 5).

**Draft (≈235 words), for voice approval:**

> Camouflaged object detection asks a model to outline objects that blend into their background.
> Labelled data is expensive — an annotator has to trace a boundary that is hard to see at all — so
> generating synthetic camouflaged images is a common partial remedy. That raises a question: if you
> can generate images, where should you aim them?
>
> We built and tested an answer. Cluster the unlabelled real images the model will face, find the
> clusters where it is least sure of itself, generate new images aimed there, retrain, repeat. The
> ingredients are standard — active learning, mean-teacher disagreement, clustering on
> self-supervised features — and the composition is ours.
>
> It does not help. Across 36 controlled training runs, aiming the budget by uncertainty does not
> beat spending it at random. Our design could detect an effect the size of the one reported for
> this approach, but not one several times smaller: it resolves 39%–45% of that improvement.
>
> The more useful finding is why the idea looks like it works. Targeted selection does pick a
> visibly different training set from a random one — but so does any rule that concentrates the
> budget on a few clusters, including one that keeps our allocation's shape while destroying the
> uncertainty signal. The separation comes from concentration, not targeting; the control that
> discriminates is a same-shape shuffle, not random selection.
>
> Independently of any of that: 41 of CHAMELEON's 76 images (53.9%) are re-encoded copies of COD10K
> and CAMO training images. Exact file hashing — the standard check — reports zero overlap, because
> the copies were re-saved in a different format. We claim non-independence rather than score
> inflation, and release a detector and a clean protocol. A control that returns zero is informative
> only if it could have returned something else.

---

### §1 Introduction — 704 → **660 words**

**What it does wrong.** Assumes the domain. Asserts "if the budget is finite" with no setup. Credits
the method to the field: *"The answer the field's methods propose is appealing"*. Leads its second
paragraph with the riddle. Carries the tier taxonomy (`Tier 3 / Tier 2 / Tier 1` preamble + 5 bullet
tags). Ends on a 32-word pre-registration paragraph duplicating §4.

**New structure:**

| ¶ | Content | Words |
|---|---|---|
| 1 | **Onboarding.** What COD is (outline an object that matches its background); why labels are scarce (tracing an invisible boundary is slow); why people generate synthetic camouflage; the question that follows — where do you aim a finite generation budget? | ~120 |
| 2 | **Our idea, as ours, intuitively before mechanism.** "We built a loop that aims the budget by the model's own uncertainty… Every ingredient is standard; the composition is ours." Then one sentence of mechanism. | ~90 |
| 3 | **We tested it; it doesn't work.** Verdict plainly, then the scope limit in the same breath (`126%` / tighter bar / `0.91×` / *no effect resolvable at this sensitivity, never a demonstration of absence*). | ~130 |
| 4 | **Why, and the second finding.** The concentration explanation in one plain sentence; the contamination finding in two. One plain sentence introducing specific-vs-general. Riddle stated once, plainly, *here* — after the reader knows the subject. | ~110 |
| 5 | **Contributions**, rewritten to stand alone. | ~210 |

**Intuition to add:** the whole of ¶1 (~120 words) — currently absent.

**Contributions bullets.** Each must be comprehensible without the body. Drop all five `[Tier n]`
tags; drop the tier-taxonomy preamble; replace with one plain sentence: *"Two of these travel beyond
our setup; two are properties of the particular loop we built, and we mark which is which."* The
`1082` / `1715` axis parenthetical is inward-facing bookkeeping — it relocates to §7 (Part 5), and
the bullet keeps *"calibrated by a negative control that found none."*

**Delete:** the closing paragraph *"Decision rules were committed before the runs they govern… two
that passed are reported and then refused."* Its content moves intact into §4's single
pre-registration statement.

---

### §2 Related Work — 417 → **375 words**

**What it does wrong.** Structurally fine. Two failures of ownership and one of jargon: *"The idea
under test is reasonable, and prior work is why"* frames our composition as communal; *"That pairing
is what we test"* is vague about who built what. "Dense prediction" and "core-set selection" are
unglossed.

**New structure.** Same four paragraphs, same order. Changes:

- Paragraph 3 opens: *"The ingredients we compose are all standard, which is why the idea was worth testing."* Then the prior work. Close with: *"What is new here is the composition and the control we test it against, not any component."*
- Paragraph 2 closes by naming precisely what is prior and what is ours: the generator and the self-training loop are prior work; the uncertainty-guided allocation on top of them is ours.
- Paragraph 4 already sits right ("our contribution is that exact hashing certifies a contaminated set as clean") — tighten only.
- Gloss "dense prediction" (*tasks that label every pixel*) on first use.

**Hard constraint: all 36 `[CITE: …]` placeholders survive, verbatim and in place.** Count in = count out.

---

### §3 The Approach Under Test → **"The Loop We Built"** — 583 → **585 words**

**What it does wrong.** Opens with a methodological credo (*"A negative result is only as informative
as the specification of what was tested…"*) instead of the idea. Goes straight to `k=75` clusters and
Equation 1 with no picture of the loop first. Calls it *"The idea under test"* — again, ownership.
Introduces ES as a formula before saying what it measures.

**New structure:**

1. **§3 preamble — the whole loop as one picture, ~90 new words, before anything formal.** Train a model on the labelled images. Look at the unlabelled real images the model will actually face, and find where it is least confident. Generate more synthetic training images aimed at exactly those places. Retrain. Repeat. Then, explicitly: *"This is our instantiation of that idea. The rest of this section specifies it exactly, because a null result is only as informative as the thing it tested."* (The credo survives as a subordinate clause, not an opening.)
2. **§3.1 Setting and loop** — unchanged content. Gloss on first use: *source pool* (the labelled images we train on), *target pool* (the unlabelled real images we want the model to work on), *endpoint* (the test set a verdict is read from). Keep the two non-obvious properties (fixed round count, generator never invoked from training) — they are load-bearing for §6.4.
3. **§3.2 Uncertainty-guided allocation** — each of the four stages gets one plain sentence before its formalism. **Equation 1 is introduced in words first:** *"We need a number, computable without labels, saying how unsure the model is about an image. We use how much the student and its own slow-moving average disagree — the same quantity the training loss already tries to reduce, which is why it is available on unlabelled data."* Equation and all constants (`a=0.9`, `b=0.3`, `k=75`, `α=1.0`, `B=1000`) unchanged.
4. **§3.3 Conditions** — gloss *arm* (a training condition) once. *"What is held constant is verified rather than assumed"* → *"We verified what was held constant:"* Keep every verification number.

---

### §4 Setup → **"Setup, and the Rules We Fixed in Advance"** — 423 → **385 words**

**What it does wrong.** The 39-word opening is the paper's biggest pre-registration flex. The
provenance paragraph ends on *"We do not present that as minor: the author of the rule also authored
its flaw"* — self-flagellation performing as rigor. Contains ~8 of the 36 pre-registration mentions.

**New structure.** Same four paragraphs, same decision rule verbatim (the tabbing block is unchanged).

- **Opening compressed to one sentence, and this is the paper's single general statement of pre-registration:** *"Every decision rule below was committed at a named commit before the runs it governs; amendments are append-only and dated; thresholds that failed are reported failed, and two that passed are reported and then refused."* Everything else about pre-registration in the paper is deleted or reduced to the three load-bearing mentions in Part 3.
- **Decision rule paragraph:** keep the rule, keep *"nothing converts them into significance claims"* (a scope limit). Delete *"a design choice, not an omission"* — the fact stands without the defence.
- **Falsification-arms paragraph:** keep in full including *"Because equality is the supporting outcome here, set distinctness was gated before any GPU time"* — this is mention #2 of the three, and the verdict's credibility genuinely rests on it.
- **Provenance paragraph:** compress from 63 to ~28 words. Keep the disclosure (*one frozen clause that no correct computation could satisfy*) and the pointer to `app:method`, which already carries the full account of all three amendments. Delete the closing self-criticism.
- Gloss *within noise* on first use: *the gap is smaller than the seed-to-seed wobble.* Gloss *cell*: *one architecture × endpoint combination.*

---

### §5 The Null Result — 734 → **690 words**

**What it does wrong.** This is where the paper is decided, and the verdict arrives buried. The
result sentence is followed immediately by three paragraphs of caveat before the reader has absorbed
it. The positive control — the thing that makes the null worth reading — arrives fourth, and opens
on an epistemology sentence rather than on what it is. Two `rather than leave it to be found/computed`
mannerisms. The closing 92-word anchoring paragraph is **entirely duplicated** by `app:anchor` (158
words), which says the same thing plus a mechanism.

**New structure — the verdict, then one caveat, then the control, then the rest:**

| ¶ | Content | Note |
|---|---|---|
| 1 | **The result, plainly, first.** *"Targeting did not beat random."* Table 1 immediately. Both architectures, both endpoints, `within noise`. | unchanged numbers |
| 2 | **The one caveat that matters, intuitively then numerically.** "The honest limit is that this campaign was coarse: its bar was *wider* than the effect it was built to detect." Then the numbers: `2σ̂ = 0.0179` vs reproduction gap `0.0142`, **`126%`**, and the bolded sentence retained verbatim: *"at 126% of the effect it was built to detect, this campaign could not have detected the reference effect had it been present."* Then the tighter imported bar (`3.24×`, `0.0028` vs `0.0090`), `0.91×`, `39%`/`45%`. | Keep the anti-conservative disclosure; **delete only the phrase** *"We state the asymmetry rather than leave it to be found"* |
| 3 | **The positive control, intuition first.** Open: *"A null is only worth reading if the same measurement can detect something real, so we checked that it can."* Then: mean-teacher arm, `0.6988` vs `0.7185`, `Δ = +0.0197` against a bar of `0.0060` — **`3.3×` the bar** (see Part 5) — `3/3`, `detected`. Then, unchanged: *"This is a control on instrument sensitivity, not an ablation"*, and *"the control's own bar, 0.0060, exceeds the decisive gap 0.0050, so an effect that size would not have cleared this pooling either."* | This paragraph moves **up**, from 4th to 3rd |
| 4 | **Both largest effects sit at 91% of threshold.** Content unchanged, tightened ~20 words. Delete *"We make this point rather than leave it to be computed."* | |
| 5 | **The monotone aggregate pattern that points away from our conclusion.** Keep. *"our own standard forbids suppressing a pattern for failing a threshold, and this one does not flatter us"* → *"We report it because it does not favour our conclusion."* | |
| 6 | **Anchoring, compressed 92 → ~40 words.** Keep `0.7136` (published) and `0.7185` (ours) and the reproduction gate in the main text; the A0 seed-spread figures (`0.0334`, `0.0211`, `0.7010`) point to `app:anchor`, where all three already appear verbatim. | Relocation, not deletion — Part 5 |

**Intuition to add:** ~60 words total — the "coarse bar" picture in ¶2 and the "we checked our
measurement can detect a real effect, and it did" opener in ¶3.

---

### §6 → **"What Generalizes"** — 1,500 → **1,430 words**

**What it does wrong.** This is the section the rewrite exists for, and it is a wall of tier-labelled
subsections. Four `[Tier n]` tags in prose plus a 35-word taxonomy preamble. §6.2 — the paper's most
transferable result — opens *"Our most transferable result, and the first instance of this paper's
thesis"* and then delivers the finding as a semicolon-chained list of Cohen's *d* values
(`1.00–1.23`, `+0.9139`, `+1.1403`, `+0.0073`, `13/20`, `−0.0649`, `4/20`, `0.634`, `0.53–0.64`) with
no picture of what the shuffle experiment *is*. Figure 1 is referenced but does not carry the story.

**Reordered** (user decision), so the transferable lessons lead and the strongest one is first:

```
6.1  Concentrating the data mimics targeting          [was 6.2]   [Figure 1 here]
6.2  There were no clusters to aim at                 [was 6.1]
6.3  Uncertainty tracks pixel error, not shape        [unchanged]
6.4  Reasons specific to our setup                    [was 6.4]
```

**Section preamble** (98 → ~80 words). Keep the three-gaps framing. Replace the tier taxonomy with:
*"Some of what follows is a quirk of our exact setup; some of it travels. We say which for each, and
Table~\ref{tab:causes} in Appendix~\ref{app:causes} assigns every cause."* Delete `\textbf{[Tier 2]}` ×3 and `\textbf{[Tier 1]}` ×1.

**§6.1 — the lesson the section exists for. Told as a story, with the figure carrying it.**

Opening, ~90 new words, before any number: *"Suppose you aim your generation budget at the clusters
where the model is least confident. The resulting training set really does look different from a
randomly chosen one of the same size — a probe trained to tell them apart succeeds easily. It is
tempting to read that as evidence the targeting worked. It is not. We repeated the selection with the
uncertainty scores shuffled between clusters, so the budget was spread just as unevenly but aimed at
the wrong places. The two sets separate from random by the same amount. We also aimed at an
arbitrary cluster: same again. Only when we removed the unevenness itself did the separation
collapse."*

Then, and only then, the numbers — all preserved: `1.00–1.23`, the previously claimed `0.10`,
`+0.9139` to `+1.1403`, `+0.0073` / `13/20` / `P≈0.13`, `−0.0649` / `4/20` / `P≈0.006`, effective-rank
ratio `0.634` and `0.53–0.64` over `20/20`. Keep *"the strongest directional evidence here points
against targeting."* Gloss *held-out Cohen's d* once (*how far apart two sets are, in standard
deviations, measured by a probe scored on data it did not see*).

Keep the trained half (`CSHUF`/`CINV`, `12/12 within noise`, largest gap `0.0050` at `1.82σ̂`, the
directional pattern reported-not-claimed) and the **whole** scope paragraph including the bolded
*"So the 12/12 trained result is weakly informative, and the geometric result carries this claim"*
and the attenuation chain (`18.4%`, `≈48%`, `8.8%`, `0.0055`). Close on the transfer sentence,
unchanged: *"the control that matters is not random selection but a same-shape allocation with the
signal destroyed."*

**Figure 1 caption** rewritten to carry the story: name the five bars in plain words and state the
punchline in the first line rather than the third. Same source line, same panels.

**§6.2 (was 6.1) — no clusters to aim at.** Opening intuition, ~35 words: *"Allocating cluster by
cluster presumes the data falls into clusters. We checked whether it does, in three different
embedding spaces, and it barely does."* Gloss *silhouette* (*a standard score for how cleanly points
fall into groups; near zero means there are no real groups*). Keep `0.1600`, `0.1465`, `0.0568`,
`0.0357`, `k=5`/`k=150`, `5.4%`, `0.9225`. *"Our pre-declared guard required an interior maximum and
failed; we record that rather than relax it"* → *"Our guard required an interior maximum, and it
failed."* Close with the plain transfer sentence.

**§6.3 — pixel error vs structural error.** Opening intuition, ~40 words: *"An uncertainty score is
useful only if it points at the errors you care about. In camouflage, what you care about is the
shape of the boundary. We found these signals track average per-pixel error better than they track
boundary quality."* Then the ordering, `six independent tests`, the `+0.0708`–`+0.3330` span, the
`0.06` floor. Keep the boundary-band failure (`2 of 8`, four negative, *outside our pre-registered
interpretation space*) — delete only *"We report it as it fell."* Keep the area control in full,
lead retained: **partialling object area *raises* ρ(1−S_α) in all eight rows** (`+0.3433`–`+0.4988`),
`7/8` and `6/8` against a `6/8` floor, the `P≈0.145` near-chance admission, the `0.0012` tie, the
`+0.7070`→`+0.4457` fall. Gloss *partialling out* (*recomputing the correlation with object size held
constant*). Keep both scope sentences.

**§6.4 — reasons specific to our setup.** Retitle from *"Why this instantiation could not have shown
a gain"*. Open plainly: *"The reasons above would apply to anyone. Three more are ours alone —
properties of the particular loop and generator we used. None of them says closed-loop generation
cannot work; they say this build of it could not have shown that it does."* Keep all three causes and
every number (`253`/`127`, bijection onto `4447`, `8885` = `4443+4442`, `1%`, `−23.6%` to `−82.9%`),
the withdrawn candidate cause, and the appendix pointer. *"Each carries a dismissal we state rather
than await"* → *"Each has an obvious rebuttal, and each rebuttal is right:"*

---

### §7 Benchmark Contamination — 897 → **865 words**

**What it does wrong.** The most self-contained section in the paper, and it opens on *"The thesis
again, in its cleanest form:"* — meaningful only to someone who has read §1 closely. The finding
itself is the third clause of the second paragraph.

**New structure:**

1. **Open on the finding, in plain words, no preamble:** *"CHAMELEON is one of the four benchmarks camouflage papers report on. More than half of it — 41 of its 76 images — is training data. The standard way of checking for this is to hash the files and look for identical bytes; that check reports zero overlap here, and it is not wrong, it is just answering a different question. The copies were re-saved in a different format, so not one byte matches, and every pixel does."* Then: *"Nothing in this section depends on whether the method in Section 3 worked."*
2. **The evidence.** Keep unchanged: `40` in COD10K-train + `1` in CAMO, author-sourced verification `76/76`, and our own first-attempt failure at `10/76` (`13.2%`) — that self-correction stays, it is evidence about the difficulty of the check, not a flex. Keep the chronology inference and *"only pool membership is measured."*
3. **The count is a property of the data.** Unchanged: tolerance sweep `11, 26, 37, 40, 41`; nearest-neighbour gap `41` below `5.51`, next `40.58`, `7.36×`; shortlist depths `8`, `32`, all.
4. **Table 2 + Figure 2.** Both unchanged and central. Figure 2's caption already states the selection rule was applied not curated — keep it.
5. **Negative control.** Unchanged, plus the relocated `1082` and `1715` axis clarification from §1 (Part 5). Keep *"An audit that finds contamination wherever it looks is worthless"* — that is plain and earns its place.
6. **Non-independence, not inflation — stated in plain terms.** *"We expected to be able to say how much a contaminated benchmark flatters a score. We measured it and found nothing: the leaked images are not systematically easier."* Then `0.448`–`0.559`, the sign flip, the `[0.25, 0.75]` pre-declared reading (mention #3 of three — the credibility of *not* making the inflation claim rests on it). Keep the bolded conclusion verbatim: *"CHAMELEON is not an independent endpoint for COD10K-trained models."*
7. **The protocol.** Unchanged: withdraw the 35-image recommendation, `41` contaminated + `25` unchecked-not-clean = **`10` verifiably clean**, retire rather than subset, report COD10K-test and NC4K disclosing the unchecked share. *"stated as a change to a released artifact, not a silent tightening"* → *"we are changing a recommendation we already released."* Keep the `[TODO: author finalize]`.
8. **The concrete instance.** Unchanged, including both verbatim quotes, the `40 of 76` target-pool figure, and *"We attribute no intent."*

---

### §8 Conclusion — 63 → **135 words**

**What it does wrong.** Too compressed to land anything. It is a numbers sentence plus the riddle, and
a reader who skips to it learns nothing they can carry.

**New structure — four plain beats, no new numbers:**

> We asked where a synthetic-data budget should be aimed, built a loop that aims it by the model's
> own uncertainty, and found no gain we could resolve — at a sensitivity of 39%–45% of the
> improvement reported for this approach, with a positive control confirming the measurement detects
> a real effect of +0.0197, though not one the size of the null. The idea was reasonable and we still
> think so. What would have to change for it to have a chance: an optimisation budget that grows with
> the pool instead of staying pinned, a foreground supply not already exhausted by the base set, and a
> generator whose output is wider than its own input rather than narrower. Separately, and for anyone
> working in this area rather than for this method: CHAMELEON is not an independent test set for
> models trained on COD10K, the usual check will not tell you so, and we release one that will. A
> control that returns zero is only as good as its ability to return something else.

Every number here (`39%`, `45%`, `+0.0197`) already appears in V4's conclusion or §5. The three
"what would have to change" items restate §6.4's three causes as conditions. The scope limit *none of
this licenses the conclusion that closed-loop generation cannot work* is carried by §6.4 and is not
weakened here.

---

## Part 2 — What the reader is never asked to already know

Every one of these is currently assumed. Each gets its plain-language introduction at the location shown.

| Concept | Where introduced |
|---|---|
| What camouflaged object detection is | §1 ¶1 |
| Why its labels are expensive | §1 ¶1 |
| Why anyone generates synthetic camouflage | §1 ¶1 |
| The loop, as a picture | §3 preamble |
| What the ES score measures | §3.2, before Eq. 1 |
| What "the bar" / σ̂ / *within noise* mean | §4, before the rule |
| What the positive control is for | §5 ¶3, before its numbers |
| What the shuffle experiment is | §6.1, before any *d* |
| Why exact hashing misses re-encoded copies | §7 ¶1 |

---

## Part 3 — Phrases to delete, with counts

### 3a. Pre-registration: **36 → 4 occurrences in main text**

| Family | Count in V4 main text | Kept in V5 |
|---|---|---|
| `pre-registered` / `pre-registration` / `pre-declared` | 19 | 3 |
| `frozen rule/clause` / `fixed before` / `fixed in advance` / `committed before` / `before the first run` / `before any result` / `before any GPU time` / `before it was run` / `before measurement` / `before the draw` | 17 | 1 |
| **Total** | **36** | **4** |

**The four that stay, and why each is load-bearing:**

1. **§4 opening** — the paper's one general statement: rules committed at named commits before the runs, amendments append-only, failed thresholds reported failed, two passing thresholds refused.
2. **§4 falsification arms** — *"Because equality is the supporting outcome here, set distinctness was gated before any GPU time at a Jaccard bound of 0.50."* The `12/12` equality verdict is only credible because the distinctness gate preceded it.
3. **§6.3 area control** — that the `6/8` floor was declared before the run is the only thing separating it from a post-hoc floor, and the paper concedes the floor is near-chance.
4. **§7 inflation** — that `[0.25, 0.75]` was the pre-declared reading is why "we measured for inflation and did not claim it" is a finding rather than a failure to look.

Every other instance is deleted or absorbed. Note the *facts* are never deleted: the decision rule,
the commits, the amendments, and the two refused thresholds all remain (in §4 and `app:method`).

### 3b. Self-congratulatory mannerisms: **8 → 0**

| # | Phrase | Location | Action |
|---|---|---|---|
| 1 | "We quantify rather than assert the limits" | Abstract | delete; abstract is rebuilt |
| 2 | "we state which of its properties are pre-registered … and which we measured rather than assumed" | §3 opening | delete; §3 opens on the loop |
| 3 | "What is held constant is verified rather than assumed" | §3.3 | → "We verified what was held constant" |
| 4 | "a design choice, not an omission" | §4 | delete; the fact stands alone |
| 5 | "We do not present that as minor: the author of the rule also authored its flaw" | §4 | delete; `app:method` keeps the full amendment record |
| 6 | "We state the asymmetry rather than leave it to be found" | §5 | delete phrase; **keep the asymmetry** |
| 7 | "We make this point rather than leave it to be computed" | §5 | delete phrase; **keep the point** |
| 8 | "we record that rather than relax it" / "We report it as it fell" / "Each carries a dismissal we state rather than await" | §6.1, §6.3, §6.4 | replace with plain statements of the same facts |

Plus, in the reproducibility statement (outside the 9-page count): *"Two limits on reproducibility
are worth stating rather than discovering"* → *"Two limits on reproducibility:"*

**Note:** `rather than` appears 12 times in the main text. Six are *load-bearing content* and must
stay: "non-independence rather than inflation" (×2), "re-encoding rather than a byte-identical copy",
"re-scored rather than re-trained", "by source reading rather than measurement", "narrowing, not
displacement". Only the mannerism instances are removed.

### 3c. Tier scaffolding: **15 → 0 in prose, 1 table column in plain words**

| Instance | Count | Action |
|---|---|---|
| §6 title "A Tiered Dissection" | 1 | → "What Generalizes" |
| §1 contributions taxonomy preamble | 1 | → one plain sentence |
| `[Tier n]` bullet tags in §1 | 5 | delete |
| `\textbf{[Tier n]}` in §6 prose | 4 | delete |
| §6 preamble tier definition | 1 | → plain sentence |
| §6.4 "[Tier 1]" + `app:tier1` heading/label | 2 | prose de-tiered; `\label{app:tier1}` **kept** (referenced) |
| `app:causes` table caption + column | 1 | column header `Tier` → **`Scope`**, values `2`→`generalizes`, `1`→`specific to this setup`, `1→2`→`specific, but the scoping sentence travels` |

The appendix heading `\section{Tier 1 causes in full}` → **"Causes specific to our setup, in full"**;
its opening `[Tier 1]` tag deleted. All `\ref{}` targets are unchanged, so no reference breaks.

### 3d. The riddle: **9 → 4, all plain**

Kept at: abstract (closing line), §1 ¶4, §6.1 transfer sentence (already plain), §8 (closing line).
Deleted at: §1 paragraph heading "The thesis: the default control certifies the comforting answer",
§6.1 "the first instance of this paper's thesis", §7 opener "The thesis again, in its cleanest form",
and two mid-sentence restatements.

---

## Part 4 — Jargon → plain language

Gloss on first use, then the term may be used freely.

| V4 term | First use | Plain-language introduction |
|---|---|---|
| label-scarce | §1 | "labelled examples are scarce, because tracing the boundary of something you can barely see is slow" |
| appearance statistics match its surroundings | §1, §2 | "looks like its background — same colours, same textures" |
| source pool | §3.1 | "the labelled images we train on" |
| target pool / target distribution | §3.1 | "the unlabelled real images we want the model to work on" |
| endpoint | §3.1 | "the test set a verdict is read from" |
| arm | §3.3 | "a training condition" |
| cell | §4 | "one architecture × endpoint combination" |
| within noise | §4 | "the gap is smaller than the seed-to-seed wobble" |
| sign consistent 3/3 | §4 | "all three seeds moved the same way" |
| pooled within-arm standard deviation | §4 | "the seed-to-seed noise, pooled across conditions" |
| EMA teacher / mean teacher | §3.1 | "a slowly-updated copy of the model, used as a second opinion" |
| pseudo-label | §3.1 | "the teacher's own guess, used as if it were a label" |
| concentration / the allocation's shape | §6.1 | "how unevenly the budget is spread — a few clusters getting most of it, versus everyone getting a little" |
| held-out Cohen's *d* | §6.1 | "how far apart two sets are in standard deviations, measured by a probe scored on data it did not see" |
| effective rank | §6.1 | "how much of the space a set spreads over" |
| silhouette | §6.2 | "a standard score for how cleanly points fall into groups; near zero means there are no real groups" |
| partialling area out | §6.3 | "recomputing the correlation with object size held constant" |
| resolution floor | §6.3 | "the smallest difference the measurement can tell apart" |
| recall against the target manifold | §6.4 | "how much of the real image variety a synthetic set covers" |
| bijection onto the base set | §6.4 | "exactly one render per source object, and nothing else" |
| instantiation | §6.4 | "our particular build of the idea" |
| dense prediction | §2 | "tasks that label every pixel" |
| exact hashing | §7 | "checking whether two files are byte-for-byte identical" |
| re-encode-tolerant matching | §7 | "comparing pixels rather than file bytes, so a re-saved copy still matches" |
| non-independence, not inflation | §7 | "the test set is not independent of training data; we do not claim scores are inflated, because we measured for that and found nothing" |

---

## Part 5 — Relocations: numbers that move, and where they land

Three, and only three. Each is verified to exist at its destination.

| # | Number(s) | From | To | Status |
|---|---|---|---|---|
| 1 | `1082`, `1715` and the "two axes must not be collapsed" clarification | §1 contributions bullet | §7 negative-control paragraph | New home; **`1082` and `1715` appear nowhere else in the manuscript** — they must be written into §7, not dropped |
| 2 | `3.3×` (the positive control's ratio to its bar) | Abstract + §1 only | §5 ¶3, beside `+0.0197` and `0.0060` | Currently orphaned from the section that owns it; abstract sheds it, so §5 must gain it |
| 3 | A0 seed-spread: `0.7010`, `0.0334`, `0.0211` | §5 ¶6 | pointer to `app:anchor` | **Already present verbatim** in `app:anchor` (158 words containing all of §5's 92) — genuine duplication, safe to compress |

Ten numeric tokens leave the abstract (`+0.0073`, `24`, `12`, `12/12`, `0`, `six`, `+0.0197`, `3.3`,
`0.10`, `41`-as-standalone). Verified: **all ten appear in the body.**

---

## Part 6 — No factual change: guarantee and verification protocol

**Guarantee.** No number, verdict, threshold, scope limit, citation, or claim changes. This is a pure
exposition rewrite. Anything that would alter a claim's meaning is flagged (Part 7a), not done.

**Automated checks, run against V4 vs V5 before the rewrite is declared done:**

1. **Numeric multiset diff.** V4 main text contains **147 distinct numeric tokens over 398
   occurrences**. Extract the same multiset from V5. Every token missing from the V5 main text must
   appear on the Part 5 relocation whitelist (3 entries) or the abstract-shedding list (10 entries,
   all verified present in the body). **Zero unexplained losses. Zero new tokens.**
2. **Citation placeholders.** `grep -c '\[CITE:'` = **36** in, **36** out; the 36 strings identical as a sorted set.
3. **TODO markers.** `grep -c 'TODO'` = **4** in, **4** out. These are author-finalize markers and stay.
4. **Verbatim-claim checklist.** ~20 sentences must survive semantically intact; the highest-risk ones are quoted in Part 7a.
5. **Cross-references.** Every `\label` and `\ref` resolves; `pdflatex` run twice with **0 undefined references**.
6. **Page limit.** Main text ends on **page ≤ 9**, measured with a section-boundary label, not by eye.
7. **Style files.** All five md5s unchanged (listed in the execution steps). `\iclrfinalcopy` still commented out.
8. **Banned-phrase scan.** Parts 3a–3d re-run against V5: pre-registration family ≤ 4, mannerisms = 0, tier labels in prose = 0, riddle ≤ 4.

---

## Part 7 — Required closing statements

### (a) Where readability risks softening a claim, and how this plan avoids it

| # | Risk | How the plan avoids it |
|---|---|---|
| 1 | **Abstract sheds 10 numbers → the null reads vaguer.** | The sensitivity bound stays numeric (`39%–45%`), which is where an over-claim would be most costly. The abstract must contain the words *"does not beat"*, not *"showed no clear benefit"*; and *"not one several times smaller"*, not *"may not detect small effects"*. Check 1 verifies all 10 shed numbers survive in the body. |
| 2 | **Deleting "we state X rather than leave it to be found" deletes the disclosure with the mannerism.** | Every deletion in Part 3b is specified at *clause* level with the retained fact named. §5 ¶2 keeps in full: *"where equality is the supporting outcome a tighter bar is conservative, but here the claim and the null coincide, so the looser bar is anti-conservative."* |
| 3 | **§5 result-first ordering buries the `126%` admission.** | The admission moves to ¶2 — second, not last, and not to the appendix — and its bolded sentence is retained verbatim: *"at 126% of the effect it was built to detect, this campaign could not have detected the reference effect had it been present."* |
| 4 | **Promoting the positive control to ¶3 makes it read as an ablation or as proof the null is real.** | Both guard sentences retained verbatim: *"This is a control on instrument sensitivity, not an ablation"*, and *"the control's own bar, 0.0060, exceeds the decisive gap Δ(C10−B) = 0.0050, so an effect that size would not have cleared this pooling either."* |
| 5 | **De-tiering §6 blurs what travels and what doesn't.** | Every subsection ends with one plain sentence naming its scope. `app:causes` keeps the split explicit with the *same row assignments and same magnitudes*, under a `Scope` column reading "generalizes" / "specific to this setup". |
| 6 | **Storytelling §6.1 upgrades "negligible in this geometry" to "zero".** | The whole scope paragraph is retained, including the bolded *"So the 12/12 trained result is weakly informative, and the geometric result carries this claim"* and *"Negligible in this geometry is supported; zero and harmful are not."* |
| 7 | **A plainer §7 upgrades non-independence to inflation.** | Mandatory retained sentences: *"Our claim is therefore non-independence, not inflation"* and the whole "we measured for it and found nothing" paragraph (`0.448`–`0.559`, the sign flip, the `[0.25,0.75]` pre-declared reading). "More than half is training data" is the finding; "scores are inflated" must appear nowhere. |
| 8 | **§8 grows by 72 words, inviting new claims.** | Its three "what would have to change" items are restatements of §6.4's three existing causes. No new numbers (checked by Part 6 check 1). The scope limit *nothing here licenses the conclusion that closed-loop generation cannot work* stays in §6.4 and is echoed, not weakened, in §8. |
| 9 | **Compressing §5 ¶6 loses the reproduction anchor.** | `0.7136` and `0.7185` and the reproduction gate stay in the main text; only the A0 seed-spread figures become a pointer, and they already appear verbatim in `app:anchor`. |
| 10 | **§2 compression drops a citation.** | Check 2: 36 in, 36 out, identical strings. |
| 11 | **Glossing "unchecked, not clean" as plain language turns a lower bound into a rate.** | Table 2's caption keeps *"Every rate is a lower bound"* verbatim, and §7 ¶7 keeps *"25 more have no same-dimension candidate and are unchecked, not clean."* |

### (b) Word count, before → after

| Section | V4 | V5 | Δ | Where the words come from / go |
|---|---|---|---|---|
| Abstract | 242 | 235 | −7 | Rebuilt; readability from structure, not compression |
| §1 Introduction | 704 | 660 | −44 | −170 (tier taxonomy, tags, riddle paragraph, duplicated pre-reg paragraph, `1082`/`1715` parenthetical) / +126 onboarding |
| §2 Related Work | 417 | 375 | −42 | Tightening; all 36 `[CITE:]` intact |
| §3 The Loop We Built | 583 | 585 | +2 | −88 (credo opening, "verified rather than assumed") / +90 loop intuition |
| §4 Setup | 423 | 385 | −38 | −58 (opening flex, provenance self-criticism, "not an omission") / +20 glosses |
| §5 The Null Result | 734 | 690 | −44 | −104 (two mannerisms, `app:anchor` duplication, tightening) / +60 intuition |
| §6 What Generalizes | 1,500 | 1,430 | −70 | −180 (tier labels, thesis line, mannerisms, tightening) / +110 plain openers and closers |
| §7 Contamination | 897 | 865 | −32 | −72 (thesis opener, tightening) / +40 plain opening + relocated `1082`/`1715` |
| §8 Conclusion | 63 | 135 | **+72** | The one section that must grow |
| **Total main text** | **5,563** | **5,360** | **−203** | |

At this template's ~620 words per text page, **−203 words ≈ −0.33 page**. V4 ends exactly at the
bottom of page 9 with zero slack; V5 ends inside page 9 with roughly a third of a page in hand. The
two figures, two tables, and one equation are unchanged in size and count, so float pressure is
unchanged. **Main text stays ≤ 9 pages.**

Cut order if it still overruns after a trial compile: §2 Related Work → §3.1/§3.2 mechanics
(detail already in `app:method`) → §6.4 (detail already in `app:tier1`). **Never cut:** either
figure, the contamination claim, the positive-control paragraph, any scope limit, or any of the four
retained pre-registration mentions.

### (c) Confirmation

**This rewrite changes exposition only — structure, ordering, and wording — and changes no content:
every number, verdict, threshold, scope limit, and citation in PAPER_V4 is preserved in PAPER_V5.**

---

# Outcome (recorded after execution)

The rewrite is applied. `main.tex` compiles with 0 errors and 0 undefined references, the
main text ends on **page 9** (page 10 begins with the AI use statement, exactly as V4 did),
and the five style files plus `appendix_tables.tex` are byte-identical to V4.

## Word budget: predicted vs actual

| Section | V4 | plan | actual | vs V4 |
|---|---:|---:|---:|---:|
| Abstract | 242 | 235 | 260 | +18 |
| S1 | 704 | 660 | 710 | +6 |
| S2 | 417 | 375 | 433 | +16 |
| S3 | 583 | 585 | 620 | +37 |
| S4 | 423 | 385 | 413 | -10 |
| S5 | 734 | 690 | 660 | -74 |
| S6 | 1500 | 1430 | 1494 | -6 |
| S7 | 897 | 865 | 925 | +28 |
| S8 | 63 | 135 | 133 | +70 |
| **Total body** | **5563** | **5360** | **5648** | **+85** |
**The plan's −203 prediction was wrong.** Genuine onboarding for a non-specialist cost about 555
words (domain intro, loop picture, shuffle story, positive-control intuition, §7 plain opening, §8),
and the reclaimable flex was ~385, not ~590. The body therefore ends **+85 words** against V4 while
still fitting 9 pages, because the rewritten paragraph structure packs differently.

The gap was closed by moving specification detail into the appendix (+176 words there), not by
dropping content. Seventeen numeric tokens left the body; every one was verified present in the
appendix before the check was allowed to pass:

| Relocated | To |
|---|---|
| `0.7010`, `0.0334`, `0.0211`, `0.7151`, `0.7172`, `0.0107`, `42` | `app:anchor` (already carried all of them) |
| `4443`, `+4442`, `8885`, `-23.6`, `-82.9` | `app:tier1` |
| `+0.3433`, `+0.4988`, `+0.7070`, `+0.4457`, `0.0012` | `app:tables` (new "area control in detail" paragraph) |

## Verification actually run

A checker (`verify.py`) was run after every edit batch and gates the result:

- **every V4 numeric token still present somewhere** in the manuscript — PASS
- **no numeric token invented** — PASS
- **tokens gone from the body are whitelisted relocations**, each asserted present in the appendix — PASS
- **`[CITE:]` 36 → 36**, identical as a sorted set — PASS
- **`[TODO:]` 4 → 4** — PASS
- **pre-registration mentions in the body: 36 → 2** (plus two that the regex does not match but which are the load-bearing ones: the §4 opening statement and §6.3's "a floor of 6/8 declared before the run") — PASS
- **tier labels in body prose: 15 → 0** — PASS
- **self-congratulatory mannerisms: 8 → 0** — PASS
- **11 load-bearing claim sentences retained verbatim** — PASS

The checker caught two regressions I introduced and would otherwise have shipped: reintroducing
"rather than assumed" in §3.3, and dropping `4443/+4442` when compressing §6.4.

## Deviations from the plan, and one thing left undone

1. **§6.3's area-control detail moved to the appendix** — not in the plan. The body keeps the
   intuition, the six tests, the boundary-band failure, the direction-of-shift headline, the
   `7/8`/`6/8` result, the near-chance-floor admission and both scope sentences; the appendix takes
   the per-row figures. This was the cut that made 9 pages reachable without touching §7.
2. **§6.4 cut harder than planned**, to ~130 words. This follows the brief ("then, briefly, the
   setup-specific reasons, plainly scoped") and `app:tier1` carries the full account.
3. **The abstract is 260 words, not 235.** Five beats in plain language would not compress further
   without going back to telegraphic phrasing, which is the disease being treated.
4. **Not done: Figure 1's panel (b) legend still reads "C10 ±2σ̂ (the frozen bar)".** That string is
   baked into `figs/fig1_thesis.pdf` by `figs/make_fig1.py`, which is not the manuscript `.tex`, so
   it was left alone. It reads as a technical label rather than self-congratulation, but if you want
   it changed, `make_fig1.py:` must be edited and the figure regenerated.

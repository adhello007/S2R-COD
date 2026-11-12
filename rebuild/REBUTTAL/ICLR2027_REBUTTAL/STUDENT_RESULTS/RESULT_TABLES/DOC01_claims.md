# DOC-01: claim calibration in the revised manuscript

**Files.**
- Original (never edited): `AD-PCHGS-250926.tex`. Unchanged copy: `revision/AD-PCHGS-original-copy.tex`.
- Revised: `revision/AD-PCHGS-revised.tex`. Full diff: `revision/manuscript.diff`.
- The revised PDF compiles to 27 pages, with no LaTeX errors or undefined references. The main text ends on
  page 10, the discussion-phase limit; the submitted main text ended on page 9.

**Overclaim search.** The instruction's grep (`doesn.t help | does not (outperform|help|beat) | no (score|effect) |
not an artifact | cannot | never | null`) matches 48 non-comment lines in the original. Most are technical uses
that make no claim beyond the evidence ("fitted once and never refitted", "never invoked during training", "the
null hypothesis"). The claims below are the ones that did overreach, plus the factual corrections D1, D2 and D5.

## Revised (outcome-independent, applied)

| # | Where | Original | Revision | Concern |
|---|---|---|---|---|
| 1 | Abstract | "uncertainty-based targeting does not outperform random allocation" | "shows no detectable advantage … 95% interval −0.0020 to +0.0067: an advantage as large as the published method's own gain (+0.0142) is excluded, but smaller ones are not" | CW-01 |
| 2 | Abstract | "Five independent controls further show that this null result is not an artifact" | "Five controls address the main ways the design itself could produce such a null" | CW-01 |
| 3 | Abstract | the training-set difference "is explained by concentrating … and, on boundary accuracy, so does aiming at the clusters the model was most certain about" | the training-set difference comes from concentration; the boundary-accuracy clause is removed (it does not hold at eight seeds); whether concentration changes accuracy goes in the result placeholder | CW-02 |
| 4 | Abstract | final sentence: concentration "accounts for the observed training-set effects" | replaced by an explicit scope sentence: LAKE-RED, fixed offline pool, 4,447 foregrounds, background-only variation, k = 75 frozen-feature clusters, two SINet architectures, two-round self-training, N = 1,000 | CW-04 |
| 5 | Intro ¶3 | "What looked like the effect of targeting was the effect of concentrating" | "…an effect of targeting **on the training set** was an effect of concentrating it", plus a sentence saying the accuracy effect is tested directly | CW-02 |
| 6 | Intro ¶4 | "shows no measurable effect that this design can resolve"; "changes nothing" | "no detectable advantage … excludes an advantage the size of the published method's gain, but not one between about +0.005 and +0.0067"; "produces no detectable change either" | CW-01 |
| 7 | Contribution 2 | "A bounded null … defended by five independent controls" | "no detectable advantage, with the sizes of effect that are and are not excluded stated, and five controls" | CW-01 |
| 8 | Intro, end | — | added a scope sentence pointing to the Discussion | CW-04 |
| 9 | §3.1 ¶1 | "did not beat spending it at random" | "showed no detectable advantage over spending it at random" | CW-01 |
| 10 | §3.1, oracle | "converts *our score did not help* into the stronger *no score of any quality helped here*" | "the absence of a detectable advantage is not specific to our score: a score aimed with the true endpoint error shows none either" | CW-01 |
| 11 | §3.1 | "Perhaps three seeds are too few. It was" (grammar) | "They were, which is why the seed expansion above exists" | — |
| 12 | §3.1, decisive ¶ | a post-hoc interval "excludes the reference effect … while admitting effects a few times smaller" | not-detected vs equivalent defined; the rule's exact sensitivity (one time in five at +0.005; 80% at 0.0087); "equivalence is not established (TOST p = 0.101)"; the new Table `tab:ci_tost` (16 contrasts: Δ, 95% CI, 90% CI, TOST p, label); placeholder for the confirmatory campaign | CW-01, QA-01 |
| 13 | §3.2 heading | "Concentration, Not Targeting" | "Concentration, Not Targeting, Shapes the Training Set" | CW-02 |
| 14 | §3.2 ¶1 | "trained accuracy … is consistent with it, and the one family of metrics … supports it" | three tiers: (1) established, the training-set difference comes from concentration; (2) established, direction makes no detectable difference to accuracy; (3) hypothesis, concentration changes accuracy, tested by the pre-registered dose-response experiment | CW-02, QA-02 |
| 15 | §3.2, TOST | "five of sixteen … four direction contrasts and one targeting-versus-random gap, on NC4K" (ambiguous) | "before any correction … four direction contrasts, and the targeting-versus-random gap on NC4K only … After a Holm correction, none is equivalent" | QA-01 |
| 16 | §3.2, boundary | "on SINet, the concentration effect finally clears its bar … *This is the strongest form of the result we have*" | the 3-seed 1.37×/1.34×, then "At eight seeds that pattern does not hold": 0.30× (+0.0046) and 0.64× (+0.0098), within noise; SINet-v2 resolves none; "do not establish that concentration changes accuracy". The table is replaced by the eight-seed `tab:boundary` (App. C) | CW-02 |
| 17 | §3.2, end | "the pattern survives every binarisation threshold … SINet-v2 resolves none of it" | the dose-response design (three concentration levels, five random directions each, pre-registered, Boundary-IoU on SINet primary); result placeholder; "The planned replication on SINet-v2 was not run, for lack of compute." | CW-02, QA-02 |
| 18 | Discussion | "a null under stated sensitivity … we have named the size at which it would have" | "excludes an advantage the size of the published method's own gain, leaves smaller ones open" | CW-01 |
| 19 | Discussion | — | new **Scope** paragraph: every item of the posted scope list, the foreground-constraint numbers (ICC 0.71; 52 of 75 clusters, with the representation caveat), and "we make no claim about other generators" | CW-04, QA-04 |
| 20 | Conclusion | "did not beat spending it at random" | "showed no detectable advantage … an advantage the size of the published method's own gain is excluded, and smaller ones are not"; result placeholders; scope sentence | CW-01, CW-04 |
| 21 | §2, rule (D1) | "every seed agrees on its sign" | "every seed at three seeds; at least seven of eight in the eight-seed expansion, fixed before that campaign ran"; App. B gives the 7/8 rule's probability | audit |
| 22 | App. G (D2) | pseudo-label means "across the seed expansion" | "over the 40 runs the seed expansion added (seeds 46–50) … over all eight seeds 1991, 2007, 2020, 2015 (range 1782–2278)" | audit |
| 23 | App. B (D5) | "the E-measure E_φ" | "the mean E-measure over thresholds, the variant SINet-V2 and RISE report" | audit |
| 24 | §1.1, App. A | RISE absent | RISE added (verified BibTeX), with what it shares with our pipeline (the SINet-V2 detector and the same 4,040 images) and what the gap therefore isolates | CW-03 |
| 25 | §3.1 → App. C | "That is the plain form …" bar-arithmetic paragraph | moved to App. C ("Why the eight-seed bar is wider"), for the page budget | — |

## Pending (outcome-dependent; filled from the pre-registered decision sentences)

| Macro | Where | Filled when |
|---|---|---|
| `\cdrverdict`, `\cdrshort` | §3.2 end; abstract; conclusion | after the 35 dose-response SINet runs are scored and analysed (projected Fri 13 Nov) |
| `\eqverdict`, `\eqshort` | §3.1 decisive ¶; abstract; conclusion | after all 81 confirmatory runs (17 Nov), or with the INCOMPLETE rule |
| protocol table and gap paragraph (DOC-02) | App. A | after the supervised anchors are scored (projected Fri 13 Nov) |

Each fill re-checks the page limit (main text ≤ 10 pages; currently 25 of 80 lines of page 10 are free).

## Title (author decides; check the ICLR policy on title changes during the discussion period)

- (i) "Concentration Without Direction: A Controlled, Bounded Null for Uncertainty-Guided Allocation of Synthetic
  Data in Camouflaged Object Detection". Use only if the dose-response test supports a downstream concentration
  effect; otherwise "Concentration" in the title could be read as a downstream claim.
- (ii) "Uncertainty-Guided Allocation of Synthetic Training Data Shows No Detectable Benefit for Camouflaged
  Object Detection". Correct whatever the dose-response test returns.

The revised source keeps the submitted title until the author decides.

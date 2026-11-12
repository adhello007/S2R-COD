# DOC-01: proposed manuscript edits (CW-01, CW-02, QA-01, QA-02)

**For:** the corresponding author. These are proposals only. The submitted `AD-PCHGS-250926.tex` is
untouched, and no patched copy has been made. Each edit gives its label, the current text, the
proposed text, the reason, and the evidence file. Numbers marked **post-review** were computed after
the review from the committed runs, with no new training. Everything else is submitted-paper
evidence.

**Page budget.** The submitted main text ends exactly on page 9, and the discussion-phase limit is 10.
The main-text edits below add about 14 lines and remove about 9, a net of +5 lines, which stays
within page 10. Edit 6 lists the cut that makes room if needed.

The CHAMELEON edits for QA-03 are in `DOC-02_CHAMELEON_PROTOCOL_CLARIFICATION.md` §5. The
claim-by-claim map is `RESULT_TABLES/DOC-01_claim_evidence_map.csv`.

---

## Edit 1: Abstract (bounded null; drop the boundary clause)

**Current:**
> …targeted training sets are measurably different from random sets, but the difference is explained
> by concentrating the generation budget rather than by where uncertainty is concentrated, as every
> concentration rule we test reproduces the effect and, on boundary accuracy, so does aiming at the
> clusters the model was most certain about. … Together, these results show that, under a fixed
> synthetic-data budget, budget concentration, not uncertainty-based targeting, accounts for the
> observed training-set effects.

**Proposed:**
> Across 103 training runs, uncertainty-based targeting does not outperform random allocation: on the
> primary endpoint the gain is +0.0024 S-measure, and gains above about 0.007 are excluded, though
> smaller ones are not. Five independent controls show that this null is not an artifact. Targeted
> training sets are measurably different from random sets, but the difference comes from
> concentrating the generation budget rather than from where uncertainty points: every concentration
> rule we test reproduces it. … Together, these results show that, under a fixed synthetic-data budget
> drawn from a fixed pool of re-rendered foregrounds, budget concentration, not uncertainty-based
> targeting, accounts for how the selected training sets differ.

**Why:** CW-01 and QA-01 ask for the bound to be stated. The boundary clause rested on three seeds and
does not hold for targeted-versus-random at eight seeds (Edit 4). The last sentence claimed
"training-set effects" in general, but the evidence is about how the selected sets differ.
**Evidence:** `RESULT_TABLES/TH-01_paired_inference.csv`; `RESULT_TABLES/AN-03_arch_boundary_grid.csv`.

## Edit 2: `sec:null`, the oracle sentence

**Current:** "This converts *our score did not help* into the stronger *no score of any quality helped here*."
**Proposed:** "This converts *our score did not help* into *no score we could supply, including the
true error, helped at this sensitivity*."
**Why:** the brief asks for this overstatement to be corrected. The oracle was tested at three seeds,
with a bar of 0.0061.

## Edit 3: `sec:null`, closing paragraph (interval, pairing, scales)

**Current:**
> …A post-hoc interval on the two arms actually compared is tighter still, placing the gap in
> $[-0.0020, +0.0067]$, which *excludes the reference effect by more than a factor of two* while
> admitting effects a few times smaller. …

**Proposed:**
> …A post-hoc Welch interval on the two arms actually compared places the gap in
> $[-0.0020, +0.0067]$. Pairing the arms by training seed gives $[-0.0023, +0.0070]$ and gains
> nothing: the random arm redraws its images at every seed, so a seed shares the training randomness
> but not the data, and the paired scores are uncorrelated ($r = -0.04$). Both intervals exclude the
> reference improvement of $+0.0142$, which is the gain of the reproduced method over its own
> baseline in this setup, not a field-wide threshold. Neither excludes a gain of $+0.005$, and the
> one-sided 95% bound is $+0.0061$. Equivalence within $\pm 0.005$ is not established
> (paired $p = 0.111$; Welch $p = 0.101$); the smallest margin at which it would be is $0.0061$.
> These intervals decide nothing, because the frozen rule admits none. They say exactly which gains
> the campaign could and could not have seen.

**Why:** CW-01b–e and QA-01a–c. The pre-registered 2σ̂ rule stays as it is. It is a per-run spread
threshold, not an inferential interval, and the edit keeps the two apart.
**Evidence:** `TH-01_paired_inference.csv` (primary row: `paired_ci95_*`, `welch_ci95_*`,
`paired_upper_one_sided_95`, `paired_tost_p_delta0p005`), `TH-01_tost_table_reproduction.csv`.

## Edit 4: `sec:concentration`, boundary paragraph and table (central change for CW-02)

**Current:**
> …Re-scoring every run's committed predictions with two boundary metrics closes that gap
> (Table~\ref{tab:boundary}), and on SINet, the concentration effect finally clears its bar. So does
> the anti-targeted arm, at $1.34\times$ against targeted selection's $1.37\times$ … *This is the
> strongest form of the result we have* …

**Proposed:**
> …Re-scoring the committed predictions with two boundary metrics tests that. At the three committed
> seeds, on SINet, both concentrated arms cleared their bar against random ($1.37\times$ targeted,
> $1.34\times$ reversed). **At all eight seeds the targeted arm does not:** its Boundary-IoU gain
> over random is $+0.0046$, $95\%$ CI $[-0.0066, +0.0158]$, $0.30\times$ its bar. The reversed arm
> keeps a smaller gain, $+0.0098$ $[+0.0039, +0.0157]$, on $7$ of $8$ seeds and at $0.64\times$ its
> bar, and it does so on NC4K and at every binarisation threshold too. But none of the $140$ eight-seed
> contrasts we examined (two boundary metrics and S-measure; both architectures, both endpoints, three
> thresholds) survives a Holm correction (smallest adjusted $p = 0.50$). On SINet-v2 the targeted arm shows
> nothing ($+0.0002$) and the reversed arm about a third as much ($+0.0033$, $[-0.0009, +0.0074]$). Tested directly,
> the architecture difference is not resolved (targeted: $+0.0044$ $[-0.0075, +0.0163]$; reversed:
> $+0.0065$ $[-0.0001, +0.0131]$). Because the targeted and reversed arms share the same
> concentration exactly, concentration alone cannot explain a gain that only one of them shows. We
> therefore report no resolved downstream benefit of concentration, only an unexplained,
> exploratory advantage of the reversed arm on one architecture.

Replace `tab:boundary` with the eight-seed version (both endpoints; contrasts C10−B, CINV−B, C10−CINV,
C10−CSHUF; paired CI; ×bar), and move the three-seed rows to `app:diag`.
Also revise the section's opening sentence. Delete "and the one family of metrics on which
concentration is large enough to resolve supports it, post hoc and on one architecture". Replace it
with: "trained accuracy at eight seeds shows no ordering by direction, and no resolved benefit of
concentration itself".
**Why:** CW-02a–c. The submitted claim was a three-seed result. Its eight-seed re-score, which is
also post-hoc, does not support it for the decisive targeted-versus-random contrast. Interaction is
tested directly, as the reviewer asked.
**Evidence:** `AN-03_arch_boundary_grid.csv` (8-seed and 3-seed rows), `AN-03_interaction.csv`,
`EXP-02_gate3_reproduction.csv` (three-seed values reproduced to 1e-16),
`FIGURES/AN-03_architecture_contrasts.png`.

## Edit 5: `sec:concentration`, equivalence paragraph

Add after "These tests are post-hoc and decide nothing.": "Paired by training seed instead of Welch,
six of the sixteen gaps are equivalent within $\pm 0.005$, and the primary targeting-versus-random gap
is still not ($p = 0.111$)."
**Evidence:** `TH-01_paired_inference.csv` (`paired_equivalent_delta0p005`).

## Edit 6: `app:diag`, "How much the trained comparison is attenuated" (correct 48% / 8.8%)

**Current:** "…only about $48\%$ of injected images differ between any two arms, giving an effective
contrast near $8.8\%$."
**Proposed:** "…the three concentrated arms share about half of their injected images: between $45\%$
and $51\%$ differ, or $8.3$–$9.4\%$ of the training pool. Targeted and random selection share far
less, $209$–$246$ of $1000$ per seed, close to the $225$ expected by chance. So $77\%$ of injected
images, $14.1\%$ of the pool, differ in the decisive comparison. Under the pinned schedule an epoch
draws $4048$ of the $5447$ source images ($0.74$ visits per image), so targeted-only images make up
about $14\%$ of source draws in round one and $10\%$ in round two. These are expected values; the
sampler order was not logged. Between rounds, each arm also appends its own pseudo-labelled target
images, and the targeted and random sets of these overlap only at Jaccard $0.58$–$0.68$. That second
difference follows from the first round and is reported, not adjusted away."
**Why:** the reviewer quoted our 8.8% (CW-01a, QA-02a). That number describes the concentrated-arm
comparisons, not the decisive one.
**Evidence:** `AN-02_overlap_by_seed.csv`, `AN-02_exposure_by_run.csv`, `AN-02_pseudolabel_overlap.csv`,
`AN-02_pool_verification.csv` (all 64 pools match their committed digests).
**Page note:** this is appendix text. If main-text room is needed, cut the positive-control
paragraph's last two sentences ("The control's own bar … *it would have seen the effect we are
nulling*"; about 4 lines). Their point is carried by Edit 3.

## Edit 7: `app:controls`, pseudo-label means

**Current:** "Across the seed expansion, the means are $1977$ (B), $2025$ (C10), $1990$ (CSHUF) and
$1979$ (CINV), with per-run values spanning $1817$ to $2259$."
**Proposed:** "Across the forty runs the seed expansion trained, the means are … (unchanged), spanning
$1817$ to $2259$. Across all sixty-four eight-seed runs they are $1991$, $2007$, $2020$ and $2015$,
spanning $1782$ to $2278$."
**Why:** the published means cover the 40 newly trained runs only. Both are true; say which is which.
**Evidence:** `EXPERIMENT_LOGS/AN-02_summary.json`, `rebuild/ABC/out/se/abc_runs.csv`.

## Edit 8: `sec:discussion`, larger budgets, architecture and generator scope (QA-02, CW-02d–e)

Add after "…a foreground supply not already exhausted,": "and in this pool a larger budget cannot
supply it. Doubling the budget raises the share of the training pool that differs between targeted
and random selection only from $14.1\%$ to $17.2\%$, tripling it lowers the share to $13.1\%$, and
spending the whole pool makes the two identical."
Add a final sentence to the first paragraph: "All of this concerns one generator used one way: a fixed
pool of offline re-renders whose foregrounds are copied from the base data. We did not test a
generator that creates new objects or adapts during training, and the null should not be read as
covering one."
**Evidence:** `EXP-01_preflight.csv`, `EXPERIMENT_LOGS/EXP-01_BLOCKER.md`, `EXPERIMENT_LOGS/EXP-03_BLOCKER.md`,
`AN-02_summary.json` (0 of 4106 injected foregrounds are new).

## Edit 9: `sec:conclusion`

**Current:** "…the gap stays within noise."
**Proposed:** "…the gap stays within noise; gains above about $0.007$ S-measure are excluded, and
smaller ones are not."

## Edit 10: `sec:why`, coverage and cluster numbers

The coverage range (synthetic 0.13–0.54; real source 0.71–0.75), the silhouette of 0.1600, "about a
fifth" of structural-error variance between clusters, and the 51.5% CAMO share were re-derived after
the review. See `RESULT_TABLES/AN-04_*` and `RESULTS_SUMMARY.md` §AN-04 for whether each reproduces.
Edit only where `RESULTS_SUMMARY.md` §AN-04 flags a discrepancy.

---

### What is deliberately *not* changed
- The pre-registered verdicts, `tab:trained`, and the 2σ̂ rule. All of them reproduce exactly.
- The geometric concentration result (`fig:thesis`a), which is untouched by any post-review analysis.
- The title. The downstream claim it makes, that targeted synthetic data does not help, is still
  supported within the stated bound.

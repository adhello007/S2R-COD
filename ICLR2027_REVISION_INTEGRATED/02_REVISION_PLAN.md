# 02 — Revision plan (written before the manuscript was edited, 2026-11-17 21:00 IST)

## Starting point

- **Submitted manuscript:** `AD-PCHGS-250926.tex` (repo root), 9-page main text. It is not modified.
- **Base for the revision:** `rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/revision/AD-PCHGS-revised.tex`.
  It already carries the RL5B edits and the confirmatory (EQ) and dose-response (CDR) results. Compiled unchanged
  as `paper/build_base/`, its main text ends on the last line of p.10.
- **Caus edits:** `manuscript_scope_edits.patch`, written against the original. Most hunks collide with RL5B's
  edits, so they are ported by hand.
- **dypE edits:** prose proposals only (`DOC-01_MANUSCRIPT_PROPOSED_EDITS.md`, and DOC-02 §5 for CHAMELEON), also
  ported by hand.

## Page rule (verified)

The [ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines) say:
- the limit is 10 pages during discussion, strictly enforced;
- references, the AI-use statement, the ethics statement and the reproducibility statement do not count.

The main-text boundary is therefore the end of the Conclusion, and the target is that it ends on p.10 or earlier.
Only template-neutral means are used: no font, margin, spacing or float-placement hacks.

## One central contribution, stated the same way everywhere

Author constraint 1, with the matching qualifier the author chose on 2026-11-17 (Q1):

> Within the tested pipeline (LAKE-RED fixed render pool, S2R-COD protocol, SINet/SINet-v2, N = 1000),
> uncertainty-guided allocation shows no detectable benefit over random allocation. A pre-registered
> confirmatory campaign establishes equivalence within ±0.005 S_α on the primary cell. Same-shape controls show that
> the direction of the signal adds nothing detectable. The selector's centroid matching and the budget's
> concentration explain how the selected training sets differ, but a pre-registered dose-response test found no
> effect of concentration on accuracy. The CHAMELEON audit is a separate contribution.

This wording is used in the abstract, the introduction, the contributions list and the conclusion. §3.2 states the
same claim at full length and its heading stays restricted to the training set.

## Headline experiment per reviewer, and why it was chosen

| Reviewer | Top concern (from the review) | Why it ranks first | Headline experiment | Main-body location |
|---|---|---|---|---|
| RL5B | CW-01 / Q1: non-detection is not equivalence | first weakness and first question; the whole null rests on it | pre-registered confirmatory campaign (EQ, 46 runs, INCOMPLETE), with the 8-seed intervals | **shared table in §3.1** (orange) |
| dypE | CW-01 / Q1: statistical sensitivity; smaller gains; paired analysis | first weakness and first question; the same concern as RL5B's | same EQ result, plus the paired analysis by seed | **same shared table in §3.1** (orange, one table for both) |
| Caus | Soundness 1. CW-01: the probe is a sanity check. Q1: an oracle of a different shape | lowest soundness score; Q1 is the only experiment Caus asked for and the only new trained one | EXP-01, oracle allocations of other shapes (12 runs) | **two rows in Table 2 (`tab:trained`) and two sentences in §3.1** (teal); the probe correction in §3.2 (teal) |

Because RL5B CW-01 and dypE CW-01 are the same concern, they get one combined body table rather than two.
The 16-row 8-seed TOST table (`tab:ci_tost`) moves to the appendix, which also pays for the new material.

## Placement map

| Result | Reviewer(s) | Main body | Appendix |
|---|---|---|---|
| EQ confirmatory, and the 8-seed Welch and paired intervals | RL5B, dypE | §3.1, new Table 3 | EQ design, deviations and RECHECK as exploratory (App. C) |
| All 16 eight-seed contrasts with 95/90% CIs and TOST | RL5B, dypE | one sentence | App. C (moved `tab:ci_tost`) |
| Oracle allocations of other shapes | Caus | Table 2 rows, §3.1 | new App. `app:shapeoracle` |
| Probe: a flat quota still separates (matching) | Caus | §3.2, one sentence | `app:shapeoracle` |
| CDR dose-response (not supported) | RL5B, dypE | §3.2 verdict sentence (existing) | new CDR table, App. C |
| Boundary metrics at 8 seeds; withdrawal of the 3-seed claim | RL5B, dypE | §3.2, two to three sentences; CINV−B exploratory sentence (constraint 7) | `tab:boundary` 8-seed, sweep, interaction (App. C) |
| Protocol-matched baselines, RISE, gap decomposition | RL5B | related-work sentence (existing) | App. A, `tab:protocol` (existing) |
| Scope: generator, foreground pool, detector, operating point | all three | Scope paragraph in the Discussion; abstract and conclusion | coverage appendix (k-NN at k = 5 and 20) |
| Foreground provenance, reuse, ICC, cluster distances | RL5B, Caus, dypE | Scope paragraph (existing) | coverage appendix |
| Realised contrast 77% / 14.1% (not 8.8%); exposure; pseudo-label Jaccard | dypE | — | App. C, "How much the trained comparison is attenuated" |
| Larger-budget preflight (1.22×, fails) | dypE | Discussion, one sentence | App. C |
| CHAMELEON: 51st match (withdrawn 17 Nov evening; report 03 §3), 32 COD10K-test re-encodes, 4 in CAMO-250, protocol exposure | dypE | §3.4, two to three sentences | CHAMELEON appendix: reconciliation and protocol table |
| COD10K-test: 7 byte-identical training images (author decision Q2) | dypE | — | CHAMELEON appendix, one sentence |
| Pre-registration timing (OR 62 min; SE at `a79886a`; tags) | Caus | — | App. B commit list; AI-use and reproducibility statements |
| Sign rule ≥ 7/8; power figures 0.20 / 0.0087 | RL5B (rule); RL5B and dypE (power) | §2, §3.1 (existing) | App. B (existing) |

## Ranked cuts for the page budget (applied in order until the Conclusion ends on p.10 or earlier)

1. Replace the 16-row `tab:ci_tost` in §3.1 with the compact shared table; move the full table to App. C, and merge it with `tab:tost` if they duplicate.
2. Shrink the §3.2 equivalence paragraph to one sentence.
3. Shrink the §3.2 boundary paragraph to about three lines plus the CINV sentence.
4. Drop the last two sentences of the positive-control paragraph; Table 3 carries their point.
5. Condense "Perhaps three seeds are too few".
6. Trim the intro paragraph that restates the null.

## What is deliberately not changed

- The title (constraint 2; ICLR does not allow title changes during discussion). The camera-ready retitle is
  proposed in `GENERAL_RESPONSE.md`.
- The pre-registered verdicts, `tab:trained`'s committed rows, and the 2σ̂ rule.
- The geometric result in Fig. 3a.

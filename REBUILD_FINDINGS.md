# REBUILD_FINDINGS.md — the cross-experiment ledger

The file [results/REBUILD_LOG.txt](results/REBUILD_LOG.txt) names this document as its destination:
*"Every number in `REBUILD_FINDINGS.md` must be traceable to a block here; a number without one is a
defect."* This is that file.

**It introduces no measured values.** Everything below is either (a) a count of `THRESHOLD` /
`OLD CLAIM` lines in the log, (b) a verdict sentence quoted from a `*_RESULTS.md`, or (c) a pointer.
For the finding behind any row, follow the row to its block. For the map of the whole package, see
[NAVIGATION.md](NAVIGATION.md); for old-value-vs-new accounting, [REVISION_TABLE.md](REVISION_TABLE.md).

**The rule: if a `*_RESULTS.md` and its log block disagree, the log wins.** §6 lists the three places
they currently disagree.

---

## 1. Read the cited blocks, not the whole log

The log is append-only and keeps superseded runs on purpose. Counting every block therefore
double-counts: E0, D2, B1, C1, D2R and D2_NC4K each hold re-runs, and a superseded block repeats its
FAIL line verbatim — C1 blocks 1–3 all carry the identical `d_order_spread` FAIL, B1 blocks 1–2 the
identical wrong-objective FAIL.

| Scope | Thresholds | PASS | FAIL |
|---|---|---|---|
| **Cited blocks only — the real state** | **143** | **127** | **16** |
| Every block in the log, including superseded | 307 | 279 | 28 |

> A grep for `FAIL` over the log returns 28 and means nothing. The honest figure is **16**, and §3
> shows that most of those 16 are the findings themselves.

Counts reproduce with:

```sh
grep -c '^THRESHOLD' results/REBUILD_LOG.txt                      # 307
grep '^THRESHOLD' results/REBUILD_LOG.txt | grep -c '> FAIL'      # 28
```

and per block by slicing the line ranges in §2.

---

## 2. Threshold ledger — per cited block

`Cited` is the block each `*_RESULTS.md` declares authoritative. Line numbers are into
`results/REBUILD_LOG.txt`.

| EXP | Cited block | Line | Thresh | PASS | FAIL | Readable file |
|---|---|---|---|---|---|---|
| E0 | 4 of 4 | 231 | 16 | 16 | 0 | [E0_RESULTS.md](rebuild/E0/E0_RESULTS.md) |
| D2 | 5 of 5 | 600 | 13 | 12 | 1 | [D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) |
| D1 | 1 of 1 | 696 | 10 | 10 | 0 | [D1_RESULTS.md](rebuild/D1/D1_RESULTS.md) |
| B1 | 2 of 4 — headline | 840 | 7 | 6 | 1 | [B1_RESULTS.md](rebuild/B1/B1_RESULTS.md) §1–8 |
| B1 | 3 of 4 — embedder sweep | 922 | 8 | 5 | 3 | B1_RESULTS.md §C1–C7 |
| B1 | 4 of 4 — allocation signal | 990 | 6 | 4 | 2 | B1_RESULTS.md §D1–D6 |
| C1 | 3 of 4 — measurement | 1148 | 7 | 6 | 1 | [C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) §1–7 |
| C1 | 4 of 4 — attribution audit | 1201 | 7 | 2 | 5 | C1_RESULTS.md §8 |
| ABC | 1 of 3 — pre-flight | 1252 | 16 | 16 | 0 | [ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) |
| ABC | 2 of 3 — run accounting | 1323 | 6 | 5 | 1 | ABC_RESULTS.md |
| ABC | 3 of 3 — verdict | 1376 | 3 | 3 | 0 | ABC_RESULTS.md |
| D2R | 4 of 4 | 1844 | 21 | 20 | 1 | [D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) |
| D2_NC4K | 2 of 2 | 2074 | 8 | 8 | 0 | *none* — [README.md](rebuild/D2_nc4k/README.md) is setup only |
| A3 | 1 of 1 | 2147 | 15 | 14 | 1 | [A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) |
| | | | **143** | **127** | **16** | |

ABC's three blocks are sequential **stages**, not re-runs: each is authoritative for its own content
and none supersedes another. B1's and C1's later blocks are **extensions** by different scripts, not
replacements — which is why both contribute their own threshold sets above.

---

## 3. What the 16 failures are

Quoted verbatim from the `THRESHOLD` lines. The classification column is each experiment's own, taken
from its `*_RESULTS.md` status header — not a judgement added here.

| # | Block | Declared threshold that failed | Its own classification |
|---|---|---|---|
| 1 | D2 b5 | no endpoint has >5% of its images as re-encodes of training data (EXPLORATORY, informs reportability) | **the headline finding** |
| 2 | B1 b2 | the binary wrong-objective classification is stable across the principled k and the old package's k=20 | **the most important result** |
| 3 | B1 b3 | the silhouette criterion actually selects a k in every embedder space (an interior maximum, not the grid edge) | substantive |
| 4 | B1 b3 | the ES-vs-error ORDERING (pixel >> structure > boundary) holds in every embedder space at every k tested | substantive |
| 5 | B1 b3 | the declared 0.5 wrong-objective boundary is stable across embedders as well as across k | substantive |
| 6 | B1 b4 | TARGET-ES keeps the same ordering as ENDPOINT-ES: MAE > 1-Sa > 1-IoU | **overturns the direction of B1's headline claim** |
| 7 | B1 b4 | on the REAL allocation signal the 0.5 wrong-objective boundary is still not stateable | substantive |
| 8 | C1 b3 | A2: d_order_spread < 0.05 at every peak cell | C1_RESULTS.md §5 |
| 9 | C1 b4 | C1's ceiling is a TARGETING ceiling: spending the whole budget on the highest-ES cluster beats an arbitrary cluster in a majority of cells | attribution audit |
| 10 | C1 b4 | ES-targeting exceeds the random-vs-random null by more than 0.5 in EVERY cell, i.e. the REOPENS verdict is attributable to targeting rather than to the statistic | attribution audit |
| 11 | C1 b4 | the ES SIGNAL itself adds something: targeted d_heldout beats its own ES-shuffled control by at least 0.1 in a majority of cells | attribution audit |
| 12 | C1 b4 | targeting the HIGHEST-ES cluster beats targeting an ARBITRARY cluster in a majority of cells | attribution audit |
| 13 | C1 b4 | the arms differ in more than their centre: spread ratio departs from 1 by at least 5% in a majority of cells | attribution audit |
| 14 | ABC b2 | CLS round-2 append counts agree across arms within 5% of the mean | divergence by construction, reported not absorbed (`ABC_PLAN.md` §A.12 item 3) |
| 15 | D2R b4 | T5 quantization tables differ in every confirmed pair AND the PIL and raw-DQT extractions agree pair-for-pair | **a correction to D2's own evidence** |
| 16 | A3 b1 | T8 the in-sample d on random halves exceeds 0.50 — reproducing C1's demonstration in A3's own data, which is what disqualifies the old 4.67 | **a correction to A3's own threshold design, left failing rather than repaired** |

Rows 9–13 are the five failures that produce C1's verdict **REOPENS-BUT-NOT-BY-TARGETING**: the old
`d ≈ 0.10` is refuted, and the separation that refutes it is *not* attributable to the ES signal.

---

## 4. Old-claim ledger

70 `OLD CLAIM` lines across the cited blocks: 66 carry a disposition, 4 blocks pin none.

| Disposition | Count | | Disposition | Count |
|---|---|---|---|---|
| MATCH | 34 | | SUPERSEDED | 4 |
| RE-MEASURED | 11 | | NEW | 3 |
| RECONCILED | 6 | | NOT-REPRODUCIBLE | 1 |
| MISMATCH | 4 | | RUN ANYWAY | 1 |
| CROSS-CHECK / CROSS-CHECKED | 2 | | *(none pinned)* | 4 blocks |

Per experiment, from its cited block:

| EXP | Dispositions |
|---|---|
| E0 | 1 SUPERSEDED, 1 CROSS-CHECK in A2 |
| D2 | 5 MATCH |
| D1 | 2 MATCH, 1 MISMATCH |
| B1 | b2: 6 RE-MEASURED · b3: 6 RECONCILED, 1 MATCH · b4: none pinned |
| C1 | b3: 3 RE-MEASURED · b4: 1 RUN ANYWAY |
| ABC | b1, b2: none pinned · b3: 2 SUPERSEDED, 2 RE-MEASURED, 1 CROSS-CHECKED against a TRAINED outcome for the first time |
| D2R | 8 MATCH, 3 MISMATCH |
| D2_NC4K | none pinned |
| A3 | 18 MATCH, 3 NEW, 1 SUPERSEDED, 1 NOT-REPRODUCIBLE |

**`RE-MEASURED` is a process marker, not an outcome** — it records that a claim was re-run with the
result treated as unknown. The outcome is in the `*_RESULTS.md`. B1's six re-measured claims resolve
in [B1_RESULTS.md §5](rebuild/B1/B1_RESULTS.md) as 3 MISMATCH (all moved *up*), 1 MATCH to four
decimals, 1 *refuted as a number* rather than moved, and 1 UNVERIFIED-DEFERRED. C1's three resolve in
[C1_RESULTS.md §2](rebuild/C1/C1_RESULTS.md). **Tabulating the log's `OLD CLAIM` field alone will
therefore mis-state the outcomes** — read those sections.

---

## 5. For writing the paper: the mandated "what changed" sections

[REBUILD_PLAN.md §2.5](REBUILD_PLAN.md) requires every `*_RESULTS.md` to carry a section stating, per
finding, *the claim we held, what was measured, the sharpened claim, and the concrete downstream
consequence.* That section — not the metric tables — is the prose-ready material.

Every file also carries a **"What X does not establish"** section — the limitation paragraphs,
already written. Both columns are section numbers within that experiment's `*_RESULTS.md`.

| EXP | "What changed" section | "Does not establish" section |
|---|---|---|
| E0 | §2 How the findings change our approach, thinking and assertions | §4 |
| D2 | §3 How the findings change our approach, thinking and assertions | §5 |
| D1 | §3 How the findings change our approach, thinking and assertions | §5 |
| B1 | §6 How the findings change our approach…; §C5 How this changes our assertions | §8, §C7, §D6 |
| C1 | §7 What this changes | §9 |
| A3 | §2 …our approach; §3 …our thinking; §4 …our assertions | §6, and §7 "Limitations, declared" |
| ABC | §3 How the findings change our approach, thinking and assertions | §5 |
| D2R | §3 How the findings change our approach, thinking and assertions | §5 |

Two more worth knowing about: [A3_RESULTS.md §0](rebuild/A3/A3_RESULTS.md) is "The result in one
paragraph" — the only such opener in the package, and directly quotable; A3 §5 is "The threshold that
FAILED — and why it stays failed", which is the write-up of row 16 in §3 above.

Three further documents carry reasoning rather than measurement:
[PREREGISTRATION.md](rebuild/ABC/PREREGISTRATION.md) (the decision rule, frozen before run 1),
[POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) (why added data cannot buy gradient
steps — a code trace with no log block of its own, §7(a) and §7(c) being the load-bearing parts), and
[CLEAN_PROTOCOL.md](rebuild/D2_reaudit/CLEAN_PROTOCOL.md) (which evaluation columns are reportable).

---

## 6. Discrepancies found while compiling this file

Recorded, not fixed. The log wins in all three.

1. **ABC block 1 threshold count.** The block carries **16** `THRESHOLD` lines, all PASS;
   `ABC_RESULTS.md` reports "15/15 thresholds PASS" in its status header and "15 PASS / 0 FAIL" in
   its block table. The 6/6 gates it also cites are a separate `METRICS` line
   (`preflight_gates_passed = 6/6`), so the two are not double-counting each other. Correct count: **16**.
2. **A3 old-claim NEW count.** The block carries **3** `-> NEW` dispositions across 23 `OLD CLAIM`
   lines; `A3_RESULTS.md` reports "4 NEW". Correct count: **3**. The other three A3 figures
   (18 MATCH, 1 SUPERSEDED, 1 NOT-REPRODUCIBLE) agree exactly.
3. **The `OLD CLAIM` vocabulary is wider than the log header declares.** The header declares
   `MATCH|MISMATCH|NEW|UNVERIFIED|NOT-REPRODUCIBLE`. In practice six more appear: `RE-MEASURED`,
   `RECONCILED`, `SUPERSEDED`, `RUN ANYWAY`, `CROSS-CHECK in A2`, and
   `CROSS-CHECKED against a TRAINED outcome for the first time`. `UNVERIFIED` is never used on an
   `OLD CLAIM` line. Either the header's list or the usage should be reconciled before publication.

Also outstanding, from [REVISION_TABLE.md](REVISION_TABLE.md) §5: **A1, A2, B2, B3, C3 were never
run**, and **C2 has no `EXP C2` block** — its load-bearing claim is carried by ABC block 2 at scale.

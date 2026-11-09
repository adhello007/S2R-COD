# EXECUTION_STATUS: RL5B rebuttal

*Living document. The final report to the corresponding author (§11 of the instructions) replaces this
header block when the work is complete.*

**Status at 2026-11-09 08:20 IST: campaigns running; nothing has been scored.**

## Compute budget (§6 of the instructions), filled at Stage 0 before launch

Measured: wall-clock minutes per committed SE run, `rebuild/ABC/out/se/abc_runs.csv`; one run per GPU
on 2× RTX PRO 6000 Blackwell.
- SINet: 105.9 min = **1.77 GPU-h**.
- SINet-v2: 121.9 min = **2.03 GPU-h**.

Concurrency probe (`EXPERIMENT_LOGS/stage0_concurrency_probe.log`), K jobs per GPU, total throughput
relative to K = 1:

| Architecture | K = 2 | K = 3 |
|---|---|---|
| SINet | 0.953× | 0.955× |
| SINet-v2 | 0.599× | — |

The GPUs are compute-bound, so the queue runs **one job per GPU**. Capacity from launch (2026-11-09
08:09) to the cutoff (2026-11-16 06:00 IST) is about 166 h × 2 ≈ 332 GPU-h.

| Task | Runs (SINet) | Runs (SINet-v2) | GPU-h/run | Total GPU-h | Priority | Decision |
|---|---|---|---|---|---|---|
| Bridge re-train | 1 | 0 | 1.77 | 1.8 | P0 | run |
| EXP-03 E3-c (single round) | 3 | 3 | ≈0.8 / ≈1.0 (est.; replaced by first measurement) | ≈5.4 | P1 | run |
| EXP-02 CDR SINet | 35 | — | 1.77 | 62.0 | P0 | run, never sacrificed |
| EXP-01 EQ SINet (n = 29) | 87 | — | 1.77 | 154.0 | P1 | run, never sacrificed |
| EXP-03 E3-e (RISE pseudo masks) | 3 | 3 | ≈0.8 / ≈1.0 | ≈5.4 | P1 | run if the released masks cover the 4040 stems |
| EXP-02 CDR SINet-v2 | — | 35 | 2.03 | 71.1 | P1 | run last; re-projected 11-12 and 11-14; dropped whole if it cannot finish |
| Inference (≈3 min/run, both endpoints) | — | — | 0.05 | ≈8.5 | — | — |
| **P0 + P1 total** | | | | **≈308** | | fits with ≈24 GPU-h of slack |
| EXP-03 E3-b (official SINet-V2 recipe) | — | 3 | ≈2 | ≈6 | P2 | **dropped before launch** (sacrifice order; E3-a and the published values stand in) |
| EXP-04 OP (higher operating point) | 21 | — | 1.77 | ≈37 | P2 | **dropped before launch**: it does not fit after P0 and P1 with any safety margin; it is reported as not run |

## Task status

| Task | Status | Start | End | GPU-h | Notes |
|---|---|---|---|---|---|
| Stage 0 setup | done | 11-09 07:30 | 11-09 08:09 | probe ≈0.9 | reproduction gate PASS (anchor and 4 SE runs, all 9 metrics at 6 dp) |
| TH-01 | done | 11-09 | 11-09 | 0 | reproduction PASS; posted sensitivity figure corrected (0.205 under the full rule, against 0.139 posted); n = 29 |
| TH-02 | done | 11-09 | 11-09 | 0 | τ_H = 0.758; toy recovers α |
| AN-01 | gate running | 11-09 | | 0 | |
| EXP-02 CDR | running (queued behind bridge and E3-c) | 11-09 | | | allocations drawn by the committed rule; gates 6/6 |
| EXP-01 EQ | queued | | | | pools being built and gated |
| EXP-03 | E3-c running | 11-09 08:09 | | | E3-a, E3-d and E3-e need the external downloads |
| EXP-04 | not run | | | 0 | dropped before launch (budget) |
| AN-02, AN-03, DOC-01/02/03 | pending | | | | |

## Deviations from the instruction file (each with its reason)

1. **Branch and working copy.** The work is on `rebuttal/iclr27/wip2`, in place, not on a new branch
   `rebuttal-RL5B` in a separate clone. The corresponding author decided this. About 600 GB of gitignored
   data and the pipeline's repo-relative paths make a clone impractical. Originals are preserved through
   new run IDs, new output tags and copy-only manuscript edits. The queue refuses to launch if the branch
   or the pipeline files change.
2. **Pushes.** This session has no GitHub credentials (no SSH key or agent, no `gh`), so it cannot push.
   The author pushes `rebuttal/iclr27/wip2` (never `main`).
3. **No co-author or attribution lines in commits**, by the author's instruction.
4. **Disk footprint.** New runs use `--save_ckpts minimal --link_pool`. This is opt-in, the defaults are
   unchanged, and the bridge run checks that it is numerically neutral. About 0.6 GB per run instead of
   about 5.5 GB, on a shared machine.
5. **Gate G3 amended.** A trainer copy is accepted only if it is byte-identical to the root trainer, or, in
   the archived `iclr2027_supplement/`, to the submitted trainer at `8d1d079`. Without the amendment the
   gate fails today on that archive.
6. **Sign rule in the TH-01 simulation.** It uses ≥ 7/8, the rule the SE campaign actually pre-registered
   and ran (`--min-sign 7`). The manuscript and the instructions say "every seed"; the 8/8 variant is
   reported beside it.
7. **CDR rule details that the instructions leave open** were fixed in `cdr_allocate.py` (commit `138ad30`)
   before the draw:
   - one stream, with LH continuing from where L1 stopped;
   - CSHUF counted as L1's P0;
   - Jaccard ≤ 0.50 also against LU and, at LH, against all L1 sets;
   - D = ½(B + LU), and σ̂ pooled over the CDR allocations (B excluded).
8. **E3-c checkpoint selection** scores the student (`--val_net student`), because a source-only EMA
   teacher has invalid BatchNorm buffers.
9. **`02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md`** was not supplied, and is listed as missing rather than
   reconstructed.
10. **Manuscript source.** `AD-PCHGS-250926.tex` differs from the committed `AD-PCHG-250926_Final.tex` only
    in two punctuation hunks in the AI-use statement. It is treated as the submitted source, as the
    instructions direct.

## Pushes the author must make

- `git push origin rebuttal/iclr27/wip2`, as soon as possible. Commits `138ad30` (the CDR rule, before the
  draw), `49383c0` (BRIDGE/E3 preregistrations) and `2137849` (EQ/CDR preregistrations) carry the
  provenance timestamps of the pre-registrations.

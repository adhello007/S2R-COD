# EXECUTION_STATUS: RL5B rebuttal

*Living document. The final report to the corresponding author (§11 of the instructions) replaces this
header block when the work is complete.*

**Status at 2026-11-11 18:30 IST: campaigns running; nothing campaign-related has been scored.**

## Author's binding rules for the revised manuscript and the final rebuttal (checked in the Phase 6 audit)

1. **Report what was not run, plainly.** The SINet-v2 replication (posted Part 2) and the higher operating point
   (posted Part 3) were not run. Never write "consistent across architectures". (11-11)
2. **Correct the posted 1.37× / 1.34×** with AN-01's eight-seed result. (11-11)
3. **TH-01 corrections to the posted sensitivity figures** are stated explicitly ("we stated X; the correct value
   is Y"). (11-11)
4. **RISE:** if AN-02 step 5 confirms it, add an explicit §8.2 correction of the posted description. (11-11)
5. **The pooled boundary regression** (AN01_regression.md: degenerate fit, post-treatment covariates) stays in
   RESULT_TABLES, labelled EXPLORATORY. In the rebuttal, report **only the per-contrast eight-seed boundary
   numbers**, and never present the pooled interval as evidence for a concentration effect; the pre-registered
   CDR test decides that. (11-12)
6. **EQ:** the section is held as the pre-written decision sentences until all 81 runs are trained; INCOMPLETE
   rule if the cutoff comes first. (11-11, 11-12)
7. **Appendix B of the paper** goes under §11 item 6. (11-11)

## Incidents on 2026-11-12 (≈11.9 GPU-h lost; no committed data lost)

| When | What happened | GPU-h lost |
|---|---|---|
| 11-11 23:21 to 11-12 01:49 | CDR L1P3/L1P4 s42 took about 147 min instead of 106, because CPU scoring (AN-01, the bridge check) competed with the data loaders | 1.37 |
| 01:50 to 02:00 | **Watchdog false restart.** The Caus pilot runs `exp01_pilot.py`, not MyTrain/MyTest, so GPU 0 looked idle for two checks. The watchdog killed the runner and its children: the pilot (re-run, then exit 0) and a healthy CDR L1P5 s42. The relaunch reused the killed run's log folder, failed verification (`rounds`) after a full run, and was retried successfully | 2.03 |
| 07:55:44 | **Power loss** (abrupt; no shutdown sequence). CDR LHP5 s42 and LU s43 were lost in training; the machine was down until 10:16 | 0.74 + 4.77 idle |
| 11:39:13 | **Power loss again.** The relaunched LHP5 s42 and LU s43 were lost after 80 min; the machine was down until 11:47 | 2.68 + 0.34 idle |

After each crash, `@reboot` restarted the runner (10:18 and 11:49). Each interrupted run was discarded and re-run
from scratch with the same seed (`discard` events). `git fsck` is clean; all completed runs are intact.

**Fixes (12:55–12:57, 11-12).**
- Watchdog: a GPU counts as busy if the runner's fresh state file lists a job on it, whatever program the job
  runs.
- Runner: a fresh launch always clears a leftover snapshot folder first.
- Runner: adoption matches only `python MyTrain.py|MyTest.py … --gpu N` processes. The first live adoption
  crashed on a shell whose command line mentioned MyTrain.py.
- `start_queue.sh` closes the watchdog's lock descriptor, so a runner started by the watchdog can no longer
  disable later watchdog checks.
- The two running CDR runs were adopted three times without interruption.

## Outage, 2026-11-09 08:48 to 2026-11-11 17:59, and the author's re-budget

**What happened.**
- **The outage.** The workstation lost power abruptly at 2026-11-09 08:48:29. The journal simply stops: there is
  no shutdown sequence and no GPU, thermal or MCE errors. Whether the combined load (two GPUs training, plus
  CPU scoring) contributed cannot be determined.
- **Restart.** The queue runner did not restart, and the machine rebooted three more times on 11-10. The queue
  was restarted at 2026-11-11 17:59. About 57 h of GPU time were lost.
- **Interrupted runs.** The bridge run was interrupted mid-training; it was discarded and re-run from scratch
  with the same seed (event `discard`, 11-11 17:59). E3 SINet s42 had finished training at 08:48:10; only its
  inference was interrupted, and it was redone.
- **Integrity.** `git fsck` is clean, and the EQ pools and manifests are intact (87 pools, gates 6/6).

**Author decisions, 2026-11-11.**
1. GPU cutoff extended to **2026-11-17 06:00 IST**.
2. **CDR SINet-v2 dropped**, before any of its runs started (sacrifice order, step 2).
3. **Order:** CDR SINet and the Caus different-shape oracle arms first, then the supervised anchors (E3-c),
   then EQ.
4. **EQ n** is the largest value that fits with at least 12 h of slack. If it is below 29, a dated
   pre-registration amendment, stating the new n and its power, is committed before any EQ run. All three
   arms are kept.
5. **The new-foreground campaign** is trained only if slack remains; otherwise its pool is built and
   validated, and the training is reported as not run.
6. An `@reboot` auto-restart and a 10-minute watchdog are added, with a heartbeat at
   `rebuild/RL5B/out/heartbeat.txt`.
7. **The final schedule is shown to the author before EQ launches.** EQ's jobs are held in
   `rebuild/RL5B/queue_jobs_held.json` until then.

**Blocked (input missing).** The Caus EXP-01 specification (the minimum set of different-shape oracle arms) and
the new-foreground campaign specification are not in the repository. The author has been asked for them.

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

1. **Branch and working copy (§0.4)** (decided 2026-11-09, restated 2026-11-11).
   - The branch is `rebuttal/iclr27/wip2`, not `rebuttal-RL5B`. It was kept to avoid touching a running
     queue; the author confirmed this on 11-11.
   - **This is not a separate working copy.** RL5B works in the main working copy
     `/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD`. The Caus and dypE sessions use their own git
     worktrees (`../S2R-COD-Caus`, `../S2R-COD-dypE`), which RL5B never reads.
   - About 600 GB of gitignored data and the pipeline's repo-relative paths make a separate clone
     impractical.
   - Originals are preserved through new run IDs, new output tags and copy-only manuscript edits. The
     runner refuses to launch if the branch or the training code changes.
2. **Pushes.** This session has no GitHub credentials (no SSH key or agent, no `gh`), so it cannot push.
   The author pushes `rebuttal/iclr27/wip2` (never `main`).
3. **No co-author or attribution lines in commits**, by the author's instruction.
4. **Disk footprint.** New runs use `--save_ckpts minimal --link_pool`. This is opt-in and the defaults are
   unchanged.
   - **Bridge check (2026-11-11):** COD10K |ΔS_α| = 0.00006, within the declared band, so the campaigns
     continue. All 21,828 linked source files are unchanged.
   - **Measured footprint** (correcting the planning estimate of 0.6 GB): about **3.1 GB per two-round SINet
     run**, against about 5.5 GB by default. The unavoidable part is CLS's committed choice to save the
     about 2,000 pseudo-labelled target images as full-resolution PNG (≈2.35 GB). Single-round anchors take
     about 0.65 GB.
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

11. **EXP-04 (higher operating point) not run** (decided 2026-11-09, before launch).
    - Reason: budget. The concurrency probe showed no throughput gain from running several jobs per GPU, and
      EXP-04 is first in the sacrifice order. It was never pre-registered.
    - Posted Part 3 promised to say so if it was not completed; the final rebuttal says it plainly.
12. **EXP-02 SINet-v2 replication not run** (decided 2026-11-11 by the author, before any of its runs
    started).
    - Reason: the 2026-11-09 power loss cost about 57 GPU-h; this is step 2 of the sacrifice order. Its 35
      jobs are recorded as cancelled in `rebuild/RL5B/queue_jobs_held.json`.
    - Posted Part 2 promised this replication. The final rebuttal says it was not run, and does **not** say
      "consistent across architectures".
13. **E3-b (official SINet-V2 recipe) skipped** (decided 2026-11-09, before launch). The reason at decision
    time was budget. E3-a then matched every published SINet-V2 COD10K value within 0.002, which meets the
    instructions' own skip condition ("skip if E3-a matches and the budget is short").
14. **EQ capped at n = 27 per arm** (2026-11-11, Amendment 1 in `prereg/EQ.md`, commit `808988b`, before any
    EQ run).
    - Reason: the outage, and GPU time given to other campaigns.
    - Power 0.78 at Δ = +0.0024; expected 90% CI half-width 0.00178.
15. **Runner guard refined** (2026-11-11 23:21).
    - What happened: commit `125cef0` moved `LICENSE` to `Src/LICENSE`. That is a non-code file inside a
      guarded directory, and the original guard paused every launch from 21:40 (GPU 0) and 22:07 (GPU 1)
      until 23:21. About 3 GPU-h were lost.
    - Fix: runner v2 (`rebuild/RL5B/rl5b_runner.py`, which imports the unmodified `rl5b_queue.py`) guards
      the same paths but only the `.py` files under `Src/`. All job commits still pass it, and no training
      code changed.
16. **Runner v2** (2026-11-11) adds:
    - adoption of in-flight runs;
    - the Caus external slots (`rebuild/REBUTTAL/EXTERNAL_JOBS/Caus/`, GPU-h counted separately);
    - the hard cutoff (2026-11-17 06:00 IST);
    - the disk rule (remaining queue + 50 GB);
    - E3-e only if it can finish before the cutoff.
18. **E3-e (our trainer on RISE's released pseudo masks) is optional and was not run** (author decision
    2026-11-12; reason: compute and the 17 Nov deadline). No E3-e run had started; its 6 jobs are recorded as
    cancelled in `rebuild/RL5B/queue_jobs_held.json`. The RISE pseudo-mask pool stays built and verified
    (`rebuild/RL5B/out/pool_risepl.json`). The gap decomposition shows E3-e's cells as "—".
19. **CPU policy while training runs** (author, 2026-11-12): all scoring and analysis runs under
    `nice -n 19`, pinned to at most 8 cores (`taskset -c 40-47`).
20. **Schedule decisions** (author, 2026-11-12): the order CDR → anchors → Caus → EQ is kept, with no Caus
    script moved or dropped. EQ stays at n = 27; if an outage leaves EQ unfinished, Amendment 1's
    INCOMPLETE rule applies. Every deliverable except the EQ results is due 16 Nov 22:00 IST; EQ results go
    in on 17 Nov after the last run, for delivery by 12:00.
21. **The EQ analysis is triggered by cron, once** (authorised by the author 2026-11-14).
    - `rebuild/RL5B/eq_autorun.sh` runs every 10 min and runs the committed `analysis/eq_analysis.py` exactly once.
    - **Strict mode** as soon as all 81 runs are trained and inferred.
    - **After the 2026-11-17 06:00 cutoff**, once no EQ run is in flight, with `--allow-incomplete` (Amendment 1's
      INCOMPLETE rule).
    - It computes and opens no EQ number before then. It runs under the CPU cap and logs to
      `EXPERIMENT_LOGS/EXP01_autorun.log`; a marker prevents a second run.
    - Its decision logic was tested on synthetic states (`--check` only) before installation.
    - Reason: the agent acts only during conversation turns. The dose-response analysis, due on 11-13 14:25,
      waited until 11-14 13:13 for that reason.
17. **Removed from scope** (author, 2026-11-11):
    - the new-foreground campaign; it is not an RL5B task, and posted Part 4 rules out a weaker substitute
      for a new generator;
    - the 8.8%/14.1% effective-contrast check and the CHAMELEON count. **Neither was computed in this
      session**; no file exists, and neither is used in any RL5B output.

## Pushes

- Confirmed on `origin/rebuttal/iclr27/wip2` (`git branch -r --contains`, 2026-11-11 21:14): `138ad30`,
  `49383c0`, `2137849`, `de3746f`, `223fa14`, `e43a5e9`, `125cef0`.
- This session still cannot push (no credentials). **`808988b` (EQ Amendment 1) and later commits need the
  author's push.**

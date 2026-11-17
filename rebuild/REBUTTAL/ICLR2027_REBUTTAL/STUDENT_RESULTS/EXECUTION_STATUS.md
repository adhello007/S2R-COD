# EXECUTION_STATUS: RL5B rebuttal

## Report to the corresponding author (§11), final at 2026-11-17 10:33 IST

**Delivery.**
- **16 Nov:** the non-EQ deliverables were complete at 21:59, against the 22:00 deadline, with no margin. The
  35-hour outage (14 Nov 21:27 to 16 Nov 08:38) had stopped all work.
- **17 Nov:** the committed EQ analysis ran once, by the cron trigger, at 07:40–08:16, after the cutoff and with
  no EQ run in flight. Its result was inserted into the manuscript, the rebuttal and these reports by 10:33, against
  the 12:00 deadline.
- **Checks:** `analysis/audit_recompute.py --final` passes (88 checks), and `analysis/path_check.py` passes.

1. **Tasks per status** (definitions from §7; details in `EXPERIMENTAL_EVIDENCE.md`).
   - **VERIFIED:** TH-01, TH-02, AN-01 (exploratory), AN-02, AN-03, DOC-02, DOC-03.
   - **PARTIALLY VERIFIED:**
     - EXP-01: INCOMPLETE, 46 of 81 runs; the primary question is resolved.
     - EXP-02: SINet complete; the SINet-v2 replication was not run.
     - EXP-03: E3-a, E3-c, E3-d and E3-f done; E3-b and E3-e not run.
     - DOC-01: everything filled; the title is the author's decision.
   - **BLOCKED (compute):** EXP-04, dropped before launch.
2. **GPU-hours** (final; one job per GPU on two GPUs):
   - RL5B campaigns: **354.1** (completed or discarded runs), plus the 0.9 h Stage 0 probe. EQ alone used 82.0
     GPU-h of training for its 46 runs.
   - Caus scripts: **22.0**, counted separately.
   - Lost to power outages: about **147**, itemised in the incident sections below.
3. **Verdicts.**
   - **EXP-01 (EQ, SINet, pre-registered, INCOMPLETE: 16 / 15 / 15 of 27 seeds per arm):** targeted and random
     allocation are **equivalent** within ±0.005 S_α on the primary cell. Δ = +0.0006, 90% CI
     [−0.0027, +0.0039], TOST p = 0.015, and 0.030 after Holm over four tests. Against the shuffled arm on
     COD10K, equivalence is not established (p = 0.056); on NC4K both contrasts are equivalent.
   - **EXP-02 (CDR, SINet, pre-registered):** the test did **not support** a downstream effect of concentration.
     Against a bar of 0.0193 Boundary-IoU, the committed shape differs from the dispersed reference by −0.0005
     and the twice-as-concentrated level by +0.0021. No secondary measure clears its bar.
4. **Corrections to the posted rebuttal** (all stated explicitly in `FINAL_UPDATED_REBUTTAL.md`):
   - Rule sensitivity at Δ = +0.005 is 0.20 under the full rule, not 0.14. The 80% detectable effect is 0.0087,
     not 0.008. σ̂ = 0.00343, not ≈ 0.00345.
   - The boundary figures 1.37× / 1.34× are three-seed figures. At eight seeds they are **0.30× / 0.64×**,
     within noise.
   - The pseudo-label means 1977–2025 cover seeds 46–50 only. Over all seeds they are 1991–2020 (runs
     1782–2278).
   - RISE's detector **is SINet-V2**, trained on pseudo masks for the same 4,040 images. It is not "a different
     training pipeline".
   - The "every seed" sign rule was ≥ 7/8 in the eight-seed campaign.
   - The confirmatory sample size, "fixed in advance", was cut from 29 to 27 before any run, and only 15–16 per
     arm finished.
5. **Concerns not FULLY ADDRESSED** (`FINAL_SCIENTIFIC_AUDIT.md`):
   - **CW-01: SUBSTANTIALLY.** Equivalence is established on the primary comparison. The title revision (P1.1b)
     is pending, and the incomplete campaign leaves H1b on COD10K unresolved. FULLY once the title is revised.
   - **CW-02: SUBSTANTIALLY.** The claim is fully corrected. The test ran on one architecture. The delivered
     concentration levels are closer than nominal. The unit-level interval excludes only boundary effects above
     ≈ 0.007.
   - **CW-03: SUBSTANTIALLY.** RISE's mask quality and recipe cannot be separated (E3-e not run). The higher
     operating point was not run.
   - **CW-04: SUBSTANTIALLY.** FULLY once the title carries the scope, as posted.
6. **Items needing the author's decision.**
   - **Title.** Option (ii) in `RESULT_TABLES/DOC01_claims.md` remains correct, and I recommend it. Two
     `[AUTHOR: title]` markers in `FINAL_UPDATED_REBUTTAL.md` (Part 4 and the summary) wait on this.
   - **Appendix B** of the paper (instruction).
   - **Push.** The 17 Nov commit needs your push.
   - **Cron entries** (`watchdog.sh`, `eq_autorun.sh`, `@reboot`): no longer needed. The runner is idle at the
     cutoff and the autorun marker is set. I have left them in place until you agree to remove them.
   - **Manuscript edits made without your review.** The main text ends exactly at the foot of page 10, with no
     spare line. All are listed in `RESULT_TABLES/DOC01_claims.md`.
     - 11-16: the delivered-concentration sentence in §3.2, and the untested operating point in the Discussion.
     - 17 Nov: the EQ sentences; an updated Discussion clause; and the removal of the conclusion's "smaller ones
       are not [excluded]", which the EQ result contradicts.
     - Page-budget trims in the Scope paragraph, and a fix to a stray ", " in the Discussion.

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

## Incidents, 2026-11-13 to 2026-11-16 (≈78 GPU-h lost; no committed data lost)

Times are from `journalctl --list-boots` and `rebuild/RL5B/out/queue_events.jsonl`. Every loss was abrupt
(the journal stops with no shutdown sequence). After each one, `@reboot` restarted the runner, which discarded
the interrupted runs and re-ran them from scratch with the same seed (`discard` events).

| Power lost | Back up | Interrupted runs (training time lost) | GPU-h lost (partial + idle) |
|---|---|---|---|
| 11-13 10:25 | 10:31 | CDR LU s47 (0.89 h) | ≈1.4 |
| 11-13 10:32 | 10:39 | none running (the runner had not restarted yet) | ≈0.2 |
| 11-13 11:36 | 12:32 | CDR LU s47 (0.95 h), E3 SINet-v2 SUPREAL s45 (0.39 h) | ≈3.3 |
| **11-14 21:27** | **11-16 08:38** | EQ C10 s108 (1.48 h), EQ CSHUF s108 (0.30 h) | **≈72.2** (35.2 h × 2 GPUs idle) |
| 11-16 10:32 | 10:40 | EQ B s109, C10 s109 (0.06 h each) | ≈0.5 |

**Consequences.**
- **EQ will not finish.** At 21:38 on 11-16, 35 of 81 EQ runs were complete, 2 were running and 44 were
  pending. One run takes ≈108 min, so 9 more runs can start before the 06:00 cutoff. Completed by about
  07:00 on 11-17: seeds 101–115 for all three arms, plus B s116, that is B 16, C10 15, CSHUF 15.
- **INCOMPLETE rule.** Amendment 1 applies: every completed run is analysed as pre-registered, the result is
  labelled INCOMPLETE, and the missing runs are named. `eq_autorun.sh` runs this once no EQ run is in flight
  after the cutoff.
- **Deadline.** The 16 Nov 22:00 deadline for the non-EQ deliverables was met with no margin (see the report above).

## Incidents on 2026-11-12 (≈11.9 GPU-h lost; no committed data lost)

| When | What happened | GPU-h lost |
|---|---|---|
| 11-11 23:21 to 11-12 01:49 | CDR L1P3/L1P4 s42 took about 147 min instead of 106, because CPU scoring (AN-01, the bridge check) competed with the data loaders | 1.37 |
| 01:50 to 02:00 | **Watchdog false restart.** The Caus pilot runs its own Python program, not MyTrain/MyTest, so GPU 0 looked idle for two checks. The watchdog killed the runner and its children: the pilot (re-run, then exit 0) and a healthy CDR L1P5 s42. The relaunch reused the killed run's log folder, failed verification (`rounds`) after a full run, and was retried successfully | 2.03 |
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

**Blocked at the time (resolved 11-11: the author supplied the Caus scripts and removed the new-foreground campaign).** The Caus EXP-01 specification (the minimum set of different-shape oracle arms) and
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
| TH-01 | VERIFIED | 11-09 | 11-09 | 0 | reproduction PASS; posted sensitivity figure corrected (0.205 under the full rule, against 0.139 posted); n = 29 recommended, capped at 27 |
| TH-02 | VERIFIED | 11-09 | 11-09 | 0 | τ_H = 0.758; toy recovers α |
| AN-01 | VERIFIED (exploratory) | 11-09 | 11-12 | 0 | 3-seed table reproduced (2 dp); 8-seed: 0.30× / 0.64×, all contrasts within noise |
| AN-02 | VERIFIED | 11-09 | 11-09 | 0 | 12/12 published values within 0.002 of our re-score; RISE correction (detector is SINet-V2); E3-e sentence corrected 11-16 (it was not run) |
| AN-03 | VERIFIED | 11-11 | 11-11 | 0 | independent count check PASS (23 arms) |
| EXP-02 CDR (SINet) | PARTIALLY VERIFIED | 11-09 (bridge) / 11-11 18:26 | runs 11-13 14:23; analysis 11-14 13:13; manuscript 11-16 21:35 | ≈64 incl. re-runs | verdict **not supported**; SINet-v2 replication not run (deviation 12) |
| EXP-01 EQ | PARTIALLY VERIFIED (INCOMPLETE) | 11-13 23:59 | runs 11-17 07:32; analysis 08:16 | 82.0 (training of 46 runs) | primary **equivalent** (TOST p = 0.015); H1b COD10K neither; 35 runs not started before the cutoff |
| EXP-03 | PARTIALLY VERIFIED | 11-09 08:09 | 11-14 13:24 | ≈7 (E3-c) | E3-a, E3-c, E3-d, E3-f done; E3-b and E3-e not run (deviations 13, 18) |
| EXP-04 | BLOCKED (compute) | | | 0 | dropped before launch (budget; deviation 11) |
| DOC-01 | PARTIALLY VERIFIED | 11-12 | 11-17 | 0 | all outcome sentences filled (CDR 11-16, EQ 11-17); main text ends on p. 10; title for the author |
| DOC-02, DOC-03 | VERIFIED | 11-12 | 11-14 | 0 | RISE, protocol table and gap paragraph; scope paragraph and sentences |
| Caus scripts (external) | 13/13 exit 0 | 11-12 | 11-14 01:13 | 22.0 (separate) | run only; not designed, read, scored or cited |

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

22. **Commit message corrected** (11-16).
    - What happened: `c5c73fd` said the CDR mixed models had run, but the script had crashed on a singular
      fit.
    - Correction: `c32d547` records that the level-only model fitted (all level contrasts ≈ 0, CIs include
      0) and that the exploratory covariate model could not be fit. Its covariates are constant within an
      allocation, so they are collinear with the grouping.
    - Both models are descriptive and decide nothing.
23. **`EXP02_allocations.csv` is not a separate file.** The per-allocation record (ρ, Jaccard to C10, nominal
    and induced N_eff, fill distances, set hashes) was written once, at the draw, to
    `rebuild/ABC/out/cdr/cdr_allocations.csv` (committed in `49383c0`, before any CDR run). It is cited from
    there rather than copied.
24. **Delivered concentration is weaker than nominal** (a design property, fixed before any run; not a
    deviation, recorded so that no one reads the CDR null without it).
    - Nominal N_eff for LU, L1 and LH is 75, 29.9 and 14.9.
    - Assigning each selected render to its nearest target centroid gives N_eff ≈ 50.3, 44.5 (40.4–48.4)
      and 40.9 (37.3–46.1). Random B gives 42.5.
    - The pre-registered test therefore varied concentration as this foreground pool can deliver it, which
      the final rebuttal states.

25. **A wording gap in the committed EQ sentence (i), noted before any EQ number exists.**
    - What it does: `analysis/eq_analysis.py` writes "with 27 fresh seeds per arm" (`N_PER_ARM`) whatever the
      number of completed runs.
    - Plan: under the INCOMPLETE rule, the sentence inserted into the manuscript and the rebuttal states the
      completed counts per arm, together with the pre-registered incomplete sentence.
    - The committed script is not changed.

## Pushes

- Confirmed on `origin/rebuttal/iclr27/wip2` at 2026-11-16 21:50 (`git branch -r --contains`): everything up
  to `c87e052`, including `808988b` (EQ Amendment 1), `b6cb93f` and `cd5fc28`.
- **Not yet pushed:** `c5c73fd`, `c32d547`, and the commits that follow (the author pushes manually).
- Earlier record (2026-11-11 21:14): `138ad30`, `49383c0`, `2137849`, `de3746f`, `223fa14`, `e43a5e9` and
  `125cef0` were on origin. This session has no credentials and never pushes.

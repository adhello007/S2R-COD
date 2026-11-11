# RL5B GPU schedule after the 2026-11-09 outage (projected 2026-11-11 18:16 IST)

**Cutoff:** 2026-11-17 06:00 IST (author decision 11-11).

**Basis.** One job per GPU on 2 GPUs, in queue-priority order. Run times are measured:

| Run type | Time per run |
|---|---|
| SINet, two rounds | 1.77 h |
| SINet, single round | 0.64 h |
| SINet-v2, single round | ≈0.75 h (estimated) |
| Inference, both endpoints | about 3 min |

**Schedule rule.** EQ n is the largest value ≤ 29 that leaves at least 12 h of slack before the cutoff.
EQ is **held** until the author approves this schedule.

**Order.**
1. Running: the bridge re-train (GPU 0, ends about 11-11 19:50) and E3-c SINet s43 (GPU 1, about 18:45).
2. CDR SINet: 35 runs.
3. Caus different-shape oracle arms: K arms × 3 seeds. **Specification pending from the author.**
4. Supervised anchors (E3-c): the remaining 4 runs.
5. EQ: B, C10, CSHUF × n seeds.
6. Only if slack remains: E3-e (RISE pseudo-label runs, 6) and the new-foreground campaign (specification
   pending).

**Dropped:** CDR SINet-v2 (35 runs), under the sacrifice order and by the author's decision. EXP-04 and E3-b
were dropped before launch.

| Caus arms K | CDR SINet ends | Caus ends | Anchors end | EQ n | Power at true Δ = +0.0024 | EQ ends | Slack |
|---|---|---|---|---|---|---|---|
| 0 | 11-13 03:28 | — | 11-13 05:03 | 29 | 0.81 | 11-16 12:21 | 17.6 h |
| 1 | 11-13 03:28 | 11-13 06:24 | 11-13 07:35 | 29 | 0.81 | 11-16 15:17 | 14.7 h |
| 2 | 11-13 03:28 | 11-13 08:56 | 11-13 10:31 | 29 | 0.81 | 11-16 17:49 | 12.2 h |
| 3 | 11-13 03:28 | 11-13 11:52 | 11-13 13:02 | 28 | 0.79 | 11-16 17:29 | 12.5 h |
| 4 | 11-13 03:28 | 11-13 14:23 | 11-13 15:59 | 27 | 0.78 | 11-16 17:49 | 12.2 h |

Power is the Welch-simulated TOST power at ±0.005, from `RESULT_TABLES/TH01_power.csv`. At every n ≥ 22,
power is at least 0.92 for a true Δ ≤ +0.0012.

If n falls below 29, a dated amendment to `prereg/EQ.md`, stating the new n and its power, is committed
before any EQ run starts.

**Protection.**
- `@reboot` restarts the queue.
- A watchdog runs every 10 minutes (`rebuild/RL5B/watchdog.sh`); its heartbeat is at
  `rebuild/RL5B/out/heartbeat.txt`.
- Any run interrupted mid-training is discarded and re-run from scratch with the same seed, and logged as a
  `discard` in `rebuild/RL5B/out/queue_events.jsonl`.
- One more outage of more than about 12 h would push EQ past the cutoff. If that happens, the n decision is
  revisited with the author before any further EQ run.

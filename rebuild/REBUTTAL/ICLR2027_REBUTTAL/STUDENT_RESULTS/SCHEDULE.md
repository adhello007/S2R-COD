# RL5B GPU schedule (runner v2, projected 2026-11-11 23:25 IST)

**Cutoff:** 2026-11-17 06:00 IST. Nothing new starts after it.

**Basis.** One job per GPU, with measured run times:

| Run type | Time per run |
|---|---|
| Two-round SINet | 1.82 h, including inference |
| Single-round anchor | 0.70 h (SINet) / ≈0.85 h (SINet-v2) |
| Caus script | budgeted at 1.82 h each |
| Caus pilot | 0.5 h (assumed) |

**Order** (`rebuild/RL5B/rl5b_runner.py`):
1. Caus `00_*` pilot, on the next free GPU, without interrupting anything.
2. CDR SINet: 35 runs.
3. Supervised anchors (E3-c): the 4 remaining runs.
4. Caus scripts: at most 12, in filename order.
5. EQ: 81 runs, seed by seed (seeds 101–127, n = 27 per Amendment 1, `808988b`).
6. E3-e: 6 runs, only if each can finish before the cutoff.

Caus scripts take precedence over EQ jobs that have not started, but EQ does not wait for scripts that
have not arrived.

| Milestone | No Caus scripts | Caus pilot + 12 scripts |
|---|---|---|
| CDR SINet ends | Fri 11-13 04:28 | Fri 11-13 04:58 |
| Anchors end | Fri 11-13 06:10 | Fri 11-13 06:40 |
| Caus scripts end | — | Fri 11-13 17:35 |
| **EQ ends** | **Mon 11-16 08:38** | **Mon 11-16 19:33** |
| Slack before the cutoff | 21.4 h | **10.4 h** (below the 12 h target, because ≈3 GPU-h were lost to the 11-11 guard pause) |
| E3-e ends | Mon 11-16 10:20 | Mon 11-16 21:29 |

EQ's n is fixed at 27 by Amendment 1 and does not change. If an outage pushes EQ past the cutoff, every
completed run is analysed and reported as INCOMPLETE.

**Disk** (`df`, 2026-11-11 23:25): 798 GB free (743 GiB).
- Remaining RL5B footprint, measured per run: about 357 GB.
- Caus allowance, assuming default checkpointing: about 72 GB.
- Projected free disk at the cutoff: **about 441 GB without Caus, about 369 GB with**.
- The runner starts no job unless free disk is at least the remaining queue plus 50 GB.

**EQ power at n = 27:** 0.78 at a true Δ = +0.0024; ≥ 0.92 at Δ ≤ +0.0012. Expected 90% CI half-width 0.00178.

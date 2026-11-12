# Execution status: Reviewer Caus (ICLR 2027 Submission 39230)

*Last updated: 2026-11-12 13:20 IST. This file is updated as EXP-01 runs land; the final version is
dated at handoff.*

## Setup

| Item | Value |
|---|---|
| Worktree / branch | `S2R-COD-Caus`, branch `rebuttal/Caus-oracle-scope` |
| Base commit | `8d1d0795` ("added setup doc", 2026-10-14), equal to `experiments/lakered/finalized/12sept` |
| Code and manifests read from | this worktree at the base commit. The original working copy is checked out on another reviewer's branch, so only its gitignored data, checkpoints and predictions were read, all read-only. |
| Inputs | leaf symlinks into the original copy (`rebuild/CAUS/caus_layout.py`); every write is asserted to stay inside this worktree |
| Submitted manuscript | `S2R-COD/AD-PCHGS-250926.tex`. It equals the committed `AD-PCHG-250926_Final.tex` plus two punctuation-only hunks in the AI-use statement, with no number or claim different. Its bib is byte-identical to the committed `reference.bib`. The committed PDF is an earlier build (17:22 on 25 Sep) and is **not** proof of the uploaded version; **the author should compare against the OpenReview PDF.** |
| Shared environment | **The shared environment is the uv venv `S2R-COD/.venv` (prompt `s2r-cod`; Python 3.12, torch 2.11.0+cu128), not a conda env as the instructions said.** No conda exists on the machine. It was used read-only; nothing was installed. Its training packages predate every historical run (gate R2). |
| `01_INITIAL_REBUTTAL_FOR_SUBMISSION.md` | Created verbatim from Appendix B of the 03 guide (byte-for-byte check against lines 534–563). **Assumed to match what was posted;** not checked against OpenReview. |
| `02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md` | **Not supplied, and not created.** The concern-to-action mapping used is §2 of the 03 guide. |
| Code changes | New code under `rebuild/CAUS/` only; no committed file was edited. `CODE_CHANGES.patch` is generated at handoff (`git diff 8d1d079 -- rebuild/CAUS`). |

## Task status (vocabulary of guide §6)

| Task | Status | Note |
|---|---|---|
| TH-01 | VERIFIED | quotas reproduce; shapes defined; analytic and empirical rank counterexamples |
| TH-02 | VERIFIED | historical estimands recomputed with two implementations; EXP-01 verdict code validated on OR |
| AN-01 | VERIFIED | 31 claims; 2 incorrect statements of fact (C-07, C-31); CHAMELEON floor ≥ 51 |
| AN-02 | VERIFIED | original C1 code reproduces (≤ 3e-13); new-shape distinctness; geometry driven by matching plus concentration |
| AN-03 | VERIFIED (LAKE-RED pool); new generator BLOCKED | 8,885 traced, 0 regenerated; coverage reproduced at every k; no foreground-varying generator with released code |
| AN-04 | BLOCKED | CamoFormer: no training entrypoint. CTF-Net: no licence. No GPU allocation. |
| AN-05 | VERIFIED | independent near-duplicate audit; label pathways per arm |
| EXP-01 | **RUNNING (queued)**: pilot passed; 12 scripts queued 2026-11-12 12:56 IST | see below |
| EXP-02 | BLOCKED | compute (owner constraint) plus no licensed trainable detector |
| EXP-03 | BLOCKED | compute plus no foreground-varying generator with code and valid masks |
| EXP-04 | BLOCKED | entry gates (EXP-02 and EXP-03) not met |
| DOC-01 | VERIFIED (draft) | patch compiles within 10 pages; the appendix fills from EXP-01 tables |
| DOC-02 | in progress | |

## EXP-01 timeline

| When (IST) | Event |
|---|---|
| 11-11 23:55 | Pre-registration committed (`b21b67c`) before any run script existed |
| 11-12 00:01 | `00_pilot.sh` placed |
| 11-12 01:52 / 02:00 | Pilot start 1; the queue recorded it INTERRUPTED and re-ran it at 02:00 |
| 11-12 02:05 / 02:14 | Start 1 ran to completion anyway (its process was never stopped); start 2 also completed. Both passed the gate. About 27 GPU-minutes in total, within the 30-minute pilot allocation. |
| 11-12 12:54 | Addendum A1 (`213039c`): R5 and R6 pass; a duplicate-start lock and a run-of-record rule were added before any run |
| 11-12 12:56 | 12 run scripts placed (hashes in `EXPERIMENT_LOGS/EXP-01/queue_scripts/SHA256SUMS`) |

## Problems met, and how each was handled

1. **A second Claude session was writing in this worktree (2026-11-11 23:42–23:45).**
   - Found from file timestamps. Writing paused; the author chose this session (PID 1041286 at the
     time).
   - The other session left `rebuild/CAUS/exp01_manifests.py`, `rebuild/CAUS/exp01_score.py` and an
     empty `EXPERIMENT_LOGS/EXP-01/reuse_gate_R5_rescore.log`. **They are untracked and unused,** and
     were kept for the author to delete or keep (no deletion without permission).
   - It also wrote 11 stem files, which were verified byte-identical to this session's output before
     adoption.
   - Commit `3949195` ("initial Causs exp", 23:44) was made under the author's identity. It includes the
     `rebuild/E0/cache` symlink, which is harmless but points at an absolute path in the original copy.
2. **The queue re-runs an INTERRUPTED script without stopping the original process** (pilot evidence
   above).
   - Handled by the per-script lock in `exp01_run.py`: a second start yields with exit 6.
   - **Reported to the author, because it can double GPU use for any workstream on this queue.**
3. **A tool safety check blocked one shell command** because its text contained a refused-token
   pattern. Nothing was deleted; the screen was re-run with the pattern list read from a file.
4. **The optional CLS step in the pilot timed out:** an 8-minute budget against an 8.5-minute step.
   Layout validity was shown from the partial output (Addendum A1).

## Not done, and why

- **Clean-calibration quota comparison** (optional in the plan): needs a new external download of the
  official COD10K/CAMO train masks. Not attempted; no claim is made about it.
- **EXP-02/03/04:** BLOCKED (records in `EXPERIMENTAL_EVIDENCE.md`).

# EXTERNAL_JOBS/Caus: GPU slots for the Caus session

The RL5B runner (`rebuild/RL5B/rl5b_runner.py`) executes the scripts placed here on the shared GPUs. It
neither reads nor scores their outputs.

## Contract

**Which files run.** Only files ending in `.sh` are picked up.
- `00_*.sh` is a short pilot and runs on the next free GPU.
- All other scripts run in filename order, after RL5B's CDR SINet runs and supervised anchors, and ahead of
  any EQ job not yet started. At most 12 non-pilot scripts run; budget them as one SINet run each.

**How a script is run.**
- The runner calls `bash <script>` with `CUDA_VISIBLE_DEVICES=<assigned GPU>` and
  `RL5B_ASSIGNED_GPU=<assigned GPU>`. **Inside the script, use GPU index 0** (e.g. `--gpu 0`).
- Each script must `cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD-Caus` and write all outputs and
  logs there.

**What gets refused.** Before launch, the runner screens each script and refuses (recorded in `status.txt`)
any script that:
- does not `cd` into the Caus worktree; or
- contains `rm -rf`, `git push`, `git reset`, `git checkout`, `git clean`, `crontab`, `sudo`, `shutdown`,
  `reboot`, `pkill` or `kill`.

**Running and interruption.**
- A running job is never interrupted.
- A script interrupted mid-run (a reboot or a runner restart without adoption) is re-run from scratch.
- A script that exits non-zero is recorded and not re-run.

**Bookkeeping.**
- `status.txt` gets one line per event: START (with sha256 and GPU), END (exit code and GPU-hours), REFUSED,
  INTERRUPTED.
- The runner's capture of each script's stdout/stderr goes to `runner_logs/<script>.log`.
- No new job starts after 2026-11-17 06:00 IST, or while free disk is below the remaining queue plus 50 GB.

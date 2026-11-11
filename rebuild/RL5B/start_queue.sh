#!/usr/bin/env bash
# Start the RL5B queue runner unless one is already running. Used by the @reboot cron entry and by
# watchdog.sh. Idempotent: an existing runner (pidfile, or exact command-line match) is left alone.
# The runner itself discards any run interrupted mid-training and re-runs it from scratch with the
# same seed (logged as a 'discard' event in rebuild/RL5B/out/queue_events.jsonl).
REPO=/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
cd "$REPO" || exit 1
PIDF=rebuild/RL5B/out/queue.pid
WLOG=rebuild/RL5B/watchdog.log
is_runner() { [ -r "/proc/$1/cmdline" ] && { tr '\0' ' ' < "/proc/$1/cmdline"; } 2>/dev/null | grep -q '^\.venv/bin/python rebuild/RL5B/rl5b_runner\.py --jobs'; }
if [ -f "$PIDF" ] && is_runner "$(cat "$PIDF")"; then exit 0; fi
for p in $(ls /proc | grep -E '^[0-9]+$'); do
  if is_runner "$p"; then echo "$p" > "$PIDF"; exit 0; fi
done
nohup .venv/bin/python rebuild/RL5B/rl5b_runner.py --jobs rebuild/RL5B/queue_jobs.json >> rebuild/RL5B/queue.log 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "[$(date '+%m-%d %H:%M:%S')] start_queue (${1:-manual}): started runner pid $(cat "$PIDF")" >> "$WLOG"

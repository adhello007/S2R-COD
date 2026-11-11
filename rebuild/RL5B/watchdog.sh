#!/usr/bin/env bash
# RL5B watchdog -- run by cron every 10 minutes. Writes a heartbeat file and keeps both GPUs working.
#
#   heartbeat: rebuild/RL5B/out/heartbeat.txt   (overwritten each check; history in rebuild/RL5B/watchdog.log)
#
# Rules
#   * runner dead and jobs pending                          -> start it (start_queue.sh)
#   * runner alive, jobs pending, a GPU without any of our  -> after 2 consecutive checks (20 min), stop the
#     MyTrain/MyTest processes, and the idle GPU is not        runner AND its children, then start a new runner;
#     explained by the queue's own guards                      the interrupted runs are discarded and re-run from
#                                                              scratch with the same seed (logged as discards)
#   * an idle GPU is "explained" (no restart) if: fewer pending jobs than idle GPUs; the GPU has < 24 GB free
#     (another user's job -- the runner is waiting by design); or the runner logged PAUSE in the last 20 minutes
REPO=/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
cd "$REPO" || exit 1
OUT=rebuild/RL5B/out
mkdir -p "$OUT"
exec 9>"$OUT/watchdog.lock"
flock -n 9 || exit 0
WLOG=rebuild/RL5B/watchdog.log
HB="$OUT/heartbeat.txt"
STATE="$OUT/watchdog_idle_count"
NVS=/usr/bin/nvidia-smi
now=$(date '+%Y-%m-%d %H:%M:%S')
PIDF="$OUT/queue.pid"
is_runner() { [ -r "/proc/$1/cmdline" ] && tr '\0' ' ' < "/proc/$1/cmdline" | grep -q '^\.venv/bin/python rebuild/RL5B/rl5b_queue\.py --jobs'; }
runner=""
if [ -f "$PIDF" ] && is_runner "$(cat "$PIDF")"; then runner=$(cat "$PIDF"); fi
pend_line=$(.venv/bin/python rebuild/RL5B/rl5b_queue.py --jobs rebuild/RL5B/queue_jobs.json --dry-run 2>/dev/null | tail -1)
pending=$(echo "$pend_line" | sed -n 's/.*pending \([0-9]*\).*/\1/p'); pending=${pending:-0}
done_n=$(echo "$pend_line" | sed -n 's/.*done \([0-9]*\),.*/\1/p'); done_n=${done_n:-0}
ours() {  # our MyTrain/MyTest parent processes on GPU $1 (workers share the cmdline; count >0 means busy)
  for p in $(ls /proc | grep -E '^[0-9]+$'); do
    c=$( { tr '\0' ' ' < /proc/$p/cmdline; } 2>/dev/null ) || continue
    case "$c" in *MyTrain.py*"--gpu $1"*|*MyTest.py*"--gpu $1"*) echo "$c" | grep -o -- '--save_model [^ ]*\|--model_path [^ ]*' | head -1 ;; esac
  done | sort -u
}
idle=0; gpu_lines=""; explained=""
for g in 0 1; do
  jobs_on=$(ours $g | sed 's#.*/\([^/]*\)/[^/]*$#\1#; s#.*/\([^/]*\)/$#\1#' | sort -u | tr '\n' ' ')
  util=$($NVS --query-gpu=utilization.gpu,memory.used,memory.free --format=csv,noheader,nounits -i $g 2>/dev/null | tr -d ' ')
  free_mb=$(echo "$util" | cut -d, -f3)
  gpu_lines="$gpu_lines\n  GPU$g util%,used MiB,free MiB = $util | our job(s): ${jobs_on:-NONE}"
  if [ -z "$jobs_on" ]; then
    idle=$((idle+1))
    if [ -n "$free_mb" ] && [ "$free_mb" -lt 24576 ]; then explained="$explained GPU$g-held-by-another-user"; fi
  fi
done
recent_pause=$(tail -40 rebuild/RL5B/queue.log | grep PAUSE | tail -1)
if [ -n "$recent_pause" ]; then
  ts=$(echo "$recent_pause" | sed -n 's/^\[\([0-9-]* [0-9:]*\)\].*/\1/p')
  if [ -n "$ts" ] && [ $(( $(date +%s) - $(date -d "$(date +%Y)-$ts" +%s 2>/dev/null || echo 0) )) -lt 1200 ]; then explained="$explained recent-PAUSE"; fi
fi
[ "$pending" -lt "$idle" ] && explained="$explained fewer-pending-than-idle"
cnt=$(cat "$STATE" 2>/dev/null || echo 0)
action="none"
if [ -z "$runner" ] && [ "$pending" -gt 0 ]; then
  bash rebuild/RL5B/start_queue.sh watchdog-runner-dead
  action="runner was dead -> started"
  echo 0 > "$STATE"
elif [ -n "$runner" ] && [ "$pending" -gt 0 ] && [ "$idle" -gt 0 ] && [ -z "$explained" ]; then
  cnt=$((cnt+1)); echo "$cnt" > "$STATE"
  if [ "$cnt" -ge 2 ]; then
    kids=$(ps -o pid= --ppid "$runner" | tr '\n' ' ')
    kill "$runner" $kids 2>/dev/null; sleep 20
    for k in $kids; do pkill -TERM -P "$k" 2>/dev/null; done; kill -9 "$runner" $kids 2>/dev/null
    rm -f "$PIDF"
    bash rebuild/RL5B/start_queue.sh watchdog-idle-gpu
    action="GPU idle for 2 checks with $pending pending -> stopped runner $runner and children [$kids], restarted"
    echo 0 > "$STATE"
  else
    action="GPU idle (check $cnt/2), watching"
  fi
else
  echo 0 > "$STATE"
fi
last=$(tail -3 rebuild/RL5B/queue.log)
disk=$(df -h "$REPO" | tail -1 | awk '{print $4" free of "$2}')
printf "RL5B heartbeat %s\nrunner pid: %s\njobs: done %s, pending %s (active jobs file; EQ held: see queue_jobs_held.json)\n%b\nexplained idle: %s\naction: %s\ndisk: %s\nlast queue log lines:\n%s\n" \
  "$now" "${runner:-NONE}" "$done_n" "$pending" "$gpu_lines" "${explained:-n/a}" "$action" "$disk" "$last" > "$HB.tmp" && mv "$HB.tmp" "$HB"
[ "$action" != "none" ] && echo "[$now] $action" >> "$WLOG"
exit 0

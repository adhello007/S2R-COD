#!/usr/bin/env bash
# One-shot trigger for the pre-registered EQ analysis (prereg/EQ.md, Amendment 1). Run by cron every 10 minutes;
# authorised by the corresponding author on 2026-11-14. Runs analysis/eq_analysis.py exactly once:
#
#   * as soon as all 81 EQ runs are trained and inferred (no EQ job pending or running) -> strict mode
#     (the script itself re-verifies all 81 and refuses if any is missing);
#   * or, after the GPU cutoff (2026-11-17 06:00 IST), once no EQ run is still in flight -> --allow-incomplete,
#     i.e. Amendment 1's INCOMPLETE rule: every completed run analysed, none dropped. Runs that started before the
#     cutoff are allowed to finish first; no new run starts after it.
#
# Until one of those holds it computes nothing and opens no EQ number. It never deletes anything. The CPU cap
# applies (nice 19, cores 40-47, BLAS threads 8). Usage: bash eq_autorun.sh [--check]  (--check: print the decision only)
REPO=/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
cd "$REPO" || exit 1
OUT=rebuild/RL5B/out
S=rebuild/REBUTTAL/ICLR2027_REBUTTAL/STUDENT_RESULTS
MARK="$OUT/eq_autorun.done"
LOG="$S/EXPERIMENT_LOGS/EXP01_autorun.log"
CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
[ -f "$MARK" ] && { [ $CHECK = 1 ] && echo "already done: $(cat "$MARK")"; exit 0; }
exec 8>"$OUT/eq_autorun.lock"
flock -n 8 || exit 0
STATE="$OUT/runner_state.json"; now=$(date +%s)
# test-only overrides, honoured ONLY with --check (they can never launch the analysis)
if [ $CHECK = 1 ]; then STATE=${EQ_AUTORUN_STATE:-$STATE}; now=${EQ_AUTORUN_NOW:-$now}; fi
read -r eq_pending eq_running state_age <<<"$( { .venv/bin/python -c "
import json,os,time
p='$STATE'; s=json.load(open(p))
pend=s.get('pending_by_campaign',{}).get('eq',0)
run=sum(1 for v in s.get('running',{}).values() if v['job'].startswith(('SINet_B_s1','SINet_C10_s1','SINet_CSHUF_s1')))
print(pend, run, int(time.time()-os.path.getmtime(p)))"; } 2>/dev/null )"
eq_pending=${eq_pending:-999}; eq_running=${eq_running:-1}; state_age=${state_age:-99999}
cutoff=$(date -d '2026-11-17 06:00:00' +%s)
mode=""
if [ "$state_age" -gt 600 ]; then
  decision="wait: runner state is stale (${state_age}s); the watchdog restarts the runner"
elif [ "$eq_pending" -eq 0 ] && [ "$eq_running" -eq 0 ]; then
  mode="strict"; decision="all EQ jobs trained and inferred -> run the pre-registered analysis"
elif [ "$now" -ge "$cutoff" ] && [ "$eq_running" -eq 0 ]; then
  mode="incomplete"; decision="cutoff passed, no EQ run in flight, $eq_pending EQ jobs never started -> Amendment 1 INCOMPLETE rule"
else
  decision="wait: $eq_pending EQ jobs pending, $eq_running running"
fi
if [ $CHECK = 1 ]; then echo "$(date '+%F %T') decision: $decision"; exit 0; fi
[ -z "$mode" ] && exit 0
run_eq() {
  ( cd "$S/analysis" && OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 \
      nice -n 19 taskset -c 40-47 "$REPO/.venv/bin/python" eq_analysis.py --workers 8 "$@" )
}
echo "[$(date '+%F %T')] $decision" >> "$LOG"
if [ "$mode" = "strict" ]; then
  run_eq >> "$LOG" 2>&1; rc=$?
  if [ $rc -ne 0 ] && [ "$now" -ge "$cutoff" ]; then
    echo "[$(date '+%F %T')] strict run refused (rc=$rc) after the cutoff -> INCOMPLETE rule" >> "$LOG"
    run_eq --allow-incomplete >> "$LOG" 2>&1; rc=$?; mode="incomplete"
  elif [ $rc -ne 0 ]; then
    echo "[$(date '+%F %T')] strict run refused (rc=$rc) before the cutoff -> waiting (a run may have been discarded and re-queued)" >> "$LOG"
    exit 0
  fi
else
  run_eq --allow-incomplete >> "$LOG" 2>&1; rc=$?
fi
echo "[$(date '+%F %T')] eq_analysis finished: mode=$mode rc=$rc" >> "$LOG"
[ $rc -eq 0 ] && echo "$(date '+%F %T') mode=$mode rc=0" > "$MARK"
exit 0

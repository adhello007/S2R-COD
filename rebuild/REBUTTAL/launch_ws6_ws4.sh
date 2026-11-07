#!/usr/bin/env bash
# REBUTTAL -- WS6 then WS4, chained so the two GPUs never carry two runs each.
# Launch ONLY on the author's explicit "go WS6+WS4". Planned start 2026-11-09 08:00 IST.
#   WS6: 12 runs (CORPROP, CORTOP x SINet, SINet-v2 x 42/43/45), ~11.5 h on two GPUs
#   WS4:  6 runs (SUP x SINet, SINet-v2 x 42/43/45), single round, wall clock UNMEASURED
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=.venv/bin/python
mkdir -p rebuild/REBUTTAL/logs
$PY rebuild/ABC/abc_train.py    --arms CORPROP,CORTOP   --tag ws6
$PY rebuild/ABC/abc_evaluate.py --arms CORPROP,CORTOP,B --tag ws6 --gaps ws6 --gpus 0,1
$PY rebuild/REBUTTAL/ws4_anchor.py --steps train,evaluate
echo WS6_WS4_DONE

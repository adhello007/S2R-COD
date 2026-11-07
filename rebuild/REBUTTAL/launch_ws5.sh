#!/usr/bin/env bash
# REBUTTAL -- WS5' (PREREGISTRATION_WS5.md). Launch ONLY on the author's explicit "go WS5'".
# Hard gate: must start by 2026-11-10 06:00 IST, else WS5' is DROPPED (SS WS5.2.1).
# Disk gate: free space must cover 102 runs x ~6.0 GB (pools already built) + 50 GB (SS WS5.2.3).
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=.venv/bin/python
DEADLINE=$(TZ=Asia/Kolkata date -d '2026-11-10 06:00' +%s)
NOW=$(date +%s)
if [ "$NOW" -gt "$DEADLINE" ]; then echo "WS5' DROPPED: past the 2026-11-10 06:00 IST launch gate"; exit 3; fi
NEED_GB=$(( 102 * 6 + 50 ))
FREE_GB=$(df -BG --output=avail . | tail -1 | tr -dc 0-9)
if [ "$FREE_GB" -lt "$NEED_GB" ]; then echo "WS5' HELD: ${FREE_GB} GB free < ${NEED_GB} GB needed (disk gate)"; exit 4; fi
if nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q .; then echo "WS5' HELD: a GPU is busy"; exit 5; fi
SEEDS=$(seq -s, 51 84)
$PY rebuild/ABC/abc_train.py    --arms B,C10,CSHUF --tag ws5 --archs SINet --seeds "$SEEDS"
$PY rebuild/ABC/abc_evaluate.py --arms B,C10,CSHUF --tag ws5 --archs SINet --seeds "$SEEDS" --gaps ws5 --min-sign 23 --gpus 0,1
$PY rebuild/REBUTTAL/ws5_analyse.py
echo WS5_DONE

#!/bin/bash
# Wait for the OR->FX chain, then run SE. rebuild/SE/PREREGISTRATION_SE.md.
# v3, 2026-09-19: scoring parallelised. The OR evaluation took 94 min at the
# default --workers 1; SE scores 64 cells, so single-threaded it would idle both
# GPUs for hours after training ends. --workers changes no number: abc_evaluate
# scores each (run, endpoint) cell independently and the pool only distributes
# those cells.
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
FX_CHAIN_PID=$1
echo "[se-chain] waiting on FX chain pid $FX_CHAIN_PID"
while kill -0 "$FX_CHAIN_PID" 2>/dev/null; do sleep 120; done
echo "[se-chain] FX chain exited at $(date -Is)"

echo "[se-chain] launching SE (40 new runs at seeds 46-50) at $(date -Is)"
.venv/bin/python rebuild/ABC/abc_train.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se > rebuild/SE/driver_se.log 2>&1
echo "[se-chain] SE driver rc=$? at $(date -Is)"

echo "[se-chain] evaluating SE (gaps=se, min-sign=7 per SE.1, workers=16)"
.venv/bin/python rebuild/ABC/abc_evaluate.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se --gaps se --min-sign 7 --workers 16 \
    > rebuild/SE/evaluate_se.log 2>&1
echo "[se-chain] SE evaluate rc=$? at $(date -Is)"
echo "[se-chain] SE_CHAIN_COMPLETE"

#!/bin/bash
# Wait for the OR->FX chain, then run the SE seed-expansion campaign.
# rebuild/SE/PREREGISTRATION_SE.md. Started 2026-09-18.
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
FX_CHAIN_PID=$1
echo "[se-chain] waiting on FX chain pid $FX_CHAIN_PID"
while kill -0 "$FX_CHAIN_PID" 2>/dev/null; do sleep 120; done
echo "[se-chain] FX chain exited at $(date -Is)"

echo "[se-chain] launching SE (40 new runs at seeds 46-50) at $(date -Is)"
.venv/bin/python rebuild/ABC/abc_train.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se > rebuild/SE/driver_se.log 2>&1
echo "[se-chain] SE driver rc=$? at $(date -Is)"

echo "[se-chain] evaluating SE (gaps=se, min-sign=7 per SE.1)"
.venv/bin/python rebuild/ABC/abc_evaluate.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se --gaps se --min-sign 7 \
    > rebuild/SE/evaluate_se.log 2>&1
echo "[se-chain] SE evaluate rc=$? at $(date -Is)"
echo "[se-chain] SE_CHAIN_COMPLETE"

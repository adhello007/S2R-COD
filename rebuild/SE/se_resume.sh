#!/bin/bash
# Resume SE after the 2026-09-20 power loss, then evaluate.
# The driver is idempotent: it re-verifies every run, skips the 36 that pass,
# and discards + re-runs the 2 that were mid-flight. No seed is added or
# dropped; SE.1's declared seed set is unchanged.
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
echo "[se-resume] start $(date -Is)"
.venv/bin/python rebuild/ABC/abc_train.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se >> rebuild/SE/driver_se.log 2>&1
echo "[se-resume] driver rc=$? at $(date -Is)"

echo "[se-resume] evaluating SE (gaps=se, min-sign=7 per SE.1, workers=16)"
.venv/bin/python rebuild/ABC/abc_evaluate.py --arms B,C10,CSHUF,CINV \
    --seeds 42,43,45,46,47,48,49,50 --tag se --gaps se --min-sign 7 --workers 16 \
    > rebuild/SE/evaluate_se.log 2>&1
echo "[se-resume] evaluate rc=$? at $(date -Is)"
echo "[se-resume] SE_COMPLETE"

#!/bin/bash
# Wait for the OR driver to exit, then evaluate OR and launch the FX campaign.
# Keeps both GPUs busy across the campaign boundary. Started 2026-09-18.
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
OR_PID=$1
echo "[chain] waiting on OR driver pid $OR_PID"
while kill -0 "$OR_PID" 2>/dev/null; do sleep 60; done
echo "[chain] OR driver exited at $(date -Is)"

echo "[chain] evaluating OR"
.venv/bin/python rebuild/ABC/abc_evaluate.py --arms CORACLE,C10,B --tag or --gaps or > rebuild/OR/evaluate_or.log 2>&1
echo "[chain] OR evaluate rc=$?"

echo "[chain] launching FX at $(date -Is)"
.venv/bin/python rebuild/ABC/abc_train.py --arms A0FX,BFX,C10FX --tag fx > rebuild/FX/driver_fx.log 2>&1
echo "[chain] FX driver rc=$? at $(date -Is)"

echo "[chain] evaluating FX"
.venv/bin/python rebuild/ABC/abc_evaluate.py --arms A0FX,BFX,C10FX --tag fx --gaps fx > rebuild/FX/evaluate_fx.log 2>&1
echo "[chain] FX evaluate rc=$? at $(date -Is)"
echo "[chain] CHAIN_COMPLETE"

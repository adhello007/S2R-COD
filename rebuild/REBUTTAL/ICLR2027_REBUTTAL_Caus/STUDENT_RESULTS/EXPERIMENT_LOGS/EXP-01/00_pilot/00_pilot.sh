#!/usr/bin/env bash
# Caus EXP-01 pilot (rebuild/CAUS/PREREGISTRATION_EXP01.md section 4). One job, hard cap 30 min.
# Smoke test, one-epoch pilots, R6 replay against the committed SINet_CORACLE_s42 log,
# inference parity on a historical checkpoint, optional CLS smoke and determinism repeat.
# Writes only inside the Caus worktree, into a NEW folder per start:
#   Result/CAUS_RUNS/00_pilot/<UTC stamp>_<pid>/
set -u
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD-Caus || exit 90
export PYTHONDONTWRITEBYTECODE=1
echo "pilot start $(date -Is) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} head $(git rev-parse --short HEAD)"
# the code this job runs is frozen by content; any drift stops the job before it uses the GPU
sha256sum --quiet -c - <<'SUMS' || { echo "code hash mismatch"; exit 91; }
6abb81784fd5ed09bf1e882366dafe6289e7c5e4a840abe1ac464001c3fcf02b  rebuild/CAUS/caus_common.py
7e51ea88272c3c84dab6ffac7fcf062589535559a2e181cd11356da1ce77cb15  rebuild/CAUS/exp01_alloc.py
8fe349918d329d853d1468bc66820797a14d31069b3a3c979a38a6806fe8a297  rebuild/CAUS/exp01_pool.py
cbe8a78754a0507a3949ed98aa82807a2873395613e1bd90d053431f4953dbd8  rebuild/CAUS/exp01_run.py
e9e02890af0fcbbf3c232fe5274b3f3656222956339f785dedecbd451da17ad6  rebuild/CAUS/exp01_pilot.py
3dbc68f4e3c466ee0bafa58c64e700c729d9b6c0c5f89e3130367f982c7878e2  rebuild/CAUS/exp01_smoke.py
c72d4b521295c601905a144693e8885ba781e549bb064fc0aee7db4058c35f68  rebuild/CAUS/exp01_cls_smoke.py
ed79f72f40e4df26d7ee0b886411e744bc920e0f11974b7f4de0b1be06aecf4f  MyTrain.py
7d17c3bf7bec8bd9c5693108dd79d1cb6b3df5f2ecb5af786619e4e98c92c7d3  MyTest.py
c111685dea74310dfb490c58e0b42775de149196114e5efe4955a5318dda577c  CLS.py
18b3f291e49f30267a80c85baf2f3f78d5bbc56467c76b235bdf3f49bbe2288e  Src/utils/Dataloader.py
97d579e1bad93f646fe04cf6d3851466a4d3d668b62fa8186444a4b94f4359b3  Src/utils/tool.py
1054af52775b7b0816d521fd0f1dc6478d79dd6b9bdbaa2fc14927a053f386a0  Src/model/SINet/SINet.py
ec4fdad101d735694c56620a15dc674d4162f79395eea16fd05df9fde450d50d  rebuild/ABC/abc_common.py
c7db1e8829535785415804609b10acf69bc83f6120e0414a9426dcdcd70f237b  rebuild/C1/c1_targeted_vs_random.py
3975157a654bc556f8932ea0a2ee9cc79ffd4c20e421d7c30a787af0b9c5bd4f  rebuild/C1/c1_space.py
a1594a2cd47ecf42416c6995f100cb50e277b0abedb1821d3effd834e7f4d93d  rebuild/ABC/abc_preflight.py
SUMS
timeout 30m /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/.venv/bin/python -B rebuild/CAUS/exp01_pilot.py --gpu 0 --budget-min 27
rc=$?
echo "pilot end $(date -Is) rc=$rc"
exit $rc

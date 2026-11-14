#!/usr/bin/env bash
# Caus EXP-01 run 05/12: SINet, arm ORTOP10, seed 43 (rebuild/CAUS/PREREGISTRATION_EXP01.md, sections 1 and 5).
# One two-round SINet run, then COD10K and NC4K inference. Writes only inside the Caus worktree,
# into a NEW folder per start: Result/CAUS_RUNS/05_EXP01_SINet_ORTOP10_s43/<UTC stamp>_<pid>/
# A second start while a first is still alive yields (exit 6) and trains nothing (Addendum A1).
set -u
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD-Caus || exit 90
export PYTHONDONTWRITEBYTECODE=1
echo "05_EXP01_SINet_ORTOP10_s43 start $(date -Is) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} head $(git rev-parse --short HEAD)"
# the code and the frozen stem list this job uses are pinned by content; drift stops it before the GPU is used
sha256sum --quiet -c - <<'SUMS' || { echo "code hash mismatch"; exit 91; }
6abb81784fd5ed09bf1e882366dafe6289e7c5e4a840abe1ac464001c3fcf02b  rebuild/CAUS/caus_common.py
7e51ea88272c3c84dab6ffac7fcf062589535559a2e181cd11356da1ce77cb15  rebuild/CAUS/exp01_alloc.py
8fe349918d329d853d1468bc66820797a14d31069b3a3c979a38a6806fe8a297  rebuild/CAUS/exp01_pool.py
58af281e118aeefc56d0962b316554c426bb4dc4e3461fc7fa6f482a0aca10c1  rebuild/CAUS/exp01_run.py
ed79f72f40e4df26d7ee0b886411e744bc920e0f11974b7f4de0b1be06aecf4f  MyTrain.py
7d17c3bf7bec8bd9c5693108dd79d1cb6b3df5f2ecb5af786619e4e98c92c7d3  MyTest.py
c111685dea74310dfb490c58e0b42775de149196114e5efe4955a5318dda577c  CLS.py
18b3f291e49f30267a80c85baf2f3f78d5bbc56467c76b235bdf3f49bbe2288e  Src/utils/Dataloader.py
97d579e1bad93f646fe04cf6d3851466a4d3d668b62fa8186444a4b94f4359b3  Src/utils/tool.py
1054af52775b7b0816d521fd0f1dc6478d79dd6b9bdbaa2fc14927a053f386a0  Src/model/SINet/SINet.py
5a79ad5d58c8cd66fb2ff35e538090d73258438a339a4db85e89fdabbf5819d9  Src/model/SINet/ResNet.py
808b55af7343407e07a71133f3672d9e7880e312661c85ac3c567afae97f85bd  Src/model/SINet/SearchAttention.py
0a5ba6d8c1dcf52befdd415659c744a8e76da0a64e1831624ea46eec48863373  rebuild/common.py
ec4fdad101d735694c56620a15dc674d4162f79395eea16fd05df9fde450d50d  rebuild/ABC/abc_common.py
a1594a2cd47ecf42416c6995f100cb50e277b0abedb1821d3effd834e7f4d93d  rebuild/ABC/abc_preflight.py
c7db1e8829535785415804609b10acf69bc83f6120e0414a9426dcdcd70f237b  rebuild/C1/c1_targeted_vs_random.py
3975157a654bc556f8932ea0a2ee9cc79ffd4c20e421d7c30a787af0b9c5bd4f  rebuild/C1/c1_space.py
1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8  rebuild/B1/out/b1_cluster_es_dinoL518.csv
5b9888d0ad319f5993bc28c39635eb88789682fede045cf3dd2014f2f39fe0e9  rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/RESULT_TABLES/EXP-01_stems/ORTOP10.txt
SUMS
/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/.venv/bin/python -B rebuild/CAUS/exp01_run.py --arm ORTOP10 --seed 43 --script 05_EXP01_SINet_ORTOP10_s43 --gpu 0
rc=$?
echo "05_EXP01_SINet_ORTOP10_s43 end $(date -Is) rc=$rc"
exit $rc

# 00 — Environment and provenance record

Recorded: 2026-11-11T18:05:06Z (UTC); 2026-11-11 23:35 IST

## Repository
```
worktree: /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD-dypE
branch:   rebuttal/dypE-validation
HEAD:     8d1d0795fc4e19474d51f89adf0c2d8fb977f313
base ref experiments/lakered/finalized/12sept: 8d1d0795fc4e19474d51f89adf0c2d8fb977f313
git status --short (at record time):
?? rebuild/REBUTTAL/
```

## Host
```
Linux ai-server-System-Product-Name 7.0.0-42-generic #42~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Mon Oct 19 14:43:01 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
CPU: AMD Ryzen Threadripper PRO 7965WX 24-Cores x 48 logical
               total        used        free      shared  buff/cache   available
Mem:             251          31         172           3          52         219
/dev/nvme0n1p2  1.8T  996G  744G  58% /
```

## GPU (listing only; no GPU process is started by this task)
```
GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition (UUID: GPU-d6fd39f7-327a-8052-7d99-daa6f50aac68)
GPU 1: NVIDIA RTX PRO 6000 Blackwell Workstation Edition (UUID: GPU-e31d9001-9405-23e5-0818-816db7cb4d5b)
driver: 595.99.02
```

## Interpreter (used read-only; CUDA_VISIBLE_DEVICES='' for every job)
```
/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/.venv/bin/python -> /usr/bin/python3.12
python 3.12.3
numpy 2.5.1
scipy 1.18.0
cv2 5.0.0
sklearn 1.9.0
torch 2.11.0+cu128
torchvision 0.26.0+cu128
matplotlib 3.11.2
PIL 12.3.0
torch.cuda.is_available() with CUDA_VISIBLE_DEVICES="": False
torch built CUDA 12.8
```

## Read boundaries
- Code and tracked artifacts: this worktree at base `8d1d079`.
- From `S2R-COD/` (checked out on another branch) only gitignored data are read: `Dataset/`, `Result/ABC/<64 manifest runids>`, `Snapshot/ABC/<same>`, plus `AD-PCHGS-250926.tex` and `reference 1.bib`.
- Nothing is written under `S2R-COD/`.

## Compute budget
CPU only (48 logical cores, jobs under nice -n 19, <=24 workers). GPUs committed to other campaigns until 17 Nov; none used here.

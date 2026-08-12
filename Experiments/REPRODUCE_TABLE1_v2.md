# Reproducing Table 1 (Ŝ2C: HKU-IS → COD10K) — "Ours" rows

Everything needed to retrain the **Ours** (CSRDA) rows of Table 1 from a clean state,
verified against the code actually in this repo (`MyTrain.py`, `CLS.py`, `Src/`, `Eval/`)
and against the machine this doc was written on.

> Status of this checkout: branch `experiments/wip1`, staged-but-uncommitted `.gitignore`,
> `pyproject.toml`, `uv.lock`. `MyTrain.py` / `CLS.py` / `Src/` / `Eval/` are the upstream
> originals — unmodified. Reproduction below assumes they stay unmodified.

---

## 1. Target numbers

Table 1, Ŝ2C task (source = synthetic HKU-IS, target = real COD10K-train unlabeled,
eval = COD10K-test).

| Model | Setting | Sα ↑ | Fβw ↑ | Eφad ↑ | Eφmn ↑ | Eφmx ↑ | Fβad ↑ | Fβmn ↑ | Fβmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|---|
| SINet | Source-Only | 0.6418 | 0.3707 | 0.7323 | 0.6570 | 0.7211 | 0.4653 | 0.4284 | 0.4718 | 0.0905 |
| SINet | Mean Teacher | 0.6984 | 0.4165 | 0.7092 | 0.7177 | 0.7805 | 0.4888 | 0.5106 | 0.5598 | 0.0915 |
| **SINet** | **Ours** | **0.7136** | **0.4814** | **0.7676** | **0.7443** | **0.7950** | **0.5548** | **0.5572** | **0.5960** | **0.0717** |
| SINet-v2 | Source-Only | 0.6466 | 0.4121 | 0.7332 | 0.6986 | 0.7035 | 0.4736 | 0.4640 | 0.4697 | 0.0976 |

The column names map 1:1 onto `Eval/MyEval.py` output columns:
`Smeasure, wFmeasure, adpEm, meanEm, maxEm, adpFm, meanFm, maxFm, MAE`.

Paper hyperparameters for Ŝ2C — **already hard-coded** as a task override in
[MyTrain.py:151-159](MyTrain.py#L151-L159), so you do **not** pass them on the CLI:

| Symbol | Meaning | Value | Flag |
|---|---|---|---|
| λ | teacher EMA smoothing | 0.996 | `--alpha` |
| μ | CLS discrepancy multiplier | 0.8 | `--u` |
| τ | CLS confidence threshold | 0.4 | `--tau` |
| a, b, c | ESLoss edge / region / saliency-offset weights | 0.9, 0.3, 0.5 | `--a --b --c` |
| — | source root | `./Dataset/Source/HKU-IS/` | `--source_root` |

Optimizer/schedule (parser defaults, [MyTrain.py:127-135](MyTrain.py#L127-L135)):
Adam, lr 1e-4, batch 16, trainsize 352, 40 epochs, decay ×0.1 at epoch 30.

---

## 2. How the CSRDA framework works

CSRDA is a **cyclic** synthetic-to-real domain adaptation loop. One invocation of
`MyTrain.py` runs `--iteration` rounds (default **2**). Each round is a full
mean-teacher training run; between rounds, CLS harvests confident pseudo-labels from
the real target domain and folds them into the source set for the next round.

```
                     ROUND i  ( for i in 1..iteration )   MyTrain.py:166
 ┌───────────────────────────────────────────────────────────────────────────┐
 │  fresh SINet student  S_θ   +  fresh teacher  T_φ  (T_φ ← copy of S_θ)     │  :170-187
 │                                                                           │
 │  ┌── source batch (labeled) ────────────────────────────────────────────┐ │
 │  │  x_s , y_s   ──► S_θ ──► (cam_sm, cam_im)                            │ │  :29
 │  │  L_sup = BCEwithLogits(cam_sm, y_s) + BCEwithLogits(cam_im, y_s)     │ │  :39
 │  └──────────────────────────────────────────────────────────────────────┘ │
 │  ┌── target batch (unlabeled, same step) ───────────────────────────────┐ │
 │  │  x_t ──weak aug──►  T_φ  ──sigmoid──►  p_tea   (no_grad)             │ │  :31-33
 │  │  x_t ──strong aug─►  S_θ  ──sigmoid──►  p_stu                        │ │  :35-36
 │  │  L_con = ESLoss(p_stu, p_tea)                                        │ │  :40
 │  └──────────────────────────────────────────────────────────────────────┘ │
 │                                                                           │
 │  L = L_sup + L_con  ──► Adam step on θ  ──► EMA: φ ← λφ + (1-λ)θ          │  :57-64
 │                                                                           │
 │  after each epoch > 20: MAE of T_φ on CAMO val → keep Tea_epoch_best.pth  │  :228-230
 └───────────────────────────────────────────────────────────────────────────┘
                                     │
                       if i < iteration │  CLS.py — Confident Label Selection
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │  load  Stu_40.pth (student)  and  Tea_epoch_best.pth (teacher)            │  CLS.py:53-65
 │                                                                           │
 │  PASS 1 — over every target image:                                        │  CLS.py:71-99
 │      d(x) = ESLoss_noWBCE( σ(S(x)) , σ(T(x)) )      # student-teacher     │
 │      d̄  = mean_x d(x)                               #   disagreement      │
 │                                                                           │
 │  PASS 2 — over every target image:                                        │  CLS.py:102-141
 │      keep x  iff  d(x) < μ · d̄                      # μ = 0.8            │  CLS.py:123
 │      cam = σ(T(x)) upsampled to original size                             │
 │      drop x if max(cam) < τ                         # τ = 0.4            │  CLS.py:131
 │      cam[cam < τ] = 0 ; min-max renormalize ; save as PNG pseudo-GT       │  CLS.py:134-137
 │                                                                           │
 │  writes:  Dataset/Source/HKU-IS_iteration{i+1}/{Image,GT}/                │
 │           = full copy of previous source  +  the kept real images         │
 │  returns that path → becomes opt.source_root for round i+1                │  MyTrain.py:233-235
 └───────────────────────────────────────────────────────────────────────────┘
```

### The three mechanisms, precisely

**(a) Mean-teacher consistency across the domain gap.**
Weak/strong augmentation split lives in
[Src/utils/Dataloader.py:82-94](Src/utils/Dataloader.py#L82-L94): the *weak* view is
resize+normalize only; the *strong* view adds `RandomAutocontrast` and
`GaussianBlur(3, σ∈[0.1,1.5])`. Both views come from the same image (with a shared
random horizontal flip applied first). The teacher sees the easy view and supervises
the student on the hard view. Teacher weights are an EMA of the student with λ=0.996
([Src/utils/tool.py:41-43](Src/utils/tool.py#L41-L43)).

**(b) ESLoss — the edge-aware + saliency-weighted consistency loss.**
[Src/utils/tool.py:45-77](Src/utils/tool.py#L45-L77):

```
edge_loss   = L1( |∇_sobel p_stu| , |∇_sobel p_tea| )
region_loss = BCE( p_stu , p_tea , weight = p_tea + c )       # c = 0.5
ESLoss      = a · edge_loss + b · region_loss                 # a = 0.9, b = 0.3
```

The Sobel term is what makes it *camouflage-aware*: boundary agreement is weighted
more heavily than area agreement, which is where synthetic→real transfer degrades
most. The saliency weight `p_tea + c` upweights pixels the teacher already believes
are object.

**(c) CLS — Confident Label Selection.**
A pseudo-label is admitted only if it passes **both** gates:
- *agreement gate* (μ): the student and teacher must disagree less than 0.8× the
  dataset-average disagreement. This is a relative, self-calibrating threshold — no
  absolute confidence cutoff needed.
- *saturation gate* (τ): the teacher's map must actually contain a confident object
  (`max(cam) ≥ 0.4`), and everything below 0.4 is zeroed before renormalizing, so the
  pseudo-GT is a clean soft mask rather than a diffuse blob.

Two instances of ESLoss exist for a reason
([MyTrain.py:193-194](MyTrain.py#L193-L194)): training uses the *saliency-weighted*
variant; CLS scoring uses `use_weighted_bce=False` so the ranking is not biased by
how much object area a given teacher map happens to predict.

**(d) The cycle.** Round 2 does **not** fine-tune round 1 — student and teacher are
re-instantiated from ImageNet weights at [MyTrain.py:170-187](MyTrain.py#L170-L187).
What carries over is only the *data*: the source set is now synthetic HKU-IS **plus**
the confidently-pseudo-labeled real COD10K images. That is the whole point — the
supervised branch now contains real-domain samples, so `L_sup` itself pulls the model
toward the target domain instead of only `L_con` doing it.

---

## 3. Training data

### What is present right now

| Role | Path | Contents | State |
|---|---|---|---|
| Source (synthetic) | `Dataset/Source/HKU-IS/` | 4447 `Image/*.jpg` + 4447 `GT/*.png` | ✅ ready |
| Source (alt, C2C) | `Dataset/Source/COD10K/` | 4446 + 4446 | ✅ present, not used for Ŝ2C |
| Val (real) | `Dataset/Val/CAMO/` | 250 `Imgs/*.jpg` + 250 `GT/*.png` | ✅ ready |
| Target (real, unlabeled) | `Dataset/Target/` | `Target.rar` (1.07 GB) | ❌ **not extracted** |
| Test (real) | `Dataset/Test/` | `Test.rar` (606 MB) | ❌ **not extracted** |

Archive contents (verified with `unrar lb`):
- `Target.rar` → `Target/Image/` × **4040** (COD10K train split), in **two naming
  schemes**: 3040 `COD10K-CAM-*.jpg` (camouflaged) + 1000 `camourflage_*.jpg`
  (non-camouflaged). Both are real target-domain images; the mix is expected, not
  corruption. It does mean CLS pseudo-labels carry both prefixes.
- `Test.rar`  → `Test/Image/*.jpg` × **2026** and `Test/GT/*.png` × **2026** (COD10K test split)

### Required final layout

```
Dataset/
├── Source/
│   └── HKU-IS/           Image/*.jpg (4447)   GT/*.png (4447)     ← source_root
│   └── HKU-IS_iteration2/  ← created by CLS after round 1, do not create by hand
├── Target/
│   └── Image/*.jpg (4040)                                          ← target_root
├── Test/
│   ├── Image/*.jpg (2026)                                          ← MyTest.py (hard-coded)
│   └── GT/*.png   (2026)                                           ← MyEval.py
└── Val/
    └── CAMO/  Imgs/*.jpg (250)   GT/*.png (250)                    ← val_root
```

⚠️ **The archives nest their own top-level folder.** Extract into `Dataset/`, not into
`Dataset/Target/` — otherwise you get `Dataset/Target/Target/Image/` and the loaders
will fail.

### Notes on the data pipeline

- `SrcDataset` pairs images↔GTs by **sorted filename order**, not by basename lookup
  ([Dataloader.py:14-18](Src/utils/Dataloader.py#L14-L18)). This is safe here:
  HKU-IS uses zero-padded numeric names (`0004.jpg` / `0004.png`) and CLS-generated
  files use `camourflage_*.png` for both image and GT, so the two sorted lists stay
  aligned across the mixed `.jpg`/`.png` source directory. **If you add data with
  other naming conventions, verify the alignment first** — a silent misalignment here
  produces garbage supervision with no error.
- `filter_files()` drops any pair where `img.size != gt.size`.
- Steps per epoch = `min(len(source_loader), len(target_loader))` =
  `min(⌈4447/16⌉, ⌈4040/16⌉)` = **253**.
- In round 2 the source set grows past 4447 while the target set stays at 4040, so
  `total_step` stays 253 and only a subset of source images is seen each epoch
  (the loader is shuffled, so coverage is stochastic across epochs).

---

## 4. Setup

### 4.1 Python environment

`uv.lock` is **missing packages the code imports**. One of them is train-blocking:

| Package | Needed by | Blocks |
|---|---|---|
| `scipy` | `Src/model/SINet/SearchAttention.py:6` (`scipy.stats`) | **training** — SINet cannot be constructed without it |
| `opencv-python` | `CLS.py`, `MyTest.py`, `Eval/MyEval.py` | training (CLS) |
| `scikit-learn` | `Eval/metrics.py:10` | evaluation only |
| `prettytable` | `Eval/MyEval.py:4` | evaluation only |
| `tqdm` | `Eval/MyEval.py:7` | evaluation only |

```bash
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD

# add the missing deps, then sync
uv add scipy opencv-python scikit-learn prettytable tqdm
uv sync

# verify
uv run python -c "
import torch, torchvision, cv2, sklearn, prettytable, tqdm, PIL, numpy
print('torch', torch.__version__, '| cuda', torch.cuda.is_available(),
      '| devices', torch.cuda.device_count())
print('capability', torch.cuda.get_device_capability(0))
"
```

Expected on this box: 2× RTX PRO 6000 Blackwell (96 GB each, sm_120), driver 595.84 /
CUDA 13.2. `pyproject.toml` already pins the `pytorch-cu128` index, which is the
correct wheel line for Blackwell.

> The paper's environment was Python 3.10 / torch 2.0.1. This box needs torch ≥ 2.7
> for sm_120, so exact bit-for-bit reproduction is not possible; expect small
> numerical drift from cuDNN/kernel differences.

### 4.2 Backbone weights (required — currently missing)

`SINet_ResNet50.initialize_weights()` loads a hard-coded path
([Src/model/SINet/SINet.py:211](Src/model/SINet/SINet.py#L211)). The file is not in
the repo. It is exactly torchvision's `IMAGENET1K_V2` ResNet-50 checkpoint, so you can
skip the Google Drive link:

```bash
curl -L -o Src/model/SINet/resnet50-11ad3fa6.pth \
  https://download.pytorch.org/models/resnet50-11ad3fa6.pth
# ~102 MB
```

Only if you also want the SINet-v2 row
([Res2Net_v1b.py:195](Src/model/SINetV2/Res2Net_v1b.py#L195)):

```bash
curl -L -o Src/model/SINetV2/res2net50_v1b_26w_4s-3cf99910.pth \
  https://shanghuagao.oss-cn-beijing.aliyuncs.com/res2net/res2net50_v1b_26w_4s-3cf99910.pth
```

### 4.3 Extract the datasets

```bash
cd Dataset
unrar x Target/Target.rar .     # -> Dataset/Target/Image/
unrar x Test/Test.rar   .       # -> Dataset/Test/{Image,GT}/
cd ..

# verify counts
ls Dataset/Target/Image | wc -l   # 4040
ls Dataset/Test/Image   | wc -l   # 2026
ls Dataset/Test/GT      | wc -l   # 2026
```

Leaving the `.rar` files in place is harmless — the loaders filter on `.jpg`/`.png`.

---

## 5. The training command

```bash
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD

uv run python MyTrain.py \
  --network SINet \
  --task S2C \
  --gpu 0 \
  --iteration 2 \
  --save_model ./Snapshot/SINet/S2C/ \
  --source_root ./Dataset/Source/HKU-IS/ \
  --target_root ./Dataset/Target/ \
  --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinet_s2c.log
```

That is the whole thing — **one command runs both CSRDA rounds and the CLS step
between them.** Do not run round 2 manually.

### Non-negotiable details

- **Every path argument must end with `/`.** The code does raw string concatenation
  (`opt.save_model + 'Tea_%d.pth'`, `opt.source_root + 'Image/'`). A missing slash
  silently writes `./Snapshot/SINet/S2CTea_40.pth`.
- **Do not change `--epoch`.** `CLS.py` looks for a checkpoint literally named
  `Stu_40.pth` ([CLS.py:42](CLS.py#L42)); it only exists because
  `--epoch 40` + the save rule at [MyTrain.py:84-86](MyTrain.py#L84-L86) produce it.
  Any other value breaks the cycle with `FileNotFoundError`.
- **Do not pass `--alpha/--u/--tau/--a/--b/--c`.** `--task S2C` overwrites them
  *after* parsing ([MyTrain.py:151-159](MyTrain.py#L151-L159)); anything you pass is
  discarded. This is by design and already matches the paper.
- Seed is fixed at 42 ([MyTrain.py:163](MyTrain.py#L163)). Note that
  `torch.backends.cudnn.deterministic` is **not** set, so runs are not bit-reproducible.

### For the SINet-v2 row

```bash
uv run python MyTrain.py --network SINet-v2 --task S2C --gpu 1 --iteration 2 \
  --save_model ./Snapshot/SINet-v2/S2C/ --source_root ./Dataset/Source/HKU-IS/
```
`--network SINet-v2` self-overrides to 100 epochs / batch 32 / decay@50 and enables
gradient clipping ([MyTrain.py:174-180](MyTrain.py#L174-L180)).

> ⚠️ **Never run SINet and SINet-v2 at the same time, and archive the CLS output
> between them.** Both networks are forced onto the same CLS working directory and
> will destroy each other's round-2 dataset. See §8 item 9 — this is the one gotcha
> that can silently invalidate a run.

```bash
# correct sequence for both rows
uv run python MyTrain.py --network SINet --task S2C --gpu 0 --iteration 2 \
  --save_model ./Snapshot/SINet/S2C/ 2>&1 | tee train_sinet_s2c.log

mv Dataset/Source/HKU-IS_iteration2 Dataset/Source/HKU-IS_iteration2-SINet   # keep the record

uv run python MyTrain.py --network SINet-v2 --task S2C --gpu 0 --iteration 2 \
  --save_model ./Snapshot/SINet-v2/S2C/ 2>&1 | tee train_sinetv2_s2c.log

mv Dataset/Source/HKU-IS_iteration2 Dataset/Source/HKU-IS_iteration2-SINetV2
```

---

## 6. Inference and evaluation

Use the **teacher** checkpoint from the **final** round.

```bash
# 1. generate masks on COD10K-test  (MyTest.py hard-codes ./Dataset/Test/{Image,GT}/)
uv run python MyTest.py \
  --network SINet \
  --model_path ./Snapshot/SINet/S2C/Tea_epoch_best.pth \
  --test_save ./Result/SINet/S2C

ls Result/SINet/S2C | wc -l    # must be 2026

# 2. evaluate — MUST run from inside Eval/ (it does `import metrics`)
cd Eval
uv run python MyEval.py \
  --gt_root   ../Dataset/Test \
  --pred_root ../Result/SINet/S2C \
  --txt_name  SINet/S2C
cd ..

cat Eval/eval_txt/SINet/S2C/_eval.txt
```

Leave `--data_lst` and `--model_lst` at their defaults (`['']`). They are declared
`type=list`, so passing a string on the CLI explodes it into single characters. With
the empty-string defaults, `os.path.join` resolves to the flat
`Dataset/Test/GT` ↔ `Result/SINet/S2C` layout, which is what you have.

---

## 7. Checklist

Run [`preflight.py`](preflight.py) to verify every item below automatically:

```bash
uv run python preflight.py                    # SINet / S2C defaults
uv run python preflight.py --network SINet-v2
uv run python preflight.py --skip-smoke       # skip the GPU fwd/bwd (no VRAM used)
uv run python preflight.py --deep             # + fully decode every source image
```

It exits 0 only when nothing is blocking, and prints the exact training command on
success. It covers packages, CUDA/arch, backbone weights (including SINet's key
remap), dataset counts, sorted-order image↔GT pairing, `filter_files` size drops,
`MyEval` name reachability, trailing slashes, stale artifacts, disk, the
`--epoch`↔`Stu_40.pth` coupling, the S2C hyperparameter override, `F.upsample`
availability, and a real batch + forward/backward at batch 16 / 352².

### Pre-flight (manual equivalent)

- [ ] `uv add opencv-python scikit-learn prettytable tqdm && uv sync` completes
- [ ] `uv run python -c "import torch;print(torch.cuda.is_available())"` → `True`
- [ ] `Src/model/SINet/resnet50-11ad3fa6.pth` exists (~102 MB)
- [ ] `Dataset/Target/Image/` has 4040 files
- [ ] `Dataset/Test/Image/` and `Dataset/Test/GT/` have 2026 files each
- [ ] `Dataset/Source/HKU-IS/{Image,GT}/` have 4447 files each
- [ ] `Dataset/Val/CAMO/{Imgs,GT}/` have 250 files each
- [ ] No stale `Dataset/Source/HKU-IS_iteration2/` from a previous attempt
      (CLS deletes it, but a partial one from a crashed run is confusing)
- [ ] No stale `Snapshot/SINet/S2C/` — **round 2 overwrites `Tea_epoch_best.pth`**;
      start clean or you cannot tell which round a checkpoint came from
- [ ] All `--*_root` / `--save_model` arguments end in `/`
- [ ] ≥ 20 GB free disk (checkpoints ≈ 220 MB each × ~15 saved, plus a 113 MB
      source copy; 1.6 TB free here — fine)

### During the run — what a healthy log looks like

- [ ] `[Source Loader] Loaded 4447 image-mask pairs` / `[Target Loader] Loaded 4040 images`
- [ ] `[INFO] initialize weights from resnet50` printed **twice** per round
      (student + teacher)
- [ ] `Global Step: XXXX/0253` — 253 steps per epoch
- [ ] `Loss_sup` falls steadily; `Loss_con` starts near 0 (teacher ≡ student at init)
      and rises, then settles
- [ ] From epoch 21: `Epoch: N, MAE: ..., bestteaMAE: ...` lines appear
- [ ] Round 1 ends → `[Info] Average edge loss: ...` → a stream of `[PGT] ...` lines.
      **Sanity-check the kept count:** `ls Dataset/Source/HKU-IS_iteration2/GT | wc -l`
      should be `4447 + N` with N a substantial fraction of 4040. N ≈ 0 or N ≈ 4040
      means μ/τ are not biting and the cycle is a no-op.
- [ ] Round 2 header `==== Iteration 2/2 started ====`, source loader now reports
      `4447 + N` pairs

### Post-run

- [ ] `Snapshot/SINet/S2C/Tea_epoch_best.pth` exists and is from round 2
- [ ] `Result/SINet/S2C/` contains 2026 PNGs
- [ ] `MyEval.py` prints no `not matching to the ground-truth` warning
- [ ] Compare against the Table 1 targets in §1. Expect ±0.005–0.01 drift from the
      published values given the different CUDA/PyTorch stack and non-deterministic
      cuDNN.

### Optional but recommended — build the full Table 1 column

To get the Source-Only and Mean Teacher rows too:
- **Source-Only**: train with only `L_sup` (comment out `loss_con` at
  [MyTrain.py:40,57](MyTrain.py#L40-L57)), `--iteration 1`.
- **Mean Teacher**: `--iteration 1` and swap `ES_Loss` for a plain MSE/BCE consistency.
Both are ablations, not the headline result — do them only if you need the deltas.

---

## 8. Known deviations and gotchas

These are **all in the original upstream code**. The defaults below are what produced
the published numbers, so *for reproduction, change nothing*. They are listed so you
are not surprised, and so you know what to fix if you later build on this.

**1. 39 epochs, not 40.**
[MyTrain.py:222](MyTrain.py#L222) is `for epoch_iter in range(1, opt.epoch)` →
`epoch_iter ∈ [1, 39]`. The checkpoint named `Tea_40.pth` is saved at `epoch_iter=39`
because saving uses `epoch+1`. Leave it alone — `CLS.py` depends on that filename.

**2. The LR schedule compounds.**
[tool.py:36-39](Src/utils/tool.py#L36-L39) does `param_group['lr'] *= decay` where
`decay = 0.1 ** (epoch // 30)`. For epochs 1–29 that is `×1` (no-op). For epochs
30–39 it is `×0.1` **every epoch**, so the LR goes 1e-5 → 1e-6 → … → 1e-14. The paper
says "dividing it by 10 after 30 epochs", i.e. a flat 1e-5.

*Practical consequence:* training is effectively frozen after epoch ~31, and
`Tea_epoch_best.pth` is in practice selected from epochs 21–31.

*Leave as-is for reproduction.* If you want the paper-as-written schedule:
```python
# Src/utils/tool.py
def adjust_lr(optimizer, epoch, decay_rate=0.1, decay_epoch=30, init_lr=1e-4):
    lr = init_lr * (decay_rate ** (epoch // decay_epoch))
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr
```

**3. `structure_loss` passes the deprecated `reduce='none'` (SINet-v2 path only).**
[tool.py:9](Src/utils/tool.py#L9) — `reduce` is the legacy argument and expects a bool,
not a string. **Verified working on torch 2.11.0+cu128** (`preflight.py` section I
exercises it and it returns a finite scalar), so this is cosmetic here, not a blocker.
It is still wrong — the intended spelling is `reduction='none'` — and it may break on a
future release, so re-run the preflight if you change the torch version.

**4. CLS copies the source tree twice.**
[CLS.py:12-28](CLS.py#L12-L28) — `MyTrain.py` passes `source_root` as *both*
`source_root` and `gt_root` ([MyTrain.py:234](MyTrain.py#L234)), so
`source_copy_root == gt_copy_root`. The function copies, then sees the destination
"already exists", deletes it, and copies again. Functionally correct, just ~113 MB of
wasted I/O. Harmless.

**5. Round 2 overwrites round 1's `Tea_epoch_best.pth`.**
Same `--save_model` directory both rounds, and `best_teamae` resets to 1 at
[MyTrain.py:197](MyTrain.py#L197). If you want round 1's model (the "Mean Teacher"-ish
baseline), copy it out during the CLS step.

**6. EMA covers parameters only, not buffers.**
[tool.py:41-43](Src/utils/tool.py#L41-L43) iterates `.parameters()`. The teacher's
BatchNorm running statistics are therefore *not* EMA'd from the student — they are
updated by the teacher's own forward passes, which happen in `train()` mode
([MyTrain.py:20](MyTrain.py#L20)) on weakly-augmented target images. This is arguably
a feature (target-domain BN statistics) but it is not standard Mean Teacher.

**7. Model selection uses CAMO, not COD10K.**
[MyTrain.py:230](MyTrain.py#L230) validates on `Dataset/Val/CAMO/`. COD10K-test is
never touched during training — good, no test leakage — but the selected checkpoint is
the CAMO-MAE-optimal one, not the COD10K-optimal one. Keep it that way; changing it
invalidates the comparison.

**9. The CLS working directory is shared by every network — and CLS deletes it.**
This is the most damaging gotcha in the repo, so it gets the most space.

`CLS.py` derives its output path from `source_root` **alone**
([CLS.py:15-16](CLS.py#L15-L16)) — the network name is not part of it:

```python
source_copy_root = source_root.rstrip('/\\') + f'_iteration{iteration + 1}/'
```

And you cannot separate the two networks with `--source_root`, because the
`--task S2C` block hard-resets it *after* argparse
([MyTrain.py:159](MyTrain.py#L159)):

```python
if opt.task == 'S2C':
    ...
    opt.source_root = './Dataset/Source/HKU-IS/'   # your --source_root is discarded
```

So **both** `--network SINet` and `--network SINet-v2` write to
`./Dataset/Source/HKU-IS_iteration2/`. CLS then opens by *deleting* it
([CLS.py:18-20](CLS.py#L18-L20)):

```python
if os.path.exists(source_copy_root):
    shutil.rmtree(source_copy_root)          # <-- the previous network's set, gone
shutil.copytree(source_root, source_copy_root)   # fresh copy of pristine HKU-IS
```

Consequences:

| Scenario | Outcome |
|---|---|
| **Sequential** (SINet finishes, then SINet-v2) | Not polluted — cleanly wiped and rebuilt from pristine `HKU-IS/`. SINet's trained weights in `Snapshot/SINet/S2C/` are safe, but its **pseudo-label set is permanently lost**, so you can no longer audit or re-run round 2. |
| **Concurrent** (`--gpu 0` and `--gpu 1` together) | **Destructive race.** `SrcDataset` snapshots its file list when the round-2 loader is built; the other process's `rmtree` then pulls the files out from under it → `FileNotFoundError` mid-epoch, or worse, silently reading the *other* network's pseudo-labels for whichever names happen to overlap. Never do this. |

Mixing is not a failure mode — deletion is. There is no code path that interleaves two
networks' pseudo-labels, because the `rmtree` + `copytree` always restores a pristine
4447-file source before writing.

*Fix, no code change:* run sequentially and rename the directory after each network.

```bash
mv Dataset/Source/HKU-IS_iteration2 Dataset/Source/HKU-IS_iteration2-SINet
```

*Fix, one-line code change* (needed only if you want concurrent runs): delete or
guard `opt.source_root = './Dataset/Source/HKU-IS/'` at
[MyTrain.py:159](MyTrain.py#L159) so `--source_root` is honoured, then give each
network its own copy of the source tree (`cp -r Dataset/Source/HKU-IS
Dataset/Source/HKU-IS-SINet`, 113 MB each). This deviates from the released code, so
note it if you publish the numbers.

`preflight.py` checks all of this: it reports the resolved CLS output path, FAILs if
another `MyTrain.py` is already running against the same source root, and WARNs if
another network's checkpoints exist.

**10. Validation only runs after epoch 20.** Before that no `Tea_epoch_best.pth`
exists. If you kill a run early, `CLS.py` falls back to `Tea_40.pth`
([CLS.py:61-63](CLS.py#L61-L63)) — which also will not exist. Let each round finish.

---

## 9. Resource and time estimates

| | |
|---|---|
| GPU memory | ~10–14 GB at batch 16 / 352² (student fwd+bwd + teacher fwd). 96 GB available. |
| Steps | 253 / epoch × 39 epochs × 2 rounds = 19,734 optimizer steps |
| CLS overhead | 2 passes × 4040 images × 2 models = ~16k forwards per cycle, a few minutes |
| Wall clock (SINet, 1× RTX PRO 6000) | **rough estimate ~2–4 h total** for both rounds. Time the first epoch and extrapolate rather than trusting this. |
| Disk | ~3.5 GB (checkpoints) + 113 MB (source copy) + ~1.7 GB (extracted data) |
| Parallelism | **None.** SINet and SINet-v2 cannot run concurrently — they share one CLS working directory (§8 item 9). Run sequentially on a single GPU. |

Note `num_workers=6` is hard-coded in the loader calls
([MyTrain.py:204](MyTrain.py#L204), [:208](MyTrain.py#L208)) — raise it there if the
GPU is data-starved.

---

## 10. Quick reference — full sequence

```bash
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD

# --- setup (once) ---
uv add opencv-python scikit-learn prettytable tqdm && uv sync
curl -L -o Src/model/SINet/resnet50-11ad3fa6.pth \
  https://download.pytorch.org/models/resnet50-11ad3fa6.pth
cd Dataset && unrar x Target/Target.rar . && unrar x Test/Test.rar . && cd ..

# --- train (both CSRDA rounds + CLS, one command) ---
uv run python MyTrain.py --network SINet --task S2C --gpu 0 --iteration 2 \
  --save_model ./Snapshot/SINet/S2C/ --source_root ./Dataset/Source/HKU-IS/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinet_s2c.log

# --- test ---
uv run python MyTest.py --network SINet \
  --model_path ./Snapshot/SINet/S2C/Tea_epoch_best.pth \
  --test_save ./Result/SINet/S2C

# --- evaluate ---
cd Eval && uv run python MyEval.py --gt_root ../Dataset/Test \
  --pred_root ../Result/SINet/S2C --txt_name SINet/S2C && cd ..
```

# SegMaR + CSRDA — Ŝ2C (HKU-IS → COD10K), Table 1 "Ours"

Settings used, every deviation from the paper, and the steps to reproduce.

Papers: *Synthetic-to-Real Camouflaged Object Detection* (S2R-COD), ACM MM '25 ·
[*Segment, Magnify and Reiterate*](https://openaccess.thecvf.com/content/CVPR2022/papers/Jia_Segment_Magnify_and_Reiterate_Detecting_Camouflaged_Objects_the_Hard_Way_CVPR_2022_paper.pdf) (SegMaR), CVPR '22 ·
Code: [dlut-dimt/SegMaR](https://github.com/dlut-dimt/SegMaR)

---

## 0. Read this first

**SegMaR was not in this repo.** `Src/model/` held only `SINet/` and `SINetV2/`, and
`--network` was a hard-coded two-way choice. This was an architecture port.

**S2R-COD never publishes SegMaR's training settings.** §4.1 gives exactly one configuration
(40 epochs / batch 16 / lr 1e-4 / ÷10 @ 30) and scopes it to *"SINet as the baseline"*. The
released code then silently overrides SINet-v2 to 100 epochs / batch 32 / decay @ 50 — numbers
that appear nowhere in the paper. So per-model settings existed but were never published, and
SegMaR's are unrecoverable from either the paper or the code.

**We therefore use SegMaR's own official defaults**, following the same convention the repo
already applies to SINet-v2: each model keeps its native config. Treat the SegMaR row as a
faithful *reconstruction*, not a settings-exact replication.

---

## 1. Training settings used

| Setting | Value | Where it comes from |
|---|---|---|
| epochs | `50` (**49 actually run**, see §4) | SegMaR `train.py` |
| batch size | `24` | SegMaR `train.py` |
| learning rate | `2.5e-5` | SegMaR `train.py` — **4× lower than SINet's 1e-4** |
| `decay_rate` | `0.9` | SegMaR `train.py` (SINet uses 0.1) |
| `decay_epoch` | `40` | SegMaR `train.py` |
| input size | `352 × 352` | both |
| `channel` | `32` | SegMaR `train.py` (`feat_channel`) |
| optimizer | Adam | both |
| gradient clipping | **off** | SegMaR `train.py` uses none |
| backbone | ResNet-50, IMAGENET1K_**V2** | see §2.4 |
| λ (teacher EMA) | `0.996` | S2R-COD §4.1, Ŝ2C |
| μ, τ (CLS) | `0.8`, `0.4` | S2R-COD §4.1, Ŝ2C |
| α, β, δ (ES Loss) | `0.9`, `0.3`, `0.5` | S2R-COD §4.3 |
| cycling iterations | `2` | S2R-COD §4.1 |
| evaluated model | teacher only | S2R-COD §4.1 |

All of this is applied automatically by `--network SegMaR --task S2C`. The per-network block in
`MyTrain.py` sets epoch/batch/lr/decay; the `--task S2C` block sets λ/μ/τ/α/β/δ. **You do not
pass any of them on the CLI** — `--task S2C` overwrites λ/μ/τ/α/β/δ after argparse, and the
network block overwrites epoch/batch/lr/decay.

### Supervised loss

SegMaR's `Generator.forward(x)` returns two maps, both upsampled to input resolution:

```
fix_pred, cod_pred2 = model(x)
loss_sup = structure_loss(fix_pred, gt) + structure_loss(cod_pred2, gt)
```

`cod_pred2` is the COD output — it alone feeds the consistency loss, CAMO validation, CLS and
testing. This mirrors SegMaR's own `train.py` (`fix_loss + cod_loss2`, equally weighted, both
via `structure_loss`), with one substitution explained in §2.3.

---

## 2. Deviations from the papers

Four, all forced. Each is a deliberate, documented choice — not an oversight.

### 2.1 SegMaR's hyperparameters come from SegMaR, not S2R-COD

Unavoidable: S2R-COD never states them (§0). The alternative — reusing the paper's SINet
settings (40/16/1e-4) — would contradict how the repo demonstrably treats SINet-v2, and would
run SegMaR at 4× its native learning rate.

### 2.2 Single-stage only (SegMaR-1) — no magnify/reiterate

SegMaR's defining feature is its iterative *Segment → Magnify → Reiterate* loop. We run **stage
one only**. `OurSampler/` requires **MobulaOP + NVIDIA-Apex on CUDA 10.0 / cuDNN 7.4 /
Python 3.6**; this machine is torch 2.11.0+cu128 on sm_120 Blackwell. Those dependencies cannot
be built here.

Mitigating context: Table 1 lists a single SegMaR row with **no stage count** (other papers
distinguish SegMaR-1 from SegMaR-4), and CSRDA already supplies its own 2-round cycling. If the
authors used multi-stage SegMaR, expect our numbers to fall short — most visibly on boundary-
sensitive metrics, since magnification is what sharpens contours.

### 2.3 `fix_pred` is supervised by GT, not the Discriminative Mask

Upstream, `fix_pred` is supervised against a precomputed **Discriminative Mask** (fixation +
edge attention). `OurSampler/DiscriminativeMask.py` builds it from `Edge/` **and** `fixation/`
maps — and **no fixation annotations exist for LAKE-RED-synthesised HKU-IS**, so the DM cannot
be constructed for our source domain at all.

SegMaR's own `train.py` sanctions the fallback:

> *"or you can replace it with GT because the discriminative mask is not provided"*

So both heads are GT-supervised, which also means **no dataloader change was needed** — the
existing `SrcDataset` is used unmodified. Cost: SegMaR loses its fixation/edge attention prior,
so this is the deviation most likely to depress the boundary metrics (`Fβw`, `Emx`).

### 2.4 Backbone is IMAGENET1K_V2, not V1

SegMaR calls `models.resnet50(pretrained=True)`, which in 2022 resolved to **V1**
(`resnet50-0676ba61.pth`). We load the **V2** file this repo already uses for SINet
(`Src/model/SINet/resnet50-11ad3fa6.pth`), so SegMaR stays comparable to the already-reproduced
SINet rows rather than introducing a second backbone variant.

This works because SegMaR's `B2_ResNet` uses **exactly** the layer names as SINet's
`ResNet_2Branch` (`layer1, layer2, layer3_1, layer4_1, layer3_2, layer4_2`), so the `_1`/`_2`
key remap and its `assert` transfer unchanged. Verified: full key coverage, no missing tensors.

### 2.5 Inherited upstream quirks (unchanged on purpose)

These affect **every** row and must stay consistent, or the Table 1 comparison breaks:

| Quirk | Effect on SegMaR |
|---|---|
| `range(1, opt.epoch)` | **49 epochs run, not 50.** `Stu_50.pth` is written at `epoch_iter = 49` — which is exactly the filename `CLS.py` requires. Do not change `--epoch`. |
| `adjust_lr` compounds (`lr *= decay` every epoch past `decay_epoch`) | **Mild here.** With `decay_rate 0.9`: `0.9¹⁰ ≈ 0.349` across epochs 40–49, so lr drifts 2.5e-5 → 8.7e-6. Contrast SINet's `0.1¹⁰ = 1e-10`, which kills training outright. |
| `structure_loss` passes legacy `reduce='none'` | Degenerates the weighted BCE to plain mean BCE (the weighted-IoU term is unaffected). SegMaR uses `structure_loss` on **both** heads, so it is more exposed than SINet — but SINet-v2 has the same exposure and still reproduced. |
| `update_ema` copies `.parameters()` only | Teacher BN statistics come from its own forwards on weakly-augmented target images. Fine for `ours`; **breaks the teacher under `--method source_only`** — see [`SOURCE_ONLY.md`](SOURCE_ONLY.md). |

---

## 3. Steps to reproduce

### 3.1 What was added (already done)

```
Src/model/SegMaR/ResNet.py             B2_ResNet         (verbatim upstream)
Src/model/SegMaR/HolisticAttention.py  HA                (verbatim; needs scipy.stats)
Src/model/SegMaR/SegMaR.py             Generator         (imports repointed; weight load → local V2)
```

Wired into `MyTrain.py` (choices, per-network block, `trainer()` branch, `val()` branch),
`MyTest.py` (choices, inference branch), `CLS.py` (model + `Stu_50.pth`/`Tea_50.pth`, both
inference passes), `preflight.py` (backbone map, epoch↔CLS coupling, smoke test).

No new dependencies: `scipy` was already installed, and no Apex/MobulaOP is involved.

### 3.2 Pre-flight

```bash
uv run python preflight.py --network SegMaR --save_model ./Snapshot/SegMaR/S2C/
```

Expect `0 fail`. It confirms the backbone key remap, that `--epoch 50` yields the `Stu_50.pth`
that `CLS.py` hard-codes, and runs a real forward/backward at batch 24.

### 3.3 Train (both CSRDA rounds + the CLS step, one command)

```bash
uv run python MyTrain.py --network SegMaR --task S2C --method ours --iteration 2 \
  --gpu 0 --save_model ./Snapshot/SegMaR/S2C/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_segmar_s2c.log
```

- Omit `--source_root`: `MyTrain.py`'s `--task S2C` block hard-resets it.
- Start from an **empty** `./Snapshot/SegMaR/S2C/` — round 2 overwrites `Tea_epoch_best.pth`.
- **Do not run concurrently with another `--iteration 2` job.** All networks are forced onto
  `Dataset/Source/HKU-IS/`, so they share `HKU-IS_iteration2/`, which CLS deletes on entry.

Then archive the pseudo-label set:

```bash
mv Dataset/Source/HKU-IS_iteration2 Dataset/Source/HKU-IS_iteration2-SegMaR
```

### 3.4 Test (teacher) and evaluate

```bash
uv run python MyTest.py --network SegMaR --gpu 0 \
  --model_path ./Snapshot/SegMaR/S2C/Tea_epoch_best.pth --test_save ./Result/SegMaR/S2C
ls Result/SegMaR/S2C | wc -l          # 2026

cd Eval && uv run python MyEval.py --gt_root ../Dataset/Test \
  --pred_root ../Result/SegMaR/S2C --txt_name SegMaR/S2C ; cd ..
cat Eval/Eval/eval_txt/SegMaR/S2C/_eval.txt
```

---

## 4. What to watch

**Measured at setup** (so you can spot a regression):

| | |
|---|---|
| Parameters | 56.2 M per network (×2 for student + teacher) |
| Peak GPU memory | 9.5 GB at batch 24 / 352² (fwd + bwd + Adam step, both nets) |
| Steps per epoch | `min(⌈4447/24⌉, ⌈4040/24⌉) = min(186, 169)` = **169** → log shows `/0169` |
| `Loss_sup` at init | ≈ 3.0, falling to ≈ 2.35 within 20 steps (two `structure_loss` heads) |
| `Loss_con` at init | ≈ 0.27–0.33 (ES Loss, α=0.9 / β=0.3) |

**During the run:**

- `Loss_con` must be **non-zero** — `0.0000` means `--method` was misrouted to `source_only`.
- Both outputs are `(B, 1, 352, 352)`; `fix_pred` and `cod_pred2` are separate heads, and only
  the second is the COD prediction.
- After round 1: `ls Dataset/Source/HKU-IS_iteration2/GT | wc -l` should be `4447 + N` with N a
  substantial fraction of 4040 (SINet gave 1906, SINet-v2 1875). N ≈ 0 or ≈ 4040 means μ/τ are
  not biting and the cycle is a no-op.
- Round 2's source loader should report `4447 + N` pairs.

**Before trusting metrics** — sanity-check the masks:

```bash
uv run python -c "
import numpy as np, cv2, glob
a=[cv2.imread(f,0).astype(np.float32)/255. for f in sorted(glob.glob('Result/SegMaR/S2C/*.png'))[:200]]
print('mean %.4f  std %.4f  frac>0.5 %.4f' % (np.mean([x.mean() for x in a]),
      np.mean([x.std() for x in a]), np.mean([(x>0.5).mean() for x in a])))"
```

Healthy ≈ `mean 0.15–0.20, std 0.26–0.34, frac>0.5 0.15–0.21` (GT is 0.180 / 0.337 / 0.180).
`mean ≈ 0.59, std ≈ 0.14` means the checkpoint did not load — see
[`CHECKPOINT_LOADING_BUG.md`](CHECKPOINT_LOADING_BUG.md).

---

## 5. Targets

Table 1, Ŝ2C, SegMaR:

| Setting | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|
| Source-Only | 0.6468 | 0.4091 | 0.6947 | 0.6943 | 0.7199 | 0.4522 | 0.4648 | 0.4880 | 0.1215 |
| Mean Teacher | 0.6597 | 0.4211 | 0.7040 | 0.7147 | 0.7382 | 0.4638 | 0.4783 | 0.4997 | 0.1071 |
| **Ours** | **0.6832** | **0.4595** | **0.7298** | **0.7409** | **0.7619** | **0.5012** | **0.5190** | **0.5407** | **0.0787** |

### Measured result (this repo, torch 2.11.0+cu128, RTX PRO 6000)

`Tea_epoch_best.pth`, 2026 masks, mask stats `mean 0.118 / std 0.266 / frac>0.5 0.117`:

| | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|
| Paper (Ours) | 0.6832 | 0.4595 | 0.7298 | 0.7409 | 0.7619 | 0.5012 | 0.5190 | 0.5407 | 0.0787 |
| Measured | 0.6973 | 0.4977 | 0.7647 | 0.7669 | 0.7775 | 0.5437 | 0.5504 | 0.5648 | 0.0817 |
| Δ | +0.014 | +0.038 | +0.035 | +0.026 | +0.016 | +0.043 | +0.031 | +0.024 | +0.003 ✗ |

Run health: both CSRDA rounds completed, `Loss_sup` 3.007 → 0.460, `Loss_con` 0.273 → 0.061,
CLS kept **2377 / 4040** target images (59%).

**We beat the reference on 8 of 9 metrics — read that as a warning, not a win.** A faithful
reproduction should land *near* the target, not above it; a systematic +0.03 on the F-measures
means this configuration is not equivalent to the authors'. Ranked suspects:

1. **The IMAGENET1K_V2 backbone (§2.4).** SegMaR trained from V1; V2 is a materially stronger
   checkpoint (~+1.5 pts ImageNet top-1). This is the one deviation that *adds* capability
   rather than removing it, and it is the cheapest to test — swap in
   `resnet50-0676ba61.pth` and retrain.
2. **More pseudo-labels.** CLS kept 59% here vs ~47% for SINet/SINet-v2, so round 2 saw
   noticeably more real data in its supervised branch.
3. **GT-supervised `fix_pred` (§2.3).** With both heads on GT, the model becomes a clean
   two-head architecture; the DM's fixation/edge prior may be less useful than a second full
   GT signal under domain shift.

Note this contradicts the prior expectation in §2.2/§2.3 that dropping magnification and DM
supervision would *depress* the numbers. It did not — so those two components matter less for
Ŝ2C than the backbone choice does.

Reference points from the rows already reproduced on this machine: SINet Ours landed within
±0.008 on every metric; SINet-v2 Source-Only within ±0.005 on eight of nine (MAE +0.011).

**Calibrate expectations for SegMaR.** Two of the deviations remove real capability — no
magnification (§2.2) and no Discriminative Mask supervision (§2.3) — so a shortfall is plausible
and would be *informative*, not a bug. Judge the run by the **Source-Only → Mean Teacher → Ours
ordering and the size of the CSRDA gain**, not solely by absolute agreement with Table 1. If you
want the full ladder for SegMaR, `--method source_only` and `--method mean_teacher` work exactly
as documented in [`SOURCE_ONLY.md`](SOURCE_ONLY.md) and [`MEAN_TEACHER.md`](MEAN_TEACHER.md).

---

## Related

- [`MEAN_TEACHER.md`](MEAN_TEACHER.md) · [`SOURCE_ONLY.md`](SOURCE_ONLY.md) — the other two ladder rows
- [`CHECKPOINT_LOADING_BUG.md`](CHECKPOINT_LOADING_BUG.md) — silent cross-device checkpoint load
- [`../Experiments/REPRODUCE_TABLE1.md`](../Experiments/REPRODUCE_TABLE1.md) — CSRDA mechanics and upstream quirks

# Source-Only baseline — Ŝ2C (HKU-IS → COD10K)

How to reproduce the **Source-Only** rows of Table 1, what the baseline actually measures,
and the one subtle trap that makes a "source-only" run secretly not source-only.

Paper: *Synthetic-to-Real Camouflaged Object Detection*, Luo, Lin & Lin, ACM MM '25.

---

## 0. TL;DR

Source-Only is the **lower bound** of the whole paper: train the COD model on synthetic
images with normal supervised learning, then test it on real images. No adaptation at all.

```
Source-Only   =  supervised training on synthetic HKU-IS,  nothing else
Mean Teacher  =  Source-Only  +  EMA teacher  +  L_CE consistency on real target
Ours (CSRDA)  =  Mean Teacher +  ES Loss      +  CLS / cycling
```

It exists to quantify the **domain gap**. From §1 and Fig. 2, even a strong model like
RISNet "performs poorly when trained solely on synthetic source domain images" — synthetic
images optimise for blending an object into a background, and in doing so produce
physically implausible scenes (a rabbit against sky, cats embedded in rock). Source-Only
measures how much that costs you.

One flag:

| Change | How |
|---|---|
| Drop the entire target-domain branch | `--method source_only` (forces `--iteration 1`) |

---

## 1. How Source-Only training works

### The mechanism

One network. One loss. No teacher, no target data.

```
 SOURCE (synthetic HKU-IS, labelled)
   x_s ──weak aug──►  MODEL  ──►  L_CE(prediction, y_s)  ──►  Adam step
                                                                  │
                                                        EMA ──────┘   (teacher = Polyak
 TARGET (real COD10K-train)                                            average only; it
   ✗  never loaded, never forwarded                                    never sees target)
```

The supervised loss is unchanged from every other row — it is whatever the architecture
uses natively:

| Network | `L_sup` |
|---|---|
| SINet | `BCEWithLogits(cam_sm, y_s) + BCEWithLogits(cam_im, y_s)` — the search and identification heads |
| SINet-v2 | `Σ structure_loss(preds[i], y_s)` over all 4 supervision heads (S_g, S_5, S_4, S_3) |

and the consistency term is simply zero:

```python
elif opt.method == 'source_only':
    return torch.zeros((), device=stu_out.device)      # no target term at all
```

### ⚠️ The trap: zeroing the loss is *not* enough

This is the part worth reading carefully, because getting it wrong inflates the baseline
and silently narrows the gap the paper is trying to measure.

The original training loop forwards target images through **both** networks on every step:

```python
with torch.no_grad():
    _, tea_out = ema_model(tar_weak_image)     # teacher forward
_, stu_out = model(tar_strong_image)            # student forward
```

Both networks are in `train()` mode. A `BatchNorm2d` layer in `train()` mode **updates its
`running_mean` / `running_var` from every batch it sees**, regardless of whether a loss is
attached. So even with `loss_con = 0` and no gradient path, those forward passes quietly
overwrite the BN statistics with **target-domain statistics**.

That is AdaBN — a real, published domain-adaptation method. A "source-only" model carrying
target-domain BN statistics has already adapted, and would score better than an honest
baseline. Since Source-Only is the number every improvement in the paper is measured
against, inflating it corrupts every delta in Tables 1–5.

**The fix**: skip the target branch entirely, not just its loss.

```python
if opt.method == 'source_only':
    batches = ((src_batch, (None, None)) for src_batch in source_loader)
else:
    batches = zip(source_loader, target_loader)
```

### Second correction: step count

The other rows are gated by `zip()`, which truncates to the shorter loader:

```
total_step = min(⌈4447/16⌉, ⌈4040/16⌉) = min(278, 253) = 253
```

With no target loader to gate it, Source-Only iterates the **full** source loader:

```python
total_step = (len(source_loader) if opt.method == 'source_only'
              else min(len(source_loader), len(target_loader)))
```

So SINet Source-Only runs **278 steps/epoch, not 253** — it sees all 4447 synthetic images
each epoch, which is what "train SINet on synthetic HKU-IS for 40 epochs" should mean. Left
gated, it would have seen only 4048 of 4447 per epoch.

> Both of these are changes *relative to the upstream loop*, and both apply only to
> `--method source_only`. The `ours` and `mean_teacher` paths keep their exact original
> model-call order and step count, so your reproduced numbers stay valid.

### ⚠️ Which checkpoint to evaluate — the STUDENT, not the teacher

**For Source-Only you must evaluate `Stu_*.pth`. `Tea_epoch_best.pth` is structurally
invalid for this row.** Measured, not theorised:

| Checkpoint | Sα | Fβw | MAE | BN buffers still at ImageNet init |
|---|---|---|---|---|
| `Tea_epoch_best.pth` | 0.4567 | **0.0533** | 0.1066 | **406 / 406** ✗ |
| `Stu_40.pth` | **0.6386** | **0.3826** | 0.1368 | 0 / 406 ✓ |

Here is the chain. `update_ema` copies **only `.parameters()`**, never buffers
([`Src/utils/tool.py:41-43`](../Src/utils/tool.py#L41-L43)):

```python
for ema_param, param in zip(ema_model.parameters(), model.parameters()):
    ema_param.data.mul_(alpha).add_(param.data, alpha=1 - alpha)
```

So BatchNorm `running_mean` / `running_var` are *never* EMA'd from the student. In the
upstream loop the teacher's BN statistics were kept alive only as an accidental side effect
of `ema_model(tar_weak_image)` executing in `train()` mode. Removing that forward pass — which
§1 above requires, because it leaks target statistics — leaves the teacher with **no path at
all** to update its BN buffers.

The result is a model whose convolution weights are fully trained (they moved 0.0258, the
same as the student's) sitting on top of **ImageNet-initialised BatchNorm statistics**. The
mismatch destroys the output: Fβw collapses to 0.0533.

Two things follow:

1. **Evaluate the student.** This also happens to be the more faithful reading of the paper,
   which defines the baseline as the model "trained using only source domain (synthetic
   images)" (Fig. 2) — there is no teacher in that description.
2. **Ignore the CAMO validation MAE for this row.** `val()` only ever validates `ema_model`,
   so `Tea_epoch_best.pth` and every `Epoch: N, MAE: …` line in a Source-Only log describe
   the broken teacher. A CAMO MAE around 0.20 is the signature; do not read it as "expected
   domain gap". There is no student-best selection in the codebase, so the student checkpoint
   is simply the last saved epoch.

---

## 2. Source-Only vs Mean Teacher vs Ours

| Module | **Source-Only** | Mean Teacher | Ours (CSRDA) |
|---|---|---|---|
| Supervised loss on synthetic source | ✅ | ✅ | ✅ |
| Target images loaded at all | ❌ **no** | ✅ | ✅ |
| EMA teacher (Eq. 4) | ⚪ runs, but never sees target | ✅ λ = 0.996 | ✅ λ = 0.996 |
| Weak / strong augmentation split | ⚪ weak only (source) | ✅ | ✅ |
| Consistency loss | ❌ none | ✅ `L_CE` (plain BCE) | ✅ `L_ES` |
| └ Edge alignment `L_EA` (Sobel, α = 0.9) | — | ❌ | ✅ |
| └ Saliency weighting `L_SW` (W = ŷ+δ) | — | ❌ | ✅ |
| Confident Label Selection (μ = 0.8, τ = 0.4) | — | ❌ | ✅ |
| Evolving real domain `D̂ₛ = Dₛ ∪ D_cl` | — | ❌ | ✅ |
| Cycling rounds | 1 | 1 | 2 |
| Steps / epoch (SINet) | **278** | 253 | 253 |

### The ablation ladder

| Paper setting | Consistency | CLS + cycle | Flags |
|---|---|---|---|
| **Source-Only** | none | no | `--method source_only` |
| Mean Teacher (`MT + L_CE`) | `L_CE` | no | `--method mean_teacher` |
| `MT + L_ES` | `L_ES` | no | `--method ours --iteration 1` |
| Ours (`MT + L_ES + CLS`) | `L_ES` | yes | `--method ours --iteration 2` |

Reading the ladder bottom-up tells you where the gains come from: target data at all
(Source-Only → MT), then better use of it (MT → +L_ES), then filtering it (+CLS).

---

## 3. Commands

### Train — both networks can run concurrently

No CLS, so nothing touches `Dataset/Source/HKU-IS_iteration2/`:

```bash
# SINet — Source-Only
uv run python MyTrain.py --network SINet --task S2C --method source_only \
  --gpu 0 --save_model ./Snapshot/SINet/S2C_SO/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinet_s2c_so.log

# SINet-v2 — Source-Only
uv run python MyTrain.py --network SINet-v2 --task S2C --method source_only \
  --gpu 1 --save_model ./Snapshot/SINet-v2/S2C_SO/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinetv2_s2c_so.log
```

`--target_root` is still required — the loader is constructed before the method branch even
though Source-Only never reads a batch from it. `--source_root` is omitted deliberately:
`MyTrain.py:159` hard-resets it inside the `--task S2C` block.

Source-Only is the **fastest** row: one forward+backward per step instead of three forwards,
so expect roughly 2–3× the throughput of Ours despite the extra 25 steps/epoch.

### Test — the STUDENT checkpoint (see §1)

```bash
uv run python MyTest.py --network SINet    --gpu 0 \
  --model_path ./Snapshot/SINet/S2C_SO/Stu_40.pth      --test_save ./Result/SINet/S2C_SO_stu
uv run python MyTest.py --network SINet-v2 --gpu 0 \
  --model_path ./Snapshot/SINet-v2/S2C_SO/Stu_100.pth  --test_save ./Result/SINet-v2/S2C_SO_stu
```

Do **not** use `Tea_epoch_best.pth` here — its BatchNorm buffers are never updated in a
Source-Only run, so it scores Fβw ≈ 0.05.

### Evaluate

```bash
cd Eval
uv run python MyEval.py --gt_root ../Dataset/Test --pred_root ../Result/SINet/S2C_SO_stu    --txt_name SINet/S2C_SO_stu
uv run python MyEval.py --gt_root ../Dataset/Test --pred_root ../Result/SINet-v2/S2C_SO_stu --txt_name SINet-v2/S2C_SO_stu
cd ..
cat Eval/Eval/eval_txt/SINet*/S2C_SO_stu/_eval.txt
```

---

## 4. Targets

**Table 1 — Ŝ2C**

| Model | Setting | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|---|
| SINet | **Source-Only** | **0.6418** | **0.3707** | **0.7323** | **0.6570** | **0.7211** | **0.4653** | **0.4284** | **0.4718** | **0.0905** |
| SINet | Mean Teacher | 0.6984 | 0.4165 | 0.7092 | 0.7177 | 0.7805 | 0.4888 | 0.5106 | 0.5598 | 0.0915 |
| SINet | Ours | 0.7136 | 0.4814 | 0.7676 | 0.7443 | 0.7950 | 0.5548 | 0.5572 | 0.5960 | 0.0717 |
| SINet-v2 | **Source-Only** | **0.6466** | **0.4121** | **0.7332** | **0.6986** | **0.7035** | **0.4736** | **0.4640** | **0.4697** | **0.0976** |
| SINet-v2 | Mean Teacher | 0.6485 | 0.4213 | 0.7143 | 0.7148 | 0.7347 | 0.4633 | 0.4709 | 0.4898 | 0.1115 |
| SINet-v2 | Ours | 0.6845 | 0.4764 | 0.7707 | 0.7571 | 0.7643 | 0.5341 | 0.5319 | 0.5380 | 0.0787 |

The gap Source-Only → Ours is what the paper is selling: SINet `Fβw` 0.3707 → 0.4814
(**+11.1 points**, quoted as "11.1%" in §4.2) and `Fmx` 0.4718 → 0.5960 (+12.5).

### Measured reproduction (this repo, torch 2.11.0+cu128, 2× RTX PRO 6000)

**SINet-v2 — near-exact:**

| | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|
| Paper | 0.6466 | 0.4121 | 0.7332 | 0.6986 | 0.7035 | 0.4736 | 0.4640 | 0.4697 | 0.0976 |
| `Stu_100.pth` | 0.6450 | 0.4114 | 0.7288 | 0.6962 | 0.7060 | 0.4705 | 0.4643 | 0.4726 | 0.1090 |
| Δ | −0.002 | −0.001 | −0.004 | −0.002 | +0.003 | −0.003 | +0.000 | +0.003 | **+0.011** |

**SINet — good on most metrics, MAE runs high:**

| | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|
| Paper | 0.6418 | 0.3707 | 0.7323 | 0.6570 | 0.7211 | 0.4653 | 0.4284 | 0.4718 | 0.0905 |
| `Stu_40.pth` (last epoch) | 0.6386 | 0.3826 | 0.6784 | 0.6573 | 0.6793 | 0.4362 | 0.4381 | 0.4566 | **0.1368** |
| `Stu_30.pth` (diagnostic) | 0.6472 | 0.3874 | 0.6841 | 0.6668 | 0.6930 | 0.4433 | 0.4443 | 0.4660 | **0.1252** |

`Stu_40.pth` is the principled choice — the last epoch, no selection. `Stu_30.pth` is listed
only as a diagnostic; picking whichever epoch best matches the paper would be cherry-picking.

**On SINet's MAE gap (0.137 vs 0.091).** Sα, Fβw, Emn and Fmn all land within ~0.017, so the
model is not broken — the predictions are just less well calibrated in magnitude, which is
exactly what MAE punishes. Two plausible contributors, in order of likelihood:

1. **Loss shape.** SINet's `L_sup` is plain `BCEWithLogits` on two heads. SINet-v2's
   `structure_loss` adds a weighted-IoU term, which constrains predicted *area* and so
   calibrates magnitude. That fits the pattern: SINet-v2's MAE is off by 0.011, SINet's by
   0.046. Note the paper has SINet's MAE *better* than SINet-v2's (0.0905 < 0.0976), while
   ours is the reverse — so this is SINet-specific, not a global offset.
2. **The compounding LR bug.** `adjust_lr` decays to ~0 by epoch ~33, so SINet never gets a
   real 1e-5 fine-tuning phase — the stage that would sharpen calibration. That `Stu_30`
   beats `Stu_40` on both Sα and MAE is consistent with this.

**Do not "fix" the LR schedule to close this gap.** The same buggy schedule produced the
reproduced Mean Teacher and Ours numbers, so changing it for Source-Only alone would make
every delta in the ladder meaningless. If you want the corrected schedule, re-run all four
rows with it and report them as a separate set.

---

## 5. What to look out for

### Source-Only should *beat* Mean Teacher on two metrics

Counter-intuitive but documented in §4.2 — unfiltered pseudo-labels inject noise, so Mean
Teacher **regresses** on MAE and `E_φ^ad`:

| | MAE (lower better) | E_φ^ad (higher better) |
|---|---|---|
| SINet: Source-Only → MT | 0.0905 → 0.0915 | 0.7323 → 0.7092 |
| SINet-v2: Source-Only → MT | 0.0976 → 0.1115 | 0.7332 → 0.7143 |

So a Source-Only MAE that comes out *better* than your Mean Teacher MAE is correct, not a
mix-up of directories. On every other metric Source-Only should be the worst of the three.

### Verify the target domain really was untouched

The whole point of the two corrections in §1. Two checks:

```bash
# 1. Loss_con must be exactly 0.0000 on every logged line
grep -oE "Loss_con: [0-9.]+" train_sinet_s2c_so.log | sort -u
#    -> must print only "Loss_con: 0.0000"

# 2. Step count must be 278 for SINet (not 253) — proof the target loader isn't gating
grep -oE "Global Step: [0-9]+/[0-9]+" train_sinet_s2c_so.log | head -1
#    -> Global Step: 0000/0278
```

If you see `/0253`, the target loader is still gating and you are running an older
`MyTrain.py`.

### Don't invalidate the ladder

- **The compounding `adjust_lr` bug must stay** (`Src/utils/tool.py` does `lr *= 0.1` every
  epoch past `decay_epoch`, decaying to ~0). It applied to your Ours and Mean Teacher runs,
  so it must apply here. Fix it for all rows or none.
- **Fresh, empty `--save_model` directory** (`S2C_SO/`). `Tea_epoch_best.pth` is overwritten
  in place and a stray checkpoint from another row is indistinguishable.
- **Keep `--task S2C`** so λ/μ/τ/α/β/δ stay at the paper's Ŝ2C values. μ, τ, α, β, δ have no
  effect for this row, but the flag also sets `source_root`.
- **Report which checkpoint you used** (`Tea_epoch_best.pth` vs `Stu_*.pth`) — see §1.

### Logs and runtime

- `Loss_con: 0.0000` throughout; only `Loss_sup` moves. `Loss_all == Loss_sup`.
- Validation (CAMO MAE → `Tea_epoch_best.pth`) still starts only after epoch 20, so a run
  killed before epoch 21 leaves no best checkpoint.
- SINet: 39 epochs × 278 steps. SINet-v2 self-overrides to 99 epochs × ⌈4447/32⌉ = 139 steps.
  (Confirmed in the logs: `0000/0278` and `0000/0139` respectively.)
- Expect a **strong training fit and weak test numbers** — that *is* the domain gap. A low
  `Loss_sup` with Sα ≈ 0.64 on COD10K is the expected, correct outcome, not overfitting to
  be debugged.

### Sanity-check the masks before trusting metrics

```bash
uv run python -c "
import numpy as np, cv2, glob
a=[cv2.imread(f,0).astype(np.float32)/255. for f in sorted(glob.glob('Result/SINet/S2C_SO/*.png'))[:200]]
print('mean %.4f  std %.4f  frac>0.5 %.4f' % (np.mean([x.mean() for x in a]),
      np.mean([x.std() for x in a]), np.mean([(x>0.5).mean() for x in a])))"
```

Healthy ≈ `mean 0.15–0.20, std 0.26–0.34, frac>0.5 0.15–0.21` (GT is 0.180 / 0.337 / 0.180).
Source-Only masks legitimately look blurrier and noisier than Ours — Fig. 2 and Fig. 5
(column 3) show exactly that, e.g. branch textures misread as camouflaged objects. But a
`mean ≈ 0.59, std ≈ 0.14` signature is not "blurry", it is a checkpoint that failed to load
— see [CHECKPOINT_LOADING_BUG.md](CHECKPOINT_LOADING_BUG.md).

---

## Related

- [`MEAN_TEACHER.md`](MEAN_TEACHER.md) — the next rung up the ladder
- [`CHECKPOINT_LOADING_BUG.md`](CHECKPOINT_LOADING_BUG.md) — the silent cross-device load failure
- [`../Experiments/REPRODUCE_TABLE1.md`](../Experiments/REPRODUCE_TABLE1.md) — full Ours reproduction guide and upstream quirks

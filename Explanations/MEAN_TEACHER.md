# Mean Teacher baseline — Ŝ2C (HKU-IS → COD10K)

How to reproduce the **Mean Teacher** rows of Table 1, what they actually are, and how
they differ from **Ours (CSRDA)**.

Paper: *Synthetic-to-Real Camouflaged Object Detection*, Luo, Lin & Lin, ACM MM '25.

---

## 0. TL;DR

Mean Teacher is **CSRDA with both contributions removed**:

```
Ours (CSRDA)  =  Mean Teacher  +  ES Loss  +  CLS/cycling
```

Concretely, two changes to the training run:

| # | Change | How |
|---|---|---|
| 1 | Consistency loss `L_ES` → plain `L_CE` (unweighted BCE) | `--method mean_teacher` |
| 2 | No CLS, no second cycle | `--iteration 1` (forced automatically) |

Everything else is untouched: same EMA teacher (λ = 0.996), same weak/strong
augmentation, same optimizer, same epochs, same teacher-only evaluation.

> **The consistency loss is BCE, not MSE.** Generic Mean Teacher (Tarvainen & Valpola)
> uses MSE, but *this paper* does not. Table 5 labels the baseline `MT + L_CE`, and its
> numbers are byte-identical to Table 1's "Mean Teacher" row — so `L_CE`, the binary
> cross-entropy of Eq. 5, is the consistency term. Implemented as
> `F.binary_cross_entropy(stu_out, tea_out)`.

---

## 1. How Mean Teacher training works

### The mechanism

Two copies of the same network. The **student** is trained by gradient descent; the
**teacher** is never trained — it is an exponential moving average of the student
(Eq. 4):

```
f_ema  ←  λ · f_ema  +  (1 − λ) · f            λ = 0.996 for Ŝ2C
```

Each training step consumes one source batch and one target batch simultaneously:

```
 SOURCE (synthetic HKU-IS, labelled)
   x_s ──weak aug──►  STUDENT  ──►  L_CE(prediction, y_s)          supervised
                                                                    │
 TARGET (real COD10K-train, unlabelled)                             │
   x_t ──weak aug────►  TEACHER  ──►  ŷ_t   (no gradient)           │
   x_t ──strong aug──►  STUDENT  ──►  p_t                           │
                              └──►  L_consistency(p_t, ŷ_t)  ──────┤
                                                                    ▼
                                        total loss  =  L_sup  +  L_con
                                        Adam step on the student
                                        EMA update of the teacher
```

The teacher sees the **easy** view and produces the pseudo-label; the student sees the
**hard** view and must agree. Because the teacher is a temporal ensemble of past
students, its pseudo-labels are more stable than any single student's — that is the whole
idea, and it is what lets unlabelled real images contribute a training signal.

### What Mean Teacher changes relative to Ours

Only the consistency term. In Ours it is the **ES Loss** (Eq. 6):

```
L_ES  =  α · L_EA  +  β · L_SW                    α = 0.9,  β = 0.3

L_EA  =  ‖ ∇ f(Ã(x_t))  −  ∇ f_ema(A(x_t)) ‖₁     Sobel edge alignment      (Eq. 7)
L_SW  =  W · BCE( f(Ã(x_t)), ŷ_t ),   W = ŷ_t + δ  saliency weighting, δ = 0.5 (Eq. 8)
```

In Mean Teacher it collapses to plain unweighted cross-entropy:

```
L_CE  =  BCE( f(Ã(x_t)), ŷ_t )
```

That is exactly `L_ES` with `α = 0` (no edge term) and `W = 1` (no saliency weighting) —
verified numerically against this repo's `ESLoss`:

```
F.binary_cross_entropy(stu, tea)        = 1.001068
ESLoss(a=0, b=1, use_weighted_bce=False) = 1.001068   ← identical
ESLoss(a=0.9, b=0.3, weighted)           = 0.920524   ← 'ours'
```

### Code changes made for this

`MyTrain.py` gained a `--method` flag. The `ours` path is **bit-identical** to before —
the flag defaults to `ours` and only routes the consistency term:

```python
def consistency_loss(stu_out, tea_out, opt):
    if opt.method == 'ours':
        return ES_Loss(stu_out, tea_out)                       # L_ES  (Eq. 6)
    elif opt.method == 'mean_teacher':
        return F.binary_cross_entropy(stu_out, tea_out)         # L_CE
    elif opt.method == 'source_only':
        return torch.zeros((), device=stu_out.device)           # no target term
```

Plus a guard, because CLS and the cycle are definitionally part of Ours:

```python
if opt.method != 'ours' and opt.iteration != 1:
    opt.iteration = 1        # prints an [Info] line when it overrides
```

---

## 2. Mean Teacher vs Ours (CSRDA), module by module

| Module | Source-Only | **Mean Teacher** | Ours (CSRDA) |
|---|---|---|---|
| Supervised loss on synthetic source | ✅ | ✅ | ✅ |
| EMA teacher, λ = 0.996 (Eq. 4) | — | ✅ | ✅ |
| Weak / strong augmentation split | — | ✅ | ✅ |
| Consistency loss on real target | ❌ none | ✅ `L_CE` (plain BCE) | ✅ `L_ES` |
| └ Edge alignment `L_EA` (Sobel, α=0.9) | — | ❌ | ✅ |
| └ Saliency weighting `L_SW` (W = ŷ+δ) | — | ❌ | ✅ |
| Confident Label Selection (μ=0.8, τ=0.4) | — | ❌ | ✅ |
| Evolving real domain `D̂ₛ = Dₛ ∪ D_cl` | — | ❌ | ✅ |
| Cycling rounds | 1 | 1 | 2 |
| Evaluated with | teacher | teacher | teacher |

### What each added module buys you

**ES Loss** attacks the *quality of the agreement signal*. Plain BCE treats every pixel
equally, so the student is rewarded just as much for matching the teacher on flat
background as on the object's boundary — and camouflage is precisely a boundary problem.
`L_EA` compares Sobel edge maps, forcing contour agreement; `L_SW` upweights pixels the
teacher already believes are object (`W = ŷ_t + δ`), so background noise pulls less. The
paper's Fig. 5 observation is that Mean Teacher "suffers from significant edge blurring" —
that is the missing `L_EA`.

**CLS** attacks the *reliability of the pseudo-labels*. Mean Teacher trusts every teacher
output. CLS keeps only images where student and teacher already agree (Eq. 9):

```
D_cl = { x  |  L_ES( f(x), f_ema(x) )  ≤  μ · E_x[ L_ES( f(x), f_ema(x) ) ] }     μ = 0.8
```

a *relative*, self-calibrating threshold — then zeroes sub-τ regions and drops images
whose peak confidence is below τ = 0.4 (Eq. 10). Survivors are folded into the source set
(Eq. 11) and a **fresh** student/teacher pair is trained on it. In this repo's Ŝ2C run that
kept **1875 of 4040** target images. The point: after cycling, real-domain samples are in
the *supervised* branch, so `L_sup` itself pulls toward the target domain instead of only
`L_con` doing it.

### The ablation ladder — all four rows from one script

Table 5 is the ladder, and every rung is reachable with flags:

| Paper setting | Consistency | CLS + cycle | Flags |
|---|---|---|---|
| Source-Only | none | no | `--method source_only` |
| **Mean Teacher** (= `MT + L_CE`) | `L_CE` | no | `--method mean_teacher` |
| `MT + L_ES` | `L_ES` | no | `--method ours --iteration 1` |
| **Ours** (= `MT + L_ES + CLS`) | `L_ES` | yes | `--method ours --iteration 2` |

`MT + L_ES` is a genuinely useful sanity rung: it isolates ES Loss from CLS, and it costs
one single-round training run.

---

## 3. Commands

### Train

`--iteration 1` means CLS never runs, so nothing touches
`Dataset/Source/HKU-IS_iteration2/` — these two **can run concurrently**:

```bash
# SINet — Mean Teacher
uv run python MyTrain.py --network SINet --task S2C --method mean_teacher \
  --gpu 0 --iteration 1 --save_model ./Snapshot/SINet/S2C_MT/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinet_s2c_mt.log

# SINet-v2 — Mean Teacher
uv run python MyTrain.py --network SINet-v2 --task S2C --method mean_teacher \
  --gpu 1 --iteration 1 --save_model ./Snapshot/SINet-v2/S2C_MT/ \
  --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ \
  2>&1 | tee train_sinetv2_s2c_mt.log
```

`--source_root` is deliberately omitted — `MyTrain.py:159` hard-resets it inside the
`--task S2C` block, so passing it does nothing.

### Test — teacher only

The paper is explicit: *"During evaluation, only the teacher model is reserved for
inference."* Use `Tea_epoch_best.pth`.

```bash
uv run python MyTest.py --network SINet    --gpu 0 \
  --model_path ./Snapshot/SINet/S2C_MT/Tea_epoch_best.pth    --test_save ./Result/SINet/S2C_MT

uv run python MyTest.py --network SINet-v2 --gpu 0 \
  --model_path ./Snapshot/SINet-v2/S2C_MT/Tea_epoch_best.pth --test_save ./Result/SINet-v2/S2C_MT
```

### Evaluate

```bash
cd Eval
uv run python MyEval.py --gt_root ../Dataset/Test --pred_root ../Result/SINet/S2C_MT    --txt_name SINet/S2C_MT
uv run python MyEval.py --gt_root ../Dataset/Test --pred_root ../Result/SINet-v2/S2C_MT --txt_name SINet-v2/S2C_MT
cd ..
cat Eval/Eval/eval_txt/SINet*/S2C_MT/_eval.txt
```

### Optional extra rungs

```bash
# Source-Only
uv run python MyTrain.py --network SINet --task S2C --method source_only \
  --gpu 0 --save_model ./Snapshot/SINet/S2C_SO/ --val_root ./Dataset/Val/CAMO/

# MT + L_ES (ES Loss, no CLS)
uv run python MyTrain.py --network SINet --task S2C --method ours --iteration 1 \
  --gpu 0 --save_model ./Snapshot/SINet/S2C_MT_ES/ --val_root ./Dataset/Val/CAMO/
```

---

## 4. Targets

**Table 1 — Ŝ2C, full metric set**

| Model | Setting | Sα ↑ | Fβw ↑ | Ead ↑ | Emn ↑ | Emx ↑ | Fad ↑ | Fmn ↑ | Fmx ↑ | M ↓ |
|---|---|---|---|---|---|---|---|---|---|---|
| SINet | Source-Only | 0.6418 | 0.3707 | 0.7323 | 0.6570 | 0.7211 | 0.4653 | 0.4284 | 0.4718 | 0.0905 |
| SINet | **Mean Teacher** | **0.6984** | **0.4165** | **0.7092** | **0.7177** | **0.7805** | **0.4888** | **0.5106** | **0.5598** | **0.0915** |
| SINet | Ours | 0.7136 | 0.4814 | 0.7676 | 0.7443 | 0.7950 | 0.5548 | 0.5572 | 0.5960 | 0.0717 |
| SINet-v2 | Source-Only | 0.6466 | 0.4121 | 0.7332 | 0.6986 | 0.7035 | 0.4736 | 0.4640 | 0.4697 | 0.0976 |
| SINet-v2 | **Mean Teacher** | **0.6485** | **0.4213** | **0.7143** | **0.7148** | **0.7347** | **0.4633** | **0.4709** | **0.4898** | **0.1115** |
| SINet-v2 | Ours | 0.6845 | 0.4764 | 0.7707 | 0.7571 | 0.7643 | 0.5341 | 0.5319 | 0.5380 | 0.0787 |

**Table 5 — the ladder** (reduced metric set)

| Model | Setting | Sα ↑ | Fβw ↑ | Emn ↑ | Fmn ↑ | M ↓ |
|---|---|---|---|---|---|---|
| SINet | MT + L_CE | 0.6984 | 0.4165 | 0.7177 | 0.5106 | 0.0915 |
| SINet | MT + L_ES | 0.7020 | 0.4531 | 0.7362 | 0.5284 | 0.0900 |
| SINet | MT + L_ES + CLS | 0.7136 | 0.4814 | 0.7433 | 0.5572 | 0.0717 |
| SINet-v2 | MT + L_CE | 0.6485 | 0.4213 | 0.7148 | 0.4709 | 0.1115 |
| SINet-v2 | MT + L_ES | 0.6624 | 0.4426 | 0.7379 | 0.4928 | 0.0974 |
| SINet-v2 | MT + L_ES + CLS | 0.6845 | 0.4764 | 0.7571 | 0.5319 | 0.0787 |

> Minor paper inconsistency: SINet Ours `Emn` is 0.7443 in Table 1 but 0.7433 in Table 5.
> Both round to 0.744; don't chase the third decimal.

---

## 5. What to look out for

### ⚠️ Mean Teacher is *supposed* to be worse than Source-Only on two metrics

This is the single most likely thing to make you think you've broken something. From §4.2:

> *"since this method does not filter the pseudo labels generated by the teacher model, a
> performance drop is observed on certain metrics… both SINet and SINet-v2 under the Mean
> Teacher method show a certain decrease in MAE and E_φ^ad compared to the Source-Only
> baseline, with the E_φ^ad metric averaging a 2% drop."*

| | MAE (lower better) | E_φ^ad (higher better) |
|---|---|---|
| SINet: Source-Only → MT | 0.0905 → **0.0915** ✗ worse | 0.7323 → **0.7092** ✗ worse |
| SINet-v2: Source-Only → MT | 0.0976 → **0.1115** ✗ worse | 0.7332 → **0.7143** ✗ worse |

Unfiltered pseudo-labels inject noise. That regression **is the result** — it is the
motivation for CLS. Sα, Fβw, Emn, Emx, Fmn and Fmx should all still *improve* over
Source-Only. If MAE improves too, suspect your config, not your luck.

Note SINet-v2's MT gain is tiny (Sα 0.6466 → 0.6485, +0.002). Don't expect a dramatic
jump there.

### Don't accidentally invalidate the comparison

- **Never patch `adjust_lr` for one row only.** `Src/utils/tool.py` compounds the LR decay
  (`lr *= 0.1` *every* epoch past `decay_epoch`, so it dies to ~0). It's an upstream bug,
  but it applied to your reproduced *Ours* run, so it must apply to Mean Teacher too. Fix
  it for all rows or none.
- **Use a fresh, empty `--save_model` directory per method.** `Tea_epoch_best.pth` is
  overwritten in place; a leftover checkpoint from another row is indistinguishable.
- **Keep λ = 0.996 and the weak/strong augmentation.** Both belong to Mean Teacher, not to
  the paper's contributions. Changing them makes it a different baseline.
- **Don't pass `--a/--b/--c`** — the `--task S2C` block overwrites them after argparse.
  They are irrelevant for `mean_teacher` anyway.
- μ and τ are CLS-only, so they have no effect here.

### Runtime and logs

- `Loss_con` will read **higher than in your Ours run**: the BCE term carries weight 1.0
  instead of β = 0.3, and there's no edge term diluting it. That is expected — it does not
  mean the consistency signal is stronger in a useful way.
- BCE between two soft maps has a **non-zero floor** — `BCE(p, p) = H(p)`, the teacher's
  own entropy — so `Loss_con` bottoms out at the teacher's uncertainty rather than 0, and
  falls only as the teacher sharpens. Don't read a plateau as a stall.
- Steps/epoch is unchanged: `min(⌈4447/16⌉, ⌈4040/16⌉) = 253` for SINet (`0253` in the log).
- Validation (CAMO MAE → `Tea_epoch_best.pth`) still starts only after epoch 20.
- Because `total_step = min(len(source), len(target))`, a **`source_only`** run still sees
  only 253×16 = 4048 of 4447 source images per epoch — the target loader gates it even
  though its loss is zero. Shuffling means coverage evens out across epochs; it's a
  faithful-to-the-repo quirk, not a bug to fix mid-comparison.

### Before trusting any metric

Sanity-check the masks — this catches a dead model in seconds:

```bash
uv run python -c "
import numpy as np, cv2, glob
a=[cv2.imread(f,0).astype(np.float32)/255. for f in sorted(glob.glob('Result/SINet/S2C_MT/*.png'))[:200]]
print('mean %.4f  std %.4f  frac>0.5 %.4f' % (np.mean([x.mean() for x in a]),
      np.mean([x.std() for x in a]), np.mean([(x>0.5).mean() for x in a])))"
```

Healthy ≈ `mean 0.15–0.19, std 0.28–0.34, frac>0.5 0.15–0.20` (GT is 0.180 / 0.337 / 0.180).
A `mean ≈ 0.59, std ≈ 0.14` signature means the checkpoint didn't load — see
[CHECKPOINT_LOADING_BUG.md](CHECKPOINT_LOADING_BUG.md). `MyTest.py` now asserts against
this, but check anyway.

---

## Related

- [`CHECKPOINT_LOADING_BUG.md`](CHECKPOINT_LOADING_BUG.md) — the silent cross-device load failure
- [`Experiments/REPRODUCE_TABLE1.md`](Experiments/REPRODUCE_TABLE1.md) — full Ours reproduction guide and upstream quirks
- [`preflight.py`](preflight.py) — pre-run environment/data checks

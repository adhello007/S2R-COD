# The silent checkpoint-load bug: why SINet-v2 scored 0.28 instead of 0.68

**Date:** 11 Aug 2026 · **Affected:** `MyTest.py` (and latently `CLS.py`) · **Status:** fixed

---

## TL;DR

SINet-v2's Ŝ2C evaluation returned **Sα 0.2816 / MAE 0.594** against a paper target of
**Sα 0.6845 / MAE 0.0787**.

The training was completely fine. `MyTest.py` **silently evaluated a randomly initialised
network**, because it loaded a checkpoint whose tensors lived on `cuda:1` into a model
living on `cuda:0`. PyTorch reported `<All keys matched successfully>` and copied
essentially nothing.

The trigger was that SINet-v2 was trained with `--gpu 1` while SINet was trained with
`--gpu 0`. Nothing about the two architectures mattered.

---

## Part 1 — The concept

If you already know what a `state_dict` is, skip to [Part 2](#part-2--what-actually-went-wrong).

### A model is two separate things

A PyTorch model is **code** (the `nn.Module` class: layer definitions, `forward()`) and
**numbers** (weights, biases, BatchNorm running statistics). Only the numbers are saved.

```python
torch.save(model.state_dict(), 'Tea_100.pth')
```

A `state_dict` is just an ordered dictionary: `{'resnet.conv1.0.weight': tensor(...), ...}`.
SINet-v2's has **880 entries**. To restore it you rebuild the code, then pour the numbers
back in:

```python
model = Network().cuda()                       # code, freshly initialised
model.load_state_dict(torch.load('Tea_100.pth'))   # numbers
```

If step 2 fails, step 1 leaves you with a **fully functional model made of random
numbers**. It runs, it produces 2026 output masks, it never errors — the masks are just
noise. That is the whole bug.

### Tensors remember which GPU they were on

This is the part that bites. Every CUDA tensor carries a device: `cuda:0`, `cuda:1`, …
`torch.save` serialises that device *label* along with the numbers.

```python
torch.cuda.set_device(1)
w = torch.randn(3).cuda()      # w.device == cuda:1
torch.save({'w': w}, 'ck.pth') # the file records "this lived on cuda:1"
```

So a checkpoint is not device-neutral. Reload it and PyTorch tries to put the tensors
back where it found them:

```python
sd = torch.load('ck.pth')      # -> sd['w'].device == cuda:1, always
```

`map_location` is how you override that:

```python
sd = torch.load('ck.pth', map_location='cpu')       # -> cpu
sd = torch.load('ck.pth', map_location='cuda:0')    # -> cuda:0
```

### Where `MyTrain.py` stamps the device

[`MyTrain.py:161`](MyTrain.py#L161):

```python
torch.cuda.set_device(opt.gpu)      # <-- this is what gets stamped into every checkpoint
```

Train with `--gpu 1` and every `.pth` in `Snapshot/` is labelled `cuda:1`. Train with
`--gpu 0` and they are labelled `cuda:0`. Same file otherwise — same 880 keys, same
shapes, byte-for-byte identical numbers. Only the label differs.

---

## Part 2 — What actually went wrong

`MyTest.py` did two things, each individually reasonable:

```python
model = Network().cuda()                            # no set_device -> lands on cuda:0
model.load_state_dict(torch.load(opt.model_path))   # no map_location -> lands on cuda:1
```

1. It never called `torch.cuda.set_device()`, and it had **no `--gpu` argument at all**, so
   the model was always built on the default device, `cuda:0`.
2. It called `torch.load()` with no `map_location`, so the checkpoint went to whichever
   device it was saved from.

For a checkpoint trained on GPU 1, those are **two different devices**. And on
torch 2.11.0+cu128, a cross-device `load_state_dict` **reports success and does not
copy**:

```python
lin = torch.nn.Linear(4, 4).cuda()                     # cuda:0
tgt = {k: torch.ones_like(v, device='cuda:1') for k, v in lin.state_dict().items()}
lin.load_state_dict(tgt)        # -> <All keys matched successfully>
(lin.weight == 1).all()         # -> False        <-- silent no-op
```

No exception. No warning. A success message. This is the entire failure.

Measured on the real checkpoint — only 159 of 880 tensors ended up matching, and those are
coincidental (BatchNorm counters and zero-initialised buffers), not real copies:

```
copied 159/880
  matched: {'weight/bias': 53, 'running_mean': 53, 'num_batches_tracked': 53}

sample tensor 'resnet.conv1.0.weight'
  checkpoint mean = -0.000880
  model mean      = -0.000695     <- still at its random-init value
```

The model also stayed on `cuda:0` — nothing moved, the copy simply had no effect.

### Why the output looked the way it did

A randomly initialised SINet-v2 emits an almost constant logit everywhere. Then
[`MyTest.py:57`](MyTest.py#L57) min-max normalises each mask:

```python
cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
```

Normalisation is exactly the wrong thing to do to a near-constant map: it **stretches
numerical noise to fill the full 0–1 range**, turning a flat blob into a confident-looking
garbage mask. That is why the failure produced plausible-looking greyscale PNGs instead of
obviously blank ones — and why nothing downstream complained.

---

## Part 3 — Why SINet was fine and SINet-v2 was not

Luck. Nothing else. From `Experiments/10_Aug/*/run_commands.txt`:

| | trained with | checkpoint stamped | `MyTest.py` model on | same device? | result |
|---|---|---|---|---|---|
| **SINet** | `--gpu 0` | `cuda:0` | `cuda:0` | ✅ yes | load works → **Sα 0.7172** (paper 0.7136) |
| **SINet-v2** | `--gpu 1` | `cuda:1` | `cuda:0` | ❌ no | silent no-op → **Sα 0.2816** (paper 0.6845) |

`MyTest.py` was equally broken for both. SINet just happened to be trained on GPU 0, which
coincides with the device `MyTest.py` implicitly assumes.

Two consequences worth internalising:

- Had SINet been trained with `--gpu 1`, it would have failed **identically**.
- Retraining SINet-v2 on `--gpu 0` would have made the problem **disappear with no code
  change** — which is the worst possible outcome, because it would have "confirmed" a
  nonexistent training bug and hidden the real one.

### How we know the training was fine

Every check pointed the same way once the checkpoint was loaded correctly:

| Check | Result |
|---|---|
| All 5 checkpoints, loaded with `map_location` | `sig[3]` mean 0.148, std 0.348 vs **GT mean 0.145** — healthy |
| `loss_sup` recomputed on round-2 source | **0.9617** vs **0.9485** logged at r2 ep99 — matches |
| Both CSRDA rounds | converged normally, `loss_sup` plateau 0.85–0.95, `loss_con` ≈ 0.04 |
| CLS pseudo-labels | 1875 kept, mean 0.078, frac>0.5 0.084 — sparse and sensible |
| SINet pseudo-labels (control) | 1906 kept, mean 0.079 — essentially identical |

And the bug reproduces exactly, which is what closed the case:

| load path | tensors copied | mask mean | std | frac>0.5 | MAE |
|---|---|---|---|---|---|
| `torch.load(p)` — the old `MyTest.py` | 159 / 880 | 0.599 | 0.175 | 0.721 | **0.604** |
| `torch.load(p, map_location='cpu')` | 880 / 880 | 0.112 | 0.268 | 0.111 | 0.130 |
| masks actually on disk from the bad run | — | 0.590 | 0.143 | 0.728 | **0.594** |

Row 1 reproduces row 3. The reported MAE 0.594 was the signature of a random network.

> **A note on how this was diagnosed.** The first two diagnostic scripts made the *same*
> `map_location` mistake and appeared to show a genuine training collapse — every
> checkpoint scoring identically to random init. The lesson generalises: when a
> measurement says a trained model is indistinguishable from a random one, suspect the
> measurement before the training.

---

## Part 4 — The fix

### `MyTest.py`

Load to CPU, then let `load_state_dict` copy across — a CPU→CUDA copy works correctly —
and **assert that it actually happened**:

```python
parser.add_argument('--gpu', type=int, default=0, help='choose which gpu you use')
opt = parser.parse_args()

torch.cuda.set_device(opt.gpu)
...
state_dict = torch.load(opt.model_path, map_location='cpu')
model.load_state_dict(state_dict)
loaded = model.state_dict()
copied = sum(torch.equal(v.to(loaded[k].device), loaded[k]) for k, v in state_dict.items())
assert copied == len(state_dict), (
    f'checkpoint load copied only {copied}/{len(state_dict)} tensors from '
    f'{opt.model_path} -- refusing to run inference on partially loaded weights')
```

`map_location` alone would have been enough here, but the assert is the part that matters:
a failure mode that reports success needs a check that does not trust the report.

Verified against the real checkpoint:

```
159/880 copied   torch.load(p)                       <- old behaviour
880/880 copied   torch.load(p, map_location='cpu')
880/880 copied   torch.load(p, map_location='cuda:0')
```

### `CLS.py`

Same pattern at [`CLS.py:53`](CLS.py#L53), [`:60`](CLS.py#L60), [`:63`](CLS.py#L63) — all
three now pass `map_location='cpu'`.

These had **not** failed yet, purely because `cls()` is called from `MyTrain.py`, which
calls `set_device(opt.gpu)` first, so model and checkpoint shared a device. But it was one
step from disaster: run CLS against a checkpoint from another GPU and it would generate the
entire round-2 pseudo-label set from a random network — sparse-looking, plausible files,
silently poisoning round 2.

---

## Part 5 — Rules to avoid this class of bug

1. **Always pass `map_location` to `torch.load`.** There is no case where relying on the
   stamped device is what you want. `map_location='cpu'` is the safe default.
2. **Never trust `<All keys matched successfully>`.** It validates key *names* and
   *shapes* — it does not promise the values were copied. Verify with an equality count,
   or check one known tensor's mean.
3. **Give every script a `--gpu` flag** and call `torch.cuda.set_device()`. Implicit
   `cuda:0` is a hidden coupling between training and inference.
4. **Sanity-check outputs before metrics.** `mean`, `std`, `frac>0.5` on a handful of
   predicted masks against GT catches this in seconds. Metrics alone tell you *something*
   is wrong, not *what*.
5. **Beware min-max normalisation on near-constant maps** — it manufactures structure out
   of noise and disguises a dead model as a working one.
6. **When a trained model measures identical to random init, suspect your harness first.**
   Training logs and checkpoints are independent evidence; cross-check them.

---

## Related

- [`Experiments/10_Aug/SINETV2/run_commands.txt`](Experiments/10_Aug/SINETV2/run_commands.txt) — corrected commands
- [`Experiments/REPRODUCE_TABLE1.md`](Experiments/REPRODUCE_TABLE1.md) — full reproduction guide and other upstream quirks
- [`preflight.py`](preflight.py) — pre-run checks
- Broken masks preserved at `Result/SINet-v2/S2C_broken-load/`

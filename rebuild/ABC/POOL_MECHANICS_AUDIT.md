# POOL_MECHANICS_AUDIT — how the source pool is built, ordered, sampled and truncated

**Scope.** A read-only trace of pool assembly, ordering, sampling and `zip()` truncation across
the two CSRDA rounds, to verify or refute: *"Stage C's added generations cannot expand the
optimization budget and can only rearrange the mixture within it."*

**TRAINS NOTHING. MODIFIES NOTHING.** No checkpoint loaded, no GPU used, no image opened, no
existing repo file changed. Two files are *added*: this document and the probe it cites.

**Probe of record.** [rebuild/ABC/pool_mechanics_probe.py](pool_mechanics_probe.py) — self-contained,
repo-relative paths only (no `/tmp`, no archive reference, so the provenance gate stays clean).
Run as `.venv/bin/python rebuild/ABC/pool_mechanics_probe.py`. All probe output quoted below is
from that script. It introspects the *real* `Src/utils/Dataloader.py` and `MyTrain.py` (by AST),
exercises the *real* `torch.utils.data.DataLoader` on synthetic tensors at the real pool sizes,
lists the *real* pool directories, and does the arithmetic from the committed
[rebuild/ABC/out/abc_runs.csv](out/abc_runs.csv).

**Code state.** `git diff c1cb293 HEAD -- MyTrain.py CLS.py Src/utils/Dataloader.py` is empty:
the three files traced here are byte-identical to what the 24 ABC runs executed.

**Verdict up front.** The claim is **correct in its conclusion and wrong in its mechanism as
usually stated.** Both loaders are **shuffled** (`shuffle=True`), so nothing is ever
*permanently* unseen. What added data buys is **zero extra gradient steps** and **strictly less
per-image exposure per epoch** — dilution, not exclusion.

---

## 1. How the source loader is constructed, and in what order — **VERIFIED**

### 1.1 List construction is `os.listdir` + `sorted`

[Src/utils/Dataloader.py:11-19](../../Src/utils/Dataloader.py#L11-L19):

```python
11  class SrcDataset(data.Dataset):
12      def __init__(self, image_root, gt_root, trainsize):
13          self.trainsize = trainsize
14          self.images = [image_root + f for f in os.listdir(image_root) if f.endswith('.jpg') or f.endswith('.png')]
15          self.gts = [gt_root + f for f in os.listdir(gt_root) if f.endswith('.tif') or f.endswith('.png')]
16          self.images = sorted(self.images)
17          self.gts = sorted(self.gts)
18          self.filter_files()
19          self.size = len(self.images)
```

- `os.listdir` order is arbitrary (inode order); [:16-17](../../Src/utils/Dataloader.py#L16-L17)
  makes it deterministic. `sorted()` on `str` is **codepoint order**, and it sorts the *full path*
  (`image_root + f`), which is a constant prefix per call, so it is equivalent to sorting the
  bare filenames. **Confirmed sorted by filename.**
- Image↔mask pairing is by **sorted-list index**, not by name
  ([:29-31](../../Src/utils/Dataloader.py#L29-L31)). `filter_files`
  ([:39-50](../../Src/utils/Dataloader.py#L39-L50)) is *not* a pairing guard — it asserts equal
  lengths and drops positional pairs whose PIL sizes differ. This is already gated by ABC's G-A4
  / G-A6 (`abc_build_pools.py:172-181`).
- `self.size` is set **after** `filter_files`, so the `[Source Loader] Loaded N` print
  ([:202](../../Src/utils/Dataloader.py#L202)) is the *post-filter* size. Cross-check: the
  directory listing and the logged size agree exactly for every pool inspected (e.g. round-2
  `SINet_B_s42` = 7349 on disk = `pool_r2` 7349 in `abc_runs.csv`), so **zero pairs were dropped
  by `filter_files` in any ABC run**.

### 1.2 The loader **shuffles**. This is the pivotal finding.

[Src/utils/Dataloader.py:200-209](../../Src/utils/Dataloader.py#L200-L209):

```python
200  def get_srcloader(image_root, gt_root, batchsize, trainsize, shuffle=True, num_workers=0, pin_memory=True):
201      dataset = SrcDataset(image_root, gt_root, trainsize)
202      print(f"[Source Loader] Loaded {len(dataset)} image-mask pairs from {image_root} and {gt_root}")
203      data_loader = data.DataLoader(dataset=dataset,
204                                    batch_size=batchsize,
205                                    shuffle=shuffle,
```

The default is `shuffle=True`, and the call site does **not** override it —
[MyTrain.py:312-316](../../MyTrain.py#L312-L316):

```python
312  source_loader = get_srcloader(image_root=opt.source_root + 'Image/',
313                          gt_root=opt.source_root + 'GT/',
314                          batchsize=opt.batchsize,
315                          trainsize=opt.trainsize,
316                          num_workers=6)
```

Probe P1:

```
  get_srcloader  shuffle default = True   all defaults: {'shuffle': True, 'num_workers': 0, 'pin_memory': True}
  get_tarloader  shuffle default = True   all defaults: {'shuffle': True, 'num_workers': 0, 'pin_memory': True}
  MyTrain.py:312  get_srcloader(image_root, gt_root, batchsize, trainsize, num_workers)  -> "shuffle" passed explicitly? False
  MyTrain.py:317  get_tarloader(image_root, batchsize, trainsize, num_workers)  -> "shuffle" passed explicitly? False
```

Probe P2 confirms the resulting sampler:

```
  source sampler class = RandomSampler
```

**Consequence, stated as the prompt asks:** we are in the **shuffled** world. *"Added from the top
or the end"* is **irrelevant** to which images are seen — every image in the pool has the same
per-epoch sampling probability. The real quantity is **coverage-per-epoch**, not position. §3 and
§4 still report sorted position, because it is the answer to a question that was asked, but every
position finding there is **conditional on `shuffle=False`, which is not the case here.**

---

## 2. What `zip(source, target)` truncation actually does — **VERIFIED**

### 2.1 The loop

[MyTrain.py:48-53](../../MyTrain.py#L48-L53):

```python
48      if opt.method == 'source_only':
49          batches = ((src_batch, (None, None)) for src_batch in source_loader)
50      else:
51          batches = zip(source_loader, target_loader)
52
53      for step, ((src_image, src_gt), (tar_weak_image, tar_strong_image)) in enumerate(batches):
```

Every ABC run used `--method ours` ([rebuild/ABC/abc_train.py:54](abc_train.py#L54)), so the
`zip` branch at [:51](../../MyTrain.py#L51) is the one that ran. (The `source_only` branch at
[:49](../../MyTrain.py#L49) is the *only* configuration that iterates the full source loader —
it is not used here.)

### 2.2 `total_step` is a *report* of the truncation, not the mechanism

[MyTrain.py:325-327](../../MyTrain.py#L325-L327):

```python
325      # zip() truncates to the shorter loader; Source-Only ignores the target loader.
326      total_step = (len(source_loader) if opt.method == 'source_only'
327                    else min(len(source_loader), len(target_loader)))
```

`total_step` appears **only** in the log format string
([:131](../../MyTrain.py#L131), [:133](../../MyTrain.py#L133),
[:135](../../MyTrain.py#L135)). Loop length is set purely by `zip`. Two consequences: the logged
`total_step` is trustworthy evidence *about* the truncation, and the `or step == total_step`
branch at [:131](../../MyTrain.py#L131) is **dead code** — `step` maxes out at
`total_step - 1 = 252`. Confirmed in a real log: the last printed step is `0250/0253`.

> Citation correction: `ABC_PLAN.md` cites this as `MyTrain.py:306-307`. On the actual file
> (unchanged since `065dac6`, the commit that wrote the plan) `:306-307` is the `PGT_Loss`
> construction. See §7 Appendix.

### 2.3 Which regime: **a different random subset every epoch**

`DataLoader` uses `drop_last=False` by default, so `len(loader) = ceil(N / batch)`. Probe P2 at
the real SINet round-1 A2/B/C numbers:

```
  len(source_loader)=341  len(target_loader)=253  min=253  drop_last=False
  ceil(5447/16)=341   ceil(4040/16)=253
  epoch 0: steps yielded=253  source idx PULLED=4064  TRAINED-ON=4048
  epoch 1: steps yielded=253  source idx PULLED=4064  TRAINED-ON=4048
  epoch 2: steps yielded=253  source idx PULLED=4064  TRAINED-ON=4048
  |E0|=4048 |E1|=4048 |E0&E1|=3015  Jaccard=0.5934  (independent-draw prediction 0.5913)
  same subset in consecutive epochs? False
  union over 3 epochs covers 5367/5447 of the pool
  source batches pulled=254  (=253 trained + 1 fetched-then-dropped by zip)
```

Three separately load-bearing facts:

1. **The consumed subset is re-drawn every epoch.** `same subset in consecutive epochs? False`,
   and the measured Jaccard (0.5934) matches the analytic prediction for two independent uniform
   subsets of size 4048 from 5447 (0.5913). It is not the *same* trailing batches each epoch.
2. **253 steps trained; 254 source batches pulled.** `zip` evaluates its iterators left to right,
   so at step 253 it calls `next(source)` — materializing a 254th source batch — and *then*
   `next(target)` raises `StopIteration`. That 254th batch is discarded without a gradient step.
   So 4064 source images are *loaded* and 4048 are *trained on* per epoch. (Measured at
   `num_workers=0`. The real runs use `num_workers=6`
   ([MyTrain.py:316](../../MyTrain.py#L316)), whose worker prefetch loads further batches that
   are likewise never trained on; the exact prefetch count is **UNVERIFIED** and does not affect
   the trained-on count, which is fixed by `zip`.)
3. **Batches are re-formed, not merely re-ordered.** Because a fresh permutation is drawn each
   epoch, the un-consumed remainder is a **uniformly random subset of size `N − 4048`**, not a
   fixed set of pre-formed trailing batches.

### 2.4 Fresh iteration each epoch — the loop structure that guarantees the re-draw

The loaders are constructed **once per CSRDA round** at
[MyTrain.py:312-320](../../MyTrain.py#L312-L320), *inside* the round loop
[:265](../../MyTrain.py#L265) but *outside* the epoch loop. The epoch loop
[MyTrain.py:336-341](../../MyTrain.py#L336-L341):

```python
336      for epoch_iter in range(1, opt.epoch):
337          adjust_lr(optimizer, epoch_iter, opt.decay_rate, opt.decay_epoch)
338
339          trainer(source_loader=source_loader, target_loader=target_loader,
340                  model=model, ema_model=model_ema, optimizer=optimizer, epoch=epoch_iter,
341                  opt=opt, loss_func=LogitsBCE, total_step=total_step, alpha=opt.alpha, log_file_path=log_file_path)
```

So the **same loader object** is passed every epoch, and `zip(...)` at
[:51](../../MyTrain.py#L51) calls `iter()` on it afresh. `persistent_workers` is not set
(default `False`), so a new `_MultiProcessingDataLoaderIter` and a new `RandomSampler` iteration —
hence a new `torch.randperm` — is produced per epoch. Probe P2 demonstrates exactly this on the
real `DataLoader` class. **Epoch N and epoch N+1 see different subsets. VERIFIED.**

Side note, **UNVERIFIED and not load-bearing**: `set_random_seed(opt.seed)`
([MyTrain.py:255](../../MyTrain.py#L255)) is called once, before the round loop, so the
permutation sequence is a deterministic function of the seed within a run. Whether the
per-epoch sampler seeds are *aligned across arms* (same seed, different pool size) was not
probed and no claim here depends on it.

### 2.5 Quantified at B = 1000 (the prompt's case) and everywhere else

| | pool | batches | trained/epoch | dropped/epoch | dropped fraction | same set each epoch? |
|---|---|---|---|---|---|---|
| R1 A0 | 4447 | 278 | 4048 | **25 batches / 399 imgs** | 8.97 % | **No — random** |
| R1 A2/B/C | 5447 | 341 | 4048 | **88 batches / 1399 imgs** | 25.68 % | **No — random** |
| R2 B s42 | 7349 | 460 | 4048 | **207 batches / 3301 imgs** | 44.92 % | **No — random** |
| R2 C10 s45 (largest) | 7610 | 476 | 4048 | **223 batches / 3562 imgs** | 46.81 % | **No — random** |

**At B = 1000: 88 of 341 source batches (25.7 %) are dropped per epoch, and they are a different
random 88 every epoch.**

Because the subset is re-drawn, `P(an image is never trained on across the whole round)` is
`p_drop ** n_epochs`:

| | `p_drop` | epochs | P(never seen in the round) |
|---|---|---|---|
| R1 A0 | 0.0897 | 39 | 1.46 × 10⁻⁴¹ |
| R1 A2/B/C | 0.2568 | 39 | 9.48 × 10⁻²⁴ |
| R2 B s42 | 0.4492 | 39 | 2.78 × 10⁻¹⁴ |
| R2 C10 s45 | 0.4681 | 39 | 1.39 × 10⁻¹³ |

**Nothing is permanently unseen.** Probe P2's 3-epoch union already reaches 5367/5447 (98.5 %).

---

## 3. Where Stage C's re-renders sit in the pool — **VERIFIED (and non-load-bearing)**

### 3.1 Filename forms

`abc_build_pools.py:66-76` links the base pool in first and then the arm's additions;
`abc_common.py:134-152` (`arm_added`) fixes the destination prefixes:

- base authors' pool: `NNNN.jpg` — digit-prefixed (`0004.jpg` … `9057.jpg`), 4447 files
- arm B and arm C additions: `SOD_<stem>.jpg` (`abc_common.py:147,150`)
- arm A2 additions: `DUP_<stem>.jpg` (`abc_common.py:144`)

### 3.2 Sorted position — probe P3

Codepoint order puts digits (`0x30`–`0x39`) before uppercase (`0x41`–`0x5A`), so the entire base
pool precedes every prefixed addition:

```
  ROUND 1  A0  s42  n=4447  batches=278  hypothetical unshuffled cut at index 4048
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool            pre-cut  4048 / post-cut   399

  ROUND 1  A2  s42  n=5447  batches=341  hypothetical unshuffled cut at index 4048
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool            pre-cut  4048 / post-cut   399
      [ 4447.. 5446] n= 1000  DUP_*.jpg          authors dup (arm A2)         pre-cut     0 / post-cut  1000

  ROUND 1  C10 s42  n=5447  batches=341  hypothetical unshuffled cut at index 4048
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool            pre-cut  4048 / post-cut   399
      [ 4447.. 5446] n= 1000  SOD_*.jpg          LAKE-RED re-render (arms B/C)  pre-cut     0 / post-cut  1000
```

**Answer:** the Stage-C re-renders **cluster in one contiguous block at the very end** —
sorted indices 4447–5446, all 1000 of them, with **zero interleaving** into the base pool.

**Explicit dependency, as required:** this matters for sampling **only if `shuffle=False`**.
It is `True` (§1.2), so position has **no effect** on which images are trained. Recorded here
because it is the answer to the question asked, and because it makes the counterfactual in §5
exact.

---

## 4. What Stage B / CLS appends for round 2, and where — **VERIFIED**

### 4.1 The round-2 pool is round-1's pool plus the appends

[CLS.py:16-29](../../CLS.py#L16-L29) — the round-1 source is **copied in whole** first:

```python
16      source_copy_root = source_root.rstrip('/\\') + f'_iteration{iteration + 1}/'
17      gt_copy_root = gt_root.rstrip('/\\') + f'_iteration{iteration + 1}/'
19      if os.path.exists(source_copy_root):
21          shutil.rmtree(source_copy_root)
23      shutil.copytree(source_root, source_copy_root)
```

Selection and append — [CLS.py:139](../../CLS.py#L139) and
[CLS.py:149-156](../../CLS.py#L149-L156):

```python
139          if edge_loss.item() < u * avg_loss:
149              if np.max(cam) < tau:
150                  print(f'[Skip] CAM: {name}')
151                  continue
155              cv2.imwrite(os.path.join(pgt_save_dir, name), cam * 255)
156              original_image.save(os.path.join(image_save_dir, name))
```

Two gates, not one: the `edge_loss < u * avg_loss` confidence test at
[:139](../../CLS.py#L139) **and** the `max(cam) >= tau` test at
[:149-151](../../CLS.py#L149-L151); image and mask are written together or both skipped
([:155-156](../../CLS.py#L155-L156), `continue` at [:151](../../CLS.py#L151)).
[CLS.py:162](../../CLS.py#L162) returns the new root, adopted at
[MyTrain.py:348-349](../../MyTrain.py#L348-L349).

**Confirmed: round-2 pool = (round-1 source pool) + (CLS-appended pseudo-labeled real target
images).** Arithmetic check against the committed table
([out/abc_runs.csv](out/abc_runs.csv)): `SINet_B_s42` `pool_r1` 5447 → `pool_r2` 7349,
`n_appended` 1902 = 7349 − 5447, and the directory holds exactly 5447 `.jpg` + 1902 `.png`
(probe: extension breakdown of `SINet_B_s42_iteration2/Image`).

### 4.2 The appends land as `.png`, in **two** places, not one

Names come from [Dataloader.py:140-142](../../Src/utils/Dataloader.py#L140-L142), which renames
`.jpg` → `.png`:

```python
140          name = self.images[self.index].split('/')[-1]
141          if name.endswith('.jpg'):
142              name = name.split('.jpg')[0] + '.png'
```

The target pool (`Dataset/Target/Image/`, 4040 images) is a **mixture of two datasets**:
`COD10K-CAM-*.jpg` and `camourflage_*.jpg`. In codepoint order
`digits < 'C'(0x43) < 'D'(0x44) < 'S'(0x53) < 'c'(0x63)`, so the appends **split around the
renders**. Probe P3 on the real round-2 directories:

```
  ROUND 2  A0  s42  n=6313  batches=395
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool
      [ 4447.. 5968] n= 1522  COD10K-*.png       CLS pseudo-label (round 2)
      [ 5969.. 6312] n=  344  camourflage_*.png  CLS pseudo-label (round 2)

  ROUND 2  B   s42  n=7349  batches=460
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool
      [ 4447.. 6042] n= 1596  COD10K-*.png       CLS pseudo-label (round 2)
      [ 6043.. 7042] n= 1000  SOD_*.jpg          LAKE-RED re-render (arms B/C)
      [ 7043.. 7348] n=  306  camourflage_*.png  CLS pseudo-label (round 2)

  ROUND 2  C10 s42  n=7299  batches=457
      [    0.. 4446] n= 4447  NNNN.jpg           authors base pool
      [ 4447.. 5980] n= 1534  COD10K-*.png       CLS pseudo-label (round 2)
      [ 5981.. 6980] n= 1000  SOD_*.jpg          LAKE-RED re-render (arms B/C)
      [ 6981.. 7298] n=  318  camourflage_*.png  CLS pseudo-label (round 2)
```

**Answer to "how do `.png` appends sort against `.jpg` and the re-renders":** the extension is
irrelevant — sorting is on the *whole* filename, so the **prefix decides**. `COD10K-*.png` sorts
**before** `SOD_*.jpg`; `camourflage_*.png` sorts **after** it (lowercase). The round-2 sorted
order is therefore `base → COD10K pseudo-labels → SOD_ renders → camourflage pseudo-labels`, and
the renders end up **sandwiched between the two pseudo-label blocks**, not at the tail. (Note:
`ls | sort` under a UTF-8 locale reports a *different* order because ICU collation ignores case
and punctuation — it wrongly shows `SOD_9057.jpg` as the tail. Only Python's `sorted()`, which is
what [Dataloader.py:16](../../Src/utils/Dataloader.py#L16) uses, is authoritative. This is why
the probe exists.)

### 4.3 Round-2 `total_step` is unchanged — **VERIFIED from the real logs**

`total_step` is recomputed per round at [MyTrain.py:326-327](../../MyTrain.py#L326-L327), but
`len(target_loader)` is unchanged (4040 target images, both rounds), and the source loader is now
even *longer*, so `min(...)` still returns the target length.

Measured, not assumed — `awk` over the round-2 half of a real
`Snapshot/ABC/SINet_B_s42/training_log.log` (split on the `Training Log` marker written per round
at [MyTrain.py:332-333](../../MyTrain.py#L332-L333)):

```
round-2 distinct total_step values: 0253
round-2 epoch range: 001/040 .. 039/040
SINetv2_B_s42, both rounds, distinct total_step values: 0127
```

and across all 24 runs, [out/abc_runs.csv](out/abc_runs.csv) column `total_step_set` is the
**single** value `0253` (SINet) / `0127` (SINet-v2), asserted by
[abc_train.py:108,111](abc_train.py#L108-L111).

**Quantified at the measured round-2 sizes** (`n_appended` 1732–2163, round-2 source
6179–7610 → 387–476 batches vs 253 target):

| arm | round-2 pool (s42/s43/s45) | batches | dropped/epoch | dropped fraction |
|---|---|---|---|---|
| A0 | 6313 / 6179 / 6243 | 395 / 387 / 391 | 142 / 134 / 138 batches | 35.9 / 34.5 / 35.2 % |
| A2 | 7227 / 7284 / 7208 | 452 / 456 / 451 | 199 / 203 / 198 batches | 44.0 / 44.4 / 43.8 % |
| B | 7349 / 7550 / 7466 | 460 / 472 / 467 | 207 / 219 / 214 batches | 45.0 / 46.4 / 45.8 % |
| C10 | 7299 / 7229 / 7610 | 457 / 452 / 476 | 204 / 199 / 223 batches | 44.6 / 44.0 / 46.8 % |

So yes: **the round-2 pool is larger and a larger fraction is un-consumed per epoch** — ~45 % for
B/C against ~35 % for A0 — but it is a *different random* 45 % every epoch.

---

## 5. The synthesis: what is actually lost — **VERIFIED**

### 5.1 Which world we are in

**We are in the shuffled world** (§1.2, `RandomSampler`, probe P1/P2). Therefore:

- **Nothing is permanently unseen.** P(never trained on in a round) ≤ 1.4 × 10⁻¹³ for the worst
  arm (§2.5).
- **What is lost is per-epoch coverage, i.e. per-image exposure.** Every image in the pool —
  base image, LAKE-RED re-render, and CLS pseudo-label alike — is sampled with the *same*
  probability `4048 / N`. Added data dilutes **everything uniformly**, including itself.
- **The optimization budget is exactly fixed.** Per run: **19,734 gradient steps**
  (253 × 39 × 2 rounds) and **315,744 source images through the model** for SINet;
  **25,146 steps / 804,672 images** for SINet-v2. **Identical for every arm and seed** — the
  logged `total_step_set` proves it for all 24 runs.

### 5.2 The unshuffled counterfactual, for completeness

Were `shuffle=False`, the picture would be catastrophically different, and the sorted-position
findings above make it exact. At the truncation cut of image index 4048:

- **Round 1, A2/B/C:** the cut falls at index 4048, still *inside* the 4447-image base block. So
  **all 1000 additions (indices 4447–5446) plus the last 399 base images would be trained on
  never, in any epoch** — Stage B and Stage C would be literal no-ops.
- **Round 2, arm B s42:** everything from index 4048 on would be dropped — 399 base images, all
  1596 `COD10K-*` pseudo-labels, all 1000 `SOD_` renders, and all 306 `camourflage_*`
  pseudo-labels: **3301 images, 44.9 % of the pool, disproportionately the appends** (100 % of
  every CLS pseudo-label and 100 % of every re-render would be dropped, versus 9.0 % of the base
  pool).

That world is the one the phrase *"added data is never sampled beyond the truncation point"*
describes. **It is not this repo's world.** Any paper text asserting it would be wrong.

### 5.3 Per-image expected exposure per epoch (probe P4/P5)

`exposure = total_step × batch / pool_size`. Target-side exposure is **1.000 every epoch in every
arm** (253 × 16 = 4048 ≥ 4040, so the target loader is exhausted exactly once per epoch — which
is *why* it is the shorter loader).

**SINet** (batch 16, `total_step` 253 → 4048 imgs/epoch, 39 epochs/round):

| arm | R1 pool | **R1 exposure** | R2 pool (mean) | **R2 exposure (mean)** | cumulative passes (R1 + R2) |
|---|---|---|---|---|---|
| **A0** | 4447 | **0.9103** | 6245 | **0.6482** | 35.5 + 25.3 = **60.8** |
| **A2** | 5447 | **0.7432** | 7240 | **0.5592** | 29.0 + 21.8 = **50.8** |
| **B** | 5447 | **0.7432** | 7455 | **0.5431** | 29.0 + 21.2 = **50.2** |
| **C10** | 5447 | **0.7432** | 7379 | **0.5488** | 29.0 + 21.4 = **50.4** |

**SINet-v2** (batch 32, `total_step` 127 → 4064 imgs/epoch, 99 epochs/round):

| arm | R1 pool | **R1 exposure** | R2 pool (mean) | **R2 exposure (mean)** | cumulative passes (R1 + R2) |
|---|---|---|---|---|---|
| **A0** | 4447 | **0.9139** | 6399 | **0.6351** | 90.5 + 62.9 = **153.4** |
| **A2** | 5447 | **0.7461** | 7489 | **0.5427** | 73.9 + 53.7 = **127.6** |
| **B** | 5447 | **0.7461** | 7467 | **0.5443** | 73.9 + 53.9 = **127.8** |
| **C10** | 5447 | **0.7461** | 7468 | **0.5443** | 73.9 + 53.9 = **127.8** |

Per-run values are in probe P4 (all 24 runs, 4-decimal). The round-1 A0-vs-B/C ratio is
**0.9103 / 0.7432 = 1.2248 — A0 gives every base image 22.5 % more exposure per epoch.** This
reproduces `ABC_PLAN.md` §A.5.1's committed 0.9103 / 0.7432 exactly; **round 2's numbers are new
here** and were not previously tabulated.

### 5.4 What "rearranging the mixture" means numerically (probe P6)

Because the sampler is uniform over the pool, the *expected composition* of the 4048 source
images trained on per epoch is the pool's composition scaled to 4048:

| run | R1: base / added | R2: base / added / CLS-pseudo | R2 pseudo share |
|---|---|---|---|
| SINet_A0_s42 | 4048 / 0 | 2851 / 0 / 1197 | 0.2956 |
| SINet_A2_s42 | 3305 / 743 | 2491 / 560 / 997 | 0.2463 |
| SINet_B_s42 | 3305 / 743 | 2450 / 551 / 1048 | 0.2588 |
| SINet_C10_s42 | 3305 / 743 | 2466 / 555 / 1027 | 0.2537 |

So Stage C's 1000 re-renders buy about **743 render-images per epoch out of a fixed 4048** in
round 1 (18.4 % of the gradient budget), falling to **~540 out of 4048** (13.3 %) in round 2 as
CLS pseudo-labels dilute them further. They buy **zero additional steps**, and they *remove*
743 base-image slots in round 1 and ~590 in round 2. **That is the whole of the mechanism.**

---

## 6. Cross-check against the measured `n_appended` variance — **VERIFIED (cause) / reasoned (confound)**

### 6.1 The cause is confirmed

`n_appended` = the count of target images passing **both** CLS gates
([CLS.py:139](../../CLS.py#L139), [:149-151](../../CLS.py#L149-L151)). Both gates are evaluated
with **that arm's own round-1 student and teacher**
([CLS.py:62-73](../../CLS.py#L62-L73), invoked at
[MyTrain.py:348](../../MyTrain.py#L348) with `opt.save_model` = the arm's RUNID-scoped snapshot
dir). Even `avg_loss` — the threshold itself — is recomputed per arm from that arm's own models
([CLS.py:85-112](../../CLS.py#L85-L112)). So **every arm × seed gets a different threshold applied
by a different pair of models to the same 4040 target images.** Different counts are the expected
outcome, not an anomaly.

Measured ([out/abc_runs.csv](out/abc_runs.csv), 24 runs): `n_appended` **1732–2163**, mean
**1945.8**, spread **22.2 % of the mean** — which is exactly the one threshold
`ABC_RESULTS.md:53-55` records as **FAILED** (`n_appended_spread_exceeds_5pct = True`). This
audit **confirms that failure and its cause**; it does not soften it.

### 6.2 Does the pinned `total_step` neutralize it? **Partly — and the residual is real**

**What the pin does neutralize:** the *optimization budget*. Every arm gets 19,734 steps and
315,744 source images regardless of `n_appended`. There is **no** confound of the form "arm C
trained longer." That is genuinely closed, and asserted for all 24 runs.

**What it does not neutralize — two residuals:**

1. **Mixture composition (real, small, non-systematic).** Round-2 pseudo-label share ranges
   **0.2443–0.2956** on SINet (**5.13 pp spread**) and **0.2590–0.3079** on SINet-v2
   (**4.88 pp**) — probe P7. So arms differ in *what* fills their fixed 4048 slots. **But for the
   campaign's actual claim, Δ(C − B), the effect is small and unsigned:** the round-2
   render share is 0.1361/0.1325/0.1339 for B vs 0.1370/0.1383/0.1314 for C10 on SINet
   (0.1341/0.1335/0.1342 vs 0.1318/0.1360/0.1339 on SINet-v2) — a **0.1–0.7 pp** difference that
   **changes sign between seeds and between architectures**. Mean round-2 exposure is 0.5431 (B)
   vs 0.5488 (C10) on SINet and 0.5443 vs 0.5443 on SINet-v2. **It is noise, not a bias in C's
   favour.**
2. **`n_appended` is itself downstream of round-1 model quality**, so it is a *mediator*, not an
   exogenous nuisance. A better round-1 model produces more confident target predictions and thus
   more appends. Conditioning on it would be conditioning on a post-treatment variable. The right
   treatment is exactly what `abc_train.py:253-261` already does: **report it, do not adjust for
   it** — and `ABC_RESULTS.md:165` correctly notes that the one arm-level pattern in it is not
   architecture-robust.

**Verdict on §6:** not a confound for **C-vs-B**; a **reported, unadjusted, arm-dependent mixture
difference** that the pinned budget bounds but does not erase. It cannot manufacture the null,
because it does not favour either arm consistently. It is a genuine — and already logged —
limitation of running the campaign at `--iteration 2`.

---

## 7. Required closing statements

### (a) The one-sentence honest statement, corrected

> **Because `zip()` stops at the shorter loader and the target loader is fixed at 253 batches
> (SINet) / 127 (SINet-v2), every arm receives an identical optimization budget — 19,734 gradient
> steps and 315,744 source images per run — regardless of pool size; and because both loaders are
> shuffled (`RandomSampler`, `shuffle=True`), added data is *not* excluded from training but
> instead uniformly dilutes the per-epoch exposure of every image in the pool, so Stage C's 1000
> re-renders can only *rearrange the composition* of a fixed number of gradient steps, never add
> any.**

This **corrects** the loose framing. The paper must say **"added data reduces per-epoch coverage
of every image"** (dilution), **not** *"added data is never sampled beyond the truncation point"*
(exclusion). The second is what an unshuffled loader would do (§5.2); this loader shuffles, and
the difference is not cosmetic — under exclusion Stage B and C would be provable no-ops, whereas
under dilution they genuinely enter ~18.4 % of round-1 gradient content and the null is a real
empirical result about that content.

### (b) Per-image per-epoch exposure, A0 vs B/C

| | round 1 | round 2 (arm mean) |
|---|---|---|
| **SINet A0** | **0.9103** | **0.6482** |
| **SINet B** | **0.7432** | **0.5431** |
| **SINet C10** | **0.7432** | **0.5488** |
| SINet A2 (clean control) | 0.7432 | 0.5592 |
| **SINet-v2 A0** | **0.9139** | **0.6351** |
| **SINet-v2 B** | **0.7461** | **0.5443** |
| **SINet-v2 C10** | **0.7461** | **0.5443** |
| SINet-v2 A2 | 0.7461 | 0.5427 |

Target-domain exposure is **1.000** in every arm, both rounds. Round 1: B and C are *exactly*
equal by construction (identical pool size 5447). Round 2: they differ only through `n_appended`,
by ≤ 1.0 % and without a consistent sign. Full per-run table: probe P4.

### (c) Does this change the interpretation of the A/B/C null?

**No — the null stands, and one caveat is now quantified rather than asserted.**

- **The null is not an artifact of truncation.** Under shuffling, Stage C's renders *were*
  trained on: ~743 render-images in each of 39 round-1 epochs (18.4 % of every epoch's source
  content), and each individual render appeared in ~29 round-1 gradient batches. The additions
  were not silently discarded. **The null is about data that actually reached the optimizer.**
- **Δ(C − B) remains the clean comparison and remains unaffected.** Identical pool size, identical
  budget, identical round-1 exposure (0.7432 / 0.7461), identical mask provenance. Round-2
  exposure differs by ≤ 1.0 % with sign flipping across seeds and architectures.
- **A0 remains an unclean control, for the reason already recorded** — and this audit adds that it
  is unclean in **both** rounds, not just round 1: A0's exposure advantage is 22.5 % in round 1
  **and 19.3 % in round 2** (0.6482 / 0.5431). `ABC_PLAN.md` §A.5.1 tabulates only the round-1
  figure; the round-2 figure is new here and should be added.
- **One framing in the write-up needs a word changed.** `ABC_RESULTS.md:231` — *"`total_step`
  pinned at 253/127 in both rounds of all 24 runs, so added data bought zero extra optimisation"*
  — is **correct as written** and is confirmed. `ABC_PLAN.md:346-347`'s *"B changes the mixture
  and not the step count"* is also **correct**. Neither overclaims exclusion. The correction in
  (a) is a guard against the *stronger* claim, which appears nowhere in the committed documents
  but is the natural misreading of "the loop can't absorb added data."

### (d) No training and no file modification occurred

- No `MyTrain.py`, `MyTest.py`, `CLS.py`, `abc_train.py` or driver invocation. No `.pth` read or
  written. No GPU allocated (the probe imports `torch` and builds CPU-only synthetic tensors).
- No existing repo file modified. `git status --short` after this audit reports **no `M` entries
  at all** — only untracked paths (`?? LAKE-RED/`, pre-existing, plus the two files below). This
  work adds only two **new** files:
  - `rebuild/ABC/POOL_MECHANICS_AUDIT.md` (this document)
  - `rebuild/ABC/pool_mechanics_probe.py` (the probe of record)
- No log block was written to `results/REBUILD_LOG.txt`; `C.log_block` was never called.
- Every real directory was touched with `os.listdir` only. The probe opens exactly one file for
  reading (`rebuild/ABC/out/abc_runs.csv`) plus `MyTrain.py` for AST parsing. **It opens no image
  and no mask.**

---

## Appendix — defects found while tracing

Recorded because the audit demanded exact `file:line` and these were in the way. Neither affects
any measured ABC result.

1. **`ABC_PLAN.md`'s `MyTrain.py` line citations are 20 lines stale from ~`:242` onward**, and
   were stale when written (`git log` shows `065dac6` — the commit that added the plan — is the
   last commit to touch `MyTrain.py`, so the file has not moved since). Verified mismatches:

   | plan cites | plan says it is | what is actually there | correct line |
   |---|---|---|---|
   | `:242` | seed / shuffle order | `opt.source_root = './Dataset/Source/HKU-IS/'` | **`:255`** (`set_random_seed`) |
   | `:306-307` | `total_step` | `PGT_Loss = ESLoss(...)` | **`:326-327`** |
   | `:316` | `range(1, opt.epoch)` | `num_workers=6)` | **`:336`** |
   | `:322` | `epoch_iter > 20` val gate | `val_loader = test_dataset(...)` | **`:342`** |
   | `:297-300` | target pool | model-parameter copy loop | **`:317-320`** |

   `:51,53` (the `zip`) and the `CLS.py` citations are **correct**. Suggest a `REVISION_TABLE`
   entry.

2. **Dead branch at [MyTrain.py:131](../../MyTrain.py#L131).** `or step == total_step` can never
   fire: `step` is 0-indexed and stops at `total_step - 1`. Harmless (the `step % 10 == 0` arm
   carries the logging), but it means the final step of each epoch is never logged unless its
   index is a multiple of 10 — the last line of every SINet epoch is `0250/0253`, not `0252/0253`.

3. **One source batch per epoch is loaded and thrown away** (§2.3 item 2): `zip` pulls the 254th
   source batch before the target iterator raises `StopIteration`. 16 images of I/O and CPU
   augmentation per epoch, ×39 epochs ×2 rounds ×24 runs. Cosmetic waste, no correctness impact,
   and it does **not** change the exposure figures (which count trained-on images).

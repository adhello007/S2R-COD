# ABC_SCOPING.md — pre-execution scoping audit for the 3-seed A/B/C training campaign

**Status: scoping only. Nothing was trained. No training script was written.**

Branch `experiments/lakered/stageC/rebuild`, HEAD `2348d76`, audited 2026-09-04.

Every DECISION below is either (a) read out of the code / committed artifacts on this machine, with a
`file:line` or log citation, or (b) marked **UNRESOLVED** with what is needed. Where a premise in the
brief is wrong, it is corrected explicitly rather than answered as asked. Six such corrections are
flagged **PREMISE CORRECTION**.

**Read §10 first if you read nothing else** — three blocking code facts must be resolved before any
arm can be constructed at all, and two of them make arms B and C *silently identical to arm A* if
missed.

---

## Contents

| § | Item | Verdict |
|---|---|---|
| 1 | Model architecture | **needs-your-call** (cost table supplied, recommendation given) |
| 2 | Which pools feed which part | **settled**, with 1 premise correction |
| 3 | The three arms; what must be identical | **mostly settled**; arm-A padding **needs-your-call** |
| 4 | Embedder | **settled**; dinoL224 repeat **needs-your-call** |
| 5 | k and B | k **settled**; B and α **need-your-call** (α is an unspecified free parameter) |
| 6 | Evaluation protocol | **settled**, with 2 premise corrections; decision rule **needs-your-call** |
| 7 | Seeds and determinism | **settled** — and it changes the design (seed-matching buys much less than assumed) |
| 8 | Oracle arm | **UNRESOLVED — data absent from this machine** |
| 9 | Current-state / ambiguity summary | **A3 is UNRUN**; the "far from real target" claim is unavailable |
| 10 | Blocking code facts, totals, and risk ranking | — |

---

# 1. Model architecture — how many, and which

## DECISION

**Repo default:** `--network SINet`, 40 epochs (39 actually run), batch 16, lr 1e-4, no gradient
clipping.

**Exact commands** (all under `--task S2C`; `--source_root` is *ignored* — see §10.1):

```bash
# SINet  — 39 ep x 253 steps x iteration, batch 16, lr 1e-4, decay 0.1 @ 30
uv run python MyTrain.py --network SINet   --task S2C --method ours --iteration 2 --gpu 0 \
  --save_model ./Snapshot/SINet/<ARM>/   --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/

# SINet-v2 — self-overrides to 99 ep, batch 32, decay @ 50, clip_grad ON
uv run python MyTrain.py --network SINet-v2 --task S2C --method ours --iteration 2 --gpu 1 \
  --save_model ./Snapshot/SINet-v2/<ARM>/ --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/

# SegMaR — self-overrides to 49 ep, batch 24, lr 2.5e-5, decay 0.9 @ 40
uv run python MyTrain.py --network SegMaR  --task S2C --method ours --iteration 2 --gpu 0 \
  --save_model ./Snapshot/SegMaR/<ARM>/   --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/
```

Per-network hyperparameters are **self-set inside the script** and cannot be overridden from the CLI.
Do **not** pass `--epoch`, `--batchsize`, `--lr`, `--decay_epoch`, `--alpha`, `--u`, `--tau`,
`--a/--b/--c`: they are overwritten after parsing.

## EVIDENCE

| Fact | Citation |
|---|---|
| `--network` choices, default `SINet` | [MyTrain.py:193](MyTrain.py#L193) |
| `--task S2C` overrides α/u/τ/a/b/c **and** `source_root` | [MyTrain.py:225-232](MyTrain.py#L225-L232) |
| SINet: channel 32, `clip_grad=False`, parser defaults 40/16/1e-4/0.1@30 | [MyTrain.py:194-199](MyTrain.py#L194-L199), [:249-252](MyTrain.py#L249-L252) |
| SINet-v2: `epoch=100`, `batchsize=32`, `decay_epoch=50`, `clip_grad=True` | [MyTrain.py:253-259](MyTrain.py#L253-L259) |
| SegMaR: `epoch=50`, `batchsize=24`, `lr=2.5e-5`, `decay_rate=0.9`, `decay_epoch=40` | [MyTrain.py:260-272](MyTrain.py#L260-L272) |
| Only `opt.epoch - 1` epochs run (`range(1, opt.epoch)`) | [MyTrain.py:316](MyTrain.py#L316) |
| CLS hard-requires `Stu_40.pth` / `Stu_100.pth` / `Stu_50.pth` — so `--epoch` must not change | [CLS.py:43,48,53](CLS.py#L43-L53) |

### Which architectures are fully trainable *and* evaluable end-to-end here

All five B1 rows have 2026 committed predictions on COD10K-test and were re-scored by B1's own
pipeline, so all five are proven end-to-end on this machine and this data:

| Arch / variant | Snapshot | Predictions | B1 score CSV | Committed eval txt |
|---|---|---|---|---|
| SINet / S2C | ✓ (17 .pth + log) | 2026 | ✓ | Sα 0.7172, MAE 0.0745 |
| SINet / S2C_MT | ✓ + log | 2026 | ✓ | Sα 0.7030 |
| SINet / S2C_SO | ✓ + log | 2026 | ✓ | Sα 0.4567 |
| SINet-v2 / S2C | ✓ (no train log) | 2026 | ✓ | Sα 0.6999 |
| SegMaR / S2C | ✓ (no train log) | 2026 | ✓ | **none** — scored only by B1 |

`Result/SINet/S2C` filenames match `Dataset/Test/COD10K/GT` with **zero** diff over 2026 files
(verified). Eval tables: `Eval/Eval/eval_txt/**`.

### Per-run wall clock — measured from `training_log.log` timestamps

| Run | Config | Measured |
|---|---|---|
| **SINet / S2C** `--iteration 2` | 39 ep × 253 steps × 2 rounds | **103.9 min span** = 48.2 (round 1) + **7.5 (CLS)** + 48.2 (round 2) |
| SINet / S2C_MT | `--iteration 1`, 39 × 253 | **52.6 min** |
| SINet / S2C_SO | `--iteration 1`, 39 × 278 | **47.1 min** active (1777-min idle gap excluded) |
| SINet-v2 / S2C_MT | `--iteration 1`, 99 × 253, batch 32 | **61.6 min** |
| SINet-v2 / S2C_SO | `--iteration 1`, 99 × 278, batch 32 | **63.3 min** active |
| SegMaR / S2C | 49 ep, batch 24 | **≈47 min / round — ESTIMATE**, no training log exists; inferred from checkpoint mtimes (Stu_10 14:46 → Stu_50 15:24, ~9.6 min per 10 epochs) |

Boundary lines: `Snapshot/SINet/S2C/training_log.log:1` (`Training Log`), `:2` (round 1 start
13:29:00), `:1015` (round 1 end 14:17:13), `:1016` (second `Training Log`), `:1017` (round 2 start
14:24:41), `:2030` (end 15:12:54). Two `Training Log` markers = two rounds in one file.

**Contention:** `SINet/S2C_MT` (52.6 min) and `SINet-v2/S2C_MT` (61.6 min) both started 12:28:xx on
2026-08-12, i.e. one job per GPU. SINet round-1 alone was 48.2 min. So **running two jobs on the two
GPUs costs ~9% per job, not 100%** — parallelism is real.

Hardware: 2 × RTX PRO 6000 Blackwell, 97887 MiB each, both idle. VRAM need is ~10–14 GB at batch
16/352², so both GPUs are usable and neither is memory-bound.

### Derived unit costs (SINet, `--iteration 2`)

- **1.75 GPU-h per run.** On 2 GPUs with the ~9% contention: **~0.95 h wall-clock per run**.
- SINet-v2 `--iteration 2` ≈ 2 × 61.6 + ~8 (CLS) = **≈2.2 GPU-h per run**.

## Recommendation (costed; **your call**)

| Option | Runs (3 arms × 3 seeds) | GPU-h | Wall-clock on 2 GPUs | Share of a 10-day (240 h) budget |
|---|---|---|---|---|
| **A. SINet only** | 9 | **15.7** | **≈8.6 h** | 3.6 % |
| B. SINet + SINet-v2 | 18 | 15.7 + 19.8 = **35.5** | **≈19 h** | 7.9 % |
| C. SINet + SINet-v2 + SegMaR | 27 | ≈49.6 | ≈27 h | 11 % |

Add inference + evaluation per run: see §6 (small, but not negligible on NC4K).

**I recommend Option B — SINet + SINet-v2.** Reasoning, and it is *not* a GPU-time argument:

1. **GPU time is not the binding constraint.** Even Option C is 11 % of the budget. Choosing SINet
   alone to save 10 h of a 240 h budget would be optimising the wrong resource. The binding
   constraint is the number of *decisions* that must be right (§10.3), and each added architecture
   multiplies the surface where one can go wrong.
2. **A single-architecture null is the weakest publishable form of this result.** The paper's claim is
   about a *method* (uncertainty-guided closed-loop generation), not about SINet. B1 already
   demonstrated that this repo's ES→error relationship is *not* architecture-invariant: `S2C_SO`
   inverts the pattern in all three embedder spaces, and ρ(1−Sα)/ρ(MAE) spans 0.520–1.268 across the
   five rows (`B1_RESULTS.md` §3, §D4). A reviewer will ask whether a null on SINet is a null on the
   method. One robustness architecture answers that; three do not answer it much better.
3. **SINet-v2 is the right second, not SegMaR.** SINet-v2 has a committed eval table, a training log
   (so its wall clock is *measured*, not estimated), and it is the second row of the paper's own
   Table 1. SegMaR has **no training log and no committed eval table**, and `Explanations/SEGMAR.md`
   §2.4 documents a deliberate backbone deviation (IMAGENET1K_V2 vs the paper's V1) plus a
   `structure_loss` `reduce='none'` exposure on *both* heads. Introducing it into a load-bearing
   ablation adds a caveat to every number it produces.
4. **The honest cost framing.** Option B doubles the run count but not the risk: SINet-v2 shares the
   whole data path, so the only new variable is the architecture. If the deadline tightens, drop
   SINet-v2 *seeds* (3 → 2) before dropping the architecture; a 2-seed robustness check still
   discriminates a real effect from noise at this σ (§6, §7).

**STATUS: needs-your-call.** One caveat that would change my recommendation: if you intend to publish
per-architecture *significance*, 3 seeds × 2 architectures is 6 numbers per arm and that is thin.
Option A with 5 seeds (15 runs, 26 GPU-h) buys more statistical power on one architecture than Option
B buys breadth. Which of those two the paper needs is a claim-shape question, not a compute question.

---

# 2. Which foreground / image pools feed which part

**This is the item the brief correctly identified as highest-risk. It is now fully resolved.**

## 2.1 What `MyTrain.py` loads as the training source under `--task S2C`

### DECISION
The **authors' synthetic pool**: `Dataset/Source/HKU-IS/Image/` (4447 `.jpg`) paired with
`Dataset/Source/HKU-IS/GT/` (4447 `.png`). This is forced and cannot be changed from the CLI.

### EVIDENCE
- [MyTrain.py:219](MyTrain.py#L219) — `--source_root` default is `./Dataset/Source/CNC/`.
- [MyTrain.py:232](MyTrain.py#L232) — inside the `--task S2C` block: `opt.source_root = './Dataset/Source/HKU-IS/'`. **This runs after `parse_args()` and silently discards any `--source_root` you pass.**
- [MyTrain.py:292-296](MyTrain.py#L292-L296) — `get_srcloader(image_root=opt.source_root+'Image/', gt_root=opt.source_root+'GT/', batchsize, trainsize, num_workers=6)`.
- Counts on disk: `Dataset/Source/HKU-IS/Image` = 4447, `Dataset/Source/HKU-IS/GT` = 4447.

### PREMISE CORRECTION 1
The brief says *"confirm from MyTrain.py:220,297"*. Those two lines are the **target** loader, not the
source: [:220](MyTrain.py#L220) is `--target_root` and [:297](MyTrain.py#L297) is `get_tarloader`.
That citation comes from `D2_RESULTS.md` §3.0, where it is correct *in its own context* (D2 was
talking about the unlabeled target pool that receives the CHAMELEON duplicates). The source-pool
citation is **[MyTrain.py:232](MyTrain.py#L232) + [:292-293](MyTrain.py#L292-L293)**. The *conclusion*
in the brief is right — the authors' pool is what training reads — but the line numbers must not be
carried into the paper as-is.

**STATUS: settled.**

## 2.2 The base synthetic pool every arm shares

| Question | Answer | Evidence |
|---|---|---|
| Which pool | **Authors' synthetic pool**, `Dataset/Source/HKU-IS/Image` (4447 jpg) | above |
| Which mask set | **`Dataset/Source/HKU-IS/GT`** (4447 png) — the *authors'* GT, **not** `HKU-IS_raw/gt` | [MyTrain.py:293](MyTrain.py#L293) |
| Which polarity | **object = WHITE**, mean white fraction **0.18557** | `D1_RESULTS.md` §1 (all 4447, measured) |

`Source/HKU-IS/GT` is **not** the same mask set as `HKU-IS_raw/gt` (0.18557 vs 0.19132 mean white
fraction; no sampled stem pixel-identical — REBUILD_PLAN trap T3). Any arm-construction script that
reaches for `HKU-IS_raw/gt` for the base pool is using the wrong masks.

**STATUS: settled.**

## 2.3 The added Stage-C images: which pool, which pipeline, written where

### DECISION — and this is a substantive recommendation, not just a lookup

**Source the added images from the pre-existing local render pool
`Dataset/LAKERED/output/HKU-IS/images/SOD_<stem>.jpg` (4447), paired with
`Dataset/LAKERED/output/HKU-IS/masks/SOD_<stem>.png` (4447). Do NOT regenerate.**

Why not regenerate — this is load-bearing:

- D2 §3.3 established by controlled experiment (s8, T1/T2/T3) that a LAKE-RED render is a function of
  **(foreground, mask, position-in-shard)**, not of the foreground alone. Three byte-identical inputs
  at positions 0/1/2 in one shard produced three *different* renders (mean|diff| 36.7 and 40.3);
  forcing each to local position 0 in three shards collapsed the divergence to **exactly 0.0**.
- Therefore: if arm B regenerates its 1000 selected foregrounds and arm C regenerates its 1000, the
  two arms' renders differ **in background noise draw** as well as in selection — because the shard
  layouts differ. That injects an uncontrolled variable into precisely the comparison the campaign
  exists to make.
- The existing 4447-render pool is a **bijection onto the raw foreground set** (`D1_RESULTS.md` §1:
  4447/4447 trace in, 0 outside, 0 unrendered), so *every* foreground already has exactly one render
  on disk. Selecting a subset of a fixed pool holds the noise draw constant by construction.
- It is also free: regeneration measures **1.77–1.85 s/image** (`LAKE-RED/logs/gen_shard{0,1}.log`:
  `2224it [1:06:54, 1.77s/it]`, `2223it [1:08:23, 1.76s/it]`), i.e. ~68 min for 4447 on 2 GPUs — cheap,
  but cheapness is not the argument. Reusing is *more correct*, not just faster.

**The generation pipeline, for the record** (`LAKE-RED/run_hkuis.sh`):
1. `src/lake_red/prepare_lakered_inputs.py` reads `HKU-IS_raw/{imgs,gt}`, **inverts** the masks into
   LAKE-RED polarity (object=0 preserved, background=255 regenerated), prefixes `SOD_`, writes a
   provenance manifest into `Dataset/LAKERED/input/HKU-IS/validation/{images,masks}`.
2. `test.py --isReplace --seed 0 --shard_index i --shard_total 2` over 2 GPUs → writes
   `output/HKU-IS/{images,masks}`. `--isReplace` composites the **source object pixels back in**, so
   only the background is synthesized (E0 §2.1; D1 §3.2 measured object-interior error 5.603 vs
   background 70.802 over all 4447 — ratio 12.64, and **0** objects showing any sign of regeneration).
3. Output masks are re-inverted back to **SOD polarity**. Measured white fraction 0.19132, identical to
   `raw_gt` to five decimals (`D1_RESULTS.md` §1).

### PREMISE CORRECTION 2
The brief describes the generation path as *"grey-128 cutout → LAKE-RED"*. **Grey-128 is not a
generator input.** It is representation **R2**, the *selection* embedding: `a[gt < 127] = 128` at
native resolution, then BICUBIC resize (REBUILD_PLAN §2, R2, from `embed_dino.py:19-23`). LAKE-RED
consumes the **raw image + the inverted mask**. The correct description is:

> grey-128 cutout embedding → **selects which foreground** → that foreground's *existing* render (made
> from the raw image + inverted mask) is injected.

Conflating the two would produce a pipeline that inpaints a grey rectangle.

### Where the added images must be written so the trainer reads them
Because [MyTrain.py:232](MyTrain.py#L232) forces `source_root` to `./Dataset/Source/HKU-IS/`, there
are exactly two options, and **one of them is unacceptable**:

- ✗ **Mutate `Dataset/Source/HKU-IS/` in place per arm.** Destroys the primary pool whose agg hash
  (`b42e5f44b5f2b0db`, REBUILD_PLAN §1) every committed experiment is traceable to. Do not.
- ✓ **Patch [MyTrain.py:232](MyTrain.py#L232) to honour `--source_root`**, give each arm its own
  directory (e.g. `Dataset/Source/ABC_<arm>_s<seed>/{Image,GT}`, ~113 MB base + additions per arm),
  and pass it. This is the fix `Experiments/REPRODUCE_TABLE1_v2.md` §8 item 9 already prescribes
  ("delete or guard `opt.source_root = ...` so `--source_root` is honoured"), and `preflight.py`
  already checks the collision it prevents. **It also unblocks GPU parallelism** — see §10.1.

**STATUS: settled** on pool + pipeline + polarity. The write location depends on the §10.1 patch,
which is **needs-your-call** only in the sense that it is a deviation from released code and must be
disclosed in the paper.

## 2.4 The paired mask, and the positional-pairing invariant

### DECISION
The mask paired with added render `SOD_<stem>.jpg` is **`output/HKU-IS/masks/SOD_<stem>.png`**, which
is **pixel-identical to `HKU-IS_raw/gt/<stem>.png`**.

### EVIDENCE
Measured here, 6/6 sampled stems (5403, 1520, 5116, 1700, 0352, 5555): identical shape, **maxdiff = 0**.
Consistent with `D1_RESULTS.md` §1 (`raw_gt` and `local_msk` white fractions agree to five decimals) and
with `test.py:173` re-inverting on write. Dimensions of render, mask and raw image match exactly on
all 6 samples.

### The invariant, and exactly how it can break
`SrcDataset` pairs image↔mask **by sorted-list index, never by filename**:

- [Dataloader.py:14](Src/utils/Dataloader.py#L14) — `images` = `os.listdir` filtered to `.jpg`/`.png`
- [Dataloader.py:15](Src/utils/Dataloader.py#L15) — `gts` = `os.listdir` filtered to **`.tif`/`.png`**
- [Dataloader.py:16-17](Src/utils/Dataloader.py#L16-L17) — the two lists are `sorted()` **independently**
- [Dataloader.py:29-37](Src/utils/Dataloader.py#L29-L37) — `__getitem__` returns `images[index]`, `gts[index]`

`filter_files()` ([Dataloader.py:39-50](Src/utils/Dataloader.py#L39-L50)) is **not** a pairing guard.
It asserts only `len(images) == len(gts)` and then drops any *positional pair* whose PIL sizes differ.
A mis-pairing between two images of identical dimensions passes silently. This is exactly the landmine
the brief names.

**Measured facts that make the invariant hold for this injection:**

| Check | Result |
|---|---|
| Stem sets of `output/.../images` and `output/.../masks` | **identical**, 4447 each |
| Stem sets of `Source/HKU-IS/Image` and `Source/HKU-IS/GT` | **identical**, 4447 each |
| All three pools' stem sets (raw / authors / local, `SOD_` prefix stripped) | **identical**, 4447 |
| Base-pool stems | numeric, e.g. `0004` … `5555` (ASCII `0x30-0x39`) |
| Added-pool stems | `SOD_<numeric>` (leading `S`, `0x53`) |

Because base stems begin with a digit and added stems begin with `S`, the *entire* base block sorts
before the *entire* added block in **both** lists, and within each block every filename in `Image/`
carries one extension and every filename in `GT/` carries one extension — so relative order is
identical. **Parity holds.** But it holds *by a property of these names*, not by any code guarantee.

**Three assertions the arm-construction script must make** (mandatory, not optional):

1. `sorted(stem(f) for f in Image/) == sorted(stem(f) for f in GT/)` — the real invariant. Extension
   differences are harmless *only* while the stem sets match exactly.
2. **No stem appears twice with different extensions** in `Image/` (e.g. both `X.jpg` and `X.png`).
   That is the one construction that provably breaks parity, and it is easy to create by accident when
   mixing a `.jpg` render pool with a `.png` CLS output.
3. **After** `SrcDataset` is constructed, re-derive the pairing and assert
   `stem(ds.images[i]) == stem(ds.gts[i])` for **all** i — not a sample. This is a 3-line check that
   costs nothing and is the only thing standing between the campaign and a silently mis-labelled
   training set.

### A fourth, separate hazard the brief did not name
`filter_files()` **silently drops** any positional pair whose PIL sizes differ. Renders and masks match
in size (measured, 6/6), so no drop is expected — but if a drop ever occurs, the pool shrinks *and the
parity of everything after it shifts*. **Assert `len(dataset) == expected` after construction.** The
loader already prints the count ([Dataloader.py:202](Src/utils/Dataloader.py#L202)) — capture it and
compare, do not eyeball it.

**STATUS: settled**, conditional on the three assertions above being implemented.

## 2.5 The target set

### DECISION
`Dataset/Target/Image`, **4040** `.jpg` — 3040 COD10K + 1000 CAMO (measured by prefix:
`COD10K*` = 3040, `camourflage*` = 1000). Consumed by
[MyTrain.py:297-300](MyTrain.py#L297-L300) → `get_tarloader` and by
[CLS.py:81-84](CLS.py#L81-L84) with `gt_root=None`.

### PREMISE CORRECTION 3 — the 7 exclusions do **not** apply to training
The brief asks to confirm the target set is *"4,040 images with the 7 D2-leaked names excluded."*
Those two halves are inconsistent, and the distinction matters:

- All **7** leaked names are **present** in `Dataset/Target/Image` — verified individually, 7/7 True.
  So the on-disk target set is 4040 **including** them.
- The exclusion is applied **downstream, in the analysis only**. B1's cluster CSV sums
  `n_target = 4033` and `n_target_scored = 4033` (= 4040 − 7) across its 75 clusters, while E0's cache
  `dinoL518_names.json['tgt']` holds all **4040**. Consumers read
  `rebuild/D2/out/d2_leaked_names.json` (`n_target_excluded: 7`); nothing hardcodes a name list
  (REBUILD_PLAN §0.2; C1 Gate 5).
- **Training reads all 4040.** That is the published S2R-COD protocol, and D2 §3.5 measured the impact:
  removing the 7 moves endpoint MAE by **−1.242e-05 (0.0167 % relative)**, their mean percentile in the
  clean set is **0.4761** (0.5 = indistinguishable), so there is **no memorisation signature**.

**Recommendation: leave the training target set at 4040 and disclose it.** Dropping 7 images to make
the training set "clean" would (a) change `total_step` from `⌈4040/16⌉ = 253` to `⌈4033/16⌉ = 253`
(no change, so no benefit), (b) deviate from the protocol the reproduced Table 1 rests on, and (c)
leave the *near*-duplicate contamination untouched anyway — D2 §5 is explicit that its sweep is a
**lower bound** and that rescaled copies are invisible to it. The analysis-side 4033 stays as it is.

**STATUS: settled**, with the premise corrected. Flag for the paper: "target set 4040; 7 exact
COD10K-test duplicates present and disclosed, measured impact 0.017 % relative MAE; CHAMELEON withdrawn
at 53.9 % contamination."

---

# 3. The three arms — exact construction, and what must be held identical

## 3.1 Arm A (baseline): is it pool-size-matched, and what follows

### DECISION
As conventionally defined (base pool only, no additions), **arm A is NOT pool-size-matched to B and C**,
and the consequence the brief anticipates is real and now quantified.

### EVIDENCE — the mechanism, computed
`total_step = min(len(source_loader), len(target_loader))` when `method != 'source_only'`
([MyTrain.py:306-307](MyTrain.py#L306-L307)); `zip()` truncates to the shorter loader
([MyTrain.py:51,53](MyTrain.py#L51-L53)).

| B (added) | `len(src)` | `len(tar)` | `total_step` | imgs seen/epoch | **per-image exposure** |
|---|---|---|---|---|---|
| **0 (arm A)** | 278 | 253 | **253** | 4048 | **0.9103** |
| 250 | 294 | 253 | **253** | 4048 | 0.8618 |
| **1000 (arms B/C)** | 341 | 253 | **253** | 4048 | **0.7432** |
| 2000 | 403 | 253 | **253** | 4048 | 0.6279 |
| 4447 | 556 | 253 | **253** | 4048 | 0.4551 |

**The step count never changes. The mixture does.** At B = 1000, every base image is seen **0.743×
per epoch in arms B/C against 0.910× in arm A — arm A gives each base image 22 % more exposure.** So
A-vs-B confounds "1000 more images" with "22 % less exposure per base image", in the direction that
*disfavours* B and C. This is `C2_RESULTS`-in-waiting: REBUILD_PLAN §C2 already records "Arm A is
**not** a clean control … only B-vs-C is clean."

### RECOMMENDATION — pad arm A, and pad it with duplicates, not with new content

Three options, in increasing strength:

| Option | Construction | What A-vs-B then isolates |
|---|---|---|
| **A0** unpadded | base 4447 only | nothing cleanly — mixture *and* exposure both move |
| **A1** duplicate-padded | base 4447 + **B duplicates of B uniformly-random base images** (new filenames, same pixels, same masks) | pool size and exposure matched ⇒ A-vs-B isolates **"is a LAKE-RED re-render worth more than a repeat of an image already in the pool?"** |
| **A2** foreground-matched | base 4447 + **the authors'-pool images of exactly the foregrounds arm B selected** | as A1, but the *foregrounds* are matched too ⇒ A-vs-B isolates **"is a new background render worth anything at all?"** — the sharpest possible statement of the Stage-C premise |

**I recommend A2, with A0 also run if budget allows.** A2 is the same cost as any other arm and turns
the weakest comparison in the campaign into the strongest: it holds the foreground set, the pool size,
the step count and the per-image exposure all constant, so the *only* difference between A2 and B is
that B's added images have LAKE-RED backgrounds and A2's have the authors' backgrounds. Given D1 §3.3
("the foreground pool is exhausted; the background is not"), that is precisely the degree of freedom
the whole method depends on — and no experiment in the rebuild has measured whether it buys anything.

Mechanics for A2: for each of arm B's selected stems `s`, copy `Source/HKU-IS/Image/<s>.jpg` →
`ARM_A2/Image/DUP_<s>.jpg` and `Source/HKU-IS/GT/<s>.png` → `ARM_A2/GT/DUP_<s>.png`. `DUP_` sorts after
digits and before `SOD_` in both lists, so parity holds — **and must still be asserted per §2.4.**

**Caveat, stated because it cuts against my own recommendation:** A2 makes arm A depend on arm B's
selection, so arm A is no longer a fixed reference shared across seeds unless arm B's selection is
itself seed-independent. Arm B's selection **is** a random draw, so either (i) fix arm B's foreground
draw across all three seeds (selection is then not seed-varying — cleaner pairing, less coverage of
selection noise), or (ii) let it vary and accept that arm A2 varies with it. **This sub-choice is
UNRESOLVED and yours** — see §5 and §7.

**STATUS: needs-your-call** (A0 / A1 / A2, and if A2, the seed-coupling sub-choice).

## 3.2 Arm B (random)

**DECISION.** `B` images = the *existing* local renders of `B` foregrounds drawn **uniformly without
replacement** from the same 4447-item pool arm C draws from, in the same order-independent way. This
matches C1's random arm exactly: *"a uniform draw without replacement of the same size B from the same
4447-item pool, in the same embedding space"* (REBUILD_PLAN §C1; implemented in
`rebuild/C1/c1_targeted_vs_random.py`). Draw RNG must be a **named, logged seed**, separate from the
training seed.

**STATUS: settled** except for `B` itself (§5).

## 3.3 Arm C (targeted)

**DECISION.** Reproduce C1's arm exactly, from the committed artifacts, and emit the selected stem list
as a tracked file before any training starts:

1. Read `rebuild/B1/out/b1_cluster_es_dinoL518.csv` → 75 rows, column **`target_es`**
   (range 0.018391–0.070668). **Do not re-cluster** (C1 Gate 2).
2. `p = softmax_alloc(es, α)`: `T = α · sd(es)`; `w = exp((es − max(es)) / T)`; `p = w / Σw`
   — [c1_targeted_vs_random.py:75-81](rebuild/C1/c1_targeted_vs_random.py#L75-L81).
3. `alloc = largest_remainder(p, B)` — integer allocation summing exactly to `B`, ties by ascending
   cluster index ([:84-95](rebuild/C1/c1_targeted_vs_random.py#L84-L95)).
4. `rank_by_centroid`: cosine of every **R2 grey-128 cutout** (4447 × 1024, row-aligned to the raw
   pool) against every cluster centroid; per-cluster descending order, stable ties
   ([:127-135](rebuild/C1/c1_targeted_vs_random.py#L127-L135)).
5. `greedy_select(alloc, order_idx, serving)` with the **`desc_nc`** serving order (C1's primary:
   clusters served in descending allocation size, ties by index), skipping already-taken images
   ([:138-181](rebuild/C1/c1_targeted_vs_random.py#L138-L181)).
6. Map index `i` → raw stem → `output/HKU-IS/images/SOD_<stem>.jpg` + `masks/SOD_<stem>.png`.

**Serving order is a real free parameter, and C1 measured its cost:** `cells_ORDER_SENSITIVE = 87` of
264, `max_d_order_spread = 0.18002`, with 2 of the 4 peak cells flagged (`C1_RESULTS.md` §5). Fix
`desc_nc` and **log it**; the point estimate moves by up to 0.18 in *d* across orders even though the
band does not.

**STATUS: settled** except `B` and `α` (§5).

## 3.4 Everything that MUST be identical across arms

| # | Must be identical | Where it is set | Silent-drift risk |
|---|---|---|---|
| 1 | `--network` | [MyTrain.py:193](MyTrain.py#L193) | — |
| 2 | `--method ours` | [MyTrain.py:204](MyTrain.py#L204) | a stray `--method` silently forces `--iteration 1` ([:236-238](MyTrain.py#L236-L238)) |
| 3 | `--iteration` | [MyTrain.py:203](MyTrain.py#L203) | see #14 |
| 4 | epochs / batch / lr / decay | self-set [:249-272](MyTrain.py#L249-L272) | **cannot drift from the CLI** — genuinely safe |
| 5 | α / u / τ / a / b / c | [:225-231](MyTrain.py#L225-L231) | overwritten after parsing — genuinely safe |
| 6 | Seed → init, shuffle order, augmentation | [:242](MyTrain.py#L242) | **hardcoded 42; needs the §7 patch** |
| 7 | Base pool (4447 + masks) | [:232](MyTrain.py#L232), [:292-293](MyTrain.py#L292-L293) | must be **byte-identical** across arms — hash it per arm |
| 8 | Target pool (4040) | [:297-300](MyTrain.py#L297-L300) | must not be filtered per arm |
| 9 | `total_step` = 253 | [:306-307](MyTrain.py#L306-L307) | **verified invariant in B** (§3.1 table) — assert it from the log |
| 10 | Checkpoint-selection set = CAMO 250 | [:302-304](MyTrain.py#L302-L304), [:322-324](MyTrain.py#L322-L324) | val only runs when `epoch_iter > 20` |
| 11 | `Tea_epoch_best.pth` selection rule (min val MAE) | [:181-188](MyTrain.py#L181-L188) | — |
| 12 | Eval protocol (endpoints, metrics, code path) | §6 | — |
| 13 | **`B`** (budget) | arm construction | **must be equal in B and C** — see §5 |
| 14 | **CLS output directory** | [CLS.py:16](CLS.py#L16) | **★ THE BIG ONE — see §10.1** |
| 15 | Backbone init file | `Src/model/SINet/resnet50-11ad3fa6.pth` | assert its hash once |

### Things in the code that WOULD silently differ — flagged

**(a) `Tea_epoch_best.pth` may not exist.** Validation runs only for `epoch_iter > 20`
([MyTrain.py:322](MyTrain.py#L322)) and `best_teamae` is initialised to 1 with the `epoch == 1` branch
([:181-186](MyTrain.py#L181-L186)) that can never fire under that guard — so `best_teamae` stays 1 and
the first validated epoch always saves. It will exist for a completed run. But **CLS falls back to
`Tea_40.pth` if it is missing** ([CLS.py:65-75](CLS.py#L65-L75)), so a killed run silently changes
which teacher generates pseudo-labels. Assert `Tea_epoch_best.pth` exists after every round.

**(b) Round 2 overwrites round 1 in place.** Both rounds write `Tea_epoch_best.pth`,
`Stu_40.pth`, … to the same `--save_model` path ([MyTrain.py:141-151](MyTrain.py#L141-L151)).
`preflight.py:432-440` already WARNs on a non-empty snapshot dir. **Use a fresh, per-(arm, seed)
`--save_model` directory** and archive round 1's checkpoints if you want them.

**(c) With `--iteration 2`, the round-2 source pool differs across arms in a second, uncontrolled
way.** CLS selects target images by `edge_loss < u · avg_loss` ([CLS.py:139](CLS.py#L139)) using the
arm's *own* round-1 model, so each arm appends a different number of differently-pseudo-labelled
images. That is legitimately part of "closed-loop", but it means arms differ in **two** places, not
one, and the second is high-variance. **Log the round-2 pool size per arm per seed** (it is printed by
[Dataloader.py:202](Src/utils/Dataloader.py#L202)); if the arms' round-2 pool sizes differ by more
than a few percent, that is a confound to report, not to hide.

**(d) `adjust_lr` compounds, and for SINet-v2 it compounds catastrophically.**
[tool.py:36-39](Src/utils/tool.py#L36-L39) does `param_group['lr'] *= decay` where
`decay = decay_rate ** (epoch // decay_epoch)`, applied **every** epoch — it is a repeated
multiplication, not a one-shot step. Computed exactly:

| Network | schedule | lr at the last epoch run |
|---|---|---|
| SINet | 1e-4, decay 0.1 @ 30, epochs 1–39 | 0.1 applied on each of epochs 30–39 ⇒ **1e-14** |
| SINet-v2 | 1e-4, decay 0.1 @ 50, epochs 1–99 | 0.1 applied on each of epochs 50–99 ⇒ **1e-54** |

This is upstream behaviour and identical across arms, so it is **not** a threat to the comparison. But
three consequences matter for the paper:

1. **Do not describe the schedule as "step decay at epoch 30/50."** It is a compounding decay that
   freezes the model.
2. **SINet-v2's last 50 of 99 epochs do essentially nothing** — its effective training length is ~49
   epochs, and half of its 2.2 GPU-h per run is spent at a learning rate of order 1e-30 or below.
   If SINet-v2 becomes the robustness architecture (§1), this is worth stating; it also means its
   per-run cost could be halved with no effect, though that would be a deviation.
3. **σ_within (§6.3) will be near-zero for both networks** because the late-epoch checkpoints are
   nearly identical models. It is a valid *lower bound* on run-to-run σ and nothing more — REBUILD_PLAN
   §5(c) item 7 already flags reporting it as if it were σ_seed as the exact failure to avoid.

**(e) `preflight.py` hard-codes the expected counts.** [preflight.py:286-287](preflight.py#L286-L287)
expects 4447 source images and 4447 source GT. Injected pools will trip it. Update it per arm or its
FAIL becomes noise you learn to ignore — which is worse than not running it.

**STATUS: settled** as an enumeration. Items 6, 13, 14 are the open ones and are handled in §5, §7, §10.

---

# 4. The embedder for clustering / selection

## DECISION
**Primary: `dinoL518`, k = 75, allocating by `target_es`.** Confirmed present and enforced.

## EVIDENCE

| Check | Result |
|---|---|
| `rebuild/B1/out/b1_cluster_es_dinoL518.csv` exists | ✓ 75 data rows |
| `target_es` column present and populated | ✓ **75 / 75**, range 0.018391 – 0.070668 |
| `n_target` / `n_target_scored` sums | **4033 / 4033** (= 4040 − 7 leaked) |
| Cutout cache row-aligned to raw pool | ✓ `cutout_rows: 4447`, `cutout_dim: 1024`, `cutout_aligned_to_raw: true` — `rebuild/B1/out/b1_c1_readiness.json` |
| C1 reads `target_es`, **not** `test_es` | [c1_space.py:70](rebuild/C1/c1_space.py#L70) `es = [float(r['target_es']) …]`; docstring `:21` names it "the signal" |
| Enforced, not merely done | `rebuild/C1/c1_preflight.py:13,65,148-185` — **Gate 1**, `BANNED_SIGNAL = 'test_es'`, an AST scan that HALTs if `test_es` appears anywhere in C1 |
| Both columns exist in the CSV | ✓ `target_es` **and** `test_es` — hence the gate |

**Why `target_es` and not `test_es` matters quantitatively:** `test_es` correlates with endpoint MAE at
ρ = **+0.8754**; `target_es` at **+0.6284** on the *identical* clusters (`B1_RESULTS.md` §D2). The two
signals agree only moderately per cluster (ρ = 0.5732). Allocating by `test_es` would use a signal the
pipeline does not possess at allocation time and would overstate the usable signal by ρ ≈ 0.25.

## Do the training arms need a dinoL224 repeat?

`B1_RESULTS.md` §C6 makes the dinoL224 sensitivity re-run **mandatory for C1** — and C1 ran it (both
spaces, 4 cells, both REOPENS). The question here is different: does the *training* campaign need it?

**Recommendation: NO for the primary campaign. Yes only as a contingency.** Reasoning:

- The reason C1 needed both spaces was that the choice *propagates* into a measurement C1 cannot
  redo. For training, the analogous risk is that arm C's *selection* is embedder-specific. C1 measured
  that directly: `d_heldout` at peak is **+1.1135** (dinoL518 R2) vs **+1.2325** (dinoL224 R2), both
  REOPENS, both CIs disjoint from zero, and the verdict is embedder-independent (`C1_RESULTS.md` §1,
  declared threshold PASS).
- More decisively, C1's **attribution audit** (§8) showed the *d* is produced by **concentration, not
  targeting** in *both* spaces: targeted − ES-shuffled = **+0.0073** (ES wins 13/20, a coin flip);
  targeted − arbitrary-cluster = **−0.0649** (ES wins 4/20). If the ES signal contributes ~0.6 % of
  the effect in both spaces, the embedder choice cannot plausibly flip a *training* outcome that the
  signal barely moves.
- **Cost if you disagree:** dinoL224 doubles arm C only (arms A and B are embedder-free), so
  +3 runs per architecture = **+5.3 GPU-h** for SINet, **+6.6** for SINet-v2. That is 2 % of the
  budget — genuinely cheap.

**The contingency that would force it:** if arm C shows a *positive* effect on the primary space, the
first question a reviewer asks is whether it survives the other space. **Pre-register the dinoL224
arm-C re-run as conditional on a positive primary result.** That costs nothing now and removes the
worst version of this problem (choosing to run it *after* seeing a result you like).

`clipL224` is **disqualified** — silhouette curve falls monotonically from k5 = 0.0568 to
k150 = 0.0357, so its k* = 5 is a grid-edge artifact, not an interior maximum; at k = 5 Spearman takes
only a few discrete values (its ρ(MAE) is exactly +1.0000). `B1_RESULTS.md` §C3; C1 Gate 3.

**STATUS: settled** for the primary. The conditional dinoL224 re-run is **needs-your-call**, and my
recommendation is to pre-register it as conditional rather than run it unconditionally.

---

# 5. k (number of clusters) and B (budget)

## 5.1 k

### DECISION
**k = 75**, inherited from B1's committed partition. **Arm C must not re-cluster.**

### EVIDENCE
- Silhouette peaks at **0.16** at k = 75 for dinoL518, and it is a genuine **interior** maximum
  (`B1_RESULTS.md` §4, §C3). Sweep: k5 = 0.0566, k20 = 0.1326, **k75 = 0.16**, k150 = 0.1507.
- Structure is weak in every space: peaks **0.1465 / 0.1600 / 0.0568** (dinoL224 / dinoL518 /
  clipL224), all far below 0.25. `THRESHOLD WEAK CLUSTER STRUCTURE is embedder-robust → PASS`.
- Reproducibility is moderate at best: bootstrap ARI **0.579**, seed ARI **0.616** at k = 75.
- Only **50 of 75** clusters clear the 15-endpoint-image floor (verified: 50 rows with `n_test ≥ 15`),
  so 25 clusters contribute no per-cluster endpoint statistic.
- Enforced by C1 Gate 2 (`BANNED_CLUSTER_MODULES = {'sklearn.cluster'}`, banned `fit_kmeans`).

### Should the result be checked at a second k?

**Recommendation: no second k for the training arms. Report the k-sensitivity from C1 instead.**

- C1 already swept `α` at fixed k in both spaces (k = 75 and k = 50), and **both** give REOPENS. The
  k-axis is therefore already covered by the *selection-space* measurement, which is where k acts.
- The honest statement B1 itself makes is that **no k is strongly supported by the data**
  (`B1_RESULTS.md` §8: *"the honest statement is that no k is strongly supported"*). Running training
  at a second k would produce two equally weakly-grounded numbers, not a resolution. It would also
  double arm C again.
- **What to write in the paper instead:** "the allocation is over a partition with silhouette 0.16
  and bootstrap ARI 0.58 — the unit of allocation is soft, and C1 measured that arm C's separation
  from arm B is reproduced by an allocation with the ES values permuted across those clusters."
  That is a stronger and more falsifiable disclosure than a second k.

**STATUS: settled**, with the k-sensitivity discharged by citing C1 rather than by more training runs.

## 5.2 B (budget)

### DECISION — recommendation, but the number is genuinely yours

**Recommend B = 1000, identical in arms B and C (and in a padded arm A).**

### EVIDENCE — the full B-curve, and why the peak is not the right operating point

`d_heldout` is **monotone decreasing** in B (dinoL518, R2, max over α; `C1_RESULTS.md` §3):

| B | max \|d\| | clusters funded | max alloc share |
|---|---|---|---|
| 250 | **+1.172** | 1 | 1.00 |
| 500 | +0.930 | 25 | 0.51 |
| **1000** | **+0.797** | **40** | **0.51** |
| 2000 | +0.476 | 4 | 0.82 |
| 3000 | +0.244 | 2 | 1.00 |
| **4447** | **−0.347** | 1 | 1.00 |

The argument for **B = 1000**, in order of weight:

1. **The peak (B = 250) is degenerate.** At B = 250 the max-|d| cell funds **1 cluster** with
   `max_alloc_share = 1.00` — the entire budget in one cluster, flagged `degenerate = 1` in
   `c1_cells.csv`. That is not "targeted generation"; it is "generate 250 images near one centroid".
   Training on it would test a caricature of the method.
2. **B = 1000 is the only budget where the arm is both well-separated and non-degenerate.** At
   B = 1000, α = 0.5: `d_heldout = 0.797` [CI 0.616, 0.968], **40 of 75 clusters funded**,
   `max_alloc_share = 0.509`, `degenerate = 0`. Verified directly from `c1_cells.csv`.
3. **It is the budget the old package proposed**, so B-vs-C is directly comparable to the claim being
   revised, and C1 measured `d` there specifically (0.655–0.830 across all four cells, all REOPENS).
4. **The brief's own bound is correct and is the strongest reason not to agonise.** Because
   `total_step` is pinned at 253 for every B (§3.1, verified arithmetically), **B changes the mixture
   and not the step count.** So B's entire effect is `4048/(4447+B)` — the per-image exposure — and it
   is bounded and monotone. Doubling B to 2000 drops exposure to 0.628 and drops `d` to 0.476: both
   axes move *against* detecting an effect. There is no B at which the effect gets easier to see.

**Flagged, as the brief requires: B must be IDENTICAL in arms B and C.** If it is not, the comparison
measures budget, not targeting. Assert `len(arm_B_selection) == len(arm_C_selection) == B` and log both.

### UNRESOLVED — α (the allocation temperature) has no specified operating point

**This is the one thing in the brief that has no answer in any committed artifact, and it is not
minor.** C1 **swept** α over 11 values (0.02 … 40) and never designated one. Arm C cannot be built
without picking one. At B = 1000, dinoL518 × R2 (from `c1_cells.csv`, verified):

| α | clusters funded | max alloc share | `d_heldout` | degenerate |
|---|---|---|---|---|
| 0.02 | 1 | 1.000 | 0.759 | **yes** |
| 0.05 | 2 | 0.998 | 0.768 | **yes** |
| 0.1 | 2 | 0.960 | 0.746 | **yes** |
| 0.2 | 4 | 0.822 | 0.777 | no |
| **0.5** | **40** | **0.509** | **0.797** | no |
| 1.0 | 75 | 0.194 | 0.642 | no |
| 2.0 | 75 | 0.063 | 0.550 | no |
| 40.0 | 75 | 0.015 | 0.522 | no |

Three defensible choices, and they are **not** equivalent:

- **α = 0.5** — the maximum non-degenerate `d` at B = 1000. Strongest test of "does a maximally
  distinct targeted set help?" **But** it is chosen by maximising the very quantity C1's audit showed
  measures *concentration*, so it maximises the confound.
- **α = 1.0** — `T = sd(es)`, the scale-free natural choice; funds all 75 clusters,
  `max_alloc_share = 0.194`. This is what "allocate proportionally to weakness" means without a tuned
  knob. **But** `d` falls to 0.642 and the cell is `ci_straddles_band = 1` / AMBIGUOUS.
- **α from the old package's grid** — `T ∈ {0.005 … 0.05}`, which REBUILD_PLAN §0.2 explicitly
  **discarded** as an unjustified inherited constant. Not available.

**My recommendation: α = 1.0, with α = 0.5 as a pre-registered secondary if you can afford 3 more
runs.** α = 1.0 is the only choice justifiable *without reference to the outcome being measured*, and
that is the property this rebuild exists to protect. If arm C is to be reported as "the method", it
should be the method's natural operating point, not the point that maximised a separation metric whose
own audit says it measures the wrong thing.

**STATUS: B = 1000 — needs-your-call but with a clear recommendation. α — UNRESOLVED, and it needs
your decision before arm C can be constructed. What is needed: nothing measurable, this is a design
choice; it must simply be declared and logged before training, not after.**

---

# 6. Evaluation protocol

## 6.1 Endpoints

### DECISION
**Primary: COD10K-test (2026). Secondary: NC4K (4121). CHAMELEON excluded. CAMO is the
checkpoint-selection set and can never be an endpoint.**

### EVIDENCE

| Endpoint | On disk | Contamination (D2, lower bound) | Role |
|---|---|---|---|
| COD10K test | `Dataset/Test/COD10K/{Imgs,GT}` 2026 + 2026 | **2/2026 = 0.1 %** near-dup; 7 exact, MAE impact −1.24e-05 | **primary** |
| NC4K | `Dataset/Test/NC4K/{Imgs,GT}` 4121 + 4121 | **1/4121 = 0.0 %** | **secondary** |
| CHAMELEON | 76 + 76 (+ Edge) | **41/76 = 53.9 %** — quantization tables differ in 41/41 pairs; nearest-distance gap 41 below 5.51, next at 40.58 (a 7.4× jump) | **REMOVED, not caveated** |
| CAMO | `Dataset/Val/CAMO/{Imgs,GT}` 250 + 250 | 4/250 = 1.6 % | **checkpoint selection only** — [MyTrain.py:221](MyTrain.py#L221), [:302-304](MyTrain.py#L302-L304), [:322-324](MyTrain.py#L322-L324); it is the published CAMO **test** split |

CAMO is identical across arms so it cannot bias B-vs-C, but it must never appear as a result
(`D2_RESULTS.md` §3.6).

**STATUS: settled.**

### ⚠ Blocking: NC4K is not currently evaluable without a code change
[MyTest.py:47](MyTest.py#L47) iterates `for dataset in ['COD10K']` and
[:51-52](MyTest.py#L51-L52) hard-codes `./Dataset/Test/Image/` and `./Dataset/Test/GT/` — with a
`.format(dataset)` on strings that contain **no placeholder**. Those two directories **do not exist**
(verified: `No such file or directory`); they were COD10K and were removed. So:

- COD10K eval currently requires pointing `MyTest.py` at `Dataset/Test/COD10K/{Imgs,GT}`.
- NC4K eval requires a dataset argument that does not exist.
- `Eval/MyEval.py` has the mirror problem: `--data_lst` / `--model_lst` are `type=list`
  ([MyEval.py:141,146](Eval/MyEval.py#L141-L146)), so a string argument is exploded into characters.
  The committed runs worked only because the defaults are `['']`, which makes
  `gt_src = os.path.join(gt_root, '', 'GT')` — i.e. `--gt_root ../Dataset/Test/COD10K` and let the
  default `['']` do the rest. **`--data_lst COD10K` will silently do the wrong thing.**

**Both are small, mechanical patches, and both must exist before the first run finishes.** Flagged
here rather than in §10 only because they block reporting, not training.

## 6.2 Metrics and the quantization question

### DECISION
Use `Eval/metrics.py` via `Eval/MyEval.py`. **MAE, Sα, Fβw all report and are quantization-free.
Eφ requires a choice of variant.**

### PREMISE CORRECTION 4 — `Eval/metrics.py` needs no rounding fix
The brief says metrics should come from `Eval/metrics.py` *"with the rounding (not truncation) fix B1
found."* That fix does not belong to `Eval/metrics.py`, and applying one there would be wrong.

What B1 actually found (`B1_RESULTS.md` §6.4, `REVISION_TABLE.md` R6): B1's *own* scoring script
recomputed predictions **in memory** and wrote `(cam*255).astype(np.uint8)` (truncation), while
[MyTest.py:76](MyTest.py#L76) writes them with `cv2.imwrite(path, cam*255)`, and OpenCV's float→uint8
conversion **rounds**. The 0.5-grey-level bias made B1's endpoint MAE 0.073237 against D2's
independently measured 0.074463 — a 1.23e-03 miss that failed a declared threshold. The fix was
`np.round` **in B1's script**, after which MAE matched to 2.3e-07 and Sα became 0.717216 (matching the
recorded 0.7172).

`Eval/MyEval.py` reads the **already-rounded PNG** off disk
([MyEval.py:33-34](Eval/MyEval.py#L33-L34), `cv2.imread(..., IMREAD_GRAYSCALE)`), so it inherits
MyTest's rounding for free. **The rule for the campaign: any script that scores from a checkpoint
in memory must use `np.round(cam*255)`. Scripts that score from written PNGs must not add anything.**

### PREMISE CORRECTION 5 — two of the reported metrics *do* truncate, and it is not the ones you'd guess
Read from the source:

| Metric | Path | Quantized? |
|---|---|---|
| **MAE** | `metrics.py:90-106` | **no** — float throughout |
| **Sα** | `metrics.py:109-218` | **no** — float throughout |
| **Fβw** | `metrics.py:333-397` | **no** — float throughout |
| `adpFm`, `adpEm` | adaptive threshold on the float array ([`:51-53`](Eval/metrics.py#L51-L53), [`:235-237`](Eval/metrics.py#L235-L237)) | **no** |
| `meanFm` / `maxFm` | `metrics.py:64` — `pred = (pred*255).astype(np.uint8)` inside `cal_pr` | **YES, truncates** |
| `meanEm` / `maxEm` | `metrics.py:274` — same, inside `cal_em_with_cumsumhistogram` | **YES, truncates** |

So *"MAE / Sα / Fβw / Eφ all report"* is true — but **Eφ is ambiguous**: `adpEm` is clean and
`meanEm` / `maxEm` truncate at the 256-bin histogram. `Eval/Eval/eval_txt/**` shows all three columns.
**Decide and declare which Eφ the paper reports.** I recommend `meanEm` (the field convention) with
the truncation disclosed, or `adpEm` if you want the quantization-free number. Do not mix them across
tables.

### PREMISE CORRECTION 6 — the reported precision is too coarse for this comparison
[MyEval.py:76](Eval/MyEval.py#L76) writes every metric with `.round(4)`. With σ(Sα) ≈ 0.0036, a
1e-4 quantum is ~2.8 % of σ — tolerable for a single number, **not** tolerable for a paired 3-seed
difference where the expected gap is itself of order σ. **Emit full float precision** (drop the
`.round(4)`, or capture the raw `sm`/`wfm`/`mae`/`em` values) and round only for the printed table.

### Also flagged
[MyEval.py:37-38](Eval/MyEval.py#L37-L38) calls `cv2.resize(pred_ary, (w,h), cv2.INTER_NEAREST)` —
`cv2.INTER_NEAREST` lands in the **third positional slot, which is `dst`, not `interpolation`**. It is
inert here because [MyTest.py:72](MyTest.py#L72) upsamples predictions to the GT shape before writing,
so shapes never mismatch. **Assert `pred.shape == gt.shape` for all 2026 / 4121 rather than relying on
that.**

**STATUS: settled**, with three corrections and one open sub-choice (which Eφ).

## 6.3 The noise floor

### DECISION — and the brief's number is real, reproducible, and **the wrong bar**

**σ(Sα) = 0.003555** is confirmed and exactly reproducible. It is **not** the right bar for a 3-seed
paired comparison. Use a **within-arm σ measured from these very runs.**

### EVIDENCE — provenance, recomputed here from primary artifacts

The old `σ(Sα) = 0.00356` came from six rescued SINet runs. Their per-run metrics survive at
`_archive_stageC_old/evidence_artifacts/noisefloor_meta/audit6.json`, and recomputing from them here:

| Set | n | mean Sα | **sd (ddof=1)** | range |
|---|---|---|---|---|
| All six runs (s42, s43, s45, s46, repB, repC) | 6 | 0.700564 | **0.003555** | 0.696107 – 0.705831 |
| Distinct seeds only (s42, s43, s45, s46) | 4 | 0.698989 | **0.002856** | 0.696107 – 0.702217 |
| **Same seed, three repeats (s42, repB, repC)** | 3 | 0.703215 | **0.002287** | 0.701596 – 0.705831 |

So old claim C3.1 (0.00356) and C3.2 (0.00286) both **reproduce exactly**. Also recomputed:
σ(Fβw) = 0.008437, σ(MAE) = 0.003876 over the six.

### Why it is the wrong bar — three reasons, in increasing severity

1. **Different operating point.** All six ran `--iteration 1`
   (`noisefloor_meta/run.sh`, `run_rep.sh`: `--method ours --iteration 1 --seed $SEED`) and landed at
   Sα ≈ 0.6989–0.7058. The committed 2-iteration endpoint is **Sα = 0.7172**. A σ measured at Sα ≈ 0.70
   after one round is not a σ for runs at Sα ≈ 0.72 after two rounds plus a CLS step that itself varies
   per arm (§3.4c).
2. **Provenance.** These artifacts were rescued from a volatile `/tmp` scratchpad by the old package's
   `e0_rescue.py`; **none was produced by version-controlled code at the time it ran**
   (`_archive_stageC_old/README.md`). REBUILD_PLAN §0.2 discarded σ = 0.00356 **as an input** for
   exactly this reason. Re-importing it as the paper's detection bar would reinstate the practice the
   rebuild was built to end.
3. **★ The severe one: the third row of the table dismantles the design premise.** Three runs at
   **the same seed 42** differ by sd(Sα) = **0.002287** — that is **64 % of the across-seed sd of
   0.003555**. `torch.backends.cudnn.deterministic` is never set (only reported, at
   [preflight.py:198-199](preflight.py#L198-L199)), so **the same seed does not reproduce the same
   run.** Seed-matching therefore removes only ~36 % of the variance in quadrature terms, not most of
   it. A "seed-matched paired comparison" is much weaker than the phrase implies.

### RECOMMENDATION
Use **σ_within from the campaign's own runs** as the primary bar:

- With 3 seeds × 3 arms you get 3 replicates per arm. Compute the **pooled within-arm sd** across arms
  (df = 3 arms × 2 = 6) — this is the correct denominator, measured at the campaign's own operating
  point, on the campaign's own code, with no provenance debt.
- Use σ = 0.00356 (n = 6) and σ = 0.00229 (same-seed n = 3) **only as pre-registered priors** for
  power framing: *"we expect σ(Sα) ≈ 0.002–0.004 based on six archived runs; we will report the σ
  actually measured."* Cite them as archived-and-provenance-caveated, never as the bar.
- Also compute **σ_within (late-epoch)** as REBUILD_PLAN §C3 specifies —
  `Tea_{36,37,38,39,40}.pth` + `Tea_epoch_best.pth` from each run, six checkpoints, over COD10K. It is
  a *lower bound* on run-to-run σ, it is free (inference only), and it separates "the run is still
  moving" from "the arms differ". **Note the compounding-lr finding (§3.4d): by epoch 39 the lr is
  ~1e-13, so σ_within will be very small and must not be presented as σ_seed.** REBUILD_PLAN §5(c)
  item 7 flags exactly this trap.

**STATUS: settled** on what to use and why. The specific arithmetic depends on the decision rule (§6.4).

## 6.4 The decision rule — pre-registered

### DECISION — proposed, **requires your sign-off before the first run**

Declare all of this in a committed file before any training starts:

```
Primary endpoint  : COD10K-test, Sα, from Tea_epoch_best.pth of the final round.
Secondary         : NC4K, Sα. Reported; never used to decide.
Reported alongside: MAE, Fβw, Eφ(<variant chosen in 6.2>) on both endpoints.
Replication       : n = 3 seeds per arm, seeds {42, 43, 45}   [44 excluded: see below]
Noise estimate    : sigma_hat = pooled within-arm sd of Sα over all arms (df = n_arms x 2)

Gap definitions   : Delta_BA = mean(Sa_B) - mean(Sa_A)      [does added data help at all]
                    Delta_CB = mean(Sa_C) - mean(Sa_B)      [THE claim: does targeting help]

DECISION RULE (declared before training):
  REAL EFFECT       iff  Delta > 2 * sigma_hat   AND  sign consistent in 3/3 seeds
  WITHIN NOISE      iff  |Delta| <= 2 * sigma_hat
  REAL REGRESSION   iff  Delta < -2 * sigma_hat  AND  sign consistent in 3/3 seeds
  INCONCLUSIVE      iff  |Delta| > 2 * sigma_hat but sign NOT consistent in 3/3
                          -> report as INCONCLUSIVE, do not add seeds to break the tie
```

With the prior σ ≈ 0.00356, the bar is **ΔSα > 0.0071**; if σ_hat comes out nearer the same-seed
0.00229, the bar is **ΔSα > 0.0046**. For scale: the whole MT→Ours gap in this repo is
0.7030 → 0.7172 = **+0.0142 = 4.0 σ** at the prior σ — i.e. **twice the detection bar**. So **the
campaign can resolve an effect half the size of the paper's own headline improvement, and no
smaller.** State that as the sensitivity of the
experiment — it is the honest power statement, and it is the number a reviewer will want.

**Why `2σ` and not a t-test:** with n = 3 the t-critical value at 95 % is 2.92 (one-sided 2.35), so
`2σ` is *less* conservative than a formal test. If you want a formal test, use a **paired** test on
the seed-matched differences (`Sα_C(s) − Sα_B(s)` for s ∈ {42,43,45}) — but §6.3 reason 3 shows the
pairing is weak (same-seed sd is 64 % of across-seed sd), so the paired test buys less than it appears
to. **Recommendation: report `2σ_hat` as the primary rule, the paired differences as a table, and the
sign-consistency count. Do not report a p-value from n = 3.**

**Seed choice:** use **{42, 43, 45}**. Seed 42 is the repo's own hardcoded value, so arm A at seed 42
should land near the committed Sα = 0.7172 and gives a free sanity check. **Seed 44 failed in the
archived campaign** (`noisefloor_meta/train_s44.log` stops after the loader lines; `status.log` shows
`TRAIN_DONE seed=44` twice, i.e. it was retried) — avoid it, or if you use it, know it has a history.

**STATUS: needs-your-call — sign off on the rule verbatim, then commit it before the first run.** The
whole value of a pre-registered rule is destroyed if it is written after the numbers exist.

---

# 7. Seeds and determinism

## DECISION
**No `--seed` mechanism exists. The 2-line patch that adds one already exists, archived and previously
used.** The data pipeline is fully seed-deterministic; the GPU kernels are not, and that is measured.

## EVIDENCE — what exists

| Fact | Citation |
|---|---|
| No `--seed` argument in the parser | [MyTrain.py:192-222](MyTrain.py#L192-L222) — verified absent |
| Seed hardcoded to 42 | [MyTrain.py:242](MyTrain.py#L242) — `set_random_seed(42)` |
| What `set_random_seed` covers | [tool.py:24-28](Src/utils/tool.py#L24-L28) — `random.seed`, `np.random.seed`, `torch.manual_seed`, `torch.cuda.manual_seed_all` |
| No worker_init_fn anywhere | repo-wide grep: zero hits |
| cudnn determinism never set | repo-wide grep: only [preflight.py:198-199](preflight.py#L198-L199), which *reports* `cudnn.deterministic` and states "seed is 42 but runs are not bit-reproducible" |

**The patch already exists**, at
`_archive_stageC_old/evidence_artifacts/noisefloor_meta/MyTrain_seed.py`. Diffed against current
`MyTrain.py` — it is exactly two lines:

```
+ parser.add_argument('--seed', type=int, default=42, help='RNG seed (was hardcoded 42)')
- set_random_seed(42)
+ set_random_seed(opt.seed)
```

It was used to produce the six archived runs. **Reapply it to `MyTrain.py` in-tree** (do not copy a
separate `MyTrain_seed.py` — a second trainer is exactly how two arms end up on different code).

## EVIDENCE — what the seed actually controls, measured here, not assumed

Ran a probe in this repo's `.venv` replicating the loader's exact RNG usage
(`np.random.rand()` in `__getitem__` at [Dataloader.py:32](Src/utils/Dataloader.py#L32),
`shuffle=True`, `num_workers=6`, `batch_size=16`):

| Property | Measured |
|---|---|
| Shuffle order reproducible across processes at the same seed | **True** |
| Shuffle order differs across seeds (42 vs 43) | **True** |
| Shuffle order differs between epoch 0 and epoch 1 | **True** (correct — fresh base seed per epoch) |
| Augmentation (flip) stream reproducible at the same seed | **True** |
| Augmentation stream differs across seeds | **True** |
| Distinct flip values over 64 items | **64** across **4** worker PIDs — workers do **not** share one stream |

So **model init, shuffle order and augmentation are all fully seed-controlled.** (PyTorch seeds each
worker's numpy from `base_seed + worker_id`, and `base_seed` is drawn from the global torch RNG that
`torch.manual_seed` sets — so no `worker_init_fn` is needed. Good news that had to be checked rather
than assumed.)

**What is NOT controlled: the GPU kernels.** Quantified in §6.3: three runs at the *same* seed 42
differ by sd(Sα) = **0.002287**, against an across-seed sd of **0.003555**. `cudnn.deterministic` is
False and `cudnn.benchmark` is untouched.

### CONSEQUENCE FOR THE DESIGN — this is the most important finding in §7
"Same seed → same init/shuffle across arms, differing only in Stage C data" is **true for the data
pipeline and false for the run**. Two arms at seed 42 share their initialisation and their shuffle
order, but they do **not** share their kernel-level numerics, and that alone contributes 64 % of the
total observed sd. **Seed-matching is worth having — it is free — but it must not be described as
making the arms paired.** Report it as "seeds matched across arms; run-to-run nondeterminism measured
at sd(Sα) = 0.0023 at fixed seed, so the comparison is only partially paired."

**Optional strengthening, costed:** setting `torch.backends.cudnn.deterministic = True` and
`benchmark = False` would make the arms genuinely paired and could cut the noise floor by ~60 %,
turning the detection bar from ΔSα > 0.0071 into something nearer 0.003. Cost: typically 10–30 %
slower training (unmeasured here) and a deviation from released code that must be disclosed. **I
recommend doing this** — it is the single highest-leverage change available to the campaign's
statistical power, and it costs less GPU time than adding one architecture. But it is a deviation, so
it is **your call**.

## Total run count — what "3-seed" means

| Config | Arms | Seeds | Archs | **Runs** | GPU-h | Wall on 2 GPUs |
|---|---|---|---|---|---|---|
| Minimum (A, B, C) | 3 | 3 | 1 (SINet) | **9** | 15.7 | ≈8.6 h |
| **+ padded arm A2** | 4 | 3 | 1 | **12** | 21.0 | **≈11.5 h** |
| + SINet-v2 | 4 | 3 | 2 | **24** | 47.4 | ≈26 h |
| + conditional dinoL224 arm C | +1 arm | 3 | 1–2 | +3 / +6 | +5.3 / +11.9 | +3 / +6.5 h |
| + Oracle (if unblocked, §8) | +1 arm | 3 | 1 | +3 | +5.3 | +3 h |

Unit costs: SINet `--iteration 2` = **1.75 GPU-h** (measured, §1); SINet-v2 = **≈2.2 GPU-h**;
~9 % contention when both GPUs are busy. **Inference + evaluation are excluded from these totals and
are NOT measured** — see §10.2.

**STATUS: settled** on mechanism and totals. cudnn determinism is **needs-your-call**.

---

# 8. The Oracle arm — in or out

## DECISION
**OUT of this campaign. It is blocked on data that is not on this machine.**

## EVIDENCE
- **DUTS is absent.** Searched `/home/ai-server` to depth 8 and the repo tree: **zero** files or
  directories matching `*DUTS*`. The only mention anywhere is prose:
  `LAKE-RED/LAKERED_HKUIS_REPRODUCTION.md:303` — *"salient-object foregrounds came from DUTS and
  DUT-OMRON, not HKU-IS, and the exact contents of …"*.
- Disk is not the constraint: 1.5 T free on `/`.
- Generation is not the constraint: at the measured **1.77–1.85 s/image**, 1000 DUTS foregrounds cost
  **≈15 min on 2 GPUs**.
- Training is not the constraint: 3 seeds × 1.75 GPU-h = **5.3 GPU-h ≈ 3 h wall**.

**What is needed to unblock it** (all four, none of which exist here):
1. DUTS-TR images **and** binary masks on disk (DUTS-TR is 10,553 image/mask pairs, ~1–2 GB).
2. A leakage sweep of the chosen DUTS subset against COD10K-test and NC4K, at D2's standard —
   exhaustive within-dimension re-encode search, not name or hash matching. D2 §3.1 is the cautionary
   case: exact hashing called CHAMELEON clean at 0/76 when the true figure was 41/76. **A DUTS subset
   that has never been swept cannot enter a load-bearing arm.**
3. A staging pass through `prepare_lakered_inputs.py` with the polarity inversion, plus verification
   that DUTS masks are in SOD polarity (object = white) — a wrong assumption here silently inverts
   every object.
4. A decision on subset size and selection rule, so the Oracle arm's `B` matches arms B and C.

## Cost, both ways

| Path | Added runs | Added GPU-h | Added wall | Blocked on |
|---|---|---|---|---|
| **Fold in now** | 3 | 5.3 (+0.25 gen) | ≈3 h | **DUTS download + a full D2-standard leakage sweep** — days of *your* attention, not GPU hours |
| **Defer** | 0 | 0 | 0 | nothing |

**Recommendation: defer.** The GPU cost is trivial (2 % of budget) — the reason to defer is that the
Oracle arm's *only* value is as a clean test of foreground exhaustion, and that value is destroyed if
its data is not swept to the same standard as everything else. Adding it now means either delaying the
whole campaign behind a dataset acquisition, or admitting an unswept pool into the one campaign that
is supposed to be load-bearing. **Neither is worth 3 h of GPU time.** Run A/B/C now; fold Oracle in as
a follow-up once DUTS is on disk and swept — the campaign's seeds, arms and eval protocol will all be
committed by then, so it can be seed-matched retrospectively.

## Its honest scope, stated for the record
The Oracle arm tests **foreground exhaustion** — whether new foregrounds (which D1 §5 explicitly does
**not** rule out as helpful) change the outcome. It holds **LAKE-RED render quality fixed** — same
generator, same `--isReplace` compositing, same 48-scalar conditioning path. It does **NOT** test
RealCamo, and it does **not** test whether real camouflaged imagery would help. D1 §5 is the citation:
*"D1 does not establish that new foregrounds could not help. It bounds only what this pipeline can add
from its fixed pool."*

**STATUS: UNRESOLVED — data absent. Recommendation: defer, and say so in the paper's limitations
rather than leaving it implied.**

---

# 9. Current-state and ambiguity summary

## 9.1 Every result the A/B/C paper will depend on, and its status

| Result | Status | Log blocks | What the paper needs it for |
|---|---|---|---|
| **E0** — regenerated caches, render pool, manifests, 3 embedders | **COMMITTED** | 4 `EXP E0` | Provenance of every embedding; the 4447/4447 bit-exact render reproduction |
| **D2** — leakage sweep | **COMMITTED** | 5 `EXP D2` | CHAMELEON withdrawal (53.9 %); the 7-name exclusion set; the position-in-shard render mechanism |
| **D1** — foreground exhaustion | **COMMITTED** | 1 `EXP D1` | "the foreground pool is exhausted; the background is not" — the scope of any null |
| **B1** — is the weakness signal real | **COMMITTED** | 6 `EXP B1` | `target_es` as the allocation signal; k = 75; the ES→error effect size |
| **C1** — targeted-vs-random distance + attribution audit | **COMMITTED** | 4 `EXP C1` | *d* = 1.00–1.23 refuting *d* ≈ 0.10 — **and** §8's audit showing the *d* is concentration, not targeting |
| **A1** — the conditioning bottleneck | **UNRUN** | 0 | The "48 scalars" bound. `ddpm.py:1586` makes a **full-resolution second path** a live possibility; `A1.4` (`fg` under the mask is zero) was **never tested** |
| **A2** — background dominance | **UNRUN** | 0 | The "~82 % invented background" headline. *Partly* covered: E0 independently measured `staging_background_frac = 0.8087`, and D1 measured per-set fg fractions (0.19132 raw / 0.18557 auth) |
| **A3** — real-vs-generated separability **with controls** | **★ UNRUN** | 0 | **See 9.2** |
| **B2** — is the coverage term worth including | **UNRUN** | 0 | The measured basis for λ_cov = 0 |
| **B3** — does steering work, and by which representation | **UNRUN** | 0 | Whether targeting is *feasible* at all; the grey-128 vs render representation slip |
| **C2** — do budget or dynamics rescue it | **UNRUN as an experiment** | **3 `EXP C2` mentions inside C1 blocks** | Its load-bearing claim (`total_step` pinned) is provable from the in-repo logs and **I verified it here**: `total_step = 0253` at `training_log.log:2` (round 1) **and** `:1017` (round 2), with `0278` in `S2C_SO` as the control. The C2 *experiment* has produced no `EXP C2` block of its own; `\|Ds\|` remains UNVERIFIED |
| **C3** — noise floor and the effect-vs-noise verdict | **UNRUN** | 0 | The detection bar. **The A/B/C campaign largely supersedes it** — it measures σ directly instead of building a 2-D sensitivity surface |

Status source: `REVISION_TABLE.md` §"Completed so far: **E0, D2, D1, B1, C1**. Seven outstanding: A1,
A2, A3, B2, B3, C2, C3." Independently confirmed by counting log blocks in `results/REBUILD_LOG.txt`:
E0 = 4, D2 = 5, D1 = 1, B1 = 6, C1 = 4, C2 = 3 (all inside C1 blocks), **A1/A2/A3/B2/B3/C3 = 0**.

## 9.2 ★ A3 — explicitly flagged, as the brief requires

**A3 is UNRUN in the rebuild. It is NOT done, and it is NOT partially done.**

- Zero `EXP A3` blocks in `results/REBUILD_LOG.txt`.
- `REVISION_TABLE.md` §5: *"Every §4 row of `REBUILD_PLAN.md` belonging to A1, A2, A3, B2, B3, C2, C3
  remains untested."*
- What exists is the **old package's** A3 (commit `fb893d5`, *"evidence A3 experiment results"*),
  whose files were removed from the tree at commit `96fe223`. Three of its embedding caches survive
  in the archive (`a3_rawhkuis_L224_cls.npy`, `a3_tgt_jpeg75_L224_cls.npy`,
  `a3_tgt_dark20_L224_cls.npy`) — regenerable, but produced by no version-controlled script.
- Its old claims (REBUILD_PLAN §4) are all `[no code]`: A3.1 AUC 0.9989, A3.2 true null 0.4781,
  A3.3 JPEG-75 0.4117, A3.4 sorted-split 0.8888, A3.5 *d* 4.67/4.61/4.33, A3.6 recall 0.4662,
  A3.7 recall 0.7461, A3.8 delta −0.2799. **Measured column: empty for all eight.**
- Worse than merely unrun: REBUILD_PLAN §5(c) item 5 records that **every old A3 number came from the
  *local* re-generation, while the model trained on the *authors'* pool** — *"The authors' pool …
  has never been probed."*

**Consequence, stated as bluntly as the brief asks:** the claim *"LAKE-RED output is far from the real
target distribution"* **cannot go in the paper.** Not as a caveated claim, not as a footnote. A3's
whole design exists because a high real-vs-generated AUC is **near-vacuous** without controls —
REBUILD_PLAN's declared threshold is *"vacuity if any identity-preserving control exceeds AUC 0.90"*,
and the old package's own JPEG-75 control (0.4117) and true null (0.4781) sat at chance while the
headline was 0.9989. Whether that pattern survives on the **authors'** pool, with a stratified split
and ≥ 2 embedder families, is unmeasured.

A3 is inference-only, needs no training, and every input is present and hashed. **If the paper needs
that claim, A3 must run — it is hours, not days.** If it does not run, the sentence must be deleted,
not softened.

## 9.3 Everything else asserted-but-not-measured that the paper would lean on

| Assertion | Status | Why it matters |
|---|---|---|
| "The conditioning channel is 48 scalars (16 × 3)" | **UNMEASURED** (A1 unrun). `ddpm.py:1586` computes `fg2bg = self.fuse(cat((vec_bg, fg)))` — a 1×1 conv seeing **raw `fg`** — and `new_fg = fg*(1-mask) + fg2bg*mask` uses it inside the regenerated region. If `fg[mask==1]` is non-zero, there is a **second, full-resolution** path | This is the bound on how much of *any* selected difference can reach a render. If it is wrong, the mechanism story is wrong |
| "Targeting is feasible — selected foregrounds land in their target cluster above chance" | **UNMEASURED** (B3 unrun). Old 20.62 % held-out had *no script and no split of any kind* | Arm C presumes steering works. If B3 is at chance, arm C's premise fails **upstream of the training result** |
| "λ_cov = 0 is justified" | **UNMEASURED** (B2 unrun) | Only matters if the paper describes the full design |
| "σ(Sα) = 0.00356" | **reproducible but provenance-caveated and at the wrong operating point** (§6.3) | Would be the detection bar. Superseded by the campaign's own σ |
| "Response rate 0.00867 Sα/SD" | **DISCARDED and not re-derivable** (REBUILD_PLAN §C3) — its pool-shift coordinate came from the deleted iteration-2 pools, and its anchor added *real* target supervision arm C does not | Do not resurrect it. The campaign measures ΔSα directly, which is strictly better |
| "\|Ds\| = 6824 / 7824 / 8824 per arm" | **UNVERIFIED** — pools deleted | Not needed if the campaign reports pool sizes it actually builds |
| Seed robustness of `target_es` / of the ES→error link | **UNVERIFIED-DEFERRED** — one checkpoint pair per architecture (`B1_RESULTS.md` §8, §D6) | The campaign will produce 3 seeds × 3 arms of checkpoints. **This is a free by-product: score `target_es` on all of them and close the gap** |
| "CHAMELEON contamination is 41/76" | **COMMITTED, but a lower bound** — 25 of the 35 unmatched images have no same-dimension candidate and are **unchecked, not clean**; rescaled copies, crops and flips are out of scope (`D2_RESULTS.md` §5) | State it as a lower bound. It is already enough to withdraw the endpoint |
| SegMaR's numbers | **no committed eval table, no training log**, and a documented backbone deviation (IMAGENET1K_V2 vs the paper's V1) | Another reason SegMaR is the wrong third architecture (§1) |

**STATUS: settled** as an inventory. **A3 is the one that blocks a specific sentence in the paper.**

---

# 10. Blocking code facts, totals, and risk ranking

## 10.1 ★★★ Three blocking code facts — resolve before constructing any arm

### (1) `--source_root` is silently discarded under `--task S2C`
[MyTrain.py:232](MyTrain.py#L232) executes `opt.source_root = './Dataset/Source/HKU-IS/'` *after*
`parse_args()`. **Consequence if missed: you build three beautiful arm pools, pass them with
`--source_root`, and all three arms train on the identical base pool. Arms A, B and C become the same
run three times, and the only symptom is that the numbers agree suspiciously well.** This is the
single highest-consequence failure mode in the campaign, because it produces a *plausible* null.

**Fix:** guard line 232 so an explicitly-passed `--source_root` wins. Then **assert** the resolved
path in the log and diff it against the intended arm directory.

### (2) The CLS output path is derived from `source_root` alone — all arms collide
[CLS.py:16-17](CLS.py#L16-L17): `source_copy_root = source_root.rstrip('/\\') + f'_iteration{i+1}/'`,
and [CLS.py:19-21](CLS.py#L19-L21) **`shutil.rmtree`s it** if it exists. The network name is not part
of the path. With `source_root` forced to the same value (fact 1), **every arm writes and deletes
`Dataset/Source/HKU-IS_iteration2/`.** Two concurrent `--iteration 2` runs destroy each other's
round-2 dataset mid-epoch.

Already documented: `Experiments/REPRODUCE_TABLE1_v2.md` §8 item 9 (*"the one gotcha that can silently
invalidate a run"*), §9 (*"Parallelism: **None.**"*), and `preflight.py:479-500`
(`check_cls_collision`, which scans `/proc` for another `MyTrain.py`).

**Fixing fact 1 fixes this too** — distinct `source_root` per arm ⇒ distinct `_iteration2` dirs ⇒
**concurrency on both GPUs becomes safe**, which is what makes the wall-clock numbers in §7 achievable.

### (3) No `--seed`
§7. Two-line patch, already written and previously used.

**All three are prerequisites, not options.** Also required before reporting: the `MyTest.py` /
`MyEval.py` patches in §6.1.

## 10.2 Measured here, and what remains unmeasured

**Evaluation cost — MEASURED.** Ran `Eval/MyEval.py` over the existing 2026-image
`Result/SINet/S2C` against `Dataset/Test/COD10K`: **141.94 s (2.37 min)**, single-threaded CPU
(`metrics.py` is numpy/scipy; the GPU is idle). Scaling by image count, NC4K (4121) ≈ **4.8 min**. So
**≈7.2 min of CPU per run for both endpoints** — 18 runs ⇒ ≈2.2 CPU-hours, and it parallelises with
training since it uses no GPU. Not a schedule risk.

**Bonus verification:** that run reproduced the committed table **exactly** — Sα **0.7172**,
wFβ **0.4746**, MAE **0.0745**, adpEm 0.7599, meanEm 0.7439, maxEm 0.7954, adpFm 0.5468, meanFm
0.5543, maxFm 0.5965, identical to `Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`. **The eval path is
faithful and the endpoint numbers are reproducible from the committed predictions** — one of the
cross-checks REBUILD_PLAN §C3 asked for, now discharged.

Still **not** measured:
- **Inference wall clock (`MyTest.py`).** It cannot run as committed (§6.1: it hard-codes the absent
  `./Dataset/Test/{Image,GT}`), so it could not be timed. 2026 + 4121 forward passes at 352² is small
  relative to training, but it is unmeasured and should be timed on the first run.
- **SegMaR wall clock** — estimated from checkpoint mtimes only (§1).
- **The cost of `cudnn.deterministic = True`** (§7) — unmeasured on this stack.
- **Whether SegMaR / SINet-v2 S2C ran with `--iteration 2`** — round 2 overwrites round 1 in place, so
  the checkpoint mtimes cannot distinguish it and neither directory has a training log.

## 10.3 Ranked — where a wrong choice does the most damage

1. **`--source_root` ignored (§10.1 fact 1).** Produces a *credible* null from three identical arms.
   Nothing downstream would catch it. **Mitigation: assert the resolved source path and its content
   hash, per arm, per seed, in the log.**
2. **Positional mis-pairing in `SrcDataset` (§2.4).** Trains on shuffled labels. `filter_files` is not
   a guard. **Mitigation: assert `stem(images[i]) == stem(gts[i])` for all i, plus `len(dataset)`.**
3. **The CLS `_iteration2` collision (§10.1 fact 2).** Silently corrupts round-2 pools; worst when
   arms run concurrently, which is exactly what the schedule wants.
4. **The noise floor (§6.3).** Importing σ = 0.00356 as the bar imports a number measured at
   `--iteration 1`, from artifacts no version-controlled script produced, and *understates* how much
   of the variance survives seed-matching (0.00229 of 0.00355 is nondeterminism). A wrong bar turns a
   null into a false positive or vice versa, and it is the number a reviewer will attack first.
5. **α, the allocation temperature (§5.2).** No committed artifact specifies one. Choosing it *after*
   seeing results, or choosing the `d`-maximising value, reintroduces exactly the practice the rebuild
   exists to end. **Declare it first.**
6. **Arm A's construction (§3.1).** Unpadded, A-vs-B is uninterpretable (mixture and 22 % exposure
   change together). Getting this wrong does not corrupt the data — it just means one of the two
   headline gaps cannot be claimed.
7. **Reporting `test_es` instead of `target_es` (§4).** Guarded by C1 Gate 1 for C1's own code, but
   **the training arm-construction script is new code and inherits no gate.** Re-implement Gate 1's
   AST check, or at minimum assert the column name being read.
8. **Wrong mask set for the base pool (§2.2).** `Source/HKU-IS/GT` ≠ `HKU-IS_raw/gt` (0.18557 vs
   0.19132). Using the raw masks with the authors' images changes every label subtly.
9. **Regenerating renders per arm instead of reusing the fixed pool (§2.3).** Injects a
   position-in-shard background difference (~37–40 grey levels, D2 s8) into the B-vs-C comparison.
10. **Metric precision and Eφ variant (§6.2).** `.round(4)` at 2.8 % of σ, and two of the reported Eφ
    variants truncate. Won't invalidate the campaign; will make the table wrong.

## 10.4 Recommended configuration and its total

**Recommended:** SINet + SINet-v2 · arms {A2 (foreground-matched padded), B, C} · seeds {42, 43, 45} ·
dinoL518 / k = 75 / `target_es` · B = 1000 · α = 1.0 · `--iteration 2` · reuse the existing render pool
· cudnn determinism ON (subject to your call) · primary COD10K-Sα, secondary NC4K, CAMO for checkpoint
selection only.

| | |
|---|---|
| Training runs | **18** (3 arms × 3 seeds × 2 architectures) |
| Training GPU-hours | **9 × 1.75 + 9 × 2.2 = 35.5** |
| Wall clock on 2 GPUs (≈9 % contention) | **≈19 h** |
| Evaluation | **≈7.2 min CPU per run** (measured: 141.94 s for COD10K-2026; NC4K scaled) ⇒ ≈2.2 CPU-h total, off the GPU critical path. Inference itself still unmeasured (§10.2) |
| Stage-C generation | **0** — the existing 4447-render pool is reused (§2.3) |
| Disk | ≈3.5 GB checkpoints per run ⇒ **≈63 GB**, plus ~120 MB per arm pool. 1.5 T free |
| Share of a 240 h budget | **≈8 %** — evaluation does not add to it (CPU, parallel) |

If arm A0 (unpadded) is also wanted as a reference: **+6 runs**, +11.9 GPU-h, +6.5 h wall — total
**24 runs, ≈47 GPU-h, ≈26 h**, still ~11 % of budget.

**Contingent, pre-registered, not run unless triggered:** dinoL224 arm C (+3 to +6 runs) only if the
primary result is positive; α = 0.5 arm C as a secondary operating point; Oracle arm once DUTS is on
disk and swept (§8).

---

## What I need from you before anything runs

1. **§1** — Option A (SINet, more seeds) or Option B (SINet + SINet-v2, 3 seeds)?
2. **§3.1** — arm A as A0, A1, or **A2**? If A2, is arm B's foreground draw fixed across seeds or does
   it vary?
3. **§5.2** — **α**. This has no answer in any artifact and arm C cannot be built without it. My
   recommendation is α = 1.0.
4. **§5.2** — B = 1000, confirmed?
5. **§6.2** — which Eφ variant does the paper report?
6. **§6.4** — sign off on the decision rule verbatim so it can be committed **before** the first run.
7. **§7** — set `cudnn.deterministic = True`? (Best available lever on statistical power; is a
   disclosed deviation.)
8. **§9.2** — does the paper need the "LAKE-RED is far from the real target" claim? If yes, **A3 must
   run first** (inference-only, inputs all present). If no, the sentence gets deleted.
9. **§10.1** — approve the three code patches (`MyTrain.py:232` guard, `--seed`, per-arm
   `source_root`) plus the `MyTest.py` / `MyEval.py` endpoint patches, all as disclosed deviations.

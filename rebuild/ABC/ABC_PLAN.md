# ABC_PLAN.md — the A/B/C/A2 training campaign

## A.0 Status, scope, and what this document is

**Status: PLAN. Approved before any ABC code exists. Nothing here is a measurement.**

Specification for the A/B/C/A2 training campaign — the first rebuild experiment with `TRAINS YES`.
Measured values live in `results/REBUILD_LOG.txt` and nowhere else until `ABC_RESULTS.md` cites them by
log block. The decision rule lives in `rebuild/ABC/PREREGISTRATION.md`, committed before the first run
and never edited after numbers exist.

Every prior rebuild experiment (E0, D2, D1, B1, C1) measured a **property**. None trained a model —
`REBUILD_PLAN.md` §3 says "**Trains? NO** for every experiment." This campaign is the first time Stage C
is actually trained, and the first measurement whose output is an **accuracy number** rather than a
property. C1 left it a specific, testable hypothesis: the targeted arm is more proximal to the target
manifold on average but spans roughly half the effective dimensionality and covers no more of it
(`C1_RESULTS.md` §8.6) — *"whether that profile trains worse, better, or identically is exactly what C3
measures and what C1 structurally cannot"* (`REVISION_TABLE.md` §5).

**Ground rules this plan is built around** (from the approving brief):

1. **Fresh from primary data.** No `/tmp`, no `_archive_stageC_old/`, no rescued cache is read by any
   training or eval step. The archive's only permitted use is that the *content* of its 2-line seed
   patch is re-applied by editing the in-tree `MyTrain.py` (§A.7 P1) — never by importing a separate
   file. Asserted mechanically in §A.8 G2.
2. **One trainer, one eval path.** Arms differ only by their data directory and their seed. A second
   copy of `MyTrain.py` or `MyTest.py` anywhere in the tree is a gate failure (§A.8 G3).
3. **Nothing is a result until a committed script writes an `EXP ABC` block** to
   `results/REBUILD_LOG.txt` in the E0–C1 discipline. Every metric carries its provenance.

**Locked decisions, built to, not re-litigated:** SINet + SINet-v2, both `--task S2C --iteration 2`;
arms A0 / A2 / B / C; seeds {42, 43, 45}; B = 1000; α = 1.0 primary and α = 0.5 pre-registered
secondary (run-only-if-budget-allows); `cudnn.deterministic = True`, `cudnn.benchmark = False`;
arm-C selection in `dinoL518` at k = 75 by the committed `target_es` column.

> **One addition to the locked decision set, flagged up front.** The approving brief's patch list omits
> the patch that makes its own arm-construction requirement possible. `MyTrain.py:232` executes
> `opt.source_root = './Dataset/Source/HKU-IS/'` **after** `parse_args()`, so `--source_root` is
> silently discarded under `--task S2C`. Without patch **P0** (§A.7) all 24 runs train on the identical
> base pool and the campaign returns a *credible* null from three copies of the same run. P0 is not a
> re-litigation of a locked decision — it is forced by the locked decision. It is listed first.

## A.1 The base pool and the target set

| Role | Path | Count | Ext | Polarity / note |
|---|---|---|---|---|
| **Base synthetic pool — images** | `Dataset/Source/HKU-IS/Image` | **4447** | 4447 × `.jpg` | the authors' pool; agg `b42e5f44b5f2b0db` (`REBUILD_PLAN.md` §1) |
| **Base synthetic pool — masks** | `Dataset/Source/HKU-IS/GT` | **4447** | 4447 × `.png` | **object = WHITE**, mean white fraction **0.18557**; agg `95a0b4ed8ce47903` |
| **Target set** (target loader + ES signal) | `Dataset/Target/Image` | **4040** | 4040 × `.jpg` | 3040 `COD10K-*` + 1000 `camourflage_*` (measured by prefix) |
| Checkpoint-selection set | `Dataset/Val/CAMO/{Imgs,GT}` | 250 + 250 | `.jpg` / `.png` | the published CAMO **test** split |
| Stage-C render pool — images | `Dataset/LAKERED/output/HKU-IS/images` | 4447 | 4447 × `.jpg` | named `SOD_<stem>.jpg` |
| Stage-C render pool — masks | `Dataset/LAKERED/output/HKU-IS/masks` | 4447 | 4447 × `.png` | **SOD polarity**, white fraction **0.19132** |

Code path for the source pool: `--source_root` default is `./Dataset/Source/CNC/`
([MyTrain.py:219](../../MyTrain.py#L219)); the `--task S2C` block resets it to
`./Dataset/Source/HKU-IS/` ([MyTrain.py:232](../../MyTrain.py#L232)); it is consumed as
`source_root + 'Image/'` / `+ 'GT/'` by `get_srcloader`
([MyTrain.py:292-296](../../MyTrain.py#L292-L296)).

> **Citation correction, carried from `ABC_SCOPING.md` §2.1.** The brief cites "MyTrain.py:220,297" for
> the training source. Those two lines are the **target** loader — `:220` is `--target_root` and `:297`
> is `get_tarloader`. That citation is correct in `D2_RESULTS.md` §3.0, where it describes the
> unlabeled target pool. The **source** citation is `:232` + `:292-293`. The conclusion is unchanged;
> the line numbers must not be carried into the paper as written.

### The 7 D2-leaked names: excluded from clustering/ES only, NOT from the training pool

All 7 names in `rebuild/D2/out/d2_leaked_names.json` → `target_names_to_exclude` are **present** in
`Dataset/Target/Image` (verified individually, 7/7). The exclusion is applied downstream in analysis:
B1's committed cluster CSV sums `n_target = n_target_scored = 4033` (= 4040 − 7) over its 75 clusters,
while E0's cache `dinoL518_names.json['tgt']` holds all 4040.

**The training target loader reads all 4040.** That is the published S2R-COD protocol, and D2 §3.5
measured its cost: removing the 7 moves endpoint MAE by **−1.242e-05 (0.0167 % relative)**, and their
mean percentile within the clean test set is **0.4761** (0.5 = indistinguishable) — no memorisation
signature. Dropping them would also change nothing mechanically: `⌈4033/16⌉ = ⌈4040/16⌉ = 253`.
**Disclosed, not fixed.** Consumers read the JSON; no name list is hardcoded anywhere
(`REBUILD_PLAN.md` §0.2).

## A.2 The run identifier and the directory scheme — collision made impossible

```
RUNID = {ARCH}_{ARM}_s{SEED}
  ARCH ∈ {SINet, SINetv2}          # SINetv2 is the filename form of --network SINet-v2
  ARM  ∈ {A0, A2, B, C10, C05}     # C10 = arm C at α=1.0 ; C05 = arm C at α=0.5 (secondary)
  SEED ∈ {42, 43, 45}
```

| What | Path | Tracked? |
|---|---|---|
| arm pool | `Dataset/Source/ABC/{RUNID}/{Image,GT}/` | no (`.gitignore: /Dataset*`) — regenerable from the committed manifest |
| CLS round-2 pool | `Dataset/Source/ABC/{RUNID}_iteration2/{Image,GT}/` | no — **written automatically** by [CLS.py:16](../../CLS.py#L16) as `source_root.rstrip('/') + '_iteration2/'` |
| checkpoints + training log | `Snapshot/ABC/{RUNID}/` | `*.pth` no; **`training_log.log` YES** (`Snapshot/` is not gitignored) |
| predictions | `Result/ABC/{RUNID}/{ENDPOINT}/` | no (`/Result*`) |
| run stdout | `rebuild/ABC/{RUNID}.log` | no (`/rebuild/*/*.log`) |
| manifests, metrics, verdict | `rebuild/ABC/out/*.{csv,json,txt}` | **YES** |

**Why collision is impossible, stated as a proof rather than a convention.** `RUNID` is a pure function
of the run's full identity `(arch, arm, seed, α)`. Every path a run writes is prefixed by its `RUNID`,
**including** the CLS output directory, because CLS derives that path from `source_root` alone and
`source_root` is `RUNID`-prefixed. Two distinct runs therefore share no write path. This is the
`_iteration2` landmine that `Experiments/REPRODUCE_TABLE1_v2.md` §8 item 9 calls "the one gotcha that
can silently invalidate a run" and that `preflight.py:479-538` (`check_cls_collision`) exists to detect:
under released code every arm collapses onto `Dataset/Source/HKU-IS_iteration2/` and each run's
[CLS.py:19-23](../../CLS.py#L19-L23) `rmtree`s the previous run's pseudo-label pool. Patch **P0** plus
this scheme is what removes it — **and it is also what makes both GPUs usable concurrently**, which
every wall-clock figure in §A.11 depends on.

Two build-time assertions make the scheme self-enforcing: the pool directory must not already exist
(refuse to overwrite), and `{RUNID}_iteration2` must be absent before the run starts.

## A.3 Arm construction

All four arms share the base 4447 pairs. Construction is: copy the base pool into the arm directory,
then add `B = 1000` pairs (A0 adds none). The base copy is asserted byte-identical to primary data via
`C.dir_digest` against the committed agg hashes in §A.1 — so "same base pool across arms" is
**verified**, not assumed.

### A0 — unpadded paper baseline

Base pool only, 4447 pairs. This is the paper-comparable row.

**A0 at seed 42 is the campaign's first run and a HARD GATE.** It differs from the committed
`Snapshot/SINet/S2C` run in exactly two ways: the seed patch (same value, 42) and cudnn determinism.
Its COD10K Sα must land within **3 σ_prior = 0.0107** of the committed **0.7172**
(`Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`; σ_prior = 0.003555, §A.6).

- PASS → proceed to the remaining 23 runs.
- FAIL → **HALT the campaign and diagnose.** An unexplained baseline shift means something other than
  the seed and cudnn flags changed, and proceeding would poison 23 runs. The gate is deliberately
  generous (3σ, not 2σ) because determinism changes cuDNN's algorithm selection and a real shift is
  expected; it is a tripwire for *unexplained* movement, not a reproduction test.

### A2 — foreground-matched clean control

Base pool + **1000 duplicates**: for each stem `s` in **arm B's selected stem list at the same seed**,
copy

```
Dataset/Source/HKU-IS/Image/{s}.jpg  ->  <pool>/Image/DUP_{s}.jpg
Dataset/Source/HKU-IS/GT/{s}.png     ->  <pool>/GT/DUP_{s}.png
```

Pool size 5447, matching B and C. A2-vs-B holds the foreground set, the pool size, `total_step` and the
per-image exposure all constant, so the only difference is that B's added images carry **LAKE-RED**
backgrounds and A2's carry the **authors'** backgrounds of the same foregrounds.

> **Residual confound in A2-vs-B, flagged for the review, quantified.** A2's added masks are the
> **authors'** GT (mean white fraction 0.18557); B's and C's added masks are the render's own output
> masks, which are pixel-identical to **raw** GT (0.19132) — see arm B below. So Δ(B − A2) confounds
> "LAKE-RED background" with a **0.00575 mean-white-fraction difference in mask tightness on 1000 of
> 5447 images (18.4 % of the pool)**. This is unavoidable under the locked A2 definition, because the
> authors' image was rendered with the authors' mask and pairing it with the raw mask would mislabel it.
> **Δ(C − B) — the campaign's actual claim — is entirely unaffected:** B and C use the same mask
> provenance, the same 1000-image budget and the same render pool.
> *A one-line alternative exists if the review prefers it:* build A2 from `HKU-IS_raw/imgs/{s}.png` +
> `HKU-IS_raw/gt/{s}.png`, which is mask-clean and isolates "generated background vs the real
> photograph's background" — at the cost of introducing a PNG-vs-JPG compression asymmetry against the
> `.jpg` base pool. **Flagged, not chosen; the locked spec is built as written.**

### B — random re-render

Base pool + the **existing** local renders of 1000 foregrounds drawn uniformly without replacement from
the 4447-item pool:

```
Dataset/LAKERED/output/HKU-IS/images/SOD_{s}.jpg  ->  <pool>/Image/SOD_{s}.jpg
Dataset/LAKERED/output/HKU-IS/masks/SOD_{s}.png   ->  <pool>/GT/SOD_{s}.png
```

**Draw RNG, recorded:** `numpy.random.default_rng(700_000 + SEED)`, then
`rng.choice(4447, size=1000, replace=False)` over the stem list `sorted(os.listdir(HKU-IS_raw/imgs))`
(the row order `c1_space` uses), sorted for output. The namespace `700_000 +` is distinct from every
RNG C1 uses (`20_000 + i` for its shuffles) so the two cannot be confused. The drawn stems are written
to the tracked artifact `rebuild/ABC/out/abc_stems_B_s{SEED}.txt`, one stem per line, with the RNG
expression recorded in `abc_pools.json`.

**Why the existing renders and not fresh generation — load-bearing.** D2 §3.3 established by controlled
experiment (s8, T1/T2/T3) that a render is a function of **(foreground, mask, position-in-shard)**:
three byte-identical inputs at shard positions 0/1/2 produced three *different* renders (mean|diff|
36.7 and 40.3), and forcing each to local position 0 collapsed the divergence to **exactly 0.0**. If arm
B regenerated its 1000 and arm C regenerated its 1000, the two arms' backgrounds would differ by a
**noise draw as well as by selection** — injecting an uncontrolled variable into the one comparison the
campaign exists to make. Selecting subsets of one fixed 4447-render pool holds the noise draw constant
by construction. D1 §1 guarantees the pool covers every foreground: the render set is a **bijection**
onto the raw foreground set (4447/4447 trace in, 0 outside, 0 unrendered). Regeneration is also not
cheap-and-therefore-tempting-anyway: it measures **1.77–1.85 s/image**
(`LAKE-RED/logs/gen_shard{0,1}.log`: `2224it [1:06:54, 1.77s/it]`, `2223it [1:08:23, 1.76s/it]`).
**Reuse is more correct, not merely faster.**

**Mask choice, and the assertion that pins it.** The added mask is the render's own output mask. D1 §1
measured `raw_gt` and `local_msk` white fractions agreeing to five decimals; verified per-file over
**200 random stems: 200/200 pixel-identical, maxdiff = 0**, and render / authors'-image / render-mask
dimensions agree 200/200. The builder asserts `maxdiff == 0` against `HKU-IS_raw/gt/{s}.png` for **all
1000 selected stems** — not a sample. Do **not** pair a render with `Source/HKU-IS/GT` (trap T3: the
two mask sets share no pixel-identical stem).

### C — targeted re-render

Same injection mechanics as B; the 1000 stems come from **reusing C1's committed selection code**, not
from a reimplementation:

```python
sys.path.insert(0, <repo>/rebuild); sys.path.insert(0, <repo>/rebuild/C1)
import c1_space
from c1_targeted_vs_random import (softmax_alloc, largest_remainder,
                                   rank_by_centroid, serving_orders, greedy_select)

sp     = c1_space.load_space('dinoL518')        # L2 already applied; es = target_es
p      = softmax_alloc(sp.es, ALPHA)            # T = ALPHA * sd(es); w = exp((es-max)/T)
alloc  = largest_remainder(p, 1000)             # integer, sums to exactly 1000
_, ord_= rank_by_centroid(sp)                   # cosine(cutout, centroid), stable argsort
serving= serving_orders(alloc, sp.es)['desc_nc']    # C1's primary order
idx, ndisp = greedy_select(alloc, ord_, serving)
stems  = [sp.names[i] for i in idx]             # sp.names are already splitext'd stems
```

`c1_targeted_vs_random.py` is import-safe: module scope holds only constants and `POOL = PF.POOL`, and
it is guarded by `if __name__ == '__main__': main()`. `c1_space.load_space` is the **only** sanctioned
way to obtain these arrays — it L2-normalises once and asserts `Space.tag == tag`, which is what makes
B1's §C2 cache-mixing defect structurally unrepeatable. Direct `np.load` of `rebuild/E0/cache/*.npy`
bypasses that discipline and is forbidden.

Inputs, all verified present: `rebuild/B1/out/b1_cluster_es_dinoL518.csv` (75 rows, `target_es`
populated 75/75, range 0.018391–0.070668), `b1_centroids_dinoL518_k75_seed0.npy`,
`b1_cluster_assignment_dinoL518.json` (`k=75, seed=0, embedder=dinoL518`),
`rebuild/E0/cache/dinoL518_{cut,local}_cls.npy` (4447 × 1024), `dinoL518_names.json`.

> `rebuild/E0/cache/` is gitignored but is **not** a rescued cache. E0 rebuilt it from primary data and
> proved the package runs with the archive and the `/tmp` scratchpad both unreachable
> (`REBUILD_PLAN.md` §E0, §5). Reading it is the sanctioned path and is what C1 does. If it is absent,
> re-run `rebuild/E0/e0_regenerate.py` before building arm C; gate G2 re-verifies a sample against
> `rebuild/E0/out/e0_manifest.sha256`.

**Selection is deterministic** — no RNG — so arm C's stem list is identical across seeds. It is emitted
once per α as `rebuild/ABC/out/abc_stems_C_a{1.0,0.5}.txt`, and the three per-seed pools are asserted to
have identical manifests.

**★ The reproduction gate.** Every quantity below is a deterministic function of the allocation and the
selection, so it must reproduce C1's committed `rebuild/C1/out/c1_cells.csv` row **exactly**. If it does
not, something drifted between C1 and ABC and the build **halts**:

| α | row `(dinoL518, B=1000, R2_cut)` | `clusters_funded` | `max_alloc_share` | `alloc_entropy_norm` | `tv_from_uniform` | `n_displaced` | `degenerate` |
|---|---|---|---|---|---|---|---|
| **1.0** (primary) | verified | **75** | **0.194** | **0.78644** | **0.49253** | **370** | 0 |
| 0.5 (secondary) | verified | **40** | **0.509** | **0.36203** | **0.85906** | **115** | 0 |

Plus `len(stems) == 1000`, all distinct, all in the 4447-stem pool.

**α = 1.0 is the primary, and the reason is a property of the choice, not of the outcome.** At α = 1.0
the temperature is `T = sd(es)` — the scale-free operating point, funding all 75 clusters with a maximum
share of 0.194. α = 0.5 maximises `d_heldout` among non-degenerate cells at B = 1000 (0.797 vs 0.642),
but C1's attribution audit showed `d` measures **concentration, not targeting** (targeted − ES-shuffled
= **+0.0073**, ES wins 13/20 — a coin flip; targeted − arbitrary-cluster = **−0.0649**, ES wins 4/20).
Selecting α to maximise that quantity would tune the arm on a metric its own audit disowns. α = 0.5 is
carried as a **pre-registered secondary**, declared before any run, run only if budget allows.

## A.4 The seed-coupling sub-choice — DECIDED

**Decision: arm B's random draw VARIES per seed** (`default_rng(700_000 + SEED)`), and **arm A2 tracks
arm B at the same seed**. Arm C is deterministic and identical across seeds. Recorded in
`abc_pools.json` and in the `EXP ABC` block as
`arm_B_draw_coupling = per-seed (rng 700000+seed)`.

**Reasoning.** The claim under test is Δ(C − B): *does targeting beat random?* "Random" is a
**distribution over draws**, not one draw. With a single fixed draw, all three seeds inherit that draw's
idiosyncrasies and the strongest available reading is "C beats this one particular random selection" —
precisely the criticism C1 pre-empted by averaging its random arm over **≥ 20 independent draws**, and
precisely what `REBUILD_PLAN.md` §0.2 discarded as an inherited defect: *"`seed 0`, single draw → ≥ 10
seeds / draws, spread reported. **One seed is not a measurement.**"* Three draws is thin, but it is a
measurement; one is not.

**The cost, stated rather than hidden.** Arm B then carries **selection variance that arms A0 and C do
not**, so its within-arm sd will exceed theirs. Three consequences, all handled:

1. Pooled σ̂ (the pre-registered bar) assumes equal within-arm variance and will be **inflated** by
   arm B — making the bar *harder*, i.e. conservative. That direction is acceptable; the reverse would
   not be.
2. **Per-arm sds are reported beside the pooled σ̂**, so the asymmetry is visible rather than absorbed.
3. If `sd(B) > 2 × sd(C)`, that is itself a reportable finding — random allocation has materially higher
   selection variance than targeted — and the Δ(C − B) reading is caveated accordingly. Declared here,
   before the numbers exist.

The alternative (one fixed draw) buys a marginally cleaner A2/B pairing and would be defensible only if
the paper's claim were about one specific baseline sample. It is not.

## A.5 What is held identical across arms — enumerated, and each one asserted

| # | Held identical | Set at | How the plan asserts it |
|---|---|---|---|
| 1 | `--network` | [MyTrain.py:193](../../MyTrain.py#L193) | in `RUNID`; command manifest |
| 2 | `--method ours` | [:204](../../MyTrain.py#L204) | command manifest; a stray `--method` silently forces `--iteration 1` ([:236-238](../../MyTrain.py#L236-L238)) |
| 3 | `--iteration 2` | [:203](../../MyTrain.py#L203) | assert **exactly 2** `Training Log` markers in each `training_log.log` |
| 4 | epochs / batch / lr / decay | self-set [:249-272](../../MyTrain.py#L249-L272) | **cannot drift from the CLI** — restated in A.5.1; assert last logged epoch |
| 5 | α / u / τ / a / b / c | [:225-231](../../MyTrain.py#L225-L231) | overwritten after parsing — structurally safe |
| 6 | seed → init, shuffle order, augmentation | [:242](../../MyTrain.py#L242) + P1 | `--seed` in the command manifest; determinism measured, §A.6 |
| 7 | base pool bytes | [:232](../../MyTrain.py#L232) + P0, [:292-293](../../MyTrain.py#L292-L293) | `C.dir_digest` of each arm's base subset == committed agg hashes (§A.1) |
| 8 | target pool (4040, unfiltered) | [:297-300](../../MyTrain.py#L297-L300) | assert `[Target Loader] Loaded 4040` in every run log |
| 9 | `total_step` | [:306-307](../../MyTrain.py#L306-L307) | assert the parsed set == `{253}` (SINet) / `{127}` (SINet-v2) in **both** rounds |
| 10 | checkpoint-selection set | [:302-304](../../MyTrain.py#L302-L304), [:322-324](../../MyTrain.py#L322-L324) | `--val_root ./Dataset/Val/CAMO/` in the manifest; 250 files asserted |
| 11 | `Tea_epoch_best.pth` rule (min val MAE) | [:181-188](../../MyTrain.py#L181-L188) | assert the file exists after each round |
| 12 | eval protocol | §A.10 | one scorer, validated against a committed number before use |
| 13 | `B = 1000` | arm construction | assert `len(added) == 1000` in A2, B, C — and that A2/B/C pool sizes are all 5447 |
| 14 | CLS output directory | [CLS.py:16](../../CLS.py#L16) | `RUNID`-prefixed by construction (§A.2) |
| 15 | backbone init file | `Src/model/**` | assert sha256 of `resnet50-11ad3fa6.pth` (102,540,417 B) and `res2net50_v1b_26w_4s-3cf99910.pth` (103,197,949 B) once, into the log block |

### A.5.1 The per-architecture schedule, restated from the code

| | SINet | SINet-v2 |
|---|---|---|
| set at | parser defaults [:194-199](../../MyTrain.py#L194-L199), [:249-252](../../MyTrain.py#L249-L252) | self-override [:253-259](../../MyTrain.py#L253-L259) |
| `--epoch` | 40 → **39 epochs run** (`range(1, opt.epoch)`, [:316](../../MyTrain.py#L316)) | 100 → **99 epochs run** |
| batch | 16 | 32 |
| lr | 1e-4 | 1e-4 |
| decay | 0.1 @ 30 | 0.1 @ 50 |
| clip_grad | False | **True** |
| `total_step` (A0 / A2·B·C) | **253 / 253** | **127 / 127** |
| imgs seen per epoch | 4048 | 4064 |
| per-image exposure (A0 / A2·B·C) | **0.9103 / 0.7432** | **0.9139 / 0.7461** |
| CLS student checkpoint | `Stu_40.pth` ([CLS.py:43](../../CLS.py#L43)) | `Stu_100.pth` ([CLS.py:48](../../CLS.py#L48)) — produced at `epoch_iter=99` by [:145-147](../../MyTrain.py#L145-L147) |

**Do not pass** `--epoch`, `--batchsize`, `--lr`, `--decay_epoch`, `--alpha`, `--u`, `--tau`, `--a`,
`--b`, `--c`. They are overwritten after parsing, and `CLS.py` hard-requires the checkpoint name that
the locked `--epoch` produces.

**Per-image exposure is why A0 is not a clean control, and why A2 exists.** `total_step` is pinned at
253 (SINet) for every pool size because `zip()` truncates to the shorter loader
([:51,53](../../MyTrain.py#L51-L53), [:306-307](../../MyTrain.py#L306-L307)), so **B changes the mixture
and not the step count.** At B = 1000 each base image is seen 0.743× per epoch against 0.910× in A0 —
**A0 gives each base image 22 % more exposure.** A0-vs-B therefore confounds "1000 more images" with
"22 % less per-image exposure", in the direction that disfavours B and C. A2 removes that confound; A0
is retained only for paper-comparability. This is `REBUILD_PLAN.md` §C2's own note: *"Arm A is **not** a
clean control … only B-vs-C is clean."*

### Flagged: what would silently differ, and how the plan neutralizes it

**(a) `Tea_epoch_best.pth` fallback.** Validation runs only for `epoch_iter > 20`
([:322](../../MyTrain.py#L322)), so the `epoch == 1` branch at
[:181-186](../../MyTrain.py#L181-L186) can never fire; `best_teamae` stays 1 and the first validated
epoch always saves. But **CLS silently falls back to `Tea_40.pth`/`Tea_100.pth`** if the best checkpoint
is missing ([CLS.py:65-75](../../CLS.py#L65-L75)), so a killed run changes which teacher generates
pseudo-labels. *Neutralized:* assert `Tea_epoch_best.pth` exists after every round; any run that does
not complete is **discarded and re-run**, and the discard is logged. No partially-trained checkpoint
enters the metrics.

**(b) Round 2 overwrites round 1 in place** ([:141-151](../../MyTrain.py#L141-L151)) — same
`--save_model` path for both rounds. *Neutralized:* a fresh, empty `Snapshot/ABC/{RUNID}/` per run
(asserted empty before launch). `preflight.py:434-436` already WARNs on a non-empty snapshot dir and
currently fires against the committed dirs — which is why ABC uses `Snapshot/ABC/`.

**(c) `--iteration 2` makes the arms differ in a SECOND place.** CLS selects target images by
`edge_loss < u · avg_loss` ([CLS.py:139](../../CLS.py#L139)) using the arm's **own** round-1 model, so
each arm appends a different number of differently-pseudo-labelled images. That is legitimately part of
"closed-loop", but it is a second, high-variance difference. *Neutralized by disclosure, not
suppression:* record `n_appended` per run (parsed from the round-2 `[Source Loader] Loaded N` print,
[Dataloader.py:202](../../Src/utils/Dataloader.py#L202)), report it as a per-arm table, and **flag if
arms differ by more than 5 %**. `total_step` stays pinned in round 2 for any `n_appended` (asserted,
#9).

**(d) `adjust_lr` compounds — and for SINet-v2 catastrophically.**
[tool.py:36-39](../../Src/utils/tool.py#L36-L39) does `param_group['lr'] *= decay` with
`decay = decay_rate ** (epoch // decay_epoch)` **every** epoch. Computed exactly: SINet reaches
**lr = 1e-14** by epoch 39; **SINet-v2 reaches lr = 1e-54** by epoch 99, i.e. its last 50 of 99 epochs
do essentially nothing. Identical across arms, so **not** a threat to the comparison. Three reporting
consequences: never describe the schedule as "step decay at epoch 30/50"; note that half of SINet-v2's
2.2 GPU-h per run is spent at a numerically dead learning rate; and expect σ_within (§A.6) to be
near-zero for both networks, so it is a *lower bound* on run-to-run σ and nothing more.

**(e) `structure_loss` passes `reduce='none'`** ([tool.py:9](../../Src/utils/tool.py#L9)) — a truthy
*string* to a legacy boolean argument, which torch resolves to `reduction='mean'`, making the `weit`
weighting on the BCE term a no-op (the weighted-IoU term is unaffected). Upstream behaviour, identical
across arms, affects SINet-v2 and SegMaR (both heads). Recorded so it is not discovered later and
mistaken for a bug introduced here.

**(f) Relative backbone paths.** `Src/model/SINet/SINet.py:211`,
`Src/model/SegMaR/SegMaR.py:360` and `Src/model/SINetV2/Res2Net_v1b.py:195` load their weights from
**relative** paths. *Neutralized:* every command in the manifest is executed with cwd =
`/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD`, asserted by the driver before launch.

**(g) `preflight.py` will report 3 FAILs for an eval-only gap.** Its spec table expects
`./Dataset/Test/Image` and `./Dataset/Test/GT` ([preflight.py:289-290](../../preflight.py#L289-L290)),
both **absent**; with `test pairing` ([:345](../../preflight.py#L345)) that is 3 FAILs and exit code 1 —
"NOT ready to train" — for paths `MyTrain.py` never touches. Its source-count rows
([:286-287](../../preflight.py#L286-L287)) are WARN-only and will fire harmlessly at 5447.
*Neutralized:* patch **P5** corrects the two stale rows (2 lines), so preflight stays a signal instead
of becoming a FAIL the operator learns to ignore. **The driver must not gate on preflight's exit code**;
ABC's own gates (§A.8) are the gate of record.

## A.6 Determinism — what the seed buys, stated without overselling

**Measured facts, not assumptions.** A probe in this repo's `.venv` reproducing the loader's exact RNG
usage (`np.random.rand()` at [Dataloader.py:32](../../Src/utils/Dataloader.py#L32), `shuffle=True`,
`num_workers=6`, `batch_size=16`) established:

| Property | Measured |
|---|---|
| shuffle order reproducible across processes at the same seed | **True** |
| shuffle order differs across seeds (42 vs 43) | **True** |
| shuffle order differs between epoch 0 and epoch 1 | **True** (fresh base seed per epoch — correct) |
| augmentation (flip) stream reproducible at the same seed | **True** |
| augmentation stream differs across seeds | **True** |
| distinct flip values over 64 items, 4 worker PIDs | **64** — workers do **not** share one stream |

So **model init, shuffle order and augmentation are fully seed-controlled**, with no `worker_init_fn`
needed (PyTorch seeds each worker's numpy from `base_seed + worker_id`, and `base_seed` comes from the
global torch RNG that `torch.manual_seed` sets). This had to be checked rather than assumed.

**What the seed does NOT control: the GPU kernels.** Recomputed from
`_archive_stageC_old/evidence_artifacts/noisefloor_meta/audit6.json`:

| Set | n | mean Sα | **sd (ddof=1)** |
|---|---|---|---|
| all six archived runs | 6 | 0.700564 | **0.003555** |
| distinct seeds only (42, 43, 45, 46) | 4 | 0.698989 | **0.002856** |
| **same seed 42, three repeats (s42, repB, repC)** | 3 | 0.703215 | **0.002287** |

Three runs at the **same seed** differ by sd = 0.002287 — **64 % of the across-seed sd**. Old claims
C3.1 (0.00356) and C3.2 (0.00286) both reproduce exactly. `cudnn.deterministic` is never set in released
code; only reported, at [preflight.py:198-199](../../preflight.py#L198-L199) ("seed is 42 but runs are
not bit-reproducible").

**Therefore, stated plainly and to be repeated in the paper:** seed-matching pairs **the data pipeline**
— init, shuffle order, augmentation. Patch **P2** turns on `cudnn.deterministic` to reduce kernel
nondeterminism; it is **not** claimed to eliminate it (non-cuDNN kernels, atomics and reduction order
are untouched, and the cost in throughput is unmeasured on this stack). The arms are therefore
**partially paired**, and how partially is an output of this campaign, not an input.

**The noise floor of record is measured from these runs.** σ̂ = pooled within-arm sd of Sα, per
architecture, per endpoint:

```
sigma_hat = sqrt( SUM_over_arms SUM_over_seeds (x[arm,seed] - mean(x[arm]))^2
                  / SUM_over_arms (n_seeds - 1) )          # df = 4 arms * 2 = 8
```

The archived σ ≈ 0.003555 (n = 6) and same-seed 0.002287 (n = 3) are quoted **only as expected scale**,
never as the bar. Both are provenance-caveated (rescued from a volatile scratchpad by code that was not
version-controlled at the time it ran — `_archive_stageC_old/README.md`) and both were measured at a
**different operating point**: those runs used `--iteration 1`
(`noisefloor_meta/run.sh`, `run_rep.sh`) and landed at Sα ≈ 0.6989–0.7058, against the committed
2-iteration endpoint of **0.7172**. `REBUILD_PLAN.md` §0.2 discarded σ = 0.00356 **as an input** for
exactly this reason; re-importing it as the bar would reinstate the practice the rebuild ended.

**Optional diagnostic (not a bar):** σ_within from `Tea_{36..40}.pth` + `Tea_epoch_best.pth` of the A0
runs, per `REBUILD_PLAN.md` §C3. Inference-only and free, but per (d) above the compounding lr makes it
a near-zero lower bound — its value is confirming convergence, not estimating run-to-run σ.
`REBUILD_PLAN.md` §5(c) item 7 names reporting it as if it were σ_seed as the exact failure to avoid.

## A.7 The patches — six, surgical, in-tree, committed once before any run

All six land in **one commit**, before the first run, and are shared by all arms. Every one is a
**disclosed deviation from released code** and must appear in the paper's reproducibility note.

### P0 — honour `--source_root` under `--task S2C` ★ REQUIRED; omitted from the brief's patch list

*Reason:* [MyTrain.py:232](../../MyTrain.py#L232) discards `--source_root` after `parse_args()`. Without
this patch §A.2's per-arm pools are unreachable and **all 24 runs train on the identical base pool** —
a credible null from three copies of the same run, with no symptom other than suspiciously close
numbers. The alternative (mutating `Dataset/Source/HKU-IS/` per run) destroys the primary pool whose
agg hash every committed experiment is traceable to. `Experiments/REPRODUCE_TABLE1_v2.md` §8 item 9
already prescribes this fix.

```diff
--- a/MyTrain.py
+++ b/MyTrain.py
@@ -219 +219,3 @@
-    parser.add_argument('--source_root', type=str, default='./Dataset/Source/CNC/')
+    parser.add_argument('--source_root', type=str, default=None,
+                        help='source pool root; if omitted, --task chooses the default '
+                             '(C2C -> ./Dataset/Source/CNC/, S2C -> ./Dataset/Source/HKU-IS/)')
@@ -231,2 +233,6 @@
         opt.c = 0.5
-        opt.source_root = './Dataset/Source/HKU-IS/'
+        if opt.source_root is None:
+            opt.source_root = './Dataset/Source/HKU-IS/'
+
+    if opt.source_root is None:
+        opt.source_root = './Dataset/Source/CNC/'
```

**Behaviour-preserving when the flag is omitted:** both task defaults resolve exactly as before.
*Assertion:* run `MyTrain.py --task S2C` with no `--source_root` and confirm the printed
`[Source Loader] Loaded 4447 image-mask pairs from ./Dataset/Source/HKU-IS/Image/`.

### P1 — `--seed` (content re-applied from the archived 2-line patch, by editing)

*Reason:* the seed is hardcoded ([MyTrain.py:242](../../MyTrain.py#L242)); a 3-seed campaign is
impossible without this. The identical patch exists at
`_archive_stageC_old/evidence_artifacts/noisefloor_meta/MyTrain_seed.py` and produced the six archived
runs. Per ground rule 1 its **content** is re-applied here by editing the in-tree file; that separate
file is **not** imported, copied, or read by any ABC script.

```diff
--- a/MyTrain.py
+++ b/MyTrain.py
@@ -221 +221,3 @@
     parser.add_argument('--val_root', type=str, default='./Dataset/Val/CAMO/', help='the test rgb images root')
+    parser.add_argument('--seed', type=int, default=42,
+                        help='RNG seed (was hardcoded 42 at MyTrain.py:242)')
     opt = parser.parse_args()
```

### P2 — determinism, at the seed-setting site

*Reason:* §A.6 — three archived runs at the same seed differ by 64 % of the across-seed sd, so without
this the arms are not paired at all. Note the removal of the two trailing spaces on the original line.

```diff
--- a/MyTrain.py
+++ b/MyTrain.py
@@ -242 +244,8 @@
-    set_random_seed(42)  
+    set_random_seed(opt.seed)
+    # Disclosed deviation from released code. Upstream leaves cuDNN nondeterministic
+    # (preflight.py:198-199 reports it). Three archived runs at the SAME seed 42 differ by
+    # sd(Sa) = 0.002287, i.e. 64% of the across-seed sd of 0.003555 -- so without this the
+    # arms are not seed-paired in any useful sense. This REDUCES, and is not claimed to
+    # eliminate, kernel nondeterminism. See rebuild/ABC/ABC_PLAN.md A.6.
+    torch.backends.cudnn.deterministic = True
+    torch.backends.cudnn.benchmark = False
```

`torch` is already imported at [MyTrain.py:1](../../MyTrain.py#L1). P1 and P2 touch adjacent lines and
are listed separately only because their reasons differ.

### P3 — `MyTest.py`: score a named endpoint

*Reason:* [MyTest.py:47](../../MyTest.py#L47) hard-codes `['COD10K']` and
[:51-52](../../MyTest.py#L51-L52) hard-codes `./Dataset/Test/Image/` and `./Dataset/Test/GT/` — both
**absent** — with a `.format(dataset)` on strings containing no placeholder. NC4K is unreachable and
COD10K is broken. **Eval-only plumbing; touches no training code path.**

```diff
--- a/MyTest.py
+++ b/MyTest.py
@@ -21 +21,4 @@
 parser.add_argument('--gpu', type=int, default=0, help='choose which gpu you use')
+# CHAMELEON is deliberately absent: 41/76 of it is training data (D2, 53.9%), so it is
+# withdrawn as an endpoint. CAMO is the checkpoint-selection set, never an endpoint.
+parser.add_argument('--dataset', type=str, default='COD10K', choices=['COD10K', 'NC4K'],
+                    help='endpoint to score, from Dataset/Test/<name>/{Imgs,GT}')
 opt = parser.parse_args()
@@ -47 +50 @@
-for dataset in ['COD10K']:
+for dataset in [opt.dataset]:
@@ -51,2 +54,2 @@
-    test_loader = test_dataset(image_root='./Dataset/Test/Image/'.format(dataset),
-                               gt_root='./Dataset/Test/GT/'.format(dataset),
+    test_loader = test_dataset(image_root='./Dataset/Test/{}/Imgs/'.format(dataset),
+                               gt_root='./Dataset/Test/{}/GT/'.format(dataset),
```

The loop shape is preserved so the diff stays minimal. The `choices` list **encodes the D2 endpoint
policy in code**: CHAMELEON predictions cannot be produced by accident.

### P4 — `Eval/MyEval.py`: argument types

*Reason:* `--data_lst` and `--model_lst` are `type=list`
([MyEval.py:141,145](../../Eval/MyEval.py#L141-L145)), so a string argument is exploded into characters.
The committed commands worked only because the defaults are `['']`.

```diff
--- a/Eval/MyEval.py
+++ b/Eval/MyEval.py
@@ -140,4 +140,4 @@
     parser.add_argument(
-        '--data_lst', type=list, help='test dataset',
+        '--data_lst', type=str, nargs='+', help='test dataset',
         default=[''],
-        choices=['CAMO', 'CHAMELEON', 'COD10K', 'NC4K'])
+        choices=['', 'COD10K', 'NC4K'])
     parser.add_argument(
-        '--model_lst', type=list, help='candidate competitors',
+        '--model_lst', type=str, nargs='+', help='candidate competitors',
         default=[''])
```

`''` is retained in `choices` so every committed historical command still resolves. CAMO and CHAMELEON
are dropped for the same policy reason as P3.

### P5 — `preflight.py`: two stale endpoint rows (recommended, not required)

*Reason:* §A.5(g). After P3 these two rows describe paths nothing reads, and leaving them makes preflight
report 3 permanent FAILs. A tool whose FAILs are routinely ignored is worse than no tool.

```diff
--- a/preflight.py
+++ b/preflight.py
@@ -289,2 +289,2 @@
-        ("test images", "./Dataset/Test/Image", (".jpg", ".png"), 2026),
-        ("test GT", "./Dataset/Test/GT", (".jpg", ".png"), 2026),
+        ("test images", "./Dataset/Test/COD10K/Imgs", (".jpg", ".png"), 2026),
+        ("test GT", "./Dataset/Test/COD10K/GT", (".jpg", ".png"), 2026),
```

*Not patched, deliberately:* the source-count rows ([:286-287](../../preflight.py#L286-L287)) stay at
4447 and will WARN at 5447. A WARN that correctly says "this is not the reference layout" is the right
output for an arm pool. Also unpatched: the stale comment at `preflight.py:826` citing "MyTrain.py:159"
for the override (the line is 232) — cosmetic, and P0 changes what it describes anyway.

**Prerequisites confirmed present, so no patch is needed for them:**
`Src/model/SINet/resnet50-11ad3fa6.pth` (102,540,417 B, shared with SegMaR) and
`Src/model/SINetV2/res2net50_v1b_26w_4s-3cf99910.pth` (103,197,949 B) both exist and load; the only live
`model_zoo.load_url` calls are in Res2Net variants nothing calls, and `Res2Net_v1b.py:197` has its URL
path commented out — so **24 runs need zero network access for weights**.

## A.8 Assertions and gates

### A.8.1 The positional-pairing invariant — the silent-corruption landmine

`SrcDataset` pairs image↔mask **by sorted-list index, never by filename**:
`images` = `os.listdir` filtered to `.jpg`/`.png`
([Dataloader.py:14](../../Src/utils/Dataloader.py#L14)); `gts` = filtered to **`.tif`/`.png`**
([:15](../../Src/utils/Dataloader.py#L15)); the two lists are `sorted()` **independently**
([:16-17](../../Src/utils/Dataloader.py#L16-L17)); `__getitem__` returns `images[index]`, `gts[index]`
([:29-37](../../Src/utils/Dataloader.py#L29-L37)).

`filter_files()` ([:39-50](../../Src/utils/Dataloader.py#L39-L50)) is **not** a pairing guard: it
asserts only `len(images) == len(gts)` and drops any *positional pair* whose PIL sizes differ. **A
mis-pairing between two images of equal dimensions passes silently.**

Six assertions per assembled arm pool. **Any failure refuses to start training** — the driver will not
emit the command.

| # | Assertion | Why |
|---|---|---|
| **1** | `len(Image/) == len(GT/)` and `== 4447` (A0) or `5447` (A2/B/C) | the count `filter_files` checks |
| **2** | `{stem(f) for f in Image/} == {stem(f) for f in GT/}` | **the true invariant**; extension differences are harmless only while stem sets match |
| **3** | no stem appears twice with different extensions in either directory | the one construction that provably breaks parity — easy to create by mixing a `.jpg` render pool with `.png` CLS output |
| **4** | ★ Construct the real `SrcDataset(pool+'Image/', pool+'GT/', 352)` and assert `stem(ds.images[i]) == stem(ds.gts[i])` for **all** i, and `len(ds) == expected` | the direct check of the actual invariant, independent of any ASCII reasoning. `len(ds)` also catches a silent `filter_files` drop, which would shift the parity of everything after it |
| **5** | spot-check: for i = `len//2` and 3 random i, decode both files and assert equal dimensions and that the mask's white fraction is within the pool's expected range | catches a same-dimension mis-pairing that #4's name check would also catch — kept as an independent path |
| **6** | ★★ **Round-2 parity, proved rather than sampled.** Simulate the worst-case CLS output: the arm pool ∪ **all 4040** target names as `.png` in *both* `Image/` and `GT/`, then re-run #2–#4 on the simulated listing | CLS appends images as **`.png`** ([CLS.py:156](../../CLS.py#L156)) via the `.jpg → .png` rename at [Dataloader.py:141-142](../../Src/utils/Dataloader.py#L141-L142), so **round 2 trains on a mixed-extension pool that nobody has ever checked.** Sorted order is preserved under deletion of the same stems from both lists, and CLS writes image and GT together or skips both ([CLS.py:151,155-156](../../CLS.py#L151-L156)) — so parity on the full union **proves** parity for every possible subset. A pure filename computation, instant, no patch required |

Why parity holds for these name sets, for the record: `Image/` is 100 % `.jpg` and `GT/` 100 % `.png` in
every arm (census over all files: base 4447/4447, renders 4447/4447; no `.tif` anywhere in
`Dataset/Source` or `Dataset/LAKERED`), and the blocks sort disjointly — digits (`0x30-39`) <
`COD10K_` (`C`, `0x43`) < `DUP_` (`D`, `0x44`) < `SOD_` (`S`, `0x53`) < `camourflage_` (`c`, `0x63`) —
identically in both directories. But the plan asserts the invariant directly (#4, #6) rather than
relying on that reasoning.

### A.8.2 The six ABC gates — `rebuild/ABC/abc_preflight.py`

Mirrors `rebuild/C1/c1_preflight.py`: every gate returns a dict, none raises for a data failure, the
report is written to `rebuild/ABC/out/abc_preflight.json` **even on failure**, and the caller halts:

```python
report = PF_ABC.run_preflight(...)
if not report['all_passed']:
    raise SystemExit('ABC HALTED at preflight: %s -- see abc_preflight.json' % failed)
```

There is **no `--force`**.

| Gate | Checks | Reuses |
|---|---|---|
| **G1 signal** | `target_es` present, populated 75/75, all > 0, `sum(n_target) == 4033`; `k == 75`, `seed == 0`, `embedder == dinoL518`, centroids `(75, 1024)`; **AST scan of `rebuild/ABC/*.py` banning `test_es` and any clustering call** | calls `c1_preflight.gate_signal(['dinoL518'])` and `.gate_cluster_source(['dinoL518'])` for the data halves **unchanged**, and reuses `PF.PRAGMA`, `PF.BANNED_SIGNAL`, `PF.BANNED_CLUSTER_CALLS`, `PF.BANNED_CLUSTER_MODULES`, `PF.docstring_ids` for the source half — declarations reused, not copied, so ABC cannot drift from C1's gate |
| **G2 provenance / freshness** | ★ **ground rule 1, asserted**: `E0.step_independence()`, assert `n_forbidden == 0`; re-hash a random sample of `['raw','raw_gt','tgt','local']` against `rebuild/E0/out/e0_manifest.sha256` | **imports and calls `e0_regenerate.step_independence()`** — which already walks *all* of `rebuild/**/*.py`, so it covers `rebuild/ABC/*.py` automatically. This is the pattern `c1_preflight.gate_freshness` uses: *"E0's own `step_independence()` is imported and called rather than re-implemented, so C1 cannot drift from the gate E0 self-tested."* **Corollary the ABC scripts must respect:** any occurrence of `/tmp/claude-`, `_archive_stageC_old`, `evidence/artifacts` or `/scratchpad` as a non-docstring string literal in `rebuild/ABC/*.py` will make **E0's and C1's gates fail retroactively.** Keep such tokens in module docstrings, or annotate the line `# provenance-ok` — exemptions are reported, never hidden |
| **G3 one trainer, one eval path** | ★ **ground rule 2, asserted**: exactly one `MyTrain.py` and one `MyTest.py` in the tree (glob `**/MyTrain*.py`, `**/MyTest*.py`, excluding `.venv/`, `LAKE-RED/`, `rebuild/reference/`); no `MyTrain_seed.py`; and all six patches present (grep for `'--seed'`, `cudnn.deterministic`, `opt.source_root is None`, `opt.dataset`, `nargs='+'`, `Test/COD10K/Imgs`) | new; the glob-exclusion list matches E0's gate pruning |
| **G4 endpoint policy** | `Dataset/Test/CHAMELEON` appears in no scored path; `MyTest.py`'s `--dataset` choices exclude CHAMELEON and CAMO; `--val_root` resolves to `Dataset/Val/CAMO/` (250 + 250) | new |
| **G5 pool integrity** | §A.8.1 #1–#6 for every arm pool; base-subset `C.dir_digest` == committed agg hashes; the 1000 render masks `maxdiff == 0` vs `raw_gt`; the arm-C reproduction table (§A.3); `overlap(B, C) / 224.9 ∈ [0.7, 1.3]` (expected chance overlap `B²/N = 1000²/4447`), reported with the Jaccard index — C1 measured overlap at the chance rate (0.94–1.05) | new |
| **G6 determinism declared** | parse `MyTrain.py` and assert `cudnn.deterministic = True`, `cudnn.benchmark = False` and `set_random_seed(opt.seed)` are present (the gate runs in a different process, so it reads the source rather than the live flags) | new |

### A.8.3 Per-run completion assertions

Parsed from `Snapshot/ABC/{RUNID}/training_log.log`, for every run, before it is admitted to the metrics:

1. exactly **2** `Training Log` markers (both CSRDA rounds ran);
2. the set of `total_step` values parsed from `Global Step: \d+/(\d+)` == `{253}` (SINet) or `{127}` (SINet-v2), in **both** rounds;
3. last logged epoch == `039/040` (SINet) or `099/100` (SINet-v2);
4. `Tea_epoch_best.pth` exists;
5. wall clock within 2× the reference (SINet ≈ 104 min, SINet-v2 ≈ 131 min) — else flag as suspect;
6. round-1 `[Source Loader] Loaded {4447|5447}` and round-2 `Loaded {N}`; record `n_appended = N − pool_size`;
7. `[Target Loader] Loaded 4040`.

Any failure → the run is **discarded, re-run, and the discard logged**.
`Snapshot/ABC/{RUNID}/training_log.log` is git-tracked (only `*.pth` is ignored), so every run's
provenance is committed.

## A.9 Scripts, artifacts, and the `EXP ABC` log blocks

Three scripts in `rebuild/ABC/`, each in the E0–C1 idiom: `sys.path` preamble, `import common as C`,
`EXP = 'ABC'`, `OUT = C.exp_dir(EXP, 'out')`, `--no-log`, `def _p(m): print(m, flush=True)`,
`_p('=== s1 ... ===')` step headers, hand-rolled `csv.DictWriter`, `C.save_json`, and one
`C.log_block(...)` at the end.

| Script | Does | `TRAINS` | Emits |
|---|---|---|---|
| `abc_build_pools.py` | G1–G6, arm selection (B draw, C reproduction), pool assembly, §A.8.1 assertions | `NO` | `EXP ABC` block **#1** — the pre-flight of record; must PASS before any run |
| `abc_train.py` | **driver only.** Emits the exact command manifest and executes the single in-tree `MyTrain.py` per run, 2 GPUs, honouring §A.8.3 | `YES` | `EXP ABC` block **#2** — run accounting |
| `abc_evaluate.py` | `MyTest.py` per (run × endpoint), scores with `Eval/metrics.py`, computes σ̂ and the gaps, applies `PREREGISTRATION.md` | `NO` | `EXP ABC` block **#3** — the verdict |

`abc_train.py` is a **driver, not a second trainer**: it builds command strings from a table and runs
`MyTrain.py`. The commands are written to the tracked `rebuild/ABC/out/abc_commands.txt` **before**
execution, so what ran is auditable text.

> Unlike E0–C1, where later blocks **superseded** earlier ones, ABC's three blocks are sequential
> **stages** — each authoritative for its own content, none superseding another. Stated explicitly so
> the log stays readable. **ABC is also the first experiment with `TRAINS YES`**; every prior block
> records `TRAINS NO`.

`C.log_block` shapes, for reference: `metrics` are 2- or 3-tuples `(name, value[, provenance])`,
`thresholds` are 2-tuples `(condition_str, bool)`, `old_claims` are 3-tuples `(label, old_value,
verdict)`, `artifacts` are repo-relative strings.

**Old claims to pin in block #3** (a record for `REVISION_TABLE.md`; never an input, never a target):

| Label | Old value |
|---|---|
| C3.1 σ(Sα), all runs n=6 | `0.00356  [no code]` |
| C3.2 σ(Sα), distinct seeds n=4 | `0.00286  [no code]` |
| C3.4 Predicted ΔSα | `0.000111  [no code]` |
| C3.5 Shortfall vs 2σ | `64x (51x at B=2000)  [no code]` |
| C1.1 Cohen's *d* targeted-vs-random | `~0.10  [no code]` → now cross-checked against a *trained* outcome for the first time |

**Tracked artifacts under `rebuild/ABC/out/`:** `abc_preflight.json`, `abc_pools.json` (per-arm manifest:
file counts, agg hashes, RNG expressions, `n_appended`), `abc_stems_B_s{42,43,45}.txt`,
`abc_stems_C_a{1.0,0.5}.txt`, `abc_commands.txt`, `abc_runs.csv` (per-run wall clock, `total_step`,
`n_appended`, discard reasons), `abc_metrics.csv` (per run × endpoint × metric, **6 decimals**),
`abc_sigma.json`, `abc_verdict.json`.

## A.10 Evaluation protocol

### Endpoints

| Endpoint | Path | Count | Role | D2 contamination (lower bound) |
|---|---|---|---|---|
| **COD10K test** | `Dataset/Test/COD10K/{Imgs,GT}` | 2026 + 2026 | **primary** | 2/2026 = 0.1 % near-dup; 7 exact, MAE impact −1.24e-05 |
| **NC4K** | `Dataset/Test/NC4K/{Imgs,GT}` | 4121 + 4121 | **secondary** — reported, never decides | 1/4121 = 0.0 % |
| CHAMELEON | — | — | **EXCLUDED** | **41/76 = 53.9 %**; quantization tables differ in 41/41 pairs; nearest-distance gap: 41 below 5.51, next at 40.58 (7.4× jump) |
| CAMO | `Dataset/Val/CAMO/{Imgs,GT}` | 250 + 250 | **selection set only, never an endpoint** | 4/250 = 1.6 % |

CAMO is identical across arms so it cannot bias any comparison, but it is the published CAMO **test**
split ([MyTrain.py:221](../../MyTrain.py#L221), `D2_RESULTS.md` §3.6) and must never appear as a result.
Both exclusions are enforced in code by P3/P4's `choices` lists and re-checked by gate G4.

### Checkpoint, metrics, precision

**Evaluate `Snapshot/ABC/{RUNID}/Tea_epoch_best.pth` of the final round**, per arm per seed per
architecture, on both endpoints. Predictions to `Result/ABC/{RUNID}/{ENDPOINT}/` via the single in-tree
`MyTest.py --dataset {ENDPOINT}`.

Metrics come from the repo's `Eval/metrics.py`. `abc_evaluate.py` imports those classes directly and
reports **6 decimal places** (σ ≈ 0.0036, so 1e-6 is 0.03 % of σ). `Eval/MyEval.py`'s `.round(4)`
([MyEval.py:76](../../Eval/MyEval.py#L76)) is a 1e-4 quantum — 2.8 % of σ — which is tolerable for a
single number and **not** tolerable for a paired 3-seed difference.

| Metric | `metrics.py` | Quantization |
|---|---|---|
| **Sα** — primary | `:109-218` | **none** — float64 throughout |
| MAE | `:90-106` | **none** |
| Fβw | `:333-397` | **none** |
| **Eφ** | see below | variant-dependent |

**Eφ variant — DECIDED.** Report all three (`adpEm`, `meanEm`, `maxEm`, all already emitted) and
designate **`meanEm`** the headline Eφ, per field convention, **with its truncation disclosed**:
`Emeasure.cal_em_with_cumsumhistogram` does `pred = (pred*255).astype(np.uint8)` at
[metrics.py:274](../../Eval/metrics.py#L274), which **truncates**, as does `Fmeasure.cal_pr` at
[metrics.py:64](../../Eval/metrics.py#L64) for `meanFm`/`maxFm`. `adpEm` and `adpFm` threshold the float
array ([:51-53](../../Eval/metrics.py#L51-L53), [:235-237](../../Eval/metrics.py#L235-L237)) and are
quantization-free. The variants must never be mixed across tables.

**Rounding, corrected from the brief.** `Eval/metrics.py` needs **no** rounding fix, and adding one
would be wrong. B1's R6 fix belonged to B1's *own in-memory* scorer, which wrote
`(cam*255).astype(np.uint8)` (truncation) where [MyTest.py:76](../../MyTest.py#L76) writes
`cv2.imwrite(path, cam*255)` (rounding) — a 0.5-grey-level bias that made B1's endpoint MAE 0.073237
against D2's independently measured 0.074463, failing a declared threshold; `np.round` brought it to a
2.3e-07 delta. Anything reading the already-rounded PNG off disk
([MyEval.py:33-34](../../Eval/MyEval.py#L33-L34)) inherits that for free. **The rule: score from written
PNGs and add nothing; any script that scores from a checkpoint in memory must use `np.round(cam*255)`.**
`abc_evaluate.py` scores from written PNGs.

**★ The scorer is validated against a committed number before it produces any new number.** Before
scoring a single ABC run, `abc_evaluate.py` scores `Result/SINet/S2C` against `Dataset/Test/COD10K` and
asserts it reproduces B1's logged **Sα = 0.717216** and **MAE = 0.074463** (deltas < 1e-5). This was
confirmed during scoping: `Eval/MyEval.py` on those predictions returned Sα **0.7172**, wFβ **0.4746**,
MAE **0.0745**, adpEm 0.7599, meanEm 0.7439, maxEm 0.7954, adpFm 0.5468, meanFm 0.5543, maxFm 0.5965 —
identical to `Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt` — in **141.94 s**. It also discharges one of
the cross-checks `REBUILD_PLAN.md` §C3 asked for.

Also asserted: `pred.shape == gt.shape` for all 2026 / 4121.
[MyEval.py:37-38](../../Eval/MyEval.py#L37-L38) calls `cv2.resize(pred, (w,h), cv2.INTER_NEAREST)` with
`INTER_NEAREST` in the **third positional slot, which is `dst`, not `interpolation`** — inert here only
because [MyTest.py:72](../../MyTest.py#L72) upsamples to the GT shape before writing. Assert it rather
than rely on it.

## A.11 Run accounting, order of execution, and budget

### Unit costs — measured from `training_log.log` timestamps on this machine

| Run | Config | Measured |
|---|---|---|
| SINet `--iteration 2` | 39 ep × 253 × 2 rounds | **103.9 min** = 48.2 (r1) + **7.5 (CLS)** + 48.2 (r2) → **1.75 GPU-h** |
| SINet `--iteration 1` | 39 × 253 | 52.6 min (concurrent with a second job) / 48.2 alone |
| SINet-v2 `--iteration 1` | 99 × 253, bs 32 | **61.6 min** → `--iteration 2` ≈ 2 × 61.6 + ~8 (CLS) = **≈2.2 GPU-h** |
| Evaluation | COD10K 2026 imgs | **141.94 s measured**; NC4K (4121) ≈ 4.8 min by count → **≈7.2 min CPU per run, both endpoints** |

Boundaries: `Snapshot/SINet/S2C/training_log.log:1` / `:2` (r1 start 13:29:00) / `:1015` (r1 end
14:17:13) / `:1016` (second `Training Log`) / `:1017` (r2 start 14:24:41) / `:2030` (end 15:12:54).
**Contention:** `SINet/S2C_MT` and `SINet-v2/S2C_MT` both started 12:28:xx on 2026-08-12, one per GPU,
at 52.6 and 61.6 min against SINet's 48.2 min solo — so two concurrent jobs cost **~9 % each, not
100 %**. Hardware: 2 × RTX PRO 6000 Blackwell, 97887 MiB each, both idle; ~10–14 GB needed at
bs 16/352², so neither GPU is memory-bound.

### Totals

| Stage | Runs | GPU-h | Wall on 2 GPUs (×1.09) |
|---|---|---|---|
| SINet: 4 arms × 3 seeds | 12 | 21.0 | ≈11.5 h |
| SINet-v2: 4 arms × 3 seeds | 12 | 26.4 | ≈14.4 h |
| **Primary total (α = 1.0)** | **24** | **47.4** | **≈26 h** |
| Inference (`MyTest`, 6147 forwards/run) | 24 × 2 | ~2 (est., **unmeasured**) | ≈1 h |
| Evaluation (CPU, parallel, off critical path) | 24 × 2 | 2.9 CPU-h | 0 |
| **Primary campaign** | **24** | **≈49** | **≈27 h → 11 % of a 240 h budget** |
| Secondary α = 0.5, arm C only (2 arch × 3 seeds) | +6 | +11.9 | +6.5 h → **≈34 h, 14 %** |

**Disk:** SINet 3.2 GiB of checkpoints per run × 12 + SINet-v2 2.2 GiB × 12 ≈ **65 GiB**; arm pool
93 MiB + its CLS copy ≈ 186 MiB × 24 ≈ **4.4 GiB**. Total **≈70 GiB against 1510 GiB free.** After
evaluation, keep only `Tea_epoch_best.pth` + `Tea_{36..40}.pth` per run and delete the rest; `*.pth` is
gitignored either way.

### Order of execution

1. **Commit the six patches (§A.7) and `PREREGISTRATION.md`.** Before anything runs.
2. Run `abc_build_pools.py` → gates G1–G6 and all pool assertions must PASS → `EXP ABC` block #1.
3. **`SINet_A0_s42` — the very first run, alone, as the sanity gate.** Evaluate immediately;
   `|Sα − 0.7172| ≤ 0.0107` or **HALT and diagnose** (§A.3).
4. Remaining 11 SINet runs, two at a time (one per GPU), never two runs sharing a `source_root` —
   impossible by construction (§A.2).
5. All 12 SINet-v2 runs.
6. `abc_evaluate.py` → σ̂, the gaps, the pre-registered rule → `EXP ABC` block #3.
7. **Only if budget allows:** the 6 α = 0.5 runs, then re-run step 6 as a separate secondary block.

Every command runs with cwd = `/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD` (§A.5(f)).
`preflight.py --gpu {0,1}` is run once for the environment and backbone checks and its output archived;
its 5447-count WARNs are expected and enumerated — **the driver does not gate on its exit code.**

## A.12 Residual confounds and limitations, stated up front

1. **A0 is not a clean control** — mixture and per-image exposure move together (§A.5.1). A2 is the
   clean control; A0 is for paper-comparability.
2. **A2-vs-B carries a mask-provenance asymmetry** — 0.00575 mean white fraction on 18.4 % of the pool
   (§A.3). Δ(C − B) is unaffected.
3. **`--iteration 2` makes the arms differ in a second place** — CLS's `n_appended` (§A.5(c)).
   Recorded, tabulated, flagged above 5 %.
4. **Arm B carries selection variance that A0 and C do not** (§A.4). Per-arm sds reported beside σ̂.
5. **The arms are only partially paired.** cuDNN determinism reduces, and is not claimed to eliminate,
   kernel nondeterminism (§A.6).
6. **The allocation partition is soft.** k = 75 is the silhouette peak at **0.16**, with bootstrap ARI
   0.579 and seed ARI 0.616; only **50 of 75** clusters clear the 15-endpoint floor. B1's own honest
   statement is that **no k is strongly supported by the data**. A second k is *not* run: C1 already
   swept α at both k = 75 (dinoL518) and k = 50 (dinoL224) and both give the same verdict, so the
   k-sensitivity is discharged by citation rather than by more training runs.
7. **Arm C's separation from arm B is a concentration effect, per C1's own audit.** Targeted −
   ES-shuffled = **+0.0073** (ES wins 13/20, a coin flip); targeted − arbitrary-cluster = **−0.0649**
   (ES wins 4/20); the one consistent edge is over a random *direction*, **+0.0479** (18/20). The
   campaign is therefore testing whether a **concentrated, more-proximal, lower-effective-rank** arm
   trains better — which is exactly C1 §8.6's hypothesis — and **not** whether the ES signal
   specifically helps. This must be the paper's framing.
8. **Scope of any null.** D1 §5: *"D1 does not establish that new foregrounds could not help. It bounds
   only what this pipeline can add from its fixed pool."* Any null is scoped to *"targeting does not
   help once the foreground pool is exhausted"* — the DUTS/Oracle arm, which would test that bound, is
   **out of this campaign** (§A.13).
9. **A3 is UNRUN**, so the claim *"LAKE-RED output is far from the real target distribution"* is
   unavailable to this paper (§A.13).

## A.13 Closing statements

### (a) Inputs this plan depends on that are NOT confirmed present on disk

**None. Every input the campaign reads is present and verified.**

Confirmed present, with sizes/counts: both backbone weights
(`Src/model/SINet/resnet50-11ad3fa6.pth` 102,540,417 B, shared with SegMaR;
`Src/model/SINetV2/res2net50_v1b_26w_4s-3cf99910.pth` 103,197,949 B — both load, 320 and 524 tensors,
**no network access required for 24 runs**); `Dataset/Source/HKU-IS/{Image,GT}` 4447 + 4447;
`Dataset/Target/Image` 4040; `Dataset/LAKERED/output/HKU-IS/{images,masks}` 4447 + 4447;
`Dataset/Test/COD10K/{Imgs,GT}` 2026 + 2026; `Dataset/Test/NC4K/{Imgs,GT}` 4121 + 4121;
`Dataset/Val/CAMO/{Imgs,GT}` 250 + 250; all five arm-C artifacts (§A.3); `Src/utils/{tool,Dataloader}.py`,
`Eval/{metrics,MyEval}.py`, `CLS.py`; 1510 GiB free against ~70 GiB needed; `Stu_100.pth` confirmed
produced for SINet-v2 at `epoch_iter = 99`, satisfying `CLS.py:48`.

**Absent but not needed by this campaign:**

- **`Dataset/Test/{Image,GT}`** — absent, and needed only by the *unpatched* `MyTest.py:51-52`. Patch P3
  removes the dependency; patch P5 removes preflight's stale expectation. **Not a blocker.**
- **DUTS / the Oracle arm — explicitly OUT of this campaign, and nothing here needs it.** Searched
  `/home/ai-server` to depth 8 and the whole repo: **zero** files or directories matching `*DUTS*`; the
  only occurrence anywhere is prose at `LAKE-RED/LAKERED_HKUIS_REPRODUCTION.md:303`. All four arms draw
  exclusively from the 4447-foreground HKU-IS pool and its existing 4447 renders. **Confirmed: no arm,
  assertion, gate or metric in this plan reads or requires DUTS.** Its honest scope, for the follow-up:
  it would test **foreground exhaustion**, holding LAKE-RED render quality fixed; it does **not** test
  RealCamo. Folding it in would need DUTS-TR on disk **and** a full D2-standard within-dimension
  re-encode leakage sweep of the chosen subset — D2 §3.1 is the cautionary case, where exact hashing
  called CHAMELEON clean at 0/76 when the true figure was 41/76.
- **A3** — UNRUN (zero `EXP A3` blocks). Not an input to this campaign, but it bounds what the paper may
  say: the claim *"LAKE-RED output is far from the real target distribution"* is unavailable until A3
  runs. It is inference-only and every input is present.

### (b) The single decision or assertion where a wrong choice would most damage the result

**Patch P0 plus the §A.2 per-`RUNID` directory scheme, verified by gate G5's base-pool hash assertion.**

If `--source_root` is not honoured, all 24 runs train on `Dataset/Source/HKU-IS/` and the four arms
become the same run repeated. The failure has **no symptom** other than four arms whose Sα agree
suspiciously well — which reads as a clean, publishable null. Everything downstream (σ̂, both gaps, the
verdict) would be computed correctly from data that never differed. It is the only failure mode in the
campaign that produces a *credible* wrong answer rather than an error.

Second-worst, for completeness: the positional-pairing invariant (§A.8.1 #4/#6). It trains on shuffled
labels, `filter_files` is not a guard, and round 2's mixed-extension pool has never been checked by
anyone. Its failure is at least *visible* — the losses would be wrong — which is why it ranks below P0.

### (c) Provenance confirmation

**No `/tmp` path, no `_archive_stageC_old/` path, and no rescued cache is read by any training or
evaluation step in this plan.** The archive appears exactly once and only as a **documented source of
two numbers and one patch's content**: σ(Sα) = 0.003555 / 0.002287, quoted in §A.6 and in
`PREREGISTRATION.md` §2.8 as expected scale and never as the bar; and the 2-line seed patch of §A.7 P1,
whose content is re-applied **by editing the in-tree `MyTrain.py`** — that file is never imported,
copied, or read at run time. Gate **G2** asserts this mechanically by calling
`e0_regenerate.step_independence()`, which walks all of `rebuild/**/*.py` (now including
`rebuild/ABC/`) and must return `n_forbidden == 0`; gate **G3** asserts one `MyTrain.py` and one
`MyTest.py` exist in the tree and that no `MyTrain_seed.py` does. Arm C reads `rebuild/E0/cache/`, which
is **regenerated from primary data by E0**, not rescued, and gate G2 re-verifies a sample against
`rebuild/E0/out/e0_manifest.sha256`.

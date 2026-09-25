# NAVIGATION.md — how to run this package, and how to check it without running

## 0. What runs right now

Four commands. No datasets, no checkpoints, no GPU. Run them from the directory you extracted this
into, after `uv sync`.

```bash
# the contamination detector, against its own known-answer fixtures
python rebuild/D2_reaudit/detect_contamination.py --self-test     # 8 assertions

# formal equivalence testing -- the paper's TOST table, from committed metrics
python rebuild/DIAG/diag_tost.py

# the area control: does the error ordering survive partialling out area?
python rebuild/AC/ac_measure.py --no-log                          # 7/8, 6/8, AREA-ROBUST

# regenerate the cross-experiment ledger from committed artifacts
python rebuild/FinalPaper/make_results.py
```

The third one is the one worth your time. It is a real measured result from the paper, it
reproduces the committed numbers to within `4.9e-05`, and it needs none of our data — the
embeddings it reads travel with this package for exactly that reason.

If those four do what this section says, the rest of the package is what it claims to be.

---

## 1. Setup

```bash
uv sync          # Python 3.12, torch 2.11 + cu128
```

That covers everything runnable from this package. Scripts that touch the generator or DINOv2
embeddings additionally want `LAKE-RED/.venv`; they also need the generator itself, which is not
shipped, so in practice they are out of reach here regardless. Each script's docstring states which
interpreter it expects. The machine the measurements were taken on is recorded in
`rebuild/E0/out/e0_environment.json`.

### What is not in this package, and why

| Missing | Size | How to get it |
|---|---|---|
| `Dataset/` — all images | ~233 GB | public sources, below |
| `Snapshot/**/*.pth` — trained checkpoints | ~285 GB | retrain; every command is in `rebuild/ABC/out/abc_commands.txt` |
| `Result/` — predicted masks | ~18 GB | regenerate with `MyTest.py` |
| ImageNet backbones (ResNet-50, Res2Net-50) | ~200 MB | standard public weights; `preflight.py` checks for them |
| LAKE-RED generator + `LAKERED.ckpt` | ~6 GB | the LAKE-RED project |
| most of `rebuild/*/cache/` — embeddings | ~1.2 GB | regenerate with `rebuild/E0/e0_regenerate.py` |

What *is* here for the training runs: the exact commands, the pool manifests, all 108 per-run
training logs under `Snapshot/ABC/<runid>/`, and the per-run metrics in `rebuild/ABC/out/`. You can
audit what happened without rerunning it.

### Data layout

| Role | Set | Count | Path |
|---|---|---|---|
| Source (synthetic) | HKU-IS, LAKE-RED-composited | 4447 pairs | `Dataset/Source/HKU-IS/{Image,GT}` |
| Source (raw SOD) | HKU-IS raw | 4447 | `Dataset/Source/HKU-IS_raw/{imgs,gt}` |
| Target (unlabelled) | COD10K-train 3040 + CAMO 1000 | 4040 | `Dataset/Target/Image` |
| Endpoint | COD10K-test | 2026 | `Dataset/Test/COD10K/{Imgs,GT}` |
| Endpoint | NC4K | 4121 | `Dataset/Test/NC4K/{Imgs,GT}` |
| Checkpoint selection only | CAMO | 250 | `Dataset/Val/CAMO/{Imgs,GT}` |
| **Withdrawn** endpoint | CHAMELEON | 76 | `Dataset/Test/CHAMELEON/{Imgs,GT}` |

`rebuild/common.py` declares this machine-readably with expected counts, and every rebuild script
checks against it rather than trusting a path. `rebuild/E0/out/e0_manifest.sha256` hashes every
primary input, so you can confirm you hold the same bytes before comparing any number.

CHAMELEON appears here only because the paper withdraws it — see §9.

### Before any training

`preflight.py` checks the environment, backbone weights, dataset layout and integrity, output
paths, config coherence, and runs a real forward/backward smoke test. Exit 0 means clear to train.

```bash
python preflight.py --network SINet-v2        # --skip-smoke to avoid allocating a GPU
```

---

## 2. Run guide

| Tier | What it needs |
|---|---|
| **1** | nothing but this package |
| **2** | this package, including the embedding subset shipped with it |
| **3** | the public image datasets |
| **4** | trained checkpoints — GPU-days |

Commands are repo-relative, run from the extraction root. Where a block in
`results/REBUILD_LOG.txt` recorded a different `CMD`, that block is the authority.

| Tier | Exp | What it answers | Command | GPU | Needs |
|---|---|---|---|---|---|
| **1** | D2_reaudit | is the detector itself correct? | `python rebuild/D2_reaudit/detect_contamination.py --self-test` | no | — |
| **1** | DIAG.1 | equivalence testing on the main gaps | `python rebuild/DIAG/diag_tost.py` | no | committed metric tables |
| **1** | — | regenerate the ledger | `python rebuild/FinalPaper/make_results.py` | no | committed artifacts |
| **2** | AC | does the error ordering survive an area control? | `python rebuild/AC/ac_measure.py --no-log` | no | shipped embedding subset |
| **3** | D1 | is the foreground pool exhausted? | `python rebuild/D1/d1_foreground_exhaustion.py --steps s1,s2,s3,s4,s5,s6` | no | images |
| **3** | D2 | leakage sweep across the evaluation sets | `python rebuild/D2/d2_leakage_sweep.py --steps s2,s3,s4,s4b,s5,s6,s7,s8` | s8 only | images |
| **3** | D2_nc4k | is NC4K independent of COD10K-test? | `python rebuild/D2_nc4k/d2_nc4k_crosscheck.py` | no | images + a COD10K-train copy |
| **3** | D2_reaudit | the re-audit against an author-sourced CHAMELEON | `python rebuild/D2_reaudit/d2r_reaudit.py --steps s0,s4r,s4br,s5r,s6r,s7r --splits full` | s5r only | images + one checkpoint |
| **3** | A3 | how far synthetic sits from real | `python rebuild/A3/a3_appearance_signature.py --steps s1,s2,s3,s4,s5,s6` | yes | images + all three embedders' caches |
| **3** | C1 | targeted-vs-random pool distance | `python rebuild/C1/c1_preflight.py` then `c1_targeted_vs_random.py --tags dinoL518` | no | `*_cut_cls.npy`, `*_local_cls.npy` — **not shipped** |
| **3** | DIAG.2 | cluster composition | `python rebuild/DIAG/diag_clusters.py` | no | `dinoL518_cut_cls.npy` — **not shipped** |
| **3** | DIAG.4 | the geometric contamination extension | `python rebuild/DIAG/diag_chameleon_ext.py` | no | four image directories |
| **3** | E0 | regenerate and hash every primary input | `python rebuild/E0/e0_regenerate.py --steps s1,s2,s3,s3b,s5` then `--steps s4 --ngpu 2` | yes | everything, incl. the generator |
| **4** | ABC | the main four-arm campaign | `abc_build_pools.py` → `abc_train.py` → `abc_evaluate.py --arms A0,A2,B,C10` | 2 GPUs | images, trains 24 runs |
| **4** | T2 / OR / FX / SE | falsification, oracle, schedule, seed expansion | the same three scripts with `--tag t2\|or\|fx\|se` | 2 GPUs | images, trains |
| **4** | PC | positive control (mean teacher) | `pc_train.py --steps pools,train,log` then `pc_evaluate.py` | yes | images, trains |
| **4** | B1 | is the allocation signal real? | `b1_es_error_correlation.py --steps s1,s2,s3,s4,s5` | yes | images + checkpoints |
| **4** | T2C | is the error ordering ES-specific? | `t2c_measure.py --steps s1` then `--steps s2` | s1 only | images + 16 checkpoints |
| **4** | DIAG.3/.5 | boundary metrics and subgroups | `diag_boundary.py` then `diag_subgroups.py` | no | `Result/` predictions |

`rebuild/A1` has no script — it is a withdrawal argued by source reading. `REGRESS` is a one-block
reproduction gate, not an experiment.

---

## 3. What each directory is

| Directory | What it holds |
|---|---|
| **`rebuild/`** | the experiments this paper reports. **Start here.** One directory per experiment, each with its scripts, its declared thresholds and its outputs |
| **`results/REBUILD_LOG.txt`** | the append-only measurement log. The authority — see §4 |
| **`Snapshot/`** | per-run training logs, 108 of them, one per training run |
| `Src/`, `Eval/`, `MyTrain.py`, `MyTest.py`, `CLS.py`, `preflight.py` | the model, the trainer, inference, metrics |
| `Experiments/`, `Explanations/` | **the operational layer** — setup notes, gotchas and failure post-mortems from reproducing the published baselines. Not results this paper claims; read them when you want to *run* something. `Explanations/CHECKPOINT_LOADING_BUG.md` in particular documents a silent failure that cost us a week |
| `REBUILD_PLAN.md` | the pre-registration of the first diagnostic wave (E0, D1, D2, A1–A3, B1–B3, C1–C3), frozen 2026-08-30. Later campaigns carry their own `rebuild/<EXP>/PREREGISTRATION_*.md`. A2, B2, B3 and C3 were specified here and never ran |
| `REVISION_TABLE.md` | where a rebuilt number differed from the pre-rebuild package. Frozen 2026-09-08; its forward-looking sections are dated judgments |
| `REBUILD_FINDINGS.md` | the supersession analysis — which log blocks are live and which are superseded re-runs. Counts are as of 2026-09-09; the live ledger is `rebuild/FinalPaper/results.md` |

---

## 4. The evidence trail

Two things carry the whole story.

### `results/REBUILD_LOG.txt` — the append-only source of truth


Two things to know before searching it. Several blocks share one `EXP <id>` — either re-runs
(E0, D2, B1, C1, D2R, D2_NC4K) or declared stages (ABC's three).

And the log is strictly chronological, not dependency-ordered

### The per-experiment `*_RESULTS.md` files — the readable reading of each block

Each names the exact block timestamp it reads. The per-experiment convention is
`<ID>.md` = **setup** (scripts, directories, thresholds declared in advance — no numbers),
`<ID>_RESULTS.md` = **verified results**.

| Experiment | Setup | Verified results |
|---|---|---|
| E0 | [rebuild/E0/E0.md](rebuild/E0/E0.md) | [rebuild/E0/E0_RESULTS.md](rebuild/E0/E0_RESULTS.md) |
| D2 | [rebuild/D2/D2.md](rebuild/D2/D2.md) | [rebuild/D2/D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) |
| D2_nc4k | [rebuild/D2_nc4k/README.md](rebuild/D2_nc4k/README.md) | *(none — see §5.1)* |
| D2_reaudit | [rebuild/D2_reaudit/REAUDIT_PLAN.md](rebuild/D2_reaudit/REAUDIT_PLAN.md) | [rebuild/D2_reaudit/D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) |
| D1 | [rebuild/D1/D1.md](rebuild/D1/D1.md) | [rebuild/D1/D1_RESULTS.md](rebuild/D1/D1_RESULTS.md) |
| B1 | [rebuild/B1/B1.md](rebuild/B1/B1.md) | [rebuild/B1/B1_RESULTS.md](rebuild/B1/B1_RESULTS.md) |
| C1 | [rebuild/C1/C1.md](rebuild/C1/C1.md) | [rebuild/C1/C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) |
| A3 | [rebuild/A3/A3.md](rebuild/A3/A3.md) | [rebuild/A3/A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) |
| ABC | [rebuild/ABC/ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md) | [rebuild/ABC/ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) |

> **The rule to trust: if a results markdown and its log block ever disagree, the log wins.**
> Each `*_RESULTS.md` states this itself.

---

## 5. The experiment map

In dependency order. One line each; the numbers are in the log block and the readable file.

| Experiment | What it establishes | Log block | Readable file | Key artifacts |
|---|---|---|---|---|
| **E0** | Regenerates every input from primary data and hashes it, so later experiments read a verified manifest rather than the old package | `EXP E0` ×4 | [E0_RESULTS.md](rebuild/E0/E0_RESULTS.md) | [rebuild/E0/out/](rebuild/E0/out/) |
| **D2** | Whether the CHAMELEON evaluation set overlaps the COD10K-train split the models train on | `EXP D2` ×5 | [D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) | [rebuild/D2/out/](rebuild/D2/out/) |
| **D2_nc4k** | Whether NC4K collides with COD10K-test — i.e. whether the second endpoint is independent | `EXP D2_NC4K` ×2 | *setup only:* [README.md](rebuild/D2_nc4k/README.md) | [rebuild/D2_nc4k/out/](rebuild/D2_nc4k/out/) |
| **D2_reaudit** | Re-runs the CHAMELEON audit against an author-sourced copy of the dataset, and releases the detector | `EXP D2R` ×4 | [D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) | [out/](rebuild/D2_reaudit/out/), [release/](rebuild/D2_reaudit/release/) |
| **D1** | Whether the source foreground pool is exhausted, and for the pool that actually feeds training | `EXP D1` ×1 | [D1_RESULTS.md](rebuild/D1/D1_RESULTS.md) | [rebuild/D1/out/](rebuild/D1/out/) |
| **B1** | Whether the ES allocation signal is valid, which clusters are weak, and how the choice of embedder moves both | `EXP B1` ×4 | [B1_RESULTS.md](rebuild/B1/B1_RESULTS.md) | [rebuild/B1/out/](rebuild/B1/out/) |
| **C1** | Targeted-vs-random pool distance, plus the attribution audit of what actually produces the separation | `EXP C1` ×4 | [C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) | [rebuild/C1/out/](rebuild/C1/out/) |
| **A3** | How far the generator's synthetic renders sit from the real target distribution, with real-vs-real controls | `EXP A3` ×1 | [A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) | [rebuild/A3/out/](rebuild/A3/out/) |
| **ABC** | The 3-seed A/B/C/A2 training campaign — the measured verdict against the pre-registered rule | `EXP ABC` ×3 | [ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) | [rebuild/ABC/out/](rebuild/ABC/out/) |
| **T2** | The falsification arms: does destroying (CSHUF) or reversing (CINV) the signal cost anything, at allocation shape held fixed | `EXP T2` ×4 | [T2_RESULTS.md](rebuild/ABC/T2_RESULTS.md) | [rebuild/ABC/out/t2/](rebuild/ABC/out/t2/) |
| **T2C** | Whether the pixel-over-structure error ordering is specific to the ES signal, or general | `EXP T2C` ×1 | [T2C_RESULTS.md](rebuild/T2C/T2C_RESULTS.md) | [rebuild/T2C/out/](rebuild/T2C/out/) |
| **AC** | Area control: whether T2C's ordering survives partialling out object and band area. Inference-free | `EXP AC` ×1 | [AC_RESULTS.md](rebuild/AC/AC_RESULTS.md) | [rebuild/AC/out/](rebuild/AC/out/) |
| **PC** | Positive control: a mean-teacher arm the rule *should* detect, to show the null is not an insensitive instrument | `EXP PC` ×2 | [PC_RESULTS.md](rebuild/PC/PC_RESULTS.md) | [rebuild/PC/out/](rebuild/PC/out/) |
| **OR** | Oracle: replaces the uncertainty score with ground-truth per-cluster error. A declared upper bound, never a method | `EXP OR` ×3 | *setup only:* [PREREGISTRATION_OR.md](rebuild/OR/PREREGISTRATION_OR.md) | [rebuild/ABC/out/or/](rebuild/ABC/out/or/) |
| **FX** | Unpins the step schedule, to test whether the fixed optimisation budget is what suppresses the effect | `EXP FX` ×4 | [FX_RESULTS.md](rebuild/FX/FX_RESULTS.md) | [rebuild/ABC/out/fx/](rebuild/ABC/out/fx/) |
| **SE** | Seed expansion to n = 8 on B, C10, CSHUF, CINV, under its own frozen rule. **Closed: all 16 comparisons WITHIN NOISE** | `EXP SE` ×4 | [PREREGISTRATION_SE.md](rebuild/SE/PREREGISTRATION_SE.md) + [abc_verdict.json](rebuild/ABC/out/se/abc_verdict.json) | [rebuild/ABC/out/se/](rebuild/ABC/out/se/) |
| **C2** | Follow-on to C1's attribution audit | `EXP C2` ×3 | *no results markdown — see §5.1* | — |
| **REGRESS** | Regression check that re-scoring the reference arms still reproduces the committed metrics | `EXP REGRESS` ×1 | *no results markdown — see §5.1* | [rebuild/ABC/out/regress/](rebuild/ABC/out/regress/) |
| **DIAG** | Post-hoc diagnostics feeding the paper's tables: TOST, subgroup/boundary metrics, cluster composition | *(no EXP block — see §5.1)* | — | [rebuild/DIAG/out/](rebuild/DIAG/out/) |
| **A1** | Withdraws the generator-conditioning-bottleneck explanation by source reading | *(no EXP block — a withdrawal)* | [A1_SCOPING.md](rebuild/A1/A1_SCOPING.md) | — |

### 5.1 The directories with no results markdown

Six experiments have no `*_RESULTS.md`, for four different reasons. None of them is an omission.

| Experiment | Why, and where its numbers are |
|---|---|
| **D2_nc4k** | `README.md` is setup only and says so. Numbers live in the `EXP D2_NC4K` block; the NC4K/COD10K-test rows are reported in [CLEAN_PROTOCOL.md](rebuild/D2_reaudit/CLEAN_PROTOCOL.md) |
| **OR** | Completed 2026-09-19, after the last results-markdown pass. Its numbers are in the three `EXP OR` blocks and [rebuild/ABC/out/or/](rebuild/ABC/out/or/); the rule they are judged against is [PREREGISTRATION_OR.md](rebuild/OR/PREREGISTRATION_OR.md) |
| **SE** | **Closed 2026-09-22.** The verdict is machine-readable at [abc_verdict.json](rebuild/ABC/out/se/abc_verdict.json) and the per-run rows are in `rebuild/ABC/out/se/abc_metrics.csv`; there is no prose `SE_RESULTS.md`. All 16 comparisons — 4 gaps × 2 architectures × 2 endpoints — returned WITHIN NOISE at n = 8, and the decisive `B→C10` gap shrank relative to n = 3 |
| **C2** | Has `EXP C2` blocks but no directory of its own; it extends C1's attribution audit and its artifacts live under [rebuild/C1/out/](rebuild/C1/out/) |
| **REGRESS** | A one-block reproduction gate, not an experiment. Its verdict is the block itself |
| **DIAG** | Post-hoc derivation from already-committed artifacts, so it has no `EXP` block by design — the same standing as the pool-mechanics audit in §6.4. Its scripts write [Paper](rebuild/DIAG/out/) tables directly |

**FX and OR completed after the paper snapshot** (`rebuild/FinalPaper/`), so read their log blocks
rather than assuming the consolidated documents already reflect them.

---

## 6. Where the headline contributions live

### 6.1 The measured negative result — the A/B/C campaign

| File | What it is |
|---|---|
| `EXP ABC` block 1 of 3 — `2026-09-04T23:36:25+05:30` | Pre-flight: pool construction and the gates that had to pass before training |
| `EXP ABC` block 2 of 3 — `2026-09-05T22:56:22+05:30` | Run accounting: the 24 runs, wall clock, per-arm appends. The first block in the rebuild with `TRAINS YES` |
| `EXP ABC` block 3 of 3 — `2026-09-06T13:37:26+05:30` | The verdict |
| [rebuild/ABC/PREREGISTRATION.md](rebuild/ABC/PREREGISTRATION.md) | The decision rule, committed before run 1 and never edited after any number existed |
| [rebuild/ABC/out/abc_metrics.csv](rebuild/ABC/out/abc_metrics.csv) | Per-run, per-endpoint metrics — the raw table behind the verdict |
| [rebuild/ABC/out/abc_verdict.json](rebuild/ABC/out/abc_verdict.json) | The pre-registered rule applied, machine-readable |
| [rebuild/ABC/out/abc_sigma.json](rebuild/ABC/out/abc_sigma.json) | The seed-spread estimate the verdict is judged against |
| [rebuild/ABC/POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) | How Stage C's added images enter training and why the step budget cannot grow — see §3.4 |

Also in that directory: `abc_preflight.json`, `abc_pools.json`, `abc_runs.csv`, `abc_discards.json`
(discarded-and-re-run runs), `abc_commands.txt` (exact commands).

### 6.2 The synthetic-vs-real coverage finding (A3)

| File | What it is |
|---|---|
| `EXP A3` block — `2026-09-08T10:34:47+05:30` | Authoritative record, single block |
| [rebuild/A3/A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) | The reading of it, with the scope caveat stated up front |
| [rebuild/A3/out/a3_coverage.csv](rebuild/A3/out/a3_coverage.csv) | Coverage — precision/recall against the real set, per embedder and *k* |
| [rebuild/A3/out/a3_probe_table.csv](rebuild/A3/out/a3_probe_table.csv) | The AUC ladder: headline separation plus the real-vs-real and quality-sweep controls |
| [rebuild/A3/out/a3_distance.csv](rebuild/A3/out/a3_distance.csv) | MMD² and effective-rank table |
| [rebuild/A3/out/a3_decision.json](rebuild/A3/out/a3_decision.json) | Declared thresholds resolved to PASS/FAIL |
| [rebuild/A3/A3_SCOPING.md](rebuild/A3/A3_SCOPING.md) | Six open questions resolved against committed artifacts *before* any A3 code was written |

### 6.3 The benchmark-contamination contribution (D2 + D2_reaudit)

**This contribution stands independently of whether the method worked.**

| File | What it is |
|---|---|
| `EXP D2` ×5 blocks | The original audit on the local dataset copy |
| `EXP D2R` ×4 blocks (the fourth is the one cited) | The re-audit against an author-sourced copy |
| [rebuild/D2/D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) | Readable reading of the D2 blocks |
| [rebuild/D2_reaudit/D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) | Readable reading of the re-audit, including where it corrects D2 |
| [rebuild/D2_reaudit/detect_contamination.py](rebuild/D2_reaudit/detect_contamination.py) | The released detector |
| [rebuild/D2_reaudit/out/chameleon_contaminated.json](rebuild/D2_reaudit/out/chameleon_contaminated.json) | The leaked-image list |
| [rebuild/D2_reaudit/CLEAN_PROTOCOL.md](rebuild/D2_reaudit/CLEAN_PROTOCOL.md) | Which evaluation columns can be reported as independent measurements, and which cannot |
| [rebuild/D2_reaudit/release/](rebuild/D2_reaudit/release/) | Self-contained bundle: `README.md`, `detect_contamination.py`, `chameleon_contaminated.json`, `CLEAN_PROTOCOL.md` |

Start with [release/README.md](rebuild/D2_reaudit/release/README.md) — it is written for someone
outside this project.

### 6.4 Pool mechanics — CSRDA Stage C additions and the `total_step` ceiling

The claim under test: *Stage C's added generations cannot expand the optimization budget and can
only rearrange the mixture within it.* The audit traces pool assembly, ordering, sampling and
`zip()` truncation across both CSRDA rounds, and reports where the usual framing of that claim is
wrong — see its **verdict up front**, §7(a) for the corrected one-sentence statement, and §7(c)
for whether it moves the ABC null.

**This is a code trace, not a measured experiment: it has no `EXP` block of its own, and says so.**
Its evidence is `file:line` citations into the real training code, its probe, and the already
committed `abc_runs.csv` — so the §4 rule is not violated. The measured half of the claim is the
`total_step` threshold in **`EXP ABC` block 2 of 3**.

| File | What it is |
|---|---|
| [rebuild/ABC/POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) | The audit. §1 loader construction and shuffling, §2 what `zip()` truncation does, §3 where Stage C's re-renders sit, §4 what CLS appends for round 2, §5–6 synthesis and cross-check, §7 closing statements, Appendix: defects found while tracing |
| [rebuild/ABC/pool_mechanics_probe.py](rebuild/ABC/pool_mechanics_probe.py) | Probe of record — self-contained, repo-relative. `.venv/bin/python rebuild/ABC/pool_mechanics_probe.py` |
| `EXP ABC` block 2 of 3 — `THRESHOLD` on `total_step` | The measured confirmation that the step budget stayed pinned in both rounds of every run |
| [rebuild/ABC/out/abc_runs.csv](rebuild/ABC/out/abc_runs.csv) | Per-run pool sizes and round-2 append counts the audit's arithmetic reads |
| [MyTrain.py](MyTrain.py), [Src/utils/Dataloader.py](Src/utils/Dataloader.py), [CLS.py](CLS.py) | The code under trace, byte-identical to what the 24 runs executed (the audit records the `git diff` check) |

---

## 7. The planning and audit-trail documents

| File | What it contains |
|---|---|
| [REBUILD_PLAN.md](REBUILD_PLAN.md) | The pre-registered plan: clean-slate rules (§0), the discarded-assumptions log (§0.2), data-provenance map (§1), representation table (§2), per-experiment deliverables (§2.5), experiment list (§3), and the frozen record of old claims (§4) |
| [REVISION_TABLE.md](REVISION_TABLE.md) | Every place a rebuilt number differs from the old package, with the reason and the log block that produced it; also tracks which experiments remain outstanding |
| [ABC_SCOPING.md](ABC_SCOPING.md) | Pre-execution scoping audit for the A/B/C campaign; flags where the brief's premises were wrong |
| [rebuild/ABC/ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md) | The campaign specification, approved before any ABC code existed |
| [rebuild/A3/A3_SCOPING.md](rebuild/A3/A3_SCOPING.md) | A3's scoping pass |
| [rebuild/C1/C1_PLAN.md](rebuild/C1/C1_PLAN.md) | C1's plan |
| [rebuild/D2_reaudit/REAUDIT_PLAN.md](rebuild/D2_reaudit/REAUDIT_PLAN.md) | The re-audit's setup document (it serves as D2R's `<ID>.md`; there is no `D2R.md`) |

---

## 8. How to reproduce a number

Every experiment is one directory, `rebuild/<EXP>/`, holding its script(s), its `out/` artifacts,
and — where it declares one — its setup and results markdowns. Each has a matching `EXP <EXP>`
block in [results/REBUILD_LOG.txt](results/REBUILD_LOG.txt) whose `CMD` field is the exact command
that produced it and whose `ARTIFACTS` field names the files it wrote; the readable `*_RESULTS.md`
cites that block by timestamp. Shared helpers are in [rebuild/common.py](rebuild/common.py). Large
binaries — embeddings and caches, regenerated renders, duplicate/pair image exports, inference
output, checkpoints, run logs — are gitignored and regenerable by the experiment that owns them
(`.gitignore` marks each as regenerable, and names the regenerating script for the bulky image
exports), and the primary inputs they derive from
are verified by hash against
[rebuild/E0/out/e0_manifest.sha256](rebuild/E0/out/e0_manifest.sha256). **`./Result/` — the model
predictions — is excluded from what is shared** (gitignored, and large); nothing in this document
depends on it.

In the distributed supplement the `rebuild/` directory is included here, not sent separately, and
one subset of the otherwise-gitignored embedding cache travels with it
(`rebuild/E0/cache/dinoL518_{tgt,test}_cls.npy` and its name map) so that the area control runs with
none of the image data present. See `README.md`.

---

## 9. What is NOT here — scope caveats

Each is documented where it was decided; none is re-argued here.

- **CHAMELEON is withdrawn as an endpoint**, and CAMO is the checkpoint-selection set, not an
  endpoint — see [D2_RESULTS.md](rebuild/D2/D2_RESULTS.md), the `EXP D2` / `EXP D2R` blocks, and
  the input table in [ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md).
- **Any null is scoped to an exhausted foreground pool** — see
  [D1_RESULTS.md](rebuild/D1/D1_RESULTS.md).
- **A3 characterizes the distribution; it is not a training-utility bound** and must not be read as
  one — stated in the `EXP A3` block's `NOTES` and at the top of
  [A3_RESULTS.md](rebuild/A3/A3_RESULTS.md).
- **The A/B/C comparison tests concentration-driven targeting, not the uncertainty signal in
  isolation** — see the attribution audit in [C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) §8 and
  [rebuild/C1/out/c1_attribution.csv](rebuild/C1/out/c1_attribution.csv).
- **The campaign's power against its own pre-registered statement** is discussed in
  [ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) and quantified by
  [abc_sigma.json](rebuild/ABC/out/abc_sigma.json).
- **Stage C's added images were trained on, not excluded** — the mechanism is dilution of
  per-epoch exposure under a fixed step budget, and A0 is an unclean control in both rounds. See
  [POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) §7(a) and §7(c).
- **Experiments not run:** A1, A2, B2, B3, C3 remain outstanding, and C2 has no `EXP C2` block of
  its own — see the status line and its note at the top of
  [REVISION_TABLE.md](REVISION_TABLE.md).

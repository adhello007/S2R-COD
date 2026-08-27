# Setup — running the Stage C evidence package from scratch

> Entry point: [EVIDENCE_README.md](EVIDENCE_README.md) · Rationale:
> [EVIDENCE_APPROACH.md](EVIDENCE_APPROACH.md) · Run-book: [EVIDENCE_SCRIPTS.md](EVIDENCE_SCRIPTS.md)

**One command tells you whether this machine is ready:**

```bash
LAKE-RED/.venv/bin/python evidence/setup_check.py
```

It runs 34 checks — interpreter, virtualenv, package pins, GPU, every dataset directory with its
expected file count, checkpoints, DINOv2 weights, source documents, rescued artifacts, and the
hash manifests — and prints `PASS` / `FAIL` / `WARN` per row with the fix. `FAIL` blocks the
experiments named beside it; `WARN` marks optional inputs. Exit code 0 means ready.

On the machine this package was built on, all 34 pass.

---

## 0. What you need

| | |
|---|---|
| **OS** | Ubuntu 24.04.4 LTS, kernel 7.0.0-28-generic |
| **GPU** | 2 × NVIDIA RTX PRO 6000 Blackwell (97 GB each), driver 595.84. **One GPU is enough**; no experiment needs both. |
| **CUDA** | 12.8 via the torch wheel. Blackwell is `sm_120`, so **cu128 wheels are mandatory** — cu121 builds fail at load. |
| **Disk** | ~60 GB: datasets ~15 GB, `LAKERED.ckpt` 6 GB, rescued artifacts 3.42 GB, checkpoints ~1 GB, DINOv2 cache 1.5 GB. |
| **Python** | 3.12.3 (`.python-version` pins 3.12) |
| **Package manager** | `uv` 0.12.0. This project does **not** use conda. |
| **CPU-only?** | A1, A2, C2, C3, D1, D2 run without a GPU. A3, B1, B3 need one (B1 for inference, A3/B3 only if re-embedding). |

**No experiment in this package trains a model.** The most expensive item, C3, re-evaluates
prediction files from six *already completed* runs.

---

## 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version        # expect 0.12.0 or newer
```

## 2. Create the virtualenv

There are two venvs in this tree and **they are not interchangeable**:

- **`LAKE-RED/.venv` — the one every command uses.** Has `timm` and `transformers`.
- `.venv` at the repo root — has **no `timm`**, so every DINOv2 experiment fails in it.

Every command in the run-book spells out the interpreter, so there is nothing to activate:

```bash
cd LAKE-RED && uv sync && cd ..
```

## 3. Pin the packages

These are the exact versions every number in the package was produced with. `setup_check.py`
compares against this list and names any drift.

```bash
LAKE-RED/.venv/bin/python -m uv pip install \
  "torch==2.11.0+cu128" "torchvision==0.26.0+cu128" \
  --index-url https://download.pytorch.org/whl/cu128

LAKE-RED/.venv/bin/python -m uv pip install \
  "timm==1.0.28" "transformers==5.15.1" "scikit-learn==1.9.0" \
  "scikit-image==0.26.0" "numpy==2.5.2" "opencv-python-headless==5.0.0.93" \
  "matplotlib==3.11.1" "scipy==1.18.0" "PyYAML==6.0.3" "einops==0.8.2" \
  "omegaconf==2.3.1" "huggingface-hub==1.28.0"
```

| package | version | used for |
|---|---|---|
| torch / torchvision | 2.11.0+cu128 / 0.26.0+cu128 | everything; cu128 is mandatory on Blackwell |
| timm | 1.0.28 | DINOv2 weights via the HF hub |
| transformers | 5.15.1 | present, not load-bearing |
| scikit-learn | 1.9.0 | k-means, the logistic-regression probe |
| scikit-image | 0.26.0 | `slic` — LAKE-RED's own superpixel call |
| numpy | 2.5.2 | |
| opencv-python-headless | 5.0.0.93 | the evaluation read path |
| matplotlib | 3.11.1 | figures |
| scipy | 1.18.0 | Spearman ρ, binomial tests |
| PyYAML / einops / omegaconf | 6.0.3 / 0.8.2 / 2.3.1 | LAKE-RED config and module imports |

## 4. Model weights

**DINOv2 (auto-downloads, ~1.5 GB).** Pinned exactly, because the embedder choice *reversed* one of
our conclusions (revision R-a) — a weaker embedder gave 0% acceptance where DINOv2 gives ~20%:

```bash
LAKE-RED/.venv/bin/python - <<'EOF'
import timm
for m in ['vit_large_patch14_dinov2.lvd142m', 'vit_base_patch14_dinov2.lvd142m']:
    timm.create_model(m, pretrained=True, num_classes=0)
    print('cached', m)
EOF
```

Lands in `~/.cache/huggingface/hub/`. For an offline machine, copy that directory across and set
`HF_HUB_OFFLINE=1`.

**LAKE-RED checkpoint (6.0 GB) → `LAKE-RED/ckpt/LAKERED.ckpt`.** Needed by A1 for the live
conditioning-tensor measurement. Source: the LAKE-RED release (see `LAKE-RED/README.md`).

**SINet reproduction checkpoints → `Snapshot/SINet/S2C/`.** `Stu_40.pth` and `Tea_epoch_best.pth`,
188 MB each, needed by B1. These come from our own reproduction run (Sα 0.7172), not from upstream.

## 5. Datasets

Download links are in the upstream [README.md](README.md). `setup_check.py` verifies every count
below, because a silently short directory would change a measurement rather than raise an error.

| path | files | needed by |
|---|---|---|
| `Dataset/Source/HKU-IS/{Image,GT}` | 4447 each | A2, D1 |
| `Dataset/Source/HKU-IS_raw/{imgs,gt}` | 4447 each | A3, D1 |
| `Dataset/LAKERED/input/HKU-IS/validation/{images,masks}` | 4447 each | A1, A2 |
| `Dataset/LAKERED/output/HKU-IS/{images,masks}` | 4447 each | A2, A3, B3, C1, D1 |
| `Dataset/Target/Image` | 4040 | A3, B3, C1, D2 |
| `Dataset/Test/COD10K/{Imgs,GT}` | 2026 each | B1, C3, D2 |
| `Dataset/Val/CAMO/{Imgs,GT}` | 250 each | B1, D2 |
| `Dataset/Test/CAMO/Imgs` | 250 | D2 |
| `Dataset/Test/CHAMELEON/Imgs` | 76 | D2 |
| `Dataset/Test/NC4K/Imgs` | 4121 | D2 |

Two facts about these directories that the experiments depend on, both measured rather than assumed:

- **Mask polarity differs between sources.** `LAKERED/input/.../masks` stores background=white (it
  *is* the inpainting mask); the three GT sets store object=white. Reading it backwards inverts A2's
  headline from 18% to 82%. A2 detects polarity per source rather than trusting either convention.
- **`Source/HKU-IS/GT` is not the same mask set as `HKU-IS_raw/gt`** (mean |Δ| 5.7e-3, 0/4447
  identical). The set training reads was processed differently from the set generation used.

## 6. Rescued evidence artifacts

C3 (the noise floor) reads prediction files from six completed training runs, and B1's cross-run
replication reads their checkpoints. Those were produced once and are **not regenerable without
retraining**, which this package exists to avoid. They live in `evidence/artifacts/` (3.42 GB,
gitignored) with hashes committed under `evidence/manifests/`.

```bash
LAKE-RED/.venv/bin/python evidence/e0_rescue.py --dry-run   # report, write nothing
LAKE-RED/.venv/bin/python evidence/e0_rescue.py             # ~7 s
```

Verify at any time, from the repo root:

```bash
sha256sum -c evidence/manifests/MANIFEST.sha256      # 81 singleton files
sha256sum -c evidence/manifests/SOURCES.sha256       # 3 immutable source documents
for r in s42 s43 s45 s46 repB repC; do sha256sum -c evidence/artifacts/pred_$r.sha256; done
```

**If `evidence/artifacts/` is absent and cannot be restored**, the honest position is in
[EVIDENCE_README.md](EVIDENCE_README.md) § Honest limits: C3 is unreproducible without 6 × 1.8 h of
retraining, and B1 degrades to a single-run correlation. Every other experiment still runs — A3, B3
and C1 take `--recompute` and rebuild their feature caches from images on the GPU.

## 7. Smoke test

```bash
LAKE-RED/.venv/bin/python evidence/setup_check.py            # 34 checks, expect exit 0
LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py --no-log
```

A1 with `--no-log` prints its block without touching the results log. Expect
`conditioning_width = 48`, `vec_fg_shape_live = (1, 16, 3)`, and 6/6 thresholds PASS. If that works,
the whole package works.

---

## 7b. Reading the results

```bash
LAKE-RED/.venv/bin/python evidence/summarize_log.py
```

Rebuilds [results/RESULTS_SUMMARY.md](results/RESULTS_SUMMARY.md) from the log — every experiment's
status, headline numbers, revisions surfaced, and what has not reproduced — plus a JSON twin for
programmatic access. Neither is hand-maintained, so neither can drift from the evidence.

## 8. Runtimes and what each experiment needs

| id | needs | GPU | runtime |
|---|---|---|---|
| E0 | the source scratchpad (once) | no | 7 s |
| A1 | `ddpm.py`, config, `LAKERED.ckpt`, LAKERED input pair | optional | 7 s |
| A2 | 4447 masks × 4 sources | no | 12 s |
| A3 | DINOv2 caches or `--recompute`; `HKU-IS_raw/imgs`, `Target/Image` | yes | 5–25 min |
| B1 | `Snapshot/SINet/S2C` ckpts, COD10K-test, CAMO-val | yes | ~15 min |
| B2 | B1's output | no | < 2 min |
| B3 | DINOv2 + InceptionV3 caches | yes | 5–20 min |
| C1 | DINOv2 caches, B1's output | no | ~3 min |
| C2 | nothing (closed form) | no | < 1 s |
| C3 | rescued predictions, COD10K-test GT | no | 10–20 min |
| D1 | HKU-IS and LAKERED directories | no | ~3 min |
| D2 | all dataset splits | no | 5–10 min |

`B2` and `C1` consume `B1`; `C3` consumes `C1`. Otherwise the order is free. Roughly **one hour**
total, none of it training.

---

## 9. Troubleshooting — the traps we actually hit

| symptom | cause and fix |
|---|---|
| `No module named 'timm'` | You used the root `.venv`. Use `LAKE-RED/.venv/bin/python`. |
| CUDA error / no kernel image on load | cu121 wheels on `sm_120`. Reinstall torch from the cu128 index. |
| timm asserts on input size | DINOv2 hard-asserts its pretrained 518 input at `timm/layers/patch_embed.py:121`. Pass `img_size=` explicitly; the scripts already do. |
| `Dataset/Test/GT` not found | Historical path. The tree is now `Dataset/Test/COD10K/GT`. The original `audit6.py` still hardcodes the old path — C3 ships a corrected port. |
| A2 reports foreground ≈ 0.81 | Mask polarity inverted. See § 5; A2 detects it per source. |
| `sha256sum -c` fails on a manifest | Run it **from the repo root** — the listings use repo-relative paths. |
| `SOURCES.sha256` fails after editing a doc | It hashes only the three *immutable* sources. If it fails, an audit or `PRIOR_REVIEW.md` changed — that is a real problem, not a stale manifest. |
| The results log grew several blocks for one experiment | Expected while a script is being fixed. Use `--no-log` while iterating; the log is append-only and nothing is ever removed. E0 has 3 blocks and A2 has 5, each explaining itself in `NOTES`. |

## 10. What cannot be reproduced, whatever you install

Stated here so it is not discovered late:

- **The iteration-2 pool directories** (`HKU-IS_iteration2`, `-SINet`, `-SINetV2`) were deleted. So
  `|Ds|` = 6824 / 7824 / 8824 and "the pool is 30–35% real target imagery" are carried as audit
  citations marked `NOT-REPRODUCIBLE`. D1 re-scopes to the part that survives.
- **A fifth distinct training seed** was never run; `snap_s44` holds no checkpoints and its log shows
  the run died just after the dataloaders initialised. σ from four distinct seeds carries a 95% CI
  spanning 6.6×.
- **In-loop acceptance with fresh sampling** was never measured; B3 uses pre-existing generations.
- **The generator-side conditioning ablation** has never been run. It is the one experiment that
  would turn this diagnosis into a prescription.

# Run-book — reproducing every number in the Stage C evidence package

> **New here?** Start with [EVIDENCE_README.md](EVIDENCE_README.md) — orientation, script map, and current status.

Companion to [EVIDENCE_APPROACH.md](EVIDENCE_APPROACH.md), which explains *why* these measurements
matter. This file is the *how*: twelve steps, executable top to bottom, each writing one block to
[results/STAGE_C_EVIDENCE_LOG.txt](results/STAGE_C_EVIDENCE_LOG.txt).

**None of these experiments trains a model.** The most expensive item (C3, the noise floor)
re-evaluates prediction files from six *already completed* training runs. Every "trains anything?"
field below reads **NO**.

---

## 0. Environment

| component | version | note |
|---|---|---|
| Python | 3.12.3 | `.python-version` pins 3.12 |
| torch | 2.11.0+cu128 | CUDA 12.8 — required for Blackwell (sm_120) |
| timm | 1.0.28 | supplies DINOv2 weights via the HF hub |
| transformers | 5.15.1 | present but not load-bearing |
| scikit-learn | 1.9.0 | logistic-regression probe, k-means |
| numpy | 2.5.2 | (the root `.venv` has 2.5.1; use `LAKE-RED/.venv`) |
| opencv-python-headless | 5.0.0.93 | `cv2.imread(..., IMREAD_GRAYSCALE)` in the eval path |
| scikit-image | 0.26.0 | `slic` — used by LAKE-RED's `LMP()` |
| GPUs | 2 × NVIDIA RTX PRO 6000 Blackwell Workstation Edition | |

### Which virtualenv — this matters

There are two, and they are **not** interchangeable:

- **`LAKE-RED/.venv` — use this one.** It has `timm` and `transformers`; the audits ran here.
- `.venv` (repo root) has **no `timm`**, so every DINOv2 experiment fails in it.

Every command below is written with the explicit interpreter path, so there is nothing to activate:

```bash
LAKE-RED/.venv/bin/python evidence/<script>.py
```

Full install instructions, exact pins, dataset layout and troubleshooting are in
**[EVIDENCE_SETUP.md](EVIDENCE_SETUP.md)**. To check a machine is ready:

```bash
LAKE-RED/.venv/bin/python evidence/setup_check.py     # 34 checks, exit 0 = ready
```

### DINOv2 variant — stated precisely, because it is load-bearing

The embedder choice **reversed one of our conclusions** (revision R-a), so it is pinned exactly:

| role | model | params | embed dim |
|---|---|---|---|
| **primary** | `timm/vit_large_patch14_dinov2.lvd142m` | 304 M | 1024 |
| size-robustness check | `timm/vit_base_patch14_dinov2.lvd142m` | 87 M | 768 |
| superseded (kept for the revision trail) | InceptionV3, 2048-d pool | — | 2048 |

- **Pooling:** CLS token, L2-normalised. (Patch-mean gave the same ordering; not reported.)
- **Resolutions:** **518 (native)** for headline numbers, **224** for sweeps, set via `img_size=`.
  timm hard-asserts the pretrained 518 input at `timm/layers/patch_embed.py:121`.
- **Why ViT-L:** it is the strongest DINOv2 short of ViT-g, and a *stronger* embedder is the
  adversarial choice — if targeting fails under the best available features, that is a property of
  the generator, not of the metric.
- Weights are already cached in `~/.cache/huggingface/hub/`; no download is needed.

### Determinism, honestly stated

- Every script takes `--seed` (default **0**) and stamps it in its log block. All stochastic steps —
  k-means init, the 70/30 probe split, the held-out generation split, random-1000 draws, permutation
  shuffles — draw from an explicitly seeded `numpy.random.default_rng(seed)`.
- **A1, A2, A3, B1, B2, B3, C1, C2, D1, D2 are bit-reproducible.** They are read-only measurements
  over fixed inputs.
- **C3 is not, and cannot be.** It summarises six training runs, so it is reported as a **spread** —
  min, max, σ under three groupings, and a 95% CI on σ itself — never as a single figure.
- The *reason* run-to-run spread exists even at a fixed seed: `set_random_seed`
  (`Src/utils/tool.py:24-28`) sets neither `torch.backends.cudnn.deterministic = True` nor
  `torch.use_deterministic_algorithms(True)`. Measured consequence: **80%** of the Sα spread is
  training nondeterminism rather than seed choice (σ_fixed 0.00229 vs σ_across-seed 0.00286).

### Verifying the inputs

Large binary inputs (prediction files, checkpoints, feature caches) cannot live in git — the repo
already ignores `/Dataset*`, `/Result*`, `*.pth`, and these total **3.42 GiB**. They live in
`evidence/artifacts/` (gitignored) and are verified by hash instead.

Three manifests are committed under `evidence/manifests/`. From the repo root:

```bash
sha256sum -c evidence/manifests/MANIFEST.sha256      # 81 singleton files (caches, ckpts, logs)
sha256sum -c evidence/manifests/SOURCES.sha256       # the 3 immutable source documents
for r in s42 s43 s45 s46 repB repC; do               # 2026 prediction files per run
  sha256sum -c evidence/artifacts/pred_$r.sha256
done
```

The 12,156 prediction files would make a committed manifest a megabyte of hashes, so
`evidence/manifests/PRED_DIGESTS.txt` commits **one aggregate digest per directory** instead — the
sha256 of that directory's sorted per-file listing, plus its file count. The full per-file listings
live beside the data in `evidence/artifacts/pred_<run>.sha256` (gitignored) and use repo-relative
paths, so `sha256sum -c` verifies them from the repo root. To confirm a listing has not itself been
edited, hash it and compare against `PRED_DIGESTS.txt`:

```bash
sha256sum < evidence/artifacts/pred_s42.sha256
```

`SOURCES.sha256` covers only the **three immutable source documents** — the two audits and the
vendored `PRIOR_REVIEW.md`. This run-book and `EVIDENCE_APPROACH.md` are deliberately *not* hashed:
they are living deliverables, corrected in place whenever a measured value disagrees with an expected
one, so hashing them would guarantee a stale manifest. Their integrity comes from git history
instead, which is the right tool for a mutable text file.

This is a real limitation of the package and is stated rather than glossed: the advisor verifies the
large inputs by checksum, not by checkout.

### Log block format

```
================================================================================
2026-08-27T14:31:07+05:30 | commit 6072d70 (clean) | EXP A1
CMD  LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py
ENV  py3.12.3 torch2.11.0+cu128 cu12.8 timm1.0.28 | 2x RTX PRO 6000 Blackwell | seed 0
METRICS
  n_super_pix                = 16          (config_LAKERED.yaml:72)
  conditioning_width         = 48
  vec_fg_shape_live          = (1, 16, 3)
THRESHOLD  conditioning_width == 48 -> PASS
EXPECTED (source)  conditioning width = 48 -> MATCH
ARTIFACTS  evidence/out/a1_conditioning.csv
REVISION   none
TRAINS     NO
NOTES      ...
================================================================================
```

`EXPECTED (source)` prints for every metric a source document pins, so match/mismatch is visible
without cross-referencing. `REVISION` names the superseded number where one exists. The log is
**append-only** — `evidence/common.py` opens it with `"a"` and never `"w"`, so a re-run adds a second
block rather than replacing the first.

Because it is append-only, every script takes **`--no-log`**: it prints the block but does not write
it. That is for iterating on a script, so that fixing a defect in the *measurement code* does not
leave a trail of near-identical blocks. The log is for accepted runs and genuine re-runs. Two
experiments carry more than one block for exactly that reason, before the flag existed: **E0** has
three (original, hash-path fix, manifest-scope fix) and **A2** has five (four while a polarity bug
was found and fixed). Each block's `NOTES` says which it is, and none were removed.

### Package layout

```
EVIDENCE_APPROACH.md              the "why"
EVIDENCE_SCRIPTS.md               this run-book
results/STAGE_C_EVIDENCE_LOG.txt  append-only results log
evidence/
  common.py                       shared: log_block, git/env stamp, seed, input resolution
  e0_rescue.py  a1_*.py  ...  d2_*.py
  manifests/                      COMMITTED hashes (MANIFEST, PRED_DIGESTS, SOURCES)
  sources/PRIOR_REVIEW.md         vendored third source document
  out/                            COMMITTED CSVs, figures, e0_environment.json
  artifacts/                      GITIGNORED rescued binaries (3.42 GiB)
```

`evidence/common.py` is imported by every script. It resolves each input from
`evidence/artifacts/` first and the volatile scratchpad second, and **fails loudly with the rescue
instruction** if neither has it — so no experiment can silently read a stale or missing input.

### Source documents

| file | role |
|---|---|
| [STAGE_C_MEASUREMENTS.md](STAGE_C_MEASUREMENTS.md) | the DINOv2 re-measurement round |
| [STAGE_C_RED_TEAM_AUDIT.md](STAGE_C_RED_TEAM_AUDIT.md) | the adversarial audit of the above |
| `evidence/sources/PRIOR_REVIEW.md` | the earlier review (cited at `STAGE_C_MEASUREMENTS.md:3`); sole source for C2's retraction table and part of D2 |

---

## 1. Execution order

Run top to bottom. **E0 is a hard gate** — it rescues irreplaceable inputs off a volatile temp path,
and nothing else should run until it has.

| # | experiment | GPU? | runtime | trains? |
|---|---|---|---|---|
| E0 | artifact rescue, hash manifest, environment capture | no | **7 s measured** (3.42 GiB, same filesystem) | NO |
| A1 | conditioning-width measurement | optional | < 2 min | NO |
| A2 | object-vs-background pixel share | no | ~2 min | NO |
| A3 | appearance signature + controls | yes (if re-embedding) | 5–25 min | NO |
| B1 | ES-vs-true-error correlation | yes | ~15 min | NO |
| B2 | coverage-term falsification | no | < 2 min | NO |
| B3 | targeting acceptance, both embedders | yes (if re-embedding) | 5–20 min | NO |
| C1 | targeted-vs-random data distance | no | ~3 min | NO |
| C2 | budget-B arithmetic + per-arm sampling | no | < 1 s | NO |
| C3 | noise floor + effect-size translation | no | 10–20 min | NO |
| D1 | foreground-exhaustion check | no | ~3 min | NO |
| D2 | leakage sweep | no | 5–10 min | NO |

---

## 2. The experiments

### E0 — Artifact rescue, hash manifest, environment capture

- **Objective.** Move every irreplaceable audit artifact off the volatile `/tmp` session path into
  `evidence/artifacts/`, hash it, and stamp the environment — before any measurement runs.
- **Script.** `evidence/e0_rescue.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/e0_rescue.py
  ```
- **Inputs read.** `$SCRATCH/noisefloor/pred_{s42,s43,s45,s46,repB,repC}/` (835 MB, 2026 PNGs each);
  `$SCRATCH/noisefloor/snap_*/{Stu_40.pth,Tea_epoch_best.pth}` (2.2 GB);
  `$SCRATCH/{dino*,cut,gen,f,n}.npy` + `*_names.json` + `locked2_scores.json` (557 MB);
  `$SCRATCH/noisefloor/{audit6.json,metrics.json,audit6.py,MyTrain_seed.py,*.log}`;
  `~/.claude/plans/hazy-launching-eclipse.md`.
  Where `$SCRATCH = /tmp/claude-1000/-home-ai-server-Public-lab-Diffusion-Inpaint-S2R-COD/56f76fa7-1340-4f64-8958-29c72d526e77/scratchpad`.
- **Method.** Copy — never move, the originals stay in place — then `sha256sum` everything into
  `evidence/manifests/` (three manifests, see above) and write
  `evidence/out/e0_environment.json`. Vendors the
  three source documents into `evidence/sources/` (`PRIOR_REVIEW.md` is outside the repo and outside
  git, so without this step C2 has no citable source). Deliberately skips the other 15 checkpoints
  per run — 17 GB, not load-bearing.
- **Expected.** 6 × 2026 = **12,156** prediction PNGs; 12/12 checkpoints; the rescued `audit6.json`
  containing the six Sα values 0.6961 / 0.6971 / 0.7005 / 0.7016 / 0.7022 / 0.7058.
- **Measured — this step has run (2026-08-27, commit `5a98247`).** 12,156 prediction PNGs **MATCH**;
  12/12 checkpoints; 39 feature-cache/score files; 30 provenance files; **3.42 GiB** rescued; 81
  singleton manifest lines; all six Sα values **MATCH** to 4 dp. All four thresholds PASS.
  Verification: 81/81 singletons OK, 2026/2026 per prediction directory (× 6), 5/5 sources OK.
- **Output / logged.** `evidence/manifests/{MANIFEST.sha256,PRED_DIGESTS.txt,SOURCES.sha256}`,
  `evidence/artifacts/pred_<run>.sha256` (× 6, gitignored), `evidence/out/e0_environment.json`,
  `evidence/sources/PRIOR_REVIEW.md`, log block `EXP E0`.
- **Trains?** NO. **Assumptions.** The `/tmp` path is still readable at execution time.
- **Notes.** Records two live breakages in the surviving code: `audit6.py` hardcodes the dead
  `$SCRATCH` path *and* `Dataset/Test/GT`, which is now `Dataset/Test/COD10K/GT`.

---

### Group A — the generator bottleneck

#### A1 — Conditioning-width measurement

- **Objective.** Show LAKE-RED's entire steerable foreground→background channel is 16 superpixels ×
  3 mean colour channels = 48 scalars.
- **Script.** `evidence/a1_conditioning_width.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py
  ```
- **Inputs read.** `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py` (`LMP()` 1548–1564, `vec_fg` 1574,
  `crossAttn` 1579, `n_super_pix` 1533); `LAKE-RED/ldm/models/ldm/inpainting_big/config_LAKERED.yaml:72`;
  `LAKE-RED/ckpt/LAKERED.ckpt`; one image+mask pair from `Dataset/LAKERED/input/HKU-IS/validation`.
- **Method.** Two paths, both logged. **(a) Static:** parse `n_super_pix` from the YAML, echo the
  source lines that consume it, and assert `LMP()` returns `b × n × 3` — the loop appends one
  3-channel mean per superpixel. **(b) Live:** forward one real sample and log the actual `vec_fg`
  tensor shape; if the checkpoint will not instantiate standalone, call `LMP()` directly on the real
  image/mask instead. The log records **which path ran**.
- **Expected.** `n_super_pix = 16`; `vec_fg.shape == (1, 16, 3)`; width = **48**.
- **Measured — has run (commit `a1` below).** `n_super_pix` **16** MATCH; per-superpixel width **3**
  read off `mlp_in.fc1.weight (6, 3)`; `conditioning_width` **48** MATCH; live `vec_fg` **(1, 16, 3)**,
  48 elements; `new_cond` `(1, 4, 128, 128)`; 16/16 BKRA weights loaded, 0 missing. All six
  thresholds PASS. **NEW:** effective width averages **45.75** (range 36–48, 20 samples) because
  `LMP` zero-fills empty superpixels — so 48 is an upper bound. Codebook is `(3, 8192)`, addressed by
  those ≤48 scalars.
- **Output / logged.** `evidence/out/a1_conditioning.csv`, log block `EXP A1`.
- **Trains?** NO. GPU optional (path b only).
- **Assumptions / limitations.** 48 is the width of the **conditioning channel**, not the model's
  capacity — the U-Net is unconstrained. The claim is that the foreground reaches the
  background-generation path only through those 48 numbers, which is precisely the pathway Stage C
  would need to exploit. The document must say this or it overclaims. The retrieval codebook holds
  8192 entries; they are addressed by the ≤48 scalars, so the bottleneck is the query side.
  Two code observations recorded in the log: `LMP` uses no attribute of `self`, and its fourth
  argument `s` is dead (sigma is hardcoded to 5 at `ddpm.py:1553`). Mask convention verified rather
  than assumed: `mask==1` is the region the generator invents, so `1-mask` is the kept foreground,
  which is what `LMP` segments.
- **Revision.** None — this number has never moved.

#### A2 — Object-vs-background pixel share

- **Objective.** Quantify how much of each generated image is invented background rather than
  preserved foreground.
- **Script.** `evidence/a2_fg_pixel_share.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/a2_fg_pixel_share.py
  ```
- **Inputs read.** `Dataset/Source/HKU-IS/GT` (4447 masks); cross-checked against
  `Dataset/LAKERED/output/HKU-IS/masks` (4447).
- **Method.** Per mask, foreground fraction = mean of the mask binarised at **threshold 127** (stated
  explicitly, since it is a choice). Report mean, median, sd, deciles, min, max over all 4447.
- **Expected.** mean ≈ **0.182** — i.e. **~81.8%** of every output is background the generator
  invents.
- **Measured — has run.** Foreground mean **0.1913** over all 4447 inpainting masks ⇒ **80.87%**
  invented background; median 0.1778, sd 0.1090, range 0.0024–0.6378, deciles 0.059→0.341. Delta to
  the source figure is **−0.93 points**, inside the ±1.0-point tolerance registered before the run,
  so logged **MATCH**. All six thresholds PASS. Cross-source: LAKE-RED input masks are the exact
  inverse of `HKU-IS_raw/gt` (4447/4447 to 1e-9) and identical to the output masks; but
  `Source/HKU-IS/GT` — the set training actually reads — differs (mean |Δ| 5.75e-3, max 2.48e-2,
  0/4447 identical), giving 81.44%. The two GT sets are not the same, which D1 revisits.
- **Output / logged.** `evidence/out/a2_fg_fraction.csv` (per image),
  `evidence/out/a2_fg_hist.png`, log block `EXP A2`.
- **Trains?** NO. CPU only.
- **Assumptions / limitations.** Binarisation threshold as above — every mask on disk is already
  binary, so the threshold does no work. **Polarity is detected, not assumed:** LAKE-RED input masks
  store background=white (they *are* the inpainting mask) while the three GT sets store object=white,
  and reading it backwards would invert the headline from 18% to 82%. Polarity is decided once per
  source by majority corner vote, because the per-image corner rule misfires on the 11 images whose
  object covers the corners; the minority count is logged as a diagnostic.
- **Revision.** Within-experiment: the first run used per-image polarity and gave 0.1923, which fell
  outside tolerance; per-source polarity gives **0.1913**. Also refines the source's 81.8% to the
  measured **80.9%**.

#### A3 — Generated-vs-real appearance signature, with its controls

- **Objective.** Show that the naive "real vs generated separates at AUC 0.999" finding is a truism,
  by placing it beside controls that score nearly as high on trivially different images.
- **Script.** `evidence/a3_appearance_signature.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/a3_appearance_signature.py            # uses rescued caches
  LAKE-RED/.venv/bin/python evidence/a3_appearance_signature.py --recompute # re-embeds from images
  ```
- **Inputs read.** `evidence/artifacts/dinoL_{tgt,gen}_cls.npy` + `dinoL_names.json`, or with
  `--recompute`, `Dataset/Target/Image` and `Dataset/LAKERED/output/HKU-IS/images`;
  `Dataset/Source/HKU-IS_raw/imgs` (the raw pre-LAKE-RED baseline). JPEG-75 and darkened-20 variants
  are generated on the fly.
- **Method.** Three panels. **(1) Pixel statistic:** mean brightness and per-channel shift, generated
  background vs real, plus the foreground→background colour correlation. **(2) Linear probe:**
  logistic regression on L2-normalised CLS features, 70/30 split at seed 0 — accuracy, AUC and
  Cohen's d on the probe axis, for real-vs-LAKE-RED **and all four controls in one table**.
  **(3) Generative precision/recall** (Kynkäänniemi et al. 2019, k=5 NN manifold) for raw HKU-IS and
  LAKE-RED output against a **random-split** real-vs-real ceiling. The script also deliberately
  recomputes the **sorted-filename** split, so the original bug is visible rather than merely asserted.
- **Expected.** Colour correlation flips **−0.36 (real) → +0.45 (generated)**, R² ≈ 0.2.

  | probe comparison | accuracy | AUC |
  |---|---|---|
  | real vs LAKE-RED | 0.9827 | **0.9989** |
  | real vs real, **random** split (true null) | 0.5240 | **0.5289** |
  | real vs **raw HKU-IS** (two ordinary datasets) | 0.9367 | **0.9831** |
  | real vs real, **JPEG-75** | 0.8905 | **0.9380** |
  | real vs real, **darkened 20 levels** | 0.3640 | **0.3204** |

  | precision / recall | precision | recall | % of ceiling |
  |---|---|---|---|
  | raw HKU-IS (pre-LAKE-RED) | 0.649 | **0.745** | 79.3% |
  | LAKE-RED output | 0.691 | **0.466** | **49.6%** |
  | real-vs-real ceiling (random split) | 0.946 | 0.939 | — |

  Also Cohen's d on the probe axis: 4.70 (L/224), 4.62 (B/224), 4.35 (L/518).
- **Output / logged.** `evidence/out/a3_probe_table.csv`, `evidence/out/a3_precision_recall.csv`,
  `evidence/out/a3_pixel_stats.csv`, log block `EXP A3`.
- **Trains?** NO — a logistic-regression probe on cached features is not model training. GPU only
  with `--recompute`.
- **Assumptions / limitations.** JPEG quality 75 and darkening of 20 levels are the specific control
  choices from the audit, not a sweep. k=5 for the manifold estimate. The feature caches were
  produced by scripts that were never saved, so `--recompute` exists to re-derive them from images
  and the log records which path ran.
- **Revisions surfaced — four.** **R-c** (sorted-filename split bug → random split; ceiling
  0.893/0.871 → **0.946/0.939**), **R-d** (54% → **49.6%**), **R-e** (darkening mechanism
  **retracted**, AUC 0.32), **R-f** (AUC framing demoted to near-vacuous). Both the buggy and the
  corrected ceiling are computed and logged side by side.

---

### Group B — the deficiency signal

#### B1 — ES-vs-true-error correlation

- **Objective.** Test whether teacher–student ES-disagreement predicts where the model is actually
  wrong, separately for MAE, S-measure and IoU.
- **Script.** `evidence/b1_es_error_correlation.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/b1_es_error_correlation.py --k 15,20,50,100
  ```
- **Inputs read.** `Snapshot/SINet/S2C/{Stu_40.pth,Tea_epoch_best.pth}`;
  `Dataset/Test/COD10K/{Imgs,GT}` (2026); `Dataset/Val/CAMO/{Imgs,GT}` (250);
  `evidence/artifacts/dinoL518_{tst,val,tgt}_cls.npy`; `Eval/metrics.py`;
  `evidence/artifacts/locked2_scores.json` and `snap_s{42,43,45,46}/` for the cross-run replication.
- **Method.** Compute ES exactly as the training loop does — `ESLoss(a=0.9, b=0.3,
  use_weighted_bce=False)` from `Src/utils/tool.py:45-77`, applied to `stu.sigmoid()` and
  `tea.sigmoid()` at 352×352, per `CLS.py:105`/`CLS.py:138`. Derive true per-image error from the
  teacher prediction upsampled and min-max normalised per `MyTest.py:72-75`, scored with the repo's
  own `Eval/metrics.py` at the `Eval/MyEval.py:33-39` convention. Assign labelled images to DINOv2
  k-means clusters (keeping clusters with ≥8 images) and take Spearman ρ of per-cluster mean ES
  against per-cluster mean MAE, (1−Sα) and (1−IoU) — **reporting val and test separately**, with a
  5000-shuffle permutation p on val where n ≈ 9 makes the asymptotic p unreliable.
- **Expected.** Pipeline self-check: per-image mean MAE on COD10K-test = **0.0747** against the
  repo's recorded **0.0745** (`Eval/Eval/eval_txt/SINet/S2C/10Aug_eval.txt`).

  | k | split | clusters | ρ(ES, MAE) | ρ(ES, 1−IoU) | perm p |
  |---|---|---|---|---|---|
  | 20 | test | 20 | **+0.857** | +0.513 | 0.0000 |
  | 50 | test | 49 | **+0.817** | +0.239 | — |
  | 100 | test | 86 | **+0.880** | +0.264 | — |
  | 15 | val | 9 | **+0.967** | — | **0.0002** |
  | 20 | val | 9 | +0.800 | +0.550 | 0.0060 |
  | 50 | val | 6 | +0.943 | +0.771 | 0.0108 |

  Against Sα: ρ(ES, 1−Sα) = **+0.645** (k=20), **+0.398** (k=50), +0.334 per-image.
  Cross-run replication over 4 independent runs: **+0.903 ± 0.041** (k=20); pairwise ranking
  agreement ρ = **0.78…0.94**; per-image **+0.770 ± 0.022**.
- **Output / logged.** `evidence/out/b1_cluster_correlations.csv`,
  `evidence/out/b1_per_image_scores.csv`, `evidence/out/b1_cross_run.csv`, log block `EXP B1`.
- **Trains?** NO — inference only, from committed checkpoints.
- **Assumptions / limitations.** The strong numbers come from **COD10K-test**; deriving λ_cov = 0
  from them is **mild test-peeking, and the log block says so**. Val has few populated clusters
  (6–9), which is why k is swept down to 15. The ES *scale* varies 40% across runs
  (0.0439–0.0612), so only the **ranking** is portable — a fixed ES threshold would not transfer.
- **Revision surfaced.** **R-h** — ρ = 0.82 licenses "ES ranks clusters by pixel-calibration error",
  **not** "ES predicts the error that matters", since Sα correlation is only +0.40…+0.65. Both
  numbers are logged in the same block.

#### B2 — Coverage-term falsification

- **Objective.** Show the coverage term `−λ_cov·log(n_s/n_t)` has no relationship to true error and
  actively destroys the ES signal — the measured justification for λ_cov = 0.
- **Script.** `evidence/b2_coverage_falsification.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/b2_coverage_falsification.py
  ```
- **Inputs read.** `evidence/out/b1_cluster_correlations.csv` (so **B1 must run first**); cluster
  occupancy `n_s`, `n_t` from `evidence/artifacts/dinoL518_{gen,tgt}_cls.npy`; the acceptance table
  from B3 if present, for the label-free corroboration.
- **Method.** Spearman ρ of the coverage term against true per-cluster MAE at k ∈ {20, 50, 100} on
  **both** val and test. Then the combined `d(c) = ES − λ_cov·cov` at λ_cov ∈ {0, 0.01, 0.05},
  reporting ρ and top-10 overlap with the true worst-10. Finally the **label-free** corroboration
  ρ(acceptance, n_s(c)), which needs no ground truth at all.
- **Expected.**

  | k | ρ(cov, MAE) **val** | ρ(cov, MAE) test | ρ(ES) val | ρ(ES + 0.05·cov) val |
  |---|---|---|---|---|
  | 20 | **−0.717** | +0.006 | +0.800 | **−0.733** |
  | 50 | −0.200 | +0.006 | +0.943 | −0.200 |
  | 100 | −0.600 | +0.070 | +1.000 | −0.300 |

  On test at k=50: ES only **+0.817** (5/10 top-10 overlap) → λ_cov=0.01 **+0.431** → λ_cov=0.05
  **+0.138** (2/10); coverage term alone **+0.006**.
  Label-free: ρ(acceptance, n_s) = **+0.762 / +0.734 / +0.873** (L/518, k=20/50/100) and
  **+0.893 / +0.918 / +0.878** (L/224).
- **Output / logged.** `evidence/out/b2_coverage_correlations.csv`, log block `EXP B2`.
- **Trains?** NO.
- **Assumptions / limitations.** Inherits B1's clustering, hence its k choice and seed.
- **Revision surfaced.** **R-i** — the val/test **sign discrepancy is reported, not smoothed**. The
  original "ρ = +0.006, i.e. noise" understated it: on val the term is worse than noise.

#### B3 — Targeting acceptance under both embedders, vs chance, in-sample and held-out

- **Objective.** Reproduce the headline reversal — acceptance in the deficient clusters under
  InceptionV3 (≈0%) vs DINOv2 (≈20–27%) — with chance baselines and the in-sample→held-out correction.
- **Script.** `evidence/b3_targeting_acceptance.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/b3_targeting_acceptance.py --k 20,50,100
  ```
- **Inputs read.** `evidence/artifacts/{cut,gen}.npy` (InceptionV3-2048, 2000 images);
  `evidence/artifacts/dino{B,L,L518}_{cut,gen,tgt}_cls.npy` + `*_names.json`;
  `Dataset/LAKERED/output/HKU-IS/images`.
- **Method.** k-means on the target images at seed 0, with the **7 test-identical target images
  excluded in memory** (4033 kept of 4040 — no files deleted). For each cluster take the N=40 cutouts
  nearest the centroid, look up where their already-generated LAKE-RED outputs land, and accept if the
  landing cluster is the intended one; report over the 12 most coverage-deficient clusters. Each cell
  also gets **(a)** a chance rate `p_land(c) = n_s(c)/Σn_s` with a one-sided pooled binomial test and
  **(b)** a **held-out** variant — rank clusters on a random half A, measure acceptance on half B.
- **Expected.**

  | embedder / k | in-sample | held-out | chance | lift | binomial p |
  |---|---|---|---|---|---|
  | InceptionV3-2048, k=50 | **0.00%** | — | — | — | — |
  | DINOv2 B/224, k=20 | 14.58% | — | — | — | — |
  | DINOv2 L/224, k=20 | 6.46% | 5.00% | 0.16% | 39.2× | 1.6e-38 |
  | DINOv2 L/224, k=50 | 3.12% | 2.92% | 0.05% | 59.6× | 5.1e-22 |
  | **DINOv2 L/518, k=20** | **26.67%** | **20.62%** | 1.63% | 16.4× | 1.3e-112 |
  | DINOv2 L/518, k=50 | 11.46% | 10.83% | 0.32% | 35.6× | 2.2e-65 |
  | DINOv2 L/518, k=100 | 3.96% | — | — | — | — |

  Inverted-competence profile (deficient-12 vs saturated-4): **1.5×** at k=20, 7.2× at k=50, 18× at
  k=100 under L/518, against ∞× under InceptionV3.
- **Output / logged.** `evidence/out/b3_acceptance.csv`, log block `EXP B3`.
- **Trains?** NO.
- **Assumptions / limitations.** Acceptance is measured on **pre-existing** generations, never inside
  a live loop with fresh sampling — in-loop acceptance is **UNVERIFIED** and the log block repeats
  that. The InceptionV3 arm depends on rescued 2000-image caches because the original embedder script
  was never saved; if they are lost the script re-embeds with `torchvision` InceptionV3 pool-2048 and
  the log marks it a **re-implementation**, not the original.
- **Revisions surfaced — two.** **R-a** (embedder: 0% → 26.67%) and **R-b** (in-sample → held-out:
  26.67% → **20.62%**). Both embedders and both split protocols appear in one table — that is the point.

---

### Group C — the effect-size wall

#### C1 — Targeted-vs-random data distance

- **Objective.** Measure how different arm C's appended 1000 images actually are from arm B's.
- **Script.** `evidence/c1_targeted_vs_random.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/c1_targeted_vs_random.py --draws 20
  ```
- **Inputs read.** `evidence/artifacts/dinoL_cut_cls.npy` (4447), `dinoL_tgt_cls.npy`;
  `evidence/out/b1_cluster_correlations.csv` for per-cluster ES.
- **Method.** Allocate B=1000 by temperature-softmax over per-cluster ES and take the nearest cutouts
  per funded cluster; compare against a uniform-random 1000 of 4447. Report ‖mean_C − mean_rand‖ and
  Cohen's d over k ∈ {20, 50} × T ∈ {0.005, 0.01, 0.02, 0.05}, logging clusters funded and max
  allocation per setting. Averaged over **20 random draws** so d is not a single-draw artifact — an
  addition beyond the audit, which used one draw, and flagged as such in the log.
- **Expected.**

  | k | T | clusters funded | max alloc | ‖Δmean‖ | Cohen's d |
  |---|---|---|---|---|---|
  | 20 | 0.005 | 14 | 456 | 0.0854 | **0.09** |
  | 20 | 0.05 | 20 | 76 | 0.0946 | **0.10** |
  | 50 | 0.005 | **1** | 999 | 0.0980 | **0.10** |
  | 50 | 0.01 | 22 | 927 | 0.0992 | **0.11** |
  | 50 | 0.05 | 49 | 76 | 0.0838 | **0.09** |

  Headline: **d ≈ 0.10**, range 0.084–0.099 across a 10× temperature sweep, while funded clusters
  swing from 1 to 49.
- **Output / logged.** `evidence/out/c1_effect_size_sweep.csv`, log block `EXP C1`.
- **Trains?** NO.
- **Assumptions / limitations.** d is a **mean** shift. Higher-moment differences (variance,
  coverage) are unmeasured and are the one route by which the true effect could exceed prediction —
  **UNVERIFIED**, and the log block carries it.
- **Revision.** None — this number never moved across any re-measurement, which is itself worth stating.

#### C2 — Budget-B arithmetic and the per-arm sampling table

- **Objective.** Two things: show that no choice of budget B rescues the effect (retracting the
  earlier "raise B" advice), and show the loop adds zero gradient steps for added data.
- **Script.** `evidence/c2_budget_arithmetic.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/c2_budget_arithmetic.py
  ```
- **Inputs read.** No data files. Constants read from `MyTrain.py:306-307` (`total_step`),
  `MyTrain.py:51` (`zip`), `Src/utils/Dataloader.py:206` (`shuffle=True`), and
  `evidence/sources/PRIOR_REVIEW.md` §0.7-D1 for the pool sizes.
- **Method.** **(1)** Reproduce `PRIOR_REVIEW.md` §0.7-D1: expected arm overlap `B²/4447` ⇒ differing
  fraction `(1 − B/4447)` ⇒ pool shift `(B/|Ds|) × (1 − B/4447)`, then predicted ΔSα via C3's
  response rate and its ratio to 2σ. Emit as a computed CSV over the whole range B = 0…4447 — not
  just the four tabulated rows — locating the maximum both analytically and numerically. **(2)** Emit
  the per-arm sampling table at **both B=1000 and B=2000**, since the budget was revised between
  documents.
- **Expected (part 1).**

  | B | block % of pool | % of block differing | pool shift | vs B=1000 | predicted ΔSα | in σ |
  |---|---|---|---|---|---|---|
  | 1000 | 12.8% | 77.5% | 0.0128 SD | 1.00× | 0.000111 | 0.031 σ |
  | **2000** | **22.7%** | **55.0%** | **0.0161 SD** | **1.26×** | **0.000140** | **0.039 σ** |
  | 3000 | 30.5% | 32.5% | 0.0128 SD | 1.00× | 0.000111 | 0.031 σ |
  | 4447 | 39.5% | **0%** | **0** | **0.00×** | 0 | 0 |

  Concave, zero at both ends, peaking at B=2000 for **1.26×** — so the ceiling over *every* budget is
  0.039σ, needing **51×** the linear response rate (vs 64× at B=1000).

- **Expected (part 2 — the gradient-step budget, load-bearing conclusion (ii)).**

  | arm | \|Ds\| | len(src) | total_step | imgs/epoch | P(image seen) | added-block presentations/epoch |
  |---|---|---|---|---|---|---|
  | A (none) | 6824 | 427 | **253** | 4048 | **0.593** | 0 |
  | B (+1000 random) | 7824 | 489 | **253** | 4048 | **0.517** | 517.4 |
  | C (+1000 targeted) | 7824 | 489 | **253** | 4048 | **0.517** | 517.4 |

  At B=2000 (|Ds| = 8824), per-run exposure is **23.1× for arm A vs 17.9× for B/C**. `total_step` is
  pinned at `ceil(4040/16) = 253` by the **target** loader in every arm, so all arms run
  253 × 39 = **9,867 identical gradient steps**.
- **Output / logged.** `evidence/out/c2_budget_curve.csv`, `evidence/out/c2_arm_sampling.csv`,
  log block `EXP C2`.
- **Trains?** NO. CPU only, sub-second.
- **Assumptions / limitations.** The |Ds| values 6824 / 7824 / 8824 derive from the **now-deleted**
  iteration-2 pool directories; they are cited to the audit and `PRIOR_REVIEW.md`, **not re-measured**
  (see D1), and the log block carries the label **UNVERIFIED-NOT-REPRODUCIBLE**. Part 1's ΔSα column
  inherits C3's linearity assumption. `PRIOR_REVIEW.md` is a planning document, not a peer-reviewed
  artifact — but it is a real recorded source, and E0 vendors it so the retraction can be read in its
  original wording.
- **Revisions surfaced — three.** **R-j** (arm A is not a clean control: 0.593 vs 0.517 per epoch,
  23.1× vs 17.9× per run — it confounds "1000 more images" with "13% less exposure", so only B-vs-C
  is clean), **R-k** (the "raise B" retraction), **R-l** (B raised 1000 → 2000 as the measured
  optimum, worth 1.26×).

#### C3 — Noise floor, and the effect-size translation

- **Objective.** Recompute σ from existing prediction files — no retraining — and translate d ≈ 0.10
  into a predicted ΔSα against the 2σ detection bar.
- **Script.** `evidence/c3_noise_floor.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/c3_noise_floor.py
  ```
- **Inputs read.** `evidence/artifacts/pred_{s42,s43,s45,s46,repB,repC}/` (2026 PNGs each);
  `Dataset/Test/COD10K/GT`; `Eval/metrics.py`; `evidence/out/c1_effect_size_sweep.csv`.
- **Method.** Re-derive Sα, Fβw, Eφ and MAE for all six runs with the repo's own `Eval/metrics.py` at
  the `Eval/MyEval.py:33-39` convention — a **corrected-path port** of the surviving `audit6.py`,
  whose hardcoded `Dataset/Test/GT` no longer resolves. Report σ under **all three groupings** with
  95% CIs, plus the paired σ_d = √2 · σ_fixed. Then the translation with every input logged: response
  rate from the MT→Ours anchor (+0.0142 Sα for a 0.348 × 4.70 = 1.637 SD shift ⇒ **0.00867 Sα/SD**),
  arm B→C shift = (1000/7824) × 0.10 = **0.01278 SD**, the resulting ΔSα, and its ratio to 2σ under
  each σ grouping and at both budgets. Also the inverse check and the secondary B-vs-A prediction.
- **Expected.** Per-run Sα: 0.6961, 0.6971, 0.7005, 0.7016, 0.7022, 0.7058.

  | grouping | n | σ(Sα) | 95% CI on σ(Sα) | σ(Fβw) | σ(MAE) |
  |---|---|---|---|---|---|
  | distinct seeds (42,43,45,46) | 4 | 0.00286 | [0.00162, 0.01065] | 0.00757 | 0.00477 |
  | same seed 42 (orig, repB, repC) | 3 | 0.00229 | [0.00119, 0.01437] | 0.00980 | 0.00281 |
  | **ALL runs = arm-run variance** | **6** | **0.00356** | **[0.00222, 0.00872]** | 0.00844 | 0.00388 |

  Paired σ_d = √2 × 0.00229 = **0.00324**. Predicted **ΔSα = 0.000111 = 0.031σ** against 2σ =
  0.00712 ⇒ **64×** short (51× at B=2000). Inverse check: the added block would need **d = 7.09**
  while the entire real-vs-LAKE-RED gap is d = **4.70**. Secondary: arm B vs arm A moves the pool
  34.8% → 30.4% real, a 0.209 SD shift *away* from target ⇒ **ΔSα ≈ −0.0018 (−0.51σ)**, i.e. adding
  synthetic images is predicted to slightly **hurt**. Robustness: 0.048σ at σ=0.00229, 0.013σ at the
  CI upper bound — null on every branch.
- **Output / logged.** `evidence/out/c3_noise_floor.csv`, `evidence/out/c3_effect_translation.csv`,
  log block `EXP C3`.
- **Trains?** **NO — this is the point.** It re-evaluates finished predictions. 10–20 min CPU.
- **Assumptions / limitations.** **Linearity** of the pool-shift → Sα response is an *assumption*
  from a *single* anchor point, and the log block states it verbatim; the anchor added real
  target-domain supervision that arm C does not, so the rate is generous to arm C. σ was measured on
  the 4447-image pool while the arms would use ~7824 with 30–35% real content — **UNVERIFIED**. n=4
  gives a 6.6× CI on σ, narrowing to 3.9× at n=6; a **fifth distinct seed was never run**. Eφ is
  included as requested, but the surviving `audit6.json` stored only Sα/Fβw/MAE and the older
  `metrics.json` has meanEm for four runs only (0.7221/0.7226/0.7151/0.7144) — so **Eφ for repB/repC
  is a new computation with no stored value to match**, logged **NEW** rather than MATCH. The
  "~50–64×" span is fully sourced: 64× at B=1000 (`STAGE_C_RED_TEAM_AUDIT.md §(a)`), 51× at B=2000
  (`PRIOR_REVIEW.md §0.7-D1`).
- **Revision surfaced.** **R-g** — σ = 0.00286 (wrong grouping: seeds only) vs **0.00356** (arm-run,
  n=6). Both are computed and logged, and the verdict is shown to be robust to the choice. Also
  **R-m**: the premise that the noise floor "was never run" is falsified — six completed runs existed.

---

### Group D — the data-integrity checks that scope any conclusion

#### D1 — Foreground-exhaustion check

- **Objective.** Establish that the HKU-IS foreground pool is exhausted, so increasing B buys
  re-renders of foregrounds already present rather than new foregrounds.
- **Script.** `evidence/d1_foreground_exhaustion.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/d1_foreground_exhaustion.py
  ```
- **Inputs read.** `Dataset/Source/HKU-IS/{Image,GT}` (4447/4447);
  `Dataset/Source/HKU-IS_raw/{imgs,gt}` (4447/4447);
  `Dataset/LAKERED/output/HKU-IS/{images,masks}` (4447/4447);
  `Dataset/LAKERED/input/HKU-IS/validation`.
- **Method.** Stem-set comparison plus SHA256 of every mask, showing the generated-output set is a
  **bijection** onto the raw HKU-IS foreground set — one generated image per foreground, identical
  masks — so the number of *distinct* foregrounds available to Stage C is exactly 4447 and is already
  fully consumed. Emits a manifest CSV of stem → source hash → generated hash → mask hash.
- **Expected.** 4447 = 4447 = 4447; stem sets identical; mask hashes matching between
  `HKU-IS_raw/gt` and `LAKERED/output/HKU-IS/masks` modulo a documented resize/re-encode; **zero**
  foregrounds in the generated pool that are absent from the base pool. Per `PRIOR_REVIEW.md` §0.5
  the render pool holds **2 internal duplicate hashes ⇒ 4445 unique of 4447**, which the script
  reports rather than rounds away.
- **Output / logged.** `evidence/out/d1_foreground_manifest.csv`, log block `EXP D1`.
- **Trains?** NO.
- **Assumptions / limitations — an honest scope reduction.** The original framing verified this
  against the **iteration-2 pool manifests** (`HKU-IS_iteration2`, `-SINet`, `-SINetV2`) and reported
  those pools as 30.0–34.8% real target imagery. **Those directories no longer exist anywhere on the
  filesystem.** So the *load-bearing* claim — 4447 distinct foregrounds, fully consumed, therefore
  additions are re-renders — **is** reproducible from what remains, and this script proves it. The
  *derived* claims that depended on the deleted pools (|Ds| = 6824/7824/8824, "30–35% real",
  "B=1000 is 18% of the synthetic part") are marked **UNVERIFIED-NOT-REPRODUCIBLE** and cited to
  `STAGE_C_MEASUREMENTS.md §(b)` — in the log block, in `EVIDENCE_APPROACH.md`, and wherever C2 and
  C3 consume them.
- **Revision.** None to the conclusion; a documented reduction in what can be re-verified.

#### D2 — Leakage sweep

- **Objective.** Bound what the experiment can and cannot claim, by full pairwise pixel-identity
  comparison across every split.
- **Script.** `evidence/d2_leakage_sweep.py`
- **Command.**
  ```bash
  LAKE-RED/.venv/bin/python evidence/d2_leakage_sweep.py
  ```
- **Inputs read.** `Dataset/Target/Image` (4040);
  `Dataset/Test/{COD10K,CAMO,CHAMELEON,NC4K}/Imgs` (2026 / 250 / 76 / 4121);
  `Dataset/Val/CAMO/Imgs` (250); `Dataset/Source/HKU-IS/Image` (4447);
  `Dataset/LAKERED/output/HKU-IS/images` (4447).
- **Method.** **Full pairwise hashing, not name matching** — 5 of the 7 known duplicates are
  cross-named. Two stages: SHA256 for byte-identity, then a decoded-pixel hash with `maxdiff == 0`
  verification on candidates, to catch jpg→png re-encodes. Sweeps every ordered pair of splits plus
  internal duplicates within each split.
- **Expected — fully sourced across the two audits and `PRIOR_REVIEW.md` §0.5.**

  | pair | expected | source |
  |---|---|---|
  | COD10K-test ∩ Target | **7** — 2 same-name (`Cat-1506`, `Crab-32`), 5 cross-named (Owl-4633↔Bird-3205, Deer-1762↔Deer-1796, Gecko-1892↔Chameleon-1694, Giraffe-1932↔Giraffe-1930, Gecko-1895↔Gecko-1928) | both audits + §0.5 |
  | CAMO / CHAMELEON / NC4K ∩ Target | **0** each | §0.5 |
  | any test set ∩ Source/HKU-IS, ∩ LAKE-RED renders | **0** | §0.5 |
  | **`Val/CAMO` ∩ `Test/CAMO`** | **250 / 250 byte-identical** | §0.5 |
  | **CAMO ∩ CHAMELEON** | **3** byte-identical | §0.5 |
  | internal duplicates in `Target/` | **2** | measurements §(a) |
  | internal duplicates in the render pool | **2** (4445 unique of 4447) | §0.5 |

  Impact bound on the 7: test MAE **0.074697** over all 2026 vs **0.074709** excluding them — a shift
  of **0.000012 (0.017% relative)**; their mean MAE percentile within the clean test set is **0.477**
  (0.5 = indistinguishable); 1−IoU is 0.579 on the 7 vs 0.551 on the rest, i.e. the leaked images
  score **worse** — no memorisation signature.
- **The scoping consequence, which is the point of D2.** `MyTrain.py:324` selects
  `Tea_epoch_best.pth` on `--val_root ./Dataset/Val/CAMO/`, and that set *is* CAMO-test. So **every
  checkpoint in every arm is chosen by its score on a test set.** It applies identically to all arms,
  so it cannot bias B-vs-C — but **CAMO can never be reported as an endpoint**. Primary stays
  COD10K-test; secondary become CHAMELEON (76) and NC4K (4121). This is inherited from the published
  S2R-COD protocol, not introduced here, so it is disclosed rather than "fixed" — changing the val
  set would break Table 1 comparability. The script asserts it and the log block records it.
- **Output / logged.** `evidence/out/d2_leakage_report.md`, `evidence/out/d2_collisions.csv`,
  log block `EXP D2`.
- **Trains?** NO. 5–10 min CPU for the ~11k-image sweep.
- **Assumptions / limitations.** **Pixel-identity only** — near-duplicates (crops, rescales,
  different photographs of the same specimen) are out of scope, and that limit is stated. The 7
  COD10K duplicates are COD10K's *own* train/test duplicates, so the defect is a violated protocol
  rather than label leakage: pseudo-labels come from the **teacher** (`CLS.py:115-156`), so test
  *pixels* enter training but test *labels* never do — the transductive UDA setting. **Not** grounds
  for re-running the Table 1 reproduction. What survives as actionable is the *mechanism*: nothing
  filters Target against Test, so every future cycle re-admits these images.
- **Revision.** None; this closes an item the audits left as an incomplete sweep.

---

## 3. Commit discipline

One experiment, one commit — never batched. Each commit contains the script, its appended log block,
and any CSV or figure it produced:

```
docs(evidence): approach and run-book for the Stage C evidence package
evidence(E0): artifact rescue, hash manifest, environment capture
evidence(A1): conditioning-width measurement
evidence(A2): object-vs-background pixel share
evidence(A3): appearance signature with JPEG and cross-dataset controls
evidence(B1): ES-vs-true-error correlation
evidence(B2): coverage-term falsification
evidence(B3): targeting acceptance, both embedders, vs chance
evidence(C1): targeted-vs-random data distance
evidence(C2): budget-B arithmetic and per-arm sampling
evidence(C3): noise floor and effect-size translation
evidence(D1): foreground-exhaustion check
evidence(D2): leakage sweep
```

Where a measured number disagrees with the expected value quoted in this run-book, the markdown is
corrected **in that experiment's own commit**, so the git history shows the disagreement rather than
hiding it.

## 3b. The results summary

```bash
LAKE-RED/.venv/bin/python evidence/summarize_log.py           # rebuild
LAKE-RED/.venv/bin/python evidence/summarize_log.py --check    # exit 1 if stale
```

Writes [results/RESULTS_SUMMARY.md](results/RESULTS_SUMMARY.md) (one quotable page: status,
headline numbers per experiment, revisions surfaced, anything that did not reproduce, what is still
pending) and `results/RESULTS_SUMMARY.json` for programmatic access. Both are derived from the log,
never hand-edited — re-run it after each experiment's commit. It is not an experiment and never
appends a block.

## 4. Verifying the package as a whole

```bash
sha256sum -c evidence/manifests/MANIFEST.sha256           # singleton inputs intact
sha256sum -c evidence/manifests/SOURCES.sha256            # source documents intact
grep -c '^====' results/STAGE_C_EVIDENCE_LOG.txt          # two lines per block
git log --oneline --grep='^evidence('                     # one commit per experiment
```

Three self-checks catch a broken pipeline rather than a wrong conclusion:

1. **B1** — per-image mean MAE on COD10K-test must land at **0.0747** against the repo's recorded
   **0.0745**.
2. **C3** — the six Sα values must match the rescued `audit6.json` to four decimals.
3. **A1** — the live `vec_fg` shape must be `(1, 16, 3)`.

Every `UNVERIFIED`, `NOT-REPRODUCIBLE` or `NEW` label in the log also appears in
[EVIDENCE_APPROACH.md](EVIDENCE_APPROACH.md), so the prose and the raw trail agree on what is not proven.

# SETUP.md — rebuilding this project on a new machine

Working notes for the ICLR 2027 submission *Concentration, Not Uncertainty: Why Targeted Synthetic
Data Doesn't Help Camouflaged Object Detection* (submitted 2026-09-25, source
[`AD-PCHG-250926.tex`](AD-PCHG-250926.tex)).

> **Why this is not in `README.md`.** `README.md` is the upstream S2R-COD readme, and it is
> **evidence, not documentation**. `rebuild/D2_reaudit/d2r_reaudit.py:787-792` parses it — counting
> `CHAMELEON` occurrences, locating the `CNC` line, and reading the `Test (Real)` section — to
> establish the paper's claim that the protocol we inherited listed CHAMELEON only inside a
> synthetic-*source* bundle and never as a test set. Editing `README.md` silently changes the
> provenance of a published claim. **Leave it alone.**

---

## 1. Five-minute verification (no GPU, no data, no checkpoints)

```bash
uv sync
uv run python rebuild/D2_reaudit/detect_contamination.py --self-test   # 8 assertions, PASS
uv run python rebuild/DIAG/diag_tost.py                                # writes diag_tost.json
```

Both verified working. [`NAVIGATION.md`](NAVIGATION.md) lists the full no-GPU check set.

---

## 2. Environment

| Requirement | Version here |
|---|---|
| Python | 3.12.3 (pinned in `.python-version`) |
| `uv` | 0.12.0 — the only package manager; **no conda** |
| CUDA | 12.8 — Blackwell cards require cu128 wheels |
| torch | 2.11.0+cu128 |
| GPU | 2× RTX PRO 6000 Blackwell, 96 GB each |

**Two separate uv projects**, deliberately — the generator's dependency tree conflicts with the lean
training environment:

```bash
uv sync                          # training, evaluation, all of rebuild/
cd LAKE-RED && uv sync && cd ..   # synthetic image generation only
```

Verify the CUDA build landed (this fails silently on Blackwell with the wrong index):

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# expect: 2.11.0+cu128 True
```

Backbones, not in git (`*.pth` is gitignored):

| File | Destination |
|---|---|
| `resnet50-11ad3fa6.pth` | `Src/model/SINet/` |
| `res2net50_v1b_26w_4s-3cf99910.pth` | `Src/model/SINetV2/` |

Then: `uv run python preflight.py` — exit 0 means clear to train.

---

## 3. What each experiment needs

Audited by scanning every script's path references. **This is the table that decides what you back
up.**

| Experiment | What it reads | Runs from a minimal restore? |
|---|---|---|
| `A1` `AC` `OR` `FX` `SE` `C1` | committed `out/` only | **yes** |
| `A3` `B1` | `Dataset/Target/Image` (+ `Result/`) | yes, with the small dataset subset |
| `D1` | `Dataset/Source/HKU-IS/Image` | yes |
| `E0` | `Dataset/Source/HKU-IS_raw`, LAKERED renders | yes |
| `D2` `D2_nc4k` `D2_FINAL_AUDIT` | `Dataset/{Test,Val,Target,chameleon_new}` | yes |
| `DIAG` | `Dataset/{Target,Test,chameleon_new}`, `Result/` | yes |
| `D2_reaudit` `T2C` | above **+ `Snapshot/`** (`Tea_epoch_best.pth`) | yes, with best checkpoints |
| `PC` `ABC` (evaluate) | `Snapshot/*/Tea_epoch_best.pth`, `Result/` | yes, with best checkpoints |
| `ABC` (train) | `Dataset/Source/ABC` (234 GB of pools) | only if you rebuild pools first |

**Nothing in `rebuild/` reads `Dataset/Source/ABC` except the training driver.** Every analysis,
diagnostic and audit experiment is independent of that 234 GB.

---

## 4. What is regenerable, verified

### Renders — regenerable, bit-for-bit

`Dataset/LAKERED/output/HKU-IS/` (118 MB, 4447 images). E0 step `s4` re-ran generation at seed 0
and compared against disk: **4447 of 4447 identical**, cluster agreement 1.0
(`rebuild/E0/out/e0_render_regen.csv`, `e0_render_cluster_agreement.json`).

Regenerating costs GPU hours and needs the LAKE-RED checkpoints (~10 GB, re-downloadable upstream).
At 118 MB, backing them up is far cheaper than ever proving that again.

```bash
uv run python rebuild/E0/e0_regenerate.py --steps s4
```

### Round-1 training pools — regenerable, cheap

`Dataset/Source/ABC/<run>/` — base 4447 pairs plus the arm's additions. The base images are
**hardlinked**, not copied (100 links each), so each round-1 pool costs ~141 MB of real disk.

```bash
uv run python rebuild/ABC/abc_build_pools.py
```

### Round-2 pools — regenerable *only with round-1 checkpoints*

`Dataset/Source/ABC/<run>_iteration2/` — 100 directories at ~2.2 GB each, **~220 GB of the 234 GB
total**. These are CLS pseudo-label output, not pool construction. `CLS.py:43-73` loads:

- `Stu_40.pth` (SINet) or `Stu_100.pth` (SINet-v2) — the **student** at the last epoch
- `Tea_epoch_best.pth` — the teacher, falling back to `Tea_40/Tea_100.pth` if absent

So `abc_build_pools.py` alone does **not** reproduce them. If you intend to re-run the closed loop
rather than just re-score it, you need the student checkpoints too (§5).

### Public datasets — re-downloadable

HKU-IS, CAMO, NC4K, COD10K, CHAMELEON: links in `README.md`. `Dataset/chameleon_new/` (33 MB) is the
author-sourced CHAMELEON release used to verify the contamination finding — keep it, it is not a
standard download.

---

## 5. Checkpoints: what is actually read

Verified by grepping every loader in `rebuild/` and `CLS.py`.

| Checkpoint | Read by | Size | Needed for |
|---|---|---|---|
| `Tea_epoch_best.pth` | `abc_evaluate.py:117`, `pc_evaluate.py:45`, `d2r_reaudit.py:77` | **15.8 GB** (110 files) | all scoring, inference, new metrics |
| `Stu_40.pth` / `Stu_100.pth` | `CLS.py:43,48` | **21.2 GB** (163 files) | re-running round 2 / pseudo-labelling |
| `Tea_40.pth` / `Tea_100.pth` | `CLS.py:44,49` (fallback only) | 21.2 GB | **not needed** — all 100 ABC runs have `Tea_epoch_best` |
| everything else (`Stu_10..39`, `Tea_10..39`) | nothing | ~200 GB | **nothing** |

Each run directory holds 17 checkpoints at ~188 MB; only 1–2 of them are ever loaded.

---

## 6. Backup tiers

| Tier | Contents | Size | Buys you |
|---|---|---|---|
| **0** | git bundle (667 MB) + `Dataset/LAKERED/` (470 MB: 118 MB renders + 353 MB staged inputs) | **~1.1 GB** | the work itself; renders are gitignored, so this machine is their only copy |
| **1** | + analysis dataset subset (§6.1) | **+3.5 GB** | every diagnostic and audit experiment |
| **2** | + `Tea_epoch_best.pth` ×110 | **+15.8 GB** | all re-scoring and new metrics without retraining (~2.5 GPU-days saved) |
| **3** | + `Stu_40/Stu_100.pth` ×163 | **+21.2 GB** | re-running the closed loop / round 2 |
| skip | `Snapshot/ABC` in full, `Dataset/Source/ABC`, public datasets, LAKE-RED ckpts | 500+ GB | nothing you cannot rebuild |

**Tier 0+1+2 ≈ 20 GB** and covers every realistic rebuttal need. Note that a free Google Drive
account is 15 GB total, so Tier 2 needs a paid plan or a second destination.

### 6.1 Commands

```bash
cd /home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD
OUT=~/s2rcod-backup && mkdir -p $OUT

# Tier 0 — the irreplaceable part
git bundle create $OUT/repo-$(date +%F).bundle --all
tar czf $OUT/renders.tar.gz Dataset/LAKERED/

# Tier 1 — analysis dataset subset (~3.5 GB)
tar czf $OUT/dataset-analysis.tar.gz \
    Dataset/Target Dataset/Test Dataset/Val \
    Dataset/chameleon_new Dataset/Source/HKU-IS Dataset/Source/HKU-IS_raw

# Tier 2 — best checkpoints (15.8 GB)
find Snapshot -name 'Tea_epoch_best.pth' -print0 \
    | tar czf $OUT/ckpt-best.tar.gz --null -T -

# Tier 3 — student checkpoints, only if re-running round 2 (21.2 GB)
find Snapshot \( -name 'Stu_40.pth' -o -name 'Stu_100.pth' \) -print0 \
    | tar czf $OUT/ckpt-student.tar.gz --null -T -

sha256sum $OUT/*.tar.gz $OUT/*.bundle > $OUT/SHA256SUMS
```

### 6.2 Restore

```bash
git clone repo-<date>.bundle S2R-COD && cd S2R-COD
uv sync && (cd LAKE-RED && uv sync)
tar xzf ~/renders.tar.gz
tar xzf ~/dataset-analysis.tar.gz
tar xzf ~/ckpt-best.tar.gz
# backbone weights per §2, then:
uv run python preflight.py
uv run python rebuild/ABC/abc_build_pools.py    # only if retraining
```

---

## 7. Gotchas

- **`README.md` is evidence.** See the banner at the top of this file.
- **`rebuild/SE/chain_se.sh:8` and `rebuild/FX/chain_fx.sh:4` hardcode the absolute repo path.**
  Edit before running elsewhere.
- **Never add seeds to a committed campaign.** The seed expansion is a separate campaign with its
  own arms, noise estimate and verdicts. Adding seeds after seeing a result is how a null gets
  talked into existence.
- **Main text is pinned at exactly 9 pages.** Any rebuttal addition must remove something else.
- `--workers` on `abc_evaluate.py` parallelises across (run, endpoint) cells and changes no number.

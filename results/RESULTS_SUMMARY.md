# Results summary — Stage C evidence package

> **Generated file — do not edit by hand.** Rebuilt from
> [STAGE_C_EVIDENCE_LOG.txt](STAGE_C_EVIDENCE_LOG.txt) by
> `evidence/summarize_log.py`, so it cannot drift from the evidence. Rationale for every
> number is in [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md); how to reproduce it is in
> [../EVIDENCE_SCRIPTS.md](../EVIDENCE_SCRIPTS.md).

Generated 2026-08-27T20:40:37+05:30 at commit fb893d5 (dirty).

**5 of 12 experiments complete.** 38 of 39 thresholds PASS. Trains a model: NO for every experiment.

## Status

| id | experiment | supports | status | thresholds | vs prior audits |
|---|---|---|---|---|---|
| **E0** | Artifact rescue, hash manifest, environment capture | gate - provenance for everything below | **DONE** (3 blocks) | 4/4 PASS | 2 MATCH |
| **A1** | Conditioning-width measurement | conclusion (i) - the generator is near-unsteerable | **DONE** | 6/6 PASS | 1 NEW, 2 MATCH |
| **A2** | Object-vs-background pixel share | conclusion (i) - what those 48 numbers have to steer | **DONE** (5 blocks) | 6/6 PASS | 2 MATCH |
| **A3** | Generated-vs-real appearance signature, with controls | context - demotes the AUC 0.999 finding to a truism (R-c..R-f) | **DONE** (2 blocks) | 8/9 **1 FAIL** | 3 MISMATCH, 10 MATCH |
| **B1** | ES-vs-true-error correlation | SURVIVED - uncertainty is a real weakness signal | **DONE** (2 blocks) | 14/14 PASS | 5 MISMATCH, 10 MATCH |
| **B2** | Coverage-term falsification | SURVIVED - lambda_cov = 0 is measured, not assumed | pending | — | — |
| **B3** | Targeting acceptance, both embedders, vs chance | SURVIVED - targeting works (and R-a, R-b) | pending | — | — |
| **C1** | Targeted-vs-random data distance | conclusion (iv) - the effect-size wall | pending | — | — |
| **C2** | Budget-B arithmetic and per-arm sampling | conclusions (ii) and (iv) - zero extra steps; no B rescues it | pending | — | — |
| **C3** | Noise floor and effect-size translation | conclusion (iv) - 0.031 sigma against a 2 sigma bar | pending | — | — |
| **D1** | Foreground-exhaustion check | conclusion (iii) - additions are re-renders | pending | — | — |
| **D2** | Leakage sweep | scope bound - what any result can and cannot claim | pending | — | — |

## Headline numbers

### E0 — Artifact rescue, hash manifest, environment capture

| metric | value | provenance |
|---|---|---|
| `prediction_files_total` | **12156** | 6 x 2026 |
| `checkpoints_rescued` | **12/12** | Stu_40.pth + Tea_epoch_best.pth per run |
| `rescued_size_gib` | **3.42** | — |

Command: `LAKE-RED/.venv/bin/python evidence/e0_rescue.py`

Artifacts: `evidence/manifests/MANIFEST.sha256`, `evidence/manifests/PRED_DIGESTS.txt`, `evidence/manifests/SOURCES.sha256`, `evidence/out/e0_environment.json`, `evidence/sources/PRIOR_REVIEW.md`

### A1 — Conditioning-width measurement

| metric | value | provenance |
|---|---|---|
| `conditioning_width` | **48** | n_super_pix x channels_per_superpixel |
| `vec_fg_shape_live` | **(1, 16, 3)** | hook on mlp_in input, sample SOD_0004 |
| `effective_width_mean` | **45.75** | 20 real samples; empty superpixels are zero-filled |

Command: `LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py --samples 20`

Artifacts: `evidence/out/a1_conditioning.csv`, `evidence/out/a1_superpixel_occupancy.csv`

### A2 — Object-vs-background pixel share

| metric | value | provenance |
|---|---|---|
| `fg_fraction_mean` | **0.1913** | threshold 127 |
| `invented_background_mean` | **0.8087** | 1 - fg |

Command: `LAKE-RED/.venv/bin/python evidence/a2_fg_pixel_share.py`

Artifacts: `evidence/out/a2_fg_fraction.csv`, `evidence/out/a2_summary.csv`, `evidence/out/a2_cross_source_consistency.csv`, `evidence/out/a2_fg_hist.png`

### A3 — Generated-vs-real appearance signature, with controls

| metric | value | provenance |
|---|---|---|
| `probe_auc_real_vs_lakered` | **0.9989** | THE headline claim |
| `probe_auc_real_vs_real_random` | **0.4781** | the TRUE null control |
| `probe_auc_jpeg75` | **0.4117** | IDENTICAL images, recompressed |
| `recall_lakered` | **0.4662** | k=5 NN manifold |
| `recall_raw_hkuis` | **0.7461** | the pool LAKE-RED starts FROM |

Command: `LAKE-RED/.venv/bin/python evidence/a3_appearance_signature.py --pixel-sample 0`

Artifacts: `evidence/out/a3_probe_table.csv`, `evidence/out/a3_precision_recall.csv`, `evidence/out/a3_pixel_stats.csv`, `evidence/out/a3_pixel_per_image.csv`

### B1 — ES-vs-true-error correlation

| metric | value | provenance |
|---|---|---|
| `selfcheck_mean_MAE_test` | **0.074463** | repo records 0.0745 |
| `selfcheck_mean_Sa_test` | **0.717216** | repo records 0.7172 |
| `pred_vs_recorded` | **n=400 mean|d|=0.000 max|d|=0.000 levels** | regenerated vs Result/SINet/S2C |

Command: `LAKE-RED/.venv/bin/python evidence/b1_es_error_correlation.py --k 15,20,50,100 --runs repro,s42,s43,s45,s46 --perm 5000`

Artifacts: `evidence/out/b1_cluster_correlations.csv`, `evidence/out/b1_cross_run.csv`, `evidence/out/b1_scores_test_*.csv`, `evidence/out/b1_scores_val_repro.csv`

## Revisions surfaced so far

Conclusions that moved once measured. The full 13-row trail, including revisions from
experiments not yet re-run here, is §5 of [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md).

- **A2** — within-experiment: first run gave fg 0.1923 under per-image polarity detection, which misfires on 11 corner-covering objects; per-source polarity gives 0.1913. Also refines the source's 81.8% invented background to the measured 80.9%.
- **A3** — R-c sorted-filename split bug (ceiling 0.893/0.871 -> corrected, both computed here); R-d recall share 54% -> recomputed; R-e ~20-level darkening RETRACTED as the mechanism; R-f AUC 0.999 demoted to near-vacuous
- **B1** — R-h: rho 0.82 is against MAE; against the headline metric Sa the same signal gives only +0.40..+0.65. Both computed here.

## Anything that did not simply reproduce

| id | claim | verdict |
|---|---|---|
| A1 | effective width on real samples = not pinned by any source | **NEW** |
| A3 | probe AUC true null vs the audit's particular draw = 0.5289 | **MISMATCH** |
| A3 | probe AUC JPEG-75 = 0.938 | **MISMATCH** |
| A3 | fg | **MISMATCH** |
| B1 | rho(ES, MAE) per-cluster k=20 test = 0.857 | **MISMATCH** |
| B1 | rho(ES, 1-Sa) per-cluster k=20 = 0.645 | **MISMATCH** |
| B1 | rho(ES, 1-IoU) per-cluster k=20 test = 0.513 | **MISMATCH** |
| B1 | rho(ES, MAE) per-cluster k=20 val = 0.8 | **MISMATCH** |
| B1 | rho(ES, MAE) per-cluster k=15 val = 0.967 | **MISMATCH** |

`NEW` means the package measured something no source document pinned, so there was
nothing to agree or disagree with.

## Still to run

- **B2** Coverage-term falsification — SURVIVED - lambda_cov = 0 is measured, not assumed
- **B3** Targeting acceptance, both embedders, vs chance — SURVIVED - targeting works (and R-a, R-b)
- **C1** Targeted-vs-random data distance — conclusion (iv) - the effect-size wall
- **C2** Budget-B arithmetic and per-arm sampling — conclusions (ii) and (iv) - zero extra steps; no B rescues it
- **C3** Noise floor and effect-size translation — conclusion (iv) - 0.031 sigma against a 2 sigma bar
- **D1** Foreground-exhaustion check — conclusion (iii) - additions are re-renders
- **D2** Leakage sweep — scope bound - what any result can and cannot claim

Expected values for these are in [../EVIDENCE_SCRIPTS.md](../EVIDENCE_SCRIPTS.md) and are
**not yet verified**. Treat any number without a log block as a claim awaiting
reproduction.


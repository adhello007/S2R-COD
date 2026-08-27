# Results summary — Stage C evidence package

> **Generated file — do not edit by hand.** Rebuilt from
> [STAGE_C_EVIDENCE_LOG.txt](STAGE_C_EVIDENCE_LOG.txt) by
> `evidence/summarize_log.py`, so it cannot drift from the evidence. Rationale for every
> number is in [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md); how to reproduce it is in
> [../EVIDENCE_SCRIPTS.md](../EVIDENCE_SCRIPTS.md).

Generated 2026-08-27T19:29:19+05:30 at commit 81005b7 (dirty).

**3 of 12 experiments complete.** 16 of 16 thresholds PASS. Trains a model: NO for every experiment.

## Status

| id | experiment | supports | status | thresholds | vs prior audits |
|---|---|---|---|---|---|
| **E0** | Artifact rescue, hash manifest, environment capture | gate - provenance for everything below | **DONE** (3 blocks) | 4/4 PASS | 2 MATCH |
| **A1** | Conditioning-width measurement | conclusion (i) - the generator is near-unsteerable | **DONE** | 6/6 PASS | 1 NEW, 2 MATCH |
| **A2** | Object-vs-background pixel share | conclusion (i) - what those 48 numbers have to steer | **DONE** (5 blocks) | 6/6 PASS | 2 MATCH |
| **A3** | Generated-vs-real appearance signature, with controls | context - demotes the AUC 0.999 finding to a truism (R-c..R-f) | pending | — | — |
| **B1** | ES-vs-true-error correlation | SURVIVED - uncertainty is a real weakness signal | pending | — | — |
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

## Revisions surfaced so far

Conclusions that moved once measured. The full 13-row trail, including revisions from
experiments not yet re-run here, is §5 of [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md).

- **A2** — within-experiment: first run gave fg 0.1923 under per-image polarity detection, which misfires on 11 corner-covering objects; per-source polarity gives 0.1913. Also refines the source's 81.8% invented background to the measured 80.9%.

## Anything that did not simply reproduce

| id | claim | verdict |
|---|---|---|
| A1 | effective width on real samples = not pinned by any source | **NEW** |

`NEW` means the package measured something no source document pinned, so there was
nothing to agree or disagree with.

## Still to run

- **A3** Generated-vs-real appearance signature, with controls — context - demotes the AUC 0.999 finding to a truism (R-c..R-f)
- **B1** ES-vs-true-error correlation — SURVIVED - uncertainty is a real weakness signal
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


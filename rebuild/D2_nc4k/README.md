# D2_NC4K — Is NC4K contaminated by the COD10K test split?

**Everything for this experiment lives in `rebuild/D2_nc4k/`.**

| File | Role |
|---|---|
| `README.md` (this file) | **Setup** — script run, directories read and written, steps, declared thresholds |
| `results/REBUILD_LOG.txt`, block `EXP D2_NC4K` | **Authoritative record.** This file is a reading of its setup, not of its numbers |

No measured number appears in this file.

| | |
|---|---|
| **Objective** | Test whether NC4K's test images overlap COD10K's test images, and separately COD10K-train. A null is a result and is reported as one |
| **Trains a model** | **NO** — no model is loaded at all |
| **Depends on** | `rebuild/D2_reaudit/detect_contamination.py` (imported, not copied), `rebuild/common.py` |
| **Consumed by** | `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` — its NC4K row is updated either way |

---

## 1. Why this specific check

The S2R-COD paper's Task Setup, **Case 3**, describes the NC4K evaluation as
additionally introducing synthetic images derived from the **COD10K test set** into the
**source** domain — Table 3's row `CAMO + CHAM. + COD10K → NC4K`.

If NC4K's own test images overlap COD10K's test images, that injection would place
synthetic renderings of NC4K's own test photographs into supervision. That is a
**source-into-test** collision, and a different mechanism from the D2/D2R CHAMELEON
finding:

| | D2 / D2R (CHAMELEON) | D2_NC4K (this experiment) |
|---|---|---|
| Side | **Target** — the unlabeled pool | **Source** — what supervises the model |
| Labels | Pseudo-labels from a teacher; test masks never enter | Source images carry supervision |
| Origin | Inherited from public dataset construction | Described by the authors in Case 3 |

So the two are not the same finding at different rates. This one is worth measuring on
its own terms — and worth reporting cleanly if it comes back empty.

## 2. Script

| Script | Role |
|---|---|
| [`d2_nc4k_crosscheck.py`](d2_nc4k_crosscheck.py) | The whole experiment: `s1` hash, `s2` NC4K vs COD10K-test, `s3` shortlist-depth sensitivity, `s4` NC4K vs COD10K-train, `s5` per-pair evidence |
| [`../D2_reaudit/detect_contamination.py`](../D2_reaudit/detect_contamination.py) | **The method.** Imported, never re-implemented |

```
LAKE-RED/.venv/bin/python rebuild/D2_nc4k/d2_nc4k_crosscheck.py
```

**Method identity is by import, not by inspection.** The sweep is the same module that
produced the committed 41/76 CHAMELEON result. It imports nothing from this repository
and passes an 8-assertion synthetic known-answer self-test, so the descriptor (32×32
greyscale BILINEAR, no contrast normalisation), the shortlist (Gram-matrix RMS ≤ 14,
exhaustive within each exact-dimension group), the confirmation rule (full-resolution
mean|A−B| ≤ 6.0), the 1/2/3/5/6 tolerance sweep and the >5× gap rule cannot drift from
the CHAMELEON audit.

## 3. Directories read

| Path | Count | Role |
|---|---|---|
| `Dataset/Test/NC4K/Imgs` | 4121 | the endpoint under test |
| `Dataset/Test/NC4K/GT` | 4121 | hashed for provenance only; no mask claim is made |
| `Dataset/Test/COD10K/Imgs` | 2026 | **the primary comparison — what Case 3 names** |
| `Dataset/Test/COD10K/GT` | 2026 | hashed for provenance only |
| `rebuild/D2_nc4k/cache/cod10k_train` | 3040 | the COD10K-CAM-* subset of `Dataset/Target/Image`, exposed as symlinks so the detector can take it as a plain path. Reported **separately** |

Nothing under `Dataset/`, `Result/` or `Snapshot/` is written. `cache/` is gitignored;
`out/` is tracked.

**On the COD10K-train side.** This checkout has no standalone COD10K-train directory:
its 3040 COD10K-CAM-* images sit inside `Dataset/Target/Image` alongside 1000 CAMO
images. The symlink view isolates the COD10K partition by construction, so a collision
can be attributed to a named split rather than to a mixed pool. Case 3's text says
"COD10K test set", so COD10K-test is the primary target of the check and the train side
exists to make the answer precise about which partition is involved.

## 4. Steps

| Step | What it does |
|---|---|
| `s1` | sha256 of file bytes, and sha256 of (shape + decoded RGB), over all three sets. Set-based intersections at both levels, filename-independent. Aggregate digests of all five input directories |
| `s2` | **NC4K vs COD10K-test.** Same-dimension exhaustive near-duplicate sweep, tolerance sweep, nearest-neighbour gap, and the unchecked count |
| `s3` | Re-runs `s2`'s nearest-neighbour analysis at shortlist depth **8 / 32 / all** and asks whether the gap verdict and the minimum nearest distance move |
| `s4` | **NC4K vs COD10K-train**, reported separately, with the partner names partitioned by split |
| `s5` | For any confirmed pair: JPEG quantization tables extracted two independent ways, plus container format — carrying D2R's caveat that a **missing** table is *not applicable*, never *differs* |

A contaminated-pair list (`out/nc4k_contaminated.json`, content-addressed by directory
digest like `chameleon_contaminated.json`) is emitted **only if there is something to
list**. An empty resource file would be a claim dressed as an artifact.

## 5. Declared thresholds

Fixed before the run. **PASS means no collision** — these assert cleanliness, so a
passing block is a clean null rather than a failure to find something.

| # | Condition |
|---|---|
| T1 | Every declared input is present with its declared count |
| T2 | NC4K ∩ COD10K-test is empty at the **file-byte** level |
| T3 | NC4K ∩ COD10K-test is empty at the **decoded-pixel** level |
| T4 | No NC4K image is a same-dimension re-encoded duplicate of a COD10K-test image at mean\|diff\| ≤ 6.0 |
| T5 | Every confirmed pair carries independent re-encoding evidence — a differing quantization table or a differing container format (vacuous if there are none) |
| T6 | The gap verdict and the minimum nearest distance are invariant across shortlist depth 8 / 32 / all |
| T7 | NC4K ∩ COD10K-train is measured and reported separately (NEW — no prior value) |
| T8 | Nothing under `Dataset/`, `Result/` or `Snapshot/` is modified |

## 6. Scope, declared in advance

- **Every count is a lower bound.** Coverage is exact duplicates plus same-dimension
  re-encodes. Rescaled copies that land outside every dimension group, crops, flips,
  rotations, colour shifts and different photographs of one specimen are **not**
  detected and are **not** claimed.
- **Unchecked is not clean.** An NC4K image with no same-dimension candidate on the
  other side cannot be compared at all. That count is logged for both comparisons
  rather than folded into a clean rate — and for this pair of sets it is large.
- **A null is quantitative here.** The minimum nearest distance and the decile spread
  of the nearest-distance distribution are logged, so "no collision" carries a margin
  instead of being a bare absence.
- **No claim about intent.** The block reports the measured overlap. Whether Case 3's
  described injection amounts to a leak follows from that measurement plus the paper's
  own text; this experiment supplies the measurement.
- **No mask claim.** GT directories are hashed for provenance. Whether NC4K and
  COD10K-test *masks* overlap is not measured.

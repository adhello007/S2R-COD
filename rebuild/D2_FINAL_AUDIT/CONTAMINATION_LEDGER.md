# CHAMELEON contamination — the number ledger

Every integer this project has produced about CHAMELEON contamination, what it means, and
where it comes from. **Written because the same integer means two different things in two
different artifacts, which made the audit trail look self-contradictory when it was not.**

Final answer: **50 of CHAMELEON's 76 images (65.8%) are copies of training-pool images.**

## The trap that caused the confusion

| `51` | means | source |
|---|---|---|
| `51/76` **checkable** | images with ≥1 *same-dimension* training candidate — the searchable denominator, not a result | `D2R_RESULTS.md` §1.3 |
| `51/76` **contaminated** | `41 + 10`, the Sept-18 headline before adjudication | `main_v2.tex`, `diag_chameleon_ext.json` |

Unrelated quantities, identical integer, coincidence. Anyone cross-reading concludes the
paper copied the wrong column. It did not. **The adjudicated count is 50, not 51** — see below.

## The ledger

| # | Quantity | Status |
|---|---|---|
| **76** | CHAMELEON size; author-sourced release byte-identical to repo copy at 76/76 | settled |
| **0** | exact hash (file bytes and decoded pixels) CHAMELEON ↔ training pool | settled |
| **41** | **Tier A** — same-dimension re-encodes, mean\|diff\| ≤ 6/255 | settled, triple-verified |
| **9** | **Tier B** — rescales/crops confirmed by post-warp residual | settled, this audit |
| **50** | **contaminated total = 41 + 9 (65.8%)** | **final** |
| 16 | unchecked — no partner found; *unchecked is not clean* | final |
| 10 | clean w.r.t. the **training pool** (not clean of CAMO-250; see below) | final |
| 25 | images the Tier-A detector could not check (Tier B resolved 9) | superseded |
| 51 | checkable denominator — **not a contamination count** | never a result |
| 51 | `41+10`, pre-adjudication headline | **superseded by 50** |
| 52 | `41+11` at the extension's looser 9-inlier threshold | rejected |
| 10/76 | first implementation; contrast normalisation destroyed the discriminative scale | known bug |
| 40 / 1 | Tier-A partners in COD10K-train / CAMO | settled |
| 7 | byte-identical train ↔ COD10K-test pairs | settled |
| 3 | byte-identical CHAMELEON ↔ CAMO-250 pairs | settled, new |
| 2 | byte-identical duplicate pairs inside the training pool | settled |

## Why 41 is not in question

D2 (Aug 31) and D2_reaudit (Sep 7) independently return the same 41 filenames; the
tolerance sweep saturates (11/26/37/40/41 at 1/2/3/5/6); an independent nearest-neighbour
gap puts 41 below 5.51 with the next at 40.58 (7.36×), invariant at shortlist depth
8/32/all; 41/41 pairs carry re-encoding evidence (40 by JPEG quantization table, 1 by
container format); all 41 are exported and were visually checked.

## Why Tier B is 9 and not 10

The extension established inlier counts. An inlier count shows that local patches agree on
a geometric model; it does not show two files are the same photograph — two exposures of
one static scene also agree on a homography. `rebuild/FINAL_AUDIT/adjudicate.py` supplies
the missing measurement: warp the partner into the CHAMELEON frame through the recovered
homography and measure the residual.

*Instrument validated first.* Run on 8 of the 41 known pairs it reproduces their recorded
mean\|diff\| to three decimals (0.603→0.603, 5.512→5.514) with H = identity.

*Nine confirm.* Residual 3.76–12.11, correlation 0.96–1.00, shear ≈ 0, perspective ≈ 0.
Scales run 0.39× to 6.36×; `animal-73` and `animal-22` sit at scale 1.000 with different
dimensions, i.e. pure crops. Difference panels are near-black. Same photographs.

*`animal-7.jpg` is rejected.* Its 25 inliers were a degenerate RANSAC fit: the homography
decomposes to **shear −86.5°, rotation 60.9°, anisotropic scale 0.24 vs 1.24**, collapsing
the image almost to a line. At full resolution with more features it yields no homography
at all. It was the only member below the extension's calibration band (525–1174 inliers)
and cleared the operating point of 20 by 5, while the NC4K negative control reached 19.
(`animal-28`, the 11th match at the looser threshold, fails identically.)

## Scoping notes the paper must respect

- **Operating point.** The extension's threshold is **20 inliers**, set by the NC4K
  control's max of **19** — not the 8+1=9 a reader derives from "maximum of 8 on random ones".
  At 9 it returns 11 matches, and 2 of those 11 are degenerate.
- **Stage 1 contributed nothing.** `stage1_pass` is 0/25; lowest `stage1_rms` 16.7 against a
  1.02 threshold. Every Tier-B match came from SIFT/RANSAC alone.
- **"Clean" means clean of the training pool.** `animal-25.jpg` is byte-identical to
  `Dataset/Val/CAMO/Imgs/camourflage_00890.jpg` (md5 `482ba6b8…`); likewise
  `animal-60 ≡ camourflage_00998` and `animal-17 ≡ camourflage_00090`. Those CAMO files are
  **not** in the training pool, so the "exact hashing returns 0" claim holds as stated — but
  CAMO-250 is this repo's checkpoint-selection set, so 3 CHAMELEON test images sit in the
  selection set. A reviewer hashing across benchmarks will find these; say it first.
- **Still a lower bound.** 16 images remain unchecked. Different photographs of one
  specimen, montages and heavy colour edits are not detected and are not claimed.

## Artifacts

| Path | What |
|---|---|
| `rebuild/FINAL_AUDIT/out/final_verdicts.{csv,json}` | per-image verdict for all 76 |
| `rebuild/FINAL_AUDIT/out/adjudication.{csv,json}` | per-pair geometry + residual |
| `rebuild/FINAL_AUDIT/out/sheet_extension.png` | the 9 confirmed + 2 rejected, visually |
| `rebuild/FINAL_AUDIT/out/sheet_anchor.png` | instrument validation against known pairs |
| `rebuild/D2_reaudit/out/chameleon_contaminated.json` | Tier A, the 41 |
| `rebuild/DIAG/out/diag_chameleon_ext.json` | extension inlier counts (pre-adjudication) |

# DOC-02: CHAMELEON protocol, duplicates and mask releases (QA-03)

**For:** the corresponding author, to draft the reply to QA-03 and amend `sec:contamination`,
`app:chamext` and `app:masks`. The proposed manuscript text is in §5. The evidence ledger is
`EXPERIMENTAL_EVIDENCE.md` §AN-05, and every number is in `RESULT_TABLES/AN-05_*.csv`.

**Status of the evidence.** Every count in the submitted paper was re-derived after the review with the
committed detectors, unchanged and at the published thresholds. **All of them reproduce exactly.** Two
facts are new: they come from pointing the same released detector at the validation and test splits,
which the submitted audit compared only against the training pool. Both are marked **new** below.

## 1. What was reproduced

| Quantity | Submitted | Re-derived after review | Source table |
|---|---|---|---|
| CHAMELEON images (author-sourced release; byte-identical to the repository copy) | 76 | 76 (76/76 identical) | `AN-05_chameleon_pairs.csv` |
| Same-dimension re-encodes in the training pool (Tier A) | 41 | 41; tolerance sweep 11/26/37/40/41; nearest-neighbour gap 5.51 → 40.58 | `RUNS/an05/tierA_target_4040.json` |
| Rescaled or cropped copies (Tier B, after warp adjudication) | 9 (`animal-7` rejected) | 9 (10 at the operating point; `animal-7` fails the full-resolution homography) | `RUNS/an05/tierB/`, `RUNS/an05/adjudicate/` |
| Confirmed duplicates (floor) | 50 / 76 | **50 / 76** | `AN-05_chameleon_pairs.csv` (`confirmed_floor_total`) |
| …of which the partner is in COD10K-train | 44 | **44** (the other 6 are in CAMO-train) | `in_cod10k_train_total` |
| No partner at either tier ("unchecked") | 16 | **16** | `unchecked_total` |
| Same-dimension candidates checked, no match (committed label "clean vs training") | 10 | **10**, but Tier B was never run on these | `tierA_checked_no_match_total` |
| Byte-identical to the training pool | 0 | 0 (also 0 pixel-identical) | `exact_sha_target` |
| Byte-identical to CAMO-250 | 3 (`animal-17/25/60`) | 3 | `exact_sha_camo250` |
| Tier-B recall on the 41 knowns; NC4K false positives | 41/41; 0 of 120 | 41/41; 0 of 120 | `run_logs/an05_tierB_adj_tables.log` |
| Mask releases: IoU as stored / after polarity alignment | 0.0 / 0.6932 | 0.0 / 0.6932; 27/76 identical after alignment; 40/76 at IoU ≥ 0.9 | `AN-05_mask_release.csv` |
| Same predictions, MAE against author-sourced vs repackaged masks | 0.2196 vs 0.0816 | 0.2196 vs 0.0816 | `AN-05_mask_release.csv` |

All 76 images are accounted for: **50 confirmed + 16 unchecked + 10 checked-without-match = 76**. The
committed record calls the last group "clean vs training". That overstates what was done: only the
same-dimension detector was run on them, so a cropped or rescaled copy would not have been found. We
recommend calling them *no duplicate found* rather than *clean*.

## 2. New: CHAMELEON also overlaps the test and validation splits

These come from the same released detector at the same 6/255 tolerance. Each shows the same kind of
nearest-neighbour discontinuity that supports the 41.

- **32 of 76 CHAMELEON photographs are re-encodes of COD10K-test images.** All 32 lie at mean
  absolute difference ≤ 4.49; the next CHAMELEON image is at 30.91, a 6.9× gap. The 32 include **all 16
  "unchecked"** images and **8 of the 10** checked-without-match images; the remaining 8 also have
  training-pool partners. So the 16 images the paper reports as unresolved are not unresolved with
  respect to COD10K. They are COD10K-test photographs, and they simply have no partner in the training
  split.
- **4, not 3, CHAMELEON photographs are in CAMO-250**, the split this repository selects checkpoints
  on. Three are byte-identical (`animal-17`, `animal-25`, `animal-60`). The fourth, `animal-28`, is a
  re-encode (mean absolute difference 0.607; next candidate at 47.7).
- In total, **74 of 76 CHAMELEON photographs have a duplicate in at least one of COD10K-train,
  CAMO-train, COD10K-test or CAMO-250**. Only `animal-38` and `animal-54` were found nowhere. NC4K
  shares no photograph with CHAMELEON (nearest candidate 39.2).

These overlaps with the test and validation splits do **not** affect any number the paper reports:
CHAMELEON is not an endpoint here. They matter for papers that report CHAMELEON beside COD10K-test, or
that select checkpoints on CAMO's test split.

## 3. Exposure pathways, separated as the reviewer asked

Per image: `RESULT_TABLES/AN-05_protocol_paths.csv`. Summary: `FIGURES/AN-05_protocol_paths.png`.

| Pathway | Common supervised COD protocol (train with masks on COD10K-train + CAMO-train) | This paper's protocol (synthetic source with labels; real COD10K/CAMO train images as an **unlabelled** target) |
|---|---|---|
| **Supervised training: the image and its mask are used** | **Direct for 50.** The model has fitted the ground-truth mask of a photograph it is then tested on. This is a violation of independent evaluation, regardless of whether the score moves | **Not detected for all 76.** The supervised source is HKU-IS plus its re-renders; no exact, pixel or same-dimension match was found (Tier B was not run against the source) |
| **Unlabelled target / transductive: the image is used, its label is not** | Not applicable | **Direct for 50.** Every run sees all 50 photographs without labels in round 1. Between rounds, **14–32 of them (mean 24.7 per run; 46 of 50 in at least one run)** are appended with the model's *own* predicted mask and trained on in round 2 (`AN-05_pseudolabel_exposure.csv`). No CHAMELEON annotation is used. Whether this would raise a CHAMELEON score depends on the method; it is exposure, not label leakage |
| **Checkpoint selection: labels of a validation split choose the model** | Protocol-dependent. **Direct for 4** where CAMO's 250-image test split is used for model selection | **Direct for 4** (3 byte-identical + 1 re-encode in CAMO-250, which selects checkpoints by MAE). This path uses labels, but only to choose among checkpoints |
| **Held-out evaluation** | CHAMELEON is the test set, and 32 of its photographs are also COD10K-test photographs, so the two are not independent benchmarks | CHAMELEON is not an endpoint. COD10K-test (primary) and NC4K (secondary) are used, and neither depends on CHAMELEON |

**Does any of this show score inflation?** No, and we make no such claim. The submitted difficulty
analysis found no advantage for the leaked subset: all eight percentiles fall between 0.448 and 0.559,
and the sign of the leaked-versus-clean difference flips with the mask release. That analysis was not
re-run after the review. A causal estimate of inflation would need a model trained without the
duplicated photographs, and none exists.

## 4. The mask-release finding, stated for re-use

The two circulating CHAMELEON annotation sets differ in polarity: the author-sourced release stores the
object as black (white fraction 0.719), the repackaged release as white (0.140). Read as stored they
overlap at IoU 0.0. After polarity alignment the mean IoU is 0.693, only 27 of 76 masks are identical,
and 40 of 76 reach IoU ≥ 0.9. Scoring one fixed set of predictions against each gives MAE 0.2196 and
0.0816, a 2.7× difference that comes from the annotation alone. A CHAMELEON number is therefore not
comparable across papers unless the release is named.

## 5. Proposed amendments (not applied to the submitted source)

1. **`sec:contamination`, after "…so $50$ is a floor rather than an estimate."** Add: *"The sixteen are
   not clean either: each is a re-encode of a COD10K-test photograph, as are 32 of the 76 in all, so
   CHAMELEON and COD10K-test are not independent benchmarks. Only two CHAMELEON images have no duplicate
   in COD10K or CAMO."*
2. **`sec:contamination`, the "uncontaminated subset is now 10 images" sentence.** Replace with: *"…the
   ten images with no training-pool partner are only same-dimension negatives, and eight of them are
   COD10K-test photographs."*
3. **`app:chamext`, "Scope of the exact-hash zero".** Change "three … byte-identical to CAMO-250" to
   *"three byte-identical, and a fourth (`animal-28`) re-encoded"*, and add that the released detector,
   pointed at COD10K-test and CAMO-250, finds 32 and 4 duplicates with nearest-neighbour gaps of 6.9×
   and 79×.
4. **`app:chamext`, "What remains uncounted".** Add the three-way accounting
   (50 confirmed / 16 unchecked / 10 same-dimension negatives) and drop "clean" wherever it describes
   the 10.
5. **A new short paragraph (appendix) on exposure by protocol**, using the table in §3. It separates
   supervised label use, transductive image use (with the 14–32 pseudo-labelled re-uses per run), and
   label-based checkpoint selection, and says plainly that none of the three is shown to change a score.

Page budget: items 1–2 add about three lines to the main text, within the 10-page discussion-phase
limit. Items 3–5 are appendix-only.

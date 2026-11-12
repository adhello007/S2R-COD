# AN-03: generator provenance, foreground diversity, coverage and mask quality

**Status: VERIFIED** for the existing LAKE-RED pool (provenance, coverage, mask QC).
**BLOCKED** for a foreground-varying generator: none was found with released code, valid masks and new
foreground content. Code: `rebuild/CAUS/an03_provenance_coverage.py`. Log:
`AN-03/provenance_coverage.log`. Tables: `AN-03_foreground_provenance.csv`,
`AN-03_coverage_and_qc.csv`.

## 1. Provenance: does the pool only repaint backgrounds?

Yes. This is independently re-measured; D1's committed per-image values are the cross-check, not the
input.

| | LAKE-RED renders (this campaign) | authors' pool |
|---|---|---|
| traced to a source photograph | 4447/4447 | 4447/4447 |
| object interior scored (mask eroded 3 px, ≥ 50 px) | 4443 | 4442 |
| interior mean abs diff, mean / max (0–255) | 5.60 / 17.5 | 9.63 / 31.4 |
| background mean abs diff | 70.8 | 70.6 |
| **objects plausibly regenerated (interior > 40)** | **0** | **0** |
| agreement with D1 per-image interior error (median / max abs diff) | 0.000 / 0.30 | 0.000 / 0.95 |

- 4443 + 4442 = **8,885 traced objects, 0 regenerated**, exactly as the manuscript states.
- **Distinct foreground photographs:** the 4,447 renders carry 4,443 (four raw images are byte
  duplicates).
- **Overlap with held-out splits:**
  - Renders against COD10K-test, NC4K and CAMO-250: 0 exact, 0 near-duplicate (AN-05).
  - Raw HKU-IS against NC4K: 1. Raw HKU-IS against CAMO-250: 3 photographs (2 unique CAMO-250
    images).

## 2. Kinds of foreground variation, and which the pool has

| Type | Description | LAKE-RED pool |
|---|---|---|
| (i) | same object/cutout, new background | **yes, the only kind** |
| (ii) | same object, recoloured/retextured | no (object interior preserved to ~6/255) |
| (iii) | same object, new shape/pose with an adjusted mask | no |
| (iv) | new object identities taken from new real cutouts | no (the cutout set is fixed at 4,443) |
| (v) | generated new object pixels/identities | no |

Re-allocating over this pool can only change *which* of 4,443 fixed foregrounds appear, and against
which background. It cannot create unseen object content.

## 3. Coverage of the target manifold, reproduced at every k

My own k-NN recall implementation reproduces the committed A3 table to 4 dp, for every embedder and
every k:

| k | renders, range across embedders | raw HKU-IS input, range |
|---|---|---|
| 3 | 0.07–0.48 | 0.60–0.64 |
| **5 (the paper's setting)** | **0.13–0.54** | **0.71–0.75** |
| 10 | 0.25–0.63 | 0.84–0.88 |
| 20 | 0.38–0.75 | 0.95–0.97 |

- The paper's 0.13–0.54 is the k = 5 row. The number is k-dependent, and the paper should say k = 5.
- **The ordering is not k-dependent.** At every k, the renders cover less of the target than their own
  input photographs do.
- Coverage is a property of the pool. It is shared by every allocation arm, and greater coverage would
  not by itself mean better segmentation.

## 4. Mask validity (the 4,447 render masks; every arm uses the same files)

- **Empty or full masks:** 0. **Non-binary pixels:** none.
- **Foreground fraction:** median 0.178; 5th–95th percentile 0.040–0.394.
- **Render mask equals the raw GT of its foreground:** 1000/1000 pixel-identical for every arm's
  selection, checked in every EXP-01 pool gate.
- **Multiple objects:** 2,105 masks (47%) have more than one connected component, and 1,114 (25%) have
  at least one hole. HKU-IS is a multi-object salient-object dataset. Every arm shares these masks, so
  they affect absolute levels, not arm contrasts.

## 5. Candidate foreground-varying generators (searched 2026-11-12)

| Candidate | What it changes | Code / weights | Verdict |
|---|---|---|---|
| Camouflage Anything (CVPR 2025) | Out-paints a camouflaged **background around a given segmented object**; the object is kept | no code link found on the CVPR listing or by search | fails the foreground-variation criterion by design; no code |
| RealCamo (arXiv 2512.22974; the manuscript's `chen2025realcamo`) | Out-painting; "the foreground region of the input image is preserved"; SD 1.5 + ControlNet, generator trained on the LAKE-RED dataset | v1: "Code and results will be released soon"; no code URL | fails the criterion; no code |
| LAKE-RED with **new source cutouts** (author-owned code, `LAKE-RED/`) | Type (iv): new foreground identities, background repainted as now | code and checkpoint are local | the only realisable route. It needs a new labelled, licensed, endpoint-disjoint cutout source, its own contamination audit and GPU rendering of ≥ 1000 renders per arm pool, and is **BLOCKED for compute**. Even then it varies identity, not object pixels. |

Sources:
- [CVPR 2025 open-access listing](https://openaccess.thecvf.com/content/CVPR2025/html/Das_Camouflage_Anything_Learning_to_Hide_using_Controlled_Out-painting_and_Representation_CVPR_2025_paper.html)
  (direct fetch refused with HTTP 403; the description comes from search snippets of this page and of
  the [CVPR poster page](https://cvpr.thecvf.com/virtual/2025/poster/32794))
- [RealCamo, arXiv 2512.22974](https://arxiv.org/abs/2512.22974v3) (v1 HTML read; v3 HTML not read)

## 6. Consequence

- **No vetted foreground-varying pool exists** for EXP-03. The acceptance condition is "enough
  validated distinct foreground-varying samples for N = 1000 per core arm, with mask integrity and
  split cleanliness", and it is not met. **EXP-03 and EXP-04 are BLOCKED.**
- The reviewer's CW-03 point therefore stands as a plausible, untested bottleneck. The audit confirms
  the premise: the pool repaints backgrounds of a fixed foreground set and covers less of the target
  than its own input. The causal claim, that the bottleneck *causes* the null, remains unproven.

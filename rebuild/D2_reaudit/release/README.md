# CHAMELEON / COD10K-train contamination: detector and leaked-image list

**41 of 76 images (53.9%) in the CHAMELEON camouflaged-object dataset are
re-encoded copies of images in the COD10K-train split** -- 40 of them in
COD10K-train and 1 in CAMO.

Any model trained on COD10K-train has therefore already seen those images.
A CHAMELEON evaluation column reported for such a model is not an independent
measurement.

## What is here

| File | What it is |
|---|---|
| `chameleon_contaminated.json` | the leaked-image list: every CHAMELEON filename that is a training re-encode, its training-pool partner, and the per-pair evidence |
| `detect_contamination.py` | the detector, standalone. Point it at any two image directories |
| `CLEAN_PROTOCOL.md` | which evaluation columns are safe to report, with measured contamination rates |

## Reproduce it

```
python detect_contamination.py --self-test          # verify the tool itself
python detect_contamination.py CHAMELEON_DIR COD10K_TRAIN_DIR
```

`listing_sha256` in the JSON is the aggregate digest of the sorted
`sha256  filename` listing of each directory, so you can confirm you hold the
same sets before comparing counts.

## What the evidence is

Same exact dimensions; mean absolute pixel difference at full resolution within
tolerance; and **differing JPEG quantization tables** in every pair -- a copied
file keeps its table, a re-encode cannot. The tables are extracted two
independent ways (PIL, and a raw DQT-marker parse) so the verdict does not rest
on one library. The count is also confirmed by a discontinuity in the sorted
nearest-neighbour distances, which owes nothing to the tolerance.

## Scope, stated precisely

- Test **pixels** enter training. Test **masks** do not. This is a transductive
  protocol violation, not label leakage, and no claim of memorisation is made.
- Every count is a **lower bound**. Crops, flips, colour shifts, rescaled copies
  that leave every dimension group, and different photographs of one specimen are
  not detected. Images with no same-dimension candidate are reported as
  `unchecked`; unchecked is not clean.
- No dataset images are redistributed here. The underlying photographs are
  third-party licensed; this bundle carries filenames, measurements and the tool.

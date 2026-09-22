# CHAMELEON / COD10K-train contamination: detector and leaked-image list

**50 of 76 images (65.8%) in the CHAMELEON camouflaged-object dataset are
copies of images in the COD10K-train / CAMO training pool** -- 44 in COD10K-train
and 6 in CAMO. Two tiers: **41** same-dimension re-encodes, which the detector in
this bundle reproduces on its own, plus **9** rescaled or cropped copies confirmed
by warping each partner into the CHAMELEON frame and measuring the residual.

> **Reading the numbers.** `51` appears in older notes as the *checkable* count --
> CHAMELEON images having any same-dimension training candidate. That is a
> denominator, not a result. It is not the contamination count and never was.
> A pre-adjudication draft also reported `51 = 41+10`; one of those 10
> (`animal-7.jpg`) turned out to be a degenerate homography and is excluded.
> The full ledger is `rebuild/FINAL_AUDIT/CONTAMINATION_LEDGER.md`.

Any model trained on COD10K-train has therefore already seen those images.
A CHAMELEON evaluation column reported for such a model is not an independent
measurement.

## What is here

| File | What it is |
|---|---|
| `chameleon_contaminated.json` | the leaked-image list: every CHAMELEON filename that is a training re-encode, its training-pool partner, and the per-pair evidence |
| `detect_contamination.py` | the detector, standalone. Point it at any two image directories. **Reproduces tier A (41) only** -- the 9 geometric matches need `rebuild/FINAL_AUDIT/adjudicate.py` |
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
- Every count is a **lower bound**. 16 images have no partner at either tier and
  are reported `unchecked`; **unchecked is not clean**. Different photographs of one
  specimen, montages and heavy colour edits are not detected.
- The exact-hash **0 is measured against the training pool**. Across benchmarks it is
  not zero: `animal-17`, `animal-25` and `animal-60` are byte-identical to CAMO-250
  images. Those files are not in the training pool, so they do not enter the count --
  but CAMO-250 is the split this repository selects checkpoints on.
- No dataset images are redistributed here. The underlying photographs are
  third-party licensed; this bundle carries filenames, measurements and the tool.

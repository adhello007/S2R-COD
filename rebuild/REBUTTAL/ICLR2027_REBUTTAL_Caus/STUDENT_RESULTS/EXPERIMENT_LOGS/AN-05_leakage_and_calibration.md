# AN-05: leakage, oracle calibration and endpoint audit

**Status: VERIFIED.** Every split was re-hashed. Cross-split duplicates were found by an independent,
re-encode-tolerant detector, whose matches were checked by eye on a random sample. Every arm's label
exposure was classified. Code: `rebuild/CAUS/an05_split_audit.py`. Tables: `AN-05_split_audit.csv`,
`AN-05_cross_split_pairs.csv`, `AN-05_role_ledger.csv`, `AN-05_chameleon_crosscheck.csv`.

## 1. Split identities

Each split was hashed from the bytes on disk; the content digests are in `AN-05_split_audit.csv`.
Every primary input also matches E0's committed manifest file by file (`EXP-01_reuse_gate.csv`,
gate R3).

| Split | files | unique sha256 |
|---|---|---|
| target pool (COD10K-train 3040 + CAMO-train 1000, no masks on disk) | 4040 | 4038 |
| COD10K-test images / masks | 2026 / 2026 | 2026 / 2026 |
| NC4K images / masks | 4121 / 4121 | 4121 / 4121 |
| CAMO-250 (checkpoint selection) images / masks | 250 / 250 | 250 / 250 |
| HKU-IS raw / authors' pool / LAKE-RED renders | 4447 each | 4443 / 4447 / 4445 |

## 2. Cross-split overlap

**Method.** Exact pairs are found by sha256. Near-duplicates are found by a 64-bit dHash (Hamming
≤ 6) and confirmed when the mean absolute difference at 256×256 is below 8/255. Of the confirmed
pairs, 13 were checked by eye (a seeded random 10 plus 3 borderline), and every one was the same
photograph. The counts are **lower bounds**: heavy crops, flips and recolouring escape the detector.

| Overlap (unique images of the second split) | exact | + near-duplicate | committed D2 | affects |
|---|---|---|---|---|
| target pool ∩ **COD10K-test** | 7 | → **15** | 7 exact | unlabelled training images; identical in every arm |
| target pool ∩ **NC4K** | 0 | → **32** | 0 | unlabelled training images; identical in every arm (**new**) |
| target pool ∩ CAMO-250 | 0 | → 9 | 0 | selection split |
| COD10K-test ∩ CAMO-250 | 0 | → 7 | 0 | checkpoint selection touches 7 endpoint photographs; identical in every arm |
| COD10K-test ∩ NC4K | 0 | → 4 | — | endpoints not fully independent |
| HKU-IS ∩ NC4K / ∩ CAMO-250 | 0 | 1 / 2 | 1 (NC4K) | the HKU-IS image is in every arm's labelled base pool |
| LAKE-RED renders ∩ any endpoint | 0 | 0 | 0 | none |
| CHAMELEON ∩ target pool | — | **42** (41 Tier-A + `animal-54`) | 41 Tier-A + 9 Tier-B = 50 | CHAMELEON is not an endpoint; floor ≥ 51/76 |

**Arm dependence.** Three HKU-IS foregrounds whose photographs appear in CAMO-250 are selected as
renders by some arms (`5189`: CINV, CORACLE, OR-TOP10-SHUF, OR-TOP5 and quota-only OR-PROP-INV;
`6051`: CINV, OR-TOP10-SHUF, OR-TOP5; `6474`: C10, CINV, CORACLE, CSHUF, OR-PROP, OR-TOP10-SHUF,
B_s45 and the quota-only OR-PROP-SHUF and OR-PROP-INV). Each appears with a new background, and the overlap touches only CAMO-250
checkpoint selection, at ≤ 3 of 250 images. **Every overlap with COD10K-test or NC4K is identical
across arms**, so it can shift absolute levels but not the arm contrasts.

## 3. Oracle calibration: is there a disjoint calibration source?

- **The only labelled images inside the 75 target clusters that are disjoint from both endpoints** are
  the target pool's own images (COD10K-train and CAMO-train).
- **Their masks are not in the pre-rebuttal workspace.** `Dataset/Target/` holds images only. The one
  local copy of the official train masks (`Dataset/_download_ws4/`, created 2026-11-07) belongs to
  another reviewer's workstream and was deliberately not used.
- **Therefore** the EXP-01 oracle arms use the committed **endpoint-label** vector, the one CORACLE
  used. Every arm is tagged `oracle_score_source = endpoint-label-leaky` (the shuffles:
  `endpoint-label-leaky (shape only)`).
- **The leak can only favour the oracle arms.** A null is conservative, and a COD10K gain must be
  checked against NC4K, whose masks are read by no allocation. Section 2 shows NC4K and COD10K-test
  share at least 4 photographs and a domain. NC4K is therefore not label-coupled, but it is not fully
  independent either.
- **Not attempted:** a clean-calibration quota comparison. It would need the official train masks
  downloaded into this worktree (a new external download with its own licence check) plus CPU
  inference of the S2C model on 4,040 images. It was not run, so no claim is made about how a
  calibration-label oracle would have allocated.

## 4. Who reads which labels

From `AN-05_role_ledger.csv`:
- **Standard arms (B, C10, CSHUF, CINV).** Allocation reads target-side ES only (gate G1, re-run
  inside every EXP-01 pool gate through the committed functions). Training reads source masks and
  unlabelled target images. Checkpoint selection reads CAMO-250 masks. Endpoint masks are read only
  after training, for scoring.
- **Oracle arms (CORACLE, OR-PROP, OR-TOP10, OR-TOP5, and OR-TOP10-SHUF in shape only).** In addition,
  COD10K-test masks set the quotas. COD10K-test is therefore **not an unbiased endpoint** for any of
  them.
- **CHAMELEON** is read by nothing.

No modern detector or new generator was introduced, so there is no pretraining-leakage question to
audit for EXP-02 or EXP-03. The one candidate examined, CTF-Net, ships weights trained on this study's
target-pool masks (AN-04).

No data-flow figure was produced. The role ledger is the complete flow, and a figure would repeat it.

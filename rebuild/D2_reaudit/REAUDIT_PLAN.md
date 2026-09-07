# D2R — CHAMELEON contamination re-audit and elevation

> **Setup document. Approved before any code ran; nothing below is a measurement.** This is D2R's
> `<ID>.md` per `REBUILD_PLAN.md` §2.5 — scripts, directories read and written, steps, and
> thresholds declared in advance. Measured values will live in `results/REBUILD_LOG.txt` block
> `EXP D2R` and nowhere else until `D2R_RESULTS.md` cites them by log block. There is no separate
> `D2R.md`.
>
> Illustrative figures quoted from `EXP D2` are the **prior** package's committed values, present so
> the comparison targets are fixed in advance. They are records under test — never inputs, baselines
> or targets.

---

## Context

`EXP D2` (log block `2026-08-31T14:32:23+05:30`, HEAD `ddf42f8`, script committed at `17dfbbf`)
found that **41 of CHAMELEON's 76 images (53.9 %)** are re-encoded copies of images in
`Dataset/Target/Image`, the unlabeled target pool that training consumes. Evidence: identical
dimensions, `mean|diff| ≤ 6.0`, differing JPEG quantization tables in 41/41 pairs, and a **7.4×**
jump in sorted nearest-neighbour distances after exactly 41 images.

D2 itself declared the gap in its own coverage, at `D2_RESULTS.md` §5:

> **CHAMELEON is not checked against its own publication** — only against the copies on this disk.

An author-sourced CHAMELEON now exists at `Dataset/chameleon_new/{animals,masks}`. D2R closes that
gap and, separately, elevates the finding from a scoping side-note into a citable resource.

Two things found while planning change what the finding *is*, and both are load-bearing:

1. **The contamination is a property of public datasets, not of this repo.** Of the 41 training
   partners in the committed `rebuild/D2/out/d2_duplicate_pairs.csv`, **40 are `COD10K-CAM-*`**
   (public COD10K-train) and **1 is `camourflage_00836.jpg`** (CAMO). So the measurement is
   *CHAMELEON ∩ COD10K-train = 40/76*, which holds for **any** method trained on COD10K-train — not
   just S2R-COD.
2. **The repo never sanctioned CHAMELEON as a test set.** `README.md` mentions CHAMELEON exactly
   once, under *"Source (Synthetic): CAMO + NC4K + CHAMELEON (CNC)"*, and lists only COD10K-test
   under *"Test (Real)"*. `Dataset/Source/CNC/` — the README's own directory for it — does not exist
   on disk, while the undocumented `Dataset/Test/CHAMELEON/` does.
   `Experiments/REPRODUCE_TABLE1_v2.md` contains **zero** CHAMELEON mentions. It was **our**
   `REBUILD_PLAN.md` §3 that named CHAMELEON a "secondary endpoint" without checking the README.

So the framing is not "we found a bug in their evaluation." It is: **CHAMELEON cannot serve as an
independent endpoint for any COD10K-trained model, and here is the measurement** — plus a
self-correction that the rebuild adopted an endpoint its own README never sanctioned.

### Discipline contract this obeys

| Rule | Source | How D2R satisfies it |
|---|---|---|
| Nothing is a finding until a committed script produces it and writes a log block | `REBUILD_PLAN.md:20-22` | One script, one `EXP D2R` block, one commit |
| Every prior value compared, never overwritten | `rebuild/B1/b1_embedder_sweep.py:350` template | Every D2 CHAMELEON metric pinned as an `OLD CLAIM` line with MATCH/MISMATCH; both values reported |
| No `/tmp`, no archive, no fallback path | `rebuild/common.py:1-24`, `:97-103` | Reads only `Dataset/`, `Snapshot/`, committed `rebuild/D2/out/`. `grep -rn '/tmp/archive'` over the repo returns **nothing** today; D2R adds no such path |
| Trains nothing | `REBUILD_PLAN.md:205` | `TRAINS NO`. `s5r-b` runs *inference* from an existing checkpoint; no optimizer, no checkpoint written |
| Nothing under `Dataset/`/`Result/`/`Snapshot/` modified | `rebuild/D2/D2.md:146` | Asserted as threshold T20 |
| Thresholds declared before running | `REBUILD_PLAN.md` §2.5 | §"Declared thresholds" below, fixed at approval time |

---

## Deliverables and layout

```
rebuild/D2_reaudit/
  REAUDIT_PLAN.md            this file — setup, no measured values
  D2R_RESULTS.md             written after the run; every bolded figure traceable to EXP D2R
  CLEAN_PROTOCOL.md          Part 4 resource: which columns are safe to report
  d2r_reaudit.py             s0,s4r,s4br,s5r,s6r,s7r → writes the EXP D2R block
  d2r_export_pairs.py        visual export (mirrors d2_export_duplicates.py)
  detect_contamination.py    Part 4 standalone public tool (imports nothing from this repo)
  out/                       tracked small artifacts (see per-part sections)
  pairs/                     gitignored — copied images + pair figures + contact sheets
  preds/                     gitignored — s5r-b inference output
  release/                   anonymized submission bundle
```

**Authoritative command:**

```
LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_reaudit.py \
    --steps s0,s4r,s4br,s5r,s6r,s7r --splits full
```

Same interpreter as every prior block, so the `ENV` line matches
(`py3.12.3 torch2.11.0+cu128 cu12.8 timm1.0.28 numpy2.5.2 | 2x RTX PRO 6000 Blackwell | seed 0`).

### Prerequisite edits, called out because they touch shared files

1. **`rebuild/common.py` — two registry rows.** `ipath()` raises `KeyError('… add it to
   common.INPUTS')` by design, so the canonical set must be *declared*:
   ```python
   'chamnew':    dict(path='Dataset/chameleon_new/animals', n=76, repr='R1-full', pool=None),
   'chamnew_gt': dict(path='Dataset/chameleon_new/masks',   n=76, repr='mask',    pool=None),
   ```
   These are path declarations, not measurements, so they do not violate §0.2's "no measured value
   frozen into upstream code". **Side effect to accept knowingly:** `e0_regenerate.py:90` checks
   `n == spec['n']` over all of `INPUTS`, so a future E0 re-run will begin covering these two
   directories. That is desirable, and it is why `n=76` is asserted by `s0` in the same commit.
2. **`REBUILD_PLAN.md` §1 — one addendum row**, marked `added by D2R 2026-09-07`, not a silent edit.
   §1 is part of an approved Phase-0 deliverable; appending a dated row keeps the approval legible.
3. **`.gitignore` — one pattern.** `/rebuild/*/duplicates/` does **not** match
   `rebuild/D2_reaudit/pairs/`. Add:
   ```
   # D2R re-audit exports: copied dataset images, figures, inference output.
   # Regenerate with rebuild/D2_reaudit/d2r_export_pairs.py. Manifests ARE tracked, in out/.
   /rebuild/*/pairs/
   /rebuild/*/preds/
   ```

---

## PART 1 — Reconcile the two CHAMELEON copies (step `s0`)

Runs **first**, and Part 2's shape depends on its outcome.

### 1.1 Locate and count

Both copies exist; the on-disk test copy has not moved. Established by read-only listing during
planning, and re-asserted by `s0`:

| Path | Expect | Notes |
|---|---|---|
| `Dataset/Test/CHAMELEON/Imgs` | 76 `.jpg` | also `GT/` 76 `.png` (8-bit grey), `Edge/` 76 `.png` |
| `Dataset/chameleon_new/animals` | 76 `.jpg` | author-sourced; file mtimes 2015 |
| `Dataset/chameleon_new/masks` | 76 `.png` | 8-bit **RGBA**, named `mask-N.png` |

`s0` asserts `len(listing('cham')) == len(listing('chamnew')) == 76` and records both counts and
both directory digests via `C.dir_digest`.

### 1.2 Same set? — by content hash, not filename

Reuse D2's two hash levels verbatim (`d2_leakage_sweep.py:76-94`):

- `fhash = sha256(file bytes)`
- `phash = sha256(str(a.shape) + a.tobytes())` on `Image.open(p).convert('RGB')`

Then compute, **as sets over hashes, independent of filenames**:

- `|fhash(cham) ∩ fhash(chamnew)|` and `|phash(cham) ∩ phash(chamnew)|`
- symmetric differences, listed by member
- separately, and only as a descriptive cross-check: the filename join agreement

Per-file table → `out/d2r_reconcile.csv`:
`name, dims_cham, dims_chamnew, bytes_cham, bytes_chamnew, fhash_equal, phash_equal, qtable_equal`

**Prior, stated as a prior and explicitly not a finding:** read-only `ls -l` during planning showed
all 76 image filenames identical across the two copies and all 76 byte sizes matching pairwise
(e.g. `animal-11.jpg` = 892776 B in both), with identical 2015 mtimes. Outcome (a) is therefore
*expected*. Nothing is claimed until `s0` hashes.

### 1.3 Masks reconcile separately — and demonstrably do not match

The mask sides differ in name, channel count and bytes: `chameleon_new/masks/mask-10.png` is 7564 B
RGBA; `Dataset/Test/CHAMELEON/GT/animal-10.png` is 3384 B 8-bit grey. Pixel dimensions agree on the
samples inspected. So the image side and the mask side must be reconciled **independently**.

- Join rule, declared: integer `N` from `mask-N.png` ↔ `animal-N.png`. Assert the join is a
  bijection over 1…76.
- Normalisation rule, declared: for each mask, take the RGB luminance after compositing on black,
  binarise at `> C.THRESH` (127) — the repo's own convention (`common.py:111`). Report the alpha
  channel's occupancy separately, because an RGBA PNG whose alpha carries the mask would binarise
  wrongly under a luminance rule, and that must be measured rather than assumed.
- Report: per-mask IoU and exact-agreement count after normalisation, plus foreground fraction on
  both sides.
- **Pre-declared handling:** any disagreement is a *finding* — the repo's CHAMELEON GT is a
  non-canonical repackaging — and gets a `REVISION_TABLE.md` §1 row. It also decides which mask set
  Part 3's impact analysis uses: **canonical (`chamnew_gt`) always**, with the repo GT reported
  beside it.

### 1.4 Which copy did D2 measure?

Established from **committed artifacts**, not from disk state, so the re-audit is checked against
the baseline it is auditing. Three independent routes, first authoritative:

1. **Registry at the D2 commit.** `git show 17dfbbf:rebuild/common.py` → assert
   `INPUTS['cham']['path'] == 'Dataset/Test/CHAMELEON/Imgs'`. `17dfbbf` is the commit containing
   `rebuild/D2/`; `ddf42f8` in the block header is HEAD at run time, which is the E0 commit — that
   distinction is recorded so nobody chases the wrong tree.
2. **Size corroboration.** `d2_duplicate_pairs.csv`'s `endpoint_kb` column against measured sizes in
   both copies.
3. **Dimension corroboration.** The same CSV's `dims` column against measured dims in both copies.

Also recorded, as weak corroboration only: `Dataset/chameleon_new/` directories were created
2026-09-07, after D2 ran on 2026-08-31, so D2 *could not* have read it. Directory mtimes are
mutable, so this never carries the assertion — route 1 does.

### 1.5 The three outcomes, with numeric boundaries fixed now

| Outcome | Boundary, declared before running | Handling |
|---|---|---|
| **(a) pixel-identical** | `\|phash ∩\| == 76` and both counts `== 76` | D2's finding transfers directly. Part 2 still runs in full against `chamnew` as an independent instrument check; expected result is exactly 41/76 |
| **(b) overlap but differ** | `1 ≤ \|phash ∩\| ≤ 75` | Report the overlap and both symmetric differences; run Part 2 on **both** copies and report two columns side by side. The canonical column is the headline |
| **(c) substantially different** | `\|phash ∩\| == 0`, or counts differ | Itself a finding — the repo shipped a non-canonical CHAMELEON. New `REVISION_TABLE.md` §1 row. Only the canonical numbers are reportable |
| **(d) on-disk copy absent** | `Dataset/Test/CHAMELEON/Imgs` missing | Declared for completeness; it is present. Would skip the both-way branch and note the loss of the baseline-side re-measurement |

Note that (a) at the **image** level is fully compatible with disagreement at the **mask** level
(§1.3), and the plan expects exactly that combination.

**Artifacts:** `out/d2r_reconcile.json`, `out/d2r_reconcile.csv`.

---

## PART 2 — Re-measure against the canonical set (steps `s4r`, `s4br`)

Method-identical to D2's authoritative `s4`/`s4b` so the comparison is apples-to-apples. Every
constant is copied, not re-chosen.

### 2.1 Split configuration

Local to `d2r_reaudit.py`; `common.SPLITS` is not touched.

```python
SPLITS_FULL = ['tgt','test','cham','chamnew','nc4k','val','raw','auth','local']   # authoritative
SPLITS_MIN  = ['tgt','cham','chamnew']                                            # fast iteration
ENDPOINTS   = ['test','cham','chamnew','nc4k','val']
TRAINING    = ['tgt','raw','auth','local']
```

`--splits full` is authoritative. Reason: the CHAMELEON-vs-training count is invariant to dropping
other splits (dimension groups are keyed on exact `(w,h)` and contamination is counted only over
endpoint↔training pairs), but D2's **global** metrics — 323 shortlisted, 132 confirmed, 49
endpoint↔training — are not. Running full is what makes *every* prior D2 value comparable rather
than only the CHAMELEON ones, which is the discipline requirement.

### 2.2 `s4r` — same-dimension exhaustive near-duplicate sweep

Constants, identical to `d2_leakage_sweep.py:204-207`:

```python
DESC = 32              # descriptor edge, greyscale, NOT contrast-normalised
SHORTLIST_RMS = 14.0   # generous descriptor cutoff; full-res verify decides
NEAR_TOL = 6.0
TOL_SWEEP = (1.0, 2.0, 3.0, 5.0, 6.0)
```

Pipeline, identical:

1. **Dimension grouping.** `Image.open(p).size` → `(w,h)` exact key. Descriptor:
   `np.asarray(im.convert('L').resize((32,32), Image.BILINEAR), dtype=np.float32).ravel()` —
   greyscale, BILINEAR, float32, **no contrast normalisation** (contrast normalisation is precisely
   what caused D2's own first-pass recall failure, `D2_RESULTS.md` §3.2: 10/76 instead of 41/76).
2. **Descriptor shortlist** within each group with >1 member, groups iterated largest-first, via
   Gram matrix:
   `sq = (X*X).sum(1)`; `d2 = sq[:,None] + sq[None,:] - 2*X@X.T`; `fill_diagonal(inf)`;
   `rms = sqrt(maximum(d2,0)/(32*32))`; take `triu(rms <= 14.0, k=1)`.
3. **Skip already-exact pairs** — `phash_of[a] == phash_of[b]` → `continue` (counted by s2/s3).
4. **Full-resolution verification of every survivor.** `np.asarray(...convert('RGB'), np.int16)`
   both sides, skip on shape mismatch, `d = |A-B|`, confirm iff `d.mean() <= tol`.
5. **Per-pair record**, same fields and same rounding: `mean_abs` (3dp), `p99_abs`
   (`int(percentile(d,99))`), `max_abs`, `frac_gt8` (5dp), `content_std` (`A.std()`, 1dp — side A
   only, as in D2).
6. **Contamination count** = distinct *endpoint image names* with ≥1 partner in `TRAINING`
   (set-based, so an image with three partners counts once).

**Tolerance sweep, not a single cutoff.** Reproduced exactly as D2 did it — a **post-hoc filter** on
the `tol=6.0` result set (`sub = [n for n in near if n['mean_abs'] <= tol]`), not five independent
sweeps. Reported for `chamnew` at 1.0/2.0/3.0/5.0/6.0 beside D2's 11/26/37/40/41.

**Artifacts:** `out/d2r_near_duplicates.csv`, `out/d2r_endpoint_contamination.json`.

### 2.3 JPEG quantization-table check on every confirmed pair

A copied file keeps its table; a re-encode cannot. Two **independent** extractions, because D2's
single method depends on PIL's `quantization` dict ordering:

1. **D2's method, for comparability.** `Image.open(path).quantization`, compared as
   `tuple(tuple(v) for v in q.values())` — `d2_export_duplicates.py:66-71,210`. PIL version
   recorded.
2. **Library-independent.** Raw JPEG **DQT** marker parse: scan for `0xFFDB` segments, read
   precision + table id + 64 coefficients in zigzag order, compare as a dict keyed by table id so
   ordering cannot matter.

Declared assertion: the two extractions return the **same differ/same verdict on every pair**, and
tables differ in 41/41 (or however many are confirmed). Per-pair table hashes are recorded so the
tables themselves are publishable evidence rather than a boolean. Both files are asserted to be
JPEG before the check runs; a non-JPEG side makes the pair `qtable_na`, never silently `differ`.

**Artifact:** `out/d2r_qtables.json`.

### 2.4 `s4br` — nearest-neighbour gap analysis

Identical to `step_endpoint_nn` (`d2_leakage_sweep.py:288-357`): same 32×32 descriptor and `by_dim`
grouping; per endpoint image, descriptor RMS against **same-dimension `TRAINING` members only**;
`order = np.argsort(rms)[:8]`; full-resolution verify all 8; keep the minimum `mean|diff|`. Images
with no same-dimension training candidate get `nearest = None` and are counted `n_unchecked` —
**unchecked is not clean**, and D2R restates that bound rather than quietly dropping it.

Gap rule, identical:

```python
for i in range(1, len(vals)):
    if vals[i] - vals[i-1] > 5 * max(vals[i-1], 1.0):
        gap = dict(below=vals[i-1], above=vals[i], n_below=i); break
```

**What confirms a data boundary vs a clean distribution, declared before running:**

- **Data boundary** iff a first gap exists with `above/below > 5` **and** `n_below` equals the
  `tol=6.0` matched count. The two instruments then agree on the same integer from independent
  directions — a count under a cutoff, and a discontinuity that owes nothing to that cutoff.
- **Clean/continuous** iff no gap is found, as for COD10K-test, NC4K and CAMO-val in D2. A
  contamination count without a gap reverts to a cutoff artifact and is *not* reportable as a
  boundary.
- Pre-declared expectation for the canonical set: gap at `n_below = 41`, `below ≈ 5.51`,
  `above ≈ 40.58`, ratio ≈ **7.4**.

**Sensitivity, added and labelled as an addition — never a substitute.** D2's top-8 shortlist means
`nearest` is a lower bound on nearest-ness: if the true nearest training image falls outside the
descriptor top-8, s4b misses it. D2R re-runs `s4br` at `TOPK ∈ {8, 32, all same-dimension}` and
reports all three. **The apples-to-apples comparison against D2 uses `TOPK = 8`.** Declared
assertion: the gap and `n_below` are stable across all three.

**Artifacts:** `out/d2r_endpoint_nearest.json`, `out/d2r_endpoint_nearest.csv`,
`out/d2r_topk_sensitivity.json`.

### 2.5 Visual export — what makes it undeniable

`d2r_export_pairs.py`, mirroring `d2_export_duplicates.py`: reads **s4br's**
`d2r_endpoint_nearest.csv` (not s4r's pair list — that is how D2 selected its 41, and the plan keeps
the same selection route), filters `endpoint == 'chamnew'` and `nearest <= 6.0`, sorts ascending by
`nearest`, and writes rank-ordered output. Constants kept: `AMPLIFY = 20` (at 1× the difference
panel looks black, which misleads in the opposite direction), `PANEL_H = 420`, `THUMB_H = 132`,
`PAD = 12`, `per_page = 14`.

```
rebuild/D2_reaudit/pairs/
  chameleon_canonical/<endpoint_image>      originals, names preserved
  target/<training_image>                   partners, names preserved
  pairs/NN_<stem>.png                       canonical CHAMELEON | training partner | amplified diff
  contact_sheet_N.png                       grids, 14 pairs/page
```

Per-pair manifest tracked at `out/d2r_duplicate_pairs.csv` — D2's exact header plus two columns:

```
rank,endpoint,endpoint_image,training_split,training_image,dims,mean_abs,p99_abs,max_abs,
frac_gt8,content_std,qtables_identical,endpoint_kb,training_kb,qtables_differ_dqt,partner_pool
```

`partner_pool ∈ {cod10k_train, camo}`, derived from the partner filename prefix — this column is
what turns the finding from repo-local into dataset-level.

### 2.6 Reporting

`out/d2r_comparison.csv` — one row per prior D2 value: `metric, d2_value, d2r_value, verdict`, with
`verdict ∈ {MATCH, MISMATCH}`. **Both values are always reported; nothing is overwritten.** The
headline row is `nearvdup_cham_images_matching_training`: canonical count and share beside D2's
`41/76 (53.9 %)`, with an explicit MATCH/MISMATCH.

---

## PART 3 — Honest scope and the "does a published paper use contaminated data" question

### 3.1 The mechanism, asserted from source rather than quoted (step `s6r`)

`D2_RESULTS.md` §3.0 cites *"`MyTrain.py:220,297` feeds `get_tarloader`"*. **That citation is
wrong**, and D2R corrects it by re-deriving the line numbers programmatically instead of trusting a
document. `MyTrain.py:220` is the `--source_root` help string; `:297` is the EMA teacher weight
copy. The mechanism D2 described is correct; only the line numbers are not — which is exactly the
class of defect the traceability rule exists to catch, so it is recorded, not silently fixed.

`s6r` parses source and asserts each of:

| Assertion | Expected | Why it matters |
|---|---|---|
| `get_tarloader(` call site in `MyTrain.py` | **line 317** | the real target-pool entry point |
| `--target_root` default | `./Dataset/Target/` (`MyTrain.py:222`) → reads `Dataset/Target/Image/` | names the directory whose pixels enter training |
| `get_tarloader` definition | `Src/utils/Dataloader.py:211` | — |
| its signature has **no** `gt_root` parameter | True | contrast `get_srcloader` (`:200`), which takes both |
| `TarDataset.__getitem__` returns 2 items, neither a mask | True | `(weak_image, strong_image)` only |
| `Dataset/Target/` contains no `GT/` subdirectory | True | there is no target label on disk to leak |
| `cls(...)` call site | `MyTrain.py:348` | where pseudo-labelling happens |
| `CLS.py` reads `target_root + 'Image/'` with `gt_root=None` | True | pseudo-labels are teacher CAMs, not ground truth |

**Statement licensed by those assertions, and no more:** test *pixels* enter training through the
unlabeled target pool and are pseudo-labelled by the teacher; CHAMELEON's ground-truth masks never
enter training. This is a **transductive-UDA protocol violation, not label leakage.** D2R will not
say "label leakage", "the model saw the answers", or "memorisation" anywhere.

**Artifact:** `out/d2r_mechanism.json`.

### 3.2 What it does and does not invalidate

Fixed wording, declared now:

- **Does:** the CHAMELEON evaluation column is unreliable for any model trained on COD10K-train,
  because 40 of its 76 images are in that training split. Reported as *"the CHAMELEON evaluation
  column is unreliable"*.
- **Does not:** invalidate a method whose COD10K-test and NC4K numbers are clean. D2R will **not**
  claim "S2R-COD is wrong."
- Recorded as supporting facts: `Result/**` contains no CHAMELEON predictions at all
  (`Result/SINet/S2C` is 2026 COD10K files; `Result/ABC/*` holds only `COD10K/` and `NC4K/`), and
  `MyTest.py:24` restricts `--dataset` to `['COD10K','NC4K']` with an in-code comment withdrawing
  CHAMELEON. The current code produces no CHAMELEON number.

### 3.3 Is CHAMELEON a sanctioned endpoint at all? (step `s6r`, continued)

Asserted, not asserted-by-prose:

| Assertion | Expected |
|---|---|
| `README.md` mentions CHAMELEON exactly once, inside the `Source (Synthetic)` / CNC bundle | True |
| `README.md` lists only COD10K-test under `Test (Real)` | True |
| `Dataset/Source/CNC/` — the README's own path for CNC — exists on disk | **False** |
| `Dataset/Test/CHAMELEON/` — absent from the README's directory block — exists on disk | **True** |
| `Experiments/REPRODUCE_TABLE1_v2.md` CHAMELEON mentions | **0** |
| `REBUILD_PLAN.md` §3 names CHAMELEON a secondary endpoint | True |

**Framing the evidence supports — the third option in the brief, with a fourth added.** CHAMELEON is
*source* material in this repo's documented design, not a test set. `Dataset/Test/CHAMELEON/` is an
undocumented local addition. Therefore:

- **Primary claim (dataset-level):** CHAMELEON cannot serve as an independent endpoint for
  COD10K-trained models — 40/76 of it is in COD10K-train. This is a fact about two public
  benchmarks and generalises past S2R-COD entirely.
- **Secondary claim (self-correction):** our own `REBUILD_PLAN.md` §3 adopted CHAMELEON as a
  secondary endpoint without checking that the README never sanctioned it. That is a D2R finding
  about the rebuild, and it belongs in `REVISION_TABLE.md` §2 beside R3 and R4.
- **Explicitly `UNVERIFIED`, and not claimable:** whether the *published* S2R-COD paper reports a
  CHAMELEON column anywhere. The PDF is not in this checkout; the reproduced Table 1 has no such
  column. D2R states this as unverified rather than guessing.
- **Flagged, not claimed:** under `--task C2C`, CNC (CAMO + NC4K + CHAMELEON) is the **source** pool
  (`MyTrain.py:245`), so for C2C, CHAMELEON is training data *by design*. If any C2C table reported
  CHAMELEON as a test set, that would be a direct source/test collision — strictly worse than what
  D2 found. Resolving it requires the paper, so D2R records the question and does not answer it.
- **Provenance direction, marked as inference:** CHAMELEON (2015) predates COD10K (2020), so the
  parsimonious reading is that COD10K-train absorbed CHAMELEON images during its construction. D2R
  measures only pool membership (40 COD10K-train + 1 CAMO) and labels the direction as inference
  from release chronology.

**Artifact:** `out/d2r_readme_scope.json`.

### 3.4 Measured impact — by how much the column misleads (step `s5r`)

Mirrors D2's `0.4761` percentile analysis for COD10K, which needs adapting because **no CHAMELEON
prediction maps exist anywhere on disk**. Two sub-steps; the model-free one is primary.

**`s5r-a` (primary, no model).** Per-image difficulty proxies from the **canonical** masks
(`chamnew_gt`, normalised per §1.3): object-area fraction, boundary complexity (boundary-pixel count
over object area), foreground/background luminance contrast, connected-component count. For each
proxy, the leaked-41's percentile within the clean-35, by D2's own percentile method
(`srt = np.sort(clean); pct = searchsorted(srt, d)/len(srt)`), plus Mann–Whitney U and an effect
size.

Declared reading, fixed now: mean percentile in **[0.25, 0.75]** ⇒ no difficulty skew;
**> 0.75** ⇒ the leaked images are easier, so the column is inflated; **< 0.25** ⇒ they are harder.

**Reported as a distribution, not a mean.** D2's `0.4761` is the mean of seven values spanning
0.028–0.913 — the mean hid the spread. D2R pre-commits to reporting min/quartiles/max and the full
per-image list for all 41, and to stating the spread in `D2R_RESULTS.md` alongside any mean.

**`s5r-b` (secondary, inference-only).** `Snapshot/SINet/S2C/Tea_epoch_best.pth` (SINet, 352×352)
over the 76 canonical images, scored per-image with the repo's own `Eval/metrics.py` (MAE and Sα)
against the canonical masks. Reports MAE(all 76), MAE(clean 35), MAE(leaked 41), the delta, and the
leaked set's percentile distribution within the clean 35. The inflation statement takes the fixed
form: *"the CHAMELEON column would read X; its clean subset reads Y; the column is inflated by
Y − X."*

Constraints on `s5r-b`, all declared:

- **`MyTest.py` is not modified.** It deliberately excludes CHAMELEON; D2R adds a local scorer
  instead of reopening a door the rebuild closed.
- Reuses `MyTest.py:41-48`'s checkpoint-load guard (`copied == len(state_dict)`, per
  `Explanations/CHECKPOINT_LOADING_BUG.md`) — a state_dict on the wrong CUDA device loads silently
  as a random network.
- Predictions go to gitignored `rebuild/D2_reaudit/preds/`. Nothing is written under `Result/`.
- **Labelled in the metric provenance and in `NOTES`: this is not a CHAMELEON endpoint result.** It
  exists only to quantify the inflation, and must never be lifted as a performance number.
- `TRAINS NO`. Inference from an existing checkpoint; no optimizer, no checkpoint written.

**If `s5r-a` and `s5r-b` disagree** — e.g. proxies show no skew but MAE does, or vice versa — both
are reported and the disagreement is the finding. Neither is adjusted to match the other.

The structural number is reported regardless of both: **41/76 = 53.9 % of the column is training
pixels**, which is a protocol fact that holds whatever the difficulty distribution turns out to be.

**Artifacts:** `out/d2r_difficulty.csv`, `out/d2r_impact.json`.

---

## PART 4 — Elevate to a first-class contribution

### 4.1 `detect_contamination.py` — standalone public detector

Takes **any two image directories**; imports nothing from this repo (stdlib + numpy + PIL only) and
contains no repo paths.

```
detect_contamination.py DIR_A DIR_B
    [--tol 6.0] [--shortlist-rms 14.0] [--desc 32] [--topk 8]
    [--json OUT.json] [--csv OUT.csv] [--pairs-dir DIR] [--workers N]
    [--self-test]
```

Implements the Part 2 method exactly: dimension grouping → 32×32 descriptor Gram-matrix shortlist →
full-resolution verification → both quantization-table extractions → nearest-neighbour gap report,
including the `n_unchecked` bound. Documented docstring stating what it detects (re-encodes, and
rescaled copies that land back on an identical dimension) and what it **cannot** (crops, flips,
colour shifts, rescaled copies that leave every dimension group, different photographs of one
specimen).

`--self-test` builds a synthetic known-answer case in a temp directory — write a JPEG at quality 95,
re-encode at 75, plus an unrelated image — and asserts the pair is detected with differing
quantization tables and the unrelated image is not. So a stranger can verify the tool without any of
this repo's data. **Declared threshold T16:** the tool passes `--self-test`, and running it on
`(Dataset/chameleon_new/animals, Dataset/Target/Image)` reproduces `s4r`'s canonical pair list
exactly. That makes the published tool's correctness a *logged* result rather than a claim.

### 4.2 `out/chameleon_contaminated.json` — the community resource

Content-addressed so a reader can confirm they hold the same sets, and free of any local path:

```json
{
  "schema_version": "1.0",
  "method": {"descriptor": "32x32 greyscale BILINEAR, no contrast normalisation",
             "shortlist_rms": 14.0, "tolerance_mean_abs": 6.0,
             "verification": "full-resolution mean|A-B| over RGB int16"},
  "reference_set": {"name": "CHAMELEON", "provenance": "author-sourced release",
                    "n": 76, "listing_sha256": "<agg digest>"},
  "training_set": {"name": "COD10K-train (+CAMO)", "n": 4040, "listing_sha256": "<agg digest>"},
  "contaminated": [
    {"chameleon_image": "animal-76.jpg",
     "partner": "COD10K-CAM-3-Flying-65-Owl-4516.jpg", "partner_pool": "cod10k_train",
     "dims": "829x466", "mean_abs": 0.603, "p99_abs": 4.0, "max_abs": 13,
     "frac_gt8": 3e-05, "content_std": 34.5,
     "qtables_differ": true, "qtables_differ_dqt": true}
  ],
  "counts": {"n_contaminated": 41, "share": 0.5395, "vs_cod10k_train": 40, "vs_camo": 1},
  "tolerance_sweep": {"1.0": 11, "2.0": 26, "3.0": 37, "5.0": 40, "6.0": 41},
  "nn_gap": {"n_below": 41, "below": 5.512, "above": 40.577, "ratio": 7.36},
  "unchecked": {"n": 25, "reason": "no same-dimension training candidate; unchecked is not clean"},
  "provenance": {"log_block": "EXP D2R", "commit": "<sha>", "timestamp": "<iso8601>"}
}
```

Illustrative values above are D2's committed figures, shown to fix the schema. **The file is written
from `s4r`/`s4br` output only** — no value is transcribed from a document.

### 4.3 `CLEAN_PROTOCOL.md` — which columns are safe to report

| Endpoint | Contamination vs training | Verification status | Verdict |
|---|---|---|---|
| COD10K-test | 2/2026 (0.1 %) | **on-disk copies; NOT author-verified** | Reportable, with the caveat stated |
| NC4K | 1/4121 (0.0 %) | **on-disk copies; NOT author-verified** | Reportable, with the caveat stated |
| **CHAMELEON** | **41/76 (53.9 %)** | **author-sourced, re-audited (D2R)** | **Not reportable** |
| CAMO | 4/250 (1.6 %) | on-disk; `Test/CAMO` deleted mid-audit | Never an endpoint — it is the checkpoint-selection set (`MyTrain.py:221`) |

Every row also carries its `n_unchecked` bound. The document states plainly that the COD10K-test and
NC4K rates were measured against on-disk copies and that **the same author-sourced re-audit is owed
for them** — the exact weakness this re-audit exists to close, left marked rather than papered over.
It also carries the transductive-UDA framing from §3.1 so a reader cannot mistake the claim for
label leakage.

### 4.4 Anonymizable for submission

A `release/` bundle built by a declared step, containing only: `detect_contamination.py`,
`chameleon_contaminated.json`, `CLEAN_PROTOCOL.md`, and a short README. **Declared threshold T17** —
a scan over every released byte finds none of:

`/home/`, the username, the author name, the author email, the git remote URL, the branch name,
`Dataset/`, `Snapshot/`, `Result/`, `rebuild/`, `LAKE-RED/.venv`, any absolute path.

Naming CHAMELEON, COD10K, CAMO, NC4K and S2R-COD is *retained* — those are public datasets and a
published paper, and citing them is normal scholarship, not deanonymisation.

**Redistribution, decided now:** the release ships **no dataset images**. Manifest, tool and
protocol only. The pair figures and contact sheets are for inspection by a human — the reader, the
professor, a reviewer — and for figure inclusion in the paper; they are not part of the
redistributable bundle, because the underlying photographs are third-party licensed. This is stated
in the release README.

---

## Declared thresholds — fixed at approval, before any code runs

| # | Condition | Verdict form |
|---|---|---|
| T1 | both CHAMELEON copies contain exactly 76 images | PASS/FAIL |
| T2 | the two copies are pixel-identical at `phash` level, 76/76 | PASS ⇒ outcome (a) |
| T3 | D2's measured copy identified from committed artifacts as `Dataset/Test/CHAMELEON/Imgs` | PASS/FAIL |
| T4 | canonical CHAMELEON contamination equals D2's 41/76 (no value overwritten — both reported) | MATCH/MISMATCH |
| T5 | quantization tables differ in every confirmed pair, **and** PIL and raw-DQT extractions agree pair-for-pair | PASS/FAIL |
| T6 | `s4br` gap exists with `above/below > 5` **and** `n_below` == the tol=6.0 matched count | PASS/FAIL |
| T7 | global s4 metrics reproduce D2 (323 shortlisted, 132 confirmed, 49 endpoint↔training) | MATCH/MISMATCH |
| T8 | tolerance sweep reproduces 11/26/37/40/41 | MATCH/MISMATCH |
| T9 | the canonical 41 names equal D2's committed name set in `d2_endpoint_contamination.json` | MATCH/MISMATCH |
| T10 | partner pool decomposition = 40 `cod10k_train` + 1 `camo` | NEW (no prior value) |
| T11 | gap and `n_below` stable across `TOPK ∈ {8,32,all}` | PASS/FAIL |
| T12 | every §3.1 source assertion holds, and `MyTrain.py:220,297` is recorded as a wrong citation | PASS/FAIL |
| T13 | every §3.3 README/disk assertion holds | PASS/FAIL |
| T14 | leaked-41 difficulty percentile reported with full distribution; skew declared iff mean outside [0.25,0.75] | PASS/FAIL |
| T15 | inference-based leaked-vs-clean split computed and the inflation stated numerically | PASS/FAIL |
| T16 | `detect_contamination.py` passes `--self-test` **and** reproduces `s4r`'s canonical pair list | PASS/FAIL |
| T17 | anonymization scan over `release/` clean against the declared pattern list | PASS/FAIL |
| T18 | every script fails loudly on a missing input; no `/tmp`, archive or scratchpad path read | PASS/FAIL |
| T19 | canonical vs repo CHAMELEON masks reconciled after normalisation | REPORTED; disagreement is a finding |
| T20 | nothing under `Dataset/`, `Result/`, `Snapshot/` modified | PASS/FAIL |

A threshold that fails because the data says so **stays failed**. D2's CHAMELEON threshold has
failed in all five of its blocks and was never relaxed; D2R inherits that stance.

---

## The `EXP D2R` block

Written by `C.log_block('D2R', …)` — the existing utility, so the format is identical by
construction. Appended to `results/REBUILD_LOG.txt`; the log is append-only.

```
================================================================================
<iso8601> | commit <sha> (dirty) | EXP D2R
CMD   LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_reaudit.py --steps s0,s4r,s4br,s5r,s6r,s7r --splits full
ENV   py3.12.3 torch2.11.0+cu128 cu12.8 timm1.0.28 numpy2.5.2 | 2x RTX PRO 6000 Blackwell | seed 0
REPR  decoded pixels (the only level that survives re-encoding) + canonical GT masks for s5r
METRICS
  cham_ondisk_n                        = <n>      (Dataset/Test/CHAMELEON/Imgs)
  chamnew_canonical_n                  = <n>      (Dataset/chameleon_new/animals, author-sourced)
  copies_identical_fhash               = <k>/76   (sha256 of file bytes, set-based)
  copies_identical_phash               = <k>/76   (decoded-RGB hash, set-based)
  copies_reconcile_outcome             = a|b|c|d  (boundaries declared in REAUDIT_PLAN.md 1.5)
  d2_measured_copy                     = <path>   (from git show 17dfbbf:rebuild/common.py)
  masks_canonical_vs_repo_identical    = <k>/76   (after declared normalisation)
  nearvdup_chamnew_matching_training   = <k>/76 (<p>%)   (distinct canonical images that are re-encodes)
  nearvdup_chamnew_at_tol_{1,2,3,5,6}  = <k>/76   (post-hoc filter on tol=6.0, as in D2)
  epNN_chamnew_checkable               = <k>/76   (has >=1 same-dimension training candidate)
  epNN_chamnew_unchecked               = <k>/76   (unchecked is NOT clean)
  epNN_chamnew_gap                     = <k> below <x>, next at <y>    (first >5x jump; ratio <r>)
  epNN_chamnew_gap_topk32 / _topkall   = <...>    (sensitivity; TOPK=8 is the comparison run)
  qtables_differ_PIL                   = <k>/<k>  (Image.quantization, D2's method)
  qtables_differ_DQT                   = <k>/<k>  (raw 0xFFDB marker parse, library-independent)
  qtable_methods_agree                 = True|False
  partners_in_cod10k_train             = <k>/<k>  (public COD10K-train split)
  partners_in_camo                     = <k>/<k>
  reconciles_with_D2                   = yes|no   (D2 measured cham 41/76, gap 41 below 5.51)
  get_tarloader_call_site              = MyTrain.py:<n>    (re-derived; D2_RESULTS.md cites 220,297)
  tarloader_reads_no_gt                = True     (get_tarloader has no gt_root parameter)
  target_dir_has_no_GT                 = True     (Dataset/Target/ has no GT/ subdirectory)
  readme_lists_cham_as_source_only     = True     (README.md, CNC bundle; never under Test (Real))
  dataset_source_CNC_exists            = False
  dataset_test_CHAMELEON_exists        = True     (undocumented local addition)
  reproduce_table1_cham_mentions       = 0        (Experiments/REPRODUCE_TABLE1_v2.md)
  leaked_difficulty_percentile_mean    = <x>      (model-free proxies; distribution also reported)
  leaked_difficulty_percentile_range   = <min>..<max>
  cham_MAE_all_76 / _clean35 / _leaked41 = <...>  (inference only; NOT a CHAMELEON endpoint result)
  cham_column_inflation                = <y-x>    (clean-subset MAE minus reported MAE)
  detector_selftest                    = PASS|FAIL
  detector_reproduces_s4r              = <k>/<k> pairs
  anonymization_scan_clean             = True|False
THRESHOLD  <T1 … T20, verbatim from the table above> -> PASS|FAIL
OLD CLAIM  D2 nearvdup_cham_images_matching_training = 41/76 (53.9%) -> MATCH|MISMATCH
OLD CLAIM  D2 epNN_cham_checkable = 51/76 -> MATCH|MISMATCH
OLD CLAIM  D2 epNN_cham_gap = 41 below 5.51, next at 40.58 -> MATCH|MISMATCH
OLD CLAIM  D2 nearvdup_cham_at_tol_{1,2,3,5,6} = 11|26|37|40|41 /76 -> MATCH|MISMATCH
OLD CLAIM  D2 near_dup_candidate_pairs_shortlisted = 323 -> MATCH|MISMATCH
OLD CLAIM  D2 near_duplicate_pairs_confirmed = 132 -> MATCH|MISMATCH
OLD CLAIM  D2 near_dup_endpoint_vs_training = 49 -> MATCH|MISMATCH
OLD CLAIM  D2 quantization tables differ in 41/41 pairs -> MATCH|MISMATCH
OLD CLAIM  D2 CHAMELEON_INTERSECT_target = 0 (exact hashing, correct at that level) -> MATCH|MISMATCH
OLD CLAIM  D2 CAMOval_INTERSECT_CHAMELEON = 3 -> MATCH|MISMATCH
OLD CLAIM  D2_RESULTS.md 3.0 cites MyTrain.py:220,297 for get_tarloader -> MISMATCH (correction)
OLD CLAIM  REBUILD_PLAN.md 3 names CHAMELEON a secondary endpoint -> MISMATCH (README never sanctioned it)
ARTIFACTS  <every out/ file, comma-joined, repo-relative>
TRAINS     NO
NOTES      <as below>
================================================================================
```

`NOTES` must carry, at minimum: that `s5r-b` is inference-only and is **not** a CHAMELEON endpoint
result; that the contamination is a lower bound (rescaled-out-of-group copies, crops, flips and
colour shifts are undetected, and `n_unchecked` images are unchecked, not clean); that the tolerance
sweep is a post-hoc filter on the tol=6.0 set; that `TOPK=8` is D2's shortlist and the sensitivity
runs bound its recall; that the provenance direction (COD10K absorbing CHAMELEON) is inference from
release chronology, not measurement; and that whether the published S2R-COD paper reports a
CHAMELEON column is `UNVERIFIED` because the PDF is not in this checkout.

### `REVISION_TABLE.md` additions

Appended after the run, each citing `EXP D2R`:

- **§1 (moved / new)** — the canonical-set contamination beside D2's 41/76; the mask
  non-reconciliation if §1.3 finds one; the partner-pool decomposition as the reframing from
  repo-local to dataset-level.
- **§2 (the rebuild's own corrections)** — `R19`: `D2_RESULTS.md` §3.0 cites `MyTrain.py:220,297`
  for `get_tarloader`; the real call site is `MyTrain.py:317`. Mechanism unaffected, citation wrong.
  `R20`: `REBUILD_PLAN.md` §3 adopted CHAMELEON as a secondary endpoint although `README.md` lists
  it only as CNC *source*. `R21`: `rebuild/D2/D2.md:38` records a stale command
  (`--steps s1,s2,s3,s4,s5,s6,s7`) omitting `s4b` and `s8`, both of which are in the authoritative
  block.
- **§3 (re-tested clean)** — every D2 CHAMELEON value that comes back MATCH.

---

## Verification

1. **Dry run, nothing logged.** `--no-log` on `d2r_reaudit.py` prints the block without writing;
   iterate there. The log is for accepted runs.
2. **Provenance gate.** Re-run with the old archive and any `/tmp` scratchpad made unreadable, and
   with `SCRATCH` unset. `grep -rn '/tmp\|_archive_stageC_old' rebuild/D2_reaudit/` must return
   nothing.
3. **Detector independence.** Run `detect_contamination.py --self-test` from a directory outside the
   repo, with `Dataset/` unreadable. Then run it on the two real directories and diff its pair list
   against `out/d2r_duplicate_pairs.csv` — must be identical (T16).
4. **Traceability gate.** Every bolded figure in `D2R_RESULTS.md` and every value in
   `chameleon_contaminated.json` must appear verbatim in the `EXP D2R` block. A number that cannot
   be traced is a defect, even when correct.
5. **Human inspection.** Open all contact sheets and both extreme-rank pair figures. The claim is
   "these are the same photographs"; a person must be able to see it.
6. **Immutability.** `git status --ignored Dataset/` unchanged; `Result/` and `Snapshot/` untouched
   (T20).
7. **Commit shape.** Exactly one commit carries the scripts, the `out/` artifacts, the log block,
   the `REVISION_TABLE.md` rows, the three prerequisite edits, and `D2R_RESULTS.md`.

---

## Closing three

**(a) Does `chameleon_new/` reconcile with the on-disk copy, or is both-way analysis needed?**
**Resolve this first — it is `s0`, and Part 2's shape depends on it.** On the image side the *prior*
strongly indicates it reconciles: all 76 filenames are identical across the two copies, all 76 byte
sizes match pairwise, and mtimes agree at 2015. That is a directory listing, not a hash, so it is a
prior and not a finding — but outcome (a) is expected, and D2's finding would then transfer
directly. **The mask side already demonstrably does not reconcile**: `chameleon_new/masks/mask-N.png`
is RGBA at ~7.5 KB against `Dataset/Test/CHAMELEON/GT/animal-N.png` at ~3.4 KB 8-bit grey, with a
different naming scheme, at the same pixel dimensions. So `Dataset/Test/CHAMELEON/GT` is a converted
repackaging, and **the mask side needs both-way analysis regardless of how the image side resolves**
— which matters because Part 3's impact analysis reads masks.

**(b) The single result that, if it came back differently, would most change the finding.**
**The `s4br` nearest-neighbour gap on the canonical set.** Not the count. The 41 is a
tolerance-conditional number — it is "how many pairs fall under 6.0", and on its own it is arguable.
The gap is what upgrades it into a claim about the data: a >5× discontinuity at exactly the same
integer, arrived at from a direction that owes nothing to the cutoff. If the canonical set returned a
continuous nearest-distance distribution with no gap — the profile COD10K-test, NC4K and CAMO-val all
show — then 41 would revert to a cutoff artifact and the headline would collapse to "some CHAMELEON
images resemble some training images", which is not publishable. Everything else that could move is
survivable: a count shifting by one or two changes a number, not the finding; and quantization tables
coming back *identical* on some pair would break the "re-encode" mechanism while making that pair a
**file copy**, i.e. stronger contamination, not weaker. The expectation is that the gap reproduces —
`chameleon_new` is very likely the same bytes D2 already measured — but that is the one result worth
watching.

**(c)** No code was executed and no `/tmp` or archive path was read while producing this plan:
planning used read-only inspection only — directory listings, `git log`/`git show` on committed
history, and reads of committed artifacts under `rebuild/D2/out/` — no measurement was computed, no
hash taken, and the only file written is this plan. `grep -rn '/tmp/archive'` over the repo returns
nothing, and D2R introduces no such path.

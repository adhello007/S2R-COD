# A3 — Scoping

**Status: SCOPING ONLY. Nothing was run. No A3 script was written. Trains nothing.**

Scope of this document: resolve the six open questions on A3 from committed artifacts, the
code, and the data on disk. Every answer carries its evidence as a log block, a `file:line`,
or a command over declared inputs. Where a committed artifact does not settle a question it
is marked **UNRESOLVED** or **needs-my-call** and the missing input is named. Nothing here is
inferred from a number I did not locate.

A3's claim under test: *"LAKE-RED's synthetic output sits far from the real target
distribution in embedding space."*

---

## 1. Prior A3 state — was it ever run, and how?

### ANSWER

**On the rebuild branch: never run.** `results/REBUILD_LOG.txt` contains **zero** `EXP A3`
blocks. There is no `rebuild/A3/` directory (this file creates it), no A3 script anywhere in
the tree, and no A3 path in `git ls-files`.

**Pre-rebuild: fully run, twice.** The old package's A3 was a complete, 563-line
implementation that already contained the entire control battery this scoping exercise was
asked to design. It was deleted wholesale by commit `96fe223` ("removal of the 41 old-package
paths") and is recoverable at `96fe223^`.

So **A3 is a port-and-repair, not a fresh build.** That is the single most consequential
finding in this document: the design work is largely done and committed, and what remains is
four specific repairs plus one new control.

**Both of the two questions asked about the old package resolve in the old package's favour:**

| Question | Answer | Old measured value |
|---|---|---|
| Was separability computed **with** the JPEG-recompression control? | **YES** | AUC **0.4117** at Q75 |
| Was recall computed with a **correct (non-sorted-filename)** split? | **YES** | ceiling **0.9405 / 0.9370** |

The sorted-filename bug was not merely fixed — it was **reproduced side by side as a labelled
control** (AUC **0.8888**, ceiling 0.8934/0.8710) so the defect is visible in the artifact
rather than described in prose. That is better practice than the rebuild requires.

**What actually "reversed" was the ceiling, not the finding.** The recall *share* moved
54% → 49.6% because the denominator was corrected (0.871 → 0.937). The coverage-loss
direction never reversed. Restating this correctly matters for Question 5.

**The AUC-0.999 claim was already self-demoted by the old A3.** Its own log block records
`THRESHOLD JPEG-75 alone reaches AUC > 0.85, so 0.999 is near-vacuous -> FAIL` and the note
*"THIS EXPERIMENT DEMOTES OUR OWN HEADLINE, which is why it is in the package."* The
truism concern in the brief is therefore not a new worry — it is a conclusion the prior work
already reached and recorded.

**Complete old A3 result set** (both blocks agree; second block adds reproduction commentary):

| Comparison | n | AUC | in-sample *d* |
|---|---|---|---|
| real target vs **LAKE-RED output** (local renders) | 4033 / 4447 | **0.9989** | 4.669 |
| real vs real, **RANDOM** split (true null) | 2016 / 2017 | **0.4781** | 0.660 |
| real target vs **raw HKU-IS** (two datasets) | 4033 / 4447 | **0.9831** | 3.275 |
| real vs same images **JPEG-75** | 4033 / 4033 | **0.4117** | 0.327 |
| real vs same images **darkened 20** | 4033 / 4033 | **0.3469** | 0.195 |
| real vs real, **SORTED-filename** split (the bug) | 2016 / 2017 | **0.8888** | 2.011 |

Precision / recall (Kynkäänniemi k=5): LAKE-RED **0.6906 / 0.4662**; raw HKU-IS
**0.6494 / 0.7461**; random-split ceiling **0.9405 / 0.9370**; sorted-split ceiling
0.8934 / 0.8710. Coverage delta gen − raw = **−0.2799 (−37.5% relative)**.

**Three old values did not reproduce**, and the old log grades them honestly: the null control
(0.4781 vs 0.5289 — both chance, a property of the draw); **JPEG-75 (0.4117 vs a claimed
0.9380 — an unexplained disagreement, source script never saved)**; and the real-side fg→bg
colour correlation (−0.191 vs −0.36, robust across n and weighting). The JPEG failure is the
important one: it cost R-f one of its two supports, so the near-vacuity argument came to rest
on the cross-dataset control alone.

### The four repairs A3 needs (all identified from committed artifacts)

1. **The authors' pool has never been probed.** Every old A3 probe and precision/recall number
   came from the *local* re-generation. `REBUILD_PLAN.md:427` names this as an outstanding gap
   in its own words. See Question 2.
2. **Cohen's *d* is computed in-sample and is not trustworthy as stated.** In the recovered
   `probe()`, the axis is fitted on `Xtr` but projected over **all** of `X`
   (`proj = X @ w / np.linalg.norm(w)`, with `a, b = proj[y == 0], proj[y == 1]`). C1 later
   *measured* that this estimator manufactures effects: with **no targeting at all** the
   in-sample *d* reaches **+1.4506**, while the held-out null sits at **−0.1328**. The old
   "4.67 SD" figure is therefore an unknown mixture of signal and fitting artefact. The AUC is
   unaffected — that one is correctly held out (`roc_auc_score(yte, p)`).
3. **One embedder, not three.** Old A3's probe/PR ran in `dinoL` only (with a *d*-only side
   check at `dinoB/224` and `dinoL/518`). The rebuild has three full caches.
4. **`n_target` changed, 4033 → 4040.** The old cache had the 7 leaked names pre-excluded; the
   rebuild's `tgt` cache is the unfiltered 4040. A3 must apply the exclusion itself. See Q2.

Plus one control the old A3 did not have: **NC4K** as a genuine cross-dataset real-vs-real
baseline (Question 3).

### EVIDENCE

- Zero rebuild A3 blocks — full block inventory of `results/REBUILD_LOG.txt`:
  ```
  3 | EXP ABC     4 | EXP B1      4 | EXP C1      1 | EXP D1
  5 | EXP D2      2 | EXP D2_NC4K 4 | EXP D2R     4 | EXP E0
  ```
  No `EXP A3`. `find rebuild/ -iname "*A3*"` → empty; `git ls-files | grep -i a3` → empty.
- Old A3 exists and was run twice — inventory of `results/STAGE_C_EVIDENCE_LOG.txt` at
  `96fe223^`: `1 EXP A1, 5 EXP A2, 2 EXP A3, 2 EXP B1, 3 EXP E0`. The two A3 blocks are
  timestamped `2026-08-27T19:54:36+05:30` and `19:56:10+05:30`, both at commit `9ac60f7`.
- Created by `fb893d5` ("evidence A3 experiment results"): `evidence/a3_appearance_signature.py`
  (563 lines) + `evidence/out/a3_{probe_table,precision_recall,pixel_stats,pixel_per_image}.csv`.
  Deleted by `96fe223`. Recover with `git show 96fe223^:evidence/a3_appearance_signature.py`.
- JPEG control present in the recovered script: `jpeg_loader` re-saves through `io.BytesIO` at
  `JPEG_QUALITY = 75`, embedded via `C.embed_cached('a3_tgt_jpeg75', ...)`.
- Correct random split present: `rng_split = C.rng(opt.seed + 1)`;
  `order = rng_split.permutation(len(tgt))`; the bug reproduced separately as
  `srt = np.argsort(names['tgt'])  # the ORIGINAL bug`. **A separate RNG stream per panel** —
  the script's own comment records that sharing one stream moved the null AUC 0.494 → 0.529
  purely by changing how many draws panel 1 consumed first.
- In-sample *d* defect: recovered `probe()` body, quoted above.
- C1's measurement of that defect: `rebuild/C1/C1_RESULTS.md:267-268` — held-out null
  `−0.1328` (range −0.2560 … −0.0109) vs in-sample null `+0.6991` (range +0.2144 … **+1.4506**),
  with the note *"Had `d_insample` been the headline, the entire REOPENS verdict would have
  been an artefact of fitting the direction to the noise it then measures."*
- Authors'-pool gap: `REBUILD_PLAN.md:427` — *"**A3 on the authors' pool.** Every old A3 number
  came from the local re-generation. The authors' pool — the one the model actually trained on
  — has never been probed."*
- A3 is already specified in the rebuild plan: `REBUILD_PLAN.md:261-269` (objective, inputs,
  method, representation R4, and a pre-declared vacuity threshold of **AUC 0.90** on any
  identity-preserving control). Old claims are pre-entered as rows A3.1–A3.8 at
  `REBUILD_PLAN.md:343-350`, awaiting the rebuild's measured column.

### STATUS

**Settled.** A3 is a port-and-repair of a recoverable, well-built prior experiment. No decision
needed on this question.

---

## 2. Which image sets are the correct comparison — the core design decision

### ANSWER — "LAKE-RED synthetic output": **report both pools. The reason is now non-arbitrary.**

| Pool | Path | n | E0 key | Role |
|---|---|---|---|---|
| **authors'** | `Dataset/Source/HKU-IS/Image` | 4447 | `auth` | **What `MyTrain.py` reads.** The base source pool in *every* ABC arm |
| **local** | `Dataset/LAKERED/output/HKU-IS/images` | 4447 | `local` | **What ABC actually added.** The 1000 extra images in arms A2/B/C |
| raw | `Dataset/Source/HKU-IS_raw/imgs` | 4447 | `raw` | The real photographs LAKE-RED starts *from* — not synthetic; the paired baseline |

The old brief's framing — "which one does training consume?" — has a clean answer
(**the authors' pool**), but it is the wrong question for the rebuild, because the two pools
play *two different load-bearing roles*:

- The **authors' pool** is what the model trains on, in all 24 ABC runs, as the 4447-image base.
- The **local renders** are what the ABC campaign *added* (1000 of them) to produce the null.
  A3 cannot claim to explain the ABC null while characterising only the pool ABC held constant.

So both are required, and the requirement is structural rather than a hedge. Reporting both is
also, for free, an **independent replication**: D2/D1/E0 established these are two genuinely
different samples of the same generator, not near-copies — **0 of 200 identical**, **mean
maxdiff 232.3 of 255**. The old A3 already exploited this in panel 1, where the fg→bg colour
sign flip landed at **+0.397** (local) and **+0.399** (authors') against **−0.191** for the real
photographs. Two independent generator runs agreeing to 0.002 while the real photos sit on the
other side of zero is a stronger claim than either run alone. Whatever A3 finds in the probe
and coverage panels should be held to the same standard.

**Which one should A3 characterise, if forced to pick one?** The **authors' pool**, because it is
what the published method consumes and therefore what a claim about "LAKE-RED's synthetic output"
means to a reader of the paper. Report local beside it as the replication. This is the reverse of
the old A3's choice, which is precisely the gap `REBUILD_PLAN.md:427` flags.

### ANSWER — "the real target distribution": **`tgt` = `Dataset/Target/Image`, 4040 — but it is NOT COD10K-train.**

This is the one place the brief's premise needs correcting, and it is the most damaging thing in
this document if it goes unaddressed.

`Dataset/Target/Image` is **3040 COD10K + 1000 CAMO**. It is a two-dataset mixture, not
"COD10K-train". Verified three ways: declared at `REBUILD_PLAN.md:123`, confirmed by filename
composition on disk (`3040` `COD10K-*` + `1000` `camourflage_*` = 4040), and consistent with the
E0 `tgt` cache at n=4040.

It *is* nonetheless the right set, for the stated reason: it is exactly what CSRDA adapts to.
ABC block #2 confirms **every run read the unfiltered 4040-image target set in both rounds**.
Using anything else would measure distance to a distribution the method never sees.

But the mixture cannot be reported as a monolith, because **the mixture is heterogeneous enough
to separate from itself at AUC 0.8888** — that is what the old "sorted-filename bug" actually
measured. Restated as a control rather than a defect, it says: *two sub-populations inside the
very target set we are adapting to separate at 0.889.* Against that, "real vs LAKE-RED at 0.999"
is a far weaker claim than it looks. See Question 3 — this is the strongest control available and
it costs nothing.

**Mandatory decomposition.** Run every comparison three times: against all **4040**, against the
**3040** COD10K-only subset, and against the **1000** CAMO-only subset. Lead with 4040 (fidelity
to the method) and report the two subsets as the decomposition that shows the finding is not an
artefact of mixing. Cost is zero — same cache, different row masks.

### ANSWER — the 7 D2-leaked names: **exclude, and the exclusion is mechanically ready.**

`rebuild/D2/out/d2_leaked_names.json` holds `target_names_to_exclude` (7 names) with method,
commit, endpoint-side partners and a scope statement. All **7 of 7 resolve** against
`names['tgt']`, so the filter is a name-set intersection, no fuzzy matching. 4040 − 7 = **4033**,
which is exactly the old A3's `n_a` — the old cache had them pre-excluded.

The exclusion's force is **conditional**, and A3 should say so rather than apply it reflexively:

- For **real-vs-synthetic**: immaterial. 7/4040 = 0.17%, and D2 measured that removing them moves
  MAE by −1.242e-05 (0.0167%) with no memorisation signature. Report the primary at **4040** with a
  **4033 sensitivity row**.
- For any comparison involving **COD10K-test**: **mandatory**. These 7 are exact duplicates of
  test images, so leaving them in puts identical rows on both sides of a real-vs-real control and
  biases it toward chance for the wrong reason.

Follow D2's own contract: **read the JSON, never type the names into a script.** D2_RESULTS §3.4
records that the old failure mode was a measured result frozen into upstream code, and that the
`Flying-53` transcription error could not have propagated because nothing downstream reads a name
typed into a document.

### ANSWER — the embedding representation: **R1-full whole images. Confirmed, and the wrong cache would be a serious error.**

The right caches are `rebuild/E0/cache/{embedder}_{set}_cls.npy` for
`set ∈ {tgt, auth, local, raw, test}` and `embedder ∈ {dinoL224, dinoL518, clipL224}`. All
**verified present at correct shape** — 21 caches, `repr=R1-full` for all five sets A3 needs.

**`cut` must not be used.** It is `R2-cutout-grey128`, and E0 measured that **82.24% of the
frame is one constant value** (128, flat, `np.unique == {128}` over n=50). A probe on cutouts
would separate on mask geometry, not appearance — it is a *selection* representation, which is
what B3/C1 use it for, and it is meaningless for a distribution comparison. The brief is right
to rule it out; this is the measurement that makes the ruling non-negotiable.

**Two choices A3 must declare rather than inherit silently:**

1. **Pooling.** Every cache stores `_cls` **and** `_pat` (patch-mean), both unnormalised
   (`rebuild/common.py:207-235`). Old A3 used CLS. Recommend CLS as primary with a patch-mean
   sensitivity row — it is free, and it guards against the finding being a property of one token.
2. **L2 normalisation.** Vectors are stored unnormalised by design ("L2-normalise at use time
   via `l2()`"). Old A3 normalised for both probe and precision/recall, and its own log flags
   this as *"our stated choice"* because the sources never said. Keep normalising, and keep
   saying so.

Embedder configs are declared, not reverse-engineered (`{tag}_embedder.json`): DINOv2
`vit_large_patch14_dinov2.lvd142m` at 224 and 518, CLIP `vit_large_patch14_clip_224.openai`,
all fp32, squash resize, each with its own mean/std. Two families, so no conclusion is
embedder-specific. Preprocessing sensitivity is bounded: cluster agreement squash-vs-aspect-crop
**0.946**, mean cosine **0.9308**.

Note the old A3 needed an **embedder gate** (re-embed 8 targets, require cos ≥ 0.999 against
cache) because the old preprocessing was never saved and had to be recovered by testing eight
candidate pipelines — near-misses were dangerous (Resize+CenterCrop 0.978, cv2.INTER_AREA 0.997).
**The rebuild does not need that gate**: the pipeline is declared in `rebuild/common.py` and
`C.embed` is the single entry point. This is a real simplification the rebuild has earned.

### EVIDENCE

- Training reads the authors' pool: `MyTrain.py:242` `opt.source_root = './Dataset/Source/HKU-IS/'`
  (S2C default), consumed at `MyTrain.py:312-313` as `image_root=opt.source_root + 'Image/'`,
  `gt_root=opt.source_root + 'GT/'`. Corroborated by `rebuild/D1/D1_RESULTS.md` per-pool table,
  which labels the authors' pool **"what `MyTrain.py` reads"**.
- ABC added the local renders: `rebuild/ABC/abc_common.py:51`
  `REN_IMG = 'Dataset/LAKERED/output/HKU-IS/images'`.
- ABC's base is the authors' pool: `rebuild/ABC/abc_build_pools.py:162`
  `('pool_size_A0', 4447, "base authors' pool only, unpadded")`; arm sizes A0 4447, A2/B/C 5447
  (`rebuild/ABC/ABC_RESULTS.md` §1.1).
- Pools are genuinely distinct: `rebuild/E0/E0_RESULTS.md` §1 s2 — "Pools identical: authors' vs
  local **0** of 200", "Mean maxdiff, authors' vs local **232.3** (of 255) — not near-copies".
  D1 adds per-pool uniqueness: raw 4443/4447, authors' 4447/4447, local 4445/4447.
- Path registry, all counts declared and asserted: `rebuild/common.py:49-65` (`INPUTS`), with
  `ipath()` at `:94` raising if a declared count does not match disk.
- Disk verification (this scoping run):
  `Target/Image 4040 · HKU-IS_raw/imgs 4447 · Source/HKU-IS/Image 4447 · LAKERED/output/HKU-IS/images 4447 · Test/COD10K/Imgs 2026 · Val/CAMO/Imgs 250 · Test/NC4K/Imgs 4121`.
- Target composition: `REBUILD_PLAN.md:123` — "Target domain (**3040 COD10K + 1000 CAMO**) |
  `Dataset/Target/Image` | 4040 jpg | `ae84685540e99138`". Filename composition on disk agrees.
- The 4040 set is what training adapts to: `rebuild/ABC/ABC_RESULTS.md` §1.2 — "every run read the
  unfiltered 4040-image target set in both rounds".
- Leaked names: `rebuild/D2/out/d2_leaked_names.json` — `n_target_excluded: 7`,
  `target_names_to_exclude` (7), `endpoint_side` (7, all `split: test`). All 7 resolve against
  `names['tgt']` (checked). Contract: `rebuild/D2/D2_RESULTS.md:251` §3.4 — "B3 and C1 **read this
  file**; they carry no name list." Immateriality: §3.5 — removing the 7 changes MAE by
  **−1.242e-05 (0.0167%)**, mean percentile 0.4761, "no memorisation signature".
- Cache inventory `rebuild/E0/out/e0_cache_summary.csv` — 21 rows, `n` matching `declared_n`
  everywhere; `tgt/raw/auth/test/val` = `R1-full`, `local` = `R3-render`, `cut` =
  `R2-cutout-grey128`. Shapes re-verified this run for all 3 × 7 caches.
- Cutout is 82% constant: `rebuild/E0/E0_RESULTS.md` §1 s2 — "Cutout background share of frame
  **0.8224** — 82.2% of the frame is one constant"; "Cutout background is flat grey **True**
  (n=50, `np.unique` == {128})".
- Pooling and normalisation: `rebuild/common.py:207-235` `embed()` returns
  `(cls, patchmean)`, docstring "Vectors are stored **UNNORMALISED**; L2-normalise at use time via
  `l2()`"; `l2()` at `:237`.
- Embedder declarations: `rebuild/E0/cache/{dinoL224,dinoL518,clipL224}_embedder.json`.
  Preprocessing sensitivity: `E0_RESULTS.md` §1 s3 — agreement **0.946**, mean cosine **0.9308**.

### STATUS

- Both synthetic pools, whole-image R1-full, three embedders, CLS primary — **settled**.
- The 7-name exclusion policy (4040 primary + 4033 sensitivity; mandatory whenever COD10K-test is
  a side) — **settled**.
- **Which target row is the headline — 4040 mixture, or the 3040 COD10K-only subset — needs
  your call.** My recommendation: **4040 as the headline**, because it is what the method adapts
  to and any other choice invites "you measured distance to a set your method never sees"; with
  the 3040/1000 decomposition **mandatory** in the same table, because the mixture separates from
  itself at 0.889 and a reviewer who notices that before you do can dismiss the whole experiment.
  I would not run A3 with only the 4040 row.

---

## 3. The controls that make separability meaningful

### ANSWER

The brief asks for two controls. There are **four** worth running, and the two most powerful are
**not** the two named — one is free and unmeasured, and one of the two named turns out not to bite.

#### Control A — the true null: real-vs-real random halves of `tgt`

Free from cache. Establishes that the protocol does not manufacture separation. Old value
**0.4781** — chance. Non-negotiable, and it is the control that licenses reading every other row.

#### Control B — in-set heterogeneity: the strongest control, free, and never cleanly measured

The target set is a 3040/1000 mixture, so it contains a real-vs-real comparison with **no
synthetic content at all** that nonetheless separates strongly. The old sorted-filename split
measured a version of this at **AUC 0.8888** — the same number the old log filed as a bug.

**The clean version has never been run.** I checked the actual sorted split: half A is **2020
COD10K**, half B is **1020 COD10K + 1000 CAMO**. It is not COD10K-vs-CAMO, and because COD10K
filenames are ordered taxonomically (`Aquatic → Terrestrial → Flying → Amphibian → Other`), the
0.8888 conflates *dataset* with *taxonomy*. A clean **COD10K (3040) vs CAMO (1000)** probe is free
from cache and is the single most informative control A3 can run: it is the separability of two
real datasets that are *both inside the target distribution the method adapts to*.

If real-vs-LAKE-RED does not clear this bar by a declared margin, A3 has no finding.

#### Control C — JPEG recompression: computable, and **it does not bite**

Computable exactly as the old A3 did it: `C.embed(items, loader=jpeg_loader)` where
`jpeg_loader` re-saves each image through `io.BytesIO` at the target quality. `C.embed`'s
`loader` argument is a plain callable (`rebuild/common.py:207`), so this needs no new code path.

- **Which real set:** `tgt` (the same 4040 images, so identity is preserved and the only change
  is the encoder).
- **What quality factor:** the old audit's Q75 gave **0.4117** — DINOv2 is essentially invariant
  to re-encoding, so this floor sits at chance and provides **no** discriminating power. The
  claimed source value of 0.9380 never reproduced and is untraceable.
- **Recommendation: sweep Q90/Q75/Q50/Q30 rather than pinning one.** A single Q is what left the
  old disagreement unresolvable, and a sweep converts "we picked 75" into "the floor stays at
  chance until quality 30", which is a much harder row to attack. Cost ~13 min of embedding.
- **Report it as a floor that fails to bite.** That is a legitimate and useful result: it says
  the separability is not an encoding artefact. It just cannot carry the vacuity argument.

The old A3's **darkening-20** control (**0.3469**) is in the same category and already produced a
retraction (R-e: the claim that background darkening drives the style axis is withdrawn — DINOv2
is invariant to a 20-level shift). Worth keeping as a second identity-preserving floor, ~3 min.

#### Control D — cross-dataset real-vs-real: **NC4K, and it needs fresh embedding**

| Candidate | n | In E0 cache? | Verdict |
|---|---|---|---|
| **NC4K** | 4121 | **NO** — needs embedding | **The right control.** Genuinely different real COD dataset, and **D2_NC4K proved 0 overlap with COD10K-train** at every level, so no leakage confound |
| COD10K-test | 2026 | yes (`test`) | Weak — same dataset, different split; expect near chance. Free, worth a row as a second null. **Must** drop the 7 leaked names |
| CAMO val | 250 | yes (`val`) | Do not use as cross-dataset. n=250 is small, and 1000 CAMO images are *inside* `tgt`. (The 250 val names are disjoint from the 1000 in `tgt` — checked, 0 overlap — but the *distribution* is not) |
| raw HKU-IS | 4447 | yes (`raw`) | **Keep, but relabel.** See below |

`Dataset/Test/NC4K/Imgs` is declared at `rebuild/common.py:65` (n=4121), verified at 4121 on disk
and hashed in E0's manifest (`agg=6d1f138926b7b1c0`), but **there is no NC4K feature cache** — the
E0 `EMBED_SETS` list does not include it (`rebuild/E0/e0_regenerate.py:49-57`). Embedding 4121
images × 3 embedders is ~3 min (Q6 cost table).

**The raw-HKU-IS row must be relabelled.** The old A3 called `tgt` vs `raw` "two ordinary
different datasets" and leaned the entire surviving vacuity argument on it (0.9831). That label is
wrong: raw HKU-IS is **LAKE-RED's own input**. It is not a generic cross-dataset baseline — it is
the **paired** baseline, and it is far more valuable as such. It answers the question that actually
matters: *does generation move its input toward the target, or away from it?* Old answer: away
(0.9831 → 0.9989). Mislabelling it as a generic control both overstates the vacuity argument and
throws away the best number in the experiment.

### The decision rule — and why it cannot be declared on AUC

**AUC is saturated and must not be the deciding metric.** The old numbers make this concrete:
real-vs-LAKE-RED **0.9989** against a cross-dataset baseline of **0.9831**. Any margin large
enough to be meaningful on an unbounded scale is impossible to express here — 0.9989 is already
only 0.0158 above the control, and the ceiling is 1.0. A rule of the form "exceeds the control by
a margin" is unstateable on AUC without either being trivially met or trivially unmeetable.

So: **declare the margin on unsaturated metrics; report AUC as description, never as the decision.**

**PRIMARY rule — the paired coverage delta.** This is the only quantity in A3 that is immune to
the truism, because it is a *within-content intervention*: same 4447 foregrounds, same masks, only
the background generated (D1 measured `raw_gt` and `local_msk` agreeing to five decimals,
**0.19132** both). Both sides are measured against the same target manifold, so no cross-dataset
confound exists by construction.

> **A3's coverage claim holds** iff `recall(gen) < recall(raw)` in **≥ 2 of 3** embedder spaces,
> for **both** synthetic pools, with the real-vs-real random-split ceiling reported in every cell.
> Declare the effect size threshold before running: **relative loss ≥ 15%**. (Old measured:
> −37.5%, so this is not a bar set to be cleared.)
>
> **If it fails:** "LAKE-RED does not measurably reduce coverage of the target manifold relative
> to its own input pool" — publishable, and it retires the coverage argument cleanly.

**SECONDARY rule — separability must exceed the in-set control on a *held-out* effect size.**

> Held-out Cohen's *d*(tgt, gen) must exceed held-out *d*(COD10K-3040, CAMO-1000) — Control B —
> by **≥ 1.0 SD**, in ≥ 2 of 3 embedder spaces, for both pools. Both terms use the **held-out**
> estimator; the in-sample one is disqualified by C1's measurement of it (Q1, repair 2).
>
> **If it fails:** "LAKE-RED's output is no further from the target distribution than two real
> camouflage datasets inside that same target distribution are from each other." That is the
> honest conclusion the brief asks to be reportable, and it must be pre-committed as such.

**TERTIARY, descriptive only, no threshold:** AUC for every comparison; identity-preserving
floors (JPEG sweep, darkening); the distributional distances of Question 4; the spread comparison.
These are reported beside the controls and interpreted, but they do not decide.

**One rule the brief implies that I would not adopt:** "exceeds *both* controls by a margin." The
JPEG floor sits at chance (0.41), so it is cleared automatically and clearing it means nothing.
Requiring a margin over a control that cannot bind is theatre. The binding controls are B (in-set
heterogeneity) and D (NC4K); the JPEG and darkening floors are reported as evidence that the
signal is not an encoding artefact, which is a different and weaker job.

Note that `REBUILD_PLAN.md:269` already carries a pre-declared threshold —
*"Vacuity if any identity-preserving control exceeds AUC 0.90. Coverage loss real if
recall(generated) < recall(raw_hkuis) on both pools and both embedders."* The coverage half is
what I am proposing to keep and sharpen (both pools, three embedders, an effect-size floor). The
vacuity half is now known not to fire, because the identity-preserving controls sit at chance —
so the plan's threshold as written would pass A3 for the wrong reason. That is the specific
reason a new rule must be declared rather than inherited.

### EVIDENCE

- JPEG control mechanics: recovered `evidence/a3_appearance_signature.py`, `jpeg_loader` using
  `io.BytesIO` + `im.save(buf, format='JPEG', quality=JPEG_QUALITY)`, `JPEG_QUALITY = 75`.
  Pluggable loader confirmed at `rebuild/common.py:207` — `embed(items, loader, tag=..., ...)`,
  with `loader(it)` called per item at `:224`.
- JPEG does not bite: old `EXP A3` block, `probe_auc_jpeg75 = 0.4117 (IDENTICAL images,
  recompressed)`; graded `THRESHOLD JPEG-75 alone reaches AUC > 0.85 ... -> FAIL`. Source's 0.9380
  logged `MISMATCH`, with "the source script was never saved, so the 0.9380 cannot be traced".
- Darkening retraction: same block, `probe_auc_darkened20 = 0.3469`; `REVISION ... R-e ~20-level
  darkening RETRACTED as the mechanism`.
- Sorted-split value: same block, `probe_auc_sorted_split_BUG = 0.8888`.
- Sorted-split composition (this scoping run, over `names['tgt']`): half A = **2020 COD10K**;
  half B = **1020 COD10K + 1000 CAMO**; boundary
  `COD10K-CAM-5-Other-69-Other-5066.jpg | camourflage_00001.jpg`. So the old log's description
  ("put COD10K on one side and CAMO on the other") is approximate — it is a mixed split, and the
  clean 3040-vs-1000 probe has never been computed.
- NC4K declared but not cached: `rebuild/common.py:65`
  `'nc4k': dict(path='Dataset/Test/NC4K/Imgs', n=4121, repr='R1-full', pool=None)`;
  `rebuild/E0/e0_regenerate.py:49-57` `EMBED_SETS` = `{tgt, raw, auth, local, cut, test, val}` —
  no `nc4k`. Hashed in E0 s1 (`nc4k n=4121 OK agg=6d1f138926b7b1c0`). 4121 verified on disk.
- NC4K is a clean control: `rebuild/D2_reaudit/CLEAN_PROTOCOL.md` — NC4K ∩ COD10K-train = **0** at
  file bytes, decoded pixels, and same-dimension near-duplicates at tolerance 1/2/3/5/6; **0**
  candidate pairs even shortlisted; closest approach mean|diff| **17.190** (2.87× the tolerance);
  nearest-neighbour gap "none — continuous". Commit `8a7a15d`.
- CAMO val vs target CAMO: 250 val names, **0** overlap with the 1000 `camourflage_*` in `tgt`
  (checked this run). Disjoint splits — but same source dataset, so not a cross-dataset control.
- Masks are shared between raw and local, so the coverage delta is paired:
  `rebuild/D1/D1_RESULTS.md` mask-polarity table — `raw_gt` **0.19132** and `local_msk`
  **0.19132**, "agree to five decimals — the output masks are the input masks re-inverted".
- AUC saturation: old block, `probe_auc_real_vs_lakered = 0.9989` vs
  `probe_auc_real_vs_raw_hkuis = 0.9831`.
- Held-out vs in-sample estimator: `rebuild/C1/C1_RESULTS.md:267-268` (quoted in Q1).
- Pre-declared A3 threshold as it stands: `REBUILD_PLAN.md:269`.
- The truism lesson C1 already paid for: `rebuild/C1/C1_RESULTS.md:161` — *"Cohen's d is a
  mean-shift measure along a single, fitted direction. In a 1024-dimensional space, any structured
  subset will separate from a random one along some direction"*; and `:230` — "C1's declared
  ceiling is not a targeting ceiling; it is a **concentration** ceiling."

### STATUS

- Controls A, B, C, D and the relabelling of the raw-HKU-IS row — **settled**.
- **The decision rule needs your call**, because it must be declared before running and it is
  yours to declare. Specifically: (i) the primary rule on the paired coverage delta with a **15%**
  relative-loss floor, and (ii) the secondary rule on held-out *d* against Control B with a
  **1.0 SD** margin. Both thresholds are my proposals; the old data suggests both are clearable
  (−37.5%, and *d* 4.67 vs 2.01 in-sample), but the held-out *d* values do not exist yet, so the
  1.0 SD margin is set blind. **That is the correct order — declare it blind, then measure.**
- Whether the "no more separable than trivial re-encoding" conclusion is pre-committed as
  publishable — **needs your call.** I recommend yes, and note the old A3 already did exactly this
  and was the better package for it.

---

## 4. Which distance/separability metrics

### ANSWER

Six metrics, all computable from the E0 caches with **no new dependencies**. Verified in the
project venv: `scipy 1.18.0` (with `linalg.sqrtm`), `sklearn 1.9.0`, `numpy 2.5.2`,
`torch 2.11.0+cu128`.

| # | Metric | Source | New deps | Controls beside it |
|---|---|---|---|---|
| 1 | **Linear-probe AUC**, held-out, stratified | `sklearn` | none | all of A–D |
| 2 | **Held-out Cohen's *d*** on the probe axis | `sklearn` + numpy | none | all of A–D |
| 3 | **Fréchet distance in embedder space** (FD-DINO / FD-CLIP) | `scipy.linalg.sqrtm` | none | all of A–D |
| 4 | **Polynomial-kernel MMD** (the KID estimator) | numpy, ~20 lines | none | all of A–D |
| 5 | **k-NN precision / recall** (Kynkäänniemi k=5) | `torch.cdist` | none | random-split ceiling |
| 6 | **Spread**: trace-cov, log-det, effective rank | reuse C1 | none | raw pool + target |

**On metric 2, the "4.35 SD"-style figure — it must be recomputed, not ported.** This is the
most important item in this section. The old **4.67** is an **in-sample** number (Q1, repair 2),
and C1 *measured* that the in-sample estimator reaches **+1.4506** with no real effect at all.
Porting 4.67 into the rebuild would import exactly the defect C1 exists to have caught. Fix:
project only the held-out rows (`proj = Xte @ w / ||w||`, split by `yte`) and reuse C1's held-out
convention so A3 and C1 are commensurable. Expect the held-out value to come in **below** 4.67 —
by how much is the measurement.

**On metric 3, name it correctly or a reviewer will reject it.** `pytorch_fid` and `cleanfid`
are **absent** (checked). `torchmetrics` is present but its FID wants InceptionV3 pool3 features,
which means a weights download and a fourth embedder that plays no other role in the package.
Computing the Fréchet formula on DINOv2/CLIP features is fine and standard practice — but it is
**not FID**, and must be labelled **FD-DINO / FD-CLIP** with the backbone stated. Calling it
"FID" would be straightforwardly wrong.

One caveat to state in the log, not discover later: FD needs a 1024×1024 covariance from
n≈4040–4447 samples. That is only ~4 samples per dimension, so the covariance is poorly
conditioned and the FD value will carry real estimation bias. This is *why* metric 4 matters —

**metric 4 (polynomial MMD / KID) is the better primary distributional distance here.** It is
unbiased, needs no covariance estimate, is ~20 lines of numpy, and its control baselines are
computed identically. Recommendation: **MMD as the primary distributional distance, FD reported
beside it** as the more familiar quantity, with the conditioning caveat attached.

**On metric 5, two incompatible definitions exist in this repo and A3 must pick one loudly.**

- Old A3's `precision_recall()` is the standard Kynkäänniemi form: `precision` = share of *fake*
  inside real's k-NN manifold; `recall` = share of *real* inside fake's manifold.
- `rebuild/C1/c1_variance_coverage.py:185` `coverage_stats()` computes something different —
  `recall_frac_of_arm_used` is the fraction of the *arm* that appears in some target image's
  k-NN, plus `mean_top1_sim` / `mean_topk_sim`.

These are not the same quantity and are not comparable. **Use the Kynkäänniemi form**, because it
is the standard, it is what the reversed claim was computed in, and it is what makes the old
numbers commensurable. Say explicitly in the log that C1's `coverage_stats` is a different measure
and was not used — otherwise a reader comparing A3's recall to C1's will conclude one of them is
wrong.

**On metric 6, reuse C1's code rather than reimplementing.**
`rebuild/C1/c1_variance_coverage.py:157` `spread_stats(A, R)` already returns `trace_cov`,
`logdet_top`, `eff_rank` and `mean_dist_to_own_mean` with ratios. Importing it gives A3 the
"is the synthetic pool narrower than the target?" comparison for free and in a form directly
comparable to C1's. Note C1's own experience: it *declared* its threshold on the trace ratio,
which failed at 1–2%, and reported effective rank **as an observation, not promoted to a
threshold**, because swapping in the agreeing metric after seeing the data is the exact move the
rebuild exists to prevent. **A3 should declare no threshold on spread at all** and report all
three descriptively.

**Not worth doing:** true InceptionV3 FID/KID (new weights, a fourth embedder, and it would sit
outside the package's DINO/CLIP story); a deep generative-metric library. Say in the log that
Inception-FID was considered and declined, so the absence is a choice rather than an oversight.

### EVIDENCE

- Dependency check (this scoping run, project venv `LAKE-RED/.venv/bin/python`):
  `scipy 1.18.0 · sklearn 1.9.0 · numpy 2.5.2 · torch 2.11.0+cu128`; `from scipy.linalg import
  sqrtm` → OK; `pytorch_fid` **False**, `cleanfid` **False**, `torchmetrics` True.
  `pyproject.toml` dependencies confirm `scikit-learn>=1.9.0`, `scipy>=1.18.0`, `torch>=2.11.0`
  and no FID package.
- Old probe implementation (AUC held out, *d* not): recovered
  `evidence/a3_appearance_signature.py`, `probe()` — `roc_auc_score(yte, p)` but
  `proj = X @ w / np.linalg.norm(w)` over all of `X`.
- Why in-sample *d* is disqualified: `rebuild/C1/C1_RESULTS.md:267-268`.
- Old precision/recall implementation: recovered `precision_recall()` — `torch.cdist`,
  `radii()` via `kthvalue(k)`, `PR_K = 5`, on `C.l2(...)` features.
- C1's different coverage definition: `rebuild/C1/c1_variance_coverage.py:185-206`
  (`coverage_stats`, docstring and `recall_frac_of_arm_used`).
- C1's spread implementation: `rebuild/C1/c1_variance_coverage.py:157-179` (`spread_stats`).
- C1's warning against post-hoc metric substitution: `rebuild/C1/C1_RESULTS.md` §8.4 — "A declared
  threshold was wrong and is reported as FAILED. The spread criterion was declared on the trace
  ratio, which fails at 1–2%. Effective rank agrees with the conclusion, and is reported **as an
  observation, not promoted to a threshold**, because swapping in the metric that agrees after
  seeing the data is exactly the move this rebuild exists to prevent."
- Old A3's own normalisation disclosure: `EXP A3` NOTES — "Precision/recall is computed on
  L2-normalised features; the sources did not state whether they normalised, so this is our
  stated choice."

### STATUS

**Settled**, with two recommendations I would not change without a reason: MMD as the primary
distributional distance (FD beside it, correctly named), and the Kynkäänniemi definition for
precision/recall. The only open item is cosmetic — whether to report FD at all given the
conditioning caveat. I would report it, labelled, because reviewers look for it.

---

## 5. The recall/coverage question — in scope, and reproducible?

### ANSWER

**Reproducible: yes, and more cheaply than the brief assumes — the correct-split version already
exists as a committed artifact.** The old A3 computed both the corrected random split and the
buggy sorted split in the same run and emitted both to
`evidence/out/a3_precision_recall.csv`. Re-running needs only the E0 caches plus the same ~40
lines of `torch.cdist`.

**The characterisation of the reversal in the brief needs one correction.** What reversed was the
**ceiling**, not the finding:

| | buggy sorted split | corrected random split |
|---|---|---|
| real-vs-real ceiling (prec / rec) | 0.8934 / 0.8710 | **0.9405 / 0.9370** |
| LAKE-RED recall share of ceiling | 54% | **49.6%** |

`recall(gen) = 0.4662` and `recall(raw) = 0.7461` are the *same* in both — they never depended on
the split, because only the ceiling did. **The direction of the coverage finding never reversed.**
That matters: the brief treats this finding as shaky because it "reversed once," but the
underlying measurement was stable and only its normalising denominator moved. A3 should say this
plainly, and should report the **raw delta** rather than the share, so no denominator is
load-bearing at all.

**In scope for A3: yes — keep it.** It is the only panel that survives the truism, it uses the
same embeddings and the same table as the probe panel, and separating it into its own experiment
would destroy the paired framing that is its entire defence. The old A3's own log reached the same
conclusion: *"THE RESULT THAT ACTUALLY MATTERS is panel 3."*

### On the apples-to-oranges concern — the brief's worry, addressed precisely

The concern as stated: raw HKU-IS is salient-object photography, LAKE-RED output is
camouflage-style renders, so comparing their recall of the target manifold compares two
different-genre sets and the comparison is not meaningful.

**In the form stated, the concern does not apply, and the reason is measurable rather than
rhetorical.** The comparison is a *paired within-content intervention*, not two independent sets:

1. **Same content.** The same 4447 foregrounds, in bijection. E0 verified the bijection at 4447
   base foreground files.
2. **Same masks.** D1 measured `raw_gt` and `local_msk` mean white fraction at **0.19132** each,
   agreeing to five decimals — the output masks are the input masks re-inverted.
3. **Same target manifold.** Both recalls are computed against the identical `tgt` embedding set,
   so there is no second manifold to be confounded by.
4. **Only the background differs.** E0 measured the `isReplace` compositing split directly:
   object-region error **6.245** mean abs (JPEG scale) vs background error **71.676** (generation
   scale), a **11.5×** ratio. D2 independently re-derived it from a different direction: in a
   clean pair the object region differs by **0.962** while the background differs by **41.667**.

So there is exactly one manipulated variable — the generated background — and both sides are
scored against one fixed manifold. That is a controlled intervention. It is also why this is the
one A3 number a "any two image sets separate" objection cannot touch: the two sets are not
arbitrary, they are the same images before and after the generator.

**The residual concern is real but different, and A3 must disclose it rather than dodge it.**
Recall of the target *manifold* is a **distributional** statement, not a **utility** statement. A
synthetic set can have low k-NN recall of COD10K+CAMO and still be useful supervision — coverage
of a manifold in DINOv2 space is not a bound on training value. That is the honest limit, and it
is precisely what the ABC campaign measured instead. A3 must not phrase the coverage loss as
"therefore it cannot help."

**Five disclosures that make the panel airtight:**

1. Frame it as a **paired within-content intervention**, citing the mask identity and the 11.5×
   object/background split, so the pairing is measured rather than asserted.
2. Report the **raw delta** `recall(gen) − recall(raw)` as the headline, not the share of ceiling
   — no denominator, nothing to reverse.
3. Report **both** synthetic pools (authors' *and* local). Two independent generator samples
   agreeing is the replication; only the local pool was ever measured.
4. Report the **random-split ceiling in every cell**, and the sorted-split ceiling beside it as a
   labelled control, exactly as the old A3 did.
5. State the **utility caveat** explicitly: this is a distributional measurement; ABC measured
   utility, and the two are linked by hypothesis, not by this experiment.

**One additional control worth adding, cheap:** `k` sensitivity. The old A3 pinned `k=5` and its
own limitations note flags it. Sweep `k ∈ {3, 5, 10, 20}` — free from cache, and it converts
"we chose 5" into "the direction holds across k", which is the same upgrade the JPEG sweep buys.

### EVIDENCE

- Committed corrected-split artifact: `evidence/out/a3_precision_recall.csv` at `96fe223^` —
  rows `LAKE-RED output 0.6906/0.4662`, `raw HKU-IS (pre-LAKE-RED) 0.6494/0.7461`,
  `real-vs-real ceiling (RANDOM split) 0.9405/0.9370`,
  `real-vs-real ceiling (SORTED split, the R-c bug) 0.8934/0.8710`; the `ceiling_used` column
  reads `random split` for both generated rows.
- Correct split mechanics: recovered script, `rng_split = C.rng(opt.seed + 1)`,
  `order = rng_split.permutation(len(tgt))`, `rand_a, rand_b = tgt[order[:half]], tgt[order[half:]]`.
- The reversal was the ceiling only: old `EXP A3` block —
  `REVISION ... R-c sorted-filename split bug (ceiling 0.893/0.871 -> corrected, both computed
  here); R-d recall share 54% -> recomputed`. `recall_lakered = 0.4662` and
  `recall_raw_hkuis = 0.7461` appear unchanged in both blocks.
- Headline delta: old block, `generation_recall_delta = -0.2799 (-37.5% relative)` (LAKE-RED
  output minus its own input pool); graded `THRESHOLD generation REDUCES recall vs its own input
  pool -> PASS`.
- Old A3's own verdict on scope: `EXP A3` NOTES — "THE RESULT THAT ACTUALLY MATTERS is panel 3,
  and it points the opposite way from the original framing: LAKE-RED does not merely have LIMITED
  coverage of the target manifold, it DESTROYS coverage its own input already had. Raw HKU-IS
  recall 0.746 -> LAKE-RED 0.466, a 37.5% relative loss, bought for +0.041 precision."
- Mask identity (the pairing): `rebuild/D1/D1_RESULTS.md` mask-polarity table — `raw_gt`
  **0.19132**, `local_msk` **0.19132**, "agree to five decimals".
- Foreground bijection: `rebuild/D1/D1_RESULTS.md` — "Base foreground files **4447**".
- Only the background is generated: `rebuild/E0/E0_RESULTS.md` §1 s2 — `isReplace` object-region
  error **6.245**, background error **71.676**, ratio **11.5×** (n=200). Independent
  re-derivation: `rebuild/D2/D2_RESULTS.md` §3.3 — "in s7's clean pair the **object** region
  differs by **0.962** while the background differs by **41.667**".
- `k=5` was a pinned choice: old `EXP A3` NOTES — "k=5 for the manifold estimate", listed under
  Limitations.

### STATUS

- Reproducible, and belongs in A3 rather than a separate experiment — **settled**.
- The five disclosures and the `k` sweep — **settled** (my recommendation; none of them costs
  anything).
- Nothing on this question needs your call.

---

## 6. Is A3 still load-bearing given the A/B/C null?

### ANSWER: **(a) a valuable explanatory pillar — but scoped to a half-day, not a day, and with one claim it must not make.**

#### What ABC actually established

Two nulls, not one. Both matter for reading A3:

| COD10K-test, Sα | 2σ̂ | Δ(B − A2) | Δ(C − B) | Δ(A0 → B) | Δ(A0 → C10) |
|---|---|---|---|---|---|
| SINet | 0.017933 | +0.005768 | **+0.005034** | +0.012497 | +0.017530 |
| SINet-v2 | 0.012257 | +0.002967 | **−0.000399** | +0.005923 | +0.005524 |

Every cell **within noise**, and both architectures agree on every verdict. So neither
*targeting* (C vs B) nor *adding synthetic data at all* (A0 → B) beat baseline by the
pre-registered rule.

#### Why the null needs a mechanism — the argument for A3

**ABC is underpowered against its own preregistration, and says so.** The measured `2σ̂` on the
primary endpoint is **0.017933**, larger than the whole MT→Ours gap of **0.0142** that the design
declared it could resolve half of. A null from a design that cannot resolve the effect size at
issue is weak evidence, and a reviewer will say exactly that. Worse for the null reading: the arm
means are **monotone increasing** in all four architecture × endpoint cells — SINet
0.700950 → 0.707679 → 0.713447 → 0.718481 — which is what a real-but-unresolvable positive effect
also looks like.

**A3 does not depend on power.** It is a deterministic computation over 4040 + 4447 fixed vectors.
There is no training variance, no seed spread, no σ̂. So A3 can carry weight in a place where ABC
structurally cannot, and that is the whole of its value: it converts "we measured nothing, though
we could not have measured much" into "here is a measured property of the synthetic distribution
that is consistent with there being little to measure."

**A3 is not redundant with anything else in the package.** C1 measured targeted-vs-random *within*
the synthetic pool and concluded the separation is **concentration, not targeting**. A3 measures
synthetic-vs-real — a different axis entirely. D1 measured foreground exhaustion. Nothing in the
rebuild currently measures the generator's output against the target distribution. That is A3's
territory and it is unoccupied.

**A3's unique contribution — the paired coverage delta.** No other experiment in the package makes
a statement about **the generator**, which is the paper's actual subject. Q5 establishes that
`recall(raw) → recall(gen)` is a controlled within-content intervention: same foregrounds, same
masks, one manipulated variable. "LAKE-RED destroys coverage its own input pool already had" is a
claim about LAKE-RED, is immune to the truism objection, and has no substitute.

#### The claim A3 must not make

**A3 does not explain the ABC null, and saying it does would be overreach.** Distributional
distance is not a bound on training utility. A distant or low-coverage synthetic set can still
improve a model — and the ABC arm means went *up*, monotonically, in every cell. If A3 is
written as "the synthetic distribution is far from real, therefore no amount of it closes the
gap," that is a non-sequitur, and it is the kind of non-sequitur this rebuild exists to catch.

The defensible claim is weaker and still worth having:

> The added synthetic data does not increase coverage of the target manifold — measured against
> its own input pool, it reduces it. That is **consistent with, and a candidate mechanism for**,
> the absence of a resolvable gain in ABC. It is not a demonstration that no gain exists, and
> ABC's own power statement is the reason it cannot be.

Note this is the same posture the old A3 took toward its own findings — *"A3 supports none of the
four load-bearing conclusions. It removes two claims we should not lean on"* — and the same
posture C1 was forced into. A3 written honestly is a pillar of explanation, not of proof.

#### Why (a) and not (b), and why a half-day

Against (b) nice-to-have: without A3, the paper's account of the ABC null is "we added synthetic
data and nothing measurable happened," with no characterisation of what was added. That is a
weak paper section and an obvious reviewer question. A3 answers it with measurements that already
mostly exist.

Against (c) redundant: nothing in E0/D1/D2/B1/C1/ABC measures synthetic-vs-real distance. Not
redundant on any axis I can find.

The honest deflation: **most of A3 is already built and committed.** The recoverable script has
the probe panel, all four identity-preserving and null controls, and the precision/recall panel
with the corrected split. The genuinely new content is: the authors' pool, three embedders, NC4K,
held-out *d*, and the target decomposition. That is a **half-day port-and-repair**, not a day of
fresh work — which improves the cost/benefit rather than weakening the case.

**If the deadline forces a cut**, the minimum viable A3 that still earns its place, in priority
order: (1) the paired coverage delta, both pools, three embedders — the finding; (2) Control B, the
in-set COD10K-vs-CAMO probe — the control without which (1) is unpublishable; (3) held-out *d*;
(4) the target decomposition. **Drop NC4K and the JPEG sweep first** — NC4K costs 3 minutes but
Control B is strictly the better control, and the JPEG floor is already known not to bite.

### EVIDENCE

- The ABC verdict: `rebuild/ABC/ABC_RESULTS.md` §1.3 — the σ̂ / Δ table quoted above; "**Every one
  of those is WITHIN NOISE**"; `architectures_agree_on_verdict = A0->A2 YES A0->B YES A0->C10 YES
  A2->B YES B->C10 YES`. Three `EXP ABC` blocks, commit `065dac6`.
- Underpowered against its own preregistration: `rebuild/ABC/ABC_RESULTS.md:8-12` — "**But the
  campaign is underpowered against its own pre-registered power statement** — the measured `2σ̂`
  on the primary endpoint is **0.017933**, larger than the whole MT→Ours gap of 0.0142 this design
  was declared able to resolve half of. Both halves of that sentence belong in any report of this
  result."
- Monotone arm means: `rebuild/ABC/ABC_RESULTS.md` §1.4 — SINet 0.700950 / 0.707679 / 0.713447 /
  0.718481; SINet-v2 0.689145 / 0.692102 / 0.695069 / 0.694669; "The arm ordering A0 < A2 < B ≈ C10
  is monotone in all four architecture × endpoint cells".
- What ABC added, and to what base: `rebuild/ABC/abc_common.py:51` (local renders);
  `rebuild/ABC/abc_build_pools.py:162` (base = authors' pool, 4447); pool sizes A0 4447, A2/B/C
  5447 (§1.1).
- C1 measures a different axis: `rebuild/C1/C1_RESULTS.md:43` — "is **concentration**, not
  **targeting**"; `:230` — "C1's declared ceiling is not a targeting ceiling; it is a
  concentration ceiling"; `:303` — "**That the separation is caused by targeting.** §8 shows it is
  not".
- A3's unique paired finding: old `EXP A3`, `generation_recall_delta = -0.2799 (-37.5% relative)`,
  with the pairing evidence in Q5.
- The posture to copy: old `EXP A3` NOTES — "A3 supports none of the four load-bearing conclusions.
  It removes two claims we should not lean on, and reframes the style gap as a CONSEQUENCE".
- C1 offers the same reconciliation as hypothesis-not-demonstration:
  `rebuild/C1/C1_RESULTS.md` §8.6 — "This is a **hypothesis the audit makes available**, not
  something it demonstrates."

### STATUS

**Needs your call** — it is a deadline judgement, not a fact. My assessment is **(a) a valuable
explanatory pillar, at half-day cost**, with the "does not explain the null" boundary written into
the log block from the start. The strongest single argument for running it is not that it explains
the null but that **ABC's own power statement means the null cannot stand alone**, and A3 is the
only measurement in the package that does not depend on power.

---

## Recommended A3 design

**Verdict: worth running.** A port-and-repair of a recoverable, well-controlled prior experiment,
with four repairs and one new control. Nothing about it trains.

### Sets

| Role | Set | n | Source |
|---|---|---|---|
| Real target (**headline**) | `tgt` | 4040 | E0 cache `R1-full` |
| Real target, decomposed | COD10K subset / CAMO subset | 3040 / 1000 | name mask on `tgt` |
| Real target, sensitivity | `tgt` minus 7 leaked | 4033 | + `d2_leaked_names.json` |
| **Synthetic, primary** | `auth` — what `MyTrain.py` reads | 4447 | E0 cache `R1-full` |
| **Synthetic, replication** | `local` — what ABC added | 4447 | E0 cache `R3-render` |
| Paired real baseline | `raw` — LAKE-RED's own input | 4447 | E0 cache `R1-full` |
| Cross-dataset control | `nc4k` | 4121 | **fresh embed, ~3 min** |
| Second null | `test` (with the 7 dropped) | 2026 | E0 cache `R1-full` |

Three embedder spaces throughout: `dinoL224`, `dinoL518`, `clipL224`. CLS pooling primary,
patch-mean as a sensitivity row, L2-normalised at use time and said so. **`cut` is not used.**

### Controls

| | Control | Cost | Role |
|---|---|---|---|
| A | real-vs-real random halves of `tgt` | free | true null; licenses every other row |
| **B** | **COD10K (3040) vs CAMO (1000)** — inside the target set | **free** | **the binding control** |
| B′ | the sorted-filename split, reproduced and labelled | free | the old defect, visible not described |
| C | JPEG sweep Q90/Q75/Q50/Q30 on `tgt` | ~13 min | identity-preserving floor (known not to bite) |
| C′ | darkening-20 on `tgt` | ~3 min | second identity-preserving floor |
| **D** | **`tgt` vs `nc4k`** | **~3 min** | genuine cross-dataset real-vs-real, leakage-free |
| D′ | `tgt`(4033) vs `test`(2026) | free | second null, same dataset different split |

### Metrics

Held-out probe AUC · **held-out** Cohen's *d* · polynomial-kernel MMD (primary distributional
distance) · FD-DINO / FD-CLIP (secondary, correctly named, conditioning caveat stated) ·
Kynkäänniemi k-NN precision/recall with `k ∈ {3,5,10,20}` · C1's `spread_stats` (descriptive, no
threshold). Every metric reported with all applicable controls in the same table.

### Decision rule — declared before running

> **PRIMARY (coverage).** The claim holds iff `recall(gen) < recall(raw)` in **≥ 2 of 3** embedder
> spaces for **both** synthetic pools, with **relative loss ≥ 15%**, and the random-split ceiling
> in every cell.
> *Failure is publishable:* "LAKE-RED does not measurably reduce coverage relative to its own
> input pool."
>
> **SECONDARY (separability).** Held-out *d*(tgt, gen) exceeds held-out *d*(COD10K, CAMO) —
> Control B — by **≥ 1.0 SD**, in ≥ 2 of 3 spaces, for both pools.
> *Failure is publishable, and must be pre-committed as such:* "LAKE-RED's output is no further
> from the target than two real camouflage datasets inside that target are from each other."
>
> **AUC is reported for every comparison and decides nothing** — it is saturated at 0.98–1.00
> across both the finding and its controls.
>
> **No threshold is declared on spread**, following C1's experience with post-hoc metric
> substitution.

### Cost — confirmed no-training, embedding-only

| Item | Cost |
|---|---|
| NC4K, 4121 × 3 embedders | ~3 min |
| JPEG sweep, 4040 × 3 × 4 qualities | ~13 min |
| Darkening, 4040 × 3 | ~3 min |
| Everything else | **reads the E0 cache — 0** |
| Probes: ~10 comparisons × 3 spaces, `LogisticRegression` on ≤ 8.5k × 1024 | minutes |
| MMD / FD / k-NN PR / spread | minutes |
| **Total compute** | **< 1 hour GPU** |
| **Total elapsed** incl. script, log block, results doc | **~half a day** |

**Confirmed: no optimizer runs, no checkpoint is written, no model is fine-tuned.** The only
model use is frozen-inference feature extraction through `C.embed`, and a logistic-regression
probe on frozen features is not model training. Timings are extrapolated from E0's measured s3
throughput: dinoL224 4447 imgs in **21.3s**, dinoL518 4040 in **112.7s**, per
`rebuild/E0/final4.log`.

---

## The one design choice that would most damage the finding if wrong

**The definition of "the real target distribution" — specifically, treating `Dataset/Target/Image`
as COD10K-train.**

It is **3040 COD10K + 1000 CAMO**. If A3 reports every separability number against that 4040-image
mixture and labels it "the real target distribution", then each number is inflated by the
mixture's own internal heterogeneity, and the inflation is not hypothetical — **a real-vs-real
split inside that very set already separates at AUC 0.8888**. A reviewer who notices the target is
a two-dataset mixture can retire the entire experiment in one sentence: *"your 0.999 is measured
against a set that separates from itself at 0.889."*

It is also the one error that would be invisible from inside the experiment. Every threshold would
pass, every control except B would look clean, the numbers would be internally consistent, and the
defect would surface only in review. The old A3 came within one label of this: it *computed* the
0.8888 and filed it as a bug in its own null control rather than recognising it as a measurement
of the target set's heterogeneity.

**The fix costs nothing and must be non-optional:** run every comparison against all three of
4040 / 3040 / 1000, make Control B (COD10K-vs-CAMO, cleanly split — never computed before) a
first-class row rather than a footnote, and state the mixture composition in the log block's
representation line. If A3 gets this one right, the controls that follow are straightforward. If
it gets this wrong, none of the rest matters.

---

## Open items requiring your decision

| # | Decision | My recommendation |
|---|---|---|
| 1 | Headline target row: 4040 mixture vs 3040 COD10K-only | **4040** (it is what CSRDA adapts to), with 3040/1000 decomposition **mandatory** in the same table |
| 2 | PRIMARY threshold: 15% relative coverage loss | Accept; old data measured −37.5%, so it is not set to be cleared |
| 3 | SECONDARY threshold: 1.0 SD held-out *d* margin over Control B | Accept, and note it is set **blind** — no held-out *d* exists yet. That is the correct order |
| 4 | Pre-commit the failure conclusions as publishable | **Yes.** The old A3 did exactly this and was the stronger package for it |
| 5 | Run A3 at all, against the deadline | **Yes — half a day**, on the ABC-power argument rather than the explains-the-null argument |
| 6 | If cut for time: drop NC4K and the JPEG sweep first | Accept; Control B is strictly the better control and is free |

Nothing in this document is UNRESOLVED. Every question resolved against a committed artifact, a
`file:line`, or a command over declared inputs.

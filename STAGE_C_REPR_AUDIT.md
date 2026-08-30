# Stage C image-representation audit

**Question under test:** which image representation does each of Stage C's two image-handling steps
actually use — (a) HKU-IS foreground cut out onto a blank background, (b) raw HKU-IS full source
image, (c) the repo-provided LAKE-RED output, or (d) a locally-generated LAKE-RED output?

**Method.** Every claim below was checked against the `.py` source that computes embeddings and does
selection, and against the arrays and image directories on disk. `EVIDENCE_APPROACH.md`,
`EVIDENCE_SCRIPTS.md`, `STAGE_C_MEASUREMENTS.md` and `STAGE_C_RED_TEAM_AUDIT.md` were treated as
documents under test, not as sources. Where a representation was in doubt, the cached vector was
re-derived from candidate image pipelines and compared by cosine — the results are exact (1.00000),
so the identifications are not inferential.

**Auditor's note on scope.** Two of the seven questions concern numbers (20.62 %, Cohen's *d* ≈ 0.10)
whose producing scripts do not exist in the tree. Those are marked UNVERIFIED and are **not**
reconstructed. One further finding is CONTRADICTED: a comment in `evidence/common.py` states the
embedding script was never saved, but it is present in the repo.

---

## Findings

| Question | Claim being tested | Verdict | Evidence (file:line + on-disk artifact) | Notes |
|---|---|---|---|---|
| **1. Target embedding — what is embedded** | Target images are embedded whole, not cropped or masked | **VERIFIED** | [embed_dino.py:44](evidence/artifacts/scripts_original/embed_dino.py#L44) `'tgt':(tgt_keep, lambda f: load_plain(f'{D}/Target/Image/{f}'))`; `load_plain` at [:17-18](evidence/artifacts/scripts_original/embed_dino.py#L17-L18) is `Image.open(p).convert('RGB').resize((RES,RES),BICUBIC)` — no mask, no crop, no aspect preservation | Squash-resize only. GT masks are never opened for the `tgt` job |
| **1b. Target directory** | Read from `Dataset/Target/Image` | **VERIFIED** | [embed_dino.py:35](evidence/artifacts/scripts_original/embed_dino.py#L35) `sorted(os.listdir(f'{D}/Target/Image'))`, `D=…/S2R-COD/Dataset` at [:3](evidence/artifacts/scripts_original/embed_dino.py#L3). On disk: `Dataset/Target/Image` = **4040** files (COD10K-CAM-* + camourflage_*) | Mixed COD10K + CAMO target domain |
| **1c. Target array shape / count** | 4033 rows after dropping 7 test-identical images | **VERIFIED** | Drop at [embed_dino.py:12-15,36](evidence/artifacts/scripts_original/embed_dino.py#L36) (`LEAK` set, 7 names). On disk `evidence/artifacts/dinoL518_tgt_cls.npy` = **(4033, 1024) float32**; also `dinoL_tgt_cls.npy` (4033,1024), `dinoB_tgt_cls.npy` (4033,768). `dinoL518_names.json['tgt']` = 4033 entries. 4040 − 7 = 4033 ✓ | Re-embedding `tgt` rows 0 and 4032 from `Dataset/Target/Image` as full images gives **cos = 1.00000** against the cache |
| **2. Selection ("nearest to centroid") — which representation** | The nearest-neighbour search embeds **(a)** the cut-out foreground on a blank background, *not* the LAKE-RED image | **VERIFIED** | Search: [analyze.py:32](evidence/artifacts/scripts_original/analyze.py#L32) `kept=np.array([int((land[np.argsort(-(Fc@C[c]))[:N]]==c).sum()) for c in range(k)])` — the ranking key is `Fc@C[c]`. `Fc` is bound at [analyze.py:11](evidence/artifacts/scripts_original/analyze.py#L11) `Ft,Fg,Fc,Fx=L('tgt'),L('gen'),L('cut'),L('tst')`, and `L` at [:10](evidence/artifacts/scripts_original/analyze.py#L10) loads `{TAG}_cut_{POOL}.npy`. Builder: [embed_dino.py:46](evidence/artifacts/scripts_original/embed_dino.py#L46) `'cut':(cut_stems, load_cutout)` → [embed_dino.py:19-23](evidence/artifacts/scripts_original/embed_dino.py#L19-L23), where **:22** is `a[np.asarray(gt)<127]=128  # object on neutral grey` | Background is **neutral grey 128**, not transparent/black. Source images `Dataset/Source/HKU-IS_raw/imgs/{stem}.png` (4447) + masks `…/gt/{stem}.png` (4447) |
| **2b. `cut` cache — decisive identification** | `dino*_cut_cls.npy` really holds grey-masked cutouts, not full scenes and not LAKE-RED output | **VERIFIED** | Re-embedded stems `0004`, `0005`, `1559`, `9057` (rows 0, 1, 1000, 4446) under three hypotheses and compared to `dinoL_cut_cls.npy`: **cutout = 1.00000 / 1.00000 / 1.00000 / 1.00000**; full raw scene = 0.90546 / 0.95709 / 0.92126 / **0.38649**; LAKE-RED output = 0.88911 / 0.88231 / 0.88495 / **0.58051** | Alternatives (b), (c)/(d) are decisively rejected. On disk `dinoL518_cut_cls.npy` = **(4447, 1024) float32** |
| **3. Landing measurement — which representation** | Acceptance embeds the finished LAKE-RED image | **VERIFIED** | [analyze.py:28](evidence/artifacts/scripts_original/analyze.py#L28) `land=(Fg@C.T).argmax(1)`; `Fg` = `{TAG}_gen_*.npy` ([analyze.py:11](evidence/artifacts/scripts_original/analyze.py#L11)). Builder: [embed_dino.py:45](evidence/artifacts/scripts_original/embed_dino.py#L45) `'gen':(gen_stems, lambda s: load_plain(f'{OUT}/images/SOD_{s}.jpg'))`, `OUT=f'{D}/LAKERED/output/HKU-IS'` at [:4](evidence/artifacts/scripts_original/embed_dino.py#L4) | Full generated image, unmasked. `dinoL518_gen_cls.npy` = **(4447, 1024) float32**; re-embed of rows 0/1/1000/4446 from `Dataset/LAKERED/output/HKU-IS/images/SOD_*.jpg` gives **cos = 1.00000** |
| **3b. Are those outputs (c) repo-shipped or (d) locally generated?** | They are **(d)**, generated on this machine | **VERIFIED** | Generator: [LAKE-RED/run_hkuis.sh:19-31](LAKE-RED/run_hkuis.sh#L19-L31) — stages inputs via `prepare_lakered_inputs.py`, then runs `test.py --dst_root "$OUT" --isReplace --seed 0 --shard_index i --shard_total 2`. On disk: `Dataset/LAKERED/output/HKU-IS/{images,masks}` = **4447 + 4447**, mtime 2026-08-21 13:19–14:28, plus `_errors_shard0.pkl`, `_errors_shard1.pkl` (the two shards), `_log/`, and run logs `LAKE-RED/logs/gen_shard{0,1}.log` (3.2 MB each). `Dataset/` is gitignored ([.gitignore:2](.gitignore#L2) `/Dataset*`) and `git ls-files Dataset/LAKERED` returns **0** tracked files. The LAKE-RED repo ships **no** pre-generated output set — `LAKE-RED/ckpt/` holds only `LAKERED.ckpt` (6.4 GB, Jun 2024) | Provenance chain is complete: `Dataset/LAKERED/input/HKU-IS/manifest_all.json` records `"staged": 4447` from `Source/HKU-IS_raw/{imgs,gt}` with the inverted mask convention |
| **4. Do selection and measurement use the SAME representation?** | They use **DIFFERENT** representations | **VERIFIED — CONFIRMED MISMATCH** | Both call sites are on adjacent lines. Selection: [analyze.py:32](evidence/artifacts/scripts_original/analyze.py#L32) ranks by `Fc@C[c]` → **(a)** grey-background cutout. Measurement: [analyze.py:28](evidence/artifacts/scripts_original/analyze.py#L28) `land=(Fg@C.T).argmax(1)` → **(d)** locally-generated LAKE-RED image. Line 32 then indexes `land` by the `Fc` ranking | The mismatch you asked about is real and is the definition of the acceptance metric: *"rank foregrounds by cutout-to-centroid cosine, then ask whether the finished render landed in that cluster."* See the prose section for why this is coherent but load-bearing |
| **4b. Index alignment across the mismatch** | `land[...]` indexed by a `Fc` ranking is valid only if `cut` and `gen` are row-aligned | **VERIFIED (no defect)** | [embed_dino.py:37-38](evidence/artifacts/scripts_original/embed_dino.py#L37-L38): `gen_stems` from `OUT/images` (strip `SOD_`), `cut_stems=[s for s in gen_stems if os.path.exists(f'{RAW}/imgs/{s}.png')]` — a filtered subset, which would silently misalign if anything were dropped. On disk **nothing is dropped**: both arrays are **4447** rows and `names.json['cut'] == names.json['gen']` evaluates **True** | The filter is a latent hazard, not an active bug: it happens to be a no-op because all 4447 output stems have a raw source. Any future partial generation would break line 32 silently |
| **5. Embedder — model, resolution, pooling** | DINOv2 ViT-L/14, `img_size` from argv, CLS token, fp16 | **VERIFIED** | [embed_dino.py:6-7](evidence/artifacts/scripts_original/embed_dino.py#L6-L7) `MODEL=sys.argv[1]; RES=int(sys.argv[2]); TAG=sys.argv[3]` → `timm.create_model(MODEL,pretrained=True,num_classes=0,img_size=RES).to(dev).eval().half()`. Pooling at [:31-32](evidence/artifacts/scripts_original/embed_dino.py#L31-L32): `f=m.forward_features(x)` then `cls.append(f[:,0]…)` (CLS) and `pat.append(f[:,1:].mean(1)…)` (patch-mean) — **both** are saved, per TAG. Normalisation at [:8-9,30](evidence/artifacts/scripts_original/embed_dino.py#L30) = ImageNet mean/std. Model id confirmed by reproduction: `vit_large_patch14_dinov2.lvd142m` at `img_size=224` reproduces `dinoL_*` at cos 1.00000 | Three caches exist: `dinoB` (ViT-B/14 @224, 768-d), `dinoL` (ViT-L/14 @224, 1024-d), `dinoL518` (ViT-L/14 @518, 1024-d). The headline uses **`dinoL518` / `cls`** |
| **5b. L2 normalisation** | Vectors are stored unnormalised and L2-normalised at use time | **VERIFIED** | Not applied in the embedder ([embed_dino.py:52](evidence/artifacts/scripts_original/embed_dino.py#L52) saves raw). Applied at use: [analyze.py:9-10](evidence/artifacts/scripts_original/analyze.py#L9-L10) `l2=lambda X: X/np.linalg.norm(X,axis=1,keepdims=True)` wrapping every load, and centroids re-normalised at [:27](evidence/artifacts/scripts_original/analyze.py#L27) `C=l2(km.cluster_centers_)`. Corroborated independently by [evidence/common.py:196](evidence/common.py#L196) "the cached vectors are NOT unit-norm (|f| ~ 47)" | So all three comparisons are cosine similarities |
| **5c. Same embedder for target, selection, measurement?** | Identical model, resolution and pooling across all three | **VERIFIED** | All five jobs (`tgt`,`gen`,`cut`,`tst`,`val`) are embedded in **one process, one model instance, one loop**: [embed_dino.py:43-53](evidence/artifacts/scripts_original/embed_dino.py#L43-L53). `analyze.py` then loads all of them with a single `TAG`/`POOL` pair ([:8,10-11](evidence/artifacts/scripts_original/analyze.py#L10-L11)) | No embedder mismatch within a run. **Caveat:** the only difference between the three representations is therefore the *image content*, which is exactly why the Q4 mismatch matters |
| **5d. Cross-experiment embedder consistency** | The evidence package uses the same embedder as the acceptance measurement | **CONTRADICTED (partially)** | The reusable path [evidence/common.py:216-220](evidence/common.py#L216-L220) `load_dinov2(variant='L', size=224…)` defaults to **L/224 in fp32 via `model(x)`**, and A3's artifacts are `a3_rawhkuis_L224_cls.npy` (4447,1024), `a3_tgt_{dark20,jpeg75}_L224_cls.npy` (4033,1024) — i.e. **L/224**. The acceptance headline is **L/518** | Not an error, but the two live at different resolutions. `common.py` guards the mix with `assert_embedder_matches_cache()` ([:267-294](evidence/common.py#L267-L294), tol 0.999), which is the right control |
| **5e. Doc claim: "the embedding script was never saved"** | — | **CONTRADICTED** | [evidence/common.py:179-180](evidence/common.py#L179-L180): *"The audits' feature caches were produced by a script that was never saved, so the preprocessing had to be reverse-engineered."* The script **is** in the repo: `evidence/artifacts/scripts_original/embed_dino.py` (55 lines), byte-identical to the scratchpad original (`diff` → IDENTICAL) | The reverse-engineering conclusion in that comment is nonetheless *correct* (squash-resize BICUBIC, ImageNet norm, CLS, unnormalised) — it matches `embed_dino.py` exactly. Only the "never saved" premise is stale. Worth fixing the comment |
| **6. K=4 / best-of-K executed?** | K=4 candidates per foreground are generated and the nearest-to-centroid kept | **UNVERIFIED — plan only** | K=4 appears **only** in a planning document: [evidence/sources/PRIOR_REVIEW.md:205](evidence/sources/PRIOR_REVIEW.md#L205) ("K=4 costs 6.4 h… ➡️ **K=4**"), [:303-307](evidence/sources/PRIOR_REVIEW.md#L303-L307), and step **O4** at [:325](evidence/sources/PRIOR_REVIEW.md#L325) *"Generate bank renders #1–3 (`--seed 1,2,3`)"*. It appears in **no** `.py` file and in **no** other document (`grep -rn "K=4\|best_of\|n_cand\|candidates"` over `*.py` → no hits outside `Eval/MyEval.py` comments). On disk there is exactly **one** render per foreground: one output dir, 4447 images, **4447 unique stems**, generated at a single seed ([run_hkuis.sh:28](LAKE-RED/run_hkuis.sh#L28) `--seed 0`). No `--seed 1,2,3` outputs exist | K on disk is **1**, not 4 |
| **6b. Were 20.62 % / 26.67 % computed from single pre-existing generations?** | Yes — not from a K=4 loop | **VERIFIED for 26.67 %** | `analyze.py` re-run against the rescued arrays reproduces the published table **exactly**: `dinoL518/cls k=20` deficient-12 = **26.6667 %**, k=50 = **11.4583 %**, k=100 = **3.9583 %**, saturated-4 k=20 = **41.25 %** — matching [STAGE_C_MEASUREMENTS.md:49](STAGE_C_MEASUREMENTS.md#L49) (26.67 / 11.46 / 3.96 / 29.8) and [:65](STAGE_C_MEASUREMENTS.md#L65) (41.2 %). The computation is [analyze.py:25-32,44](evidence/artifacts/scripts_original/analyze.py#L25-L32) with `N=40` and no generation step of any kind — `Fg` is a cache of images already on disk | The producing script is confirmed and its output is bit-consistent with the docs. `EVIDENCE_SCRIPTS.md:532-533` independently concedes this: *"Acceptance is measured on pre-existing generations, never inside a live loop with fresh sampling — in-loop acceptance is **UNVERIFIED**"* |
| **6c. The 20.62 % held-out figure** | Produced by a held-out split (rank on half A, measure on half B) | **UNVERIFIED — code does not exist** | The script named as its source, [`evidence/b3_targeting_acceptance.py`](EVIDENCE_SCRIPTS.md#L502) ([EVIDENCE_SCRIPTS.md:502,505](EVIDENCE_SCRIPTS.md#L502)), **does not exist**. Its declared output `evidence/out/b3_acceptance.csv` does not exist. `results/RESULTS_SUMMARY.md` lists **B3 as `pending`**, and `results/STAGE_C_EVIDENCE_LOG.txt` contains **no `EXP B3` block** (only E0×3, A1, A2×5, A3×2, B1×2). `analyze.py` contains no split whatsoever — no `train_test_split` on `Fc`/`Fg`, no half-A/half-B. `20.62` appears in **zero** `.py` files and **zero** artifacts; only in four markdown docs | The number has no executed provenance anywhere in the tree or in the surviving scratchpad. Not reconstructed here |
| **7. The random arm / Cohen's *d* ≈ 0.10** | Random arm = random selection over the same pre-existing pool (not re-generated foregrounds) | **UNVERIFIED — code does not exist** | The script named as its source, [`evidence/c1_targeted_vs_random.py`](EVIDENCE_SCRIPTS.md#L547) ([EVIDENCE_SCRIPTS.md:547,550](EVIDENCE_SCRIPTS.md#L547)), **does not exist**; nor does its declared output `evidence/out/c1_effect_size_sweep.csv`. **C1 is `pending`** in `results/RESULTS_SUMMARY.md`, with **no `EXP C1` block** in the log. No `.py` file computes a targeted-vs-random Cohen's *d* | The *design* in the run-book ([EVIDENCE_SCRIPTS.md:552-556](EVIDENCE_SCRIPTS.md#L552)) is *"take the nearest cutouts per funded cluster; compare against a uniform-random 1000 of 4447"* — i.e. **random selection over the same 4447 cutout embeddings, no re-generation**. Quoted as the stated intent; it is **not** verified, because nothing executes it |
| **7b. The one Cohen's *d* that IS executed** | — | **VERIFIED (different quantity)** | [analyze.py:23](evidence/artifacts/scripts_original/analyze.py#L23) computes a Cohen's *d* — but on the **linear-probe axis separating real-COD targets from LAKE-RED outputs** (`Ft` vs `Fg`, [:15-23](evidence/artifacts/scripts_original/analyze.py#L15-L23)), not targeted-vs-random. [evidence/a3_appearance_signature.py:197](evidence/a3_appearance_signature.py#L197) computes the same `cohens_d_probe_axis` quantity, and A3 **has** a log block | Do not confuse this *d* with the C1 *d* ≈ 0.10. They measure different things |
| **A. Provenance of the acceptance arrays** | The arrays used above are the audit originals, not re-derivations | **VERIFIED** | `analyze.py` as committed reads `SP=/tmp/claude-1000/…/56f76fa7-…/scratchpad` ([analyze.py:7](evidence/artifacts/scripts_original/analyze.py#L7)) — a volatile path. That scratchpad **still exists**, and all six scripts there are byte-identical to `evidence/artifacts/scripts_original/` (`diff` → IDENTICAL for `analyze.py`, `embed_dino.py`, `locked2.py`, `audit6.py`, `eval_seeds.py`, `m4_deficiency.py`). Arrays rescued to `evidence/artifacts/` by [evidence/e0_rescue.py](evidence/e0_rescue.py) | Reproduction above used the rescued copies in `evidence/artifacts/` and hit the published numbers exactly, so the rescue is faithful |
| **B. The InceptionV3 "0.00 % acceptance" arm** | Reproducible | **UNVERIFIED — producing code absent** | The arrays exist: `evidence/artifacts/cut.npy` **(2000, 2048)**, `gen.npy` **(2000, 2048)**, `f.npy` **(10513, 2048)**, `n.npy` `[4040 4447 2026]` (= the three concatenation sizes, 10513 total). But **no script in the repo or the scratchpad** references or produces them (`grep -rn "f\.npy\|gen\.npy\|cut\.npy\|n\.npy" --include=*.py` → no hits), there is **no** `names.json` for them, and no script anywhere saves 2048-d features (the repo's only InceptionV3 use is the torchmetrics FID scalar in `LAKE-RED/src/lake_red/eval_fid.py:76-77`, which caches nothing). `EVIDENCE_SCRIPTS.md:535-538` concedes "the original embedder script was never saved" | Which 2000 of the 4447 images populate `cut.npy`/`gen.npy` is **not recoverable** from the artifacts. Not reconstructed here |

---

## What representation each step actually uses

Stated as settled fact where verified above.

**The target side (clustering).** `Dataset/Target/Image` — 4040 mixed COD10K-CAM and CAMO
`camourflage_*` images — is read whole. Seven test-identical filenames are dropped in memory
([embed_dino.py:12-15,36](evidence/artifacts/scripts_original/embed_dino.py#L36)), leaving **4033**.
Each is squash-resized to `RES×RES` with BICUBIC and embedded; no mask is opened and no crop is taken.
The result is `dinoL518_tgt_cls.npy`, **(4033, 1024) float32**. k-means (k ∈ {20, 50, 100}, `n_init=10`,
`random_state=0`) runs on the L2-normalised version of this array
([analyze.py:27](evidence/artifacts/scripts_original/analyze.py#L27)), and its centroids are the
"intended clusters" everything else is measured against.

**The selection step uses (a) — the cut-out foreground on a blank background.** This is the
load-bearing finding and it is exact. `analyze.py:32` ranks foregrounds by `Fc@C[c]`, and `Fc` is the
`cut` cache. `cut` is built by `load_cutout`
([embed_dino.py:19-23](evidence/artifacts/scripts_original/embed_dino.py#L19-L23)): open
`Dataset/Source/HKU-IS_raw/imgs/{stem}.png`, open the matching GT from `…/gt/{stem}.png`, and set
**every pixel where the mask is < 127 to the constant value 128** — object preserved, background
replaced by flat neutral grey. So "blank background" is precise, with the caveat that the blank is
grey 128 rather than transparent or black. 4447 rows, `(4447, 1024) float32`. Re-embedding four
scattered rows reproduces the cache at **cos = 1.00000**, while the full raw scene gives 0.386–0.957
and the LAKE-RED output gives 0.581–0.889 for the same rows. Representations (b), (c) and (d) are
therefore excluded, not merely disfavoured.

**The measurement step uses (d) — a locally-generated LAKE-RED output.** `analyze.py:28` assigns
`land=(Fg@C.T).argmax(1)`, and `Fg` is the `gen` cache: full, unmasked reads of
`Dataset/LAKERED/output/HKU-IS/images/SOD_{stem}.jpg`
([embed_dino.py:45](evidence/artifacts/scripts_original/embed_dino.py#L45)). Those 4447 images were
produced **on this machine**, not shipped: `LAKE-RED/run_hkuis.sh` stages inverted-polarity masks and
runs `test.py` across two GPU shards at `--seed 0`; the two shard error-pickles, the 3.2 MB-per-shard
generation logs, and the 2026-08-21 13:19–14:28 mtimes are all present, `Dataset/` is gitignored and
untracked, and the LAKE-RED checkout contains no pre-generated output set at all — only
`ckpt/LAKERED.ckpt`. **The answer to (c)-vs-(d) is (d).**

**Selection and measurement are therefore on DIFFERENT representations, and this is by design.** The
acceptance metric reads: *rank the 4447 foregrounds by how close the grey-background cutout sits to a
target centroid, take the nearest N=40, then check whether each one's finished camouflaged render
landed in that same cluster.* Selection sees the object with its context deleted; measurement sees the
object plus the painted background. Both call sites are four lines apart
([analyze.py:28](evidence/artifacts/scripts_original/analyze.py#L28) and
[:32](evidence/artifacts/scripts_original/analyze.py#L32)) and share the same embedder, the same
`TAG`/`POOL`, and the same centroids — so the mismatch is purely in image content.

This is coherent as a *feasibility* proxy: at selection time in a real pipeline you would only have
the foreground, so ranking on the cutout is the honest thing to condition on. But it is load-bearing
in a way worth stating plainly. The 26.67 % is not "26.67 % of renders land where a render-based
selector aimed them" — it is "26.67 % of renders land where a *cutout*-based selector aimed them."
Note also that the plan specifies something different: `PRIOR_REVIEW.md` steps **O4/O5**
([:325](evidence/sources/PRIOR_REVIEW.md#L325)) call for embedding the *bank renders* and picking
best-of-K by render-to-centroid distance — i.e. selection on **(d)**, matching measurement. The
executed code selects on **(a)**. The plan's selection representation and the executed selection
representation are not the same one.

**Index alignment across the mismatch holds.** `analyze.py:32` cross-indexes `land` (a `gen`-ordered
array) with a ranking computed over `Fc` (a `cut`-ordered array). That is only valid if the two share
row order, and `cut_stems` is a *filtered* subset of `gen_stems`
([embed_dino.py:38](evidence/artifacts/scripts_original/embed_dino.py#L38)). On disk the filter is a
no-op — both arrays are 4447 rows and the two name lists compare equal — so there is no live defect.
It is a latent hazard: a partial or extended generation run would misalign the two silently, with no
error and a plausible-looking acceptance number.

**The embedder is uniform within a run.** DINOv2 ViT-L/14 (`vit_large_patch14_dinov2.lvd142m`, or
ViT-B/14 for the `dinoB` tag), `img_size` passed on the command line, fp16, ImageNet mean/std,
squash-resize BICUBIC with no aspect preservation and no centre crop. Both poolings are cached per
tag: **CLS token** (`f[:,0]`) and **patch-mean** (`f[:,1:].mean(1)`). Vectors are stored
**unnormalised** (‖f‖ ≈ 47) and L2-normalised at use time, so every comparison in `analyze.py` is a
cosine. Target, selection and measurement are embedded in one process against one model instance
([embed_dino.py:51-53](evidence/artifacts/scripts_original/embed_dino.py#L51-L53)) and consumed under
a single `TAG`/`POOL` — there is no embedder discrepancy between the three steps. The published
headline is `dinoL518` + `cls`, i.e. **ViT-L/14 at 518 px, CLS token**. One inconsistency to note
across *experiments*: the reusable helper in `evidence/common.py` defaults to **L/224 in fp32**, and
A3's artifacts are L/224, so the evidence package's newer work is at a different resolution from the
acceptance headline; `assert_embedder_matches_cache()` exists precisely to stop fresh and cached
vectors being mixed.

**K on disk is 1.** There is no best-of-K loop in any executed code and no multi-seed render bank.
4447 foregrounds, 4447 output images, 4447 unique stems, one seed. The 26.67 % figure was computed
from those single pre-existing generations by `analyze.py:32` — reproduced here exactly (26.6667 % at
k=20, 11.4583 % at k=50, 3.9583 % at k=100, 41.25 % saturated-4, all matching the published table).
K=4 exists only as a costing decision in a planning document.

---

## Could not be verified from executed code

Each item says **why**, per your instruction. None is reconstructed.

1. **The 20.62 % held-out acceptance figure.** — *The code does not exist.*
   `evidence/b3_targeting_acceptance.py`, named at `EVIDENCE_SCRIPTS.md:502`, is absent; its declared
   output `evidence/out/b3_acceptance.csv` is absent; B3 is `pending` in `results/RESULTS_SUMMARY.md`
   with no `EXP B3` block in `results/STAGE_C_EVIDENCE_LOG.txt`. `analyze.py` — the only acceptance
   code that has run — contains no half-A/half-B split. The string `20.62` occurs in no `.py` file and
   no artifact, only in markdown. The *in-sample* 26.67 % is fully verified; the held-out correction is
   not.

2. **The targeted-vs-random Cohen's *d* ≈ 0.10, and how the random arm is constructed.** — *The code
   does not exist.* `evidence/c1_targeted_vs_random.py` (`EVIDENCE_SCRIPTS.md:547`) and
   `evidence/out/c1_effect_size_sweep.csv` are both absent; C1 is `pending` with no `EXP C1` log block.
   The run-book *states* the random arm is a uniform-random 1000 drawn from the same 4447 cutout
   embeddings — random **selection** over pre-existing data, not re-generation — but nothing executes
   it, so the construction is UNVERIFIED, including the "not re-generated" part.

3. **K=4 / best-of-K generation and selection.** — *The code does not exist, and neither does the
   artifact.* K=4 is a costing decision in `evidence/sources/PRIOR_REVIEW.md:205` and a planned step
   `O4` at `:325`. No `.py` implements it; on disk there is exactly one render per foreground at one
   seed. `EVIDENCE_SCRIPTS.md:532-533` already concedes in-loop acceptance is UNVERIFIED.

4. **The InceptionV3 "0.00 % acceptance" arm, and the composition of `cut.npy` / `gen.npy` /
   `f.npy`.** — *The artifacts survive but the producing code is gone.* The arrays are on disk
   ((2000, 2048), (2000, 2048), (10513, 2048), with `n.npy = [4040 4447 2026]`) but no script in the
   repo **or** in the surviving scratchpad references them, no `names.json` accompanies them, and no script anywhere
   saves 2048-d features. The repo's only InceptionV3 use is the torchmetrics FID/KID scalar in
   `LAKE-RED/src/lake_red/eval_fid.py:76-77`, which caches no feature arrays; the two other
   `Inception` mentions are a rescue label (`evidence/e0_rescue.py:227`) and a metric-name string
   (`evidence/summarize_log.py:56`). Which 2000 images populate the 2000-row arrays, and whether they
   are cutouts or full scenes, cannot be established from what remains.

5. **B2, C2, C3, D1, D2.** — *The code does not exist.* Listed in
   `evidence/summarize_log.py:49-73` and specified in `EVIDENCE_SCRIPTS.md`, but no corresponding
   `.py` files exist and no log blocks have been written. Only E0, A1, A2, A3 and B1 have executed
   (`5 of 12 experiments complete`, per `results/RESULTS_SUMMARY.md`). Any number attributed to these
   is a run-book claim, not a measurement.

6. **The A3-vs-headline resolution difference** is *verified as a difference* (L/224 vs L/518) but
   whether the acceptance result is stable across that change is **UNVERIFIED** — *the code exists but
   has not been run at both settings for the acceptance metric.* `analyze.py` supports it directly
   (`TAG` is `sys.argv[1]`); the L/224 acceptance numbers reproduced above (6.4583 % at k=20) differ
   substantially from L/518's 26.67 %, so the headline is resolution-sensitive and that sensitivity is
   not addressed by any log block.

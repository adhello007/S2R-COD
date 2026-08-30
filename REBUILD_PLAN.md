# REBUILD_PLAN.md — Stage C evidence package, rebuilt from primary data

> **Phase 0 deliverable — approved 2026-08-30, commit 1 on branch
> `experiments/lakered/stageC/rebuild`.** Nothing below is a measurement. The "old claim" column
> exists **only** to feed `REVISION_TABLE.md`; it is never an input, a baseline, or a target.
> Measured values live in `results/REBUILD_LOG.txt` and nowhere else until `REBUILD_FINDINGS.md`
> cites them by log block.

---

## Context

The previous Stage C package wrote conclusions first and left scripts to catch up. Its own generated
summary records **5 of 12 experiments DONE** (E0, A1, A2, A3, B1) with B2, B3, C1, C2, C3, D1, D2 all
`pending` — while `EVIDENCE_SCRIPTS.md` quotes precise "Expected" values for all seven unrun ones
(*d* ≈ 0.10, 20.62 %, σ = 0.00356, 64×). Those have no producing script and no log block. A later
audit also found a silent representation slip: what the documents called "foreground cutouts" are
object-on-**grey-128** cutouts.

This rebuild re-derives every claim from code and data verified here. **No number enters any document
until a committed script has produced it and written it to the log.** Anything not computable is
`UNVERIFIED` — never a placeholder.

**One question, end to end:** why does targeting LAKE-RED generation at the model's weakest clusters
produce no meaningful accuracy gain, and why is Stage C therefore not a solid contribution?

### Decisions taken

| Decision | Effect |
|---|---|
| **Clean branch; prior work treated as garbage.** | Old files leave the tree (§0). Old *assumptions* are also discarded, not just old files — see §0.2, the substantive half of this. |
| **No retraining.** `Snapshot/SINet/S2C` is the final SINet model. | C3 restructured (no σ from primary data). B1's robustness axis moves from seeds to other primary trained models. |
| **Both HKU-IS pools, side by side.** | A3/B3/C1 report every number twice — authors' pool (what training read) and local re-generation. |
| **Port to COD10K paths.** | Scripts target `Dataset/Test/COD10K/{Imgs,GT}`; identity proof logged; no dataset path recreated. |

---

## §0 Clean slate

### 0.1 Branch and file removal

`git rev-parse --abbrev-ref HEAD` → **`experiments/lakered/stageC/30aug_26`** (the session-start
snapshot said `20aug_26`; it was stale). This is `20aug_26` + commit `14c6fdf` and carries the entire
old package.

| Step | Action |
|---|---|
| 1 | Cut `experiments/lakered/stageC/rebuild` from current HEAD |
| 2 | Commit 1: `REBUILD_PLAN.md` (this file) |
| 3 | Commit 2: `git rm -r` the **41 tracked** old paths — `EVIDENCE_*.md` (4), `STAGE_C_*.md` (3), `evidence/**` (tracked scripts, `out/`, `manifests/`, `sources/`), `results/{RESULTS_SUMMARY.md,RESULTS_SUMMARY.json,STAGE_C_EVIDENCE_LOG.txt}` |
| 4 | **Move, do not delete**, the untracked `evidence/artifacts/` (3.7 GB — rescued checkpoints, predictions, feature caches) to `../_archive_stageC_old/`, outside the repo. It is gitignored so `git rm` would leave it in the tree. |
| 5 | New scripts live in **`rebuild/`**, not `evidence/`, so no path is shared with the old package |

**Why move rather than delete.** The archive holds ~3.4 GB of checkpoints and predictions from six
training runs that cannot be regenerated without the retraining you deferred. A second copy survives
in the old `/tmp` scratchpad (20 GB, still present) but `/tmp` is volatile. Moving is reversible and
costs nothing; deleting is not and could destroy the only durable copy. **This is the one step I want
confirmed** — say the word and it becomes a delete instead.

After step 4 the working tree contains **zero** old evidence. Old claims survive only in git history
at `14c6fdf` and in §4 of this file.

### 0.2 Inherited assumptions being discarded — the part that matters

"Treat the previous experiments and their assumptions as garbage" disqualifies more than files. The
old package's numbers rest on constants nobody justified. Copying them would silently inherit its
design even with every file deleted. Each is now either re-derived by measurement or swept.

| Old constant | Where it mattered | Rebuild's treatment |
|---|---|---|
| `k ∈ {20,50,100}` clusters | every clustered result | **Re-derived.** Choose k by an independent criterion (silhouette + bootstrap cluster stability); report the full sweep and the verdict's sensitivity to k |
| `N = 40` nearest per cluster | the acceptance headline | **Swept.** Acceptance reported as a curve in N, not one number |
| "the 12 most-deficient clusters" | the acceptance headline | **Defined by a stated rule, then swept.** Report over all clusters *and* the deficient subset, with subset size varied |
| `B = 1000` budget | C1, C2, C3 | **Never privileged.** C2 computes over all B ∈ [0, 4447]; C1 sweeps B |
| `T ∈ {0.005…0.05}` | C1 allocation | **Widened by measurement** until both degenerate ends are reached (1 cluster funded ↔ effectively uniform) |
| `seed 0`, single draw | k-means, splits, random arm | **≥ 10 seeds / draws**, spread reported. One seed is not a measurement |
| DINOv2 L/14 only | every embedding | **≥ 2 independent embedder families** so no conclusion is embedder-specific; resolution swept (B3 showed 4.1× sensitivity) |
| Hardcoded 7-name `LEAK` set | target filtering in B3/C1 | **Not hardcoded.** Consumed from D2's *measured* output — which forces D2 to run early (§3.0) |
| Linear response rate `0.00867 Sα/SD` from **one** anchor | C3's entire arithmetic | **Discarded.** Cannot be re-derived from primary data either (see C3). C3 reports a 2-D sensitivity surface instead of assuming a rate |
| σ = 0.00356 from rescued runs | C3's detection bar | **Discarded as input.** See C3 |

Legitimately retained, because they are facts about *this repo's code*, not old-package choices:
`ESLoss(a=0.9, b=0.3, c=0.5, use_weighted_bce=False)` on sigmoid outputs (`MyTrain.py:225-227,286`
under `--task S2C`, called at `CLS.py:100-105`); `n_super_pix = 16`; batch size 16; 352×352 inference;
mask polarity conventions. Each is cited to its line and re-asserted in code.

---

## ⚠ Live change to primary data, mid-audit

`Dataset/Test/CAMO/` **was deleted at 2026-08-30 13:03**, during this exploration. It was present when
I began (250 files counted, 5 hashed). Every command I ran was read-only; `find` confirms
`Dataset/Test` is the only repo path modified today. `Dataset/Val/CAMO/` is intact.

| Measurement | Status |
|---|---|
| `Val/CAMO/Imgs` vs `Test/CAMO/Imgs` filename identity, 250/250 | VERIFIED pre-deletion (`diff` → 0 lines) |
| Content identity, 5/5 sampled | VERIFIED pre-deletion (sha256 equal) |
| Content identity, full 250/250 | **NOW UNVERIFIABLE** — input removed |

The scoping consequence survives and is independently provable: `MyTrain.py:324` selects
`Tea_epoch_best.pth` on `--val_root ./Dataset/Val/CAMO/`, which is the published CAMO **test** split
⇒ **CAMO can never be reported as an endpoint**. Please confirm the deletion was intentional.

---

## §1 Data-provenance map

Counts and hashes verified by me in Phase 0. `agg` = first 16 hex of
`sha256( sorted per-file "sha256  name" listing )`; E0 recomputes these into a full manifest.

| Input | Path | Count | agg |
|---|---|---|---|
| HKU-IS photographs | `Dataset/Source/HKU-IS_raw/imgs` | 4447 png | `8dd2c5242e1c4128` |
| HKU-IS masks — **object = WHITE** | `Dataset/Source/HKU-IS_raw/gt` | 4447 png | `fb7b5a054348722d` |
| Authors' synthetic pool — **what `MyTrain.py` reads** | `Dataset/Source/HKU-IS/Image` | 4447 jpg | `b42e5f44b5f2b0db` |
| Authors' pool GT (≠ raw gt) | `Dataset/Source/HKU-IS/GT` | 4447 png | `95a0b4ed8ce47903` |
| Local LAKE-RED renders | `Dataset/LAKERED/output/HKU-IS/images` | 4447 jpg | `79797ac73c338bf6` |
| Local render masks — **SOD polarity** (trap T2) | `…/output/HKU-IS/masks` | 4447 png | `6694672cab970ddd` |
| LAKE-RED staged inputs — masks **inverted** (0.783) | `…/input/HKU-IS/validation/{images,masks}` | 4447 + 4447 | E0 |
| Target domain (3040 COD10K + 1000 CAMO) | `Dataset/Target/Image` | 4040 jpg | `ae84685540e99138` |
| Test, primary | `Dataset/Test/COD10K/{Imgs,GT}` | 2026 + 2026 | `100ac2e5c998ea29` / `2e0a8003194a0c6f` |
| Val (≡ CAMO test) | `Dataset/Val/CAMO/{Imgs,GT}` | 250 + 250 | `1c70eeb9a90e9088` |
| Test, secondary | `Dataset/Test/{CHAMELEON,NC4K}/Imgs` | 76 / 4121 | E0 |
| **Final SINet model** | `Snapshot/SINet/S2C/` | 17 `.pth` + log | E0 |
| Other primary models (B1's robustness axis) | `Snapshot/{SINet,SINet-v2}/S2C{,_MT,_SO}`, `Snapshot/SegMaR/S2C` | 7 runs | E0 |
| Primary predictions | `Result/**` (6 dirs) | 2026 each | `dc6d34d306498563` (S2C) |
| LAKE-RED weights | `LAKE-RED/ckpt/LAKERED.ckpt` | 6.4 GB | E0 |
| LAKE-RED provenance manifest | `…/input/HKU-IS/manifest_all.json` | records `object_frac_stats.mean = 0.191323` | E0 |

**Renders are regenerable.** `run_hkuis.sh` is self-contained: stages inverted masks via
`prepare_lakered_inputs.py`, runs `test.py --isReplace --seed 0` over 2 GPU shards; prior run
13:19→14:28 (~70 min). Env verified: torch 2.11.0+cu128, CUDA 12.8, 2× RTX PRO 6000 Blackwell (98 GB),
timm 1.0.28.

### Missing / removed

| Input | Status | Consequence |
|---|---|---|
| `Dataset/Test/{Image,GT}` | **ABSENT**; hardcoded by `MyTest.py:53-54` and every old audit script | Were COD10K — `Result/SINet/S2C` filenames match `Test/COD10K/GT` with **zero** diff over 2026. Scripts use COD10K paths; proof logged |
| `Dataset/Test/CAMO/` | **DELETED 13:03 today** | See above |
| `HKU-IS_iteration2` pools | ABSENT | `\|Ds\|` not re-measurable — **but C2's load-bearing claim no longer needs them** (see C2) |
| Seed runs s42…repC | `/tmp`-rescued only; retraining deferred | σ_seed is `UNVERIFIED-DEFERRED` |
| InceptionV3 caches | Present but **orphaned** — no producing script, no `names.json`, unrecoverable which 2000 of 4447 | Re-implemented from scratch or dropped, with reason |

---

## §2 Representation table — every step that embeds an image

Where the last slip lived. Each row: what I found **in the code**, plus the pixel-level check that
re-proves it at execution. Variable names are not evidence.

| # | Step | Representation found in code | Source | Pixel check |
|---|---|---|---|---|
| R1 | Target / val / test clustering | **Raw full image**, squash-resized S×S BICUBIC; no mask, no crop, no aspect preservation | `embed_dino.py:17-18,44` | Assert no mask path opened; re-embed 8 rows against a fresh full-image embed |
| R2 | **Selection — the slip** | **Object on flat grey 128.** `a[gt < 127] = 128` at native resolution, *then* BICUBIC-resized — object edges blend into grey; ~81 % of the frame is constant | `embed_dino.py:19-23` (`:22`) | Assert `np.unique` of the masked region == `{128}`, covering `1 − fg_frac` of pixels; log the literal 128 |
| R3 | Landing / acceptance | **Finished LAKE-RED render**, full and unmasked | `embed_dino.py:45` | Re-embed against a fresh render embed |
| R4 | A3 signature | Full images, three pools | — | Confirm each pool's agg hash matches §1 |
| R5 | ES scoring | 352×352 + ImageNet norm; `ESLoss(a=0.9,b=0.3,c=0.5,use_weighted_bce=False)` on **sigmoid** | `MyTrain.py:225-227,286`; `CLS.py:100-105` | Assert the loss object's config equals `MyTrain.py:286` under `--task S2C` |

### New representation traps found in Phase 0 — none flagged by the old package

- **T1 — three HKU-IS pools, all 4447, none identical.** `HKU-IS_raw/imgs` (photographs),
  `Source/HKU-IS/Image` (authors' synthetic, **what training reads**), `LAKERED/output/…/images`
  (local). Pairwise maxdiff on stem `0004`: authors↔raw **251**, authors↔local **240**. The old
  package embedded the *local* pool while the model trained on the *authors'* pool.
- **T2 — render-mask polarity flips back.** LAKE-RED *input* masks are inverted (frac>127 = 0.783) as
  `run_hkuis.sh` documents, but *output* masks are back in **SOD polarity** (0.217, identical to
  `raw/gt`). Reusing output masks as LAKE-RED-polarity masks silently inverts the object.
- **T3 — `Source/HKU-IS/GT` ≠ `HKU-IS_raw/gt`.** No sampled stem is pixel-identical; fg fraction
  0.2114 vs 0.2170 on `0004`. A2 must say *which* mask set it measured.
- **T4 — the old embedder ran fp16** (`embed_dino.py:6` `.half()`) while `common.py:216` rebuilt it
  fp32. The rebuild declares one canonical embedder in-repo and states precision.

---

## §3 Experiment list

**Trains? NO** for every experiment.

### 3.0 Execution order — dependency, not alphabet

The old package ran D1/D2 last, then hardcoded their findings upstream. That inverts the dependency
and is how a 7-name `LEAK` set became a magic constant. Order:

**E0 → D2 → D1 → A1 → A2 → A3 → B1 → B2 → B3 → C1 → C2 → C3**

D2 first because B3 and C1 must *consume* the measured leakage set. C3 last because it consumes C1.
One script, one commit, one log block each.

---

### E0 — Regenerate, don't rescue
- **Objective.** Rebuild every feature cache and the render pool from primary data; prove the package runs with the old scratchpad unreachable.
- **Inputs.** All of §1.
- **Method.** Declare one canonical embedder in-repo (**≥ 2 families** per §0.2; resolution swept; CLS + patch-mean; squash-resize BICUBIC; ImageNet norm; precision stated; unnormalised storage, L2 at use). Embed all sets × 3 pools. Re-run `run_hkuis.sh --seed 0` into a **new** directory and compare with the existing renders. Emit a full SHA256 manifest + environment/seed stamp.
- **Representation.** R1–R4, each named in the manifest.
- **Confirms / refutes.** Manifest complete and every later script runs with `SCRATCH` unset / any script still needing a `/tmp` path.
- **Threshold.** Manifest covers 100 % of declared inputs. Renders: report mean/max pixel delta **and** cluster-assignment agreement — **≥ 95 % identical** at the chosen k. Byte-identity is *not* required (cuDNN nondeterminism); claiming it would be the error.

### D2 — Leakage sweep *(runs early — B3/C1 consume it)*
- **Objective.** Bound what any result can claim and which sets can be reported; produce the leaked-name set as **data**, not a constant.
- **Inputs.** `Target/Image` (4040); `Test/{COD10K,CHAMELEON,NC4K}/Imgs`; `Val/CAMO/Imgs`; `Source/HKU-IS/Image`; `…/output/HKU-IS/images`. `Test/CAMO` no longer exists.
- **Method.** **Full pairwise hashing, not name matching** — Phase 0 confirmed only **2 of the 7** claimed duplicates share a filename (`Cat-1506`, `Crab-32`); the other 5 are cross-named and invisible to a name check. SHA256 for byte identity, then decoded-pixel hash with `maxdiff == 0` on candidates to catch jpg→png re-encodes. Every ordered pair of splits plus internal duplicates. **Emits `rebuild/out/d2_leaked_names.json`, which B3 and C1 read.**
- **Representation.** Decoded pixels — the only one that catches re-encodes.
- **Confirms / refutes.** A measured duplicate count / any count differing from the old claim.
- **Threshold.** Exact counts, no rounding. CAMO row reports reduced pre-deletion evidence.
- **Scoping consequence, asserted in code.** Checkpoint selection runs on a test set (above) ⇒ CAMO is never an endpoint. Primary COD10K; secondary CHAMELEON + NC4K.
- **Limitation.** Pixel-identity only; near-duplicates out of scope.

### D1 — Foreground exhaustion
- **Objective.** Scope any null to "targeting doesn't help when the foreground pool is exhausted."
- **Inputs.** `HKU-IS_raw/{imgs,gt}`, `Source/HKU-IS/{Image,GT}`, `…/output/HKU-IS/{images,masks}` — 4447 each.
- **Method.** SHA256 every foreground, mask and render; prove the render set is a **bijection** onto the raw foreground set; count internal duplicates per pool. **Assert mask polarity explicitly at both ends** (trap T2) rather than assuming the documented inversion.
- **Confirms / refutes.** Zero renders whose foreground is outside the base pool ⇒ every "added" image is a re-render / any render tracing outside the 4447.
- **Threshold.** Binary. Internal duplicates reported, not rounded away.

### A1 — The conditioning bottleneck
- **Objective.** Establish the true width of the channel through which the foreground steers background generation.
- **Inputs.** `ddpm.py`, `config_LAKERED.yaml`, `LAKERED.ckpt`, real HKU-IS samples.
- **Method.** Read `n_super_pix` from config (`:72` → **16**). Forward real samples with a hook on `mlp_in`'s input; log the live tensor shape. Log per-superpixel occupancy (`LMP` zero-fills empty segments, so nominal ≠ effective).
- **The sub-check that decides the claim.** `ddpm.py:1586` computes `fg2bg = self.fuse(torch.cat((vec_bg, fg), dim=1))` — a 1×1 conv seeing **raw `fg`** alongside the 48 scalars — and `new_fg = fg*(1-mask) + fg2bg*mask` uses it *inside* the regenerated region. If `fg` is non-zero at `mask==1` pixels, foreground information reaches the background through a **second, full-resolution** path and "48 scalars" is wrong. I will capture `fg[mask==1]` and log its statistics.
- **Confirms.** `vec_fg.shape == (1,16,3)` **and** `fg[mask==1]` identically zero.
- **Refutes.** Non-zero `fg` under the mask ⇒ the claim is revised, not restated.
- **Threshold.** Both binary; occupancy reported, not thresholded.

### A2 — Background dominance
- **Objective.** Measure the foreground pixel share — how much of each image the model invents.
- **Inputs.** All **three** mask sets (T3), 4447 each.
- **Method.** Per-image `mean(mask > 127)` with polarity fixed **per source** (per-image detection misfires on corner-covering objects). Mean, median, sd, deciles, range, for each set. Cross-check against `manifest_all.json`'s recorded `0.191323`.
- **Confirms / refutes.** Three sets agree within 0.5 pp / divergence > 0.5 pp ⇒ the "~82 % background" headline is set-dependent and must be stated per set.
- **Threshold.** Report; flag divergence > 0.5 pp.

### A3 — The generator's signature, with honest controls
- **Objective.** Test whether real-vs-generated separability means anything, and whether LAKE-RED reduces manifold coverage relative to **its own input pool**.
- **Inputs.** `Target/Image` (4040), both generated pools (4447 each), `HKU-IS_raw/imgs` (4447).
- **Method.** Linear probe real-vs-generated with a **stratified random** split (the old sorted-filename split is reproduced deliberately as a *labelled control*, not as a result). Controls: (i) real-vs-real random halves = true null, (ii) JPEG-75 recompression of *identical* images, (iii) darkening, (iv) cross-dataset real-vs-real. Then k-NN precision/recall against the target manifold for both generated pools **and** the raw HKU-IS input pool.
- **Representation.** R4 — full images, three pools, ≥ 2 embedder families, resolution swept.
- **Confirms.** High AUC is near-vacuous — an identity-preserving recompression separates comparably.
- **Refutes.** Controls at chance while real-vs-generated is high ⇒ a genuine generator limitation, and this link weakens.
- **Threshold.** Vacuity if any identity-preserving control exceeds **AUC 0.90**. Coverage loss real if `recall(generated) < recall(raw_hkuis)` on both pools and both embedders.

### B1 — Is the weakness signal real?
- **Objective.** Test whether ES-disagreement predicts *the error that matters* (structure/boundary), not just pixel error.
- **Inputs.** `Snapshot/SINet/S2C/{Stu_40, Tea_epoch_best}.pth`; `Test/COD10K/{Imgs,GT}`; `Val/CAMO/{Imgs,GT}`; E0 embeddings.
- **Method.** k-means the target (verify R1 — **whole images**) at the k chosen in §0.2, ≥ 10 seeds. Per image compute ES in the repo's exact `CLS.py:100-105` convention (R5). Compute TRUE error separately as **MAE, 1−Sα, 1−IoU** via `Eval/metrics.py`. Spearman ρ per cluster and per image, val and test, with a permutation test.
- **Robustness axis (replaces seeds).** Repeat across the other **primary** trained models — `SINet/S2C_MT`, `SINet/S2C_SO`, `SINet-v2/S2C`, `SegMaR/S2C`: a cross-architecture check, fully regenerable. Seed-level robustness is `UNVERIFIED-DEFERRED`.
- **Confirms.** ρ(ES, MAE) high **and** ρ(ES, 1−Sα) materially lower ⇒ targeting optimizes the wrong objective.
- **Refutes.** ρ(ES, 1−Sα) ≈ ρ(ES, MAE) ⇒ ES is a valid proxy for the headline metric; this link fails.
- **Threshold.** "Wrong objective" if `ρ(ES,1−Sα) < 0.5 × ρ(ES,MAE)` at the chosen k on test, holding across seeds and architectures.

### B2 — Is the coverage term worth including?
- **Objective.** Test whether the design's second term helps or harms — the measured basis for λ_cov = 0.
- **Inputs.** B1's per-cluster table; cluster occupancy from E0.
- **Method.** Spearman ρ of `−log(n_s/n_t)` alone against true per-cluster error; then combined `d(c) = ES − λ_cov·cov` over a λ_cov sweep, at the k sweep, on val **and** test, with top-10 overlap against the true worst-10.
- **Confirms / refutes.** Coverage alone ≈ 0 or negative and adding it degrades ρ ⇒ λ_cov = 0 is measured / coverage improves ρ at any λ_cov ⇒ λ_cov = 0 was wrong.
- **Threshold.** Degradation real if ρ drops by **> 0.2** across the λ_cov sweep. Val/test sign disagreement reported, not smoothed.

### B3 — Does steering work, and by which representation? *(the slip experiment)*
- **Objective.** Establish feasibility of targeting and expose how much the headline depends on arbitrary choices.
- **Inputs.** E0 embeddings for target, cutouts, and **both** render pools; `rebuild/out/d2_leaked_names.json` from D2.
- **Method.** k-means the target (k sweep, ≥ 10 seeds, leaked names dropped **from D2's measured set**). For each cluster take the N nearest foregrounds and ask whether their render lands in that cluster. **Three selection representations in one table:**
  - **(a) grey-128 cutout** — what the old code did (R2)
  - **(b) rendered image** — what the plan's O4/O5 specified (R3)
  - **(c) raw full scene** — the third natural option; cheap, and closes the question
  
  Each × resolution sweep × both pools × N sweep. Every cell gets a chance baseline `p_land(c) = n_s(c)/Σn_s` with a one-sided binomial test, **and** a held-out split (rank on half A, measure on half B) so the number is not self-referential.
- **Representation.** R2 / R3 / R1 per arm, **printed in the log block**, not implied.
- **Confirms / refutes.** Acceptance materially above chance in deficient clusters ⇒ targeting feasible / acceptance at chance ⇒ infeasible, and the argument short-circuits before C1.
- **Threshold.** Above chance if binomial p < 0.001. **Resolution-sensitivity flagged if two resolutions differ by > 2×** (the old package's 6.46 % vs 26.67 % is a 4.1× swing).

### C1 — The decisive number: how different is targeted data from random? *(never run before)*
- **Objective.** Measure the actual distance between the targeted training set and a random one. **Load-bearing.**
- **Inputs.** E0 embeddings; B1's per-cluster ES; D2's leaked-name set.
- **Method.** Allocate budget B by temperature-softmax over per-cluster ES; select the nearest cutouts per funded cluster. **Random arm, stated exactly:** a uniform draw *without replacement* of the same size B from the *same* 4447-item pool, in the *same* embedding space, averaged over **≥ 20 independent draws** (the old design used one). Report ‖Δmean‖ and Cohen's *d* over the k × T × B sweeps, logging clusters funded and max allocation per cell, with T widened until both degenerate ends are reached.
- **Representation.** R2 (cutouts) **and** R3 (renders) — B3 will have shown the two disagree.
- **Confirms / refutes.** Small *d* ⇒ the arms see nearly identical data and no gain is possible / large *d* ⇒ the arms genuinely differ and the null needs another explanation.
- **Threshold.** **d < 0.2** ⇒ materially identical. **d ≥ 0.5** ⇒ this link fails and the verdict must change. The value 0.10 is an old claim in §4 with a blank measured column — **not** an expectation.
- **Limitation logged.** *d* is a **mean** shift; higher-moment differences (variance, coverage) are unmeasured and are the one route by which the true effect could exceed prediction.

### C2 — Do budget or training dynamics rescue it?
- **Objective.** Show added data buys zero extra optimization, and that no budget B makes the effect detectable.
- **Inputs.** `MyTrain.py:47,51,306-307`; `Src/utils/Dataloader.py:200-216`; and — **new** — the in-repo training logs.
- **Method, part 1 — direct empirical proof, no arithmetic.** Phase 0 found this in primary data; the script asserts it. `Snapshot/SINet/S2C/training_log.log` logs `total_step = 0253` at **both** iteration 1 (line 2) and iteration 2 (line 1017). Iteration 2's source pool is strictly larger — `CLS.py` appends accepted pseudo-labelled target images — **yet the step count is identical.** Control: `S2C_SO/training_log.log` logs `0278` = ⌈4447/16⌉ (source loader ungated at `MyTrain.py:47`) against `0253` = ⌈4040/16⌉ (pinned by the *target* loader). **This retires the old package's dependence on the deleted iteration-2 pools**, which it had to mark `UNVERIFIED-NOT-REPRODUCIBLE`.
- **Method, part 2.** Pool-shift curve `(B/|Ds|)·(1 − B/4447)` over all B ∈ [0, 4447], maximum located analytically and numerically. Per-arm sampling table. `|Ds|` values depending on deleted pools stay `UNVERIFIED`; the curve's **shape** (concave, zero at both ends) does not depend on them.
- **Confirms / refutes.** Identical `total_step` across a growing pool ⇒ added data buys zero gradient steps; curve → 0 at B = 4447 / `total_step` differing between iterations.
- **Threshold.** Binary on the log assertion; curve endpoint exactly 0 at B = 4447.
- **Also logged.** Arm A is **not** a clean control — it confounds "1000 more images" with less per-image exposure, so only B-vs-C is clean.

### C3 — The noise floor and the effect-vs-noise verdict *(restructured — assumption-free)*
- **Objective.** Establish the detection bar and translate C1's measured *d* against it.
- **What primary data supports.** Re-derive Sα, Fβw, Eφ, MAE with the repo's own `Eval/metrics.py` at the `Eval/MyEval.py:33-39` convention for **σ_within (PRIMARY)** — `Snapshot/SINet/S2C/Tea_{36,37,38,39,40}.pth` + `Tea_epoch_best.pth`, six late-epoch checkpoints from the one final run, over COD10K. This is a **within-run stability floor** and a *lower bound* on run-to-run σ. It is **not** seed-σ and the log block says so in those words. Plus a cross-check of `Result/SINet/S2C` against fresh inference from `Tea_epoch_best.pth`, proving the eval path faithful.
- **What it cannot.** **σ_seed is `UNVERIFIED-DEFERRED`** — the six seed runs exist only as archived files and retraining is deferred.
- **The response rate is also discarded, and cannot be re-derived.** The old anchor (`0.00867 Sα/SD`) rests on one MT→Ours point whose pool-shift x-coordinate came from the deleted iteration-2 pools — and the anchor added *real target-domain supervision* that arm C does not, so it was generous to arm C anyway. The repo's other primary runs (SO / MT / Ours × SINet / SINet-v2 / SegMaR) differ by **method**, not pool composition, so they cannot supply the missing points. **I will not invent a rate.**
- **What C3 therefore reports.** A **2-D sensitivity surface** of `ΔSα / 2σ` over (response rate *r*, noise σ), with C1's measured *d* as the only fixed input, and an explicit statement of the region where the effect *would* be detectable: *"undetectable unless r > X and σ < Y."* σ_within is drawn on it as the one primary reference line. This is a stronger and more falsifiable claim than a single ratio, and it needs no assumed constant.
- **Confirms / refutes.** The detectable region lies outside anything the repo's own measurements reach / a plausible (r, σ) inside it.
- **Threshold.** Detectable iff ΔSα ≥ 2σ. The boundary (X, Y) is reported explicitly.

---

## §4 Record of old claims — for `REVISION_TABLE.md` only

Transcribed from the old package **as a frozen record**, so the revision table has something to
compare against once those files leave the tree (§0.1). **Not an input, not a baseline, not an
expectation.** `[no code]` = no producing script ever existed — the seven never-run experiments.

| # | Claim | Old value | Measured | Verdict |
|---|---|---|---|---|
| A1.1 | Conditioning width | 48 (16 × 3) | | |
| A1.2 | Live `vec_fg` shape | (1, 16, 3) | | |
| A1.3 | Effective width, 20 samples | 45.75 | | |
| A1.4 | `fg` under mask is zero | *never tested* | | **NEW** |
| A2.1 | Mean fg fraction | 0.1913 | | |
| A2.2 | Invented background | 80.87 % | | |
| A2.3 | Same, authors' GT | 81.44 % | | |
| A3.1 | Probe AUC real-vs-LAKE-RED | 0.9989 | | |
| A3.2 | Probe AUC true null | 0.4781 | | |
| A3.3 | Probe AUC JPEG-75 | 0.4117 | | |
| A3.4 | Probe AUC sorted-split bug | 0.8888 | | |
| A3.5 | Cohen's *d* probe axis | 4.67 / 4.61 / 4.33 | | |
| A3.6 | Recall, LAKE-RED | 0.4662 | | |
| A3.7 | Recall, raw HKU-IS | 0.7461 | | |
| A3.8 | Generation recall delta | −0.2799 (−37.5 %) | | |
| B1.1 | ρ(ES, MAE) k=20 test | +0.788 | | |
| B1.2 | ρ(ES, 1−Sα) k=20 test | +0.409 | | |
| B1.3 | ρ(ES, 1−IoU) k=20 test | +0.265 / +0.271 | | |
| B1.4 | ρ(ES, MAE) k=20 val | +0.976 | | |
| B1.5 | ρ per-image ES vs MAE test | +0.751 | | |
| B1.6 | Cross-run ρ, MAE k=20 | +0.893 ± 0.059 (n=5) | | axis changed |
| B2.1 | ρ(cov, MAE) k=20 val | −0.717 `[no code]` | | |
| B2.2 | ρ(cov, MAE) k=20 test | +0.006 `[no code]` | | |
| B2.3 | ρ(ES + 0.05·cov) k=20 val | −0.733 `[no code]` | | |
| B2.4 | ρ(acceptance, n_s) k=20 | +0.762 `[no code]` | | |
| B3.1 | Acceptance L/518 k=20 in-sample | 26.67 % `[no code]` | | |
| B3.2 | Acceptance L/518 k=20 held-out | **20.62 %** `[no code]` | | never had a script |
| B3.3 | Acceptance L/224 k=20 in-sample | 6.46 % `[no code]` | | |
| B3.4 | Acceptance L/224 k=20 held-out | 5.00 % `[no code]` | | |
| B3.5 | Chance rate L/518 k=20 | 1.63 % `[no code]` | | |
| B3.6 | InceptionV3 k=50 | 0.00 % `[no code]` | | arrays orphaned |
| B3.7 | Selection on **render** | *never run* | | **NEW — the slip arm** |
| C1.1 | **Cohen's *d* targeted-vs-random** | **≈ 0.10** `[no code]` | | **load-bearing; never run** |
| C1.2 | ‖Δmean‖ | 0.084–0.099 `[no code]` | | |
| C2.1 | `total_step` pinned | 253 `[no code]` | | provable from logs |
| C2.2 | `total_step`, source-only | 278 `[no code]` | | |
| C2.3 | Pool shift peaks at B | 2000 (1.26×) `[no code]` | | |
| C2.4 | Pool shift at B=4447 | 0 `[no code]` | | |
| C2.5 | \|Ds\| per arm | 6824 / 7824 / 8824 `[no code]` | | pools deleted |
| C3.1 | σ(Sα), all runs n=6 | 0.00356 `[no code]` | | deferred |
| C3.2 | σ(Sα), distinct seeds n=4 | 0.00286 `[no code]` | | deferred |
| C3.3 | σ_within, late-epoch | *never measured* | | **NEW — primary** |
| C3.4 | Predicted ΔSα | 0.000111 `[no code]` | | |
| C3.5 | Shortfall vs 2σ | 64× (51× at B=2000) `[no code]` | | |
| D1.1 | Distinct foregrounds | 4447 `[no code]` | | |
| D1.2 | Internal render duplicates | 2 (4445 unique) `[no code]` | | |
| D2.1 | COD10K-test ∩ Target | 7 (2 same-name, 5 cross) `[no code]` | | 2 same-name confirmed |
| D2.2 | Val/CAMO ≡ Test/CAMO | 250/250 `[no code]` | | **input deleted** |
| D2.3 | CAMO ∩ CHAMELEON | 3 `[no code]` | | |
| D2.4 | Internal duplicates in Target | 2 `[no code]` | | |
| D2.5 | MAE impact of the 7 | 0.000012 `[no code]` | | |

---

## §5 Phase-0 close

### (a) Confident — fully executable from primary data

**E0, D2, D1, A1, A2, A3, B1, B2, B3, C1** — every input verified present and hashed in §1. C1 in
particular, the load-bearing never-run experiment, needs only E0's embeddings, B1's cluster ES and
D2's leakage set; all regenerable. **C2 joined this group during Phase 0**: its central claim proved
directly from the in-repo training logs, removing its dependence on the deleted pools.

### (b) Depends on inputs that are missing or need regeneration

| Experiment | Input at risk | Handling |
|---|---|---|
| **C3** | σ_seed (runs archived, retraining deferred) **and** the response rate (single confounded anchor, pool-shift coordinate deleted) | σ_within from six primary late-epoch checkpoints; verdict reported as a 2-D surface over (r, σ) with an explicit detectable region. No constant invented |
| **C2** part 2 | `\|Ds\|` = 6824/7824/8824 | `UNVERIFIED`. Curve shape and part 1 unaffected |
| **B3** Inception arm | Orphaned caches; which 2000 of 4447 is unrecoverable | Re-implement and log as a re-implementation, or drop with reason |
| **D2** CAMO row | `Test/CAMO` deleted today | Report pre-deletion evidence and reduced scope |
| **E0** render regen | Byte-identity not expected across a re-run | Threshold is cluster-assignment agreement |
| **All** | `Dataset/Test/{Image,GT}` absent | Ported to COD10K with the identity proof logged |

### (c) Where I most expect the rebuilt number to DIFFER — watch these

1. **C1's Cohen's *d* (old ≈ 0.10).** Highest stakes. It never had a script, yet the old docs call it
   the one number that "never moved across any re-measurement" — impossible for a number nothing
   computed. It inherits B1's cluster ES, which the old package's own summary lists as **MISMATCH on
   5 of 5** ρ values. If ES moved, the allocation moves and *d* moves. The verdict rests here.
2. **Everything touched by §0.2.** Discarding the inherited constants is the single largest source of
   expected divergence — B3's acceptance is defined by (k, N, deficient-subset size) and the old
   package fixed all three without justification. Re-deriving k alone should move every clustered
   number in B1, B2, B3 and C1.
3. **B3's 20.62 % held-out.** No script, no CSV, no log block; `analyze.py` contains no split of any
   kind. Expect it to change, and expect the **render-selection arm (B3.7)** — measured for the first
   time — to differ substantially from the cutout arm. That is the slip.
4. **A2's foreground fraction.** Your brief says "expected ~18 %"; the old package measured 0.1913
   (19.13 %) on raw GT and 18.56 % on authors' GT, and `manifest_all.json` independently records
   0.191323. The "~18 %" and the "82 % background" headline appear to come from *different mask sets*
   (trap T3) — a mixed pair.
5. **A3 on the authors' pool.** Every old A3 number came from the *local* re-generation. The authors'
   pool — the one the model actually trained on — has never been probed.
6. **A1's effective width.** If `fg` is non-zero under the mask, "48 scalars" understates the
   conditioning channel. `ddpm.py:1586` makes this a real possibility, not a formality.
7. **C3's shape, not just its value.** σ_within is a different quantity from σ_seed and will almost
   certainly be **smaller**, making the shortfall ratio *larger*. Reporting it as if it were seed-σ
   would be the exact failure this rebuild exists to prevent.

---

## Verification

- After each experiment: `results/REBUILD_LOG.txt` gains exactly one block (timestamp, commit, exact
  command, metrics, old claim beside each, PASS/FAIL vs threshold, revision note), and exactly one
  commit contains the script + log block + any CSV.
- Gate before any prose: `grep` every number in `REBUILD_FINDINGS.md` back to a log block. A number
  without one is a defect.
- Provenance gate at the end of E0: re-run every script with the archived artifacts and the `/tmp`
  scratchpad both made unreadable. Any failure means a rescued dependency survives.
- Final: `REVISION_TABLE.md` lists every §4 row whose measured value differs, with the reason.

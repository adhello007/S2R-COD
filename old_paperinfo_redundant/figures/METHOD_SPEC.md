# METHOD_SPEC.md — evidence spec for the S2R-COD ICLR 2027 figure set

**Status: PHASE 0 DELIVERABLE. No `.tex` has been written.**

**Sourcing rule.** Every factual row below carries a `file:line` citation. Numbers were read by me
directly from the committed machine-readable artifact named in the row, not transcribed from a prose
summary. Where the artifact and a `*_RESULTS.md` could disagree, the rule of
`NAVIGATION.md:34-35` applies — *"if a results markdown and its log block ever disagree, the log
wins."* Nothing here is interpolated, rounded from memory, or reconstructed.

**Sources deliberately not used.** `rebuild/PAPER/main.tex` and `rebuild/PAPER/PAPER_PLAN.md` are
gitignored (`.gitignore:31`) and untracked (`git ls-files rebuild/PAPER/` is empty), and you
instructed that they are unverified. They are used **only** as an advisory terminology cross-check in
Phase 3, never as an evidence source. `rebuild/reference/old_scripts/` is archived and unused.

---

## 0. Four corrections to the brief (repo wins)

| # | Brief assumed | Repo says | Citation |
|---|---|---|---|
| 0.1 | "Tier" = confirmed / provisional | Tier 1/2/3 is a **scope** classification: specific to CSRDA/LAKE-RED · travels to the data+signal · method-independent | `rebuild/TIER_SEGREGATION.md:14-19` |
| 0.2 | `ABC/T2` is one experiment | **Two experiments sharing one directory.** `EXP T2` has no `rebuild/T2/`; it lives in `rebuild/ABC/` with artifacts in `out/t2/` | `rebuild/FINAL_RESULTS.md:84` |
| 0.3 | A1 is diagram-worthy | **A1 was never run.** Zero `EXP A1` blocks; *"No number in this document enters `results/REBUILD_LOG.txt`"* | `rebuild/FINAL_RESULTS.md:73,85`; `rebuild/TIER_SEGREGATION.md:430` |
| 0.4 | There is a closed generation loop | **There is not.** See §3 | `MyTrain.py:203,265,269-294`; `rebuild/ABC/abc_common.py:64-65` |

`T1`/`T2`/`T3` is overloaded four ways in this repository and the repo says so
(`rebuild/FINAL_RESULTS.md:42-53`). This spec therefore never writes a bare tier digit: scope is
written as the words `gen` / `signal+data` / `indep`, and the brief's figure tiers are written
"main figure" / "consolidated figure" / "per-experiment figure".

---

## 1. Notation table

Symbols that will appear in the figures. The `main.tex` column is **advisory only** (that file is
untracked and unverified); the definition column is authoritative.

| Symbol | Meaning | Defined in code | Configured value | main.tex (advisory) |
|---|---|---|---|---|
| `S_alpha` | Structure measure, the primary endpoint metric. Higher is better | `Eval/metrics.py:109` `class Smeasure(alpha=0.5)`, result key `sm` at `:217` | alpha = 0.5 | `$S_\alpha$` |
| `MAE` | Mean absolute error. **Lower** is better. Checkpoint-selection metric | `Eval/metrics.py:90` `class MAE`, key `mae` at `:106` | — | `MAE` |
| `F_beta^w` | Weighted F-measure | `Eval/metrics.py:333` `class WeightedFmeasure(beta=1)`, key `wfm` at `:397` | beta = 1 | — |
| `E_phi` | Enhanced-alignment measure; headline variant is `meanEm` | `Eval/metrics.py:220` `class Emeasure`, key `em` at `:330`; selection at `rebuild/ABC/abc_evaluate.py:44` | — | — |
| `L = L_sup + L_ES` | Total objective, **unweighted sum, no ramp-up** | `MyTrain.py:122` | — | `main.tex:218-223` |
| `L_ES = a*L_edge + b*L_region` | The ES consistency loss | `Src/utils/tool.py:45-77`, return at `:77` | a = 0.9, b = 0.3, c = 0.5 | `0.9 L_EA + 0.3 L_SW` |
| `lambda` | EMA teacher momentum | `Src/utils/tool.py:41-43`, called `MyTrain.py:129` | 0.9996 default, **0.996 under S2C** (`MyTrain.py:230`) | `$\lambda = 0.996$` |
| `es_j` | Per-cluster mean of the target-side ES signal | `rebuild/B1/b1_allocation_signal.py:135-147` | 75 clusters; range 0.018391-0.070668 | `$\mathit{es}_j$` |
| `w_j`, `T = alpha*sd(es)` | Softmax allocation weight and temperature | `rebuild/C1/c1_targeted_vs_random.py:75-81` | alpha = 1.0 (`rebuild/ABC/abc_common.py:43`) | `main.tex:292-296` |
| `B` | Generation budget, images added per arm | `rebuild/ABC/abc_common.py:57` `BUDGET = 1000` | 1000 | `$B = 1000$` |
| `k` | k-means cluster count on the target set | `rebuild/T2C/t2c_signals.py:37` `K=75` | 75, embedder `dinoL518`, seed 0 | `$k=75$` |
| `u`, `tau` | CLS pseudo-label rule `edge_loss < u * avg_loss`; CAM floor | `CLS.py:139`, `:149` | u = 0.8, tau = 0.4 (`MyTrain.py:231-232`) | `main.tex:282-288` |
| `sigma_hat`, `2 sigma_hat` | Pooled within-arm sd of `S_alpha`; the decision bar | `rebuild/ABC/abc_evaluate.py`; values in `out/abc_verdict.json` | df = 8 | `$\hat{\sigma}$` |
| `Delta(C-B)` | **The pre-registered claim** | gap set `rebuild/ABC/abc_evaluate.py:46-48` | — | `$\Delta(\mathrm{C}-\mathrm{B})$` |
| `total_step` | Gradient steps per round; pinned by `zip()` truncation | `MyTrain.py:325-327` | **253** (SINet) / **127** (SINet-v2) | — |

---

## 2. Stage inventory

Ordered. "Trained / frozen / deterministic" is the figure's shape-and-border axis.

| # | Stage | In | Out | Implementation | Hyperparameters (configured) | Status |
|---|---|---|---|---|---|---|
| 1 | Source pool | HKU-IS 4447 image+GT | `SrcDataset` | `Src/utils/Dataloader.py:11-19`; `os.listdir` + `sorted`, paired by **index not name** (`:29-31`) | trainsize 352 | deterministic |
| 2 | Target pool | 4040 unlabelled images, **no GT** | weak + strong views | `Src/utils/Dataloader.py:76`; strong = weak + `RandomAutocontrast` + `GaussianBlur(3, 0.1-1.5)` (`:88-94`) | — | deterministic |
| 3 | **LAKE-RED render pool** | 4447 (image, inverted mask) | 4447 renders | `LAKE-RED/test.py`; cond = `concat(VQ-encode(masked_image), downsample(mask))` at `:127-138` | 50 DDIM steps (`:194`), `--isReplace` (`:192`), `--seed 0` | **FROZEN, OFFLINE, ONE-SHOT** — `test.py:96` `eval()`, `:121` `no_grad()`, `:122` `ema_scope()`; no optimizer, no `.backward()` |
| 4 | ES signal | target images, (student, teacher) checkpoints | per-image scalar | `rebuild/B1/b1_allocation_signal.py:94-106`, mirroring `CLS.py:81-105` | 352 px, ImageNet norm, `use_weighted_bce=False` | deterministic |
| 5 | Clustering | DINOv2-L/518 CLS embeddings, L2-normalised | k=75 partition | `rebuild/B1/b1_es_error_correlation.py:425-433` `KMeans(n_init=10, random_state=seed)` | k=75, seed 0, 4033 target images | deterministic, **committed and never refit** |
| 6 | Allocation | `es_j` per cluster | 1000 chosen stems | `c1_targeted_vs_random.py:75-81` softmax, `:84-94` largest-remainder, `:125-134` centroid-cosine rank in R2 grey-128 cutout, `:153-177` greedy distinct | alpha=1.0, B=1000, serving `desc_nc` | deterministic; **imported not reimplemented** (`abc_common.py:203-214`) |
| 7 | Pool assembly | base 4447 + 1000 | arm pool 5447 | `rebuild/ABC/abc_build_pools.py:53-79`, **hard links** | A0 4447; A2/B/C10/CSHUF/CINV 5447 | deterministic |
| 8 | CSRDA round 1 | arm pool + target | student, EMA teacher | `MyTrain.py:48-129` | batch 16/32, lr 1e-4, epochs 40/100, `total_step` 253/127 | **trained** |
| 9 | Checkpoint selection | teacher, CAMO 250 | `Tea_epoch_best.pth` | `MyTrain.py:153-188`, driven `:342-344`, gated `epoch_iter > 20` | min MAE on CAMO | deterministic |
| 10 | CLS pseudo-labelling | target set, (student last-epoch, teacher best) | appended pool | `CLS.py:81-112` (denominator pass), `:138-159` (selection pass) | u=0.8, tau=0.4; label is teacher CAM, tau-floored then min-max renormalised (soft, not binary) | deterministic given checkpoints |
| 11 | CSRDA round 2 | enlarged pool | final teacher | `MyTrain.py:265` loop; **models rebuilt from ImageNet weights at `:269-294`** | same | **trained, from scratch** |
| 12 | Evaluation | `Tea_epoch_best.pth` of final round | metrics | `rebuild/ABC/abc_evaluate.py:106-111`; scorer validated to `S_alpha` 0.717216 / MAE 0.074463 before any new number | 352 px inference, 6 dp | deterministic |

**Measured budget consequence.** `zip()` stops at the shorter loader and the target loader binds, so
every arm receives an identical budget of **19,734 gradient steps and 315,744 source images**
regardless of pool size; both loaders shuffle, so added data **dilutes per-epoch exposure rather than
being excluded** — `rebuild/ABC/POOL_MECHANICS_AUDIT.md:528-543`. Per-image per-epoch exposure,
round 1: A0 **0.9103**, B and C10 **0.7432** (`POOL_MECHANICS_AUDIT.md:545-556`). That 22.5 % gap is
why A0 is an unclean control and why A2 exists.

---

## 3. The "closed loop" — what is actually operational

**There is no generation loop, and no stopping criterion.** Drawing one would be the single largest
fabrication available in this figure set. Evidence:

| Claim | Evidence |
|---|---|
| Round count is a hardcoded constant, not a criterion | `MyTrain.py:203` `--iteration` default **2**; `rebuild/ABC/abc_train.py:54` passes `'--iteration','2'` literally. **No convergence check anywhere in `MyTrain.py`** |
| Rounds executed = exactly 2, asserted per run | `rebuild/ABC/abc_train.py:110` `rounds == 2`; threshold at `:279-280`; PASS for 24/24 ABC and 12/12 T2 runs |
| Round 2 does not carry model state | `MyTrain.py:269-294` rebuilds student **and** teacher from ImageNet weights inside the round loop |
| The generator is never invoked from training | No LAKE-RED reference in `MyTrain.py`, `CLS.py`, `MyTest.py`, `Src/**`. The render pool is a string constant: `rebuild/ABC/abc_common.py:64-65` |
| Regeneration was excluded by design, in writing, before the campaign | `rebuild/ABC/ABC_PLAN.md:195-208` — *"If arm B regenerated its 1000 and arm C regenerated its 1000, the two arms' backgrounds would differ by a noise draw as well as by selection"* |
| The only returning edge carries pseudo-labels, not images | `MyTrain.py:346-349` calls `cls(...)`; `CLS.py:138-159` writes target images + teacher CAMs into the round-2 pool |
| Even a loop could not add foregrounds | Render set is a **bijection** onto the 4447 raw foregrounds: `auth_in_base 4447`, `auth_outside_base []`, `is_bijection_auth true` — read from `rebuild/D1/out/d1_bijection.json` |

**Honest topology for fig:method:** a straight spine with one feedback edge.

```
ES(target) -> kmeans k=75 -> softmax(alpha=1) -> budget B=1000 -> rank -> greedy select
     |                                                                        |
     +--------- offline, frozen, one-shot ---------> [LAKE-RED render pool] --+
                                                                              |
                                                                              v
  base 4447 -------------------------------------------------> arm pool 5447 --> round 1
                                                                              |
                            CLS pseudo-label (the ONLY feedback edge) <-------+
                                                                              |
                                                                              v
                                             round 2 (fresh ImageNet init) --> Tea_epoch_best --> endpoints
```

---

## 4. Data flow and the contamination gate

| Path | Count | Role | Citation |
|---|---|---|---|
| `Dataset/Source/HKU-IS/{Image,GT}` | 4447 | S2C source; what `MyTrain.py` reads | `MyTrain.py:242` |
| `Dataset/Target/Image` | 4040 | unlabelled target; **a two-dataset mixture** 3040 COD10K-train + 1000 CAMO | `MyTrain.py:222` |
| `Dataset/LAKERED/output/HKU-IS/images` | 4447 | pre-generated render pool | `rebuild/ABC/abc_common.py:64` |
| `Dataset/Source/ABC/<runid>/{Image,GT}` | 4447 or 5447 | per-arm pools, hard-linked | `rebuild/ABC/abc_build_pools.py:53-79` |
| `Dataset/Val/CAMO` | 250 | **checkpoint selection only, never an endpoint** | `MyTrain.py:223`; `rebuild/D2_reaudit/CLEAN_PROTOCOL.md:37,212-213` |
| `Dataset/Test/COD10K` | 2026 | **primary endpoint** | `rebuild/ABC/abc_common.py:66` |
| `Dataset/Test/NC4K` | 4121 | secondary endpoint, reported but never decides | `PREREGISTRATION.md` §1 |
| `Dataset/Test/CHAMELEON` | 76 | **WITHDRAWN** | see gate below |

**The gate is real and implemented, so it may be drawn.** `rebuild/D2_reaudit/detect_contamination.py:64-69`
fixes `DESC=32`, `SHORTLIST_RMS=14.0`, `NEAR_TOL=6.0`, `TOPK=8`. Measured, read from
`rebuild/D2_reaudit/out/d2r_endpoint_contamination.json`:

- CHAMELEON **41 / 76 = 0.5395** re-encoded training data; identical in the author-sourced copy
  (`chamnew`: 41/76, 0.5395).
- COD10K-test **2 / 2026 = 0.001**; NC4K **1 / 4121 = 0.0002**; CAMO-val **4 / 250 = 0.016**.
- Tolerance sweep saturates: CHAMELEON 11 / 26 / 37 / 40 / **41** at tol 1.0 / 2.0 / 3.0 / 5.0 / 6.0.
- Negative control, read from `rebuild/D2_nc4k/out/d2nc4k_sweep_test.json`: NC4K vs COD10K-**test**
  `contaminated.n = 0`, share `0.0`, 1 candidate shortlisted, 0 confirmed. Against COD10K-**train**
  (`d2nc4k_sweep_train.json`): `n = 0`, 0 shortlisted.
- **Binding limit that must appear on the figure:** `n_unchecked = 3039` of 4121 = 73.7 %, invariant
  at topk 8 / 32 / all (`d2nc4k_topk_sensitivity.json`). Every rate is a **lower bound**.

Leakage mechanism: test pixels enter training through the **unlabelled target pool**; test masks never
do. It is a transductive protocol violation, not label leakage
(`rebuild/D2_reaudit/CLEAN_PROTOCOL.md:110-116`).

---

## 5. Experimental arms

Base pool 4447 image+GT pairs is common to every arm. `B = 1000` additions except A0.
Seeds `{42, 43, 45}` (`rebuild/ABC/abc_common.py:56`), architectures `{SINet, SINet-v2}` (`:35-40`).

| Arm | Pool | What it adds | Isolates | Citation |
|---|---|---|---|---|
| **A0** | 4447 | nothing — the unpadded paper baseline | **UNCLEAN control**: +22.5 % round-1 per-image exposure | `abc_common.py:229-230`; exposure `POOL_MECHANICS_AUDIT.md:545-556` |
| **A2** | 5447 | 1000 **authors' originals** of arm B's stems, `DUP_` prefix | the clean, exposure-matched control | `abc_common.py:231-237` |
| **B** | 5447 | 1000 **random** renders, `default_rng(700000 + seed)`, redrawn per seed | the random Stage-C budget | `abc_common.py:125-131` |
| **C10 = "Ours"** | 5447 | 1000 **ES-targeted** renders at alpha=1.0 | concentration **and** targeting together | `abc_common.py:241-243` |
| **CSHUF** | 5447 | C10 with `es` **permuted across clusters** | targeting **destroyed**, concentration held | `abc_common.py:180-190` |
| **CINV** | 5447 | C10 with `es` **rank-reversed** | targeting **reversed**, concentration held | `abc_common.py:172-179` |
| C05 | — | alpha = 0.5 | pre-registered secondary | **NEVER RUN** — no `C05` dir in `Snapshot/ABC/` |

**"Ours" is C10.** It is the arm named in the decisive gap of `PREREGISTRATION.md` §1
(`Delta_CB = mean(Sa_C) - mean(Sa_B)`) and the reference arm both T2 falsification arms are defined
against (`PREREGISTRATION_T2.md` §T2.1).

**The C-family arms are deterministic across seeds.** Verified by me from
`rebuild/ABC/out/t2/abc_pools.json`: `SINet_CINV_s42/s43/s45` all carry
`image_digest = 4579e18cab84b2d8...`, identical, with `added = 1000`, `n_image = 5447`.

**Held constant across arms** (`PREREGISTRATION_T2.md` §T2.2; asserted in code): base 4447 bytes
against E0's manifest; target set 4040 unfiltered in both rounds (`abc_train.py:287-288`);
`total_step` 253/127 in both rounds of every run (`abc_train.py:281-283`); one trainer
`MyTrain.py --task S2C --method ours --iteration 2` (`abc_train.py:52-59`); checkpoint
`Tea_epoch_best.pth` of the final round; cuDNN determinism; endpoints and metrics.

**The T2 crux — shape held exactly, direction varied.** CSHUF and CINV reproduce C1's committed
allocation cell on four keys at exact 5-dp equality, `rebuild/ABC/abc_common.py:71-76`:
`clusters_funded 75`, `max_alloc_share 0.194`, `alloc_entropy_norm 0.78644`, `tv_from_uniform 0.49253`.
`n_displaced` (370 / 404 / 367) is reported, never asserted. This is what A/B/C structurally could not
do, and it is the single most figure-worthy control in the repository.

**Decision rule, frozen before run 1** (`rebuild/ABC/PREREGISTRATION.md` §1):

```
REAL EFFECT     iff Delta >  2*sigma_hat AND sign consistent 3/3 seeds
WITHIN NOISE    iff |Delta| <= 2*sigma_hat
REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3 -> report as-is, do NOT add seeds
```

**No p-values, by design, at n = 3** (`rebuild/FINAL_RESULTS.md:1966-1970`).

---

## 6. Metrics

| Metric | Class | Result key | rebuild key | Direction | Reported in paper tables |
|---|---|---|---|---|---|
| S-measure | `Smeasure(alpha=0.5)` `Eval/metrics.py:109` | `sm` `:217` | `Sm` | **higher better** | yes — the only tabulated metric |
| MAE | `MAE` `Eval/metrics.py:90` | `mae` `:106` | `MAE` | **lower better** | contamination + selection only |
| weighted F | `WeightedFmeasure(beta=1)` `:333` | `wfm` `:397` | `wFm` | higher better | computed, not reported |
| E-measure | `Emeasure` `:220` | `em.adp`, `em.curve` | `adpEm`, `meanEm`, `maxEm` | higher better | computed, not reported |
| F-measure | `Fmeasure(beta=0.3)` `:32` | `fm.adp`, `fm.curve` | `adpFm`, `meanFm`, `maxFm` | higher better | computed, not reported |

rebuild key tuple: `rebuild/ABC/abc_evaluate.py:45`
`METRIC_KEYS = ('Sm','wFm','MAE','adpEm','meanEm','maxEm','adpFm','meanFm','maxFm')`.

**Two cautions for the figures.** (a) `Fmeasure` and `WeightedFmeasure` apply beta in the *non-squared*
form `(1+b)PR/(bP+R)` (`Eval/metrics.py:60`, `:377`), not the textbook `beta^2` — so the figure must
write the metric name, never a formula. (b) The legacy text tables under `Eval/Eval/eval_txt/` exist in
**two different column orders** (`MAE` last in the older generation, 5th in the current one), so they
must never be parsed positionally. The collection script reads `rebuild/*/out/*.csv|json` instead.

---

## 7. Result candidates for the consolidated figure

All values below read by me directly from the named artifact. `n_seeds = 3` throughout the training
campaigns; spread is `sigma_hat` = pooled within-arm sd of `S_alpha`, df = 8.

### 7.1 ABC — `rebuild/ABC/out/abc_verdict.json`

| Cell | sigma_hat | 2 sigma_hat | arm means (A0 / A2 / B / C10) | `Delta(C10-B)` | sign | verdict |
|---|---|---|---|---|---|---|
| SINet \| COD10K **(primary)** | 0.008966 | 0.017933 | 0.700950 / 0.707679 / 0.713447 / 0.718481 | **+0.005034** | 3/3 | **WITHIN NOISE** |
| SINet-v2 \| COD10K | 0.006129 | 0.012257 | 0.689145 / 0.692102 / 0.695069 / 0.694669 | **-0.000399** | 2/3 | **WITHIN NOISE** |
| SINet \| NC4K | 0.004155 | 0.008310 | 0.758122 / 0.763210 / 0.766904 / 0.769013 | +0.002110 | 3/3 | WITHIN NOISE |
| SINet-v2 \| NC4K | 0.005267 | 0.010534 | 0.744411 / 0.747884 / 0.748613 / 0.749559 | +0.000946 | 2/3 | WITHIN NOISE |

**Delta(C-B) is WITHIN NOISE in all four cells, and the two architectures disagree on its sign.**

**One non-null verdict exists, and is EXCLUDED FROM ALL FIGURES BY AUTHOR DECISION.** In the same
file, `SINet|NC4K` gap `A0->C10` = **+0.010892**, sign **3/3**, verdict **REAL EFFECT** — the only
non-null verdict in 20 ABC comparisons. It sits on a *secondary* endpoint and compares against the
*unclean* A0 control, and `ABC_RESULTS.md:77-80` states it must not be read as support.
**Decision (2026-09-12): it appears in no figure.** It is not a distortion of `fig:exp:abc` to omit
it, because ABC's pre-registered primary claim is `Delta(C-B)` and that is what the figure reports.
It is recorded as an explicitly excluded row in `figures/FIGURE_EVIDENCE.md` so the audit trail stays
complete.

**The power statement travels with the null** (`ABC_RESULTS.md:8-12`): 2 sigma_hat = **0.017933** is
*larger* than the entire reference MT->Ours gap of **0.0142** the design claimed to half-resolve.

### 7.2 T2 — `rebuild/ABC/out/t2/abc_verdict.json`

| Cell | sigma_hat | 2 sigma_hat | arm means (B / C10 / CSHUF / CINV) | largest \|Delta\| | verdict |
|---|---|---|---|---|---|
| SINet \| COD10K | 0.002767 | 0.005533 | 0.713447 / 0.718481 / 0.716956 / 0.719346 | 0.002390 | WITHIN NOISE |
| SINet-v2 \| COD10K | 0.003195 | 0.006390 | 0.695069 / 0.694669 / 0.697326 / 0.696981 | 0.002656 | WITHIN NOISE |
| SINet \| NC4K | 0.002757 | 0.005514 | 0.766904 / 0.769013 / 0.767308 / 0.772315 | 0.005007 | WITHIN NOISE |
| SINet-v2 \| NC4K | 0.002781 | 0.005563 | 0.748613 / 0.749559 / 0.751399 / 0.753463 | 0.003904 | WITHIN NOISE |

**12 of 12 gaps WITHIN NOISE.** Largest anywhere **0.005007** (1.82 sigma_hat). The bar is
**3.24x tighter** than ABC's on SINet because T2's noise pool excludes the unstable A0 arm by
pre-registered definition. Directional note from the same file, reported despite non-significance:
**C10 — the real signal — has the highest arm mean in none of the four cells**, and CINV (maximally
anti-targeted) has it in three.

### 7.3 T2C — `rebuild/T2C/out/t2c_table.csv` (`primary = 1` rows only)

| Arch | Signal | rho(MAE) | rho(1-Sa) | rho(1-IoU) | ordering | seeds |
|---|---|---|---|---|---|---|
| SINet | ES | +0.6284 +/-0.0381 | +0.3433 +/-0.0301 | +0.2613 +/-0.0383 | PASS | 10/10 |
| SINet | entropy | +0.5892 +/-0.0368 | +0.4267 +/-0.0277 | +0.3588 +/-0.0351 | PASS | 10/10 |
| SINet | ensemble A0 | +0.6028 +/-0.0466 | +0.2698 +/-0.0487 | +0.1491 +/-0.0560 | PASS | 10/10 |
| SINet | ensemble CSHUF | +0.5212 +/-0.0564 | +0.4006 +/-0.0459 | +0.3361 +/-0.0447 | PASS | 10/10 |
| SINet-v2 | ES | +0.7070 +/-0.0404 | +0.5628 +/-0.0359 | +0.4591 +/-0.0315 | PASS | 10/10 |
| SINet-v2 | entropy | +0.7393 +/-0.0309 | +0.5404 +/-0.0408 | +0.4070 +/-0.0395 | PASS | 10/10 |
| SINet-v2 | ensemble A0 | +0.6191 +/-0.0675 | +0.5483 +/-0.0409 | +0.4540 +/-0.0451 | PASS | 9/10 |
| SINet-v2 | ensemble CSHUF | +0.5576 +/-0.0690 | +0.4488 +/-0.0580 | +0.3370 +/-0.0577 | PASS | 10/10 |

Whole-image ordering `rho(MAE) > rho(1-Sa) > rho(1-IoU)`: **8 / 8 PASS**. Boundary-restricted:
**2 / 8**, and four rows go negative (SINet-v2 ES boundary rho(MAE) = **-0.5485 +/-0.0745**, 0/10
seeds). The strong reading fails: rho(1-Sa) reaches **+0.5628** on SINet-v2, so *"uncertainty carries
no localisation information"* is false as stated. The claim is **ordinal and comparative only**.

### 7.4 B1 — `rebuild/B1/out/b1_faithful_correlation.json`, `dinoL518`

k = 75, 50 clusters used, 3428 target images in used clusters.

| Signal measured where | rho(MAE) | rho(1-Sa) | rho(1-IoU) | ratio (1-Sa)/MAE |
|---|---|---|---|---|
| **endpoint** ES (what B1 first measured) | +0.8754 | +0.3810 | +0.2304 | 0.4352 |
| **target** ES (what the pipeline actually has) | +0.6284 | +0.3433 | +0.2613 | **0.5463** |

`rho` drop from endpoint-measured to allocation-available = **+0.2470** on MAE.
`rho(target ES, endpoint ES)` per cluster = only **+0.5732**. The declared 0.5 "wrong-objective"
boundary lands on the **opposite side** on the real signal — B1's own headline framing is not
supported by the signal the method can actually compute.

Cluster structure, from `rebuild/B1/out/b1_embedder_sweep.json`: best silhouette is
**0.1600** (dinoL518, k=75); clipL224 peaks at **0.0568** at k=5, which is the **grid edge** and is
therefore disqualified as a selection.

### 7.5 C1 — `rebuild/C1/out/c1_attribution.csv`

The attribution ladder at `dinoL518 / R2_cut / B=250 / alpha=0.2`, read directly:

| Arm | `d_heldout` | what it destroys |
|---|---|---|
| TARGETED_by_target_es | 1.1135 | nothing — the real arm |
| shuffled_es | **1.1304** | targeting, keeps allocation shape |
| random_centroid | **1.2262** | targeting entirely — and scores **higher** |
| random_vs_random | **-0.0373** | everything — the true null |

Destroying the signal reproduces the headline separation. Campaign-wide paired increments
(`C1_RESULTS.md:206-211`): targeted minus shuffled = **+0.0073** of a `d`, winning **13/20** cells (a
coin flip); targeted minus arbitrary cluster = **-0.0649**, winning **4/20**. The declared ceiling is
a **concentration** ceiling, not a **targeting** ceiling.

### 7.6 A3 — `rebuild/A3/out/a3_coverage.csv` (k=5) and `a3_probe_table.csv`

Manifold coverage (recall against the real target set), read directly:

| Set | dinoL224 | dinoL518 | clipL224 |
|---|---|---|---|
| ceiling, random halves | 0.9332 | 0.9431 | 0.8931 |
| NC4K (a different real set) | 0.8874 | 0.8995 | 0.7921 |
| raw HKU-IS (LAKE-RED's own input) | 0.7473 | 0.7097 | 0.7470 |
| **authors' synthetic pool** | **0.4829** | **0.4834** | **0.1277** |
| relative loss vs its own input pool | **-35.4 %** | **-31.9 %** | **-82.9 %** |

**The vacuity exhibit**, read from `a3_probe_table.csv`. In `clipL224` the headline
real-vs-synthetic AUC is **0.9993** (authors' pool) / **0.9995** (local renders) — but a **JPEG-30
re-encode of the identical target images separates them from themselves at 0.9928**, i.e. within
**0.0067** of the headline, on content that is identical by construction. The floor ladder in that
space is 0.6266 / 0.8548 / 0.9690 / **0.9928** at JPEG-90 / 75 / 50 / 30. Separately, the estimator
itself manufactures effects: on `real vs real, RANDOM halves (true null)` the held-out `d` is
**0.0318** while the *in-sample* `d` on the same true null is **0.6867** (dinoL224). The coverage
finding survives; the AUC metric that used to carry it does not.

### 7.7 D1 — `rebuild/D1/out/d1_bijection.json`

`base_foregrounds 4447`, `auth_in_base 4447`, `auth_outside_base []`, `local_in_base 4447`,
`base_without_local []`, `is_bijection_auth true`, `is_bijection_local true`. Combined with
`--isReplace` compositing (`LAKE-RED/test.py:159-166`), **0 of 8885 traced objects across both pools
show any sign of having been regenerated rather than composited**. Every null in the paper is scoped
to an exhausted foreground pool.

---

## 8. Scope and confidence map (the two marking axes)

Because the repo's tier vocabulary is **scope**, the figures carry two independent marks. Neither is
invented: scope comes from the `TIER_SEGREGATION.md` §1 master table by finding number; confidence is
derived mechanically from whether a committed `EXP` block and a pre-registered threshold exist.

| Claim the figures make | Finding # | Scope badge | Confidence | Evidence |
|---|---|---|---|---|
| `total_step` pinned 253/127; added data buys 0 steps | 1 | `gen` | pre-registered | `EXP ABC` b2 @ `REBUILD_LOG.txt:1323` |
| Render set is a bijection; objects copied not generated | 2, 3 | `gen` -> `signal+data` | pre-registered | `EXP D1` @ `:696` |
| Delta(C-B) WITHIN NOISE, both archs, both endpoints | 8 | `gen` | pre-registered | `EXP ABC` b3 @ `:1376` |
| Campaign underpowered: 2 sigma_hat 0.017933 vs gap 0.0142 | 9 | `gen` | pre-registered | `EXP ABC` b3 |
| Target set has almost no cluster structure (silhouette 0.1600) | 15 | `signal+data` | pre-registered | `EXP B1` b3 @ `:922` |
| Pixel-over-structure ordering holds 8/8, three signals, two archs | 19 | `signal+data` | pre-registered | `EXP T2C` @ `:2550` |
| Magnitude does **not** generalise; rho(1-Sa) reaches +0.5628 | 20 | `signal+data` | pre-registered | `EXP T2C` |
| Allocation signal is weaker where it is actually available (+0.2470) | 21 | `signal+data` | pre-registered | `EXP B1` b4 @ `:990` |
| ES adds +0.0073 of a d over its own shuffle (13/20) | 22 | `signal+data` | pre-registered | `EXP C1` b4 @ `:1201` |
| Declared ceiling is a concentration ceiling, not a targeting ceiling | 23 | `signal+data` | pre-registered | `EXP C1` b4 |
| Real / destroyed / reversed targeting indistinguishable, 12/12 | 25 | `signal+data` | pre-registered | `EXP T2` b3 @ `:2452` |
| CHAMELEON 41/76 = 53.9 % re-encoded training data | 26, 27 | `indep` | pre-registered | `EXP D2` b5 @ `:600`; `EXP D2R` b4 @ `:1844` |
| 41 is a property of the data, not the cutoff (7.36x gap) | 28 | `indep` | pre-registered | `EXP D2R` b4 |
| No difficulty skew, so no inflation figure is defensible | 29 | `indep` | pre-registered | `EXP D2R` b4 |
| NC4K clean 0/4121, min nearest 3.44x tolerance | 31 | `indep` | pre-registered | `EXP D2_NC4K` b2 @ `:2074` |
| Unchecked is not clean: 73.7 % of NC4K unchecked | 32 | `indep` | pre-registered | `EXP D2_NC4K` b2 |
| Real-vs-synthetic AUC near 1.0 is near-vacuous (0.9928 floor) | 33 | `indep` (boundary) | pre-registered | `EXP A3` @ `:2147` |
| In-sample d manufactures +0.6991 on a true null | 34 | `indep` | pre-registered | `EXP C1` b4, reproduced in `EXP A3` |
| Synthetic pools cover the manifold at 0.13-0.54 vs real 0.71-0.90 | 36 | `gen` (boundary) | pre-registered | `EXP A3` |
| T2C boundary-inversion **mechanism** | — | `signal+data` | **POST-HOC — hatched** | self-labelled POST-HOC, `T2C_RESULTS.md:87` |
| A1's four conditioning routes | 7 | `gen` | **NO EXP BLOCK — excluded** | `FINAL_RESULTS.md:73,85` |

**Rendering rule.** Solid fill = `EXP` block + pre-registered threshold. Hatched fill = `EXP` block but
post-hoc reading. Dashed border = no `EXP` block, and **barred from both main figures**. Scope is a
small corner word, never a bare digit. Any `Delta` whose magnitude is inside `2 sigma_hat` is drawn as
**unresolved**, never as a win.

---

## 9. EXPERIMENT_TRIAGE

| Dir | Question it asked | What it measured | Headline outcome | Scope | Verdict |
|---|---|---|---|---|---|
| **D1** | What may any null be scoped to? | bijection counts; object-region vs background mean\|diff\| | Bijection 4447/4447, 0 outside, 0 unrendered; **0 of 8885** objects regenerated | `gen`->`signal+data` | **DIAGRAM** (~7 nodes) |
| **B1** | Does the ES signal predict endpoint error — and where is it available? | per-cluster Spearman rho; silhouette; seed/bootstrap ARI | rho(MAE) drops **+0.2470** from endpoint- to target-measured; ratio crosses the declared boundary; silhouette **0.1600** | `signal+data` | **DIAGRAM** |
| **C1** | Is a targeted allocation actually different from a random one? | held-out Cohen's d against four measured nulls | Separation `d ~ 1.1` **reproduced with the signal destroyed**; ES adds **+0.0073** (13/20) | `signal+data` | **DIAGRAM** — best control lattice in the repo |
| **ABC** | Does concentrated allocation beat random? | `S_alpha`, `sigma_hat`, five gaps x four cells | `Delta(C-B)` **WITHIN NOISE** in 4/4; archs disagree on sign; underpowered against its own statement | `gen` | **DIAGRAM** |
| **T2** | Does the ES signal's *direction* do anything to accuracy? | same, arms C10 / CSHUF / CINV at exactly fixed concentration | **12/12 WITHIN NOISE** at a bar **3.24x** tighter | `signal+data` | **DIAGRAM** |
| **T2C** | Is the pixel-over-structure gap specific to ES? | Spearman rho for 3 signals x 2 aggregations x 2 archs | whole **8/8 PASS**; boundary **2/8**, four rows invert; strong reading refuted | `signal+data` | **DIAGRAM** |
| **D2 + D2R + D2_NC4K** | Is CHAMELEON re-encoded training data — and does the detector find contamination everywhere? | near-duplicate cascade; tolerance sweep; nearest-neighbour gap | 41/76 = **53.9 %**, saturating at tol 6.0; author-sourced copy identical; NC4K **0/4121** | `indep` | **MERGE -> `fig:exp:d2`**, 3 panels |
| **A3** | How far do the synthetic images sit from the real target? | k-NN coverage precision/recall; probe AUC; MMD2 | coverage **0.13-0.54** vs real **0.71-0.90**; but AUC is near-vacuous (**0.9928** floor) | `gen` (boundary) + `indep` | **DIAGRAM** |
| **E0** | Can every shared input be rebuilt from primary data? | 48,365 SHA-256 hashes; byte-identity of regeneration | 16/16 PASS; **4447/4447 byte-identical**; 5.4 % cluster-membership instability | `gen` + `signal+data` | **TABLE** — a provenance record with no branching structure. Its two substantive numbers are routed: the `isReplace` split into D1, the 5.4 % instability into B1 |
| **A1** | Is the conditioning channel a narrow bottleneck? | source reading; one weight-norm ratio | Hypothesis **withdrawn**; 4 routes found | `gen` | **SKIP** — zero `EXP` blocks; *"No number in this document enters `results/REBUILD_LOG.txt`"*. Cannot carry a results-grounded diagram |
| C2, A2, B2, B3, C3 | — | — | — | — | **SKIP** — declared unrun (`REBUILD_FINDINGS.md:150`) |

**Eight figures, not eleven.** E0 and A1 are argued out above rather than padded in; D2_NC4K has no
results markdown and is structurally D2's negative control, so it is a panel, not a figure.

---

## 10. FIGURE_PLAN

Page budget: `\textwidth` = **5.5 true in = 396 bp** and `\textheight` = **9.0 true in**, read from
`iclr2027/iclr2027_conference.sty:48-49`. Single column (no `\twocolumn` in the `.sty`; the class is
plain `article`). Nothing is wrapped in `\resizebox`.

### 10.1 `fig:method` — main text, full 5.5 in

```
 +-- OFFLINE / FROZEN -------------------------------------+
 | HKU-IS 4447 --(image, inverted mask)--> [LAKE-RED]       |   frozen: eval() + no_grad() + ema_scope()
 |   raw fg          50 DDIM steps, --isReplace             |   ckpt LAKERED.ckpt, --seed 0
 |                          |                               |   !! 0 of 8885 objects regenerated
 |                          v   render pool 4447            |
 +--------------------------|-------------------------------+
                            |
 Target 4040 --> [ES] --> [k-means k=75] --> [softmax a=1] --> [budget B=1000] --> [rank+select]
 (unlabelled)     ^                                                                     |
                  |                                                                     v
                  |                                        base 4447 + 1000 --> ARM POOL 5447
                  |                                                                     |
                  |                                                                     v
                  |                         +--- total_step PINNED 253/127 -------------+
                  |                         |    19,734 steps, 315,744 imgs, ANY pool size
                  |                         v
                  |                   [ROUND 1: student + EMA teacher, lambda=0.996 ]
                  |                         |    L = L_sup + L_ES   (unweighted)
                  |                         v
                  +---- CLS pseudo-label ---+   edge_loss < 0.8*avg ; tau=0.4
                        (THE ONLY FEEDBACK EDGE - carries target images, not renders)
                                            |
                                            v
                        [ROUND 2: models REBUILT from ImageNet weights]
                                            |
                                            v
                        Tea_epoch_best <-- selected on CAMO 250 (selection only, NEVER an endpoint)
                                            |
                        +-------------------+-------------------+
                        v                                       v
                  COD10K-test 2026                        NC4K 4121
                  (primary)                               (secondary)
                        [ CHAMELEON 76 --- WITHDRAWN, 41/76 = 53.9% ]
```

~22 nodes. Shape carries kind (rectangle = data object, rounded = operator); border carries training
status (solid = trained, double = frozen, dotted = deterministic). The feedback edge is the only
dashed accent-coloured path and is labelled with what it carries. Justification: this is the system
**under test**. Every annotation is a measured constraint on what the loop could possibly do, placed
at the stage where it was measured, so a reviewer reading only Figure 1 already knows why the result
is a null and cannot mistake the offline generator path for a closed loop.

### 10.2 `fig:results` — main text, option (B) ablation flow

```
                                   BASE POOL 4447  +  FIXED BUDGET 19,734 steps
                                              |
   which embedder?  B1: dinoL518, silhouette 0.1600 (weak structure)  ......... [fig:exp:b1]
   targeting or concentration?  C1: signal adds +0.0073 of a d (13/20) ........ [fig:exp:c1]
                                              |
        +--------+--------+--------+----------+----------+
        v        v        v        v          v          v
       A0       A2        B       C10       CSHUF      CINV
      4447     5447     5447     5447       5447       5447
    unpadded  authors' random   ES-target  shuffled   reversed
    UNCLEAN   dupes    draw     = "Ours"   (destroyed)(reversed)
        |        |        |        |          |          |
        v        v        v        v          v          v
   S_alpha    .7077    .7134    .7185      .7170      .7193      SINet | COD10K
    .7010       |        |        |          |          |
                +--------+---+----+----------+----------+
                             |
                   |<-- 2 sigma_hat = 0.0179 (ABC) -->|   Delta(C-B) = +0.0050  WITHIN NOISE
                        |<-- 2 sigma_hat = 0.0055 (T2) -->|  12/12          WITHIN NOISE
                             |
              VERDICT: real, destroyed and reversed targeting are indistinguishable
```

~20 nodes plus a 2-sigma band. Justification: there is no working configuration to instantiate, so
option (A) would imply a selection the evidence does not support. The falsification arms **are** the
argument, and a branch diagram is the only layout that puts C10, CSHUF and CINV at the same visual
rank — which is exactly the claim. Fed by `fig:exp:{abc,t2,c1,b1}`; caption `\ref`s the appendix-only
`fig:exp:{d1,d2,a3,t2c}`.

### 10.3 Per-experiment template — four zones, identical across all eight

```
+============================================================+
| QUESTION  (one line, from the PREREGISTRATION, not results)|
+------------------------------------------------------------+
| SETUP        | MEASUREMENT                                  |
|  inputs      |   metric named exactly as in Eval/metrics.py |
|  manipulation|   n, seeds, aggregation                      |
|  held fixed  |                                              |
+------------------------------------------------------------+
| OUTCOME   effect size +/- spread, n_seeds, scope badge,     |
|           confidence fill, and PLAINLY whether it refuted   |
+============================================================+
```

<= 0.30 `\textheight`, 6-12 nodes, one column width. Labels `fig:exp:<dir>`.

| Figure | Panels | Est. nodes | Placement |
|---|---|---|---|
| `fig:exp:abc` | 1 | 11 | main-text feed |
| `fig:exp:t2` | 1 | 10 | main-text feed |
| `fig:exp:c1` | 1 | 9 | main-text feed |
| `fig:exp:b1` | 1 | 10 | main-text feed |
| `fig:exp:d2` | 3 (a) D2 (b) D2R (c) NC4K | 12 | appendix |
| `fig:exp:t2c` | 1 | 11 | appendix |
| `fig:exp:a3` | 2 (a) coverage ladder (b) AUC vacuity | 12 | appendix |
| `fig:exp:d1` | 1 | 7 | appendix |

---

## 11. OPEN_QUESTIONS

Answered in the approved plan; recorded here for the audit trail. Defaults were taken on all eight.

1. Two-axis marking (scope word + confidence fill) instead of a single "tier"? -> **yes**
2. Generator drawn offline/frozen/one-shot, "feedback" reserved for the CLS edge? -> **yes**
3. Greyscale-safe primary channel, colour as redundant reinforcement? -> **yes**
4. E0 -> TABLE, numbers routed into D1 and B1? -> **yes**
5. D1 at ~7 nodes, below the 6-12 target? -> **yes**
6. `rebuild/PAPER/main.tex` as advisory terminology cross-check only? -> **yes**
7. NC4K `A0->C10` REAL EFFECT drawn as a marked non-supporting artifact? -> **NO (author decision,
   2026-09-12): excluded from every figure; recorded in `FIGURE_EVIDENCE.md` as an excluded row**
8. SINet as the headline arch, SINet-v2 as a second row? -> **yes**

### Residual discrepancies found while compiling this spec (recorded, not fixed)

1. **Stale line citations in committed code comments.** `rebuild/B1/b1_es_error_correlation.py:63-64`
   and the task brief both cite `MyTrain.py:221` for CAMO checkpoint selection; the live line is
   **`MyTrain.py:223`**. `rebuild/ABC/abc_train.py:301` cites `MyTrain.py:306-307` for `total_step`;
   the live lines are **325-327**. Figures will cite live line numbers.
2. **`target_es` is SINet/S2C's ES for every architecture** (`b1_allocation_signal.py:283`), so the
   SINet-v2 arms were allocated by SINet's uncertainty. Disclosed at `FINAL_RESULTS.md:1740-1746`.
   This must appear on `fig:exp:b1` and `fig:exp:t2`.
3. **`Eval/Eval/eval_txt/` files exist in two different column orders.** Never parse positionally.
4. **`figures/` is untracked but not gitignored**; `iclr2027/` and `rebuild/PAPER*` are gitignored.

---

**PHASE 0 COMPLETE — awaiting approval.** No `.tex` written. On approval the order is:
`s2rcod_style.tex` -> `collect_figure_data.py` -> the eight per-experiment figures one at a time
(status checkpoint after D1/B1/C1 and after ABC/T2/T2C) -> `fig:results` -> `fig:method` ->
verification and `FIGURE_EVIDENCE.md`.

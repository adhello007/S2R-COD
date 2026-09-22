# Supplementary material

This is the code and evidence package for the submission *Concentration, Not Targeting: A
Pre-Registered Null for Uncertainty-Guided Synthetic Data in Camouflaged Object Detection*.

The paper reports a negative result: allocating a fixed synthetic-generation budget toward the
clusters a detector is worst on does not beat allocating it at random, once you hold the *shape* of
the allocation fixed. A package accompanying a null has a particular burden — it has to show the
null was not simply a failure to look carefully. So the organising idea here is that every number in
the paper was written down by a script, into an append-only log, under a rule that was committed
before the run that produced it.

You do not have to take that on trust. It is checkable from this directory.

---

## Start here

Two files carry the story.

**`results/REBUILD_LOG.txt`** is the append-only measurement log — one block per accepted run,
stamped with an ISO timestamp, the commit sha, and whether the tree was clean. Each block records
the exact command (`CMD`), the environment, the metrics, the declared threshold and its PASS/FAIL,
the artifacts written, and whether the experiment trained anything. Its own header states the rule
it was kept under: *no number appears in any document before it appears here.*

**`NAVIGATION.md`** maps every experiment to its directory, its log blocks and its readable results
file.

One rule governs the whole package, and every results document repeats it:

> **If a results markdown and its log block ever disagree, the log wins.**

---

## What you can run right now, with none of our data

Three things, on a laptop, in under a minute each. These are the fastest way to confirm the package
is real rather than decorative.

```bash
# 1. The contamination detector, against its own known-answer fixtures.
#    Eight assertions, no project data touched.
python rebuild/D2_reaudit/detect_contamination.py --self-test

# 2. The area control. Inference-free, no GPU: it reads committed artifacts
#    and re-derives the table in rebuild/AC/out/.
python rebuild/AC/ac_measure.py --no-log

# 3. Regenerate the consolidated results document from committed artifacts.
python rebuild/FinalPaper/make_results.py
```

The detector is also the one piece meant to be useful on its own. Point it at any two image
directories and it will find re-encoded duplicates between them:

```bash
python rebuild/D2_reaudit/detect_contamination.py <DIR_A> <DIR_B>
```

`rebuild/D2_reaudit/release/` holds that tool packaged standalone, with the leaked-image list, the
clean-evaluation protocol, and a README written for someone outside this project.

---

## What needs the datasets

Everything else reads images. The datasets are public but large, and we cannot redistribute them.

| Role | Set | Count | Expected path |
|---|---|---|---|
| Source (synthetic) | HKU-IS, LAKE-RED-composited | 4447 pairs | `Dataset/Source/HKU-IS/{Image,GT}` |
| Source (raw SOD) | HKU-IS raw | 4447 | `Dataset/Source/HKU-IS_raw/{imgs,gt}` |
| Target (unlabelled) | COD10K-train 3040 + CAMO 1000 | 4040 | `Dataset/Target/Image` |
| Test endpoint | COD10K-test | 2026 | `Dataset/Test/COD10K/{Imgs,GT}` |
| Test endpoint | NC4K | 4121 | `Dataset/Test/NC4K/{Imgs,GT}` |
| Checkpoint selection | CAMO | 250 | `Dataset/Val/CAMO/{Imgs,GT}` |
| Withdrawn endpoint | CHAMELEON | 76 | `Dataset/Test/CHAMELEON/{Imgs,GT}` |

`rebuild/common.py` declares this table machine-readably, with the expected count and image
representation for each, and every rebuild script checks against it rather than trusting a path.
`rebuild/E0/out/e0_manifest.sha256` hashes every primary input, so you can confirm you hold the same
bytes we did before comparing any number.

COD10K, CAMO, NC4K and HKU-IS are obtained from their original authors. The upstream S2R-COD
repository additionally distributes packaged copies of the source and target pools.

**CHAMELEON is included in the table only because the paper withdraws it.** See below.

## What we cannot ship, and where to get it

| Missing | Size | How to obtain |
|---|---|---|
| `Dataset/` | ~233 GB | public sources above |
| `Snapshot/**/*.pth` — trained checkpoints | ~285 GB | retrain; every command is in `rebuild/ABC/out/abc_commands.txt` |
| `Result/` — predicted masks | ~18 GB | regenerate with `MyTest.py` |
| ImageNet backbones (ResNet-50, Res2Net-50) | ~200 MB | standard public weights; `preflight.py` checks for them |
| LAKE-RED generator + `LAKERED.ckpt` | ~6 GB | the LAKE-RED project |

What *is* shipped for the training runs: the exact commands, the pool manifests, the per-run
training logs (`Snapshot/ABC/<runid>/training_log.log`, 106 of them), and the per-run metrics
(`rebuild/ABC/out/abc_metrics.csv` and siblings). You can audit what happened without rerunning it.

---

## Environment

```bash
uv sync          # Python 3.12, torch 2.11 + cu128
```

**There are two virtualenvs, and it matters which you use.** The detector, analysis and audit
scripts run under the root `.venv`. Scripts that touch the generator or DINOv2 embeddings run under
`LAKE-RED/.venv`, which carries the diffusion stack. Each script's docstring states which. The
machine we measured on is recorded in `rebuild/E0/out/e0_environment.json`.

`preflight.py` is the gate before any training run — it checks the environment, the backbone
weights, the dataset layout and integrity, output paths, config coherence, and runs a real
forward/backward smoke test. Exit 0 means clear to train.

---

## Hazards a reproducer will actually hit

These cost us real time. They are documented here so they do not cost you any.

- **Never run SINet and SINet-v2 training concurrently against the same source root.** Both write
  `<source_root>_iteration2/`, and `CLS.py` deletes that directory on entry. Every campaign arm gets
  its own `--source_root` for this reason.
- **Checkpoints can load silently wrong.** `Explanations/CHECKPOINT_LOADING_BUG.md` documents an
  evaluation that returned Sα 0.2816 against a target of 0.6845 because `MyTest.py` had quietly
  evaluated a randomly initialised network. `MyTest.py` now asserts every tensor was copied.
- **The dataloader pairs images to masks by sorted index, not by filename**
  (`Src/utils/Dataloader.py`). A missing mask silently shifts every subsequent pair.
  `preflight.py` checks for this explicitly.
- **`--task S2C` overwrites the loss hyperparameters** you pass on the command line
  (`MyTrain.py`, post-parse). This is the upstream behaviour, kept deliberately.
- **Learning-rate decay compounds** in `Src/utils/tool.py:adjust_lr`.
- Image roots must end in a trailing slash; paths are concatenated, not joined.

`Experiments/SINETV2/run_commands.txt` is the most detailed worked example: preflight, train,
archive the round-2 pool, infer, evaluate, sanity-check the masks, with the expected healthy
statistics at each step.

---

## Reading the run names

A run id is `<architecture>_<arm>_s<seed>`, so `SINetv2_CSHUF_s48` is SINet-v2, the shuffled-signal
arm, seed 48. Canonical definitions are in `rebuild/ABC/abc_common.py`.

| Arm | What it is |
|---|---|
| `A0` | base pool alone. An *unclean* control — it differs from the others in pool size too. |
| `A2` | base pool + the 1000 original photographs that arm B's renders were made from. Separates pool size from generated content. |
| `B` | base pool + 1000 renders drawn uniformly at random, redrawn per seed. The honest baseline. |
| `C10` | base pool + the 1000 chosen by the uncertainty allocation. The digits are the softmax temperature: `C10` = α 1.0. |
| `CSHUF` | the allocation with per-cluster scores permuted across clusters. **Destroys targeting, preserves allocation shape exactly.** |
| `CINV` | the allocation with scores rank-reversed. Maximally anti-targeted. |
| `CORACLE` | scores replaced by ground-truth per-cluster error. A declared diagnostic upper bound, never a method. |
| `*FX` suffix | same pool, but the step schedule unpinned (`--exposure fixed_exposures`). |
| `MT` | mean-teacher positive control. |

`CSHUF` and `CINV` are the falsification arms and the heart of the paper: if the uncertainty signal
carried information beyond the concentration of the allocation, destroying or reversing it should
cost something. It does not.

Campaign codes: **ABC** main four-arm · **T2** same-shape falsification · **T2C** signal generality ·
**AC** area control · **PC** positive control · **OR** oracle · **FX** schedule · **SE** seed
expansion · plus the earlier audits **E0, D1, D2, D2R, D2_NC4K, A1, A3, B1, C1** and the post-hoc
**DIAG**.

---

## Scope — what this package does not claim

Each of these is argued where it was decided; none is re-argued here.

- **CHAMELEON is withdrawn as an evaluation endpoint.** We measure that a majority of it consists of
  re-encoded copies of images in the COD10K-train split that the models train on. A CHAMELEON column
  reported for such a model is not an independent measurement. CAMO is used for checkpoint
  selection, never as an endpoint. See `rebuild/D2_reaudit/`.
- **The null is scoped to an exhausted foreground pool** — see `rebuild/D1/D1_RESULTS.md`.
- **A3 characterises the synthetic-vs-real distribution. It is not a training-utility bound** and
  must not be read as one.
- **The comparison tests concentration-driven targeting, not the uncertainty signal in isolation** —
  see `rebuild/C1/C1_RESULTS.md` §8.
- **Stage C's added images were trained on, not excluded.** The mechanism is dilution of per-epoch
  exposure under a fixed step budget. See `rebuild/ABC/POOL_MECHANICS_AUDIT.md`.
- Byte-identical regeneration was established **on one machine with one software stack**. It is not
  a claim of determinism across hardware or driver versions.
- A render is a function of its foreground, its mask, **and its position within the processing
  shard** — changing the shard count changes the outputs even at a fixed seed.

---

## Anonymity

This package is anonymous supplementary material. Two mechanical substitutions were applied to it
and nothing else:

- absolute filesystem paths became `<REPO>` and `<HOME>`;
- author-identifying tokens that appeared *inside* two evidence files became `<author-given-name>`
  and similar placeholders. Those files — the re-audit script's pattern list and the log lines
  echoing it — record that an anonymisation scan was run and what it searched for. The fact of the
  scan is evidence worth keeping; the names in it are not, so the names are redacted and the
  structure is left intact.

`results/REBUILD_LOG.txt` carries a note at its end recording both substitutions and confirming that
no timestamp, commit sha, metric, threshold, verdict or artifact name was altered. That note exists
because the log is append-only, and silently rewriting it would be a defect under its own rules.

The scanner that gates this and the script that builds the package are not included, because their
pattern lists necessarily contain the very identifiers they search for. They will accompany the
de-anonymised release.

`LICENSE` is the MIT notice of the upstream S2R-COD repository this work builds on, preserved
verbatim as that licence requires. It is not the submitting authors' name.

## Attribution

This work builds on the S2R-COD repository (Luo et al., ACM MM 2025), the LAKE-RED generator (Zhao
et al.), the SINet and SINet-v2 detectors, and the DGNet evaluation protocol. All are cited in the
paper, and third-party attribution headers are preserved in the files that carry them.

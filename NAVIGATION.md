# NAVIGATION.md — how to find things in this evidence package

## 1. Start here

Two things carry the whole story.

### `results/REBUILD_LOG.txt` — the append-only source of truth


Two things to know before searching it. Several blocks share one `EXP <id>` — either re-runs
(E0, D2, B1, C1, D2R, D2_NC4K) or declared stages (ABC's three).

And the log is strictly chronological, not dependency-ordered

### The per-experiment `*_RESULTS.md` files — the readable reading of each block

Each names the exact block timestamp it reads. The per-experiment convention is
`<ID>.md` = **setup** (scripts, directories, thresholds declared in advance — no numbers),
`<ID>_RESULTS.md` = **verified results**.

| Experiment | Setup | Verified results |
|---|---|---|
| E0 | [rebuild/E0/E0.md](rebuild/E0/E0.md) | [rebuild/E0/E0_RESULTS.md](rebuild/E0/E0_RESULTS.md) |
| D2 | [rebuild/D2/D2.md](rebuild/D2/D2.md) | [rebuild/D2/D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) |
| D2_nc4k | [rebuild/D2_nc4k/README.md](rebuild/D2_nc4k/README.md) | *(none — see §2)* |
| D2_reaudit | [rebuild/D2_reaudit/REAUDIT_PLAN.md](rebuild/D2_reaudit/REAUDIT_PLAN.md) | [rebuild/D2_reaudit/D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) |
| D1 | [rebuild/D1/D1.md](rebuild/D1/D1.md) | [rebuild/D1/D1_RESULTS.md](rebuild/D1/D1_RESULTS.md) |
| B1 | [rebuild/B1/B1.md](rebuild/B1/B1.md) | [rebuild/B1/B1_RESULTS.md](rebuild/B1/B1_RESULTS.md) |
| C1 | [rebuild/C1/C1.md](rebuild/C1/C1.md) | [rebuild/C1/C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) |
| A3 | [rebuild/A3/A3.md](rebuild/A3/A3.md) | [rebuild/A3/A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) |
| ABC | [rebuild/ABC/ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md) | [rebuild/ABC/ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) |

> **The rule to trust: if a results markdown and its log block ever disagree, the log wins.**
> Each `*_RESULTS.md` states this itself.

---

## 2. The experiment map

In dependency order. One line each; the numbers are in the log block and the readable file.

| Experiment | What it establishes | Log block | Readable file | Key artifacts |
|---|---|---|---|---|
| **E0** | Regenerates every input from primary data and hashes it, so later experiments read a verified manifest rather than the old package | `EXP E0` ×4 | [E0_RESULTS.md](rebuild/E0/E0_RESULTS.md) | [rebuild/E0/out/](rebuild/E0/out/) |
| **D2** | Whether the CHAMELEON evaluation set overlaps the COD10K-train split the models train on | `EXP D2` ×5 | [D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) | [rebuild/D2/out/](rebuild/D2/out/) |
| **D2_nc4k** | Whether NC4K collides with COD10K-test — i.e. whether the second endpoint is independent | `EXP D2_NC4K` ×2 | *setup only:* [README.md](rebuild/D2_nc4k/README.md) | [rebuild/D2_nc4k/out/](rebuild/D2_nc4k/out/) |
| **D2_reaudit** | Re-runs the CHAMELEON audit against an author-sourced copy of the dataset, and releases the detector | `EXP D2R` ×4 | [D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) | [out/](rebuild/D2_reaudit/out/), [release/](rebuild/D2_reaudit/release/) |
| **D1** | Whether the source foreground pool is exhausted, and for the pool that actually feeds training | `EXP D1` ×1 | [D1_RESULTS.md](rebuild/D1/D1_RESULTS.md) | [rebuild/D1/out/](rebuild/D1/out/) |
| **B1** | Whether the ES allocation signal is valid, which clusters are weak, and how the choice of embedder moves both | `EXP B1` ×4 | [B1_RESULTS.md](rebuild/B1/B1_RESULTS.md) | [rebuild/B1/out/](rebuild/B1/out/) |
| **C1** | Targeted-vs-random pool distance, plus the attribution audit of what actually produces the separation | `EXP C1` ×4 | [C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) | [rebuild/C1/out/](rebuild/C1/out/) |
| **A3** | How far the generator's synthetic renders sit from the real target distribution, with real-vs-real controls | `EXP A3` ×1 | [A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) | [rebuild/A3/out/](rebuild/A3/out/) |
| **ABC** | The 3-seed A/B/C/A2 training campaign — the measured verdict against the pre-registered rule | `EXP ABC` ×3 | [ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) | [rebuild/ABC/out/](rebuild/ABC/out/) |

**D2_nc4k has no results markdown.** Its `README.md` is setup only and says so; its numbers live in
the `EXP D2_NC4K` block, and its NC4K/COD10K-test rows are reported in
[CLEAN_PROTOCOL.md](rebuild/D2_reaudit/CLEAN_PROTOCOL.md).

---

## 3. Where the headline contributions live

### 3.1 The measured negative result — the A/B/C campaign

| File | What it is |
|---|---|
| `EXP ABC` block 1 of 3 — `2026-09-04T23:36:25+05:30` | Pre-flight: pool construction and the gates that had to pass before training |
| `EXP ABC` block 2 of 3 — `2026-09-05T22:56:22+05:30` | Run accounting: the 24 runs, wall clock, per-arm appends. The first block in the rebuild with `TRAINS YES` |
| `EXP ABC` block 3 of 3 — `2026-09-06T13:37:26+05:30` | The verdict |
| [rebuild/ABC/PREREGISTRATION.md](rebuild/ABC/PREREGISTRATION.md) | The decision rule, committed before run 1 and never edited after any number existed |
| [rebuild/ABC/out/abc_metrics.csv](rebuild/ABC/out/abc_metrics.csv) | Per-run, per-endpoint metrics — the raw table behind the verdict |
| [rebuild/ABC/out/abc_verdict.json](rebuild/ABC/out/abc_verdict.json) | The pre-registered rule applied, machine-readable |
| [rebuild/ABC/out/abc_sigma.json](rebuild/ABC/out/abc_sigma.json) | The seed-spread estimate the verdict is judged against |
| [rebuild/ABC/POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) | How Stage C's added images enter training and why the step budget cannot grow — see §3.4 |

Also in that directory: `abc_preflight.json`, `abc_pools.json`, `abc_runs.csv`, `abc_discards.json`
(discarded-and-re-run runs), `abc_commands.txt` (exact commands).

### 3.2 The synthetic-vs-real coverage finding (A3)

| File | What it is |
|---|---|
| `EXP A3` block — `2026-09-08T10:34:47+05:30` | Authoritative record, single block |
| [rebuild/A3/A3_RESULTS.md](rebuild/A3/A3_RESULTS.md) | The reading of it, with the scope caveat stated up front |
| [rebuild/A3/out/a3_coverage.csv](rebuild/A3/out/a3_coverage.csv) | Coverage — precision/recall against the real set, per embedder and *k* |
| [rebuild/A3/out/a3_probe_table.csv](rebuild/A3/out/a3_probe_table.csv) | The AUC ladder: headline separation plus the real-vs-real and quality-sweep controls |
| [rebuild/A3/out/a3_distance.csv](rebuild/A3/out/a3_distance.csv) | MMD² and effective-rank table |
| [rebuild/A3/out/a3_decision.json](rebuild/A3/out/a3_decision.json) | Declared thresholds resolved to PASS/FAIL |
| [rebuild/A3/A3_SCOPING.md](rebuild/A3/A3_SCOPING.md) | Six open questions resolved against committed artifacts *before* any A3 code was written |

### 3.3 The benchmark-contamination contribution (D2 + D2_reaudit)

**This contribution stands independently of whether the method worked.**

| File | What it is |
|---|---|
| `EXP D2` ×5 blocks | The original audit on the local dataset copy |
| `EXP D2R` ×4 blocks (the fourth is the one cited) | The re-audit against an author-sourced copy |
| [rebuild/D2/D2_RESULTS.md](rebuild/D2/D2_RESULTS.md) | Readable reading of the D2 blocks |
| [rebuild/D2_reaudit/D2R_RESULTS.md](rebuild/D2_reaudit/D2R_RESULTS.md) | Readable reading of the re-audit, including where it corrects D2 |
| [rebuild/D2_reaudit/detect_contamination.py](rebuild/D2_reaudit/detect_contamination.py) | The released detector |
| [rebuild/D2_reaudit/out/chameleon_contaminated.json](rebuild/D2_reaudit/out/chameleon_contaminated.json) | The leaked-image list |
| [rebuild/D2_reaudit/CLEAN_PROTOCOL.md](rebuild/D2_reaudit/CLEAN_PROTOCOL.md) | Which evaluation columns can be reported as independent measurements, and which cannot |
| [rebuild/D2_reaudit/release/](rebuild/D2_reaudit/release/) | Self-contained bundle: `README.md`, `detect_contamination.py`, `chameleon_contaminated.json`, `CLEAN_PROTOCOL.md` |

Start with [release/README.md](rebuild/D2_reaudit/release/README.md) — it is written for someone
outside this project.

### 3.4 Pool mechanics — CSRDA Stage C additions and the `total_step` ceiling

The claim under test: *Stage C's added generations cannot expand the optimization budget and can
only rearrange the mixture within it.* The audit traces pool assembly, ordering, sampling and
`zip()` truncation across both CSRDA rounds, and reports where the usual framing of that claim is
wrong — see its **verdict up front**, §7(a) for the corrected one-sentence statement, and §7(c)
for whether it moves the ABC null.

**This is a code trace, not a measured experiment: it has no `EXP` block of its own, and says so.**
Its evidence is `file:line` citations into the real training code, its probe, and the already
committed `abc_runs.csv` — so the §1 rule is not violated. The measured half of the claim is the
`total_step` threshold in **`EXP ABC` block 2 of 3**.

| File | What it is |
|---|---|
| [rebuild/ABC/POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) | The audit. §1 loader construction and shuffling, §2 what `zip()` truncation does, §3 where Stage C's re-renders sit, §4 what CLS appends for round 2, §5–6 synthesis and cross-check, §7 closing statements, Appendix: defects found while tracing |
| [rebuild/ABC/pool_mechanics_probe.py](rebuild/ABC/pool_mechanics_probe.py) | Probe of record — self-contained, repo-relative. `.venv/bin/python rebuild/ABC/pool_mechanics_probe.py` |
| `EXP ABC` block 2 of 3 — `THRESHOLD` on `total_step` | The measured confirmation that the step budget stayed pinned in both rounds of every run |
| [rebuild/ABC/out/abc_runs.csv](rebuild/ABC/out/abc_runs.csv) | Per-run pool sizes and round-2 append counts the audit's arithmetic reads |
| [MyTrain.py](MyTrain.py), [Src/utils/Dataloader.py](Src/utils/Dataloader.py), [CLS.py](CLS.py) | The code under trace, byte-identical to what the 24 runs executed (the audit records the `git diff` check) |

---

## 4. The planning and audit-trail documents

| File | What it contains |
|---|---|
| [REBUILD_PLAN.md](REBUILD_PLAN.md) | The pre-registered plan: clean-slate rules (§0), the discarded-assumptions log (§0.2), data-provenance map (§1), representation table (§2), per-experiment deliverables (§2.5), experiment list (§3), and the frozen record of old claims (§4) |
| [REVISION_TABLE.md](REVISION_TABLE.md) | Every place a rebuilt number differs from the old package, with the reason and the log block that produced it; also tracks which experiments remain outstanding |
| [ABC_SCOPING.md](ABC_SCOPING.md) | Pre-execution scoping audit for the A/B/C campaign; flags where the brief's premises were wrong |
| [rebuild/ABC/ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md) | The campaign specification, approved before any ABC code existed |
| [rebuild/A3/A3_SCOPING.md](rebuild/A3/A3_SCOPING.md) | A3's scoping pass |
| [rebuild/C1/C1_PLAN.md](rebuild/C1/C1_PLAN.md) | C1's plan |
| [rebuild/D2_reaudit/REAUDIT_PLAN.md](rebuild/D2_reaudit/REAUDIT_PLAN.md) | The re-audit's setup document (it serves as D2R's `<ID>.md`; there is no `D2R.md`) |

---

## 5. How to reproduce a number

Every experiment is one directory, `rebuild/<EXP>/`, holding its script(s), its `out/` artifacts,
and — where it declares one — its setup and results markdowns. Each has a matching `EXP <EXP>`
block in [results/REBUILD_LOG.txt](results/REBUILD_LOG.txt) whose `CMD` field is the exact command
that produced it and whose `ARTIFACTS` field names the files it wrote; the readable `*_RESULTS.md`
cites that block by timestamp. Shared helpers are in [rebuild/common.py](rebuild/common.py). Large
binaries — embeddings and caches, regenerated renders, duplicate/pair image exports, inference
output, checkpoints, run logs — are gitignored and regenerable by the experiment that owns them
(`.gitignore` marks each as regenerable, and names the regenerating script for the bulky image
exports), and the primary inputs they derive from
are verified by hash against
[rebuild/E0/out/e0_manifest.sha256](rebuild/E0/out/e0_manifest.sha256). **`./Result/` — the model
predictions — is excluded from what is shared** (gitignored, and large); nothing in this document
depends on it. The `rebuild/` directory is being sent separately.

---

## 6. What is NOT here — scope caveats

Each is documented where it was decided; none is re-argued here.

- **CHAMELEON is withdrawn as an endpoint**, and CAMO is the checkpoint-selection set, not an
  endpoint — see [D2_RESULTS.md](rebuild/D2/D2_RESULTS.md), the `EXP D2` / `EXP D2R` blocks, and
  the input table in [ABC_PLAN.md](rebuild/ABC/ABC_PLAN.md).
- **Any null is scoped to an exhausted foreground pool** — see
  [D1_RESULTS.md](rebuild/D1/D1_RESULTS.md).
- **A3 characterizes the distribution; it is not a training-utility bound** and must not be read as
  one — stated in the `EXP A3` block's `NOTES` and at the top of
  [A3_RESULTS.md](rebuild/A3/A3_RESULTS.md).
- **The A/B/C comparison tests concentration-driven targeting, not the uncertainty signal in
  isolation** — see the attribution audit in [C1_RESULTS.md](rebuild/C1/C1_RESULTS.md) §8 and
  [rebuild/C1/out/c1_attribution.csv](rebuild/C1/out/c1_attribution.csv).
- **The campaign's power against its own pre-registered statement** is discussed in
  [ABC_RESULTS.md](rebuild/ABC/ABC_RESULTS.md) and quantified by
  [abc_sigma.json](rebuild/ABC/out/abc_sigma.json).
- **Stage C's added images were trained on, not excluded** — the mechanism is dilution of
  per-epoch exposure under a fixed step budget, and A0 is an unclean control in both rounds. See
  [POOL_MECHANICS_AUDIT.md](rebuild/ABC/POOL_MECHANICS_AUDIT.md) §7(a) and §7(c).
- **Experiments not run:** A1, A2, B2, B3, C3 remain outstanding, and C2 has no `EXP C2` block of
  its own — see the status line and its note at the top of
  [REVISION_TABLE.md](REVISION_TABLE.md).

# ICLR 2027 anonymous supplement for the S2R-COD uncertainty-guided-generation work

## Status — updated 2026-09-22

**Phases 1-3 complete. The package builds, gates clean and verifies from a fresh extraction.**

| | |
|---|---|
| Artifact | `s2r-cod-supplement.zip` — **40 MB** against a 100 MB cap, 477 files |
| Build | `bash tools/build_supplement.sh --zip` — idempotent, re-runnable after any regeneration |
| Gate | `tools/anon_scan.py` — **PASS**. Zero occurrences of any author name, email, domain, account or hostname in the extracted zip |
| Verified from extraction | detector self-test 8/8 · area control reproduces committed numbers (7/8, 6/8, AREA-ROBUST, max dev 4.9e-05) · `make_results.py` regenerates |

Two corrections made during execution, both worth recording:

1. **`rebuild/FinalPaper/Paper/` was a committed duplicate of `Paper/`**, including `.fls`/`.log`
   LaTeX build artifacts. It carried 607 of the 697 initial fatal hits. Excluded.
2. **Author tokens survived inside evidence files** — the `ANON_PATTERNS` literal in
   `d2r_reaudit.py` and the four log lines echoing it printed the author's given name and email
   domain in plain text. These were initially whitelisted as "evidence"; that was wrong, since a
   name is identifying regardless of the sentence around it. They are now redacted to
   `<author-given-name>` placeholders, the redaction is recorded in the log's anonymisation note,
   and **`tools/` is not shipped at all** — the scanner's own pattern list contains the identifiers
   it searches for.

A third finding improved the package rather than fixing a defect: shipping two DINOv2 embedding
files (25 MB of the otherwise-gitignored 1.2 GB cache) makes the area control runnable end to end
with none of the image data. It is now the one non-trivial measured result a reviewer can reproduce
on a laptop.

**Outstanding — yours, not mine:**

- The **SE freeze decision** (below). SE is at 38/40 complete as of 14:02 today; the last two runs
  finish ~16:04 and evaluation follows.
- Two unresolved `% AUTHORS:` TODOs in `Paper/main_v2.tex`: the **AI Use Statement** at line 790
  (ICLR 2027 requires it to describe your actual use — mandatory, do not submit the draft unread)
  and the **dataset licence line** at 826. The third TODO, on the delivery route, is resolved and
  removed.
- Nothing is committed. `tools/`, `SUPPLEMENT_README.md`, `ICLR2027_SUPPLEMENT_PLAN.md` are new;
  `NAVIGATION.md`, `rebuild/FinalPaper/make_results.py` and `Paper/main_v2.tex` are modified.

---

## Context

The paper (`Paper/main_v2.tex`, "Concentration, Not Targeting: A Pre-Registered Null for
Uncertainty-Guided Synthetic Data in Camouflaged Object Detection") is written, anonymised, and
already carries AI Use, Ethics and Reproducibility statements. Its Reproducibility Statement
(`Paper/main_v2.tex:812-830`) promises reviewers a **self-contained supplement** containing "Code,
pre-registration documents, per-run metrics, the append-only experiment log, and the released
detector", delivered as supplementary material "which preserves anonymity without a third-party
host."

That supplement does not exist yet. This plan builds it.

The working tree cannot be the supplement: it is **564 GB** (`Dataset/` 233 GB, `Snapshot/`
checkpoints 285 GB, `LAKE-RED/` 27 GB, `Result/` 18 GB), its `README.md` is the *upstream* authors'
ACM MM 2025 readme, its `LICENSE` and git history carry real names, and its git remote is a
de-anonymising GitHub URL. The material that actually matters is small: **640 tracked files, 79 MB**.

### Verified ICLR 2027 constraints

| Item | Value | Source |
|---|---|---|
| Abstract deadline | Sep 18, 2026 AoE — **registered** (confirmed by user) | [CFP](https://iclr.cc/Conferences/2027/CallForPapers) |
| **Paper + supplementary deadline** | **Sep 25, 2026 11:59 PM AoE** | [Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines) |
| Separate supplementary deadline | **None.** "The deadline is the same for the full paper and for the supplementary materials." | Author Guidelines |
| Supplementary size cap | ~100 MB (OpenReview) | [ICLR Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |
| Anonymity | "Any paper where author identity is revealed in either the main text **or the supplementary material** will be desk rejected." | Author Guidelines |
| Code route chosen | Anonymised `.zip` as supplementary material (matches what the paper already claims) | Author Guidelines |
| Visibility | The zip becomes **public** with the paper and reviews | Author Guidelines |

Deadline is **3 days out**. Anonymity is the only failure mode that is fatal and irreversible, so it
is done first and gated twice.

### Scope decision (confirmed with user)

Evidence is reproducible; training is documented, not runnable-from-scratch. Every analysis/audit
experiment re-runs from its own script; the 36+ training runs are fully specified (exact commands,
seeds, `preflight.py`, per-run logs, per-run metrics) but require the public datasets to be
re-downloaded. This is stated plainly in the supplement rather than implied away.

---

## The one blocking decision: the SE freeze point

`rebuild/SE/driver_se.log` was last written **today 11:59**, currently training
`SINetv2_CINV_s48`; `rebuild/ABC/out/se/` holds pools and stems but **no metrics yet**. Runs take
~122 min on 2 GPUs.

This matters beyond packaging. Per `rebuild/SE/PREREGISTRATION_SE.md` and
`rebuild/FinalPaper/EXPERIMENTS_EXPLAINED.md` §17, the projected SE bar (~0.0034) sits **below** the
committed decisive gap (0.0050). The pre-registration commits in advance that if the gap holds, SE
returns **REAL EFFECT** and the paper's central null must be re-reported as a power failure.

**Gate — decide by Sep 24, 09:00:**

- **SE complete and evaluated by then** → include `rebuild/ABC/out/se/` in the supplement, and the
  paper's null claim must be reconciled with the SE verdict before submission. This is a
  paper-rewrite risk, not a packaging risk.
- **SE not complete** → exclude SE metrics from the supplement; ship `PREREGISTRATION_SE.md` and the
  driver logs, and state in the supplement README that SE is in flight and pre-registered. The
  paper's existing power caveat then stands as written.

Do **not** ship a half-evaluated SE. The campaign's whole value is that it was pre-registered against
optional stopping; a partial report destroys that. (Consistent with the standing rule: never add
seeds to a committed campaign.)

---

## Build layout

Build at **`iclr2027_supplement/`** in the repo root. `.gitignore` already contains `/iclr2027*`,
so the build directory is ignored by construction and cannot be accidentally committed.

**Preserve the existing relative paths exactly.** Do not restructure into `code/`, `logs/`, etc.
Every `CMD` line in `results/REBUILD_LOG.txt` is a repo-relative command, `rebuild/common.py:51-70`
declares repo-relative primary-input paths, and the paper cites log-block line numbers. Restructuring
silently breaks all three. The supplement is a **filtered copy of the tracked tree**, plus new
top-level docs.

```
iclr2027_supplement/            → zips to s2r-cod-supplement.zip
  README.md                     REPLACED — reviewer entry point (upstream readme deleted)
  NAVIGATION.md                 UPDATED — currently covers 9 of 18 experiments
  REBUILD_PLAN.md  REBUILD_FINDINGS.md  REVISION_TABLE.md      kept
  LICENSE                       kept verbatim (see Anonymity §3)
  pyproject.toml  uv.lock  .python-version
  MyTrain.py  MyTest.py  CLS.py  preflight.py
  Src/        model + utils (no .pth — backbones are gitignored)
  Eval/       MyEval.py, metrics.py, eval_txt/
  rebuild/    the evidence — one directory per experiment + common.py
  results/REBUILD_LOG.txt       the append-only source of truth
  Snapshot/ABC/<runid>/training_log.log    106 per-run training logs
  tools/anon_scan.py            NEW — the anonymity gate
```

**Excluded, with reasons:**

| Excluded | Why |
|---|---|
| `.git/` | 52 commits authored by real names/emails; remote is `adhello007/S2R-COD` |
| `old_paperinfo_redundant/` (142 files, 9 MB) | superseded drafts; also holds ~3,700 `/home/ai-server` hits in `.fls`/`.fdb_latexmk`/`.log` build artifacts and a `figures/contact.pdf` |
| `Paper/` | the paper is uploaded separately as the PDF; shipping `.tex` adds anonymity surface for no gain |
| `Paper.rar`, `rebuild/FinalPaper/Paper_SEPT20.zip` | paper archives |
| `Explanations/S2R-CODpaper.pdf` | third-party arXiv PDF, embeds `Author: Zhihao Luo; Luojun Lin; Zheng Lin` + ORCID in metadata |
| `rebuild/reference/old_scripts/` | dead code with hardcoded absolute paths |
| `skills-lock.json`, `manuscript_revision.md` | internal agent tooling, not research artifacts |
| `src/s2r_cod/` | dead 2-line stub (`print("Hello from s2r-cod!")`) that `pyproject.toml:[project.scripts]` points at |
| `Dataset/`, `Result/`, `*.pth`, `LAKE-RED/` | 543 GB; documented as external dependencies instead |

**Size budget (measured, not estimated):** the candidate set is 456 files / **60.3 MB raw / 16.0 MB
gzipped**. A zip will land ~20-25 MB against the 100 MB cap. There is room to keep all 106 training
logs (33 MB raw → 4 MB compressed); do not trim them.

---

## Phase 1 — Anonymity (do first; this is the desk-reject risk)

### 1. Build the gate before the bundle: `tools/anon_scan.py`

Reuse the pattern list that already exists at **`rebuild/D2_reaudit/d2r_reaudit.py:847`**:

```python
ANON_PATTERNS = ('/home/', 'ai-server', 'Akshat', 'akshat', 'imagine.io',
                 'Dataset/', 'Snapshot/', 'Result/', 'rebuild/', '.venv',
                 'experiments/lakered', 'S2R-COD/')
```

That list was already used to certify the `rebuild/D2_reaudit/release/` bundle
(`results/REBUILD_LOG.txt` records `anonymization_scan_clean = True` against it four times), so this
is an extension of an existing, exercised gate — not a new invention.

Changes needed for the supplement's wider scope:
- **Drop the structural patterns** `Dataset/`, `Snapshot/`, `Result/`, `rebuild/`, `S2R-COD/` from
  the *fatal* set. They were right for a 4-file standalone bundle; here those directory names are the
  documented layout and appear thousands of times legitimately. Keep them as a *warn* tier.
- **Fatal tier:** `/home/`, `ai-server`, `Akshat`, `akshat`, `Dobhal`, `dobhal`, `imagine.io`,
  `adhello007`, `github.com/`, `Muscape`, `1650020800@qq.com`, `akshatdobhal17@gmail.com`,
  `@gmail`, `@qq.com`, `.venv`.
- **Self-exclusion:** `rebuild/D2_reaudit/d2r_reaudit.py` contains `'Akshat'` and `'imagine.io'`
  *inside its own `ANON_PATTERNS` literal*, and `results/REBUILD_LOG.txt` echoes that list on 4
  lines. The scanner must whitelist those specific occurrences by line, or it will never go green.
  Do not "fix" them by editing the pattern list out of the script — that script is evidence.
- **Binary sweep:** run `pdfinfo`/`exiftool` over every shipped PDF/PNG for `Author`, `Creator`,
  `Producer`, `Title`. Current shipped-set figures are Matplotlib-generated and clean, but re-check
  after any regeneration.
- Exit non-zero on any fatal hit. Print `file:line` for each.

### 2. Scrub absolute paths in the ~16 shipping files that carry them

Outside the excluded directories, `/home/ai-server/...` survives in:

| File | Hits | Fix |
|---|---|---|
| `results/REBUILD_LOG.txt` | 7 | replace with `<REPO>/` — **append a dated note** recording the substitution, since the log is append-only and must not be silently rewritten |
| `rebuild/PC/out/pc_*.log` (8 files) | 1 each | replace with `<REPO>/` |
| `rebuild/D2/out/d2_seed_experiment.json` | 5 | replace with `<REPO>/` |
| `rebuild/ABC/ABC_PLAN.md`, `ABC_SCOPING.md` | 3, 1 | replace with `<REPO>/` |
| `rebuild/SE/chain_se.sh`, `se_resume.sh`, `rebuild/FX/chain_fx.sh` | 1 each | replace hardcoded `cd` with `cd "$(dirname "$0")/../.."` |
| `rebuild/E0/out/e0_environment.json` | 1 | `executable` field → `<REPO>/LAKE-RED/.venv/bin/python` |

Scrub the **copy** in `iclr2027_supplement/`, never the working tree — the working tree's log must
stay byte-identical to what the commits reference.

### 3. `LICENSE` and `README.md`

- **`LICENSE`: keep verbatim.** It reads `Copyright (c) 2025 Muscape` — the *upstream* S2R-COD
  author, not the submitting authors. MIT requires preserving that notice, and it does not reveal
  submitter identity. **Do not add your own copyright line** — that would break anonymity.
- **`README.md`: replace entirely.** The current file is upstream's and opens "This is the official
  (Pytorch) implementation for the paper ... ACM MM 2025", citing Luo, Lin & Lin. Shipping it as the
  supplement's front door is both wrong and confusing. Rewrite per Phase 2. Cite S2R-COD and
  LAKE-RED in third person, as the paper already does.

### 4. Confirm no VCS metadata

The build must be a `git archive`/file copy, never a clone. Assert `.git`, `.gitignore`-only
artifacts, `.venv`, `__pycache__`, `.claude/`, `.agents/` are absent from the zip.

---

## Phase 2 — Make it self-contained and honest

### `README.md` (new — the reviewer's entry point)

Written for someone outside the project, modelled on the existing
`rebuild/D2_reaudit/release/README.md`, which is already written to that standard. Must cover:

1. **What this is** — the supplement for the paper, one paragraph, anonymous.
2. **Start here** — point at `NAVIGATION.md` and the rule that carries the whole package: *if a
   results markdown and its log block disagree, the log wins.*
3. **What you can reproduce without our data** — the contamination detector's 8-assertion
   self-test (`rebuild/D2_reaudit/detect_contamination.py --self-test`), the area control
   (`rebuild/AC/ac_measure.py`, no GPU, no inference), and every table/figure regeneration from
   committed artifacts (`rebuild/FinalPaper/make_results.py`, `rebuild/DIAG/diag_emit.py`).
4. **What needs the public datasets** — COD10K / CAMO / NC4K / HKU-IS download table (lift the
   links from the current README, they are the public sources), expected layout and counts from
   `rebuild/common.py:51-70`, and `preflight.py` as the gate before any training.
5. **What we cannot ship** — 233 GB of data, 285 GB of checkpoints, the two ImageNet backbones and
   `LAKERED.ckpt` (6 GB). Name each and where to get it.
6. **Environment** — `uv sync`, Python 3.12, torch 2.11+cu128; and the fact that there are **two
   virtualenvs** (`.venv` and `LAKE-RED/.venv`) with different scripts requiring different
   interpreters. State which per entry point.
7. **Known hazards a reproducer will hit** — promote these from `Experiments/SINETV2/run_commands.txt`
   and `Explanations/`:
   - never run SINet and SINet-v2 concurrently: both write `Dataset/Source/HKU-IS_iteration2/` and
     `CLS.py` `rmtree`s it on entry;
   - the compounding-LR bug in `Src/utils/tool.py:adjust_lr`;
   - the silent checkpoint-loading failure documented in `Explanations/CHECKPOINT_LOADING_BUG.md`
     (copy that file in — it is a real reproducibility trap);
   - `Src/utils/Dataloader.py:13-15` pairs images and GT by sorted **index**, not basename;
   - `MyTrain.py:253-259`: `--task S2C` silently overwrites `alpha/u/tau/a/b/c`.
8. **Scope caveats** — copy NAVIGATION.md §6 forward (CHAMELEON withdrawn, null scoped to an
   exhausted foreground pool, A3 is not a training-utility bound, ABC tests concentration-driven
   targeting not the signal in isolation).

### `NAVIGATION.md` (update — it is stale)

It documents 9 experiments (E0, D2, D2_nc4k, D2_reaudit, D1, B1, C1, A3, ABC). The log now holds
**18** `EXP` ids; missing are **T2, T2C, AC, PC, OR, FX, SE, C2, REGRESS**. Add a row each, with log
block count and readable file. Also fix §5, which currently says "The `rebuild/` directory is being
sent separately" — in this package it is not separate.

Note the directories that have no `*_RESULTS.md`: `OR` (1 tracked file), `SE`, `DIAG` (19 files),
`D2_nc4k`, `A1`, `FinalPaper`, `reference`. For OR and FX especially — both completed after the
paper snapshot — either add a short results markdown or state explicitly in NAVIGATION that their
numbers live only in their log blocks.

### Arm/campaign glossary (new, short)

Reviewers will meet `SINetv2_CSHUF_s48` in the logs with no way to decode it. One table, sourced from
`rebuild/ABC/abc_common.py:31-76`: A0, A2, B, C10 (digits = temperature α), CSHUF, CINV, CORACLE,
`*FX` suffix, MT; `sNN` = seed; campaign codes ABC/T2/T2C/AC/PC/OR/FX/SE.

---

## Phase 3 — Verification (all must pass before upload)

Run against the **extracted zip in a clean directory**, not the build directory:

1. `python tools/anon_scan.py .` → exits 0, no fatal hits.
2. `grep -rIl -e '/home/' -e 'ai-server' -e 'adhello007' -e '@gmail' -e '@qq.com' .` → only the
   whitelisted evidence lines in `d2r_reaudit.py` and `REBUILD_LOG.txt`.
3. `find . -name '.git*' -o -name '*.venv*' -o -name '__pycache__'` → empty.
4. For every shipped PDF: `pdfinfo` shows no `Author`.
5. `du -sh s2r-cod-supplement.zip` → well under 100 MB (expect ~20-25 MB).
6. **Fresh-extract smoke test**, the real proof of self-containment:
   - `python rebuild/D2_reaudit/detect_contamination.py --self-test` → 8 assertions pass with no
     project data present;
   - `python rebuild/AC/ac_measure.py --no-log` → reproduces `rebuild/AC/out/ac_table.csv`;
   - `python rebuild/FinalPaper/make_results.py` → regenerates `results.md` byte-identically.
7. **Traceability spot-check**: pick 5 numbers from the paper's Table 2 / `tab:tost` /
   `tab:boundary` and confirm each resolves to a committed artifact and a log block, per the mapping
   in Appendix `app:tables`.
8. Read the new `README.md` end to end as if you had never seen the project.

---

## Phase 4 — Paper-side edits (small, but required for consistency)

The paper is otherwise in good shape: already `\author{Anonymous Authors}`, and it already carries
the **AI Use Statement** (`main_v2.tex:759`), **Ethics Statement** (`:788`) and **Reproducibility
Statement** (`:812`) that ICLR 2027 asks for.

1. **`main_v2.tex:827-829`** — delete the `% AUTHORS:` comment block offering the
   anonymous.4open.science alternative. Decision made: zip supplement. Leave the surrounding
   sentence, which already says the supplement "preserves anonymity without a third-party host."
2. **Reconcile the Artifacts paragraph with what actually ships.** It currently promises "Code,
   pre-registration documents, per-run metrics, the append-only experiment log, and the released
   detector" — all four are in the plan above, so this holds. But it also says "every experiment is
   one directory holding its scripts, its declared thresholds and its outputs" — true only once
   NAVIGATION is updated and the `RESULTS.md`-less directories are addressed (Phase 2).
3. **If OR/FX/SE land in the paper**, their directories must ship with them. OR and FX completed
   after the `Paper_SEPT20.zip` snapshot and are **not yet in `main_v2.tex`**; FX in particular
   measures the optimisation-budget question the paper currently concedes as "the largest open
   question this paper creates". Decide whether they go in — that decision changes both the paper
   and the supplement contents.
4. *Minor, optional:* `\appendix` (`:838`) precedes `\bibliography` (`:1192`), while the guidelines
   say supplementary text should appear after the references. Low risk; fix only if time allows.

---

## Timeline

| When | What |
|---|---|
| **Sep 22 (today)** | Phase 1 entirely: `tools/anon_scan.py`, the filtered copy, path scrubbing, README/LICENSE. Get the gate green on a throwaway build. |
| **Sep 23** | Phase 2: new README, NAVIGATION update, glossary, hazards section. Rebuild, re-gate. |
| **Sep 24, 09:00** | **SE freeze decision.** Then Phase 3 verification on the extracted zip. Phase 4 paper edits. |
| **Sep 24, evening** | Upload PDF + `s2r-cod-supplement.zip` to OpenReview. **Do not wait for Sep 25** — the cap is AoE but OpenReview load and any re-upload after a failed anonymity check both need slack. |

## Risks

- **SE overturning the central null** is the largest risk and it is scientific, not logistical. The
  gate above forces the decision on Sep 24 rather than at upload time.
- **The supplement is public on acceptance.** Everything shipped should be something you are content
  to have permanently attached to the paper — including `REVISION_TABLE.md`, which documents where
  earlier numbers were wrong. Recommendation: keep it. It is the strongest evidence the package's
  discipline is real, and the paper already leans on that discipline.
- **Anonymity regression on rebuild.** Any regeneration after the gate goes green (figures, tables,
  `make_results.py`) can reintroduce absolute paths. Re-run `anon_scan.py` as the last step before
  zipping, every time.

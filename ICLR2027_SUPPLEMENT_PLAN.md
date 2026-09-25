# ICLR 2027 supplement — DONE

## Deliverable

**`s2r-cod-supplement.zip` — 40 MB, 483 files.** Rebuild at any time with
`bash tools/build_supplement.sh --zip` (idempotent; re-gates automatically).

Verified on a **fresh extraction**, not the build directory:

| Check | Result |
|---|---|
| Anonymity gate | **PASS** |
| Author identifiers (name, email, domain, GitHub account, hostname) | **0 occurrences** |
| `Muscape` | LICENSE only — upstream MIT notice, required, not a submitting author |
| Excluded: `tools/`, `rebuild/FinalPaper/{Paper,UpdatedPaper}/`, `official_papers/` | all absent |
| PDFs / zips / `.git` / `.venv` / `__pycache__` | 0 |
| Dangling `Experiments/` · `Explanations/` references | **none** |
| `d2r_reaudit.py` finds `Experiments/REPRODUCE_TABLE1_v2.md` | yes |
| Size against the 100 MB OpenReview cap | 40 MB |

The four commands, each run from the extraction:

```
detect_contamination.py --self-test   ->  PASS (8 assertions)
diag_tost.py                          ->  OK
ac_measure.py --no-log                ->  AREA-ROBUST, max dev 4.92e-05
make_results.py                       ->  results.md, 708 lines, SE COMPLETE
```

## What was done

1. **Two regressions from the new commits, fixed.** `tools/` was committed in `9a8d1a0`, so
   `git ls-files` swept it into the package — and `anon_scan.py`'s whitelist exempted it from every
   fatal pattern, so the gate would have reported PASS while shipping the author's name, email
   domain and GitHub account. Excluded `tools/`, removed both whitelist entries so a recurrence
   fails loudly, and added `--self-exempt` for scanning the source tree. Also excluded
   `rebuild/FinalPaper/UpdatedPaper/` (its `main.log` alone held 55 absolute paths) and
   `official_papers/` (third-party PDFs).
2. **`NAVIGATION.md` is now a run guide.** New §0 (four working commands), §1 (setup, what could
   not be shipped, data layout, preflight), §2 (all 16 experiments tiered by what they need),
   §3 (what each directory is). Existing content renumbered to §4–§9, cross-references updated,
   SE status corrected to closed.
3. **`REVISION_TABLE.md`**: replaced a quotation attributed to `REBUILD_PLAN.md` §3 that `git log -S`
   shows never existed; superseded the CHAMELEON row and pointed it at `D2_FINAL_AUDIT`'s 50/76.
4. **`SUPPLEMENT_README.md`** aligned to four commands, and states plainly that four of sixteen
   experiments run from the package.
5. **Repointed three pre-existing dead links** in `Explanations/` (`REPRODUCE_TABLE1.md` → `_v2`,
   `Experiments/10_Aug/` → the reorganised paths).

The paper directories are out; `rebuild/FinalPaper/` retains only `results.md`,
`make_results.py` and `EXPERIMENTS_EXPLAINED.md`, which document experiments rather than the paper.

## Remaining — yours

- **Upload Sep 24**, not the 25th. PDF and zip go together; ICLR 2027 has no separate supplementary
  deadline (Sep 25 23:59 AoE for both).
- **Main-text page limit.** The PDF is 21 pages total; ICLR allows 9 for the main text, with
  references and appendix unlimited. The appendix is correctly placed after the bibliography.
- **Nothing is committed.** Modified: `NAVIGATION.md`, `REVISION_TABLE.md`, `SUPPLEMENT_README.md`,
  `tools/*`, `Explanations/*.md`.

---

# ICLR 2027 supplement — final pass

## Where things stand

**SE closed and the null held.** All 16 comparisons — 4 gaps × {SINet, SINet-v2} × {COD10K, NC4K} —
came back `WITHIN NOISE` at n = 8, and the decisive `B→C10` gap *shrank* with more data
(SINet-v2 COD10K −0.0011, sign-consistency 5/8). The paper's central claim now rests on 8 seeds per
arm instead of 3. No re-report as a power failure is needed.

Everything is committed and pushed through `de2c845`. The paper has been rewritten with OR/FX/SE and
lives at `rebuild/FinalPaper/UpdatedPaper/main.tex` — anonymous, all three `% AUTHORS:` TODOs
resolved, CHAMELEON stated as 65.8% (matching `D2_FINAL_AUDIT/CONTAMINATION_LEDGER.md`), appendix
after the references, PDF carries no author metadata.

The supplement builds, gates clean, and four commands run from a fresh extraction. Deadline is
**Sep 25 23:59 AoE**; it is Sep 23.

---

## 1. Two build fixes — do these first, they are regressions

The new commits added files that `git ls-files` now sweeps into the supplement.

**a. Exclude `rebuild/FinalPaper/UpdatedPaper/`.** 25 files including `main.log`, which carries
**55 absolute-path hits**. The build already excludes `rebuild/FinalPaper/Paper/`; this is the same
directory under a new name. The paper uploads separately as a PDF.

**b. Exclude `tools/`.** This is the one that matters. `tools/` was committed in `9a8d1a0`, so the
selection now picks it up — and `anon_scan.py` and `build_supplement.sh` contain the author's given
name, family name, email domain and GitHub account inside their pattern and redaction lists. The
script's comment says tools/ is not shipped, but nothing in the selection enforces it.

Worse: `anon_scan.py`'s own WHITELIST exempts both files from every fatal pattern, so **the gate
would report PASS while shipping the identifiers**. Fix both halves —

- add `tools/` to the selection excludes, and
- **remove `tools/anon_scan.py` and `tools/build_supplement.sh` from the WHITELIST**, so that if
  they ever land in the package again the scan fails loudly instead of waving them through.

Two `grep -vE` lines and two deleted whitelist entries.

---

## 2. The one real piece of work: `NAVIGATION.md` as a run guide

Keep everything already in it — the experiment map is current at 20 rows. Put a run guide in front.

```
0. What runs right now    the four verified commands
1. Setup                  uv sync; which venv each script needs; backbone weights
                          and datasets (not shippable) and where to get them;
                          preflight.py before any training
2. Run guide              per experiment: command, interpreter, GPU?, what it needs
3. What each directory is rebuild/ = this paper, start here. results/ = the authority.
                          Snapshot/ = per-run training records. Experiments/ and
                          Explanations/ = the operational layer: setup notes, gotchas
                          and post-mortems from reproducing the published baselines
4+. existing content      experiment map, headline contributions, scope caveats
```

### §0 — verified, each run from a fresh extraction

```bash
python rebuild/D2_reaudit/detect_contamination.py --self-test   # 8/8, no data at all
python rebuild/DIAG/diag_tost.py                                # the paper's TOST table
python rebuild/AC/ac_measure.py --no-log                        # 7/8, 6/8, AREA-ROBUST
python rebuild/FinalPaper/make_results.py                       # regenerates results.md
```

### §2 — the table

One row per experiment with an honest dependency column: *runs now* / *needs images* / *needs
checkpoints* / *needs un-shipped cache*. Of 16 experiment directories, four commands run from the
zip. **Say that plainly.** A reviewer who trusts the table and finds it true will trust the rest;
one who finds it optimistic will not.

Commands come from the `CMD` field of each `EXP` block in `results/REBUILD_LOG.txt` first, script
docstrings second, `rebuild/ABC/out/{,t2/,or/,fx/,se/}abc_commands.txt` for training runs.

---

## 3. Two one-line fixes while in there

- **`REVISION_TABLE.md:108`** quotes `REBUILD_PLAN.md` §3 as saying *"secondary endpoints CHAMELEON
  and NC4K"*. `git log -S` shows that string has never existed in the file. The finding is sound,
  the citation is invented. Point it at the real text (`REBUILD_PLAN.md:126`) or drop the quote
  marks.
- **`REVISION_TABLE.md:52`/`:129`** still file CHAMELEON as 41/76 under "re-tested clean". The paper
  now says 65.8% (50/76). Point the row at `rebuild/D2_FINAL_AUDIT/CONTAMINATION_LEDGER.md`.

Nothing else. The root documents get no header campaign — a reviewer reaches them through
NAVIGATION §3, which now says what each one is and when it froze.

---

## 4. Ship

```bash
bash tools/build_supplement.sh --zip
```

Then verify on the **extracted** zip, not the build directory:

- anon scan PASS, and confirm `tools/` is absent from the extraction;
- zero hits for every author identifier, and no `rebuild/FinalPaper/UpdatedPaper/`;
- no `.git`, `.venv`, `__pycache__`;
- `official_papers/*.pdf` absent — three third-party copyrighted PDFs, already caught by the
  `\.(pdf|zip|rar)$` exclusion, but confirm rather than assume;
- `rebuild/D2_reaudit/d2r_reaudit.py` still finds `Experiments/REPRODUCE_TABLE1_v2.md`;
- the four §0 commands run and produce what NAVIGATION says;
- zip under 100 MB (it was 40 MB).

Upload the PDF and `s2r-cod-supplement.zip` to OpenReview together — ICLR 2027 has no separate
supplementary deadline. Do it **Sep 24**, not on the 25th: a failed anonymity check with no slack is
the one mistake that cannot be undone.

## 5. Yours, not mine

- **Page limit.** The PDF is 21 pages total. ICLR 2027 allows 9 for the main text; references and
  appendix are unlimited and the appendix is correctly placed after the bibliography (`:622`,
  `:625`). Worth confirming the main text itself lands within 9.
- **Nothing about the paper's content.** It reads as finished; I have not touched it.

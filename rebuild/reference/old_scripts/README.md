# The old package's scripts — audited object, not input

These six files are the **only** surviving scripts that produced the previous Stage C package's
numbers. They lived in `evidence/artifacts/scripts_original/`, which is gitignored
(`.gitignore:6 /evidence/artifacts/`), so they were never in git history and would have been lost
when that directory was archived out of the repo.

They are kept here for exactly one reason: `REVISION_TABLE.md` must cite the source of each defect it
corrects, and these files are that source. Frozen copies, byte-identical to the originals.

**Nothing in `rebuild/` imports, executes, or reads these files.** They are not a dependency, not a
baseline, and not a source of any value. Every number in the rebuild comes from a script in
`rebuild/` run against primary data, per `REBUILD_PLAN.md` §0.2.

## What each one is, and what it proves

| File | Role in the old package | What it is cited for |
|---|---|---|
| `embed_dino.py` | Built every DINOv2 feature cache | **The grey-128 slip.** `:22` — `a[np.asarray(gt)<127]=128  # object on neutral grey`. The "foreground cutouts" are object-on-flat-grey, applied at native resolution and *then* BICUBIC-resized. Also `:6` `.half()` — the caches are fp16 |
| `analyze.py` | Produced the acceptance headline (26.67 %, 6.46 %) | **The representation mismatch.** `:32` ranks by `Fc@C[c]` (the grey cutout) while `:28` computes `land=(Fg@C.T).argmax(1)` (the finished render) — selection and measurement on different representations, four lines apart. Contains **no** train/test split of any kind, which is why the 20.62 % "held-out" figure has no provenance. Reads from a `/tmp` scratchpad at `:7` |
| `m4_deficiency.py` | ES-vs-error correlation (B1's ancestor) | The `ESLoss` call convention, and the now-absent `Dataset/Test/{Image,GT}` paths |
| `locked2.py` | Per-run ES / Sα / MAE across seeds | Same absent paths; the six-run set whose checkpoints exist only as rescued copies |
| `audit6.py` | Sα / Fβw / MAE per run — the noise floor σ | Hardcodes the volatile scratchpad *and* `Dataset/Test/GT`; neither resolves today |
| `eval_seeds.py` | Seed-run evaluation driver | Same |

## Provenance

Copied from `evidence/artifacts/scripts_original/` on 2026-08-30, before that directory was moved out
of the repo. A prior audit verified them byte-identical to the copies in the original `/tmp`
scratchpad. Their outputs — feature caches, checkpoints, prediction PNGs — are **not** kept here and
are not used.

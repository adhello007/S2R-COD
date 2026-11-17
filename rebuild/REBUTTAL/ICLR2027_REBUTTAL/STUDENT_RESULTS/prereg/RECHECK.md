# RECHECK: two re-training runs on the current system (diagnostic; decides nothing in any campaign)

*Written and committed 2026-11-17, before either run starts. No number from these runs exists yet.*

**Why.** The kernel changed from 7.0.0-42 to 7.0.0-43 at the reboot of 2026-11-13 10:31; the NVIDIA driver and
CUDA stack are unchanged. Every EQ run trained after that change, and EQ's pseudo-label counts and S_α are slightly
lower than those of the eight-seed campaign. These two runs test whether the current system reproduces earlier
training.

**Runs.** Both use the queue's command builder, `--save_ckpts minimal --link_pool`, and a fresh hardlinked copy
of the committed pool, whose digests must match the committed record before launch. Nothing existing is
overwritten.
- **R1:** `SINet_C10_s42` on GPU 0. The same run and flags as the 2026-11-11 bridge, which ran on the old kernel
  and gave COD10K S_α 0.717103 (committed 0.717165).
- **R2:** `SINet_CSHUF_s115` on GPU 1. The lowest EQ run, COD10K S_α 0.693264, trained on the new kernel.

**Checks per run.** The queue's own verification (2 rounds, step pin 253, last epoch 039/040, checkpoint, pool
5,447), then inference on COD10K-test and NC4K and scoring with the committed scorer.

**Comparison (COD10K-test S_α), declared now.** R1 is compared with the bridge value; R2 with 0.693264.

| \|Δ\| | Reading |
|---|---|
| ≤ 0.001 | **reproduces**: the current system repeats earlier training to the precision the bridge showed |
| 0.001 to 0.0069 | **within the bridge band** (2σ̂ of the SE campaign) but not reproduced exactly: nondeterminism larger than at the bridge |
| > 0.0069 | **outside the band**: the system change affects training |

**What each outcome would mean.**
- **R1 reproduces:** the kernel change has no effect, and EQ's lower level is seed-to-seed variation.
- **R2 reproduces:** that run's low score is a property of its seed, not a transient fault.
- **Any other outcome** is reported as it is. EQ's within-campaign contrasts are unaffected in every case, because
  all EQ arms trained on the same system, interleaved seed by seed. Only the pooled EQ+SE secondary analysis
  would be flagged.

No result here re-decides EQ, CDR or any verdict.

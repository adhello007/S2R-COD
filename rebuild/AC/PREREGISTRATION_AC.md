# PREREGISTRATION_AC.md — the area control on the pixel-over-structure ordering

> **Committed before `ac_measure.py` was written and before any AC number existed.**
> If any part of §AC.1–§AC.4 is changed after a single partial correlation has been computed, this
> experiment is void. Amendments are append-only and dated, never edits in place.

## §AC.0 Why this exists

`EXP T2C` established that the ordering `rho(MAE) > rho(1-Sa) > rho(1-IoU)` holds on 8 of 8
whole-image rows across four signal variants and two architectures, and concluded that the
pixel-over-structure gap is a property of the signal class rather than of ES.

A reviewer raised a confound that T2C's own post-hoc explanation implies but does not test. T2C
explained the boundary-aggregation collapse by observing that *"band area alone predicts MAE at
+0.6286 on SINet-v2"* and that a whole-image mean is effectively `uncertainty density x area`. **That
argument applies to the whole-image rows too.** MAE scales with the area of the erroneous region;
`S_alpha` carries an object-size term that does not scale the same way; and every uncertainty signal
here is itself an area-weighted mean. If area drives all three, the ordering is a property of the
*metrics*, not of uncertainty signals.

This experiment tests that, and is pre-registered to be able to overturn T2C's licensed claim.

## §AC.1 What is held identical to the committed measurement

Non-negotiable, so that any difference in outcome is attributable to the area control and to nothing
else:

- The **same cluster partition**: `dinoL518`, `k = 75`, committed seed 0, via
  `t2c_signals.cluster_target_signal` and `b1_es_error_correlation.assign_clusters`, imported, not
  reimplemented.
- The **same floors**, copied through the imported code path: `>= 15` endpoint images per cluster
  (binding) and `>= 5` target images per cluster.
- The **same per-cluster aggregation**: `a` = mean target-side signal over the cluster's target
  images; `b` = mean endpoint error over the cluster's endpoint images.
- The **same eight whole-image rows**: `{ES, entropy, ensemble A0, ensemble CSHUF} x {SINet, SINet-v2}`.
- Spearman rank correlation throughout.

Gate **G-AC1**: with zero covariates partialled, the recomputed `rho` must reproduce
`rebuild/T2C/out/t2c_table.csv` at the committed seed to `< 1e-9`. If it does not, this experiment
halts and reports the discrepancy rather than proceeding.

## §AC.2 The area covariates, declared in advance

Two, reported separately and never averaged together:

- **`z_obj`** — object area. Per-cluster mean of `gt_fg_frac` over the cluster's **endpoint** images.
  Source: the committed `gt_fg_frac` column of `rebuild/B1/out/b1_scores_<arch>_test.csv`. This is the
  covariate that addresses the MAE-versus-`S_alpha` asymmetry directly.
- **`z_unc`** — uncertain-region area. Per-cluster mean of `band_frac` over the cluster's **target**
  images. Source: the committed `band_frac` column of `rebuild/T2C/out/t2c_signals_<arch>.csv`. This
  is the covariate that addresses the signal side.

## §AC.3 The statistic

First-order partial Spearman correlation, computed on ranks by the standard formula:

```
rho(a, b | z) = ( rho_ab - rho_az * rho_bz ) / sqrt( (1 - rho_az^2) * (1 - rho_bz^2) )
```

applied independently for each covariate `z` in `{z_obj, z_unc}`, for each of the three errors
`{MAE, 1-Sa, 1-IoU}`, for each of the eight rows. The unpartialled `rho_ab` is reported beside every
partialled value so the shift is visible.

## §AC.4 The decision rule — frozen

```
ordering_pass(row, z)  iff  rho(MAE|z) > rho(1-Sa|z) > rho(1-IoU|z)

AREA-ROBUST      iff ordering_pass holds on >= 6 of 8 rows for z_obj
                 AND ordering_pass holds on >= 6 of 8 rows for z_unc
NOT AREA-ROBUST  otherwise
```

**Consequence, declared now so it cannot be softened later.**

- If **AREA-ROBUST**: T2C's licensed claim stands as written, and the paper additionally reports that
  it survives partialling on both area covariates.
- If **NOT AREA-ROBUST**: the claim is **withdrawn to its aggregation** — *"the ordering holds at the
  whole-image aggregation; it is not established independently of area"* — and the contribution bullet
  is rewritten to match. The `8/8` result is still reported, with the partialled result beside it.

Threshold **T-AC1** records which of the two branches obtained. A `NOT AREA-ROBUST` outcome is a FAIL
of the licensed claim and is reported as a FAIL, not relaxed.

## §AC.5 Secondary, reported but not decisive

`EXP T2C` §4 named the statistic its design could not reach: *"an area-controlled statistic (e.g.
partialling out band area, or a band **sum** rather than mean)"*. We report the band-sum variant,
`signal_band_sum = signal_boundary * band_frac`, for the boundary rows, as an **observation**. It is
explicitly **not** promoted to a threshold and does not enter §AC.4, because T2C already declared the
boundary question not reachable from this design and we are not reopening it on a statistic chosen
after seeing that failure.

## §AC.6 What this experiment cannot establish

- **It is still correlational.** Partialling out a covariate does not establish causation, and a
  surviving ordering does not show the signal is useful.
- **Two covariates, not all confounds.** Object area and band area are the two named in T2C's own
  post-hoc account. Contrast, object count, boundary complexity and scale are not controlled.
- **One endpoint.** COD10K-test only, inherited from T2C.
- **First-order partials only.** The two covariates are partialled one at a time, not jointly;
  a joint control is not declared here and will not be substituted after the fact.
- **Nothing about trained accuracy.** This experiment trains nothing and re-scores nothing.

## §AC.7 Provenance

Reads only committed artifacts: `rebuild/B1/out/b1_scores_*.csv`,
`rebuild/T2C/out/t2c_signals_*.csv`, `rebuild/T2C/out/t2c_table.csv`, and the committed E0 embedding
caches via the imported B1 loader. Writes only under `rebuild/AC/out/`. Emits one `EXP AC` block to
`results/REBUILD_LOG.txt`. **Trains nothing. No GPU required.**

---

## Addendum A1 — 2026-09-13. Append-only. §AC.1's reference tolerance was unsatisfiable.

**The defect.** §AC.1 declares Gate G-AC1 as requiring the recomputed `rho` to reproduce
`rebuild/T2C/out/t2c_table.csv` **`< 1e-9`**. That is **unsatisfiable by any correct computation**:
the committed file records `rho` to **four decimal places**, so rounding alone admits deviations up to
`5e-5`, roughly fifty thousand times the stated tolerance. No implementation could have passed it.

**This is the same defect `PREREGISTRATION_T2.md` recorded in its own Addendum A1**, and the fact that
it recurred here — in a file written by the author who had just documented it — is itself worth
recording rather than quietly fixing.

**The replacement.** G-AC1 requires **exact agreement at the recorded precision**: every recomputed
`rho` must round to the committed 4-decimal value, i.e. deviation `< 5e-5`. This is the strictest
satisfiable form of the original intent, and it is derived from the file's recorded precision, not
chosen against an observed number.

**Disclosure of when this was found, in full.** The defect was found during a `--no-log` pass in which
the partial correlations had **already been computed and printed**. The replacement tolerance was
therefore selected with the results visible. Two facts bound what that could have influenced, and a
reader should check both rather than accept this framing:

1. The tolerance is a function of the committed file's format (4 dp -> 5e-5) and of nothing else. Any
   other value would have been arbitrary.
2. **G-AC1 governs only the unpartialled reproduction gate**, which is a check that this script reads
   the committed partition correctly. It is not one of the three decision thresholds in §AC.4, none of
   which is altered, relaxed or re-pointed by this addendum. The measured gate deviation is `4.92e-05`.

§AC.2–§AC.7 are untouched. The §AC.4 decision rule is untouched.

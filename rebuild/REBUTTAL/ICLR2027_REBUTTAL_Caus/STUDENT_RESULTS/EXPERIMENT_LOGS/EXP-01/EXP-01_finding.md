# EXP-01: reviewer-facing finding

The submitted oracle (CORACLE) kept C10's quota shape, so it tested only where the budget points, not
how it is spread. Before training, we pre-registered three oracle allocations of different shapes at
the same 1,000-image budget, pool and selector [E1]: error-proportional (OR-PROP), ten worst clusters
(OR-TOP10) and five worst clusters (OR-TOP5), plus a same-shape shuffle of OR-TOP10. All are built from
the endpoint-error vector CORACLE used. They are leaky diagnostics: COD10K-test labels chose their
training data, and NC4K labels were read by none of them [E2].

We trained them with SINet (seeds 42/43/45; 12 runs, 21.7 GPU-h, all passing their completion checks)
[E3]. We compared them with the committed B, C10 and CORACLE runs, reused after a gate showing
identical code, data, selections and first training step, and an exact re-score [E4].

All four primary contrasts are within noise on both endpoints (2σ̂ = 0.0057 on COD10K, df 14) [E5]:

| Contrast | Δ COD10K | sign |
|---|---|---|
| OR-TOP10 − CORACLE | +0.0022 | 2/3 |
| OR-TOP10 − its shuffle | −0.0002 | 2/3 |
| OR-PROP − CORACLE | +0.0023 | 2/3 |
| OR-TOP5 − CORACLE | +0.0011 | 2/3 |

Two cautions apply. OR-PROP's direction is untestable, because any shuffle leaves at least 84% of its
images unchanged. OR-TOP5 has no same-shape control [E1, E6]. Scores were verified by an independent
S-measure, and the verdicts by two independent statistics implementations [E7].

This is a null at three seeds, not proof of no effect, and it is bounded to SINet on the LAKE-RED
pipeline.

Evidence IDs:
- [E1] `PREREGISTRATION_EXP01.md`
- [E2] `../AN-05_leakage_and_calibration.md`
- [E3] `runs/`, `queue_status_final.txt`
- [E4] `../../RESULT_TABLES/EXP-01_reuse_gate.csv`, `../../RESULT_TABLES/EXP-01_reuse_R5_rescore.csv`, `00_pilot/`
- [E5] `../../RESULT_TABLES/EXP-01_comparisons.csv`, `../../RESULT_TABLES/EXP-01_metrics_by_seed.csv`
- [E6] `../../RESULT_TABLES/AN-02_selection_overlap.csv`
- [E7] `../../RESULT_TABLES/EXP-01_independent_sm_check_new.csv`, `scoring/exp01_stats.log`

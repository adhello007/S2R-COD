# BRIDGE: re-train one committed run with the patched pipeline (pre-registration)

**Status.** Committed before the bridge run is launched. This is a reproducibility check, not a
campaign; it decides nothing about any reviewer question.

## Purpose

The new campaigns (CDR, EQ) run with the patched pipeline: `--save_ckpts minimal`, `--link_pool`, the
CDR registry and the queue. CDR also compares new runs with references trained in September (B, CSHUF,
C10, CINV). The bridge checks that the patched pipeline, with its footprint flags on, still reproduces a
committed run.

## Run

`SINet_C10_s42` is re-trained from a fresh hardlinked copy of its committed pool:
- pool: `Dataset/Source/RL5B/bridge/SINet_C10_s42`; its digests equal the committed ones, see
  `rebuild/RL5B/out/pool_bridge_SINet_C10_s42.json`;
- snapshot: `Snapshot/RL5B/bridge/SINet_C10_s42`;
- trainer: `MyTrain.py --network SINet --task S2C --method ours --iteration 2 --seed 42
  --save_ckpts minimal --link_pool`.

It is inferred on COD10K-test and NC4K and scored with the committed scorer at 6 decimals. The
reference is `rebuild/ABC/out/abc_metrics.csv`, row SINet/C10/42.

## Rule, fixed now

- All nine metrics equal at 6 dp → **deterministic**. The footprint flags are numerically neutral.
- Otherwise, report |ΔS_α|. If |ΔS_α| ≤ 2σ̂_SE = 0.0069, the run reproduces within the committed noise
  band; this is reported as residual nondeterminism, and the campaigns continue.
- If |ΔS_α| > 0.0069 on COD10K-test, **pause the queue** and diagnose before any CDR or EQ result is used.
- Independently of the metric, after the bridge run three things are re-hashed against their committed
  digests: the base files of the bridge pool, `Dataset/LAKERED/output/HKU-IS`, and
  `Dataset/Source/HKU-IS`. This proves `--link_pool` wrote through no hardlink. Any mismatch stops
  everything.

Analysis: `analysis/bridge_check.py`.

---
*Amendment 2026-11-09 08:15 IST (written after launch, before any bridge number exists). As executed,
the queue names the run directories after the job id, so the snapshot is
`Snapshot/RL5B/bridge/BRIDGE_SINet_C10_s42` and the predictions are under
`Result/RL5B/bridge/BRIDGE_SINet_C10_s42/`. `bridge_check.py` reads these paths from
`rebuild/RL5B/queue_jobs.json`. The pool, the command and the rule are unchanged.*

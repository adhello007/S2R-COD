# EXP-01: blocker record (training half)

**Task:** EXP-01, a robustness check at a larger matched budget with a larger contrast (CW-01, QA-02).
**Preflight status:** executed on CPU. **Result: FAILED its pre-specified pass rule**
(`RESULT_TABLES/EXP-01_preflight.csv`, `EXPERIMENT_LOGS/EXP-01_preflight.json`).
**Training status:** `BLOCKED`, for two independent reasons:
1. The preflight rule says not to train, because no larger budget materially enlarges the contrast.
2. Compute: no GPU before the 17 Nov cutoff.

## Blocker fields
| Field | Value |
|---|---|
| Task ID | EXP-01 (training half) |
| Missing item | (a) a budget N at which B_N and C10_N differ materially more than at N = 1000; (b) GPU time |
| Attempted discovery / command | `scripts/exp01_preflight.py`: base selection code at N ∈ {1000, 2000, 3000, 4447}, 8 B seeds. N = 1000 reproduces all 9 committed stem files byte for byte |
| Error / outcome | DC(N), the fraction of the training pool that differs between B_N and C10_N, is 0.1407 / 0.1719 / 0.1307 / 0.0000. The ratio to N = 1000 is 1.22× at N = 2000 (rule needs ≥ 1.5×) and 0.93× at N = 3000. At N = 4447 the pool is exhausted and both arms are identical |
| Required resource | A larger foreground pool (more than 4447 distinct foregrounds), or a different sampling algorithm; plus ≈ 23 GPU-hours (2 arms × 3 seeds × 2 architectures, SE's measured per-run cost) or ≈ 61 GPU-hours at 8 seeds |
| Valid alternative | Keep the budget at N = 1000 and draw the random arm **only from foregrounds C10 did not select**. This sets the injected overlap to 0, so DC = 1000/5447 = 0.184, which is 1.31× the current 0.141. It is a **different sampling algorithm** ("random among the unselected"), not arm B, and would need its own pre-registration. A larger pool with new foregrounds is the other route, and it runs into the EXP-03 blocker |
| Scientific conclusion left unresolved | Whether a materially larger realised contrast would reveal an effect. In this pool it cannot be built by raising N, because overlap grows with N (Jaccard 0.13 → 0.29 → 0.51 → 1.00) |

## Why larger N does not help here (descriptive)
B draws uniformly without replacement from the same 4447 foregrounds that C10 ranks. As N approaches
4447 the two sets must converge. The differing count N − |B ∩ C10| peaks near N = 2000 (about 1108 of
2000) and then falls, while the pool grows as 4447 + N. The pinned schedule also keeps steps per epoch
fixed at 253 (SINet) or 127 (SINet-v2), so the expected visits to arm-specific images per epoch scale
with DC(N): about 570, 696, 529 and 0 per epoch for SINet.

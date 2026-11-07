# PREREGISTRATION_WS6.md — two different-shape oracle arms

> **Committed before the first WS6 training run. Never edited after any WS6 number exists.**
>
> Dated **2026-11-07 (IST)**. Additive to `rebuild/ABC/PREREGISTRATION.md` (frozen at
> `065dac6`), `PREREGISTRATION_T2.md` and `rebuild/OR/PREREGISTRATION_OR.md`, all unaltered.
> No committed arm, gate, verdict or artifact is restated, recomputed or replaced. Arm code:
> `rebuild/ABC/abc_common.py` (`CORPROP`, `CORTOP`, `_oracle_alloc`, `declared_shape`),
> commit `177a0ce`.

## §WS6.0 The declaration that must be read first

**Both arms deliberately allocate by ground-truth error on the primary endpoint. They are
diagnostics, not methods.** OR §0's three commitments apply to them word for word: never
reported as a method, a configuration or a recommendation; not runnable without endpoint
labels; and gate G1 is run and recorded anyway, with `oracle_uses_endpoint_labels = true`
disclosed.

**Why they exist.** Reviewer Caus asks whether the oracle we ran (CORACLE) was the right
test, because it reused C10's allocation shape and only re-aimed it. WS6 adds two oracles
with **their own shapes**: one proportional to true error, one concentrated on the truly
worst clusters.

## §WS6.1 The rule — verbatim

```
Oracle source    : rebuild/B1/out/b1_cluster_es_dinoL518.csv, column test_one_minus_sa
                   (per-cluster mean 1 - S_alpha on COD10K-test, 75 clusters), read through
                   abc_common.oracle_error() -- the OR arm's sanctioned accessor -- and never
                   recomputed. sha256 1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8.
                   It holds SINet's errors (OR Addendum A1), so the SINet-v2 cells are
                   NEAR-oracle (rho +0.92 between the two architectures' per-cluster errors).

CORPROP          : Equation 2 applied to the oracle vector in place of the ES score:
                     p = softmax_alloc(oracle, alpha = 1.0)   # temperature alpha * sd(oracle)
                     alloc = largest_remainder(p, 1000)
                   Its own shape. Measured at commit 177a0ce, before any training:
                   clusters_funded 75, max_alloc_share 0.099, alloc_entropy_norm 0.87985,
                   tv_from_uniform 0.40676 (C10: 75, 0.194, 0.78644, 0.49253).

CORTOP           : the whole budget of 1000 on the k = 5 clusters with the LARGEST true
                   error, among clusters with n_test >= 2 (a one-image cluster cannot be
                   "truly worst"), split EQUALLY (200 each, largest remainder). k = 5 is
                   fixed now. Measured at commit 177a0ce: clusters {4, 13, 18, 20, 56},
                   n_test {12, 24, 50, 39, 7}, tv_from_uniform 0.93333.
                   Supply: selection walks each funded cluster's centroid ranking over all
                   4447 cutouts (C1 greedy_select), so 1000 distinct renders is feasible at
                   any k. The preflight verifies n_selected == 1000 and
                   clusters_funded == 5; if either fails, k rises to the smallest value
                   that satisfies both, decided in preflight and logged BEFORE training,
                   never after a number exists.

Everything else  : identical to C10 -- B = 1000, dinoL518 partition, R2 grey-128 centroid
                   ranking, desc_nc serving order, greedy distinct selection, LAKE-RED
                   render pool, base pool HKU-IS 4447, target 4040. Both arms are
                   deterministic across training seeds.

Comparator       : arm B at seeds {42, 43, 45}, exactly as committed (ABC). NOT re-trained.
                   Its committed predictions are RE-SCORED and must reproduce
                   rebuild/ABC/out/abc_metrics.csv at 6 dp, or WS6 halts.

Architectures    : SINet (primary), SINet-v2.   Seeds: {42, 43, 45}.   New runs: 12.
Primary endpoint : COD10K-test, S_alpha, Tea_epoch_best.pth, final round.
Secondary        : NC4K S_alpha (reported, never decides). MAE, F-beta-w, E-phi reported.

Noise estimate   : sigma_hat = pooled within-arm sd of S_alpha over {B, CORPROP, CORTOP},
                   per architecture, per endpoint, df = 3 x 2 = 6.
Gaps             : Delta_PROP = mean(CORPROP) - mean(B)
                   Delta_TOP  = mean(CORTOP)  - mean(B)

Rule (identical to A/B/C, T2 and OR, unchanged):
  REAL EFFECT     iff Delta > 2*sigma_hat AND sign consistent 3/3 seeds
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND sign consistent 3/3 seeds
  INCONCLUSIVE    iff |Delta| > 2*sigma_hat but sign not 3/3 -> report as-is, ADD NO SEEDS

Interpretation, fixed before any WS6 number exists (primary cell decides):
  BOTH WITHIN NOISE
      -> neither a proportional nor a top-k allocation of perfect error information moves
         the endpoint in this pipeline. With CORACLE, that is three oracle shapes. The
         constraint is downstream of the acquisition score.
  Delta_TOP REAL EFFECT
      -> concentrating on the truly worst clusters helps. The null is then partly a
         property of the ES score's aim. Reported, in the main text, and the paper's
         framing is revised to say so.
  Delta_PROP REAL EFFECT
      -> an error-proportional allocation helps. Same consequence.
  Either REAL REGRESSION
      -> that allocation is harmful here. Reported, not explained away.
  INCONCLUSIVE
      -> reported as-is.
  Whichever occurs is reported. No arm is dropped, no seed added, no gap redefined.

Also reported    : the four shape statistics of both arms beside C10's and CORACLE's;
                   paired per-seed differences; sign counts; Jaccard overlap with C10 and
                   with each B draw. POST-HOC and labelled so: Welch 95% CIs. NO p-value
                   decides anything at n = 3.
```

## §WS6.2 Mechanical notes

1. **Gate G1** reads the ES score's provenance. These arms read `test_one_minus_sa`, so G1
   will pass on syntax while the arms violate its intent. That is disclosed here and in the
   WS6 preflight block, exactly as for OR.
2. **The same-shape assertion does not apply.** These arms differ in shape by design. The
   preflight asserts `declared_shape()` instead: CORTOP funds exactly 5 clusters, and both
   select exactly 1000 distinct renders. The shape statistics are reported, never asserted
   against C1's cell.
3. **Distinctness** is gated as for every C-family arm: Jaccard ≤ 0.50 against C10 and each
   other. Measured before training: CORPROP|C10 0.452, CORTOP|C10 0.229.
4. **Runs:** `abc_build_pools.py --arms CORPROP,CORTOP --tag ws6`, then
   `abc_train.py --arms CORPROP,CORTOP --tag ws6`, then
   `abc_evaluate.py --arms CORPROP,CORTOP,B --gaps ws6 --tag ws6 --gpus 0,1`.

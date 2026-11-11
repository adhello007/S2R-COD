# PREREGISTRATION_EXP01.md — different-shape oracle allocation (Reviewer Caus, QA-01)

> **Committed before any EXP-01 run script exists and before any EXP-01 training run.** Never edited
> after the first EXP-01 number exists; later corrections go in dated, append-only addenda.
>
> **Additive and post-review.** `rebuild/ABC/PREREGISTRATION.md`, `PREREGISTRATION_T2.md`,
> `rebuild/OR/PREREGISTRATION_OR.md`, `PREREGISTRATION_FX.md` and `rebuild/SE/PREREGISTRATION_SE.md`
> are frozen and are not altered, superseded or reinterpreted. No committed arm, verdict, σ̂ or bar
> is restated or replaced. EXP-01 is a separate campaign with its own σ̂ and verdicts, reported beside
> the committed ones and never in place of them, and never merged into the 103-run figures.
>
> Dated **2026-11-12 (IST)**, branch `rebuttal/Caus-oracle-scope`, base commit `8d1d079`. Written after
> the quota/selection preflight below (inputs only) and **before** any EXP-01 pool was trained on.

---

## §0 Declaration

**Every new oracle arm deliberately uses COD10K-test labels to choose training data.** The error
vector is CORACLE's: per-cluster mean (1 − Sα) of the committed SINet/S2C model on COD10K-test,
`rebuild/B1/out/b1_cluster_es_dinoL518.csv:test_one_minus_sa`, sha256
`1ff27cd1efdf6ed01be557c1d339547792fdfcc219f8db6ecfd5db9195f693f8` (identical to the value
`PREREGISTRATION_OR.md` recorded; one commit in its history, `470e224`).

- Every EXP-01 arm is a **diagnostic stress test, never a method**. COD10K-test is therefore **not an
  unbiased endpoint** for any of them. `oracle_score_source = endpoint-label-leaky` for OR-PROP,
  OR-TOP10, OR-TOP5 and CORACLE. It is `endpoint-label-leaky (shape only)` for the shuffles, whose
  sorted multiset comes from the leaky vector but whose cluster assignment is destroyed.
- **The leak can only favour the oracle arms.** A null is therefore conservative. A COD10K gain is
  checked against NC4K, whose labels no allocation reads. NC4K is still domain-coupled to COD10K
  (both are camouflage photography), so an NC4K difference is "not label-driven", not "independent".
- **Why not disjoint calibration labels.** The only endpoint-disjoint labelled images that fall in the
  target clusters are the 4,040 target images' own masks (COD10K-train + CAMO-train). Those masks are
  **not in the pre-rebuttal workspace**. The one local copy is a 7 Nov download made by another
  reviewer's workstream, which this work does not use. A 12-run budget also cannot carry two error
  sources and still keep the exact shape contrast against CORACLE. A CPU-only comparison of
  calibration-label quotas is attempted separately if the official masks can be obtained; it trains
  nothing.

## §1 The rule

```
Question     : CORACLE kept C10's quota multiset and only re-aimed it by true error. Does an
               oracle that changes the SHAPE of the allocation -- error-proportional, or
               concentrated on the truly worst clusters -- train a better SINet at the same
               N = 1000, generator, pool, selector and protocol?

Arms trained : OR-PROP, OR-TOP10, OR-TOP10-SHUF, OR-TOP5  x  seeds {42, 43, 45}  = 12 SINet runs
Arms reused  : B, C10, CORACLE (SINet, seeds 42, 43, 45), conditional on reuse gate R1-R6 (§3)
Reference    : CSHUF (SINet, 42/43/45) is reported beside them and decides nothing
Quota-only   : OR-PROP-SHUF, OR-PROP-INV, OR-TOP5-SHUF -- built and audited, never trained
Architecture : SINet only (SINet-v2 is not in the budget)

Definitions (err = the §0 vector, 75 clusters, cluster order 0..74):
  OR-PROP      w_j = max(err_j, 0) + eps, eps = 1e-6 * max(err);  q = largest_remainder(w/sum(w), 1000)
               (C1's committed largest_remainder; ties by ascending cluster index)
  OR-TOP10     100 to each of the 10 largest err (stable argsort of -err), 0 elsewhere
  OR-TOP5      200 to each of the 5 largest err, 0 elsewhere
  *-SHUF       q[sigma] for the FIRST offset off in 0..63 such that
               sigma = numpy.random.default_rng(NS + off).permutation(75) has no fixed point and
               |scipy spearmanr(q[sigma], err)| <= 0.10;  NS = 920000 PROP, 930000 TOP10,
               940000 TOP5.  Realised: OR-PROP-SHUF 920004, OR-TOP10-SHUF 930000, OR-TOP5-SHUF 940007.
  OR-PROP-INV  q rank-reversed against err (deterministic; the CINV device)
  Selector     unchanged and identical to C10/CORACLE: R2 grey-128 cutout dinoL518 embedding,
               per-cluster cosine ranking to the committed centroid, desc_nc serving order, greedy
               distinct selection over all 4,447 LAKE-RED renders. No per-cluster cap.
  Pool         HKU-IS base 4447 pairs + the 1000 selected renders (render masks); target 4040.
  Training     MyTrain.py --network SINet --task S2C --method ours --iteration 2 --seed s, all
               other flags default: the command line of every committed SINet run except paths.
  Checkpoint   Tea_epoch_best.pth of the final round (selected on CAMO-250 MAE).

Endpoints    : COD10K-test S-alpha (primary, leaky for every oracle arm -- §0);
               NC4K S-alpha (secondary, reported, never decides).
               MAE, wF, E-phi on both, reported as exploratory.

Noise        : sigma_hat = pooled within-arm sd of S-alpha over the 7 analysis arms
               {B, C10, CORACLE, OR-PROP, OR-TOP10, OR-TOP10-SHUF, OR-TOP5}, per endpoint,
               df = 7 x 2 = 14. Per-arm sds, the new-arms-only sigma_hat (df = 8) and OR's own
               sigma_hat are reported beside it and replace nothing.

Primary contrasts (Delta = mean S-alpha of first arm minus second):
  P1  OR-TOP10 - CORACLE        shape at true-error aim (C10 multiset -> top-10 equal split)
  P2  OR-TOP10 - OR-TOP10-SHUF  aim at the top-10 shape (same multiset, Jaccard 0.2158)
  P3  OR-PROP  - CORACLE        shape (flat); MECHANICALLY OVERLAPPING: Jaccard 0.5232,
                                313 of 1000 images differ -- flagged wherever reported
  P4  OR-TOP5  - CORACLE        shape-PLUS-aim (see the smaller-plan clause); never aim-isolated
Secondary: each oracle arm - B and - C10; OR-TOP10-SHUF - B. All on both endpoints.

Rule (identical to A/B/C, T2, OR):
  REAL EFFECT     iff Delta >  2*sigma_hat AND per-seed sign consistent 3/3
  WITHIN NOISE    iff |Delta| <= 2*sigma_hat
  REAL REGRESSION iff Delta < -2*sigma_hat AND per-seed sign consistent 3/3
  INCONCLUSIVE    iff |Delta| >  2*sigma_hat but sign not 3/3 -> reported as-is, NO seeds added
  Per-seed sign: sign(S_a(s) - S_b(s)) for s in {42,43,45}, pairing by training seed only.
  Four primary contrasts are judged with no multiplicity correction, as in every committed
  campaign; this is stated beside the verdicts.

Interpretation, fixed before any EXP-01 number exists:
  P1-P4 all WITHIN NOISE
    -> no true-error allocation shape tested here (flat, C10, top-10, top-5) buys a gain over the
       C10-shaped oracle resolvable at this sensitivity, although the leak favours every one of
       them. Consistent with the binding constraint sitting downstream of allocation in THIS
       pipeline (offline LAKE-RED fixed-foreground pool, two-round S2R-COD, SINet). Reported as
       "no effect resolvable at this sensitivity", never "no effect", with the largest effect the
       bar could have missed.
  P1 REAL EFFECT and P2 REAL EFFECT
    -> a concentrated, error-aimed allocation helps, and aim matters at that shape. The paper's
       "concentration, not uncertainty" reading must be qualified: once the allocation is
       concentrated, the quality of the score becomes binding. This is the outcome most damaging
       to the current framing and is reported prominently, with the leak caveat and the NC4K read.
  P1 REAL EFFECT, P2 WITHIN NOISE
    -> a shape effect with no resolvable aim specificity: concentration, not aim, at top-10.
  P2 REAL EFFECT, P1 WITHIN NOISE
    -> aim matters at the top-10 shape, but the top-10 oracle does not beat the C10-shaped one.
  Any REAL REGRESSION
    -> reported as a regression and not explained away.
  A COD10K REAL EFFECT whose NC4K Delta has the opposite sign is reported as possibly
  label-leak-driven.
  Whichever occurs is reported. No arm is dropped, no seed added, no contrast redefined, no
  endpoint or metric substituted, no result reclassified once seen.

Report       : 2*sigma_hat rule primary; paired per-seed differences; sign counts; NO p-value at
               n = 3. Supplementary, labelled post-review EXPLORATORY: Welch 95% CI with
               arm-specific sds, and the paired-seed t interval (df = 2, flagged unstable).
```

### Smaller plan, predeclared with its rationale

The guide's full EXP-01 table has nine arms. Its stated priority is B, C10, CORACLE, OR-PROP,
OR-PROP-SHUF, OR-TOP10, OR-TOP10-SHUF. This campaign departs from that table as follows, before
any training:

1. **OR-PROP-SHUF is not trained because it is uninformative, not because of cost.** Per-cluster
   error spans only 0.087–0.471, so the error-proportional quota is almost flat (4–24 per
   cluster, normalised entropy 0.989; its selection overlaps a flat centroid allocation at Jaccard
   0.837). Its frozen shuffle shares 897 of 1000 images (Jaccard 0.8132). The deterministic
   rank-reversed alternative, OR-PROP-INV, still shares 844 (Jaccard 0.7301). Both fail the
   inherited same-shape distinctness gate (Jaccard ≤ 0.50; T2.7 / OR.2.4). No permutation of this
   multiset can move more than about 16% of the images, so the aim at the flat shape cannot be
   tested with this selector. That is reported as a finding (TH-01 / AN-02), not as a run.
2. **OR-TOP5 takes the three runs freed by OR-PROP-SHUF.** It extends the shape axis to the
   reviewer's "concentrated on the truly worst clusters" at its strongest (5 clusters × 200).
3. **OR-TOP5 has no same-shape shuffle in training.** OR-TOP5-SHUF is built and passes the gate
   (Jaccard 0.1983), but it is not trained. **Every OR-TOP5 contrast is therefore shape-plus-aim
   and is never reported as aim-isolated.** The only aim-isolated contrast at a new shape is P2.
4. B, C10 and CORACLE are reused rather than retrained, under §3. If §3 fails, contrasts against
   them are labelled "not fully comparable", and P2, which is within this campaign, stays primary.

## §2 Frozen inputs (inputs only; no outcome existed when these were computed)

Produced by `rebuild/CAUS/exp01_tables.py`. The full tables are in
`STUDENT_RESULTS/RESULT_TABLES/{TH-01_quota_properties,AN-02_selection_overlap,EXP-01_quota_manifests}.csv`.
The stem lists are in `STUDENT_RESULTS/RESULT_TABLES/EXP-01_stems/`. Entropy and HHI are computed on
the realised integer shares.

| Arm | funded | max q | top-5 share | entropy_norm | HHI | Gini | Spearman(q, err) | n_displaced | quota sha256[:12] | stems sha256[:12] |
|---|---|---|---|---|---|---|---|---|---|---|
| C10 (reused) | 75 | 194 | 0.505 | 0.78668 | 0.07395 | 0.627 | +0.235 | 370 | 115a28800ae9 | 477033501309 |
| CORACLE (reused) | 75 | 194 | 0.505 | 0.78668 | 0.07395 | 0.627 | +0.996 | 509 | 33bc03e0de08 | d07054377fc6 |
| OR-PROP | 75 | 24 | 0.109 | 0.98855 | 0.01462 | 0.174 | +0.996 | 514 | 56a17e9bbb47 | 29f2685f96f7 |
| OR-TOP10 | 10 | 100 | 0.500 | 0.53332 | 0.10000 | 0.867 | +0.589 | 447 | 270e03260f7b | 84d38af6f5a4 |
| OR-TOP10-SHUF | 10 | 100 | 0.500 | 0.53332 | 0.10000 | 0.867 | −0.094 | 210 | e68449c660a0 | 705815acf05a |
| OR-TOP5 | 5 | 200 | 1.000 | 0.37277 | 0.20000 | 0.933 | +0.432 | 178 | 7e047cd15109 | 94eb645d0d40 |
| OR-PROP-SHUF (quota-only) | 75 | 24 | 0.109 | 0.98855 | 0.01462 | 0.174 | −0.045 | 477 | 2250786dccff | 47afdcaf846f |
| OR-PROP-INV (quota-only) | 75 | 24 | 0.109 | 0.98855 | 0.01462 | 0.174 | −0.996 | 474 | 157075d538b5 | 21c4ef172bfa |
| OR-TOP5-SHUF (quota-only) | 5 | 200 | 1.000 | 0.37277 | 0.20000 | 0.933 | −0.005 | 190 | 7ea6fc95a1dc | a9a63aa6b82d |

Distinctness of the decisive pairs (chance overlap = 1000²/4447 = 224.9):

| Pair | Jaccard | images differing | gate |
|---|---|---|---|
| OR-TOP10 vs OR-TOP10-SHUF | 0.2158 | 645 | PASS |
| OR-TOP5 vs OR-TOP5-SHUF | 0.1983 | 669 | PASS (not trained) |
| OR-PROP vs OR-PROP-SHUF | 0.8132 | 103 | **FAIL** |
| OR-PROP vs OR-PROP-INV | 0.7301 | 156 | **FAIL** |
| OR-TOP10 vs CORACLE | 0.4695 | 361 | disclosed |
| OR-PROP vs CORACLE | 0.5232 | 313 | disclosed (overlapping) |
| OR-TOP5 vs CORACLE | 0.4276 | 401 | disclosed |
| each new arm vs B_s42 | 0.124–0.133 | 765–780 | at chance (0.98–1.05×) |

Spearman(q, err) for the top-k arms is below 1 by construction: it ranks a vector with 65 or 70
tied zeros.

## §3 Reuse gate for the historical B / C10 / CORACLE runs

| Gate | What must hold | Status when this was committed |
|---|---|---|
| R1 code | Trainer-path source at each run's recorded commit differs from HEAD only by the opt-in `--exposure` patch (default branch untouched) and comments | PASS: 065dac6, 617a2e1, 80d2e0f, b755aa9, e16d649; each differs by the same 31-line P6 patch |
| R2 env | Shared venv training packages predate the first run | PASS: torch 2.11.0+cu128, numpy, scipy, opencv, pillow installed 8–10 Aug |
| R3 data | Every file of every primary input matches E0's manifest | PASS: 0 mismatches over raw, raw_gt, auth, auth_gt, renders, render masks, target, COD10K, CAMO-250, NC4K images |
| R4 stems | Committed C10, CORACLE, CSHUF, CINV and B_s42/43/45 stems are reproduced byte-for-byte | PASS (`exp01_alloc_test.py`) |
| R5 metrics | Re-scoring the committed predictions reproduces committed `abc_metrics.csv` at 6 dp on both endpoints | run before the pilot; recorded in `EXP-01_reuse_R5_rescore.csv` |
| R6 replay | Pilot: the historical CORACLE_s42 configuration, re-run for one epoch, reproduces the committed step-0 loss line at 4 dp | pilot |

The historical driver logs record each commit as "(dirty)" without recording what was uncommitted.
R6 is the behavioural check on that. A pass shows that initialisation, data order and the first
forward pass are identical; it does not show bit-identical training thereafter (cuDNN determinism
reduces nondeterminism but does not remove it). If R5 or R6 fails, §1 clause 4 applies.

## §4 Pilot gate (`00_pilot.sh`, ≤ 30 min, hard-capped)

The whole pilot runs under `timeout 30m`, and each step under its own `timeout`. Gate-critical
steps run first. Optional steps are skipped, with the skip recorded, once elapsed time leaves no
room for them. Every pilot output goes to a fresh folder per start. Steps:

1. Environment report: GPU, torch/CUDA, free disk, free GPU memory.
2. Pools built and gated for OR-TOP10_s42 (new code path) and CORACLE_s42 (replay).
3. Smoke test: two batches of forward, loss and backward for SINet on the OR-TOP10 pool. Losses
   must be finite.
4. One-epoch pilot: `MyTrain.py --epoch 2 --iteration 1` on OR-TOP10_s42. Must log 253 steps, with
   finite losses.
5. R6 replay: the same on CORACLE_s42, compared with the committed log.
6. Scorer and inference parity: `MyTest.py` on the historical SINet_CORACLE_s42 checkpoint for
   COD10K. PNGs are compared with the committed predictions, and Sα is re-scored against the
   committed 0.712710.
7. Optional: a CLS round-2 smoke (pseudo-labelling with the historical CORACLE_s42 checkpoint on
   this campaign's pool layout; parity and counts).
8. Optional: a rerun-from-scratch determinism repeat of step 4.

**Gate:** steps 1–6 exit 0; step 3–5 losses finite; step 4 total_step = 0253; step 5 step-0 line
equal at 4 dp; step 6 Sα re-scored from re-inferred PNGs within 1e-4 of 0.712710 (exact PNG
equality is reported, not required). A failure blocks the run scripts until it is diagnosed. A pilot
number is never evidence about any arm.

## §5 Run protocol

- Twelve scripts, one run each, ordered by seed so that a partial campaign stays balanced:
  `01..04` = s42 {OR-TOP10, OR-TOP10-SHUF, OR-PROP, OR-TOP5}, `05..08` = s43 (same order),
  `09..12` = s45 (same order).
- Each start writes into a new folder, `Result/CAUS_RUNS/<script>/<UTC stamp>_<pid>/`, holding
  `pool/` (leaf symlinks to the base pool and renders), `pool_iteration2/` (the trainer's CLS copy),
  `snap/`, `pred/{COD10K,NC4K}/` and `logs/`. A re-run never overwrites anything.
- Before training: the pool gates (counts; Image/GT stem parity; positional parity of the real
  `SrcDataset`; round-2 worst-case union parity; base bytes against E0's manifest; render mask equal
  to raw GT; stems equal to the frozen list).
- After training, the completion assertions of `abc_train.verify_run`: 2 rounds; total_step 0253;
  last epoch 039/040; Tea_epoch_best present; round-1 pool 5447; 4040 targets loaded twice. Then
  `MyTest.py` on COD10K and NC4K. Then `run_record.json` with hashes.
- Scoring happens on CPU afterwards, with `caus_score.py` (the committed scorer), checked by an
  independent S-measure on a subset.
- **Failures:** a failed run is preserved and never deleted.
  - If the cause is recoverable (I/O, OOM, environment, or an interruption that did not re-run), the
    corresponding author is told immediately, so a same-seed, same-config retry can be authorised.
    The retry is a new script with a new run folder.
  - A protocol violation is recorded as FAILED.
  - The retry needs compute beyond the 12-run allocation, so it is the author's decision.
- **Partial completion:** contrasts use only seeds complete for both arms, and the campaign status is
  PARTIAL. No arm or seed is substituted.

## §6 What EXP-01 cannot show

It cannot show that any allocation is optimal. Nor can it show that closed-loop or
foreground-generating pipelines would behave alike, that the result transfers to SINet-v2 or to a
modern detector, or that a leaky oracle's COD10K gain would be achievable without labels.

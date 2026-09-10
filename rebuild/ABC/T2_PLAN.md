# T2_PLAN.md — the falsification arms: C-shuffled and C-inverted

> **Specification, approved before any T2 code was written or any T2 pool was built.**
> Decision rule: `rebuild/ABC/PREREGISTRATION_T2.md`, committed and FROZEN.
> **TRAINS NOTHING.** This document specifies; the existing A/B/C driver trains.
>
> Dated 2026-09-10. Additive to the frozen A/B/C campaign.

---

## §T.0 What T2 is

A/B/C answered "does a **concentrated**, targeted-looking arm train better than a dispersed one?"
Its answer on the primary endpoint was WITHIN NOISE. What A/B/C could **not** answer — and said so
explicitly in its own log block (`abc_build_pools.py:325-332`, `ABC_RESULTS.md` §3.7) — is whether
the *uncertainty signal itself* contributes anything:

> WHAT ARM C IS AND IS NOT. C1's attribution audit measured the ES signal's contribution at +0.0073
> of `d` paired against its own shuffle (13/20, a coin flip) and −0.0649 against an arbitrary
> cluster (4/20). So this campaign tests whether a CONCENTRATED, more-proximal, lower-effective-rank
> arm trains better than a dispersed one. It is NOT a test of whether the uncertainty signal
> specifically helps, and no result from it may be reported as evidence about that signal.

C1's audit is decisive but lives entirely in **embedding-distance space**: permuting ES across
clusters reproduces the same Cohen's `d` (+0.91…+1.14 against a targeted +1.00…+1.23), and spending
the whole budget on an **arbitrary** cluster beats spending it on the highest-ES cluster in
**16 of 20 cells** (`C1_RESULTS.md` §8.2, `REVISION_TABLE.md:30-38`). The `d` measures
**concentration**, not **targeting**.

§6(v) of the paper claims the signal is uninformative. Nothing has yet tested that claim on
**trained accuracy**. **T2 does exactly that, and nothing else:** it holds the allocation *shape*
exactly fixed and varies only the signal's *direction*.

T2 is the experiment that discharges the disclaimer above. It is designed so that its outcome is
informative in either direction, and the interpretation of both directions is fixed in writing
before a single run.

---

## §T.1 Additivity

| Status | Item |
|---|---|
| **Frozen, untouched** | `PREREGISTRATION.md`; arms A0, A2, B, C10; all 24 committed runs; `abc_metrics.csv`, `abc_verdict.json`, `abc_sigma.json`, `abc_runs.csv`, `abc_pools.json`, `abc_preflight.json`; the three `EXP ABC` log blocks |
| **New** | two arms (`CSHUF`, `CINV`); one gap set (`--gaps t2`); one output namespace (`--tag t2` → `rebuild/ABC/out/t2/`); three `EXP T2` log blocks |
| **Reused verbatim** | `abc_build_pools.py`, `abc_train.py`, `abc_evaluate.py`, `abc_preflight.py`, `abc_common.py`, `MyTrain.py`, `MyTest.py`, `Eval/metrics.py`, C1's five allocation/selection functions |

No committed artifact is rewritten. Enforcement is mechanical, not procedural — see §T.5 and
`PREREGISTRATION_T2.md` §T2.12.

---

## §T.2 The two arms

### T.2.1 Why not "negate or reflect the ES vector"

The natural construction — invert the signal in value space before the softmax — was examined first
and rejected on two grounds, both established **before** any arm was built.

**(1) Negation and reflection are the same operation here.** `softmax_alloc`
(`c1_targeted_vs_random.py:75-81`) max-subtracts, and `np.std` is invariant under both maps:

```
negation   : es' = -es            ->  es' - max(es') = -es + min(es)          = min(es) - es
reflection : es' = max(es) - es   ->  es' - max(es') = (max-es) - (max-min)   = min(es) - es
```

Identical to float ULP, with `sd` unchanged in both. The choice between them controls nothing.

**(2) Neither preserves the allocation shape.** `target_es` spans 0.018391–0.070668 over 75 clusters
and is not symmetric, so `exp(+z)` and `exp(−z)` have different entropies. Whichever map is used,
the inverted arm would vary **direction and concentration together** — reintroducing precisely the
confound that C-shuffled's same-shape assertion exists to eliminate, and leaving
`Δ(C10 − CINV)` uninterpretable.

### T.2.2 Both arms are permutations

A permutation of the ES vector leaves `softmax_alloc`'s `p` a **permutation of C10's `p`**. Entropy,
TV-from-uniform and max are symmetric functions of the multiset `{p_c}`, so all three — and
`clusters_funded` — are preserved **exactly, by construction**. Only *which cluster receives which
budget* changes.

That yields three points on a single axis with concentration nailed down:

```
                    Spearman rho( es[sigma], es )      allocation shape
  C10   identity              +1                       entropy 0.78644, TV 0.49253, max-share 0.194
  CSHUF random perm           ~0  (|rho| <= 0.10)      IDENTICAL, asserted
  CINV  rank-reversal         -1  exactly              IDENTICAL, asserted
```

- **CINV** — `asc = argsort(es, kind='stable')`, then `sigma[asc] = asc[::-1]`. The cluster holding
  the r-th largest ES is served the allocation the (k+1−r)-th largest would have received, so budget
  flows to the **lowest-deficiency** clusters, where the model is most confident. No RNG. It is
  deliberately the **maximally anti-correlated member** of the shuffle family, not a separate
  mechanism.
- **CSHUF** — the **first** offset in `0..63` for which `default_rng(910_000 + offset).permutation(75)`
  has zero fixed points and `|Spearman(es[sigma], es)| <= 0.10`. The acceptance rule is declared in
  the pre-registration **before the draw**, so the permutation is chosen by a rule and never by
  inspection of its consequences. Exhausting 64 draws HALTS.

Everything else is C10's, unchanged: α = 1.0, k = 75, B = 1000, dinoL518, R2 grey-128 centroid
ranking, `desc_nc` serving order, greedy distinct selection, LAKE-RED render pool, the same 4447
base pool and the same 4040 target set.

---

## §T.3 Inherited properties

Each is **asserted by existing code over the new pools**, not re-implemented:

| Property | Assertion site |
|---|---|
| Real `SrcDataset` positional parity, every index, `n = 5447` | `abc_preflight.py:226-231` |
| Round-2 worst-case parity on the full union, `n = 9487` | `abc_preflight.py:240-246` |
| `E0.step_independence()` called, not re-implemented | `abc_preflight.py:112` |
| Six patches present (P0 `--source_root`, P2 cudnn determinism, …) | `abc_preflight.py:144-150` |
| cudnn determinism declared in `MyTrain.py` | `abc_preflight.py:318-329` |
| Base 4447+4447 byte-identical to E0's manifest | `abc_preflight.py:262-274` |
| Render masks pixel-identical to `raw_gt`, all selected stems | `abc_preflight.py:276-286` |
| Scorer reproduces B1's Sα = 0.717216 / MAE = 0.074463 at < 1e-5 before any new number | `abc_evaluate.py:131-140` |
| Cross-seed / cross-arch pool-content identity for deterministic arms | `abc_build_pools.py:139-150` |

**One trainer, one eval (G3).** T2 does not fork a script. `MyTrain.py` and `MyTest.py` are the same
single copies the gate counts, and the eval path is the same `abc_evaluate.py`. Identity is *proved*
by the gate rather than argued in prose.

---

## §T.4 The diff — the only new code

Four files. **No new script.** `MyTrain.py`, `MyTest.py` and `Eval/metrics.py` are untouched.

### T.4.1 `rebuild/ABC/abc_common.py` — the new allocation function, beside C10's

Constants, after line 42:

```diff
 ARMS = ('A0', 'A2', 'B', 'C10')          # C05 is the pre-registered secondary
-ARM_ALPHA = {'C10': 1.0, 'C05': 0.5}
+T2_ARMS = ('CSHUF', 'CINV')              # PREREGISTRATION_T2.md -- additive, dated
+ARM_ALPHA = {'C10': 1.0, 'C05': 0.5, 'CSHUF': 1.0, 'CINV': 1.0}
+# T2: how each C-family arm permutes the COMMITTED target_es vector before the
+# softmax. None is C10's identity. BOTH T2 transforms are PERMUTATIONS, so the
+# allocation SHAPE is preserved exactly and only the cluster->budget assignment
+# changes (PREREGISTRATION_T2.md T2.4).
+ARM_ES_PERM = {'C10': None, 'C05': None,
+               'CSHUF': 'shuffled', 'CINV': 'rank_reversed'}
+SHAPE_KEYS = ('clusters_funded', 'max_alloc_share',
+              'alloc_entropy_norm', 'tv_from_uniform')   # n_displaced EXCLUDED
+SHUF_NS = 910_000        # T2 C-shuffled permutation namespace
+SHUF_MAX_RHO = 0.10      # |Spearman(es[sigma], es)| acceptance bound
+SHUF_TRIES = 64          # declared before the draw; exhausting it is a HALT
+T2_MAX_JACCARD = 0.50    # C-vs-C distinctness gate (PREREGISTRATION_T2.md T2.7)
```

Output namespacing, after line 32:

```diff
+def set_out(tag=''):
+    """Point OUT at a subdirectory so an additive campaign cannot overwrite a
+    committed one. tag='' is A/B/C's own path, unchanged. Every ABC script
+    rebinds its own OUT from this in main(), so one switch moves all of them."""
+    global OUT
+    OUT = os.path.join(C.exp_dir(EXP, 'out'), tag) if tag else C.exp_dir(EXP, 'out')
+    return OUT
```

The permutation, immediately before `arm_c_stems`:

```diff
+def _spearman_perm(es, sigma):
+    """Spearman rho between the permuted ES vector es[sigma] and es itself.
+    +1 identity (C10), -1 rank-reversing (CINV), ~0 a random permutation (CSHUF).
+    THIS -- not index order -- is what says whether an arm still targets what the
+    real signal targets; cluster indices are arbitrary k-means labels. target_es
+    has 75 distinct floats, so ranks are an exact argsort-of-argsort and scipy is
+    not needed."""
+    r = np.argsort(np.argsort(es, kind='stable'), kind='stable').astype(np.float64)
+    a, b = r[sigma] - r.mean(), r - r.mean()
+    return float(a @ b / np.sqrt((a @ a) * (b @ b)))
+
+
+def es_permutation(es, kind):
+    """The T2 cluster permutation sigma, with es_used = es[sigma].
+
+    A permutation leaves softmax_alloc's p a permutation of C10's p, so
+    alloc_entropy_norm, tv_from_uniform, max_alloc_share and clusters_funded are
+    preserved EXACTLY -- same shape, different target. Only the cluster->budget
+    assignment, hence the selected image set and n_displaced, change.
+
+      None            identity; arm_c_stems reproduces C10 bit for bit.
+      'rank_reversed' the unique rank-reversing map: the cluster with the r-th
+                      largest ES is served the allocation the (k+1-r)-th largest
+                      would have received, so budget flows to the LOWEST-
+                      deficiency clusters. rho = -1 exactly. No RNG.
+      'shuffled'      the FIRST offset in 0..SHUF_TRIES-1 whose
+                      default_rng(SHUF_NS + offset) permutation has no fixed point
+                      and |rho| <= SHUF_MAX_RHO. The acceptance rule is declared in
+                      PREREGISTRATION_T2.md BEFORE the draw, so the permutation is
+                      chosen by a rule and never by inspection.
+
+    Deterministic in every branch: no seed argument, so the arm is identical
+    across the three TRAINING seeds, exactly like C10.
+    """
+    k = len(es)
+    if kind is None:
+        return np.arange(k), dict(es_perm='identity', perm_rho=1.0,
+                                  perm_fixed_points=k, perm_seed=None)
+    if kind == 'rank_reversed':
+        asc = np.argsort(es, kind='stable')
+        sigma = np.empty(k, dtype=np.int64)
+        sigma[asc] = asc[::-1]
+        return sigma, dict(es_perm='rank_reversed',
+                           perm_rho=round(_spearman_perm(es, sigma), 5),
+                           perm_fixed_points=int((sigma == np.arange(k)).sum()),
+                           perm_seed=None)
+    if kind == 'shuffled':
+        for off in range(SHUF_TRIES):
+            sigma = np.random.default_rng(SHUF_NS + off).permutation(k)
+            fx = int((sigma == np.arange(k)).sum())
+            rho = _spearman_perm(es, sigma)
+            if fx == 0 and abs(rho) <= SHUF_MAX_RHO:
+                return sigma, dict(es_perm='shuffled', perm_rho=round(rho, 5),
+                                   perm_fixed_points=fx, perm_seed=int(SHUF_NS + off))
+        raise RuntimeError('T2 HALT: no permutation in %d draws from %d met the '
+                           'declared rule (no fixed point, |rho| <= %.2f)'
+                           % (SHUF_TRIES, SHUF_NS, SHUF_MAX_RHO))
+    raise ValueError('unknown es_perm %r' % kind)
```

`arm_c_stems` — six changed lines (112-131):

```diff
-def arm_c_stems(alpha):
-    """Reuse C1's committed selection. Returns (stems, measured_cell)."""
+def arm_c_stems(alpha, es_perm=None):
+    """Reuse C1's committed selection. Returns (stems, measured_cell).
+
+    es_perm=None reproduces C10 EXACTLY -- same call, same numbers, byte-identical
+    stem list. Any other value permutes the COMMITTED target_es vector before the
+    softmax and changes NOTHING else: same alpha, same budget, same R2 centroid
+    ranking, same desc_nc serving, same greedy distinct selection. That single
+    substitution is the whole T2 intervention.
+    """
     import c1_space
     from c1_targeted_vs_random import (softmax_alloc, largest_remainder,
                                        rank_by_centroid, serving_orders,
                                        greedy_select)
     sp = c1_space.load_space(EMBEDDER)
-    p = softmax_alloc(sp.es, alpha)
+    sigma, info = es_permutation(sp.es, es_perm)
+    es = sp.es if es_perm is None else sp.es[sigma]
+    p = softmax_alloc(es, alpha)
     alloc = largest_remainder(p, BUDGET)
     _, order = rank_by_centroid(sp)
-    serving = serving_orders(alloc, sp.es)[SERVING]
+    serving = serving_orders(alloc, es)[SERVING]      # desc_nc reads alloc only
     idx, disp = greedy_select(alloc, order, serving)
     cell = dict(
         clusters_funded=int((alloc > 0).sum()),
         max_alloc_share=round(float(alloc.max() / BUDGET), 5),
         alloc_entropy_norm=round(float(-(p[p > 0] * np.log(p[p > 0])).sum()
                                        / np.log(sp.k)), 5),
         tv_from_uniform=round(float(0.5 * np.abs(p - 1.0 / sp.k).sum()), 5),
         n_displaced=int(disp))
+    cell.update(info)
     return [sp.names[i] for i in idx], cell
```

`arm_added` — one line (149-151):

```diff
     if arm in ARM_ALPHA:
-        return 'SOD_', 'SOD_', arm_c_stems(ARM_ALPHA[arm])[0], \
+        return 'SOD_', 'SOD_', arm_c_stems(ARM_ALPHA[arm], ARM_ES_PERM[arm])[0], \
                (REN_IMG, '.jpg'), (REN_MSK, '.png')
```

**C10 is unaffected.** `ARM_ES_PERM['C10'] is None`, so every C10 call path takes the identity
branch and returns the identical stem list. The extra `cell` keys are inert: both consumers iterate
a fixed key set (`abc_build_pools.py:106`, `abc_preflight.py:292`).

### T.4.2 `rebuild/ABC/abc_preflight.py` — generalise G5 from `C10` to the C-family

Three hard-coded `('C10', 1.0)` sites, plus the two new checks. Add `import itertools`.

```diff
+    # every distinct C-family arm actually in this run set
+    cfam = [m for m in dict.fromkeys(m for _, m, _ in runs) if m in A.ARM_ALPHA]
+
     # the 1000 render masks equal raw_gt, for every distinct arm-B/C stem set
-    for label, stems in [('C10', A.arm_c_stems(1.0)[0])] + \
+    for label, stems in [(m, A.arm_c_stems(A.ARM_ALPHA[m], A.ARM_ES_PERM[m])[0])
+                         for m in cfam] + \
                         [('B_s%d' % s, A.arm_b_stems(s)) for s in A.SEEDS]:
```

```diff
-    # arm-C reproduction of C1's committed cell
-    repro = {}
-    for arm, alpha in (('C10', 1.0),):
-        _, cell = A.arm_c_stems(alpha)
-        repro[arm] = dict(measured=cell, c1=A.C1_CELL[alpha],
-                          match=all(cell[k] == A.C1_CELL[alpha][k] for k in A.C1_CELL[alpha]))
+    # C-family reproduction. C10 must reproduce C1's committed cell in FULL. A T2
+    # permutation arm must reproduce its SHAPE keys exactly -- the same-shape
+    # assertion (PREREGISTRATION_T2.md T2.4). n_displaced is a consequence of the
+    # allocation, so it is REPORTED and never asserted for a permuted arm.
+    repro = {}
+    for arm in cfam:
+        alpha = A.ARM_ALPHA[arm]
+        _, cell = A.arm_c_stems(alpha, A.ARM_ES_PERM[arm])
+        keys = A.SHAPE_KEYS if A.ARM_ES_PERM[arm] else tuple(A.C1_CELL[alpha])
+        repro[arm] = dict(measured=cell, c1=A.C1_CELL[alpha], asserted=list(keys),
+                          match=all(cell[k] == A.C1_CELL[alpha][k] for k in keys))
```

```diff
-    # overlap(B, C) against chance
-    sc = set(A.arm_c_stems(1.0)[0])
-    chance = A.BUDGET * A.BUDGET / 4447.0
-    ov = {}
-    for s in A.SEEDS:
-        sb = set(A.arm_b_stems(s))
-        ov['s%d' % s] = dict(overlap=len(sb & sc), chance=round(chance, 1),
-                             ratio=round(len(sb & sc) / chance, 3),
-                             jaccard=round(len(sb & sc) / len(sb | sc), 4))
+    # pairwise overlap against chance over every distinct selected set in play
+    chance = A.BUDGET * A.BUDGET / 4447.0
+    sets = {m: set(A.arm_c_stems(A.ARM_ALPHA[m], A.ARM_ES_PERM[m])[0]) for m in cfam}
+    sets.update({'B_s%d' % s: set(A.arm_b_stems(s)) for s in A.SEEDS})
+    ov = {}
+    for a, b in itertools.combinations(sorted(sets), 2):
+        x, y = sets[a], sets[b]
+        kind = ('CxC' if a in A.ARM_ALPHA and b in A.ARM_ALPHA
+                else ('BxB' if a not in A.ARM_ALPHA and b not in A.ARM_ALPHA else 'BxC'))
+        ov['%s|%s' % (a, b)] = dict(overlap=len(x & y), chance=round(chance, 1),
+                                    ratio=round(len(x & y) / chance, 3),
+                                    jaccard=round(len(x & y) / len(x | y), 4),
+                                    n_differing=A.BUDGET - len(x & y), kind=kind)
```

```diff
     ok = bool(all(... unchanged per-pool clauses ...)
               and all(v['match'] for v in repro.values())
-              and all(0.7 <= v['ratio'] <= 1.3 for v in ov.values()))
+              and all(0.7 <= v['ratio'] <= 1.3
+                      for v in ov.values() if v['kind'] == 'BxC')
+              # T2.7 distinctness: two C-family arms sharing most of their images
+              # cannot test the claim -- a null would be mechanical.
+              and all(v['jaccard'] <= A.T2_MAX_JACCARD
+                      for v in ov.values() if v['kind'] == 'CxC'))
```

Write to the namespaced OUT (line 356):

```diff
-    C.save_json(os.path.join(OUT, 'abc_preflight.json'), report)
+    C.save_json(os.path.join(A.OUT, 'abc_preflight.json'), report)   # A.set_out() moves it
```

**Equivalence for the frozen campaign.** With A/B/C's arm set there is exactly one C-family arm, so
`CxC` is empty and the new clause is vacuously true; `BxB` was previously unmeasured and is now
reported but not gated; `BxC` is the identical old band; and `cfam == ['C10']` restores the old
`repro` on all five keys. **Re-running the A/B/C pre-flight under this diff yields the same pass/fail
decision.** Verified as step 7 of §T.7.

### T.4.3 `rebuild/ABC/abc_build_pools.py` — emit the T2 stem lists, namespace the output

```diff
+    ap.add_argument('--tag', default='', help='output namespace; "t2" is additive')
     args = ap.parse_args()
     arms = tuple(a.strip() for a in args.arms.split(',') if a.strip())
     skip = {s.strip() for s in args.skip_gate.split(',') if s.strip()}
+    global OUT, EXP
+    OUT = A.set_out(args.tag)
+    EXP = 'T2' if args.tag == 't2' else A.EXP
     os.makedirs(OUT, exist_ok=True)
```

```diff
-    for arm, alpha in (('C10', 1.0),):
-        st, cell = A.arm_c_stems(alpha)
+    for arm in [m for m in arms if m in A.ARM_ALPHA]:
+        alpha = A.ARM_ALPHA[arm]
+        st, cell = A.arm_c_stems(alpha, A.ARM_ES_PERM[arm])
         sel[arm] = st
-        with open(os.path.join(OUT, 'abc_stems_C_a%.1f.txt' % alpha), 'w') as fh:
+        name = ('abc_stems_C_a%.1f.txt' % alpha if A.ARM_ES_PERM[arm] is None
+                else 'abc_stems_%s.txt' % arm)
+        with open(os.path.join(OUT, name), 'w') as fh:
             fh.write('\n'.join(st) + '\n')
-        _p('  arm %s: %d stems, C1 cell reproduced = %s'
-           % (arm, len(st), all(cell[k] == A.C1_CELL[alpha][k] for k in A.C1_CELL[alpha])))
+        keys = A.SHAPE_KEYS if A.ARM_ES_PERM[arm] else tuple(A.C1_CELL[alpha])
+        _p('  arm %-6s %d stems, perm=%-13s rho=%+.5f  shape reproduced = %s'
+           % (arm, len(st), cell['es_perm'], cell['perm_rho'],
+              all(cell[k] == A.C1_CELL[alpha][k] for k in keys)))
```

The block-#1 metric loop (211-218) becomes `overlap_%s` keyed by the pair name, additionally emits
`n_differing` and the per-arm `perm_seed` / `perm_rho` / `n_displaced`, and gains one threshold line
for the distinctness gate. The `--arms` echo in the `log_block` command string is already dynamic.

### T.4.4 `rebuild/ABC/abc_evaluate.py` — the T2 gap set and the reference-arm consistency check

```diff
+GAPS = {'abc': (('A2', 'B'), ('B', 'C10'), ('A0', 'B'), ('A0', 'C10'), ('A0', 'A2')),
+        't2':  (('CSHUF', 'C10'), ('CINV', 'C10'), ('CINV', 'CSHUF'))}
```

```diff
     ap.add_argument('--arms', default=','.join(A.ARMS))
+    ap.add_argument('--gaps', default='abc', choices=sorted(GAPS),
+                    help='which FROZEN gap set to apply; "t2" is '
+                         'PREREGISTRATION_T2.md, additive')
+    ap.add_argument('--tag', default='')
     ...
+    global OUT, EXP
+    OUT = A.set_out(args.tag)
+    EXP = 'T2' if args.tag == 't2' else A.EXP
```

```diff
-            for lo, hi in (('A2', 'B'), ('B', 'C10'), ('A0', 'B'), ('A0', 'C10'), ('A0', 'A2')):
+            for lo, hi in GAPS[args.gaps]:
```

New consistency check, immediately after `rows` is built:

```diff
+    # T2 re-scores the COMMITTED B and C10 predictions to build the sigma_hat
+    # pool through this same code path. They must reproduce abc_metrics.csv or
+    # something drifted between the campaigns.
+    ref = os.path.join(C.exp_dir(A.EXP, 'out'), 'abc_metrics.csv')   # A/B/C's own path
+    if args.tag and os.path.isfile(ref):
+        old = {(r['runid'], r['endpoint']): float(r['Sm'])
+               for r in csv.DictReader(open(ref))}
+        bad = [(r['runid'], r['endpoint'], r['Sm'], old[(r['runid'], r['endpoint'])])
+               for r in rows if (r['runid'], r['endpoint']) in old
+               and abs(r['Sm'] - old[(r['runid'], r['endpoint'])]) > 1e-9]
+        if bad:
+            raise SystemExit('T2 HALTED: reference arms do not reproduce '
+                             'abc_metrics.csv: %s' % bad[:5])
+        _p('  reference arms reproduce abc_metrics.csv: %d cells, max delta < 1e-9'
+           % sum(1 for r in rows if (r['runid'], r['endpoint']) in old))
```

The reference path is computed directly rather than via `set_out('')`, so reading A/B/C's committed
metrics never mutates the module-level `OUT` that T2's own artifacts are written to.

`abc_train.py` needs only the same three-line `--tag` / `OUT` / `EXP` preamble; its
`--arms CSHUF,CINV` path is already generic.

---

## §T.5 Pre-flight gates and the two new checks

All six A/B/C gates run unchanged over the new pools, with no `--skip-gate`. Two checks are added
inside G5.

| Check | Rule | On failure |
|---|---|---|
| **Same-shape** (§T2.4) | `clusters_funded == 75`, `max_alloc_share == 0.194`, `alloc_entropy_norm == 0.78644`, `tv_from_uniform == 0.49253`, at exact equality of the 5-dp rounded values (|Δ| < 5e-6). `n_displaced` excluded. | **HALT.** A failure means the transform was not a permutation — a code defect. Never widen the tolerance. |
| **Distinctness** (§T2.7) | `Jaccard ≤ 0.50` for every C×C pair. | **HALT before training.** Report the number and redesign. |

Retained without modification: C10's full five-key cell reproduction; the B×C chance band 0.7–1.3×;
real-`SrcDataset` positional parity for every index at `n = 5447`; round-2 worst-case parity at
`n = 9487`; base bytes vs E0's manifest; render masks vs `raw_gt`; `E0.step_independence()`;
patch marks; cudnn determinism.

---

## §T.6 Run accounting and order

| # | Step | Command | Cost |
|---|---|---|---|
| 1 | Commit both documents **and** the diff before any run | — | — |
| 2 | Build both pools; six gates; the two new checks | `abc_build_pools.py --arms CSHUF,CINV --tag t2` | ~10 min, 0 GPU |
| 3 | **Halt points:** any gate FAIL · shape assertion FAIL · `Jaccard(C10,CSHUF) > 0.50` · C10 full-cell drift | — | — |
| 4 | Sanity check — `SINet_CSHUF_s42` trains **and** evaluates end to end without error | `abc_train.py --arms CSHUF --tag t2`, then evaluate that RUNID | ~1.8 h |
| 5 | Remaining 11 runs, two at a time, one per GPU | `abc_train.py --arms CSHUF,CINV --tag t2` | ~22 GPU-h |
| 6 | Infer + score the 12 new runs; **re-score** committed B and C10 (no training, no inference) | `abc_evaluate.py --arms B,C10,CSHUF,CINV --gaps t2 --tag t2 --gpus 0,1 --workers 4` | ~1.5 h |
| 7 | `EXP T2` blocks #1/#2/#3 → `results/REBUILD_LOG.txt`; `T2_RESULTS.md` with the verdict block | — | — |

**12 training runs** = 2 architectures × 2 new arms × 3 seeds. At the campaign's reference wall times
(SINet 104.5 min, SINet-v2 131.0 min): 6 × 104.5 + 6 × 131.0 = **1413 min ≈ 23.6 GPU-h**, ≈ **12 h on
2 GPUs**, plus ~1.5 h evaluation. Disk: 12 hard-linked pools (≈0) plus 12 CLS round-2 pools (real
files, ~9.5k images each).

---

## §T.7 Verification

Before training:

1. `abc_build_pools.py --arms CSHUF,CINV --tag t2` prints `PASS` for all six gates and exits 0.
2. `rebuild/ABC/out/t2/abc_preflight.json`: `armC_reproduces_C1['CSHUF'].match == true` and
   `['CINV'].match == true` on the four `SHAPE_KEYS`, with `measured.alloc_entropy_norm == 0.78644`,
   `tv_from_uniform == 0.49253`, `max_alloc_share == 0.194`, `clusters_funded == 75`.
3. `perm_rho` ≈ 0 for CSHUF (|ρ| ≤ 0.10) and exactly −1.0 for CINV; `perm_fixed_points == 0` for
   CSHUF and **exactly 1** for CINV — structurally necessary at odd k, see `PREREGISTRATION_T2.md`
   §T2.3; `perm_seed` recorded for CSHUF.
4. Every C×C `jaccard ≤ 0.50`; every B×C pair still `0.7 ≤ ratio ≤ 1.3`; `n_differing` recorded.
5. `pools_SrcDataset_parity_all_i == 12/12`; `pools_total_parity_mismatches == 0`;
   `pools_round2_worstcase_parity == 12/12`; `base_bytes_mismatched_vs_E0_manifest == 0`;
   `forbidden_path_references == 0`.
6. Cross-seed identity: the three `image_digest` values per (arch, T2 arm) are equal.
7. **Regression on the frozen campaign:** `abc_build_pools.py --arms A0,A2,B,C10 --no-log` (no
   `--tag`) still reports 6/6 with an unchanged C10 cell, and its emitted stem list is byte-identical
   to the committed `rebuild/ABC/out/abc_stems_C_a1.0.txt`.
8. `git status` shows no modification under `rebuild/ABC/out/` other than the new `t2/` subdirectory.

After training: `t2/abc_verdict.json` carries `sigma_hat`, `df == 8`, `per_arm_sd` for all four arms,
and the three T2 gaps with their bands, per architecture per endpoint.

---

## §T.8 What T2 cannot answer

Stated before results, so it cannot be softened after them.

1. **Sensitivity.** At A/B/C's committed COD10K σ̂ the bar is ≈ 0.0179 (SINet) and ≈ 0.0123
   (SINet-v2) — comparable to the paper's entire MT→Ours gap of 0.0142. C1's +0.0073 of a Cohen's
   `d` is a geometric quantity and predicts no accuracy difference at all. **A WITHIN NOISE result
   means "no effect resolvable at this sensitivity," never "no effect."**
2. **T2 says nothing about concentration.** It varies *direction* at exactly fixed concentration.
   Whether concentration itself helps is A/B/C's `Δ(C10 − B)` question, already answered WITHIN
   NOISE.
3. **CINV is a permutation**, hence formally a member of the shuffle family — deliberately its
   maximally anti-correlated member. It is not a test of a value-space inversion, which §T.2.1 shows
   would have been uninterpretable here.
4. **Set overlap attenuates.** Even under the 0.50 gate, C-family arms share images by construction.
   `n_differing` is reported with every verdict so the true contrast is visible.
5. **n = 3.** No p-value, no bootstrap, no correction. Three gaps, one bar, sign-consistency counts.

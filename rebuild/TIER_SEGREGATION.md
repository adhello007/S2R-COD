# TIER_SEGREGATION.md — what generalizes, and how far

**What this file is.** A scope classification of every finding in `rebuild/FINAL_RESULTS.md`. It
decides which findings can support a main-track claim and which are properties of this particular
instantiation. It introduces **no new numbers**: every value here is quoted from a committed result
document or `EXP` log block, cited as in `FINAL_RESULTS.md`.

**What this file is not.** It does not decide the paper's section structure and makes no claim that is
not traceable to a committed artifact.

## The tier definitions

- **Tier 1** — the finding is specific to **the CSRDA framework or the LAKE-RED generator**. It is a
  property of this training loop or this generator.
- **Tier 2** — the finding concerns **the target data or the uncertainty signal**, and travels beyond
  this instantiation.
- **Tier 3** — the finding is **independent of the method entirely**. It would stand unchanged if the
  method under test had worked.

**Derivation note.** These tiers were assigned from the committed result documents alone.
`rebuild/PAPER/` (`PAPER_PLAN.md`, `main.tex`, `main.pdf`) is gitignored and untracked, is therefore
not a committed artifact, and was **not** consulted — see `FINAL_RESULTS.md` §16(e). If that
directory contains a tier map, this one may disagree with it, and the disagreement has not been
reconciled.

**Assignment rule used.** Where a finding has a mechanism at one tier and a consequence at another,
both are stated (written `Tier 1 → Tier 2`), because collapsing them is precisely how a Tier 1 cause
gets read as a Tier 2 claim. Where the tier is genuinely arguable, the finding appears in §5 with
both readings rather than being silently assigned.

## A naming hazard, restated

`T1`/`T2`/`T3` are overloaded four ways in this repository. **In this file, scope tiers are always
written "Tier 1 / Tier 2 / Tier 3", spelled out.** A bare `T2` never means a tier here: `EXP T2` and
`EXP T2C` are experiments; `T1`…`T8` inside an experiment are that experiment's own pre-registered
threshold labels; `trap T1/T2/T3` are the data traps in `REBUILD_PLAN.md` §2.

---

# 1. Master table

| # | Finding | Source | Tier | Why this tier | Generalizes to |
|---|---|---|---|---|---|
| 1 | `total_step` is pinned at **253** (SINet) / **127** (SINet-v2) in both rounds of all 24 runs, independent of pool size | ABC | **Tier 1** | A property of this training loop's schedule: adding data buys no optimisation here | Nothing beyond this loop. It is a fact about CSRDA's step budget, not about synthetic data |
| 2 | The render set is a **bijection** onto the 4447 raw foregrounds — **0** outside, **0** unrendered, on both pools | D1 | **Tier 1 → Tier 2** | Mechanism is LAKE-RED's `isReplace`; the consequence — the null is scoped to an exhausted foreground supply — travels | Any generator that composites a fixed foreground set; and the scoping sentence any such null must carry |
| 3 | Object pixels are **copied, not generated**: interior error **5.603** / **9.633** against backgrounds **70.802** / **70.555**; **0** of 8885 objects regenerated | D1 (E0 at n=200) | **Tier 1** | A measured property of LAKE-RED's `--isReplace` compositing | The measurement design (interior-vs-background error ratio) is reusable on any inpainting generator |
| 4 | LAKE-RED regenerates **4447/4447** images and masks **byte-identical** at `--seed 0` | E0 | **Tier 1** | Reproducibility of this generator on this stack; source scopes it to *"this machine with this stack"* | Nothing. It is a provenance claim |
| 5 | A render is **not** a function of (image, mask) — it depends on **position-in-shard**; T1 diverges at **36.738** / **40.338**, T3 collapses to **0.0** | D2 | **Tier 1** | A property of LAKE-RED's per-process seeding and stride sharding | Any batched diffusion pipeline that seeds once per process — a reusable caution, not a result |
| 6 | Generator seed variance moves one fixed foreground by **~37–40** grey levels | D2 | **Tier 1** | Measured on this generator, on one foreground | Sets the feasibility scale for best-of-K schemes on this generator only |
| 7 | The conditioning channel is **not narrow** — four routes, the dominant one bypassing the 48-scalar summary; `fuse` weight norm **0.907 vs 0.810** | A1 | **Tier 1** | A fact about LAKE-RED's architecture, read from source | Nothing. **A withdrawn cause**, not a positive claim |
| 8 | `Δ(C − B)` is **WITHIN NOISE** on both architectures and both endpoints | ABC | **Tier 1** | The null itself is a property of this loop, this generator and this budget | Nothing on its own. Its reach comes entirely from the Tier 2 causes beneath it |
| 9 | The campaign is **underpowered against its own statement**: `2σ̂ = 0.017933` against a reference gap of **0.0142** | ABC | **Tier 1** | A property of this campaign's design and seed count | Nothing — but it bounds every claim built on finding 8 |
| 10 | The **unpadded** arm A0 is the unstable arm in both architectures (sd **0.017266** / **0.010575**), and it is **unexplained** | ABC | **Tier 1** | A property of this loop's exposure schedule; no mechanism offered | Nothing. Explicitly *"a concrete follow-up, not a finding"* |
| 11 | Pseudo-labelling is a **second uncontrolled channel**: `n_appended` spread **22.2 %** (ABC) and **17.6 %** (T2) against a 5 % bound | ABC, T2 | **Tier 1** | A property of CSRDA's CLS selection rule (`edge_loss < u·avg_loss` on each arm's own round-1 model) | Any self-training loop where the pseudo-label filter depends on the arm's own model — a design caution |
| 12 | `S2C_SO`'s correlation inversion (ρ(MAE) **+0.402**) reproduces in all three embedding spaces | B1 | **Tier 1** | A property of the source-only training variant: no consistency loss, never forwards a target image | Any EMA-teacher scheme where the source-only ablation lacks the teacher's provenance |
| 13 | CAMO is the **checkpoint-selection set**, and it is the published CAMO **test** split (`MyTrain.py:221`) | D2 | **Tier 1** | A property of this repository's training protocol | A reporting caution: CAMO can never be an endpoint here |
| 14 | CHAMELEON was never a **sanctioned** endpoint in this repository — README lists it as CNC **source** only; **0** CHAMELEON predictions under `Result/` | D2R | **Tier 1** | A fact about this repository's documented design, and a correction to **our own** plan | Nothing about the literature. D2R states this explicitly |
| 15 | The target set **barely has cluster structure**: best silhouette **0.1600**, and **0.1465** / **0.0568** in the other two spaces | B1 | **Tier 2** | A property of the COD target data itself, measured in three independent embedding spaces | **Any** method that allocates a budget over clusters of this target distribution |
| 16 | An arbitrary preprocessing choice **reassigns 5.4 %** of cluster memberships (agreement **94.6 %**, mean cosine **0.9308**) | E0 | **Tier 2** | A property of clustering this image distribution, not of the generator | Any cluster-membership-defined metric on this data; sets a floor below which no effect is attributable to targeting |
| 17 | The "target distribution" is a **two-dataset mixture** (3040 COD10K + 1000 CAMO) whose components separate at **0.8648 / 0.8592 / 0.9225** | A3 | **Tier 2** | A property of the target data as constructed | Any experiment treating this target pool as one distribution; and a general caution about mixture targets |
| 18 | Uncertainty predicts **pixel** error far better than **structural** error: ρ(MAE) **+0.8553** vs ρ(1−Sα) **+0.4276** per-cluster; **+0.7514** vs **+0.3114** per-image | B1 | **Tier 2** | A property of the uncertainty signal against COD error metrics | Sharpened and extended by finding 19 — see there for the honest claim |
| 19 | **The ordering is not a property of ES.** `ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)` passes **8/8** whole-image rows across three signals × two architectures | T2C | **Tier 2** | Holds for predictive entropy and ensemble disagreement as well as ES — it is a property of the signal **class** and the problem | **Uncertainty-guided allocation for COD in general** — the broadest Tier 2 finding in the suite |
| 20 | The **magnitude** does not generalise: ρ(1−Sα) reaches **+0.54 to +0.56** on SINet-v2 | T2C | **Tier 2** | The same measurement bounds its own claim | Forces the claim to be **ordinal and comparative**, never "uncertainty carries no localisation information" |
| 21 | The **real** allocation signal is materially weaker than the endpoint-measured one: ρ drop **+0.2100** / **+0.2470** | B1 | **Tier 2** | A property of the uncertainty signal measured where it is actually available | Any allocation scheme validated on a signal measured on the test set — it will overstate the usable signal |
| 22 | The ES signal contributes **+0.0073** of a *d* against its own shuffle (**13/20**, a coin flip) and **−0.0649** against an arbitrary cluster (**4/20**) | C1 | **Tier 2** | A property of the uncertainty signal in embedding geometry | The separation credited to "targeting" is available from **concentration alone** |
| 23 | **The declared ceiling is a concentration ceiling, not a targeting ceiling**: `mean +0.0077`, top-ES wins **10/20** | C1 | **Tier 2** | Cross-checked across two scripts in two runs; a property of the signal, not the loop | Any "allocate to the highest-uncertainty cluster" heuristic on data with this cluster structure |
| 24 | Targeting buys **average proximity, not coverage**: effective rank ratio **0.53–0.64** in **20/20** cells, coverage Δ ≈ 0, top-1 similarity up to **+0.096** | C1 | **Tier 2** | A geometric property of cluster-wise budget allocation | Any concentration-based selection: it narrows the selected set rather than extending its reach |
| 25 | **On trained accuracy, real / destroyed / reversed targeting are indistinguishable — 12/12 WITHIN NOISE**, at a bar **3.24×** tighter than the preceding campaign | T2 | **Tier 2** *(measured only in this loop — see §3)* | Concerns the uncertainty signal's **direction**, at exactly fixed concentration | The strongest available statement that this uncertainty signal's direction carries no accuracy-relevant information |
| 26 | **CHAMELEON is 41/76 (53.9 %) re-encoded training data**, and exact hashing calls it perfectly clean (**0** collisions) | D2 | **Tier 3** | A fact about two datasets. Independent of whether the method worked | Every COD paper reporting a CHAMELEON column |
| 27 | **`CHAMELEON ∩ COD10K-train = 40/76`** — a fact about **two public benchmarks** | D2R | **Tier 3** | Author-sourced release, byte-identical to the repo copy (**76/76**) | *"the CHAMELEON column is not an independent measurement for the whole class of COD10K-trained methods"* |
| 28 | **41 is a property of the data, not of the cutoff**: gap at **41 below 5.51, next at 40.58** (**7.36×**), invariant at shortlist depth 8 / 32 / all | D2, D2R | **Tier 3** | A structural property of the distance distribution | Makes the count defensible without arguing about a tolerance — a reusable audit design |
| 29 | **No difficulty skew, so no inflation figure**: all eight percentiles in **0.448–0.559**; `split_direction_agrees_across_mask_sets` = **False** | D2R | **Tier 3** | A measured null about the datasets | *"A protocol violation does not need a score advantage to be disqualifying"* |
| 30 | **The two CHAMELEON mask releases are different annotations**: aligned IoU **0.6932**, **27/76** identical, and the choice moves MAE by **2.7×** | D2R | **Tier 3** | Entirely unrelated to contamination or to the method | A second, independent reason published CHAMELEON numbers are not comparable across papers |
| 31 | **NC4K is clean on both axes**: **0/4121**, min nearest **20.610** = **3.44×** the tolerance, no gap | D2_NC4K | **Tier 3** | A measured null about two public datasets | The negative control that makes finding 26 credible — the detector does not find contamination everywhere |
| 32 | **Unchecked is not clean**: **73.7 %** of NC4K and **25/76** of CHAMELEON have no same-dimension candidate at all | D2, D2R, D2_NC4K | **Tier 3** | A property of the audit method, applying to every rate it produces | Every contamination rate in this literature is a **lower bound** unless the unchecked share is stated |
| 33 | **A real-vs-synthetic AUC near 1.0 is near-vacuous**: a JPEG-30 re-encode of the *identical* images separates them at **0.9928**, above both real-vs-real controls and **0.0067** short of the headline | A3 | **Tier 3** *(boundary — see §5)* | A property of the metric, demonstrated with content held identical | Any paper using linear-probe AUC to argue two image sets are distributionally different |
| 34 | **In-sample effect-size estimation manufactures effects from nothing**: **+0.6991** on a true null, reaching **+1.4506** — larger than the headline it would have supported | C1 (reproduced by A3 at **0.6867 / 0.6805 / 0.4854**) | **Tier 3** | A property of the estimator, independent of the data and the method | Any *d*-style separation claim fitted and evaluated on the same split |
| 35 | Exact hashing is the **wrong instrument** for contamination and returns a confidently clean answer — demonstrated on the original work **and on D2's own first implementation** (10/76 vs 41/76) | D2 | **Tier 3** | A methodological finding about contamination auditing | Every dataset-overlap audit that reports byte or pixel identity as "clean" |
| 36 | The **synthetic pools cover the target manifold at 0.13–0.54** while every real set covers it at **0.71–0.90**, including real photographs of a different genre | A3 | **Tier 1** *(boundary — see §5)* | It measures **LAKE-RED's** output, so by the letter of the definitions it is generator-specific | The *measurement design* — a paired within-content coverage delta against the generator's own input pool — is reusable on any generator |
| 37 | A grep is not a provenance gate; a gate that has never failed is not evidence | E0 | **Tier 3** | A research-hygiene finding, independent of the method | Reusable audit practice; not a measurement about COD |

---

# 2. Tier 1 — findings specific to CSRDA or LAKE-RED

**These carry the largest apparent force in the account of the failure, and they are the ones a
reviewer can most easily set aside.** For each, the dismissal a reviewer could legitimately make is
stated, because that dismissal is the finding's ceiling.

### 1. `total_step` is pinned (ABC, finding 1)

`total_step` pinned at **253** / **127** *"in **both** rounds of **every** run"* regardless of pool
size `[ABC_RESULTS.md §1.2 | EXP ABC #2 @ REBUILD_LOG.txt:1323]`.

> **How a reviewer dismisses it:** *"You fixed the number of gradient steps and then observed that
> adding data didn't help. That is a scheduling bug in your training script, not a result about
> synthetic data. Scale the steps with the pool and re-run."*

**That dismissal is correct, and it must be conceded in the paper.** This is the single most
important reason the central claim cannot be widened: the most striking cause of the null is a
property of the loop. Nothing in this suite measures what happens when the optimisation budget is
allowed to grow.

### 2–3. Foreground exhaustion and literal object copying (D1, findings 2–3)

Bijection **4447/4447**, **0** outside, **0** unrendered; **0** of 8885 objects regenerated
`[D1_RESULTS.md §1, §3.1, §3.2 | EXP D1 @ REBUILD_LOG.txt:696]`.

> **How a reviewer dismisses it:** *"LAKE-RED composites the source object back in by design. Of
> course you got no new foregrounds — you chose a generator that cannot make them. A generator that
> synthesises the object too would not have this limit."*

The dismissal holds for the **mechanism**. What survives it is the **consequence**, and D1 states it
as the scope every null inherits: *"it is evidence about targeting under an exhausted foreground
pool, and it is silent on whether a larger or more diverse foreground set would change the outcome."*
The suite never ran the arm that would test this — the DUTS/Oracle arm was *"deliberately out of this
campaign"* `[ABC_RESULTS.md §5]`.

### 4–6. Generator determinism, shard-position dependence, seed variance (E0, D2, findings 4–6)

> **How a reviewer dismisses it:** *"These are implementation properties of one released checkpoint
> and one sharding scheme. They are provenance, not findings."*

Correct. These support the paper's reproducibility claims and nothing more. E0 scopes its own:
*"this establishes reproducibility **on this machine with this stack**, not determinism in general."*

### 7. The conditioning channel is not narrow (A1, finding 7)

> **How a reviewer dismisses it:** *"This is a reading of one generator's source code, with no
> experiment. And you withdrew a cause rather than establishing one."*

Both halves are true and the source concedes them: no `EXP A1` block exists, and A1 explicitly
declines to claim the generator is *"not the binding constraint"* or that it is *steerable*. Its
value to the paper is **as a withdrawal** — a candidate explanation removed by the authors rather
than left standing as a convenient hypothesis.

### 8–9. The null itself and its power statement (ABC, findings 8–9)

> **How a reviewer dismisses it:** *"n = 3 seeds, one budget, one α, one k, one embedder. Your own
> bar (`2σ̂ = 0.017933`) is larger than the improvement you set out to detect (0.0142). You have not
> shown there is no effect; you have shown you could not see one."*

**This dismissal is not only legitimate, it is the source's own position** — ABC insists both halves
of the sentence travel together, and lists *"That Stage C does not work"* first among what it does not
establish. T2 later improves the bar by **3.24×**, which is the suite's best answer to this objection,
but even T2 resolves only **39–45 %** of the reference gap.

### 10–13. A0 instability, pseudo-label spread, `S2C_SO`, CAMO-as-val (findings 10–13)

> **How a reviewer dismisses it:** *"Second-order properties of your own pipeline. One of them
> (A0's instability) you cannot even explain."*

Correct, and stated as such: *"**Unexplained, and stated as unexplained**"* `[ABC_RESULTS.md §3.3]`.
Their value is as **disclosure** — finding 11 in particular documents a channel through which the
arms differ beyond the manipulation under test, which a reader would otherwise have no way to know
about.

### 14. CHAMELEON was never a sanctioned endpoint (D2R, finding 14)

> **How a reviewer dismisses it:** *"This is housekeeping about your own repository."*

Correct — and D2R goes further, recording that *"it was **our own** rebuild plan that promoted it to
a secondary endpoint without checking."* It is a Tier 1 correction to the authors' own work, not a
criticism of anyone else's. The Tier 3 contamination findings (26–32) do **not** depend on it.

---

# 3. Tier 2 — the findings that travel

**These are the paper's generalizable contributions.** For each: the broadest claim it honestly
supports, and the scope limit past which it becomes overclaiming.

### ★ Finding 19 — the pixel-over-structure ordering is a property of uncertainty signals for COD, not of ES `[STRONGEST MAIN-TRACK CANDIDATE]`

`ρ(MAE) > ρ(1−Sα) > ρ(1−IoU)` passes **8 of 8** whole-image rows, 7 at 10/10 k-means seeds, across
**three signals** (ES, predictive entropy, ensemble disagreement) × **two architectures**, under a
criterion fixed before the run `[T2C_RESULTS.md §1, §2 | EXP T2C @ REBUILD_LOG.txt:2550]`.

- **Broadest honest claim:** *for camouflaged object detection, uncertainty signals of the kinds this
  pipeline can compute predict pixel-average error substantially better than they predict structural
  error — and this is a property of the signal class, not of any one signal.*
- **Scope limit:** it is **correlational**, on **one endpoint** (COD10K-test), with the magnitude
  explicitly **not** generalising. The source's own bound: *"**Not causal.** T2-C is correlational. It
  cannot upgrade into 'uncertainty guidance fails in training' for signals T2 did not train."* And
  *"**Not 'no localisation information'.** ρ(1−Sα) reaches +0.56 on SINet-v2. The claim is ordinal."*
- **Why it is the strongest candidate:** it is the only finding in the suite whose subject is
  *uncertainty-guided allocation for COD in general* rather than ES-in-CSRDA, and it was established
  by a pre-registered criterion that 6 of 8 boundary rows then failed — so the instrument demonstrably
  can fail.

### ★ Finding 15 — the target distribution has almost no cluster structure `[STRONG MAIN-TRACK CANDIDATE]`

Best silhouette **0.1600** (dinoL518), **0.1465** (dinoL224), **0.0568** (clipL224, and at the grid
edge) `[B1_RESULTS.md §C3 | EXP B1 #3 @ REBUILD_LOG.txt:922]`.

- **Broadest honest claim:** *the COD target distribution used here does not decompose into
  well-separated clusters in any of three standard embedding spaces, so a cluster-wise allocation
  budget is being spent over a partition that is itself weakly supported.*
- **Scope limit:** three embedding spaces and k-means only. *"no k is strongly supported by the
  data"*, and B1 does not claim the clusters are meaningless — only weakly separated and *"only
  moderately reproducible"*. It says nothing about non-clustering allocation schemes.
- **Why it matters:** this is **upstream** of whether the signal works. It undercuts the premise of
  cluster-wise allocation without needing the null at all, and it is reinforced independently by
  finding 16 (a preprocessing choice moves 5.4 % of memberships).

### ★ Finding 25 — real, destroyed and reversed targeting are indistinguishable on trained accuracy `[STRONG MAIN-TRACK CANDIDATE]`

**12/12 WITHIN NOISE**, largest gap **0.005007** (1.82 σ̂), at a bar **3.24×** tighter than A/B/C
`[T2_RESULTS.md §1, §1.1, §1.2 | EXP T2 #3 @ REBUILD_LOG.txt:2452]`.

- **Broadest honest claim:** *when concentration is held exactly fixed, the direction of this
  target-side uncertainty signal makes no difference to trained COD accuracy that is resolvable at
  39–45 % of the reference improvement.*
- **Scope limit, and it is the important one:** this was measured **only inside CSRDA with LAKE-RED**.
  The finding *concerns* the uncertainty signal (Tier 2), but a different training loop could in
  principle exploit the same signal differently — nothing here excludes that. It is also bounded by
  sensitivity, by the source's own pre-committed sentence: *"**A WITHIN NOISE result means 'no effect
  resolvable at this sensitivity,' never 'no effect'.**"* And by attenuation: 452–511 of 1000 images
  differ between arms, so *"The effective contrast is … roughly half the nominal budget."*
- **Why it is strong anyway:** the concentration control is **exact, not approximate** — CSHUF and
  CINV reproduce C1's committed allocation cell to 5 dp on four keys (Table 11.3), so this is a clean
  test of direction, which A/B/C structurally could not perform.

### Findings 22–24 — the ES signal adds almost nothing beyond concentration, in geometry

`+0.0073` of a *d* against its own shuffle (13/20); **−0.0649** against an arbitrary cluster (4/20);
the declared ceiling is a concentration ceiling (`+0.0077`, 10/20); effective rank ratio
**0.53–0.64** in 20/20 cells `[C1_RESULTS.md §8.2, §8.3, §8.4 | EXP C1 #4 @ REBUILD_LOG.txt:1201]`.

- **Broadest honest claim:** *the geometric separation credited to uncertainty-targeted selection is
  reproduced by selection rules that discard the uncertainty information entirely; what the targeted
  arm actually does is concentrate — narrowing to roughly half the effective dimensionality while
  covering no more of the target manifold.*
- **Scope limit:** embedding geometry only, in two DINO spaces, at k = 75/50. C1 is explicit: *"That
  targeting improves accuracy. C1 measures set separation, not model performance"*, and *"'Negligible
  in this geometry' is supported; 'zero' and 'harmful' are not."*
- **Pairing note:** this is the **prediction** that finding 25 turned into a measurement. The paper
  should present them as a pair — geometry first, trained accuracy second — because the transition
  from predicted to measured is itself a strength.

### Findings 18, 20, 21 — what the signal does and does not predict

- **18** (B1's original ordering) is **subsumed by 19** and should not be stated on its own. B1's own
  binary framing ("ES optimises the wrong objective") is **not supported** by the real allocation
  signal — the ratio lands at **0.5166 / 0.5463**, *above* the declared boundary. The paper must not
  revive it.
- **20** is the scope limit on 19 and travels with it.
- **21** is a methodological Tier 2 finding worth stating in its own right: measuring an allocation
  signal on the **endpoint** rather than where it is actually available overstates it by
  **+0.2100 / +0.2470** of ρ. Scope limit: measured on one signal, one dataset, two embedding spaces.

### Findings 16–17 — properties of the target data itself

- **16:** an arbitrary preprocessing choice reassigns **5.4 %** of cluster memberships. Broadest
  claim: *cluster membership on this data is not a robust label, which sets a floor beneath which no
  effect can be attributed to targeting.* Scope limit: two preprocessing policies, k = 20, n = 2000.
- **17:** the "target distribution" is a **mixture** (3040 COD10K + 1000 CAMO) whose components
  separate at **0.8648–0.9225**. Broadest claim: *a target pool assembled from two datasets should be
  decomposed in the same table as any headline measured against it.* Scope limit: a fact about this
  pool's construction; the general lesson is methodological.

---

# 4. Tier 3 — findings independent of the method entirely

**Each of these would stand unchanged if the method under test had worked.** That is what makes them
the paper's most durable contribution — and, for the same reason, the section most at risk of being
over-quoted.

### ★ Findings 26–28 — CHAMELEON contamination `[STRONGEST MAIN-TRACK CANDIDATE OVERALL]`

**41 of CHAMELEON's 76 images (53.9 %)** are re-encoded training data; sharpened by the author-sourced
re-audit to **`CHAMELEON ∩ COD10K-train = 40/76`**, *"a fact about two **public benchmarks**"*; and
**41 is a property of the data, not of the cutoff** — a **7.36×** gap at exactly 41, invariant across
shortlist depth `[D2_RESULTS.md §1.4, §3.1; D2R_RESULTS.md §1.2, §1.3, §1.6, §3.1]`.

**Why it stands regardless of the method:** it is a measurement over two published datasets. No
training was involved, no arm was compared, and the result does not reference CSRDA or LAKE-RED at
all. Its independence is structural, not rhetorical: the author-sourced release is **byte-identical**
to the repo copy (**76/76** at both hash levels), so the finding does not even depend on which copy
was audited.

**The honest claim, and it is narrower than the tempting one:** *"CHAMELEON is not an independent
endpoint for COD10K-trained models"* — **not** *"CHAMELEON scores are inflated"*. D2R's consequence
table says this in as many words, and finding 29 is why.

### Finding 29 — no difficulty skew, so no inflation figure

All eight percentiles in **0.448–0.559**; `split_direction_agrees_across_mask_sets` = **False**.

**Why it stands regardless:** it is a property of the images and the masks. It is also the discipline
that makes findings 26–28 credible — the authors pre-declared the reading, measured nothing, and
declined to write the quotable sentence. *"A protocol violation does not need a score advantage to be
disqualifying."*

### Finding 30 — the two CHAMELEON mask releases are different annotations

Aligned IoU **0.6932**; **27/76** identical; the choice of release moves MAE by **2.7×** on identical
predictions.

**Why it stands regardless:** it has nothing to do with contamination *or* the method. It is an
independent reason any published CHAMELEON number is not comparable across papers, and it applies to
work that never touches synthetic data.

### Finding 31–32 — NC4K is clean, and unchecked is not clean

NC4K **0/4121** on both axes, minimum nearest distance **20.610** = **3.44×** the tolerance, no gap;
and **73.7 %** of NC4K, **25/76** of CHAMELEON are unchecked.

**Why they stand regardless:** finding 31 is the **negative control** — the same detector, *imported
rather than re-implemented*, returns a clean null with a quantified margin on a benchmark where the
paper's own described protocol gave reason to expect a problem. Without it, the CHAMELEON result is
one measurement; with it, the instrument is shown to be capable of returning "clean". Finding 32 is
the honesty bound that makes every rate in this section a **lower bound**.

### Findings 33–35 — methodological findings about metrics and estimators

- **33** (AUC vacuity at **0.9928** on identity-preserving content) — see §5, it is a boundary case.
- **34** (in-sample *d* returns **+0.6991**, up to **+1.4506**, on a true null): *any* separation
  claim fitted and evaluated on the same split is suspect. Independently reproduced by A3 at
  **0.6867 / 0.6805 / 0.4854**.
- **35** (exact hashing is the wrong instrument, demonstrated twice — on the original work at 0/76,
  and on D2's own first implementation at 10/76 against the true 41/76).

**Why they stand regardless:** all three are properties of estimators and metrics, demonstrated on
data where the correct answer is known by construction.

### Finding 37 — audit practice

*"a gate that has never failed is not evidence"* — the provenance gate was verified **negatively**
before being trusted. Independent of the method; reusable as practice, not a measurement.

---

# 5. Boundary cases — flagged, not silently assigned

### Finding 33 — the AUC vacuity demonstration: Tier 3 or Tier 2?

A JPEG-30 re-encode of the **identical** target images separates them from themselves at **0.9928**
in `clipL224` — above the 0.90 vacuity trigger, above **both** genuine real-vs-real controls, and
**0.0067** short of the real-vs-LAKE-RED headline; meanwhile MMD² between them is **0.000054**
`[A3_RESULTS.md §0, §1.3, §1.4 | EXP A3 @ REBUILD_LOG.txt:2147]`.

- **Reading A — Tier 3 (assigned here).** The two sets contain *the same photographs*. The finding is
  therefore about the **metric**, not about any generator, any target distribution or any method. It
  would stand if Stage C had worked, and it applies to any paper using linear-probe AUC to argue two
  image sets differ distributionally.
- **Reading B — Tier 2.** The floors were measured on *this* target set, and A3 notes they *"sweep two
  dimensions only"* (JPEG quality and a luminance shift), so *"0.9928 is a lower bound on how high a
  floor can reach"* — arguably a property of this data rather than of the metric in general.
- **Assigned Tier 3**, because the control holds content identical by construction, which is what
  makes it a statement about the instrument. **Reading B is the reviewer's likely objection** and the
  paper should pre-empt it by reporting the sweep rather than the single 0.9928.

### Finding 36 — A3's coverage result: Tier 1 by the letter, Tier 2 by intuition

Synthetic pools cover the target manifold at **0.13–0.54**; every real set, including photographs of
an entirely different genre, covers it at **0.71–0.90**.

- **Assigned Tier 1**, because what it measures is **LAKE-RED's output**, and the definitions put
  generator properties in Tier 1. A different generator would give a different number.
- **Why it is nonetheless valuable:** it is *"the only measurement in the rebuild that speaks to
  synthetic-vs-real distance **and does not depend on power**"* `[A3_RESULTS.md §6]` — which matters
  precisely because the Tier 1 nulls (findings 8–9) do depend on power.
- **What generalises is the design, not the number:** a paired within-content coverage delta against
  the generator's **own input pool**, with the real-set ladder as the reference. A3 states the
  publishable form as strictly comparative.
- **The limit that must travel with it:** *"A3 is a distributional characterization, not a
  training-utility bound … writing it as 'the distribution is far, therefore no amount of it can
  help' would be a non-sequitur."*

### Finding 25 — Tier 2 claim, Tier 1 measurement context

T2's subject is the **uncertainty signal** (Tier 2), but every measurement was taken inside CSRDA with
LAKE-RED (Tier 1 context). Assigned **Tier 2** because the manipulation is on the signal and
concentration is held exactly fixed — but §3 states the scope limit explicitly, and the paper should
not let it drift into a claim about uncertainty-guided generation in other loops.

### Finding 2 — Tier 1 mechanism, Tier 2 consequence

The bijection is a LAKE-RED property (Tier 1). The consequence — that any null from this suite is
*"evidence about targeting under an exhausted foreground pool"* — is a **scoping obligation** that
travels to any comparable setup (Tier 2). Both halves are stated because collapsing them is how a
Tier 1 cause becomes a Tier 2 claim.

---

# 6. Generalization ceiling

**The central claim cannot reach "synthetic data does not help", and cannot even reach "uncertainty-
guided closed-loop generation does not help" in general.** The two causes with the largest apparent
force are Tier 1: the optimisation budget is pinned at **253** / **127** steps regardless of pool size,
so additional data buys no additional training in this loop, and the foreground supply is a bijection
onto 4447 existing objects that are copied pixel-for-pixel rather than synthesised. A reviewer can
set both aside as properties of CSRDA and LAKE-RED, and would be right to. The honest ceiling for the
central result is therefore: *instantiated in CSRDA with LAKE-RED, uncertainty-guided closed-loop
generation yields no accuracy gain resolvable at 39–45 % of the reference improvement* — a null
bounded by sensitivity, not a demonstration of absence.

**What reaches further is less flattering to the idea than to the implementation.** Three Tier 2
findings survive the "just your setup" objection because their subject is the data or the signal
rather than the loop: the target distribution has almost no cluster structure to allocate over (best
silhouette **0.1600**); the uncertainty signal contributes **+0.0073** of a *d* over its own shuffle
in geometry and nothing resolvable on trained accuracy in **12/12** cells; and the pixel-over-structure
ordering holds for **every** uncertainty signal this pipeline can compute (**8/8**), not just ES. Those
three support a claim about *uncertainty-guided allocation for COD* — not about synthetic data, and
not about closed-loop generation generally.

**The Tier 3 contamination result is the only part of the paper whose reach does not depend on any of
this**, and it is also the part most easily overstated. It supports *"CHAMELEON is not an independent
endpoint for COD10K-trained models"* and explicitly **not** *"CHAMELEON scores are inflated"* — D2R
measured for the inflation figure, found none (percentiles **0.448–0.559**, sign flipping with the
mask release), and declined to report one. Every rate in that section is a lower bound with a stated
unchecked share.

**The one experiment that would raise the ceiling was never run.** D1's central limit — that the null
is silent on whether *new* foregrounds would help — can only be closed by an arm with a genuinely
different foreground supply, and *"the DUTS/Oracle arm was deliberately out of this campaign"*. Until
that exists, the strongest defensible framing is a **scoped null with a tiered dissection**, not a
claim about the approach in general.

---

# 7. CONSOLIDATION_NOTES

## (a) Experiments missing a result document or a log block

| Experiment | Missing | Detail |
|---|---|---|
| **A1** | **No `EXP A1` log block** (zero) | `A1_SCOPING.md` states it: *"No experiment was written and none was run … **No number in this document enters `results/REBUILD_LOG.txt`.**"* Its one figure (`fuse` weight norm **0.907 vs 0.810**) is marked `[NOT IN COMMITTED LOG BLOCK]`. |
| **D2_NC4K** | **No `*_RESULTS.md`** | Two committed blocks; `README.md` is a setup document — *"**No measured number appears in this file.**"* All numbers sourced from the log block and `CLEAN_PROTOCOL.md`. |
| **C2** | **Both** | Declared **UNRUN** — 0 blocks, no directory, no document (`C1_RESULTS.md` §6). |
| `POOL_MECHANICS_AUDIT.md` | **No log block** | 628 lines of numbers from `pool_mechanics_probe.py`, which emitted no `EXP` block. **Not used** in either consolidation file. |

## (b) Discrepancies between a result document and its log block

Full detail in `FINAL_RESULTS.md` §16(b). Summary, worst first:

1. **ABC block #3 carries an annotation that is false and uncorrected in the committed log.** The
   `per_arm_sd_*` provenance note asserts arm B inflates pooled σ̂; ABC's own measured values refute
   it (A0 is largest by ~an order of magnitude). *"The **values** in that metric are correct; the
   **explanation attached to them is refuted by the values themselves.**"* `REVISION_TABLE.md` R17.
   **The paper must not quote that annotation.**
2. **`B1_RESULTS.md` cites a log timestamp that does not exist** — `2026-09-01T14:04+05:30`; the
   second `EXP B1` block is `13:56:55`, and no block anywhere carries `14:04`. The block is still
   identifiable by ordinal and commit (`0a1d238`). The same header's *"the log holds **two** `EXP B1`
   blocks"* is stale — there are **four**.
3. **`D2_RESULTS.md` §6 is headed "four D2 blocks"; there are five**, and the section's own table
   lists five. Heading text only; no number affected.
4. **`D1_RESULTS.md` still cites `MyTrain.py:220,297`**, which D2R measured as **`MyTrain.py:317`**.
   D2R corrected D2's copy but not D1's. Mechanism correct, line numbers wrong.
5. **`T2_RESULTS.md` cites ABC's disclaimer as §3.7**; it is **§3.6**. Cross-reference only.
6. **Two NC4K rates on two different axes** (D2's **1/4121** vs the full Target pool; D2_NC4K's
   **0/4121** vs COD10K-train and vs COD10K-test) — not a contradiction, but must not be collapsed.
7. `common.py:248-263` claims `dir_digest` matches `REBUILD_PLAN.md` §1's `agg` values; it does not
   (**d7f6de696d5c223e** vs pinned **b42e5f44b5f2b0db**). Primary data unchanged; `REVISION_TABLE.md` R16.
8. E0 (**+0.00542**, n=200) and D1 (**0.00575**, all 4447) report the mask-fraction difference
   differently — different sample sizes, and D1 flags its value as derived.
9. The CHAMELEON gap is quoted at **7.4x** (D2) and **7.36×** (D2R, `CLEAN_PROTOCOL.md`). Prefer 7.36×.

## (c) Numbers the paper will likely want that are `[NOT IN COMMITTED ARTIFACTS]`

Full list in `FINAL_RESULTS.md` §16(d). The ones most likely to be asked for in review:

- **Any p-value or confidence interval on an arm gap.** Absent **by design** — *"n = 3. No p-value,
  no bootstrap, no multiple-comparison correction"*. Verdicts are Δ against 2σ̂ with sign counts.
- **A CHAMELEON inflation figure.** Deliberately unavailable; D2R measured for it and found none.
- **Whether the published S2R-COD paper reports a CHAMELEON column.** `UNVERIFIED` — the PDF is not
  in this checkout. This is the single most quotable gap, because the paper's framing of the
  contamination section depends on it.
- **Author-sourced contamination rates for COD10K-test, NC4K and CAMO.** The re-audit is **owed**;
  until then those rates are provisional.
- **Seed variance of the ES signal and of the allocation signal.** `UNVERIFIED-DEFERRED` throughout.
- **Generator seed variance at the pool level.** Unmeasured; D2 s8 measures it at the image level on
  **one** foreground.
- **A mechanism for A0's instability.** Explicitly unexplained.
- **A boundary-localised uncertainty result.** Declared **not reachable from this design**.
- **A DUTS/Oracle (new-foregrounds) arm.** Out of scope by design — and it is the arm that would test
  D1's central limit and raise the paper's ceiling.

## (d) The Tier 2 findings strongest for main-track significance

1. **T2C finding 19 — the pixel-over-structure ordering is a property of uncertainty signals for COD,
   not of ES (8/8 rows, three signals, two architectures).** It is the only finding whose subject is
   uncertainty-guided allocation *for the problem* rather than for this implementation, and the
   pre-registered criterion demonstrably can fail — 6 of 8 boundary rows failed it.
2. **T2 finding 25 — real, destroyed and reversed targeting are indistinguishable on trained accuracy,
   12/12 WITHIN NOISE at a bar 3.24× tighter than the preceding campaign.** It converts C1's geometric
   prediction into a measurement, and the concentration control is exact (5-dp reproduction of C1's
   committed cell), so it isolates *direction* in a way A/B/C structurally could not.
3. **B1 finding 15 — the target distribution has almost no cluster structure (best silhouette
   0.1600, in all three embedding spaces).** It undercuts the premise of cluster-wise allocation
   upstream of any signal question, needs no training run, and is independently reinforced by E0's
   5.4 % membership instability.
4. **C1 findings 22–24 — the separation credited to targeting is reproduced with the signal
   destroyed (+0.0073 of a *d*, 13/20; −0.0649 against an arbitrary cluster, 4/20).** It is the
   mechanism behind 25 and supplies the concentration-vs-targeting distinction the whole signal-side
   argument rests on.

**One caution on framing.** The single most quotable result in the suite — CHAMELEON at **53.9 %** —
is **Tier 3**, not Tier 2. It is the most durable finding and the least dependent on anything else,
but it is not evidence about the method, and a main-track case built primarily on it is a
dataset-audit paper rather than a negative-results paper about uncertainty-guided generation. The
Tier 2 findings above are what carry the latter.

---

*End of `TIER_SEGREGATION.md`. Per-experiment numbers, tables and provenance are in
`rebuild/FINAL_RESULTS.md`.*

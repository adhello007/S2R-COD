# EXPERIMENTS_EXPLAINED.md — every experiment in `rebuild/`, in plain English

**What this is.** One entry per experiment, written to be read rather than decoded, so you can
decide how to frame each one in the paper. Every number is taken from that experiment's committed
result document or its `EXP` block in `results/REBUILD_LOG.txt`.

**The rule that governs all of them:** if this file and the log ever disagree, **the log wins** and
this file is wrong.

**Reading order.** Experiments are listed in dependency order — the order in which each one's
inputs became trustworthy — not in the order they were run.

**A note on the word "null".** Several experiments return *no measurable difference*. Throughout,
that means **no effect large enough for this design to resolve** — never "the effect is zero." Each
entry says what size of effect it could and could not have seen.

---

# How to read the numbers

Every score below is **Sα (S-measure)** on COD10K-test — the CSV column `Sm`. It rates how well a
predicted mask matches the true one *structurally*, runs 0–1, higher is better, and sits near 0.70
here. So `+0.0050` means five ten-thousandths of an S-measure point.

> **Notation collision to fix in the paper.** The subscript in **S<sub>α</sub>** is a fixed
> weighting parameter (0.5). §3.2 uses **α** again for the allocation temperature (1.0). Two
> different α's, one symbol.

**The four quantities that recur:**

| Term | What it is | Worked example (ABC, SINet) |
|---|---|---|
| **Δ (delta)** | one arm's 3-seed mean minus another's | C10 0.718481 − B 0.713447 = **+0.005034** |
| **σ̂ (sigma-hat)** | typical seed-to-seed wobble of a single run, pooled across arms | **0.008966** |
| **the bar** | 2σ̂ — a gap must beat this *and* have all 3 seeds agree on sign | **0.017933** |
| **sensitivity** | the smallest true effect the design could have detected = the bar | effects below 0.0179 are invisible |

**How σ̂ is computed.** Sum each arm's squared deviations from *its own* mean, add them, divide by
the degrees of freedom (4 arms × 2 = 8), square-root.

**The reference effect, 0.0142**, is not from this campaign — it is the improvement this repository
reproduced for the published method (MT 0.7030 → 0.7172). It is the target the design had to be
able to see. **126%** is just `0.017933 ÷ 0.0142`: the yardstick was 26% larger than the thing being
measured.

**Why the bar was so wide — the thread through most of these numbers.** Arm A0's three runs are
0.715 / 0.682 / 0.706, roughly ten times noisier than any other arm, and unexplained. **A0 alone
contributes 92.7% of the pooled variance**, yet A0 appears in none of the decisive comparisons:

| Noise pooled over | σ̂ | bar | Δ(C10−B) against it |
|---|---|---|---|
| A0, A2, B, C10 (ABC, n = 3) | 0.008966 | 0.017933 | 0.28× — far inside |
| B, C10, CSHUF, CINV (T2, n = 3) | 0.002767 | 0.005533 | **0.91×** — just inside |
| B and C10 only (post-hoc) | — | ~0.0051 | 95% CI [−0.0035, +0.0136] |
| **B, C10, CSHUF, CINV (SE, n = 8)** | **0.003431** | **0.006862** | **0.34×** — comfortably inside |

So **3.24×** = 0.008966 ÷ 0.002767, the factor by which dropping A0 tightens the bar, and **0.91×**
= 0.005034 ÷ 0.005533, the decisive gap as a fraction of that tighter bar. The headline verdict is
unchanged throughout; what changes is how coarse the instrument is said to be.

**Careful reading the last row.** The first three rows all measure *the same* Δ = 0.005034 against
different bars. SE's row does not: at eight seeds **the gap itself is different**, +0.002352, and
0.34× is that new gap against SE's own bar. SE is a separate campaign, so it has its own Δ, its own
σ̂ and its own verdicts. See §17.

**Degrees of freedom, and why they decide how much to trust a bar.** σ̂ is an *estimate* of the
wobble, and estimates have their own error. The relevant count is `df` = arms × (seeds − 1):

| campaign | seeds per arm | df | what that buys |
|---|---|---|---|
| ABC, T2 | 3 | **8** | a noisy estimate — it lands low about as often as high |
| **SE** | **8** | **28** | 3.5× the evidence about how noisy training actually is |

This is the single most important thing to understand about SE, because it explains an outcome that
looks backwards at first glance: **more runs made the bar wider, not narrower.** A bar computed from
three runs per arm can easily come out too small — three runs that happen to land close together look
like a stable method. With eight, you see more of the real spread. SE did not buy a *smaller* bar; it
bought a *trustworthy* one, and in doing so showed that the three-seed bars were optimistic.

**Arm names.** `A` = baselines (A0 unpadded, A2 padded with real photographs), `B` = random
selection, `C` = chosen by uncertainty. The digits are the temperature: **C10 is α = 1.0**, and the
never-run secondary `C05` would have been α = 0.5. `CSHUF`/`CINV` scramble and reverse the signal;
`CORACLE` replaces it with truth; the `FX` suffix means the same arm under the unpinned schedule.

---

# 1. E0 — Rebuild every input from scratch and hash it

### The essence, and why we did it

Before measuring anything, we had to know that the files we were measuring were the files we thought
they were. The old package had accumulated inputs whose origin nobody could now state with
certainty. E0 regenerates every input from primary data, hashes all of it, and produces a manifest
that every later experiment checks against instead of trusting a filename. It also re-runs the image
generator to see whether it produces the same pictures twice. This is plumbing, but every result in
the project rests on it.

### How we did it

We listed every directory the pipeline reads and hashed all **48,365** files across **15** input
directories, recording the count and digest of each. We then re-ran the LAKE-RED generator on the
full foreground set at a fixed seed and compared its output, file by file, against the copy already
on disk. Separately we tested whether the clustering the method depends on is stable: we changed one
arbitrary image-preprocessing choice and re-clustered, then measured how many images changed
cluster. We declared sixteen pass/fail thresholds in advance and ran them mechanically. No model was
trained. The manifest it produced, `e0_manifest.sha256`, is the file every later experiment verifies
its inputs against. Everything E0 touches is regenerable, so nothing had to be rescued from the old
package.

### What we found

Every declared input resolved and re-hashed clean — **0** count mismatches across 15 directories,
and all **16** thresholds passed. The generator reproduced **4447 of 4447** images and masks
byte-for-byte at seed 0, which establishes that our pipeline is deterministic on this machine with
this software stack. But a render turned out **not** to be a function of the image and mask alone:
it also depends on the image's *position within the processing batch*, so changing how the work is
split across shards changes the pictures even at a fixed seed. And the clustering is not a firm
label — an arbitrary preprocessing choice **moved 5.4% of images into different clusters** (94.6%
agreement, mean cosine similarity 0.9308).

### Why it matters

That 5.4% figure became a floor used throughout the project: any effect smaller than it cannot
honestly be attributed to which cluster an image landed in. And the shard-position finding is a
reusable warning for anyone batching a diffusion pipeline and assuming a seed is enough.

---

# 2. D1 — Is the generator actually inventing anything?

### The essence, and why we did it

The whole premise of generating synthetic training data is that you get *new* images. LAKE-RED works
by taking a real cut-out object and painting a fresh background behind it, so we wanted to know how
much of the output is genuinely new and how much is the original photograph carried through. If the
objects are simply copied, then the supply of distinct foregrounds is fixed no matter how many
images you generate, and every conclusion about "more synthetic data" inherits that ceiling. This
sets the scope of every later null.

### How we did it

We first checked how many genuinely distinct images each pool contains, since duplicates would
inflate any count. We then traced every rendered image back to the raw foreground it came from, and
asked two questions: does every render trace to a real source, and does every source get rendered?
For the object-copying test we compared each rendered image against its source photograph *inside
the object mask* and *outside it*, separately, measuring the average brightness difference in grey
levels (0–255). We eroded each mask slightly first so that edge blending would not contaminate the
interior measurement. We ran this over all objects with a valid interior — **8885** of them — across
both the authors' pool and our own regeneration. Ten thresholds were declared in advance. No model
was trained.

### What we found

The pools are nearly duplicate-free: the authors' pool is **4447/4447** unique, the raw photographs
**4443/4447**, our local renders **4445/4447**. The render set is an exact **bijection** onto the
4447 raw foregrounds — every render traces to a source, **0** fall outside it, and **0** sources go
unrendered. The copying result is stark: inside the object the average difference from the source
photograph is **5.603** and **9.633** grey levels, while outside it — the part the generator
actually paints — the difference is **70.802** and **70.555**. Of the 8885 objects checked, **0**
showed any sign of having been regenerated. All ten thresholds passed, and of three older claims
re-tested, two matched and one did not.

### Why it matters

The generator paints backgrounds and copies objects, so the foreground supply is exhausted at 4447
and no amount of generation adds a new animal. Every null in this project must therefore carry the
scope line *"measured under an exhausted foreground pool"* — which is a real limit, but also a
precise one.

---

# 3. D2 — Is the CHAMELEON benchmark actually training data?

### The essence, and why we did it

CHAMELEON is one of four benchmarks that camouflage papers routinely report scores on. While
building the pipeline we noticed images that looked familiar, and the standard way to check for
overlap — hashing the files and looking for identical bytes — reported nothing at all. We suspected
the copies had been re-saved in a different image format, which changes every byte while leaving
every pixel effectively unchanged. This finding is completely independent of whether our own method
worked, and it turned out to be one of the project's most portable contributions.

### How we did it

We grouped every image by its exact pixel dimensions, because a re-saved copy keeps its dimensions
and only same-size images can be compared pixel to pixel. Within each size group we compared every
pair using a small 32×32 grey thumbnail to build a shortlist, deliberately **not** normalising
contrast, because normalising destroys the very scale that distinguishes a copy from a similar
photograph. Every shortlisted pair was then verified at full resolution by average absolute pixel
difference. For each confirmed pair we extracted the JPEG compression tables two independent ways,
since different tables are positive evidence that a file was re-encoded rather than copied. We swept
the matching tolerance rather than picking one, to see whether the answer depended on our choice.
Any image with no same-size partner was reported as **unchecked**, not clean. No model was trained.

### What we found

**41 of CHAMELEON's 76 images (53.9%) are the same photographs as images in the COD10K-train and
CAMO training pool**, re-saved in a different format — 40 in COD10K-train, one in CAMO. Exact
hashing returns **0** collisions and is perfectly correct at what it measures; it simply answers a
different question. The count is a property of the data and not of our tolerance: sweeping the
threshold gives 11, 26, 37, 40, **41** matches and then stops rising, and the sorted
nearest-neighbour distances independently put 41 images below 5.51 with the next at 40.58 — a
**7.36× jump**. We also caught ourselves making the same mistake we were documenting: our first
implementation reported only 10/76 because it normalised contrast. **25 of 76** images had no
same-size partner and were left unchecked.

### Why it matters

A model trained on COD10K-train has already seen more than half of CHAMELEON before being evaluated
on it, and the standard check will tell you the benchmark is clean. This is a fact about two public
datasets that every paper reporting a CHAMELEON column inherits.

---

# 4. D2_NC4K — Does the detector find contamination everywhere?

### The essence, and why we did it

An audit that reports contamination wherever you point it is worthless, because you cannot tell a
real finding from an instrument that always says yes. We needed a case where the honest answer is
"clean" and check that our detector returns it. NC4K is a separate camouflage benchmark assembled
from Flickr, with no reason to overlap COD10K's test split. This is the negative control that makes
the CHAMELEON number believable.

### How we did it

We imported the *identical* detector used on CHAMELEON rather than re-implementing it, so that no
difference in code could explain a difference in outcome. We ran it on NC4K against the COD10K test
split, and separately against the full training pool, because those are two different questions and
collapsing them would be misleading. We swept the same tolerance range as before. We recorded not
just the match count but the minimum nearest-neighbour distance, since a clean result should show
matches sitting far away rather than just below the threshold. We also recorded how many NC4K images
had no same-size partner and so could not be checked at all. Every declared threshold was fixed
before the run and no model was loaded.

### What we found

NC4K against COD10K-test is **clean on every axis**: 0 byte-identical, 0 pixel-identical, and
**0 of 4121** re-encoded at every tolerance swept. The closest any NC4K image came to a COD10K test
image was a distance of **20.610**, which is **3.44×** the tolerance used to confirm a CHAMELEON
match — so the clean result is not a near miss, it is a comfortable one. There was no discontinuity
anywhere in the sorted distances, unlike CHAMELEON's sharp jump at 41. Only 1082 of NC4K's images
were actually checkable against the test split. **73.7%** of NC4K had no same-size candidate and is
therefore unchecked rather than proven clean.

### Why it matters

The detector does not find contamination everywhere, so when it finds 41 in CHAMELEON that number
means something. It also shows honestly that every rate this method produces is a lower bound,
because the unchecked share is large.

---

# 5. D2_reaudit — Check the finding against the authors' own copy

### The essence, and why we did it

Our CHAMELEON finding was measured against a copy of the dataset that had been sitting on our disk,
which is a weak foundation for a claim about a public benchmark. If our copy had been altered at
some point, the whole result would evaporate. So we obtained the dataset from its original source
and re-ran everything. We also used the opportunity to test whether the leaked images were unusually
easy, which would let us say how much the contamination inflates published scores.

### How we did it

We compared the author-sourced release against our local copy file by file, then re-ran the full
audit on the author-sourced version. We re-tested eight measurements from the original audit to see
which reproduced and which did not, treating any mismatch as a correction to our own prior work
rather than to the data. To test for score inflation we compared the leaked and clean subsets on
four model-free difficulty proxies and four inference metrics, asking where the leaked subset sits
as a percentile within the clean set — 0.5 means indistinguishable. We had declared in advance that
a percentile inside [0.25, 0.75] means no detectable skew. We also compared the two different
CHAMELEON ground-truth mask releases that circulate. Finally we packaged the detector, the confirmed
pair list and a clean-usage protocol as a standalone release.

### What we found

The author-sourced copy is **byte-identical to ours at 76/76**, so the finding does not depend on
our local files. Eight of eight measurements reproduced; three mismatches corrected our own earlier
work rather than the data. Against the public COD10K-train split alone the overlap is **40 of 76**.
We looked for score inflation and did not find it: all eight difficulty percentiles land between
**0.448 and 0.559**, and the sign of the clean-minus-leaked difference actually **flips** depending
on which mask release you use. Separately, the two circulating CHAMELEON mask releases turn out to
be **different annotations** — mean IoU **0.6932** after fixing a polarity difference, only **27 of
76** identical — and on identical predictions the choice of release alone moves MAE by **2.7×**.

### Why it matters

Because we measured for inflation and found none, the defensible claim is **non-independence**, not
"the scores are inflated" — a protocol violation does not need a score advantage to disqualify a
benchmark. The mask-release discovery is a second, entirely separate reason published CHAMELEON
numbers cannot be compared across papers.

---

# 6. B1 — Is the uncertainty signal measuring what we think it measures?

### The essence, and why we did it

The method sends generated images toward the clusters where the model is least confident, which
assumes the confidence score actually predicts where the model is wrong. That assumption had never
been tested. We also needed to know whether the target images fall into meaningful clusters at all,
because the entire allocation is spent cluster by cluster. This experiment tests the two foundations
the method stands on before any training run is spent on it.

### How we did it

We computed the student–teacher disagreement score for every image and correlated it against three
different kinds of error: average pixel error (MAE), structural error (1 − S-measure, which is what
the paper is judged on), and localisation error (1 − IoU). We did this per cluster and also per
image, so the finding would not depend on any clustering choice. We repeated the clustering across
ten different random seeds and three different image-embedding spaces to check the answer was not an
artifact of one setup. We swept the number of clusters and recorded the silhouette score, a standard
measure of how cleanly data separates into groups where values near zero mean the groups are not
really there. Critically, we measured the signal twice: once on the labelled test set where error is
known, and once on the unlabelled target pool where the method actually has to operate. Seven
thresholds were declared in advance. No model was trained.

### What we found

The signal predicts pixel error about **twice as strongly** as structural error: per-cluster
correlations of **+0.8553** for MAE against **+0.4276** for 1 − S-measure and **+0.2983** for
1 − IoU. Since S-measure is the metric the paper is judged on, the signal is a much better proxy for
something we are not optimising than for something we are. The target data barely clusters at all:
the best silhouette score is **0.1600**, with **0.1465** and **0.0568** in the other two embedding
spaces — all far below any conventional threshold. And the signal is **materially weaker where it is
actually used**: measured on the unlabelled target pool rather than the labelled test set, its
correlation with pixel error drops by **+0.2100** and **+0.2470**. Six of seven thresholds passed,
and the one that failed is the most informative result in the experiment.

### Why it matters

A method that allocates a budget over clusters is spending it over a partition the data barely
supports, using a signal that points at the wrong kind of error and is weaker in deployment than in
validation. This is the first concrete reason to expect the approach not to work.

---

# 7. C1 — Does targeting produce a different training set, and if so, why?

### The essence, and why we did it

Before spending GPU time on training, we checked whether targeted selection even *picks* a different
set of images from random selection — if it does not, nothing downstream can differ. An earlier
claim put that difference at a very small effect size, and we wanted to verify it. But we then asked
a harder question that turned out to be the pivot of the whole project: *if* the sets differ, is it
because of the uncertainty information, or merely because the budget is spread unevenly? This
distinction is the paper's central thesis.

### How we did it

We trained a simple probe to tell a targeted set apart from a random set of the same size, scoring
it on held-out data so the number could not be inflated by memorisation. We measured the separation
in Cohen's *d*, which expresses the gap in standard deviations. Then came the attribution audit: we
built rules that keep the allocation's *shape* — the same lopsided spread of the budget across
clusters — while destroying the information inside it. One shuffled the uncertainty scores between
clusters; another simply aimed at an arbitrary cluster; another drew two random sets with no
unevenness at all. We compared these across twenty different cells of budget and configuration. We
also measured whether targeting *covers more* of the data or merely sits *closer* to its centre,
using effective rank and coverage. Separately we tested what happens when effect size is estimated
on the same data used to fit the probe.

### What we found

The old claim of a tiny effect is **refuted**: targeted and random sets separate at a held-out
Cohen's *d* of roughly **1.00 to 1.23**, an order of magnitude larger. But the audit dismantles the
obvious reading of that. Shuffling the uncertainty scores across clusters still gives **+0.9139 to
+1.1403** — essentially the same separation — and aiming at an arbitrary cluster gives as much again.
Paired across twenty cells, the real signal adds just **+0.0073** of a *d* over its own shuffle
(winning 13 of 20, near a coin flip) and is **negative at −0.0649** against an arbitrary cluster
(winning only 4 of 20). What targeting actually buys is **narrowness**, not reach: effective rank
ratio **0.53–0.64** in 20 of 20 cells with coverage essentially unchanged. We also showed that
estimating the effect on the same data used to fit it manufactures **+0.6991** out of a known null.

### Why it matters

The separation everyone would read as "the targeting worked" is produced by concentration alone, and
the control that distinguishes them is a same-shape shuffle rather than a random baseline. This is
the paper's title and its most transferable methodological point.

---

# 8. A1 — Can the generator even be steered? (source reading, no experiment)

### The essence, and why we did it

A convenient explanation for the method's failure was available: perhaps information about the
desired foreground reaches the generator only through a narrow bottleneck, so it physically cannot
act on a detailed instruction. That would have been a tidy story. We went to check it in the
released generator's source code before building an experiment around it. What we found refuted our
own hypothesis, and we withdrew it rather than leaving it standing.

### How we did it

This is a **code trace, not a measurement** — it has no `EXP` block, runs no model, and logs no
metric, and it says so plainly. We read the released LAKE-RED architecture and traced every path by
which information about the foreground reaches the region being repainted. For each path we recorded
where it enters, what it carries and how wide it is. We compared the weight norms of the competing
routes to see which dominates. We wrote down in advance which claims a source reading could and
could not license. Because no experiment was run, the strongest available outcome was the removal of
a hypothesis rather than the establishment of one. We then updated the paper to record the
withdrawal.

### What we found

The conditioning channel is **not narrow**. Four separate routes carry foreground information into
the regenerated region, the low-dimensional summary we had suspected is only one of them, and the
dominant route **bypasses that summary entirely** — the competing weight norms are **0.907 against
0.810**. So the tidy explanation is false as stated. But we deliberately did **not** convert this
into the opposite claim. Showing that a channel is wide does not show that its capacity is used, and
the generator still offers no interface through which a specific deficiency could be named. We
therefore declined both the claim that the generator is "not the binding constraint" and the claim
that it is steerable.

### Why it matters

Its value to the paper is as a **withdrawal** — a candidate explanation removed by us rather than
left standing because it was convenient. A reviewer can fairly say this is a reading of one
codebase with no experiment behind it, and that is exactly how the paper presents it.

---

# 9. A3 — How far is the synthetic data from the real data?

### The essence, and why we did it

If the generated images sit in a very different region from the real ones the model will face, then
the choice of *which* synthetic images to add matters less than the fact that they are synthetic at
all. We wanted to characterise that distance properly. We also wanted to check a measurement
convention the field relies on — training a probe to tell real from synthetic and reporting how well
it does — because we suspected that number is nearly meaningless. This ended up producing both a
finding about our pipeline and a caution about the metric itself.

### How we did it

We embedded real and synthetic images in three different feature spaces and measured **coverage**:
what fraction of the real target distribution the synthetic set actually reaches. Crucially we built
comparison sets that isolate the effect of *being synthetic* from the effect of *being different
content*: the generator's own input photographs (real, but a different genre) and a different real
camouflage dataset. We measured effective rank and precision alongside recall, because a set can be
narrow without being displaced, and those are different failures. For the probe caution we took the
*identical* images, re-saved them at JPEG quality 30, and asked the probe to separate the originals
from the re-saves — content held perfectly constant. We swept generation quality and ran real-versus-real
controls. Fifteen thresholds were declared in advance. No model was trained; this is frozen feature
extraction plus probes on frozen features.

### What we found

The synthetic pools reach only **0.1277 to 0.5421** of the real target distribution, while the
generator's own input photographs — real images of an entirely different genre — reach **0.7097 to
0.7473**, and a different real camouflage dataset reaches **0.7921 to 0.8995**. In other words, real
photographs of the *wrong subject* cover the target better than synthetic images generated *from
those very photographs*, a paired loss of **−23.6% to −82.9%**. The failure is **narrowing, not
displacement**: effective rank falls from 243.3 to 193.2 while precision actually *rises* from
0.6490 to 0.6886. And the probe caution landed hard — a JPEG re-encode of *identical* images
separates at **0.9928 AUC**, higher than both real-versus-real controls and only 0.0067 below the
headline real-versus-synthetic number. We also confirmed the target pool is a two-dataset mixture,
separating from itself at up to **0.9225**.

### Why it matters

The generated distribution is narrower than its own input, which bounds how much any allocation
policy over it could achieve. And a real-versus-synthetic AUC near 1.0 is near-vacuous as evidence —
a lossy re-save of the same pictures achieves it.

---

# 10. ABC — The main training campaign

### The essence, and why we did it

This is the experiment the paper is named for: does aiming the generation budget by uncertainty
actually produce a better model than spending it at random? Everything before this point measured
properties of signals, data and generators; this measures trained accuracy. It was pre-registered in
full — arms, endpoints, seeds, noise estimate, decision rule and interpretations — before a single
run launched. It is the campaign whose verdict the paper reports.

### How we did it

We defined four training conditions sharing one base pool of 4447 labelled pairs and differing only
in what is added: **A0** adds nothing; **A2** adds 1000 of the authors' original photographs;
**B** adds 1000 randomly chosen generated images, redrawn per seed; **C10** adds the 1000 chosen by
the uncertainty allocation. A2, B and C10 all hold 5447 pairs, so the comparison that matters — C10
against B — holds pool size fixed and varies only *which* images. We ran two architectures (SINet
and SINet-v2) at three seeds each, two training rounds per run, giving **24 runs**. The decision rule
was fixed in advance: a gap counts only if it exceeds twice the seed-to-seed spread *and* all three
seeds agree on its sign, with no p-values at n = 3. Six pre-flight gates had to pass before any run
launched, including a byte-level check that every pool matched E0's manifest. We measured the actual
optimisation budget per run rather than assuming it.

### What we found

**The decisive gap is WITHIN NOISE on both architectures and both endpoints.** On SINet,
Δ(C10 − B) = **+0.0050** with all three seeds agreeing; on SINet-v2 it is **−0.0004** with the seeds
disagreeing — the two architectures do not even agree on the sign. The campaign resolved coarsely:
the pooled seed spread put the bar at **0.0179** (SINet), which is **126%** of the 0.0142 improvement
this approach reports, so this campaign alone could not have detected that improvement. We also
measured that the optimisation budget is **pinned at 253 steps (SINet) and 127 (SINet-v2) in both
rounds of every run** regardless of pool size, so adding 1000 images bought no extra training. The
unpadded arm A0 turned out to be the least stable (seed spread 0.017266) and we could not explain
why. The pseudo-labelling step between rounds varied by **22.2%** across runs, a second uncontrolled
channel we disclose rather than hide.

### Why it matters

This is the headline null, and it comes with its own honest limit attached: it says no benefit was
resolvable at this sensitivity, not that no benefit exists. Its reach comes entirely from the
experiments that explain *why*.

---

# 11. T2 — Destroy the signal but keep the shape

### The essence, and why we did it

Comparing C10 against B changes two things at once: the budget becomes lopsided *and* it is aimed by
uncertainty. So that comparison can never tell you which one mattered. C1 had shown that
concentration alone explains the geometric separation; T2 asks whether the same is true of trained
accuracy. It holds the lopsidedness *exactly* fixed and varies only where the budget points.

### How we did it

We built two new arms by permuting the uncertainty scores across clusters. **CSHUF** shuffles them
randomly, so the budget is spread just as unevenly but points at the wrong clusters; **CINV**
reverses their rank exactly, so the budget flows to the clusters the model is *most* confident about.
Because both are permutations, the shape of the allocation is preserved to five decimal places on
all four recorded shape statistics — we assert this rather than assume it, and a failure would halt
the run. The shuffle was chosen by a rule declared before the draw: the first candidate with no fixed
points and near-zero rank correlation, giving **−0.03351** against CINV's exact **−1.0**. Before
spending any GPU time we checked the arms actually select different images, gating at a Jaccard
bound; between **452 and 511** of each pair's 1000 images differ. We trained 12 new runs and
re-scored the existing B and C10 predictions rather than re-training them.

### What we found

**All twelve cells are WITHIN NOISE**, and this campaign's bar is **3.24× tighter** than the main
campaign's — a seed spread of 0.0028 against 0.0090, putting the bar at 0.0055. Under that tighter
bar the main campaign's decisive gap sits at **0.91× threshold**: still within noise, but only just.
The largest gap anywhere in T2 is 0.0050. A directional pattern exists and we report it without
claiming it: C10 is best in none of the four cells, the **anti-targeted CINV has the highest mean in
three of four**, and the architectures disagree on the sign of two of three gaps — which is the
signature of noise rather than of an effect. None of it reaches the bar.

### Why it matters

With concentration held exactly fixed, the direction of the uncertainty signal changes nothing we
can measure. The control that discriminates is the same-shape shuffle, not the random baseline —
and that is the lesson that transfers to any uncertainty-guided acquisition method.

---

# 12. T2C — Is the pixel-over-structure finding specific to our signal?

### The essence, and why we did it

B1 found that the uncertainty score predicts pixel error far better than structural error. That is
an interesting finding, but only if it is a property of uncertainty signals in general rather than a
quirk of the particular score we happened to use. If it is general, it is a caution for the whole
field; if it is specific to us, it is a footnote about our implementation. This experiment decides
which.

### How we did it

We computed two additional uncertainty signals that have nothing to do with our student–teacher
score: **predictive entropy**, which measures how unsure a single model's output is, and **ensemble
disagreement**, which measures how much separately trained models differ. We crossed these with both
architectures and re-ran B1's exact correlation test — using B1's own committed test code rather
than a reimplementation, so the comparison is genuinely like for like. The pass criterion was fixed
before the run: the ordering ρ(MAE) > ρ(1−Sα) > ρ(1−IoU) must hold. We repeated it across ten
k-means seeds to check stability. We also ran the same test aggregated over a boundary band rather
than the whole image, since that is the region the signal is nominally about. This required
**64,640** inference forward passes but trained nothing and fitted no new partition.

### What we found

**The ordering generalises: it passes on 8 of 8 whole-image rows**, seven of them at all ten
clustering seeds, across three signals and two architectures. So B1's finding is not about our score
— it is a property of every uncertainty signal this pipeline can compute. **But the magnitude does
not generalise**, and we say so plainly: on SINet-v2, ρ(1−Sα) reaches **+0.54 to +0.56**, which is
substantial rather than negligible, so "uncertainty carries no localisation information" is false as
stated. The surviving claim is strictly **ordinal and comparative**. Aggregated over a boundary band
the criterion largely fails — only **2 of 8** rows pass and four go negative, an inversion our
declared interpretation space had not anticipated.

### Why it matters

The finding becomes a statement about uncertainty-guided allocation for this task in general, which
is the broadest claim in the suite. The failed boundary rows are reported as a failure, which also
demonstrates that the criterion is capable of failing.

---

# 13. AC — Is the ordering just an artifact of object size?

### The essence, and why we did it

We came up with an objection to our own finding. A whole-image average is essentially *density
multiplied by area*, so if both MAE and the uncertainty signals scale with how big the object is,
while S-measure carries a size term that does not, the ordering could be an arithmetic artifact
rather than anything about uncertainty. This is the kind of confound that quietly invalidates a
result. We tested it rather than arguing about it.

### How we did it

We partialled out area — that is, we recomputed every correlation with object size held constant, so
any part of the relationship explained by size alone is removed. We used two different area
covariates because there are two defensible choices: the object's area on the endpoint side, and the
area of the uncertain region on the target side. We declared the pass floor before running: the
ordering must survive on at least 6 of 8 rows. We reused T2C's committed signal tables rather than
recomputing them, so only the statistical treatment changed. We recorded the *direction* each
correlation moved, not just whether it still passed, because direction is the more informative
quantity here. An addendum records that one reference tolerance in the plan was unsatisfiable against
a four-decimal file and was replaced by exact agreement at the recorded precision — no decision
threshold was altered.

### What we found

The confound is refuted, and the evidence is the **direction** of the shift rather than the pass
count. Partialling out object area **raises** ρ(1−Sα) in **all eight rows** — the exact opposite of
what the confound predicts, meaning area was *suppressing* the structural correlation rather than
inflating the pixel one. The ordering then survives on **7 of 8** rows for one covariate and **6 of
8** for the other, against the declared floor of 6/8. We flag that this is weak: 6 of 8 has a
probability of about **0.145** under a fair coin, so the second covariate clears a near-chance bar by
exactly zero margin. Area accounts for part of the gap but not its sign.

### Why it matters

The pixel-over-structure ordering is not an artifact of object size, which was the most plausible
mechanical explanation for it. We report the zero-margin pass rather than presenting 6/8 as
comfortable.

---

# 14. PC — Can this measurement detect anything at all?

### The essence, and why we did it

By this point every trained comparison had returned "no difference," which leaves a dangerous
ambiguity: either there really is no effect, or our measurement is simply too blunt to see one.
Nothing committed distinguished those two readings. A positive control resolves it by measuring
something we are confident *is* different and checking that the apparatus notices. Without this,
every null in the project is uninterpretable.

### How we did it

We trained a mean-teacher baseline — a method we expected to be clearly worse than the full approach
— using the same architecture, the same three seeds, the same scorer, the same endpoint and the same
decision rule as every other campaign. The trainer forces this method to a single round by
construction, which we recorded rather than chose. It uses the unpadded base pool and receives no
generated images. The committed C10 runs served as the reference and were re-used as already scored,
never re-trained. Before any PC number was computed, a gate required the scorer to reproduce a
previously committed score exactly. We stated the expected outcome in advance and committed to
publishing whichever way it fell, noting explicitly that a negative result would mean our nulls are
bounded by the instrument rather than the method.

### What we found

**The instrument is not blind.** The gap between the full method and the mean-teacher baseline is
**+0.0197**, against a bar of **0.005954** — **3.3× the bar**, with all three seeds agreeing, verdict
**DETECTED**, and the secondary endpoint agreeing. But PC's own results document is emphatic about
what this does *not* establish, and that limit is load-bearing. The nulls in this paper concern
effects near **0.005**; this demonstrates detection at **0.0197**, roughly four times larger. In fact
the arithmetic runs against us: **PC's own bar (0.005954) is larger than the decisive gap
(0.005034)**, so an effect that size would not have cleared this pooling either. It is also not an
ablation — method, round count and pool size all differ at once — and it covers only one
architecture.

### Why it matters

A positive control at 0.020 licenses *the instrument works*; it does not license *it would have seen
the effect we are nulling*. Reporting both halves is what keeps the null honest, and it is why the
seed-expansion campaign was still needed.

---

# 15. OR — What if the score were perfect?

### The essence, and why we did it

The loop has two halves: a score that decides where to aim, and a generator that makes the pictures.
When it fails, either half could be responsible, and nothing so far separates them. The obvious
reviewer objection — *"you simply picked a bad uncertainty estimator"* — was untested. OR settles it
by cheating: it throws the score away and substitutes the true answer. If even perfect information
buys nothing, the score was never the bottleneck.

### How we did it

We built an arm that takes C10's committed allocation **shape** and re-assigns it across clusters by
the rank of each cluster's **true error on the test set**, read from a committed table. Because this
is a permutation, the shape is preserved exactly and only the targeting changes — the same device T2
uses, with ground truth supplying the ranking instead of a shuffle. This deliberately uses test
labels to choose training data, which a pre-flight gate exists to forbid for any real method, so the
pre-registration declares up front that this is a diagnostic upper bound and never a method, and
that passing the gate on a technicality is disclosed rather than claimed as cleanliness. We trained
6 runs (2 architectures × 3 seeds) and re-scored the committed B and C10 predictions rather than
re-training them, requiring them to reproduce exactly at 6 decimal places first. Everything else —
budget, temperature, clustering, render pool, seeds — is identical to C10.

### What we found

**All eight cells are WITHIN NOISE**, and not one is even directionally stable — sign consistency is
**2/3 everywhere**. Against random allocation the perfect score gains **+0.0008** on the primary
architecture and endpoint; against the real uncertainty score it *loses* **−0.0042**. On SINet-v2 it
gains **+0.0023** and **+0.0027**, still far inside the bar. Building the arm also produced a
striking number in its own right: the uncertainty score and the true per-cluster error agree at a
rank correlation of only **+0.237**, so the score is a weak proxy for where the model actually errs
— and replacing it with something four times better still changes nothing measurable. An addendum
discloses that the oracle is derived from one architecture's errors and applied to both; the two
architectures' per-cluster errors agree at **+0.9211**, so the second architecture gets a near-oracle
rather than a perfect one.

### Why it matters

The acquisition score is **not** the binding constraint: no score of any quality helps in this
pipeline, so the limit lies downstream in the generator, the exhausted foreground supply or the
training schedule. This converts "our score didn't help" into the much stronger "no score could
have."

---

# 16. FX — What if the added data were actually trained on?

### The essence, and why we did it

The single strongest objection to the paper is that we fixed the number of gradient steps and then
observed that adding data did not help — which would make the null a scheduling bug rather than a
result. The trainer pairs a labelled batch with an unlabelled batch at every step and stops when
either runs out; since the unlabelled pool is smaller, it ends every epoch early. The consequence is
that adding 1000 images **displaces** existing ones rather than adding to them. FX removes that pin
and re-runs the comparison.

### How we did it

We changed the trainer so the labelled pool decides when an epoch ends, and the unlabelled pool
simply restarts whenever it is exhausted. This is opt-in behind a flag whose default is byte-identical
to the committed code path. It does not obtain more real images — it re-uses the 4040 we have, so
each real image is now seen about **1.35 times per epoch** instead of once, which we disclose as one
of four things the change bundles together. We built three arms mirroring A0, B and C10 with
byte-identical pools, differing only in the flag, and trained 18 runs at the same three seeds. A gate
declared that any run whose step count stayed at the old pinned value was a halt rather than a
result, since that would mean the change never took effect. We deliberately did not rescale the
learning-rate schedule, because doing so would re-impose a fixed budget and defeat the control.

### What we found

The manipulation worked exactly as specified: steps per epoch rose from the pinned **253 to 341**
(SINet) and **127 to 171** (SINet-v2), so every labelled image is now seen once per epoch instead of
0.74 times. **The decisive gap is WITHIN NOISE in all four cells** — at 0.12×, 0.21×, 0.07× and 0.03×
of its bar. More tellingly, the gap **shrank**: on SINet it fell from **+0.0050** under the old
schedule to **+0.0014** under the new one. Growing the budget by 35% made every arm slightly
*worse*, with **11 of 12** cross-schedule comparisons negative, most likely because the
learning-rate schedule decays per epoch and was deliberately left unrescaled. Two comparisons
involving the unpadded arm came out **INCONCLUSIVE** — above the bar at +0.0120 and +0.0134 but with
seeds disagreeing — which hints that *padding the pool* may help, a claim about how many images
rather than which ones. This cost **57.7 GPU-hours** across 18 runs.

### Why it matters

The null survives removal of the dilution confound, and the targeting gap moves toward zero rather
than away. The paper can now delete its sentence about the optimisation budget being the largest
open question, because that question has been measured rather than conceded.

---

# 17. SE — Does the null survive more seeds? *(complete, 2026-09-22)*

### The essence, and why we did it

Every verdict rests on three training runs per condition, and three is few. The seed-to-seed wobble
estimated from three runs is itself wobbly, which makes the bar wide and leaves the decisive gap
sitting at 0.91× threshold — uncomfortably close. More runs would tighten the bar by roughly
**1.63×**. But the project's own frozen rules forbid adding seeds, for a good reason, so this had to
be built carefully.

### How we did it

Adding seeds to an existing campaign after seeing its result is *optional stopping*: it lets you keep
sampling until the answer changes, and it invalidates every verdict the campaign reports. So SE is
**not** the old campaign with more seeds. It is a **separate campaign** with its own noise estimate,
its own bar and its own verdicts, reported alongside the committed three-seed results and never
replacing them — the same additive pattern T2 used. Its eight seeds were fixed in writing before the
first run, so SE is not subject to optional stopping either. It covers the four arms that appear in a
decisive gap (B, C10, CSHUF, CINV) and excludes A0 and A2, which appear in none. The twelve runs at
the original seeds are re-scored rather than re-trained and must reproduce their committed values
exactly. The sign-consistency requirement was set at 7 of 8 and declared in the direction that makes
our own claim *harder* to support, since the alternative would have biased toward the answer we
expect.

### What we found

**All sixteen gaps came back `WITHIN NOISE`** — four comparisons × two architectures × two
endpoints. The committed null survives. 40 new runs, 75.9 GPU-hours, finished 2026-09-22 17:54.

A power loss on 2026-09-20 interrupted the campaign: 36 runs verified intact, 2 partial runs were
discarded and re-run from scratch, and no partially trained model could enter the pool. Because no SE
number had been computed at that moment, resuming cannot have been influenced by any result.

**The decisive comparison, before and after.** Both rows are the same question — *does choosing
images by uncertainty beat choosing them at random?*

| | seeds | Δ(C10 − B) | σ̂ | bar (2σ̂) | gap ÷ bar | verdict |
|---|---|---|---|---|---|---|
| ABC, committed | 3 | +0.005034 | 0.008966 | 0.017933 | 0.28× | `WITHIN NOISE` |
| *(same gap vs T2's tighter bar)* | 3 | +0.005034 | 0.002767 | 0.005533 | **0.91×** | `WITHIN NOISE` |
| **SE** | **8** | **+0.002352** | **0.003431** | **0.006862** | **0.34×** | **`WITHIN NOISE`** |

**Two things moved, and they moved apart.**

*The gap halved* — +0.005034 → +0.002352. Part of what the three-seed campaign measured as a gap was
seed luck, and it washed out with more runs. That is what a real nothing looks like when you sample
it more.

*The bar widened* — against T2's 0.005533, SE's is 0.006862. This is the result that reads
backwards, and it is the most important thing in this entry. Every arm's seed-to-seed spread came out
larger at eight seeds than at three:

| arm | sd at n = 3 (T2) | sd at n = 8 (SE) |
|---|---|---|
| B (random) | 0.00181 | 0.00251 |
| C10 (targeted) | 0.00406 | 0.00489 |
| CSHUF (shuffled) | 0.00166 | 0.00278 |
| CINV (reversed) | 0.00285 | 0.00302 |

Nothing got worse. **We found out the old number was too small.** A spread estimated from three runs
per arm (df = 8) lands low about as often as high; SE's rests on df = 28. The three-seed bars were
optimistic, and SE is the measurement that shows it.

**What this does to the sensitivity claim — the number that actually matters.** The design had to be
able to see the **0.0142** reference effect (the improvement this repository reproduced for the
published method). Against that target:

| | bar | bar ÷ 0.0142 | could it rule out the published effect? |
|---|---|---|---|
| ABC, committed | 0.017933 | **126%** | **No** — the yardstick was larger than the thing measured |
| **SE** | **0.006862** | **48%** | **Yes** — with room to spare |

This is the concrete gain. The paper's most awkward admission was that its headline instrument was
too blunt to exclude the very effect it argued against. **SE's bar is 2.6× tighter than the committed
campaign's and less than half the reference effect, and the measured gap is a third of the bar.** The
honest scope sentence changes from *"no effect above 0.0179"* to *"no effect above roughly 0.0069,
on eight seeds per arm."*

**The arm that points the wrong way wins, in every cell.**

| cell | B | C10 | CSHUF | **CINV** |
|---|---|---|---|---|
| SINet · COD10K | 0.71513 | 0.71748 | 0.71717 | **0.71959** |
| SINet · NC4K | 0.76802 | 0.76836 | 0.76768 | **0.77141** |
| SINet-v2 · COD10K | 0.69627 | 0.69517 | 0.69850 | **0.69865** |
| SINet-v2 · NC4K | 0.74998 | 0.74903 | 0.75138 | **0.75329** |

CINV *reverses* the uncertainty signal — it spends the budget on the clusters the score calls least
uncertain — and it holds the highest mean in **4 of 4** cells. T2 saw this in 3 of 4 at three seeds.
C10, the targeted arm, is below random on both SINet-v2 cells. Every one of these differences is
inside the bar, so **this is not a claim that reversing the signal helps.** It is the absence of any
ordering by signal direction, now at eight seeds: what the budget is aimed at does nothing this
instrument can see, while the fact that it is concentrated somewhere does.

### Why it matters

This closes the last of the three standard objections to a null — bad score (**OR**), untrained data
(**FX**), too few seeds (**SE**) — and it closes it in the uncomfortable direction first: the
pre-registration committed, in writing and before any run, to reporting a `REAL EFFECT` as a power
failure that would withdraw the paper's central claim. That branch did not occur, and it could have.

The result is stronger than the branch we were bracing for. The feared outcome was a bar shrinking to
0.0034 beneath a gap holding at 0.0050. What happened is that the bar grew slightly on 3.5× the
evidence *and* the gap halved, so the null holds comfortably rather than marginally — and it now
holds on the best noise estimate the project has.

**One caution for the write-up.** Do not say SE "tightened the bar" without naming the comparison.
Against the committed campaign it is 2.6× tighter; against T2 it is 1.24× wider. Both are true, and
only the first supports the sensitivity claim.

**Reported beside, never instead.** The committed three-seed verdicts are not recomputed or replaced.
SE agrees with them, so nothing has to be adjudicated — but that is two campaigns concurring, not one
confirming the other.

---

# 18. DIAG — Post-hoc diagnostics on data already collected

### The essence, and why we did it

After the campaigns were committed, several questions remained that needed no new training because
the answers were already sitting in the saved predictions and tables. What interval is the data
actually consistent with? What is the budget really being aimed at? Does the picture change if we
measure the boundary, which is what the signal was designed to move? And how much of the CHAMELEON
benchmark is still unchecked? None of this re-decides any verdict; all of it is labelled post-hoc.

### How we did it

We computed formal equivalence tests and confidence intervals on the committed scores, using only
the two arms in each comparison rather than pooling across all four. We broke the funded clusters
down by which source dataset their images come from, and decomposed endpoint error into the part
that sits between clusters and the part that sits within them. We re-scored all 36 runs' saved
predictions with two metrics built for boundaries, and swept the binarisation threshold to check the
answer was not an artifact of where we drew the line. For the contamination audit we added
resolution-normalised matching and keypoint matching with geometric verification, calibrating both
thresholds on the 41 pairs whose answer was already known and validating against a dataset where the
answer should be clean. Nothing was trained and nothing was re-inferred.

### What we found

Four things. **First**, the decisive gap is better resolved than the paper claims: the pre-registered
bar is inflated by an arm not in the comparison, and an interval computed on the two arms actually
compared is **[−0.0035, +0.0136]**, which *excludes* the 0.0142 reference improvement. **Second**,
the allocation is partly a dataset-source selector — **51.5%** of the budget lands on CAMO images
which are only **24.8%** of the pool, the two largest quotas take a third of the budget while holding
**7 of 2026** test images, and only **20.5%** of endpoint error variance sits between clusters at
all. **Third**, on boundary metrics the concentration effect becomes *measurable* on SINet (1.37× the
bar, all seeds agreeing) — but the **anti-targeted arm captures it just as fully**, and this holds at
every binarisation threshold. **Fourth**, CHAMELEON contamination rises from 41/76 to at least
**50/76 (65.8%)**, with the negative control still flagging zero.

> **The 51 you may remember is a superseded number.** DIAG's geometric extension put **10**
> candidates above the inlier operating point, which is where `41 + 10 = 51` came from. Clearing an
> inlier threshold only shows that local patches agree on a geometric model — two exposures of one
> static scene do too. `rebuild/D2_FINAL_AUDIT` adjudicates each candidate by warping the partner
> into the CHAMELEON frame and measuring the residual, and **rejects one of the ten** (`animal-7`,
> whose homography decomposes to −86.5° of shear). The adjudicated count is **50 = 41 Tier A + 9
> Tier B**, with **16** unchecked and **10** clean with respect to the training pool.
> `CONTAMINATION_LEDGER.md` is the authority; `results.md` §5.4 now reads from it.

### Why it matters

Two of these strengthen the paper materially: the interval is a stronger statement than "we could not
have seen it," and the boundary result demonstrates the concentration-not-targeting thesis on trained
accuracy rather than only on geometry. The mixture finding is a new, independently transferable
caution about allocating over a mixed target pool.

---

# The consensus across all experiments

The project tested whether a model's own uncertainty can tell you which synthetic images to
generate. The answer is a null defended from four directions rather than asserted once. Every
control has failed to explain it away. Not the score: perfect knowledge of true test error changed
nothing (OR, 8 of 8 cells within noise). Not the schedule: when the added images are genuinely
trained on instead of displacing existing ones, the gap *shrinks*, from +0.0050 to +0.0014 (FX).
Not a blind instrument: the same apparatus detects +0.0197 at 3.3x its bar (PC), though not an
effect the size of the nulls. And not too few seeds: at eight seeds per arm the committed gap halves,
from +0.0050 to +0.0024 against a bar of 0.0069, and all 16 cells return within noise (SE).

What survives positively is sharper than the null. Targeted selection does pick a different training
set — but so does any rule that spreads the budget unevenly, including one that keeps the shape and
destroys the signal inside it. Concentration, not targeting, produces the effect, and on boundary
metrics the anti-targeted arm captures all of it. Underneath sit concrete reasons: the data barely
clusters, the signal predicts the wrong kind of error, half the budget lands on a quarter of the
data, and the generator copies objects rather than inventing them.

Independently, CHAMELEON is at least two-thirds training data and the standard check calls it clean.

The one question that could have overturned the central claim is now closed. The seed expansion was
the only experiment with the standing to withdraw the paper's headline, it was pre-committed to
reporting that outcome if it occurred, and it did not occur. It also corrected the record in a way
that cuts against us: the three-seed bars were optimistic, and the project's honest sensitivity is
**no effect above roughly 0.0069 Sα** — coarser than the 0.0034 we projected, and still less than
half the 0.0142 effect the design had to be able to see.

# SCOPING_ANALYSIS.md — what the exemplars do, what our draft does, and what to do about it

**Status:** analysis only. Nothing here is drafted paper prose, and no part of `main_v2` was
edited. The rewrite plan is a separate document.

**Audience for this file:** us — the authors — as the working brief that the rewrite plan will be
built from.

**Sources read.** `official_papers/{VisionTransformer,CamoDiffusion,BiRefNet}.pdf` in full;
`rebuild/FinalPaper/Paper/main_v2.tex` (1325 lines) and its compiled PDF (28 pp., main text pp.
1–12, appendix from p. 13); `rebuild/FinalPaper/EXPERIMENTS_EXPLAINED.md`;
`rebuild/FinalPaper/results.md`; `rebuild/D2_FINAL_AUDIT/CONTAMINATION_LEDGER.md`;
`rebuild/{OR,FX,SE}/` logs and pre-registrations; `rebuild/FX/FX_RESULTS.md`.

**One measurement up front, because it frames everything below.** Numbers per 1000 words of running
prose, table rows excluded:

| Paper | main text | abstract + intro | conclusion |
|---|---|---|---|
| ViT | 74 | **52** | 11 |
| CamoDiffusion | 71 | **43** | 13 |
| BiRefNet | 70 | **41** | 0 |
| **`main_v2`** | **139** | **132** | **105** |

All three exemplars roughly halve their numeric density when they move from results into
introduction, and drop it by another factor of four in the conclusion. Our draft does not vary at
all: the introduction is as dense as the results section, and the conclusion is denser than any
exemplar's results. Our abstract+intro is 1151 words against ViT's 524. This one ratio is the
single most reliable signal of the "reads like a data dump" problem, and it is fixable
mechanically.

---
---

# PART 1 — The exemplars, section by section

## 1.1 ViT — *An Image is Worth 16x16 Words* (ICLR 2021, 9 pp. main text)

### Page budget (measured from the PDF)

| Section | Pages | Share |
|---|---|---|
| Title + abstract | 0.25 | 3% |
| 1 Introduction | 1.2 | 13% |
| 2 Related Work | 0.8 | 9% |
| 3 Method (3.1 ViT, 3.2 Fine-tuning) incl. Fig. 1 | 1.6 | 18% |
| 4 Experiments (4.1–4.6) incl. 6 figures, 2 tables | 4.75 | 53% |
| 5 Conclusion | 0.4 | 4% |

Method is 18% of the paper. Experiments are more than half. **The method section is the smallest
substantive section in the paper** — a point worth sitting with, given that our own Methods
currently runs longer than our headline result.

### The narrative arc, and why the order works

ViT's introduction is a five-move funnel, and the fourth move is a negative result:

1. **Where the field is, stated as a fact about another field.** "Self-attention-based
   architectures ... have become the model of choice in NLP." Two sentences on why: pre-train
   large, fine-tune small, no sign of saturation.
2. **The contrast.** "In computer vision, however, convolutional architectures remain dominant."
   Then a list of what has been tried to bridge the gap and exactly why each failed to displace
   CNNs — "have not yet been scaled effectively on modern hardware accelerators due to the use of
   specialized attention patterns."
3. **What we did, in the plainest possible words.** "we split an image into patches and provide the
   sequence of linear embeddings of these patches as an input to a Transformer. Image patches are
   treated the same way as tokens (words) in an NLP application." No notation. No equation. No
   architecture name yet.
4. **The negative result, volunteered, with its mechanism.** "When trained on mid-sized datasets
   such as ImageNet without strong regularization, these models yield modest accuracies of a few
   percentage points below ResNets of comparable size. This seemingly discouraging outcome may be
   expected: Transformers lack some of the inductive biases inherent to CNNs, such as translation
   equivariance and locality, and therefore do not generalize well when trained on insufficient
   amounts of data."
5. **The turn, and the scope condition.** "However, the picture changes if the models are trained
   on larger datasets (14M-300M images). We find that large scale training trumps inductive bias."
   Only now do the headline numbers appear — four of them, in one sentence, never repeated in the
   body.

**This is the structure our paper needs and does not have.** ViT's paper is, read cold, a paper
about a method that does not work under the obvious conditions and does work under a stated one.
It leads with the failure, gives a mechanism for the failure, and then bounds it. We have the same
shape — the loop does not help; here is why; here is what actually moves the training set — and we
currently present it as a verdict plus a pile of qualifications.

Note also what move 4 does rhetorically: **the negative result is introduced as something the
reader should have expected**, not as a disappointment. "may be expected" converts a weakness into
evidence that the authors understand their own object.

### How an outsider gets onboarded

ViT assumes you know that CNNs and Transformers exist. Everything else is defined at the point of
use, in prose, usually by analogy:

- patch embeddings, `[class]` token, position embeddings — each gets a sentence in §3.1, tied to
  BERT ("Similar to BERT's `[class]` token, we prepend a learnable embedding").
- "attention distance" — a quantity they invent — is defined by analogy in the same sentence:
  "This 'attention distance' is analogous to receptive field size in CNNs."
- Every dataset gets its size inline the first time it appears: "ImageNet-21k with 21k classes and
  14M images", "JFT with 18k classes and 303M high-resolution images".
- VTAB is not assumed: its three task groups are spelled out ("Natural – tasks like the above,
  Pets, CIFAR, etc. Specialized – medical and satellite imagery, and Structured – tasks that
  require geometric understanding like localization").
- Few-shot vs. fine-tuning accuracy — the two reporting modes — get a paragraph explaining what
  each means and *why they use each one* ("we sometimes use linear few-shot accuracies for fast
  on-the-fly evaluation where fine-tuning would be too costly").

The background cost is paid in §4.1 "Setup", in one labelled place, in four bolded run-in
paragraphs: **Datasets. / Model Variants. / Training & Fine-tuning. / Metrics.** Nothing
methodological leaks into the results.

### Intuition-to-formalism ratio

§3.1 is roughly 350 words of prose wrapped around four numbered equations. The equations are
**never walked through** — no "where the first term..." The prose *before* them does all the
explaining, and the equations act as a precise restatement for someone who wants to implement it.

Then, crucially, two named prose paragraphs follow the math and say what it *means*:

- **"Inductive bias."** — what the architecture gives up relative to a CNN, and where the
  remaining 2D structure enters. This paragraph is what makes §4.3's whole argument legible.
- **"Hybrid Architecture."** — the variant, in prose, no equations.

§3 contains **zero numbers**. The entire method section is qualitative.

### How claims are made and evidenced

Uniformly claim-first, evidence-second, table-deferred:

> "Table 2 shows the results. The smaller ViT-L/16 model pre-trained on JFT-300M outperforms BiT-L
> (which is pre-trained on the same dataset) on all tasks, while requiring substantially less
> computational resources to train."

Note: "on all tasks" and "substantially less" — no numbers quoted at all, because they are in the
table two inches away. When ViT does quote a number in prose, it is a **ratio or a shape**, not a
table read-out: "ViT uses approximately 2−4x less compute to attain the same performance"; "ViT-B/32
is slightly faster than ResNet50; it performs much worse on the 9M subset, but better on 90M+
subsets."

§4.3 — the section carrying the paper's actual thesis — quotes almost no absolute numbers. Its
argument is carried entirely by Figures 3 and 4, with prose describing *the shape of the curves*.

### Connective tissue

Section openings are recap → question → plan:

> §4.3: "The Vision Transformer performs well when pre-trained on a large JFT-300M dataset. With
> fewer inductive biases for vision than ResNets, how crucial is the dataset size? We perform two
> series of experiments."

Section 4 opens with a roadmap that also grades its own contents, weakest last: "Lastly, we perform
a small experiment using self-supervision, and show that self-supervised ViT holds promise for the
future."

Sections close forward: §4.3 ends "Further analysis of few-shot properties of ViT is an exciting
direction of future work."

### How ViT handles limitations and honest negatives — the four moves we should steal

1. **Concede inline, then point at where it is controlled.** §4.2, immediately after the headline
   win: "However, we note that pre-training efficiency may be affected not only by the architecture
   choice, but also other parameters, such as training schedule, optimizer, weight decay, etc. We
   provide a controlled study of performance vs. compute for different architectures in Section
   4.4." One sentence of concession, one sentence of pointer. No paragraph of hedging.
2. **Volunteer the surprise that cuts against you.** §4.4: "This result is somewhat surprising,
   since one might expect convolutional local feature processing to assist ViT at any size."
3. **State a shortfall as a plain number and stop.** §4.6: self-supervised pre-training gives
   "a significant improvement of 2% to training from scratch, but still 4% behind supervised
   pre-training." Then: "We leave exploration of contrastive pre-training to future work."
   One paragraph, placed last, for the weakest thing in the paper.
4. **A conclusion that is a list of open problems.** "While these initial results are encouraging,
   many challenges remain." Three named challenges, no numbers.

---

## 1.2 CamoDiffusion (preprint, 9.5 pp. before references)

### Page budget

| Section | Pages | Share |
|---|---|---|
| Title + abstract | 0.3 | 3% |
| 1 Introduction (incl. 3 numbered contributions) | 1.2 | 13% |
| 2 Related Work (2.1 COD, 2.2 diffusion for segmentation) | 0.85 | 9% |
| 3 Method (3.1 background, 3.2 architecture, 3.3 training, 3.4 sampling) + Figs. 1–2 | 3.5 | 37% |
| 4 Experiment (4.1 settings, 4.2 comparisons, 4.3 ablations, 4.4 analysis) + Tabs. 1–2, Figs. 3–6 | 3.3 | 35% |
| 5 Conclusion | 0.3 | 3% |

### The narrative arc

The introduction is a four-move funnel and it is the cleanest template in the three papers for a
*task* introduction (ViT's is a *field* introduction):

1. **What the phenomenon is, in the world, before any computer vision.** "Camouflage, a pervasive
   defense strategy in nature, endows organisms with the capacity to meld seamlessly into their
   surroundings, thereby allowing them to elude predators or approach prey surreptitiously." Then
   why anyone should care: species conservation, medical image segmentation, industrial flaw
   detection — three named applications with citations.
2. **What has been tried, as a taxonomy.** Three numbered families (multi-stream, bottom-up/
   top-down, branched), one sentence each, citation clumps. This is the entire related-work
   preview, done in the intro, in six lines.
3. **The single shared flaw.** All three families "build upon the foundational semantic
   segmentation paradigm ... However, such a paradigm is prone to confuse the subtle deviation
   between boundaries and surroundings of camouflaged objects due to the body outline disguising,
   leading to unsatisfactory predictions. Furthermore, the segmentation paradigm depends on
   pixel-wise probabilities leading to overconfident incorrect predictions."
4. **Our paradigm, its three advantages, its three contributions.** Advantages are numbered 1–3 in
   prose; contributions are numbered 1–3 as a list. Both are short.

### How an outsider gets onboarded — the best single lesson in the three papers

**§3.1 is titled "Background and Notation" and it teaches diffusion models from zero.** Forward
process, marginal, reverse process, the choice to predict `x̂₀` rather than `x_{t−1}`, the loss —
four equations, all standard, all cited to Ho et al., none of them the paper's contribution.
Roughly 0.7 of a page spent teaching the reader something the authors did not invent, placed
immediately before the first thing they did.

That subsection exists purely so that §3.2 onward can be read by someone who has never implemented
a diffusion model. **This is the move our paper most needs and completely lacks**: one labelled
place where the reader is taught the vocabulary — S-measure, arm, seed, pooled spread, the bar —
before any of it is used to decide anything.

§3 also opens with an explicit roadmap: "We first introduce the basic background and notation in
Section 3.1. Then we discuss the architectural details of the ATCN and DN in Section 3.2. The
details of the specially designed learning strategies are mentioned in Sec. 3.3 and Sec. 3.4."

### Intuition-to-formalism ratio

Every component follows the same three-beat micro-arc, and it is worth naming because it is
mechanical enough to copy:

> **challenge → why the obvious thing fails → our fix → (equation) → what it buys**

Zero Overlapping Embedding, in full: "To incorporate the noise mask `x_t` into the PVT without
destroying the original transformer structure and pre-training parameters, we propose the Zero
Overlapping Embedding (ZOE) ... Specifically, ZOE uses an extra convolution layer initialized with
zeros, which gradually introduces `x_t` in a controlled manner without affecting the position
encoding during initialization." → Eq. 6 → "This module effectively addresses the challenges
associated with the conventional approach of modifying the input channel of OE, which leads to the
re-initialization of layer parameters and longer convergence times."

The two design *challenges* are enumerated before either is solved: "We identify two primary
challenges in the design of a conditional network: 1) Extracting more discriminative image
features; 2) Adaptively supplying conditional features in accordance with the denoising step."
The rest of the subsection answers 1) and 2) in order.

### How claims are made and evidenced

**Extremely sparing with numbers in prose.** §4.2's entire quantitative comparison paragraph quotes
exactly two, both *relative*: "our model dramatically reduces the MAE error by 17.4% and increases
`F_β^w` by 4.2% compared to the second-best performer, CamoFormer-P." Everything else — 19
competitors, 4 metrics, 3 datasets — is Table 1.

**The ablation section quotes zero numbers.** §4.3 is three paragraphs of "Tab. 2a shows... Our
results show that the integration of the diffusion framework significantly improves the performance
of the proposed method." The mechanism is explained in prose ("the absence of ZOE leads to inferior
performance compared to the baseline, primarily because the random initialization of the
convolution layer fails to add positional information to the embeddings, resulting in slower
convergence") and the reader is trusted to read the table.

**Qualitative results get real prose.** §4.2's "Visual Comparison" walks specific rows of Figure 3:
"The examples illustrated in the first six rows exhibit typical scenarios... The examples in the
seventh to ninth rows contain complex topological structures and detailed edges."

### Honest framing

One move, done well and inline: naming the competitor's advantage in the same breath as the win.
"Notably, HitNet also performs well on these examples, but it utilizes high-resolution images of
704² as input, whereas CamoDiffusion achieves better results using only images of 384² resolution."
And the hyperparameter ablation names the cost of its own choice: "the model's performance improves
as the number of sampling steps increases, but it also leads to longer inference time. We set the
sampling steps to 10 for a trade-off."

No limitations section. The concessions are one clause long and sit where the claim is made.

---

## 1.3 BiRefNet (CVPR-style, 11 pp. before references)

### Page budget

| Section | Pages | Share |
|---|---|---|
| Fig. 1 teaser + abstract + 1 Introduction + contributions | 1.6 | 15% |
| 2 Related Works (2.1 HR class-agnostic seg., 2.2 progressive refinement) + Fig. 2 | 1.4 | 13% |
| 3 Methodology (3.1–3.6) + Figs. 3–4 | 2.7 | 25% |
| 4 Experiments (4.1 datasets, 4.2 **evaluation protocol**, 4.3 impl., 4.4 ablation, 4.5 SOTA) | 4.6 | 42% |
| 5 Potential Applications + 6 Third-Party Creations | 1.2 | 11% |
| 7 Conclusions | 0.3 | 3% |

### The narrative arc

1. **A teaser figure before the abstract.** Figure 1 is four zoomed crops: GT / Ours / IS-Net /
   UDUN. The reader sees the claim before reading a word.
2. **Intro in three paragraphs.** Where the task came from and who uses it ("by Samsung, Adobe, and
   Disney"); what recent work does and the one-sentence summary of its limit ("they either split
   the supervision at the feature-level or introduce an additional prior to enhance feature
   extraction. These strategies are, however, still insufficient to capture very fine features (see
   Fig. 1)"); **then an observation, stated as an observation**: "Based on our observations, we
   found that fine and non-salient features in image objects can be well reflected by obtaining
   gradient features through derivative operations on the original image." The method is derived
   from that observation in the next two sentences.
3. **Four numbered contributions**, one line each, the last carrying all the headline numbers.
4. **Figure 2 on page 2: a positioning diagram.** Four schematic pipelines side by side —
   (a) common framework, (b) image pyramid as input, (c) scaled images as inward reference,
   (d) ours — with a two-line caption. **This is the single most transferable graphical device in
   the three papers for our paper**, and it is discussed further in Part 2.

### How an outsider gets onboarded — the second big lesson

**§4.2 "Evaluation Protocol" spends most of a page defining the metrics**, with equations:
S-measure, max/mean/weighted F-measure, max/mean E-measure, MAE, and relax HCE. Each gets a
sentence of plain description before its formula — "S-measure is a structural similarity
measurement between a saliency map and its corresponding GT map. Evaluation with `S_α` can be
obtained at high speed without binarization" — and the α = 0.5 default is stated with its source.

This is a paper written *for* the segmentation community, whose readers all know what S-measure is,
and it defines S-measure anyway, with an equation, on page 6. **Our paper reports a single primary
endpoint in `S_α`, decides every verdict on it, and never defines it in the main text.**

Also note §3.3's opening: it motivates a design choice from a general principle before naming any
component — "The setting of the receptive field (RF) has been a challenge of HR segmentation. Small
RFs lead to inadequate context information to locate the right target on a large background,
whereas large RFs often result in insufficient feature extraction in detailed areas. To achieve
balance, we propose..."

### Intuition-to-formalism ratio

Formalism is concentrated in §3.5 (objective function) and §4.2 (metrics) — two labelled places.
§3.2–3.4, the actual contribution, are almost pure prose plus two figures. The BiRef mechanism is
explained in functional terms before any symbol: "Inward reference and outward reference play the
roles of supplementing HR information and drawing attention to areas with dense details,
respectively."

### How claims are made and evidenced

Same pattern as the other two: **mechanism in prose, then one relative number.**

> "InRef supplemented lossless HR information globally, while OutRef drew more attention to the
> fine-detail parts to achieve higher precision in those areas. As shown in Tab. 2, they work
> jointly to bring 2.9% `F_β^x` relative improvement to BiRefNet. RM and BiRef are combined to
> achieve 6.2% `F_β^x` relative improvement."

Every quoted figure in §4.4 is a *relative* improvement. The absolutes — seven tables' worth — are
never read aloud.

§3.6 is unusual and useful: **a subsection of negative and practical findings about training**,
written as four numbered observations ("First, we found that our model converges relatively
quickly in the localization of targets ... However, the performance in segmenting fine parts is
still increasing after very long training"). It reports a *cost* honestly — "Although simple long
training can achieve better results, the improvement is relatively small, concerning its high
computational cost on HR data" — and then presents the cheaper alternative.

### Where BiRefNet is an anti-exemplar for us

BiRefNet has **no limitations section and no negative framing at all.** It is a pure-win paper, and
it spends its spare 1.2 pages on Potential Applications and Third-Party Creations — the things a
paper does when it has no caveats to spend space on. Take its craft (metric definitions, the
positioning figure, mechanism-then-relative-number ablations, the practical-findings subsection);
do not take its rhetoric. Our paper's centre of gravity is the opposite.

---
---

# PART 2 — The distilled section playbook

Ten patterns hold across all three papers. They are listed first as rules, then applied to the
sections our paper should have.

## 2.1 The ten recurring patterns

| # | Pattern | Evidence |
|---|---|---|
| **P1** | **One controlling question per section, stated in its first two sentences.** Recap what is settled, ask the new question, say how many experiments answer it. | ViT §4.3, §4.4; BiRefNet §3.3 |
| **P2** | **Background is paid for once, in a labelled place, immediately before the contribution needs it** — never scattered at point of use, never deferred to an appendix. | CamoDiffusion §3.1; BiRefNet §4.2; ViT §4.1 |
| **P3** | **Intuition → formalism → consequence.** No equation without a preceding sentence saying what it is for and a following sentence saying what it buys. Equations are never walked through term by term. | ViT §3.1 + "Inductive bias."; CamoDiffusion ZOE |
| **P4** | **Numbers in prose are sparse, relative, and stated once.** Absolutes live in tables. Target: ~45 numbers per 1000 words in abstract+intro, ~70 in results, ~10 in the conclusion. | measured, all three |
| **P5** | **Claim first, evidence second, one claim per paragraph.** The claim is the topic sentence; the table reference is the second sentence. | all three, uniformly |
| **P6** | **A positioning figure in the first three pages** that places the work inside a family of alternatives at a glance. | BiRefNet Fig. 2; ViT Fig. 1; CamoDiffusion Fig. 1 |
| **P7** | **Concede inline in one sentence, then point at where it is controlled.** Never build a paragraph around a caveat that an experiment already answers. | ViT §4.2 → §4.4; CamoDiffusion on HitNet |
| **P8** | **Sections close forward** — a summary sentence or a pointer to what the next section settles. | ViT §4.3; CamoDiffusion §3 roadmap |
| **P9** | **The weakest result goes last and gets exactly one paragraph**, with its shortfall stated as a plain number. | ViT §4.6 |
| **P10** | **Mechanism before metric.** Say in words what a component or condition does; quote one relative number afterward. | BiRefNet §4.4; CamoDiffusion §4.3 |

Two further observations that are not patterns so much as calibration:

- **Method sections are small.** ViT 18%, BiRefNet 25%, CamoDiffusion 37% (and CamoDiffusion is a
  pure architecture paper). Evidence sections are 35–53%. Our draft currently spends more space on
  its decision rule than on the result the rule decides.
- **Visual density is high.** ViT: 2 tables + 7 figures in 9 pages. CamoDiffusion: 2 + 6 in 9.5.
  BiRefNet: 7 + 9 in 11. **Our main text has 2 tables and 1 figure in 12 pages.** The argument is
  carried almost entirely by prose, which is why it reads as a wall.

## 2.2 The playbook applied — the sections our paper should have

The ordering below is the recommendation. Each entry gives the section's **job**, its **voice**,
what **content belongs**, and what must **not** be there.

---

### §1 Introduction — target 1.2 pp.

**Job.** Get a non-COD reader from "what is camouflaged object detection" to "these authors built a
reasonable thing, it did not work, and they found out why" in under five paragraphs. The reader
should be able to state the paper's claim after reading only this section.

**Voice.** Plain, declarative, almost no notation. ViT move 3: describe the loop in words a person
could follow without a figure.

**Content, in this order (the ViT five-move funnel, adapted):**
1. The task and why its labels are expensive — one paragraph, no citations needed beyond the
   survey. Why synthetic data is the standard remedy.
2. The question nobody has answered: under a fixed budget, *which* images should you generate?
   Name the obvious answer (let the model's own uncertainty choose) and note that every ingredient
   is standard, so this is a composition anyone would try.
3. What we built, in one short paragraph of plain words.
4. **The negative result, volunteered, with its mechanism named but not quantified.** This is
   ViT's move 4. State that the direction of the signal changes nothing we can resolve; then
   immediately state the positive finding that explains it — concentration, not direction, is what
   makes a targeted set different.
5. The scope sentence: what size of effect this design could and could not see, in one sentence
   with at most two numbers. Then the second, independent contribution (CHAMELEON) in two
   sentences.

**Content budget:** ≤ 650 words, ≤ 30 numbers. Currently 1151 words and 152 numbers.

**Must not contain.** `C10`, `B`, `CSHUF`, `CINV`, `σ̂`, `2σ̂`, `within noise`, `df = 8`, `S_α`,
"126%", "3.24×", "0.91×", or three different noise bars. None of these mean anything yet.

**Contributions list.** Keep it, at BiRefNet length: four items, one line each, numbers only in the
last one. Not five paragraphs.

---

### §2 Background and Related Work — target 0.9 pp.

**Job.** Two things: (a) teach the reader the four or five terms the rest of the paper decides on,
and (b) place the work among systems that steer a generation budget.

**Voice.** Textbook for (a), comparative for (b).

**Content.** This is where CamoDiffusion §3.1 and BiRefNet §4.2 get adapted. A short labelled
block — "What we measure and how we decide" or similar — that defines, in plain words with at most
one equation:
- **S-measure (`S_α`)**: what it rewards, its range, and the fact that scores here sit near 0.70,
  so the reader can calibrate every Δ in the paper. *Non-negotiable: we decide everything on this
  metric and currently never define it.*
- **arm / seed / endpoint** — three words, one sentence each.
- **the reference effect** the design was built to detect, stated once in plain terms.

Then related work as three short paragraphs: closest systems (LAKE-RED, S2R-COD) and what we
changed; acquisition/uncertainty lineage; the three budget-steering systems (GAUDA, DisCL,
SynQuE) and the control none of them runs.

**Must not contain.** The `tab:closest` comparison table. ViT places no comparison table in related
work; two sentences carry the same content and the table moves to the appendix. This alone
recovers ~0.35 pp.

**Also move out.** The "Evaluation context" paragraph (currently at the end of §2) is Methods
content — which datasets, which detectors, which metrics. It belongs in §3.

---

### §3 The loop we built — target 1.4 pp.

**Job.** Specify the thing that failed precisely enough that the null means something, and no more
precisely than that.

**Voice.** CamoDiffusion's four-stage narration. Picture first, then stages, then the one equation.

**Content.**
- The setting: source pool, target pool, two endpoints. One paragraph.
- The four allocation stages, as they are now — this part of the draft already works.
- Equation 1 (the ES score), kept, with P3 applied: one sentence before saying what it is for, one
  after saying what it buys. Flag and fix the α collision (`S_α`'s weighting parameter vs. the
  allocation temperature) here.
- **The arms, presented as a figure, not a list.** See §2.3 below.
- The decision rule, compressed: the four verdict bands stay, but the provenance apparatus
  ("committed at a named commit", "append-only and dated", "thresholds that failed are reported
  failed") moves to the Reproducibility statement, which already says all of it.

**Must not contain.** The Jaccard gate, the permutation-selection rule (first of 64 draws with
`|ρ| ≤ 0.10`), the realised rank correlation, the df bookkeeping. All appendix. They are
reassurance, not argument, and each one costs a reader's attention at the exact moment they are
trying to hold six arm names in their head.

---

### §4 Does targeting beat random? — target 1.8 pp.

**Job.** Deliver the null and, in the same section, close the three standard objections to it.

**Voice.** ViT §4.2 — claim, table, one concession, pointer. Not apologetic.

**Content.**
- The verdict, in one sentence, with one number.
- **One table carrying every trained comparison**: ABC (the null), T2 (same-shape), OR (oracle),
  FX (unpinned), PC (positive control), and SE when it lands. Currently these are scattered, and
  three of them are not in the paper at all.
- Then three short paragraphs, each closing one objection, each following P7 (concede once, point
  at the control):
  - *"You picked a bad uncertainty estimator."* → **OR.** Replacing the score with the true
    per-cluster test error changes nothing (8/8 within noise); the score and the truth agree at
    ρ = +0.237, so we replaced it with something four times better and still nothing moved.
  - *"Your added data was never trained on."* → **FX.** Unpin the schedule and the gap *shrinks*.
  - *"Three seeds is not enough."* → **PC** for sensitivity, **SE** for the bar. See §4.4 below
    on how to write this before SE lands.
- The sensitivity statement: one bar, one interval, stated once. Not three bars.

**Must not contain.** Three competing noise bars narrated in sequence. Pick the defensible headline
(the arm-specific Welch interval, which is the strongest honest statement we have) and put the
pooled-bar arithmetic in the appendix with a one-sentence pointer.

---

### §5 Concentration, not targeting — target 1.4 pp.

**Job.** This is the paper's positive result and its title. It should read as a discovery, not as a
control.

**Voice.** Confident. This is the one section with no hedging in it, because the evidence is strong
and the draft already knows it ("we state it without hedging" — keep that instinct and extend it to
the whole section).

**Content.**
- The setup as a near-paradox, which the current §4.1 already does well: a probe separates targeted
  from random sets easily, and it is tempting to read that as success.
- The dismantling: shuffle the scores, the separation survives; aim at an arbitrary cluster, it
  survives; destroy the unevenness and it collapses.
- Figure (the existing `fig1_thesis`), which carries this.
- **Then the promotion of the boundary result from the appendix into this section.** The draft
  itself calls this "the paper's thesis on accuracy rather than geometry, and the strongest form of
  it we have" — and its table is currently in Appendix E. On SINet the concentration effect clears
  its bar on Boundary IoU and Boundary F, and the *anti*-targeted arm reproduces it to within a
  tenth of a bar. This is the one place where we can show the instrument resolving concentration
  and failing to resolve direction *in the same cells*, which is what makes the null something
  other than an absence of power. It must be in the main text with its table.
- The qualifications, at ViT length: not pre-registered; binarisation swept; SINet-v2 resolves
  none of it. Three clauses, not three bolded paragraphs.

---

### §6 Why it fails — target 0.7 pp.

**Job.** Convert four separate measurements into one causal chain, so the reader leaves with a
mechanism rather than a list.

**Voice.** ViT's "This seemingly discouraging outcome may be expected" — the failure as something
the evidence predicts.

**Content.** One paragraph per link, each with one number:
1. The data barely clusters (silhouette 0.16 at best, three embedding spaces) — so a cluster-wise
   policy is partitioning something the data does not support.
2. Only ~20% of endpoint error variance sits between clusters at all — so four fifths of what a
   perfect policy would have to fix is invisible to any cluster-level allocation.
3. The budget is partly a dataset selector: 51.5% lands on CAMO, which is 24.8% of the pool.
4. The signal points at pixel error, not structural error, and this holds for three independent
   uncertainty estimators — so it is a property of uncertainty-guided allocation here, not of our
   score.
5. The generator copies objects and paints backgrounds, so the foreground supply is fixed at 4447
   and the generated distribution is narrower than its own input.

**This section absorbs the current §4.3, §4.4 and §5.1.** Those are causes, not results; presenting
them as three more result subsections after the null is why the middle of the paper sags.

**Must contain, and currently does not:** the deletion of the claim that the pinned optimisation
budget "is also the largest open question this paper creates." FX measured it. It is now a closed
cause, and a stronger one for being measured.

---

### §7 CHAMELEON is mostly training data — target 0.9 pp.

**Job.** Deliver a fully independent, highly portable contribution, and make the methodological
rhyme with §5 without labouring it.

**Voice.** Flat and factual. The finding does not need help.

**Content, three paragraphs and a figure:**
1. The finding and the failure of the standard check: 50 of 76 are re-encoded, rescaled or cropped
   copies of COD10K-train and CAMO training images; exact hashing returns 0 because not one byte
   matches while every pixel does. 16 unresolved, so 50 is a floor.
2. How we know: two tiers (same-dimension re-encode; homography-warped residual for rescales and
   crops), calibrated on the 41 already known, verified against an author-sourced release, and a
   negative control that flags 0 on NC4K.
3. What we claim and what we do not: non-independence, not inflation — we measured for inflation
   and did not find it. Then the protocol recommendation (retire, do not subset) and the concrete
   instance in the protocol we test (44 of 76 sit in its unlabelled target pool).
4. Figure: the confirmed pairs (`fig:chamext` / `fig:pairs`, currently appendix-only).

**Must not contain.** The tolerance sweep, the 7.36× nearest-neighbour jump, the CAMO-250
byte-identical triple, the mask-release IoU, the inlier operating point, the excluded tenth
candidate and its shear decomposition. Every one of those is good work and every one belongs in the
appendix. The current version is **3.0 pages** — a third of an ICLR paper spent on a result whose
essential content is three paragraphs.

**Structural change:** promote this from `\subsection` of the Discussion to a top-level
`\section`. It is currently a depth-2 subsection sitting behind a limitations subsection, which is
the least visible position in the paper for its most portable contribution.

---

### §8 Discussion and conclusion — target 0.4 pp.

**Job.** Say what transfers, and what would have to be true for the idea to work.

**Voice.** ViT's conclusion: what we did, what is simple about it, what remains. Near-zero numbers
(exemplar rate: 0–13 per 1000 words; ours is currently 105).

**Content.** The two-kinds-of-evidence distinction, stated **once** — it currently appears in the
abstract, the introduction, the opening of §5 and the conclusion, four times in near-identical
words. The transfer claims, which are already written well and scattered as `\textbf{Transfers:}`
tags at the end of subsections: gather them here. What would have to change for the loop to have a
chance.

**Must not contain.** A recap of the sensitivity arithmetic. A fourth restatement of the
geometric/downstream split.

---

## 2.3 Two figures the paper needs and does not have

**Figure 1 — the arm diagram (BiRefNet Fig. 2 adapted).** The paper asks the reader to hold seven
allocation rules (A0, A2, B, C10, CSHUF, CINV, CORACLE, plus the FX variants) that differ along two
independent axes — *how concentrated the budget is* and *where it points*. There is currently no
picture of this, and the distinction between the two axes **is the paper's thesis**. BiRefNet
places exactly this kind of one-glance family diagram on page 2, before the method. A 2×N grid or a
two-axis schematic showing which arm holds what fixed would do more work than any paragraph in §3.

**Figure 2 — what a targeted allocation actually looks like.** The 51.5%-to-CAMO finding, the two
largest quotas holding 7 of 2026 endpoint images, and the weak silhouette are currently three
sentences and an appendix figure. One panel showing the budget landing on the pool would make §6
land in a glance. `fig:clusterdiag` already exists in the appendix and may be adaptable.

Both are cheap in pages (~0.25 pp. each) and both buy back more prose than they cost.

---
---

# PART 3 — Diagnosis of `main_v2`

## 3.1 What the draft actually is right now

Compiled: 28 pp. Main text pp. 1–12 (appendix begins p. 13). Measured allocation:

| Section | `main_v2.tex` lines | Pages | ICLR target |
|---|---|---|---|
| Title + abstract | 11–76 | 0.55 | 0.3 |
| 1 Introduction | 81–159 | 1.6 | 1.2 |
| 2 Related Work (incl. `tab:closest`) | 163–255 | 1.35 | 0.9 |
| 3 Methods (3.1–3.4) | 257–370 | 1.55 | 1.4 |
| 4 Results (4.1–4.4, `tab:null`, `fig:thesis`) | 374–616 | 3.5 | 3.2 |
| 5 Discussion (5.1 limitations, 5.2 contamination) | 621–774 | 3.0 | 1.6 |
| 6 Conclusion | 776–801 | 0.45 | 0.4 |
| Statements (AI use / ethics / reproducibility) | 803–881 | 1.0 | excluded from limit |
| Appendices A–J | 884–1325 | 15 | unlimited |

**Main text through the conclusion is ~11.9 pp. against a 9 pp. budget — about 3 pages over**,
assuming ICLR 2027 excludes the ethics and reproducibility statements as ICLR normally does. That
assumption should be confirmed against the 2027 CFP before the rewrite locks its budget.

Main-text visual anchors: **2 tables, 1 figure.** Exemplars at comparable length: 2+7, 2+6, 7+9.

---

## 3.2 Findings, most consequential first

Each is a concrete location, a concrete problem, and the playbook rule that fixes it.

---

### F1 — Three of our five strongest experiments are not in the paper at all
**Playbook: §4 content; P7.**

`grep` across the whole of `main_v2.tex` finds **no mention of OR, FX or SE** in the main text.
The only occurrence of "oracle" is a table cell at line 241, inside the related-work comparison
table. Yet these are precisely the answers to the three standard objections a reviewer will raise
against a null:

| Objection | Experiment | Status in `main_v2` |
|---|---|---|
| "You picked a bad uncertainty estimator" | **OR** — oracle targeting, 8/8 within noise, score↔truth ρ = +0.237 | absent |
| "Your added data displaced rather than augmented" | **FX** — unpin the schedule, gap shrinks +0.0050 → +0.0014 | absent |
| "Three seeds is not enough" | **SE** — 8 seeds, bar projected ~0.0034 | absent (running) |

The draft predates them (git: *"Waiting on SE completion and a rewrite with OR, FX and SE
results"*). This is the largest single gap between what the project has proved and what the paper
claims, and it is a gap in our favour.

**Consequence beyond the omission:** §5.1 (lines 645–652) still tells the reader that the pinned
optimisation budget "**is also the largest open question this paper creates**." FX closed that
question on 2026-09-20. The draft is currently conceding, in bold, a weakness we have measured and
eliminated.

---

### F2 — The core claim is stated four different ways and two of them are different claims
**Playbook: §1 move 4; P5.**

| Location | The claim as stated |
|---|---|
| Title (line 13) | "**Why Targeted Synthetic Data Doesn't Help** Camouflaged Object Detection" |
| Abstract (line 42) | "No advantage survives measurement" |
| Intro (line 98) | "a targeted allocation does not beat a random one" |
| §4 opening (line 377) | "Targeting did not beat random." |
| §5 opening (line 621) | the thesis is "concentration, not the uncertainty direction" |

The title asserts that targeted synthetic data does not help. The paper's strongest and
best-evidenced claim is different: **concentration explains the apparent effect of targeting, and
the direction of the signal contributes nothing this design can resolve.** The first is a null; the
second is a positive finding. A reviewer cannot tell which one they are being asked to evaluate,
and the draft's own §5 says the paper "is worth reading only if they are kept apart" — while the
title runs them together.

The commented-out alternative title at line 11 (*"Concentration, Not Targeting: A Pre-Registered
Null for..."*) is closer to the paper's actual content than the active one.

---

### F3 — The introduction is a results section
**Playbook: P4; §1 content budget.**

Abstract + introduction: **1151 words, 152 numbers, 132 numbers per 1000 words.** ViT: 524 words,
52/1000. CamoDiffusion: 680 words, 43/1000. BiRefNet: 441 words, 41/1000.

The worst single instance is the paragraph at lines 98–112, "What we found, and how far the
measurement reaches", which in one paragraph asks the reader to absorb:

> 24 runs · two architectures · four conditions · three seeds · `WITHIN NOISE` · a pooled bar ·
> "dominated by the unpadded arm A0" · 126% · a second campaign of 12 runs · 3.24× · 0.91× ·
> Δ(C10−B) = +0.0050 · 95% [−0.0035, +0.0136] · 0.0142 · a mean-teacher positive control ·
> +0.0197 · 3.3×

— **three different noise bars, ten quantities, and six undefined terms**, before the reader knows
what an arm is, what a seed is, what `S_α` measures, or what scale +0.0050 is on. Compare ViT's
equivalent moment, which is one sentence with four numbers and no notation.

The contributions list (lines 126–159) repeats the problem: five multi-sentence bullets, the second
of which carries six numbers to support a claim ("the target distribution separates only weakly")
that needs none at that point. BiRefNet's four contributions are one line each; ViT has no
contributions list at all.

---

### F4 — Vocabulary is used well before it is defined, and `S_α` is never defined
**Playbook: P2; §2 background block.**

| Term | First used | First defined |
|---|---|---|
| "arm" | line 42 (**abstract**) | line 311 (§3.3) |
| `WITHIN NOISE` | line 100 (intro) | line 337 (§3.4) |
| `C10`, `B` | line 105 (intro) | line 311 (§3.3) |
| `σ̂`, `2σ̂`, "df = 8" | lines 100–110 (intro) | line 338 (§3.4) |
| "mean-teacher" | line 40 (**abstract**) | line 276 (§3.1) |
| `S_α` | line 148 (intro, as `1−S_α` variance) | **never, in the main text** |

`S_α` is the paper's sole primary endpoint. Every verdict in the paper is a comparison of `S_α`
values. It appears first in a contribution bullet on page 2, is used to decide everything from page
5 onward, and is pinned to α = 0.5 only in Appendix B (line 961). An outsider has no way to know
whether +0.0050 is large or small, or what "structural" means as distinct from "pixel" error —
which is the distinction §4.4's entire argument rests on.

**BiRefNet defines S-measure with an equation on page 6, for an audience that already knows it.**
This is the clearest single fix available to us.

---

### F5 — The paper's strongest evidence for its own thesis is in the appendix
**Playbook: §5 content; P6.**

§4.2 (lines 515–545) says of the boundary-metric result:

> "This is the paper's thesis on accuracy rather than geometry, and the strongest form of it we
> have: the instrument that resolves concentration fails to resolve direction in the same cells, so
> the null on direction is not simply an absence of sensitivity."

Its table, `tab:boundary`, is labelled in `table_subgroup_metrics.tex` and `\input` at line 1061 —
inside **Appendix E, "Post-Hoc Diagnostics"**. The main text asks the reader to accept the paper's
strongest claim on the basis of numbers quoted in a paragraph, with the table eight pages away.

This is the clearest instance of a general problem: the main text has 2 tables and 1 figure across
12 pages, while the appendix holds 4 tables and 3 figures. The evidence and the argument have been
separated.

---

### F6 — Structural seams from an unfinished edit are visible to the reader
**Playbook: P8.**

- `% 5. DISCUSSION` appears **twice** as a section marker — at line 451 and again at line 619.
  Three subsections were moved out of Discussion into Results and the marker was left behind.
- Immediately after the first stray marker, lines 454–456 address the reader about a previous
  revision:
  > "The rest of this section reports the measurements that say *why*. **Three of them were
  > previously placed in the discussion; they are results, and they are reported as results.**
  > Each closes with what it transfers beyond this setup."

  The middle sentence is a note to ourselves about an editorial decision. A reader has never seen
  the earlier draft and cannot use this.
- §2 ends with an "Evaluation context" paragraph (lines 247–255) that is Methods content —
  datasets, detectors, metrics — sitting in Related Work.
- §7 (contamination), the paper's most portable contribution, is a `\subsection` of the Discussion,
  placed *after* the limitations subsection.

---

### F7 — The draft tells the reader how to read it, repeatedly, instead of showing the control
**Playbook: P7. Also: our own standing note on prose style — own the work, do not announce rigour.**

Reader-instruction moments in the main text, by line:

| Line | Text |
|---|---|
| 401 | "**The honest limit: this campaign resolved coarsely.**" |
| 426 | "The instrument is not blind." |
| 441 | "**Two loose ends, neither of which flatters us.**" |
| 486 | "**Scope, and the trained half is the weaker one.**" |
| 533 | "**Three qualifications, all cutting against it.**" |
| 627 | "A reader who takes the second claim as *proof* ... has read more than we measured; a reader who takes the first as merely suggestive has read less." |
| 653 | "Each has an obvious rebuttal and each rebuttal is right" |

Each is individually defensible. Together they make the paper read as anxious about its own result,
and they cost roughly a page. ViT's equivalent is one sentence of concession followed by a pointer
to §4.4, where the concession is controlled.

**We are in a better position than the hedging implies.** We have PC, T2, OR and FX — four controls
that close four objections with measurements. The playbook fix is to replace the hedge with the
pointer: state the objection in one clause and name the experiment that answers it.

The same instinct shows up as announced rigour: "committed at a named commit before the runs it
governs", "amendments are append-only and dated", "every numeric value in this paper is traceable
to a log block emitted by a committed script, and no number in this paper was transcribed by hand."
All true, all valuable — and all already stated in the Reproducibility statement, which is where
they belong.

---

### F8 — Run counts contradict each other across the paper
**Playbook: P5 (one claim, stated once).**

| Line | Count |
|---|---|
| 42 (abstract) | "Across **36** controlled training runs" |
| 98 (intro) | "Across **24** training runs" |
| 377 (§4) | "applied to **24** training runs" |
| 862 (reproducibility) | "Per-run metrics for all **36** training runs" |

Both are defensible under different scopes (ABC = 24; ABC + T2 = 36), but the paper never says so,
and the abstract's "36 runs, targeting does not beat random" attributes the decisive comparison to
a set that includes arms not in it. With OR (6), FX (18), PC (3) and SE (40) the project total is
now **103 training runs** — a genuinely impressive number that the paper currently does not claim.

---

### F9 — Three competing noise bars are narrated in sequence
**Playbook: §4 content; P4.**

§4 (lines 401–425) walks the reader through the pre-registered pooled bar (0.0179), then the
T2-tightened pooled bar (0.0055, "3.24× tighter"), then the arm-specific Welch interval
([−0.0035, +0.0136]), with an explanation of why each supersedes the last and a paragraph on why
the asymmetry matters. It is correct and it is roughly 0.4 pp.

The strongest honest statement we have is the third one — it *excludes* the 0.0142 reference
improvement, which is more than "we could not have seen it." Lead with that; put the pooled-bar
arithmetic in the appendix behind one sentence. The current order asks the reader to learn two
instruments we then set aside.

---

### F10 — Numbers appear without the scale needed to read them

- Line 102: "at **126%** of the improvement the published approach reports" — the 0.0142 reference
  effect is never given a plain-language sentence saying what it is and where it came from.
- Line 476: "an order of magnitude above a **previously claimed 0.10**" — claimed by whom? (It is
  our own earlier estimate, refuted in C1, but nothing in the sentence says so; a reader will read
  it as a dig at a cited work.)
- Line 143: "$51.5\%$ of it lands on CAMO images, which are $24.8\%$ of the pool" appears in the
  contributions list on page 2, before the reader knows the target pool is a two-dataset mixture.

---

### F11 — §4.3 and §4.4 are causes presented as results
**Playbook: §6.**

"Cluster Structure of the Target Distribution" (§4.3) and "Uncertainty and Error-Type Ordering"
(§4.4) do not report outcomes of the intervention; they report *reasons the intervention could not
have worked*. Placed after the null and before the Discussion, they read as two more result
subsections, and the reader has no frame for them. Gathered into a single "Why it fails" section
with a stated causal chain, they become the most satisfying part of the paper — this is exactly
what ViT §4.3 does with the inductive-bias story.

The `\textbf{Transfers:}` tags that close these subsections are genuinely good and are the most
quotable material in the draft. They are currently distributed across four subsections where no
reader will assemble them; they belong gathered in §8.

---

## 3.3 What the draft already does well, and must survive the rewrite

Listed so the rewrite plan does not throw them away:

- **§4.1's opening** (lines 462–470) is the best writing in the paper: a near-paradox posed in
  plain words, then dismantled in four sentences with no notation. It is exactly P3 and P5. Use it
  as the tonal reference for the whole rewrite.
- **The `Transfers:` device.** Ending a result with what it means for someone who is not us is a
  device none of the three exemplars uses, and it is the paper's best answer to "why should a
  non-COD reader care." Keep it; gather the tags.
- **The concentration/direction distinction** is genuinely novel and correctly argued.
- **The contamination audit's self-discipline** — measuring for score inflation, not finding it,
  and refusing to write the quotable sentence — is the strongest single demonstration of the
  paper's methodological point, and it happens to be about *us*.
- **The withdrawal of our own candidate cause (A1)** and the correction of our own 10/76 bug are
  credibility we cannot buy any other way. Keep both, at one sentence each in the main text.
- **The α-collision note** flagged in `EXPERIMENTS_EXPLAINED.md` (`S_α`'s weighting parameter vs.
  the allocation temperature, both α) is real and still unfixed in the draft.

---
---

# PART 4 — Evidence-to-narrative map

Eighteen experiments. Role vocabulary: **motivation** (why the reader should care before we do
anything), **core** (a claim the paper stands on), **mechanism** (why the core result came out that
way), **control** (rules out an alternative explanation), **robustness** (shows a finding is not
an artifact of one choice), **infrastructure** (makes other results trustworthy but carries no
claim), **open risk**.

## 4.1 The map

| # | Exp | What it establishes | Role | Where it belongs | In `main_v2`? |
|---|---|---|---|---|---|
| 1 | **E0** | 48,365 inputs hashed; generator byte-reproducible at fixed seed; render depends on shard position; clustering moves 5.4% under a trivial preprocessing change | infrastructure; the 5.4% is a **scope constant** | 5.4% floor → §6; shard finding → Reproducibility stmt; rest → appendix | partly (5.4% in §4.3) |
| 2 | **D1** | The generator copies objects and paints backgrounds: interior Δ 5.6/9.6 grey levels vs exterior 70.8; render set is a **bijection** onto 4447 foregrounds; 0 of 8885 objects regenerated | **motivation + scope-setter** | §3 (what the pipeline is) and §6 (exhausted foreground supply) | yes, §5.1 only |
| 3 | **D2** | 41/76 CHAMELEON = re-encoded COD10K-train/CAMO training images; exact hash returns **0**; count saturates, 7.36× NN jump | **core (second headline)** | §7 ¶1–2 | yes, §5.2 |
| 4 | **D2_NC4K** | 0/4121 on NC4K at every tolerance; closest distance 3.44× the confirmation tolerance | **control** — makes D2 believable | §7 ¶2, one sentence | yes |
| 5 | **D2_reaudit** | Author-sourced release byte-identical 76/76; **measured for score inflation and found none** (percentiles 0.448–0.559, sign flips with mask release); two mask releases are different annotations (IoU 0.693) | **robustness + the paper's best honesty exhibit** | §7 ¶3; mask-release finding → appendix + 1 clause | yes, §5.2 |
| 6 | **D2_FINAL_AUDIT** | +9 rescale/crop copies confirmed by post-warp residual → **50/76 (65.8%)**, 16 unchecked, 10 clean | extension of core | §7 ¶1–2 | yes (as 50) |
| 7 | **B1** | Signal predicts MAE (ρ = +0.86) about twice as well as structural error (+0.43); best silhouette 0.1600 across three spaces; signal is **weaker where it is used** (−0.21 on the target pool) | **mechanism (causes 1 and 4)** | §6 | yes, §4.3/§4.4 |
| 8 | **C1** | Targeted vs random separates at held-out d ≈ 1.00–1.23 — **but the same-shape shuffle reproduces it** (+0.91 to +1.14); signal adds +0.0073 of a d over its own shuffle; targeting buys narrowness (eff-rank 0.53–0.64, 20/20), not reach | **CORE — the positive result** | §5 ¶1–3 + figure | yes, §4.1 |
| 9 | **A1** | Conditioning channel is **not** narrow (four routes, dominant one bypasses the summary, 0.907 vs 0.810); hypothesis **withdrawn** | honesty exhibit; **withdrawn cause** | §6, one sentence + appendix | yes, 1 clause in §5.1 |
| 10 | **A3** | Synthetic reaches 0.13–0.54 of the real target distribution; the generator's **own input photographs** reach 0.71–0.75; narrowing not displacement; **a JPEG re-save of identical images separates at 0.9928 AUC** | **mechanism (cause 5)** + a transferable methodological caution | §6; the AUC caution → §8 transfers | partly (appendix) |
| 11 | **ABC** | Δ(C10−B) `WITHIN NOISE` both architectures, both endpoints; pooled bar 0.0179 = 126% of the 0.0142 reference; budget pinned at 253/127 steps | **CORE — the null** | §4, table row 1 | yes, §4 |
| 12 | **T2** | With concentration held **exactly** fixed, 12/12 cells `WITHIN NOISE`; bar 3.24× tighter; CINV highest mean in 3 of 4 | **CORE control — the discriminating one** | §4 table + §5 | yes, §3.4/§4.1 |
| 13 | **T2C** | The pixel-over-structure ordering holds 8/8 across three independent signals × two architectures; **magnitude does not generalise** (ρ(1−`S_α`) reaches +0.56); boundary-band aggregation fails 2/8 | **robustness** — promotes a local quirk to a field-level caution | §6, one sentence + appendix table | yes, §4.4 |
| 14 | **AC** | Partialling object area **raises** ρ(1−`S_α`) in **8/8** rows — opposite of what the confound predicts; ordering survives 7/8 and 6/8 against a declared 6/8 floor (P ≈ 0.145, zero margin) | **control** against the most plausible confound | appendix + one clause in §6 | yes, §4.4 (over-detailed) |
| 15 | **PC** | Mean-teacher arm: Δ = +0.0197 at **3.3× its bar**, `DETECTED`; but PC's own bar (0.005954) exceeds the decisive gap (0.005034) | **control — instrument sensitivity** | §4, table row + one paragraph | yes, §4 |
| 16 | **OR** | Replace the score with the **true per-cluster test error**: 8/8 `WITHIN NOISE`, sign consistency 2/3 everywhere; score↔truth agree at only **ρ = +0.237** | **control — the strongest in the suite.** Converts "our score didn't help" into "no score could have" | §4, table row + one paragraph | **NO** |
| 17 | **FX** | Unpin the optimisation budget (253→341, 127→171): decisive gap `WITHIN NOISE` in 4/4 cells and **shrinks** from +0.0050 to +0.0014; two A0 comparisons come out `INCONCLUSIVE`, hinting that *padding* helps | **control — kills the strongest objection** | §4, table row + one paragraph; the A0 hint → §6 | **NO** |
| 18 | **SE** | Seed expansion to n = 8 on B, C10, CSHUF, CINV. **40/40 training runs complete; scoring was still in flight at the time of writing** (`se_resume.sh` live, `rebuild/ABC/out/se/` holds no `abc_verdict.json` yet). Projected bar ~0.0034 against a committed gap of 0.0050 | **OPEN RISK** | §4 | **NO** |
| 19 | **DIAG** | Welch interval on the two arms compared: **[−0.0035, +0.0136], excluding 0.0142**; 51.5% of budget → CAMO (24.8% of pool); only 20.5% of endpoint error variance between clusters; **boundary metrics resolve concentration at 1.37× bar and CINV captures it in full** | sharpens the core null; **demonstrates the thesis on accuracy** | §4 (interval), §5 (boundary), §6 (mixture) | yes, but boundary table is in the appendix |

## 4.2 The nulls, named explicitly

The paper contains **two nulls of different character plus one positive result**, and the rewrite
must keep them apart — the draft's own §5 says so and then blurs them by restating the split four
times in near-identical words.

**Null A — the headline, a bounded null.** The direction of the uncertainty signal moves trained
accuracy by nothing this design resolves. This is *not* "no effect." It is "no effect above a
stated size," and the size is now stateable three ways, of which the strongest is the Welch
interval [−0.0035, +0.0136], which **excludes** the 0.0142 improvement reported for this approach
while admitting effects up to about two-thirds of it. Defended from four directions — PC (the
instrument sees +0.0197 at 3.3× its bar), OR (a perfect score changes nothing), FX (removing the
dilution confound shrinks the gap), T2 (holding concentration exactly fixed, 12/12 within noise).

**Null B — a non-finding, reported as a refusal.** We expected contamination to inflate CHAMELEON
scores, measured it, and found nothing (all eight difficulty percentiles 0.448–0.559; the sign of
the clean-minus-leaked difference flips with the mask release). The pre-declared reading is what
stopped us writing the quotable sentence, so the claim became **non-independence, not inflation**.
This is the most persuasive thing in the paper about the authors' discipline, and it is currently
one paragraph deep inside a Discussion subsection.

**The positive result — not a null at all.** Concentration, not the uncertainty direction, produces
the separation that makes targeted selection look like it works (C1 geometry; T2 trained;
DIAG boundary metrics). The draft already states this without hedging in one place. **The rewrite
should lead with it** and use Null A as its scope, rather than the reverse. The title should follow.

## 4.3 How the exemplars handle negatives, mapped onto our material

| Exemplar move | Where it applies to us |
|---|---|
| **ViT §1 move 4** — volunteer the negative in the introduction, give it a mechanism, then bound it ("This seemingly discouraging outcome may be expected: Transformers lack...") | The whole paper's shape. Our mechanism chain (weak clustering → 20% between-cluster variance → budget goes to CAMO → signal points at pixel error → generator copies objects) is the direct analogue of ViT's inductive-bias story. |
| **ViT §4.2** — concede in one sentence, point at the controlled study | Every objection in §4. "The schedule was pinned" → FX. "Maybe the score was bad" → OR. "Three seeds" → SE. Replaces ~1 page of hedging with ~4 sentences and a table. |
| **ViT §4.4** — "This result is somewhat surprising, since one might expect..." | The monotone A0<A2<B≈C10 ordering, and the FX finding that growing the budget by 35% made *every* arm slightly worse. Both point away from us; both are more interesting stated as surprises than as confessions. |
| **ViT §4.6** — one paragraph, last, for the weakest thing, shortfall as a plain number | A1's withdrawal. And SE, if it lands too late for a full treatment. |
| **CamoDiffusion on HitNet** — name the confound in the same clause as the claim | The A2 confound (it pairs the authors' original photographs with our stems), and the 22.2% pseudo-label variance. One clause each, not a paragraph. |
| **BiRefNet §3.6** — a subsection of practical findings that reports a cost honestly and then gives the cheaper alternative | The `Transfers:` material, gathered: the three checks that cost no training and should precede any cluster-wise allocation. |
| **BiRefNet — the anti-exemplar** | It has no limitations section and spends the space on applications. Our paper cannot and should not imitate this; noted only so the rewrite does not read BiRefNet's confidence as a licence to drop scope statements. |

---
---

# PART 5 — Proposed page budget for 9 pages

## 5.1 The budget

| § | Section | Pages | Now | Δ | Visual anchors |
|---|---|---|---|---|---|
| — | Title + abstract | 0.3 | 0.55 | −0.25 | — |
| 1 | Introduction | 1.2 | 1.6 | −0.4 | — |
| 2 | Background and related work | 0.9 | 1.35 | −0.45 | — |
| 3 | The loop we built | 1.4 | 1.55 | −0.15 | **Fig. 1 — arm diagram (new)** |
| 4 | Does targeting beat random? | 1.8 | ~1.2 | **+0.6** | **Tab. 1 — every trained comparison** |
| 5 | Concentration, not targeting | 1.4 | ~1.3 | +0.1 | **Fig. 2 — `fig1_thesis`**; **Tab. 2 — boundary (promoted)** |
| 6 | Why it fails | 0.7 | ~1.3 | −0.6 | — |
| 7 | CHAMELEON is mostly training data | 0.9 | 3.0 | **−2.1** | **Fig. 3 — confirmed pairs (promoted)** |
| 8 | Discussion and conclusion | 0.4 | 0.9 | −0.5 | — |
| | **Main text total** | **9.0** | **11.85** | **−2.85** | 2 tables + 3 figures |
| — | Statements (AI use / ethics / reproducibility) | 1.0 | 1.0 | 0 | excluded from limit |
| — | References + appendices | — | 15 | grows | absorbs everything cut |

Visual density after the change: **2 tables + 3 figures in 9 pages.** Still below ViT (2+7) and
CamoDiffusion (2+6), but roughly triple the current draft and enough to break up the prose.

## 5.2 Where the 2.85 pages come from

| Cut | Saves | Goes to |
|---|---|---|
| §7 contamination: 8 paragraphs → 3 + figure (tolerance sweep, 7.36× jump, CAMO-250 triple, mask-release IoU, inlier operating point, the excluded tenth candidate and its shear decomposition) | **2.1** | Appendix F/G, already partly written |
| `tab:closest` comparison table out of §2, replaced by two sentences (ViT places no comparison table in related work) | **0.35** | Appendix A |
| §4: three competing noise bars → one headline interval + one sentence | **0.4** | Appendix D |
| §1: 1151 words → ≤ 650; five contribution paragraphs → four one-line items | **0.4** | — |
| §5.1 limitations → absorbed into §6 as a causal chain; pre-registration provenance apparatus → Reproducibility statement | **0.3** | Appendix B + statements |
| §4.4's area-control detail (pass counts, the P ≈ 0.145 margin, the covariate discussion) → one clause | **0.25** | Appendix C, already written |
| Removal of duplicated `% 5. DISCUSSION` marker and the orphan paragraph at lines 454–456 | 0.05 | deleted |
| | **≈ 3.85** | |

## 5.3 Where it goes back

| Spend | Costs |
|---|---|
| §4: OR, FX and SE — three paragraphs and three table rows | **0.6** |
| §2: the background block defining `S_α`, arm, seed, endpoint, the reference effect | **0.3** |
| §3: Fig. 1, the arm diagram | **0.25** |
| §5: `tab:boundary` promoted from Appendix E | **0.25** |
| §7: `fig:chamext` / `fig:pairs` promoted from the appendix | **0.3** |
| | **≈ 1.7** |

Net: −3.85 + 1.7 = **−2.15** against a required −2.85. **The remaining ~0.7 pp. has to come from
line-level compression**, and the numeric-density measurement in the header says where: bringing
abstract+intro from 132 numbers/1000 words to the exemplars' ~45 removes roughly 100 numbers and
the clauses carrying them, which is worth about half a page on its own. §6 and §8 carry most of the
rest.

## 5.4 Order-of-work note for the planning prompt

Two items gate the rewrite and should be settled before prose is drafted:

1. **SE.** All 40 training runs are complete; scoring was still in flight at the time of writing
   (`se_resume.sh` running, no `abc_verdict.json` in `rebuild/ABC/out/se/`), so no SE number
   exists yet. The projected bar (~0.0034) is **below** the committed decisive gap
   (0.0050). SE's own pre-registration states the consequence plainly: *"if the gap holds and the
   bar tightens as projected, SE returns a `REAL EFFECT` and the committed null becomes a power
   failure that must be reported as one."* §4 and the title cannot be finalised until SE lands. The
   rewrite can proceed on every other section in the meantime — §2, §3, §6, §7 and §8 are
   SE-independent — and §4 should be planned with both branches written out.
2. **The ICLR 2027 page rules.** The 9-page budget above assumes ethics and reproducibility
   statements sit outside the limit, as they normally do at ICLR. Worth confirming against the 2027
   CFP, since it changes the budget by a full page.

## 5.5 Consistency items to fix during the rewrite

Small, mechanical, and each one is a thing a reviewer can catch:

- **Run counts.** Abstract says 36, intro and §4 say 24, reproducibility says 36. Pick a scope per
  sentence and say which. The project total is now 103 trained runs (ABC 24, T2 12, PC 3, OR 6,
  FX 18, SE 40) — a number worth claiming once, accurately.
- **The pinned-budget concession.** §5.1 lines 645–652 call it "the largest open question this
  paper creates." FX closed it. Delete and replace with the measurement.
- **The contamination count.** `main_v2` says 50/76; `EXPERIMENTS_EXPLAINED.md` §18 (DIAG) still
  says 51/76. `CONTAMINATION_LEDGER.md` adjudicates: **50 is final**, and 51 was two unrelated
  quantities sharing an integer. The ledger's own warning — that cross-reading makes the audit
  trail look self-contradictory when it is not — applies to a reviewer reading our supplement.
  One number, everywhere.
- **The α collision.** `S_α`'s weighting parameter (0.5) and the allocation temperature (1.0) are
  both written α. Flagged in `EXPERIMENTS_EXPLAINED.md`, still unfixed in §3.2.
- **"a previously claimed 0.10"** (line 476) reads as a criticism of a cited work. It is our own
  earlier estimate. Say so.
- **`\fix` and `\new` margin macros** are defined at lines 24–25 and should not survive to
  submission.
- **Author-facing `% AUTHORS:` comments** remain in the AI Use, Ethics and Reproducibility
  statements. Each asks for a confirmation that has not been recorded as made.

---
---

# PART 6 — Summary of the argument

The draft's content is empirically correct and, in places, unusually well written — §4.1's opening
and the `Transfers:` device are better than anything in the three exemplars at the same job. What
is wrong is structural and it is four things:

1. **The paper leads with its null and treats its positive result as a control.** Every exemplar
   leads with the thing it found. Ours found something: concentration, not direction, is what makes
   a targeted training set different — and we demonstrate it on geometry *and* on trained accuracy.
   The null is the scope of that finding, not the headline.
2. **It never onboards.** `S_α` — the quantity every verdict in the paper is measured in — is never
   defined in the main text. Six other terms are used in the abstract or introduction and defined
   three to six pages later. CamoDiffusion spends 0.7 pp. teaching diffusion models it did not
   invent; BiRefNet defines S-measure for an audience that knows it. One labelled background block
   fixes this.
3. **It reports at results density everywhere.** 132 numbers per 1000 words in the abstract and
   introduction, against 41–52 for all three exemplars; 105 in the conclusion against 0–13. The
   fix is mechanical: absolutes go in tables, prose carries relative quantities and shapes, each
   number appears once.
4. **It is three experiments out of date, and they are the three that defend it.** OR, FX and SE
   answer the three standard objections to a null and none of them appears in the main text, while
   §5.1 still concedes in bold a weakness FX has measured and closed.

The page budget follows from the diagnosis rather than driving it: the contamination section alone
is 3.0 pp. for a result whose essential content is three paragraphs and a figure, and that single
cut plus the density correction funds everything the paper is missing.


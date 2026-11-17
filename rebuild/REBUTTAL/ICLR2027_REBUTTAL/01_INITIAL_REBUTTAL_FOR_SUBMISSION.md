# Initial Response to Reviewer dypE

We thank the reviewer for the constructive assessment and for recognizing our controls and CHAMELEON audit. We agree the null requires qualification.

### CW-01: Statistical sensitivity
**Reviewer Concern (verbatim excerpt):** “However, they do not fully rule out smaller gains.”

**Response:** Agreed. Our pre-registered threshold of twice the pooled *per-run standard deviation* plus seed-wise sign agreement is a conservative decision rule, **not** a confidence bound or proof of no effect (Methods; Appendix “Decisive Gap”). For eight-seed SINet/COD10K, C10–B = +0.0024, with post-hoc 95% CI [−0.0020, +0.0067]. This excludes the reproduced reference improvement (+0.0142), but admits smaller positive gains. At ±0.005, post-hoc equivalence of C10 and B is **not** established (p = 0.101). Injected images are 18.4% of the pool; about 48% differ between arms, yielding roughly 8.8% total-pool contrast. We will make these qualifications prominent and examine paired-seed sensitivity and realized data exposure without assuming their outcomes.

### CW-02: Concentration versus downstream performance
**Reviewer Concern (verbatim excerpt):** “However, this does not mean that concentration improves detection performance.”

**Response:** We agree. Dataset distinguishability and embedding geometry show that **concentration changes the selected data**, not that it universally improves detection. Same-shape shuffle (CSHUF) and reversed-ranking (CINV) controls do not establish an uncertainty-direction benefit in downstream S-measure. On post-hoc SINet boundary metrics, C10–B and CINV–B reach approximately 1.37× and 1.34× their bars, respectively; SINet-v2 shows no comparably resolved effect. We will explicitly separate geometric from downstream claims, test architecture-dependent contrasts, and label all boundary analyses exploratory. The fixed offline LAKE-RED pool reuses foregrounds, so our null does **not** generalize to adaptive generation or novel foreground synthesis; we will audit diversity and state this boundary explicitly.

### QA-01: Smaller meaningful improvements and pairing
**Reviewer Concern (verbatim excerpt):** “Could the authors clarify what level of improvement they consider meaningful for COD? Also, could they provide a paired analysis using the same random seeds?”

**Response:** +0.0142 is a *reproduced, study-specific reference effect*, not a universal minimum meaningful COD improvement. The ±0.005 margin is exploratory, not a validated practical-significance threshold. We will report uncertainty against both scales and compute matched-seed C10–B differences, paired CIs, and paired equivalence tests from the existing eight-seed runs (seeds 42, 43, 45–50), after checking run manifests. Smaller useful gains cannot currently be excluded.

### QA-02: Limited contrast and foreground diversity
**Reviewer Concern (verbatim excerpt):** “Would the same conclusion hold if the training sets had larger differences or if the generator could produce more diverse foreground content?”

**Response:** That remains untested. Shared base images and substantial injection overlap attenuate the contrast (Appendix “How much the trained comparison is attenuated”); the background-only, fixed-pool generator limits content diversity (Section “Why It Fails”). We will quantify realized per-seed overlap and exposure, preflight larger matched-budget allocations to ensure they truly increase between-arm differences, and analyze coverage conditional on foreground identity. We will attempt controlled training where feasible. Without a genuine new-foreground capability, we will report adaptive/diverse foreground generation as an open limitation, not imply it has been evaluated.

### QA-03: Protocol consequences of CHAMELEON overlap
**Reviewer Concern (verbatim excerpt):** “In particular, it would be useful to distinguish between supervised training, unlabeled target-domain adaptation, and checkpoint selection.”

**Response:** We confirm at least 50/76 CHAMELEON photographs in COD10K/CAMO training pools (44 in COD10K-train): 41 re-encodes and nine geometrically verified copies despite zero exact-hash training matches (Section “CHAMELEON Is Mostly Training Data”; Appendix “CHAMELEON Contamination”). **Supervised overlap** violates independent-image evaluation; **unlabeled adaptation** can expose the model to test photographs without using test labels, so its consequences depend on the protocol; **checkpoint selection** on overlapping validation images introduces a separate selection path (the appendix documents CAMO-250 matches). This finding does **not** demonstrate score inflation, which our difficulty analysis did not show. We will audit exposure by protocol, distinguish 16 unchecked cases, disclose mask-release sensitivity, and favor COD10K-test/NC4K.

We will report inconclusive outcomes alongside any additional findings.

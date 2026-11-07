# REVISION_DIFFS.md — revision 1, as before/after text

Base: `AD-PCHG-250926_Final.tex` (submitted). **Diffs only: the paper's .tex is not edited
here.** Every "after" number cites the log block it comes from. "Post-hoc" is kept wherever
the number is post-hoc. Line numbers refer to the base file. Dated 2026-11-07, written
after EXP REBUTTAL_STATS, REBUTTAL_CONTAM, REBUTTAL_PREREG_PROVENANCE and the three EXP DIAG
blocks.

**What changed against the plan's D1–D11:** the eight-seed boundary re-score (EXP
REBUTTAL_STATS `bnd8_*`) does **not** reproduce the SINet boundary effect. C10−B Boundary IoU
is +0.0046 (0.30× bar, 5/8), down from +0.0138 (1.37×, 3/3) at three seeds. So the
abstract's boundary clause and the §3.2 "strongest form of the result" paragraph are
**withdrawn**, not merely qualified (D1, D5b). This is the largest change in the revision.

---

### D1 — Abstract (l.48)
**Before:** "…targeted training sets are measurably different from random sets, but the difference is explained by concentrating the generation budget rather than by where uncertainty is concentrated, as every concentration rule we test reproduces the effect and, on boundary accuracy, so does aiming at the clusters the model was most certain about."

**After:** "…targeted training sets are measurably different from random sets, and that difference is explained by concentrating the generation budget, not by where it points: every concentration rule we test reproduces it. On trained accuracy we find no evidence that targeting helps, and we bound its benefit over random allocation at +0.0067 S_α on the primary cell."

*Source:* EXP REBUTTAL_STATS `rule_out_sentence_X`. The boundary clause is removed because the eight-seed re-score does not support it (`bnd8_SINet_boundary_iou_C10-B`).

### D2 — Abstract, last sentence
**Before:** "…budget concentration, not uncertainty-based targeting, accounts for the observed training-set effects."
**After:** "…budget concentration, not uncertainty-based targeting, accounts for the observed separation between training sets, in a LAKE-RED, background-only, fixed-foreground setting on the SINet family."

### D3 — Contribution 2 (l.81)
**Before:** "\textit{A bounded null on the direction}, defended by five independent controls: …"
**After:** "\textit{A bounded null.} Targeting does not beat random allocation: on the primary cell, benefits above +0.0067 S_α are ruled out (95% CI). Equivalence at ±0.005 holds for the same-shape direction contrast (TOST p = 0.019) but not for targeted-versus-random (p = 0.10). The null is defended by five independent controls: …"
*Source:* EXP REBUTTAL_STATS (`SINet_COD10K_C10-B`, `SINet_COD10K_C10-CSHUF`); Table 6.

### D4 — §3.2 opener (l.328–332)
**Before:** "…The geometry of the selected set shows it; trained accuracy at eight seeds is consistent with it, and the one family of metrics on which concentration is large enough to resolve supports it, post hoc and on one architecture."
**After:** "…The geometry of the selected set shows it, and that much is established. Whether concentration also explains downstream accuracy is not: on trained S_α at eight seeds neither concentration nor direction is resolved, and a three-seed boundary-metric effect on SINet did not survive re-scoring at eight seeds (below)."

### D5a — §3.2 TOST paragraph (l.355–359): add after "…targeting against random is not ($p = 0.101$)."
"C10−B mixes concentration with direction, so a small concentration effect would sit exactly there. It is the one gap the eight-seed design cannot close: its minimum detectable effect at 80% power is 0.0059 [EXP REBUTTAL_STATS `MDE80_SINet_COD10K_C10-B`]. Two contrasts outside the frozen gap set have post-hoc intervals that exclude zero on SINet: the anti-targeted arm against random (CINV−B, +0.0045, [+0.0015, +0.0074]) and destroyed against reversed direction (CSHUF−CINV, paired [−0.0044, −0.0004]). Both are unadjusted, one architecture, and inside their 2σ̂ bars."
*Source:* EXP REBUTTAL_STATS `SINet_COD10K_CINV-B`, `SINet_COD10K_CSHUF-CINV`, `intervals_excluding_zero`.

### D5b — §3.2 boundary paragraph (l.361–366): **replace whole paragraph**
**Before:** "The acquisition signal … Re-scoring every run's committed predictions with two boundary metrics closes that gap (Table~\ref{tab:boundary}), and on SINet, the concentration effect finally clears its bar. So does the anti-targeted arm, at $1.34\times$ against targeted selection's $1.37\times$ … \textit{This is the strongest form of the result we have}, because …"

**After:** "The acquisition signal of Equation~\ref{eq:es} is boundary-focused, but S_α is not, so we re-scored every run's predictions with two boundary metrics (post-hoc). At three seeds, SINet's concentration gap cleared its bar on Boundary IoU (C10−B 1.37×, CINV−B 1.34×, Table~\ref{tab:boundary}). **At eight seeds it does not:** C10−B is +0.0046 (0.30× its bar, 5/8 seeds) and CINV−B +0.0098 (0.64×), and SINet-v2 resolves nothing at either seed count. At eight seeds the direction contrasts stay far inside their bars on every metric and both architectures (at most 0.37×). We therefore do not claim a downstream effect of concentration on any metric. What survives is weaker but still informative: no metric we tried shows direction mattering."
*Source:* EXP REBUTTAL_STATS `bnd8_*` (8 seeds); EXP DIAG (boundary part) for the 3-seed values.

### D6 — Table 3 caption (`table_subgroup_metrics.tex`)
Add: "**Three seeds.** At eight seeds none of these gaps clears its bar (Appendix~\ref{app:diag}, new eight-seed table); this table is kept to show what the three-seed reading was."
Add an eight-seed version to Appendix D from `rebuild/REBUTTAL/out/ws1_boundary8.csv`.

### D7 — Discussion: new scope paragraph (after l.475)
"\paragraph{Scope.} Everything here is measured inside one protocol: LAKE-RED, which varies only the background, over a fixed pool of 4,447 HKU-IS foregrounds, under S2R-COD's synthetic-source, unlabelled-target adaptation, on two ResNet-family detectors (SINet, SINet-v2). The null concerns the allocation layer inside that protocol, meaning which 1,000 synthetic images to add. It says nothing about generators that vary the foreground, such as RealCamo or CamDiff, or about modern backbones (PVTv2, DINOv2), which we did not test."

### D8 — App. C, effective contrast (l.838–840) — **P3**
**Before:** "…and only about $48\%$ of injected images differ between any two arms, giving an effective contrast near $8.8\%$."
**After:** "…and between C10 and random, 76.7% of injected images differ (overlap at chance, 209–246 of 1,000 across the eight seeds), giving an effective contrast of 14.1% of the pool. Between C-family arms 45–51% differ, giving 8.3–9.4%. That figure applies to the direction contrasts, not to targeted-versus-random."
*Source:* EXP REBUTTAL_STATS `overlap_B_C10_per_seed`, `effective_contrast_C10-B`, `effective_contrast_C_family`.

### D9 — App. B, pre-registration commits (l.732–737) — **P1** (wording per REBUTTAL_PLAN Addendum 1 A1)
**Before:** "…the seed expansion's at \texttt{b755aa9}, dated 2026-09-18. The oracle and optimization schedule campaigns carry their own pre-registrations, each committed before that campaign's first training run."
**After:** "Our repository history records that the pre-registrations for the seed expansion, the oracle and the unpinned schedule were committed together at \texttt{a79886a} (18 Sept 2026, 11:48 IST). A later history rewrite re-committed them unchanged as \texttt{28cfd84}, and the original commit is preserved under a tag. The schedule and seed-expansion campaigns began after that commit. The oracle campaign's first runs began about an hour earlier, at 10:46, before any oracle result existed (the first endpoint-derived number dates from 16:51). Its verdict rule is the four-arm rule frozen at \texttt{065dac6}, unchanged. Its arm, its two gaps and the arms its noise estimate pools over were new."
*Source:* EXP REBUTTAL_PREREG_PROVENANCE.

### D10 — AI-use statement (l.516–522)
The P2 EXP DIAG blocks now exist, so the traceability sentence can stand with one precise edit:
**Before:** "…every number is emitted by a committed script and is traceable to a log block, and no result was transcribed by hand. The decision rules … were pre-registered before the runs they govern …"
**After:** "…every number is emitted by a committed script and is traceable to a log block (for the post-hoc diagnostics, blocks added during the discussion period, dated 2026-11), and no result was transcribed by hand. The decision rules … were pre-registered before the runs they govern, with the one timing exception stated in Appendix~\ref{app:method} …"
**Add:** "During the discussion period, generative AI tools were also used to draft the post-hoc statistics, contamination and provenance scripts, the allocation code for the additional oracle arms, the campaign drivers, and the response text. All outputs are committed, and every new number is emitted by a committed script into a dated log block."

### D11 — new main-text table, §3.1 (≈⅓ page)
"Failed to detect vs evidence of equivalence", post-hoc. One row per C10−B and C10−CSHUF cell; columns: 2σ̂ verdict, equivalent at 0.005 (Welch/paired), equivalent at 0.0071 (Welch/paired), δ_min. From `rebuild/REBUTTAL/out/ws1_intervals.csv`. Caption carries: "0.0071 is half the method's own gain and was the pre-registered sensitivity target, not a declared equivalence margin."

### D12 — App. D sweep sentence (l.829–834)
**Before:** "…while the two direction contrasts never exceed $0.52\times$ and $0.14\times$ anywhere in the sweep."
**After:** "…while the two direction contrasts reach at most $0.51\times$ and $0.15\times$ anywhere in the sweep." Then append: "These are three-seed values; at eight seeds the concentration gaps no longer clear their bars (§3.2)."
*Source:* EXP DIAG (boundary part): `sweep_C10-CSHUF_max_ratio` 0.5050, `sweep_C10-CINV_max_ratio` 0.1432. The paper's "0.52×" is not reproduced, and "never exceeds 0.14×" is strictly exceeded by 0.143.

### D13 — App. F adjudication table, animal-72 row
**Before:** scale "$6.36$". **After:** "$6.36/6.38$". (EXP REBUTTAL_CONTAM `paper_scale_display_omissions`.)

### D14 — App. F: contamination by protocol (new short table, dypE Q3)
From `rebuild/REBUTTAL/out/ws3_protocol_table.csv` (EXP REBUTTAL_CONTAM): supervised standard split 50/76 (44 COD10K-train + 6 CAMO-train); S2R-COD target as described 44/76; released 4040-image target 50/76; checkpoint selection 3/76 byte-identical to CAMO-250 (animal-17 and animal-60 also Tier A; animal-25 otherwise clean). Caption: "Non-independence, not a measured score inflation."
**Also fix §3.4 footnote (l.452):** "the target pool, which holds the same $44$" → "the target pool, which holds the same 44 under the protocol as described, and all 50 under the released 4,040-image pool".

### D15 — Literature/anchor table (App., one main-text sentence), RL5B
Rows (each with backbone and label usage): S2R-COD published S2C (SINet 0.6418/0.6984/0.7136, SINet-v2 0.6466/0.6485/0.6845; external); our same-code anchors with campaign labels (MT 0.6988, three seeds, EXP PC; B 0.7151 and C10 0.7175, eight-seed means, EXP SE; SUP pending WS4); RISE 0.763/0.790 (DINOv2 ViT-L/14, unsupervised; external); supervised SINet 0.771 (ResNet-50, full masks; external, SINet CVPR'20). **SINet-v2 0.815 and UCOD-DPL enter only after a manual check against their PDFs** (REBUTTAL_PLAN Phase 0 (i)).

---

**Page budget (10 pages):** D11 ≈ ⅓ page; D7 ≈ ¼; D5a/D5b net ≈ +⅛ (D5b shortens); D1–D4 ≈ 0. All other items are appendix. Title unchanged (locked by the Author Guide until 18 Nov).

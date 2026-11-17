# 01 — Reviewer traceability matrix

## How to read this

- **Issue IDs** follow each review's own order: CW = Critical Weakness, Q = Question for Authors.
- **Evidence status** uses the definitions in `03_EXPERIMENT_EVIDENCE_AUDIT.md`.
- **Colour:**
  - A = RL5B, blue
  - B = Caus, teal
  - C = dypE, purple
  - S = shared, orange
- **Locations** use the numbering of the compiled revision, checked by `tools/check_locators.py`.
- **Overlaps were found by meaning, not keywords:**
  - RL5B-CW1/Q1 ≡ dypE-CW1/Q1 (equivalence vs. non-detection): one shared table.
  - RL5B-CW2/Q2 ≡ dypE-CW2 (concentration vs. downstream): one shared treatment.
  - RL5B-CW4/Q4 ≡ Caus-CW2/CW3/Q2 ≡ dypE-CW2 (generator) and dypE-Q2 (diversity): one shared Scope paragraph.

| Issue | Concern (short) | Posted commitment (8 Nov) | Verified new evidence (status) | Manuscript change | Colour | Location | Reply pointer |
|---|---|---|---|---|---|---|---|
| **RL5B-CW1 / Q1** | CI [−0.0020, +0.0067] does not show equivalence | reword claims; a main-text CI/TOST table; a pre-registered confirmatory campaign | EQ: H1 equivalent (p = 0.015), H1b neither; INCOMPLETE 16/15/15 of 27 (**PARTIAL**). TH01 power corrected to 0.20 / 0.0087 (**VERIFIED**) | **Headline**: Table 3 with the 8-seed Welch and paired rows and the confirmatory rows; definitions in §3.1; abstract, intro, contributions, conclusion; the 16-contrast table moved to App. C | S | Table 3 (§3.1); Table 9 (App. C); App. C (EQ design) | RL5B comment 1, CW-01 |
| **RL5B-CW2 / Q2** | concentration explains the distribution, not accuracy | restate claim tiers; dose-response with SINet-v2 replication; boundary re-score | CDR not supported (**PARTIAL**: SINet only). Boundary at 8 seeds: 0.30× / 0.64× (**VERIFIED**; contradicts the posted 1.37× / 1.34×) | §3.2 heading and three claim tiers; CDR verdict; boundary claim withdrawn; one exploratory CINV−B sentence (constraint 7) | S | §3.2; Table 7, Table 8 (App. C) | RL5B comment 1, CW-02 |
| **RL5B-CW3 / Q3** | absolute gap to RISE and supervised SINet-v2 | RISE in related work; protocol table; supervised training; re-score; decomposition; higher operating point | E3-a/c/d/f done (**PARTIAL**: E3-b and E3-e not run; EXP-04 not run). RISE description corrected | RISE sentence in §1.1; App. A paragraph, gap paragraph, Table 4 (0.717 rounding fixed); E-measure variant | A | §1.1; Table 4 (App. A) | RL5B comment 2, CW-03 |
| **RL5B-CW4 / Q4** | fixed generator and pool limit generality | scope statements in title, abstract and conclusion; quantify reuse, ICC and distances | AN03: reuse 1000/1000, ICC 0.71, 52/75 clusters (**VERIFIED**). Title change not possible during discussion | Scope paragraph (§4); abstract, intro, conclusion; camera-ready title proposed in the general response | S | §4 Scope; App. E | RL5B comment 2, CW-04 and Title |
| **Caus-CW1** | probe result is only a sanity check; limited contribution | sharpen the distinction; emphasise CHAMELEON as a separate contribution | AN-02: reproduction exact; flat quota d = 0.52; rank not set by concentration (**VERIFIED**; contradicts "concentration the whole time") | Central claim now "matching and concentration" (author Q1) in abstract, intro, §3.2, §3.3, discussion, conclusion; Fig. 2 caption; App. I paragraph | B | §3.2; App. I | Caus comment 1, CW-01 |
| **Caus-CW2** | conclusions bounded to LAKE-RED / SINet | narrow abstract, claims and conclusion; assess a modern detector if feasible | Scoping done. Modern detector **UNRESOLVED (blocked)**. EQ adds equivalence within scope | Shared Scope paragraph; teal sentence "a modern transformer-based detector is untested" | S + B | §4; Table 3 | Caus comment 2, CW-02 |
| **Caus-CW3** | fixed foreground cut-outs narrow the distribution | verify provenance and coverage; compare with a foreground-varying generator if available | Provenance 8,885 / 0 regenerated; coverage at every k (**VERIFIED**). Generator **UNRESOLVED (blocked)** | §3.3 "k-NN recall at k = 5; lower than input at every k"; App. E k-dependence; Scope | B | §3.3; App. E | Caus comment 2, CW-03 |
| **Caus-Q1** | oracle with a different shape? | evaluate error-proportional and top-error allocations with controls | ORS: 4 pre-registered contrasts within noise on both endpoints (**VERIFIED**) | **Headline**: Table 2 rows ORS; §3.1 sentences; new App. I; "no score of any quality" scoped; pre-registration timing corrected (App. B, statements) | B (S for the scoped oracle sentence) | Table 2 (§3.1); App. I; App. B | Caus comment 1, Q1 |
| **Caus-Q2** | replicate with a modern backbone and a foreground-varying generator; scope the claim | assess both if code, licences and compute allow; scope regardless | Neither run (**UNRESOLVED, blocked**); scoping done | Scope paragraph; limitations stated | S + B | §4 | Caus comment 2, Q2 |
| **dypE-CW1** | small gains not excluded; 8.8% contrast; 2σ̂ is conservative | make the qualifications prominent; paired sensitivity; realised exposure | Paired analysis (**VERIFIED**); EQ equivalence on the primary cell (**PARTIAL**); 77% / 14.1% (**VERIFIED**; contradicts the posted 8.8%) | **Headline**: shared Table 3 (Welch, paired, confirmatory); pairing sentence §3.1; Table 10; App. C attenuation paragraph | S (+ C for pairing, Table 10, App. C) | Table 3 (§3.1); Table 10, App. C | dypE comment 1, CW-01 and Q2 (part) |
| **dypE-CW2** | concentration ≠ performance; architecture dependence; fixed pool | separate geometry from downstream; test the interaction; label boundary results exploratory | 8-seed boundary and interaction not resolved; Holm across 140 (**VERIFIED**); CDR not supported (**PARTIAL**) | §3.2 boundary paragraph with the interaction clause; App. C paragraph "Architecture, multiplicity and domain mix"; Scope | S (+ C for the interaction) | §3.2; Table 8 (App. C) | dypE comment 2, CW-02 |
| **dypE-Q1** | what improvement is meaningful; paired analysis | report against both scales; paired CIs and TOST | **VERIFIED** (Table 10); EQ (**PARTIAL**) | Table 3; Table 10; §3.1 scale sentence | S + C | Table 3; Table 10 | dypE comment 1, CW-01 / Q1 |
| **dypE-Q2** | larger differences or more diverse foregrounds? | quantify overlap; preflight larger budgets; coverage | Preflight fails at 1.22× (**VERIFIED**); selection coverage (**VERIFIED**); new-foreground generator **UNRESOLVED** | Discussion clause; App. C preflight sentences; App. E selection coverage; Scope | C (S for Scope) | §4; App. C; App. E | dypE comment 2, Q2 |
| **dypE-Q3** | CHAMELEON consequences by protocol | audit exposure by protocol; resolve the 16 unchecked; mask releases | 32 COD10K-test, 4 CAMO-250, 74/76 duplicated somewhere, protocol matrix (**VERIFIED**); animal-54 not claimed (withdrawn unadjudicated, `73c18d6`); 7 COD10K-test byte-identical training images (author decision Q2) | §3.4 sentences; App. F: CAMO-250 fourth, COD10K-test, Table 17, protocol paragraph, "no duplicate found" | C | §3.4; Table 17 (App. F) | dypE comment 2, Q3 |
| General | colour legend, central claim, title, corrections | — | — | Appendix colour legend (marked build only) | — | App. start | `GENERAL_RESPONSE.md` |

## Constraint checklist (`AUTHOR_REVISION_CONSTRAINTS.md`)

| # | Author decision | Where it is implemented |
|---|---|---|
| 1 | Central claim stated the same way in abstract, intro, contributions and conclusion | Abstract, §1 paragraphs 3–4 and the contribution bullets, §5. "Matching and" was added by author decision Q1 (2026-11-17). |
| 2 | Title unchanged; camera-ready retitle stated | Title untouched; proposal given in `GENERAL_RESPONSE.md` and the RL5B reply (comment 2). The Caus reply points to it. |
| 3 | EQ pre-registered and INCOMPLETE, 46/81; H1 and H1b numbers; 16/15/15; exploratory checks only in the appendix | Table 3 caption, §3.1, §5, App. C. "15 per arm" appears nowhere (grep). |
| 4 | CDR "not supported"; concentration claims restricted; SINet-v2 not run | §3.2 heading and verdict (pre-registered sentence), Table 7, abstract, §5 |
| 5 | Withdraw "strongest form" and the 3-seed boundary statements | §3.2 rewritten; the 3-seed ratios appear only as superseded history in Table 8 and the App. C sweep |
| 6 | CHAMELEON at least 50/76 automated; animal-54 makes 51; COD10K-test re-encodes new; counts reconciled | Abstract, intro, conclusion ("at least 50"); §3.4; App. F; Table 17; this repo's report 03 §3. **The animal-54 part is overridden** (author, 2026-11-17 evening: evidence overrides the constraint; the Caus package withdrew the match unadjudicated in `73c18d6`), so the paper and replies report the released detectors' 50/76 and 74/76 |
| 7 | CINV−B: one main-text sentence, exploratory, with multiplicity status | §3.2 (unadjusted only, Holm-adjusted p = 0.79); App. C details |
| 8 | Pre-registration timing corrected to the git evidence | App. B commit paragraph; AI-use and reproducibility statements; App. H oracle paragraph |
| 9 | Every correction stated as "we stated X; correct is Y" | RL5B: 0.14, 0.008, σ̂, n, sign rule, 1.37/1.34, RISE, title. Caus: k-NN k, "depend on architecture", oracle wording, timing. dypE: 8.8%, 1.37/1.34, 16 unchecked, three CAMO-250, 50 |
| 10 | At most 5,000 characters per comment, at most 2 comments per reviewer | `tools/count_chars.py`: RL5B 4711 / 3609; Caus 4161 / 3548; dypE 3376 / 3814; general 4527 |
| 11 | Delivery order | tex/bib, then replies, then GENERAL_RESPONSE, then reports, all delivered before the deadline |

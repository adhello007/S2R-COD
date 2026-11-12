#!/usr/bin/env python
"""Write RESULT_TABLES/DOC-01_claim_evidence_map.csv: manuscript claim -> status after review -> evidence."""
import argparse
import csv
import os

ap = argparse.ArgumentParser()
ap.add_argument('--sr', required=True)
a = ap.parse_args()

R = [
    # id, label, manuscript claim (abridged), status, post-review evidence, proposed action (DOC-01 edit)
    ('C1', 'abstract; sec:null; tab:trained', 'Targeting does not beat random; 8-seed gap +0.0024, 0.34x bar, WITHIN NOISE',
     'SUPPORTED (reproduced exactly)', 'AN-01_original_vs_recomputed.csv; TH-01_paired_inference.csv', 'keep; add bound (Edits 1, 3, 9)'),
    ('C2', 'sec:null', 'Post-hoc interval [-0.0020, +0.0067] excludes the reference effect',
     'SUPPORTED; interval is Welch; paired gives [-0.0023, +0.0070]', 'TH-01_paired_inference.csv; TH-01_tost_table_reproduction.csv',
     'add paired interval, one-sided bound +0.0061, scale note (Edit 3)'),
    ('C3', 'sec:concentration; tab:tost', 'Five of sixteen gaps equivalent at +-0.005; primary not (p = 0.101)',
     'SUPPORTED (Welch); paired: 6 of 16, primary p = 0.111', 'TH-01_paired_inference.csv', 'add paired count (Edit 5)'),
    ('C4', 'sec:null', '"no score of any quality helped here"', 'OVERSTATED (oracle tested at 3 seeds, bar 0.0061)',
     'tab:trained (submitted)', 'soften (Edit 2)'),
    ('C5', 'abstract; sec:concentration; tab:boundary; app:diag', 'On SINet boundary metrics concentration clears its bar (C10-B 1.37x, CINV-B 1.34x); "strongest form of the result"',
     'NOT SUPPORTED AT 8 SEEDS for C10-B (0.30x, CI spans 0); CINV-B 0.64x, uncorrected CI excludes 0; 3-seed values reproduce exactly',
     'AN-03_arch_boundary_grid.csv; EXP-02_gate3_reproduction.csv', 'replace with 8-seed result; withdraw "strongest form" (Edits 1, 4)'),
    ('C6', 'sec:concentration', 'SINet-v2 resolves none of it', 'SUPPORTED descriptively; interaction NOT resolved (C10-B p 0.43; CINV-B p 0.053)',
     'AN-03_interaction.csv', 'report direct interaction test (Edit 4)'),
    ('C7', 'sec:concentration; fig:thesis(a)', 'Geometric separation comes from concentration, reproduced by shuffled/reversed allocations',
     'NOT RE-TESTED (no post-review analysis touches it); quota-multiset identity VERIFIED', 'TH-02_quota_invariants.csv',
     'keep; state it is geometric only (Edits 1, 4)'),
    ('C8', 'app:diag (attenuation)', 'About 48% of injected images differ between any two arms; effective contrast near 8.8%',
     'INCORRECT for B vs C10 (77%; 14.1% of pool); correct for C-family pairs (45-51%; 8.3-9.4%)', 'AN-02_overlap_by_seed.csv',
     'correct (Edit 6)'),
    ('C9', 'app:method', 'Pinned steps 253/127 so appended images displace exposure', 'SUPPORTED; theoretical exposure quantified; actual visits unverified',
     'AN-02_exposure_by_run.csv; AN-02_sampler_trace_search.json', 'add exposure figures (Edit 6)'),
    ('C10', 'app:controls', 'Pseudo-label means 1977/2025/1990/1979, range 1817-2259 "across the seed expansion"',
     'SUPPORTED for the 40 SE-trained runs; all 64 runs: 1991/2007/2020/2015, range 1782-2278', 'AN-02_summary.json', 'qualify (Edit 7)'),
    ('C11', 'app:method', 'CINV single fixed point is the median; same-shape arms preserve allocation shape',
     'VERIFIED (multiset identical; CSHUF rho -0.03351; s_e 0.0101)', 'TH-02_quota_invariants.csv', 'none'),
    ('C12', 'sec:discussion', 'Need a foreground supply not already exhausted', 'SUPPORTED: larger N gives <= 1.22x contrast; 0 new foregrounds among 4106 injected',
     'EXP-01_preflight.csv; AN-02_summary.json', 'add preflight + generator scope (Edit 8)'),
    ('C13', 'sec:why', 'Synthetic coverage 0.13-0.54 vs real source 0.71-0.75; silhouette 0.1600; ~1/5 variance between clusters; 51.5% budget on CAMO',
     'SUPPORTED (coverage 12/12 at 4 dp; eta^2 0.2046; silhouette 0.156 Euclidean / 0.253 cosine; CAMO 51.5% nearest-centroid, 53.0% committed labels)',
     'AN-04_gate4_coverage_reproduction.csv; AN-04_cluster_structure.csv; AN-04_cluster_domain_mix.csv',
     'note distance convention; optional label-based CAMO share (Edit 10)'),
    ('C19', 'sec:concentration', 'Targeting "covers no more of the target manifold"',
     'ESTIMATOR-DEPENDENT: C1 target recall saturated (~1.0); appendix k-NN recall (k=5) on injected renders: concentrated 0.62-0.64 vs random 0.35-0.43',
     'AN-04_foreground_coverage.csv; rebuild/C1/out/c1_coverage.csv', 'qualify (Edit 10.4)'),
    ('C20', 'sec:why', 'ES tracks per-pixel error about twice as strongly as structural error; ordering holds for three estimator families on both architectures',
     'SUPPORTED for SINet, SINet-v2, SegMaR, SINet-MT (reproduced exactly for SINet); REVERSED for source-only SINet (0.355 vs 0.458)',
     'AN-04_signal_correlations.csv; AN-04b_summary.json', 'add exception (Edit 10.3)'),
    ('C21', 'tab:arms; sec:concentration', 'Same-shape arms hold concentration fixed and differ only in direction',
     'SUPPORTED for quotas; but domain mix differs strongly (CAMO share C10 0.530, CSHUF 0.285, CINV 0.199)',
     'AN-04_cluster_domain_mix.csv; TH-02_quota_invariants.csv', 'mention as untested candidate explanation (Edit 10.2)'),
    ('C14', 'sec:contamination; app:chamext', '50/76 (41 + 9), 44 COD10K-train, 16 unchecked, 0 exact-hash vs training',
     'SUPPORTED (reproduced exactly)', 'AN-05_chameleon_pairs.csv', 'keep'),
    ('C15', 'app:chamext', 'Three CHAMELEON images byte-identical to CAMO-250', 'INCOMPLETE: 4 (adds animal-28 re-encode)',
     'AN-05_cross_benchmark.csv', 'amend (DOC-02 item 3)'),
    ('C16', 'sec:contamination', 'Sixteen unchecked; uncontaminated subset is 10 images',
     'INCOMPLETE: all 16 and 8 of the 10 are COD10K-test re-encodes; the 10 are same-dimension negatives only',
     'AN-05_cross_benchmark.csv', 'amend (DOC-02 items 1, 2, 4)'),
    ('C17', 'app:masks', 'Releases differ in polarity; IoU 0.0 / 0.6932; MAE 0.2196 vs 0.0816', 'SUPPORTED (reproduced exactly)',
     'AN-05_mask_release.csv', 'keep'),
    ('C18', 'sec:contamination', 'Difficulty analysis found no leaked-subset advantage', 'NOT RE-RUN (submitted evidence)', 'rebuild/D2_reaudit/D2R_RESULTS.md',
     'keep; no inflation claimed'),
]
cols = ['claim_id', 'manuscript_label', 'manuscript_claim', 'status_after_review', 'evidence', 'proposed_action']
with open(os.path.join(a.sr, 'RESULT_TABLES/DOC-01_claim_evidence_map.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    w.writerows(R)
print('wrote', len(R), 'rows')

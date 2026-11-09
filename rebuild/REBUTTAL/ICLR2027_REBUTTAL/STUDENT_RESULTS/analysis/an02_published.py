"""AN-02 -- published baselines and protocols for the performance gap (CW-03 / QA-03).

Every published value below was read from the ORIGINAL paper; the source (table, PDF page, printed page) is
stored with it. The PDFs are in Dataset/External/papers/ (sha256 in papers.sha256) and
Explanations/S2R-CODpaper.pdf. Each published value that has a released-map counterpart is cross-checked
against our re-score of those maps (EXP-03 E3-a / E3-d, RESULT_TABLES/EXP03_external_scores.csv).
Our own C10 values are computed here from the committed per-run CSVs.

E_phi is the MEAN E-measure throughout: SINet, SINet-V2 and RISE state "E_phi denotes mean E-measure" /
"mean E-measure (E_phi)", and S2R-COD reports E^mn explicitly. Our scorer's `meanEm` is that variant.

Outputs: RESULT_TABLES/AN02_published_baselines.{md,json}, RESULT_TABLES/AN02_rise.bib
"""
import csv
import json
import os

import numpy as np

import _repo as R

PUB = {
    'SINet-V2 (supervised)': dict(
        source='Fan, Ji, Cheng, Shao, "Concealed Object Detection", IEEE TPAMI 44(10), 2022; arXiv:2102.10274v2, '
               'Table 2, PDF p.8 (row "SINet (OUR)"; CHAMELEON / CAMO-Test / COD10K-Test)',
        COD10K=dict(Sm=0.815, meanEm=0.887, wFm=0.680, MAE=0.037), NC4K=None,
        nc4k_note='NC4K is not reported in the paper (arXiv v2). The repository released NC4K prediction maps '
                  '(news 2021/04/20); the reviewer\'s 0.847 matches our re-score of those maps (E3-a).',
        labels='real masks', training_images='CAMO-train + COD10K-train (4040), "without EXTRA" (p.8 fn. 4)',
        backbone='Res2Net-50, ImageNet-pretrained', input='352x352', recipe='Adam 1e-4, /10 every 50 epochs, 100 epochs, batch 36',
        generator='none'),
    'SINet (supervised, CVPR 2020)': dict(
        source='Fan et al., "Camouflaged Object Detection", CVPR 2020, Table 3, PDF p.7 (printed p.2783), '
               'row "SINet\'20 Training setting (iii)" = CAMO + COD10K + EXTRA',
        COD10K=dict(Sm=0.771, meanEm=0.806, wFm=0.551, MAE=0.051), NC4K=None,
        nc4k_note='NC4K postdates the paper.', labels='real masks', training_images='CAMO + COD10K + EXTRA (setting iii)',
        backbone='ResNet-50, ImageNet-pretrained', input='352x352', recipe='paper Sec. 5.1', generator='none'),
    'RISE (unsupervised, ICCV 2025)': dict(
        source='Du et al., ICCV 2025 (CVF open access), Table 1, PDF p.6 (printed p.22136), row "RISE DINOv2-ViT-L14"; '
               'implementation details same page (Sec. 4.1)',
        COD10K=dict(Sm=0.763, meanEm=0.840, wFm=0.600, MAE=0.049), NC4K=dict(Sm=0.805, meanEm=0.868, wFm=0.705, MAE=0.061),
        labels='none: pseudo masks from DINOv2-ViT-L/14 (last layer) clustering + multi-view KNN retrieval',
        training_images='3040 COD10K + 1000 CAMO (the same 4040 images as our unlabelled target pool)',
        backbone='detector: SINet-V2 (Res2Net-50, ImageNet), "the whole training process is identical to SINet-V2"; '
                 'pseudo-labelling: frozen DINOv2-ViT-L/14 at 476x476',
        input='352x352 (SINet-V2 recipe)', recipe='SINet-V2 recipe on pseudo masks', generator='none'),
    'S2R-COD SINet "Ours" (synthetic-to-real)': dict(
        source='Luo et al., "Synthetic-to-Real Camouflaged Object Detection", ACM MM 2025, Table 1 (HKU-IS -> COD10K), '
               'PDF p.5', COD10K=dict(Sm=0.7136, meanEm=0.7443, wFm=0.4814, MAE=0.0717), NC4K=None,
        nc4k_note='Table 1 (S2C) reports COD10K-test only.',
        labels='synthetic: 4447 HKU-IS composites; target unlabelled',
        training_images='paper text: "the real unlabeled COD10K training set"; the authors\' released Target archive '
                        'holds 4040 images (3040 COD10K + 1000 CAMO), which our reproduction used',
        backbone='ResNet-50 (SINet)', input='352x352', recipe='40 epochs, batch 16, Adam 1e-4, two rounds', generator='HKU-IS synthetic set'),
    'S2R-COD SINet-v2 "Ours" (synthetic-to-real)': dict(
        source='Luo et al., ACM MM 2025, Table 1, PDF p.5', COD10K=dict(Sm=0.6845, meanEm=0.7571, wFm=0.4764, MAE=0.0787),
        NC4K=None, nc4k_note='Table 1 reports COD10K-test only.', labels='synthetic', training_images='as above',
        backbone='Res2Net-50 (SINet-v2)', input='352x352', recipe='as above', generator='HKU-IS synthetic set'),
    'S2R-COD SINet Mean Teacher': dict(source='Luo et al., ACM MM 2025, Table 1, PDF p.5',
                                       COD10K=dict(Sm=0.6984, meanEm=0.7177, wFm=0.4165, MAE=0.0915), NC4K=None,
                                       nc4k_note='', labels='synthetic', training_images='as above', backbone='ResNet-50',
                                       input='352x352', recipe='single round', generator='HKU-IS synthetic set'),
}
REVIEWER = dict(C10=(0.719, 0.769), RISE=(0.763, 0.805), SINetV2=(0.815, 0.847))
RISE_BIB = r"""@inproceedings{du2025rise,
  title     = {Beyond Single Images: Retrieval Self-Augmented Unsupervised Camouflaged Object Detection},
  author    = {Du, Ji and Wang, Xin and Hao, Fangwei and Yu, Mingyang and Chen, Chunyuan and Wu, Jiesheng and Wang, Bin and Xu, Jing and Li, Ping},
  booktitle = {Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)},
  pages     = {22131--22142},
  year      = {2025}
}
% Verified 2026-11-09 against the CVF open-access PDF (title, all nine authors in order, ICCV 2025,
% printed pages 22131 on PDF p.1 to 22142 on PDF p.12) and arXiv:2510.18437. The DOI suggested in the
% instructions (10.1109/ICCV51701.2025.02055) could NOT be verified (IEEE Xplore not accessed) and is omitted.
"""


def c10_means():
    out = {}
    for path, seeds, tag in (('rebuild/ABC/out/abc_metrics.csv', (42, 43, 45), '3-seed (ABC)'),
                             ('rebuild/ABC/out/se/abc_metrics.csv', (42, 43, 45, 46, 47, 48, 49, 50), '8-seed (SE)')):
        rows = list(csv.DictReader(open(os.path.join(R.REPO, path))))
        for arch in ('SINet', 'SINetv2'):
            for ep in ('COD10K', 'NC4K'):
                v = [r for r in rows if r['arch'] == arch and r['arm'] == 'C10' and r['endpoint'] == ep and int(r['seed']) in seeds]
                out[(tag, arch, ep)] = {k: float(np.mean([float(r[k]) for r in v])) for k in ('Sm', 'meanEm', 'wFm', 'MAE')}
    return out


def main():
    ext = {(r['source'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(R.TABLES, 'EXP03_external_scores.csv')))}
    rescore = {'SINet-V2 (supervised)': 'E3-a SINet-V2 (released maps)', 'RISE (unsupervised, ICCV 2025)': 'E3-d RISE (released maps)'}
    checks = []
    for name, src in rescore.items():
        for ep in ('COD10K', 'NC4K'):
            pub = PUB[name][ep]
            r = ext[(src, ep)]
            if pub:
                for k in ('Sm', 'meanEm', 'wFm', 'MAE'):
                    checks.append(dict(method=name, endpoint=ep, metric=k, published=pub[k], rescored=float(r[k]),
                                       abs_diff=abs(pub[k] - float(r[k])), within_0p002=abs(pub[k] - float(r[k])) <= 0.002))
    c10 = c10_means()
    js = dict(published=PUB, rescored_released_maps={'%s|%s' % k: v for k, v in ext.items()}, checks=checks,
              ours_C10={'%s|%s|%s' % k: v for k, v in c10.items()}, reviewer_quoted=REVIEWER)
    json.dump(js, open(os.path.join(R.TABLES, 'AN02_published_baselines.json'), 'w'), indent=2)
    open(os.path.join(R.TABLES, 'AN02_rise.bib'), 'w').write(RISE_BIB)
    f3 = lambda x: '%.3f' % x
    md = ['# AN-02 -- published baselines, protocols, and the reviewer\'s quoted values', '',
          '*Generated by `analysis/an02_published.py`. Published values were read from the original papers '
          '(sources per row); "re-scored" values are our scorer on the officially released prediction maps '
          '(EXP-03 E3-a / E3-d). E_phi is the mean E-measure everywhere.*', '',
          '## Protocol table', '',
          '| Method | Labels used | Training / target images | Detector backbone (pretraining) | Generator | COD10K S_a / E_phi / F_w | NC4K S_a / E_phi / F_w | Source |',
          '|---|---|---|---|---|---|---|---|']
    for name, p in PUB.items():
        cod = ' / '.join(f3(p['COD10K'][k]) for k in ('Sm', 'meanEm', 'wFm'))
        nc = ' / '.join(f3(p['NC4K'][k]) for k in ('Sm', 'meanEm', 'wFm')) if p['NC4K'] else 'not reported'
        md.append('| %s (published) | %s | %s | %s | %s | %s | %s | %s |' % (name, p['labels'], p['training_images'], p['backbone'],
                                                                            p['generator'], cod, nc, p['source']))
    for name, src in rescore.items():
        cod = ' / '.join(f3(float(ext[(src, 'COD10K')][k])) for k in ('Sm', 'meanEm', 'wFm'))
        nc = ' / '.join(f3(float(ext[(src, 'NC4K')][k])) for k in ('Sm', 'meanEm', 'wFm'))
        md.append('| %s (released maps, re-scored by us) | as above | as above | as above | — | %s | %s | `EXP03_external_scores.csv` |'
                  % (name, cod, nc))
    for tag in ('3-seed (ABC)', '8-seed (SE)'):
        for arch in ('SINet', 'SINetv2'):
            cod = ' / '.join(f3(c10[(tag, arch, 'COD10K')][k]) for k in ('Sm', 'meanEm', 'wFm'))
            nc = ' / '.join(f3(c10[(tag, arch, 'NC4K')][k]) for k in ('Sm', 'meanEm', 'wFm'))
            md.append('| Ours, C10 %s %s | synthetic (4447 LAKE-RED-era composites + 1000 injected renders); target unlabelled | '
                      '4040 unlabelled target (3040 COD10K + 1000 CAMO) | %s | LAKE-RED (fixed, offline) | %s | %s | committed metrics CSV |'
                      % (arch, tag, 'ResNet-50 (ImageNet)' if arch == 'SINet' else 'Res2Net-50 (ImageNet)', cod, nc))
    md += ['', '## Published vs re-scored (scorer agreement; tolerance 0.002)', '',
           '| Method | Endpoint | Metric | Published | Re-scored | abs diff | within 0.002 |', '|---|---|---|---|---|---|---|']
    for c in checks:
        md.append('| %s | %s | %s | %.3f | %.6f | %.6f | %s |' % (c['method'], c['endpoint'], c['metric'], c['published'], c['rescored'],
                                                                c['abs_diff'], c['within_0p002']))
    md += ['', '## The reviewer\'s quoted values (CW-03)', '',
           '- **C10 approx. 0.719 (COD10K-test) and 0.769 (NC4K):** our 3-seed SINet C10 means are %.4f and %.4f '
           '(per-run rows in Appendix D); at 8 seeds %.4f and %.4f. SINet-v2 C10 is lower: %.4f and %.4f (8 seeds).'
           % (c10[('3-seed (ABC)', 'SINet', 'COD10K')]['Sm'], c10[('3-seed (ABC)', 'SINet', 'NC4K')]['Sm'],
              c10[('8-seed (SE)', 'SINet', 'COD10K')]['Sm'], c10[('8-seed (SE)', 'SINet', 'NC4K')]['Sm'],
              c10[('8-seed (SE)', 'SINetv2', 'COD10K')]['Sm'], c10[('8-seed (SE)', 'SINetv2', 'NC4K')]['Sm']),
           '- **RISE 0.763 / 0.805:** RISE Table 1, row DINOv2-ViT-L14 (their strongest DINO configuration); our re-score of '
           'the released maps gives %.4f / %.4f.' % (float(ext[('E3-d RISE (released maps)', 'COD10K')]['Sm']),
                                                    float(ext[('E3-d RISE (released maps)', 'NC4K')]['Sm'])),
           '- **SINet-v2 approx. 0.815 / 0.847:** 0.815 is SINet-V2 Table 2 (COD10K); NC4K is not in the paper, and 0.847 '
           'matches our re-score of the officially released NC4K maps (%.4f).' % float(ext[('E3-a SINet-V2 (released maps)', 'NC4K')]['Sm']),
           '', '## Correction to the initial rebuttal (RISE description)', '',
           'The initial response described RISE as relying on "a different representation (frozen self-supervised ViT '
           'features with dataset-level retrieval) and a different training pipeline". The paper (Sec. 4.1, p.6) shows '
           'that RISE\'s detector **is SINet-V2**, trained with SINet-V2\'s own training process, on pseudo masks that '
           'RISE generates for **the same 4040 COD10K/CAMO training images** that our pipeline uses as its unlabelled '
           'target pool; the frozen DINOv2-ViT-L/14 features and retrieval are used only to generate those pseudo masks. '
           'The gap to RISE therefore isolates the *source of supervision on the target images* (RISE: pseudo masks on the '
           'real target images; ours: synthetic renders plus self-training) far more than a difference in detector or '
           'representation. EXP-03 E3-e (our trainer on RISE\'s released pseudo masks) measures this directly. Our '
           'clustering also uses frozen DINOv2 ViT-L/14 features, but only to allocate the synthetic budget.']
    open(os.path.join(R.TABLES, 'AN02_published_baselines.md'), 'w').write('\n'.join(md) + '\n')
    bad = [c for c in checks if not c['within_0p002']]
    print('AN-02 written; scorer agreement: %d/%d published values within 0.002 of our re-score%s'
          % (len(checks) - len(bad), len(checks), '' if not bad else '; outside: %s' % [(c['method'], c['endpoint'], c['metric'], round(c['abs_diff'], 4)) for c in bad]))


if __name__ == '__main__':
    main()

{
  "notes": [
    {
      "content": {
        "paper_summary": {
          "value": "This paper investigates whether uncertainty-guided allocation of a fixed synthetic-data budget improves camouflaged object detection (COD). The authors develop a pipeline that clusters unlabeled real images, estimates cluster-level uncertainty from student–teacher disagreement, and allocates synthetic samples toward high-uncertainty clusters. Using SINet and SINet-v2, they compare this strategy against random allocation and several controls designed to separate the effect of uncertainty targeting from the concentration of the allocation budget.\n\nAcross 103 training runs, the authors find no consistent improvement from uncertainty-guided targeting. Additional experiments suggest that the distinguishability of targeted and randomly selected synthetic datasets is primarily explained by allocation concentration rather than the direction of the uncertainty signal. The paper further investigates several potential explanations for the negative result, including weak clustering structure, limited alignment between uncertainty and evaluation metrics, and insufficient coverage of the target distribution by synthetic samples.\n\nSeparately, the authors identify substantial data contamination in the CHAMELEON benchmark, reporting that at least 50 of its 76 images overlap with COD10K or CAMO training data despite exact file hashing detecting no overlap. They provide a duplicate-detection procedure and discuss the implications for COD evaluation."
        },
        "presentation": {
          "value": 3
        },
        "informativeness": {
          "value": 2
        },
        "soundness": {
          "value": 2
        },
        "critical_strengths": {
          "value": "1. A rigorously controlled study investigating a potentially significant confounding factor in the synthetic data allocation process.\n\nThe study’s most notable methodological contribution lies in its distinction between \"allocation concentration\" and \"targeting direction.\" Comparing uncertainty-based selection solely against random sampling fails to disentangle these two factors; in contrast, control techniques such as \"concentration-preserving shuffle\" and \"reversed-ranking\" provide more meaningful experimental comparisons.\n\nThe authors’ transparent presentation of these negative—or rather, inconclusive—results further strengthens the study’s empirical contribution.\n\nThis is highly significant, as the proposed control methods are not limited to the field of Camouflaged Object Detection (COD) but are also valuable for evaluating other uncertainty-guided data acquisition and augmentation strategies.\n\n2. A critical finding regarding \"benchmark contamination,\" which holds independent value in its own right.\n\nThe analysis of the CHAMELEON dataset represents a substantial contribution. The authors reveal that 50 out of the 76 images in this dataset overlap with the training data—comprising 41 re-encoded copies (with identical dimensions) and 9 matches identified via geometric verification. Crucially, these overlaps could not be detected through simple exact hashing, highlighting the limitations of conventional deduplication methods.\n\nFurthermore, the study demonstrates that different versions of the CHAMELEON mask data lead to significant discrepancies in evaluation results—an observation that underscores the practical importance of this analysis.\n\nRegardless of the ultimate success of the \"uncertainty-guided\" generation strategy proposed in the paper, these findings have profound implications for assessing the reliability and comparability of existing benchmarks for the COD task."
        },
        "critical_weaknesses": {
          "value": "1. Statistical Sensitivity and Interpretation of the Negative Result\n\nThe difference between targeted and random training is quite small. Synthetic images make up only 18.4% of the training set, and about half are shared across different groups. As noted in Appendix C, only around 8.8% of the full training set actually differs. This may make small improvements hard to detect.\n\nThe authors also use twice the pooled standard deviation as their decision rule, which is more conservative than using the standard error. The eight-seed comparison shows a difference of +0.0024, with a 95% confidence interval of [-0.0020, +0.0067]. This rules out the reference improvement of +0.0142, but smaller gains are still possible. Also, the targeting-versus-random comparison does not pass the equivalence test at ±0.005.\n\nOverall, the results show that this method does not bring a large improvement in the tested setting. However, they do not fully rule out smaller gains. I think the paper should make this limitation clearer.\n\n2. Downstream Validation and Generalizability of the Concentration Hypothesis**\n\nThe geometric analysis shows that concentrating samples changes the selected dataset, even when uncertainty scores are shuffled or reversed. However, this does not mean that concentration improves detection performance.\n\nIn the post-hoc boundary-metric analysis, both targeted and reversed allocation perform better than random allocation on SINet. However, these gains are much smaller on SINet-v2. This suggests that the effect of concentration may depend on the model architecture.\n\nThe experiments also use a fixed pool of LAKE-RED images generated offline. Since no new foreground content is generated, uncertainty guidance can only select from existing samples. This may limit its benefits, especially when the synthetic data does not cover the real data distribution well.\n\nTherefore, the negative results may be partly caused by the generation setup. It is still unclear whether the same conclusion would hold with better synthetic data or an adaptive generation process."
        },
        "questions_for_authors": {
          "value": "1. How well do the results rule out smaller improvements from uncertainty-guided targeting?\n\nThe eight-seed results rule out large improvements, but the targeting-versus-random comparison does not pass the equivalence test at ±0.005. Could the authors clarify what level of improvement they consider meaningful for COD? Also, could they provide a paired analysis using the same random seeds? This would help clarify whether the negative result also applies to smaller but useful improvements.\n\n2. How much do the limited training-set differences and synthetic data diversity affect the conclusion?\n\nAs noted in Appendix C, only about 8.8% of the training pool differs between the compared groups. The synthetic data also have limited coverage of the real data distribution. Would the same conclusion hold if the training sets had larger differences or if the generator could produce more diverse foreground content? Additional experiments or discussion on these limitations would help support the generality of the results.\n\n3. How does CHAMELEON contamination affect existing COD evaluation results?\n\nThe paper identifies 50 overlapping images, including 44 that also appear in COD10K-train. Could the authors clarify how these overlaps may affect common COD training and evaluation protocols? In particular, it would be useful to distinguish between supervised training, unlabeled target-domain adaptation, and checkpoint selection. This would help readers better understand the practical impact of the contamination finding."
        },
        "flag_for_ethics_review": {
          "value": "No"
        },
        "rating": {
          "value": 2
        },
        "confidence": {
          "value": 2
        }
      },
      "id": "YRkN11gOzp",
      "forum": "B7MDj5uE2e",
      "replyto": "B7MDj5uE2e",
      "signatures": [
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_dypE"
      ],
      "nonreaders": [],
      "readers": [
        "everyone"
      ],
      "writers": [
        "ICLR.cc/2027/Conference",
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_dypE"
      ],
      "number": 3,
      "invitations": [
        "ICLR.cc/2027/Conference/Submission39230/-/Official_Review",
        "ICLR.cc/2027/Conference/-/Edit"
      ],
      "domain": "ICLR.cc/2027/Conference",
      "tcdate": 1792588796763,
      "cdate": 1792588796763,
      "tmdate": 1793968301866,
      "mdate": 1793968301866,
      "parentInvitations": "ICLR.cc/2027/Conference/-/Official_Review",
      "license": "CC BY 4.0",
      "version": 2,
      "details": {
        "writable": false
      }
    }
  ],
  "count": 1
}
{
  "notes": [
    {
      "content": {
        "paper_summary": {
          "value": "This paper investigates whether an uncertainty-guided closed-loop strategy can efficiently allocate a fixed synthetic data generation budget (e.g., 1,000 images)\n\nThe authors evaluate a standard active-learning-style loop:\nCluster unlabeled real target images into k=75 clusters using self-supervised representations (DINOv2)\n\nMeasure model uncertainty across clusters using a student–teacher disagreement score\n\nAllocate more synthetic images to clusters where the model is least certain using a softmax temperature distribution.\n\nAppend the synthetic data to the training pool and retrain the model\n\nKey Finding — Null Result on Uncertainty: Across 103 training runs, uncertainty-based targeting does not beat allocating synthetic data uniformly at random on downstream segmentation accuracy."
        },
        "presentation": {
          "value": 2
        },
        "informativeness": {
          "value": 2
        },
        "soundness": {
          "value": 1
        },
        "critical_strengths": {
          "value": "Authors introduces the \"same-shape shuffle\" control to decouple budget concentration (shape) from budget direction (aim). This exposes a major drawback present in prior synthetic data allocation literature.\n\nIn-Depth Failure Diagnosis: Rather than stopping at a null result, the authors rigorously analyze why the loop failed (clustering silhouette analysis, within vs. between error variance, manifold coverage)"
        },
        "critical_weaknesses": {
          "value": "The  main contribution of this paper is the validation of null hypothesis i.e.  Any non-uniform allocation is separable from a uniform draw with lower effective rank, so the probe result is only as good as  a sanity check . From a contribution view point this has limited role in advancing the camouflage object detection methodology.\n\nBounded Scope: The conclusions are bounded to Camouflaged Object Detection (COD) using the LAKE-RED generator, SINet/SINet-v2 architectures, and background replacement. Findings may not directly transfer to task domains with vastly more expressive generative feedback loops.\n\nGenerator Expressiveness Bottleneck: The generator is constrained to reusing fixed foreground cutouts, creating a narrow synthetic distribution (0.13 --0.54 manifold coverage) that may inherently limit the potential benefit of any steering policy"
        },
        "questions_for_authors": {
          "value": "CORACLE keeps C10's shape. Did you test an oracle with a different shape (e.g., proportional to true error, or concentrated on the truly worst clusters)?\n\nReplicate with one modern backbone and one foreground-varying generator,  and scope the claim to the LAKE-RED/S2R-COD pipeline."
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
      "id": "vCJZ38XuMk",
      "forum": "B7MDj5uE2e",
      "replyto": "B7MDj5uE2e",
      "signatures": [
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_Caus"
      ],
      "nonreaders": [],
      "readers": [
        "everyone"
      ],
      "writers": [
        "ICLR.cc/2027/Conference",
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_Caus"
      ],
      "number": 2,
      "invitations": [
        "ICLR.cc/2027/Conference/Submission39230/-/Official_Review",
        "ICLR.cc/2027/Conference/-/Edit"
      ],
      "domain": "ICLR.cc/2027/Conference",
      "tcdate": 1792488733734,
      "cdate": 1792488733734,
      "tmdate": 1793968303374,
      "mdate": 1793968303374,
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
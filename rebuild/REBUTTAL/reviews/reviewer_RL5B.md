{
  "notes": [
    {
      "content": {
        "paper_summary": {
          "value": "This paper studies whether uncertainty-guided allocation of a fixed synthetic-data budget improves camouflaged object detection (COD). Through controlled comparisons with random, shuffled, reversed, and current-error-guided allocation, the authors find no reliable improvement in the primary metrics. The paper also reports substantial image overlap between CHAMELEON and training data."
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
          "value": "- The same-shape shuffled and reversed controls provide a meaningful way to isolate the contribution of uncertainty-guided allocation. The extensive experiments make the negative results more informative than a simple comparison against random sampling.\n- The CHAMELEON overlap audit examines re-encoded and geometrically transformed images, offering potentially useful evidence about benchmark integrity."
        },
        "critical_weaknesses": {
          "value": "- For the primary comparison C10−B, the reported difference is $+0.0024$, with a $95%$ confidence interval of $[−0.0020, +0.0067]$. This interval does not establish equivalence within the proposed margin of ($\\delta=0.005$). The results support a lack of reliable evidence for an advantage, not the stronger conclusion that uncertainty guidance has no meaningful effect.\n- The distributional analyses show that concentrated allocation changes the training-set composition, but this does not establish that concentration explains downstream performance changes. The post-hoc boundary-metric results are suggestive but are not consistent across both architectures.\n- The reported C10 results achieve approximately ($S_\\alpha=0.719$) on COD10K-test and ($0.769$) on NC4K, below the reported unsupervised RISE results of $0.763$ and $0.805$, respectively, and standard supervised SINet-v2 results of approximately $0.815$ and $0.847$. These results are not directly comparable because the training protocols differ. And the gap raises questions about the effectiveness of the overall pipeline. Stronger protocol-matched baselines and a clearer explanation of the performance gap are needed.\n- The method relies on a fixed generator and a limited foreground pool, with synthetic diversity primarily coming from background changes. Weak clustering structure and limited foreground diversity may constrain the method from the outset. Consequently, the results provide limited evidence about uncertainty-guided synthetic-data generation more generally."
        },
        "questions_for_authors": {
          "value": "- Could the primary confidence intervals and equivalence-test results be presented more prominently, with a clear distinction between failure to detect an effect and evidence of equivalence?\n- What evidence supports the claim that budget concentration explains downstream performance, rather than merely changing the training-set distribution?\n- Can the performance gap be explained through protocol-matched comparisons with supervised and unsupervised COD baselines?\n- Can the conclusions be better bounded to the specific generator, foreground pool, and training setup evaluated?"
        },
        "flag_for_ethics_review": {
          "value": "No"
        },
        "rating": {
          "value": 2
        },
        "confidence": {
          "value": 3
        }
      },
      "id": "OX34XCOS3I",
      "forum": "B7MDj5uE2e",
      "replyto": "B7MDj5uE2e",
      "signatures": [
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_RL5B"
      ],
      "nonreaders": [],
      "readers": [
        "everyone"
      ],
      "writers": [
        "ICLR.cc/2027/Conference",
        "ICLR.cc/2027/Conference/Submission39230/Reviewer_RL5B"
      ],
      "number": 1,
      "invitations": [
        "ICLR.cc/2027/Conference/Submission39230/-/Official_Review",
        "ICLR.cc/2027/Conference/-/Edit"
      ],
      "domain": "ICLR.cc/2027/Conference",
      "tcdate": 1792479077361,
      "cdate": 1792479077361,
      "tmdate": 1793968305018,
      "mdate": 1793968305018,
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
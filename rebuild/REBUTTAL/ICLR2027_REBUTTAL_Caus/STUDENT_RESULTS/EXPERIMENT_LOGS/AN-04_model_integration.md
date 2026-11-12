# AN-04: modern detector integration and protocol-parity preflight

**Status: BLOCKED.** The candidate rule was applied and recorded before any outcome existed. No
detector was integrated, and no detector number exists. The table is `RESULT_TABLES/AN-04_preflight.csv`.

## Candidate rule, as applied

The guide's rule: first consider **CamoFormer**. Use **CTF-Net** only if CamoFormer cannot be
integrated reproducibly. Prefer models with a checkpoint, training code and a compatible licence, and
declare any replacement before outcomes.

1. **CamoFormer** ([repository](https://github.com/HVision-NKU/CamoFormer)). The README documents only
   install, download, test (`test.sh`) and evaluation (`eval.sh`). The visible files include
   `dataset.py` and `test.py` but no training script, and search found no training instructions. Its
   licence is the README line "Code in this repo is for non-commercial use only". **It fails the rule's
   trainability condition.** Trainability cannot be established without reconstructing a training
   pipeline, which would no longer be "the official model".
2. **CTF-Net** ([repository](https://github.com/zcc0616/CTF-Net)). `etrain.py` contains a complete
   training loop (100 epochs, batch 12, 384 px, Adam 1e-4). **The repository carries no licence.**
   With no licence, reuse rights are not granted. Licensing is reserved to the corresponding author, so
   this is recorded as a blocker, not decided here.
3. **Protocol conflict common to both.** Released COD checkpoints are trained with COD10K-train and
   CAMO-train masks. Those are exactly this study's *unlabelled* target pool. Initialising from them
   would leak target labels into every arm. A fair replication must train the detector from an
   ImageNet backbone inside the two-round S2R-COD loop. That means a new adapter for the student/EMA
   teacher, the ES consistency loss and CLS, plus its own stable-baseline run before any arm comparison.
4. **Compute.** Even a minimal B/C10/CSHUF × 3-seed cell for a ~100-epoch, 384 px detector, trained in
   two rounds, is several times the cost of a SINet run per seed. It lies wholly outside the
   12-run allocation, and the owner's constraint marks EXP-02 BLOCKED for compute.

## §6 blocker record (EXP-02, and EXP-04 through it)

| Field | Content |
|---|---|
| Missing item | A trainable, licensed modern COD detector integrated into the two-round loop, plus ≥ 9 GPU runs |
| Discovery tried | Repository pages and file listings of CamoFormer and CTF-Net read on 2026-11-12; a search for CamoFormer training code |
| Exact errors | CamoFormer: no training entrypoint found. CTF-Net: no licence. Both: released weights trained on this study's target-pool labels. |
| Resources/permission needed | (a) An author decision on CTF-Net's licence status, or another candidate with a licence and training code. (b) A GPU allocation for an adapter pilot plus ≥ 9 runs. |
| Alternative attempted | The guide's fallback (CTF-Net) was evaluated and is blocked by its licence |
| Claim that cannot be made | That the absence of a direction effect persists under a modern transformer-based detector. The null stays scoped to SINet and SINet-v2. |

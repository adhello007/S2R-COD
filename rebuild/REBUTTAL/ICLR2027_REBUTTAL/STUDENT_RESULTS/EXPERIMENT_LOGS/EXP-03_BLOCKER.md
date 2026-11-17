# EXP-03: blocker record

**Task:** EXP-03, a conditional test with a generator that produces new foregrounds or adapts during
training (CW-02, QA-02).
**Status:** `BLOCKED`, because its own gate fails. Compute is a second, independent blocker.
**Recorded:** 2026-11-12 (IST).

## The gate (from the brief, §5 EXP-03)
The gate needs a generator that produces **genuinely new foreground content** that is legally usable
and independently validated. It also needs masks, quality control, provenance, a contamination screen,
and permission to use compute. A fixed pool that only re-renders backgrounds explicitly does not
qualify.

## What was searched (read-only, no downloads)
| Location | Found | Qualifies? |
|---|---|---|
| `S2R-COD/LAKE-RED/` (code + `ckpt/LAKERED.ckpt`, 6.4 GB, Apache-2.0) | LAKE-RED (CVPR 2024): generates a camouflaged **background** around a given foreground mask, using latent background-knowledge retrieval | **No.** The foreground and its mask are inputs, so the object is copied, not generated |
| `S2R-COD/Dataset/LAKERED/output/HKU-IS/` | 4447 offline renders, one per base foreground | **No.** This is the fixed pool under test |
| `~/.cache/huggingface/hub` | `timm` DINOv2-L/14, DINOv2-B/14 and CLIP-L/14 encoders; one unrelated simulation dataset | **No.** These are encoders, not generators |
| Filesystem search (`find / -xdev -maxdepth 6`) for `*stable-diffusion*`, `*sdxl*`, `*controlnet*`, `*.safetensors` | nothing | — |

## Evidence that the current pool copies foregrounds (post-review, AN-02/AN-04)
- Every injected render stem maps one-to-one onto a base-pool foreground. Of the 4106 distinct stems
  injected across arms and seeds, **0 are novel** relative to the 4447 base foregrounds
  (`RESULT_TABLES/AN-02_overlap_by_seed.csv`, `EXPERIMENT_LOGS/AN-02_summary.json`).
- In 12 randomly drawn render masks, IoU with the base ground truth of the same stem is 0.92–0.98
  (`RESULT_TABLES/AN-02_hand_inspection.csv`). AN-04 extends this to all stems.
- The manuscript already reports, from committed artifacts, that none of 8885 traced objects shows any
  sign of regeneration (`sec:why`).

## Resources needed to unblock
1. A generator that synthesises new object identities, with masks: for example a text- or
   layout-conditioned diffusion model with a mask-producing head, or a 3D/asset-based compositor using
   a licensed object library. Its licence must be recorded and its novelty validated independently
   (nearest-neighbour distance of every generated object to the training foregrounds and to every
   endpoint, using the AN-05 detector).
2. Matched generation for B_new and C10_new at the same budget, with identical acceptance filtering
   and every rejected draw logged.
3. GPU time for training. At the SE campaign's measured cost, a minimal screening design of
   2 arms × 3 seeds × 2 architectures is about 23 GPU-hours, and eight seeds is about 61 GPU-hours.
   No GPU is available to this reviewer's work before the 17 Nov cutoff.

## Valid alternative used instead
AN-04's observational coverage audit, labelled descriptive. **No claim is made about adaptive or
novel-foreground generation.** The fixed-pool null stays scoped to re-backgrounded copies of existing
foregrounds.

## What remains unresolved
Whether uncertainty-directed allocation helps when the generator can change the **foreground
support**. This experiment is still the only way to answer that.

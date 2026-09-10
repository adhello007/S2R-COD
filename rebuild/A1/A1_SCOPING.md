# A1 — Pre-planning scoping audit: the conditioning channel of the LAKE-RED generator

> **Outcome, decided 2026-09-10.** Resolved by **static citation only — no experiment run.** The
> refutation in §3.3 is settled by source reading, so **A1-S** was taken and **A1-T / A1-P** (§4.1)
> were not run. `rebuild/PAPER/main.tex` was updated accordingly: §6(ii) records the withdrawal, and
> the abstract, the contributions list, `tab:causes`, `tab:trace`, the conclusion's fourth
> requirement and the unverified-claims ledger were brought into line. The A1 rows of §4 of
> `REBUILD_PLAN.md` are filled, including a new row A1.5 for the U-Net route.
>
> Two claims were **deliberately kept out** of the paper as unsupported by static reading: that the
> generator is *"not the binding constraint"*, and that it is *steerable*. Static reading shows the
> channel is not narrow; it does not show the capacity is used (§4.3(2)), and the generator still has
> no port through which a deficiency could be named (§3.3 note). The paper says only the former.
>
> Still open: decisions (d)(3)–(d)(6) in §6, and whether §3 (A1) of `REBUILD_PLAN.md` receives a
> dated amendment for its unsatisfiable pre-registered confirm condition.

**Status of this document.** Scoping audit; superseded on its decision points by the box above. No
experiment was written and none was run. The only code executed was read-only: a `torch.load` of
`LAKE-RED/ckpt/LAKERED.ckpt` to read one 18-parameter tensor, a polarity read of three staged mask
files, and `sha256sum` over the cited generator sources. No number in this document enters
`results/REBUILD_LOG.txt`.

**Generator source location.** `LAKE-RED/` is untracked in this repository (`git status`: `?? LAKE-RED/`).
Every `file:line` below is therefore a citation into a working-tree file, not a committed artifact —
the caveat the paper carries in the source comments of §6(ii). Those sources are now pinned:
`rebuild/A1/out/a1_source_manifest.sha256` records a SHA256 for each of the nine files cited here.

**Line numbers** are as of this audit against the working tree. Paths are relative to the repo root
unless prefixed, in which case they are relative to `LAKE-RED/`.

---

## 0. Executive answer (details and evidence in §§1–5)

The narrow-channel account in `main.tex:592-604` is **refuted as stated**, and it is refuted by
static reading of the architecture — not by a marginal leakage effect that a runtime trace would
have to adjudicate.

There are **four** routes by which foreground information reaches the regenerated background region.
Exactly one of them is the 48-scalar summary. The largest is one the existing plan does not mention:
the full-resolution foreground latent is handed to the UNet directly, and the UNet is globally
connected by spatial self-attention.

Additionally, the decisive check the paper names — "whether the foreground tensor is identically
zero under the mask" — is the **wrong check**. It is (a) architecturally unsatisfiable, and
(b) not sufficient even if it held, because the dominant route bypasses the tensor it inspects.
A1 must be re-specified before it is planned. This is the main output of this audit.

---

## 1. The masking and compositing contract

### 1.1 Mask polarity

**DECISION.** On disk, a LAKE-RED mask stores **object = 0 (black)** and **background = 255 (white)**.
In tensor space `mask == 1` is the **background**, and it is the region the diffusion model
**regenerates**. `mask == 0` is the **object**, and it is **preserved**. This is the inverse of the
SOD/COD ground-truth convention.

**EVIDENCE.**
- `LAKE-RED/test.py:72` — `masked_image = (1 - mask) * image`. With `mask == 0` on the object,
  `(1 - mask) == 1` there, so `masked_image` **keeps the object and blacks out the background**.
  Despite its name, `masked_image` is a *foreground cutout on black*. This is why the tensor is
  called `fg` inside BKRA (`ldm/ldm/models/diffusion/ddpm.py:1567`).
- `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1552` — `m = 1-mask[b].squeeze()` is passed as the SLIC
  `mask=` argument, so the superpixel pooling runs over `mask == 0`, i.e. over the object.
- `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1590` — `new_fg = fg*(1-mask) + fg2bg*mask`: the
  generated content `fg2bg` lands where `mask == 1`.
- `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1595` — the reconstruction loss is
  `get_loss(new_fg*mask, x_start*mask)`, i.e. BKRA is trained to reconstruct the `mask == 1` region.
  That region is therefore the background, by construction of the training objective.
- `LAKE-RED/src/lake_red/prepare_lakered_inputs.py:50-61` — `to_lakered_mask` does
  `np.where(is_object, 0, 255)`; docstring at `:3-15` quotes the LAKE-RED paper §3 to the same effect.
- `LAKE-RED/run_hkuis.sh:4-6` — the pipeline comment states the inversion is deliberate.
- Empirical, this audit: the three staged masks `Dataset/LAKERED/input/HKU-IS/validation/masks/SOD_000{4,5,6}.png`
  are 78.3 % / 72.5 % / 82.1 % white — i.e. predominantly background-white, object-black.
- `rebuild/E0/E0.md` §2 already certifies this as threshold **T2** ("LAKE-RED input masks are
  inverted (object = 0)"), so A1 inherits it rather than re-deriving it.

**STATUS: settled.** No decision needed.

### 1.2 What is actually fed to the diffusion model, and in what numeric range

**DECISION.** The UNet receives a 7-channel tensor: 3 channels of noisy latent, 3 channels of
BKRA-processed conditioning (`new_fg`), 1 channel of downsampled mask. The mask channel is in
**{−1, +1}**, not {0, 1}, and this materially changes the arithmetic at `ddpm.py:1590`.

**EVIDENCE.**
- `LAKE-RED/test.py:128` — `c = model.cond_stage_model.encode(batch["masked_image"])`. With
  `cond_stage_config: __is_first_stage__` (`config_LAKERED.yaml:67`) this is the VQ encoder;
  `VQModelInterface.encode` returns the **pre-quantization** continuous latent
  (`ldm/ldm/models/autoencoder.py:267-270`). `embed_dim: 3` and `ch_mult: [1,2,4]`
  (`config_LAKERED.yaml:47,58-61`) give 3 channels at f=4, so 512 px → **(1, 3, 128, 128)**.
- `LAKE-RED/test.py:131-134` — mask nearest-interpolated to 128×128 and concatenated →
  `cond` is (1, 4, 128, 128).
- `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1467` — `xc = torch.cat([x] + c_concat, dim=1)`
  → 3 + 3 + 1 = **7**, matching `in_channels: 7` (`config_LAKERED.yaml:29`) and the loaded input
  convolution `model.diffusion_model.input_blocks.0.0.weight` of shape **(256, 7, 3, 3)** (measured
  from the checkpoint, this audit).
- **The {−1,+1} mask.** `LAKE-RED/test.py:76-77` rescales *every* batch key by `* 2.0 - 1.0`,
  including `"mask"`. So in `ddpm.py:1590`, `mask ∈ {−1, +1}` and `(1-mask) ∈ {+2, 0}`, giving:
  - at background (`mask=+1`): `new_fg = 0·fg + 1·fg2bg = fg2bg`
  - at object (`mask=−1`): `new_fg = 2·fg − fg2bg`

  This is **not** a clean composite, and the object region of `new_fg` is an amplified copy of the
  foreground latent minus the generated content. The same rescale is applied on the training side
  (`ldm/ldm/data/PIL_data.py:186`, over a batch that includes `"mask"` at `:184`) and
  `DDPM.get_input` performs no further rescaling (`ddpm.py:684-690`), so this is the **trained
  convention, not an inference bug**. Flagged because it is load-bearing for §3 below and because
  it is not what the arithmetic looks like on a first read.

**STATUS: settled.**

### 1.3 A second masking asymmetry: dilated vs undilated

**DECISION.** `masked_image` is built from the **undilated** mask while the mask channel given to
the model is **dilated**. A thin ring of *literal original object pixels* therefore sits at
positions the model is told to regenerate.

**EVIDENCE.**
- `LAKE-RED/test.py:47-57` — the dilated mask (`cv2.dilate`, `kernel_size=2`, 1 iteration) becomes
  `batch["mask"]` at `:74`.
- `LAKE-RED/test.py:65-72` — a *separately re-read, undilated* mask builds `masked_image` at `:72`.
- Because the on-disk mask is background-white, dilation grows the **background**, i.e. it moves the
  `mask == 1` boundary *inward* over the object. In that ring `mask == 1` (regenerate) but
  `masked_image` still holds real object pixels.
- Scale: `--dilate_kernel` default 2 (`test.py:193`), 1 iteration, at 512 px → ~1 px, which is
  sub-cell at f=4. Real but small.

**STATUS: settled as a fact.** Its magnitude is minor and it is *not* the decisive route; recorded
so A1's plan does not later mistake it for the main finding.

### 1.4 The compositing path (`isReplace`) and the resulting baseline

**DECISION.** At the flags actually used, the output object region is **(a) the original pixels
pasted back** at original resolution — not diffusion output, not a blend. The **only** open question
for A1 is therefore whether foreground information reaches the **background** region.

**EVIDENCE.**
- `LAKE-RED/test.py:159-166`:
  ```python
  if args.isReplace:
      # composite at ORIGINAL resolution: mask==0 is the object region
      # that LAKE-RED must preserve pixel-exactly (paper Sec. 3)
      image_array = np.array(original_image)
      mask_array  = np.array(original_mask)
      out_array   = np.array(img)
      out_array[mask_array == 0] = image_array[mask_array == 0]
      img = Image.fromarray(out_array)
  ```
  A hard assignment, no feathering, no alpha — a paste, at the original (un-resized) resolution,
  using the **undilated** on-disk mask (`original_mask`, read at `test.py:82`).
- `--isReplace` is a store-true flag (`LAKE-RED/test.py:192`) and **is passed** by the script that
  produced the pools: `LAKE-RED/run_hkuis.sh:28` — `--isReplace --seed 0 --shard_index ...`.
- Already measured by E0 and already in the paper: object-interior MAE 5.603 vs background 70.802,
  ratio 12.64, no image above 40 inside the object (`rebuild/PAPER/main.tex:884-887`; threshold
  "background error exceeds foreground error by ≥ 5×" in `rebuild/E0/E0.md` §5). The residual 5.603
  is JPEG re-encode (`test.py:169` writes `.jpg`) plus the ~1 px dilation ring, not diffusion.

**STATUS: settled.** A1 must **not** re-measure this; it cites E0. A1's scope is the background
region only, and its plan should say so in one line.

---

## 2. The narrow summary path (the claimed 48-scalar bottleneck)

### 2.1 Construction and exact dimensionality

**DECISION.** The summary is exactly **48 scalars = 16 superpixels × 3 channels**, and the statistic
is a **mean over the object's superpixels of the 3-channel VQ latent** — *not* a mean RGB colour.
The paper's "≈16 superpixels × 3 mean colours" is right in arithmetic and **wrong in substance**:
the pooled quantity is a learned latent, not colour.

**EVIDENCE.** `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1548-1564` (Localized Masked Pooling):
```python
def LMP(self, fg, mask, n, s):
    res = []
    for b in range(fg.shape[0]):
        img = rearrange(fg[b].cpu(), 'c h w -> h w c')
        m = 1-mask[b].squeeze().cpu()
        segments = slic(img_as_float(img), n_segments=n, sigma=5, mask=m)
        temp_seg = []
        for value in range(1, n+1):
            value_indices = (segments == value)
            if value_indices.any():
                img_subset = fg[b][:, value_indices]
                avg_pooled = img_subset.mean(dim=1)
                temp_seg.append(avg_pooled)
            else:
                temp_seg.append(torch.tensor([0, 0, 0]).to(fg.device))
        res.append(torch.stack(temp_seg))
    return torch.stack(res)
```
- **16 superpixels.** `self.n_super_pix = int(LR_config['n_super_pix'])` at `ddpm.py:1533`;
  `n_super_pix: 16` at `LAKE-RED/ldm/models/ldm/inpainting_big/config_LAKERED.yaml:72`.
- **3 channels each.** `fg` is the 3-channel VQ latent (§1.2). `img_subset.mean(dim=1)` reduces the
  spatial axis only, leaving a length-3 vector.
- **Statistic: unweighted spatial mean** of the latent over each superpixel's cells.
- **Fixed width, always.** The loop is `range(1, n+1)` with `torch.tensor([0,0,0])` zero-fill at
  `:1562`, so the tensor is (b, 16, 3) whatever SLIC returns. Nominal width is therefore exactly
  **48**; *effective* width is lower whenever SLIC yields fewer than 16 occupied labels (the old
  package's figure was 45.75/48 over 20 samples — `REBUILD_PLAN.md:336-339`, an **unverified** old
  number that A1 should regenerate, not quote).
- **`img_as_float(img)` is applied to a latent, not an image** (`:1553`). skimage's float branch
  expects values in [−1, 1]; VQ f4 latents routinely exceed that. E0's `--seed 0` regeneration
  completed and was bit-exact (`rebuild/E0/E0.md` §5, threshold s4), so in practice it does not
  raise on this stack — but A1's trace should log `fg.min()/fg.max()` and whether a warning is
  emitted, because a clipped or rescaled SLIC input changes which superpixels exist.

**STATUS: settled on dimensionality (48 = 16 × 3).** **needs-my-call** on one wording point: the
paper says "mean colours"; the code pools the VQ latent. See §6(d)(1).

### 2.2 Where the summary goes, and its spatial layout

**DECISION.** The 48 scalars pass through an MLP, a **cross-attention over a fixed 8192-entry
codebook**, and a second MLP, yielding another 48 scalars. Those are then painted as **16 horizontal
bands** across the whole 128×128 latent and fused **per-position** with `fg`. Injection into the
diffusion model is by **channel concatenation**, not cross-attention.

**EVIDENCE.** `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1574-1591`:
```python
vec_fg = self.LMP(fg, mask, self.n_super_pix, 5)          # b 16 3
vec_fg_q = self.mlp_in(vec_fg)                             # b 16 3
code_book = self.bg_embed.transpose(1,0).unsqueeze(0).repeat(...)   # b 8192 3
bg_emb  = self.crossAttn(vec_fg_q, code_book)              # b 16 3
vec_bg  = self.mlp_out(bg_emb)                             # b 16 3
vec_bg  = rearrange(vec_bg, 'b n c -> b c n')              # b 3 16
vec_bg  = vec_bg.unsqueeze(3).expand(-1,-1, -1, self.n_super_pix)   # b 3 16 16
vec_bg  = torch.nn.functional.interpolate(vec_bg, size=[128,128], mode='nearest')
fg2bg   = self.fuse(torch.cat((vec_bg, fg),dim=1))
new_fg  = fg*(1-mask) + fg2bg*mask
new_cond = torch.cat((new_fg, mask), dim=1)
```
- Widths are 3 throughout: `mlp_in = Mlp(3, 6, 3)`, `mlp_out = Mlp(3, 6, 3)`
  (`ddpm.py:1522-1532`); `crossAttn = CrossAttention(3, 3)` (`:1527`) which internally lifts to
  `8 heads × 64 = 512` and projects back to 3 (`ldm/ldm/modules/attention.py:153-168`). Token count
  stays 16. So the branch is **48 scalars in, 48 scalars out** — the bottleneck is genuine *for this
  branch*.
- The codebook `bg_embed` is a `register_buffer` of shape (3, 8192) (`ddpm.py:1519-1520`), **learned
  and present in the checkpoint** — measured this audit: `model.SBG_module.bg_embed (3, 8192)`. It
  is a buffer, so it is not EMA-shadowed; the EMA state carries only the MLP/attention/fuse
  parameters.
- **Spatial layout is degenerate.** `unsqueeze(3).expand(...)` at `:1585` replicates along the
  *last* axis, so axis 2 is the **superpixel token index** and axis 3 is a broadcast. Nearest-upsampled
  to 128×128, token *i* becomes horizontal band *i* spanning the full width. SLIC labels are assigned
  in roughly raster order, so there is a loose vertical correspondence and **no horizontal
  correspondence at all** to where each superpixel actually was. Worth one sentence in the paper: the
  summary is not merely narrow, it is spatially scrambled.
- **Injection is concatenation.** `conditioning_key == 'concat'` (from `concat_mode: true`,
  `config_LAKERED.yaml:14`, resolved at `ddpm.py:454-455`), taking the branch at `ddpm.py:1463-1468`.
  No cross-attention into the UNet: `context` is never passed, and `context_dim` is unset in
  `unet_config`.

**STATUS: settled.**

### 2.3 Is the summary computed from the foreground or the background?

**DECISION.** From the **foreground**. This part of the paper's framing is **correct**.

**EVIDENCE.** `ddpm.py:1552-1553` — SLIC is masked by `1-mask`, which is non-zero exactly where
`mask ≠ 1`, i.e. on the object (§1.1). `ddpm.py:1556-1559` pools `fg` only at `value_indices`, which
are SLIC labels and therefore lie inside that mask. The `mask` here is the {−1,+1} tensor, so
`1-mask ∈ {2, 0}`; SLIC coerces its `mask` argument to boolean, and `2 → True`, so the intended
object region is selected. Corroborated by the early-exit at `ddpm.py:1570-1572`:
`if not self.training and (1 - mask).sum() == 0: return cond, 0` — guarding the case with **no
object**, commented "Extremely small obeject".

**STATUS: settled.** The 48 numbers do summarise the foreground. The "48-scalar *foreground*
bottleneck" framing is not wrong about *what* is summarised — it is wrong about it being the **only**
route (§3).

---

## 3. The full-resolution path(s) — the decisive section

### 3.1 The route the plan names (`fuse`), and its learned weight

**DECISION.** The route exists, is **architecturally active**, and is **not learned away**. The `fuse`
1×1 convolution devotes **more** weight norm to `fg` than to the 48-scalar summary.

**EVIDENCE.**
- `LAKE-RED/ldm/ldm/models/diffusion/ddpm.py:1587` —
  `fg2bg = self.fuse(torch.cat((vec_bg, fg), dim=1))`. `self.fuse = nn.Conv2d(6, 3, kernel_size=1)`
  (`:1534`). So `fg` enters at **full latent resolution** (128×128), and by `:1590` `fg2bg` is
  precisely what fills every `mask == 1` position.
- `kernel_size=1` means the fuse itself performs **no spatial mixing**: position (i,j) of `fg2bg`
  depends on `fg` only at (i,j). This bounds *this* route to per-position leakage — it is not, on its
  own, a global foreground→background channel.
- **Measured from the checkpoint (this audit, read-only):**
  `model.SBG_module.fuse.weight` has shape (3, 6, 1, 1) with values
  ```
  [[ 0.3502,  0.1546,  0.3714,   0.1383, -0.1134, -0.2859],
   [-0.2784, -0.2797,  0.3522,  -0.3708, -0.3564, -0.4090],
   [ 0.2693, -0.0132, -0.1353,   0.0252, -0.4010,  0.3406]]
   |___ vec_bg block ____|      |______ fg block ______|
  ```
  `‖vec_bg block‖₂ = 0.8095`, `‖fg block‖₂ = 0.9072`, ratio **fg/vec_bg = 1.12**. The EMA copy
  (`model_ema.SBG_modulefuseweight`, which is what `test.py:122` `model.ema_scope()` actually uses)
  agrees to 3 decimals: 0.8088 / 0.9073, ratio 1.12.
  Reproduce with:
  ```
  LAKE-RED/.venv/bin/python -c "import torch;sd=torch.load('LAKE-RED/ckpt/LAKERED.ckpt',map_location='cpu',weights_only=False)['state_dict'];print(sd['model.SBG_module.fuse.weight'].view(3,6))"
  ```
  **Reading:** training did not suppress the `fg` half. The generator weights the raw
  full-resolution latent at least as heavily as the 48-scalar summary when synthesising background
  conditioning.

**STATUS: settled** — this route is active. What it *carries* is §3.2.

### 3.2 Is `fg` zero (or foreground-independent) under the mask?

**DECISION. No — on both counts, and this is determinable statically.** `fg[mask==1]` cannot be
identically zero, and it is not even independent of foreground content.

**EVIDENCE (three separate reasons, in increasing importance).**
1. **Bias terms.** In the background, `masked_image = −1` (§1.2: `0 * 2 − 1`). The VQ encoder is a
   deep conv stack with biased convolutions ending in `conv_out` then `quant_conv`
   (`ldm/ldm/models/autoencoder.py:268-269`). A constant input maps to a *constant*, generically
   **non-zero**, latent value. Zero would be coincidence.
2. **Local receptive-field spill.** The first-stage encoder is `attn_type: none`,
   `attn_resolutions: []` (`config_LAKERED.yaml:51,63`), so it is purely convolutional and its
   receptive field is bounded — but not small. Latent cells within that radius of the object
   boundary see real object pixels. So near-boundary background cells carry genuine
   full-resolution foreground content. Plus the ~1 px dilation ring of §1.3, which puts *literal*
   object pixels at `mask == 1` positions.
3. **GroupNorm makes it global.** `ldm/ldm/modules/diffusionmodules/model.py:38-39` —
   `Normalize` is `torch.nn.GroupNorm(num_groups=32, ..., affine=True)`, used throughout the encoder.
   GroupNorm normalises over `(C/G, H, W)` — **the whole spatial extent**. Every latent position is
   therefore a function of the global statistics of the input, which include every foreground pixel.
   `fg` in the deep background is not "the encoding of black"; it is "the encoding of black *given
   this particular foreground's global statistics*."

**Consequence for the paper's stated decisive check.** `main.tex:602-604` names the check as
"whether the foreground tensor is identically zero under the mask", and `REBUILD_PLAN.md:250-251`
makes `fg[mask==1]` identically zero a **confirm** condition. That condition is **architecturally
unsatisfiable**. A1 as currently planned can only ever return "refuted". Worse, it is also
**insufficient** — see §3.3. The check must be replaced, not run.

**Exactly which tensor, at which line.** The tensor named by the plan is `fg` as bound at
`ddpm.py:1567` (`fg, mask = cond[0].split(3, 1)`), inspected at its `mask == 1` positions — i.e.
immediately before its use at `:1587`. A1 can capture it with a forward hook on
`model.model.SBG_module` or by re-running `test.py:128-134` standalone and calling
`SBG_module.forward` directly. **This needs no diffusion sampling at all** — one VQ encode is
enough, seconds per sample.

**STATUS: settled by static reading** (bias terms + GroupNorm). A runtime read is worth doing anyway
to *quantify* it — see §4.3 — but not to decide it.

### 3.3 The route the plan misses, and which dominates

**DECISION.** The dominant full-resolution foreground→background path is not inside BKRA at all.
`new_fg` **retains the full-resolution foreground latent in the object region**, that tensor is
concatenated into the UNet input, and the UNet contains **global spatial self-attention**. So
background output positions can read object-region conditioning at full latent resolution, with no
bottleneck and no leakage argument required.

**EVIDENCE.**
- `ddpm.py:1590-1591` — at object positions (`mask = −1`), `new_fg = 2·fg − fg2bg`. Not zeroed, not
  summarised: an amplified copy of the foreground latent. `new_cond = torch.cat((new_fg, mask), 1)`.
- `ddpm.py:1467-1468` — `xc = torch.cat([x] + c_concat, dim=1); out = self.diffusion_model(xc, t)`.
  The 3 channels of `new_fg` — object region included — are UNet input channels 3:6.
- `ldm/ldm/modules/diffusionmodules/openaimodel.py:318-324`:
  ```python
  def _forward(self, x):
      b, c, *spatial = x.shape
      x = x.reshape(b, c, -1)
      qkv = self.qkv(self.norm(x))
      h = self.attention(qkv)
  ```
  `AttentionBlock` flattens all spatial positions into one sequence — **unmasked, global
  self-attention**, as its own docstring says ("allows spatial positions to attend to each other",
  `:280`).
- Attention is instantiated at `openaimodel.py:541` (`if ds in attention_resolutions`) with
  `ds` doubling at `:586`, and unconditionally in the middle block at `:606`.
  `attention_resolutions: [8, 4, 2]` (`config_LAKERED.yaml:32-35`) with a 128×128 latent puts global
  self-attention at 64×64, 32×32 and 16×16, plus the middle block. So the UNet's receptive field over
  its own conditioning channels is **the entire image**.

**Reading.** Even if `fg` were identically zero under the mask, and even if the `fuse` fg-block
weights were zero, the UNet would still see the full-resolution foreground latent and could still
route it anywhere in the background through self-attention. The 48-scalar bottleneck constrains the
**BKRA branch only**. It does not constrain the **conditioning of the generator**, which is what
§6(ii) claims.

**STATUS: settled.** This is the single most important finding of the audit.

### 3.4 Complete route inventory

| # | Route | Resolution | Spatial reach | Active at inference | Evidence |
|---|---|---|---|---|---|
| R0 | `isReplace` paste-back | original px | object region only | **yes** | `test.py:159-166`; `run_hkuis.sh:28`; E0 ratio 12.64 |
| R1 | LMP → BKRM → `vec_bg` (**48 scalars**) | 16 bands ← 48 scalars | **global** | **yes** | `ddpm.py:1548-1586` |
| R2 | `fg` into `fuse` (1×1) | full latent (128²) | per-position; global only via encoder GroupNorm, local via receptive field + dilation ring | **yes**, weight ratio 1.12 | `ddpm.py:1587`; ckpt `fuse.weight`; `model.py:38-39` |
| R3 | `new_fg` object region → UNet input → **global self-attention** | full latent (128²) | **global, unbottlenecked** | **yes** | `ddpm.py:1590,1467`; `openaimodel.py:318-324,541,606`; `config_LAKERED.yaml:29,32-35` |

R0 is out of scope (§1.4). R1 is the paper's claim. **R2 and R3 together refute it**, and R3 does so
without needing any quantification.

---

## 4. What A1 can conclude, and its honest limits

### 4.1 Static or runtime?

**DECISION.** **Both**, but with the weight inverted from the current plan. The *conclusion* is
static; the runtime work is for **magnitude**, and is optional-but-recommended.

- **Static analysis alone settles the qualitative claim.** §3.3 needs no run: the architecture hands
  the full-resolution foreground latent to a globally-attending UNet. §3.1's weight measurement is a
  checkpoint read, already done above. §3.2's "not identically zero" follows from GroupNorm and bias
  terms.
- **Runtime is needed only to answer "how much".** Static reading establishes the channel is *not*
  narrow; it does not say whether the extra capacity is *used* to a degree that matters. If the
  paper wants to say anything quantitative in §6(ii), a run is required. If it retreats to "the
  architecture does not bound this", static suffices.

**Recommendation (minimal sufficient design), three tiers:**

- **A1-S (static, mandatory).** Document R0–R3 with the citations in §§1–3; report `fuse` weight
  norms from the checkpoint; report nominal width 48 and the layout degeneracy of §2.2. **No GPU
  sampling.** This alone lets §6(ii) be rewritten honestly.
- **A1-T (trace, cheap, recommended).** One VQ encode per sample over N ≈ 50 real HKU-IS samples,
  no diffusion. Log: live `vec_fg.shape`; per-sample SLIC occupancy (effective width out of 48);
  `fg[mask==1]` statistics — mean, sd, `max|·|`, fraction exactly zero; and the **between-sample sd
  of `fg[mask==1]` at matched positions under a fixed mask**, which is the direct measure of how much
  foreground identity survives into the background half of the conditioning tensor. Minutes, one GPU.
- **A1-P (perturbation, only if a number is wanted for §6(ii)).** §4.2.

### 4.2 If a runtime experiment is run: the clean design

The honest form of "does foreground content beyond the summary influence the output" is a
**perturbation with the summary held fixed and the noise held fixed**.

**Design.**
1. Take one real sample. Run the pipeline verbatim through `test.py:128-134` to get `cond`.
2. **Fix the noise.** Draw `x_T = torch.randn(shape, generator=g)` from an explicitly seeded
   generator and pass it through: `sampler.sample(..., x_T=x_T)`. `x_T` is accepted at
   `ldm/ldm/models/diffusion/ddim.py:73` and threaded to `:105` and `:121-124`. **This is essential.**
   `test.py:90-92` seeds once per process, and `ddim.py:122` plus the `noise_like` call at `ddim.py:35`
   (still invoked though multiplied by `sigma_t = 0` at `eta=0.`, `ddim.py:65`) draw from the global
   RNG, so any change in call order or count silently changes the noise. Passing `x_T` removes the
   entire class of confound.
3. **Arm A:** unmodified `cond`.
   **Arm B:** perturb the foreground latent — e.g. spatially permute `fg` *within* the object region,
   or swap in another sample's object latent — chosen so that **`vec_fg` is unchanged to numerical
   tolerance** (a within-superpixel permutation preserves every superpixel mean exactly, which is the
   cleanest construction: it holds all 48 numbers *identically* fixed while changing every
   full-resolution value).
   Assert `‖vec_fg_A − vec_fg_B‖∞ < 1e-6` before sampling. If that assertion cannot be met, the arm
   is invalid and must be reported as such rather than softened.
4. Decode both, and compare **only at `mask == 1`** (background), at the original resolution, before
   any `isReplace` paste and before JPEG. Metric: per-pixel MAE over the background.
5. **Control arm (mandatory).** Same sample, same `x_T`, `cond` byte-identical: MAE must be **0**.
   This proves the harness is deterministic and that any Arm-A-vs-B difference is attributable to the
   perturbation and not to the pipeline. E0 established bit-exactness at `--seed 0` on this stack
   (`rebuild/E0/E0.md` §5, s4), so a non-zero control is a harness bug, not a finding.

**Decision rule, declared before the run.**
- **"The narrow channel binds"** — background MAE(A, B) is at the control's floor, i.e.
  **≤ 1/255 (one quantisation level)** and not distinguishable from the control across all N samples.
  Only this outcome supports the §6(ii) claim as written.
- **"It does not bind"** — background MAE(A, B) is materially above the control floor. Suggested
  pre-declared threshold: median background MAE **≥ 1.0/255** across N samples, with the control at 0.
  A1 should additionally report the *distribution* over N and an object-boundary-distance breakdown,
  because "leakage confined to a 4-cell boundary band" and "leakage across the whole frame" are
  different claims and R2-vs-R3 predicts different answers (R2 → boundary-concentrated;
  R3 → frame-wide).
- **N.** 50 samples is enough to state a median and a range; this is a mechanism check, not an
  effect-size estimate, and no inferential test should be attached to it.

**Note.** Given §3.3, the expected outcome is "does not bind". A1's plan should nonetheless declare
the threshold in advance and report whatever comes back — including the possibility that the
measured leakage is frame-wide but small, which is a *third* outcome the paper does not currently
have language for (§6(c)).

### 4.3 What A1 cannot establish, even if perfectly executed

State these in `A1_RESULTS.md` as explicitly as A3 does (`main.tex:683`):

1. **It bounds the architectural channel, not the training benefit.** A1 says how much foreground
   information *can* reach the background. It says nothing about whether a *richer* conditioning
   interface would have improved anything — that would require retraining the generator with a wider
   interface and re-running the loop, which is a separate and untested question.
2. **It does not measure whether the capacity is used semantically.** A non-zero background MAE shows
   foreground content perturbs the output. It does not show the generator uses that content to
   *adapt the background to the object*. Those are different claims and A1 can only reach the first.
3. **It does not license the converse.** Even the "binds" outcome would not show the bottleneck
   *caused* the null result in §5; it would only make the bottleneck a viable explanation. The
   paper's "plausible but unverified cause" framing must survive in weakened form either way.
4. **It says nothing about the checkpoint's training regime.** `bg_embed` is a learned buffer of
   8192 entries (§2.2); whether it is well-used, collapsed, or near-random is a separate probe that
   A1 should not silently fold in.
5. **Generator-source provenance.** `LAKE-RED/` is untracked here, so A1's citations are pinned only
   by the hashes A1 itself records (§5).

---

## 5. Determinism and provenance for any runtime trace

**DECISION.** A1 reuses E0's discipline unchanged, with **one addition** (explicit `x_T`) that E0 did
not need.

| Requirement | How A1 satisfies it | Evidence / precedent |
|---|---|---|
| Same seed convention | `--seed 0` default, stamped via `common.env_stamp(seed)` | `rebuild/common.py:287`; `rebuild/E0/e0_regenerate.py:638,647` |
| Determinism **stronger** than E0's | Pass explicit `x_T` from a seeded `torch.Generator`; do **not** rely on process-level `torch.manual_seed` | `ddim.py:73,105,121-124`; the global draws at `ddim.py:122` and `:35` are order-sensitive (§4.2 step 2) |
| Determinism **proven**, not assumed | The byte-identical control arm (§4.2 step 5) must give MAE exactly 0 | E0 s4 achieved bit-exact reproduction at seed 0 on this stack (`rebuild/E0/E0.md` §5) |
| Reads only primary data | Resolve inputs through `common.INPUTS` — `lr_in_img`, `lr_in_mask`, `raw`, `raw_gt` | `rebuild/common.py:49-58`; E0.md §3 "Read" table |
| Touches no archive / scratchpad | Inherits the s5 gate; A1's script must pass it | `FORBIDDEN_PATHS` / `FORBIDDEN_IMPORTS` at `rebuild/E0/e0_regenerate.py:539-541` |
| Per-experiment directory | Writes only under `rebuild/A1/` — `out/` (text, in git), `cache/` and `regen/` if any (gitignored, regenerable). Nothing under `Dataset/`, nothing over the existing pools | E0.md §3 "Written" table |
| Generator sources pinned | SHA256 `LAKE-RED/{test.py, ldm/ldm/models/diffusion/ddpm.py, ldm/ldm/models/diffusion/ddim.py, ldm/ldm/modules/diffusionmodules/openaimodel.py, ldm/ldm/modules/diffusionmodules/model.py, ldm/ldm/models/autoencoder.py, ldm/ldm/modules/attention.py, ldm/models/ldm/inpainting_big/config_LAKERED.yaml}` into `rebuild/A1/out/a1_source_manifest.sha256` | **new for A1** — necessary because `LAKE-RED/` is untracked and every claim above is a line citation |
| Checkpoint pinned | Record the `fuse`/`bg_embed` tensor digests, and cite E0's existing hash of `LAKERED.ckpt` rather than re-hashing 6.4 GB | E0.md §3; C3's precedent of hashing the specific checkpoints it loads |
| One log block | Exactly one `EXP A1` block appended to `results/REBUILD_LOG.txt` via `common.log_block`, with thresholds declared before the run | `rebuild/common.py:319`; `REBUILD_PLAN.md` §Verification |
| Old claims confronted | The block must carry `A1.1`–`A1.4` from `REBUILD_PLAN.md:336-339` as `old_claims`, including `A1.4` ("`fg` under mask is zero — *never tested*") | `REBUILD_PLAN.md:336-339,429` |

**STATUS: settled**, except that A1's script does not yet exist (`rebuild/A1/` contained nothing
before this file).

---

## 6. Closing summary

### (a) The single most important finding

**A full-resolution foreground→background path exists, and it is active at inference. It is not the
path the plan was looking for, and it is not marginal.**

Stated as precisely as the code allows:

> `new_fg` (`ddpm.py:1590`) retains the foreground latent at full resolution in the object region;
> that tensor is concatenated into the UNet's input channels (`ddpm.py:1467`, `in_channels: 7`); and
> the UNet applies **unmasked global spatial self-attention** at three resolutions plus its middle
> block (`openaimodel.py:318-324,541,606`; `attention_resolutions: [8,4,2]`). Background output
> positions can therefore read object-region conditioning at full latent resolution. Separately, the
> `fuse` 1×1 convolution (`ddpm.py:1587`) admits the raw `fg` latent into every regenerated position
> with a **larger** learned weight norm than the 48-scalar summary receives (0.907 vs 0.810, ratio
> 1.12, measured from the released checkpoint), and `fg` under the mask is neither zero nor
> foreground-independent — the first-stage encoder's GroupNorm (`model.py:38-39`) makes every latent
> position a function of the whole input's statistics.

The 48-scalar figure is correct **as a description of the BKRA branch** and incorrect **as a
description of the generator's conditioning channel**. The paper's §6(ii) sentence "in this generator
the foreground reaches the background synthesis through a deliberately narrow summary" is not
supportable and must be rewritten.

### (b) Static, runtime, or both

**Static analysis is sufficient for the conclusion; a cheap runtime trace is recommended for
magnitude, and a perturbation run is required only if §6(ii) is to carry a number.**

Concretely: run **A1-S** (mandatory, no GPU sampling) + **A1-T** (recommended, minutes) and treat
**A1-P** as optional and gated on your answer to §6(d)(3). The current plan has this backwards — it
makes the runtime check decisive when the decisive fact is static, and it names a confirm condition
that the architecture cannot satisfy.

### (c) The exact claim A1 will be able to make for §6(ii), three ways

**(c-1) — Narrow channel REFUTED.** *This is the outcome the static analysis already forces; the
other two are retained because you asked for all three and because A1-P could still surprise us on
magnitude.*

> **(ii) The conditioning channel. [T1, measured — the earlier framing was wrong]**
> We had described the generator as passing foreground information to background synthesis through a
> deliberately narrow summary, and named the resulting bound as a plausible cause. Reading the
> generator's source settles it against us. The narrow summary is real — the foreground is reduced
> to 16 superpixel means of a 3-channel latent, 48 scalars, which are re-expanded into 16 horizontal
> bands with no horizontal spatial correspondence. But it is one of several routes, not the only one.
> The same module admits the full-resolution foreground latent into every regenerated position
> through a 1×1 convolution whose foreground weights are, in the released checkpoint, larger in norm
> than its summary weights; and the conditioning tensor handed to the diffusion UNet retains the
> foreground latent at full resolution in the object region, where the UNet's global spatial
> self-attention can read it from any background position. The channel is therefore not narrow, and
> a conditioning bottleneck is **not** available as an explanation for the null result. We withdraw
> it.

**(c-2) — Narrow channel CONFIRMED** *(would require `fg` provably inert under the mask **and** no
UNet route — neither holds; retained for completeness only)*:

> **(ii) The conditioning channel. [T1, measured]**
> The foreground reaches background synthesis through a 48-scalar summary and through no other
> active route: the full-resolution foreground tensor is inert under the mask, and perturbing
> foreground pixels while holding all 48 summary values identically fixed leaves the generated
> background unchanged to within one quantisation level. The channel is therefore genuinely narrow,
> which bounds how much of any selected difference a selection policy can express. We record this as
> a measured bound on the mechanism — not as a demonstration that it caused the null result.

**(c-3) — Genuinely UNDETERMINABLE.** *The one live route to this outcome is not "we could not read
the code" — we could — but the third measurement outcome of §4.2: leakage that is real, frame-wide,
and too small to interpret.*

> **(ii) The conditioning channel. [T1, partially measured]**
> The architecture provides more than the narrow summary: alongside the 48-scalar reduction, the
> full-resolution foreground latent reaches both the fused conditioning and the UNet's globally
> attending input. So the channel is not narrow in the architectural sense. Whether the additional
> capacity carries information the generator actually uses, we cannot say: perturbing the foreground
> with the summary held fixed changes the generated background measurably but by a margin we are not
> willing to interpret. We therefore assert neither a bound nor its absence, and we do not offer
> conditioning width as an explanation of the null result in either direction.

**Also to update if A1 runs:** `main.tex:559` (the §6 summary table row "(ii) Generator conditioning
width | Not measured..."), `main.tex:1086-1090` (the not-established list), `main.tex:133`
("a conditioning bottleneck we explicitly could not measure"), `main.tex:888` ("whether the present
conditioning interface is the binding constraint is precisely the measurement we could not make"),
and `REBUILD_PLAN.md:336-339` + `:429`.

### (d) Your decisions, needed before the plan prompt can be written

1. **The paper says "mean colours"; the code pools the VQ latent (§2.1).** Rewrite as
   "16 superpixel means of a 3-channel latent"? It is still 48 scalars, so the arithmetic survives,
   but "mean colours" is inaccurate and a reviewer who opens `ddpm.py:1558` will see it.
2. **Does A1's scope expand to cover R3 (§3.3), or does R3 become a separate finding?** R3 is the
   decisive route and it lives in the UNet, not in BKRA — outside the "conditioning width" framing
   A1 was given. My recommendation: **expand A1**, because the question §6(ii) actually asks is
   "can foreground information reach the background", and answering it while ignoring the UNet would
   repeat the exact error the audit was commissioned to catch. But it does widen A1 beyond
   `REBUILD_PLAN.md:245-252`.
3. **Do you want a number in §6(ii), or a withdrawal?** If withdrawal (c-1), A1-S + A1-T is enough
   and no GPU sampling is needed. If a number, A1-P must run (§4.2) — ~1 GPU-hour for N = 50 at 50
   DDIM steps × 3 arms, plus harness work.
4. **`REBUILD_PLAN.md:250-251`'s confirm condition is unsatisfiable (§3.2).** Do I rewrite that
   plan entry as part of A1, or leave the plan as the historical record and let `A1_RESULTS.md`
   record that the pre-registered condition was ill-posed? The rebuild's own discipline
   ("regenerate, don't rescue"; declare thresholds before the run) argues for **amending the plan
   explicitly and dating the amendment**, not silently substituting a different check.
5. **Old numbers `A1.1`–`A1.3` (`REBUILD_PLAN.md:336-339`)** — 48, `(1,16,3)`, effective width
   45.75 — come from the old package. `A1.1` I have now confirmed statically. Should A1-T regenerate
   `A1.2` and `A1.3`, or may `A1.3` be dropped as decoration now that the width question is settled
   against the narrow-channel account? My recommendation: regenerate both, since A1-T is minutes and
   the effective-width figure is the one quantitative thing about R1 the paper could still keep.
6. **Perturbation construction for A1-P (§4.2 step 3).** Within-superpixel permutation is the only
   construction I can see that holds all 48 summary scalars *exactly* fixed. Accept that, or do you
   want a foreground swap with a numerically-matched-summary tolerance instead (weaker assertion,
   more natural perturbation)?

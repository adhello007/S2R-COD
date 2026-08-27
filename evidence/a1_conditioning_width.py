"""A1 -- Conditioning-width measurement.

=============================================================================
GOAL
    Establish, from three independent sources, that LAKE-RED's entire steerable
    foreground -> background channel is 16 superpixels x 3 mean colour values =
    48 scalars.

WHY IT MATTERS -- how this fits the argument
    This is load-bearing conclusion (i) of the evidence package: "the generator
    is near-unsteerable." Stage C's whole proposal is to *aim* the generator at
    a chosen target cluster. A1 measures the width of the only channel through
    which the foreground can influence the generated background. Paired with A2
    (which shows ~82% of every output is invented background), it says: we are
    steering 82% of the picture through 48 numbers.

    It is also the basis for the one forward path we identify -- widening this
    channel at ddpm.py:1579 -- so the number has to be exact, not approximate.

WHAT "48" IS, PRECISELY
    48 is the width of the CONDITIONING CHANNEL, not the model's capacity. The
    U-Net is unconstrained and the retrieval codebook holds 8192 entries. The
    claim is narrower and stronger: the foreground reaches the background
    generator only as 48 scalars, and those 48 scalars are what addresses the
    8192-entry codebook. The bottleneck is the query, not the codebook.

METHOD -- three independent confirmations
    Panel 1  config + source. n_super_pix is read from the YAML, and the source
             lines that consume it are quoted, showing LMP returns b x n x 3.
    Panel 2  the TRAINED WEIGHTS, independent of the config. The checkpoint's
             own tensor shapes prove the per-superpixel width is 3.
    Panel 3  a LIVE forward pass of the real BKRA module with real checkpoint
             weights on a real image/mask pair, capturing vec_fg's actual shape
             via a hook on mlp_in (the tensor entering ddpm.py:1577).
    Panel 4  occupancy. LMP zero-fills superpixels that SLIC leaves empty, so
             48 is an UPPER bound; this measures the effective width on real
             samples.

SOURCE REPRODUCED
    STAGE_C_MEASUREMENTS.md section 6.1: "LAKE-RED's entire steerable channel is
    16 superpixels x 3 mean-colour channels = 48 numbers (ddpm.py:1548-1590)".

REVISION SURFACED
    None. This number has never moved.

TRAINS ANYTHING?
    NO. One forward pass of a small conditioning module, inference only.

USAGE
    LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py [--samples 20]
=============================================================================
"""

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

DDPM = 'LAKE-RED/ldm/ldm/models/diffusion/ddpm.py'
CONFIG = 'LAKE-RED/ldm/models/ldm/inpainting_big/config_LAKERED.yaml'
CKPT = 'LAKE-RED/ckpt/LAKERED.ckpt'
IMGS = 'Dataset/LAKERED/input/HKU-IS/validation/images'
MASKS = 'Dataset/LAKERED/input/HKU-IS/validation/masks'

CHANNELS_PER_SUPERPIXEL = 3      # mean R, G, B per superpixel
EXPECTED_WIDTH = 48              # the number under test

# Source lines that define the channel, quoted into the CSV for the reader.
KEY_LINES = {
    1533: 'self.n_super_pix = int(LR_config[\'n_super_pix\'])',
    1553: 'segments = slic(img_as_float(img), n_segments=n, sigma=5, mask=m)',
    1574: 'vec_fg = self.LMP(fg, mask, self.n_super_pix, 5)   # b n 3',
    1577: 'vec_fg_q = self.mlp_in(vec_fg)',
    1579: 'bg_emb = self.crossAttn(vec_fg_q, code_book)',
}


def panel1_config_and_source(repo):
    """n_super_pix from the YAML, plus the source lines that consume it."""
    text = open(os.path.join(repo, CONFIG)).read()
    m = re.search(r'^\s*n_super_pix:\s*(\d+)', text, re.M)
    if not m:
        sys.exit('FATAL: n_super_pix not found in %s' % CONFIG)
    n_super_pix = int(m.group(1))
    line_no = text[:m.start()].count('\n') + 1

    src = open(os.path.join(repo, DDPM)).readlines()
    quoted = {}
    for ln in sorted(KEY_LINES):
        quoted[ln] = src[ln - 1].strip()

    # LMP appends one 3-vector per superpixel index, including empty ones.
    lmp = ''.join(src[1547:1565])
    returns_bn3 = ('avg_pooled = img_subset.mean(dim=1)' in lmp
                   and 'torch.tensor([0, 0, 0])' in lmp
                   and 'torch.stack' in lmp)
    return n_super_pix, line_no, quoted, returns_bn3


def panel2_from_weights(repo):
    """Per-superpixel width read off the TRAINED weights, not the config."""
    import torch
    sd = torch.load(os.path.join(repo, CKPT), map_location='cpu',
                    weights_only=False)
    sd = sd.get('state_dict', sd)
    pre = 'model.SBG_module.'
    sub = {k[len(pre):]: v for k, v in sd.items() if k.startswith(pre)}
    if not sub:
        sys.exit('FATAL: no model.SBG_module.* keys in %s' % CKPT)
    shapes = {
        'mlp_in.fc1.weight': tuple(sub['mlp_in.fc1.weight'].shape),
        'mlp_out.fc2.weight': tuple(sub['mlp_out.fc2.weight'].shape),
        'crossAttn.to_q.weight': tuple(sub['crossAttn.to_q.weight'].shape),
        'bg_embed': tuple(sub['bg_embed'].shape),
    }
    # mlp_in maps each superpixel token from R^d -> ... ; d is its input width.
    token_width = shapes['mlp_in.fc1.weight'][1]
    codebook_entries = shapes['bg_embed'][1]
    attn_inner = shapes['crossAttn.to_q.weight'][0]
    return sub, shapes, token_width, codebook_entries, attn_inner


def _load_pair(repo, stem, size=128):
    import cv2
    import numpy as np
    import torch
    img = cv2.imread(os.path.join(repo, IMGS, stem + '.jpg'), cv2.IMREAD_COLOR)
    msk = cv2.imread(os.path.join(repo, MASKS, stem + '.png'), cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    msk = cv2.resize(msk, (size, size), interpolation=cv2.INTER_NEAREST)
    fg = torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                          .astype('float32') / 127.5 - 1.0).permute(2, 0, 1)[None]
    # mask == 1 marks the region the generator invents; 1-mask is the kept
    # foreground, which is what LMP segments (ddpm.py:1552).
    mk = torch.from_numpy((msk > 127).astype('float32'))[None, None]
    return fg, mk


def panel3_live_forward(repo, sub, n_super_pix, stem):
    """Real BKRA, real weights, real sample -> vec_fg's actual shape."""
    import torch
    import yaml
    sys.path.insert(0, os.path.join(repo, 'LAKE-RED/ldm'))
    from ldm.models.diffusion.ddpm import BKRA

    cfg = yaml.safe_load(open(os.path.join(repo, CONFIG)))
    lr_cfg = cfg['model']['params']['LR_config']
    bkra = BKRA(lr_cfg)
    missing, unexpected = bkra.load_state_dict(sub, strict=False)
    bkra.eval()
    # rec_loss is left exactly as the config sets it (true) so the live pass runs
    # the real code path; BKRA.get_loss is defined at ddpm.py:1598.

    captured = {}

    def hook(_mod, inp, _out):
        captured['vec_fg'] = tuple(inp[0].shape)   # the tensor at ddpm.py:1577

    h = bkra.mlp_in.register_forward_hook(hook)
    fg, mk = _load_pair(repo, stem)
    with torch.no_grad():
        # BKRA.forward returns ([new_cond], bgrec_loss) -- ddpm.py:1596
        new_cond, bgrec = bkra([torch.cat((fg, mk), dim=1)], fg)
    h.remove()
    return (captured.get('vec_fg'), tuple(new_cond[0].shape),
            len(missing), len(unexpected), bkra,
            'computed' if bgrec is not None else 'None')


def panel4_occupancy(repo, bkra, n_super_pix, stems):
    """LMP zero-fills empty superpixels, so 48 is an UPPER bound. Measure the
    effective width on real samples."""
    import torch
    rows = []
    for stem in stems:
        fg, mk = _load_pair(repo, stem)
        with torch.no_grad():
            vec = bkra.LMP(fg, mk, n_super_pix, 5)      # (1, n, 3)
        nonzero = int((vec[0].abs().sum(dim=1) > 0).sum())
        rows.append({'stem': stem,
                     'superpixels_requested': n_super_pix,
                     'superpixels_nonempty': nonzero,
                     'effective_width': nonzero * CHANNELS_PER_SUPERPIXEL,
                     'fg_fraction': round(float(1.0 - mk.mean()), 4)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--samples', type=int, default=20,
                    help='how many real samples for the occupancy panel')
    ap.add_argument('--seed', type=int, default=C.SEED)
    opt = ap.parse_args()
    repo = C.REPO

    # ---- Panel 1: config + source -------------------------------------
    n_super_pix, cfg_line, quoted, returns_bn3 = panel1_config_and_source(repo)

    # ---- Panel 2: trained weights -------------------------------------
    sub, shapes, token_width, codebook_entries, attn_inner = panel2_from_weights(repo)

    # ---- Panel 3: live forward ----------------------------------------
    stems = sorted(os.path.splitext(f)[0]
                   for f in os.listdir(os.path.join(repo, IMGS)))
    (live_vec, live_cond, n_missing, n_unexpected, bkra,
     bgrec_state) = panel3_live_forward(repo, sub, n_super_pix, stems[0])

    # ---- Panel 4: occupancy -------------------------------------------
    rng = C.rng(opt.seed)
    pick = [stems[i] for i in rng.choice(len(stems), size=min(opt.samples, len(stems)),
                                        replace=False)]
    occ = panel4_occupancy(repo, bkra, n_super_pix, pick)
    eff = [r['effective_width'] for r in occ]
    eff_mean = sum(eff) / len(eff)

    width = n_super_pix * CHANNELS_PER_SUPERPIXEL
    live_numel = live_vec[0] * live_vec[1] * live_vec[2] if live_vec else None

    # ---- outputs -------------------------------------------------------
    os.makedirs(os.path.join(repo, 'evidence', 'out'), exist_ok=True)
    facts_csv = os.path.join(repo, 'evidence', 'out', 'a1_conditioning.csv')
    with open(facts_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['panel', 'key', 'value', 'provenance'])
        w.writerow(['1-config', 'n_super_pix', n_super_pix,
                    '%s:%d' % (os.path.basename(CONFIG), cfg_line)])
        w.writerow(['1-source', 'LMP_returns_b_n_3', returns_bn3,
                    'ddpm.py:1548-1564'])
        for ln in sorted(quoted):
            w.writerow(['1-source', 'ddpm.py:%d' % ln, quoted[ln], DDPM])
        for k, v in shapes.items():
            w.writerow(['2-weights', k, v, 'LAKERED.ckpt model.SBG_module.' + k])
        w.writerow(['2-weights', 'channels_per_superpixel', token_width,
                    'mlp_in.fc1.weight input dim'])
        w.writerow(['2-weights', 'codebook_entries', codebook_entries, 'bg_embed'])
        w.writerow(['2-weights', 'crossattn_inner_dim', attn_inner, 'to_q.weight'])
        w.writerow(['3-live', 'vec_fg_shape', live_vec, 'hook on mlp_in input'])
        w.writerow(['3-live', 'vec_fg_numel', live_numel, 'hook on mlp_in input'])
        w.writerow(['3-live', 'new_cond_shape', live_cond, 'BKRA.forward return'])
        w.writerow(['4-occupancy', 'effective_width_mean', round(eff_mean, 2),
                    '%d real samples' % len(occ)])
        w.writerow(['summary', 'conditioning_width', width,
                    'n_super_pix x channels_per_superpixel'])

    occ_csv = os.path.join(repo, 'evidence', 'out', 'a1_superpixel_occupancy.csv')
    with open(occ_csv, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(occ[0]))
        w.writeheader()
        w.writerows(occ)

    metrics = [
        ('n_super_pix', n_super_pix, '%s:%d' % (os.path.basename(CONFIG), cfg_line)),
        ('channels_per_superpixel', token_width,
         'ckpt mlp_in.fc1.weight %s -> input dim' % (shapes['mlp_in.fc1.weight'],)),
        ('conditioning_width', width, 'n_super_pix x channels_per_superpixel'),
        ('vec_fg_shape_live', live_vec, 'hook on mlp_in input, sample %s' % stems[0]),
        ('vec_fg_numel_live', live_numel, 'live forward'),
        ('new_cond_shape_live', live_cond, 'BKRA.forward return, ddpm.py:1596'),
        ('bgrec_loss_live', bgrec_state, 'rec_loss=true as configured'),
        ('codebook_entries', codebook_entries,
         'bg_embed %s -- addressed BY the 48' % (shapes['bg_embed'],)),
        ('crossattn_inner_dim', attn_inner, 'crossAttn.to_q.weight'),
        ('superpixel_algorithm', 'slic(n_segments=%d, sigma=5, mask=1-mask)' % n_super_pix,
         'ddpm.py:1553'),
        ('effective_width_mean', round(eff_mean, 2),
         '%d real samples; empty superpixels are zero-filled' % len(occ)),
        ('effective_width_range', '%d-%d' % (min(eff), max(eff)), 'same samples'),
        ('ckpt_keys_loaded', '%d loaded, %d missing, %d unexpected'
         % (len(sub), n_missing, n_unexpected), 'load_state_dict(strict=False)'),
    ]

    thresholds = [
        ('conditioning_width == %d' % EXPECTED_WIDTH, width == EXPECTED_WIDTH),
        ('live vec_fg numel == %d' % EXPECTED_WIDTH, live_numel == EXPECTED_WIDTH),
        ('live vec_fg shape == (1, %d, %d)' % (n_super_pix, CHANNELS_PER_SUPERPIXEL),
         live_vec == (1, n_super_pix, CHANNELS_PER_SUPERPIXEL)),
        ('per-superpixel width from WEIGHTS == %d' % CHANNELS_PER_SUPERPIXEL,
         token_width == CHANNELS_PER_SUPERPIXEL),
        ('LMP returns b x n x 3 (source check)', returns_bn3),
        ('all BKRA checkpoint weights load', n_missing == 0),
    ]

    expected = [('conditioning width (STAGE_C_MEASUREMENTS.md 6.1)', EXPECTED_WIDTH,
                 'MATCH' if width == EXPECTED_WIDTH else 'MISMATCH'),
                ('n_super_pix', 16, 'MATCH' if n_super_pix == 16 else 'MISMATCH'),
                ('effective width on real samples', 'not pinned by any source', 'NEW')]

    notes = (
        'PRECISION: 48 is the width of the CONDITIONING CHANNEL, not the model capacity. '
        'The U-Net is unconstrained and the retrieval codebook holds %d entries -- but those '
        'entries are addressed by only 48 scalars, so the bottleneck is the query side. '
        'Stating it any more broadly would overclaim.\n'
        'Three INDEPENDENT confirmations, which is why this is not just a config read: the '
        'config gives the token count (16), the TRAINED WEIGHTS give the per-token width '
        '(mlp_in.fc1.weight is %s, so each superpixel enters as 3 numbers), and a live '
        'forward pass of the real module on a real sample gives vec_fg = %s.\n'
        'NEW FINDING, not in any source document: 48 is an UPPER bound. LMP zero-fills '
        'superpixels that SLIC leaves empty (ddpm.py:1558-1560), so the effective width on '
        'real samples is %.2f on average (range %d-%d over %d samples). The channel is at '
        'most 48 numbers wide and in practice narrower.\n'
        'Code observations while reading: LMP uses no attribute of self, and its fourth '
        'argument s is dead -- sigma=5 is hardcoded at ddpm.py:1553.\n'
        'Mask convention verified, not assumed: mask==1 is the region the generator invents, '
        'so 1-mask is the kept foreground, which is what LMP segments (ddpm.py:1552).\n'
        'HOW THIS INTEGRATES: this is conclusion (i) of the package. With A2 (~82%% of every '
        'output is invented background) it gives "we steer 82%% of the picture through 48 '
        'numbers". It is also the target of the one forward path we identify -- widening this '
        'channel at ddpm.py:1579 -- so the width had to be exact.'
        % (codebook_entries, shapes['mlp_in.fc1.weight'], live_vec, eff_mean,
           min(eff), max(eff), len(occ)))

    block = C.log_block(
        exp='A1',
        cmd='LAKE-RED/.venv/bin/python evidence/a1_conditioning_width.py --samples %d'
            % opt.samples,
        metrics=metrics, thresholds=thresholds, expected=expected,
        artifacts=['evidence/out/a1_conditioning.csv',
                   'evidence/out/a1_superpixel_occupancy.csv'],
        revision='none -- this number has never moved',
        trains='NO', notes=notes, seed=opt.seed)
    print(block)


if __name__ == '__main__':
    main()

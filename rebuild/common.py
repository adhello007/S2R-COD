"""Shared helpers for the Stage C rebuild.

One source of truth for the things that must not drift between experiments:
the embedder, the image loaders (i.e. *which pixels* get embedded), the hashing,
and the log-block format.

Design rules, from REBUILD_PLAN.md:

  * The embedder is DECLARED here, not reverse-engineered to match any cache.
    The previous package had to reconstruct its preprocessing by testing eight
    candidate pipelines against saved vectors, because the producing script was
    gitignored. Nothing here is inferred from an artifact.

  * There is NO fallback path. No scratchpad, no archive, no rescued file. If an
    input is missing the script fails loudly. Silent fallback is how the old
    package ended up depending on /tmp.

  * Every loader states, in its docstring and in its returned tag, exactly which
    representation it produces. A variable name is not documentation --
    `load_cutout` returning an object-on-grey-128 image while the docs said
    "foreground cutout" is the defect this rebuild exists to catch.

  * results/REBUILD_LOG.txt is APPEND ONLY.
"""

import datetime
import hashlib
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD = os.path.join(REPO, 'rebuild')
LOG = os.path.join(REPO, 'results', 'REBUILD_LOG.txt')


def exp_dir(exp, *parts):
    """Path inside one experiment's own folder, e.g. exp_dir('E0', 'out')."""
    return os.path.join(REBUILD, exp, *parts)


# ---------------------------------------------------------------------------
# Primary inputs. Every path is relative to the repo root and must exist.
# ---------------------------------------------------------------------------
# `repr` names the representation each set produces, per REBUILD_PLAN.md §2.
# `pool` marks the three distinct 4447-image HKU-IS pools (trap T1) so that no
# script can conflate them.

INPUTS = {
    # --- images ---
    'tgt':   dict(path='Dataset/Target/Image',                  n=4040, repr='R1-full',   pool=None),
    'raw':   dict(path='Dataset/Source/HKU-IS_raw/imgs',        n=4447, repr='R1-full',   pool='raw'),
    'auth':  dict(path='Dataset/Source/HKU-IS/Image',           n=4447, repr='R1-full',   pool='authors'),
    'local': dict(path='Dataset/LAKERED/output/HKU-IS/images',  n=4447, repr='R3-render', pool='local'),
    'test':  dict(path='Dataset/Test/COD10K/Imgs',              n=2026, repr='R1-full',   pool=None),
    'val':   dict(path='Dataset/Val/CAMO/Imgs',                 n=250,  repr='R1-full',   pool=None),
    # --- masks / ground truth ---
    'raw_gt':    dict(path='Dataset/Source/HKU-IS_raw/gt',         n=4447, repr='mask', pool='raw'),
    'auth_gt':   dict(path='Dataset/Source/HKU-IS/GT',             n=4447, repr='mask', pool='authors'),
    'local_msk': dict(path='Dataset/LAKERED/output/HKU-IS/masks',  n=4447, repr='mask', pool='local'),
    'test_gt':   dict(path='Dataset/Test/COD10K/GT',               n=2026, repr='mask', pool=None),
    'val_gt':    dict(path='Dataset/Val/CAMO/GT',                  n=250,  repr='mask', pool=None),
    # --- secondary test sets (D2 leakage sweep) ---
    'cham':  dict(path='Dataset/Test/CHAMELEON/Imgs', n=76,   repr='R1-full', pool=None),
    'nc4k':  dict(path='Dataset/Test/NC4K/Imgs',      n=4121, repr='R1-full', pool=None),
    # --- LAKE-RED staging inputs (mask polarity is INVERTED here; trap T2) ---
    'lr_in_img':  dict(path='Dataset/LAKERED/input/HKU-IS/validation/images', n=4447, repr='R1-full',      pool=None),
    'lr_in_mask': dict(path='Dataset/LAKERED/input/HKU-IS/validation/masks',  n=4447, repr='mask-INVERTED', pool=None),
}

# Derived set: not a directory. Built from raw + raw_gt at load time.
DERIVED = {
    'cut': dict(built_from=('raw', 'raw_gt'), n=4447, repr='R2-cutout-grey128', pool='raw'),
}

# Predictions and checkpoints (C3, B1) -- primary, in-repo, no rescued copies.
PRIMARY_MODELS = {
    'SINet/S2C':      'Snapshot/SINet/S2C',
    'SINet/S2C_MT':   'Snapshot/SINet/S2C_MT',
    'SINet/S2C_SO':   'Snapshot/SINet/S2C_SO',
    'SINet-v2/S2C':   'Snapshot/SINet-v2/S2C',
    'SINet-v2/S2C_MT': 'Snapshot/SINet-v2/S2C_MT',
    'SINet-v2/S2C_SO': 'Snapshot/SINet-v2/S2C_SO',
    'SegMaR/S2C':     'Snapshot/SegMaR/S2C',
}


def ipath(key):
    """Absolute path of a declared input. Raises if it is not on disk."""
    if key not in INPUTS:
        raise KeyError('%s is not a declared input; add it to common.INPUTS' % key)
    p = os.path.join(REPO, INPUTS[key]['path'])
    if not os.path.isdir(p):
        raise FileNotFoundError(
            '%s (%s) is missing. This rebuild has NO fallback path by design -- '
            'regenerate it from primary data or mark the dependent experiment '
            'UNVERIFIED. See REBUILD_PLAN.md §1.' % (INPUTS[key]['path'], key))
    return p


def listing(key):
    """Sorted filenames of a declared input directory."""
    return sorted(os.listdir(ipath(key)))


# ---------------------------------------------------------------------------
# Image loaders -- each states exactly which pixels it returns
# ---------------------------------------------------------------------------

GREY = 128        # the flat background value of the R2 cutout
THRESH = 127      # mask binarisation threshold, matching prepare_lakered_inputs.py:73


def load_full(path):
    """R1 / R3 -- the image as stored, unmodified, RGB. No mask, no crop."""
    from PIL import Image
    return Image.open(path).convert('RGB')


def load_cutout(img_path, mask_path, grey=GREY, threshold=THRESH):
    """R2 -- object preserved, background painted FLAT GREY `grey` (128).

    This is the representation the previous package's documents called a
    "foreground cutout". It is not transparent and not black: every pixel where
    the mask is below `threshold` becomes the constant value 128.

    Mask polarity: HKU-IS ground truth stores the OBJECT as white, so the
    background is `mask < threshold`. Verified in E0 step 2, not assumed.

    The grey is applied at NATIVE resolution, before any resize -- so a later
    resize blends object edges into the grey. Roughly 81% of the resulting
    frame is the constant value (see A2).
    """
    import numpy as np
    from PIL import Image
    im = Image.open(img_path).convert('RGB')
    gt = Image.open(mask_path).convert('L').resize(im.size, Image.NEAREST)
    a = np.asarray(im).copy()
    a[np.asarray(gt) < threshold] = grey
    return Image.fromarray(a)


# ---------------------------------------------------------------------------
# Embedders -- DECLARED, not reconstructed
# ---------------------------------------------------------------------------
# Two independent families so that no conclusion is embedder-specific
# (REBUILD_PLAN.md §0.2), and a resolution sweep because B3's headline moved
# 4.1x between 224 and 518 in the old package.
#
# Precision is fp32. The old caches were fp16 (embed_dino.py:6 `.half()`);
# this is a deliberate difference, recorded rather than matched.
#
# Normalisation comes from each model's OWN pretrained_cfg -- CLIP's mean/std
# is (0.481, 0.458, 0.408), NOT ImageNet's. Using one mean/std for both
# families would quietly corrupt the second one.

EMBEDDERS = {
    'dinoL224': dict(model='vit_large_patch14_dinov2.lvd142m', size=224, family='dinov2'),
    'dinoL518': dict(model='vit_large_patch14_dinov2.lvd142m', size=518, family='dinov2'),
    'clipL224': dict(model='vit_large_patch14_clip_224.openai', size=224, family='clip'),
}
DEFAULT_EMBEDDER = 'dinoL518'

# Resize policy. Squash to (S, S) with BICUBIC: the whole frame is kept and
# nothing is cropped away, at the cost of distorting aspect ratio. This is a
# CHOICE, not a necessity -- E0 step 3b measures how much it matters by
# comparing against aspect-preserving resize + centre crop.
RESIZE_SQUASH = 'squash'
RESIZE_CROP = 'aspect_crop'


def build_model(tag, device='cuda'):
    """Instantiate a declared embedder. Returns (model, transform, meta)."""
    import timm
    import torchvision.transforms as T
    if tag not in EMBEDDERS:
        raise KeyError('unknown embedder %r; declared: %s' % (tag, list(EMBEDDERS)))
    spec = EMBEDDERS[tag]
    model = timm.create_model(spec['model'], pretrained=True, num_classes=0,
                              img_size=spec['size']).to(device).eval()
    cfg = model.pretrained_cfg
    mean, std = tuple(cfg['mean']), tuple(cfg['std'])
    meta = dict(tag=tag, model=spec['model'], size=spec['size'],
                family=spec['family'], mean=mean, std=std,
                precision='fp32', resize=RESIZE_SQUASH, pooling='cls+patchmean')
    return model, _transform(spec['size'], mean, std, RESIZE_SQUASH), meta


def _transform(size, mean, std, policy):
    import torchvision.transforms as T
    if policy == RESIZE_SQUASH:
        pre = [T.Resize((size, size), interpolation=T.InterpolationMode.BICUBIC)]
    elif policy == RESIZE_CROP:
        pre = [T.Resize(size, interpolation=T.InterpolationMode.BICUBIC),
               T.CenterCrop(size)]
    else:
        raise ValueError(policy)
    return T.Compose(pre + [T.ToTensor(), T.Normalize(mean, std)])


def embed(items, loader, tag=DEFAULT_EMBEDDER, batch=32, device='cuda',
          transform=None, model=None, progress=None):
    """Embed `items` through `loader`. Returns (cls, patchmean) float32 arrays.

    Vectors are stored UNNORMALISED; L2-normalise at use time via l2().
    Both poolings are returned so no experiment has to re-embed to change its
    mind about pooling.
    """
    import numpy as np
    import torch
    own = model is None
    if own:
        model, transform, _ = build_model(tag, device)
    cls_out, pat_out = [], []
    with torch.no_grad():
        for i in range(0, len(items), batch):
            chunk = items[i:i + batch]
            x = torch.stack([transform(loader(it)) for it in chunk]).to(device)
            f = model.forward_features(x)
            cls_out.append(f[:, 0].float().cpu().numpy())
            pat_out.append(f[:, 1:].mean(1).float().cpu().numpy())
            if progress and (i // batch) % 25 == 0:
                progress(min(i + batch, len(items)), len(items))
    if own:
        del model
        torch.cuda.empty_cache()
    return (np.concatenate(cls_out).astype('float32'),
            np.concatenate(pat_out).astype('float32'))


def l2(a):
    import numpy as np
    return a / np.linalg.norm(a, axis=-1, keepdims=True)


# ---------------------------------------------------------------------------
# Hashing, environment, logging
# ---------------------------------------------------------------------------

def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def dir_digest(path):
    """(n_files, aggregate_hash) over a directory's immediate files.

    Aggregate = sha256 of the sorted "sha256  name" listing, so it changes if
    any file's content OR the file set changes. Matches the `agg` values pinned
    in REBUILD_PLAN.md §1.
    """
    names = sorted(f for f in os.listdir(path)
                   if os.path.isfile(os.path.join(path, f)))
    h = hashlib.sha256()
    per_file = []
    for nm in names:
        d = sha256(os.path.join(path, nm))
        per_file.append((nm, d))
        h.update(('%s  %s\n' % (d, nm)).encode())
    return len(names), h.hexdigest(), per_file


def now():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def git_commit():
    try:
        sha = subprocess.check_output(['git', '-C', REPO, 'rev-parse', '--short', 'HEAD'],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(['git', '-C', REPO, 'status', '--porcelain'],
                                        text=True, stderr=subprocess.DEVNULL).strip()
        return '%s (%s)' % (sha, 'dirty' if dirty else 'clean')
    except Exception:
        return 'unknown (unknown)'


def env_stamp(seed=0):
    import platform
    import sys
    env = dict(python=platform.python_version(), platform=platform.platform(),
               seed=seed, executable=sys.executable)
    try:
        import torch
        env.update(torch=torch.__version__, cuda=torch.version.cuda,
                   cudnn=torch.backends.cudnn.version(),
                   gpus=[torch.cuda.get_device_name(i)
                         for i in range(torch.cuda.device_count())]
                   if torch.cuda.is_available() else [])
    except Exception:
        env.update(torch='n/a', cuda='n/a', cudnn='n/a', gpus=[])
    for mod, key in (('timm', 'timm'), ('sklearn', 'scikit-learn'),
                     ('numpy', 'numpy'), ('cv2', 'opencv'), ('PIL', 'pillow'),
                     ('scipy', 'scipy')):
        try:
            env[key] = __import__(mod).__version__
        except Exception:
            env[key] = 'n/a'
    return env


def env_line(env):
    gpus = env.get('gpus') or []
    gpu = '%dx %s' % (len(gpus), gpus[0]) if gpus else 'no gpu'
    return ('py%s torch%s cu%s timm%s numpy%s | %s | seed %s'
            % (env['python'], env['torch'], env['cuda'], env['timm'],
               env['numpy'], gpu, env['seed']))


def log_block(exp, cmd, metrics, thresholds=(), old_claims=(), artifacts=(),
              representation='n/a', trains='NO', notes='', seed=0, env=None,
              write=True):
    """Append ONE block to results/REBUILD_LOG.txt.

    metrics     : (name, value, provenance)
    thresholds  : (condition_str, passed_bool)
    old_claims  : (label, old_value, verdict)  verdict in
                  MATCH / MISMATCH / NEW / UNVERIFIED / NOT-REPRODUCIBLE
                  -- the old value is a RECORD for REVISION_TABLE.md, never an
                  input and never a target.

    write=False formats without touching the log, for iterating on a script.
    The log is for accepted runs, not debugging rounds.
    """
    env = env or env_stamp(seed)
    bar = '=' * 80
    lines = [bar,
             '%s | commit %s | EXP %s' % (now(), git_commit(), exp),
             'CMD   %s' % cmd,
             'ENV   %s' % env_line(env),
             'REPR  %s' % representation,
             'METRICS']
    width = max([len(str(m[0])) for m in metrics], default=1)
    for name, value, *prov in metrics:
        p = prov[0] if prov and prov[0] else ''
        lines.append('  %-*s = %s%s' % (width, name, value, '    (%s)' % p if p else ''))
    for cond, ok in thresholds:
        lines.append('THRESHOLD  %s -> %s' % (cond, 'PASS' if ok else 'FAIL'))
    if not thresholds:
        lines.append('THRESHOLD  none declared')
    for label, old, verdict in old_claims:
        lines.append('OLD CLAIM  %s = %s -> %s' % (label, old, verdict))
    if not old_claims:
        lines.append('OLD CLAIM  none pinned')
    lines.append('ARTIFACTS  %s' % (', '.join(artifacts) if artifacts else 'none'))
    lines.append('TRAINS     %s' % trains)
    for i, para in enumerate(notes.strip().split('\n') if notes else ['none']):
        lines.append('%s %s' % ('NOTES     ' if i == 0 else '          ', para))
    lines += [bar, '']
    text = '\n'.join(lines)
    if write:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if not os.path.exists(LOG):
            _write_log_header()
        with open(LOG, 'a') as fh:              # APPEND ONLY -- never 'w'
            fh.write(text + '\n')
    else:
        text = text.replace(bar, bar, 1) + '\n[--no-log: NOT written]'
    return text


def _write_log_header():
    hdr = """\
Stage C rebuild -- measurement log
==================================

APPEND ONLY. One block per accepted run. Every number in REBUILD_FINDINGS.md
must be traceable to a block here; a number without one is a defect.

Block format
------------
  <ISO-8601 timestamp> | commit <sha> (clean|dirty) | EXP <id>
  CMD        the exact command that produced this block
  ENV        versions, GPU, seed
  REPR       which image representation was embedded (REBUILD_PLAN.md §2)
  METRICS    name = value  (provenance)
  THRESHOLD  declared condition -> PASS|FAIL
  OLD CLAIM  the previous package's value -> MATCH|MISMATCH|NEW|UNVERIFIED|
             NOT-REPRODUCIBLE. A RECORD for REVISION_TABLE.md only: never an
             input, never a baseline, never a target.
  ARTIFACTS  files written
  TRAINS     whether this experiment trained a model
  NOTES      caveats, assumptions stated AS assumptions, what is UNVERIFIED

Rules
-----
  * No number appears in any document before it appears here.
  * Anything not computable is UNVERIFIED -- never a placeholder value.
  * No experiment reads the archived old artifacts or any /tmp scratchpad.

"""
    with open(LOG, 'w') as fh:
        fh.write(hdr)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    return path

"""Shared helpers for the Stage C evidence package.

Every evidence script imports from here, so that:
  * log blocks have one uniform shape,
  * the results log is only ever opened in APPEND mode,
  * the environment stamp and git commit are recorded identically everywhere,
  * inputs resolve to the rescued copies first and the volatile scratchpad second.

See EVIDENCE_SCRIPTS.md for the run-book and results/STAGE_C_EVIDENCE_LOG.txt
for the format legend.
"""

import datetime
import hashlib
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(REPO, 'evidence', 'artifacts')
MANIFESTS = os.path.join(REPO, 'evidence', 'manifests')
SOURCES = os.path.join(REPO, 'evidence', 'sources')
OUT = os.path.join(REPO, 'evidence', 'out')
LOG = os.path.join(REPO, 'results', 'STAGE_C_EVIDENCE_LOG.txt')

# The volatile session scratchpad the original audits ran in. E0 rescues out of
# it; every later script reads from ARTIFACTS and only falls back to here. This
# path is NOT durable -- see EVIDENCE_SCRIPTS.md section E0.
SCRATCH = ('/tmp/claude-1000/-home-ai-server-Public-lab-Diffusion-Inpaint-S2R-COD/'
           '56f76fa7-1340-4f64-8958-29c72d526e77/scratchpad')

# Fixed seed for every stochastic step (k-means init, probe splits, held-out
# generation splits, random-1000 draws, permutation shuffles).
SEED = 0

_RESCUE_HINT = (
    'Run E0 first:  LAKE-RED/.venv/bin/python evidence/e0_rescue.py\n'
    'If the scratchpad is also gone, this input cannot be regenerated without '
    'retraining -- see EVIDENCE_SCRIPTS.md section E0.')


def now():
    """Local ISO-8601 timestamp with UTC offset."""
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def git_commit():
    """Short commit sha plus a clean/dirty flag for the working tree."""
    try:
        sha = subprocess.check_output(
            ['git', '-C', REPO, 'rev-parse', '--short', 'HEAD'],
            text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(
            ['git', '-C', REPO, 'status', '--porcelain'],
            text=True, stderr=subprocess.DEVNULL).strip()
        return '%s (%s)' % (sha, 'dirty' if dirty else 'clean')
    except Exception:
        return 'unknown (unknown)'


def env_stamp(seed=SEED):
    """Version/hardware dict. Imports are best-effort so CPU-only scripts still
    record what they can rather than failing."""
    import platform
    import sys
    env = {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'seed': seed,
        'executable': sys.executable,
    }
    try:
        import torch
        env['torch'] = torch.__version__
        env['cuda'] = torch.version.cuda
        env['gpus'] = ([torch.cuda.get_device_name(i)
                        for i in range(torch.cuda.device_count())]
                       if torch.cuda.is_available() else [])
    except Exception:
        env['torch'] = env['cuda'] = 'n/a'
        env['gpus'] = []
    for mod, key in (('timm', 'timm'), ('transformers', 'transformers'),
                     ('sklearn', 'scikit-learn'), ('numpy', 'numpy'),
                     ('cv2', 'opencv'), ('skimage', 'scikit-image')):
        try:
            env[key] = __import__(mod).__version__
        except Exception:
            env[key] = 'n/a'
    return env


def env_line(env):
    """One-line ENV field for the log block."""
    gpus = env.get('gpus') or []
    gpu = '%dx %s' % (len(gpus), gpus[0]) if gpus else 'no gpu'
    return 'py%s torch%s cu%s timm%s sklearn%s | %s | seed %s' % (
        env['python'], env['torch'], env['cuda'], env['timm'],
        env['scikit-learn'], gpu, env['seed'])


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def resolve(name):
    """Locate a rescued input. Prefers evidence/artifacts/, falls back to the
    volatile scratchpad, and fails loudly with the rescue instruction."""
    for root in (ARTIFACTS, SCRATCH, os.path.join(SCRATCH, 'noisefloor')):
        cand = os.path.join(root, name)
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError('%s not found in %s or %s\n%s'
                            % (name, ARTIFACTS, SCRATCH, _RESCUE_HINT))


def rng(seed=SEED):
    import numpy as np
    return np.random.default_rng(seed)


def log_block(exp, cmd, metrics, thresholds=(), expected=(), artifacts=(),
              revision='none', trains='NO', notes='', seed=SEED, env=None,
              write=True):
    """Append ONE block to results/STAGE_C_EVIDENCE_LOG.txt.

    write=False formats the block and returns it WITHOUT touching the log. Use
    it (via each script's --no-log) while iterating on a script, so that fixing
    a defect in the measurement code does not leave a trail of near-identical
    blocks. The log is for accepted runs and genuine re-runs, not for debugging
    rounds -- and because it is append-only, the only way to keep it readable is
    to not write the noise in the first place.

    metrics    : list of (name, value, provenance)
    thresholds : list of (condition_str, passed_bool)
    expected   : list of (label, expected_value, verdict)  verdict in
                 MATCH / MISMATCH / NEW / UNVERIFIED / NOT-REPRODUCIBLE
    """
    env = env or env_stamp(seed)
    bar = '=' * 80
    lines = [bar,
             '%s | commit %s | EXP %s' % (now(), git_commit(), exp),
             'CMD  %s' % cmd,
             'ENV  %s' % env_line(env),
             'METRICS']
    width = max([len(str(m[0])) for m in metrics], default=1)
    for name, value, *prov in metrics:
        prov = prov[0] if prov and prov[0] else ''
        lines.append('  %-*s = %s%s' % (width, name, value,
                                        '    (%s)' % prov if prov else ''))
    for cond, ok in thresholds:
        lines.append('THRESHOLD  %s -> %s' % (cond, 'PASS' if ok else 'FAIL'))
    if not thresholds:
        lines.append('THRESHOLD  none declared')
    for label, exp_val, verdict in expected:
        lines.append('EXPECTED (source)  %s = %s -> %s' % (label, exp_val, verdict))
    if not expected:
        lines.append('EXPECTED (source)  none pinned')
    lines.append('ARTIFACTS  %s' % (', '.join(artifacts) if artifacts else 'none'))
    lines.append('REVISION   %s' % revision)
    lines.append('TRAINS     %s' % trains)
    for i, para in enumerate(notes.strip().split('\n') if notes else ['none']):
        lines.append('%s %s' % ('NOTES     ' if i == 0 else '          ', para))
    lines += [bar, '']
    if write:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a') as fh:                # APPEND ONLY -- never 'w'
            fh.write('\n'.join(lines) + '\n')
    else:
        lines.insert(1, '[--no-log: NOT written to the results log]')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# DINOv2 embedding -- the ORIGINAL pipeline, recovered by search
# ---------------------------------------------------------------------------
# The audits' feature caches were produced by a script that was never saved, so
# the preprocessing had to be reverse-engineered. Eight candidate pipelines were
# tested against the cached vectors; exactly one reproduces them:
#
#     PIL -> Resize((S, S), BICUBIC)  [squash, NO aspect preserve, NO crop]
#         -> ToTensor -> Normalize(ImageNet mean/std)
#         -> timm ViT CLS token, stored UNNORMALISED
#
# Verified at cos = 1.00000 against dinoL_tgt_cls.npy and dinoL_gen_cls.npy.
# The near-misses are informative: Resize(S)+CenterCrop(S) gives 0.978 and
# cv2.INTER_AREA gives 0.997, so a plausible-looking pipeline would have
# silently produced slightly wrong features. Any script mixing fresh and cached
# features MUST call assert_embedder_matches_cache() first.
#
# Two traps: timm.data.resolve_data_config() returns 518 even for a model built
# with img_size=224 (DINOv2's pretrained size), and timm then hard-asserts on it
# at timm/layers/patch_embed.py:121 -- so the transform is built by hand here.
# And the cached vectors are NOT unit-norm (|f| ~ 47), so normalise at use time.

DINOV2 = {'L': 'vit_large_patch14_dinov2.lvd142m',
          'B': 'vit_base_patch14_dinov2.lvd142m'}
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def l2(a):
    import numpy as np
    return a / np.linalg.norm(a, axis=-1, keepdims=True)


def _transform(size):
    import torchvision.transforms as T
    return T.Compose([
        T.Resize((size, size), interpolation=T.InterpolationMode.BICUBIC),
        T.ToTensor(), T.Normalize(IMAGENET_MEAN, IMAGENET_STD)])


def load_dinov2(variant='L', size=224, device='cuda'):
    import timm
    model = timm.create_model(DINOV2[variant], pretrained=True, num_classes=0,
                              img_size=size).to(device).eval()
    return model, _transform(size)


def embed(items, variant='L', size=224, batch=64, device='cuda', loader=None,
          progress=None):
    """CLS features for a list of image paths (or arrays, via loader).

    Returns an UNNORMALISED (n, d) float32 array, matching how the original
    caches were stored. `loader` maps an item to a PIL image or HWC uint8 array;
    the default opens a path and converts to RGB.
    """
    import numpy as np
    import torch
    from PIL import Image
    if loader is None:
        def loader(x):
            return Image.open(x).convert('RGB')
    model, tf = load_dinov2(variant, size, device)
    out = []
    with torch.no_grad():
        for i in range(0, len(items), batch):
            chunk = items[i:i + batch]
            ims = []
            for it in chunk:
                im = loader(it)
                ims.append(tf(im if isinstance(im, Image.Image)
                              else Image.fromarray(im)))
            out.append(model(torch.stack(ims).to(device)).float().cpu().numpy())
            if progress and (i // batch) % 20 == 0:
                progress(min(i + batch, len(items)), len(items))
    del model
    torch.cuda.empty_cache()
    return np.concatenate(out).astype('float32')


def embed_cached(name, items, variant='L', size=224, **kw):
    """embed() with an on-disk cache under evidence/artifacts/."""
    import numpy as np
    path = os.path.join(ARTIFACTS, '%s_%s%d_cls.npy' % (name, variant, size))
    if os.path.exists(path):
        return np.load(path), False
    feats = embed(items, variant=variant, size=size, **kw)
    os.makedirs(ARTIFACTS, exist_ok=True)
    np.save(path, feats)
    return feats, True


def assert_embedder_matches_cache(variant='L', size=224, n=8, seed=SEED,
                                  tol=0.999):
    """Gate: prove this pipeline reproduces the audits' cached features.

    Re-embeds n random images of the target set and compares against the stored
    vectors. Raises unless every cosine >= tol, so a script can never silently
    mix two different preprocessing pipelines.
    """
    import json
    import numpy as np
    tag = 'dino%s%s' % (variant, '' if size == 224 else str(size))
    cache = os.path.join(ARTIFACTS, '%s_tgt_cls.npy' % tag)
    names_p = os.path.join(ARTIFACTS, '%s_names.json' % tag)
    if not (os.path.exists(cache) and os.path.exists(names_p)):
        return None                      # nothing to check against
    cached = l2(np.load(cache))
    names = json.load(open(names_p))['tgt']
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(names), size=min(n, len(names)), replace=False)
    fresh = l2(embed([os.path.join(REPO, 'Dataset/Target/Image', names[i])
                      for i in pick], variant=variant, size=size))
    cos = [float(fresh[j] @ cached[i]) for j, i in enumerate(pick)]
    if min(cos) < tol:
        raise RuntimeError(
            'embedder does not reproduce the cached features (min cos %.5f < '
            '%.3f). Fresh and cached vectors must not be mixed. See the '
            'pipeline note in evidence/common.py.' % (min(cos), tol))
    return {'n': len(cos), 'min_cos': min(cos), 'mean_cos': float(np.mean(cos))}

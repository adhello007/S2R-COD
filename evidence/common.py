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

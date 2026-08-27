"""Environment and input checker for the Stage C evidence package.

Verifies that this machine can run the experiments, and says exactly what is
missing when it cannot. This is NOT an experiment: it writes nothing to the
results log.

    LAKE-RED/.venv/bin/python evidence/setup_check.py

Exit code 0 if every REQUIRED check passes, 1 otherwise. WARN rows are
non-blocking: they mark inputs only some experiments need.

See EVIDENCE_SETUP.md for how to fix each failure.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

# package -> version this package was validated against
PINS = {
    'torch': '2.11.0+cu128', 'torchvision': '0.26.0+cu128',
    'timm': '1.0.28', 'transformers': '5.15.1',
    'scikit-learn': '1.9.0', 'scikit-image': '0.26.0',
    'numpy': '2.5.2', 'opencv-python-headless': '5.0.0.93',
    'matplotlib': '3.11.1', 'scipy': '1.18.0', 'PyYAML': '6.0.3',
    'einops': '0.8.2', 'omegaconf': '2.3.1', 'huggingface-hub': '1.28.0',
}

# path -> (expected file count or None, required?, which experiments need it)
DATA = [
    ('Dataset/Source/HKU-IS/Image', 4447, True, 'D1'),
    ('Dataset/Source/HKU-IS/GT', 4447, True, 'A2 D1'),
    ('Dataset/Source/HKU-IS_raw/imgs', 4447, True, 'A3 D1'),
    ('Dataset/Source/HKU-IS_raw/gt', 4447, True, 'A2 D1'),
    ('Dataset/LAKERED/input/HKU-IS/validation/images', 4447, True, 'A1'),
    ('Dataset/LAKERED/input/HKU-IS/validation/masks', 4447, True, 'A1 A2'),
    ('Dataset/LAKERED/output/HKU-IS/images', 4447, True, 'A3 B3 C1 D1'),
    ('Dataset/LAKERED/output/HKU-IS/masks', 4447, True, 'A2 D1'),
    ('Dataset/Target/Image', 4040, True, 'A3 B3 C1 D2'),
    ('Dataset/Test/COD10K/Imgs', 2026, True, 'B1 D2'),
    ('Dataset/Test/COD10K/GT', 2026, True, 'B1 C3 D2'),
    ('Dataset/Val/CAMO/Imgs', 250, True, 'B1 D2'),
    ('Dataset/Val/CAMO/GT', 250, True, 'B1 D2'),
    ('Dataset/Test/CAMO/Imgs', 250, False, 'D2'),
    ('Dataset/Test/CHAMELEON/Imgs', 76, False, 'D2'),
    ('Dataset/Test/NC4K/Imgs', 4121, False, 'D2'),
]

CKPTS = [
    ('LAKE-RED/ckpt/LAKERED.ckpt', True, 'A1'),
    ('Snapshot/SINet/S2C/Stu_40.pth', True, 'B1'),
    ('Snapshot/SINet/S2C/Tea_epoch_best.pth', True, 'B1'),
]

SOURCES = [
    ('STAGE_C_MEASUREMENTS.md', True), ('STAGE_C_RED_TEAM_AUDIT.md', True),
    ('evidence/sources/PRIOR_REVIEW.md', True),
]

RUNS = ['s42', 's43', 's45', 's46', 'repB', 'repC']

rows = []


def add(name, ok, detail, required=True):
    rows.append((name, 'PASS' if ok else ('FAIL' if required else 'WARN'), detail))
    return ok


def main():
    repo = C.REPO
    hard_fail = False

    # ---- interpreter -----------------------------------------------------
    v = '%d.%d.%d' % sys.version_info[:3]
    hard_fail |= not add('python %s' % v, sys.version_info[:2] == (3, 12),
                         'expected 3.12.x')
    try:
        import timm  # noqa: F401
        right_venv = True
    except ImportError:
        right_venv = False
    hard_fail |= not add(
        'correct virtualenv', right_venv,
        'timm importable -> this is LAKE-RED/.venv; the root .venv lacks it '
        'and every DINOv2 experiment fails there')

    # ---- packages --------------------------------------------------------
    from importlib.metadata import version, PackageNotFoundError
    mism = []
    for pkg, want in PINS.items():
        try:
            got = version(pkg)
        except PackageNotFoundError:
            got = None
        if got is None:
            mism.append('%s MISSING' % pkg)
        elif got != want:
            mism.append('%s %s!=%s' % (pkg, got, want))
    add('package versions (%d pins)' % len(PINS), not mism,
        'all match' if not mism else '; '.join(mism), required=False)

    # ---- gpu -------------------------------------------------------------
    try:
        import torch
        n = torch.cuda.device_count() if torch.cuda.is_available() else 0
        names = [torch.cuda.get_device_name(i) for i in range(n)]
        add('cuda available', n > 0,
            '%d gpu(s): %s' % (n, ', '.join(sorted(set(names))) or 'none'),
            required=False)
        cap = torch.cuda.get_device_capability(0) if n else None
        if cap and cap[0] >= 12:
            add('Blackwell needs cu128 wheels', '+cu128' in torch.__version__,
                'sm_%d%d with torch %s' % (cap[0], cap[1], torch.__version__))
    except Exception as e:
        add('cuda available', False, str(e), required=False)

    # ---- datasets --------------------------------------------------------
    for rel, want, req, exps in DATA:
        d = os.path.join(repo, rel)
        if not os.path.isdir(d):
            hard_fail |= not add(rel, False, 'MISSING (needed by %s)' % exps, req)
            continue
        n = len([f for f in os.listdir(d) if not f.startswith('.')])
        ok = (want is None or n == want)
        hard_fail |= not add(rel, ok, '%d files%s (%s)'
                             % (n, '' if ok else ', expected %d' % want, exps), req)

    # ---- checkpoints -----------------------------------------------------
    for rel, req, exps in CKPTS:
        p = os.path.join(repo, rel)
        ok = os.path.isfile(p)
        hard_fail |= not add(rel, ok,
                             ('%.1f GiB (%s)' % (os.path.getsize(p) / 1024 ** 3, exps))
                             if ok else 'MISSING (needed by %s)' % exps, req)

    # ---- DINOv2 weights --------------------------------------------------
    hub = os.path.expanduser('~/.cache/huggingface/hub')
    for m in ('vit_large_patch14_dinov2.lvd142m', 'vit_base_patch14_dinov2.lvd142m'):
        d = os.path.join(hub, 'models--timm--' + m)
        add('DINOv2 %s' % m.split('_patch')[0], os.path.isdir(d),
            'cached' if os.path.isdir(d) else 'not cached -- will download on first use',
            required=False)

    # ---- source documents ------------------------------------------------
    for rel, req in SOURCES:
        p = os.path.join(repo, rel)
        hard_fail |= not add(rel, os.path.isfile(p),
                             'present' if os.path.isfile(p) else 'MISSING', req)

    # ---- rescued artifacts (E0) -----------------------------------------
    art = C.ARTIFACTS
    preds = [(r, os.path.join(art, 'pred_%s' % r)) for r in RUNS]
    got = [r for r, d in preds if os.path.isdir(d)]
    counts = {r: len(os.listdir(d)) for r, d in preds if os.path.isdir(d)}
    add('rescued predictions (C3)', len(got) == 6 and set(counts.values()) == {2026},
        '%d/6 dirs, counts %s' % (len(got), sorted(set(counts.values())) or 'n/a'),
        required=False)
    cks = sum(os.path.isfile(os.path.join(art, 'snap_%s' % r, f))
              for r in RUNS for f in ('Stu_40.pth', 'Tea_epoch_best.pth'))
    add('rescued checkpoints (B1 cross-run)', cks == 12, '%d/12' % cks, required=False)
    caches = [f for f in os.listdir(art) if f.endswith('.npy')] \
        if os.path.isdir(art) else []
    add('rescued feature caches (A3 B3 C1)', len(caches) >= 30,
        '%d .npy files' % len(caches), required=False)
    if not os.path.isdir(art):
        add('evidence/artifacts present', False,
            'run: LAKE-RED/.venv/bin/python evidence/e0_rescue.py', required=False)

    # ---- manifests -------------------------------------------------------
    for m in ('MANIFEST.sha256', 'SOURCES.sha256'):
        p = os.path.join(C.MANIFESTS, m)
        if not os.path.isfile(p):
            add('manifest %s' % m, False, 'MISSING', required=False)
            continue
        r = subprocess.run(['sha256sum', '-c', os.path.relpath(p, repo)],
                           cwd=repo, capture_output=True, text=True)
        n_ok = r.stdout.count(': OK')
        n_bad = r.stdout.count('FAILED')
        add('manifest %s' % m, n_bad == 0 and n_ok > 0,
            '%d OK, %d FAILED' % (n_ok, n_bad), required=False)

    # ---- report ----------------------------------------------------------
    w = max(len(n) for n, _, _ in rows)
    print('=' * (w + 58))
    print('Stage C evidence package -- environment check')
    print('=' * (w + 58))
    for name, status, detail in rows:
        print('  [%-4s] %-*s  %s' % (status, w, name, detail))
    n_fail = sum(1 for _, s, _ in rows if s == 'FAIL')
    n_warn = sum(1 for _, s, _ in rows if s == 'WARN')
    print('-' * (w + 58))
    print('  %d checks: %d PASS, %d FAIL, %d WARN'
          % (len(rows), len(rows) - n_fail - n_warn, n_fail, n_warn))
    if n_fail:
        print('\n  FAIL rows block the experiments that name them. See EVIDENCE_SETUP.md.')
    elif n_warn:
        print('\n  Ready. WARN rows are optional inputs; only the experiments named '
              'beside them are affected.')
    else:
        print('\n  Ready: every check passed.')
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()

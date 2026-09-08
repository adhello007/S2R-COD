#!/usr/bin/env python
"""ABC -- the read-only probe behind rebuild/ABC/POOL_MECHANICS_AUDIT.md.

TRAINS NOTHING. WRITES NOTHING. Opens no image, loads no checkpoint, touches
no GPU. It (a) introspects the real Src/utils/Dataloader.py signatures and the
real MyTrain.py call sites by AST, (b) exercises torch's real DataLoader on
synthetic tensors at the real pool/target sizes to settle the shuffle and
zip()-truncation mechanics, (c) lists the real pool directories exactly as
SrcDataset builds its list, and (d) does the exposure arithmetic from the
committed rebuild/ABC/out/abc_runs.csv.

Usage:
  .venv/bin/python rebuild/ABC/pool_mechanics_probe.py
"""

import ast
import csv
import inspect
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)


def hdr(t):
    print('\n' + '=' * 78); print(t); print('=' * 78)


# ---------------------------------------------------------------- P1
hdr('P1  shuffle default in get_srcloader/get_tarloader + the MyTrain call sites')
from Src.utils.Dataloader import get_srcloader, get_tarloader            # noqa: E402

for f in (get_srcloader, get_tarloader):
    sg = inspect.signature(f)
    print('  %-14s shuffle default = %r   all defaults: %s'
          % (f.__name__, sg.parameters['shuffle'].default,
             {k: v.default for k, v in sg.parameters.items()
              if v.default is not inspect.Parameter.empty}))

tree = ast.parse(open(os.path.join(REPO, 'MyTrain.py')).read())
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, 'id', '') in (
            'get_srcloader', 'get_tarloader'):
        kw = [k.arg for k in node.keywords]
        print('  MyTrain.py:%d  %s(%s)  -> "shuffle" passed explicitly? %s'
              % (node.lineno, node.func.id, ', '.join(kw), 'shuffle' in kw))

# ---------------------------------------------------------------- P2
hdr('P2  sampler identity, reshuffle-per-epoch, and what zip() actually drops')
import torch                                                             # noqa: E402
from torch.utils import data as tdata                                    # noqa: E402


class Rec(tdata.Dataset):
    """Records which dataset indices __getitem__ actually touched."""

    def __init__(self, n):
        self.n = n
        self.seen = []

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        self.seen.append(i)
        return torch.zeros(1), torch.zeros(1)


N_SRC, N_TGT, B = 5447, 4040, 16          # the real SINet round-1 A2/B/C numbers
src_ds, tgt_ds = Rec(N_SRC), Rec(N_TGT)
src_loader = tdata.DataLoader(src_ds, batch_size=B, shuffle=True,
                              num_workers=0, pin_memory=False)
tgt_loader = tdata.DataLoader(tgt_ds, batch_size=B, shuffle=True,
                              num_workers=0, pin_memory=False)
TS = min(len(src_loader), len(tgt_loader))
print('  len(source_loader)=%d  len(target_loader)=%d  min=%d  drop_last=%s'
      % (len(src_loader), len(tgt_loader), TS, src_loader.drop_last))
print('  source sampler class = %s' % type(src_loader.sampler).__name__)
print('  ceil(%d/%d)=%d   ceil(%d/%d)=%d'
      % (N_SRC, B, math.ceil(N_SRC / B), N_TGT, B, math.ceil(N_TGT / B)))

sets, pulled = [], []
for ep in range(3):
    src_ds.seen, tgt_ds.seen = [], []
    steps = sum(1 for _ in zip(src_loader, tgt_loader))
    sets.append(set(src_ds.seen[:steps * B]))
    pulled.append(len(src_ds.seen))
    print('  epoch %d: steps yielded=%d  source idx PULLED=%d  TRAINED-ON=%d'
          % (ep, steps, len(src_ds.seen), steps * B))
e0, e1 = sets[0], sets[1]
jac = len(e0 & e1) / len(e0 | e1)
exp_int = len(e0) * len(e1) / N_SRC
print('  |E0|=%d |E1|=%d |E0&E1|=%d  Jaccard=%.4f  (independent-draw prediction %.4f)'
      % (len(e0), len(e1), len(e0 & e1), jac,
         exp_int / (len(e0) + len(e1) - exp_int)))
print('  same subset in consecutive epochs? %s' % (e0 == e1))
print('  union over 3 epochs covers %d/%d of the pool' % (len(set().union(*sets)), N_SRC))
print('  source batches pulled=%d  (=%d trained + %d fetched-then-dropped by zip)'
      % (pulled[0] // B, TS, pulled[0] // B - TS))

# ---------------------------------------------------------------- P3
hdr('P3  sorted() position of every filename class, exactly as SrcDataset builds it')


def cls_of(nm):
    if nm.startswith('SOD_'):
        return 'SOD_*.jpg          LAKE-RED re-render (arms B/C)'
    if nm.startswith('DUP_'):
        return 'DUP_*.jpg          authors dup (arm A2)'
    if nm.startswith('COD10K'):
        return 'COD10K-*.png       CLS pseudo-label (round 2)'
    if nm.startswith('camourflage'):
        return 'camourflage_*.png  CLS pseudo-label (round 2)'
    return 'NNNN.jpg           authors base pool'


def blocks(d):
    # Dataloader.py:14,16 -- os.listdir filtered to .jpg/.png, then sorted()
    names = sorted(f for f in os.listdir(d)
                   if f.endswith('.jpg') or f.endswith('.png'))
    out, i = [], 0
    while i < len(names):
        c = cls_of(names[i]); j = i
        while j < len(names) and cls_of(names[j]) == c:
            j += 1
        out.append((c, i, j - 1, j - i, names[i], names[j - 1])); i = j
    return names, out


POOLS = (('ROUND 1  A0  s42', 'Dataset/Source/ABC/SINet_A0_s42/Image'),
         ('ROUND 1  A2  s42', 'Dataset/Source/ABC/SINet_A2_s42/Image'),
         ('ROUND 1  C10 s42', 'Dataset/Source/ABC/SINet_C10_s42/Image'),
         ('ROUND 2  A0  s42', 'Dataset/Source/ABC/SINet_A0_s42_iteration2/Image'),
         ('ROUND 2  B   s42', 'Dataset/Source/ABC/SINet_B_s42_iteration2/Image'),
         ('ROUND 2  C10 s42', 'Dataset/Source/ABC/SINet_C10_s42_iteration2/Image'))
CUT = 253 * 16
for label, d in POOLS:
    full = os.path.join(REPO, d)
    if not os.path.isdir(full):
        print('\n  %s  MISSING: %s' % (label, d)); continue
    names, bl = blocks(full)
    print('\n  %s  n=%d  batches=%d  hypothetical unshuffled cut at index %d'
          % (label, len(names), math.ceil(len(names) / 16), CUT))
    print('    head %s  tail %s' % (names[:2], names[-2:]))
    for c, a, b, n, fa, fb in bl:
        inside = max(0, min(b + 1, CUT) - a)
        print('      [%5d..%5d] n=%5d  %-46s  pre-cut %5d / post-cut %5d'
              % (a, b, n, c, inside, n - inside))

# ---------------------------------------------------------------- P4/P5
hdr('P4  per-image expected exposure per epoch, from the committed run table')
rows = list(csv.DictReader(open(os.path.join(REPO, 'rebuild/ABC/out/abc_runs.csv'))))
print('  %-16s %3s %5s %5s | %-26s | %-26s'
      % ('runid', 'B', 'tstep', 'imgs', 'R1 pool/batches/exposure',
         'R2 pool/batches/exposure'))
for r in rows:
    b = 16 if r['arch'] == 'SINet' else 32
    ts = int(r['total_step_set']); n = ts * b
    p1, p2 = int(r['pool_r1']), int(r['pool_r2'])
    print('  %-16s %3d %5d %5d | %5d /%4d / %.4f      | %5d /%4d / %.4f'
          % (r['runid'], b, ts, n, p1, math.ceil(p1 / b), n / p1,
             p2, math.ceil(p2 / b), n / p2))

hdr('P5  arm-mean exposure and cumulative exposure over the run')
for arch, ts, b, eps in (('SINet', 253, 16, 39), ('SINetv2', 127, 32, 99)):
    n = ts * b
    print('  --- %s (%d imgs/epoch, %d epochs/round) ---' % (arch, n, eps))
    for arm in ('A0', 'A2', 'B', 'C10'):
        rs = [r for r in rows if r['arm'] == arm and r['arch'] == arch]
        if not rs:
            continue
        e1 = sum(n / int(r['pool_r1']) for r in rs) / len(rs)
        e2 = sum(n / int(r['pool_r2']) for r in rs) / len(rs)
        print('    %-4s r1 %.4f  r2 %.4f   cumulative %.1f + %.1f = %.1f passes'
              % (arm, e1, e2, eps * e1, eps * e2, eps * (e1 + e2)))

hdr('P6  expected COMPOSITION of the images actually trained on per epoch')
print('  %-16s | %-22s | %-40s'
      % ('runid', 'R1 base / added', 'R2 base / added / CLS-pseudo (pseudo share)'))
for r in rows:
    b = 16 if r['arch'] == 'SINet' else 32
    n = int(r['total_step_set']) * b
    p1, p2, ps = int(r['pool_r1']), int(r['pool_r2']), int(r['n_appended'])
    add = p1 - 4447
    print('  %-16s | %6.0f / %5.0f        | %6.0f / %5.0f / %6.0f   (%.4f)'
          % (r['runid'], n * 4447 / p1, n * add / p1,
             n * 4447 / p2, n * add / p2, n * ps / p2, ps / p2))

hdr('P7  spread of the round-2 pseudo-label share across arms (mixture confound)')
for arch in ('SINet', 'SINetv2'):
    sh = [(r['runid'], int(r['n_appended']) / int(r['pool_r2']))
          for r in rows if r['arch'] == arch]
    lo, hi = min(sh, key=lambda x: x[1]), max(sh, key=lambda x: x[1])
    print('  %-8s min %.4f (%s)  max %.4f (%s)  spread %.2f pp'
          % (arch, lo[1], lo[0], hi[1], hi[0], 100 * (hi[1] - lo[1])))
    rd = [(r['runid'], (int(r['pool_r1']) - 4447) / int(r['pool_r2']))
          for r in rows if r['arch'] == arch and r['arm'] in ('A2', 'B', 'C10')]
    print('           added-render share in round 2: %.4f-%.4f'
          % (min(x[1] for x in rd), max(x[1] for x in rd)))

print('\nPROBE COMPLETE. Wrote nothing; trained nothing.')

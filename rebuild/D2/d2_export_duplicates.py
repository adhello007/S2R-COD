#!/usr/bin/env python
"""D2 export -- materialise the CHAMELEON / Target duplicate pairs for inspection.

Not a measurement. Every number it writes is recomputed from the images and must
agree with log block EXP D2; this script exists so the finding can be LOOKED at
rather than taken on trust.

What it produces under rebuild/D2/duplicates/:

  chameleon/            the CHAMELEON endpoint images, as-is
  target/               their nearest Target training-pool partners, as-is
  pairs/                one PNG per pair: CHAMELEON | Target | amplified diff
  contact_sheet_*.png   grids for scanning all pairs at once
  d2_duplicate_pairs.csv  per-pair measurements

The diff panel is amplified (default 20x) because the whole point is that these
differ only by JPEG re-encoding: at 1x the difference image looks black, which
would be misleading in the opposite direction.

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2/d2_export_duplicates.py
  LAKE-RED/.venv/bin/python rebuild/D2/d2_export_duplicates.py --endpoint nc4k --tol 6
"""

import argparse
import csv
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image, ImageDraw, ImageFont                   # noqa: E402

EXP = 'D2'
OUT = C.exp_dir(EXP, 'out')
DUP = C.exp_dir(EXP, 'duplicates')

PANEL_H = 420          # per-panel height in a pair figure
THUMB_H = 132          # per-panel height in a contact sheet
AMPLIFY = 20           # diff amplification
PAD = 12
BG = (250, 250, 250)
INK = (20, 20, 20)
ACCENT = (170, 30, 30)


def _font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'):
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


F_HEAD = _font(19)
F_SUB = _font(14)
F_TINY = _font(11)


def qtable(path):
    try:
        q = Image.open(path).quantization
        return tuple(tuple(v) for v in q.values()) if q else None
    except Exception:
        return None


def scaled(im, h):
    w = max(1, int(round(im.width * h / im.height)))
    return im.resize((w, h), Image.LANCZOS)


def load_pairs(endpoint, tol):
    """Read the pairs straight out of s4b's output -- no re-derivation of WHICH
    pairs count, only of their measurements."""
    src = os.path.join(OUT, 'd2_endpoint_nearest.csv')
    if not os.path.isfile(src):
        raise SystemExit('missing %s -- run d2_leakage_sweep.py --steps s4b' % src)
    rows = []
    for r in csv.DictReader(open(src)):
        if r['endpoint'] != endpoint or not r['nearest']:
            continue
        if float(r['nearest']) <= tol:
            rows.append(r)
    rows.sort(key=lambda r: float(r['nearest']))
    return rows


def measure(pa, pb):
    A = np.asarray(Image.open(pa).convert('RGB'), np.int16)
    B = np.asarray(Image.open(pb).convert('RGB'), np.int16)
    if A.shape != B.shape:
        return None
    d = np.abs(A - B)
    return dict(mean_abs=float(d.mean()), max_abs=int(d.max()),
                p99_abs=float(np.percentile(d, 99)),
                frac_gt8=float((d > 8).mean()),
                content_std=float(A.std()), diff=d.astype(np.uint8))


def pair_figure(idx, n, ep, ename, tname, pa, pb, m, amplify):
    a = scaled(Image.open(pa).convert('RGB'), PANEL_H)
    b = scaled(Image.open(pb).convert('RGB'), PANEL_H)
    dmap = Image.fromarray(np.clip(m['diff'].astype(np.int32) * amplify, 0, 255)
                           .astype(np.uint8))
    dmap = scaled(dmap, PANEL_H)

    head_h, label_h = 74, 46
    W = PAD * 4 + a.width + b.width + dmap.width
    H = head_h + PANEL_H + label_h + PAD
    fig = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(fig)

    dr.text((PAD, 8), '[%d/%d]  %s  vs  %s' % (idx, n, ename, tname),
            font=F_HEAD, fill=INK)
    dr.text((PAD, 32),
            'same dimensions %dx%d   mean|diff| %.3f   p99 %.0f   max %d   '
            '%.2f%% of pixels differ by >8   content std %.1f'
            % (Image.open(pa).width, Image.open(pa).height, m['mean_abs'],
               m['p99_abs'], m['max_abs'], 100 * m['frac_gt8'], m['content_std']),
            font=F_SUB, fill=INK)
    dr.text((PAD, 52),
            'JPEG quantization tables: %s   ->  the same photograph, re-encoded'
            % ('IDENTICAL' if m['q_same'] else 'DIFFERENT'),
            font=F_SUB, fill=ACCENT)

    x = PAD
    for im, cap in ((a, 'CHAMELEON  (endpoint / test)  %s' % _kb(pa)),
                    (b, 'Target pool  (unlabeled TRAINING)  %s' % _kb(pb)),
                    (dmap, '|difference| x%d' % amplify)):
        fig.paste(im, (x, head_h))
        dr.text((x, head_h + PANEL_H + 6), cap, font=F_TINY, fill=INK)
        x += im.width + PAD
    return fig


def _kb(p):
    return '%d KB' % round(os.path.getsize(p) / 1024)


def contact_sheet(items, amplify, per_page=14):
    """Grid: one row per pair, three panels each."""
    pages = []
    for start in range(0, len(items), per_page):
        chunk = items[start:start + per_page]
        rows = []
        for it in chunk:
            a = scaled(Image.open(it['pa']).convert('RGB'), THUMB_H)
            b = scaled(Image.open(it['pb']).convert('RGB'), THUMB_H)
            d = scaled(Image.fromarray(
                np.clip(it['m']['diff'].astype(np.int32) * amplify, 0, 255)
                .astype(np.uint8)), THUMB_H)
            rows.append((a, b, d, it))
        cap_w = 330
        W = cap_w + PAD * 4 + max(a.width + b.width + d.width for a, b, d, _ in rows)
        H = PAD + len(rows) * (THUMB_H + PAD) + 46
        sheet = Image.new('RGB', (W, H), BG)
        dr = ImageDraw.Draw(sheet)
        dr.text((PAD, 8),
                'CHAMELEON images that are re-encodes of unlabeled Target training '
                'images  -  page %d/%d  -  diff amplified x%d'
                % (start // per_page + 1, (len(items) + per_page - 1) // per_page,
                   amplify),
                font=F_SUB, fill=INK)
        y = 38
        for a, b, d, it in rows:
            dr.text((PAD, y + 4), '%s' % it['ename'], font=F_TINY, fill=INK)
            dr.text((PAD, y + 20), '%s' % it['tname'][:44], font=F_TINY, fill=INK)
            dr.text((PAD, y + 36), 'mean|diff| %.2f   %s'
                    % (it['m']['mean_abs'], it['dims']), font=F_TINY, fill=ACCENT)
            x = cap_w
            for im in (a, b, d):
                sheet.paste(im, (x, y))
                x += im.width + PAD
            y += THUMB_H + PAD
        pages.append(sheet)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--endpoint', default='cham')
    ap.add_argument('--tol', type=float, default=6.0)
    ap.add_argument('--amplify', type=int, default=AMPLIFY)
    args = ap.parse_args()

    rows = load_pairs(args.endpoint, args.tol)
    print('%d %s pairs at mean|diff| <= %.1f' % (len(rows), args.endpoint, args.tol))

    for sub in ('chameleon', 'target', 'pairs'):
        d = os.path.join(DUP, sub)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)

    items, manifest = [], []
    for i, r in enumerate(rows, 1):
        ename, tname = r['name'], r['nearest_name']
        pa = os.path.join(C.ipath(args.endpoint), ename)
        pb = os.path.join(C.ipath(r['nearest_split']), tname)
        m = measure(pa, pb)
        if m is None:
            print('  skip (shape mismatch): %s' % ename)
            continue
        m['q_same'] = (qtable(pa) == qtable(pb))
        shutil.copyfile(pa, os.path.join(DUP, 'chameleon', ename))
        shutil.copyfile(pb, os.path.join(DUP, 'target', tname))
        fig = pair_figure(i, len(rows), args.endpoint, ename, tname, pa, pb, m,
                          args.amplify)
        fig.save(os.path.join(DUP, 'pairs', '%02d_%s.png'
                              % (i, os.path.splitext(ename)[0])))
        items.append(dict(ename=ename, tname=tname, pa=pa, pb=pb, m=m,
                          dims=r['dims']))
        manifest.append(dict(
            rank=i, endpoint=args.endpoint, endpoint_image=ename,
            training_split=r['nearest_split'], training_image=tname,
            dims=r['dims'], mean_abs=round(m['mean_abs'], 3),
            p99_abs=round(m['p99_abs'], 1), max_abs=m['max_abs'],
            frac_gt8=round(m['frac_gt8'], 5),
            content_std=round(m['content_std'], 1),
            qtables_identical=int(m['q_same']),
            endpoint_kb=round(os.path.getsize(pa) / 1024),
            training_kb=round(os.path.getsize(pb) / 1024)))
        print('  [%2d] %-16s <-> %-46s mean|d|=%6.3f' % (i, ename, tname[:46],
                                                         m['mean_abs']))

    with open(os.path.join(DUP, 'd2_duplicate_pairs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    # a tracked copy of the manifest, so the finding is auditable without the images
    shutil.copyfile(os.path.join(DUP, 'd2_duplicate_pairs.csv'),
                    os.path.join(OUT, 'd2_duplicate_pairs.csv'))

    for i, sheet in enumerate(contact_sheet(items, args.amplify), 1):
        sheet.save(os.path.join(DUP, 'contact_sheet_%d.png' % i))

    q_diff = sum(1 for m in manifest if not m['qtables_identical'])
    print('\nwrote %d pairs to %s' % (len(manifest), DUP))
    print('quantization tables differ in %d/%d pairs (re-encode evidence)'
          % (q_diff, len(manifest)))
    print('mean|diff| range: %.3f .. %.3f'
          % (min(m['mean_abs'] for m in manifest),
             max(m['mean_abs'] for m in manifest)))


if __name__ == '__main__':
    main()

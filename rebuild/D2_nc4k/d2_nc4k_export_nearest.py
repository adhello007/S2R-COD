#!/usr/bin/env python
"""D2_NC4K export -- render the CLOSEST NC4K / COD10K pairs for visual inspection.

Not a measurement. Every number it draws is recomputed from the images and must agree
with log block EXP D2_NC4K.

The CHAMELEON audit exported its confirmed duplicates so a human could see that they
were the same photograph. This experiment found NO confirmed pairs, so the equivalent
check is the opposite one: render the pairs that came CLOSEST to matching and confirm
by eye that they are plainly different photographs. A null that has been looked at is
worth more than a null that has only been computed.

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2_nc4k/d2_nc4k_export_nearest.py [--n 3] [--other test]
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image, ImageDraw, ImageFont                   # noqa: E402

OUT = C.exp_dir('D2_nc4k', 'out')
DST = C.exp_dir('D2_nc4k', 'cache', 'nearest')
NC4K = 'Dataset/Test/NC4K/Imgs'
OTHER = {'test': 'Dataset/Test/COD10K/Imgs',
         'train': 'rebuild/D2_nc4k/cache/cod10k_train'}
PANEL_H, PAD, AMPLIFY = 420, 12, 20
BG, INK, ACCENT = (250, 250, 250), (20, 20, 20), (170, 30, 30)


def _font(s):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, s)
            except Exception:
                pass
    return ImageFont.load_default()


F_HEAD, F_SUB, F_TINY = _font(19), _font(14), _font(11)


def scaled(im, h):
    return im.resize((max(1, int(round(im.width * h / im.height))), h),
                     Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--other', default='test', choices=list(OTHER))
    args = ap.parse_args()

    src = os.path.join(OUT, 'd2nc4k_nearest_%s.csv' % args.other)
    if not os.path.isfile(src):
        raise SystemExit('missing %s -- run d2_nc4k_crosscheck.py first' % src)
    rows = [r for r in csv.DictReader(open(src)) if r['nearest']]
    rows.sort(key=lambda r: float(r['nearest']))
    rows = rows[:args.n]
    os.makedirs(DST, exist_ok=True)

    print('the %d closest NC4K / COD10K-%s pairs (none confirmed; tolerance was 6.0)'
          % (len(rows), args.other))
    for i, r in enumerate(rows, 1):
        pa = os.path.join(C.REPO, NC4K, r['name'])
        pb = os.path.join(C.REPO, OTHER[args.other], r['nearest_name'])
        A = np.asarray(Image.open(pa).convert('RGB'), np.int16)
        B = np.asarray(Image.open(pb).convert('RGB'), np.int16)
        d = np.abs(A - B)
        a = scaled(Image.open(pa).convert('RGB'), PANEL_H)
        b = scaled(Image.open(pb).convert('RGB'), PANEL_H)
        dm = scaled(Image.fromarray(np.clip(d.astype(np.int32) * AMPLIFY, 0, 255)
                                    .astype(np.uint8)), PANEL_H)
        head = 74
        fig = Image.new('RGB', (PAD * 4 + a.width + b.width + dm.width,
                                head + PANEL_H + 46 + PAD), BG)
        dr = ImageDraw.Draw(fig)
        dr.text((PAD, 8), '[closest %d/%d]  %s  vs  %s'
                % (i, len(rows), r['name'], r['nearest_name']), font=F_HEAD, fill=INK)
        dr.text((PAD, 32), 'same dimensions %s   mean|diff| %.3f   max %d   '
                           'content std %.1f'
                % (r['dims'], float(d.mean()), int(d.max()), float(A.std())),
                font=F_SUB, fill=INK)
        dr.text((PAD, 52), 'NOT a match: mean|diff| %.3f is %.1fx the confirmation '
                           'tolerance of 6.0  ->  different photographs'
                % (float(d.mean()), float(d.mean()) / 6.0), font=F_SUB, fill=ACCENT)
        x = PAD
        for im, cap in ((a, 'NC4K  (test)'),
                        (b, 'COD10K-%s' % args.other),
                        (dm, '|difference| x%d' % AMPLIFY)):
            fig.paste(im, (x, head))
            dr.text((x, head + PANEL_H + 6), cap, font=F_TINY, fill=INK)
            x += im.width + PAD
        out = os.path.join(DST, '%02d_%s_vs_%s.png'
                           % (i, os.path.splitext(r['name'])[0],
                              os.path.splitext(r['nearest_name'])[0][:40]))
        fig.save(out)
        print('  [%d] %-12s <-> %-46s mean|d|=%7.3f  -> %s'
              % (i, r['name'], r['nearest_name'][:46], float(d.mean()),
                 os.path.relpath(out, C.REPO)))


if __name__ == '__main__':
    main()

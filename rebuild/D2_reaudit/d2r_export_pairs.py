#!/usr/bin/env python
"""D2R export -- materialise the canonical-CHAMELEON / training pairs for inspection.

Not a measurement. Every number it draws is recomputed from the images and must
agree with log block EXP D2R; this script exists so the finding can be LOOKED at
rather than taken on trust. A human -- you, a supervisor, a reviewer -- has to be
able to see that these are the same photographs.

Mirrors rebuild/D2/d2_export_duplicates.py, including its layout constants, so the
canonical export and D2's own export are visually comparable side by side. The
CHAMELEON side is `Dataset/chameleon_new/animals` (author-sourced) rather than the
repo's repackaged copy.

What it produces under rebuild/D2_reaudit/pairs/ (gitignored):

  chameleon_canonical/  the canonical CHAMELEON images, as-is
  target/               their nearest training-pool partners, as-is
  pairs/                one PNG per pair: CHAMELEON | training partner | amplified diff
  contact_sheet_*.png   grids for scanning every pair at once

The diff panel is amplified (default 20x) because the whole point is that these
differ only by JPEG re-encoding: at 1x the difference image looks black, which
would mislead in the opposite direction.

Usage:
  LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_export_pairs.py
  LAKE-RED/.venv/bin/python rebuild/D2_reaudit/d2r_export_pairs.py --endpoint cham
"""

import argparse
import csv
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C                                            # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect_contamination as DET                            # noqa: E402

import numpy as np                                            # noqa: E402
from PIL import Image, ImageDraw, ImageFont                   # noqa: E402

OUT = C.exp_dir('D2_reaudit', 'out')
PAIRS = C.exp_dir('D2_reaudit', 'pairs')

# layout constants, identical to d2_export_duplicates.py:41-48
PANEL_H = 420
THUMB_H = 132
AMPLIFY = 20
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


F_HEAD, F_SUB, F_TINY = _font(19), _font(14), _font(11)

SIDE_LABEL = {'chamnew': 'CHAMELEON  (author-sourced release)',
              'cham': 'CHAMELEON  (repo copy)'}


def _kb(p):
    return '%d KB' % round(os.path.getsize(p) / 1024)


def scaled(im, h):
    w = max(1, int(round(im.width * h / im.height)))
    return im.resize((w, h), Image.LANCZOS)


def load_pairs(endpoint, tol):
    """Read the pairs straight out of s4br's output -- no re-derivation of WHICH
    pairs count, only of their measurements. Same selection route D2 used."""
    src = os.path.join(OUT, 'd2r_endpoint_nearest.csv')
    if not os.path.isfile(src):
        raise SystemExit('missing %s -- run d2r_reaudit.py --steps s4br' % src)
    rows = [r for r in csv.DictReader(open(src))
            if r['endpoint'] == endpoint and r['nearest']
            and float(r['nearest']) <= tol]
    rows.sort(key=lambda r: float(r['nearest']))
    if not rows:
        raise SystemExit('no pairs for endpoint %r at tol %s' % (endpoint, tol))
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
    dmap = scaled(Image.fromarray(
        np.clip(m['diff'].astype(np.int32) * amplify, 0, 255).astype(np.uint8)),
        PANEL_H)

    head_h, label_h = 74, 46
    W = PAD * 4 + a.width + b.width + dmap.width
    H = head_h + PANEL_H + label_h + PAD
    fig = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(fig)
    with Image.open(pa) as src:
        w0, h0 = src.size

    dr.text((PAD, 8), '[%d/%d]  %s  vs  %s' % (idx, n, ename, tname),
            font=F_HEAD, fill=INK)
    dr.text((PAD, 32),
            'same dimensions %dx%d   mean|diff| %.3f   p99 %.0f   max %d   '
            '%.2f%% of pixels differ by >8   content std %.1f'
            % (w0, h0, m['mean_abs'], m['p99_abs'], m['max_abs'],
               100 * m['frac_gt8'], m['content_std']), font=F_SUB, fill=INK)
    if m['q_verdict'] == 'na':
        ev = ('no comparable JPEG table (%s vs %s) -- the CONTAINER FORMATS '
              'differ, which is itself re-encoding evidence'
              % (m['fmt_a'], m['fmt_b']))
    else:
        ev = ('JPEG quantization tables: %s   ->  the same photograph, re-encoded'
              % ('IDENTICAL' if m['q_verdict'] == 'same' else 'DIFFERENT'))
    dr.text((PAD, 52), ev, font=F_SUB, fill=ACCENT)

    x = PAD
    for im, cap in ((a, '%s  %s' % (SIDE_LABEL.get(ep, ep), _kb(pa))),
                    (b, 'Target pool  (unlabeled TRAINING)  %s' % _kb(pb)),
                    (dmap, '|difference| x%d' % amplify)):
        fig.paste(im, (x, head_h))
        dr.text((x, head_h + PANEL_H + 6), cap, font=F_TINY, fill=INK)
        x += im.width + PAD
    return fig


def contact_sheet(items, amplify, ep, per_page=14):
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
                '%s images that are re-encodes of unlabeled Target training images  '
                '-  page %d/%d  -  diff amplified x%d'
                % (SIDE_LABEL.get(ep, ep), start // per_page + 1,
                   (len(items) + per_page - 1) // per_page, amplify),
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
    ap.add_argument('--endpoint', default='chamnew',
                    help='chamnew = author-sourced (default); cham = the repo copy')
    ap.add_argument('--tol', type=float, default=6.0)
    ap.add_argument('--amplify', type=int, default=AMPLIFY)
    args = ap.parse_args()

    rows = load_pairs(args.endpoint, args.tol)
    for sub in ('chameleon_canonical', 'target', 'pairs'):
        d = os.path.join(PAIRS, sub)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)

    print('exporting %d pairs for endpoint %s at tol %s'
          % (len(rows), args.endpoint, args.tol))
    items, q_diff, q_na, q_fmt = [], 0, 0, 0
    for i, r in enumerate(rows, 1):
        ename, tname = r['name'], r['nearest_name']
        pa = os.path.join(C.ipath(args.endpoint), ename)
        pb = os.path.join(C.ipath(r['nearest_split']), tname)
        m = measure(pa, pb)
        if m is None:
            print('  skip (shape mismatch): %s' % ename)
            continue
        m['q_same_pil'] = (DET.qtable_pil(pa) == DET.qtable_pil(pb))
        v, _agree, _qa, _qb = DET.qtable_verdict(pa, pb)
        m['q_verdict'] = v
        m['fmt_a'] = DET.container_format(pa)
        m['fmt_b'] = DET.container_format(pb)
        q_diff += int(v == 'differ')
        q_na += int(v == 'na')
        q_fmt += int(v == 'na' and m['fmt_a'] != m['fmt_b'])
        shutil.copyfile(pa, os.path.join(PAIRS, 'chameleon_canonical', ename))
        shutil.copyfile(pb, os.path.join(PAIRS, 'target', tname))
        fig = pair_figure(i, len(rows), args.endpoint, ename, tname, pa, pb, m,
                          args.amplify)
        fig.save(os.path.join(PAIRS, 'pairs', '%02d_%s.png'
                              % (i, os.path.splitext(ename)[0])))
        items.append(dict(ename=ename, tname=tname, pa=pa, pb=pb, m=m,
                          dims=r['dims']))
        print('  [%2d] %-16s <-> %-46s mean|d|=%6.3f' % (i, ename, tname[:46],
                                                         m['mean_abs']))

    for i, sheet in enumerate(contact_sheet(items, args.amplify, args.endpoint), 1):
        sheet.save(os.path.join(PAIRS, 'contact_sheet_%d.png' % i))

    print('\nquantization tables differ in %d/%d pairs (re-encode evidence)'
          % (q_diff, len(items)))
    if q_na:
        print('%d/%d pair(s) carry no comparable JPEG table; %d of those differ in '
              'CONTAINER FORMAT, which is re-encoding evidence in its own right'
              % (q_na, len(items), q_fmt))
        print('so %d/%d pairs carry independent re-encoding evidence'
              % (q_diff + q_fmt, len(items)))
    print('mean|diff| range: %.3f .. %.3f' % (items[0]['m']['mean_abs'],
                                              items[-1]['m']['mean_abs']))
    print('wrote %s' % PAIRS)
    print('The per-pair manifest is tracked at '
          'rebuild/D2_reaudit/out/d2r_duplicate_pairs.csv; these images are not.')


if __name__ == '__main__':
    main()

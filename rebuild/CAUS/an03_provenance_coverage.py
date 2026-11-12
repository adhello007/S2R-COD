#!/usr/bin/env python
"""CAUS AN-03 -- foreground provenance, mask QC and target-manifold coverage, re-measured independently.

1. Provenance (own code; D1's committed per-image table is the cross-check). For every stem: the LAKE-RED
   render vs its raw HKU-IS photograph under raw_gt, and the authors' pool image vs the raw photograph
   under auth_gt. Interior = mask eroded 3 px (cv2.erode, 3x3 cross... applied 3 times), scored when
   >= 50 px. "Regenerated" = interior mean|diff| > 40 on 0-255 (D1's threshold, reused so the counts
   are comparable). Also: background mean|diff|, foreground identity count (unique raw sha256).
2. Mask QC on the 4447 render masks (= raw_gt): empty / full masks, foreground fraction, connected
   components, holes, binary-ness. Same gate for every arm: these masks are shared by all arms.
3. Coverage (own k-NN recall implementation, Kynkaenniemi et al. 2019): fraction of the 4040 target
   embeddings inside the union of k-NN balls of a compared set, frozen E0 embeddings, L2-normalised,
   Euclidean; k in {3, 5, 10, 20}; compared against rebuild/A3/out/a3_coverage.csv.
Writes RESULT_TABLES/AN-03_foreground_provenance.csv, AN-03_coverage_and_qc.csv.
"""

import csv
import os
import sys
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

import numpy as np                                             # noqa: E402

RAW = 'Dataset/Source/HKU-IS_raw/imgs'
RAW_GT = 'Dataset/Source/HKU-IS_raw/gt'
REN = 'Dataset/LAKERED/output/HKU-IS/images'
REN_MSK = 'Dataset/LAKERED/output/HKU-IS/masks'
AUTH = 'Dataset/Source/HKU-IS/Image'
AUTH_GT = 'Dataset/Source/HKU-IS/GT'


def _trace(args):
    import cv2
    stem, raw_p, gt_p, cand_p = args
    raw = cv2.imread(raw_p, cv2.IMREAD_COLOR)
    cand = cv2.imread(cand_p, cv2.IMREAD_COLOR)
    gt = cv2.imread(gt_p, cv2.IMREAD_GRAYSCALE)
    if raw is None or cand is None or gt is None:
        return dict(stem=stem, status='UNREADABLE')
    if raw.shape != cand.shape:
        return dict(stem=stem, status='SHAPE-MISMATCH')
    if gt.shape != raw.shape[:2]:
        gt = cv2.resize(gt, (raw.shape[1], raw.shape[0]), interpolation=cv2.INTER_NEAREST)
    fg = (gt >= 128).astype(np.uint8)
    if fg.sum() == 0 or fg.sum() == fg.size:
        return dict(stem=stem, status='DEGENERATE-MASK')
    d = np.abs(raw.astype(np.int16) - cand.astype(np.int16))
    er = cv2.erode(fg, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=3).astype(bool)
    rec = dict(stem=stem, status='OK', obj_mean=float(d[fg.astype(bool)].mean()),
               bg_mean=float(d[~fg.astype(bool)].mean()), interior_px=int(er.sum()), interior_mean='')
    if er.sum() >= 50:
        rec['interior_mean'] = float(d[er].mean())
    return rec


def _mask_qc(p):
    import cv2
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    b = (m >= 128).astype(np.uint8)
    frac = float(b.mean())
    n_fg, _ = cv2.connectedComponents(b)
    n_bg, _ = cv2.connectedComponents(1 - b)
    nonbinary = float(((m > 10) & (m < 245)).mean())
    return dict(frac=frac, comps=n_fg - 1, holes=max(n_bg - 2, 0), nonbinary=nonbinary)


def knn_recall(real, other, k):
    """Fraction of `real` points inside the union of k-NN balls of `other` (radius = distance from each
    `other` point to its k-th nearest neighbour within `other`)."""
    o2 = (other ** 2).sum(1)
    D = np.sqrt(np.maximum(o2[:, None] + o2[None, :] - 2 * other @ other.T, 0))
    np.fill_diagonal(D, np.inf)
    rad = np.sort(D, axis=1)[:, k - 1]
    r2 = (real ** 2).sum(1)
    inside = np.zeros(len(real), bool)
    for s in range(0, len(real), 1024):
        Dr = np.sqrt(np.maximum(r2[s:s + 1024, None] + o2[None, :] - 2 * real[s:s + 1024] @ other.T, 0))
        inside[s:s + 1024] = (Dr <= rad[None, :]).any(1)
    return float(inside.mean())


def main():
    stems = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(K.REPO, RAW)))
    raw_ext = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(K.REPO, RAW))}
    j = lambda *a: os.path.join(K.REPO, *a)                    # noqa: E731
    jobs_local = [(s, j(RAW, raw_ext[s]), j(RAW_GT, s + '.png'), j(REN, 'SOD_%s.jpg' % s)) for s in stems]
    jobs_auth = [(s, j(RAW, raw_ext[s]), j(AUTH_GT, s + '.png'), j(AUTH, s + '.jpg')) for s in stems]
    with Pool(8) as pool:
        loc = pool.map(_trace, jobs_local, chunksize=32)
        aut = pool.map(_trace, jobs_auth, chunksize=32)
        qc = pool.map(_mask_qc, [j(REN_MSK, 'SOD_%s.png' % s) for s in stems], chunksize=64)
    prov = []
    for pool_name, recs, d1 in (('local renders (LAKE-RED, this campaign)', loc, 'rebuild/D1/out/d1_trace_local.csv'),
                                ("authors' pool", aut, 'rebuild/D1/out/d1_trace_auth.csv')):
        ok = [r for r in recs if r['status'] == 'OK']
        inter = [r for r in ok if r['interior_mean'] != '']
        ref = {r['stem']: r for r in csv.DictReader(open(j(d1)))}
        diffs = [abs(r['interior_mean'] - float(ref[r['stem']]['obj_interior_mean'])) for r in inter
                 if ref.get(r['stem'], {}).get('obj_interior_mean') not in (None, '')]
        prov.append(dict(pool=pool_name, n_files=len(recs), traced_ok=len(ok), interior_scored=len(inter),
                         regenerated_interior_gt40=sum(r['interior_mean'] > 40 for r in inter),
                         max_interior_mean=round(max(r['interior_mean'] for r in inter), 3),
                         mean_interior=round(float(np.mean([r['interior_mean'] for r in inter])), 3),
                         mean_background=round(float(np.mean([r['bg_mean'] for r in ok])), 3),
                         interior_3x_closer=sum(r['interior_mean'] * 3 < r['bg_mean'] for r in inter),
                         vs_D1_interior_mean_absdiff_median=round(float(np.median(diffs)), 4) if diffs else '',
                         vs_D1_interior_mean_absdiff_max=round(float(np.max(diffs)), 4) if diffs else ''))
    raw_sha = [K.sha256(j(RAW, raw_ext[s])) for s in stems]
    prov.append(dict(pool='foreground identities (raw HKU-IS photographs)', n_files=len(stems),
                     traced_ok=len(set(raw_sha)), interior_scored='', regenerated_interior_gt40='',
                     max_interior_mean='', mean_interior='', mean_background='', interior_3x_closer='',
                     vs_D1_interior_mean_absdiff_median='unique sha256 count in traced_ok',
                     vs_D1_interior_mean_absdiff_max=''))
    K.write_csv(os.path.join(K.TABLES, 'AN-03_foreground_provenance.csv'), prov)
    for r in prov:
        print(r)

    rows = []
    fr = np.array([q['frac'] for q in qc])
    rows += [dict(block='mask QC (4447 render masks, shared by every arm)', item=k, value=v) for k, v in (
        ('empty masks (fg fraction = 0)', int((fr == 0).sum())), ('full masks (fg fraction = 1)', int((fr == 1).sum())),
        ('fg fraction median', round(float(np.median(fr)), 4)), ('fg fraction 5th-95th pct',
                                                                 '%.4f-%.4f' % tuple(np.percentile(fr, [5, 95]))),
        ('masks with >1 connected component', int(sum(q['comps'] > 1 for q in qc))),
        ('masks with >=1 hole', int(sum(q['holes'] >= 1 for q in qc))),
        ('mean share of non-binary pixels (10<v<245)', round(float(np.mean([q['nonbinary'] for q in qc])), 5)))]
    # coverage
    cache = os.path.join(K.REPO, 'rebuild/E0/cache')
    a3 = list(csv.DictReader(open(j('rebuild/A3/out/a3_coverage.csv'))))
    setmap = {'local renders': 'local', "authors' pool": 'auth', 'raw HKU-IS (pre-LAKE-RED)': 'raw'}
    for emb in ('dinoL224', 'dinoL518', 'clipL224'):
        T = np.load(os.path.join(cache, '%s_tgt_cls.npy' % emb)).astype(np.float64)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        for label, key in setmap.items():
            O = np.load(os.path.join(cache, '%s_%s_cls.npy' % (emb, key))).astype(np.float64)
            O /= np.linalg.norm(O, axis=1, keepdims=True)
            for k in (3, 5, 10, 20):
                rec = knn_recall(T, O, k)
                ref = next((float(r['recall']) for r in a3 if r['embedder'] == emb and r['set'] == label
                            and int(r['k']) == k), None)
                rows.append(dict(block='coverage: kNN recall of the 4040 target images', item='%s | %s | k=%d' % (emb, label, k),
                                 value=round(rec, 4), committed_a3=round(ref, 4) if ref is not None else '',
                                 abs_diff=round(abs(rec - ref), 5) if ref is not None else ''))
                print('%-9s %-28s k=%2d recall %.4f (A3 %s)' % (emb, label, k, rec, ref))
    K.write_csv(os.path.join(K.TABLES, 'AN-03_coverage_and_qc.csv'), rows,
                ['block', 'item', 'value', 'committed_a3', 'abs_diff'])
    for r in rows[:7]:
        print(r)


if __name__ == '__main__':
    main()

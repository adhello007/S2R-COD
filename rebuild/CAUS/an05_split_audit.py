#!/usr/bin/env python
"""CAUS AN-05 -- split, exposure and leakage audit, computed independently of D2's code.

1. Every split re-hashed from the bytes on disk (sha256); per-split counts and content digests.
2. Exact cross-split collisions by sha256, every pair of splits.
3. Re-encode-tolerant near-duplicates: 64-bit difference hash (9x8 grey, PIL LANCZOS), every pair of
   splits that matters for leakage, Hamming <= 6 shortlisted, then CONFIRMED when the two images,
   resized to 256x256 grey, differ by mean |.| < 8/255. Own implementation; D2's committed counts
   are the cross-check, not an input.
4. The role ledger: which labelled image sets influence quotas, weights, pseudo-labels, checkpoint
   selection and endpoints, per arm family.
Writes RESULT_TABLES/AN-05_split_audit.csv, AN-05_cross_split_pairs.csv, AN-05_role_ledger.csv.
"""

import csv
import os
import sys
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

import numpy as np                                             # noqa: E402

SPLITS = {
    'tgt': 'Dataset/Target/Image', 'test': 'Dataset/Test/COD10K/Imgs', 'test_gt': 'Dataset/Test/COD10K/GT',
    'nc4k': 'Dataset/Test/NC4K/Imgs', 'nc4k_gt': 'Dataset/Test/NC4K/GT', 'val': 'Dataset/Val/CAMO/Imgs',
    'val_gt': 'Dataset/Val/CAMO/GT', 'raw': 'Dataset/Source/HKU-IS_raw/imgs', 'auth': 'Dataset/Source/HKU-IS/Image',
    'local': 'Dataset/LAKERED/output/HKU-IS/images', 'cham': 'Dataset/Test/CHAMELEON/Imgs',
}
IMAGE_SPLITS = ('tgt', 'test', 'nc4k', 'val', 'raw', 'auth', 'local', 'cham')
NEAR_PAIRS = (('tgt', 'test'), ('tgt', 'nc4k'), ('tgt', 'val'), ('test', 'nc4k'), ('test', 'val'),
              ('nc4k', 'val'), ('raw', 'test'), ('raw', 'nc4k'), ('raw', 'val'), ('local', 'test'),
              ('local', 'nc4k'), ('local', 'val'), ('auth', 'test'), ('auth', 'nc4k'), ('cham', 'val'))
HAM = 6
MAD = 8.0


def _hash_one(path):
    from PIL import Image
    h = K.sha256(path)
    im = Image.open(path).convert('L')
    small = np.asarray(im.resize((9, 8), Image.LANCZOS), dtype=np.int16)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    dh = int(np.packbits(bits).view('>u8')[0])
    return h, dh, im.size


def _mad(pair):
    from PIL import Image
    a, b = pair
    x = np.asarray(Image.open(a).convert('L').resize((256, 256), Image.BILINEAR), dtype=np.float64)
    y = np.asarray(Image.open(b).convert('L').resize((256, 256), Image.BILINEAR), dtype=np.float64)
    return float(np.abs(x - y).mean())


def popcount64(x):
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return ((x * np.uint64(0x0101010101010101)) >> np.uint64(56)).astype(np.int64)


def main():
    files = {k: sorted(os.listdir(os.path.join(K.REPO, v))) for k, v in SPLITS.items()}
    paths = {k: [os.path.join(K.REPO, SPLITS[k], f) for f in files[k]] for k in SPLITS}
    H, D = {}, {}
    with Pool(8) as pool:
        for k in SPLITS:
            if k in IMAGE_SPLITS:
                out = pool.map(_hash_one, paths[k], chunksize=64)
                H[k] = [o[0] for o in out]
                D[k] = np.array([o[1] for o in out], dtype=np.uint64)
            else:
                H[k] = pool.map(K.sha256, paths[k], chunksize=64)
    split_rows = [dict(split=k, path=SPLITS[k], n_files=len(files[k]),
                       content_sha256=K.list_digest(['%s %s' % (h, f) for h, f in zip(H[k], files[k])]),
                       n_unique_sha=len(set(H[k]))) for k in SPLITS]
    # exact collisions, every image-split pair
    pairs = []
    keys = list(IMAGE_SPLITS)
    for i, a in enumerate(keys):
        sa = {}
        for h, f in zip(H[a], files[a]):
            sa.setdefault(h, []).append(f)
        for b in keys[i + 1:]:
            for h, f in zip(H[b], files[b]):
                for fa in sa.get(h, []):
                    pairs.append(dict(split_a=a, file_a=fa, split_b=b, file_b=f, tier='exact sha256',
                                      hamming=0, mad_256=0.0))
    exact = {(p['split_a'], p['split_b']) for p in pairs}
    # near duplicates
    cand = []
    for a, b in NEAR_PAIRS:
        da, db = D[a], D[b]
        for s in range(0, len(da), 512):
            x = popcount64(da[s:s + 512, None] ^ db[None, :])
            ii, jj = np.nonzero(x <= HAM)
            for i, j in zip(ii, jj):
                cand.append((a, s + i, b, j, int(x[i, j])))
    with Pool(8) as pool:
        mads = pool.map(_mad, [(paths[a][i], paths[b][j]) for a, i, b, j, _ in cand], chunksize=16)
    have = {(p['split_a'], p['file_a'], p['split_b'], p['file_b']) for p in pairs}
    for (a, i, b, j, hm), m in zip(cand, mads):
        if (a, files[a][i], b, files[b][j]) in have:
            continue
        pairs.append(dict(split_a=a, file_a=files[a][i], split_b=b, file_b=files[b][j],
                          tier='near-duplicate (confirmed)' if m < MAD else 'dhash candidate, rejected by MAD',
                          hamming=hm, mad_256=round(m, 3)))
    K.write_csv(os.path.join(K.TABLES, 'AN-05_cross_split_pairs.csv'), pairs)
    summ = {}
    for p in pairs:
        k = (p['split_a'], p['split_b'], p['tier'])
        summ[k] = summ.get(k, 0) + 1
    for (a, b, t), n in sorted(summ.items()):
        split_rows.append(dict(split='%s x %s' % (a, b), path=t, n_files=n, content_sha256='', n_unique_sha=''))
        print('%-6s x %-6s %-34s %d' % (a, b, t, n))
    K.write_csv(os.path.join(K.TABLES, 'AN-05_split_audit.csv'), split_rows)
    for r in split_rows[:len(SPLITS)]:
        print('%-8s n=%5d unique=%5d %s' % (r['split'], r['n_files'], r['n_unique_sha'], r['content_sha256'][:16]))

    ledger = [
        dict(image_set='HKU-IS (authors\' 4447 pairs)', labels_used_for='supervised source loss, every arm', arms='all',
             endpoint_disjoint='yes (0 exact, see near-duplicate table)', risk='none identified'),
        dict(image_set='LAKE-RED renders of HKU-IS (4447) + render masks', labels_used_for='1000 appended pairs per arm',
             arms='B, C10, CSHUF, CINV, CORACLE, EXP-01 arms', endpoint_disjoint='yes', risk='foreground identity fixed (AN-03)'),
        dict(image_set='Target pool 4040 (COD10K-train 3040 + CAMO-train 1000), NO labels on disk',
             labels_used_for='none; images enter training unlabelled (consistency loss) and via round-2 pseudo-labels',
             arms='all', endpoint_disjoint='NO: 7 images byte-identical to COD10K-test (committed D2; re-measured here)',
             risk='transductive exposure of 7/2026 endpoint images, identical for every arm; their test masks are never read'),
        dict(image_set='CAMO-250 (Val/CAMO) images + GT', labels_used_for='checkpoint selection (CAMO MAE) in every arm',
             arms='all', endpoint_disjoint='yes for COD10K/NC4K; 3 byte-identical to CHAMELEON (not an endpoint)',
             risk='selection split, never an endpoint'),
        dict(image_set='COD10K-test GT (2026)', labels_used_for='(a) primary endpoint for all arms; (b) the oracle '
             'error vector that sets quotas for CORACLE and every EXP-01 oracle arm', arms='CORACLE, OR-PROP, OR-TOP10, '
             'OR-TOP5 (direction+shape); OR-TOP10-SHUF (shape only)', endpoint_disjoint='NO for the oracle arms',
             risk='endpoint-label-leaky: COD10K-test is not an unbiased endpoint for any oracle arm'),
        dict(image_set='COD10K-test GT (2026), standard arms', labels_used_for='endpoint scoring only',
             arms='B, C10, CSHUF, CINV', endpoint_disjoint='n/a', risk='none: allocation reads target ES only (gate G1)'),
        dict(image_set='NC4K GT (4121)', labels_used_for='secondary endpoint only; read by no allocation and no selection',
             arms='all', endpoint_disjoint='1 near-duplicate vs training in committed D2', risk='domain-coupled to COD10K, not label-coupled'),
        dict(image_set='CHAMELEON (76)', labels_used_for='nothing (withdrawn as an endpoint)', arms='none',
             endpoint_disjoint='NO: >=50/76 are training photographs', risk='never used as a clean endpoint'),
    ]
    K.write_csv(os.path.join(K.TABLES, 'AN-05_role_ledger.csv'), ledger)


if __name__ == '__main__':
    main()

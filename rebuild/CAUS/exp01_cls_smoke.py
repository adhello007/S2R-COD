#!/usr/bin/env python
"""CAUS EXP-01 pilot step 7 (optional) -- CLS round-2 smoke on this campaign's pool layout.

Calls the committed CLS.cls() exactly as MyTrain.py does for --task S2C (PGT_Loss = ESLoss(a=0.9,
b=0.3, c=0.5, use_weighted_bce=False), u=0.8, tau=0.4, iteration=1, network='SINet'). The model
comes from a HISTORICAL snapshot, which is only read. The source pool is a symlinked EXP-01 pool;
CLS copies it, dereferencing links, to <pool>_iteration2/. Checks: round-2 Image/GT counts equal,
stem parity on the real SrcDataset for every index, n_appended in (0, 4040].
Usage: exp01_cls_smoke.py <pool_dir> <model_dir> <out_json> [--gpu 0]
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

sys.path.insert(0, K.REPO)
os.chdir(K.REPO)


def main():
    pool, model_dir, out = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/', sys.argv[3]
    gpu = int(sys.argv[sys.argv.index('--gpu') + 1]) if '--gpu' in sys.argv else 0
    K.assert_writable(pool.rstrip('/') + '_iteration2')
    import torch
    from CLS import cls
    from Src.utils.tool import ESLoss
    from Src.utils.Dataloader import SrcDataset
    torch.cuda.set_device(gpu)
    pgt = ESLoss(a=0.9, b=0.3, c=0.5, use_weighted_bce=False).cuda()
    new_root = cls(model_dir, pool, pool, './Dataset/Target/', pgt, 0.8, 0.4, iteration=1, network='SINet')
    K.assert_writable(new_root)
    img = sorted(os.listdir(os.path.join(new_root, 'Image')))
    gt = sorted(os.listdir(os.path.join(new_root, 'GT')))
    n_base = len(os.listdir(os.path.join(pool, 'Image')))
    ds = SrcDataset(os.path.join(new_root, 'Image') + '/', os.path.join(new_root, 'GT') + '/', 352)
    stem = lambda f: os.path.splitext(os.path.basename(f))[0]  # noqa: E731
    mism = sum(1 for i in range(len(ds)) if stem(ds.images[i]) != stem(ds.gts[i]))
    n_app = len(img) - n_base
    links = sum(os.path.islink(os.path.join(new_root, 'Image', f)) for f in img[:200])
    res = dict(new_root=os.path.relpath(new_root, K.REPO), n_image=len(img), n_gt=len(gt),
               n_base=n_base, n_appended=n_app, parity_mismatches=mism, len_dataset=len(ds),
               symlinks_in_copy_first200=links, model_dir=model_dir)
    res['passed'] = bool(len(img) == len(gt) == len(ds) and mism == 0 and 0 < n_app <= 4040 and links == 0)
    K.save_json(out, res)
    print(res)
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main()

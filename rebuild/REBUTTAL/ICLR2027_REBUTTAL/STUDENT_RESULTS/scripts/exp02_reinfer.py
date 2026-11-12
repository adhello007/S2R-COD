#!/usr/bin/env python
"""EXP-02 two-image CPU re-inference check (ANALYSIS_PRESPEC.md §7). NO GPU: CUDA_VISIBLE_DEVICES=''.

Re-runs base MyTest.py's pipeline (test_dataset transform -> model -> bilinear upsample to GT size ->
sigmoid -> min-max -> cv2.imwrite(cam*255)) on CPU for runs SINet_C10_s46 and SINetv2_C10_s46, on the
first and last image of the sorted COD10K GT list, and compares with the stored prediction PNGs.

SINet_ResNet50's constructor would load ImageNet weights from a relative path; that step is skipped
(the checkpoint then overwrites every tensor, asserted below). SINet-v2 is built with
imagenet_pretrained=False for the same reason (no download).
Pass: max|diff| <= 2 grey levels and >= 99.9% of pixels within +-1.
"""
import argparse
import json
import os
import sys
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import cv2                       # noqa: E402
import numpy as np               # noqa: E402
import torch                     # noqa: E402
import torch.nn.functional as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--worktree', required=True)
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
WT, DR, SR = a.worktree, a.data_root, a.sr
sys.path.insert(0, WT)
sys.path.insert(0, os.path.join(WT, 'Eval'))
from Src.model.SINet.SINet import SINet_ResNet50                  # noqa: E402
from Src.model.SINetV2.Network_Res2Net_GRA_NCD import Network     # noqa: E402
from Src.utils.Dataloader import test_dataset                     # noqa: E402
import metrics as Measure                                         # noqa: E402

assert not torch.cuda.is_available(), 'GPU visible -- refusing to run'
torch.set_num_threads(4)
SINet_ResNet50.initialize_weights = lambda self: None
RUNS = [('SINet_C10_s46', 'SINet'), ('SINetv2_C10_s46', 'SINet-v2')]


def main():
    out_dir = os.path.join(SR, 'RUNS/exp02_reinfer')
    os.makedirs(out_dir, exist_ok=True)
    img_root = os.path.join(DR, 'Dataset/Test/COD10K/Imgs') + '/'
    gt_root = os.path.join(DR, 'Dataset/Test/COD10K/GT') + '/'
    loader = test_dataset(image_root=img_root, gt_root=gt_root, testsize=352, mode='test')
    gts = sorted(os.listdir(gt_root))
    targets = [gts[0], gts[-1]]
    res = []
    for rid, net in RUNS:
        model = SINet_ResNet50() if net == 'SINet' else Network(imagenet_pretrained=False)
        ck = os.path.join(DR, 'Snapshot/ABC', rid, 'Tea_epoch_best.pth')
        state = torch.load(ck, map_location='cpu')
        model.load_state_dict(state, strict=True)
        loaded = model.state_dict()
        copied = sum(torch.equal(v, loaded[k]) for k, v in state.items())
        assert copied == len(state) == len(loaded), (copied, len(state), len(loaded))
        model.eval()
        for gname in targets:
            loader.index = [os.path.basename(p).replace('.jpg', '.png') for p in loader.images].index(gname)
            image, gt, name, _ = loader.load_data()
            assert name == gname, (name, gname)
            gt = np.asarray(gt, np.float32)
            t0 = time.time()
            with torch.no_grad():
                if net == 'SINet':
                    _, cam = model(image)
                else:
                    _, _, _, cam = model(image)
                cam = F.interpolate(cam, size=gt.shape, mode='bilinear', align_corners=True)
                cam = cam.sigmoid().numpy().squeeze()
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
            os.makedirs(os.path.join(out_dir, rid), exist_ok=True)
            outp = os.path.join(out_dir, rid, name)
            cv2.imwrite(outp, cam * 255)
            mine = cv2.imread(outp, cv2.IMREAD_GRAYSCALE).astype(np.int32)
            stored = cv2.imread(os.path.join(DR, 'Result/ABC', rid, 'COD10K', name), cv2.IMREAD_GRAYSCALE).astype(np.int32)
            g8 = cv2.imread(os.path.join(gt_root, name), cv2.IMREAD_GRAYSCALE)
            d = np.abs(mine - stored)
            sm = []
            for p in (mine, stored):
                m = Measure.Smeasure()
                m.step(pred=p.astype(np.uint8), gt=g8)
                sm.append(float(m.get_results()['sm']))
            r = dict(runid=rid, image=name, shape=list(mine.shape), max_abs_diff=int(d.max()),
                     mean_abs_diff=float(d.mean()), frac_within_1=float((d <= 1).mean()),
                     sa_cpu=sm[0], sa_stored=sm[1], sa_abs_diff=abs(sm[0] - sm[1]), seconds=round(time.time() - t0, 1),
                     passed=bool(d.max() <= 2 and (d <= 1).mean() >= 0.999), tensors_loaded=copied,
                     checkpoint=os.path.relpath(ck, DR), device='cpu', torch=torch.__version__)
            res.append(r)
            print(json.dumps(r), flush=True)
    summ = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), rows=res,
                all_passed=all(r['passed'] for r in res),
                rule='max|diff| <= 2 grey levels and >= 99.9% of pixels within +-1 (ANALYSIS_PRESPEC.md §7)')
    json.dump(summ, open(os.path.join(SR, 'EXPERIMENT_LOGS/EXP-02_reinference.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != 'rows'}))


if __name__ == '__main__':
    main()

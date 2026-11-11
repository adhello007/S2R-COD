#!/usr/bin/env python
"""CAUS EXP-01 pilot step 3 -- two-batch SINet smoke test on an EXP-01 pool.

Mirrors MyTrain.trainer's SINet branch for --task S2C --method ours: supervised BCE-with-logits on
both SINet heads for the source batch, ES consistency loss between the EMA teacher (weak view) and
the student (strong view) on a target batch, backward, Adam step, EMA update. Losses and gradient
norms must be finite. Usage: exp01_smoke.py <pool_dir> <out_json> [--gpu 0]
"""

import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

sys.path.insert(0, K.REPO)
os.chdir(K.REPO)


def main():
    pool, out = sys.argv[1], sys.argv[2]
    gpu = int(sys.argv[sys.argv.index('--gpu') + 1]) if '--gpu' in sys.argv else 0
    import torch
    from Src.model.SINet.SINet import SINet_ResNet50
    from Src.utils.Dataloader import get_srcloader, get_tarloader
    from Src.utils.tool import ESLoss, set_random_seed, update_ema
    torch.cuda.set_device(gpu)
    set_random_seed(42)
    model = SINet_ResNet50(channel=32).cuda()
    ema = SINet_ResNet50(channel=32).cuda()
    for q, k in zip(model.parameters(), ema.parameters()):
        k.data.copy_(q.data)
    opt = torch.optim.Adam(model.parameters(), 1e-4)
    bce = torch.nn.BCEWithLogitsLoss()
    es = ESLoss(a=0.9, b=0.3, c=0.5).cuda()
    src = get_srcloader(os.path.join(pool, 'Image') + '/', os.path.join(pool, 'GT') + '/', 16, 352)
    tar = get_tarloader('./Dataset/Target/Image/', 16, 352)
    rec = []
    torch.cuda.reset_peak_memory_stats()
    for step, ((x, y), (tw, ts)) in enumerate(zip(src, tar)):
        opt.zero_grad()
        x, y, tw, ts = x.cuda(), y.cuda(), tw.cuda(), ts.cuda()
        sm, im = model(x)
        with torch.no_grad():
            _, t = ema(tw)
        _, s = model(ts)
        ls = bce(sm, y) + bce(im, y)
        lc = es(s.sigmoid(), t.sigmoid())
        (ls + lc).backward()
        gn = math.sqrt(sum(float(p.grad.detach().pow(2).sum()) for p in model.parameters() if p.grad is not None))
        opt.step()
        update_ema(model, ema, 0.996)
        rec.append(dict(step=step, loss_sup=float(ls), loss_con=float(lc), grad_norm=gn,
                        batch=list(x.shape), gt_range=[float(y.min()), float(y.max())]))
        if step == 1:
            break
    peak = torch.cuda.max_memory_allocated() / 2 ** 30
    ok = len(rec) == 2 and all(math.isfinite(r['loss_sup']) and math.isfinite(r['loss_con'])
                               and math.isfinite(r['grad_norm']) and r['grad_norm'] > 0 for r in rec)
    res = dict(passed=ok, steps=rec, peak_gpu_gb=round(peak, 2), n_source=len(src.dataset),
               n_target=len(tar.dataset))
    K.save_json(out, res)
    print(json.dumps(res, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

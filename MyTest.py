import torch
import torch.nn.functional as F
import numpy as np
import os
import argparse
from Src.model.SINet.SINet import SINet_ResNet50
from Src.model.SINetV2.Network_Res2Net_GRA_NCD import Network
from Src.model.SegMaR.SegMaR import Generator
from Src.utils.Dataloader import test_dataset
from Src.utils.tool import eval_mae, numpy2tensor
import cv2


parser = argparse.ArgumentParser()
parser.add_argument('--network', type=str, default='SINet-v2', choices=['SINet', 'SINet-v2', 'SegMaR'], help='Select the model architecture.')
parser.add_argument('--testsize', type=int, default=352, help='the snapshot input size')
parser.add_argument('--model_path', type=str,
                    default='./Snapshot/SINet-v2/test/Tea_epoch_best.pth')
parser.add_argument('--test_save', type=str,
                    default='./Result/SINet-v2/test/')
parser.add_argument('--gpu', type=int, default=0, help='choose which gpu you use')
opt = parser.parse_args()

torch.cuda.set_device(opt.gpu)

if opt.network == 'SINet':
    model = SINet_ResNet50().cuda()
elif opt.network == 'SINet-v2':
    model = Network().cuda()
elif opt.network == 'SegMaR':
    model = Generator().cuda()

# Load onto CPU and let load_state_dict copy across to the model's device.
# A state_dict whose tensors live on a *different* CUDA device than the model, is
# silently not copied at all -- load_state_dict still returns "All keys matched
# successfully", leaving a randomly initialised network. See CHECKPOINT_LOADING_BUG.md.
state_dict = torch.load(opt.model_path, map_location='cpu')
model.load_state_dict(state_dict)
loaded = model.state_dict()
copied = sum(torch.equal(v.to(loaded[k].device), loaded[k]) for k, v in state_dict.items())
assert copied == len(state_dict), (
    f'checkpoint load copied only {copied}/{len(state_dict)} tensors from '
    f'{opt.model_path} -- refusing to run inference on partially loaded weights')
model.eval()


for dataset in ['COD10K']:
    save_path = opt.test_save + '/'
    os.makedirs(save_path, exist_ok=True)

    test_loader = test_dataset(image_root='./Dataset/Test/Image/'.format(dataset),
                               gt_root='./Dataset/Test/GT/'.format(dataset),
                               testsize=opt.testsize,
                               mode='test')
    img_count = 1
    avg_mae = 0.0
    for iteration in range(test_loader.size):
        # load data
        image,  gt, name, _ = test_loader.load_data()
        gt = np.asarray(gt, np.float32)
        gt /= (gt.max() + 1e-8)
        image = image.cuda()
        # inference
        if opt.network == 'SINet':
            _, cam = model(image)
        elif opt.network == 'SINet-v2':
            _, _, _, res2 = model(image)
            cam = res2
        elif opt.network == 'SegMaR':
            _, cam = model(image)          # (fix_pred, cod_pred2)
        # reshape and squeeze
        cam = F.upsample(cam, size=gt.shape, mode='bilinear', align_corners=True)
        cam = cam.sigmoid().data.cpu().numpy().squeeze()
        # normalize
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        cv2.imwrite(save_path+name, cam*255)
        # evaluate
        mae = eval_mae(numpy2tensor(cam), numpy2tensor(gt))
        avg_mae += mae
        # coarse score
        print('[Eval-Test] Dataset: {}, Image: {} ({}/{}), MAE: {}'.format(dataset, name, img_count,
                                                                           test_loader.size, mae))
        img_count += 1

avg_mae /= test_loader.size
print("\n[Congratulations! Testing Done]")
print("\nAvg_MAE: {}".format(avg_mae))
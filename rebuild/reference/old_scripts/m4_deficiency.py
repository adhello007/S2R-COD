"""Does the plan's ES-disagreement term predict where the model is actually bad?
Reuses the repo's own ESLoss with the exact CLS.py:105/138 call convention."""
import os, sys, json, numpy as np, torch, torch.nn.functional as F
from PIL import Image
import torchvision.transforms as T
sys.path.insert(0,'/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD')
from Src.model.SINet.SINet import SINet_ResNet50
from Src.utils.tool import ESLoss
D='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Dataset'
SNAP='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Snapshot/SINet/S2C'
SP=os.path.dirname(os.path.abspath(__file__)); dev='cuda:0'

stu=SINet_ResNet50().to(dev); tea=SINet_ResNet50().to(dev)
stu.load_state_dict(torch.load(f'{SNAP}/Stu_40.pth',map_location='cpu'))
tea.load_state_dict(torch.load(f'{SNAP}/Tea_epoch_best.pth',map_location='cpu'))
stu.eval(); tea.eval()
# exactly MyTrain.py:286 / --task S2C overrides (a=0.9, b=0.3, unweighted BCE)
PGT = ESLoss(a=0.9, b=0.3, c=0.5, use_weighted_bce=False).to(dev)
tf=T.Compose([T.Resize((352,352)),T.ToTensor(),T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])

@torch.no_grad()
def score(img_dir, gt_dir, names):
    es,mae,iou=[],[],[]
    for n in names:
        stem=os.path.splitext(n)[0]
        im=Image.open(f'{img_dir}/{n}').convert('RGB')
        x=tf(im).unsqueeze(0).to(dev)
        _,s=stu(x); _,t=tea(x)
        es.append(PGT(s.sigmoid(), t.sigmoid()).item())          # CLS.py:105 convention
        gt=np.asarray(Image.open(f'{gt_dir}/{stem}.png').convert('L'),np.float32); gt/= (gt.max()+1e-8)
        cam=F.interpolate(t,size=gt.shape,mode='bilinear',align_corners=True).sigmoid().cpu().numpy().squeeze()
        cam=(cam-cam.min())/(cam.max()-cam.min()+1e-8)           # MyTest.py:72-75
        mae.append(float(np.abs(cam-gt).mean()))
        p,g=cam>=0.5,gt>=0.5
        iou.append(1.0-(np.logical_and(p,g).sum()/max(np.logical_or(p,g).sum(),1)))
    return np.array(es),np.array(mae),np.array(iou)

names=json.load(open(f'{SP}/dinoL_names.json'))
out={}
for split,idir,gdir in [('tst',f'{D}/Test/Image',f'{D}/Test/GT'),('val',f'{D}/Val/CAMO/Imgs',f'{D}/Val/CAMO/GT')]:
    e,m,i=score(idir,gdir,names[split]); out[split]=dict(es=e.tolist(),mae=m.tolist(),iou=i.tolist())
    print(f'{split}: n={len(e)}  ES mean={e.mean():.4f}±{e.std():.4f}  MAE={m.mean():.4f}  1-IoU={i.mean():.4f}',flush=True)
json.dump(out,open(f'{SP}/m4_scores.json','w'))

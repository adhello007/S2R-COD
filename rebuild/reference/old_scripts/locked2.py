import os,sys,json,numpy as np,cv2,torch,torch.nn.functional as F
from PIL import Image
import torchvision.transforms as T
R='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD'
sys.path.insert(0,R); sys.path.insert(0,f'{R}/Eval')
from Src.model.SINet.SINet import SINet_ResNet50
from Src.utils.tool import ESLoss
import metrics as Measure
SP=os.path.dirname(os.path.abspath(__file__)); NF=f'{SP}/noisefloor'
GT=f'{R}/Dataset/Test/GT'; IMG=f'{R}/Dataset/Test/Image'
names=json.load(open(f'{SP}/dinoL_names.json'))['tst']          # same order as DINOv2 features
dev='cuda:0'
PGT=ESLoss(a=0.9,b=0.3,c=0.5,use_weighted_bce=False).to(dev)
tf=T.Compose([T.Resize((352,352)),T.ToTensor(),T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
out={}
RUNS=[('s42',f'{NF}/snap_s42'),('s43',f'{NF}/snap_s43'),('s45',f'{NF}/snap_s45'),('s46',f'{NF}/snap_s46'),
      ('repro',f'{R}/Snapshot/SINet/S2C')]
for tag,snap in RUNS:
    stu=SINet_ResNet50().to(dev); tea=SINet_ResNet50().to(dev)
    stu.load_state_dict(torch.load(f'{snap}/Stu_40.pth',map_location='cpu'))
    tea.load_state_dict(torch.load(f'{snap}/Tea_epoch_best.pth',map_location='cpu'))
    stu.eval(); tea.eval()
    es=[]; sa=[]; mae=[]
    predroot = f'{NF}/pred_{tag}' if tag!='repro' else f'{R}/Result/SINet/S2C'
    have_pred=os.path.isdir(predroot) and len(os.listdir(predroot))>=2026
    with torch.no_grad():
        for n in names:
            stem=os.path.splitext(n)[0]
            x=tf(Image.open(f'{IMG}/{stem}.jpg').convert('RGB')).unsqueeze(0).to(dev)
            _,s=stu(x); _,t=tea(x)
            es.append(PGT(s.sigmoid(),t.sigmoid()).item())
            g=cv2.imread(f'{GT}/{stem}.png',cv2.IMREAD_GRAYSCALE)
            if have_pred:
                p=cv2.imread(f'{predroot}/{stem}.png',cv2.IMREAD_GRAYSCALE)
                if p is None: p=np.zeros_like(g)
                if p.shape!=g.shape: p=cv2.resize(p,(g.shape[1],g.shape[0]),cv2.INTER_NEAREST)
            else:
                cam=F.interpolate(t,size=g.shape,mode='bilinear',align_corners=True).sigmoid().cpu().numpy().squeeze()
                p=((cam-cam.min())/(cam.max()-cam.min()+1e-8)*255).astype(np.uint8)
            SM=Measure.Smeasure(); SM.step(pred=p,gt=g); sa.append(float(SM.sms[0]))
            gg=g.astype(np.float64)/max(g.max(),1); pp=p.astype(np.float64)/255.
            mae.append(float(np.abs(pp-gg).mean()))
    out[tag]=dict(es=es,sa=sa,mae=mae,pred_source=predroot if have_pred else 'recomputed')
    print(f'{tag}: n={len(es)} ES={np.mean(es):.4f} Sa={np.mean(sa):.4f} MAE={np.mean(mae):.4f} src={out[tag]["pred_source"]}',flush=True)
    json.dump(out,open(f'{SP}/locked2_scores.json','w'))
print('DONE')

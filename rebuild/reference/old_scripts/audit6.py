import os,sys,json,numpy as np,cv2,torch
sys.path.insert(0,'/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Eval')
import metrics as Measure
SP='/tmp/claude-1000/-home-ai-server-Public-lab-Diffusion-Inpaint-S2R-COD/56f76fa7-1340-4f64-8958-29c72d526e77/scratchpad/noisefloor'
GT='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Dataset/Test/GT'
names=sorted(os.listdir(GT)); res={}
for r in ['s42','s43','s45','s46','repB','repC']:
    pd=f'{SP}/pred_{r}'
    FM,WFM,SM,EM,MAE=Measure.Fmeasure(),Measure.WeightedFmeasure(),Measure.Smeasure(),Measure.Emeasure(),Measure.MAE()
    with torch.no_grad():
        for n in names:
            p=cv2.imread(f'{pd}/{n}',cv2.IMREAD_GRAYSCALE); g=cv2.imread(f'{GT}/{n}',cv2.IMREAD_GRAYSCALE)
            if p.shape!=g.shape: p=cv2.resize(p,(g.shape[1],g.shape[0]),cv2.INTER_NEAREST)
            for M in (FM,WFM,SM,EM,MAE): M.step(pred=p,gt=g)
    res[r]=dict(Sa=float(SM.get_results()['sm']),Fbw=float(WFM.get_results()['wfm']),MAE=float(MAE.get_results()['mae']))
    print(r,res[r],flush=True); json.dump(res,open(f'{SP}/audit6.json','w'))
print('DONE')

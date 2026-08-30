import os, sys, json, numpy as np, cv2, torch
sys.path.insert(0,'/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Eval')
import metrics as Measure
SP='/tmp/claude-1000/-home-ai-server-Public-lab-Diffusion-Inpaint-S2R-COD/56f76fa7-1340-4f64-8958-29c72d526e77/scratchpad/noisefloor'
GT='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Dataset/Test/GT'
res={}
for s in (42,43,45,46):
    pd=f'{SP}/pred_s{s}'
    FM,WFM,SM,EM,MAE=Measure.Fmeasure(),Measure.WeightedFmeasure(),Measure.Smeasure(),Measure.Emeasure(),Measure.MAE()
    with torch.no_grad():
        for n in os.listdir(GT):
            p=cv2.imread(f'{pd}/{n}',cv2.IMREAD_GRAYSCALE); g=cv2.imread(f'{GT}/{n}',cv2.IMREAD_GRAYSCALE)
            if p is None: raise SystemExit(f'missing pred {pd}/{n}')
            if p.shape!=g.shape: p=cv2.resize(p,(g.shape[1],g.shape[0]),cv2.INTER_NEAREST)
            for M in (FM,WFM,SM,EM,MAE): M.step(pred=p,gt=g)
    res[s]=dict(Sa=float(SM.get_results()['sm']), Fbw=float(WFM.get_results()['wfm']),
                MAE=float(MAE.get_results()['mae']),
                meanEm=float(EM.get_results()['em']['curve'].mean()),
                meanFm=float(FM.get_results()['fm']['curve'].mean()))
    print(f"seed {s}: " + "  ".join(f"{k}={v:.4f}" for k,v in res[s].items()), flush=True)
json.dump(res,open(f'{SP}/metrics.json','w'))
print()
print(f"{'metric':8} {'mean':>9} {'sd':>9} {'min':>9} {'max':>9} {'range':>9}")
for k in ('Sa','Fbw','MAE','meanEm','meanFm'):
    v=np.array([res[s][k] for s in res])
    print(f"{k:8} {v.mean():9.5f} {v.std(ddof=1):9.5f} {v.min():9.5f} {v.max():9.5f} {v.max()-v.min():9.5f}")

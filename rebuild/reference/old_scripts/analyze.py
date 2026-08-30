import numpy as np, sys, json
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
SP='/tmp/claude-1000/-home-ai-server-Public-lab-Diffusion-Inpaint-S2R-COD/56f76fa7-1340-4f64-8958-29c72d526e77/scratchpad'
TAG=sys.argv[1]; POOL=sys.argv[2] if len(sys.argv)>2 else 'cls'
l2=lambda X: X/np.linalg.norm(X,axis=1,keepdims=True)
L=lambda k: l2(np.load(f'{SP}/{TAG}_{k}_{POOL}.npy').astype(np.float64))
Ft,Fg,Fc,Fx=L('tgt'),L('gen'),L('cut'),L('tst')
print(f"=== {TAG} / {POOL} pooling ===  target {Ft.shape}  gen {Fg.shape}  cut {Fc.shape}\n")

# ---------- 2b. linear probe: real-COD target vs LAKE-RED output ----------
X=np.vstack([Ft,Fg]); y=np.r_[np.zeros(len(Ft)),np.ones(len(Fg))]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.3,random_state=0,stratify=y)
clf=LogisticRegression(max_iter=3000,C=1.0).fit(Xtr,ytr)
acc=clf.score(Xte,yte); auc=roc_auc_score(yte,clf.decision_function(Xte))
print(f"[2b] linear probe real-COD vs LAKE-RED: acc={acc:.4f}  AUC={auc:.4f}  (chance acc={max((y==0).mean(),(y==1).mean()):.4f})")
# how much of the gap is one direction?
w=clf.coef_[0]/np.linalg.norm(clf.coef_[0])
print(f"     probe-axis projection: target {float((Ft@w).mean()):+.3f}±{float((Ft@w).std()):.3f}   LAKE-RED {float((Fg@w).mean()):+.3f}±{float((Fg@w).std()):.3f}")
print(f"     Cohen's d on that axis = {abs(float((Fg@w).mean()-(Ft@w).mean()))/np.sqrt(0.5*((Fg@w).var()+(Ft@w).var())):.2f}\n")

N=40
for k in (20,50,100):
    km=KMeans(k,n_init=10,random_state=0).fit(Ft); C=l2(km.cluster_centers_)
    at=km.labels_; land=(Fg@C.T).argmax(1)
    ct=np.bincount(at,minlength=k); cs=np.bincount(land,minlength=k)
    pt,ps=ct/ct.sum(),cs/cs.sum(); tv=0.5*np.abs(pt-ps).sum()
    dt=np.linalg.norm(Ft-km.cluster_centers_[at],axis=1); ds=np.linalg.norm(Fg-km.cluster_centers_[land],axis=1)
    kept=np.array([int((land[np.argsort(-(Fc@C[c]))[:N]]==c).sum()) for c in range(k)])
    defic=np.argsort(np.log((cs+1)/(ct+1)))
    print(f"--- k={k} ---")
    print(f"[2] TV(target,synth occupancy) = {tv:.3f} | empty-for-synth {int((cs==0).sum())}/{k} | "
          f"largest synth cluster {cs.max()} ({cs.max()/cs.sum():.1%}) | median n_s={int(np.median(cs))} vs n_t={int(np.median(ct))}")
    print(f"    edge-dweller: dist-to-own-centroid target {dt.mean():.3f} vs synth {ds.mean():.3f} (ratio {ds.mean()/dt.mean():.3f})")
    print(f"[1] acceptance: all-cluster mean {kept.mean():.2f}/{N} = {kept.mean()/N:.2%} | clusters with 0 kept: {int((kept==0).sum())}/{k}")
    top=defic[:12]
    print(f"    12 MOST-DEFICIENT clusters (where the budget goes):")
    print(f"      {'cluster':>8} {'n_t':>5} {'n_s':>6} {'kept/40':>8} {'accept':>7}")
    for c in top:
        print(f"      {'c'+str(c):>8} {ct[c]:5} {cs[c]:6} {kept[c]:8} {kept[c]/N:6.1%}")
    print(f"    -> deficient-12 mean acceptance = {kept[top].mean()/N:.2%}   "
          f"(saturated-4 = {kept[defic[-4:]].mean()/N:.1%})")
    a=kept[top].mean()/N
    print(f"    -> gens for B=1000 in deficient clusters: "
          f"{'INFEASIBLE (0%)' if a==0 else f'{int(1000/a):,} = {1000/a*1.73/3600:.1f} GPU-h/cycle/arm'}\n")

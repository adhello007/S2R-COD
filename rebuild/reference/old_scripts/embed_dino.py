import timm, torch, os, numpy as np, sys, json
from PIL import Image
D='/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/Dataset'
RAW=f'{D}/Source/HKU-IS_raw'; OUT=f'{D}/LAKERED/output/HKU-IS'
SP=os.path.dirname(os.path.abspath(__file__))
MODEL=sys.argv[1]; RES=int(sys.argv[2]); TAG=sys.argv[3]; dev='cuda:1'
m=timm.create_model(MODEL,pretrained=True,num_classes=0,img_size=RES).to(dev).eval().half()
MEAN=torch.tensor([0.485,0.456,0.406],device=dev).view(1,3,1,1).half()
STD =torch.tensor([0.229,0.224,0.225],device=dev).view(1,3,1,1).half()

# --- 7 test-identical target images (A8): 2 same-name + 5 cross-named ---
LEAK={'COD10K-CAM-2-Terrestrial-23-Cat-1506.jpg','COD10K-CAM-1-Aquatic-3-Crab-32.jpg',
      'COD10K-CAM-3-Flying-53-Bird-3205.jpg','COD10K-CAM-2-Terrestrial-28-Deer-1796.jpg',
      'COD10K-CAM-2-Terrestrial-26-Chameleon-1694.jpg','COD10K-CAM-2-Terrestrial-32-Giraffe-1930.jpg',
      'COD10K-CAM-2-Terrestrial-31-Gecko-1928.jpg'}

def load_plain(p):
    return Image.open(p).convert('RGB').resize((RES,RES),Image.BICUBIC)
def load_cutout(stem):
    im=Image.open(f'{RAW}/imgs/{stem}.png').convert('RGB')
    gt=Image.open(f'{RAW}/gt/{stem}.png').convert('L').resize(im.size,Image.NEAREST)
    a=np.asarray(im).copy(); a[np.asarray(gt)<127]=128       # object on neutral grey
    return Image.fromarray(a).resize((RES,RES),Image.BICUBIC)

@torch.no_grad()
def embed(items,loader,bs=48):
    cls,pat=[],[]
    for i in range(0,len(items),bs):
        b=torch.stack([torch.from_numpy(np.asarray(loader(it)).copy()) for it in items[i:i+bs]])
        x=b.permute(0,3,1,2).to(dev).half().div_(255.); x=(x-MEAN)/STD
        f=m.forward_features(x)                              # B, 1+N, C
        cls.append(f[:,0].float().cpu()); pat.append(f[:,1:].mean(1).float().cpu())
    return torch.cat(cls).numpy(), torch.cat(pat).numpy()

tgt_names=[f for f in sorted(os.listdir(f'{D}/Target/Image'))]
tgt_keep=[f for f in tgt_names if f not in LEAK]
gen_stems=[os.path.splitext(f)[0][4:] for f in sorted(os.listdir(f'{OUT}/images'))]   # strip SOD_
cut_stems=[s for s in gen_stems if os.path.exists(f'{RAW}/imgs/{s}.png')]
tst=[f for f in sorted(os.listdir(f'{D}/Test/Image'))]
val=[f for f in sorted(os.listdir(f'{D}/Val/CAMO/Imgs'))]
print(f'target kept {len(tgt_keep)} (dropped {len(tgt_names)-len(tgt_keep)} leaked)  gen {len(gen_stems)}  cut {len(cut_stems)}  test {len(tst)}  val {len(val)}',flush=True)

jobs={
 'tgt':(tgt_keep, lambda f: load_plain(f'{D}/Target/Image/{f}')),
 'gen':(gen_stems, lambda s: load_plain(f'{OUT}/images/SOD_{s}.jpg')),
 'cut':(cut_stems, load_cutout),
 'tst':(tst, lambda f: load_plain(f'{D}/Test/Image/{f}')),
 'val':(val, lambda f: load_plain(f'{D}/Val/CAMO/Imgs/{f}')),
}
meta={}
for k,(items,ld) in jobs.items():
    c,p=embed(items,ld); np.save(f'{SP}/{TAG}_{k}_cls.npy',c); np.save(f'{SP}/{TAG}_{k}_pat.npy',p)
    meta[k]=items; print(f'  {k}: {c.shape}',flush=True)
json.dump(meta,open(f'{SP}/{TAG}_names.json','w'))
print('done',TAG)

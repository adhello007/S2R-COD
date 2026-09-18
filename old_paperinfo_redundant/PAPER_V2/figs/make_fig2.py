#!/usr/bin/env python3
"""Figure 2 -- six confirmed contamination pairs, from the committed pair list.

Selection rule, declared in the caption and applied here: the six LOWEST
mean|diff| among pairs whose partner lies in cod10k_train. Nothing is cherry
picked by eye; the ordering is the committed metric.

Sources: rebuild/D2_reaudit/out/chameleon_contaminated.json (EXP D2R #4),
         Dataset/chameleon_new/  (author-sourced CHAMELEON release)
         Dataset/Target/Image/   (the training pool)
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(REPO, 'rebuild', 'PAPER_V2', 'figs', 'fig2_pairs.pdf')
CHAM = os.path.join(REPO, 'Dataset', 'chameleon_new', 'animals')
TRAIN = os.path.join(REPO, 'Dataset', 'Target', 'Image')
N = 6

pairs = json.load(open(os.path.join(
    REPO, 'rebuild/D2_reaudit/out/chameleon_contaminated.json')))['contaminated']
pairs = sorted([p for p in pairs if p['partner_pool'] == 'cod10k_train'],
               key=lambda r: r['mean_abs'])[:N]

fig, axes = plt.subplots(2, N, figsize=(11.0, 2.0))
for j, p in enumerate(pairs):
    a = Image.open(os.path.join(CHAM, p['chameleon_image'])).convert('RGB')
    b = Image.open(os.path.join(TRAIN, p['partner'])).convert('RGB')
    for i, (im, tag) in enumerate(((a, 'CHAMELEON'), (b, 'COD10K-train'))):
        ax = axes[i][j]
        ax.imshow(im)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor('#c0392b' if i == 0 else '#1f4e79')
            s.set_linewidth(1.3)
        if j == 0:
            ax.set_ylabel(tag, fontsize=8.0)
    ev = 'qtable' if p['qtables_differ'] else 'container'
    axes[1][j].set_xlabel(r'mean$|\Delta|$ = %.3f' % p['mean_abs'] + '\n%s  ·  %s'
                          % (p['dims'], ev), fontsize=6.9, labelpad=3)
    axes[0][j].set_title(p['chameleon_image'].replace('.jpg', ''), fontsize=7.0, pad=3)

plt.tight_layout(w_pad=0.55, h_pad=0.35)
plt.savefig(OUT, bbox_inches='tight', dpi=210)
print('wrote', OUT)
for p in pairs:
    print('  %-16s <- %-46s mean|d| %.3f  max %d  %s'
          % (p['chameleon_image'], p['partner'], p['mean_abs'], p['max_abs'],
             p['qtable_evidence']))

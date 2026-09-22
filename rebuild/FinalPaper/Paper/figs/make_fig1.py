#!/usr/bin/env python3
"""Figure 1 -- the paper's thesis, in two panels, from committed artifacts only.

left : held-out Cohen's d per selection rule (EXP C1 #4, c1_attribution.csv)
right: trained S_alpha per C-family arm with the frozen 2*sigma_hat bar
       (EXP T2 #3, out/t2/abc_metrics.csv + abc_sigma.json)
"""
import csv, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(REPO, 'rebuild', 'PAPER_V4', 'figs', 'fig1_thesis.pdf')
PEAK_B = 250          # the peak cell Table 9.1 reports

ARMS = [('TARGETED_by_target_es', 'targeted\n(real signal)', '#1f4e79'),
        ('shuffled_es',           'shuffled\n(signal destroyed)', '#4a7fb5'),
        ('random_centroid',       'arbitrary\ncluster', '#7aa8d2'),
        ('random_direction',      'random\ndirection', '#a9c7e4'),
        ('random_vs_random',      'two random draws\n(no concentration)', '#c0392b')]

rows = list(csv.DictReader(open(os.path.join(REPO, 'rebuild/C1/out/c1_attribution.csv'))))
cells = {}
for r in rows:
    if int(r['B']) != PEAK_B:
        continue
    cells.setdefault(r['arm'], []).append(float(r['d_heldout']))

met = list(csv.DictReader(open(os.path.join(REPO, 'rebuild/ABC/out/t2/abc_metrics.csv'))))
sig = json.load(open(os.path.join(REPO, 'rebuild/ABC/out/t2/abc_sigma.json')))

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.0, 1.95))

# ---------------- left panel ----------------
xs = np.arange(len(ARMS))
mean = [float(np.mean(cells[a])) for a, _, _ in ARMS]
lo = [m - min(cells[a]) for m, (a, _, _) in zip(mean, ARMS)]
hi = [max(cells[a]) - m for m, (a, _, _) in zip(mean, ARMS)]
axL.bar(xs, mean, yerr=[lo, hi], capsize=3.5,
        color=[c for _, _, c in ARMS], edgecolor='black', linewidth=0.6, width=0.68)
axL.axhline(0, color='black', lw=0.8)
axL.set_xticks(xs)
axL.set_xticklabels([l for _, l, _ in ARMS], fontsize=7.2)
axL.set_ylabel(r"held-out Cohen's $d$", fontsize=9)
axL.set_title('(a) Every rule that keeps concentration\nreproduces the separation',
              fontsize=9.5, pad=6)
axL.tick_params(axis='y', labelsize=8)
for x, m, h in zip(xs, mean, hi):
    axL.text(x, m + h + 0.075, '%+.2f' % m, ha='center', fontsize=7.4)
axL.set_ylim(-0.28, 1.72)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)

# ---------------- right panel ----------------
ARCH = [('SINet', 'SINet'), ('SINetv2', 'SINet-v2')]
CARMS = ['C10', 'CSHUF', 'CINV']
LBL = {'C10': 'C10\n(real)', 'CSHUF': 'CSHUF\n(destroyed)', 'CINV': 'CINV\n(reversed)'}
COL = {'C10': '#1f4e79', 'CSHUF': '#4a7fb5', 'CINV': '#7aa8d2'}
pos, tick, lab = 0, [], []
for ai, (akey, aname) in enumerate(ARCH):
    s2 = sig['%s|COD10K' % akey]['sigma_hat']
    base = np.mean([float(r['Sm']) for r in met
                    if r['arch'] == akey and r['arm'] == 'C10' and r['endpoint'] == 'COD10K'])
    axR.add_patch(plt.Rectangle((pos - 0.5, base - 2 * s2), 3.0, 4 * s2,
                                color='#dfe6ee', zorder=0,
                                label=r'C10 $\pm\,2\hat{\sigma}$ (the frozen bar)' if ai == 0 else None))
    for arm in CARMS:
        v = [float(r['Sm']) for r in met
             if r['arch'] == akey and r['arm'] == arm and r['endpoint'] == 'COD10K']
        axR.plot([pos] * len(v), v, 'o', ms=4.0, color=COL[arm],
                 markeredgecolor='black', markeredgewidth=0.4, zorder=3)
        axR.plot([pos - 0.26, pos + 0.26], [np.mean(v)] * 2, '-',
                 color='black', lw=1.6, zorder=4)
        tick.append(pos); lab.append(LBL[arm])
        pos += 1
    axR.text(pos - 2, 0.7268, aname, ha='center', fontsize=9)
    pos += 1
axR.set_xlim(-0.7, pos - 1.3)
axR.set_xticks(tick); axR.set_xticklabels(lab, fontsize=7.2)
axR.set_ylim(0.6855, 0.7285)
axR.set_ylabel(r'COD10K-test $S_\alpha$', fontsize=9)
axR.set_title('(b) Real, destroyed and reversed targeting\nare indistinguishable',
              fontsize=9.5, pad=6)
axR.tick_params(axis='y', labelsize=8)
axR.legend(fontsize=7.0, loc='center left', framealpha=0.95, ncol=1)
for s_ in ('top', 'right'):
    axR.spines[s_].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, bbox_inches='tight')
print('wrote', OUT)
for a, l, _ in ARMS:
    print('  %-26s mean %+0.4f  over %d cells' % (a, np.mean(cells[a]), len(cells[a])))

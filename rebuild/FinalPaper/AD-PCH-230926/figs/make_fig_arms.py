#!/usr/bin/env python3
"""Figure 1 -- what each training arm holds fixed and what it varies.

The paper turns on separating two things that the obvious comparison changes at
once: how CONCENTRATED an allocation is, and WHERE it points.  This figure is
the map of that separation.

Axis positions are not schematic.  The vertical axis is each arm's rank
correlation with the committed uncertainty ranking, from committed artifacts:

  C10      +1.0      it IS the committed ranking, by construction
  CORACLE  +0.2372   rho(ES, 1-S_alpha) per cluster
                     -- rebuild/FinalPaper/results.md  5.2
  CSHUF    -0.03351  realised correlation of the selected permutation
                     -- rebuild/ABC/T2_RESULTS.md:155
  CINV     -1.0      exact rank reversal, by construction

Pool sizes from rebuild/ABC/out/abc_pools.json (A0 4447; A2/B/C10 5447, +1000).
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from _repo import fig_out
OUT = fig_out('fig_arms.pdf')

DISPERSED, CONCENTRATED = 0.0, 1.0

# (x, y, label, sublabel, colour).  CORACLE and CSHUF sit only 0.27 apart on a
# real axis, so labels are single-line -- stacked ones collide.
ARMS = [
    (DISPERSED,     0.00, 'B',       'random selection',      '#c0392b'),
    (CONCENTRATED, +1.00, 'C10',     'targeted, the method',  '#1f4e79'),
    (CONCENTRATED, +0.24, 'CORACLE', 'aimed by true error',   '#4a7fb5'),
    (CONCENTRATED, -0.03, 'CSHUF',   'signal destroyed',      '#7aa8d2'),
    (CONCENTRATED, -1.00, 'CINV',    'signal reversed',       '#a9c7e4'),
]

fig, ax = plt.subplots(figsize=(7.0, 2.75))

# The C-family shares one allocation shape to five decimal places -- the band
# is the visual statement of that, and it is what makes the vertical contrast
# a clean one.
ax.add_patch(Rectangle((CONCENTRATED - 0.20, -1.35), 0.40, 2.70,
                       facecolor='#e8eef6', edgecolor='#9db8d4',
                       linewidth=0.7, linestyle=(0, (4, 2)), zorder=0))
ax.text(CONCENTRATED, 1.46, 'identical allocation shape\n(five decimal places)',
        ha='center', va='bottom', fontsize=6.6, color='#2c5c8f', style='italic')

for x, y, name, sub, col in ARMS:
    ax.scatter([x], [y], s=118, color=col, edgecolor='black',
               linewidth=0.7, zorder=4)
    ax.text(x + 0.085, y, r'$\bf{%s}$   %s' % (name, sub), ha='left',
            va='center', fontsize=7.6, color='#222222', zorder=5)

# The decisive gap changes BOTH coordinates -- which is exactly why it cannot
# attribute an effect to either one.
ax.add_patch(FancyArrowPatch((DISPERSED + 0.03, 0.05),
                             (CONCENTRATED - 0.26, +0.93),
                             arrowstyle='<->', mutation_scale=9,
                             linewidth=1.25, color='#c0392b', zorder=3))
ax.text(0.375, 0.80, 'the decisive gap\nchanges both axes at once',
        ha='center', va='center', fontsize=6.9, color='#c0392b',
        fontweight='bold', linespacing=1.35, zorder=6,
        bbox=dict(boxstyle='round,pad=0.22', facecolor='white',
                  edgecolor='none', alpha=0.94))

# The falsification contrast changes only the vertical coordinate.
ax.annotate('', xy=(CONCENTRATED - 0.215, 1.00),
            xytext=(CONCENTRATED - 0.215, -1.00),
            arrowprops=dict(arrowstyle='<->', linewidth=1.25, color='#1f4e79'))
ax.text(CONCENTRATED - 0.265, -0.42, 'only the\ndirection\nchanges',
        ha='right', va='center', fontsize=6.9, color='#1f4e79',
        fontweight='bold', linespacing=1.35, zorder=6,
        bbox=dict(boxstyle='round,pad=0.22', facecolor='white',
                  edgecolor='none', alpha=0.94))

# A0 adds nothing at all, so it has no allocation to place on either axis.
ax.text(-0.235, -1.34,
        'A0  base pool only, 4447 pairs, no allocation\n'
        'A2  +1000 real photographs, drawn as B draws',
        ha='left', va='bottom', fontsize=6.4, color='#555555',
        linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.36', facecolor='#f7f7f7',
                  edgecolor='#cccccc', linewidth=0.6))

ax.axhline(0, color='#bbbbbb', lw=0.7, zorder=1)
ax.set_xlim(-0.30, 1.72)
ax.set_ylim(-1.62, 1.62)
ax.set_xticks([DISPERSED, CONCENTRATED])
ax.set_xticklabels(['dispersed\n(budget spread evenly)',
                    'concentrated\n(budget piled on a few clusters)'], fontsize=7.4)
ax.set_yticks([-1, 0, 1])
ax.set_yticklabels(['reversed', 'none', 'as scored'], fontsize=7.4)
ax.set_ylabel('where the budget points\n(rank correlation with the uncertainty ranking)',
              fontsize=7.4, linespacing=1.5)
ax.set_xlabel('how concentrated the allocation is', fontsize=7.4)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
ax.tick_params(length=2.5, width=0.7)

fig.tight_layout()
fig.savefig(OUT, bbox_inches='tight')
print('wrote', OUT)

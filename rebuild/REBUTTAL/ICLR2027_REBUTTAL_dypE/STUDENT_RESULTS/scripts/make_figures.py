#!/usr/bin/env python
"""Figures from committed RESULT_TABLES only (no new computation): AN-02 and AN-05."""
import argparse
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--sr', required=True)
ap.add_argument('--which', default='an02,an05')
a = ap.parse_args()
RT, FG = os.path.join(a.sr, 'RESULT_TABLES'), os.path.join(a.sr, 'FIGURES')
C = {'B-C10': '#2a6fbb', 'B-CSHUF': '#5aa0d8', 'B-CINV': '#9cc7ec', 'C10-CSHUF': '#d1762b',
     'C10-CINV': '#e59a5c', 'CSHUF-CINV': '#f0bf91'}


def rows(n):
    return list(csv.DictReader(open(os.path.join(RT, n))))


def an02():
    ov = rows('AN-02_overlap_by_seed.csv')
    ex = rows('AN-02_exposure_by_run.csv')
    pf = rows('EXP-01_preflight.csv')
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
    pairs = ['B-C10', 'B-CSHUF', 'B-CINV', 'C10-CSHUF', 'C10-CINV', 'CSHUF-CINV']
    for i, p in enumerate(pairs):
        x, y = p.split('-')
        v = [float(r['frac_injection_differs']) for r in ov if r['arm_x'] == x and r['arm_y'] == y]
        ax[0].scatter([i] * len(v), v, color=C[p], s=18, zorder=3)
    ax[0].axhline(0.48, color='0.3', ls='--', lw=1)
    ax[0].text(5.4, 0.49, 'manuscript "about 48%"', ha='right', fontsize=7, color='0.3')
    ax[0].set_xticks(range(len(pairs)))
    ax[0].set_xticklabels(pairs, rotation=30, fontsize=8)
    ax[0].set_ylim(0, 1)
    ax[0].set_ylabel('share of the 1,000 injected images\nthat differ (one dot per seed)', fontsize=8)
    ax[0].set_title('Injected-set difference by arm pair', fontsize=9)
    for arch, mk in (('SINet', 'o'), ('SINetv2', 's')):
        for rnd in ('1', '2'):
            v = [float(r['arm_specific_share_of_draws_vs_B']) for r in ex
                 if r['architecture'] == arch and r['round'] == rnd and r['arm'] == 'C10']
            ax[1].scatter([int(rnd) + (0.1 if arch == 'SINetv2' else -0.1)] * len(v), v, marker=mk,
                          color='#2a6fbb' if arch == 'SINet' else '#d1762b', s=18,
                          label='%s' % arch if rnd == '1' else None)
    ax[1].set_xticks([1, 2])
    ax[1].set_xticklabels(['round 1', 'round 2'])
    ax[1].set_ylim(0, 0.2)
    ax[1].set_ylabel('expected share of source draws on\nC10-only images (vs B), per epoch', fontsize=8)
    ax[1].set_title('Theoretical exposure (no sampler trace logged)', fontsize=9)
    ax[1].legend(fontsize=7, frameon=False)
    ns = [int(r['N']) for r in pf]
    ax[2].plot(ns, [float(r['DC_mean']) for r in pf], 'o-', color='#2a6fbb')
    ax[2].fill_between(ns, [float(r['DC_min']) for r in pf], [float(r['DC_max']) for r in pf], color='#2a6fbb', alpha=0.2)
    ax[2].axhline(1.5 * float(pf[0]['DC_mean']), color='0.3', ls='--', lw=1)
    ax[2].text(4400, 1.5 * float(pf[0]['DC_mean']) + 0.004, 'pre-specified pass line (1.5x N=1000)', ha='right', fontsize=7)
    ax[2].set_xlabel('matched budget N', fontsize=8)
    ax[2].set_ylabel('share of training pool differing,\nB_N vs C10_N (8 seeds)', fontsize=8)
    ax[2].set_title('EXP-01 preflight: larger N does not enlarge the contrast', fontsize=9)
    fig.suptitle('Post-review exploratory (AN-02, EXP-01 preflight)', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FG, 'AN-02_overlap_exposure.png'), dpi=150)


def an05():
    pr = rows('AN-05_chameleon_pairs.csv')
    pp = rows('AN-05_protocol_paths.csv')
    cols = ['common_supervised_protocol_train_labels', 'this_paper_unlabelled_target_image',
            'this_paper_checkpoint_selection', 'cross_benchmark_cod10k_test', 'this_paper_supervised_source_labels']
    labels = ['common protocol:\nsupervised training\n(image + mask)', 'this paper:\nunlabelled target\n(image only)',
              'this paper:\ncheckpoint selection\n(CAMO-250)', 'also a COD10K-test\nphotograph\n(cross-benchmark)',
              'this paper:\nsupervised source\n(HKU-IS + renders)']
    cat = defaultdict(lambda: defaultdict(int))
    for r in pp:
        for c in cols:
            cat[c][r[c].split(' ')[0]] += 1
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    colors = {'direct': '#c0392b', 'unknown': '#9a9a9a', 'not-detected': '#2e8b57', 'absent': '#2e8b57'}
    for i, c in enumerate(cols):
        left = 0
        for k in ('direct', 'unknown', 'not-detected'):
            n = cat[c].get(k, 0)
            if n:
                ax.barh(i, n, left=left, color=colors[k], label=k)
                ax.text(left + n / 2, i, str(n), ha='center', va='center', fontsize=8, color='white')
                left += n
    ax.set_yticks(range(len(cols)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlim(0, 76)
    ax.set_xlabel('CHAMELEON images (76)', fontsize=8)
    h, l = ax.get_legend_handles_labels()
    seen = {}
    for hh, ll in zip(h, l):
        seen.setdefault(ll, hh)
    ax.legend(seen.values(), seen.keys(), fontsize=7, frameon=True, facecolor='white', framealpha=1.0, loc='upper left', bbox_to_anchor=(1.01, 1.0))
    n_conf = sum(r['status'] == 'confirmed' for r in pr)
    ax.set_title('Where the 76 CHAMELEON photographs also appear, by pathway (%d confirmed training-pool duplicates;\n'
                 '"unknown" = no partner found, not shown absent; "not-detected" = searched, none found -- a lower bound)'
                 % n_conf, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FG, 'AN-05_protocol_paths.png'), dpi=150)


if __name__ == '__main__':
    w = a.which.split(',')
    if 'an02' in w:
        an02()
    if 'an05' in w:
        an05()

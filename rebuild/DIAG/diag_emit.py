#!/usr/bin/env python
"""DIAG.6 -- consolidate the diagnostics and emit the paper's tables and figures.

Reads only what DIAG.1-DIAG.5 wrote. Computes nothing new except formatting.

Emits:
  rebuild/DIAG/out/diagnostics_summary.json
  Paper/table_tost_equivalence.tex
  Paper/table_cluster_composition.tex
  Paper/table_subgroup_metrics.tex
  Paper/figs/fig_cluster_diagnostics.pdf
  Paper/figs/fig_chameleon_pairs.pdf

Usage:
  .venv/bin/python rebuild/DIAG/diag_emit.py
"""

import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib import image as mpimg                          # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT = os.path.join(_HERE, 'out')
PAPER = os.path.join(REPO, 'Paper')
FIGS = os.path.join(PAPER, 'figs')

NAVY, MID, LIGHT, PALE, RED = '#1f4e79', '#4a7fb5', '#7aa8d2', '#a9c7e4', '#c0392b'


def _p(m):
    print(m, flush=True)


def load(name):
    return json.load(open(os.path.join(OUT, name)))


# ============================================================ tables
def table_tost(tost):
    """Equivalence and interval estimates for the gaps that carry the paper."""
    rows = [('SINet', 'ABC|SINet|COD10K|C10-B', r'$\mathrm{C10}-\mathrm{B}$'),
            ('SINet-v2', 'ABC|SINetv2|COD10K|C10-B', r'$\mathrm{C10}-\mathrm{B}$'),
            ('SINet', 'T2|SINet|COD10K|C10-CSHUF', r'$\mathrm{C10}-\mathrm{CSHUF}$'),
            ('SINet', 'T2|SINet|COD10K|C10-CINV', r'$\mathrm{C10}-\mathrm{CINV}$'),
            ('SINet-v2', 'T2|SINetv2|COD10K|C10-CSHUF', r'$\mathrm{C10}-\mathrm{CSHUF}$'),
            ('SINet-v2', 'T2|SINetv2|COD10K|C10-CINV', r'$\mathrm{C10}-\mathrm{CINV}$')]
    L = [r'\begin{table}[t]',
         r'\caption{Post-hoc interval estimates for the gaps this paper turns on, on COD10K-test '
         r'$S_\alpha$. \emph{These decide nothing}: the verdicts remain the pre-registered '
         r'$2\hat{\sigma}$ rule of Section~\ref{sec:setup}, which reports no $p$-value at $n=3$. '
         r'Intervals are Welch (unequal-variance) on the two arms actually compared, so they are '
         r'not inflated by A0. TOST is run at the SESOI $\delta = 0.005$; the final column '
         r'gives the smallest $\delta$ at which each comparison \emph{could} have concluded '
         r'equivalence, which is the honest positive statement the data supports. '
         r'\emph{Source:} \texttt{rebuild/DIAG/out/diag\_tost.json}.}',
         r'\label{tab:tost}', r'\begin{center}', r'\footnotesize',
         r'\setlength{\tabcolsep}{4pt}',
         r'\begin{tabular}{@{}llcccc@{}}', r'\toprule',
         r'Arch. & Gap & $\Delta$ & 90\% CI & 95\% CI & smallest $\delta$ \\',
         r'\midrule']
    for arch, key, lbl in rows:
        if key not in tost['gaps']:
            continue
        w = tost['gaps'][key]['welch']
        L.append(r'%s & %s & $%+.4f$ & $[%+.4f, %+.4f]$ & $[%+.4f, %+.4f]$ & $%.4f$ \\'
                 % (arch, lbl, w['diff'], w['ci90'][0], w['ci90'][1],
                    w['ci95'][0], w['ci95'][1], w['achieved_equivalence_bound']))
    L += [r'\bottomrule', r'\end{tabular}', r'\end{center}',
          r'\footnotesize No comparison reaches equivalence at $\delta = 0.005$: at $n = 3$ per arm '
          r'a TOST has almost no power, and reporting that plainly is more useful than reporting '
          r'the $p$-values. What the intervals \emph{do} establish is stated in '
          r'Section~\ref{sec:null}.',
          r'\end{table}']
    return '\n'.join(L) + '\n'


def table_cluster(cl):
    """Composition of the funded clusters -- the mixture confound, quantified."""
    per = {r['cluster']: r for r in cl['per_cluster']}
    top = sorted(cl['per_cluster'], key=lambda r: -r['alloc'])[:10]
    m = cl['mixture']
    L = [r'\begin{table}[t]',
         r'\caption{The ten most-funded clusters, and what the budget is actually aimed at. '
         r'The target pool is $24.8\%$ CAMO, but $51.5\%$ of the generation budget lands on '
         r'CAMO images --- a $2.08\times$ enrichment ($2.14\times$ under the committed '
         r'assignment). The two largest quotas take $33.5\%$ of the budget, are $90.2\%$ CAMO, '
         r'and between them hold $7$ of the $2026$ primary-endpoint images. '
         r'\emph{Source:} \texttt{rebuild/DIAG/out/diag\_clusters.json}.}',
         r'\label{tab:clustercomp}', r'\begin{center}', r'\small',
         r'\begin{tabular}{rrrrrrr}', r'\toprule',
         r'Cluster & Budget & \% of $B$ & $n_{\text{target}}$ & CAMO \% & '
         r'$n_{\text{test}}$ & $\mathit{es}_j$ \\',
         r'\midrule']
    for r in top:
        L.append(r'%d & %d & %.1f & %d & %.1f & %d & %.4f \\'
                 % (r['cluster'], r['alloc'], 100 * r['alloc_share'], r['n_target'],
                    100 * r['camo_share'], r['n_test'], r['target_es']))
    L += [r'\midrule',
          r'\multicolumn{7}{l}{\emph{Budget-weighted totals against the pool they are drawn from}} \\',
          r'\multicolumn{4}{l}{CAMO share of the target pool} & \multicolumn{3}{r}{$%.3f$} \\'
          % m['pool_camo_share'],
          r'\multicolumn{4}{l}{CAMO share of the \emph{budget}} & \multicolumn{3}{r}{$\mathbf{%.3f}$} \\'
          % m['budget_weighted_camo_share'],
          r'\multicolumn{4}{l}{Endpoint images per unit budget, against uniform} '
          r'& \multicolumn{3}{r}{$%.3f$} \\' % m['endpoint_coverage_ratio'],
          r'\bottomrule', r'\end{tabular}', r'\end{center}', r'\end{table}']
    return '\n'.join(L) + '\n'


def table_subgroup(sg):
    """Boundary metrics: the concentration effect on trained accuracy."""
    L = [r'\begin{table}[t]',
         r'\caption{Arm differences on \emph{boundary} metrics, COD10K-test, same three seeds, '
         r'same pooled-$\hat{\sigma}$ rule. \textbf{Post-hoc: these metrics were not '
         r'pre-registered and no campaign verdict is re-decided.} On SINet the concentration '
         r'gap $\mathrm{C10}-\mathrm{B}$ clears its bar --- and so does '
         r'$\mathrm{CINV}-\mathrm{B}$, the \emph{anti}-targeted arm, by as much; the two '
         r'direction contrasts stay within noise. SINet-v2 resolves none of it, and that '
         r'disagreement is reported as a disagreement. '
         r'\emph{Source:} \texttt{rebuild/DIAG/out/diag\_subgroups.json}.}',
         r'\label{tab:boundary}', r'\begin{center}', r'\footnotesize',
         r'\setlength{\tabcolsep}{3.5pt}',
         r'\begin{tabular}{@{}llccccc@{}}', r'\toprule',
         r'Arch. & Metric & $2\hat{\sigma}$ & $\mathrm{C10}\!-\!\mathrm{B}$ & '
         r'$\mathrm{CINV}\!-\!\mathrm{B}$ & $\mathrm{C10}\!-\!\mathrm{CSHUF}$ & '
         r'$\mathrm{C10}\!-\!\mathrm{CINV}$ \\',
         r'\midrule']
    NICE = {'boundary_iou': 'Boundary IoU', 'boundary_f': 'Boundary $F$', 'iou': 'IoU'}
    for arch, disp in (('SINet', 'SINet'), ('SINetv2', 'SINet-v2')):
        for met in ('boundary_iou', 'boundary_f', 'iou'):
            k = '%s|%s' % (arch, met)
            if k not in sg['whole_set']:
                continue
            w = sg['whole_set'][k]
            def cell(name):
                g = w['gaps'].get(name)
                if g is None:
                    return '---'
                mark = r'\textbf{' if g['verdict'] in ('REAL EFFECT', 'REAL REGRESSION') else ''
                s = r'$%+.4f$ %s' % (g['delta'], g['sign_consistent'])
                return (mark + s + '}') if mark else s
            L.append(r'%s & %s & $%.4f$ & %s & %s & %s & %s \\'
                     % (disp, NICE[met], w['bar'], cell('C10-B'), cell('CINV-B'),
                        cell('C10-CSHUF'), cell('C10-CINV')))
        L.append(r'\midrule' if arch == 'SINet' else '')
    L = [x for x in L if x != '']
    L += [r'\bottomrule', r'\end{tabular}', r'\end{center}',
          r'\footnotesize Bold marks a gap exceeding $2\hat{\sigma}$ with $3/3$ sign consistency. '
          r'Counts after each $\Delta$ are sign-consistency across the three seeds. '
          r'\textbf{Threshold robustness (SINet, Boundary IoU):} at binarisation thresholds '
          r'$0.4/0.5/0.6$, $\Delta(\mathrm{C10}-\mathrm{B})$ is '
          r'$1.39/1.37/1.23\times$ bar and $\Delta(\mathrm{CINV}-\mathrm{B})$ is '
          r'$1.25/1.34/1.26\times$, both $3/3$ at every threshold, while '
          r'$\Delta(\mathrm{C10}-\mathrm{CSHUF})$ and $\Delta(\mathrm{C10}-\mathrm{CINV})$ never '
          r'exceed $0.52\times$ and $0.14\times$. The pattern is not an artifact of the threshold.',
          r'\end{table}']
    return '\n'.join(L) + '\n'


# ============================================================ figures
def fig_cluster(cl):
    per = cl['per_cluster']
    m = cl['mixture']
    alloc = np.array([r['alloc'] for r in per], float)
    camo = np.array([r['camo_share'] for r in per], float)
    ntest = np.array([r['n_test'] for r in per], float)
    ntgt = np.array([r['n_target'] for r in per], float)

    fig, ax = plt.subplots(1, 3, figsize=(11.0, 2.45))

    # (a) budget vs CAMO share
    a = ax[0]
    a.scatter(100 * camo, alloc, s=np.clip(ntgt * 0.45, 6, 90), c=NAVY,
              alpha=0.62, edgecolor='none')
    a.axvline(100 * m['pool_camo_share'], color=RED, lw=1.1, ls='--')
    a.text(100 * m['pool_camo_share'] + 2.5, alloc.max() * 0.87,
           'pool share\n%.1f%%' % (100 * m['pool_camo_share']),
           color=RED, fontsize=7.0, va='top')
    a.set_xlabel('CAMO share of cluster (%)', fontsize=8.5)
    a.set_ylabel('budget allocated', fontsize=8.5)
    a.set_title('(a) The budget concentrates on\nthe CAMO component', fontsize=9.3, pad=6)

    # (b) budget vs endpoint representation
    b = ax[1]
    b.scatter(ntest, alloc, s=26, c=MID, alpha=0.72, edgecolor='none')
    for r in sorted(per, key=lambda r: -r['alloc'])[:2]:
        b.annotate('cluster %d\n%d%% CAMO, $n_{test}=%d$'
                   % (r['cluster'], round(100 * r['camo_share']), r['n_test']),
                   (r['n_test'], r['alloc']), textcoords='offset points',
                   xytext=(14, -6), fontsize=6.8, color=RED)
    b.set_xlabel('endpoint images in cluster ($n_{\\mathrm{test}}$)', fontsize=8.5)
    b.set_ylabel('budget allocated', fontsize=8.5)
    b.set_title('(b) The largest quotas land where\nthe endpoint barely is', fontsize=9.3, pad=6)

    # (c) variance decomposition
    c = ax[2]
    u = cl['operational_utility']
    keys = [('one_minus_sa', r'$1-S_\alpha$'), ('mae', 'MAE'), ('one_minus_iou', r'$1-$IoU')]
    xs = np.arange(len(keys))
    btw = [100 * u[k]['between_frac'] for k, _ in keys]
    c.bar(xs, btw, color=NAVY, edgecolor='black', linewidth=0.6, width=0.6, label='between clusters')
    c.bar(xs, [100 - v for v in btw], bottom=btw, color=PALE, edgecolor='black',
          linewidth=0.6, width=0.6, label='within clusters')
    for x, v in zip(xs, btw):
        c.text(x, v + 2.4, '%.1f%%' % v, ha='center', fontsize=7.4, color=NAVY)
    c.set_xticks(xs)
    c.set_xticklabels([l for _, l in keys], fontsize=8)
    c.set_ylabel('% of endpoint error variance', fontsize=8.5)
    c.set_ylim(0, 108)
    c.set_title('(c) Four fifths of the error sits\n$\\it{inside}$ clusters', fontsize=9.3, pad=6)
    c.legend(fontsize=6.9, loc='upper right', frameon=False, ncol=1)

    for a_ in ax:
        a_.tick_params(labelsize=7.6)
        for s in ('top', 'right'):
            a_.spines[s].set_visible(False)
    fig.tight_layout()
    p = os.path.join(FIGS, 'fig_cluster_diagnostics.pdf')
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    _p('wrote %s' % p)


def fig_cham(ext):
    rows = [r for r in ext['rows'] if r.get('at_operating_point')]
    rows = sorted(rows, key=lambda r: -r['n_inlier'])[:6]
    cham_dir = os.path.join(REPO, 'Dataset/chameleon_new/animals')
    tr_dir = os.path.join(REPO, 'Dataset/Target/Image')
    fig, ax = plt.subplots(2, 6, figsize=(11.0, 3.55))
    for i, r in enumerate(rows):
        for j, (d, nm) in enumerate(((cham_dir, r['chameleon_image']),
                                     (tr_dir, r['best_partner']))):
            a = ax[j, i]
            try:
                a.imshow(mpimg.imread(os.path.join(d, nm)))
            except Exception:                                   # noqa: BLE001
                a.text(0.5, 0.5, 'unreadable', ha='center', fontsize=6)
            a.set_xticks([]); a.set_yticks([])
            for s in a.spines.values():
                s.set_linewidth(0.7)
                s.set_color(NAVY if j == 0 else MID)
        ax[0, i].set_title('%s\n%s' % (r['chameleon_image'], r['cham_dims']),
                           fontsize=6.6, pad=3)
        ax[1, i].set_xlabel('%s\n%s $\\cdot$ %d inliers'
                            % (r['best_partner'][:26], r['partner_dims'], r['n_inlier']),
                            fontsize=6.2, labelpad=3)
    ax[0, 0].set_ylabel('CHAMELEON', fontsize=8, color=NAVY)
    ax[1, 0].set_ylabel('training pool', fontsize=8, color=MID)
    fig.tight_layout()
    p = os.path.join(FIGS, 'fig_chameleon_pairs.pdf')
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    _p('wrote %s' % p)


def main():
    tost, cl, sg, ext = (load('diag_tost.json'), load('diag_clusters.json'),
                         load('diag_subgroups.json'), load('diag_chameleon_ext.json'))

    summary = dict(
        generated_by='rebuild/DIAG/diag_emit.py',
        status='POST-HOC diagnostics. No pre-registered verdict is re-decided by any of it.',
        equivalence_and_intervals=tost,
        cluster_and_mixture=dict(mixture=cl['mixture'],
                                 operational_utility=cl['operational_utility'],
                                 predictability=cl['predictability'],
                                 partition_stability=cl['partition_stability'],
                                 per_cluster=cl['per_cluster']),
        boundary_and_subgroups=sg,
        chameleon_extension=ext)
    p = os.path.join(OUT, 'diagnostics_summary.json')
    json.dump(summary, open(p, 'w'), indent=2, sort_keys=True)
    _p('wrote %s' % p)

    for name, txt in (('table_tost_equivalence.tex', table_tost(tost)),
                      ('table_cluster_composition.tex', table_cluster(cl)),
                      ('table_subgroup_metrics.tex', table_subgroup(sg))):
        q = os.path.join(PAPER, name)
        open(q, 'w').write(txt)
        _p('wrote %s' % q)

    fig_cluster(cl)
    fig_cham(ext)


if __name__ == '__main__':
    main()

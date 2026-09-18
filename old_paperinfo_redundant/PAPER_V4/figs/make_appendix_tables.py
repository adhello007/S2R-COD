#!/usr/bin/env python3
"""Emit appendix_tables.tex from committed artifacts. Regenerable, not hand-typed."""
import csv, json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(REPO, 'rebuild', 'PAPER_V4', 'appendix_tables.tex')
B1 = os.path.join(REPO, 'rebuild', 'B1', 'out')
T2C = os.path.join(REPO, 'rebuild', 'T2C', 'out')
AC = os.path.join(REPO, 'rebuild', 'AC', 'out')
ABC = os.path.join(REPO, 'rebuild', 'ABC', 'out')
L = []
def w(x=''): L.append(x)

# ---------- A1: full silhouette sweep ----------
sw = {}
for tag in ('dinoL224', 'dinoL518', 'clipL224'):
    for r in csv.DictReader(open(os.path.join(B1, 'b1_k_sweep_%s.csv' % tag))):
        sw.setdefault(int(r['k']), {})[tag] = (
            float(r['silhouette_mean']), float(r['bootstrap_ari_mean']), float(r['seed_ari_mean']))
w(r"""\begin{table}[h]
\caption{Full clustering sweep over the target set: silhouette (mean over 10 $k$-means seeds),
bootstrap ARI and seed ARI, for every $k$ in the declared grid and all three embedding spaces.
The principled $k$ per space is \textbf{bold}. No $k$ in any space reaches a silhouette conventionally
regarded as well-separated structure, and \texttt{clipL224} falls monotonically, so its selection
criterion returns the grid edge rather than an interior maximum --- recorded as a FAIL of the declared
guard. \emph{Source:} \texttt{rebuild/B1/out/b1\_k\_sweep\_\{dinoL224,dinoL518,clipL224\}.csv};
block \texttt{EXP B1} \#3 @ \texttt{results/REBUILD\_LOG.txt:922}.}
\label{tab:silhouette}
\begin{center}\small
\begin{tabular}{rcccccccccc}
\toprule
& \multicolumn{3}{c}{\texttt{dinoL224}} & \multicolumn{3}{c}{\texttt{dinoL518}} & \multicolumn{3}{c}{\texttt{clipL224}} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}
$k$ & sil. & bs.ARI & sd.ARI & sil. & bs.ARI & sd.ARI & sil. & bs.ARI & sd.ARI \\
\midrule""")
STAR = {'dinoL224': 50, 'dinoL518': 75, 'clipL224': 5}
for k in sorted(sw):
    cells = []
    for tag in ('dinoL224', 'dinoL518', 'clipL224'):
        sil, ba, sa = sw[k][tag]
        f = (r'\textbf{%.4f}' % sil) if STAR[tag] == k else ('%.4f' % sil)
        cells += [f, '%.3f' % ba, '%.3f' % sa]
    w('%d & %s \\\\' % (k, ' & '.join(cells)))
w(r"""\bottomrule
\end{tabular}
\end{center}
\end{table}
""")

# ---------- A2: full T2C table, 16 rows ----------
w(r"""\begin{table}[h]
\caption{Full signal-generality measurement, all 16 rows: four signal variants across three signal
families, two architectures, two aggregations. $\rho$ at the committed seed, $\pm$ sd over 10
$k$-means seeds. The whole-image block passes the pre-registered ordering $8/8$; the boundary block
passes $2/8$ with four rows going negative, an outcome outside the pre-registered interpretation
space, reported as it fell. \emph{Source:} \texttt{rebuild/T2C/out/t2c\_table.csv}; block
\texttt{EXP T2C} @ \texttt{results/REBUILD\_LOG.txt:2550}.}
\label{tab:t2cfull}
\begin{center}\small
\begin{tabular}{llcccccc}
\toprule
arch & signal & agg. & $\rho(\mathrm{MAE})$ & $\rho(1-S_\alpha)$ & $\rho(1-\mathrm{IoU})$ & order & seeds \\
\midrule""")
rows = [r for r in csv.DictReader(open(os.path.join(T2C, 't2c_table.csv'))) if r['primary'] == '1']
for r in sorted(rows, key=lambda x: (x['arch'], x['aggregation'] != 'whole', x['signal'])):
    w('%s & %s & %s & $%+.4f \\pm %.4f$ & $%+.4f \\pm %.4f$ & $%+.4f \\pm %.4f$ & %s & %s \\\\'
      % (r['arch'].replace('/S2C', ''), r['signal'].replace(' (re-derived)', ''),
         r['aggregation'][:5], float(r['rho_mae']), float(r['sd_mae']),
         float(r['rho_one_minus_sa']), float(r['sd_one_minus_sa']),
         float(r['rho_one_minus_iou']), float(r['sd_one_minus_iou']),
         'PASS' if r['ordering_pass'] == 'True' else 'FAIL', r['ordering_seeds']))
w(r"""\bottomrule
\end{tabular}
\end{center}
\end{table}
""")

# ---------- A3: area control ----------
acr = json.load(open(os.path.join(AC, 'ac_partials.json')))
w(r"""\begin{table}[h]
\caption{The area control (\texttt{EXP AC}). First-order partial Spearman on the same cluster
partition and floors as the committed measurement. $z_{\mathrm{obj}}$ = per-cluster mean object area
on the endpoint side; $z_{\mathrm{unc}}$ = per-cluster mean uncertain-region area on the target side.
Ordering survives $7/8$ and $6/8$ against a floor of $6/8$ declared before the run. Note that
partialling object area \emph{raises} $\rho(1-S_\alpha)$ in every row --- the opposite of the
confound's prediction. \emph{Source:} \texttt{rebuild/AC/out/ac\_table.csv}; block \texttt{EXP AC} @
\texttt{results/REBUILD\_LOG.txt:2612}.}
\label{tab:areacontrol}
\begin{center}\small
\begin{tabular}{llcccccc}
\toprule
 & & \multicolumn{2}{c}{raw} & \multicolumn{2}{c}{$|\,z_{\mathrm{obj}}$} & \multicolumn{2}{c}{$|\,z_{\mathrm{unc}}$} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}
arch & signal & MAE & $1-S_\alpha$ & MAE & $1-S_\alpha$ & MAE & $1-S_\alpha$ \\
\midrule""")
for r in acr['rows']:
    w('%s & %s & $%+.4f$ & $%+.4f$ & $%+.4f$ & $%+.4f$ & $%+.4f$ & $%+.4f$ \\\\'
      % (r['arch'].replace('/S2C', ''), r['signal'], r['rho_mae'], r['rho_one_minus_sa'],
         r['z_obj_rho_mae'], r['z_obj_rho_one_minus_sa'],
         r['z_unc_rho_mae'], r['z_unc_rho_one_minus_sa']))
w(r"""\midrule
\multicolumn{2}{l}{ordering holds} & \multicolumn{2}{c}{$8/8$} & \multicolumn{2}{c}{$%d/8$} & \multicolumn{2}{c}{$%d/8$} \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
""" % (acr['n_obj'], acr['n_unc']))

# ---------- A4: per-run metrics ----------
def runs(path, tag):
    out = []
    for r in csv.DictReader(open(path)):
        out.append((tag, r['arch'], r['arm'], r['seed'], r['endpoint'],
                    float(r['Sm']), float(r['MAE'])))
    return out
allr = runs(os.path.join(ABC, 'abc_metrics.csv'), 'A/B/C') + \
       runs(os.path.join(ABC, 't2', 'abc_metrics.csv'), 'falsif.') + \
       runs(os.path.join(REPO, 'rebuild', 'PC', 'out', 'pc_metrics.csv'), 'pos.ctrl')
seen, uniq = set(), []
for t in allr:
    key = (t[1], t[2], t[3], t[4])
    if key in seen:
        continue
    seen.add(key); uniq.append(t)
w(r"""\begin{table}[h]
\caption{Per-run metrics at full recorded precision for every training run in this work --- the two frozen
campaigns and the mean-teacher positive control --- on both endpoints. Arms B and C10 appear once; they were re-scored, not re-trained, for the
falsification campaign and reproduced their committed values exactly at six decimal places.
\emph{Source:} \texttt{rebuild/ABC/out/abc\_metrics.csv} and \texttt{out/t2/abc\_metrics.csv}; blocks
\texttt{EXP ABC} \#3 and \texttt{EXP T2} \#3.}
\label{tab:perrun}
\begin{center}\small
\begin{tabular}{llllcc}
\toprule
arch & arm & seed & endpoint & $S_\alpha$ & MAE \\
\midrule""")
for tag, arch, arm, seed, ep, sm, mae in sorted(uniq, key=lambda t: (t[4], t[1], t[2], t[3])):
    w('%s & %s & %s & %s & %.6f & %.6f \\\\' % (arch, arm, seed, ep, sm, mae))
w(r"""\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
open(OUT, 'w').write('\n'.join(L))
print('wrote', OUT, len(L), 'lines;', len(uniq), 'runs tabulated')

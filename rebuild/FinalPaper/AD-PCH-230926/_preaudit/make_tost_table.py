#!/usr/bin/env python3
"""Regenerate table_tost_equivalence.tex from the EIGHT-seed campaign.

The committed table was built on n = 3 and its footnote -- "no comparison
reaches equivalence at delta = 0.005" -- is false at n = 8: five of the
sixteen SE gaps reject.  Method is make_results.py's welch_tost(), unchanged,
so this table and results.md section 4 agree by construction.
"""
import csv, collections, os
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'rebuild/ABC/out/se/abc_metrics.csv')
OUT = os.path.join(HERE, '..', 'table_tost_equivalence.tex')
DELTA = 0.005


def welch_tost(a, b):
    na, nb = len(a), len(b)
    ma, mb = np.mean(a), np.mean(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    se = np.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = float(ma - mb)
    t95 = stats.t.ppf(0.975, df)
    p1 = float(stats.t.sf((d + DELTA) / se, df))
    p2 = float(stats.t.cdf((d - DELTA) / se, df))
    return dict(d=d, ci95=(d - t95 * se, d + t95 * se), df=float(df),
                p_tost=max(p1, p2), bound=float(abs(d) + stats.t.ppf(0.95, df) * se))


rows = list(csv.DictReader(open(SRC)))
by = collections.defaultdict(dict)
for r in rows:
    if r['endpoint'] != 'COD10K':
        continue
    by[r['arch']].setdefault(r['arm'], {})[r['seed']] = float(r['Sm'])

GAPS = [('C10', 'B'), ('C10', 'CSHUF'), ('C10', 'CINV'), ('CSHUF', 'CINV')]
NAME = {'SINet': 'SINet', 'SINetv2': 'SINet-v2'}

lines = []
for arch in ('SINet', 'SINetv2'):
    for hi, lo in GAPS:
        seeds = sorted(set(by[arch][hi]) & set(by[arch][lo]))
        w = welch_tost([by[arch][hi][s] for s in seeds], [by[arch][lo][s] for s in seeds])
        eq = r'\textbf{%.4f}' % w['p_tost'] if w['p_tost'] < 0.05 else '%.4f' % w['p_tost']
        lines.append(r'%s & $\mathrm{%s}-\mathrm{%s}$ & $%+.4f$ & $[%+.4f, %+.4f]$ & %s & $%.4f$ \\'
                     % (NAME[arch], hi, lo, w['d'], w['ci95'][0], w['ci95'][1], eq, w['bound']))
    if arch == 'SINet':
        lines.append(r'\midrule')

tex = r"""\begin{table}[t]
\caption{Post-hoc interval estimates at \textbf{eight seeds per arm}, COD10K-test $S_\alpha$.
\emph{These decide nothing}: verdicts remain the pre-registered $2\hat{\sigma}$ rule of
Section~\ref{sec:method}. Intervals are Welch on the two arms actually compared, so they are not
inflated by an arm outside the comparison. TOST is run at $\delta = 0.005$; bold marks the
comparisons that reject, and the final column gives the smallest $\delta$ at which each comparison
\emph{could} have concluded equivalence. \emph{Source:} \texttt{out/se/abc\_metrics.csv}, via
\texttt{figs/make\_tost\_table.py} using \texttt{make\_results.py}'s \texttt{welch\_tost}.}
\label{tab:tost}
\begin{center}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}llcccc@{}}
\toprule
Arch. & Gap & $\Delta$ & 95\% CI & TOST $p$ & smallest $\delta$ \\
\midrule
""" + '\n'.join(lines) + r"""
\bottomrule
\end{tabular}
\end{center}
\footnotesize At three seeds no comparison reached equivalence at $\delta = 0.005$; at eight,
\textbf{the \emph{direction} contrasts do and the targeting-versus-random gap does not}. That
asymmetry is the same one Section~\ref{sec:concentration} reports, in statistical form.
\end{table}
"""
open(OUT, 'w').write(tex)
print('wrote', os.path.normpath(OUT))
for l in lines:
    if l != r'\midrule':
        print('  ', l[:96])

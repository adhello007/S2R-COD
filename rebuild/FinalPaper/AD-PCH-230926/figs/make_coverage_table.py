#!/usr/bin/env python3
"""Emit appendix_coverage.tex from the committed A3 artifacts. Regenerable, not hand-typed."""
import csv
import os

from _repo import REPO, paper_out, write_text
A3 = os.path.join(REPO, "rebuild", "A3", "out")
OUT = paper_out("appendix_coverage.tex")
EMB = ["dinoL224", "dinoL518", "clipL224"]
SETS = [("ceiling, RANDOM halves", "target against itself (random halves)"),
        ("COD10K 3040 vs CAMO 1000", "COD10K part vs CAMO part of the target"),
        ("NC4K (a different real set)", "NC4K, a different real set"),
        ("raw HKU-IS (pre-LAKE-RED)", "raw HKU-IS, the generator's input"),
        ("authors' pool", "authors' synthetic pool"),
        ("local renders", "our synthetic renders")]

cov = {(r["embedder"], r["set"]): float(r["recall"])
       for r in csv.DictReader(open(os.path.join(A3, "a3_coverage.csv"), encoding="utf-8"))
       if r["k"] == "5"}
auc = {(r["embedder"], r["comparison"]): float(r["auc"])
       for r in csv.DictReader(open(os.path.join(A3, "a3_probe_table.csv"), encoding="utf-8"))}

rows = [r"%s & %s \\" % (label, " & ".join("%.4f" % cov[(e, key)] for e in EMB)) for key, label in SETS]
jpeg30 = auc[("clipL224", "real vs same images JPEG-30")]
head_auth = auc[("clipL224", "real target vs AUTHORS pool (what MyTrain reads)")]
head_local = auc[("clipL224", "real target vs LOCAL renders (what ABC added)")]

tex = r"""\section{Coverage of the Target Manifold, and Why AUC Is Not Used}
\label{app:coverage}

Section~\ref{sec:why} measures how much of the real target manifold a set covers as $k$-NN recall
at $k = 5$~\citep{kynkaanniemi2019improved}: the fraction of the $4040$ target images that fall inside
the $k$-NN balls of the compared set, in each of the three embedding spaces of Table~\ref{tab:silhouette}.
Every real set covers the target near its own ceiling; both synthetic pools collapse, most sharply in
\texttt{clipL224}.

\begin{center}\small
\begin{tabular}{lccc}
\toprule
Compared set & \texttt{dinoL224} & \texttt{dinoL518} & \texttt{clipL224} \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{center}

A real-versus-synthetic classifier is not used as evidence, because it cannot distinguish a
distributional gap from a re-encoding artifact: re-saving the \emph{identical} target images at
JPEG quality $30$ already separates them from themselves at AUC $%.4f$ in \texttt{clipL224}, against
$%.4f$ and $%.4f$ for the two synthetic pools. \emph{Source:} \texttt{rebuild/A3/out/a3\_coverage.csv},
\texttt{a3\_probe\_table.csv}.
""" % (jpeg30, head_auth, head_local)
write_text(OUT, tex)
print("wrote", OUT)

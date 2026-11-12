"""Descriptive mixed models (reported, never deciding) for EXP-02 (CDR.4 item 5) and AN-01 (regression).

Runs in the separate analysis environment (rebuild/REBUTTAL/ICLR2027_REBUTTAL/.venv-analysis; statsmodels),
on long-format CSVs written by cdr_analysis.py / an01_full.py.

  cdr   BIoU@0.5 COD10K ~ C(level) + (1|allocation) + seed variance component      (statsmodels MixedLM)
        exploratory: + fill_dist_mean + n_appended  (both post-treatment; descriptive only)
  an01  metric ~ concentrated + n_appended + jaccard_to_C10 + C(arch) + (1|seed)

Usage: .venv-analysis/bin/python mixed_models.py cdr <EXP02_<arch>_long.csv> <out.md>
       .venv-analysis/bin/python mixed_models.py an01 <AN01_long.csv> <out.md>
"""
import sys
import warnings

import pandas as pd
import statsmodels.formula.api as smf


def cdr(path, out):
    df = pd.read_csv(path)
    df = df[(df.endpoint == 'COD10K') & (df.thresh == 0.5) & (df.level.isin(['LU', 'L1', 'LH', 'B']))].copy()
    df['level'] = pd.Categorical(df.level, categories=['LU', 'B', 'L1', 'LH'])
    lines = ['# EXP-02 mixed models (DESCRIPTIVE; decide nothing)', '', 'Source: `%s`' % path, '']
    for name, formula, sub in (('level only', 'boundary_iou ~ C(level)', df),
                               ('exploratory: + fill distance + pseudo-label count (post-treatment)',
                                'boundary_iou ~ C(level) + fill_dist_mean + n_appended',
                                df[df.level.isin(['LU', 'L1', 'LH'])].copy())):
        with warnings.catch_warnings(record=True) as wl:
            m = smf.mixedlm(formula, sub, groups=sub['allocation'], vc_formula={'seed': '0 + C(seed)'}).fit(reml=True)
        lines += ['## %s' % name, '', '```', str(m.summary()), '```'] + (['warnings: %s' % '; '.join(str(w.message) for w in wl)] if wl else []) + ['']
    open(out, 'w').write('\n'.join(lines) + '\n')


def an01(path, out):
    df = pd.read_csv(path)
    lines = ['# AN-01 exploratory regression -- EXPLORATORY / POST HOC, DESCRIPTIVE ONLY', '',
             '**Caveats, all binding.** (1) The fits are degenerate: the seed random-effect variance is at the boundary '
             '(singular covariance) and several optimisations did not converge (warnings per table), so standard errors and '
             'intervals are unreliable. (2) The covariates (pseudo-label count, overlap with the C10 set) are post-treatment, '
             'so no coefficient is causal. (3) The model pools both architectures, which the pre-registered rule never does. '
             '**No coefficient here, including the pooled "concentrated" interval, is evidence for a concentration effect; '
             'the pre-registered dose-response test (CDR) decides that.** The rebuttal reports only the per-contrast '
             'eight-seed boundary numbers from AN01_boundary_8seed.md (author instruction, 2026-11-12).', '']
    for (ep, metric), sub in df.groupby(['endpoint', 'metric']):
        with warnings.catch_warnings(record=True) as wl:
            m = smf.mixedlm('value ~ concentrated + n_appended + jaccard_to_C10 + C(arch)', sub, groups=sub['seed']).fit(reml=True)
        ci = m.conf_int()
        lines += ['## %s, %s' % (ep, metric), '', '| term | coef | 95% CI | p |', '|---|---|---|---|']
        for term in m.params.index:
            if term == 'Group Var':
                continue
            lines.append('| %s | %+.5f | [%+.5f, %+.5f] | %.3f |' % (term, m.params[term], ci.loc[term, 0], ci.loc[term, 1], m.pvalues[term]))
        if wl:
            lines.append('warnings: ' + '; '.join(str(w.message) for w in wl))
        lines.append('')
    open(out, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    {'cdr': cdr, 'an01': an01}[sys.argv[1]](sys.argv[2], sys.argv[3])

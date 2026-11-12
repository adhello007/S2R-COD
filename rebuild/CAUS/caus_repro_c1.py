#!/usr/bin/env python
"""CAUS AN-02 / TH-01 -- re-run the ORIGINAL C1 attribution / spread / coverage code from the frozen
embeddings and compare every output cell with the committed CSVs. Original code, unchanged; only its
output directory is redirected (to a gitignored scratch run folder), and its log block is not written.

Then derives, from both the reproduced and the committed tables:
  probe attribution: mean over the 20 cells of d(targeted) - d(null) for each null arm
  effective rank (the ORIGINAL definition, participation ratio (sum ev)^2 / sum ev^2): mean ratio,
  cells below 1; plus two labelled-exploratory alternatives on the same matrices (entropy effective
  rank, Roy & Vetterli 2007; numerical rank at 1e-6 relative tolerance)
  label-shuffle check: arm labels permuted, held-out d must collapse toward 0
Writes RESULT_TABLES/AN-02_probe_geometry.csv and AN-02_c1_reproduction.csv.
"""

import csv
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

for _p in (os.path.join(K.REBUILD, 'C1'), K.REBUILD):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np                                             # noqa: E402

COMMITTED = os.path.join(K.REBUILD, 'C1', 'out')
SCRATCH = os.path.join(K.RUNS_ROOT, '_cpu_repro', 'C1_out')
FILES = ('c1_attribution.csv', 'c1_spread.csv', 'c1_coverage.csv', 'c1_occupancy.csv')


def compare(a, b):
    ra, rb = list(csv.DictReader(open(a))), list(csv.DictReader(open(b)))
    if len(ra) != len(rb) or list(ra[0]) != list(rb[0]):
        return dict(rows=len(ra), rows_committed=len(rb), max_abs_diff='SHAPE MISMATCH', n_cells=0)
    worst, n = 0.0, 0
    for x, y in zip(ra, rb):
        for k in x:
            try:
                d = abs(float(x[k]) - float(y[k]))
                worst = max(worst, d)
                n += 1
            except ValueError:
                if x[k] != y[k]:
                    worst = float('inf')
    return dict(rows=len(ra), rows_committed=len(rb), max_abs_diff=worst, n_cells=n)


def attribution(path):
    by = {}
    for r in csv.DictReader(open(path)):
        by.setdefault((r['tag'], r['repr'], r['B']), {})[r['arm']] = float(r['d_heldout'])
    out = {}
    for null in ('shuffled_es', 'random_centroid', 'random_direction', 'random_vs_random'):
        diffs = [v['TARGETED_by_target_es'] - v[null] for v in by.values()]
        out[null] = (float(np.mean(diffs)), sum(d > 0 for d in diffs), len(diffs))
    return out


def eff_rank_alternatives():
    """Original participation ratio vs entropy effective rank vs numerical rank, same matrices."""
    import c1_space
    import c1_variance_coverage as V
    from c1_targeted_vs_random import rank_by_centroid
    rows = []
    for tag in ('dinoL518', 'dinoL224'):
        sp = c1_space.load_space(tag)
        _, order = rank_by_centroid(sp)
        verdicts = __import__('json').load(open(os.path.join(COMMITTED, 'c1_verdicts.json')))
        for rep in V.REPRS:
            alpha = verdicts['%s|%s' % (tag, rep)]['peak_alpha']
            X = V.arm_matrix(sp, rep)
            for B in V.B_GRID:
                sel, _ = V.targeted_indices(sp, order, alpha, B)
                rnd = np.random.default_rng(10_000).choice(V.POOL, B, replace=False)

                def spec(Z):
                    Zc = Z - Z.mean(0)
                    s = np.linalg.svd(Zc, compute_uv=False)
                    ev = s ** 2 / (len(Z) - 1)
                    pr = (ev.sum() ** 2) / (ev ** 2).sum()
                    p = ev / ev.sum()
                    p = p[p > 0]
                    erank = float(np.exp(-(p * np.log(p)).sum()))
                    nrank = int((s > 1e-6 * s.max()).sum())
                    return pr, erank, nrank
                a, r = spec(X[sel]), spec(X[rnd])
                rows.append(dict(tag=tag, repr=rep, B=B, pr_ratio_original=a[0] / r[0],
                                 entropy_erank_ratio_exploratory=a[1] / r[1],
                                 numerical_rank_A=a[2], numerical_rank_R=r[2]))
    return rows


def label_shuffle():
    """Permute arm labels between the targeted and random sets; held-out d should be ~0."""
    import c1_space
    import c1_variance_coverage as V
    from c1_targeted_vs_random import rank_by_centroid, effect_size
    sp = c1_space.load_space('dinoL518')
    _, order = rank_by_centroid(sp)
    verdicts = __import__('json').load(open(os.path.join(COMMITTED, 'c1_verdicts.json')))
    rows = []
    for rep in V.REPRS:
        alpha = verdicts['dinoL518|%s' % rep]['peak_alpha']
        X = V.arm_matrix(sp, rep)
        for B in (250, 1000):
            sel, _ = V.targeted_indices(sp, order, alpha, B)
            ds, dsh = [], []
            for i in range(20):
                rnd = np.random.default_rng(10_000 + i).choice(V.POOL, B, replace=False)
                ds.append(effect_size(X[sel], X[rnd], i)['d_heldout'])
                Z = np.concatenate([X[sel], X[rnd]])
                perm = np.random.default_rng(50_000 + i).permutation(len(Z))
                dsh.append(effect_size(Z[perm[:B]], Z[perm[B:]], i)['d_heldout'])
            rows.append(dict(tag='dinoL518', repr=rep, B=B, d_heldout_targeted_vs_random=float(np.mean(ds)),
                             d_heldout_label_shuffled=float(np.mean(dsh)),
                             d_heldout_label_shuffled_sd=float(np.std(dsh))))
    return rows


def main():
    import c1_variance_coverage as V
    K.assert_writable(SCRATCH)
    os.makedirs(SCRATCH, exist_ok=True)
    shutil.copy2(os.path.join(COMMITTED, 'c1_verdicts.json'), SCRATCH)
    V.OUT = SCRATCH
    sys.argv = ['c1_variance_coverage.py', '--no-log']
    V.main()
    rep = []
    for f in FILES:
        c = compare(os.path.join(SCRATCH, f), os.path.join(COMMITTED, f))
        c['file'] = f
        rep.append(c)
        print('reproduction %-20s rows %d/%d  max|diff| %s' % (f, c['rows'], c['rows_committed'], c['max_abs_diff']))
    K.write_csv(os.path.join(K.TABLES, 'AN-02_c1_reproduction.csv'), rep,
                ['file', 'rows', 'rows_committed', 'n_cells', 'max_abs_diff'])
    out = []
    for src, p in (('reproduced', SCRATCH), ('committed', COMMITTED)):
        at = attribution(os.path.join(p, 'c1_attribution.csv'))
        for null, (m, wins, n) in at.items():
            out.append(dict(source=src, quantity='mean d(targeted) - d(%s)' % null, value=round(m, 5),
                            detail='targeted larger in %d/%d cells' % (wins, n), label='original analysis'))
        sp = list(csv.DictReader(open(os.path.join(p, 'c1_spread.csv'))))
        r = [float(x['eff_rank_ratio']) for x in sp]
        out.append(dict(source=src, quantity='effective-rank ratio C/random (participation ratio)',
                        value=round(float(np.mean(r)), 5),
                        detail='below 1 in %d/%d cells; range %.3f-%.3f' % (sum(v < 1 for v in r), len(r), min(r), max(r)),
                        label='original analysis'))
    alt = eff_rank_alternatives()
    K.write_csv(os.path.join(K.TABLES, 'AN-02_effrank_definitions.csv'), alt)
    out.append(dict(source='reproduced', quantity='effective-rank ratio, participation ratio (recomputed here)',
                    value=round(float(np.mean([a['pr_ratio_original'] for a in alt])), 5),
                    detail='below 1 in %d/%d' % (sum(a['pr_ratio_original'] < 1 for a in alt), len(alt)),
                    label='original definition'))
    out.append(dict(source='reproduced', quantity='effective-rank ratio, entropy erank',
                    value=round(float(np.mean([a['entropy_erank_ratio_exploratory'] for a in alt])), 5),
                    detail='below 1 in %d/%d' % (sum(a['entropy_erank_ratio_exploratory'] < 1 for a in alt), len(alt)),
                    label='EXPLORATORY alternative definition'))
    for r in label_shuffle():
        out.append(dict(source='reproduced', quantity='label-shuffle check %s B=%d' % (r['repr'], r['B']),
                        value=round(r['d_heldout_label_shuffled'], 5),
                        detail='targeted vs random d=%.4f; shuffled-label d sd %.4f'
                               % (r['d_heldout_targeted_vs_random'], r['d_heldout_label_shuffled_sd']),
                        label='leakage control'))
    K.write_csv(os.path.join(K.TABLES, 'AN-02_probe_geometry.csv'), out)
    for r in out:
        print('%-11s %-62s %+.5f  %s' % (r['source'], r['quantity'], r['value'], r['detail']))


if __name__ == '__main__':
    main()

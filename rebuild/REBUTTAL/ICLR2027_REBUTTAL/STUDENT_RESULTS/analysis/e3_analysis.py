"""EXP-03 (descriptive; prereg/E3.md): protocol-matched references and the gap decomposition.

Subcommands
  external   score the released SINet-V2 (E3-a) and RISE (E3-d) prediction maps with OUR scorer
             (rebuild/ABC/abc_evaluate.score) on COD10K-test and NC4K -> RESULT_TABLES/EXP03_external_scores.csv
  anchors    score committed anchor runs that have saved maps (E3-f) -> RESULT_TABLES/EXP03_anchor_scores.csv
  runs       score the E3-c / E3-e runs trained by the queue -> RESULT_TABLES/EXP03_run_scores.csv
  table      assemble RESULT_TABLES/EXP03_protocol_matched.{csv,md} and EXP03_gap_decomposition.md from the
             three score files and the verified published values (RESULT_TABLES/AN02_published_baselines.json).
             Only measured or verified cells are filled; anything missing is shown as an em dash.

Run: .venv/bin/python e3_analysis.py {external,anchors,runs,table} [--workers 16]
"""
import argparse
import csv
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

import _repo as R

KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
EPS = ('COD10K', 'NC4K')
EXT = os.path.join(R.REPO, 'Dataset', 'External')
EXTERNAL = {'E3-a SINet-V2 (released maps)': os.path.join(EXT, 'SINetV2_official', 'extract', '2021-TPAMI-SINetV2-PyTorch'),
            'E3-d RISE (released maps)': os.path.join(EXT, 'RISE', 'extract', 'RISE', 'PredictedMap')}


def _score(args):
    import abc_evaluate as E
    return E.score(*args)


def gt(ep):
    return os.path.join(R.REPO, 'Dataset', 'Test', ep, 'GT')


def write(name, rows):
    with open(os.path.join(R.TABLES, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def external(workers):
    jobs = [(name, ep, (gt(ep), os.path.join(root, ep))) for name, root in EXTERNAL.items() for ep in EPS]
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [j[2] for j in jobs]))
    rows = [dict(source=n, endpoint=ep, n=m['n'], shape_mismatch=m['shape_mismatch'], **{k: '%.6f' % m[k] for k in KEYS})
            for (n, ep, _), m in zip(jobs, res)]
    write('EXP03_external_scores.csv', rows)
    for r in rows:
        print('%-32s %-6s n=%d shape_mismatch=%d Sa %s meanEm %s wFm %s MAE %s' % (
            r['source'], r['endpoint'], r['n'], r['shape_mismatch'], r['Sm'], r['meanEm'], r['wFm'], r['MAE']))


def anchors(workers):
    """Committed single-run S2R-COD reproductions with saved maps (COD10K at Result/<net>/<run>; NC4K if present)."""
    cand = [('E3-f SINet ours (two-round, reproduced 0.7172)', 'Result/SINet/S2C'),
            ('E3-f SINet mean teacher (reproduced 0.7030)', 'Result/SINet/S2C_MT'),
            ('E3-f SINet source-only (student)', 'Result/SINet/S2C_SO_stu'),
            ('E3-f SINet-v2 ours (two-round)', 'Result/SINet-v2/S2C'),
            ('E3-f SINet-v2 mean teacher', 'Result/SINet-v2/S2C_MT'),
            ('E3-f SINet-v2 source-only (student)', 'Result/SINet-v2/S2C_SO_stu')]
    jobs = []
    for name, rel in cand:
        base = os.path.join(R.REPO, rel)
        for ep in EPS:
            d = os.path.join(base, ep) if os.path.isdir(os.path.join(base, ep)) else (base if ep == 'COD10K' else None)
            if d and os.path.isdir(d) and len([f for f in os.listdir(d) if f.endswith('.png')]) == len(os.listdir(gt(ep))):
                jobs.append((name, ep, (gt(ep), d)))
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [j[2] for j in jobs]))
    rows = [dict(source=n, endpoint=ep, n=m['n'], shape_mismatch=m['shape_mismatch'], **{k: '%.6f' % m[k] for k in KEYS})
            for (n, ep, _), m in zip(jobs, res)]
    write('EXP03_anchor_scores.csv', rows)
    for r in rows:
        print('%-50s %-6s Sa %s meanEm %s wFm %s' % (r['source'], r['endpoint'], r['Sm'], r['meanEm'], r['wFm']))


def runs(workers):
    jobs_f = json.load(open(os.path.join(R.REPO, 'rebuild', 'RL5B', 'queue_jobs.json')))['jobs']
    jobs = []
    for j in jobs_f:
        if j.get('campaign') in ('e3c', 'e3e'):
            for ep in EPS:
                d = os.path.join(R.REPO, j['pred_root'], ep)
                if os.path.isdir(d) and len(os.listdir(d)) == len(os.listdir(gt(ep))):
                    jobs.append((j, ep, (gt(ep), d)))
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(_score, [x[2] for x in jobs]))
    rows = [dict(job=j['id'], campaign=j['campaign'], arch=j['arch'], seed=j['seed'], endpoint=ep, n=m['n'],
                 **{k: '%.6f' % m[k] for k in KEYS}) for (j, ep, _), m in zip(jobs, res)]
    write('EXP03_run_scores.csv', rows)
    print('scored %d run x endpoint folders' % len(rows))


def _mean_sd(xs):
    xs = [float(x) for x in xs]
    return (float(np.mean(xs)), float(np.std(xs, ddof=1)) if len(xs) > 1 else float('nan'), len(xs))


def _welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d = float(a.mean() - b.mean())
    t = stats.t.ppf(0.975, df)
    return d, d - t * se, d + t * se


def table():
    """Protocol-matched table and gap decomposition. Only measured (our scorer) or verified published (AN-02) cells
    are filled; a missing cell is an em dash, never an estimate. The decomposition is NOT additive."""
    M3 = ('Sm', 'meanEm', 'wFm')
    rows = []

    def add(group, method, labels, train_imgs, backbone, ep_vals, n, source):
        r = dict(group=group, method=method, labels=labels, training_images=train_imgs, backbone=backbone, n=n, source=source)
        for ep in EPS:
            for m in M3:
                v = ep_vals.get(ep, {}).get(m)
                r['%s_%s' % (ep, m)] = '' if v is None else '%.4f' % v[0]
                r['%s_%s_sd' % (ep, m)] = '' if v is None or v[1] != v[1] else '%.4f' % v[1]
        rows.append(r)
    se = list(csv.DictReader(open(R.SE_METRICS)))
    abc = list(csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'abc_metrics.csv'))))
    pc = list(csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'PC', 'out', 'pc_metrics.csv'))))
    runs = list(csv.DictReader(open(os.path.join(R.TABLES, 'EXP03_run_scores.csv'))))
    ext = {(r['source'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(R.TABLES, 'EXP03_external_scores.csv')))}
    anc = {(r['source'], r['endpoint']): r for r in csv.DictReader(open(os.path.join(R.TABLES, 'EXP03_anchor_scores.csv')))}
    pub = json.load(open(os.path.join(R.TABLES, 'AN02_published_baselines.json')))['published']
    BB = {'SINet': 'ResNet-50 (ImageNet)', 'SINetv2': 'Res2Net-50 (ImageNet)'}

    def from_rows(rs, keys=M3):
        return {ep: {m: _mean_sd([r[m] for r in rs if r['endpoint'] == ep]) for m in keys if m in rs[0]}
                for ep in EPS if any(r['endpoint'] == ep for r in rs)}
    for arch in ('SINet', 'SINetv2'):
        for arm, desc in (('C10', 'Ours: targeted allocation (C10)'), ('B', 'Ours: random allocation (B)')):
            rs = [r for r in se if r['arch'] == arch and r['arm'] == arm]
            add('Synthetic-to-real (this paper)', '%s, %s' % (desc, arch), 'synthetic renders; target unlabelled',
                '4447 + 1000 renders; 4040 unlabelled', BB[arch], from_rows(rs), '8 seeds', 'committed SE runs')
        rs = [r for r in abc if r['arch'] == arch and r['arm'] == 'A0']
        add('Synthetic-to-real (this paper)', 'Ours: base pool only (A0), %s' % arch, 'synthetic renders; target unlabelled',
            '4447 renders; 4040 unlabelled', BB[arch], from_rows(rs), '3 seeds', 'committed ABC runs')
    rs = [r for r in pc if r['arm'] == 'MT']
    add('Synthetic-to-real (this paper)', 'Mean teacher, single round, SINet', 'synthetic renders; target unlabelled',
        '4447 renders; 4040 unlabelled', BB['SINet'], from_rows(rs, ('Sm',)), '3 seeds', 'committed PC runs')
    for name in ('E3-f SINet ours (two-round, reproduced 0.7172)', 'E3-f SINet mean teacher (reproduced 0.7030)',
                 'E3-f SINet source-only (student)', 'E3-f SINet-v2 ours (two-round)', 'E3-f SINet-v2 mean teacher',
                 'E3-f SINet-v2 source-only (student)'):
        vals = {ep: {m: (float(anc[(name, ep)][m]), float('nan'), 1) for m in M3} for ep in EPS if (name, ep) in anc}
        add('S2R-COD reproduction (single run, our scorer)', name.replace('E3-f ', ''), 'synthetic; target unlabelled',
            '4447 renders; 4040 unlabelled', BB['SINetv2' if 'v2' in name else 'SINet'], vals, '1 run', 'committed snapshots')
    for arch in ('SINet', 'SINetv2'):
        rs = [r for r in runs if r['campaign'] == 'e3c' and r['arch'] == arch]
        add('Supervised upper reference (our trainer)', 'Real masks of the same 4040 images, single round, %s' % arch,
            'real masks', '4040 labelled', BB[arch], from_rows(rs), '3 seeds', 'E3-c')
    add('Supervised upper reference (our trainer)', 'RISE pseudo masks, our trainer (E3-e)', 'RISE pseudo masks', '4040',
        'SINet / SINet-v2', {}, '—', 'not run (optional; author 11-12)')
    add('Released maps, re-scored by us', 'SINet-V2, supervised (released maps)', 'real masks', 'CAMO + COD10K train (4040)',
        BB['SINetv2'], {ep: {m: (float(ext[('E3-a SINet-V2 (released maps)', ep)][m]), float('nan'), 1) for m in M3} for ep in EPS},
        'released', 'E3-a')
    add('Released maps, re-scored by us', 'RISE, unsupervised (released maps, DINOv2-ViT-L14)', 'none (pseudo masks)',
        '4040 unlabelled', 'SINet-V2 detector', {ep: {m: (float(ext[('E3-d RISE (released maps)', ep)][m]), float('nan'), 1)
                                                   for m in M3} for ep in EPS}, 'released', 'E3-d')
    for name in ('SINet-V2 (supervised)', 'SINet (supervised, CVPR 2020)', 'RISE (unsupervised, ICCV 2025)',
                 'S2R-COD SINet "Ours" (synthetic-to-real)', 'S2R-COD SINet-v2 "Ours" (synthetic-to-real)'):
        p = pub[name]
        vals = {ep: {m: (p[ep][m], float('nan'), 1) for m in M3} for ep in EPS if p.get(ep)}
        add('Published (AN-02, original papers)', name, p['labels'], p['training_images'], p['backbone'], vals, 'paper',
            p['source'])
    with open(os.path.join(R.TABLES, 'EXP03_protocol_matched.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    cell = lambda r, ep, m: ('%s%s' % (r['%s_%s' % (ep, m)], (' ± ' + r['%s_%s_sd' % (ep, m)]) if r['%s_%s_sd' % (ep, m)] else '')
                             if r['%s_%s' % (ep, m)] else '—')
    md = ['# EXP-03: protocol-matched references for the performance gap (descriptive; prereg/E3.md)', '',
          '*Generated by `analysis/e3_analysis.py table`. One scorer (Eval/metrics.py), one set of test splits. E_phi is '
          'the mean E-measure. Values are mean ± SD over seeds where seeds exist. A missing cell is "—", never an estimate. '
          'A supervised model is an upper reference, not a competitor.*', '',
          '| Group | Method | Labels | n | COD10K S_a | COD10K E_phi | COD10K F_w | NC4K S_a | NC4K E_phi | NC4K F_w |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        md.append('| %s | %s | %s | %s | %s |' % (r['group'], r['method'], r['labels'], r['n'],
                                                 ' | '.join(cell(r, ep, m) for ep in EPS for m in M3)))
    open(os.path.join(R.TABLES, 'EXP03_protocol_matched.md'), 'w').write('\n'.join(md) + '\n')
    # ---- gap decomposition (S_alpha)
    def sa(arch, arm, ep):
        return [float(r['Sm']) for r in se if r['arch'] == arch and r['arm'] == arm and r['endpoint'] == ep]

    def e3c(arch, ep):
        return [float(r['Sm']) for r in runs if r['campaign'] == 'e3c' and r['arch'] == arch and r['endpoint'] == ep]
    g = ['# EXP-03: gap decomposition on S_alpha (measured cells only; NOT additive)', '',
         '*Generated by `analysis/e3_analysis.py table`. Each line compares two measured quantities under one scorer. '
         'The components overlap and do not sum to the total gap. "—" marks a component that needs a run that was not '
         'done.*', '', '| Component | Comparison | Arch | COD10K | NC4K |', '|---|---|---|---|---|']
    gap = []
    for arch in ('SINet', 'SINetv2'):
        vals = []
        for ep in EPS:
            d, lo, hi = _welch(e3c(arch, ep), sa(arch, 'C10', ep))
            vals.append('%+.4f [%+.4f, %+.4f]' % (d, lo, hi))
            gap.append(dict(component='label supervision, our recipe', arch=arch, endpoint=ep, delta=d, lo=lo, hi=hi))
        g.append('| Label supervision under our recipe | supervised anchor (real masks, 3 seeds) − C10 (8 seeds); Welch 95%% CI | %s | %s | %s |'
                 % (arch, vals[0], vals[1]))
    vals = []
    for ep in EPS:
        d = float(ext[('E3-a SINet-V2 (released maps)', ep)]['Sm']) - float(np.mean(e3c('SINetv2', ep)))
        vals.append('%+.4f (anchor seed SD %.4f)' % (d, float(np.std(e3c('SINetv2', ep), ddof=1))))
        gap.append(dict(component='recipe and reproduction', arch='SINetv2', endpoint=ep, delta=d))
    g.append('| Recipe and reproduction (official vs ours, both supervised) | released SINet-V2 − supervised anchor | SINet-v2 | %s | %s |' % tuple(vals))
    vals = []
    for ep in EPS:
        d = float(ext[('E3-d RISE (released maps)', ep)]['Sm']) - float(np.mean(sa('SINetv2', 'C10', ep)))
        vals.append('%+.4f' % d)
        gap.append(dict(component='unsupervised method and target supervision', arch='SINetv2', endpoint=ep, delta=d))
    g.append('| Unsupervised method and target supervision | RISE (re-scored) − C10 | SINet-v2 | %s | %s |' % tuple(vals))
    g.append('| Supervision quality vs recipe | our trainer on RISE pseudo masks (E3-e) − C10; RISE − E3-e | SINet / SINet-v2 | — | — |')
    sc = json.load(open(os.path.join(R.TABLES, 'AN02_published_baselines.json')))['checks']
    worst = max(c['abs_diff'] for c in sc)
    g.append('| Scorer | published − our re-score of the same released maps | SINet-V2, RISE | max abs diff %.4f over %d values | |' % (worst, len(sc)))
    g += ['', 'E3-e (our trainer on RISE pseudo masks) was optional and not run (author, 11-12), so supervision quality and '
          'recipe cannot be separated for RISE. E3-b (official SINet-V2 recipe re-trained) was not run; the released '
          'SINet-V2 maps stand in for it.']
    open(os.path.join(R.TABLES, 'EXP03_gap_decomposition.md'), 'w').write('\n'.join(g) + '\n')
    json.dump(gap, open(os.path.join(R.TABLES, 'EXP03_gap_decomposition.json'), 'w'), indent=2)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    bars = [('C10 SINet', np.mean(sa('SINet', 'C10', 'COD10K'))), ('C10 SINet-v2', np.mean(sa('SINetv2', 'C10', 'COD10K'))),
            ('RISE (re-scored)', float(ext[('E3-d RISE (released maps)', 'COD10K')]['Sm'])),
            ('Supervised anchor SINet', np.mean(e3c('SINet', 'COD10K'))),
            ('Supervised anchor SINet-v2', np.mean(e3c('SINetv2', 'COD10K'))),
            ('SINet-V2 released (re-scored)', float(ext[('E3-a SINet-V2 (released maps)', 'COD10K')]['Sm']))]
    ax.barh([b[0] for b in bars], [b[1] for b in bars], color=['0.55', '0.55', 'tab:orange', 'tab:blue', 'tab:blue', 'tab:blue'])
    ax.set_xlim(0.6, 0.85)
    ax.set_xlabel(r'$S_\alpha$ on COD10K-test (one scorer)', fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    os.makedirs(R.FIGS, exist_ok=True)
    fig.savefig(os.path.join(R.FIGS, 'EXP03_gap_bars.pdf'))
    print('\n'.join(g[5:10]))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['external', 'anchors', 'runs', 'table'])
    ap.add_argument('--workers', type=int, default=16)
    a = ap.parse_args()
    {'external': lambda: external(a.workers), 'anchors': lambda: anchors(a.workers), 'runs': lambda: runs(a.workers),
     'table': table}[a.cmd]()

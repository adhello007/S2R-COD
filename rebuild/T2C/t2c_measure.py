#!/usr/bin/env python
"""T2-C driver -- score the uncertainty signals, gate, correlate, log.

s1  score  : per-image signals on the UNLABELED TARGET set (GPU, 8 forwards/img)
s2  report : post-signal gates (G1, G4, G6, G7, G12) + the correlation matrix

INFERENCE ONLY. TRAINS NOTHING. Writes nothing outside rebuild/T2C/out/ (the one
disclosed exception is E0.step_independence's own report -- see
t2c_preflight.gate_provenance).

Usage:
  LAKE-RED/.venv/bin/python rebuild/T2C/t2c_measure.py --steps s1 --archs SINet/S2C --gpu 0
  LAKE-RED/.venv/bin/python rebuild/T2C/t2c_measure.py --steps s2
"""

import argparse
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _pth in (_REBUILD, os.path.join(_REBUILD, 'B1'), os.path.join(_REBUILD, 'C1'),
             os.path.join(_REBUILD, 'E0'), os.path.join(_REBUILD, 'ABC'),
             _HERE, os.path.dirname(_REBUILD)):
    if _pth not in sys.path:
        sys.path.insert(0, _pth)
import common as C                                            # noqa: E402
import b1_es_error_correlation as B1                           # noqa: E402
import t2c_signals as S                                        # noqa: E402
import t2c_preflight as PFT                                    # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'T2C'
OUT = S.OUT

# The section-8 table: 10 k-means seeds each, so every rho carries an sd.
PRIMARY_COLS = [
    ('es_whole',         'ES (re-derived)',   'whole'),
    ('es_boundary',      'ES (re-derived)',   'boundary'),
    ('ent_whole',        'entropy',           'whole'),
    ('ent_boundary',     'entropy',           'boundary'),
    ('ens_a0_whole',     'ensemble A0',       'whole'),
    ('ens_a0_boundary',  'ensemble A0',       'boundary'),
    ('ens_cshuf_whole',  'ensemble CSHUF',    'whole'),
    ('ens_cshuf_boundary', 'ensemble CSHUF',  'boundary'),
]
# Free variants -- same forwards, aggregation only. Seed 0 only; the
# pre-registration asks for these to be reported, not error-barred.
ROBUST_COLS = [
    ('ent_eps12_whole',    'entropy clamp 1e-12',      'whole'),
    ('ent_eps12_boundary', 'entropy clamp 1e-12',      'boundary'),
    ('es_band1',           'ES (re-derived)',          'boundary 2px'),
    ('ent_band1',          'entropy',                  'boundary 2px'),
    ('ens_a0_band1',       'ensemble A0',              'boundary 2px'),
    ('ens_cshuf_band1',    'ensemble CSHUF',           'boundary 2px'),
    ('ens_a0_sd_whole',    'ensemble A0 mean(sd)',     'whole'),
    ('ens_a0_sd_boundary', 'ensemble A0 mean(sd)',     'boundary'),
    ('ens_cshuf_sd_whole', 'ensemble CSHUF mean(sd)',  'whole'),
    ('ens_cshuf_sd_boundary', 'ensemble CSHUF mean(sd)', 'boundary'),
    ('ens_a0_ownband',     'ensemble A0 own band',     'boundary'),
    ('ens_cshuf_ownband',  'ensemble CSHUF own band',  'boundary'),
]
ALL_COLS = [c[0] for c in PRIMARY_COLS + ROBUST_COLS]
DIAG_COLS = ['es_scalar', 'band_frac', 'band1_frac', 'band_empty', 'band1_empty']


def _p(m):
    print(m, flush=True)


def sig_path(arch):
    return os.path.join(OUT, 't2c_signals_%s.csv' % arch.replace('/', '-'))


# ---------------------------------------------------------------------------
# s1 -- per-image signals on the unlabeled target set
# ---------------------------------------------------------------------------

def score_target_signals(arch, es_cfg, device='cuda', progress=500):
    """Per-image uncertainty signals. NO ground truth is used or needed.

    A direct generalisation of b1_allocation_signal.score_target_es:75-111 --
    same loader, same 352x352 + ImageNet transform, same B1._head picks, same
    sigmoid-then-statistic convention -- emitting the pre-registered scalars
    instead of one. The only reason ES is recomputed here rather than read from
    b1_target_es_<arch>.csv is that the BOUNDARY aggregation needs the unreduced
    field; the whole-image value is gated against that committed CSV (G6).

    cudnn determinism is set so T2-C's own numbers are reproducible. B1's
    committed ES was produced WITHOUT it, which is exactly why G6/G7 carry
    1e-5 / 5e-6 tolerances rather than exact equality.
    """
    import torch
    import torchvision.transforms as T
    from PIL import Image
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    spec = B1.ARCHS[arch]
    net = spec['net']
    snap = os.path.join(C.REPO, 'Snapshot', arch)

    stu = B1._load_net(net, device)
    tea = B1._load_net(net, device)
    B1._load_ckpt(stu, os.path.join(snap, spec['stu']), device)
    B1._load_ckpt(tea, os.path.join(snap, 'Tea_epoch_best.pth'), device)

    ens = {}
    for arm in S.ENS_ARMS:
        members = []
        for sd in S.ENS_SEEDS:
            rid = '%s_%s_s%d' % (S.ABC_ARCH[net], arm, sd)
            m = B1._load_net(net, device)
            B1._load_ckpt(m, os.path.join(C.REPO, 'Snapshot/ABC', rid,
                                          'Tea_epoch_best.pth'), device)
            members.append(m)
        ens[arm] = members

    es_loss, live = B1.build_es_loss(es_cfg, device)
    tf = T.Compose([T.Resize((B1.TESTSIZE, B1.TESTSIZE)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    d = C.ipath('tgt')
    names = C.listing('tgt')
    rows, paths_opened = [], []
    max_es_identity = 0.0
    with torch.no_grad():
        for i, nm in enumerate(names):
            fp = os.path.join(d, nm)
            paths_opened.append(fp)
            x = tf(Image.open(fp).convert('RGB')).unsqueeze(0).to(device)

            s = B1._head(net, stu(x)).sigmoid()
            t = B1._head(net, tea(x)).sigmoid()

            # --- ES, unreduced. G4 is checked on every image, not sampled.
            esm = S.es_map(es_loss, s, t)
            es_scalar = float(es_loss(s, t).item())
            esm_np = esm.squeeze().detach().cpu().numpy().astype(np.float64)

            tp = t.squeeze().detach().cpu().numpy().astype(np.float64)
            band = S.boundary_band(tp)                       # shared, iters=2
            band1 = S.boundary_band(tp, iters=1)             # 2px variant

            ent = S.binary_entropy_map(tp)
            ent12 = S.binary_entropy_map(tp, eps=1e-12)

            r = dict(arch=arch, name=nm, es_scalar=es_scalar)
            a_es = S.aggregate(esm_np, band)
            r['es_whole'], r['es_boundary'] = a_es['whole'], a_es['boundary']
            max_es_identity = max(max_es_identity,
                                  abs(a_es['whole'] - es_scalar))
            a_ent = S.aggregate(ent, band)
            r['ent_whole'], r['ent_boundary'] = a_ent['whole'], a_ent['boundary']
            a_e12 = S.aggregate(ent12, band)
            r['ent_eps12_whole'] = a_e12['whole']
            r['ent_eps12_boundary'] = a_e12['boundary']
            r['es_band1'] = S.aggregate(esm_np, band1)['boundary']
            r['ent_band1'] = S.aggregate(ent, band1)['boundary']

            for arm, key in (('A0', 'a0'), ('CSHUF', 'cshuf')):
                probs = [B1._head(net, m(x)).sigmoid().squeeze()
                         .detach().cpu().numpy().astype(np.float64)
                         for m in ens[arm]]
                var = S.ensemble_var_map(probs)
                sdm = np.sqrt(var)
                av = S.aggregate(var, band)
                r['ens_%s_whole' % key] = av['whole']
                r['ens_%s_boundary' % key] = av['boundary']
                asd = S.aggregate(sdm, band)
                r['ens_%s_sd_whole' % key] = asd['whole']
                r['ens_%s_sd_boundary' % key] = asd['boundary']
                r['ens_%s_band1' % key] = S.aggregate(var, band1)['boundary']
                own = S.boundary_band(np.mean(probs, axis=0))
                r['ens_%s_ownband' % key] = S.aggregate(var, own)['boundary']

            r['band_frac'] = 0.0 if band is None else float(band.mean())
            r['band1_frac'] = 0.0 if band1 is None else float(band1.mean())
            r['band_empty'] = int(band is None)
            r['band1_empty'] = int(band1 is None)
            rows.append(r)
            if (i + 1) % progress == 0:
                _p('    %s target %d/%d' % (arch, i + 1, len(names)))

    del stu, tea, ens
    torch.cuda.empty_cache()
    meta = dict(es_live=live, n=len(rows),
                max_es_map_identity_dev=max_es_identity,
                n_band_empty=sum(r['band_empty'] for r in rows),
                n_band1_empty=sum(r['band1_empty'] for r in rows),
                mean_band_frac=float(np.mean([r['band_frac'] for r in rows])),
                mean_band1_frac=float(np.mean([r['band1_frac'] for r in rows])))
    return rows, meta, paths_opened


def step_score(arch, es_cfg, device='cuda', force=False):
    p = sig_path(arch)
    if os.path.isfile(p) and not force:
        _p('  %s signals cached' % arch)
        return None
    _p('  scoring signals: %s' % arch)
    rows, meta, paths = score_target_signals(arch, es_cfg, device)

    # --- G1, the target-side invariant. HALTS before anything is written.
    inv = S.assert_target_side({r['name']: r['es_whole'] for r in rows},
                               paths, arch=arch)
    meta['target_side'] = inv
    _p('  G1 target-side invariant PASS %s' % inv)

    # --- G4, unreduced-ES identity, over every image.
    if meta['max_es_map_identity_dev'] > 1e-6:
        S._halt('G4: max |es_map.mean() - ESLoss.forward| = %.3e > 1e-6'
                % meta['max_es_map_identity_dev'])
    _p('  G4 unreduced-ES identity PASS max dev %.3e'
       % meta['max_es_map_identity_dev'])

    # --- G12, boundary coverage.
    frac = meta['n_band_empty'] / float(len(rows))
    if frac > S.MAX_EMPTY_BAND_FRAC:
        S._halt('G12: %.3f of target images have an empty band (> %.2f)'
                % (frac, S.MAX_EMPTY_BAND_FRAC))
    _p('  G12 boundary coverage PASS %d/%d empty (%.4f), mean band frac %.4f'
       % (meta['n_band_empty'], len(rows), frac, meta['mean_band_frac']))

    os.makedirs(OUT, exist_ok=True)
    fields = ['arch', 'name'] + ALL_COLS + DIAG_COLS
    with open(p, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: ('' if r.get(k) is None else r.get(k)) for k in fields})
    C.save_json(os.path.join(OUT, 't2c_signal_meta_%s.json'
                             % arch.replace('/', '-')), meta)
    _p('  wrote %s (%d rows)' % (os.path.relpath(p, C.REPO), len(rows)))
    return meta


def load_signals(arch):
    p = sig_path(arch)
    if not os.path.isfile(p):
        return None
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        for k in ALL_COLS + DIAG_COLS:
            r[k] = None if r[k] == '' else float(r[k])
    return rows


# ---------------------------------------------------------------------------
# s2 -- ES reproduction gates, then the correlation matrix
# ---------------------------------------------------------------------------

def gate_es_reproduction(arch, rows):
    """G6 per image and G7 per cluster, against the COMMITTED ES artifacts."""
    p = os.path.join(B1.OUT, 'b1_target_es_%s.csv' % arch.replace('/', '-'))
    committed = {r['name']: float(r['es']) for r in csv.DictReader(open(p))}
    dev = [abs(r['es_whole'] - committed[r['name']]) for r in rows
           if r['name'] in committed]
    g6 = dict(gate='es_repro_per_image', n=len(dev), max=float(np.max(dev)),
              mean=float(np.mean(dev)),
              passed=bool(np.max(dev) < 1e-5 and np.mean(dev) < 1e-6),
              tol='max < 1e-5, mean < 1e-6')

    # G7 has a committed per-cluster reference for the PRIMARY architecture only.
    # b1_cluster_es_<tag>.csv's target_es column is written by
    # augment_cluster_csv(tag, prim) with prim = tgt_es['SINet/S2C']
    # (b1_allocation_signal.py:283, 307), so it holds SINet/S2C's ES for every
    # architecture. Running G7 on a non-primary arch compares that arch's ES
    # against SINet/S2C's -- an unsatisfiable check, not a reproduction failure.
    # Verified: feeding B1's OWN committed SINet-v2 per-image ES through the
    # same aggregation reproduces the identical 8.754e-02 deviation.
    # See PREREGISTRATION_T2C.md Addendum A1.
    if not B1.ARCHS[arch].get('primary'):
        g7 = dict(gate='es_repro_per_cluster', not_applicable=True, passed=True,
                  reason=('b1_cluster_es_%s.csv target_es is SINet/S2C\'s ES for '
                          'every arch (b1_allocation_signal.py:283); no committed '
                          'per-cluster reference exists for %s. G6 carries the '
                          'reproduction burden and is per-architecture.'
                          % (S.TAG, arch)))
        return g6, g7

    sig = {r['name']: r['es_whole'] for r in rows}
    ces = S.cluster_target_signal(S.TAG, S.K, S.COMMITTED_SEED, sig)
    cc = {int(r['cluster']): r['target_es'] for r in csv.DictReader(
        open(os.path.join(B1.OUT, 'b1_cluster_es_%s.csv' % S.TAG)))
        if r['target_es'] not in ('', None)}
    cdev = [abs(ces[c][0] - float(cc[c])) for c in sorted(ces) if c in cc]
    g7 = dict(gate='es_repro_per_cluster', n=len(cdev), max=float(np.max(cdev)),
              passed=bool(np.max(cdev) <= 5e-6), tol='<= 5e-6 (6-dp storage)')
    return g6, g7


def correlate_all(arch, rows, seeds, X, tnames):
    """Every column x every seed, through the ONE gated correlation function."""
    res = {}
    for col, label, agg in PRIMARY_COLS + ROBUST_COLS:
        sig = {r['name']: r[col] for r in rows if r[col] is not None}
        use = seeds if col in [c[0] for c in PRIMARY_COLS] else [S.COMMITTED_SEED]
        per_seed = []
        for sd in use:
            f = S.t2c_correlation(
                S.TAG, S.K, sd, sig, arch=arch,
                n_perm=(2000 if sd == S.COMMITTED_SEED else 200),
                X=X, tnames=tnames)
            per_seed.append(f)
        head = per_seed[0]
        rec = dict(col=col, label=label, agg=agg, arch=arch,
                   n_images=len(sig), seeds=list(use), per_seed=per_seed,
                   degenerate=bool(head.get('degenerate')))
        if not rec['degenerate']:
            for e in B1.ERRORS:
                vals = [f[e]['rho'] for f in per_seed
                        if not f.get('degenerate') and f[e]['rho'] is not None]
                rec[e] = dict(rho=head[e]['rho'], perm_p=head[e]['perm_p'],
                              ci=head[e]['ci'],
                              rho_sd=(float(np.std(vals)) if len(vals) > 1 else None),
                              n_seeds=len(vals))
            rec['clusters_used'] = head['clusters_used']
            rec['n_target_in_used'] = head['n_target_in_used']
            rec['ordering_pass'] = head['ordering_pass']
            ords = [f['ordering_pass'] for f in per_seed if not f.get('degenerate')]
            rec['ordering_seeds'] = '%d/%d' % (sum(ords), len(ords))
            rec['ratio'] = head['ratio_1mSa_over_MAE']
            rr = [f['ratio_1mSa_over_MAE'] for f in per_seed
                  if not f.get('degenerate') and f['ratio_1mSa_over_MAE'] is not None]
            rec['ratio_sd'] = float(np.std(rr)) if len(rr) > 1 else None
            rec['ratio_delta_vs_es'] = rec['ratio'] - ES_COMMITTED_RATIO
        res[col] = rec
        _p('    %-24s %s' % (col, _fmt_row(rec)))
    return res


ES_COMMITTED_RATIO = 0.5463          # B1, REBUILD_LOG.txt:1008


def _fmt_row(rec):
    if rec.get('degenerate'):
        return 'DEGENERATE (%d clusters)' % rec['per_seed'][0]['clusters_used']
    def f(e):
        d = rec[e]
        return ('%+.4f+-%.4f' % (d['rho'], d['rho_sd'])
                if d['rho_sd'] is not None else '%+.4f' % d['rho'])
    return ('MAE %s | 1-Sa %s | 1-IoU %s | ord %s %s | ratio %.4f (%+.4f)'
            % (f('mae'), f('one_minus_sa'), f('one_minus_iou'),
               'PASS' if rec['ordering_pass'] else 'FAIL',
               rec['ordering_seeds'], rec['ratio'], rec['ratio_delta_vs_es']))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='s1,s2')
    ap.add_argument('--archs', default=','.join(S.ARCHS))
    ap.add_argument('--gpu', default='0')
    ap.add_argument('--seeds', type=int, default=S.N_SEEDS)
    ap.add_argument('--force-score', action='store_true')
    ap.add_argument('--skip-gate', default='')
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    steps = [s.strip() for s in args.steps.split(',')]
    archs = [a.strip() for a in args.archs.split(',')]
    os.makedirs(OUT, exist_ok=True)

    metrics, thresholds, notes, artifacts = [], [], [], []
    es_cfg = B1.parse_es_config()

    # ---------------- s1: the signal pass ----------------
    if 's1' in steps:
        _p('=== s1 uncertainty signals on the UNLABELED TARGET set ===')
        os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
        for arch in archs:
            step_score(arch, es_cfg, force=args.force_score)

    if 's2' not in steps:
        return

    # ---------------- s2: gates, then the matrix ----------------
    _p('=== s2 pre-signal gates ===')
    report = PFT.run_preflight(skip={s.strip() for s in args.skip_gate.split(',')
                                     if s.strip()})
    g = {x['gate']: x for x in report['gates']}
    for name in PFT.GATES:
        thresholds.append(('G-%s: %s' % (name, g[name].get('note', name)[:70]),
                           bool(g[name]['passed'])))
    h = g['harness']
    metrics.append(('harness_reproduces_B1_bitwise',
                    'MAE %+.16f | 1-Sa %+.16f | 1-IoU %+.16f'
                    % tuple(h['rho'][e] for e in B1.ERRORS),
                    '%d clusters, %d target images; BIT-IDENTICAL to '
                    'b1_faithful_correlation.json' % (h['clusters_used'],
                                                      h['n_target_in_used'])))
    sc = g['scorer']
    metrics.append(('scorer_reproduces_B1',
                    'Sa %.6f (delta %.2e), MAE %.6f (delta %.2e)'
                    % (sc['Sm'], sc['d_Sa'], sc['MAE'], sc['d_MAE']),
                    'abc_evaluate.score unchanged on the COMMITTED predictions, '
                    'BEFORE any new number; B1 logged 0.717216 / 0.074463'))
    ck = g['checkpoints']
    metrics.append(('signal_checkpoints_hashed', ck['n'],
                    '8 per architecture; %d duplicate ensemble members (a '
                    'duplicate would mean an arm is <3 distinct networks)'
                    % ck['duplicate_ensemble_members']))
    metrics.append(('c1_literal_ban_also_passes',
                    g['signal']['c1_literal_ban_also_passes'],
                    'T2-C never reads the endpoint ES column at all, so the '
                    'allocation-signal ban passes even though it is not the '
                    'operative rule -- the departure is narrower than '
                    'PREREGISTRATION_T2C.md T2C.2.3 anticipated'))

    X, tnames, lmeta = B1.load_target(S.TAG)
    metrics.append(('target_clustered', lmeta['kept'],
                    'of %d; %d leaked names dropped, read from %s'
                    % (lmeta['total'], lmeta['leaked_found'], lmeta['source'])))

    seeds = list(range(args.seeds))
    allres, gates_es = {}, {}
    for arch in archs:
        rows = load_signals(arch)
        if rows is None:
            _p('  %s signals MISSING -- run s1 first' % arch)
            continue
        _p('=== s2 ES reproduction gates: %s ===' % arch)
        g6, g7 = gate_es_reproduction(arch, rows)
        gates_es[arch] = (g6, g7)
        _p('  G6 per-image  max %.3e mean %.3e -> %s'
           % (g6['max'], g6['mean'], 'PASS' if g6['passed'] else 'FAIL'))
        if g7.get('not_applicable'):
            _p('  G7 per-cluster NOT APPLICABLE -- %s' % g7['reason'])
        else:
            _p('  G7 per-cluster max %.3e -> %s'
               % (g7['max'], 'PASS' if g7['passed'] else 'FAIL'))
        thresholds.append(('G6 %s: re-derived ES reproduces the committed '
                           'per-image ES (max < 1e-5, mean < 1e-6)' % arch,
                           g6['passed']))
        if not g7.get('not_applicable'):
            thresholds.append(('G7 %s: re-derived ES reproduces the committed '
                               'per-cluster target_es (<= 5e-6)' % arch,
                               g7['passed']))
        else:
            metrics.append(('G7_not_applicable_%s' % arch.replace('/', '-'),
                            'no committed per-cluster reference',
                            g7['reason']))
        if not (g6['passed'] and g7['passed']):
            S._halt('ES reproduction failed for %s; refusing to correlate' % arch)

        sm = json.load(open(os.path.join(
            OUT, 't2c_signal_meta_%s.json' % arch.replace('/', '-'))))
        metrics.append(('band_empty_%s' % arch.replace('/', '-'),
                        '%d/%d (%.4f), mean band frac %.4f'
                        % (sm['n_band_empty'], sm['n'],
                           sm['n_band_empty'] / float(sm['n']),
                           sm['mean_band_frac']),
                        'empty band -> the image contributes no boundary value; '
                        '>5%% would be a HALT'))
        metrics.append(('es_map_identity_%s' % arch.replace('/', '-'),
                        '%.3e' % sm['max_es_map_identity_dev'],
                        'max |es_map.mean() - ESLoss.forward| over all %d '
                        'images (G4, tol 1e-6)' % sm['n']))

        _p('=== s2 correlations: %s (%d seeds) ===' % (arch, len(seeds)))
        allres[arch] = correlate_all(arch, rows, seeds, X, tnames)

    C.save_json(os.path.join(OUT, 't2c_correlations.json'), allres)
    artifacts.append('rebuild/T2C/out/t2c_correlations.json')
    artifacts.append('rebuild/T2C/out/t2c_preflight.json')

    # ---------------- the section-8 table ----------------
    tp = os.path.join(OUT, 't2c_table.csv')
    with open(tp, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['arch', 'signal', 'aggregation', 'n_images', 'clusters_used',
                    'rho_mae', 'sd_mae', 'rho_one_minus_sa', 'sd_one_minus_sa',
                    'rho_one_minus_iou', 'sd_one_minus_iou', 'ordering_pass',
                    'ordering_seeds', 'ratio', 'ratio_sd', 'ratio_delta_vs_es',
                    'primary'])
        prim = {c[0] for c in PRIMARY_COLS}
        for arch, res in allres.items():
            for col, label, agg in PRIMARY_COLS + ROBUST_COLS:
                r = res.get(col)
                if r is None or r.get('degenerate'):
                    continue
                w.writerow([arch, label, agg, r['n_images'], r['clusters_used']]
                           + [x for e in B1.ERRORS
                              for x in ('%.4f' % r[e]['rho'],
                                        '' if r[e]['rho_sd'] is None
                                        else '%.4f' % r[e]['rho_sd'])]
                           + [r['ordering_pass'], r['ordering_seeds'],
                              '%.4f' % r['ratio'],
                              '' if r['ratio_sd'] is None else '%.4f' % r['ratio_sd'],
                              '%+.4f' % r['ratio_delta_vs_es'],
                              int(col in prim)])
    artifacts.append('rebuild/T2C/out/t2c_table.csv')

    # ---------------- metrics, per row ----------------
    for arch, res in allres.items():
        a = arch.replace('/', '-')
        for col, label, agg in PRIMARY_COLS:
            r = res.get(col)
            if r is None or r.get('degenerate'):
                metrics.append(('%s_%s' % (a, col), 'DEGENERATE', label))
                continue
            metrics.append(
                ('%s_%s' % (a, col),
                 'MAE %+.4f+-%.4f | 1-Sa %+.4f+-%.4f | 1-IoU %+.4f+-%.4f'
                 % tuple(x for e in B1.ERRORS
                         for x in (r[e]['rho'], r[e]['rho_sd'] or 0.0)),
                 'ordering %s (%s seeds); ratio %.4f+-%.4f, %+.4f vs ES 0.5463; '
                 '%d clusters'
                 % ('PASS' if r['ordering_pass'] else 'FAIL',
                    r['ordering_seeds'], r['ratio'], r['ratio_sd'] or 0.0,
                    r['ratio_delta_vs_es'], r['clusters_used'])))

    # ---------------- the pre-registered decision ----------------
    prim_rows = [(arch, col, res[col]) for arch, res in allres.items()
                 for col, _, _ in PRIMARY_COLS
                 if col in res and not res[col].get('degenerate')]
    whole = [(a, c, r) for a, c, r in prim_rows if c.endswith('_whole')]
    bound = [(a, c, r) for a, c, r in prim_rows if c.endswith('_boundary')]
    for nm, grp in (('whole', whole), ('boundary', bound)):
        ok = [r['ordering_pass'] for _, _, r in grp]
        metrics.append(('ORDERING_%s' % nm, '%d/%d rows PASS' % (sum(ok), len(ok)),
                        'the frozen criterion: rho(MAE) > rho(1-Sa) > rho(1-IoU) '
                        'at seed 0, per signal x architecture'))
    thresholds.append(
        ('PRE-REGISTERED: every WHOLE-IMAGE signal keeps ES\'s ordering '
         'rho(MAE) > rho(1-Sa) > rho(1-IoU) at seed 0 -- the gap is NOT '
         'ES-specific', all(r['ordering_pass'] for _, _, r in whole)))
    thresholds.append(
        ('PRE-REGISTERED: every BOUNDARY-RESTRICTED signal keeps the same '
         'ordering', all(r['ordering_pass'] for _, _, r in bound)))

    # the A0-vs-CSHUF sensitivity condition
    for arch, res in allres.items():
        for agg in ('whole', 'boundary'):
            a0, cs = res.get('ens_a0_%s' % agg), res.get('ens_cshuf_%s' % agg)
            if not a0 or not cs or a0.get('degenerate') or cs.get('degenerate'):
                continue
            agree = a0['ordering_pass'] == cs['ordering_pass']
            metrics.append(
                ('ENSEMBLE_sensitivity_%s_%s' % (arch.replace('/', '-'), agg),
                 'A0 %s / CSHUF %s -> %s'
                 % ('PASS' if a0['ordering_pass'] else 'FAIL',
                    'PASS' if cs['ordering_pass'] else 'FAIL',
                    'AGREE' if agree else 'DISAGREE -- possible weak-member artifact'),
                 'A0 arm sd 0.017266 (SINet) / 0.010575 (SINetv2) vs CSHUF '
                 '0.001655 / 0.003523; a finding only in A0 is not a result'))
            thresholds.append(
                ('ENSEMBLE sensitivity %s %s: the A0 finding survives the tight '
                 'CSHUF ensemble' % (arch, agg), agree))

    notes.append(
        'T2-C is CORRELATIONAL. It establishes a strong prior that '
        'uncertainty-guided allocation fails for COD; it is NOT proof that every '
        'signal fails in training. COD10K-test is the SOLE endpoint (NC4K has no '
        'DINOv2 cache, is not a B1 split, and has no per-cluster error columns). '
        'rho differences below ~0.06 between signals are NOT interpreted: the '
        'committed 10-seed sds at k=75 are +-0.0264 / 0.0461 / 0.0564, so two '
        'independent rho(1-Sa) values differ with sd ~0.065. The ratio is '
        'DESCRIPTIVE ONLY, benchmarked against ES\'s committed 0.5463 and never '
        'against 0.5 -- B1 itself froze a threshold declaring the 0.5 boundary '
        '"still not stateable" and logged VERDICT_binary_is_k_stable=False.')
    notes.append(
        'Ensemble rows are the WEAKEST evidence here: 3 members (a 3-sample '
        'variance has ~70% relative standard error), A0 members differ by 0.0334 '
        'Sa (SINet), only the training seed differs so this is '
        'optimisation-stochasticity disagreement rather than epistemic '
        'uncertainty, and the members are NOT the model whose error is the '
        'endpoint column (S2C teacher Sa 0.717216 matches no A0 member). A null '
        'from the ensemble is weaker than a null from entropy.')
    notes.append(
        'ONE shared boundary band per image, from the S2C teacher, used by all '
        'three signals, so "boundary-restricted" names the same region in every '
        'row. A per-signal band would make each row a different region and '
        'confound the comparison invisibly; it is reported for the ensemble as '
        'the ens_*_ownband robustness row only.')

    block = C.log_block(
        EXP,
        'LAKE-RED/.venv/bin/python rebuild/T2C/t2c_measure.py --steps %s --archs %s'
        % (args.steps, args.archs),
        metrics, thresholds, [], artifacts,
        representation=('signals on the UNLABELED TARGET set at 352x352 + ImageNet '
                        'norm on the RAW sigmoid; error from B1\'s committed '
                        'COD10K-test per-image CSV; joined ONLY through the '
                        'committed dinoL518 k=75 seed=0 partition'),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

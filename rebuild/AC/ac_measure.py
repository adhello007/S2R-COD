#!/usr/bin/env python
"""EXP AC -- the area control on the pixel-over-structure ordering.

Tests whether T2C's licensed claim survives partialling out area. Rule frozen in
PREREGISTRATION_AC.md, committed at c2114af before this file existed.

INFERENCE-FREE. TRAINS NOTHING. NO GPU. Reads only committed artifacts; writes
only under rebuild/AC/out/.

Usage:
  .venv/bin/python rebuild/AC/ac_measure.py            # measure + log
  .venv/bin/python rebuild/AC/ac_measure.py --no-log   # iterate without logging
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
             os.path.join(_REBUILD, 'T2C'), _HERE, os.path.dirname(_REBUILD)):
    if _pth not in sys.path:
        sys.path.insert(0, _pth)
import common as C                                            # noqa: E402
import b1_es_error_correlation as B1                           # noqa: E402
import t2c_signals as S                                        # noqa: E402
import numpy as np                                             # noqa: E402

EXP = 'AC'
OUT = C.exp_dir(EXP, 'out')

# The eight whole-image rows of PREREGISTRATION_AC.md SS AC.1, in table order.
ROWS = [
    ('SINet/S2C',    'es_whole',         'ES'),
    ('SINet/S2C',    'ent_whole',        'entropy'),
    ('SINet/S2C',    'ens_a0_whole',     'ensemble A0'),
    ('SINet/S2C',    'ens_cshuf_whole',  'ensemble CSHUF'),
    ('SINet-v2/S2C', 'es_whole',         'ES'),
    ('SINet-v2/S2C', 'ent_whole',        'entropy'),
    ('SINet-v2/S2C', 'ens_a0_whole',     'ensemble A0'),
    ('SINet-v2/S2C', 'ens_cshuf_whole',  'ensemble CSHUF'),
]
ERRORS = ('mae', 'one_minus_sa', 'one_minus_iou')


def _p(m):
    print('[AC] %s' % m, flush=True)


def rank(v):
    """Average-rank transform, ties averaged -- the Spearman convention."""
    v = np.asarray(v, dtype=float)
    order = np.argsort(v, kind='stable')
    r = np.empty(len(v), dtype=float)
    r[order] = np.arange(1, len(v) + 1, dtype=float)
    # average ties
    for u in np.unique(v):
        m = (v == u)
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    xc, yc = x - x.mean(), y - y.mean()
    d = np.sqrt((xc ** 2).sum() * (yc ** 2).sum())
    return float(xc.dot(yc) / d) if d > 0 else float('nan')


def spearman(a, b):
    return pearson(rank(a), rank(b))


def partial_spearman(a, b, z):
    """First-order partial Spearman, PREREGISTRATION_AC.md SS AC.3."""
    r_ab, r_az, r_bz = spearman(a, b), spearman(a, z), spearman(b, z)
    den = np.sqrt((1.0 - r_az ** 2) * (1.0 - r_bz ** 2))
    if not np.isfinite(den) or den <= 0:
        return float('nan'), r_ab, r_az, r_bz
    return float((r_ab - r_az * r_bz) / den), r_ab, r_az, r_bz


def load_signals(arch):
    p = os.path.join(S.OUT, 't2c_signals_%s.csv' % arch.replace('/', '-'))
    if not os.path.exists(p):
        raise RuntimeError('AC HALT: missing committed signal file %s' % p)
    return list(csv.DictReader(open(p)))


def build_cells(arch, col):
    """Per-cluster a (target signal), b (endpoint errors), z_obj, z_unc.

    Cluster membership, both floors and both aggregations are taken through the
    SAME committed code path T2C used -- SS AC.1.
    """
    assign = S.committed_assignment(S.TAG)
    tnames = list(assign['target_names'])
    tlab = [int(l) for l in assign['target_labels']]

    sig_rows = {r['name']: r for r in load_signals(arch)}
    # target-side per-cluster signal mean and band-area mean
    tsig, tband = {}, {}
    for nm, c in zip(tnames, tlab):
        r = sig_rows.get(nm)
        if r is None or r[col] == '' or r['band_frac'] == '':
            continue
        tsig.setdefault(c, []).append(float(r[col]))
        tband.setdefault(c, []).append(float(r['band_frac']))

    # endpoint-side per-cluster errors and object area
    X, xn, _ = B1.load_target(S.TAG)
    amap, _ = B1.assign_clusters(X, xn, S.K, S.COMMITTED_SEED, 'test', S.TAG)
    rows = B1.load_scores(arch, 'test')
    if rows is None:
        raise RuntimeError('AC HALT: committed endpoint scores missing for %s' % arch)
    err = {}
    for r in rows:
        c = amap.get(r['name'])
        if c is not None:
            err.setdefault(c, []).append(r)

    used = sorted(c for c in err
                  if len(err[c]) >= B1.MIN_CLUSTER_N and c in tsig
                  and len(tsig[c]) >= S.MIN_TARGET_IN_CLUSTER)
    cells = dict(
        used=used,
        a=[float(np.mean(tsig[c])) for c in used],
        z_unc=[float(np.mean(tband[c])) for c in used],
        z_obj=[float(np.mean([float(r['gt_fg_frac']) for r in err[c]])) for c in used],
    )
    for e in ERRORS:
        cells[e] = [float(np.mean([float(r[e]) for r in err[c]])) for c in used]
    return cells


def committed_rho_table():
    """T2C's committed seed-0 rho for the eight whole rows -- Gate G-AC1."""
    p = os.path.join(S.OUT, 't2c_table.csv')
    out = {}
    for r in csv.DictReader(open(p)):
        if r['aggregation'] != 'whole':
            continue
        key = (r['arch'], r['signal'])
        out[key] = dict(mae=float(r['rho_mae']),
                        one_minus_sa=float(r['rho_one_minus_sa']),
                        one_minus_iou=float(r['rho_one_minus_iou']))
    return out


SIGNAL_LABEL = {'ES': 'ES (re-derived)', 'entropy': 'entropy',
                'ensemble A0': 'ensemble A0', 'ensemble CSHUF': 'ensemble CSHUF'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()

    committed = committed_rho_table()
    results, gate_dev = [], []

    for arch, col, label in ROWS:
        cells = build_cells(arch, col)
        a = cells['a']
        rec = dict(arch=arch, signal=label, column=col,
                   clusters_used=len(cells['used']))
        # --- unpartialled, and Gate G-AC1 against the committed table
        for e in ERRORS:
            rec['rho_' + e] = spearman(a, cells[e])
        ck = committed.get((arch, SIGNAL_LABEL[label]))
        if ck is None:
            raise RuntimeError('AC HALT: no committed row for %s / %s' % (arch, label))
        for e in ERRORS:
            gate_dev.append(abs(rec['rho_' + e] - round(ck[e], 4)))
        # --- partials
        for zname in ('z_obj', 'z_unc'):
            for e in ERRORS:
                pr, r_ab, r_az, r_bz = partial_spearman(a, cells[e], cells[zname])
                rec['%s_rho_%s' % (zname, e)] = pr
                rec['%s_sigz_%s' % (zname, e)] = r_bz
            rec['%s_signal_vs_area' % zname] = spearman(a, cells[zname])
            rec['%s_ordering' % zname] = bool(
                rec['%s_rho_mae' % zname] > rec['%s_rho_one_minus_sa' % zname]
                > rec['%s_rho_one_minus_iou' % zname])
        rec['ordering_unpartialled'] = bool(
            rec['rho_mae'] > rec['rho_one_minus_sa'] > rec['rho_one_minus_iou'])
        results.append(rec)
        _p('%-14s %-15s rho(MAE)=%+.4f -> obj %+.4f / unc %+.4f  [%s|%s]'
           % (arch, label, rec['rho_mae'], rec['z_obj_rho_mae'],
              rec['z_unc_rho_mae'],
              'PASS' if rec['z_obj_ordering'] else 'FAIL',
              'PASS' if rec['z_unc_ordering'] else 'FAIL'))

    n_obj = sum(r['z_obj_ordering'] for r in results)
    n_unc = sum(r['z_unc_ordering'] for r in results)
    n_raw = sum(r['ordering_unpartialled'] for r in results)
    area_robust = (n_obj >= 6) and (n_unc >= 6)
    max_gate = max(gate_dev)

    C.save_json(os.path.join(OUT, 'ac_partials.json'),
                dict(rows=results, n_obj=n_obj, n_unc=n_unc, n_raw=n_raw,
                     area_robust=area_robust, gate_max_dev=max_gate))
    with open(os.path.join(OUT, 'ac_table.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=sorted(results[0]))
        w.writeheader()
        for r in results:
            w.writerow(r)

    _p('')
    _p('unpartialled ordering        : %d/8' % n_raw)
    _p('partialled on object area    : %d/8' % n_obj)
    _p('partialled on band area      : %d/8' % n_unc)
    _p('VERDICT                      : %s'
       % ('AREA-ROBUST' if area_robust else 'NOT AREA-ROBUST'))
    _p('G-AC1 max dev vs committed   : %.2e' % max_gate)

    if args.no_log:
        _p('--no-log: nothing written to REBUILD_LOG.txt')
        return

    metrics = [
        ('ordering_unpartialled', '%d/8' % n_raw,
         'reproduces T2C at the committed seed 0'),
        ('ordering_partial_object_area', '%d/8' % n_obj,
         'z_obj = per-cluster mean gt_fg_frac over endpoint images'),
        ('ordering_partial_band_area', '%d/8' % n_unc,
         'z_unc = per-cluster mean band_frac over target images'),
        ('area_robust_verdict', 'AREA-ROBUST' if area_robust else 'NOT AREA-ROBUST',
         'PREREGISTRATION_AC.md SS AC.4, >=6/8 on BOTH covariates'),
        ('G_AC1_max_dev_vs_t2c_table', '%.3e' % max_gate,
         'recomputed rho vs committed t2c_table.csv at 4dp'),
    ]
    for r in results:
        metrics.append((
            '%s|%s' % (r['arch'], r['signal']),
            'raw %+.4f/%+.4f/%+.4f | obj %+.4f/%+.4f/%+.4f | unc %+.4f/%+.4f/%+.4f'
            % (r['rho_mae'], r['rho_one_minus_sa'], r['rho_one_minus_iou'],
               r['z_obj_rho_mae'], r['z_obj_rho_one_minus_sa'], r['z_obj_rho_one_minus_iou'],
               r['z_unc_rho_mae'], r['z_unc_rho_one_minus_sa'], r['z_unc_rho_one_minus_iou']),
            'MAE/1-Sa/1-IoU; %d clusters' % r['clusters_used']))
    thresholds = [
        ('recomputed rho reproduces the committed T2C whole-image table at 4dp',
         max_gate < 1e-4),
        ('ordering survives partialling on object area in >=6 of 8 rows', n_obj >= 6),
        ('ordering survives partialling on band area in >=6 of 8 rows', n_unc >= 6),
    ]
    C.log_block(
        EXP,
        cmd='.venv/bin/python rebuild/AC/ac_measure.py',
        metrics=metrics, thresholds=thresholds,
        artifacts=[os.path.join(OUT, 'ac_partials.json'),
                   os.path.join(OUT, 'ac_table.csv')],
        representation=('per-cluster target signal vs per-cluster endpoint error, '
                        'dinoL518 k=75 committed seed 0, floors >=15 endpoint / '
                        '>=5 target, first-order partial Spearman'),
        trains='NO',
        notes=('AREA CONTROL ON T2C. Rule frozen in PREREGISTRATION_AC.md at c2114af, '
               'BEFORE this script existed. Tests the confound T2C\'s own post-hoc '
               'explanation implies but does not test: a whole-image mean is '
               'uncertainty density x area, MAE scales with area and S_alpha carries '
               'an object-size term that does not. Cluster partition, both floors and '
               'both aggregations are IMPORTED from the committed T2C/B1 code path, '
               'not reimplemented, so any difference is attributable to the partial '
               'and to nothing else. G-AC1 asserts the unpartialled recomputation '
               'reproduces the committed table before any partial is reported.'))
    _p('EXP AC block appended.')


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""CDR (RL5B rebuttal) -- draw and commit the concentration dose-response allocations.

Pre-registration: rebuild/REBUTTAL/ICLR2027_REBUTTAL/STUDENT_RESULTS/prereg/CDR.md.
This script implements the permutation-acceptance rule stated there; it is run ONCE, before any
CDR run, and its output manifest (rebuild/ABC/out/cdr/cdr_permutations.json) is committed. Every
other script (pool builder, gates, trainer driver) reads the arms from that manifest via
abc_common.CDR, so the allocations cannot drift.

Levels (budget N = 1000, committed target scores, committed fill rule):
  LU  cluster-uniform quotas (largest remainder), no direction        -> arm CDRLU
  L1  softmax at tau = 1.0 (the committed shape q*) under 5 new admissible permutations
                                                                       -> arms CDRL1P1..CDRL1P5
  LH  softmax at tau = tau_H (TH-02, N_eff(q(tau_H)) ~ N_eff(q*)/2) under 5 new permutations
                                                                       -> arms CDRLHP1..CDRLHP5

Acceptance rule (fixed before drawing; never chosen by inspecting consequences):
  one stream, numpy default_rng(2027); candidate i is rng.permutation(75), i = 0, 1, 2, ...
  A candidate is accepted at a level iff
    (a) zero fixed points,
    (b) |Spearman rho(permuted scores, scores)| <= 0.10,
    (c) Jaccard(set, C10 set) <= J_C10 (0.35; relaxed to 0.40, 0.45, 0.50 in that order only if
        fewer than 5 are accepted within 10,000 candidates at the current bound),
    (d) Jaccard(set, every already-accepted set at the same level) <= 0.50 -- at L1 the committed
        CSHUF set counts as already accepted (it is L1's permutation P0),
    (e) Jaccard(set, LU set) <= 0.50, and at LH also Jaccard(set, every L1 set, CSHUF included)
        <= 0.50, so the global set-distinctness gate (every pair among the CDR sets and CSHUF
        <= 0.50) holds by construction for every drawn set.
  L1 takes the first 5 accepted. LH continues the SAME stream from the candidate after L1's fifth
  acceptance. If a level needs a relaxation step, that level is re-scanned from its own start
  position with the next bound; the step used is recorded.

Usage:
  .venv/bin/python rebuild/ABC/cdr_allocate.py draw --tau-high 0.758
  .venv/bin/python rebuild/ABC/cdr_allocate.py show --allocation_mode {uniform,permuted,tau} \
        [--tau T] [--perm_seed I]        # print one allocation's quotas and set statistics
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(_HERE), _HERE, os.path.join(os.path.dirname(_HERE), 'C1')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402
import c1_space                                               # noqa: E402
from c1_targeted_vs_random import (softmax_alloc, largest_remainder, rank_by_centroid,  # noqa: E402
                                   serving_orders, greedy_select)

RNG_SEED = 2027
MAX_RHO = 0.10
J_C10_STEPS = (0.35, 0.40, 0.45, 0.50)
J_PAIR_MAX = 0.50
N_PER_LEVEL = 5
SCAN = 10_000
TAU_L1 = 1.0
OUT_DIR = os.path.join(C.REPO, 'rebuild', 'ABC', 'out', 'cdr')


def space():
    return c1_space.load_space(A.EMBEDDER)


def allocation(sp, mode, tau=None, sigma=None):
    """(quotas, selected row indices, n_displaced, fill distances) for one allocation."""
    es = sp.es
    if mode == 'uniform':
        p = np.full(sp.k, 1.0 / sp.k)
        es_used = es
    else:
        es_used = es if sigma is None else es[np.asarray(sigma)]
        p = softmax_alloc(es_used, tau)
    q = largest_remainder(p, A.BUDGET)
    scores, order = rank_by_centroid(sp)
    serving = serving_orders(q, es_used)[A.SERVING]
    idx, disp = greedy_select(q, order, serving)
    return q, p, idx, disp


def fill_distances(sp, q, es_used):
    scores, order = rank_by_centroid(sp)
    serving = serving_orders(q, es_used)[A.SERVING]
    taken = np.zeros(order.shape[0], dtype=bool)
    d = []
    for c in serving:
        need, got = int(q[c]), 0
        for row in order[:, c]:
            if got == need:
                break
            if taken[row]:
                continue
            taken[row] = True
            d.append(1.0 - scores[row, c])
            got += 1
    d = np.array(d)
    return float(d.mean()), float(np.quantile(d, 0.9)), float(d.max())


def n_eff(q):
    p = np.asarray(q, float) / np.sum(q)
    p = p[p > 0]
    return float(math.exp(-(p * np.log(p)).sum()))


def jac(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b)


def spearman(es, sigma):
    return A._spearman_perm(es, np.asarray(sigma))


def stats_for(sp, name, mode, tau, sigma, idx, q, disp):
    es_used = sp.es if (mode == 'uniform' or sigma is None) else sp.es[np.asarray(sigma)]
    fm, f90, fmax = fill_distances(sp, q, es_used)
    lab = np.argmax(sp.cut[idx] @ sp.centroids.T, axis=1)
    induced = np.bincount(lab, minlength=sp.k)
    stems = [sp.names[i] for i in idx]
    return dict(arm=name, mode=mode, tau=tau, n_eff_nominal=n_eff(q), n_eff_induced=n_eff(induced),
                max_quota=int(q.max()), clusters_funded=int((q > 0).sum()), n_displaced=int(disp),
                fill_dist_mean=fm, fill_dist_p90=f90, fill_dist_max=fmax,
                stems_sha256=hashlib.sha256(('\n'.join(stems) + '\n').encode()).hexdigest())


def scan_level(sp, rng_state, tau, refs_same_level, refs_other, c10_set, bound, start_index):
    """Scan candidates from start_index with a fresh default_rng(RNG_SEED) advanced to that index.
    Returns (accepted list, index after the last candidate examined, counters)."""
    rng = np.random.default_rng(RNG_SEED)
    for _ in range(start_index):
        rng.permutation(sp.k)
    acc, cnt = [], dict(examined=0, fixed_point=0, rho=0, jaccard_c10=0, jaccard_pair=0)
    i = start_index
    while len(acc) < N_PER_LEVEL and i < start_index + SCAN:
        sigma = rng.permutation(sp.k)
        i += 1
        cnt['examined'] += 1
        if int((sigma == np.arange(sp.k)).sum()) != 0:
            cnt['fixed_point'] += 1
            continue
        rho = spearman(sp.es, sigma)
        if abs(rho) > MAX_RHO:
            cnt['rho'] += 1
            continue
        q, p, idx, disp = allocation(sp, 'permuted', tau, sigma)
        st = [sp.names[j] for j in idx]
        jc = jac(st, c10_set)
        if jc > bound:
            cnt['jaccard_c10'] += 1
            continue
        others = list(refs_same_level.values()) + [a['stems'] for a in acc] + list(refs_other.values())
        if any(jac(st, o) > J_PAIR_MAX for o in others):
            cnt['jaccard_pair'] += 1
            continue
        acc.append(dict(draw_index=i - 1, sigma=[int(x) for x in sigma], rho=rho, jaccard_c10=jc,
                        q=q, idx=idx, disp=disp, stems=st))
    return acc, i, cnt


def draw(tau_high):
    sp = space()
    c10, _ = A.arm_c_stems(1.0, None)
    cshuf, _ = A.arm_c_stems(1.0, 'shuffled')
    qu, _, idx_u, disp_u = allocation(sp, 'uniform')
    lu = [sp.names[j] for j in idx_u]
    manifest = dict(generated=C.now(), commit=C.git_commit(), rule=__doc__.split('Acceptance rule')[1].split('Usage:')[0].strip(),
                    rng_seed=RNG_SEED, tau_L1=TAU_L1, tau_H=tau_high, budget=A.BUDGET, embedder=A.EMBEDDER,
                    serving=A.SERVING, levels={}, arms={})
    rows = [stats_for(sp, 'CDRLU', 'uniform', None, None, idx_u, qu, disp_u)]
    rows[0].update(draw_index=None, rho=None, jaccard_c10=jac(lu, c10), level='LU')
    manifest['arms']['CDRLU'] = dict(mode='uniform', tau=None, sigma=None, draw_index=None)
    start = 0
    accepted_sets = {}
    for level, tau, prefix in (('L1', TAU_L1, 'CDRL1P'), ('LH', tau_high, 'CDRLHP')):
        same = {'CSHUF': cshuf} if level == 'L1' else {}
        other = {'CDRLU': lu}
        if level == 'LH':
            other['CSHUF'] = cshuf
            other.update({k: v for k, v in accepted_sets.items() if k.startswith('CDRL1P')})
        used = None
        for step, bound in enumerate(J_C10_STEPS):
            acc, end, cnt = scan_level(sp, None, tau, same, other, c10, bound, start)
            if len(acc) == N_PER_LEVEL:
                used = (step, bound, cnt)
                break
        if used is None:
            raise SystemExit('CDR HALT: level %s found fewer than %d admissible permutations at every '
                             'declared bound' % (level, N_PER_LEVEL))
        manifest['levels'][level] = dict(tau=tau, start_index=start, end_index=end, relaxation_step=used[0],
                                         jaccard_c10_bound=used[1], counters=used[2],
                                         acceptance_rate=N_PER_LEVEL / used[2]['examined'])
        for n, a in enumerate(acc, 1):
            name = '%s%d' % (prefix, n)
            accepted_sets[name] = a['stems']
            manifest['arms'][name] = dict(mode='permuted', tau=tau, sigma=a['sigma'], draw_index=a['draw_index'],
                                          rho=round(a['rho'], 5), jaccard_c10=round(a['jaccard_c10'], 4))
            r = stats_for(sp, name, 'permuted', tau, a['sigma'], a['idx'], a['q'], a['disp'])
            r.update(draw_index=a['draw_index'], rho=a['rho'], jaccard_c10=a['jaccard_c10'], level=level)
            rows.append(r)
        start = end
    # global set-distinctness gate (every CDR pair, plus each vs C10 and CSHUF), asserted
    allsets = dict(CDRLU=lu, **accepted_sets)
    pair = {}
    names = sorted(allsets)
    for i_, a in enumerate(names):
        for b in names[i_ + 1:]:
            pair['%s|%s' % (a, b)] = round(jac(allsets[a], allsets[b]), 4)
    for a in names:
        pair['%s|C10' % a] = round(jac(allsets[a], c10), 4)
        pair['%s|CSHUF' % a] = round(jac(allsets[a], cshuf), 4)
    gate = all(v <= J_PAIR_MAX for k, v in pair.items() if not k.endswith('|C10'))
    manifest['set_distinctness_gate'] = dict(passed=gate, max_pair_jaccard=J_PAIR_MAX, pairs=pair)
    if not gate:
        raise SystemExit('CDR HALT: set-distinctness gate failed: %s' % {k: v for k, v in pair.items() if v > J_PAIR_MAX})
    os.makedirs(OUT_DIR, exist_ok=True)
    C.save_json(os.path.join(OUT_DIR, 'cdr_permutations.json'), manifest)
    for name, st in allsets.items():
        with open(os.path.join(OUT_DIR, 'cdr_stems_%s.txt' % name), 'w') as fh:
            fh.write('\n'.join(st) + '\n')
    import csv
    keys = ['arm', 'level', 'mode', 'tau', 'draw_index', 'rho', 'jaccard_c10', 'n_eff_nominal', 'n_eff_induced',
            'max_quota', 'clusters_funded', 'n_displaced', 'fill_dist_mean', 'fill_dist_p90', 'fill_dist_max',
            'stems_sha256']
    with open(os.path.join(OUT_DIR, 'cdr_allocations.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ('%.6g' % r[k] if isinstance(r[k], float) else r[k]) for k in keys})
    for level, d in manifest['levels'].items():
        print('%s tau %.3f: candidates %d-%d, relaxation step %d (J_C10 <= %.2f), acceptance rate %.4f, rejections %s'
              % (level, d['tau'], d['start_index'], d['end_index'] - 1, d['relaxation_step'], d['jaccard_c10_bound'],
                 d['acceptance_rate'], d['counters']))
    for r in rows:
        print('  %-9s draw %-5s rho %+.4f J(C10) %.4f N_eff nominal %5.2f induced %5.2f max quota %3d fill mean %.4f'
              % (r['arm'], r['draw_index'], r['rho'] if r['rho'] is not None else float('nan'), r['jaccard_c10'],
                 r['n_eff_nominal'], r['n_eff_induced'], r['max_quota'], r['fill_dist_mean']))
    print('set-distinctness gate: %s (max pair Jaccard %.4f)' % (
        'PASS' if gate else 'FAIL', max(v for k, v in pair.items() if not k.endswith('|C10'))))


def show(mode, tau, perm_seed):
    sp = space()
    sigma = None
    if mode == 'permuted':
        rng = np.random.default_rng(RNG_SEED)
        for _ in range(perm_seed):
            rng.permutation(sp.k)
        sigma = rng.permutation(sp.k)
    t = None if mode == 'uniform' else (TAU_L1 if tau is None else tau)
    q, p, idx, disp = allocation(sp, 'uniform' if mode == 'uniform' else 'permuted', t, sigma)
    r = stats_for(sp, 'show', mode, t, sigma, idx, q, disp)
    print(json.dumps(dict(r, quotas=[int(x) for x in q]), indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('draw')
    d.add_argument('--tau-high', type=float, required=True)
    s = sub.add_parser('show')
    s.add_argument('--allocation_mode', choices=['uniform', 'permuted', 'tau'], required=True)
    s.add_argument('--tau', type=float, default=None)
    s.add_argument('--perm_seed', type=int, default=0, help='candidate index in the default_rng(2027) stream')
    a = ap.parse_args()
    if a.cmd == 'draw':
        draw(a.tau_high)
    else:
        show('permuted' if a.allocation_mode == 'permuted' else a.allocation_mode,
             a.tau, a.perm_seed)


if __name__ == '__main__':
    main()

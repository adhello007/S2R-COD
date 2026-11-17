#!/usr/bin/env python
"""CAUS EXP-01 / TH-01 / AN-02 -- quota, shape, capacity and overlap tables. CPU only.

Writes (under STUDENT_RESULTS/RESULT_TABLES/):
  TH-01_oracle_shapes.csv        per-cluster signal, error and the quota of every arm
  TH-01_quota_properties.csv     per-arm concentration / direction diagnostics + hashes
  TH-01_eligibility_caps.csv     per-arm x funded-cluster selection depth and similarity
  AN-02_selection_overlap.csv    every pair of arms: overlap, chance ratio, Jaccard, gate
  EXP-01_quota_manifests.csv     one row per EXP-01 / reference arm: role, hashes, files
  EXP-01_stems/<ARM>.txt         the frozen stem list of every new arm
TRAINS NOTHING. Reads endpoint-label-derived err (declared leaky) for the oracle arms only.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                             # noqa: E402

import caus_common as K                                        # noqa: E402
import exp01_alloc as X                                        # noqa: E402

REF = ('C10', 'CORACLE', 'CSHUF', 'CINV')
CHANCE = 1000 * 1000 / 4447
POLICY = ('all 4447 renders eligible for every cluster; per-cluster ranking by cosine of the '
          'R2 grey-128 cutout embedding to the dinoL518 centroid; greedy distinct selection in '
          'desc_nc serving order; no per-cluster cap; fixed N=1000')
ROLE = {'ORTOP10': 'trained (new)', 'ORTOP10SHUF': 'trained (new)', 'ORPROP': 'trained (new)',
        'ORTOP5': 'trained (new)', 'ORPROPSHUF': 'quota-only: fails distinctness gate',
        'ORPROPINV': 'quota-only: frozen alternative, also fails gate',
        'ORTOP5SHUF': 'quota-only: no budget', 'C10': 'reused historical (ABC)',
        'CORACLE': 'reused historical (OR)', 'CSHUF': 'reference only (T2/SE)',
        'CINV': 'reference only (T2/SE)', 'B': 'reused historical (ABC), per-seed draw'}
CONTROL_OF = {'ORTOP10SHUF': 'ORTOP10', 'ORTOP5SHUF': 'ORTOP5', 'ORPROPSHUF': 'ORPROP',
              'ORPROPINV': 'ORPROP', 'CSHUF': 'C10', 'CINV': 'C10', 'CORACLE': 'C10'}


def source(arm):
    if arm in X.NEW_ARMS or arm == 'CORACLE':
        return 'endpoint-label-leaky' if not arm.endswith(('SHUF', 'INV')) else \
            'endpoint-label-leaky (shape only; direction destroyed)'
    return 'not-applicable'


def instrumented_walk(q):
    """Re-walk the committed greedy selector per cluster, recording depth and similarity.
    Asserted to select exactly what X.select() selects."""
    from c1_targeted_vs_random import rank_by_centroid, serving_orders
    sp = X._space()
    scores, order = rank_by_centroid(sp)
    serving = serving_orders(q, sp.es)['desc_nc']
    taken = np.zeros(order.shape[0], dtype=bool)
    rows, picked = [], []
    for c in serving:
        need = int(q[c])
        if need <= 0:
            continue
        got, disp, depth, sims = 0, 0, 0, []
        for pos, row in enumerate(order[:, c]):
            if taken[row]:
                disp += 1
                continue
            taken[row] = True
            picked.append(int(row))
            sims.append(float(scores[row, c]))
            got += 1
            depth = pos + 1
            if got == need:
                break
        top = scores[order[:need, c], c]
        rows.append(dict(cluster=int(c), quota=need, picked=got, displaced_in_cluster=disp,
                         walk_depth=depth, mean_cos_selected=round(float(np.mean(sims)), 5),
                         min_cos_selected=round(float(np.min(sims)), 5),
                         mean_cos_undisplaced_topq=round(float(np.mean(top)), 5),
                         cos_loss_from_displacement=round(float(np.mean(top) - np.mean(sims)), 5)))
    idx = np.array(sorted(picked))
    ref = X.select(q)[2]
    if not np.array_equal(idx, ref):
        raise SystemExit('EXP01 HALT: instrumented walk diverges from the committed selector')
    return rows


def main():
    sp = X._space()
    err, prov = X.oracle_err()
    arms = list(REF) + list(X.NEW_ARMS)
    Q, meta = {}, {}
    for a in REF:
        Q[a], meta[a] = X.reference_quota(a)
    for a in X.NEW_ARMS:
        Q[a], meta[a] = X.quota(a)

    # per-cluster table
    rows_b1 = sorted(csv.DictReader(open(os.path.join(K.REPO, X.A.ORACLE_CSV))),
                     key=lambda r: int(r['cluster']))
    err_rank = np.argsort(np.argsort(-err, kind='stable'), kind='stable') + 1
    es_rank = np.argsort(np.argsort(-sp.es, kind='stable'), kind='stable') + 1
    rows = []
    for c in range(X.K):
        r = dict(cluster=c, n_target=int(rows_b1[c]['n_target']), n_test=int(rows_b1[c]['n_test']),
                 oracle_err_test_one_minus_sa=round(float(err[c]), 6), err_rank=int(err_rank[c]),
                 target_es=round(float(sp.es[c]), 6), es_rank=int(es_rank[c]))
        for a in arms:
            r['q_' + a] = int(Q[a][c])
        rows.append(r)
    K.write_csv(os.path.join(K.TABLES, 'TH-01_oracle_shapes.csv'), rows)

    # selections
    S = {}
    for a in arms:
        S[a] = X.stems(a)
    for s in X.SEEDS:
        S['B_s%d' % s] = X.stems('B', s)
    disp = {a: X.select(Q[a])[1] for a in arms}

    # properties
    prop_rows = []
    for a in arms:
        p = X.properties(Q[a])
        prop_rows.append(dict(arm=X.DISPLAY[a], file_name=a, role=ROLE[a],
                              oracle_score_source=source(a), n_displaced=disp[a],
                              perm_seed=meta[a].get('perm_seed'),
                              perm_rule=meta[a].get('perm_rule', meta[a].get('es_perm')), **p))
    K.write_csv(os.path.join(K.TABLES, 'TH-01_quota_properties.csv'), prop_rows)

    # capacity / depth
    cap_rows = []
    for a in arms:
        for r in instrumented_walk(Q[a]):
            cap_rows.append(dict(arm=X.DISPLAY[a], eligible_capacity=4447, **r))
    K.write_csv(os.path.join(K.TABLES, 'TH-01_eligibility_caps.csv'), cap_rows)

    # overlaps
    keys = ['B_s42', 'B_s43', 'B_s45'] + arms
    shape = {a: X.shape_hash(Q[a]) for a in arms}
    ov = []
    for i, x in enumerate(keys):
        for y in keys[i + 1:]:
            a, b = set(S[x]), set(S[y])
            n = len(a & b)
            same = (x in shape and y in shape and shape[x] == shape[y])
            gated = same and (CONTROL_OF.get(x) == y or CONTROL_OF.get(y) == x or
                              {x, y} <= {'C10', 'CSHUF', 'CINV', 'CORACLE'})
            jac = n / len(a | b)
            ov.append(dict(arm_a=X.DISPLAY.get(x, x), arm_b=X.DISPLAY.get(y, y), overlap=n,
                           chance=round(CHANCE, 1), ratio_to_chance=round(n / CHANCE, 3),
                           jaccard=round(jac, 4), n_differing=1000 - n, same_shape=same,
                           distinctness_gate_applies=gated,
                           gate_pass=(jac <= X.JACCARD_GATE) if gated else ''))
    K.write_csv(os.path.join(K.TABLES, 'AN-02_selection_overlap.csv'), ov)

    # stems + manifest
    sd = os.path.join(K.TABLES, 'EXP-01_stems')
    K.assert_writable(sd)
    os.makedirs(sd, exist_ok=True)
    man = []
    for a in arms:
        fn = os.path.join(sd, '%s.txt' % a)
        with open(fn, 'w') as fh:
            fh.write('\n'.join(S[a]) + '\n')
        ctrl = CONTROL_OF.get(a)
        jc = (len(set(S[a]) & set(S[ctrl])) / len(set(S[a]) | set(S[ctrl]))) if ctrl else None
        man.append(dict(arm=X.DISPLAY[a], file_name=a, role=ROLE[a],
                        oracle_score_source=source(a), eligible_capacity_policy=POLICY,
                        quota_sha256=X.vec_hash(Q[a]), shape_sha256=shape[a],
                        selected_stems_sha256=K.sha256(fn), n_selected=len(S[a]),
                        n_displaced=disp[a], perm_seed=meta[a].get('perm_seed'),
                        same_shape_control_of=X.DISPLAY.get(ctrl, '') if ctrl else '',
                        jaccard_vs_control=round(jc, 4) if jc is not None else '',
                        distinctness_gate=('PASS' if jc <= X.JACCARD_GATE else 'FAIL') if jc is not None else '',
                        stems_file=os.path.relpath(fn, K.CAUS_OUT)))
    for s in X.SEEDS:
        fn = os.path.join(K.REPO, X.COMMITTED_STEMS['B_s%d' % s])
        man.append(dict(arm='B (seed %d)' % s, file_name='B_s%d' % s, role=ROLE['B'],
                        oracle_score_source='not-applicable', eligible_capacity_policy=
                        'uniform without replacement from the 4447 renders, rng 700000+seed',
                        quota_sha256='', shape_sha256='', selected_stems_sha256=K.sha256(fn),
                        n_selected=len(S['B_s%d' % s]), n_displaced='', perm_seed=700000 + s,
                        same_shape_control_of='', jaccard_vs_control='', distinctness_gate='',
                        stems_file=os.path.relpath(fn, K.REPO) + ' (committed, repo-relative)'))
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_quota_manifests.csv'), man)
    print('oracle provenance:', prov)
    for r in man:
        print('%-16s %-40s gate=%-4s J=%s disp=%s' % (r['arm'], r['role'], r['distinctness_gate'],
                                                     r['jaccard_vs_control'], r['n_displaced']))


if __name__ == '__main__':
    main()

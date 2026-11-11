#!/usr/bin/env python
"""CAUS TH-01 / AN-02 / EXP-01 -- quota, shape, capacity, overlap and selection-manifest tables.

Inputs only (allocation signal, oracle vector, frozen embeddings, committed stem files).
No training output and no endpoint SCORE of any EXP-01 run is read -- none exists when this runs.

Writes, under STUDENT_RESULTS/RESULT_TABLES/:
  TH-01_oracle_shapes.csv       per arm x cluster: err, n_test, n_target, target_es, quota
  TH-01_quota_properties.csv    per arm: sum, funded, top-1/top-5 share, entropy, HHI, Gini, TV,
                                direction (Spearman vs err and vs ES), hashes, n_displaced
  TH-01_eligibility_caps.csv    per arm x funded cluster: quota, obtained, displaced, centroid-rank
                                depth reached, cosine of last pick (capacity policy: all 4447)
  AN-02_selection_overlap.csv   every arm pair: overlap, chance, ratio, Jaccard, n_differing,
                                pair kind, and the distinctness gate where it applies
  EXP-01_quota_manifests.csv    per arm: provenance + hashes (oracle_score_source etc.)
  EXP-01_selection_manifest.csv per arm x selected image: stem, serving cluster, rank, cosine,
                                render/mask sha256
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                             # noqa: E402

import caus_common as K                                        # noqa: E402
import exp01_alloc as X                                        # noqa: E402

REF_ARMS = ('C10', 'CORACLE', 'CSHUF', 'CINV')
CHANCE = 1000 * 1000 / 4447.0


def traced_select(q):
    """Mirror of C1 greedy_select that also records WHICH cluster took each image.
    Asserted identical (indices and n_displaced) to the committed function on every call."""
    from c1_targeted_vs_random import rank_by_centroid, serving_orders, greedy_select
    sp = X._space()
    scores, order = rank_by_centroid(sp)
    serving = serving_orders(q, sp.es)[X.A.SERVING]
    taken = np.zeros(order.shape[0], dtype=bool)
    rec, per = [], {}
    disp_total = 0
    for c in serving:
        need = int(q[c])
        if need <= 0:
            continue
        got, disp, depth = 0, 0, 0
        for r, row in enumerate(order[:, c]):
            if taken[row]:
                disp += 1
                continue
            taken[row] = True
            rec.append((int(row), int(c), r, float(scores[row, c])))
            got += 1
            depth = r
            if got == need:
                break
        disp_total += disp
        per[int(c)] = dict(quota=need, obtained=got, displaced=disp, rank_depth=depth + 1,
                           last_cos=round(float(scores[order[depth, c], c]), 5),
                           first_cos=round(float(scores[order[0, c], c]), 5))
    idx_ref, disp_ref = greedy_select(q, order, serving)
    idx = np.array(sorted(r[0] for r in rec), dtype=np.int64)
    if not (np.array_equal(idx, idx_ref) and disp_total == disp_ref):
        raise SystemExit('EXP01 HALT: traced selector diverges from committed greedy_select')
    return rec, per, int(disp_ref)


def main():
    sp = X._space()
    err, prov = X.oracle_err()
    import csv
    b1 = sorted(csv.DictReader(open(os.path.join(K.REPO, X.A.ORACLE_CSV))),
                key=lambda r: int(r['cluster']))
    n_test = [int(r['n_test']) for r in b1]
    n_target = [int(r['n_target']) for r in b1]

    arms = list(REF_ARMS) + list(X.NEW_ARMS)
    quotas, info = {}, {}
    for a in REF_ARMS:
        quotas[a], info[a] = X.reference_quota(a)
    for a in X.NEW_ARMS:
        quotas[a], info[a] = X.quota(a)

    # ---- shapes, per cluster
    rows = []
    for c in range(X.K):
        r = dict(cluster=c, err_test_one_minus_sa=round(float(err[c]), 6), n_test=n_test[c],
                 n_target=n_target[c], target_es=round(float(sp.es[c]), 6))
        for a in arms:
            r['q_' + X.DISPLAY[a]] = int(quotas[a][c])
        rows.append(r)
    K.write_csv(os.path.join(K.TABLES, 'TH-01_oracle_shapes.csv'), rows)

    # ---- selections (traced), properties, capacities, per-image manifest
    sel, props, caps, man = {}, [], [], []
    ren_img = os.path.join(K.REPO, X.A.REN_IMG)
    ren_msk = os.path.join(K.REPO, X.A.REN_MSK)
    for a in arms:
        rec, per, disp = traced_select(quotas[a])
        st = sorted(sp.names[r[0]] for r in rec)
        if a in REF_ARMS and st != X.committed_stems(a):
            raise SystemExit('EXP01 HALT: %s selection != committed stem file' % a)
        sel[a] = set(st)
        sf = os.path.join(K.TABLES, 'EXP-01_stems', '%s.txt' % a)
        K.assert_writable(sf)
        os.makedirs(os.path.dirname(sf), exist_ok=True)
        body = '\n'.join(st) + '\n'
        if os.path.exists(sf) and open(sf).read() != body:
            raise SystemExit('EXP01 HALT: existing %s differs from this code path' % sf)
        with open(sf, 'w') as fh:
            fh.write(body)
        p = X.properties(quotas[a])
        p.update(arm=X.DISPLAY[a], n_displaced=disp, n_selected=len(st),
                 stems_sha256=K.list_digest(st), perm_seed=info[a].get('perm_seed'),
                 trained_in_exp01=a in X.TRAINED_ARMS,
                 role=('historical reference (reused)' if a in ('C10', 'CORACLE')
                       else 'historical reference (report only)' if a in REF_ARMS
                       else 'EXP-01 trained' if a in X.TRAINED_ARMS else 'EXP-01 quota-only'))
        props.append(p)
        for c, d in sorted(per.items()):
            caps.append(dict(arm=X.DISPLAY[a], cluster=c, eligible_capacity=4447, **d))
        if a in X.NEW_ARMS or a in ('C10', 'CORACLE'):
            for row, c, r, cos in sorted(rec, key=lambda t: sp.names[t[0]]):
                stem = sp.names[row]
                man.append(dict(arm=X.DISPLAY[a], stem=stem, serving_cluster=c,
                                rank_in_cluster=r + 1, cos_to_centroid=round(cos, 5),
                                quota_of_cluster=int(quotas[a][c]),
                                render_sha256=K.sha256(os.path.join(ren_img, 'SOD_' + stem + '.jpg')),
                                mask_sha256=K.sha256(os.path.join(ren_msk, 'SOD_' + stem + '.png'))))
    lead = ['arm', 'role', 'trained_in_exp01']
    K.write_csv(os.path.join(K.TABLES, 'TH-01_quota_properties.csv'), props,
                lead + [k for k in props[0] if k not in lead])
    K.write_csv(os.path.join(K.TABLES, 'TH-01_eligibility_caps.csv'), caps)
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_selection_manifest.csv'), man)

    # ---- B draws (seed-dependent) join the overlap table
    for s in X.SEEDS:
        sel['B_s%d' % s] = set(X.stems('B', s))
        if sorted(sel['B_s%d' % s]) != X.committed_stems('B_s%d' % s):
            raise SystemExit('EXP01 HALT: B_s%d != committed stem file' % s)
    names = [X.DISPLAY.get(a, a) for a in arms] + ['B_s%d' % s for s in X.SEEDS]
    key = dict(zip(names, arms + ['B_s%d' % s for s in X.SEEDS]))
    shape = {a: X.shape_hash(quotas[a]) for a in arms}
    same_shape_pairs = {('OR-TOP10', 'OR-TOP10-SHUF'), ('OR-TOP5', 'OR-TOP5-SHUF'),
                        ('OR-PROP', 'OR-PROP-SHUF'), ('OR-PROP', 'OR-PROP-INV')}
    ov = []
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            A_, B_ = sel[key[x]], sel[key[y]]
            inter = len(A_ & B_)
            jac = inter / len(A_ | B_)
            kx, ky = key[x], key[y]
            if kx.startswith('B_') or ky.startswith('B_'):
                kind = 'random-draw pair'
            elif shape.get(kx) == shape.get(ky):
                kind = 'same-shape pair'
            else:
                kind = 'different-shape pair'
            gated = (x, y) in same_shape_pairs or (y, x) in same_shape_pairs
            ov.append(dict(arm_a=x, arm_b=y, overlap=inter, chance=round(CHANCE, 1),
                           ratio_to_chance=round(inter / CHANCE, 3), jaccard=round(jac, 4),
                           n_differing=1000 - inter, kind=kind,
                           distinctness_gate=('PASS' if jac <= X.JACCARD_GATE else 'FAIL')
                           if gated else 'not gated (disclosed)'))
    K.write_csv(os.path.join(K.TABLES, 'AN-02_selection_overlap.csv'), ov)

    # ---- per-arm manifest
    qm = []
    for a in arms:
        p = next(r for r in props if r['arm'] == X.DISPLAY[a])
        qm.append(dict(
            arm=X.DISPLAY[a], role=p['role'],
            allocation_shape=('C10 softmax multiset (tau=1.0)' if a in REF_ARMS else
                              {'ORPROP': 'proportional to err', 'ORTOP10': 'top-10 equal (100 each)',
                               'ORTOP5': 'top-5 equal (200 each)'}.get(a.replace('SHUF', '').replace('INV', ''))),
            alignment={'C10': 'target ES', 'CORACLE': 'true-err rank (C10 shape)',
                       'CSHUF': 'frozen shuffle of ES', 'CINV': 'ES rank-reversed'}.get(
                a, 'true err' if a in ('ORPROP', 'ORTOP10', 'ORTOP5')
                else 'rank-reversed vs err' if a.endswith('INV') else 'frozen shuffle'),
            oracle_score_source=('not-applicable' if a in ('C10', 'CSHUF', 'CINV')
                                 else 'endpoint-label-leaky' if a in ('CORACLE', 'ORPROP', 'ORTOP10', 'ORTOP5')
                                 else 'endpoint-label-leaky (shape only)'),
            eligible_capacity_policy='all 4447 renders eligible to every cluster; greedy distinct, '
                                     'desc_nc serving; no per-cluster cap',
            quota_sum=p['quota_sum'], clusters_funded=p['clusters_funded'],
            quota_sha256=p['quota_sha256'], shape_sha256=p['shape_sha256'],
            stems_sha256=p['stems_sha256'], perm_seed=p['perm_seed'],
            oracle_vector_sha256=prov['sha256'], oracle_source='%s:%s' % (prov['source'], prov['column'])))
    K.write_csv(os.path.join(K.TABLES, 'EXP-01_quota_manifests.csv'), qm)
    for r in props:
        print('%-14s funded=%2d max=%3d H=%.4f HHI=%.4f gini=%.3f rho_err=%+.3f disp=%d'
              % (r['arm'], r['clusters_funded'], r['max_quota'], r['entropy_norm'], r['hhi'],
                 r['gini'], r['spearman_q_err'], r['n_displaced']))
    for r in ov:
        if r['distinctness_gate'] in ('PASS', 'FAIL'):
            print('gate %-14s vs %-14s J=%.4f n_diff=%d %s' % (r['arm_a'], r['arm_b'], r['jaccard'],
                                                              r['n_differing'], r['distinctness_gate']))


if __name__ == '__main__':
    main()

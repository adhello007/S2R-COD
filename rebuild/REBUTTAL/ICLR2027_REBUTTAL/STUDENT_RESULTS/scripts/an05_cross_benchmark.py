#!/usr/bin/env python
"""AN-05 addendum: where each of the 76 CHAMELEON photographs also appears across public COD splits.

Reads only AN-05 outputs (Tier-A JSONs from the unchanged released detector, the pairs ledger). The test
and validation pools were part of the pre-specified pool list (ANALYSIS_PRESPEC.md §9). No threshold
is changed. Output: RESULT_TABLES/AN-05_cross_benchmark.csv, EXPERIMENT_LOGS/AN-05_cross_benchmark.json
"""
import argparse
import collections
import csv
import json
import os

ap = argparse.ArgumentParser()
ap.add_argument('--sr', required=True)
a = ap.parse_args()
SR = a.sr
RUN, RT = os.path.join(SR, 'RUNS/an05'), os.path.join(SR, 'RESULT_TABLES')


def tierA(pool):
    j = json.load(open(os.path.join(RUN, 'tierA_%s.json' % pool)))
    out = collections.defaultdict(list)
    for p in j['pairs']:
        out[p['image_a'][:-4]].append((p['image_b'], p['mean_abs']))
    gap = j['nearest_neighbour']['largest_gap']
    return out, gap


test, gap_t = tierA('cod10k_test')
val, gap_v = tierA('camo250_val')
nc4k, _ = tierA('nc4k_test')
rows = []
for r in csv.DictReader(open(os.path.join(RT, 'AN-05_chameleon_pairs.csv'))):
    s = r['chameleon']
    t = test.get(s, [])
    v = val.get(s, [])
    in_train = r['status'] == 'confirmed'
    rows.append(dict(
        chameleon=s, training_pool_status=r['status'], training_partner_pools=r['partner_pools'],
        cod10k_test_partner=' '.join(x for x, _ in t), cod10k_test_mean_abs=(min(d for _, d in t) if t else ''),
        camo250_partner=' '.join(x for x, _ in v) or r['exact_sha_camo250'],
        camo250_byte_identical=bool(r['exact_sha_camo250']),
        nc4k_partner=' '.join(x for x, _ in nc4k.get(s, [])),
        in_any_public_training_split=in_train,
        in_cod10k_test=bool(t), in_camo250=bool(v or r['exact_sha_camo250']),
        duplicated_anywhere_checked=bool(in_train or t or v or r['exact_sha_camo250']),
        note='Tier A = same-dimension re-encode (released detector, unchanged tolerance 6/255); a lower bound'))
with open(os.path.join(RT, 'AN-05_cross_benchmark.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
c = collections.Counter
summ = dict(
    n=len(rows),
    in_training_pools=sum(r['in_any_public_training_split'] for r in rows),
    in_cod10k_test=sum(r['in_cod10k_test'] for r in rows),
    in_cod10k_test_by_training_status=dict(c(r['training_pool_status'] for r in rows if r['in_cod10k_test'])),
    in_both_training_and_cod10k_test=sum(r['in_any_public_training_split'] and r['in_cod10k_test'] for r in rows),
    in_camo250=sum(r['in_camo250'] for r in rows),
    camo250_names=[r['chameleon'] for r in rows if r['in_camo250']],
    camo250_byte_identical=sum(r['camo250_byte_identical'] for r in rows),
    in_nc4k=sum(bool(r['nc4k_partner']) for r in rows),
    duplicated_somewhere=sum(r['duplicated_anywhere_checked'] for r in rows),
    not_found_anywhere=[r['chameleon'] for r in rows if not r['duplicated_anywhere_checked']],
    cod10k_test_nn_gap=gap_t, camo250_nn_gap=gap_v)
json.dump(summ, open(os.path.join(SR, 'EXPERIMENT_LOGS/AN-05_cross_benchmark.json'), 'w'), indent=1)
print(json.dumps(summ, indent=1))

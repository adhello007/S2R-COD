#!/usr/bin/env python
"""AN-05 addendum: was the transductive path actually exercised in this paper's 64 eight-seed runs?

For each run, list the round-2 pool (Dataset/Source/ABC/<rid>_iteration2/Image, read-only) and count how
many of the training-pool partners of the 50 confirmed CHAMELEON duplicates were appended there with the
teacher's prediction as a pseudo-label. Descriptive; decides nothing.
Output: RESULT_TABLES/AN-05_pseudolabel_exposure.csv, EXPERIMENT_LOGS/AN-05_pseudolabel_exposure.json
"""
import argparse
import csv
import json
import os
import statistics as st

ap = argparse.ArgumentParser()
ap.add_argument('--data-root', required=True)
ap.add_argument('--sr', required=True)
a = ap.parse_args()
RT = os.path.join(a.sr, 'RESULT_TABLES')
pairs = list(csv.DictReader(open(os.path.join(RT, 'AN-05_chameleon_pairs.csv'))))
partner_to_cham = {}
for r in pairs:
    if r['status'] == 'confirmed':
        for p in r['partners'].split():
            partner_to_cham[os.path.splitext(p)[0]] = r['chameleon']
runs = sorted({'%s_%s_s%s' % (r['architecture'], r['arm'], r['seed'])
               for r in csv.DictReader(open(os.path.join(RT, 'run_manifest.csv')))})
rows = []
for rid in runs:
    r1 = {os.path.splitext(n)[0] for n in os.listdir(os.path.join(a.data_root, 'Dataset/Source/ABC', rid, 'Image'))}
    r2 = {os.path.splitext(n)[0] for n in os.listdir(os.path.join(a.data_root, 'Dataset/Source/ABC', rid + '_iteration2', 'Image'))}
    app = r2 - r1
    hit = sorted({partner_to_cham[n] for n in app if n in partner_to_cham})
    rows.append(dict(runid=rid, n_appended=len(app), n_cham_partners_appended=len(hit),
                     chameleon_images_pseudolabelled=' '.join(hit)))
with open(os.path.join(RT, 'AN-05_pseudolabel_exposure.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
v = [r['n_cham_partners_appended'] for r in rows]
ever = set()
for r in rows:
    ever |= set(r['chameleon_images_pseudolabelled'].split())
summ = dict(n_runs=len(rows), n_partner_images=len(partner_to_cham), per_run_min=min(v), per_run_max=max(v),
            per_run_mean=st.mean(v), chameleon_images_pseudolabelled_in_any_run=len(ever),
            note='these photos were seen unlabelled in round 1 by every run, and some were re-used in round 2 '
                 'with the model\'s own predicted mask; no CHAMELEON ground truth is used anywhere')
json.dump(summ, open(os.path.join(a.sr, 'EXPERIMENT_LOGS/AN-05_pseudolabel_exposure.json'), 'w'), indent=1)
print(json.dumps(summ, indent=1))

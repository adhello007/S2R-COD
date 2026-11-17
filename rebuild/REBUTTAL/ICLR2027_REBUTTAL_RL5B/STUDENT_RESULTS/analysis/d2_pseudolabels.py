"""D2: pseudo-label counts per arm from the committed SE run table (rebuild/ABC/out/se/abc_runs.csv, n_appended =
pool_r2 - pool_r1), for the 40 runs the seed expansion added (seeds 46-50) and for all eight seeds (42-50), both
architectures. Writes RESULT_TABLES/D2_pseudolabel_counts.json. The manuscript quotes the seeds-46-50 figures."""
import csv
import json
import os

import numpy as np

import _repo as R

rows = list(csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'se', 'abc_runs.csv'))))
out = {}
for tag, seeds in (('added_seeds_46_50', {46, 47, 48, 49, 50}), ('all_eight_seeds_42_50', {42, 43, 45, 46, 47, 48, 49, 50})):
    sub = [r for r in rows if int(r['seed']) in seeds]
    out[tag] = dict(n_runs=len(sub), mean_by_arm={a: round(float(np.mean([int(r['n_appended']) for r in sub if r['arm'] == a])), 1)
                                                  for a in ('B', 'C10', 'CSHUF', 'CINV')},
                    min=min(int(r['n_appended']) for r in sub), max=max(int(r['n_appended']) for r in sub))
json.dump(out, open(os.path.join(R.TABLES, 'D2_pseudolabel_counts.json'), 'w'), indent=2)
print(json.dumps(out, indent=1))

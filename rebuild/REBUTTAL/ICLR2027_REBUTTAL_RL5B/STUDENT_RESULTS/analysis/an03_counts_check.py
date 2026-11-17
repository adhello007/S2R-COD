"""Independent re-count for AN-03 (validation). Counts distinct injected foregrounds per arm from the POOL
DIRECTORIES actually trained on (Dataset/Source/ABC/<RID>/Image, files prefixed SOD_), not from the stem lists
an03_foreground.py reads, and compares with RESULT_TABLES/AN03_foreground_diversity.csv.
Writes EXPERIMENT_LOGS/AN03_counts_check.log."""
import csv
import os

import _repo as R

POOLS = os.path.join(R.REPO, 'Dataset', 'Source', 'ABC')
pools = {'B_s%d' % s: 'SINet_B_s%d' % s for s in (42, 43, 45, 46, 47, 48, 49, 50)}
pools.update({a: 'SINet_%s_s42' % a for a in ('C10', 'CSHUF', 'CINV', 'CORACLE')})
pools.update({a: 'SINet_%s_s42' % a for a in ['CDRLU'] + ['CDRL1P%d' % i for i in range(1, 6)] + ['CDRLHP%d' % i for i in range(1, 6)]})
ref = {r['arm']: r for r in csv.DictReader(open(os.path.join(R.TABLES, 'AN03_foreground_diversity.csv')))}
base = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(R.REPO, 'Dataset/Source/HKU-IS/Image'))}
lines, ok_all = [], True
for arm, rid in pools.items():
    img = os.listdir(os.path.join(POOLS, rid, 'Image'))
    inj = {os.path.splitext(f)[0][4:] for f in img if f.startswith('SOD_')}
    basef = {os.path.splitext(f)[0] for f in img if not f.startswith('SOD_')}
    r = ref[arm]
    ok = (len(inj) == int(r['distinct_foregrounds']) and len(inj & base) == int(r['in_base_pool'])
          and len(img) == int(r['images_in_training_pool']) and basef == base)
    ok_all &= ok
    lines.append('%-9s pool %-18s injected %4d (ref %s), in base %4d (ref %s), images %d (ref %s), base set intact %s -> %s'
                 % (arm, rid, len(inj), r['distinct_foregrounds'], len(inj & base), r['in_base_pool'], len(img),
                    r['images_in_training_pool'], basef == base, 'MATCH' if ok else 'MISMATCH'))
lines.append('AN-03 independent count check: %s (%d arms)' % ('PASS' if ok_all else 'FAIL', len(pools)))
open(os.path.join(R.LOGS, 'AN03_counts_check.log'), 'w').write('\n'.join(lines) + '\n')
print(lines[-1])

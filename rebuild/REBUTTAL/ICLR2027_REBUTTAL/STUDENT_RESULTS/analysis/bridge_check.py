"""Bridge check (prereg/BRIDGE.md): does the patched pipeline reproduce committed run SINet_C10_s42?

1. Score Result/RL5B/bridge/SINet_C10_s42/{COD10K,NC4K} with the committed scorer and compare all nine
   metrics to rebuild/ABC/out/abc_metrics.csv (row SINet/C10/42) at 6 decimals.
2. Re-hash the bridge pool's base files, Dataset/LAKERED/output/HKU-IS and Dataset/Source/HKU-IS against
   their committed digests (rebuild/ABC/out/abc_pools.json, rebuild/E0/out/e0_manifest.sha256) to prove
   --link_pool wrote through no hardlink.
Writes EXPERIMENT_LOGS/BRIDGE_check.{json,log}.
"""
import csv
import json
import os

import _repo as R

KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
BAR = 0.0069


def main():
    import abc_evaluate as E
    import common as C
    ref = {}
    for r in csv.DictReader(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'abc_metrics.csv'))):
        if r['arch'] == 'SINet' and r['arm'] == 'C10' and r['seed'] == '42':
            ref[r['endpoint']] = r
    job = [j for j in json.load(open(os.path.join(R.REPO, 'rebuild', 'RL5B', 'queue_jobs.json')))['jobs']
           if j.get('campaign') == 'bridge'][0]           # paths exactly as the queue executed them
    out = dict(metrics={}, job_id=job['id'], pred_root=job['pred_root'], snapshot=job['snap'])
    for ep in ('COD10K', 'NC4K'):
        got = E.score(os.path.join(R.REPO, 'Dataset', 'Test', ep, 'GT'),
                      os.path.join(R.REPO, job['pred_root'], ep))
        out['metrics'][ep] = {k: dict(bridge='%.6f' % got[k], committed=ref[ep][k],
                                      equal='%.6f' % got[k] == ref[ep][k]) for k in KEYS}
    d_sa = abs(float(out['metrics']['COD10K']['Sm']['bridge']) - float(ref['COD10K']['Sm']))
    all_equal = all(v['equal'] for ep in out['metrics'].values() for v in ep.values())
    # integrity of linked sources
    pools = json.load(open(os.path.join(R.REPO, 'rebuild', 'ABC', 'out', 'abc_pools.json')))['pools']['SINet_C10_s42']
    bp = os.path.join(R.REPO, 'Dataset', 'Source', 'RL5B', 'bridge', 'SINet_C10_s42')
    _, hi, _ = C.dir_digest(os.path.join(bp, 'Image'))
    _, hg, _ = C.dir_digest(os.path.join(bp, 'GT'))
    # e0_manifest.sha256 lines are "<sha256>  <input_key>/<filename>"; the key -> directory map is
    # common.INPUTS. These five keys are every file a hardlinked pool can share an inode with.
    keys = ('auth', 'auth_gt', 'local', 'local_msk', 'tgt')
    bad, checked = [], 0
    for line in open(os.path.join(R.REPO, 'rebuild', 'E0', 'out', 'e0_manifest.sha256')):
        if line.startswith('#') or not line.strip():
            continue
        h, p = line.strip().split(None, 1)
        key, _, fname = p.strip().partition('/')
        if key in keys:
            checked += 1
            full = os.path.join(R.REPO, C.INPUTS[key]['path'], fname)
            if C.sha256(full) != h:
                bad.append(os.path.relpath(full, R.REPO))
    out['integrity'] = dict(bridge_pool_image_digest_ok=hi == pools['image_digest'],
                            bridge_pool_gt_digest_ok=hg == pools['gt_digest'],
                            source_files_checked=checked, source_files_changed=bad[:20], n_changed=len(bad))
    integ_ok = out['integrity']['bridge_pool_image_digest_ok'] and out['integrity']['bridge_pool_gt_digest_ok'] and not bad
    verdict = ('DETERMINISTIC (all 18 metric values equal at 6 dp)' if all_equal else
               ('WITHIN NOISE BAND (|dSa| %.6f <= %.4f): residual nondeterminism, campaigns continue' % (d_sa, BAR)
                if d_sa <= BAR else 'OUTSIDE BAND (|dSa| %.6f > %.4f): PAUSE AND DIAGNOSE' % (d_sa, BAR)))
    out.update(delta_Sa_COD10K=d_sa, verdict=verdict, integrity_ok=integ_ok)
    json.dump(out, open(os.path.join(R.LOGS, 'BRIDGE_check.json'), 'w'), indent=2)
    lines = ['BRIDGE: %s' % verdict, 'integrity of hardlinked sources: %s (%d files re-hashed, %d changed)'
             % ('PASS' if integ_ok else 'FAIL', checked, len(bad))]
    for ep in ('COD10K', 'NC4K'):
        lines.append('  %s Sa bridge %s committed %s' % (ep, out['metrics'][ep]['Sm']['bridge'], out['metrics'][ep]['Sm']['committed']))
    open(os.path.join(R.LOGS, 'BRIDGE_check.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()

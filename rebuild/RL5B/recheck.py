#!/usr/bin/env python
"""RECHECK (prereg/RECHECK.md): re-train SINet_C10_s42 (GPU 0) and SINet_CSHUF_s115 (GPU 1) on the current
system, with the queue's command, verification and inference, then score with the committed scorer.

Everything goes to new paths (Dataset/Source/RL5B/recheck/, Snapshot/RL5B/recheck/, Result/RL5B/recheck/); the
script refuses to start if any of them already exists, and it never deletes anything.
Usage: nohup .venv/bin/python rebuild/RL5B/recheck.py > rebuild/RL5B/recheck.log 2>&1 &
Writes rebuild/REBUTTAL/ICLR2027_REBUTTAL/STUDENT_RESULTS/EXPERIMENT_LOGS/RECHECK.{log,json}.
"""
import csv
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(REPO, 'rebuild'))
sys.path.insert(0, os.path.join(REPO, 'rebuild', 'ABC'))
import common as C            # noqa: E402
import make_pools as MP       # noqa: E402  (link_tree: the bridge's hardlink routine)
import rl5b_queue as Q        # noqa: E402  (custom_cmd, custom_verify: the queue's own)
import abc_evaluate as E      # noqa: E402  (score: the committed scorer)

LOGS = os.path.join(REPO, 'rebuild', 'REBUTTAL', 'ICLR2027_REBUTTAL', 'STUDENT_RESULTS', 'EXPERIMENT_LOGS')
EXPECT = {'rounds': 2, 'total_step': '0253', 'last_epoch': '039/040', 'pool_r1': 5447}
RUNS = [  # (run id, gpu, committed pool, pool record file, reference S_alpha on COD10K, what the reference is)
    ('SINet_C10_s42', 0, 'rebuild/ABC/out/abc_pools.json', 0.717103, 'bridge 2026-11-11, old kernel'),
    ('SINet_CSHUF_s115', 1, 'rebuild/ABC/out/eq/abc_pools.json', 0.693264, 'EQ run, new kernel'),
]


def job(rid, gpu):
    return dict(id='RECHECK_' + rid, kind='custom', arch='SINet', network='SINet', method='ours', iteration=2,
                seed=int(rid.rsplit('_s', 1)[1]), pool='Dataset/Source/RL5B/recheck/' + rid,
                snap='Snapshot/RL5B/recheck/RECHECK_' + rid, log='rebuild/RL5B/RECHECK_%s.log' % rid,
                extra=['--save_ckpts', 'minimal', '--link_pool'], ckpt='Tea_epoch_best.pth',
                pred_root='Result/RL5B/recheck/RECHECK_' + rid, expect=EXPECT, gpu=gpu)


def say(m):
    print('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), m), flush=True)


def main():
    jobs = [job(rid, gpu) for rid, gpu, *_ in RUNS]
    ph = Q.pipeline_hash()
    if ph != '281e42b8c66b3a74':          # the value every EQ run launched under
        raise SystemExit('pipeline hash %s differs from the EQ campaign: not launched' % ph)
    for j in jobs:
        for p in (j['pool'], j['pool'] + '_iteration2', j['snap'], j['pred_root']):
            if os.path.exists(os.path.join(REPO, p)):
                raise SystemExit('exists, not touched: %s' % p)
    # fresh hardlinked pools, verified against the committed digests before any GPU time
    for (rid, gpu, rec, ref, _), j in zip(RUNS, jobs):
        src = os.path.join(REPO, 'Dataset', 'Source', 'ABC', rid)
        dst = os.path.join(REPO, j['pool'])
        names, gts = sorted(os.listdir(os.path.join(src, 'Image'))), sorted(os.listdir(os.path.join(src, 'GT')))
        MP.link_tree([((os.path.join(src, 'Image', a), os.path.join(src, 'GT', b)), (a, b)) for a, b in zip(names, gts)],
                     os.path.join(dst, 'Image'), os.path.join(dst, 'GT'))
        want = json.load(open(os.path.join(REPO, rec)))['pools'][rid]
        _, hi, _ = C.dir_digest(os.path.join(dst, 'Image'))
        _, hg, _ = C.dir_digest(os.path.join(dst, 'GT'))
        if not (hi == want['image_digest'] and hg == want['gt_digest']):
            raise SystemExit('pool digest mismatch for %s: not launched' % rid)
        say('pool %s linked; digests equal to the committed record' % j['pool'])
    procs = []
    for j in jobs:
        os.makedirs(os.path.join(REPO, j['snap']), exist_ok=True)
        cmd = Q.custom_cmd(j, j['gpu'])
        lg = open(os.path.join(REPO, j['log']), 'w')
        lg.write('# RUNID   %s\n# started %s\n# commit  %s\n# CMD     %s\n\n' % (j['id'], C.now(), C.git_commit(), ' '.join(cmd)))
        lg.flush()
        procs.append((j, subprocess.Popen(cmd, cwd=REPO, stdout=lg, stderr=subprocess.STDOUT), lg))
        say('launched %s on GPU %d' % (j['id'], j['gpu']))
    out = dict(kernel=os.uname().release, commit=C.git_commit(), pipeline_hash=ph, runs={})
    for (rid, gpu, rec, ref, what), (j, p, lg) in zip(RUNS, procs):
        rc = p.wait()
        lg.close()
        ok, v = Q.custom_verify(j)
        say('%s finished rc=%d verify=%s %s' % (j['id'], rc, ok, v.get('failed_checks')))
        r = dict(rc=rc, verify_ok=ok, verify=v, reference_Sm_COD10K=ref, reference=what, metrics={})
        if rc == 0 and ok:
            for ep in ('COD10K', 'NC4K'):
                pd = os.path.join(j['pred_root'], ep)
                cmd = [Q.PY, 'MyTest.py', '--network', 'SINet', '--gpu', str(gpu), '--dataset', ep,
                       '--model_path', './' + os.path.join(j['snap'], j['ckpt']), '--test_save', './' + pd]
                with open(os.path.join(REPO, j['log'].replace('.log', '_infer_%s.log' % ep)), 'w') as il:
                    irc = subprocess.call(cmd, cwd=REPO, stdout=il, stderr=subprocess.STDOUT)
                r['metrics'][ep] = E.score(os.path.join(REPO, 'Dataset', 'Test', ep, 'GT'), os.path.join(REPO, pd))
                r['metrics'][ep]['infer_rc'] = irc
            d = abs(r['metrics']['COD10K']['Sm'] - ref)
            r['abs_delta_Sm_COD10K'] = d
            r['reading'] = ('reproduces' if d <= 0.001 else 'within the bridge band, not reproduced exactly' if d <= 0.0069
                            else 'outside the band')
        out['runs'][rid] = r
    json.dump(out, open(os.path.join(LOGS, 'RECHECK.json'), 'w'), indent=2)
    lines = ['# RECHECK (prereg/RECHECK.md): kernel %s, commit %s' % (out['kernel'], out['commit'])]
    for rid, r in out['runs'].items():
        if r['metrics']:
            m = r['metrics']['COD10K']
            lines.append('%-18s COD10K S_a %.6f vs %.6f (%s): |delta| %.6f -> %s; NC4K S_a %.6f; n_appended %s; best_epoch %s'
                         % (rid, m['Sm'], r['reference_Sm_COD10K'], r['reference'], r['abs_delta_Sm_COD10K'], r['reading'],
                            r['metrics']['NC4K']['Sm'], r['verify'].get('n_appended'), r['verify'].get('best_epoch')))
        else:
            lines.append('%-18s FAILED: rc %s, verify %s' % (rid, r['rc'], r['verify'].get('failed_checks') or r['verify'].get('fail')))
    open(os.path.join(LOGS, 'RECHECK.log'), 'w').write('\n'.join(lines) + '\n')
    say('\n'.join(lines))


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Append one campaign's jobs to rebuild/RL5B/queue_jobs.json (append-only; a campaign is added once).

Each job carries the commit that pre-registered its campaign; rl5b_queue.py refuses to launch a job
if the pipeline files differ from that commit.

  bridge   prereg/BRIDGE.md   1 SINet run (re-train of committed SINet_C10_s42), priority 1
  e3c      prereg/E3.md       SUP-ours on real masks, SINet + SINet-v2 x seeds 42,43,45, priority 2
  cdr      prereg/CDR.md      SINet: LU x 42,43,45,46,47 + L1/LH P1-P5 x 42,43,45 (35), priority 3
  eq       prereg/EQ.md       SINet: B, C10, CSHUF x seeds 101-129 (87), interleaved by seed, priority 4
  e3e      prereg/E3.md       RISE pseudo-label runs, SINet + SINet-v2 x 42,43,45, priority 5
  cdrv2    prereg/CDR.md      SINet-v2 replication of cdr (35), priority 6

Usage: .venv/bin/python rebuild/RL5B/make_jobs.py <campaign> --commit <hash>
"""
import argparse
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.path.join(_HERE, 'queue_jobs.json')
SPEC = {'SINet': dict(network='SINet', total_step='0253', last_epoch='039/040'),
        'SINetv2': dict(network='SINet-v2', total_step='0127', last_epoch='099/100')}
L1 = ['CDRL1P%d' % i for i in range(1, 6)]
LH = ['CDRLHP%d' % i for i in range(1, 6)]


def custom(id_, arch, method, iteration, seed, pool, tag, extra, ckpt, pool_r1, prio, campaign, commit):
    s = SPEC[arch]
    return dict(id=id_, kind='custom', campaign=campaign, commit=commit, priority=prio, arch=arch,
                network=s['network'], method=method, iteration=iteration, seed=seed, pool=pool,
                snap='Snapshot/RL5B/%s/%s' % (tag, id_), log='rebuild/RL5B/%s.log' % id_, extra=extra, ckpt=ckpt,
                pred_root='Result/RL5B/%s/%s' % (tag, id_),
                expect=dict(rounds=iteration, total_step=s['total_step'], last_epoch=s['last_epoch'], pool_r1=pool_r1))


def abc(arch, arm, seed, prio, campaign, commit):
    return dict(kind='abc', campaign=campaign, commit=commit, priority=prio, arch=arch, arm=arm, seed=seed)


def build(campaign, commit):
    if campaign == 'bridge':
        return [custom('BRIDGE_SINet_C10_s42', 'SINet', 'ours', 2, 42, 'Dataset/Source/RL5B/bridge/SINet_C10_s42',
                       'bridge', ['--save_ckpts', 'minimal', '--link_pool'], 'Tea_epoch_best.pth', 5447, 1, campaign, commit)]
    if campaign in ('e3c', 'e3e'):
        tag, pool, arm, prio = (('E3', 'Dataset/Source/RL5B/REAL4040', 'SUPREAL', 2) if campaign == 'e3c'
                                else ('E3', 'Dataset/Source/RL5B/RISEPL', 'RISEPL', 5))
        return [custom('E3_%s_%s_s%d' % (a, arm, s), a, 'source_only', 1, s, pool, tag,
                       ['--val_net', 'student', '--save_ckpts', 'minimal'], 'Stu_epoch_best.pth', 4040, prio, campaign, commit)
                for a in ('SINet', 'SINetv2') for s in (42, 43, 45)]
    if campaign in ('cdr', 'cdrv2'):
        arch, prio = ('SINet', 3) if campaign == 'cdr' else ('SINetv2', 6)
        jobs = []
        for s in (42, 43, 45):
            for arm in ['CDRLU'] + L1 + LH:
                jobs.append(abc(arch, arm, s, prio, campaign, commit))
        for s in (46, 47):
            jobs.append(abc(arch, 'CDRLU', s, prio, campaign, commit))
        return jobs
    if campaign == 'eq':
        return [abc('SINet', arm, s, 4, campaign, commit) for s in range(101, 130) for arm in ('B', 'C10', 'CSHUF')]
    raise SystemExit('unknown campaign %s' % campaign)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('campaign')
    ap.add_argument('--commit', required=True)
    a = ap.parse_args()
    data = json.load(open(JOBS)) if os.path.isfile(JOBS) else dict(jobs=[], campaigns={})
    if a.campaign in data['campaigns']:
        raise SystemExit('campaign %s already queued (append-only)' % a.campaign)
    new = build(a.campaign, a.commit)
    data['jobs'].extend(new)
    data['campaigns'][a.campaign] = dict(commit=a.commit, n_jobs=len(new))
    json.dump(data, open(JOBS, 'w'), indent=1)
    print('queued %d %s jobs at commit %s' % (len(new), a.campaign, a.commit))


if __name__ == '__main__':
    main()

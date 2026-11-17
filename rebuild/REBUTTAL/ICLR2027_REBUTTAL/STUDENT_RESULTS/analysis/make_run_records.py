"""Per-run configuration and provenance record for every RL5B job (§10 "per-run configs"; EXP step 6, "record
hardware and software for each run"). One row per job, generated from rebuild/RL5B/queue_jobs.json,
rebuild/RL5B/queue_jobs_held.json, rebuild/RL5B/out/queue_events.jsonl and each run's own log header (the exact
command line, written before launch). Writes EXPERIMENT_LOGS/run_records.csv.
Usage: python analysis/make_run_records.py
"""
import csv
import datetime as dt
import json
import os
import re

import _repo as R

RL5B = os.path.join(R.REPO, 'rebuild', 'RL5B')
KERNEL_CHANGE = dt.datetime(2026, 11, 13, 10, 31, 15)


def job_id(j):
    return j.get('id') or 'SINet%s_%s_s%d' % ('' if j['arch'] == 'SINet' else 'v2', j['arm'], j['seed'])


def log_path(j):
    if j.get('log'):
        return os.path.join(R.REPO, j['log'])
    return os.path.join(R.REPO, 'rebuild', 'ABC', job_id(j) + '.log')


def main():
    jobs = json.load(open(os.path.join(RL5B, 'queue_jobs.json')))['jobs']
    hj = json.load(open(os.path.join(RL5B, 'queue_jobs_held.json')))
    held = [dict(j, _held=k) for k, v in hj.items() if isinstance(v, list) for j in v if isinstance(j, dict)]
    ev = [json.loads(l) for l in open(os.path.join(RL5B, 'out', 'queue_events.jsonl'))]
    by = {}
    for e in ev:
        if e.get('job'):
            by.setdefault(e['job'], []).append(e)
    rows = []
    seen = {job_id(j) for j in jobs}
    for j, src in [(j, 'queue') for j in jobs] + [(j, 'held') for j in held if job_id(j) not in seen]:
        rid = job_id(j)
        es = by.get(rid, [])
        starts = [e for e in es if e.get('kind') == 'train_start']
        ok = [e for e in es if e.get('kind') == 'train_ok']
        done = any(e.get('kind') == 'job_done' for e in es)
        last = starts[-1] if starts else {}
        cmd = ''
        lp = log_path(j)
        if os.path.isfile(lp):
            m = re.search(r'^# CMD\s+(.*)$', open(lp, errors='replace').read(4000), re.M)
            cmd = m.group(1) if m else ''
        v = ok[-1]['verify'] if ok else {}
        t0 = dt.datetime.fromisoformat(last['at']) if last else None
        rows.append(dict(
            job=rid, campaign=j.get('campaign', ''), prereg_commit=j.get('commit', ''),
            status='done' if done else (('not run: %s' % j['_held']) if src == 'held' else ('not started' if not starts else 'incomplete')),
            arch=j.get('arch', ''), arm=j.get('arm', ''), seed=j.get('seed', ''),
            attempts=len(starts), discards=sum(e.get('kind') == 'discard' for e in es),
            gpu=last.get('gpu', ''), train_start=last.get('at', ''), train_ok=ok[-1]['at'] if ok else '',
            wall_min=v.get('wall_min', ''), rounds=v.get('rounds', ''), total_step=v.get('total_step_set', ''),
            last_epoch=v.get('last_epoch', ''), best_epoch=v.get('best_epoch', ''), n_appended=v.get('n_appended', ''),
            failed_checks=','.join(v.get('failed_checks') or []),
            head_at_launch=last.get('head', '')[:7], pipeline_hash=last.get('pipeline_hash', ''),
            kernel=('' if t0 is None else ('7.0.0-43' if t0 > KERNEL_CHANGE else '7.0.0-42')),
            driver='595.99.02' if t0 else '', command=cmd))
    out = os.path.join(R.LOGS, 'run_records.csv')
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print('%d jobs -> %s' % (len(rows), os.path.relpath(out, R.REPO)))
    print(Counter((r['campaign'], r['status']) for r in rows))
    print('done jobs missing a command line:', [r['job'] for r in rows if r['status'] == 'done' and not r['command']])
    print('pipeline hashes on done jobs:', sorted({r['pipeline_hash'] for r in rows if r['status'] == 'done'}))
    # Two values: runner v1 hashed every file under Src/ (and LICENSE moved there in 125cef0); runner v2 hashes only
    # Src/**/*.py. The .py training and scoring code is byte-identical at every launch commit (audit, 2026-11-17).


if __name__ == '__main__':
    main()

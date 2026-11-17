"""Parse the Stage-0 concurrency probe.

Usage: .venv/bin/python stage0_probe_parse.py <probe_out_dir>
Writes EXPERIMENT_LOGS/stage0_concurrency_probe.{log,json}.

For every probe process, steps/s is measured from MyTrain.py's '[timestamp] ... Global Step'
lines (one per 10 steps) over the window after the first 90 s (data-loader warm-up and
cuDNN autotune-free start-up) to the last logged line. Aggregate throughput of a config is the
sum over its processes. Speed-up is the aggregate relative to K = 1 (one process per GPU, the
configuration every committed campaign used).
"""
import datetime
import json
import os
import re
import sys

import _repo as R

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\].*Epoch Num: (\d+)/\d+.*Global Step: (\d+)/(\d+)')
WARMUP_S = 90


def proc_rate(log_path):
    pts = []
    for line in open(log_path):
        m = TS.match(line)
        if m:
            t = datetime.datetime.fromisoformat(m.group(1))
            ep, st, tot = int(m.group(2)), int(m.group(3)), int(m.group(4))
            pts.append((t, (ep - 1) * tot + st))
    if len(pts) < 3:
        return None
    t0 = pts[0][0]
    w = [(t, g) for t, g in pts if (t - t0).total_seconds() >= WARMUP_S]
    if len(w) < 2:
        return None
    dt = (w[-1][0] - w[0][0]).total_seconds()
    return dict(steps=w[-1][1] - w[0][1], seconds=dt, steps_per_s=(w[-1][1] - w[0][1]) / dt)


def main(out_dir):
    res = {}
    for tag in sorted(os.listdir(out_dir)):
        d = os.path.join(out_dir, tag)
        if not os.path.isdir(d):
            continue
        procs = {}
        for p in sorted(os.listdir(d)):
            lp = os.path.join(d, p, 'training_log.log')
            if os.path.isfile(lp):
                procs[p] = proc_rate(lp)
        ok = [v for v in procs.values() if v]
        res[tag] = dict(n_proc=len(procs), n_measured=len(ok),
                        per_proc_steps_per_s=[round(v['steps_per_s'], 4) for v in ok],
                        aggregate_steps_per_s=round(sum(v['steps_per_s'] for v in ok), 4),
                        pth_written=any(f.endswith('.pth') for _, _, fs in os.walk(d) for f in fs))
    lines = ['Stage-0 concurrency probe (aggregate over both GPUs; K = processes per GPU)']
    for arch in ('SINet', 'SINetv2'):
        base = res.get('%s_k1' % arch)
        for tag in sorted(t for t in res if t.startswith(arch + '_')):
            r = res[tag]
            sp = (r['aggregate_steps_per_s'] / base['aggregate_steps_per_s']) if base and base['aggregate_steps_per_s'] else float('nan')
            r['speedup_vs_k1'] = round(sp, 3)
            per = r['per_proc_steps_per_s']
            r['per_run_slowdown_vs_k1'] = round((sum(base['per_proc_steps_per_s']) / len(base['per_proc_steps_per_s']))
                                                / (sum(per) / len(per)), 3) if per and base else None
            lines.append('  %-11s procs %d (measured %d): aggregate %.3f steps/s, speed-up vs K=1 %.3fx, '
                         'each run %.2fx slower; checkpoint written: %s'
                         % (tag, r['n_proc'], r['n_measured'], r['aggregate_steps_per_s'], sp,
                            r['per_run_slowdown_vs_k1'] or float('nan'), r['pth_written']))
    txt = '\n'.join(lines) + '\n'
    os.makedirs(R.LOGS, exist_ok=True)
    open(os.path.join(R.LOGS, 'stage0_concurrency_probe.log'), 'w').write(txt)
    json.dump(res, open(os.path.join(R.LOGS, 'stage0_concurrency_probe.json'), 'w'), indent=2)
    print(txt, end='')


if __name__ == '__main__':
    main(sys.argv[1])

#!/usr/bin/env python
"""CAUS EXP-01 pilot (PREREGISTRATION_EXP01.md §4). Run by 00_pilot.sh under `timeout 30m`.

Gate-critical steps first; optional steps start only while the elapsed time leaves room, and a skip
is recorded. Every child process has its own timeout. SIGTERM (the outer timeout) stops the current
child and writes the report before exiting. Writes Result/CAUS_RUNS/00_pilot/<stamp>_<pid>/:
pilot_report.json plus every step's log and output. TRAINS NO ARM -- no pilot number is evidence.
"""

import argparse
import math
import os
import re
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caus_common as K                                        # noqa: E402
import exp01_pool as P                                         # noqa: E402
import exp01_run as R                                          # noqa: E402

LINE = re.compile(r'Epoch Num: (\d+)/\d+\] => \[Global Step: (\d+)/(\d+)\] => '
                  r'\[Loss_all: ([\d.]+) Loss_sup: ([\d.]+) Loss_con: ([\d.]+)\]')
HIST_LOG = 'Snapshot/ABC/SINet_CORACLE_s42/training_log.log'            # committed, tracked
HIST_SNAP = K.orig('Snapshot/ABC/SINet_CORACLE_s42')                     # read only
HIST_PRED = K.orig('Result/ABC/SINet_CORACLE_s42/COD10K')                # read only
T0 = time.time()
STATE = dict(proc=None, report=None, path=None)


def elapsed_min():
    return (time.time() - T0) / 60.0


def run_step(cmd, logpath, timeout_s):
    with open(logpath, 'w') as lg:
        lg.write('# CMD %s\n' % ' '.join(cmd))
        lg.flush()
        p = subprocess.Popen(cmd, cwd=K.REPO, stdout=lg, stderr=subprocess.STDOUT)
        STATE['proc'] = p
        try:
            rc = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            p.terminate()
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill()
            rc = 'timeout'
        STATE['proc'] = None
    return rc


def on_term(signum, frame):
    p = STATE['proc']
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()
    if STATE['report'] is not None:
        STATE['report']['terminated_by_signal'] = signum
        K.save_json(STATE['path'], STATE['report'])
    sys.exit(124)


def parse_log(path, epoch=1):
    out = {}
    for line in open(path):
        if line.startswith('Training Log') and out:
            break                                   # stop at the second round's header
        m = LINE.search(line)
        if m and int(m.group(1)) == epoch:
            out[int(m.group(2))] = (m.group(4), m.group(5), m.group(6), m.group(3))
    return out


def one_epoch(seed, pool, snap, gpu, logpath, timeout_s):
    cmd = [K.PY, 'MyTrain.py', '--network', 'SINet', '--task', 'S2C', '--method', 'ours',
           '--iteration', '1', '--epoch', '2', '--seed', str(seed),
           '--save_model', './' + os.path.relpath(snap, K.REPO) + '/',
           '--source_root', './' + os.path.relpath(pool, K.REPO) + '/',
           '--target_root', './Dataset/Target/', '--val_root', './Dataset/Val/CAMO/', '--gpu', str(gpu)]
    rc = run_step(cmd, logpath, timeout_s)
    tl = os.path.join(snap, 'training_log.log')
    lines = parse_log(tl) if os.path.isfile(tl) else {}
    steps = sorted(lines)
    finite = all(math.isfinite(float(v)) for t in lines.values() for v in t[:3])
    return dict(rc=rc, n_logged_steps=len(steps), last_step=steps[-1] if steps else None,
                total_step={t[3] for t in lines.values()} and sorted({t[3] for t in lines.values()}),
                finite=finite, step0=lines.get(0), cmd=' '.join(cmd)), lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gpu', type=int, default=0)
    ap.add_argument('--budget-min', type=float, default=27.0)
    args = ap.parse_args()
    run = R.new_run_dir('00_pilot')
    L = os.path.join(run, 'logs')
    rep = dict(started=K.now(), git=K.git_head(), run_dir=os.path.relpath(run, K.REPO),
               budget_min=args.budget_min, steps={})
    STATE.update(report=rep, path=os.path.join(run, 'pilot_report.json'))
    signal.signal(signal.SIGTERM, on_term)
    save = lambda: K.save_json(STATE['path'], rep)              # noqa: E731

    def done(name, d):
        d['elapsed_min_at_end'] = round(elapsed_min(), 2)
        rep['steps'][name] = d
        save()
        print('[pilot %5.1f min] %s: %s' % (elapsed_min(), name, d.get('passed')), flush=True)

    # 1 environment
    env = R.env_record(args.gpu)
    done('1_env', dict(passed=env.get('gpu_free_gb', 0) >= R.MIN_FREE_GPU_GB and env['disk_free_gb'] >= 15,
                       **env))
    # 2 pools + gates
    pools = {}
    for arm, seed in (('ORTOP10', 42), ('CORACLE', 42)):
        sub = os.path.join(run, '%s_s%d' % (arm, seed))
        os.makedirs(sub)
        pool, stems = P.build(sub, arm, seed)
        pools[arm] = pool
        g = P.gate(pool, arm, seed, stems)
        done('2_pool_%s' % arm, g)
    tg = P.trainer_gates()
    done('2_trainer_gates', tg)
    # 3 smoke
    out = os.path.join(L, 'smoke.json')
    rc = run_step([K.PY, '-B', os.path.join(K.HERE, 'exp01_smoke.py'), pools['ORTOP10'], out, '--gpu', str(args.gpu)],
                  os.path.join(L, 'smoke.log'), 180)
    sm = dict(rc=rc)
    if os.path.isfile(out):
        import json
        sm.update(json.load(open(out)))
    sm['passed'] = rc == 0 and bool(sm.get('passed'))
    done('3_smoke', sm)
    # 4 one epoch, new code path
    d4, lines4 = one_epoch(42, pools['ORTOP10'], os.path.join(run, 'ORTOP10_s42', 'snap_a'), args.gpu,
                           os.path.join(L, 'epoch1_ORTOP10_s42_a.log'), 330)
    d4['passed'] = d4['rc'] == 0 and d4['finite'] and d4['total_step'] == ['0253'] and d4['last_step'] == 250
    done('4_epoch1_ORTOP10', d4)
    # 5 R6 replay of the committed CORACLE_s42 configuration
    d5, lines5 = one_epoch(42, pools['CORACLE'], os.path.join(run, 'CORACLE_s42', 'snap'), args.gpu,
                           os.path.join(L, 'epoch1_CORACLE_s42_replay.log'), 330)
    hist = parse_log(os.path.join(K.REPO, HIST_LOG))
    common = sorted(set(hist) & set(lines5))
    diffs = [max(abs(float(a) - float(b)) for a, b in zip(hist[s][:3], lines5[s][:3])) for s in common]
    d5.update(hist_step0=hist.get(0), step0_equal_4dp=bool(hist.get(0) and lines5.get(0)
                                                           and hist[0][:3] == lines5[0][:3]),
              n_steps_compared=len(common), n_steps_identical=sum(hist[s][:3] == lines5[s][:3] for s in common),
              max_abs_loss_diff=max(diffs) if diffs else None,
              first_divergent_step=next((s for s in common if hist[s][:3] != lines5[s][:3]), None))
    d5['passed'] = d5['rc'] == 0 and d5['step0_equal_4dp']
    done('5_R6_replay_CORACLE_s42', d5)
    # 6 inference parity on the historical checkpoint
    po = os.path.join(run, 'pred_hist_CORACLE_s42', 'COD10K')
    irc, n, n_gt = R.infer(os.path.join(HIST_SNAP, 'Tea_epoch_best.pth'), po, 'COD10K', args.gpu,
                           os.path.join(L, 'infer_hist_CORACLE_s42_COD10K.log'), timeout=300)
    same = 0
    if os.path.isdir(po):
        for nm in os.listdir(po):
            hp = os.path.join(HIST_PRED, nm)
            if os.path.isfile(hp) and K.sha256(hp) == K.sha256(os.path.join(po, nm)):
                same += 1
    done('6_infer_parity', dict(rc=irc, n=n, n_gt=n_gt, png_byte_identical=same,
                                passed=irc == 0 and n == n_gt,
                                note='Sa re-scored on CPU after the pilot against committed 0.712710'))
    # 7 optional CLS smoke
    if elapsed_min() <= args.budget_min - 10:
        out = os.path.join(L, 'cls_smoke.json')
        rc = run_step([K.PY, '-B', os.path.join(K.HERE, 'exp01_cls_smoke.py'), pools['CORACLE'], HIST_SNAP, out,
                       '--gpu', str(args.gpu)], os.path.join(L, 'cls_smoke.log'), 480)
        d7 = dict(rc=rc)
        if os.path.isfile(out):
            import json
            d7.update(json.load(open(out)))
        d7['passed'] = rc == 0 and bool(d7.get('passed'))
        done('7_cls_smoke', d7)
    else:
        done('7_cls_smoke', dict(passed=None, skipped='elapsed %.1f min left no room' % elapsed_min()))
    # 8 optional rerun-from-scratch determinism repeat of step 4
    if elapsed_min() <= args.budget_min - 5.5:
        d8, lines8 = one_epoch(42, pools['ORTOP10'], os.path.join(run, 'ORTOP10_s42', 'snap_b'), args.gpu,
                               os.path.join(L, 'epoch1_ORTOP10_s42_b.log'), 330)
        common = sorted(set(lines4) & set(lines8))
        d8.update(n_steps_compared=len(common),
                  n_steps_identical=sum(lines4[s][:3] == lines8[s][:3] for s in common),
                  first_divergent_step=next((s for s in common if lines4[s][:3] != lines8[s][:3]), None))
        d8['passed'] = d8['rc'] == 0 and d8['finite']
        done('8_determinism_repeat', d8)
    else:
        done('8_determinism_repeat', dict(passed=None, skipped='elapsed %.1f min left no room' % elapsed_min()))

    crit = ['1_env', '2_pool_ORTOP10', '2_pool_CORACLE', '2_trainer_gates', '3_smoke', '4_epoch1_ORTOP10',
            '5_R6_replay_CORACLE_s42', '6_infer_parity']
    rep['gate_critical_passed'] = all(rep['steps'][k].get('passed') for k in crit)
    rep['ended'] = K.now()
    rep['elapsed_min'] = round(elapsed_min(), 2)
    save()
    print('PILOT gate-critical passed: %s (%.1f min)' % (rep['gate_critical_passed'], elapsed_min()))
    sys.exit(0 if rep['gate_critical_passed'] else 1)


if __name__ == '__main__':
    main()

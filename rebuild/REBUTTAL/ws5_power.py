#!/usr/bin/env python
"""REBUTTAL WS5' -- seeds per arm for the three-arm equivalence extension, from
power and the deadline. Run BEFORE PREREGISTRATION_WS5.md is written, which takes n
from this block.

Design being sized (REBUTTAL_PLAN.md Addendum 1, A2): arms B, C10, CSHUF; SINet;
fresh seeds 51, 52, ...; primary endpoint COD10K-test S_alpha; Welch TOST at
delta = 0.005, alpha = 0.05. Three contrasts with fixed roles:
  C10 - B      total targeting effect
  C10 - CSHUF  direction effect, same shape
  CSHUF - B    concentration effect, same budget, no aim

POWER is simulated (DRAWS draws, fixed rng) with each arm drawn N(mean, sd), where
mean and sd are the SE campaign's eight-seed values on that cell, so every contrast
is simulated at its OBSERVED difference. The three arms are drawn jointly per
draw, so the probability that all three contrasts conclude equivalence is reported
as well. This is a planning calculation on committed data. It decides nothing and
re-decides no SE verdict.

DEADLINE: n is the largest value with every run trained, verified and scored by
DEADLINE, given LAUNCH, one run per GPU on two GPUs, the SE campaign's measured
SINet wall-clock, and a BUFFER (10%) for interruption and scoring:
    ceil(3n / 2) * wall_min * (1 + BUFFER) <= DEADLINE - LAUNCH

Trains nothing. Reads rebuild/ABC/out/se/abc_metrics.csv and abc_runs.csv.

Usage:
  .venv/bin/python rebuild/REBUTTAL/ws5_power.py [--no-log]
"""

import argparse
import csv
import datetime
import math
import os
import sys

import numpy as np
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import common as C                                            # noqa: E402

OUT = os.path.join(_HERE, 'out')
SE = os.path.join(C.REPO, 'rebuild/ABC/out/se')
ARMS = ('B', 'C10', 'CSHUF')
CONTRASTS = (('C10', 'B', 'total targeting effect'),
             ('C10', 'CSHUF', 'direction effect, same shape'),
             ('CSHUF', 'B', 'concentration effect, same budget, no aim'))
DELTA, ALPHA = 0.005, 0.05
DRAWS = 4000
RNG = 20261107
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
LAUNCH = datetime.datetime(2026, 11, 10, 6, 0, tzinfo=IST)
DEADLINE = datetime.datetime(2026, 11, 14, 12, 0, tzinfo=IST)
BUFFER = 0.10
GPUS = 2
N_GRID = (8, 16, 24, 32)


def load_cell(arch, endpoint):
    x = {}
    with open(os.path.join(SE, 'abc_metrics.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            if r['arch'] == arch and r['endpoint'] == endpoint and r['arm'] in ARMS:
                x.setdefault(r['arm'], []).append(float(r['Sm']))
    for a in ARMS:
        if len(x.get(a, [])) != 8:
            raise RuntimeError('HALT: %s %s arm %s has %d SE runs, expected 8'
                               % (arch, endpoint, a, len(x.get(a, []))))
    return {a: (float(np.mean(v)), float(np.std(v, ddof=1))) for a, v in x.items()}


def sinet_wall():
    w = []
    with open(os.path.join(SE, 'abc_runs.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            if r['arch'] == 'SINet' and int(r['seed']) >= 46:     # SE's own new runs
                w.append(float(r['wall_min']))
    if len(w) != 20:
        raise RuntimeError('HALT: expected 20 SE-new SINet runs, found %d' % len(w))
    return float(np.mean(w)), len(w)


def tost_pass(a, b):
    """Welch TOST at DELTA, alpha: the 90% CI lies inside (-DELTA, +DELTA).
    Vectorised over the leading axis (draws)."""
    na, nb = a.shape[1], b.shape[1]
    va, vb = a.var(axis=1, ddof=1), b.var(axis=1, ddof=1)
    se = np.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = a.mean(axis=1) - b.mean(axis=1)
    return np.abs(d) + stats.t.ppf(1 - ALPHA, df) * se < DELTA


def power(cell, n, rng):
    draw = {a: rng.normal(cell[a][0], cell[a][1], size=(DRAWS, n)) for a in ARMS}
    passes = {(hi, lo): tost_pass(draw[hi], draw[lo]) for hi, lo, _ in CONTRASTS}
    joint = np.logical_and.reduce(list(passes.values()))
    return {k: float(v.mean()) for k, v in passes.items()}, float(joint.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(RNG)

    wall, n_wall = sinet_wall()
    window_min = (DEADLINE - LAUNCH).total_seconds() / 60.0
    n = 0
    while math.ceil(3 * (n + 1) / GPUS) * wall * (1 + BUFFER) <= window_min:
        n += 1
    batches = math.ceil(3 * n / GPUS)
    end = LAUNCH + datetime.timedelta(minutes=batches * wall * (1 + BUFFER))
    end_raw = LAUNCH + datetime.timedelta(minutes=batches * wall)

    M = [('sinet_wall_min_measured', '%.1f' % wall, 'mean of %d SE-new SINet runs, abc_runs.csv' % n_wall),
         ('launch', LAUNCH.isoformat(), 'hard gate, REBUTTAL_PLAN.md Addendum 1 A2'),
         ('deadline_trained_verified_scored', DEADLINE.isoformat(), ''),
         ('window_min', '%.0f' % window_min, ''),
         ('buffer', '%.0f%%' % (100 * BUFFER), 'interruption + scoring'),
         ('n_per_arm_chosen', n, 'largest n with ceil(3n/%d)*wall*(1+buffer) <= window' % GPUS),
         ('runs_total', 3 * n, '3 arms x n, SINet only'),
         ('gpu_batches', batches, '%d GPUs, one run per GPU' % GPUS),
         ('end_with_buffer', end.isoformat(timespec='minutes'), ''),
         ('end_without_buffer', end_raw.isoformat(timespec='minutes'), ''),
         ('n_plus_1_end_with_buffer',
          (LAUNCH + datetime.timedelta(minutes=math.ceil(3 * (n + 1) / GPUS) * wall * (1 + BUFFER))).isoformat(timespec='minutes'),
          'misses the deadline, so n+1 is infeasible'),
         ('seeds', '%d..%d' % (51, 50 + n), 'fresh, disjoint from every committed campaign')]

    rows = []
    for endpoint in ('COD10K', 'NC4K'):
        cell = load_cell('SINet', endpoint)
        for a in ARMS:
            M.append(('SE8_%s_%s_mean_sd' % (endpoint, a), '%.6f / %.6f' % cell[a], 'simulation input'))
        for hi, lo, role in CONTRASTS:
            M.append(('observed_%s_%s-%s' % (endpoint, hi, lo), '%+.4f' % (cell[hi][0] - cell[lo][0]), role))
        for nn in sorted(set(N_GRID) | {n}):
            pw, joint = power(cell, nn, rng)
            for hi, lo, role in CONTRASTS:
                rows.append(dict(endpoint=endpoint, n=nn, contrast='%s-%s' % (hi, lo), role=role,
                                 observed=round(cell[hi][0] - cell[lo][0], 6), power=round(pw[(hi, lo)], 4)))
            rows.append(dict(endpoint=endpoint, n=nn, contrast='all three', role='joint',
                             observed='', power=round(joint, 4)))
            tag = '%s_n%d' % (endpoint, nn)
            M.append(('power_%s' % tag,
                      '  '.join('%s-%s %.2f' % (hi, lo, pw[(hi, lo)]) for hi, lo, _ in CONTRASTS)
                      + '  | all-three %.2f' % joint,
                      'Welch TOST delta=%.3f alpha=%.2f, %d draws, at observed differences%s'
                      % (DELTA, ALPHA, DRAWS, ' -- CHOSEN n' if nn == n else '')))

    path = os.path.join(OUT, 'ws5_power.csv')
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    T = [('n >= 24 (the floor below which the plan recommends against running)', n >= 24),
         ('end_with_buffer <= deadline', end <= DEADLINE)]
    notes = ('PLANNING CALCULATION ON COMMITTED DATA. Sizes the standalone WS5\' campaign. Decides nothing, re-decides no SE verdict, and pools nothing with SE: the SE spreads enter only as simulation inputs.\n'
             'Power is simulated at the OBSERVED eight-seed differences, which is the pessimistic case for C10-B and CSHUF-B. At a true difference of 0, power is higher.\n'
             'Independent-normal arms are an ASSUMPTION. Arm B carries draw variance by construction and the simulation inherits it through B\'s observed sd. The within-seed correlation, which the ad hoc audit measured near 0 on this cell, is ignored, matching the Welch (unpaired) primary test.\n'
             'Wall-clock assumes WS6/WS4 have released both GPUs by the launch time, and that each run takes the SE mean. A run that fails verify_run and is re-run consumes buffer.')
    print(C.log_block('REBUTTAL_WS5_POWER', '.venv/bin/python rebuild/REBUTTAL/ws5_power.py', M,
                      thresholds=T, artifacts=[os.path.relpath(path, C.REPO)], notes=notes,
                      write=not args.no_log))


if __name__ == '__main__':
    main()

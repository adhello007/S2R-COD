#!/usr/bin/env python
"""ABC -- evaluate every run, apply the FROZEN rule, and write EXP ABC block #3.

Decision rule: rebuild/ABC/PREREGISTRATION.md, committed before block #1 and
FROZEN. This script READS it only to echo it; it never writes it, and it contains
no tunable threshold of its own.

Metrics come from the repo's Eval/metrics.py, scored from the PNGs MyTest.py
wrote, at 6 decimal places (ABC_PLAN.md A.10). Before scoring any new run the
scorer is validated against B1's committed Sa = 0.717216 and MAE = 0.074463 on
the committed Result/SINet/S2C predictions -- so the eval path is proved faithful
before it produces a number.

Framing constraint (ABC_PLAN.md A.12 item 7): C1's audit measured the ES signal's
own contribution at ~0.6% of d. This campaign therefore tests whether a
CONCENTRATED, more-proximal, lower-effective-rank arm trains better than a
dispersed one. No result here is evidence about the uncertainty signal.

Usage:
  .venv/bin/python rebuild/ABC/abc_evaluate.py [--skip-infer] [--no-log]
"""

import argparse
import csv
import itertools
import math
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(_HERE), _HERE, os.path.dirname(os.path.dirname(_HERE)),
           os.path.join(os.path.dirname(os.path.dirname(_HERE)), 'Eval')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import abc_common as A                                        # noqa: E402

EXP = A.EXP
OUT = A.OUT
PY = '.venv/bin/python'
B1_SA, B1_MAE, TOL = 0.717216, 0.074463, 1e-5
REF_SA, GATE = 0.7172, 0.0107          # committed SINet/S2C; 3*sigma_prior
METRIC_KEYS = ('Sm', 'wFm', 'MAE', 'adpEm', 'meanEm', 'maxEm', 'adpFm', 'meanFm', 'maxFm')
# The frozen gap sets. 'abc' is PREREGISTRATION.md and stays the default so a
# bare re-run of A/B/C is bit-identical; 't2' is PREREGISTRATION_T2.md, additive.
GAPS = {'abc': (('A2', 'B'), ('B', 'C10'), ('A0', 'B'), ('A0', 'C10'), ('A0', 'A2')),
        't2':  (('CSHUF', 'C10'), ('CINV', 'C10'), ('CINV', 'CSHUF'))}
# What T2 cross-checks. C1 measured these in embedding-distance space only.
OLD_CLAIMS_T2 = [
    ('C1.4 ES contribution vs its own shuffle',
     '+0.0073 of d, 13/20 cells  [C1_RESULTS 8.2]',
     'CROSS-CHECKED on TRAINED ACCURACY for the first time'),
    ('C1.5 top-ES cluster vs an arbitrary cluster',
     '-0.0649 of d, worse in 16/20 cells  [C1_RESULTS 8.2]',
     'CROSS-CHECKED on TRAINED ACCURACY'),
    ('paper 6(v) the ES signal is uninformative',
     'asserted on embedding geometry alone',
     'TESTED on accuracy, in both directions'),
]


def _p(m):
    print(m, flush=True)


def score(gt_dir, pred_dir):
    import cv2
    import torch
    import metrics as Measure
    FM, WFM, SM, EM, MAE = (Measure.Fmeasure(), Measure.WeightedFmeasure(),
                            Measure.Smeasure(), Measure.Emeasure(), Measure.MAE())
    names = sorted(os.listdir(gt_dir))
    nshape = 0
    with torch.no_grad():
        for nm in names:
            gp, pp = os.path.join(gt_dir, nm), os.path.join(pred_dir, nm)
            assert os.path.isfile(pp), 'missing prediction %s' % pp
            pred = cv2.imread(pp, cv2.IMREAD_GRAYSCALE)
            gt = cv2.imread(gp, cv2.IMREAD_GRAYSCALE)
            if pred.shape != gt.shape:
                nshape += 1
                pred = cv2.resize(pred, (gt.shape[1], gt.shape[0]),
                                  interpolation=cv2.INTER_NEAREST)
            for m in (FM, WFM, SM, EM, MAE):
                m.step(pred=pred, gt=gt)
    fm, wfm = FM.get_results()['fm'], WFM.get_results()['wfm']
    sm, em, mae = SM.get_results()['sm'], EM.get_results()['em'], MAE.get_results()['mae']
    return dict(n=len(names), shape_mismatch=nshape, Sm=float(sm), wFm=float(wfm),
                MAE=float(mae), adpEm=float(em['adp']),
                meanEm=float(em['curve'].mean()), maxEm=float(em['curve'].max()),
                adpFm=float(fm['adp']), meanFm=float(fm['curve'].mean()),
                maxFm=float(fm['curve'].max()))


def infer_needed(arch, arm, seed, endpoint):
    rid = A.runid(arch, arm, seed)
    out = os.path.join(C.REPO, A.pred_dir(rid, endpoint))
    gtn = len(os.listdir(os.path.join(C.REPO, 'Dataset/Test/%s/GT' % endpoint)))
    return not (os.path.isdir(out) and len(os.listdir(out)) == gtn)


def infer_start(arch, arm, seed, endpoint, gpu):
    """Launch one MyTest.py. MyTest.py:41-43 asserts every checkpoint tensor was
    copied, so a partially loaded network cannot silently produce predictions."""
    rid = A.runid(arch, arm, seed)
    ck = './' + os.path.join(A.snap_dir(rid), 'Tea_epoch_best.pth')
    cmd = [PY, 'MyTest.py', '--network', A.ARCHS[arch]['network'], '--gpu', str(gpu),
           '--dataset', endpoint, '--model_path', ck,
           '--test_save', './' + A.pred_dir(rid, endpoint)]
    lg = open(os.path.join(C.REPO, 'rebuild/ABC/infer_%s_%s.log' % (rid, endpoint)), 'w')
    return subprocess.Popen(cmd, cwd=C.REPO, stdout=lg, stderr=subprocess.STDOUT), lg


def score_task(t):
    """Pool worker. Pure function of two directories."""
    gt, pred = t['gt'], t['pred']
    return t['key'], score(gt, pred)


def sd(xs):
    n = len(xs)
    if n < 2:
        return float('nan')
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def mean(xs):
    return sum(xs) / len(xs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', default=','.join(A.ARMS))
    ap.add_argument('--skip-infer', action='store_true')
    ap.add_argument('--workers', type=int, default=1,
                    help='parallel SCORING processes. Scoring is a pure function of '
                         'two directories, so this changes throughput and no number.')
    ap.add_argument('--gpus', default='0', help='comma list for inference')
    ap.add_argument('--no-log', action='store_true')
    ap.add_argument('--gaps', default='abc', choices=sorted(GAPS),
                    help='which FROZEN gap set to apply; "t2" is '
                         'PREREGISTRATION_T2.md, additive')
    ap.add_argument('--tag', default='', help='output namespace; "t2" is additive')
    args = ap.parse_args()
    arms = tuple(a.strip() for a in args.arms.split(',') if a.strip())
    global OUT, EXP
    OUT = A.set_out(args.tag)
    EXP = 'T2' if args.tag == 't2' else A.EXP
    os.makedirs(OUT, exist_ok=True)

    _p('=== s1 scorer validation against B1\'s committed values ===')
    v = score(os.path.join(C.REPO, 'Dataset/Test/COD10K/GT'),
              os.path.join(C.REPO, 'Result/SINet/S2C'))
    dsa, dmae = abs(v['Sm'] - B1_SA), abs(v['MAE'] - B1_MAE)
    _p('  Sa  %.6f (B1 %.6f, delta %.2e)   MAE %.6f (B1 %.6f, delta %.2e)'
       % (v['Sm'], B1_SA, dsa, v['MAE'], B1_MAE, dmae))
    scorer_ok = bool(dsa < TOL and dmae < TOL)
    if not scorer_ok:
        raise SystemExit('ABC HALTED: scorer does not reproduce B1\'s committed values')
    _p('  scorer PASS -- cleared to score new runs')

    _p('=== s2 inference ===')
    gpus = [int(g) for g in args.gpus.split(',') if g.strip() != '']
    tasks = []
    for arch in ('SINet', 'SINetv2'):
        for arm in arms:
            for seed in A.SEEDS:
                rid = A.runid(arch, arm, seed)
                if not os.path.isfile(os.path.join(C.REPO, A.snap_dir(rid),
                                                   'Tea_epoch_best.pth')):
                    _p('  %-22s SKIP (no Tea_epoch_best.pth)' % rid)
                    continue
                for ep in A.ENDPOINTS:
                    tasks.append(dict(key=(rid, arch, arm, seed, ep),
                                      gt=os.path.join(C.REPO, 'Dataset/Test/%s/GT' % ep),
                                      pred=os.path.join(C.REPO, A.pred_dir(rid, ep))))
    todo = [t for t in tasks if not args.skip_infer
            and infer_needed(t['key'][1], t['key'][2], t['key'][3], t['key'][4])]
    cached = len(tasks) - len(todo)
    _p('  %d prediction sets: %d cached, %d to run on gpus %s'
       % (len(tasks), cached, len(todo), gpus))
    q, running = list(todo), {}
    while q or running:
        for g in gpus:
            if g not in running and q:
                t = q.pop(0)
                rid, arch, arm, seed, ep = t['key']
                running[g] = (infer_start(arch, arm, seed, ep, g), rid, ep)
                _p('    infer %-22s %-7s gpu %d' % (rid, ep, g))
        if not running:
            break
        time.sleep(5)
        for g in list(running):
            (proc, lg), rid, ep = running[g][0], running[g][1], running[g][2]
            if proc.poll() is None:
                continue
            lg.close()
            del running[g]
            if proc.returncode != 0:
                raise SystemExit('ABC HALTED: inference failed for %s %s (rc=%d)'
                                 % (rid, ep, proc.returncode))
    for t in tasks:
        rid, arch, arm, seed, ep = t['key']
        n = len(os.listdir(t['pred']))
        exp = len(os.listdir(t['gt']))
        if n != exp:
            raise SystemExit('ABC HALTED: %s %s has %d predictions, expected %d'
                             % (rid, ep, n, exp))

    _p('=== s2b scoring (%d workers) ===' % args.workers)
    if args.workers > 1:
        import multiprocessing as mp
        with mp.Pool(args.workers) as pool:
            scored = pool.map(score_task, tasks)
    else:
        scored = [score_task(t) for t in tasks]
    rows = []
    for (rid, arch, arm, seed, ep), r in scored:
        rows.append(dict(runid=rid, arch=arch, arm=arm, seed=seed, endpoint=ep,
                         infer='skipped' if args.skip_infer else 'done', **r))
        _p('  %-22s %-7s Sa=%.6f MAE=%.6f wFm=%.6f meanEm=%.6f'
           % (rid, ep, r['Sm'], r['MAE'], r['wFm'], r['meanEm']))

    with open(os.path.join(OUT, 'abc_metrics.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['runid', 'arch', 'arm', 'seed', 'endpoint',
                                           'n', 'shape_mismatch', 'infer'] + list(METRIC_KEYS))
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x['endpoint'], x['runid'])):
            w.writerow({k: ('%.6f' % r[k] if k in METRIC_KEYS else r[k])
                        for k in w.fieldnames})

    # T2 re-scores the COMMITTED B and C10 predictions to build the sigma_hat
    # pool through this same code path. They must reproduce abc_metrics.csv or
    # something drifted between the campaigns.
    ref = os.path.join(C.exp_dir(A.EXP, 'out'), 'abc_metrics.csv')   # A/B/C's own path
    if args.tag and os.path.isfile(ref):
        # abc_metrics.csv records Sa at 6 dp (PREREGISTRATION.md 2.4), so the
        # comparison is made at THAT precision: exact equality of the recorded
        # values. The raw-float-vs-rounded-string test at 1e-9 that T2.1
        # literally specifies cannot be satisfied by ANY correct computation --
        # 6-dp rounding alone admits up to 5e-7. Exact equality at the recorded
        # precision is STRICTER than a 1e-6 tolerance, not looser.
        # See PREREGISTRATION_T2.md addendum A1 (2026-09-11).
        ref_sa = {(r['runid'], r['endpoint']): r['Sm']
                  for r in csv.DictReader(open(ref))}
        shared = [r for r in rows if (r['runid'], r['endpoint']) in ref_sa]
        bad = [(r['runid'], r['endpoint'], '%.6f' % r['Sm'],
                ref_sa[(r['runid'], r['endpoint'])]) for r in shared
               if '%.6f' % r['Sm'] != '%.6f' % float(ref_sa[(r['runid'], r['endpoint'])])]
        if bad:
            raise SystemExit('T2 HALTED: reference arms do not reproduce '
                             'abc_metrics.csv at 6 dp: %s' % bad[:5])
        _p('  reference arms reproduce abc_metrics.csv EXACTLY at the recorded '
           '6 dp: %d/%d cells' % (len(shared) - len(bad), len(shared)))

    _p('=== s3 sigma_hat and the gaps, per the FROZEN rule ===')
    verdicts = {}
    for arch in ('SINet', 'SINetv2'):
        for ep in A.ENDPOINTS:
            sub = [r for r in rows if r['arch'] == arch and r['endpoint'] == ep]
            byarm = {m: {r['seed']: r['Sm'] for r in sub if r['arm'] == m} for m in arms}
            byarm = {m: d for m, d in byarm.items() if d}
            if not byarm:
                continue
            # pooled within-arm sd of Sa across ALL arms (PREREGISTRATION 2.2)
            ss, df = 0.0, 0
            per_arm_sd = {}
            for m, d in byarm.items():
                xs = list(d.values())
                if len(xs) < 2:
                    continue
                mu = mean(xs)
                ss += sum((x - mu) ** 2 for x in xs)
                df += len(xs) - 1
                per_arm_sd[m] = sd(xs)
            sigma = math.sqrt(ss / df) if df else float('nan')
            gaps = {}
            for lo, hi in GAPS[args.gaps]:
                if lo not in byarm or hi not in byarm:
                    continue
                seeds = sorted(set(byarm[lo]) & set(byarm[hi]))
                if not seeds:
                    continue
                delta = mean([byarm[hi][s] for s in seeds]) - mean([byarm[lo][s] for s in seeds])
                paired = {s: byarm[hi][s] - byarm[lo][s] for s in seeds}
                sgn = 1 if delta > 0 else (-1 if delta < 0 else 0)
                consistent = sum(1 for s in seeds
                                 if (paired[s] > 0) == (delta > 0) and paired[s] != 0)
                if abs(delta) <= 2 * sigma:
                    verdict = 'WITHIN NOISE'
                elif delta > 2 * sigma and consistent == len(seeds):
                    verdict = 'REAL EFFECT'
                elif delta < -2 * sigma and consistent == len(seeds):
                    verdict = 'REAL REGRESSION'
                else:
                    verdict = 'INCONCLUSIVE'
                gaps['%s->%s' % (lo, hi)] = dict(
                    delta=delta, paired={str(s): paired[s] for s in seeds},
                    sign_consistent='%d/%d' % (consistent, len(seeds)),
                    verdict=verdict, n_seeds=len(seeds))
            verdicts['%s|%s' % (arch, ep)] = dict(
                sigma_hat=sigma, df=df, per_arm_sd=per_arm_sd,
                arm_means={m: mean(list(d.values())) for m, d in byarm.items()},
                arm_n={m: len(d) for m, d in byarm.items()}, gaps=gaps)
            _p('  %s %s: sigma_hat=%.6f (df=%d)  2sigma=%.6f' % (arch, ep, sigma, df, 2 * sigma))
            for g, d in gaps.items():
                _p('     %-10s delta=%+.6f  sign %s  -> %s'
                   % (g, d['delta'], d['sign_consistent'], d['verdict']))
    C.save_json(os.path.join(OUT, 'abc_verdict.json'),
                dict(generated=C.now(), commit=C.git_commit(),
                     rule='rebuild/ABC/PREREGISTRATION.md (frozen)',
                     scorer_validation=dict(Sm=v['Sm'], MAE=v['MAE'], passed=scorer_ok),
                     verdicts=verdicts))
    C.save_json(os.path.join(OUT, 'abc_sigma.json'),
                {k: dict(sigma_hat=x['sigma_hat'], df=x['df'], per_arm_sd=x['per_arm_sd'])
                 for k, x in verdicts.items()})

    _p('=== s4 log block ===')
    metrics, thresholds, artifacts, notes = [], [], [], []
    metrics.append(('scorer_reproduces_B1',
                    'Sa %.6f (delta %.2e), MAE %.6f (delta %.2e)'
                    % (v['Sm'], dsa, v['MAE'], dmae),
                    'validated on the COMMITTED Result/SINet/S2C BEFORE scoring any '
                    'new run; B1 logged 0.717216 / 0.074463'))
    thresholds.append(('the eval path reproduces B1\'s committed Sa and MAE to <1e-5 '
                       'before producing any new number', scorer_ok))
    metrics.append(('runs_scored', len({r['runid'] for r in rows})))
    metrics.append(('endpoint_shape_mismatches', sum(r['shape_mismatch'] for r in rows),
                    'pred.shape == gt.shape asserted for every image of every run'))
    for r in sorted(rows, key=lambda x: (x['endpoint'], x['runid'])):
        metrics.append(('%s_%s' % (r['runid'], r['endpoint']),
                        'Sa %.6f  MAE %.6f  Fbw %.6f  meanEm %.6f'
                        % (r['Sm'], r['MAE'], r['wFm'], r['meanEm']),
                        'n=%d  adpEm %.6f  maxEm %.6f' % (r['n'], r['adpEm'], r['maxEm'])))
    for key, x in verdicts.items():
        metrics.append(('sigma_hat_%s' % key,
                        '%.6f  (2*sigma_hat = %.6f, df=%d)'
                        % (x['sigma_hat'], 2 * x['sigma_hat'], x['df']),
                        'pooled within-arm sd of Sa across arms %s'
                        % ','.join(sorted(x['arm_n']))))
        metrics.append(('per_arm_sd_%s' % key,
                        '  '.join('%s %.6f' % (m, s) for m, s in sorted(x['per_arm_sd'].items())),
                        'arm B carries selection variance A0 and C do not '
                        '(ABC_PLAN.md A.4) -- pooled sigma_hat is inflated by it'))
        metrics.append(('arm_means_Sa_%s' % key,
                        '  '.join('%s %.6f (n=%d)' % (m, x['arm_means'][m], x['arm_n'][m])
                                  for m in sorted(x['arm_means']))))
        for g, d in x['gaps'].items():
            metrics.append(('DELTA_%s_%s' % (g, key),
                            '%+.6f  sign %s  -> %s' % (d['delta'], d['sign_consistent'],
                                                       d['verdict']),
                            'paired per seed: '
                            + '  '.join('s%s %+.6f' % (s, dv)
                                        for s, dv in sorted(d['paired'].items()))))
    prim = verdicts.get('SINet|COD10K')
    sec = verdicts.get('SINetv2|COD10K')
    if prim and sec:
        agree = {g: (prim['gaps'][g]['verdict'] == sec['gaps'][g]['verdict'])
                 for g in prim['gaps'] if g in sec['gaps']}
        metrics.append(('architectures_agree_on_verdict',
                        '  '.join('%s %s' % (g, 'YES' if a else 'NO')
                                  for g, a in sorted(agree.items())),
                        'a null on one architecture is weaker than a null on both'))
        thresholds.append(('SINet and SINet-v2 return the same verdict for every gap '
                           'on the primary endpoint', all(agree.values())))
    if prim:
        need = (('CSHUF->C10', 'CINV->C10') if args.gaps == 't2' else ('B->C10',))
        thresholds.append((
            'the primary claim%s decided by the frozen rule, whatever the answer'
            % (' Delta(C10-CSHUF) and Delta(C10-CINV) are' if args.gaps == 't2'
               else ' Delta(C-B) is'),
            all(g in prim['gaps'] for g in need)))
    relout = os.path.relpath(OUT, C.REPO)
    artifacts += [os.path.join(relout, f) for f in
                  ('abc_metrics.csv', 'abc_verdict.json', 'abc_sigma.json')]
    notes.append(
        'BLOCK 3 OF 3 -- THE VERDICT. Applied strictly by rebuild/ABC/'
        'PREREGISTRATION.md, committed before block #1 and unchanged since. '
        'sigma_hat is the pooled within-arm sd of Sa MEASURED FROM THESE RUNS. The '
        'archived 0.003555 (n=6) and 0.002287 (same seed, n=3) were expected scale '
        'only, never the bar, and were measured at a different operating point '
        '(--iteration 1, Sa ~0.699 against this campaign\'s ~0.715).')
    notes.append(
        'WHAT THIS CAMPAIGN TESTS, AND WHAT IT DOES NOT. C1\'s attribution audit '
        'measured the ES signal\'s own contribution as +0.0073 of d against its own '
        'shuffle (13/20 -- a coin flip) and -0.0649 against an arbitrary cluster '
        '(4/20, i.e. targeting the highest-signal cluster is WORSE than picking one '
        'at random). Arm C differs from arm B by CONCENTRATION: effective rank ratio '
        '0.53-0.64, mean top-1 similarity to the target manifold up to +0.096, '
        'target coverage delta ~0. So Delta(C-B) answers whether a concentrated, '
        'more-proximal, lower-effective-rank training set beats a dispersed one. It '
        'is NOT evidence about the uncertainty signal, and must not be reported as '
        'such whichever way it lands.')
    notes.append(
        'NO p-VALUE AT n=3, and no optional stopping. The rule reports 2*sigma_hat, '
        'the paired per-seed differences and the sign-consistency count. Seeds are '
        'NOT added to break an INCONCLUSIVE -- PREREGISTRATION.md 1 says so in those '
        'words. With n=3 the t-critical value at 95% is 2.92, so 2*sigma_hat is LESS '
        'conservative than a formal test; that is disclosed rather than dressed up.')
    notes.append(
        'PER-ARM sd IS REPORTED BESIDE THE POOLED VALUE. Pooling assumes equal '
        'within-arm variance, and arm B violates it by construction: its draw varies '
        'per seed, so it carries selection variance arms A0 and C do not. That '
        'inflates sigma_hat and makes the bar HARDER, which is the conservative '
        'direction. If sd(B) exceeds 2x sd(C) that is itself a finding -- random '
        'allocation has materially higher selection variance than targeted -- and '
        'the Delta(C-B) reading is caveated accordingly.')
    notes.append(
        'A0 IS NOT A CLEAN CONTROL and the Delta values against it are for '
        'paper-comparability only. total_step is pinned at 253/127, so A0 gives each '
        'base image 22% more exposure per epoch than A2/B/C. A2 is the clean control. '
        'Delta(B-A2) additionally carries the 0.00575 mask-tightness asymmetry on '
        '18.4% of the pool (block #1). Only Delta(C-B) is free of both.')
    notes.append(
        'ENDPOINTS. COD10K-test is primary (2/2026 = 0.1% near-duplicate '
        'contamination, 7 exact with a measured MAE impact of -1.24e-05). NC4K is '
        'secondary and REPORTED ONLY -- it never decides. CHAMELEON is withdrawn '
        '(41/76 = 53.9% of it is training data) and CAMO is the checkpoint-selection '
        'set, never an endpoint; both are unreachable in code and re-checked by gate '
        'G4. Any null inherits D1\'s scope: it is evidence about targeting under an '
        'EXHAUSTED FOREGROUND POOL, and is silent on whether new foregrounds would '
        'help.')

    if args.gaps == 't2':
        notes = []
        notes.append(
            'BLOCK 3 OF 3 OF THE T2 EXTENSION -- THE VERDICT. Applied strictly by '
            'rebuild/ABC/PREREGISTRATION_T2.md, committed before T2 block #1 and '
            'unchanged since. ADDITIVE: rebuild/ABC/PREREGISTRATION.md and every '
            'committed A/B/C number are untouched by this block, which writes only '
            'under rebuild/ABC/out/t2/.')
        notes.append(
            'SIGMA_HAT IS MEASURED FROM THE T2 COMPARISON SET -- arms '
            '{B, C10, CSHUF, CINV}, df = 4 x 2 = 8 -- so the bar is estimated on the '
            'runs the gaps are actually taken between, not inherited from A/B/C. If '
            'it comes out larger than A/B/C\'s, the bar rises with it: the bar is '
            '2*sigma_hat, never a fixed number.')
        notes.append(
            'B AND C10 WERE RE-SCORED, NOT RE-TRAINED. Their committed predictions '
            'were scored by this same scorer in this same process and had to '
            'reproduce rebuild/ABC/out/abc_metrics.csv to <1e-9 before any T2 gap '
            'was computed. That both builds the noise pool through one code path and '
            're-proves nothing drifted between the campaigns.')
        notes.append(
            'WHAT A "WITHIN NOISE" RESULT DOES AND DOES NOT MEAN. At A/B/C\'s '
            'committed COD10K sigma_hat the bar is ~0.0179 (SINet) and ~0.0123 '
            '(SINet-v2) -- comparable to the paper\'s ENTIRE MT->Ours gap of 0.0142. '
            'C1\'s +0.0073 of a Cohen\'s d is a geometric quantity and predicts no '
            'accuracy difference at all. So a null here means "NO EFFECT RESOLVABLE '
            'AT THIS SENSITIVITY", never "no effect". This sentence was committed '
            'before any T2 number existed precisely so it could not be softened '
            'after one.')
        notes.append(
            'THE ARMS SHARE IMAGES BY CONSTRUCTION, AND THAT ATTENUATES EVERY GAP. '
            'All three C-family arms fund all 75 clusters, so they overlap above '
            'chance even at a permuted allocation: 452 to 511 of 1000 images differ '
            '(Jaccard 0.32-0.38, gated below 0.50 before training). Read every '
            'Delta against that effective contrast, reported in T2 block #1.')
        notes.append(
            'PREREGISTRATION_T2.md was committed before T2 block #1 and is FROZEN. '
            'This script neither reads it as an input nor writes it, and contains no '
            'tunable threshold of its own.')

    block = C.log_block(
        EXP, '.venv/bin/python rebuild/ABC/abc_evaluate.py --arms %s --gaps %s%s'
        % (args.arms, args.gaps, ' --tag ' + args.tag if args.tag else ''),
        metrics, thresholds,
        OLD_CLAIMS_T2 if args.gaps == 't2' else
        [('C3.1 sigma(Sa) all runs n=6', '0.00356  [no code]', 'SUPERSEDED'),
         ('C3.2 sigma(Sa) distinct seeds n=4', '0.00286  [no code]', 'SUPERSEDED'),
         ('C3.4 predicted Delta Sa', '0.000111  [no code]', 'RE-MEASURED'),
         ('C3.5 shortfall vs 2sigma', '64x (51x at B=2000)  [no code]', 'RE-MEASURED'),
         ('C1.1 Cohen\'s d targeted-vs-random', '~0.10  [no code]',
          'CROSS-CHECKED against a TRAINED outcome for the first time')],
        artifacts,
        representation=('Tea_epoch_best.pth of the final CSRDA round, 352x352 '
                        'inference, scored from written PNGs with Eval/metrics.py at '
                        '6 decimals'),
        trains='NO', notes='\n'.join(notes), write=not args.no_log)
    print(block)


if __name__ == '__main__':
    main()

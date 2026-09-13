#!/usr/bin/env python
"""EXP PC block #2 -- score the mean-teacher arm and apply the frozen rule.

Rule frozen in PREREGISTRATION_PC.md at c2114af, BEFORE any run. Nothing here
may alter it. C10 enters as a RE-SCORED reference arm, never re-trained.

Usage:
  .venv/bin/python rebuild/PC/pc_evaluate.py --gpu 0
  .venv/bin/python rebuild/PC/pc_evaluate.py --gpu 0 --no-log
"""
import argparse, csv, json, os, subprocess, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _p_ in (_REBUILD, os.path.join(_REBUILD, 'ABC'), _HERE, os.path.dirname(_REBUILD)):
    if _p_ not in sys.path:
        sys.path.insert(0, _p_)
import common as C                                          # noqa: E402
import abc_common as A                                      # noqa: E402
sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
import abc_evaluate as AE                                   # noqa: E402
import pc_train as PT                                       # noqa: E402

EXP = 'PC'
OUT = C.exp_dir(EXP, 'out'); os.makedirs(OUT, exist_ok=True)
PY = '.venv/bin/python'
B1_SA, B1_MAE, TOL = 0.717216, 0.074463, 1e-5
ENDPOINTS = ('COD10K', 'NC4K')


def _p(m): print('[%s] [PC] %s' % (time.strftime('%H:%M:%S'), m), flush=True)


def pred_dir(seed, endpoint):
    return os.path.join('Result/PC', PT.runid(seed), endpoint)


def infer(seed, endpoint, gpu):
    rid = PT.runid(seed)
    out = os.path.join(C.REPO, pred_dir(seed, endpoint))
    gtd = os.path.join(C.REPO, 'Dataset/Test/%s/GT' % endpoint)
    need = not (os.path.isdir(out) and len(os.listdir(out)) == len(os.listdir(gtd)))
    if not need:
        _p('  %s/%s predictions present' % (rid, endpoint)); return
    ck = './' + os.path.join('Snapshot/PC', rid, 'Tea_epoch_best.pth')
    cmd = [PY, 'MyTest.py', '--network', 'SINet', '--gpu', str(gpu),
           '--dataset', endpoint, '--model_path', ck,
           '--test_save', './' + pred_dir(seed, endpoint)]
    _p('  infer %s/%s' % (rid, endpoint))
    lg = open(os.path.join(OUT, 'pc_infer_%s_%s.log' % (rid, endpoint)), 'w')
    r = subprocess.run(cmd, cwd=C.REPO, stdout=lg, stderr=subprocess.STDOUT)
    lg.close()
    if r.returncode != 0:
        raise RuntimeError('PC HALT: inference failed for %s/%s' % (rid, endpoint))


def sd(xs):
    m = sum(xs) / len(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gpu', type=int, default=0)
    ap.add_argument('--no-log', action='store_true')
    a = ap.parse_args()

    # ---- G-PC1: scorer validation, before any PC number exists
    _p('G-PC1 scorer validation against B1 committed values')
    v = AE.score(os.path.join(C.REPO, 'Dataset/Test/COD10K/GT'),
                 os.path.join(C.REPO, 'Result/SINet/S2C'))
    dsa, dmae = abs(v['Sm'] - B1_SA), abs(v['MAE'] - B1_MAE)
    _p('  Sa %.6f (d %.2e)  MAE %.6f (d %.2e)' % (v['Sm'], dsa, v['MAE'], dmae))
    scorer_ok = bool(dsa < TOL and dmae < TOL)
    if not scorer_ok:
        raise RuntimeError('PC HALT: scorer failed G-PC1; refusing to score PC runs')

    # ---- MT: infer + score
    mt = {}
    for ep in ENDPOINTS:
        for s in PT.SEEDS:
            infer(s, ep, a.gpu)
        for s in PT.SEEDS:
            r = AE.score(os.path.join(C.REPO, 'Dataset/Test/%s/GT' % ep),
                         os.path.join(C.REPO, pred_dir(s, ep)))
            mt[(ep, s)] = r
            _p('  MT %s s%d  Sa %.6f  MAE %.6f' % (ep, s, r['Sm'], r['MAE']))

    # ---- C10 committed, re-scored never re-trained
    c10 = {}
    for row in csv.DictReader(open(os.path.join(C.REPO, 'rebuild/ABC/out/abc_metrics.csv'))):
        if row['arch'] == 'SINet' and row['arm'] == 'C10':
            c10[(row['endpoint'], int(row['seed']))] = float(row['Sm'])

    results = {}
    for ep in ENDPOINTS:
        mtv = [mt[(ep, s)]['Sm'] for s in PT.SEEDS]
        cv = [c10[(ep, s)] for s in PT.SEEDS]
        # sigma_hat pooled within-arm over {MT, C10}, df = 2*(3-1) = 4
        ss = sum((x - sum(mtv) / 3) ** 2 for x in mtv) + sum((x - sum(cv) / 3) ** 2 for x in cv)
        sig = (ss / 4) ** 0.5
        delta = sum(cv) / 3 - sum(mtv) / 3
        paired = [cv[i] - mtv[i] for i in range(3)]
        npos = sum(1 for d in paired if d > 0)
        signc = max(npos, 3 - npos)
        if abs(delta) <= 2 * sig:
            verdict = 'NOT DETECTED'
        elif signc == 3:
            verdict = 'DETECTED' if delta > 0 else 'REAL REGRESSION'
        else:
            verdict = 'INCONCLUSIVE'
        results[ep] = dict(mt_mean=sum(mtv) / 3, c10_mean=sum(cv) / 3, mt=mtv, c10=cv,
                           sigma_hat=sig, bar=2 * sig, delta=delta, paired=paired,
                           sign='%d/3' % npos, verdict=verdict,
                           mt_sd=sd(mtv), c10_sd=sd(cv),
                           vs_falsification_bar=bool(delta > 0.005533))
        _p('')
        _p('  %s: MT %.6f  C10 %.6f  Delta %+.6f  bar %.6f  sign %d/3  -> %s'
           % (ep, results[ep]['mt_mean'], results[ep]['c10_mean'], delta, 2 * sig,
              npos, verdict))

    C.save_json(os.path.join(OUT, 'pc_verdict.json'), results)
    with open(os.path.join(OUT, 'pc_metrics.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['arm', 'arch', 'seed', 'endpoint', 'Sm', 'MAE'])
        for ep in ENDPOINTS:
            for s in PT.SEEDS:
                w.writerow(['MT', 'SINet', s, ep, '%.6f' % mt[(ep, s)]['Sm'],
                            '%.6f' % mt[(ep, s)]['MAE']])
    if a.no_log:
        _p('--no-log: nothing written to REBUILD_LOG.txt'); return

    pr = results['COD10K']
    metrics = [
        ('scorer_reproduces_B1', 'Sa %.6f (delta %.2e), MAE %.6f (delta %.2e)'
         % (v['Sm'], dsa, v['MAE'], dmae), 'G-PC1, on committed Result/SINet/S2C'),
        ('MT_mean_COD10K', '%.6f' % pr['mt_mean'], 'sd %.6f; seeds %s'
         % (pr['mt_sd'], ' '.join('%.6f' % x for x in pr['mt']))),
        ('C10_mean_COD10K', '%.6f' % pr['c10_mean'],
         'committed arm, RE-SCORED never re-trained; sd %.6f' % pr['c10_sd']),
        ('sigma_hat_PC_COD10K', '%.6f' % pr['sigma_hat'],
         'pooled within-arm over {MT, C10}, df=4; bar = %.6f' % pr['bar']),
        ('DELTA_C10_minus_MT_COD10K', '%+.6f' % pr['delta'],
         'paired per seed: %s; sign %s' % (
             ' '.join('%+.6f' % d for d in pr['paired']), pr['sign'])),
        ('PC_VERDICT_COD10K', pr['verdict'], 'PREREGISTRATION_PC.md SS PC.5, frozen'),
        ('delta_exceeds_falsification_bar', str(pr['vs_falsification_bar']),
         'T-PC2: Delta against the frozen 0.005533 bar used by the paper'),
    ]
    sec = results['NC4K']
    metrics.append(('NC4K_secondary', 'MT %.6f  C10 %.6f  Delta %+.6f  bar %.6f -> %s'
                    % (sec['mt_mean'], sec['c10_mean'], sec['delta'], sec['bar'],
                       sec['verdict']), 'secondary endpoint, reported never decides'))
    thresholds = [
        ('scorer reproduces B1 committed Sa/MAE before any PC number', scorer_ok),
        ('T-PC1: Delta(C10-MT) > 2*sigma_hat AND sign 3/3 on the primary endpoint',
         pr['verdict'] == 'DETECTED'),
        ('T-PC2: Delta(C10-MT) also exceeds the frozen falsification bar 0.005533',
         pr['vs_falsification_bar']),
    ]
    C.log_block(
        EXP,
        cmd='%s rebuild/PC/pc_evaluate.py' % PY,
        metrics=metrics, thresholds=thresholds,
        artifacts=[os.path.join(OUT, 'pc_verdict.json'),
                   os.path.join(OUT, 'pc_metrics.csv')],
        representation=('Tea_epoch_best.pth, 352x352 inference, scored from written '
                        'PNGs with Eval/metrics.py at 6 decimals; identical scorer and '
                        'endpoint as every committed campaign'),
        trains='NO',
        notes=('BLOCK 2 OF 2 -- THE POSITIVE CONTROL VERDICT. Rule frozen in '
               'PREREGISTRATION_PC.md at c2114af before the first run; not altered here. '
               'This is a control on INSTRUMENT SENSITIVITY, not an ablation: C10 differs '
               'from MT in method, round count and pool size at once, so no component '
               'attribution follows and none is made. C10 is re-scored from its committed '
               'predictions, never re-trained. A DETECTED verdict establishes that effects '
               'of roughly the reference magnitude are visible to this harness; it says '
               'nothing about whether effects the size of the paper\'s nulls would be.'))
    _p('EXP PC block #2 appended.')


if __name__ == '__main__':
    main()

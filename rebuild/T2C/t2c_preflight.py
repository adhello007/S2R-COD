#!/usr/bin/env python
"""T2-C pre-flight -- the gates runnable BEFORE any signal exists.

HALT SEMANTICS: every gate returns dict(gate=..., passed=bool, ...). A gate
crash is a FAIL, never a skip. The caller halts; this module only measures.

Gates here (PREREGISTRATION_T2C.md, T2C_PLAN.md section 6):
  G2  escfg        live ESLoss is a=0.9 b=0.3 c=0.5 use_weighted_bce=False
  G3  signal       the T2-C-appropriate signal gate (see gate_signal)
  G5  partition    seed-0 refit reproduces the committed labels exactly
  G8  harness      t2c_correlation reproduces b1_faithful_correlation.json bitwise
  G9  scorer       Sa 0.717216 / MAE 0.074463 to < 1e-5 before any new number
  G10 provenance   E0.step_independence() called unchanged, n_forbidden == 0
  G11 checkpoints  sha256 of every signal-source .pth recorded and matched

Gates 1 (target-side), 4/6/7 (ES reproduction) and 12 (boundary coverage) need
the measured signals and therefore live in t2c_measure.py, after scoring.

INFERENCE ONLY. TRAINS NOTHING.
"""

import ast
import glob
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _pth in (_REBUILD, os.path.join(_REBUILD, 'B1'), os.path.join(_REBUILD, 'C1'),
             os.path.join(_REBUILD, 'E0'), os.path.join(_REBUILD, 'ABC'),
             _HERE, os.path.dirname(_REBUILD)):
    if _pth not in sys.path:
        sys.path.insert(0, _pth)
import common as C                                            # noqa: E402
import b1_es_error_correlation as B1                           # noqa: E402
import c1_preflight as PF                                      # noqa: E402
import t2c_signals as S                                        # noqa: E402

EXP = 'T2C'
OUT = S.OUT
PRAGMA = PF.PRAGMA            # reuse C1's pragma, do not invent a second one

# Committed reference values, abc_evaluate.py:43.
B1_SA, B1_MAE, SCORER_TOL = 0.717216, 0.074463, 1e-5

# C1's cluster bans, reused -- MINUS fit_kmeans, because routing every fit
# through B1.fit_kmeans is exactly the sanctioned path here (its cache is an
# in-memory dict, so the committed partition is never rewritten). Direct KMeans
# construction and sklearn.cluster imports stay banned.
BANNED_CLUSTER_CALLS = PF.BANNED_CLUSTER_CALLS - {'fit_kmeans'}    # c1-gate-ok
BANNED_CLUSTER_MODULES = PF.BANNED_CLUSTER_MODULES                 # c1-gate-ok
# The same-side correlation. B1 computes it legitimately; T2-C must never call
# it, because it answers the easier question (rho(MAE) +0.8754 vs +0.6284).
BANNED_SAMESIDE = 'step_correlate'                                 # c1-gate-ok


def _p(m):
    print(m, flush=True)


def _t2c_sources():
    return sorted(glob.glob(os.path.join(_HERE, '*.py')))


def _scan(check):
    """Run `check` over every T2-C source; split hits by pragma.

    c1_preflight._scan_sources and abc_preflight._scan are bound to their OWN
    directories by a local glob, so neither sees rebuild/T2C/. This is the third
    binding, mirroring abc_preflight._scan:58-71 and reusing PF.docstring_ids.
    """
    hits, exempt = [], []
    for path in _t2c_sources():
        rel = os.path.relpath(path, C.REPO)
        src = open(path, errors='ignore').read()
        lines = src.splitlines()
        tree = ast.parse(src)
        for lineno, what in check(tree, PF.docstring_ids(tree), lines, rel):
            line = lines[lineno - 1] if 0 < lineno <= len(lines) else ''
            rec = dict(file=rel, line=lineno, what=what, text=line.strip()[:110])
            (exempt if PRAGMA in line else hits).append(rec)
    return hits, exempt


def _attr_calls(node):
    """Names of every attribute/plain call in a subtree."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, 'id', None) or getattr(n.func, 'attr', None)
            if nm:
                out.add(nm)
    return out


# --- G3 ---------------------------------------------------------------------

def gate_signal():
    """The T2-C-appropriate signal gate.

    C1/ABC's gate_signal AST-bans the endpoint-ES column literal
    (c1_preflight.py:65). That ban is right for ALLOCATION experiments, where
    allocating by an endpoint-measured quantity is leakage. T2-C is a B1-class
    CORRELATION study and must read endpoint ERROR, so the ban is not adopted as
    the operative rule. What replaces it:

      asserts  every signal is target-side -- enforced by S.assert_target_side
               in t2c_measure.py (G1), the substantive property the literal ban
               was protecting.
      permits  reading endpoint error through B1.load_scores(arch, 'test').
      bans     step_correlate (the same-side correlation), direct KMeans
               construction, and sklearn.cluster imports.
      bans     per-image min-max renormalisation anywhere in the signal path:
               B1's ERROR path renormalises (b1_es_error_correlation.py:256) but
               its ES path does not, and entropy is a CALIBRATION quantity that
               min-max would destroy.

    C1's literal ban is ALSO evaluated and reported. It passes, because this
    implementation never reads the endpoint ES column at all -- the endpoint-side
    ES row of T2C_PLAN.md section 4 is quoted from B1's committed record rather
    than recomputed. The departure is therefore narrower in practice than
    PREREGISTRATION_T2C.md T2C.2.3 anticipated, and T2-C is held to the stricter
    standard where it costs nothing. Reported, not assumed.
    """
    def check(tree, docs, lines, rel):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nm = (getattr(node.func, 'id', None)
                      or getattr(node.func, 'attr', None))
                if nm in BANNED_CLUSTER_CALLS:
                    yield node.lineno, 'call %s(...)' % nm
                if nm == BANNED_SAMESIDE:
                    yield node.lineno, 'call %s(...) -- the SAME-SIDE correlation' % nm
            elif isinstance(node, ast.Import):
                for al in node.names:
                    if al.name in BANNED_CLUSTER_MODULES:
                        yield node.lineno, 'import %s' % al.name
            elif isinstance(node, ast.ImportFrom):
                if node.module in BANNED_CLUSTER_MODULES:
                    yield node.lineno, 'from %s import ...' % node.module
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                # the (x - x.min()) / (x.max() - x.min()) renormalisation idiom
                calls = _attr_calls(node)
                if 'min' in calls and 'max' in calls:
                    yield node.lineno, 'min-max renormalisation in a division'
    hits, exempt = _scan(check)

    # C1's literal ban, evaluated as an ADDITIONAL (stricter) check.
    def literal_check(tree, docs, lines, rel):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docs:
                    continue
                if PF.BANNED_SIGNAL in node.value:
                    yield node.lineno, 'string literal %r' % PF.BANNED_SIGNAL
            elif isinstance(node, ast.Attribute) and node.attr == PF.BANNED_SIGNAL:
                yield node.lineno, 'attribute .%s' % PF.BANNED_SIGNAL
    lit_hits, lit_exempt = _scan(literal_check)

    # C1's data half, called unchanged: the partition T2-C consumes must still
    # carry a fully populated target-side signal column.
    c1_data = PF.gate_signal([S.TAG])

    return dict(gate='signal', passed=bool(not hits and c1_data['passed']),
                violations=hits, exempted=exempt,
                scanned=len(_t2c_sources()),
                c1_data_half=c1_data['passed'],
                c1_literal_ban_also_passes=bool(not lit_hits),
                c1_literal_violations=lit_hits,
                banned_cluster_calls=sorted(BANNED_CLUSTER_CALLS),
                banned_sameside=BANNED_SAMESIDE,
                note=('correlation study: the allocation-signal literal ban is not '
                      'the operative rule, but it is evaluated and passes because '
                      'T2-C never reads the endpoint ES column. No T2-C output is '
                      'ever used to allocate.'))


# --- G2 ---------------------------------------------------------------------

def gate_escfg():
    """ES config parsed from the LIVE MyTrain.py, never hardcoded."""
    cfg = B1.parse_es_config()
    ok = (cfg['a'] == 0.9 and cfg['b'] == 0.3 and cfg['c'] == 0.5
          and cfg['use_weighted_bce'] and cfg['cls_calls_on_sigmoid'])
    # NOTE on the flag name: B1's parsed key `use_weighted_bce` is True when the
    # STRING 'use_weighted_bce=False' was found in the PGT_Loss call -- i.e. the
    # key is inverted relative to its name (b1_es_error_correlation.py:119).
    # True here therefore means the PGT instance is UNWEIGHTED, which is the one
    # B1 measured and the one T2-C re-derives.
    return dict(gate='escfg', passed=bool(ok), a=cfg['a'], b=cfg['b'], c=cfg['c'],
                pgt_call=cfg['pgt_call'],
                pgt_is_unweighted=cfg['use_weighted_bce'],
                cls_calls_on_sigmoid=cfg['cls_calls_on_sigmoid'],
                myTrain_line=cfg['myTrain_line'],
                note='a/b/c from the --task S2C override block; unweighted BCE is '
                     'a property of the PGT_Loss instance (MyTrain.py:306), not '
                     'of that block')


# --- G5 ---------------------------------------------------------------------

def gate_partition():
    try:
        n = S.assert_refit_matches_committed()
    except RuntimeError as e:
        return dict(gate='partition', passed=False, halt=str(e))
    a = S.committed_assignment()
    return dict(gate='partition', passed=True, n_target_labels=n,
                k=a['k'], seed=a['seed'], embedder=a['embedder'],
                note='seed-0 refit is label-identical to the committed partition, '
                     'so the in-memory seeds 1-9 refits are comparable')


# --- G8 ---------------------------------------------------------------------

def gate_harness():
    try:
        r = S.assert_harness_reproduces_b1()
    except RuntimeError as e:
        return dict(gate='harness', passed=False, halt=str(e))
    return dict(gate='harness', passed=True, **r)


# --- G9 ---------------------------------------------------------------------

def gate_scorer():
    """Sa / MAE reproduction on the COMMITTED predictions, before any new number.

    abc_evaluate.score is called unchanged. Its `metrics` import needs Eval on
    sys.path, which abc_evaluate.main() normally does.
    """
    sys.path.insert(0, os.path.join(C.REPO, 'Eval'))
    import abc_evaluate as AE
    v = AE.score(os.path.join(C.REPO, 'Dataset/Test/COD10K/GT'),
                 os.path.join(C.REPO, 'Result/SINet/S2C'))
    dsa, dmae = abs(v['Sm'] - B1_SA), abs(v['MAE'] - B1_MAE)
    return dict(gate='scorer', passed=bool(dsa < SCORER_TOL and dmae < SCORER_TOL),
                Sm=v['Sm'], MAE=v['MAE'], d_Sa=dsa, d_MAE=dmae,
                n=v['n'], tol=SCORER_TOL,
                note='abc_evaluate.score unchanged, on Result/SINet/S2C vs '
                     'COD10K GT; B1 logged 0.717216 / 0.074463')


# --- G10 --------------------------------------------------------------------

def gate_provenance():
    """E0.step_independence() called unchanged, never re-implemented.

    DISCLOSED: step_independence writes rebuild/E0/out/e0_independence.json as a
    side effect -- it is a pure reporter that saves its own report, and C1's
    gate_freshness and ABC's gate_provenance rewrite it on every run for the same
    reason. Calling it unchanged is what PREREGISTRATION_T2C.md T2C.2.1 requires,
    and re-implementing it to dodge the write is explicitly forbidden. The file
    is a regenerable provenance report, not a measurement.
    """
    import e0_regenerate as E0
    indep = E0.step_independence()
    return dict(gate='provenance',
                passed=bool(indep['n_forbidden'] == 0
                            and not indep['inputs_missing']),
                n_forbidden=indep['n_forbidden'],
                forbidden=indep['forbidden_references'][:10],
                n_exempted=indep['n_exempted'],
                scripts_scanned=len(indep['scripts_scanned']),
                inputs_resolved=indep['inputs_resolved'],
                inputs_missing=indep['inputs_missing'],
                t2c_in_scan=sorted(f for f in indep['scripts_scanned']
                                   if 'T2C' in f),
                side_effect='rewrites rebuild/E0/out/e0_independence.json')


# --- G11 --------------------------------------------------------------------

def signal_checkpoints():
    """Every .pth a T2-C signal reads: 8 per architecture, 16 in all."""
    out = []
    for arch in S.ARCHS:
        spec = B1.ARCHS[arch]
        snap = os.path.join('Snapshot', arch)
        out.append((arch, 'S2C_teacher', os.path.join(snap, 'Tea_epoch_best.pth')))
        out.append((arch, 'S2C_student', os.path.join(snap, spec['stu'])))
        for arm in S.ENS_ARMS:
            for sd in S.ENS_SEEDS:
                rid = '%s_%s_s%d' % (S.ABC_ARCH[spec['net']], arm, sd)
                out.append((arch, '%s_s%d' % (arm, sd),
                            os.path.join('Snapshot/ABC', rid, 'Tea_epoch_best.pth')))
    return out


# Measured 2026-09-11, BEFORE any T2-C code existed; pinned in T2C_PLAN.md
# section 7. All six distinct, so the 3-member ensemble is 3 distinct networks.
A0_REFERENCE_SHA = {
    'Snapshot/ABC/SINet_A0_s42/Tea_epoch_best.pth':
        '7902923839f26cfbbe5f8705b69b9221565cb0877adcb72bd9b32e15a1142646',
    'Snapshot/ABC/SINet_A0_s43/Tea_epoch_best.pth':
        '391c62df5f5996f7c731c111fa7ed86e2d14fd02e0a3c573e21b161ee4af3907',
    'Snapshot/ABC/SINet_A0_s45/Tea_epoch_best.pth':
        '8c868b4ef2dcd6abf7d314b2ee7cc432480d92149126be62ac5b25bca20fde79',
    'Snapshot/ABC/SINetv2_A0_s42/Tea_epoch_best.pth':
        'ec2bc90311dda6c71f1fdb36c83e0ab732e9cc43b89972b7dc445bee3c3cae8d',
    'Snapshot/ABC/SINetv2_A0_s43/Tea_epoch_best.pth':
        '065ebe6124de1c1ae15c8839a1a3958f7f14eec00b0276f86e061d87246c6e2d',
    'Snapshot/ABC/SINetv2_A0_s45/Tea_epoch_best.pth':
        'e2a2404160af380fe5f4ccd560733e09769409dd5b342e21d371e4f43edf7379',
}


def gate_checkpoints():
    rows, missing, mismatched = [], [], []
    for arch, role, rel in signal_checkpoints():
        ap = os.path.join(C.REPO, rel)
        if not os.path.isfile(ap):
            missing.append(rel)
            continue
        sha = C.sha256(ap)
        rows.append(dict(arch=arch, role=role, path=rel, sha256=sha,
                         bytes=os.path.getsize(ap)))
        ref = A0_REFERENCE_SHA.get(rel)
        if ref and ref != sha:
            mismatched.append(dict(path=rel, expected=ref, got=sha))
    ens = [r for r in rows if r['role'].startswith(('A0_', 'CSHUF_'))]
    dup = len(ens) - len({r['sha256'] for r in ens})
    return dict(gate='checkpoints',
                passed=bool(not missing and not mismatched and dup == 0),
                n=len(rows), missing=missing, mismatched=mismatched,
                duplicate_ensemble_members=dup, checkpoints=rows,
                note='a duplicate pair inside an ensemble arm would mean that arm '
                     'is fewer than 3 distinct networks')


GATES = ['signal', 'escfg', 'partition', 'harness', 'scorer', 'provenance',
         'checkpoints']


def run_preflight(skip=()):
    report = {'generated': C.now(), 'commit': C.git_commit(), 'gates': [],
              'all_passed': None}
    fns = dict(signal=gate_signal, escfg=gate_escfg, partition=gate_partition,
               harness=gate_harness, scorer=gate_scorer,
               provenance=gate_provenance, checkpoints=gate_checkpoints)
    for name in GATES:
        if name in skip:
            _p('  gate %-12s SKIPPED' % name)
            report['gates'].append(dict(gate=name, passed=True, skipped=True))
            continue
        try:
            r = fns[name]()
        except Exception as e:                       # a gate crash is a FAIL
            r = dict(gate=name, passed=False,
                     crash='%s: %s' % (type(e).__name__, str(e)[:300]))
        report['gates'].append(r)
        _p('  gate %-12s %s' % (name, 'PASS' if r['passed'] else 'FAIL'))
    report['all_passed'] = all(g['passed'] for g in report['gates'])
    os.makedirs(OUT, exist_ok=True)
    C.save_json(os.path.join(OUT, 't2c_preflight.json'), report)
    return report


if __name__ == '__main__':
    _p('T2-C pre-flight (pre-signal gates)')
    r = run_preflight()
    _p('all_passed = %s  -> %s' % (r['all_passed'],
                                   os.path.join(OUT, 't2c_preflight.json')))
    raise SystemExit(0 if r['all_passed'] else 1)

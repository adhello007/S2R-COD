#!/usr/bin/env python
"""ABC Phase 0 -- the six gates.

HALT SEMANTICS, copied from C1 deliberately. Every gate returns a dict; none
raises for a data failure. The report is written to rebuild/ABC/out/
abc_preflight.json even when a gate fails, so the failure is itself an artifact.
There is no --force.

  G1 signal        allocate by the target-side signal, never the endpoint one;
                   consume B1's committed partition; never fit one
  G2 provenance    no archive / scratchpad dependency anywhere in rebuild/;
                   primary inputs still match E0's manifest
  G3 one trainer   exactly one MyTrain.py and one MyTest.py in the tree, and all
                   six patches present in them
  G4 endpoints     CHAMELEON withdrawn, CAMO is selection-only
  G5 pools         per-arm integrity: counts, stem-set equality, REAL SrcDataset
                   positional parity for every index, round-2 worst case, base
                   bytes against E0's manifest, arm-C reproduction of C1's cell
  G6 determinism   MyTrain.py declares cudnn.deterministic / benchmark / seed

G1's data half and G2 both CALL the upstream gate rather than re-implementing
it, so ABC cannot drift from the gates C1 and E0 self-tested.

TRAINS NOTHING.
"""

import ast
import glob
import itertools
import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REBUILD = os.path.dirname(_HERE)
for _p in (_REBUILD, os.path.join(_REBUILD, 'C1'), os.path.join(_REBUILD, 'E0'),
           _HERE, os.path.dirname(_REBUILD)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import common as C                                            # noqa: E402
import c1_preflight as PF                                     # noqa: E402
import abc_common as A                                        # noqa: E402

OUT = A.OUT
MANIFEST = C.exp_dir('E0', 'out', 'e0_manifest.sha256')
PRAGMA = PF.PRAGMA          # reuse C1's pragma, do not invent a second one


def _p(m):
    print(m, flush=True)


def _abc_sources():
    return sorted(glob.glob(os.path.join(_HERE, '*.py')))


def _scan(check):
    """Run `check` over every ABC source; split hits by pragma. Mirrors
    c1_preflight._scan_sources, which is bound to C1's own file list."""
    hits, exempt = [], []
    for path in _abc_sources():
        rel = os.path.relpath(path, C.REPO)
        src = open(path, errors='ignore').read()
        lines = src.splitlines()
        tree = ast.parse(src)
        for lineno, what in check(tree, PF.docstring_ids(tree), lines, rel):
            line = lines[lineno - 1] if 0 < lineno <= len(lines) else ''
            rec = dict(file=rel, line=lineno, what=what, text=line.strip()[:110])
            (exempt if PRAGMA in line else hits).append(rec)
    return hits, exempt


# --- G1 ---------------------------------------------------------------------

def gate_signal():
    sig = PF.gate_signal([A.EMBEDDER])            # C1's data half, unchanged
    src = PF.gate_cluster_source([A.EMBEDDER])    # C1's partition half, unchanged

    def check(tree, docs, lines, rel):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docs:
                    continue
                if PF.BANNED_SIGNAL in node.value:
                    yield node.lineno, 'string literal %r' % PF.BANNED_SIGNAL
            elif isinstance(node, ast.Attribute) and node.attr == PF.BANNED_SIGNAL:
                yield node.lineno, 'attribute .%s' % PF.BANNED_SIGNAL
            elif isinstance(node, ast.Call):
                nm = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
                if nm in PF.BANNED_CLUSTER_CALLS:
                    yield node.lineno, 'call %s(...)' % nm
            elif isinstance(node, ast.Import):
                for al in node.names:
                    if al.name in PF.BANNED_CLUSTER_MODULES:
                        yield node.lineno, 'import %s' % al.name
            elif isinstance(node, ast.ImportFrom):
                if node.module in PF.BANNED_CLUSTER_MODULES:
                    yield node.lineno, 'from %s import ...' % node.module
    hits, exempt = _scan(check)
    ok = bool(sig['passed'] and src['passed'] and not hits)
    return dict(gate='signal', passed=ok, c1_signal=sig['passed'],
                c1_cluster_source=src['passed'], violations=hits,
                exempted=exempt, scanned=len(_abc_sources()),
                note='C1 gate_signal + gate_cluster_source called unchanged; ABC '
                     'sources scanned with C1\'s own banned-token declarations')


# --- G2 ---------------------------------------------------------------------

def gate_provenance(sample=200, seed=0):
    import e0_regenerate as E0
    indep = E0.step_independence()
    rng = random.Random(seed)
    bad, checked = [], 0
    man = {}
    for line in open(MANIFEST):
        if line.startswith('#'):
            continue
        d, k = line.split()
        man[k] = d
    for key in ('raw', 'raw_gt', 'auth', 'auth_gt', 'tgt', 'local', 'local_msk'):
        path = C.ipath(key)
        names = sorted(os.listdir(path))
        for nm in rng.sample(names, min(sample // 7 + 1, len(names))):
            exp = man.get('%s/%s' % (key, nm))
            checked += 1
            if exp is None or C.sha256(os.path.join(path, nm)) != exp:
                bad.append('%s/%s' % (key, nm))
    ok = bool(indep['n_forbidden'] == 0 and not indep['inputs_missing'] and not bad)
    return dict(gate='provenance', passed=ok,
                n_forbidden=indep['n_forbidden'], n_exempted=indep['n_exempted'],
                scripts_scanned=len(indep['scripts_scanned']),
                abc_scripts_seen=sum(1 for s in indep['scripts_scanned']
                                     if os.sep + 'ABC' + os.sep in s),
                inputs_resolved=indep['inputs_resolved'],
                inputs_missing=indep['inputs_missing'],
                manifest_checked=checked, manifest_bad=bad,
                note='E0.step_independence() imported and CALLED, not '
                     're-implemented; it walks all of rebuild/ so it covers ABC')


# --- G3 ---------------------------------------------------------------------

PATCH_MARKS = {
    'MyTrain.py': ["'--seed'", 'cudnn.deterministic', 'cudnn.benchmark',
                   'opt.source_root is None', 'set_random_seed(opt.seed)'],
    'MyTest.py': ["'--dataset'", "Test/{}/Imgs/", 'opt.dataset'],
    'Eval/MyEval.py': ["nargs='+'"],
    'preflight.py': ['Test/COD10K/Imgs'],
}
SKIP_DIRS = ('.venv', 'LAKE-RED', os.path.join('rebuild', 'reference'), '__pycache__')


def gate_one_trainer():
    found = {'MyTrain': [], 'MyTest': []}
    for root, dirs, files in os.walk(C.REPO):
        rel = os.path.relpath(root, C.REPO)
        if any(s in rel for s in SKIP_DIRS):
            dirs[:] = []
            continue
        for f in files:
            for key in found:
                if f.startswith(key) and f.endswith('.py'):
                    found[key].append(os.path.join(rel, f))
    missing = {}
    for f, marks in PATCH_MARKS.items():
        src = open(os.path.join(C.REPO, f)).read()
        absent = [m for m in marks if m not in src]
        if absent:
            missing[f] = absent
    ok = bool(len(found['MyTrain']) == 1 and len(found['MyTest']) == 1 and not missing)
    return dict(gate='one_trainer', passed=ok, mytrain=found['MyTrain'],
                mytest=found['MyTest'], patches_missing=missing,
                note='ground rule 2: arms differ only by data dir and seed, so a '
                     'second trainer anywhere in the tree is a FAIL')


# --- G4 ---------------------------------------------------------------------

def gate_endpoints():
    mt = open(os.path.join(C.REPO, 'MyTest.py')).read()
    ev = open(os.path.join(C.REPO, 'Eval/MyEval.py')).read()
    d = dict(
        mytest_excludes_chameleon="'CHAMELEON'" not in mt,
        mytest_excludes_camo="'CAMO'" not in mt,
        myeval_excludes_chameleon="'CHAMELEON'" not in ev,
        endpoints=list(A.ENDPOINTS),
        val_root_is_camo=os.path.isdir(os.path.join(C.REPO, 'Dataset/Val/CAMO/Imgs')),
        camo_n=len(os.listdir(os.path.join(C.REPO, 'Dataset/Val/CAMO/Imgs'))),
        camo_gt_n=len(os.listdir(os.path.join(C.REPO, 'Dataset/Val/CAMO/GT'))))
    for e in A.ENDPOINTS:
        d['%s_imgs' % e] = len(os.listdir(os.path.join(C.REPO, 'Dataset/Test/%s/Imgs' % e)))
        d['%s_gt' % e] = len(os.listdir(os.path.join(C.REPO, 'Dataset/Test/%s/GT' % e)))
    d['passed'] = bool(d['mytest_excludes_chameleon'] and d['mytest_excludes_camo']
                       and d['myeval_excludes_chameleon']
                       and d['camo_n'] == d['camo_gt_n'] == 250
                       and d['COD10K_imgs'] == d['COD10K_gt'] == 2026
                       and d['NC4K_imgs'] == d['NC4K_gt'] == 4121)
    d['gate'] = 'endpoints'
    d['note'] = ('CHAMELEON withdrawn on D2 (41/76 = 53.9% is training data); CAMO '
                 'is the checkpoint-selection set and can never be an endpoint')
    return d


# --- G5 ---------------------------------------------------------------------

def check_pool(rid, arm, seed):
    """ABC_PLAN.md A.8.1 #1-#6 for one assembled pool. Returns a dict."""
    from Src.utils.Dataloader import SrcDataset
    from PIL import Image
    import numpy as np
    stem = lambda f: os.path.splitext(f)[0]                       # noqa: E731
    pool = os.path.join(C.REPO, A.pool_dir(rid))
    expect = 4447 if arm == 'A0' else 4447 + A.BUDGET
    img = sorted(os.listdir(pool + '/Image'))
    gt = sorted(os.listdir(pool + '/GT'))
    r = dict(runid=rid, arm=arm, seed=seed, n_image=len(img), n_gt=len(gt),
             expect=expect)
    r['a1_counts'] = bool(len(img) == len(gt) == expect)
    r['a2_stem_sets'] = bool({stem(f) for f in img} == {stem(f) for f in gt})
    r['a3_no_dup_stem'] = bool(len({stem(f) for f in img}) == len(img)
                               and len({stem(f) for f in gt}) == len(gt))
    r['exts'] = dict(Image=sorted({os.path.splitext(f)[1] for f in img}),
                     GT=sorted({os.path.splitext(f)[1] for f in gt}))
    r['a3_no_tif'] = not any(f.endswith('.tif') for f in gt)
    ds = SrcDataset(pool + '/Image/', pool + '/GT/', 352)
    r['len_dataset'] = len(ds)
    mism = [i for i in range(len(ds))
            if stem(os.path.basename(ds.images[i])) != stem(os.path.basename(ds.gts[i]))]
    r['a4_parity_all_i'] = bool(not mism and len(ds) == expect)
    r['a4_mismatches'] = len(mism)
    idxs = [len(ds) // 2] + random.Random(seed).sample(range(len(ds)), 3)
    spot = True
    for i in idxs:
        a = Image.open(ds.images[i])
        b = Image.open(ds.gts[i]).convert('L')
        wf = float((np.array(b) > 127).mean())
        spot &= bool(a.size == b.size and 0.0 < wf < 1.0)
    r['a5_spotcheck'] = spot
    # #6 round-2 worst case: the pool union ALL 4040 target names as .png in both
    tgt = sorted(os.listdir(os.path.join(C.REPO, 'Dataset/Target/Image')))
    app = [stem(f) + '.png' for f in tgt]
    si, sg = sorted(img + app), sorted(gt + app)
    r['a6_round2_n'] = len(si)
    r['a6_round2_parity'] = bool(len(si) == len(sg)
                                 and all(stem(si[i]) == stem(sg[i]) for i in range(len(si))))
    return r


def gate_pools(runs):
    man = {}
    for line in open(MANIFEST):
        if not line.startswith('#'):
            d, k = line.split()
            man[k] = d
    per, base_ok, mask_ok = [], [], []
    seen_base = set()
    for arch, arm, seed in runs:
        rid = A.runid(arch, arm, seed)
        r = check_pool(rid, arm, seed)
        per.append(r)
        # base subset against E0's manifest -- once per distinct pool content
        pool = os.path.join(C.REPO, A.pool_dir(rid))
        if rid not in seen_base:
            seen_base.add(rid)
            nb = 0
            for key, sub, ext in (('auth', 'Image', '.jpg'), ('auth_gt', 'GT', '.png')):
                for nm in sorted(os.listdir(os.path.join(pool, sub))):
                    if nm.startswith(('SOD_', 'DUP_')):
                        continue
                    exp = man.get('%s/%s' % (key, nm))
                    if exp is None or C.sha256(os.path.join(pool, sub, nm)) != exp:
                        nb += 1
            base_ok.append((rid, nb))
    # every distinct C-family arm actually in this run set
    cfam = [m for m in dict.fromkeys(m for _, m, _ in runs) if m in A.ARM_ALPHA]
    # C10 is ALWAYS a reference set even when it is not in this run set: its full
    # cell must still reproduce (which is what anchors the signal's provenance),
    # and it is the arm every T2 gap is measured against, so its overlap with each
    # new arm has to be gated too (PREREGISTRATION_T2.md T2.7, T2.8).
    cref = list(dict.fromkeys(cfam + ['C10']))
    # the 1000 render masks equal raw_gt, for every distinct arm-B/C stem set
    import numpy as np
    from PIL import Image
    for label, stems in [(m, A.arm_c_stems(A.ARM_ALPHA[m], A.ARM_ES_PERM[m])[0])
                         for m in cfam] + \
                        [('B_s%d' % s, A.arm_b_stems(s)) for s in A.SEEDS]:
        nb = 0
        for st in stems:
            a = np.array(Image.open(os.path.join(C.REPO, A.RAW_GT, st + '.png')).convert('L'))
            b = np.array(Image.open(os.path.join(C.REPO, A.REN_MSK, 'SOD_' + st + '.png')).convert('L'))
            if a.shape != b.shape or int(np.abs(a.astype(int) - b.astype(int)).max()) != 0:
                nb += 1
        mask_ok.append((label, len(stems), nb))
    # C-family reproduction. C10 must reproduce C1's committed cell in FULL. A T2
    # permutation arm must reproduce its SHAPE keys exactly -- the same-shape
    # assertion (PREREGISTRATION_T2.md T2.4). n_displaced is a consequence of the
    # allocation, so it is REPORTED and never asserted for a permuted arm.
    repro = {}
    for arm in cref:
        alpha = A.ARM_ALPHA[arm]
        _, cell = A.arm_c_stems(alpha, A.ARM_ES_PERM[arm])
        keys = A.SHAPE_KEYS if A.ARM_ES_PERM[arm] else tuple(A.C1_CELL[alpha])
        repro[arm] = dict(measured=cell, c1=A.C1_CELL[alpha], asserted=list(keys),
                          match=all(cell[k] == A.C1_CELL[alpha][k] for k in keys))
    # pairwise overlap against chance over every distinct selected set in play
    chance = A.BUDGET * A.BUDGET / 4447.0
    sets = {m: set(A.arm_c_stems(A.ARM_ALPHA[m], A.ARM_ES_PERM[m])[0]) for m in cref}
    sets.update({'B_s%d' % s: set(A.arm_b_stems(s)) for s in A.SEEDS})
    ov = {}
    for a, b in itertools.combinations(sorted(sets), 2):
        x, y = sets[a], sets[b]
        kind = ('CxC' if a in A.ARM_ALPHA and b in A.ARM_ALPHA
                else ('BxB' if a not in A.ARM_ALPHA and b not in A.ARM_ALPHA else 'BxC'))
        ov['%s|%s' % (a, b)] = dict(overlap=len(x & y), chance=round(chance, 1),
                                    ratio=round(len(x & y) / chance, 3),
                                    jaccard=round(len(x & y) / len(x | y), 4),
                                    n_differing=A.BUDGET - len(x & y), kind=kind)
    ok = bool(all(r['a1_counts'] and r['a2_stem_sets'] and r['a3_no_dup_stem']
                  and r['a3_no_tif'] and r['a4_parity_all_i'] and r['a5_spotcheck']
                  and r['a6_round2_parity'] for r in per)
              and all(n == 0 for _, n in base_ok)
              and all(n == 0 for _, _, n in mask_ok)
              and all(v['match'] for v in repro.values())
              and all(0.7 <= v['ratio'] <= 1.3
                      for v in ov.values() if v['kind'] == 'BxC')
              # T2.7 distinctness: two C-family arms sharing most of their images
              # cannot test the claim -- a null would be mechanical.
              and all(v['jaccard'] <= A.T2_MAX_JACCARD
                      for v in ov.values() if v['kind'] == 'CxC'))
    return dict(gate='pools', passed=ok, n_pools=len(per), per_pool=per,
                base_bytes_bad=base_ok, render_mask_bad=mask_ok,
                armC_reproduces_C1=repro, overlap_B_vs_C=ov,
                note='parity asserted on the REAL SrcDataset for every index, and '
                     'round-2 parity proved on the full worst-case union')


# --- G6 ---------------------------------------------------------------------

def gate_determinism():
    src = open(os.path.join(C.REPO, 'MyTrain.py')).read()
    d = dict(gate='determinism',
             deterministic_true='torch.backends.cudnn.deterministic = True' in src,
             benchmark_false='torch.backends.cudnn.benchmark = False' in src,
             seed_from_opt='set_random_seed(opt.seed)' in src,
             hardcoded_42_gone='set_random_seed(42)' not in src)
    d['passed'] = all(v for k, v in d.items() if k != 'gate')
    d['note'] = ('read from source, not from live flags: the gate runs in a '
                 'different process than training. REDUCES, does not eliminate, '
                 'kernel nondeterminism (ABC_PLAN.md A.6)')
    return d


GATES = ['signal', 'provenance', 'one_trainer', 'endpoints', 'pools', 'determinism']


def run_preflight(runs, skip=()):
    report = {'generated': C.now(), 'commit': C.git_commit(),
              'runs': ['%s_%s_s%d' % r for r in runs], 'gates': [],
              'all_passed': None}
    fns = dict(signal=gate_signal, provenance=gate_provenance,
               one_trainer=gate_one_trainer, endpoints=gate_endpoints,
               pools=lambda: gate_pools(runs), determinism=gate_determinism)
    for name in GATES:
        if name in skip:
            _p('  gate %-14s SKIPPED' % name)
            report['gates'].append(dict(gate=name, passed=True, skipped=True))
            continue
        try:
            r = fns[name]()
        except Exception as e:                          # a gate crash is a FAIL
            r = dict(gate=name, passed=False,
                     crash='%s: %s' % (type(e).__name__, str(e)[:300]))
        report['gates'].append(r)
        _p('  gate %-14s %s' % (name, 'PASS' if r['passed'] else 'FAIL'))
    report['all_passed'] = all(g['passed'] for g in report['gates'])
    os.makedirs(A.OUT, exist_ok=True)                        # A.set_out() moves both
    C.save_json(os.path.join(A.OUT, 'abc_preflight.json'), report)
    return report

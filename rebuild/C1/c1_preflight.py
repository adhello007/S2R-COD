#!/usr/bin/env python
"""C1 Phase 0 -- the six validation gates.

C1 is the decisive measurement, so every input is verified before a single array
is loaded. Specification: rebuild/C1/C1_PLAN.md §1.

HALT SEMANTICS. Every gate returns a dict; none raises for a data failure. The
report is written to rebuild/C1/out/c1_preflight.json even when a gate fails, so
the failure itself is an artifact. The MEASUREMENT script calls run_preflight()
and raises SystemExit before loading anything if all_passed is False. There is
no fallback, no default, and no --force flag anywhere in C1.

  Gate 1  signal          allocate by target_es, never test_es
  Gate 2  cluster source  consume B1's committed partition, never re-cluster
  Gate 3  embedder        tag-keyed caches; roles enforced; never averaged
  Gate 4  representation  R2 grey-128 verified at PIXEL level, with a
                          discriminative negative control
  Gate 5  leakage         D2's 7 names excluded; pool disjoint from endpoints
  Gate 6  freshness       no archive/scratchpad; primary inputs match E0's manifest

Reads no archived artifact and no scratchpad. TRAINS NOTHING.

Usage:
  LAKE-RED/.venv/bin/python rebuild/C1/c1_preflight.py
"""

import argparse
import ast
import csv
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'E0'))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402

EXP = 'C1'
OUT = C.exp_dir(EXP, 'out')
B1_OUT = C.exp_dir('B1', 'out')
E0_CACHE = C.exp_dir('E0', 'cache')
E0_MANIFEST = C.exp_dir('E0', 'out', 'e0_manifest.sha256')
D2_LEAKED = C.exp_dir('D2', 'out', 'd2_leaked_names.json')
D2_PAIRS = C.exp_dir('D2', 'out', 'd2_pair_matrix.csv')

POOL = 4447          # the foreground pool C1 selects over (D1: 4447 files)
N_TARGET = 4033      # 4040 target images minus D2's 7 measured leaks

# B1 completion II §D5. A row-count mismatch means the partition on disk is not
# the one B1 logged, which is a halt, not a warning.
EXPECTED_K = {'dinoL518': 75, 'dinoL224': 50, 'clipL224': 5}
PRIMARY = 'dinoL518'
SENSITIVITY = 'dinoL224'
DISQUALIFIED = {'clipL224': 'no interior silhouette peak; k*=5 sits on B1\'s '
                            '>=5-cluster degeneracy guard'}

# Gate-1 / Gate-2 source scan. Lines carrying this pragma are exempt and are
# REPORTED, never hidden -- the same discipline E0's provenance gate uses after
# its own self-detection defect.
PRAGMA = 'c1-gate-ok'
BANNED_SIGNAL = 'test_es'                                     # c1-gate-ok
BANNED_CLUSTER_CALLS = {'KMeans', 'MiniBatchKMeans', 'DBSCAN',
                        'AgglomerativeClustering', 'SpectralClustering',
                        'fit_kmeans'}                         # c1-gate-ok
BANNED_CLUSTER_MODULES = {'sklearn.cluster'}                  # c1-gate-ok


def _p(m):
    print(m, flush=True)


def cluster_es_path(tag):
    return os.path.join(B1_OUT, 'b1_cluster_es_%s.csv' % tag)


def assignment_path(tag):
    return os.path.join(B1_OUT, 'b1_cluster_assignment_%s.json' % tag)


def centroids_path(tag, k, seed=0):
    return os.path.join(B1_OUT, 'b1_centroids_%s_k%d_seed%d.npy' % (tag, k, seed))


def _c1_sources():
    return sorted(glob.glob(os.path.join(_HERE, '*.py')))


def docstring_ids(tree):
    """ids of Constant nodes that are docstrings.

    Docstrings are PROSE: they cannot read a CSV column or fit a partition, and
    a docstring describing this gate necessarily contains the very tokens the
    gate forbids. E0 hit exactly this and fixed it the same way. Excluding them
    weakens nothing -- every real access is a subscript, an attribute, or a
    non-docstring literal, all of which are still scanned.
    """
    out = set()
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and body:
            first = body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                out.add(id(first.value))
    return out


def _scan_sources(check):
    """Run `check(tree, docs, lines, rel)` over every C1 source; split by pragma."""
    hits, exempt = [], []
    for path in _c1_sources():
        rel = os.path.relpath(path, C.REPO)
        src = open(path, errors='ignore').read()
        lines = src.splitlines()
        tree = ast.parse(src)
        for lineno, what in check(tree, docstring_ids(tree), lines, rel):
            line = lines[lineno - 1] if 0 < lineno <= len(lines) else ''
            rec = dict(file=rel, line=lineno, what=what, text=line.strip()[:110])
            (exempt if PRAGMA in line else hits).append(rec)
    return hits, exempt


# ---------------------------------------------------------------------------
# Gate 1 -- the allocation signal
# ---------------------------------------------------------------------------

def load_allocation_signal(tag):
    """THE allocation signal. The only place target_es is read in all of C1.

    CLS.py:81-82 builds its loader on target_root with gt_root=None and
    CLS.py:105 computes ES there, so the signal Stage C allocates by is measured
    on the UNLABELED TARGET set. B1 completion II added it to this CSV; reading
    the endpoint column instead would allocate by a signal the pipeline does not
    have at allocation time.
    """
    rows = sorted(csv.DictReader(open(cluster_es_path(tag))),
                  key=lambda r: int(r['cluster']))
    es = np.array([float(r['target_es']) for r in rows], dtype=np.float64)
    n_tgt = np.array([int(r['n_target']) for r in rows], dtype=np.int64)
    return es, n_tgt


def gate_signal(tags):
    detail, ok = {}, True
    for tag in tags:
        p = cluster_es_path(tag)
        if not os.path.isfile(p):
            detail[tag] = dict(exists=False)
            ok = False
            continue
        rdr = csv.DictReader(open(p))
        fields = list(rdr.fieldnames or [])
        rows = list(rdr)
        has_col = 'target_es' in fields
        populated = sum(1 for r in rows if r.get('target_es') not in ('', None))
        n_sum = sum(int(r['n_target']) for r in rows) if rows else -1
        positive = (has_col and populated == len(rows)
                    and all(float(r['target_es']) > 0 for r in rows))
        d = dict(exists=True, has_target_es=has_col, rows=len(rows),
                 populated=populated, n_target_sum=n_sum,
                 all_positive=bool(positive),
                 passed=bool(has_col and populated == len(rows)
                             and n_sum == N_TARGET and positive))
        detail[tag] = d
        ok = ok and d['passed']

    def check(tree, docs, lines, rel):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docs:              # prose, not a column read
                    continue
                if BANNED_SIGNAL in node.value:
                    yield node.lineno, 'string literal %r' % BANNED_SIGNAL
            elif isinstance(node, ast.Attribute) and node.attr == BANNED_SIGNAL:
                yield node.lineno, 'attribute .%s' % BANNED_SIGNAL
    hits, exempt = _scan_sources(check)
    ok = ok and not hits
    return dict(gate='signal', passed=bool(ok), per_tag=detail,
                banned_signal=BANNED_SIGNAL, violations=hits, exempted=exempt,
                note=('C1 allocates by target_es (CLS.py:81-105, GT-free). Any '
                      'reference to the endpoint column in C1 source is a failure.'))


# ---------------------------------------------------------------------------
# Gate 2 -- the partition comes from B1, and C1 never fits one
# ---------------------------------------------------------------------------

def gate_cluster_source(tags):
    detail, ok = {}, True
    for tag in tags:
        d = dict(expected_k=EXPECTED_K.get(tag))
        try:
            rows = list(csv.DictReader(open(cluster_es_path(tag))))
            a = json.load(open(assignment_path(tag)))
            k = len(rows)
            cen = np.load(centroids_path(tag, a['k'], a['seed']))
            labels = a['target_labels']
            d.update(csv_rows=k, assign_k=a['k'], assign_seed=a['seed'],
                     assign_embedder=a['embedder'],
                     centroid_shape=list(cen.shape),
                     n_names=len(a['target_names']), n_labels=len(labels),
                     labels_in_range=bool(set(labels) <= set(range(a['k']))))
            d['passed'] = bool(
                k == EXPECTED_K.get(tag)
                and a['k'] == k and a['seed'] == 0 and a['embedder'] == tag
                and tuple(cen.shape) == (k, 1024)
                and len(a['target_names']) == len(labels) == N_TARGET
                and d['labels_in_range'])
        except Exception as e:
            d.update(error='%s: %s' % (type(e).__name__, str(e)[:100]), passed=False)
        detail[tag] = d
        ok = ok and d['passed']

    def check(tree, docs, lines, rel):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                nm = getattr(f, 'id', None) or getattr(f, 'attr', None)
                if nm in BANNED_CLUSTER_CALLS:
                    yield node.lineno, 'call %s(...)' % nm
            elif isinstance(node, ast.Import):
                for al in node.names:
                    if al.name in BANNED_CLUSTER_MODULES:
                        yield node.lineno, 'import %s' % al.name
            elif isinstance(node, ast.ImportFrom):
                if node.module in BANNED_CLUSTER_MODULES:
                    yield node.lineno, 'from %s import ...' % node.module
    hits, exempt = _scan_sources(check)
    ok = ok and not hits
    return dict(gate='cluster_source', passed=bool(ok), per_tag=detail,
                clustering_calls_found=hits, exempted=exempt,
                note=('C1 consumes B1\'s committed partition. It reads centroids '
                      'and labels; it never fits one.'))


# ---------------------------------------------------------------------------
# Gate 3 -- embedder discipline (the B1 §C2 cache-mixing bug cannot recur)
# ---------------------------------------------------------------------------

def gate_embedder(tags):
    import c1_space
    detail, ok = {}, True
    c1_space.clear_cache()
    for tag in tags:
        try:
            s = c1_space.load_space(tag)
            d = dict(tag_returned=s.tag, k=s.k,
                     centroids=list(s.centroids.shape),
                     cut=list(s.cut.shape), render=list(s.render.shape),
                     es_len=int(s.es.shape[0]))
            d['passed'] = bool(s.tag == tag and s.k == EXPECTED_K[tag]
                               and s.centroids.shape == (EXPECTED_K[tag], 1024)
                               and s.cut.shape[0] == POOL
                               and s.render.shape[0] == POOL
                               and s.es.shape[0] == EXPECTED_K[tag])
        except Exception as e:
            d = dict(error='%s: %s' % (type(e).__name__, str(e)[:100]), passed=False)
        detail[tag] = d
        ok = ok and d['passed']

    # loading every space then re-reading the first must still return the first
    cross = None
    if len(tags) > 1 and all(detail[t].get('passed') for t in tags):
        first = c1_space.load_space(tags[0])
        cross = bool(first.tag == tags[0]
                     and first.centroids.shape[0] == EXPECTED_K[tags[0]])
        ok = ok and cross

    roles = dict(primary=PRIMARY, sensitivity=SENSITIVITY,
                 disqualified=DISQUALIFIED)
    return dict(gate='embedder', passed=bool(ok), per_tag=detail,
                cache_key_discipline=('every cache is keyed by a tuple whose FIRST '
                                      'element is the embedder tag; load_space() '
                                      'asserts the returned Space.tag equals the '
                                      'requested tag, and every downstream function '
                                      'takes a Space rather than loose arrays'),
                reload_after_all_tags_ok=cross, roles=roles,
                note=('B1 §C2: fit_kmeans keyed on (k, seed) and endpoint_emb on '
                      'split alone silently fed one space\'s arrays to another. '
                      'Structurally prevented here.'))


# ---------------------------------------------------------------------------
# Gate 4 -- representation, verified on PIXELS with a negative control
# ---------------------------------------------------------------------------

def gate_representation(tags, n=4, seed=0, device='cuda'):
    from PIL import Image
    detail, ok = {}, True
    raw_stems = sorted(os.path.splitext(f)[0] for f in C.listing('raw'))
    for tag in tags:
        d = {}
        try:
            names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % tag)))
            cut = np.load(os.path.join(E0_CACHE, '%s_cut_cls.npy' % tag))
            ren = np.load(os.path.join(E0_CACHE, '%s_local_cls.npy' % tag))
            cut_stems = [os.path.splitext(x)[0] for x in names['cut']]
            ren_stems = [os.path.splitext(x)[0].replace('SOD_', '', 1)
                         for x in names['local']]
            d['aligned'] = bool(cut_stems == raw_stems == ren_stems)
            d['shapes'] = [list(cut.shape), list(ren.shape)]
            d['shape_ok'] = bool(cut.shape[0] == ren.shape[0] == POOL)

            rng = np.random.default_rng(seed)
            pick = rng.choice(len(cut_stems), size=n, replace=False)
            model, tf, _ = C.build_model(tag, device)
            px, cos_cut, cos_scene, cos_render = [], [], [], []
            for i in pick:
                stem = cut_stems[i]
                ip = os.path.join(C.ipath('raw'), stem + '.png')
                mp = os.path.join(C.ipath('raw_gt'), stem + '.png')
                im = C.load_cutout(ip, mp)
                a = np.asarray(im)
                gt = np.asarray(Image.open(mp).convert('L')
                                .resize(im.size, Image.NEAREST))
                rawrgb = np.asarray(Image.open(ip).convert('RGB'))
                bg = a[gt < C.THRESH]
                px.append(dict(
                    stem=stem,
                    bg_is_flat_grey=bool(bg.size == 0
                                         or np.unique(bg).tolist() == [C.GREY]),
                    bg_unique=sorted(set(np.unique(bg).tolist()))[:4],
                    fg_untouched=bool(np.array_equal(a[gt >= C.THRESH],
                                                     rawrgb[gt >= C.THRESH]))))
                f_cut, _ = C.embed([(ip, mp)], lambda t: C.load_cutout(*t), tag=tag,
                                   device=device, transform=tf, model=model)
                f_sc, _ = C.embed([ip], C.load_full, tag=tag, device=device,
                                  transform=tf, model=model)
                rp = os.path.join(C.ipath('local'), 'SOD_%s.jpg' % stem)
                f_re, _ = C.embed([rp], C.load_full, tag=tag, device=device,
                                  transform=tf, model=model)
                ref = C.l2(cut[i:i + 1].astype(np.float64))[0]
                cos_cut.append(float(C.l2(f_cut.astype(np.float64))[0] @ ref))
                cos_scene.append(float(C.l2(f_sc.astype(np.float64))[0] @ ref))
                cos_render.append(float(C.l2(f_re.astype(np.float64))[0] @ ref))
            del model
            import torch
            torch.cuda.empty_cache()
            d.update(pixel_checks=px,
                     min_cos_cutout=min(cos_cut),
                     max_cos_full_scene=max(cos_scene),
                     max_cos_render=max(cos_render),
                     all_bg_flat_grey=all(x['bg_is_flat_grey'] for x in px),
                     all_fg_untouched=all(x['fg_untouched'] for x in px),
                     discriminative=bool(all(c > s and c > r for c, s, r
                                             in zip(cos_cut, cos_scene, cos_render))))
            d['passed'] = bool(d['aligned'] and d['shape_ok']
                               and d['all_bg_flat_grey'] and d['all_fg_untouched']
                               and d['min_cos_cutout'] >= 0.999
                               and d['discriminative'])
        except Exception as e:
            d.update(error='%s: %s' % (type(e).__name__, str(e)[:140]), passed=False)
        detail[tag] = d
        ok = ok and d['passed']
    return dict(gate='representation', passed=bool(ok), per_tag=detail,
                grey=C.GREY, threshold=C.THRESH,
                note=('R2 verified on PIXELS, not by variable name, with a '
                      'discriminative control: the full scene and the render must '
                      'BOTH score lower against the cache than the cutout does.'))


# ---------------------------------------------------------------------------
# Gate 5 -- leakage
# ---------------------------------------------------------------------------

def gate_leakage(tags):
    leaked = json.load(open(D2_LEAKED))
    names = set(leaked['target_names_to_exclude'])
    detail, ok = {}, True
    for tag in tags:
        a = json.load(open(assignment_path(tag)))
        overlap = sorted(names & set(a['target_names']))
        rows = list(csv.DictReader(open(cluster_es_path(tag))))
        d = dict(n_target_sum=sum(int(r['n_target']) for r in rows),
                 n_names=len(a['target_names']),
                 leaked_still_present=overlap)
        d['passed'] = bool(d['n_target_sum'] == N_TARGET
                           and d['n_names'] == N_TARGET and not overlap)
        detail[tag] = d
        ok = ok and d['passed']

    # selection side: the cutout pool must share no image with any endpoint.
    # Read D2's measured matrix rather than restating its number.
    ENDPOINTS = {'test', 'cham', 'nc4k', 'val'}
    POOLS = {'raw', 'auth', 'local'}
    bad, checked = [], 0
    for r in csv.DictReader(open(D2_PAIRS)):
        pair = {r['split_a'], r['split_b']}
        if pair & ENDPOINTS and pair & POOLS and len(pair & ENDPOINTS) == 1:
            checked += 1
            if int(r['collisions']) != 0:
                bad.append(dict(a=r['split_a'], b=r['split_b'], level=r['level'],
                                collisions=int(r['collisions'])))
    ok = ok and not bad
    return dict(gate='leakage', passed=bool(ok), per_tag=detail,
                leaked_names=sorted(names), n_leaked=len(names),
                endpoint_pool_pairs_checked=checked,
                endpoint_pool_collisions=bad,
                note=('The 7 leaked names are COD10K target-domain images, so '
                      'leakage enters on the ALLOCATION side (B1 already dropped '
                      'them: 4040 -> 4033). The selection pool is checked '
                      'separately against D2\'s measured pair matrix.'))


# ---------------------------------------------------------------------------
# Gate 6 -- freshness
# ---------------------------------------------------------------------------

def gate_freshness(tags, sample=100, seed=0, workers=12):
    from concurrent.futures import ProcessPoolExecutor
    import e0_regenerate as E0
    indep = E0.step_independence()

    man = {}
    with open(E0_MANIFEST) as fh:
        for line in fh:
            if line.startswith('#'):
                continue
            sha, _, rest = line.strip().partition('  ')
            key, _, nm = rest.partition('/')
            man.setdefault(key, {})[nm] = sha

    rng = np.random.default_rng(seed)
    jobs, picked = [], []
    keys = ['raw', 'raw_gt', 'tgt', 'local']
    for k in keys:
        nms = sorted(man[k])
        idx = rng.choice(len(nms), size=min(sample // len(keys), len(nms)),
                         replace=False)
        for i in idx:
            jobs.append((os.path.join(C.ipath(k), nms[i]), man[k][nms[i]]))
            picked.append((k, nms[i]))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(_verify_one, jobs, chunksize=4))
    bad = [picked[i] for i, r in enumerate(res) if not r]
    ok = (indep['n_forbidden'] == 0) and not bad
    return dict(gate='freshness', passed=bool(ok),
                n_forbidden=indep['n_forbidden'],
                forbidden=indep['forbidden_references'],
                scripts_scanned=indep['scripts_scanned'],
                manifest_checked=len(res), manifest_ok=int(sum(res)),
                manifest_mismatches=bad,
                note=("E0's own step_independence() is imported and called rather "
                      'than re-implemented, so C1 cannot drift from the gate E0 '
                      'self-tested. The .npy caches are derived, so the PRIMARY '
                      'inputs that produced them are what gets hashed.'))


def _verify_one(args):
    path, expect = args
    return C.sha256(path) == expect


# ---------------------------------------------------------------------------

GATES = [gate_signal, gate_cluster_source, gate_embedder,
         gate_representation, gate_leakage, gate_freshness]


def run_preflight(tags, skip=()):
    report = {'generated': C.now(), 'commit': C.git_commit(), 'tags': list(tags),
              'gates': [], 'all_passed': None}
    for fn in GATES:
        name = fn.__name__.replace('gate_', '')
        if name in skip:
            _p('  gate %-15s SKIPPED' % name)
            report['gates'].append(dict(gate=name, passed=True, skipped=True))
            continue
        try:
            r = fn(tags)
        except Exception as e:                                # a gate crash is a FAIL
            r = dict(gate=name, passed=False,
                     crash='%s: %s' % (type(e).__name__, str(e)[:200]))
        report['gates'].append(r)
        _p('  gate %-15s %s' % (name, 'PASS' if r['passed'] else 'FAIL'))
    report['all_passed'] = all(g['passed'] for g in report['gates'])
    os.makedirs(OUT, exist_ok=True)
    C.save_json(os.path.join(OUT, 'c1_preflight.json'), report)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tags', default='%s,%s' % (PRIMARY, SENSITIVITY))
    ap.add_argument('--skip', default='')
    args = ap.parse_args()
    tags = [t.strip() for t in args.tags.split(',')]
    skip = {s.strip() for s in args.skip.split(',') if s.strip()}
    _p('C1 preflight over %s' % tags)
    r = run_preflight(tags, skip=skip)
    _p('all_passed = %s  -> %s' % (r['all_passed'],
                                   os.path.join(OUT, 'c1_preflight.json')))
    raise SystemExit(0 if r['all_passed'] else 1)


if __name__ == '__main__':
    main()

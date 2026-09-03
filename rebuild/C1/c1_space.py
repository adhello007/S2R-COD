#!/usr/bin/env python
"""C1 -- the one loader, and the cache-key discipline that makes B1's §C2 bug
structurally impossible to repeat.

B1's completion found `fit_kmeans` cached on `(k, seed)` and `endpoint_emb` on
`split` alone, while callers passed no embedder tag. With one embedder that is
inert. With three it silently hands the second and third spaces the FIRST
space's arrays, and every "embedder-robust" conclusion becomes one cache read
three times.

Two rules here prevent it:

  1. Every cache is keyed by a tuple whose FIRST element is the embedder tag,
     and `load_space` asserts the returned Space.tag equals the requested tag
     before handing it back. A wrong-space value cannot be returned.
  2. No bare array is stored at module scope and no function takes loose arrays.
     Everything downstream takes a `Space`, which carries its own tag, so a
     wrong-space value cannot be PASSED either.

Loads only committed artifacts:
  rebuild/B1/out/b1_cluster_es_{tag}.csv          target_es  (the signal)
  rebuild/B1/out/b1_centroids_{tag}_k{k}_seed0.npy
  rebuild/B1/out/b1_cluster_assignment_{tag}.json
  rebuild/E0/cache/{tag}_cut_cls.npy              R2, selection space
  rebuild/E0/cache/{tag}_local_cls.npy            R3, measurement space

TRAINS NOTHING. Re-embeds nothing.
"""

import collections
import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import common as C                                            # noqa: E402

import numpy as np                                            # noqa: E402

B1_OUT = C.exp_dir('B1', 'out')
E0_CACHE = C.exp_dir('E0', 'cache')

Space = collections.namedtuple(
    'Space', 'tag k centroids cut render es n_target names seed')

# key IS the tag, by construction -- see rule 1 above
_SPACE_CACHE = {}


def clear_cache():
    _SPACE_CACHE.clear()


def _build_space(tag):
    a = json.load(open(os.path.join(B1_OUT,
                                    'b1_cluster_assignment_%s.json' % tag)))
    if a['embedder'] != tag:
        raise RuntimeError('assignment file for %r declares embedder %r'
                           % (tag, a['embedder']))
    k, seed = a['k'], a['seed']

    rows = sorted(csv.DictReader(open(os.path.join(
        B1_OUT, 'b1_cluster_es_%s.csv' % tag))), key=lambda r: int(r['cluster']))
    if len(rows) != k:
        raise RuntimeError('%s: cluster CSV has %d rows, assignment says k=%d'
                           % (tag, len(rows), k))
    # THE allocation signal -- target-measured, GT-free (CLS.py:81-105).
    es = np.array([float(r['target_es']) for r in rows], dtype=np.float64)
    n_target = np.array([int(r['n_target']) for r in rows], dtype=np.int64)

    cen = np.load(os.path.join(B1_OUT,
                               'b1_centroids_%s_k%d_seed%d.npy' % (tag, k, seed)))
    cut = np.load(os.path.join(E0_CACHE, '%s_cut_cls.npy' % tag))
    ren = np.load(os.path.join(E0_CACHE, '%s_local_cls.npy' % tag))
    names = json.load(open(os.path.join(E0_CACHE, '%s_names.json' % tag)))

    if cen.shape[0] != k:
        raise RuntimeError('%s: centroids %s vs k=%d' % (tag, cen.shape, k))
    if cut.shape[0] != ren.shape[0]:
        raise RuntimeError('%s: cut %s vs render %s' % (tag, cut.shape, ren.shape))

    # L2 once, here, so no downstream site can forget to normalise
    return Space(tag=tag, k=k, seed=seed,
                 centroids=C.l2(cen.astype(np.float64)),
                 cut=C.l2(cut.astype(np.float64)),
                 render=C.l2(ren.astype(np.float64)),
                 es=es, n_target=n_target,
                 names=[os.path.splitext(n)[0] for n in names['cut']])


def load_space(tag):
    """The ONLY way C1 obtains arrays. Returns a Space that carries its own tag."""
    if tag not in _SPACE_CACHE:
        _SPACE_CACHE[tag] = _build_space(tag)
    s = _SPACE_CACHE[tag]
    assert s.tag == tag, 'cache key/tag mismatch: asked %r, got %r' % (tag, s.tag)
    return s

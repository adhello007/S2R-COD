"""Point the UNCHANGED base selection code (rebuild/ABC/abc_common.py, rebuild/C1/*) at the original
working copy's gitignored data, read-only.

Only two data lookups are redirected:
  * c1_space.E0_CACHE  -> <data-root>/rebuild/E0/cache   (committed embedding cache, gitignored)
  * abc_common.base_stems() -> lists <data-root>/Dataset/Source/HKU-IS_raw/imgs
Everything else (B1 cluster files, selection functions, constants) is the base worktree's.
Callers must verify that N=1000 reproduces the committed stem files byte for byte.
"""
import os
import sys


def setup(worktree, data_root):
    for p in (os.path.join(worktree, 'rebuild'), os.path.join(worktree, 'rebuild/C1'),
              os.path.join(worktree, 'rebuild/ABC'), worktree):
        if p not in sys.path:
            sys.path.insert(0, p)
    import common as C              # noqa: F401
    import c1_space
    import abc_common as A
    c1_space.E0_CACHE = os.path.join(data_root, 'rebuild/E0/cache')
    c1_space.clear_cache()
    raw = os.path.join(data_root, 'Dataset/Source/HKU-IS_raw/imgs')

    def base_stems():
        return sorted(os.path.splitext(f)[0] for f in os.listdir(raw))
    A.base_stems = base_stems
    return A, c1_space

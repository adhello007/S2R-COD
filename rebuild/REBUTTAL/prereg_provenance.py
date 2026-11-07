#!/usr/bin/env python
"""REBUTTAL Step 1 -- the pre-registration record for OR, FX and SE, from git objects.

Answers one question the paper's Appendix B makes a claim about: were the OR, FX and
SE decision rules committed before their campaigns ran? A first audit (2026-11-07)
read only `git log` on the branch, saw 28cfd84 (2026-09-19), and got it wrong: the
files were committed at a79886a (2026-09-18 11:48), a commit a 12:05 reset later took
off the branch. This script re-derives the record from the commits and blobs
themselves, NOT from the reflog alone, so the answer does not depend on reflog
retention.

Measured here:
  * tag prereg-or-fx-se-a79886a resolves to a79886a, and a79886a is a commit
  * a79886a author and committer dates
  * FX and SE blobs byte-identical between a79886a and 28cfd84 (sha256 of blob content)
  * OR's a79886a content is an exact PREFIX of its 28cfd84 content, i.e. the only
    change is an append (Addendum A1), and SS OR.0 / OR.1 are byte-identical
  * first training step per campaign (training logs), first endpoint-derived OR
    number (MyTest per-image MAE, inference-log birth time), first OR S_alpha
    (abc_metrics.csv birth time, and the EXP OR scoring block)
  * whether the tag is visible on the configured remote

Filesystem birth/mtime values are reported AS filesystem evidence: weaker than a
git object, because a filesystem time is not content-addressed.

Trains nothing. Reads git objects and file metadata. Writes rebuild/REBUTTAL/out/.

Usage:
  .venv/bin/python rebuild/REBUTTAL/prereg_provenance.py [--no-log]
"""

import argparse
import datetime
import glob
import hashlib
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import common as C                                            # noqa: E402

OUT = os.path.join(_HERE, 'out')
TAG = 'prereg-or-fx-se-a79886a'
PREREG = 'a79886a'
RECOMMIT = '28cfd84'
FILES = {'OR': 'rebuild/OR/PREREGISTRATION_OR.md',
         'FX': 'rebuild/FX/PREREGISTRATION_FX.md',
         'SE': 'rebuild/SE/PREREGISTRATION_SE.md'}


def git(*args, check=True):
    r = subprocess.run(['git', '-C', C.REPO] + list(args), capture_output=True, text=False)
    if check and r.returncode != 0:
        raise RuntimeError('git %s failed: %s' % (' '.join(args), r.stderr.decode()))
    return r


def blob(rev, path):
    return git('show', '%s:%s' % (rev, path)).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def section(text, start, stop):
    i = text.index(start)
    j = text.index(stop, i)
    return text[i:j]


def ftime(path, which):
    st = os.stat(path)
    t = st.st_birthtime if which == 'birth' and hasattr(st, 'st_birthtime') else None
    if which == 'birth' and t is None:
        # Linux statx birth time via stat(1); os.stat does not expose it on glibc
        out = subprocess.run(['stat', '-c', '%W', path], capture_output=True, text=True).stdout.strip()
        t = float(out) if out not in ('', '0', '-') else None
    if which == 'mtime':
        t = st.st_mtime
    if t is None:
        return 'UNVERIFIED (no birth time on this filesystem)'
    return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec='seconds')


def first_step(path):
    with open(path) as fh:
        for line in fh:
            if line.startswith('['):
                return line[1:20]
    raise RuntimeError('no timestamped line in %s' % path)


def earliest(paths, key):
    vals = sorted((key(p), p) for p in paths)
    return vals[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-log', action='store_true')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    M, T, notes = [], [], []

    # --- the tag and the commit ------------------------------------------------
    full = git('rev-parse', PREREG).stdout.decode().strip()
    tag_target = git('rev-parse', TAG + '^{commit}').stdout.decode().strip()
    kind = git('cat-file', '-t', PREREG).stdout.decode().strip()
    ad, cd = git('log', '-1', '--format=%ad|%cd', '--date=iso-strict', PREREG).stdout.decode().strip().split('|')
    subj = git('log', '-1', '--format=%s', PREREG).stdout.decode().strip()
    M += [('a79886a_full_sha', full, ''),
          ('tag_%s_resolves_to' % TAG, tag_target, 'git rev-parse %s^{commit}' % TAG),
          ('a79886a_object_type', kind, 'git cat-file -t'),
          ('a79886a_author_date', ad, 'git log -1 --format=%ad'),
          ('a79886a_committer_date', cd, 'git log -1 --format=%cd'),
          ('a79886a_subject', subj, '')]
    T += [('tag %s resolves to a79886a' % TAG, tag_target == full),
          ('a79886a is a commit object', kind == 'commit')]
    reach = git('branch', '-a', '--contains', PREREG, check=False).stdout.decode().split()
    M.append(('a79886a_on_any_branch', 'yes: %s' % reach if reach else 'NO (reachable only via tag/reflog)',
              'git branch -a --contains'))
    rd = git('log', '-1', '--format=%ad|%cd', '--date=iso-strict', RECOMMIT).stdout.decode().strip().split('|')
    M.append(('28cfd84_author_committer_date', '%s / %s' % tuple(rd), 're-commit after the 2026-09-18 reset'))

    # --- the three files, blob by blob -----------------------------------------
    for k in ('FX', 'SE'):
        a, b = blob(PREREG, FILES[k]), blob(RECOMMIT, FILES[k])
        M.append(('%s_blob_sha256_a79886a' % k, sha(a), FILES[k]))
        M.append(('%s_blob_sha256_28cfd84' % k, sha(b), FILES[k]))
        T.append(('%s pre-registration byte-identical in a79886a and 28cfd84' % k, a == b))
    a, b = blob(PREREG, FILES['OR']), blob(RECOMMIT, FILES['OR'])
    M += [('OR_blob_sha256_a79886a', sha(a), FILES['OR']),
          ('OR_blob_sha256_28cfd84', sha(b), FILES['OR']),
          ('OR_bytes_a79886a_vs_28cfd84', '%d -> %d (+%d)' % (len(a), len(b), len(b) - len(a)), '')]
    T.append(('OR a79886a content is an exact prefix of its 28cfd84 content (append-only change)',
              b.startswith(a)))
    ta, tb = a.decode(), b.decode()
    for name, start, stop in (('OR.0', '## §OR.0', '## §OR.1'), ('OR.1', '## §OR.1', '## §OR.2')):
        same = section(ta, start, stop) == section(tb, start, stop)
        T.append(('§%s byte-identical between a79886a and 28cfd84' % name, same))
    appended = tb[len(ta):]
    M.append(('OR_appended_heading', appended.strip().splitlines()[2] if appended.strip() else 'none', ''))
    head = open(os.path.join(C.REPO, FILES['OR']), 'rb').read()
    T.append(('working-tree OR pre-registration equals 28cfd84 (no later edit)', head == b))
    diff = git('diff', PREREG, RECOMMIT, '--', FILES['OR']).stdout
    open(os.path.join(OUT, 'or_prereg_a79886a_to_28cfd84.diff'), 'wb').write(diff)
    for k, p in FILES.items():
        bid = git('rev-parse', '%s:%s' % (PREREG, p)).stdout.decode().strip()
        obj = os.path.join(git('rev-parse', '--git-dir').stdout.decode().strip(), 'objects', bid[:2], bid[2:])
        obj = obj if os.path.isabs(obj) else os.path.join(C.REPO, obj)
        M.append(('%s_blob_object_written' % k,
                  ftime(obj, 'mtime') if os.path.isfile(obj) else 'packed (no per-object time)',
                  'mtime of the loose object git wrote at `git add` -- filesystem evidence'))
        M.append(('%s_file_birth_on_disk' % k, ftime(os.path.join(C.REPO, p), 'birth'),
                  'filesystem birth time -- not content-addressed'))

    # --- when each campaign ran, and when the first OR number existed ----------
    snaps = 'Snapshot/ABC'
    t, p = earliest(glob.glob(os.path.join(C.REPO, snaps, '*CORACLE_s*/training_log.log')), first_step)
    M.append(('OR_first_training_step', t, os.path.relpath(p, C.REPO)))
    or_first = t
    t, p = earliest(glob.glob(os.path.join(C.REPO, snaps, '*FX_s*/training_log.log')), first_step)
    M.append(('FX_first_training_step', t, os.path.relpath(p, C.REPO)))
    fx_first = t
    se = [q for s in range(46, 51) for q in glob.glob(os.path.join(C.REPO, snaps, '*_s%d/training_log.log' % s))]
    t, p = earliest(se, first_step)
    M.append(('SE_first_new_run_step', t, os.path.relpath(p, C.REPO) + ' (seeds 46-50 are SE-only)'))
    se_first = t
    inf = glob.glob(os.path.join(C.REPO, 'rebuild/ABC/infer_*CORACLE*.log'))
    t, p = earliest(inf, lambda q: ftime(q, 'birth'))
    M.append(('OR_first_endpoint_number', t,
              '%s birth: MyTest.py prints a per-image endpoint MAE from its first image' % os.path.relpath(p, C.REPO)))
    or_num = t
    M.append(('OR_first_avg_MAE_written', ftime(p, 'mtime'), 'same log, mtime = Avg_MAE line'))
    met = os.path.join(C.REPO, 'rebuild/ABC/out/or/abc_metrics.csv')
    M.append(('OR_first_S_alpha_written', ftime(met, 'birth'),
              'rebuild/ABC/out/or/abc_metrics.csv birth; EXP OR scoring block 2026-09-18T18:23:17'))
    commit_t = cd[:19].replace('T', ' ')
    T += [('FX first training step is after the a79886a commit', fx_first > commit_t),
          ('SE first new-run training step is after the a79886a commit', se_first > commit_t),
          ('OR first training step is after the a79886a commit', or_first > commit_t),
          ('OR first endpoint-derived number is after the a79886a commit', or_num[:19].replace('T', ' ') > commit_t)]

    # --- is the tag on the remote? ---------------------------------------------
    r = git('ls-remote', '--tags', 'origin', TAG, check=False)
    remote = git('remote', 'get-url', 'origin', check=False).stdout.decode().strip() or 'none configured'
    if r.returncode == 0:
        status = 'present on origin' if r.stdout.strip() else 'NOT on origin'
    else:
        status = 'UNVERIFIED: remote unreachable from this environment (%s)' % r.stderr.decode().strip().splitlines()[0]
    M += [('remote_origin', remote, ''), ('tag_on_remote', status, 'git ls-remote --tags origin')]

    notes = (
        'POST-HOC PROVENANCE AUDIT, not an experiment. Re-derives from git objects whether the OR/FX/SE decision rules were committed before their campaigns ran, correcting a first audit (2026-11-07) that read branch history only.\n'
        'FINDING: OR, FX and SE pre-registrations were committed together at a79886a. A reset at 2026-09-18 12:05 removed that commit from the branch, and the same files were re-committed as 28cfd84 (2026-09-19). FX and SE are byte-identical between the two. OR differs only by an appended, dated Addendum A1, with §OR.0 and §OR.1 byte-identical.\n'
        'FX and SE trained only after a79886a. OR trained BEFORE it: OR runs launched at 10:46, about 62 min before the commit, from a file whose filesystem birth time is 10:44. Git records OR text only from the 11:47:56 staging, so the content at launch is not established by git. No OR endpoint-derived number existed before the commit: the first is a MyTest per-image MAE at 16:51, and S_alpha follows at 18:23. The OR decision rule is the ABC 2*sigma_hat / sign rule frozen at 065dac6, applied to a new arm.\n'
        'Filesystem times are reported as filesystem evidence and are weaker than git objects. a79886a is on no branch; the tag preserves it locally. Whether the tag is on the remote is the tag_on_remote line.')
    text = C.log_block('REBUTTAL_PREREG_PROVENANCE', '.venv/bin/python rebuild/REBUTTAL/prereg_provenance.py',
                       M, thresholds=T, artifacts=['rebuild/REBUTTAL/out/or_prereg_a79886a_to_28cfd84.diff'],
                       notes=notes, write=not args.no_log)
    print(text)


if __name__ == '__main__':
    main()

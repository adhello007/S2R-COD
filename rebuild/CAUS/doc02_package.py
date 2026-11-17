#!/usr/bin/env python
"""CAUS DOC-02 -- code patch, link check, character count, archive + checksums.

1. STUDENT_RESULTS/CODE_CHANGES.patch = `git diff 8d1d079 HEAD -- rebuild/CAUS` (all source added for this
   reviewer; no committed file outside rebuild/CAUS was changed).
2. Link check over every .md in ICLR2027_REBUTTAL_Caus/: markdown links [..](path) and backticked paths
   that name a file or folder under STUDENT_RESULTS (RESULT_TABLES/, EXPERIMENT_LOGS/, FIGURES/, ...).
   Each must resolve relative to the .md file or to STUDENT_RESULTS/. URLs are skipped. Any miss is a
   non-zero exit.
3. Unicode character count of FINAL_UPDATED_REBUTTAL_OPENREVIEW_5000.md (limit 5000, Markdown as text).
4. STUDENT_RESULTS/SHA256SUMS over every file, then ../STUDENT_RESULTS_<date>.tar.gz and its .sha256.
Usage: doc02_package.py [--archive]
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tarfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import caus_common as K                                        # noqa: E402

TOP = os.path.dirname(K.CAUS_OUT)                              # ICLR2027_REBUTTAL_Caus/
SR = K.CAUS_OUT
LINK = re.compile(r'\]\(([^)\s]+)\)')
TICK = re.compile(r'`([^`\s]+)`')
STEMS = ('RESULT_TABLES/', 'EXPERIMENT_LOGS/', 'FIGURES/', '../FIGURES/', '../manuscript_scope_edits.patch',
         'manuscript_scope_edits.patch', 'CODE_CHANGES.patch', 'FINAL_', 'RESULTS_SUMMARY', 'EXPERIMENTAL_EVIDENCE',
         'EXECUTION_STATUS', 'AN-0', 'TH-0', 'DOC-0', 'EXP-01')


def code_patch():
    d = subprocess.run(['git', 'diff', K.BASE_COMMIT, 'HEAD', '--', 'rebuild/CAUS'], cwd=K.REPO,
                       capture_output=True, text=True, check=True).stdout
    p = os.path.join(SR, 'CODE_CHANGES.patch')
    K.assert_writable(p)
    with open(p, 'w') as fh:
        fh.write('# All source added for Reviewer Caus: git diff %s HEAD -- rebuild/CAUS\n' % K.BASE_COMMIT[:7])
        fh.write('# No committed file outside rebuild/CAUS was modified by this work.\n')
        fh.write(d)
    return p, d.count('\ndiff --git') + (1 if d.startswith('diff --git') else 0)


def candidates(text):
    out = set(LINK.findall(text))
    for t in TICK.findall(text):
        t = t.rstrip('.,;:)')
        if t.startswith(STEMS) and ('/' in t or t.endswith(('.md', '.csv', '.patch', '.json', '.log', '.png', '.jpg'))):
            out.add(t)
    return {c for c in out if not c.startswith(('http://', 'https://', '#'))}


def link_check():
    misses, n = [], 0
    for root, _, files in os.walk(TOP):
        for f in files:
            if not f.endswith('.md') or f.startswith('03_'):
                continue
            p = os.path.join(root, f)
            for c in candidates(open(p, encoding='utf-8').read()):
                if '*' in c or '<' in c or '{' in c:
                    continue                                   # patterns / templates, not paths
                n += 1
                c0 = c.split('#')[0]
                ok = any(os.path.exists(os.path.normpath(os.path.join(b, c0)))
                         for b in (root, SR, os.path.join(SR, 'EXPERIMENT_LOGS'), os.path.join(SR, 'RESULT_TABLES'), K.REPO))
                if not ok:
                    misses.append('%s: %s' % (os.path.relpath(p, TOP), c))
    return n, misses


def checksums():
    lines = []
    for root, _, files in os.walk(SR):
        for f in sorted(files):
            p = os.path.join(root, f)
            if os.path.relpath(p, SR) == 'SHA256SUMS':
                continue
            lines.append('%s  %s' % (K.sha256(p), os.path.relpath(p, SR)))
    lines.sort(key=lambda s: s.split('  ', 1)[1])
    out = os.path.join(SR, 'SHA256SUMS')
    K.assert_writable(out)
    open(out, 'w').write('\n'.join(lines) + '\n')
    return len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', action='store_true')
    args = ap.parse_args()
    p, nfiles = code_patch()
    print('CODE_CHANGES.patch: %d files' % nfiles)
    f5 = os.path.join(SR, 'FINAL_UPDATED_REBUTTAL_OPENREVIEW_5000.md')
    if os.path.isfile(f5):
        n = len(open(f5, encoding='utf-8').read())
        print('OpenReview copy: %d Unicode characters (limit 5000) -> %s' % (n, 'OK' if n <= 5000 else 'OVER'))
    n, misses = link_check()
    print('link check: %d path references, %d unresolved' % (n, len(misses)))
    for m in misses:
        print('  MISSING', m)
    if args.archive:
        if misses:
            raise SystemExit('refusing to archive with unresolved links')
        k = checksums()
        name = os.path.join(TOP, 'STUDENT_RESULTS_%s.tar.gz' % time.strftime('%Y%m%d'))
        K.assert_writable(name)
        with tarfile.open(name, 'w:gz') as tf:
            tf.add(SR, arcname='STUDENT_RESULTS')
        h = K.sha256(name)
        open(name + '.sha256', 'w').write('%s  %s\n' % (h, os.path.basename(name)))
        print('archive %s (%d files checksummed) sha256 %s' % (os.path.relpath(name, K.REPO), k, h))
    sys.exit(1 if misses else 0)


if __name__ == '__main__':
    main()

"""§10 link check: every path referenced in a Markdown file under STUDENT_RESULTS/ must exist.

A reference is any backticked token that contains '/' or ends in a file extension. Each one is resolved
against, in order: the Markdown file's own folder, STUDENT_RESULTS/, ICLR2027_REBUTTAL/ and the repository
root. Brace lists ({a,b}) are expanded; tokens with '*' or '<…>' placeholders are checked as globs and must
match at least one file; command lines (tokens with spaces) contribute each path-like word. Tokens that are
plainly not paths (flags, CLI options, numbers, and expected outputs not yet produced, which the file itself
marks with "exist after") are skipped and listed.

Usage: python analysis/path_check.py     (exit 1 if any reference is missing)
Writes EXPERIMENT_LOGS/path_check.log.
"""
import datetime
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDENT = os.path.dirname(HERE)
REB = os.path.dirname(STUDENT)
REPO = os.path.abspath(os.path.join(REB, '..', '..', '..'))
EXT = r'\.(md|csv|json|tex|pdf|png|py|sh|log|txt|patch|diff|hash|bib|sty|bst|npy|jsonl|zip|pth|sha256)$'


def expand(tok):
    m = re.search(r'\{([^{}]*,[^{}]*)\}', tok)
    if not m:
        return [tok]
    return [x for alt in m.group(1).split(',') for x in expand(tok[:m.start()] + alt + tok[m.end():])]


def candidates(tok):
    words = tok.split() if ' ' in tok else [tok]
    out = []
    for w in words:
        w = w.strip('`"\'(),;:').rstrip('.')
        w = re.sub(r':\d+(-\d+)?$', '', w)               # file.py:12
        if not w or w.startswith('-') or '=' in w or w.startswith('http'):
            continue
        for part in w.split('|'):
            if len(part) > 3 and ('/' in part or re.search(EXT, part)):
                out.extend(expand(part))
    return out


SEARCH = [os.path.join(STUDENT, d) for d in ('analysis', 'RESULT_TABLES', 'revision', 'prereg', 'EXPERIMENT_LOGS')] + \
         [REB, REPO] + [os.path.join(REPO, 'rebuild', d) for d in ('RL5B', 'ABC', 'ABC/out/cdr', 'DIAG', 'REBUTTAL')]
# References the Markdown files themselves declare absent or superseded; each is listed in the log with its reason.
DECLARED = {
    '02_REVIEWER_CONCERN_AND_ACTION_MATRIX.md': 'not supplied by the author; recorded as missing (deviation 9)',
    'EXP02_allocations.csv': 'not a separate file; the record is rebuild/ABC/out/cdr/cdr_allocations.csv (deviation 23)',
    'EXPERIMENT_LOGS/EXP01_autorun.log': 'created by the cron trigger when it fires after the cutoff (deviation 21)',
    'Snapshot/RL5B/bridge/SINet_C10_s42': 'superseded by the file\'s own amendment: Snapshot/RL5B/bridge/BRIDGE_SINet_C10_s42',
}


def git_ok(tok):
    import subprocess
    if re.fullmatch(r'(origin/)?rebuttal/iclr27/wip\d', tok):
        return subprocess.run(['git', '-C', REPO, 'rev-parse', '--verify', '-q', tok], capture_output=True).returncode == 0, 'git ref'
    if subprocess.run(['git', '-C', REPO, 'cat-file', '-e', '8d1d079:' + tok], capture_output=True).returncode == 0:
        return True, 'exists at the base commit 8d1d079 (removed later by the author)'
    return False, ''


def resolve(tok, md_dir):
    if exists(tok, md_dir):
        return True, ''
    if '/' not in tok:                                    # a bare file name: look in the known folders
        for d in SEARCH:
            if os.path.exists(os.path.join(d, tok)):
                return True, ''
        if tok.endswith('.pth') and any(glob.glob(os.path.join(REPO, 'Snapshot', *(['*'] * k), tok)) for k in (2, 3)):
            return True, ''
    m = re.fullmatch(r'(.+)\.(\w+)', tok)                 # module.function, e.g. rebuild/ABC/abc_evaluate.score
    if m and not re.search(EXT, tok) and exists(m.group(1) + '.py', md_dir):
        return True, ''
    ok, why = git_ok(tok)
    if ok:
        return True, why
    if tok in DECLARED:
        return None, DECLARED[tok]
    return False, ''


def exists(path, md_dir):
    for base in (md_dir, STUDENT, REB, REPO):
        p = os.path.normpath(os.path.join(base, path))
        if '*' in path or '<' in path:
            pat = re.sub(r'<[^>]*>', '*', p)
            if glob.glob(pat):
                return True
        elif os.path.exists(p):
            return True
    return False


def main():
    mds = sorted(glob.glob(os.path.join(STUDENT, '**', '*.md'), recursive=True))
    mds = [m for m in mds if '/build_' not in m and '/__pycache__/' not in m]
    lines, missing, n_ok, skipped, notes, declared = [], [], 0, [], [], []
    for md in mds:
        text = open(md, encoding='utf-8').read()
        rel = os.path.relpath(md, STUDENT)
        for ln, line in enumerate(text.splitlines(), 1):
            pending = 'exist after' in line or 'Artifacts (exist after' in line
            for tok in re.findall(r'`([^`]+)`', line):
                for c in candidates(tok):
                    ok, why = resolve(c, os.path.dirname(md))
                    if ok:
                        n_ok += 1
                        if why:
                            notes.append('%s:%d  %s  (%s)' % (rel, ln, c, why))
                    elif ok is None:
                        declared.append('%s:%d  %s  (%s)' % (rel, ln, c, why))
                    elif pending:
                        skipped.append('%s:%d  %s  (declared as produced later)' % (rel, ln, c))
                    else:
                        missing.append('%s:%d  %s' % (rel, ln, c))
    lines.append('# path_check (%s): %d Markdown files under STUDENT_RESULTS/' % (
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), len(mds)))
    lines += ['  ' + os.path.relpath(m, STUDENT) for m in mds]
    lines.append('references resolved: %d' % n_ok)
    lines.append('resolved through git (ref, or the base commit): %d' % len(notes))
    lines += ['  ' + s for s in notes]
    lines.append('declared absent or superseded by the file itself: %d' % len(declared))
    lines += ['  ' + s for s in declared]
    lines.append('declared as produced later (not yet required): %d' % len(skipped))
    lines += ['  ' + s for s in skipped]
    lines.append('MISSING: %d' % len(missing))
    lines += ['  ' + m for m in missing]
    lines.append('RESULT: %s' % ('PASS' if not missing else 'FAIL'))
    open(os.path.join(STUDENT, 'EXPERIMENT_LOGS', 'path_check.log'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()

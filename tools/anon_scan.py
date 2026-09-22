#!/usr/bin/env python3
"""
Anonymity gate for the ICLR anonymous supplement.

Extends the pattern list already exercised in
rebuild/D2_reaudit/d2r_reaudit.py:847, which certified the standalone detector
bundle (`anonymization_scan_clean = True` in results/REBUILD_LOG.txt).

That list was written for a four-file bundle, so it treated the repository's own
directory names (Dataset/, Snapshot/, rebuild/, ...) as fatal. Here those names
ARE the documented layout and appear thousands of times legitimately, so they
drop to a warn tier and the fatal tier carries only what actually identifies a
person, a machine or an account.

Usage
-----
    python tools/anon_scan.py <dir>            # scan a built supplement
    python tools/anon_scan.py <dir> --verbose  # list warns too

Exit 0 = safe to ship. Exit 1 = at least one FATAL hit.
"""

import argparse
import os
import re
import subprocess
import sys

# --- what actually de-anonymises ------------------------------------------
# (pattern, human-readable reason)
FATAL = [
    (r'/home/',                      'absolute path reveals the account name'),
    (r'ai-server',                   'machine hostname'),
    (r'[Aa]kshat',                   'author given name'),
    (r'[Dd]obhal',                   'author family name'),
    (r'imagine\.io',                 'author email domain'),
    (r'adhello007',                  'author GitHub account'),
    (r'akshatdobhal17@gmail\.com',   'author email'),
    (r'1650020800@qq\.com',          'upstream author email'),
    (r'[\w.+-]+@[\w-]+\.(?:com|org|net|edu|ac\.\w+)', 'email address'),
]

# --- legitimate, but re-read before shipping ------------------------------
WARN = [
    (r'github\.com/',        'third-party project links are fine; a link to OUR repo is not'),
    (r'\.venv',              'local venv path; harmless but check it is not absolute'),
    (r'[Mm]uscape',          'upstream copyright holder; expected in LICENSE only'),
    (r'experiments/lakered', 'internal branch name'),
    (r'S2R-COD/',            'repo directory name'),
]

# --- occurrences that are themselves evidence and must not be edited ------
# These files legitimately CONTAIN the pattern list, because they are the
# record of the scan that used it. Editing them to satisfy the scanner would
# corrupt the evidence trail, so they are whitelisted by (path, pattern).
WHITELIST = {
    # The ANON_PATTERNS literal and the log lines echoing it keep the STRUCTURAL
    # tokens (/home/, ai-server) as a record of what was scanned for. The
    # author-identifying tokens in them are redacted by build_supplement.sh --
    # they are deliberately NOT whitelisted here, so if the redaction ever
    # regresses this gate fails.
    'rebuild/D2_reaudit/d2r_reaudit.py': {r'/home/'},
    'results/REBUILD_LOG.txt':           {r'/home/'},
    # MIT requires the upstream copyright notice be preserved verbatim
    'LICENSE':                           {r'[Mm]uscape'},
    # third-party attribution header: the DGNet/PySODMetrics author, not a
    # submitting author. Removing it would strip required credit.
    'Eval/metrics.py':                   {r'[\w.+-]+@[\w-]+\.(?:com|org|net|edu|ac\.\w+)'},
    # the re-audit plan quotes the anonymisation pattern list in prose
    'rebuild/D2_reaudit/REAUDIT_PLAN.md': {r'/home/'},
    # this gate's own source and the build script that drives it
    'tools/anon_scan.py':                {p for p, _ in FATAL} | {p for p, _ in WARN},
    'tools/build_supplement.sh':         {p for p, _ in FATAL} | {p for p, _ in WARN},
}

SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', '.mypy_cache'}
BINARY_EXT = {'.pth', '.ckpt', '.npy', '.npz', '.zip', '.rar', '.tar', '.gz',
              '.jpg', '.jpeg', '.png', '.tif', '.pkl', '.mat', '.so'}
PDF_FIELDS = ('Author', 'Creator', 'Producer', 'Title', 'Subject', 'Keywords')


def _whitelisted(rel, pattern):
    return pattern in WHITELIST.get(rel, ())


def scan_text(root):
    fatal, warn = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            if os.path.splitext(fn)[1].lower() in BINARY_EXT:
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='strict') as fh:
                    lines = fh.readlines()
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable; handled by scan_binaries
            for tier, bucket in ((FATAL, fatal), (WARN, warn)):
                for pat, why in tier:
                    if _whitelisted(rel, pat):
                        continue
                    rx = re.compile(pat)
                    for i, line in enumerate(lines, 1):
                        if rx.search(line):
                            bucket.append((rel, i, pat, why, line.strip()[:120]))
    return fatal, warn


def scan_binaries(root):
    """PDF/image metadata is the classic leak a text grep cannot see."""
    findings, checked = [], 0
    have_pdfinfo = subprocess.run(['which', 'pdfinfo'],
                                  capture_output=True).returncode == 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.lower().endswith('.pdf'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            checked += 1
            if not have_pdfinfo:
                findings.append((rel, 'pdfinfo not installed - CHECK BY HAND'))
                continue
            out = subprocess.run(['pdfinfo', path],
                                 capture_output=True, text=True).stdout
            for line in out.splitlines():
                key, _, val = line.partition(':')
                if key.strip() in PDF_FIELDS and val.strip():
                    for pat, _why in FATAL:
                        if re.search(pat, val):
                            findings.append((rel, '%s: %s' % (key.strip(), val.strip())))
    return findings, checked


def scan_vcs(root):
    """A clone, a venv or a cache in the zip leaks history or absolute paths."""
    bad = []
    for dirpath, dirnames, filenames in os.walk(root):
        for d in list(dirnames):
            if d in ('.git', '.venv', '__pycache__', '.claude', '.agents'):
                bad.append(os.path.relpath(os.path.join(dirpath, d), root))
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--verbose', action='store_true', help='list warn-tier hits')
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    print('anon_scan: %s\n' % root)

    vcs = scan_vcs(root)
    fatal, warn = scan_text(root)
    pdfs, n_pdf = scan_binaries(root)

    if vcs:
        print('VCS/ENV DIRECTORIES PRESENT  (%d)' % len(vcs))
        for p in sorted(set(vcs)):
            print('   %s' % p)
        print()

    if fatal:
        print('FATAL  (%d)' % len(fatal))
        for rel, ln, pat, why, text in fatal:
            print('   %s:%d  [%s]  %s' % (rel, ln, why, text))
        print()

    if pdfs:
        print('PDF METADATA  (%d)' % len(pdfs))
        for rel, detail in pdfs:
            print('   %s  %s' % (rel, detail))
        print()

    if warn:
        by_pat = {}
        for rel, ln, pat, why, text in warn:
            by_pat.setdefault((pat, why), []).append('%s:%d' % (rel, ln))
        print('WARN  (%d hits, %d patterns)' % (len(warn), len(by_pat)))
        for (pat, why), hits in sorted(by_pat.items()):
            print('   %-22s %4d hits  -- %s' % (pat, len(hits), why))
            if args.verbose:
                for h in hits[:40]:
                    print('        %s' % h)
                if len(hits) > 40:
                    print('        ... and %d more' % (len(hits) - 40))
        print()

    print('%d PDFs checked' % n_pdf)
    failed = bool(fatal or vcs or pdfs)
    print('\nRESULT: %s' % ('FAIL' if failed else 'PASS'))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

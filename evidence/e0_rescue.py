"""E0 -- artifact rescue, hash manifest, environment capture.

Objective
    Move every irreplaceable audit artifact off the volatile /tmp session path
    into evidence/artifacts/, hash it, and stamp the environment -- before any
    measurement runs.

Why this is the gate
    The six noise-floor prediction directories are the ONLY copy. Losing them
    means C3 -- the noise floor, which is the denominator of the whole decisive
    argument (0.031 sigma against a 2 sigma bar) -- could only be restored by
    6 x 1.8 h of retraining, which is exactly the retraining this package is
    specified to avoid. The per-seed checkpoints are likewise the only copy of
    the four independent runs behind B1's cross-run replication.

    This script also vendors evidence/sources/PRIOR_REVIEW.md out of
    ~/.claude/plans/, which is outside the repo and outside git yet is the sole
    source for C2's retraction table and part of D2's expected values.

Trains anything?  NO -- this is a copy-and-hash step.

Usage
    LAKE-RED/.venv/bin/python evidence/e0_rescue.py [--dry-run]
"""

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

RUNS = ['s42', 's43', 's45', 's46', 'repB', 'repC']
CKPTS = ['Stu_40.pth', 'Tea_epoch_best.pth']
PRED_FILES_PER_RUN = 2026

# Sa per run, recomputed in the audit from the prediction files with the repo's
# own Eval/metrics.py. E0 only checks that the rescued audit6.json still carries
# them; C3 recomputes them from the pixels.
EXPECTED_SA = {'s42': 0.7022, 's43': 0.7005, 's45': 0.6961,
               's46': 0.6971, 'repB': 0.7058, 'repC': 0.7016}

PRIOR_REVIEW_SRC = os.path.expanduser('~/.claude/plans/hazy-launching-eclipse.md')
# Only the IMMUTABLE sources are hashed. EVIDENCE_APPROACH.md and
# EVIDENCE_SCRIPTS.md are deliberately excluded: they are living deliverables,
# corrected in place whenever a measured value disagrees with an expected one,
# so hashing them would guarantee a stale manifest. Their integrity comes from
# git history, which is the right tool for a mutable text file.
IN_REPO_SOURCES = ['STAGE_C_MEASUREMENTS.md', 'STAGE_C_RED_TEAM_AUDIT.md']


def copy_file(src, dst, dry):
    if not os.path.exists(src):
        return False
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    return True


def copy_tree(src, dst, dry):
    if not os.path.isdir(src):
        return 0
    if not dry:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    return len([f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true',
                    help='report what would be copied, write nothing')
    ap.add_argument('--note', default='',
                    help='extra line appended to the log block NOTES field')
    opt = ap.parse_args()
    dry = opt.dry_run

    nf = os.path.join(C.SCRATCH, 'noisefloor')
    if not os.path.isdir(nf):
        sys.exit('FATAL: scratchpad gone: %s\nThe noise-floor predictions cannot '
                 'be regenerated without retraining.' % nf)

    for d in (C.ARTIFACTS, C.MANIFESTS, C.SOURCES, C.OUT):
        if not dry:
            os.makedirs(d, exist_ok=True)

    report, missing = [], []

    # ---- 1. prediction directories (the irreplaceable part) ----------------
    pred_counts = {}
    for run in RUNS:
        n = copy_tree(os.path.join(nf, 'pred_%s' % run),
                      os.path.join(C.ARTIFACTS, 'pred_%s' % run), dry)
        pred_counts[run] = n
        report.append('pred_%-5s %5d files' % (run, n))
        if n != PRED_FILES_PER_RUN:
            missing.append('pred_%s has %d files, expected %d'
                           % (run, n, PRED_FILES_PER_RUN))

    # ---- 2. the two load-bearing checkpoints per run ----------------------
    ck_ok = 0
    for run in RUNS:
        for ck in CKPTS:
            if copy_file(os.path.join(nf, 'snap_%s' % run, ck),
                         os.path.join(C.ARTIFACTS, 'snap_%s' % run, ck), dry):
                ck_ok += 1
            else:
                missing.append('snap_%s/%s' % (run, ck))
    report.append('checkpoints  %d/%d' % (ck_ok, len(RUNS) * len(CKPTS)))
    # The other 15 checkpoints per run (~17 GB) are deliberately NOT rescued.

    # ---- 3. feature caches and per-image score files ----------------------
    caches = 0
    for fn in sorted(os.listdir(C.SCRATCH)):
        if fn.endswith(('.npy', '.json')):
            if copy_file(os.path.join(C.SCRATCH, fn),
                         os.path.join(C.ARTIFACTS, fn), dry):
                caches += 1
    report.append('feature caches / score json  %d files' % caches)

    # ---- 4. original scripts and run logs (provenance, not inputs) --------
    meta = 0
    for fn in sorted(os.listdir(nf)):
        if fn.endswith(('.json', '.py', '.sh', '.log')):
            if copy_file(os.path.join(nf, fn),
                         os.path.join(C.ARTIFACTS, 'noisefloor_meta', fn), dry):
                meta += 1
    for fn in sorted(os.listdir(C.SCRATCH)):
        if fn.endswith(('.py', '.md')):
            if copy_file(os.path.join(C.SCRATCH, fn),
                         os.path.join(C.ARTIFACTS, 'scripts_original', fn), dry):
                meta += 1
    report.append('original scripts + logs  %d files' % meta)

    # ---- 5. vendor the third source document ------------------------------
    prior = os.path.join(C.SOURCES, 'PRIOR_REVIEW.md')
    if copy_file(PRIOR_REVIEW_SRC, prior, dry):
        report.append('vendored PRIOR_REVIEW.md  from ~/.claude/plans/')
    else:
        missing.append('PRIOR_REVIEW.md source (%s)' % PRIOR_REVIEW_SRC)

    if dry:
        print('\n'.join(report))
        print('\nDRY RUN -- nothing written.')
        if missing:
            print('MISSING:\n  ' + '\n  '.join(missing))
        return

    # ---- 6. hash everything ----------------------------------------------
    # Singleton files go into a sha256sum-compatible manifest, verifiable with
    # `sha256sum -c` from the repo root. The 12k prediction PNGs get one
    # aggregate digest per directory (the full per-file listing stays beside
    # them in the gitignored artifacts dir), so the committed manifest stays
    # readable instead of being a megabyte of hashes.
    singles = []
    for root, _dirs, files in os.walk(C.ARTIFACTS):
        if os.path.basename(root).startswith('pred_'):
            continue
        for fn in sorted(files):
            if fn.endswith('.sha256'):
                continue
            p = os.path.join(root, fn)
            singles.append((C.sha256(p), os.path.relpath(p, C.REPO)))
    with open(os.path.join(C.MANIFESTS, 'MANIFEST.sha256'), 'w') as fh:
        for h, rel in sorted(singles, key=lambda x: x[1]):
            fh.write('%s  %s\n' % (h, rel))

    digests = {}
    for run in RUNS:
        d = os.path.join(C.ARTIFACTS, 'pred_%s' % run)
        lines = ['%s  %s' % (C.sha256(os.path.join(d, fn)),
                             os.path.relpath(os.path.join(d, fn), C.REPO))
                 for fn in sorted(os.listdir(d))]
        with open(os.path.join(C.ARTIFACTS, 'pred_%s.sha256' % run), 'w') as fh:
            fh.write('\n'.join(lines) + '\n')
        import hashlib
        digests[run] = hashlib.sha256(
            ('\n'.join(lines) + '\n').encode()).hexdigest()
    with open(os.path.join(C.MANIFESTS, 'PRED_DIGESTS.txt'), 'w') as fh:
        fh.write('# Aggregate digest per prediction directory.\n'
                 '# digest = sha256 of the sorted "<sha256>  <filename>" listing,\n'
                 '# which is written in full to evidence/artifacts/pred_<run>.sha256\n'
                 '# (gitignored). Paths are repo-relative, so from the repo root:\n'
                 '#   sha256sum -c evidence/artifacts/pred_<run>.sha256\n'
                 '# And to check the listing itself against the digest below:\n'
                 '#   sha256sum < evidence/artifacts/pred_<run>.sha256\n\n')
        for run in RUNS:
            fh.write('pred_%-6s files=%d  digest=%s\n'
                     % (run, pred_counts[run], digests[run]))

    src_hashes = []
    for rel in IN_REPO_SOURCES:
        p = os.path.join(C.REPO, rel)
        if os.path.exists(p):
            src_hashes.append((C.sha256(p), rel))
    src_hashes.append((C.sha256(prior), os.path.relpath(prior, C.REPO)))
    with open(os.path.join(C.MANIFESTS, 'SOURCES.sha256'), 'w') as fh:
        for h, rel in sorted(src_hashes, key=lambda x: x[1]):
            fh.write('%s  %s\n' % (h, rel))

    # ---- 7. verify the rescued noise-floor values -------------------------
    a6 = json.load(open(os.path.join(C.ARTIFACTS, 'noisefloor_meta', 'audit6.json')))
    got = {k: round(v['Sa'], 4) for k, v in a6.items()}
    sa_ok = got == EXPECTED_SA

    # ---- 8. environment capture ------------------------------------------
    env = C.env_stamp()
    env['dinov2_primary'] = 'timm/vit_large_patch14_dinov2.lvd142m'
    env['dinov2_secondary'] = 'timm/vit_base_patch14_dinov2.lvd142m'
    env['n_super_pix'] = 16
    env['scratch_source'] = C.SCRATCH
    env['rescued_bytes'] = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _d, fs in os.walk(C.ARTIFACTS) for f in fs)
    with open(os.path.join(C.OUT, 'e0_environment.json'), 'w') as fh:
        json.dump(env, fh, indent=2, sort_keys=True)

    total_pred = sum(pred_counts.values())
    gb = env['rescued_bytes'] / 1024 ** 3

    metrics = [('prediction_dirs_rescued', len(RUNS), 'pred_{s42,s43,s45,s46,repB,repC}'),
               ('prediction_files_total', total_pred, '6 x %d' % PRED_FILES_PER_RUN),
               ('checkpoints_rescued', '%d/%d' % (ck_ok, len(RUNS) * len(CKPTS)),
                'Stu_40.pth + Tea_epoch_best.pth per run'),
               ('feature_cache_files', caches, 'dinoB/L/L518 + InceptionV3 + score json'),
               ('provenance_files', meta, 'original scripts and run logs'),
               ('manifest_lines_singletons', len(singles), 'MANIFEST.sha256'),
               ('rescued_size_gib', '%.2f' % gb, ''),
               ('sa_values_rescued', json.dumps(got, sort_keys=True), 'audit6.json')]

    thresholds = [('every pred_* dir has %d files' % PRED_FILES_PER_RUN,
                   all(n == PRED_FILES_PER_RUN for n in pred_counts.values())),
                  ('all %d checkpoints present' % (len(RUNS) * len(CKPTS)),
                   ck_ok == len(RUNS) * len(CKPTS)),
                  ('PRIOR_REVIEW.md vendored', os.path.exists(prior)),
                  ('rescued Sa values match the audit to 4 dp', sa_ok)]

    expected = [('prediction files', 12156, 'MATCH' if total_pred == 12156 else 'MISMATCH'),
                ('Sa per run (6 runs)',
                 '0.6961/0.6971/0.7005/0.7016/0.7022/0.7058',
                 'MATCH' if sa_ok else 'MISMATCH')]

    notes = (
        'Copies only -- the originals in the scratchpad are left untouched.\n'
        'Deliberately NOT rescued: the other 15 checkpoints per run (~17 GB); they are '
        'not load-bearing for any experiment in this package.\n'
        'snap_s44 holds no checkpoints -- train_s44.log shows the run died just after '
        'loading the dataloaders. That is the "5th distinct seed NOT RUN" item in '
        'STAGE_C_RED_TEAM_AUDIT.md (d)(3); its logs are rescued as evidence of the '
        'failed attempt.\n'
        'Two live breakages recorded in the surviving code: audit6.py hardcodes the '
        'scratchpad path AND Dataset/Test/GT, which is now Dataset/Test/COD10K/GT. C3 '
        'ships a corrected-path port rather than the original.\n'
        'evidence/artifacts/ is gitignored (~3.5 GB, and *.pth is ignored repo-wide). '
        'The manifests under evidence/manifests/ ARE committed, so inputs are verified '
        'by checksum rather than by checkout. This is a real limitation of the package.\n'
        'PRIOR_REVIEW.md is vendored from ~/.claude/plans/hazy-launching-eclipse.md, '
        'which is outside the repo and outside git -- it is the sole source for C2 '
        'section 0.7-D1 (the "raise B" retraction) and part of D2 section 0.5.')
    if opt.note:
        notes += '\n' + opt.note

    block = C.log_block(
        exp='E0',
        cmd='LAKE-RED/.venv/bin/python evidence/e0_rescue.py',
        metrics=metrics, thresholds=thresholds, expected=expected,
        artifacts=['evidence/manifests/MANIFEST.sha256',
                   'evidence/manifests/PRED_DIGESTS.txt',
                   'evidence/manifests/SOURCES.sha256',
                   'evidence/out/e0_environment.json',
                   'evidence/sources/PRIOR_REVIEW.md'],
        revision='none (this step establishes provenance for the rest)',
        trains='NO', notes=notes, env=env)

    print('\n'.join(report))
    if missing:
        print('\nMISSING:\n  ' + '\n  '.join(missing))
    print('\n' + block)


if __name__ == '__main__':
    main()

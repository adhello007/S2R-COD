"""Build results/RESULTS_SUMMARY.md from the append-only results log.

Objective
    Give a reader -- and anyone writing the results up -- one quotable page:
    every experiment, its status, its headline numbers, whether its thresholds
    passed, and whether it agreed with the prior audits. Regenerated from the
    log rather than maintained by hand, so it cannot drift from the evidence.

    This is NOT an experiment: it reads the log and writes a summary. It never
    appends a block.

Usage
    LAKE-RED/.venv/bin/python evidence/summarize_log.py
    LAKE-RED/.venv/bin/python evidence/summarize_log.py --check   # CI: stale?

Outputs
    results/RESULTS_SUMMARY.md    human-readable, for quoting
    results/RESULTS_SUMMARY.json  same content, machine-readable
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

# id, title, which claim it supports, metric names to feature as the headline
EXPERIMENTS = [
    ('E0', 'Artifact rescue, hash manifest, environment capture',
     'gate - provenance for everything below',
     ['prediction_files_total', 'checkpoints_rescued', 'rescued_size_gib']),
    ('A1', 'Conditioning-width measurement',
     'conclusion (i) - the generator is near-unsteerable',
     ['conditioning_width', 'vec_fg_shape_live', 'effective_width_mean']),
    ('A2', 'Object-vs-background pixel share',
     'conclusion (i) - what those 48 numbers have to steer',
     ['fg_fraction_mean', 'invented_background_mean']),
    ('A3', 'Generated-vs-real appearance signature, with controls',
     'context - demotes the AUC 0.999 finding to a truism (R-c..R-f)',
     ['probe_auc_real_vs_lakered', 'probe_auc_real_vs_real_random',
      'probe_auc_jpeg75', 'recall_lakered', 'recall_raw_hkuis']),
    ('B1', 'ES-vs-true-error correlation',
     'SURVIVED - uncertainty is a real weakness signal',
     ['rho_es_mae_k20_test', 'rho_es_mae_k50_test', 'rho_es_1msa_k20',
      'cross_run_rho_mean']),
    ('B2', 'Coverage-term falsification',
     'SURVIVED - lambda_cov = 0 is measured, not assumed',
     ['rho_cov_mae_test', 'rho_cov_mae_val', 'rho_es_plus_cov_val',
      'rho_acceptance_ns']),
    ('B3', 'Targeting acceptance, both embedders, vs chance',
     'SURVIVED - targeting works (and R-a, R-b)',
     ['acceptance_dinoL518_k20_heldout', 'acceptance_dinoL518_k20_insample',
      'acceptance_inceptionv3_k50', 'lift_over_chance']),
    ('C1', 'Targeted-vs-random data distance',
     'conclusion (iv) - the effect-size wall',
     ['cohens_d_mean', 'cohens_d_range']),
    ('C2', 'Budget-B arithmetic and per-arm sampling',
     'conclusions (ii) and (iv) - zero extra steps; no B rescues it',
     ['total_step', 'gradient_steps_per_arm', 'peak_shift_ratio', 'peak_at_B']),
    ('C3', 'Noise floor and effect-size translation',
     'conclusion (iv) - 0.031 sigma against a 2 sigma bar',
     ['sigma_sa_armrun', 'two_sigma', 'predicted_delta_sa',
      'shortfall_factor']),
    ('D1', 'Foreground-exhaustion check',
     'conclusion (iii) - additions are re-renders',
     ['distinct_foregrounds', 'unique_renders', 'bijection']),
    ('D2', 'Leakage sweep',
     'scope bound - what any result can and cannot claim',
     ['cod10k_test_inter_target', 'val_camo_inter_test_camo',
      'camo_inter_chameleon']),
]

VERDICTS = ['MISMATCH', 'NOT-REPRODUCIBLE', 'UNVERIFIED', 'NEW', 'MATCH']
BAR = '=' * 80


def parse_log(path):
    """Return {exp_id: [block, ...]} in file order."""
    if not os.path.exists(path):
        return {}
    text = open(path).read()
    blocks, cur = [], None
    for line in text.splitlines():
        head = re.match(r'^(\S+) \| commit (\S+) \((\w+)\) \| EXP (\S+)\s*$', line)
        if head:
            cur = {'timestamp': head.group(1), 'commit': head.group(2),
                   'tree': head.group(3), 'exp': head.group(4),
                   'cmd': '', 'metrics': [], 'thresholds': [], 'expected': [],
                   'artifacts': '', 'revision': '', 'trains': '', 'notes': [],
                   'no_log': False}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith('CMD  '):
            cur['cmd'] = line[5:].strip()
        elif re.match(r'^  \S+\s+= ', line):
            name, rest = line.strip().split('=', 1)
            val, prov = rest.strip(), ''
            m = re.match(r'^(.*?)\s{2,}\((.*)\)$', val)
            if m:
                val, prov = m.group(1).strip(), m.group(2)
            cur['metrics'].append({'name': name.strip(), 'value': val,
                                   'provenance': prov})
        elif line.startswith('THRESHOLD  '):
            body = line[11:].strip()
            if body == 'none declared':
                continue
            passed = body.endswith('PASS')
            cur['thresholds'].append({'condition': body.rsplit('->', 1)[0].strip(),
                                      'passed': passed})
        elif line.startswith('EXPECTED (source)  '):
            body = line[19:].strip()
            if body.startswith('none pinned'):
                continue
            verdict = next((v for v in VERDICTS if v in body), '?')
            cur['expected'].append({'claim': body.split('->')[0].strip(),
                                    'verdict': verdict})
        elif line.startswith('ARTIFACTS  '):
            cur['artifacts'] = line[11:].strip()
        elif line.startswith('REVISION   '):
            cur['revision'] = line[11:].strip()
        elif line.startswith('TRAINS     '):
            cur['trains'] = line[11:].strip()
        elif line.startswith('NOTES      ') or (line.startswith(' ' * 11)
                                                and cur['notes']):
            cur['notes'].append(line[11:].strip())
        elif '[--no-log' in line:
            cur['no_log'] = True

    by_exp = {}
    for b in blocks:
        by_exp.setdefault(b['exp'], []).append(b)
    return by_exp


def headline(block, wanted):
    """Featured metrics, falling back to the first three if none match."""
    have = {m['name']: m for m in block['metrics']}
    picked = [have[w] for w in wanted if w in have]
    return picked or block['metrics'][:3]


def render(by_exp):
    from datetime import datetime
    md = []
    a = md.append
    a('# Results summary — Stage C evidence package')
    a('')
    a('> **Generated file — do not edit by hand.** Rebuilt from')
    a('> [STAGE_C_EVIDENCE_LOG.txt](STAGE_C_EVIDENCE_LOG.txt) by')
    a('> `evidence/summarize_log.py`, so it cannot drift from the evidence. Rationale for every')
    a('> number is in [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md); how to reproduce it is in')
    a('> [../EVIDENCE_SCRIPTS.md](../EVIDENCE_SCRIPTS.md).')
    a('')
    a('Generated %s at commit %s.'
      % (datetime.now().astimezone().replace(microsecond=0).isoformat(),
         C.git_commit()))
    a('')

    done = [e for e in EXPERIMENTS if e[0] in by_exp]
    pend = [e for e in EXPERIMENTS if e[0] not in by_exp]
    n_thr = sum(len(by_exp[e[0]][-1]['thresholds']) for e in done)
    n_pass = sum(sum(t['passed'] for t in by_exp[e[0]][-1]['thresholds'])
                 for e in done)
    trains = {by_exp[e[0]][-1]['trains'] for e in done}

    a('**%d of %d experiments complete.** %d of %d thresholds PASS. '
      'Trains a model: %s.'
      % (len(done), len(EXPERIMENTS), n_pass, n_thr,
         'NO for every experiment' if trains == {'NO'} else ', '.join(sorted(trains))))
    a('')

    # ---- status table ---------------------------------------------------
    a('## Status')
    a('')
    a('| id | experiment | supports | status | thresholds | vs prior audits |')
    a('|---|---|---|---|---|---|')
    for eid, title, claim, _w in EXPERIMENTS:
        if eid not in by_exp:
            a('| **%s** | %s | %s | pending | — | — |' % (eid, title, claim))
            continue
        b = by_exp[eid][-1]
        thr = b['thresholds']
        tp = sum(t['passed'] for t in thr)
        verd = [e['verdict'] for e in b['expected']]
        vs = ', '.join('%d %s' % (verd.count(v), v)
                       for v in VERDICTS if verd.count(v)) or 'none pinned'
        runs = len(by_exp[eid])
        status = '**DONE**' + ('' if runs == 1 else ' (%d blocks)' % runs)
        verdict = ('PASS' if tp == len(thr)
                   else '**%d FAIL**' % (len(thr) - tp))
        a('| **%s** | %s | %s | %s | %d/%d %s | %s |'
          % (eid, title, claim, status, tp, len(thr), verdict, vs))
    a('')

    # ---- headline numbers ----------------------------------------------
    a('## Headline numbers')
    a('')
    for eid, title, _c, wanted in EXPERIMENTS:
        if eid not in by_exp:
            continue
        b = by_exp[eid][-1]
        a('### %s — %s' % (eid, title))
        a('')
        a('| metric | value | provenance |')
        a('|---|---|---|')
        for m in headline(b, wanted):
            a('| `%s` | **%s** | %s |'
              % (m['name'], m['value'], m['provenance'] or '—'))
        a('')
        a('Command: `%s`' % b['cmd'])
        if b['artifacts'] and b['artifacts'] != 'none':
            a('')
            a('Artifacts: %s' % ', '.join('`%s`' % x.strip()
                                          for x in b['artifacts'].split(',')))
        a('')

    # ---- revisions ------------------------------------------------------
    revs = [(eid, by_exp[eid][-1]['revision']) for eid, *_ in EXPERIMENTS
            if eid in by_exp and by_exp[eid][-1]['revision']
            and not by_exp[eid][-1]['revision'].startswith('none')]
    a('## Revisions surfaced so far')
    a('')
    if revs:
        a('Conclusions that moved once measured. The full 13-row trail, including revisions from')
        a('experiments not yet re-run here, is §5 of [../EVIDENCE_APPROACH.md](../EVIDENCE_APPROACH.md).')
        a('')
        for eid, r in revs:
            # older blocks carry a literal %% from a script format-string slip
            a('- **%s** — %s' % (eid, r.replace('%%', '%')))
    else:
        a('None yet: every completed experiment reproduced its source value.')
    a('')

    # ---- disagreements --------------------------------------------------
    bad = [(eid, e['claim'], e['verdict']) for eid, *_ in EXPERIMENTS
           if eid in by_exp
           for e in by_exp[eid][-1]['expected']
           if e['verdict'] not in ('MATCH',)]
    a('## Anything that did not simply reproduce')
    a('')
    if bad:
        a('| id | claim | verdict |')
        a('|---|---|---|')
        for eid, claim, v in bad:
            a('| %s | %s | **%s** |' % (eid, claim, v))
        a('')
        a('`NEW` means the package measured something no source document pinned, so there was')
        a('nothing to agree or disagree with.')
    else:
        a('Every pinned value reproduced.')
    a('')

    # ---- remaining ------------------------------------------------------
    a('## Still to run')
    a('')
    if pend:
        for eid, title, claim, _w in pend:
            a('- **%s** %s — %s' % (eid, title, claim))
        a('')
        a('Expected values for these are in [../EVIDENCE_SCRIPTS.md](../EVIDENCE_SCRIPTS.md) and are')
        a('**not yet verified**. Treat any number without a log block as a claim awaiting')
        a('reproduction.')
    else:
        a('None — every experiment has a log block.')
    a('')
    return '\n'.join(md) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if the summary on disk is stale')
    opt = ap.parse_args()

    by_exp = parse_log(C.LOG)
    md = render(by_exp)
    out_md = os.path.join(os.path.dirname(C.LOG), 'RESULTS_SUMMARY.md')
    out_js = os.path.join(os.path.dirname(C.LOG), 'RESULTS_SUMMARY.json')

    if opt.check:
        cur = open(out_md).read() if os.path.exists(out_md) else ''
        strip = lambda t: '\n'.join(l for l in t.splitlines()
                                    if not l.startswith('Generated '))
        stale = strip(cur) != strip(md)
        print('STALE - re-run evidence/summarize_log.py' if stale
              else 'up to date')
        sys.exit(1 if stale else 0)

    open(out_md, 'w').write(md)
    payload = {eid: {'title': t, 'supports': c, 'runs': by_exp.get(eid, [])}
               for eid, t, c, _w in EXPERIMENTS}
    json.dump(payload, open(out_js, 'w'), indent=2)

    done = sum(1 for eid, *_ in EXPERIMENTS if eid in by_exp)
    print('wrote %s (%d/%d experiments)' % (os.path.relpath(out_md, C.REPO),
                                            done, len(EXPERIMENTS)))
    print('wrote %s' % os.path.relpath(out_js, C.REPO))


if __name__ == '__main__':
    main()

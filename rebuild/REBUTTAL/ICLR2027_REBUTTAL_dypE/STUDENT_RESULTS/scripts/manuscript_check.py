#!/usr/bin/env python
"""Read-only integrity check of the submitted manuscript: cite keys vs bib, labels vs refs.

Reads the manuscript and bib from the original working copy (never writes there) and the
\\input files from this worktree's base commit (rebuild/FinalPaper/AD-PCH-230926/).
Writes one JSON report to the path given by --out.
"""
import argparse
import hashlib
import json
import os
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--tex', required=True)
ap.add_argument('--bib', required=True)
ap.add_argument('--inputs-dir', required=True, help='directory holding the \\input files')
ap.add_argument('--out', required=True)
a = ap.parse_args()


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def strip_comments(s):
    return re.sub(r'(?<!\\)%.*', '', s)


main = strip_comments(open(a.tex, encoding='utf-8').read())
inputs = re.findall(r'\\input\{([^}]+)\}', main)
texts = {'<main>': main}
missing_inputs = []
for name in inputs:
    fn = name if name.endswith('.tex') else name + '.tex'
    p = os.path.join(a.inputs_dir, fn)
    if os.path.isfile(p):
        texts[fn] = strip_comments(open(p, encoding='utf-8').read())
    else:
        missing_inputs.append(fn)
figs = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', main)
missing_figs = [f for f in figs if not os.path.isfile(os.path.join(a.inputs_dir, f))]

allt = '\n'.join(texts.values())
cite_cmds = re.findall(r'\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}', allt)
cited = sorted({k.strip() for grp in cite_cmds for k in grp.split(',')
                if k.strip() and not k.strip().startswith('#')})
main_cmds = re.findall(r'\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}', main)
cited_main = sorted({k.strip() for grp in main_cmds for k in grp.split(',')
                     if k.strip() and not k.strip().startswith('#')})
bib = open(a.bib, encoding='utf-8').read()
entries = re.findall(r'@([a-zA-Z]+)\s*\{\s*([^,\s]+)\s*,', bib)
bib_keys = [k for t, k in entries if t.lower() not in ('comment', 'preamble', 'string')]
dup_bib = sorted({k for k in bib_keys if bib_keys.count(k) > 1})
missing_cites = [k for k in cited if k not in set(bib_keys)]
labels = re.findall(r'\\label\{([^}]+)\}', allt)
refs = re.findall(r'\\(?:ref|eqref|autoref|cref|Cref|pageref)\{([^}]+)\}', allt)
ref_keys = sorted({k.strip() for grp in refs for k in grp.split(',')
                   if not k.strip().startswith('#')})  # '#n' = macro parameters
undefined = [r for r in ref_keys if r not in set(labels)]
dup_labels = sorted({l for l in labels if labels.count(l) > 1})

rep = dict(
    tex=a.tex, tex_sha256=sha(a.tex), bib=a.bib, bib_sha256=sha(a.bib),
    inputs=inputs, missing_inputs=missing_inputs, figures=figs, missing_figures=missing_figs,
    n_unique_cited_keys=len(cited), n_unique_cited_keys_main_file_only=len(cited_main),
    cited_only_in_inputs=[k for k in cited if k not in set(cited_main)],
    n_bib_entries=len(bib_keys), uncited_bib_entries=[k for k in bib_keys if k not in set(cited)], duplicate_bib_keys=dup_bib,
    cited_keys_missing_from_bib=missing_cites,
    n_labels=len(labels), duplicate_labels=dup_labels, n_unique_refs=len(ref_keys),
    undefined_refs=undefined,
    note='syntax-level check only; no external semantic verification of references')
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
json.dump(rep, open(a.out, 'w'), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k not in ('inputs', 'figures')}, indent=1))
sys.exit(0 if not (missing_cites or undefined or missing_inputs or missing_figs or dup_labels) else 1)

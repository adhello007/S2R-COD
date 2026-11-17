#!/usr/bin/env python3
"""Check every manuscript locator in the replies against the compiled PDF's label numbering.

1. Reads paper/build/REVISED_MARKED.aux (label -> number).
2. For each expected (reply file, label, phrase) it renders the locator from the aux number and asserts that the
   rendered locator occurs in that reply. So "Table 3" in a reply is checked to be tab:equiv, not just "a table".
3. Lists every 'Table N', 'App. X', '§N(.N)' token in the replies and fails on any that no expectation covers.
"""
import pathlib, re, sys

B = pathlib.Path(__file__).resolve().parents[1]
aux = (B / "paper/build/REVISED_MARKED.aux").read_text()
NUM = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}", aux)}

def T(l): return f"Table {NUM[l]}"
def S(l): return f"§{NUM[l]}"
def A(l): return f"App. {NUM[l]}"

R = {k: (B / f"REVIEWERS/{k}/FINAL_UPDATED_REBUTTAL.md").read_text() for k in ("RL5B", "Caus", "dypE")}
R["GENERAL"] = (B / "GENERAL_RESPONSE.md").read_text()
EXPECT = [
    # (file, rendered locator, what it must point to)
    ("RL5B", f"{T('tab:equiv')} ({S('sec:null')})", "shared headline table, Sec 3.1"),
    ("RL5B", f"{T('tab:ci_tost')} ({A('app:diag')})", "16 eight-seed contrasts"),
    ("RL5B", f"{S('sec:concentration')} (verdict); {T('tab:cdr')} ({A('app:diag')})", "dose-response"),
    ("RL5B", f"{T('tab:boundary')}, {A('app:diag')}", "boundary 8 seeds"),
    ("RL5B", f"{T('tab:protocol')} and \"Where the absolute gap comes from\" ({A('app:related')})", "protocol table"),
    ("RL5B", f"{S('sec:discussion')} (Scope)", "scope paragraph"),
    ("RL5B", f"{A('app:coverage')} (coverage", "coverage appendix"),
    ("RL5B", f"{S('sec:related')}", "RISE in related work"),
    ("RL5B", f"({S('sec:method')}, {A('app:method')})", "sign rule"),
    ("RL5B", f"amendment committed 2026-11-11; {A('app:method')}", "EQ amendment commit"),
    ("Caus", f"{S('sec:concentration')}; {A('app:shapeoracle')} (\"Separability", "probe / flat quota"),
    ("Caus", f"{T('tab:trained')} ({S('sec:null')}, rows ORS); {A('app:shapeoracle')}", "oracle shapes"),
    ("Caus", f"{T('tab:equiv')} ({S('sec:null')}); {A('app:diag')}", "shared headline table"),
    ("Caus", f"{S('sec:why')}; {A('app:coverage')}", "coverage by k"),
    ("Caus", f"{A('app:method')} now states this", "pre-registration timing"),
    ("Caus", f"({S('sec:concentration')}; {A('app:diag')})", "boundary / interaction"),
    ("Caus", f"{S('sec:discussion')}", "scope"),
    ("dypE", f"{T('tab:equiv')} ({S('sec:null')})", "shared headline table"),
    ("dypE", f"{T('tab:paired')} ({A('app:diag')})", "paired, four cells"),
    ("dypE", f"{A('app:diag')} (\"How much the trained comparison is attenuated\")", "14.1% correction"),
    ("dypE", f"{S('sec:concentration')}; {T('tab:boundary')} and \"Architecture, multiplicity and domain mix\" ({A('app:diag')})", "boundary 8 seeds"),
    ("dypE", f"{T('tab:cdr')}, {A('app:diag')}", "dose-response"),
    ("dypE", f"{A('app:coverage')}'s estimator", "selection coverage"),
    ("dypE", f"{S('sec:discussion')}, Scope", "scope"),
    ("dypE", f"{S('sec:contamination')}; {T('tab:chamcount')} and \"What the overlap means for each protocol\" ({A('app:chamext')})", "CHAMELEON"),
    ("dypE", f"no contrast is affected ({A('app:chamext')})", "COD10K-test duplicates"),
    ("GENERAL", f"{T('tab:equiv')} ({S('sec:null')})", "headline"),
    ("GENERAL", f"{T('tab:ci_tost')} ({A('app:diag')})", "16 contrasts"),
    ("GENERAL", f"({T('tab:cdr')})", "CDR"), ("GENERAL", f"({T('tab:boundary')})", "boundary"),
    ("GENERAL", f"Scope paragraph ({S('sec:discussion')})", "scope"), ("GENERAL", f"({A('app:coverage')})", "coverage"),
    ("GENERAL", f"({T('tab:trained')}; {A('app:shapeoracle')})", "oracle shapes"), ("GENERAL", f"({S('sec:concentration')})", "probe"),
    ("GENERAL", f"({T('tab:protocol')}, {A('app:related')})", "protocol"), ("GENERAL", f"({T('tab:chamcount')}, {A('app:chamext')})", "CHAMELEON"),
    ("GENERAL", f"({A('app:method')})", "pre-registration"),
]
bad = 0
covered = {k: set() for k in R}
for f, loc, what in EXPECT:
    ok = loc in R[f]
    bad += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {f:7s} {loc!r:90s} -> {what}")
    for tok in re.findall(r"Table \d+|App\. [A-Z]|§\d+(?:\.\d+)?", loc):
        covered[f].add(tok)
for f, s in R.items():
    for tok in sorted(set(re.findall(r"Table \d+|App\. [A-Z]|§\d+(?:\.\d+)?", s))):
        if tok not in covered[f]:
            bad += 1
            print(f"FAIL  {f:7s} locator {tok!r} is not covered by any checked expectation")
print(f"\n{'ALL LOCATORS VERIFIED' if not bad else f'{bad} problem(s)'} against {B / 'paper/build/REVISED_MARKED.aux'}")
sys.exit(1 if bad else 0)

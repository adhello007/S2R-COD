#!/usr/bin/env python3
"""Check that every file path named in backticks in the deliverable Markdown files exists."""
import pathlib, re, sys
B = pathlib.Path(__file__).resolve().parents[1]; ROOT = B.parent
PKG = {"RL5B/": ROOT / "rebuild/REBUTTAL/ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/",
       "Caus/": ROOT / "rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/",
       "dypE/": ROOT / "rebuild/REBUTTAL/ICLR2027_REBUTTAL_dypE/STUDENT_RESULTS/"}
EXT = (".md", ".csv", ".tex", ".json", ".py", ".pdf", ".patch", ".log", ".txt", ".jsonl", ".sty", ".bst", ".bib")
bad = n = 0
for md in sorted(B.rglob("*.md")):
    if "paper" in md.parts: continue
    for tok in re.findall(r"`([^`\s]+)`", md.read_text()):
        t = tok.rstrip(".,;:)")
        if not (t.endswith(EXT) or t.endswith("/")) or "<" in t or "*" in t or t.startswith(("\\", "http")): continue
        n += 1
        cands = [B / t, ROOT / t, md.parent / t] + [r / t[len(k):] for k, r in PKG.items() if t.startswith(k)]
        cands += [r / t for r in PKG.values()] + [r / "RESULT_TABLES" / t for r in PKG.values()]
        cands += [B / "paper" / t, B / "tools" / t]
        if not any(c.exists() for c in cands):
            bad += 1; print(f"MISSING  {md.relative_to(B)}: {t}")
print(f"{n} paths checked, {bad} missing"); sys.exit(1 if bad else 0)

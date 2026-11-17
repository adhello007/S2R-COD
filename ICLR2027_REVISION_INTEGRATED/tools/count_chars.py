#!/usr/bin/env python3
"""Count each OpenReview comment in the reply files.

A comment is the text between '<!-- BEGIN COMMENT ... -->' and '<!-- END COMMENT ... -->' (markers excluded,
surrounding whitespace stripped). That is exactly the text to paste. Limit: 5,000 characters per comment
(Python len, i.e. Unicode code points, whitespace and Markdown included); at most 2 comments per reviewer.
"""
import pathlib, re, sys

BASE = pathlib.Path(__file__).resolve().parents[1]
FILES = [BASE / "REVIEWERS/RL5B/FINAL_UPDATED_REBUTTAL.md", BASE / "REVIEWERS/Caus/FINAL_UPDATED_REBUTTAL.md",
         BASE / "REVIEWERS/dypE/FINAL_UPDATED_REBUTTAL.md", BASE / "GENERAL_RESPONSE.md"]
LIMIT, MAXC = 5000, 2
bad = 0
for f in FILES:
    if not f.exists():
        print(f"MISSING {f}"); bad += 1; continue
    s = f.read_text()
    blocks = re.findall(r"<!-- BEGIN COMMENT ([^>]*?) -->(.*?)<!-- END COMMENT \1 -->", s, flags=re.S)
    n_ok = len(blocks) <= MAXC and len(blocks) >= 1
    print(f"{f.relative_to(BASE)}: {len(blocks)} comment(s) {'OK' if n_ok else 'TOO MANY/NONE'}")
    bad += not n_ok
    for name, body in blocks:
        n = len(body.strip())
        b = len(body.strip().encode())
        ok = n <= LIMIT
        bad += not ok
        print(f"   comment {name}: {n} chars ({b} UTF-8 bytes) {'OK' if ok else 'OVER'}")
sys.exit(1 if bad else 0)

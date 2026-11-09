"""Extract the posted initial rebuttal (Appendix A, verbatim) from the instruction file.

Usage: python extract_initial_rebuttal.py <instructions.md> <out.md>
Everything after the line '## Appendix A — Initial rebuttal as posted (verbatim)' and its
one-paragraph preamble is copied byte-for-byte; nothing is edited.
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(lines) if l.startswith('## Appendix A'))
first = next(i for i in range(start + 1, len(lines)) if lines[i].startswith('## Response to Reviewer RL5B'))
body = '\n'.join(lines[first:]).rstrip('\n') + '\n'
open(dst, 'w', encoding='utf-8').write(body)
print(f'copied lines {first + 1}-{len(lines)} of {src} -> {dst} ({len(body)} chars)')

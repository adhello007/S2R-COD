"""Measure each OpenReview post in FINAL_UPDATED_REBUTTAL.md and (re)write the trailing count comment.

A post is the text from its '## ' heading to the next '---' separator line. Limits: 5,000 characters per
reviewer part, 2,500 for the summary post. Exit code 1 if any limit is exceeded.
Usage: python analysis/count_rebuttal.py
"""
import datetime
import os
import re
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'FINAL_UPDATED_REBUTTAL.md')
TAG = '<!-- CHARACTER COUNTS'


def main():
    s = open(P).read()
    if TAG in s:
        s = s[:s.index(TAG)].rstrip() + '\n'
    rows, bad = [], False
    for chunk in re.split(r'\n---\n', s):
        if '\n## ' not in '\n' + chunk:
            continue
        body = chunk[chunk.index('## '):].strip()
        title = body.splitlines()[0][3:]
        limit = 2500 if title.startswith('Summary') else 5000
        n = len(body)
        bad |= n > limit
        rows.append('  %-62s %5d / %d %s' % (title[:62], n, limit, 'OK' if n <= limit else 'OVER'))
    markers = len(re.findall(r'\*\*\[(EQ|AUTHOR)', s))
    note = ('%s (measured by analysis/count_rebuttal.py, %s; Python len() on each post from its "## " heading to the '
            'next "---")\n%s\n  unresolved [EQ]/[AUTHOR] markers: %d\n-->\n'
            % (TAG, datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), '\n'.join(rows), markers))
    open(P, 'w').write(s + '\n' + note)
    print(note)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

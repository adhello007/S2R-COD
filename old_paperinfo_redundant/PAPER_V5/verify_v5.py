#!/usr/bin/env python3
"""Verify PAPER_V5 main.tex preserves every fact from PAPER_V4 main.tex."""
import re, sys, collections

V4 = '/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/rebuild/PAPER_V4/main.tex'
V5 = '/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD/rebuild/PAPER_V5/main.tex'

# Numbers allowed to leave the MAIN TEXT because they moved to the appendix,
# or (abstract-shedding) because they remain elsewhere in the main text.
RELOCATED_TO_APPENDIX = {'0.7010', '0.0334', '0.0211',  # A0 spread -> app:anchor
                         '4443', '+4442',             # erosion split -> app:tier1
                         '0.0107', '0.7151', '0.7172', '42',  # A0 repro gate -> app:anchor
                         '-23.6', '-82.9', '8885',    # coverage/bijection detail -> app:tier1
                         '+0.3433', '+0.4988', '+0.7070', '+0.4457', '0.0012'}  # area detail -> app:tables
# tab:causes 'Tier' column values became plain words ('generalizes' / 'specific to this
# setup'); these are labels, never measurements. 7x'2', 4x'1', 1x'1'+1x'2' from the arrow row.
TIER_LABEL_TOKENS = {'1': 5, '2': 8}
# '1,' existed only inside the label '[Tier 1, scoped]'
TIER_ONLY_TOKENS = {'1,'}

def split(path):
    s = open(path).read()
    s = re.sub(r'(?<!\\)%.*', '', s)          # strip comments
    a = s.index('\\begin{abstract}')
    b = s.index('\\appendix')
    return s[a:b], s[b:], s

def nums(t):
    t = re.sub(r'p\{[\d.]+cm\}', ' ', t)          # tabular column widths are layout, not content
    t = re.sub(r'\\itemsep[\d.]+em', ' ', t)          # list spacing is layout, not content
    t = re.sub(r'\\includegraphics\[[^\]]*\]', ' ', t)
    return collections.Counter(
        m.group(0).rstrip(',.') for m in re.finditer(r'[+-]?\d[\d,]*\.?\d*', t))

def report(name, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  -- ' + detail) if detail else ''))
    return ok

def main():
    m4, a4, f4 = split(V4)
    m5, a5, f5 = split(V5)
    allok = True

    # 1. numeric multiset over the WHOLE manuscript (main + appendix)
    w4, w5 = nums(m4) + nums(a4), nums(m5) + nums(a5)
    # A fact is preserved if its token still appears SOMEWHERE in the manuscript.
    # Counts may legitimately fall where the rewrite removed duplication.
    vanished = sorted(set(w4) - set(w5) - TIER_ONLY_TOKENS)
    invented = sorted(set(w5) - set(w4))
    allok &= report('every V4 numeric token still present somewhere',
                    not vanished, f'VANISHED {vanished}' if vanished else '')
    allok &= report('no numeric token invented',
                    not invented, f'INVENTED {invented}' if invented else '')
    dropped = {k: (w4[k], w5.get(k, 0)) for k in w4
               if w5.get(k, 0) < w4[k] and k not in TIER_LABEL_TOKENS}
    if dropped:
        print('  note   occurrences reduced (duplication removed), token still present:')
        for k, (o, n) in sorted(dropped.items()):
            print(f'           {k}: {o} -> {n}')

    # 2. tokens that left the MAIN TEXT entirely must be whitelisted relocations
    n4, n5 = nums(m4), nums(m5)
    gone = set(n4) - set(n5)
    unexplained = gone - RELOCATED_TO_APPENDIX - TIER_ONLY_TOKENS
    allok &= report('tokens gone from main text are whitelisted relocations',
                    not unexplained, f'unexplained {sorted(unexplained)}' if unexplained else '')
    for k in sorted(gone & RELOCATED_TO_APPENDIX):
        assert k in nums(a5), k
    if gone & RELOCATED_TO_APPENDIX:
        print(f'  note   relocated to appendix, verified present there: '
              f'{sorted(gone & RELOCATED_TO_APPENDIX)}')

    # 3. citation placeholders
    c4 = sorted(re.findall(r'\[CITE: [^\]]*\]', f4))
    c5 = sorted(re.findall(r'\[CITE: [^\]]*\]', f5))
    allok &= report(f'[CITE:] placeholders {len(c4)} -> {len(c5)}, identical set',
                    c4 == c5, 'set differs' if c4 != c5 else '')

    # 4. TODO markers
    t4, t5 = f4.count('[TODO:'), f5.count('[TODO:')
    allok &= report(f'[TODO:] markers {t4} -> {t5}', t4 == t5)

    # 5. banned-phrase scan (main text only, excluding citation placeholders)
    scan5 = re.sub(r'\[CITE:[^\]]*\]', ' ', m5)
    # the three required ICLR statements sit after the 9-page body; the reproducibility
    # statement is the proper home for a provenance sentence, so exclude them here
    scan5 = scan5[:scan5.index('\\subsection*{AI use statement}')]
    prereg = len(re.findall(
        r'pre-?registrat\w*|pre-?registered|pre-?declared|frozen (?:rule|clause|before)|'
        r'fixed (?:before|in advance)|committed before|before the first run|'
        r'before any (?:result|GPU time)|before it was run|before measurement|before the draw', scan5))
    allok &= report(f'pre-registration mentions in main text <= 4 (was 36): {prereg}', prereg <= 4)

    tiers = len(re.findall(r'Tier ?[123]|[Tt]iered', scan5))
    allok &= report(f'tier labels in main-text prose == 0 (was 15): {tiers}', tiers == 0)

    manner = re.findall(r'rather than (?:leave|leaving|await|awaiting|discover|discovering|'
                        r'be found|be computed|assumed|relax)|as it fell|not an omission|'
                        r'does not flatter us|we state rather than', scan5)
    allok &= report(f'self-congratulatory mannerisms == 0 (was 8): {len(manner)}',
                    not manner, str(manner) if manner else '')

    # 6. load-bearing sentences that must survive verbatim
    MUST = [
        'could not have detected the reference effect had it been present',
        'This is a control on \\emph{instrument sensitivity}, not an ablation',
        'non-independence rather than inflation',
        'CHAMELEON is not an independent endpoint for COD10K-trained models',
        'unchecked, not clean',
        'Every rate is a\n\\emph{lower bound}',
        'the geometric result carries this claim',
        'zero and harmful are not',
        'never a demonstration of absence',
        'nothing converts them into significance claims',
        'None licenses the conclusion that closed-loop\ngeneration cannot work',
    ]
    missing = [s for s in MUST if s.replace('\n', ' ') not in ' '.join(f5.split())
               and s not in f5]
    allok &= report(f'{len(MUST)} load-bearing claim sentences retained',
                    not missing, f'MISSING: {missing}' if missing else '')

    # 7. word count
    def wc(t):
        t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', t)
        t = re.sub(r'[{}$&\\_^~]', ' ', t)
        return len([w for w in t.split() if re.search(r'[A-Za-z0-9]', w)])
    body4 = m4[:m4.index('\\subsection*{AI use statement}')]
    body5 = m5[:m5.index('\\subsection*{AI use statement}')]
    print(f'\n  BODY (abstract..conclusion, counts against 9pp): '
          f'{wc(body4)} -> {wc(body5)}  ({wc(body5)-wc(body4):+d})')
    print(f'  statements (not in 9pp): {wc(m4)-wc(body4)} -> {wc(m5)-wc(body5)}')
    print(f'  appendix : {wc(a4)} -> {wc(a5)}  ({wc(a5)-wc(a4):+d})')

    print('\n' + ('ALL CHECKS PASS' if allok else '*** FAILURES ABOVE ***'))
    return 0 if allok else 1

sys.exit(main())

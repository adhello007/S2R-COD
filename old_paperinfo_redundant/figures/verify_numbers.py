#!/usr/bin/env python3
"""Numeric-literal audit for the S2R-COD figure set.  READ-ONLY.

Rule: every number a figure RENDERS must trace to figures/figure_data.json.
Coordinates, node widths and other geometry are not claims and are excluded --
but they are excluded PRECISELY (by parsing what each \foreach slot is bound
to), never by guessing from magnitude.

Pass 1  prose     -- strip comments, citations, balanced geometry groups and
                     \foreach slots bound to coordinate variables, then check
                     every literal that survives.
Pass 2  chip grids-- EXP T2 / D2 carry their VALUES inside \foreach lists,
                     which pass 1 strips. Those are checked value-by-value.
"""
import json, os, re, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(REPO, "figures/figure_data.json")))["entries"]

known = set()
for e in D.values():
    for v in (e["value"], e["spread"], e["delta_vs_baseline"], e["n_seeds"]):
        if isinstance(v, (int, float)):
            known.add(str(v))
            for nd in range(7):
                known.add(("%." + str(nd) + "f") % abs(v))
            if float(v) == int(v):
                known.add(str(int(abs(v))))
    for m in re.finditer(r"\d+\.\d+|\d{2,}", e.get("note") or ""):
        known.add(m.group(0))

DERIVED = {
 "3.24": "ABC bar / T2 bar on SINet|COD10K (0.017933 / 0.005533)",
 "53.9": "41/76 as a percent (d2r.cham.frac = 0.5395)",
 "73.7": "3039/4121 as a percent (d2nc4k unchecked share)",
 "31.9": "a3 rel_loss_vs_raw 0.3188 as a percent",
 "22.5": "A0 round-1 exposure advantage -- POOL_MECHANICS_AUDIT, NO EXP BLOCK",
 "0.0067": "a3 headline 0.9995 minus the JPEG-30 floor 0.9928",
 "7.36": "d2r nearest-distance gap ratio", "5.51": "d2r gap lower value",
 "40.58": "d2r gap upper value", "0.448": "d2r percentile floor",
 "0.559": "d2r percentile ceiling",
 "0.0142": "the reference MT->Ours gap the ABC design set out to halve",
 "8885": "D1: 4447 traced objects x 2 pools",
 "1.82": "T2 largest |Delta| / sigma_hat",
 "0.194": "C1 committed cell max_alloc_share",
 "0.78644": "C1 alloc_entropy_norm", "0.49253": "C1 tv_from_uniform",
}
COORD_VARS = {"x", "xa", "dx", "x0", "y", "dy"}
CITATION = re.compile(r"[A-Za-z_0-9]+\.(py|tex|md)\s*:\s*[\d]+(\s*[-,]\s*\d+)*")
GEOMGROUP = re.compile(r"\(\s*[-+\d.,*/\s]*(?:\\[a-zA-Z]+[-+\d.,*/\s]*)*\)"
                       r"|\{\s*[-+\d.,*/\s]*(?:\\[a-zA-Z]+[-+\d.,*/\s]*)*\}"
                       r"|-?\d+(?:\.\d+)?(?:mm|pt)")
NUM = re.compile(r"(?<![\w.])(\d+\.\d+|\d{2,})(?![\w])")


def balanced(text, i):
    """Return the index just past the '{...}' group starting at text[i]=='{'."""
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def strip_foreach_coords(text):
    """Blank out \foreach slots bound to a coordinate-named variable."""
    out, pos = [], 0
    for m in re.finditer(r"\\foreach\s+((?:\\[a-zA-Z]+/?)+)\s+in\s*", text):
        j = text.find("{", m.end())
        if j < 0:
            continue
        k = balanced(text, j)
        spec = [v.lstrip("\\") for v in m.group(1).split("/")]
        drop = {i for i, v in enumerate(spec) if v in COORD_VARS}
        if not drop:
            continue
        body = text[j + 1:k - 1]
        kept = []
        for tup in re.split(r",(?![^{]*\})", body):
            parts, buf, depth = [], "", 0
            for ch in tup:                       # split on '/' at depth 0
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                if ch == "/" and depth == 0:
                    parts.append(buf); buf = ""
                else:
                    buf += ch
            parts.append(buf)
            kept.append("/".join(p for i, p in enumerate(parts) if i not in drop))
        out.append(text[pos:j + 1]); out.append(",".join(kept)); pos = k - 1
    out.append(text[pos:])
    return "".join(out)


bodies = [os.path.join(REPO, "figures/fig_method.tex"),
          os.path.join(REPO, "figures/fig_results_block.tex")]
bodies += sorted(p for p in glob.glob(os.path.join(REPO, "figures/exp/fig_*.tex"))
                 if not p.endswith("_standalone.tex"))

orphans = []
for b in bodies:
    raw = open(b).read()
    raw = "\n".join(l.split("%")[0] for l in raw.split("\n"))   # drop comments
    raw = strip_foreach_coords(raw)
    raw = CITATION.sub(" ", raw)
    prev = None
    while prev != raw:
        prev, raw = raw, GEOMGROUP.sub(" ", raw)
    for m in NUM.finditer(raw):
        t = m.group(1)
        if t in known or t in DERIVED or re.fullmatch(r"\d{1,2}", t):
            continue
        line = raw[:m.start()].count("\n") + 1
        ctx = raw[max(0, m.start() - 30):m.start() + 30].replace("\n", " ")
        orphans.append((os.path.relpath(b, REPO), line, t, ctx))

GRIDS = {
 "exp/fig_t2.tex": [("t2.SINet.COD10K.gap.CSHUF->C10.ratio", "0.55"),
                    ("t2.SINetv2.COD10K.gap.CSHUF->C10.ratio", "0.83"),
                    ("t2.SINet.NC4K.gap.CSHUF->C10.ratio", "0.62"),
                    ("t2.SINetv2.NC4K.gap.CSHUF->C10.ratio", "0.66"),
                    ("t2.SINet.COD10K.gap.CINV->C10.ratio", "0.31"),
                    ("t2.SINetv2.COD10K.gap.CINV->C10.ratio", "0.72"),
                    ("t2.SINet.NC4K.gap.CINV->C10.ratio", "1.20"),
                    ("t2.SINetv2.NC4K.gap.CINV->C10.ratio", "1.40"),
                    ("t2.SINet.COD10K.gap.CINV->CSHUF.ratio", "0.86"),
                    ("t2.SINetv2.COD10K.gap.CINV->CSHUF.ratio", "0.11"),
                    ("t2.SINet.NC4K.gap.CINV->CSHUF.ratio", "1.82"),
                    ("t2.SINetv2.NC4K.gap.CINV->CSHUF.ratio", "0.74")],
 "exp/fig_d2.tex": [("d2r.sweep.tol_1.0.cham", "11"), ("d2r.sweep.tol_2.0.cham", "26"),
                    ("d2r.sweep.tol_3.0.cham", "37"), ("d2r.sweep.tol_5.0.cham", "40"),
                    ("d2r.sweep.tol_6.0.cham", "41")],
}
grid_fail = []
for fn, pairs in GRIDS.items():
    txt = open(os.path.join(REPO, "figures", fn)).read()
    for key, shown in pairs:
        if key not in D:
            grid_fail.append((fn, key, shown, "no such figure_data key")); continue
        got = ("%.2f" % D[key]["value"]) if "." in shown else str(int(D[key]["value"]))
        if got != shown:
            grid_fail.append((fn, key, shown, "figure_data says %s" % got))
        elif shown not in txt:
            grid_fail.append((fn, key, shown, "not present in the .tex"))

print("bodies audited          : %d" % len(bodies))
print("orphan literals         : %d" % len(orphans))
for o in orphans:
    print("   %s:%d  %-10s  ...%s..." % o)
print("chip-grid values checked: %d" % sum(len(v) for v in GRIDS.values()))
print("chip-grid mismatches    : %d" % len(grid_fail))
for g in grid_fail:
    print("   %s  %s  shown=%s  %s" % g)
sys.exit(1 if (orphans or grid_fail) else 0)

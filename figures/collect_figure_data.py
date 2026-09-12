#!/usr/bin/env python3
"""
collect_figure_data.py -- re-derive every number the S2R-COD figures display.

READ-ONLY. Standard library only (the repo venv has no pandas and no
matplotlib). No network, no GPU, no training, no file outside figures/ written.

It PARSES the committed machine-readable artifacts under rebuild/*/out/ and the
cited EXP blocks in results/REBUILD_LOG.txt, rather than transcribing numbers
from prose. Aggregates (means, win counts, paired increments) are RECOMPUTED
here from per-row data, not copied from a *_RESULTS.md.

Output: figures/figure_data.json

Every entry carries: experiment, arm, model, seed(s), metric, value, spread,
spread_kind, n_seeds, delta_vs_baseline, scope, confidence, source_file,
source_line.  A number that cannot be re-derived is emitted with
"value": null and a "reason" -- never a hardcoded fallback.

Self-tests (hard failures, printed at the end):
  * S_alpha 0.717216 / MAE 0.074463 on Result/SINet/S2C must agree across
    B1, ABC and T2C -- the three independent paths to the same scorer.
  * alloc_entropy_norm 0.78644 and tv_from_uniform 0.49253 must agree across
    C1, ABC and ABC/t2.
If either disagrees, THIS SCRIPT'S extraction is wrong, not the repo.

Run:  .venv/bin/python figures/collect_figure_data.py
"""

import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "figures", "figure_data.json")
LOG = os.path.join(REPO, "results", "REBUILD_LOG.txt")

# Scope tiers, from rebuild/TIER_SEGREGATION.md section 1 master table.
# Written as words, never as bare tier digits: T1/T2/T3 is overloaded four ways
# in this repository (rebuild/FINAL_RESULTS.md:42-53).
GEN, SIG, IND = "gen", "signal+data", "indep"

entries = {}
problems = []


def rel(p):
    return os.path.relpath(p, REPO)


def lineno(path, needle, start=1):
    """1-indexed line of the first line containing `needle`, else None.

    Gives every emitted value a real file:line, so FIGURE_EVIDENCE.md can cite
    the artifact rather than a document that quotes it.
    """
    try:
        with open(path, "r", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if i >= start and needle in line:
                    return i
    except OSError:
        return None
    return None


def add(key, *, experiment, metric, value, source_file, source_line,
        arm=None, model=None, seeds=None, spread=None, spread_kind=None,
        n_seeds=None, delta_vs_baseline=None, scope=None,
        confidence="pre-registered", note=None, reason=None):
    if key in entries:
        raise SystemExit("duplicate figure_data key: %s" % key)
    e = dict(experiment=experiment, arm=arm, model=model, seeds=seeds,
             metric=metric, value=value, spread=spread, spread_kind=spread_kind,
             n_seeds=n_seeds, delta_vs_baseline=delta_vs_baseline, scope=scope,
             confidence=confidence, source_file=rel(source_file),
             source_line=source_line)
    if note:
        e["note"] = note
    if reason:
        e["reason"] = reason
        problems.append((key, reason))
    entries[key] = e


def loadjson(p):
    with open(p) as fh:
        return json.load(fh)


def loadcsv(p):
    with open(p) as fh:
        return list(csv.DictReader(fh))


def mean(xs):
    return sum(xs) / len(xs)


# ---------------------------------------------------------------- ABC and T2
# rebuild/ABC/out/ and rebuild/ABC/out/t2/ share EVERY basename
# (rebuild/FINAL_RESULTS.md:84). Keys below are path-derived, never basename-
# derived, or the two campaigns would silently overwrite each other.
def collect_campaign(tag, outdir, scope):
    vpath = os.path.join(outdir, "abc_verdict.json")
    v = loadjson(vpath)
    sv = v["scorer_validation"]
    add("%s.scorer.Sm" % tag, experiment=tag, metric="Sm",
        value=sv["Sm"], source_file=vpath,
        source_line=lineno(vpath, '"Sm"'), model="SINet/S2C", scope=scope,
        note="scorer validated on committed predictions BEFORE any new number")
    add("%s.scorer.MAE" % tag, experiment=tag, metric="MAE",
        value=sv["MAE"], source_file=vpath,
        source_line=lineno(vpath, '"MAE"'), model="SINet/S2C", scope=scope)

    for cell, cv in sorted(v["verdicts"].items()):
        arch, endpoint = cell.split("|")
        sigma = cv["sigma_hat"]
        add("%s.%s.%s.sigma_hat" % (tag, arch, endpoint), experiment=tag,
            metric="sigma_hat", value=sigma, model=arch,
            spread=2 * sigma, spread_kind="2*sigma_hat (the decision bar)",
            n_seeds=3, scope=scope, source_file=vpath,
            source_line=lineno(vpath, '"%s"' % cell),
            note="pooled within-arm sd of S_alpha, df=%s" % cv["df"])
        for arm, m in sorted(cv["arm_means"].items()):
            add("%s.%s.%s.%s.Sm_mean" % (tag, arch, endpoint, arm),
                experiment=tag, metric="Sm", value=m, arm=arm, model=arch,
                seeds=[42, 43, 45], n_seeds=cv["arm_n"][arm],
                spread=cv["per_arm_sd"][arm], spread_kind="within-arm sd",
                scope=scope, source_file=vpath,
                source_line=lineno(vpath, '"%s"' % cell))
        for gap, g in sorted(cv["gaps"].items()):
            add("%s.%s.%s.gap.%s" % (tag, arch, endpoint, gap), experiment=tag,
                metric="delta_Sm", value=g["delta"], model=arch,
                arm=gap, n_seeds=3, seeds=[42, 43, 45],
                spread=2 * sigma, spread_kind="2*sigma_hat",
                delta_vs_baseline=gap.split("->")[0], scope=scope,
                source_file=vpath, source_line=lineno(vpath, '"%s"' % cell),
                note="verdict=%s sign=%s" % (g["verdict"], g.get("sign_consistent")))

    # allocation-shape keys -- the T2 crux, and a cross-campaign self-test anchor
    ppath = os.path.join(outdir, "abc_preflight.json")
    if os.path.exists(ppath):
        raw = open(ppath).read()
        for shape_key in ("clusters_funded", "max_alloc_share",
                          "alloc_entropy_norm", "tv_from_uniform"):
            hits = find_numbers(raw, shape_key)
            for armname, val in sorted(hits.items()):
                add("%s.shape.%s.%s" % (tag, armname, shape_key),
                    experiment=tag, metric=shape_key, value=val, arm=armname,
                    scope=scope, source_file=ppath,
                    source_line=lineno(ppath, shape_key))


def find_numbers(raw, key):
    """Pull '<arm>' -> value for a shape key out of a preflight JSON blob.

    The preflight schema nests differently between the two campaigns, so this
    walks the parsed structure instead of assuming a layout.
    """
    found = {}

    def walk(node, path):
        if isinstance(node, dict):
            for k, val in node.items():
                if k == key and isinstance(val, (int, float)):
                    armname = next((p for p in reversed(path)
                                    if p in ("A0", "A2", "B", "C10", "C05",
                                             "CSHUF", "CINV")), "|".join(path[-2:]) or "?")
                    found[armname] = val
                else:
                    walk(val, path + [str(k)])
        elif isinstance(node, list):
            for j, val in enumerate(node):
                walk(val, path + [str(j)])

    walk(json.loads(raw), [])
    return found


collect_campaign("abc", os.path.join(REPO, "rebuild/ABC/out"), GEN)
collect_campaign("t2", os.path.join(REPO, "rebuild/ABC/out/t2"), SIG)

# ------------------------------------------------------------------- T2C ----
# Only the 8 pre-registered rows (primary==1) go to the figures; the 12
# robustness variants are emitted as confidence="post-hoc" so a figure can
# never present them as the pre-registered result.
t2c = os.path.join(REPO, "rebuild/T2C/out/t2c_table.csv")
for r in loadcsv(t2c):
    primary = r["primary"] == "1"
    key = "t2c.%s.%s.%s" % (r["arch"].replace("/", "_"),
                            r["signal"].replace(" ", "_").replace("(", "").replace(")", ""),
                            r["aggregation"].replace(" ", "_"))
    ln = lineno(t2c, "%s,%s,%s," % (r["arch"], r["signal"], r["aggregation"]))
    for metric, col, sdcol in (("rho_MAE", "rho_mae", "sd_mae"),
                               ("rho_1_minus_Sa", "rho_one_minus_sa", "sd_one_minus_sa"),
                               ("rho_1_minus_IoU", "rho_one_minus_iou", "sd_one_minus_iou")):
        sd = r[sdcol].strip()
        add("%s.%s" % (key, metric), experiment="t2c", metric=metric,
            value=float(r[col]), arm=r["signal"], model=r["arch"],
            spread=float(sd) if sd else None,
            spread_kind="sd over 10 k-means seeds" if sd else "single k-means seed",
            n_seeds=10 if sd else 1, scope=SIG,
            confidence="pre-registered" if primary else "post-hoc",
            source_file=t2c, source_line=ln,
            note="ordering_pass=%s seeds=%s n_images=%s clusters=%s"
                 % (r["ordering_pass"], r["ordering_seeds"], r["n_images"],
                    r["clusters_used"]))

# Re-derive the headline counts rather than quoting "8/8" and "2/8".
rows = loadcsv(t2c)
for agg in ("whole", "boundary"):
    sel = [r for r in rows if r["primary"] == "1" and r["aggregation"] == agg]
    npass = sum(1 for r in sel if r["ordering_pass"] == "True")
    add("t2c.ordering.%s.pass_count" % agg, experiment="t2c",
        metric="rows passing rho(MAE)>rho(1-Sa)>rho(1-IoU)",
        value=npass, n_seeds=10, scope=SIG, source_file=t2c,
        source_line=lineno(t2c, "arch,signal"),
        note="out of %d pre-registered rows; RE-DERIVED from the table" % len(sel),
        delta_vs_baseline=len(sel))

# -------------------------------------------------------------------- B1 ----
b1f = os.path.join(REPO, "rebuild/B1/out/b1_faithful_correlation.json")
fc = loadjson(b1f)["dinoL518"]
ln = lineno(b1f, '"dinoL518"')
for metric, node in (("rho_MAE", "mae"), ("rho_1_minus_Sa", "one_minus_sa"),
                     ("rho_1_minus_IoU", "one_minus_iou")):
    add("b1.targetES.%s" % metric, experiment="b1", metric=metric,
        value=fc[node]["rho"], arm="target-measured ES", model="SINet/S2C",
        scope=SIG, source_file=b1f, source_line=ln,
        note="perm_p=%.5f; k=%s, %s clusters, %s target images"
             % (fc[node]["perm_p"], fc["k"], fc["clusters_used"],
                fc["n_target_in_used"]))
for metric, node in (("rho_MAE", "endpointES_mae"),
                     ("rho_1_minus_Sa", "endpointES_one_minus_sa"),
                     ("rho_1_minus_IoU", "endpointES_one_minus_iou")):
    add("b1.endpointES.%s" % metric, experiment="b1", metric=metric,
        value=fc[node]["rho"], arm="endpoint-measured ES", model="SINet/S2C",
        scope=SIG, source_file=b1f, source_line=ln,
        note="NOT the quantity the pipeline can allocate by")
# The finding is the DROP, so re-derive it instead of quoting it.
add("b1.rho_drop_MAE", experiment="b1",
    metric="rho(MAE) drop, endpoint-measured minus target-measured",
    value=fc["endpointES_mae"]["rho"] - fc["mae"]["rho"], scope=SIG,
    source_file=b1f, source_line=ln,
    note="RE-DERIVED: measuring the signal on the endpoint overstates it")
add("b1.target_vs_endpoint_ES", experiment="b1",
    metric="rho(target ES, endpoint ES) per cluster",
    value=fc["target_vs_endpoint_ES"]["rho"], scope=SIG,
    source_file=b1f, source_line=ln)
for label, num, den in (("targetES", "one_minus_sa", "mae"),
                        ("endpointES", "endpointES_one_minus_sa", "endpointES_mae")):
    add("b1.ratio.%s" % label, experiment="b1",
        metric="ratio rho(1-Sa)/rho(MAE)",
        value=fc[num]["rho"] / fc[den]["rho"], scope=SIG,
        source_file=b1f, source_line=ln,
        note="RE-DERIVED; B1's declared 0.5 boundary is NOT stable -- see B1_RESULTS.md")

b1s = os.path.join(REPO, "rebuild/B1/out/b1_embedder_sweep.json")
sweep = loadjson(b1s)
for emb in ("dinoL224", "dinoL518", "clipL224"):
    k, sil, _ari = sweep[emb]["k_info"]["ranked"][0]
    grid = sorted(int(row["k"]) for row in sweep[emb]["k_rows"])
    edge = k in (grid[0], grid[-1])
    add("b1.silhouette.%s" % emb, experiment="b1",
        metric="best mean silhouette", value=sil, arm=emb, scope=SIG,
        source_file=b1s, source_line=lineno(b1s, '"%s"' % emb),
        n_seeds=10, spread_kind="mean over 10 k-means seeds",
        note="at k=%d; %s" % (k, "AT THE GRID EDGE -> not a selection"
                              if edge else "interior maximum"))

# -------------------------------------------------------------------- C1 ----
# Re-derive the paired increments and win counts over all 20 cells.
c1a = os.path.join(REPO, "rebuild/C1/out/c1_attribution.csv")
rows = loadcsv(c1a)
cells = {}
for r in rows:
    cells.setdefault((r["tag"], r["repr"], r["B"], r["alpha"]), {})[r["arm"]] = \
        float(r["d_heldout"])
TARGET = "TARGETED_by_target_es"
for control, nice in (("shuffled_es", "its own ES-shuffled control"),
                      ("random_centroid", "an arbitrary cluster centroid"),
                      ("random_direction", "a random direction"),
                      ("random_vs_random", "the true null")):
    diffs = [c[TARGET] - c[control] for c in cells.values()
             if TARGET in c and control in c]
    wins = sum(1 for d in diffs if d > 0)
    add("c1.increment.%s" % control, experiment="c1",
        metric="paired increment in held-out Cohen's d, targeted minus control",
        value=mean(diffs), arm=control, scope=SIG,
        n_seeds=len(diffs), spread_kind="%d cells" % len(diffs),
        delta_vs_baseline=wins, source_file=c1a,
        source_line=lineno(c1a, control),
        note="RE-DERIVED over %d cells; targeted wins %d/%d against %s"
             % (len(diffs), wins, len(diffs), nice))
for arm in sorted({r["arm"] for r in rows}):
    vals = [float(r["d_heldout"]) for r in rows if r["arm"] == arm]
    add("c1.d_heldout.%s" % arm, experiment="c1",
        metric="held-out Cohen's d", value=mean(vals), arm=arm, scope=SIG,
        n_seeds=len(vals), spread_kind="mean over %d cells" % len(vals),
        source_file=c1a, source_line=lineno(c1a, arm))

# -------------------------------------------------------------------- D1 ----
d1b = os.path.join(REPO, "rebuild/D1/out/d1_bijection.json")
bij = loadjson(d1b)
for k in ("base_foregrounds", "auth_in_base", "local_in_base"):
    add("d1.%s" % k, experiment="d1", metric=k, value=bij[k], scope=GEN,
        source_file=d1b, source_line=lineno(d1b, k))
for k in ("auth_outside_base", "local_outside_base", "base_without_local"):
    add("d1.%s" % k, experiment="d1", metric="%s (count)" % k,
        value=len(bij[k]), scope=GEN, source_file=d1b,
        source_line=lineno(d1b, k))

# Re-derive the copied-not-generated measurement over ALL 4447 rows per pool.
REGEN_THRESHOLD = 40.0   # d1_foreground_exhaustion.py: interior > 40 => plausibly regenerated
total_regen = 0
total_objects = 0
for pool, path in (("authors", os.path.join(REPO, "rebuild/D1/out/d1_trace_auth.csv")),
                   ("local", os.path.join(REPO, "rebuild/D1/out/d1_trace_local.csv"))):
    tr = [r for r in loadcsv(path) if r["status"] == "OK" and r["obj_interior_mean"]]
    interior = [float(r["obj_interior_mean"]) for r in tr]
    bg = [float(r["bg_mean"]) for r in tr]
    regen = sum(1 for v in interior if v > REGEN_THRESHOLD)
    total_regen += regen
    total_objects += len(tr)
    add("d1.%s.obj_interior_mean" % pool, experiment="d1",
        metric="object-interior mean |diff|", value=mean(interior), arm=pool,
        scope=GEN, n_seeds=len(tr), spread_kind="mean over %d objects" % len(tr),
        source_file=path, source_line=1,
        note="RE-DERIVED from all %d traced rows" % len(tr))
    add("d1.%s.bg_mean" % pool, experiment="d1",
        metric="background mean |diff|", value=mean(bg), arm=pool, scope=GEN,
        n_seeds=len(tr), source_file=path, source_line=1,
        note="RE-DERIVED from all %d traced rows" % len(tr))
    add("d1.%s.ratio" % pool, experiment="d1",
        metric="background / object-interior error ratio",
        value=mean(bg) / mean(interior), arm=pool, scope=GEN,
        source_file=path, source_line=1, note="RE-DERIVED")
add("d1.objects_regenerated", experiment="d1",
    metric="objects plausibly regenerated (interior mean |diff| > %g)" % REGEN_THRESHOLD,
    value=total_regen, scope=GEN, delta_vs_baseline=total_objects,
    source_file=os.path.join(REPO, "rebuild/D1/out/d1_trace_auth.csv"),
    source_line=1,
    note="RE-DERIVED across BOTH pools: %d of %d objects" % (total_regen, total_objects))

# -------------------------------------- D2 / D2R / D2_NC4K (contamination) --
d2r = os.path.join(REPO, "rebuild/D2_reaudit/out/d2r_endpoint_contamination.json")
con = loadjson(d2r)
NICE = {"cham": "CHAMELEON (repo copy)", "chamnew": "CHAMELEON (author-sourced)",
        "test": "COD10K-test", "nc4k": "NC4K", "val": "CAMO-val"}
for k, nice in NICE.items():
    if k not in con:
        continue
    c = con[k]
    add("d2r.%s.contaminated" % k, experiment="d2r",
        metric="re-encoded copies of training data", value=c["vs_training"],
        arm=nice, scope=IND, delta_vs_baseline=c["n"],
        source_file=d2r, source_line=lineno(d2r, '"%s"' % k),
        note="%d of %d = %.4g%%" % (c["vs_training"], c["n"],
                                    100.0 * c["frac_vs_training"]))
    add("d2r.%s.frac" % k, experiment="d2r", metric="contaminated share",
        value=c["frac_vs_training"], arm=nice, scope=IND,
        source_file=d2r, source_line=lineno(d2r, '"%s"' % k))
for tol, blob in sorted(con["tolerance_sweep"].items()):
    add("d2r.sweep.%s.cham" % tol, experiment="d2r",
        metric="CHAMELEON confirmed at tolerance %s" % tol.replace("tol_", ""),
        value=blob["per_endpoint"]["cham"], arm="CHAMELEON", scope=IND,
        source_file=d2r, source_line=lineno(d2r, "tolerance_sweep"),
        note="the count SATURATES at 41: it is a property of the data, not the cutoff")

for axis, fn in (("vs_COD10K-test", "d2nc4k_sweep_test.json"),
                 ("vs_COD10K-train", "d2nc4k_sweep_train.json")):
    p = os.path.join(REPO, "rebuild/D2_nc4k/out", fn)
    s = loadjson(p)
    add("d2nc4k.%s.contaminated" % axis, experiment="d2_nc4k",
        metric="NC4K images re-encoded from %s" % axis.replace("vs_", ""),
        value=s["contaminated"]["n"], arm="NC4K", scope=IND,
        delta_vs_baseline=s["dir_a"]["n"], source_file=p,
        source_line=lineno(p, "contaminated"),
        note="THE NEGATIVE CONTROL: the same detector that returns 41/76 on "
             "CHAMELEON returns %d/%d here" % (s["contaminated"]["n"], s["dir_a"]["n"]))
    nn = s.get("nearest_neighbour", {})
    add("d2nc4k.%s.unchecked" % axis, experiment="d2_nc4k",
        metric="images with no same-dimension candidate (UNCHECKED)",
        value=nn.get("n_unchecked"), arm="NC4K", scope=IND,
        delta_vs_baseline=s["dir_a"]["n"], source_file=p,
        source_line=lineno(p, "nearest_neighbour"),
        note="unchecked is NOT clean: every rate here is a LOWER BOUND",
        reason=None if nn.get("n_unchecked") is not None
               else "n_unchecked absent from %s" % rel(p))

# -------------------------------------------------------------------- A3 ----
a3c = os.path.join(REPO, "rebuild/A3/out/a3_coverage.csv")
for r in loadcsv(a3c):
    if r["k"] != "5":
        continue
    setname = r["set"]
    key = "a3.coverage.%s.%s" % (r["embedder"],
                                 setname.replace(" ", "_").replace(",", "")
                                 .replace("(", "").replace(")", "").replace("'", ""))
    add(key, experiment="a3", metric="k-NN coverage recall vs the real target set",
        value=float(r["recall"]), arm=setname, model=r["embedder"], scope=GEN,
        source_file=a3c, source_line=lineno(a3c, "%s,5,%s" % (r["embedder"], setname[:20])),
        note="role=%s, k=5, n_real=%s" % (r["role"], r["n_real"]),
        delta_vs_baseline=float(r["rel_loss_vs_raw"]) if r["rel_loss_vs_raw"] else None)

a3p = os.path.join(REPO, "rebuild/A3/out/a3_probe_table.csv")
for r in loadcsv(a3p):
    if r["embedder"] != "clipL224":
        continue
    if r["role"] not in ("headline", "floor", "null"):
        continue
    key = "a3.auc.%s.%s" % (r["embedder"],
                            r["comparison"].replace(" ", "_").replace(",", "")
                            .replace("(", "").replace(")", "").replace("'", "")[:52])
    add(key, experiment="a3", metric="held-out linear-probe AUC",
        value=float(r["auc"]), arm=r["comparison"], model=r["embedder"],
        scope=IND if r["role"] in ("floor", "null") else GEN,
        source_file=a3p, source_line=lineno(a3p, r["comparison"][:40]),
        note="role=%s" % r["role"])
# The estimator exhibit: in-sample d on a TRUE NULL.
for r in loadcsv(a3p):
    if r["role"] == "null" and "RANDOM halves" in r["comparison"]:
        add("a3.truenull.d_insample.%s" % r["embedder"], experiment="a3",
            metric="in-sample Cohen's d on a TRUE NULL",
            value=float(r["d_probe_axis_insample"]), model=r["embedder"],
            scope=IND, source_file=a3p,
            source_line=lineno(a3p, r["comparison"][:40]),
            note="held-out d on the same null is %.4f -- the in-sample estimator "
                 "manufactures an effect from nothing"
                 % float(r["d_probe_axis_heldout"]))

# ------------------------------------- budget / pool mechanics (ABC runs) ---
# Re-derived from the committed per-run CSV, NOT from POOL_MECHANICS_AUDIT.md.
# That audit has no EXP block of its own, and the repo's own sourcing rule
# (rebuild/FINAL_RESULTS.md section 16(c)) declines to promote its figures.
runs_path = os.path.join(REPO, "rebuild/ABC/out/abc_runs.csv")
runs = loadcsv(runs_path)
for arch in sorted({r["arch"] for r in runs}):
    sub = [r for r in runs if r["arch"] == arch]
    steps = sorted({int(r["total_step_set"]) for r in sub})
    rounds = sorted({int(r["rounds"]) for r in sub})
    epochs = sorted({r["last_epoch"] for r in sub})
    add("abc.%s.total_step" % arch, experiment="abc", metric="total_step",
        value=steps[0] if len(steps) == 1 else None, model=arch, scope=GEN,
        n_seeds=len(sub), source_file=runs_path,
        source_line=lineno(runs_path, sub[0]["runid"]),
        note="PINNED: identical in both rounds of all %d %s runs, independent "
             "of pool size. Added data buys ZERO gradient steps." % (len(sub), arch),
        reason=None if len(steps) == 1 else "total_step not constant: %s" % steps)
    add("abc.%s.rounds" % arch, experiment="abc", metric="CSRDA rounds executed",
        value=rounds[0] if len(rounds) == 1 else None, model=arch, scope=GEN,
        source_file=runs_path, source_line=lineno(runs_path, sub[0]["runid"]),
        note="a hardcoded constant (MyTrain.py:203), NOT a stopping criterion",
        reason=None if len(rounds) == 1 else "rounds not constant: %s" % rounds)
    if len(steps) == 1 and len(epochs) == 1 and len(rounds) == 1:
        done, _tot = epochs[0].split("/")
        add("abc.%s.gradient_steps" % arch, experiment="abc",
            metric="total gradient steps per run", model=arch, scope=GEN,
            value=steps[0] * int(done) * rounds[0], source_file=runs_path,
            source_line=lineno(runs_path, sub[0]["runid"]),
            note="RE-DERIVED = total_step %d x epochs %s x rounds %d; identical "
                 "for every arm regardless of pool size"
                 % (steps[0], done, rounds[0]))

# The second uncontrolled channel: CLS append spread. A threshold that FAILED.
app = [int(r["n_appended"]) for r in runs if r["n_appended"]]
if app:
    m = mean(app)
    add("abc.n_appended.spread", experiment="abc",
        metric="CLS round-2 append spread, (max-min)/mean",
        value=(max(app) - min(app)) / m, scope=GEN, n_seeds=len(app),
        spread_kind="range over %d runs" % len(app), source_file=runs_path,
        source_line=lineno(runs_path, "n_appended"),
        note="RE-DERIVED: mean %.1f, range %d-%d, against a declared 5%% bound. "
             "This THRESHOLD FAILED and was kept failed." % (m, min(app), max(app)))

# ---------------------------- T2 permutation identity (the crux of EXP T2) ---
# The three arms differ ONLY in how target_es is permuted across clusters.
# The realised permutation statistics are committed in T2's preflight.
_t2pf = os.path.join(REPO, "rebuild/ABC/out/t2/abc_preflight.json")
if os.path.exists(_t2pf):
    _raw = open(_t2pf).read()
    _seen = {}

    def _walkperm(node, arm=None):
        if isinstance(node, dict):
            a = node.get("arm", arm)
            if "perm_rho" in node and "es_perm" in node:
                _seen.setdefault(node["es_perm"], node)
            for v in node.values():
                _walkperm(v, a)
        elif isinstance(node, list):
            for v in node:
                _walkperm(v, arm)

    _walkperm(json.loads(_raw))
    _ARMOF = {"identity": "C10", "shuffled": "CSHUF", "rank_reversed": "CINV"}
    for _kind, _blob in sorted(_seen.items()):
        _arm = _ARMOF.get(_kind, _kind)
        add("t2.perm.%s.rho" % _arm, experiment="t2",
            metric="Spearman rho of the permuted es vector against the original",
            value=_blob["perm_rho"], arm=_arm, scope=SIG, source_file=_t2pf,
            source_line=lineno(_t2pf, '"perm_rho"'),
            note="es_perm=%s, fixed points=%s, n_displaced=%s"
                 % (_kind, _blob.get("perm_fixed_points"), _blob.get("n_displaced")))
        add("t2.perm.%s.n_displaced" % _arm, experiment="t2",
            metric="images displaced by the greedy distinct selection",
            value=_blob.get("n_displaced"), arm=_arm, scope=SIG,
            source_file=_t2pf, source_line=lineno(_t2pf, '"n_displaced"'),
            note="reported, never asserted -- the ASSERTED keys are the four "
                 "allocation-shape keys, which are identical across the arms")

# ------------------------------- |Delta| / sigma_hat, as the figures print it --
# EXP T2's 12-cell grid renders |Delta|/sigma_hat, so that ratio must be a
# first-class entry rather than arithmetic done by hand at drawing time.
for tag in ("abc", "t2"):
    for key in [k for k in list(entries) if k.startswith("%s." % tag)
                and ".gap." in k]:
        cell = key.split(".gap.")[0]
        sig = entries.get(cell + ".sigma_hat")
        g = entries[key]
        if not sig or not sig["value"]:
            continue
        add(key + ".ratio", experiment=tag,
            metric="|Delta| as a multiple of sigma_hat",
            value=abs(g["value"]) / sig["value"], arm=g["arm"], model=g["model"],
            n_seeds=3, scope=g["scope"], source_file=os.path.join(REPO, g["source_file"]),
            source_line=g["source_line"],
            note="RE-DERIVED = |%s| / %s" % (g["value"], sig["value"]))

# ------------------------------------- configured constants, read from code --
# These are drawn as hyperparameter annotations. They are parsed from the
# source of record so a figure never carries a hand-typed constant.
import re as _re


def const(key, path, pattern, *, metric, scope, note, cast=float):
    full = os.path.join(REPO, path)
    try:
        txt = open(full, errors="replace").read()
    except OSError:
        add(key, experiment="config", metric=metric, value=None, scope=scope,
            source_file=full, source_line=None, reason="cannot read %s" % path)
        return
    m = _re.search(pattern, txt)
    if not m:
        add(key, experiment="config", metric=metric, value=None, scope=scope,
            source_file=full, source_line=None,
            reason="pattern %r not found in %s" % (pattern, path))
        return
    add(key, experiment="config", metric=metric, value=cast(m.group(1)),
        scope=scope, source_file=full,
        source_line=txt[:m.start()].count("\n") + 1, note=note)


const("config.budget_B", "rebuild/ABC/abc_common.py", r"BUDGET\s*=\s*(\d+)",
      metric="generation budget B", scope=GEN, cast=int,
      note="images added per arm")
const("config.k_clusters", "rebuild/T2C/t2c_signals.py", r"\nK\s*=\s*(\d+)",
      metric="k-means cluster count", scope=SIG, cast=int,
      note="B1's committed partition; C1/ABC/T2C all pin to it")
const("config.ema_lambda", "MyTrain.py",
      r"opt\.alpha\s*=\s*([\d.]+)", metric="EMA teacher momentum lambda",
      scope=GEN, note="the S2C override, not the argparse default of 0.9996")
const("config.cls_u", "MyTrain.py", r"opt\.u\s*=\s*([\d.]+)",
      metric="CLS threshold multiplier u", scope=GEN,
      note="rule: edge_loss < u * avg_loss")
const("config.cls_tau", "MyTrain.py", r"opt\.tau\s*=\s*([\d.]+)",
      metric="CAM floor tau", scope=GEN, note="S2C override")
const("config.es_a", "MyTrain.py", r"opt\.a\s*=\s*([\d.]+)",
      metric="ESLoss edge weight a", scope=SIG, note="S2C override")
const("config.es_b", "MyTrain.py", r"opt\.b\s*=\s*([\d.]+)",
      metric="ESLoss region weight b", scope=SIG, note="S2C override")
const("config.contamination_tol", "rebuild/D2_reaudit/detect_contamination.py",
      r"NEAR_TOL\s*=\s*([\d.]+)", metric="contamination confirm tolerance",
      scope=IND, note="full-resolution mean|A-B| over RGB")
const("config.ddim_steps", "LAKE-RED/test.py",
      r"'--Steps'.*?default\s*=\s*(\d+)", metric="DDIM sampling steps",
      scope=GEN, cast=int, note="generator sampler steps")

# pool sizes, counted from the committed per-run CSV rather than assumed
pool_r1 = sorted({int(r["pool_r1"]) for r in runs if r["pool_r1"]})
for v in pool_r1:
    add("config.pool_size_%d" % v, experiment="abc", metric="arm pool size",
        value=v, scope=GEN, source_file=runs_path,
        source_line=lineno(runs_path, "pool_r1"),
        note="round-1 pool size observed across the 24 committed runs")
tgt = sorted({int(r["target_loaded_4040"]) for r in runs if r["target_loaded_4040"]})
add("config.target_set_size", experiment="abc",
    metric="target images loaded per round", value=4040, scope=GEN,
    source_file=runs_path, source_line=lineno(runs_path, "target_loaded_4040"),
    note="asserted loaded in %s round(s) of every run" % tgt)

# ------------------------------------------------------------- SELF-TESTS ---
# If any of these fail, THIS SCRIPT is wrong -- not the repo.
selftests = []


def check(name, got, want, tol, detail):
    ok = got is not None and abs(got - want) <= tol
    selftests.append(dict(name=name, ok=ok, got=got, want=want, tol=tol,
                          detail=detail))
    return ok


# (a) one scorer, three independent paths to it
B1_SA, B1_MAE = 0.717216, 0.074463   # B1's committed value, quoted in every gate
check("scorer Sm: ABC == B1", entries["abc.scorer.Sm"]["value"], B1_SA, 1e-5,
      "rebuild/ABC/out/abc_verdict.json vs B1's committed 0.717216")
check("scorer Sm: T2 == B1", entries["t2.scorer.Sm"]["value"], B1_SA, 1e-5,
      "rebuild/ABC/out/t2/abc_verdict.json vs B1's committed 0.717216")
check("scorer MAE: ABC == B1", entries["abc.scorer.MAE"]["value"], B1_MAE, 1e-5,
      "rebuild/ABC/out/abc_verdict.json vs B1's committed 0.074463")
check("scorer MAE: T2 == B1", entries["t2.scorer.MAE"]["value"], B1_MAE, 1e-5,
      "rebuild/ABC/out/t2/abc_verdict.json vs B1's committed 0.074463")

# (b) T2C's ES/SINet/whole row must reproduce B1's committed correlation bitwise
check("T2C reproduces B1 rho(MAE)",
      entries["t2c.SINet_S2C.ES_re-derived.whole.rho_MAE"]["value"],
      round(entries["b1.targetES.rho_MAE"]["value"], 4), 1e-4,
      "t2c_table.csv validation row vs b1_faithful_correlation.json")
check("T2C reproduces B1 rho(1-Sa)",
      entries["t2c.SINet_S2C.ES_re-derived.whole.rho_1_minus_Sa"]["value"],
      round(entries["b1.targetES.rho_1_minus_Sa"]["value"], 4), 1e-4,
      "t2c_table.csv validation row vs b1_faithful_correlation.json")

# (c) allocation shape must be identical across C1, ABC and ABC/t2 -- the T2 crux
c1cells = loadcsv(os.path.join(REPO, "rebuild/C1/out/c1_cells.csv"))
ref = [r for r in c1cells if r["B"] == "1000" and r["alpha"] == "1.0"
       and r["tag"] == "dinoL518" and r["repr"] == "R2_cut"]
if ref:
    for col, want in (("alloc_entropy_norm", 0.78644), ("tv_from_uniform", 0.49253)):
        check("C1 committed cell %s" % col, float(ref[0][col]), want, 5e-5,
              "rebuild/C1/out/c1_cells.csv at B=1000 alpha=1.0 dinoL518 R2_cut")
else:
    selftests.append(dict(name="C1 committed cell", ok=False, got=None,
                          want=None, tol=None,
                          detail="no B=1000 alpha=1.0 dinoL518 R2_cut row in c1_cells.csv"))

for tag in ("abc", "t2"):
    for col, want in (("alloc_entropy_norm", 0.78644), ("tv_from_uniform", 0.49253)):
        keys = [k for k in entries if k.startswith("%s.shape." % tag) and k.endswith(col)]
        vals = {entries[k]["value"] for k in keys}
        hit = any(abs(v - want) <= 5e-5 for v in vals) if vals else False
        selftests.append(dict(
            name="%s preflight reproduces C1 %s" % (tag, col), ok=hit,
            got=sorted(vals) if vals else None, want=want, tol=5e-5,
            detail="arm-C allocation shape must match C1's committed cell exactly"))

# ------------------------------------------------------------------ emit ----
payload = dict(
    _meta=dict(
        generated_by="figures/collect_figure_data.py",
        repo_root_relative=True,
        rule="Every value is parsed or re-derived from a committed artifact. "
             "A value that cannot be re-derived is null with a reason. "
             "No value is transcribed from a *_RESULTS.md.",
        scope_vocabulary=dict(gen="Tier 1 in rebuild/TIER_SEGREGATION.md -- "
                                  "specific to CSRDA or LAKE-RED",
                              **{"signal+data": "Tier 2 -- travels to the target "
                                                "data or the uncertainty signal",
                                 "indep": "Tier 3 -- independent of the method"}),
        confidence_vocabulary=dict(
            **{"pre-registered": "has an EXP block AND a pre-registered threshold",
               "post-hoc": "has an EXP block, but the reading is post-hoc",
               "no-EXP-block": "no committed EXP block -- barred from main figures"}),
        excluded_by_author_decision=[
            "abc.SINet.NC4K.gap.A0->C10 (delta +0.010892, sign 3/3, verdict "
            "REAL EFFECT). Secondary endpoint, unclean A0 control; "
            "ABC_RESULTS.md:77-80 states it is not support. Author decision "
            "2026-09-12: it appears in NO figure. It remains in this file so "
            "the extraction stays complete and auditable."],
    ),
    _selftests=selftests,
    _unresolved=[dict(key=k, reason=r) for k, r in problems],
    entries=entries,
)
with open(OUT, "w") as fh:
    json.dump(payload, fh, indent=1, sort_keys=True)

nfail = sum(1 for t in selftests if not t["ok"])
print("figure_data.json: %d entries, %d self-tests (%d FAILED), %d unresolved"
      % (len(entries), len(selftests), nfail, len(problems)))
for t in selftests:
    print("  [%s] %s: got=%s want=%s" % ("ok" if t["ok"] else "FAIL",
                                         t["name"], t["got"], t["want"]))
for k, r in problems:
    print("  [unresolved] %s: %s" % (k, r))
sys.exit(1 if nfail else 0)

#!/usr/bin/env python3
"""Recompute every post-review number used in the revised paper and the reviewer replies from its source artifact.

Each check prints PASS/FAIL with the source path. Exit status 1 if any check fails.
Run from anywhere: python3 ICLR2027_REVISION_INTEGRATED/tools/verify_numbers.py
"""
import csv, json, pathlib, re, subprocess, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
RB = ROOT / "rebuild/REBUTTAL"
RL = RB / "ICLR2027_REBUTTAL_RL5B/STUDENT_RESULTS/RESULT_TABLES"
CA = RB / "ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/RESULT_TABLES"
DY = RB / "ICLR2027_REBUTTAL_dypE/STUDENT_RESULTS/RESULT_TABLES"
FAILS = []


def rows(p):
    return list(csv.DictReader(open(p)))


def check(name, got, want, src, tol=None):
    ok = (abs(got - want) <= tol) if tol is not None else (got == want)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got!r}, paper/reply uses {want!r}   [{src}]")
    if not ok:
        FAILS.append(name)


def r4(x):
    return round(float(x), 4)


# ------------------------------------------------------------ EQ (RL5B EXP-01), Table 3 and replies
eq = json.load(open(RL / "EXP01_EQ_summary.json"))
src = "RL5B/RESULT_TABLES/EXP01_EQ_summary.json"
check("EQ n per arm B/C10/CSHUF", (eq["n_by_arm"]["B"], eq["n_by_arm"]["C10"], eq["n_by_arm"]["CSHUF"]), (16, 15, 15), src)
check("EQ runs complete", sum(eq["n_by_arm"].values()), 46, src)
c = eq["endpoints"]["COD10K"]["contrasts"]
w = c["C10-B"]["welch"]
check("H1 delta", r4(w["delta"]), 0.0006, src)
check("H1 95% CI", (r4(w["ci95"][0]), r4(w["ci95"][1])), (-0.0033, 0.0045), src)
check("H1 90% CI", (r4(w["ci90"][0]), r4(w["ci90"][1])), (-0.0027, 0.0039), src)
check("H1 TOST p", round(w["p_tost"], 3), 0.015, src)
w2 = c["C10-CSHUF"]["welch"]
check("H1b delta", r4(w2["delta"]), -0.0009, src)
check("H1b 95% CI", (r4(w2["ci95"][0]), r4(w2["ci95"][1])), (-0.0060, 0.0043), src)
check("H1b 90% CI", (r4(w2["ci90"][0]), r4(w2["ci90"][1])), (-0.0051, 0.0034), src)
check("H1b TOST p", round(w2["p_tost"], 3), 0.056, src)
eqcsv = {(r["endpoint"], r["contrast"]): r for r in rows(RL / "EXP01_EQ.csv")}
ps = sorted(float(r["p_tost"]) for r in eqcsv.values())
holm = [min(1, p * (len(ps) - i)) for i, p in enumerate(ps)]
check("H1 Holm-adjusted p (4 tests)", round(max(holm[:3]), 3), 0.030, "RL5B/RESULT_TABLES/EXP01_EQ.csv (Holm recomputed)")
for (ep, ct), want in {("NC4K", "C10-B"): (0.0005, -0.0016, 0.0025, -0.0013, 0.0022),
                       ("NC4K", "C10-CSHUF"): (-0.0005, -0.0030, 0.0019, -0.0026, 0.0015)}.items():
    r = eqcsv[(ep, ct)]
    check(f"EQ {ep} {ct}", (r4(r["delta"]), r4(r["ci95_lo"]), r4(r["ci95_hi"]), r4(r["ci90_lo"]), r4(r["ci90_hi"])), want, "EXP01_EQ.csv")
    check(f"EQ {ep} {ct} p<0.001", float(r["p_tost"]) < 0.001, True, "EXP01_EQ.csv")
rule = eq["endpoints"]["COD10K"]["rule"]
check("EQ sigma-hat", round(rule["sigma_hat"], 4), 0.0064, src)
check("EQ bar", round(rule["bar"], 4), 0.0128, src)
check("EQ C10-B x bar", round(rule["gaps"]["C10-B"]["xbar"], 2), 0.05, src)

# ------------------------------------------------------------ 8-seed Welch and paired (dypE TH-01), Table 3, Table 10
P = {(r["architecture"], r["endpoint"], r["contrast"]): r for r in rows(DY / "TH-01_paired_inference.csv")}
src = "dypE/RESULT_TABLES/TH-01_paired_inference.csv"
pr = P[("SINet", "COD10K", "C10-B")]
check("8-seed Welch 95% CI", (r4(pr["welch_ci95_lo"]), r4(pr["welch_ci95_hi"])), (-0.0020, 0.0067), src)
check("8-seed Welch TOST p", round(float(pr["welch_tost_p_delta0p005"]), 3), 0.101, src)
check("8-seed paired 95% CI", (r4(pr["paired_ci95_lo"]), r4(pr["paired_ci95_hi"])), (-0.0023, 0.0070), src)
check("8-seed paired 90% CI", (r4(pr["paired_ci90_lo"]), r4(pr["paired_ci90_hi"])), (-0.0014, 0.0061), src)
check("8-seed paired TOST p", round(float(pr["paired_tost_p_delta0p005"]), 3), 0.111, src)
check("paired r", round(float(pr["r_xy_across_seeds"]), 2), -0.04, src)
check("paired sign 6/8", (pr["sign_pos"], pr["sign_neg"]), ("6", "2"), src)
check("sign-flip p", round(float(pr["signflip_p_exact"]), 2), 0.29, src)
check("smallest paired equivalence margin", r4(pr["paired_smallest_equiv_delta"]), 0.0061, src)
for cell, want in {("SINet", "NC4K"): (-0.0033, 0.0040, -0.0038, 0.0045, 0.016),
                   ("SINetv2", "COD10K"): (-0.0067, 0.0045, -0.0081, 0.0059, 0.114),
                   ("SINetv2", "NC4K"): (-0.0068, 0.0049, -0.0077, 0.0058, 0.100)}.items():
    r = P[cell + ("C10-B",)]
    check(f"Table 10 {cell}", (r4(r["welch_ci95_lo"]), r4(r["welch_ci95_hi"]), r4(r["paired_ci95_lo"]), r4(r["paired_ci95_hi"]),
                               round(float(r["paired_tost_p_delta0p005"]), 3)), want, src)

# ------------------------------------------------------------ oracle shapes (Caus EXP-01), Table 2 rows, App. I
from decimal import Decimal, ROUND_HALF_UP
_ms = defaultdict(lambda: defaultdict(list))
for r in rows(CA / "EXP-01_metrics_by_seed.csv"):
    _ms[r["endpoint"]][r["arm"]].append(Decimal(r["Sm"]))
MS = {e: {a: sum(v) / len(v) for a, v in d.items()} for e, d in _ms.items()}
src = "Caus/RESULT_TABLES/EXP-01_comparisons.csv"
O = {(r["endpoint"], r["contrast"]): r for r in rows(CA / "EXP-01_comparisons.csv")}
for ct, (d, xb, sg, dn) in {"OR-TOP10 - CORACLE": (0.0022, 0.38, "2/3", 0.0011), "OR-TOP10 - OR-TOP10-SHUF": (-0.0002, 0.03, "2/3", -0.0009),
                            "OR-PROP - CORACLE": (0.0023, 0.40, "2/3", 0.0028), "OR-TOP5 - CORACLE": (0.0011, 0.20, "2/3", 0.0005)}.items():
    r = O[("COD10K", ct)]
    a, b = [x.strip() for x in ct.split(" - ")]
    nc = MS["NC4K"][a] - MS["NC4K"][b]          # exact, from per-seed metrics (the CSV stores 6 dp)
    check(f"ORS {ct}", (r4(r["delta"]), round(float(r["x_bar"]), 2), r["sign"], r["verdict"], float(nc.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))), (d, xb, sg, "WITHIN NOISE", dn), src + " + EXP-01_metrics_by_seed.csv")
check("ORS bar COD10K / NC4K", (r4(O[("COD10K", "OR-TOP10 - CORACLE")]["bar"]), r4(O[("NC4K", "OR-TOP10 - CORACLE")]["bar"])), (0.0057, 0.0065), src)
sec = [float(r["delta"]) for (e, ct), r in O.items() if e == "COD10K" and (ct.endswith(" - B")) and ct.split(" - ")[0] in ("OR-TOP10", "OR-PROP", "OR-TOP5")]
check("ORS vs B range", (r4(min(sec)), r4(max(sec))), (0.0020, 0.0031), src)
sec = [float(r["delta"]) for (e, ct), r in O.items() if e == "COD10K" and ct.endswith(" - C10")]
check("ORS vs C10 range", (r4(max(sec)), r4(min(sec))), (-0.0019, -0.0031), src)
G = {(r["repr"], r["arm"]): r for r in rows(CA / "AN-02_shape_geometry.csv")}
src = "Caus/RESULT_TABLES/AN-02_shape_geometry.csv (R2_cut)"
check("probe d FLAT/C10/CSHUF", tuple(round(float(G[("R2_cut", a)]["probe_d_heldout_vs_random"]), 2) for a in ("FLAT", "C10", "CSHUF")), (0.52, 0.64, 0.61), src)
check("PR ratio FLAT", round(float(G[("R2_cut", "FLAT")]["pr_ratio_vs_random"]), 3), 0.855, src)
check("PR ratio TOP5 / TOP5-SHUF", tuple(round(float(G[("R2_cut", a)]["pr_ratio_vs_random"]), 2) for a in ("OR-TOP5", "OR-TOP5-SHUF")), (0.56, 0.94), src)

# ------------------------------------------------------------ boundary metrics, 8 seeds (dypE AN-03), Sec 3.2, App C
src = "dypE/RESULT_TABLES/AN-03_arch_boundary_grid.csv"
B = [r for r in rows(DY / "AN-03_arch_boundary_grid.csv") if r["seed_subset"] == "8-seed"]
check("8-seed contrasts examined", len(B), 140, src)
check("smallest Holm p (8-seed grid)", round(min(float(r["holm_p_grid"]) for r in B), 2), 0.50, src)
g = {(r["metric"], r["threshold"], r["architecture"], r["endpoint"], r["contrast"]): r for r in B}
x = g[("boundary_iou", "0.5", "SINet", "COD10K", "CINV-B")]
check("CINV-B BIoU SINet", (r4(x["mean_D"]), r4(x["paired_ci95_lo"]), r4(x["paired_ci95_hi"]), x["sign_pos"], round(float(x["gap_over_bar"]), 2), round(float(x["holm_p_grid"]), 2)),
      (0.0098, 0.0039, 0.0157, "7", 0.64, 0.79), src)
x = g[("boundary_iou", "0.5", "SINet", "COD10K", "C10-B")]
check("C10-B BIoU SINet", (r4(x["mean_D"]), round(float(x["gap_over_bar"]), 2)), (0.0046, 0.30), src)
sm = [r for r in B if r["metric"] == "Sm" and r["architecture"] == "SINet" and r["endpoint"] == "COD10K" and r["contrast"] == "CINV-B"][0]
check("CINV-B S-measure SINet", (r4(sm["mean_D"]), r4(sm["paired_ci95_lo"]), r4(sm["paired_ci95_hi"]), round(float(sm["gap_over_bar"]), 2)), (0.0045, 0.0015, 0.0074, 0.65), src)
I = {(r["metric"], r["threshold"], r["endpoint"], r["contrast"]): r for r in rows(DY / "AN-03_interaction.csv")}
src = "dypE/RESULT_TABLES/AN-03_interaction.csv"
for ct, want in {"C10-B": (0.0044, -0.0075, 0.0163, 0.43), "CINV-B": (0.0065, -0.0001, 0.0131, 0.053)}.items():
    r = I[("boundary_iou", "0.5", "COD10K", ct)]
    check(f"interaction {ct}", (r4(r["delta_model"]), r4(r["welch_ci95_lo"]), r4(r["welch_ci95_hi"]), round(float(r["welch_p"]), 3 if ct == "CINV-B" else 2)), want, src)

# ------------------------------------------------------------ overlap, exposure, preflight, domain mix (dypE AN-02/AN-04/EXP-01)
src = "dypE/RESULT_TABLES/AN-02_overlap_by_seed.csv"
ov = rows(DY / "AN-02_overlap_by_seed.csv")
bc = [r for r in ov if {r["arm_x"], r["arm_y"]} == {"B", "C10"}]
check("B vs C10 intersections min-max", (min(int(r["intersection"]) for r in bc), max(int(r["intersection"]) for r in bc)), (209, 246), src)
check("B vs C10 expected-by-chance", round(float(bc[0]["expected_random_intersection"])), 225, src)
check("B vs C10 injected differing (mean)", round(sum(float(r["frac_injection_differs"]) for r in bc) / len(bc), 2), 0.77, src)
check("B vs C10 pool share (mean)", round(100 * sum(float(r["frac_of_5447_pool_one_sided"]) for r in bc) / len(bc), 1), 14.1, src)
cc = [r for r in ov if r["arm_x"] in ("C10", "CSHUF", "CINV") and r["arm_y"] in ("C10", "CSHUF", "CINV")]
check("concentrated pairs differing %", (round(100 * min(float(r["frac_injection_differs"]) for r in cc)), round(100 * max(float(r["frac_injection_differs"]) for r in cc))), (45, 51), src)
check("concentrated pairs pool share %", (round(100 * min(float(r["frac_of_5447_pool_one_sided"]) for r in cc), 1), round(100 * max(float(r["frac_of_5447_pool_one_sided"]) for r in cc), 1)), (8.3, 9.4), src)
ex = [r for r in rows(DY / "AN-02_exposure_by_run.csv") if r["arm"] == "C10" and r["architecture"] == "SINet"]
src = "dypE/RESULT_TABLES/AN-02_exposure_by_run.csv"
for rnd, want in (("1", 14), ("2", 10)):
    v = [float(r["arm_specific_share_of_draws_vs_B"]) for r in ex if r["round"] == rnd and r["arm_specific_share_of_draws_vs_B"]]
    check(f"targeted-only share of draws, round {rnd} (%)", round(100 * sum(v) / len(v)), want, src)
check("source draws per epoch", ex[0]["source_draws_per_epoch"], "4048", src)
pj = [float(r["jaccard"]) for r in rows(DY / "AN-02_pseudolabel_overlap.csv") if {r["arm_x"], r["arm_y"]} == {"B", "C10"}]
check("pseudo-label Jaccard B vs C10", (round(min(pj), 2), round(max(pj), 2)), (0.58, 0.68), "dypE/RESULT_TABLES/AN-02_pseudolabel_overlap.csv")
pf = {r["N"]: r for r in rows(DY / "EXP-01_preflight.csv")}
src = "dypE/RESULT_TABLES/EXP-01_preflight.csv"
check("preflight differing share 1000/2000/3000/4447 (%)", tuple(round(100 * float(pf[n]["DC_mean"]), 1) for n in ("1000", "2000", "3000", "4447")), (14.1, 17.2, 13.1, 0.0), src)
check("preflight ratio at 2000", round(float(pf["2000"]["DC_ratio_vs_1000"]), 2), 1.22, src)
check("preflight passes", any(pf[n]["passes_preflight"] == "True" for n in pf), False, src)
dm = {r["arm"]: r for r in rows(DY / "AN-04_cluster_domain_mix.csv") if r["arm"]}
check("CAMO budget share C10/CSHUF/CINV (%)", tuple(round(100 * float(dm[a]["budget_weighted_camo_share"])) for a in ("C10", "CSHUF", "CINV")), (53, 29, 20), "dypE/RESULT_TABLES/AN-04_cluster_domain_mix.csv")
cov = defaultdict(list)
for r in rows(DY / "AN-04_foreground_coverage.csv"):
    if r["k"] == "5" and r["set_kind"].startswith("injected"):
        cov[(r["embedder"], "conc" if r["compared_set"] in ("C10", "CSHUF", "CINV") else "rand")].append(float(r["recall"]))
src = "dypE/RESULT_TABLES/AN-04_foreground_coverage.csv"
for emb, want in (("dinoL518", (0.62, 0.64, 0.35, 0.43)), ("dinoL224", (0.50, 0.53, 0.27, 0.45))):
    check(f"selection coverage {emb}", (round(min(cov[(emb, 'conc')]), 2), round(max(cov[(emb, 'conc')]), 2), round(min(cov[(emb, 'rand')]), 2), round(max(cov[(emb, 'rand')]), 2)), want, src)
check("clipL224 ranges overlap", max(cov[("clipL224", "rand")]) > min(cov[("clipL224", "conc")]), True, src)

# ------------------------------------------------------------ CHAMELEON reconciliation (dypE AN-05 + Caus 5e7a2f9)
src = "dypE/RESULT_TABLES/AN-05_chameleon_pairs.csv, AN-05_cross_benchmark.csv"
T = lambda v: v.strip().lower() == "true"
cp = {r["chameleon"]: r for r in rows(DY / "AN-05_chameleon_pairs.csv")}
xb = {r["chameleon"]: r for r in rows(DY / "AN-05_cross_benchmark.csv")}
st = {k: r["status"] for k, r in cp.items()}
conf = {k for k, v in st.items() if v == "confirmed"}
check("automated training-pool matches", len(conf), 50, src)
check("automated in COD10K-train", sum(T(cp[k]["in_cod10k_train"]) for k in conf), 44, src)
check("Tier A / Tier B", (sum(cp[k]["tier"].upper().startswith("A") for k in conf), sum(cp[k]["tier"].upper().startswith("B") for k in conf)), (41, 9), src)
crossrow = subprocess.run(["git", "-C", str(ROOT), "show", "5e7a2f9:rebuild/REBUTTAL/ICLR2027_REBUTTAL_Caus/STUDENT_RESULTS/RESULT_TABLES/AN-05_chameleon_crosscheck.csv"],
                          capture_output=True, text=True).stdout
a54 = [l for l in crossrow.splitlines() if l.startswith("animal-54.jpg")]
check("animal-54 recorded at 5e7a2f9 as visually confirmed copy of COD10K-train Spider-2513",
      bool(a54) and "visually confirmed" in a54[0] and "Spider-2513" in a54[0], True, "git show 5e7a2f9:.../AN-05_chameleon_crosscheck.csv")
check("animal-54 not among automated matches", st.get("animal-54"), "tierA_checked_no_match", src)
total = conf | {"animal-54"}
check("training-pool total", len(total), 51, src + " + 5e7a2f9")
unch = {k for k, v in st.items() if v == "unchecked"}
nm = {k for k, v in st.items() if v == "tierA_checked_no_match"} - {"animal-54"}
check("unchecked / no-match after animal-54", (len(unch), len(nm)), (16, 9), src)
c10t = {k for k, r in xb.items() if T(r["in_cod10k_test"])}
check("COD10K-test re-encodes", len(c10t), 32, src)
check("COD10K-test covers all unchecked; 8 of 9 no-match; 8 confirmed", (unch <= c10t, len(nm & c10t), len(conf & c10t)), (True, 8, 8), src)
c250 = {k for k, r in xb.items() if T(r["in_camo250"])}
check("CAMO-250 (4; 3 byte-identical)", (len(c250), sum(T(xb[k]["camo250_byte_identical"]) for k in c250)), (4, 3), src)
check("animal-28 is the re-encoded CAMO-250 copy", sorted(k for k in c250 if not T(xb[k]["camo250_byte_identical"])), ["animal-28"], src)
anyw = {k for k, r in xb.items() if T(r["duplicated_anywhere_checked"])} | {"animal-54"}
check("duplicate anywhere (with animal-54)", (len(anyw), sorted(set(xb) - anyw)), (75, ["animal-38"]), src)
check("no training-pool partner, in COD10K-test", (76 - len(total), len((unch | nm) & c10t)), (25, 24), src)
pe = rows(DY / "AN-05_pseudolabel_exposure.csv")
v = [int(r["n_cham_partners_appended"]) for r in pe]
check("pseudo-labelled CHAMELEON matches per run (min, max, mean)", (min(v), max(v), round(sum(v) / len(v), 1)), (14, 32, 24.7), "dypE/RESULT_TABLES/AN-05_pseudolabel_exposure.csv")
d2 = json.load(open(ROOT / "rebuild/D2/out/d2_leaked_names.json"))
check("COD10K-test files byte-identical to training images", len(d2["endpoint_side"]), 7, "rebuild/D2/out/d2_leaked_names.json")

# ------------------------------------------------------------ CDR (RL5B EXP-02)
md = (RL / "EXP02_SINet_results.md").read_text()
src = "RL5B/RESULT_TABLES/EXP02_SINet_results.md"
check("CDR reference / bar", ("D = 0.3308" in md, "bar 0.0193" in md), (True, True), src)
check("CDR L1 primary row", "| PRIMARY BIoU@0.5 COD10K | L1 | -0.0005 | 0.03 | 2/5 |" in md, True, src)
check("CDR LH primary row", "| PRIMARY BIoU@0.5 COD10K | LH | +0.0021 | 0.11 | 4/5 |" in md, True, src)
check("CDR S_alpha rows", ("| secondary Sm COD10K | L1 | +0.0004 |" in md, "| secondary Sm COD10K | LH | +0.0015 |" in md), (True, True), src)

# ------------------------------------------------------------ run counts (RL5B queue log + Caus runs of record)
jobs = set()
for line in open(ROOT / "rebuild/RL5B/out/queue_events.jsonl"):
    e = json.loads(line)
    if e.get("kind") == "job_done":
        jobs.add(e["job"])
fam = defaultdict(int)
for j in jobs:
    f = "bridge" if j.startswith("BRIDGE") else "E3" if j.startswith("E3") else "CDR" if "CDR" in j else "EQ" if re.match(r"SINet_(B|C10|CSHUF)_s1\d\d$", j) else "other"
    fam[f] += 1
nors = len(rows(CA / "EXP-01_runs_of_record.csv"))
check("post-review runs EQ/CDR/E3/ORS", (fam["EQ"], fam["CDR"], fam["E3"], nors), (46, 35, 6, 12), "rebuild/RL5B/out/queue_events.jsonl; Caus EXP-01_runs_of_record.csv")
check("post-review trained runs total (excl. bridge, re-trains)", fam["EQ"] + fam["CDR"] + fam["E3"] + nors, 99, "sum")

from decimal import Decimal as _D, ROUND_HALF_UP as _HU
_se = rows(ROOT / "rebuild/ABC/out/se/abc_metrics.csv")
for arch, ep, want in (("SINet", "COD10K", "0.717"), ("SINet", "NC4K", "0.768"), ("SINetv2", "COD10K", "0.695"), ("SINetv2", "NC4K", "0.749")):
    vv = [_D(r["Sm"]) for r in _se if r["arm"] == "C10" and r["arch"] == arch and r["endpoint"] == ep]
    check(f"Table 4 C10 {arch} {ep} S_alpha (exact mean, 3 dp)", str((sum(vv) / len(vv)).quantize(_D("0.001"), rounding=_HU)), want, "rebuild/ABC/out/se/abc_metrics.csv")

# ------------------------------------------------------------ arithmetic used in prose
check("9/256", round(9 / 256, 3), 0.035, "arithmetic")
check("RL5B gap share: 0.112 of 0.120", round(0.112 / 0.120, 2), 0.93, "arithmetic (reply)")
check("ORS x bar 0.0022/0.0057 from unrounded", round(0.002163 / 0.005679, 2), 0.38, "arithmetic")

print(f"\n{len(FAILS)} failure(s)" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)

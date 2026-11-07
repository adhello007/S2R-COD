# PREREGISTRATION_WS4.md — a same-code supervised anchor on the standard split

> **Committed before the first WS4 training run. Never edited after any WS4 number exists.**
>
> Dated **2026-11-07 (IST)**. Additive. It alters, supersedes or re-decides no committed
> campaign, rule or verdict. Driver: `rebuild/REBUTTAL/ws4_anchor.py` (commit `9bb08a7`).

## §WS4.0 What this is, and what it is not

Reviewer RL5B notes that C10's absolute scores sit below RISE and below supervised SINet-v2,
and asks for protocol-matched baselines. WS4 answers one part of that: **where does a model
trained by this repository's code, on the same 4040 real images with their real masks, land
on this repository's scorer?** It gives the ceiling the synthetic-source protocol sits under.

**It is a descriptive anchor. It has no decision rule, tests no arm against any other, and
nothing in the paper's argument depends on its value.** It is reported whatever it shows.

## §WS4.1 The rule — verbatim

```
Arm              : SUP = MyTrain.py --method source_only, single round (MyTrain forces
                   --iteration 1 for any non-'ours' method), native epochs (SINet 40,
                   SINet-v2 100), source_root = Dataset/Source/WS4/REAL4040/{Image,GT}.
                   source_only iterates the labelled source loader only and never forwards
                   a target image (MyTrain.py trainer()).
Data             : the SINet-V2 README's training/validation bundle (Google Drive id
                   1M8-Ivd33KslvyehLK9_IUBGJ_Kf52bWG): COD10K-train camouflaged 3040 +
                   CAMO-train 1000, images + masks.
GATE             : downloaded images byte-identical (sha256) to Dataset/Target/Image,
                   4040/4040, name for name, or WS4 STOPS. Masks: 4040, stems equal to the
                   images', binary up to edge anti-aliasing.
Architectures    : SINet, SINet-v2.
Seeds            : {42, 43, 45}. 6 runs.
Checkpoint       : Tea_epoch_best.pth, selected on CAMO-250 val MAE, as every arm here is.
Endpoints        : COD10K-test S_alpha (headline), NC4K S_alpha; MAE, F-beta-w, mean E-phi
                   reported. Scored by abc_evaluate.score() after the B1 scorer gate.
Decision rule    : NONE.
Report           : per-run values, and per architecture x endpoint mean and sd (n = 3),
                   beside the S2R-COD protocol's own numbers and the published supervised
                   numbers, each labelled with its backbone and label usage. If SUP lands
                   below the published supervised SINet (0.771) or SINet-v2 (0.815), the
                   gap is reported and NOT tuned away: those numbers come from different
                   code, schedules and checkpoint selection.
Discards         : a run that fails verification is re-run under the same seed and logged
                   as a discard. All six runs are reported or none.
```

## §WS4.2 Disclosures fixed now

1. **Checkpoint selection uses CAMO-250**, which holds three files byte-identical to
   CHAMELEON images (`EXP REBUTTAL_CONTAM`). CHAMELEON is not an endpoint here.
2. **SUP is not a reproduction** of published SINet/SINet-v2 training. It uses this repo's
   trainer, EMA teacher and checkpoint rule, which is what makes it protocol-matched.
3. **The gate passed in preflight before this file was committed.** `EXP REBUTTAL_WS4`
   preflight was dry-run (`--no-log`) to confirm the download. The logged preflight block
   follows this commit, and **no training run precedes it**.

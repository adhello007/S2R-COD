#!/usr/bin/env python3
"""
Pre-flight checklist for reproducing Table 1 (S2C: HKU-IS -> COD10K), SINet "Ours".

Verifies every precondition MyTrain.py depends on -- environment, backbone weights,
dataset layout and integrity, output paths, config coherence, and a real
forward/backward smoke test -- before you spend hours on a training run.

Usage
-----
    uv run python preflight.py                       # defaults match the SINet S2C run
    uv run python preflight.py --network SINet-v2
    uv run python preflight.py --skip-smoke          # no GPU allocation
    uv run python preflight.py --deep                # + full image decode (slow)

Exit code 0 = clear to train. 1 = at least one FAIL. WARNs never block.
See REPRODUCE_TABLE1.md for the reasoning behind each check.
"""

import argparse
import importlib
import os
import shutil
import sys
import warnings

# The deprecations these raise (F.upsample, reduce=) are themselves checked and
# reported in section I -- silence the raw tracebacks so the report stays readable.
warnings.filterwarnings("ignore", category=UserWarning)

REPO = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- reporting ---

_C = sys.stdout.isatty()
GREEN, YELLOW, RED, GREY, BOLD, OFF = (
    ("\033[32m", "\033[33m", "\033[31m", "\033[90m", "\033[1m", "\033[0m")
    if _C
    else ("", "", "", "", "", "")
)

TALLY = {"PASS": 0, "WARN": 0, "FAIL": 0}
FAILURES = []
WARNINGS = []


def section(title):
    print(f"\n{BOLD}{title}{OFF}\n{'-' * len(title)}")


def report(status, label, detail="", fix=""):
    """status in {PASS, WARN, FAIL, INFO}"""
    TALLY[status] = TALLY.get(status, 0) + 1
    mark, col = {
        "PASS": ("PASS", GREEN),
        "WARN": ("WARN", YELLOW),
        "FAIL": ("FAIL", RED),
        "INFO": ("info", GREY),
    }[status]
    line = f"  [{col}{mark}{OFF}] {label}"
    if detail:
        line += f"{GREY} — {detail}{OFF}"
    print(line)
    if fix:
        print(f"         {GREY}fix: {fix}{OFF}")
    if status == "FAIL":
        FAILURES.append((label, detail, fix))
    elif status == "WARN":
        WARNINGS.append((label, detail, fix))


def guard(label):
    """Decorator: turn an unexpected exception inside a check into a FAIL."""

    def deco(fn):
        def wrapped(*a, **kw):
            try:
                return fn(*a, **kw)
            except Exception as e:  # noqa: BLE001
                report("FAIL", label, f"check itself raised: {type(e).__name__}: {e}")

        return wrapped

    return deco


# ------------------------------------------------------------------ helpers ---


def listdir_ext(path, exts):
    """Mirror the dataloaders' filtering: extension-suffix match, no recursion."""
    return sorted(f for f in os.listdir(path) if f.endswith(exts))


def stem(name):
    return os.path.splitext(name)[0]


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ================================================================= A. repo ===


def check_repo():
    section("A. Repo layout")
    if os.getcwd() != REPO:
        report(
            "WARN",
            "working directory",
            f"cwd={os.getcwd()}",
            f"MyTrain.py resolves relative paths from cwd — run from {REPO}",
        )
    else:
        report("PASS", "working directory", REPO)

    for f in ("MyTrain.py", "MyTest.py", "CLS.py", "Src/utils/tool.py",
              "Src/utils/Dataloader.py", "Eval/MyEval.py", "Eval/metrics.py"):
        p = os.path.join(REPO, f)
        report("PASS" if os.path.isfile(p) else "FAIL", f"{f} present")


# ============================================================ B. python env ===

# scipy is train-critical, not eval-only: Src/model/SINet/SearchAttention.py imports
# scipy.stats, so SINet cannot even be constructed without it.
TRAIN_PKGS = ["torch", "torchvision", "cv2", "PIL", "numpy", "scipy"]
EVAL_PKGS = ["sklearn", "prettytable", "tqdm"]  # Eval/{MyEval,metrics}.py


def check_packages():
    section("B. Python packages")
    report("INFO", "interpreter", sys.executable)
    missing_eval = []
    for name, pkgs, critical in (("train", TRAIN_PKGS, True), ("eval", EVAL_PKGS, False)):
        for m in pkgs:
            try:
                mod = importlib.import_module(m)
                report("PASS", f"{m}", f"{getattr(mod, '__version__', '?')} ({name})")
            except Exception as e:  # noqa: BLE001
                if critical:
                    report("FAIL", f"{m}", str(e),
                           "uv add <pkg> && uv sync")
                else:
                    missing_eval.append(m)
                    report("WARN", f"{m}", f"{e} — needed only at eval time")
    if missing_eval:
        pip_names = {"sklearn": "scikit-learn", "cv2": "opencv-python"}
        pkgs = " ".join(pip_names.get(m, m) for m in missing_eval)
        report("INFO", "eval deps install", f"uv add {pkgs} && uv sync")


# ============================================================ C. torch/cuda ===


@guard("CUDA / GPU")
def check_cuda(opt):
    section("C. PyTorch / CUDA / GPU")
    try:
        import torch
    except Exception:
        report("FAIL", "torch import", "cannot continue GPU checks")
        return None

    report("INFO", "torch build", f"{torch.__version__}")
    if not torch.cuda.is_available():
        report("FAIL", "torch.cuda.is_available()", "False",
               "MyTrain.py calls .cuda() unconditionally — training cannot run")
        return None

    n = torch.cuda.device_count()
    report("PASS", "CUDA available", f"{n} device(s)")

    if opt.gpu >= n:
        report("FAIL", f"--gpu {opt.gpu} valid", f"only {n} device(s) visible",
               f"use --gpu 0..{n - 1}")
        return None

    props = torch.cuda.get_device_properties(opt.gpu)
    cap = f"sm_{props.major}{props.minor}"
    report("PASS", f"target device cuda:{opt.gpu}",
           f"{props.name}, {human(props.total_memory)}, {cap}")

    # Blackwell (sm_120) needs a cu12.8+ wheel; a mismatched wheel only fails at
    # the first kernel launch, which the smoke test in section J will catch.
    if props.major >= 12:
        arches = torch.cuda.get_arch_list()
        ok = any(a.endswith(f"_{props.major}{props.minor}") for a in arches)
        report("PASS" if ok else "WARN", "wheel supports this arch",
               f"{cap} in {arches}" if ok else f"{cap} not in {arches}",
               "" if ok else "install torch from the cu128 index (see pyproject.toml)")

    # deterministic=False is upstream behaviour; flag it so run-to-run drift is expected
    report("INFO", "cudnn.deterministic", f"{torch.backends.cudnn.deterministic} "
           "(seed is 42 but runs are not bit-reproducible)")
    return torch


# ======================================================== D. backbone weights ===

BACKBONES = {
    "SINet": ("Src/model/SINet/resnet50-11ad3fa6.pth", 102540417,
              "https://download.pytorch.org/models/resnet50-11ad3fa6.pth"),
    "SINet-v2": ("Src/model/SINetV2/res2net50_v1b_26w_4s-3cf99910.pth", None,
                 "https://shanghuagao.oss-cn-beijing.aliyuncs.com/res2net/"
                 "res2net50_v1b_26w_4s-3cf99910.pth"),
}


@guard("backbone weights")
def check_backbone(opt, torch):
    section("D. Backbone weights")
    rel, expect_size, url = BACKBONES[opt.network]
    path = os.path.join(REPO, rel)

    if not os.path.isfile(path):
        report("FAIL", f"{rel} present", "missing",
               f"curl -L -o {rel} {url}")
        return
    size = os.path.getsize(path)
    if expect_size and size != expect_size:
        report("WARN", f"{rel} size", f"{human(size)} (expected {human(expect_size)})",
               "re-download if the load below fails")
    else:
        report("PASS", f"{rel} present", human(size))

    if torch is None:
        return

    # torch>=2.6 flipped torch.load's weights_only default; prove the file still loads.
    try:
        sd = torch.load(path, map_location="cpu")
        report("PASS", "checkpoint loads", f"{len(sd)} tensors")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "checkpoint loads", f"{type(e).__name__}: {e}",
               "if this is a weights_only error, the file is not a plain state_dict")
        return

    # Replay SINet's own key-remapping so a silent assert at model init is caught here.
    if opt.network == "SINet":
        try:
            sys.path.insert(0, REPO)
            from Src.model.SINet.ResNet import ResNet_2Branch

            target = ResNet_2Branch().state_dict()
            mapped = 0
            for k in target:
                if k in sd:
                    mapped += 1
                elif "_1" in k and (k.split("_1")[0] + k.split("_1")[1]) in sd:
                    mapped += 1
                elif "_2" in k and (k.split("_2")[0] + k.split("_2")[1]) in sd:
                    mapped += 1
            if mapped == len(target):
                report("PASS", "ResNet_2Branch key remap", f"{mapped}/{len(target)} keys")
            else:
                report("FAIL", "ResNet_2Branch key remap",
                       f"only {mapped}/{len(target)} keys map",
                       "SINet.py:228 asserts full coverage — wrong checkpoint")
        except Exception as e:  # noqa: BLE001
            report("WARN", "ResNet_2Branch key remap", f"could not verify: {e}")


# ================================================================ E/F. data ===

# role -> (path, extensions the loader accepts, expected count or None)
EXPECTED = {
    "source images": ("Image", (".jpg", ".png"), 4447),
    "source GT": ("GT", (".tif", ".png"), 4447),
}


@guard("dataset presence")
def check_data_presence(opt):
    section("E. Dataset presence and counts")
    specs = [
        ("source images", os.path.join(opt.source_root, "Image"), (".jpg", ".png"), 4447),
        ("source GT", os.path.join(opt.source_root, "GT"), (".tif", ".png"), 4447),
        ("target images", os.path.join(opt.target_root, "Image"), (".jpg", ".png"), 4040),
        ("test images", "./Dataset/Test/Image", (".jpg", ".png"), 2026),
        ("test GT", "./Dataset/Test/GT", (".jpg", ".png"), 2026),
        ("val images", os.path.join(opt.val_root, "Imgs"), (".jpg", ".png"), 250),
        ("val GT", os.path.join(opt.val_root, "GT"), (".jpg", ".png"), 250),
    ]
    counts = {}
    for label, path, exts, expect in specs:
        if not os.path.isdir(path):
            report("FAIL", f"{label}", f"{path} is not a directory",
                   "extract the .rar into Dataset/ (the archives nest their own folder)")
            counts[label] = None
            continue
        files = listdir_ext(path, exts)
        counts[label] = files
        total = len(os.listdir(path))
        extra = total - len(files)
        detail = f"{len(files)} files in {path}"
        if extra:
            detail += f" (+{extra} ignored non-image entries)"
        if expect is not None and len(files) != expect:
            report("WARN", label, detail + f"; expected {expect}",
                   "count differs from the reference layout — verify your extraction")
        elif len(files) == 0:
            report("FAIL", label, detail)
        else:
            report("PASS", label, detail)

    # MyTest.py hard-codes ./Dataset/Test/{Image,GT}/ regardless of CLI args.
    report("INFO", "test root", "MyTest.py hard-codes ./Dataset/Test/{Image,GT}/")
    return counts


@guard("dataset integrity")
def check_data_integrity(opt, counts, deep):
    section("F. Dataset integrity (pairing + geometry)")

    def pairing(label, imgs, gts, note=""):
        """SrcDataset/test_dataset pair by sorted-order index, not by basename."""
        if imgs is None or gts is None:
            report("FAIL", f"{label} pairing", "directory missing above")
            return
        if len(imgs) != len(gts):
            report("FAIL", f"{label} pairing",
                   f"{len(imgs)} images vs {len(gts)} GT",
                   "SrcDataset.filter_files asserts equal length")
            return
        bad = [(i, a, b) for i, (a, b) in enumerate(zip(imgs, gts)) if stem(a) != stem(b)]
        if bad:
            ex = ", ".join(f"[{i}] {a} <> {b}" for i, a, b in bad[:3])
            report("FAIL", f"{label} pairing",
                   f"{len(bad)} index-aligned pairs have different stems: {ex}",
                   "loaders zip sorted lists — misalignment silently corrupts supervision")
        else:
            report("PASS", f"{label} pairing", f"{len(imgs)} pairs aligned by stem{note}")

    pairing("source", counts.get("source images"), counts.get("source GT"))
    pairing("test", counts.get("test images"), counts.get("test GT"))
    pairing("val", counts.get("val images"), counts.get("val GT"))

    # MyEval.py indexes predictions by the GT filename, so every GT stem must be
    # producible by MyTest.py (which rewrites .jpg -> .png when naming its output).
    ti, tg = counts.get("test images"), counts.get("test GT")
    if ti and tg:
        pred_names = {stem(f) + ".png" for f in ti}
        orphan = [g for g in tg if g not in pred_names]
        if orphan:
            report("FAIL", "eval name mapping",
                   f"{len(orphan)} GT files have no matching prediction name "
                   f"(e.g. {orphan[:3]})",
                   "MyEval.py looks up pred/<gt_filename> — names must match exactly")
        else:
            report("PASS", "eval name mapping", f"{len(tg)} GT names reachable from images")

    # filter_files() silently drops pairs whose image and GT differ in size.
    src_i, src_g = counts.get("source images"), counts.get("source GT")
    if src_i and src_g and len(src_i) == len(src_g):
        try:
            from PIL import Image

            dropped, broken = [], []
            ir = os.path.join(opt.source_root, "Image")
            gr = os.path.join(opt.source_root, "GT")
            for a, b in zip(src_i, src_g):
                try:
                    with Image.open(os.path.join(ir, a)) as im, \
                         Image.open(os.path.join(gr, b)) as gm:
                        if im.size != gm.size:
                            dropped.append((a, b, im.size, gm.size))
                        if deep:
                            im.load()
                            gm.load()
                except Exception as e:  # noqa: BLE001
                    broken.append((a, repr(e)))
            kept = len(src_i) - len(dropped)
            if broken:
                report("FAIL", "source images readable",
                       f"{len(broken)} unreadable, e.g. {broken[0]}")
            elif deep:
                report("PASS", "source images fully decode", f"{len(src_i)} files")
            if dropped:
                report("WARN", "source size match",
                       f"{len(dropped)} pairs dropped by filter_files "
                       f"(e.g. {dropped[0][0]} {dropped[0][2]} vs {dropped[0][3]}); "
                       f"{kept} usable",
                       "expected 0 for the reference HKU-IS release")
            else:
                report("PASS", "source size match", f"all {kept} pairs same-size")
        except Exception as e:  # noqa: BLE001
            report("WARN", "source size match", f"could not verify: {e}")

    # steps/epoch = min(len(src_loader), len(tar_loader)) -- zip() truncates.
    tgt = counts.get("target images")
    if src_i and tgt:
        import math

        s = math.ceil(len(src_i) / opt.batchsize)
        t = math.ceil(len(tgt) / opt.batchsize)
        report("INFO", "steps per epoch",
               f"min(src {s}, tar {t}) = {min(s, t)}  "
               f"→ log should read 'Global Step: XXXX/{min(s, t):04d}'")


# ========================================================= G. output paths ===


@guard("output paths")
def check_outputs(opt):
    section("G. Output paths and stale artifacts")

    # Raw string concatenation everywhere: save_path + 'Tea_%d.pth'
    for flag, val in (("--save_model", opt.save_model),
                      ("--source_root", opt.source_root),
                      ("--target_root", opt.target_root),
                      ("--val_root", opt.val_root)):
        if val.endswith("/"):
            report("PASS", f"{flag} trailing slash", val)
        else:
            report("FAIL", f"{flag} trailing slash", f"{val!r}",
                   f"code concatenates raw strings — use {val}/")

    # Snapshot dir: round 2 overwrites round 1's Tea_epoch_best.pth in place.
    sm = opt.save_model
    if os.path.isdir(sm):
        existing = [f for f in os.listdir(sm) if f.endswith(".pth")]
        if existing:
            report("WARN", "snapshot dir clean",
                   f"{len(existing)} .pth already in {sm} (e.g. {sorted(existing)[:3]})",
                   "start from an empty dir — rounds overwrite Tea_epoch_best.pth")
        else:
            report("PASS", "snapshot dir clean", f"{sm} exists, no checkpoints")
    else:
        report("PASS", "snapshot dir clean", f"{sm} will be created")

    # CLS writes <source_root>_iteration2/ ; a partial one from a crashed run confuses.
    it2 = opt.source_root.rstrip("/\\") + "_iteration2/"
    if os.path.exists(it2):
        n = len(os.listdir(os.path.join(it2, "GT"))) if os.path.isdir(
            os.path.join(it2, "GT")) else 0
        report("WARN", "no stale CLS output", f"{it2} exists ({n} GT files)",
               f"CLS rmtree's it at the start of the cycle: rm -rf {it2}")
    else:
        report("PASS", "no stale CLS output", f"{it2} absent")

    # Writability of every directory the run creates files in.
    for label, path in (("snapshot parent", os.path.dirname(sm.rstrip("/")) or "."),
                        ("source parent (CLS copy)",
                         os.path.dirname(opt.source_root.rstrip("/")) or "."),
                        ("repo root (Result/, logs)", REPO)):
        probe = path if os.path.isdir(path) else REPO
        if os.access(probe, os.W_OK):
            report("PASS", f"{label} writable", probe)
        else:
            report("FAIL", f"{label} writable", f"{probe} not writable")

    # Disk: ~220MB per checkpoint, up to ~15 saved per round, + a source-tree copy.
    free = shutil.disk_usage(REPO).free
    src_sz = 0
    if os.path.isdir(opt.source_root):
        for root, _, files in os.walk(opt.source_root):
            src_sz += sum(os.path.getsize(os.path.join(root, f)) for f in files)
    need = 15 * 220 * 1024**2 * 2 + src_sz * 2
    if free > need:
        report("PASS", "free disk", f"{human(free)} free, ~{human(need)} needed")
    else:
        report("FAIL", "free disk", f"{human(free)} free, ~{human(need)} needed")

    check_cls_collision(opt, it2)


@guard("CLS output collision")
def check_cls_collision(opt, it2):
    """CLS derives its output path from --source_root ALONE (CLS.py:15-16) -- the
    network name is not part of it. Two networks sharing a --source_root therefore
    fight over one directory, and CLS starts by rmtree'ing it (CLS.py:18-20)."""
    report("INFO", "CLS output path", f"{it2}  (derived from --source_root only, "
           "NOT from --network)")

    # A concurrent run on the same source_root is a destructive race: the other
    # process's rmtree deletes this run's round-2 dataset mid-epoch.
    others = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                argv = fh.read().decode("utf-8", "replace").split("\0")
        except OSError:
            continue
        if not any("MyTrain.py" in a for a in argv):
            continue
        root = "./Dataset/Source/CNC/"  # MyTrain.py default
        for i, a in enumerate(argv):
            if a == "--source_root" and i + 1 < len(argv):
                root = argv[i + 1]
            elif a.startswith("--source_root="):
                root = a.split("=", 1)[1]
        if any(a == "S2C" for a in argv):
            root = "./Dataset/Source/HKU-IS/"  # --task S2C overrides after parsing
        if os.path.normpath(root) == os.path.normpath(opt.source_root):
            others.append((pid, root))

    if others:
        report("FAIL", "no concurrent run on this source_root",
               f"MyTrain.py already running as pid(s) "
               f"{', '.join(p for p, _ in others)} with the same --source_root",
               f"both will rmtree {it2}; give each network its own --source_root "
               "(see the fix below) or run them strictly sequentially")
    else:
        report("PASS", "no concurrent run on this source_root", "no other MyTrain.py")

    # Even sequentially, the second network destroys the first network's pseudo-label
    # set. Detect that a different network has already trained against this root.
    siblings = []
    snap_parent = os.path.dirname(os.path.dirname(opt.save_model.rstrip("/")))
    if os.path.isdir(snap_parent):
        for d in sorted(os.listdir(snap_parent)):
            if d != os.path.basename(os.path.dirname(opt.save_model.rstrip("/"))):
                if any(f.endswith(".pth")
                       for _, _, fs in os.walk(os.path.join(snap_parent, d))
                       for f in fs):
                    siblings.append(d)
    if siblings:
        report("WARN", "no other network trained on this source_root",
               f"checkpoints exist for {siblings}; with --task S2C every network is "
               f"forced onto {opt.source_root}, so this run's CLS will rmtree their "
               f"pseudo-label set",
               f"archive it first: mv {it2.rstrip('/')} {it2.rstrip('/')}-<network>  "
               "(--source_root cannot separate them — MyTrain.py:159 overrides it)")
    else:
        report("PASS", "no other network trained on this source_root", "")


# ======================================================== H. config sanity ===


@guard("config coherence")
def check_config(opt):
    section("H. Config coherence")

    # CLS.py loads a checkpoint named literally Stu_40.pth (SINet) / Stu_100.pth (v2).
    required_epoch = {"SINet": 40, "SINet-v2": 100}[opt.network]
    ckpt = {"SINet": "Stu_40.pth", "SINet-v2": "Stu_100.pth"}[opt.network]
    if opt.iteration > 1:
        if opt.epoch == required_epoch:
            report("PASS", "epoch ↔ CLS checkpoint name",
                   f"--epoch {opt.epoch} produces {ckpt}, which CLS.py requires")
        else:
            report("FAIL", "epoch ↔ CLS checkpoint name",
                   f"--epoch {opt.epoch} will not produce {ckpt}",
                   f"use --epoch {required_epoch}; CLS.py hard-codes the filename")
    else:
        report("INFO", "epoch ↔ CLS checkpoint name",
               "--iteration 1: CLS is skipped, no coupling")

    if opt.network == "SINet-v2":
        report("INFO", "SINet-v2 self-override",
               "MyTrain.py forces epoch=100, batchsize=32, decay_epoch=50, clip_grad=True")

    # MyTrain.py applies the S2C paper hyperparameters AFTER parsing; confirm the
    # override block still holds the published values.
    want = {"alpha": "0.996", "u": "0.8", "tau": "0.4"}
    try:
        with open(os.path.join(REPO, "MyTrain.py")) as fh:
            src = fh.read()
        blk = src.split("if opt.task == 'S2C':", 1)
        if len(blk) != 2:
            report("WARN", "S2C hyperparameter override", "override block not found")
        else:
            body = blk[1][:600]
            bad = [f"{k}={v}" for k, v in want.items()
                   if f"opt.{k} = {v}" not in body]
            if bad:
                report("FAIL", "S2C hyperparameter override",
                       f"expected {bad} in the --task S2C block",
                       "paper values are λ=0.996, μ=0.8, τ=0.4 — MyTrain.py was edited")
            else:
                report("PASS", "S2C hyperparameter override",
                       "λ=0.996, μ=0.8, τ=0.4 set by --task S2C")
            report("INFO", "CLI hyperparameters ignored",
                   "--alpha/--u/--tau/--a/--b/--c are overwritten by --task S2C")
    except Exception as e:  # noqa: BLE001
        report("WARN", "S2C hyperparameter override", f"could not verify: {e}")

    # Documented upstream quirks that change what "40 epochs" means.
    report("INFO", "epoch loop",
           f"range(1, {opt.epoch}) → {opt.epoch - 1} epochs actually run; "
           f"the file named Tea_{opt.epoch}.pth is written at epoch {opt.epoch - 1}")
    report("WARN", "LR schedule compounds",
           "tool.py adjust_lr does lr *= 0.1 every epoch past decay_epoch "
           "(1e-5 → 1e-14), not once",
           "upstream behaviour — leave as-is for reproduction (REPRODUCE_TABLE1.md §8.2)")
    report("INFO", "model selection",
           f"teacher MAE on {opt.val_root} (CAMO), epochs 21+ only → Tea_epoch_best.pth")


# ====================================================== I. API compat guards ===


@guard("API compatibility")
def check_api(opt, torch):
    section("I. API compatibility guards")
    if torch is None:
        return
    import torch.nn.functional as F
    import torchvision.transforms as T

    # val() and MyTest.py use the long-deprecated F.upsample.
    if hasattr(F, "upsample"):
        try:
            F.upsample(torch.zeros(1, 1, 4, 4), size=(8, 8),
                       mode="bilinear", align_corners=False)
            report("PASS", "F.upsample available",
                   "used by MyTrain.val() and MyTest.py")
        except Exception as e:  # noqa: BLE001
            report("FAIL", "F.upsample callable", f"{type(e).__name__}: {e}",
                   "replace F.upsample with F.interpolate in MyTrain.py/MyTest.py")
    else:
        report("FAIL", "F.upsample available", "removed from this torch",
               "validation would crash at epoch 21 — switch to F.interpolate")

    for attr in ("RandomAutocontrast", "GaussianBlur"):
        report("PASS" if hasattr(T, attr) else "FAIL", f"transforms.{attr}",
               "strong-augmentation branch of TarDataset")

    # ESLoss is the consistency objective; exercise it on the real code path.
    try:
        sys.path.insert(0, REPO)
        from Src.utils.tool import ESLoss

        loss = ESLoss(a=0.9, b=0.3, c=0.5)
        v = loss(torch.rand(2, 1, 16, 16), torch.rand(2, 1, 16, 16))
        ok = torch.isfinite(v)
        report("PASS" if ok else "FAIL", "ESLoss forward", f"value={v.item():.4f}")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "ESLoss forward", f"{type(e).__name__}: {e}")

    # structure_loss passes the legacy `reduce=` arg; only the SINet-v2 path uses it.
    try:
        from Src.utils.tool import structure_loss

        v = structure_loss(torch.randn(2, 1, 32, 32), torch.rand(2, 1, 32, 32))
        report("PASS", "structure_loss forward", f"value={v.item():.4f}")
    except Exception as e:  # noqa: BLE001
        sev = "FAIL" if opt.network == "SINet-v2" else "WARN"
        report(sev, "structure_loss forward", f"{type(e).__name__}: {e}",
               "tool.py:9 passes reduce='none' (legacy bool arg) — change to "
               "reduction='none'. Affects the SINet-v2 path only.")


# ========================================================== J. smoke tests ===


@guard("smoke test")
def check_smoke(opt, torch):
    section("J. Smoke tests (real data, real kernels)")
    if torch is None:
        report("WARN", "smoke tests", "skipped: no CUDA")
        return
    sys.path.insert(0, REPO)

    # --- one real batch through both dataloaders -----------------------------
    try:
        from Src.utils.Dataloader import get_srcloader, get_tarloader, test_dataset

        sl = get_srcloader(image_root=opt.source_root + "Image/",
                           gt_root=opt.source_root + "GT/",
                           batchsize=opt.batchsize, trainsize=opt.trainsize,
                           num_workers=0, pin_memory=False)
        si, sg = next(iter(sl))
        ok = (si.shape == (opt.batchsize, 3, opt.trainsize, opt.trainsize)
              and sg.shape == (opt.batchsize, 1, opt.trainsize, opt.trainsize))
        report("PASS" if ok else "FAIL", "source batch",
               f"image {tuple(si.shape)}, gt {tuple(sg.shape)}, "
               f"gt range [{sg.min():.2f}, {sg.max():.2f}]")
        if sg.max() <= 1e-6:
            report("FAIL", "source GT non-empty", "first batch of masks is all zeros")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "source batch", f"{type(e).__name__}: {e}")

    try:
        tl = get_tarloader(image_root=opt.target_root + "Image/",
                           batchsize=opt.batchsize, trainsize=opt.trainsize,
                           num_workers=0, pin_memory=False)
        weak, strong = next(iter(tl))
        differ = not torch.allclose(weak, strong)
        report("PASS" if differ else "FAIL", "target weak/strong views",
               f"{tuple(weak.shape)}, "
               f"mean|weak-strong|={(weak - strong).abs().mean():.4f}",
               "" if differ else "strong augmentation is a no-op — consistency loss is trivial")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "target batch", f"{type(e).__name__}: {e}")

    try:
        vl = test_dataset(image_root=opt.val_root + "Imgs/",
                          gt_root=opt.val_root + "GT/",
                          testsize=opt.trainsize)
        img, gt, name, _ = vl.load_data()
        report("PASS", "val loader", f"{vl.size} images, first={name}, "
               f"tensor {tuple(img.shape)}")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "val loader", f"{type(e).__name__}: {e}")

    if opt.skip_smoke:
        report("INFO", "model fwd/bwd", "skipped (--skip-smoke)")
        return

    # --- student fwd + bwd and teacher fwd at the real batch size ------------
    try:
        torch.cuda.set_device(opt.gpu)
        torch.cuda.reset_peak_memory_stats(opt.gpu)
        if opt.network == "SINet":
            from Src.model.SINet.SINet import SINet_ResNet50 as Net
            kw = {"channel": 32}
        else:
            from Src.model.SINetV2.Network_Res2Net_GRA_NCD import Network as Net
            kw = {"channel": 32}

        model, ema = Net(**kw).cuda(), Net(**kw).cuda()
        report("PASS", "model init on GPU",
               f"{opt.network}, {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M "
               "params ×2 (student + teacher)")

        x = torch.randn(opt.batchsize, 3, opt.trainsize, opt.trainsize, device="cuda")
        y = torch.rand(opt.batchsize, 1, opt.trainsize, opt.trainsize, device="cuda")
        opt_ = torch.optim.Adam(model.parameters(), 1e-4)

        outs = model(x)
        bce = torch.nn.BCEWithLogitsLoss()
        if opt.network == "SINet":
            loss = bce(outs[0], y) + bce(outs[1], y)
        else:
            from Src.utils.tool import structure_loss
            loss = sum(structure_loss(o, y) for o in outs)
        with torch.no_grad():
            _ = ema(x)
        loss.backward()
        opt_.step()
        torch.cuda.synchronize()

        peak = torch.cuda.max_memory_allocated(opt.gpu)
        total = torch.cuda.get_device_properties(opt.gpu).total_memory
        report("PASS", "fwd + bwd + step",
               f"loss={loss.item():.4f}, peak GPU mem {human(peak)} "
               f"({100 * peak / total:.1f}% of {human(total)})")

        from Src.utils.tool import update_ema

        before = next(ema.parameters()).clone()
        update_ema(model, ema, 0.996)
        moved = not torch.allclose(before, next(ema.parameters()))
        report("PASS" if moved else "WARN", "EMA update",
               "teacher parameters move" if moved else "teacher unchanged")

        del model, ema, x, y, outs, opt_
        torch.cuda.empty_cache()
    except ModuleNotFoundError as e:
        report("FAIL", "model fwd/bwd", f"missing dependency: {e.name}",
               f"uv add {e.name} && uv sync  (imported on the model's own code path)")
    except Exception as e:  # noqa: BLE001
        report("FAIL", "model fwd/bwd", f"{type(e).__name__}: {e}",
               "if this is a kernel/arch error, the CUDA wheel does not match this GPU")


# ==================================================================== main ===


def main():
    p = argparse.ArgumentParser(
        description="Pre-flight checklist for the S2R-COD Table 1 (S2C) reproduction.")
    p.add_argument("--network", default="SINet", choices=["SINet", "SINet-v2"])
    p.add_argument("--task", default="S2C", choices=["C2C", "S2C"])
    p.add_argument("--gpu", type=int, default=0)
    p.add_argument("--epoch", type=int, default=40)
    p.add_argument("--batchsize", type=int, default=16)
    p.add_argument("--trainsize", type=int, default=352)
    p.add_argument("--iteration", type=int, default=2)
    p.add_argument("--save_model", default="./Snapshot/SINet/S2C/")
    p.add_argument("--source_root", default="./Dataset/Source/HKU-IS/")
    p.add_argument("--target_root", default="./Dataset/Target/")
    p.add_argument("--val_root", default="./Dataset/Val/CAMO/")
    p.add_argument("--skip-smoke", dest="skip_smoke", action="store_true",
                   help="skip the GPU forward/backward test (no VRAM allocated)")
    p.add_argument("--deep", action="store_true",
                   help="fully decode every source image (slow, catches truncation)")
    opt = p.parse_args()

    if opt.network == "SINet-v2":  # mirror MyTrain.py:174-180
        opt.epoch, opt.batchsize = 100, 32

    # MyTrain.py:159 hard-resets source_root inside the --task S2C block, AFTER
    # argparse. Mirror it so every path this script reports is the one actually used.
    s2c_forced = "./Dataset/Source/HKU-IS/"
    overridden = opt.task == "S2C" and os.path.normpath(opt.source_root) != os.path.normpath(s2c_forced)
    if opt.task == "S2C":
        opt.source_root = s2c_forced

    print(f"{BOLD}S2R-COD pre-flight — {opt.network} / {opt.task} / cuda:{opt.gpu}{OFF}")
    print(f"{GREY}repo: {REPO}{OFF}")

    check_repo()
    if overridden:
        section("A0. Argument override")
        report("WARN", "--source_root is a no-op with --task S2C",
               f"MyTrain.py:159 forces source_root = {s2c_forced}; "
               "everything below reports that path",
               "to use a different source root you must edit MyTrain.py:159")
    check_packages()
    torch = check_cuda(opt)
    check_backbone(opt, torch)
    counts = check_data_presence(opt) or {}
    check_data_integrity(opt, counts, opt.deep)
    check_outputs(opt)
    check_config(opt)
    check_api(opt, torch)
    check_smoke(opt, torch)

    section("Summary")
    print(f"  {GREEN}{TALLY['PASS']} pass{OFF}   "
          f"{YELLOW}{TALLY['WARN']} warn{OFF}   "
          f"{RED}{TALLY['FAIL']} fail{OFF}")

    if WARNINGS:
        print(f"\n  {YELLOW}Warnings (non-blocking):{OFF}")
        for label, detail, _ in WARNINGS:
            print(f"    - {label}: {detail}")

    if FAILURES:
        print(f"\n  {RED}Blocking failures:{OFF}")
        for label, detail, fix in FAILURES:
            print(f"    - {label}: {detail}")
            if fix:
                print(f"      → {fix}")
        print(f"\n{RED}NOT ready to train.{OFF}")
        return 1

    cmd = (f"uv run python MyTrain.py --network {opt.network} --task {opt.task} "
           f"--gpu {opt.gpu} --iteration {opt.iteration} "
           f"--save_model {opt.save_model} --source_root {opt.source_root} "
           f"--target_root {opt.target_root} --val_root {opt.val_root} "
           f"2>&1 | tee train_{opt.network.lower()}_{opt.task.lower()}.log")
    print(f"\n{GREEN}Clear to train.{OFF}\n\n  {cmd}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

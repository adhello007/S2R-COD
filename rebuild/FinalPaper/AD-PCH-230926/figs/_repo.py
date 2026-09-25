"""Locate the supplement root and the paper output folders, wherever these scripts sit."""
import os


def _find_repo():
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(d, "rebuild")) and os.path.isdir(os.path.join(d, "results")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("Run this script from inside the supplement: no rebuild/ and results/ "
                             "directories were found above %s" % os.path.dirname(os.path.abspath(__file__)))
        d = parent


REPO = _find_repo()
PAPER = os.path.join(REPO, "Paper")
FIGS = os.path.join(PAPER, "figs")


def paper_out(name):
    os.makedirs(PAPER, exist_ok=True)
    return os.path.join(PAPER, name)


def fig_out(name):
    os.makedirs(FIGS, exist_ok=True)
    return os.path.join(FIGS, name)


def write_text(path, text):
    # LF endings on every OS, so generated tables compare byte-for-byte with the references.
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

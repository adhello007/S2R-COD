#!/usr/bin/env bash
# Build the ICLR anonymous supplement from the tracked tree.
#
# Idempotent: wipes and rebuilds iclr2027_supplement/ every run, so it can be
# re-run after any regeneration and re-gated. Never touches the working tree --
# all scrubbing happens on the copy.
#
#   bash tools/build_supplement.sh          # build + scrub
#   bash tools/build_supplement.sh --zip    # also produce the upload artifact
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
SUP="iclr2027_supplement"
ZIPNAME="s2r-cod-supplement.zip"

# ---------------------------------------------------------------- selection --
# Excluded, with reasons:
#   old_paperinfo_redundant/   superseded drafts + LaTeX build artifacts
#   Paper/                     the paper is uploaded separately as a PDF
#   rebuild/FinalPaper/Paper/  committed duplicate of Paper/, incl. .fls/.log
#                              build artifacts holding ~600 absolute paths
#   *.pdf *.zip *.rar          paper archives and third-party PDFs (one embeds
#                              the upstream authors' names in its metadata)
#   rebuild/reference/old_scripts/  dead code with hardcoded absolute paths
#   skills-lock.json, manuscript_revision.md  internal agent tooling
#   src/                       dead 2-line stub referenced by pyproject scripts
echo "==> selecting files"
rm -rf "$SUP"; mkdir -p "$SUP"
git ls-files \
  | grep -vE '^old_paperinfo_redundant/' \
  | grep -vE '^Paper/' \
  | grep -vE '^rebuild/FinalPaper/Paper/' \
  | grep -vE '^rebuild/reference/old_scripts/' \
  | grep -vE '^src/' \
  | grep -vE '^(Paper\.rar|skills-lock\.json|manuscript_revision\.md|ICLR2027_SUPPLEMENT_PLAN\.md|SUPPLEMENT_README\.md)$' \
  | grep -vE '\.(pdf|zip|rar)$' \
  > /tmp/_sup_list.txt
echo "    $(wc -l < /tmp/_sup_list.txt) files"

echo "==> copying"
while IFS= read -r f; do [ -f "$f" ] && install -D "$f" "$SUP/$f"; done < /tmp/_sup_list.txt
# tools/ is deliberately NOT shipped. anon_scan.py and this script necessarily
# contain the author-identifying tokens they search for, so shipping them would
# defeat the gate they implement. The README states that the package was built
# and gated by them without reproducing their contents.
#
# the reviewer-facing README replaces the upstream project's readme, which
# describes a different paper by different authors
install -m 644 SUPPLEMENT_README.md "$SUP/README.md"
cp .python-version "$SUP/.python-version" 2>/dev/null || true

# Minimal DINOv2 embedding cache. rebuild/*/cache/ is gitignored and totals
# 1.2 GB, but the area control (rebuild/AC) needs only these, and shipping them
# is what makes AC runnable with none of the image data -- the one non-trivial
# measured result a reviewer can reproduce end to end on a laptop.
echo "==> embedding cache subset for the area control"
for f in dinoL518_tgt_cls.npy dinoL518_test_cls.npy dinoL518_names.json dinoL518_embedder.json; do
  [ -f "rebuild/E0/cache/$f" ] && install -D "rebuild/E0/cache/$f" "$SUP/rebuild/E0/cache/$f"
done

# ------------------------------------------------------------------ scrubbing --
# The working tree's copies stay byte-identical to what the commits reference;
# only the shipped copy is rewritten.
echo "==> scrubbing absolute paths"
ABS="/home/ai-server/Public/lab/Diffusion_Inpaint/S2R-COD"
find "$SUP" -type f \
  \( -name '*.md' -o -name '*.txt' -o -name '*.json' -o -name '*.log' \
     -o -name '*.py' -o -name '*.sh' -o -name '*.csv' -o -name '*.toml' \) \
  -print0 | xargs -0 sed -i \
    -e "s|${ABS}|<REPO>|g" \
    -e "s|/home/ai-server|<HOME>|g" \
    -e "s|/home/[a-z0-9_-]\+|<HOME>|g"

# Author-identifying tokens survive inside two evidence files: the ANON_PATTERNS
# literal in the re-audit script, and the THRESHOLD lines in the log that echo
# it. They are there because a scan happened, not because anything was leaked --
# but printing a name is a leak regardless of the sentence around it. Redact the
# tokens, keep the fact of the scan.
echo "==> redacting author tokens inside evidence files"
find "$SUP" -type f \( -name '*.py' -o -name '*.txt' -o -name '*.md' \) -print0 \
  | xargs -0 sed -i \
      -e "s/'Akshat', 'akshat'/'<author-given-name>', '<author-given-name-lc>'/g" \
      -e "s/Akshat, akshat/<author-given-name>, <author-given-name-lc>/g" \
      -e "s/'imagine\.io'/'<author-email-domain>'/g" \
      -e "s/imagine\.io/<author-email-domain>/g" \
      -e "s/\bAkshat\b/<author-given-name>/g" \
      -e "s/\bakshat\b/<author-given-name-lc>/g" \
      -e "s/\bDobhal\b/<author-family-name>/g" \
      -e "s/adhello007/<author-account>/g" \
      -e "s/'ai-server'/'<hostname>'/g" \
      -e "s/, ai-server,/, <hostname>,/g"

# Shell drivers: make the cd relocatable rather than just anonymous, so the
# scripts still run from an extracted copy.
echo "==> relocating shell drivers"
for s in "$SUP"/rebuild/SE/chain_se.sh "$SUP"/rebuild/SE/se_resume.sh "$SUP"/rebuild/FX/chain_fx.sh; do
  [ -f "$s" ] || continue
  sed -i 's|^cd <REPO>$|cd "$(cd "$(dirname "$0")/../.." \&\& pwd)"|' "$s"
done

# The append-only log must not be silently rewritten. Record the substitution.
LOG="$SUP/results/REBUILD_LOG.txt"
if [ -f "$LOG" ]; then
  echo "==> annotating REBUILD_LOG.txt"
  cat >> "$LOG" <<'NOTE'

================================================================================
ANONYMISATION NOTE -- applies to the ICLR supplement copy of this file only.

The copy of this log distributed as anonymous supplementary material has had one
mechanical substitution applied, and nothing else:

    the absolute filesystem path of the repository  ->  <REPO>
    any remaining home-directory prefix             ->  <HOME>
    author-identifying tokens inside the THRESHOLD  ->  <author-...> placeholders
      lines below that echo the scan's pattern list

No timestamp, commit sha, metric, threshold, verdict or artifact name was
altered, added or removed. The substitution is performed by
tools/build_supplement.sh and is verifiable by re-running it. The in-repository
log remains byte-identical to the file the commits reference; this note exists
because the log is append-only and a silent rewrite of it would be a defect
under its own rules.
================================================================================
NOTE
fi

# --------------------------------------------------------------------- gate --
echo "==> anonymity gate"
python3 tools/anon_scan.py "$SUP" | tail -25

if [ "${1:-}" = "--zip" ]; then
  echo "==> zipping"
  rm -f "$ZIPNAME"
  ( cd "$SUP" && zip -q -r -9 "../$ZIPNAME" . -x '.DS_Store' )
  ls -lh "$ZIPNAME"
fi

echo "==> $(find "$SUP" -type f | wc -l) files, $(du -sh "$SUP" | cut -f1)"

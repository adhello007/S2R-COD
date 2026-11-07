#!/usr/bin/env bash
# REBUTTAL P2 + WS1.6: re-emit the committed boundary diagnostics, then the 8-seed re-score.
# CPU only. Each job writes suffixed files under rebuild/DIAG/out/ and never the committed ones.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=.venv/bin/python
$PY rebuild/DIAG/diag_boundary.py --workers 40 --seeds 42,43,45 --arms A0,A2,B,C10,CSHUF,CINV --suffix _reemit
$PY rebuild/DIAG/diag_subgroups.py --suffix _reemit
$PY rebuild/DIAG/diag_boundary.py --workers 40 --seeds 42,43,45 --arch SINet --arms B,C10,CSHUF,CINV --thresh 0.4 --suffix _reemit_t0.40
$PY rebuild/DIAG/diag_boundary.py --workers 40 --seeds 42,43,45 --arch SINet --arms B,C10,CSHUF,CINV --thresh 0.6 --suffix _reemit_t0.60
$PY rebuild/DIAG/diag_boundary.py --workers 40 --arms B,C10,CSHUF,CINV --suffix _se8
echo RESCORE_DONE

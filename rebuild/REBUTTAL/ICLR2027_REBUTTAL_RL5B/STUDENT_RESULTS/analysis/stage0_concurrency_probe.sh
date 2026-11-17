#!/usr/bin/env bash
# Stage-0 concurrency probe: does running K training processes per GPU raise total throughput?
#
# Usage (from the repo root):  bash <this> <probe_out_dir> [seconds_per_config]
#
# For each config (arch, K) it starts K MyTrain.py processes on EACH of the two GPUs, using a
# committed pool read-only (Dataset/Source/ABC/SINet_C10_s46 or SINetv2_C10_s46), lets them run
# for SECS seconds (240 s for SINet-v2), then kills them. That keeps every process inside
# epoch 9, i.e. before MyTrain's first checkpoint save, so no .pth is written. Snapshot dirs (training logs only)
# go under <probe_out_dir>, outside the repo. Steps/s are parsed afterwards by
# stage0_probe_parse.py from the '[timestamp] ... Global Step' lines MyTrain logs every 10 steps.
set -u
OUT=${1:?probe_out_dir}; SECS=${2:-360}
mkdir -p "$OUT"
run_cfg () {   # arch network pool K secs
  local arch=$1 net=$2 pool=$3 k=$4 secs=$5 pids=() tag="${1}_k${4}"
  for gpu in 0 1; do
    for i in $(seq 1 "$k"); do
      d="$OUT/$tag/g${gpu}_p${i}/"; mkdir -p "$d"
      .venv/bin/python MyTrain.py --network "$net" --task S2C --method ours --iteration 2 \
        --seed $((900 + gpu * 10 + i)) --save_model "$d" --source_root "./$pool/" \
        --target_root ./Dataset/Target/ --val_root ./Dataset/Val/CAMO/ --gpu "$gpu" \
        > "$d/stdout.log" 2>&1 &
      pids+=($!)
    done
  done
  echo "[$(date +%T)] $tag started pids ${pids[*]}"
  sleep "$secs"
  kill "${pids[@]}" 2>/dev/null; sleep 5; kill -9 "${pids[@]}" 2>/dev/null
  wait 2>/dev/null
  if find "$OUT/$tag" -name '*.pth' | grep -q .; then echo "WARNING: a checkpoint was written under $OUT/$tag"; fi
  echo "[$(date +%T)] $tag stopped"
}
# SINet epochs take ~80 s (first save after epoch 9 at ~12 min); SINet-v2 epochs ~37 s
# (first save at ~5.5 min), so SINet-v2 configs run for 240 s.
run_cfg SINet SINet Dataset/Source/ABC/SINet_C10_s46 1 "$SECS"
run_cfg SINet SINet Dataset/Source/ABC/SINet_C10_s46 2 "$SECS"
run_cfg SINet SINet Dataset/Source/ABC/SINet_C10_s46 3 "$SECS"
run_cfg SINetv2 SINet-v2 Dataset/Source/ABC/SINetv2_C10_s46 1 240
run_cfg SINetv2 SINet-v2 Dataset/Source/ABC/SINetv2_C10_s46 2 240
echo "[$(date +%T)] probe done"

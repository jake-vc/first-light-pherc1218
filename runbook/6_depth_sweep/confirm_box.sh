#!/bin/bash
# confirm_box.sh <box target dir>... - depth sweep (-15..+15) for a reviewed candidate box:
# the winner's four models (dense_native, ink_9um seeds 42/43, Hecate) plus reader-v2 and reader-v3 at every depth
# d = -15..+15 (reader-v3 added after the control), each model reading its 17-layer window around d. Reuses the
# box's existing render (66 layers, so d -15..+15 fits) and every depth the candidate review already ran (d -8..+8
# step 2); runs only what is missing, three models at a time (as review_run.sh). The z-score ensemble and images are
# made afterwards by confirm_images.py. Prints one line per depth: ok / failed / already there.
set -uo pipefail
W=/workspace; S=$W/p8/scripts
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp L0_ONLY=0 MKL_NUM_THREADS=3
MS=(dnative hybrid_3d2d-seed42 hybrid_3d2d-seed43 hecate readerv2 readerv3)
log() { echo "=== $(date -u +%FT%TZ) $*"; }
have() {  # <maps dir> <model> <d>: output already there (same test as rerun_failed.sh)
  local s=$(($3 + 25)) out
  if [ "$2" = hecate ]; then out=$(ls $1/render__hecate__L66zc$(awk -v d=$3 'BEGIN{printf "%.2f", 32.5 + d}').json 2>/dev/null); [ -n "$out" ] && [ -s "$out" ]
  else out=$1/render__${2}__L66s${s}.tif; [ -s "$out" ] && [ -s "${out%.tif}_reverse.tif" ]; fi
}
for D in "$@"; do
  [ -d $D/render.zarr ] || { log "$D: no render, skipped"; continue; }
  log "$D: confirmation sweep d -15..+15"
  for d in $(seq -15 15); do
    todo=(); for m in "${MS[@]}"; do have $D/maps $m $d || todo+=($m); done
    [ ${#todo[@]} = 0 ] && continue
    for ((g = 0; g < ${#todo[@]}; g += 3)); do
      for m in "${todo[@]:g:3}"; do
        ( OMP_NUM_THREADS=3 bash $S/run_ink.sh $D/render.zarr $m $d $D/maps > /dev/null 2>> $D/ink.$m.err || log "$D: $m d=$d failed" ) &
      done
      wait
    done
    log "$D: d=$d done (${todo[*]})"
  done
  touch $D/confirm.ok; log "$D: sweep complete"
done

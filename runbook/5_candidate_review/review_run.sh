#!/bin/bash
# review_run.sh <screen dir> <umbilicus.json> [max_boxes] - detail review of flagged screen areas (plan: review_plan.py).
# Per planned box: crop-render (66 layers, full resolution, same frame as the screen) the flagged turn and its
# neighbours; reader-v2 / dense_native / reader-v3 at d = -8..+8 step 2 on the target, d = 0 on the neighbours; then
# review_images.py writes native-resolution panels + a summary. CT streamed from the bucket.
set -uo pipefail
SD=$1; UMB=$2; MAXB=${3:-12}
W=/workspace; S=$W/p8/scripts; R=$SD/${REVIEW_SUBDIR:-review}  # REVIEW_SUBDIR / ONLY_TURNS: see review_plan.py
CT=${CT_URL:-https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr}
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp L0_ONLY=0 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
mkdir -p $R $TMPDIR
log() { echo "=== $(date -u +%FT%TZ) $*"; }
# One job per window (two would overwrite each other's plan.json): skip if another review job holds the lock.
exec 9> "$R/.review.lock"; flock -n 9 || { log "$SD: another review job is on this window; skipping"; exit 0; }
$PY $S/review_plan.py "$SD" "$UMB" "$MAXB" || exit 2
n=$($PY -c "import json,sys; print(len(json.load(open(sys.argv[1]))))" $R/plan.json)
for i in $(seq 0 $((n - 1))); do
  eval "$($PY - $R/plan.json $i <<'EOF'
import json, shlex, sys
j = json.load(open(sys.argv[1]))[int(sys.argv[2])]
for k in ("box_id", "role", "mesh", "direction", "x", "y", "w", "h"):
    print(f"J_{k.upper()}={shlex.quote(str(j.get(k, '')))}")
print(f"J_MISSING={1 if j.get('missing') else 0}")
EOF
)"
  [ "$J_MISSING" = 1 ] && { log "$J_BOX_ID $J_ROLE: no matching neighbour region"; continue; }
  D=$R/$J_BOX_ID/$J_ROLE; Z=$D/render.zarr; mkdir -p $D
  [ -f $D/maps.ok ] && continue
  log "$J_BOX_ID $J_ROLE: render ${J_W}x${J_H} at ($J_X,$J_Y)"
  [ -d $Z/0 ] || env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
     --group-idx 0 --scale 1 --segmentation "$J_MESH" --num-slices 66 --slice-step 1 --cache-gb 8 \
     --crop-x $J_X --crop-y $J_Y --crop-width $J_W --crop-height $J_H --zarr-output $Z > $D/render.log 2>&1
  [ -d $Z/0 ] || { log "$J_BOX_ID $J_ROLE: render FAILED"; continue; }
  if [ "$J_ROLE" = target ]; then DS=${REVIEW_TARGET_DEPTHS:-"-8 -6 -4 -2 0 2 4 6 8"}; else DS=0; fi
  # REVIEW_MODELS: models shown in the review (flagging always uses the three calibrated screen models).
  # Run three at a time: each run is mostly model-load overhead on a small crop.
  MS=(${REVIEW_MODELS:-readerv3 dnative readerv2 hybrid_3d2d-seed42 hybrid_3d2d-seed43 hecate})
  for d in $DS; do
    for ((g = 0; g < ${#MS[@]}; g += 3)); do
      for m in "${MS[@]:g:3}"; do
        ( OMP_NUM_THREADS=3 bash $S/run_ink.sh $Z $m $d $D/maps > /dev/null 2>> $D/ink.$m.err || log "$J_BOX_ID $J_ROLE: $m d=$d failed" ) &
      done
      wait
    done
  done
  touch $D/maps.ok
done
$PY $S/review_images.py $R
log "review done: $R/summary.md"

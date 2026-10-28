#!/bin/bash
# whole_turn_yellow.sh <window>/<turn>... - yellow ink view over a WHOLE screened turn, not just the review box
# (submission checklist: look at large areas). Re-renders only 5 CT layers at the surface for the turn's screen crop
# (render_crop.txt, same mesh), then whole_turn_yellow.py averages the turn's existing screen maps (reader-v2,
# dense_native, reader-v3 at d = 0, reading side) in yellow over the dimmed CT. Output <screen>/<turn>/whole_yellow.png.
# Note: these are the three SCREEN models at one depth, not the winner's four models over -8..+8 used in the box view.
set -uo pipefail
W=/workspace; S=$W/p8/scripts
CT=${CT_URL:-https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr}
log() { echo "=== $(date -u +%FT%TZ) $*"; }
for wt in "$@"; do
  D=$W/screen/$wt; [ -d $D/maps ] || { log "$wt: no screen maps, skipped"; continue; }
  read -r cw ch cx cy < <(sed -E 's/crop \[([0-9]+)×([0-9]+) from \(([0-9]+),([0-9]+)\)\]/\1 \2 \3 \4/' $D/render_crop.txt)
  if [ ! -d $D/ct5.zarr/0 ]; then
    env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
      --group-idx 0 --scale 1 --segmentation "$(cat $D/mesh_path.txt)" --num-slices 5 --slice-step 1 --cache-gb 8 \
      --crop-x $cx --crop-y $cy --crop-width $cw --crop-height $ch --zarr-output $D/ct5.zarr > $D/ct5.log 2>&1 \
      || { log "$wt: render FAILED"; continue; }
  fi
  $W/venv/bin/python $S/whole_turn_yellow.py $D && log "$wt: $D/whole_yellow.png"
done

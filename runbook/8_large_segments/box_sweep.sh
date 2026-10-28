#!/bin/bash
# box_sweep.sh <segment dir> <out box dir> <crop x> <crop y> <w> <h> - depth sweep (-15..+15) on a box of a
# large segment (seg_big.sh output): crop-render its flattened surface, 66 layers, in the segment's
# full-render frame (as review_run.sh), then the unchanged confirm_box.sh (six models, d -15..+15) and
# confirm_images.py. Run through launch.sh.
set -uo pipefail
G=$1; D=$2/target; W=/workspace; S=$W/p8/scripts
CT=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr
mkdir -p $D
if [ ! -d $D/render.zarr/0 ]; then
  env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
    --group-idx 0 --scale 1 --segmentation $G/flat/tifxyz/flatten.tifxyz --num-slices 66 --slice-step 1 --cache-gb 8 \
    --crop-x $3 --crop-y $4 --crop-width $5 --crop-height $6 --zarr-output $D/render.zarr > $D/render.log 2>&1 \
    || { echo "render FAILED"; exit 1; }
fi
bash $S/confirm_box.sh $D && $W/venv/bin/python $S/confirm_images.py $D

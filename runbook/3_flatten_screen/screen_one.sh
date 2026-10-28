#!/bin/bash
# screen_one.sh <mesh dir> <out dir> <label> - render one mesh (66 layers, same recipe as screen_1218.sh), run the three
# screen models at d = 0 (same run_depth_sweep.sh call), score it with screen_sheet.py; prints the summary line.
set -uo pipefail
M=$1; D=$2; LAB=$3; W=/workspace; S=$W/p8/scripts
CT=${CT:-https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr}
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp L0_ONLY=0 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
mkdir -p $D; Z=$D/render.zarr
[ -d "$Z/0" ] || env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
  --group-idx 0 --scale 1 --segmentation "$M" --num-slices 66 --slice-step 1 --auto-crop --cache-gb 8 --zarr-output "$Z" > "$Z.log" 2>&1
MODELS="readerv2 dnative readerv3" P_VILLA=2 P_HEC=0 bash $S/run_depth_sweep.sh "$Z" $D/maps 0 0 > $D/sweep.log 2>&1 || { echo "sweep failed"; exit 1; }
$PY $S/screen_sheet.py "$Z" $D/maps $D "$LAB"

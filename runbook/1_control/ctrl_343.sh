#!/bin/bash
# ctrl_343.sh - P8 positive control (prereg "Positive control"): render Nieuwlaar's published PHerc0343 segment and run
# the screen models (reader-v2, ink_9um seed 42) at d = -1, 0, +1, both directions. Log: /workspace/p8/out/ctrl.log
set -euo pipefail
W=/workspace; S=$W/p8/scripts; C=$W/ctrl
N=concat_w047-w048_R5B2_z9500-11000
CT=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp
mkdir -p $S $C $TMPDIR
step() { echo "=== $(date -u +%FT%TZ) $*"; }

# our copies of the winner's ink scripts, plus a reader-v2 case (drop-in ink_9um checkpoint, same villa CLI)
cp $W/pherc343/ink/scripts/{run_ink.sh,run_depth_sweep.sh,hecate_prep.py} $S/
sed -i 's|^  hecate) CK=\$CKPT_DIR/hecate_9.6um.pth ;;|  hecate) CK=$CKPT_DIR/hecate_9.6um.pth ;;\n  readerv2) CK=$CKPT_DIR/reader-v2-step040000.pth ;;|' $S/run_ink.sh
grep -q 'readerv2) CK=' $S/run_ink.sh

step render 66 layers "(VC3D 359bbed, CT streamed from the open-data bucket)"
MESH=$W/pherc343/outputs/$N.tifxyz
ls $MESH/x.tif $MESH/y.tif $MESH/z.tif >/dev/null
if [ ! -d $C/${N}_66.zarr/0 ]; then
  env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=12 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz \
    --volume "$CT" --group-idx 0 --scale 1 --segmentation "$MESH" \
    --num-slices 66 --slice-step 1 --cache-gb 16 --zarr-output $C/${N}_66.zarr
fi

step waiting for setup_pod.sh to finish
while pgrep -f setup_pod.sh >/dev/null; do sleep 20; done
grep -q "^=== .* done" $W/p8/out/setup.log || { echo "setup did not finish; see setup.log"; exit 5; }

step screen "(reader-v2, seed42; d -1..+1)"
MODELS="readerv2 hybrid_3d2d-seed42" P_VILLA=2 P_HEC=0 bash $S/run_depth_sweep.sh $C/${N}_66.zarr $C/maps -1 1

step done
ls -la $C/maps; cat $C/maps/logs/timings.tsv

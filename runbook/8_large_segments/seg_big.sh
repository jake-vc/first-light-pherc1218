#!/bin/bash
# seg_big.sh <winding>... - LARGE segments from the tall fit (submission checklist: bigger, better segments).
# For each winding of /workspace/fit1218C_main/Ctall10k/final/exportf: the winner's snap (pherc343 mesh/snap_meshes.py),
# the winner's flatten (flatten_one.sh), a full 66-layer render of the whole flattened winding (as the review renders,
# auto-cropped), the winner's four models at d = 0 (run_ink.sh), the on-sheet check of the snapped winding, and
# seg_yellow.py: the four-model average in yellow over the dimmed CT, whole winding. Output under $B/<winding>/.
set -uo pipefail
W=/workspace; S=$W/p8/scripts; E=$W/fit1218C_main/Ctall10k/final; B=$W/seg_big
PY=$W/villa/volume-cartographer/.venv/bin/python
CT=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr
export SURF_ZARR=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr RANK_PROCS=8
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp L0_ONLY=0 MKL_NUM_THREADS=3  # as review_run.sh
log() { echo "=== $(date -u +%FT%TZ) $*"; }
# NOTE: df on the RunPod network volume shows the whole storage cluster, not this volume's 500 GB quota, and the API
# reports no usage; so this guard cannot see the quota (a full volume shows up only as "Disk quota exceeded" errors).
df_ok() { [ "$(df --output=avail -B1G $W | tail -1)" -gt 12 ] || { log "less than 12 GB free on the volume: stopping"; exit 1; }; }
for w in "$@"; do
  D=$B/$w; mkdir -p $D; df_ok
  if [ ! -f $D/snap.ok ]; then
    echo $w > $D/windings.txt
    $PY $W/pherc343/mesh/snap_meshes.py $E/exportf PHerc1218 $D/snap --windings $D/windings.txt > $D/snap.log 2>&1 && \
    $PY $W/pherc343/mesh/snap_meshes.py $D/snap PHerc1218 $D/snap_check --windings $D/windings.txt --max-off 2 > $D/snapcheck.log 2>&1 \
      && touch $D/snap.ok || { log "$w snap FAILED"; continue; }
    log "$w snapped: $(tail -1 $D/snap_check/snap_report.tsv | cut -f1-3)"
  fi
  if [ ! -f $D/flat/tifxyz/flatten.tifxyz/x.tif ]; then
    bash $S/flatten_one.sh $D/snap/$w $D/flat || { log "$w flatten FAILED"; continue; }
  fi
  if [ ! -d $D/render.zarr/0 ]; then
    df_ok
    env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
      --group-idx 0 --scale 1 --segmentation $D/flat/tifxyz/flatten.tifxyz --num-slices 66 --slice-step 1 --cache-gb 8 \
      --auto-crop --zarr-output $D/render.zarr > $D/render.log 2>&1 || { log "$w render FAILED"; continue; }
    log "$w rendered: $(grep -oE 'rendering [0-9]+x[0-9]+' $D/render.log | tail -1)"
  fi
  for m in dnative hybrid_3d2d-seed42 hybrid_3d2d-seed43 hecate; do
    ls $D/maps/render__${m}__L66*_reverse.* >/dev/null 2>&1 && continue
    OMP_NUM_THREADS=6 bash $S/run_ink.sh $D/render.zarr $m 0 $D/maps > /dev/null 2>> $D/ink.$m.err || log "$w $m FAILED"
  done
  $W/venv/bin/python $S/seg_yellow.py $D && log "$w done: $D/yellow.png"
done

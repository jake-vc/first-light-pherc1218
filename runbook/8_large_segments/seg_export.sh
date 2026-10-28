#!/bin/bash
# seg_export.sh - after the tall fit (job seg_tall, /workspace/fit1218C_main/Ctall10k): export its windings, measure
# each winding's placement (winner's +-2 voxel on-sheet check on the raw windings, m7 prediction), and find the
# candidate boxes in the new windings (map_candidates.py). Run through launch.sh.
set -uo pipefail
W=/workspace; S=$W/p8/scripts; F=$W/fit1218C_main; O=$F/Ctall10k; E=$O/final
VS=$W/villa_autosteps/spiral-fitting; VPY=$W/villa_main/spiral-fitting/.venv/bin/python
PY=$W/villa/volume-cartographer/.venv/bin/python
export SURF_ZARR=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr RANK_PROCS=10
log() { echo "=== $(date -u +%FT%TZ) $*"; }
until [ -e $W/p8/state/seg_tall.done ] || [ -e $W/p8/state/seg_tall.failed ]; do sleep 30; done
[ -e $W/p8/state/seg_tall.done ] || { log "seg_tall failed"; exit 1; }
CK=$(ls $O/full/*/checkpoint_fitted.ckpt | head -1) || exit 1  # the original: a copy on the volume was once cut short
mkdir -p $E
if [ ! -f $E/export.done ]; then
  log "export $CK"
  (cd $VS && $VPY $S/main_export_windings.py "$CK" $E/export $F/umbilicus.json 10 140) > $E/export.log 2>&1 || { tail -5 $E/export.log; exit 1; }
  mkdir -p $E/exportf; for d in $E/export/w*_main; do ln -sfn $d/$(basename $d) $E/exportf/$(basename $d); done
  touch $E/export.done
fi
ls -d $E/exportf/w*_main | xargs -n1 basename > $E/windings.txt; log "$(wc -l < $E/windings.txt) windings"
log "m7 on-sheet check (raw)"
$PY $W/pherc343/mesh/snap_meshes.py $E/exportf PHerc1218 $E/raw --windings $E/windings.txt --max-off 2 > $E/raw.log 2>&1 || log "raw check FAILED"
log "map candidates"
$W/venv/bin/python $S/map_candidates.py $E/exportf \
  C2f/w090=C2f/w090:11307,411,1556,1165 C2f/w081=C2f/w081:2666,358,1551,1349 C2f/w084=C2f/w084:1596,399,1464,1388 \
  C4f/w050=C4f/w050:6423,93,1803,1338 C4f/w049=C4f/w049:2695,0,1386,1365 C4f/w038=C4f/w038:3142,214,1176,1206 \
  C4f/w059=C4f/w059:874,272,1100,1062 C4f/w073=C4f/w073:9022,326,1127,1148 \
  C5f/w057=C5f/w057:5002,360,1518,1268 C5f/w073=C5f/w073:2998,0,1207,931 > $E/candidates.tsv 2> $E/map.err
cat $E/candidates.tsv; log done

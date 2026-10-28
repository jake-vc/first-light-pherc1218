#!/bin/bash
# fetch_band.sh <dataset dir> <z0> <z1> - a band's input slabs (z0, z1 multiples of 4, level-0 slices), like fetch_C.sh:
# lasagna normals/grad level 2, m7 level 1 and 0, CT level 1 and the whole of CT level 4; listing-based, in parallel.
set -euo pipefail
C=$1; Z0=$2; Z1=$3; S=/workspace/p8/scripts/fetch_subzarr.py
[ $((Z0 % 4)) -eq 0 ] && [ $((Z1 % 4)) -eq 0 ] || { echo "z0/z1 must be multiples of 4"; exit 2; }
SC=${SCROLL:-PHerc1218}; SS=${SESSION:-20250521120456}  # scan session id of that scroll
K=$SC/representations; L=$K/predictions/lasagna/$SS-lasagna-20260419180421
M=$K/predictions/surfaces/$SS-surface-20260413222639-surface-m7-L0-th0.2.zarr
V=$SC/volumes/$SS-8.640um-1.2m-116keV-masked.zarr
pids=()
for v in nx ny grad_mag; do python3 $S $L/${SC}_$v.ome.zarr 2 $((Z0 / 4)) $((Z1 / 4)) $C/lasagna_inputs/las_008_$v.ome.zarr 24 & pids+=($!); done
python3 $S $M 1 $((Z0 / 2)) $((Z1 / 2)) $C/src/m7.zarr 24 & pids+=($!)
(python3 $S $V 1 $((Z0 / 2)) $((Z1 / 2)) $C/src/ct.zarr 24 && python3 $S $V 4 0 1453 $C/src/ct.zarr 16) & pids+=($!)
python3 $S $M 0 $Z0 $Z1 $C/src/m7_L0.zarr 24 & pids+=($!)
rc=0; for p in "${pids[@]}"; do wait $p || rc=1; done
[ $rc -eq 0 ] && echo FETCH_DONE
exit $rc

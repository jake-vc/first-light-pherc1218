#!/bin/bash
# prep_band.sh <dataset dir> <z0> <z1> - build a band's fit inputs from already-downloaded slabs, like band A:
#   surf-SDT (m7 level 1, threshold 128, CT level-4 occupancy, CT level-1 zero mask), tracks (0fb38c45 extractor,
#   default spacing) from the local m7 level-0 slab; also writes spiral-scroll.json (CW, 8.64 um) and the Dopico axis.
# Expects <dataset>/src/{m7.zarr (group 1), m7_L0.zarr (group 0), ct.zarr (groups 1, 4)} and lasagna_inputs/las_008_*.
# Run it through launch.sh. Fails loudly if an input is missing.
set -euo pipefail
F=$1; Z0=$2; Z1=$3
SP=/workspace/villa/volume-cartographer/scripts/spiral; PYF=/workspace/villa/volume-cartographer/.venv/bin/python
for p in src/m7.zarr/1 src/m7_L0.zarr/0 src/ct.zarr/1 src/ct.zarr/4 lasagna_inputs/las_008_nx.ome.zarr/2 \
         lasagna_inputs/las_008_ny.ome.zarr/2 lasagna_inputs/las_008_grad_mag.ome.zarr/2; do
  [ -d "$F/$p" ] || { echo "missing input $F/$p"; exit 2; }
done
cp ${UMB:-/workspace/p8_pod_bundle/umbilicus_dopico_1218.json} "$F/umbilicus.json"
echo '{"schema_version": 1, "name": "'"${SCROLL:-PHerc1218}"'", "voxel_size_um": 8.64, "spiral_outward_sense": "CW", "normal_zarr_group": "2", "surf_sdt_zarr_group": "1", "lasagna_scale": 4}' > "$F/spiral-scroll.json"

echo "=== $(date -u +%FT%TZ) surf-SDT z $Z0:$Z1"
if ! [ -f "$F/sdt.ok" ]; then
  RES=""; [ -d "$F/lasagna_inputs/las_008_surf_sdt.ome.zarr" ] && RES=--resume  # --resume refuses a missing store
  (cd "$SP" && $PYF make_surf_sdt.py --surf "$F/src/m7.zarr" --group 1 --out "$F/lasagna_inputs/las_008_surf_sdt.ome.zarr" \
     --threshold 128 --working-voxel-um 8.64 --z-range "$Z0:$Z1" --ct "$F/src/ct.zarr" --ct-group 4 --ct-dilate 1 --workers ${SDT_WORKERS:-12} $RES)
  touch "$F/sdt.ok"
fi

echo "=== $(date -u +%FT%TZ) tracks z $Z0:$Z1"
if ! [ -f "$F/tracks.ok" ]; then
  mkdir -p "$F/tracks"
  sed -e "s|^predictions_zarr_path = .*|predictions_zarr_path = \"$F/src/m7_L0.zarr/0\"|" \
      -e "s|^tracks_dbm_path = .*|tracks_dbm_path = \"$F/tracks/2um_ds2_ps256_surf_v2.dbm\"|" \
      -e "s|^z_min, z_max = .*|z_min, z_max = $Z0, $Z1|" "$SP/extract_surface_tracks.py" > "$SP/extract_surface_tracks_$(basename "$F").py"
  # the copy must live in $SP: the extractor finds villa's vesuvius package relative to its own location
  (cd "$SP" && $PYF "$SP/extract_surface_tracks_$(basename "$F").py")
  ls "$F"/tracks/*.dbm.vctracks >/dev/null
  touch "$F/tracks.ok"
fi
echo "=== $(date -u +%FT%TZ) prep done"

#!/bin/bash
# flatten_one.sh <snapped winding dir> <out dir> - the winner's flattening step (pherc343 mesh/README.md step 4):
# villa lasagna fit.py with configs/flatten_fast_nofilter.json on one snapped winding; the flattened mesh is written to
# <out dir>/tifxyz/flatten.tifxyz. Prints the wall time.
set -euo pipefail
M=$(cd "$1" && pwd); O=$2; L=/workspace/villa/lasagna; PY=/workspace/villa/volume-cartographer/.venv/bin/python
mkdir -p "$O"; echo "{\"external_surfaces\": [{\"path\": \"$M\"}]}" > "$O/flatten_input.json"
t0=$(date +%s)
(cd $L && $PY fit.py configs/flatten_fast_nofilter.json "$O/flatten_input.json" --device cuda --out-dir "$O") > "$O/flatten.log" 2>&1
ls "$O/tifxyz/flatten.tifxyz/x.tif" >/dev/null && rm -rf "$O/model_snapshots" "$O/model_final.pt" && echo "flattened $(basename $M) in $(( $(date +%s) - t0 ))s -> $O/tifxyz/flatten.tifxyz"

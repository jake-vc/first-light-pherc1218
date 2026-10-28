#!/bin/bash
# run_fit.sh <window name> <dataset dir> <z_begin> <z_end> [steps] - fit one window with the band A settings:
#   1) 50-step smoke run (catches setup errors in minutes), 2) full run, 3) winner's snap, 4) +-2 vox on-sheet check.
# Each window has its own out/cache dirs under <dataset>/<name>/, so windows can run side by side (one per GPU via
# CUDA_VISIBLE_DEVICES). Run it through launch.sh; on-sheet summary in <dataset>/<name>/onsheet.txt.
# DENSE_SPACING_MODE (default phase = winner's, uses surf-SDT) can be set to winding_model (villa main's default) for the ablation.
set -euo pipefail
NAME=$1; F=$2; ZB=$3; ZE=$4; STEPS=${5:-30000}
W=/workspace; SP=$W/villa/volume-cartographer/scripts/spiral; PYF=$W/villa/volume-cartographer/.venv/bin/python
SURF=${SURF:-https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr}
D=$F/$NAME; mkdir -p "$D"
if [ "${SNAP_ONLY:-0}" != 1 ]; then  # snap-only needs only the fitted meshes
  [ -f "$F/sdt.ok" ] && [ -f "$F/tracks.ok" ] || { echo "band inputs not prepared (run prep_band.sh)"; exit 2; }
fi
overrides() { echo "{\"z_begin\": $ZB, \"z_end\": $ZE, \"input_disable_patches\": true, \"loss_weight_shell_outer\": 0, \"loss_weight_shell_patch_radius\": 0, \"dense_spacing_mode\": \"${DENSE_SPACING_MODE:-phase}\", \"optimizer_num_training_steps\": $1, \"track_crossing_mode\": \"count\"}"; }
fit() {  # <steps> <out dir> <log>
  mkdir -p "$2"
  (cd "$SP" && PYTHONUNBUFFERED=1 FIT_SPIRAL_OUT_DIR="$2" FIT_SPIRAL_CACHE_DIR="$D/cache" FIT_SPIRAL_RUN_TAG="p8$NAME" \
     FIT_SPIRAL_CONFIG_OVERRIDES="$(overrides "$1")" $PYF fit_spiral.py --dataset "$F") > "$3" 2>&1
  ls -d "$2"/*/meshes/fitted_* >/dev/null 2>&1 || { echo "no fitted meshes in $2"; return 1; }
}
if [ "${SNAP_ONLY:-0}" != 1 ]; then  # SNAP_ONLY=1: the fit already finished; redo only snap + on-sheet check
echo "=== $(date -u +%FT%TZ) $NAME smoke run (50 steps)"
fit 50 "$D/smoke" "$D/fit_smoke.log" || { echo "=== $(date -u +%FT%TZ) $NAME smoke run failed (e.g. GPU memory taken by screens); retrying once in 5 min"; rm -rf "$D/smoke"; sleep 300; fit 50 "$D/smoke" "$D/fit_smoke.log"; }
echo "=== $(date -u +%FT%TZ) $NAME full run ($STEPS steps), z $ZB-$ZE"
# A failed full run (disk full, OOM, a GPU hiccup) is retried ONCE from scratch: the August fitter cannot resume.
fit "$STEPS" "$D/runs" "$D/fit.log" || { echo "=== $(date -u +%FT%TZ) $NAME full run failed; retrying once from scratch"; mv "$D/fit.log" "$D/fit_failed1.log"; rm -rf "$D/runs" "$D/cache"; sleep 60; fit "$STEPS" "$D/runs" "$D/fit.log"; }
fi
# snap workers: 12 unless the container's memory cap is under 64 GB (pod a: 31 GB; 12 workers were OOM-killed)
MEMCAP=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo max); NP=12
[ "$MEMCAP" != max ] && [ "$MEMCAP" -lt 64000000000 ] && NP=4
MD=$(ls -dt "$D"/runs/*/meshes/fitted_* | head -1)
echo "=== $(date -u +%FT%TZ) $NAME snap + on-sheet check ($MD)"
ls -d "$MD"/w*_spliced_* | xargs -n1 basename > "$D/windings.txt"
SURF_ZARR=$SURF RANK_PROCS=${SNAP_PROCS:-$NP} $W/venv/bin/python $W/pherc343/mesh/snap_meshes.py "$MD" ${SCROLL:-PHerc1218} "$D/snap" --windings "$D/windings.txt" > "$D/snap.log" 2>&1
SURF_ZARR=$SURF RANK_PROCS=${SNAP_PROCS:-$NP} $W/venv/bin/python $W/pherc343/mesh/snap_meshes.py "$D/snap" ${SCROLL:-PHerc1218} "$D/snap_check" --windings "$D/windings.txt" --max-off 2 > "$D/snapcheck.log" 2>&1
$W/venv/bin/python - "$D" > "$D/onsheet.txt" <<'EOF'
import csv, json, sys
d = sys.argv[1]
r = list(csv.DictReader(open(f"{d}/snap_check/snap_report.tsv"), delimiter="\t"))
on = sorted(float(x["frac_with_sheet"]) for x in r)
area = {x["winding"]: json.load(open(f"{d}/snap/{x['winding']}/meta.json"))["area_cm2"] * float(x["frac_with_sheet"]) for x in r}
print(f"{len(on)} turns; on-sheet (+-2 vox) median {on[len(on)//2]:.2f}, max {on[-1]:.2f}; >=0.8: {sum(v >= 0.8 for v in on)}, >=0.6: {sum(v >= 0.6 for v in on)}; on-sheet area {sum(area.values()):.0f} cm2")
EOF
cat "$D/onsheet.txt"
# convergence note (assumption A1): loss averaged over the last 1,000 steps before 2k-steps-earlier and the end
$W/venv/bin/python - "$D/fit.log" "$STEPS" > "$D/converge.txt" <<'EOF2'
import re, sys
L = {int(a): float(b) for a, b in re.findall(r"step (\d+): loss = ([\d.]+)", open(sys.argv[1], errors="ignore").read())}
n = int(sys.argv[2]); avg = lambda k: sum(L[x] for x in L if k - 1000 <= x <= k) / max(1, sum(1 for x in L if k - 1000 <= x <= k))
a, b = avg(n - 2000), avg(n)
print(f"loss {a:.1f} at ~{n - 2000} -> {b:.1f} at ~{n}: {100 * (a - b) / max(a, 1e-9):.1f}% better in the last 2k steps" + (" (STILL IMPROVING > 3%)" if (a - b) / max(a, 1e-9) > 0.03 else ""))
EOF2
cat "$D/converge.txt"
echo "=== $(date -u +%FT%TZ) $NAME done"

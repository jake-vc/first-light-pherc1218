#!/bin/bash
# seam_pool.sh <worker id> - SEAM PASS: screen the strip across every spiral seam (theta 360|0) between consecutive
# windings w, w+1 of a window, when BOTH are in the preregistered scope (on-sheet >= 0.70, >= 1 cm2). Per seam:
# seam_strip.py (last/first 25 columns of the snapped windings) -> flatten_one.sh (winner's lasagna step) ->
# screen_one.sh (66-layer render, the three screen models at d = 0, screen_sheet.py: same rule) -> results in
# /workspace/screen/<W>s/<w>/ (stats.json, maps) and one line in /workspace/screen/<W>s/summary.jsonl. Claims are atomic
# mkdirs shared by any number of workers; renders are deleted after scoring. Windows in SEAM_POOL order.
set -uo pipefail
S=/workspace/p8/scripts; ST=/workspace/p8/state; PY=/workspace/venv/bin/python
ds() { case $1 in C*) echo /workspace/fit1218C ;; D*) echo /workspace/fit1218D ;; E[1-8]) echo /workspace/fit1218Ehi ;; E*) echo /workspace/fit1218Elo ;; esac; }
log() { echo "=== $(date -u +%FT%TZ) [$1] ${*:2}"; }
while true; do
  pending=0
  for W in ${SEAM_POOL:?}; do
    SM=${SEAM_MIN:-0.70}; SUF=s; [ "$SM" != 0.70 ] && SUF=sx  # sx = EXPLORATORY seams (a side below 0.70)
    F=$(ds $W); O=/workspace/screen/${W}$SUF; T=/workspace/seam/$W$SUF
    [ -f $ST/fit$W.failed ] && continue
    [ -f $ST/fit$W.done ] || { pending=1; continue; }
    [ -f $O/.complete ] && continue
    mkdir -p $O $T/.claim
    mapfile -t P < <(SEAM_MIN=$SM $PY - "$F/$W" <<'PY'
import csv, json, os, re, sys
d = sys.argv[1]; ok = {}; lo = float(os.environ.get("SEAM_MIN", "0.70")); sc = {}
for r in csv.DictReader(open(f"{d}/snap_check/snap_report.tsv"), delimiter="\t"):
    w, s = r["winding"], float(r["frac_with_sheet"]); m = f"{d}/snap/{w}"
    if s >= lo and os.path.exists(f"{m}/meta.json") and json.load(open(f"{m}/meta.json"))["area_cm2"] * s >= 1:
        k = int(re.match(r"w(\d+)", w).group(1)); ok[k] = w; sc[k] = s
for n in sorted(ok):  # exploratory mode keeps only the seams the preregistered pass skips (a side below 0.70)
    if n + 1 in ok and (lo >= 0.70 or min(sc[n], sc[n + 1]) < 0.70): print(ok[n], ok[n + 1])
PY
)
    for pr in "${P[@]}"; do
      set -- $pr; a=$1; b=$2; n=${a%%_*}; D=$O/$n
      [ -s $D/stats.json ] || [ -f $D/FAILED ] && continue
      mkdir $T/.claim/$n 2>/dev/null || continue
      if $PY $S/seam_strip.py $F/$W/snap/$a $F/$W/snap/$b $T/$n/strip.tifxyz > $T/$n.log 2>&1 \
         && bash $S/flatten_one.sh $T/$n/strip.tifxyz $T/$n/flat >> $T/$n.log 2>&1 \
         && line=$(bash $S/screen_one.sh $T/$n/flat/tifxyz/flatten.tifxyz $D "${W}$SUF/$n" 2>>$T/$n.log | tail -1) && [ -s $D/stats.json ]; then
        echo $T/$n/flat/tifxyz/flatten.tifxyz > $D/mesh_path.txt
        ( flock 7; echo "$line" >> $O/summary.jsonl ) 7>$O/.summary.lock
        rm -rf $D/render.zarr $D/render.zarr.log; log $1 "$W seam $n: $line"
      elif [ -f $T/$n.retried ]; then mkdir -p $D; echo "seam failed twice; see $T/$n.log" > $D/FAILED; log $1 "$W seam $n FAILED twice"
      else touch $T/$n.retried; rm -rf $T/.claim/$n $T/$n/flat $D; log $1 "$W seam $n failed once; released for retry"; sleep 30; fi
    done
    got=$(find $O -mindepth 2 -maxdepth 2 \( -name stats.json -size +0 -o -name FAILED \) 2>/dev/null | wc -l)
    if [ "$got" -ge "${#P[@]}" ]; then touch $O/.complete; log $1 "$W seam pass complete: $got of ${#P[@]} seams"; else pending=1; fi
  done
  [ $pending = 0 ] && { log $1 "all seams done"; exit 0; }
  sleep 60
done

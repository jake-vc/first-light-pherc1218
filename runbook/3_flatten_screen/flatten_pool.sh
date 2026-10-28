#!/bin/bash
# flatten_pool.sh <worker id> - flatten every in-scope snapped winding (readout rules) for the windows in
# FLAT_POOL, in order, sharing the work with other workers (claim = atomic mkdir). For window W (fit done):
#   in scope = on-sheet >= 0.70 (snap_check report) and mesh area x on-sheet >= 1 cm2 (same rule as the screen);
#   flatten_one.sh -> /workspace/flat/W/<winding>/tifxyz/flatten.tifxyz, linked as /workspace/flat/W/mesh/<winding dir>
#   (x/y/z from the flattened mesh; meta.json = flattened meta + the snapped mesh's area_cm2 for the scope rule);
#   /workspace/flat/W/.complete once every in-scope winding is flattened or FAILED.
set -uo pipefail
S=/workspace/p8/scripts; ST=/workspace/p8/state; PY=/workspace/venv/bin/python
ds() { case $1 in A) echo /workspace/fitA ;; C*) echo /workspace/fit1218C ;; D*) echo /workspace/fit1218D ;; E[1-8]) echo /workspace/fit1218Ehi ;; E*) echo /workspace/fit1218Elo ;; esac; }
log() { echo "=== $(date -u +%FT%TZ) [$1] ${*:2}"; }
while true; do
  pending=0
  for W in ${FLAT_POOL:?}; do
    F=$(ds $W); O=/workspace/flat/$W
    [ -f $ST/fit$W.failed ] && continue
    [ -f $ST/fit$W.done ] || { pending=1; continue; }
    MK=$O/.complete; [ "${FLAT_MIN:-0.70}" != 0.70 ] && MK=$O/.complete_${FLAT_MIN}
    [ -f $MK ] && continue
    # no readable on-sheet report yet -> not complete (an empty in-scope list once marked windows complete with 0 turns)
    [ -s $F/$W/snap_check/snap_report.tsv ] || { pending=1; continue; }
    mkdir -p $O/.claim $O/mesh
    mapfile -t WS < <($PY - "$F/$W" <<'PY'
import csv, json, sys, glob, os
d = sys.argv[1]
for r in csv.DictReader(open(f"{d}/snap_check/snap_report.tsv"), delimiter="\t"):
    w, s = r["winding"], float(r["frac_with_sheet"])
    m = f"{d}/snap/{w}"
    if s >= float(os.environ.get("FLAT_MIN", "0.70")) and os.path.exists(f"{m}/meta.json") and json.load(open(f"{m}/meta.json"))["area_cm2"] * s >= 1: print(w)
PY
)
    for w in "${WS[@]}"; do
      [ -e $O/mesh/$w/meta.json ] || [ -f $O/$w/FAILED ] && continue
      mkdir $O/.claim/$w 2>/dev/null || continue
      if bash $S/flatten_one.sh $F/$W/snap/$w $O/$w > $O/$w.log 2>&1; then
        mkdir -p $O/mesh/$w; for c in x y z mask; do [ -e $O/$w/tifxyz/flatten.tifxyz/$c.tif ] && ln -sfn $O/$w/tifxyz/flatten.tifxyz/$c.tif $O/mesh/$w/$c.tif; done
        $PY -c "import json,sys; a=json.load(open(sys.argv[1])); a['area_cm2']=json.load(open(sys.argv[2]))['area_cm2']; json.dump(a, open(sys.argv[3], 'w'))" \
          $O/$w/tifxyz/flatten.tifxyz/meta.json $F/$W/snap/$w/meta.json $O/mesh/$w/meta.json
        log $1 "$W/$w flattened ($(tail -1 $O/$w.log | grep -o 'in [0-9]*s'))"
      elif [ -f $O/$w.retried ]; then  # second failure: give up on this winding
        mkdir -p $O/$w; echo "flatten failed twice; see $O/$w.log" > $O/$w/FAILED; log $1 "$W/$w FAILED twice"
      else  # first failure (e.g. GPU memory taken by fits/screens at that moment): release it for one retry
        touch $O/$w.retried; rm -rf $O/$w $O/.claim/$w; log $1 "$W/$w failed once; released for retry"; sleep 30
      fi
    done
    n_ok=$(ls -d $O/mesh/*/meta.json 2>/dev/null | wc -l); n_bad=$(ls $O/*/FAILED 2>/dev/null | wc -l)
    if [ $((n_ok + n_bad)) -ge ${#WS[@]} ]; then touch $MK; log $1 "$W flattening complete: $n_ok ok, $n_bad failed"; else pending=1; fi
  done
  [ $pending = 0 ] && { log $1 "all windows flattened"; exit 0; }
  sleep 60
done

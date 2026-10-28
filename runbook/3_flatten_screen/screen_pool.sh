#!/bin/bash
# screen_pool.sh <worker id> - one screening worker. Walks the night's windows in order (band C, then D, then E) and
# helps screen every window whose fit is done (screen_1218.sh claims windings, so any number of workers on any pods
# share a window). When a window has no unclaimed windings left and all its windings are screened, the first worker to
# notice runs the detail review if anything was flagged (job review<n>). Loops until every window's fit is finished
# and nothing is left to claim. POOL="C1 C2 ..." picks the windows this pod can see (its datasets).
set -uo pipefail
S=/workspace/p8/scripts; ST=/workspace/p8/state; UMB=/workspace/p8_pod_bundle/umbilicus_dopico_1218.json
log() { echo "=== $(date -u +%FT%TZ) [$1] ${*:2}"; }
ds() { case $1 in A) echo /workspace/fitA ;; C*) echo /workspace/fit1218C ;; D*) echo /workspace/fit1218D ;;
       E[1-8]) echo /workspace/fit1218Ehi ;; E*) echo /workspace/fit1218Elo ;; esac; }
while true; do
  pending=0
  for n in ${POOL:?set POOL}; do
    b=${n%f}; b=${b%x}; F=$(ds $b); O=/workspace/screen/$n
    LO=${SCOPE_MIN:-0.70}; HI=9; FM=/workspace/flat/$b/.complete
    case $n in *x) LO=0.60; HI=0.70; FM=/workspace/flat/$b/.complete_0.60 ;; esac  # EXPLORATORY (outside prereg scope)
    [ -f $ST/fit$b.failed ] && continue
    [ -f $ST/fit$b.done ] || { pending=1; continue; }
    [ -f $O/.complete ] && continue
    MD=$F/$b/snap  # "<window>f" = the window's flattened meshes (readout rules), once flattening is complete
    if [ "$n" != "$b" ]; then [ -f $FM ] || { pending=1; continue; }; MD=/workspace/flat/$b/mesh; fi
    D_MIN=0 D_MAX=0 MIN_CM2=1 MIN_SNAP=$LO MAX_SNAP=$HI SNAP_REPORT=$F/$b/snap_check/snap_report.tsv SNAP_COL=frac_with_sheet \
      bash $S/screen_1218.sh $n $MD >> /workspace/p8/out/pool_$(hostname)_$1_$n.log 2>&1
    # complete when every in-scope winding has stats.json (claims of dead workers would block this: checked by hand)
    want=$(grep -o "^=== .* band $n: [0-9]* windings" /workspace/p8/out/pool_$(hostname)_$1_$n.log | tail -1 | awk '{print $5}')
    got=$(find $O -mindepth 2 -maxdepth 2 \( -name stats.json -size +0 -o -name FAILED \) 2>/dev/null | wc -l)  # empty files (disk-full) do not count; FAILED = gave up after a retry
    if [ -n "$want" ] && [ "$got" -ge "$want" ] && { [ "$n" = "$b" ] || [ -f $FM ]; }; then  # flattened: only once all its flattening is done
      touch $O/.complete; log $1 "$n complete: $got windings, $(grep -c '"candidate": true' $O/summary.jsonl 2>/dev/null) flagged"
      if grep -q '"candidate": true' $O/summary.jsonl 2>/dev/null && ! [ -f $ST/review$n.done ]; then
        bash $S/launch.sh review$n bash $S/retry.sh 2 bash $S/review_run.sh $O $UMB 6 && log $1 "review$n done"
      fi
    else
      pending=1  # others still screening it
    fi
  done
  [ $pending = 0 ] && { log $1 "all windows done"; exit 0; }
  sleep 60
done

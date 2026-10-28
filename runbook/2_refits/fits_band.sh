#!/bin/bash
# fits_band.sh <band> <dataset dir> <prep job> - fits_C.sh for any band: run this pod's share of the band's windows on
# its GPU, as many at once as GPU memory allows (measured on the first). Windows: WINDOWS="D1 15220 16220 D2 ..." (all
# of the band, same names on every pod); FIT_WINDOWS="D1 D2" picks this pod's share. Each window is job fit<name>.
set -uo pipefail
B=$1; F=$2; PREP=$3
S=/workspace/p8/scripts; ST=/workspace/p8/state
until [ -e $ST/$PREP.done ]; do sleep 60; done  # keep waiting if the prep fails: a restarted prep unblocks us (no give-up)
read -ra W <<< "${WINDOWS:?set WINDOWS}"; MINE=(); for ((i = 0; i < ${#W[@]}; i += 3)); do
  [[ " ${FIT_WINDOWS:-${W[i]}} " == *" ${W[i]} "* || -z "${FIT_WINDOWS:-}" ]] && MINE+=("${W[i]} ${W[i+1]} ${W[i+2]}"); done
NCPU=$(nproc 2>/dev/null); NCPU=${NCPU:-16}; [ "$NCPU" -gt 16 ] && NCPU=16
export OMP_NUM_THREADS=$(( NCPU / 4 > 2 ? NCPU / 4 : 2 )) MKL_NUM_THREADS=$(( NCPU / 4 > 2 ? NCPU / 4 : 2 ))
log() { echo "=== $(date -u +%FT%TZ) $*"; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }
optimising() { grep -q -E "Optimizing — [1-9][0-9]{2,}" "$F/$1/fit.log" 2>/dev/null; }
running() { pgrep -f "[r]un_fit.sh " | wc -l; }  # every band's fits on this pod (state dir is shared across pods)
need=${FIT_MIB:-0}  # MiB one fit needs (x1.2 margin); measured on the first window if unset
for w in "${MINE[@]}"; do
  set -- $w; name=$1
  [ -f "$ST/fit$name.done" ] && { log "$name already done"; continue; }
  exec 8>"/tmp/gpu_start.lock"; flock 8  # one start decision at a time per pod (several band schedulers share a GPU)
  if [ "$need" -gt 0 ]; then
    until [ "$(free_mib)" -gt "$need" ] && [ "$(running)" -lt ${MAX_FITS:-4} ]; do sleep 60; done
  fi
  log "start $name (z $2-$3), GPU free $(free_mib) MiB, ${OMP_NUM_THREADS} threads/fit"
  (setsid nohup bash $S/launch.sh "fit$name" bash $S/run_fit.sh "$name" "$F" "$2" "$3" "${FIT_STEPS:-10000}" >/dev/null 2>&1 </dev/null 8>&- &)  # 8>&-: the fit must not hold the start lock
  until optimising "$name" || [ -f "$ST/fit$name.failed" ]; do sleep 30; done
  [ -f "$ST/fit$name.failed" ] && { log "$name failed before optimising"; exec 8>&-; [ "$need" -eq 0 ] && exit 1; continue; }
  if [ "$need" -eq 0 ]; then
    sleep 120; used=$(nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits | sort -n | tail -1)
    need=$(( used * 12 / 10 )); log "one fit uses ${used} MiB on the GPU; next windows start when ${need} MiB is free"
  else
    sleep 60  # let the new fit's memory show up before the next decision
  fi
  exec 8>&-
done
log "all windows started; waiting for them to finish"
for w in "${MINE[@]}"; do set -- $w; bash $S/waitfor.sh fit$1; echo "$1: $(cat $F/$1/onsheet.txt 2>/dev/null || echo 'no on-sheet result')"; done

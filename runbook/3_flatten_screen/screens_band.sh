#!/bin/bash
# screens_band.sh <dataset dir> - screens_C.sh for any band: for each window in FIT_WINDOWS (this pod's share), wait for its fit job
# (fitC<n>), then screen every turn with >= 70% of nodes on the m7 sheet and >= 1 cm2 on-sheet (prereg scope), with
# reader-v2 + dense_native + reader-v3 at d = 0; then the detail review if anything is flagged. Each window is its own
# launcher job scrC<n>. Screens run on the same GPU as any remaining fits.
set -uo pipefail
S=/workspace/p8/scripts; ST=/workspace/p8/state; F=${1:?dataset dir}
UMB=/workspace/p8_pod_bundle/umbilicus_dopico_1218.json
log() { echo "=== $(date -u +%FT%TZ) $*"; }
for n in ${FIT_WINDOWS:?set FIT_WINDOWS, e.g. "C1 C2"}; do
  until [ -f $ST/fit$n.done ] || [ -f $ST/fit$n.failed ]; do sleep 30; done; [ -f $ST/fit$n.done ] || { log "fit$n failed; skipping its screen"; continue; }
  [ -f $ST/scr$n.done ] && { log "scr$n already done"; continue; }
  log "screening $n"
  bash $S/launch.sh scr$n bash -c "D_MIN=0 D_MAX=0 MIN_CM2=1 MIN_SNAP=${SCOPE_MIN:-0.70} SNAP_REPORT=$F/$n/snap_check/snap_report.tsv \
      SNAP_COL=frac_with_sheet bash $S/screen_1218.sh $n $F/$n/snap && \
      if grep -q '\"candidate\": true' /workspace/screen/$n/summary.jsonl 2>/dev/null; then bash $S/review_run.sh /workspace/screen/$n $UMB 6; fi"
  log "$n: $(grep -c '' /workspace/screen/$n/summary.jsonl 2>/dev/null) turns screened, $(grep -c '"candidate": true' /workspace/screen/$n/summary.jsonl 2>/dev/null) flagged"
done

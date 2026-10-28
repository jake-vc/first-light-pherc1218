#!/bin/bash
# autosteps_run.sh - one placement-vs-steps run for the auto-steps study (work/proposals/auto-steps/PLAN.md), with the
# villa branch fit-track-satisfaction-monitor (worktree /workspace/villa_autosteps, villa_main's venv). Generalises
# autosteps_c7.sh: any dataset/window, tracks on, extra config members (e.g. the periodic track-satisfaction metric or
# the early stop), the 1,000-step autosave checkpoints copied as they appear, then per checkpoint the winner's +-2 voxel
# on-sheet check on the RAW windings and, at SNAP_STEPS, snap + check. Output: $O/curve.tsv (as autosteps_c7.sh),
# $O/metrics.jsonl (FIT_SPIRAL_METRICS_HISTORY), $O/fit.log. No change to the dataset inputs. Run through launch.sh.
# Required env: NAME (run name), SRC (August-format dataset dir), Z0 Z1 (z window), WLO WHI (windings to export).
# Optional: STEPS (10000), EXTRA (JSON members appended to the overrides), SCROLL (PHerc1218), SURF (m7 surface zarr),
#           NUM_WINDINGS (260; empty = villa default), CHECK (raw | none), SNAP_STEPS ("3000 6000 10000").
#           CHECKS_ONLY=1: no fit; run the checks on the checkpoints already in $O/ck (steps already in curve.tsv are
#           skipped), e.g. after the checks of a finished fit were interrupted.
set -uo pipefail
: "${NAME:?}" "${SRC:?}" "${Z0:?}" "${Z1:?}" "${WLO:?}" "${WHI:?}"
STEPS=${STEPS:-10000}; EXTRA=${EXTRA:-}; SCROLL=${SCROLL:-PHerc1218}; CHECK=${CHECK:-raw}
SNAP_STEPS=${SNAP_STEPS:-"3000 6000 10000"}; NUM_WINDINGS=${NUM_WINDINGS-260}
SURF=${SURF:-https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr}
W=/workspace; VS=$W/villa_autosteps/spiral-fitting; VPY=$W/villa_main/spiral-fitting/.venv/bin/python
F=${SRC}_main; O=$F/$NAME; D=$O/full
PY=$W/villa/volume-cartographer/.venv/bin/python; SNAP="$PY $W/pherc343/mesh/snap_meshes.py"
export SURF_ZARR=$SURF RANK_PROCS=8
log() { echo "=== $(date -u +%FT%TZ) $*"; }
mkdir -p $D $O/ck
git -C $VS log -1 --format='%H %s' | tee $O/villa_commit.txt

# villa-main view of the August dataset (as main_fit_c7.sh setup): links + main's own packed sidecars
if [ ! -f $F/spiral-scroll.json ]; then
  log "setting up $F from $SRC"
  mkdir -p $F/lasagna_inputs
  ln -sfn $SRC/src $F/src; ln -sfn $SRC/tracks $F/tracks; cp $SRC/umbilicus.json $F/
  for v in nx ny grad_mag; do ln -sfn $SRC/lasagna_inputs/las_008_$v.ome.zarr $F/lasagna_inputs/las_008_$v.ome.zarr; done
  nw=""; [ -n "$NUM_WINDINGS" ] && nw=", \"num_windings\": $NUM_WINDINGS"
  echo "{\"schema_version\": 1, \"name\": \"$SCROLL\", \"voxel_size_um\": 8.64, \"spiral_outward_sense\": \"CW\", \"normal_zarr_group\": \"2\", \"lasagna_scale\": 4, \"paths\": {\"tracks_dbm\": \"tracks/2um_ds2_ps256_surf_v2.dbm\"}$nw}" > $F/spiral-scroll.json
  (cd $VS && $VPY pack_resident_pools.py $F/lasagna_inputs --what normals,grad_mag --normal-group 2 --ct $F/src/ct.zarr --ct-group 4) > $F/pack.log 2>&1 \
    || { log "pack FAILED"; tail -5 $F/pack.log; exit 1; }
fi

check() {  # <step> <checkpoint>: export + raw check (+ snap at SNAP_STEPS); one curve line (as autosteps_c7.sh)
  local s=$1 ck=$2 E=$O/s$1; mkdir -p $E
  (cd $VS && $VPY $W/p8/scripts/main_export_windings.py "$ck" $E/export $F/umbilicus.json $WLO $WHI) > $E/export.log 2>&1 \
    || { log "step $s export FAILED"; return; }
  mkdir -p $E/exportf; for d in $E/export/w*_main; do ln -sfn $d/$(basename $d) $E/exportf/$(basename $d); done
  ls -d $E/exportf/w*_main* | xargs -n1 basename > $E/windings.txt
  $SNAP $E/exportf $SCROLL $E/raw --windings $E/windings.txt --max-off 2 > $E/raw.log 2>&1 || log "step $s raw check FAILED"
  local snapped=""
  if [[ " $SNAP_STEPS " == *" $s "* ]]; then
    $SNAP $E/exportf $SCROLL $E/snap --windings $E/windings.txt > $E/snap.log 2>&1 && \
      $SNAP $E/snap $SCROLL $E/snap_check --windings $E/windings.txt --max-off 2 > $E/snapcheck.log 2>&1 \
      && snapped=$E/snap_check/snap_report.tsv || log "step $s snap FAILED"
  fi
  $PY - $s $E/raw/snap_report.tsv "$snapped" >> $O/curve.tsv <<'EOF'
import csv, statistics, sys
def stats(p):
    if not p: return "", "", ""
    v = [float(r["frac_with_sheet"]) for r in csv.DictReader(open(p), delimiter="\t")]
    return len(v), f"{statistics.median(v):.3f}", f"{statistics.mean(v):.3f}"
n, med, mean = stats(sys.argv[2]); _, smed, smean = stats(sys.argv[3])
print(f"{sys.argv[1]}\t{n}\t{med}\t{mean}\t{smed}\t{smean}")
EOF
  log "step $s: $(tail -1 $O/curve.tsv)"
}

[ -f $O/curve.tsv ] || printf 'step\twindings\traw_median\traw_mean\tsnapped_median\tsnapped_mean\n' > $O/curve.tsv
if [ "${CHECKS_ONLY:-0}" = 1 ]; then
  for s in $(ls $O/ck/step_*.ckpt | grep -oE 'step_[0-9]+' | cut -d_ -f2 | sort -n); do
    cut -f1 $O/curve.tsv | grep -qx "$s" && continue
    check $s $O/ck/step_$s.ckpt
  done
  log "done: $O/curve.tsv"; cat $O/curve.tsv; exit 0
fi
OVR="{\"z_begin\": $Z0, \"z_end\": $Z1, \"input_disable_patches\": true, \"loss_weight_shell_outer\": 0, \"input_use_outer_shell\": false, \"dense_spacing_mode\": \"grad_mag\", \"input_use_tracks\": true, \"optimizer_num_training_steps\": $STEPS${EXTRA:+, $EXTRA}}"
echo "$OVR" > $O/overrides.json; log "fit start: $OVR"
start=$(date +%s)
(cd $VS && PYTHONUNBUFFERED=1 FIT_SPIRAL_OUT_DIR=$D FIT_SPIRAL_CACHE_DIR=$O/cache FIT_SPIRAL_RUN_TAG=p8$NAME \
  FIT_SPIRAL_METRICS_HISTORY=$O/metrics.jsonl FIT_SPIRAL_CONFIG_OVERRIDES="$OVR" \
  $VPY fit_spiral.py --dataset $F) > $O/fit.log 2>&1 & fit=$!
last=""; pending=()
while :; do
  ck=$(ls $D/*/checkpoint_fitted.ckpt 2>/dev/null | head -1)
  if [ -n "$ck" ]; then
    sig=$(stat -c %Y.%s "$ck")
    if [ "$sig" != "$last" ]; then  # new autosave: step = last logged step (every 200) rounded down to 1,000
      last=$sig; n=$(grep -oE '^step [0-9]+:' $O/fit.log | tail -1 | grep -oE '[0-9]+'); k=$(( ${n:-0} / 1000 * 1000 ))
      [ $k -gt 0 ] && [ ${n:-0} -lt $((STEPS - 200)) ] && { cp "$ck" $O/ck/step_$k.ckpt && [ "$(stat -c %s "$ck")" = "$(stat -c %s $O/ck/step_$k.ckpt)" ] \
        && { log "saved checkpoint at step $k"; pending+=($k); } || { log "checkpoint copy at step $k INCOMPLETE, skipped"; rm -f $O/ck/step_$k.ckpt; }; }
    fi
  fi
  kill -0 $fit 2>/dev/null || break
  sleep 20
done
wait $fit; rc=$?; secs=$(( $(date +%s) - start ))
ran=$(grep -oE '^early stop after [0-9]+' $O/fit.log | grep -oE '[0-9]+$'); ran=${ran:-$STEPS}
log "fit exit $rc after ${secs}s; iterations run $ran; $(grep -c 'satisfied_track_points =' $O/fit.log) track-satisfaction lines"
echo -e "fit_seconds\t$secs\niterations\t$ran" > $O/fit_time.tsv
[ $rc = 0 ] || exit $rc
safe_cp() {  # copy and verify the size (a copy on the network volume was once cut short without an error)
  cp "$1" "$2" && [ "$(stat -c %s "$1")" = "$(stat -c %s "$2")" ] || { log "copy of $1 INCOMPLETE"; rm -f "$2"; return 1; }
}
safe_cp $(ls $D/*/checkpoint_fitted.ckpt | head -1) $O/ck/step_$ran.ckpt || exit 1  # the final checkpoint
[ "$CHECK" = none ] && { log "done (no checks)"; exit 0; }
for s in $(printf '%s\n' "${pending[@]}" $ran | sort -nu); do check $s $O/ck/step_$s.ckpt; done
log "done: $O/curve.tsv"; cat $O/curve.tsv

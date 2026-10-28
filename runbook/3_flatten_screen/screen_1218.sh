#!/bin/bash
# screen_1218.sh - prereg screen of one PHerc1218 sweep window: every spliced winding >= MIN_CM2, largest first.
#   screen_1218.sh <band label> <fitted meshes dir>        e.g. A /workspace/p8_pod_bundle/1218_sweep/<run>/meshes/fitted_<run>
# Per winding: 66-layer render (VC3D 359bbed, CT streamed) -> reader-v2 + dense_native, d -1..+1, both directions ->
# screen_sheet.py -> delete the render (maps, stats.json, sheet.png kept). The next render runs while the GPU works.
set -uo pipefail
BAND=$1; MDIR=$2; MIN_CM2=${MIN_CM2:-4}; MAX_TURNS=${MAX_TURNS:-0}; D_MIN=${D_MIN:--1}; D_MAX=${D_MAX:-1}
W=/workspace; S=$W/p8/scripts; OUT=$W/screen/$BAND
CT=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr
export CKPT_DIR=$W/ckpt PY=$W/venv/bin/python HECATE_PY=$W/ckpt/hecate.py TMPDIR=$W/tmp L0_ONLY=0 OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
mkdir -p $OUT $TMPDIR
log() { echo "=== $(date -u +%FT%TZ) $*"; }

# prereg Scope: only windings snapped onto the m7 sheet over >= MIN_SNAP of their nodes (snap_report.tsv from the
# winner's snap_meshes.py, run on MDIR beforehand); the rest is "no data", listed in $OUT/no_data.tsv.
# SNAP_REPORT/SNAP_COL: which report and column give the on-sheet fraction (default: the +-2 vox check of the snapped
# meshes, column frac_with_sheet). MIN_CM2 applies to mesh area x on-sheet fraction.
MIN_SNAP=${MIN_SNAP:-0.8}; SNAP_REPORT=${SNAP_REPORT:-$MDIR/snap_report.tsv}; SNAP_COL=${SNAP_COL:-frac_snapped}
export MAX_TURNS
mkdir -p $OUT
mapfile -t MESHES < <($PY - "$MDIR" "$MIN_CM2" "$MIN_SNAP" "$OUT/no_data.tsv" "$SNAP_REPORT" "$SNAP_COL" <<'EOF'
import csv, glob, json, os, sys
d, mn, ms_, nd, rp, col = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
snap = {r["winding"]: float(r[col]) for r in csv.DictReader(open(rp), delimiter="\t")}
keep, drop = [], []
for f in glob.glob(f"{d}/w*_spliced_*/meta.json"):
    w = f.split("/")[-2]; a = json.load(open(f))["area_cm2"]; s = snap.get(w, 0.0)
    (keep if a * s >= mn and s >= ms_ and s < float(os.environ.get("MAX_SNAP", "9")) else drop).append((a * s, a, s, w))
with open(nd, "w") as fh:
    fh.write("winding\tmesh_cm2\tfrac_snapped\n")
    for _, a, s, w in sorted(drop, reverse=True): fh.write(f"{w}\t{a:.2f}\t{s:.3f}\n")
for _, a, s, w in sorted(keep, reverse=True)[: int(os.environ.get("MAX_TURNS", "0")) or None]: print(f"{d}/{w}")
EOF
)
log "band $BAND: ${#MESHES[@]} windings with snapped area >= $MIN_CM2 cm2 and frac_snapped >= $MIN_SNAP in $MDIR ($(($(wc -l < $OUT/no_data.tsv) - 1)) no-data)"

render() {  # <mesh> <out.zarr>
  [ -d "$2/0" ] && return 0
  env QT_QPA_PLATFORM=offscreen OMP_NUM_THREADS=6 $W/vc3d/squashfs-root/AppRun vc_render_tifxyz --volume "$CT" \
    --group-idx 0 --scale 1 --segmentation "$1" --num-slices 66 --slice-step 1 --auto-crop --cache-gb 8 --zarr-output "$2" > "$2.log" 2>&1
}
zpath() { local n; n=$(basename "$1"); n=${n%%_spliced*}; echo "$W/renders/${BAND}_$n.zarr"; }
mkdir -p $W/renders
# Several workers (on this pod or others) may screen the same band at once: each winding is claimed with an atomic
# mkdir in $OUT/.claim before rendering, so no two workers render or screen the same winding; summary lines are
# appended under a lock. A worker's next winding is claimed (and pre-rendered) while the GPU works on the current one.
mkdir -p $OUT/.claim
claim() {  # <first index> -> echo the first unscreened winding index >= it that this worker claimed, or nothing
  local k
  for ((k = $1; k < ${#MESHES[@]}; k++)); do
    local n; n=$(basename "${MESHES[$k]}"); n=${n%%_spliced*}
    [ -s $OUT/$n/stats.json ] && continue
    mkdir $OUT/.claim/$n 2>/dev/null && { echo "$(hostname) $$ $(date -u +%FT%TZ)" > $OUT/.claim/$n/by; echo $k; return; }
  done
}
i=$(claim 0); pid=""
while [ -n "$i" ]; do
  M=${MESHES[$i]}; N=$(basename "$M"); N=${N%%_spliced*}; Z=$(zpath "$M"); D=$OUT/$N
  t0=$(date +%s)
  [ -n "$pid" ] && wait $pid
  [ -d "$Z/0" ] || render "$M" "$Z"
  t1=$(date +%s)
  nx=$(claim $((i + 1))); pid=""
  if [ -n "$nx" ]; then Mn=${MESHES[$nx]}; render "$Mn" "$(zpath "$Mn")" & pid=$!; fi
  if [ -d "$Z/0" ]; then
    if ! MODELS="${SCREEN_MODELS:-readerv2 dnative readerv3}" P_VILLA=${P_VILLA:-2} P_HEC=0 bash $S/run_depth_sweep.sh "$Z" $D/maps $D_MIN $D_MAX > $D.sweep.log 2>&1; then
      # an incomplete sweep (missing model maps) must never be scored: retry once (another worker), then mark FAILED
      mkdir -p $D
      if [ -f $D/retried ]; then echo "sweep failed twice; see $D.sweep.log" > $D/FAILED; log "$N sweep FAILED twice: not screened"
      else rm -rf $D/maps; touch $D/retried; rm -rf $OUT/.claim/$N; log "$N sweep had failures: released for one retry"; fi
      rm -rf "$Z" "$Z.log"; i=$nx; continue
    fi
    t2=$(date +%s)
    grep -a -o "crop \[[^]]*\]" "$Z.log" | tail -1 > $D/render_crop.txt  # auto-crop origin, for review
    echo "$M" > $D/mesh_path.txt
    if line=$($PY $S/screen_sheet.py "$Z" $D/maps $D "$BAND/$N" 2>> $OUT/errors.log); then
      ( flock 7; echo "$line" >> $OUT/summary.jsonl ) 7>$OUT/.summary.lock; rm -rf "$Z" "$Z.log"
    fi
    log "$N render $((t1 - t0))s sweep $((t2 - t1))s (winding $((i + 1)) of ${#MESHES[@]}) $line"
  else
    mkdir -p $D  # same rule for a failed render: retry once, then mark FAILED
    if [ -f $D/retried ]; then echo "render failed twice; see $Z.log" > $D/FAILED; log "$N render FAILED twice: not screened"
    else touch $D/retried; rm -rf "$Z" "$Z.log" $OUT/.claim/$N; log "$N render FAILED: released for one retry"; fi
  fi
  i=$nx
done
[ -n "$pid" ] && wait $pid
log "band $BAND: this worker has nothing left to claim"

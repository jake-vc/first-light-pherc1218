#!/bin/bash
# retry.sh <tries> <command...> - run a command up to <tries> times (60 s apart) until it succeeds. For idempotent
# steps only (prep_band.sh resumes via sdt.ok/tracks.ok and --resume; fetch skips existing chunks; reviews redo renders).
n=$1; shift
for ((i = 1; i <= n; i++)); do
  "$@" && exit 0
  echo "=== $(date -u +%FT%TZ) attempt $i of $n failed: $*"; [ $i -lt $n ] && sleep 60
done
exit 1

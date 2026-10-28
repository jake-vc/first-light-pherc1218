#!/bin/bash
# waitfor.sh <job>... - block until every named job has a .done marker; exit 1 as soon as any has a .failed marker.
S=/workspace/p8/state
while true; do
  all=1
  for j in "$@"; do
    [ -f "$S/$j.failed" ] && { echo "waitfor: $j failed: $(cat "$S/$j.failed")"; exit 1; }
    [ -f "$S/$j.done" ] || all=0
  done
  [ "$all" = 1 ] && exit 0
  sleep 30
done

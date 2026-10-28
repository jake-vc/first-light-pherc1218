#!/bin/bash
# launch.sh <job> <command...> - run one P8 pod job at most once at a time, with explicit state markers.
# Refuses to start if <job> is already running (flock), so a duplicate launch can never run alongside.
# State in /workspace/p8/state: <job>.running while it runs, then <job>.done or <job>.failed (exit code, times).
# Log: /workspace/p8/out/<job>.log. Start detached:  setsid nohup bash launch.sh <job> cmd... >/dev/null 2>&1 </dev/null &
# If the launcher is stopped by a signal (killtree.sh sends TERM), the job is recorded as .failed and .running is
# removed, so a marker never outlives its job (SIGKILL cannot be caught: night_check.sh also checks the PID).
# P8_STATE / P8_OUT override the two directories (tests only).
set -u
J=$1; shift
S=${P8_STATE:-/workspace/p8/state}; O=${P8_OUT:-/workspace/p8/out}; mkdir -p "$S" "$O"
exec 9>"$S/$J.lock"
flock -n 9 || { echo "$J is already running: $(cat "$S/$J.running" 2>/dev/null)"; exit 3; }
rm -f "$S/$J.done" "$S/$J.failed"
start=$(date -u +%FT%TZ)
finish() {  # <exit code> [note]: record the outcome and clear the running marker
  local end; end=$(date -u +%FT%TZ)
  if [ "$1" -eq 0 ]; then echo "rc=0 start=$start end=$end" > "$S/$J.done"
  else echo "rc=$1 start=$start end=$end${2:+ $2}" > "$S/$J.failed"; fi
  rm -f "$S/$J.running"
}
for sig in TERM INT HUP; do
  trap "kill \$child 2>/dev/null; finish 143 'stopped by SIG$sig'; exit 143" $sig
done
echo "pid=$$ start=$start cmd=$*" > "$S/$J.running"
"$@" > "$O/$J.log" 2>&1 9>&- & child=$!  # 9>&-: children must not inherit the lock; background + wait so a signal
wait $child; rc=$?                       # to the launcher is handled at once, not after the job ends
finish "$rc"
exit "$rc"

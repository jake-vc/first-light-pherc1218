#!/bin/bash
# tests/launch_test.sh <launch.sh> - launch.sh behaviour, on the pod (needs flock), in a throwaway state dir:
# success -> .done; failure -> .failed with rc; duplicate refused; TERM to the launcher -> .failed, no .running,
# job process gone.
set -u
L=$1; T=$(mktemp -d); export P8_STATE=$T/state P8_OUT=$T/out; fail=0
ok() { echo "ok   $1"; }; bad() { echo "FAIL $1"; fail=1; }
bash $L t1 true; [ -e $P8_STATE/t1.done ] && [ ! -e $P8_STATE/t1.running ] && ok "success -> done" || bad "success -> done"
bash $L t2 bash -c 'exit 7'; grep -q "rc=7" $P8_STATE/t2.failed 2>/dev/null && ok "failure -> failed rc=7" || bad "failure -> failed"
setsid bash $L t3 sleep 300 >/dev/null 2>&1 </dev/null & sleep 1
out=$(bash $L t3 true); [ $? = 3 ] && ok "duplicate refused" || bad "duplicate refused ($out)"
lp=$(grep -oE "pid=[0-9]+" $P8_STATE/t3.running | cut -d= -f2); sp=$(ps -o pid= --ppid $lp | tr -d ' ')
kill -TERM $lp; sleep 1
[ ! -e $P8_STATE/t3.running ] && grep -q "stopped by SIGTERM" $P8_STATE/t3.failed && ok "TERM -> failed, marker cleared" || bad "TERM -> failed, marker cleared"
kill -0 $sp 2>/dev/null && { bad "job process still running ($sp)"; kill $sp; } || ok "job process stopped"
rm -rf $T; exit $fail

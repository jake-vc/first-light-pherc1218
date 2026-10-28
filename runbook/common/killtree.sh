#!/bin/bash
# killtree.sh <job> - stop one launcher job and everything it started, by exact PID (never a name pattern). Only acts
# if the PID from <job>.running exists on THIS pod and is that job's launch.sh (the state dir is shared across pods).
J=$1; ST=/workspace/p8/state
pid=$(sed -n 's/^pid=\([0-9]*\).*/\1/p' $ST/$J.running 2>/dev/null); [ -n "$pid" ] || exit 0
ps -p $pid -o args= 2>/dev/null | grep -q "launch.sh $J " || exit 0
tree() { local c; for c in $(ps -o pid= --ppid $1); do tree $c; done; echo $1; }
kill $(tree $pid) 2>/dev/null; sleep 1; echo "stopped $J (pid $pid) on $(hostname)"

#!/bin/bash
# ctrl_v3.sh - run reader-v3 on the PHerc. 343 control render (d -1..+1) and score it with calib_343.py.
set -euo pipefail
export CKPT_DIR=/workspace/ckpt PY=/workspace/venv/bin/python HECATE_PY=/workspace/ckpt/hecate.py TMPDIR=/workspace/tmp L0_ONLY=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
mkdir -p /workspace/tmp
MODELS=readerv3 P_VILLA=2 P_HEC=0 bash /workspace/p8/scripts/run_depth_sweep.sh /workspace/ctrl/concat_w047-w048_R5B2_z9500-11000_66.zarr /workspace/ctrl/maps_v3 -1 1
mkdir -p /workspace/p8/out/ctrl_v3
/workspace/venv/bin/python /workspace/p8/scripts/calib_343.py /workspace/ctrl/maps_v3 /workspace/pherc343 /workspace/p8/out/ctrl_v3

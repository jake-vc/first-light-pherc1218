#!/bin/bash
# prep_C.sh - wait for band C inputs and the pod setup, then prepare band C (z 9976-15744) with prep_band.sh.
set -euo pipefail
bash /workspace/p8/scripts/waitfor.sh fetchC setup_extra
bash /workspace/p8/scripts/prep_band.sh /workspace/fit1218C 9976 15744

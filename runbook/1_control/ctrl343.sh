#!/bin/bash
# ctrl343.sh - prepare PHerc0343 inputs for z 9736-10864 (window 9800-10800 +- 64), gently (CPU only, during the 1218 run)
set -euo pipefail
S=/workspace/p8/scripts; export SCROLL=PHerc0343 SESSION=20250521140437 UMB=/workspace/pherc343/inputs/umbilicus_PHerc0343.json
nice -n 10 bash $S/fetch_band.sh /workspace/fit343 9736 10864
SDT_WORKERS=6 nice -n 10 bash $S/prep_band.sh /workspace/fit343 9736 10864

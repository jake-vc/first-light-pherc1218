#!/bin/bash
# after setup_pod.sh: VC3D renderer (main-branch build), spiral-fit env (villa 0fb38c45 + psutil), winner's patch
set -euo pipefail
export UV_CACHE_DIR=/workspace/.uv-cache UV_PYTHON_INSTALL_DIR=/workspace/.uv-python UV_LINK_MODE=copy UV_HTTP_TIMEOUT=600 PATH=/workspace/bin:$PATH
mkdir -p /workspace/vc3d && cd /workspace/vc3d
# VC3D from main: whatever the "latest" release (rebuilt from main) currently serves; name and sha256 recorded
URL=$(curl -sf https://api.github.com/repos/ScrollPrize/villa/releases/tags/latest | python3 -c '
import json, sys
print([a["browser_download_url"] for a in json.load(sys.stdin)["assets"] if a["name"].endswith("linux-x86_64.AppImage")][0])')
NAME=$(basename "$URL")
if [ ! -x squashfs-root/AppRun ]; then
  curl -sfL -o "$NAME" "$URL"; chmod +x "$NAME"; ./"$NAME" --appimage-extract >/dev/null
fi
sha256sum "$NAME" | tee /workspace/p8/out/vc3d_build.txt
cd /workspace/villa/volume-cartographer/scripts/spiral && CMAKE_BUILD_PARALLEL_LEVEL=8 uv sync
uv pip install -q --python /workspace/villa/volume-cartographer/.venv/bin/python psutil
cd /workspace/villa && (git apply --check /workspace/pherc343/mesh/fit_spiral_shell_optional.patch && git apply /workspace/pherc343/mesh/fit_spiral_shell_optional.patch) || git diff --stat
/workspace/villa/volume-cartographer/.venv/bin/python -c "import torch, psutil; print('spiral env torch', torch.__version__, torch.cuda.is_available())"

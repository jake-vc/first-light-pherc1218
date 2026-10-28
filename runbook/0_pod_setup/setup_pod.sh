#!/bin/bash
# setup_pod.sh - P8 pod environment, following Nieuwlaar/pherc343-first-letters ink/Dockerfile by hand.
# Everything lives on /workspace (survives stop/start). Log: /workspace/p8/out/setup.log
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 UV_LINK_MODE=copy UV_HTTP_TIMEOUT=600
export UV_CACHE_DIR=/workspace/.uv-cache UV_PYTHON_INSTALL_DIR=/workspace/.uv-python PATH=/workspace/bin:$PATH
W=/workspace; mkdir -p $W/p8/out $W/bin $W/ckpt
VILLA_COMMIT=0fb38c45b488e192566ea83ae36369cb6db92652
step() { echo "=== $(date -u +%FT%TZ) $*"; }

step apt
apt-get update -qq
apt-get install -y -qq --no-install-recommends git build-essential cmake ninja-build pkg-config libgomp1 zstd pigz rsync file jq unzip \
  libgl1 libglib2.0-0 libglx0 libegl1 libopengl0 libxkbcommon0 libfontconfig1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 \
  libxcb-shape0 libxcb-xkb1 libxkbcommon-x11-0 libdbus-1-3 >/dev/null

step uv
python3 -m pip install -q --break-system-packages --target $W/.uvpkg uv
ln -sf $W/.uvpkg/bin/uv $W/bin/uv
uv --version
uv python install 3.14

step villa $VILLA_COMMIT
if [ ! -d $W/villa/.git ]; then
  mkdir -p $W/villa && cd $W/villa && git init -q && git remote add origin https://github.com/ScrollPrize/villa.git
fi
cd $W/villa && git fetch -q --depth 1 origin $VILLA_COMMIT && git checkout -q FETCH_HEAD
test "$(git rev-parse HEAD)" = "$VILLA_COMMIT"

step venv
cd $W/villa/lasagna && python3 scripts/bootstrap_venv.py --venv $W/venv --backend cu130
uv pip install --python $W/venv/bin/python tifffile zarr numpy numcodecs opencv-python-headless safetensors huggingface_hub
$W/venv/bin/python -c "import torch, vesuvius.ink_detection.inference.infer as m; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0))"

step winner repo + checkpoints
[ -d $W/pherc343 ] || git clone -q --depth 1 https://github.com/Nieuwlaar/pherc343-first-letters.git $W/pherc343
(cd $W/pherc343 && git log --oneline -1)
chmod +x $W/pherc343/ink/scripts/*.sh $W/pherc343/ink/scripts/*.py
PY=$W/venv/bin/python bash $W/pherc343/ink/scripts/fetch_checkpoints.sh $W/pherc343/ink/models.tsv $W/ckpt

step reader-v2
$W/venv/bin/hf download domenicor046/reader-v2 reader-v2-step040000.pth --local-dir $W/ckpt
sha256sum $W/ckpt/reader-v2-step040000.pth | tee $W/p8/out/readerv2.sha256

step done
ls -la $W/ckpt

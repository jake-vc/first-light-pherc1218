#!/bin/bash
# aptlibs.sh - per-container system libraries for the VC3D AppImage renderer (the rest of the software is on the volume)
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq --no-install-recommends libgl1 libglib2.0-0 libglx0 libegl1 libopengl0 \
  libxkbcommon0 libfontconfig1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xkb1 libxkbcommon-x11-0 \
  libdbus-1-3 rsync >/dev/null && echo apt-ok

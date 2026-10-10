#!/usr/bin/env bash
set -euo pipefail
export DISPLAY=:99
Xvfb :99 -screen 0 800x600x24 -nolisten tcp > /tmp/three-room-xvfb.log 2>&1 &
sleep 1
/usr/games/scummvm --config=/work/verification/linux.ini --logfile=/work/verification/linux-scummvm.log last-shift > /work/verification/linux-stdout.log 2>&1 &
wait

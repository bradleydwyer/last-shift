#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
if [[ ! -d tools/lucasartsifier/.git ]]; then
  git clone https://github.com/katiahayati/lucasartsifier tools/lucasartsifier
  git -C tools/lucasartsifier checkout 45068351290ffd90e74186c69322d200fa60cafd
fi
if [[ ! -d tools/lucasartsifier/vendor/SCICompanion/.git ]]; then
  git clone https://github.com/icefallgames/SCICompanion tools/lucasartsifier/vendor/SCICompanion
  git -C tools/lucasartsifier/vendor/SCICompanion checkout f1a603b48b1aa7abf94f78574a8f69a653e2ca62
fi
if ! docker inspect three-room-sci-builder >/dev/null 2>&1; then
  docker run --name three-room-sci-builder -d -v "$project_dir:/work" -w /work ubuntu:24.04 sleep infinity
else
  docker start three-room-sci-builder >/dev/null
fi
docker exec three-room-sci-builder bash -c 'apt-get update -qq && apt-get install -y -qq cmake g++ make && cmake -S tools/lucasartsifier/tools/scicompile -B tools/lucasartsifier/tools/scicompile/build && cmake --build tools/lucasartsifier/tools/scicompile/build -j8'
mkdir -p tools/lucasartsifier/tools/scicompile/build/include
cp tools/lucasartsifier/vendor/SCICompanion/SCICompanion/Files/CompileInclude/* tools/lucasartsifier/tools/scicompile/build/include/
printf 'Compiler ready. Run python3 scripts/compile_game.py\n'

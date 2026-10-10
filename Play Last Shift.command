#!/bin/zsh
set -eu
project_dir="${0:A:h}"
runtime="/Applications/ScummVM.app/Contents/MacOS/scummvm"
if [[ ! -x "$runtime" ]]; then
  print 'Install ScummVM from https://www.scummvm.org/downloads/ and try again.'
  exit 1
fi
cd "$project_dir"
mkdir -p "$project_dir/saves"
# Run a fixed resource snapshot; rebuilding dist must not change an open game.
build_hash="$(cd "$project_dir/dist/Last Shift" && shasum -a 256 **/*(.) | shasum -a 256 | cut -c 1-16)"
game_snapshot="$project_dir/release/runtime-$build_hash"
if [[ ! -d "$game_snapshot" ]]; then
  mkdir -p "$project_dir/release"
  staging_snapshot="$(mktemp -d "$project_dir/release/staging.XXXXXX")"
  cp -R "$project_dir/dist/Last Shift/." "$staging_snapshot/"
  mv "$staging_snapshot" "$game_snapshot"
fi
config_file="$project_dir/last-shift-player.ini"
if [[ ! -f "$config_file" ]]; then
  cat > "$config_file" <<'EOF'
[scummvm]
savepath=saves
fullscreen=false
aspect_ratio=true
filtering=false
confirm_exit=false
music_volume=110
sfx_volume=160

[last-shift]
engineid=sci
gameid=sq5
description=Last Shift
path=dist/Last Shift
savepath=saves
platform=pc
language=en
updates_check=0
EOF
fi
exec "$runtime" --config="$config_file" --path="$game_snapshot" last-shift

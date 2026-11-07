#!/usr/bin/env bash
# Launches the retail game as a headless Bolt server under Wine.
#
# The game itself is the server (there is no separate server binary), so this
# just runs it headless with the patch installed. Provide your own game files.
#
# Usage: ./run-headless.sh /path/to/game [map]
set -euo pipefail

game_dir="${1:?usage: run-headless.sh /path/to/game [map]}"
map="${2:-}"

export WINEPREFIX="${WINEPREFIX:-$HOME/.sjg-wine}"
export WINEDLLOVERRIDES="winhttp=n,b"   # let BepInEx's doorstop winhttp load
export WINEDEBUG="${WINEDEBUG:--all}"

cd "$game_dir"

echo "==> Starting headless Soviet Jump Game server"
echo "    game:  $game_dir"
[[ -n "$map" ]] && echo "    map:   $map (via patched server config)"

# -batchmode => Headless.IsHeadless() == true (Packages.dll), so the runtime skips
# rendering and HeadlessServerManager takes over.
exec wine SovietJumpGame.exe -batchmode -nographics "$@"

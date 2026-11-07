# Launches the retail game as a headless Bolt server under Wine/Proton on Windows.
#
# (On Windows you normally just want to run the game normally and host from the
#  MATCHMAKING button; this is only for running a dedicated server.)
#
# Usage: powershell -ExecutionPolicy Bypass -File run-headless.ps1 -GameDir "C:\path\to\game"
param(
    [Parameter(Position = 0)][string]$GameDir
)

$ErrorActionPreference = "Stop"
if (-not $GameDir) { $GameDir = $env:SJG_GAME_DIR }
if (-not $GameDir) { Write-Error "usage: run-headless.ps1 -GameDir 'C:\path\to\game'"; exit 1 }

Write-Host "==> Starting headless Soviet Jump Game server"
Write-Host "    game: $GameDir"
Set-Location $GameDir

& ".\SovietJumpGame.exe" -batchmode -nographics

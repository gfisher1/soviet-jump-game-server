# Runs the Soviet Jump Game backend on Windows.
#
#   .\run.ps1
#   $env:SJG_STATIC_SERVERS = "10.0.0.5:42010:My Server"; .\run.ps1
param(
    [string]$HostAddr = "0.0.0.0",
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$venv = Join-Path $here ".venv"
$py = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "==> Creating virtualenv ($venv)"
    python -m venv $venv
    & (Join-Path $venv "Scripts\pip.exe") install --quiet --upgrade pip
    & (Join-Path $venv "Scripts\pip.exe") install --quiet -r requirements.txt
}

Write-Host "==> Soviet Jump Game backend on http://${HostAddr}:$Port"
& $py -m uvicorn app.main:app --host $HostAddr --port $Port

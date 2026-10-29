# Starts the SIERRAH React frontend (installs packages on first run).
# Usage (from the repo root):  .\scripts\start-frontend.ps1
$ErrorActionPreference = 'Stop'
$frontend = Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend'
Set-Location $frontend

if (-not (Test-Path 'node_modules')) {
    Write-Host 'Installing npm packages...' -ForegroundColor Cyan
    npm install
}
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }

Write-Host 'SIERRAH app  ->  http://localhost:5173' -ForegroundColor Green
npm run dev

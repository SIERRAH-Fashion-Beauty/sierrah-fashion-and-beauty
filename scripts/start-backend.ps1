# Starts the SIERRAH FastAPI backend (creates the virtual environment on first run).
# Usage (from the repo root):  .\scripts\start-backend.ps1
$ErrorActionPreference = 'Stop'
$backend = Join-Path (Split-Path -Parent $PSScriptRoot) 'backend'
Set-Location $backend

if (-not (Test-Path '.venv')) {
    Write-Host 'Creating Python virtual environment...' -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) { py -m venv .venv } else { python -m venv .venv }
}

$python = Join-Path $backend '.venv\Scripts\python.exe'
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -r requirements.txt

if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }

Write-Host 'SIERRAH API  ->  http://127.0.0.1:8000  (docs: /docs)' -ForegroundColor Green
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

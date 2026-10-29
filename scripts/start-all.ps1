# Opens the backend and the frontend in two separate PowerShell windows.
# Usage (from the repo root):  .\scripts\start-all.ps1
$scripts = $PSScriptRoot
Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $scripts 'start-backend.ps1')
Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $scripts 'start-frontend.ps1')
Write-Host 'Started. Open http://localhost:5173 once both windows say they are ready.' -ForegroundColor Green

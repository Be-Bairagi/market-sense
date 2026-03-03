# start-project.ps1
param (
    [switch]$Agy
)

$ErrorActionPreference = "Continue"

Write-Host "=========================================" -ForegroundColor DarkGray
Write-Host "Starting MarketSense Development Environment..." -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor DarkGray

$backendDir = Resolve-Path ".\MarketSense-backend"
$frontendDir = Resolve-Path ".\Marketsense-frontend"

# Use cmd /k so the windows stay open even if there is an error, so you can read the logs!
$backendCmd = ".\venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$frontendCmd = ".\venv_311\Scripts\activate.bat && streamlit run app.py"

try {
    # Attempt to use Windows Terminal (wt.exe) to create a beautiful split-pane dashboard
    # The first pane runs backend, the second pane (-V for vertical split) runs frontend
    $wtArgs = "-d `"$backendDir`" cmd.exe /k `"$backendCmd`" `; split-pane -V -d `"$frontendDir`" cmd.exe /k `"$frontendCmd`""
    
    Write-Host "Launching Windows Terminal dashboard..." -ForegroundColor Cyan
    Start-Process wt.exe -ArgumentList $wtArgs -ErrorAction Stop
    
    Write-Host "Successfully launched seamlessly in Windows Terminal!" -ForegroundColor Green
} catch {
    # Fallback to popping two standard PowerShell windows if Windows Terminal is not installed
    Write-Host "Windows Terminal not found. Falling back to separate windows..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd MarketSense-backend; .\venv\Scripts\Activate.ps1; invoke run`""
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd Marketsense-frontend; .\venv_311\Scripts\Activate.ps1; invoke run`""
}

Write-Host "`n"
for ($i = 7; $i -gt 0; $i--) {
    Write-Host "`rClosing this launcher in $i seconds... " -NoNewline -ForegroundColor DarkGray
    Start-Sleep -Seconds 1
}

# Stop the current powershell process to close the terminal automatically
Stop-Process -Id $PID

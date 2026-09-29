$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:BIS_EMBEDDINGS = "off"
Set-Location -Path "$PSScriptRoot\bis_engine"
Write-Host "Starting BIS Standards Recommendation Engine on http://localhost:8002 ..." -ForegroundColor Cyan
$pythonCmd = if (Get-Command "py" -ErrorAction SilentlyContinue) { "py -3.13" } elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") { "& '$env:LOCALAPPDATA\Programs\Python\Python313\python.exe'" } else { "python" }
Invoke-Expression "$pythonCmd -m uvicorn main:app --reload --port 8002"

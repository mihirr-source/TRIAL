@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set BIS_EMBEDDINGS=off
cd /d "%~dp0bis_engine"
echo Starting PARAKH Standards Recommendation Engine on http://localhost:8002 ...
py -3.13 -m uvicorn main:app --reload --port 8002 2>nul || "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" -m uvicorn main:app --reload --port 8002 2>nul || python -m uvicorn main:app --reload --port 8002
pause

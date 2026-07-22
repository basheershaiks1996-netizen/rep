@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
start "" http://127.0.0.1:8000
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
pause

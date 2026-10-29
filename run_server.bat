@echo off
cd /d "%~dp0"
echo Starting HER Biomedical Image Analysis server...
echo Dashboard: http://127.0.0.1:8000
echo MRI studio: http://127.0.0.1:8000/image-analysis
echo API documentation: http://127.0.0.1:8000/docs
py -3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause

@echo off
cd /d "%~dp0"
echo Starting HER Biomedical Image Analysis server...
echo Open http://127.0.0.1:8000/image-analysis in your browser
py -3 -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

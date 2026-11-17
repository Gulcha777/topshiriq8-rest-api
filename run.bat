@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -q -r requirements.txt
python -m app.seed
echo Swagger UI: http://localhost:8000/docs
uvicorn app.main:app --port 8000

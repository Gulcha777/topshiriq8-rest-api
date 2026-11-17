#!/usr/bin/env bash
# Ishga tushirish: ./run.sh   (virtual muhit, o'rnatish, seed, server)
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
python -m app.seed
echo "Swagger UI: http://localhost:8000/docs"
exec uvicorn app.main:app --port 8000

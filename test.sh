#!/usr/bin/env bash
# Testlarni ishga tushirish: ./test.sh
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
python -m pytest -v

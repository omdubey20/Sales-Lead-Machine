#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting Sales Lead Machine Frontend Platform"
echo " Landing Page:  http://localhost:8000"
echo " API Health:    http://localhost:8000/api/health"
echo " Docs:          http://localhost:8000/docs"
echo "=========================================================="

python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

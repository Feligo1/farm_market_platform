#!/usr/bin/env bash
set -e

if [ -f "backend/wsgi.py" ]; then
  cd backend
fi

exec gunicorn wsgi:app --bind "0.0.0.0:${PORT}" --workers 1 --timeout 120

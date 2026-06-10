#!/usr/bin/env bash
set -e

exec gunicorn wsgi:app --bind "0.0.0.0:${PORT}" --workers 1 --timeout 120

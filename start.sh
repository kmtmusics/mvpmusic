#!/usr/bin/env bash
set -e
python3 create_db.py || true
python3 upgrade_db.py || true
python3 create_users.py || true
exec gunicorn -w 2 -b 0.0.0.0:$PORT app:app

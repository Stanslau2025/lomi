#!/usr/bin/env bash
set -o errexit

python manage.py check --deploy
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py ensure_admin

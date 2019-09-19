#!/bin/sh

python3 manage.py migrate --no-input
python manage.py sync_translation_fields --no-input
python manage.py buildstatic --no-input
gunicorn --bind 0.0.0.0:8080 -w $WORKER_COUNT linkedevents.wsgi
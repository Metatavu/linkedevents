#!/bin/sh

python3 manage.py migrate
python3 manage.py sync_translation_fields
gunicorn --bind 0.0.0.0:8080 -w $WORKER_COUNT linkedevents.wsgi
#!/bin/sh

python3 manage.py migrate
python3 manage.py collectstatic --no-input
service nginx start

gunicorn --bind 0.0.0.0:8080 -w $WORKER_COUNT linkedevents.wsgi
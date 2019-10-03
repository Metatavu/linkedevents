#!/bin/sh

python3 manage.py migrate
python3 manage.py sync_translation_fields

python3 manage.py runserver

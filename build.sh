#!/usr/bin/env bash
# exit on error
set -o errexit

rm -rf poetry.lock
poetry lock --no-update
poetry install

pwd
ls

python manage.py collectstatic --no-input
python manage.py migrate
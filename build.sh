#!/usr/bin/env bash
# exit on error
set -o errexit

rm -rf poetry.lock
poetry lock --no-update
poetry install

python manage.py collectstatic
python manage.py migrate
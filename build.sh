#!/usr/bin/env bash
# exit on error
set -o errexit

rm -rf poetry.lock
poetry lock --no-update
poetry install

python -m spacy download en_core_web_sm

python manage.py collectstatic --noinput
python manage.py migrate
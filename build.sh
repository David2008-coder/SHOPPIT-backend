#!/usr/bin/env bash
# exit on error
set -o errexit

# Step into the folder containing your code and requirements
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
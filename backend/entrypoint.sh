#!/bin/bash
set -e

echo 'Waiting for database...'
python - << END
import sys
import psycopg2
import time
import os

db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_host = os.environ['DB_HOST']
db_port = os.environ['DB_PORT']

for i in range(30):
    try:
        psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        print('Database available!')
        sys.exit(0)
    except psycopg2.OperationalError:
        print('Database unavailable, waiting 1s...')
        time.sleep(1)

sys.exit(1)
END

echo 'Applying database migrations...'
python manage.py makemigrations
python manage.py migrate

echo 'Starting server...'
exec "$@"

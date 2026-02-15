
#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Starting server..."
exec "$@"

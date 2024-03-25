#!/bin/sh

if [ -z ${LOG_LEVEL} ]; then
  export LOG_LEVEL="info"
fi

if [ -z ${HTTP_PORT} ]; then
  export HTTP_PORT=":8000"
fi
if [ -z ${HTTP_WORKERS} ]; then
  export HTTP_WORKERS=2
fi

# wait for MySQL
echo "============================="
echo "Waiting for MySQL..."
echo "============================="

while ! nc -z "${MYSQL_HOST}" "${MYSQL_PORT}"; do
  sleep 0.1
done

export DATABASE_URL="mysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}"

echo "========================================="
echo "MySQL is available"
echo "========================================="

echo "============================="
echo "Initializing DB..."
echo "============================="
python manage.py migrate
python manage.py collectstatic --noinput
status=$?
if [ $status -eq 0 ]; then
  echo "============================="
  echo "Loading fixtures..."
  echo "============================="
  python manage.py loaddata fixtures.json

  echo "============================="
  echo "Starting Gunicorn..."
  echo "============================="

  # Start Celery worker in the background
  celery -A core worker -l INFO --detach

  gunicorn --workers $HTTP_WORKERS \
           --worker-class=gthread \
           --reload core.wsgi \
           -b $HTTP_PORT \
           --timeout 120 \
           --log-level $LOG_LEVEL
else
  echo "Error initializing DB, exiting..."
fi

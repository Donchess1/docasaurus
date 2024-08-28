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

# wait for postgres
echo "============================="
echo "Waiting for postgres..."
echo "============================="

# while ! nc -z db ${POSTGRES_PORT}; do
#   sleep 0.1
# done

if [ -z "${POSTGRES_USER}" ]; then
    base_postgres_image_default_user='postgres'
    export POSTGRES_USER="${base_postgres_image_default_user}"
fi

export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

wait_for_postgres() {
    suggest_unrecoverable_after=30
    start=$(date +%s)
    while true; do
        # Try to connect to the target database
        if PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" -d "${POSTGRES_DB}" -c '\q'; then
            echo "========================================="
            echo "PostgreSQL is available"
            echo "========================================="
            break
        fi
        echo "=============================================="
        echo "Waiting for PostgreSQL to become available..."
        echo "=============================================="
        if [ $(($(date +%s) - start)) -gt "${suggest_unrecoverable_after}" ]; then
            echo "============================================================================"
            echo "This is taking longer than expected. It may indicate an unrecoverable error."
            echo "============================================================================"
            break
        fi

        sleep 1
    done
}

wait_for_postgres
echo "============================="
echo "Initializing DB..."
echo "============================="
echo "Current directory structure:"
ls -R /app

echo "============================="
echo "Running Django commands..."
echo "============================="
cd /app/src  # Change to the src directory

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

web: gunicorn agricloud.wsgi --preload --timeout 30 --log-file -
worker: celery -A agricloud worker -l info
web: gunicorn mascotas_serv.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
worker: celery -A mascotas_serv worker --loglevel=info
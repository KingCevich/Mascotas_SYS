"""
celery.py — Configuración de Celery para mascotas_serv
=======================================================
Para correr el worker en local:
    celery -A mascotas_serv worker --loglevel=info

Requiere Redis corriendo:
    redis-server        (Linux/Mac)
    docker run -p 6379:6379 redis  (con Docker)
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mascotas_serv.settings")

app = Celery("mascotas_serv")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
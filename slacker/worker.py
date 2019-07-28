import os
from celery import Celery

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379'),
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

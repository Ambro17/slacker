import os
from celery import Celery
from loguru import logger

CELERY_BROKER_URL = os.environ.get('CELERY_BACKEND', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER', 'redis://localhost:6379')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
logger.debug(f"Message broker: {CELERY_BROKER_URL}")

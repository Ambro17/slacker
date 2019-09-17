from celery import Celery
from loguru import logger

from slacker.app_config import CELERY_BROKER, CELERY_BACKEND

celery = Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)
logger.debug(f"Message broker: {CELERY_BROKER}")

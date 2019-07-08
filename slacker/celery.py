import os

from celery import Celery

celery = Celery('slacker',
                broker=os.getenv('CELERY_BROKER'),
                backend=os.getenv('CELERY_BACKEND'))
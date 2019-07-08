"""
Celery worker that runs scheduled tasks from main app. It provides app context to each task.

References:
    https://medium.com/@frassetto.stefano/flask-celery-howto-d106958a15fe
    https://blog.miguelgrinberg.com/post/celery-and-the-flask-application-factory-pattern
"""
from slacker import create_app
from slacker.celery import celery
from slacker.celery_utils import init_celery

app = create_app()

init_celery(celery, app)

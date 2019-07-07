from celery import Celery

def make_celery(app_name=__name__):
    # Configure celery instance not yet bound to an app
    broker = 'amqp://localhost'
    return Celery(app_name, broker=broker)

# Unbound Celery instance accesible to all modules
celery = make_celery()

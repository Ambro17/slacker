from celery import Celery

def make_celery(app_name='slacker'):
    # Configure celery instance not yet bound to an app
    broker = 'amqp://localhost'
    backend = 'rpc://'
    return Celery(app_name, broker=broker, backend=backend)

# Unbound Celery instance accesible to all modules
celery = make_celery()

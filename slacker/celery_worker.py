"""
Celery worker that runs scheduled tasks from main app. It provides app context to each task.

References:
    https://medium.com/@frassetto.stefano/flask-celery-howto-d106958a15fe
    https://blog.miguelgrinberg.com/post/celery-and-the-flask-application-factory-pattern
"""
from slacker import create_app
from slacker.celery import celery


def init_celery(celery, app):
    """Bind celery instance to app in order to provide context

    Side-effect:
        celery will add an aplication context to each task.
    """
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Provide app context to all celery tasks"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


app = create_app()
init_celery(celery, app)

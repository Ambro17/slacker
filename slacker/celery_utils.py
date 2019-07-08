def init_celery(celery, app):
    """Bind celery instance to app in order to provide context

    Side-effect:
        Now importing celery will add an aplication context to each task.
    """
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Provide app context to all celery tasks"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

from time import sleep

from slacker import celery


@celery.task
def add_together(a, b):
    sleep(5)
    return 'hola'


"""
This module has functions that call the celery tasks on the remote worker
"""
from slacker.worker import celery


def send_ephemeral_message(message, channel, user, **kwargs):
    return celery.send_task('tasks.send_ephemeral_message', args=(message, channel, user))

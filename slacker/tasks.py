from flask import current_app

from slacker.celery import celery


@celery.task
def send_message_async(message):
    r = current_app.slack_cli.api_call('chat.postMessage', text=message, channel='#general')
    return r['ok'], r.get('error')


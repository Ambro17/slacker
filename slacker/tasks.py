from flask import current_app

from slacker.celery import celery


@celery.task
def send_message_async(message, channel='#general', **kwargs):
    r = current_app.slack_cli.api_call('chat.postMessage', text=message, channel=channel, **kwargs)
    return r['ok'], r.get('error')


@celery.task
def send_ephemeral_message(message, channel, user, **kwargs):
    r = current_app.slack_cli.api_call(
        'chat.postEphemeral',
         text=message,
         channel=channel,
         user=user,
         **kwargs
    )
    return r['ok'], r.get('error')


@celery.task
def slack_api(method, **kwargs):
    r = current_app.slack_cli.api_call(method, **kwargs)
    return r['ok'], r.get('error')

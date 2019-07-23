import os
import time
from celery import Celery
from dotenv import load_dotenv
from slack import WebClient

load_dotenv()
CELERY_BROKER_URL = os.environ['CELERY_BROKER']
CELERY_RESULT_BACKEND = os.environ['CELERY_BACKEND']

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
Slack = WebClient(os.environ["BOT_TOKEN"])


@celery.task
def delayed_sum(x: int) -> int:
    time.sleep(2)
    return x + 10


@celery.task
def send_message(message, channel='#general', **kwargs):
    r = Slack.chat_postMessage(channel=channel, text=message, **kwargs)
    return r['ok'], r.get('error')


@celery.task
def send_ephemeral_message(message, channel, user, **kwargs):
    r = Slack.chat_postEphemeral(channel=channel, user=user, text=message, **kwargs)
    return r['ok'], r.get('error')


# OVI Tasks
@celery.task
def start_vms(cli, vm_names):
    stdout = cli.start_many(vm_names)
#    send_ephemeral_message(stdout, channel, user)

import logging
import os
import time
from typing import List

from celery import Celery
from dotenv import load_dotenv
from slack import WebClient

load_dotenv()

logger = logging.getLogger(__name__)

CELERY_BROKER_URL = os.environ['CELERY_BROKER']
CELERY_RESULT_BACKEND = os.environ['CELERY_BACKEND']

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
Slack = WebClient(os.environ["BOT_TOKEN"])


class SlackTask(celery.Task):
    """Slack task wrapper to notify user of what happened with the task"""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        try:
            success, error_msg = retval
        except ValueError:
            logger.error(f'{retval} {args} {kwargs} {einfo} {task_id}')
            return

        if not success:
            Slack.chat_postEphemeral(
                channel='#errors',
                user='@Ambro',
                text=f'{task_id}\n{error_msg}\n{args}\n{kwargs}\n{einfo}',
                **kwargs
            )
            # Notify user on private message

class ResponseNotOK(Exception):
    """Slack api request was not successfull"""


@celery.task(base=SlackTask)
def send_message(message: str, channel: str = '#general', **kwargs) -> (bool, str):
    r = Slack.chat_postMessage(channel=channel, text=message, **kwargs)
    if not r['ok']:
        raise ResponseNotOK(f"Slack api request error:\n{r.get('error')}")

    return r['ok'], r.get('error', '')


@celery.task(base=SlackTask)
def send_ephemeral_message(message: str, channel: str, user: str, **kwargs) -> (bool, str):
    r = Slack.chat_postEphemeral(channel=channel, user=user, text=message, **kwargs)
    if not r['ok']:
        raise ResponseNotOK(f"Slack api request error:\n{r.get('error')}")

    return r['ok'], r.get('error', '')


@celery.task(base=SlackTask)
def send_message_with_blocks(blocks: List[dict], channel: str, **kwargs) -> (bool, str):
    r = Slack.chat_postMessage(blocks=blocks, channel=channel, **kwargs)
    if not r['ok']:
        raise ResponseNotOK(f"Slack api request error:\n{r.get('error')}")

    return r['ok'], r.get('error', '')

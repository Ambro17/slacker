import logging
import os
from typing import List

import celery as _celery
from celery import Celery
from dotenv import load_dotenv
from slack import WebClient

load_dotenv()

logger = logging.getLogger(__name__)

CELERY_BROKER_URL = os.environ['REDIS_URL']
CELERY_RESULT_BACKEND = os.environ['REDIS_URL']

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
Slack = WebClient(os.environ["BOT_TOKEN"])


class SlackTask(_celery.Task):
    """Slack task wrapper to notify user of what happened with the task"""
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        try:
            success, error_msg = retval
        except Exception as e:
            error_details = f'Unknown exception. {retval} {args} {kwargs} {einfo} {task_id}. Exception: {repr(e)}'
            Slack.chat_postEphemeral(
                channel=os.environ['ERRORS_CHANNEL'],
                user=os.environ['BOT_FATHER'],
                text=error_details,
            )
        else:
            if not success:
                error_details = f'Slack request error.\n{task_id}\n{error_msg}\n{args}\n{kwargs}\nException:{einfo}'
                Slack.chat_postEphemeral(
                    channel=os.environ['ERRORS_CHANNEL'],
                    user=os.environ['BOT_FATHER'],
                    text=error_details,
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

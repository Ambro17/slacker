import logging
import os
from typing import List

from dotenv import load_dotenv
import celery as _celery
from awsadm.ovicli import OviCli

from slack import WebClient

load_dotenv()

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ['BOT_TOKEN']
OVIBOT = os.environ["OVIBOT"]
ERRORS_CHANNEL = os.environ['ERRORS_CHANNEL']
BOT_FATHER = os.environ['BOT_FATHER']
CELERY_BROKER_URL = os.environ['CELERY_BACKEND']
CELERY_RESULT_BACKEND = os.environ['CELERY_BROKER']


celery = _celery.Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
Slack = WebClient(BOT_TOKEN)
OviBot = WebClient(OVIBOT)


class ResponseNotOK(Exception):
    """Slack api request was not successfull"""


def notify_error_to_admin(error_msg):
    mono_error = f'```{error_msg}```'
    r = OviBot.chat_postEphemeral(channel=ERRORS_CHANNEL,
                                  user=BOT_FATHER,
                                  text=mono_error)
    assert r['ok'], f"Admin not notified: {r['error']}"


# Slack tasks
class SlackTask(_celery.Task):
    """Slack task wrapper to notify admin if a task failed"""
    def on_success(self, return_value, task_id, args, kwargs):
        # Notify admin if task did not respect the task contract or if request failed
        try:
            success, error_msg = return_value
        except ValueError:
            error_details = f"Slack Task returned {repr(return_value)} instead of tuple. {task_id} {args} {kwargs}."
            notify_error_to_admin(error_details)
            return

        if not success:
            error_details = f'Invalid Slack request: \n{error_msg}'
            notify_error_to_admin(error_details)

        # If slack request was successful do nothing.

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        error_details = (
            f'Exception handling slack task.\n'
            f'Task id: {task_id}\n'
            f'Details: {exc}\n'
            f'Args: {args}\n'
            f'Kwargs: {kwargs}\n'
            f'Exception info:\n{einfo}'
        )
        notify_error_to_admin(error_details)


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


@celery.task(base=SlackTask)
def upload_file(file, channel, name, header, **kwargs) -> (bool, str):
    r = OviBot.files_upload(file=file, channels=channel, filename=name, initial_comment=header, **kwargs)
    if not r['ok']:
        raise ResponseNotOK(f"Slack api request error:\n{r.get('error')}")

    return r['ok'], r.get('error', '')


# Ovi Tasks
class OviTask(_celery.Task):
    """Task to wrap ovicli calls. Return output unmodified. Notifying failure"""
    def on_success(self, ovi_return_value, task_id, args, kwargs):
        # Send task output to user
        Slack.chat_postEphemeral(
            channel=kwargs['channel'],
            user=kwargs['user'],
            text=ovi_return_value,
        )

    def on_failure(self, task_exception, task_id, args, kwargs, einfo):
        # Notify admin and user of failure (with different level of detail)
        error_details = f'Exception: {task_exception}.\nDetails: {task_id}\n{args}\n{kwargs}\n{einfo}'
        notify_error_to_admin(error_details)
        Slack.chat_postEphemeral(
            channel=kwargs['channel'],
            user=kwargs['user'],
            text='Task failed 😢',
        )


@celery.task(base=OviTask)
def start_vms(vms: dict, target_vms: List[str], ovi_user: str, token: str, **kwargs) -> str:
    cli = OviCli(vms, ovi_user, token)
    stdout = cli.start_many(target_vms)
    return stdout


@celery.task(base=OviTask)
def stop_vms(vms: dict, target_vms: List[str], ovi_user: str, token: str, **kwargs) -> str:
    cli = OviCli(vms, ovi_user, token)
    stdout = cli.stop_many(target_vms)
    return stdout


@celery.task(base=OviTask)
def list_vms(vms: dict, timeout, ovi_user: str, token: str, **kwargs) -> str:
    cli = OviCli(vms, ovi_user, token)
    stdout = cli.list_vms_remote(timeout)
    resp = cli.format_vms_remote(stdout, monospace=True)
    return resp


@celery.task(base=OviTask)
def redeploy_vm(vms: dict, target_vm: str, snapshot_id, ovi_user: str, token: str, **kwargs) -> str:
    cli = OviCli(vms, ovi_user, token)
    out = cli.redeploy(target_vm, snapshot_id)
    resp = cli.format_redeploy(out)
    return resp


@celery.task(base=OviTask)
def get_redeploy_snapshots(ovi_user, token, **kwargs):
    cli = OviCli({}, ovi_user, token)
    out = cli.snapshots()
    return cli.format_snapshots(out, monospace=True)


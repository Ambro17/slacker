import logging
import traceback
from functools import partial
from typing import List

from flask import request, make_response

from slacker.database import db
from slacker.exceptions import SlackerException
from slacker.models import VM, VMOwnership
from slacker.models.user import get_or_create_user
from slacker.slack_cli import Slack, OviBot
from slacker.tasks_proxy import (
    start_vms_task,
    stop_vms_task,
    list_vms_task,
    redeploy_vm_task,
    get_snapshots_task,
    send_ephemeral_message_async,
)
from slacker.utils import BaseBlueprint, reply, command_response, OK

START_USAGE = "Usage: `/ovi_start <vm_name> [<vm_name> ...]`"
STOP_USAGE = "Usage: `/ovi_stop <vm_name> [<vm_name> ...]`"
INFO_USAGE = "Usage: `/ovi_info <vm_name> [<vm_name> ...]`"
LIST_VMS_USAGE = "Usage: `/ovi_list_vms`"
REDEPLOY_USAGE = "Usage: `/ovi_redeploy konsole <snapshot_id>`\nCheck `/snapshots` for available options"

WRONG_ALIAS_MESSAGE = "You don't have a VM under alias '{alias}'"

bp = BaseBlueprint('ovi', __name__, url_prefix='/ovi')

logger = logging.getLogger(__name__)

command_response = partial(command_response, bot_name='OviBot')


class OviException(SlackerException):
    """Wrong usage of ovi api"""


class DuplicateAliasException(SlackerException):
    """Raised if user wants to save a vm under an alias that already maps to one oh her/his vms"""


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'text': 'Ovi Management',
        'commands': ['start', 'stop', 'info', 'redeploy', 'snapshots']
    })


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Open Register VMs dialog. interactivity blueprint will handle form input"""
    logger.debug(request.form)
    user_id = request.form['user_id']
    logger.info("User %s called /register", user_id)
    dialog = {
        "callback_id": "aws_callback",
        "title": "Register your VMs",
        "state": f"{user_id}",
        "submit_label": "Save",
        "elements": [
            {
                "type": "text",
                "label": "API User",
                "name": "user"
            },
            {
                "type": "text",
                "label": "API Token",
                "name": "token"
            },
            {
                "label": "VMs information",
                "type": "textarea",
                "hint": "Put your vm alias and ids. One line for each vm",
                "placeholder": "console=5kyq3bdcnl6sbnsv9t6q\nsensor=wwt6adcuow78sj9hj8hi",
                "name": "vms_info",
            }
        ]
    }
    logger.debug("Opening VMs dialog")
    OviBot.dialog_open(
        trigger_id=request.form['trigger_id'],
        dialog=dialog
    )
    logger.info("Dialog shown")

    return make_response('', 200)


def handle_aws_submission(action):
    """Handle a form submission action and respond accordingly with OK or form errors"""
    user_id = action['user']['id']

    form = action['submission']
    name = form['user']
    token = form['token']
    raw_vms = form['vms_info']

    logger.debug(f"Parsing VMs input:\n{raw_vms}")
    vms_info = load_vms_info(raw_vms)
    logger.debug(f"User vms:\n{vms_info}")

    if vms_info is None:
        resp = {
            'errors': [{
                'name': 'vms_info',
                'error': 'Invalid VMs format. Check the placeholder to see the correct format'
            }]
        }
    else:
        logger.debug(f"Get or create user. Id '{user_id}'")
        user = get_or_create_user(Slack, user_id)
        logger.debug("User: %s", user.real_name)

        try:
            logger.debug(f"Saving VMs of '{user.real_name}'..")
            save_user_vms(user, name, token, vms_info)
            logger.debug("VMs saved")
        except Exception as e:
            logger.info(f"Something went bad while saving vms, {repr(e)}")
            resp = {
                'errors': [{
                    'name': 'vms_info',
                    'error': f'{e.__class__.__name__}: {str(e)}'
                }]
            }
        else:
            vms = '\n'.join(f'`{vm}: {hash}`' for vm, hash in vms_info.items())
            msg = f':check: VMs saved successfully.\nAPI User: `{name}`\nVMs:\n{vms}'

            promise = send_ephemeral_message_async(msg, channel=action['channel']['id'], user=user_id)
            logger.debug("Task %s sent to notify user of aws submission success." % promise)

            resp = OK

    return resp


def load_vms_info(vms):
    """Load vms ids from text separated by newlines and `=`

    Example:
        console=1234
        sensor=12356
    Output:
        {
            'console': 1234,
            'sensor': 12356
        }
    """
    vms_info = {}
    for vm in vms.splitlines():
        try:
            vm_name, vmid = vm.split('=')
            vms_info.update({f'{vm_name.strip()}': f'{vmid.strip()}'})
        except Exception:
            logger.info("Bad vsm info format. '%r'" % vms)
            return None

    return vms_info


def save_user_vms(user, ovi_name, ovi_token, new_user_vms):
    existing_user_vms = {vm.alias for vm in user.owned_vms}
    repeated_alias = next((alias for alias in new_user_vms if alias in existing_user_vms), False)
    if repeated_alias:
        raise DuplicateAliasException(
            f"'{repeated_alias}' is already mapped to a VM. Change it and retry."
        )

    for alias, vm_id in new_user_vms.items():
        logger.debug(f"Atttempting to add VM with alias={alias} and id={vm_id}")
        vm = VM.query.get(vm_id)
        if not vm:
            vm = VM(id=vm_id)

        owned_vm = VMOwnership.query.filter_by(alias=alias, user_id=user.id, vm_id=vm_id).one_or_none()
        if not owned_vm:
            logger.debug("Creating vm ownership")
            owned_vm = VMOwnership(vm=vm, user=user, alias=alias)
            db.session.add(owned_vm)
        else:
            logger.debug(f"Ignoring {str(owned_vm)} because it's already on database.")

    user.ovi_name = ovi_name
    user.ovi_token = ovi_token

    db.session.commit()


@bp.route('/start', methods=('GET', 'POST'))
def start():
    """Start a vm owned by a user"""
    target_vms_raw = request.form.get('text')
    user_id = request.form['user_id']
    channel = request.form['channel_id']
    user = get_or_create_user(Slack, user_id)
    try:
        owned_vms, target_vms = _validate_ovi_request(target_vms_raw, user.owned_vms, usage_help=START_USAGE)
    except OviException as error:
        return command_response(str(error))

    # Send async task
    task_id = start_vms_task(owned_vms, target_vms, user.ovi_name, user.ovi_token,
                             user=user_id,
                             channel=channel)
    logger.debug(f"Task '{task_id}' sent to start vms of user {user.real_name}. VMs: {target_vms}")

    return command_response('Start VMs task sent :check:')


def _validate_ovi_request(target_vms: str,
                          user_vms: List,
                          usage_help: str) -> (dict, List[str]):
    """
    Validates:
        - That user specified the required parameters (target vms)
        - That the user has at least one saved vm to manage
        - That all target vms are valid aliases of user-owned vms
    """

    if not target_vms:
        raise OviException(usage_help)  # User did not specify target vm to start/stop
    if not user_vms:
        raise OviException("You don't own any vm yet. Add them with `/register`")

    # Split vm names into list of strings
    targeted_vms = target_vms.split()
    owned_vms = {vm.alias: vm.vm_id for vm in user_vms}

    missing_alias = next((alias for alias in targeted_vms if alias not in owned_vms), False)
    if missing_alias:
        raise OviException(WRONG_ALIAS_MESSAGE.format(alias=missing_alias))

    return owned_vms, targeted_vms


@bp.route('/stop', methods=('GET', 'POST'))
def stop():
    target_vms = request.form.get('text')
    user_id = request.form['user_id']
    channel = request.form['channel_id']
    user = get_or_create_user(Slack, user_id)
    try:
        user_vms, target_vms = _validate_ovi_request(target_vms, user.owned_vms, usage_help=STOP_USAGE)
    except OviException as error:
        return command_response(str(error))

    # Send async task
    task_id = stop_vms_task(user_vms, target_vms, user.ovi_name, user.ovi_token,
                            user=user_id,
                            channel=channel)
    logger.debug(f"Task '{task_id}' sent to stop '{target_vms}' of user {user.real_name}.")

    return command_response('Stop VMs task sent :check:')


@bp.route('/list_vms', methods=('GET', 'POST'))
def list_vms():
    """List VMs owned by the user on oviup"""
    timeout = request.form.get('text') or 30
    user_id = request.form['user_id']
    channel_id = request.form['channel_id']
    logger.info("The timeout was: %s", timeout)
    user = get_or_create_user(Slack, user_id)

    # No need to get user owned vms nor to receive alias from user
    task_id = list_vms_task({}, timeout, user.ovi_name, user.ovi_token,
                            user=user_id,
                            channel=channel_id)
    logger.debug(f"Task '{task_id}' sent to show remote vms of user {user.real_name}.")

    return command_response('List VMs task sent :check: (This may take a while..)')


@bp.route('/redeploy', methods=('GET', 'POST'))
def redeploy():
    target_vms = request.form.get('text')
    if not target_vms:
        return command_response('Bad usage. `/ovi_redeploy konsole 17`')

    try:
        alias, snapshot_id = _validate_command_syntax(target_vms)
    except OviException as e:
        return command_response(str(e))

    user_id = request.form['user_id']
    channel_id = request.form['channel_id']
    user = get_or_create_user(Slack, user_id)
    try:
        user_vms, _ = _validate_ovi_request(alias, user.owned_vms, usage_help=REDEPLOY_USAGE)
    except OviException as error:
        return command_response(str(error))

    # Send async task
    task_id = redeploy_vm_task(user_vms, alias, snapshot_id,  user.ovi_name, user.ovi_token,
                               user=user_id,
                               channel=channel_id)

    logger.debug(f"Task '{task_id}' sent to redeploy '{alias}'' of user {user.real_name} to image {snapshot_id}")

    return command_response('Redeploy task sent :check:')


def _validate_command_syntax(text: str):
    """Syntax: <vm>: <digit>"""
    try:
        text = text.strip()
        alias, snapshot_id = text.split()
    except ValueError:
        raise OviException('Invalid command usage. i.e: `/redeploy konsole: 10`')

    alias = alias.strip()
    snapshot_id = snapshot_id.strip()
    if not snapshot_id.isdigit():
        raise OviException(f'Invalid command usage. Snapshot must be a digit, not {repr(snapshot_id)}')
    if len(alias.split()) > 1:
        raise OviException(f'Invalid command usage. You must specify only one vm alias. Got {alias}')

    return alias, snapshot_id


@bp.route('/snapshots', methods=('GET', 'POST'))
def snapshots():
    user_id = request.form['user_id']
    user = get_or_create_user(Slack, user_id)

    # Send async task
    task_id = get_snapshots_task(user.ovi_name, user.ovi_token, user=user_id, channel=request.form['channel_id'])
    logger.debug(f"Task '{task_id}' sent to show available redeploy snapshots to {user.real_name}")

    return command_response('Snapshots task sent :check:')


@bp.route('/my_vms', methods=('GET', 'POST'))
def user_owned_vms():
    """List VMs that were added by the user into slack and can be controlled through the bot"""
    user_id = request.form['user_id']
    user = get_or_create_user(Slack, user_id)

    user_vms = user.owned_vms
    if not user_vms:
        msg = f"Hey {user.first_name}, you don't own any vm yet. Start with `/register`"
    else:
        name = user.ovi_name or 'No name set'
        msg = f'Ovi username: `{name}`\n'
        msg += '\n'.join(f"`{vm.alias}: {vm.vm_id}`" for vm in user_vms)

    return command_response(msg)


@bp.route('/unregister', methods=('GET', 'POST'))
def delete_my_vms():
    """Delete VMs that were added by the user into slack and can be controlled through the bot"""
    user_id = request.form['user_id']
    user = get_or_create_user(Slack, user_id)

    user_vms = user.owned_vms
    if not user_vms:
        msg = f"Hey {user.first_name}, you don't own any vm to delete"
    else:
        user.owned_vms = []
        db.session.commit()
        msg = "Your VMs have been deleted"

    return command_response(msg)


@bp.errorhandler(500)
def unexpected_thing(error):
    if isinstance(error, SlackerException):
        # Handle expected exception (a little bit of an oximoron)
        resp = {'text': f':anger:  {str(error)}'}
    else:
        exception_text = traceback.format_exc()
        logger.error(f'Error: {repr(error)}\nTraceback:\n{exception_text}')
        resp = {
            'text': f'You hurt the bot :face_with_head_bandage:.. Be gentle when speaking with him.\n'
                    f'Error: `{repr(error)}`'
        }

    return reply(resp)

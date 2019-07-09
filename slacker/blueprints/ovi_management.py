from flask import request, current_app as the_app, make_response

from slacker.models.user import get_or_create_user
from slacker.utils import BaseBlueprint, reply, command_response

bp = BaseBlueprint('ovi', __name__, url_prefix='/ovi')

START_USAGE = "Usage: `/start <vm_name> [<another_vm>]"
STOP_USAGE = "Usage: `/stop <vm_name> [<another_vm>]"
INFO_USAGE = "Usage: `/info <vm_name> [<another_vm>]"
REDEPLOY_USAGE = "Usage: `/redeploy <vm> <snapshot_id>\nCheck `/snapshots` for available options"

WRONG_ALIAS_MESSAGE = "You don't have a VM under alias '{alias}'"

class OviCli:
    def __init__(self, vms_config, name=None, token=None):
        self.vms = vms_config
        self.name = name
        self.token = token


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'text': 'Ovi Management',
        'commands': ['start', 'stop', 'info', 'redeploy', 'snapshots']
    })


@bp.route('/register', methods=('GET', 'POST'))
def register():
    trigger_id = request.form.get('trigger_id')
    user_id = request.form.get('user_id')
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

    the_app.slack_cli.api_call(
        "dialog.open",
        trigger_id=trigger_id,
        dialog=dialog
    )

    return make_response('', 200)


@bp.route('/start', methods=('GET', 'POST'))
def start():
    alias = request.form.get('text')
    user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
    stored_vms = {vm.alias: vm.vm_id for vm in user.owned_vms}
    vms, error = validate_existing_alias(alias, stored_vms, usage_help=START_USAGE)
    if error:
        return command_response(error)

    cli = OviCli(stored_vms, user.ovi_name, user.ovi_token)
    cli.start_many(vms)  # Should be celery task
    return command_response(':check:')


def validate_existing_alias(choice, saved_vms, usage_help='Missing required argument.'):
    """Checks that invocation of parameter has the required args and those references are valid

    Returns:
        (str, None) - If choice was valid
        (None, error_msg) - If there was a problem with the choice
    """
    error = None
    if not choice:
        error = usage_help

    # Get the vm_name or vm_names as a list
    vm_names = choice.split()

    missing_alias = next((alias for alias in vm_names if alias not in saved_vms), False)
    if missing_alias:
        error = WRONG_ALIAS_MESSAGE.format(alias=missing_alias)

    return vm_names, error


@bp.route('/stop', methods=('GET', 'POST'))
def stop():
    alias = request.form.get('text')
    user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
    stored_vms = {vm.alias: vm.vm_id for vm in user.owned_vms}
    vm_names, error = validate_existing_alias(alias, stored_vms, usage_help=STOP_USAGE)
    if error:
        return command_response(error)

    cli = OviCli(stored_vms, user.ovi_name, user.ovi_token)
    cli.start_many(vm_names)
    return command_response(':check:')


@bp.route('/list', methods=('GET', 'POST'))
def show_vms():
    remote = request.form.get('text', '')
    show_remote = '-r' in remote or '--remote' in remote

    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    stored_vms = {vm.alias: vm.vm_id for vm in user.owned_vms}
    cli = OviCli(stored_vms, user.ovi_name, user.ovi_token)
    cli.list_vms(remote=show_remote)

    return command_response(':check:')


@bp.route('/info', methods=('GET', 'POST'))
def info():
    alias = request.form.get('text')
    user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
    stored_vms = {vm.alias: vm.vm_id for vm in user.owned_vms}
    vm_names, error = validate_existing_alias(alias, stored_vms, usage_help=INFO_USAGE)
    if error:
        return command_response(error)

    cli = OviCli(stored_vms, user.ovi_name, user.ovi_token)
    cli.info_many(vm_names)
    return command_response(':check:')


@bp.route('/redeploy', methods=('GET', 'POST'))
def redeploy():
    vm_name = request.form.get('text')
    if not vm_name:
        return command_response(REDEPLOY_USAGE)

    try:
        vm_name, image = vm_name.split()
    except ValueError:
        return command_response(REDEPLOY_USAGE)

    user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
    stored_vms = {vm.alias: vm.vm_id for vm in user.owned_vms}
    if vm_name not in stored_vms:
        return command_response(WRONG_ALIAS_MESSAGE.format(alias=vm_name))

    cli = OviCli(stored_vms, user.ovi_name, user.ovi_token)
    cli.redeploy(vm_name, image)
    return command_response(':check:')


@bp.route('/snapshots', methods=('GET', 'POST'))
def snapshots():
    user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
    cli = OviCli({}, user.ovi_name, user.ovi_token)
    cli.snapshots()
    return command_response(':check:')

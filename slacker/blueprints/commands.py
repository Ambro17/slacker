import threading
import json

from flask import Blueprint, current_app as the_app, request, make_response, Response
from loguru import logger

from slacker.api.aws.aws import load_vms_info, save_user_vms
from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte
from slacker.database import db
from slacker.utils import reply, command_response

bp = Blueprint('commands', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a command.",
        'commands': ['feriados', 'hoypido', 'subte']
    })


@bp.route('/feriados', methods=('GET', 'POST'))
def feriados() -> Response:
    response = get_feriadosarg()
    return command_response(response)


@bp.route('/hoypido', methods=('GET', 'POST'))
def hoypido() -> str:
    menus = get_hoypido()
    return command_response(menus)


@bp.route('/subte', methods=('GET', 'POST'))
def subte() -> str:
    status = get_subte()
    return command_response(status)


@bp.route('/aws', methods=('GET', 'POST'))
def aws() -> str:
    trigger_id = request.form.get('trigger_id')
    user_id = request.form.get('user_id')
    dialog = {
        "callback_id": f"aws_callback",
        "title": "My amazon VMs",
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
                "hint": "Put your vm alias and ids. Separated by commas and new lines",
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


@bp.route('/poll', methods=('GET', 'POST'))
def create_poll():
    number_emojis = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
    text = request.form.get('text')
    channel = request.form.get('channel_id')

    try:
        question, rest = text.split('?')
    except ValueError:
        return command_response('Mal formato. Uso: /poll pregunta? opcion1 opcion2')
    else:
        if not rest:
            return command_response('Mal formato. Faltaron las opciones. /poll pregunta? op1 op2 op3')
        options_with_reaction = ''
        options = rest.split()
        print(options)
        for i, op in zip(range(10), options):
            options_with_reaction += f':{number_emojis[i]}: {op}\n'


        msg = f'*{question}?*\n{options_with_reaction}'

    r = the_app.slack_cli.api_call("chat.postMessage", channel=channel, text=msg)
    if not r['ok']:
        return command_response('Error!')

    msg_timestamp = r['message']['ts']


    def add_options_as_reactions(options, ts):
        for i, option in zip(range(10), options):  # Hardcode limit of 10 options
            r = the_app.slack_cli.api_call("reactions.add",
                                           channel=channel,
                                           timestamp=ts,
                                           name=number_emojis[i])

    add_options_as_reactions(options, msg_timestamp)
    OK = ''  # reply is sent as a new message in order to capture message timestamp (required to add reactions to msg)
    return OK, 200


@bp.route("/slack/message_actions", methods=["POST"])
def message_actions():
    action = json.loads(request.form["payload"])

    is_aws_submission = action["type"] == "dialog_submission" and action.get('callback_id', '').startswith('aws_callback')
    OK = ''
    if is_aws_submission:
        # Update the message to show that we're in the process of taking their order
        form = action['submission']
        name, token, vms = form['user'], form['token'], form['vms_info']
        vm_data = load_vms_info(vms)
        if vm_data is None:
            resp = {
                'errors': [{
                    'name': 'vms_info',
                    'error': 'Invalid VMs format. Check the placeholder to see the correct format'
                }]
            }
        else:
            save_user_vms(db.session, the_app.slack_cli, action['user']['id'], name, token, vms)
            vms = '\n'.join(f':point_right: {vm}: {hash}' for vm, hash in vm_data.items())
            msg = f':check: Tus vms quedaron guardadas:\n{vms}'
            resp = OK

            the_app.slack_cli.api_call("chat.postMessage",
                                       channel=action['channel']['id'],
                                       text=msg)
    else:
        resp = OK
    logger.info("response %r" % resp)
    return reply(resp, 200)

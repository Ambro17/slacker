import json

from flask import Blueprint, current_app as the_app, request, Response
from loguru import logger

from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte
from slacker.models.poll import Poll
from slacker.tasks import add_together
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
def hoypido():
    menus = get_hoypido()
    return command_response(menus)


@bp.route('/subte', methods=('GET', 'POST'))
def subte():
    status = get_subte()
    return command_response(status)


@bp.route('/celery', methods=('GET', 'POST'))
def celery():
    add_together.delay(5, 3)
    return 'Task sent'


@bp.route('/poll', methods=('GET', 'POST'))
def create_poll():
    """Creates a poll from a user question and options.

    i.e: is this the real life? yes no

    """
    text = request.form.get('text')
    channel = request.form.get('channel_id')

    poll, error = Poll.from_string(text)
    if error:
        return command_response(error)

    msg_section = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": str(poll)}
    }

    block_elems = [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": str(option_number),
            },
            "value": f'{option_number}',
            "action_id": f'poll_vote:{option_number}'
        }
        for option_number in range(1, len(poll.options) + 1)
    ]
    blocks = [
        msg_section,
        {'type': 'actions', 'block_id': f'{poll.id}', 'elements': block_elems}
    ]
    r = the_app.slack_cli.api_call("chat.postMessage", channel=channel, blocks=blocks)
    if not r['ok']:
        logger.error(r)
        return command_response('Error!')

    OK = ''
    return OK, 200


@bp.errorhandler(500)
def not_found(error):
    resp = {'text': f':anger:  {repr(error)}'}
    return reply(resp)
from flask import Blueprint, current_app as the_app, request, url_for
from loguru import logger

import celery.states as states

from slacker.database import db
from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte
from slacker.models.poll import Poll
from slacker.models.user import get_or_create_user, User
from slacker.slack_cli import slack_cli, Slack
from slacker.utils import reply, command_response, USER_REGEX, ephemeral_reply

from slacker.worker import celery

bp = Blueprint('commands', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a command.",
        'commands': ['feriados', 'hoypido', 'subte']
    })


@bp.route('/help', methods=('GET', 'POST'))
def help():
    """Lists all bot commands."""
    commands = """
    *Retro Management*
    - `/retro_help`
    - `/add_team`
    - `/start_sprint`
    - `/add_retro_item`
    - `/show_retro_items`
    - `/end_sprint`
    - `/team_members`

    *Stickers*
    - `/add_sticker`
    - `/delete_sticker`
    - `/send_sticker`
    - `/show_stickers`

    *OVI Management*
    - `/start`
    - `/stop`
    - `/list`
    - `/info`
    - `/redeploy`
    - `/snapshots`

    *Miscellaneous*
    - `/poll`
    - `/feriados`
    - `/hoypido`
    - `/subte`

    *Meta*
    - `/skills` (Shows this message)

    """
    return command_response(commands)


@bp.route('/subte', methods=('GET', 'POST'))
def subte():
    status = get_subte()
    return command_response(status)


@bp.route('/feriados', methods=('GET', 'POST'))
def feriados():
    response = get_feriadosarg()
    return command_response(response)


@bp.route('/hoypido', methods=('GET', 'POST'))
def hoypido():
    menus = get_hoypido()
    return command_response(menus)


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
    r = Slack.chat_postMessage(channel=channel, blocks=blocks)
    if not r['ok']:
        logger.error(r)
        return command_response('Error!')

    OK = ''
    return OK, 200


@bp.route('/ping', methods=('GET', 'POST'))
def ping():
    text = request.form.get('text')
    user_id = request.form.get('user_id')
    if not text:
        return command_response('Who are you challenging? `/ping @user`')

    match = USER_REGEX.search(text)
    if not match:
        return command_response('Who are you challenging? `/ping @user`')

    mention = match.groupdict()['user_id']
    user = get_or_create_user(slack_cli, user_id)
    defied_user = get_or_create_user(slack_cli, mention)
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Ping.. :table_tennis_paddle_and_ball: from `{user.first_name}`"
            }
        },
        {
            "type": "actions",
            'block_id': f'ping_block:{user_id}:{defied_user.user_id}',
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Pong"
                    },
                    "style": "primary",
                    "value": "YES",
                    "action_id": f"{defied_user.first_name}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Not now"
                    },
                    "style": "danger",
                    "value": "NO",
                }
            ]
        }
    ]
    celery.send_task("tasks.send_message_with_blocks", args=(block, mention))
    return ephemeral_reply(f'Sent challenge to {defied_user.first_name} :table_tennis_paddle_and_ball:')


@bp.errorhandler(500)
def not_found(error):
    resp = {'text': f':anger:  {repr(error)}'}
    return reply(resp)

import json

from flask import Blueprint, current_app as the_app, request, make_response, Response
from loguru import logger

from slacker.api.aws.aws import load_vms_info, save_user_vms
from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.stickers import show_stickers, lookup_sticker, sticker_add
from slacker.api.poll import user_has_voted
from slacker.api.subte import get_subte
from slacker.database import db
from slacker.models.poll import Poll, Vote
from slacker.models.user import get_or_create_user
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


@bp.route('/add_sticker', methods=('GET', 'POST'))
def add_sticker():
    text = request.form.get('text')
    try:
        name, url = text.split()
        return sticker_add(name, url)
    except ValueError:
        return command_response('Usage: `/add_sticker mymeme https://i.imgur.com/12345678.png`')


@bp.route('/send_sticker', methods=('GET', 'POST'))
def send_sticker():
    sticker_name = request.form.get('text')
    if not sticker_name:
        resp =  command_response('Error. Usage: /sticker <sticker_name>')
    else:
        resp = lookup_sticker(sticker_name)

    return resp


@bp.route('/list_stickers', methods=('GET', 'POST'))
def list_stickers():
    stickers = show_stickers()
    return stickers


@bp.route('/aws', methods=('GET', 'POST'))
def aws():
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


@bp.route('/poll', methods=('GET', 'POST'))
def create_poll():
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


@bp.route("/slack/message_actions", methods=["POST"])
def message_actions():
    logger.debug("Handling message action.")
    # TODO: Respond OK ASAP and process request async
    action = json.loads(request.form["payload"])
    logger.debug(f"Action: {action}")

    # TODO: Implement better handling of action callbacks and loop over handlers like ptb lib.
    is_aws_submission = action["type"] == "dialog_submission" and action.get('callback_id', '').startswith('aws_callback')
    OK = ''
    if is_aws_submission:
        # Update the message to show that we're in the process of taking their order
        form = action['submission']
        name, token, raw_vms = form['user'], form['token'], form['vms_info']

        logger.debug(f"VMs input:\n{raw_vms}")
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
            logger.debug(f"Get or create user. Id {action['user']['id']}")
            user = get_or_create_user(the_app.slack_cli, action['user']['id'])
            logger.debug("User: %s" % user.real_name)
            try:
                logger.debug("Saving VMs..")
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
                vms = '\n'.join(f':point_right: {vm}: {hash}' for vm, hash in vms_info.items())
                msg = f':check: Tus vms quedaron guardadas:\n{vms}'
                resp = OK
                logger.debug("Notifying user of success")
                # the_app.slack_cli.api_call("chat.postMessage",
                #                            channel=action['channel']['id'],
                #                            text=msg)  # Should be async. It takes too long and slack thinks dialog
                #                            post went wrong
                logger.debug("User notified")


    elif action["type"] == "block_actions":
        """
        {
            'type': 'block_actions',
            'team': {
                'id': 'TG4H5ANVC',
                'domain': 'boedo'
            },
            'user': {
                'id': 'UG31KD90T',
                'username': 'ambro17.1',
                'name': 'ambro17.1',
                'team_id': 'TG4H5ANVC'
            },
            'api_app_id': 'AG4H6GBEJ',
            'token': 'eplrfng7b3YBA93ZYNVFLUi6',
            'container': {
                'type': 'message',
                'message_ts': '1561846841.001400',
                'channel_id': 'CKSMVKQC9',
                'is_ephemeral': True
            },
            'trigger_id': '679915593636.548583362998.50b265af2e667a9c6abb37c80542998f',
            'channel': {
                'id': 'CKSMVKQC9',
                'name': 'test2'
            },
            'response_url': 'https://hooks.slack.com/actions/TG4H5ANVC/680397789861/XywBRhjn82vIgOuQrBfUxxFS',
            'actions': [{
                'action_id': 'send_sticker_action_id',
                'block_id': 'send_sticker_block_id',
                'text': {
                    'type': 'plain_text',
                    'text': 'Send!',
                    'emoji': True
                },
                'value': 'send_sticker',
                'style': 'primary',
                'type': 'button',
                'action_ts': '1561846848.181810'
            }]
        }            
        """
        the_action = action['actions'][0]
        if the_action['action_id'].startswith('send_sticker_action_id'):
            """
            'actions': [{
                'action_id': 'send_sticker_action_id',
                'block_id': 'send_sticker_block_id',
                'text': {
                    'type': 'plain_text',
                    'text': 'Send!',
                    'emoji': True
                },
                'value': 'link',
                'style': 'primary',
                'type': 'button',
                'action_ts': '1561848669.221608'
            }]                
            """
            _, sticker_name = the_action['action_id'].split(':', 1)
            img_url = the_action['value']
            blocks = [
                {
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": sticker_name,
                    },
                    "image_url": img_url,
                    "alt_text": sticker_name
                }
            ]
            logger.debug(f'Sending sticker.. {img_url}')
            r = the_app.slack_cli.api_call('chat.postMessage',
                                           channel=action['channel']['id'],
                                           blocks=blocks)
            if not r['ok']:
                logger.error("Sticker not sent. %s" % r)

        elif the_action['action_id'].startswith('poll_vote'):
            poll_id = the_action['block_id']
            poll = Poll.find(id=poll_id)
            if not poll:
                return reply('Poll not found.')

            vote_choice = the_action['value']
            op = next((op for op in poll.options if op.number == int(vote_choice)), None)
            if not op:
                return reply('Vote choice not found')

            # Add vote for chosen option
            user_id = action['user']['id']
            if user_has_voted(user_id, poll.id):
                return reply('You have already voted.')

            db.session.add(Vote(option_id=op.id, user_id=user_id))
            db.session.commit()


            blocks = action['message']['blocks']
            # Update block's text with new votes
            blocks[0]['text']['text'] = str(poll)
            r = the_app.slack_cli.api_call("chat.update",
                                           channel=action['channel']['id'],
                                           ts=action['message']['ts'],
                                           blocks=blocks)
            if not r['ok']:
                logger.error(r)
                return reply('Error updating vote')

            logger.debug('Poll vote was updated.')

        resp = OK
    else:
        resp = OK

    return reply(resp, 200)


@bp.errorhandler(500)
def not_found(error):
    resp = {'text': f':anger:  {repr(error)}'}
    return reply(resp)
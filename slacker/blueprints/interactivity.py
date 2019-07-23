"""
Slack offers buttons, dialogs, blocks, menus, etc, that hit a special endpoint when user interacts with them.
This module handles those interactions. Validating user input, sending the corresponding tasks or doing whatever is
necessary.
"""
import json

from loguru import logger
from flask import request, current_app as the_app

from slacker.database import db
from slacker.api.aws.aws import load_vms_info, save_user_vms
from slacker.api.poll import user_has_voted
from slacker.models import Poll, Vote
from slacker.models.user import get_or_create_user
from slacker.tasks_proxy import send_ephemeral_message
from slacker.utils import BaseBlueprint, reply, ephemeral_reply, OK, reply_raw
from slacker.worker import celery

bp = BaseBlueprint('interactive', __name__, url_prefix='/interactive')


@bp.route("/message_actions", methods=["POST"])
def message_actions():
    logger.debug("Handling message action..")
    action = json.loads(request.form["payload"])
    try:
        return handle_action(action)
    except Exception as e:
        send_ephemeral_message(f'Something bad happened.\n`{repr(e)}`',
                               channel=action['channel']['id'],
                               user=action['user']['id'])
        return reply_raw(OK)

def handle_action(action):
    logger.debug(f"Action: {action}")
    # TODO: Respond OK ASAP and process request async
    is_aws_submission = action["type"] == "dialog_submission" and action.get('callback_id', '').startswith('aws_callback')
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
                resp = OK

                logger.debug("Notifying user of success")
                vms = '\n'.join(f'`{vm}: {hash}`' for vm, hash in vms_info.items())
                msg = f':check: Tus vms quedaron guardadas.\nUser: `{name}`\nVMs:\n{vms}'
                promise = send_ephemeral_message(msg, channel=action['channel']['id'], user=action['user']['id'])
                logger.debug("Task %s sent." % promise)


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
            option = next((op for op in poll.options if op.number == int(vote_choice)), None)
            if not option:
                logger.debug('Vote choice %s not found on poll %s' % (vote_choice, poll.id))
                return ephemeral_reply('Vote choice not found')

            # Add vote for chosen option
            user_id = action['user']['id']
            if user_has_voted(user_id, poll.id):
                logger.debug('User has already voted')
                send_ephemeral_message('You have already voted.',
                                       channel=action['channel']['id'],
                                       user=action['user']['id'])
                return reply_raw(OK)

            db.session.add(Vote(poll=poll, option=option, user_id=user_id))
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

        elif the_action['block_id'].startswith('ping'):
            _, user, mentioned_id = the_action['block_id'].split(':')
            accept = the_action['value']
            challenged_user = the_action['action_id']
            msg = f'Challenge accepted by {challenged_user} :muscle:' if accept == 'YES' else 'Not now..'
            celery.send_task("tasks.send_message", args=(msg, mentioned_id))

        resp = OK
    else:
        logger.info('No handler for this action')
        resp = OK


    return reply_raw(resp)

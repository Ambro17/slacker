"""
Slack offers buttons, dialogs, blocks, menus, etc, that hit a special endpoint when user interacts with them.
This module handles those interactions. Validating user input, sending the corresponding tasks or doing whatever is
necessary.
"""
import json

from slacker.log import logger
from flask import request

from slacker.api.poll import user_has_voted
from slacker.blueprints.ovi_management import handle_aws_submission
from slacker.database import db
from slacker.models import Poll, Vote
from slacker.slack_cli import Slack, PollsBot
from slacker.tasks_proxy import send_ephemeral_message_async, send_ephemeral_message_polls
from slacker.utils import BaseBlueprint, reply, ephemeral_reply, OK, reply_raw, reply_text
from slacker.worker import celery

bp = BaseBlueprint('interactive', __name__, url_prefix='/interactive')


@bp.route("/message_actions", methods=["POST"])
def message_actions():
    logger.debug("Handling message action..")
    action = json.loads(request.form["payload"])
    try:
        return handle_action(action)
    except Exception as e:
        logger.exception(f"Error handling interactive action: {action!r}")
        send_ephemeral_message_async(f'Something bad happened.\n`{repr(e)}`',
                                     channel=action['channel']['id'],
                                     user=action['user']['id'])
        return reply_text(OK)


def handle_action(action):
    logger.debug(f"Action: {action}")

    if action["type"] == "dialog_submission" and action.get('callback_id', '').startswith('aws_callback'):
        resp = handle_aws_submission(action)

    elif action["type"] == "block_actions":
        the_action = action['actions'][0]
        if the_action['action_id'].startswith('send_sticker_action_id'):
            _, sticker_name = the_action['action_id'].split(':', 1)
            img_url = the_action['value']
            sticker = [
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
            r = Slack.chat_postMessage(channel=action['channel']['id'], blocks=sticker)
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
                send_ephemeral_message_polls('Cheater! You have already voted.',
                                             channel=action['channel']['id'],
                                             user=user_id)

                return reply_raw(OK)

            db.session.add(Vote(poll=poll, option=option, user_id=user_id))
            db.session.commit()

            blocks = action['message']['blocks']
            # Update block's text with new votes
            blocks[0]['text']['text'] = str(poll)
            r = PollsBot.chat_update(channel=action['channel']['id'], ts=action['message']['ts'], blocks=blocks)
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
        logger.error('No handler for this action')
        resp = OK

    return reply_raw(resp)

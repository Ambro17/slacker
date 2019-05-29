import os
from flask import (
    Blueprint, request, jsonify
)
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from loguru import logger


bp = Blueprint('api', __name__, url_prefix='/slack/events')

app = SlackEventAdapter(os.environ["SLACK_SIGNATURE"],
                        endpoint="/events",
                        server=app)

slack_client = SlackClient(os.environ["BOT_TOKEN"])

@bp.route('/', methods=('GET', 'POST'))
def index():
    return jsonify({'message': "You must specify a command"})


@app.on("message")
def handle_message(event_data):
    event = event_data['event']
    if event.get("subtype") != 'bot_message' and not event.get('text', '').startswith('/'):
        slack_client.api_call("chat.postMessage",
                              channel=event['channel'],
                              text=event['text'].upper())
        resp = slack_client.api_call("users.info",
                                     user=event['user'])

        if resp['ok']:
            user = resp['user']
            u = S.query(User.user).filter_by(user=user['id']).one_or_none()
            if u is None:
                try:
                    S.add(User.from_json(user['profile'], user=user['id']))
                except Exception:
                    logger.opt(exception=True).error('Error adding user from %s', resp)
                else:
                    S.commit()
                    logger.info('User %s added to db', user['id'])

        else:
            logger.error('Bad request: %s', resp)


@app.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text)


@app.on("error")
def error_handler(err):
    print("ERROR: " + str(err))


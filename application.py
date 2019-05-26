import json
import os

from flask import Flask, request, make_response, jsonify, url_for
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
from werkzeug.routing import BuildError
from werkzeug.utils import redirect
from loguru import logger

from commands.aws.aws import get_aws
from commands.dolar.dolar import get_dolar
from commands.dolar_rofex.rofex import get_rofex
from commands.feriados.feriados import get_feriadosarg
from commands.hoypido.hoypido import get_hoypido, get_hoypido_by_day
from commands.posiciones.posiciones import get_posiciones
from commands.subte.subte import get_subte
from db import S
from models.user import User
from utils import send_message, make_answer

app = Flask(__name__)

events_route = SlackEventAdapter(os.environ["SLACK_SIGNATURE"],
                                 endpoint="/slack/events",
                                 server=app)

slack_client = SlackClient(os.environ["BOT_TOKEN"])


@events_route.on("message")
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


@events_route.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text)


@events_route.on("error")
def error_handler(err):
    print("ERROR: " + str(err))


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/', methods=['GET', 'POST'])
def command_dispatcher():
    command = request.form.get('command', '')[1:]
    try:
        return redirect(url_for(command))
    except BuildError:
        if not command:
            msg = 'You must pass a command argument'
        else:
            msg = f'Unknown command "{command}"'
    return send_message(msg)


@app.route('/dolar', methods=['GET', 'POST'])
def dolar():
    return send_message(get_dolar())


@app.route('/rofex', methods=['GET', 'POST'])
def rofex():
    return send_message(get_rofex())


@app.route('/subte', methods=['GET', 'POST'])
def subte():
    return send_message(get_subte())


@app.route('/feriados', methods=['GET', 'POST'])
def feriados():
    return send_message(get_feriadosarg())


@app.route('/hoypido', methods=['GET', 'POST'])
def hoypido():
    day = request.form.get('text')
    if not day:
        menu = get_hoypido()
    else:
        menu = get_hoypido_by_day(day)

    return send_message(menu, msg_type='ephemeral')


@app.route('/posiciones', methods=['GET', 'POST'])
def posiciones():
    return send_message(get_posiciones())


@app.route('/aws', methods=['GET', 'POST'])
def amazon_aws():
    trigger_id = request.form.get('trigger_id')
    text = request.form.get('text')
    if text:
        # If user exists in db, search if text[command] and text[vm_name]
        # to execute /aws start console or /aws stop sensor
        return 'some text'

    if not trigger_id:
        send_message('Ups')
        return 'Bad'

    dialog = {
        "callback_id": "mycallbackid",
        "title": "My amazon VMs",
        "submit_label": "Save",
        "state": "Limo",
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
                "placeholder": "console, 5kyq3bdcnl6sbnsv9t6q\nsensor, wwt6adcuow78sj9hj8hi",
                "name": "vmsinfo",
            }
        ]
    }

    slack_client.api_call(
        "dialog.open",
        trigger_id=trigger_id,
        dialog=dialog
    )

    return make_response('', 200)


@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    message_action = json.loads(request.form["payload"])

    if message_action["type"] == "dialog_submission":
        # Update the message to show that we're in the process of taking their order
        slack_client.api_call(
            "chat.postMessage",
            channel='#general',
            text=":white_check_mark: Datos Guardados",
        )

    return make_response("", 200)


if __name__ == "__main__":
    logger.info('Running..')
    app.run(host='0.0.0.0', port='3000', debug=os.getenv('DEBUG', False))
    logger.info('Stopping..')

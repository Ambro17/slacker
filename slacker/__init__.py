import os

from flask import Flask, make_response, jsonify
from loguru import logger
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter

from .database import db
from slacker import manage
from slacker.blueprints import retroapp
from .models.user import User
from .blueprints import commands


def create_app(config_object='slacker.settings'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    slackcli = SlackClient(os.environ["BOT_TOKEN"])
    app.slack_cli = slackcli
    register_event_handlers(app)

    return app


def register_extensions(app):
    """Register SQLAlchemy extension."""
    db.init_app(app)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(commands.bp)
    app.register_blueprint(retroapp.bp)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(manage.test, 'test')
    app.cli.add_command(manage.clean, 'clean')
    app.cli.add_command(manage.init_db_command, 'init-db')


def register_error_handlers(app):
    """Register error handlers to respond nicely"""
    @app.errorhandler(400)
    def not_found(error):
        return make_response(jsonify({'error': 'Bad request'}), 400)

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.errorhandler(500)
    def not_found(error):
        return make_response(jsonify({'error': 'Server error. Sh*t happens.'}), 500)


def register_event_handlers(app):
    """Register handlers for slack events subscriptions"""
    events = SlackEventAdapter(os.environ["SLACK_SIGNATURE"],
                               endpoint="/events",
                               server=app)

    @events.on("message")
    def handle_message(event_data):
        """Save new users"""
        event = event_data['event']
        if event.get("subtype") != 'bot_message' and not event.get('text', '').startswith('/'):
            app.slack_cli.api_call("chat.postMessage",
                                  channel=event['channel'],
                                  text=event['text'].upper())
            resp = app.slack_cli.api_call("users.info",
                                         user=event['user'])
            if resp['ok']:
                user = resp['user']
                print(resp)
                u = db.session.query(User.user).filter_by(user_id=user['id']).one_or_none()
                if u is None:
                    try:
                        db.session.add(User.from_json(user))
                    except Exception:
                        logger.opt(exception=True).error('Error adding user from %s', resp)
                    else:
                        db.session.commit()
                        logger.info('User %s added to db', user['id'])

            else:
                logger.error('Bad request: %s', resp)

    @events.on("reaction_added")
    def reaction_added(event_data):
        """Reply reaction"""
        event = event_data["event"]
        emoji = event["reaction"]
        channel = event["item"]["channel"]
        text = ":%s:" % emoji
        app.slack_cli.api_call("chat.postMessage", channel=channel, text=text)

    @events.on("error")
    def error_handler(err):
        app.slack_cli.api_call("chat.postMessage", channel=err['channel'], text='Sh*t happens')
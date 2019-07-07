import os
import re

from flask import Flask
from loguru import logger
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from raven.contrib.flask import Sentry

from slacker.blueprints import ovimanagement, interactivity, stickers
from slacker.utils import reply, is_user_message, add_user
from .manage import test, clean, init_db_command
from .database import db
from .models.user import User
from .blueprints import commands, retroapp

sentry = Sentry()


def create_app(config_object='slacker.settings'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    app.slack_cli = SlackClient(os.environ["BOT_TOKEN"])
    register_event_handlers(app)

    return app


def register_extensions(app):
    """Register SQLAlchemy extension."""
    db.init_app(app)
    sentry_logging = os.getenv('SENTRY_DSN')
    if sentry_logging is not None:
        sentry.init_app(app, dsn=sentry_logging)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(commands.bp)
    app.register_blueprint(retroapp.bp)
    app.register_blueprint(ovimanagement.bp)
    app.register_blueprint(interactivity.bp)
    app.register_blueprint(stickers.bp)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(test, 'test')
    app.cli.add_command(clean, 'clean')
    app.cli.add_command(init_db_command, 'init-db')


def register_error_handlers(app):
    """Register error handlers to respond nicely"""
    @app.errorhandler(400)
    def not_found(error):
        return reply({'text': 'Bad request', 'error': repr(error)})

    @app.errorhandler(404)
    def not_found(error):
        return reply({'text': 'Request not found', 'error': repr(error)})

    @app.errorhandler(500)
    def not_found(error):
        return reply({'text': 'Server error. Sh*t happens.', 'error': repr(error)})


def register_event_handlers(app):
    """Register handlers for slack events subscriptions"""
    events = SlackEventAdapter(os.environ["SLACK_SIGNATURE"],
                               endpoint="/slack/events",
                               server=app)

    @events.on("message")
    def handle_message(event_data):
        """Save new users"""
        logger.debug('Processing message event:\n%r' % event_data['event'])
        event = event_data['event']
        if is_user_message(event):
            message = event.get('text')
            if message is None:
                return


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

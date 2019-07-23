from flask import Flask
from dotenv import load_dotenv

from .blueprints import commands, retroapp, interactivity, stickers
from .database import db
from .manage import test, clean, init_db_command
from .utils import reply, is_user_message, add_user

def create_app(config_object='slacker.settings'):
    """Create and configure an instance of the Flask application."""
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    return app


def register_extensions(app):
    """Register db, logging and task extensions."""
    db.init_app(app)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(commands.bp)
    app.register_blueprint(retroapp.bp)
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
    def bad_request(error):
        return reply({'text': 'Invalid Request', 'error': repr(error)})

    @app.errorhandler(500)
    def server_error(error):
        return reply({'text': 'Server error. Sh*t happens.', 'error': repr(error)})

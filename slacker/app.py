from flask import Flask
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from slacker.security import Crypto
from .blueprints import commands as commands_bp, retroapp, interactivity, stickers, ovi_management, rooms
from .database import db
from .manage import clean, init_db
from .utils import reply


def create_app(config_object='slacker.settings'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    return app


def register_extensions(app):
    """Register db and bcrypt extensions."""
    db.init_app(app)
    Crypto.configure(app.config['HASH_SECRET'])
    logger.debug(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(commands_bp.bp)
    app.register_blueprint(retroapp.bp)
    app.register_blueprint(interactivity.bp)
    app.register_blueprint(ovi_management.bp)
    app.register_blueprint(stickers.bp)
    app.register_blueprint(rooms.bp)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(clean, 'clean')
    app.cli.add_command(init_db, 'init-db')


def register_error_handlers(app):
    """Register error handlers to respond nicely"""
    # Validate that slack requests come from slack. See slackevents api for implementation hint
    @app.errorhandler(400)
    def not_found(error):
        return reply({'text': 'Bad request', 'error': repr(error)})

    @app.errorhandler(404)
    def bad_request(error):
        return reply({'text': 'Invalid Request', 'error': repr(error)})

    @app.errorhandler(500)
    def server_error(error):
        return reply({'text': 'Oops ¯\\_(ツ)_/¯. Errors happen', 'error': repr(error)})

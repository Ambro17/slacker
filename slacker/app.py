import hashlib
import hmac
import time

from flask import Flask, request
from loguru import logger

from .blueprints import commands as commands_bp, retroapp, interactivity, stickers, ovi_management, rooms
from .database import db
from .manage import clean, init_db
from .security import Crypto
from .app_config import CUERVOT_SIGNATURE, OVIBOT_SIGNATURE
from .utils import reply


def create_app(config_object='slacker.app_config'):
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
    """Register app handlers to respond nicely"""

    @app.before_request
    def verify_request_signature():
        """
        On each HTTP request that Slack sends, they add an X-Slack-Signature
        HTTP header. The signature is created by combining the signing secret
        with the body of the request they're sending using a standard
        HMAC-SHA256 keyed hash.

        Docs: https://api.slack.com/docs/verifying-requests-from-slack#verification_token_deprecation

        """
        # Encode secrets as bytestrings
        mainsecret = CUERVOT_SIGNATURE.encode('utf-8')
        ovisecret = OVIBOT_SIGNATURE.encode('utf-8')

        # Read request headers and reject it if it's too old
        try:
            real_signature = request.headers['X-Slack-Signature']
            timestamp = request.headers['X-Slack-Request-Timestamp']
        except KeyError:
            return bad_request('Are you really slack?')

        if abs(time.time() - int(timestamp)) > 60 * 2:
            return bad_request('Request too old')

        # Build verification string with timestamp and request data
        data = request.get_data()
        verification_string = f'v0:{timestamp}:'.encode('utf-8') + data
        try:
            signature =  hmac.new(mainsecret, verification_string, hashlib.sha256).hexdigest()
            assert hmac.compare_digest(f'v0={signature}', real_signature), "Invalid request. You are not slack"
        except AssertionError:
            # Retry with the other bot secret contained by the app
            signature = hmac.new(ovisecret, verification_string, hashlib.sha256).hexdigest()
            try:
                assert hmac.compare_digest(f'v0={signature}', real_signature), "Invalid request. You are not slack"
            except AssertionError:
                # The request is definitely not from slack. Reject it
                return bad_request('Invalid request secrets')

    @app.errorhandler(400)
    def not_found(error):
        return reply({'text': 'Bad request', 'error': repr(error)})

    @app.errorhandler(404)
    def bad_request(error):
        return reply({'text': 'Invalid Request', 'error': repr(error)})

    @app.errorhandler(500)
    def server_error(error):
        return reply({'text': 'Oops ¯\\_(ツ)_/¯. Errors happen', 'error': repr(error)})

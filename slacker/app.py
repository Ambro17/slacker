import hashlib
import hmac
import time
import traceback

from flask import Flask, request
from loguru import logger

from .app_config import CUERVOT_SIGNATURE, OVIBOT_SIGNATURE, HASH_SECRET, SQLALCHEMY_DATABASE_URI, DEBUG
from .blueprints import commands as commands_bp, retroapp, interactivity, stickers, ovi_management, rooms
from .database import db
from .manage import clean, init_db
from .security import Crypto
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
    Crypto.configure(HASH_SECRET)
    logger.debug(f"Database: {SQLALCHEMY_DATABASE_URI}")


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
        if DEBUG:
            logger.debug('Dev mode. Bypassing signature checking..')
            return

        # Encode secrets as bytestrings
        mainsecret = CUERVOT_SIGNATURE
        ovisecret = OVIBOT_SIGNATURE

        # Read request headers and reject it if it's too old
        logger.debug('Headers:\n{}', request.headers)

        try:
            request_hash = request.headers['X-Slack-Signature']
            timestamp = request.headers['X-Slack-Request-Timestamp']
        except KeyError:
            return bad_request('Missing required headers')

        if abs(time.time() - int(timestamp)) > 60 * 2:
            return bad_request('Request too old')

        if not verify_signatures(timestamp, request_hash, (mainsecret, ovisecret)):
            return bad_request('Failed request authenticity check. You are not slack..')

    @app.errorhandler(400)
    def bad_request(error):
        return reply({'text': 'Bad request', 'error': repr(error)})

    @app.errorhandler(404)
    def not_found(error):
        return reply({'text': 'Resource not found', 'error': repr(error)})

    @app.errorhandler(500)
    def server_error(error):
        exception_text = traceback.format_exc()
        logger.error(f'Error: {repr(error)}\nTraceback:\n{exception_text}')
        return reply({'text': 'Oops ¯\\_(ツ)_/¯. Errors happen', 'error': repr(error)})


def verify_signatures(timestamp, signature, signing_secrets):
    return any(verify_signature(timestamp, signature, app_signing_secret) for app_signing_secret in signing_secrets)


def verify_signature(timestamp, signature, signing_secret):
    # Verify the request signature of the request sent from Slack
    # Generate a new hash using the app's signing secret, the request timestamp and data
    req = f'v0:{timestamp}:'.encode('utf-8') + request.get_data()
    request_hash = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        req,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(request_hash, signature)

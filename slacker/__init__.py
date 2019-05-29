import os

from flask import Flask, request, make_response, jsonify
from loguru import logger

from .blueprints import commands
from .database import db


def create_app(config_object='slacker.settings'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app

def register_extensions(app):
    """Register SQLAlchemy extension."""
    db.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(commands.bp)
#    app.register_blueprint(blog.bp)
    return None


def register_error_handlers(app):
    @app.errorhandler(400)
    def not_found(error):
        return make_response(jsonify({'error': 'Bad request'}), 400)

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.errorhandler(500)
    def not_found(error):
        return make_response(jsonify({'error': 'Server error. Sh*t happens.'}), 500)

    return None
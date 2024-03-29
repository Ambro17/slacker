import logging

import pytest


from _pytest.logging import caplog as _caplog
from cryptography.fernet import Fernet
from loguru import logger
from slacker.app import create_app
from slacker.database import db as _db
from slacker.security import Crypto


@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app('tests.settings')
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def test_app(app):
    app.before_request_funcs = {}  # Avoid validating slack signature
    return app.test_client()


@pytest.fixture
def client(app):
    """A test client for the app to check its endpoints."""
    return app.test_client()


@pytest.fixture
def slack_cli(mocker):
    """A test client for the app."""
    cli = mocker.MagicMock()
    mocker.patch.object(cli, 'api_call')
    return cli


@pytest.fixture(scope='session')
def f():
    from tests import factorium
    return factorium


@pytest.fixture
def crypto():
    Crypto.configure(Fernet.generate_key())
    return Crypto


@pytest.fixture
def caplog(_caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropagateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)

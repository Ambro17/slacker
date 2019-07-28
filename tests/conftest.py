import logging

import pytest


from _pytest.logging import caplog as _caplog
from loguru import logger
from slacker import create_app
from slacker.database import db as _db


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
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def slack_cli(mocker):
    """A test client for the app."""
    cli = mocker.MagicMock()
    mocker.patch.object(cli, 'api_call')
    return cli


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='session')
def f():
    from tests import factorium
    return factorium


@pytest.fixture
def caplog(_caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropagateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)

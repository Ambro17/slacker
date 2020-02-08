import click
import os

from slacker.log import logger

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, 'tests')


@click.command()
def clean():
    """Stolen from SO https://stackoverflow.com/a/48281845"""
    CLEAN_CMD = 'find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +'
    out = os.system(CLEAN_CMD)
    logger.info('✅ .pyc files cleaned.')


@click.command()
def init_db():
    """Clear existing data and create new tables."""
    from slacker.database import init_db; init_db()
    logger.info('✅ Database initialized.')

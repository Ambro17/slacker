import logging
import unicodedata
from functools import wraps

import requests
from bs4 import BeautifulSoup
from flask import jsonify, Blueprint
from loguru import logger

from slacker.models import User
from slacker.database import db


JSON_TYPE = {'ContentType':'application/json'}


class BaseBlueprint(Blueprint):
    """The Flask Blueprint subclass.

    Credits to https://gist.github.com/hodgesmr/2db123b4e1bd8dcca5c4
    """

    def route(self, rule, **options):
        """Override the `route` method; add rules with and without slash."""
        def decorator(f):
            new_rule = rule.rstrip('/')
            new_rule_with_slash = '{}/'.format(new_rule)
            super(BaseBlueprint, self).route(new_rule, **options)(f)
            super(BaseBlueprint, self).route(new_rule_with_slash, **options)(f)
            return f
        return decorator


def safe(on_error: str = 'Algo salió mal..'):
    """Sends on_error message if func raises an exception"""

    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.exception('An error occurred')
                return on_error

        return wrapped_func

    return decorator


def _soupify_url(url, timeout=2, encoding='utf-8', **kwargs):
    """Given a url returns a BeautifulSoup object"""
    try:
        r = requests.get(url, timeout=timeout, **kwargs)
    except requests.ReadTimeout:
        logger.info("[soupify_url] Request for %s timed out.", url)
        raise
    except Exception as e:
        logger.error(f"Request for {url} could not be resolved", exc_info=True)
        raise ConnectionError(repr(e))


    r.raise_for_status()
    if r.status_code == 200:
        r.encoding = encoding
        return BeautifulSoup(r.text, 'lxml')
    else:
        raise ConnectionError(
            f'{url} returned error status %s - ', r.status_code, r.reason
        )


def soupify_url(url, timeout=2, encoding='utf-8', **kwargs):
    try:
        return _soupify_url(url, timeout, encoding, **kwargs)
    except Exception as e:
        raise Exception(f"Can't soupify url '{url}'") from e


def string_to_ascii(banco_name):
    """Normalize a single tag: remove non valid chars, lower case all. - Credits to @eduzen"""
    value = unicodedata.normalize("NFKD", banco_name)
    value = value.encode("ascii", "ignore").decode("utf-8")
    return value.capitalize()


def trim(text, limit=11, trim_end='.'):
    """Trim and append . if text is too long. Else return it unmodified"""
    return f'{text[:limit]}{trim_end}' if len(text) > limit else text


def monospace(text):
    return f'```\n{text}\n```'


def bold(text):
    return f'*{text}*'


def italic(text):
    return f'_{text}_'


def send_message(text, msg_type='in_channel'):
    return jsonify({
        "response_type": msg_type,
        "text": text,
    })


def reply(response, status=200, response_type=JSON_TYPE):
    return jsonify(response), status, response_type


def get_or_create_user_from_response(user_info: dict, user_id: str) -> str:
    """Adds user if response was ok

    user_info (dict): {'ok': <boolean>, 'user': <user_dict>}
    user_id (str): user identifier (i.e U12345)
    """
    if not user_info['ok']:
        raise Exception("Error getting info for %s" % user_id)

    user = user_info['user']
    u = db.session.query(User).filter_by(user_id=user['id']).one_or_none()
    if u is None:
        logger.info('Adding new user with id %s' % user_id)
        try:
            new_user = User.from_json(user)
            db.session.add(new_user)
        except Exception:
            logger.opt(exception=True).error('Error adding user from %s', user)
            raise
        else:
            db.session.commit()
            the_user_id = new_user.id
            logger.info('User %s added to db with id %s' % (user['id'], new_user.id))
    else:
        the_user_id = u.id
        logger.info('User %s already on db.' % user_id)

    return the_user_id

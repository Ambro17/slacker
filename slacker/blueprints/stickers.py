import traceback

import requests
from loguru import logger
from sqlalchemy.exc import IntegrityError

from slacker.database import db
from slacker.models.stickers import Sticker
from slacker.utils import command_response, sticker_response, reply
from flask import request

from slacker.utils import BaseBlueprint

bp = BaseBlueprint('sticker', __name__, url_prefix='/sticker')


@bp.route('/add', methods=('GET', 'POST'))
def add_sticker():
    text = request.form.get('text', '')
    user_id = request.form.get('user_id')
    try:
        name, url = text.split()
    except ValueError:
        return command_response('Usage: `/add_sticker mymeme https://i.imgur.com/12345678.png`')

    # Should check if url is reachable, but infosec doesn't allow to reach it
    msg = _add_sticker(user_id, name, url)
    return command_response(msg)


def _add_sticker(author, name, image_url):
    try:
        Sticker.create(author=author, name=name, image_url=image_url)
        msg = f'Sticker `{name}` saved'
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f'Sticker not saved. Args: {name} {image_url}\nException: {repr(e)}')
        msg = f'Something went wrong. Is the sticker name `{name}` taken already?'
    return msg


@bp.route('/send', methods=('GET', 'POST'))
def send_sticker():
    sticker_name = request.form.get('text')
    if not sticker_name:
        resp = command_response('Bad usage. Usage: `/send_sticker sticker_name`')
    else:
        resp = lookup_sticker(sticker_name)

    return resp


def lookup_sticker(sticker_name):
    s = Sticker.find(name=sticker_name)
    if not s:
        msg = f'No sticker found under `{sticker_name}`'
        resp = command_response(msg)
    else:
        resp = sticker_response(s.name, s.image_url)

    return resp


@bp.route('/list', methods=('GET', 'POST'))
def list_stickers():
    stickers = Sticker.query.all()
    if not stickers:
        resp = command_response('No stickers added yet.')
    else:
        header = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*List of stickers*. You can send them with `/sticker <name>`"}
        }
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": sticker.name
                },
                "accessory": {
                    "type": "image",
                    "image_url": sticker.image_url,
                    "alt_text": sticker.name
                }
            } for sticker in stickers
        ]
        blocks.insert(0, header)
        resp = command_response('*Stickers*', blocks=blocks, response_type='ephemeral')

    return resp


@bp.route('/delete', methods=('GET', 'POST'))
def delete_sticker():
    sticker_name = request.form.get('text')
    if not sticker_name:
        return command_response('Bad Usage. /delete_sticker <name>.\n'
                                'Note: Only the original uploader can delete the sticker')

    user_id = request.form.get('user_id')
    sticker = Sticker.query.filter_by(name=sticker_name, author=user_id).one_or_none()
    if not sticker:
        msg = f'No sticker found under `{sticker_name}`. Are you the original uploader?'
    else:
        db.session.delete(sticker)
        msg = f'{sticker_name} deleted :check:'

    return command_response(msg)

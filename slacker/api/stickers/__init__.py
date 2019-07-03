from loguru import logger
from sqlalchemy.exc import IntegrityError

from slacker.models.stickers import Sticker
from slacker.utils import command_response, sticker_response


def sticker_add(name, image_url):
    try:
        Sticker.create(name=name, image_url=image_url)
        msg = f'Sticker `{name}` saved'
    except IntegrityError:
        logger.opt(exception=True).error('Sticker not saved. Args: %s %s' % (name, image_url))
        msg = f'Something went wrong. Is the sticker name `{name}` taken already?'

    return msg


def lookup_sticker(sticker_name):
    s = Sticker.find(name=sticker_name)
    if not s:
        msg = f'No sticker found under `{sticker_name}`'
        resp = command_response(msg)
    else:
        resp = sticker_response(s.name, s.image_url)

    return resp

def delete_sticker(is_owner):
    pass

def show_stickers():
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

def is_valid_format(message):
    """Validates that message has a name and a reachable url"""
    pass
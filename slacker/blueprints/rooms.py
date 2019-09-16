"""
Blueprint to manage rooms functionality
- Find free rooms for meetings
- Get room location
- Show office map
"""
from os import path

from flask import request, make_response
from loguru import logger
from google.auth.transport.requests import Request

from slacker.api.rooms.locations import (
    get_room_location, create_image_from_map, draw_office_map, get_image_dir, OFFICE_MAP
)
from slacker.api.rooms.login import calendar
from slacker.api.rooms.api import get_free_rooms, RoomFinder
from slacker.slack_cli import OviBot
from slacker.tasks_proxy import upload_file_async
from slacker.utils import BaseBlueprint, reply, monospace, reply_text

bp = BaseBlueprint('rooms', __name__, url_prefix='/rooms')


@bp.route('/request_user_consent', methods=('GET', 'POST'))
def get_authorization_url():
    """First step of oauth2 flow"""
    channel = request.form.get('channel_id')
    user = request.form.get('user_id')
    url = calendar.get_authorization_url()
    msg = (
        f'Visit the following url to get the authorization code:\n{url}\n'
        'Then enter the auth code via `/set_token <auth_code>`'
    )
    r = OviBot.chat_postEphemeral(channel=channel, user=user, text=msg)
    if not r['ok']:
        logger.error(f"Auth url not sent to user. Error {r['error']}")
    logger.info(f'Shared authorization url ({url}) with user. Waiting for auth code..')

    return make_response('', 200)


@bp.route('/fetch_token', methods=('GET', 'POST'))
def set_token():
    """Final step of oauth2 flow. Set token for further api requests"""
    form = request.form
    auth_code = form.get('text')
    if not auth_code:
        return reply('Usage: /authorize <my_auth_code>')

    calendar.get_token(code=auth_code)
    logger.debug('fetched token: {}', calendar.credentials.token)

    OviBot.chat_postEphemeral(
        channel=form['channel_id'], user=form['user_id'], text=':check: Success!'
    )
    return make_response('', 200)


@bp.route('/find_free_rooms', methods=('GET', 'POST'))
def find():
    try:
        credentials = calendar.get_credentials()
    except ValueError:
        logger.exception('No token found on session. Have you already authorized the app?')
        return reply('You must first authorize the app')

    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            # Update credentials if they are expired using the refresh token
            credentials.refresh(Request())
        else:
            attrs = [getattr(credentials, attr, None) for attr in dir(credentials)]
            logger.debug(f"Valid credentials but refresh token failed. creds={attrs}")
            return reply('No Credentials for requests. Have you `/authorize`d and `/set_token`?')

    args = request.form.get('text', '').split()
    logger.debug('Find free rooms args: {!r}', args)
    try:
        free_rooms = get_free_rooms(credentials, args)
    except ValueError as e:
        message = monospace(str(e))
    except Exception as e:
        message = f'Unexpected error. {str(e)}'
    else:
        if not free_rooms:
            message = 'No available rooms right now.. Try `/find_free_rooms --all`'
        else:
            message = (
                '_*Available rooms:*_\n'
                f'{free_rooms}\n'
                '_To know the location of a room run_ `/whereis <room_name>`'
            )

    return reply_text(message)


@bp.route('/office_map', methods=('GET', 'POST'))
def room_map():
    """Show room map"""
    channel = request.form.get('channel_id')
    image_path = OFFICE_MAP
    if not path.exists(image_path):
        logger.debug('Building office map..')
        image_path = draw_office_map(image_path)

    logger.debug('Uploading file..')
    task = upload_file_async(image_path,
                             channel=channel,
                             filename='office.png')  # Maybe avoid re-uploading by saving file id.
    logger.debug('Upload office image task sent. {}', task.id)
    return reply_text('Drawing image... :clock4:')


@bp.route('/room_location', methods=('GET', 'POST'))
def locate_room():
    """Show where a room is on the map"""
    channel = request.form.get('channel_id')
    room_name = request.form.get('text')
    if not room_name:
        return reply_text('Specify a room. To show office map run `/office_map`')

    try:
        room = RoomFinder.get_room_by_name(room_name)
    except KeyError:
        return reply_text('Specified room does not exist. Check for typos')

    location_map = get_room_location(room)
    image_path = get_image_dir(f'{room.name}.png')
    logger.debug('PATH: {}', image_path)
    if not path.exists(image_path):
        logger.debug('Generating image for {}', room.name)
        image_path = create_image_from_map(location_map, image_path)
        logger.debug('Image created at {}', image_path)

    logger.debug('Image path to upload: {}', image_path)
    upload_file_async(file=image_path, channel=channel, filename=room.name)
    logger.debug('Image uploaded')
    return reply_text('Locating room.. :mag:')

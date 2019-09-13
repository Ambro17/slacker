from flask import request, make_response
from loguru import logger
from google.auth.transport.requests import Request

from slacker.api.rooms.locations import office_map, get_room_location
from slacker.api.rooms.login import calendar
from slacker.api.rooms.api import get_free_rooms, RoomFinder
from slacker.slack_cli import OviBot
from slacker.utils import BaseBlueprint, reply, reply_raw, monospace, reply_text

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
    logger.debug('cal id {!r}', id(calendar))
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
    free_rooms = get_free_rooms(credentials, args)
    resp = free_rooms + '\n' + "To know the location of a room run `/whereis <room_name>`"

    return reply_raw(resp)


@bp.route('/office_map', methods=('GET', 'POST'))
def room_map():
    """Show room map"""
    return reply_raw(monospace(office_map))


@bp.route('/room_location', methods=('GET', 'POST'))
def locate_room():
    """Show where a room is on the map"""
    room_name = request.form.get('text')
    if not room_name:
        return reply_text('Specify a room. To show office map run `/office_map`')

    try:
        room = RoomFinder.get_room_by_name(room_name)
    except KeyError:
        return reply_text('Specified room does not exist. Check for typos')

    location_map = get_room_location(room)
    return reply_text(monospace(location_map))

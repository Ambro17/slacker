"""
Get available room for meetings.

Usage:
    getaroom.py [--start=START] [--end=END] [--room=ROOM] [--floor=FLOOR] [--all]
    getaroom.py listrooms

Options:
    -h, --help                  Show this screen and exit.
    -s START, --start START     Start date to look for available rooms
    -e END, --end     END       End date to mark a time slot as available
    -r ROOM, --room   ROOM      Room where to find free time slots
    -f ROOM, --floor  FLOOR     Room where to find free time slots
"""
from flask import request, make_response
from loguru import logger
from google.auth.transport.requests import Request

from slacker.api.rooms import calendar
from slacker.api.rooms.api import get_free_rooms
from slacker.slack_cli import OviBot
from slacker.utils import BaseBlueprint, reply

bp = BaseBlueprint('rooms', __name__, url_prefix='/rooms')


@bp.route('/', methods=('GET', 'POST'))
def index():
    # Check if token is active
    return reply({
        'message': 'Is token active?'
    })


@bp.route('/request_user_consent', methods=('GET', 'POST'))
def get_authorization_url():
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
    form = request.form
    auth_code = form.get('text')
    if not auth_code:
        return reply('Usage: /authorize <my_auth_code>')

    calendar.fetch_token(code=auth_code)

    OviBot.chat_postEphemeral(
        channel=form['channel_id'], user=form['user_id'], text=':check: Success!'
    )
    return make_response('', 200)


@bp.route('/find', methods=('GET', 'POST'))
def find():
    credentials = calendar.credentials
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        # Update credentials if they are expired using the refresh token
        credentials.refresh(Request())
    else:
        logger.debug(f"Credentials not set. Valid={credentials.valid}, Expired={credentials.expired}")
        return reply('No Credentials for requests. Have you `/authorize`d and `/set_token`?')

    args = request.form.get('text', '').split()
    free_rooms = get_free_rooms(credentials, args)

    return reply(free_rooms)


@bp.route('/map', methods=('GET', 'POST'))
def room_map():
    """Show room map"""
    pass


@bp.route('/whereis', methods=('GET', 'POST'))
def locate_room():
    """Show where a room is on the map"""
    pass

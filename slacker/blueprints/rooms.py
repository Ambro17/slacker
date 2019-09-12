from flask import request, make_response
from loguru import logger
from google.auth.transport.requests import Request

from slacker.api.rooms import calendar
from slacker.api.rooms.api import get_free_rooms
from slacker.slack_cli import OviBot
from slacker.utils import BaseBlueprint, reply, reply_raw

bp = BaseBlueprint('rooms', __name__, url_prefix='/rooms')


@bp.route('/', methods=('GET', 'POST'))
def index():
    # Check if token is active
    return reply({
        'message': 'Is token active?'
    })


@bp.route('/request_user_consent', methods=('GET', 'POST'))
def get_authorization_url():
    """First step of oauth2 flow"""
    logger.debug('cal id (auth) {!r}', id(calendar))
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
    """Final step of oauth2 flow. Set token for api requests"""
    logger.debug('cal id (token) {!r}', id(calendar))
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


@bp.route('/find', methods=('GET', 'POST'))
def find():
    logger.debug('cal id {!r}', id(calendar))
    try:
        credentials = calendar.get_credentials()
    except ValueError:
        logger.exception('No token found on session. Have you already authorized the app?')
        return reply('First authorize the app')

    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            # Update credentials if they are expired using the refresh token
            credentials.refresh(Request())
        else:
            logger.debug(f"Valid credentials but refresh token failed. Expired={credentials.expired}")
            return reply('No Credentials for requests. Have you `/authorize`d and `/set_token`?')

    args = request.form.get('text', '').split()
    free_rooms = get_free_rooms(credentials, args)

    return reply_raw(free_rooms)


@bp.route('/map', methods=('GET', 'POST'))
def room_map():
    """Show room map"""
    pass


@bp.route('/whereis', methods=('GET', 'POST'))
def locate_room():
    """Show where a room is on the map"""
    pass

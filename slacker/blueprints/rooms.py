"""
Get available room for meetings.
    getaroom.py [-s START] [-e END] [-r ROOM] [-f FLOOR] [--all]
    getaroom.py listrooms
"""
import datetime as dt

import pytz
from flask import request
from loguru import logger
from google.auth.transport.requests import Request

from slacker.api.rooms import CalendarApi
from slacker.api.rooms.api import RoomFinder
from slacker.slack_cli import Slack
from slacker.utils import BaseBlueprint, reply


bp = BaseBlueprint('rooms', __name__, url_prefix='/rooms')

bsas = pytz.timezone('America/Buenos_Aires')


@bp.route('/', methods=('GET', 'POST'))
def index():
    # Check if token is active
    return reply({
        'message': 'Is token active?'
    })


@bp.route('/authorization_url', methods=('GET', 'POST'))
def get_authorization_url():
    channel = request.form.get('channel_id')
    user = request.form.get('user_id')
    url = CalendarApi.get_authorization_url()
    msg = f'Visit the following url to get the authorization code:\n{url}'
    r = Slack.chat_postEphemeral(channel=channel, user=user, text=msg)
    if not r['ok']:
        logger.error(f"Auth url not sent to user. Error {r['error']}")
    logger.info(f'Shared authorization url ({url}) with user. Waiting for auth code..')


@bp.route('/authorize', methods=('GET', 'POST'))
def set_token():
    auth_code = request.form.get('text')
    if not auth_code:
        return reply('Usage: /authorize <my_auth_code>')

    CalendarApi.set_token(auth_code)


@bp.route('/find', methods=('GET', 'POST'))
def find():
    credentials = CalendarApi.credentials
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        # Update credentials if they are expired using the refresh token
        credentials.refresh(Request())
    else:
        logger.debug(f"Credentials not set. Valid={credentials.valid}, Expired={credentials.expired}")
        return reply('No Credentials for requests. Have you `/authorize`d and `/set_token`?')

    start = bsas.fromutc(dt.datetime.utcnow()).replace(microsecond=0)
    end = start.replace(hour=23, minute=59)

    logger.debug(f"Looking for free slots between '{start.isoformat()}' and '{end.isoformat()}'.")

    finder = RoomFinder(credentials)
    response = finder.request_calendars(start.isoformat(), end.isoformat(),
                                        calendars=[{'id': calendar} for calendar in RoomFinder.CALENDARS])

    free_rooms = RoomFinder.get_rooms_free_slots(response['calendars'], start, end)
    pretty_rooms = RoomFinder.format_room_availability(free_rooms)

    return reply(pretty_rooms)

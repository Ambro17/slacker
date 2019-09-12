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
import datetime as dt
from functools import partial

from attr import dataclass
from dateparser import parse
from typing import List, Tuple, Dict
import pytz
from docopt import docopt
from googleapiclient.discovery import build
from loguru import logger
import unidecode

bsas = pytz.timezone('America/Argentina/Buenos_Aires')
parse_date = partial(parse, settings={'TIMEZONE': 'America/Buenos_Aires', 'RETURN_AS_TIMEZONE_AWARE': True})


class RoomDoesNotExist(Exception):
    pass


@dataclass
class Room:
    name: str
    floor: int
    size: str
    capacity: int
    has_tv: bool = True
    has_meet: bool = False
    where: str = ''

    def __str__(self):
        # Boole - Fl. PB - Size: small - Meet? Yes
        floor = f'Fl. {self.floor}' if self.floor else 'PB'
        return f"{self.name.title()} - {floor} - Size: {self.size} - Meet? {'Yes' if self.has_meet else 'No'}"


class RoomFinder:

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    KNUTH = 'onapsis.com_2d3238373435353436323133@resource.calendar.google.com'
    LOVELACE = 'onapsis.com_38313235313930372d343632@resource.calendar.google.com'
    BOOLE = 'onapsis.com_2d34363136313333322d393133@resource.calendar.google.com'
    HUFFMAN = 'onapsis.com_2d34303031303433392d373734@resource.calendar.google.com'
    ANGELA_RUIZ = 'onapsis.com_32353331373635362d363136@resource.calendar.google.com'
    SHANNON = 'onapsis.com_373733373134362d353536@resource.calendar.google.com'
    TURING = 'onapsis.com_2d34313837373335322d393235@resource.calendar.google.com'
    DIFFIE = 'onapsis.com_35323435343435302d313231@resource.calendar.google.com'
    HAMMING = 'onapsis.com_2d38313235333830392d3435@resource.calendar.google.com'
    RITCHIE = 'onapsis.com_34343835323438352d313335@resource.calendar.google.com'
    GODEL = 'onapsis.com_2d383836303836332d383638@resource.calendar.google.com'
    MARIE_CURIE = 'onapsis.com_2d35343234383034373838@resource.calendar.google.com'
    ANITA_BORG = 'onapsis.com_3630363839303534363038@resource.calendar.google.com'

    CALENDARS = {
        KNUTH, LOVELACE, BOOLE, HUFFMAN, ANGELA_RUIZ, SHANNON, TURING,
        DIFFIE, HAMMING, RITCHIE, GODEL, MARIE_CURIE, ANITA_BORG
    }

    ROOMS = {
        # Ground floor
        SHANNON: Room('shannon', 0,  'medium', 6, has_meet=True),
        DIFFIE: Room('diffie', 0, 'small', 5, has_meet=True),
        GODEL: Room('godel', 0, 'small', 5, has_meet=True),
        MARIE_CURIE: Room('marie curie', 0, 'small', 4, has_meet=True),

        # First floor
        KNUTH: Room('knuth', 1, 'small', 4),
        BOOLE: Room('boole', 1, 'small', 4),
        HAMMING: Room('hamming', 1, 'small', 4),
        RITCHIE: Room('ritchie', 1, 'small', 4),
        ANITA_BORG: Room('anita borg', 1, 'small', 5, has_meet=True),
        LOVELACE: Room('lovelace', 1, 'small', 5, has_meet=True),
        HUFFMAN: Room('huffman', 1, 'medium', 6, has_meet=True),

        # Second floor
        ANGELA_RUIZ: Room('angela ruiz', 2, 'big', 8, has_meet=True),
        TURING: Room('turing', 2, 'big', 20, has_meet=True),
    }
    ROOM_IDS_BY_NAME = {room.name: cal_id for cal_id, room in ROOMS.items()}

    @classmethod
    def get_room_by_name(cls, room_name):
        room_id = cls.ROOM_IDS_BY_NAME[cls.normalize(room_name)]
        return cls.ROOMS[room_id]

    @classmethod
    def normalize(cls, name):
        """Replace spaces by underscores and lowercase it"""
        ascii_name = unidecode.unidecode(name)
        return ascii_name.lower()

    def __init__(self, creds):
        self.api = build('calendar', 'v3', credentials=creds)

    def calendar_list(self):
        return self.api.calendarList().list().execute()

    def request_calendars(self, start: str, end: str, tz='America/Buenos_Aires', calendars: List[Dict] = None):
        body = {
            "timeMin": start,
            "timeMax": end,
            "timeZone": tz,
            "items": calendars or [{'id': calendar} for calendar in RoomFinder.CALENDARS]
        }

        return self.api.freebusy().query(body=body).execute()

    @classmethod
    def _get_free_slots(cls,
                        busy_slots: List[dict],
                        start_date: dt.datetime,
                        end_date: dt.datetime) -> Tuple[List[Tuple[dt.datetime, dt.datetime]], bool]:
        """Get free time slots of a calendar by iterating with a cursor over busy time slots."""
        free_slots = []
        cursor = start_date
        for slot in busy_slots:
            start, end = parse(slot['start']), parse(slot['end'])
            if start < start_date or end > end_date:
                # Event does not belong to the current timeframe
                continue
            if cursor < start:
                # There is a free slot until next event starts
                free_slots.append((cursor, start))
                cursor = end
            elif cursor >= start:
                if cursor >= end:
                    # Event has already happened
                    continue
                else:
                    # This time slot is occupied, advance the cursor
                    cursor = end

        if cursor < end_date:
            # There's time left until the end of the day
            free_slots.append((cursor, end_date))

        is_free_now = bool(free_slots) and free_slots[0][0] == start_date

        return free_slots, is_free_now

    @classmethod
    def get_rooms_free_slots(cls,
                             freebusy_resp: dict,
                             start=None,
                             end=None,
                             tz=bsas,
                             skip_occupied_rooms=True,
                             floor_filter=None) -> Dict[str, Dict]:
        """
        Input
        {
          "room_calendar1": {
            "busy": [
              {
                "end": "2019-08-19T12:00:00-03:00",
                "start": "2019-08-19T11:02:10-03:00"
              },
                ...
            ]
          },
          "room_calendar2": {
            "busy": [
              {
                "end": "2019-08-19T15:15:00-03:00",
                "start": "2019-08-19T15:00:00-03:00"
              },
               ...
            ]
          },
          ...
        }
        """
        if start is None:
            start = tz.fromutc(dt.datetime.utcnow())  # Timezone aware .now().
        if end is None:
            end = start.replace(hour=23, minute=59, second=59)

        room_slots = {}
        for room_id, calendar in freebusy_resp.items():
            room = cls.ROOMS[room_id]
            free_slots, is_free_now = cls._get_free_slots(calendar['busy'], start, end)
            if skip_occupied_rooms and not is_free_now:
                continue
            if floor_filter and room.floor != int(floor_filter):
                continue
            room_slots[room.name] = {'room': room,
                                     'slots': free_slots,
                                     'is_free_now': is_free_now,
                                     'details': str(room)}

        return room_slots

    @classmethod
    def format_room_availability(cls, free_rooms):
        return '\n'.join(
            f"{details['details']}\n"
            f"Free: {details['is_free_now'] and 'Yes' or 'No'}\n"
            f"{[f'{s:%H:%M}-{e:%H:%M}' for s, e in details['slots']]}\n"
            for room, details in free_rooms.items()
        )


def get_free_rooms(credentials, args):
    """Get free rooms filtered by optional user args"""
    opt = docopt(__doc__, args)

    now = bsas.fromutc(dt.datetime.utcnow()).replace(microsecond=0)
    start = parse_date(opt['--start']).replace(microsecond=0) if opt['--start'] else now
    end = parse_date(opt['--end']).replace(microsecond=0) if opt['--end'] else start.replace(hour=23, minute=59)

    logger.debug(f"Looking for free slots between '{start.isoformat()}' and '{end.isoformat()}'.")

    finder = RoomFinder(credentials)
    request_calendars = partial(finder.request_calendars, start=start.isoformat(), end=end.isoformat())

    if opt['--room']:
        calendar = RoomFinder.ROOM_IDS_BY_NAME.get(opt['--room'].lower())
        if not calendar:
            raise RoomDoesNotExist(f"Room '{opt['--room']}' doesn't exist. "
                                   f"Options are:\n{list(RoomFinder.ROOM_IDS_BY_NAME.keys())}')")
        calendars = [calendar]
    else:
        calendars = RoomFinder.CALENDARS

    response = request_calendars(calendars=[{'id': calendar} for calendar in calendars])

    skip_occupied_rooms = True if not opt['--all'] else False
    free_rooms = RoomFinder.get_rooms_free_slots(response['calendars'], start, end,
                                                 skip_occupied_rooms=skip_occupied_rooms,
                                                 floor_filter=opt['--floor'])
    pretty_rooms = RoomFinder.format_room_availability(free_rooms)
    return pretty_rooms

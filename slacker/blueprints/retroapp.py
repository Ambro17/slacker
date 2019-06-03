import re

from flask import request, current_app as the_app
from loguru import logger

from slacker.database import db
from slacker.models import get_or_create, Team
from slacker.models.retro.crud import add_team_members
from slacker.models.user import User
from slacker.utils import reply, BaseBlueprint, get_or_create_user_from_response

bp = BaseBlueprint('retro', __name__, url_prefix='/retro')

# Match user_id and user_name unescaped from slack
# i.e: foo <@U1234|john> -> user_id=U1234, name=john
user_id = '(?P<user_id>[^|]+)'
name = '(?P<name>[^>]*)'
USER_REGEX = re.compile(rf'<@{user_id}\|{name}>')


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a retro action.",
        'commands': ['add_team', 'start_sprint', 'add_item', 'show_items', 'end_sprint']
    })


class SlackerException(Exception):
    """Base exception for app exceptions"""


@bp.route('/add_team', methods=('POST', ))
def add_team() -> str:
    text = request.form.get('text')
    if not text:
        return 'Bad usage. i.e /add_team t1 @john @carla'

    def read_team_members(text):
        """
        Args:
            text (str): escaped usernames: "team_name <@U123|john> <@W456|carla>"

        Returns:
            tuple(str, list[dict]): team name and list of user matchdicts
        """
        name, members = text.split(maxsplit=1)
        users = [m.groupdict() for m in USER_REGEX.finditer(members)]
        return name.strip(), users

    def get_user_id_from_members(users):
        user_ids = []
        for u in users:
            resp = the_app.slack_cli.api_call("users.info", user=u['user_id'])  # TODO: Add threading to improve i/o
            try:
                user_id = get_or_create_user_from_response(resp, u['user_id'])
            except Exception as e:
                raise SlackerException("Error creating user from response") from e

            user_ids.append(user_id)

        return user_ids

    team_name, members = read_team_members(text)
    team = get_or_create(db.session, Team, name=team_name)
    user_ids = get_user_id_from_members(members)
    add_team_members(user_ids, team.id)

    members_friendly = ' '.join(m['name'] for m in members)
    return f'Success! {team_name} was created. Members: {members_friendly}'


@bp.route('/start_sprint', methods=('GET', 'POST'))
def start_sprint() -> str:
    # name
    return 'start_sprint'


@bp.route('/add_item', methods=('GET', 'POST'))
def add_item() -> str:
    # item.
    return 'add_item'


@bp.route('/show_items', methods=('GET', 'POST'))
def show_items() -> str:
    # team_id.
    return 'show_items'


@bp.route('/end_sprint', methods=('GET', 'POST'))
def end_sprint() -> str:
    # user + optional team_id.
    return 'end_sprint'

import re

from flask import request, current_app as the_app
from sqlalchemy import func

from slacker.api.retro.retro import start_sprint, add_item, end_sprint
from slacker.database import db
from slacker.models import get_or_create, Team, Sprint, RetroItem
from slacker.models.retro.crud import add_team_members, get_team_members
from slacker.models.user import get_or_create_user
from slacker.utils import reply, BaseBlueprint, format_datetime

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
            user = get_or_create_user(the_app.slack_cli, u['user_id'])
            user_ids.append(user.user_id)

        return user_ids

    team_name, members = read_team_members(text)
    team = get_or_create(db.session, Team, name=team_name)
    user_ids = get_user_id_from_members(members)
    add_team_members(user_ids, team.id)

    members_friendly = ' '.join(m['name'] for m in members)
    return f'Success :check:\n{team_name} was created. Members: {members_friendly}'


@bp.route('/start_sprint', methods=('POST',))
def start_sprint_callback() -> str:
    """Usage: /start_sprint <sprint_name>"""
    sprint_name = request.form.get('text')
    if not sprint_name:
        return 'Bad usage. i.e: /start_sprint <sprint_name>'

    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        start_sprint(sprint_name, user.team.id)
        msg = f"Sprint `{sprint_name}` started :check:"

    return msg


@bp.route('/add_item', methods=('GET', 'POST'))
def add_item_callback() -> str:
    item = request.form.get('text')
    if not item:
        return 'Bad usage. i.e: /add_retro_item <text>'

    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)
    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        sprint = Sprint.query.filter_by(running=True, team_id=team.id).one_or_none()
        if sprint is None:
            msg = "No active sprint"
        else:
            add_item(sprint.id, user.id, user.first_name, item)
            msg = 'Item saved :check:'

    return msg


@bp.route('/show_items', methods=('GET', 'POST'))
def show_items() -> str:
    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)
    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        sprint = Sprint.query.filter_by(running=True, team_id=team.id).one_or_none()
        if sprint is None:
            msg = "No active sprint"
        else:
            items = db.session.query(
                RetroItem.author,
                RetroItem.text,
                RetroItem.datetime
            ).filter_by(sprint_id=sprint.id)
            msg = '\n'.join(f'*{x.author}* | {x.text} | _{format_datetime(x.datetime)}_' for x in items)

    return msg


@bp.route('/end_sprint', methods=('GET', 'POST'))
def end_sprint_callback() -> str:
    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        sprint_name = end_sprint(team.id)
        msg = f"`{sprint_name}'s` watch has ended :check:"

    return msg


@bp.route('/team_members', methods=('POST', ))
def team_members() -> str:
    team_name = request.form.get('text')
    if not team_name:
        user = get_or_create_user(the_app.slack_cli, request.form.get('user_id'))
        if user.team is not None:
            team_name = user.team.name
        else:
            return 'Bad usage. i.e: /team_members <team>'

    team = Team.query.filter_by(name=team_name).one_or_none()
    if team is None:
        msg = f"Team '{team_name}' does not exist"
    else:
        members = get_team_members(team.id)
        msg = f'{team_name} members:\n'
        msg += '\n '.join(f':star: {m.real_name}' for m in members)
    return msg


@bp.route('/help', methods=('POST', ))
def help():
    msg = """
Simple app for managing retroitems.
Teams have members. Add them with `/add_team my_team_name @member1 @member2 ...`
Teams have sprints. Start one with `/start_sprint my first sprint`
Each sprint can have many retro items.\nAdd them with `/add_retro_item we need to improve our estimations`
If you want to see current retro items write `/show_retro_items`
If you have already seen them the retro meeting has ended you can write `/end_sprint` and start over
    """
    return msg

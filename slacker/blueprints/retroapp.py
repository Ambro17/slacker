import re

from flask import request, current_app as the_app
from loguru import logger

from slacker.api.retro.retro import start_sprint, add_item
from slacker.database import db
from slacker.models import get_or_create, Team, Sprint
from slacker.models.retro.crud import add_team_members, get_team_members
from slacker.models.user import User, get_or_create_user
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


@bp.route('/start_sprint', methods=('POST',))
def start_sprint_callback() -> str:
    text = request.form.get('text')
    if not text:
        return 'Bad usage. i.e: /start_sprint <sprint_name>'

    # Check if command was with or without team argument.
    args = text.split()
    if len(args) == 1:
        sprint_name = args[0]
        team_name = None
    elif len(args) == 2:
        sprint_name, team_name = args
    else:
        return 'Bad Usage. `/start_sprint <name>`'

    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    try:
        team_id = user.team.id
    except User.OrphanUserException:
        logger.info('User has no team')
        return 'You are not part of any team yet. `/add_team` before you can start sprints'
    except User.MultipleTeamsException:
        logger.info("User has more than one team")
        if team_name is None:
            return "You did not specify a team. Usage: `/start_sprint <name> <team>`"
        else:
            t = Team.query.filter_by(name=team_name).one_or_none()
            if t is None:
                return "Team %s does not exist" % team_name
            else:
                team_id = t.id

    start_sprint(sprint_name, team_id)
    return f"Sprint `{sprint_name}` started :check:"


@bp.route('/add_item', methods=('GET', 'POST'))
def add_item_callback() -> str:
    text = request.form.get('text')
    if not text:
        return 'Bad usage. i.e: /add_retro_item <text>'

    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    # Check if command was with or without team argument.
    args = text.split('-')
    if len(args) == 1:
        item = args[0]
        team_name = None
    elif len(args) == 2:
        item, team_name = args[0], args[1].strip()
    else:
        return 'Bad Usage. `/add_retro_item <text>`'

    try:
        team = user.team
    except User.OrphanUserException:
        logger.info(f'User {user_id} has no team')
        return 'You are not part of any team yet. `/add_team` before you can add items'

    except User.MultipleTeamsException:
        logger.info(f"User {user_id} has more than one team")
        if team_name is None:
            return "You did not specify a team. Usage: `/add_retro_item <text> - <team>`"
        else:
            team = Team.query.filter_by(name=team_name).one_or_none()
            if team is None:
                return f"Team {team_name} does not exist"

    sprint = Sprint.query.filter_by(running=True, team_id=team.id).one_or_none()
    if sprint is None:
        return "No active sprint"

    add_item(sprint.id, user.id, item)

    return 'Item saved :check:'


@bp.route('/show_items', methods=('GET', 'POST'))
def show_items() -> str:
    user_id = request.form.get('user_id')
    user = get_or_create_user(the_app.slack_cli, user_id)

    return 'show_items'


@bp.route('/end_sprint', methods=('GET', 'POST'))
def end_sprint() -> str:
    # user + optional team_id.
    return 'end_sprint'


@bp.route('/team_members', methods=('POST', ))
def team_members() -> str:
    team_name = request.form.get('text')
    if not team_name:
        return 'Bad usage. i.e: /team_members <team>'

    team = Team.query.filter_by(name=team_name).one_or_none()
    if team is None:
        msg = f"Team {team_name} does not exist"
    else:
        members = get_team_members(team.id)
        msg = f'{team_name} members:\n'
        msg += ' '.join(m.real_name for m in members)
    return msg

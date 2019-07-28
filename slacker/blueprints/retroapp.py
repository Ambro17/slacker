import re
import traceback

from flask import request
from loguru import logger

from slacker.slack_cli import slack_cli
from slacker.api.retro.retro import start_sprint, add_item, end_sprint
from slacker.database import db
from slacker.exceptions import RetroAppException
from slacker.models import Team, Sprint, RetroItem
from slacker.models.model_utils import get_or_create
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


@bp.route('/add_team', methods=('POST', ))
def add_team() -> str:
    text = request.form.get('text')
    if not text:
        return 'Bad usage. i.e `/add_team t1 @john @carla`'

    def read_team_members(text):
        """
        Args:
            text (str): escaped usernames: "team_name <@U123|john> <@W456|carla>"

        Returns:
            tuple(str, list[dict]): team name and list of user matchdicts
        """
        name, members = text.split(maxsplit=1)
        users = [m.groupdict() for m in USER_REGEX.finditer(members)]
        return name.strip().upper(), users

    def get_user_id_from_members(users):
        user_ids = []
        for u in users:
            user = get_or_create_user(slack_cli, u['user_id'])
            user_ids.append(user.user_id)

        return user_ids

    try:
        team_name, members = read_team_members(text)
    except ValueError:
        return ':no_entry_sign: Bad usage. Specify team name and members: `/add_team team_name @member1 @member2`'

    team = get_or_create(db.session, Team, name=team_name)
    user_ids = get_user_id_from_members(members)

    if not user_ids:
        return ':no_entry_sign: Bad usage. You must add at least one member (tag them with @username)'

    add_team_members(user_ids, team.id)

    members_friendly = ' '.join(m['name'] for m in members)
    return f'Success :check:\n`{team_name}` team was created. Members: {members_friendly}'


@bp.route('/start_sprint', methods=('POST',))
def start_sprint_callback() -> str:
    """Usage: /start_sprint <sprint_name>"""
    sprint_name = request.form.get('text')
    if not sprint_name:
        return 'Bad usage. Usage: `/start_sprint <sprint_name>`'

    user_id = request.form.get('user_id')
    user = get_or_create_user(slack_cli, user_id)

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
        return 'Bad usage. Usage: `/add_retro_item <text>`'

    user_id = request.form.get('user_id')
    user = get_or_create_user(slack_cli, user_id)
    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        sprint = Sprint.query.filter_by(running=True, team_id=team.id).one_or_none()
        if sprint is None:
            msg = "No active sprint. Start one to store new retro items"
        else:
            add_item(sprint.id, user.id, user.first_name, item)
            msg = 'Item saved :check:'

    return msg


@bp.route('/show_items', methods=('GET', 'POST'))
def show_items() -> str:
    user_id = request.form.get('user_id')
    user = get_or_create_user(slack_cli, user_id)
    team = user.team
    if team is None:
        msg = "You are not part of any team. Action not allowed"
    else:
        sprint = Sprint.query.filter_by(running=True, team_id=team.id).one_or_none()
        if sprint is None:
            msg = "There's no active sprint. Start one to store and show retro items"
        else:
            items = db.session.query(
                RetroItem.author,
                RetroItem.text,
                RetroItem.datetime
            ).filter_by(sprint_id=sprint.id).all()
            if not items:
                msg = 'No saved items yet'
            else:
                msg = f'`{sprint.name.capitalize()}` items:\n'
                msg += '\n'.join(f'*{x.author}* | {x.text} | _{format_datetime(x.datetime)}_' for x in items)

    return msg


@bp.route('/end_sprint', methods=('GET', 'POST'))
def end_sprint_callback() -> str:
    user_id = request.form.get('user_id')
    user = get_or_create_user(slack_cli, user_id)

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
        user = get_or_create_user(slack_cli, request.form.get('user_id'))
        if user.team is not None:
            team_name = user.team.name
        else:
            return 'Bad usage. Usage: `/team_members <team>`'

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
Teams have members. Add them with `/add_team my_team_name @member1 @member2 ...`
Teams have sprints. Start one with `/start_sprint my first sprint`
Each sprint can have many retro items,\nadd them with `/add_retro_item we need to improve our estimations`
If you want to see current retro items write `/show_retro_items`
If you have already seen them the retro meeting has ended you can write `/end_sprint` and start over
    """
    return msg


@bp.errorhandler(400)
def not_found(error):
    return reply({'text': 'Bad request'})


@bp.errorhandler(404)
def not_found(error):
    return reply({'text': 'Resource not found'})


@bp.errorhandler(500)
def not_found(error):
    if isinstance(error, RetroAppException):
        # Handle expected exception (a little bit of an oximoron)
        resp = {'text': f':anger:  {str(error)}'}
    else:
        exception_text = traceback.format_exc()
        logger.error(f'Error: {repr(error)}\nTraceback:\n{exception_text}')
        resp = {
            'text': f'You hurt the bot :face_with_head_bandage:.. Be gentle when speaking with him.\n'
                    f'Error: `{repr(error)}`'
        }

    return reply(resp)

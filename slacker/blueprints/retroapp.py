import re

from flask import request, current_app as the_app
from loguru import logger

from slacker.database import db
from slacker.models import get_or_create, Team
from slacker.models.retro.crud import add_team_members
from slacker.models.user import User
from slacker.utils import reply, BaseBlueprint

bp = BaseBlueprint('retro', __name__, url_prefix='/retro')

# Match user_id and user_name unescaped from slack
# i.e: foo <@U1234|john> -> user_id=1234, name=john
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
        return 'Bad usage. i.e /add_team t1 @john @carla'

    def read_team_members(text):
        name, members = text.split(maxsplit=1)
        users = [m.groupdict() for m in USER_REGEX.finditer(members)]
        return name.strip(), users

    def get_members_ids(users):
        user_ids = []
        for u in users:
            resp = the_app.slack_cli.api_call("users.info", user=u['user_id'])  # TODO: Add threading to improve i/o
            # wait
            if not resp['ok']:
                raise Exception("Error getting info for %s" % u['user_id'])

            user = resp['user']
            u = db.session.query(User).filter_by(user_id=user['id']).one_or_none()
            if u is None:
                try:
                    new_user = User.from_json(user)
                    db.session.add(new_user)
                except Exception:
                    logger.opt(exception=True).error('Error adding user from %s', resp)
                else:
                    db.session.commit()
                    user_ids.append(new_user.id)
                    logger.info('User %s added to db', user['id'])
            else:
                user_ids.append(u.id)

        return user_ids

    team_name, members = read_team_members(text)
    team = get_or_create(db.session, Team, name=team_name)
    user_ids = get_members_ids(members)
    add_team_members(user_ids, team.id)

    return 'Success!'


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

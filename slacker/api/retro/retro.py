from datetime import datetime as d

from loguru import logger

from slacker import db, User
from slacker.models import Sprint, Team, RetroItem

S = db.session


class TeamNotFoundException(Exception):
    """No team found under the required parameters"""


class MultipleActiveSprintsException(Exception):
    """More than one sprint active. Scrum specifies one sprint at a time"""


def add_team(name, users):
    users = _build_users_from_mentions(users)
    team = Team(name=name, members=users)
    S.add(team)
    S.commit()
    return team.id


def _build_users_from_mentions(users):

    def build_user(u):
        return u

    return [build_user(u) for u in users]


def start_sprint(name, team_id):
    team = Team.query.filter_by(id=team_id).one_or_none()
    if team is None:
        raise TeamNotFoundException("No team with id %r" % team_id)

    sprint_query = Sprint.query.filter_by(team_id=team_id, running=True)
    active_sprint = S.query(sprint_query.exists()).scalar()
    if active_sprint:
        raise MultipleActiveSprintsException(
            "There can only be one active sprint per team at a time"
        )

    sprint = Sprint(
        name=name,
        start_date=d.utcnow(),
        team_id=team.id,
    )
    S.add(sprint)
    S.commit()
    return sprint.id


def end_sprint(name):
    sprint = _get_sprint(name=name)
    sprint.running = False
    S.commit()
    return sprint.id


def add_item(sprint_id, user_id, text):
    sprint = _get_sprint(id=sprint_id)
    item = RetroItem(
        user_id=user_id,
        text=text,
        datetime=d.utcnow(),
        sprint_id=sprint.id,
    )
    S.add(item)
    S.commit()
    return item.id


def get_retro_items(sprint_id):
    sprint = _get_sprint(id=sprint_id)
    items = RetroItem.query.filter_by(sprint_id=sprint.id).all()
    return items


class SprintNotFoundException(Exception):
    """Raised when we try to reference a sprint that doesn't exist"""


class InactiveSprintException(Exception):
    """There's no active sprint to apply this action to"""


def _get_sprint(**kwargs):
    sprint = S.query(Sprint).filter_by(**kwargs).one_or_none()
    if sprint is None:
        raise SprintNotFoundException("Sprint %r does not exist." % kwargs)
    if sprint.running is False:
        raise InactiveSprintException(
            "No active sprint with specified parameters %r" % kwargs
        )
    return sprint

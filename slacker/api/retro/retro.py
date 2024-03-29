from datetime import datetime as d

from slacker.database import db
from slacker.exceptions import RetroAppException
from slacker.models import Sprint, Team, RetroItem, User

S = db.session


class TeamNotFoundException(RetroAppException):
    """No team found under the required parameters"""


class MultipleActiveSprintsException(RetroAppException):
    """More than one sprint active. Scrum specifies one sprint at a time"""


def start_sprint(name, team_id):
    team = Team.query.filter_by(id=team_id).one_or_none()
    if team is None:
        raise TeamNotFoundException("No team with id %r" % team_id)

    sprint_query = Sprint.query.filter_by(team_id=team_id, running=True)
    active_sprint = S.query(sprint_query.exists()).scalar()
    if active_sprint:
        raise MultipleActiveSprintsException(
            "There can only be one active sprint per team at a time. End the current sprint before starting a new one."
        )

    sprint = Sprint(
        name=name,
        start_date=d.utcnow(),
        team_id=team.id,
    )
    S.add(sprint)
    S.commit()
    return sprint.id


def end_sprint(team_id):
    sprint = _get_sprint(team_id=team_id, running=True)
    sprint.running = False
    S.commit()
    return sprint.name


def add_item(sprint_id, user_id, user_name, text):
    sprint = _get_sprint(id=sprint_id)
    item = RetroItem(
        author_id=user_id,
        author=user_name,
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


class SprintNotFoundException(RetroAppException):
    """Raised when we try to reference a sprint that doesn't exist"""


class InactiveSprintException(RetroAppException):
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

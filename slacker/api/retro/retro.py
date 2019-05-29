from datetime import datetime as d

from slacker.database import S
from models import Sprint, Team, RetroItem


def start_sprint(name, team):
    sprint = Sprint.query.filter_by(team=team, running=True).one_or_none()
    if sprint is not None:
        return "Can't start sprint if there's already one in progress."

    the_team = Team.query.filter_by(name=team).one_or_none()
    if the_team is None:
        return 'Non-existing team'

    sprint = Sprint(
        name=name,
        start_date=d.utcnow(),
        team_id=the_team.id,  # Maybe look team id by user id and team information.
    )
    S.add(sprint)
    S.commit()


def add_item(user, text):
    sprint = Sprint.query.filter_by(running=True, team=user.team).one_or_none()
    S.add(
        RetroItem(
            user=user,
            text=text,
            datetime=d.now(),
            sprint_id=sprint.id,
        )
    )
    S.commit()


def show_items():
    items = RetroItem.query.filter_by(expired=False).all()
    return items


def end_sprint(name):
    sprint = Sprint.query.filter_by(name=name).one_or_none()
    if sprint:
        if sprint.running:
            sprint.running = False
            S.commit()
        else:
            'sprint already stopped'

    else:
        'inexistent sprint name'

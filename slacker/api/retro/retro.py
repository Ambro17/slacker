from datetime import datetime as d

from sqlalchemy import exists

from slacker import db
from slacker.models import Sprint, Team, RetroItem

S = db.session

def start_sprint(name, team_id):
    the_team = Team.query.filter_by(id=team_id).one_or_none()
    if the_team is None:
        return 'Non-existing team'

    sprint_q = Sprint.query.filter_by(team_id=team_id, running=True)
    active_sprint = S.query(sprint_q.exists()).scalar()
    if active_sprint:
        return "Can't start sprint if there's already one in progress."

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

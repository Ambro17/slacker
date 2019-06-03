from slacker import db
from slacker.models import Member, get_or_create


def add_team_member(user_id, team_id):
    member = get_or_create(db.session, Member, user_id=user_id, team_id=team_id)
    db.session.add(member)
    db.session.commit()


def add_team_members(user_ids, team_id):
    for user_id in user_ids:
        add_team_member(user_id, team_id)

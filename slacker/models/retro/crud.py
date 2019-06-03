from slacker.database import db
from slacker.models.user import User, get_or_create_user


def add_team_member(user_id, team_id):
    user = db.session.query(User).filter_by(user_id=user_id).one_or_none()
    user.team_id = team_id
    db.session.add(user)
    db.session.commit()


def add_team_members(user_ids, team_id):
    for user_id in user_ids:
        add_team_member(user_id, team_id)


def get_team_members(team_id):
    users = db.session.query(User).filter_by(team_id=team_id).all()
    return users

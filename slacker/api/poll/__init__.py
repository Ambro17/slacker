from slacker.models import Vote


def user_has_voted(user_id, poll_id):
    return Vote.query.filter_by(user_id=user_id, poll_id=poll_id).scalar() is not None
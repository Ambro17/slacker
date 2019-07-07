from slacker.models import Vote


def user_has_voted(user_id, poll_id):
    """Assumes that a valid poll and user are passed and determines whether a user has already voted on said poll"""
    return Vote.query.filter_by(user_id=user_id, poll_id=poll_id).scalar() is not None
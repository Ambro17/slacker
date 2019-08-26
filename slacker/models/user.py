import os

from loguru import logger
from sqlalchemy.ext.hybrid import hybrid_property

from slacker.security import Crypto
from slacker.database import db
from slacker.exceptions import SlackerException
from slacker.slack_cli import Slack


class ResponseNotOkException(SlackerException):
    """Raised when a call to slack api returned a non-ok status"""


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    real_name = db.Column(db.String)
    display_name = db.Column(db.String)
    timezone = db.Column(db.String)

    ovi_name = db.Column(db.String)
    _ovi_token = db.Column(db.LargeBinary)

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', back_populates='members')

    @property
    def ovi_token(self):
        """Read token from bytes to str"""
        if not self._ovi_token:
            return None

        return Crypto.decrypt(self._ovi_token)

    @ovi_token.setter
    def ovi_token(self, plain_token: str):
        """Save token as bytes"""
        self._ovi_token = Crypto.encrypt(plain_token)

    @property
    def sprint(self):
        if self.team:
            return self.team.active_sprint
        else:
            return None

    def __repr__(self):
        return f"User(id={self.id!r}, user={self.user_id})"

    def __str__(self):
        if self.real_name:
            return f"{self.real_name}"
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name or 'Unknown'

    @classmethod
    def from_json(cls, user_resp):
        """Flattens slack users.info json response and builds a user from it"""
        # Flatten profile keys
        user_resp.update(user_resp['profile'])

        raw_user = dict(
            user_id=user_resp['id'],
            first_name=user_resp.get('first_name'),
            last_name=user_resp.get('last_name'),
            real_name=user_resp.get('real_name'),
            display_name=user_resp.get('display_name'),
            timezone=user_resp.get('timezone'),
        )
        return User(**raw_user)


def get_or_create_user(cli, user_id):
    """Returns the user_id, creating it if necessary"""
    logger.debug("Get or create user")
    user = db.session.query(User).filter_by(user_id=user_id).one_or_none()
    if user is not None:
        logger.debug(f"User {user.real_name} already exists")
        return user

    logger.debug("User didn't exist. Requesting user info")
    resp = Slack.users_info(user=user_id)
    if resp['ok']:
        logger.debug("Info obtained")
        new_user = User.from_json(resp['user'])
        db.session.add(new_user)
    else:
        logger.debug(f"Error requestion user info.\n{resp}")
        raise ResponseNotOkException("Slack api did not respond OK when requesting user info")

    return new_user

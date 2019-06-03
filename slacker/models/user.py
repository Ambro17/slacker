from loguru import logger

from slacker.database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    real_name = db.Column(db.String)
    display_name = db.Column(db.String)
    timezone = db.Column(db.String)

    ovi_name = db.Column(db.String)
    ovi_token = db.Column(db.String)

    teams = db.relationship(
        "Team",
        secondary='member',
        back_populates='members'
    )

    @property
    def team(self):
        """Returns the team of the user.

        * or None if it hasn't one
        * or ValueError if s/he has more than one
        """
        team_quantity = len(self.teams)
        if team_quantity == 1:
            return self.teams[0]
        elif team_quantity == 0:
            raise self.OrphanUserException(
                'User (%r, %r) has no team!' % (self.user_id, self.first_name)
            )
        else:
            raise self.MultipleTeamsException(
                'User is member of more than one team. %s' %
                [str(t) for t in self.teams]
            )

    @property
    def sprint(self):
        try:
            return self.team.active_sprint
        except (self.OrphanUserException, self.MultipleTeamsException):
            return None
        except Exception:
            logger.opt(exception=True).error('Error getting user sprint')
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
            user_id=user_resp.get('id'),
            first_name=user_resp.get('first_name'),
            last_name=user_resp.get('last_name'),
            real_name=user_resp.get('real_name'),
            timezone=user_resp.get('timezone'),
        )
        return User(**raw_user)

    @classmethod
    def flatten_user(cls):
        """unnest profile key """
        pass

    class MultipleTeamsException(Exception):
        """Exception raised when tried to use .team property but multiple teams exist"""

    class OrphanUserException(Exception):
        """Exception raised when a user is not member of any team"""

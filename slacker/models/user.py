from slacker.database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    real_name = db.Column(db.String)
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
            return None
        else:
            raise ValueError(
                'User is member of more than one team. %s' %
                [str(t) for t in self.teams]
            )

    def __repr__(self):
        return f"User(id={self.id!r}, user={self.user})"

    def __str__(self):
        if self.real_name:
            return f"{self.real_name}"
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name or 'Unknown'

    @classmethod
    def from_json(cls, raw_user, **kwargs):
        raw_user = dict(
            user=raw_user.get('id'),
            first_name=raw_user.get('first_name'),
            last_name=raw_user.get('last_name'),
            real_name=raw_user.get('real_name'),
            timezone=raw_user.get('timezone'),
        )
        raw_user.update(kwargs)
        return User(**raw_user)

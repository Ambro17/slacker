"""
Models to support sprints with retroitems
         .---------.
         |  Team   |
         |---------|
         |+id      |
         |+name    |
         `---------`
              1
              |
              |
    .---------+----------.
    |                    |
    *                    *
,--------.         ,------------.
|  User  |         |    Sprint  |
|--------|         |------------|
|+id     |         |+ id        |
|+name   |         |+ name      |
|+team_id|         |+ start_date|
`--------`         `------------`
    1                     1
    |                     |
    |                     *
    |               ,------------.
    |               |  RetroItem |
    |               |------------|
    |               |+text       |
    `------------ 1 |+user_id    |
                    |+sprint_id  |
                    |+date       |
                    `------------`

+ Powered by http://www.plantuml.com/plantuml/uml/
"""
from slacker.database import db


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    sprints = db.relationship("Sprint", backref='team')
    members = db.relationship(
        "User",
        secondary='member',
        back_populates='teams',
    )

    @property
    def active_sprint(self):
        return next((s for s in self.sprints if s.running is True), None)


class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, unique=True)
    start_date = db.Column(db.TIMESTAMP(timezone=True))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    running = db.Column(db.Boolean, default=True)

    retro_items = db.relationship("RetroItem", backref='sprint')


class RetroItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.String)
    datetime = db.Column(db.TIMESTAMP(timezone=True))

    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id'))

    @property
    def expired(self):
        return self.sprint.running is False

    @property
    def team(self):
        return self.sprint.team

    def __repr__(self):
        return "RetroItem(user_id='%s', text='%s', datetime='%s', sprint_id='%s')" % (
            self.user_id,
            self.text,
            self.datetime,
            self.sprint_id,
        )


class Member(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)

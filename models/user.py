from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    user = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    real_name = Column(String)
    timezone = Column(String)

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

from .user import User
from .retro import RetroItem, Team, Sprint
from .aws import VM, OwnedVM


def get_or_create(S, Model, **kwargs):
    instance = S.query(Model).filter_by(**kwargs).one_or_none()
    if instance is None:
        instance = Model(**kwargs)
        S.add(instance)
        S.commit()

    return instance

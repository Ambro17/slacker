from slacker.database import db
from .user import User
from .retro import RetroItem, Team, Sprint
from .aws import VM, VMOwnership


def get_or_create(S, Model, **kwargs):
    instance = S.query(Model).filter_by(**kwargs).one_or_none()
    if instance is None:
        instance = Model(**kwargs)
        S.add(instance)
        S.commit()

    return instance


class CRUDMixin(object):
    """CRUD Mixin to be used with flask-sqlalchemy to keep it DRY on models."""
    __table_args__ = {'extend_existing': True}

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def find(cls, **kwargs):
        """
        Find an object in the database with certain properties.
        Args:
	        kwargs (dict): the values of the object to find
	    Returns:
	    	the object that was found, or else None
        """

        return cls.query.filter_by(**kwargs).first()

    def update(self, commit=True, **kwargs):
        """
        Update this object with new values.
        Args:
            commit (boolean): to commit or not to commit
            kwargs (dict): the values of the object to update

        Returns:
            the object that was updated
        """

        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()

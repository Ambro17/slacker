from datetime import datetime

import factory.fuzzy
from factory.alchemy import SQLAlchemyModelFactory

from slacker.database import db
from slacker.models.aws import VM, VMOwnership
from slacker.models.retro import Sprint, Team, RetroItem
from slacker.models.user import User


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""
        abstract = True
        sqlalchemy_session = db.session


class TeamFactory(BaseFactory):
    class Meta:
        model = Team

    id = factory.sequence(lambda n: n + 1)
    name = factory.Faker('first_name')

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for member in extracted:
                self.members.append(member)


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.sequence(lambda n: n + 1)
    user_id = factory.sequence(lambda n: f'U{n}' )
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    team = factory.SubFactory(TeamFactory)


class SprintFactory(BaseFactory):
    class Meta:
        model = Sprint

    id = factory.sequence(lambda n: n + 1)
    name = factory.Faker('first_name')
    start_date = factory.LazyFunction(datetime.now)
    team = factory.SubFactory(TeamFactory)
    running = True
    retro_items = []


class RetroItemFactory(BaseFactory):
    class Meta:
        model = RetroItem

    id = factory.sequence(lambda n: n + 1)
    text = factory.fuzzy.FuzzyText()
    sprint = factory.SubFactory(SprintFactory)


class VMFactory(BaseFactory):
    class Meta:
        model = VM

    id = factory.fuzzy.FuzzyText(length=20)


class OwnedVMFactory(BaseFactory):
    class Meta:
        model = VMOwnership

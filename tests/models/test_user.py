from datetime import datetime as d

import pytest
from cryptography.fernet import Fernet

from slacker.models import User, Team, RetroItem
from slacker.security import Encrypter, Crypto
from tests.factorium import UserFactory, TeamFactory, SprintFactory, RetroItemFactory, VMFactory, VMOwnershipFactory


def test_create_user(db):
    """Test user factory."""
    user = UserFactory(first_name='juan', last_name='perez', team=None)
    assert User.query.one() is user
    assert user.first_name == 'juan'
    assert user.last_name == 'perez'
    assert user.team is None

    team = TeamFactory(members=(user,))
    assert user.team == team


def test_create_team(db):
    """Test user factory."""
    team = TeamFactory(name='t3')
    assert Team.query.one() is team
    assert team.name == 't3'
    assert not team.sprints
    assert not team.members

    u = UserFactory(team=team)
    assert u in team.members

    s = SprintFactory(team=team)
    assert s in team.sprints


def test_create_sprint(db):
    now = d.now()
    sprint = SprintFactory(name='marzo', start_date=now)
    assert sprint.name == 'marzo'
    assert sprint.start_date == now
    assert sprint.team
    assert sprint.running

    assert not sprint.retro_items
    retro_item = RetroItemFactory(text='queja', sprint=sprint)
    assert retro_item in sprint.retro_items
    assert retro_item.team == sprint.team


def test_create_retro_item(db):
    ri = RetroItemFactory(text='larala')
    assert RetroItem.query.one() is ri
    assert ri.text == 'larala'
    assert ri in ri.sprint.retro_items


def test_user_cant_have_two_teams(db):
    T1 = TeamFactory()

    U1 = UserFactory(team=None)
    assert U1.team is None

    U1.team = T1
    assert U1 in T1.members


def test_user_can_have_many_vms(db):
    user = UserFactory()
    vm = VMFactory()
    vm_2 = VMFactory()

    my_vm = VMOwnershipFactory(user=user, vm=vm)
    my_other_vm = VMOwnershipFactory(user=user, vm=vm_2)
    db.session.flush()

    assert len(user.owned_vms) == 2
    assert my_vm in user.owned_vms
    assert my_other_vm in user.owned_vms


def test_user_cant_set_ovi_token_without_secrets(db):
    user = UserFactory()
    assert user.ovi_token is None  # By default ovi_token is None (field is optional)

    # Assert ovi_token setter fails if Crypto was not configured (doesn't have a cypher key)
    Crypto.cypher = None
    with pytest.raises(ValueError, match='Encrypter not configured'):
        user.ovi_token = '123'

    # Configure encrypter with secret
    Crypto.configure(Fernet.generate_key())

    # Now the setter should work
    user.ovi_token = '123'
    assert user.ovi_token == '123'

    # And the private attribute should have an encrypted value
    assert type(user._ovi_token) == bytes
    assert str(user._ovi_token) != '123'


def test_user_ovi_token_setter_with_secrets_provided(db, crypto):
    user = UserFactory()
    assert user.ovi_token is None  # By default ovi_token is None (field is optional)
    user.ovi_token = '00123'
    assert user.ovi_token == '00123'
    assert str(user._ovi_token) != '00123'


def test_add_user_with_ovi_token_as_bytes(db, crypto):
    user = UserFactory()
    user.ovi_token = 'ABC123'

    db.session.add(user)

    users = db.session.query(User).all()
    assert len(users) == 1, "A test has left a user created as a side-effect"
    assert users[0].id == user.id

from datetime import datetime as d

from slacker.models.retro import Team, RetroItem
from slacker.models.user import User
from tests.factorium import (
    UserFactory,
    TeamFactory,
    RetroItemFactory,
    SprintFactory,
    VMFactory,
    VMOwnershipFactory,
)


def test_index(client):
    response = client.get('/')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {
        'error': 'You must specify a command.',
        'commands': ['feriados', 'hoypido', 'subte'],
    }


def test_retro_index(client):
    response = client.get('/retro')

    expected_response = {
        'error': "You must specify a retro action.",
        'commands': [
            'add_team', 'start_sprint', 'add_item', 'show_items', 'end_sprint'
        ]
    }

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == expected_response

    response = client.get('/retro/')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == expected_response


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

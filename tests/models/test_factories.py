from datetime import datetime as d

import pytest

from slacker.models.retro import Team, RetroItem
from slacker.models.user import User
from tests.factorium import UserFactory, TeamFactory, RetroItemFactory, SprintFactory, MemberFactory


def test_index(client):
    response = client.get('/')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {
        'error': 'You must specify a command.',
        'commands': ['feriados', 'hoypido', 'subte'],
    }


def test_create_user(db):
    """Test user factory."""
    user = UserFactory(first_name='juan', last_name='perez')
    assert User.query.one() is user
    assert user.first_name == 'juan'
    assert user.last_name == 'perez'
    assert user.teams == []

    team = TeamFactory(members=(user,))
    assert user.teams == [team]
    # Test shortcut when user has only one team
    assert user.team == team



def test_create_team(db):
    """Test user factory."""
    team = TeamFactory(name='t3')
    assert Team.query.one() is team
    assert team.name == 't3'
    assert not team.sprints
    assert not team.members

    u = UserFactory(teams=(team,))
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


def test_user_has_one_or_more_teams(db):
    T1 = TeamFactory()
    T2 = TeamFactory()
    U1 = UserFactory(teams=(T1, T2))
    U2 = UserFactory()

    assert U2.team is None
    with pytest.raises(ValueError,
                       match='User is member of more than one team'):
        U1.team

    assert U1 in T1.members
    assert U1 in T2.members

    U3 = UserFactory()
    U4 = UserFactory()
    T3 = TeamFactory(members=(U3, U4))

    assert U3 in T3.members
    assert U4 in T3.members

    assert U3.team == T3
    assert U4.team == T3
import pytest

from slacker.api.retro.retro import (
    start_sprint,
    end_sprint,
    add_item,
    InactiveSprintException,
    get_retro_items,
    SprintNotFoundException)
from slacker.models import Sprint, RetroItem


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
            'save_team', 'start_sprint', 'add_item', 'show_items', 'end_sprint'
        ]
    }

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == expected_response

    response = client.get('/retro/')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == expected_response


def test_start_sprint(db, f):
    t = f.TeamFactory()
    sprint_id = start_sprint('test sprint', t.id)
    db_sprint = Sprint.query.one()
    assert sprint_id == db_sprint.id


def test_end_sprint(db, f):
    team = f.TeamFactory()
    sprint_id = start_sprint('test sprint', team.id)
    db_sprint = Sprint.query.one()
    assert sprint_id == db_sprint.id

    end_sprint(team.id)
    db_sprint = Sprint.query.get(sprint_id)
    assert db_sprint is not None
    assert db_sprint.running is False


def test_add_retroitem(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(team=team)

    sprint_id = start_sprint('test sprint', team.id)
    item_id = add_item(user.sprint.id, user.id, user.real_name, 'hay que mejorar los tests')
    item_id2 = add_item(user.sprint.id, user.id, user.real_name, 'hay que empezar a hacer TDD')

    S = db.session
    db_items = S.query(RetroItem.id).filter_by(sprint_id=sprint_id).all()
    assert sorted((item_id, item_id2)) == sorted([item for item, in db_items])


def test_add_retroitem_fails_if_no_active_sprint(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(team=team)

    assert user.sprint is None
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'id'"):
        add_item(user.sprint.id, user.id, user.real_name, 'foo')


def test_add_retroitem_fails_if_expired_sprint(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(team=team)
    sprint = f.SprintFactory(team=team, running=False)

    with pytest.raises(InactiveSprintException,
                       match="No active sprint with specified parameters"):
        add_item(sprint.id, user.id, user.real_name, 'foo')


def test_add_retroitem_fails_if_bad_sprint_id(db, f):
    user = f.UserFactory()

    _id_ = 1
    with pytest.raises(SprintNotFoundException,
                       match="Sprint .* does not exist."):
        add_item(_id_, user.id, user.real_name, 'foo')


def test_show_retroitems_per_team(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(team=team)
    spid = start_sprint('test sprint', team.id)

    item_id_1 = add_item(user.sprint.id, user.id, user.real_name, 'un item')
    item_id_2 = add_item(user.sprint.id, user.id, user.real_name, 'otro item')
    item_id_3 = add_item(user.sprint.id, user.id, user.real_name, 'otro más')

    items = get_retro_items(spid)
    items_ids = [item.id for item in items]
    assert sorted([item_id_1, item_id_2, item_id_3]) == sorted(items_ids)


def test_cant_have_two_active_sprints(db, f):
    team = f.TeamFactory()
    f.UserFactory(team=team)
    f.SprintFactory(team=team, name='sprint name')

    sp = Sprint.query.one_or_none()
    assert sp is not None
    assert sp.running is True

    end_sprint(team.id)

    sp = Sprint.query.one_or_none()
    assert sp is not None
    assert sp.running is False

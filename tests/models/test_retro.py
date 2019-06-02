import re

import pytest

from slacker.api.retro.retro import (
    start_sprint,
    end_sprint,
    add_item,
    InactiveSprintException,
    get_retro_items,
    SprintNotFoundException)
from slacker.models import Sprint, RetroItem


def test_start_sprint(db, f):
    t = f.TeamFactory()
    sprint_id = start_sprint('test sprint', t.id)
    db_sprint = Sprint.query.one()
    assert sprint_id == db_sprint.id


def test_end_sprint(db, f):
    t = f.TeamFactory()
    sprint_id = start_sprint('test sprint', t.id)
    db_sprint = Sprint.query.one()
    assert sprint_id == db_sprint.id

    end_sprint('test sprint')
    db_sprint = Sprint.query.get(sprint_id)
    assert db_sprint is not None
    assert db_sprint.running is False


def test_add_retroitem(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(teams=(team,))

    sprint_id = start_sprint('test sprint', team.id)
    item_id = add_item(user.sprint.id, user.id, 'hay que mejorar los tests')
    item_id2 = add_item(user.sprint.id, user.id, 'hay que empezar a hacer TDD')

    S = db.session
    db_items = S.query(RetroItem.id).filter_by(sprint_id=sprint_id).all()
    assert sorted((item_id, item_id2)) == sorted([item for item, in db_items])


def test_add_retroitem_fails_if_no_active_sprint(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(teams=(team,))

    assert user.sprint is None
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'id'"):
        add_item(user.sprint.id, user.id, 'foo')


def test_add_retroitem_fails_if_expired_sprint(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(teams=(team,))
    sprint = f.SprintFactory(team=team, running=False)

    _id_ = sprint.id
    with pytest.raises(InactiveSprintException,
                       match="No active sprint with specified parameters"):
        add_item(sprint.id, user.id, 'foo')


def test_add_retroitem_fails_if_bad_sprint_id(db, f):
    user = f.UserFactory()

    _id_ = 1
    with pytest.raises(SprintNotFoundException,
                       match="Sprint .* does not exist."):
        add_item(_id_, user.id, 'foo')


def test_show_retroitems_per_team(db, f):
    team = f.TeamFactory()
    user = f.UserFactory(teams=(team,))
    spid = start_sprint('test sprint', team.id)

    item_id_1 = add_item(user.sprint.id, user.id, 'un item')
    item_id_2 = add_item(user.sprint.id, user.id, 'otro item')
    item_id_3 = add_item(user.sprint.id, user.id, 'otro más')

    items = get_retro_items(spid)
    items_ids = [item.id for item in items]
    assert sorted([item_id_1, item_id_2, item_id_3]) == sorted(items_ids)


def test_cant_have_two_active_sprints(db, f):
    team = f.TeamFactory()
    f.UserFactory(teams=(team,))
    f.SprintFactory(team=team, name='sprint name')

    sp = Sprint.query.one_or_none()
    assert sp is not None
    assert sp.running is True

    end_sprint('sprint name')

    sp = Sprint.query.one_or_none()
    assert sp is not None
    assert sp.running is False

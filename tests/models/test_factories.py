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
    PollFactory,
    OptionFactory,
    VoteFactory,
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
        'commands': ['add_team', 'start_sprint', 'add_item', 'show_items', 'end_sprint']
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

    my_vm = VMOwnershipFactory(user_id=user.id, vm_id=vm.id)
    my_other_vm = VMOwnershipFactory(user_id=user.id, vm_id=vm_2.id)
    db.session.flush()

    assert len(user.owned_vms) == 2
    assert my_vm in user.owned_vms
    assert my_other_vm in user.owned_vms


def test_create_poll(db):
    option_1 = OptionFactory(poll=None, number=1, text='first')
    option_2 = OptionFactory(poll=None, number=2, text='second op')
    option_3 = OptionFactory(poll=None, number=3, text='3rd op')
    options = (option_1, option_2, option_3)

    poll = PollFactory(question='who?', options=options)
    assert poll.question == 'who?'
    assert len(poll.options) == 3
    assert all(op in poll.options for op in options)

    assert poll.to_dict() == {
        'question': 'who?',
        'options': [
            (1, 'first', 0),
            (2, 'second op', 0),
            (3, '3rd op', 0),
        ],
    }


def test_vote_count_on_options(db):
    option_1 = OptionFactory(poll=None, number=1)
    option_2 = OptionFactory(poll=None, number=2)
    option_3 = OptionFactory(poll=None, number=3)
    options = (option_1, option_2, option_3)

    poll = PollFactory(question='et tu?', options=options)
    assert poll.question

    VoteFactory(option=option_1)
    VoteFactory(option=option_1)
    VoteFactory(option=option_2)

    op1 = next(o for o in poll.options if o.number == 1)
    op2 = next(o for o in poll.options if o.number == 2)
    op3 = next(o for o in poll.options if o.number == 3)
    assert len(op1.votes) == 2
    assert len(op2.votes) == 1
    assert len(op3.votes) == 0

    assert poll.to_dict() == {
        'question': 'et tu?',
        'options': [
            (1, option_1.text, 2),
            (2, option_2.text, 1),
            (3, option_3.text, 0),
        ],
    }


def test_create_orphan_option_and_then_assign_to_poll(db):
    option_1 = OptionFactory(poll=None, number=1, text='A')
    assert option_1
    options = (option_1, )
    poll = PollFactory(question='et tu?', options=options)
    db.session.flush()

    assert option_1.poll_id == poll.id
    assert option_1.votes == []

    VoteFactory(option=option_1)

    assert len(option_1.votes) == 1

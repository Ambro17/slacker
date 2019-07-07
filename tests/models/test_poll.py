import pytest
from sqlalchemy.orm.exc import FlushError

from slacker.api.poll import user_has_voted
from slacker.models.poll import Poll
from tests.factorium import OptionFactory, PollFactory, VoteFactory, UserFactory


def test_format_options(db):
    option_1 = OptionFactory(number=1, text='A')
    option_2 = OptionFactory(number=2, text='B')
    options = (option_1, option_2)

    poll = PollFactory(question='et tu?', options=options)
    options = poll.options_to_string()
    assert options == "1. A\n2. B"

    VoteFactory(option=option_1)
    VoteFactory(option=option_1)
    options = poll.options_to_string()
    assert options == "1. A `2`\n2. B"

    VoteFactory(option=option_2)
    options = poll.options_to_string()
    assert options == "1. A `2`\n2. B `1`"


def test_create_poll_with_options(db):
    question = 'pregunta'
    options_list = ['red', 'blue', 'white']
    options = [
        OptionFactory(poll=None, number=i, text=text)
        for i, text in enumerate(options_list)
    ]

    the_poll = PollFactory(question=question, options=options)
    db.session.flush()
    assert all(op.poll_id == the_poll.id for op in options)


def test_create_poll_from_string(db):
    p, error = Poll.from_string('is this a question? yes no')
    assert error is None
    assert p.id
    assert p.question == 'is this a question'
    assert len(p.options) == 2
    options_text = [o.text for o in p.options]
    assert sorted(options_text) == ['no', 'yes']


def test_create_poll(db):
    option_1 = OptionFactory(number=1, text='first')
    option_2 = OptionFactory(number=2, text='second op')
    option_3 = OptionFactory(number=3, text='3rd op')
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
    option_1 = OptionFactory(number=1)
    option_2 = OptionFactory(number=2)
    option_3 = OptionFactory(number=3)
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


def test_dont_accept_multiple_votes_from_the_same_user(db):
    op1 = OptionFactory(number=1, text='me')
    op2 = OptionFactory(number=2, text='you')
    poll = PollFactory(question='who?', options=(op1, op2))

    user = UserFactory()
    VoteFactory(poll=poll, option=op1, user_id=user.id)
    db.session.flush()

    with pytest.raises(FlushError, match=r'New instance .* conflicts with persistent instance'):
        VoteFactory(poll=poll, option=op1, user_id=user.id)
        db.session.flush()


def test_user_has_voted(db):
    # Non-existent user has not voted on non-existing poll
    assert user_has_voted(1, 0) is False
    op1 = OptionFactory(number=2, text='you')
    poll = PollFactory(question='who?', options=(op1, ))
    user = UserFactory()

    assert user_has_voted(user.id, poll.id) is False

    VoteFactory(poll=poll, option=op1, user_id=user.id)
    assert user_has_voted(user.id, poll.id) is True

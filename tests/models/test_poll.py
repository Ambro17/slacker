from slacker.models.poll import Poll
from tests.factorium import OptionFactory, PollFactory, VoteFactory


def test_format_options(db):
    option_1 = OptionFactory(poll=None, number=1, text='A')
    option_2 = OptionFactory(poll=None, number=2, text='B')
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

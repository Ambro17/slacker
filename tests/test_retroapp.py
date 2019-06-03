import pytest

from slacker.blueprints.retroapp import USER_REGEX


@pytest.mark.parametrize("escaped_text, expected_user", (
        ("<@U1234|juan>", {'user_id': 'U1234', 'name':'juan'}),
        ("<@W1234|tomás>", {'user_id': 'W1234', 'name':'tomás'}),
        ("  <@W123456789|alex>  ", {'user_id': 'W123456789', 'name':'alex'}),
))
def test_read_user_from_mention(escaped_text, expected_user):
    assert USER_REGEX.search(escaped_text).groupdict() == expected_user


@pytest.mark.parametrize('input_str, expected_users', (
        (
                """
                <@U999|yon> <@U000|abc>
                """,
                [
                    ('U999', 'yon'),
                    ('U000', 'abc'),
                ]
        ),
        (
                """
                <@U123|yon> <@W456|xxx> <@U789|felipe> <@W777|carla>
                """,
                [
                    ('U123', 'yon'),
                    ('W456', 'xxx'),
                    ('U789', 'felipe'),
                    ('W777', 'carla'),
                ]
        ),
        (
                """
                <X@U123|yon> <Y@W456|xxx> <@U789|fel|ipe> <@W777|joséα>
                """,
                [
                    ('U789', 'fel|ipe'),
                    ('W777', 'joséα'),
                ]
        ),
))
def test_read_all_users_from_big_text(input_str, expected_users):
    assert USER_REGEX.findall(input_str) == expected_users

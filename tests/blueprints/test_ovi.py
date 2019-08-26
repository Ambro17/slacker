import pytest

from slacker.blueprints.ovi_management import _validate_command_syntax


@pytest.mark.parametrize('command_args, alias, image', [
    ('console 5', 'console', '5'),
    ('app     5', 'app', '5'),
    ('   appliance       0', 'appliance', '0'),
])
def test_redeploy_invokation_good_boy(command_args, alias, image):
    assert _validate_command_syntax(command_args) == (alias, image)


@pytest.mark.parametrize('command_args', [
    'console,5',
    'console:5',
    'console::5',
    'app   , 5',
    'app5',
    'app : -1',
    'app:-1',  # Negative snapshots not allowed
    'app second_app: 2',  # Negative snapshots not allowed
])
def test_redeploy_invokation_bad_boy(command_args):
    with pytest.raises(Exception) as e:
        _validate_command_syntax(command_args)

    assert 'Invalid command usage' in str(e)

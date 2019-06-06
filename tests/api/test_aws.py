import pytest

from slacker.api.aws.aws import save_user_vms, delete_user_vms


def test_user_can_add_vm(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(db.session, slack_cli, user.user_id, 'apiname', 'secret_token', {'console': 1234})

    assert user.ovi_name == 'apiname'
    assert user.ovi_token == 'secret_token'
    assert len(user.owned_vms) == 1

    user_vm = user.owned_vms[0]
    assert user_vm.vm_id == '1234'
    assert user_vm.alias == 'console'


def test_user_cant_have_conflicting_aliases(db, f, slack_cli):
    user = f.UserFactory()
    VM_ID = 1234
    save_user_vms(db.session, slack_cli, user.user_id, 'foo', 'bar', {'console': VM_ID})
    assert len(user.owned_vms) == 1

    OTHER_VM = 999
    with pytest.raises(Exception, match='One of your VM aliases conflicts with an existing one.'):
        save_user_vms(db.session, slack_cli, user.user_id, 'foo', 'bar', {'console': OTHER_VM})


def test_user_remove_all_vms(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(db.session, slack_cli, user.user_id, 'foo', 'bar', {'console': 1, 'sensor': 2})
    assert len(user.owned_vms) == 2
    delete_user_vms(db.session, slack_cli, user.user_id)
    assert len(user.owned_vms) == 0


def test_user_can_add_delete_and_readd_under_the_same_alias(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(db.session, slack_cli, user.user_id, 'foo', 'bar', {'console': 1})
    assert len(user.owned_vms) == 1
    delete_user_vms(db.session, slack_cli, user.user_id)
    assert len(user.owned_vms) == 0
    save_user_vms(db.session, slack_cli, user.user_id, 'foo', 'bar', {'console': 1})
    assert len(user.owned_vms) == 1

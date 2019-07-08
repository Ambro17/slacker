import pytest

from slacker.api.aws.aws import save_user_vms, delete_user_vms, DuplicateAliasException


def test_user_can_add_vm(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(user, 'apiname', 'secret_token', {'console': 1234})

    assert user.ovi_name == 'apiname'
    assert user.ovi_token == 'secret_token'
    assert len(user.owned_vms) == 1

    user_vm = user.owned_vms[0]
    assert user_vm.vm_id == '1234'
    assert user_vm.alias == 'console'


def test_user_cant_have_conflicting_aliases(db, f, slack_cli):
    user = f.UserFactory()
    VM_ID = 1234
    save_user_vms(user, 'foo', 'bar', {'console': VM_ID})
    assert len(user.owned_vms) == 1

    OTHER_VM = 999
    repeated_alias = 'console'
    with pytest.raises(DuplicateAliasException,
                       match=f"'{repeated_alias}' is already mapped to a VM. Change it and retry."):
        save_user_vms(user, 'foo', 'bar', {repeated_alias: OTHER_VM})


def test_user_remove_all_vms(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(user, 'foo', 'bar', {'console': 1, 'sensor': 2})
    assert len(user.owned_vms) == 2
    delete_user_vms(user)
    assert len(user.owned_vms) == 0


def test_user_can_add_delete_and_readd_under_the_same_alias(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(user, 'oviname', 'sicret', {'console': 1})
    assert len(user.owned_vms) == 1
    delete_user_vms(user)
    assert len(user.owned_vms) == 0
    save_user_vms(user, 'name', 'sikret', {'console': 2})
    assert len(user.owned_vms) == 1


def test_can_add_multiple_aliases_to_same_vm(db, f):
    user = f.UserFactory()
    some_vm = 'abc-123'
    save_user_vms(user, 'oviname', 'sicret', {'console': some_vm})
    assert len(user.owned_vms) == 1
    save_user_vms(user, 'oviname', 'sicret', {'another_alias': some_vm})
    assert len(user.owned_vms) == 2
    assert set(x.alias for x in user.owned_vms) == {'console', 'another_alias'}

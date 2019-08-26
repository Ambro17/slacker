import pytest

from slacker.blueprints.ovi_management import save_user_vms, DuplicateAliasException
from slacker.security import Encrypter, Fernet


def test_user_can_add_vm(db, f, slack_cli, crypto):
    user = f.UserFactory()
    save_user_vms(user, 'apiname', 'secret_token', {'console': 1234})

    assert user.ovi_name == 'apiname'
    assert user.ovi_token == 'secret_token'
    assert len(user.owned_vms) == 1

    user_vm = user.owned_vms[0]
    assert user_vm.vm_id == '1234'
    assert user_vm.alias == 'console'


def test_user_cant_have_conflicting_aliases(db, f, slack_cli, crypto):
    user = f.UserFactory()
    VM_ID = 1234
    save_user_vms(user, 'foo', 'bar', {'console': VM_ID})
    assert len(user.owned_vms) == 1

    OTHER_VM = 999
    repeated_alias = 'console'
    with pytest.raises(DuplicateAliasException,
                       match=f"'{repeated_alias}' is already mapped to a VM. Change it and retry."):
        save_user_vms(user, 'foo', 'bar', {repeated_alias: OTHER_VM})


def test_can_add_multiple_aliases_to_same_vm(db, f, crypto):
    user = f.UserFactory()
    some_vm = 'abc-123'
    save_user_vms(user, 'oviname', 'sicret', {'console': some_vm})
    assert len(user.owned_vms) == 1
    save_user_vms(user, 'oviname', 'sicret', {'another_alias': some_vm})
    assert len(user.owned_vms) == 2
    assert set(x.alias for x in user.owned_vms) == {'console', 'another_alias'}


def test_token_encryption():
    dirty_secret = 'my secret message'
    encryption_key = Fernet.generate_key()

    crypto = Encrypter(encryption_key)

    encrypted_msg = crypto.encrypt(dirty_secret)

    assert crypto.decrypt(encrypted_msg) == dirty_secret


def test_token_encryption_bad_key():
    dirty_secret = 'my secret message'

    good_key = Fernet.generate_key()
    bad_key = Fernet.generate_key()

    crypto = Encrypter(good_key)
    encrypted_msg = crypto.encrypt(dirty_secret)

    # Create an encryptator with a bad key. It should fail decrypting the dirty secret
    crypto_wrong_key = Encrypter(bad_key)

    with pytest.raises(ValueError, match='Kaker, you are not allowed to see this message'):
        crypto_wrong_key.decrypt(encrypted_msg)

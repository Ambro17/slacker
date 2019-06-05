from slacker.api.aws.aws import save_user_vms


def test_user_can_add_vm(db, f, slack_cli):
    user = f.UserFactory()
    save_user_vms(db.session, slack_cli, user.user_id, 'apiname', 'secret_token', {'console': 1234})

    assert user.ovi_name == 'apiname'
    assert user.ovi_token == 'secret_token'
    assert len(user.owned_vms) == 1

    user_vm = user.owned_vms[0]
    assert user_vm.vm_id == '1234'
    assert user_vm.alias == 'console'

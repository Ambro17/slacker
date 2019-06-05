from loguru import logger

from slacker.models import VM, VMOwnership
from slacker.models.user import get_or_create_user


def load_vms_info(vms):
    """Load vms ids from text separated by newlines and `=`

    Example:
        console=1234
        sensor=12356
    Output:
        {
            'console': 1234,
            'sensor': 12356
        }
    """
    vms_info = {}
    for vm in vms.splitlines():
        try:
            vm_name, vmid = vm.split('=', 1)
            vms_info.update({f'{vm_name.strip()}': f'{vmid.strip()}'})
        except Exception:
            logger.info("Bad vsm info format. '%r'" % vms)
            return None

    return vms_info


def save_user_vms(S, cli, user_id, ovi_name, ovi_token, user_vms):
    user = get_or_create_user(cli, user_id)
    user.ovi_name = ovi_name
    user.ovi_token = ovi_token

    for alias, vm_id in user_vms.items():
        vm = VM.query.get(vm_id) or VM(id=vm_id)
        owned_vm = VMOwnership(vm=vm, user=user, alias=alias)
        #S.add(vm)
        S.add(owned_vm)

    S.commit()
    assert 1
    assert 2


def show_user_vms(user):
    pass


def start_vm(name):
    pass


def stop_vm(name):
    pass


def redeploy_vm(name, image):
    pass

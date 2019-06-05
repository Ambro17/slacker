from loguru import logger

from slacker.models import OwnedVM, VM
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

    for alias, vm_id in user_vms:
        vm= VM.query.get(vm_id) or VM(vm_id)
        owned_vm = OwnedVM(
            vm_id=vm.id,
            vm_alias=alias,
            user_id=user.id,
            user_name=user.name,

        )
        S.add(owned_vm)

    S.commit()


def show_user_vms():
    pass


def start_vm(name):
    pass


def stop_vm(name):
    pass

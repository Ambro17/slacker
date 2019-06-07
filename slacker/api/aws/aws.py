from loguru import logger

from slacker.exceptions import SlackerException
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


class DuplicateAliasException(SlackerException):
    """Raised if user wants to save a vm under an alias that already maps to one oh her/his vms"""


def save_user_vms(S, cli, user_id, ovi_name, ovi_token, user_vms):
    user = get_or_create_user(cli, user_id)

    existing_user_vm_aliases = {vm.alias for vm in user.owned_vms}
    if any(alias in existing_user_vm_aliases for alias in user_vms):
        raise DuplicateAliasException(
            f"One of your VM aliases conflicts with an existing one. "
            f"Try a different name or remove all vms and readd the ones you want to keep"
        )

    for alias, vm_id in user_vms.items():
        vm = VM.query.get(vm_id) or VM(id=vm_id)
        S.add(VMOwnership(vm=vm, user=user, alias=alias))

    user.ovi_name = ovi_name
    user.ovi_token = ovi_token

    S.commit()


def delete_user_vms(S, cli, user_id):
    user = get_or_create_user(cli, user_id)
    user.owned_vms = []
    S.commit()


def show_user_vms(user):
    pass


def start_vm(name):
    pass


def stop_vm(name):
    pass


def redeploy_vm(name, image):
    pass

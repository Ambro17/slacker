from loguru import logger

from slacker.database import db
from slacker.exceptions import SlackerException
from slacker.models import VM, VMOwnership


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


def save_user_vms(user, ovi_name, ovi_token, new_user_vms):
    existing_user_vms = {vm.alias for vm in user.owned_vms}
    repeated_alias = next((alias for alias in new_user_vms if alias in existing_user_vms), False)
    if repeated_alias:
        raise DuplicateAliasException(
            f"{repeated_alias} is already mapped to a VM. Change it and retry."
        )

    for alias, vm_id in new_user_vms.items():
        logger.debug(f"Atttempting to add VM with alias={alias} and id={vm_id}")
        vm = VM.query.get(vm_id)
        if not vm:
            vm = VM(id=vm_id)

        owned_vm = VMOwnership.query.filter_by(alias=alias, user_id=user.id, vm_id=vm_id).one_or_none()
        if not owned_vm:
            logger.debug("Creating vm ownership")
            owned_vm = VMOwnership(vm=vm, user=user, alias=alias)
            db.session.add(owned_vm)
        else:
            logger.debug(f"Ignoring {str(owned_vm)} because it's already on database.")

    user.ovi_name = ovi_name
    user.ovi_token = ovi_token

    db.session.commit()


def delete_user_vms(user):
    user.owned_vms = []
    db.session.commit()


def show_user_vms(user):
    pass


def start_vm(name):
    pass


def stop_vm(name):
    pass


def redeploy_vm(name, image):
    pass

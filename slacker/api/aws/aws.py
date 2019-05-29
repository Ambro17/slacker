def get_aws(event):
    print(event)
    return dict(event)


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
            raise ValueError("Bad format on vms file '%s'" % vms)

    return vms_info
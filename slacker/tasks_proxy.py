"""
This module has functions that call the celery tasks on the remote worker
"""
from slacker.worker import celery


def send_ephemeral_message_async(message, channel, user):
    return celery.send_task('tasks.send_ephemeral_message', args=(message, channel, user))


def start_vms_task(user_vms, target_vms, name, tk, **kwargs):
    return celery.send_task('tasks.start_vms', args=(user_vms, target_vms, name, tk), kwargs=kwargs)


def stop_vms_task(user_vms, target_vms, name, tk, **kwargs):
    return celery.send_task('tasks.stop_vms', args=(user_vms, target_vms, name, tk), kwargs=kwargs)


def list_vms_task(user_vms, timeout, name, tk, **kwargs):
    return celery.send_task('tasks.list_vms', args=(user_vms, timeout, name, tk), kwargs=kwargs)


def redeploy_vm_task(user_vms, target_vm, snapshot_id, name, tk, **kwargs):
    return celery.send_task('tasks.redeploy_vm', args=(user_vms, target_vm, snapshot_id, name, tk), kwargs=kwargs)


def get_snapshots_task(name, tk, **kwargs):
    return celery.send_task('tasks.get_redeploy_snapshots', args=(name, tk), kwargs=kwargs)


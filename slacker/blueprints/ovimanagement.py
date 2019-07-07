from flask import request, current_app as app, make_response

from slacker.utils import BaseBlueprint, reply

bp = BaseBlueprint('ovi', __name__, url_prefix='/ovi')

@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'text': 'Ovi Management',
        'commands': ['start', 'stop', 'info', 'redeploy']
    })


@bp.route('/register', methods=('GET', 'POST'))
def register():
    trigger_id = request.form.get('trigger_id')
    user_id = request.form.get('user_id')
    dialog = {
        "callback_id": f"aws_callback",
        "title": "My amazon VMs",
        "state": f"{user_id}",
        "submit_label": "Save",
        "elements": [
            {
                "type": "text",
                "label": "API User",
                "name": "user"
            },
            {
                "type": "text",
                "label": "API Token",
                "name": "token"
            },
            {
                "label": "VMs information",
                "type": "textarea",
                "hint": "Put your vm alias and ids. One line for each vm",
                "placeholder": "console=5kyq3bdcnl6sbnsv9t6q\nsensor=wwt6adcuow78sj9hj8hi",
                "name": "vms_info",
            }
        ]
    }

    app.slack_cli.api_call(
        "dialog.open",
        trigger_id=trigger_id,
        dialog=dialog
    )

    return make_response('', 200)


@bp.route('/start', methods=('GET', 'POST'))
def start():
    pass


@bp.route('/stop', methods=('GET', 'POST'))
def stop():
    pass


@bp.route('/info', methods=('GET', 'POST'))
def info():
    pass


@bp.route('/redeploy', methods=('GET', 'POST'))
def redeploy():
    pass
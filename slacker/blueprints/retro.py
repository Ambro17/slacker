from flask import Blueprint

from slacker.utils import reply, BaseBlueprint

bp = BaseBlueprint('retro', __name__, url_prefix='/retro')


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a retro action.",
        'commands': ['add_item', 'show_items', 'start_sprint', 'end_sprint', 'add_team']
    })

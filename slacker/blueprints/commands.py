from flask import Blueprint

from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte
from slacker.utils import reply

bp = Blueprint('commands', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a command.",
        'commands': ['feriados', 'hoypido', 'subte']
    })


@bp.route('/feriados', methods=('GET', 'POST'))
def feriados() -> str:
    response = get_feriadosarg()
    return response


@bp.route('/hoypido', methods=('GET', 'POST'))
def hoypido() -> str:
    response = get_hoypido()
    return response


@bp.route('/subte', methods=('GET', 'POST'))
def subte() -> str:
    response = get_subte()
    return response

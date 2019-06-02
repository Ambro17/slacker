import json

from flask import (
    Blueprint, request, jsonify,
    current_app)

from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte
from slacker.utils import reply

bp = Blueprint('api', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    return reply({
        'error': "You must specify a command.",
        'commands': ['feriados', 'hoypido', 'subte']
    })


@bp.route('/feriados', methods=('GET', 'POST'))
def feriados():
    response = get_feriadosarg()
    return response


@bp.route('/hoypido', methods=('GET', 'POST'))
def hoypido():
    response = get_hoypido()
    return response


@bp.route('/subte', methods=('GET', 'POST'))
def subte():
    response = get_subte()
    return response

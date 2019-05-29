from flask import (
    Blueprint, request, jsonify
)

from slacker.api.feriados import get_feriadosarg
from slacker.api.hoypido import get_hoypido
from slacker.api.subte import get_subte

bp = Blueprint('api', __name__, url_prefix='/cmd')


@bp.route('/', methods=('GET', 'POST'))
def index():
    return jsonify({'message': "You must specify a command"})


@bp.route('/feriados', methods=('GET', 'POST'))
def feriados():
    response = get_feriadosarg()
    return jsonify(response)


@bp.route('/hoypido', methods=('GET', 'POST'))
def hoypido():
    response = get_hoypido()
    return jsonify(response)


@bp.route('/subte', methods=('GET', 'POST'))
def subte():
    response = get_subte()
    return jsonify(response)


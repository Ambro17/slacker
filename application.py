import logging
import os

from flask import Flask, jsonify, request, make_response, url_for, redirect
from werkzeug.routing import BuildError

from commands.dolar.dolar import dolar as dolar_
from commands.dolar_rofex.rofex import rofex as rofex_
from commands.subte.subte import subte as subte_
from commands.feriados.feriados import feriadosarg
from commands.hoypido.hoypido import hoypido as hoypido_, hoypido_by_day
from commands.posiciones.posiciones import posiciones as posiciones_
from events.dispatcher import dispatch_event
from utils import send_message, JSON_TYPE

logger = logging.getLogger(__name__)

app = Flask(__name__)

application = app


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/interactive', methods=['GET', 'POST'])
def test():
    return send_message('Proximamente..')


@app.route('/', methods=['GET', 'POST'])
def command_dispatcher():
    command = request.form.get('command', '')[1:]
    try:
        return redirect(url_for(command))
    except BuildError:
        if not command:
            msg = 'You must pass a command argument'
        else:
            msg = f'Unknown command "{command}"'
        return send_message(msg)


@app.route('/dolar', methods=['GET', 'POST'])
def dolar():
    return send_message(dolar_())


@app.route('/rofex', methods=['GET', 'POST'])
def rofex():
    return send_message(rofex_())


@app.route('/subte', methods=['GET', 'POST'])
def subte():
    return send_message(subte_())


@app.route('/feriados', methods=['GET', 'POST'])
def feriados():
    return send_message(feriadosarg())


@app.route('/hoypido', methods=['GET', 'POST'])
def hoypido():
    day = request.form.get('text')
    if not day:
        menu = hoypido_()
    else:
        menu = hoypido_by_day(day)

    return send_message(menu, msg_type='ephemeral')


@app.route('/posiciones', methods=['GET', 'POST'])
def posiciones():
    return send_message(posiciones_())


@app.route('/events', methods=['GET', 'POST'])
def events():
    event = request.get_json(force=True, silent=True) or {}
    if not event:
        return make_response({'error': False, 'reason': 'Ignored'})

    try:
        return dispatch_event(event)
    except Exception:
        return make_response({'error': True, 'reason': 'Unknown'}, 400)


if __name__ == '__main__':
    application.run(debug=os.environ.get('DEBUG', False))

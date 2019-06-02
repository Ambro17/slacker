import random
import re
import logging

import os
import requests
from requests.exceptions import ReadTimeout

from slacker.utils import soupify_url

logger = logging.getLogger(__name__)

LINEA = re.compile(r'Linea([A-Z]{1})')


def get_subte() -> str:
    update = check_update()
    if update is None:
        msg = 'Internal error'
    elif not update:
        msg = ':check: Los subtes funcionan normalmente'
    else:
        msg = prettify_updates(update)

    return msg


def check_update():
    """Returns status incidents per line.
    None if response code is not 200
    empty dict if there are no updates
    dict with linea as keys and incident details as values.
    Returns:
        dict|None: mapping of line incidents
        {
          'A': 'rota',
          'E': 'demorada',
        }
    """
    url = 'https://apitransporte.buenosaires.gob.ar/subtes/serviceAlerts'
    params = {
        'client_id': os.environ['CABA_CLI_ID'],
        'client_secret': os.environ['CABA_SECRET'],
        'json': 1,
    }
    r = requests.get(url, params=params, timeout=5)

    if r.status_code != 200:
        logger.info('Response failed. %s, %s' % (r.status_code, r.reason))
        return None

    data = r.json()

    alerts = data['entity']
    logger.info('Alerts: %s', alerts)

    updates = (get_update_info(alert['alert']) for alert in alerts)
    return {
        linea: status
        for linea, status in updates
    }

def get_update_info(alert):
    linea = _get_linea_name(alert)
    incident = _get_incident_text(alert)
    return linea, incident


def _get_linea_name(alert):
    try:
        nombre_linea = alert['informed_entity'][0]['route_id']
    except (IndexError, KeyError):
        return None

    try:
        nombre_linea = LINEA.match(nombre_linea).group(1)
    except AttributeError:
        # There was no linea match -> Premetro y linea Urquiza
        nombre_linea = nombre_linea.replace('PM-', 'PM ')

    return nombre_linea


def _get_incident_text(alert):
    translations = alert['header_text']['translation']
    spanish_desc = next((translation
                         for translation in translations
                         if translation['language'] == 'es'), None)
    if spanish_desc is None:
        logger.info('raro, no tiene desc en español. %s' % alert)
        return None

    return spanish_desc['text']

def prettify_updates(updates):
    DELAY_ICONS = (':construction:', ':traffic_light:', ':warning:',
                   ':train2:', ':bullettrain_front:', ':metro:')
    return '\n'.join(
        f'{linea} | {random.choice(DELAY_ICONS)}️ {status.strip()}'
        for linea, status in updates.items()
    )
import re
import logging

from requests.exceptions import ReadTimeout

from slacker.utils import soupify_url

logger = logging.getLogger(__name__)


def get_subte():
    try:
        return _subte()
    except Exception:
        logger.exception('Something bad happened getting subte status')
        return 'Oops! 👻'


def _subte():
    """Estado de las lineas de subte, premetro y urquiza."""
    try:
        soup = soupify_url('https://www.metrovias.com.ar')
    except ReadTimeout:
        logger.info('Error in metrovias url request')
        return '⚠️ Metrovias no responde. Intentá más tarde'

    subtes = soup.find('table', {'class': 'table'})
    REGEX = re.compile(r'Línea *([A-Z]){1} +(.*)', re.IGNORECASE)
    estado_lineas = []
    for tr in subtes.tbody.find_all('tr'):
        estado_linea = tr.text.strip().replace('\n', ' ')
        match = REGEX.search(estado_linea)
        if match:
            linea, estado = match.groups()
            estado_lineas.append((linea, estado))

    return '\n'.join(
        format_estado_de_linea(info_de_linea) for info_de_linea in estado_lineas
    )


def format_estado_de_linea(info_de_linea):
    linea, estado = info_de_linea
    if estado.lower() == 'normal':
        estado = '✔️'
    else:
        estado = f'⚠ {estado} ⚠'
    return f'{linea} {estado}'

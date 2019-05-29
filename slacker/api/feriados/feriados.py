from datetime import datetime, timezone, timedelta
import logging

from slacker.api.feriados.utils import (
    get_feriados,
    prettify_feriados,
    filter_feriados,
    next_feriado_message
)

logger = logging.getLogger(__name__)


def get_feriadosarg() -> str:
    today = datetime.now(tz=timezone(timedelta(hours=-3)))
    feriados = get_feriados(today.year)
    if not feriados:
        return '🏳️ La api de feriados no responde'

    following_feriados = filter_feriados(today, feriados)
    if following_feriados:
        header_msg = next_feriado_message(today, following_feriados)
        all_feriados = prettify_feriados(following_feriados)
        msg = '\n'.join([header_msg, all_feriados])
    else:
        msg = 'No hay más feriados este año'

    return msg

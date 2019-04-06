from commands.dolar_rofex.constants import DOLAR_REGEX, Contrato, month_name, EMPTY_MESSAGE
from utils import soupify_url, monospace


def get_rofex():
    """Print dolar futuro contracts."""
    rofex_data = _get_rofex()
    contratos = prettify_rofex(rofex_data)
    return contratos


def _get_rofex():
    try:
        soup = soupify_url('https://www.rofex.com.ar/', verify=False)
    except TimeoutError:
        return None

    table = soup.find('table', class_='table-rofex')
    cotizaciones = table.find_all('tr')[1:]  # Exclude header
    contratos = []

    for cotizacion in cotizaciones:
        contrato, valor, _, variacion, var_porc = cotizacion.find_all('td')
        month, year = DOLAR_REGEX.match(contrato.text).groups()
        contratos.append(Contrato(int(month), year, valor.text))

    return contratos


def prettify_rofex(contratos):
    values = '\n'.join(
        f"{month_name[month]} {year} | {value[:5]}" for month, year, value in contratos
    )
    header = '  Dólar  | Valor\n'
    return monospace(header + values) if contratos is not None else EMPTY_MESSAGE

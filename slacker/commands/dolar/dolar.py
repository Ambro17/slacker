from collections import defaultdict

from utils import string_to_ascii, trim, soupify_url, monospace


def dolar():
    soup = soupify_url("http://www.dolarhoy.com/usd")
    data = soup.find_all('table')

    cotiz = get_cotizaciones(data)
    pretty_result = pretty_print_dolar(cotiz)
    return pretty_result


def get_cotizaciones(response_soup):
    """Returns a dict of cotizaciones with banco as keys and exchange rate as value.

    {
        "Banco Nación": {
            "Compra": "30.00",
            "Venta": "32.00",
        },
        "Banco Galicia": {
            "Compra": "31.00",
            "Venta": "33.00",
        }
    }

    """
    cotizaciones = defaultdict(dict)
    for table in response_soup:
        # Get cotizaciones
        for row_cotizacion in table.tbody.find_all('tr'):
            banco, compra, venta = (
                item.get_text() for item in row_cotizacion.find_all('td')
            )
            banco_raw = banco.replace('Banco ', '')
            banco = string_to_ascii(banco_raw)
            cotizaciones[banco]['compra'] = compra
            cotizaciones[banco]['venta'] = venta

    return cotizaciones


def pretty_print_dolar(cotizaciones, limit=7):
    """Returns dolar rates separated by newlines and with code markdown syntax.
    ```
    Banco Nacion  | $30.00 | $40.00
    Banco Galicia | $30.00 | $40.00
                   ...
    ```
    """
    return monospace('\n'.join(
            "{:<12} | {:7} | {:7}".format(
                trim(banco), valor['compra'], valor['venta']
            )
            for banco, valor in cotizaciones.items()
        )
    )

from utils import soupify_url, monospace, safe, trim


@safe(on_error='No compré el olé todavía.. preguntame más tarde')
def get_posiciones() -> str:
    soup = soupify_url('http://www.promiedos.com.ar/primera', encoding='ISO-8859-1')
    tabla = soup.find('table', {'id': 'posiciones'})
    info = parse_posiciones(tabla)
    msg = prettify_table_posiciones(info)
    return msg


def parse_posiciones(tabla, top=10):
    CONTENT_ROWS = 4
    # ['Rank', 'Equipo', 'Pts', 'PJ']
    headers = [th.text for th in tabla.thead.find_all('th')[:CONTENT_ROWS]]
    posiciones = []

    for row in tabla.tbody.find_all('tr')[:top]:
        equipo = [trim(r.text) for r in row.find_all('td')[:CONTENT_ROWS]]
        posiciones.append(equipo)

    posiciones.insert(0, headers)
    return posiciones


def prettify_table_posiciones(info):
    try:
        return monospace(
            '\n'.join(
                '{:2} | {:12} | {:3} | {:3}'.format(*team_stat) for team_stat in info
            )
        )
    except Exception:
        return 'No te entiendo..'

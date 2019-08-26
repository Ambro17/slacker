from loguru import logger

from slacker.api.hoypido.utils import (
    get_comidas,
    prettify_food_offers,
    day_to_int,
    filter_comidas,
    day_names,
)


def get_hoypido_specials() -> str:
    week_menu = get_comidas()
    final = []
    for day, menu in week_menu.items():
        daily_specials = menu.get('especiales')
        if daily_specials:
            final.append((day, daily_specials))

    res = ":carrot: *Especiales de la semana* :carrot:\n"
    for day, offers in sorted(final):
        foods = '\n'.join(f'> {option}' for option in offers)
        res += f"*» {day_names[day]}:*\n{foods}\n"

    return res


def get_hoypido_by_day(day) -> str:
    comidas = get_comidas()

    day_num = day_to_int.get(day.upper())
    if day_num is None:
        return 'No entiendo ese día.\nLas opciones son `L`, `M`, `X`, `J` y `V`'
    comidas_del_dia = filter_comidas(comidas,
                                     lambda dia, comidas: dia == day_num)

    msg = prettify_food_offers(comidas_del_dia)

    return msg


def get_hoypido_all() -> str:
    week_menu = get_comidas()
    return prettify_food_offers(week_menu)

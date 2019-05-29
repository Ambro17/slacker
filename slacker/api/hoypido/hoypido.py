from slacker.api.hoypido.utils import (
    get_comidas,
    prettify_food_offers,
    day_to_int,
    filter_comidas,
)


def get_hoypido() -> str:
    comidas = get_comidas()
    msg = prettify_food_offers(comidas)
    return msg


def get_hoypido_by_day(day) -> str:
    comidas = get_comidas()

    day_num = day_to_int.get(day.upper())
    if day_num is None:
        return 'No entiendo ese día.\nLas opciones son `L`, `M`, `X`, `J` y `V`'
    comidas_del_dia = filter_comidas(comidas,
                                     lambda dia, comidas: dia == day_num)

    msg = prettify_food_offers(comidas_del_dia)

    return msg

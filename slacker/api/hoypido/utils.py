import os
import logging
from datetime import datetime
from collections import defaultdict
from typing import Optional

import requests

from slacker.app_config import HOYPIDO_USER, HOYPIDO_MENU, HOYPIDO_TOKEN
from slacker.exceptions import SlackerException

logger = logging.getLogger(__name__)

url = 'https://hoypido-api-v2.herokuapp.com/customer'
ONAPSIS_SALUDABLE = f"{url}/{HOYPIDO_USER}/location/{HOYPIDO_MENU}/menus"


MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(0, 7)

day_names = {
    MONDAY: 'Lunes',
    TUESDAY: 'Martes',
    WEDNESDAY: 'Miércoles',
    THURSDAY: 'Jueves',
    FRIDAY: 'Viernes',
    SATURDAY: 'Sábado',
    SUNDAY: 'Domingo',
}

day_to_int = {
    'L': MONDAY,
    'M': TUESDAY,
    'X': WEDNESDAY,
    'J': THURSDAY,
    'V': FRIDAY,
}


def get_comidas():
    """
    Output:
    {
        0: {
            'pastas': ['Tallarines con Salsa Bolognesa', 'Spaghetti Mediterrxe1neo'],
            'tartas': ['3 Empanadas de Jamxf3n y Queso ', '3 Empanadas de Verdura y Salsa Blanca']
            'especiales': ['Tarta de Zapallitos y Queso con Ensalada Mixta']
            'ensaladas': ['Ensalada de Lechuga, lentejas, tomate, pepino, zanahorias.']
        },
        [...]
        4: {
            'especiales': ['Salteado de carne y vegetales con arroz aromatico']
            'ensaladas': ['Ensalada de Lechuga, lentejas, tomate, pepino, zanahorias.']
            'sandwiches': ['6 Triples de Miga de Jamxf3n y Queso', 'Figazza de Jamon y queso']
        }
    }
    """
    menu_por_dia = {}
    r = requests.get(ONAPSIS_SALUDABLE, params={'access_token': HOYPIDO_TOKEN}, timeout=2)
    if r.status_code != 200:
        raise SlackerException(f'Could not connect to hoypido API. Try again later. {r.status_code}-{r.reason}-{r.url}')

    week_menu = r.json()
    for day_menu in week_menu:
        date = datetime.strptime(day_menu["active_date"], "%Y-%m-%dT%H:%M:%S")
        menu = defaultdict(list)
        for plato in day_menu['options']:
            food_category = plato.get('subtype') or 'Otro'
            menu[food_category].append(plato['name'])

        menu_por_dia[date.weekday()] = menu

    return menu_por_dia


def filter_comidas(comidas: dict, func=lambda k, v: True) -> Optional[dict]:
    """Filter comidas according to a custom criteria"""
    return {k: v for k, v in comidas.items() if func(k, v)}


def prettify_food_offers(menu_por_dia) -> str:
    """
    Args:
        menu_por_dia:

    Returns:
        str: Pretty printed menu with food type as header for each day

    Sample input:
    {
        0: {
            'pastas': ['Tallarines con Salsa Bolognesa', 'Spaghetti Mediterrxe1neo'],
            'tartas': ['3 Empanadas de Jamxf3n y Queso ', '3 Empanadas de Verdura y Salsa Blanca']
            'especiales': ['Tarta de Zapallitos y Queso con Ensalada Mixta']
            'ensaladas': ['Ensalada de Lechuga, lentejas, tomate, pepino, zanahorias.']
            'carnes': ['Bife a la plancha con Ensalada', 'Bife a la plancha'],
            'milanesas': ['Milanesa de Ternera con huevo frito y pure de papa']
            'vegetarianos': ['Omelette Caprese con Ensalada']
            'sandwiches': ['6 Triples de Miga de Jamxf3n y Queso']
            'pollo': ['Pollo al Limxf3n y Arroz con Queso']
        },
        [...]
        4: {
            'especiales': ['Salteado de carne y vegetales con arroz aromatico']
            'ensaladas': ['Ensalada de Lechuga, lentejas, tomate, pepino, zanahorias.']
            'milanesas': ['Milanesa de Ternera con huevo frito y pure de papa']
            'vegetarianos': ['Omelette Caprese con Ensalada']
            'sandwiches': ['6 Triples de Miga de Jamxf3n y Queso', 'Figazza de Jamon y queso']
        }
    }

    Sample output:
        Lunes
        »Pollo
            Pollo al Limón y Arroz con Queso
            Pechuga
        »Carne
            Carne al horno
            Carne cruda
        Martes
        »Pollo
            Pollo al Limón y Arroz con Queso
            Pechuga
        »Carne
            Carne al horno
            Carne cruda
    """
    if menu_por_dia:
        today = datetime.today().weekday()
        day = MONDAY if today in (SATURDAY, SUNDAY) else today
        foods = {d: v for d, v in menu_por_dia.items() if d >= day}
        msg = prettify(foods)
    else:
        msg = 'No hay información sobre el menú solicitado 🍽'

    return msg


def prettify(foods):
    """
    {
        0: {
            'pastas': ['Tallarines con Salsa Bolognesa', 'Spaghetti Mediterrxe1neo'],
            'pollo': ['Pollo al Limxf3n y Arroz con Queso']
        },
        [...]
        4: {
            'especiales': ['Salteado de carne y vegetales con arroz aromatico']
            'sandwiches': ['6 Triples de Miga de Jamxf3n y Queso', 'Figazza de Jamon y queso']
        }
    }
    
    """
    msg = ""
    for day_num, menu_by_food_type in foods.items():
        msg += prettify_day_menu(day_num, menu_by_food_type)

    return msg


def prettify_day_menu(day, food_types):
    """
    Args:
        day_name (str): day name
        food_types (dict): food dishes as a mapping from food type

    Sample:
    Lunes,
    {
        'tartas': ['3 Empanadas de Jamxf3n y Queso ', '3 Empanadas de Verdura y Salsa Blanca']
        'especiales': ['Tarta de Zapallitos y Queso con Ensalada Mixta']
        'pollo': ['Pollo al Limxf3n y Arroz con Queso']
    }
    ->
    Lunes
    »Tartas
        Pollo al Limón y Arroz con Queso
        Pechuga
    »Especiales
        Carne al horno
        Carne cruda
        [...]
    [...]

    """
    day_name = day_names[day]
    menu = f'*{day_name}*\n'
    for food_type, foods in food_types.items():
        # Append > to quote each dish option and join on newlines
        foods = '\n'.join(f'>{f}' for f in foods)
        # Add the food type and all its dishes options and continue with the next food type
        menu += f"`{food_type.capitalize()}` \n{foods}\n"

    return menu

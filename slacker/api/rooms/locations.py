from functools import partial
from os.path import dirname, abspath, join as os_join
from PIL import Image, ImageDraw, ImageFont
from slacker.log import logger

from slacker.api.rooms.api import RoomFinder, Room

office_map = """
╔══════════════════╗          ╔═══════════════╦═════╗
║ Ground Floor     ║          ║               ║  1  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  2  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  3  ║
║                  ║          ║               ╚═════╣
║                  ║          ║                     ║
║                  ╚══════════╝                     ║
║                                                   ║
╚════════╦═════════╦════════════════════════════════╝
         ║    4    ║
         ╚═════════╝

1. Marie Curie
2. Godel
3. Diffie
4. Shannon

╔══════════════════╗          ╔═══════════════╦═════╗  ╔════╦═════════╦════╗
║ 1st Floor        ║          ║               ║  5  ║  ║    ║         ║    ║
║                  ║          ║               ╠═════╣  ║    ║    9    ║    ║
║                  ║          ║               ║  6  ║  ║    ╠═════════╣    ║
║                  ║          ║               ╠═════╣  ║  8 ║         ║ 10 ║
║                  ║          ║               ║  7  ║  ╠════╝         ╚════╣
║                  ║          ║               ╚═════╣  ║                   ║
║                  ║          ║                     ║  ║                   ║
║                  ╚══════════╝                     ╚══╝                   ║
║                                                                          ║
╚════════╦═════════╦═══════════════════════════════════════════════════════╝
         ║   11    ║
         ╚═════════╝

5. Knuth
6. Anita Borg
7. Lovelace
8. Boole
9. Ritchie
10. Hamming
11. Huffman

╔══════════════════╗         ╔═════════════════════╗
║ 2nd Floor        ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║          12         ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ╠═════════════════════╣
║                  ║         ║                     ║
║                  ╚═════════╝                     ║
║                                                  ║
╚════════╦═════════╦═══════════════════════════════╝
         ║    13   ║
         ╚═════════╝

12. Turing
13. Angela Ruiz
""".strip()


ground_floor = """
╔══════════════════╗          ╔═══════════════╦═════╗
║ Ground Floor     ║          ║               ║  {marie_curie}  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  {godel}  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  {diffie}  ║
║                  ║          ║               ╚═════╣
║                  ║          ║                     ║
║                  ╚══════════╝                     ║
║                                                   ║
╚════════╦═════════╦════════════════════════════════╝
         ║    {shannon}    ║
         ╚═════════╝
""".strip()


first_floor = """
╔══════════════════╗          ╔═══════════════╦═════╗  ╔════╦═══════╦════╗
║ 1st Floor        ║          ║               ║  {knuth}  ║  ║    ║       ║    ║
║                  ║          ║               ╠═════╣  ║    ║   {ritchie}   ║    ║
║                  ║          ║               ║  {anita_borg}  ║  ║    ╠═══════╣    ║
║                  ║          ║               ╠═════╣  ║  {boole} ║       ║ {hamming}  ║
║                  ║          ║               ║  {lovelace}  ║  ╠════╝       ╚════╣
║                  ║          ║               ╚═════╣  ║                 ║
║                  ║          ║                     ║  ║                 ║
║                  ╚══════════╝                     ╚══╝                 ║
║                                                                        ║
╚════════╦═════════╦═════════════════════════════════════════════════════╝
         ║    {huffman}    ║
         ╚═════════╝
""".strip()


second_floor = """
╔══════════════════╗         ╔═════════════════════╗
║ 2nd Floor        ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║          {turing}          ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ╠═════════════════════╣
║                  ║         ║                     ║
║                  ╚═════════╝                     ║
║                                                  ║
╚════════╦═════════╦═══════════════════════════════╝
         ║    {angela_ruiz}    ║
         ╚═════════╝
""".strip()


rooms = {
    0: ground_floor,
    1: first_floor,
    2: second_floor,
}
MARK = '■'
IMAGES_DIR = os_join(dirname(abspath(__file__)), 'images')
get_image_dir = partial(os_join, IMAGES_DIR)
OFFICE_MAP = get_image_dir('office_map.png')


def get_room_location(room: Room):
    room_map = rooms[room.floor]
    # Fill the map with empty spaces to render the ascii map correctly
    default_format_args = {normalize(name): ' ' for name in RoomFinder.ROOM_IDS_BY_NAME}
    default_format_args.update({normalize(room.name): MARK})  # Mark room location
    return room_map.format(**default_format_args)


def create_image_from_map(amap: str, image_path, **kwargs):
    return create_image(amap, image_path, **kwargs)


def normalize(name):
    """Replace spaces by underscores and lowercase it"""
    return name.lower().replace(' ', '_')


def create_image(text, image_path, size=(620, 240), text_pos_xy=(15, 5), font_size=14):
    black = (0, 0, 0)
    logger.debug(f'Creating image at {image_path}')
    img = Image.new('RGB', size, color='white')
    drawer = ImageDraw.Draw(img)
    font = ImageFont.truetype('/Library/Fonts/DejaVuSansMono.ttf', font_size)
    drawer.text(text_pos_xy, text, font=font, fill=black)
    img.save(image_path, quality=95)
    logger.debug(f'Image saved at {image_path}')
    return image_path


def draw_office_map(path):
    return create_image(office_map, path, size=(1100, 1600), text_pos_xy=(15, 15), font_size=24)

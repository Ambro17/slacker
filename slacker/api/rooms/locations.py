from slacker.api.rooms.api import RoomFinder

ground_floor = """
╔══════════════════╗          ╔═══════════════╦═════╗
║ Ground Floor     ║          ║               ║  {0}  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  {1}  ║
║                  ║          ║               ╠═════╣
║                  ║          ║               ║  {2}  ║
║                  ║          ║               ╚═════╣
║                  ║          ║                     ║
║                  ╚══════════╝                     ║
║                                                   ║
╚════════╦═════════╦════════════════════════════════╝
         ║    {3}    ║
         ╚═════════╝                  
"""

first_floor = """
╔══════════════════╗          ╔═══════════════╦═════╗  ╔════╦═══════╦════╗
║ 1st Floor        ║          ║               ║  {0}  ║  ║    ║       ║    ║
║                  ║          ║               ╠═════╣  ║    ║   {4}   ║    ║
║                  ║          ║               ║  {1}  ║  ║    ╠═══════╣    ║
║                  ║          ║               ╠═════╣  ║  {3} ║       ║ {5}  ║
║                  ║          ║               ║  {2}  ║  ╠════╝       ╚════╣
║                  ║          ║               ╚═════╣  ║                 ║
║                  ║          ║                     ║  ║                 ║
║                  ╚══════════╝                     ╚══╝                 ║
║                                                                        ║
╚════════╦═════════╦═════════════════════════════════════════════════════╝
         ║    {6}    ║
         ╚═════════╝
"""

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
"""

rooms = {
    0: ground_floor,
    1: first_floor,
    2: second_floor,
}


def get_room_location(room):
    room_map = rooms[room.floor]
    # Fill the map with empty spaces to render the ascii map
    default_format_args = {normalize(name): ' ' for name in RoomFinder.ROOM_IDS_BY_NAME}
    default_format_args.update({normalize(room.name): 'ӿ'})  # Mark room location
    return room_map.format(**default_format_args)


def normalize(name):
    """Replace spaces by underscores and lowercase it"""
    return name.lower().replace(' ', '_')

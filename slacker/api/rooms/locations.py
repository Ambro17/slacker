from slacker.api.rooms.api import RoomFinder

office_map = """
╔══════════════════╗          ╔═══════════════╦═════╗
║ Ground Floor     ║          ║               ║  {curie}  ║
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

1. Curie
2. Godel
3. Diffie
4. Shannon

╔══════════════════╗          ╔═══════════════╦═════╗  ╔════╦═════════╦════╗
║ 1st Floor        ║          ║               ║  5  ║  ║    ║    9    ║    ║
║                  ║          ║               ╠═════╣  ║ 8  ║         ║ 10 ║
║                  ║          ║               ║  6  ║  ║    ╠═════════╣    ║
║                  ║          ║               ╠═════╣  ║    ║         ║    ║
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
║                  ║         ╠═════════════════════╣qq
║                  ║         ║                     ║
║                  ╚═════════╝                     ║
║                                                  ║
╚════════╦═════════╦═══════════════════════════════╝
         ║    13   ║
         ╚═════════╝

12. Turing
13. Angela Ruiz


"""

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
"""

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
    # Fill the map with empty spaces to render the ascii map correctly
    default_format_args = {normalize(name): ' ' for name in RoomFinder.ROOM_IDS_BY_NAME}
    default_format_args.update({normalize(room.name): 'ӿ'})  # Mark room location
    return room_map.format(**default_format_args)


def normalize(name):
    """Replace spaces by underscores and lowercase it"""
    return name.lower().replace(' ', '_')

from slacker.api.rooms.api import RoomFinder
from slacker.api.rooms.locations import get_room_location


def test_room_location_second_floor():
    angela = RoomFinder.get_room_by_name('angela Ruiz')
    result = get_room_location(angela)
    assert result == """
╔══════════════════╗         ╔═════════════════════╗
║ 2nd Floor        ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ╠═════════════════════╣
║                  ║         ║                     ║
║                  ╚═════════╝                     ║
║                                                  ║
╚════════╦═════════╦═══════════════════════════════╝
         ║    ӿ    ║
         ╚═════════╝
"""
    angela = RoomFinder.get_room_by_name('TuRing')
    result = get_room_location(angela)
    assert result == """
╔══════════════════╗         ╔═════════════════════╗
║ 2nd Floor        ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ║          ӿ          ║
║                  ║         ║                     ║
║                  ║         ║                     ║
║                  ║         ╠═════════════════════╣
║                  ║         ║                     ║
║                  ╚═════════╝                     ║
║                                                  ║
╚════════╦═════════╦═══════════════════════════════╝
         ║         ║
         ╚═════════╝
"""


def test_room_location_ground_floor():
    angela = RoomFinder.get_room_by_name('angela Ruiz')
    result = get_room_location(angela)


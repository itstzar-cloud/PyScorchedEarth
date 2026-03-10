import os
import unittest
import pygame
from menu.option import Option
from game_core.tank import Tank
from game_core.constants import *

# Always resolve relative to the test file so this works both when run
# directly (python test/tests.py) and via pytest from the project root.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def empty_function():
    pass


def return_text(text):
    return text


class OptionTestCase(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.title_font = pygame.font.Font('assets/fonts/DeathFromAbove.ttf', 100)
        self.is_called = False

    def _mark_called(self):
        self.is_called = True

    def test_option_text(self):
        test = Option(lambda: return_text("SCORCHED  EARTH"), 20, empty_function, self.title_font)
        self.assertEqual(test.text(), "SCORCHED  EARTH")

    def test_option_text_position(self):
        test = Option(lambda: return_text("SCORCHED  EARTH"), 20, empty_function, self.title_font)
        self.assertEqual(test.pos, 20)

    def test_option_hovered(self):
        test = Option(lambda: return_text("SCORCHED  EARTH"), 20, empty_function, self.title_font)
        test.hovered = True
        self.assertEqual(test.hovered, True)

    def test_option_hovered_and_color(self):
        test = Option(lambda: return_text("SCORCHED  EARTH"), 20, empty_function, self.title_font)
        test.hovered = True
        self.assertEqual(test.get_color(), (251, 223, 124))
        test.hovered = False
        self.assertEqual(test.get_color(), (0, 0, 0))

    def test_option_select(self):
        test = Option(lambda: return_text("SCORCHED  EARTH"), 20, self._mark_called, self.title_font)
        test.select()
        self.assertEqual(self.is_called, True)


class TankTestCase(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.tank = Tank((display_height, display_width), (100, 100), (200, 200), black)

    def test_tank_calculate_distance_from_tank_center(self):
        point = self.tank.calculate_distance_from_tank_center((200, 200))
        self.assertEqual(point, 141)

    def test_tank_turret_and_coordinates(self):
        tac = self.tank.get_turret_end_coordinates()
        self.assertEqual(tac, (0, 0))

    def test_tank_update_turret_angle(self):
        self.tank.turret_angle = 0
        self.assertEqual(self.tank.turret_angle, 0)
        self.tank.update_turret_angle(50)
        self.assertEqual(self.tank.turret_angle, 1.5707963267948966)
        self.tank.turret_angle = 0
        self.assertEqual(self.tank.turret_angle, 0)
        self.tank.update_turret_angle(-20)
        self.assertEqual(self.tank.turret_angle, -1.5707963267948966)

    def test_tank_update_power(self):
        self.assertEqual(self.tank.tank_power, 50)
        self.tank.update_tank_power(200)
        self.assertEqual(self.tank.tank_power, 100)

    def test_tank_get_health(self):
        self.assertEqual(self.tank.tank_health, 100)
        self.assertEqual(self.tank.get_tank_health(), 100)

    def test_tank_get_position(self):
        self.assertEqual(self.tank.position, [100, 100])
        self.assertEqual(self.tank.get_tank_position(), (100, 100))

    def test_tank_update_position(self):
        self.assertEqual(self.tank.position, [100, 100])
        self.tank.update_tank_position((200, 200))
        self.assertEqual(self.tank.position, [200, 200])


if __name__ == '__main__':
    unittest.main()

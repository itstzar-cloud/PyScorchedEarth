import pygame
from math import sqrt, sin, cos
from shapely.geometry import LineString
from game_core.constants import *
from game_core.utils import sys_text_object, animate_explosion, halt_whole_game
from random import randint


class Tank:
    """
    Class which represents tank object in game
    """

    def __init__(self, game_display, pos, health_bar_pos, color):
        """
        Initialize tank
        :param game_display: handle to display
        :param pos: initial position of the tank as list
        :param health_bar_pos: position of health bar os tuple
        :param color: color of this player tanks
        """
        self.position = list(pos)
        self.health_bar_position = health_bar_pos
        self.tank_health = initial_tank_health
        self.turret_angle = initial_turret_angle + (randint(0, int(pi / angle_step)) * angle_step)
        self.player_color = color
        self.turret_end_x = 0
        self.turret_end_y = 0
        self.tank_power = 50
        self.game_display = game_display
        self.explosion_sound = pygame.mixer.Sound("assets/music/Explosion3.wav")
        self.fire_sound = pygame.mixer.Sound("assets/music/Cannon1.wav")
        self.special_counter = 0
        self.weapon_index = 0
        self.fuel = tank_fuel
        self.shield = initial_shield

    def calculate_distance_from_tank_center(self, explosion_point):
        """
        Calculates distance from explosion_point to tank center
        :param explosion_point: coordinates of explosion point as tuple
        :return: distance to tank center
        """
        return int(sqrt((explosion_point[0]-self.position[0])**2+(explosion_point[1]-self.position[1])**2))

    def check_collision_with_tank(self, shell_line):
        """
        Checks whether there was a collision with tank and returns collision coordinates
        :param shell_line: trajectory line of the shell
        :return: intersection point coordinates or None
        """
        tank_line1 = LineString([[self.position[0] - int(tank_width / 2), self.position[1]],
                                 [self.position[0] + int(tank_width / 2), self.position[1]]])
        tank_line2 = LineString([[self.position[0] - int(tank_width / 2), self.position[1]],
                                 [self.position[0] - int(tank_width / 2), self.position[1] + tank_height]])
        tank_line3 = LineString([[self.position[0] + int(tank_width / 2), self.position[1]],
                                 [self.position[0] + int(tank_width / 2), self.position[1] + tank_height]])
        tank_line4 = LineString([[self.position[0] - int(tank_width / 2), self.position[1] + tank_height],
                                 [self.position[0] + int(tank_width / 2), self.position[1] + tank_height]])
        intersection = tank_line1.intersection(shell_line)
        if intersection:
            return int(intersection.x), int(intersection.y)

        intersection = tank_line2.intersection(shell_line)
        if intersection:
            return int(intersection.x), int(intersection.y)

        intersection = tank_line3.intersection(shell_line)
        if intersection:
            return int(intersection.x), int(intersection.y)

        intersection = tank_line4.intersection(shell_line)
        if intersection:
            return int(intersection.x), int(intersection.y)
        return None

    def apply_damage(self, explosion_point, explosion_power, explosion_radius):
        """
        Applies damage taken by tank regarding to position of explosion point and its power
        :param explosion_radius: radius of explosion
        :param explosion_point: coordinates of explosion point
        :param explosion_power: power of explosion
        :return: True if tank is destructed, False otherwise
        """
        distance_from_tank = self.calculate_distance_from_tank_center(explosion_point)
        damage = 0
        if distance_from_tank < explosion_radius:
            damage = int(((explosion_radius - distance_from_tank) / explosion_radius) * explosion_power)

        # Shield absorbs incoming damage before health is affected
        if self.shield > 0 and damage > 0:
            absorbed = min(self.shield, damage)
            self.shield -= absorbed
            damage -= absorbed

        self.tank_health = max(self.tank_health - damage, 0)
        if self.tank_health == 0:
            return True
        else:
            return False

    def draw_tank(self):
        """
        Draws this tank on specified game display
        :param game_display: PyGame display where the tank should appear
        :return: none
        """
        x = self.position[0]
        y = self.position[1]
        pygame.draw.circle(self.game_display, self.player_color,  (x, y), int(tank_height/4*3))
        pygame.draw.rect(self.game_display, self.player_color, (x-int(tank_width/2), y, tank_width, tank_height))

        self.turret_end_x = x + int(sin(self.turret_angle) * turret_length)
        self.turret_end_y = (y-2) - int(cos(self.turret_angle) * turret_length)
        pygame.draw.line(self.game_display,
                         self.player_color,
                         (x, y-2),
                         (self.turret_end_x, self.turret_end_y),
                         turret_width)

        # draw wheels? is it needed??
        pygame.draw.circle(self.game_display, self.player_color, (x - 15, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x - 10, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x - 5, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x + 5, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x + 10, y + tank_height), wheel_width)
        pygame.draw.circle(self.game_display, self.player_color, (x + 15, y + tank_height), wheel_width)

    def get_turret_end_coordinates(self):
        """
        Returns coordinates of the turret end
        :return: turret end coordinates as tuple
        """
        return self.turret_end_x, self.turret_end_y

    def _draw_parachute(self, color):
        """
        Draw a simple parachute canopy + strings above the tank in the given colour.
        """
        x = self.position[0]
        y = self.position[1]
        canopy_r = 25
        # Canopy top sits 18 px above the tank body top
        canopy_top_y = y - tank_height - canopy_r - 18
        # Semicircular canopy
        pygame.draw.arc(self.game_display, color,
                        (x - canopy_r, canopy_top_y, canopy_r * 2, canopy_r * 2),
                        0, pi, 3)
        # Two strings from canopy rim to tank top
        pygame.draw.line(self.game_display, color,
                         (x - canopy_r, canopy_top_y + canopy_r),
                         (x - int(tank_width / 4), y - tank_height), 1)
        pygame.draw.line(self.game_display, color,
                         (x + canopy_r, canopy_top_y + canopy_r),
                         (x + int(tank_width / 4), y - tank_height), 1)

    def update_tank_coordinates(self, move_tank):
        """
        Update coordinates of the tank
        :param move_tank: change of X coordinate
        :return: none
        """
        coord_x = self.position[0]
        if move_tank > 0:
            self.position[0] = min(coord_x + move_tank, display_width - int(tank_width / 2))
        elif move_tank < 0:
            self.position[0] = max(coord_x + move_tank, int(tank_width / 2))

    def update_turret_angle(self, angle_change):
        """
        Update turret angle
        :param angle_change: angle change
        :return: none
        """
        current_angle = self.turret_angle
        if angle_change > 0:
            self.turret_angle = min(current_angle + angle_change, pi / 2)
        elif angle_change < 0:
            self.turret_angle = max(current_angle + angle_change, -pi / 2)

    def update_tank_power(self, power_change):
        """
        Update tank's power
        :param power_change: change of power
        :return: none
        """
        current_power = self.tank_power
        if power_change > 0:
            self.tank_power = min(current_power + power_change, 100)
        elif power_change < 0:
            self.tank_power = max(current_power + power_change, 0)

    def get_init_data_for_shell(self):
        """
        Returns all required parameters to shoot a shell
        :return: (tank_power, turret_angle, fire_sound, color, (turret_end_x, turret_end_y))
        """
        ret_color = self.player_color
        return self.tank_power, self.turret_angle, self.fire_sound, ret_color, (self.turret_end_x, self.turret_end_y)

    def show_tanks_power(self):
        """
        Displays tank's power to screen
        :return: none
        """
        (text_surface, rect_size) = sys_text_object("Power: " + str(self.tank_power) + "%", white, FontSize.SMALL)
        self.game_display.blit(text_surface, [int(display_width / 2) - int(rect_size.width / 2), 28])

    def draw_health_bar(self, active=False):
        """
        Draws health bar of a tank on the screen
        :return: none
        """
        color = low_health_color
        if self.tank_health > 65:
            color = good_health_color
        elif self.tank_health > 40:
            color = normal_health_color

        if active:
            color = white
        pygame.draw.rect(self.game_display,
                         color,
                         (self.health_bar_position[0], self.health_bar_position[1], self.tank_health, 25))
        pygame.draw.rect(self.game_display,
                         white,
                         (self.health_bar_position[0], self.health_bar_position[1], 100, 25),
                         2)
        # Shield bar (blue, drawn below the health bar; outline always visible)
        if self.shield > 0:
            pygame.draw.rect(self.game_display, (0, 120, 255),
                             (self.health_bar_position[0], self.health_bar_position[1] + 28,
                              self.shield, 10))
        pygame.draw.rect(self.game_display, (100, 150, 255),
                         (self.health_bar_position[0], self.health_bar_position[1] + 28, 100, 10), 1)

    def self_destruct(self):
        """
        Animation of self destruction
        :return: none
        """
        animate_explosion(self.game_display, self.position, self.explosion_sound, tank_explosion_radius)

    def get_tank_health(self):
        """
        Getter for tanks health
        :return: tank's health
        """
        return self.tank_health

    def get_tank_position(self):
        """
        Return tanks center position
        :return: tank_position as tuple (x, y)
        """
        return self.position[0], self.position[1]

    def update_tank_position(self, new_coordinates):
        """
        Updates tank current position
        :param new_coordinates: new coordinates
        :return: none
        """
        self.position = list(new_coordinates)

    def get_weapon(self):
        """
        Return the currently selected WeaponDef.
        :return: WeaponDef namedtuple
        """
        return WEAPONS[self.weapon_index]

    def cycle_weapon(self, delta: int) -> None:
        """
        Cycle through available weapons.
        :param delta: +1 for next, -1 for previous
        """
        self.weapon_index = (self.weapon_index + delta) % len(WEAPONS)

    def show_weapon_name(self) -> None:
        """
        Display current weapon name below the power indicator.
        """
        weapon = self.get_weapon()
        (text_surface, rect_size) = sys_text_object(f"[ Q/E ]  {weapon.name}", white, FontSize.SMALL)
        self.game_display.blit(text_surface, [int(display_width / 2) - int(rect_size.width / 2), 48])

    def show_fuel(self) -> None:
        """
        Display remaining movement fuel below the weapon name.
        """
        (text_surface, rect_size) = sys_text_object(f"Fuel: {max(0, self.fuel)}", white, FontSize.SMALL)
        self.game_display.blit(text_surface, [int(display_width / 2) - int(rect_size.width / 2), 68])

    def refuel(self) -> None:
        """
        Restore full fuel at the start of a new turn.
        """
        self.fuel = tank_fuel

    def show_tank_special(self):
        """
        Show tank as white, when chosen
        :return: none
        """
        self.special_counter += 1
        if self.special_counter % 10 == 0:
            real_color = self.player_color
            self.player_color = white
            self.draw_tank()
            self.draw_health_bar(True)
            self.player_color = real_color
            self.special_counter = 0

    def animate_tank_fall(self, desirable_height):
        """
        Animate tank falling.  Deploys a parachute if the drop is large enough.
        :param desirable_height: target y coordinate (pixels, pygame down-positive)
        :return: none
        """
        fall_distance = desirable_height - self.position[1]
        use_parachute = fall_distance > parachute_threshold
        clock = pygame.time.Clock()
        while self.position[1] != desirable_height:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    halt_whole_game()

            # Erase current position (draw in black)
            temp_color = self.player_color
            self.player_color = black
            self.draw_tank()
            if use_parachute:
                self._draw_parachute(black)

            # Move one pixel downward
            self.position[1] += 1

            # Draw at new position
            self.player_color = temp_color
            self.draw_tank()
            if use_parachute:
                self._draw_parachute(self.player_color)

            pygame.display.update()
            # Slower fall speed when parachute is deployed
            clock.tick(60 if use_parachute else 100)

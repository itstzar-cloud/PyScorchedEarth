import pygame
from shapely.geometry import LineString
from random import choice, uniform
from math import sin, cos
from game_core.constants import *
from game_core.ground import Ground
from game_core.player import Player
from game_core.utils import animate_ground_sloughing, halt_whole_game, animate_explosion, message_to_screen, sys_text_object


class GameManager:
    """
    Class which represents game manager object in game
    """
    def __init__(self, player_number, tank_number):
        """
        Init function
        :param player_number: number of players
        :param tank_number: number of tanks for each player
        """
        self.players = []
        self.active_player = None
        _info = pygame.display.Info()
        _win_w = min(display_width,  _info.current_w)
        _win_h = min(display_height, _info.current_h - 40)
        self.game_display = pygame.display.set_mode((_win_w, _win_h), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption('ScorchedEarth')
        self.clock = pygame.time.Clock()
        self.strike_earth_sound = pygame.mixer.Sound("assets/music/Explosion1.wav")
        self.normal_strike_sound = pygame.mixer.Sound("assets/music/Explosion2.wav")
        self.ground = None
        self.players_number = player_number
        self.tank_number = tank_number
        self.wind = 0.0

    def reinitialize_players(self):
        """
        Reinitialize available tanks in the game
        :return: none
        """
        self.ground = Ground(self.game_display)
        self.players = []
        left_colors = player_colors[:]
        for i in range(self.players_number):
            chosen_color = choice(left_colors)
            left_colors.remove(chosen_color)
            self.players.append(Player(self.game_display, self.tank_number, chosen_color, i))
        init_tanks_positions = []
        for player in self.players:
            player.initialize_tanks(init_tanks_positions, self.ground)
        self.active_player = self.players[0]
        self.generate_wind()

    def generate_wind(self):
        """
        Generate a new random wind value for the next turn.
        Positive = blowing right, negative = blowing left.
        """
        self.wind = round(uniform(-max_wind, max_wind), 1)

    def draw_wind_indicator(self):
        """
        Draw a wind bar and label at the top-centre of the screen.
        The bar extends left or right from centre based on wind direction/strength.
        """
        cx = display_width // 2
        cy = 10
        bar_height = 14

        # Label
        label_surf, label_rect = sys_text_object("WIND", white)
        label_rect.right = cx - wind_bar_max_width - 8
        label_rect.top = cy
        self.game_display.blit(label_surf, label_rect)

        # Background track
        pygame.draw.rect(self.game_display, dark_gray,
                         (cx - wind_bar_max_width, cy, wind_bar_max_width * 2, bar_height))

        # Filled bar (orange)
        fill_width = int(abs(self.wind) / max_wind * wind_bar_max_width)
        if self.wind >= 0:
            pygame.draw.rect(self.game_display, orange,
                             (cx, cy, fill_width, bar_height))
        else:
            pygame.draw.rect(self.game_display, orange,
                             (cx - fill_width, cy, fill_width, bar_height))

        # Centre divider
        pygame.draw.line(self.game_display, white,
                         (cx, cy), (cx, cy + bar_height), 2)

        # Numeric value + direction arrow
        direction = ">" if self.wind >= 0 else "<"
        value_surf, value_rect = sys_text_object(f"{direction} {abs(self.wind):.1f}", white)
        value_rect.left = cx + wind_bar_max_width + 8
        value_rect.top = cy
        self.game_display.blit(value_surf, value_rect)

    def check_collision(self, prev_shell_position, current_shell_position):
        """
        Checks collision of shell with other objects and return coordinates of shell collision
        :param prev_shell_position: Coordinates of previous shell position
        :param current_shell_position: Coordinates of updated shell position
        :return: Coordinates of collision or None if no collision detected
        """
        line1 = LineString([prev_shell_position, current_shell_position])

        for player in self.players:
            intersection = player.check_collision_with_tanks(line1)
            if intersection:
                return intersection

        return self.ground.check_collision(line1)

    def correct_ground(self, point, explosion_radius):
        """
        Corrects ground after explosion
        :param point: point of explosion
        :param explosion_radius: radius of explosion
        :return: none
        """
        left_ground = self.ground.update_after_explosion(point, explosion_radius)
        if len(left_ground) > 0:
            self.draw_all()
            animate_ground_sloughing(self.game_display, left_ground, self.ground)
            self.ground.update_after_sloughing(left_ground)

    def apply_players_damages(self, collision_point, shell_power, shell_radius):
        """
        Applies damages for players tanks
        :param collision_point: point of collision
        :param shell_power: power of shell
        :param shell_radius: radius of shell
        :return: none
        """
        explosion_points = []
        for player in self.players:
            explosion_points.extend(player.apply_damage(collision_point, shell_power, shell_radius))
        if len(explosion_points) > 0:
            for point in explosion_points:
                self.correct_ground(point, tank_explosion_radius)
                self.apply_players_damages(point, tank_explosion_power, tank_explosion_radius)

    def correct_tanks_heights(self):
        """
        Corrects heights of all players' tanks
        :return: none
        """
        for player in self.players:
            player.correct_tanks_heights(self.ground)

    def _get_ground_height_for_tank(self, x):
        """
        Return the average ground height under the tank body at horizontal position x.
        :param x: tank centre x coordinate
        :return: ground y pixel (higher value = lower on screen)
        """
        heights = [self.ground.get_ground_height_at_point(px)
                   for px in range(x - int(tank_width / 2), x + int(tank_width / 2))]
        return int(sum(heights) / len(heights))

    def _fly_shell(self, start_pos, speed, angle, color, dot_radius=4):
        """
        Animate a single shell in flight. Returns collision point or None if out of bounds.
        :param start_pos: (x, y) starting position
        :param speed: initial shell speed
        :param angle: launch angle (radians)
        :param color: dot colour
        :param dot_radius: drawn shell radius in pixels
        :return: (x, y) collision point or None
        """
        shell_position = list(start_pos)
        elapsed_time = 0.1

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    halt_whole_game()

            prev_pos = list(shell_position)
            vertical_speed = -((speed * cos(angle)) - 10 * elapsed_time / 2)
            horizontal_speed = (speed * sin(angle)) + self.wind
            shell_position[0] += int(horizontal_speed * elapsed_time)
            shell_position[1] += int(vertical_speed * elapsed_time)
            elapsed_time += 0.1

            if shell_position[1] > 2 * display_height:
                return None
            if shell_position[0] < 0 or shell_position[0] > display_width:
                return None

            collision_point = self.check_collision(prev_pos, shell_position)
            if collision_point:
                return collision_point

            pygame.draw.circle(self.game_display, color, (shell_position[0], shell_position[1]), dot_radius)
            pygame.display.update()
            self.clock.tick(60)

    def _explode(self, point, weapon, sound=None):
        """
        Trigger explosion effects, ground correction, and player damage.
        :param point: (x, y) explosion centre
        :param weapon: WeaponDef to read power/radius from
        :param sound: optional override sound; defaults to strike_earth_sound
        """
        snd = sound if sound else self.strike_earth_sound
        animate_explosion(self.game_display, point, snd, weapon.radius)
        self.correct_ground(point, weapon.radius)
        self.apply_players_damages(point, weapon.power, weapon.radius)
        self.correct_tanks_heights()

    def fire_weapon(self, tank_object):
        """
        Dispatch firing to the correct method based on the tank's active weapon.
        :param tank_object: the firing Tank instance
        """
        weapon = tank_object.get_weapon()
        (power, gun_angle, fire_sound, color, gun_end_coord) = tank_object.get_init_data_for_shell()
        pygame.mixer.Sound.play(fire_sound)
        speed = min_shell_speed + shell_speed_step * power

        if weapon.shell_type == 'simple':
            self._fire_simple(gun_end_coord, speed, gun_angle, color, weapon)
        elif weapon.shell_type == 'mirv':
            self._fire_mirv(gun_end_coord, speed, gun_angle, color, weapon)
        elif weapon.shell_type == 'napalm':
            self._fire_napalm(gun_end_coord, speed, gun_angle, color, weapon)
        elif weapon.shell_type == 'nuke':
            self._fire_nuke(gun_end_coord, speed, gun_angle, color, weapon)

    def _fire_simple(self, start_pos, speed, angle, color, weapon):
        """Single shell that explodes on impact."""
        collision_point = self._fly_shell(start_pos, speed, angle, color)
        if collision_point:
            self._explode(collision_point, weapon)

    def _fire_mirv(self, start_pos, speed, angle, color, weapon):
        """
        Shell that flies to apogee then splits into 5 sub-warheads.
        If it hits terrain before apogee it detonates like a normal shell.
        """
        shell_position = list(start_pos)
        elapsed_time = 0.1
        prev_vy = None
        apogee_pos = None

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    halt_whole_game()

            prev_pos = list(shell_position)
            vy = -((speed * cos(angle)) - 10 * elapsed_time / 2)
            vx = (speed * sin(angle)) + self.wind
            shell_position[0] += int(vx * elapsed_time)
            shell_position[1] += int(vy * elapsed_time)
            elapsed_time += 0.1

            if shell_position[1] > 2 * display_height:
                return
            if shell_position[0] < 0 or shell_position[0] > display_width:
                return

            collision_point = self.check_collision(prev_pos, shell_position)
            if collision_point:
                # Hit ground before apogee — detonate as normal shell
                self._explode(collision_point, weapon, self.normal_strike_sound)
                return

            # Draw main shell (larger dot, cyan tint)
            pygame.draw.circle(self.game_display, (0, 220, 255), (shell_position[0], shell_position[1]), 5)
            pygame.display.update()
            self.clock.tick(60)

            # Apogee = vertical velocity flips from up to down
            if prev_vy is not None and prev_vy < 0 <= vy:
                apogee_pos = list(shell_position)
                break
            prev_vy = vy

        if apogee_pos is None:
            return

        # Fire 5 sub-warheads spreading from apogee
        sub_speed = speed * 0.65
        spread_offsets = [-pi / 4, -pi / 8, 0, pi / 8, pi / 4]
        for offset in spread_offsets:
            sub_angle = angle + offset
            cp = self._fly_shell(apogee_pos, sub_speed, sub_angle, (0, 220, 255), dot_radius=3)
            if cp:
                self._explode(cp, weapon, self.normal_strike_sound)

    def _fire_napalm(self, start_pos, speed, angle, color, weapon):
        """
        Shell that bursts into a horizontal spray of fire clusters on impact.
        """
        collision_point = self._fly_shell(start_pos, speed, angle, orange)
        if not collision_point:
            return

        # Five fire clusters spreading left/right from impact
        spreads = [-80, -40, 0, 40, 80]
        for spread in spreads:
            cx = collision_point[0] + spread
            cy = collision_point[1]
            cluster_power = weapon.power // 3
            cluster_radius = weapon.radius // 3
            animate_explosion(self.game_display, (cx, cy), self.normal_strike_sound, cluster_radius)
            self.correct_ground((cx, cy), cluster_radius)
            self.apply_players_damages((cx, cy), cluster_power, cluster_radius)
        self.correct_tanks_heights()

    def _fire_nuke(self, start_pos, speed, angle, color, weapon):
        """
        Massive explosion with a white screen flash.
        """
        collision_point = self._fly_shell(start_pos, speed, angle, (255, 255, 100), dot_radius=6)
        if not collision_point:
            return

        # Screen flash
        flash = pygame.surface.Surface((display_width, display_height))
        flash.fill(white)
        self.game_display.blit(flash, (0, 0))
        pygame.display.update()
        pygame.time.wait(120)

        self._explode(collision_point, weapon)

    def update_players(self):
        """
        Updates each player information
        :return: none
        """
        left_players = []
        for player in self.players:
            if player.is_in_game():
                left_players.append(player)

        if self.active_player in left_players:
            self.active_player = left_players[(left_players.index(self.active_player) + 1) % len(left_players)]
        else:
            if len(left_players) > 0:
                init_index = self.players.index(self.active_player)
                while True:
                    self.active_player = self.players[(init_index + 1) % len(self.players)]
                    if self.active_player in left_players:
                        break

        self.players = left_players

    def draw_all(self):
        """
        Draws all elements on display
        :return: none
        """
        self.game_display.fill(black)
        self.ground.draw()
        for player in self.players:
            player.draw_tanks_and_bars()
        self.draw_wind_indicator()

    def run(self):
        """
        Run game
        :return: none
        """
        self.reinitialize_players()
        active_tank = self.players[0].next_active_tank()
        game_exit = False
        game_over = False
        fps = 15

        angle_change = 0
        power_change = 0
        move_change = 0

        while not game_exit:
            if game_over:
                message_to_screen(self.game_display, "Game over", red, -50, FontSize.LARGE, sys_font=False)
                message_to_screen(self.game_display, "S - play again", green, 50, sys_font=False)
                message_to_screen(self.game_display, "Q - quit", green, 80, sys_font=False)
                pygame.display.update()
                while game_over:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_q:
                                game_exit = True
                                game_over = False
                            if event.key == pygame.K_s:
                                self.reinitialize_players()
                                active_tank = self.players[0].next_active_tank()
                                move_change = 0
                                game_exit = False
                                game_over = False
                                break
                        elif event.type == pygame.QUIT:
                            game_exit = True
                            game_over = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        power_change = 1
                    elif event.key == pygame.K_DOWN:
                        power_change = -1
                    elif event.key == pygame.K_LEFT:
                        # change angle
                        angle_change = -angle_step
                    elif event.key == pygame.K_RIGHT:
                        # change angle
                        angle_change = angle_step
                    elif event.key == pygame.K_a:
                        move_change = -1
                    elif event.key == pygame.K_d:
                        move_change = 1
                    elif event.key == pygame.K_q:
                        active_tank.cycle_weapon(-1)
                    elif event.key == pygame.K_e:
                        active_tank.cycle_weapon(1)
                    elif event.key == pygame.K_SPACE:
                        self.fire_weapon(active_tank)
                        self.generate_wind()
                        self.update_players()
                        active_tank = self.active_player.next_active_tank()
                        move_change = 0
                        if active_tank:
                            active_tank.refuel()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                        angle_change = 0
                    elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        power_change = 0
                    elif event.key == pygame.K_a or event.key == pygame.K_d:
                        move_change = 0

            self.draw_all()

            if len(self.players) <= 1:
                game_over = True

            if active_tank:
                active_tank.show_tank_special()
                active_tank.show_tanks_power()
                active_tank.show_weapon_name()
                active_tank.show_fuel()
                active_tank.update_turret_angle(angle_change)
                active_tank.update_tank_power(power_change)
                # Tank movement (A / D) — consumed fuel limits travel distance
                if move_change != 0 and active_tank.fuel > 0:
                    prev_x = active_tank.get_tank_position()[0]
                    active_tank.update_tank_coordinates(move_step * move_change)
                    new_x = active_tank.get_tank_position()[0]
                    if new_x != prev_x:
                        active_tank.fuel = max(0, active_tank.fuel - 1)
                        opt_h = self._get_ground_height_for_tank(new_x)
                        active_tank.update_tank_position((new_x, opt_h - full_tank_height))

            pygame.display.update()
            self.clock.tick(fps)

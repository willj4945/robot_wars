"""Robot state, plus the safe objects that student code is allowed to touch.

Headings work like a compass: 0 is up, 90 is right, 180 is down, 270 is left.
"""

import math

from . import config


def compass_angle(from_x, from_y, to_x, to_y):
    """Compass heading pointing from one point to another."""
    return math.degrees(math.atan2(to_x - from_x, -(to_y - from_y))) % 360


def angle_difference(current, target):
    """Signed turn (-180..180) needed to get from `current` to `target`."""
    return (target - current + 180) % 360 - 180


def _xy(thing):
    """Accept an enemy, `me`, or an (x, y) pair."""
    if isinstance(thing, (tuple, list)):
        return thing[0], thing[1]
    return thing.x, thing.y


class Robot:
    """The engine's real robot. Students never get this object."""

    def __init__(self, program, x, y, heading):
        self.program = program
        self.name = program.name
        self.color = program.color
        self.x = float(x)
        self.y = float(y)
        self.heading = heading % 360
        self.health = float(config.START_HEALTH)
        self.speed = 0.0
        self.gun_heat = 0
        self.memory = {}

        self.alive = True
        self.status = "fighting"      # or "destroyed", "disqualified: ..."
        self.died_at = None

        # stats
        self.shots = 0
        self.hits = 0
        self.damage_dealt = 0.0
        self.distance_moved = 0.0
        self.errors = 0
        self.slow_turns = 0
        self.think_time_total = 0.0
        self.think_calls = 0
        self.last_error = None

        self.reset_orders()

    def reset_orders(self):
        self.order_speed = 0.0
        self.order_turn = 0.0
        self.order_fire = 0


class Me:
    """What a bot sees as `me`. Read your stats and give orders for this tick."""

    __slots__ = ("_robot", "_world")

    def __init__(self, robot, world):
        self._robot = robot
        self._world = world

    # ---- information -------------------------------------------------
    @property
    def name(self):
        return self._robot.name

    @property
    def x(self):
        return self._robot.x

    @property
    def y(self):
        return self._robot.y

    @property
    def heading(self):
        return self._robot.heading

    @property
    def health(self):
        return self._robot.health

    @property
    def speed(self):
        return self._robot.speed

    @property
    def gun_heat(self):
        """Ticks until you can fire again (0 means ready)."""
        return self._robot.gun_heat

    @property
    def memory(self):
        """A dictionary that keeps its contents between ticks."""
        return self._robot.memory

    # ---- helpers -----------------------------------------------------
    def distance_to(self, thing):
        tx, ty = _xy(thing)
        return math.hypot(tx - self.x, ty - self.y)

    def angle_to(self, thing):
        """Compass heading from you to the thing."""
        tx, ty = _xy(thing)
        return compass_angle(self.x, self.y, tx, ty)

    def closest(self, things):
        """The nearest thing in a list, or None if the list is empty."""
        if not things:
            return None
        return min(things, key=self.distance_to)

    def can_fire(self):
        return self._robot.gun_heat == 0

    def near_wall(self, distance=config.NEAR_WALL_DISTANCE):
        return (
            self.x < distance
            or self.y < distance
            or self.x > config.ARENA_WIDTH - distance
            or self.y > config.ARENA_HEIGHT - distance
        )

    # ---- orders (the last order of each kind in a tick wins) ---------
    def forward(self, speed=config.MAX_SPEED):
        self._robot.order_speed = _clamp(speed, 0, config.MAX_SPEED)

    def backward(self, speed=config.MAX_SPEED):
        self._robot.order_speed = -_clamp(speed, 0, config.MAX_SPEED)

    def stop(self):
        self._robot.order_speed = 0.0

    def turn_left(self, degrees=config.MAX_TURN):
        self._robot.order_turn = -_clamp(degrees, 0, config.MAX_TURN)

    def turn_right(self, degrees=config.MAX_TURN):
        self._robot.order_turn = _clamp(degrees, 0, config.MAX_TURN)

    def turn_toward(self, thing):
        """Turn (as fast as allowed) to face the thing. Does nothing if thing is None."""
        if thing is None:
            return
        self.turn_to_heading(self.angle_to(thing))

    def turn_to_heading(self, heading):
        diff = angle_difference(self.heading, heading)
        self._robot.order_turn = _clamp(diff, -config.MAX_TURN, config.MAX_TURN)

    def fire(self, power=1):
        """Fire a bullet (power 1-3). Returns True if it actually fired."""
        if not self.can_fire():
            return False
        self._robot.order_fire = int(_clamp(round(power), config.MIN_POWER, config.MAX_POWER))
        return True


class EnemyView:
    """A snapshot of another robot. Changing it does nothing to the real robot."""

    __slots__ = ("name", "x", "y", "heading", "health", "speed")

    def __init__(self, robot):
        self.name = robot.name
        self.x = robot.x
        self.y = robot.y
        self.heading = robot.heading
        self.health = robot.health
        self.speed = robot.speed

    def __repr__(self):
        return f"<Enemy {self.name} at ({self.x:.0f}, {self.y:.0f}) health {self.health:.0f}>"


class ArenaInfo:
    __slots__ = ("width", "height", "tick", "max_ticks")

    def __init__(self, tick):
        self.width = config.ARENA_WIDTH
        self.height = config.ARENA_HEIGHT
        self.tick = tick
        self.max_ticks = config.MAX_TICKS


def _clamp(value, low, high):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(value):
        return 0.0
    return max(low, min(high, value))

"""The physics: one call to step() is one tick of the game."""

import math

from . import config
from .guard import run_think
from .robot import ArenaInfo, EnemyView, Me


class Bullet:
    __slots__ = ("x", "y", "dx", "dy", "power", "owner")

    def __init__(self, x, y, heading, power, owner):
        rad = math.radians(heading)
        self.x = x
        self.y = y
        self.dx = math.sin(rad) * config.BULLET_SPEED
        self.dy = -math.cos(rad) * config.BULLET_SPEED
        self.power = power
        self.owner = owner


class World:
    def __init__(self, robots):
        self.robots = robots
        self.bullets = []
        self.tick = 0
        self.events = []     # things the viewer may want to draw this tick

    @property
    def alive(self):
        return [r for r in self.robots if r.alive]

    def is_over(self):
        return len(self.alive) <= 1 or self.tick >= config.MAX_TICKS

    def step(self):
        self.events = []
        fighters = self.alive
        arena = ArenaInfo(self.tick)

        # 1. Everyone decides, all looking at the same moment in time.
        views = {r: EnemyView(r) for r in fighters}
        for robot in fighters:
            if robot.gun_heat > 0:
                robot.gun_heat -= 1
            enemies = [views[o] for o in fighters if o is not robot]
            problem = run_think(robot, Me(robot, self), enemies, arena)
            if problem:
                self.kill(robot, problem)

        # 2. Carry out the orders.
        for robot in self.alive:
            self._move(robot)
            if robot.order_fire:
                self._fire(robot, robot.order_fire)

        self._robot_collisions()
        self._move_bullets()

        for robot in self.alive:
            if robot.health <= 0:
                robot.health = 0
                self.kill(robot, "destroyed")

        self.tick += 1

    def kill(self, robot, status):
        if not robot.alive:
            return
        robot.alive = False
        robot.status = status
        robot.died_at = self.tick
        self.events.append(("boom", robot.x, robot.y, robot.color))

    def _move(self, robot):
        robot.heading = (robot.heading + robot.order_turn) % 360
        robot.speed = robot.order_speed
        rad = math.radians(robot.heading)
        new_x = robot.x + math.sin(rad) * robot.speed
        new_y = robot.y - math.cos(rad) * robot.speed

        r = config.ROBOT_RADIUS
        clamped_x = min(max(new_x, r), config.ARENA_WIDTH - r)
        clamped_y = min(max(new_y, r), config.ARENA_HEIGHT - r)
        if clamped_x != new_x or clamped_y != new_y:
            robot.health -= config.WALL_DAMAGE
            self.events.append(("wall", clamped_x, clamped_y))

        robot.distance_moved += math.hypot(clamped_x - robot.x, clamped_y - robot.y)
        robot.x, robot.y = clamped_x, clamped_y

    def _fire(self, robot, power):
        if robot.gun_heat > 0:
            return
        rad = math.radians(robot.heading)
        tip = config.ROBOT_RADIUS + config.BULLET_RADIUS + 1
        x = robot.x + math.sin(rad) * tip
        y = robot.y - math.cos(rad) * tip
        self.bullets.append(Bullet(x, y, robot.heading, power, robot))
        robot.gun_heat = config.HEAT_PER_POWER * power
        robot.shots += 1
        self.events.append(("fire", x, y))

    def _robot_collisions(self):
        fighters = self.alive
        min_dist = config.ROBOT_RADIUS * 2
        for i, a in enumerate(fighters):
            for b in fighters[i + 1:]:
                dx, dy = b.x - a.x, b.y - a.y
                dist = math.hypot(dx, dy)
                if dist >= min_dist:
                    continue
                if dist == 0:
                    dx, dy, dist = 1.0, 0.0, 1.0
                push = (min_dist - dist) / 2
                nx, ny = dx / dist, dy / dist
                r = config.ROBOT_RADIUS
                a.x = min(max(a.x - nx * push, r), config.ARENA_WIDTH - r)
                a.y = min(max(a.y - ny * push, r), config.ARENA_HEIGHT - r)
                b.x = min(max(b.x + nx * push, r), config.ARENA_WIDTH - r)
                b.y = min(max(b.y + ny * push, r), config.ARENA_HEIGHT - r)
                a.health -= config.RAM_DAMAGE
                b.health -= config.RAM_DAMAGE

    def _move_bullets(self):
        hit_dist = config.ROBOT_RADIUS + config.BULLET_RADIUS
        remaining = []
        for bullet in self.bullets:
            bullet.x += bullet.dx
            bullet.y += bullet.dy
            if not (0 <= bullet.x <= config.ARENA_WIDTH and 0 <= bullet.y <= config.ARENA_HEIGHT):
                continue
            target = None
            for robot in self.alive:
                if robot is not bullet.owner and math.hypot(robot.x - bullet.x, robot.y - bullet.y) <= hit_dist:
                    target = robot
                    break
            if target is None:
                remaining.append(bullet)
                continue
            damage = min(config.DAMAGE_PER_POWER * bullet.power, max(target.health, 0))
            target.health -= config.DAMAGE_PER_POWER * bullet.power
            bullet.owner.hits += 1
            bullet.owner.damage_dealt += damage
            self.events.append(("hit", bullet.x, bullet.y))
        self.bullets = remaining

"""Set up a match, run it, and work out who won."""

import math
import random
from dataclasses import dataclass, field

from . import config
from .robot import Robot
from .world import World


@dataclass
class MatchResult:
    winner: object                     # the winning Robot, or None for a draw
    placements: list                   # Robots, best first
    ticks: int
    reason: str
    robots: list = field(default_factory=list)

    @property
    def winner_name(self):
        return self.winner.name if self.winner else None


class Match:
    def __init__(self, programs, seed=None):
        if len(programs) < 2:
            raise ValueError("A match needs at least two robots.")
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        rng = random.Random(self.seed)
        random.seed(self.seed)   # bots that use `random` get repeatable results too

        order = list(programs)
        rng.shuffle(order)
        spots = _spawn_points(len(order), rng)
        robots = [Robot(p, x, y, h) for p, (x, y, h) in zip(order, spots)]
        _unique_names(robots)
        robots.sort(key=lambda r: programs.index(r.program))
        self.world = World(robots)
        self.result = None

    @property
    def robots(self):
        return self.world.robots

    def step(self):
        """Advance one tick. Returns the MatchResult once the match is over."""
        if self.result:
            return self.result
        self.world.step()
        if self.world.is_over():
            self.result = self._decide()
        return self.result

    def run(self):
        while not self.result:
            self.step()
        return self.result

    def _decide(self):
        world = self.world
        alive = sorted(world.alive, key=lambda r: r.health, reverse=True)
        dead = sorted((r for r in world.robots if not r.alive), key=lambda r: r.died_at, reverse=True)
        placements = alive + dead

        if len(alive) == 1:
            return MatchResult(alive[0], placements, world.tick, "last robot standing", world.robots)
        if not alive:
            return MatchResult(None, placements, world.tick, "everyone was destroyed", world.robots)
        if alive[0].health > alive[1].health:
            return MatchResult(alive[0], placements, world.tick, "time up, most health", world.robots)
        return MatchResult(None, placements, world.tick, "time up, tied on health", world.robots)


def _spawn_points(count, rng):
    cx, cy = config.ARENA_WIDTH / 2, config.ARENA_HEIGHT / 2
    rx = config.ARENA_WIDTH / 2 - config.ROBOT_RADIUS * 4
    ry = config.ARENA_HEIGHT / 2 - config.ROBOT_RADIUS * 4
    offset = rng.uniform(0, 360) if count > 2 else rng.choice([90, 270]) + rng.uniform(-15, 15)
    spots = []
    for i in range(count):
        angle = math.radians(offset + i * 360 / count)
        x = cx + math.sin(angle) * rx
        y = cy - math.cos(angle) * ry
        facing = math.degrees(math.atan2(cx - x, -(cy - y))) + rng.uniform(-20, 20)
        spots.append((x, y, facing))
    return spots


def _unique_names(robots):
    seen = {}
    for robot in robots:
        seen[robot.name] = seen.get(robot.name, 0) + 1
        if seen[robot.name] > 1:
            robot.name = f"{robot.name} ({seen[robot.name]})"

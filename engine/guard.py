"""Run a bot's think() without letting a broken bot ruin the match."""

import time

from . import config
from .loader import describe_error


def run_think(robot, me, enemies, arena):
    """Call the bot's think(). Returns a message if something went wrong, else None."""
    robot.reset_orders()
    start = time.perf_counter()
    try:
        robot.program.think(me, enemies, arena)
    except Exception as exc:
        robot.reset_orders()
        robot.errors += 1
        robot.last_error = describe_error(exc, robot.program.path)
        if robot.errors >= config.MAX_ERRORS:
            return f"disqualified: crashed {robot.errors} times ({robot.last_error})"
        return None
    finally:
        elapsed = time.perf_counter() - start
        robot.think_time_total += elapsed
        robot.think_calls += 1

    if elapsed > config.THINK_TIME_LIMIT:
        robot.reset_orders()
        robot.slow_turns += 1
        robot.last_error = f"think() took {elapsed * 1000:.0f} ms (limit {config.THINK_TIME_LIMIT * 1000:.0f} ms)"
        if robot.slow_turns >= config.MAX_SLOW_TURNS:
            return f"disqualified: too slow {robot.slow_turns} times"
    return None

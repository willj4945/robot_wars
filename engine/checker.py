"""Test a bot file the same way the teacher will, with friendly results.

The bot runs in a separate process so an infinite loop can be caught and stopped.
"""

import io
import multiprocessing
import queue
import sys
from pathlib import Path

from . import EXAMPLES_DIR, config

TEST_TICKS = 500
LOAD_TIMEOUT = 10      # seconds
MATCH_TIMEOUT = 15     # seconds per test match

PASS, WARN, FAIL = "pass", "warn", "fail"
ICONS = {PASS: "✅", WARN: "⚠️ ", FAIL: "❌"}


def check_bot(path):
    """Returns a list of (status, message)."""
    path = Path(path).resolve()
    ctx = multiprocessing.get_context("spawn")
    results = ctx.Queue()
    worker = ctx.Process(target=_worker, args=(str(path), results), daemon=True)
    worker.start()
    checks = []
    try:
        _collect(results, worker, checks)
    finally:
        if worker.is_alive():
            worker.terminate()
        worker.join(1)
    return checks


def _collect(results, worker, checks):
    try:
        kind, *data = results.get(timeout=LOAD_TIMEOUT)
    except queue.Empty:
        checks.append((FAIL, "Your file got stuck while loading. Is there a loop outside think() that never ends?"))
        return
    if kind == "load_error":
        checks.append((FAIL, "Your file can't be loaded:\n" + _indent(data[0])))
        return
    name, color = data
    checks.append((PASS, f'Loads fine: NAME = "{name}", COLOR = {color}, think(me, enemies, arena) found'))
    checks.append((PASS, "Only uses allowed imports and commands"))

    stats = []
    opponent = None
    while True:
        try:
            kind, *data = results.get(timeout=MATCH_TIMEOUT)
        except queue.Empty:
            checks.append((FAIL, f"Got stuck fighting {opponent}. Is there a loop inside think() that never ends?"))
            return
        if kind == "start":
            opponent = data[0]
        elif kind == "done":
            stats.append(data[0])
        elif kind == "finished":
            break

    crashes = {}
    for s in stats:
        if s["errors"]:
            crashes.setdefault(s["last_error"], []).append(s["opponent"])
        elif s["slow"]:
            checks.append((FAIL, f"Too slow {s['slow']} times vs {s['opponent']}. Keep think() quick."))
        else:
            checks.append((PASS, f"No crashes vs {s['opponent']} ({s['outcome']})"))
    for error, opponents in crashes.items():
        checks.append((FAIL, f"Crashed vs {', '.join(opponents)}\n     {error}"))

    calls = sum(s["calls"] for s in stats)
    avg_ms = 1000 * sum(s["think_time"] for s in stats) / max(calls, 1)
    limit_ms = config.THINK_TIME_LIMIT * 1000
    if avg_ms < limit_ms / 5:
        checks.append((PASS, f"Fast enough: think() takes {avg_ms:.2f} ms on average"))
    else:
        checks.append((WARN, f"think() takes {avg_ms:.1f} ms on average. The limit is {limit_ms:.0f} ms, so it's close."))

    if not any(s["moved"] > 1 for s in stats):
        checks.append((WARN, "Your robot never moved. Try me.forward()"))
    if not any(s["shots"] for s in stats):
        checks.append((WARN, "Your robot never fired. Try me.fire()"))
    if any(s["printed"] for s in stats):
        checks.append((WARN, "Your robot uses print(). That's fine for testing, but it slows things down."))


def _worker(path, results):
    """Runs in the child process."""
    from .loader import BotLoadError, load_bot
    from .match import Match

    printed = io.StringIO()
    sys.stdout = printed
    try:
        program = load_bot(path)
    except BotLoadError as exc:
        results.put(("load_error", str(exc)))
        return
    results.put(("loaded", program.name, repr(program.color_name)))

    for example in sorted(EXAMPLES_DIR.glob("*.py")):
        opponent = load_bot(example)
        results.put(("start", opponent.name))
        match = Match([load_bot(path), opponent], seed=42)
        while match.world.tick < TEST_TICKS and not match.step():
            pass
        me = match.robots[0]
        if match.result and match.result.winner is me:
            outcome = "you won"
        elif not me.alive:
            outcome = "you lost" if me.status == "destroyed" else me.status
        elif match.result:
            outcome = "draw"
        else:
            outcome = f"still fighting after {TEST_TICKS} ticks"
        results.put(("done", {
            "opponent": opponent.name,
            "errors": me.errors,
            "slow": me.slow_turns,
            "last_error": me.last_error,
            "calls": me.think_calls,
            "think_time": me.think_time_total,
            "moved": me.distance_moved,
            "shots": me.shots,
            "printed": bool(printed.tell()),
            "outcome": outcome,
        }))
    results.put(("finished",))


def print_report(path, checks, out=None):
    out = out or sys.stdout
    icons = ICONS
    try:
        "".join(ICONS.values()).encode(out.encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        icons = {PASS: "[OK]  ", WARN: "[WARN]", FAIL: "[FAIL]"}
    print(f"\nChecking {Path(path).name}\n", file=out)
    for status, message in checks:
        print(f"  {icons[status]} {message}", file=out)
    print(file=out)
    return not any(status == FAIL for status, _ in checks)


def _indent(text):
    return "\n".join("     " + line for line in text.splitlines())

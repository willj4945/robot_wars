from pathlib import Path

import pytest

from engine import EXAMPLES_DIR, config
from engine.loader import BotLoadError, BotProgram, load_bot
from engine.match import Match
from engine.robot import angle_difference, compass_angle
from engine.tournament import Competition

BAD = Path(__file__).parent / "bad_bots"


def bot(think, name="Test"):
    return BotProgram(name, (255, 0, 0), think, Path(__file__))


def idle(me, enemies, arena):
    pass


def place(match, *spots):
    """Put the robots at exact (x, y, heading) positions."""
    for robot, (x, y, h) in zip(match.robots, spots):
        robot.x, robot.y, robot.heading = x, y, h


# ---- geometry ----------------------------------------------------------

def test_compass_angles():
    assert compass_angle(0, 0, 0, -10) == pytest.approx(0)
    assert compass_angle(0, 0, 10, 0) == pytest.approx(90)
    assert compass_angle(0, 0, 0, 10) == pytest.approx(180)
    assert compass_angle(0, 0, -10, 0) == pytest.approx(270)
    assert angle_difference(350, 10) == pytest.approx(20)
    assert angle_difference(10, 350) == pytest.approx(-20)


# ---- movement ----------------------------------------------------------

def test_forward_moves_in_heading_direction():
    m = Match([bot(lambda me, e, a: me.forward()), bot(idle)], seed=1)
    place(m, (400, 300, 90), (100, 100, 0))
    m.step()
    assert m.robots[0].x == pytest.approx(400 + config.MAX_SPEED)
    assert m.robots[0].y == pytest.approx(300)


def test_speed_and_turn_are_capped():
    def greedy(me, enemies, arena):
        me.forward(1000)
        me.turn_right(1000)
    m = Match([bot(greedy), bot(idle)], seed=1)
    place(m, (400, 300, 0), (100, 100, 0))
    m.step()
    assert m.robots[0].heading == pytest.approx(config.MAX_TURN)
    assert m.robots[0].speed == pytest.approx(config.MAX_SPEED)


def test_turn_toward_takes_short_way():
    m = Match([bot(lambda me, e, a: me.turn_toward((300, 300))), bot(idle)], seed=1)
    place(m, (400, 300, 0), (100, 100, 0))   # target is at 270, so turn left
    m.step()
    assert m.robots[0].heading == pytest.approx(360 - config.MAX_TURN)


def test_walls_stop_and_hurt():
    m = Match([bot(lambda me, e, a: me.forward()), bot(idle)], seed=1)
    place(m, (400, config.ROBOT_RADIUS + 1, 0), (100, 300, 0))
    m.step()
    m.step()
    assert m.robots[0].y == pytest.approx(config.ROBOT_RADIUS)
    assert m.robots[0].health < config.START_HEALTH


def test_orders_reset_each_tick():
    calls = []
    def once(me, enemies, arena):
        if not calls:
            me.forward()
        calls.append(1)
    m = Match([bot(once), bot(idle)], seed=1)
    place(m, (400, 300, 90), (100, 100, 0))
    m.step()
    m.step()
    assert m.robots[0].x == pytest.approx(400 + config.MAX_SPEED)


# ---- shooting ----------------------------------------------------------

def test_bullet_hits_and_gun_heats_up():
    def shooter(me, enemies, arena):
        me.fire(2)
    m = Match([bot(shooter), bot(idle)], seed=1)
    place(m, (400, 300, 90), (500, 300, 0))
    m.step()
    assert m.robots[0].gun_heat == config.HEAT_PER_POWER * 2
    for _ in range(10):
        m.step()
    target = m.robots[1]
    assert target.health == config.START_HEALTH - 2 * config.DAMAGE_PER_POWER
    assert m.robots[0].hits == 1
    assert m.robots[0].shots == 1


def test_cannot_fire_while_hot():
    m = Match([bot(lambda me, e, a: me.fire()), bot(idle)], seed=1)
    place(m, (400, 300, 0), (100, 500, 0))
    for _ in range(config.HEAT_PER_POWER):
        m.step()
    assert m.robots[0].shots == 1
    m.step()
    assert m.robots[0].shots == 2


def test_enemy_views_are_copies():
    def meddler(me, enemies, arena):
        enemies[0].health = 0
    m = Match([bot(meddler), bot(idle)], seed=1)
    m.step()
    assert m.robots[1].health == config.START_HEALTH


# ---- winning -----------------------------------------------------------

def test_last_robot_standing_wins():
    m = Match([bot(idle, "A"), bot(idle, "B")], seed=1)
    m.robots[1].health = 0
    result = m.step()
    assert result.winner is m.robots[0]
    assert result.reason == "last robot standing"


def test_time_up_tie_is_a_draw(monkeypatch):
    monkeypatch.setattr(config, "MAX_TICKS", 5)
    result = Match([bot(idle, "A"), bot(idle, "B")], seed=1).run()
    assert result.winner is None
    assert result.ticks == 5


def test_time_up_most_health_wins(monkeypatch):
    monkeypatch.setattr(config, "MAX_TICKS", 5)
    m = Match([bot(idle, "A"), bot(idle, "B")], seed=1)
    m.robots[0].health = 50
    assert m.run().winner is m.robots[1]


def test_same_seed_same_result():
    files = sorted(EXAMPLES_DIR.glob("*.py"))
    def outcome(seed):
        r = Match([load_bot(f) for f in files], seed=seed).run()
        return r.ticks, [(x.name, round(x.health, 3)) for x in r.placements]
    assert outcome(11) == outcome(11)


# ---- guards ------------------------------------------------------------

def test_crashing_bot_loses_turns_then_is_disqualified():
    m = Match([load_bot(BAD / "crashes.py"), bot(idle)], seed=1)
    x = m.robots[0].x
    m.step()
    assert m.robots[0].errors == 1
    assert "ZeroDivisionError" in m.robots[0].last_error
    assert "Line 6" in m.robots[0].last_error
    assert m.robots[0].x == x          # the forward() order was thrown away
    result = m.run()
    assert m.robots[0].status.startswith("disqualified")
    assert result.winner is m.robots[1]


def test_slow_bot_is_disqualified(monkeypatch):
    import time
    monkeypatch.setattr(config, "THINK_TIME_LIMIT", 0.001)
    m = Match([bot(lambda me, e, a: time.sleep(0.003)), bot(idle)], seed=1)
    result = m.run()
    assert m.robots[0].status.startswith("disqualified: too slow")
    assert result.winner is m.robots[1]


# ---- loader ------------------------------------------------------------

@pytest.mark.parametrize("name, message", [
    ("syntax_error.py", "Line 4: syntax error"),
    ("no_think.py", "def think(me, enemies, arena)"),
    ("imports_os.py", "can't import 'os'"),
    ("cheater.py", "'._robot' is off limits"),
    ("bad_color.py", "isn't a color I know"),
    ("wrong_args.py", "exactly three inputs"),
])
def test_loader_rejects_bad_bots(name, message):
    with pytest.raises(BotLoadError, match=message.replace("(", r"\(").replace(")", r"\)")):
        load_bot(BAD / name)


def test_examples_all_load():
    for f in EXAMPLES_DIR.glob("*.py"):
        load_bot(f)


# ---- competitions ------------------------------------------------------

def test_round_robin_points():
    files = sorted(EXAMPLES_DIR.glob("*.py"))
    c = Competition(files, seed=3)
    c.round_robin()
    total_games = len(files) * (len(files) - 1) // 2
    assert sum(s.played for s in c.standings.values()) == total_games * 2
    wins = sum(s.wins for s in c.standings.values())
    draws = sum(s.draws for s in c.standings.values())
    assert sum(s.points for s in c.standings.values()) == wins * 3 + draws


def test_bracket_crowns_one_champion():
    c = Competition(sorted(EXAMPLES_DIR.glob("*.py")), seed=3)
    champion = c.bracket(best_of=3)
    assert [s.path for s in c.standings.values() if s.note == "CHAMPION"] == [champion]
    assert c.ranked()[0].path == champion

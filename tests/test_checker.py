from pathlib import Path

from engine import checker
from engine.checker import FAIL, PASS, check_bot

BAD = Path(__file__).parent / "bad_bots"
KIT = Path(__file__).parent.parent / "student_kit"


def statuses(checks):
    return [s for s, _ in checks]


def test_starter_bot_passes():
    checks = check_bot(KIT / "my_bot.py")
    assert FAIL not in statuses(checks)
    assert statuses(checks).count(PASS) >= 7


def test_crashing_bot_fails_with_line_number():
    checks = check_bot(BAD / "crashes.py")
    failures = [m for s, m in checks if s == FAIL]
    assert failures and "Line 6" in failures[0]


def test_bad_import_fails():
    checks = check_bot(BAD / "imports_os.py")
    assert checks[0][0] == FAIL and "os" in checks[0][1]


def test_infinite_loop_is_caught(monkeypatch):
    monkeypatch.setattr(checker, "MATCH_TIMEOUT", 3)
    checks = check_bot(BAD / "infinite_loop.py")
    assert checks[-1][0] == FAIL
    assert "never ends" in checks[-1][1]

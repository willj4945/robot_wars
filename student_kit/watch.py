"""Watch your robot fight.

    python watch.py my_bot.py                 vs Chaser
    python watch.py my_bot.py sniper          vs any example bot (or another .py file)
    python watch.py my_bot.py all             free-for-all against every example bot

Keys: SPACE pause   +/- speed   ESC skip to the end   N next   Q quit
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE, HERE.parent):
    if (folder / "engine").is_dir():
        sys.path.insert(0, str(folder))
        break

from engine import EXAMPLES_DIR  # noqa: E402
from engine.loader import BotLoadError, load_bot  # noqa: E402
from engine.match import Match  # noqa: E402


def find(name):
    for candidate in (Path(name), EXAMPLES_DIR / name, EXAMPLES_DIR / f"{name}.py"):
        if candidate.is_file():
            return candidate
    examples = ", ".join(p.stem for p in sorted(EXAMPLES_DIR.glob("*.py")))
    sys.exit(f"Can't find '{name}'. Example bots: {examples}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    mine = find(sys.argv[1])
    other = sys.argv[2] if len(sys.argv) > 2 else "chaser"
    if other == "all":
        opponents = sorted(EXAMPLES_DIR.glob("*.py"))
        title = "Free-for-all"
    else:
        opponents = [find(other)]
        title = None

    try:
        programs = [load_bot(mine)] + [load_bot(p) for p in opponents]
    except BotLoadError as exc:
        sys.exit(f"Your robot can't load:\n{exc}")

    try:
        from viewer.pygame_view import Viewer, ViewerClosed
    except ImportError:
        sys.exit("The window needs pygame. Install it with:  pip install pygame-ce")

    viewer = Viewer()
    try:
        while True:
            match = Match([load_bot(mine)] + [load_bot(p) for p in opponents])
            viewer.play(match, title or " vs ".join(p.name for p in programs))
    except ViewerClosed:
        pass
    viewer.close()


if __name__ == "__main__":
    main()

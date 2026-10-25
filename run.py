"""Robot Wars: the teacher's control panel.

  python run.py duel alice bob                 one match, watched in a window
  python run.py duel alice bob --best-of 3
  python run.py ffa bots/                      everyone at once
  python run.py ffa bots/ --rounds 5           five rounds, points for outlasting others
  python run.py tournament bots/               round-robin, everyone plays everyone
  python run.py tournament bots/ --style bracket --best-of 3 --watch-final
  python run.py validate bots/                 check every submission before class

Bots can be files, folders, or just names (looked up in bots/ then examples/).
Add --fast to any game command to skip the window and just print results.
"""

import argparse
import sys
from pathlib import Path

from engine import EXAMPLES_DIR, ROOT
from engine.checker import check_bot, print_report
from engine.loader import BotLoadError, load_bot
from engine.tournament import Competition

BOTS_DIR = ROOT / "bots"


def resolve_bots(names):
    paths = []
    for name in names:
        p = Path(name)
        if p.is_dir():
            paths += sorted(f for f in p.glob("*.py") if not f.name.startswith("_"))
            continue
        candidates = [p, BOTS_DIR / p, EXAMPLES_DIR / p]
        candidates += [c.with_suffix(".py") for c in candidates if c.suffix != ".py"]
        found = next((c for c in candidates if c.is_file()), None)
        if not found:
            sys.exit(f"Can't find a bot called '{name}'. Looked in the current folder, bots/ and examples/.")
        paths.append(found)

    unique = []
    for p in paths:
        if p.resolve() not in [u.resolve() for u in unique]:
            unique.append(p)
    return unique


def loadable(paths):
    """Drop bots that can't load, explaining why."""
    good = []
    for p in paths:
        try:
            load_bot(p)
            good.append(p)
        except BotLoadError as exc:
            print(f"Skipping {p.name}:\n    " + str(exc).replace("\n", "\n    "))
    return good


def make_competition(args, paths):
    if args.fast:
        def show_game(match, title):
            result = match.run()
            winner = result.winner_name or "DRAW"
            print(f"  {title:<60} -> {winner} ({result.reason})")
            return result
        return Competition(paths, seed=args.seed, show_game=show_game), None

    from viewer.pygame_view import Viewer
    viewer = Viewer()
    watch_final = getattr(args, "watch_final", False)

    def show_game(match, title):
        if watch_final and not title.startswith("Final"):
            result = match.run()
            print(f"  {title:<60} -> {result.winner_name or 'DRAW'}")
            return result
        return viewer.play(match, title, auto_advance=args.auto)

    def announce(title, lines):
        if not watch_final:
            viewer.show_text(title, lines, auto_advance=args.auto)

    return Competition(paths, seed=args.seed, show_game=show_game, announce=announce), viewer


def run_competition(args, paths, mode, play):
    from_viewer_closed = ()
    competition, viewer = make_competition(args, paths)
    if viewer:
        from viewer.pygame_view import ViewerClosed
        from_viewer_closed = (ViewerClosed,)
    print(f"Seed {competition.seed} (use --seed {competition.seed} to replay exactly)\n")
    finished = True
    try:
        play(competition)
    except from_viewer_closed:
        finished = False
        print("\nWindow closed, stopping early.")

    print()
    print("\n".join(competition.leaderboard_lines()))
    if finished and len(paths) > 2:
        board, games = competition.save(mode)
        print(f"\nSaved {board} and {games}")
    if viewer:
        if finished and len(paths) > 2:
            try:
                viewer.show_text("Final standings", competition.leaderboard_lines())
            except ViewerClosed:
                pass
        viewer.close()


def cmd_duel(args):
    paths = loadable(resolve_bots([args.bot1, args.bot2]))
    if len(paths) != 2:
        sys.exit("A duel needs two different bots that load.")
    run_competition(args, paths, "duel", lambda c: c.duel(args.best_of))


def cmd_ffa(args):
    paths = loadable(resolve_bots(args.bots))
    if len(paths) < 2:
        sys.exit("A free-for-all needs at least two bots that load.")
    run_competition(args, paths, "ffa", lambda c: c.free_for_all(args.rounds))


def cmd_tournament(args):
    paths = loadable(resolve_bots(args.bots))
    if len(paths) < 2:
        sys.exit("A tournament needs at least two bots that load.")
    if args.style == "bracket":
        play = lambda c: c.bracket(args.best_of)
    else:
        play = lambda c: c.round_robin(args.best_of)
    run_competition(args, paths, args.style, play)


def cmd_validate(args):
    paths = resolve_bots(args.bots)
    failed = []
    for p in paths:
        if not print_report(p, check_bot(p)):
            failed.append(p.name)
    print(f"{len(paths) - len(failed)} of {len(paths)} bots are ready.")
    if failed:
        print("Need fixing: " + ", ".join(failed))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Robot Wars", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def game_options(p):
        p.add_argument("--seed", type=int, help="replay a match exactly")
        p.add_argument("--fast", action="store_true", help="no window, just print results")
        p.add_argument("--auto", type=float, metavar="SECONDS", help="move on by itself after this many seconds")

    p = sub.add_parser("duel", help="two bots fight")
    p.add_argument("bot1")
    p.add_argument("bot2")
    p.add_argument("--best-of", type=int, default=1)
    game_options(p)
    p.set_defaults(func=cmd_duel)

    p = sub.add_parser("ffa", help="free-for-all, everyone at once")
    p.add_argument("bots", nargs="+")
    p.add_argument("--rounds", type=int, default=1)
    game_options(p)
    p.set_defaults(func=cmd_ffa)

    p = sub.add_parser("tournament", help="round-robin or bracket")
    p.add_argument("bots", nargs="+")
    p.add_argument("--style", choices=["roundrobin", "bracket"], default="roundrobin")
    p.add_argument("--best-of", type=int, default=1)
    p.add_argument("--watch-final", action="store_true", help="bracket: only watch the final")
    game_options(p)
    p.set_defaults(func=cmd_tournament)

    p = sub.add_parser("validate", help="check submissions")
    p.add_argument("bots", nargs="+")
    p.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

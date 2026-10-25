"""Duels, free-for-alls, round-robins and brackets, plus the leaderboard."""

import csv
import itertools
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .loader import load_bot
from .match import Match


@dataclass
class Standing:
    name: str
    path: Path
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: int = 0
    damage: float = 0.0
    hits: int = 0
    shots: int = 0
    note: str = ""

    @property
    def accuracy(self):
        return self.hits / self.shots if self.shots else 0.0


class Competition:
    """Runs games and keeps score.

    show_game(match, title) -> MatchResult   plays a match (in a window, or headless)
    announce(title, lines)                   shows a message between games
    """

    def __init__(self, paths, seed=None, show_game=None, announce=None):
        self.paths = [Path(p) for p in paths]
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        self.games_played = 0
        self.show_game = show_game or (lambda match, title: match.run())
        self.announce = announce or (lambda title, lines: None)
        self.standings = {p: Standing(load_bot(p).name, p) for p in self.paths}
        self.log = []

    # ---- single game ----------------------------------------------------
    def play(self, paths, title):
        seed = self.seed + self.games_played
        self.games_played += 1
        match = Match([load_bot(p) for p in paths], seed=seed)
        result = self.show_game(match, title)
        for robot in result.robots:
            s = self.standings[robot.program.path]
            s.damage += robot.damage_dealt
            s.hits += robot.hits
            s.shots += robot.shots
        self.log.append({
            "game": self.games_played,
            "title": title,
            "seed": seed,
            "robots": " vs ".join(r.name for r in result.robots),
            "winner": result.winner_name or "DRAW",
            "reason": result.reason,
            "ticks": result.ticks,
            "placements": " > ".join(r.name for r in result.placements),
        })
        return result

    def series(self, a, b, best_of, title):
        """Play up to best_of games between two bots. Returns the winning path, or None if tied."""
        needed = best_of // 2 + 1
        score = {a: 0, b: 0}
        for game in range(1, best_of + 1):
            label = title if best_of == 1 else f"{title}  (game {game} of {best_of})"
            result = self.play([a, b], label)
            if result.winner:
                score[result.winner.program.path] += 1
            if max(score.values()) >= needed:
                break
        if score[a] == score[b]:
            return None
        return a if score[a] > score[b] else b

    # ---- modes ----------------------------------------------------------
    def duel(self, best_of=1):
        a, b = self.paths
        title = f"{self.standings[a].name} vs {self.standings[b].name}"
        winner = self.series(a, b, best_of, title)
        self._record_series(a, b, winner)
        return winner

    def free_for_all(self, rounds=1):
        """Everyone at once. Each round you score 1 point per robot you outlast."""
        for round_number in range(1, rounds + 1):
            title = "Free-for-all" if rounds == 1 else f"Free-for-all  (round {round_number} of {rounds})"
            result = self.play(self.paths, title)
            count = len(result.placements)
            for place, robot in enumerate(result.placements):
                s = self.standings[robot.program.path]
                s.played += 1
                s.points += count - 1 - place
                if place == 0 and result.winner:
                    s.wins += 1
            if rounds > 1:
                self.announce(f"After round {round_number}", self.leaderboard_lines())

    def round_robin(self, best_of=1):
        """Everyone plays everyone. Win = 3 points, draw = 1."""
        pairs = list(itertools.combinations(self.paths, 2))
        random.Random(self.seed).shuffle(pairs)
        for number, (a, b) in enumerate(pairs, 1):
            title = f"Match {number}/{len(pairs)}: {self.standings[a].name} vs {self.standings[b].name}"
            self._record_series(a, b, self.series(a, b, best_of, title))
            self.announce("Leaderboard", self.leaderboard_lines())

    def bracket(self, best_of=1):
        """Single elimination. A tied series goes to whoever did more damage."""
        alive = list(self.paths)
        random.Random(self.seed).shuffle(alive)
        round_number = 1
        while len(alive) > 1:
            name = _round_name(len(alive), round_number)
            next_round, lines = [], []
            if len(alive) % 2:
                lucky = alive.pop()
                next_round.append(lucky)
                lines.append(f"{self.standings[lucky].name} gets a bye")
            for a, b in zip(alive[::2], alive[1::2]):
                title = f"{name}: {self.standings[a].name} vs {self.standings[b].name}"
                before = {p: self.standings[p].damage for p in (a, b)}
                winner = self.series(a, b, best_of, title)
                if winner is None:
                    dealt = {p: self.standings[p].damage - before[p] for p in (a, b)}
                    if dealt[a] != dealt[b]:
                        winner = max(dealt, key=dealt.get)
                    else:
                        winner = random.Random(self.seed + round_number).choice([a, b])
                loser = b if winner == a else a
                self._record_series(winner, loser, winner)
                self.standings[loser].note = f"out in {name.lower()}"
                next_round.append(winner)
                lines.append(f"{self.standings[winner].name}  beat  {self.standings[loser].name}")
            self.announce(f"{name} results", lines)
            alive = next_round
            round_number += 1
        champion = alive[0]
        self.standings[champion].note = "CHAMPION"
        return champion

    # ---- scoring --------------------------------------------------------
    def _record_series(self, a, b, winner):
        for p in (a, b):
            s = self.standings[p]
            s.played += 1
            if winner is None:
                s.draws += 1
                s.points += 1
            elif winner == p:
                s.wins += 1
                s.points += 3
            else:
                s.losses += 1

    def ranked(self):
        return sorted(
            self.standings.values(),
            key=lambda s: (s.note == "CHAMPION", s.points, s.wins, s.damage),
            reverse=True,
        )

    def leaderboard_lines(self):
        lines = [f"{'#':>2}  {'Robot':<24} {'Pts':>4} {'W':>3} {'D':>3} {'L':>3} {'Damage':>7} {'Acc':>5}  "]
        for i, s in enumerate(self.ranked(), 1):
            lines.append(
                f"{i:>2}  {s.name:<24} {s.points:>4} {s.wins:>3} {s.draws:>3} {s.losses:>3} "
                f"{s.damage:>7.0f} {s.accuracy:>5.0%}  {s.note}"
            )
        return lines

    def save(self, mode, folder="results"):
        folder = Path(folder)
        folder.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        board = folder / f"{mode}_{stamp}_leaderboard.csv"
        with board.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["rank", "robot", "file", "points", "wins", "draws", "losses", "damage", "accuracy", "note"])
            for i, s in enumerate(self.ranked(), 1):
                writer.writerow([i, s.name, s.path.name, s.points, s.wins, s.draws, s.losses,
                                 round(s.damage), f"{s.accuracy:.0%}", s.note])
        games = folder / f"{mode}_{stamp}_games.csv"
        with games.open("w", newline="", encoding="utf-8") as f:
            fields = ["game", "title", "seed", "robots", "winner", "reason", "ticks", "placements"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.log)
        return board, games


def _round_name(remaining, number):
    if remaining == 2:
        return "Final"
    if remaining <= 4:
        return "Semi-final"
    if remaining <= 8:
        return "Quarter-final"
    return f"Round {number}"

"""Load a student's bot file, checking it follows the rules first."""

import ast
import inspect
import itertools
import traceback
import types
from pathlib import Path

from . import config

_module_ids = itertools.count()


class BotLoadError(Exception):
    """A bot file that can't be used. The message is written for students."""


class BotProgram:
    def __init__(self, name, color, think, path, color_name=None):
        self.name = name
        self.color = color
        self.color_name = color_name if color_name is not None else color
        self.think = think
        self.path = Path(path)

    def __repr__(self):
        return f"<BotProgram {self.name} from {self.path.name}>"


def scan_source(tree):
    """Return a list of rule problems found in the parsed code."""
    problems = []
    allowed = ", ".join(sorted(config.ALLOWED_IMPORTS))
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in config.ALLOWED_IMPORTS:
                    problems.append(f"Line {line}: you can't import '{alias.name}'. Allowed imports: {allowed}.")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level or root not in config.ALLOWED_IMPORTS:
                problems.append(f"Line {line}: you can't import from '{node.module}'. Allowed imports: {allowed}.")
        elif isinstance(node, ast.Name):
            if node.id in config.BANNED_NAMES:
                problems.append(f"Line {line}: '{node.id}' isn't allowed in a robot.")
            elif node.id.startswith("__") and node.id != "__name__":
                problems.append(f"Line {line}: '{node.id}' isn't allowed in a robot.")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            problems.append(f"Line {line}: '.{node.attr}' is off limits (names starting with _ are private).")
    return problems


def describe_error(exc, path):
    """Turn an exception into one friendly line pointing at the student's code."""
    path = str(Path(path).resolve())
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if str(Path(frame.filename).resolve()) == path:
            line = frame.lineno
    where = f"Line {line}: " if line else ""
    return f"{where}{type(exc).__name__}: {exc}"


def parse_color(color):
    if isinstance(color, str) and color.lower().strip() in config.COLORS:
        return config.COLORS[color.lower().strip()]
    if (
        isinstance(color, (tuple, list))
        and len(color) == 3
        and all(isinstance(c, int) and 0 <= c <= 255 for c in color)
    ):
        return tuple(color)
    names = ", ".join(config.COLORS)
    raise BotLoadError(f"COLOR {color!r} isn't a color I know. Pick one of: {names} (or an (r, g, b) tuple).")


def load_bot(path):
    """Load a bot file and return a BotProgram, or raise BotLoadError."""
    path = Path(path)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BotLoadError(f"Couldn't read {path.name}: {exc}") from None

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        text = (exc.text or "").rstrip()
        pointer = ""
        if text and exc.offset:
            pointer = "\n    " + text + "\n    " + " " * (exc.offset - 1) + "^"
        raise BotLoadError(f"Line {exc.lineno}: syntax error, {exc.msg}{pointer}") from None

    problems = scan_source(tree)
    if problems:
        raise BotLoadError("\n".join(problems))

    module = types.ModuleType(f"robot_{next(_module_ids)}_{path.stem}")
    module.__file__ = str(path)
    try:
        exec(compile(tree, str(path), "exec"), module.__dict__)
    except Exception as exc:
        raise BotLoadError(f"Your file crashed while loading. {describe_error(exc, path)}") from None

    name = getattr(module, "NAME", None)
    if not isinstance(name, str) or not name.strip():
        raise BotLoadError('Your file needs a NAME, like:  NAME = "Robo Destroyer"')
    if not hasattr(module, "COLOR"):
        raise BotLoadError('Your file needs a COLOR, like:  COLOR = "red"')
    color = parse_color(module.COLOR)

    think = getattr(module, "think", None)
    if not callable(think):
        raise BotLoadError("Your file needs a function:  def think(me, enemies, arena):")
    try:
        inspect.signature(think).bind(None, None, None)
    except TypeError:
        raise BotLoadError("think must take exactly three inputs:  def think(me, enemies, arena):") from None

    return BotProgram(name.strip()[:24], color, think, path, module.COLOR)

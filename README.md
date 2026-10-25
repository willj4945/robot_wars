# Robot Wars

Students learn Python by programming a robot. You collect the robot files and run the fights on the projector.

## Setup (teacher machine)
```
python -m pip install -r requirements.txt      # just pygame-ce
```
Python 3.10 or newer is needed. The engine uses only the standard library. pygame is only needed for the window.

## Hand out the kit
```
python make_student_kit.py
```
This builds `dist/robot_wars_student_kit.zip`. Students unzip it, edit `my_bot.py`, and use:
- `python watch.py my_bot.py chaser` to watch a fight (`all` gives a free-for-all against the examples)
- `python check_my_bot.py my_bot.py` to get the "ready to hand in" checklist

Everything a student needs to know is in `student_kit/GUIDE.md`: the API, the rules, and a ladder of challenges that each teach a Python idea.

## Collect bots
Students hand in a **single `.py` file**, by USB, shared drive, LMS, or anything else. Put the files in `bots/`, ideally named after each student, e.g. `bots/alex.py`.

Check them all before class:
```
python run.py validate bots/
```
This runs the same checks the students ran. It catches crashes, banned imports, and infinite loops.

## Fight!
```
python run.py duel alex sam                      # one match
python run.py duel alex sam --best-of 3
python run.py ffa bots/                          # everyone at once
python run.py ffa bots/ --rounds 5               # 1 point for every robot you outlast
python run.py tournament bots/                   # round-robin: win 3, draw 1
python run.py tournament bots/ --style bracket --best-of 3
python run.py tournament bots/ --style bracket --watch-final   # sim everything, watch the final
```
Options that work with every fight command:
- `--fast` prints results with no window.
- `--auto 5` moves on by itself after 5 seconds.
- `--seed N` replays a match exactly. The seed is printed at the start.

Bots can be given as files, folders, or names (looked up in `bots/`, then `examples/`). Results for tournaments and free-for-alls are saved as CSV in `results/`.

**Window keys:**
- SPACE: pause
- `+` / `-`: speed
- ESC: skip to the result
- N / ENTER: next
- F: fullscreen
- Q: quit

## Tuning the game
All the numbers live in `engine/config.py`: speed, turn rate, damage, reload time, match length, and the crash/time limits. If you change them, rebuild the student kit so students test with the same rules.

## Safety
Each bot file is scanned before loading:
- Only `math` and `random` can be imported.
- No `open`, `eval`, `exec`, and so on.
- No touching private `_` attributes, so `me._robot.health = 1000` is blocked.

A bot that crashes or is too slow loses its turn, and is disqualified if it keeps doing it. Infinite loops are caught by `validate`.

This is a classroom guard, not a security sandbox. Skim submissions if anything looks odd.

## Layout
| Path | What's there |
|---|---|
| `engine/` | physics, loader, guards, match, tournaments, checker |
| `viewer/` | pygame window |
| `examples/` | 5 sample bots |
| `student_kit/` | student-facing files |
| `tests/` | `python -m pytest tests` |

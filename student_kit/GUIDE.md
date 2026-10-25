# Robot Wars: Student Guide

You're going to program a robot in Python. Then it fights everyone else's robot.

## Getting started

1. Install the window library (you only need to do this once):
   ```
   pip install pygame-ce
   ```
2. Open `my_bot.py`. Change the `NAME` and `COLOR`.
3. Watch it fight:
   ```
   python watch.py my_bot.py chaser
   ```
4. Check it's ready to hand in:
   ```
   python check_my_bot.py my_bot.py
   ```
5. Hand in **only `my_bot.py`**. You can rename it, e.g. `alex_bot.py`.

## How it works

Your file needs three things:

```python
NAME = "Robo Crusher"
COLOR = "red"

def think(me, enemies, arena):
    ...
```

The game calls `think` **30 times every second**. Each time, you look at what's happening and give your robot orders for that moment. If you don't give an order, the robot won't do it. For example, call `me.forward()` every time if you want to keep moving.

### The arena

- It is 800 wide and 600 tall. `(0, 0)` is the **top-left** corner.
- `x` gets bigger going right. `y` gets bigger going **down**.
- Headings work like a compass: `0` is up, `90` is right, `180` is down, `270` is left.

```
            0 (up)
            |
 270 -------+------- 90
            |
           180
```

## What your robot can do

### Information (`me.something`)
| Code | What it gives you |
|---|---|
| `me.x`, `me.y` | where you are |
| `me.heading` | which way you're facing (0-360) |
| `me.health` | 100 at the start, 0 means destroyed |
| `me.speed` | how fast you're moving |
| `me.gun_heat` | ticks until you can fire again |
| `me.memory` | a dictionary that remembers things between ticks |

### Orders
| Code | What it does |
|---|---|
| `me.forward()` | drive forward at full speed (4). `me.forward(2)` drives at half speed |
| `me.backward()` | drive backward |
| `me.stop()` | stand still |
| `me.turn_left()` / `me.turn_right()` | turn as fast as possible (6 degrees per tick), or e.g. `me.turn_left(2)` for a smaller turn |
| `me.turn_toward(thing)` | turn to face an enemy, or a point like `(400, 300)` |
| `me.turn_to_heading(90)` | turn to face a compass direction |
| `me.fire()` | shoot. `me.fire(3)` is a big shot, but it takes longer to reload |

### Helpers (they give you an answer)
| Code | Answer |
|---|---|
| `me.distance_to(thing)` | how far away something is |
| `me.angle_to(thing)` | the compass heading pointing at something |
| `me.closest(enemies)` | the nearest enemy |
| `me.can_fire()` | `True` if your gun is ready |
| `me.near_wall()` | `True` if you're close to a wall |

### Enemies
`enemies` is a **list**. Each enemy has `.name`, `.x`, `.y`, `.heading`, `.health` and `.speed`.

### The arena object
`arena.width`, `arena.height`, and `arena.tick`, which counts up from 0.

## The rules

- **Bullets:**
  - Power 1 does 10 damage, power 2 does 20, power 3 does 30.
  - Bigger shots take longer to reload.
- **Damage that isn't from bullets:**
  - Driving into a wall hurts a little.
  - Crashing into another robot hurts both of you.
- **Winning:** the last robot standing wins. After 2 minutes, the most health wins.
- **Imports:** only `import math` and `import random` are allowed.
- **Speed:** `think` must be quick (under 50 ms). If it's too slow or it crashes, you lose that turn. Too many slow or crashed turns and you're **disqualified**.

## Challenges

Work through these in order. Each one teaches a Python idea.

### 1. Drive (variables and calling functions)
Make your robot drive in a circle with `me.forward()` and `me.turn_right()`. Use a variable for the speed:
```python
speed = 3
me.forward(speed)
```

### 2. Don't hit the wall (if / else)
```python
if me.near_wall():
    me.turn_right()
else:
    me.forward()
```

### 3. Only shoot when it's worth it (comparisons, `and`)
Only fire when the gun is ready **and** the enemy is closer than 300:
```python
target = me.closest(enemies)
if me.can_fire() and me.distance_to(target) < 300:
    me.fire()
```

### 4. Write your own function
Put your dodging code in its own function and call it from `think`:
```python
def dodge(me):
    me.turn_left()
    me.backward()
```

### 5. Pick the weakest enemy (lists and loops)
In a free-for-all, finishing off a weak robot can be smart:
```python
weakest = enemies[0]
for enemy in enemies:
    if enemy.health < weakest.health:
        weakest = enemy
```

### 6. Remember things (dictionaries)
`me.memory` keeps its contents between ticks. Count your ticks, remember where the enemy was, or switch between "attack" and "run away" modes:
```python
if "mode" not in me.memory:
    me.memory["mode"] = "attack"
if me.health < 30:
    me.memory["mode"] = "run"
```

### 7. Boss level: aim ahead (math)
Bullets take time to fly. Use the enemy's `heading` and `speed` to work out where they'll be, then aim there. Look at `examples/sniper.py` for one way to do it.

## Example robots

Look inside the `examples` folder. Read their code, fight them, and beat them all:

| Robot | Strategy |
|---|---|
| Sitting Duck | does nothing |
| Spinner | goes in circles and shoots |
| Chaser | charges the closest enemy |
| Wall Runner | drives around the edge |
| Sniper | aims ahead and fires big shots |

## When something goes wrong

- **`check_my_bot.py` shows the line number.** Look at that line first.
- **Want to see what your robot is thinking?** Use `print()` while testing. Remove it before you hand in.
- **The window shows your robot's latest error** in red under its name in the sidebar.

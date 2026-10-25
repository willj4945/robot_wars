"""Game rules. Tweak these numbers to change how the game feels."""

ARENA_WIDTH = 800
ARENA_HEIGHT = 600

TICKS_PER_SECOND = 30          # how fast the viewer plays at 1x speed
MAX_TICKS = 30 * 120           # 2 minutes, then highest health wins

ROBOT_RADIUS = 18
START_HEALTH = 100
MAX_SPEED = 4.0                # pixels per tick
MAX_TURN = 6.0                 # degrees per tick

BULLET_SPEED = 12.0            # pixels per tick
BULLET_RADIUS = 4
MIN_POWER = 1
MAX_POWER = 3
DAMAGE_PER_POWER = 10          # a power-2 shot does 20 damage
HEAT_PER_POWER = 15            # a power-2 shot means 30 ticks before you can fire again

WALL_DAMAGE = 0.5              # per tick spent pushing into a wall
RAM_DAMAGE = 1.0               # per tick two robots are touching

NEAR_WALL_DISTANCE = 60        # what me.near_wall() means

# Guards against broken bots
THINK_TIME_LIMIT = 0.05        # seconds per think() call before the turn is skipped
MAX_ERRORS = 30                # crashes before a bot is disqualified
MAX_SLOW_TURNS = 15            # slow turns before a bot is disqualified

ALLOWED_IMPORTS = {"math", "random"}
BANNED_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "input",
    "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit",
}

COLORS = {
    "red": (230, 60, 60),
    "blue": (70, 130, 240),
    "green": (60, 190, 90),
    "yellow": (240, 220, 60),
    "orange": (245, 150, 40),
    "purple": (160, 90, 220),
    "pink": (240, 120, 190),
    "cyan": (60, 210, 220),
    "white": (235, 235, 235),
    "lime": (170, 240, 60),
    "teal": (40, 160, 150),
    "gold": (215, 175, 50),
    "silver": (170, 175, 185),
    "magenta": (220, 50, 200),
    "brown": (160, 110, 70),
    "navy": (60, 80, 170),
}

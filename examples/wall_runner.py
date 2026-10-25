# Drives around the edge of the arena, shooting at whoever is closest.
# Concepts: functions, if/elif, using memory to remember things between ticks.

NAME = "Wall Runner"
COLOR = "cyan"

# The four corners we drive between, in order.
CORNERS = [(90, 90), (710, 90), (710, 510), (90, 510)]


def next_corner(me):
    if "corner" not in me.memory:
        me.memory["corner"] = 0
    corner = CORNERS[me.memory["corner"]]
    if me.distance_to(corner) < 30:
        me.memory["corner"] = (me.memory["corner"] + 1) % len(CORNERS)
        corner = CORNERS[me.memory["corner"]]
    return corner


def think(me, enemies, arena):
    me.turn_toward(next_corner(me))
    me.forward()

    target = me.closest(enemies)
    # Only shoot if we're already roughly facing the target.
    difference = abs(me.angle_to(target) - me.heading) % 360
    if me.can_fire() and (difference < 15 or difference > 345):
        me.fire()
